"""Linked trips derived from experienced plans, and one iteration's mode share.

`iteration_trips.derive` is what lets a twelve-mode reading exist at an
iteration that wrote experienced plans but no trips table; the gate readers
then hand its rows to `measure_iteration_modes.mode_share_at`. Both sit on the
result path, so the rules they reproduce from MATSim are pinned here on a
hand-written experienced-plans file:

  * a trip ends at every activity whose type does NOT end in `interaction`;
  * every declared transit mode folds to `pt`, then walk legs drop out and the
    one remaining mode is the main mode - more than one is flagged ambiguous;
  * only the selected plan is read, and a plan WITHOUT a `selected` stamp is
    the selected one (MATSim's writer does not always stamp it);
  * the distance is the sum of the legs' route distances, and a pt leg's
    in-vehicle metres are kept per boarded route's submode;
  * a pt route the schedule does not know is counted, not guessed.

`mode_share_at` then counts every trip, the target LGA's trips by home LGA,
and persons with no home LGA - on rows passed in, so no run is read.
"""
import gzip
import json

import pytest

import extract_metrics as em
import iteration_trips as itr
import measure_iteration_modes as mim

ROUTE_MODE = {('L1', 'R1'): 'bus', ('L2', 'R2'): 'rail'}


def _pt(line, route, dist):
    return ('<leg mode="bus"><route type="default_pt" distance="%s">%s</route></leg>'
            % (dist, json.dumps({'transitLineId': line, 'transitRouteId': route})))


def _leg(mode, dist):
    return '<leg mode="%s"><route type="generic" distance="%s"/></leg>' % (mode, dist)


def _act(typ):
    return '<activity type="%s" x="0" y="0"/>' % typ


PLANS = ''.join([
    '<?xml version="1.0" encoding="utf-8"?><population>',
    # person 1: unstamped plan - walk / bus / walk to work, then drive home
    '<person id="1"><plan>',
    _act('home'), _leg('walk', 100), _act('pt interaction'), _pt('L1', 'R1', 2000),
    _act('pt interaction'), _leg('walk', 50), _act('work'),
    _leg('car', 5000), _act('home'),
    '</plan></person>',
    # person 2: an unselected car plan is ignored; the selected walk plan counts
    '<person id="2"><plan selected="no">', _act('home'), _leg('car', 9999),
    _act('shop'), '</plan><plan selected="yes">', _act('home'),
    _leg('walk', 300), _act('shop'), '</plan></person>',
    # person 3: two non-walk modes in one trip - ambiguous, first one wins
    '<person id="3"><plan selected="yes">', _act('home'), _leg('car', 1000),
    _act('car interaction'), _leg('bike', 400), _act('work'), '</plan></person>',
    # person 4: a pt route the schedule does not carry
    '<person id="4"><plan>', _act('home'), _pt('LX', 'RX', 700), _act('work'),
    '</plan></person>',
    '</population>'])


@pytest.fixture
def run_dir(tmp_path):
    (tmp_path / 'config.xml').write_text(
        '<config><module name="transit">'
        '<param name="transitModes" value="pt, bus,rail" /></module></config>',
        encoding='utf-8')
    it = tmp_path / 'output' / 'ITERS' / 'it.5'
    it.mkdir(parents=True)
    with gzip.open(it / '5.experienced_plans.xml.gz', 'wt', encoding='utf-8') as fh:
        fh.write(PLANS)
    (tmp_path / 'output' / 'ITERS' / 'it.10').mkdir()     # no plans written
    return str(tmp_path)


def test_transit_modes_are_read_from_the_run_config(run_dir, tmp_path):
    assert itr.transit_modes(run_dir) == {'pt', 'bus', 'rail'}
    other = tmp_path / 'other'
    other.mkdir()
    (other / 'config.xml').write_text('<config/>', encoding='utf-8')
    assert itr.transit_modes(str(other)) == set()


def test_iterations_with_plans_lists_only_written_iterations(run_dir):
    assert itr.iterations_with_plans(run_dir) == [5]
    assert itr.plans_path(run_dir, 10) is None
    assert not itr.trips_table_exists(run_dir, 5)


@pytest.mark.parametrize('legs, fold, expected', [
    (['walk'], set(), ('walk', False)),
    (['walk', 'non_network_walk', 'transit_walk'], set(), ('walk', False)),
    (['walk', 'car', 'walk'], set(), ('car', False)),
    (['bus'], {'bus'}, ('pt', False)),
    (['walk', 'bus', 'walk', 'rail', 'walk'], {'bus', 'rail'}, ('pt', False)),
    (['car', 'bike'], set(), ('car', True)),
])
def test_main_mode_rule(legs, fold, expected):
    assert itr.main_mode(legs, fold) == expected


def test_derive_splits_linked_trips_from_the_selected_plan(run_dir):
    trips, unknown = itr.derive(run_dir, 5, route_mode=ROUTE_MODE)
    got = [(t.person, t.trip_id, t.main_mode, t.traveled_distance, t.ambiguous)
           for t in trips]
    assert got == [
        ('1', '1_1', 'pt', 2150.0, False),
        ('1', '1_2', 'car', 5000.0, False),
        ('2', '2_1', 'walk', 300.0, False),
        ('3', '3_1', 'car', 1400.0, True),
        ('4', '4_1', 'pt', 700.0, False),
    ]
    assert unknown == 1
    # in-vehicle metres by the boarded route's submode; the unknown route has none
    assert itr.submodes_by_trip(trips) == {('1', '1_1'): {'bus': 2000.0}}


def test_derive_refuses_an_iteration_without_plans(run_dir):
    with pytest.raises(SystemExit):
        itr.derive(run_dir, 10, route_mode=ROUTE_MODE)


def test_as_trip_rows_carries_the_trips_table_columns(run_dir):
    trips, _ = itr.derive(run_dir, 5, route_mode=ROUTE_MODE)
    rows = list(itr.as_trip_rows(trips))
    assert rows[0] == {'person': '1', 'trip_id': '1_1', 'main_mode': 'pt',
                       'traveled_distance': '2150'}
    assert [r['main_mode'] for r in rows] == ['pt', 'car', 'walk', 'car', 'pt']


# --------------------------------------------------------------------------
# measure_iteration_modes.mode_share_at
# --------------------------------------------------------------------------
def test_mode_share_at_counts_residents_and_the_target_lga():
    target = em.TARGET_LGA
    rows = [{'person': '1', 'main_mode': 'car'},
            {'person': '1', 'main_mode': 'pt'},
            {'person': '2', 'main_mode': 'car'},
            {'person': '2', 'main_mode': 'walk'},
            {'person': '3', 'main_mode': 'car'},      # another LGA
            {'person': '4', 'main_mode': 'bike'}]     # no home LGA
    person_lga = {'1': target, '2': target, '3': 'Elsewhere-' + str(target)}
    share = mim.mode_share_at(None, None, person_lga, rows=rows)
    assert share['all_residents_trips'] == 6
    one_in_six = round(100.0 / 6, 4)             # the reader rounds to 4 places
    assert share['all_residents_pct'] == {
        'bike': one_in_six, 'car': 50.0, 'pt': one_in_six, 'walk': one_in_six}
    assert share['target_lga_trips'] == 4
    assert share['target_lga_counts'] == {'car': 2, 'pt': 1, 'walk': 1}
    assert share['target_lga_pct'] == {'car': 50.0, 'pt': 25.0, 'walk': 25.0}
    assert share['persons_without_home_lga'] == 1
    # the percentages come back in mode order, as fit.score_mode_share reads them
    assert list(share['all_residents_pct']) == sorted(share['all_residents_pct'])


def test_mode_share_at_on_no_target_trips_is_empty_not_zero():
    share = mim.mode_share_at(None, None, {}, rows=[{'person': '9', 'main_mode': 'car'}])
    assert share['target_lga_pct'] == {}
    assert share['target_lga_trips'] == 0
    assert share['persons_without_home_lga'] == 1


def test_trip_rows_falls_back_to_the_experienced_plans(run_dir, monkeypatch):
    # no trips table under it.5, so the rows are derived from its plans; the
    # schedule lookup is the run's, stood in for here
    monkeypatch.setattr(em, 'transit_route_modes', lambda _run: dict(ROUTE_MODE))
    rows, source = mim.trip_rows(run_dir, 5)
    assert source == 'experienced plans (derived)'
    assert len(rows) == 5
    share = mim.mode_share_at(run_dir, 5, {'1': em.TARGET_LGA})
    assert share['target_lga_counts'] == {'pt': 1, 'car': 1}
    assert share['persons_without_home_lga'] == 3


def test_trip_rows_refuses_an_iteration_with_neither_source(run_dir):
    with pytest.raises(SystemExit):
        mim.trip_rows(run_dir, 10)
