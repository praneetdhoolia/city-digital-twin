"""Independently check identities and references in the native network input."""
import hashlib
import json
from pathlib import Path

import city
from build.audit_osm_references import audit

OUTPUT_INPUTS = {
    'data/processed/acquisition/network_source/osm_reference_audit.json': [
        'networks/osm/network_source.osm.gz',
        'data/processed/acquisition/osm_network_source_audit.json'],
    'data/processed/acquisition/network_source/osm_missing_references.csv': [
        'networks/osm/network_source.osm.gz',
        'data/processed/acquisition/osm_network_source_audit.json'],
    'data/processed/acquisition/network_source/osm_duplicate_ids.csv': [
        'networks/osm/network_source.osm.gz',
        'data/processed/acquisition/osm_network_source_audit.json'],
}


def main():
    expected = json.loads(Path(city.path('data/processed/acquisition/osm_network_source_audit.json')).read_text(encoding='utf-8'))
    source = Path(city.path('networks/osm/network_source.osm.gz'))
    with source.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != expected['output_sha256']:
            raise ValueError('Native network source differs from its extraction audit')
    result = audit(source, Path(city.path('data/processed/acquisition/network_source')))
    if not result['identity_and_reference_checks_pass'] or result['counts'] != expected['output_counts']:
        raise ValueError('Native network identity or reference verification failed')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
