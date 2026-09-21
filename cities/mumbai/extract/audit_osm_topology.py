"""Independently parse converted XML and count retained network evidence.

This streaming check does not establish reference closure or legal permissions.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import city
from osm_parse import parse

OUTPUT_INPUTS = {
    'data/processed/acquisition/osm_topology_audit.json': [
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json'],
}


def main():
    converted = json.loads(Path(city.path('data/processed/acquisition/osm_conversion_audit.json')).read_text(encoding='utf-8'))
    xml_path = Path(city.path('data/processed/geospatial/osm_full_source.osm.gz'))
    with xml_path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != converted['output_sha256']:
        raise ValueError('Converted XML differs from the recorded PBF conversion')
    counts, highways, relations, controls = Counter(), Counter(), Counter(), Counter()
    invalid_nodes = short_ways = empty_relations = 0
    for entity in parse(xml_path):
        kind, tags = entity[0], entity[-1]
        counts[kind] += 1
        if kind == 'node':
            lat, lon = entity[2:4]
            invalid_nodes += not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180)
            if tags.get('highway') == 'traffic_signals':
                controls['signal_nodes'] += 1
            if 'barrier' in tags:
                controls['barrier_nodes'] += 1
        elif kind == 'way':
            short_ways += len(entity[2]) < 2
            if 'highway' in tags:
                highways[tags['highway']] += 1
                for key in tags:
                    if key.split(':')[0] in ('access', 'vehicle', 'motor_vehicle', 'motorcar', 'motorcycle', 'bicycle', 'foot', 'bus', 'psv', 'hgv', 'oneway', 'maxspeed', 'lanes', 'toll'):
                        controls['highway_way_tag:'+key] += 1
        else:
            relations[tags.get('type', '(missing)')] += 1
            empty_relations += not entity[2]
    mapped = dict(nodes=counts['node'], ways=counts['way'], relations=counts['rel'])
    if mapped != converted['counts']:
        raise ValueError('Independent XML parser counts differ from PBF conversion counts')
    audit = dict(schema_version=1, counts=mapped, counts_agree=True,
                 invalid_node_coordinates=invalid_nodes, ways_with_fewer_than_two_nodes=short_ways,
                 empty_relations=empty_relations, highway_classes=dict(sorted(highways.items())),
                 relation_types=dict(sorted(relations.items())), control_evidence=dict(sorted(controls.items())),
                 limits='Whole acquired source extent, not city counts. Syntax and entity counts only; no missing-reference, duplicate-ID, turn-restriction applicability, connectivity or road-capacity validation.')
    target = Path(city.path('data/processed/acquisition/osm_topology_audit.json'))
    target.write_text(json.dumps(audit, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('highway_classes','relation_types','control_evidence')}))


if __name__ == '__main__':
    main()
