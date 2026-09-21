"""Normalise published MMB evidence without inventing daily ferry services.

The annual series and service directory have different row identifiers. They
are deliberately kept separate until a reviewed route crosswalk exists.
"""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

import city

OUTPUT_INPUTS = {
    'data/processed/observed/water_annual_passengers.csv': ['data/raw/water/mmb_performance_*.json'],
    'data/processed/observed/water_service_directory.csv': ['data/raw/water/mmb_routes_*.json'],
    'data/processed/observed/_water_evidence_audit.json': [
        'data/raw/water/mmb_performance_*.json', 'data/raw/water/mmb_routes_*.json'],
}


def acquired(source_id):
    provenance = Path(city.path('data/raw/water', 'provenance_' + source_id + '.json'))
    record = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
    path = Path(city.path(record['path']))
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
            raise ValueError('Source hash mismatch: ' + source_id)
    return record, json.loads(path.read_text(encoding='utf-8'))['data']


def write_csv(name, rows):
    output = Path(city.path('data/processed/observed', name))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    source, data = acquired('mmb_performance')
    rows, vectors = [], defaultdict(list)
    keys = set()
    for route in data['stats']:
        vector = []
        for year in route['years']:
            key = (route['id'], year['label'])
            if key in keys:
                raise ValueError('Duplicate route/year in published statistics')
            keys.add(key)
            raw = str(year['total']).strip()
            numeric = raw.replace(',', '')
            # NIL is retained as a reported token, never guessed to mean zero.
            value = int(numeric) if re.fullmatch(r'[0-9]+', numeric) else ''
            vector.append((year['label'], raw))
            rows.append(dict(
                publication_route_id=route['id'], port_group=route['portGroupEn'],
                route_name=route['routeEn'], financial_year=year['label'],
                reported_passengers_count=value, reported_count_raw=raw,
                parse_status='numeric' if value != '' else 'non_numeric_token',
                source='reported_observation', source_id='mmb_performance',
                source_url=source['url'], source_sha256=source['sha256'],
                count_definition='Published passenger total; journey/boarding/direction definition unverified',
                geography_status='Statewide source; MMR membership not yet resolved',
                calibration_eligible='false'))
        vectors[tuple(vector)].append(route['routeEn'])
    write_csv('water_annual_passengers.csv', rows)
    services_source, services = acquired('mmb_routes')
    directory = []
    for route in services['routes']:
        directory.append(dict(
            directory_route_id=route['id'], port_group=route['portGroupEn'],
            route_name=route['routesEn'], first_departure_raw=route['firstDepartureEn'],
            last_departure_raw=route['lastDepartureEn'], fare_raw=route['fareEn'],
            passenger_capacity_raw=route['totalPassengerCapacityEn'],
            source='published_service_directory', source_id='mmb_routes',
            source_url=services_source['url'], source_sha256=services_source['sha256'],
            validation_status='Units, season, vessel/fleet basis and base-date service unverified'))
    write_csv('water_service_directory.csv', directory)
    audit = dict(
        annual_route_count=len(data['stats']), annual_observation_rows=len(rows),
        service_directory_rows=len(directory),
        years=sorted({row['financial_year'] for row in rows}),
        non_numeric_count_rows=sum(row['parse_status'] != 'numeric' for row in rows),
        identical_reported_series=[{'routes': names, 'series': list(vector)}
                                   for vector, names in sorted(vectors.items()) if len(names) > 1],
        unresolved=[
            'Statistics and directory row identifiers refer to different routes; never join by numeric id.',
            'Identical series on separately named routes may be duplicated reporting; do not sum without resolution.',
            'NIL, empty and numeric zero remain distinct.',
            'The source covers Maharashtra, not only the study region.',
            'First and last departure are not a timetable; service frequency remains unmeasured.',
            'Capacity strings include seasonal ranges and potentially aggregate fleet capacity; no per-vessel conversion made.',
            'English and Marathi fields can disagree; retain raw bilingual source for reconciliation.',
            'Annual passenger totals do not establish weekday, peak-hour or linked journey counts.',
        ],
    )
    output = Path(city.path('data/processed/observed/_water_evidence_audit.json'))
    output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ('annual_route_count', 'annual_observation_rows',
                                         'service_directory_rows', 'non_numeric_count_rows')}))


if __name__ == '__main__':
    main()
