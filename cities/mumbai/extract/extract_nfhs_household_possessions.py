"""Extract household vehicle possession from the NFHS-4 and NFHS-5 Maharashtra reports.

The National Family Health Survey's state reports print, in their household
possessions table, the percentage of urban, rural and all households owning a
bicycle, a motorcycle or scooter and a car (Table 5 of the 2015-16 report,
Table 7 of the 2019-21 report). The census of 2011 is the possession the
population synthesiser starts from and the base year is 2026; these two
surveys are the only later observations of household vehicle possession the
package holds, at the state level - a check on the registration-stock
projection (derive_vehicle_possession_growth.py), never a district control.
Both rows are kept as printed; nothing is interpolated.
"""
import json
import re
from pathlib import Path

from pypdf import PdfReader
import city
from extract_census_controls import source, write

REPORTS = {
    'nfhs4_maharashtra_report_2015_16': dict(survey='NFHS-4', period='2015-16', table='Table 5 Household possessions and land ownership'),
    'nfhs5_maharashtra_report_2019_21': dict(survey='NFHS-5', period='2019-21', table='Table 7 Household possessions and land ownership'),
}
ITEMS = {'Bicycle': 'bicycle', 'Motorcycle or scooter': 'motorcycle_or_scooter', 'Car': 'car'}
OUTPUT_INPUTS = {
    'data/processed/observed/nfhs_household_vehicle_possession.csv': [
        'data/raw/population/nfhs4_maharashtra_report_2015_16_*.pdf', 'data/raw/population/nfhs5_maharashtra_report_2019_21_*.pdf'],
    'data/processed/acquisition/nfhs_household_possessions_audit.json': [
        'data/raw/population/nfhs4_maharashtra_report_2015_16_*.pdf', 'data/raw/population/nfhs5_maharashtra_report_2019_21_*.pdf'],
}


def main():
    rows, audit = [], []
    for source_id, spec in REPORTS.items():
        record, path = source(source_id, 'population')
        pages = PdfReader(path).pages
        found = None
        for number, page in enumerate(pages, start=1):
            text = page.extract_text(extraction_mode='layout') or ''
            if spec['table'] in ' '.join(text.split()) and 'Motorcycle or scooter' in text:
                found = (number, text)
                break
        if not found:
            raise ValueError('%s: %s not found' % (source_id, spec['table']))
        number, text = found
        header = next(l for l in text.splitlines() if 'Household possessions' in l and 'Urban' in l)
        columns = [c.strip() for c in re.split(r'\s{2,}', header.strip())][1:]
        if columns[:3] != ['Urban', 'Rural', 'Total']:
            raise ValueError('%s: column order changed: %s' % (source_id, columns))
        got = {}
        for line in text.splitlines():
            m = re.match(r'\s*(Bicycle|Motorcycle or scooter|Car)\s{2,}((?:\d+\.\d\s+)+\d+\.\d)\s*$', line)
            if m:
                values = [float(v) for v in m.group(2).split()]
                got[m.group(1)] = values
        if set(got) != set(ITEMS):
            raise ValueError('%s: rows %s' % (source_id, sorted(got)))
        for item, values in got.items():
            for residence, value in zip(('urban', 'rural', 'total'), values[:3]):
                rows.append(dict(survey=spec['survey'], reference_period=spec['period'], state='Maharashtra',
                                 residence=residence, item=ITEMS[item], households_possessing_pct=value,
                                 universe='households (de jure population column not taken)',
                                 source='observed', source_id=source_id, source_sha256=record['sha256'],
                                 source_page=number, source_table=spec['table'],
                                 status='state_survey_observation_not_district_control'))
        audit.append(dict(source_id=source_id, page=number, table=spec['table'], items=sorted(got)))
    write('nfhs_household_vehicle_possession.csv', rows)
    Path(city.path('data/processed/acquisition/nfhs_household_possessions_audit.json')).write_text(
        json.dumps(dict(rows=len(rows), reports=audit,
                        limitations=['State-level percentages of households; the Mumbai districts are not published separately.',
                                     'A survey share of owning households, not a vehicle count; second vehicles are invisible.']),
                   indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
