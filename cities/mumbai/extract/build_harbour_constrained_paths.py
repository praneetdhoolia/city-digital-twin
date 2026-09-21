"""Fit timetable boarding candidates to fixed mapped passenger track chains.

Source stop-list discrepancies remain visible. This stage neither repairs OSM
relations nor infers permission, current operation or a train's platform.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

import city
from build.ordered_route_geometry import locate_ordered_stops, match_ordered_candidates
from manifest_io import manifest_reader

OUTPUT_INPUTS = {
    'data/processed/transit/cr_harbour_chain_coverage.csv': [
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/transit/cr_harbour_mapped_route_stops.csv',
        'data/processed/acquisition/cr_harbour_mapped_routes_audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/transit/cr_harbour_constrained_path_candidates.csv': [
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/transit/cr_harbour_mapped_route_stops.csv',
        'data/processed/acquisition/cr_harbour_mapped_routes_audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/network/cr_harbour_constrained_path_segments.csv': [
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/transit/cr_harbour_mapped_route_stops.csv',
        'data/processed/acquisition/cr_harbour_mapped_routes_audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/transit/cr_harbour_constrained_service_candidates.csv': [
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/transit/cr_harbour_mapped_route_stops.csv',
        'data/processed/acquisition/cr_harbour_mapped_routes_audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_service_path_candidates.csv'],
    'data/processed/acquisition/cr_harbour_constrained_paths_audit.json': [
        'data/processed/network/cr_harbour_mapped_route_segments.csv', 'data/processed/transit/cr_harbour_mapped_route_stops.csv',
        'data/processed/acquisition/cr_harbour_mapped_routes_audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/transit/cr_harbour_path_patterns.csv', 'data/processed/transit/cr_harbour_service_path_candidates.csv'],
}


def read(path):
    with Path(city.path(path)).open(encoding='utf-8') as stream:
        return list(manifest_reader(stream))


def serial(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(path):
    return hashlib.sha256(Path(city.path(path)).read_bytes()).hexdigest()


def dump(path, rows):
    if not rows:
        raise ValueError('Expected nonempty constrained-route evidence: ' + path)
    with Path(city.path(path)).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    inputs = sorted(set(p for paths in OUTPUT_INPUTS.values() for p in paths))
    hashes = {p: digest(p) for p in inputs}
    parent_audit = json.loads(Path(city.path('data/processed/acquisition/cr_harbour_mapped_routes_audit.json')).read_text(encoding='utf-8'))
    for p, recorded in parent_audit['input_sha256'].items():
        if digest(p) != recorded:
            raise ValueError('Mapped route evidence has stale input: ' + p)
    boarding = defaultdict(set)
    for row in read('data/processed/network/cr_harbour_boarding_nodes.csv'):
        if row['native_presence'] != 'present' or not json.loads(row['rail_parent_ways']):
            continue
        for key in json.loads(row['station_keys']):
            boarding[key].add(int(row['osm_node_id']))
    traces, route_stops = defaultdict(list), defaultdict(list)
    for row in read('data/processed/network/cr_harbour_mapped_route_segments.csv'):
        traces[row['osm_route_relation_id']].append(row)
    for row in read('data/processed/transit/cr_harbour_mapped_route_stops.csv'):
        route_stops[row['osm_route_relation_id']].append(row)
    route_nodes = {}
    for route_id, trace in traces.items():
        trace.sort(key=lambda r: int(r['route_segment_index_zero_based']))
        if [int(r['route_segment_index_zero_based']) for r in trace] != list(range(len(trace))):
            raise ValueError('Mapped route segment order is incomplete')
        if any(a['to_osm_node_id'] != b['from_osm_node_id'] for a, b in zip(trace, trace[1:])):
            raise ValueError('Mapped route segment chain is disconnected')
        route_nodes[route_id] = [int(trace[0]['from_osm_node_id'])] + [int(r['to_osm_node_id']) for r in trace]
        route_stops[route_id].sort(key=lambda r: int(r['route_stop_sequence']))
    patterns = [r for r in read('data/processed/transit/cr_harbour_path_patterns.csv') if r['variant'] == 'static_oneway_screen']
    services = [r for r in read('data/processed/transit/cr_harbour_service_path_candidates.csv') if r['variant'] == 'static_oneway_screen']
    service_counts = Counter(r['pattern_id'] for r in services)
    coverage_rows, candidate_rows, segment_rows, candidates_by_pattern = [], [], [], defaultdict(list)
    for pattern in patterns:
        keys = json.loads(pattern['station_keys_json'])
        for route_id, nodes in sorted(route_nodes.items(), key=lambda item: int(item[0])):
            match = match_ordered_candidates(nodes, [boarding[key] for key in keys])
            coverage_rows.append(dict(pattern_id=pattern['pattern_id'], timetable_services=service_counts[pattern['pattern_id']],
                osm_route_relation_id=route_id, status=match['status'], assignment_count=match['assignment_count'],
                station_keys_json=serial(keys), candidate_route_node_positions_json=serial(match['candidate_positions']),
                viable_route_node_positions_json=serial(match['viable_positions']),
                missing_station_keys_json=serial([keys[i] for i in match['missing_stop_indices']]),
                schedule_export_eligible=False))
            if match['assignment_count'] != 1:
                continue
            positions = match['unique_positions']
            boarding_nodes = [nodes[p] for p in positions]
            candidate_id = hashlib.sha256(serial([pattern['pattern_id'], route_id, positions]).encode('utf-8')).hexdigest()
            candidates_by_pattern[pattern['pattern_id']].append(candidate_id)
            trace = traces[route_id]
            travelled = trace[positions[0]:positions[-1]]
            listed_stops = [int(r['osm_node_id']) for r in route_stops[route_id]]
            listed_positions = locate_ordered_stops(listed_stops, boarding_nodes)
            source_order_agrees = all(r['status'] == 'present_in_order' for r in listed_positions)
            assigned_set = set(boarding_nodes)
            covered_nodes = set(nodes[positions[0]:positions[-1] + 1])
            unrepresented = sorted((set(listed_stops) & covered_nodes) - assigned_set)
            added = sorted(assigned_set - set(listed_stops))
            lengths = [math.fsum(float(r['length_geodesic_m']) for r in trace[a:b]) for a, b in zip(positions, positions[1:])]
            candidate_rows.append(dict(source='derived_boarding_assignment_on_fixed_mapped_chain', candidate_id=candidate_id,
                pattern_id=pattern['pattern_id'], timetable_services=service_counts[pattern['pattern_id']],
                osm_route_relation_id=route_id, station_keys_json=serial(keys), boarding_node_ids_json=serial(boarding_nodes),
                route_node_positions_json=serial(positions), leg_lengths_geodesic_m_json=serial(lengths),
                length_geodesic_m=math.fsum(lengths), segment_traversals=len(travelled),
                listed_stop_order_agrees=source_order_agrees,
                assigned_nodes_not_listed_in_relation_json=serial(added),
                mapped_stops_without_timetable_candidate_json=serial(unrepresented),
                direction_status_counts_json=serial(dict(sorted(Counter(r['direction_status'] for r in travelled).items()))),
                against_preferred_direction_segments=sum(r['against_preferred_direction'] == 'True' for r in travelled),
                status='mapped_track_candidate_operating_assignment_unverified', schedule_export_eligible=False))
            for leg, (a, b) in enumerate(zip(positions, positions[1:]), 1):
                for route_index in range(a, b):
                    row = trace[route_index]
                    segment_rows.append(dict(candidate_id=candidate_id, pattern_id=pattern['pattern_id'], leg_sequence=leg,
                        path_segment_sequence=route_index - positions[0] + 1, **row))
    service_rows = []
    for service in services:
        candidate_ids = candidates_by_pattern.get(service['pattern_id'], [])
        service_rows.append(dict(train_number=service['train_number'], pattern_id=service['pattern_id'],
            constrained_candidate_ids_json=serial(candidate_ids), candidate_count=len(candidate_ids),
            status='fixed_mapped_track_candidates' if candidate_ids else 'no_complete_single_mapped_chain_assignment',
            timetable_coverage_status=service['timetable_coverage_status'], timetable_applicability=service['timetable_applicability'],
            calendar_status=service['calendar_status'], schedule_export_eligible=False))
    if hashes != {p: digest(p) for p in inputs}:
        raise ValueError('Input changed during fixed-chain assignment')
    report = dict(source='derived_fixed_mapped_chain_boarding_evidence', input_sha256=hashes,
        mapped_track_chains=len(traces), timetable_patterns=len(patterns), timetable_services=len(services),
        coverage_rows=len(coverage_rows), coverage_status_counts=dict(sorted(Counter(r['status'] for r in coverage_rows).items())),
        path_candidates=len(candidate_rows), patterns_with_candidates=len(candidates_by_pattern),
        services_with_candidates=sum(r['candidate_count'] > 0 for r in service_rows),
        services_without_candidates=sum(r['candidate_count'] == 0 for r in service_rows),
        patterns_with_multiple_routes=sum(len(v) > 1 for v in candidates_by_pattern.values()),
        candidates_with_listed_stop_order_disagreement=sum(not r['listed_stop_order_agrees'] for r in candidate_rows),
        candidates_with_unrepresented_mapped_stops=sum(bool(json.loads(r['mapped_stops_without_timetable_candidate_json'])) for r in candidate_rows),
        candidates_with_unlisted_boarding_nodes=sum(bool(json.loads(r['assigned_nodes_not_listed_in_relation_json'])) for r in candidate_rows),
        candidates_against_static_oneway=sum(json.loads(r['direction_status_counts_json']).get('against_explicit_oneway', 0) > 0 for r in candidate_rows),
        segment_rows=len(segment_rows),
        unresolved_patterns=sorted(p['pattern_id'] for p in patterns if p['pattern_id'] not in candidates_by_pattern),
        limitations=[
            'Every trace follows one original mapped passenger-route way chain without shortest-path detours or station snapping.',
            'The timetable supplies stop order; disagreements with the original mapped stop list remain explicit, and no source relation is edited.',
            'A mapped stop without a timetable candidate is not evidence of a non-stop train: source omissions and quarantined cells still require resolution.',
            'All complete boarding assignments are counted; ambiguous assignments are retained as coverage evidence without arbitrary selection.',
            'Different mapped routes remain separate alternatives. Route evidence and source tags do not establish current or trip-specific operating permissions.',
            'Composite routes, reversals, missing track members, signal blocks, gauge, calendars and fleet allocation remain unresolved. No timetable is exported.',
        ])
    for path, rows in (
        ('data/processed/transit/cr_harbour_chain_coverage.csv', coverage_rows),
        ('data/processed/transit/cr_harbour_constrained_path_candidates.csv', candidate_rows),
        ('data/processed/network/cr_harbour_constrained_path_segments.csv', segment_rows),
        ('data/processed/transit/cr_harbour_constrained_service_candidates.csv', service_rows)):
        dump(path, rows)
    Path(city.path('data/processed/acquisition/cr_harbour_constrained_paths_audit.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'input_sha256'}))


if __name__ == '__main__':
    main()
