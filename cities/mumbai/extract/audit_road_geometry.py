"""Verify native road geometry against attributes, access and the rail layer."""
from collections import Counter, defaultdict
import csv
import itertools
import json
import math
import os
from pathlib import Path
import tempfile

import city
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'data/processed/network/road_rail_shared_nodes.csv': [
        'data/processed/network/road_geometry/nodes.csv', 'data/processed/network/road_geometry/ways.csv',
        'data/processed/network/rail_geometry/nodes.csv', 'data/processed/network/rail_geometry/ways.csv'],
    'data/processed/acquisition/road_geometry_join_audit.json': [
        'data/processed/network/road_geometry/*', 'data/processed/network/rail_geometry/*',
        'data/processed/network/osm_way_attributes.csv', 'data/processed/network/osm_way_access_profiles.csv',
        'data/processed/network/osm_access_profiles.json',
        'data/processed/acquisition/road_attribute_evidence_audit.json',
        'data/processed/acquisition/raster_tile_selection.json'],
}


def rows(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        yield from csv.DictReader(stream)


def serial(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def main():
    base = Path(city.path('data/processed/network'))
    paths = [base / layer / name for layer in ('road_geometry', 'rail_geometry')
             for name in ('nodes.csv', 'ways.csv', 'segments.csv', 'audit.json')]
    paths += [base / name for name in ('osm_way_attributes.csv', 'osm_way_access_profiles.csv',
                                      'osm_access_profiles.json')]
    paths.append(Path(city.path('data/processed/acquisition/road_attribute_evidence_audit.json')))
    extent_path = Path(city.path('data/processed/acquisition/raster_tile_selection.json'))
    paths.append(extent_path)
    hashes = {city.rel(str(p)): fingerprint(p) for p in paths}
    road_audit = json.loads((base / 'road_geometry/audit.json').read_text(encoding='utf-8'))
    rail_audit = json.loads((base / 'rail_geometry/audit.json').read_text(encoding='utf-8'))
    attribute_audit = json.loads(Path(city.path('data/processed/acquisition/road_attribute_evidence_audit.json')).read_text(encoding='utf-8'))
    bounds = json.loads(extent_path.read_text(encoding='utf-8'))['extent_wgs84']
    if len(bounds) != 4 or not bounds[0] < bounds[2] or not bounds[1] < bounds[3]:
        raise ValueError('Invalid source-derived research envelope')
    if (road_audit['input_sha256'] != rail_audit['input_sha256'] or
            road_audit['input_sha256'] != [item['sha256'] for item in attribute_audit['inputs']] or
            road_audit['projected_crs'] != rail_audit['projected_crs']):
        raise ValueError('Geometry layers and road attributes must use the same native source and projection')
    road_ways = {}
    for row in rows(base / 'road_geometry/ways.csv'):
        identity = int(row['osm_way_id'])
        if identity in road_ways:
            raise ValueError('Duplicate road geometry way')
        row['refs'] = json.loads(row['ordered_node_ids_json'])
        if int(row['node_count']) != len(row['refs']) or int(row['segment_count']) != len(row['refs']) - 1:
            raise ValueError('Way reference/count mismatch')
        road_ways[identity] = row
    expected_attribute_ids = {identity for identity, r in road_ways.items()
                              if r['highway_tag'] and r['geometry_role'] == 'native_way_geometry'}
    attribute_ids = set()
    for row in rows(base / 'osm_way_attributes.csv'):
        identity = int(row['osm_way_id'])
        if identity in attribute_ids or identity not in expected_attribute_ids:
            raise ValueError('Duplicate or unexpected attribute way')
        attribute_ids.add(identity)
        geometry = road_ways[identity]
        if (json.loads(row['source_tags_json']) != json.loads(geometry['source_tags_json']) or
                row['highway'] != geometry['highway_tag']):
            raise ValueError('Geometry and road attribute tags disagree')
    if attribute_ids != expected_attribute_ids:
        raise ValueError('Road attributes miss native linear highway geometry')
    profiles = {r['access_profile_sha256']: r for r in json.loads(
        (base / 'osm_access_profiles.json').read_text(encoding='utf-8'))}
    access_ids, profile_counts = set(), Counter()
    for row in rows(base / 'osm_way_access_profiles.csv'):
        identity, profile = int(row['osm_way_id']), row['access_profile_sha256']
        if identity in access_ids or identity not in attribute_ids or profile not in profiles:
            raise ValueError('Duplicate or unjoinable access-profile assignment')
        access_ids.add(identity)
        profile_counts[profile] += 1
        tags = json.loads(road_ways[identity]['source_tags_json'])
        if any(tags.get(k) != v for k, v in profiles[profile]['source_tags'].items()):
            raise ValueError('Access profile is not an exact subset of native way tags')
    if access_ids != attribute_ids or any(profile_counts[p] != r['referenced_ways_count'] for p, r in profiles.items()):
        raise ValueError('Geometry/access counts do not reconcile')
    segment_ways, segment_count = set(), 0
    for identity, group in itertools.groupby(rows(base / 'road_geometry/segments.csv'), key=lambda r: int(r['osm_way_id'])):
        if identity in segment_ways or identity not in road_ways:
            raise ValueError('Noncontiguous, repeated or unrecognised segment way group')
        segment_ways.add(identity)
        way = road_ways[identity]
        projected, geodesic = [], []
        for index, row in enumerate(group):
            if (int(row['segment_index_zero_based']) != index or index >= len(way['refs']) - 1 or
                    [int(row['from_osm_node_id']), int(row['to_osm_node_id'])] != way['refs'][index:index + 2] or
                    row['geometry_role'] != way['geometry_role'] or row['highway_tag'] != way['highway_tag']):
                raise ValueError('Segment does not match the ordered native way')
            projected.append(float(row['length_projected_m']))
            geodesic.append(float(row['length_geodesic_m']))
            segment_count += 1
        if (len(projected) != int(way['segment_count']) or
                math.fsum(projected) != float(way['length_projected_m']) or
                math.fsum(geodesic) != float(way['length_geodesic_m'])):
            raise ValueError('Segment count or length totals differ from native way')
    if segment_ways != road_ways.keys() or segment_count != road_audit['segments']:
        raise ValueError('Incomplete segment geometry')
    rail_nodes = {int(r['osm_node_id']): r for r in rows(base / 'rail_geometry/nodes.csv')}
    shared = {}
    unshared_railway_tags = defaultdict(list)
    unshared_context = {}
    road_node_ids = set()
    for row in rows(base / 'road_geometry/nodes.csv'):
        identity = int(row['osm_node_id'])
        if identity in road_node_ids:
            raise ValueError('Duplicate road geometry node')
        road_node_ids.add(identity)
        if identity in rail_nodes:
            if row != rail_nodes[identity]:
                raise ValueError('Shared road/rail node coordinates, tags or provenance disagree')
            shared[identity] = row
        else:
            tags = json.loads(row['source_tags_json'])
            if 'railway' in tags:
                unshared_railway_tags[tags['railway']].append(identity)
                x, y = float(row['longitude_deg']), float(row['latitude_deg'])
                unshared_context[identity] = dict(railway_tag=tags['railway'],
                    within_research_envelope=bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3],
                    source_tags=tags, road_parent_way_ids=[])
    if len(road_node_ids) != road_audit['nodes'] or any(set(r['refs']) - road_node_ids for r in road_ways.values()):
        raise ValueError('Native road node references are incomplete')
    parents = {kind: defaultdict(list) for kind in ('road', 'rail')}
    for way in road_ways.values():
        for identity in set(way['refs']) & unshared_context.keys():
            unshared_context[identity]['road_parent_way_ids'].append(int(way['osm_way_id']))
    for kind, way_rows, tag in (('road', road_ways.values(), 'highway_tag'),
                                ('rail', rows(base / 'rail_geometry/ways.csv'), 'railway_tag')):
        for row in way_rows:
            refs = row['refs'] if kind == 'road' else json.loads(row['ordered_node_ids_json'])
            for identity in sorted(set(refs) & shared.keys()):
                parents[kind][identity].append(dict(osm_way_id=int(row['osm_way_id']),
                    feature_value=row[tag], geometry_role=row['geometry_role']))
    shared_rows = []
    shared_tags = Counter()
    for identity, row in sorted(shared.items()):
        tags = json.loads(row['source_tags_json'])
        shared_tags[tags.get('railway', 'not_tagged')] += 1
        shared_rows.append(dict(osm_node_id=identity, longitude_deg=row['longitude_deg'], latitude_deg=row['latitude_deg'],
            projected_x_m=row['projected_x_m'], projected_y_m=row['projected_y_m'], projected_crs=row['projected_crs'],
            source_tags_json=row['source_tags_json'], road_parent_ways_json=serial(sorted(parents['road'][identity], key=lambda r: r['osm_way_id'])),
            rail_parent_ways_json=serial(sorted(parents['rail'][identity], key=lambda r: r['osm_way_id'])),
            model_connection_status='native_shared_node_not_transfer_or_conflict_permission'))
    report = dict(source='derived_native_geometry_join', input_sha256=hashes,
        road_geometry_ways=len(road_ways), road_geometry_nodes=len(road_node_ids), road_geometry_segments=segment_count,
        road_attribute_ways_matched=len(attribute_ids), access_profile_ways_matched=len(access_ids),
        geometry_ways_outside_linear_attribute_scope=len(road_ways) - len(attribute_ids),
        native_road_rail_shared_nodes=len(shared), shared_nodes_by_railway_tag=dict(sorted(shared_tags.items())),
        road_nodes_with_railway_tag_not_in_rail_geometry={k: sorted(v) for k, v in sorted(unshared_railway_tags.items())},
        unshared_railway_node_context={str(k): v for k, v in sorted(unshared_context.items())},
        model_connections_created=0, limitations=[
            'Native shared identity is geometry evidence only. A road/rail crossing is not a passenger transfer or permission to enter track.',
            'Parent lists include area and non-operating features with their source classes; they must not be treated uniformly as active links.',
            'Geometrically intersecting ways without a common native node are not connected or snapped by this audit.',
            'No signal phase, level-crossing operation, barrier passability, speed, capacity or mode permission is inferred.',
            'The research envelope check explains whole-way overcoverage; it is not a legal study boundary or a model exclusion rule.',
        ])
    if hashes != {city.rel(str(p)): fingerprint(p) for p in paths}:
        raise ValueError('Geometry inputs changed during join audit')
    with tempfile.TemporaryDirectory(prefix='geometry-join-', dir=base) as temporary:
        stage = Path(temporary)
        fields = ['osm_node_id', 'longitude_deg', 'latitude_deg', 'projected_x_m', 'projected_y_m', 'projected_crs',
                  'source_tags_json', 'road_parent_ways_json', 'rail_parent_ways_json', 'model_connection_status']
        with (stage / 'road_rail_shared_nodes.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(shared_rows)
        (stage / 'road_geometry_join_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
        for relative in OUTPUT_INPUTS:
            target = Path(city.path(relative))
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / target.name, target)
    print(json.dumps({k: v for k, v in report.items() if k != 'input_sha256'}), flush=True)


if __name__ == '__main__':
    main()
