"""Audit acquired GTFS bytes without treating publication as validation.

The report is deterministic and preserves feed scope and structural defects.
It does not repair schedules or invent missing day-type variation.
"""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

import city

OUTPUT_INPUTS = {
    'data/processed/acquisition/bus_gtfs_audit.json': ['data/raw/transit/bus_gtfs_20260918_*.zip'],
}


def seconds(value):
    h, m, s = map(int, value.split(':'))
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError(value)
    return h * 3600 + m * 60 + s


def main():
    provenance = Path(city.path('data/raw/transit/provenance_bus_gtfs_20260918.json'))
    record = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
    source = Path(city.path(record['path']))
    with source.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
            raise ValueError('Acquired GTFS hash differs from provenance')
    defects = Counter()
    counts = {}
    with zipfile.ZipFile(source) as archive:
        def rows(name):
            with archive.open(name) as raw:
                yield from csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig'))

        def keyed(name, key):
            table = {}
            counts[name] = 0
            for row in rows(name):
                counts[name] += 1
                if row[key] in table:
                    defects[name + ':duplicate_' + key] += 1
                table[row[key]] = row
            return table

        agencies = keyed('agency.txt', 'agency_id')
        stops = keyed('stops.txt', 'stop_id')
        routes = keyed('routes.txt', 'route_id')
        trips = keyed('trips.txt', 'trip_id')
        calendar = keyed('calendar.txt', 'service_id')
        route_agencies = Counter()
        trip_agencies = Counter()
        for row in routes.values():
            route_agencies[row.get('agency_id', '')] += 1
            if row.get('agency_id', '') not in agencies:
                defects['routes:unknown_agency'] += 1
        for row in trips.values():
            route = routes.get(row['route_id'])
            if route is None:
                defects['trips:unknown_route'] += 1
            else:
                trip_agencies[route.get('agency_id', '')] += 1
            if row['service_id'] not in calendar:
                defects['trips:unknown_calendar_service'] += 1
        operated_routes = {row['route_id'] for row in trips.values()}
        empty_routes = Counter(row.get('agency_id', '') for key, row in routes.items()
                               if key not in operated_routes)
        coordinates = []
        for row in stops.values():
            try:
                lat, lon = float(row['stop_lat']), float(row['stop_lon'])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
                    raise ValueError('outside geographic domain')
                coordinates.append((lat, lon))
            except (ValueError, KeyError):
                defects['stops:invalid_coordinates'] += 1
        # Disk-backed ordering: the standard does not require rows to be sorted.
        with tempfile.TemporaryDirectory(prefix='gtfs-audit-') as temporary:
            db = sqlite3.connect(str(Path(temporary, 'times.sqlite')))
            db.execute('CREATE TABLE times (trip TEXT, seq INTEGER, arr INTEGER, dep INTEGER)')
            batch = []
            served = set()
            used_stops = set()
            counts['stop_times.txt'] = 0
            for row in rows('stop_times.txt'):
                counts['stop_times.txt'] += 1
                trip, stop = row['trip_id'], row['stop_id']
                served.add(trip)
                used_stops.add(stop)
                if trip not in trips:
                    defects['stop_times:unknown_trip'] += 1
                if stop not in stops:
                    defects['stop_times:unknown_stop'] += 1
                try:
                    seq = int(row['stop_sequence'])
                    if seq < 0:
                        raise ValueError('negative sequence')
                    arr, dep = seconds(row['arrival_time']), seconds(row['departure_time'])
                    if dep < arr:
                        defects['stop_times:departure_before_arrival'] += 1
                    batch.append((trip, seq, arr, dep))
                except (ValueError, KeyError):
                    defects['stop_times:missing_or_invalid_time_or_sequence'] += 1
                if len(batch) >= 10000:
                    db.executemany('INSERT INTO times VALUES (?,?,?,?)', batch)
                    batch.clear()
            db.executemany('INSERT INTO times VALUES (?,?,?,?)', batch)
            db.commit()
            previous = None
            for trip, seq, arr, dep in db.execute('SELECT trip,seq,arr,dep FROM times ORDER BY trip,seq,arr,dep'):
                if previous and previous[0] == trip:
                    if previous[1] == seq:
                        defects['stop_times:duplicate_trip_sequence'] += 1
                    if arr < previous[3]:
                        defects['stop_times:arrival_before_previous_departure'] += 1
                previous = (trip, seq, arr, dep)
            db.close()
        defects['trips:without_stop_times'] = len(set(trips) - served)
        findings = {
            'schema_version': 1,
            'input_path': record['path'], 'input_sha256': record['sha256'],
            'source': record['url'], 'source_kind': 'community compilation',
            'validation_scope': 'structural audit only; operational accuracy unverified',
            'tables': sorted(archive.namelist()), 'row_counts': counts,
            'agencies': list(agencies.values()),
            'routes_by_agency': dict(sorted(route_agencies.items())),
            'trips_by_agency': dict(sorted(trip_agencies.items())),
            'routes_without_trips_by_agency': dict(sorted(empty_routes.items())),
            'route_types': sorted({r['route_type'] for r in routes.values()}),
            'calendar': list(calendar.values()),
            'feed_info': list(rows('feed_info.txt')),
            'unused_stops_count': len(set(stops) - used_stops),
            'coordinate_extent_measured_from_feed': {
                'south_deg': min(x[0] for x in coordinates),
                'north_deg': max(x[0] for x in coordinates),
                'west_deg': min(x[1] for x in coordinates),
                'east_deg': max(x[1] for x in coordinates),
            } if coordinates else None,
            'defects': dict(sorted(defects.items())),
            'missing_optional_tables': sorted(set(('shapes.txt', 'frequencies.txt', 'calendar_dates.txt',
                                                   'transfers.txt', 'fare_attributes.txt', 'fare_rules.txt'))
                                               - set(archive.namelist())),
            'limitations': [
                'Advertised feed validity is not evidence that services operate as represented.',
                'Calendar and day-type variation must be checked against operator schedules.',
                'No assumption that this feed covers every bus operator or any other transport mode.',
                'Structural validity does not verify routes against roads, capacity, fares or observed ridership.',
            ],
        }
    output = Path(city.path('data/processed/acquisition/bus_gtfs_audit.json'))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'counts': counts, 'defects': findings['defects'], 'path': city.rel(str(output))}))


if __name__ == '__main__':
    main()
