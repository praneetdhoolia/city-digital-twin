"""Retain directional ADT, peak counts and rounded vehicle shares separately."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

SID = 'bmc_coastal_traffic_peer_review_2016'
OUTPUT_INPUTS = {
    'data/processed/observed/coastal_2016_daily_counts.csv': [
        'data/raw/traffic/bmc_coastal_traffic_peer_review_2016_*.pdf',
        'extract/transcriptions/coastal_2016_daily_counts.json'],
    'data/processed/observed/coastal_2016_peak_counts.csv': [
        'data/raw/traffic/bmc_coastal_traffic_peer_review_2016_*.pdf',
        'extract/transcriptions/coastal_2016_daily_counts.json'],
    'data/processed/observed/coastal_2016_peak_vehicle_shares.csv': [
        'data/raw/traffic/bmc_coastal_traffic_peer_review_2016_*.pdf',
        'extract/transcriptions/coastal_2016_daily_counts.json'],
    'data/processed/acquisition/coastal_2016_traffic_count_audit.json': [
        'data/raw/traffic/bmc_coastal_traffic_peer_review_2016_*.pdf',
        'extract/transcriptions/coastal_2016_daily_counts.json'],
}


def common(record):
    return dict(source='observed', source_id=SID, source_sha256=record['sha256'],
                survey_month='2016-01', count_survey_days=7,
                exact_survey_dates='not_reported_in_section',
                site_georeferencing='unresolved',
                target_status='historical_selected_sites_not_current_or_regionwide_target')


def daily(path, record):
    spec = json.loads(Path(city.path('extract/transcriptions/coastal_2016_daily_counts.json')).read_text(encoding='utf-8'))
    if spec['source_id'] != SID or spec['source_sha256'] != record['sha256']:
        raise ValueError('Daily-count transcription belongs to another source')
    text = '\n'.join(page_text(path, page) for page in spec['source_pdf_pages'])
    available = Counter(int(value) for value in re.findall(r'\b\d{4,6}\b', text))
    required = Counter(value for row in spec['rows'] for value in (row[3], row[5], row[6]))
    if required - available:
        raise ValueError('A transcribed daily count is absent from the PDF text')
    sites, rows, checks = {}, [], []
    for cells in spec['rows']:
        if len(cells) != len(spec['columns']):
            raise ValueError('Incomplete daily-count transcription')
        row = dict(zip(spec['columns'], cells))
        sid = row['site_id']
        if sid in sites:
            raise ValueError('Duplicate traffic count site')
        sites[sid] = row['location']
        counts = [row[key] for key in ('direction_1_adt_vehicles_per_day',
                                      'direction_2_adt_vehicles_per_day',
                                      'printed_total_adt_vehicles_per_day')]
        if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in counts):
            raise ValueError('Invalid daily traffic observation')
        delta = counts[2] - sum(counts[:2])
        # Three independently rounded integer vehicle/day means: this is an
        # arithmetic compatibility bound, not survey uncertainty.
        bound = Decimal(len(counts)) / 2
        status = 'exact' if delta == 0 else 'rounding_compatible' if abs(delta) <= bound else 'source_disagreement'
        checks.append(dict(site_id=sid, printed_total_vehicles_per_day=counts[2],
                           directional_sum_vehicles_per_day=sum(counts[:2]),
                           residual_vehicles_per_day=delta,
                           integer_rounding_envelope_vehicles_per_day=str(bound), status=status))
        for component, direction, count in (
            ('direction_1', row['direction_1'], counts[0]),
            ('direction_2', row['direction_2'], counts[1]),
            ('printed_total', 'both_reported_directions', counts[2]),
        ):
            rows.append(dict(**common(record), source_table='4-3', source_pdf_pages='43;44',
                             site_id=sid, location=row['location'], component=component,
                             direction=direction, adt_vehicles_per_day=count,
                             source_total_check=status,
                             aggregation='seven_day_average_daily_traffic_not_annual_average'))
    return sites, rows, checks


def crop(path, page, left):
    # PDF layout crop in points, not geographical coordinates.
    return subprocess.run(['pdftotext', '-layout', '-f', str(page), '-l', str(page),
                           '-x', str(left), '-y', '0', '-W', '420', '-H', '600', str(path), '-'],
                          check=True, capture_output=True, encoding='utf-8').stdout


def peaks(path, record, sites):
    rows = []
    # Table 4-4 follows Table 4-3's site order across two columns/pages.
    for page, left, site_ids in ((48, 420, range(1, 11)), (49, 0, range(11, 18))):
        body = crop(path, page, left).split('As can be observed', 1)[0]
        if 'Average Peak Traffic (Vehicles/hour)' not in body:
            raise ValueError('Peak count table units changed')
        starts = re.findall(r'(\d\d:\d\d)-\s+(\d\d:\d\d)-', body)
        ends = re.findall(r'(?<![\d:])(\d\d:\d\d)(?![-\d:])\s+(\d\d:\d\d)(?![-\d:])', body)
        values = re.findall(r'^.*?\b(\d{4,6})\s+(\d{4,6})\s*$', body, re.M)
        if not len(starts) == len(ends) == len(values) == len(site_ids):
            raise ValueError('Peak time/value row coverage changed')
        for sid, begin, finish, counts in zip(site_ids, starts, ends, values):
            for period, start, end, count in zip(('morning', 'evening'), begin, finish, counts):
                minutes = lambda t: int(t[:2]) * 60 + int(t[3:])
                if minutes(end) - minutes(start) != 60:
                    raise ValueError('Expected printed one-hour peak interval')
                rows.append(dict(**common(record), source_table='4-4', source_pdf_page=page,
                                 site_id=sid, location=sites[sid], period=period,
                                 local_start_time=start, local_end_time=end,
                                 average_peak_vehicles_per_hour=int(count),
                                 direction_scope='not_broken_out_by_direction_in_table',
                                 aggregation='average_peak_hour_not_saturation_capacity'))
    return rows


def shares(path, record, sites):
    body = page_text(path, 50)
    blocks = (
        ('4-5', body.split('Table 4-5', 1)[1].split('Table 4-6', 1)[0], range(1, 9),
         ('Two Wheelers', 'Cars/Jeep/Van', 'Taxi', 'Bus', 'Goods Vehicles')),
        ('4-6', body.split('Table 4-6', 1)[1], range(9, 18),
         ('Two Wheelers', 'Three Wheelers', 'Cars/Jeep/Van', 'Taxi', 'Mini Bus', 'Bus', 'Goods Temp')),
    )
    rows, checks = [], []
    for table, block, site_ids, expected_modes in blocks:
        if 'Traffic Composition of Average Peak Hour Traffic' not in block:
            raise ValueError('Vehicle-share table heading changed')
        parsed = re.findall(r'^\s*(.+?)\s+((?:\d+%\s*)+)\s*$', block, re.M)
        if tuple(label.strip() for label, _ in parsed) != expected_modes:
            raise ValueError('Published mode categories changed')
        totals = Counter()
        for label, raw in parsed:
            values = [int(value) for value in re.findall(r'(\d+)%', raw)]
            if len(values) != len(site_ids) or any(not 0 <= value <= 100 for value in values):
                raise ValueError('Invalid vehicle-share coverage or value')
            for sid, value in zip(site_ids, values):
                totals[sid] += value
                rows.append(dict(**common(record), source_table=table, source_pdf_page=50,
                                 site_id=sid, location=sites[sid], vehicle_class_as_printed=label.strip(),
                                 published_share_percent=value, published_precision_percent=1,
                                 zero_cell_status='rounded_zero_not_proven_absence' if value == 0 else 'nonzero',
                                 peak_and_direction_scope='not_split_by_morning_evening_or_direction',
                                 count_derivation_status='not_multiplied_by_daily_or_period_specific_counts'))
        for sid in site_ids:
            delta = totals[sid] - 100
            bound = Decimal(len(expected_modes)) / 2
            checks.append(dict(table=table, site_id=sid, published_sum_percent=totals[sid],
                               residual_percentage_points=delta, whole_percent_rounding_envelope=str(bound),
                               status='exact' if delta == 0 else 'rounding_compatible' if abs(delta) <= bound else 'source_disagreement'))
    return rows, checks


def main():
    record, path = source(SID, 'traffic')
    survey = ' '.join(page_text(path, 39).split())
    if not all(text in survey for text in ('seven days in the month of January, 2016', '7 (24 Hrs.)', '1 (12 Hrs.)')):
        raise ValueError('Survey period or duration changed')
    sites, daily_rows, daily_checks = daily(path, record)
    peak_rows = peaks(path, record, sites)
    share_rows, share_checks = shares(path, record, sites)
    write('coastal_2016_daily_counts.csv', daily_rows)
    write('coastal_2016_peak_counts.csv', peak_rows)
    write('coastal_2016_peak_vehicle_shares.csv', share_rows)
    audit = dict(source_id=SID, source_sha256=record['sha256'],
                 sites=len(sites), daily_rows=len(daily_rows), peak_rows=len(peak_rows), share_rows=len(share_rows),
                 daily_total_checks=daily_checks, share_sum_checks=share_checks,
                 source_categories_not_imputed=True,
                 limitations=[
                     'Counts are vehicle passages at selected influence-area sites, not unique vehicles, people or a citywide mode split.',
                     'Directional rows and printed totals overlap; they must not be summed as independent counts.',
                     'Whole-percent zeroes do not establish zero traffic; absent categories in a table remain absent.',
                     'Goods Temp and Goods Vehicles are distinct source labels; no heavy/light freight split is inferred.',
                     'Peak shares are not assigned to morning/evening or directions, and are not used to manufacture modal daily counts.',
                     'Source disagreements are retained without choosing or correcting a value.',
                     'No historical count has been adopted as a 2026 target or extrapolated using an assumed growth rate.',
                 ])
    Path(city.path('data/processed/acquisition/coastal_2016_traffic_count_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('sites', 'daily_rows', 'peak_rows', 'share_rows')}))
    print(json.dumps([check for check in daily_checks + share_checks if check['status'] == 'source_disagreement']))


if __name__ == '__main__':
    main()
