"""Retain mapped activity areas missing from the point-only destination layer."""
from collections import Counter
import json
from pathlib import Path
import re
import sys
import warnings

import pandas as pd
import pyogrio
from shapely.geometry import box, mapping

import city
import registry
from extract_census_controls import source
from extract_transport_points import decode_hstore

sys.path.insert(0, city.path('build'))
from build_baseline_activities import eligible_purposes

OUTPUT_INPUTS = {
    'data/processed/geospatial/osm_activity_areas.geojson': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/processed/acquisition/raster_tile_selection.json',
        'registry/B_baseline_activities.json'],
    'data/processed/acquisition/osm_activity_areas_audit.json': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/processed/acquisition/raster_tile_selection.json',
        'registry/B_baseline_activities.json'],
}


def main():
    cfg = registry.load()
    record, path = source('osm_western_zone_20260915', 'osm')
    selection = json.loads(Path(city.path('data/processed/acquisition/raster_tile_selection.json')).read_text(encoding='utf-8'))
    bounds = selection['extent_wgs84']
    extent = box(*bounds)
    tag_mapping = cfg.get('B.activities.location_tags')
    keys = sorted({key for criteria in tag_mapping.values() for key in criteria})
    fields = set(pyogrio.read_info(path, layer='multipolygons')['fields'])
    if any(not re.fullmatch('[a-z_]+', key) or key not in fields for key in keys):
        raise ValueError('Activity selector requires a known promoted OGR tag column')
    where = ' OR '.join('"' + key + '" IS NOT NULL' for key in keys)
    print('Reading acquired PBF activity polygons', flush=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        frame = pyogrio.read_dataframe(path, layer='multipolygons', bbox=tuple(bounds), where=where)
    if frame.crs is None or frame.crs.to_epsg() != 4326:
        raise ValueError('Expected WGS84 source polygons')
    features, excluded, counts = [], Counter(), Counter()
    for _, row in frame.iterrows():
        tags = decode_hstore(row.other_tags)
        for key in frame.columns:
            if key in ('geometry', 'other_tags', 'osm_id', 'osm_way_id') or pd.isna(row[key]):
                continue
            value = str(row[key])
            if key in tags and tags[key] != value:
                raise ValueError('Conflicting driver tag: ' + key)
            tags[key] = value
        purposes = eligible_purposes(tags, tag_mapping)
        if not purposes:
            excluded['inactive_or_no_positive_purpose_match'] += 1
            continue
        shape = row.geometry
        if shape is None or shape.is_empty or not shape.is_valid:
            excluded['invalid_or_empty_geometry_not_repaired'] += 1
            continue
        if not shape.intersects(extent):
            excluded['no_actual_extent_intersection'] += 1
            continue
        relation = None if pd.isna(row.osm_id) else str(row.osm_id)
        way = None if pd.isna(row.osm_way_id) else str(row.osm_way_id)
        if (relation is None) == (way is None):
            raise ValueError('Expected exactly one OSM object namespace')
        kind, identity = ('relation', relation) if relation else ('way', way)
        features.append(dict(type='Feature', id=f'{kind}/{identity}', geometry=mapping(shape),
            properties=dict(osm_object_type=kind, osm_object_id=identity, name=tags.get('name', ''),
                purposes=purposes, all_driver_tags=tags, source='mapped_OSM_area_not_capacity_or_entrance',
                source_id='osm_western_zone_20260915', source_sha256=record['sha256'])))
        counts.update(purposes)
    features.sort(key=lambda f: (f['properties']['osm_object_type'], int(f['properties']['osm_object_id'])))
    output = Path(city.path('data/processed/geospatial/osm_activity_areas.geojson'))
    output.write_text(json.dumps(dict(type='FeatureCollection', features=features), ensure_ascii=False,
                                separators=(',', ':')) + '\n', encoding='utf-8')
    audit = dict(source_sha256=record['sha256'], licence='ODbL 1.0; OpenStreetMap contributors',
        source='derived_activity_area_inventory', source_candidates_count=len(frame),
        retained_areas_count=len(features), purpose_counts=dict(counts), excluded=dict(excluded),
        driver_warnings=sorted({str(item.message) for item in caught}),
        limitations=['Mapped areas are not verified current operations, capacity or access entrances.',
                    'Invalid geometry is counted and excluded without silent repair.',
                    'Node/area duplicate identities are not resolved by this inventory.',
                    'Whole valid geometries intersecting the research envelope are retained.'])
    Path(city.path('data/processed/acquisition/osm_activity_areas_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
