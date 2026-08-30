#!/usr/bin/env python
"""Measure why corridor PT demand boards buses rather than the tram.

DIAGNOSTIC MEASUREMENT OF AN EXISTING RUN - NOT A RESULT ABOUT THE LIGHT
RAIL. On the closed pre-repair family the light rail carried ~37% of its
observed boardings while the PT aggregate overshot (+116% relative,
DECISIONS.md 9.64) - the demand rides buses past the tram. This script
decomposes ONE completed run's corridor PT composition so the candidate
explanations each carry a number before the next repair family runs.
Nothing here compares scenario against scenario.

What it measures, all from the run's own artefacts:

1. CATCHMENT - the walkable band of the tram alignment is derived from
   the run's own mapped schedule (`output/output_transitSchedule.xml.gz`:
   the stops of every route with <transportMode>tram</transportMode>) and
   the transit router's declared `maxBeelineWalkConnectionDistance` from
   the run's config snapshot (`config.xml`). No typed coordinate, no
   hand-drawn extent, no invented radius.

2. COMPOSITION - PT trips (final-iteration realised legs/trips, the
   tables MATSim writes from the last iteration's events) whose origin or
   destination lies inside the band, split by the submodes they actually
   boarded (bus / tram / rail / ferry, from the schedule's per-route
   transportMode). Boarding counts are reconciled against the run's
   events-derived `_metrics.json` submode totals.

3. THE FOUR CANDIDATE EXPLANATIONS, each quantified:
   (a) frequency  - scheduled departures and headways on the tram routes
                    vs the bus routes that parallel the corridor (more
                    than one distinct in-band stop location - the
                    structural minimum for running ALONG rather than
                    across it), from the run's own day-filtered schedule;
   (b) times      - realised door-to-door, wait and in-vehicle time for
                    corridor trips that used bus vs those that used the
                    tram, next to the tram's scheduled offering
                    (end-to-end runtime, mean/peak headway);
   (c) coverage   - how many corridor-catchment trips have BOTH ends
                    inside the band (the tram could serve them alone) vs
                    ONE end (the tram needs a transfer for the far end,
                    a bus may not);
   (d) transfers  - one-seat vs multi-boarding rides among the corridor
                    bus trips, against the declared interchange price
                    (`utilityOfLineSwitch`) and waiting price
                    (`waitingPt`) from the run's config snapshot.

Usage:
    python src/analyse/measure_corridor_composition.py results/<run-dir>

Writes `_corridor_pt_composition.json` into the run directory (read-only
over everything else) and prints the tables. The run's comparability
family is read from the declared `docs/run_families.json` via
build_run_index, never re-derived. The holdout split under
`data/processed/validation/` is not read.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_run_index import load_families, family_of  # noqa: E402

def runs_along_band(n_inband_locations):
    """A route runs ALONG the corridor (rather than merely crossing or
    terminating at it) when it serves MORE THAN ONE distinct in-band stop
    location - the structural minimum for an alignment, which needs two
    points. A counting bound, not a model value: no behavioural or
    physical quantity depends on it, and it is stated in the output."""
    return n_inband_locations > 1


def hhmmss_to_s(t):
    if not t:
        return None
    h, m, s = t.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def fmt_min(seconds):
    return round(seconds / 60.0, 1) if seconds is not None else None


# --- the run's declared parameters (its own config snapshot) -----------------

def load_config_params(run_dir):
    """The declared values this diagnostic reuses, from the run's config.

    Nothing is typed in: the band radius is the transit router's
    maxBeelineWalkConnectionDistance; the interchange and waiting prices
    are the scoring parameters the run actually priced PT with.
    """
    tree = ET.parse(run_dir / 'config.xml')
    root = tree.getroot()
    out = {}
    for module in root.iter('module'):
        mname = module.get('name')
        if mname == 'transitRouter':
            for p in module.iter('param'):
                if p.get('name') == 'maxBeelineWalkConnectionDistance':
                    out['max_beeline_walk_connection_distance_m'] = \
                        float(p.get('value'))
        if mname in ('planCalcScore', 'scoring'):
            for p in module.iter('param'):
                if p.get('name') == 'utilityOfLineSwitch':
                    out['utility_of_line_switch'] = float(p.get('value'))
                if p.get('name') == 'waitingPt':
                    out['waiting_pt_util_hr'] = float(p.get('value'))
            for mp in module.iter('parameterset'):
                if mp.get('type') != 'modeParams':
                    continue
                kv = {p.get('name'): p.get('value')
                      for p in mp.findall('param')}
                if kv.get('mode') == 'pt':
                    out['pt_constant'] = float(kv.get('constant', 0.0))
                    out['pt_marginal_utility_of_traveling_util_hr'] = \
                        float(kv.get(
                            'marginalUtilityOfTraveling_util_hr', 0.0))
                else:
                    # Under pt-submode scoring (issue #49 Tier C, DECISIONS.md
                    # 9.78) each mapped submode carries its own constant, and
                    # a corridor diagnostic about WHY demand boards buses
                    # must report the bus-vs-tram price it actually ran with.
                    # Collected for every scored mode here; filtered to the
                    # mapped submodes once the swissRailRaptor module below
                    # says which those are.
                    out.setdefault('_mode_constants', {})[kv.get('mode')] = \
                        float(kv.get('constant', 0.0))
        if mname == 'swissRailRaptor':
            for mp in module.iter('parameterset'):
                if mp.get('type') != 'modeMapping':
                    continue
                kv = {p.get('name'): p.get('value')
                      for p in mp.findall('param')}
                if kv.get('passengerMode'):
                    out.setdefault('submode_passenger_modes', []).append(
                        kv['passengerMode'])
    if 'max_beeline_walk_connection_distance_m' not in out:
        raise SystemExit('transitRouter/maxBeelineWalkConnectionDistance not '
                         'found in the run config - cannot derive the band')
    mode_constants = out.pop('_mode_constants', {})
    for sub in sorted(out.get('submode_passenger_modes', [])):
        if sub in mode_constants:
            out.setdefault('submode_constants', {})[sub] = mode_constants[sub]
    return out


# --- the run's own mapped, day-filtered schedule -----------------------------

def load_schedule(run_dir):
    """Stops, per-route submode, stop sequences, offsets and departures."""
    stops = {}          # facility id -> (x, y, name)
    routes = {}         # (line, route) -> dict
    with gzip.open(run_dir / 'output' / 'output_transitSchedule.xml.gz',
                   'rb') as fh:
        root = ET.parse(fh).getroot()
    for sf in root.iter('stopFacility'):
        stops[sf.get('id')] = (float(sf.get('x')), float(sf.get('y')),
                               sf.get('name') or sf.get('id'))
    for line in root.iter('transitLine'):
        lid = line.get('id')
        for tr in line.findall('transitRoute'):
            rid = tr.get('id')
            mode = tr.findtext('transportMode')
            profile = [(st.get('refId'),
                        hhmmss_to_s(st.get('arrivalOffset')
                                    or st.get('departureOffset')))
                       for st in tr.find('routeProfile').findall('stop')]
            deps = sorted(hhmmss_to_s(d.get('departureTime'))
                          for d in tr.find('departures').findall('departure'))
            routes[(lid, rid)] = {'mode': mode, 'profile': profile,
                                  'departures': deps}
    return stops, routes


def dedupe_locations(stop_ids, stops):
    """Distinct physical stop locations (mapped facilities repeat one
    physical stop once per network link)."""
    return {(stops[s][0], stops[s][1]) for s in stop_ids if s in stops}


def headway_stats(deps):
    """Departure count, service span, mean headway and busiest clock hour -
    all derived from the schedule's own departure times."""
    if not deps:
        return None
    by_hour = Counter(int(d // 3600) for d in deps)
    peak_hour, peak_n = max(by_hour.items(), key=lambda kv: (kv[1], -kv[0]))
    gaps = [b - a for a, b in zip(deps, deps[1:])]
    return {
        'departures': len(deps),
        'first': fmt_min(deps[0]), 'last': fmt_min(deps[-1]),
        'span_h': round((deps[-1] - deps[0]) / 3600.0, 2),
        'mean_headway_min': fmt_min(statistics.mean(gaps)) if gaps else None,
        'median_headway_min': (fmt_min(statistics.median(gaps))
                               if gaps else None),
        'busiest_hour': f'{peak_hour:02d}:00', 'busiest_hour_departures': peak_n,
    }


# --- realised demand (final iteration) ---------------------------------------

def load_pt_legs(run_dir, routes):
    """Per-trip PT boardings from the run's realised legs table
    (written by MATSim from the final iteration's events)."""
    trips = defaultdict(list)   # trip_id -> [leg dict]
    boardings = Counter()       # submode -> boardings (all legs)
    unknown_route = 0
    with gzip.open(run_dir / 'output' / 'output_legs.csv.gz', 'rt',
                   encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter=';'):
            # A PT-vehicle leg is identified by the transit route it boarded,
            # never by the leg-mode label: under pt-submode scoring (issue
            # #49 Tier C, DECISIONS.md 9.78) the label is the scheduled
            # bus/tram/rail/ferry, and filtering on `mode == 'pt'` would
            # silently drop every boarding in the run.
            if not (r['transit_route'] or '').strip():
                continue
            key = (r['transit_line'], r['transit_route'])
            info = routes.get(key)
            if info is None:
                unknown_route += 1
                continue
            sub = info['mode']
            boardings[sub] += 1
            trips[r['trip_id']].append({
                'submode': sub,
                'line': r['transit_line'],
                'route': r['transit_route'],
                'access_stop': r['access_stop_id'],
                'egress_stop': r['egress_stop_id'],
                'wait_s': hhmmss_to_s(r['wait_time']),
                'trav_s': hhmmss_to_s(r['trav_time']),
            })
    return trips, boardings, unknown_route


def load_pt_trips(run_dir, pt_trip_ids):
    """Door-to-door geometry and time for every trip that boarded PT."""
    out = {}
    with gzip.open(run_dir / 'output' / 'output_trips.csv.gz', 'rt',
                   encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter=';'):
            if r['trip_id'] not in pt_trip_ids:
                continue
            out[r['trip_id']] = {
                'person': r['person'],
                'start_xy': (float(r['start_x']), float(r['start_y'])),
                'end_xy': (float(r['end_x']), float(r['end_y'])),
                'trav_s': hhmmss_to_s(r['trav_time']),
                'wait_s': hhmmss_to_s(r['wait_time']),
                'start_act': r['start_activity_type'],
                'end_act': r['end_activity_type'],
            }
    return out


def min_dist(pt, locations):
    x, y = pt
    return min(math.hypot(x - lx, y - ly) for lx, ly in locations)


def time_stats(values_s):
    v = [x for x in values_s if x is not None]
    if not v:
        return {'n': 0}
    return {'n': len(v), 'mean_min': fmt_min(statistics.mean(v)),
            'median_min': fmt_min(statistics.median(v))}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run_dir = Path(sys.argv[1])

    fams, overrides = load_families()
    family, fam_note = family_of(run_dir.name, fams, overrides)
    fam_label = next((f['label'] for k, f in fams if k == family), '')
    run_meta = json.loads((run_dir / '_run.json').read_text(encoding='utf-8'))
    metrics = json.loads(
        (run_dir / '_metrics.json').read_text(encoding='utf-8'))

    params = load_config_params(run_dir)
    band_m = params['max_beeline_walk_connection_distance_m']

    stops, routes = load_schedule(run_dir)

    # --- the corridor: tram stops and the walk band --------------------------
    tram_routes = {k: v for k, v in routes.items() if v['mode'] == 'tram'}
    tram_stop_ids = {s for v in tram_routes.values() for s, _ in v['profile']}
    tram_locs = dedupe_locations(tram_stop_ids, stops)
    tram_stop_names = sorted({stops[s][2] for s in tram_stop_ids})

    def in_band(pt):
        return min_dist(pt, tram_locs) <= band_m

    # every stop facility inside the band, and the routes serving them
    inband_stop_ids = {sid for sid, (x, y, _) in stops.items()
                       if in_band((x, y))}
    routes_by_inband_locs = {}
    for key, v in routes.items():
        locs = dedupe_locations(
            [s for s, _ in v['profile'] if s in inband_stop_ids], stops)
        if locs:
            routes_by_inband_locs[key] = len(locs)

    # (a) frequency: tram vs the parallel bus routes ---------------------------
    tram_sched = {}
    for (lid, rid), v in tram_routes.items():
        end_to_end = v['profile'][-1][1] - v['profile'][0][1]
        tram_sched[f'{lid} / {rid}'] = {
            'stops': len(v['profile']),
            'scheduled_end_to_end_min': fmt_min(end_to_end),
            **(headway_stats(v['departures']) or {}),
        }
    parallel_bus = {}
    bus_touching = 0
    for key, n_locs in sorted(routes_by_inband_locs.items()):
        if routes[key]['mode'] != 'bus':
            continue
        bus_touching += 1
        if runs_along_band(n_locs):
            lid, rid = key
            parallel_bus[f'{lid} / {rid}'] = {
                'in_band_stop_locations': n_locs,
                **(headway_stats(routes[key]['departures']) or {}),
            }
    # combined corridor bus service: all departures of parallel routes
    all_parallel_deps = sorted(
        d for key, v in routes.items()
        if routes[key]['mode'] == 'bus'
        and runs_along_band(routes_by_inband_locs.get(key, 0))
        for d in v['departures'])
    all_tram_deps = sorted(d for v in tram_routes.values()
                           for d in v['departures'])

    # --- realised corridor demand --------------------------------------------
    pt_legs, boardings_all, unknown_route = load_pt_legs(run_dir, routes)
    pt_trips = load_pt_trips(run_dir, set(pt_legs))

    catchment = {}   # trip_id -> classification
    for tid, t in pt_trips.items():
        o_in, d_in = in_band(t['start_xy']), in_band(t['end_xy'])
        if not (o_in or d_in):
            continue
        legs = pt_legs[tid]
        submodes = sorted({lg['submode'] for lg in legs})
        catchment[tid] = {
            'o_in': o_in, 'd_in': d_in, 'both': o_in and d_in,
            'submodes': '+'.join(submodes),
            'used_tram': 'tram' in submodes,
            'used_bus': 'bus' in submodes,
            'n_boardings': len(legs),
            'boarded_in_band': any(lg['access_stop'] in inband_stop_ids
                                   for lg in legs),
            'wait_s': sum(lg['wait_s'] or 0 for lg in legs),
            'ivt_s': sum((lg['trav_s'] or 0) - (lg['wait_s'] or 0)
                         for lg in legs),
            'door_s': t['trav_s'],
        }

    n_catch = len(catchment)
    submode_split = Counter(c['submodes'] for c in catchment.values())
    catch_boardings = Counter()
    for tid, c in catchment.items():
        for lg in pt_legs[tid]:
            catch_boardings[lg['submode']] += 1
    inband_boardings = Counter()
    for legs in pt_legs.values():
        for lg in legs:
            if lg['access_stop'] in inband_stop_ids:
                inband_boardings[lg['submode']] += 1

    bus_no_tram = [c for c in catchment.values()
                   if c['used_bus'] and not c['used_tram']]
    tram_users = [c for c in catchment.values() if c['used_tram']]

    # (c) coverage
    coverage = {
        'catchment_trips': n_catch,
        'both_ends_in_band': sum(1 for c in catchment.values() if c['both']),
        'one_end_in_band': sum(1 for c in catchment.values() if not c['both']),
        'bus_no_tram_trips': len(bus_no_tram),
        'bus_no_tram_both_ends_in_band':
            sum(1 for c in bus_no_tram if c['both']),
        'bus_no_tram_one_end_in_band':
            sum(1 for c in bus_no_tram if not c['both']),
        'both_ends_split': dict(Counter(
            c['submodes'] for c in catchment.values() if c['both'])),
    }

    # (d) transfers
    transfers = {
        'bus_no_tram_one_seat':
            sum(1 for c in bus_no_tram if c['n_boardings'] == 1),
        'bus_no_tram_multi_boarding':
            sum(1 for c in bus_no_tram if c['n_boardings'] > 1),
        'bus_no_tram_one_seat_with_far_end_outside_band':
            sum(1 for c in bus_no_tram
                if c['n_boardings'] == 1 and not c['both']),
        'tram_trips': len(tram_users),
        'tram_trips_multi_boarding':
            sum(1 for c in tram_users if c['n_boardings'] > 1),
        'tram_mean_boardings': (round(statistics.mean(
            c['n_boardings'] for c in tram_users), 2) if tram_users else None),
        'declared_utility_of_line_switch':
            params.get('utility_of_line_switch'),
        'declared_waiting_pt_util_hr': params.get('waiting_pt_util_hr'),
    }

    # (b) times
    times = {
        'bus_no_tram': {
            'door_to_door': time_stats([c['door_s'] for c in bus_no_tram]),
            'wait': time_stats([c['wait_s'] for c in bus_no_tram]),
            'in_vehicle': time_stats([c['ivt_s'] for c in bus_no_tram]),
        },
        'tram_users': {
            'door_to_door': time_stats([c['door_s'] for c in tram_users]),
            'wait': time_stats([c['wait_s'] for c in tram_users]),
            'in_vehicle': time_stats([c['ivt_s'] for c in tram_users]),
        },
        'both_ends_bus_no_tram': {
            'door_to_door': time_stats(
                [c['door_s'] for c in bus_no_tram if c['both']]),
            'wait': time_stats([c['wait_s'] for c in bus_no_tram if c['both']]),
            'in_vehicle': time_stats(
                [c['ivt_s'] for c in bus_no_tram if c['both']]),
        },
    }

    report = {
        'title': 'corridor PT composition: why the demand rides buses past '
                 'the tram, quantified on one completed run',
        'diagnostic_notice': (
            'DIAGNOSTIC MEASUREMENT OF AN EXISTING RUN - NOT A RESULT ABOUT '
            'THE LIGHT RAIL. The run measured is an arm of a CLOSED, '
            'pre-repair comparability family; nothing here is current model '
            'output and nothing compares scenario against scenario.'),
        'run': {
            'dir': run_dir.name,
            'family': family or 'unattributed',
            'family_label': fam_label,
            'family_note': fam_note,
            'scenario': run_meta.get('scenario'),
            'day': run_meta.get('day'),
            'fraction': run_meta.get('fraction'),
            'sample_note': 'counts are SAMPLE counts at this fraction; '
                           'shares and times are the comparable quantities',
        },
        'band': {
            'derivation': 'stops of every schedule route with '
                          'transportMode=tram, from the run\'s own mapped '
                          'day-filtered schedule; radius = the transit '
                          'router\'s declared '
                          'maxBeelineWalkConnectionDistance from the run\'s '
                          'config snapshot',
            'radius_m': band_m,
            'tram_stop_locations': len(tram_locs),
            'tram_stops': tram_stop_names,
            'stop_facilities_in_band': len(inband_stop_ids),
        },
        'declared_params_reused': params,
        'reconciliation': {
            'boardings_by_submode_legs_table': dict(sorted(boardings_all.items())),
            'boardings_by_submode_metrics_json': metrics.get(
                'pt_split', {}).get('boardings_by_submode'),
            'unknown_route_legs': unknown_route,
            'note': 'output_legs.csv.gz is written by MATSim from the final '
                    'iteration\'s events; the two columns must match',
        },
        'composition': {
            'pt_trips_total': len(pt_trips),
            'corridor_catchment_trips': n_catch,
            'catchment_definition': 'trip origin OR destination within '
                                    'radius_m of a tram stop location',
            'submode_split_of_catchment_trips': dict(
                sorted(submode_split.items(), key=lambda kv: -kv[1])),
            'boardings_by_submode_catchment_trips': dict(
                sorted(catch_boardings.items())),
            'boardings_at_in_band_stops_by_submode': dict(
                sorted(inband_boardings.items())),
        },
        'a_frequency': {
            'tram_routes': tram_sched,
            'tram_all_departures': headway_stats(all_tram_deps),
            'parallel_bus_route_definition':
                'bus route serving more than one distinct in-band stop '
                'location (the structural minimum for an alignment: running '
                'along the corridor rather than crossing it)',
            'parallel_bus_routes': parallel_bus,
            'parallel_bus_all_departures': headway_stats(all_parallel_deps),
            'bus_routes_touching_band': bus_touching,
        },
        'b_times': times,
        'c_coverage': coverage,
        'd_transfers': transfers,
    }

    out_path = run_dir / '_corridor_pt_composition.json'
    out_path.write_text(json.dumps(report, indent=1), encoding='utf-8')

    print(report['diagnostic_notice'])
    print(f"run {run_dir.name}  family {family} ({fam_label})  "
          f"scenario {run_meta.get('scenario')} {run_meta.get('day')} "
          f"fraction {run_meta.get('fraction')}")
    print(f"\nband: {len(tram_locs)} tram stop locations, radius {band_m} m "
          f"(declared maxBeelineWalkConnectionDistance); "
          f"{len(inband_stop_ids)} stop facilities in band")
    print(f"\nreconciliation legs-vs-metrics boardings: "
          f"{dict(sorted(boardings_all.items()))} vs "
          f"{report['reconciliation']['boardings_by_submode_metrics_json']}")
    print(f"\ncorridor catchment: {n_catch} of {len(pt_trips)} PT trips")
    print('submode split of catchment trips:')
    for k, v in sorted(submode_split.items(), key=lambda kv: -kv[1]):
        print(f'  {k:>24} {v:>7}  {v / n_catch:7.1%}')
    print('\n(a) frequency')
    for name, s in tram_sched.items():
        print(f'  tram {name}: {s["departures"]} deps, mean headway '
              f'{s["mean_headway_min"]} min, end-to-end '
              f'{s["scheduled_end_to_end_min"]} min')
    pb = report['a_frequency']['parallel_bus_all_departures']
    print(f'  parallel bus routes: {len(parallel_bus)} '
          f'(of {bus_touching} touching the band), combined '
          f'{pb["departures"] if pb else 0} departures')
    print('\n(b) times (door-to-door / wait / in-vehicle, mean min)')
    for grp in ('bus_no_tram', 'tram_users', 'both_ends_bus_no_tram'):
        t = times[grp]
        print(f'  {grp:>22}: n={t["door_to_door"]["n"]:>6} '
              f'door {t["door_to_door"].get("mean_min")} '
              f'wait {t["wait"].get("mean_min")} '
              f'ivt {t["in_vehicle"].get("mean_min")}')
    print('\n(c) coverage')
    for k, v in coverage.items():
        if k != 'both_ends_split':
            print(f'  {k}: {v}')
    print(f'  both_ends_split: {coverage["both_ends_split"]}')
    print('\n(d) transfers')
    for k, v in transfers.items():
        print(f'  {k}: {v}')
    print(f'\nwrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
