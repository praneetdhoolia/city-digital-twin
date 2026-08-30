"""Linked main-mode trips for an iteration that wrote no trips table.

MATSim writes `<n>.trips.csv.gz` on `writeTripsInterval`, and every gate reader
in this repository - `measure_iteration_modes.py`, `report_mode_ridership.py` -
reads that table and nothing else. Between two of those iterations the run
still writes `<n>.experienced_plans.xml.gz` on `writePlansInterval`, and that
file is the SOURCE the trips table is derived from: `TripsAndLegsCSVWriter`
walks the experienced plans, splits them into trips at every activity that is
not a stage activity, and asks the bound `AnalysisMainModeIdentifier` for the
main mode. So a twelve-mode reading is obtainable at every plans-writing
iteration, not only at the trips-writing ones - the goal's monitoring rule
asks for it, and the readers were refusing iterations the run had fully
written.

This module rebuilds the same linked trips from the experienced plans:

  * a trip ends at every activity whose type is not a stage activity - MATSim's
    `StageActivityTypeIdentifier` rule, a type ending in `interaction`;
  * the main mode is `PtSubmodeMainModeIdentifier`'s: every scheduled transit
    leg (the run's declared `transitModes`, read from its own config) folds to
    `pt`, then MATSim's `DefaultAnalysisMainModeIdentifier` decides - a single
    leg is its own mode, otherwise the walk legs drop out and the one mode
    that remains is the answer;
  * `traveled_distance` is the sum of the legs' route distances, which is what
    the writer sums;
  * the pt submode split keeps, per trip, the in-vehicle metres on each
    boarded route's `transportMode`, resolved through the run's own schedule
    exactly as `report_mode_ridership.pt_submode_trips` does from the legs
    table.

**It is validated, not assumed, against the trips table wherever one exists**:
`--validate` reproduces an iteration that holds both and refuses to report a
difference as agreement. A derivation that disagrees with the writer on any
mode count is a defect in the derivation, and the trips table wins.

    python src/analyse/iteration_trips.py --run <run dir> --it 30
    python src/analyse/iteration_trips.py --run <run dir> --validate 1

Reads the run directory only. Writes nothing. Nothing here is a result.
"""
import argparse
import collections
import gzip
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import extract_metrics as em                                      # noqa: E402

WALK_MODES = ('walk', 'non_network_walk', 'transit_walk')


class Trip(object):
    __slots__ = ('person', 'trip_id', 'main_mode', 'traveled_distance',
                 'submode_metres', 'ambiguous')

    def __init__(self, person, trip_id, main_mode, distance, submode_metres,
                 ambiguous):
        self.person = person
        self.trip_id = trip_id
        self.main_mode = main_mode
        self.traveled_distance = distance
        self.submode_metres = submode_metres
        self.ambiguous = ambiguous


def plans_path(run_dir, iteration):
    p = os.path.join(run_dir, 'output', 'ITERS', 'it.%d' % iteration,
                     '%d.experienced_plans.xml.gz' % iteration)
    return p if os.path.exists(p) else None


def trips_table_exists(run_dir, iteration):
    base = os.path.join(run_dir, 'output', 'ITERS', 'it.%d' % iteration,
                        '%d.trips' % iteration)
    return any(os.path.exists(base + ext)
               for ext in ('.csv.gz', '.csv', '.csv.zst'))


def iterations_with_plans(run_dir):
    """Iterations whose experienced plans exist, ascending."""
    out = []
    root = os.path.join(run_dir, 'output', 'ITERS')
    if not os.path.isdir(root):
        return out
    for d in os.listdir(root):
        m = re.match(r'it\.(\d+)$', d)
        if m and plans_path(run_dir, int(m.group(1))):
            out.append(int(m.group(1)))
    return sorted(out)


def transit_modes(run_dir):
    """The run's declared transit modes, from its own config - never typed."""
    cfg = open(os.path.join(run_dir, 'config.xml'), encoding='utf-8').read()
    m = re.search(r'name="transitModes" value="([^"]*)"', cfg)
    if not m:
        return set()
    return set(x.strip() for x in m.group(1).split(',') if x.strip())


def main_mode(leg_modes, fold):
    """`PtSubmodeMainModeIdentifier` over `DefaultAnalysisMainModeIdentifier`.

    Returns (mode, ambiguous). `ambiguous` is True when more than one non-walk
    mode survives the fold, which the stock identifier refuses outright - the
    derivation reports the count rather than hiding a guess.
    """
    folded = ['pt' if (m in fold and m != 'pt') else m for m in leg_modes]
    if len(folded) == 1:
        return folded[0], False
    non_walk = []
    for m in folded:
        if m not in WALK_MODES and m not in non_walk:
            non_walk.append(m)
    if not non_walk:
        return 'walk', False
    if len(non_walk) == 1:
        return non_walk[0], False
    return non_walk[0], True


def derive(run_dir, iteration, route_mode=None):
    """Every linked trip of one iteration, from its experienced plans.

    `route_mode` is `extract_metrics.transit_route_modes(run_dir)`; pass it in
    when deriving several iterations so the schedule is read once.
    """
    path = plans_path(run_dir, iteration)
    if path is None:
        raise SystemExit('iteration %d wrote no experienced plans under %s'
                         % (iteration, run_dir))
    if route_mode is None:
        route_mode = em.transit_route_modes(run_dir)
    fold = transit_modes(run_dir)

    trips = []
    unknown_routes = 0
    with gzip.open(path, 'rb') as fh:
        person = None
        in_selected = False
        legs = []          # (mode, distance, submode or None)
        n_trip = 0
        for ev, el in ET.iterparse(fh, events=('start', 'end')):
            if ev == 'start':
                if el.tag == 'person':
                    person = el.get('id')
                    n_trip = 0
                elif el.tag == 'plan':
                    # experienced plans carry one plan per person; be explicit
                    in_selected = el.get('selected', 'yes') != 'no'
                    legs = []
                continue
            # end events
            if el.tag == 'activity' and in_selected:
                typ = el.get('type') or ''
                if typ.endswith('interaction'):
                    el.clear()
                    continue
                if legs:
                    n_trip += 1
                    modes = [m for m, _, _ in legs]
                    mode, amb = main_mode(modes, fold)
                    dist = sum(d for _, d, _ in legs)
                    sub = collections.Counter()
                    for m, d, sm in legs:
                        if sm is not None:
                            sub[sm] += d
                    trips.append(Trip(person, '%s_%d' % (person, n_trip),
                                      mode, dist, sub, amb))
                    legs = []
                el.clear()
            elif el.tag == 'leg' and in_selected:
                mode = el.get('mode') or ''
                dist = 0.0
                sm = None
                route = el.find('route')
                if route is not None:
                    try:
                        dist = float(route.get('distance') or 0.0)
                    except ValueError:
                        dist = 0.0
                    if route.get('type') == 'default_pt' and route.text:
                        try:
                            j = json.loads(route.text)
                            key = (j.get('transitLineId'),
                                   j.get('transitRouteId'))
                            sm = route_mode.get(key)
                            if sm is None:
                                unknown_routes += 1
                        except ValueError:
                            unknown_routes += 1
                legs.append((mode, dist, sm))
                el.clear()
            elif el.tag == 'person':
                el.clear()
    return trips, unknown_routes


def boardings(run_dir, iteration, route_mode=None):
    """Every pt boarding of one iteration: (submode, boarding stop name) -> n.

    9.130: a boardings-basis target counts every traveller who boards, resident
    or not, exactly as the publication counts them - so this reads every
    subpopulation's selected plan, one boarding per pt leg, resolved to the
    boarded route's transportMode through the run's own schedule and to the
    access stop's name through the same schedule.
    """
    path = plans_path(run_dir, iteration)
    if path is None:
        raise SystemExit('iteration %d wrote no experienced plans under %s'
                         % (iteration, run_dir))
    if route_mode is None:
        route_mode = em.transit_route_modes(run_dir)
    stop_name = em.transit_stop_names(run_dir)
    out = collections.Counter()
    with gzip.open(path, 'rb') as fh:
        in_selected = False
        for ev, el in ET.iterparse(fh, events=('start', 'end')):
            if ev == 'start':
                if el.tag == 'plan':
                    in_selected = (el.get('selected') == 'yes')
                continue
            if el.tag == 'route' and in_selected and el.get('type') == 'default_pt' and el.text:
                try:
                    j = json.loads(el.text)
                except ValueError:
                    continue
                sm = route_mode.get((j.get('transitLineId'), j.get('transitRouteId')))
                if sm is None:
                    continue
                out[(sm, stop_name.get(j.get('accessFacilityId'), ''))] += 1
            if el.tag in ('leg', 'activity', 'person'):
                el.clear()
    return out


def as_trip_rows(trips):
    """The trips-table columns the readers consume, one dict per trip."""
    for t in trips:
        yield {'person': t.person, 'trip_id': t.trip_id,
               'main_mode': t.main_mode,
               'traveled_distance': '%d' % round(t.traveled_distance)}


def submodes_by_trip(trips):
    """(person, trip_id) -> {submode: metres}, for pt trips that boarded."""
    return {(t.person, t.trip_id): t.submode_metres
            for t in trips if t.submode_metres}


def validate(run_dir, iteration):
    """Reproduce an iteration that holds BOTH sources; every mode must agree."""
    if not trips_table_exists(run_dir, iteration):
        raise SystemExit('iteration %d has no trips table to validate against'
                         % iteration)
    import csv
    table = collections.Counter()
    table_km = collections.Counter()
    n_table = 0
    with em.open_output(run_dir, 'ITERS/it.%d/%d.trips' % (iteration, iteration)) as fh:
        for r in csv.DictReader(fh, delimiter=';'):
            table[r['main_mode']] += 1
            table_km[r['main_mode']] += float(r['traveled_distance'] or 0)
            n_table += 1
    trips, unknown = derive(run_dir, iteration)
    got = collections.Counter(t.main_mode for t in trips)
    got_km = collections.Counter()
    for t in trips:
        got_km[t.main_mode] += t.traveled_distance
    amb = sum(1 for t in trips if t.ambiguous)
    print('VALIDATE iteration %d: trips table %d rows, derived %d trips, '
          '%d ambiguous main modes, %d unresolved transit routes'
          % (iteration, n_table, len(trips), amb, unknown))
    print('%-14s %10s %10s %8s   %12s %12s'
          % ('mode', 'table', 'derived', 'diff', 'table km', 'derived km'))
    ok = True
    for m in sorted(set(table) | set(got)):
        d = got[m] - table[m]
        km_t, km_g = table_km[m] / 1000.0, got_km[m] / 1000.0
        km_ok = abs(km_t - km_g) <= 0.001 * max(km_t, 1.0)
        if d or not km_ok:
            ok = False
        print('%-14s %10d %10d %+8d   %12.1f %12.1f%s'
              % (m, table[m], got[m], d, km_t, km_g, '' if (not d and km_ok) else '  MISMATCH'))
    print('RESULT: %s' % ('AGREES on every mode count and distance'
                          if ok else 'DISAGREES - the trips table wins; fix the derivation'))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--it', type=int, help='iteration to derive and summarise')
    ap.add_argument('--validate', type=int, metavar='IT',
                    help='iteration holding BOTH a trips table and experienced '
                         'plans; the derivation must reproduce the table')
    a = ap.parse_args()
    if a.validate is not None:
        raise SystemExit(0 if validate(a.run, a.validate) else 1)
    have = iterations_with_plans(a.run)
    if not have:
        raise SystemExit('no experienced plans under %s' % a.run)
    it = a.it if a.it is not None else have[-1]
    trips, unknown = derive(a.run, it)
    c = collections.Counter(t.main_mode for t in trips)
    print('iteration %d: %d linked trips, %d unresolved transit routes' % (it, len(trips), unknown))
    for m, n in sorted(c.items()):
        print('  %-12s %d' % (m, n))


if __name__ == '__main__':
    main()
