"""Extract operator station geometry and retain incomplete access information."""
import csv
import hashlib
import json
import math
from pathlib import Path

import city

OUTPUT_INPUTS = {
    'data/processed/observed/metro3_stations.csv': ['data/raw/transit/mmrcl_all_stations_*.json', 'data/raw/transit/mmrcl_station_*.json'],
    'data/processed/observed/metro3_gates.csv': ['data/raw/transit/mmrcl_station_*.json'],
    'data/processed/observed/metro3_neighbours.csv': ['data/raw/transit/mmrcl_station_*.json'],
    'data/processed/observed/_metro3_station_audit.json': ['data/raw/transit/mmrcl_all_stations_*.json', 'data/raw/transit/mmrcl_station_*.json'],
}


def read(source_id):
    record = json.loads(Path(city.path('data/raw/transit/provenance_'+source_id+'.json')).read_text(encoding='utf-8'))['files'][0]
    path = Path(city.path(record['path']))
    with path.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=record['sha256']:
            raise ValueError('Source hash mismatch: '+source_id)
    return json.loads(path.read_text(encoding='utf-8')), record


def coordinate(value, limit):
    if value in (None, ''):
        return None
    number=float(value)
    if not math.isfinite(number) or abs(number)>limit:
        raise ValueError('Invalid coordinate: '+repr(value))
    return number


def write(name, rows):
    with Path(city.path('data/processed/observed',name)).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def main():
    directory, _=read('mmrcl_all_stations')
    known={s['code'] for s in directory}
    if len(known)!=len(directory):
        raise ValueError('Duplicate station code in operator directory')
    stations,gates,neighbours=[],[],[]
    missing_times,conflicts=[],[]
    for listed in sorted(directory,key=lambda s:s['code']):
        sid='mmrcl_station_'+listed['code'].lower()
        detail,record=read(sid)
        if detail['code']!=listed['code'] or detail['id']!=listed['id']:
            raise ValueError('Directory/detail identity mismatch: '+sid)
        stations.append(dict(station_code=detail['code'],afc_station_code=detail['afc_station_code'],
                             station_name=detail['name'],latitude_deg=coordinate(detail['latitude'],90),
                             longitude_deg=coordinate(detail['longitude'],180),source_type_label=detail['type'],
                             interchange_declared=detail['interchange'],source='observed',source_id=sid,
                             source_sha256=record['sha256']))
        if detail['type'].lower()=='elevated' and 'at-grade' in detail.get('description','').lower():
            conflicts.append(dict(station_code=detail['code'],field='type',
                                  conflict='Type says elevated; description says at-grade. Preserve both in raw data.'))
        if not any(values for item in detail.get('first_last_train',[]) for values in item.values()):
            missing_times.append(detail['code'])
        for ordinal,gate in enumerate(detail.get('gates',[]),start=1):
            try:
                latitude=coordinate(gate.get('gate_latitude'),90)
                longitude=coordinate(gate.get('gate_longitude'),180)
                coordinate_status='missing' if latitude is None or longitude is None else 'range_checked_only'
            except ValueError:
                latitude,longitude=None,None
                coordinate_status='invalid_degrees_or_undeclared_projected_crs'
                conflicts.append(dict(station_code=detail['code'],field='gate_coordinates',
                                      gate=gate['gate_name'],conflict='Published latitude/longitude fields exceed degree ranges. CRS unresolved.'))
            gates.append(dict(station_code=detail['code'],source_gate_ordinal=ordinal,gate_name=gate['gate_name'],
                              gate_code=gate.get('gate_code'),latitude_deg=latitude,longitude_deg=longitude,
                              source_gate_latitude=gate.get('gate_latitude'),source_gate_longitude=gate.get('gate_longitude'),
                              coordinate_status=coordinate_status,
                              source_status=gate.get('status'),divyang_friendly_declared=gate.get('divyang_friendly'),
                              source='observed',source_id=sid,source_sha256=record['sha256']))
        for group in detail['prev_next_stations']:
            for line_name,entries in group.items():
                for entry in entries:
                    for direction in ('prev_station','next_station'):
                        target=entry.get(direction)
                        if target:
                            if target['code'] not in known:
                                raise ValueError('Unknown neighbouring station: '+target['code'])
                            neighbours.append(dict(station_code=detail['code'],neighbour_code=target['code'],
                                                   direction=direction,line_name=line_name,source='observed',
                                                   source_id=sid,source_sha256=record['sha256']))
    edges={(r['station_code'],r['neighbour_code'],r['direction']) for r in neighbours}
    for a,b,direction in edges:
        reverse='prev_station' if direction=='next_station' else 'next_station'
        if (b,a,reverse) not in edges:
            conflicts.append(dict(station_code=a,field='neighbours',conflict='Nonreciprocal '+direction+' to '+b))
    forward={a:b for a,b,d in edges if d=='next_station'}
    starts=known-set(forward.values())
    chains=[]
    for start in sorted(starts):
        chain=[]
        current=start
        while current not in chain:
            chain.append(current)
            if current not in forward:
                break
            current=forward[current]
        chains.append(chain)
    chain_complete=len(chains)==1 and set(chains[0])==known
    if not chain_complete:
        conflicts.append(dict(field='neighbour_chain',conflict='Published neighbour graph is disconnected or incomplete; no missing link inferred.'))
    Path(city.path('data/processed/observed')).mkdir(parents=True,exist_ok=True)
    write('metro3_stations.csv',stations);write('metro3_gates.csv',gates);write('metro3_neighbours.csv',neighbours)
    result=dict(schema_version=1,source='derived',status='evidence_only',station_count=len(stations),gate_count=len(gates),
                gate_count_missing_coordinates=sum(r['latitude_deg'] is None or r['longitude_deg'] is None for r in gates),
                directed_neighbour_count=len(neighbours),station_chains=chains,complete_station_chain=chain_complete,
                stations_without_first_last_times=sorted(missing_times),source_conflicts=conflicts,
                limitations=['Published station coordinates are points, not validated entrance or platform geometry.',
                             'Schematic x/y fields are not geographical coordinates and are excluded.',
                             'Null entrance coordinates remain null; station centroids cannot substitute for entrances.',
                             'API lift status and estimated nearby-place walking times are not field measurements.',
                             'Observed means published by the operator; contradictions remain flagged for review.'])
    Path(city.path('data/processed/observed/_metro3_station_audit.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    main()
