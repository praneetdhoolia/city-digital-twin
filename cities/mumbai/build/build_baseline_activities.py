"""Add mapped destinations and discretionary tours to the fixed resident cohort.

State time-use participation is an activity benchmark, not a trip rate. Declared
out-of-home fractions and time allocations are provisional modelling choices.
OSM points and areas are location candidates, never measured jobs or attraction capacity.
"""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import geopandas as gpd
import numpy as np
import pyogrio
import pandas as pd
from shapely.geometry import shape

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {'demand/baseline/plans_with_activities.xml.gz': ['demand/baseline/persons.csv',
                                                  'demand/baseline/plans.xml.gz',
                                                  'registry/B_baseline_activities.json',
                                                  'data/processed/geospatial/osm_research.gpkg',
                                                  'data/processed/geospatial/osm_activity_areas.geojson',
                                                  'data/processed/geospatial/census_2011_geographies.gpkg',
                                                  'data/processed/observed/state_time_use_controls.csv'],
 'demand/baseline/activities.csv': ['demand/baseline/persons.csv',
                                    'demand/baseline/plans.xml.gz',
                                    'registry/B_baseline_activities.json',
                                    'data/processed/geospatial/osm_research.gpkg',
                                                  'data/processed/geospatial/osm_activity_areas.geojson',
                                    'data/processed/geospatial/census_2011_geographies.gpkg',
                                    'data/processed/observed/state_time_use_controls.csv'],
 'data/processed/geospatial/baseline_activity_locations.csv': ['demand/baseline/persons.csv',
                                                               'demand/baseline/plans.xml.gz',
                                                               'registry/B_baseline_activities.json',
                                                               'data/processed/geospatial/osm_research.gpkg',
                                                  'data/processed/geospatial/osm_activity_areas.geojson',
                                                               'data/processed/geospatial/census_2011_geographies.gpkg',
                                                               'data/processed/observed/state_time_use_controls.csv'],
 'data/processed/acquisition/baseline_activities.json': ['demand/baseline/persons.csv',
                                                         'demand/baseline/plans.xml.gz',
                                                         'registry/B_baseline_activities.json',
                                                         'data/processed/geospatial/osm_research.gpkg',
                                                  'data/processed/geospatial/osm_activity_areas.geojson',
                                                         'data/processed/geospatial/census_2011_geographies.gpkg',
                                                         'data/processed/observed/state_time_use_controls.csv']}
INPUTS = OUTPUT_INPUTS['demand/baseline/plans_with_activities.xml.gz']


def read_rows(relative):
    with Path(city.path(relative)).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def write_rows(relative, records):
    if not records:
        raise ValueError('No records for ' + relative)
    with Path(city.path(relative)).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def eligible_purposes(tags, mapping):
    """Explicit positive tag matches; inactive features cannot attract a visit."""
    if any(tags.get(key) not in (None, 'no') for key in ('disused', 'abandoned', 'construction', 'proposed')):
        return []
    return [purpose for purpose, criteria in mapping.items()
            if any(tags.get(key) not in (None, '', 'no', 'vacant', 'disused')
                   and ('*' in values or tags[key] in values)
                   for key, values in criteria.items())]


def benchmark(rows, activity, residence, sex, denominator):
    selected = [r for r in rows if r['activity'] == activity and r['residence'] == residence
                and r['sex'] == sex and r['activity_scope'] == 'major_activity'
                and r['denominator'] == denominator]
    if len(selected) != 1:
        raise ValueError(f'Time-use benchmark must be unique: {activity}/{residence}/{sex}/{denominator}')
    row = selected[0]
    unit = 'percent' if denominator == 'participation' else 'minutes_per_day'
    if row['unit'] != unit:
        raise ValueError('Unexpected time-use unit: ' + row['unit'])
    return float(row['value']), row['source_id']


def select_destination(rng, home_xy, candidates, scale_m):
    """Stable distance-weighted sampling; candidate weights are declared proxies."""
    xy = np.array([(r['x_m'], r['y_m']) for r in candidates], dtype=float)
    distance = np.linalg.norm(xy - home_xy, axis=1)
    weights = np.array([r['weight'] for r in candidates], dtype=float)
    if scale_m <= 0 or not np.isfinite(scale_m) or np.any(weights <= 0):
        raise ValueError('Invalid destination weights or distance scale')
    logits = np.log(weights) - distance / scale_m
    weights = np.exp(logits - logits.max())
    return candidates[int(rng.choice(len(candidates), p=weights / weights.sum()))]


def main():
    sys.path.insert(0, city.path('extract'))
    from extract_transport_points import decode_hstore

    cfg = registry.load()
    rng = np.random.default_rng(cfg.get('B.activities.seed'))
    mapping = cfg.get('B.activities.location_tags')
    poi_probability = cfg.get('B.activities.poi_probability')
    scales = cfg.get('B.activities.distance_scale_m')
    purpose_benchmarks = cfg.get('B.activities.time_use_activities')
    outside = cfg.get('B.activities.out_of_home_fraction')
    time_fractions = cfg.get('B.activities.out_of_home_time_fraction')
    for values in (poi_probability, outside, time_fractions):
        if any(not np.isfinite(value) or not 0 <= value <= 1 for value in values.values()):
            raise ValueError('Activity fractions must be finite and within [0, 1]')
    if cfg.get('B.activities.max_optional_tours') < 0 or cfg.get('B.activities.home_break_s') <= 0:
        raise ValueError('Tour limit and home interval are invalid')
    if cfg.get('B.activities.discretionary_departure_s') < cfg.get('B.activities.departure_spread_s'):
        raise ValueError('Discretionary departure window crosses the start of the simulated day')
    residents = {r['person_id']: r for r in read_rows('demand/baseline/persons.csv')}
    tus = read_rows('data/processed/observed/state_time_use_controls.csv')
    zones = pyogrio.read_dataframe(city.path('data/processed/geospatial/census_2011_geographies.gpkg'),
                                  layer='census_leaves').to_crs(city.crs())
    zones = zones[zones.geometry.notna() & (zones.persons_count.astype(float) > 0)]
    zones = zones.sort_values('geography_id').reset_index(drop=True)
    zones_by_id = zones.set_index('geography_id')
    points = pyogrio.read_dataframe(city.path('data/processed/geospatial/osm_research.gpkg'),
                                   layer='points').to_crs(city.crs())
    points['purposes'] = points.other_tags.map(lambda text: eligible_purposes(decode_hstore(text), mapping))
    points = points[points.purposes.map(bool)].copy()
    selected_point_count = len(points)
    points['location_id'] = 'osm_node_' + points.osm_id.astype(str)
    points['source'] = 'OSM_point_location_not_capacity'
    inventory = json.loads(Path(city.path('data/processed/geospatial/osm_activity_areas.geojson')).read_text(encoding='utf-8'))
    area_rows = []
    for feature in inventory['features']:
        props = feature['properties']
        area_rows.append(dict(location_id='osm_' + props['osm_object_type'] + '_' + props['osm_object_id'],
            name=props['name'], purposes=eligible_purposes(props['all_driver_tags'], mapping),
            geometry=shape(feature['geometry']), source='OSM_area_representative_point_not_capacity_or_entrance'))
    areas = gpd.GeoDataFrame(area_rows, crs='EPSG:4326').to_crs(city.crs())
    # Only an exact, nonempty name inside a mapped area establishes a duplicate.
    # Remove shared purposes from the node, retaining any distinct node uses.
    duplicated_purposes = Counter()
    for index, point in points.iterrows():
        name = point.get('name')
        if not isinstance(name, str) or not name:
            continue
        covered = set()
        for area_index in areas.sindex.query(point.geometry, predicate='within'):
            area = areas.iloc[area_index]
            if name == area['name']:
                covered.update(area.purposes)
        removed = set(point.purposes) & covered
        duplicated_purposes.update(removed)
        points.at[index, 'purposes'] = [p for p in point.purposes if p not in removed]
    points = points[points.purposes.map(bool)]
    areas.geometry = areas.geometry.representative_point()
    columns = ['location_id', 'purposes', 'source', 'geometry']
    facilities = gpd.GeoDataFrame(pd.concat([points[columns], areas[columns]], ignore_index=True), crs=city.crs())
    matched = gpd.sjoin(facilities, zones[['geography_id', 'geometry']], how='left', predicate='within')
    matched = matched.sort_values(['location_id', 'geography_id'])
    ambiguous = int(matched.location_id.duplicated().sum())
    matched = matched.drop_duplicates('location_id')
    outside_zones = int(matched.geography_id.isna().sum())
    matched['geography_id'] = matched.geography_id.fillna('')
    locations = []
    candidates = {purpose: [] for purpose in mapping}
    for point in matched.itertuples():
        for purpose in point.purposes:
            row = dict(location_id=point.location_id, purpose=purpose,
                       geography_id=point.geography_id, x_m=float(point.geometry.x),
                       y_m=float(point.geometry.y), source=point.source)
            locations.append(row)
            candidates[purpose].append(dict(row, weight=1.0))
    if any(not values for values in candidates.values()):
        raise ValueError('A declared purpose has no mapped location candidates')
    fallback = [dict(location_id='census_' + str(row.geography_id), geography_id=row.geography_id,
                     x_m=float(row.geometry.representative_point().x),
                     y_m=float(row.geometry.representative_point().y),
                     weight=float(row.persons_count), source='historical_population_location_proxy')
                for row in zones.itertuples()]
    with gzip.open(city.path('demand/baseline/plans.xml.gz'), 'rb') as stream:
        population = ET.parse(stream).getroot()
    activities, tour_counts, source_counts = [], Counter(), Counter()
    benchmark_rows = {}
    total_primary_relocated = 0
    for person in population.findall('person'):
        resident = residents[person.get('id')]
        age, sex = int(resident['age_years']), resident['sex']
        home_zone = zones_by_id.loc[resident['home_geography_id']]
        residence = str(home_zone.rural_urban).lower()
        plan = person.find('plan')
        old_acts = plan.findall('activity')
        home = dict(old_acts[0].attrib)
        home.pop('end_time', None)
        home_xy = np.array([float(home['x']), float(home['y'])])
        tours = []
        primary = resident['purpose']
        if primary in ('work', 'education'):
            destination = dict(location_id='census_' + resident['destination_geography_id'],
                               geography_id=resident['destination_geography_id'],
                               x_m=float(old_acts[1].get('x')), y_m=float(old_acts[1].get('y')),
                               source='unchanged_primary_zone_proxy')
            if rng.random() < poi_probability[primary]:
                destination = select_destination(rng, home_xy, candidates[primary], scales[primary])
                total_primary_relocated += 1
            tours.append((primary, destination, float(resident['activity_duration_s']), resident['initial_mode']))
        optional = []
        if age >= cfg.get('B.activities.optional_min_age_years'):
            for purpose, activity in purpose_benchmarks.items():
                participation, source_id = benchmark(tus, activity, residence, sex, 'participation')
                minutes, _ = benchmark(tus, activity, residence, sex, 'per_participant')
                probability = participation / 100 * outside[purpose]
                seconds = minutes * 60 * time_fractions[purpose]
                if not 0 <= probability <= 1 or seconds <= 0:
                    raise ValueError('Invalid derived outing probability or duration')
                key = f'{residence}/{sex}/{purpose}'
                benchmark_rows[key] = dict(source_id=source_id, activity_participation_pct=participation,
                    modelled_outing_probability=probability, benchmark_minutes_per_participant=minutes,
                    modelled_duration_s=seconds, source='state_all_6_plus_benchmark_with_assumed_out_of_home_fractions')
                if rng.random() < probability:
                    optional.append((purpose, seconds))
        rng.shuffle(optional)
        optional = optional[:cfg.get('B.activities.max_optional_tours')]
        for purpose, seconds in optional:
            choices = candidates[purpose] if rng.random() < poi_probability[purpose] else fallback
            destination = select_destination(rng, home_xy, choices, scales[purpose])
            tours.append((purpose, destination, seconds, str(rng.choice(resident['permitted_modes'].split(',')))))
        for child in list(plan):
            plan.remove(child)
        first_departure = (float(resident['departure_s']) if primary in ('work', 'education') else
                           cfg.get('B.activities.discretionary_departure_s') + rng.uniform(
                               -cfg.get('B.activities.departure_spread_s'), cfg.get('B.activities.departure_spread_s')))
        for index, (purpose, destination, seconds, mode) in enumerate(tours):
            time_attribute = ({'end_time': str(round(first_departure))} if index == 0 else
                              {'max_dur': str(cfg.get('B.activities.home_break_s'))})
            ET.SubElement(plan, 'activity', **home, **time_attribute)
            ET.SubElement(plan, 'leg', mode=mode)
            ET.SubElement(plan, 'activity', type=purpose, x=str(destination['x_m']),
                          y=str(destination['y_m']), max_dur=str(round(seconds)))
            ET.SubElement(plan, 'leg', mode=mode)
            activities.append(dict(person_id=person.get('id'), tour_index=index, purpose=purpose,
                location_id=destination['location_id'], destination_geography_id=destination['geography_id'],
                x_m=destination['x_m'], y_m=destination['y_m'], duration_s=round(seconds),
                initial_mode=mode, source='synthetic_provisional_activity',
                destination_source=destination['source']))
            source_counts[destination['source']] += 1
        ET.SubElement(plan, 'activity', **home)
        tour_counts[len(tours)] += 1
    write_rows('data/processed/geospatial/baseline_activity_locations.csv', locations)
    write_rows('demand/baseline/activities.csv', activities)
    xml = b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n' + ET.tostring(population, encoding='utf-8')
    with Path(city.path('demand/baseline/plans_with_activities.xml.gz')).open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            stream.write(xml)
    audit = dict(source='provisional_activity_model_not_observed_trip_diaries',
        input_sha256={p: fingerprint(Path(city.path(p))) for p in INPUTS},
        residents_count=len(residents), location_candidates_by_purpose={k: len(v) for k, v in candidates.items()},
        selected_point_count=selected_point_count, retained_point_count=len(points), retained_area_count=len(areas),
        duplicate_node_purposes_removed=dict(duplicated_purposes),
        ambiguous_zone_matches_count=ambiguous, retained_locations_without_census_zone_count=outside_zones,
        primary_tours_relocated_count=total_primary_relocated, persons_by_tour_count=dict(sorted(tour_counts.items())),
        tours_by_purpose=dict(Counter(r['purpose'] for r in activities)), destination_sources=dict(source_counts),
        time_use_benchmarks=benchmark_rows,
        limitations=['OSM point and area coverage is uneven; attraction capacities and verified entrances are absent.',
            'Only exact nonempty named nodes inside same-purpose areas are deduplicated; other duplicates may remain.',
            'Research-envelope destinations outside available census polygons are retained without invented zone IDs.',
            'Each mapped location is an equal opportunity proxy, not one observed job or customer.',
            'State all-age activity participation is not local adult out-of-home travel; fractions and tour cap are assumed.',
            'Optional activities are home-based tours without household escort or joint scheduling.',
            'Actual route times determine subsequent departures; no guarantee all activities fit a civil day.',
            'No visitor/external passenger demand, work attendance calibration or ridership quota.'])
    Path(city.path('data/processed/acquisition/baseline_activities.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ('residents_count', 'location_candidates_by_purpose', 'persons_by_tour_count', 'tours_by_purpose')}))


if __name__ == '__main__':
    main()
