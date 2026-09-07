"""Two runs' wall clock, phase by phase, with the comparability rule enforced.

Every timing decision in the record so far was assembled by hand out of each
run's `stopwatch.csv` - the 9.59 knob table, the 9.147 probe, the 9.154
before-and-after. Doing that by hand is how a comparison quietly gets made
across a family boundary, across sample fractions, or between a profiled run
and an unprofiled one, and the reader is never told.

So this refuses what the project's own rules refuse. `DECISIONS.md` 3.5: a
comparison is legitimate only inside ONE comparability family at ONE sample
fraction. `RUN.machine.jfr_profile` costs about 8% of a run's clock, so a
profiled side and an unprofiled side do not price each other. Each of those is
reported as a BLOCKER and the exit code is non-zero unless `--anyway` is
given, which stamps the reason into the output so it travels with the figure.

    python src/analyse/compare_runs.py <baseline> <candidate>
    python src/analyse/compare_runs.py <baseline> <candidate> --iterations 1:3
    python src/analyse/compare_runs.py <a> <b> --json

Reads only each run's own artefacts: `output/stopwatch.csv` for the phases,
`_run.json` and `_meta.json` for what the run was. Writes nothing.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from src.run import results_store                                # noqa: E402

# The phases MATSim's stopwatch names, in the order it runs them. The trailing
# summary columns of stopwatch.csv carry each as an HH:MM:SS duration.
PHASES = ('iterationStartsListeners', 'replanning', 'beforeMobsimListeners',
          'dump all plans', 'prepareForMobsim', 'mobsim',
          'afterMobsimListeners', 'scoring', 'iterationEndsListeners',
          'iteration')
TOTAL = 'iteration'


def _secs(text):
    """`HH:MM:SS` to seconds; blank or malformed to None."""
    text = (text or '').strip()
    if not text:
        return None
    parts = text.split(':')
    if len(parts) != 3:
        return None
    try:
        h, m, s = (int(p) for p in parts)
    except ValueError:
        return None
    return h * 3600 + m * 60 + s


def read_stopwatch(run):
    """[{iteration: int, <phase>: seconds}] from a run's own stopwatch."""
    d = results_store.resolve(run)
    if d is None:
        raise SystemExit(
            'no bulk on disk for %r. The stopwatch lives in the run\'s bulk, '
            'which the results store trims once its findings are extracted '
            '(9.137); a trimmed run cannot be re-timed.' % run)
    path = os.path.join(d, 'output', 'stopwatch.csv')
    if not os.path.exists(path):
        raise SystemExit('%s has no output/stopwatch.csv - it did not reach '
                         'an iteration' % run)
    # The header carries `iteration` TWICE - column 0 is the iteration number
    # and the last column is that iteration's total duration - so a DictReader
    # silently keeps only the second and every row reads as a duration. The
    # two halves are separated by one empty column name: everything after it
    # is the per-phase duration block. Parse by position, not by name.
    with io.open(path, encoding='utf-8') as fh:
        reader = csv.reader(fh, delimiter=';')
        header = next(reader, None)
        if not header:
            raise SystemExit('%s: empty stopwatch' % run)
        try:
            split = header.index('')
        except ValueError:
            raise SystemExit('%s: stopwatch has no duration block; MATSim\'s '
                             'format changed and this reader must follow it'
                             % run)
        dur = {name: split + 1 + i
               for i, name in enumerate(header[split + 1:]) if name}
        rows = []
        for r in reader:
            if not r or not r[0].strip():
                continue
            try:
                it = int(r[0].strip())
            except ValueError:
                continue
            # 'iteration' is also a PHASE name (the total), so the index
            # lives under its own key or the loop below overwrites it.
            row = {'index': it}
            for p in PHASES:
                idx = dur.get(p)
                row[p] = _secs(r[idx]) if idx is not None and idx < len(r) else None
            rows.append(row)
    return rows


def describe(run):
    """What the run WAS, from its own record - never from a document."""
    d = results_store.resolve_records(run)
    out = dict(name=run, family=None, fraction=None, threads=None,
               event_handler_threads=None, profiled=None, completion=None,
               iterations=None, scenario=None, day=None)
    if d is None:
        return out
    for fname, keys in (('_run.json', ('completion', 'fraction', 'threads',
                                       'iterations', 'scenario', 'day')),
                        ('_meta.json', ('fraction', 'threads', 'iterations',
                                        'scenario', 'day'))):
        p = os.path.join(d, fname)
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding='utf-8') as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        for k in keys:
            if out.get(k) is None and doc.get(k) is not None:
                out[k] = doc.get(k)
        for k in ('family', 'comparability_family'):
            if out['family'] is None and doc.get(k):
                out['family'] = doc[k]
    cfg = os.path.join(d, '_config.json')
    if os.path.exists(cfg):
        try:
            with io.open(cfg, encoding='utf-8') as fh:
                doc = json.load(fh)
            values = doc.get('values') if isinstance(doc, dict) else None
            src = values if isinstance(values, dict) else doc
            if isinstance(src, dict):
                if out['profiled'] is None:
                    out['profiled'] = src.get('RUN.machine.jfr_profile')
                if out['event_handler_threads'] is None:
                    out['event_handler_threads'] = src.get(
                        'RUN.machine.event_handler_threads')
        except (OSError, ValueError):
            pass
    if out['profiled'] is None:
        out['profiled'] = os.path.exists(
            os.path.join(results_store.resolve(run) or '', 'profile.jfr'))
    if out['family'] is None:
        out['family'] = _family_from_index(run)
    return out


def _family_from_index(run):
    """The run index already attributes every run to a family; ask it."""
    path = os.path.join(REPO, 'results', 'INDEX.csv')
    if not os.path.exists(path):
        return None
    try:
        with io.open(path, encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                if r.get('name') == run:
                    return r.get('family') or None
    except OSError:
        return None
    return None


def window(rows, spec, default_skip_first=True):
    """The iterations to compare. Iteration 0 pays JIT warm-up and is dropped
    unless the caller names it (9.154: 'a profile taken during warm-up
    describes the compiler rather than the model')."""
    if spec:
        first, last = (int(x) for x in spec.split(':'))
        return [r for r in rows if first <= r['index'] <= last]
    if default_skip_first:
        return [r for r in rows if r['index'] > 0]
    return list(rows)


def median(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0


def blockers(a, b):
    """What makes this pair incomparable, in the project's own terms."""
    out = []
    if a['family'] and b['family'] and a['family'] != b['family']:
        out.append('DIFFERENT COMPARABILITY FAMILIES (%s vs %s): nothing run '
                   'before a boundary compares with anything after it '
                   '(DECISIONS.md 3.5)' % (a['family'], b['family']))
    if a['fraction'] is not None and b['fraction'] is not None \
            and float(a['fraction']) != float(b['fraction']):
        out.append('DIFFERENT SAMPLE FRACTIONS (%s vs %s): the pace does not '
                   'scale linearly and the two do not price each other'
                   % (a['fraction'], b['fraction']))
    if bool(a['profiled']) != bool(b['profiled']):
        out.append('ONE SIDE IS PROFILED and the other is not (%s vs %s): the '
                   'flight recorder costs about 8%% of the clock, which is '
                   'larger than most knobs being measured'
                   % (bool(a['profiled']), bool(b['profiled'])))
    return out


def differences(a, b):
    """What actually differs between the two runs - the thing being measured."""
    out = []
    for key, label in (('threads', 'qsim threads'),
                       ('event_handler_threads', 'event handler threads'),
                       ('scenario', 'scenario'), ('day', 'day type')):
        if a.get(key) != b.get(key):
            out.append('%s: %s -> %s' % (label, a.get(key), b.get(key)))
    return out


def compare(base_name, cand_name, spec=None):
    a, b = describe(base_name), describe(cand_name)
    ra = window(read_stopwatch(base_name), spec)
    rb = window(read_stopwatch(cand_name), spec)
    if not ra or not rb:
        raise SystemExit('one side has no iterations in the window; widen '
                         '--iterations or check the run reached an iteration')
    phases = []
    for p in PHASES:
        va = [r[p] for r in ra if r[p] is not None]
        vb = [r[p] for r in rb if r[p] is not None]
        ma, mb = median(va), median(vb)
        if ma is None and mb is None:
            continue
        delta = None if (ma is None or mb is None) else mb - ma
        pct = None if (not ma or delta is None) else 100.0 * delta / ma
        # A phase that fires in only SOME of the compared iterations is not
        # part of a typical one, and a median over the iterations it does fire
        # in reads as though it were. `dump all plans` is the case that made
        # this rule: MATSim writes plans at iteration 0 and 1 and then not
        # again until writePlansInterval, so a median over iterations 1-3
        # reported 59 s of a 206 s iteration that does not pay it at all.
        phases.append(dict(phase=p, base_s=ma, candidate_s=mb,
                           delta_s=delta, delta_pct=pct,
                           base_n=len(va), candidate_n=len(vb),
                           base_of=len(ra), candidate_of=len(rb),
                           every_iteration=(len(va) == len(ra)
                                            and len(vb) == len(rb))))
    return dict(baseline=a, candidate=b,
                baseline_iterations=[r['index'] for r in ra],
                candidate_iterations=[r['index'] for r in rb],
                phases=phases, blockers=blockers(a, b),
                differences=differences(a, b))


def render(res):
    a, b = res['baseline'], res['candidate']
    w = 26
    print('=' * 78)
    print('WALL CLOCK, PHASE BY PHASE')
    print('=' * 78)
    print('  baseline   %s' % a['name'])
    print('             family=%s fraction=%s qsim_threads=%s '
          'event_threads=%s profiled=%s'
          % (a['family'], a['fraction'], a['threads'],
             a['event_handler_threads'], bool(a['profiled'])))
    print('             iterations compared: %s' % res['baseline_iterations'])
    print('  candidate  %s' % b['name'])
    print('             family=%s fraction=%s qsim_threads=%s '
          'event_threads=%s profiled=%s'
          % (b['family'], b['fraction'], b['threads'],
             b['event_handler_threads'], bool(b['profiled'])))
    print('             iterations compared: %s' % res['candidate_iterations'])
    if res['differences']:
        print('\n  WHAT DIFFERS (the thing being measured)')
        for d in res['differences']:
            print('    - %s' % d)
    else:
        print('\n  WHAT DIFFERS: nothing this tool can see from the records.')
    if res['blockers']:
        print('\n  ** NOT COMPARABLE **')
        for bl in res['blockers']:
            print('    - %s' % bl)
    print('\n%-*s %10s %10s %10s %9s' % (w, 'phase (median s)', 'baseline',
                                         'candidate', 'delta', 'delta %'))
    print('-' * 78)
    occasional = []
    for row in res['phases']:
        star = ' <' if row['phase'] == TOTAL else ''
        if not row.get('every_iteration', True):
            star = ' *'
            occasional.append(row)
        print('%-*s %10s %10s %10s %9s%s'
              % (w, row['phase'],
                 '-' if row['base_s'] is None else '%.1f' % row['base_s'],
                 '-' if row['candidate_s'] is None else '%.1f' % row['candidate_s'],
                 '-' if row['delta_s'] is None else '%+.1f' % row['delta_s'],
                 '-' if row['delta_pct'] is None else '%+.1f%%' % row['delta_pct'],
                 star))
    for row in occasional:
        print('  * %s fires in %d of %d baseline and %d of %d candidate '
              'iterations, so it is NOT part of a typical one and its median '
              'must not be read as though it were.'
              % (row['phase'], row['base_n'], row['base_of'],
                 row['candidate_n'], row['candidate_of']))
    tot = next((r for r in res['phases'] if r['phase'] == TOTAL), None)
    if tot and tot['delta_pct'] is not None:
        verdict = ('FASTER' if tot['delta_pct'] < 0 else
                   'SLOWER' if tot['delta_pct'] > 0 else 'UNCHANGED')
        print('\n  the candidate iteration is %s by %.1f%% (%.1f s -> %.1f s)'
              % (verdict, abs(tot['delta_pct']), tot['base_s'],
                 tot['candidate_s']))
    print('\n  Nothing here is a reading of any mode. A probe is plumbing and '
          'timing evidence,\n  never a result (DECISIONS.md 9.7, 9.43).')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('baseline')
    ap.add_argument('candidate')
    ap.add_argument('--iterations', metavar='FIRST:LAST',
                    help='the comparison window; iteration 0 is dropped by '
                         'default because it pays JIT warm-up')
    ap.add_argument('--anyway', action='store_true',
                    help='compare across a blocker and stamp the reason into '
                         'the output')
    ap.add_argument('--json', dest='as_json', action='store_true')
    args = ap.parse_args(argv)

    res = compare(args.baseline, args.candidate, args.iterations)
    if args.as_json:
        print(json.dumps(res, indent=1, default=str))
    else:
        render(res)
        if res['blockers'] and args.anyway:
            print('\n  --anyway was given: the figures above cross the '
                  'blocker(s) listed and\n  must carry that sentence wherever '
                  'they are quoted.')
    if res['blockers'] and not args.anyway:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
