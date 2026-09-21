"""Extract dated Navi Mumbai Metro observations without importing other cities."""
import json
from pathlib import Path
import re

from pypdf import PdfReader
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/navi_metro_reported_controls.csv': ['data/raw/transit/mahametro_current_annual_*.pdf'],
    'data/processed/acquisition/navi_metro_controls_audit.json': ['data/raw/transit/mahametro_current_annual_*.pdf'],
}


def main():
    rows = []
    source_id = 'mahametro_current_annual_2024_25'
    record, path = source(source_id, 'transit')
    pages = PdfReader(path).pages
    text = ' '.join(pages[29].extract_text().split())
    section = text.split('Navi Mumbai Metro Line I', 1)[1].split('5. ROLLING STOCK', 1)[0]
    growth = re.search(r'from ([\d,]+) in April 2024 to ([\d,]+) in March 2025, representing a growth of (\d+)%', section)
    event = re.search(r'(\d+) additional revenue trips and (\d+) supplementary trips beyond regular service hours.*?([\d,]+) passengers', section)
    headway = re.search(r'(\d+)-minute intervals during peak hours and (\d+)-minute intervals during non-peak hours', section)
    if not all((growth, event, headway)):
        raise ValueError('Published operating paragraph changed')

    def add(metric, value, unit, period, precision, page=30):
        rows.append(dict(source_id=source_id, source_sha256=record['sha256'], source_page=page,
                         operator='Maha Metro for CIDCO', line='Navi Mumbai Metro Line 1',
                         measure=metric, value_in_stated_unit=value, stated_unit=unit,
                         period_or_effective_date=period, precision_note=precision,
                         source='operator_reported', validation_status='historical_source_not_current_calibration_target'))

    first, last, published_growth = [int(v.replace(',', '')) for v in growth.groups()]
    add('average_daily_ridership', first, 'passenger_journeys_per_day', '2024-04', 'Published integer daily average; underlying total not supplied here.')
    add('average_daily_ridership', last, 'passenger_journeys_per_day', '2025-03', 'Published integer daily average; underlying total not supplied here.')
    add('claimed_ridership_growth', published_growth, 'percent', '2024-04 to 2025-03', 'Conflicts with arithmetic from the two reported averages.')
    additional, supplementary, passengers = [int(v.replace(',', '')) for v in event.groups()]
    add('ijtema_extra_revenue_trips', additional, 'train_trips', '2025-02-02', 'Special-event addition; not a regular-day schedule.')
    add('ijtema_extra_trips_beyond_hours', supplementary, 'train_trips', '2025-02-02', 'Special-event addition; not a regular-day schedule.')
    add('ijtema_ridership', passengers, 'passenger_journeys', '2025-02-02', 'Event-day count; not an average day.')
    for label, value in zip(('peak', 'non_peak'), headway.groups()):
        add(label + '_headway', int(value), 'minutes', 'effective 2025-01-20', 'Peak-period clock boundaries and later amendments not supplied in this paragraph.')
    calculated_growth = (last / first - 1) * 100
    # The same numbers appear in the highlights; repetition is a consistency
    # check within one publication, not independent corroboration.
    highlight = ' '.join(pages[22].extract_text().split()).split('Navi Mumbai Metro Line 1', 1)[1].split('Thane Integral Ring Metro', 1)[0]
    repeated = re.search(growth.re, highlight)
    if not repeated or repeated.groups() != growth.groups():
        raise ValueError('Highlights and operating section disagree')

    source_id = 'mahametro_current_annual_2023_24'
    record, path = source(source_id, 'transit')
    text = ' '.join(PdfReader(path).pages[22].extract_text().split())
    section = text.split('Navi Mumbai Metro Line', 1)[1].split('5. ROLLING STOCK', 1)[0]
    ridership = re.search(r'ridership of ([\d.]+) million passengers', section)
    revenue = re.search(r'farebox revenue of\s*[^\d]*([\d.]+) crore', section)
    operation = re.search(r'headway of (\d+) minutes.*?total of (\w+) trains from (\d{2}:\d{2}) to (\d{2}:\d{2})', section)
    performance = re.search(r'availability is ([\d.]+)%.*?punctuality rate is ([\d.]+)%', section)
    if not all((ridership, revenue, operation, performance)) or operation.group(2) != 'five':
        raise ValueError('Unexpected initial-operation paragraph')
    period = '2023-11-17 to 2024-03-31 (FY 2023-24 operation)'
    add('ridership', ridership.group(1), 'million_passenger_journeys', period, 'Rounded to two decimal million; do not treat as an exact integer count.', 23)
    add('farebox_revenue', revenue.group(1), 'crore_INR', period, 'Rounded published monetary value.', 23)
    add('reported_headway', int(operation.group(1)), 'minutes', 'FY 2023-24 report', 'Historical operating description.', 23)
    add('trains_utilised', 5, 'trains', 'FY 2023-24 report', 'Trains utilised, not a verified total fleet or seating capacity.', 23)
    for label, value in zip(('first_service_clock', 'last_service_clock'), operation.groups()[2:]):
        add(label, value, 'local_hhmm', 'FY 2023-24 report', 'Historical operating window; direction and calendar exceptions unresolved.', 23)
    for label, value in zip(('train_availability', 'punctuality'), performance.groups()):
        add(label, value, 'percent', 'FY 2023-24 report', 'Operator statistic; measurement definition needs confirmation.', 23)
    write('navi_metro_reported_controls.csv', rows)
    audit = dict(schema_version=1, rows=len(rows), repeated_ridership_figures_agree=True,
                 growth_check=dict(published_percent=published_growth, calculated_percent=calculated_growth,
                                   derived_from='(March 2025 reported daily average / April 2024 reported daily average - 1) * 100',
                                   agrees_to_published_integer=round(calculated_growth) == published_growth),
                 limits='Historical reports. No current departures, peak clock bands, fares, rolling-stock capacity, station-level demand or representative-date target is established. Event service remains separate from regular service. Other cities in the corporate reports are excluded.')
    Path(city.path('data/processed/acquisition/navi_metro_controls_audit.json')).write_text(json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
