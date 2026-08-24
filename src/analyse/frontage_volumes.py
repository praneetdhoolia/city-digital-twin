#!/usr/bin/env python
"""Pedestrian volumes past the corridor's frontage links, from a run's own
physical walk events (task 4.7.10; hypothesis B1's fallback instrument).

No pedestrian count is published for this city, which leaves hypothesis B1
(frontage footfall) with no observable (STATUS, P6 6.1). But since 9.53 walk
is PHYSICALLY simulated - every walking agent traverses real links and emits
real link events - so the model can at least produce the MODELLED half of the
comparison: walk traversals per corridor frontage link per hour, from
`output_events.xml.gz`. That is an instrument, not a result: it reports what
the model's pavement carries so that a scenario-vs-scenario footfall DELTA
exists the day scenarios run, and it informs the pending 6.1 REWORK decision
(fallback-only vs buy counters vs report B1 untestable).

Mode attribution is by the events' own `VehicleEntersTraffic.networkMode` -
never by vehicle-id string convention (car vehicles carry the bare person id,
the recorded trap). Frontage links are the corridor trunk edges of
`A1_corridor_road_edges.csv` resolved through the network's `osm:way:id`
attribute - no typed coordinate, no name heuristic.

    python src/analyse/frontage_volumes.py --run results/<run>
"""
import argparse
import collections
import csv
import gzip
import io
import json
import os
import sys
import xml.etree.ElementTree as ET

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import city as _city  # noqa: E402

CORRIDOR = _city.path('data/processed/network/A1_corridor_road_edges.csv')


def frontage_way_ids():
    """The corridor trunk's OSM way ids - the frontage B1 is defined over."""
    ways = set()
    with open(CORRIDOR, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r.get('is_corridor_trunk') == '1':
                ways.add(r['edge_id'].lstrip('w'))
    return ways


def frontage_links(network_path, way_ids):
    """network link id -> (osm way id, length) for links on frontage ways
    that walk may use."""
    out = {}
    with gzip.open(network_path, 'rb') as f:
        for ev, el in ET.iterparse(f, events=('end',)):
            if el.tag == 'link':
                modes = (el.get('modes') or '').split(',')
                if 'walk' in modes:
                    attrs = {a.get('name'): a.text
                             for a in el.iter('attribute')}
                    wid = attrs.get('osm:way:id')
                    if wid in way_ids:
                        out[el.get('id')] = (wid, float(el.get('length')))
                el.clear()
    return out


def count_walk_traversals(events_path, links):
    """(link, hour) -> walk traversals, streaming the events file once.

    A vehicle's mode for its CURRENT traversal comes from its
    VehicleEntersTraffic event; LinkEnter events while that mode is `walk`
    are footfall. Wait-at-stop, boarding and teleported stages emit no link
    events, so nothing here double-counts a PT access stage - only the
    physically walked links count, which is what a footfall instrument
    means."""
    by_link_hour = collections.Counter()
    mode_of_vehicle = {}
    with gzip.open(events_path, 'rb') as f:
        for ev, el in ET.iterparse(f, events=('end',)):
            if el.tag != 'event':
                continue
            t = el.get('type')
            if t == 'vehicle enters traffic':
                mode_of_vehicle[el.get('vehicle')] = el.get('networkMode')
            elif t == 'vehicle leaves traffic':
                mode_of_vehicle.pop(el.get('vehicle'), None)
            elif t == 'entered link':
                link = el.get('link')
                if (link in links
                        and mode_of_vehicle.get(el.get('vehicle')) == 'walk'):
                    hour = int(float(el.get('time'))) // 3600
                    by_link_hour[(link, hour)] += 1
            el.clear()
    return by_link_hour


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True, help='a results/<name> directory')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    run_dir = (a.run if os.path.isdir(a.run)
               else os.path.join(ROOT, 'results', a.run))
    rec = json.load(open(os.path.join(run_dir, '_run.json'), encoding='utf-8'))
    events = os.path.join(run_dir, 'output', 'output_events.xml.gz')
    if not os.path.exists(events):
        raise SystemExit('no %s - the run kept no final events file' % events)
    # the run's own network: the config points at the scenario network the
    # run actually loaded
    cfg_text = open(os.path.join(run_dir, 'config.xml'), encoding='utf-8').read()
    import re
    m = re.search(r'name="inputNetworkFile" value="([^"]+)"', cfg_text)
    network = m.group(1)
    if not os.path.exists(network):
        # runs recorded before the repository rename carry the old absolute
        # path; the scenario's network is the same file at its current home
        network = _city.path('scenarios', 'matsim', rec['scenario'],
                             'network.xml.gz')

    ways = frontage_way_ids()
    links = frontage_links(network, ways)
    if not links:
        raise SystemExit('no walkable frontage links found in %s' % network)
    counts = count_walk_traversals(events, links)

    fraction = rec['fraction']
    rows_out = []
    per_link = collections.Counter()
    for (link, hour), n in sorted(counts.items()):
        wid, length = links[link]
        per_link[link] += n
        rows_out.append(dict(link=link, osm_way_id=wid, length_m=length,
                             hour=hour, walk_traversals=n,
                             walk_traversals_scaled=round(n / fraction)))
    out = a.out or os.path.join(run_dir, '_frontage_volumes.csv')
    with io.open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['link', 'osm_way_id', 'length_m',
                                          'hour', 'walk_traversals',
                                          'walk_traversals_scaled'])
        w.writeheader()
        w.writerows(rows_out)
    summary = dict(
        run=rec['name'], scenario=rec['scenario'], day=rec['day'],
        fraction=fraction,
        frontage_walk_links=len(links),
        links_with_walk_traffic=len(per_link),
        total_walk_traversals=sum(counts.values()),
        total_scaled=round(sum(counts.values()) / fraction),
        note='MODELLED footfall on the corridor frontage links, from the '
             'final iteration\'s physical walk events. An instrument for the '
             'B1 scenario-vs-scenario delta (task 4.7.10; informs the 6.1 '
             'REWORK decision). NOT a result, and comparable to no observed '
             'count - none is published.')
    with io.open(os.path.splitext(out)[0] + '.json', 'w', encoding='utf-8',
                 newline='\n') as f:
        json.dump(summary, f, indent=2)
        f.write('\n')
    print('%s: %d frontage walk links, %d with walk traffic, %d traversals '
          '(scaled %d) -> %s'
          % (rec['name'], len(links), len(per_link), sum(counts.values()),
             summary['total_scaled'], out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
