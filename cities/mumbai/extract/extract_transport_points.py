"""Preserve mapped transport-point tags and coordinates for source matching.

No fuzzy station joins, mode inference, merging of entrances or operating-status
assumptions are made. Polygon-only stations are outside this point inventory.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import pandas as pd
import pyogrio
from pyproj import Transformer
import city
from extract_census_controls import write

OUTPUT_INPUTS = {
    'data/processed/observed/osm_transport_points.csv': ['data/processed/geospatial/osm_research.gpkg'],
    'data/processed/observed/_transport_points_audit.json': ['data/processed/geospatial/osm_research.gpkg'],
}


def decode_hstore(value):
    if pd.isna(value):
        return {}
    pattern = r'"((?:[^"\\]|\\.)*)"=>"((?:[^"\\]|\\.)*)"'
    result, position = {}, 0
    for match in re.finditer(pattern,value):
        if value[position:match.start()] != (',' if position else ''):
            raise ValueError('Unparsed OGR tag text')
        # OGR hstore can contain literal newlines in quoted OSM tag values.
        # Preserve them; JSON's strict control-character rule is not hstore's.
        key,val = (json.loads('"'+v+'"',strict=False) for v in match.groups())
        if key in result:
            raise ValueError('Duplicate OGR tag key')
        result[key] = val
        position = match.end()
    if position != len(value):
        raise ValueError('Unparsed trailing OGR tag text')
    return result


def main():
    path = Path(city.path('data/processed/geospatial/osm_research.gpkg'))
    descriptor = json.loads(Path(city.path('city.json')).read_text(encoding='utf-8'))
    epsg = descriptor['crs']['epsg']
    transformer = Transformer.from_crs(4326,epsg,always_xy=True)
    frame = pyogrio.read_dataframe(path,layer='points')
    rows, counts = [], Counter()
    for _,row in frame.iterrows():
        tags = decode_hstore(row['other_tags'])
        for field in frame.columns:
            if field in ('geometry','other_tags','osm_id') or pd.isna(row[field]):
                continue
            if field in tags and tags[field]!=str(row[field]):
                raise ValueError('Conflicting driver-exposed tag')
            tags[field] = str(row[field])
        selected = {}
        for key in ('railway','public_transport'):
            if key in tags:
                selected[key]=tags[key]
        if tags.get('amenity') in ('bus_station','ferry_terminal','taxi','bicycle_rental','bicycle_parking'):
            selected['amenity']=tags['amenity']
        if tags.get('highway') in ('bus_stop','traffic_signals','crossing'):
            selected['highway']=tags['highway']
        if not selected:
            continue
        lon,lat = row.geometry.x,row.geometry.y
        x,y = transformer.transform(lon,lat)
        rows.append(dict(osm_node_id=row['osm_id'],name=tags.get('name',''),
                         longitude_deg=lon,latitude_deg=lat,x_m=x,y_m=y,projected_epsg=epsg,
                         selected_tags_json=json.dumps(selected,ensure_ascii=False,sort_keys=True),
                         all_driver_tags_json=json.dumps(tags,ensure_ascii=False,sort_keys=True),
                         source='mapped_osm_feature',status='unverified_operation_and_station_identity'))
        counts.update(key+'='+value for key,value in selected.items())
    if not rows:
        raise ValueError('No mapped transport points')
    rows.sort(key=lambda row:int(row['osm_node_id']))
    write('osm_transport_points.csv',rows)
    with path.open('rb') as stream:
        sha = hashlib.file_digest(stream,'sha256').hexdigest()
    audit = dict(input_sha256=sha,point_features=len(rows),selected_tag_counts=dict(sorted(counts.items())),
                 unnamed_features=sum(not row['name'] for row in rows),
                 limitations=['Tag counts overlap: one node may carry multiple selected tags.',
                              'Geography is a research envelope, not the notified metropolitan boundary.',
                              'This excludes polygon-only stations, relation-only stops and unmapped facilities.',
                              'Names and refs need validated joins to operator station identifiers.',
                              'Mapped point locations do not prove current operations, accessibility or capacity.'])
    Path(city.path('data/processed/observed/_transport_points_audit.json')).write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit))


if __name__=='__main__':
    main()
