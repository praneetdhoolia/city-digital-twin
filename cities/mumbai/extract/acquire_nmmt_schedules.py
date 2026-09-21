"""Acquire all route timetables, optionally followed by all published trip details.

Only the public passenger-information queries observed in the operator website
are called. Each family of queries is one harvest (see harvest.py): the route
timetables are the members of one archive, the trip stop timetables of another.
Responses remain immutable and are independently reproducible from the
catalogue and the acquired route directory. Resume by running the same command.
"""
import argparse
import hashlib
import json
from pathlib import Path

import requests
import city
import harvest

ENDPOINT = 'https://nmmtitmsmobileapi.amnex.co.in/api/TimeTable/'
LICENCE = 'Operator/vendor publication; reuse terms unverified'
SCHEDULES = harvest.Harvest(
    'nmmt_route_schedules', 'transit',
    title='NMMT public passenger timetables, one query per current route',
    licence=LICENCE, url=ENDPOINT + 'GetScheduelByRoute', method='POST',
    coverage='Published timetable queries, not observed operation. Service dates and completeness need validation.',
    discovered_from='nmmt_current_routes', harvester='acquire_nmmt_schedules.py')
TRIPS = harvest.Harvest(
    'nmmt_trip_timetables', 'transit',
    title='NMMT public trip stop timetables, one query per published trip',
    licence=LICENCE, url=ENDPOINT + 'GetScheduelDetail', method='POST',
    coverage='Public timetable detail requested with route and trip fields from the current route schedule.',
    discovered_from='nmmt_route_schedules', harvester='acquire_nmmt_schedules.py')


def read(source_id):
    """A loose single acquisition's successful data list (the route directory)."""
    record = json.loads(Path(city.path('data/raw/transit', 'provenance_'+source_id+'.json')).read_text(encoding='utf-8'))['files'][0]
    path = Path(city.path(record['path']))
    with path.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=record['sha256']:
            raise ValueError('Source hash mismatch: '+source_id)
    return data_list(json.loads(path.read_text(encoding='utf-8')), source_id)


def data_list(payload, label):
    """HTTP success alone does not establish application success."""
    if payload.get('issuccess') is not True or not isinstance(payload.get('data'),list):
        raise ValueError('Passenger API did not return a successful data list: '+label)
    if payload.get('rowcount') != len(payload['data']):
        raise ValueError('Passenger API count differs from response: '+label)
    return payload['data']


def read_member(which, member_id, listing=None):
    """One harvest member's successful data list."""
    return data_list(harvest.read_json(which.id, which.category, member_id, listing), member_id)


def register(entries):
    """Register LOOSE catalogue entries (single acquisitions), refusing an identity change."""
    path = Path(city.path('extract/sources.json'))
    catalogue = json.loads(path.read_text(encoding='utf-8'))
    existing = {entry['id']: entry for entry in catalogue['sources']}
    for entry in entries:
        if entry['id'] in existing:
            previous = existing[entry['id']]
            if any(previous.get(key)!=entry.get(key) for key in ('url','method','request_json')):
                raise ValueError('Immutable source identity changed: '+entry['id'])
        else:
            catalogue['sources'].append(entry)
    path.write_text(json.dumps(catalogue,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def entry(source_id, endpoint, body, parent):
    return dict(id=source_id, category='transit', format='json', method='POST',
                url=ENDPOINT+endpoint, request_json=body,
                title='NMMT public passenger timetable '+source_id, licence=LICENCE,
                coverage='Published timetable query, not observed operation. Service dates and completeness need validation.',
                discovered_from=parent)


def check_data_list(item, data):
    data_list(json.loads(data.decode('utf-8-sig')), item['id'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--details',action='store_true',help='Also acquire each published trip stop timetable.')
    parser.add_argument('--pause-seconds',type=float,default=0.25,help='Pause between uncached requests; network courtesy only.')
    args=parser.parse_args()
    if Path(city.path()).resolve()!=Path(__file__).resolve().parents[1]:
        raise ValueError('CITYSIM_CITY must select the city that owns this script')
    if not 0<=args.pause_seconds<=60:
        raise ValueError('Request pause must be between zero and sixty seconds')
    catalogue=json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    directory_entry=next(e for e in catalogue['sources'] if e['id']=='nmmt_current_routes')
    transport_mode=directory_entry['request_json']['intTransportMode']
    routes=read('nmmt_current_routes')
    route_ids=[row['strRouteId'] for row in routes]
    if len(set(route_ids))!=len(route_ids):
        raise ValueError('Repeated route identifier in directory')
    entries=[entry('nmmt_schedule_'+route_id,'GetScheduelByRoute',
                   dict(intTransportMode=transport_mode,strRouteId=route_id),'nmmt_current_routes')
             for route_id in sorted(route_ids,key=int)]
    allowed=harvest.allowed_domains()
    with requests.Session() as session:
        session.headers['User-Agent']='city-digital-twin public transport research/1.0'
        count, unresolved = harvest.pack(SCHEDULES, entries, session, allowed, args.pause_seconds,
                                         check=check_data_list)
        harvest.register(SCHEDULES, entries)
        if unresolved:
            raise SystemExit('%d route timetable(s) did not answer with a data list' % len(unresolved))
        if not args.details:
            return
        details={}
        listing = harvest.members(SCHEDULES.id, SCHEDULES.category)
        for source in entries:
            for trip in read_member(SCHEDULES, source['id'], listing):
                route_id,trip_id=str(trip['strRouteId']),int(trip['intTripId'])
                if route_id!=source['request_json']['strRouteId']:
                    raise ValueError('Trip assigned to another route')
                source_id=f'nmmt_trip_{route_id}_{trip_id}'
                body=dict(intTransportMode=transport_mode,strRouteId=route_id,
                          strFromStationId=trip['strFromStationId'],strToStationId=trip['strToStationId'],
                          intTripId=trip_id,intDirection=trip.get('intDirection',0),strRouetNo=trip['strRouteNo'])
                item=entry(source_id,'GetScheduelDetail',body,source['id'])
                if source_id in details and details[source_id]['request_json']!=body:
                    raise ValueError('Conflicting identity for a published trip')
                details[source_id]=item
        print('PUBLISHED TRIP QUERIES',len(details),flush=True)
        count, unresolved = harvest.pack(TRIPS, [details[key] for key in sorted(details)], session, allowed,
                                         args.pause_seconds, check=check_data_list)
        harvest.register(TRIPS, [details[key] for key in sorted(details)])
        if unresolved:
            raise SystemExit('%d trip timetable(s) did not answer with a data list' % len(unresolved))


if __name__=='__main__':
    main()
