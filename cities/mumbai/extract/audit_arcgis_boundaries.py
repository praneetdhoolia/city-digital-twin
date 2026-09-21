"""Check public GIS downloads, census joins and source inconsistencies."""
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import city

OUTPUT_INPUTS = {
    'data/processed/acquisition/arcgis_boundary_audit.json': [
        'data/raw/boundaries/wri_mmr_*.json',
        'data/processed/observed/census_2011_leaf_controls.csv'],
}


def read(source_id):
    record = json.loads(Path(city.path('data/raw/boundaries', 'provenance_'+source_id+'.json')).read_text(encoding='utf-8'))['files'][0]
    path = Path(city.path(record['path']))
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
            raise ValueError('Source hash mismatch: '+source_id)
    payload = json.loads(path.read_text(encoding='utf-8'))
    if 'error' in payload:
        raise ValueError('API returned an error: '+source_id)
    return payload, path, record


def main():
    service, _, _ = read('wri_mmr_service')
    census = pd.read_csv(city.path('data/processed/observed/census_2011_leaf_controls.csv'), dtype=str)
    census['ward_join_key'] = (census.state_code+census.district_code+census.subdistrict_code+
                               census.town_village_code+census.ward_code)
    rows = []
    for layer in service['layers']:
        prefix = 'wri_mmr_layer_'+str(layer['id'])
        metadata, _, _ = read(prefix+'_metadata')
        ids, _, _ = read(prefix+'_ids')
        payload, path, record = read(prefix+'_features')
        expected = set(ids['objectIds'])
        oid = ids['objectIdFieldName']
        actual = [feature['attributes'][oid] for feature in payload['features']]
        if payload.get('exceededTransferLimit') or set(actual) != expected or len(actual) != len(expected):
            raise ValueError('Incomplete or duplicated feature query: '+prefix)
        geo = gpd.read_file(path)
        missing = geo.geometry.isna() | geo.geometry.is_empty
        invalid = ~missing & ~geo.geometry.is_valid
        row = dict(source_id=prefix+'_features', source_sha256=record['sha256'],
                   layer_name=metadata['name'], feature_count=len(geo), query_ids_complete=True,
                   crs=str(geo.crs), missing_geometry_count=int(missing.sum()),
                   invalid_geometry_count=int(invalid.sum()),
                   extent_wgs84=geo.to_crs(4326).total_bounds.tolist(),
                   feature_area_sum_km2=float(geo.to_crs(city.descriptor()['crs']['epsg']).area.sum()/1e6)
                   if metadata['geometryType']=='esriGeometryPolygon' else None)
        if 'SUB_DIST' in geo:
            row['subdistrict_names'] = sorted(geo.SUB_DIST.dropna().unique().tolist())
        for field, targets in [('F2011_ID', set(census.town_village_code)),
                               ('C_CODE11', set(census.loc[census.level=='WARD','ward_join_key']))]:
            if field not in geo:
                continue
            keys = geo[field].astype(str)
            duplicates = geo.loc[keys.duplicated(keep=False)]
            row['census_join'] = dict(field=field, matched_feature_count=int(keys.isin(targets).sum()),
                                     unique_key_count=int(keys.nunique()),
                                     unmatched_keys=sorted(set(keys)-targets),
                                     duplicate_key_features=json.loads(duplicates.drop(columns='geometry').to_json(orient='records')),
                                     status='candidate_join_only_no_population_assigned')
        rows.append(row)
    result = dict(schema_version=1, source='derived', status='evidence_only', layers=rows,
                  limitations=[
                      'Item publication in 2020 does not establish the boundary vintage.',
                      'The source taluka layer omits Palghar. This is not the complete 2019 notified extent.',
                      'Web Mercator Shape__Area values are not local metric areas. Audit areas use the city projected CRS.',
                      'Duplicate census codes sometimes have different names or talukas. Do not join populations by code alone.',
                      'Matched codes do not establish correct geometry or present-day administrative boundaries.',
                      'No polygons were repaired, dissolved, clipped or substituted for the legal MMR boundary.'])
    output = Path(city.path('data/processed/acquisition/arcgis_boundary_audit.json'))
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'layers':len(rows),'features':sum(r['feature_count'] for r in rows),
                      'invalid_geometries':sum(r['invalid_geometry_count'] for r in rows)}))


if __name__ == '__main__':
    main()
