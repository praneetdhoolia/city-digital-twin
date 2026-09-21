"""Acquire one immutable detail query for each vehicle in a labelled route snapshot.

Selection comes from the acquired public passenger responses, not guessed IDs.
These sequential snapshots do not establish fleet size or tracking freshness.
One snapshot label is one harvest archive (harvest.py).
"""
import argparse
import csv
import json
from pathlib import Path
import re

import requests
import city
import harvest

URL = 'https://nmmtitmsmobileapi.amnex.co.in/api/BusTracking/GetVehicleTripDetails_v2'
# Anonymous fields observed in the public passenger client; no account token.
ANONYMOUS = dict(lan='en', userId=9, clientId=1, deviceType='web', deviceId='web-portal', authtoken='')


def snapshot(label):
    return harvest.Harvest(
        'nmmt_vehicle_snapshot_' + label, 'transit',
        title='NMMT public indicated vehicle trip details ' + label + ', one query per indicated vehicle',
        licence='Operator publication; reuse terms unverified', url=URL, method='POST',
        coverage='Public passenger query for each vehicle indicated in a route snapshot; not a complete fleet sample or validated trajectory.',
        discovered_from='nmmt_route_stop_snapshot_' + label, harvester='acquire_nmmt_vehicle_details.py')


def check_detail(item, data):
    payload = json.loads(data.decode('utf-8-sig'))
    stops, locations = payload.get('RouteDetails'), payload.get('LiveLocation')
    if not isinstance(stops, list) or not isinstance(locations, list):
        raise ValueError('Unexpected detail response structure')
    if payload.get('RowCount') != len(stops) + len(locations):
        raise ValueError('Response row count does not reconcile')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot-label', required=True)
    parser.add_argument('--pause-seconds', type=float, default=.25)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9_]+', args.snapshot_label) or not 0 <= args.pause_seconds <= 60:
        raise ValueError('Invalid snapshot label or request pause')
    if Path(city.path()).resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError('CITYSIM_CITY must select the owner of this script')
    selection = Path(city.path('data/processed/observed/nmmt_vehicle_indications.csv'))
    parents = {}
    with selection.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            if row['source_id'].endswith('_' + args.snapshot_label):
                vehicle_id = int(row['vehicle_id'])
                if vehicle_id <= 0:
                    raise ValueError('Nonpositive vehicle ID in source indications')
                parents.setdefault(vehicle_id, set()).add(row['source_id'])
    if not parents:
        raise ValueError('No vehicle indications for the requested snapshot label')
    which = snapshot(args.snapshot_label)
    entries = [dict(
        id=f'nmmt_vehicle_{vehicle_id}_{args.snapshot_label}', category='transit', format='json',
        method='POST', url=URL, request_json=dict(ANONYMOUS, vehicleId=vehicle_id),
        title=f'NMMT public indicated vehicle trip detail snapshot {vehicle_id}',
        licence=which.licence, coverage=which.coverage,
        discovered_from=sorted(source_ids)) for vehicle_id, source_ids in sorted(parents.items())]
    with requests.Session() as session:
        session.headers['User-Agent'] = 'city-digital-twin public transport research/1.0'
        count, unresolved = harvest.pack(which, entries, session, harvest.allowed_domains(),
                                         args.pause_seconds, check=check_detail)
    harvest.register(which, entries)
    return bool(unresolved)


if __name__ == '__main__':
    raise SystemExit(main())
