"""Select public spatial-support tiles from source-derived district extents.

This deliberately overcovers the research area. It does not select a legal
simulation boundary, clip data or assign population to the model.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

import pyogrio
from pyproj import Transformer
from shapely.geometry import box

import city
from extract_census_controls import source

OUTPUT_INPUTS = {
    'data/processed/acquisition/raster_tile_selection.json': [
        'data/processed/acquisition/boundary_source_audit.json',
        'data/raw/geospatial/ghsl_tile_grid_*.zip',
        'data/raw/geospatial/cop_dem_tile_list_*.txt'],
}

PRODUCTS = [
    ('GHS_POP_GLOBE_R2023A', f'GHS_POP_E{epoch}_GLOBE_R2023A_54009_100')
    for epoch in (2020,2025)
] + [
    (f'GHS_BUILT_{kind}_GLOBE_R2023A', f'GHS_BUILT_{kind}{component}_E{epoch}_GLOBE_R2023A_54009_100')
    for kind in ('S','V') for component in ('','_NRES') for epoch in (2020,2025)
] + [('GHS_BUILT_H_GLOBE_R2023A', f'GHS_BUILT_H_{kind}_E2018_GLOBE_R2023A_54009_100') for kind in ('AGBH','ANBH')]


def main():
    if Path(city.path()).resolve()!=Path(__file__).resolve().parents[1]:
        raise ValueError('Select the city that owns this script')
    audit_path=Path(city.path('data/processed/acquisition/boundary_source_audit.json'))
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    administrative=[s for s in audit['sources'] if s['source_id'].startswith('iitb_boundary_')]
    extents=[l['extent_wgs84_from_dataset'] for s in administrative for l in s['layers']]
    if not extents or any(not e or len(e)!=4 or not all(math.isfinite(x) for x in e) for e in extents):
        raise ValueError('Missing valid source extents')
    bounds=[min(e[0] for e in extents), min(e[1] for e in extents), max(e[2] for e in extents), max(e[3] for e in extents)]
    grid_record,grid_path=source('ghsl_tile_grid','geospatial')
    with zipfile.ZipFile(grid_path) as archive:
        members=[n for n in archive.namelist() if n.endswith('.shp')]
    if len(members)!=1:
        raise ValueError('Expected one published grid')
    grid=pyogrio.read_dataframe('/vsizip/'+grid_path.as_posix()+'/'+members[0])
    # Project only the small research envelope. Projecting the entire global
    # grid can create invalid wrap-around polygons near the Mollweide rim.
    envelope=Transformer.from_crs(4326,grid.crs,always_xy=True).transform_bounds(*bounds,densify_pts=21)
    selected=grid[grid.intersects(box(*envelope))]
    if selected.empty or not selected.geometry.is_valid.all():
        raise ValueError('Invalid selected raster grid')
    tiles=sorted(selected['tile_id'].tolist())
    entries=[]
    for family,product in PRODUCTS:
        for tile in tiles:
            name=f'{product}_V1_0_{tile}.zip'
            entries.append(dict(id=name[:-4].lower(),
                                url=f'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/{family}/{product}/V1-0/tiles/{name}',
                                title=product+' '+tile,format='zip',category='geospatial',
                                licence='CC-BY 4.0 (GHSL; product and methodological citation required)',
                                coverage='Source-derived research envelope; modelled population/building layers, not current direct observations or a legal study boundary.'))
    dem_record,dem_path=source('cop_dem_tile_list','geospatial')
    dem_tiles=[]
    for tile in dem_path.read_text(encoding='utf-8').splitlines():
        match=re.fullmatch(r'Copernicus_DSM_COG_10_([NS])(\d+)_00_([EW])(\d+)_00_DEM',tile)
        if not match:
            raise ValueError('Unrecognised published DSM tile name')
        ns,lat,ew,lon=match.groups()
        y=int(lat)*(1 if ns=='N' else -1);x=int(lon)*(1 if ew=='E' else -1)
        if x < bounds[2] and x+1 > bounds[0] and y < bounds[3] and y+1 > bounds[1]:
            dem_tiles.append(tile)
            entries.append(dict(id=tile.lower(),url=f'https://copernicus-dem-30m.s3.amazonaws.com/{tile}/{tile}.tif',
                                title='Copernicus GLO30 public DSM '+tile,format='tif',category='geospatial',
                                licence='Copernicus DEM free licence; prescribed attribution and product terms apply',
                                coverage='DSM including buildings and vegetation; historical acquisition. Must not be used as surveyed road, bridge or tunnel elevation.'))
    catalogue_path=Path(__file__).with_name('sources.json')
    catalogue=json.loads(catalogue_path.read_text(encoding='utf-8'))
    existing={e['id']:e for e in catalogue['sources']}
    for entry in entries:
        if entry['id'] in existing:
            if existing[entry['id']]['url']!=entry['url']:
                raise ValueError('Catalogue identity changed')
        else:
            catalogue['sources'].append(entry)
    catalogue_path.write_text(json.dumps(catalogue,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    selection=dict(schema_version=1,source='derived',purpose='Acquisition overcoverage, not a simulation boundary',
                   source_administrative_extents=[dict(source_id=s['source_id'],sha256=s['source_sha256']) for s in administrative],
                   boundary_audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
                   extent_wgs84=bounds,ghsl_grid_sha256=grid_record['sha256'],ghsl_tiles=tiles,
                   dem_tile_list_sha256=dem_record['sha256'],dem_tiles=dem_tiles,
                   selected_source_ids=[e['id'] for e in entries],
                   limitations=['Whole historical administrative extents overcover MMR.',
                                'Projected-envelope tile intersection is conservative and does not repair source boundary polygons.',
                                'No population or elevation value has been assigned to a simulation.'])
    Path(city.path('data/processed/acquisition/raster_tile_selection.json')).write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(selection))


if __name__=='__main__':
    main()
