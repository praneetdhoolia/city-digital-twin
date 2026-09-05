#!/usr/bin/env python
"""Driver-licence holding rate by age band and LGA, observed over observed
(DECISIONS.md 9.131).

Numerator: TfNSW Driver Licence Statistics snapshot - holders whose PRIMARY
licence is any non-learner type (P1, P2, Unrestricted) of any class, by age
group and customer-address LGA, in the latest month the snapshot carries. A
learner may not drive unaccompanied and is not a driver for mode choice; a
holder whose primary class is Rider or a heavy class holds the car class
beneath it, so classes are not filtered. Suppressed cells ("<=5") are taken
at 3, the midpoint of what they can be, and counted.

Denominator: ABS estimated resident population by five-year age group and
LGA at 30 June 2024, the nearest official population to the snapshot. The
snapshot's age groups (16-17, 18-20, 21-24, then five-year groups) do not
all align with the ABS groups, and B.population.age_bands (12-17, 18-24,
then ten-year bands) align with neither below 25: the population inside a
five-year ABS group is split to single years by the census's own single-year
age profile for that LGA (G04), which is the only observed within-group
shape the package holds.

Writes data/processed/observed/licence_rates_by_age_lga.csv (one row per
LGA x model age band, plus a pooled row per band) and the pooled vector as
data/processed/observed/licence_rate_by_age_band.json, in the order of
B.population.age_bands, which the registry field carries and the population
builder reads per LGA.
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', '..', 'src'))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402
import csv, io, json, os, zipfile, collections, re  # noqa: E402
import pandas as pd  # noqa: E402

RAW = _city.path('data/raw')
OBS = _city.path('data/processed/observed')
CEN = _city.path('data/processed/census')
ZON = _city.path('data/processed/zones')


def snapshot_rows():
    z = zipfile.ZipFile(os.path.join(RAW, 'tfnsw', 'driver_licences_snapshot_2026.zip'))
    names = sorted(n for n in z.namelist() if n.lower().endswith('.csv'))
    latest = names[-1]
    month = re.search(r'(\d{6})', latest).group(1)
    raw = z.read(latest).decode('utf-8-sig').splitlines()
    return month, list(csv.DictReader(raw, delimiter='|'))


def count(c):
    c = c.strip()
    if c.startswith('<='):
        return 3.0
    return float(c)


def erp_by_lga(lgas):
    x = pd.ExcelFile(os.path.join(RAW, 'abs', '32350DS0003_2024.xlsx'))
    df = x.parse('Table 3', header=None)
    hdr = None
    for i in range(len(df)):
        if str(df.iloc[i, 0]).strip() == 'S/T code':
            hdr = i
            break
    groups = [str(g).replace('–', '-').replace('', '-').strip()
              for g in df.iloc[hdr - 1, 4:].tolist()]
    out = {}
    for i in range(hdr + 1, len(df)):
        name = str(df.iloc[i, 3]).strip()
        if name in lgas:
            vals = df.iloc[i, 4:].tolist()
            out[name] = {}
            for g, v in zip(groups, vals):
                try:
                    out[name][g] = float(v)
                except (TypeError, ValueError):
                    pass
    return out


def single_year_shape(lgas):
    """LGA -> {age: census persons}, from G04 single years (0..99), for the
    within-group split. 100+ carries no single years and is not needed."""
    sa1_lga = {}
    with open(os.path.join(ZON, 'sa1_to_lga.csv'), encoding='utf-8') as fh:
        for z in csv.DictReader(fh):
            sa1_lga[z['SA1_CODE21']] = z['lga_name']
    shape = collections.defaultdict(collections.Counter)
    for part in ('census2021_G04A_SA1.csv', 'census2021_G04B_SA1.csv'):
        path = os.path.join(CEN, part)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as fh:
            rd = csv.DictReader(fh)
            cols = [(c, int(c.split('_')[2])) for c in rd.fieldnames
                    if re.match(r'^Age_yr_\d+_P$', c)]
            for r in rd:
                lga = sa1_lga.get(r['SA1_CODE_2021'])
                if lga not in lgas:
                    continue
                for c, a in cols:
                    try:
                        shape[lga][a] += float(r[c] or 0)
                    except ValueError:
                        pass
    return shape


def erp_single_years(erp, shape):
    """LGA -> {age: ERP}, each ABS five-year group split by the census shape."""
    out = {}
    for lga, groups in erp.items():
        out[lga] = {}
        for g, v in groups.items():
            m = re.match(r'^(\d+)-(\d+)$', g)
            if m:
                lo, hi = int(m.group(1)), int(m.group(2))
            elif g.endswith('and over') or g.endswith('+'):
                lo, hi = int(re.match(r'^(\d+)', g).group(1)), 120
            else:
                continue
            ages = list(range(lo, min(hi, 99) + 1))
            w = [shape[lga].get(a, 0.0) for a in ages]
            tot = sum(w)
            for a, wa in zip(ages, w):
                out[lga][a] = v * (wa / tot if tot else 1.0 / len(ages))
    return out


def main():
    cfg = _registry.load(strict=True)
    bands = [tuple(b) for b in cfg.get('B.population.age_bands')]
    month, rows = snapshot_rows()
    # the LGAs that hold synthetic residents - the population the rates are
    # drawn for - never a typed list
    sa1_lga = {}
    with open(os.path.join(ZON, 'sa1_to_lga.csv'), encoding='utf-8') as fh:
        for z in csv.DictReader(fh):
            sa1_lga[z['SA1_CODE21']] = z['lga_name']
    lgas = set()
    with open(_city.path('data/processed/zones/zones_SA1.csv'), encoding='utf-8') as fh:
        for z in csv.DictReader(fh):
            if z.get('zone_tier') == 'core' and z['SA1_CODE21'] in sa1_lga:
                lgas.add(sa1_lga[z['SA1_CODE21']])
    # holders by (lga, snapshot age group)
    hold = collections.defaultdict(collections.Counter)
    suppressed = 0
    for r in rows:
        lga = r['CUSTOMER ADDRESS LGA'].strip()
        if lga not in lgas:
            continue
        if r['PRIMARY LICENCE FLAG'] != 'TRUE' or r['LICENCE TYPE'] == 'Learner':
            continue
        if r['COUNT'].strip().startswith('<='):
            suppressed += 1
        hold[lga][r['AGE GROUP'].strip()] += count(r['COUNT'])
    lgas = sorted(l for l in lgas if l in hold)
    erp = erp_by_lga(set(lgas))
    missing = [l for l in lgas if l not in erp]
    if missing:
        print('no ABS ERP row for %s - not rated (name differs or outside the cube)'
              % ', '.join(missing))
    lgas = [l for l in lgas if l in erp]
    shape = single_year_shape(set(lgas))
    erp1 = erp_single_years(erp, shape)

    def group_ages(g):
        m = re.match(r'^(\d+)-(\d+)$', g)
        if m:
            return list(range(int(m.group(1)), int(m.group(2)) + 1))
        if g.endswith('+'):
            return list(range(int(g[:-1]), 121))
        return []

    out_rows = []
    pooled_h = collections.Counter()
    pooled_p = collections.Counter()
    vector = []
    for lga in lgas:
        # holders to single years by the snapshot group's own ERP shape, then
        # to the model's bands - exact where the groups nest, shape-split
        # where they do not (16-17 and 18-20 inside 15-19)
        h1 = collections.Counter()
        for g, n in hold[lga].items():
            ages = group_ages(g)
            w = [erp1[lga].get(a, 0.0) for a in ages]
            tot = sum(w)
            for a, wa in zip(ages, w):
                h1[a] += n * (wa / tot if tot else 1.0 / max(1, len(ages)))
        for lo, hi in bands:
            h = sum(h1.get(a, 0.0) for a in range(lo, hi + 1))
            p = sum(erp1[lga].get(a, 0.0) for a in range(lo, hi + 1))
            rate = min(1.0, h / p) if p else 0.0
            out_rows.append(dict(lga=lga, band='%d-%d' % (lo, hi), holders=round(h, 1),
                                 erp_2024=round(p, 1), rate=round(rate, 4)))
            pooled_h[(lo, hi)] += h
            pooled_p[(lo, hi)] += p
    for lo, hi in bands:
        p = pooled_p[(lo, hi)]
        rate = min(1.0, pooled_h[(lo, hi)] / p) if p else 0.0
        vector.append(round(rate, 4))
        out_rows.append(dict(lga='ALL', band='%d-%d' % (lo, hi),
                             holders=round(pooled_h[(lo, hi)], 1),
                             erp_2024=round(p, 1), rate=round(rate, 4)))
    os.makedirs(OBS, exist_ok=True)
    with open(os.path.join(OBS, 'licence_rates_by_age_lga.csv'), 'w', newline='',
              encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['lga', 'band', 'holders', 'erp_2024', 'rate'],
                           lineterminator='\n')
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    json.dump(dict(decisions_ref='9.131', snapshot_month=month,
                   numerator='TfNSW Driver Licence Statistics snapshot: primary licence, any class, non-learner',
                   denominator='ABS ERP by age and LGA, 30 June 2024, split to single years by census G04',
                   suppressed_cells_taken_at_3=suppressed, lgas=lgas,
                   age_bands=['%d-%d' % b for b in bands], rate_by_age_band=vector),
              open(os.path.join(OBS, 'licence_rate_by_age_band.json'), 'w', newline='\n'), indent=2)
    print('snapshot %s; %d LGA(s); %d suppressed cell(s) at 3' % (month, len(lgas), suppressed))
    print('pooled rate by band:', ', '.join('%d-%d %.3f' % (b[0], b[1], v) for b, v in zip(bands, vector)))
    for lga in lgas:
        print('  %-15s %s' % (lga, ' '.join('%.2f' % r['rate'] for r in out_rows if r['lga'] == lga)))
    # The registry carries this pooled vector as B.population.licence_rate_by_age_band
    # (source `measured`), so the declared value and the observation it is
    # written from are two copies of one number. Asserted here, the way
    # build_mode_targets.py asserts its declared inputs against their sources
    # (DECISIONS.md 9.116): a re-derivation that moves the vector must move the
    # registry field in the same change, or the population builder draws
    # licences from a value the observation no longer supports.
    declared = [float(v) for v in cfg.get('B.population.licence_rate_by_age_band')]
    if len(declared) != len(vector) or any(abs(a - b) > 5e-5 for a, b in zip(declared, vector)):
        print('DRIFT: B.population.licence_rate_by_age_band declares %s but the '
              'snapshot derives %s - update the registry field in the same change'
              % (declared, vector))
        _sys.exit(1)
    print('B.population.licence_rate_by_age_band matches the derived vector')


if __name__ == '__main__':
    main()
