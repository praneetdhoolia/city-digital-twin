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
import json
import collections
import pandas as pd

import registry as _registry  # noqa: E402

OBS = _city.path('data/processed/observed')
HTS = _city.path('data/processed/hts')
CEN = _city.path('data/processed/census')
OUT = _city.path('data/processed/validation')

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


def g62_composition():
    """One-method JTW journeys by mode, this city's core SA1s only."""
    d = pd.read_csv(os.path.join(CEN, 'census2021_G62_SA1.csv'))
    d = d[d.zone_tier == 'core']
    return {k: int(d[col].fillna(0).sum()) for k, col in G62.items()}


def opal_pt_boardings(cfg):
    """Bus / heavy rail / light rail boardings over the common recent window.

    Three separate TfNSW publications, so the window is the intersection of
    what all three cover rather than each source's own newest data - a split
    taken over mismatched periods would be an artefact of the calendar.
    """
    months = int(cfg.get('CAL.pt_split.window_months'))

    bus = collections.Counter()
    for _, r in pd.read_csv(
            os.path.join(OBS, 'opal_bus_newcastle_hunter.csv')).iterrows():
        mon, yr = str(r['Year_Month']).split('-')
        bus['%s-%s' % (yr, MON[mon])] += float(r['Trip'] or 0)

    sta = collections.defaultdict(collections.Counter)
    for _, r in pd.read_csv(
            os.path.join(OBS, 'station_entries_exits_newcastle.csv')).iterrows():
        if r['Entry_Exit'] != 'Entry':
            continue
        sta[r['Station_Type']][str(r['MonthYear'])[:7]] += float(r['Trip'] or 0)

    common = sorted(set(bus) & set(sta['Train']) & set(sta['Light rail']))
    window = common[-months:]
    got = dict(bus=sum(bus[m] for m in window),
               rail=sum(sta['Train'][m] for m in window),
               light_rail=sum(sta['Light rail'][m] for m in window))
    return window, got


def main():
    cfg = _registry.load(strict=True)
    year, lga, lv = hts_levels(cfg)
    g = g62_composition()
    window, pt = opal_pt_boardings(cfg)

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

    for mode, key, gkey in (('bus', 'bus', 'bus'),
                            ('heavy_rail', 'rail', 'train'),
                            ('light_rail', 'light_rail', 'tram')):
        obs_share = pt[key] / pt_tot
        cen_share = g[gkey] / g_pt
        v = pt_level * obs_share
        alt = pt_level * cen_share
        add(mode, v, 'resident person trips', 'derived',
            'HTS "%s" Public transport %.1f%% x Opal/station boardings share '
            '%.3f%% over %s..%s (%d of %d boardings). Census G62 commute '
            'composition gives %.3f%% instead and sets the sweep\'s far end'
            % (year, pt_level, 100.0 * obs_share, window[0], window[-1],
               pt[key], pt_tot, 100.0 * cen_share),
            (min(v, alt), max(v, alt)))

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
        'TfNSW classified weekday counts: heavy vehicles as a share of all '
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
    d = pd.DataFrame(rows)
    dst = os.path.join(OUT, 'mode_targets_by_mode.csv')
    d.to_csv(dst, index=False)

    rep = dict(
        hts_vintage=year, target_lga=lga,
        hts_levels=lv,
        g62_core_one_method=g,
        pt_window=[window[0], window[-1]], pt_boardings=pt,
        n_modes=len(d),
        by_status=d['status'].value_counts().to_dict(),
        person_trip_target_sum=round(float(
            d[d.denominator == 'resident person trips']['target_pct']
            .fillna(0).sum()), 4))
    json.dump(rep, open(os.path.join(OUT, '_mode_targets_report.json'), 'w'),
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
