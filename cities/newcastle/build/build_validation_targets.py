#!/usr/bin/env python
"""Validation targets, split into calibration and holdout sets.

Proposal s9 requires holding out validation targets and reporting fit on unseen
counts, precisely because calibrating mode constants to observed patronage risks
fitting away the effect under test (ASC absorption).

Split rule, fixed before any scenario is run:
  calibration - aggregate light rail and bus patronage, traffic counts at
                permanent stations, and HTS mode share
  holdout     - stop-level light rail boardings, station entries/exits, and
                traffic counts at sample (non-permanent) stations
"""

# This builder encodes THIS CITY's intervention, corridor or history, so it lives
# with the city rather than in the framework. It still uses the framework's
# generic machinery, which is two directories up.
import os as _os
import sys as _sys
_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.dirname(_os.path.abspath(__file__)))))
_sys.path.insert(0, _os.path.join(_REPO, 'src'))
_sys.path.insert(0, _os.path.join(_REPO, 'src', 'build'))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402
import os
import json
import pandas as pd

CFG = _registry.load()
# How dense censoring may get before the exclusion of censored cells from the
# holdout station means stops being a marginal treatment (#129, 9.142).
CENSORED_SHARE_MAX = CFG.get('CAL.pt.censored_share_max')

OBS = _city.path('data/processed/observed')
HTS = _city.path('data/processed/hts')
CEN = _city.path('data/processed/census')
COR = _city.path('data/processed/corridor')
OUT = _city.path('data/processed/validation')
os.makedirs(OUT, exist_ok=True)

rows = []


def add(metric, geography, period, value, unit, source, split, note=''):
    rows.append(dict(target_id='V%03d' % (len(rows) + 1), metric=metric,
                     geography=geography, period=period, value=value, unit=unit,
                     source=source, split=split, note=note))


def escort_legs():
    """Escort legs in the committed weekday demand, counted rather than stated.

    The note this feeds asserted a fact about the demand for three phases after
    the 9.15 repair made it false (DECISIONS.md 9.142). A count measured at
    build time cannot go stale; where the demand is not built yet it says so
    rather than guessing a number.
    """
    path = _city.path('demand/plans/B2_activity_trips_WEEKDAY.csv')
    if not os.path.exists(path):
        return 'count unavailable - the weekday trip table is not built'
    n = 0
    with open(path, encoding='utf-8') as fh:
        for r in __import__('csv').DictReader(fh):
            if r.get('purpose') == 'HX':
                n += 1
    return '%s weekday legs' % format(n, ',d')


def main():
    # ---------------- light rail patronage ----------------
    lr = pd.read_csv(os.path.join(OBS, 'opal_lr_newcastle_by_month_cardtype.csv'))
    lr['Trip'] = pd.to_numeric(lr['Trip'], errors='coerce')
    m = lr.groupby('Year_Month', sort=False)['Trip'].sum()

    def parse_ym(s):
        for f in ('%b-%y', '%b-%Y', '%Y-%m'):
            try:
                return pd.to_datetime(s, format=f)
            except Exception:
                pass
        return pd.NaT
    idx = pd.Series([parse_ym(x) for x in m.index], index=m.index)
    ser = pd.DataFrame({'d': idx, 'trips': m.values}).dropna().sort_values('d')
    # pre-pandemic window: the Opal light rail series starts at opening, so a
    # clean post-opening pre-pandemic baseline does exist (Mar 2019 - Feb 2020)
    pre = ser[(ser.d >= '2019-03-01') & (ser.d < '2020-03-01')]
    cur = ser[ser.d >= '2025-07-01']
    if len(pre):
        add('lr_boardings_monthly_mean', 'Newcastle Light Rail', '2019-03..2020-02',
            round(float(pre.trips.mean()), 0), 'boardings/month',
            'TfNSW Opal Trips - Light Rail', 'calibration',
            'Post-opening, pre-pandemic baseline')
        add('lr_boardings_daily_mean', 'Newcastle Light Rail', '2019-03..2020-02',
            round(float(pre.trips.mean()) / 30.4, 0), 'boardings/day',
            'TfNSW Opal Trips - Light Rail', 'calibration', 'Derived from monthly')
    if len(cur):
        add('lr_boardings_monthly_mean', 'Newcastle Light Rail', '2025-07..latest',
            round(float(cur.trips.mean()), 0), 'boardings/month',
            'TfNSW Opal Trips - Light Rail', 'calibration',
            'Post-2024 methodology epoch; not comparable with pre-2024 series')
    ser.assign(Year_Month=ser.index).to_csv(
        os.path.join(OUT, 'lr_monthly_series.csv'), index=False)

    # card-type mix, used to segment fares and concession behaviour
    mix = lr.groupby('Card_type')['Trip'].sum()
    tot = mix.sum()
    for k, v in mix.items():
        add('lr_cardtype_share', 'Newcastle Light Rail', 'all',
            round(float(v) / tot * 100, 2), 'per cent',
            'TfNSW Opal Trips - Light Rail', 'calibration', str(k))

    # ---------------- light rail by stop (HOLDOUT) ----------------
    st = pd.read_csv(os.path.join(OBS, 'opal_lr_newcastle_by_stop.csv'))
    st['Trip'] = pd.to_numeric(st['Trip'], errors='coerce')
    bystop = st.groupby('Location')['Trip'].sum().sort_values(ascending=False)
    tots = bystop.sum()
    for k, v in bystop.items():
        add('lr_tapon_share_by_stop', str(k), 'to 2024-06',
            round(float(v) / tots * 100, 2), 'per cent of tap-ons',
            'TfNSW Opal Light Rail by tap-on station', 'holdout',
            'Pre-2024 methodology epoch')
    bystop.to_frame('taps').to_csv(os.path.join(OUT, 'lr_taps_by_stop.csv'))

    # ---------------- bus patronage ----------------
    bus = pd.read_csv(os.path.join(OBS, 'opal_bus_newcastle_hunter.csv'))
    bus['Trip'] = pd.to_numeric(bus['Trip'], errors='coerce')
    bm = bus.groupby('Year_Month', sort=False)['Trip'].sum()
    bidx = pd.Series([parse_ym(x) for x in bm.index], index=bm.index)
    bser = pd.DataFrame({'d': bidx, 'trips': bm.values}).dropna().sort_values('d')
    bpre = bser[(bser.d >= '2019-03-01') & (bser.d < '2020-03-01')]
    if len(bpre):
        add('bus_boardings_monthly_mean', 'NISC 1 contract region', '2019-03..2020-02',
            round(float(bpre.trips.mean()), 0), 'boardings/month',
            'TfNSW Opal Trips - Bus (NISC 1)', 'calibration', '')
    bser.assign(Year_Month=bser.index).to_csv(
        os.path.join(OUT, 'bus_monthly_series.csv'), index=False)

    # LR share of Newcastle PT, the A1 falsification metric
    if len(pre) and len(bpre):
        share = float(pre.trips.mean()) / (float(pre.trips.mean()) + float(bpre.trips.mean())) * 100
        add('lr_share_of_local_pt_boardings', 'Newcastle (LR + NISC 1 bus)',
            '2019-03..2020-02', round(share, 2), 'per cent',
            'Derived from TfNSW Opal', 'calibration',
            'Hypothesis A1 falsifies below about 10 per cent. Boardings, not '
            'person-legs; the model must reproduce the person-leg version.')

    # ---------------- station entries/exits (HOLDOUT) ----------------
    # Censoring: a station-month the Opal series reports as the text
    # "Less than 50" is EXCLUDED from these means, and that exclusion is the
    # PRE-REGISTERED treatment of these 143 holdout rows, not an oversight
    # (#129, DECISIONS.md 9.142). The mode-target builder counts a censored
    # cell as the declared CAL.pt.censored_cell_value instead, because its
    # heavy-rail boardings target is a SUM over stations where dropping a cell
    # would drop a station's whole contribution; here the quantity is a MEAN
    # per station-and-direction, where one censored month among many is
    # missing data rather than a zero. The two rules differ because the two
    # statistics differ, and the difference is recorded rather than unified.
    #
    # It is safe only while censoring stays marginal, so the builder MEASURES
    # that rather than assuming it: the guard below refuses to write a target
    # whose mean rests on nothing, or a series where censoring has spread far
    # enough to bias a mean it silently drops cells from.
    se = pd.read_csv(os.path.join(OBS, 'station_entries_exits_newcastle.csv'))
    se['Trip_num'] = pd.to_numeric(se['Trip'], errors='coerce')
    se['censored'] = se['Trip_num'].isna() & se['Trip'].notna()
    n_cens = int(se['censored'].sum())
    grp = se.groupby(['Station', 'Entry_Exit'])
    cens_by_group = grp['censored'].sum()
    size_by_group = grp['censored'].size()
    empty = sorted('%s/%s' % k for k in
                   size_by_group.index[(cens_by_group == size_by_group).to_numpy()])
    if empty:
        raise SystemExit(
            'every cell is censored for %d station-direction group(s): %s. '
            'Excluding censored cells would delete a PRE-REGISTERED holdout '
            'row, which the 9.13 rule forbids after the fact - decide the '
            'treatment (#129) before rebuilding.' % (len(empty), empty))
    heavy_entry = se[se['Station_Type'].astype(str).str.strip().str.lower().eq('train')
                     & se['Entry_Exit'].astype(str).str.strip().str.lower().eq('entry')]
    n_heavy_cens = int(heavy_entry['censored'].sum())
    if n_heavy_cens:
        raise SystemExit(
            '%d censored cell(s) now fall in the (Train, Entry) series the '
            'heavy-rail boardings target sums (DECISIONS.md 9.130). That '
            'target counts a censored cell as CAL.pt.censored_cell_value '
            'while these holdout means exclude it; the two rules only agree '
            'while this series carries none (#129).' % n_heavy_cens)
    cens_share = n_cens / float(len(se)) if len(se) else 0.0
    if cens_share > CENSORED_SHARE_MAX:
        raise SystemExit(
            'censored cells are %.2f%% of the station series against a %.2f%% '
            'ceiling: exclusion is no longer a marginal treatment and the '
            'means it produces are biased upward (#129).'
            % (100 * cens_share, 100 * CENSORED_SHARE_MAX))
    g = grp['Trip_num'].mean().reset_index()
    note = ('Values reported as "Less than 50" are censored and EXCLUDED - the '
            'pre-registered treatment of these holdout rows (#129, '
            'DECISIONS.md 9.142). %d of %d cells in the series are censored, '
            'none of them in the (Train, Entry) series the heavy-rail target '
            'sums, and no station-direction group is wholly censored.'
            % (n_cens, len(se)))
    for _, r in g.iterrows():
        if pd.isna(r['Trip_num']):
            continue
        add('station_%s_monthly_mean' % str(r['Entry_Exit']).lower(),
            str(r['Station']).strip(), 'from 2024-11',
            round(float(r['Trip_num']), 0), 'trips/month',
            'TfNSW station entries and exits (Opal batch)', 'holdout', note)
    g.to_csv(os.path.join(OUT, 'station_entries_exits_mean.csv'), index=False)

    # ---------------- road traffic ----------------
    aadt = pd.read_csv(os.path.join(OBS, 'traffic_aadt.csv'), low_memory=False)
    stn = pd.read_csv(os.path.join(OBS, 'traffic_count_stations_newcastle.csv'), low_memory=False)
    aadt['traffic_count'] = pd.to_numeric(aadt['traffic_count'], errors='coerce')
    # Most study-area sites are sample stations counted once every few years, so
    # take each station's most recent survey year rather than a fixed window, and
    # carry the year through so the calibration report can weight by recency.
    #
    # `period` MUST be filtered. The RMS extract publishes seven periods per
    # station-year - ALL DAYS, WEEKDAYS, WEEKENDS, AM PEAK, PM PEAK, OFF PEAK
    # and PUBLIC HOLIDAYS - and the first cut of this file filtered on
    # classification and direction but not on period, then took the station
    # mean. Every target was therefore a daily total averaged together with
    # peak-period counts: station 55710 in 2021 has ALL DAYS = 50,133 and was
    # recorded as 33,114. Across all 119 stations the recorded value came out
    # 0.58-0.71x the true figure, and because the number of period rows varies
    # by station it was not even a constant rescaling that a calibration
    # constant could absorb. DECISIONS.md 12.2.
    #
    # The basis is WEEKDAYS, not ALL DAYS: the model runs a weekday day type,
    # and WEEKDAYS is published for every one of the 119 stations. ALL DAYS is
    # carried alongside so the weekday choice stays visible rather than baked in.
    PERIOD = 'WEEKDAYS'
    aadt['cls'] = aadt['classification_type'].astype(str).str.upper()
    aadt['dirn'] = aadt['traffic_direction_name'].astype(str).str.upper()
    aadt['per'] = aadt['period'].astype(str).str.upper()
    two_way = aadt[aadt['dirn'].eq('PRESCRIBED AND COUNTER')
                   & aadt['traffic_count'].notna()]
    allveh = two_way[two_way['cls'].isin(['ALL VEHICLES', 'UNCLASSIFIED'])]
    sel = allveh[allveh['per'].eq(PERIOD)]
    # Most study-area sites are sample stations counted once every few years, so
    # take each station's most recent survey year rather than a fixed window, and
    # carry the year through so the calibration report can weight by recency.
    latest_year = sel.groupby('station_key')['year'].max()
    sel = sel.merge(latest_year.rename('yr_max'), on='station_key')
    sel = sel[sel['year'] == sel['yr_max']]
    perm = set(stn.loc[stn['permanent_station'].astype(str).isin(['1', 'True', 'true']),
                       'station_key'].astype(str))
    key = sel.groupby('station_key')['traffic_count'].mean()
    kyear = sel.groupby('station_key')['year'].max()

    def period_value(station, year, period, cls_filter):
        s = two_way[(two_way['station_key'] == station) & (two_way['year'] == year)
                    & two_way['per'].eq(period) & two_way['cls'].isin(cls_filter)]
        return float(s['traffic_count'].mean()) if len(s) else float('nan')

    meta = stn.set_index('station_key')[['name', 'road_name', 'suburb', 'lga',
                                         'wgs84_latitude', 'wgs84_longitude']]
    out = []
    for k, v in key.items():
        if pd.isna(v):
            continue
        mrow = meta.loc[k] if k in meta.index else None
        if mrow is None:
            continue
        if isinstance(mrow, pd.DataFrame):
            mrow = mrow.iloc[0]
        split = 'calibration' if str(k) in perm else 'holdout'
        yr = int(kyear.get(k, 0))
        all_days = period_value(k, yr, 'ALL DAYS', ['ALL VEHICLES', 'UNCLASSIFIED'])
        light = period_value(k, yr, PERIOD, ['LIGHT VEHICLES'])
        heavy = period_value(k, yr, PERIOD, ['HEAVY VEHICLES'])
        # Heavy-vehicle share is observed at the minority of stations that carry
        # a classified count. It is the handle on the freight the model does not
        # represent; where it is absent the comparison has to sweep it instead
        # (DECISIONS.md 12.2), so it is recorded per station rather than filled.
        heavy_share = (heavy / (light + heavy)
                       if light == light and heavy == heavy and (light + heavy) > 0
                       else float('nan'))
        add('road_aadt', '%s (%s, %s)' % (mrow['name'], mrow['suburb'], mrow['lga']),
            str(yr), round(float(v), 0), 'vehicles/weekday',
            'NSW Roads traffic volume counts', split,
            'station_key=%s; latest survey year; period=%s, two-way, all classes'
            % (k, PERIOD))
        out.append(dict(station_key=k, name=mrow['name'], road_name=mrow['road_name'],
                        suburb=mrow['suburb'], lga=mrow['lga'],
                        lat=mrow['wgs84_latitude'], lon=mrow['wgs84_longitude'],
                        weekday_count=round(float(v), 0), period=PERIOD,
                        all_days_count=(round(all_days, 0) if all_days == all_days
                                        else ''),
                        light_vehicles=(round(light, 0) if light == light else ''),
                        heavy_vehicles=(round(heavy, 0) if heavy == heavy else ''),
                        heavy_share=(round(heavy_share, 4)
                                     if heavy_share == heavy_share else ''),
                        heavy_share_source=('observed' if heavy_share == heavy_share
                                            else 'not_classified_at_this_station'),
                        survey_year=yr, split=split))
    aadt_out = pd.DataFrame(out)
    aadt_out.to_csv(os.path.join(OUT, 'road_aadt_targets.csv'), index=False)

    # ---------------- comparison corrections for the count targets -----------
    # A modelled link volume is not directly comparable to an observed
    # all-classes count, and the difference must be stated rather than absorbed
    # by a calibrated constant (DECISIONS.md 12.2a). Written as a parameter
    # artefact rather than left in prose so the sweep-range rule can be tested.
    obs = aadt_out[aadt_out['heavy_share_source'] == 'observed']
    hs = pd.to_numeric(obs['heavy_share'], errors='coerce').dropna()
    corr = {
        'heavy_vehicle_share': {
            'value': round(float(hs.median()), 4),
            'sweep': [round(float(hs.min()), 4), round(float(hs.max()), 4)],
            'source': 'measured - NSW Roads traffic volume counts, LIGHT vs '
                      'HEAVY VEHICLES classification, %s period, two-way' % PERIOD,
            'stations_observed': int(len(hs)),
            'stations_total': int(len(aadt_out)),
            'calibration_stations_observed':
                int((obs['split'] == 'calibration').sum()),
            'mean': round(float(hs.mean()), 4),
            'note': 'The model represents no freight. At the %d stations with a '
                    'classified count the station\'s own observed share is used; '
                    'at the remaining %d it is assumed, and the sweep is the '
                    'observed range across the classified stations. Only %d of '
                    'the 34 calibration stations carry a classified count, so '
                    'the assumed case is the usual one.'
                    % (len(hs), len(aadt_out) - len(hs),
                       int((obs['split'] == 'calibration').sum())),
        },
        'vehicles_per_leg': {
            'car': 1.0,
            'ride': 0.0,
            'source': 'derived - HTS vehicle occupancy 1.3503 persons per '
                      'vehicle (params/C4_mode_constraints.json) means observed '
                      'vehicle trips ARE driver trips',
            # 9.142: this note is MEASURED from the demand each build rather
            # than asserted. It used to say "B2 generates none" of the escort
            # trip, which the 9.15 repair had made false; the committed
            # artefact was corrected by hand and this producer was not, so
            # every run of this builder silently reverted the correction.
            'note': 'A passenger rides in a vehicle that is already counted, so '
                    'the modelled vehicle count is the car legs alone and a ride '
                    'leg correctly contributes none. This holds only while the '
                    'modelled ride:car ratio matches the observed '
                    'passenger:driver ratio, which is what DECISIONS.md 9.8 '
                    'constrains asc_car_passenger to reproduce. Escort tours ARE '
                    'generated since the 9.15 repair - B2 carries HX as its own '
                    'tour purpose (%s), driven by the escorting licence holder. '
                    'What stays genuinely unmodelled here is freight '
                    '(issue 24).' % escort_legs(),
        },
    }
    json.dump(corr, open(_city.path('params', 'C3_count_comparison.json'), 'w'),
              indent=2)

    # ---------------- mode share ----------------
    hm = pd.read_csv(os.path.join(HTS, 'hts_mode.csv'))
    hm['MODE_SHARE'] = pd.to_numeric(hm['MODE_SHARE'], errors='coerce')
    for yr, split in [('2018/19', 'calibration'), ('2024/25', 'calibration')]:
        sel = hm[(hm.geography == 'lga') & (hm.area_name.str.strip() == 'Newcastle') &
                 (hm.FINANCIAL_YEAR.astype(str) == yr)]
        for _, r in sel.iterrows():
            if pd.isna(r['MODE_SHARE']):
                continue
            add('hts_mode_share', 'Newcastle LGA', yr, float(r['MODE_SHARE']),
                'per cent of trips', 'NSW Household Travel Survey', split,
                str(r['TRAVEL_MODE']).strip())

    # ---------------- corridor run time ----------------
    if os.path.exists(os.path.join(COR, '_corridor_report.json')):
        cr = json.load(open(os.path.join(COR, '_corridor_report.json')))
        for d, v in cr['scheduled_end_to_end_s'].items():
            add('lr_scheduled_runtime', 'Newcastle Light Rail direction %s' % d, '2026',
                round(v / 60.0, 2), 'minutes', 'TfNSW GTFS base2026', 'calibration',
                'Scheduled, not observed. Observed run time requires GTFS-Realtime.')
        add('lr_alignment_length', 'Newcastle Light Rail', '2026',
            round(list(cr['alignment_length_m'].values())[0], 0), 'metres',
            'TfNSW GTFS shapes', 'calibration', '')

    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(OUT, 'validation_targets.csv'), index=False)
    rep = dict(n_targets=len(d),
               by_split=d['split'].value_counts().to_dict(),
               by_metric=d['metric'].value_counts().to_dict())
    json.dump(rep, open(os.path.join(OUT, '_validation_report.json'), 'w'), indent=2)
    print(json.dumps(rep, indent=2))
    print('\nheadline targets:')
    for m in ['lr_boardings_daily_mean', 'lr_share_of_local_pt_boardings',
              'lr_scheduled_runtime', 'lr_alignment_length']:
        for _, r in d[d.metric == m].iterrows():
            print('  %-34s %-42s %10s %s' % (r['metric'], r['geography'][:42],
                                             r['value'], r['unit']))


if __name__ == '__main__':
    main()
