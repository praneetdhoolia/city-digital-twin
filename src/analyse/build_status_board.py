#!/usr/bin/env python
"""Regenerate the GENERATED blocks of a city's board (STATUS.md).

    python src/analyse/build_status_board.py           rewrite the blocks in place
    python src/analyse/build_status_board.py --check   exit 1 if a block is stale

The board used to be typed by hand, and the parts of it that a run or a build
decides - the per-mode scoreboard, the open comparability family, the runs on
disk, the registry and manifest counts - lagged the artefacts by a family or
more within a day. Those parts are now written by this script between marker
comments, and the hand-written part of the board is capped by
`tests/check_doc_shape.py`. A block is delimited by

    <!-- generated:NAME start -->
    ...
    <!-- generated:NAME end -->

and everything between the markers is replaced; nothing outside them is
touched. The three blocks:

  scoreboard   every mode individually against its target, from the newest
               run directory that holds a readable iteration - the reader
               `report_mode_ridership.py` computes it; this only lays it out.
               Timestamps are the RUN'S OWN (launch, iteration), never the
               wall clock, so the block is reproducible.
  runs         the newest run directories with status, family and cause.
  state        the open family, the registry, manifest and run-input counts,
               and the position pages with their update dates - every value
               from a COMMITTED artefact, so CI can check this block.

`--check` regenerates each block and compares. The two results-derived blocks
are SKIPPED when `results/` holds no readable run (CI has no bulk data); the
`state` block is always compared. Nothing here is a result: a run without
`_run.json` is not a result, and the scoreboard says which run and iteration
it read.
"""
import argparse
import contextlib
import csv
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
for _p in (os.path.join(ROOT, 'src'), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import city as _city                                              # noqa: E402

for _p in (os.path.join(ROOT, 'src', 'run'),):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import results_store as _store                                    # noqa: E402

RESULTS = os.path.join(ROOT, 'results')
MARK = re.compile(r'<!-- generated:(\w+) start -->\n(.*?)<!-- generated:\1 end -->',
                  re.S)
RUN_DIR = re.compile(r'^(aborted_)?\d{8}T\d{6}_\d+it_\d+pct$')


# ------------------------------------------------------------------ helpers

def _read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _json(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _families():
    import build_run_index as bri
    return bri.load_families()


def _family_of(name):
    import build_run_index as bri
    fams, overrides = _families()
    return bri.family_of(name, fams, overrides)[0]


def _run_dirs():
    import build_run_index as bri
    names = [n for n in _store.run_names() if RUN_DIR.match(n)]
    return sorted(names, key=lambda n: bri.launch_stamp(n) or '', reverse=True)


def _dir_of(name):
    """A run's directory: raw while the bulk lives, processed after a trim."""
    return _store.resolve_records(name) or os.path.join(RESULTS, name)


def _iterations_reached(run_dir):
    iters = os.path.join(run_dir, 'output', 'ITERS')
    if not os.path.isdir(iters):
        return None
    nums = [int(d[3:]) for d in os.listdir(iters)
            if d.startswith('it.') and d[3:].isdigit()]
    return max(nums) if nums else None


def _horizon_floor():
    """The lower bound of the declared sweep on the iteration horizon.

    A run that DECLARES fewer iterations than the smallest value the registry
    admits as a modelling run is a plumbing test (the `smoke` overlay says so
    in its own justification): its shares are two iterations of seed plans and
    may not be quoted, compared or fitted. The board must never carry one as
    its reading - a smoke launched after an arm would otherwise displace that
    arm's last gate reading. None when the registry cannot say."""
    try:
        import registry as _registry
        sweep = _registry.load(strict=True).sweep('RUN.controler.last_iteration')
        return float(sweep['interval'][0])
    except Exception:
        return None


def _is_plumbing_test(run_dir, floor):
    if floor is None:
        return False
    meta = _json(os.path.join(run_dir, '_meta.json')) or {}
    declared = meta.get('iterations')
    return isinstance(declared, (int, float)) and declared < floor


def _fmt(v, target):
    if v is None:
        return '-'
    big = (target is not None and abs(target) >= 1000) or abs(v) >= 1000
    return '{:,.0f}'.format(v) if big else '%.4f' % v


# ------------------------------------------------------------------- blocks

def block_scoreboard():
    """The twelve-mode table from the newest readable run, or None.

    A plumbing test (a run declaring fewer iterations than the registry's
    horizon floor) is skipped, so the reading is the newest ARM's. So is an
    arm of a family the ledger declares `"readings": "none"` - a family
    whose arm ran a model later found broken at the root (9.148: a global
    `wait` that stranded every non-chain mode), which the runs block still
    lists with its cause but the scoreboard must never present."""
    import measure_iteration_modes as mim
    import iteration_trips as itr
    floor = _horizon_floor()
    fams, _overrides = _families()
    no_readings = {fam_id for fam_id, fam in fams if fam.get('readings') == 'none'}
    for name in _run_dirs():
        run_dir = _dir_of(name)
        if _is_plumbing_test(run_dir, floor):
            continue
        if _family_of(name) in no_readings:
            continue
        try:
            have = sorted(set(mim.iterations_with_trips(run_dir))
                          | set(itr.iterations_with_plans(run_dir)))
        except Exception:                      # a half-written directory
            continue
        if not have:
            continue
        import report_mode_ridership as rmr
        # the newest iteration may still be being written on a running arm
        meta = _json(os.path.join(run_dir, '_meta.json')) or {}
        candidates = have[:-1] if meta.get('status') == 'running' and len(have) > 1 else have
        for it in reversed(candidates):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    rmr.report(run_dir, it)
            except SystemExit:
                continue
            rows = rmr.LAST['rows']
            break
        else:
            continue
        fam = _family_of(name) or '-'
        frac = rmr.LAST.get('fraction')
        lines = []
        lines.append('Read from `%s` at **iteration %d** (family `%s`, status `%s`, '
                     '%s%% sample, launched %s, %s). **Not a result** - only a run '
                     'whose `_run.json` says `ran_to_last_iteration` is one, and '
                     'every arm since F4 stopped before its gate.'
                     % (name, it, fam, meta.get('status', 'unknown'),
                        ('%g' % (100 * frac)) if frac else '?',
                        meta.get('started', '?'), rmr.LAST.get('source', '')))
        lines.append('Reproduce: `python src/analyse/report_mode_ridership.py '
                     '--run %s --it %d` (`--trend` for the direction).' % (name, it))
        lines.append('')
        lines.append('| # | mode | modelled | target | deviation | gate | basis |')
        lines.append('|---|---|---:|---:|---:|---|---|')
        for r in rows:
            dev = r.get('deviation_pct')
            dev_s = '-' if dev is None else '%+.1f%%' % dev
            flag = r.get('flag') or ''
            if flag.startswith('STOP'):
                gate = '**STOP** >=20%'
            elif flag.startswith('over'):
                gate = 'over 10%'
            elif flag == 'ok':
                gate = 'ok'
            else:
                gate = flag
            lines.append('| %d | %s | %s | %s | %s | %s | %s |'
                         % (r['n'], r['mode'], _fmt(r.get('modelled'), r.get('target')),
                            _fmt(r.get('target'), r.get('target')), dev_s, gate,
                            r.get('basis', '')))
        stop = [r['mode'] for r in rows if (r.get('flag') or '').startswith('STOP')]
        inside = [r['mode'] for r in rows if r.get('flag') == 'ok']
        lines.append('')
        lines.append('Inside 10%%: **%s**. Past the 20%% stop bar: **%s**.'
                     % (', '.join(inside) or 'none', ', '.join(stop) or 'none'))
        return '\n'.join(lines) + '\n'
    return None


def block_runs():
    """The newest run directories, or None when there are none.

    Six rows: the board is one page, and the full list is results/INDEX.md.
    """
    names = _run_dirs()
    if not names:
        return None
    lines = ['| run | status | family | reached | cause / note |',
             '|---|---|---|---:|---|']
    for name in names[:6]:
        run_dir = _dir_of(name)
        meta = _json(os.path.join(run_dir, '_meta.json')) or {}
        reached = _iterations_reached(run_dir)
        cause = (meta.get('cause') or '').replace('|', '/').replace('\n', ' ')
        if len(cause) > 140:
            cause = cause[:137] + '...'
        # A record no longer means the run reached its horizon - one stopped at
        # a gate carries one too - so the cell says WHICH boundary ended it.
        rec = _json(os.path.join(run_dir, '_run.json'))
        record = ('%s `_run.json`'
                  % rec.get('completion', 'ran_to_last_iteration')) if rec else ''
        lines.append('| `%s` | %s | %s | %s | %s |'
                     % (name, meta.get('status', '?'), _family_of(name) or '-',
                        '-' if reached is None else reached,
                        cause or record or '-'))
    lines.append('')
    lines.append('%d run directories on disk; `results/INDEX.md` labels every one. '
                 'A dead run states its cause in its own `_meta.json`.' % len(names))
    return '\n'.join(lines) + '\n'


def block_state():
    """Committed-artefact state: family, counts, positions."""
    fams, _ = _families()
    fam_id, fam = fams[-1]
    lines = []
    lines.append('| | |')
    lines.append('|---|---|')
    lines.append('| Open comparability family | `%s` (opened `%s`, §%s) - nothing run before it compares with anything after it |'
                 % (fam_id, fam.get('from_launch', '?'), fam.get('decisions_ref', '?')))
    # registry fields
    reg_dir = _city.path('registry')
    n_fields = 0
    for fn in sorted(os.listdir(reg_dir)):
        if fn.endswith('.json'):
            doc = _json(os.path.join(reg_dir, fn)) or {}
            n_fields += len(doc.get('fields', doc))
    lines.append('| Input registry | **%d fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |' % n_fields)
    # manifest
    man = _city.path('data', 'MANIFEST.csv')
    n_files = 0
    if os.path.exists(man):
        with open(man, newline='', encoding='utf-8') as fh:
            n_files = sum(1 for _ in csv.DictReader(fh))
    lines.append('| Data package | **%d files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |' % n_files)
    # run-input sets - counted from the COMMITTED manifest (one config.xml per
    # scenario x day-type set), never from the gitignored directories, so the
    # block reads the same in CI as on the workstation
    sets = 0
    if os.path.exists(man):
        with open(man, newline='', encoding='utf-8') as fh:
            for row in csv.DictReader(fh):
                parts = row['path'].split('/')
                if (len(parts) == 5 and parts[0] == 'scenarios' and parts[1] == 'matsim'
                        and parts[4] == 'config.xml'):
                    sets += 1
    lines.append('| Run inputs assembled | **%d** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |' % sets)
    # positions
    pos_dir = _city.path('docs', 'positions')
    if os.path.isdir(pos_dir):
        items = []
        for fn in sorted(os.listdir(pos_dir)):
            if not fn.endswith('.md'):
                continue
            text = _read(os.path.join(pos_dir, fn))
            m = re.search(r'\*\*Updated:\*\*\s*([^·\n]+)', text)
            items.append('[%s](positions/%s) (%s)' % (fn[:-3], fn, (m.group(1).strip() if m else '?')))
        lines.append('| Position pages | %s |' % ' · '.join(items))
    return '\n'.join(lines) + '\n'


BLOCKS = {
    'scoreboard': block_scoreboard,
    'runs': block_runs,
    'state': block_state,
}


# --------------------------------------------------------------------- main

def apply(text, check=False):
    """Return (new_text, report) where report lists (name, verdict)."""
    report = []

    def sub(m):
        name, old = m.group(1), m.group(2)
        fn = BLOCKS.get(name)
        if fn is None:
            report.append((name, 'UNKNOWN BLOCK - left as is'))
            return m.group(0)
        new = fn()
        if new is None:
            report.append((name, 'SKIPPED - no readable run on this machine'))
            return m.group(0)
        if new == old:
            report.append((name, 'current'))
        else:
            report.append((name, 'STALE' if check else 'rewritten'))
        body = old if check else new
        return '<!-- generated:%s start -->\n%s<!-- generated:%s end -->' % (name, body, name)

    return MARK.sub(sub, text), report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true',
                    help='compare the blocks with what would be generated; exit 1 if stale')
    ap.add_argument('--board', default=None,
                    help='the board file (default: the city\'s docs/STATUS.md)')
    a = ap.parse_args()
    board = a.board or _city.path('docs', 'STATUS.md')
    text = _read(board)
    new, report = apply(text, check=a.check)
    for name, verdict in report:
        print('  %-11s %s' % (name, verdict))
    if not report:
        print('no generated blocks found in %s' % board)
        return 1
    stale = [n for n, v in report if v == 'STALE']
    if a.check:
        print('BOARD %s' % ('STALE: ' + ', '.join(stale) if stale else 'current'))
        return 1 if stale else 0
    if new != text:
        with open(board, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(new)
        print('wrote %s' % os.path.relpath(board, ROOT))
    else:
        print('board unchanged')
    return 0


if __name__ == '__main__':
    sys.exit(main())
