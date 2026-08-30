#!/usr/bin/env python
"""Score a SINGLE ITERATION's mode share against the calibration targets.

`fit.py` scores a FINISHED run from `output_trips`. There was no way to ask the
same question of an arm still running, or of an arm stopped before it wrote one
— and the gap was filled by reading `modestats.csv`, which answers a DIFFERENT
question and reads as though it answered this one.

**`modestats.csv` counts PLANNED modes.** It is written at `IterationEnds`,
after the `AfterMobsim` restore that puts an unpaired ride leg's mode back
(DECISIONS.md 9.81), so a leg the agent physically WALKED is counted as a ride
trip. MATSim's per-iteration `<n>.trips.csv.gz` is derived from the EVENTS
stream instead, so it records what happened, and it is already linked and
already main-mode — the same quantity `output_trips` carries and `fit.py`
scores.

This module reads that file for one iteration and hands it to `fit.py`'s OWN
`score_mode_share`, so the folds (the survey's vehicle-driver category holding
motorcyclists; its residual category holding taxi alongside bicycle) and the
target vintage filter cannot drift from the real fit. Nothing is re-implemented
here except the choice of which file to read.

    python src/analyse/measure_iteration_modes.py --run <run dir> --it 150
    python src/analyse/measure_iteration_modes.py --run <run dir> --all

Per-iteration trips are written on the interval the run's config declares, so
not every iteration has one; `--all` lists what the run actually holds. A run
still writing the newest iteration will have that file incomplete — prefer the
previous available one.

Reads the run directory only. Writes nothing. Nothing here is a result: a run
without `_run.json` is not a result no matter how it scores.
"""

# City-relative paths resolve through src/city.py: `data/...` names a
# location inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_os.path.join(_HERE, '..'), _os.path.join(_HERE, '..', 'calibrate')):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import csv
import glob
import json
import argparse
import collections

import extract_metrics as em                                      # noqa: E402
import fit as fitmod                                              # noqa: E402

TRIPS_STEM = 'ITERS/it.%d/%d.trips'


def iterations_with_trips(run_dir):
    """Iterations whose per-iteration trips table exists, ascending."""
    found = []
    pattern = _os.path.join(run_dir, 'output', 'ITERS', 'it.*')
    for d in glob.glob(pattern):
        try:
            n = int(_os.path.basename(d).split('.', 1)[1])
        except (IndexError, ValueError):
            continue
        for ext in ('.csv.gz', '.csv'):
            if _os.path.exists(_os.path.join(d, '%d.trips%s' % (n, ext))):
                found.append(n)
                break
    return sorted(found)


def trip_rows(run_dir, iteration):
    """The iteration's linked trips, as trips-table rows.

    From `<n>.trips.csv.gz` when the run wrote one; otherwise derived from the
    same iteration's experienced plans by `iteration_trips.py`, which is
    validated to reproduce the table exactly wherever both exist. Returns
    (rows, source) so a reader can say which it read.
    """
    stem = TRIPS_STEM % (iteration, iteration)
    base = _os.path.join(run_dir, 'output', stem)
    if any(_os.path.exists(base + ext) for ext in ('.csv.gz', '.csv', '.csv.zst')):
        with em.open_output(run_dir, stem) as fh:
            return list(csv.DictReader(fh, delimiter=';')), 'trips table'
    import iteration_trips as itr
    if itr.plans_path(run_dir, iteration) is None:
        raise SystemExit('iteration %d wrote neither a trips table nor '
                         'experienced plans under %s' % (iteration, run_dir))
    trips, _ = itr.derive(run_dir, iteration)
    return list(itr.as_trip_rows(trips)), 'experienced plans (derived)'


def mode_share_at(run_dir, iteration, person_lga, rows=None):
    """`extract_metrics.mode_share`'s quantity, for ONE iteration's trips.

    Same shape the finished-run path produces, so `fit.score_mode_share` reads
    it without knowing which of the two produced it. `rows` lets a caller that
    already holds the iteration's trips pass them in.
    """
    everyone = collections.Counter()
    target = collections.Counter()
    unknown = 0
    if rows is None:
        rows, _ = trip_rows(run_dir, iteration)
    for trip in rows:
        mode = trip['main_mode']
        everyone[mode] += 1
        who = person_lga.get(trip['person'])
        if who == em.TARGET_LGA:
            target[mode] += 1
        elif who is None:
            unknown += 1

    def pct(counter):
        total = sum(counter.values())
        if not total:
            return {}
        return {k: round(100.0 * v / total, 4)
                for k, v in sorted(counter.items())}

    return dict(all_residents_pct=pct(everyone),
                all_residents_trips=sum(everyone.values()),
                target_lga_pct=pct(target),
                target_lga_trips=sum(target.values()),
                target_lga_counts=dict(target),
                persons_without_home_lga=unknown)


def score(run_dir, iteration, person_lga=None):
    """Score one iteration exactly as `fit.py` would score a finished run."""
    if person_lga is None:
        person_lga = em.home_lga()
    share = mode_share_at(run_dir, iteration, person_lga)
    out = {'unscorable': []}
    scored = fitmod.score_mode_share(fitmod.load_targets(),
                                     {'mode_share': share}, out)
    return share, scored, out


def report(run_dir, iteration, person_lga=None):
    share, scored, out = score(run_dir, iteration, person_lga)
    print('=' * 78)
    print('run       %s' % _os.path.basename(_os.path.normpath(run_dir)))
    print('iteration %d' % iteration)
    print('basis     linked main mode from the iteration trips table '
          '(events-derived)')
    print('=' * 78)
    counts = share['target_lga_counts']
    print('%-12s %14s %14s %12s'
          % ('mode', 'all resident%', 'target LGA%', 'LGA trips'))
    for mode in sorted(set(share['all_residents_pct']) | set(counts)):
        print('%-12s %14.2f %14.2f %12d'
              % (mode,
                 share['all_residents_pct'].get(mode, 0.0),
                 share['target_lga_pct'].get(mode, 0.0),
                 counts.get(mode, 0)))
    print('%-12s %14d %14d'
          % ('TOTAL trips', share['all_residents_trips'],
             share['target_lga_trips']))

    if not scored or not scored.get('errors'):
        print('\nno mode-share target of the base-year vintage was scorable')
        return share, scored, out
    print()
    print('%-22s %10s %10s %10s %10s'
          % ('survey category', 'modelled', 'observed', 'abs pp', 'pct err'))
    for e in scored['errors']:
        print('%-22s %10.2f %10.2f %+10.2f %+9.1f%%   [%s=%s]'
              % (e['hts_category'], e['modelled'], e['observed'],
                 e['abs_error'], e['pct_error'],
                 e['target_id'], e['matsim_mode']))
    print('%-22s %32s %10.3f'
          % ('MEAN ABS ERROR', '', scored['mean_abs_pp']))
    for u in out['unscorable']:
        print('  UNSCORABLE %-8s %-16s %s'
              % (u['target_id'], u['note'], u['reason'][:70]))
    return share, scored, out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run', required=True, help='run directory')
    ap.add_argument('--it', type=int, help='iteration to score')
    ap.add_argument('--all', action='store_true',
                    help='score every iteration whose trips table exists')
    ap.add_argument('--json', action='store_true',
                    help='emit the scored block as JSON instead of a table')
    a = ap.parse_args()

    run_dir = a.run
    if not _os.path.isdir(run_dir):
        raise SystemExit('no such run directory: %s' % run_dir)
    have = iterations_with_trips(run_dir)
    if not have:
        raise SystemExit(
            'no per-iteration trips table under %s; the run writes them on the '
            'interval its config declares' % _os.path.join(run_dir, 'output',
                                                           'ITERS'))
    if a.all:
        wanted = have
    elif a.it is not None:
        if a.it not in have:
            raise SystemExit('iteration %d has no trips table; this run holds %s'
                             % (a.it, ', '.join(str(i) for i in have)))
        wanted = [a.it]
    else:
        wanted = [have[-1]]

    person_lga = em.home_lga()
    if a.json:
        blocks = []
        for it in wanted:
            share, scored, out = score(run_dir, it, person_lga)
            blocks.append(dict(iteration=it, mode_share=share, scored=scored,
                               unscorable=out['unscorable']))
        print(json.dumps(blocks, indent=2))
        return
    for it in wanted:
        report(run_dir, it, person_lga)
        print()


if __name__ == '__main__':
    main()
