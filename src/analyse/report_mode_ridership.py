#!/usr/bin/env python
"""Every simulated mode, individually, against its own real-life target.

`measure_iteration_modes.py` scores one iteration against the SURVEY's
categories, which fold five modes into two targets and four into one. This
reports the same iteration against the per-mode targets the city derives in
`data/processed/validation/mode_targets_by_mode.csv`, one row per mode, so an
excess in one member of a fold cannot hide behind a deficit in the other.

Standing directive: **never an umbrella row.** `pt` is split into the submodes
the fleet already runs, read from the iteration's own legs table via each
boarded route's `transportMode` - the same resolution `extract_metrics.pt_split`
uses on a finished run, applied per iteration.

Three modes are NOT on the person-trip denominator and are printed with the
denominator they do have, never silently mixed in:

  truck          heavy vehicles as a share of road vehicles
  ferry          a target this city cannot observe - the level is printed,
                 the deviation is not, because there is nothing to deviate from
  freight_train  deliberately not simulated; the modelled zero is a DECISION

    python src/analyse/report_mode_ridership.py --run <run dir>
    python src/analyse/report_mode_ridership.py --run <run dir> --it 100

Reads the run directory and the city's target artefact. Writes nothing.
**Nothing here is a result**: a run without `_run.json` is not a result no
matter how it scores.
"""

import os as _os
import sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_os.path.join(_HERE, '..'), _os.path.join(_HERE, '..', 'calibrate')):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import csv
import gzip
import json
import time
import argparse
import collections

import city as _city                                              # noqa: E402
import registry as _registry                                      # noqa: E402
import extract_metrics as em                                      # noqa: E402
import measure_iteration_modes as mim                             # noqa: E402

# The city's own submode vocabulary maps onto the target file's mode names.
# A schedule calls the heavy-rail mode `rail` and the light-rail mode `tram`;
# the targets name them for what a reader of the survey would call them.
SUBMODE_TO_TARGET = {
    'bus': 'bus',
    'rail': 'heavy_rail',
    'train': 'heavy_rail',
    'tram': 'light_rail',
    'light_rail': 'light_rail',
    'ferry': 'ferry',
}

# Road vehicles, for the freight denominator. A ride passenger is NOT a
# vehicle - they travel in a car that is already counted - so ride is absent
# here by construction, not by oversight.
ROAD_VEHICLE_MODES = ('car', 'truck', 'motorbike', 'taxi')

# The gate's two thresholds are the DIRECTIVE's, not this script's, so they
# are declared like every other controllable value rather than typed here.
_CFG = _registry.load(strict=True)
GATE_STOP_PCT = float(_CFG.get('CAL.gate.stop_deviation_pct'))
GATE_PASS_PCT = float(_CFG.get('CAL.gate.pass_deviation_pct'))


def load_targets():
    """The city's per-mode targets, keyed by mode."""
    path = _city.path('data/processed/validation/mode_targets_by_mode.csv')
    if not _os.path.exists(path):
        raise SystemExit(
            'no per-mode target artefact at %s - build it with\n'
            '  python cities/<city>/build/build_mode_targets.py' % path)
    out = collections.OrderedDict()
    with open(path, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            def num(k):
                v = (r.get(k) or '').strip()
                return float(v) if v else None
            out[r['mode']] = dict(target=num('target_pct'),
                                  low=num('sweep_low'),
                                  high=num('sweep_high'),
                                  denominator=r['denominator'],
                                  status=r['status'],
                                  basis=r['basis'])
    return out


def pt_submode_trips(run_dir, iteration, person_lga):
    """Target-LGA linked pt trips, keyed by the submodes the trip boarded.

    A trip that boards more than one submode is counted once for EACH submode
    it used, because the question a per-mode target asks is "how many trips
    used this mode", not "how many trips used only this mode". The count of
    such trips is returned so the double-count is visible rather than implied.
    """
    route_mode = em.transit_route_modes(run_dir)
    stem = 'ITERS/it.%d/%d.legs' % (iteration, iteration)
    submodes = collections.defaultdict(set)
    unknown = 0
    with em.open_output(run_dir, stem) as fh:
        for l in csv.DictReader(fh, delimiter=';'):
            line = (l.get('transit_line') or '').strip()
            if not line:
                continue
            route = (l.get('transit_route') or '').strip()
            sm = route_mode.get((line, route))
            if sm is None:
                unknown += 1
                continue
            submodes[(l['person'], l['trip_id'])].add(sm)

    per_submode = collections.Counter()
    multi = 0
    stem = 'ITERS/it.%d/%d.trips' % (iteration, iteration)
    with em.open_output(run_dir, stem) as fh:
        for t in csv.DictReader(fh, delimiter=';'):
            if t['main_mode'] != 'pt':
                continue
            if person_lga.get(t['person']) != em.TARGET_LGA:
                continue
            sms = submodes.get((t['person'], t['trip_id']))
            if not sms:
                per_submode['pt:no_boarding'] += 1
                continue
            if len(sms) > 1:
                multi += 1
            for sm in sms:
                per_submode[SUBMODE_TO_TARGET.get(sm, sm)] += 1
    return per_submode, multi, unknown


def crossing_closures(run_dir):
    """Closure EPISODES this run applied, from its own change-events file.

    Freight rail reaches the road as timed capacity-zero events on the matched
    level-crossing links, so the modelled quantity for that mode is the number
    of closures the run actually loaded - not a trip count, and not zero. An
    episode is one event that takes flow capacity to zero; the paired reopening
    is not a second closure.
    """
    import re
    cfg = _os.path.join(run_dir, 'config.xml')
    if not _os.path.exists(cfg):
        return None
    text = open(cfg, encoding='utf-8').read()
    m = re.search(r'name="inputChangeEventsFile"\s+value="([^"]*)"', text)
    if not m or not m.group(1) or not _os.path.exists(m.group(1)):
        return None
    body = open(m.group(1), encoding='utf-8').read()
    return len(re.findall(r'<flowCapacity[^>]*value="0(?:\.0*)?"', body))


def road_vehicle_share(counts_all):
    """Heavy vehicles as a share of modelled road vehicle trips.

    Computed over EVERY subpopulation, not target-LGA residents: freight is
    not a resident's person trip, and scoring it on the resident denominator
    is the geography error that flatters or damns a mode for the wrong reason.
    """
    tot = sum(counts_all.get(m, 0) for m in ROAD_VEHICLE_MODES)
    if not tot:
        return None, 0
    return 100.0 * counts_all.get('truck', 0) / tot, tot


def report(run_dir, iteration):
    person_lga = em.home_lga()
    share = mim.mode_share_at(run_dir, iteration, person_lga)
    tgt = load_targets()

    lga_pct = share['target_lga_pct']
    lga_cnt = share['target_lga_counts']
    lga_tot = share['target_lga_trips']

    sub, multi, unknown = pt_submode_trips(run_dir, iteration, person_lga)

    # every subpopulation, for the freight denominator
    all_counts = collections.Counter()
    with em.open_output(run_dir, 'ITERS/it.%d/%d.trips'
                        % (iteration, iteration)) as fh:
        for t in csv.DictReader(fh, delimiter=';'):
            all_counts[t['main_mode']] += 1
    truck_pct, road_tot = road_vehicle_share(all_counts)
    closures = crossing_closures(run_dir)

    modelled = {}
    trips = {}
    for mode in tgt:
        if mode in ('bus', 'heavy_rail', 'light_rail', 'ferry'):
            n = sub.get(mode, 0)
            modelled[mode] = 100.0 * n / lga_tot if lga_tot else 0.0
            trips[mode] = n
        elif mode == 'truck':
            modelled[mode] = truck_pct
            trips[mode] = all_counts.get('truck', 0)
        elif mode == 'freight_train':
            modelled[mode] = None
            trips[mode] = closures if closures is not None else 0
        else:
            modelled[mode] = lga_pct.get(mode, 0.0)
            trips[mode] = lga_cnt.get(mode, 0)

    stamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    name = _os.path.basename(_os.path.normpath(run_dir))
    print('=' * 100)
    print('PER-MODE RIDERSHIP   %s   run %s   iteration %d' % (stamp, name, iteration))
    print('basis  linked main-mode trips, %s residents, from the iteration\'s '
          'own trips table (events-derived)' % em.TARGET_LGA)
    print('       pt split from that iteration\'s legs table by each boarded '
          'route\'s transportMode')
    print('=' * 100)
    print('%-15s %10s %10s %11s %12s  %s'
          % ('mode', 'modelled%', 'target%', 'deviation', 'count', 'gate'))
    print('-' * 100)

    breaches = []
    for i, (mode, t) in enumerate(tgt.items(), 1):
        m = modelled[mode]
        if t['status'] == 'not_simulated':
            print('%-15s %10s %10s %11s %12d  %s'
                  % ('%d %s' % (i, mode), '-', '-', '-', trips[mode],
                     'NOT SIMULATED (decision)'))
            continue
        if t['target'] is None:
            # a mode with no percentage denominator prints no percentage:
            # a 0.0000 in that column reads as "measured zero", which is the
            # opposite of "this quantity is not a share of anything"
            print('%-15s %10s %10s %11s %12d  %s'
                  % ('%d %s' % (i, mode),
                     '-' if m is None else '%.4f' % m,
                     'unobtained', 'n/a', trips[mode],
                     'NO TARGET - swept, never pinned'))
            continue
        dev = 100.0 * (m - t['target']) / t['target']
        if abs(dev) >= GATE_STOP_PCT:
            flag = 'STOP  >=%.0f%%' % GATE_STOP_PCT
            breaches.append((mode, m, t['target'], dev))
        elif abs(dev) >= GATE_PASS_PCT:
            flag = 'over %.0f%%' % GATE_PASS_PCT
        else:
            flag = 'ok'
        print('%-15s %10.4f %10.4f %+10.1f%% %12d  %s'
              % ('%d %s' % (i, mode), m, t['target'], dev, trips[mode], flag))

    print('-' * 100)
    print('target-LGA linked trips %d   modelled road vehicle trips %d '
          '(all subpopulations)' % (lga_tot, road_tot))
    if sub.get('pt:no_boarding'):
        print('pt trips that boarded nothing (raptor direct-walk fallback): %d'
              % sub['pt:no_boarding'])
    if multi:
        print('pt trips boarding more than one submode, counted once per '
              'submode used: %d' % multi)
    if unknown:
        print('pt legs whose route did not resolve to a submode: %d' % unknown)

    if breaches:
        print('\nGATE: %d mode(s) at or past %.0f%% deviation - the standing '
              'directive is to STOP the run and fix the cause from the root:'
              % (len(breaches), GATE_STOP_PCT))
        for mode, m, t, dev in sorted(breaches, key=lambda x: -abs(x[3])):
            print('   %-14s modelled %8.4f  target %8.4f  %+.1f%%'
                  % (mode, m, t, dev))
    else:
        print('\nGATE: no mode at or past %.0f%% deviation.' % GATE_STOP_PCT)
    return breaches


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--it', type=int,
                    help='iteration; default the newest one with a trips table')
    ap.add_argument('--all', action='store_true',
                    help='list the iterations this run holds and exit')
    a = ap.parse_args()

    have = mim.iterations_with_trips(a.run)
    if a.all:
        print(' '.join(str(i) for i in have))
        return
    if not have:
        raise SystemExit('%s holds no per-iteration trips table yet' % a.run)
    it = a.it if a.it is not None else have[-1]
    if it not in have:
        raise SystemExit('iteration %d has no trips table; this run holds %s'
                         % (it, ' '.join(str(i) for i in have)))
    report(a.run, it)


if __name__ == '__main__':
    main()
