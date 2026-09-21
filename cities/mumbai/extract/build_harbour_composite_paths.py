"""Derive two-chain candidates through an identical native boarding point.

Equivalent joins retain their provenance but count as one physical path. No
platform transfer, coordinate snapping or inferred train permission is allowed.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

import city
from build.ordered_route_geometry import shared_boarding_joins
from build_harbour_constrained_paths import digest, dump, read, serial

OUTPUT_INPUTS = {
    'data/processed/transit/cr_harbour_composite_join_candidates.csv': [
        'data/processed/acquisition/cr_harbour_constrained_paths_audit.json',
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_constrained_service_candidates.csv'],
    'data/processed/transit/cr_harbour_composite_path_candidates.csv': [
        'data/processed/acquisition/cr_harbour_constrained_paths_audit.json',
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_constrained_service_candidates.csv'],
    'data/processed/network/cr_harbour_composite_path_segments.csv': [
        'data/processed/acquisition/cr_harbour_constrained_paths_audit.json',
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_constrained_service_candidates.csv'],
    'data/processed/transit/cr_harbour_composite_service_candidates.csv': [
        'data/processed/acquisition/cr_harbour_constrained_paths_audit.json',
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_constrained_service_candidates.csv'],
    'data/processed/acquisition/cr_harbour_composite_paths_audit.json': [
        'data/processed/acquisition/cr_harbour_constrained_paths_audit.json',
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_constrained_service_candidates.csv'],
}


def segment_identity(row):
    return (int(row['osm_way_id']), int(row['native_segment_index_zero_based']),
            int(row['from_osm_node_id']), int(row['to_osm_node_id']))


def source_reference(row):
    return dict(osm_route_relation_id=row['osm_route_relation_id'],
                route_segment_index_zero_based=int(row['route_segment_index_zero_based']),
                source_member_order=int(row['source_member_order']))


def main():
    inputs = sorted(set(p for paths in OUTPUT_INPUTS.values() for p in paths))
    hashes = {p: digest(p) for p in inputs}
    parent = json.loads(Path(city.path('data/processed/acquisition/cr_harbour_constrained_paths_audit.json')).read_text(encoding='utf-8'))
    for path, recorded in parent['input_sha256'].items():
        if digest(path) != recorded:
            raise ValueError('Fixed-chain evidence has stale input: ' + path)
    boarding = defaultdict(set)
    for row in read('data/processed/network/cr_harbour_boarding_nodes.csv'):
        if row['native_presence'] == 'present' and json.loads(row['rail_parent_ways']):
            for key in json.loads(row['station_keys']):
                boarding[key].add(int(row['osm_node_id']))
    traces = defaultdict(list)
    for row in read('data/processed/network/cr_harbour_mapped_route_segments.csv'):
        traces[row['osm_route_relation_id']].append(row)
    nodes = {}
    for route_id, rows in traces.items():
        rows.sort(key=lambda r: int(r['route_segment_index_zero_based']))
        if [int(r['route_segment_index_zero_based']) for r in rows] != list(range(len(rows))):
            raise ValueError('Source route trace has missing segment positions')
        if any(a['to_osm_node_id'] != b['from_osm_node_id'] for a, b in zip(rows, rows[1:])):
            raise ValueError('Source route trace is disconnected')
        nodes[route_id] = [int(rows[0]['from_osm_node_id'])] + [int(r['to_osm_node_id']) for r in rows]
    patterns = [r for r in read('data/processed/transit/cr_harbour_path_patterns.csv') if r['variant'] == 'static_oneway_screen']
    services = read('data/processed/transit/cr_harbour_constrained_service_candidates.csv')
    service_counts = Counter(r['pattern_id'] for r in services)
    unresolved = set(parent['unresolved_patterns'])
    if unresolved != {r['pattern_id'] for r in services if int(r['candidate_count']) == 0}:
        raise ValueError('Unresolved pattern audit and service evidence disagree')
    join_rows, paths = [], {}
    ordered_routes = sorted(traces, key=int)
    for pattern in patterns:
        pattern_id = pattern['pattern_id']
        if pattern_id not in unresolved:
            continue
        keys = json.loads(pattern['station_keys_json'])
        for station_index in range(1, len(keys) - 1):
            before = [boarding[k] for k in keys[:station_index + 1]]
            after = [boarding[k] for k in keys[station_index:]]
            for left_id in ordered_routes:
                for right_id in ordered_routes:
                    if left_id == right_id:
                        continue
                    for join in shared_boarding_joins(nodes[left_id], nodes[right_id], before, after):
                        join_id = hashlib.sha256(serial([pattern_id, station_index, left_id, right_id,
                            join['left_join_position'], join['right_join_position']]).encode('utf-8')).hexdigest()
                        candidate_id = ''
                        reversal = ''
                        left_positions, right_positions = join['left_unique_positions'], join['right_unique_positions']
                        if join['assignment_count'] == 1:
                            prefix = traces[left_id][left_positions[0]:left_positions[-1]]
                            suffix = traces[right_id][right_positions[0]:right_positions[-1]]
                            if not prefix or not suffix or prefix[-1]['to_osm_node_id'] != suffix[0]['from_osm_node_id']:
                                raise ValueError('Composite boarding join is not physically continuous')
                            trace = prefix + suffix
                            incoming, outgoing = segment_identity(prefix[-1]), segment_identity(suffix[0])
                            reversal = incoming == outgoing[:2] + outgoing[2:][::-1]
                            positions = [p - left_positions[0] for p in left_positions]
                            positions += [len(prefix) + p - right_positions[0] for p in right_positions[1:]]
                            selected_nodes = [nodes[left_id][p] for p in left_positions]
                            selected_nodes += [nodes[right_id][p] for p in right_positions[1:]]
                            identities = [segment_identity(r) for r in trace]
                            candidate_id = hashlib.sha256(serial([pattern_id, selected_nodes, positions, identities]).encode('utf-8')).hexdigest()
                            if candidate_id not in paths:
                                paths[candidate_id] = dict(pattern_id=pattern_id, keys=keys, trace=trace,
                                    boarding_nodes=selected_nodes, positions=positions, joins=[],
                                    provenance=[set() for _ in trace], reversals=set())
                            candidate = paths[candidate_id]
                            if identities != [segment_identity(r) for r in candidate['trace']]:
                                raise ValueError('Composite physical-path identity collision')
                            candidate['joins'].append(join_id)
                            if reversal:
                                candidate['reversals'].add(station_index + 1)
                            for index, row in enumerate(trace):
                                candidate['provenance'][index].add(serial(source_reference(row)))
                        join_rows.append(dict(source='derived_same_native_boarding_join', join_id=join_id,
                            pattern_id=pattern_id, timetable_services=service_counts[pattern_id],
                            join_stop_sequence=station_index + 1, join_station_key=keys[station_index],
                            join_osm_node_id=join['join_node_id'], left_osm_route_relation_id=left_id,
                            right_osm_route_relation_id=right_id, left_join_node_position=join['left_join_position'],
                            right_join_node_position=join['right_join_position'], assignment_count=join['assignment_count'],
                            left_assignment_count=join['left_assignment_count'], right_assignment_count=join['right_assignment_count'],
                            left_unique_boarding_positions_json=serial(left_positions),
                            right_unique_boarding_positions_json=serial(right_positions),
                            candidate_id=candidate_id, immediate_reversal_at_join=reversal,
                            status='derived_composite_geometry_only' if candidate_id else 'ambiguous_boarding_assignments_unselected',
                            schedule_export_eligible=False))
    path_rows, segment_rows = [], []
    by_pattern = defaultdict(list)
    for candidate_id, candidate in sorted(paths.items()):
        trace, positions = candidate['trace'], candidate['positions']
        by_pattern[candidate['pattern_id']].append(candidate_id)
        lengths = [math.fsum(float(r['length_geodesic_m']) for r in trace[a:b]) for a, b in zip(positions, positions[1:])]
        path_rows.append(dict(source='derived_composite_of_mapped_passenger_track_chains', candidate_id=candidate_id,
            pattern_id=candidate['pattern_id'], timetable_services=service_counts[candidate['pattern_id']],
            station_keys_json=serial(candidate['keys']), boarding_node_ids_json=serial(candidate['boarding_nodes']),
            path_node_positions_json=serial(positions), leg_lengths_geodesic_m_json=serial(lengths),
            length_geodesic_m=math.fsum(lengths), segment_traversals=len(trace), equivalent_join_ids_json=serial(sorted(candidate['joins'])),
            immediate_reversal_stop_sequences_json=serial(sorted(candidate['reversals'])),
            direction_status_counts_json=serial(dict(sorted(Counter(r['direction_status'] for r in trace).items()))),
            status='derived_composite_candidate_current_operation_and_assignment_unverified', schedule_export_eligible=False))
        for leg, (a, b) in enumerate(zip(positions, positions[1:]), 1):
            for index in range(a, b):
                row = trace[index]
                segment_rows.append(dict(candidate_id=candidate_id, pattern_id=candidate['pattern_id'], leg_sequence=leg,
                    path_segment_sequence=index + 1, osm_way_id=row['osm_way_id'],
                    native_segment_index_zero_based=row['native_segment_index_zero_based'], from_osm_node_id=row['from_osm_node_id'],
                    to_osm_node_id=row['to_osm_node_id'], traversal_relative_to_native_order=row['traversal_relative_to_native_order'],
                    length_geodesic_m=row['length_geodesic_m'], direction_status=row['direction_status'],
                    against_preferred_direction=row['against_preferred_direction'], source_way_tags_json=row['source_way_tags_json'],
                    source_route_segment_references_json=serial([json.loads(ref) for ref in sorted(candidate['provenance'][index])])))
    service_rows = []
    for service in services:
        fixed = json.loads(service['constrained_candidate_ids_json'])
        composite = by_pattern.get(service['pattern_id'], [])
        service_rows.append(dict(train_number=service['train_number'], pattern_id=service['pattern_id'],
            fixed_chain_candidate_ids_json=serial(fixed), composite_candidate_ids_json=serial(composite),
            geometry_candidate_count=len(fixed) + len(composite),
            status='fixed_mapped_chain_evidence' if fixed else 'derived_two_chain_evidence' if composite else
                   'no_complete_one_or_two_chain_boarding_join_evidence',
            timetable_coverage_status=service['timetable_coverage_status'], timetable_applicability=service['timetable_applicability'],
            calendar_status=service['calendar_status'], schedule_export_eligible=False))
    if hashes != {p: digest(p) for p in inputs}:
        raise ValueError('Composite route inputs changed during extraction')
    report = dict(source='derived_native_boarding_join_evidence', input_sha256=hashes,
        attempted_unresolved_patterns=len(unresolved), join_candidates=len(join_rows),
        ambiguous_join_candidates=sum(r['assignment_count'] != 1 for r in join_rows),
        unique_composite_paths=len(path_rows), composite_patterns=len(by_pattern),
        newly_supported_services=sum(bool(json.loads(r['composite_candidate_ids_json'])) for r in service_rows),
        services_with_track_candidates=sum(r['geometry_candidate_count'] > 0 for r in service_rows),
        services_without_track_candidates=sum(r['geometry_candidate_count'] == 0 for r in service_rows),
        segment_rows=len(segment_rows), composite_paths_with_join_reversal=sum(bool(c['reversals']) for c in paths.values()),
        composite_paths_against_static_oneway=sum(json.loads(r['direction_status_counts_json']).get('against_explicit_oneway', 0) > 0 for r in path_rows),
        unresolved_patterns=sorted({r['pattern_id'] for r in service_rows if r['geometry_candidate_count'] == 0}),
        limitations=[
            'Two source route chains are joined only at a shared native node already identified as the same timetable boarding stop.',
            'Identical physical paths from alternative join positions count once; every source-chain segment reference remains available.',
            'A composite path is derived evidence, not an observed route relation, operating permission or train-specific platform allocation.',
            'Only previously unresolved patterns and one join between two mapped chains are assessed; lack of such evidence does not prove impossibility.',
            'Reversal flags identify immediate segment reversals only; signal routes, turnouts, gauge, train length and reversal operations still need validation.',
            'Calendars, mixed source vintages, unresolved source cells and incomplete external branches retain their original statuses. No service is exported.',
        ])
    for path, rows in (
        ('data/processed/transit/cr_harbour_composite_join_candidates.csv', join_rows),
        ('data/processed/transit/cr_harbour_composite_path_candidates.csv', path_rows),
        ('data/processed/network/cr_harbour_composite_path_segments.csv', segment_rows),
        ('data/processed/transit/cr_harbour_composite_service_candidates.csv', service_rows)):
        dump(path, rows)
    Path(city.path('data/processed/acquisition/cr_harbour_composite_paths_audit.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'input_sha256'}))


if __name__ == '__main__':
    main()
