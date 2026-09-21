"""The one gate the launcher fold declares: where a city's scoring comes from.

Until 21 September 2026 (9.204, #238) the harness translated the reference
city's C1 nested-logit table into MATSim scoring at every emission and read
the HTS purpose share to do it, so a city with no C1 table - one that binds
every scoring parameter as a registry field - could not run through it and ran
through a launcher of its own. `RUN.scoring.translation` names the two ways,
and these invariants keep the fold honest:

* under `c1_translation` the emitter's runtime carries the four translated
  scoring parameters and the derived prices exactly as before;
* under `bound_fields` it carries NONE of them - the bound fields write them -
  and no C1 field (a time weight, a taxi fare part, the purpose share) is read;
* a value outside the two members is refused, never guessed at;
* the city-declared scenario tables (a boarding-fare table, a hired-fleet
  derivation) enter only under their own representation gates, and a gate
  that is on with no table is refused.
"""
import json
import os

import pytest

import build_matsim_run_inputs as bi


class FakeCfg(object):
    """A resolved registry that answers from a dict and records what was read."""

    def __init__(self, values):
        self.values = dict(values)
        self.read = []

    def get(self, key, caller=None):
        self.read.append(key)
        if key not in self.values:
            raise KeyError('no registry field %r' % key)
        return self.values[key]

    def sweep(self, key):
        return [0, 1]


BASE = {
    'RUN.mode_choice.modes': ['car', 'ride', 'walk', 'bike', 'pt', 'taxi'],
    'RUN.routing.pt_submode_scoring': 'aggregate',
    'RUN.transit_router.access_egress_basis': 'beeline',
    'A.parking.charged_hours_by_day_type': {'WEEKDAY': [8.0, 18.0]},
    'C.scoring.activity_typical_duration_s': {'home': 43200, 'work': 28800},
    'C.scoring.activity_minimal_duration_s': 900,
    'RUN.sample.storage_capacity_exponent': 1.0,
    'RUN.replanning.score_msa_representation': 'absent',
    'A.signals.representation': 'implicit_delay',
    'A.bike_stress.representation': 'absent',
    'C.crowding.representation': 'absent',
    'C.time_weights.service_quality_representation': 'absent',
    'A.parking.search_time_representation': 'absent',
    'C.income.representation': 'absent',
    'A.crossings.representation': 'absent',
    'A.fare.boarding_representation': 'absent',
    'B.hired_fleet.representation': 'absent',
}
PATHS = dict(output='out', network='n.xml.gz', plans='p.xml.gz', schedule='s.xml.gz',
             vehicles='v.xml.gz', mode_vehicles='veh.xml', parking_prices='pp.tsv',
             fraction=0.25)
SCORING = dict(waiting_pt=-1.0, utility_of_line_switch=-0.5, vot_aud_hr_used=20.0,
               modes={'car': dict(constant=0.0, marginalUtilityOfTraveling=-6.0),
                      'walk': dict(constant=-1.0, marginalUtilityOfTraveling=-7.0)})
TRANSLATED = ('scoring.waitingPt', 'scoring.utilityOfLineSwitch',
              'scoring.modeParams[*].constant',
              'scoring.modeParams[*].marginalUtilityOfTraveling_util_hr')


def test_the_two_members_and_nothing_else():
    assert bi.scoring_translation(FakeCfg({'RUN.scoring.translation': 'c1_translation'})) \
        == 'c1_translation'
    assert bi.scoring_translation(FakeCfg({'RUN.scoring.translation': 'bound_fields'})) \
        == 'bound_fields'
    with pytest.raises(SystemExit):
        bi.scoring_translation(FakeCfg({'RUN.scoring.translation': 'nested_logit'}))


def test_c1_translation_emits_the_translated_parameters_and_the_taxi_blend():
    cfg = FakeCfg(dict(BASE, **{
        'RUN.scoring.translation': 'c1_translation',
        'B.taxi.rideshare_trip_share': 0.5, 'B.taxi.fare_per_km_taxi': 2.0,
        'B.taxi.fare_per_km_rideshare': 1.0, 'B.taxi.flagfall_taxi': 4.0,
        'B.taxi.flagfall_rideshare': 2.0}))
    runtime = bi.config_runtime(cfg, SCORING, 'WEEKDAY', PATHS)
    for key in TRANSLATED:
        assert key in runtime, key
    assert runtime['scoring.modeParams[*].constant'][0] == {'car': 0.0, 'walk': -1.0}
    assert runtime['scoring.modeParams[taxi].monetaryDistanceRate'][0] == -0.0015
    assert runtime['fare.flagfall'][0] == 3.0


def test_bound_fields_emits_no_translated_parameter_and_reads_no_c1_field():
    cfg = FakeCfg(dict(BASE, **{'RUN.scoring.translation': 'bound_fields',
                                'C.crowding.representation': 'in_vehicle_time',
                                'C.time_weights.service_quality_representation': 'headway_and_reliability',
                                'A.bike_stress.representation': 'felt_time',
                                'A.parking.search_time_representation': 'scoring',
                                'RUN.qsim.end_time_h': 30, 'RUN.qsim.start_time_h': 0}))
    runtime = bi.config_runtime(cfg, None, 'WEEKDAY', PATHS)
    for key in TRANSLATED + ('scoring.modeParams[taxi].monetaryDistanceRate', 'fare.flagfall',
                             'fare.mode', 'ptCrowding.penaltyUtilsPerHour',
                             'serviceQuality.headwayUtilsPerMin',
                             'serviceQuality.reliabilityUtilsPerMin',
                             'bikeStress.penaltyUtilsPerHour',
                             'parking.searchPenaltyUtilsPerMin'):
        assert key not in runtime, key
    # what no registry holds is still supplied
    for key in ('qsim.flowCapacityFactor', 'qsim.storageCapacityFactor',
                'parking.chargedStartHour', 'scoring.fractionOfIterationsToStartScoreMSA',
                'scoring.activityParams[*].minimalDuration', 'serviceQuality.headwayCapMin'):
        assert key in runtime, key
    assert runtime['serviceQuality.headwayCapMin'][0] == 1800.0
    c1_keys = [k for k in cfg.read
               if k.startswith(('C.time_weights.beta', 'B.taxi.fare', 'B.taxi.flagfall',
                                'B.taxi.rideshare', 'C.asc.'))]
    assert not c1_keys, c1_keys


def test_c1_scoring_is_none_under_bound_fields_without_opening_the_c1_table():
    cfg = FakeCfg({'RUN.scoring.translation': 'bound_fields'})
    assert bi.c1_scoring(cfg, None) is None


def test_the_scoring_order_rule_reads_the_bound_rates_under_bound_fields():
    ok = FakeCfg({'RUN.scoring.translation': 'bound_fields',
                  'C.scoring.marginal_utility_of_traveling': {'walk': -6.0, 'bike': -6.5}})
    bi.check_scoring_order(ok)
    inverted = FakeCfg({'RUN.scoring.translation': 'bound_fields',
                        'C.scoring.marginal_utility_of_traveling': {'walk': -7.0, 'bike': -6.0}})
    with pytest.raises(SystemExit):
        bi.check_scoring_order(inverted)


def test_scenario_tables_enter_only_under_their_gates(tmp_path):
    cfg = FakeCfg(dict(BASE, **{'RUN.scoring.translation': 'bound_fields',
                                'A.fare.boarding_representation': 'table',
                                'B.hired_fleet.representation': 'pooled_queue'}))
    with pytest.raises(SystemExit):
        bi.config_runtime(cfg, None, 'WEEKDAY', PATHS)          # the gates are on, no tables
    fleet = tmp_path / 'hired_fleet.json'
    fleet.write_text(json.dumps({'vehicles_by_mode': {'taxi': 8, 'auto_rickshaw': 17}}),
                     encoding='utf-8')
    paths = dict(PATHS, boarding_fares='fares.csv', hired_fleet=str(fleet))
    runtime = bi.config_runtime(cfg, None, 'WEEKDAY', paths)
    assert runtime['boardingFare.tableFile'][0] == 'fares.csv'
    assert runtime['hiredFleet.vehiclesByMode'][0] == 'auto_rickshaw:17,taxi:8'
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps({'vehicles_by_mode': {'taxi': 1.5}}), encoding='utf-8')
    with pytest.raises(SystemExit):
        bi.config_runtime(cfg, None, 'WEEKDAY', dict(paths, hired_fleet=str(bad)))
    off = FakeCfg(dict(BASE, **{'RUN.scoring.translation': 'bound_fields'}))
    runtime = bi.config_runtime(off, None, 'WEEKDAY', paths)
    assert 'boardingFare.tableFile' not in runtime
    assert 'hiredFleet.vehiclesByMode' not in runtime


def test_the_launcher_of_the_second_city_is_gone():
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    assert not os.path.exists(os.path.join(repo, 'src', 'run', 'baseline_smoke.py'))
    assert '--baseline-smoke' not in open(os.path.join(repo, 'run.py'), encoding='utf-8').read()


def test_a_run_fraction_above_the_plans_build_fraction_is_refused(tmp_path, monkeypatch):
    """A city too large for a file of everyone writes the households the
    sampler's nested hash keeps at a build fraction (9.205); the launcher
    refuses a run above it and passes one at or below it, and a report
    without the field (the reference city's) means everyone is there."""
    import run_matsim
    monkeypatch.setattr(run_matsim, 'PLANS', str(tmp_path))
    assert run_matsim.plans_build_fraction() == 1.0
    (tmp_path / '_plans_report.json').write_text(json.dumps({'build_fraction': 0.05}), encoding='utf-8')
    assert run_matsim.plans_build_fraction() == 0.05
    run_matsim.refuse_fraction_above_build(0.05)
    run_matsim.refuse_fraction_above_build(0.001)
    with pytest.raises(SystemExit):
        run_matsim.refuse_fraction_above_build(0.25)


def test_a_whole_population_fleet_scales_with_the_run_fraction(tmp_path):
    cfg = FakeCfg(dict(BASE, **{'RUN.scoring.translation': 'bound_fields',
                                'B.hired_fleet.representation': 'pooled_queue'}))
    fleet = tmp_path / 'hired_fleet.json'
    fleet.write_text(json.dumps({'vehicles_by_mode': {'taxi': 143224, 'auto_rickshaw': 297664},
                                 'scale_with_sample_fraction': True}), encoding='utf-8')
    runtime = bi.config_runtime(cfg, None, 'WEEKDAY', dict(PATHS, hired_fleet=str(fleet), fraction=0.001))
    assert runtime['hiredFleet.vehiclesByMode'][0] == 'auto_rickshaw:298,taxi:143'
    fleet.write_text(json.dumps({'vehicles_by_mode': {'taxi': 8}}), encoding='utf-8')
    runtime = bi.config_runtime(cfg, None, 'WEEKDAY', dict(PATHS, hired_fleet=str(fleet), fraction=0.001))
    assert runtime['hiredFleet.vehiclesByMode'][0] == 'taxi:8'
