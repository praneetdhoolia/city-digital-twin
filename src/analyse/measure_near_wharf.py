"""The near-wharf split: the ferry's own market and what it chose (issue #94).

    python src/analyse/measure_near_wharf.py --run <run> [--it N] [--radius-m R]

Of a run's resident trips, those whose two ends lie within the transit
router's own search radius (`RUN.transit_router.search_radius_m`, the distance
within which a trip end can reach a stop at all) of two DIFFERENT ferry stops
are the ferry's captive market (the Newcastle and Stockton wharves are a
kilometre apart across the harbour, so a trip inside one catchment needs no
ferry); the reader prints that market's size, its mode split, and
the ferry boardings by wharf, all from the run's OWN schedule and tables.
DECISIONS.md 9.163 measured the market on the demand by hand (84,293 of
2,343,637 trip ends, 3.60 %); this is the same reading codified on a run, so
the next arm's near-wharf split is one command. Nothing here is a target.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os

import extract_metrics as em
import iteration_trips as itr
import registry as _registry


def nearest(x, y, stops, radius_m):
    """The id of the nearest stop within radius_m, or None."""
    best, best_d = None, radius_m
    for sid, (sx, sy) in stops.items():
        d = math.hypot(x - sx, y - sy)
        if d <= best_d:
            best, best_d = sid, d
    return best


def measure(run_dir, iteration=None, radius_m=None, submode='ferry'):
    if radius_m is None:
        radius_m = float(_registry.load().get(
            'RUN.transit_router.search_radius_m'))
    stops = em.transit_stops_of_mode(run_dir, submode)
    if not stops:
        return dict(run=os.path.basename(run_dir), submode=submode,
                    stops=0, note='the run\'s schedule serves no %s route'
                    % submode)
    person_lga = em.home_lga(run_dir)
    target = em.TARGET_LGA
    if iteration is not None:
        em._READ_AT['iteration'] = iteration
    market = collections.Counter()
    everyone = collections.Counter()
    n_resident = 0
    for t in em.rows(run_dir, 'output_trips'):
        if person_lga.get(t['person']) != target:
            continue
        n_resident += 1
        # main_mode folds every submode into `pt`; a trip is the submode's
        # when its first boarding stop is one of the submode's stops
        mode = t['main_mode']
        if mode == 'pt' and t.get('first_pt_boarding_stop') in stops:
            mode = submode
        everyone[mode] += 1
        try:
            sx, sy = float(t['start_x']), float(t['start_y'])
            ex, ey = float(t['end_x']), float(t['end_y'])
        except (TypeError, ValueError):
            continue
        a, b = nearest(sx, sy, stops, radius_m), nearest(ex, ey, stops, radius_m)
        # the market is a trip between two DIFFERENT stops' catchments: two
        # wharves a kilometre apart across the harbour share a catchment on
        # land, and a trip inside one catchment needs no ferry
        if a is not None and b is not None and a != b:
            market[mode] += 1
    n_market = sum(market.values())
    it = iteration if iteration is not None else em._READ_AT['iteration']
    boardings = collections.Counter()
    if it is not None:
        for (s, stop), c in itr.boardings(run_dir, it).items():
            if s == submode:
                boardings[stop] += c
    from report_mode_ridership import sample_fraction   # noqa: PLC0415
    frac = sample_fraction(run_dir) or None
    doc = dict(
        run=os.path.basename(run_dir), submode=submode, iteration=it,
        radius_m=radius_m, stops=len(stops),
        resident_trips=n_resident,
        market_trips=n_market,
        market_share_of_resident_trips_pct=round(100.0 * n_market / n_resident, 4) if n_resident else None,
        market_mode_split_pct={m: round(100.0 * c / n_market, 2)
                               for m, c in sorted(market.items())} if n_market else {},
        submode_share_of_market_pct=round(100.0 * market.get(submode, 0) / n_market, 3) if n_market else None,
        submode_share_of_all_resident_trips_pct=round(100.0 * everyone.get(submode, 0) / n_resident, 4) if n_resident else None,
        boardings_by_stop_sampled=dict(sorted(boardings.items())),
        boardings_per_weekday_scaled=(round(sum(boardings.values()) / frac) if frac else None),
        note='a measurement on the run\'s own schedule and tables; the '
             'market is every resident trip with both ends within the '
             'router\'s search radius of a %s stop; nothing here is a target'
             % submode)
    with open(os.path.join(run_dir, '_near_wharf.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(doc, fh, indent=1)
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--it', type=int, default=None)
    ap.add_argument('--radius-m', type=float, default=None)
    ap.add_argument('--submode', default='ferry')
    a = ap.parse_args()
    run_dir = em._resolve_run(a.run) if not os.path.isdir(a.run) else a.run
    doc = measure(run_dir, a.it, a.radius_m, a.submode)
    print(json.dumps(doc, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
