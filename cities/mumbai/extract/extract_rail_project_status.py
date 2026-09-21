"""Separate dated railway project statements from operational supply."""
import json
from pathlib import Path
import re

import city
from extract_census_controls import write
from extract_suburban_fleet_claims import one, publication

OUTPUT_INPUTS = {
    'data/processed/observed/rail_terminal_project_status_20260325.csv': ['data/raw/rail/pib_mumbai_rail_capacity_projects_20260325_*.html'],
    'data/processed/observed/rail_corridor_project_status_20260325.csv': ['data/raw/rail/pib_mumbai_rail_capacity_projects_20260325_*.html'],
    'data/processed/observed/rail_capacity_claims_20260325.csv': ['data/raw/rail/pib_mumbai_rail_capacity_projects_20260325_*.html'],
    'data/processed/acquisition/rail_project_status_audit.json': ['data/raw/rail/pib_mumbai_rail_capacity_projects_20260325_*.html'],
}


def main():
    sid = 'pib_mumbai_rail_capacity_projects_20260325'
    record, body, text = publication(sid, '2245194')
    if '25 MAR 2026' not in text:
        raise ValueError('Rail project statement date changed')
    tables = [[[' '.join(cell.get_text(' ', strip=True).split()) for cell in row.find_all(['td', 'th'])]
               for row in table.find_all('tr')] for table in body.find_all('table')]
    # The article has separate Mumbai and Pune tables; the latter are outside
    # this extraction. The page's duplicated accessibility copy is outside body.
    terminal_tables = [rows for rows in tables if rows[0] == ['SN', 'Location', 'Details']
                       and rows[1][1] == 'Bandra Terminus']
    corridor_tables = [rows for rows in tables if rows[0] == ['SN', 'Name of Project', 'Cost (₹ in Cr.)']]
    if len(terminal_tables) != 1 or len(corridor_tables) != 1:
        raise ValueError('Missing or ambiguous project tables')
    terminal, corridor = terminal_tables[0], corridor_tables[0]
    if len(terminal) != 13 or len(corridor) != 14:
        raise ValueError('Reviewed project table row counts changed')
    common = dict(source='observed_official_publication_claim', source_id=sid, source_sha256=record['sha256'],
                  publication_date='2026-03-25', current_model_supply_adopted=False)
    terminals, corridors = [], []
    for order, (number, location, details) in enumerate(terminal[1:], 1):
        if int(number) != order:
            raise ValueError('Terminal table row order changed')
        terminals.append(dict(**common, source_table='Capacity Augmentation works for Mumbai Area', source_row=number,
            location_as_printed=location, details_as_printed=details,
            status_scope='completed_as_stated' if 'have been completed' in details else
                         'mixed_completed_taken_up_planned_heading_row_status_unresolved',
            commissioned_date='', operational_capacity_status='not_established_by_this_table'))
    for order, (number, project, cost) in enumerate(corridor[1:], 1):
        if int(number) != order or not re.fullmatch(r'[\d,]+', cost):
            raise ValueError('Corridor table row or monetary units changed')
        lengths = re.findall(r'\(([\d.]+)\s*Km\)', project, flags=re.IGNORECASE)
        if len(lengths) > 1:
            raise ValueError('Multiple stated project lengths')
        corridors.append(dict(**common, source_table='New projects for increasing capacity', source_row=number,
            project_as_printed=project, stated_project_length_km=lengths[0] if lengths else '',
            stated_cost_INR_crore=int(cost.replace(',', '')), status_scope='sanctioned_project_not_proof_of_commissioning',
            commissioned_date='', operational_capacity_status='not_established_by_this_table'))
    claims = []

    def claim(metric, value, unit, qualifier, status, anchor):
        claims.append(dict(**common, metric=metric, reported_value=value, units=unit, qualifier=qualifier,
                           status_scope=status, source_anchor=anchor))

    trains, services = one(r'around ([\d,]+) originating Mail/Express trains and nearly ([\d,]+) suburban train services daily', text)
    claim('originating_mail_express', int(trains.replace(',', '')), 'train_services_per_day', 'around',
          'dated_approximate_operational_aggregate_counting_frame_requires_reconciliation', 'Opening Mumbai paragraph')
    claim('suburban_services', int(services.replace(',', '')), 'train_services_per_day', 'nearly',
          'dated_approximate_operational_aggregate_counting_frame_requires_reconciliation', 'Opening Mumbai paragraph')
    stations, cars = one(r'Platform extension work at (\d+) stations to accommodate (\d+) car EMUs have been taken up', text)
    claim('stations_with_platform_extension_work', int(stations), 'stations', 'taken_up',
          'works_not_confirmed_completed', 'Platform length extension')
    claim('formation_target_of_platform_extensions', int(cars), 'cars_per_rake', 'target',
          'design_target_not_current_trip_assignment', 'Platform length extension')
    rakes, formation = one(r'(\d+) rakes of (\d+) cars each with doors have been sanctioned', text)
    claim('sanctioned_door_equipped_rakes', int(rakes), 'rakes', 'sanctioned',
          'procurement_not_active_fleet', 'New generation trains')
    claim('sanctioned_rake_formation', int(formation), 'cars_per_rake', 'sanctioned',
          'procurement_not_current_trip_assignment', 'New generation trains')
    write('rail_terminal_project_status_20260325.csv', terminals)
    write('rail_corridor_project_status_20260325.csv', corridors)
    write('rail_capacity_claims_20260325.csv', claims)
    audit = dict(source_id=sid, source_sha256=record['sha256'], terminal_project_rows=len(terminals),
        corridor_project_rows=len(corridors), aggregate_claim_rows=len(claims), model_parameters_adopted=False,
        limitations=[
            'The terminal heading mixes completed, taken-up and planned works; only explicit row wording establishes a reported status.',
            'Project length, cost, platform counts and sanctioned rake quantities do not prove commissioning or current usable capacity.',
            'The Goregaon-Borivali Harbour extension is a sanctioned project here; this source cannot resolve an individual Borivali timetable service.',
            'Approximate network-wide service totals have a different date and precision from later operator counts; they must not be pooled or used as exact targets.',
            'A repeated procurement statement is not an additional stock receipt. No project or vehicle is added to the operating simulation.',
            'Pune tables and the duplicated accessibility copy are excluded from these Mumbai observations.',
        ])
    Path(city.path('data/processed/acquisition/rail_project_status_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
