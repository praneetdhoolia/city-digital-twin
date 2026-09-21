"""Build native-way road attributes for subsequent physical network assembly."""
from collections import Counter, defaultdict
import csv
import json
import os
from pathlib import Path
import tempfile

import city
from build.extract_osm_network import entities, fingerprint
from build.osm_road_attributes import resolve

OUTPUT_INPUTS = {
    'data/processed/network/osm_way_attributes.csv': ['city.json#osm_network_inputs'],
    'data/processed/acquisition/road_attribute_evidence_audit.json': ['city.json#osm_network_inputs'],
}


def main():
    inputs = [Path(path) for path in city.network_osm_inputs()]
    hashes = [fingerprint(path) for path in inputs]
    seen, counts, by_class = set(), Counter(), defaultdict(Counter)
    output = Path(city.path('data/processed/network/osm_way_attributes.csv'))
    audit_output = Path(city.path('data/processed/acquisition/road_attribute_evidence_audit.json'))
    output.parent.mkdir(parents=True, exist_ok=True)
    audit_output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='road-attributes-', dir=output.parent) as temporary:
        stage = Path(temporary, output.name)
        with stage.open('w', encoding='utf-8', newline='') as stream:
            writer = None
            for path, sha in zip(inputs, hashes):
                for el in entities(path):
                    if el.tag != 'way':
                        continue
                    identity = el.get('id')
                    if identity in seen:
                        counts['duplicate_way_occurrences_skipped'] += 1
                        continue
                    seen.add(identity)
                    tags = {t.get('k'): t.get('v', '') for t in el.findall('tag')}
                    if 'highway' not in tags:
                        continue
                    counts['highway_ways'] += 1
                    if tags.get('area') == 'yes' or len(el.findall('nd')) < 2:
                        counts['nonlinear_highway_ways_excluded'] += 1
                        continue
                    row = dict(osm_way_id=identity, highway=tags['highway'],
                               source_path=city.rel(str(path)), source_sha256=sha, **resolve(tags))
                    if writer is None:
                        writer = csv.DictWriter(stream, fieldnames=list(row), lineterminator='\n')
                        writer.writeheader()
                    writer.writerow(row)
                    counts['attribute_rows'] += 1
                    group = by_class[tags['highway']]
                    group['ways'] += 1
                    for field in ('oneway_basis', 'lanes_status', 'speed_limit_forward_status', 'speed_limit_backward_status'):
                        group[field + ':' + row[field]] += 1
                    for field in ('lane_or_direction_qualifier_keys', 'unresolved_speed_qualifier_keys'):
                        if row[field]:
                            group[field + ':present'] += 1
        if not counts['attribute_rows'] or hashes != [fingerprint(path) for path in inputs]:
            raise ValueError('Empty road evidence or source changed during extraction')
        report = dict(source='derived', inputs=[dict(path=city.rel(str(path)), sha256=sha)
                                               for path, sha in zip(inputs, hashes)],
                      counts=dict(sorted(counts.items())),
                      by_highway_class={key: dict(sorted(values.items())) for key, values in sorted(by_class.items())},
                      interpretation=[
                          'All linear highway-tagged ways retained, including paths and construction; this is not a routability decision.',
                          'Directions follow OSM node order. No geographic left/right inference.',
                          'Missing oneway remains unresolved except the documented motorway and roundabout implication.',
                          'No equal split of two-way lane totals, class defaults, free-flow speeds or capacities are imputed.',
                          'One-way totals are resolved only without conflicting counts or lane/direction qualifiers.',
                          'Posted speed candidates preserve directional precedence and explicit units; they are not observed travel speeds.',
                          'Access, time conditions, reserved lanes, source currency and official notices must be resolved before model use.',
                      ])
        audit_stage = Path(temporary, audit_output.name)
        audit_stage.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        os.replace(stage, output)
        os.replace(audit_stage, audit_output)
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
