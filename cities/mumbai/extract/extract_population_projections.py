"""Extract published state projections with their dates, units and rounding."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/state_population_projections.csv': ['data/raw/population/nhm_population_projection_2019_*.pdf'],
    'data/processed/observed/state_age_population_projections.csv': ['data/raw/population/nhm_population_projection_2019_*.pdf'],
    'data/processed/observed/state_age_population_projection_shares.csv': ['data/raw/population/nhm_population_projection_2019_*.pdf'],
    'data/processed/acquisition/state_population_projection_audit.json': ['data/raw/population/nhm_population_projection_2019_*.pdf'],
}
SID = 'nhm_population_projection_2019'
# Source table locations, not model parameters. Each header is checked below.
ANNUAL = ((52, 8, '03-01', 'Total'), (65, 9, '03-01', 'Urban'),
          (91, 11, '07-01', 'Total'), (104, 12, '07-01', 'Urban'),
          (130, 14, '10-01', 'Total'), (143, 15, '10-01', 'Urban'))
SEX = ('persons', 'male', 'female')
QUANTUM = Decimal('1')  # Integer thousands in the source count tables.


def page_text(path, page):
    return subprocess.run(['pdftotext', '-layout', '-f', str(page), '-l', str(page),
                           str(path), '-'], check=True, capture_output=True, encoding='utf-8').stdout


def values(tokens):
    if not all(re.fullmatch(r'\d[\d,]*(?:\.\d+)?', token) for token in tokens):
        raise ValueError('Non-numeric projection cell')
    return [Decimal(token.replace(',', '')) for token in tokens]


def evidence(record, page, table):
    return dict(source='modelled', source_id=SID, source_sha256=record['sha256'],
                source_pdf_page=page, source_table=table, publisher_edition='November 2019',
                area_name='Maharashtra', geography_level='state',
                status='published_projection_or_smoothed_baseline_not_city_observation')


def audit_identity(checks, name, key, total, parts, quantum=QUANTUM):
    delta = total - sum(parts)
    # Each independently rounded term contributes half its printed quantum.
    bound = quantum * Decimal(len(parts) + 1) / 2
    checks.append(dict(check=name, key=key, delta_in_printed_units=str(delta),
                       rounding_bound_in_printed_units=str(bound),
                       status='exact' if delta == 0 else 'rounding_compatible' if abs(delta) <= bound
                       else 'source_disagreement'))


def annual(record, path):
    rows = []
    for page, table, month_day, residence in ANNUAL:
        text = page_text(path, page)
        if not re.search(r'TABLE\s*[-–]\s*' + str(table) + r'\b', text):
            raise ValueError('Annual projection table header changed')
        if not re.search(r'GUJARAT\s+MAHARASHTRA\s+ANDHRA PRADESH', text):
            raise ValueError('Annual projection state column order changed')
        month = {'03-01': 'March', '07-01': 'July', '10-01': 'October'}[month_day]
        if not re.search(r'1\s*st\s+' + month, text):
            raise ValueError('Annual projection reference date changed')
        page_rows = []
        for line in text.splitlines():
            match = re.fullmatch(r'\s*(20\d{2})\s+(.+?)\s*', line)
            if not match:
                continue
            cells = match[2].split()
            if len(cells) != 9:
                raise ValueError('Unexpected annual projection row width')
            counts = values(cells)[3:6]
            if any(n != n.to_integral_value() for n in counts):
                raise ValueError('Count table is not integer thousands')
            page_rows.append(dict(**evidence(record, page, table),
                                  reference_date=match[1] + '-' + month_day, residence=residence,
                                  **{sex + '_thousands_count': int(n) for sex, n in zip(SEX, counts, strict=True)}))
        if [r['reference_date'][:4] for r in page_rows] != [str(y) for y in range(2011, 2037)]:
            raise ValueError('Annual projection year coverage changed')
        rows.extend(page_rows)
    return rows


def age_table(record, path, page, table, unit):
    text = page_text(path, page)
    if ('MAHARASHTRA' not in text or not re.search(r'TABLE\s*-\s*' + str(table) + r'\b', text)):
        raise ValueError('Age projection table header changed')
    rows, years, headers = [], None, []
    for line in text.splitlines():
        header = re.fullmatch(r'\s*(?:Age(?:\s+group)?\s+)?(20\d{2})\s+(20\d{2})\s+(20\d{2})\s*', line)
        if header:
            years = list(map(int, header.groups()))
            headers.extend(years)
            continue
        match = re.fullmatch(r'\s*(\d+-\d+|\d+\+|Total|\d+)\s+(.+?)\s*', line)
        if not match or years is None:
            continue
        age, cells = match[1], match[2].split()
        if len(cells) != 9 or not all(re.fullmatch(r'\d[\d,]*(?:\.\d+)?', c) for c in cells):
            continue
        # Exclude the printed column-number row.
        if age == '1':
            continue
        parsed = values(cells)
        if unit != 'percent' and any(n != n.to_integral_value() for n in parsed):
            raise ValueError('Count table is not integer thousands')
        for column, year in enumerate(years):
            row = dict(**evidence(record, page, table), reference_date=str(year) + '-03-01',
                       age_label=age, age_partition='supplementary_overlapping' if age == '0-1'
                       else 'total' if age == 'Total' else 'single_year' if age.isdigit() else 'five_year_or_open')
            row.update({sex + '_' + unit: str(n) if unit == 'percent' else int(n)
                        for sex, n in zip(SEX, parsed[column*3:column*3+3], strict=True)})
            rows.append(row)
    if headers != list(range(2011, 2037, 5)):
        raise ValueError('Age projection year headings changed')
    expected = ({'0-1', 'Total', '80+'} | {str(a) + '-' + str(a+4) for a in range(0, 80, 5)}) if table == 18 else (
        {'Total', '80+'} | {str(a) + '-' + str(a+4) for a in range(0, 80, 5)}) if table == 19 else (
        {'Total'} | {str(a) for a in range(5, 24)})
    for year in headers:
        labels = [r['age_label'] for r in rows if r['reference_date'].startswith(str(year))]
        if set(labels) != expected or len(labels) != len(expected):
            raise ValueError('Missing or duplicated age labels')
    return rows


def main():
    record, path = source(SID, 'population')
    if 'November, 2019' not in page_text(path, 1):
        raise ValueError('Projection edition changed')
    population = annual(record, path)
    ages = age_table(record, path, 234, 18, 'thousands_count')
    single = age_table(record, path, 236, 20, 'thousands_count')
    shares = age_table(record, path, 235, 19, 'percent')
    checks = []
    for row in population + ages + single:
        key = {k: row[k] for k in ('source_table', 'reference_date', 'residence', 'age_label') if k in row}
        audit_identity(checks, 'sex_sum', key, Decimal(row['persons_thousands_count']),
                       [Decimal(row[s + '_thousands_count']) for s in SEX[1:]])
    by_annual = {(r['reference_date'], r['residence']): r for r in population}
    by_age = {(r['reference_date'], r['age_label']): r for r in ages}
    by_single = {(r['reference_date'], r['age_label']): r for r in single}
    for date in sorted({r['reference_date'] for r in population}):
        for sex in SEX:
            if by_annual[date, 'Urban'][sex + '_thousands_count'] > by_annual[date, 'Total'][sex + '_thousands_count']:
                raise ValueError('Projected urban population exceeds total')
    for date in sorted({r['reference_date'] for r in ages}):
        for sex in SEX:
            field = sex + '_thousands_count'
            total = by_age[date, 'Total'][field]
            if total != by_annual[date, 'Total'][field]:
                raise ValueError('Annual and age table totals disagree')
            audit_identity(checks, 'age_partition_sum', dict(reference_date=date, sex=sex), Decimal(total),
                           [Decimal(r[field]) for r in ages if r['reference_date'] == date
                            and r['age_partition'] == 'five_year_or_open'])
            if by_age[date, '0-1'][field] > by_age[date, '0-4'][field]:
                raise ValueError('Supplementary youngest-age count exceeds its containing age group')
            share_rows = [r for r in shares if r['reference_date'] == date]
            audit_identity(checks, 'age_share_partition_sum', dict(reference_date=date, sex=sex),
                           next(Decimal(r[sex + '_percent']) for r in share_rows if r['age_label'] == 'Total'),
                           [Decimal(r[sex + '_percent']) for r in share_rows if r['age_label'] != 'Total'],
                           quantum=Decimal('.1'))
            audit_identity(checks, 'single_age_sum', dict(reference_date=date, sex=sex),
                           Decimal(by_single[date, 'Total'][field]),
                           [Decimal(by_single[date, str(a)][field]) for a in range(5, 24)])
            for lower in (5, 10, 15):
                label = str(lower) + '-' + str(lower+4)
                audit_identity(checks, 'single_to_group_sum', dict(reference_date=date, sex=sex, age_label=label),
                               Decimal(by_age[date, label][field]),
                               [Decimal(by_single[date, str(a)][field]) for a in range(lower, lower+5)])
    # Table 20 omits the unit in its own title. Retain this explicitly inferred
    # unit only if all comparable whole age groups reconcile with Table 18.
    if any(c['status'] == 'source_disagreement' for c in checks if c['check'] == 'single_to_group_sum'):
        raise ValueError('Cannot establish the unit of the single-age table')
    for r in ages:
        r['unit_basis'] = 'printed_table_18_heading'
    for r in single:
        r['unit_basis'] = 'derived_by_reconciliation_to_table_18_thousands_not_printed_in_table_20_title'
    for row in shares:
        for sex in SEX:
            numerator = Decimal(by_age[row['reference_date'], row['age_label']][sex + '_thousands_count'])
            denominator = Decimal(by_age[row['reference_date'], 'Total'][sex + '_thousands_count'])
            printed = Decimal(row[sex + '_percent'])
            low = (numerator - QUANTUM/2) / (denominator + QUANTUM/2) * 100
            high = (numerator + QUANTUM/2) / (denominator - QUANTUM/2) * 100
            checks.append(dict(check='age_share', key=dict(reference_date=row['reference_date'], sex=sex, age_label=row['age_label']),
                               status='rounding_compatible' if low <= printed + Decimal('.05') and high >= printed - Decimal('.05')
                               else 'source_disagreement'))
    write('state_population_projections.csv', population)
    write('state_age_population_projections.csv', ages + single)
    write('state_age_population_projection_shares.csv', shares)
    audit = dict(source='derived', source_id=SID, source_sha256=record['sha256'],
                 annual_rows=len(population), age_count_rows=len(ages + single), age_share_rows=len(shares),
                 checks=checks, check_status_counts=dict(sorted(Counter(c['status'] for c in checks).items())),
                 limitations=['State projections do not observe Mumbai or district population.',
                              'Reference dates are distinct; March, July and October are not interchangeable.',
                              'Count units are thousands and have been retained without asserting person-level precision.',
                              'The 0-1 row overlaps 0-4 and is excluded from age partition sums.',
                              'The 2011 age distribution is smoothed; it is not the raw single-age census distribution.',
                              'No state growth rate or age profile has been imposed on a city population.'])
    Path(city.path('data/processed/acquisition/state_population_projection_audit.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ('annual_rows', 'age_count_rows', 'age_share_rows', 'check_status_counts')}))


if __name__ == '__main__':
    main()
