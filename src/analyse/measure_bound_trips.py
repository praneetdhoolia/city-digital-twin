"""What a run did with the trips the demand bound to a driver (issues #86, #145).

    python src/analyse/measure_bound_trips.py --run <run> [--it N]

The four binder passes bind a passenger's trips to a named driver
(escort, lift, joint, shared), and the seed puts `ride` on every bound trip
in every plan (`B.mode.bound_passenger_placement` = every_plan, 9.164). A run
then executes each bound trip as ride or as something else. This reads, from
the run's OWN persons table (`boundRideTrips`, `carAvail`) and trips table,
the executed main mode of every bound trip - by binding type (from the city's
B2 binding tables, the plans' own source) and by car availability - and the
seed's own selected-plan ride share from the run's input plans.

`held_tour_spill` (in the same JSON): for residents, the OTHER trips of every
home-based tour that holds a held ride trip (`heldRideTrips`), by executed
main mode and routing mode - `walk|walk` a chosen walk, `walk|pt` a pt request
the router answered with a walk - with count, share and mean km, beside the
same for ride tours without a held trip and for tours with no ride at all.

Measured first on the routers pair (16 September 2026, 9.177): 109,816 bound
trips in the sample, 59.0 % executed as ride at iteration 250; car-available
escort members drove themselves 52 %, joint companions 37 %, lift passengers
65 %; car-less passengers walked or cycled 18-27 %. The binders bind 20.62 %
of core legs - the observed passenger share - so ride's target is reached
only if every bound trip rides. Nothing here is a target.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import os
import re

import pandas as pd

import city as _city
import extract_metrics as em

BINDINGS = (('escort', 'member_person_id', 'member_tour_id'),
            ('lift', 'passenger_person_id', 'passenger_tour_id'),
            ('joint', 'companion_person_id', 'companion_tour_id'),
            ('shared', 'passenger_person_id', 'passenger_tour_id'))


def binding_kind(day, persons):
    """(person, tour) -> the pass that bound it, escort winning a tie the way
    the binders run (escort, then lift, then joint, then shared)."""
    kind = {}
    plans = _city.path('demand/plans')
    trips = pd.read_csv(os.path.join(plans, 'B2_activity_trips_%s.csv' % day),
                        usecols=['person_id', 'tour_id', 'trip_seq'], dtype={'person_id': str})
    trips = trips[trips.person_id.isin(persons)].sort_values(['person_id', 'trip_seq'])
    trips['idx'] = trips.groupby('person_id').cumcount() + 1
    tour_of = {(p, i): t for p, i, t in zip(trips.person_id, trips.idx, trips.tour_id)}
    for name, pc, tc in BINDINGS:
        path = os.path.join(plans, 'B2_%s_bindings_%s.csv' % (name, day))
        if not os.path.exists(path):
            continue
        b = pd.read_csv(path, dtype={pc: str})
        for p, t in zip(b[pc], b[tc]):
            kind.setdefault((p, t), name)
    return kind, tour_of


def seed_ride_share(run_dir):
    """The ride share of core persons' SELECTED plans in the run's input plans."""
    path = os.path.join(run_dir, 'plans.xml.gz')
    if not os.path.exists(path):
        return None
    leg = re.compile(r'<leg mode="([^"]+)"')
    sub = re.compile(r'name="subpopulation"[^>]*>([^<]+)<')
    n = ride = 0
    is_person = False
    selected = False
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if '<person id=' in line:
                is_person = False
            elif 'name="subpopulation"' in line:
                is_person = sub.search(line).group(1) == 'person'
            elif '<plan ' in line:
                selected = 'selected="yes"' in line
            elif is_person and selected and '<leg mode=' in line:
                n += 1
                ride += leg.search(line).group(1) == 'ride'
    return dict(selected_plan_legs=n, ride_share_pct=round(100.0 * ride / n, 4) if n else None)


HOME_ACTIVITY = 'home'     # the plans' home activity type (build_matsim_plans.ACT_TYPES)


def _tours(trips):
    """A person's trips (sorted by trip_number) cut into home-based tours: a
    new tour starts at every trip after the first that leaves home."""
    tours, cur = [], []
    for t in trips:
        if cur and t.get('start_activity_type') == HOME_ACTIVITY:
            tours.append(cur)
            cur = []
        cur.append(t)
    if cur:
        tours.append(cur)
    return tours


def held_tour_spill(trip_rows, attrs, routing=None):
    """What the OTHER trips of a tour holding a held ride trip execute.

    A held ride trip (`heldRideTrips`, D12) may not be driven, and subtour
    mode choice changes a tour's modes together - so the rest of that tour is
    where a held trip's constraint spills. For residents' executed plans this
    returns, per tour class - `held_ride_tour` (its non-held trips), `ride_tour`
    (a tour with a ride trip and no held one) and `no_ride_tour` - the trips by
    executed main mode and routing mode (`walk|pt` is a pt request the router
    answered with a walk), each with its count, share of the class and mean
    km, and the class's trips by `carAvail`.

    `trip_rows` are trips-table dicts; `attrs` is person -> {subpopulation,
    heldRideTrips, carAvail}; `routing` is (person, trip_number) -> routingMode
    (`iteration_trips.trip_routing_modes`), or None when the plans are absent.
    """
    per_person = collections.defaultdict(list)
    for t in trip_rows:
        a = attrs.get(t['person'])
        if a is None or a.get('subpopulation') != 'person':
            continue
        per_person[t['person']].append(t)
    classes = {k: dict(n=collections.Counter(), km=collections.Counter(),
                       car=collections.Counter())
               for k in ('held_ride_tour', 'ride_tour', 'no_ride_tour')}
    for person, trips in per_person.items():
        a = attrs[person]
        held = {int(x) for x in (a.get('heldRideTrips') or '').split(',')
                if x.strip().isdigit()}
        trips.sort(key=lambda t: int(t['trip_number']))
        for tour in _tours(trips):
            nums = [int(t['trip_number']) for t in tour]

            def rmode(t):
                return (routing or {}).get((person, int(t['trip_number'])))
            if held.intersection(nums):
                cls = 'held_ride_tour'
            elif any(t['main_mode'] == 'ride' or rmode(t) == 'ride' for t in tour):
                cls = 'ride_tour'
            else:
                cls = 'no_ride_tour'
            c = classes[cls]
            for t in tour:
                if cls == 'held_ride_tour' and int(t['trip_number']) in held:
                    continue
                rm = rmode(t) if routing is not None else None
                key = '%s|%s' % (t['main_mode'], rm if rm else 'unknown')
                try:
                    km = float(t.get('traveled_distance') or 0.0) / 1000.0
                except ValueError:
                    km = 0.0
                c['n'][key] += 1
                c['km'][key] += km
                c['car'][a.get('carAvail') or '(none)'] += 1
    out = {}
    for cls, c in classes.items():
        n = sum(c['n'].values())
        out[cls] = dict(
            trips=n, km=round(sum(c['km'].values()), 1),
            by_main_and_routing_mode={
                k: dict(trips=v, share_pct=round(100.0 * v / n, 2),
                        mean_km=round(c['km'][k] / v, 3))
                for k, v in c['n'].most_common()},
            by_car_availability=dict(c['car'].most_common()))
    out['note'] = ('residents\' executed trips, tours cut at home; keys are '
                   'main_mode|routingMode (walk|pt = a pt request answered with '
                   'a walk; routing unknown when the run kept no experienced '
                   'plans); held_ride_tour counts the tour\'s trips OTHER than '
                   'its held ride trips')
    return out


def measure(run_dir, iteration=None):
    if iteration is None:
        # a stopped arm is read where its close-out read it (_metrics.json)
        try:
            with open(os.path.join(run_dir, '_metrics.json'), encoding='utf-8') as fh:
                iteration = json.load(fh).get('read_at_iteration')
        except (OSError, ValueError):
            iteration = None
    if iteration is not None:
        em._READ_AT['iteration'] = iteration
    day = (json.load(open(os.path.join(run_dir, '_meta.json'), encoding='utf-8')) or {}).get('day', 'WEEKDAY')
    # the run's own persons, from output_persons or - for a stopped arm,
    # which writes none - its input plans (iteration_reading.person_attributes)
    import iteration_reading
    attrs = iteration_reading.person_attributes(
        run_dir, ('subpopulation', 'boundRideTrips', 'heldRideTrips', 'carAvail'))
    bound = {p: ({int(x) for x in a['boundRideTrips'].split(',') if x.strip()},
                 a.get('carAvail'))
             for p, a in attrs.items()
             if a.get('subpopulation') == 'person'
             and a.get('boundRideTrips', '').strip()}
    kind, tour_of = binding_kind(day, set(bound))
    by = collections.defaultdict(collections.Counter)
    total = collections.Counter()
    for t in em.rows(run_dir, 'output_trips'):
        entry = bound.get(t['person'])
        if entry is None:
            continue
        idx, car = entry
        n = int(t['trip_number'])
        if n not in idx:
            continue
        k = kind.get((t['person'], tour_of.get((t['person'], n))), 'unknown')
        by['%s|%s' % (k, car)][t['main_mode']] += 1
        total[t['main_mode']] += 1

    # the held-tour spill reads the same trips table, plus the routing mode
    # only the experienced plans of the same iteration carry
    import iteration_trips
    plans = iteration_trips.experienced_plans_path(run_dir, em._READ_AT['iteration']
                                                   if not em._final_exists(run_dir, 'output_trips')
                                                   else None)
    residents = {p for p, a in attrs.items() if a.get('subpopulation') == 'person'}
    routing = iteration_trips.trip_routing_modes(plans, residents) if plans else None
    spill = held_tour_spill(em.rows(run_dir, 'output_trips'), attrs, routing)

    def split(c):
        s = sum(c.values())
        return {m: round(100.0 * v / s, 2) for m, v in c.most_common()} if s else {}
    n_bound = sum(total.values())
    doc = dict(run=os.path.basename(run_dir), iteration=em._READ_AT['iteration'], day=day,
               bound_persons=len(bound), bound_trips=n_bound,
               executed_pct=split(total),
               ride_executed_pct=round(100.0 * total['ride'] / n_bound, 2) if n_bound else None,
               by_binding_and_car_availability={k: dict(trips=sum(c.values()), executed_pct=split(c))
                                                for k, c in sorted(by.items())},
               seed=seed_ride_share(run_dir),
               held_tour_spill=spill,
               note='the executed main mode of every trip the demand bound to a driver, from the '
                    "run's own persons and trips tables; binding types from the city's B2 binding "
                    'tables (the plans\' source); nothing here is a target')
    with open(os.path.join(run_dir, '_bound_trips.json'), 'w', encoding='utf-8') as fh:
        json.dump(doc, fh, indent=1)
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--it', type=int, default=None)
    a = ap.parse_args()
    run_dir = em._resolve_run(a.run) if not os.path.isdir(a.run) else a.run
    doc = measure(run_dir, a.it)
    print(json.dumps(doc, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
