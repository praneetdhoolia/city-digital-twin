"""Compare timetable patterns with ordered native passenger-route evidence.

No relation member is reordered or replaced. A matched OSM route window is
evidence of a mapped path, not proof of current operation or train assignment.
"""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import city
from build.ordered_route_geometry import locate_ordered_stops, orient_ordered_ways
from build.rail_path_candidates import orientations
from manifest_io import manifest_reader

OUTPUT_INPUTS = {
    'data/processed/transit/cr_harbour_mapped_routes.csv': [
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/acquisition/osm_network_source_audit.json', 'data/processed/network/rail_geometry/audit.json',
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/cr_harbour_boarding_nodes.csv', 'data/processed/transit/cr_harbour_path_patterns.csv',
        'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/network/cr_harbour_mapped_route_segments.csv': [
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/acquisition/osm_network_source_audit.json', 'data/processed/network/rail_geometry/audit.json',
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/cr_harbour_boarding_nodes.csv', 'data/processed/transit/cr_harbour_path_patterns.csv',
        'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/transit/cr_harbour_mapped_route_stops.csv': [
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/acquisition/osm_network_source_audit.json', 'data/processed/network/rail_geometry/audit.json',
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/cr_harbour_boarding_nodes.csv', 'data/processed/transit/cr_harbour_path_patterns.csv',
        'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/transit/cr_harbour_pattern_route_evidence.csv': [
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/acquisition/osm_network_source_audit.json', 'data/processed/network/rail_geometry/audit.json',
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/cr_harbour_boarding_nodes.csv', 'data/processed/transit/cr_harbour_path_patterns.csv',
        'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/acquisition/cr_harbour_mapped_routes_audit.json': [
        'data/processed/observed/osm_transport_relations.csv', 'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/acquisition/osm_network_source_audit.json', 'data/processed/network/rail_geometry/audit.json',
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/cr_harbour_boarding_nodes.csv', 'data/processed/transit/cr_harbour_path_patterns.csv',
        'data/processed/transit/cr_harbour_service_path_candidates.csv'],
}


def read(path):
    with Path(city.path(path)).open(encoding='utf-8') as stream:
        return list(manifest_reader(stream))


def serial(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def dump(path, rows):
    if not rows:
        raise ValueError('No mapped-route evidence: ' + path)
    with Path(city.path(path)).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    inputs = sorted(set(p for paths in OUTPUT_INPUTS.values() for p in paths))
    hashes = {p: hashlib.sha256(Path(city.path(p)).read_bytes()).hexdigest() for p in inputs}
    audit = lambda p: json.loads(Path(city.path(p)).read_text(encoding='utf-8'))
    relation_audit = audit('data/processed/acquisition/osm_transport_relations_audit.json')
    network_audit = audit('data/processed/acquisition/osm_network_source_audit.json')
    geometry_audit = audit('data/processed/network/rail_geometry/audit.json')
    if (relation_audit['source_native_sha256'] != network_audit['source_sha256'] or
            geometry_audit['input_sha256'] != [network_audit['output_sha256']]):
        raise ValueError('Relation and reduced railway geometry builds do not share native ancestry')
    boarding = {int(r['osm_node_id']): r for r in read('data/processed/network/cr_harbour_boarding_nodes.csv')}
    if any(r['source_native_sha256'] != network_audit['output_sha256'] for r in boarding.values()):
        raise ValueError('Boarding evidence belongs to a different native build')
    keys = {node: set(json.loads(r['station_keys'])) for node, r in boarding.items()}
    ways = {int(r['osm_way_id']): r for r in read('data/processed/network/rail_geometry/ways.csv')
            if r['railway_tag'] == 'rail' and r['geometry_role'] != 'area_boundary'}
    segments = {(int(r['osm_way_id']), int(r['segment_index_zero_based'])): r
                for r in read('data/processed/network/rail_geometry/segments.csv')}
    route_rows, segment_rows, stop_rows, routes = [], [], [], {}
    for relation in read('data/processed/observed/osm_transport_relations.csv'):
        tags = json.loads(relation['all_tags_json'])
        if tags.get('route') != 'train' or tags.get('public_transport:version') != '2':
            continue
        members = [dict(member_order=i, **m) for i, m in enumerate(json.loads(relation['ordered_members_json']), 1)]
        stops = [m for m in members if m['type'] == 'node' and m['role'] in ('stop', 'stop_entry_only', 'stop_exit_only')]
        # Two identified stops are the minimum for a source-corridor comparison.
        if sum(int(m['ref']) in keys for m in stops) < 2:
            continue
        if relation['source_native_sha256'] != relation_audit['source_native_sha256']:
            raise ValueError('Stale relation row source identity')
        platform_roles = ('platform', 'platform_entry_only', 'platform_exit_only')
        tracks = [m for m in members if m['type'] == 'way' and m['role'] not in platform_roles]
        missing = [m for m in tracks if int(m['ref']) not in ways]
        unsupported = [m for m in members if (m['type'] == 'relation' and m['role'] not in platform_roles) or
                       (m['type'] == 'way' and m['role'] and m['role'] not in platform_roles) or
                       (m['type'] == 'node' and m['role'] not in ('stop', 'stop_entry_only', 'stop_exit_only',
                                                                   'platform', 'platform_entry_only', 'platform_exit_only'))]
        chain = (dict(status='missing_or_nonrail_way_members', nodes=(), orientations=(), orientation_count=0)
                 if missing else dict(status='unsupported_relation_member_roles', nodes=(), orientations=(), orientation_count=0)
                 if unsupported else orient_ordered_ways([json.loads(ways[int(m['ref'])]['ordered_node_ids_json']) for m in tracks]))
        route_id = relation['osm_relation_id']
        traced = []
        for member, forward in zip(tracks, chain['orientations']):
            way_id = int(member['ref'])
            way = ways[way_id]
            way_tags = json.loads(way['source_tags_json'])
            indexes = list(range(int(way['segment_count'])))
            if not forward:
                indexes.reverse()
            for index in indexes:
                segment = segments[(way_id, index)]
                a, b = int(segment['from_osm_node_id']), int(segment['to_osm_node_id'])
                if not forward:
                    a, b = b, a
                preferred = way_tags.get('railway:preferred_direction', '')
                traced.append(dict(osm_route_relation_id=route_id, route_segment_index_zero_based=len(traced),
                    source_member_order=member['member_order'], osm_way_id=way_id, native_segment_index_zero_based=index,
                    from_osm_node_id=a, to_osm_node_id=b, traversal_relative_to_native_order='forward' if forward else 'backward',
                    length_geodesic_m=float(segment['length_geodesic_m']),
                    direction_status=dict(orientations(way_tags, screen_static_oneway=False))[forward],
                    against_preferred_direction=(preferred == 'forward' and not forward) or (preferred == 'backward' and forward),
                    source_way_tags_json=serial(way_tags)))
        if traced and tuple([traced[0]['from_osm_node_id']] + [r['to_osm_node_id'] for r in traced]) != chain['nodes']:
            raise ValueError('Ordered segment trace differs from native way chain')
        locations = (locate_ordered_stops(chain['nodes'], [int(m['ref']) for m in stops]) if chain['nodes'] else
                     [dict(node_id=int(m['ref']), node_index=None, status='route_geometry_unresolved') for m in stops])
        for i, (member, location) in enumerate(zip(stops, locations), 1):
            stop_rows.append(dict(osm_route_relation_id=route_id, route_stop_sequence=i,
                source_member_order=member['member_order'], source_member_role=member['role'],
                osm_node_id=member['ref'], station_keys_json=serial(sorted(keys.get(int(member['ref']), set()))),
                native_node_tags_json=boarding.get(int(member['ref']), {}).get('native_node_tags_json', '{}'),
                route_node_index_zero_based=location['node_index'], chain_status=location['status']))
        stop_counts = Counter(r['status'] for r in locations)
        route_rows.append(dict(source='derived_native_mapped_route_evidence', osm_route_relation_id=route_id,
            source_native_sha256=relation['source_native_sha256'], source_reduced_sha256=network_audit['output_sha256'],
            name=relation['name'], route_source_tags_json=serial(tags), stop_members=len(stops),
            identified_stop_members=sum(int(m['ref']) in keys for m in stops), way_members=len(tracks),
            missing_or_nonrail_members_json=serial(missing), unsupported_members_json=serial(unsupported),
            geometry_status=chain['status'], orientation_count=chain['orientation_count'],
            first_disconnected_way_index=chain.get('first_disconnected_way_index', ''),
            segment_traversals=len(traced), length_geodesic_m=sum(r['length_geodesic_m'] for r in traced),
            stop_status_counts_json=serial(dict(sorted(stop_counts.items()))),
            direction_status_counts_json=serial(dict(sorted(Counter(r['direction_status'] for r in traced).items()))),
            coherent_stop_geometry=bool(traced) and set(stop_counts) == {'present_in_order'}, schedule_export_eligible=False))
        routes[route_id] = dict(stops=stops, locations=locations, segments=traced)
        segment_rows.extend(traced)
    patterns = [r for r in read('data/processed/transit/cr_harbour_path_patterns.csv') if r['variant'] == 'static_oneway_screen']
    services = Counter(r['pattern_id'] for r in read('data/processed/transit/cr_harbour_service_path_candidates.csv')
                       if r['variant'] == 'static_oneway_screen')
    pattern_rows = []
    for pattern in patterns:
        station_keys = json.loads(pattern['station_keys_json'])
        shortest_boarding = json.loads(pattern['boarding_node_ids_json'])
        for route_id, route in routes.items():
            stops, locations = route['stops'], route['locations']
            for start in range(len(stops) - len(station_keys) + 1):
                window = stops[start:start + len(station_keys)]
                if station_keys[0] not in keys.get(int(window[0]['ref']), set()) or station_keys[-1] not in keys.get(int(window[-1]['ref']), set()):
                    continue
                conflicts = [dict(pattern_stop_sequence=i + 1, timetable_station_key=key,
                                  route_stop_node_id=m['ref'], mapped_station_keys=sorted(keys.get(int(m['ref']), set())))
                             for i, (key, m) in enumerate(zip(station_keys, window)) if key not in keys.get(int(m['ref']), set())]
                positions = locations[start:start + len(station_keys)]
                coherent = all(p['status'] == 'present_in_order' for p in positions)
                trace = route['segments'][positions[0]['node_index']:positions[-1]['node_index']] if coherent else []
                status = ('station_order_conflict' if conflicts else 'stop_geometry_unresolved' if not coherent else
                          'contiguous_mapped_route_geometry_evidence')
                pattern_rows.append(dict(pattern_id=pattern['pattern_id'], timetable_services=services[pattern['pattern_id']],
                    osm_route_relation_id=route_id, route_start_stop_sequence=start + 1, route_end_stop_sequence=start + len(window),
                    station_keys_json=serial(station_keys), station_order_conflicts_json=serial(conflicts),
                    mapped_stop_node_ids_json=serial([int(m['ref']) for m in window]),
                    mapped_stop_chain_status_json=serial(positions), status=status,
                    route_start_node_index_zero_based=positions[0]['node_index'] if coherent else '',
                    route_end_node_index_zero_based=positions[-1]['node_index'] if coherent else '',
                    length_geodesic_m=sum(r['length_geodesic_m'] for r in trace) if coherent else '',
                    segment_traversals=len(trace) if coherent else '',
                    direction_status_counts_json=serial(dict(sorted(Counter(r['direction_status'] for r in trace).items()))),
                    shortest_candidate_boarding_differences=sum(int(m['ref']) != node for m, node in zip(window, shortest_boarding)),
                    schedule_export_eligible=False))
    matched = {r['pattern_id'] for r in pattern_rows if r['status'] == 'contiguous_mapped_route_geometry_evidence'}
    for p in inputs:
        if hashlib.sha256(Path(city.path(p)).read_bytes()).hexdigest() != hashes[p]:
            raise ValueError('Input changed during mapped-route extraction: ' + p)
    report = dict(source='derived_mapped_route_and_timetable_evidence', input_sha256=hashes,
        selected_relations=len(route_rows), selection='PTv2 train routes with at least two identified timetable boarding stops',
        route_geometry_status_counts=dict(sorted(Counter(r['geometry_status'] for r in route_rows).items())),
        coherent_complete_route_stop_geometry=sum(r['coherent_stop_geometry'] for r in route_rows),
        route_stop_rows=len(stop_rows), route_segment_rows=len(segment_rows), pattern_route_rows=len(pattern_rows),
        pattern_route_status_counts=dict(sorted(Counter(r['status'] for r in pattern_rows).items())),
        timetable_patterns=len(patterns), patterns_with_contiguous_mapped_geometry=len(matched),
        services_with_contiguous_mapped_geometry=sum(services[p] for p in matched),
        patterns_without_contiguous_mapped_geometry=sorted(p['pattern_id'] for p in patterns if p['pattern_id'] not in matched),
        limitations=[
            'OSM route members are mapped evidence, not independently verified current service or train-specific platform assignments.',
            'Member order, repeated ways and native node identity remain intact; no stop substitutions or gap repairs are made.',
            'Only contiguous equal-length stop windows are compared; skipped-stop, composite, reversal and external branches require separate evidence.',
            'Route and static direction tags can conflict; unknown permissions, gauge, switches, signals, calendars and fleet assignment remain unresolved.',
            'Several route relations and repeated services share the same sources; they are not independent observations.',
            'No service is eligible for schedule export from these evidence tables.',
        ])
    dump('data/processed/transit/cr_harbour_mapped_routes.csv', route_rows)
    dump('data/processed/network/cr_harbour_mapped_route_segments.csv', segment_rows)
    dump('data/processed/transit/cr_harbour_mapped_route_stops.csv', stop_rows)
    dump('data/processed/transit/cr_harbour_pattern_route_evidence.csv', pattern_rows)
    Path(city.path('data/processed/acquisition/cr_harbour_mapped_routes_audit.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'input_sha256'}))


if __name__ == '__main__':
    main()
