"""Reconcile historical age, school-attendance and household-size controls."""
from collections import defaultdict
import csv
import json
from pathlib import Path

import xlrd
import city
from extract_census_controls import count, source, write

OUTPUT_INPUTS = {
    'data/processed/observed/census_2011_age_sex.csv': ['data/raw/population/census_c14_*.xls', 'data/processed/observed/census_2011_leaf_controls.csv'],
    'data/processed/observed/census_2011_school_attendance.csv': ['data/raw/population/census_c12_*.xls', 'data/processed/observed/census_2011_leaf_controls.csv'],
    'data/processed/observed/census_2011_household_sizes.csv': ['data/raw/population/census_hh1_*.xls', 'data/processed/observed/census_2011_leaf_controls.csv'],
    'data/processed/observed/_demographic_controls_audit.json': ['data/raw/population/census_c14_*.xls', 'data/raw/population/census_c12_*.xls', 'data/raw/population/census_hh1_*.xls', 'data/processed/observed/census_2011_leaf_controls.csv'],
}


def workbook(source_id):
    record, path = source(source_id, 'population')
    sheet = xlrd.open_workbook(path).sheet_by_index(0)
    return record, sheet


def sex_counts(row, start):
    p, m, f = [count(row[i]) for i in range(start, start+3)]
    if m+f != p:
        raise ValueError('Sex counts do not reconcile')
    return dict(persons_count=p, male_persons_count=m, female_persons_count=f)


def evidence(record, source_id, row_number):
    return dict(source='observed', source_id=source_id, source_sha256=record['sha256'],
                source_row=row_number, observation_year=2011,
                status='historical_control_not_current_demand')


def main():
    with Path(city.path('data/processed/observed/census_2011_leaf_controls.csv')).open(encoding='utf-8') as stream:
        leaves = list(csv.DictReader(stream))
    districts = {r['district_code'] for r in leaves}
    towns = {r['town_village_code'] for r in leaves if r['rural_urban']=='Urban'}
    pca = defaultdict(int)
    for row in leaves:
        pca[row['district_code']] += int(row['persons_count'])
    ages, schools, households, checks = [], [], [], []
    sid='census_c14_maharashtra'
    record, sheet = workbook(sid)
    if 'FIVE YEAR AGE-GROUP' not in str(sheet.cell_value(0,4)):
        raise ValueError('Unexpected C14 workbook')
    for i in range(sheet.nrows):
        row=sheet.row_values(i)
        if row[0]!='C4114' or row[2] not in districts:
            continue
        for residence, col in [('Total',5),('Rural',8),('Urban',11)]:
            ages.append(dict(state_code=row[1],district_code=row[2],area_name=row[3],
                             age_band=row[4],residence=residence,**sex_counts(row,col),
                             **evidence(record,sid,i+1)))
    for district in sorted(districts):
        for residence in ('Total','Rural','Urban'):
            subset=[r for r in ages if r['district_code']==district and r['residence']==residence]
            all_ages=[r for r in subset if r['age_band']=='All ages']
            if len(all_ages)!=1:
                raise ValueError('No unique C14 all-age total')
            for field in ('persons_count','male_persons_count','female_persons_count'):
                if sum(r[field] for r in subset if r['age_band']!='All ages')!=all_ages[0][field]:
                    raise ValueError('Age bands do not reconcile')
            if residence=='Total' and all_ages[0]['persons_count']!=pca[district]:
                raise ValueError('C14 and PCA district totals differ')
        checks.append(dict(district_code=district,c14_pca_persons_match=True,age_bands_reconcile=True))
    sid='census_c12_maharashtra'
    record,sheet=workbook(sid)
    if 'C-12:' not in str(sheet.cell_value(0,5)):
        raise ValueError('Unexpected C12 workbook')
    activities=['main_worker','marginal_worker_3_to_under_6_months','marginal_worker_under_3_months','non_worker']
    for i in range(sheet.nrows):
        row=sheet.row_values(i)
        if row[0]!='C3412' or row[2] not in districts:
            continue
        age=str(int(row[5])) if isinstance(row[5],float) else row[5]
        all_counts=sex_counts(row,6)
        sums=defaultdict(int)
        for attending, start in [(True,9),(False,21)]:
            for offset, activity in enumerate(activities):
                values=sex_counts(row,start+3*offset)
                for field,value in values.items():
                    sums[field]+=value
                schools.append(dict(state_code=row[1],district_code=row[2],area_name=row[3],
                                    residence=row[4],age_years_or_band=age,
                                    attends_education=str(attending).lower(),economic_activity=activity,
                                    **values,**evidence(record,sid,i+1)))
        if sums!=all_counts:
            raise ValueError('C12 activity/attendance categories do not reconcile')
    grouped=defaultdict(list)
    for row in schools:
        grouped[tuple(row[k] for k in ('district_code','residence','attends_education','economic_activity'))].append(row)
    for subset in grouped.values():
        total=[r for r in subset if r['age_years_or_band']=='5-19']
        single=[r for r in subset if r['age_years_or_band']!='5-19']
        if len(total)!=1 or {r['age_years_or_band'] for r in single}!={str(i) for i in range(5,20)}:
            raise ValueError('Unexpected C12 age universe')
        for field in ('persons_count','male_persons_count','female_persons_count'):
            if sum(r[field] for r in single)!=total[0][field]:
                raise ValueError('C12 single ages do not reconcile')
    for sid,is_city in [('census_hh1_maharashtra',False),('census_hh1_cities_maharashtra',True)]:
        record,sheet=workbook(sid)
        if is_city:
            state_col, district_col, town_col, name_col, residence_col, count_col=0,1,2,3,4,5
        else:
            state_col, district_col, town_col, name_col, residence_col, count_col=1,2,4,5,6,7
        sizes=[str(v) for v in sheet.row_values(3)[count_col+2:count_col+11]]
        if sizes != ['1','2','3','4','5','6','7-10','11-14','15+']:
            raise ValueError('Unexpected HH1 size columns')
        for i in range(6,sheet.nrows):
            row=sheet.row_values(i)
            if (row[town_col] not in towns) if is_city else (row[district_col] not in districts):
                continue
            total=count(row[count_col]);population=count(row[count_col+1])
            buckets=[count(v) for v in row[count_col+2:count_col+11]]
            if sum(buckets)!=total:
                raise ValueError('HH1 household sizes do not reconcile')
            for size,value in zip(sizes,buckets):
                households.append(dict(state_code=row[state_col],district_code=row[district_col],
                                       subdistrict_code=None if is_city else row[3],town_code=row[town_col],
                                       area_name=row[name_col],residence=row[residence_col],household_size_band=size,
                                       households_count=value,all_size_households_count=total,
                                       all_size_normal_household_persons_count=population,
                                       published_mean_household_size_persons=row[count_col+11],
                                       universe='Normal households; repeated totals and nested geography must not be summed',
                                       **evidence(record,sid,i+1)))
    write('census_2011_age_sex.csv',ages)
    write('census_2011_school_attendance.csv',schools)
    write('census_2011_household_sizes.csv',households)
    audit=dict(schema_version=1,source='derived',status='historical_evidence_only',
               age_rows=len(ages),school_rows=len(schools),household_size_rows=len(households),
               district_checks=checks,c12_categories_and_single_ages_reconcile=True,hh1_size_counts_reconcile=True,
               limitations=['Normal households exclude institutional and houseless households; PCA includes different universes.',
                            'City, district, subdistrict and residence totals overlap; no joint synthetic population is created.',
                            'Age not stated remains a separate source category, not reassigned.',
                            'School attendance is not a count of daily school trips or locations.',
                            'Greater Mumbai city can use a special district code in the city table; its source identity is retained.',
                            'The four historical districts cover more than the current metropolitan region.'])
    Path(city.path('data/processed/observed/_demographic_controls_audit.json')).write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit))


if __name__=='__main__':
    main()
