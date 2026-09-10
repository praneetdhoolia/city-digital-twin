#!/usr/bin/env python
"""What fraction of agents can choose each mode at all - the arithmetic ceiling
on every constant this project might tune.

A scoring constant reallocates agents BETWEEN the plans they hold. It cannot
give an agent a plan they have never held. So for any mode `m`, the plan-holding
coverage `c(m)` - the share of agents whose plan memory contains at least one
plan using `m` - is an arithmetic upper bound on the share `m` can reach, no
matter what its constant is set to:

    share(m) <= c(m)

and, symmetrically, the most any constant can ADD to `m` is `c(m) - share(m)`.
When a mode's deviation is larger than that headroom, the deviation is NOT a
statement about that mode's constant: it is a statement about the choice set,
and tuning the constant cannot close it. This is the quantity the 10 September
2026 assessment named as unmeasured (recommendation 9): MATSim writes
`modeChoiceCoverage1x.txt` on every arm and no module in this repository read
it.

Nothing here is assumed. The bound is arithmetic and the coverage is MATSim's
own per-iteration count; the only judgement in this file is which comparison to
print beside it.

    python src/analyse/report_choice_set_coverage.py --run <run>
    python src/analyse/report_choice_set_coverage.py --run <run> --it 100
    python src/analyse/report_choice_set_coverage.py --run <run> --trend
    python src/analyse/report_choice_set_coverage.py --run <run> --json out.json

`--against-targets` joins the city's per-mode targets and prints, for every
mode, whether its target is REACHABLE at the coverage the run actually has.

MATSim writes coverage at three memory depths - `1x`, `5x` and `10x`, the share
of agents holding the mode in their last 1, 5 or 10 plans. `1x` is the one that
bounds a constant, because selection at any iteration is over the memory the
agent holds then; the others are printed for context with `--depth`.

Reads a run directory and the city's target artefact. Writes nothing unless
`--json` is given. **Nothing here is a result**: coverage is read from whatever
iterations the run wrote, and a run whose `_run.json` does not say
`ran_to_last_iteration` is a reading at its own `reached_iteration` and nowhere
past it.
"""

import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_os.path.join(_HERE, '..'),
           _os.path.join(_HERE, '..', 'run'),
           _os.path.join(_HERE, '..', 'calibrate')):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import csv
import json
import argparse

import city as _city                                              # noqa: E402
import results_store as _store                                    # noqa: E402

# The three memory depths MATSim writes, and what each one means.
DEPTHS = {
    '1x': 'the agent\'s CURRENT plan memory - the set selection chooses from',
    '5x': 'any of the last 5 plans',
    '10x': 'any of the last 10 plans',
}
BOUNDING_DEPTH = '1x'

# The coverage file names MATSim's own mode keys; the target artefact names the
# modes a reader of the survey would recognise. `pt` covers every submode
# together, because MATSim offers `pt` as ONE alternative and the submode is
# chosen downstream by the router - so coverage cannot be split below it.
COVERAGE_TO_TARGET = {
    'car': 'car',
    'ride': 'ride',
    'walk': 'walk',
    'bike': 'bike',
    'taxi': 'taxi',
    'motorbike': 'motorbike',
    'truck': 'truck',
}
PT_SUBMODES = ('bus', 'heavy_rail', 'light_rail', 'ferry')

# The only target denominator a coverage FRACTION can bound.
SHARE_DENOMINATOR = 'resident person trips'

# Modes that are not members of `RUN.mode_choice.modes`: the person is carved
# to them and holds no alternative, so mode-choice coverage does not describe
# them and their share can legitimately exceed it. Reported, never bounded.
LOCKED_MODES = ('motorbike', 'truck')


def coverage_path(run_dir, depth):
    return _os.path.join(run_dir, 'output', 'modeChoiceCoverage%s.txt' % depth)


def read_coverage(run_dir, depth=BOUNDING_DEPTH):
    """{iteration: {mode: fraction}}, from MATSim's own tab-separated table."""
    path = coverage_path(run_dir, depth)
    if not _os.path.exists(path):
        raise SystemExit(
            'no %s in %s: this run wrote no choice-set coverage, so the bound '
            'below cannot be computed. MATSim writes it on every arm; a run '
            'that stopped before its first write has none.'
            % (_os.path.basename(path), _os.path.relpath(run_dir, _city.REPO)))
    out = {}
    with open(path, encoding='utf-8') as fh:
        rows = csv.DictReader(fh, delimiter='\t')
        for row in rows:
            it = int(row['Iteration'])
            out[it] = {k: float(v) for k, v in row.items()
                       if k != 'Iteration' and v not in ('', None)}
    return out


def read_shares(run_dir, iteration):
    """Realised mode share at `iteration`, on the same denominator the board
    uses - the target LGA's resident linked trips - via the run's own metrics
    where they exist, else None. Coverage is meaningful without it; the
    headroom column is not."""
    meta = _os.path.join(run_dir, '_metrics.json')
    if not _os.path.exists(meta):
        return None, None
    with open(meta, encoding='utf-8') as fh:
        m = json.load(fh)
    if m.get('reached_iteration') != iteration:
        # The metrics describe ONE iteration - the run's last. Comparing them
        # against coverage at a different iteration would be the exact defect
        # this file exists to report, one layer up.
        return None, m.get('reached_iteration')
    return (m.get('mode_share', {}) or {}).get('target_lga_pct'), iteration


def load_targets():
    """The city's per-mode targets, keyed by mode.

    Only targets on the RESIDENT PERSON TRIP denominator are comparable with a
    coverage fraction. Heavy rail and light rail are stated as boardings per
    weekday, truck as vehicles at count stations and freight rail as crossing
    closures; a coverage percentage cannot bound a boarding count, and pretending
    it can would be the exact defect this file reports."""
    path = _city.path('data/processed/validation/mode_targets_by_mode.csv')
    if not _os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh):
            mode = (row.get('mode') or '').strip()
            denominator = (row.get('denominator') or '').strip()
            try:
                value = float(row.get('target_pct') or '')
            except ValueError:
                continue
            out[mode] = {'target': value, 'denominator': denominator,
                         'on_trip_share': denominator == SHARE_DENOMINATOR}
    return out


def report(run_dir, iteration=None, depth=BOUNDING_DEPTH, against_targets=False):
    cov = read_coverage(run_dir, depth)
    if not cov:
        raise SystemExit('coverage table is empty')
    if iteration is None:
        iteration = max(cov)
    if iteration not in cov:
        raise SystemExit('iteration %d is not in the coverage table (it holds '
                         '%d..%d)' % (iteration, min(cov), max(cov)))
    row = cov[iteration]
    shares, share_it = read_shares(run_dir, iteration)
    targets = load_targets() if against_targets else {}

    print('choice-set coverage at iteration %d, memory depth %s (%s)'
          % (iteration, depth, DEPTHS[depth]))
    print('run: %s' % _os.path.relpath(run_dir, _city.REPO))
    if shares is None and share_it is not None:
        print('note: the run\'s _metrics.json describes iteration %s, not %d, '
              'so no share or headroom is printed - a coverage reading and a '
              'share reading from different iterations are not comparable.'
              % (share_it, iteration))
    print('')
    head = '%-12s %10s' % ('mode', 'coverage')
    if shares:
        head += ' %10s %10s' % ('share', 'headroom')
    if targets:
        head += '  %s' % 'target reachable?'
    print(head)
    print('-' * len(head))

    result = {}
    for mode in sorted(row):
        c = row[mode] * 100.0
        locked = mode in LOCKED_MODES
        line = '%-12s %9.2f%%' % (mode, c)
        entry = {'coverage_pct': round(c, 4), 'locked_carve': locked}
        if shares:
            s = shares.get(mode)
            if s is None:
                line += ' %10s %10s' % ('-', '-')
            elif locked:
                # Bounding a locked carve by mode-choice coverage would be
                # meaningless: the person never holds an alternative, so the
                # strategy that writes this table never sees them.
                entry['share_pct'] = s
                line += ' %9.2f%% %10s' % (s, 'n/a')
            else:
                entry['share_pct'] = s
                entry['headroom_pct'] = round(c - s, 4)
                line += ' %9.2f%% %9.2f%%' % (s, c - s)
        if targets and not locked:
            verdict = _reachable(mode, c, targets)
            if verdict is not None:
                entry['target_reachable'] = verdict['reachable']
                entry['target_pct'] = verdict['target']
                line += '  %s' % verdict['text']
        elif targets and locked:
            line += '  n/a - locked carve, not a choice-set member'
        result[mode] = entry
        print(line)

    print('')
    print('pt is ONE alternative in RUN.mode_choice.modes; its submodes '
          '(%s) are chosen downstream by the router, so coverage cannot be '
          'split below `pt` and every submode target shares the `pt` bound.'
          % ', '.join(PT_SUBMODES))
    print('%s are person-level LOCKED carves, not members of the choice set: '
          'the agent holds no alternative, so this table reports their share '
          'and prints no bound for them.' % ' and '.join(LOCKED_MODES))
    print('')
    print('A scoring constant reallocates between plans an agent already '
          'holds. `headroom` is therefore the MOST any constant for that mode '
          'can add to its share; a deviation larger than the headroom is a '
          'choice-set finding, not a constant finding.')
    return {'run': _os.path.basename(run_dir), 'iteration': iteration,
            'depth': depth, 'modes': result}


def _reachable(mode, coverage_pct, targets):
    key = COVERAGE_TO_TARGET.get(mode)
    if key is None and mode == 'pt':
        # Every pt submode target is bounded by the single `pt` coverage, but
        # only the submodes stated as a trip share can be compared with it at
        # all; heavy and light rail are stated as boardings per weekday.
        comparable = [t['target'] for sub in PT_SUBMODES
                      for t in [targets.get(sub)] if t and t['on_trip_share']]
        if not comparable:
            return None
        need = sum(comparable)
        ok = coverage_pct >= need
        return {'reachable': ok, 'target': need,
                'text': ('YES (submode trip-share targets sum to %.4f%%; heavy '
                         'and light rail are on a boardings basis and are not '
                         'bounded here)' % need) if ok else
                        'NO - coverage %.2f%% < %.4f%%' % (coverage_pct, need)}
    t = targets.get(key)
    if not t or not t['on_trip_share']:
        return None
    ok = coverage_pct >= t['target']
    return {'reachable': ok, 'target': t['target'],
            'text': 'YES (target %.4f%%)' % t['target'] if ok else
                    'NO - coverage %.2f%% < target %.4f%%'
                    % (coverage_pct, t['target'])}


def trend(run_dir, depth=BOUNDING_DEPTH):
    cov = read_coverage(run_dir, depth)
    its = sorted(cov)
    modes = sorted(cov[its[-1]])
    print('choice-set coverage by iteration, memory depth %s' % depth)
    print('%-10s %s' % ('iteration', ' '.join('%10s' % m for m in modes)))
    for it in its:
        print('%-10d %s' % (it, ' '.join('%9.2f%%' % (cov[it].get(m, 0.0) * 100.0)
                                         for m in modes)))
    # Where each mode's choice set effectively closed. A bare "did it change at
    # all" test answers `no` only in the last decimals and reads as growth to
    # the final iteration, which is how "the choice set is still opening" and
    # "it closed at iteration 50" can both be said of one table. Both thresholds
    # are stated so neither can be quoted without the other.
    print('')
    print('where each mode\'s choice set effectively closed. `within 1 pp` is '
          'the first iteration whose coverage is within 1 percentage point of '
          'the final value; `last move > 0.01 pp` is the last iteration at '
          'which it moved by more than a hundredth of a point:')
    print('  %-12s %12s %18s %10s' % ('mode', 'within 1 pp', 'last move >0.01pp',
                                      'final'))
    for m in modes:
        final = cov[its[-1]].get(m, 0.0)
        within = next((i for i in its
                       if abs(cov[i].get(m, 0.0) - final) <= 0.01), its[-1])
        last = its[0]
        for a, b in zip(its, its[1:]):
            if abs(cov[b].get(m, 0.0) - cov[a].get(m, 0.0)) > 0.0001:
                last = b
        print('  %-12s %12d %18d %9.2f%%' % (m, within, last, final * 100.0))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True,
                    help='a run name (resolved through the results store) or a '
                         'path to a run directory')
    ap.add_argument('--it', type=int,
                    help='iteration; default the last one in the table')
    ap.add_argument('--depth', default=BOUNDING_DEPTH, choices=sorted(DEPTHS),
                    help='plan-memory depth; default %s, the one that bounds a '
                         'constant' % BOUNDING_DEPTH)
    ap.add_argument('--trend', action='store_true',
                    help='one row per iteration, plus where each mode\'s '
                         'choice set closed')
    ap.add_argument('--against-targets', action='store_true',
                    help='join the city\'s per-mode targets and say, for each, '
                         'whether the target is reachable at this coverage')
    ap.add_argument('--json', metavar='OUT', help='also write the table as JSON')
    a = ap.parse_args()

    resolved = _store.resolve(a.run)
    if resolved is None:
        raise SystemExit('no such run: %s' % a.run)
    run_dir = resolved

    if a.trend:
        trend(run_dir, a.depth)
        return 0
    out = report(run_dir, a.it, a.depth, a.against_targets)
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump(out, fh, indent=1)
        print('\nwrote %s' % a.json)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
