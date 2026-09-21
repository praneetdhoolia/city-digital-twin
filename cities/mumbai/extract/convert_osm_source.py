"""Preserve the acquired PBF's full topology in the framework's XML format.

This is the entire source extract, not a clipped or runnable city network.
"""
import hashlib
import json
from pathlib import Path

import city
from convert_osm_pbf import convert
from extract_census_controls import source

OUTPUT_INPUTS = {
    'data/processed/geospatial/osm_full_source.osm.gz': ['data/raw/osm/osm_western_zone_*.osm.pbf'],
    'data/processed/acquisition/osm_conversion_audit.json': ['data/raw/osm/osm_western_zone_*.osm.pbf'],
}


def main():
    record, path = source('osm_western_zone_20260915', 'osm')
    output = Path(city.path('data/processed/geospatial/osm_full_source.osm.gz'))
    counts = convert(path, output)
    with output.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    audit = dict(schema_version=1, counts=counts, source_sha256=record['sha256'],
                 output_sha256=digest, output_bytes=output.stat().st_size,
                 geometry_scope='Entire acquired source; no boundary clipping or simplification.',
                 preserved='Node coordinates, tags, way node references, ordered relation members and roles.',
                 omitted='Contributor edit metadata and PBF header bounds; original raw bytes remain available.',
                 limits='Not a runnable network. Legal region boundary, topology closure, modal permissions, restrictions, link capacities and road matching still need validation.')
    target = Path(city.path('data/processed/acquisition/osm_conversion_audit.json'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
