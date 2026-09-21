"""Add provisional goods movements, independent of resident mode innovation."""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pyogrio

import city
import registry
import subpopulations
from build.extract_osm_network import fingerprint
from build.mode_connectivity import largest_strong_component

OUTPUT_INPUTS = {
    'demand/baseline/plans_with_freight.xml.gz': [
        'demand/baseline/plans_with_activities.xml.gz', 'registry/B_baseline_freight.json',
        'networks/matsim/schedules/baseline_regional/network.xml.gz',
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/observed/tbtt_2018_reported_aggregates.csv',
        'data/processed/observed/jnpa_rake_observations.csv'],
    'demand/baseline/freight_movements.csv': [
        'demand/baseline/plans_with_activities.xml.gz', 'registry/B_baseline_freight.json',
        'networks/matsim/schedules/baseline_regional/network.xml.gz',
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/observed/tbtt_2018_reported_aggregates.csv',
        'data/processed/observed/jnpa_rake_observations.csv'],
    'data/processed/acquisition/baseline_freight.json': [
        'demand/baseline/plans_with_activities.xml.gz', 'registry/B_baseline_freight.json',
        'networks/matsim/schedules/baseline_regional/network.xml.gz',
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/observed/tbtt_2018_reported_aggregates.csv',
        'data/processed/observed/jnpa_rake_observations.csv'],
}


def rows(relative):
    with Path(city.path(relative)).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def modal_anchors(links, nodes, mode, port, axes, limit):
    selected = [l for l in links if mode in l['modes'].split(',')]
    largest = largest_strong_component((l['from'], l['to']) for l in selected)
    connected = [l for l in selected if l['from'] in largest and l['to'] in largest]
    if not connected:
        raise ValueError('No connected freight network for ' + mode)
    points = np.array([(np.array(nodes[l['from']]) + nodes[l['to']]) / 2
                       for l in connected])
    distances = np.linalg.norm(points - port, axis=1)
    closest = int(distances.argmin())
    if distances[closest] > limit:
        raise ValueError(f'Port snap for {mode} is {distances[closest]:.1f} m, above {limit}')
    gates = []
    for axis in axes:
        coordinate = {'east': 0, 'north': 1}[axis]
        chosen = int(points[:, coordinate].argmax())
        gates.append(dict(link=connected[chosen]['id'], xy=points[chosen].tolist(), axis=axis))
    return dict(port=dict(link=connected[closest]['id'], xy=points[closest].tolist()),
                gates=gates, port_snap_m=float(distances[closest]),
                connected_links_count=len(connected))


def main():
    cfg = registry.load()
    base = Path(city.path('demand/baseline/plans_with_activities.xml.gz'))
    with gzip.open(base, 'rb') as stream:
        population = ET.parse(stream).getroot()
    residents = len(population.findall('person'))
    classified = [r for r in rows('data/processed/observed/tbtt_2018_reported_aggregates.csv')
                  if r['aggregate_kind'] == 'equal_mean_of_four_different_sites']
    counts = {r['class_as_printed']: float(r['reported_daily_count']) for r in classified}
    goods_ratio = sum(counts[c] for c in cfg.get('B.freight.goods_count_classes')) / counts[cfg.get('B.freight.reference_car_class')]
    truck_count = round(residents * cfg.get('B.freight.car_equivalent_movements_per_person_day') * goods_ratio)
    rakes = rows('data/processed/observed/jnpa_rake_observations.csv')
    handled = Counter(r['handled_date'] for r in rakes)
    mean_rakes = sum(handled.values()) / len(handled)
    rail_count = round(mean_rakes * cfg.get('B.freight.rake_movements_per_handled_rake'))
    points = pyogrio.read_dataframe(city.path('data/processed/geospatial/osm_research.gpkg'),
                                   layer='points', where='osm_id = ' + repr(cfg.get('B.freight.port_osm_node_id'))).to_crs(city.crs())
    if len(points) != 1:
        raise ValueError('The declared freight port must resolve to exactly one acquired point')
    port = np.array([points.geometry.iloc[0].x, points.geometry.iloc[0].y])
    network = Path(city.path('networks/matsim/schedules/baseline_regional/network.xml.gz'))
    with gzip.open(network, 'rb') as stream:
        root = ET.parse(stream).getroot()
    nodes = {n.get('id'): (float(n.get('x')), float(n.get('y'))) for n in root.findall('nodes/node')}
    links = [dict(l.attrib) for l in root.findall('links/link')]
    del root
    rng = np.random.default_rng(cfg.get('B.freight.seed'))
    records, anchors = [], {}
    start, end = cfg.get('B.freight.movement_window_s')
    for mode, source_mode, count in [('truck', 'car', truck_count), ('freight_rail', 'rail', rail_count)]:
        anchor = modal_anchors(links, nodes, source_mode, port,
                               cfg.get('B.freight.gate_axes'), cfg.get('B.freight.port_snap_limit_m'))
        anchors[mode] = anchor
        for index in range(count):
            gate = anchor['gates'][index % len(anchor['gates'])]
            outbound = (index // len(anchor['gates'])) % 2
            origin, destination = (anchor['port'], gate) if outbound else (gate, anchor['port'])
            departure = int(rng.uniform(start, end))
            identity = f'background_{mode}_{index}'
            person = ET.SubElement(population, 'person', id=identity)
            attributes = ET.SubElement(person, 'attributes')
            for key, value in [('subpopulation', subpopulations.FREIGHT), ('lockedMode', mode), ('permittedModes', mode)]:
                ET.SubElement(attributes, 'attribute', name=key, attrib={'class': 'java.lang.String'}).text = value
            plan = ET.SubElement(person, 'plan', selected='yes')
            ET.SubElement(plan, 'activity', type='freight_start', link=origin['link'],
                          x=str(origin['xy'][0]), y=str(origin['xy'][1]), end_time=str(departure))
            ET.SubElement(plan, 'leg', mode=mode)
            ET.SubElement(plan, 'activity', type='freight_end', link=destination['link'],
                          x=str(destination['xy'][0]), y=str(destination['xy'][1]))
            records.append(dict(person_id=identity, mode=mode, departure_s=departure,
                origin_link_id=origin['link'], destination_link_id=destination['link'],
                gate_axis=gate['axis'], source='modelled_provisional_background_from_historical_controls',
                od_status='port_locality_and_connected_research_network_extremities_not_observed_od'))
    target = Path(city.path('demand/baseline'))
    xml = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n' + ET.tostring(population, encoding='utf-8')
    with (target / 'plans_with_freight.xml.gz').open('wb') as stream:
        with gzip.GzipFile(fileobj=stream, filename='', mtime=0, mode='wb') as zipped:
            zipped.write(xml)
    with (target / 'freight_movements.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(records)
    report = dict(residents_count=residents, truck_movements_count=truck_count,
        freight_rail_movements_count=rail_count, goods_to_cars_historical_ratio=goods_ratio,
        handled_rakes_by_report_day=dict(handled), mean_handled_rakes=mean_rakes, anchors=anchors,
        input_sha256={p: fingerprint(Path(city.path(p))) for p in OUTPUT_INPUTS['demand/baseline/plans_with_freight.xml.gz']},
        limitations=['Not observed current regional freight demand or OD.',
                     'All port access and cordon endpoints are provisional network anchors.',
                     'No regional expansion, time bans, depot circulation or freight calibration.'])
    Path(city.path('data/processed/acquisition/baseline_freight.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('input_sha256', 'anchors')}, indent=2))


if __name__ == '__main__':
    main()
