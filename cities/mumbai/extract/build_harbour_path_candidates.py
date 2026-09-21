"""Construct continuous Harbour geometry witnesses, not operational train routes."""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

import city
from build.rail_path_candidates import CandidateRouter, graph_from_segments
from evidence_io import dump_rows, read_rows, serial

OUTPUT_INPUTS = {
    'data/processed/transit/cr_harbour_path_patterns.csv': [
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/rail_geometry/audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/acquisition/cr_harbour_track_evidence_audit.json',
        'data/processed/transit/cr_harbour_stop_candidates.csv', 'data/processed/transit/cr_harbour_service_candidates.csv'],
    'data/processed/network/cr_harbour_path_segments.csv': [
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/rail_geometry/audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/acquisition/cr_harbour_track_evidence_audit.json',
        'data/processed/transit/cr_harbour_stop_candidates.csv', 'data/processed/transit/cr_harbour_service_candidates.csv'],
    'data/processed/transit/cr_harbour_service_path_candidates.csv': [
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/rail_geometry/audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/acquisition/cr_harbour_track_evidence_audit.json',
        'data/processed/transit/cr_harbour_stop_candidates.csv', 'data/processed/transit/cr_harbour_service_candidates.csv'],
    'data/processed/transit/cr_harbour_path_time_diagnostics.csv': [
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/rail_geometry/audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/acquisition/cr_harbour_track_evidence_audit.json',
        'data/processed/transit/cr_harbour_stop_candidates.csv', 'data/processed/transit/cr_harbour_service_candidates.csv'],
    'data/processed/acquisition/cr_harbour_path_audit.json': [
        'data/processed/network/rail_geometry/ways.csv', 'data/processed/network/rail_geometry/segments.csv',
        'data/processed/network/rail_geometry/audit.json', 'data/processed/network/cr_harbour_boarding_nodes.csv',
        'data/processed/acquisition/cr_harbour_track_evidence_audit.json',
        'data/processed/transit/cr_harbour_stop_candidates.csv', 'data/processed/transit/cr_harbour_service_candidates.csv'],
}


def main():
    inputs = sorted(set(p for paths in OUTPUT_INPUTS.values() for p in paths))
    hashes = {p: hashlib.sha256(Path(city.path(p)).read_bytes()).hexdigest() for p in inputs}
    geometry_audit = json.loads(Path(city.path('data/processed/network/rail_geometry/audit.json')).read_text(encoding='utf-8'))
    boarding_audit = json.loads(Path(city.path('data/processed/acquisition/cr_harbour_track_evidence_audit.json')).read_text(encoding='utf-8'))
    if geometry_audit['input_sha256'] != [boarding_audit['source_native_sha256']]:
        raise ValueError('Boarding and railway geometry must use the same native build')
    ways = {int(r['osm_way_id']): r for r in read_rows('data/processed/network/rail_geometry/ways.csv')
            if r['railway_tag'] == 'rail' and r['geometry_role'] != 'area_boundary'}
    way_tags = {k: json.loads(v['source_tags_json']) for k,v in ways.items()}
    segments = [r for r in read_rows('data/processed/network/rail_geometry/segments.csv') if int(r['osm_way_id']) in ways]
    station_nodes = defaultdict(set)
    for row in read_rows('data/processed/network/cr_harbour_boarding_nodes.csv'):
        if row['native_presence'] != 'present' or not json.loads(row['rail_parent_ways']):
            continue
        if row['source_native_sha256'] != boarding_audit['source_native_sha256']:
            raise ValueError('Boarding row has stale native source identity')
        for key in json.loads(row['station_keys']):
            station_nodes[key].add(int(row['osm_node_id']))
    trains = defaultdict(list)
    for row in read_rows('data/processed/transit/cr_harbour_stop_candidates.csv'):
        trains[row['train_number']].append(row)
    services = {r['train_number']:r for r in read_rows('data/processed/transit/cr_harbour_service_candidates.csv')}
    if services.keys() != trains.keys():
        raise ValueError('Timetable service/stop sets disagree')
    patterns, train_pattern = {}, {}
    for train, rows in sorted(trains.items()):
        rows.sort(key=lambda r:int(r['stop_sequence']))
        if [int(r['stop_sequence']) for r in rows] != list(range(1,len(rows)+1)):
            raise ValueError('Timetable stop sequence is not contiguous')
        sequence = tuple(r['station_key'] for r in rows)
        identity = hashlib.sha256(serial(sequence).encode('utf-8')).hexdigest()
        if identity in patterns and patterns[identity] != sequence:
            raise ValueError('Pattern identifier collision')
        patterns[identity], train_pattern[train] = sequence, identity
    pattern_rows, segment_rows, service_rows, time_rows = [], [], [], []
    reversal_evidence = []
    variant_counts = {}
    for variant, screening in (('geometry_only', False), ('static_oneway_screen', True)):
        router = CandidateRouter(graph_from_segments(segments, way_tags, screen_static_oneway=screening))
        results = {}
        for identity, sequence in sorted(patterns.items()):
            missing = [key for key in sequence if not station_nodes[key]]
            route = router.through_stops([station_nodes[key] for key in sequence])
            status = 'unresolved_station_identity' if missing else 'no_continuous_path' if route is None else 'continuous_geometry_candidate_only'
            results[identity] = (status, route)
            arcs = [arc for leg in route['legs'] for arc in leg] if route else []
            flags = Counter(a.direction_status for a in arcs)
            pattern_rows.append(dict(source='derived_geometry_witness', pattern_id=identity, variant=variant,
                station_keys_json=serial(sequence), missing_station_keys_json=serial(missing), status=status,
                boarding_node_ids_json=serial(route['boarding_nodes']) if route else '[]',
                length_geodesic_m=route['length_m'] if route else '', segment_traversals=len(arcs),
                direction_status_segment_counts_json=serial(dict(sorted(flags.items()))),
                unresolved_direction_length_m=math.fsum(a.length_m for a in arcs if 'unresolved' in a.direction_status) if route else '',
                against_static_oneway_length_m=math.fsum(a.length_m for a in arcs if a.direction_status=='against_explicit_oneway') if route else '',
                assignment_status='not_an_operational_path_switch_signals_gauge_and_platform_allocation_unvalidated'))
            if route:
                ordered_arcs = [(leg_index, arc) for leg_index, leg in enumerate(route['legs'], 1) for arc in leg]
                for (previous_leg, incoming), (next_leg, outgoing) in zip(ordered_arcs, ordered_arcs[1:]):
                    if (incoming.way, incoming.segment, incoming.start, incoming.end) != (
                            outgoing.way, outgoing.segment, outgoing.end, outgoing.start):
                        continue
                    at_stop = next_leg == previous_leg + 1
                    boundary_key = sequence[previous_leg] if at_stop else ''
                    dwell_evidence = []
                    if at_stop:
                        for train, stops in sorted(trains.items()):
                            if train_pattern[train] != identity:
                                continue
                            stop = stops[previous_leg]
                            if int(stop['boundary_dwell_seconds'] or 0) > 0:
                                dwell_evidence.append(dict(train_number=train,
                                    boundary_arrival_hhmm=stop['boundary_arrival_hhmm'],
                                    boundary_departure_hhmm=stop['boundary_departure_hhmm'],
                                    boundary_dwell_seconds=int(stop['boundary_dwell_seconds']),
                                    source_references=json.loads(stop['source_references'])))
                    reversal_evidence.append(dict(pattern_id=identity, variant=variant,
                        osm_node_id=incoming.end, osm_way_id=incoming.way,
                        native_segment_index_zero_based=incoming.segment,
                        previous_leg_sequence=previous_leg, next_leg_sequence=next_leg,
                        station_key=boundary_key, reversal_at_scheduled_stop=at_stop,
                        native_way_tags=way_tags[incoming.way], timed_boundary_service_evidence=dwell_evidence,
                        status='geometry_reversal_only_dwell_does_not_establish_operating_permission_or_train_clearance'))
                traversal = 0
                for leg_index, leg in enumerate(route['legs'],1):
                    for arc in leg:
                        traversal += 1
                        tags = way_tags[arc.way]
                        side = 'forward' if arc.forward else 'backward'
                        preferred = tags.get('railway:preferred_direction','')
                        segment_rows.append(dict(pattern_id=identity, variant=variant, leg_sequence=leg_index,
                            path_segment_sequence=traversal, osm_way_id=arc.way, native_segment_index_zero_based=arc.segment,
                            from_osm_node_id=arc.start, to_osm_node_id=arc.end, traversal_relative_to_native_order=side,
                            length_geodesic_m=arc.length_m, direction_status=arc.direction_status,
                            oneway_as_tag=tags.get('oneway',''), preferred_direction_as_tag=preferred,
                            against_preferred_direction=preferred in ('forward','backward') and preferred!=side,
                            bidirectional_as_tag=tags.get('railway:bidirectional',''), gauge_as_tag=tags.get('gauge',''),
                            service_as_tag=tags.get('service',''), usage_as_tag=tags.get('usage',''),
                            maxspeed_as_tag=tags.get('maxspeed',''), directional_maxspeed_as_tag=tags.get('maxspeed:'+side,'')))
        for train, stops in sorted(trains.items()):
            identity = train_pattern[train]
            status, route = results[identity]
            service_rows.append(dict(train_number=train, pattern_id=identity, variant=variant, status=status,
                candidate_length_geodesic_m=route['length_m'] if route else '',
                timetable_coverage_status=services[train]['coverage_status'],
                timetable_applicability=services[train]['applicability'],
                calendar_status=services[train]['calendar_status'], schedule_export_eligible=False))
            for index, (a,b) in enumerate(zip(stops,stops[1:]),1):
                # Explicit boundary dwell is removed from the preceding clock;
                # all other arrival/departure ambiguities remain visible.
                interval = int(b['elapsed_seconds_since_first_printed_time'])-int(a['elapsed_seconds_since_first_printed_time'])-int(a['boundary_dwell_seconds'] or 0)
                length = math.fsum(arc.length_m for arc in route['legs'][index-1]) if route else None
                time_rows.append(dict(train_number=train, pattern_id=identity, variant=variant, leg_sequence=index,
                    from_station_key=a['station_key'], to_station_key=b['station_key'],
                    candidate_length_geodesic_m=length if length is not None else '', printed_interval_seconds=interval,
                    removed_explicit_origin_dwell_seconds=a['boundary_dwell_seconds'] or 0,
                    geometry_distance_over_printed_interval_kmh=length/interval*3.6 if length is not None and interval>0 else '',
                    status='diagnostic_only_unresolved_clock_roles_and_minute_precision' if route and interval>0 else status if route is None else 'nonpositive_printed_interval_requires_review'))
        variant_counts[variant] = dict(pattern_status_counts=dict(sorted(Counter(s for s,_ in results.values()).items())),
            service_status_counts=dict(sorted(Counter(results[train_pattern[t]][0] for t in trains).items())),
            patterns_with_unresolved_direction=sum(bool(r['unresolved_direction_length_m']) for r in pattern_rows if r['variant']==variant),
            patterns_against_explicit_oneway=sum(bool(r['against_static_oneway_length_m']) for r in pattern_rows if r['variant']==variant),
            patterns_against_preferred_direction=len({r['pattern_id'] for r in segment_rows if r['variant']==variant and r['against_preferred_direction']}),
            nonpositive_printed_intervals=sum(r['printed_interval_seconds']<=0 for r in time_rows if r['variant']==variant),
            cached_boarding_pairs=len(router.paths))
        print(variant, json.dumps(variant_counts[variant]), flush=True)
    if hashes != {p:hashlib.sha256(Path(city.path(p)).read_bytes()).hexdigest() for p in inputs}:
        raise ValueError('Rail path inputs changed during construction')
    for path, rows in (
        ('data/processed/transit/cr_harbour_path_patterns.csv',pattern_rows),
        ('data/processed/network/cr_harbour_path_segments.csv',segment_rows),
        ('data/processed/transit/cr_harbour_service_path_candidates.csv',service_rows),
        ('data/processed/transit/cr_harbour_path_time_diagnostics.csv',time_rows)):
        dump_rows(path, rows)
    audit = dict(source='derived_geometry_and_timetable_evidence', input_sha256=hashes,
        source_native_sha256=boarding_audit['source_native_sha256'], station_patterns=len(patterns), timetable_services=len(trains),
        rail_ways=len(ways), rail_segments=len(segments), variants=variant_counts,
        immediate_segment_reversals=reversal_evidence,
        pattern_rows=len(pattern_rows), segment_traversal_rows=len(segment_rows), service_rows=len(service_rows), interval_rows=len(time_rows),
        limitations=[
            'Paths minimise horizontal geometric distance through all candidate stops jointly; consecutive legs share their intermediate boarding node.',
            'Geometry-only paths ignore directions. The second variant screens static explicit oneway tags but permits unresolved directions as candidates only.',
            'Preferred direction is retained as evidence, not treated as an absolute prohibition. Conditional directions remain unresolved.',
            'Track switches, reversal feasibility, signals, gauge compatibility, current operating status and service-specific platform allocation are not established.',
            'Immediate reversal diagnostics retain source boundary clocks; dwell does not prove permission or train clearance, and repeated variants are not additional services.',
            'Sidings and yard tracks remain in the geometry graph; shortest paths are not proof of passenger operating routes.',
            'Timetable distances/time ratios are diagnostics, not observed speed, free-flow speed or capacity. Clock roles, minute precision and calendars remain unresolved.',
            'Incomplete external branches and mixed timetable vintages retain their source status. No service is eligible for schedule export.',
        ], tagging_references=['https://wiki.openstreetmap.org/wiki/Key:oneway','https://wiki.openstreetmap.org/wiki/Key:railway:preferred_direction'])
    Path(city.path('data/processed/acquisition/cr_harbour_path_audit.json')).write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('input_sha256','limitations','tagging_references','immediate_segment_reversals')}))


if __name__ == '__main__':
    main()
