"""Acquire operator route geometry through the public passenger map query.

The catalogue directory determines scope. Geometry is published alignment,
not evidence of actual operation. All routes' responses are the members of one
harvest archive (harvest.py); the acquisition is immutable and resumable.
"""
import argparse
import json

import requests
import harvest
from acquire_nmmt_schedules import read

ALIGNMENTS = harvest.Harvest(
    'nmmt_route_alignments', 'transit',
    title='NMMT public route alignments, one passenger-map query per current route',
    licence='Operator publication; reuse terms unverified',
    url='https://nmmtitmsmobileapi.amnex.co.in/api/BusTracking/GetRoutePathData', method='POST',
    coverage='Passenger map geometry. Direction, road matching and current operation need validation.',
    discovered_from='nmmt_current_routes', harvester='acquire_nmmt_paths.py')


def check_path(item, data):
    payload = json.loads(data.decode('utf-8-sig'))
    if (payload.get('IsSuccess') is not True or not isinstance(payload.get('Data'), list)
            or payload.get('RowCount') != len(payload['Data'])):
        raise ValueError('Route path response status/count mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pause-seconds', type=float, default=.25)
    args = parser.parse_args()
    if not 0 <= args.pause_seconds <= 60:
        raise ValueError('Request pause must be between zero and sixty seconds')
    routes = read('nmmt_current_routes')
    ids = [int(row['strRouteId']) for row in routes]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate route identifiers')
    entries = [dict(
        id='nmmt_route_path_'+str(route_id), category='transit', format='json',
        method='POST', url=ALIGNMENTS.url,
        request_json=dict(routeid=route_id), title='NMMT public route alignment '+str(route_id),
        licence=ALIGNMENTS.licence, coverage=ALIGNMENTS.coverage,
        discovered_from='nmmt_current_routes') for route_id in sorted(ids)]
    with requests.Session() as session:
        session.headers['User-Agent'] = 'city-digital-twin public transport research/1.0'
        count, unresolved = harvest.pack(ALIGNMENTS, entries, session, harvest.allowed_domains(),
                                         args.pause_seconds, check=check_path)
    harvest.register(ALIGNMENTS, entries)
    return bool(unresolved)


if __name__ == '__main__':
    raise SystemExit(main())
