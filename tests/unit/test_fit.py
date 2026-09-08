"""Scoring, and what it refuses to score, on synthetic metrics.

`src/calibrate/fit.py` is the deliverable that states how well the model
reproduces observation, and it had no test at all until the whole-package check
grew one: that is how issue 19 survived - a defect that silently IMPROVED the
reported fit by dropping the stations where the model failed hardest, in code
nothing exercised. Two rules are asserted here rather than assumed:

  * a modelled ZERO is a result and is scored at -100%; only a target with no
    modelled counterpart at all is unscorable, and the two cases carry
    different reasons;
  * every target is scored or explained, and every statistic names the target
    ids it was computed over.

The metrics are synthetic dicts, the targets are synthetic rows: no run, no
`results/`, no package. The HTS category labels come from the module (which
reads them from the active city's own adapter), so no survey label is typed
here.
"""
import pytest

import fit


CAR = fit.MODE_TO_HTS['car']
RIDE = fit.MODE_TO_HTS['ride']
PT = fit.MODE_TO_HTS['pt']
WALK = fit.MODE_TO_HTS['walk']
BIKE = fit.MODE_TO_HTS['bike']
VINTAGE = fit.BASE_YEAR_HTS


# --------------------------------------------------------------------------
# scale_error: the deliberate asymmetry
# --------------------------------------------------------------------------
def test_a_modelled_zero_is_scored_and_an_observed_zero_is_not():
    scored = fit.scale_error(0, 100.0)
    assert scored is not None and scored['pct_error'] == -100.0
    # a zero denominator has no percentage; the asymmetry is deliberate
    assert fit.scale_error(5.0, 0) is None
    assert fit.scale_error(None, 100.0) is None


def test_scale_error_reports_both_sides_and_the_signed_error():
    e = fit.scale_error(120.0, 100.0)
    assert (e['modelled'], e['observed']) == (120.0, 100.0)
    assert e['abs_error'] == 20.0 and e['pct_error'] == 20.0


# --------------------------------------------------------------------------
# score_counts (issue 19): a modelled zero vs a station that resolves to nothing
# --------------------------------------------------------------------------
def count_target(target_id, key, value):
    return dict(target_id=target_id, metric='road_aadt', period='2024',
                note='station_key=%s;something else' % key, value=str(value),
                split='calibration')


def station(key, modelled):
    return dict(station_key=key, road_name='a fixture road', links='1',
                matched_by='name_and_proximity', max_distance_m=10.0,
                modelled_vehicles=modelled)


CORRECTIONS = dict(heavy_vehicle_share=dict(value=0.1))


def score_counts(targets, stations):
    out = dict(unscorable=[])
    block = fit.score_counts(targets, dict(counts=dict(stations=stations)),
                             CORRECTIONS, out)
    return block, out


def test_a_modelled_zero_is_scored_at_minus_one_hundred_not_dropped():
    targets = [count_target('R1', 'k1', 10000)]
    block, out = score_counts(targets, [station('k1', 0)])
    assert [e['target_id'] for e in block['errors']] == ['R1']
    assert block['errors'][0]['pct_error'] == -100.0
    assert block['errors'][0]['modelled_zero'] is True
    assert out['unscorable'] == [], (
        'dropping it would flatter every aggregate by removing the stations '
        'where the model fails hardest')


def test_a_modelled_zero_is_named_rather_than_buried_in_the_aggregate():
    targets = [count_target('R1', 'k1', 10000),
               count_target('R2', 'k2', 20000)]
    block, _ = score_counts(targets, [station('k1', 0), station('k2', 18000)])
    assert block['modelled_zero_stations'] == ['R1']


def test_a_station_that_resolves_to_no_link_is_unscorable_in_its_own_words():
    targets = [count_target('R1', 'k1', 10000)]
    block, out = score_counts(targets, [])
    assert block['errors'] == []
    assert len(out['unscorable']) == 1
    reason = out['unscorable'][0]['reason']
    assert 'did not resolve to any link' in reason
    assert 'routes no traffic' not in reason, (
        'the two causes must not share one reason string - an earlier cut '
        'emitted the unresolved reason for a modelled zero as well')


def test_the_observed_count_is_put_on_a_light_vehicle_basis():
    # the model has no freight, so the all-classes observation is corrected by
    # the station's heavy share - here the assumed default
    targets = [count_target('R1', 'k1', 10000)]
    block, _ = score_counts(targets, [station('k1', 9000)])
    e = block['errors'][0]
    assert e['observed'] == 9000.0 and e['heavy_share'] == 0.1
    assert e['heavy_share_source'] == 'assumed'
    assert e['pct_error'] == 0.0


def test_the_counts_block_names_its_targets_and_reconciles():
    targets = [count_target('R%d' % i, 'k%d' % i, 10000 + i)
               for i in range(1, 5)]
    block, out = score_counts(targets, [station('k1', 9000),
                                        station('k2', 0)])
    assert block['n'] == len(block['targets']) == 2
    unscorable = [u for u in out['unscorable'] if u['metric'] == 'road_aadt']
    assert block['n'] + len(unscorable) == len(targets), (
        'no target is silently neither scored nor explained')


def test_an_empty_counts_block_reports_no_statistic_at_all():
    block, _ = score_counts([], [])
    assert block == dict(targets=[], n=0, errors=[])


def test_the_counts_aggregates_are_computed_over_the_scored_targets():
    targets = [count_target('R1', 'k1', 10000),
               count_target('R2', 'k2', 10000)]
    # observed light = 9000 each; modelled 9900 and 8100 -> +/-10%
    block, _ = score_counts(targets, [station('k1', 9900),
                                      station('k2', 8100)])
    assert block['mean_pct_error'] == 0.0
    assert block['mean_abs_pct_error'] == 10.0
    assert block['rmse'] == 900.0


# --------------------------------------------------------------------------
# score_mode_share: the folds, and the categories nothing corresponds to
# --------------------------------------------------------------------------
def share_target(target_id, category, value, period=None):
    return dict(target_id=target_id, metric='hts_mode_share',
                period=period or VINTAGE, note=category, value=str(value),
                split='calibration')


def score_mode_share(targets, shares):
    out = dict(unscorable=[])
    block = fit.score_mode_share(
        targets, dict(mode_share=dict(target_lga_pct=shares)), out)
    return block, out


def test_the_car_row_is_compared_against_car_plus_motorbike():
    # the survey's driver category contains motorcyclists, and the model carves
    # motorbike out of car-driver demand: comparing car alone under-reads the
    # model by exactly the declared carve
    block, _ = score_mode_share([share_target('M1', CAR, 60.0)],
                                {'car': 55.0, 'motorbike': 5.0})
    e = block['errors'][0]
    assert e['matsim_mode'] == 'car+motorbike'
    assert e['modelled'] == 60.0 and e['abs_error'] == 0.0


def test_the_other_row_is_compared_against_bike_plus_taxi_once_taxi_exists():
    block, _ = score_mode_share([share_target('M2', BIKE, 3.0)],
                                {'bike': 2.0, 'taxi': 1.0})
    assert block['errors'][0]['matsim_mode'] == 'bike+taxi'
    assert block['errors'][0]['modelled'] == 3.0


def test_a_mode_with_no_taxi_in_the_run_is_compared_on_bike_alone():
    block, _ = score_mode_share([share_target('M2', BIKE, 3.0)],
                                {'bike': 2.0})
    assert block['errors'][0]['matsim_mode'] == 'bike'
    assert block['errors'][0]['modelled'] == 2.0


def test_an_hts_category_with_no_matsim_mode_is_unscorable_with_a_reason():
    block, out = score_mode_share(
        [share_target('M9', 'Walk linked', 0.0)], {'walk': 15.0})
    assert block['n'] == 0
    assert len(out['unscorable']) == 1
    assert out['unscorable'][0]['target_id'] == 'M9'
    assert out['unscorable'][0]['reason']


def test_a_different_survey_vintage_is_unscorable_rather_than_scored():
    targets = [share_target('M1', CAR, 60.0),
               share_target('M8', PT, 12.0, period='2016/17')]
    block, out = score_mode_share(targets, {'car': 60.0, 'pt': 6.0})
    assert block['targets'] == ['M1']
    assert [u['target_id'] for u in out['unscorable']] == ['M8']
    assert '2016/17' in out['unscorable'][0]['reason']


def test_the_mode_share_statistic_names_its_targets_and_averages_over_them():
    targets = [share_target('M1', CAR, 60.0), share_target('M3', PT, 10.0),
               share_target('M4', WALK, 15.0)]
    block, _ = score_mode_share(targets, {'car': 62.0, 'pt': 8.0, 'walk': 15.0})
    assert block['targets'] == ['M1', 'M3', 'M4'] and block['n'] == 3
    # rounded to three decimals by fit.py, which is what the report prints
    assert block['mean_abs_pp'] == round((2.0 + 2.0 + 0.0) / 3, 3)


def test_a_mode_the_run_never_produced_is_scored_as_zero_not_skipped():
    block, out = score_mode_share([share_target('M5', RIDE, 8.0)], {'car': 60.0})
    assert block['errors'][0]['modelled'] == 0.0
    assert block['errors'][0]['pct_error'] == -100.0
    assert out['unscorable'] == []


# --------------------------------------------------------------------------
# account_for_the_rest: no silent third case
# --------------------------------------------------------------------------
def test_every_remaining_target_is_given_a_reason():
    targets = [dict(target_id='X1', metric='lr_scheduled_runtime',
                    period='2025', note='a fixture', value='12.0',
                    split='calibration'),
               dict(target_id='X2', metric='an_unmapped_metric',
                    period='2025', note='a fixture', value='1.0',
                    split='calibration')]
    out = dict(unscorable=[], mode_share=dict(targets=[]),
               patronage=dict(targets=[]), counts=dict(targets=[]))
    fit.account_for_the_rest(targets, out)
    listed = {u['target_id']: u['reason'] for u in out['unscorable']}
    assert set(listed) == {'X1', 'X2'}
    assert 'schedule INPUT' in listed['X1']
    # a metric with no recorded reason says so, rather than looking accounted for
    assert 'gap in fit.py' in listed['X2']


def test_a_target_already_scored_is_not_listed_twice():
    targets = [dict(target_id='X1', metric='road_aadt', period='2024',
                    note='station_key=k1', value='1.0', split='calibration')]
    out = dict(unscorable=[], mode_share=dict(targets=[]),
               patronage=dict(targets=[]), counts=dict(targets=['X1']))
    fit.account_for_the_rest(targets, out)
    assert out['unscorable'] == []


# --------------------------------------------------------------------------
# the constraints, which are reported beside the fit and never scored
# --------------------------------------------------------------------------
def test_the_occupancy_constraint_folds_motorbike_into_the_driver_denominator():
    c4 = dict(passenger_per_driver=dict(value=0.2, sweep=[0.15, 0.25]))
    o = fit.score_occupancy(
        dict(mode_share=dict(target_lga_pct={'car': 55.0, 'motorbike': 5.0,
                                             'ride': 12.0})), c4)
    assert o['modelled_passenger_per_driver'] == 0.2
    assert o['inside_observed_range'] is True
    assert o['modelled_vehicle_occupancy'] == 1.2
    assert 'not counted in any fit statistic' in o['note']


def test_the_occupancy_constraint_is_none_when_the_run_has_no_drivers():
    c4 = dict(passenger_per_driver=dict(value=0.2, sweep=[0.15, 0.25]))
    assert fit.score_occupancy(
        dict(mode_share=dict(target_lga_pct={'ride': 1.0})), c4) is None


# --------------------------------------------------------------------------
# the GOAL's twelve modes: the objective the goal actually states
#
# These lock in the change that made the objective and the gate the same
# statistic. The loop previously minimised `mode_share.mean_abs_pp` - a MEAN
# over five FOLDED survey categories in percentage points - while GOAL.md
# requirement 7 is a MAXIMUM over twelve UNFOLDED modes in relative per cent.
# Measured on a real run at the moment of the change: the folded objective read
# 11.18 pp on a model whose heavy rail was +471.7%.
# --------------------------------------------------------------------------
class _StubReader:
    """Stands in for src/analyse/report_mode_ridership, whose real `report`
    parses a run's trips table. The contract under test is the one this module
    depends on: `report()` fills `LAST['rows']`, one dict per mode, and a row
    the reader refuses to score on the target's own ground carries
    `deviation_pct=None`."""

    GATE_PASS_PCT = 10.0
    GATE_STOP_PCT = 20.0

    def __init__(self, rows):
        self.LAST = {'rows': rows}

    def report(self, run_dir, iteration):
        return []


def _row(mode, dev, flag='ok', modelled=1.0, target=1.0):
    return dict(mode=mode, modelled=modelled, target=target,
                deviation_pct=dev, basis='share of resident linked trips',
                flag=flag, count=10)


def _goal(monkeypatch, rows, iteration=100):
    monkeypatch.setitem(__import__('sys').modules,
                        'report_mode_ridership', _StubReader(rows))
    return fit.score_goal_modes('/nowhere', iteration)


def test_the_objective_is_the_worst_mode_not_the_average(monkeypatch):
    g = _goal(monkeypatch, [_row('car', 5.0), _row('heavy_rail', 247.2),
                            _row('light_rail', -47.2)])
    # the mean of these is 99.8; the goal is satisfied by the WORST mode alone
    assert g['max_abs_rel_pct'] == 247.2
    assert g['worst_mode'] == 'heavy_rail'
    assert g['goal_met'] is False


def test_truck_and_freight_rail_are_reported_and_never_optimised_against(
        monkeypatch):
    g = _goal(monkeypatch, [
        _row('car', 5.0),
        _row('truck', None, flag='level only'),
        _row('freight_train', None, flag='representation')])
    assert g['n'] == 1                      # only car entered the maximum
    assert g['max_abs_rel_pct'] == 5.0
    modes = {m['mode']: m for m in g['modes']}
    assert modes['truck']['optimised'] is False
    assert modes['freight_train']['optimised'] is False
    # reported, not dropped: a mode that vanishes from the block is a mode
    # nobody notices is unscored
    assert len(g['modes']) == 3


def test_the_objective_is_inside_the_band_exactly_when_every_mode_is(
        monkeypatch):
    """The guard the change was made for: objective <= the pass band if and
    only if the gate would say every mode is inside it."""
    all_inside = _goal(monkeypatch, [_row('car', 5.0), _row('bus', -9.9),
                                     _row('ride', 0.0)])
    assert all_inside['max_abs_rel_pct'] <= all_inside['pass_band_pct']
    assert all_inside['goal_met'] is True
    assert all_inside['n_inside_pass_band'] == 3

    one_outside = _goal(monkeypatch, [_row('car', 5.0), _row('bus', -9.9),
                                      _row('ride', 10.1)])
    assert one_outside['max_abs_rel_pct'] > one_outside['pass_band_pct']
    assert one_outside['goal_met'] is False
    assert one_outside['n_inside_pass_band'] == 2


def test_a_run_the_reader_cannot_score_says_so_rather_than_scoring_zero(
        monkeypatch):
    g = _goal(monkeypatch, [])
    assert g['max_abs_rel_pct'] is None
    assert 'no rows' in g['reason']


def test_the_gate_thresholds_come_from_the_reader_not_from_fit(monkeypatch):
    """One registry field, one loader. If fit re-declared the pass band it
    could drift from the gate that judges the same run."""
    stub = _StubReader([_row('car', 12.0)])
    stub.GATE_PASS_PCT, stub.GATE_STOP_PCT = 15.0, 30.0
    monkeypatch.setitem(__import__('sys').modules,
                        'report_mode_ridership', stub)
    g = fit.score_goal_modes('/nowhere', 100)
    assert g['pass_band_pct'] == 15.0 and g['stop_bar_pct'] == 30.0
    assert g['goal_met'] is True            # 12.0 is inside a 15.0 band


# --------------------------------------------------------------------------
# the key the consumers read
# --------------------------------------------------------------------------
def test_the_patronage_level_uses_the_name_its_consumers_read():
    """`report.py` and `build_fit_figures.py` both read
    `intervention_boardings`. This block wrote a third name nothing read, so
    the calibration report's patronage section and FIGURES.json's block were
    silently empty from the rename at f1f0a09 until it was found by audit. A
    silently empty section is the failure mode a test exists to stop."""
    p = fit.score_patronage([], dict(pt=dict(intervention_boardings=1234)),
                            dict(unscorable=[]))
    assert p['intervention_boardings'] == 1234
    # the orphaned name is kept so a _fit.json written before the fix renders
    assert p['modelled_intervention_weekday_boardings'] == 1234
    # n=0 is CORRECT here and is not a gap: every patronage target is
    # unscorable against a 2026 base (DECISIONS.md 12.1)
    assert p['n'] == 0
