"""Inspect acquired boundary files without silently repairing or clipping them."""
import hashlib
import json
from pathlib import Path
import zipfile

import pyogrio
from shapely import is_valid_reason
import city

OUTPUT_INPUTS = {
    'data/processed/acquisition/boundary_source_audit.json': ['data/raw/boundaries/iitb_*.zip'],
}


def main():
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    sources = []
    for entry in catalogue['sources']:
        if entry['category'] != 'boundaries' or entry['format'] != 'zip':
            continue
        provenance = Path(city.path('data/raw/boundaries', 'provenance_' + entry['id'] + '.json'))
        if not provenance.exists():
            continue
        record = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
        path = Path(city.path(record['path']))
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                raise ValueError('Boundary source hash mismatch')
        layers = []
        with zipfile.ZipFile(path) as archive:
            members = sorted(n for n in archive.namelist() if n.lower().endswith('.shp'))
        for member in members:
            geo = pyogrio.read_dataframe('/vsizip/' + path.as_posix() + '/' + member)
            nonempty = geo.geometry.notna() & ~geo.geometry.is_empty
            invalid = nonempty & ~geo.geometry.is_valid
            names = {}
            for column in ('Name', 'district_n', 'taluka_nam'):
                if column in geo:
                    names[column] = sorted(str(v) for v in geo[column].dropna().unique())
            layer = dict(
                member=member, feature_count=len(geo), crs=str(geo.crs) if geo.crs else None,
                missing_or_empty_geometry_count=int((~nonempty).sum()),
                invalid_geometry_count=int(invalid.sum()),
                invalid_geometry_examples=[str(is_valid_reason(g)) for g in geo.loc[invalid, 'geometry'].head(5)],
                attributes=[c for c in geo.columns if c != 'geometry'], administrative_names=names,
                extent_wgs84_from_dataset=geo.loc[nonempty].to_crs(4326).total_bounds.tolist()
                if geo.crs and nonempty.any() else None,
            )
            layers.append(layer)
        sources.append(dict(source_id=entry['id'], source_path=record['path'],
                            source_sha256=record['sha256'], layers=layers))
    result = dict(
        schema_version=1, sources=sources,
        validation_scope='Source geometry inventory only; not a legal MMR boundary or census crosswalk',
        unresolved=[
            'The notified MMR includes partial areas along Tansa River and specified Karjat villages.',
            'Current administrative boundaries and census geography are not interchangeable.',
            'Invalid geometries must be repaired with an audited change in area and topology before use.',
            'An empty shapefile is not acquired usable geometry, even if its ZIP downloaded correctly.',
            'Boundary completeness must be checked against census totals, gazette and adjacent areas.',
        ],
    )
    output = Path(city.path('data/processed/acquisition/boundary_source_audit.json'))
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'sources': len(sources), 'layers': sum(len(s['layers']) for s in sources),
                      'empty_layers': [s['source_id'] for s in sources if any(not l['feature_count'] for l in s['layers'])]}))


if __name__ == '__main__':
    main()
