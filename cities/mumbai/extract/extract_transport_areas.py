"""Preserve OSM transport areas omitted by the point/line research inventory.

Area geometry is not a boarding point, platform link or operating-status claim.
Ways and relations have separate ID namespaces. No geometry is repaired or
clipped, and all driver-exposed tags remain available for subsequent matching.
"""
from collections import Counter
import json
from pathlib import Path
import warnings

import pandas as pd
import pyogrio
from shapely.geometry import box, mapping
import city
from extract_census_controls import source
from extract_transport_points import decode_hstore

OUTPUT_INPUTS = {
    'data/processed/geospatial/osm_transport_areas.geojson': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/processed/acquisition/raster_tile_selection.json'],
    'data/processed/acquisition/osm_transport_areas_audit.json': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/processed/acquisition/raster_tile_selection.json'],
}

AMENITIES = ('bus_station', 'ferry_terminal', 'taxi', 'bicycle_rental', 'bicycle_parking')
AEROWAYS = ('aerodrome', 'terminal', 'helipad')


def main():
    record, path = source('osm_western_zone_20260915', 'osm')
    selection = json.loads(Path(city.path('data/processed/acquisition/raster_tile_selection.json')).read_text(encoding='utf-8'))
    bounds = selection['extent_wgs84']
    if len(bounds) != 4 or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError('Invalid source-derived research envelope')
    extent = box(*bounds)
    # These are source-tag categories, not simulated mode classifications.
    where = ('other_tags LIKE \'%"railway"=>%\' OR other_tags LIKE \'%"public_transport"=>%\' '
             "OR amenity IN (" + ','.join("'"+v+"'" for v in AMENITIES) + ') '
             "OR aeroway IN (" + ','.join("'"+v+"'" for v in AEROWAYS) + ')')
    print('READING transport multipolygons from acquired PBF', flush=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        frame = pyogrio.read_dataframe(path, layer='multipolygons', where=where, bbox=tuple(bounds))
    driver_warnings = sorted({str(item.message) for item in caught})
    if frame.crs is None or frame.crs.to_epsg() != 4326:
        raise ValueError('Expected WGS84 source geometry')
    features, excluded, issues, counts = [], Counter(), Counter(), Counter()
    for _, row in frame.iterrows():
        tags = decode_hstore(row['other_tags'])
        for name in frame.columns:
            if name in ('geometry', 'other_tags', 'osm_id', 'osm_way_id') or pd.isna(row[name]):
                continue
            value = str(row[name])
            if name in tags and tags[name] != value:
                raise ValueError('Conflicting driver-exposed tag: ' + name)
            tags[name] = value
        selected = {key: tags[key] for key in ('railway', 'public_transport') if key in tags}
        if tags.get('amenity') in AMENITIES:
            selected['amenity'] = tags['amenity']
        if tags.get('aeroway') in AEROWAYS:
            selected['aeroway'] = tags['aeroway']
        if not selected:
            excluded['no_selected_transport_tag'] += 1
            continue
        relation = None if pd.isna(row['osm_id']) else str(row['osm_id'])
        way = None if pd.isna(row['osm_way_id']) else str(row['osm_way_id'])
        if (relation is None) == (way is None):
            raise ValueError('An area must identify exactly one OSM way or relation')
        object_type, object_id = ('relation', relation) if relation else ('way', way)
        if not object_id.isdigit():
            raise ValueError('Invalid OSM object ID')
        geometry = row.geometry
        if geometry is None or geometry.is_empty:
            geometry_status, intersection = 'empty_or_missing', 'unchecked'
            issues[geometry_status] += 1
        elif not geometry.is_valid:
            geometry_status, intersection = 'invalid_unrepaired', 'unchecked'
            issues[geometry_status] += 1
        else:
            geometry_status = 'valid'
            if not geometry.intersects(extent):
                excluded['no_actual_extent_intersection'] += 1
                continue
            intersection = 'intersects_research_envelope'
        key = object_type + '/' + object_id
        features.append(dict(type='Feature', id=key,
                             geometry=mapping(geometry) if geometry is not None else None,
                             properties=dict(osm_object_type=object_type, osm_object_id=object_id,
                                             name=tags.get('name', ''), all_driver_tags=tags,
                                             selected_tags=selected, geometry_status=geometry_status,
                                             extent_intersection_status=intersection,
                                             source='mapped_osm_feature', source_id='osm_western_zone_20260915',
                                             source_sha256=record['sha256'],
                                             status='unverified_operation_and_station_identity',
                                             boarding_coordinate_status='not_derived_from_area')))
        counts.update(key+'='+value for key, value in selected.items())
    features.sort(key=lambda f: (f['properties']['osm_object_type'], int(f['properties']['osm_object_id'])))
    if not features or len({f['id'] for f in features}) != len(features):
        raise ValueError('Missing transport areas or duplicate OSM object identity')
    output = Path(city.path('data/processed/geospatial/osm_transport_areas.geojson'))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(type='FeatureCollection', features=features), ensure_ascii=False,
                                 sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8', newline='\n')
    audit = dict(source_id='osm_western_zone_20260915', source_sha256=record['sha256'],
                 source_layer='multipolygons', research_extent_wgs84=bounds, coordinate_crs='EPSG:4326',
                 driver_candidates=len(frame), retained_features=len(features),
                 object_type_counts=dict(sorted(Counter(f['properties']['osm_object_type'] for f in features).items())),
                 selected_tag_counts=dict(sorted(counts.items())), excluded=dict(sorted(excluded.items())),
                 geometry_issues=dict(sorted(issues.items())), driver_warnings=driver_warnings,
                 limitations=[
                     'Research overcoverage is not a notified administrative or simulation boundary.',
                     'Source-tag classes do not establish operational mode, status, capacity or station identity.',
                     'Station areas may overlap station points; neither may be counted as a separate station without reconciliation.',
                     'Area geometry is not a boarding coordinate, platform, entrance or network attachment.',
                     'Invalid geometry is retained without repair and excluded from confident spatial interpretation.',
                     'OGR exposes assembled area geometry, not its original member roles; the native OSM source remains authoritative.',
                 ])
    Path(city.path('data/processed/acquisition/osm_transport_areas_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('limitations', 'driver_warnings')}))


if __name__ == '__main__':
    main()
