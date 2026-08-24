#!/usr/bin/env python
"""Represent the light-rail charging dwell natively in the transit schedule
(issue #74; DECISIONS.md 9.74/9.76).

With SUMO descoped (9.74), MATSim is the only home for the wire-free
charging-dwell question (S2 vs S2a). Until now the dwell lived only INSIDE the
scheduled run times (`build_scenario_schedules.py` scales the GTFS timeline by
the run-time decomposition), so a tram never physically HELD at a stop - the
dwell was schedule padding, invisible to the corridor's traffic. This builder
makes it a mechanism: at every INTERMEDIATE stop of each intervention-mode
route, `departureOffset = arrivalOffset + max(existing gap, dwell_charging_s)`
with `awaitDepartureTime` on, so the vehicle occupies the stop for the dwell
and the signal/traffic interaction (#73's world) sees it.

**Derivation rule (DECISIONS.md 3.5):** the input is each scenario's OWN
already-mapped schedule; the mapper is never re-run. Arrival offsets are NOT
touched, so the end-to-end scheduled run time - a calibration anchor the
model reproduces by construction (12.1) - is byte-identical before and after.
What changes is only where inside the timeline the tram waits.

**Concurrent, not additive (decision recorded in 9.76):** charging on the CAF
Urbos happens DURING passenger exchange - that is the point of charge-at-stop
- so dwell = max(boarding, charging) and plain offsets suffice. The additive
reading (dwell = boarding + charging) would need a custom TransitStopHandler
and would double-count the boarding time the scheduled gap already carries.

**Per-scenario values come from each scenario's own overlay resolution**
(`A.lightrail.dwell_charging_s`: 20 s swept 10-35 in S2; 0 in S2a - the field
STAYS swept, never pinned, 9.74). A zero dwell is an identity transform, which
is exactly what S2a means.

**Sequencing (9.75):** built INERT - output lands beside the mapped schedule
as `transitSchedule_dwell.xml.gz` and nothing consumes it until the batched
family boundary re-derives the run-input sets from it.

    python cities/newcastle/build/build_charging_dwell_offsets.py
"""

# This builder encodes THIS CITY's intervention, so it lives with the city.
import os as _os
import sys as _sys
_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.dirname(_os.path.abspath(__file__)))))
_sys.path.insert(0, _os.path.join(_REPO, 'src'))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402

import gzip
import json
import os
import xml.etree.ElementTree as ET

SCHEDULES = _city.path('networks', 'matsim', 'schedules')
OUT_REPORT = os.path.join(SCHEDULES, '_dwell_report.json')
INTERVENTION_MODE = _city.descriptor()['intervention']['mode']


def parse_offset(text):
    h, m, s = text.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def fmt_offset(seconds):
    return '%02d:%02d:%02d' % (seconds // 3600, (seconds % 3600) // 60,
                               seconds % 60)


def transform_schedule(src, dst, dwell_s):
    """Apply the dwell to every intermediate intervention-mode stop.

    Returns (routes_touched, stops_held, max_hold_s). Raises if a hold would
    consume the whole gap to the next stop - that would mean the dwell no
    longer fits inside the scheduled timeline and arrival offsets would have
    to move, which this builder refuses to do (the 12.00 min scheduled run
    time is an anchor, 12.1)."""
    with gzip.open(src, 'rt', encoding='utf-8') as f:
        tree = ET.parse(f)
    root = tree.getroot()
    routes_touched = stops_held = 0
    max_hold = 0
    for line in root.iter('transitLine'):
        for route in line.findall('transitRoute'):
            if route.findtext('transportMode') != INTERVENTION_MODE:
                continue
            prof = route.find('routeProfile')
            stops = prof.findall('stop')
            touched = False
            for k in range(1, len(stops) - 1):
                arr = parse_offset(stops[k].get('arrivalOffset'))
                dep_old = parse_offset(stops[k].get('departureOffset'))
                gap = dep_old - arr
                hold = max(gap, int(round(dwell_s)))
                nxt = parse_offset(stops[k + 1].get('arrivalOffset'))
                if arr + hold >= nxt:
                    raise SystemExit(
                        '%s: a %ds hold at stop %s leaves no running time '
                        'to the next stop (arr %s, next arr %s). The dwell '
                        'no longer fits inside the scheduled timeline - '
                        'that needs a schedule change, not an offset one.'
                        % (os.path.basename(src), hold,
                           stops[k].get('refId'),
                           stops[k].get('arrivalOffset'),
                           stops[k + 1].get('arrivalOffset')))
                if hold != gap:
                    stops[k].set('departureOffset', fmt_offset(arr + hold))
                    stops[k].set('awaitDeparture', 'true')
                    stops_held += 1
                    touched = True
                max_hold = max(max_hold, hold)
            if touched:
                routes_touched += 1
    with gzip.open(dst, 'wt', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE transitSchedule SYSTEM '
                '"http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n')
        f.write(ET.tostring(root, encoding='unicode'))
    return routes_touched, stops_held, max_hold


def main():
    report = dict(
        purpose='native charging dwell in the transit schedule (issue #74)',
        rule='departureOffset = arrivalOffset + max(existing gap, '
             'A.lightrail.dwell_charging_s) at INTERMEDIATE intervention-mode '
             'stops; arrival offsets untouched, so end-to-end scheduled run '
             'time is unchanged by construction',
        concurrency='CONCURRENT with boarding: dwell = max(board, charge) - '
                    'charge-at-stop happens during passenger exchange, so '
                    'plain offsets suffice and boarding time is not '
                    'double-counted (decision, DECISIONS.md 9.76)',
        derivation='from each scenario\'s own already-mapped schedule; the '
                   'mapper is never re-run (DECISIONS.md 3.5)',
        activation='INERT until the batched family boundary re-derives the '
                   'run-input sets from transitSchedule_dwell.xml.gz',
        scenarios={})
    for scenario in sorted(os.listdir(SCHEDULES)):
        src = os.path.join(SCHEDULES, scenario, 'transitSchedule.xml.gz')
        if not os.path.isfile(src) or scenario.startswith(('era', 'base')):
            continue
        cfg = _registry.load(scenario=scenario)
        try:
            dwell = cfg.get('A.lightrail.dwell_charging_s')
        except _registry.RegistryError:
            # the field is swept/unresolved for this scenario: skip, stated
            report['scenarios'][scenario] = dict(skipped='no resolved dwell')
            continue
        dst = os.path.join(SCHEDULES, scenario, 'transitSchedule_dwell.xml.gz')
        routes, stops, max_hold = transform_schedule(src, dst, dwell)
        report['scenarios'][scenario] = dict(
            dwell_charging_s=dwell, routes_touched=routes, stops_held=stops,
            max_hold_s=max_hold,
            output=_city.rel(dst))
        print('%-5s dwell %5.1fs  routes touched %4d  stops held %5d -> %s'
              % (scenario, dwell, routes, stops, os.path.basename(dst)))
    with open(OUT_REPORT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('report -> %s' % OUT_REPORT)


if __name__ == '__main__':
    main()
