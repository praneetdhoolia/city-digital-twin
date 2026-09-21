"""Extract dated classified counts; keep legal-speed density proxies separate."""
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
import base64
import hashlib
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

OUTPUT_INPUTS = {
    'data/processed/observed/jvlr_journal_classified_counts.csv': ['data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf'],
    'data/processed/observed/jvlr_journal_road_controls.csv': ['data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf'],
    'data/processed/observed/jvlr_journal_pcu_factors.csv': ['data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf'],
    'data/processed/acquisition/jvlr_journal_audit.json': [
        'data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf',
        'data/raw/traffic/jvlr_conference_poster_2026_response_*.json',
        'extract/jvlr_poster_transcription.json'],
}
SID = 'jvlr_traffic_study_2026_pdf'
COUNT_COLUMNS = ('cars_vehicles_h', 'two_wheelers_vehicles_h', 'auto_vehicles_h',
                 'truck_vehicles_h', 'tempo_vehicles_h', 'bus_vehicles_h',
                 'cycle_vehicles_h', 'pedestrians_persons_h', 'published_flow_pcu_h')
ROAD_COLUMNS = ('lanes_count', 'official_reference_speed_kmh', 'published_flow_pcu_h',
                'flow_pcu_h_lane', 'los_flow', 'indicative_density_pcu_km',
                'indicative_density_pcu_km_lane', 'los_density')


def clock(text, period):
    return datetime.strptime(text + period.replace('.', '').upper(), '%I:%M%p').strftime('%H:%M:%S')


def main():
    record, path = source(SID, 'traffic')
    methods = page_text(path, 5) + page_text(path, 6)
    dates = re.search(r'from\s+(\d+ June 2025) \(Monday\) to (\d+ June 2025) \(Sunday\)', methods)
    selected = re.search(r'Tuesday, (\d+ June 2025), was selected', methods)
    if not dates or not selected or 'highest aggregate traffic volume' not in methods:
        raise ValueError('Survey timing or peak-day selection method changed')
    to_date = lambda text: datetime.strptime(text, '%d %B %Y').date().isoformat()
    common = dict(source_id=SID, source_sha256=record['sha256'], survey_date=to_date(selected[1]),
                  survey_start_date=to_date(dates[1]), survey_end_date=to_date(dates[2]),
                  time_basis='published_local_clock_times_no_UTC_conversion',
                  day_selection='highest_aggregate_volume_day_in_seven_day_survey',
                  calibration_status='requires_2025_scenario_and_count_line_matching')
    factor_text = page_text(path, 4).split('Table 1. PCU Standards.', 1)[1].split('Source:', 1)[0]
    factors = []
    for line in factor_text.splitlines():
        match = re.fullmatch(r'\s*(\d+)\s+(.+?)\s+(\d+\.\d+)\s*', line)
        if match:
            factors.append(dict(source='literature', source_id=SID, source_sha256=record['sha256'],
                                source_pdf_page=4, source_table='1', source_row=match[1],
                                vehicle_categories=match[2], pcu_equivalency_factor=match[3],
                                purpose='reproduce_published_count_conversion_not_local_dynamic_pce'))
    weights = {}
    for row in factors:
        label, value = row['vehicle_categories'], Decimal(row['pcu_equivalency_factor'])
        if label.startswith('Passenger car, tempo, auto,'):
            weights.update({key: value for key in ('cars_vehicles_h', 'tempo_vehicles_h', 'auto_vehicles_h')})
        elif label.startswith('Truck, bus,'):
            weights.update({key: value for key in ('truck_vehicles_h', 'bus_vehicles_h')})
        elif label.startswith('Motor-cycle, scooter and cycle'):
            weights.update({key: value for key in ('two_wheelers_vehicles_h', 'cycle_vehicles_h')})
    if set(weights) != set(COUNT_COLUMNS[:-2]):
        raise ValueError('Published PCU categories do not cover the classified vehicle columns')
    text = page_text(path, 8).split('Table 3. PCU Calculation for Peak Hour.', 1)[1].split('Note:', 1)[0]
    number_tail = r'\s+'.join([r'(\d+)'] * len(COUNT_COLUMNS))
    pattern = re.compile(r'^\s*(\d+\.\d+)\s+(.*?)\s*(\d+:\d+)[–-](\d+:\d+)\s+(a\.m\.|p\.m\.)\s+' + number_tail + r'\s*$')
    counts, pending, site = [], '', None
    for line in text.splitlines():
        group = re.fullmatch(r'\s*(\d+)\s+([A-Za-z].+?)\s*', line)
        match = pattern.fullmatch(line)
        if group:
            site = group[2]
        elif match:
            row = dict(source='observed', **common, source_pdf_page=8, source_table='3',
                       row_id=match[1], site=site, road_label=(match[2].strip() or pending),
                       peak_start_time=clock(match[3], match[5]), peak_end_time=clock(match[4], match[5]))
            row.update(zip(COUNT_COLUMNS, (int(v) for v in match.groups()[5:])))
            if not site or not row['road_label'] or row['peak_end_time'] <= row['peak_start_time']:
                raise ValueError('Missing location or invalid count window')
            duration = (datetime.strptime(row['peak_end_time'], '%H:%M:%S') -
                        datetime.strptime(row['peak_start_time'], '%H:%M:%S'))
            if duration != timedelta(hours=1):
                raise ValueError('Count window is not one hour; hourly units need re-derivation')
            row['observation_duration_s'] = int(duration.total_seconds())
            row['pcu_flow_source'] = 'derived_from_classified_counts_using_table_1'
            counts.append(row)
            pending = ''
        elif line.strip().startswith('Road '):
            pending = line.strip()
        elif re.fullmatch(r'[A-Za-z ]+\)', line.strip()) and counts:
            counts[-1]['road_label'] += ' ' + line.strip()
    table4 = page_text(path, 11).split('Table 4.', 1)[1]
    road_pattern = re.compile(r'^\s*(\d+\.\d+)\s+.*?\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+(?:\.\d+)?)\s+([A-F])\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+([A-F])\s*$')
    roads = []
    index = {r['row_id']: r for r in counts}
    for line in table4.splitlines():
        match = road_pattern.fullmatch(line)
        if match:
            counted = index[match[1]]
            row = dict(source='literature', **common, source_pdf_page=11, source_table='4',
                       row_id=match[1], site=counted['site'], road_label=counted['road_label'],
                       speed_source='official_reference_limit_reported_by_paper_not_observed_speed',
                       density_source='flow_divided_by_reference_limit_not_observed_density')
            row.update(zip(ROAD_COLUMNS, match.groups()[1:]))
            roads.append(row)
    poster = json.loads(Path(city.path('extract/jvlr_poster_transcription.json')).read_text(encoding='utf-8'))
    poster_record, poster_path = source(poster['source_id'], 'traffic')
    poster_bytes = base64.b64decode(json.loads(poster_path.read_text(encoding='utf-8'))['fileContent'], validate=True)
    if hashlib.sha256(poster_bytes).hexdigest() != poster['poster_sha256']:
        raise ValueError('Version comparison transcription differs from the acquired poster')
    expected_ids = {r[0] for r in poster['rows']}
    if set(index) != expected_ids or len(index) != len(counts) or {r['row_id'] for r in roads} != expected_ids or len(roads) != len(expected_ids):
        raise ValueError('Classified count and physical-control rows do not cover the source stretches')
    checks = []
    for row in counts:
        calculated = sum(Decimal(row[key]) * weight for key, weight in weights.items())
        published = Decimal(row['published_flow_pcu_h'])
        checks.append(dict(row_id=row['row_id'], check='classified_counts_to_pcu',
                           calculated=str(calculated), published=str(published),
                           status='exact' if calculated == published else 'source_disagreement'))
    for row in roads:
        count = index[row['row_id']]['published_flow_pcu_h']
        checks.append(dict(row_id=row['row_id'], check='table_3_to_table_4_flow',
                           status='exact' if Decimal(row['published_flow_pcu_h']) == count else 'source_disagreement'))
    changes = []
    for values in poster['rows']:
        old = dict(zip(poster['columns'], values))
        new = next(r for r in roads if r['row_id'] == old['row_id'])
        for before, after in [('flow_pcu_h', 'published_flow_pcu_h'), ('los_flow', 'los_flow'), ('los_density', 'los_density')]:
            if old[before] != new[after]:
                changes.append(dict(row_id=old['row_id'], field=after, poster=old[before], journal=new[after]))
    out = Path(city.path('data/processed/observed'))
    for name, rows in [('classified_counts', counts), ('road_controls', roads), ('pcu_factors', factors)]:
        write(out / ('jvlr_journal_' + name + '.csv'), rows)
    report = dict(source='derived', **common, classified_count_rows=len(counts), road_control_rows=len(roads),
                  poster_source_sha256=poster_record['sha256'], poster_pdf_sha256=poster['poster_sha256'],
                  pcu_factor_rows=len(factors), checks=checks, check_status_counts=dict(Counter(r['status'] for r in checks)),
                  poster_to_journal_changes=changes,
                  limitations=[
                      'Each stretch has its own selected peak hour; summing rows does not give a simultaneous corridor flow.',
                      'Selected observations describe June 2025 peak periods, not 2026 or a full day.',
                      'Posted limits are reference speeds; derived densities cannot validate simulated speeds or densities.',
                      'PCU factors reproduce the publication; they are not measured local dynamic vehicle equivalents.',
                      'Exact count lines still need georeferencing to source maps and the mapped network.',
                      'The raw video and seven daily classified tables are not provided by these extracted tables.',
                      'Road inventory and temporal variability are extracted separately by extract_jvlr_inventory.py.',
                  ])
    Path(city.path('data/processed/acquisition/jvlr_journal_audit.json')).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('classified_count_rows', 'road_control_rows', 'pcu_factor_rows', 'check_status_counts')}))


if __name__ == '__main__':
    main()
