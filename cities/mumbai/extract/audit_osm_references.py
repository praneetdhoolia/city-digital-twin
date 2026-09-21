"""Check identities and complete way/relation references in the acquired OSM source."""
import hashlib
import json
from pathlib import Path

import city
from build.audit_osm_references import audit

OUTPUT_INPUTS = {
    'data/processed/acquisition/osm_reference_audit.json': [
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json'],
    'data/processed/acquisition/osm_missing_references.csv': [
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json'],
    'data/processed/acquisition/osm_duplicate_ids.csv': [
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json'],
}


def main():
    converted = json.loads(Path(city.path('data/processed/acquisition/osm_conversion_audit.json')).read_text(encoding='utf-8'))
    source = Path(city.path('data/processed/geospatial/osm_full_source.osm.gz'))
    with source.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != converted['output_sha256']:
            raise ValueError('Converted source differs from its recorded hash')
    result = audit(source, Path(city.path('data/processed/acquisition')))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
