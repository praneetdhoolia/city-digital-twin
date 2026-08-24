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
    # Closures are spread EVENLY across the declared window: no closure log is
    # published (9.70), so any temporal pattern would be invented. Uniform
    # spacing is the least-informative deterministic choice, and both the count
    # and the duration are swept. The sites are PHASE-OFFSET from each other
    # (site i shifted by i/n_sites of one interval): one boom is not the
    # other's, and synchronising them would overstate coincident closure.
    w0, w1 = [h * 3600.0 for h in CLOSURE_WINDOW_H]
    n = int(CLOSURES_PER_DAY)
    interval = (w1 - w0) / n
    root = ET.Element('networkChangeEvents',
                      {'xmlns': 'http://www.matsim.org/files/dtd',
                       'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                       'xsi:schemaLocation':
                           'http://www.matsim.org/files/dtd '
                           'http://www.matsim.org/files/dtd/networkChangeEvents.xsd'})
    n_events = 0
    events = []
    for si, site in enumerate(sites):
        for i in range(n):
            start = w0 + (i + 0.5 + si / max(1, len(sites))) * interval
            if start + CLOSURE_DURATION_S > w1:
                start = w1 - CLOSURE_DURATION_S
            events.append((start, site))
    for start, site in sorted(events, key=lambda t: t[0]):
        end = start + CLOSURE_DURATION_S
        close = ET.SubElement(root, 'networkChangeEvent',
                              {'startTime': hhmmss(start)})
        for sl in site['links']:
            ET.SubElement(close, 'link', {'refId': sl['link']['id']})
        ET.SubElement(close, 'freespeed',
                      {'type': 'absolute', 'value': '%g' % CLOSED_FREESPEED})
        ET.SubElement(close, 'flowCapacity',
                      {'type': 'absolute',
                       'value': '%g' % (CLOSED_FLOW / 3600.0)})
        n_events += 1
        # restoration must return each link to ITS OWN recorded values; with
        # several links per event that needs one event per distinct value set,
        # so restores are emitted per link
        for sl in site['links']:
            r = ET.SubElement(root, 'networkChangeEvent',
                              {'startTime': hhmmss(end)})
            ET.SubElement(r, 'link', {'refId': sl['link']['id']})
            ET.SubElement(r, 'freespeed',
                          {'type': 'absolute',
                           'value': '%g' % sl['link']['freespeed']})
            ET.SubElement(r, 'flowCapacity',
                          {'type': 'absolute',
                           'value': '%g' % (sl['link']['capacity'] / 3600.0)})
            n_events += 1

    ET.indent(root)
    ET.ElementTree(root).write(OUT_XML, encoding='UTF-8', xml_declaration=True)

    report = dict(
        purpose='freight level-crossing closures (issue #68, DECISIONS.md 9.70/9.76)',
        derivation='OSM railway=level_crossing nodes with a boom-barrier tag, '
                   'clustered, matched to car links by the network\'s own '
                   'osm:way:name against the declared road names. No typed '
                   'coordinate.',
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
            timing_source='assumed (closure logs unpublished; swept, 9.70)',
            spacing='uniform per site across the window, sites phase-offset from each other - any richer pattern would be invented'),
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
