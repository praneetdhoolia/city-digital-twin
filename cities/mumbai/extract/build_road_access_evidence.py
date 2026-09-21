"""Derive explicit road access profiles while preserving unresolved permissions."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile

import city
from build.extract_osm_network import fingerprint
from build.osm_access_evidence import ACCESS_CHAINS, access_tags, resolve
from extract_census_controls import source
from evidence_io import serial

OUTPUT_INPUTS = {
    'data/processed/network/osm_way_access_profiles.csv': ['data/processed/network/osm_way_attributes.csv'],
    'data/processed/network/osm_access_profiles.json': ['data/processed/network/osm_way_attributes.csv'],
    'data/processed/network/osm_access_class_evidence.csv': [
        'data/processed/network/osm_way_attributes.csv', 'data/raw/research/osm_wiki_*_20260919_*.html'],
    'data/processed/acquisition/road_access_evidence_audit.json': [
        'data/processed/network/osm_way_attributes.csv',
        'data/processed/acquisition/road_attribute_evidence_audit.json',
        'data/raw/research/osm_wiki_*_20260919_*.html'],
}


def main():
    input_path = Path(city.path('data/processed/network/osm_way_attributes.csv'))
    audit_path = Path(city.path('data/processed/acquisition/road_attribute_evidence_audit.json'))
    hashes = {city.rel(str(path)): fingerprint(path) for path in (input_path, audit_path)}
    parent_audit = json.loads(audit_path.read_text(encoding='utf-8'))
    native_sources = {(item['path'], item['sha256']) for item in parent_audit['inputs']}
    for path, digest in native_sources:
        if fingerprint(Path(city.path(path))) != digest:
            raise ValueError('Native source changed since road-attribute extraction')
    references = []
    for key in ('access', 'motorcar', 'psv', 'oneway'):
        sid = 'osm_wiki_' + key + '_20260919'
        record, _ = source(sid, 'research')
        references.append(dict(source_id=sid, sha256=record['sha256'], url=record['url']))
    seen, profiles, counts, by_class = set(), {}, Counter(), defaultdict(Counter)
    destination = Path(city.path('data/processed/network'))
    with tempfile.TemporaryDirectory(prefix='road-access-', dir=destination) as temporary:
        stage = Path(temporary)
        with (stage / 'osm_way_access_profiles.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['osm_way_id', 'access_profile_sha256'], lineterminator='\n')
            writer.writeheader()
            with input_path.open(encoding='utf-8', newline='') as incoming:
                for row in csv.DictReader(incoming):
                    way_id = row['osm_way_id']
                    if way_id in seen or (row['source_path'], row['source_sha256']) not in native_sources:
                        raise ValueError('Repeated way or unrecognised native provenance')
                    seen.add(way_id)
                    tags = access_tags(json.loads(row['source_tags_json']))
                    encoded = serial(tags)
                    profile_id = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
                    if profile_id in profiles and profiles[profile_id] != tags:
                        raise ValueError('Access profile hash collision')
                    profiles[profile_id] = tags
                    counts[profile_id] += 1
                    by_class[row['highway']][profile_id] += 1
                    writer.writerow(dict(osm_way_id=way_id, access_profile_sha256=profile_id))
        if len(seen) != parent_audit['counts']['attribute_rows']:
            raise ValueError('Road access rows disagree with parent extraction')
        profile_rows = [dict(access_profile_sha256=identity, source_tags=tags,
                             referenced_ways_count=counts[identity])
                        for identity, tags in sorted(profiles.items())]
        (stage / 'osm_access_profiles.json').write_text(
            json.dumps(profile_rows, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        statuses = defaultdict(Counter)
        evidence = {}
        with (stage / 'osm_access_class_evidence.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = None
            for identity, tags in sorted(profiles.items()):
                for transport in sorted(ACCESS_CHAINS):
                    resolved = resolve(tags, transport)
                    evidence[identity, transport] = resolved
                    statuses[transport][resolved['resolution_status']] += counts[identity]
                    row = dict(access_profile_sha256=identity, referenced_ways_count=counts[identity],
                               **{k: serial(v) if isinstance(v, (dict, list)) else v for k, v in resolved.items()})
                    if writer is None:
                        writer = csv.DictWriter(stream, fieldnames=list(row), lineterminator='\n')
                        writer.writeheader()
                    writer.writerow(row)
        class_counts = {}
        for highway, grouped in sorted(by_class.items()):
            class_counts[highway] = {}
            for transport in sorted(ACCESS_CHAINS):
                totals = Counter()
                for profile_id, count in grouped.items():
                    totals[evidence[profile_id, transport]['resolution_status']] += count
                class_counts[highway][transport] = dict(sorted(totals.items()))
        audit = dict(source='derived_from_mapper_reported_tags', input_sha256=hashes,
            native_inputs=parent_audit['inputs'], documentation_references=references,
            ways=len(seen), access_profiles=len(profiles),
            ways_without_explicit_access_family_tags=sum(counts[p] for p, tags in profiles.items() if not tags),
            transport_classes=sorted(ACCESS_CHAINS), class_profile_rows=len(evidence),
            way_counts_by_transport_and_status={k: dict(sorted(v.items())) for k, v in sorted(statuses.items())},
            by_highway_class=class_counts, simulation_permissions_established=0,
            limitations=[
                'Profiles preserve explicit access-family tags only; missing tags do not imply permission or prohibition.',
                'OSM transport categories are not automatic assignments to local legal classes, model modes or vehicle types.',
                'Direction, reserved lanes, physical suitability, gates, barriers, turn restrictions, traffic notices and current law must be joined separately.',
                'Conditional, directional, lane and nonstandard qualified access tags are retained without evaluation.',
                'Private, destination, customer and permit access requires traveller-specific treatment; neither generic through access nor blanket deletion is established.',
                'Motorcar tags can have disputed scope for other double-tracked vehicles. Those profiles retain a scope warning instead of silently assigning it.',
                'All highway-tagged linear evidence remains present, including inactive or non-road features; no class is declared operational by this extraction.',
                'No MATSim network was written or modified. A tagged grant does not establish a routable link.',
            ])
        (stage / 'road_access_evidence_audit.json').write_text(
            json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        if hashes != {city.rel(str(path)): fingerprint(path) for path in (input_path, audit_path)}:
            raise ValueError('Road attribute inputs changed during extraction')
        for relative in OUTPUT_INPUTS:
            target = Path(city.path(relative))
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / target.name, target)
    print(json.dumps({k: audit[k] for k in ('ways', 'access_profiles', 'class_profile_rows',
        'ways_without_explicit_access_family_tags', 'way_counts_by_transport_and_status')}))


if __name__ == '__main__':
    main()
