"""The second city's builders, stage by stage, on fixtures a test can build.

Until the sixteenth report every Mumbai builder was one 155-215 line main()
no test imported; the stage functions split_stages.py made of them
(8 October 2026) take their inputs as arguments, so each is exercised here
on a three-leaf census, a three-person population or a two-train sheet,
with the city's own paths redirected to a temporary directory.
"""
import csv
import gzip
import io
import json
import os
import sys
import types
import zipfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MUMBAI_BUILD = os.path.join(REPO, 'cities', 'mumbai', 'build')
if MUMBAI_BUILD not in sys.path:
    sys.path.insert(0, MUMBAI_BUILD)

pd = pytest.importorskip('pandas')
# the builders import the geospatial stack at module level; the CI unit job
# installs the standard library and pandas only, so these tests run where the
# package is installed (the workstation) and are skipped, not failed, elsewhere
pytest.importorskip('pyogrio')
pytest.importorskip('geopandas')


class FakeCfg:
    def __init__(self, values):
        self.values = values

    def get(self, key):
        return self.values[key]


def _city_in(monkeypatch, module, tmp_path):
    """Point a builder's `city.path` at a temporary city directory."""
    monkeypatch.setattr(module.city, 'path', lambda *parts: str(tmp_path.joinpath(*parts)))


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------ gtfs_feed

def test_gtfs_feed_writes_the_same_bytes_twice_and_widens_appended_columns(tmp_path):
    import gtfs_feed
    content = {'stops.txt': gtfs_feed.table([dict(stop_id='a', stop_name='A')], ['stop_id', 'stop_name'])}
    gtfs_feed.append_table(content, 'stops.txt', [dict(stop_id='b', stop_name='B', stop_lon='72.8')])
    assert content['stops.txt'] == b'stop_id,stop_name,stop_lon\na,A,\nb,B,72.8\n'
    gtfs_feed.write_feed(tmp_path / 'one.zip', content)
    gtfs_feed.write_feed(tmp_path / 'two.zip', content)
    assert (tmp_path / 'one.zip').read_bytes() == (tmp_path / 'two.zip').read_bytes()
    with zipfile.ZipFile(tmp_path / 'one.zip') as z:
        assert z.namelist() == ['stops.txt'] and z.read('stops.txt') == content['stops.txt']


# ------------------------------------------------------------ build_population

TOP = 100


def _population_inputs():
    districts = ['519']
    leaves = []
    for i, (persons, males, hh) in enumerate(((40, 21, 10), (30, 14, 8), (0, 0, 0))):
        leaves.append(dict(geography_id='27:519:%d' % i, district_code='519', rural_urban='Urban',
                           subdistrict_code='99999', town_village_code='802794', ward_code='%04d' % (i + 1),
                           male_persons_count=str(males), female_persons_count=str(persons - males),
                           persons_count=str(persons), persons_age_0_6_count=str(persons // 10),
                           households_count=str(hh), main_workers_count=str(persons // 3),
                           marginal_workers_count=str(persons // 10),
                           male_main_workers_count=str(males // 2), male_marginal_workers_count='1',
                           female_main_workers_count=str((persons - males) // 4), female_marginal_workers_count='1'))
    w = np.ones(TOP + 1)
    ages = {('519', 'Urban', s): w / w.sum() for s in ('male', 'female')}
    work = {('519', 'Total', s): (np.full(TOP + 1, 0.5), np.full(TOP + 1, 0.1)) for s in ('male', 'female')}
    attend = {('519', 'Total'): {act: np.full(TOP + 1, 0.3) for act in ('main_worker', 'marginal_worker', 'non_worker')}}
    profile = dict(area_name='Ward', household_size_1_pct='10', household_size_2_pct='20', household_size_3_pct='20',
                   household_size_4_pct='30', household_size_5_pct='10', household_size_6_to_8_pct='8',
                   household_size_9_plus_pct='2', households_with_two_wheeler_pct='30',
                   households_with_car_jeep_van_pct='10', households_with_bicycle_pct='20')
    profiles = {('519', '00000', '000000', '0000', 'Total'): profile}
    factors = {'519': {'male': 1.0, 'female': 1.0}}
    return districts, leaves, ages, work, attend, profiles, factors


def test_synthesise_leaves_writes_every_projected_person_and_counts_substitutions(tmp_path, monkeypatch):
    import build_population as bp
    _city_in(monkeypatch, bp, tmp_path)
    _districts, leaves, ages, work, attend, profiles, factors = _population_inputs()
    cfg = FakeCfg({'B.population.bike_min_age': 5})
    rng = np.random.default_rng(1)
    by_district, profile_levels, substituted, totals = bp.synthesise_leaves(
        adult=18, ages=ages, attend=attend, cfg=cfg, factors=factors, growth={}, income_median=20000.0,
        income_min=5000.0, income_sigma=0.5, leaves=leaves, licence_p=0.6, open_max=12, profiles=profiles,
        rng=rng, tertiary=0.0, work=work)
    persons = pd.read_csv(tmp_path / bp.PERSONS)
    households = pd.read_csv(tmp_path / bp.HOUSEHOLDS)
    assert totals['leaves'] == 2                       # the empty leaf writes nothing
    assert len(persons) == 70 and by_district['519']['persons'] == 70
    assert list(persons.columns) == bp.PERSON_COLUMNS
    assert persons['person_id'].tolist() == list(range(1, 71))
    assert households['size'].sum() == 70 and households['household_id'].is_unique
    assert set(persons['household_id']) == set(households['household_id'])
    # the leaf's own residence cell was unpublished for work and attendance:
    # the district's Total cell stood in, and the report says so per district
    assert substituted['age_distribution'] == {}
    assert substituted['worker_rates'] == {'519': 4}          # two leaves x two sexes
    assert substituted['attendance_rates'] == {'519': 2}
    assert profile_levels == {'district': 2}
    grand = bp.district_summaries(by_district, factors, {})
    assert grand['persons'] == 70 and by_district['519']['mean_household_size'] == round(70 / len(households), 3)


def test_synthesise_leaves_refuses_a_district_with_no_cell_at_any_level(tmp_path, monkeypatch):
    import build_population as bp
    _city_in(monkeypatch, bp, tmp_path)
    _districts, leaves, ages, work, attend, profiles, factors = _population_inputs()
    del work[('519', 'Total', 'male')]
    with pytest.raises(SystemExit, match='worker_rates has no cell'):
        bp.synthesise_leaves(adult=18, ages=ages, attend=attend, cfg=FakeCfg({'B.population.bike_min_age': 5}),
                             factors=factors, growth={}, income_median=20000.0, income_min=5000.0,
                             income_sigma=0.5, leaves=leaves, licence_p=0.6, open_max=12, profiles=profiles,
                             rng=np.random.default_rng(1), tertiary=0.0, work=work)


def test_district_cell_takes_the_leaf_cell_first_and_counts_the_fallback():
    import build_population as bp
    from collections import Counter
    counts = {'age_distribution': Counter()}
    table = {('519', 'Rural', 'male'): 'own', ('519', 'Urban', 'male'): 'urban'}
    assert bp.district_cell(table, ('519', 'Rural', 'male'), 'Urban', counts, 'age_distribution') == 'own'
    assert counts['age_distribution'] == {}
    table[('519', 'Urban', 'female')] = 'urban_f'
    assert bp.district_cell(table, ('519', 'Rural', 'female'), 'Urban', counts, 'age_distribution') == 'urban_f'
    assert counts['age_distribution'] == {'519': 1}
    with pytest.raises(SystemExit):
        bp.district_cell(table, ('520', 'Rural', 'female'), 'Urban', counts, 'age_distribution')


# ------------------------------------------------------------ build_plans

def test_kept_persons_reads_the_population_once_and_counts_it(tmp_path, monkeypatch):
    import build_plans as bpl
    _city_in(monkeypatch, bpl, tmp_path)
    _write_csv(tmp_path / 'demand/population/B1_households.csv',
               [dict(household_id=h, geography_id='27:519:0', size=1, two_wheelers=0, cars=0, bicycles=0)
                for h in range(1, 21)])
    _write_csv(tmp_path / 'demand/population/B1_synthetic_population.csv',
               [dict(person_id=p, household_id=p, geography_id='27:519:0', age=30) for p in range(1, 21)])
    hh, kept_ids, persons, persons_in_population = bpl.kept_persons(build_fraction=1.0, seed=20260810)
    assert len(hh) == 20 and kept_ids == set(range(1, 21))
    assert persons_in_population == 20 and len(persons) == 20
    hh, kept_ids, persons, n = bpl.kept_persons(build_fraction=0.5, seed=20260810)
    assert n == 20 and 0 < len(kept_ids) < 20 and set(persons['household_id']) == kept_ids


def test_band_redirects_climb_first_then_descend_and_refuse_an_empty_set():
    import build_plans as bpl
    empty = np.array([], dtype=int)
    members = [empty, np.array([1]), empty, empty, np.array([2, 3]), empty, empty]
    assert bpl.band_redirects(members) == {0: 1, 2: 4, 3: 4, 5: 4, 6: 4}
    assert bpl.band_redirects([empty] * len(bpl.BANDS)) is None
    with pytest.raises(SystemExit, match='no band holds a work candidate'):
        bpl.refuse_no_candidate('27:519:0', '0-1')


# ------------------------------------------------------------ build_mode_targets

def test_active_and_car_passenger_splits_from_fixture_tables(tmp_path, monkeypatch):
    import build_mode_targets as bmt
    _city_in(monkeypatch, bmt, tmp_path)
    _write_csv(tmp_path / 'data/processed/observed/census_2011_b28_commuting.csv', [
        dict(district_code='519', residence='Total', distance_band_km_raw='Total', mode_raw='On foot', persons_count='300'),
        dict(district_code='519', residence='Total', distance_band_km_raw='Total', mode_raw='Bicycle', persons_count='100'),
        dict(district_code='519', residence='Urban', distance_band_km_raw='0-1', mode_raw='Bicycle', persons_count='999')])
    b28, bicycle_of_active = bmt.active_split()
    assert bicycle_of_active == pytest.approx(0.25) and b28 == {'On foot': 300.0, 'Bicycle': 100.0}
    _write_csv(tmp_path / 'demand/population/B1_synthetic_population.csv', [
        dict(person_id=1, age=30, household_cars=1, car_available=1),
        dict(person_id=2, age=30, household_cars=1, car_available=0),
        dict(person_id=3, age=3, household_cars=1, car_available=0),     # under 5: not counted
        dict(person_id=4, age=40, household_cars=0, car_available=0)])   # no car: not counted
    drivers, passenger_share, riders = bmt.car_passenger_split()
    assert (drivers, riders) == (1, 1) and passenger_share == 0.5


# ------------------------------------------------------------ build_regional_bus_feed

def test_add_pattern_emits_a_route_its_stops_and_a_trip_per_departure():
    import build_regional_bus_feed as brb
    additions = {n: [] for n in ('agency.txt', 'routes.txt', 'trips.txt', 'stop_times.txt')}
    used = {}
    stops = [dict(stop_id='NMMT_1', stop_name='A', stop_lon=73.0, stop_lat=19.0),
             dict(stop_id='NMMT_2', stop_name='B', stop_lon=73.1, stop_lat=19.1)]
    brb.add_pattern(additions, used, 'SVC', 'NMMT', 'NMMT_r1', '1', stops, [0, 600],
                    [('NMMT_r1_t1', 6 * 3600), ('NMMT_r1_t2', 7 * 3600)])
    assert [r['route_id'] for r in additions['routes.txt']] == ['NMMT_r1']
    assert set(used) == {'NMMT_1', 'NMMT_2'}
    assert [t['trip_id'] for t in additions['trips.txt']] == ['NMMT_r1_t1', 'NMMT_r1_t2']
    assert additions['stop_times.txt'][1] == dict(trip_id='NMMT_r1_t1', arrival_time='06:10:00',
                                                  departure_time='06:10:00', stop_id='NMMT_2', stop_sequence=2)
    assert brb.pooled_headway([1800, 1800], fleet=4, terminal_dwell=300) == 1050


# ------------------------------------------------------------ build_suburban_timetable_feed

def test_read_sheets_and_assemble_trains_on_a_two_train_sheet():
    import build_suburban_timetable_feed as bst
    from collections import Counter, defaultdict
    sheets = {'wr_up': dict(line='WR', role='primary')}
    cells = []
    for train, clocks in (('91001', ('06:00', '06:10', '06:25')), ('91002', ('07:05', '07:15', '07:30'))):
        for order, (label, hhmm) in enumerate(zip(('Churchgate', 'Dadar', 'Bandra'), clocks)):
            cells.append(dict(source_id='wr_up', train_number=train, source_page='1', station_row_order=str(order),
                              aligned_station_row_label=label, printed_local_hhmm=hhmm))
    by_sheet_train = defaultdict(list)
    for c in cells:
        by_sheet_train[(c['source_id'], c['train_number'])].append(c)
    line_index = {'WR': ({'churchgate': 'n1', 'dadar': 'n2', 'bandra': 'n3'}, {})}
    aliases = {'labels': {}, 'skipped': {}}
    readings, refused, counts, unresolved, trains = defaultdict(list), [], Counter(), Counter(), {}
    bst.read_sheets(aliases, by_sheet_train, counts, line_index, readings, refused, sheets, unresolved)
    assert counts['readings'] == 2 and not refused
    assert readings[('WR', '91001')][0][1] == [('n1', 6 * 3600), ('n2', 6 * 3600 + 600), ('n3', 6 * 3600 + 1500)]
    skipped = bst.assemble_trains(counts, readings, refused, sheets, trains, unresolved)
    assert skipped == {} and counts['trains_read'] == 2
    assert trains[('WR', '91002')]['direction'] == 'sheet' and trains[('WR', '91002')]['role'] == 'primary'


def test_sequence_times_reads_the_direction_from_the_clocks():
    import build_suburban_timetable_feed as bst
    forward = [(0, 'a', 100), (1, 'b', 200), (2, 'c', 300)]
    assert bst.sequence_times(forward) == (forward, 'sheet')
    stops, direction = bst.sequence_times([(0, 'a', 300), (1, 'b', 200), (2, 'c', 100)])
    assert direction == 'reverse' and [s[1] for s in stops] == ['c', 'b', 'a']
    assert bst.sequence_times([(0, 'a', 300), (1, 'b', 100), (2, 'c', 200)]) == (None, 'non_monotonic_times')


# ------------------------------------------------------------ build_baseline_transit_feed

def test_merge_printed_timetable_takes_the_printed_feeds_tables(tmp_path, monkeypatch):
    import build_baseline_transit_feed as btf
    _city_in(monkeypatch, btf, tmp_path)
    (tmp_path / 'schedules').mkdir()
    with zipfile.ZipFile(tmp_path / 'schedules/baseline_suburban_timetable.zip', 'w') as z:
        z.writestr('stops.txt', 'stop_id,stop_name,stop_lon,stop_lat\nBASE_OSM_1,Churchgate,72.8,18.9\n')
        z.writestr('routes.txt', 'route_id,agency_id,route_short_name,route_long_name,route_type\n'
                                 'BASE_TT_WR_P1,BASELINE,WR,Churchgate to Virar,2\n')
        z.writestr('trips.txt', 'route_id,service_id,trip_id,direction_id\nBASE_TT_WR_P1,S,BASE_TT_WR_91001,0\n')
        z.writestr('stop_times.txt', 'trip_id,arrival_time,departure_time,stop_id,stop_sequence\n'
                                     'BASE_TT_WR_91001,06:00:00,06:00:00,BASE_OSM_1,0\n')
    new_stops, new_routes, new_trips, new_times, report = {}, [], [], [], []
    n = btf.merge_printed_timetable(new_routes, new_stops, new_times, new_trips, report, 'printed_timetables')
    assert n == 1 and list(new_stops) == ['BASE_OSM_1'] and new_stops['BASE_OSM_1']['stop_lon'] == 72.8
    assert report == [dict(route_id='BASE_TT_WR_P1', mode='train', stops_count=None, departures_count=1,
                           geometry_source='mapped_native_stops', timetable_source='printed_timetable_trips')]
    assert btf.merge_printed_timetable([], {}, [], [], [], 'generated') == 0


def test_published_trips_check_counts_a_relation_pair_once():
    import build_baseline_transit_feed as btf
    cfg = FakeCfg({'A.baseline_transit.line_published_weekday_trips': {
        'harbour': dict(relations=['1', '2'], trips=100)}})
    report = [dict(osm_relation_id='1', departures_count=60), dict(osm_relation_id='2', departures_count=50)]
    out = btf.published_trips_check(cfg, report)
    assert out['harbour'] == dict(relations=['1', '2'], generated_departures=110, published_weekday_trips=100,
                                  deviation_pct=10.0)


def test_directory_clock_reads_the_boards_printed_forms():
    import build_baseline_transit_feed as btf
    assert btf.directory_clock('05.30 AM', 0) == 5 * 3600 + 30 * 60
    assert btf.directory_clock('12.00 AM', 0) == 24 * 3600
    assert btf.directory_clock('09:00 PM (BHAYANDER)', 0) == 21 * 3600
    assert btf.directory_clock('no clock here', 42) == 42


# ------------------------------------------------------------ build_baseline_activities

def test_eligible_purposes_and_the_distance_weighted_destination():
    import build_baseline_activities as bba
    mapping = {'shopping': {'shop': ['*']}, 'education': {'amenity': ['school']}}
    assert bba.eligible_purposes({'shop': 'bakery'}, mapping) == ['shopping']
    assert bba.eligible_purposes({'shop': 'bakery', 'disused': 'yes'}, mapping) == []
    assert bba.eligible_purposes({'amenity': 'school'}, mapping) == ['education']
    rng = np.random.default_rng(3)
    near = dict(x_m=10.0, y_m=0.0, weight=1.0)
    far = dict(x_m=50000.0, y_m=0.0, weight=1.0)
    picks = [bba.select_destination(rng, np.array([0.0, 0.0]), [near, far], 500.0) for _ in range(20)]
    assert all(p is near for p in picks)
    with pytest.raises(ValueError):
        bba.select_destination(rng, np.array([0.0, 0.0]), [near], 0.0)
