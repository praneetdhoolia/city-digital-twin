"""Extract spatial evidence from PBF within a source-derived research envelope.

These OGR layers preserve source tags and OSM IDs but are not a routing graph:
way-node references and restriction relations require the native OSM pipeline.
The envelope overcovers the provisional region and is not a legal boundary.
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile

import pyogrio
from shapely.geometry import box
import city
from extract_census_controls import source

OUTPUT_INPUTS = {
    'data/processed/geospatial/osm_research.gpkg': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/raw/osm/provenance_osm_western_zone_*.json',
        'data/processed/acquisition/raster_tile_selection.json'],
    'data/processed/acquisition/osm_research_audit.json': [
        'data/raw/osm/osm_western_zone_*.osm.pbf',
        'data/raw/osm/provenance_osm_western_zone_*.json',
        'data/processed/acquisition/raster_tile_selection.json'],
}


def main():
    record,path = source('osm_western_zone_20260915','osm')
    source_date = datetime.fromisoformat(record['retrieved']).isoformat(timespec='milliseconds').replace('+00:00','Z')
    selection_path = Path(city.path('data/processed/acquisition/raster_tile_selection.json'))
    selection = json.loads(selection_path.read_text(encoding='utf-8'))
    bounds = selection['extent_wgs84']
    if len(bounds)!=4 or bounds[0]>=bounds[2] or bounds[1]>=bounds[3]:
        raise ValueError('Invalid source-derived research envelope')
    output = Path(city.path('data/processed/geospatial/osm_research.gpkg'))
    output.parent.mkdir(parents=True,exist_ok=True)
    layers = []
    with tempfile.TemporaryDirectory(prefix='osm_research_',dir=output.parent) as work:
        staged = Path(work)/output.name
        for layer in ('points','lines','multilinestrings'):
            print('READING',layer,flush=True)
            frame = pyogrio.read_dataframe(path,layer=layer,bbox=tuple(bounds))
            if frame.empty or frame.crs is None or frame.crs.to_epsg()!=4326:
                raise ValueError('Missing expected OSM evidence or WGS84 CRS')
            candidates = len(frame)
            # Some OGR drivers apply an envelope-only spatial filter. Require
            # the actual geometry to intersect, retaining complete geometry.
            frame = frame[frame.geometry.intersects(box(*bounds))].copy()
            if frame.empty:
                raise ValueError('No intersecting OSM geometry')
            ids = frame['osm_id'].astype(str)
            if ids.duplicated().any():
                raise ValueError('Duplicate OSM IDs in a layer')
            fields = {str(k):int(frame[k].notna().sum()) for k in frame.columns if k!='geometry'}
            layers.append(dict(layer=layer,features=len(frame),envelope_candidates=candidates,
                               rejected_nonintersecting_geometries=candidates-len(frame),fields_populated=fields,
                               invalid_geometries=int((~frame.geometry.is_valid).sum()),
                               empty_geometries=int(frame.geometry.is_empty.sum()),
                               geometry_bounds_wgs84=[float(v) for v in frame.total_bounds],
                               source_fields=list(fields)))
            # GDAL otherwise stamps the build's wall clock into gpkg_contents.
            # The immutable acquisition date fixes container metadata without
            # inventing an observation date for any mapped feature.
            previous_date = pyogrio.get_gdal_config_option('OGR_CURRENT_DATE')
            pyogrio.set_gdal_config_options({'OGR_CURRENT_DATE':source_date})
            try:
                pyogrio.write_dataframe(frame,staged,layer=layer,driver='GPKG')
            finally:
                pyogrio.set_gdal_config_options({'OGR_CURRENT_DATE':previous_date})
            print('EXTRACTED',layer,len(frame),flush=True)
        os.replace(staged,output)
    audit = dict(source_sha256=record['sha256'],selection_sha256=hashlib.sha256(selection_path.read_bytes()).hexdigest(),
                 research_envelope_wgs84=bounds,gdal_version=pyogrio.__gdal_version_string__,layers=layers,
                 container_timestamp_from_immutable_acquisition=source_date,
                 licence='ODbL 1.0; OpenStreetMap contributors',status='spatial_evidence_not_model_network',
                 limitations=['Envelope derives from district datasets and is not the notified metropolitan boundary.',
                              'Features intersecting the envelope retain their complete source geometry.',
                              'OGR attributes do not retain complete way-node references or restriction relations.',
                              'Tags describe mapped features, not verified current operations or capacity.',
                              'No silent geometry repair, connectivity inference or modal permission assignment.'])
    Path(city.path('data/processed/acquisition/osm_research_audit.json')).write_text(
        json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit))


if __name__=='__main__':
    main()
