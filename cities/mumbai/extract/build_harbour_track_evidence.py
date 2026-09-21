"""Join explicit stop-area roles to native rail nodes and test topology only.

No nearest-track snapping, platform allocation, direction default, speed or
capacity is introduced. Undirected connectedness is a necessary check and does
not certify an operable train path through switches, signals and platforms.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path

import city
from build.extract_osm_network import entities, fingerprint
from match_harbour_station_geometry import mode_status
from evidence_io import dump_rows, read_rows, serial

OUTPUT_INPUTS = {
    'data/processed/transit/cr_harbour_stop_area_members.csv': [
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/transit/cr_harbour_geometry_candidates.csv', 'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv', 'data/processed/geospatial/osm_transport_areas.geojson'],
    'data/processed/network/cr_harbour_boarding_nodes.csv': [
        'networks/osm/network_source.osm.gz', 'data/processed/acquisition/osm_network_source_audit.json',
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/transit/cr_harbour_geometry_candidates.csv', 'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson'],
    'data/processed/network/cr_harbour_track_memberships.csv': [
        'networks/osm/network_source.osm.gz', 'data/processed/acquisition/osm_network_source_audit.json',
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/transit/cr_harbour_geometry_candidates.csv', 'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson'],
    'data/processed/network/cr_harbour_adjacent_station_topology.csv': [
        'networks/osm/network_source.osm.gz', 'data/processed/acquisition/osm_network_source_audit.json',
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/transit/cr_harbour_geometry_candidates.csv', 'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv', 'data/processed/geospatial/osm_transport_areas.geojson'],
    'data/processed/acquisition/cr_harbour_track_evidence_audit.json': [
        'networks/osm/network_source.osm.gz', 'data/processed/acquisition/osm_network_source_audit.json',
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/transit/cr_harbour_geometry_candidates.csv', 'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv', 'data/processed/geospatial/osm_transport_areas.geojson'],
}


def main():
    geometry = read_rows('data/processed/transit/cr_harbour_geometry_candidates.csv')
    anchors, boarding = defaultdict(set), defaultdict(lambda: defaultdict(list))
    for row in geometry:
        if row['retain_for_identity_review'] != 'True':
            continue
        key, feature = row['station_key'], row['osm_feature_id']
        anchors[feature].add(key)
        if row['evidence_feature_kind'] == 'stop' and feature.startswith('node/'):
            boarding[feature.split('/')[1]][key].append(dict(basis='direct_geometry_candidate', feature=feature,
                                                            identity_match_evidence=json.loads(row['match_evidence'])))
    direct_nodes = set(boarding)
    point_rows = {r['osm_node_id']: r for r in read_rows('data/processed/observed/osm_transport_points.csv')}
    tags_by_feature = {'node/'+key: json.loads(row['all_driver_tags_json']) for key, row in point_rows.items()}
    for f in json.loads(Path(city.path('data/processed/geospatial/osm_transport_areas.geojson')).read_text(encoding='utf-8'))['features']:
        tags_by_feature[f['id']] = f['properties']['all_driver_tags']
    members_out, relations_used, excluded_relations = [], set(), set()
    excluded_nonrail_members = set()
    for relation in read_rows('data/processed/observed/osm_transport_relations.csv'):
        if relation['public_transport_tag'] != 'stop_area':
            continue
        members = json.loads(relation['ordered_members_json'])
        anchor_features = sorted({m['type']+'/'+m['ref'] for m in members} & anchors.keys())
        if not anchor_features:
            continue
        keys = sorted(set().union(*(anchors[f] for f in anchor_features)))
        relation_tags = json.loads(relation['all_tags_json'])
        mixed_or_other_mode = mode_status(relation_tags).startswith('excluded_') or any(
            mode_status(tags_by_feature.get(m['type']+'/'+m['ref'], {})).startswith('excluded_') for m in members)
        identity = relation['osm_relation_id']
        relations_used.add(identity)
        if mixed_or_other_mode:
            excluded_relations.add(identity)
        for index, member in enumerate(members, 1):
            feature = member['type']+'/'+member['ref']
            tags = tags_by_feature.get(feature, {})
            stop_role = member['role'] in ('stop', 'stop_entry_only', 'stop_exit_only')
            stop_tag = tags.get('railway') == 'stop' or (tags.get('public_transport') == 'stop_position' and tags.get('train') == 'yes')
            nonrail = tags.get('bus') == 'yes' or tags.get('highway') == 'bus_stop' or tags.get('ferry') == 'yes' or tags.get('amenity') == 'ferry_terminal'
            if member['type'] == 'node' and (stop_role or stop_tag) and nonrail:
                excluded_nonrail_members.add(feature)
            candidate = member['type'] == 'node' and (stop_role or stop_tag) and not mixed_or_other_mode and not nonrail
            for key in keys:
                members_out.append(dict(source='derived_explicit_relation_membership', station_key=key,
                                        osm_relation_id=identity, relation_name=relation['name'],
                                        relation_anchor_features=serial(anchor_features), member_order=index,
                                        member_feature_id=feature, member_role=member['role'],
                                        geometry_inventory_status='available' if feature in tags_by_feature else 'not_in_current_inventory',
                                        member_tags_json=serial(tags), candidate_boarding_node=candidate,
                                        member_mode_status='excluded_explicit_nonrail' if nonrail else 'requires_native_rail_membership_check',
                                        relation_mode_status='excluded_other_or_mixed_rail_mode' if mixed_or_other_mode else 'requires_native_rail_membership_check'))
                if candidate:
                    boarding[member['ref']][key].append(dict(basis='explicit_stop_area_member', relation=identity,
                                                           member_order=index, role=member['role'],
                                                           stop_role=stop_role, stop_tag=stop_tag))

    native = Path(city.path('networks/osm/network_source.osm.gz'))
    network_audit = json.loads(Path(city.path('data/processed/acquisition/osm_network_source_audit.json')).read_text(encoding='utf-8'))
    relation_audit = json.loads(Path(city.path('data/processed/acquisition/osm_transport_relations_audit.json')).read_text(encoding='utf-8'))
    native_hash = fingerprint(native)
    if native_hash != network_audit['output_sha256'] or network_audit['source_sha256'] != relation_audit['source_native_sha256']:
        raise ValueError('Relation and reduced network evidence must use the same full native build')
    wanted, found, memberships, rail_parents = set(boarding), {}, [], defaultdict(set)
    parent = {}

    def component(node):
        parent.setdefault(node, node)
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            following = parent[node]
            parent[node] = root
            node = following
        return root

    rail_way_count = 0
    print('SCANNING native stop-node membership and undirected rail components', flush=True)
    for element in entities(native):
        identity = element.get('id')
        if element.tag == 'node' and identity in wanted:
            if identity in found:
                raise ValueError('Duplicate boarding node in native source')
            found[identity] = dict(latitude_deg=float(element.get('lat')), longitude_deg=float(element.get('lon')),
                                   tags={t.get('k'): t.get('v', '') for t in element.findall('tag')})
        elif element.tag == 'way':
            refs = [n.get('ref') for n in element.findall('nd')]
            hits = wanted.intersection(refs)
            railway_element = element.find("tag[@k='railway']")
            railway = railway_element.get('v') if railway_element is not None else ''
            if railway == 'rail':
                rail_way_count += 1
                for a, b in zip(refs, refs[1:]):
                    ra, rb = component(a), component(b)
                    if ra != rb:
                        small, large = sorted((ra, rb))
                        parent[large] = small
            if not hits:
                continue
            tags = {t.get('k'): t.get('v', '') for t in element.findall('tag')}
            for index, node in enumerate(refs):
                if node not in hits:
                    continue
                memberships.append(dict(source='native_osm_way_node_membership', osm_node_id=node,
                                        station_keys=serial(sorted(boarding[node])), osm_way_id=identity,
                                        way_node_index_zero_based=index, previous_node_id=refs[index-1] if index else '',
                                        next_node_id=refs[index+1] if index+1 < len(refs) else '',
                                        railway_tag=railway, oneway_as_tag=tags.get('oneway', ''),
                                        gauge_as_tag=tags.get('gauge', ''), all_way_tags_json=serial(tags),
                                        source_native_sha256=native_hash, allocation_status='track_membership_only_no_service_platform_assignment'))
                if railway == 'rail':
                    rail_parents[node].add(identity)
    memberships.sort(key=lambda r: (int(r['osm_node_id']), int(r['osm_way_id']), r['way_node_index_zero_based']))
    nodes_out, coordinate_deltas = [], []
    for node in sorted(wanted, key=int):
        item = found.get(node)
        if item is not None and node in point_rows:
            coordinate_deltas.append(max(abs(item[k]-float(point_rows[node][k])) for k in ('longitude_deg', 'latitude_deg')))
        nodes_out.append(dict(source='derived_native_boarding_candidate', osm_node_id=node,
                              station_keys=serial(sorted(boarding[node])), evidence_references=serial(boarding[node]),
                              latitude_deg=item['latitude_deg'] if item else '', longitude_deg=item['longitude_deg'] if item else '',
                              native_node_tags_json=serial(item['tags']) if item else '',
                              native_presence='present' if item else 'missing', rail_parent_ways=serial(sorted(rail_parents[node], key=int)),
                              undirected_rail_component=component(node) if rail_parents[node] else '',
                              source_native_sha256=native_hash,
                              assignment_status=('candidate_only_direction_and_platform_allocation_unresolved' if item and rail_parents[node]
                                                 else 'rejected_missing_native_node_or_rail_parent')))
    station_nodes, station_components = defaultdict(set), defaultdict(set)
    for node, keys in boarding.items():
        if not rail_parents[node]:
            continue
        for key in keys:
            station_nodes[key].add(node)
            station_components[key].add(component(node))
    trains = defaultdict(list)
    for stop in read_rows('data/processed/transit/cr_harbour_stop_candidates.csv'):
        trains[stop['train_number']].append(stop)
    pair_trains = defaultdict(set)
    for train, stops in trains.items():
        stops.sort(key=lambda r: int(r['stop_sequence']))
        for a, b in zip(stops, stops[1:]):
            pair_trains[(a['station_key'], b['station_key'])].add(train)
    pairs = []
    for (a, b), services in sorted(pair_trains.items()):
        shared = station_components[a] & station_components[b]
        status = ('boarding_identity_unresolved' if not station_nodes[a] or not station_nodes[b] else
                  'potentially_connected_undirected' if shared else 'disconnected_in_mapped_rail_graph')
        pairs.append(dict(from_station_key=a, to_station_key=b, timetable_service_count=len(services),
                          from_native_boarding_nodes=serial(sorted(station_nodes[a], key=int)),
                          to_native_boarding_nodes=serial(sorted(station_nodes[b], key=int)),
                          shared_undirected_components=serial(sorted(shared, key=int)), status=status,
                          validation_scope='necessary_topology_check_only_no_direction_length_signalling_or_route_validation'))
    if fingerprint(native) != native_hash:
        raise ValueError('Native source changed during track audit')
    dump_rows('data/processed/transit/cr_harbour_stop_area_members.csv', members_out)
    dump_rows('data/processed/network/cr_harbour_boarding_nodes.csv', nodes_out)
    dump_rows('data/processed/network/cr_harbour_track_memberships.csv', memberships)
    dump_rows('data/processed/network/cr_harbour_adjacent_station_topology.csv', pairs)
    audit = dict(source_native_sha256=native_hash, stop_area_relations_used=len(relations_used),
                 excluded_mixed_or_other_mode_relations=sorted(excluded_relations, key=int),
                 excluded_explicit_nonrail_member_features=sorted(excluded_nonrail_members),
                 member_association_rows=len(members_out), direct_boarding_nodes=len(direct_nodes),
                 relation_added_boarding_nodes=len(wanted-direct_nodes), total_boarding_nodes=len(wanted),
                 missing_native_node_ids=sorted(wanted-found.keys(), key=int),
                 nodes_without_rail_parent=sorted((node for node in wanted if not rail_parents[node]), key=int),
                 native_track_membership_rows=len(memberships), railway_rail_ways=rail_way_count,
                 station_keys_with_native_boarding_nodes=sum(bool(nodes) for nodes in station_nodes.values()),
                 adjacent_station_pairs=len(pairs), pair_status_counts=dict(sorted(Counter(p['status'] for p in pairs).items())),
                 largest_point_inventory_coordinate_difference_deg=max(coordinate_deltas, default=None),
                 limitations=[
                     'Native reference membership preserves rail levels and shared junction identity without coordinate snapping.',
                     'Stop-area groups are not expanded; an interchange group must not merge metro, monorail and suburban boarding nodes.',
                     'A stop-area may contain long-distance and suburban platforms; train-specific allocation remains unknown.',
                     'Native railway=rail connectedness is undirected and includes sidings; it proves neither an operable route nor a realistic path length.',
                     'Oneway, gauge and other source tags are preserved but not converted into a train-control or capacity model.',
                     'Switch states, signal/block conflicts, service direction, dwell, accessibility and current operational status still need validation.',
                 ])
    Path(city.path('data/processed/acquisition/cr_harbour_track_evidence_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: value for key, value in audit.items() if key != 'limitations'}))


if __name__ == '__main__':
    main()
