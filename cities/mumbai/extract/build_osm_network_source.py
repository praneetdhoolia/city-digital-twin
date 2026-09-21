"""Build native OSM network input over the source-derived research envelope."""
import hashlib
import json
from pathlib import Path
import warnings

import pyogrio
from shapely.geometry import box

import city
from extract_osm_network import extract
from extract_census_controls import source

OUTPUT_INPUTS = {
    'networks/osm/network_source.osm.gz': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json',
        'data/processed/acquisition/raster_tile_selection.json'],
    'data/processed/acquisition/osm_network_source_audit.json': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/processed/geospatial/osm_full_source.osm.gz',
        'data/processed/acquisition/osm_conversion_audit.json',
        'data/processed/acquisition/raster_tile_selection.json'],
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    record, pbf = source('osm_western_zone_20260915', 'osm')
    converted = Path(city.path('data/processed/geospatial/osm_full_source.osm.gz'))
    conversion = json.loads(Path(city.path('data/processed/acquisition/osm_conversion_audit.json')).read_text(encoding='utf-8'))
    if conversion['source_sha256'] != record['sha256'] or digest(converted) != conversion['output_sha256']:
        raise ValueError('Native XML and spatial seed PBF must be the same source build')
    selection_path = Path(city.path('data/processed/acquisition/raster_tile_selection.json'))
    selection = json.loads(selection_path.read_text(encoding='utf-8'))
    bounds = selection['extent_wgs84']
    if len(bounds) != 4 or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError('Invalid source-derived envelope')
    area = box(*bounds)
    nodes, ways, layers, spatial_warnings = set(), set(), [], []
    # OGR puts closed area ways in multipolygons. Reading only lines would
    # omit these native ways, including some pedestrian spaces.
    for layer, field, target in [('points', 'osm_id', nodes), ('lines', 'osm_id', ways),
                                 ('multipolygons', 'osm_way_id', ways)]:
        print('Spatial seeds:', layer, flush=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            frame = pyogrio.read_dataframe(pbf, layer=layer, columns=[field], bbox=tuple(bounds))
        spatial_warnings.extend(dict(layer=layer, warning=str(item.message)) for item in caught)
        if frame.crs is None or frame.crs.to_epsg() != 4326:
            raise ValueError('Seed layer must use WGS84')
        selected = frame[field].notna() & frame.geometry.notna() & frame.geometry.intersects(area)
        identifiers = frame.loc[selected, field].astype('int64')
        if identifiers.duplicated().any():
            raise ValueError('Duplicate source IDs in spatial layer: ' + layer)
        target.update(int(n) for n in identifiers)
        layers.append(dict(layer=layer, id_field=field, native_entities_selected=len(identifiers),
                           envelope_candidates=len(frame),
                           invalid_selected_geometries=int((~frame.loc[selected].geometry.is_valid).sum())))
    print('Extracting native topology:', len(nodes), 'seed nodes,', len(ways), 'seed ways', flush=True)
    output = Path(city.path('networks/osm/network_source.osm.gz'))
    report = extract(converted, output, node_ids=nodes, way_ids=ways)
    report.update(source='derived', raw_pbf_sha256=record['sha256'],
                  selection_sha256=digest(selection_path), selection_extent_wgs84=bounds,
                  spatial_seed_layers=layers, gdal_version=pyogrio.__gdal_version_string__,
                  spatial_parser_warnings=spatial_warnings,
                  spatial_parser_warning_scope='The PBF driver processes the source before its spatial filter; warnings need not identify an in-envelope feature. Native way sequences are retained without OGR repairs.',
                  output_bytes=output.stat().st_size,
                  geometry_scope='Research envelope overcoverage with complete ways and touching restrictions; not the legal MMR boundary',
                  preserved='Native coordinates, way-node sequence, selected relation-member sequence, roles and all entity tags',
                  excluded='Other relations except required nested members; GTFS, route inventory and legal boundary remain separate inputs',
                  licence='ODbL 1.0; OpenStreetMap contributors')
    Path(city.path('data/processed/acquisition/osm_network_source_audit.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
