"""`report_mode_ridership.py --stations`: heavy-rail boardings split into
station ENTRIES and rail-to-rail TRANSFERS, each entry labelled by its access,
its traveller's car availability and subpopulation, scaled by the fraction.

A synthetic legs table: one walk-to-rail trip, one bus-to-rail trip, one
rail-to-rail change, one long walk to rail, and a bus-only trip.
"""
import gzip

import pytest

import report_mode_ridership as rmr

HEADER = 'person;trip_id;mode;distance;access_stop_id;egress_stop_id;transit_line;transit_route'
LEGS = [
    # p1: walk 400 m, rail at Hamilton, walk
    'p1;p1_1;walk;400;;;;',
    'p1;p1_1;rail;9000;h1;n1;CCN;r1',
    'p1;p1_1;walk;100;;;;',
    # p2: walk, bus to Broadmeadow, rail from Broadmeadow (entry via bus)
    'p2;p2_1;walk;200;;;;',
    'p2;p2_1;bus;3000;b1;bm1;B10;rb',
    'p2;p2_1;walk;50;;;;',
    'p2;p2_1;rail;5000;bm1;n1;CCN;r1',
    # p3: walk 2.5 km in two legs, rail at Hamilton, change at Broadmeadow
    'p3;p3_1;non_network_walk;1000;;;;',
    'p3;p3_1;walk;1500;;;;',
    'p3;p3_1;rail;2000;h1;bm1;CCN;r1',
    'p3;p3_1;walk;30;;;;',
    'p3;p3_1;rail;8000;bm1;x1;HUN;r2',
    # p4: bus only - no rail boarding
    'p4;p4_1;walk;100;;;;',
    'p4;p4_1;bus;2000;b1;b2;B10;rb',
]
ROUTE_MODE = {('CCN', 'r1'): 'rail', ('HUN', 'r2'): 'rail', ('B10', 'rb'): 'bus'}
STOP_NAME = {'h1': 'Hamilton Station Platform 1', 'bm1': 'Broadmeadow Station Platform 2',
             'n1': 'Newcastle Interchange', 'x1': 'Maitland Station', 'b1': 'Bus stop',
             'b2': 'Bus stop 2'}
PERSONS = {'p1': {'subpopulation': 'person', 'carAvail': 'always'},
           'p2': {'subpopulation': 'person', 'carAvail': 'never'},
           'p3': {'subpopulation': 'visitor'},
           'p4': {'subpopulation': 'person', 'carAvail': 'always'}}
TARGETS = {'hamilton': (10.0, 12.0), 'broadmeadow': (4.0, 5.0), 'kotara': (1.0, 1.2)}


@pytest.fixture
def doc(tmp_path):
    it_dir = tmp_path / 'output' / 'ITERS' / 'it.10'
    it_dir.mkdir(parents=True)
    with gzip.open(it_dir / '10.legs.csv.gz', 'wt', encoding='utf-8') as fh:
        fh.write('\n'.join([HEADER] + LEGS) + '\n')
    return rmr.station_entries(str(tmp_path), 10, fraction=0.25, targets=TARGETS,
                               route_mode=ROUTE_MODE, stop_name=STOP_NAME,
                               persons=PERSONS)


def _row(doc, st):
    return next(r for r in doc['stations'] if r['station'] == st)


def test_entries_and_transfers_are_split_and_scaled(doc):
    ham, bm = _row(doc, 'hamilton'), _row(doc, 'broadmeadow')
    assert (ham['entries'], ham['transfers']) == (8.0, 0.0)      # p1 + p3, x4
    assert (bm['entries'], bm['transfers']) == (4.0, 4.0)        # p2 entry, p3 change
    assert ham['entries_to_target'] == pytest.approx(8.0 / 12.0, abs=1e-3)
    kot = _row(doc, 'kotara')
    assert kot['entries'] == 0 and kot['disclosed']


def test_each_entry_carries_its_access_car_and_subpopulation(doc):
    ham, bm = _row(doc, 'hamilton'), _row(doc, 'broadmeadow')
    assert ham['access'] == {'walk <1 km': 4.0, 'walk 2-5 km': 4.0}
    assert bm['access'] == {'from bus': 4.0}
    assert ham['car_availability'] == {'always': 4.0, '(none)': 4.0}
    assert ham['subpopulation'] == {'person': 4.0, 'visitor': 4.0}


def test_totals_split_disclosed_from_undisclosed(doc):
    t = doc['totals']
    assert t['disclosed']['entries'] == 12.0
    assert t['disclosed']['transfers'] == 4.0
    assert t['disclosed']['target_per_weekday'] == pytest.approx(18.2)
    assert t['undisclosed']['stations'] == 0
    assert t['all']['access']['from bus'] == 4.0


def test_the_table_prints(doc, capsys):
    rmr.print_station_entries(doc)
    out = capsys.readouterr().out
    assert 'hamilton' in out and 'TOTAL disclosed' in out


def test_a_run_without_a_fraction_is_refused(tmp_path):
    with pytest.raises(SystemExit, match='REFUSED'):
        rmr.station_entries(str(tmp_path), 10, targets={}, route_mode={},
                            stop_name={}, persons={})


def test_rail_legs_read_distance_shapes_and_pairs(doc):
    r = doc['rail_legs']
    # rail legs of 9, 5, 2 and 8 km; the lower nearest rank of each percent
    assert (r['legs'], r['legs_per_day']) == (4, 16.0)
    assert r['in_vehicle_km'] == {'p10': 2.0, 'p25': 5.0, 'p50': 8.0, 'p75': 9.0, 'p90': 9.0}
    assert (r['share_under_3_km_pct'], r['share_under_5_km_pct']) == (25.0, 25.0)
    # the bus-only trip has no shape; each rail trip's boarded submodes in order
    assert {s['shape']: s['trips'] for s in r['trip_shapes']} == {
        'rail': 1, 'bus > rail': 1, 'rail > rail': 1}
    pairs = {(p['board'], p['alight']): p['per_day'] for p in r['top_station_pairs']}
    assert pairs == {('hamilton', 'newcastle interchange'): 4.0,
                     ('broadmeadow', 'newcastle interchange'): 4.0,
                     ('hamilton', 'broadmeadow'): 4.0,
                     ('broadmeadow', 'maitland'): 4.0}


def test_the_rail_legs_print(doc, capsys):
    rmr.print_station_entries(doc)
    out = capsys.readouterr().out
    assert 'RAIL LEGS  4 (16 per day)' in out and 'bus > rail' in out
    assert 'hamilton -> broadmeadow' in out


def test_access_bands():
    assert [rmr.access_band(k) for k in (0.2, 1.0, 4.99, 5.0)] == [
        'walk <1 km', 'walk 1-2 km', 'walk 2-5 km', 'walk >=5 km']
