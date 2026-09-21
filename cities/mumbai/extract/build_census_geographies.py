"""Join historical census controls to source polygons, retaining every gap.

This is an intermediate population input, not the metropolitan boundary or
current household locations. No observation is apportioned or duplicated.
"""
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

import geopandas as gpd
import pandas as pd
import pyogrio
import shapely

import city
from extract_census_controls import COUNTS, source

OUTPUT_INPUTS = {
    'data/processed/geospatial/census_2011_geographies.gpkg': [
        'data/raw/boundaries/iitb_census_*.zip',
        'data/raw/boundaries/wri_mmr_layer_5_*.json',
        'data/raw/boundaries/wri_mmr_layer_6_*.json',
        'data/processed/observed/census_2011_leaf_controls.csv'],
    'data/processed/geospatial/census_2011_geometry_crosswalk.csv': [
        'data/raw/boundaries/iitb_census_*.zip',
        'data/raw/boundaries/wri_mmr_layer_5_*.json',
        'data/raw/boundaries/wri_mmr_layer_6_*.json',
        'data/processed/observed/census_2011_leaf_controls.csv'],
    'data/processed/acquisition/census_geography_audit.json': [
        'data/raw/boundaries/iitb_census_*.zip',
        'data/raw/boundaries/wri_mmr_layer_5_*.json',
        'data/raw/boundaries/wri_mmr_layer_6_*.json',
        'data/processed/observed/census_2011_leaf_controls.csv'],
}


def normal_name(value):
    """Only case, punctuation and whitespace, never fuzzy name substitution."""
    return re.sub(r'[^a-z0-9]', '', value.lower())


def integer_code(value, width):
    value = str(value)
    if not value.isdecimal() or len(value) > width:
        raise ValueError('Invalid census identifier: ' + value)
    return value.zfill(width)


def normal_place_name(value):
    # Remove explicitly printed census type suffixes, not lexical name parts.
    value = value.split(' WARD NO.')[0]
    value = re.sub(r'\((CT|M Cl|M Corp\.|N\.?V\.?)\)', '', value, flags=re.I)
    return normal_name(value)


def arcgis(layer, records):
    sid = 'wri_mmr_layer_' + str(layer) + '_features'
    record, path = source(sid, 'boundaries')
    id_record, id_path = source('wri_mmr_layer_' + str(layer) + '_ids', 'boundaries')
    records.extend([record, id_record])
    ids = json.loads(id_path.read_text(encoding='utf-8'))
    payload = json.loads(path.read_text(encoding='utf-8'))
    if 'error' in payload or payload.get('exceededTransferLimit'):
        raise ValueError('Incomplete feature query: ' + sid)
    geo = gpd.read_file(path).to_crs(4326)
    oid = ids['objectIdFieldName']
    if geo[oid].duplicated().any() or set(geo[oid]) != set(ids['objectIds']):
        raise ValueError('Feature IDs differ from source inventory: ' + sid)
    return sid, record, geo, oid


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def polygon(geometry, identity, crs, repairs):
    if geometry is None or geometry.is_empty:
        return None, 'missing_source_geometry'
    if geometry.geom_type not in ('Polygon', 'MultiPolygon'):
        raise ValueError('Non-polygon census geometry: ' + identity)
    if geometry.is_valid:
        return geometry, 'source_polygon'
    repaired = shapely.make_valid(geometry, method='linework', keep_collapsed=True)
    if (not repaired.is_valid or repaired.is_empty or
            repaired.geom_type not in ('Polygon', 'MultiPolygon')):
        raise ValueError('Repair requires further interpretation: ' + identity)
    areas = gpd.GeoSeries([geometry, repaired], crs=crs).to_crs(city.crs()).area
    repairs.append(dict(
        source_feature_id=identity, reason=shapely.is_valid_reason(geometry),
        method='GEOS make_valid linework, keep_collapsed=True',
        original_type=geometry.geom_type, repaired_type=repaired.geom_type,
        original_wkb_sha256=hashlib.sha256(geometry.wkb).hexdigest(),
        repaired_wkb_sha256=hashlib.sha256(repaired.wkb).hexdigest(),
        original_area_m2=float(areas.iloc[0]), repaired_area_m2=float(areas.iloc[1]),
        area_change_m2=float(areas.iloc[1] - areas.iloc[0])))
    return repaired, 'repaired_source_polygon'


def main():
    census_path = Path(city.path('data/processed/observed/census_2011_leaf_controls.csv'))
    census = pd.read_csv(census_path, dtype=str, keep_default_na=False)
    if census.geography_id.duplicated().any():
        raise ValueError('Census leaf identifiers are not unique')
    count_columns = list(dict.fromkeys(COUNTS.values()))
    for field in count_columns:
        census[field] = pd.to_numeric(census[field], errors='raise').astype('int64')
    census = census.sort_values('geography_id').set_index('geography_id', drop=False)
    census.index.name = None
    census['ward_join_key'] = (census.state_code + census.district_code +
                               census.subdistrict_code + census.town_village_code + census.ward_code)
    villages = census[census.level == 'VILLAGE'].set_index('town_village_code')
    wards = census[census.level == 'WARD'].set_index('ward_join_key')
    if villages.index.duplicated().any() or wards.index.duplicated().any():
        raise ValueError('Source geography keys are ambiguous')

    geometries = {key: None for key in census.index}
    joins = {key: dict(geography_id=key, geometry_status='no_source_polygon',
                      geometry_source_id='', geometry_source_sha256='',
                      source_feature_ids='', identity_basis='',
                      previous_geometry_source_id='',
                      comparable_count_cells=0, missing_count_cells=0)
             for key in census.index}
    records, repairs, source_audits, seen = [], [], [], set()
    for sid in ('iitb_census_palghar', 'iitb_census_thane', 'iitb_census_raigad'):
        record, path = source(sid, 'boundaries')
        records.append(record)
        with zipfile.ZipFile(path) as archive:
            members = sorted(n for n in archive.namelist() if n.lower().endswith('.shp'))
        if len(members) != 1:
            raise ValueError('Expected one census shapefile: ' + sid)
        geo = pyogrio.read_dataframe('/vsizip/' + path.resolve().as_posix() + '/' + members[0])
        if geo.crs is None:
            raise ValueError('Missing source CRS: ' + sid)
        geo = geo.to_crs(4326)
        # Longer DBF names are truncated and can collide. Only literal,
        # untruncated source names are checked here; no suffix is guessed.
        field_map = {raw.lower(): target for raw, target in COUNTS.items()
                     if len(raw) <= 10 and raw.lower() in geo.columns}
        checks, missing = 0, 0
        for _, row in geo.iterrows():
            code = integer_code(row.census_201, 6)
            if code in seen or code not in villages.index:
                raise ValueError('Duplicate or unknown village code: ' + code)
            seen.add(code)
            control = villages.loc[code]
            for field, target, width in [('state_code', 'state_code', 2),
                                          ('district_c', 'district_code', 3),
                                          ('taluka_cod', 'subdistrict_code', 5)]:
                if integer_code(row[field], width) != control[target]:
                    raise ValueError('Administrative identifier mismatch: ' + code)
            if normal_name(row.village_na) != normal_name(control['name']):
                raise ValueError('Village name mismatch: ' + code)
            observed, blank = 0, 0
            for field, target in field_map.items():
                if pd.isna(row[field]):
                    blank += 1
                elif row[field] == control[target]:
                    observed += 1
                else:
                    raise ValueError('GIS/census count mismatch: ' + code + ' ' + field)
            key = control.geography_id
            geometry, status = polygon(row.geometry, sid + ':' + code, geo.crs, repairs)
            geometries[key] = geometry
            joins[key].update(geometry_status=status, geometry_source_id=sid,
                              geometry_source_sha256=record['sha256'], source_feature_ids=code,
                              identity_basis='Exact administrative codes and normalised name',
                              comparable_count_cells=observed, missing_count_cells=blank)
            checks += observed
            missing += blank
        source_audits.append(dict(source_id=sid, source_sha256=record['sha256'],
                                 features=len(geo), count_field_map=field_map,
                                 exact_count_comparisons=checks, blank_count_cells=missing))
    if seen != set(villages.index):
        raise ValueError('Rural source attributes do not cover every census village')

    sid, record, geo, oid = arcgis(6, records)
    duplicates = []
    for key, group in geo.groupby('C_CODE11', sort=True):
        if key not in wards.index:
            raise ValueError('Unknown ward key: ' + key)
        control = wards.loc[key]
        if any(normal_name(name) != normal_name(control['name']) for name in group.NAME2):
            raise ValueError('Ward name mismatch: ' + key)
        identity = control.geography_id
        feature_ids = ','.join(str(n) for n in sorted(group[oid]))
        joins[identity].update(geometry_source_id=sid, geometry_source_sha256=record['sha256'],
                               source_feature_ids=feature_ids,
                               identity_basis='Exact full census ward key and normalised name')
        if len(group) != 1:
            joins[identity]['geometry_status'] = 'ambiguous_multiple_source_polygons'
            duplicates.append(dict(geography_id=identity, source_feature_ids=feature_ids,
                                   source_name=control['name'], census_persons_count=int(control.persons_count)))
            continue
        geometry, status = polygon(group.geometry.iloc[0], sid + ':' + feature_ids, geo.crs, repairs)
        geometries[identity] = geometry
        joins[identity]['geometry_status'] = status
    source_audits.append(dict(source_id=sid, source_sha256=record['sha256'],
                             features=len(geo), unique_census_keys=int(geo.C_CODE11.nunique()),
                             duplicate_keys=duplicates, count_comparisons=0))

    # A town polygon may stand for a ward only when the source census has
    # exactly one leaf for that complete town key. No multi-ward allocation.
    sid, record, places, place_oid = arcgis(5, records)
    group_fields = ['state_code', 'district_code', 'subdistrict_code', 'town_village_code']
    groups = {key: group for key, group in census.groupby(group_fields, sort=True)}
    duplicate_codes = set(places.loc[places.F2011_ID.duplicated(keep=False), 'F2011_ID'])
    outcomes, rejected, filled = Counter(), [], Counter()
    for _, row in places.sort_values(place_oid).iterrows():
        key = tuple(integer_code(row[field], width) for field, width in
                    [('StateCode', 2), ('DistCode', 3), ('SDistCode', 5), ('F2011_ID', 6)])
        group = groups.get(key)
        if group is None or len(group) != 1:
            outcomes['not_a_single_census_leaf'] += 1
            continue
        control = group.iloc[0]
        identity = control.geography_id
        if joins[identity]['geometry_status'] not in ('missing_source_geometry', 'no_source_polygon'):
            outcomes['existing_geometry_or_ward_ambiguity_preserved'] += 1
            continue
        reason = None
        if row.F2011_ID in duplicate_codes:
            reason = 'duplicate_census_code_in_source'
        elif normal_place_name(row.NAME) != normal_place_name(control['name']):
            reason = 'place_name_conflict'
        if reason:
            outcomes[reason] += 1
            rejected.append(dict(source_feature_id=int(row[place_oid]), geography_id=identity,
                                 source_name=row.NAME, census_name=control['name'], reason=reason))
            continue
        feature_id = str(row[place_oid])
        geometry, status = polygon(row.geometry, sid + ':' + feature_id, places.crs, repairs)
        if geometry is None:
            outcomes['source_polygon_missing'] += 1
            continue
        geometries[identity] = geometry
        joins[identity].update(
            previous_geometry_source_id=joins[identity]['geometry_source_id'],
            geometry_source_id=sid, geometry_source_sha256=record['sha256'],
            source_feature_ids=feature_id, geometry_status=status,
            identity_basis='Exact administrative codes, one census leaf and normalised place name')
        outcomes['geometry_gap_filled'] += 1
        filled[control.level] += 1
    source_audits.append(dict(source_id=sid, source_sha256=record['sha256'], features=len(places),
                             outcomes=dict(sorted(outcomes.items())), filled_by_level=dict(filled),
                             rejected_identity_matches=rejected, count_comparisons=0,
                             name_rule='Case/punctuation/whitespace; remove printed CT, M Cl, M Corp., NV type markers'))

    crosswalk = pd.DataFrame(list(joins.values())).sort_values('geography_id')
    frame = census.drop(columns='ward_join_key').merge(crosswalk, on='geography_id', validate='one_to_one')
    frame = gpd.GeoDataFrame(frame, geometry=[geometries[key] for key in frame.geography_id],
                             crs=4326).to_crs(city.crs())
    nonempty = frame.geometry.notna() & ~frame.geometry.is_empty
    if not frame.loc[nonempty].geometry.is_valid.all():
        raise ValueError('Invalid projected geometry remains')
    # Use one explicit polygon container type so GDAL does not promote a
    # subset implicitly during serialisation. Coordinates remain unchanged.
    frame.geometry = frame.geometry.map(
        lambda geometry: shapely.MultiPolygon([geometry])
        if geometry is not None and geometry.geom_type == 'Polygon' else geometry)
    frame['geometry_area_m2'] = frame.geometry.area
    frame['spatial_status'] = 'Historical source geography; current MMR inclusion unresolved'
    reconciliation = {}
    for district, part in frame.groupby('district_code', sort=True):
        expected = census[census.district_code == district]
        totals = {}
        for field in count_columns:
            actual = int(part[field].sum())
            if actual != int(expected[field].sum()):
                raise ValueError('Population controls changed during geometry join')
            totals[field] = actual
        located = part.geometry.notna()
        reconciliation[district] = dict(
            leaf_records=len(part), records_with_geometry=int(located.sum()),
            persons_with_geometry_count=int(part.loc[located, 'persons_count'].sum()),
            persons_without_geometry_count=int(part.loc[~located, 'persons_count'].sum()),
            preserved_count_totals=totals)

    date = max(datetime.fromisoformat(r['retrieved']) for r in records)
    date = date.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    output = Path(city.path('data/processed/geospatial/census_2011_geographies.gpkg'))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='census_geographies_', dir=output.parent) as work:
        staged = Path(work) / output.name
        previous = pyogrio.get_gdal_config_option('OGR_CURRENT_DATE')
        pyogrio.set_gdal_config_options({'OGR_CURRENT_DATE': date})
        try:
            pyogrio.write_dataframe(frame, staged, layer='census_leaves', driver='GPKG')
            # Keep both duplicate ward geometries for investigation. This layer
            # intentionally has no joined population or synthetic households.
            candidates = geo[[oid, 'C_CODE11', 'NAME2', 'geometry']].sort_values(oid).to_crs(city.crs())
            pyogrio.write_dataframe(candidates, staged, layer='ward_source_candidates', driver='GPKG')
        finally:
            pyogrio.set_gdal_config_options({'OGR_CURRENT_DATE': previous})
        restored = pyogrio.read_dataframe(staged, layer='census_leaves')
        if (restored.geography_id.tolist() != frame.geography_id.tolist() or
                not restored[count_columns].equals(frame[count_columns]) or
                not restored.geometry.to_wkb().equals(frame.geometry.to_wkb())):
            raise ValueError('Written census layer failed its round-trip check')
        os.replace(staged, output)
    crosswalk.to_csv(city.path('data/processed/geospatial/census_2011_geometry_crosswalk.csv'),
                     index=False, lineterminator='\n')
    audit = dict(
        source='derived', status='historical_geographies_with_explicit_gaps',
        census_controls_sha256=digest(census_path), census_records=len(frame),
        geometry_status_counts=dict(sorted(Counter(frame.geometry_status).items())),
        sources=source_audits, repairs=repairs, district_reconciliation=reconciliation,
        count_columns_preserved=count_columns, container_timestamp_from_acquisition=date,
        projected_crs=str(frame.crs), shapely_version=shapely.__version__,
        geos_version=shapely.geos_version_string, gdal_version=pyogrio.__gdal_version_string__,
        limitations=[
            'Every source census leaf remains once, including null and ambiguous geometry.',
            'Matched attributes do not independently verify polygon boundaries or current residential locations.',
            'The four source districts exceed the provisional metropolitan research extent.',
            'Historical controls have not been projected to the model year or converted into households.',
            'No population is spread over duplicate ward polygons or substituted with a centroid.',
            'Other towns need ward geometry or an explicit audited allocation within town boundaries.',
            'Cross-polygon topology, historical boundary accuracy and legal MMR inclusion remain unresolved.',
            'Long truncated DBF count names are not inferred. Blank GIS counts are not zero.',
            'Source geometry reuse terms remain unverified. This is not an OSM-derived layer.'])
    Path(city.path('data/processed/acquisition/census_geography_audit.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(census_records=len(frame), geometry_status_counts=audit['geometry_status_counts'],
                         repaired_polygons=len(repairs), preserved_count_columns=len(count_columns))))


if __name__ == '__main__':
    main()
