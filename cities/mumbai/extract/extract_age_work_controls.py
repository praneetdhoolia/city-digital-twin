"""Reconcile historical single-year ages and Census work-status controls.

Census main/marginal work is not a full-time/part-time classification. Seeking
work categories overlap their parent categories and are retained separately.
"""
from collections import defaultdict
import csv
import json
from pathlib import Path

import city
from extract_census_controls import write
from extract_demographic_controls import workbook, sex_counts, evidence

OUTPUT_INPUTS = {
    'data/processed/observed/census_2011_single_year_ages.csv': [
        'data/raw/population/census_c13_maharashtra_*.xls',
        'data/processed/observed/census_2011_age_sex.csv'],
    'data/processed/observed/census_2011_work_status.csv': [
        'data/raw/population/census_b01_maharashtra_*.xls',
        'data/processed/observed/census_2011_single_year_ages.csv'],
    'data/processed/observed/_age_work_controls_audit.json': [
        'data/raw/population/census_c13_maharashtra_*.xls',
        'data/raw/population/census_b01_maharashtra_*.xls',
        'data/processed/observed/census_2011_age_sex.csv',
        'data/processed/observed/census_2011_leaf_controls.csv'],
}
FIELDS = ('persons_count', 'male_persons_count', 'female_persons_count')


def reconcile_leaf_work(work):
    """Check finer-area joint work controls against the independent B01 table."""
    with Path(city.path('data/processed/observed/census_2011_leaf_controls.csv')).open(
            encoding='utf-8', newline='') as stream:
        leaves = list(csv.DictReader(stream))
    categories = {
        'population': 'persons', 'main_worker': 'main_workers',
        'marginal_worker_under_3_months': 'marginal_workers_under_3_months',
        'marginal_worker_3_to_6_months': 'marginal_workers_3_to_6_months',
        'non_worker': 'non_workers',
    }
    checks = []
    for row in work:
        if row['age_band'] != 'Total':
            continue
        selected = [leaf for leaf in leaves if leaf['district_code'] == row['district_code']
                    and (row['residence'] == 'Total' or leaf['rural_urban'] == row['residence'])]
        for category, leaf_label in categories.items():
            for sex in ('', 'male_', 'female_'):
                value = sum(int(leaf[sex + leaf_label + '_count']) for leaf in selected)
                expected = row[category + '_' + sex + 'persons_count']
                if value != expected:
                    raise ValueError('PCA/B01 joint work mismatch: ' + str(
                        (row['district_code'], row['residence'], category, sex, value, expected)))
                checks.append(dict(district_code=row['district_code'], residence=row['residence'],
                                   category=category, sex=sex.rstrip('_') or 'all',
                                   pca_leaf_count=value, b01_count=expected))
    if not checks:
        raise ValueError('No B01 total-age rows found for joint work reconciliation')
    return checks


def matches(age, band):
    if band in ('All ages', 'Total'):
        return age != 'All ages'
    if band == 'Age not stated':
        return age == band
    if age in ('All ages', 'Age not stated'):
        return False
    if band.endswith('+'):
        return int(age.rstrip('+')) >= int(band[:-1])
    low, high = map(int, band.split('-'))
    return low <= int(age.rstrip('+')) <= high


def main():
    with Path(city.path('data/processed/observed/census_2011_age_sex.csv')).open(encoding='utf-8') as stream:
        grouped = list(csv.DictReader(stream))
    districts = {r['district_code'] for r in grouped}
    sid = 'census_c13_maharashtra'
    record, sheet = workbook(sid)
    if 'SINGLE YEAR AGE' not in str(sheet.cell_value(0, 4)):
        raise ValueError('Unexpected C13 workbook')
    ages, by_area = [], defaultdict(list)
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        if row[0] != 'C3713' or row[2] not in districts:
            continue
        age = str(int(row[4])) if isinstance(row[4], float) else row[4]
        for residence, col in [('Total', 5), ('Rural', 8), ('Urban', 11)]:
            result = dict(state_code=row[1], district_code=row[2], area_name=row[3],
                          residence=residence, age_years_or_band=age,
                          **sex_counts(row, col), **evidence(record, sid, i+1))
            ages.append(result)
            by_area[(row[2], residence)].append(result)
    expected = {str(i) for i in range(100)} | {'100+', 'Age not stated', 'All ages'}
    for rows in by_area.values():
        if len(rows) != len(expected) or {r['age_years_or_band'] for r in rows} != expected:
            raise ValueError('Missing or duplicated C13 ages')
    for row in grouped:
        selected = [r for r in by_area[(row['district_code'], row['residence'])]
                    if matches(r['age_years_or_band'], row['age_band'])]
        if any(sum(r[k] for r in selected) != int(row[k]) for k in FIELDS):
            raise ValueError('C13 and C14 age/sex controls differ')
    sid = 'census_b01_maharashtra'
    record, sheet = workbook(sid)
    if 'B-1 Main workers' not in str(sheet.cell_value(0, 5)):
        raise ValueError('Unexpected B01 workbook')
    columns = dict(population=6, main_worker=9, marginal_worker_under_3_months=12,
                   marginal_worker_3_to_6_months=15, marginal_worker_seeking_available=18,
                   non_worker=21, non_worker_seeking_available=24)
    work, seen = [], set()
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        if row[0] != 'B0101' or row[2] not in districts:
            continue
        key = (row[2], row[4], row[5])
        if key in seen:
            raise ValueError('Duplicated B01 control')
        seen.add(key)
        categories = {name: sex_counts(row, col) for name, col in columns.items()}
        for field in FIELDS:
            parts = ['main_worker', 'marginal_worker_under_3_months',
                     'marginal_worker_3_to_6_months', 'non_worker']
            if sum(categories[k][field] for k in parts) != categories['population'][field]:
                raise ValueError('B01 economic categories do not reconcile')
            marginal = sum(categories[k][field] for k in parts[1:3])
            if categories['marginal_worker_seeking_available'][field] > marginal:
                raise ValueError('Marginal worker subset exceeds parent')
            if categories['non_worker_seeking_available'][field] > categories['non_worker'][field]:
                raise ValueError('Non-worker subset exceeds parent')
            selected = [r for r in by_area[(row[2], row[4])]
                        if matches(r['age_years_or_band'], row[5])]
            if sum(r[field] for r in selected) != categories['population'][field]:
                raise ValueError('B01 and C13 population controls differ')
        result = dict(state_code=row[1], district_code=row[2], area_name=row[3],
                      residence=row[4], age_band=row[5], **evidence(record, sid, i+1))
        result.update({category+'_'+field: value for category, values in categories.items()
                       for field, value in values.items()})
        work.append(result)
    leaf_checks = reconcile_leaf_work(work)
    write('census_2011_single_year_ages.csv', ages)
    write('census_2011_work_status.csv', work)
    audit = dict(single_year_age_rows=len(ages), work_status_rows=len(work),
                 c14_rows_reconciled=len(grouped), b01_c13_checks=len(work)*len(FIELDS),
                 pca_b01_joint_work_checks=len(leaf_checks),
                 pca_b01_joint_work_reconciliation=leaf_checks,
                 status='historical_controls_not_current_population_or_demand',
                 limitations=[
                     'All ages and residence totals overlap constituent rows.',
                     'Age 100+ remains top coded; unstated age is retained.',
                     'B01 age 15-59 and 60+ overlap detailed age bands.',
                     'B01 has no separate 0-4 row; totals include this population.',
                     'Seeking/available categories overlap marginal and non-worker totals.',
                     'Main and marginal work are annual duration categories, not full/part-time employment.',
                     'District boundaries are historical; no allocation to a current model boundary.'])
    Path(city.path('data/processed/observed/_age_work_controls_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
