"""The household population of the core extent, from the census controls (9.204).

Every distribution that bears on how a person chooses a mode is taken from the
published data for this city (GOAL.md requirement 5) - here the Census of
India 2011 and the IIPS district projections that carry it to the base year:

  leaf (ward / village, PCA)   households, persons by sex, persons aged 0-6 by
                               sex, main and marginal workers by sex
  ward / village (HL-14)       the household-size distribution (1, 2, 3, 4, 5,
                               6-8, 9+) and the share of households with a
                               two-wheeler, a car and a bicycle
  district x residence (C-13)  single-year ages by sex
  district x residence (B-01)  main and marginal workers by age band and sex
  district x residence (C-12)  school attendance by single age 5-19 and by
                               economic activity
  district (IIPS 2012-2031)    the projected population by age band and sex in
                               the base year, against 2011 - the growth factor
  district (RTO stock)         the growth of registered two-wheelers and cars
                               per household 2011 -> base year, derived by
                               derive_vehicle_possession_growth.py from the
                               2017 and 2025 office stock and the state series

For every core leaf of `data/processed/zones/mmr_extent.csv` (D13) the
synthesiser draws households whose sizes follow the leaf's HL-14 distribution
until the leaf's projected person count is reached, then draws each person's
sex from the leaf's ratio, age from the district's single-year distribution in
two strata (0-6 as the leaf publishes it; 7+), work status by the district's
age-by-sex rates scaled to the leaf's own worker counts, school attendance by
the district's age-by-activity rates, and the household's vehicles by the
leaf's 2011 possession shares carried to the base year by the district's stock
growth (B.population.vehicle_possession_projection). Licence holding and income are not published: each
is a declared assumption with its sweep, labelled in the report. Everything
is seeded (B.seed.master) and vectorised per leaf.

Outputs, in the framework's population layer:
  demand/population/B1_synthetic_population.csv   one row per person
  demand/population/B1_households.csv             one row per household
  demand/population/_population_report.json       the controls and what the
                                                  synthesis reached against them

Nothing here is a trip or a mode: the plans are the activity builder's, and no
citywide plans have been built from this population yet.
"""
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

import city
import registry
from build.extract_osm_network import fingerprint

OBS = 'data/processed/observed/'
OUTPUT_INPUTS = {
    'demand/population/B1_synthetic_population.csv': [
        'data/processed/zones/mmr_extent.csv',
        'data/processed/observed/census_2011_leaf_controls.csv',
        'data/processed/observed/census_2011_household_assets.csv',
        'data/processed/observed/census_2011_single_year_ages.csv',
        'data/processed/observed/census_2011_work_status.csv',
        'data/processed/observed/census_2011_school_attendance.csv',
        'data/processed/observed/district_age_population_projections.csv',
        'data/processed/derived/vehicle_possession_growth.csv',
        'registry/B_population.json', 'registry/B_baseline_demand.json'],
    'demand/population/B1_households.csv': [
        'data/processed/zones/mmr_extent.csv',
        'data/processed/observed/census_2011_leaf_controls.csv',
        'data/processed/observed/census_2011_household_assets.csv',
        'data/processed/observed/district_age_population_projections.csv',
        'data/processed/derived/vehicle_possession_growth.csv',
        'registry/B_population.json'],
    'demand/population/_population_report.json': [
        'data/processed/zones/mmr_extent.csv',
        'data/processed/observed/census_2011_leaf_controls.csv',
        'data/processed/observed/census_2011_household_assets.csv',
        'data/processed/observed/census_2011_single_year_ages.csv',
        'data/processed/observed/census_2011_work_status.csv',
        'data/processed/observed/census_2011_school_attendance.csv',
        'data/processed/observed/district_age_population_projections.csv',
        'data/processed/derived/vehicle_possession_growth.csv',
        'registry/B_population.json', 'registry/B_baseline_demand.json'],
}
PERSONS = 'demand/population/B1_synthetic_population.csv'
HOUSEHOLDS = 'demand/population/B1_households.csv'
REPORT = 'demand/population/_population_report.json'
PERSON_COLUMNS = ['person_id', 'household_id', 'geography_id', 'tier', 'district_code', 'rural_urban',
                  'age', 'sex', 'worker_status', 'student', 'licence_holder', 'household_size',
                  'household_two_wheelers', 'household_cars', 'household_bicycles',
                  'car_available', 'two_wheeler_available', 'bike_available',
                  'income_monthly_inr', 'weight']
SIZE_BANDS = (('household_size_1_pct', 1, 1), ('household_size_2_pct', 2, 2), ('household_size_3_pct', 3, 3),
              ('household_size_4_pct', 4, 4), ('household_size_5_pct', 5, 5), ('household_size_6_to_8_pct', 6, 8),
              ('household_size_9_plus_pct', 9, None))


def rows(name):
    with Path(city.path(OBS, name)).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def band_bounds(label, open_top):
    if label.endswith('+'):
        return int(label[:-1]), open_top
    if '-' in label:
        lo, hi = label.split('-')
        return int(lo), int(hi)
    return int(label), int(label)


def projection_factors(cfg, districts):
    """district code -> {sex: base-year persons / 2011 persons}, and the base-year
    age-band structure by sex, from the IIPS district projections."""
    base_year = str(city.descriptor()['base_year'])
    names = cfg.get('B.population.projection_district_names')
    proj = rows('district_age_population_projections.csv')
    census = rows('census_2011_age_sex.csv')
    out, structure = {}, {}
    for code in districts:
        printed = names[code]
        target = {r['age_label']: (float(r['male_persons_count']), float(r['female_persons_count']))
                  for r in proj if r['district_name_as_printed'] == printed and r['reference_year'] == base_year}
        if 'All ages' not in target:
            raise SystemExit('no %s projection for district %s (%s)' % (base_year, code, printed))
        c = [r for r in census if r['district_code'] == code and r['residence'] == 'Total' and r['age_band'] == 'All ages'][0]
        out[code] = {'male': target['All ages'][0] / float(c['male_persons_count']),
                     'female': target['All ages'][1] / float(c['female_persons_count'])}
        structure[code] = {k: v for k, v in target.items() if k != 'All ages'}
    return out, structure


def age_distributions(cfg, districts, structure):
    """(district, residence, sex) -> weights over single ages 0..open_top: the
    district's 2011 single-year shape within each band, at the base year's
    band structure."""
    top = cfg.get('B.baseline.open_age_upper_years')
    single = rows('census_2011_single_year_ages.csv')
    dist = {}
    for code in districts:
        for residence in ('Urban', 'Rural'):
            for sex, col in (('male', 'male_persons_count'), ('female', 'female_persons_count')):
                w = np.zeros(top + 1)
                for r in single:
                    if r['district_code'] != code or r['residence'] != residence:
                        continue
                    label = r['age_years_or_band']
                    if label in ('All ages', 'Age not stated'):
                        continue
                    lo, hi = band_bounds(label, top)
                    if lo > top:                 # ages past the open top fold into it
                        w[top] += float(r[col])
                        continue
                    hi = min(hi, top)
                    w[lo:hi + 1] += float(r[col]) / (hi - lo + 1)
                if w.sum() <= 0:
                    continue
                # re-weight each projected band to the base year's structure
                scaled = w.copy()
                for label, (m, f) in structure[code].items():
                    lo, hi = band_bounds(label, top)
                    if lo > top:
                        continue
                    hi = min(hi, top)
                    band_2011 = w[lo:hi + 1].sum()
                    if band_2011 > 0:
                        scaled[lo:hi + 1] *= ((m if sex == 'male' else f) / band_2011)
                dist[(code, residence, sex)] = scaled / scaled.sum()
    return dist


def worker_rates(districts, top):
    """(district, residence, sex) -> per-age weights for main and marginal work,
    from B-01's age bands."""
    ws = rows('census_2011_work_status.csv')
    out = {}
    for r in ws:
        if r['district_code'] not in districts or r['age_band'] in ('Total', 'Age not stated', '15-59', '60+'):
            continue
        lo, hi = band_bounds(r['age_band'], top)
        if lo > top:
            continue
        hi = min(hi, top)
        for sex, suffix in (('male', 'male_persons_count'), ('female', 'female_persons_count')):
            key = (r['district_code'], r['residence'], sex)
            main, marg = out.setdefault(key, (np.zeros(top + 1), np.zeros(top + 1)))
            pop = float(r['population_' + suffix])
            if pop <= 0:
                continue
            main[lo:hi + 1] = float(r['main_worker_' + suffix]) / pop
            marg[lo:hi + 1] = (float(r['marginal_worker_under_3_months_' + suffix])
                               + float(r['marginal_worker_3_to_6_months_' + suffix])) / pop
    return out


def attendance_rates(districts, top):
    """(district, residence) -> {activity: per-age attendance probability}, C-12."""
    sa = rows('census_2011_school_attendance.csv')
    cells = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    for r in sa:
        if r['district_code'] not in districts or '-' in r['age_years_or_band']:
            continue
        age = int(r['age_years_or_band'])
        act = 'marginal_worker' if r['economic_activity'].startswith('marginal') else r['economic_activity']
        cell = cells[(r['district_code'], r['residence'])][(act, age)]
        cell[0 if r['attends_education'] == 'true' else 1] += float(r['persons_count'])
    out = {}
    for key, table in cells.items():
        rates = {act: np.zeros(top + 1) for act in ('main_worker', 'marginal_worker', 'non_worker')}
        for (act, age), (yes, no) in table.items():
            if yes + no > 0 and age <= top:
                rates[act][age] = yes / (yes + no)
        out[key] = rates
    return out


def household_profiles(cfg):
    """(district, subdistrict, town, ward) -> the HL-14 row, exact key."""
    hl = rows('census_2011_household_assets.csv')
    return {(r['district_code'], r['subdistrict_code'], r['town_village_code'], r['ward_code'], r['residence']): r
            for r in hl}


def possession_growth(cfg):
    """(district, category) -> the growth of registered vehicles per household
    2011 -> base year, at the declared bound; {} when the gate is `none`."""
    if cfg.get('B.population.vehicle_possession_projection') == 'none':
        return {}
    column = 'growth_per_household' + {'central': '', 'low': '_low', 'high': '_high'}[cfg.get('B.population.vehicle_possession_growth_bound')]
    path = Path(city.path('data/processed/derived/vehicle_possession_growth.csv'))
    with path.open(encoding='utf-8') as stream:
        return {(r['district_code'], r['category']): float(r[column]) for r in csv.DictReader(stream)}


def projected_share(share_2011_pct, growth):
    """The share of households owning at least one vehicle after the stock per
    household grows by `growth`, by the Poisson identity: lambda = -ln(1 - s)."""
    s = min(max(share_2011_pct / 100.0, 0.0), 0.999999)
    return 1.0 - math.exp(-growth * -math.log(1.0 - s))


def profile_for(profiles, leaf):
    """The leaf's own HL-14 row, else its town's, its subdistrict's, its district's."""
    d, sd, tv, w = leaf['district_code'], leaf['subdistrict_code'], leaf['town_village_code'], leaf['ward_code']
    residence = leaf['rural_urban']
    for key, level in (((d, sd, tv, w, residence), 'leaf'), ((d, sd, tv, w, 'Total'), 'leaf'),
                       ((d, sd, tv, '0000', residence), 'town'), ((d, sd, tv, '0000', 'Total'), 'town'),
                       ((d, sd, '000000', '0000', residence), 'subdistrict'), ((d, sd, '000000', '0000', 'Total'), 'subdistrict'),
                       ((d, '00000', '000000', '0000', residence), 'district'), ((d, '00000', '000000', '0000', 'Total'), 'district')):
        if key in profiles:
            return profiles[key], level
    raise SystemExit('no HL-14 household profile at any level for %s' % leaf['geography_id'])


def draw_sizes(rng, profile, n_persons, open_max):
    """Household sizes from the HL-14 band shares until n_persons is covered."""
    shares = np.array([max(float(profile[col]), 0.0) for col, _, _ in SIZE_BANDS])
    if shares.sum() <= 0:
        raise SystemExit('empty household-size distribution for ' + profile['area_name'])
    shares /= shares.sum()
    mean_size = sum(s * ((lo + (hi if hi else open_max)) / 2.0) for s, (_, lo, hi) in zip(shares, SIZE_BANDS))
    los_of = np.array([lo for _, lo, _ in SIZE_BANDS])
    his_of = np.array([(hi if hi else open_max) for _, _, hi in SIZE_BANDS])
    sizes = np.zeros(0, dtype=int)
    while sizes.sum() < n_persons:                 # draw until the persons are covered
        n_draw = int((n_persons - sizes.sum()) / mean_size * 1.2) + 4
        bands = rng.choice(len(SIZE_BANDS), size=n_draw, p=shares)
        sizes = np.concatenate([sizes, rng.integers(los_of[bands], his_of[bands] + 1)])
    cum = np.cumsum(sizes)
    k = int(np.searchsorted(cum, n_persons))       # the household that crosses the total
    sizes = sizes[:k + 1]
    sizes[-1] -= int(cum[k] - n_persons)            # trimmed to land exactly, never below one
    return sizes[sizes > 0]


def main():
    cfg = registry.load()
    rng = np.random.default_rng(int(cfg.get('B.seed.master')))
    top = int(cfg.get('B.baseline.open_age_upper_years'))
    adult = int(cfg.get('B.baseline.adult_age_years'))
    open_max = int(cfg.get('B.population.household_size_open_band_max'))
    licence_p = float(cfg.get('B.baseline.licence_given_vehicle_probability'))
    # UNOBTAINED: the registry refuses a point value; the sweep's floor (nobody
    # aged 20-24 attends) is the member taken, explicitly, and the report says so
    tertiary_sweep = cfg.sweep('B.population.tertiary_attendance_rate_20_24')
    tertiary = float((tertiary_sweep['interval'] if isinstance(tertiary_sweep, dict) else tertiary_sweep)[0])
    income_median, income_sigma, income_min = (cfg.get('B.baseline.income_median_monthly_inr'),
                                               cfg.get('B.baseline.income_log_sigma'),
                                               cfg.get('B.baseline.income_minimum_monthly_inr'))

    extent = {r['geography_id']: r for r in csv.DictReader(open(city.path('data/processed/zones/mmr_extent.csv'), encoding='utf-8'))}
    leaves = [r for r in rows('census_2011_leaf_controls.csv') if extent[r['geography_id']]['tier'] == 'core']
    districts = sorted({r['district_code'] for r in leaves})
    factors, structure = projection_factors(cfg, districts)
    ages = age_distributions(cfg, districts, structure)
    work = worker_rates(districts, top)
    attend = attendance_rates(districts, top)
    profiles = household_profiles(cfg)
    growth = possession_growth(cfg)

    out_persons = Path(city.path(PERSONS))
    out_households = Path(city.path(HOUSEHOLDS))
    out_persons.parent.mkdir(parents=True, exist_ok=True)
    person_id = household_id = 0
    totals = Counter()
    by_district = defaultdict(Counter)
    profile_levels = Counter()
    first = True
    for leaf in sorted(leaves, key=lambda r: r['geography_id']):
        code, residence = leaf['district_code'], leaf['rural_urban']
        gid = leaf['geography_id']
        n_m = int(round(float(leaf['male_persons_count']) * factors[code]['male']))
        n_f = int(round(float(leaf['female_persons_count']) * factors[code]['female']))
        n = n_m + n_f
        if n <= 0:
            continue
        profile, level = profile_for(profiles, leaf)
        profile_levels[level] += 1
        sizes = draw_sizes(rng, profile, n, open_max)
        n = int(sizes.sum())
        hh_ids = np.arange(household_id + 1, household_id + 1 + len(sizes))
        household_id += len(sizes)
        hh_of_person = np.repeat(hh_ids, sizes)
        size_of_person = np.repeat(sizes, sizes)
        # sex: the leaf's own ratio, exact counts
        sex = np.array(['male'] * n_m + ['female'] * max(n - n_m, 0))[:n]
        rng.shuffle(sex)
        # age in two strata: 0-6 as the leaf publishes it (scaled), 7+ the rest
        share_06 = float(leaf['persons_age_0_6_count']) / max(float(leaf['persons_count']), 1.0)
        age = np.zeros(n, dtype=int)
        for s in ('male', 'female'):
            idx = np.flatnonzero(sex == s)
            if not len(idx):
                continue
            w = ages[(code, residence, s)] if (code, residence, s) in ages else ages[(code, 'Urban', s)]
            n06 = int(round(len(idx) * share_06))
            young, old = w[:7] / max(w[:7].sum(), 1e-12), w[7:] / max(w[7:].sum(), 1e-12)
            pick = rng.permutation(idx)
            age[pick[:n06]] = rng.choice(7, size=n06, p=young)
            age[pick[n06:]] = 7 + rng.choice(len(old), size=len(idx) - n06, p=old)
        # work status: the district's age-by-sex rates as weights, the leaf's counts as totals
        status = np.array(['non_worker'] * n, dtype=object)
        for s, col_main, col_marg in (('male', 'male_main_workers_count', 'male_marginal_workers_count'),
                                      ('female', 'female_main_workers_count', 'female_marginal_workers_count')):
            idx = np.flatnonzero(sex == s)
            if not len(idx):
                continue
            main_w, marg_w = work[(code, residence, s)] if (code, residence, s) in work else work[(code, 'Total', s)]
            scale = len(idx) / max(float(leaf['male_persons_count' if s == 'male' else 'female_persons_count']), 1.0)
            n_main = min(int(round(float(leaf[col_main]) * scale)), len(idx))
            n_marg = min(int(round(float(leaf[col_marg]) * scale)), len(idx) - n_main)
            pm = main_w[age[idx]]
            if pm.sum() <= 0:
                pm = np.ones(len(idx))
            chosen = rng.choice(idx, size=n_main, replace=False, p=pm / pm.sum()) if n_main else np.array([], dtype=int)
            status[chosen] = 'main_worker'
            rest = np.setdiff1d(idx, chosen)
            pg = marg_w[age[rest]]
            if pg.sum() <= 0:
                pg = np.ones(len(rest))
            chosen = rng.choice(rest, size=n_marg, replace=False, p=pg / pg.sum()) if n_marg and len(rest) else np.array([], dtype=int)
            status[chosen] = 'marginal_worker'
        # school attendance: C-12 by age and activity for 5-19; 20-24 as declared (unobtained -> 0)
        rates = attend[(code, residence)] if (code, residence) in attend else attend[(code, 'Total')]
        p_attend = np.zeros(n)
        for act in ('main_worker', 'marginal_worker', 'non_worker'):
            m = status == act
            p_attend[m] = rates[act][age[m]]
        p_attend[(age >= 20) & (age <= 24)] = tertiary
        student = (rng.random(n) < p_attend).astype(int)
        # household vehicles: the leaf's 2011 possession shares carried to the
        # base year by the district's stock growth (B.population.vehicle_possession_projection)
        n_hh = len(sizes)
        p_two_w = float(profile['households_with_two_wheeler_pct']) / 100
        p_car = float(profile['households_with_car_jeep_van_pct']) / 100
        if growth:
            p_two_w = projected_share(float(profile['households_with_two_wheeler_pct']), growth[(code, 'two_wheeler')])
            p_car = projected_share(float(profile['households_with_car_jeep_van_pct']), growth[(code, 'car')])
        two_w = (rng.random(n_hh) < p_two_w).astype(int)
        cars = (rng.random(n_hh) < p_car).astype(int)
        bikes = (rng.random(n_hh) < float(profile['households_with_bicycle_pct']) / 100).astype(int)
        hh_two_w, hh_cars, hh_bikes = np.repeat(two_w, sizes), np.repeat(cars, sizes), np.repeat(bikes, sizes)
        # licence: an adult in a motorised household, at the declared probability (not published)
        motorised = (hh_two_w + hh_cars) > 0
        licence = ((age >= adult) & motorised & (rng.random(n) < licence_p)).astype(int)
        car_avail = (licence & (hh_cars > 0)).astype(int)
        tw_avail = (licence & (hh_two_w > 0)).astype(int)
        bike_avail = ((hh_bikes > 0) & (age >= int(cfg.get('B.population.bike_min_age')))).astype(int)
        income = np.maximum(income_min, rng.lognormal(np.log(income_median), income_sigma, size=n))
        income = np.where(status == 'non_worker', 0.0, income)
        ids = np.arange(person_id + 1, person_id + 1 + n)
        person_id += n
        frame = pd.DataFrame({
            'person_id': ids, 'household_id': hh_of_person, 'geography_id': gid, 'tier': 'core',
            'district_code': code, 'rural_urban': residence, 'age': age, 'sex': sex,
            'worker_status': status, 'student': student, 'licence_holder': licence,
            'household_size': size_of_person, 'household_two_wheelers': hh_two_w,
            'household_cars': hh_cars, 'household_bicycles': hh_bikes,
            'car_available': car_avail, 'two_wheeler_available': tw_avail, 'bike_available': bike_avail,
            'income_monthly_inr': np.round(income, 2), 'weight': 1.0})[PERSON_COLUMNS]
        frame.to_csv(out_persons, mode='w' if first else 'a', header=first, index=False, lineterminator='\n')
        pd.DataFrame({'household_id': hh_ids, 'geography_id': gid, 'size': sizes,
                      'two_wheelers': two_w, 'cars': cars, 'bicycles': bikes}).to_csv(
            out_households, mode='w' if first else 'a', header=first, index=False, lineterminator='\n')
        first = False
        t = by_district[code]
        t['persons'] += n
        t['households'] += n_hh
        t['persons_2011'] += int(leaf['persons_count'])
        t['households_2011'] += int(leaf['households_count'])
        t['main_workers'] += int((status == 'main_worker').sum())
        t['marginal_workers'] += int((status == 'marginal_worker').sum())
        t['main_workers_2011'] += int(leaf['main_workers_count'])
        t['marginal_workers_2011'] += int(leaf['marginal_workers_count'])
        t['persons_0_6'] += int((age <= 6).sum())
        t['persons_0_6_2011'] += int(leaf['persons_age_0_6_count'])
        t['female'] += int((sex == 'female').sum())
        t['students'] += int(student.sum())
        t['licence_holders'] += int(licence.sum())
        t['households_with_two_wheeler'] += int(two_w.sum())
        t['households_with_car'] += int(cars.sum())
        t['car_available'] += int(car_avail.sum())
        t['two_wheeler_available'] += int(tw_avail.sum())
        totals['leaves'] += 1
    for code, t in by_district.items():
        t['projection_factor_male'] = round(factors[code]['male'], 4)
        t['projection_factor_female'] = round(factors[code]['female'], 4)
        t['mean_household_size'] = round(t['persons'] / max(t['households'], 1), 3)
        t['share_0_6'] = round(t['persons_0_6'] / max(t['persons'], 1), 4)
        t['share_0_6_2011'] = round(t['persons_0_6_2011'] / max(t['persons_2011'], 1), 4)
        t['female_share'] = round(t['female'] / max(t['persons'], 1), 4)
        t['households_two_wheeler_pct'] = round(100.0 * t['households_with_two_wheeler'] / max(t['households'], 1), 2)
        t['households_car_pct'] = round(100.0 * t['households_with_car'] / max(t['households'], 1), 2)
        if growth:
            t['vehicle_possession_growth_two_wheeler'] = growth[(code, 'two_wheeler')]
            t['vehicle_possession_growth_car'] = growth[(code, 'car')]
    grand = Counter()
    for t in by_district.values():
        for k in ('persons', 'households', 'persons_2011', 'households_2011', 'main_workers', 'marginal_workers',
                  'students', 'licence_holders', 'car_available', 'two_wheeler_available'):
            grand[k] += t[k]
    report = dict(
        source='synthetic_from_census_2011_controls_projected_to_base_year',
        base_year=city.descriptor()['base_year'], seed=int(cfg.get('B.seed.master')),
        extent='core tier of data/processed/zones/mmr_extent.csv (D13, 9.204)',
        leaves=totals['leaves'], persons=grand['persons'], households=grand['households'],
        persons_2011=grand['persons_2011'], households_2011=grand['households_2011'],
        by_district=dict(sorted(by_district.items())),
        household_profile_levels=dict(profile_levels),
        totals=dict(grand),
        assumed=['licence holding: B.baseline.licence_given_vehicle_probability for an adult in a household with a '
                 'two-wheeler or a car; not published',
                 'income: the declared lognormal (B.baseline.income_*), workers only; not published at the person level',
                 'tertiary attendance 20-24: B.population.tertiary_attendance_rate_20_24 is unobtained; the sweep floor %g is taken' % tertiary,
                 'household sizes within the 6-8 and 9+ bands: uniform up to B.population.household_size_open_band_max',
                 'two-wheeler, car and bicycle possession drawn independently per household (no joint table published)',
                 ('vehicle possession: the 2011 HL-14 shares carried to the base year by the district registered stock '
                  'per household (derive_vehicle_possession_growth.py, bound %s) through the Poisson at-least-one identity'
                  % cfg.get('B.population.vehicle_possession_growth_bound')) if growth else
                 'vehicle possession: the 2011 HL-14 shares as published (B.population.vehicle_possession_projection = none)',
                 'the leaf\'s 2011 age-0-6 share and worker counts move with the district\'s projected growth'],
        inputs_sha256={p: fingerprint(Path(city.path(p))) for p in OUTPUT_INPUTS[PERSONS] if Path(city.path(p)).exists()},
        note='No trip, tour or mode: the plans are the activity builder\'s. The external tier is not synthesised.')
    Path(city.path(REPORT)).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                                       encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('leaves', 'persons', 'households', 'persons_2011', 'households_2011', 'household_profile_levels')}, indent=1))
    for code, t in sorted(by_district.items()):
        print(code, {k: t[k] for k in ('persons', 'households', 'mean_household_size', 'share_0_6', 'share_0_6_2011',
                                       'households_two_wheeler_pct', 'households_car_pct', 'projection_factor_male')
                     + (('vehicle_possession_growth_two_wheeler', 'vehicle_possession_growth_car') if growth else ())})
    return 0


if __name__ == '__main__':
    sys.exit(main())
