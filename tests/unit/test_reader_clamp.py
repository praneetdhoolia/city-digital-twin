"""No reader quotes a stopped arm past its record (sixteenth report).

A stopped arm is citable at its record's `reached_iteration` and nowhere past
it (GOAL.md, 9.143), and MATSim writes an iteration's tables inside the
iterationEnds listeners, so a trips table can exist on disk for an iteration
the record says the run never completed. The clamp used to live in the board
and in report_mode_ridership alone; it lives in `iteration_reading` now, under
every reader that asks it for a table. The fixture: three persons, trips
tables at iterations 1 and 2, a `_run.json` saying the run stopped at 1.
"""
import gzip
import json
import os

import pytest

import iteration_reading as reading

TRIPS = ('person;trip_id;main_mode;traveled_distance;trav_time;dep_time;start_link;end_link;end_activity_type\n'
         'p1;p1_1;car;5000;00:10:00;08:00:00;a;b;work\n'
         'p2;p2_1;walk;800;00:12:00;08:30:00;a;c;shop\n'
         'p3;p3_1;pt;12000;00:40:00;07:45:00;d;b;work\n')


@pytest.fixture
def stopped_run(tmp_path):
    run = tmp_path / '20260101T000000_2it_1pct'
    for it in (1, 2):
        d = run / 'output' / 'ITERS' / ('it.%d' % it)
        d.mkdir(parents=True)
        with gzip.open(str(d / ('%d.trips.csv.gz' % it)), 'wt', encoding='utf-8') as fh:
            fh.write(TRIPS)
        with gzip.open(str(d / ('%d.experienced_plans.xml.gz' % it)), 'wt', encoding='utf-8') as fh:
            fh.write('<population/>\n')
    (run / '_run.json').write_text(json.dumps(dict(
        completion='stopped_by_operator', reached_iteration=1, iterations=2, rc=0)), encoding='utf-8')
    reading.clear()
    yield str(run)
    reading.clear()


def test_the_record_sets_the_ceiling(stopped_run):
    assert reading.citable_ceiling(stopped_run) == 1
    assert reading.iterations_with(stopped_run, 'trips') == [1, 2]
    assert reading.citable_iterations(stopped_run, 'trips') == [1]
    assert reading.citable_iterations(stopped_run, iterations=[1, 2]) == [1]


def test_a_finished_run_has_no_ceiling(stopped_run):
    with open(os.path.join(stopped_run, '_run.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(completion='ran_to_last_iteration', reached_iteration=2), fh)
    assert reading.citable_ceiling(stopped_run) is None
    assert reading.citable_iterations(stopped_run, 'trips') == [1, 2]
    assert len(reading.table(stopped_run, 'trips', 2)) == 3


def test_the_table_reader_refuses_iteration_2_and_reads_1(stopped_run):
    with pytest.raises(SystemExit, match='past this run'):
        reading.table(stopped_run, 'trips', 2)
    rows = reading.table(stopped_run, 'trips', 1)
    assert [r['person'] for r in rows] == ['p1', 'p2', 'p3']


def test_a_projection_decodes_only_the_columns_asked(stopped_run):
    rows = reading.table(stopped_run, 'trips', 1, columns=('person', 'main_mode', 'missing'))
    assert rows == [{'person': 'p1', 'main_mode': 'car'}, {'person': 'p2', 'main_mode': 'walk'},
                    {'person': 'p3', 'main_mode': 'pt'}]
    # a full decode already cached serves a projection; a projection never serves a wider read
    reading.clear()
    full = reading.table(stopped_run, 'trips', 1)
    assert reading.table(stopped_run, 'trips', 1, columns=('trip_id',)) == [{'trip_id': r['trip_id']} for r in full]
    assert reading.table(stopped_run, 'trips', 1) is full


def test_mode_by_demographics_refuses_2_and_reads_1(stopped_run):
    import mode_by_demographics as mbd
    with pytest.raises(SystemExit, match='past this run'):
        mbd.trips_rows(stopped_run, 2)
    assert len(mbd.trips_rows(stopped_run, 1)) == 3
    # with no close-out metrics and no final output, the newest CITABLE iteration is read
    assert mbd.read_at_iteration(stopped_run) == 1
    # a close-out that recorded iteration 2 is refused the same way
    with open(os.path.join(stopped_run, '_metrics.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(read_at_iteration=2), fh)
    with pytest.raises(SystemExit, match='past this run'):
        mbd.trips_rows(stopped_run, mbd.read_at_iteration(stopped_run))


def test_measure_demographic_modes_refuses_2_and_reads_1(stopped_run):
    import measure_demographic_modes as mdm
    pop = {'p1': ('25_34', 'M', 'employed', '1'), 'p3': ('25_34', 'F', 'employed', '0')}
    with pytest.raises(SystemExit, match='past this run'):
        mdm.tabulate_trips(stopped_run, pop, 2)
    all_t, com_t, totals, com_totals, unmatched = mdm.tabulate_trips(stopped_run, pop, 1)
    assert dict(totals) == {'car': 1, 'pt': 1} and unmatched == 1
    assert dict(com_totals) == {'car': 1, 'pt': 1}


def test_transit_link_delays_refuses_2_and_reads_1(stopped_run, monkeypatch):
    import transit_link_delays as tld
    with pytest.raises(SystemExit, match='past this run'):
        tld.analyse(stopped_run, 2, 5)
    # --access reads the trips table through the same clamp
    net = {'a': dict(capacity=100.0, length=10.0, freespeed=10.0, lanes=1.0, to='x'),
           'b': dict(capacity=100.0, length=10.0, freespeed=10.0, lanes=1.0, to='y')}
    trips = reading.table(stopped_run, 'trips', 1, columns=tld.ACCESS_COLUMNS)
    report = tld.access_load(trips, net, 0.01, 5)
    assert report['road_vehicle_trips'] == 1
    with pytest.raises(SystemExit, match='past this run'):
        reading.table(stopped_run, 'trips', 2, columns=tld.ACCESS_COLUMNS)


def test_iteration_trips_refuses_2_and_lists_1(stopped_run):
    import iteration_trips as itr
    assert itr.iterations_with_plans(stopped_run) == [1, 2]
    assert itr.citable_plans_iterations(stopped_run) == [1]
    with pytest.raises(SystemExit, match='past this run'):
        itr.derive(stopped_run, 2)


def test_report_mode_ridership_lists_only_citable_iterations(stopped_run):
    import report_mode_ridership as rmr
    assert rmr.readable_iterations(stopped_run) == [1]


def test_corridor_market_resolves_the_run_through_the_store(monkeypatch, capsys):
    """corridor_market reads the demand INPUT (B2 trips), not an iteration, so
    it has no iteration to clamp; what it shares with the readers is the one
    `--run` resolver (results_store.resolve_or_die) that replaced five pasted
    copies, and a run the store does not know is refused before any read."""
    import sys
    import corridor_market as cm
    monkeypatch.setattr(sys, 'argv', ['corridor_market.py', '--run', 'no_such_run_20990101',
                                      '--mode', 'tram', '--radius-m', '400'])
    with pytest.raises(SystemExit):
        cm.main()
