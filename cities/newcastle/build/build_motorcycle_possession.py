#!/usr/bin/env python
"""Share of households holding a motorcycle, by postcode, observed over observed
(DECISIONS.md 9.214, D22, #257).

Numerator: BITRE Road Vehicles Australia (31 January 2025) motorcycles by
GARAGING postcode (data/raw/bitre/rva-2025-mvs-vehtype-streg-poagar-mtvpwr-rpc.csv,
summed over motive power and over every state of registration) - where the
vehicle is kept is the household's question, where its owner is recorded is
not (BITRE: the garaging postcode where recorded, else the registered one).
The postal areas are the study area's, found by geometry in
data/processed/observed/bitre_registrations_study_area.csv
(extract/extract_bitre_registrations.py, more than half inside the core).

Denominator: census 2021 occupied private dwellings (G34 Total_dwelings) of
the SA1s whose largest overlap is that postal area. Every SA1 the package's
census carries (core and external ring) is assigned to one postal area by the
geometry alone - the ABS SA1 and POA polygons in the city's CRS - so no
postcode and no correspondence is typed. The census motor-vehicle count
excludes motorcycles, so the car and the motorcycle possession stay separate
quantities.

Identity: lambda = motorcycles / dwellings per postal area, and the share of
households holding at least one by B.motorbike.possession_identity
(src/build/possession.py; Poisson at-least-one by default, the identity 9.209
uses). The pooled share over the core SA1s' dwellings is declared as
B.population.household_motorcycle_share and asserted against here.

Writes data/processed/observed/motorcycle_possession_by_postcode.csv,
motorcycle_possession_by_sa1.csv (core SA1s whose postal area carries a rate)
and _motorcycle_possession_report.json.
"""
import sys as _sys
import city as _city
import registry as _registry
import possession
import csv, json, os

OBS = _city.path('data/processed/observed')
BITRE = os.path.join(OBS, 'bitre_registrations_study_area.csv')
GARAGING = _city.path('data/raw/bitre/rva-2025-mvs-vehtype-streg-poagar-mtvpwr-rpc.csv')
G34 = _city.path('data/processed/census/census2021_G34_SA1.csv')
SA1_GEOM = _city.path('data/processed/zones/zones_SA1.gpkg')
POA = _city.path('data/raw/boundaries/POA_2021_AUST_GDA2020_SHP.zip')
# BITRE's own vehicle-type label and the census column of occupied private
# dwellings - the two sources' vocabularies, not modelling values
MOTORCYCLE_TYPE = 'Motorcycles'
DWELLINGS_COLUMN = 'Total_dwelings'

OUTPUT_INPUTS = {
    'data/processed/observed/motorcycle_possession_by_postcode.csv': [
        'data/processed/observed/bitre_registrations_study_area.csv',
        'data/raw/bitre/rva-2025-mvs-vehtype-streg-poagar-mtvpwr-rpc.csv',
        'data/processed/census/census2021_G34_SA1.csv',
        'data/processed/zones/zones_SA1.gpkg',
        'data/raw/boundaries/POA_2021_AUST_GDA2020_SHP.zip'],
    'data/processed/observed/motorcycle_possession_by_sa1.csv': [
        'data/processed/observed/bitre_registrations_study_area.csv',
        'data/raw/bitre/rva-2025-mvs-vehtype-streg-poagar-mtvpwr-rpc.csv',
        'data/processed/census/census2021_G34_SA1.csv',
        'data/processed/zones/zones_SA1.gpkg',
        'data/raw/boundaries/POA_2021_AUST_GDA2020_SHP.zip'],
    'data/processed/observed/_motorcycle_possession_report.json': [
        'data/processed/observed/bitre_registrations_study_area.csv',
        'data/raw/bitre/rva-2025-mvs-vehtype-streg-poagar-mtvpwr-rpc.csv',
        'data/processed/census/census2021_G34_SA1.csv',
        'data/processed/zones/zones_SA1.gpkg',
        'data/raw/boundaries/POA_2021_AUST_GDA2020_SHP.zip'],
}


def motorcycles_by_postcode():
    """{study postcode: motorcycles garaged there}, and the registered count
    beside it for the report. The study set is the registration extract's
    (geometry-derived); the count is the garaging file's."""
    registered = {}
    with open(BITRE, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['vehicle_type'] == MOTORCYCLE_TYPE:
                registered[r['postcode']] = int(r['vehicles'])
    garaged = {p: 0 for p in registered}
    with open(GARAGING, encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            if r['vehicle_type'] == MOTORCYCLE_TYPE and r['garaging_postcode'] in garaged:
                garaged[r['garaging_postcode']] += int(r['no_vehicles'])
    return garaged, registered


def dwellings_by_sa1():
    out = {}
    with open(G34, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            try:
                out[r['SA1_CODE_2021']] = float(r[DWELLINGS_COLUMN] or 0)
            except ValueError:
                continue
    return out


def sa1_postcode():
    """({SA1: postcode of its largest overlap}, {SA1: tier},
    {postcode: share of its area the census SA1s cover}) in the city's CRS."""
    import geopandas as gpd
    crs = _city.crs()
    sa1 = gpd.read_file(SA1_GEOM).to_crs(crs)
    sa1['SA1_CODE21'] = sa1['SA1_CODE21'].astype(str)
    poa = gpd.read_file('zip://' + POA).to_crs(crs)
    code = next(c for c in poa.columns if c.upper().startswith('POA_CODE'))
    covered = sa1.geometry.union_all()
    poa = poa[poa.geometry.intersects(covered)].copy()
    poa['coverage'] = poa.geometry.intersection(covered).area / poa.geometry.area
    ov = gpd.overlay(sa1[['SA1_CODE21', 'geometry']], poa[[code, 'geometry']],
                     how='intersection', keep_geom_type=True)
    ov['area_m2'] = ov.geometry.area
    # ties broken by the postcode so the assignment never depends on row order
    ov = ov.sort_values(['SA1_CODE21', 'area_m2', code], ascending=[True, False, True])
    best = ov.drop_duplicates('SA1_CODE21', keep='first')
    assign = {str(r['SA1_CODE21']): str(r[code]) for _, r in best.iterrows()}
    tier = dict(zip(sa1['SA1_CODE21'], sa1['zone_tier']))
    coverage = {str(r[code]): float(r['coverage']) for _, r in poa.iterrows()}
    return assign, tier, coverage


def main():
    cfg = _registry.load(strict=True)
    identity = cfg.get('B.motorbike.possession_identity')
    moto, registered = motorcycles_by_postcode()
    dw = dwellings_by_sa1()
    assign, tier, coverage = sa1_postcode()
    hh = {}
    for s, p in assign.items():
        hh[p] = hh.get(p, 0.0) + dw.get(s, 0.0)
    rows, share = [], {}
    for p in sorted(moto):
        h = hh.get(p, 0.0)
        lam = moto[p] / h if h > 0 else None
        s = possession.share_owning(moto[p], h, identity)
        if s is not None:
            share[p] = s
        rows.append(dict(postcode=p, motorcycles_garaged=moto[p],
                         motorcycles_registered=registered[p],
                         households_census2021=int(round(h)),
                         census_area_coverage=round(coverage.get(p, 0.0), 4),
                         lambda_per_household='' if lam is None else round(lam, 5),
                         p_household_holds_motorcycle='' if s is None else round(s, 5)))
    with open(os.path.join(OBS, 'motorcycle_possession_by_postcode.csv'), 'w',
              newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    core = sorted(s for s, t in tier.items() if t == 'core')
    sa1_rows = [dict(SA1_CODE21=s, postcode=assign[s],
                     p_household_holds_motorcycle=round(share[assign[s]], 5))
                for s in core if assign.get(s) in share]
    with open(os.path.join(OBS, 'motorcycle_possession_by_sa1.csv'), 'w',
              newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['SA1_CODE21', 'postcode',
                                           'p_household_holds_motorcycle'],
                           lineterminator='\n')
        w.writeheader()
        w.writerows(sa1_rows)
    rated = {r['SA1_CODE21'] for r in sa1_rows}
    num = sum(dw.get(s, 0.0) * share[assign[s]] for s in rated)
    den = sum(dw.get(s, 0.0) for s in rated)
    pooled = round(num / den, 4) if den else 0.0
    unrated = [s for s in core if s not in rated]
    values = sorted(share.values())
    report = dict(
        decisions_ref='9.214', identity=identity,
        numerator='BITRE Road Vehicles Australia, 31 January 2025: motorcycles by GARAGING '
                  'postcode (rva-2025-mvs-vehtype-streg-poagar-mtvpwr-rpc.csv, every motive '
                  'power and state of registration), for the study postal areas of '
                  'bitre_registrations_study_area.csv',
        motorcycles_garaged=sum(moto.values()),
        motorcycles_registered=sum(registered.values()),
        denominator='census 2021 occupied private dwellings (G34) of the SA1s whose largest '
                    'overlap is the postal area',
        postcodes=len(moto), postcodes_rated=len(share),
        postcodes_without_households=sorted(p for p in moto if p not in share),
        share_range=[round(values[0], 4), round(values[-1], 4)] if values else None,
        core_sa1_rated=len(rated), core_sa1_unrated=len(unrated),
        core_dwellings_unrated=int(round(sum(dw.get(s, 0.0) for s in unrated))),
        pooled_share_core_dwelling_weighted=pooled,
        note='The garaging postcode is where the vehicle is kept (BITRE falls back to the '
             'registered postcode where none is recorded); business, fleet and dealer '
             'vehicles are in the stock - one postal area holds twice as many garaged as '
             'registered motorcycles (see the table); the census dwellings are '
             '2021 against a 2025 stock. A core SA1 whose postal area is outside the study '
             'set takes B.population.household_motorcycle_share in the plans builder.')
    with open(os.path.join(OBS, '_motorcycle_possession_report.json'), 'w',
              encoding='utf-8', newline='\n') as fh:
        json.dump(report, fh, indent=2)
        fh.write('\n')
    print('%d postcodes, %d rated; share %s; %d core SA1 rated, %d unrated (%d dwellings); '
          'pooled %.4f (%s)' % (len(moto), len(share), report['share_range'], len(rated),
                                len(unrated), report['core_dwellings_unrated'], pooled, identity))
    declared = float(cfg.get('B.population.household_motorcycle_share'))
    if abs(declared - pooled) > 5e-5:
        print('DRIFT: B.population.household_motorcycle_share declares %s but the '
              'garaged motorcycles derive %s - update the registry field in the same change'
              % (declared, pooled))
        _sys.exit(1)
    print('B.population.household_motorcycle_share matches the derived value')


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
