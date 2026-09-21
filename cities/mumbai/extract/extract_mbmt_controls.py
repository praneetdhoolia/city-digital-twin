"""Retain undated municipal fleet/allocation claims and contract specifications."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/mbmt_published_fleet.csv': ['data/raw/transit/mbmt_operator_profile_*.html'],
    'data/processed/observed/mbmt_published_bus_allocations.csv': ['data/raw/transit/mbmt_operator_profile_*.html'],
    'data/processed/observed/mbmt_contract_capacities.csv': [
        'data/raw/transit/mbmt_electric_bus_agreement_*.pdf',
        'extract/transcriptions/mbmt_electric_bus_contract_capacities.json'],
    'data/processed/acquisition/mbmt_controls_audit.json': [
        'data/raw/transit/mbmt_operator_profile_*.html', 'data/raw/transit/mbmt_electric_bus_agreement_*.pdf',
        'extract/transcriptions/mbmt_electric_bus_contract_capacities.json'],
}


def cells(table):
    return [[' '.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['th', 'td'])]
            for tr in table.find_all('tr')]


def unique_table(soup, first_row):
    tables = [cells(t) for t in soup.find_all('table') if not t.find('table')]
    matches = [rows for rows in tables if rows and rows[0] == first_row]
    if len(matches) != 1:
        raise ValueError('Municipal table headers missing or ambiguous')
    return matches[0]


def main():
    sid = 'mbmt_operator_profile'
    record, path = source(sid, 'transit')
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    common = dict(source_id=sid, source_sha256=record['sha256'],
                  source='undated_municipal_operator_profile', model_ready=False,
                  status='reference_date_and_current_operation_unverified')
    fleet_table = unique_table(soup, ['Sr.No.', 'Details', 'Bus Number', 'Total', 'Remarks'])
    fleet = []
    for row in fleet_table[1:-1]:
        if len(row) != 5:
            raise ValueError('Unexpected fleet row')
        match = re.fullmatch(r'(.+?)\s*\(\s*Migrant capacity\s+(\d+)\s*\+\s*(\d+)\s*=\s*(\d+)\)', row[1])
        if not match or int(row[2]) != int(row[3]):
            raise ValueError('Fleet capacity expression or duplicated bus count changed')
        label, a, b, total = match.groups()
        if int(a) + int(b) != int(total):
            raise ValueError('Printed capacity arithmetic does not agree')
        fleet.append(dict(**common, vehicle_description_raw=label.strip(),
                          capacity_expression_raw=row[1], capacity_component_a_persons=int(a),
                          capacity_component_b_persons=int(b), total_capacity_persons=int(total),
                          component_labels_status='seated_standing_labels_not_explicit_in_this_table',
                          published_buses_count=int(row[2])))
    fleet_total = fleet_table[-1]
    if fleet_total[0] != 'Total' or sum(r['published_buses_count'] for r in fleet) != int(fleet_total[2]):
        raise ValueError('Published fleet subtotal does not reconcile')
    headings = ['Sl. No.', 'Bus Route No.', 'Bus route name', 'Monday.to.Friday.',
                'Saturday', 'Sundays and public holidays']
    table = unique_table(soup, headings)
    allocations = []
    for sequence, row in enumerate(table[1:], start=1):
        if len(row) != len(headings):
            raise ValueError('Unexpected route allocation row')
        for heading, value in zip(headings[3:], row[3:], strict=True):
            allocations.append(dict(**common, source_row_sequence=sequence, source_serial_raw=row[0],
                                    route_label_raw=row[1], route_name_raw=row[2], day_type_raw=heading,
                                    buses_count=int(value), is_subtotal=row[0] == 'Total'))
    totals = []
    for heading in headings[3:]:
        selected = [r for r in allocations if r['day_type_raw'] == heading]
        published = [r['buses_count'] for r in selected if r['is_subtotal']]
        calculated = sum(r['buses_count'] for r in selected if not r['is_subtotal'])
        if len(published) != 1:
            raise ValueError('Expected one published day-type total')
        totals.append(dict(day_type_raw=heading, published_buses_count=published[0],
                           summed_route_buses_count=calculated, difference_buses=calculated-published[0]))
    path = Path(city.path('extract/transcriptions/mbmt_electric_bus_contract_capacities.json'))
    transcription = json.loads(path.read_text(encoding='utf-8'))
    record, _ = source(transcription['source_id'], 'transit')
    if record['sha256'] != transcription['source_sha256']:
        raise ValueError('Contract transcription source hash changed')
    contract = [dict(**row, source_id=transcription['source_id'], source_sha256=record['sha256'],
                     transcription_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     source=transcription['source'], status=transcription['status'], model_ready=False)
                for row in transcription['rows']]
    serials = Counter(row[0] for row in table[1:-1])
    result = dict(status='published_claims_not_current_operating_fleet', fleet_rows=len(fleet),
                  allocation_cells=len(allocations), contract_configurations=len(contract),
                  allocation_subtotals=totals,
                  duplicate_source_serials={k: v for k, v in serials.items() if v > 1},
                  limitations=transcription['limitations'] + [
                      'Municipal profile dates are unresolved; its fleet table omits the electric fleet described elsewhere on the page.',
                      'Capacity addition is printed but the components are not explicitly labelled seated/standing in the English table.',
                      'Day-type bus allocation is not a departure timetable or independently observed daily operation.',
                      'Route numbers do not directly identify the passenger API RouteId; the crosswalk remains unresolved.',
                      'Repeated source serial numbers are retained and never used as unique route identifiers.'])
    for name, rows in [('mbmt_published_fleet.csv', fleet), ('mbmt_published_bus_allocations.csv', allocations),
                       ('mbmt_contract_capacities.csv', contract)]:
        write(name, rows)
    Path(city.path('data/processed/acquisition/mbmt_controls_audit.json')).write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('fleet_rows', 'allocation_cells', 'contract_configurations', 'allocation_subtotals')}))


if __name__ == '__main__':
    main()
