"""Retain native corridor candidates and adjoining ways for spatial rule review.

No network permissions, speeds or opening dates are assigned by this audit.
Shared node references describe topology, not legal or directed connectivity.
"""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

import city
import harvest
from build.extract_osm_network import entities, fingerprint
from register_traffic_notices import notices

OUTPUT_INPUTS = {
    'data/processed/geospatial/coastal_access_candidates.geojson': [
        'networks/osm/network_source.osm.gz', 'geometry/coastal_road_review.json',
        'extract/transcriptions/coastal_road_order_187_20260825.json',
        'data/processed/observed/traffic_notice_index.csv',
        'data/raw/roads/mtp_traffic_notices_*.zip'],
    'data/processed/acquisition/coastal_access_audit.json': [
        'networks/osm/network_source.osm.gz', 'geometry/coastal_road_review.json',
        'extract/transcriptions/coastal_road_order_187_20260825.json',
        'data/processed/observed/traffic_notice_index.csv',
        'data/raw/roads/mtp_traffic_notices_*.zip'],
}


def tags_of(element):
    return {tag.get('k'): tag.get('v', '') for tag in element.findall('tag')}


def components(ways):
    """Stable undirected components keyed by the smallest native way ID."""
    node_ways = defaultdict(set)
    for identity, way in ways.items():
        for node in way['node_refs']:
            node_ways[node].add(identity)
    remaining = set(ways)
    result = {}
    while remaining:
        anchor = min(remaining)
        pending = [anchor]
        remaining.remove(anchor)
        while pending:
            current = pending.pop()
            result[current] = anchor
            neighbours = set().union(*(node_ways[node] for node in ways[current]['node_refs']))
            added = neighbours & remaining
            remaining.difference_update(added)
            pending.extend(sorted(added, reverse=True))
    return result


def main():
    network = Path(city.path('networks/osm/network_source.osm.gz'))
    selection_path = Path(city.path('geometry/coastal_road_review.json'))
    selection = json.loads(selection_path.read_text(encoding='utf-8'))
    order_path = Path(city.path(selection['source_order']))
    order = json.loads(order_path.read_text(encoding='utf-8'))
    # the notice's index (and so its harvest) is what the registered listing says it is
    with Path(city.path('data/processed/observed/traffic_notice_index.csv')).open(encoding='utf-8', newline='') as stream:
        listed = {row['source_id']: row['index_source_id'] for row in csv.DictReader(stream)}
    which, _, _ = notices(listed[order['source_id']])
    record, _ = harvest.source(which.id, which.category, order['source_id'])
    if record['sha256'] != order['source_sha256']:
        raise ValueError('Transcribed order source mismatch')
    inputs = [network, selection_path, order_path]
    before = {str(path.relative_to(Path(city.path()))).replace('\\', '/'): fingerprint(path)
              for path in inputs}
    candidates = {}
    seed_nodes = set()
    for element in entities(network):
        if element.tag != 'way':
            continue
        tags = tags_of(element)
        name = tags.get('name', '')
        if 'highway' not in tags or tags.get('area') == 'yes':
            continue
        if not any(fragment.casefold() in name.casefold() for fragment in selection['name_search_fragments']):
            continue
        identity = int(element.get('id'))
        if identity in candidates:
            raise ValueError('Duplicate candidate way')
        refs = [int(node.get('ref')) for node in element.findall('nd')]
        if len(refs) < 2:
            raise ValueError('Candidate has no linear geometry')
        status = ('corridor_name_candidate' if name in selection['corridor_name_candidates'] else
                  'approach_name_candidate' if name in selection['approach_name_candidates'] else
                  'search_only_name_match')
        candidates[identity] = dict(osm_way_id=identity, selection_status=status,
                                    node_refs=refs, osm_tags=tags)
        if status == 'corridor_name_candidate':
            seed_nodes.update(refs)
    if not seed_nodes:
        raise ValueError('No corridor candidates')
    required_nodes = {node for way in candidates.values() for node in way['node_refs']}
    coordinates, tagged_nodes, adjacent = {}, [], []
    for element in entities(network):
        identity = int(element.get('id'))
        if element.tag == 'node' and identity in required_nodes:
            if identity in coordinates:
                raise ValueError('Duplicate candidate geometry node')
            coordinates[identity] = [float(element.get('lon')), float(element.get('lat'))]
            tags = tags_of(element)
            if identity in seed_nodes and tags:
                tagged_nodes.append(dict(osm_node_id=identity, osm_tags=tags,
                                         coordinates_lon_lat=coordinates[identity]))
        elif element.tag == 'way' and identity not in candidates:
            tags = tags_of(element)
            if 'highway' not in tags or tags.get('area') == 'yes':
                continue
            refs = [int(node.get('ref')) for node in element.findall('nd')]
            shared = sorted(set(refs) & seed_nodes)
            if shared:
                adjacent.append(dict(osm_way_id=identity, shared_corridor_node_ids=shared,
                                     node_refs=refs, osm_tags=tags,
                                     selection_status='adjacent_topology_only'))
    if required_nodes != coordinates.keys():
        raise ValueError('Candidate geometry has absent native nodes')
    component_ids = components(candidates)
    features = []
    for identity, way in sorted(candidates.items()):
        properties = dict(way, topology_component_min_way_id=component_ids[identity],
                          source='derived', model_assignment_status='unassigned_extent_and_current_rules_pending')
        features.append(dict(type='Feature', id=str(identity), properties=properties,
                             geometry=dict(type='LineString', coordinates=[coordinates[n] for n in way['node_refs']])))
    after = {str(path.relative_to(Path(city.path()))).replace('\\', '/'): fingerprint(path)
             for path in inputs}
    if before != after:
        raise ValueError('Input changed during audit')
    audit = dict(source='derived', source_sha256=before, notification_source_sha256=record['sha256'],
                 notification_number=order['notification_number'], notification_scope=order['scope'],
                 classification_counts=dict(sorted(Counter(w['selection_status'] for w in candidates.values()).items())),
                 name_counts=dict(sorted(Counter(w['osm_tags']['name'] for w in candidates.values()).items())),
                 candidate_way_count=len(candidates), candidate_node_count=len(coordinates),
                 topology_component_count=len(set(component_ids.values())),
                 adjacent_way_count=len(adjacent),
                 adjacent_ways=sorted(adjacent, key=lambda row: row['osm_way_id']),
                 tagged_corridor_nodes=sorted(tagged_nodes, key=lambda row: row['osm_node_id']),
                 limitations=selection['notes'], model_permissions_assigned=False,
                 crs='OGC:CRS84; GeoJSON longitude, latitude in degrees')
    values = [dict(type='FeatureCollection', features=features), audit]
    for name, value in zip(OUTPUT_INPUTS, values):
        path = Path(city.path(name))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('classification_counts', 'candidate_way_count',
                                                'candidate_node_count', 'topology_component_count',
                                                'adjacent_way_count')}))


if __name__ == '__main__':
    main()
