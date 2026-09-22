"""MATSim plans for the synthesised core population, at the harness's own sample (9.205).

The 1,000-person development chain (`build_baseline_population.py`,
`build_baseline_activities.py`, `build_baseline_choices.py`) does not scale to
the 27 million persons of `demand/population/B1_synthetic_population.csv`, and
a plans file for all of them would be tens of gigabytes the launcher reads at
every launch. This builder writes the plans of the households the HARNESS
would keep: `sample_population.keep()` - the framework's nested inclusion hash
on the household id and the seed - at `B.population.plans_build_fraction`, so a
run at `RUN.sample.fraction` f <= that fraction keeps exactly the households it
would have kept from a file of everyone (the hash nests), and the capacity
factors the harness derives from f stay the identities they are. The plans
report carries the build fraction; the launcher refuses a fraction above it.

What a person's day is, from the published data and the declared mechanisms:

  * home         a point drawn inside the leaf's census polygon; a municipal
                 ward with no polygon (the towns of the four districts other
                 than Greater Mumbai) inside its municipality's polygon from
                 the public MMR GIS; a village with no polygon inside its
                 taluka (IIT Bombay) - each placement labelled;
  * work         every main or marginal worker (B1) makes a home-work-home
                 tour unless drawn into B-28's "No travel" share (Census 2011
                 table B-28, the district's residence-to-work distance bands
                 by residence type); the workplace is a work location
                 candidate (`baseline_activity_locations.csv`, OSM) at a
                 distance from home in the band B-28 draws, drawn within the
                 band in proportion to the candidate's attraction - the GHSL
                 built volume around it, non-residential and total mixed by
                 the district's own-account job share (`B.activities.work_attraction`,
                 `activity_location_attraction.csv`; uniform when the gate says
                 so); timing from `B.baseline.activity_start_s` and
                 `B.baseline.activity_duration_s`;
  * education    every student (B1, the C-12 rates) makes a home-education-home
                 tour to an education candidate by the declared gravity
                 (`B.activities.distance_scale_m`), or a work tour first if
                 also a worker;
  * optional     shopping, social and leisure tours by the state time-use
                 participation benchmarks with the declared out-of-home
                 fractions (`B.activities.*`), as in the development chain, to
                 a candidate by the declared distance decay times its total
                 built volume (the same gate);
  * modes        `permittedModes` from the person's own attributes (age,
                 licence, the household's vehicles) as the development chain
                 declares them, one selected plan seeded with one drawn mode -
                 the run's own mode choice does the rest.

No freight movement is written: the development chain's port-to-gate proxy
(every truck between one port node and two network extremities) is not where
goods traffic occurs (GOAL.md requirement 4), and at citywide scale it would
load two corridors with millions of movements. The requirement stays open in
`docs/requirements.json` until a goods OD or a count-based share exists.
Nothing here is a trip diary or a result.
"""
from collections import Counter, defaultdict
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import sys
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import pyogrio
import shapely

import city
import registry
import sample_population
import subpopulations
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'demand/baseline/plans_core_sample.xml.gz': [
        'demand/population/B1_synthetic_population.csv', 'demand/population/B1_households.csv',
        'data/processed/zones/mmr_extent.csv',
        'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/geospatial/baseline_activity_locations.csv',
        'data/processed/geospatial/activity_location_attraction.csv',
        'data/processed/observed/census_2011_b28_commuting.csv',
        'data/processed/observed/state_time_use_controls.csv',
        'data/raw/boundaries/wri_mmr_layer_2_*.json', 'data/raw/boundaries/wri_mmr_layer_3_*.json',
        'data/raw/boundaries/iitb_boundary_*.zip',
        'registry/B_population.json', 'registry/B_baseline_demand.json', 'registry/B_baseline_activities.json'],
    'demand/baseline/_plans_core_sample_report.json': [
        'demand/population/B1_synthetic_population.csv', 'demand/population/B1_households.csv',
        'data/processed/zones/mmr_extent.csv',
        'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/geospatial/baseline_activity_locations.csv',
        'data/processed/geospatial/activity_location_attraction.csv',
        'data/processed/observed/census_2011_b28_commuting.csv',
        'data/processed/observed/state_time_use_controls.csv',
        'data/raw/boundaries/wri_mmr_layer_2_*.json', 'data/raw/boundaries/wri_mmr_layer_3_*.json',
        'data/raw/boundaries/iitb_boundary_*.zip',
        'registry/B_population.json', 'registry/B_baseline_demand.json', 'registry/B_baseline_activities.json'],
}
PERSONS = 'demand/population/B1_synthetic_population.csv'
OUT = 'demand/baseline/plans_core_sample.xml.gz'
REPORT = 'demand/baseline/_plans_core_sample_report.json'
BANDS = (('0-1', 0, 1000), ('2-5', 1000, 5000), ('6-10', 5000, 10000), ('11-20', 10000, 20000),
         ('21-30', 20000, 30000), ('31-50', 30000, 50000), ('51+', 50000, 400000))

_spec = importlib.util.spec_from_file_location('build_mmr_extent',
                                               Path(__file__).resolve().parents[1] / 'extract' / 'build_mmr_extent.py')
_extent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_extent)


def rows(relative):
    with Path(city.path(relative)).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def points_in(rng, geometry, n):
    """n uniform points inside a polygon, by rejection in its bounding box."""
    minx, miny, maxx, maxy = geometry.bounds
    out = np.empty((0, 2))
    prepared = shapely.prepared.prep(geometry)
    while len(out) < n:
        k = max(int((n - len(out)) * 4), 64)
        xs = rng.uniform(minx, maxx, k)
        ys = rng.uniform(miny, maxy, k)
        keep = [prepared.contains(shapely.Point(x, y)) for x, y in zip(xs, ys)]
        out = np.vstack([out, np.column_stack([xs, ys])[keep]])
    return out[:n]


def home_polygons(leaves_needed, records):
    """geography_id -> (polygon, placement) for the leaves that need one."""
    geo = pyogrio.read_dataframe(city.path('data/processed/geospatial/census_2011_geographies.gpkg'),
                                 layer='census_leaves', columns=['geography_id', 'name', 'subdistrict_code'])
    geo = geo.set_index('geography_id')
    municipal = {}
    for layer in (3, 2):
        for f in _extent.wri(layer, records)['features']:
            rings = f['geometry']['rings']
            poly = shapely.make_valid(shapely.MultiPolygon([shapely.Polygon(r) for r in rings])
                                      if len(rings) > 1 else shapely.Polygon(rings[0]))
            import geopandas as gpd                                       # noqa: PLC0415
            municipal[_extent.normal(f['attributes']['Name'])] = gpd.GeoSeries([poly], crs=4326).to_crs(city.crs()).iloc[0]
    cfg_aliases = {_extent.normal(k): _extent.normal(v)
                   for k, v in registry.load().get('A.extent.municipal_name_aliases').items()}
    talukas = {}
    import glob, zipfile                                                  # noqa: PLC0415
    for zip_path in sorted(glob.glob(city.path('data/raw/boundaries/iitb_boundary_*.zip'))):
        for member in zipfile.ZipFile(zip_path).namelist():
            if member.endswith('.shp'):
                frame = pyogrio.read_dataframe('zip://%s!%s' % (zip_path, member))
                if 'taluka_cod' in frame.columns:
                    frame = frame.to_crs(city.crs())
                    for code, g in zip(frame['taluka_cod'], frame.geometry):
                        talukas[str(code).zfill(5)] = shapely.make_valid(g)
    out = {}
    for gid in leaves_needed:
        row = geo.loc[gid]
        g = row.geometry
        if g is not None and not g.is_empty:
            out[gid] = (g, 'leaf_polygon')
            continue
        town = _extent.normal(_extent.town_name(row['name']))
        town = cfg_aliases.get(town, town)
        if town in municipal:
            out[gid] = (municipal[town], 'municipality_polygon')
            continue
        if str(row['subdistrict_code']) in talukas:
            out[gid] = (talukas[str(row['subdistrict_code'])], 'taluka_polygon')
            continue
        raise SystemExit('no polygon at any level for leaf %s (%s)' % (gid, row['name']))
    return out


def b28_bands(districts):
    """(district, residence) -> (p_no_travel, band probabilities) from table B-28, All Modes."""
    out = {}
    for r in rows('data/processed/observed/census_2011_b28_commuting.csv'):
        if r['district_code'] not in districts or r['mode_raw'] != 'All Modes':
            continue
        cell = out.setdefault((r['district_code'], r['residence']), {})
        cell[r['distance_band_km_raw']] = float(r['persons_count'])
    result = {}
    for key, cell in out.items():
        stated = sum(cell.get(b, 0.0) for b, _, _ in BANDS)
        total = stated + cell.get('No travel', 0.0)
        if total <= 0:
            continue
        result[key] = (cell.get('No travel', 0.0) / total,
                       np.array([cell.get(b, 0.0) for b, _, _ in BANDS]) / stated)
    return result


def benchmark(tus, activity, residence, sex, denominator):
    for r in tus:
        if (r['activity'] == activity and r['residence'] == residence and r['sex'] == sex
                and r['denominator'] == denominator):
            return float(r['value'])
    raise SystemExit('no time-use benchmark for %s/%s/%s/%s' % (activity, residence, sex, denominator))


def main():
    cfg = registry.load()
    build_fraction = float(cfg.get('B.population.plans_build_fraction'))
    seed = int(cfg.get('B.seed.master'))
    rng = np.random.default_rng(seed)
    adult = int(cfg.get('B.baseline.adult_age_years'))
    school_min = int(cfg.get('B.baseline.school_min_age_years'))
    starts, durations = cfg.get('B.baseline.activity_start_s'), cfg.get('B.baseline.activity_duration_s')
    spread = float(cfg.get('B.baseline.departure_spread_s'))
    modes_order = cfg.get('B.baseline.initial_choice_modes')
    scales = cfg.get('B.activities.distance_scale_m')
    poi_probability = cfg.get('B.activities.poi_probability')
    purposes_tus = cfg.get('B.activities.time_use_activities')
    outside = cfg.get('B.activities.out_of_home_fraction')
    time_fractions = cfg.get('B.activities.out_of_home_time_fraction')
    optional_min_age = int(cfg.get('B.activities.optional_min_age_years'))
    max_optional = int(cfg.get('B.activities.max_optional_tours'))
    home_break = int(cfg.get('B.activities.home_break_s'))
    disc_departure = float(cfg.get('B.activities.discretionary_departure_s'))
    disc_spread = float(cfg.get('B.activities.departure_spread_s'))
    records = []

    # the households the harness would keep, by the framework's own rule
    hh = pd.read_csv(city.path('demand/population/B1_households.csv'))
    kept = hh['household_id'].map(lambda h: sample_population.keep(None, build_fraction, seed=seed,
                                                                   household_id=int(h), unit='household'))
    kept_ids = set(hh.loc[kept, 'household_id'].tolist())
    print('households kept %d of %d at build fraction %g' % (len(kept_ids), len(hh), build_fraction), flush=True)
    persons = pd.concat([chunk[chunk['household_id'].isin(kept_ids)]
                         for chunk in pd.read_csv(city.path(PERSONS), chunksize=2_000_000)], ignore_index=True)
    print('persons kept', len(persons), flush=True)

    leaves = sorted(persons['geography_id'].unique())
    polygons = home_polygons(leaves, records)
    placement_counts = Counter(p for _, p in polygons.values())
    districts = sorted(persons['district_code'].astype(str).unique())
    bands = b28_bands(districts)
    tus = rows('data/processed/observed/state_time_use_controls.csv')
    locs = pd.read_csv(city.path('data/processed/geospatial/baseline_activity_locations.csv'))
    cand = {p: locs[locs['purpose'] == p][['x_m', 'y_m']].to_numpy() for p in locs['purpose'].unique()}
    # the attraction of every candidate (build_activity_attraction.py), aligned
    # with `cand`; ones when the gate draws uniformly
    attraction_gate = cfg.get('B.activities.work_attraction')
    attr = {p: np.ones(len(cand[p])) for p in cand}
    if attraction_gate == 'ghsl_nres_volume':
        weights_table = pd.read_csv(city.path('data/processed/geospatial/activity_location_attraction.csv'))
        for p in cand:
            merged = locs[locs['purpose'] == p][['location_id']].merge(
                weights_table[weights_table['purpose'] == p][['location_id', 'attraction_weight']],
                on='location_id', how='left', validate='one_to_one')
            if merged['attraction_weight'].isna().any():
                raise SystemExit('activity_location_attraction.csv lacks a weight for a %s candidate' % p)
            attr[p] = merged['attraction_weight'].to_numpy(dtype=float)
    # the census-zone fallback for optional tours: leaf representative points weighted by persons
    geo = pyogrio.read_dataframe(city.path('data/processed/geospatial/census_2011_geographies.gpkg'),
                                 layer='census_leaves', columns=['geography_id', 'persons_count'])
    geo = geo[geo.geometry.notna() & ~geo.geometry.is_empty & (geo['persons_count'].astype(float) > 0)]
    fallback_xy = np.column_stack([geo.geometry.representative_point().x, geo.geometry.representative_point().y])
    fallback_w = geo['persons_count'].astype(float).to_numpy()
    bench = {}
    for residence in ('urban', 'rural'):
        for sex in ('male', 'female'):
            for purpose, activity in purposes_tus.items():
                p = benchmark(tus, activity, residence, sex, 'participation') / 100 * outside[purpose]
                s = benchmark(tus, activity, residence, sex, 'per_participant') * 60 * time_fractions[purpose]
                bench[(residence, sex, purpose)] = (p, s)

    out = Path(city.path(OUT))
    out.parent.mkdir(parents=True, exist_ok=True)
    tour_counts, mode_counts, band_hits, no_candidate = Counter(), Counter(), Counter(), Counter()
    zero_attraction = Counter()
    persons_written = 0
    persons = persons.sort_values(['geography_id', 'household_id', 'person_id'])
    with out.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as z:
        z.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE population SYSTEM '
                b'"http://www.matsim.org/files/dtd/population_v6.dtd">\n<population>\n')
        for gid, group in persons.groupby('geography_id', sort=True):
            poly, _placement = polygons[gid]
            households = group['household_id'].unique()
            hxy = points_in(rng, poly, len(households))
            home_of = dict(zip(households, hxy))
            centre = np.array(poly.representative_point().coords[0])
            district = str(group['district_code'].iloc[0])
            residence = str(group['rural_urban'].iloc[0])
            p_no_travel, band_p = bands.get((district, residence)) or bands[(district, 'Total')]
            d_work = np.linalg.norm(cand['work'] - centre, axis=1)
            band_members = [np.flatnonzero((d_work >= lo) & (d_work < hi)) for _, lo, hi in BANDS]
            d_edu = np.linalg.norm(cand['education'] - centre, axis=1)
            w_edu = np.exp(-d_edu / scales['education'])
            w_edu /= w_edu.sum()
            opt_weights = {}
            for purpose in purposes_tus:
                d = np.linalg.norm(cand[purpose] - centre, axis=1)
                w = np.exp(-d / scales[purpose]) * attr[purpose]
                if w.sum() <= 0:                       # every candidate weightless: the decay alone
                    w = np.exp(-d / scales[purpose])
                    zero_attraction[purpose] += 1
                opt_weights[purpose] = w / w.sum()
            d_fb = np.linalg.norm(fallback_xy - centre, axis=1)
            w_fb = fallback_w * np.exp(-d_fb / scales['shopping'])
            w_fb /= w_fb.sum()
            lines = []
            for r in group.itertuples(index=False):
                age = int(r.age)
                home = home_of[r.household_id]
                licence = bool(r.licence_holder)
                available = ['walk', 'pt']
                if r.household_cars:
                    available.append('ride')
                if age >= adult:
                    available += ['taxi', 'auto_rickshaw']
                if age >= school_min and r.bike_available:
                    available.append('bike')
                if licence:
                    if r.car_available:
                        available.append('car')
                    if r.two_wheeler_available:
                        available.append('motorbike')
                available = [m for m in modes_order if m in available]
                tours = []
                is_worker = r.worker_status in ('main_worker', 'marginal_worker')
                if is_worker and rng.random() >= p_no_travel:
                    b = int(rng.choice(len(BANDS), p=band_p))
                    members = band_members[b]
                    k = b
                    while len(members) == 0:              # the nearest band with a candidate
                        k = k + 1 if k + 1 < len(BANDS) else k - 1
                        members = band_members[k]
                        no_candidate[BANDS[b][0]] += 1
                    band_hits[BANDS[k][0]] += 1
                    w = attr['work'][members]
                    if w.sum() > 0:
                        dest = cand['work'][int(rng.choice(members, p=w / w.sum()))]
                    else:                              # a band with no attraction at all: uniform, counted
                        zero_attraction['work'] += 1
                        dest = cand['work'][int(rng.choice(members))]
                    tours.append(('work', dest, starts['work'] + rng.uniform(-spread, spread), durations['work']))
                elif r.student and age >= school_min:
                    dest = cand['education'][int(rng.choice(len(w_edu), p=w_edu))]
                    tours.append(('education', dest, starts['education'] + rng.uniform(-spread, spread),
                                  durations['education']))
                if age >= optional_min_age:
                    optional = []
                    for purpose in purposes_tus:
                        p, s = bench[(residence.lower(), r.sex, purpose)]
                        if rng.random() < p:
                            optional.append((purpose, s))
                    rng.shuffle(optional)
                    for purpose, s in optional[:max_optional]:
                        if rng.random() < poi_probability[purpose]:
                            dest = cand[purpose][int(rng.choice(len(opt_weights[purpose]), p=opt_weights[purpose]))]
                        else:
                            dest = fallback_xy[int(rng.choice(len(w_fb), p=w_fb))]
                        tours.append((purpose, dest, disc_departure + rng.uniform(-disc_spread, disc_spread), s))
                mode = str(rng.choice(available))
                mode_counts[mode] += 1
                tour_counts[len(tours)] += 1
                attrs = [('subpopulation', subpopulations.RESIDENT, 'String'), ('householdId', int(r.household_id), 'String'),
                         ('age', age, 'Integer'), ('sex', r.sex, 'String')]
                if float(r.income_monthly_inr) > 0:      # no attribute for a person without one (IncomeScoringConfigGroup)
                    attrs.append(('income', float(r.income_monthly_inr), 'Double'))
                attrs += [('carAvail', 'always' if r.car_available else 'never', 'String'),
                         ('hasLicense', 'yes' if licence else 'no', 'String'),
                         ('bikeAvail', 'always' if r.bike_available else 'never', 'String'),
                         ('permittedModes', ','.join(available), 'String')]
                lines.append('<person id="%d"><attributes>' % r.person_id)
                for name, value, jtype in attrs:
                    lines.append('<attribute name="%s" class="java.lang.%s">%s</attribute>'
                                 % (name, jtype, escape(str(value))))
                lines.append('</attributes><plan selected="yes">')
                hx, hy = '%.1f' % home[0], '%.1f' % home[1]
                if not tours:
                    lines.append('<activity type="home" x="%s" y="%s" />' % (hx, hy))
                for i, (purpose, dest, depart, dur) in enumerate(tours):
                    if i == 0:
                        lines.append('<activity type="home" x="%s" y="%s" end_time="%d" />' % (hx, hy, round(depart)))
                    else:
                        lines.append('<activity type="home" x="%s" y="%s" max_dur="%d" />' % (hx, hy, home_break))
                    lines.append('<leg mode="%s" />' % mode)
                    lines.append('<activity type="%s" x="%.1f" y="%.1f" max_dur="%d" />' % (purpose, dest[0], dest[1], round(dur)))
                    lines.append('<leg mode="%s" />' % mode)
                if tours:
                    lines.append('<activity type="home" x="%s" y="%s" />' % (hx, hy))
                lines.append('</plan></person>')
                persons_written += 1
            z.write(('\n'.join(lines) + '\n').encode('utf-8'))
        z.write(b'</population>\n')
    report = dict(
        source='synthetic_plans_from_census_population_and_declared_mechanisms',
        build_fraction=build_fraction, seed=seed, sample_unit='household',
        households=len(kept_ids), households_in_population=int(len(hh)), persons=persons_written,
        persons_in_population=int(sum(1 for _ in open(city.path(PERSONS), encoding='utf-8')) - 1),
        leaves=len(leaves), home_placement=dict(placement_counts),
        persons_by_tour_count=dict(sorted(tour_counts.items())),
        initial_mode=dict(mode_counts), work_distance_band_drawn=dict(band_hits),
        work_band_without_candidate_redirected=dict(no_candidate),
        destination_attraction=attraction_gate,
        bands_or_leaves_without_attraction_drawn_uniform=dict(zero_attraction),
        freight='none: the port-to-gate proxy is not where goods traffic occurs; requirement open',
        inputs_sha256={p: fingerprint(Path(city.path(p))) for p in OUTPUT_INPUTS[OUT]
                       if '*' not in p and Path(city.path(p)).exists()},
        sources=records,
        limitations=['Work distances are the district B-28 residence-to-work bands (2011, other workers); a workplace is an '
                     'OSM work candidate uniform within the band, measured from the leaf\'s representative point.',
                     'Education and optional destinations follow the declared gravity scales; the time-use benchmarks are '
                     'state figures (docs/requirements.json: demand).',
                     'Homes in a municipal ward without a polygon are uniform within the municipality; in a village without '
                     'one, within its taluka.',
                     'One selected plan with one drawn seed mode; no initial alternatives (the run\'s mode choice innovates).',
                     'No freight, no external tier, no escort or joint travel, no observed trip diary.'])
    Path(city.path(REPORT)).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n',
                                       encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('build_fraction', 'households', 'persons', 'leaves', 'home_placement',
                                            'persons_by_tour_count', 'initial_mode', 'work_distance_band_drawn')}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
