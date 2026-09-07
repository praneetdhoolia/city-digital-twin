#!/usr/bin/env python
"""Per-mode ridership targets: one row per mode this city simulates.

`validation_targets.csv` carries the survey's OWN categories, and the survey
folds. The NSW Household Travel Survey publishes six of them (its data document,
`hts_data_document_2020_2024.pdf`, quoted verbatim below), so five modes the
model simulates separately share a target with another mode, and four share one
target between them:

    Vehicle driver       -> car + motorbike
    Vehicle passenger    -> ride
    Public Transport     -> bus + light rail + heavy rail + ferry
      "(includes Train, Metro, Bus, Light Rail, Ferry)"
    Other                -> bike + taxi
      "(includes Taxi/rideshare/carshare, wheelchair, bicycle, aircraft)"
    Walk only            -> walk
    Walk linked          -> 0.0 by construction (MODE_SHARE excludes it)

The standing directive is that EVERY mode is checked individually against real
life, which a folded target cannot answer: a fold hides an excess in one member
behind a deficit in the other. This builder disaggregates the folded HTS levels
using the composition measured from OTHER observed artefacts in this package,
and writes one row per mode with the derivation it came from.

**It does not invent an observation.** Every number here is either an HTS level,
a count measured from an acquired artefact, or the product of the two - and the
transfer each product relies on (a commute composition standing in for an
all-purpose one; a boardings composition standing in for a linked-trip one) is
NOT free. It is the modelling choice in this file, it is declared in the
registry with a sweep, and the sweep is written into every row so no reader can
mistake a derived target for a measured one.

**These targets are deliberately NOT added to `validation_targets.csv`.** They
are a disaggregation of targets already in that file, so scoring them beside
their own parents would count the same observation twice, move the reported
MAE for a reason that is not a model change, and disturb the 67/143 split.
`fit.py` is untouched; this is a second, finer view of the same observation.

Outputs `data/processed/validation/mode_targets_by_mode.csv`.
"""

# This builder encodes THIS CITY's survey vocabulary and patronage sources, so
# it lives with the city rather than in the framework.
import os as _os
import sys as _sys
_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.dirname(_os.path.abspath(__file__)))))
_sys.path.insert(0, _os.path.join(_REPO, 'src'))
_sys.path.insert(0, _os.path.join(_REPO, 'src', 'build'))
import city as _city  # noqa: E402
import os
import re
import csv
import io as _io
import json
import zipfile
import collections
import pandas as pd

import registry as _registry  # noqa: E402

_CENSORED = None


def _censored():
    """What a censored Opal cell ('Less than 50') counts as: the declared
    CAL.pt.censored_cell_value (#129), never a literal. Three builders once
    treated the same cell three ways - excluded, zero, and a crash."""
    global _CENSORED
    if _CENSORED is None:
        _CENSORED = float(_registry.load().get('CAL.pt.censored_cell_value'))
    return _CENSORED


def _trip_cell(raw):
    """A Trip cell to a number: numeric text as it is, an empty cell as 0,
    a censored cell as the declared value."""
    s = str(raw if raw is not None else '').replace(',', '').strip()
    if not s or s.lower() == 'nan':
        return 0.0
    try:
        return float(s)
    except ValueError:
        return _censored()

OBS = _city.path('data/processed/observed')
HTS = _city.path('data/processed/hts')
CEN = _city.path('data/processed/census')
OUT = _city.path('data/processed/validation')
ZON = _city.path('data/processed/zones')

MON = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05',
       'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10',
       'Nov': '11', 'Dec': '12'}

# The G62 one-method journey-to-work columns, by the mode each one names.
G62 = {
    'train': 'One_method_Train_P',
    'bus': 'One_method_Bus_P',
    'ferry': 'One_method_Ferry_P',
    'tram': 'One_met_Tram_or_lt_rail_P',
    'taxi': 'One_met_Taxi_or_Rideshare_P',
    'car': 'One_method_Car_as_driver_P',
    'car_passenger': 'One_method_Car_as_passenger_P',
    'truck': 'One_method_Truck_P',
    'motorbike': 'One_method_Motorbike_scootr_P',
    'bike': 'One_method_Bicycle_P',
    'walk': 'One_method_Walked_only_P',
}


def hts_trip_means():
    """Observed mean trip length by the survey's OWN mode category.

    Published beside the mode shares as TRIP_AVG_DISTANCE and carried into
    `hts_mode.csv` at acquisition. A folded category's mean applies to every
    mode inside it - four public transport modes share one - so the row says
    which category it came from and a reader can see when a mean is shared.
    """
    year = _city.readers().survey_vintage()
    lga = _city.target_lga()
    hm = pd.read_csv(os.path.join(HTS, 'hts_mode.csv'))
    sel = hm[(hm.geography == 'lga')
             & (hm.area_name.str.strip() == lga)
             & (hm.FINANCIAL_YEAR.astype(str) == year)]
    out = {}
    for _, r in sel.iterrows():
        key = str(r['TRAVEL_MODE']).strip().rstrip('*').strip().lower()
        v = pd.to_numeric(r.get('TRIP_AVG_DISTANCE'), errors='coerce')
        if pd.notna(v):
            out[key] = float(v)
    return out


# Which survey category each simulated mode takes its observed mean from.
MEAN_CATEGORY = {
    'car': 'vehicle driver',
    'motorbike': 'vehicle driver',
    'ride': 'vehicle passenger',
    'walk': 'walk only',
    'bike': 'other',
    'taxi': 'other',
    'bus': 'public transport',
    'heavy_rail': 'public transport',
    'light_rail': 'public transport',
    'ferry': 'public transport',
}


def hts_levels(cfg):
    """The current-vintage HTS category levels for this city's target LGA.

    The vintage and the LGA literal are the CITY's, and both already have an
    accessor - `fit.py` reads the same two. Re-declaring them here would put
    one fact in two places, which is the failure the doc-currency gate exists
    for.
    """
    year = _city.readers().survey_vintage()
    lga = _city.target_lga()
    hm = pd.read_csv(os.path.join(HTS, 'hts_mode.csv'))
    hm['MODE_SHARE'] = pd.to_numeric(hm['MODE_SHARE'], errors='coerce')
    sel = hm[(hm.geography == 'lga')
             & (hm.area_name.str.strip() == lga)
             & (hm.FINANCIAL_YEAR.astype(str) == year)]
    out = {}
    for _, r in sel.iterrows():
        # the published labels carry significance asterisks on low-sample cells
        key = str(r['TRAVEL_MODE']).strip().rstrip('*').strip().lower()
        if pd.notna(r['MODE_SHARE']):
            out[key] = float(r['MODE_SHARE'])
    return year, lga, out


def region_trip_totals(year):
    """Weekday trips by LGA on the survey's own mode-share base.

    The point-to-point trips band counts the whole study area, so turning it
    into a share needs the study area's trip total - not the target LGA's.
    Walk-linked rows are excluded because the survey excludes them from
    MODE_SHARE, and mixing the two bases would inflate the denominator.
    """
    hm = pd.read_csv(os.path.join(HTS, 'hts_mode.csv'))
    hm['MODE_SHARE'] = pd.to_numeric(hm['MODE_SHARE'], errors='coerce')
    hm['TRIPS_BY_MODE'] = pd.to_numeric(hm['TRIPS_BY_MODE'], errors='coerce')
    sel = hm[(hm.geography == 'lga')
             & (hm.FINANCIAL_YEAR.astype(str) == year)
             & hm.MODE_SHARE.notna() & (hm.MODE_SHARE > 0)]
    return {str(k).strip(): float(v) for k, v
            in sel.groupby('area_name')['TRIPS_BY_MODE'].sum().items()}


def g62_composition(scope='target_lga'):
    """One-method JTW journeys by mode.

    `target_lga` (DECISIONS.md 9.122): the SA1s the boundary layer puts in
    the target LGA - the population whose HTS levels every other target rests
    on and whose modelled share the fit measures. `core` is the five-LGA core,
    which this split used until 9.122: motorbike was then generated for one
    geography and scored against another (0.408% of driver journeys on the
    core cell against 0.642% on the LGA's own), the 9.91/9.100 class.
    """
    d = pd.read_csv(os.path.join(CEN, 'census2021_G62_SA1.csv'))
    if scope == 'core':
        d = d[d.zone_tier == 'core']
    elif scope == 'target_lga':
        lga = pd.read_csv(os.path.join(ZON, 'sa1_to_lga.csv'), dtype=str)
        inside = set(lga.loc[lga.lga_name.str.strip() == _city.target_lga(),
                             'SA1_CODE21'])
        d = d[d.SA1_CODE_2021.astype(str).isin(inside)]
    else:
        raise SystemExit('unknown G62 scope %r' % scope)
    return {k: int(d[col].fillna(0).sum()) for k, col in G62.items()}


def _norm_stop(name):
    """A publication's station label reduced to what a schedule stop calls it."""
    t = re.sub(r'\s+', ' ', str(name)).strip().lower()
    for suffix in (r'\s+platform\s+\d+$', r'\s+station$', r'\s+light rail$'):
        t = re.sub(suffix, '', t)
    return t


def model_pt_stations():
    """Every rail/light-rail stop THIS CITY's own mapped schedule contains,
    with the LGA the boundary layer puts it in.

    The composition that splits the survey's PT level must be measured over the
    ground the survey measured, and neither half of that may be asserted: which
    stops exist is the city's schedule, and which LGA one sits in is the city's
    boundary. Nothing here names a place. A station the publication carries but
    the schedule does not is not this city's - the published Newcastle series
    carries a light rail stop belonging to another city entirely (9.100).
    """
    import geopandas as gpd
    from shapely.geometry import Point

    z = zipfile.ZipFile(_city.path('schedules/base2026.zip'))
    rd = lambda n: list(csv.DictReader(_io.TextIOWrapper(z.open(n), 'utf-8-sig')))
    routes = {r['route_id']: r for r in rd('routes.txt')}
    trip_route = {t['trip_id']: t['route_id'] for t in rd('trips.txt')}
    kind_of = {}
    for r in rd('stop_times.txt'):
        rt = trip_route.get(r['trip_id'])
        if rt is not None:
            kind_of[r['stop_id']] = routes[rt]['route_type']

    lga = gpd.read_file(os.path.join(ZON, 'zones_LGA.gpkg')).to_crs('EPSG:4326')
    out = {}
    for st in rd('stops.txt'):
        kind = kind_of.get(st['stop_id'])
        if kind not in ('0', '2'):
            continue
        key = (_norm_stop(st['stop_name']), kind)
        if key in out:
            continue
        hit = lga[lga.geometry.contains(
            Point(float(st['stop_lon']), float(st['stop_lat'])))]
        out[key] = None if hit.empty else str(hit.iloc[0]['LGA_NAME21'])
    return out


def _unbroken_months(series_by_month, ratio):
    """The months of one series that are NOT a structural break.

    A patronage series can stop meaning what it meant - an operator or contract
    change empties one region's rows while every other region in the same
    publication continues normally. Such a month is not a season and must not
    enter a composition. It is separated from a season by size: the seasonal
    trough in these series is ~20% below the median and the break is ~88%
    below, so any threshold in between finds the same answer.
    """
    if not series_by_month:
        return set()
    med = sorted(series_by_month.values())[len(series_by_month) // 2]
    return {m for m, v in series_by_month.items() if med <= 0 or v >= ratio * med}


def opal_pt_boardings(cfg):
    """Bus / heavy rail / light rail boardings over the common recent window.

    Three separate publications, so the window is the intersection of what all
    three cover rather than each source's own newest data - a split taken over
    mismatched periods would be an artefact of the calendar. Three further
    things the window and the totals must survive (9.100):

    * a station the publication carries that this city does not contain, or
      that sits outside the LGA the survey level describes, is EXCLUDED;
    * a month in which a series structurally breaks may not enter the window;
    * a line the current publication reports at ONE stop is scaled to the whole
      line by the measured share that stop takes, rather than being read as if
      the stop were the line.
    """
    months = int(cfg.get('CAL.pt_split.window_months'))
    scope = str(cfg.get('CAL.pt_split.station_scope'))
    ratio = float(cfg.get('CAL.pt_split.break_ratio'))
    lr_share = float(cfg.get('CAL.pt_split.lr_observed_stop_share'))
    target = _city.target_lga()
    known = model_pt_stations()

    bus = collections.Counter()
    for _, r in pd.read_csv(
            os.path.join(OBS, 'opal_bus_newcastle_hunter.csv')).iterrows():
        mon, yr = str(r['Year_Month']).split('-')
        bus['%s-%s' % (yr, MON[mon])] += float(r['Trip'] or 0)

    sta = collections.defaultdict(collections.Counter)
    excluded = collections.Counter()
    for _, r in pd.read_csv(
            os.path.join(OBS, 'station_entries_exits_newcastle.csv')).iterrows():
        if r['Entry_Exit'] != 'Entry':
            continue
        kind = '2' if r['Station_Type'] == 'Train' else '0'
        key = (_norm_stop(r['Station']), kind)
        if scope == 'target_lga':
            where = known.get(key, False)
            if where is False:
                excluded['%s (not in this city)' % str(r['Station']).strip()] += 1
                continue
            if where != target:
                excluded['%s (%s)' % (str(r['Station']).strip(),
                                      where or 'outside every LGA')] += 1
                continue
        sta[r['Station_Type']][str(r['MonthYear'])[:7]] += _trip_cell(r['Trip'])

    clean_bus = _unbroken_months(dict(bus), ratio)
    common = sorted((set(bus) & set(sta['Train']) & set(sta['Light rail']))
                    & clean_bus)
    # The window must be CONTIGUOUS and must not span a break. Pooling months
    # from either side of one measures the break: after a contract change the
    # series is a different series, and whether it has recovered its old
    # meaning is exactly what cannot be known from it. A run must also be long
    # enough to say something - half the declared window, so no new free value
    # is introduced - which disqualifies the two-month tail that follows this
    # city's bus break and selects the intact period before it (9.100).
    runs, run = [], []
    for m in common:
        ordinal = int(m[:4]) * 12 + int(m[5:7])
        if run and ordinal != run[-1][0] + 1:
            runs.append([x[1] for x in run])
            run = []
        run.append((ordinal, m))
    if run:
        runs.append([x[1] for x in run])
    usable = [r for r in runs if len(r) >= max(1, months // 2)]
    if not usable:
        raise SystemExit(
            'no contiguous stretch of at least %d month(s) is covered by all '
            'three PT publications and free of a structural break, so no '
            'composition can be measured. Resolve the sources rather than '
            'relaxing CAL.pt_split.break_ratio.' % max(1, months // 2))
    window = usable[-1][-months:]

    got = dict(bus=sum(bus[m] for m in window),
               rail=sum(sta['Train'][m] for m in window),
               light_rail=sum(sta['Light rail'][m] for m in window) / lr_share)
    return window, got, excluded, lr_share


def disclosed_pt_boardings(cfg):
    """Light rail line boardings and heavy rail station entries, per day.

    9.130: both are DISCLOSED counts - the line's own Opal series by month
    and card type, and the station entries publication - so the model is held
    to them directly, per weekday, counting every traveller who boards (the
    publications count everyone, resident or not). The window is the latest
    CAL.pt_split.window_months months each series carries; stations are those
    this city's own mapped schedule contains (model_pt_stations), so a station
    the publication carries and the model cannot board is excluded and named.

    Censoring (#129, 9.142): a station-month published as the text 'Less than
    50' counts as CAL.pt.censored_cell_value here, because this statistic is a
    SUM over stations and excluding the cell would drop that station's whole
    contribution to a day's boardings. The holdout station MEANS take the other
    rule and exclude it, which is recorded as their pre-registered treatment;
    the two agree on every scored target while this series carries no censored
    cell, so the count is returned and written into the target's basis rather
    than left to be assumed.
    Returns (light_rail_per_day, rail_per_day, rail_stations, windows,
    excluded, censored_cells_in_window).
    """
    months = int(cfg.get('CAL.pt_split.window_months'))
    lr = pd.read_csv(os.path.join(OBS, 'opal_lr_newcastle_by_month_cardtype.csv'))
    lr['m'] = pd.to_datetime(lr['Year_Month'], format='mixed').dt.to_period('M')
    by_m = lr.groupby('m')['Trip'].sum().sort_index()
    lr_months = list(by_m.index[-months:])
    lr_days = sum(m.days_in_month for m in lr_months)
    lr_per_day = float(by_m.loc[lr_months].sum()) / lr_days

    known = model_pt_stations()
    st = pd.read_csv(os.path.join(OBS, 'station_entries_exits_newcastle.csv'))
    st = st[(st['Station_Type'] == 'Train') & (st['Entry_Exit'] == 'Entry')].copy()
    st['censored'] = pd.to_numeric(st['Trip'], errors='coerce').isna() \
        & st['Trip'].notna()
    st['Trip'] = st['Trip'].map(_trip_cell)
    st['m'] = st['MonthYear'].astype(str).str[:7]
    st_months = sorted(st['m'].unique())[-months:]
    st = st[st['m'].isin(st_months)]
    n_censored = int(st['censored'].sum())
    st_days = sum(pd.Period(m).days_in_month for m in st_months)
    per_station = {}
    excluded = []
    for name, v in st.groupby(st['Station'].str.strip())['Trip'].sum().items():
        if known.get((_norm_stop(name), '2'), False) is False:
            excluded.append(name)
            continue
        per_station[name] = float(v) / st_days
    rail_per_day = sum(per_station.values())
    return (lr_per_day, rail_per_day, per_station,
            dict(light_rail=[str(lr_months[0]), str(lr_months[-1])],
                 heavy_rail=[st_months[0], st_months[-1]]),
            excluded, n_censored)


def main():
    cfg = _registry.load(strict=True)
    year, lga, lv = hts_levels(cfg)
    g = g62_composition()
    window, pt, pt_excluded, lr_share = opal_pt_boardings(cfg)

    rows = []

    def add(mode, target, denominator, status, basis, sweep=None):
        rows.append(dict(
            mode=mode,
            target_pct=None if target is None else round(target, 4),
            denominator=denominator,
            status=status,
            sweep_low=None if not sweep else round(sweep[0], 4),
            sweep_high=None if not sweep else round(sweep[1], 4),
            basis=basis))

    # ---- the person-trip modes -------------------------------------
    # Vehicle driver splits across the three one-method driver categories the
    # census distinguishes. The truck slice is NOT a model mode: this city
    # represents road freight as its own subpopulation of vehicles, not as a
    # resident's person trip, so it is written out as a named deduction rather
    # than folded silently into car.
    drv = g['car'] + g['motorbike'] + g['truck']
    vd = lv['vehicle driver']
    tol = float(cfg.get('CAL.mode_split.commute_transfer_tolerance'))

    # The two observations this split rests on are DECLARED, because the
    # motorbike carve in build_matsim_plans.py is derived from them and a
    # registry value that silently disagrees with the artefact is the
    # duplication failure 9.79 was written about. They are read from the
    # acquired sources here, as they always were - this only refuses to let
    # the two copies drift apart. 9.115.
    _decl_vd = float(cfg.get('CAL.mode_split.vehicle_driver_level'))
    _decl_mb = float(cfg.get('CAL.mode_split.motorbike_driver_journey_share'))
    # 9.125: the resident truck driver's cell, asserted like the motorbike's
    # - the plans builder carves residents locked to `truck` from it
    _decl_tk = float(cfg.get('CAL.mode_split.truck_driver_journey_share'))
    _obs_vd = vd / 100.0
    _obs_mb = g['motorbike'] / drv
    _obs_tk = g['truck'] / drv
    for name, declared, observed in (
            ('CAL.mode_split.vehicle_driver_level', _decl_vd, _obs_vd),
            ('CAL.mode_split.motorbike_driver_journey_share',
             _decl_mb, _obs_mb),
            ('CAL.mode_split.truck_driver_journey_share',
             _decl_tk, _obs_tk)):
        if abs(declared - observed) > 5e-5:
            raise SystemExit(
                'registry drift: %s declares %.7f but the acquired source '
                'measures %.7f. The declared value is what the motorbike '
                'carve derives from (9.115); update the field in the same '
                'change as the data, or the carve and its target stop '
                'describing one quantity.' % (name, declared, observed))

    car = vd * g['car'] / drv
    mbk = vd * g['motorbike'] / drv
    trk_resident = vd * g['truck'] / drv

    add('car', car, 'resident person trips',
        'derived',
        'HTS "%s" %.1f%% x census G62 one-method car-as-driver %d of %d '
        'driver journeys (%.3f%%)' % (year, vd, g['car'], drv,
                                      100.0 * g['car'] / drv),
        (car * (1 - tol), car * (1 + tol)))

    add('ride', lv['vehicle passenger'], 'resident person trips',
        'observed',
        'HTS "%s" Vehicle passenger, read directly - no disaggregation needed'
        % year)

    add('walk', lv['walk only'], 'resident person trips',
        'observed',
        'HTS "%s" Walk only, read directly. Walk linked is 0.0 by '
        'construction and is not a target' % year)

    # "Other" holds taxi/rideshare/carshare, wheelchair, bicycle and aircraft
    # by the data document's own list. Splitting it by the CENSUS was wrong and
    # is corrected here (9.91): the census counts JOURNEYS TO WORK, and taxi is
    # overwhelmingly NOT a commute mode - it carries nights out, airport runs,
    # medical trips and the carless - so a commute share understates it by
    # roughly five times. The city has a better source, already declared:
    # B.taxi.daily_trips_band, the IPART 2025 point-to-point incidence band for
    # the study area. Taxi therefore takes its level from that band, and BIKE
    # takes the residual - the two share one survey category, so one cannot
    # move without the other.
    oth = lv['other']
    band = cfg.get('B.taxi.daily_trips_band')
    conc = float(cfg.get('CAL.taxi.lga_concentration'))
    totals = region_trip_totals(year)
    region = sum(totals.values())
    lga_trips = totals[lga]
    lo_share = 100.0 * (band[0] / region) * conc
    hi_share = 100.0 * (band[1] / region) * conc
    taxi = 0.5 * (lo_share + hi_share)

    if taxi >= oth:
        raise SystemExit(
            'the point-to-point band implies a taxi share of %.4f%%, which '
            'is not smaller than the whole HTS "Other" category (%.4f%%). '
            'Bike would be negative. Either the band, the concentration or '
            'the survey category has changed meaning - resolve it rather '
            'than clamping.' % (taxi, oth))
    bike = oth - taxi

    add('taxi', taxi, 'resident person trips', 'derived',
        'B.taxi.daily_trips_band %d-%d point-to-point trips/day across the '
        'study area (IPART 2025 incidence x usage rate), against %d study-area '
        'weekday trips = %.4f%%-%.4f%% of trips, x CAL.taxi.lga_concentration '
        '%.2f. NOT the census share: the census counts journeys to WORK and '
        'taxi is overwhelmingly a non-commute mode, which understated it about '
        'fivefold (9.91). The target LGA carries %d of those weekday trips'
        % (band[0], band[1], region, lo_share, hi_share, conc, lga_trips),
        (lo_share, hi_share))

    add('bike', bike, 'resident person trips', 'derived',
        'HTS "%s" Other %.1f%% MINUS the point-to-point share above, because '
        'bicycle and taxi/rideshare sit in ONE survey category and cannot be '
        'set independently. The residual also carries wheelchair, carshare and '
        'aircraft, which this city does not model, so it is a slight OVER-'
        'statement of cycling rather than an under-statement. The census G62 '
        'bicycle count (%d of %d bicycle+taxi journeys) is not used for the '
        'level for the same reason it is not used for taxi - commuting is not '
        'a random sample of travel - but it agrees on the ordering: cycling is '
        'the larger of the two'
        % (year, oth, g['bike'], g['bike'] + g['taxi']),
        (oth - hi_share, oth - lo_share))

    add('motorbike', mbk, 'resident person trips', 'derived',
        'HTS "%s" Vehicle driver %.1f%% x census G62 motorbike/scooter %d of '
        '%d driver journeys (%.3f%%)'
        % (year, vd, g['motorbike'], drv, 100.0 * g['motorbike'] / drv),
        (mbk * (1 - tol), mbk * (1 + tol)))

    # Public transport splits on CURRENT boardings, not on the 2021 census:
    # the census was enumerated during a lockdown that suppressed PT commuting
    # specifically. The census composition is kept as the sweep's far end,
    # because the two disagree and the disagreement is real uncertainty.
    pt_level = lv['public transport']
    pt_tot = pt['bus'] + pt['rail'] + pt['light_rail']
    g_pt = g['bus'] + g['train'] + g['tram'] + g['ferry']

    # 9.130: heavy rail and light rail are held to their DISCLOSED boardings
    # below; only bus keeps the composition-derived trip share, because its
    # published series is a contract-region subset with a structural break.
    for mode, key, gkey in (('bus', 'bus', 'bus'),):
        obs_share = pt[key] / pt_tot
        cen_share = g[gkey] / g_pt
        v = pt_level * obs_share
        alt = pt_level * cen_share
        add(mode, v, 'resident person trips', 'derived',
            'HTS "%s" Public transport %.1f%% x Opal/station boardings '
            'share %.3f%% over %s..%s (%d of %d boardings). The window is '
            'the CONTIGUOUS run of months all three publications cover in '
            "which no series structurally breaks (9.100): this city's bus "
            'contract region falls 88%% in one month while every other '
            'region in the same publication continues normally, and the '
            'window used before 9.100 lay entirely inside that broken '
            "stretch. Stations are restricted to those this city's own "
            'mapped schedule contains inside the target LGA '
            '(CAL.pt_split.station_scope), which excluded %d of them - %s '
            '- because the HTS level being split is a share of TARGET-LGA '
            "residents' trips and the composition must be measured over "
            'the same ground. Light rail is reported by the current '
            "publication at ONE of the line's stops, so it is scaled to "
            'the line by the measured CAL.pt_split.lr_observed_stop_share '
            '%.4f. Census G62 commute composition gives %.3f%% instead '
            "and sets the sweep's far end"
            % (year, pt_level, 100.0 * obs_share, window[0], window[-1],
               pt[key], pt_tot, len(pt_excluded),
               '; '.join(sorted(pt_excluded)), lr_share, 100.0 * cen_share),
            (min(v, alt), max(v, alt)))

    # 9.130: the two public-transport modes whose patronage IS disclosed are
    # held to the disclosed count - every boarding, every traveller, per
    # weekday - rather than to an HTS trip share split by a boardings
    # composition. Measured before this change: the composition put light
    # rail at 0.644% of resident trips (some 14,500 trips a day) against a
    # published line total of 2,754 boardings a day, and heavy rail at 0.774%
    # (17,500) against 6,086 station entries a day - the survey level and
    # the operator counts differ by a factor the composition cannot see, and
    # a model reading -96% on the derived basis read -48% on the disclosed
    # one while heavy rail read +65% derived and roughly +400% disclosed.
    lr_day, rail_day, rail_stations, pt_windows, rail_excluded, rail_censored = \
        disclosed_pt_boardings(cfg)
    wf = float(cfg.get('CAL.pt.weekday_factor'))
    wf_lo, wf_hi = 1.0, 1.3
    add('heavy_rail', rail_day * wf,
        'boardings per weekday at the disclosed stations (all travellers)',
        'measured',
        'DISCLOSED: station entries (Train, Entry) summed over the %d '
        'stations this city\'s mapped schedule contains, %s..%s, %.0f a day '
        'over all days, x CAL.pt.weekday_factor %.4f. Every traveller who '
        'boards is counted, as the publication counts them; %d published '
        'station(s) the model cannot board are excluded%s. %s. The '
        'composition-derived trip share this replaces (HTS "%s" PT %.1f%% x '
        'the boardings split) was %.4f%% of resident trips'
        % (len(rail_stations), pt_windows['heavy_rail'][0],
           pt_windows['heavy_rail'][1], rail_day, wf, len(rail_excluded),
           (': ' + ', '.join(sorted(rail_excluded))) if rail_excluded else '',
           ('%d station-month(s) in this window are censored ("Less than 50") '
            'and count as CAL.pt.censored_cell_value %.0f trips, the rule '
            'declared for a SUM over stations (#129)'
            % (rail_censored, _censored())) if rail_censored else
           ('No station-month in this window is censored ("Less than 50"), so '
            'CAL.pt.censored_cell_value moves this target at neither end of '
            'its sweep; the holdout station means EXCLUDE a censored cell '
            'instead, their recorded pre-registered treatment (#129)'),
           year, pt_level, pt_level * pt['rail'] / pt_tot),
        (rail_day * wf_lo, rail_day * wf_hi))
    add('light_rail', lr_day * wf,
        'boardings per weekday on the line (all travellers)',
        'measured',
        'DISCLOSED: the line\'s own Opal series by month and card type, all '
        'card types, %s..%s, %.0f a day over all days, x '
        'CAL.pt.weekday_factor %.4f. The composition-derived trip share this '
        'replaces (HTS "%s" PT %.1f%% x the boardings split) was %.4f%% of '
        'resident trips'
        % (pt_windows['light_rail'][0], pt_windows['light_rail'][1], lr_day,
           wf, year, pt_level, pt_level * pt['light_rail'] / pt_tot),
        (lr_day * wf_lo, lr_day * wf_hi))
    json.dump(dict(decisions_ref='9.130', weekday_factor=wf,
                   light_rail=dict(per_day=round(lr_day, 2),
                                   per_weekday=round(lr_day * wf, 2),
                                   window=pt_windows['light_rail']),
                   heavy_rail=dict(per_day=round(rail_day, 2),
                                   per_weekday=round(rail_day * wf, 2),
                                   window=pt_windows['heavy_rail'],
                                   stations={k: round(v, 2) for k, v in
                                             sorted(rail_stations.items())},
                                   excluded=sorted(rail_excluded))),
              open(os.path.join(OUT, 'pt_boardings_targets.json'), 'w', newline='\n'),
              indent=2)

    # Ferry: no Newcastle ferry patronage is published in any acquired
    # artefact. The all-modes Opal series carries a Ferry row but it is
    # NSW-wide and Sydney-dominated, so it identifies nothing here. The only
    # city-specific ferry observation in existence in this package is the
    # census one-method count, and it is lockdown-vintage. Declared UNOBTAINED
    # and swept, per the standing rule for an input this project cannot
    # observe: it is not pinned to a point value.
    ferry_cen = pt_level * g['ferry'] / g_pt
    add('ferry', ferry_cen, 'resident person trips', 'derived',
        'DERIVED, not observed: no Newcastle ferry patronage is published in '
        'any acquired artefact - the Opal all-modes Ferry series is NSW-wide '
        'and Sydney-dominated, and the station entries/exits publication '
        'carries Train and Light rail only. The one city-specific ferry '
        'observation that exists is the census G62 one-method count, %d of %d '
        'PT journeys (%.3f%%), and it sets the ferry share WITHIN public '
        'transport, which the HTS PT level then scales. Two things make that '
        'transfer more defensible for this mode than for the others: the '
        'Stockton service is a CAPTIVE crossing (the road alternative is a '
        '~20 km detour via Hexham), so its riders are not choosing it on the '
        'margin the way a bus rider might; and a share WITHIN PT is far less '
        'sensitive to the August 2021 lockdown than an absolute level, because '
        'the lockdown suppressed the numerator and denominator together. The '
        'sweep is nonetheless wide - 0 to twice the point value - because the '
        'lockdown vintage is real and unquantified'
        % (g['ferry'], g_pt, 100.0 * g['ferry'] / g_pt),
        (0.0, 2.0 * ferry_cen))

    # ---- the modes on their own denominators -----------------------
    # Road freight is not a resident's person trip in this model, so it cannot
    # be scored on the person-trip denominator at all. Its observation is the
    # classified traffic count: heavy vehicles as a share of all vehicles at
    # the stations that classify them.
    av = pd.read_csv(os.path.join(OBS, 'traffic_aadt.csv'), low_memory=False)
    av = av[av.period == 'WEEKDAYS']
    # CALIBRATION STATIONS ONLY. This is a scored gate target, so it may not be
    # derived over the holdout half of the 67/143 split. The split rule is the
    # one build_validation_targets.py applies: a calibration station is a
    # PERMANENT station. report_mode_ridership.truck_at_count_stations already
    # scores truck against calibration stations only; deriving the target over
    # both halves scored the model against an observation it must not see.
    _stn = pd.read_csv(os.path.join(OBS, 'traffic_count_stations_newcastle.csv'),
                       low_memory=False)
    _perm = set(_stn.loc[_stn['permanent_station'].astype(str)
                         .isin(['1', 'True', 'true']), 'station_key'].astype(str))
    av = av[av['station_key'].astype(str).isin(_perm)]
    yrs = sorted(int(y) for y in av.year.dropna().unique())
    span = []
    for y in yrs:
        s = av[av.year == y]
        piv = s.groupby('classification_type')['traffic_count'].sum()
        if 'HEAVY VEHICLES' not in piv or 'ALL VEHICLES' not in piv:
            continue
        if piv['ALL VEHICLES'] <= 0:
            continue
        span.append((y, 100.0 * piv['HEAVY VEHICLES'] / piv['ALL VEHICLES']))
    recent = [v for y, v in span if y >= int(cfg.get('CAL.truck.count_year_from'))]
    add('truck', sum(recent) / len(recent) if recent else None,
        'weekday vehicles at classified count stations', 'derived',
        'TfNSW classified weekday counts at CALIBRATION (permanent) stations '
        'only, the holdout excluded: heavy vehicles as a share of all '
        'vehicles, mean of %s. NOT a person-trip share and NOT comparable '
        'with one - only a handful of stations classify, and they sit on '
        'freight routes, so this is the share where heavy vehicles are '
        'measured, not across the network'
        % ', '.join('%d %.2f%%' % (y, v) for y, v in span
                    if y >= int(cfg.get('CAL.truck.count_year_from'))),
        (min(recent), max(recent)) if recent else None)

    # Freight rail's ROAD EFFECT is simulated; the train itself is not a
    # vehicle in the mobsim, and that is the decision rather than a gap. The
    # coal chain has run on dedicated grade-separated track since 2006, so a
    # train in the mobsim would interact with nothing - except at the two
    # level crossings, which ARE simulated, as timed capacity closures on the
    # matched car links. The comparable quantity is therefore closures per
    # day, not train movements, and its observation does not exist: TfNSW and
    # ARTC do not publish crossing closure logs. So it is swept, exactly like
    # the other three inputs this project cannot observe.
    crep_path = _city.path('networks/matsim/crossings/_crossings_report.json')
    crep = json.load(open(crep_path, encoding='utf-8')) if os.path.exists(crep_path) else None
    if crep and crep.get('closure_source') == 'schedule_derived':
        per_site = crep['closures_per_site']
        total = sum(per_site.values())
        add('freight_train', float(total),
            'level-crossing closures per weekday', 'derived',
            'ROAD EFFECT SIMULATED, train not a mobsim vehicle. The coal chain '
            'has run on dedicated grade-separated track since 2006 (ARTC/PWCS/'
            'NCIG, ~110 movements/day), so the only real road interaction is '
            'the level crossings - and those are now DERIVED from the mapped '
            'rail timetable rather than assumed (9.90): one closure per '
            'scheduled train that crosses, at the time it crosses. %s, '
            '%d/weekday in total, each %.0f s. Non-timetabled freight is added '
            'on top at A.crossings.freight_closures_per_day, zero by default '
            'because the coal chain does not cross these roads at grade and '
            'ARTC publishes no movement log for what else might. A modelled '
            'count of train VEHICLES of zero is the decision, not a defect'
            % (', '.join('%s %d' % (k, v) for k, v in sorted(per_site.items())),
               total, float(cfg.get('A.crossings.closure_duration_s'))),
            None)
    else:
        per = float(cfg.get('A.crossings.closures_per_day'))
        sites_n = len(cfg.get('A.crossings.freight_road_names'))
        sweep = cfg.sweep('A.crossings.closures_per_day')
        lo, hi = (sweep['interval'] if isinstance(sweep, dict) else sweep)
        add('freight_train', None, 'level-crossing closures per weekday',
            'unobtained',
            'ROAD EFFECT SIMULATED under the assumed_uniform closure source: '
            '%d closures/day across %d sites, %.0f s each, spread evenly '
            'because no closure log is published. Swept %g-%g per site'
            % (per * sites_n, sites_n,
               float(cfg.get('A.crossings.closure_duration_s')), lo, hi),
            (lo * sites_n, hi * sites_n))

    os.makedirs(OUT, exist_ok=True)
    means = hts_trip_means()
    shared = collections.Counter(MEAN_CATEGORY.values())
    for row in rows:
        cat = MEAN_CATEGORY.get(row['mode'])
        row['target_mean_km'] = (None if cat is None
                                 else round(means.get(cat), 4)
                                 if means.get(cat) is not None else None)
        row['mean_km_basis'] = (
            '' if cat is None else
            'HTS "%s" %s TRIP_AVG_DISTANCE%s' % (
                year, cat,
                '' if shared[cat] == 1 else
                ', a FOLDED category shared by %d simulated modes - the survey '
                'publishes no finer mean, so this is the same observation for '
                'each of them and a deviation against it is not independent '
                'evidence about one mode' % shared[cat]))
    d = pd.DataFrame(rows)
    dst = os.path.join(OUT, 'mode_targets_by_mode.csv')
    d.to_csv(dst, index=False)

    rep = dict(
        hts_vintage=year, target_lga=lga,
        hts_levels=lv,
        g62_core_one_method=g,
        # 9.122: the key name predates the scope change; the cell is the
        # target LGA's since then, and this says so where the key cannot
        g62_one_method_scope='target_lga',
        pt_window=[window[0], window[-1]], pt_boardings=pt,
        n_modes=len(d),
        by_status=d['status'].value_counts().to_dict(),
        person_trip_target_sum=round(float(
            d[d.denominator == 'resident person trips']['target_pct']
            .fillna(0).sum()), 4))
    json.dump(rep, open(os.path.join(OUT, '_mode_targets_report.json'), 'w', newline='\n'),
              indent=2)

    print('wrote %s' % dst)
    print('%-14s %10s  %-34s %s' % ('mode', 'target %', 'denominator', 'status'))
    for _, r in d.iterrows():
        print('%-14s %10s  %-34s %s'
              % (r['mode'],
                 '-' if pd.isna(r['target_pct']) else '%.4f' % r['target_pct'],
                 r['denominator'], r['status']))
    print('\nperson-trip targets sum to %.4f%% (HTS categories sum to %.1f%%)'
          % (rep['person_trip_target_sum'], sum(lv.values())))


if __name__ == '__main__':
    main()
