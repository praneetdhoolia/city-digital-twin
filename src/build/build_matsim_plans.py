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
# DECISIONS.md 9.122: the carve at the resolution the census observes it.
# `region` applies B.motorbike.trip_share everywhere; `sa1_thinned` derives
# a share per home SA1 from the same G62 cell (motorbike / car-as-driver
# journeys x CAL.mode_split.vehicle_driver_level), falling back to the SA1's
# SA2 where the driver cell is under B.census.thin_cell_min_journeys - ABS
# perturbs small cells. Measured: SA2 shares run 0 to 1.13% of drivers
# against a flat 0.41%, and the flat carve delivered 0.06% of target-LGA
# trips against 0.24% on the F16/F17 arms (#93 fact 2).
MOTORBIKE_CARVE_RESOLUTION = CFG.get('B.motorbike.carve_resolution')
VEHICLE_DRIVER_LEVEL = CFG.get('CAL.mode_split.vehicle_driver_level')
THIN_CELL_MIN = CFG.get('B.census.thin_cell_min_journeys')
_MOTORBIKE_Q = {'q': 0.0}   # solved in main() from the eligible share
_MOTORBIKE_Q_BY_PID = {}    # 9.122: per-person q under `sa1_thinned`
# DECISIONS.md 9.125: residents who drive a truck for a living - census G62
# one-method Truck journeys to work, 223 of 43,959 driver journeys in the
# target LGA, carried to all-purpose trips by the survey's driver level
# exactly as the motorbike carve is. A person-level carve locked to `truck`:
# the vehicle is the person's own (`vehicles` carries a truck per person),
# the mode is chain-based by nature, and no preference observation exists to
# let it compete in mode choice. Drawn on its own hash namespace so the
# motorbike draws are byte-identical to before; a person can hold one lock.
TRUCK_RESIDENT_SHARE = CFG.get('B.truck.resident_trip_share')
_TRUCK_Q = {'q': 0.0}

import hashlib as _hashlib  # noqa: E402


def truck_user(pid):
    if _TRUCK_Q['q'] <= 0.0:
        return False
    h = _hashlib.sha256(('truck|%s|%d' % (pid, SEED)).encode()).hexdigest()
    return int(h[:12], 16) / float(1 << 48) < _TRUCK_Q['q']


def motorbike_user(pid):
    q = _MOTORBIKE_Q_BY_PID.get(pid, _MOTORBIKE_Q['q']) \
        if _MOTORBIKE_Q_BY_PID else _MOTORBIKE_Q['q']
    if q <= 0.0:
        return False
    h = _hashlib.sha256(('motorbike|%s|%d' % (pid, SEED)).encode()).hexdigest()
    return int(h[:12], 16) / float(1 << 48) < q


def motorbike_share_by_cell():
    """(home SA1 -> motorbike share of trips) from the census cell, thinned.

    The identity is B.motorbike.trip_share's, applied per cell: share =
    CAL.mode_split.vehicle_driver_level x (one-method motorbike journeys /
    one-method car-as-driver journeys). A cell with fewer driver journeys than
    B.census.thin_cell_min_journeys takes its SA2's ratio. Returns the map and
    the cells used, for the report.
    """
    import csv as _csv
    g62 = _city.path('data/processed/census/census2021_G62_SA1.csv')
    zones = _city.path('data/processed/zones/zones_SA1.csv')
    sa2_of = {}
    with open(zones, newline='', encoding='utf-8') as fh:
        for r in _csv.DictReader(fh):
            sa2_of[r['SA1_CODE21']] = r['SA2_CODE21']
    drv, moto = {}, {}
    with open(g62, newline='', encoding='utf-8') as fh:
        for r in _csv.DictReader(fh):
            sa1 = r['SA1_CODE_2021']
            try:
                drv[sa1] = float(r.get('One_method_Car_as_driver_P') or 0)
                moto[sa1] = float(r.get('One_method_Motorbike_scootr_P') or 0)
            except ValueError:
                continue
    sa2_drv, sa2_moto = {}, {}
    for sa1, d in drv.items():
        s2 = sa2_of.get(sa1)
        sa2_drv[s2] = sa2_drv.get(s2, 0.0) + d
        sa2_moto[s2] = sa2_moto.get(s2, 0.0) + moto[sa1]
    share, used = {}, {'sa1': 0, 'sa2': 0, 'none': 0}
    for sa1, d in drv.items():
        if d >= THIN_CELL_MIN and d > 0:
            share[sa1] = VEHICLE_DRIVER_LEVEL * moto[sa1] / d
            used['sa1'] += 1
        else:
            s2 = sa2_of.get(sa1)
            if sa2_drv.get(s2, 0.0) > 0:
                share[sa1] = VEHICLE_DRIVER_LEVEL * sa2_moto[s2] / sa2_drv[s2]
                used['sa2'] += 1
            else:
                share[sa1] = 0.0
                used['none'] += 1
    return share, used, drv, moto


def motorbike_identity_by_lga(drv, moto):
    """(LGA name -> the LGA's own identity share, SA1 -> LGA) from the same
    G62 cells summed over each LGA: CAL.mode_split.vehicle_driver_level x
    (motorbike journeys / car-as-driver journeys). The target LGA's value is
    B.motorbike.trip_share by construction (9.115, 9.122)."""
    import csv as _csv
    lga_of = {}
    with open(_city.path('data/processed/zones/sa1_to_lga.csv'), newline='',
              encoding='utf-8') as fh:
        for r in _csv.DictReader(fh):
            lga_of[r['SA1_CODE21']] = r['lga_name']
    d_l, m_l = collections.Counter(), collections.Counter()
    for sa1, d in drv.items():
        lga = lga_of.get(sa1)
        if lga is None:
            continue
        d_l[lga] += d
        m_l[lga] += moto.get(sa1, 0.0)
    identity = {lga: (VEHICLE_DRIVER_LEVEL * m_l[lga] / d_l[lga]) if d_l[lga] else 0.0
                for lga in d_l}
    return identity, lga_of
# An escort trip's traveller is the driver - the identity that already limits
# HX generation to licence holders, carried through to mode choice: a person
# whose day includes an escort activity is denied `ride` FOR THAT DAY TYPE.
# Measured motivation: 4,791 escort trips on the relaxed 25% arm were made BY
# ride, a passenger being driven in order to convey somebody (DECISIONS.md
# 9.46). Day-plan level because PermissibleModesCalculator is per plan; the
# collateral - the escorting driver cannot be driven on their OTHER tours the
# same day - is stated, small, and plausibly the truth.
ESCORT_EXCLUDES_RIDE = CFG.get('B.activity.escort_excludes_ride')
# 9.143 (#86): WHERE that denial applies. `subtour` leaves the person's other
# tours free - the escorting tour is held at car by the seed and by
# GatedSubtourModeChoice's refusal of a non-car proposal on boundDriveTrips,
# so two mechanisms already carry it. `day` is the pre-9.143 behaviour and
# recovers that build exactly.
ESCORT_EXCLUSION_SCOPE = CFG.get('B.activity.escort_exclusion_scope')
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
# 9.143 (#86): the non-chain mode a seeded plan puts on the UNCOVERED leg of
# a partially bound tour, so its covered leg can be seeded as `ride` without
# the chain/non-chain subtour mix MATSim refuses (9.119).
PARTIAL_BIND_BASE = CFG.get('B.mode.partial_bind_base')
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
# The open top income band's representative value is its lower bound times
# this declared factor (DECISIONS.md 9.138); every closed band takes its
# interval midpoint by identity.
TOP_BAND_FACTOR = CFG.get('C.income.top_band_factor')


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
                             'mobility_impairment_flag', 'income_band'])

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
                           int(r.bike_avail), int(r.household_id),
                           income_band_midpoint(r.income_band))
        for r in p.itertuples()
    }


def income_band_midpoint(band):
    """Weekly income (AUD) represented by a census income band, or None.

    The identity is the band label's own bounds: a closed band `lo_hi` takes
    its interval midpoint; the open top band `lo_more` takes lo x the declared
    C.income.top_band_factor (the conventional open-interval treatment); the
    no-income band and anything unparseable take None, so the person carries
    NO income attribute and keeps the subpopulation marginalUtilityOfMoney by
    MATSim's documented fallback (DECISIONS.md 9.138, issue #108). Only the
    RATIO of a person's income to the population average ever reaches
    scoring, so the weekly basis needs no unit conversion.
    """
    parts = str(band).split('_')
    if len(parts) != 2 or not parts[0].isdigit():
        return None                      # Neg_Nil, blanks, unknown labels
    lo = float(parts[0])
    if parts[1] == 'more':
        return round(lo * TOP_BAND_FACTOR, 1)
    if not parts[1].isdigit():
        return None
    return round((lo + float(parts[1])) / 2.0, 1)


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


# 9.140 (#96): the run's own subtour decomposition parameters, so the seed
# is tested exactly as MATSim will decompose it.
COORD_DISTANCE_M = float(CFG.get('RUN.mode_choice.coord_distance_m'))
CHAIN_BASED_MODES = frozenset(CFG.get('RUN.mode_choice.chain_based_modes'))


def leaf_mixed_tours(rows, plan_modes):
    """Tour ids whose trips fall in a LEAF subtour mixing chain- and
    non-chain-based modes, by MATSim's own rule.

    TripStructureUtils.getSubtours(plan, coordDistance): trips are taken in
    order; each trip joins the unallocated list, and if the LATEST
    unallocated trip whose origin lies within coordDistance of this trip's
    destination exists, the trips from it onward close one subtour and
    leave the list. A subtour whose trips are contiguous in plan order has
    no children - a leaf, one excursion - and a leaf holding both a
    chain-based and a non-chain-based leg is the state
    ChooseRandomLegModeForSubtour refuses (9.119): the vehicle is not where
    the agent left it. Measured on the 9.133 plans: 3 leaf mixes in
    4,667,170 subtours, every one a serve stop within coordDistance of home
    and a later base-mode activity at the served location (9.140).
    """
    acts = [(float(rows[0]['origin_x']), float(rows[0]['origin_y']))]
    acts += [(float(r['dest_x']), float(r['dest_y'])) for r in rows]
    tids = [int(r['tour_id']) for r in rows]
    unalloc = []
    bad = set()
    cd2 = COORD_DISTANCE_M * COORD_DISTANCE_M
    for t in range(len(rows)):
        unalloc.append(t)
        dx, dy = acts[t + 1]
        for k in range(len(unalloc) - 1, -1, -1):
            ox, oy = acts[unalloc[k]]
            if (ox - dx) ** 2 + (oy - dy) ** 2 <= cd2:
                sub = unalloc[k:]
                del unalloc[k:]
                if sub[-1] - sub[0] + 1 == len(sub):     # contiguous: a leaf
                    modes = {plan_modes[tids[i]] for i in sub}
                    if any(m in CHAIN_BASED_MODES for m in modes) and \
                            any(m not in CHAIN_BASED_MODES for m in modes):
                        bad.update(tids[i] for i in sub
                                   if plan_modes[tids[i]] not in CHAIN_BASED_MODES)
                break
    return bad


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
    # 9.124: the shared-ride pass - a car-less resident's direct tour bound
    # to non-household drivers making the same SA1-to-SA1 trip. Read
    # exactly as the lift table: the driver's identity, the driver's
    # household for the runtime candidate search, the direction for
    # coverage; and the DRIVER's tour becomes a serving tour (held at car,
    # boundDriveTrips) like a joint driver's.
    shared_driver = {}   # driver pid -> set of tour ids that carry a passenger
    shared_hh = {}       # passenger pid -> [driver household ids] (9.127)
    shared = os.path.join(PLANS, 'B2_shared_bindings_%s.csv' % day)
    if os.path.exists(shared):
        with open(shared, encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                p = int(r['passenger_person_id'])
                hh = int(r['driver_household_id'])
                bind(p, int(r['driver_person_id']))
                lift_hh.setdefault(p, [])
                if hh not in lift_hh[p]:
                    lift_hh[p].append(hh)
                shared_hh.setdefault(p, [])
                if hh not in shared_hh[p]:
                    shared_hh[p].append(hh)
                lift_cover.setdefault(
                    (p, int(r['passenger_tour_id'])), set()).add(r['direction'])
                shared_driver.setdefault(
                    int(r['driver_person_id']), set()).add(int(r['driver_tour_id']))
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
    # 9.144 (#142): serve tours landing on a person whose household owns no
    # vehicle. The four binder passes all test car availability on the driver
    # side now, so this class is EMPTY by construction; it is counted, not
    # tolerated - a non-zero figure here means a binding escaped that identity
    # again and the seed is about to put a walker on a declared drive trip.
    serve_tours_carless = [0]
    # 9.84: ride legs seeded through escort/lift/joint COVERAGE, split out so
    # the package check can hold the uniform draw to its 9.11 invariant while
    # the coverage-seeded component legitimately raises ride above it.
    covered_ride_legs = [0]
    # 9.120: how many plans each person starts with under the seed method
    seed_plans_hist = collections.Counter()
    n_legs_selected = 0
    # 9.140 (#96): variants whose leaf subtour mixed a held car leg with the
    # base mode, repaired by driving the offending tour
    leaf_mix_repairs = {'tours': 0, 'ride_tours_driven': 0, 'persons': set()}
    # 9.143 (#86): what the per-trip variant reached, and what is STILL
    # unreachable because the person holds no ride availability at all - split
    # by the two identities that deny it, because they are different defects
    # and only one of them is this change's.
    partial_bind = {'tours': 0, 'trips': 0, 'plans_added': 0, 'persons': set()}
    unreachable = {'escort_day_trips': 0, 'escort_day_persons': set(),
                   'no_vehicle_trips': 0, 'no_vehicle_persons': set()}

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
                inc = None               # a volume, not a budget (9.138)
                moto = False
                trk = False
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
                inc = None               # household-less, no G17 band (9.138)
                moto = False
                trk = False
            else:
                a = attrs.get(pid)
                if a is None:
                    continue
                car_av, age, lic, emp, stu, mob, ride_av, bike_av, hh_id, inc = a
                if pid in lift_hh:
                    # 9.60: a bound lift passenger has, by construction, a
                    # driver who can carry them - the identity ride_avail
                    # derives from is satisfied across the household boundary.
                    ride_av = 1
                escort_denied = False
                if (ESCORT_EXCLUDES_RIDE and ESCORT_EXCLUSION_SCOPE == 'day'
                        and ride_av
                        and any(r['dest_activity_type'] == 'escort'
                                for r in rows)):
                    # 9.143: the DAY-wide denial, kept only as the sweep's
                    # `day` member. Under `subtour` the person keeps ride
                    # availability and the escorting tour is still held at car
                    # - by the seed, which keeps a serve tour on car, and by
                    # GatedSubtourModeChoice, which refuses a non-car proposal
                    # on boundDriveTrips. The identity is enforced where it
                    # applies instead of across the whole day, which cost
                    # 33,832 WEEKDAY bound trips the demand had already bound
                    # to a named driver.
                    ride_av = 0
                    escort_denied = True
                    escort_ride_denied[0] += 1
                # The motorbike carve (DECISIONS.md 9.52) - but never on an
                # escort day: a pillion passenger is not how the escorted
                # child travels in any data this project holds, and the ride
                # pairing pairs passengers with CAR legs. Same day-plan-level
                # denial pattern as ESCORT_EXCLUDES_RIDE above.
                # 9.125: a person the binders named as someone's DRIVER is
                # never carved - the pairing engine pairs ride legs with CAR
                # legs only, so a carved driver would strand the passenger
                # the demand bound to them. Escort days were already excluded.
                names_driver = (pid in joint_driver or pid in shared_driver
                                or any(r['dest_placement'] in
                                       ('escorted', 'lift_pickup', 'lift_serve')
                                       for r in rows))
                moto = (bool(car_av) and bool(lic) and not names_driver
                        and motorbike_user(pid)
                        and not any(r['dest_activity_type'] == 'escort'
                                    for r in rows))
                # 9.125: the resident truck carve, same pool, one lock per
                # person (a motorcyclist is not also a truck driver)
                trk = (not moto and bool(car_av) and bool(lic)
                       and not names_driver and truck_user(pid)
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
                # 9.124: a driver carrying a shared-ride passenger serves too
                serve_tours |= shared_driver.get(pid, EMPTY_SET)
                covered_tours = covered_by_pid.get(pid, EMPTY_SET)
                if serve_tours and not car_av:
                    serve_tours_carless[0] += len(serve_tours)
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
                    elif trk:
                        m = 'truck'
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
                # 9.143 (#86): a bound trip on a person the availability
                # identity denies `ride` to is unreachable no matter what the
                # seed offers - no variant may carry a mode the person cannot
                # use. MEASURED, NOT CHANGED: the escort-day denial is
                # B.activity.escort_excludes_ride, whose own derivation calls
                # this collateral "small" and has never counted it in trips;
                # the vehicle-less denial is the ride_avail identity itself.
                if bound_ride_trips and not ride_av:
                    if escort_denied:
                        unreachable['escort_day_trips'] += len(bound_ride_trips)
                        unreachable['escort_day_persons'].add(pid)
                    else:
                        unreachable['no_vehicle_trips'] += len(bound_ride_trips)
                        unreachable['no_vehicle_persons'].add(pid)

            # The plans this person starts with. `uniform_draw`: the one
            # plan the loop above drew. `full_choice_set` (9.120): one plan
            # per usable mode, each mode on every tour it may take -
            # serving tours stay car (the commitment) and the bound-ride
            # variant puts ride on the covered tours only. Locked tiers and
            # the carve keep their single plan: a lock is a definition.
            # 9.143: a plan is (tour modes, per-trip overrides). The
            # override is empty for every plan but the partial-bind variant,
            # so `uniform_draw` and every base-mode plan behave exactly as
            # before.
            plan_set = [(dict(tour_mode), {})]
            if (SEED_METHOD == 'full_choice_set' and not external
                    and not moto and not trk):
                base_modes = []
                if car_av:
                    base_modes.append('car')
                base_modes.append('walk')
                if bike_av and (BIKE_MIN_AGE <= 0 or age >= BIKE_MIN_AGE):
                    base_modes.append('bike')
                base_modes.append('pt')
                if TAXI_MIN_AGE <= 0 or age >= TAXI_MIN_AGE:
                    base_modes.append('taxi')
                # 9.143 (#86): a tour is FULLY bound when every trip of it is
                # served, and PARTLY bound when only some are - a drop-off
                # binds the tour's first trip and a pick-up its last (9.120),
                # so a one-directional escort or lift always lands here.
                ride_tours, partial_tours = set(), {}
                if ride_av and bound_ride_trips:
                    for tid, idx in by_tour.items():
                        covered = [i for i in idx if i in bound_ride_trips]
                        if not covered:
                            continue
                        if len(covered) == len(idx):
                            ride_tours.add(tid)
                        else:
                            partial_tours[tid] = covered
                plan_set = []
                for base in base_modes:
                    p = {}
                    for tid in by_tour:
                        if tid in serve_tours and car_av:
                            p[tid] = 'car'
                        else:
                            p[tid] = base
                    plan_set.append((p, {}))
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
                    plan_set.append((p, {}))
                # 9.143 (#86): THE PARTIALLY BOUND TOUR GETS A PLAN AT ALL.
                # Until now such a tour was excluded from the ride variant
                # outright, so its bound trips never became a `ride`
                # alternative ANYWHERE in plan memory and co-evolution was
                # never offered them - 2.09% of core trips (9.142), which no
                # scoring or pairing repair downstream could reach.
                #
                # It could not be offered because a seeded plan carried ONE
                # MODE PER TOUR: `ride` on the covered leg with the car base
                # on the other is a subtour mixing a chain-based mode with a
                # non-chain one, the exact state ChooseRandomLegModeForSubtour
                # refuses and that crashed two arms (9.119). The plan now
                # carries a PER-TRIP override, and the uncovered leg takes
                # B.mode.partial_bind_base - a non-chain mode - so the whole
                # subtour is non-chain and the refused state is structurally
                # unreachable rather than repaired after the fact.
                #
                # A car-LESS person needs no new plan: their bound-ride
                # variant above is already walk-based, so the override rides
                # on it. Only a car-available person gets this extra plan,
                # which is why the seed's plan count rises by at most one.
                if partial_tours:
                    base = PARTIAL_BIND_BASE if car_av else 'walk'
                    p, over = {}, {}
                    for tid in by_tour:
                        if tid in serve_tours and car_av:
                            p[tid] = 'car'
                        elif tid in ride_tours:
                            p[tid] = 'ride'
                            covered_seed_tids.add(tid)
                        elif tid in partial_tours:
                            # the tour's nominal mode is the non-chain base;
                            # the covered trips override to ride
                            p[tid] = base
                            covered_seed_tids.add(tid)
                            for i in partial_tours[tid]:
                                over[i] = 'ride'
                        else:
                            p[tid] = base
                    if not car_av and ride_tours:
                        # the walk-based bound-ride variant was appended just
                        # above and this plan is that plan plus the overrides,
                        # so it REPLACES it rather than spending a second slot
                        plan_set[-1] = (p, over)
                    else:
                        # a car-available person needs the non-chain base this
                        # plan alone carries; a car-less person with no fully
                        # bound tour has no bound-ride variant to fold onto
                        plan_set.append((p, over))
                    partial_bind['tours'] += len(partial_tours)
                    partial_bind['trips'] += sum(len(v) for v
                                                 in partial_tours.values())
                    partial_bind['persons'].add(pid)
                    if car_av or not ride_tours:
                        partial_bind['plans_added'] += 1
                # 9.140 (#96): a plan MATSim's own subtour decomposition
                # cannot hold is not offered. A serving tour is held at car
                # while the variant's other tours take the base mode, and
                # where a serve stop sits within subtourModeChoice's
                # coordDistance of an activity the person later reaches by
                # the base mode, the decomposition closes a LEAF loop
                # holding one car leg and one non-chain leg - the exact
                # state ChooseRandomLegModeForSubtour refuses (9.119). The
                # offending free tour is driven in that variant instead: the
                # person keeps every other tour on the variant's mode.
                if car_av:
                    for p, over in plan_set:
                        for _ in range(4):
                            bad = leaf_mixed_tours(rows, p)
                            if not bad:
                                break
                            for tid in bad:
                                if p[tid] == 'ride':
                                    leaf_mix_repairs['ride_tours_driven'] += 1
                                p[tid] = 'car'
                                # 9.143: a tour driven to repair a mix must
                                # lose its per-trip ride with it - leaving the
                                # override would put ride on one leg of a car
                                # tour, which is the very state being repaired
                                for i in [i for i in over
                                          if int(rows[i - 1]['tour_id']) == tid]:
                                    del over[i]
                                    leaf_mix_repairs['ride_tours_driven'] += 1
                            leaf_mix_repairs['tours'] += len(bad)
                            leaf_mix_repairs['persons'].add(pid)
                seed_plans_hist[len(plan_set)] += 1
                # 9.121: WHICH seeded plan is executed first is drawn
                # uniformly over the person's plans, by a hash of the person
                # id and the master seed (no rng stream consumed). With the
                # car plan first for everyone, iteration 0 put 74.7% of
                # residents in a car on a 10% network - 162,812 departures,
                # 6,820 cars stuck at 30:00 - and every car plan in memory
                # kept that gridlock score while the other modes were scored
                # on near-empty roads in iterations 1-6: a 60-100 util
                # handicap ChangeExpBeta never re-tests. Drawn uniformly,
                # iteration 0 is a mixed traffic state like every later one
                # and no mode's plans are scored under a state the others
                # were not.
                h = _hashlib.sha256(('seedorder|%s|%d' % (pid, SEED))
                                    .encode()).hexdigest()
                first = int(h[:12], 16) % len(plan_set)
                if first:
                    plan_set = [plan_set[first]] + plan_set[:first] + plan_set[first + 1:]

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
            if inc is not None:
                # The person's weekly income, the G17 band's midpoint (9.138,
                # #108): DATA like householdId, stamped whenever the band is
                # held; whether anything READS it is gated by
                # C.income.representation, which binds MATSim core's
                # IndividualPersonScoringParameters to scale this person's
                # marginalUtilityOfMoney by (average/personal)^exponent.
                # Absent (the Neg_Nil band, boundary tiers, freight) means the
                # subpopulation value applies - the class's documented
                # fallback, not a zero.
                w.write('\t\t\t<attribute name="income" '
                        'class="java.lang.Double">%s</attribute>\n' % inc)
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
            if not external and pid in shared_hh:
                # 9.127: the subset of liftHousehold that came from the
                # shared-ride pass. The sampler EXCLUDES these from its
                # household clusters - the binder already guarantees a shared
                # driver is kept whenever its passenger is (the unit-hash
                # rule) - so the clusters stay the small lift couplings of
                # 9.60 instead of the giant components shared rides make.
                w.write('\t\t\t<attribute name="sharedDriverHousehold" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ','.join('%d' % h for h in shared_hh[pid]))
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
            if tier in ('through', 'freight') or moto or trk:
                # locks SubtourModeChoice to {car} / {truck} / {motorbike} for
                # this agent - a volume anchored on an observation must stay
                # on it, and a mode with no preference data cannot compete in
                # choice without inventing a constant (DECISIONS.md 9.52;
                # 9.125 for the resident truck driver)
                w.write('\t\t\t<attribute name="lockedMode" '
                        'class="java.lang.String">%s</attribute>\n'
                        % ('truck' if (tier == 'freight' or trk) else
                           'motorbike' if moto else 'car'))
            w.write('\t\t</attributes>\n')
            for k, (plan_modes, trip_modes) in enumerate(plan_set):
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
                    # 9.143 (#86): a per-TRIP mode wins over the tour's,
                    # which is what lets one leg of a partially bound tour ride
                    # while the other takes a non-chain base
                    mode = trip_modes.get(i + 1) or plan_modes[int(r['tour_id'])]
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
                       # 9.144 (#142): must be 0 - a serve tour on a person
                       # with no household vehicle is a binding that escaped
                       # the driver-side car-availability identity
                       serve_tours_carless=serve_tours_carless[0],
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
                       # 9.140 (#96): leaf subtours that would have mixed a
                       # held car leg with the variant's mode, repaired at
                       # the seed by driving the offending tour
                       leaf_mix_repairs=dict(
                           tours=leaf_mix_repairs['tours'],
                           ride_tours_driven=leaf_mix_repairs['ride_tours_driven'],
                           persons=len(leaf_mix_repairs['persons']),
                           coord_distance_m=COORD_DISTANCE_M,
                           chain_based_modes=sorted(CHAIN_BASED_MODES)),
                       # 9.143 (#86): what the per-trip variant reached - the
                       # partially bound tours whose covered leg can now be
                       # seeded as `ride` at all
                       partial_bind=dict(
                           tours=partial_bind['tours'],
                           trips=partial_bind['trips'],
                           plans_added=partial_bind['plans_added'],
                           persons=len(partial_bind['persons']),
                           base=PARTIAL_BIND_BASE),
                       # 9.143 (#86): bound trips STILL unreachable, because
                       # the person holds no ride availability at all. MEASURED,
                       # NOT CHANGED - a different defect from the one repaired
                       # here, and the escort split is the first count of the
                       # collateral B.activity.escort_excludes_ride declares.
                       bound_trips_unreachable=dict(
                           escort_day_trips=unreachable['escort_day_trips'],
                           escort_day_persons=len(unreachable['escort_day_persons']),
                           no_vehicle_trips=unreachable['no_vehicle_trips'],
                           no_vehicle_persons=len(unreachable['no_vehicle_persons'])),
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
    # 9.122: a carved person is DENIED the mode on an escort day (write_day:
    # a pillion is not how the escorted child travels), and that denial
    # happens after the draw. Solving q on all eligible persons therefore
    # delivered share x (1 - the escorters' trip share): measured 0.128% of
    # legs against 0.241% solved for, with 38.0% of eligible persons holding
    # 47% of eligible trips being escorters on WEEKDAY. The denial is known
    # before the draw, so the pool is the eligible persons who will not be
    # denied - the carve then delivers what it solves for.
    # 9.129: the draw (write_day) also refuses every person the binders
    # NAMED as a driver - joint, shared, escorted / lift placements (9.125)
    # - and those held 42.1% of the non-escorting eligible pool's trips on
    # WEEKDAY, so a probability solved without them delivered 58% of its
    # share (measured 0.153% of resident trips against 0.2654% solved).
    # The denial is known before the draw, exactly as the escort denial is,
    # so the pool is the persons who will actually be offered the draw.
    escorters = set()
    for pid, rows in stream_persons(
            os.path.join(PLANS, 'B2_activity_trips_%s.csv' % first_day)):
        if any(r['dest_activity_type'] == 'escort' for r in rows):
            escorters.add(pid)
        elif any(r['dest_placement'] in ('escorted', 'lift_pickup', 'lift_serve')
                 for r in rows):
            escorters.add(pid)
    for fname, col in (('B2_joint_bindings_%s.csv' % first_day, 'driver_person_id'),
                       ('B2_shared_bindings_%s.csv' % first_day, 'driver_person_id')):
        fpath = os.path.join(PLANS, fname)
        if os.path.exists(fpath):
            with open(fpath, encoding='utf-8') as fh:
                for r in csv.DictReader(fh):
                    escorters.add(int(r[col]))
    eligible = sum(1 for p, a in attrs.items()
                   if a[0] and a[2] and p not in escorters)
    eligible_trips = sum(trips_by_pid[p] for p, a in attrs.items()
                         if a[0] and a[2] and p not in escorters)
    q = (MOTORBIKE_SHARE * total_trips / eligible_trips) if eligible_trips else 0.0
    _MOTORBIKE_Q['q'] = min(1.0, q)
    print('motorbike carve: trip share %.5f -> q=%.5f over %d eligible '
          'persons (of %d; escorters and named drivers excluded, 9.129) '
          'making %d of %d %s trips'
          % (MOTORBIKE_SHARE, _MOTORBIKE_Q['q'], eligible, len(attrs),
             eligible_trips, total_trips, first_day), flush=True)
    # 9.125: the resident truck carve on the same pool, the same arithmetic
    qt = (TRUCK_RESIDENT_SHARE * total_trips / eligible_trips) if eligible_trips else 0.0
    _TRUCK_Q['q'] = min(1.0, qt)
    print('resident truck carve: trip share %.5f -> q=%.5f on the same '
          'non-escorting eligible pool' % (TRUCK_RESIDENT_SHARE, _TRUCK_Q['q']),
          flush=True)
    carve_cells = None
    if MOTORBIKE_CARVE_RESOLUTION == 'sa1_thinned':
        # 9.122: the same identity per home SA1 (its SA2 where thin), each
        # cell's probability solved on ITS eligible persons' own trips
        share_by_sa1, used, g62_drv, g62_moto = motorbike_share_by_cell()
        home = pd.read_csv(os.path.join(POP, 'B1_synthetic_population.csv'),
                           usecols=['person_id', 'home_sa1'], dtype=str)
        sa1_of = dict(zip(home['person_id'].astype(int), home['home_sa1']))
        cell_trips, cell_elig = collections.Counter(), collections.Counter()
        for p, a in attrs.items():
            c = sa1_of.get(p)
            cell_trips[c] += trips_by_pid[p]
            if a[0] and a[2] and p not in escorters:
                cell_elig[c] += trips_by_pid[p]
        # 9.140 (#93): per-LGA conservation of the cell shares. The census
        # ratio is taken per SA1 (its SA2 where thin) and then weighted by
        # each cell's TRIPS, and cells with a high motorbike ratio make more
        # trips per driver journey than the LGA average - so the
        # trip-weighted intended share sat 9-38% above each LGA's own
        # identity before any draw (+12% Newcastle, +10% Maitland, +38%
        # Cessnock, measured 1 Sep, 9.136), and the F22 gate read motorbike
        # +13.3% at the plans' own over-delivery. The identity that the
        # target is built on is the LGA's (9.122), so each LGA's cell shares
        # are scaled by one factor that makes their trip-weighted mean equal
        # the LGA's identity: the spatial pattern within the LGA is the
        # census's, the level is the LGA's, and generation and scoring
        # describe one quantity again. The resident truck carve (9.125) is a
        # flat region probability on the same pool and delivers its solve
        # exactly, so it needs no conservation.
        identity_by_lga, lga_of = motorbike_identity_by_lga(g62_drv, g62_moto)
        # The target LGA conserves to the DECLARED identity - the same census
        # riders the fit target is built from (CAL.mode_split.*, 9.122) -
        # so generation and scoring describe one quantity. Its SA1 cells
        # summed differ from that LGA cell by ABS's small-cell perturbation
        # (measured 0.0038289 against 0.0037849, +1.2%, 3 Sep 2026): stated,
        # and not the basis. The other LGAs have no declared identity and
        # conserve to their own summed cells.
        tgt = HTS_TARGET_LGA
        cells_tgt = identity_by_lga.get(tgt)
        if cells_tgt is not None and abs(cells_tgt - MOTORBIKE_SHARE) > 0.05 * MOTORBIKE_SHARE:
            raise SystemExit(
                'the %s G62 cells summed (%.7f) sit more than 5%% from '
                'B.motorbike.trip_share (%.7f): the declared pair and the '
                'census have drifted apart (9.116)' % (tgt, cells_tgt, MOTORBIKE_SHARE))
        identity_by_lga[tgt] = MOTORBIKE_SHARE
        intended_l, trips_l = collections.Counter(), collections.Counter()
        for c, t in cell_trips.items():
            lga = lga_of.get(c)
            intended_l[lga] += share_by_sa1.get(c, 0.0) * t
            trips_l[lga] += t
        conserve = {}
        for lga, t in trips_l.items():
            mean = intended_l[lga] / t if t else 0.0
            conserve[lga] = (identity_by_lga.get(lga, 0.0) / mean) if mean > 0 else 1.0
        for c in list(share_by_sa1):
            share_by_sa1[c] = share_by_sa1[c] * conserve.get(lga_of.get(c), 1.0)
        weighted = 0.0
        for p, a in attrs.items():
            c = sa1_of.get(p)
            s = share_by_sa1.get(c, 0.0)
            qc = (s * cell_trips[c] / cell_elig[c]) if cell_elig[c] else 0.0
            _MOTORBIKE_Q_BY_PID[p] = min(1.0, qc)
        for c, t in cell_trips.items():
            weighted += share_by_sa1.get(c, 0.0) * t
        weighted = weighted / total_trips if total_trips else 0.0
        by_lga = {}
        for lga in sorted(trips_l, key=str):
            t = trips_l[lga]
            by_lga[str(lga)] = dict(
                identity=round(identity_by_lga.get(lga, 0.0), 6),
                intended_before=round(intended_l[lga] / t if t else 0.0, 6),
                conservation_factor=round(conserve[lga], 4),
                trips=int(t))
        carve_cells = dict(resolution='sa1_thinned', cells_at_sa1=used['sa1'],
                           cells_at_sa2=used['sa2'], cells_without=used['none'],
                           trip_weighted_share=round(weighted, 6),
                           declared_region_share=MOTORBIKE_SHARE,
                           lga_conservation=by_lga)
        print('motorbike carve per cell: %d SA1 cells, %d thinned to SA2, %d '
              'without a cell; trip-weighted share %.5f against the declared '
              'region share %.5f' % (used['sa1'], used['sa2'], used['none'],
                                     weighted, MOTORBIKE_SHARE), flush=True)
        for lga, row in by_lga.items():
            print('   %-16s identity %.5f  intended before %.5f  factor %.4f'
                  % (lga, row['identity'], row['intended_before'],
                     row['conservation_factor']), flush=True)
        if cells_tgt is not None:
            carve_cells['target_lga_cells_summed'] = round(cells_tgt, 7)
            print('   %s SA1 cells summed %.7f against the declared identity '
                  '%.7f (ABS small-cell perturbation; the declared value is '
                  'the basis)' % (tgt, cells_tgt, MOTORBIKE_SHARE), flush=True)
    report = {}
    for d in day_types:
        write_day(d, attrs, rng, report, seed_table)
    meta = dict(seed=seed, seed_mode=seed_mode,
                # 9.120: the seed METHOD - `full_choice_set` writes one plan
                # per usable mode and the split below is then only the
                # selected plan's draw
                seed_method=SEED_METHOD,
                # 9.122: the carve's resolution and, per cell, what it solved
                motorbike_carve=carve_cells or dict(resolution='region',
                                                    declared_region_share=MOTORBIKE_SHARE),
                # 9.125: the resident truck carve's declared share and solved q
                truck_carve=dict(declared_share=TRUCK_RESIDENT_SHARE,
                                 q=round(_TRUCK_Q['q'], 6)),
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
    json.dump(meta, open(os.path.join(OUT, '_plans_report.json'), 'w', newline='\n'), indent=2)


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
