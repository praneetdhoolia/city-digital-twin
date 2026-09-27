"""`extract_metrics.trip_geometry`'s `road_speed` block: the road-vehicle
speed tail of every traveller's trips, the slow-trip shares of trips and of
travel time, the slow trips by departure hour, and the day's stuck agents per
mode from the legHistogram.

A synthetic finished run: a trips table, a config snapshot carrying the two
values trip_geometry reads, and one legHistogram.
"""
import gzip
import json

import pytest

import extract_metrics as em

HEADER = 'person;trip_id;main_mode;dep_time;trav_time;traveled_distance;euclidean_distance'
TRIPS = [
    # car: 36 km/h, 7.2 km/h, 12 km/h, 60 km/h
    'a;a_1;car;08:10:00;00:10:00;6000;5000',
    'b;b_1;car;08:30:00;00:50:00;6000;5000',
    'c;c_1;car;17:05:00;00:30:00;6000;5000',
    'd;d_1;car;09:00:00;00:06:00;6000;5000',
    # excluded: zero time, zero distance
    'e;e_1;car;09:00:00;00:00:00;6000;5000',
    'f;f_1;car;09:00:00;00:05:00;0;0',
    # not a road vehicle
    'g;g_1;walk;09:00:00;00:30:00;2000;1800',
    'h;h_1;ride;09:00:00;00:10:00;6000;5000',
    # truck: one trip at 30 km/h
    'i;i_1;truck;10:00:00;00:20:00;10000;9000',
]
HISTOGRAM = ('time\ttime\tdepartures_all\tstuck_all\tstuck_car\tstuck_truck\n'
             '00:00:00\t0\t5\t0\t0\t0\n'
             '08:00:00\t28800\t7\t3\t2\t1\n'
             '09:00:00\t32400\t2\t1\t1\t0\n')


@pytest.fixture
def geometry(tmp_path):
    (tmp_path / 'output' / 'ITERS' / 'it.20').mkdir(parents=True)
    with gzip.open(tmp_path / 'output' / 'output_trips.csv.gz', 'wt', encoding='utf-8') as fh:
        fh.write('\n'.join([HEADER] + TRIPS) + '\n')
    (tmp_path / 'output' / 'ITERS' / 'it.20' / '20.legHistogram.txt').write_text(
        HISTOGRAM, encoding='utf-8')
    (tmp_path / '_config.json').write_text(json.dumps({'values': {
        'B.activity.short_trip_band_km': 2.0, 'B.activity.detour_factor': 1.3}}),
        encoding='utf-8')
    return em.trip_geometry(str(tmp_path), {}, histogram_iteration=20)


def test_car_speed_tail_and_slow_shares(geometry):
    car = geometry['road_speed']['by_mode']['car']
    assert car['trips'] == 4
    assert car['speed_kmh'] == {'p5': 7.2, 'p10': 7.2, 'p25': 12.0, 'p50': 36.0,
                                'p75': 60.0, 'p90': 60.0}
    assert car['share_under_10_kmh_pct'] == 25.0
    assert car['share_under_15_kmh_pct'] == 50.0
    # 50 + 30 of 96 minutes are in trips under 15 km/h
    assert car['time_share_under_15_kmh_pct'] == pytest.approx(100 * 80 / 96, abs=0.01)
    assert car['mean_time_min'] == 24.0
    assert car['mean_time_min_at_least_15_kmh'] == 8.0
    assert car['under_15_kmh_by_departure_hour'] == {'8': 1, '17': 1}


def test_only_road_vehicles_are_read(geometry):
    assert sorted(geometry['road_speed']['by_mode']) == ['car', 'truck']
    assert geometry['road_speed']['by_mode']['truck']['speed_kmh']['p50'] == 30.0


def test_stuck_comes_from_the_leg_histogram(geometry):
    assert geometry['road_speed']['stuck_by_mode'] == {'all': 4, 'car': 3, 'truck': 1}


def test_existing_keys_are_unchanged(geometry):
    assert {'geography', 'by_mode', 'short_trips', 'note'} <= set(geometry)


def test_no_histogram_is_none(tmp_path):
    assert em.leg_histogram_stuck(str(tmp_path), 7) is None


def test_bands_and_ranks():
    assert [em.slow_band(v) for v in (9.99, 10, 14.99, 15)] == [
        'under_10_kmh', '10_to_15_kmh', '10_to_15_kmh', 'at_least_15_kmh']
    assert em.rank_percentiles([4, 1, 3, 2], (0, 50, 99)) == {'p0': 1, 'p50': 3, 'p99': 4}
    assert em.rank_percentiles([], (50,)) == {}
    assert em.trip_seconds('25:01:02') == 90062
