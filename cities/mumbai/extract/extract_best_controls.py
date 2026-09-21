"""Extract operator fare products and depot listings without inferring service."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/best_published_fares.csv': [
        'data/raw/transit/best_bus_pass_2025_*.pdf',
        'extract/transcriptions/best_fares_passes_20250508.json'],
    'data/processed/observed/best_published_passes.csv': [
        'data/raw/transit/best_bus_pass_2025_*.pdf',
        'extract/transcriptions/best_fares_passes_20250508.json'],
    'data/processed/observed/best_depot_listing.csv': ['data/raw/transit/best_depots_20260919_*.html'],
    'data/processed/observed/best_depot_route_listing.csv': ['data/raw/transit/best_depots_20260919_*.html'],
    'data/processed/acquisition/best_controls_audit.json': [
        'data/raw/transit/best_bus_pass_2025_*.pdf',
        'extract/transcriptions/best_fares_passes_20250508.json',
        'data/raw/transit/best_depots_20260919_*.html'],
}


def fares_and_passes():
    path = Path(city.path('extract/transcriptions/best_fares_passes_20250508.json'))
    transcription = json.loads(path.read_text(encoding='utf-8'))
    record, _ = source(transcription['source_id'], 'transit')
    if record['sha256'] != transcription['source_sha256']:
        raise ValueError('Fare transcription belongs to a different source PDF')
    common = dict(source='official_fare_table_visual_transcription',
                  source_id=transcription['source_id'], source_sha256=record['sha256'],
                  transcription_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  effective_date_as_printed=transcription['effective_date_as_printed'],
                  status=transcription['status'], model_ready=False)
    fares, passes = [], []
    for row in transcription['fare_rows']:
        if len(row) != len(transcription['fare_columns']) or any(type(v) is not int or v <= 0 for v in row):
            raise ValueError('Invalid transcribed fare row')
        for column, value in zip(transcription['fare_columns'][1:], row[1:], strict=True):
            fares.append(dict(stage_distance_as_printed_km=row[0], fare_class=column.removesuffix('_inr'),
                              base_fare_inr=value, source_page_1_based=1, **common))
    for column in transcription['fare_columns'][1:]:
        selected = [r for r in fares if r['fare_class'] == column.removesuffix('_inr')]
        if any(b['base_fare_inr'] < a['base_fare_inr'] or
               b['stage_distance_as_printed_km'] <= a['stage_distance_as_printed_km']
               for a, b in zip(selected, selected[1:])):
            raise ValueError('Non-increasing stage or decreasing fare; inspect the source')
    for row in transcription['pass_rows']:
        if len(row) != len(transcription['pass_columns']) or any(type(v) is not int or v <= 0 for v in row):
            raise ValueError('Invalid transcribed pass row')
        for column, price in zip(transcription['pass_columns'][1:], row[1:], strict=True):
            match = re.fullmatch(r'(weekly|monthly)_(\d+)_trips_(\d+)_days_inr', column)
            if not match:
                raise ValueError('Unknown pass header')
            passes.append(dict(product=column.removesuffix('_inr'), up_to_distance_km=row[0],
                               valid_days=int(match.group(3)), valid_period_raw=match.group(1),
                               trips=int(match.group(2)), unlimited=False, price_inr=price,
                               eligibility_raw='Separate product eligibility and tax treatment unresolved',
                               source_page_1_based=2, **common))
    for row in transcription['other_passes']:
        passes.append(dict(product=row['product'], up_to_distance_km='', valid_days=row['valid_days'],
                           valid_period_raw='', trips=row['trips'], unlimited=row['unlimited'],
                           price_inr=row['price_inr'], eligibility_raw='Separate product eligibility unresolved',
                           source_page_1_based=2, **common))
    for row in transcription['special_role_passes_as_printed']:
        passes.append(dict(product=row['role'], up_to_distance_km='', valid_days='',
                           valid_period_raw=row['period'], trips='', unlimited='',
                           price_inr=row['price_inr'], eligibility_raw=row['role'],
                           source_page_1_based=2, **common))
    return transcription, fares, passes


def depots_and_routes():
    source_id = 'best_depots_20260919'
    record, path = source(source_id, 'transit')
    text = path.read_text(encoding='utf-8')
    # The raw page lacks a '<' in two closing td tags. Repair only that
    # syntax in memory; retain both exact edits in the audit and raw bytes.
    repairs = [
        ('Wadala, Mumbai/td>', 'Wadala, Mumbai</td>'),
        ('<td>GR/td>', '<td>GR</td>'),
    ]
    for before, after in repairs:
        if text.count(before) != 1:
            raise ValueError('Source HTML repair no longer uniquely matches')
        text = text.replace(before, after)
    soup = BeautifulSoup(text, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('Expected one depot table')
    headers = [' '.join(cell.get_text(' ', strip=True).split()) for cell in tables[0].select('thead th')]
    if headers != ['No.', 'Depot Name', 'Depot Code', 'Address', 'Bus Route No.', 'Bus Stations', 'Major Operation']:
        raise ValueError('Depot source table headers changed')
    zone, depots, routes = None, [], []
    for tr in tables[0].select('tbody tr'):
        cells = [' '.join(cell.get_text(' ', strip=True).split())
                 for cell in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) == 1:
            zone = cells[0]
            continue
        if len(cells) != len(headers) or not zone or not cells[0].isdigit():
            raise ValueError('Unrecognised depot row')
        common = dict(source='official_undated_operator_listing', source_id=source_id,
                      source_sha256=record['sha256'], source_row_serial=cells[0],
                      depot_code=cells[2], depot_name=cells[1], zone_raw=zone,
                      status='current_operation_and_geocoding_unverified')
        depots.append(dict(**common, address_raw=cells[3], routes_raw=cells[4],
                           bus_stations_raw=cells[5], major_operation_raw=cells[6]))
        for ordinal, label in enumerate(cells[4].split(','), start=1):
            if not label.strip():
                raise ValueError('Blank route token in source listing')
            routes.append(dict(**common, route_ordinal=ordinal, route_label_raw=label.strip(),
                               mode='bus', identity_crosswalk_status='unresolved'))
    if len({r['depot_code'] for r in depots}) != len(depots):
        raise ValueError('Duplicated depot code')
    return depots, routes, [dict(before=b, after=a) for b, a in repairs]


def main():
    transcription, fares, passes = fares_and_passes()
    depots, routes, repairs = depots_and_routes()
    pairs = Counter((r['depot_code'], r['route_label_raw']) for r in routes)
    audit = dict(status='published_controls_not_validated_current_bus_operations',
                 fare_cells=len(fares), pass_cells=len(passes), depots=len(depots),
                 depot_route_mentions=len(routes), distinct_route_labels=len({r['route_label_raw'] for r in routes}),
                 duplicate_depot_route_mentions=[dict(depot_code=k[0], route_label_raw=k[1], mentions=n)
                                                for k, n in sorted(pairs.items()) if n > 1],
                 html_syntax_repairs=repairs, fare_rules=transcription['fare_rules'],
                 pass_rules=transcription['pass_rules'],
                 limitations=transcription['limitations'] + [
                     'Depot route listings do not establish a current timetable, route geometry or vehicle allocation.',
                     'Route identifiers retain leading zeros, suffixes and direction/variant text.',
                     'FORT FERRY labels in this source identify bus services, not water transport.',
                     'No ridership, headway or capacity is inferred from the number of route mentions.'])
    for name, rows in [('best_published_fares.csv', fares), ('best_published_passes.csv', passes),
                       ('best_depot_listing.csv', depots), ('best_depot_route_listing.csv', routes)]:
        write(name, rows)
    Path(city.path('data/processed/acquisition/best_controls_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ['fare_cells', 'pass_cells', 'depots',
                                           'depot_route_mentions', 'distinct_route_labels']}))


if __name__ == '__main__':
    main()
