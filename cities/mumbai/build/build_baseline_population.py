"""Build representative people and activities for the broad behavioural smoke.

Historical census marginals guide geography, age, sex, worker and vehicle
access draws. Joint distributions, incomes and destinations remain provisional.
This is not a calibrated population or a full-household synthesis.
"""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pyogrio

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'demand/baseline/persons.csv': [
        'registry/B_baseline_demand.json', 'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/observed/census_2011_age_sex.csv',
        'data/processed/observed/census_2011_household_assets.csv'],
    'demand/baseline/plans.xml.gz': [
        'registry/B_baseline_demand.json', 'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/observed/census_2011_age_sex.csv',
        'data/processed/observed/census_2011_household_assets.csv'],
    'data/processed/acquisition/baseline_population.json': [
        'registry/B_baseline_demand.json', 'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/observed/census_2011_age_sex.csv',
        'data/processed/observed/census_2011_household_assets.csv'],
}


def rows(name):
    with Path(city.path('data/processed/observed', name)).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    cfg = registry.load()
    rng = np.random.default_rng(cfg.get('B.baseline.seed'))
    inputs = OUTPUT_INPUTS['demand/baseline/persons.csv']
    hashes = {p: fingerprint(Path(city.path(p))) for p in inputs}
    zones = pyogrio.read_dataframe(city.path('data/processed/geospatial/census_2011_geographies.gpkg'),
                                  layer='census_leaves').to_crs(city.crs())
    zones = zones[zones.geometry.notna() & (zones.persons_count.astype(float) > 0)].copy()
    zones = zones.sort_values('geography_id').reset_index(drop=True)
    locations = zones.geometry.representative_point()
    xy = np.column_stack([locations.x, locations.y])
    persons = zones.persons_count.to_numpy(dtype=float)
    workers = zones.workers_count.to_numpy(dtype=float)
    ages = rows('census_2011_age_sex.csv')
    assets = rows('census_2011_household_assets.csv')
    asset_lookup = {(r['district_code'], r['residence']): r for r in assets
                    if r['subdistrict_code'] == '00000' and r['town_village_code'] == '000000'
                    and r['ward_code'] == '0000'}
    choices, age_weights, adult_fractions = {}, {}, {}
    adult, work_max = cfg.get('B.baseline.adult_age_years'), cfg.get('B.baseline.work_max_age_years')
    for district in sorted(set(zones.district_code.astype(str))):
        cells = []
        for row in ages:
            if row['district_code'] != district or row['residence'] != 'Total':
                continue
            band = row['age_band']
            if band in ('All ages', 'Age not stated'):
                continue
            low, high = (int(band[:-1]), cfg.get('B.baseline.open_age_upper_years')) if band.endswith('+') else map(int, band.split('-'))
            for age in range(low, high + 1):
                for sex, column in (('male', 'male_persons_count'), ('female', 'female_persons_count')):
                    cells.append((age, sex, float(row[column]) / (high - low + 1)))
        if not cells:
            raise ValueError('No district age/sex distribution')
        weights = np.array([r[2] for r in cells])
        choices[district], age_weights[district] = cells, weights / weights.sum()
        adult_fractions[district] = sum(w for age, _, w in cells if adult <= age <= work_max) / weights.sum()
    home_indices = rng.choice(len(zones), size=cfg.get('B.baseline.persons'), p=persons / persons.sum())
    root, records = ET.Element('population'), []
    purposes, initial_modes = Counter(), Counter()
    for index, home in enumerate(home_indices):
        zone = zones.iloc[home]
        district = str(zone.district_code)
        age, sex, _ = choices[district][rng.choice(len(choices[district]), p=age_weights[district])]
        residence = str(zone.rural_urban)
        asset = asset_lookup.get((district, residence), asset_lookup[(district, 'Total')])
        access = {key: bool(rng.random() < float(asset[col]) / 100) for key, col in (
            ('car', 'households_with_car_jeep_van_pct'),
            ('bike', 'households_with_bicycle_pct'),
            ('motorbike', 'households_with_two_wheeler_pct'))}
        licence = age >= adult and rng.random() < cfg.get('B.baseline.licence_given_vehicle_probability')
        available = ['walk', 'pt']
        if access['car']:
            available.append('ride')
        if age >= adult:
            available += ['taxi', 'auto_rickshaw']
        if age >= cfg.get('B.baseline.school_min_age_years') and access['bike']:
            available.append('bike')
        if licence:
            available.extend(m for m in ('car', 'motorbike') if access[m])
        available = [m for m in cfg.get('B.baseline.initial_choice_modes') if m in available]
        income = max(cfg.get('B.baseline.income_minimum_monthly_inr'), rng.lognormal(
            np.log(cfg.get('B.baseline.income_median_monthly_inr')), cfg.get('B.baseline.income_log_sigma')))
        probability = min(1.0, workers[home] / persons[home] / adult_fractions[district])
        employed = adult <= age <= work_max and rng.random() < probability
        purpose = ('home_only' if age < cfg.get('B.baseline.school_min_age_years') else
                   'education' if age < adult else 'work' if employed else 'other')
        destination, departure, duration, mode = home, 0, 0, ''
        if purpose != 'home_only':
            distances = np.linalg.norm(xy - xy[home], axis=1)
            weights = (workers if purpose == 'work' else persons) * np.exp(
                -distances / cfg.get('B.baseline.gravity_distance_scale_m')[purpose])
            destination = rng.choice(len(zones), p=weights / weights.sum())
            departure = cfg.get('B.baseline.activity_start_s')[purpose] + rng.uniform(
                -cfg.get('B.baseline.departure_spread_s'), cfg.get('B.baseline.departure_spread_s'))
            duration = cfg.get('B.baseline.activity_duration_s')[purpose]
            mode = str(rng.choice(available))
            initial_modes[mode] += 1
        identity = f'baseline_{index}'
        person = ET.SubElement(root, 'person', id=identity)
        attrs = ET.SubElement(person, 'attributes')
        for key, value, java_type in (
                ('subpopulation', 'resident', 'String'), ('age', int(age), 'Integer'),
                ('sex', sex, 'String'), ('income', float(income), 'Double'),
                ('carAvail', 'always' if licence and access['car'] else 'never', 'String'),
                ('hasLicense', 'yes' if licence else 'no', 'String'),
                ('bikeAvail', 'always' if access['bike'] else 'never', 'String'),
                ('permittedModes', ','.join(available), 'String')):
            ET.SubElement(attrs, 'attribute', name=key, attrib={'class': 'java.lang.' + java_type}).text = str(value)
        plan = ET.SubElement(person, 'plan', selected='yes')
        home_attrs = dict(type='home', x=str(xy[home, 0]), y=str(xy[home, 1]))
        if purpose != 'home_only':
            ET.SubElement(plan, 'activity', **home_attrs, end_time=str(round(departure)))
            ET.SubElement(plan, 'leg', mode=mode)
            ET.SubElement(plan, 'activity', type=purpose, x=str(xy[destination, 0]),
                          y=str(xy[destination, 1]), end_time=str(round(departure + duration)))
            ET.SubElement(plan, 'leg', mode=mode)
        ET.SubElement(plan, 'activity', **home_attrs)
        purposes[purpose] += 1
        records.append(dict(person_id=identity, home_geography_id=zone.geography_id,
            destination_geography_id=zones.iloc[destination].geography_id, age_years=age, sex=sex,
            employed=employed, income_monthly_inr=income, permitted_modes=','.join(available),
            purpose=purpose, initial_mode=mode, departure_s=departure, activity_duration_s=duration,
            source='synthetic_from_historical_marginals_and_provisional_assumptions'))
    target = Path(city.path('demand/baseline')); target.mkdir(parents=True, exist_ok=True)
    with (target / 'persons.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(records)
    xml = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n' + ET.tostring(root, encoding='utf-8')
    with (target / 'plans.xml.gz').open('wb') as f:
        with gzip.GzipFile(fileobj=f, mode='wb', filename='', mtime=0) as zipped:
            zipped.write(xml)
    audit = dict(source='synthetic_provisional_behavioural_smoke', input_sha256=hashes,
        persons_count=len(records), source_geographies_count=len(zones),
        source_historical_persons_count=int(persons.sum()), purposes=dict(purposes),
        initial_exploration_modes=dict(initial_modes),
        limitations=['Representative persons, not coupled households.',
            'Historical asset ownership proxies personal access; joint distribution is provisional.',
            'Resident worker locations proxy employment attractions; income and activity timing are provisional.',
            'Initial modes explore available options uniformly; these are not simulated ridership.',
            'Research geography and missing polygons do not define a current full-city population.'])
    Path(city.path('data/processed/acquisition/baseline_population.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('persons_count', 'source_geographies_count', 'purposes', 'initial_exploration_modes')}))


if __name__ == '__main__':
    main()
