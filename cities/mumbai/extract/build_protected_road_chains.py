"""Reduce geometry segmentation while retaining native controls and every edge."""
from collections import Counter
import csv
from decimal import Decimal, Inexact, localcontext
import itertools
import json
import os
from pathlib import Path
import tempfile

import city
from build.extract_osm_network import entities, fingerprint
from build.protected_way_segments import partition, protected_nodes
from evidence_io import serial

OUTPUT_INPUTS = {
    'data/processed/network/road_chains/nodes.csv': [
        'data/processed/network/road_geometry/*', 'data/processed/network/road_rail_shared_nodes.csv',
        'city.json#osm_network_inputs'],
    'data/processed/network/road_chains/chains.csv': [
        'data/processed/network/road_geometry/*', 'data/processed/network/road_rail_shared_nodes.csv',
        'data/processed/network/osm_way_access_profiles.csv', 'city.json#osm_network_inputs'],
    'data/processed/network/road_chains/audit.json': [
        'data/processed/network/road_geometry/*', 'data/processed/network/road_rail_shared_nodes.csv',
        'data/processed/network/osm_way_access_profiles.csv', 'city.json#osm_network_inputs'],
}


def rows(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        yield from csv.DictReader(stream)


def build_chains():
    base = Path(city.path('data/processed/network'))
    geometry = base / 'road_geometry'
    native_paths = [Path(p) for p in city.network_osm_inputs()]
    paths = [geometry / name for name in ('nodes.csv', 'ways.csv', 'segments.csv', 'audit.json')]
    paths += [base / 'road_rail_shared_nodes.csv', base / 'osm_way_access_profiles.csv'] + native_paths
    hashes = {city.rel(str(p)): fingerprint(p) for p in paths}
    parent = json.loads((geometry / 'audit.json').read_text(encoding='utf-8'))
    if parent['input_sha256'] != [hashes[city.rel(str(p))] for p in native_paths]:
        raise ValueError('Native restriction source differs from geometry build')
    ways, records = {}, {}
    for row in rows(geometry / 'ways.csv'):
        identity = int(row['osm_way_id'])
        if identity in ways:
            raise ValueError('Duplicate native way')
        ways[identity] = json.loads(row['ordered_node_ids_json'])
        records[identity] = row
    tagged = {int(r['osm_node_id']) for r in rows(geometry / 'nodes.csv') if json.loads(r['source_tags_json'])}
    anchors = {'road_rail_shared_identity': {int(r['osm_node_id']) for r in rows(base / 'road_rail_shared_nodes.csv')},
               'restriction_node_member': set(), 'restriction_way_member': set()}
    restriction_ids, member_way_ids = set(), set()
    restriction_details = {}
    for path in native_paths:
        for el in entities(path):
            if el.tag != 'relation':
                continue
            tags = {t.get('k'): t.get('v') for t in el.findall('tag')}
            if tags.get('type') != 'restriction':
                continue
            relation_id = int(el.get('id'))
            restriction_ids.add(relation_id)
            restriction_details[relation_id] = dict(osm_relation_id=relation_id, source_tags=tags,
                members=[dict(type=m.get('type'), ref=int(m.get('ref')), role=m.get('role', ''))
                         for m in el.findall('member')])
            for member in el.findall('member'):
                identity = int(member.get('ref'))
                if member.get('type') == 'node':
                    anchors['restriction_node_member'].add(identity)
                elif member.get('type') == 'way':
                    member_way_ids.add(identity)
                    if identity in ways:
                        anchors['restriction_way_member'].update(ways[identity])
    protected, absent = protected_nodes(ways, tagged, anchors)
    if absent['road_rail_shared_identity'] or tagged - protected.keys():
        raise ValueError('Known tagged or shared road nodes were not retained')
    access = {}
    for row in rows(base / 'osm_way_access_profiles.csv'):
        identity = int(row['osm_way_id'])
        if identity in access or identity not in ways:
            raise ValueError('Invalid access-profile way join')
        access[identity] = row['access_profile_sha256']
    target = base / 'road_chains'
    target.mkdir(parents=True, exist_ok=True)
    chain_count = source_segments = zero_lengths = self_loops = retained_node_count = 0
    length_totals = {'projected': Decimal(0), 'geodesic': Decimal(0)}
    chain_length_totals = {'projected': Decimal(0), 'geodesic': Decimal(0)}
    seen_ways = set()
    with tempfile.TemporaryDirectory(prefix='protected-chains-', dir=target) as temporary:
        stage = Path(temporary)
        with (stage / 'nodes.csv').open('w', encoding='utf-8', newline='') as out:
            writer = None
            for row in rows(geometry / 'nodes.csv'):
                identity = int(row['osm_node_id'])
                if identity not in protected:
                    continue
                row['retention_reasons_json'] = serial(protected[identity])
                if writer is None:
                    writer = csv.DictWriter(out, fieldnames=list(row), lineterminator='\n')
                    writer.writeheader()
                writer.writerow(row)
                retained_node_count += 1
        with (stage / 'chains.csv').open('w', encoding='utf-8', newline='') as out:
            writer = None
            for identity, group in itertools.groupby(rows(geometry / 'segments.csv'), key=lambda r: int(r['osm_way_id'])):
                if identity in seen_ways or identity not in ways:
                    raise ValueError('Invalid native segment group')
                seen_ways.add(identity)
                refs, record = ways[identity], records[identity]
                segments = list(group)
                if len(segments) != len(refs) - 1:
                    raise ValueError('Native segment count mismatch')
                for index, seg in enumerate(segments):
                    if (int(seg['segment_index_zero_based']) != index or
                            [int(seg['from_osm_node_id']), int(seg['to_osm_node_id'])] != refs[index:index + 2]):
                        raise ValueError('Native segment adjacency mismatch')
                    for kind in length_totals:
                        value = Decimal(seg['length_' + kind + '_m'])
                        if not value.is_finite() or value < 0:
                            raise ValueError('Invalid native segment length')
                        length_totals[kind] += value
                covered = 0
                for start, end in partition(refs, protected):
                    if start != covered or any(n in protected for n in refs[start + 1:end]):
                        raise ValueError('Partition loses a segment or a protected interior node')
                    covered = end
                    lengths = {kind: sum((Decimal(s['length_' + kind + '_m']) for s in segments[start:end]), Decimal(0))
                               for kind in length_totals}
                    for kind, value in lengths.items():
                        chain_length_totals[kind] += value
                    zero_lengths += lengths['geodesic'] == 0
                    self_loops += refs[start] == refs[end]
                    row = dict(native_chain_id=f'{identity}:{start}:{end}', osm_way_id=identity,
                        first_source_segment_index_zero_based=start, last_source_segment_index_exclusive=end,
                        from_osm_node_id=refs[start], to_osm_node_id=refs[end], source_segment_count=end - start,
                        length_projected_m=str(lengths['projected']), length_geodesic_m=str(lengths['geodesic']),
                        ordered_node_ids_json=serial(refs[start:end + 1]), highway_tag=record['highway_tag'],
                        geometry_role=record['geometry_role'], access_profile_sha256=access.get(identity, ''),
                        model_input_status='geometry_candidate_not_simulation_link')
                    if writer is None:
                        writer = csv.DictWriter(out, fieldnames=list(row), lineterminator='\n')
                        writer.writeheader()
                    writer.writerow(row)
                    chain_count += 1
                if covered != len(segments):
                    raise ValueError('Incomplete native segment coverage')
                source_segments += len(segments)
        if (seen_ways != ways.keys() or retained_node_count != len(protected) or
                source_segments != parent['segments'] or length_totals != chain_length_totals):
            raise ValueError('Geometry retention or exact decimal length identity failed')
        reasons = Counter(reason for reason_list in protected.values() for reason in reason_list)
        report = dict(source='derived_native_geometry_partition', input_sha256=hashes,
            source_nodes=parent['nodes'], source_ways=len(ways), source_segments=source_segments,
            retained_nodes=len(protected), tagged_source_nodes=len(tagged), native_chains=chain_count,
            internal_shape_nodes=parent['nodes'] - len(protected),
            retention_reason_counts=dict(sorted(reasons.items())), restriction_relations=len(restriction_ids),
            restriction_member_ways_outside_road_geometry=sorted(member_way_ids - ways.keys()),
            supplied_anchors_outside_road_geometry=absent, self_loop_chains=self_loops, zero_length_chains=zero_lengths,
            restriction_relations_with_node_members_outside_road_geometry=[r for _, r in sorted(restriction_details.items())
                if any(m['type'] == 'node' and m['ref'] in absent['restriction_node_member'] for m in r['members'])],
            exact_sums_of_input_decimal_lengths_m={k: str(v) for k, v in length_totals.items()},
            segment_coverage='every_native_adjacent_segment_once_in_source_order',
            model_links_exported=0, limitations=[
                'All source tags survive on retained nodes; parent-way tags remain in the native way table.',
                'Lengths are exact sums of the decimal representations in the input segment table, not an assertion of survey precision.',
                'Shape nodes remain in each ordered chain geometry and are not deleted from the source tables.',
                'Area and lifecycle-only geometry retains its source role; the candidate chains do not confer operating status.',
                'Unmapped transit stops and activity connectors may require more anchors before a final network is assembled.',
                'Control-node retention does not implement gate, signal, crossing, permission or turn behaviour.',
                'Queue storage, flow, discrete time steps and junction interactions require simulation equivalence tests before adopting a reduction.',
            ])
        if hashes != {city.rel(str(p)): fingerprint(p) for p in paths}:
            raise ValueError('Inputs changed during protected-chain construction')
        (stage / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
        for name in ('nodes.csv', 'chains.csv', 'audit.json'):
            os.replace(stage / name, target / name)
    print(json.dumps({k: v for k, v in report.items() if k != 'input_sha256'}), flush=True)


def main():
    # Exact-sum claims must fail rather than silently round if a future input
    # exceeds the Decimal context's precision. This changes no model tolerance.
    with localcontext() as context:
        context.traps[Inexact] = True
        build_chains()


if __name__ == '__main__':
    main()
