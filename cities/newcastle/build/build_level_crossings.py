#!/usr/bin/env python
"""Build the freight level-crossing closure events (issue #68, DECISIONS.md 9.70).

The Hunter Valley coal chain is deliberately NOT simulated - it runs on
dedicated track grade-separated from the modelled passenger line since the 2006
Sandgate Flyover (9.70). The two real interactions between rail freight and the
modelled ROAD network are boom-gated level crossings, and this builder turns
them into MATSim `networkChangeEvents`: a closure drops the crossing links'
flow capacity to zero (with a small nonzero freespeed floor so the router's
arithmetic stays finite) and a second event restores each link's OWN recorded
values when the boom lifts.

**Everything is derived or declared - no typed coordinate, no place name in
code.** The crossings are located from OSM `railway=level_crossing` nodes that
carry a boom-barrier tag (`crossing:barrier` other than no/none), clustered,
and matched to MATSim links through the network's own `osm:way:name` attribute
against the DECLARED road names (`A.crossings.freight_road_names`, literature:
the TfNSW Lower Hunter Freight Corridor Draft SEA names the St James Road
crossing's "up to ten minutes" delays; 9.70 records both interactions).
Closure count and duration are ASSUMED AND SWEPT - closure logs are not
published (9.70), so neither is ever pinned.

**The Stewart Avenue rule (9.75) is asserted, not assumed:** the corridor's
light-rail crossing at Stewart Avenue is a T-aspect SIGNAL site, not a boom
gate - it belongs to the signal build (#73) and must never be double-treated.
Its OSM nodes carry `crossing:barrier=no`, so the barrier filter already
excludes it; this builder additionally REFUSES to emit any closure within the
declared exclusion distance of the tram alignment, so the two mechanisms
cannot silently overlap even if tagging changes.

**Sequencing (9.75):** this output is built INERT. Nothing here touches the
assembled run-input sets; the closure events activate only at the batched
family boundary, which also needs `RUN.travel_time.bin_size_s` at or below
300 s so the router can see a closure shorter than a bin (the field is
declared with exactly that basis).

Output: `networks/matsim/crossings/crossing_change_events.xml` (+ a report
JSON beside it), regenerable from the committed inputs.
"""

# This builder encodes THIS CITY's freight-crossing interactions, so it lives
# with the city rather than in the framework.
import os as _os
import sys as _sys
_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.dirname(_os.path.abspath(__file__)))))
_sys.path.insert(0, _os.path.join(_REPO, 'src'))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402

import gzip
import json
import math
import os
import re
import xml.etree.ElementTree as ET

CFG = _registry.load()

RAILWAYS_OSM = _city.path('networks/osm/railways.osm')
BASE_NETWORK = _city.path('networks/matsim/base/network.xml.gz')
A2_SIGNALS = _city.path('data/processed/corridor/A2_signal_control_corridor.csv')
OUT_DIR = _city.path('networks/matsim/crossings')
OUT_XML = os.path.join(OUT_DIR, 'crossing_change_events.xml')
OUT_REPORT = os.path.join(OUT_DIR, '_crossings_report.json')

ROAD_NAMES = CFG.get('A.crossings.freight_road_names')
CLOSURES_PER_DAY = CFG.get('A.crossings.closures_per_day')
CLOSURE_DURATION_S = CFG.get('A.crossings.closure_duration_s')
CLOSURE_WINDOW_H = CFG.get('A.crossings.closure_window_h')
CLOSED_FLOW = CFG.get('A.crossings.closed_flow_capacity_veh_h')
CLOSED_FREESPEED = CFG.get('A.crossings.closed_freespeed_ms')
MATCH_RADIUS_M = CFG.get('A.crossings.link_match_radius_m')
CLUSTER_M = CFG.get('A.crossings.node_cluster_m')
CORRIDOR_EXCLUSION_M = CFG.get('A.crossings.corridor_exclusion_m')
CLOSURE_SOURCE = CFG.get('A.crossings.closure_source')
FREIGHT_CLOSURES = CFG.get('A.crossings.freight_closures_per_day')

# The mapped WEEKDAY schedule is the timetable a closure is derived from. It is
# the scenario's own already-mapped feed, never a re-run of the mapper
# (DECISIONS.md 3.5): schedule mapping is not reproducible run to run, so a
# second mapping would put the trains on different links from the ones the
# scenario actually simulates.
SCHEDULE = _city.path(
    'scenarios/matsim/%s/WEEKDAY/transitSchedule.xml.gz'
    % _city.descriptor()['intervention']['base_scenario'])
RAIL_MATCH_M = CFG.get('A.crossings.rail_match_radius_m')
CLOSURE_DURATION_PASSENGER_S = CFG.get(
    'A.crossings.closure_duration_passenger_s')


def boom_crossing_nodes():
    """OSM level-crossing nodes with a boom barrier, from the rail layer.

    `crossing:barrier=no` - which is what the Stewart Avenue T-aspect site
    carries - is excluded here, by tag, not by name."""
    out = []
    for ev, el in ET.iterparse(RAILWAYS_OSM, events=('end',)):
        if el.tag == 'node':
            tags = {t.get('k'): t.get('v') for t in el.findall('tag')}
            if (tags.get('railway') == 'level_crossing'
                    and tags.get('crossing:barrier') not in (None, 'no', 'none')):
                out.append(dict(osm_node_id=el.get('id'),
                                lat=float(el.get('lat')),
                                lon=float(el.get('lon')),
                                barrier=tags.get('crossing:barrier')))
            el.clear()
        elif el.tag == 'way':
            el.clear()
    return out


def project(nodes):
    import pyproj
    tf = pyproj.Transformer.from_crs('EPSG:4326', _city.crs(), always_xy=True)
    for n in nodes:
        n['x'], n['y'] = tf.transform(n['lon'], n['lat'])
    return nodes


def cluster(nodes, radius):
    """Group nodes closer than `radius` (a double-track crossing is two OSM
    nodes a few metres apart). Greedy, order-independent enough at 50 m."""
    clusters = []
    for n in sorted(nodes, key=lambda n: n['osm_node_id']):
        for c in clusters:
            if math.hypot(c['x'] - n['x'], c['y'] - n['y']) <= radius:
                c['members'].append(n)
                c['x'] = sum(m['x'] for m in c['members']) / len(c['members'])
                c['y'] = sum(m['y'] for m in c['members']) / len(c['members'])
                break
        else:
            clusters.append(dict(x=n['x'], y=n['y'], members=[n]))
    return clusters


def read_network(path):
    """Nodes and car links, each with its own capacity and freespeed."""
    nodes, links = {}, []
    with gzip.open(path, 'rb') as f:
        for ev, el in ET.iterparse(f, events=('end',)):
            if el.tag == 'node':
                nodes[el.get('id')] = (float(el.get('x')), float(el.get('y')))
                el.clear()
            elif el.tag == 'link':
                modes = (el.get('modes') or '').split(',')
                attrs = {a.get('name'): a.text for a in el.iter('attribute')}
                if 'car' in modes:
                    links.append(dict(
                        id=el.get('id'), frm=el.get('from'), to=el.get('to'),
                        capacity=float(el.get('capacity')),
                        freespeed=float(el.get('freespeed')),
                        name=attrs.get('osm:way:name'),
                        way=attrs.get('osm:way:id')))
                el.clear()
    return nodes, links


def corridor_intersections():
    """The 14 corridor intersections' projected coordinates from A2 - the
    alignment's own declared point set (the BASE network carries no mapped
    tram links; the alignment lives in the scenario networks, DECISIONS 9.3)."""
    import csv
    import pyproj
    tf = pyproj.Transformer.from_crs('EPSG:4326', _city.crs(), always_xy=True)
    pts = {}
    with open(A2_SIGNALS, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            pts[r['intersection_id']] = tf.transform(float(r['lon']),
                                                     float(r['lat']))
    return pts


def seg_dist(px, py, ax, ay, bx, by):
    """Point-to-segment distance."""
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def hhmmss(seconds):
    s = int(round(seconds))
    return '%02d:%02d:%02d' % (s // 3600, (s % 3600) // 60, s % 60)


def rail_movements(site, rail_links, schedule_text, fac):
    """Scheduled times at which a train crosses this site, in seconds.

    A crossing closes for every train that crosses it - not for a number
    somebody chose - and the city's own mapped timetable says which services
    those are. A route is counted when its mapped link sequence traverses one
    of the rail links at the crossing; the closure time is that route's own
    stop time at its stop nearest the crossing, so a closure lands when the
    train is actually there rather than at a uniform tick.

    The residual is stated rather than hidden: the offset between the nearest
    stop and the crossing itself is not modelled, and at these two sites the
    nearest rail stop is the adjacent station, so it is well under a minute.
    """
    times = []
    for rid, body in re.findall(r'<transitRoute id="([^"]+)">(.*?)</transitRoute>',
                                schedule_text, re.S):
        mode = re.search(r'<transportMode>([^<]+)</transportMode>', body)
        if not mode or mode.group(1) != 'rail':
            continue
        links = set(re.findall(r'<link refId="([^"]+)"', body))
        if not (links & rail_links):
            continue
        nearest = None
        for sid, attrs in re.findall(r'<stop refId="([^"]+)"([^/]*)/>', body):
            if sid not in fac:
                continue
            dist = math.hypot(fac[sid][0] - site['x'], fac[sid][1] - site['y'])
            off = (re.search(r'departureOffset="([^"]+)"', attrs)
                   or re.search(r'arrivalOffset="([^"]+)"', attrs))
            if nearest is None or dist < nearest[0]:
                nearest = (dist, hhmmss_to_s(off.group(1)) if off else 0)
        if nearest is None:
            continue
        for dep in re.finditer(r'<departure[^>]*departureTime="([^"]+)"', body):
            times.append(hhmmss_to_s(dep.group(1)) + nearest[1])
    return sorted(times)


def merge_spans(spans):
    """Overlapping or touching closures become one closure.

    The boom does not lift between two trains that arrive inside one closure,
    and a model that lifts it would let traffic through a crossing that is
    shut. Touching spans merge too: a reopen and a reclose at the same second
    is not a gap anything can drive through.
    """
    out = []
    for start, end in sorted(spans):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(a, b) for a, b in out]


def hhmmss_to_s(text):
    h, m, sec = text.split(':')
    return int(h) * 3600 + int(m) * 60 + int(sec)


def rail_links_near(x, y, nodes, rail):
    """The mapped rail links whose midpoint lies within the declared radius."""
    out = set()
    for lid, frm, to in rail:
        if frm not in nodes or to not in nodes:
            continue
        ax, ay = nodes[frm]
        bx, by = nodes[to]
        if math.hypot((ax + bx) / 2 - x, (ay + by) / 2 - y) <= RAIL_MATCH_M:
            out.add(lid)
    return out


def read_rail_links(path):
    """(id, from, to) for every link the network permits a train on."""
    out = []
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        for line in fh:
            m = re.search(r'<link id="([^"]+)" from="([^"]+)" to="([^"]+)"'
                          r'[^>]*modes="([^"]*)"', line)
            if m and re.search(r'\b(rail|train)\b', m.group(4)):
                out.append((m.group(1), m.group(2), m.group(3)))
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    booms = project(boom_crossing_nodes())
    clusters = cluster(booms, CLUSTER_M)
    nodes, car_links = read_network(BASE_NETWORK)
    corridor_pts = corridor_intersections()

    # named-road candidate links, geometry-resolved per link
    named = [l for l in car_links if l['name'] in set(ROAD_NAMES)]

    sites = []
    for name in ROAD_NAMES:
        cands = [l for l in named if l['name'] == name]
        best = None
        for c in clusters:
            for l in cands:
                ax, ay = nodes[l['frm']]
                bx, by = nodes[l['to']]
                d = seg_dist(c['x'], c['y'], ax, ay, bx, by)
                if d <= MATCH_RADIUS_M:
                    if best is None or d < best['dist_m']:
                        best = dict(cluster=c, dist_m=round(d, 1))
        if best is None:
            raise SystemExit(
                'no boom-barrier level-crossing cluster lies within %g m of a '
                'network link named %r. The declared interaction set '
                '(A.crossings.freight_road_names) and the OSM harvest '
                'disagree - resolve before emitting closures.'
                % (MATCH_RADIUS_M, name))
        c = best['cluster']
        site_links = []
        for l in cands:
            ax, ay = nodes[l['frm']]
            bx, by = nodes[l['to']]
            d = seg_dist(c['x'], c['y'], ax, ay, bx, by)
            if d <= MATCH_RADIUS_M:
                site_links.append(dict(link=l, dist_m=round(d, 1)))
        sites.append(dict(road_name=name, x=c['x'], y=c['y'],
                          osm_nodes=[m['osm_node_id'] for m in c['members']],
                          barriers=sorted({m['barrier'] for m in c['members']}),
                          links=site_links))

    # ---- the Stewart Avenue rule (9.75): refuse a closure near the tram ----
    # The light-rail crossing is a T-aspect SIGNAL site (#73's mechanism, never
    # a boom gate). Asserted against the corridor's own A2 intersection set -
    # which brackets the alignment end to end, Stewart Avenue included - so
    # #68 and #73 cannot double-treat one movement even if OSM tagging shifts.
    for site in sites:
        nearest_id, d_tram = min(
            ((iid, math.hypot(site['x'] - x, site['y'] - y))
             for iid, (x, y) in corridor_pts.items()), key=lambda t: t[1])
        site['nearest_corridor_intersection'] = nearest_id
        site['dist_to_corridor_m'] = round(d_tram, 1)
        if d_tram < CORRIDOR_EXCLUSION_M:
            raise SystemExit(
                'crossing on %r sits %.0f m from corridor intersection %s, '
                'inside the %g m exclusion: the corridor crossing is a '
                'T-aspect signal site (#73), never a boom-gate closure (9.75).'
                % (site['road_name'], d_tram, nearest_id, CORRIDOR_EXCLUSION_M))

    # ---- emit the change events ----
    # Under `schedule_derived` (9.90, the default) a closure is emitted for
    # every SCHEDULED TRAIN that crosses, at the time the timetable says it
    # crosses - so the count is per site (110 at Adamstown, 204 at Islington)
    # and the pattern is peaked where the service is peaked. Non-timetabled
    # freight is added uniformly on top, and is zero by default because the
    # coal chain is grade-separated (9.70).
    #
    # Under `assumed_uniform` - every arm before 9.90 - closures are spread
    # EVENLY across the declared window because no closure log is published,
    # uniform spacing being the least-informative deterministic choice, with
    # the sites PHASE-OFFSET from each other so one boom is not the other's.
    w0, w1 = [h * 3600.0 for h in CLOSURE_WINDOW_H]
    n = int(CLOSURES_PER_DAY)
    interval = (w1 - w0) / n
    derived = CLOSURE_SOURCE == 'schedule_derived'
    if derived:
        rail = read_rail_links(BASE_NETWORK)
        text = gzip.open(SCHEDULE, 'rt', encoding='utf-8').read()
        fac = {m.group(1): (float(m.group(2)), float(m.group(3)))
               for m in re.finditer(
                   r'<stopFacility id="([^"]+)"[^>]*x="([^"]+)"[^>]*y="([^"]+)"',
                   text)}
        for site in sites:
            site['rail_links'] = sorted(rail_links_near(
                site['x'], site['y'], nodes, rail))
            if not site['rail_links']:
                raise SystemExit(
                    'no mapped rail link lies within %g m of the level '
                    'crossing on %r. A crossing with no railway is not a '
                    'crossing - resolve before emitting closures.'
                    % (RAIL_MATCH_M, site['road_name']))
            site['closure_times_s'] = rail_movements(
                site, set(site['rail_links']), text, fac)
            if not site['closure_times_s']:
                raise SystemExit(
                    'the mapped rail links at the crossing on %r carry NO '
                    'scheduled movement. Either the schedule mapping missed '
                    'the line or the links are the wrong ones; a silent zero '
                    'here would delete the crossing from the model.'
                    % site['road_name'])
    root = ET.Element('networkChangeEvents',
                      {'xmlns': 'http://www.matsim.org/files/dtd',
                       'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                       'xsi:schemaLocation':
                           'http://www.matsim.org/files/dtd '
                           'http://www.matsim.org/files/dtd/networkChangeEvents.xsd'})
    n_events = 0
    events = []
    for si, site in enumerate(sites):
        spans = []
        if derived:
            # One closure per scheduled train, at the time it crosses, for the
            # PASSENGER duration - the per-train figure, not the coal-train
            # one (9.90).
            for start in site['closure_times_s']:
                start = min(max(start, w0), w1 - CLOSURE_DURATION_PASSENGER_S)
                spans.append((start, start + CLOSURE_DURATION_PASSENGER_S))
            # Non-timetabled freight on top, spread evenly because no movement
            # log is published - zero by default on 9.70's grade separation -
            # and at the FREIGHT duration, which is what that 240 s describes.
            nf = int(FREIGHT_CLOSURES)
            for i in range(nf):
                start = w0 + (i + 0.5) * ((w1 - w0) / max(1, nf))
                start = min(start, w1 - CLOSURE_DURATION_S)
                spans.append((start, start + CLOSURE_DURATION_S))
        else:
            for i in range(n):
                start = w0 + (i + 0.5 + si / max(1, len(sites))) * interval
                if start + CLOSURE_DURATION_S > w1:
                    start = w1 - CLOSURE_DURATION_S
                spans.append((start, start + CLOSURE_DURATION_S))
        # A boom that is already down STAYS down. Two trains inside one
        # closure are one closure, not two, and emitting them separately would
        # reopen the road between them - and would hand MATSim two change
        # events on one link at overlapping times, which its time-variant
        # network refuses outright ("Expected number of change events (408)
        # differs from the number of events found (375)", measured on the
        # first derived probe). Merging is both the physical truth and the
        # thing that makes the accounting close.
        site['closure_spans_s'] = merge_spans(spans)
        for start, end in site['closure_spans_s']:
            events.append((start, end, site))
    for start, end, site in sorted(events, key=lambda t: (t[0], t[1])):
        close = ET.SubElement(root, 'networkChangeEvent',
                              {'startTime': hhmmss(start)})
        for sl in site['links']:
            ET.SubElement(close, 'link', {'refId': sl['link']['id']})
        # schema order is flowCapacity THEN freespeed (networkChangeEvents.xsd
        # sequence) - MATSim's validating reader refuses the reverse, measured
        # on the first activated probe (9.77)
        ET.SubElement(close, 'flowCapacity',
                      {'type': 'absolute',
                       'value': '%g' % (CLOSED_FLOW / 3600.0)})
        ET.SubElement(close, 'freespeed',
                      {'type': 'absolute', 'value': '%g' % CLOSED_FREESPEED})
        n_events += 1
        # restoration must return each link to ITS OWN recorded values; with
        # several links per event that needs one event per distinct value set,
        # so restores are emitted per link
        for sl in site['links']:
            r = ET.SubElement(root, 'networkChangeEvent',
                              {'startTime': hhmmss(end)})
            ET.SubElement(r, 'link', {'refId': sl['link']['id']})
            ET.SubElement(r, 'flowCapacity',
                          {'type': 'absolute',
                           'value': '%g' % (sl['link']['capacity'] / 3600.0)})
            ET.SubElement(r, 'freespeed',
                          {'type': 'absolute',
                           'value': '%g' % sl['link']['freespeed']})
            n_events += 1

    ET.indent(root)
    ET.ElementTree(root).write(OUT_XML, encoding='UTF-8', xml_declaration=True)

    report = dict(
        purpose='freight level-crossing closures (issue #68, DECISIONS.md 9.70/9.76)',
        derivation='OSM railway=level_crossing nodes with a boom-barrier tag, '
                   'clustered, matched to car links by the network\'s own '
                   'osm:way:name against the declared road names. No typed '
                   'coordinate.',
        closure_source=CLOSURE_SOURCE,
        freight_closures_per_day=FREIGHT_CLOSURES,
        closures_per_site={s['road_name']: len(s.get('closure_times_s', []))
                           for s in sites},
        closure_spans_per_site={s['road_name']: len(s.get('closure_spans_s', []))
                                for s in sites},
        closed_seconds_per_site={
            s['road_name']: round(sum(b - a for a, b
                                      in s.get('closure_spans_s', [])), 1)
            for s in sites},
        sites=[{k: v for k, v in s.items() if k != 'links'} |
               {'links': [dict(id=sl['link']['id'], way=sl['link']['way'],
                               dist_m=sl['dist_m'],
                               base_capacity_veh_h=sl['link']['capacity'],
                               base_freespeed_ms=sl['link']['freespeed'])
                          for sl in s['links']]}
               for s in sites],
        parameters=dict(
            closures_per_day=CLOSURES_PER_DAY,
            closure_duration_s=CLOSURE_DURATION_S,
            closure_window_h=CLOSURE_WINDOW_H,
            closed_flow_capacity_veh_h=CLOSED_FLOW,
            closed_freespeed_ms=CLOSED_FREESPEED,
            timing_source=(
                'DERIVED from the mapped rail timetable (9.90): one closure '
                'per scheduled train that crosses, timed from that service '
                'own stop time at the nearest rail stop'
                if CLOSURE_SOURCE == 'schedule_derived'
                else 'assumed (closure logs unpublished; swept, 9.70)'),
            spacing=(
                "the timetable's own, so closures are peaked where the service "
                'is peaked; non-timetabled freight, if any is declared, is '
                'added uniformly because ARTC publishes no movement log'
                if CLOSURE_SOURCE == 'schedule_derived'
                else 'uniform per site across the window, sites phase-offset from each other - any richer pattern would be invented')),
        stewart_avenue_rule='asserted: every emitted site is >%g m from every '
                            'A2 corridor intersection (9.75)' % CORRIDOR_EXCLUSION_M,
        activation='INERT until the batched family boundary: nothing consumes '
                   'this file until network.timeVariantNetwork and the change '
                   'events path are wired at activation, with '
                   'RUN.travel_time.bin_size_s <= 300 s so the router can see '
                   'a closure (issue #68).')
    with open(OUT_REPORT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('crossings: %d site(s), %d links, %d change events -> %s'
          % (len(sites), sum(len(s['links']) for s in sites), n_events, OUT_XML))
    for s in sites:
        print('  %-18s nodes %s  barrier %s  links %s  corridor %.0f m (%s)'
              % (s['road_name'], ','.join(s['osm_nodes']),
                 '/'.join(s['barriers']),
                 ','.join(sl['link']['id'] for sl in s['links']),
                 s['dist_to_corridor_m'], s['nearest_corridor_intersection']))


if __name__ == '__main__':
    main()
