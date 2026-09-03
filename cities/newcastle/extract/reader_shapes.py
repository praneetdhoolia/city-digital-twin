#!/usr/bin/env python
"""Newcastle's reader-shape adapter (issue #62 A5).

The framework's demand and measurement readers consume the declared shapes in
`config/schema/reader_shapes.json`; this module maps Newcastle's PUBLISHED
shapes - the NSW Household Travel Survey labels and the RMS/TfNSW classified
traffic-count vocabulary - to that schema AT READ TIME. Nothing is rewritten:
the processed artefacts keep their published column names and this module is
the only place the framework's readers meet them. The framework resolves it
through `city.readers()` (src/city.py, the only module that knows where a
city lives); a second city supplies its own copy speaking its own agency's
vocabulary.

All three families are adapted: the HTS mode-share aggregates, the
classified counts and, since 3 Sep 2026 (9.140), the census attributes. The
remaining HTS readers are declared but still source-shaped -
`config/schema/reader_shapes.json` lists exactly which.
"""
import city as _city

# --------------------------------------------------------------------------
# HTS mode-share aggregates
# --------------------------------------------------------------------------
HTS_MODE_FILE = 'data/processed/hts/hts_mode.csv'
# The NSW HTS financial-year label of the base-year survey, exactly as the
# published files and the derived validation targets spell it.
SURVEY_VINTAGE = '2024/25'
# The geography level of the published series the mode-share target uses.
SURVEY_GEOGRAPHY = 'lga'
# framework mode_category -> the label the NSW HTS prints for it. The survey
# decorates labels with significance asterisks ('Vehicle passenger*'); those
# are stripped before matching, so these are the clean spellings.
MODE_CATEGORY_LABELS = {
    'car_driver': 'Vehicle driver',
    'car_passenger': 'Vehicle passenger',
    'walk_only': 'Walk only',
    'walk_linked': 'Walk linked',
    'public_transport': 'Public transport',
    'other': 'Other',
}


def survey_vintage():
    """The base-year survey vintage, in the survey's own spelling."""
    return SURVEY_VINTAGE


def mode_category_labels():
    """framework mode_category -> this survey's printed label."""
    return dict(MODE_CATEGORY_LABELS)


def mode_share_table():
    """The base-year mode-share rows, one per (area_name, mode_category).

    A list of dicts with the declared columns: `area_name`, `mode_category`
    (a framework category, or 'unmapped:<label>' for a published category the
    framework does not consume - it still counts toward totals), `trips`
    (unlinked TRIPS_BY_MODE, summed) and `linked_share_pct` (the published
    linked MODE_SHARE, None where not published as a single row).
    """
    import pandas as pd
    h = pd.read_csv(_city.path(HTS_MODE_FILE))
    h = h[(h['FINANCIAL_YEAR'] == SURVEY_VINTAGE)
          & (h['geography'] == SURVEY_GEOGRAPHY)].copy()
    cleaned = (h['TRAVEL_MODE'].str.replace('*', '', regex=False)
               .str.strip().str.lower())
    label_to_cat = {v.lower(): k for k, v in MODE_CATEGORY_LABELS.items()}
    h['mode_category'] = [label_to_cat.get(m, 'unmapped:%s' % m)
                          for m in cleaned]
    out = []
    for (area, cat), grp in h.groupby(['area_name', 'mode_category'],
                                      sort=True):
        share = grp['MODE_SHARE'].dropna()
        out.append(dict(
            area_name=area,
            mode_category=cat,
            trips=float(grp['TRIPS_BY_MODE'].sum()),
            linked_share_pct=(float(share.iloc[0]) if len(share) == 1
                              else None)))
    return out


# --------------------------------------------------------------------------
# classified traffic counts
# --------------------------------------------------------------------------
COUNTS_FILE = 'data/processed/observed/traffic_aadt.csv'
# The RMS classification labels that mean TOTAL volume - a station publishes
# either a classified ALL VEHICLES total or an UNCLASSIFIED count, never both
# meanings under one label.
TOTAL_VOLUME_CLASSES = ('ALL VEHICLES', 'UNCLASSIFIED')
# RMS period label -> the framework's day-type period vocabulary. The other
# published periods (peaks, ALL DAYS, PUBLIC HOLIDAYS) are not consumed by
# the framework and are dropped here.
PERIOD_LABELS = {'WEEKDAYS': 'weekday', 'WEEKENDS': 'weekend'}


def total_volume_counts():
    """Total-vehicle-volume observations as a DataFrame with the declared
    columns: station_key, year, period ('weekday'/'weekend'), volume.

    One row per published observation (directions and total-classification
    variants stay separate rows, exactly as published) - the framework does
    its own aggregation, so the adapter adds none.
    """
    import pandas as pd
    t = pd.read_csv(_city.path(COUNTS_FILE), low_memory=False)
    t = t[t['classification_type'].isin(TOTAL_VOLUME_CLASSES)
          & t['period'].isin(PERIOD_LABELS)].copy()
    return pd.DataFrame(dict(
        station_key=t['station_key'],
        year=t['year'],
        period=t['period'].map(PERIOD_LABELS),
        volume=t['traffic_count']))


# --------------------------------------------------------------------------
# census attributes (issue #62 A5, the third family; DECISIONS.md 9.140)
# --------------------------------------------------------------------------
# Everything below is the ABS 2021 Census DataPack's own vocabulary - table
# names, column spellings, the sex-split table pairs and the bandings each
# table publishes. The framework reads only the shapes returned by the
# functions, never a column name.
CENSUS_DIR = 'data/processed/census'
CENSUS_ZONE_KEY = 'SA1_CODE_2021'
# G46 labour-force status by age and sex: the table's own bands
LF_BANDS = [('15_19', 15, 19), ('20_24', 20, 24), ('25_34', 25, 34),
            ('35_44', 35, 44), ('45_54', 45, 54), ('55_64', 55, 64),
            ('65_74', 65, 74), ('75_84', 75, 84), ('85ov', 85, 200)]
# G01 education attendance age groups, with the two column spellings the
# DataPack uses ('educ_inst' up to 14, 'edu_inst' from 15)
EDU_GROUPS = [('0_4', 0, 4, 'Age_psns_att_educ_inst_0_4_P', 'Age_0_4_yr_P'),
              ('5_14', 5, 14, 'Age_psns_att_educ_inst_5_14_P', 'Age_5_14_yr_P'),
              ('15_19', 15, 19, 'Age_psns_att_edu_inst_15_19_P', 'Age_15_19_yr_P'),
              ('20_24', 20, 24, 'Age_psns_att_edu_inst_20_24_P', 'Age_20_24_yr_P')]
EDU_25OV_ATT = 'Age_psns_att_edu_inst_25_ov_P'
EDU_25OV_POP = ['Age_25_34_yr_P', 'Age_35_44_yr_P', 'Age_45_54_yr_P',
                'Age_55_64_yr_P', 'Age_65_74_yr_P', 'Age_75_84_yr_P',
                'Age_85ov_P']
# G04 publishes single years to 79 and grouped columns for 80-99 and 100+
G04_GROUPED = [(80, 84, 'Age_yr_80_84_%s'), (85, 89, 'Age_yr_85_89_%s'),
               (90, 94, 'Age_yr_90_94_%s'), (95, 99, 'Age_yr_95_99_%s')]
G04_100_PLUS = 'Age_yr_100_yr_over_%s'
# G60 occupation (ANZSCO 1-digit) by age and sex
OCCUPATION_LABELS = ['Managers', 'Professionals', 'TechnicTrades_Wrs',
                     'CommunPersnlSvc_W', 'ClericalAdminis_W', 'Sales_W',
                     'Mach_oper_drivers', 'Labourers']
OCCUPATION_BANDS = ('15_19', '20_24', '25_34', '35_44', '45_54', '55_64',
                    '65_74', '75ov')
# G17 personal weekly income bands by age and sex
INCOME_BANDS = ['Neg_Nil', '1_149', '150_299', '300_399', '400_499', '500_649',
                '650_799', '800_999', '1000_1249', '1250_1499', '1500_1749',
                '1750_1999', '2000_2999', '3000_more']
INCOME_AGE_BANDS = ('15_19_yrs', '20_24_yrs', '25_34_yrs', '35_44_yrs',
                    '45_54_yrs', '55_64_yrs', '65_74_yrs', '75_84_yrs')
# G36 dwelling structure, G35 household size, G34 motor vehicles
DWELLING_TYPES = [('separate_house', 'OPDs_Separate_house_Dwellings'),
                  ('semi_terrace', 'OPDs_SD_r_t_h_th_Tot_Dwgs'),
                  ('flat_apartment', 'OPDs_F_ap_I_Tot_Dwgs'),
                  ('other', 'OPDs_Other_dwelling_Tot_Dwgs')]
HOUSEHOLD_SIZE_COLS = ['Num_Psns_UR_%s_Total' % s
                       for s in ('1', '2', '3', '4', '5', '6mo')]
VEHICLE_COLS = ['Num_MVs_per_dweling_%s' % s
                for s in ('0_MVs', '1_MVs', '2_MVs', '3_MVs', '4mo_MVs')]
# G15 tertiary attendance, full time / part time, the table's own bands
# standing for the framework's 18_24 / 25_ov
TERTIARY_BANDS = (('18_24', '15_24'), ('25_ov', '25_ov'))


def labour_force_bands():
    """[(band, lo, hi)] - the bands labour-force rates are published in."""
    return list(LF_BANDS)


def education_groups():
    """[(group, lo, hi)] - the age groups attendance is published in."""
    return [(n, lo, hi) for n, lo, hi, _, _ in EDU_GROUPS] + [('25_ov', 25, 200)]


def occupation_labels():
    return list(OCCUPATION_LABELS)


def income_band_labels():
    return list(INCOME_BANDS)


def dwelling_types():
    return [n for n, _ in DWELLING_TYPES]


def _read(name):
    import pandas as pd
    return pd.read_csv(_city.path(CENSUS_DIR + '/' + name), low_memory=False)


def _cell(row, col):
    import pandas as pd
    v = row.get(col, 0)
    try:
        return float(v) if pd.notna(v) else 0.0
    except (TypeError, ValueError):
        return 0.0


class _Residence:
    """The residence-side tables, loaded once and indexed by zone."""

    def __init__(self):
        key = CENSUS_ZONE_KEY
        g04 = _read('census2021_G04A_SA1.csv').merge(
            _read('census2021_G04B_SA1.csv'), on=[key, 'zone_tier'], suffixes=('', '_b'))
        g46 = _read('census2021_G46A_SA1.csv').merge(
            _read('census2021_G46B_SA1.csv'), on=[key, 'zone_tier'], suffixes=('', '_b'))
        g17 = _read('census2021_G17A_SA1.csv').merge(
            _read('census2021_G17B_SA1.csv'), on=[key, 'zone_tier'], suffixes=('', '_b'))
        g60 = _read('census2021_G60A_SA1.csv').merge(
            _read('census2021_G60B_SA1.csv'), on=[key, 'zone_tier'], suffixes=('', '_b'))
        tables = dict(g01=_read('census2021_G01_SA1.csv'), g04=g04,
                      g34=_read('census2021_G34_SA1.csv'),
                      g35=_read('census2021_G35_SA1.csv'),
                      g36=_read('census2021_G36_SA1.csv'), g46=g46, g17=g17, g60=g60)
        for d in tables.values():
            d[key] = d[key].astype(str)
        self.tables = tables
        self.idx = {k: d.set_index(key) for k, d in tables.items()}

    def row(self, table, zone):
        import pandas as pd
        r = self.idx[table].loc[zone]
        if isinstance(r, pd.DataFrame):
            r = r.iloc[0]
        return r


_RESIDENCE = []


def _residence():
    if not _RESIDENCE:
        _RESIDENCE.append(_Residence())
    return _RESIDENCE[0]


def _num(v):
    import pandas as pd
    return float(v) if v is not None and pd.notna(v) else None


def residence_marginals(zone):
    """The per-zone marginals the population synthesiser draws from, in the
    framework's shape, or None where the zone is absent from any table.

    Counts are returned as published (a None where the table has no such
    column or no value); every rate is the framework's to form.
    """
    import pandas as pd
    res = _residence()
    try:
        r = {t: res.row(t, zone) for t in ('g01', 'g04', 'g34', 'g35', 'g36',
                                            'g46', 'g17', 'g60')}
    except KeyError:
        return None
    r04 = r['g04']
    single = [(a, _num(r04.get('Age_yr_%d_M' % a)), _num(r04.get('Age_yr_%d_F' % a)))
              for a in range(0, 80)]
    grouped = [(lo, hi, _num(r04.get(pat % 'M')), _num(r04.get(pat % 'F')))
               for lo, hi, pat in G04_GROUPED]
    over = (100, _num(r04.get(G04_100_PLUS % 'M')), _num(r04.get(G04_100_PLUS % 'F')))
    lf = {}
    r46 = r['g46']
    for sex in ('M', 'F'):
        for band, _, _ in LF_BANDS:
            lf[(sex, band)] = (_cell(r46, '%s_Tot_Emp_%s' % (sex, band)),
                               _cell(r46, '%s_Tot_LF_%s' % (sex, band)),
                               _cell(r46, '%s_Not_in_LF_%s' % (sex, band)),
                               _cell(r46, '%s_Emp_FullT_%s' % (sex, band)),
                               _cell(r46, '%s_Emp_PartT_%s' % (sex, band)),
                               _cell(r46, '%s_Tot_Unemp_%s' % (sex, band)))
    edu = {}
    for name, _, _, att_col, pop_col in EDU_GROUPS:
        edu[name] = (_cell(r['g01'], att_col), _cell(r['g01'], pop_col))
    edu['25_ov'] = (_cell(r['g01'], EDU_25OV_ATT),
                    sum(_cell(r['g01'], c) for c in EDU_25OV_POP))
    occ = []
    r60 = r['g60']
    for o in OCCUPATION_LABELS:
        v = 0.0
        for pre in ('M', 'F'):
            for band in OCCUPATION_BANDS:
                c = '%s%s_%s' % (pre, band, o)
                if c in r60.index and pd.notna(r60[c]):
                    v += float(r60[c])
        occ.append(v)
    inc = []
    r17 = r['g17']
    for b in INCOME_BANDS:
        v = 0.0
        for pre in ('M', 'F'):
            for band in INCOME_AGE_BANDS:
                c = '%s_%s_income_%s' % (pre, b, band) if b == 'Neg_Nil' else \
                    '%s_%s_%s' % (pre, b, band)
                if c in r17.index and pd.notna(r17[c]):
                    v += float(r17[c])
        inc.append(v)
    return dict(
        age_single_year=single, age_grouped=grouped, age_over=over,
        household_size=[r['g35'].get(c, 0) for c in HOUSEHOLD_SIZE_COLS],
        vehicles=[r['g34'].get(c, 0) for c in VEHICLE_COLS],
        dwellings=[r['g36'].get(c, 0) for _, c in DWELLING_TYPES],
        labour_force=lf, education=edu, occupation=occ, income=inc)


def region_labour_force_totals():
    """{(sex, band): (employed, in_labour_force, not_in_labour_force,
    full_time, part_time, unemployed)} summed over the core zones - the
    fallback for a zone whose own cell holds nobody of that sex and band."""
    g46 = _residence().tables['g46']
    sums = g46[g46.zone_tier == 'core'].sum(numeric_only=True)
    out = {}
    for sex in ('M', 'F'):
        for band, _, _ in LF_BANDS:
            out[(sex, band)] = (_cell(sums, '%s_Tot_Emp_%s' % (sex, band)),
                                _cell(sums, '%s_Tot_LF_%s' % (sex, band)),
                                _cell(sums, '%s_Not_in_LF_%s' % (sex, band)),
                                _cell(sums, '%s_Emp_FullT_%s' % (sex, band)),
                                _cell(sums, '%s_Emp_PartT_%s' % (sex, band)),
                                _cell(sums, '%s_Tot_Unemp_%s' % (sex, band)))
    return out


def region_education_totals():
    """{group: (attendees, persons)} summed over the core zones."""
    g01 = _residence().tables['g01']
    sums = g01[g01.zone_tier == 'core'].sum(numeric_only=True)
    out = {}
    for name, _, _, att_col, pop_col in EDU_GROUPS:
        out[name] = (_cell(sums, att_col), _cell(sums, pop_col))
    out['25_ov'] = (_cell(sums, EDU_25OV_ATT),
                    sum(_cell(sums, c) for c in EDU_25OV_POP))
    return out


def tertiary_full_time_shares():
    """(zone -> {band: full-time share of tertiary attendees}, {band: the
    share over every zone}) from G15, Voc and Uni attendees combined and the
    not-stated column excluded (DECISIONS.md 9.61)."""
    g15 = _read('census2021_G15_SA1.csv')
    key = [c for c in g15.columns if c.upper().startswith('SA1_CODE')][0]
    out, agg = {}, {}
    for band, tag in TERTIARY_BANDS:
        ft = (g15['Tert_Voc_edu_Ft_%s_P' % tag]
              + g15['Tert_Uni_oth_h_edu_Ft_%s_P' % tag]).to_numpy(dtype=float)
        pt = (g15['Tert_Voc_edu_Pt_%s_P' % tag]
              + g15['Tert_Uni_oth_h_edu_Pt_%s_P' % tag]).to_numpy(dtype=float)
        tot = ft + pt
        agg[band] = float(ft.sum() / tot.sum())
        for code, f, t in zip(g15[key].astype(str), ft, tot):
            if t > 0:
                out.setdefault(code, {})[band] = float(f / t)
    return out, agg


def residence_counts():
    """Population and dwellings per zone as a DataFrame with the declared
    columns zone_id, population, dwellings_total, dwellings_occupied."""
    g01 = _read('census2021_G01_SA1.csv')
    kc = [c for c in g01.columns if c.upper().startswith('SA1_CODE')][0]
    g01[kc] = g01[kc].astype(str)
    pcol = 'Tot_P_P' if 'Tot_P_P' in g01.columns else \
        [c for c in g01.columns if c.endswith('_P')][0]
    d = g01[[kc, pcol]].rename(columns={kc: 'zone_id', pcol: 'population'})
    g36 = _read('census2021_G36_SA1.csv')
    k36 = [c for c in g36.columns if c.upper().startswith('SA1_CODE')][0]
    g36[k36] = g36[k36].astype(str)
    dw = 'Total_PDs_Dwellings' if 'Total_PDs_Dwellings' in g36.columns else None
    occ = [c for c in g36.columns if 'Occup_priv_dwgs' in c and c.endswith('Total')]
    cols = [k36] + ([dw] if dw else []) + occ[:1]
    ren = {k36: 'zone_id'}
    if dw:
        ren[dw] = 'dwellings_total'
    if occ:
        ren[occ[0]] = 'dwellings_occupied'
    return d.merge(g36[cols].rename(columns=ren), on='zone_id', how='left')


def workplace_jobs():
    """(jobs, industry, n_industry_columns): jobs is a DataFrame
    [workplace_zone, jobs] at the place-of-work geography; industry is a
    DataFrame indexed by workplace_zone with one column per published
    industry division total, in the division vocabulary the census publishes
    (None where the tables are absent)."""
    import pandas as pd
    w09b = _read('census2021_W09B_POW_SA2.csv')
    kw = [c for c in w09b.columns if 'SA2_CODE' in c.upper()
          or c.upper().startswith('POW')][0]
    w09b[kw] = w09b[kw].astype(str).str.replace('POW', '', regex=False)
    jobs = w09b[[kw, 'Tot_P']].rename(columns={kw: 'workplace_zone', 'Tot_P': 'jobs'})
    jobs['workplace_zone'] = jobs['workplace_zone'].astype(str)
    jobs['jobs'] = pd.to_numeric(jobs['jobs'], errors='coerce').fillna(0)
    ind = []
    n_cols = 0
    for part in ['W09A', 'W09B']:
        w = _read('census2021_%s_POW_SA2.csv' % part)
        k = [c for c in w.columns if 'SA2_CODE' in c.upper()
             or c.upper().startswith('POW')][0]
        w[k] = w[k].astype(str).str.replace('POW', '', regex=False)
        tot_p = [c for c in w.columns if c.endswith('_Tot_P')]
        if tot_p:
            n_cols = len(tot_p)
            ind.append(w[[k] + tot_p].rename(columns={k: 'workplace_zone'})
                       .set_index('workplace_zone'))
    industry = pd.concat(ind, axis=1) if ind else None
    return jobs, industry, n_cols


def work_attendance_counts():
    """Employed persons on census day: total, worked from home, did not go
    to work (G62)."""
    g = _read('census2021_G62_SA1.csv')
    return dict(total=float(g['Tot_P'].sum()),
                worked_home=float(g['Worked_home_P'].sum()),
                did_not_go=float(g['Did_not_go_to_work_P'].sum()))
