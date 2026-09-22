"""Carry the 2011 household vehicle possession to the base year from the registration stock.

The population synthesiser draws each household's two-wheeler and car from the
Census 2011 HL-14 possession shares of its leaf. Fifteen years of registration
growth separate that census from the 2026 base year, and the growth is
observed - not at the leaf, but at the RTO office and the state:

  * 31 March 2017, office and category (Table 24 of the Transport
    Commissioner's statistics 2016-17, `mts_2017_office_category_stock.csv`);
  * 31 March 2025, the same offices and categories (`rto_2025_vehicle_categories.csv`)
    and the 2024-25 new registrations (`rto_2025_summary.csv`);
  * 31 March 2011 and 2017, category, the state (Tables 15 and 16,
    `mts_state_category_stock_series.csv`) - no office-level 2011 stock is
    published, so the first leg is the state's;
  * households 2011 (the census leaf controls of the core extent) and 2026
    (2011 households at the district's IIPS projected persons ratio, the
    factor `build_population.py` grows the district by).

For each census district and category the growth of vehicles per household is

    g = (stock_2026 / households_2026) / (stock_2011 / households_2011)

with stock_2026 = stock_2025 x (stock_2025 / stock_2017) ^ (1/8) (one more year
at the offices' own 2017-2025 rate) and stock_2011 = stock_2017 / (state
2017 / state 2011). The synthesiser turns g into a possession share by the
Poisson identity for "at least one": share = 1 - exp(-lambda), lambda_2026 =
g x lambda_2011, lambda_2011 = -ln(1 - share_2011) - a household's vehicle
count is treated as Poisson, so the share of owning households rises slower
than the stock as owners add second vehicles. The sweep brackets the two legs
this cannot observe: the low bound extrapolates the offices' own 2017-2025
rate back to 2011 (no state leg); the high bound adds the 2024-25 gross
registrations without scrappage for the 2026 leg.

Registration stock counts vehicles on record at the office, not vehicles in
use in the district: a growth RATIO cancels a constant record inflation, not a
changing one, and the report says so. The only later survey observation of
possession the package holds - NFHS-4 (2015-16) and NFHS-5 (2019-21),
Maharashtra urban households (`nfhs_household_vehicle_possession.csv`) - is
compared in the report as a yearly growth of the Poisson rate lambda =
-ln(1 - share) beside each district's derived yearly growth: a state-level
check on the direction and pace, not a control. Outputs:
`data/processed/derived/vehicle_possession_growth.csv` and its report.
"""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path

import city
import registry

OUTPUT_INPUTS = {
    'data/processed/derived/vehicle_possession_growth.csv': [
        'data/processed/observed/mts_2017_office_category_stock.csv',
        'data/processed/observed/mts_state_category_stock_series.csv',
        'data/processed/observed/rto_2025_vehicle_categories.csv',
        'data/processed/observed/rto_2025_summary.csv',
        'data/processed/observed/census_2011_leaf_controls.csv',
        'data/processed/observed/district_population_projections.csv',
        'data/processed/zones/mmr_extent.csv',
        'registry/B_population.json',
    ],
    'data/processed/derived/_vehicle_possession_growth_report.json': [
        'data/processed/derived/vehicle_possession_growth.csv',
        'data/processed/observed/nfhs_household_vehicle_possession.csv',
    ],
}
# the RTO offices of registration inside each Census 2011 district (Palghar,
# carved from Thane in 2014, is inside 517 as the census drew it): the labels
# as the two publications print them
OFFICES = {
    '519': {'2017': ['Mumbai (C)'], '2025': ['Mumbai (C)']},
    '518': {'2017': ['Mumbai (W)', 'Mumbai (E)', 'Borivali'], '2025': ['Mumbai (W)', 'Mumbai (E)', 'Borivali']},
    '517': {'2017': ['Thane', 'Kalyan', 'Vashi N.Mumbai', 'Vasai'], '2025': ['Thane', 'Kalyan', 'Vashi N.mumbai', 'Vasai']},
    '520': {'2017': ['Panvel', 'Pen Raigad'], '2025': ['Panvel', 'Pen-Raigad']},
}
# category codes shared by the two office tables -> the state series category
CATEGORIES = {
    'two_wheeler': (['1', '2', '3'], 'Two Wheelers'),
    'car': (['4', '5', '6'], 'Cars/Jeeps/ St. Wagons'),
}


def read(path):
    with Path(city.path(path)).open(encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def main():
    stock_2017, stock_2025, new_2025 = defaultdict(int), defaultdict(int), defaultdict(int)
    for r in read('data/processed/observed/mts_2017_office_category_stock.csv'):
        if r['office_level'] == 'office':
            stock_2017[(r['office_label'], r['category_code'])] += int(r['vehicles_count'])
    for r in read('data/processed/observed/rto_2025_vehicle_categories.csv'):
        if r['office_level'] == 'office':
            target = stock_2025 if r['measure'] == 'registered_stock_20250331' else new_2025
            target[(r['office_label'], r['category_code'])] += int(r['vehicles_count'])
    state = {(r['category'], int(r['stock_year_31_march'])): int(r['vehicles_count'])
             for r in read('data/processed/observed/mts_state_category_stock_series.csv')}
    # the stock dates the two publications print, and the census year of the
    # state series, read from the tables themselves
    def stock_year(path):
        measures = {r['measure'] for r in read(path) if r['measure'].startswith('registered_stock_')}
        if len(measures) != 1:
            raise SystemExit('%s prints %d stock dates, expected one' % (path, len(measures)))
        return int(measures.pop().replace('registered_stock_', '')[:4])
    year_2017 = stock_year('data/processed/observed/mts_2017_office_category_stock.csv')
    year_2025 = stock_year('data/processed/observed/rto_2025_vehicle_categories.csv')
    year_2011 = int(next(r['observation_year'] for r in read('data/processed/observed/census_2011_leaf_controls.csv')))
    cfg = registry.load()
    base_year = str(city.descriptor()['base_year'])
    base_year_int = int(base_year)
    names = cfg.get('B.population.projection_district_names')
    extent = {r['geography_id']: r['tier'] for r in read('data/processed/zones/mmr_extent.csv')}
    hh_2011_of = defaultdict(int)
    for r in read('data/processed/observed/census_2011_leaf_controls.csv'):
        if extent.get(r['geography_id']) == 'core':
            hh_2011_of[r['district_code']] += int(r['households_count'])
    persons = {}
    for r in read('data/processed/observed/district_population_projections.csv'):
        persons[(r['district_name_as_printed'], r['reference_year'])] = int(r['male_persons_count']) + int(r['female_persons_count'])
    rows = []
    for district, offices in OFFICES.items():
        hh_2011 = hh_2011_of[district]
        growth = persons[(names[district], base_year)] / persons[(names[district], '2011')]
        hh_2026 = int(round(hh_2011 * growth))
        for category, (codes, state_label) in CATEGORIES.items():
            s17 = sum(stock_2017[(o, c)] for o in offices['2017'] for c in codes)
            s25 = sum(stock_2025[(o, c)] for o in offices['2025'] for c in codes)
            n25 = sum(new_2025[(o, c)] for o in offices['2025'] for c in codes)
            if not s17 or not s25:
                raise SystemExit('no %s stock for district %s: offices %s' % (category, district, offices))
            office_ratio = s25 / s17                       # the offices, observed between their two stock dates
            state_ratio = state[(state_label, year_2017)] / state[(state_label, year_2011)]
            annual = office_ratio ** (1 / (year_2025 - year_2017))     # the offices' own yearly rate
            s11 = s17 / state_ratio
            s26 = s25 * annual ** (base_year_int - year_2025)
            per_hh_2011 = s11 / hh_2011
            central = (s26 / hh_2026) / per_hh_2011
            # the offices' rate extrapolated over the whole census-to-base-year span
            low = (s26 / hh_2026) / ((s25 / annual ** (year_2025 - year_2011)) / hh_2011)
            high = ((s25 + n25) / hh_2026) / per_hh_2011                          # gross additions, no scrappage
            rows.append(dict(
                district_code=district, category=category,
                offices=' + '.join(offices['2025']),
                stock_20170331=s17, stock_20250331=s25, new_registrations_2024_25=n25,
                office_ratio_2025_over_2017=round(office_ratio, 4),
                state_ratio_2017_over_2011=round(state_ratio, 4),
                stock_2011_derived=int(round(s11)), stock_2026_derived=int(round(s26)),
                households_2011=hh_2011, households_2026=hh_2026,
                vehicles_per_household_2011=round(per_hh_2011, 4),
                vehicles_per_household_2026=round(s26 / hh_2026, 4),
                growth_per_household=round(central, 4),
                growth_per_household_low=round(min(low, high, central), 4),
                growth_per_household_high=round(max(low, high, central), 4),
                source='derived',
                basis='office stock 2017 and 2025 (observed), state category ratio 2011-2017 (observed), households 2011 (census) and 2026 (projected)'))
    out = Path(city.path('data/processed/derived/vehicle_possession_growth.csv'))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    # the NFHS check: the state's urban lambda growth a year between the two surveys
    nfhs = read('data/processed/observed/nfhs_household_vehicle_possession.csv')
    survey_mid = {'2015-16': 2015.5, '2019-21': 2020.0}       # the survey periods' midpoints
    check = {}
    for category, item in (('two_wheeler', 'motorcycle_or_scooter'), ('car', 'car')):
        shares = {r['reference_period']: float(r['households_possessing_pct']) / 100
                  for r in nfhs if r['residence'] == 'urban' and r['item'] == item}
        periods = sorted(shares, key=survey_mid.get)
        lam = [-math.log(1 - shares[p]) for p in periods]
        years = survey_mid[periods[-1]] - survey_mid[periods[0]]
        check[category] = dict(nfhs_urban_share_by_period={p: shares[p] for p in periods},
                               nfhs_urban_lambda_growth_per_year=round((lam[-1] / lam[0]) ** (1 / years), 4),
                               derived_growth_per_year_by_district={
                                   r['district_code']: round(r['growth_per_household'] ** (1 / (base_year_int - year_2011)), 4)
                                   for r in rows if r['category'] == category})
    report = dict(source='derived', method='see the module docstring', rows=len(rows),
                  years=dict(census=year_2011, office_stock_first=year_2017, office_stock_last=year_2025, base=base_year_int),
                  nfhs_check=check,
                  reading='the derived per-household stock growth a year is compared with the growth a year of the '
                          'Poisson rate of the state urban possession share between the two surveys; a district whose '
                          'derived rate exceeds the survey rate is projected faster than the state moved')
    Path(city.path('data/processed/derived/_vehicle_possession_growth_report.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(check, indent=1))
    for r in rows:
        print('%s %-11s stock %9d -> %9d  per household %.3f -> %.3f  growth %.2f [%.2f, %.2f]' % (
            r['district_code'], r['category'], r['stock_20170331'], r['stock_20250331'],
            r['vehicles_per_household_2011'], r['vehicles_per_household_2026'],
            r['growth_per_household'], r['growth_per_household_low'], r['growth_per_household_high']))


if __name__ == '__main__':
    main()
