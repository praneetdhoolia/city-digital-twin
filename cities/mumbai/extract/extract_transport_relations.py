"""Recover ordered OSM transport relation members from the full native source.

The road-network subset intentionally retained restrictions only. This separate
evidence layer preserves stop-area, route and network membership without
pretending that a mapped route is an operating timetable or a complete graph.
"""
from collections import Counter
import csv
import json
from pathlib import Path

import pyogrio
import city
from build.extract_osm_network import entities, fingerprint

OUTPUT_INPUTS = {
    'data/processed/observed/osm_transport_relations.csv': [
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json',
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/acquisition/osm_research_audit.json',
        'data/processed/geospatial/osm_transport_areas.geojson',
        'data/processed/acquisition/osm_transport_areas_audit.json'],
    'data/processed/acquisition/osm_transport_relations_audit.json': [
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json',
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/acquisition/osm_research_audit.json',
        'data/processed/geospatial/osm_transport_areas.geojson',
        'data/processed/acquisition/osm_transport_areas_audit.json'],
}

# Source relation categories, not a declaration of operational transport modes.
RELATION_TYPES = {'public_transport', 'route', 'route_master', 'superroute', 'network', 'tracks', 'site'}


def main():
    native = Path(city.path('data/processed/geospatial/osm_full_source.osm.gz'))
    conversion = json.loads(Path(city.path('data/processed/acquisition/osm_conversion_audit.json')).read_text(encoding='utf-8'))
    research = json.loads(Path(city.path('data/processed/acquisition/osm_research_audit.json')).read_text(encoding='utf-8'))
    area_audit = json.loads(Path(city.path('data/processed/acquisition/osm_transport_areas_audit.json')).read_text(encoding='utf-8'))
    native_hash = fingerprint(native)
    if native_hash != conversion['output_sha256'] or {conversion['source_sha256'], research['source_sha256'], area_audit['source_sha256']} != {conversion['source_sha256']}:
        raise ValueError('Native and spatial evidence must use the same acquired OSM build')
    gpkg = Path(city.path('data/processed/geospatial/osm_research.gpkg'))
    seeds = {
        kind: set(pyogrio.read_dataframe(gpkg, layer=layer, columns=['osm_id'], read_geometry=False)['osm_id'].astype(str))
        for kind, layer in (('node', 'points'), ('way', 'lines'))}
    seeds['relation'] = set()
    for feature in json.loads(Path(city.path('data/processed/geospatial/osm_transport_areas.geojson')).read_text(encoding='utf-8'))['features']:
        props = feature['properties']
        seeds[props['osm_object_type']].add(props['osm_object_id'])
    records, counts = {}, Counter()
    print('SCANNING original transport relation members; node and way geometry is not copied', flush=True)
    for element in entities(native):
        counts[element.tag] += 1
        if element.tag != 'relation':
            continue
        tags = {tag.get('k'): tag.get('v', '') for tag in element.findall('tag')}
        if tags.get('type') not in RELATION_TYPES:
            continue
        identity = element.get('id')
        if identity in records:
            raise ValueError('Duplicate OSM relation identity')
        members = [dict(type=m.get('type'), ref=m.get('ref'), role=m.get('role', '')) for m in element.findall('member')]
        if any(m['type'] not in seeds or not m['ref'].isdigit() for m in members):
            raise ValueError('Invalid typed relation member')
        records[identity] = dict(tags=tags, members=members)
    expected = {singular: conversion['counts'][plural] for singular, plural in (('node', 'nodes'), ('way', 'ways'), ('relation', 'relations'))}
    if dict(counts) != expected or fingerprint(native) != native_hash:
        raise ValueError('Full OSM scan differs from verified conversion')
    direct = {identity for identity, row in records.items()
              if identity in seeds['relation'] or any(m['ref'] in seeds[m['type']] for m in row['members'])}
    retained = set(direct)
    changed = True
    while changed:
        changed = False
        for identity, row in records.items():
            children = {m['ref'] for m in row['members'] if m['type'] == 'relation'}
            if identity in retained or children & retained:
                added = ({identity} | (children & records.keys())) - retained
                if added:
                    retained.update(added)
                    changed = True
    rows = []
    member_types, roles, external_children = Counter(), Counter(), set()
    for identity in sorted(retained, key=int):
        item = records[identity]
        tags, members = item['tags'], item['members']
        member_types.update(m['type'] for m in members)
        roles.update(m['role'] for m in members)
        external_children.update(m['ref'] for m in members if m['type'] == 'relation' and m['ref'] not in retained)
        rows.append(dict(source='mapped_osm_relation', osm_relation_id=identity,
                         source_native_sha256=native_hash, source_pbf_sha256=conversion['source_sha256'],
                         relation_type=tags.get('type', ''), public_transport_tag=tags.get('public_transport', ''),
                         route_tag=tags.get('route', ''), route_master_tag=tags.get('route_master', ''),
                         name=tags.get('name', ''), ref=tags.get('ref', ''),
                         network=tags.get('network', ''), operator=tags.get('operator', ''),
                         selection_basis='direct_research_geometry_member' if identity in direct else 'related_parent_or_child',
                         member_count=len(members), ordered_members_json=json.dumps(members, ensure_ascii=False, separators=(',', ':')),
                         all_tags_json=json.dumps(tags, ensure_ascii=False, sort_keys=True),
                         status='membership_evidence_not_operating_schedule_or_reference_closed_geometry'))
    if not rows:
        raise ValueError('No transport relations intersect the research evidence')
    output = Path(city.path('data/processed/observed/osm_transport_relations.csv'))
    with output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    audit = dict(source_native_sha256=native_hash, source_pbf_sha256=conversion['source_sha256'],
                 scanned_counts=dict(counts), source_candidate_relations=len(records),
                 spatial_seed_counts={key: len(value) for key, value in seeds.items()},
                 direct_relations=len(direct), retained_relations=len(retained), related_relations_added=len(retained-direct),
                 by_relation_type=dict(sorted(Counter(r['relation_type'] for r in rows).items())),
                 by_public_transport_tag=dict(sorted(Counter(r['public_transport_tag'] for r in rows if r['public_transport_tag']).items())),
                 by_route_tag=dict(sorted(Counter(r['route_tag'] for r in rows if r['route_tag']).items())),
                 member_type_counts=dict(sorted(member_types.items())), member_role_counts=dict(sorted(roles.items())),
                 child_relations_outside_retained_categories=sorted(external_children, key=int),
                 limitations=[
                     'Selection uses the source-derived research envelope, not the final legal or simulation boundary.',
                     'Whole relations and related parents/children may extend outside the spatial seed envelope.',
                     'The selected source types include unclassified sites and networks; their presence is not proof of transport function.',
                     'Every retained member keeps its type, reference, role and ordering; member geometry availability is not asserted.',
                     'OSM route and stop-area membership do not prove current service, timetable, platform allocation or accessibility.',
                     'Unretained child relation IDs are not necessarily absent from the full raw source; category and geometry resolution remain separate.',
                 ])
    Path(city.path('data/processed/acquisition/osm_transport_relations_audit.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('source_candidate_relations', 'direct_relations', 'retained_relations', 'related_relations_added', 'by_relation_type', 'by_public_transport_tag', 'by_route_tag')}))


if __name__ == '__main__':
    main()
