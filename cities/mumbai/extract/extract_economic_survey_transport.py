"""Extract dated operator aggregates without treating them as current schedules."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

OUTPUT_INPUTS = {
    'data/processed/observed/economic_survey_bus_controls.csv': ['data/raw/population/maha_economic_survey_2025_26_*.pdf'],
    'data/processed/observed/economic_survey_suburban_rail_controls.csv': ['data/raw/population/maha_economic_survey_2025_26_*.pdf'],
    'data/processed/acquisition/economic_survey_transport_audit.json': ['data/raw/population/maha_economic_survey_2025_26_*.pdf'],
}
SID = 'maha_economic_survey_2025_26'


def number(text, integer=False):
    if text == '-':
        return None
    result = Decimal(text.replace(',', ''))
    if result < 0 or (integer and result != result.to_integral_value()):
        raise ValueError('Invalid published transport statistic')
    return int(result) if integer else str(result)


def main():
    record, path = source(SID, 'population')
    common = dict(source='observed', source_id=SID, source_sha256=record['sha256'],
                  publication_edition='2025-26', status='dated_published_aggregate_not_current_operating_input')
    text = page_text(path, 219)
    if not all(s in text for s in ('Table 9.27', 'As on 31st March', '2024', '2025', 'Average effective km')):
        raise ValueError('Bus control table header changed')
    body = text.split('Table 9.27', 1)[1].split('Source:', 1)[0]
    token = r'(\d[\d,]*(?:\.\d+)?|-)'
    pattern = re.compile(r'^\s*([A-Za-z].+?)\s+' + r'\s+'.join([token]*6) + r'\s*$')
    operators = []
    for line in body.splitlines():
        match = pattern.fullmatch(line)
        if match:
            operators.append([match[1].strip(), list(match.groups()[1:])])
        elif line.strip() == 'Mahamandal Ltd.':
            if not operators or operators[-1][0] != 'Pune Mahanagar Parivahan':
                raise ValueError('Unattached wrapped provider name')
            operators[-1][0] += ' ' + line.strip()
    if len(operators) != 17 or len({name for name, _ in operators}) != len(operators):
        raise ValueError('Bus provider coverage changed')
    bus = []
    for name, cells in operators:
        for i, year in enumerate((2024, 2025)):
            bus.append(dict(**common, source_pdf_page=219, source_table='9.27', provider=name,
                            reference_date_as_printed=str(year) + '-03-31',
                            averaging_period='not_explicit_beyond_as_on_date_in_table_heading',
                            average_vehicles_on_road_per_day_count=number(cells[i], integer=True),
                            average_passengers_per_day_lakh=number(cells[2+i]),
                            average_effective_km_per_day_lakh=number(cells[4+i]),
                            missing_value_marker='-'))
    text = ' '.join(page_text(path, 221).split())
    paragraph = text.split('9.29 Mumbai Suburban Railway:', 1)[1]
    match = re.search(r'During (\d{4}-\d{2}), daily fleet of (\d+) local trains including (\d+) AC local trains '
                      r'was deployed to operate ([\d,]+) train services of which (\d+) were AC services\. '
                      r'On an average the system carried (\d+(?:\.\d+)?) lakh passengers per day\.', paragraph)
    if not match:
        raise ValueError('Suburban railway statistical paragraph changed')
    period, fleet, ac_fleet, services, ac_services, passengers = match.groups()
    rail = [dict(**common, source_pdf_page=221, source_section='9.29',
                 service_universe='Mumbai suburban Western and Central including Harbour and Trans Harbour',
                 reference_financial_year=period, daily_fleet_local_trains_count=int(fleet),
                 of_which_ac_local_trains_count=int(ac_fleet),
                 train_services_count=int(services.replace(',', '')),
                 of_which_ac_services_count=int(ac_services),
                 average_passengers_per_day_lakh=passengers,
                 passenger_count_definition='not_resolved_as_unique_people_journeys_or_boardings')]
    if rail[0]['of_which_ac_local_trains_count'] > rail[0]['daily_fleet_local_trains_count'] or (
            rail[0]['of_which_ac_services_count'] > rail[0]['train_services_count']):
        raise ValueError('AC subset exceeds reported fleet or service total')
    write('economic_survey_bus_controls.csv', bus)
    write('economic_survey_suburban_rail_controls.csv', rail)
    audit = dict(source='derived', source_id=SID, source_sha256=record['sha256'],
                 bus_provider_count=len(operators), bus_rows=len(bus), rail_rows=len(rail),
                 bus_missing_cells=sum(r[k] is None for r in bus for k in (
                     'average_vehicles_on_road_per_day_count', 'average_passengers_per_day_lakh',
                     'average_effective_km_per_day_lakh')),
                 bus_rows_by_reference_date=dict(sorted(Counter(r['reference_date_as_printed'] for r in bus).items())),
                 rail_ac_subsets_within_totals=True,
                 limitations=['Bus table dates are retained as printed; the averaging period and day-type weights are not defined.',
                              'A dash is missing, not zero. Ulhasnagar has missing 2024 cells and reported 2025 cells.',
                              'Vehicles on road per day are neither registered fleet size nor vehicle-by-trip assignments.',
                              'Passenger and effective-kilometre cells retain lakh units and their printed precision.',
                              'MSRTC city operations and other out-of-region providers must not be assigned wholly to MMR.',
                              'The suburban aggregate is for 2024-25, not a verified September 2026 timetable or train-formation inventory.',
                              'Aggregate passengers cannot be matched to simulation legs until the counting definition is reconciled.'])
    Path(city.path('data/processed/acquisition/economic_survey_transport_audit.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ('bus_provider_count', 'bus_rows', 'rail_rows', 'bus_missing_cells')}))


if __name__ == '__main__':
    main()
