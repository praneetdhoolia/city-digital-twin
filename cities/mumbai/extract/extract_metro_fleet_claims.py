"""Preserve dated fleet claims, their units and capacity qualifiers."""
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
import city
from extract_census_controls import source, write
from extract_population_projections import page_text

OUTPUT_INPUTS = {
    'data/processed/observed/metro_fleet_publication_claims.csv': [
        'data/raw/transit/alstom_metro3_opening_2024_*.pdf',
        'data/raw/transit/pib_beml_mumbai_order_2018_*.html'],
    'data/processed/acquisition/metro_fleet_claims_audit.json': [
        'data/raw/transit/alstom_metro3_opening_2024_*.pdf',
        'data/raw/transit/pib_beml_mumbai_order_2018_*.html'],
}


def one(pattern, text):
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise ValueError('Expected one fleet specification match: ' + pattern)
    return int(matches[0].replace(',', ''))


def main():
    rows = []

    def add(record, sid, date, route, metric, value, unit, qualifier, anchor):
        rows.append(dict(source='published_specification', source_id=sid,
                         source_sha256=record['sha256'], source_url=record['url'],
                         publication_date=date, route_scope=route, metric=metric,
                         value=value, unit=unit, qualifier=qualifier, source_anchor=anchor,
                         seats_count='', standing_places_count='',
                         standing_density_persons_per_m2='',
                         capacity_split_status='not_stated_in_publication',
                         operational_trip_assignment_status='unresolved',
                         model_input_status='evidence_only_not_adopted'))

    sid = 'alstom_metro3_opening_2024'
    record, path = source(sid, 'transit')
    first = ' '.join(page_text(path, 1).split())
    second = ' '.join(page_text(path, 2).split())
    if '5 October 2024' not in first or 'Mumbai Metro' not in first:
        raise ValueError('Alstom publication identity changed')
    contracted = one(r'manufacturing of (\d+) lightweight', first)
    coaches = one(r'metro trains of (\d+) cars each', first)
    capacity = one(r'accommodate at least ([\d,]+) passengers', second)
    delivered = one(r'So far, (\d+) trainsets have been delivered', second)
    for metric, value, unit, qualifier, anchor in (
        ('contracted_trainsets', contracted, 'trainsets', 'contract_scope', 'PDF page 1, engagement paragraph'),
        ('formation', coaches, 'cars_per_train', 'contract_specification', 'PDF page 1, engagement paragraph'),
        ('passenger_capacity', capacity, 'passengers_per_train', 'at_least', 'PDF page 2, first paragraph'),
        ('delivered_trainsets', delivered, 'trainsets', 'as_of_publication', 'PDF page 2, manufacturing paragraph'),
    ):
        add(record, sid, '2024-10-05', 'Mumbai Metro Line 3', metric, value, unit, qualifier, anchor)

    sid = 'pib_beml_mumbai_order_2018'
    record, path = source(sid, 'transit')
    text = ' '.join(BeautifulSoup(path.read_bytes(), 'html.parser').stripped_strings)
    text = ' '.join(text.split())
    if '22-November-2018' not in text or '2A, 2B & 7' not in text:
        raise ValueError('PIB publication identity changed')
    trains = one(r'Total Trains:\s*(\d+)', text)
    coaches = one(r'Coaches per Train:\s*(\d+)', text)
    capacity = one(r'Carrying capacity of (\d+) passengers in each coach', text)
    total_cars = one(r'order includes manufacturing of (\d+) Metro cars', text)
    if trains * coaches != total_cars:
        raise ValueError('PIB contract cars disagree with formation and train count')
    for metric, value, unit, qualifier in (
        ('contracted_trainsets', trains, 'trainsets', 'contract_scope'),
        ('formation', coaches, 'cars_per_train', 'contract_specification'),
        ('passenger_capacity', capacity, 'passengers_per_car', 'nominal_unspecified_density'),
        ('contracted_cars', total_cars, 'cars', 'contract_scope'),
    ):
        add(record, sid, '2018-11-22', 'Mumbai Metro Lines 2A;2B;7', metric,
            value, unit, qualifier, 'Order paragraph and salient-features list')
    write('metro_fleet_publication_claims.csv', rows)
    audit = dict(claim_rows=len(rows), source_ids=sorted({r['source_id'] for r in rows}),
                 pib_contract_identity=dict(trainsets=trains, cars_per_train=coaches,
                                            cars=total_cars, status='exact'),
                 seating_and_standing_split='unobtained_not_zero',
                 current_operating_fleet_and_assignments='unresolved',
                 demand_forecasts='not_extracted_as_observations',
                 model_parameters_adopted=False)
    Path(city.path('data/processed/acquisition/metro_fleet_claims_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
