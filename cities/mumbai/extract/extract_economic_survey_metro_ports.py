"""Extract merged metro controls and dated port totals without changing scope."""
from decimal import Decimal
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_economic_survey_transport import number, SID
from extract_population_projections import page_text

OUTPUT_INPUTS = {
    'data/processed/observed/economic_survey_metro_routes.csv': [
        'data/raw/population/maha_economic_survey_2025_26_*.pdf'],
    'data/processed/observed/economic_survey_metro_controls.csv': [
        'data/raw/population/maha_economic_survey_2025_26_*.pdf'],
    'data/processed/observed/economic_survey_port_controls.csv': [
        'data/raw/population/maha_economic_survey_2025_26_*.pdf'],
    'data/processed/acquisition/economic_survey_metro_ports_audit.json': [
        'data/raw/population/maha_economic_survey_2025_26_*.pdf'],
}
# Source row order and the membership of the printed merged cells. These are
# extraction identities, not operational assignments or simulated routes.
METRO_ROWS = (
    ('mumbai_1', 'mumbai_1', ('1 Varsova to Ghatkoper',)),
    ('mumbai_2a', 'mumbai_2a_7', ('2A Dahisar to D.N. nagar',)),
    ('mumbai_7', 'mumbai_2a_7', ('7 Andheri (E) to Dahisar (E)',)),
    ('mumbai_3', 'mumbai_3', ('3 Colaba-Bandra-SEEPZ',)),
    ('navi_mumbai_1', 'navi_mumbai_1', ('CBD Belapur to Pendhar',)),
    ('nagpur_north_south', 'nagpur_phase_1', ('North-South corridor -', 'Khapri to Automotive', 'square (orange line)')),
    ('nagpur_east_west', 'nagpur_phase_1', ('East-West corridor -', 'Lokmanya Nagar to', 'Prajapati Nagar (aqua line)')),
    ('pune_corridor_1', 'pune_phase_1', ('Corridor I-Pimpri', 'Chinchwad to Swargate', '(Purple line)')),
    ('pune_corridor_2', 'pune_phase_1', ('Corridor II-Vanaz to', 'Ramwadi (Aqua line)')),
)
MERGED = {
    'mumbai_2a_7': 'Mumbai Metro Rail',
    'nagpur_phase_1': 'Nagpur Metro rail phase 1',
    'pune_phase_1': 'Pune Metro Rail phase 1',
}


def metro_tables(path, common):
    body = page_text(path, 223).split('Table 9.34 Details', 1)[1].split('Source:', 1)[0]
    if not all(text in body for text in ('commissioned year', 'Length', '(km)', '(lakh)')):
        raise ValueError('Metro table headings changed')
    pattern = re.compile(r'\b([A-Za-z]+ 20\d\d)\s+(\d+(?:\.\d+)?)(?:\s+(\d+(?:\.\d+)?))?\s*$')
    numeric_rows = [match for line in body.splitlines() if (match := pattern.search(line))]
    if len(numeric_rows) != len(METRO_ROWS):
        raise ValueError('Metro row coverage changed')
    routes, passengers = [], {}
    normal = ' '.join(body.split())
    for (identity, group, labels), match in zip(METRO_ROWS, numeric_rows):
        if not all(label in normal for label in labels):
            raise ValueError('Missing metro source label: ' + identity)
        routes.append(dict(**common, source_pdf_page=223, source_table='9.34', route_id=identity,
                           passenger_control_group_id=group, route_as_printed=' '.join(labels),
                           commissioned_month_as_printed=match[1], reported_length_km=number(match[2]),
                           commissioning_scope='table_entry_not_complete_phase_history'))
        if match[3] is not None:
            if group in passengers:
                raise ValueError('Repeated metro passenger control')
            passengers[group] = number(match[3])
    for group, label in MERGED.items():
        # Pune's merged provider cell shares its line with a wrapped route cell.
        matches = re.findall(r'^\s*' + re.escape(label)
                             + r'\s+(?:\(Purple line\)\s+)?(\d+(?:\.\d+)?)\s*$', body, re.M)
        if len(matches) != 1 or group in passengers:
            raise ValueError('Ambiguous merged metro passenger cell: ' + group)
        passengers[group] = number(matches[0])
    groups = sorted({row['passenger_control_group_id'] for row in routes})
    if set(groups) != passengers.keys():
        raise ValueError('Every metro route must belong to exactly one printed control group')
    controls = []
    for group in groups:
        members = [row['route_id'] for row in routes if row['passenger_control_group_id'] == group]
        controls.append(dict(**common, source_pdf_page=223, source_table='9.34', control_group_id=group,
                             route_ids=';'.join(members), route_count=len(members),
                             average_passengers_per_day_lakh=passengers[group],
                             averaging_period='not_stated_in_table',
                             passenger_count_definition='not_resolved_as_unique_people_journeys_or_boardings',
                             allocation_status='combined_control_not_allocated_to_member_routes' if len(members) > 1
                             else 'single_route_control',
                             target_status='requires_period_and_counting_definition_reconciliation'))
    return routes, controls


def half_quantum(value):
    return Decimal(1).scaleb(Decimal(value).as_tuple().exponent) / 2


def port_tables(path, common):
    body = page_text(path, 225).split('Table 9.36 Transport statistics of major ports', 1)[1]
    if not all(text in body for text in ('Mumbai Port', 'Jawaharlal Nehru Port', 'N.A. Not Applicable')):
        raise ValueError('Port table headings changed')
    body = body.split('Source:', 1)[0]
    dates = re.findall(r'20\d\d-\d\d', body)
    if len(dates) != 4:
        raise ValueError('Port year-column coverage changed')
    labels = (
        ('Total cargo capacity (lakh MT)', 'cargo_capacity_lakh_mt'),
        ('Cargo traffic handled (lakh MT)', 'cargo_handled_lakh_mt'),
        ('a) Import', 'import_lakh_mt'), ('b) Export', 'export_lakh_mt'),
        ("Passenger traffic handled ('000)", 'passengers_handled_thousands'),
        ('Vessels handled (no.)', 'vessels_handled_count'),
    )
    cells = {}
    for label, field in labels:
        lines = [line for line in body.splitlines() if label in line]
        if len(lines) != 1:
            raise ValueError('Ambiguous port metric: ' + field)
        values = lines[0].split(label, 1)[1].split()
        if len(values) != len(dates):
            raise ValueError('Port metric column coverage changed: ' + field)
        cells[field] = values
    ports, checks = [], []
    for index, (port, year) in enumerate(zip(('Mumbai Port', 'Mumbai Port', 'Jawaharlal Nehru Port', 'Jawaharlal Nehru Port'), dates)):
        row = dict(**common, source_pdf_page=225, source_table='9.36', port=port, reference_financial_year=year)
        for _, field in labels:
            token = cells[field][index]
            row[field] = None if token == 'N.A.' else number(token, integer=field == 'vessels_handled_count')
        row['passengers_cell_status'] = 'not_applicable' if cells['passengers_handled_thousands'][index] == 'N.A.' else 'reported'
        row['cargo_unit_as_printed'] = 'lakh MT'
        row['cargo_mode_split'] = 'not_supplied_in_table'
        row['passenger_count_scope'] = 'port_handled_traffic_not_established_as_local_ferry_boardings'
        row['target_status'] = 'requires_modal_scope_and_period_reconciliation'
        ports.append(row)
        total, imported, exported = [Decimal(row[key]) for key in ('cargo_handled_lakh_mt', 'import_lakh_mt', 'export_lakh_mt')]
        residual = total - imported - exported
        tolerance = sum(half_quantum(row[key]) for key in ('cargo_handled_lakh_mt', 'import_lakh_mt', 'export_lakh_mt'))
        checks.append(dict(port=port, reference_financial_year=year, identity='cargo_handled_equals_import_plus_export',
                           residual_lakh_mt=str(residual), source_rounding_envelope_lakh_mt=str(tolerance),
                           status='exact' if residual == 0 else 'rounding_compatible' if abs(residual) <= tolerance
                           else 'source_disagreement'))
    return ports, checks


def main():
    record, path = source(SID, 'population')
    common = dict(source='observed', source_id=SID, source_sha256=record['sha256'], publication_edition='2025-26')
    routes, controls = metro_tables(path, common)
    ports, checks = port_tables(path, common)
    write('economic_survey_metro_routes.csv', routes)
    write('economic_survey_metro_controls.csv', controls)
    write('economic_survey_port_controls.csv', ports)
    audit = dict(source='derived', source_id=SID, source_sha256=record['sha256'],
                 metro_route_rows=len(routes), metro_control_groups=len(controls), port_period_rows=len(ports),
                 port_arithmetic_checks=checks,
                 limitations=[
                     'Metro averaging dates and the passenger counting definition are not stated in the table.',
                     'Merged metro passenger cells remain one group; no figure is duplicated or divided between routes.',
                     'Commissioning months describe the published route entry, not every opening phase.',
                     'The table also includes Nagpur and Pune; those observations are not Mumbai demand.',
                     'Port passenger N.A. is not applicable, not zero; local ferry counting scope is unresolved.',
                     'Cargo mass and vessel counts do not imply road vehicles, train movements or passenger services.',
                     'Cargo units retain the printed lakh MT; no load factor, modal split or empty return flow is inferred.',
                 ])
    output = Path(city.path('data/processed/acquisition/economic_survey_metro_ports_audit.json'))
    output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('metro_route_rows', 'metro_control_groups', 'port_period_rows', 'port_arithmetic_checks')}))


if __name__ == '__main__':
    main()
