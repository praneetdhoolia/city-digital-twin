"""Acquire one labelled snapshot of public route stops and vehicle indications.

This is a sequential census of directory queries, not a simultaneous fleet
snapshot or a repeated tracking service. Each response records retrieval time.
One snapshot label is one harvest archive (harvest.py).
"""
import argparse
import json
import re

import requests
import harvest
from acquire_nmmt_schedules import read

URL = 'https://nmmtitmsmobileapi.amnex.co.in/api/BusTracking/SearchByRouteDetails_v4'
# These are the public web client's anonymous query fields, not account
# credentials. The public query supplies an empty authentication token.
ANONYMOUS = dict(lan='en', userId=9, clientId=1, deviceType='web', deviceId='web-portal', authtoken='')


def snapshot(label):
    return harvest.Harvest(
        'nmmt_route_stop_snapshot_' + label, 'transit',
        title='NMMT public route stop and vehicle snapshot ' + label + ', one query per current route',
        licence='Operator publication; reuse terms unverified', url=URL, method='POST',
        coverage='Sequential public query. Stops and reported vehicles need spatial, timestamp and operating-status validation; not a fleet census.',
        discovered_from='nmmt_current_routes', harvester='acquire_nmmt_route_stops.py')


def check_stops(item, data):
    payload = json.loads(data.decode('utf-8-sig'))
    if any(not isinstance(payload.get(direction, {}).get('data'), list) for direction in ('up', 'down')):
        raise ValueError('Route stop response status/structure mismatch')
    if payload.get('issuccess') is not True:
        if not (payload.get('issuccess') is False and payload.get('message') == 'Data not found'
                and not payload['up']['data'] and not payload['down']['data']):
            raise ValueError('Unexpected route stop application status')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot-label', required=True, help='New immutable acquisition label, e.g. YYYYMMDD.')
    parser.add_argument('--pause-seconds', type=float, default=.25)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9_]+', args.snapshot_label) or not 0 <= args.pause_seconds <= 60:
        raise ValueError('Invalid snapshot label or request pause')
    routes = read('nmmt_current_routes')
    ids = [int(row['strRouteId']) for row in routes]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate route identifiers')
    which = snapshot(args.snapshot_label)
    entries = [dict(
        id=f'nmmt_route_live_{route_id}_{args.snapshot_label}', category='transit', format='json',
        method='POST', url=URL, request_json=dict(ANONYMOUS, routeid=route_id, servicetypeid=0),
        title=f'NMMT public route stop and vehicle snapshot {route_id} {args.snapshot_label}',
        licence=which.licence, coverage=which.coverage,
        discovered_from='nmmt_current_routes') for route_id in sorted(ids)]
    with requests.Session() as session:
        session.headers['User-Agent'] = 'city-digital-twin public transport research/1.0'
        count, unresolved = harvest.pack(which, entries, session, harvest.allowed_domains(),
                                         args.pause_seconds, check=check_stops)
    harvest.register(which, entries)
    return bool(unresolved)


if __name__ == '__main__':
    raise SystemExit(main())
