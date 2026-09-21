"""Retain native turn rules, audit road joins and diagnose an upstream defect."""
from collections import Counter
import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import city
from build.extract_osm_network import entities, fingerprint
from build.osm_turn_evidence import inspect_relation
from extract_census_controls import source

OUTPUT_INPUTS = {
    'data/processed/network/osm_turn_restrictions.json': [
        'city.json#osm_network_inputs', 'data/processed/network/road_geometry/ways.csv'],
    'data/processed/acquisition/turn_restriction_audit.json': [
        'city.json#osm_network_inputs', 'data/processed/network/road_geometry/ways.csv',
        'data/raw/roads/osm_relation_*_history_20260919_*.xml',
        'data/raw/research/osm_wiki_restriction_20260919_*.html'],
}


def relation(element):
    return dict(osm_relation_id=int(element.get('id')),
        version=element.get('version'), timestamp=element.get('timestamp'),
        visible=element.get('visible'),
        source_tags={t.get('k'): t.get('v') for t in element.findall('tag')},
        members=[dict(type=m.get('type'), ref=int(m.get('ref')), role=m.get('role', ''))
                 for m in element.findall('member')])


def main():
    native = [Path(p) for p in city.network_osm_inputs()]
    ways_path = Path(city.path('data/processed/network/road_geometry/ways.csv'))
    hashes = {city.rel(str(p)): fingerprint(p) for p in [*native, ways_path]}
    with ways_path.open(encoding='utf-8', newline='') as stream:
        ways = {}
        for row in csv.DictReader(stream):
            identity = int(row['osm_way_id'])
            if identity in ways:
                raise ValueError('Repeated native road way')
            ways[identity] = json.loads(row['ordered_node_ids_json'])
    records = {}
    for path in native:
        for el in entities(path):
            if el.tag != 'relation':
                continue
            row = relation(el)
            if row['source_tags'].get('type', '').split(':', 1)[0] != 'restriction':
                continue
            identity = row['osm_relation_id']
            if identity in records:
                raise ValueError('Repeated native restriction')
            row['source_path'] = city.rel(str(path))
            row['source_sha256'] = hashes[row['source_path']]
            row.update(inspect_relation(row['source_tags'], row['members'], ways))
            records[identity] = row
    reference, _ = source('osm_wiki_restriction_20260919', 'research')
    histories = []
    for identity, snapshot in sorted(records.items()):
        if not snapshot['structural_issues']:
            continue
        history_record, history_path = source(f'osm_relation_{identity}_history_20260919', 'roads')
        history = [relation(el) for el in ET.parse(history_path).getroot().findall('relation')]
        history.sort(key=lambda r: int(r['version']))
        if not history or {r['osm_relation_id'] for r in history} != {identity}:
            raise ValueError('History must describe exactly the requested relation')
        latest = history[-1]
        matches = (latest['source_tags'] == snapshot['source_tags'] and
                   latest['members'] == snapshot['members'])
        if not matches:
            raise ValueError('History no longer matches native snapshot; review evidence')
        for r in history:
            r['structure'] = inspect_relation(r['source_tags'], r['members'], ways)
        histories.append(dict(osm_relation_id=identity,
            source={k: history_record[k] for k in ('path', 'url', 'sha256')},
            versions=history, latest_history_matches_native_members_and_tags=matches))
    values = Counter(r['source_tags'].get('restriction', '(qualified or absent)') for r in records.values())
    issues = Counter(i for r in records.values() for i in r['structural_issues'])
    scopes = Counter(i for r in records.values() for i in r['scope_review'])
    audit = dict(source='derived', input_sha256=hashes, relations_count=len(records),
        via_way_geometry_status_counts=dict(sorted(Counter(
            r['via_way_chain']['status'] for r in records.values() if r['via_way_chain']).items())),
        restriction_values=dict(sorted(values.items())),
        structural_issue_counts=dict(sorted(issues.items())),
        scope_review_counts=dict(sorted(scopes.items())),
        relations_with_structural_issues=[i for i, r in sorted(records.items()) if r['structural_issues']],
        relations_with_scope_review=[i for i, r in sorted(records.items()) if r['scope_review']],
        defective_relation_histories=histories,
        documentation_reference={k: reference[k] for k in ('path', 'url', 'sha256')},
        historical_members_restored=False, model_turns_exported=0,
        limitations=['Geometry membership is not directed turn feasibility.',
                     'Vehicle classes, exceptions, conditional scope and current legal validity remain unresolved.',
                     'Historical from/to ways do not repair the latest incomplete source relation.',
                     'Counts describe the extracted research network, not a complete legal turn inventory.'])
    for p, digest in hashes.items():
        if fingerprint(Path(city.path(p))) != digest:
            raise ValueError('Input changed during turn extraction')
    outputs = list(OUTPUT_INPUTS)
    for output, value in zip(outputs, ([r for _, r in sorted(records.items())], audit)):
        Path(city.path(output)).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n',
                                          encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('relations_count', 'restriction_values',
          'structural_issue_counts', 'scope_review_counts', 'relations_with_structural_issues')}, indent=2))


if __name__ == '__main__':
    main()
