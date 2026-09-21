"""Audit acquired spatial-support containers and raster metadata.

This checks acquisition integrity and coverage metadata, not the accuracy of
population, built-form or elevation estimates. No model extent is assumed.
"""
import hashlib
import json
from pathlib import Path
import zipfile

import rasterio
from rasterio.warp import transform_bounds
import city

OUTPUT_INPUTS = {
    'data/processed/acquisition/raster_source_audit.json': [
        'data/processed/acquisition/raster_tile_selection.json',
        'data/raw/geospatial/ghs_*.zip',
        'data/raw/geospatial/copernicus_dsm_*.tif'],
}


def main():
    selection = json.loads(Path(city.path('data/processed/acquisition/raster_tile_selection.json')).read_text(encoding='utf-8'))
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    entries = {r['id']: r for r in catalogue['sources']}
    acquired, missing = [], []
    for sid in selection['selected_source_ids']:
        entry = entries[sid]
        provenance = Path(city.path('data/raw', entry['category'], 'provenance_'+sid+'.json'))
        if not provenance.exists():
            missing.append(sid)
            continue
        record = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
        path = Path(city.path(record['path']))
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                raise ValueError('Acquired file hash mismatch: '+sid)
        crc = None
        if path.suffix == '.zip':
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise ValueError('ZIP CRC mismatch: '+sid)
                members = [m for m in archive.namelist() if m.lower().endswith(('.tif', '.tiff'))]
                if not members:
                    raise ValueError('No TIFF in raster ZIP: '+sid)
            crc = True
            datasets = [('/vsizip/'+path.as_posix()+'/'+m, m) for m in members]
        else:
            datasets = [(str(path), path.name)]
        layers = []
        for location, member in datasets:
            with rasterio.open(location) as raster:
                if raster.crs is None or raster.count < 1 or min(raster.shape) < 1:
                    raise ValueError('Missing raster CRS or grid: '+sid)
                extent = transform_bounds(raster.crs, 'EPSG:4326', *raster.bounds, densify_pts=21)
                layers.append(dict(member=member, crs=raster.crs.to_string(),
                                   width=raster.width, height=raster.height, bands=raster.count,
                                   dtypes=list(raster.dtypes), nodata=raster.nodata,
                                   bounds_native=list(raster.bounds), bounds_wgs84=list(extent),
                                   pixel_size_native=list(raster.res), units=list(raster.units),
                                   scales=list(raster.scales), offsets=list(raster.offsets)))
        acquired.append(dict(source_id=sid, sha256=record['sha256'], bytes=record['bytes'],
                             zip_crc_verified=crc, layers=layers))
    result = dict(selected_sources=len(selection['selected_source_ids']), acquired_sources=len(acquired),
                  missing_source_ids=missing, sources=acquired,
                  acquisition_complete=not missing,
                  limitations=[
                      'Metadata and container audit only; pixel values are not validated observations.',
                      'Missing DEM tiles are not filled with zero elevation.',
                      'Copernicus DEM is a digital surface model, not bare-earth road elevation.',
                      'GHSL estimates need independent demographic controls and uncertainty assessment.',
                      'Research envelope overcovers the intended city; whole-tile totals are not city totals.',
                      'Product units must be read from the product documentation when TIFF units are absent.'])
    Path(city.path('data/processed/acquisition/raster_source_audit.json')).write_text(
        json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='sources'}, indent=2))


if __name__ == '__main__':
    main()
