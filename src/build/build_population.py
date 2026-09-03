#!/usr/bin/env python
"""Layer B1 - synthetic population (households and persons).

Method
------
Households are drawn per SA1 to match the census marginals for household size
(G35), motor vehicles (G34) and dwelling structure (G36). Persons are then drawn
to match the SA1 age-sex distribution (G04, including the grouped 80-99
columns), the age- and sex-conditional labour force status (G46, per SA1 with a
core-region fallback for empty cells), and the age-conditional education
attendance (G01). Licence holding, income band and occupation follow.

Daily activity chains are **not** built here. They were until P3, as layer B2 in
this same pass; `src/build/build_activity_chains.py` now owns them, builds them
as home-anchored tours rather than a shuffled activity list, and produces one
file per day type. See DECISIONS.md 9.

Everything is seeded. Re-running with the same seed reproduces the population
exactly; the seed is recorded in the scenario configuration (schema E1).
"""

# City-relative paths resolve through src/city.py: `data/...` names a
# location inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', 'src'))
import city as _city  # noqa: E402
import os
import csv
import json
import math
import argparse
import numpy as np
import pandas as pd

# Model inputs come from cities/<city>/registry/, not from literals here. Every
# value below carries its units, provenance and either a sweep, a held-fixed rule
# or a derived-from identity there. See DECISIONS.md 15.
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import registry as _registry  # noqa: E402
CFG = _registry.load()

LU = _city.path('data/processed/landuse')
OUT = _city.path('demand')
os.makedirs(os.path.join(OUT, 'population'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'plans'), exist_ok=True)
# The census is read through the city's reader adapter (issue #62 A5,
# DECISIONS.md 9.140): this synthesiser consumes the shapes declared in
# config/schema/reader_shapes.json and never a published column name.
READERS = _city.readers()

AGE_BANDS = CFG.get('B.population.age_bands')
BAND_LABEL = ['0-4', '5-11', '12-17', '18-24', '25-34', '35-44',
              '45-54', '55-64', '65-74', '75-84', '85+']
# Driver-licence holding rate by age band: the pooled measured vector
# (B.population.licence_rate_by_age_band, DECISIONS.md 9.131), and the
# per-LGA table it was pooled from, which the draw prefers - the rate is
# observed per LGA (Newcastle's 18-24 hold at 0.68, Port Stephens' at 0.84)
# and a pooled number would put the same licence in every suburb.
LICENCE_RATE = CFG.get('B.population.licence_rate_by_age_band')
LICENCE_RATE_BY_LGA = {}   # (lga, band index) -> rate
_LICENCE_TABLE = _city.path('data/processed/observed/licence_rates_by_age_lga.csv')
_SA1_LGA_TABLE = _city.path('data/processed/zones/sa1_to_lga.csv')
SA1_LGA = {}
if os.path.exists(_LICENCE_TABLE) and os.path.exists(_SA1_LGA_TABLE):
    import csv as _csv
    with open(_SA1_LGA_TABLE, encoding='utf-8') as _fh:
        for _z in _csv.DictReader(_fh):
            SA1_LGA[_z['SA1_CODE21']] = _z['lga_name']
    with open(_LICENCE_TABLE, encoding='utf-8') as _fh:
        for _r in _csv.DictReader(_fh):
            if _r['lga'] == 'ALL':
                continue
            _lo, _hi = (int(x) for x in _r['band'].split('-'))
            for _bi, _b in enumerate(CFG.get('B.population.age_bands')):
                if int(_b[0]) == _lo and int(_b[1]) == _hi:
                    LICENCE_RATE_BY_LGA[(_r['lga'], _bi)] = float(_r['rate'])


def licence_rate(sa1, b):
    """The licence holding rate for a person of age band b living in sa1:
    the LGA's measured rate, else the pooled vector (9.131)."""
    lga = SA1_LGA.get(str(sa1))
    if lga is not None:
        v = LICENCE_RATE_BY_LGA.get((lga, b))
        if v is not None:
            return v
    return LICENCE_RATE[b]
# Of 18+ education attendees (observed), the share studying full time - the
# ones who draw a mandatory HE tour. MEASURED per zone from the census
# tertiary attendance table through the reader adapter (DECISIONS.md 9.61,
# 9.140): full-time / (full-time + part-time) tertiary attendees, the
# table's own bands standing for 18_24 / 25_ov; a zone with an empty cell
# falls back to the share over every zone. Replaced the assumed
# B.population.tertiary_ft_share.
# The occupation and income vocabularies are the city's published ones,
# carried into B1 as labels (build_matsim_plans reads the income band's
# interval off the label).
OCCUPATIONS = READERS.occupation_labels()
INCOME_BANDS = READERS.income_band_labels()


def norm(a):
    a = np.asarray(a, dtype=float)
    a = np.where(np.isfinite(a) & (a > 0), a, 0.0)
    s = a.sum()
    return a / s if s > 0 else np.full(len(a), 1.0 / len(a))


TERTIARY_FT_SA1, TERTIARY_FT_CORE = READERS.tertiary_full_time_shares()

# The bandings the census PUBLISHES labour force and education attendance
# in, read from the adapter - the tables' banding, not a modelling choice;
# the model's own banding stays B.population.age_bands.
LF_BANDS = READERS.labour_force_bands()
EDU_GROUPS = READERS.education_groups()


def abs_lf_band(age):
    for name, lo, hi in LF_BANDS:
        if lo <= age <= hi:
            return name
    return None


def lf_rates_from(cells):
    """(employment, FT-of-employed, unemployed-of-non-employed) for one
    (sex, band) cell of counts - (employed, in labour force, not in labour
    force, full time, part time, unemployed) - or None where the cell holds
    nobody to measure.

    The employment base is persons with a STATED labour force status
    (in + not in the labour force); the census not-stated residual is
    excluded from the denominator rather than counted as not-working.
    """
    emp, lf, nilf, ft, pt, unemp = cells
    stated = lf + nilf
    if stated <= 0:
        return None
    non_emp = unemp + nilf
    return (min(emp / stated, 1.0),
            (ft / (ft + pt)) if (ft + pt) > 0 else None,
            (unemp / non_emp) if non_emp > 0 else 0.0)


def region_lf_rates():
    """Core-region (sex, band) labour-force rates - the fallback for the 7.4%
    of SA1 cells that hold nobody of that sex and band."""
    totals = READERS.region_labour_force_totals()
    out = {}
    for sex in ('M', 'F'):
        for band, _, _ in LF_BANDS:
            r = lf_rates_from(totals[(sex, band)])
            if r is None:
                r = (0.0, 0.0, 0.0)
            ft = r[1] if r[1] is not None else 0.0
            out[(sex, band)] = (r[0], ft, r[2])
    return out


def region_edu_rates():
    """Core-region attendance rate per published age group - the SA1
    fallback."""
    out = {}
    for name, (att, pop) in READERS.region_education_totals().items():
        out[name] = min(att / pop, 1.0) if pop > 0 else 0.0
    return out


def sa1_lf_rates(cells_by_sex_band, fallback):
    """(sex, band) -> rates for one SA1, falling back to the region where the
    SA1's own cell holds nobody of that sex and band."""
    out = {}
    for sex in ('M', 'F'):
        for band, _, _ in LF_BANDS:
            r = lf_rates_from(cells_by_sex_band[(sex, band)])
            if r is None:
                out[(sex, band)] = fallback[(sex, band)]
            else:
                ft = r[1] if r[1] is not None else fallback[(sex, band)][1]
                out[(sex, band)] = (r[0], ft, r[2])
    return out


def sa1_edu_rates(att_pop_by_group, fallback):
    """published age group -> attendance rate for one SA1, region fallback."""
    out = {}
    for name, (att, pop) in att_pop_by_group.items():
        out[name] = min(att / pop, 1.0) if pop > 0 else fallback[name]
    return out


def edu_group_of(age):
    for name, lo, hi in EDU_GROUPS:
        if lo <= age <= hi:
            return name
    return EDU_GROUPS[-1][0]


def age_sex_dist(m):
    """Collapse the published age counts into the model's age bands, by sex.

    Single years as far as the table publishes them, the grouped columns
    above that apportioned to bands by year overlap (uniform within a
    group), and the open top group to whichever band reaches it. (The
    grouped 80-99 columns were once skipped: the built population held 186
    persons 85+ against a census 15,151 - age-structure dossier, D1.)
    """
    single = {a: (mm, ff) for a, mm, ff in m['age_single_year']}
    out = np.zeros((len(AGE_BANDS), 2))
    for bi, (lo, hi) in enumerate(AGE_BANDS):
        for a in range(lo, hi + 1):
            if a in single:
                for si, v in enumerate(single[a]):
                    if v is not None:
                        out[bi, si] += v
        for glo, ghi, mm, ff in m['age_grouped']:
            overlap = max(0, min(hi, ghi) - max(lo, glo) + 1)
            if overlap <= 0:
                continue
            frac = overlap / float(ghi - glo + 1)
            for si, v in enumerate((mm, ff)):
                if v is not None:
                    out[bi, si] += frac * v
        olo, mm, ff = m['age_over']
        if hi >= olo:
            for si, v in enumerate((mm, ff)):
                if v is not None:
                    out[bi, si] += v
    return out


def main(seed=None, sample=None, max_sa1=None, out_dir=None):
    # Resolved, not defaulted. The seed is this project's headline determinism
    # claim and it existed in nine copies; the build sample is ONE, always, and
    # is a different quantity from the run-time RUN.sample.fraction.
    seed = CFG.get('B.seed.master') if seed is None else seed
    sample = CFG.get('B.population.build_sample_share') if sample is None else sample
    rng = np.random.default_rng(seed)
    out_dir = out_dir or OUT
    os.makedirs(os.path.join(out_dir, 'population'), exist_ok=True)
    zones = pd.read_csv(os.path.join(LU, 'D1_zone_attractions_SA1.csv'),
                        dtype={'SA1_CODE21': str})
    core = zones[zones.zone_tier == 'core'].reset_index(drop=True)
    if max_sa1:
        core = core.head(max_sa1)
    # core-region fallbacks for SA1 cells that hold nobody of a sex and band
    region_lf = region_lf_rates()
    region_edu = region_edu_rates()

    hh_f = open(os.path.join(out_dir, 'population', 'B1_households.csv'), 'w', newline='', encoding='utf-8')
    pp_f = open(os.path.join(out_dir, 'population', 'B1_synthetic_population.csv'), 'w', newline='', encoding='utf-8')
    hw = csv.writer(hh_f)
    pw = csv.writer(pp_f)
    hw.writerow(['household_id', 'home_sa1', 'home_x_mga56', 'home_y_mga56', 'home_lon', 'home_lat',
                 'household_size', 'household_vehicles', 'dwelling_type', 'weight'])
    pw.writerow(['person_id', 'household_id', 'home_sa1', 'age_band', 'age', 'sex',
                 'employment_status', 'occupation_anzsco1', 'income_band', 'licence_holder',
                 'household_vehicles', 'household_size', 'dwelling_type', 'student_status',
                 'mobility_impairment_flag', 'car_available', 'weight'])

    hid = 0
    pid = 0
    stats = dict(households=0, persons=0, employed=0, students=0, zero_car_hh=0)
    # ABS-band accumulators so the report states the realised age-conditional
    # rates beside the census they were drawn from: [persons, employed, FT students]
    bands = {}

    dw_names = READERS.dwelling_types()

    for _, z in core.iterrows():
        sa1 = z['SA1_CODE21']
        pop = int(z['population'])
        if pop <= 0:
            continue
        pop = int(round(pop * sample))
        if pop <= 0:
            continue
        m = READERS.residence_marginals(sa1)
        if m is None:
            continue

        asd = age_sex_dist(m)
        if asd.sum() <= 0:
            continue
        p_age = norm(asd.sum(axis=1))
        p_sex_given_age = np.array([norm(asd[b])[0] if asd[b].sum() > 0 else 0.5
                                    for b in range(len(AGE_BANDS))])

        # household size distribution (1..6+)
        hs = norm(m['household_size'])
        hs_vals = np.array([1, 2, 3, 4, 5, 6.6])
        # vehicles per dwelling (0..4+)
        veh = norm(m['vehicles'])
        veh_vals = np.array([0, 1, 2, 3, 4])
        # dwelling structure
        dw = norm(m['dwellings'])

        # labour force status per (sex, published age band) from this SA1's
        # own cells, and education attendance per age group - the
        # region-wide rates fill the cells that hold nobody
        lf = sa1_lf_rates(m['labour_force'], region_lf)
        edu = sa1_edu_rates(m['education'], region_edu)
        # occupation distribution (persons 15+, all ages summed)
        p_occ = norm(m['occupation'])
        # income distribution (persons 15+)
        inc_tot = m['income']
        p_inc = norm(inc_tot) if sum(inc_tot) > 0 else norm(np.ones(len(INCOME_BANDS)))

        # jitter radius from zone area so homes are not all stacked on the centroid
        rad = math.sqrt(max(float(z['area_km2']), 1e-4) * 1e6 / math.pi) * 0.6

        made = 0
        while made < pop:
            hid += 1
            bsz = int(rng.choice(len(hs_vals), p=hs))
            # the top category is "6 or more"; give it a small tail
            size = 6 + int(rng.geometric(0.55)) - 1 if bsz == 5 else int(hs_vals[bsz])
            size = max(1, min(size, 10))
            if made + size > pop + 2:
                size = max(1, pop - made)
            nv = int(rng.choice(veh_vals, p=veh))
            dt = dw_names[int(rng.choice(len(dw_names), p=dw))]
            ang = rng.uniform(0, 2 * math.pi)
            rr = rad * math.sqrt(rng.uniform(0, 1))
            hx, hy = float(z['x_mga56']) + rr * math.cos(ang), float(z['y_mga56']) + rr * math.sin(ang)
            hw.writerow([hid, sa1, round(hx, 1), round(hy, 1), z['lon'], z['lat'],
                         size, nv, dt, round(1.0 / sample, 4)])
            stats['households'] += 1
            if nv == 0:
                stats['zero_car_hh'] += 1

            members = []
            for k in range(size):
                pid += 1
                if k == 0:
                    # the household reference person is an adult
                    b = int(rng.choice(len(AGE_BANDS),
                                       p=norm(np.concatenate([np.zeros(3), p_age[3:]]))))
                else:
                    b = int(rng.choice(len(AGE_BANDS), p=p_age))
                lo, hi = AGE_BANDS[b]
                age = int(rng.integers(lo, min(hi, 95) + 1))
                sex = 'M' if rng.random() < p_sex_given_age[b] else 'F'
                if age < 15:
                    est = 'not_in_labour_force'
                else:
                    er, fts, us = lf[(sex, abs_lf_band(age))]
                    if rng.random() < er:
                        est = ('employed_full_time' if rng.random() < fts
                               else 'employed_part_time')
                    else:
                        est = ('unemployed' if rng.random() < us
                               else 'not_in_labour_force')
                employed = est.startswith('employed')
                occ = OCCUPATIONS[int(rng.choice(len(OCCUPATIONS), p=p_occ))] if employed else ''
                ib = INCOME_BANDS[int(rng.choice(len(INCOME_BANDS), p=p_inc))] if age >= 15 else 'Neg_Nil'
                # 9.131: drawn at the LGA's measured rate; 16 is the
                # provisional minimum and the 12-17 band's rate is the
                # 16-17-year-olds' holding spread over the band
                lic = int(age >= 16 and rng.random() < licence_rate(sa1, b))
                # attendance is observed (G01); how an 18+ attendee splits
                # full/part-time is not held and is declared and swept
                if rng.random() < edu[edu_group_of(age)]:
                    if age < 18:
                        student = 'full_time'
                    else:
                        band_key = '18_24' if age <= 24 else '25_ov'
                        share = TERTIARY_FT_SA1.get(str(sa1), {}).get(
                            band_key, TERTIARY_FT_CORE[band_key])
                        student = ('full_time' if rng.random() < share
                                   else 'part_time')
                else:
                    student = 'none'
                mob = int(rng.random() < (0.05 + 0.25 * max(0, (age - 70)) / 30.0))
                cav = int(lic == 1 and nv > 0)
                pw.writerow([pid, hid, sa1, BAND_LABEL[b], age, sex, est, occ, ib, lic,
                             nv, size, dt, student, mob, cav, round(1.0 / sample, 4)])
                members.append(dict(pid=pid, age=age, band=b, est=est, employed=employed,
                                    student=student, cav=cav, hx=hx, hy=hy))
                stats['persons'] += 1
                if employed:
                    stats['employed'] += 1
                if student == 'full_time':
                    stats['students'] += 1
                bk = abs_lf_band(age) or ('0_4' if age < 5 else '5_14')
                acc = bands.setdefault(bk, [0, 0, 0])
                acc[0] += 1
                acc[1] += int(employed)
                acc[2] += int(student == 'full_time')
            made += size


    for f in (hh_f, pp_f):
        f.close()

    stats['seed'] = seed
    stats['sample_fraction'] = sample
    stats['mean_household_size'] = round(stats['persons'] / max(stats['households'], 1), 3)
    stats['pct_zero_car_households'] = round(stats['zero_car_hh'] / max(stats['households'], 1) * 100, 1)
    stats['pct_employed_of_persons'] = round(stats['employed'] / max(stats['persons'], 1) * 100, 1)
    stats['by_abs_age_band'] = {
        k: dict(persons=n, employed_pct=round(100.0 * e / max(n, 1), 1),
                student_full_time_pct=round(100.0 * s / max(n, 1), 1))
        for k, (n, e, s) in sorted(bands.items())}
    json.dump(stats, open(os.path.join(out_dir, 'population', '_population_report.json'), 'w'), indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, help='override B.seed.master')
    ap.add_argument('--sample', type=float,
                    help='override B.population.build_sample_share')
    ap.add_argument('--max-sa1', type=int, default=None)
    ap.add_argument('--out', default=None,
                    help='override the demand directory (a verification build '
                         'writes beside the canonical one, never over it)')
    a = ap.parse_args()
    main(a.seed, a.sample, a.max_sa1, a.out)
