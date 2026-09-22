"""The first per-mode targets of the second city, from the published mode splits (9.205).

`data/processed/validation/mode_targets_by_mode.csv` is what the twelve-mode
reporter, the gate watcher and the board read (GOAL.md requirement 7). Every
row here is derived from a transcribed publication or a census table, and the
derivation is the row's `basis`:

  * the CTS Updation's Table 6-8 (`published_mode_splits.csv`): the 2017
    daily MOTORISED main-mode split of the MMR, and its household survey's
    statement that the active modes are about 47 % of all trips. An all-trip
    share of a motorised mode is its motorised share x (1 - active share);
  * the walk / bicycle split of the active share from Census 2011 table B-28
    (On foot against Bicycle, the four districts summed) - the only published
    series that separates them;
  * the car-driver / car-passenger split from the synthesised population
    (B1): among the persons aged 5 and over in car-owning households, the
    share who may drive (licence holders with a car available) against those
    who may only ride - the only published-data-derived ratio the package
    holds, itself resting on the declared licence assumption;
  * ferry from the Maharashtra Maritime Board's published passenger totals
    for the MMR port groups (Bandra and Mora) - annual passengers to a daily
    count against the CTS's daily trips;
  * truck as the CMP's screenline traffic composition (goods vehicles 11.5 %
    of vehicles), a level the reporter prints beside the network-wide share
    and never scores as a deviation;
  * freight rail `not_simulated`: the citywide plans carry no freight
    movement (9.205).

The survey years are 2017 (CTS), 2014 (CMP), 2011 (B-28) and 2022-25 (MMB)
against a 2026 base year; no projection is applied and the sweep on every
derived row carries the "about 47 %" rounding of the active share. No target
value is invented; a mode the publications do not separate carries the
derivation that separates it, stated, with its sweep.
"""
import csv
import json
from pathlib import Path
import sys

import pandas as pd

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'data/processed/validation/mode_targets_by_mode.csv': [
        'data/processed/observed/published_mode_splits.csv',
        'data/processed/observed/census_2011_b28_commuting.csv',
        'data/processed/observed/water_annual_passengers.csv',
        'data/processed/observed/economic_survey_metro_controls.csv',
        'data/processed/acquisition/ogd_metro_ridership_audit.json',
        'demand/population/B1_synthetic_population.csv',
        'registry/B_targets.json'],
    'data/processed/validation/_mode_targets_audit.json': [
        'data/processed/observed/published_mode_splits.csv',
        'data/processed/observed/census_2011_b28_commuting.csv',
        'data/processed/observed/water_annual_passengers.csv',
        'data/processed/observed/economic_survey_metro_controls.csv',
        'data/processed/acquisition/ogd_metro_ridership_audit.json',
        'demand/population/B1_synthetic_population.csv',
        'registry/B_targets.json'],
}
OUT = 'data/processed/validation/mode_targets_by_mode.csv'
AUDIT = 'data/processed/validation/_mode_targets_audit.json'
COLUMNS = ['mode', 'target_pct', 'denominator', 'status', 'sweep_low', 'sweep_high', 'basis',
           'target_mean_km', 'mean_km_basis']
DENOM = 'resident person trips'


def rows(relative):
    with Path(city.path(relative)).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    cfg = registry.load()
    area, year = cfg.get('B.targets.published_split_area'), int(cfg.get('B.targets.published_split_year'))
    active_sweep = cfg.get('B.targets.active_share_sweep_pp')
    port_groups = cfg.get('B.targets.ferry_port_groups')
    goods_share = float(cfg.get('B.targets.goods_vehicle_traffic_share_pct'))
    splits = [r for r in rows('data/processed/observed/published_mode_splits.csv')
              if r['area'] == area and int(r['survey_year']) == year]
    motorised = {r['mode_raw']: float(r['share_pct']) for r in splits if r['share_basis'].startswith('motorised')}
    active = [float(r['share_pct']) for r in splits if r['mode_raw'].startswith('Active modes')]
    if not active or 'Train' not in motorised:
        raise SystemExit('the published splits carry no %s %d table or active share' % (area, year))
    active_pct = active[0]
    m = (100.0 - active_pct) / 100.0                     # motorised trips as a share of all trips
    lo_m, hi_m = (100.0 - (active_pct + active_sweep)) / 100.0, (100.0 - (active_pct - active_sweep)) / 100.0

    # walk : bicycle from B-28, the four districts summed
    b28 = {}
    for r in rows('data/processed/observed/census_2011_b28_commuting.csv'):
        if r['residence'] == 'Total' and r['distance_band_km_raw'] == 'Total':
            b28[r['mode_raw']] = b28.get(r['mode_raw'], 0.0) + float(r['persons_count'])
    bicycle_of_active = b28['Bicycle'] / (b28['Bicycle'] + b28['On foot'])

    # car driver : car passenger from the synthesised population
    drivers = riders = 0
    for chunk in pd.read_csv(city.path('demand/population/B1_synthetic_population.csv'),
                             usecols=['age', 'household_cars', 'car_available'], chunksize=2_000_000):
        in_car_hh = chunk[(chunk['household_cars'] > 0) & (chunk['age'] >= 5)]
        drivers += int((in_car_hh['car_available'] > 0).sum())
        riders += int((in_car_hh['car_available'] == 0).sum())
    passenger_share = riders / (drivers + riders)

    # ferry: MMB annual passengers of the MMR port groups, the newest year, to a day
    water = [r for r in rows('data/processed/observed/water_annual_passengers.csv')
             if r['port_group'] in port_groups and r['parse_status'] == 'numeric']
    newest = max(r['financial_year'] for r in water)
    annual = sum(float(r['reported_passengers_count']) for r in water if r['financial_year'] == newest)
    daily_trips_all = sum(float(r['trips_per_day']) for r in splits
                          if r['mode_raw'] == 'Total' and r['share_basis'].startswith('motorised')) / m
    ferry_pct = 100.0 * (annual / 365.0) / daily_trips_all

    def motor(mode_raw):
        s = motorised[mode_raw]
        return round(s * m, 4), round(s * lo_m, 4), round(s * hi_m, 4)

    cts = 'CTS Updation Table 6-8 (%s, %d) motorised share %%s x (1 - active share %s%%%%)' % (area, year, active_pct)
    car_all, car_lo, car_hi = motor('Car')
    out = []
    for mode, raw in (('bus', 'Bus'), ('heavy_rail', 'Train'),
                      ('motorbike', 'Two-Wheeler'), ('taxi', 'Taxi'), ('auto_rickshaw', 'Rickshaw')):
        t, lo, hi = motor(raw)
        out.append(dict(mode=mode, target_pct=t, denominator=DENOM, status='derived', sweep_low=lo, sweep_high=hi,
                        basis=(cts % (raw + ' ' + str(motorised[raw]))), target_mean_km='', mean_km_basis=''))
    # metro and monorail: the operators' observed daily passengers, not the
    # 2017 split (2.2 % of motorised trips when Line 1 and the Monorail were
    # the network): MMRDA's daily series for Lines 2A/7 and the Monorail (OGD,
    # the weekday mean of the latest three full months) and the Economic
    # Survey's average daily passengers for Line 1, Line 3 and Navi Mumbai
    # Line 1 (2024-25), summed against the CTS's all-mode daily trips. The
    # sweep spans the Economic Survey's own 2A/7 figure (the 2024-25 average,
    # below the latest weekday mean) and the CTS share's upper edge.
    ogd = json.loads(Path(city.path('data/processed/acquisition/ogd_metro_ridership_audit.json')).read_text(encoding='utf-8'))['lines']
    survey = {r['control_group_id']: float(r['average_passengers_per_day_lakh']) * 100000
              for r in rows('data/processed/observed/economic_survey_metro_controls.csv')
              if r['control_group_id'].startswith(('mumbai', 'navi'))}
    ogd_2a7 = ogd['ogd_metro_2a_7_ridership_daily_2024_2025']['weekday_mean_latest_three_months']
    ogd_mono = ogd['ogd_monorail_ridership_daily_2024_2025']['weekday_mean_latest_three_months']
    other = sum(v for k, v in survey.items() if k != 'mumbai_2a_7')
    daily_metro = ogd_2a7 + ogd_mono + other
    daily_metro_survey = survey['mumbai_2a_7'] + ogd_mono + other
    metro_pct = 100.0 * daily_metro / daily_trips_all
    metro_lo = 100.0 * daily_metro_survey / daily_trips_all
    peak_2a7 = max(ogd['ogd_metro_2a_7_ridership_daily_2024_2025']['weekday_mean_by_month'].values())
    metro_hi = 100.0 * (peak_2a7 + ogd_mono + other) / daily_trips_all   # the series' busiest month
    out.append(dict(mode='metro', target_pct=round(metro_pct, 4), denominator=DENOM, status='derived',
                    sweep_low=round(min(metro_lo, metro_pct), 4), sweep_high=round(metro_hi, 4),
                    basis='operators\' daily passengers %d against the CTS all-mode daily trips %d: Lines 2A and 7 %d '
                          '(MMRDA OGD daily series, weekday mean of %s), Monorail %d (OGD, %s), Line 1 %d, Line 3 %d, '
                          'Navi Mumbai Line 1 %d (Economic Survey 2025-26 average daily passengers 2024-25); the low '
                          'bound takes the Survey\'s 2A/7 average %d, the high the series\' busiest weekday month %d; metro and '
                          'monorail read as one target'
                          % (round(daily_metro), round(daily_trips_all), ogd_2a7,
                             '-'.join(ogd['ogd_metro_2a_7_ridership_daily_2024_2025']['latest_full_months']),
                             ogd_mono, '-'.join(ogd['ogd_monorail_ridership_daily_2024_2025']['latest_full_months']),
                             survey['mumbai_1'], survey['mumbai_3'], survey['navi_mumbai_1'], survey['mumbai_2a_7'], peak_2a7),
                    target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='car', target_pct=round(car_all * (1 - passenger_share), 4), denominator=DENOM, status='derived',
                    sweep_low=round(car_lo * (1 - passenger_share), 4), sweep_high=round(car_hi * (1 - passenger_share), 4),
                    basis=(cts % ('Car ' + str(motorised['Car']))) + '; driver share %.4f of persons aged 5+ in car-owning '
                    'households of the synthesised population (licence holders with a car available: %d of %d)'
                    % (1 - passenger_share, drivers, drivers + riders), target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='ride', target_pct=round(car_all * passenger_share, 4), denominator=DENOM, status='derived',
                    sweep_low=round(car_lo * passenger_share, 4), sweep_high=round(car_hi * passenger_share, 4),
                    basis=(cts % ('Car ' + str(motorised['Car']))) + '; passenger share %.4f (the complement of the driver '
                    'share); rests on B.baseline.licence_given_vehicle_probability' % passenger_share,
                    target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='walk', target_pct=round(active_pct * (1 - bicycle_of_active), 4), denominator=DENOM, status='derived',
                    sweep_low=round((active_pct - active_sweep) * (1 - bicycle_of_active), 4),
                    sweep_high=round((active_pct + active_sweep) * (1 - bicycle_of_active), 4),
                    basis='CTS Updation household survey: active modes about %s%% of all trips; walk share of active %.4f '
                    'from Census 2011 B-28 (On foot %d, Bicycle %d, four districts)'
                    % (active_pct, 1 - bicycle_of_active, b28['On foot'], b28['Bicycle']), target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='bike', target_pct=round(active_pct * bicycle_of_active, 4), denominator=DENOM, status='derived',
                    sweep_low=round((active_pct - active_sweep) * bicycle_of_active, 4),
                    sweep_high=round((active_pct + active_sweep) * bicycle_of_active, 4),
                    basis='CTS Updation household survey: active modes about %s%% of all trips; bicycle share of active %.4f '
                    'from Census 2011 B-28 (a commute series; the only one separating bicycle from foot)'
                    % (active_pct, bicycle_of_active), target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='ferry', target_pct=round(ferry_pct, 4), denominator=DENOM, status='derived',
                    sweep_low=round(ferry_pct * lo_m / m, 4), sweep_high=round(ferry_pct * hi_m / m, 4),
                    basis='Maharashtra Maritime Board published passengers %s, port groups %s: %d a year / 365 against '
                    '%.0f daily trips (CTS motorised trips / (1 - active share)); journey definition unverified'
                    % (newest, ', '.join(port_groups), annual, daily_trips_all), target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='truck', target_pct=goods_share, denominator='road vehicles at the CMP screenlines (traffic composition)',
                    status='observed', sweep_low='', sweep_high='',
                    basis='CMP for Greater Mumbai executive summary: goods vehicles %s%% of screenline traffic; a level the '
                    'reporter prints beside the network-wide road-vehicle share, not a share of resident trips' % goods_share,
                    target_mean_km='', mean_km_basis=''))
    out.append(dict(mode='freight_train', target_pct='', denominator='train movements', status='not_simulated',
                    sweep_low='', sweep_high='',
                    basis='no freight movement in the citywide plans (9.205); the Mumbai Port rake statistics are acquired '
                    '(mumbai_port_rail_statistics) and represent the movements once a path exists',
                    target_mean_km='', mean_km_basis=''))
    order = ['car', 'ride', 'walk', 'bike', 'motorbike', 'taxi', 'auto_rickshaw', 'bus', 'heavy_rail', 'metro',
             'ferry', 'truck', 'freight_train']
    out.sort(key=lambda r: order.index(r['mode']))
    path = Path(city.path(OUT))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator='\n')
        w.writeheader()
        w.writerows(out)
    share_rows = [r for r in out if r['denominator'] == DENOM]
    audit = dict(source='derived', published_split=dict(area=area, year=year, active_share_pct=active_pct,
                                                        motorised_shares=motorised),
                 bicycle_share_of_active=bicycle_of_active, car_passenger_share=passenger_share,
                 car_household_persons=dict(drivers=drivers, riders=riders),
                 ferry=dict(financial_year=newest, annual_passengers=annual, daily_trips_all_modes=daily_trips_all),
                 sum_of_share_targets_pct=round(sum(r['target_pct'] for r in share_rows), 4),
                 inputs_sha256={p: fingerprint(Path(city.path(p))) for p in OUTPUT_INPUTS[OUT]
                                if Path(city.path(p)).exists()},
                 limitations=['Survey years 2017 (CTS), 2014 (CMP), 2011 (B-28), %s (MMB) against a 2026 base year; '
                              'no projection is applied.' % newest,
                              'The active share is printed "about 47 %"; the sweep on every derived row carries '
                              '+/- B.targets.active_share_sweep_pp.',
                              'The car-driver split rests on the synthesised licence assumption, not a survey.',
                              'The ferry passenger count\'s journey definition is unverified.',
                              'The 67/143 validation split of the reference city has no counterpart here; every row '
                              'is a calibration target and no holdout exists yet.'])
    Path(city.path(AUDIT)).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n',
                                      encoding='utf-8', newline='\n')
    for r in out:
        print('%-14s %8s  %s' % (r['mode'], r['target_pct'], r['status']))
    print('sum of share targets %.2f %%' % audit['sum_of_share_targets_pct'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
