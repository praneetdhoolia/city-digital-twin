"""Retain dated municipal population estimates and their published conflicts.

These estimates are evidence for growth controls, not census observations or
MMR totals. Source labels and inconsistent subtotals are never corrected here.
"""
from collections import defaultdict
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/bmc_population_estimates.csv': [
        'data/raw/population/bmc_civic_diary_2025_*.pdf',
        'data/raw/population/bmc_civic_diary_2026_*.pdf',
        'data/raw/population/bmc_environment_report_2024_25_*.pdf'],
    'data/processed/acquisition/bmc_population_estimates_audit.json': [
        'data/raw/population/bmc_civic_diary_2025_*.pdf',
        'data/raw/population/bmc_civic_diary_2026_*.pdf',
        'data/raw/population/bmc_environment_report_2024_25_*.pdf'],
}
REGIONS = {
    'City': ('A', 'B', 'C', 'D', 'E', 'F/S', 'F/N', 'G/S', 'G/N'),
    'Western': ('H/E', 'H/W', 'K/E', 'K/W', 'P/S', 'P/N', 'R/S', 'R/C', 'R/N'),
    'Eastern': ('L', 'M/E', 'M/W', 'N', 'S', 'T'),
}
WARD_REGION = {ward: region for region, wards in REGIONS.items() for ward in wards}
DIARIES = (('bmc_civic_diary_2025', 78, 2023), ('bmc_civic_diary_2026', 87, 2025))
WARD_LABEL = r'[A-Z](?:\s*/\s*[A-Z])?'
INTEGER = r'\d[\d,]*'


def page_text(source_id, page):
    record, path = source(source_id, 'population')
    text = subprocess.run(['pdftotext', '-layout', '-f', str(page), '-l', str(page),
                           str(path), '-'], check=True, capture_output=True,
                          encoding='utf-8').stdout
    return record, text


def observation(source_id, record, page, year, area, population, area_km2=''):
    if area not in WARD_REGION and area not in REGIONS and area != 'Greater Mumbai':
        raise ValueError('Unexpected source area label: ' + area)
    return dict(source_id=source_id, source_sha256=record['sha256'], source_page_1_based=page,
                reference_year_as_printed=year, area_name=area,
                geography_level='administrative_ward' if area in WARD_REGION else 'subtotal',
                region=WARD_REGION.get(area, area), population_persons_count=population,
                area_km2=area_km2, source='published_municipal_estimate',
                status='source_conflicts_and_current_geography_unresolved',
                model_ready=False)


def read_diary(source_id, page, year):
    record, text = page_text(source_id, page)
    year_match = re.search(r'Mid\s+Year\s+Estimated\s+Population\s+Year\s*-\s*(\d{4})',
                           text, re.IGNORECASE)
    if not year_match or int(year_match.group(1)) != year:
        raise ValueError('Diary population reference year changed')
    body = text.split('WARDWISE POPULATION OF GREATER MUMBAI', 1)[1]
    pattern = re.compile(r'(?<!\S)(' + WARD_LABEL + r')\s+(' + INTEGER + r')(?!\S)')
    rows = []
    for line in body.splitlines():
        for match in pattern.finditer(line):
            area = re.sub(r'\s+', '', match.group(1))
            rows.append(observation(source_id, record, page, year, area,
                                    int(match.group(2).replace(',', ''))))
    if {r['area_name'] for r in rows} != set(WARD_REGION) or len(rows) != len(WARD_REGION):
        raise ValueError('Missing or duplicated diary ward cells')
    total_lines = [line for line in body.splitlines() if len(re.findall(r'\bTotal\b', line)) == len(REGIONS)]
    if len(total_lines) != 1:
        raise ValueError('Ambiguous diary subtotal row')
    totals = re.findall(r'\bTotal\s+(' + INTEGER + ')', total_lines[0])
    for region, count in zip(REGIONS, totals, strict=True):
        rows.append(observation(source_id, record, page, year, region, int(count.replace(',', ''))))
    grand = re.findall(r'TOTAL MUMBAI\s+(' + INTEGER + ')', body)
    if len(grand) != 1:
        raise ValueError('Ambiguous diary grand total')
    rows.append(observation(source_id, record, page, year, 'Greater Mumbai', int(grand[0].replace(',', ''))))
    return rows


def read_environment():
    source_id, page = 'bmc_environment_report_2024_25', 19
    record, text = page_text(source_id, page)
    body = text.split('Table No 4.2:', 1)[1].split('Source:', 1)[0]
    if not re.search(r'2024\s+2025', body):
        raise ValueError('Environment table years changed')
    labels = {'City Ward': 'City', 'Western Ward': 'Western',
              'Eastern Ward': 'Eastern', 'Brihanmumbai': 'Greater Mumbai'}
    pattern = re.compile(r'(?<!\S)(City Ward|Western Ward|Eastern Ward|Brihanmumbai|'
                         + WARD_LABEL + r')\s+(\d+\.\d+)\s+(\d+)\s+(\d+)(?!\S)')
    rows = []
    for match in pattern.finditer(body):
        label = match.group(1)
        area = labels.get(label, re.sub(r'\s+', '', label))
        for year, group in ((2024, 3), (2025, 4)):
            rows.append(observation(source_id, record, page, year, area,
                                    int(match.group(group)), match.group(2)))
    for year in (2024, 2025):
        selected = [r for r in rows if r['reference_year_as_printed'] == year]
        expected = set(WARD_REGION) | set(REGIONS) | {'Greater Mumbai'}
        if {r['area_name'] for r in selected} != expected or len(selected) != len(expected):
            raise ValueError('Missing or duplicated environmental population cells')
    return rows


def audit(rows):
    tables = defaultdict(dict)
    for row in rows:
        key = row['source_id'], row['reference_year_as_printed']
        if row['area_name'] in tables[key]:
            raise ValueError('Duplicate population estimate')
        tables[key][row['area_name']] = row['population_persons_count']
    checks = []
    for (sid, year), values in tables.items():
        for parent, children in list(REGIONS.items()) + [('Greater Mumbai', tuple(REGIONS))]:
            total = sum(values[child] for child in children)
            checks.append(dict(source_id=sid, reference_year_as_printed=year,
                               area_name=parent, sum_of_children_persons=total,
                               published_total_persons=values[parent],
                               difference_persons=total-values[parent]))
    shared_year = DIARIES[-1][2]
    diary = tables[(DIARIES[-1][0], shared_year)]
    environment = tables[('bmc_environment_report_2024_25', shared_year)]
    comparison = [dict(area_name=area, reference_year_as_printed=shared_year,
                       diary_persons=diary[area], environment_persons=environment[area],
                       diary_minus_environment_persons=diary[area]-environment[area])
                  for area in diary]
    return dict(status='published_estimates_with_unresolved_conflicts', rows=len(rows),
                subtotal_checks=checks, subtotal_disagreements=sum(c['difference_persons'] != 0 for c in checks),
                same_labelled_year_comparison=comparison,
                same_labelled_year_disagreements=sum(c['diary_minus_environment_persons'] != 0 for c in comparison),
                limitations=[
                    'Reference years remain as printed; apparent reuse of older figures is not silently relabelled.',
                    'Municipal estimates are not observed census counts and their estimation method is unresolved.',
                    'Administrative wards differ from Census wards and need a spatial crosswalk.',
                    'Greater Mumbai is only part of MMR; these controls do not cover the whole model extent.',
                    'Subtotals overlap their children and must not be summed together.',
                    'No projection to 2026 or assignment to model agents has been made.'])


def main():
    rows = [row for spec in DIARIES for row in read_diary(*spec)] + read_environment()
    result = audit(rows)
    write('bmc_population_estimates.csv', rows)
    Path(city.path('data/processed/acquisition/bmc_population_estimates_audit.json')).write_text(
        json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('rows', 'subtotal_disagreements',
                                                  'same_labelled_year_disagreements')}))


if __name__ == '__main__':
    main()
