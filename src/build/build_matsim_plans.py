#!/usr/bin/env python
"""MATSim plans (population_v6) from the B2 activity chains, one file per day type.

Consumes `demand/plans/B2_activity_trips_<DAY>.csv` and writes
`demand/plans/matsim/population_<DAY>.xml.gz`. Nothing here invents travel: the
activity sequence, its coordinates and its timing all come from B2. What this
adds is the two things MATSim needs and B2 deliberately does not carry -
a mode on every leg, and person attributes for the scoring and choice modules.

Mode is a seed, not a prediction
--------------------------------
DECISIONS.md 9 keeps mode out of B2 on purpose: assigning it there would
pre-empt the question the model exists to answer. But a MATSim plan file cannot
omit it - every leg needs a mode to be routed and scored at iteration 0. So a
mode is drawn here **per tour**, from a car-availability-conditioned
multinomial, and is an *initial condition* for the co-evolutionary loop, not an
output. Two properties make that safe:

  * it is drawn per **tour**, never per leg, so a car that leaves home comes
    home again and `SubtourModeChoice`'s mass conservation for chain-based modes
    holds from iteration 0;
  * the shares are recorded in DECISIONS.md as assumed with a sweep range, and
    P4 is expected to move them.

The full-day chains B2 now produces are what make this work at all. Under the P1
chains every agent had exactly one subtour, so a per-tour draw would have fixed
one mode for the entire day.

Determinism: one seeded generator, persons consumed in the file's own sorted
order, so the same B2 reproduces the same plans byte for byte.
"""

# City-relative paths resolve through src/city.py: `data/...` names a
# location inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', 'src'))
import city as _city  # noqa: E402
import os
import csv
import json
import argparse
import collections

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from det_io import gzip_writer
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import registry as _registry  # noqa: E402
CFG = _registry.load()
# Whether `ride` is withheld from a person with nobody to drive them. Derived
# from B1 household composition; see DECISIONS.md 15 and src/java/citysim/.
RIDE_REQUIRES_DRIVER = CFG.get('B.population.ride_requires_household_driver')
# Share of persons with a bicycle available. Until this existed, car was the
# only mode whose ownership was modelled and bike was silently universal -
# issue #29, DECISIONS.md 9.39. Assumed and swept; 1.0 reproduces the old
# behaviour.
BIKE_AVAILABLE_RATE = CFG.get('B.population.bike_available_rate')
# An external boundary agent is a household-less boundary treatment, not a
# synthesised person: its attributes are placeholders, and its ride availability
# follows from having no household at all rather than from an unknown one.
EXTERNAL_PROFILE = CFG.get('B.external.agent_profile')
EXTERNAL_RIDE_AVAILABLE = CFG.get('B.external.agent_ride_available')

# Motorbike (issue #49, DECISIONS.md 9.52): a PERSON-LEVEL carve from
# car-driver demand. A licensed, car-available person becomes a motorbike
# user with the probability that makes carved persons' trips
# B.motorbike.trip_share of all trips (anchored on the MEASURED census G62
# journey-to-work share; the commute->all-purpose transfer is the assumption,
# declared and swept - zero turns the mode off). Their day LOCKS to the mode:
# vehicle continuity is chain-based by nature, and no preference observation
# exists to let motorbike compete in mode choice, so a locked carve is the
# honest form (the same reasoning that locks through and freight agents).
# The draw is a HASH of the person id and the master seed - deterministic,
# identical across day types, and consuming no rng stream, so every existing
# draw sequence is byte-identical to the pre-motorbike build.
MOTORBIKE_SHARE = CFG.get('B.motorbike.trip_share')
_MOTORBIKE_Q = {'q': 0.0}   # solved in main() from the eligible share

import hashlib as _hashlib  # noqa: E402


def motorbike_user(pid):
    if _MOTORBIKE_Q['q'] <= 0.0:
        return False
    h = _hashlib.sha256(('motorbike|%s|%d' % (pid, SEED)).encode()).hexdigest()
    return int(h[:12], 16) / float(1 << 48) < _MOTORBIKE_Q['q']
# An escort trip's traveller is the driver - the identity that already limits
# HX generation to licence holders, carried through to mode choice: a person
# whose day includes an escort activity is denied `ride` FOR THAT DAY TYPE.
# Measured motivation: 4,791 escort trips on the relaxed 25% arm were made BY
# ride, a passenger being driven in order to convey somebody (DECISIONS.md
# 9.46). Day-plan level because PermissibleModesCalculator is per plan; the
# collateral - the escorting driver cannot be driven on their OTHER tours the
# same day - is stated, small, and plausibly the truth.
ESCORT_EXCLUDES_RIDE = CFG.get('B.activity.escort_excludes_ride')
# The bike age gate (DECISIONS.md 9.84, #50), applied to the SEED as well as
# to replanning: AvailabilityModesCalculator governs only NEW mode choices
# and never strips a mode from a held plan, so an under-age person seeded
# bike would hold an illegal plan ChangeExpBeta can re-select forever (the
# 9.15 class, measured for ride at 4,723 surviving legs). Taxi needs no seed
# gate - it is not in either declared seed split. Zero disables.
BIKE_MIN_AGE = CFG.get('B.population.bike_min_age')

PLANS = _city.path('demand/plans')
POP = _city.path('demand/population')
OUT = os.path.join(PLANS, 'matsim')
SEED = CFG.get('B.seed.master')
# the CITY's day-type vocabulary, not the framework's (city.json day_types)
DAY_TYPES = list(_city.descriptor()['day_types'])

# Seed mode split: UNINFORMED, uniform over the modes a person can use.
#
# The P3 seed was positioned so the blended share landed near the HTS aggregate
# (car 55.7 against 57.5, pt 4.0 against 3.4). That is defensible as a
# convergence aid and indefensible as an initial condition for a calibration
# whose target *is* the HTS mode share: a model that starts at the answer cannot
# be said to have found it. Worse, until P4 fixed the mode-choice configuration
# `ride` was not in MATSim's choice set at all, so the seeded 18.6% car-passenger
# share was not an initial condition but the model's output (DECISIONS.md 9.6).
#
# The only thing conditioned on here is **car availability**, which is a
# population attribute from B1, not a behavioural prior. Within the modes a
# person can actually use, the draw is uniform. This is deliberately a bad guess:
# it starts the co-evolution far from the observed point so that arriving there
# is evidence about the model rather than about the seed.
def _seed_table(key):
    """A declared seed split as the {car_available: [(mode, share)]} form used here.

    JSON has no boolean keys, so the field names the two cases; the mapping back
    happens once, here, rather than at each of the three call sites.
    """
    table = CFG.get(key)
    return {True: sorted(table['car_available'].items()),
            False: sorted(table['no_car'].items())}


# The uniform seed: deliberately a bad guess, so that arriving at the observed
# point is evidence about the model rather than about the seed.
SEED_MODE_SPLIT = _seed_table('B.mode.seed_split')
# The sweep is over WHICH SEED IS USED, not over the shares - the two entries
# are the only two seeds this script can produce, and DECISIONS.md 9.7 reports
# the measured difference between them.
SEED_MODE_SWEEP = {'seed_mode': tuple(
    CFG.sweep('B.mode.seed_split_informed')['categorical'])}
# The informed seed the uniform one replaced, retained so that "the result does
# not depend on the seed" can be tested rather than asserted (DECISIONS.md 9.6);
# selected with --seed-mode informed.
SEED_MODE_SPLIT_INFORMED = _seed_table('B.mode.seed_split_informed')

# DECISIONS.md 9.68. A BOUND serve tour seeds as the mode that can actually
# serve its booked passenger (the pairing engine pairs ride legs with CAR
# legs only - measured: the uniform seed's 0.2 car probability WAS the
# converged arm's 0.196 outbound pairing ceiling), and a passenger tour
# covered by serve tours in BOTH directions seeds at the coherent two-sided
# state. Seeds only: SubtourModeChoice remains free to move both.
SERVE_TOUR_SEED = CFG.get('B.mode.serve_tour_seed')
BOUND_PASSENGER_SEED = CFG.get('B.mode.bound_passenger_seed')
# DECISIONS.md 9.120. `full_choice_set` seeds every person with ONE PLAN PER
# MODE they may use - car, walk, bike, pt, taxi as availability allows, and
# the bound-ride variant where the demand declared a driver - so that the
# whole choice set is executed and SCORED inside the first few iterations
# (MATSim runs a random UNSCORED plan before it consults the selector, read
# from the pinned jar's GenericPlanStrategyImpl.run). Measured on the F14 arm
# at iteration 30: 65% of the agents still cycling held NO bike-free plan
# in memory - the uniform draw had put bike on a fifth of tours and random
# innovation had not yet offered the alternative. No mode is favoured: each
# plan is one mode, once. `uniform_draw` is the pre-9.120 seed.
SEED_METHOD = CFG.get('B.mode.seed_method')
# The taxi age gate the run enforces (citysim.AvailabilityModesCalculator):
# a seeded taxi plan for a person under it would be an illegal plan in
# memory (the 9.15 class), so the seed reads the same declared value.
TAXI_MIN_AGE = CFG.get('B.taxi.min_unaccompanied_age')
EMPTY_SET = frozenset()
HTS_TARGET_LGA = _city.target_lga()


def hts_mode_share():
    """Both HTS 2024/25 aggregations, derived from the file rather than typed.

    They are different quantities and the difference matters:

    * **unlinked, five LGAs** - trips-weighted over the whole study area, with
      the walk stage of a public transport trip counted as its own walk trip.
      This is the aggregate the P3 seed was positioned against.
    * **linked, Newcastle LGA** - the published `MODE_SHARE` column, where a
      walk-plus-bus trip counts once, as public transport, so `walk linked` is
      0.0 by construction.

    MATSim's `modestats` reports the **main mode of a trip**, which is the
    linked concept, and the pre-registered calibration targets V202-V207 are the
    linked Newcastle-LGA figures (DECISIONS.md 12.1). So the linked aggregate is
    the one a fit is computed against; the unlinked one is kept only because it
    is what the P3 seed was compared to, and dropping it would make that
    comparison unreproducible.

    Read through the city's reader-shape adapter (issue #62 A5): the survey's
    own labels and vintage spelling live in
    cities/<city>/extract/reader_shapes.py, and this function sees only the
    declared mode categories of config/schema/reader_shapes.json.
    """
    table = _city.readers().mode_share_table()
    t = collections.Counter()
    for r in table:
        t[r['mode_category']] += r['trips'] or 0.0
    tot = sum(t.values())
    unlinked = {'car': 100 * t['car_driver'] / tot,
                'ride': 100 * t['car_passenger'] / tot,
                'walk': 100 * (t['walk_only'] + t['walk_linked']) / tot,
                'pt': 100 * t['public_transport'] / tot,
                'bike_other': 100 * t['other'] / tot}
    n = {r['mode_category']: r['linked_share_pct'] for r in table
         if r['area_name'] == HTS_TARGET_LGA}
    linked = {'car': float(n['car_driver']), 'ride': float(n['car_passenger']),
              'walk': float(n['walk_only']), 'pt': float(n['public_transport']),
              'bike_other': float(n['other'])}
    return ({k: round(v, 2) for k, v in unlinked.items()},
            {k: round(v, 2) for k, v in linked.items()})

# Activity types carried through to the scoring configuration.
ACT_TYPES = ('home', 'work', 'education', 'shopping', 'other', 'business')
# A SECOND COPY of C.scoring.activity_typical_duration_s lived here, with six
# keys against the field's seven - it had no `escort`, the drop-off that comes
# with the serve-passenger tour purpose. Two tables of the same quantity, one of
# them silently short.
TYPICAL_DURATION_S = CFG.get('C.scoring.activity_typical_duration_s')
# Proportional sweep on every typical duration. Not Newcastle-specific: this is
# MATSim's scoring shape parameter, not an observable local quantity.
TYPICAL_DURATION_SWEEP = CFG.sweep(
    'C.scoring.activity_typical_duration_s')['proportional']


def hhmmss(s):
    s = max(0, int(round(s)))
    return '%02d:%02d:%02d' % (s // 3600, (s % 3600) // 60, s % 60)


def esc(v):
    return (str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def load_person_attributes(rng_bike):
    """car, ride and BIKE availability plus demographics, by person id.

    `rideAvail` is DERIVED, not assumed: a person may be a car passenger only if
    their household holds at least one vehicle AND contains at least one OTHER
    licence holder who could actually drive them. MATSim's standard treatment
    lets any agent be a passenger on any trip, which DECISIONS.md 9.10 measures
    at 0.72 of legs against an observed 0.206 - 5.9 people in every car.

    `bikeAvail` is ASSUMED, not derived - the census carries no bicycle
    variable - and is drawn per person at B.population.bike_available_rate from
    its own seeded stream, so the same seed reproduces the same availability
    (issue #29, DECISIONS.md 9.39).

    Core MATSim honours `carAvail` but has no equivalent for `ride` or `bike`,
    so both attributes are consumed by
    src/java/citysim/AvailabilityModesCalculator.

    `householdId` is carried through unchanged. It is not a behavioural
    parameter and nothing chooses it: it is the B1 membership that makes a
    household-coupled mechanism possible at all. Two consumers need it and
    neither could derive it - src/java/citysim/RidePairingEngine, which finds
    the driver a `ride` leg rides with, and src/run/sample_population.py, which
    must keep WHOLE households or destroy that coupling in a way that varies
    with the sample fraction (DECISIONS.md 9.45). Carrying it as a person
    attribute rather than as a side file means there is ONE mechanism, and one
    place it can be wrong.
    """
    p = pd.read_csv(os.path.join(POP, 'B1_synthetic_population.csv'),
                    usecols=['person_id', 'household_id', 'age', 'car_available',
                             'licence_holder', 'employment_status', 'student_status',
                             'mobility_impairment_flag'])

    if RIDE_REQUIRES_DRIVER:
        # licence holders per household, and whether the household has a vehicle
        drivers = p.groupby('household_id')['licence_holder'].sum()
        vehicles = p.groupby('household_id')['household_vehicles'].max() \
            if 'household_vehicles' in p.columns else None
        if vehicles is None:
            veh = pd.read_csv(os.path.join(POP, 'B1_households.csv'),
                              usecols=['household_id', 'household_vehicles'])
            vehicles = veh.set_index('household_id')['household_vehicles']
        hh_drivers = p['household_id'].map(drivers).fillna(0).astype(int)
        hh_vehicles = p['household_id'].map(vehicles).fillna(0).astype(int)
        # "another" driver: subtract the person's own licence
        other_drivers = hh_drivers - p['licence_holder'].astype(int)
        ride_ok = ((hh_vehicles > 0) & (other_drivers > 0)).astype(int)
    else:
        ride_ok = pd.Series(1, index=p.index)

    p = p.assign(ride_avail=ride_ok.values,
                 bike_avail=(rng_bike.random(len(p))
                             < BIKE_AVAILABLE_RATE).astype(int))
    return {
        int(r.person_id): (int(r.car_available), int(r.age), int(r.licence_holder),
                           str(r.employment_status), str(r.student_status),
                           int(r.mobility_impairment_flag), int(r.ride_avail),
                           int(r.bike_avail), int(r.household_id))
        for r in p.itertuples()
    }


def pick_mode(car_available, u, table_by_avail=None, ride_available=True,
              bike_available=True):
    """Draw a seed mode from the modes this person may actually use.

    `ride_available` and `bike_available` matter as much as `car_available`.
    MATSim's PermissibleModesCalculator governs only NEW mode choices - it never
    strips a mode from a plan the agent already holds - so seeding a person with
    a mode they may not use leaves an illegal plan in their memory that
    ChangeExpBeta can re-select forever. Measured for ride: 4,723 such legs
    survived 30 iterations before this was fixed.
    """
    table = (table_by_avail or SEED_MODE_SPLIT)[bool(car_available)]
    drop = ({'ride'} if not ride_available else set()) | \
           ({'bike'} if not bike_available else set())
    if drop:
        table = [(m, w) for m, w in table if m not in drop]
        total = sum(w for _, w in table)
        table = [(m, w / total) for m, w in table]   # renormalise, do not reweight
    x = u()
    c = 0.0
    for mode, p in table:
        c += p
        if x <= c:
            return mode
    return table[-1][0]


def stream_persons(path):
    """Yield (person_id, [legs]) from a B2 file already sorted by person id."""
    with open(path, newline='', encoding='utf-8') as f:
        cur, rows = None, []
        for r in csv.DictReader(f):
            pid = int(r['person_id'])
            if cur is not None and pid != cur:
                yield cur, rows
                rows = []
            cur = pid
            rows.append(r)
        if cur is not None:
            yield cur, rows


def write_day(day, attrs, rng, report, seed_table=None):
    src = os.path.join(PLANS, 'B2_activity_trips_%s.csv' % day)
    dst = os.path.join(OUT, 'population_%s.xml.gz' % day)
    # DECISIONS.md 9.60: the non-household lift bindings. A bound passenger
    # gains `ride` availability (a specific driver's re-targeted escort tour
    # now exists to carry them - the availability identity is satisfied by
    # construction) and carries the driver's household id as `liftHousehold`,
    # which widens citysim.RidePairingEngine's candidate search to that
    # household. The binding is an eligibility, not a guarantee.
    # 9.85: the DECLARED driver identity, from every binding table that
    # names one. All three have always carried it and this builder has
    # always discarded it, so citysim.RidePairingEngine had to RE-DISCOVER
    # a declared pair from geometry and the clock - which MATSim's own
    # TimeAllocationMutator then breaks, moving the two members
    # independently at a range the registry did not declare until 9.85.
    bound_driver = {}     # passenger pid -> [driver pids, ordered]

    def bind(passenger, driver):
        bound_driver.setdefault(passenger, [])
        if driver not in bound_driver[passenger]:
            bound_driver[passenger].append(driver)

    lift_hh = {}          # passenger pid -> [driver household ids, ordered]
    lift_cover = {}       # (passenger pid, tour_id) -> set of directions
    lifts = os.path.join(PLANS, 'B2_lift_bindings_%s.csv' % day)
    if os.path.exists(lifts):
        with open(lifts, encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                p = int(r['passenger_person_id'])
                hh = int(r['driver_household_id'])
                bind(p, int(r['driver_person_id']))
                lift_hh.setdefault(p, [])
                if hh not in lift_hh[p]:
                    lift_hh[p].append(hh)
                # pre-9.68 tables carry no direction column; treat as 'drop'
                lift_cover.setdefault(
                    (p, int(r['passenger_tour_id'])), set()).add(
                        r.get('direction') or 'drop')
    # 9.68: household escort coverage - which member tours the placed
    # household serve tours cover, by direction. A tour covered in BOTH
    # directions seeds as B.mode.bound_passenger_seed.
    escort_cover = {}
    escorts = os.path.join(PLANS, 'B2_escort_bindings_%s.csv' % day)
    if os.path.exists(escorts):
        with open(escorts, encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                bind(int(r['member_person_id']),
                     int(r['driver_person_id']))
                escort_cover.setdefault(
                    (int(r['member_person_id']), int(r['member_tour_id'])),
                    set()).add(r['direction'])
    covered_by_pid = {}
    for (p, tid), dirs in list(escort_cover.items()) + list(lift_cover.items()):
        if {'drop', 'pickup'} <= dirs:
            covered_by_pid.setdefault(p, set()).add(tid)
    # 9.84: joint household tours. The companion travels WITH the driver on
    # both legs by construction, so a joint companion tour is covered in both
    # directions and seeds as B.mode.bound_passenger_seed; the driver's tour
    # seeds car like a bound serve tour - the pairing engine pairs ride legs
    # with CAR legs only, and a joint driver on any other mode cannot carry
    # the companion bound onto their car.
    joint_driver = {}   # pid -> set of tour ids
    joint_companion = {}   # pid -> set of tour ids ridden WITH the driver
    joints = os.path.join(PLANS, 'B2_joint_bindings_%s.csv' % day)
    if os.path.exists(joints):
        with open(joints, encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                covered_by_pid.setdefault(
                    int(r['companion_person_id']), set()).add(
                        int(r['companion_tour_id']))
                joint_companion.setdefault(
                    int(r['companion_person_id']), set()).add(
                        int(r['companion_tour_id']))
                joint_driver.setdefault(
                    int(r['driver_person_id']), set()).add(
                        int(r['driver_tour_id']))
                bind(int(r['companion_person_id']),
                     int(r['driver_person_id']))
    u_buf = {'buf': rng.random(1 << 20), 'i': 0}

    def u():
        if u_buf['i'] >= u_buf['buf'].size:
            u_buf['buf'] = rng.random(1 << 20)
            u_buf['i'] = 0
        v = u_buf['buf'][u_buf['i']]
        u_buf['i'] += 1
        return float(v)

    n_persons = n_legs = n_acts = 0
    modes = collections.Counter()
    act_counts = collections.Counter()
    tours = 0
    escort_ride_denied = [0]
    # 9.84: ride legs seeded through escort/lift/joint COVERAGE, split out so
    # the package check can hold the uniform draw to its 9.11 invariant while
    # the coverage-seeded component legitimately raises ride above it.
    covered_ride_legs = [0]
    # 9.120: how many plans each person starts with under the seed method
    seed_plans_hist = collections.Counter()
    n_legs_selected = 0

    with gzip_writer(dst) as w:
        w.write('<?xml version="1.0" encoding="utf-8"?>\n')
        w.write('<!DOCTYPE population SYSTEM '
                '"http://www.matsim.org/files/dtd/population_v6.dtd">\n')
        w.write('<population>\n')
        for pid, rows in stream_persons(src):
            rows.sort(key=lambda r: int(r['trip_seq']))
            tier = rows[0]['agent_tier']
            external = tier in ('external', 'through', 'freight')
            if tier in ('through', 'freight'):
                # A through agent is a boundary-tier vehicle crossing the study
                # area (issue #20, DECISIONS.md 9.41); a freight agent is a
                # heavy-vehicle background trip (issue #24, DECISIONS.md 9.49).
                # Both volumes are anchored on observed road counts, so the
                # mode is locked - car and truck respectively: the availability
                # calculator returns exactly that singleton and the seed never
                # draws. Demographics are the external placeholders.
                car_av, age, lic, emp, stu, mob = (
                    1, EXTERNAL_PROFILE['age'], 1,
                    EXTERNAL_PROFILE['employment_status'],
                    EXTERNAL_PROFILE['student_status'],
                    EXTERNAL_PROFILE['mobility_impairment_flag'])
                ride_av, bike_av, hh_id = 0, 0, None
                moto = False
            elif external:
                # An external boundary agent has no B1 household, so its
                # attributes are definitional placeholders (B.external
                # .agent_profile). Ride availability is NOT one of them and is
                # not "unknown": a car passenger needs a household vehicle AND
                # another licence holder to drive them, and a household-less
                # agent has neither, so ride is unavailable by the same identity
                # that governs everyone else. Resolving it the other way, which
                # is what this branch used to do, made 432 of 962 external trips
                # car-passenger trips with no possible driver (DECISIONS.md 9.15).
                car_av, age, lic, emp, stu, mob = (
                    EXTERNAL_PROFILE['car_available'], EXTERNAL_PROFILE['age'],
                    EXTERNAL_PROFILE['licence_holder'],
                    EXTERNAL_PROFILE['employment_status'],
                    EXTERNAL_PROFILE['student_status'],
                    EXTERNAL_PROFILE['mobility_impairment_flag'])
                ride_av = int(EXTERNAL_RIDE_AVAILABLE)
                # a boundary agent is household-less, so no ownership identity
                # exists to deny bike from; the choice is recorded in
                # DECISIONS.md 9.39 rather than silently made
                bike_av = 1
                # A boundary agent has no B1 household by construction, so it
                # carries no householdId and can never pair with a driver. That
                # is the same identity that already denies it `ride`.
                hh_id = None
                moto = False
            else:
                a = attrs.get(pid)
                if a is None:
                    continue
                car_av, age, lic, emp, stu, mob, ride_av, bike_av, hh_id = a
                if pid in lift_hh:
                    # 9.60: a bound lift passenger has, by construction, a
                    # driver who can carry them - the identity ride_avail
                    # derives from is satisfied across the household boundary.
                    ride_av = 1
                if ESCORT_EXCLUDES_RIDE and ride_av and any(
                        r['dest_activity_type'] == 'escort' for r in rows):
                    ride_av = 0
                    escort_ride_denied[0] += 1
                # The motorbike carve (DECISIONS.md 9.52) - but never on an
                # escort day: a pillion passenger is not how the escorted
                # child travels in any data this project holds, and the ride
                # pairing pairs passengers with CAR legs. Same day-plan-level
                # denial pattern as ESCORT_EXCLUDES_RIDE above.
                moto = (bool(car_av) and bool(lic) and motorbike_user(pid)
                        and not any(r['dest_activity_type'] == 'escort'
                                    for r in rows))

            # one mode per tour keeps chain-based modes conserved from the start
            serve_tours = set()
            covered_tours = set()
            covered_seed_tids = set()
            if not external:
                for r in rows:
                    # a BOUND serve tour carries a serving placement on one of
                    # its legs ('escorted' from the 9.46 household binder,
                    # 'lift_pickup'/'lift_serve' from the 9.60 pass)
                    if r['dest_placement'] in ('escorted', 'lift_pickup',
                                               'lift_serve'):
                        serve_tours.add(int(r['tour_id']))
                # 9.84: a joint driver's tour is a serving tour in the same
                # sense - a companion is booked into that car
                serve_tours |= joint_driver.get(pid, EMPTY_SET)
                covered_tours = covered_by_pid.get(pid, EMPTY_SET)
            tour_mode = {}
            for r in rows:
                tid = int(r['tour_id'])
                if tid not in tour_mode:
                    if tier == 'freight':
                        m = 'truck'
                    elif tier == 'through':
                        m = 'car'
                    elif moto:
                        m = 'motorbike'
                    elif tid in serve_tours and car_av:
                        # 9.68 B.mode.serve_tour_seed: the pairing engine
                        # pairs ride legs with CAR legs only - a bound serve
                        # tour seeded with any other mode cannot serve the
                        # passenger booked onto it. Seed only; SubtourModeChoice
                        # stays free to move it. A LICENSED-BUT-CARLESS escort
                        # (a parent walking a child to school) keeps the
                        # uninformed draw - seeding car would put an illegal
                        # plan in memory (the 9.15 class).
                        m = SERVE_TOUR_SEED
                    elif (tid in covered_tours and ride_av
                            and BOUND_PASSENGER_SEED != 'uninformed'):
                        # 9.68 B.mode.bound_passenger_seed: a tour covered by
                        # serve tours in BOTH directions starts at the coherent
                        # two-sided state; selection keeps or abandons it.
                        m = BOUND_PASSENGER_SEED
                        covered_seed_tids.add(tid)
                    else:
                        m = pick_mode(car_av, u, seed_table,
                                      ride_available=bool(ride_av),
                                      bike_available=bool(bike_av) and (
                                          BIKE_MIN_AGE <= 0
                                          or age >= BIKE_MIN_AGE))
                    tour_mode[tid] = m
            tours += len(tour_mode)

            # 9.120: WHICH TRIPS the bindings actually cover, as 1-based trip
            # indices in plan order - the same numbering MATSim's own
            # TripStructureUtils.getTrips and the trips table use. The binding
            # tables have always carried the tour AND the direction; the
            # population carried only `boundDriver`, a person-level identity,
            # so the run could offer `ride` on any trip of a bound person and
            # on every trip of an unbound one. Measured on the F14 arm at
            # iteration 30: 36% of residents' planned ride legs belonged to
            # persons with no declared driver at all, and every one of them
            # was executed as a drive or a walk while the plan kept `ride`.
            #   boundRideTrips  - trips a declared driver serves (a drop-off
            #                     is the tour's first trip, a pick-up its
            #                     last, a joint companion tour every trip)
            #   boundDriveTrips - trips on a tour that SERVES a booked
            #                     passenger (the driver's commitment)
            # Consumed by citysim.GatedSubtourModeChoice, which refuses a
            # `ride` proposal off the first list and a non-car proposal on
            # the second, and by the full-choice-set seed below.
            bound_ride_trips = []
            bound_drive_trips = []
            if not external:
                by_tour = {}
                for i, r in enumerate(rows):
                    by_tour.setdefault(int(r['tour_id']), []).append(i + 1)
                for tid, idx in by_tour.items():
                    dirs = set()
                    dirs |= escort_cover.get((pid, tid), EMPTY_SET)
                    dirs |= lift_cover.get((pid, tid), EMPTY_SET)
                    if tid in joint_companion.get(pid, EMPTY_SET):
                        dirs |= {'drop', 'pickup'}
                        bound_ride_trips.extend(idx)
                    else:
                        if 'drop' in dirs:
                            bound_ride_trips.append(idx[0])
                        if 'pickup' in dirs and len(idx) > 1:
                            bound_ride_trips.append(idx[-1])
                    if tid in serve_tours:
                        bound_drive_trips.extend(idx)
                bound_ride_trips = sorted(set(bound_ride_trips))
                bound_drive_trips = sorted(set(bound_drive_trips))

            # The plans this person starts with. `uniform_draw`: the one
            # plan the loop above drew. `full_choice_set` (9.120): one plan
            # per usable mode, each mode on every tour it may take -
            # serving tours stay car (the commitment) and the bound-ride
            # variant puts ride on the covered tours only. Locked tiers and
            # the carve keep their single plan: a lock is a definition.
            plan_set = [dict(tour_mode)]
            if (SEED_METHOD == 'full_choice_set' and not external
                    and not moto):
                base_modes = []
                if car_av:
                    base_modes.append('car')
                base_modes.append('walk')
                if bike_av and (BIKE_MIN_AGE <= 0 or age >= BIKE_MIN_AGE):
                    base_modes.append('bike')
                base_modes.append('pt')
                if TAXI_MIN_AGE <= 0 or age >= TAXI_MIN_AGE:
                    base_modes.append('taxi')
                ride_tours = set()
                if ride_av and bound_ride_trips:
                    for tid, idx in by_tour.items():
                        # a tour is a ride tour only when EVERY trip of it is
                        # served: a one-way binding leaves the other leg to
                        # the base mode, which mixes only within non-chain
                        # modes when the base is walk/pt/taxi - so a
                        # partially bound tour rides only on a non-chain base
                        if all(i in bound_ride_trips for i in idx):
                            ride_tours.add(tid)
                plan_set = []
                for base in base_modes:
                    p = {}
                    for tid in by_tour:
                        if tid in serve_tours and car_av:
                            p[tid] = 'car'
                        else:
                            p[tid] = base
                    plan_set.append(p)
                if ride_tours:
                    # the bound-ride variant on the car base when a car is
                    # available (the uncovered tours are driven), else on walk
                    base = 'car' if car_av else 'walk'
                    p = {}
                    for tid in by_tour:
                        if tid in serve_tours and car_av:
                            p[tid] = 'car'
                        elif tid in ride_tours:
                            p[tid] = 'ride'
                            covered_seed_tids.add(tid)
                        else:
                            p[tid] = base
                    plan_set.append(p)
                seed_plans_hist[len(plan_set)] += 1

            w.write('\t<person id="%d">\n' % pid)
            w.write('\t\t<attributes>\n')
            w.write('\t\t\t<attribute name="subpopulation" class="java.lang.String">'
                    '%s</attribute>\n' % ('freight' if tier == 'freight' else
                                          'external' if external else 'person'))
            w.write('\t\t\t<attribute name="carAvail" class="java.lang.String">'
                    '%s</attribute>\n' % ('always' if car_av else 'never'))
            w.write('\t\t\t<attribute name="hasLicense" class="java.lang.String">'
                    '%s</attribute>\n' % ('yes' if lic else 'no'))
            w.write('\t\t\t<attribute name="age" class="java.lang.Integer">'
                    '%d</attribute>\n' % age)
            w.write('\t\t\t<attribute name="employment" class="java.lang.String">'
                    '%s</attribute>\n' % esc(emp))
            w.write('\t\t\t<attribute name="mobilityImpaired" class="java.lang.String">'
                    '%s</attribute>\n' % ('yes' if mob else 'no'))
            # consumed by citysim.AvailabilityModesCalculator; absent means
            # available, so a population without them behaves as before
            w.write('\t\t\t<attribute name="rideAvail" class="java.lang.String">'
                    '%s</attribute>\n' % ('always' if ride_av else 'never'))
            w.write('\t\t\t<attribute name="bikeAvail" class="java.lang.String">'
                    '%s</attribute>\n' % ('always' if bike_av else 'never'))
            if hh_id is not None:
                # B1 household membership, consumed by
                # src/java/citysim/RidePairingEngine and by
                # src/run/sample_population.py. Absent on the boundary tiers,
                # which have no household - so its absence is meaningful, and it
                # is exactly what those two consumers test for.
                w.write('\t\t\t<attribute name="householdId" '
                        'class="java.lang.String">%d</attribute>\n' % hh_id)
            if not external and pid in lift_hh:
                # 9.60: consumed by citysim.RidePairingEngine - the DRIVER
                # household(s) this passenger's pairing may also search.
                # Comma-separated since 9.68: a round-trip pair may be served
                # by drivers from two different households.
                w.write('\t\t\t<attribute name="liftHousehold" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ','.join('%d' % h for h in lift_hh[pid]))
            if bound_ride_trips:
                # 9.120: consumed by citysim.GatedSubtourModeChoice and
                # citysim.RidePairingEngine - the trips (1-based, plan order)
                # a declared driver serves. `ride` is refused on any other.
                w.write('\t\t\t<attribute name="boundRideTrips" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ','.join('%d' % i for i in bound_ride_trips))
            if bound_drive_trips:
                # 9.120: consumed by citysim.GatedSubtourModeChoice - the
                # trips on which this person is the declared driver of a
                # booked passenger; a proposal moving them off car is refused.
                w.write('\t\t\t<attribute name="boundDriveTrips" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ','.join('%d' % i for i in bound_drive_trips))
            if not external and pid in bound_driver:
                # 9.85: the DECLARED driver(s) this passenger was generated
                # to travel with - joint companion, escorted member or
                # bound lift passenger alike, since the defect and its
                # repair are identical in all three. Consumed by
                # citysim.RidePairingEngine. The binding is an IDENTITY,
                # not a proximity: the engine may recognise this pair after
                # replanning has moved either member's clock, which the
                # geometric+window search cannot do. It remains an
                # ELIGIBILITY - endpoints, vehicle capacity and physical
                # boarding still decide whether the pairing is made, and
                # the gap is waiting time the passenger pays for in score.
                w.write('\t\t\t<attribute name="boundDriver" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ','.join('%d' % d for d in bound_driver[pid]))
            if tier in ('through', 'freight') or moto:
                # locks SubtourModeChoice to {car} / {truck} / {motorbike} for
                # this agent - a volume anchored on an observation must stay
                # on it, and a mode with no preference data cannot compete in
                # choice without inventing a constant (DECISIONS.md 9.52)
                w.write('\t\t\t<attribute name="lockedMode" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ('truck' if tier == 'freight' else
                           'motorbike' if moto else 'car'))
            w.write('\t\t</attributes>\n')
            for k, plan_modes in enumerate(plan_set):
                # the first plan is the selected one; under the full choice
                # set MATSim executes every unscored plan once regardless
                w.write('\t\t<plan selected="%s">\n' % ('yes' if k == 0 else 'no'))

                # opening activity: home, at the first leg's origin
                first = rows[0]
                w.write('\t\t\t<activity type="home" x="%s" y="%s" end_time="%s" />\n'
                        % (first['origin_x'], first['origin_y'],
                           hhmmss(int(first['dep_time_s']))))
                n_acts += 1
                act_counts['home'] += 1

                for i, r in enumerate(rows):
                    mode = plan_modes[int(r['tour_id'])]
                    w.write('\t\t\t<leg mode="%s" />\n' % mode)
                    modes[mode] += 1
                    if mode == 'ride' and int(r['tour_id']) in covered_seed_tids:
                        covered_ride_legs[0] += 1
                    n_legs += 1
                    act = r['dest_activity_type']
                    act_counts[act] += 1
                    n_acts += 1
                    if i == len(rows) - 1:
                        w.write('\t\t\t<activity type="%s" x="%s" y="%s" />\n'
                                % (act, r['dest_x'], r['dest_y']))
                    else:
                        end = int(rows[i + 1]['dep_time_s'])
                        w.write('\t\t\t<activity type="%s" x="%s" y="%s" '
                                'end_time="%s" />\n'
                                % (act, r['dest_x'], r['dest_y'], hhmmss(end)))
                w.write('\t\t</plan>\n')
                if k == 0:
                    n_legs_selected += len(rows)
            w.write('\t</person>\n')
            n_persons += 1
        w.write('</population>\n')

    report[day] = dict(persons=n_persons, legs=n_legs, activities=n_acts,
                       tours=tours, bytes=os.path.getsize(dst),
                       escort_ride_denied=escort_ride_denied[0],
                       # 9.120: legs counted over EVERY seeded plan; the
                       # selected plan's own count is what a 1-plan build
                       # used to report as `legs`
                       legs_selected_plan=n_legs_selected,
                       seed_method=SEED_METHOD,
                       seed_plans_per_person={
                           str(k): v for k, v in sorted(seed_plans_hist.items())},
                       seed_mode_share={k: round(v / max(n_legs, 1), 4)
                                        for k, v in sorted(modes.items())},
                       # 9.84: the coverage-seeded ride component (escort,
                       # lift and joint bindings), as a share of legs - the
                       # remainder of the ride seed is the uniform draw
                       seed_ride_covered_share=round(
                           covered_ride_legs[0] / max(n_legs, 1), 4),
                       activity_types=dict(sorted(act_counts.items())))
    print('%-8s %7d persons %9d legs %9d activities  %s'
          % (day, n_persons, n_legs, n_acts,
             {k: round(v / max(n_legs, 1), 3) for k, v in sorted(modes.items())}),
          flush=True)


def main(seed=SEED, day_types=None, seed_mode='uninformed'):
    day_types = day_types or DAY_TYPES
    seed_table = (SEED_MODE_SPLIT_INFORMED if seed_mode == 'informed'
                  else SEED_MODE_SPLIT)
    hts_unlinked, hts_linked = hts_mode_share()
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(seed)
    print('loading person attributes ...', flush=True)
    # bike availability draws from its own child stream so the mode-seed
    # stream is not perturbed by the number of persons (issue #29)
    attrs = load_person_attributes(np.random.default_rng([seed, 1]))
    # The motorbike carve probability (DECISIONS.md 9.52): carved persons'
    # trips should be B.motorbike.trip_share of all trips. Eligible persons
    # (licensed AND car-available - a motorcyclist is a licensed vehicle
    # owner in every data source this project holds) are assumed to trip at
    # the population's average rate; the approximation is absorbed by the
    # field's own sweep and stated in its basis.
    # 9.120: the probability is solved on the eligible persons' OWN trip
    # counts, not on the population's average rate. The earlier form assumed
    # eligible persons trip at the average and the assumption was measured
    # false (issue #93: carved persons made 3.48 trips/day against 4.11, so
    # the carve delivered 55% of its declared share). Trips are counted on
    # the first day type built - the share is a share of all trips and the
    # carve is one draw per person across day types.
    trips_by_pid = collections.Counter()
    first_day = day_types[0]
    for pid, rows in stream_persons(
            os.path.join(PLANS, 'B2_activity_trips_%s.csv' % first_day)):
        trips_by_pid[pid] = len(rows)
    total_trips = sum(trips_by_pid[p] for p in attrs)
    eligible = sum(1 for a in attrs.values() if a[0] and a[2])
    eligible_trips = sum(trips_by_pid[p] for p, a in attrs.items()
                         if a[0] and a[2])
    q = (MOTORBIKE_SHARE * total_trips / eligible_trips) if eligible_trips else 0.0
    _MOTORBIKE_Q['q'] = min(1.0, q)
    print('motorbike carve: trip share %.5f -> q=%.5f over %d eligible '
          'persons (of %d) making %d of %d %s trips'
          % (MOTORBIKE_SHARE, _MOTORBIKE_Q['q'], eligible, len(attrs),
             eligible_trips, total_trips, first_day), flush=True)
    report = {}
    for d in day_types:
        write_day(d, attrs, rng, report, seed_table)
    meta = dict(seed=seed, seed_mode=seed_mode,
                # 9.120: the seed METHOD - `full_choice_set` writes one plan
                # per usable mode and the split below is then only the
                # selected plan's draw
                seed_method=SEED_METHOD,
                seed_mode_split={str(k): v for k, v in seed_table.items()},
                seed_mode_sweep=SEED_MODE_SWEEP,
                bike_available_rate=BIKE_AVAILABLE_RATE,
                bike_available_sweep=list(
                    CFG.sweep('B.population.bike_available_rate')),
                # The #62 A5 refactor moved the survey file and vintage behind
                # the city's reader adapter, and these two provenance strings
                # kept naming the removed HTS_FILE/HTS_YEAR globals - a
                # NameError that only fired on the first plans build after the
                # refactor. The framework no longer knows the file: the
                # adapter is the source it can honestly name.
                hts_mode_share_pct=hts_unlinked,
                hts_mode_share_pct_source=(
                    'derived through the city reader mode_share_table '
                    '(cities/<city>/extract/reader_shapes.py, #62 A5): '
                    'trips-weighted over the study-area LGAs, unlinked, walk '
                    'includes the walk stage of a PT trip'),
                hts_calibration_target_pct=hts_linked,
                hts_calibration_target_source=(
                    'derived through the city reader mode_share_table '
                    '(cities/<city>/extract/reader_shapes.py, #62 A5): the '
                    'published linked MODE_SHARE column for the %s LGA. This '
                    'is the basis of validation targets V202-V207 and the one '
                    'a MATSim mode share is comparable to (DECISIONS.md 12.1)'
                    % HTS_TARGET_LGA),
                typical_duration_s=TYPICAL_DURATION_S,
                typical_duration_sweep=TYPICAL_DURATION_SWEEP,
                note='Seed modes are initial conditions for MATSim co-evolution, '
                     'drawn per tour so chain-based modes stay conserved. The '
                     'default seed is UNINFORMED - uniform over the modes each '
                     'person can use, conditioned only on B1 car availability - '
                     'so that the HTS mode share is a target the model has to '
                     'reach rather than one it is handed (DECISIONS.md 9.6). '
                     'Run with --seed-mode informed to reproduce the P3 seed.',
                by_day=report)
    json.dump(meta, open(os.path.join(OUT, '_plans_report.json'), 'w'), indent=2)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=SEED)
    ap.add_argument('--day-types', default=','.join(DAY_TYPES))
    ap.add_argument('--seed-mode', choices=['uninformed', 'informed'],
                    default='uninformed',
                    help='uninformed (default): uniform over usable modes. '
                         'informed: the P3 seed positioned near the HTS '
                         'aggregate, retained so the seed dependence can be '
                         'tested rather than asserted.')
    ap.add_argument('--out', default=None,
                    help='override the output directory (for seed experiments)')
    a = ap.parse_args()
    if a.out:
        OUT = a.out
    main(a.seed, [d for d in a.day_types.split(',') if d], a.seed_mode)
