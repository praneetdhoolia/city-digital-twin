"""What the calibration loop is allowed to move, and how it says so.

Three defects lived here at once, and none was visible from the outside because
`src/calibrate/calibrate.py` was imported by no test at all:

  * the loop handed REGISTRY keys to `run_matsim.py`'s RAW MATSim `--set`
    channel, so `--execute` could not complete a single candidate and the
    search had never once run;
  * `rebuild_stage` classified a field by its consumer's BASENAME and excluded
    anything the lookup table did not recognise - correct as a default over a
    name, but it also excluded fields carrying a declared `matsim_param`
    binding, which reach the config on every run whatever else consumes them.
    That is how a registry of 482 declared fields produced a movable set of
    five;
  * `run_inputs` sat in `STAGES_IMPLEMENTED` while `evaluate()` rebuilt
    nothing, so a candidate on such a field ran the SHIPPED value and the
    search compared a parameter against itself.

These assert the contracts rather than the implementations, and they build
their own synthetic fields: no registry, no run, no `results/`.
"""
import calibrate


def _field(**kw):
    f = dict(source='assumed', status='active', value=1.0, sweep=[0.0, 2.0])
    f.update(kw)
    return f


# --------------------------------------------------------------------------
# the binding is the evidence
# --------------------------------------------------------------------------
def test_a_matsim_binding_makes_a_field_run_time_realisable():
    """A declared binding reaches the config on every run, so the consumer
    table must not be able to say it reaches nothing."""
    stage, why = calibrate.rebuild_stage(
        'A.gradient.bike_speed_floor_factor',
        _field(matsim_param='gradient.bikeSpeedFloorFactor',
               consumers=['src/java/citysim/GradientConfigGroup.java']))
    assert stage == 'none' and why is None


def test_a_binding_with_no_declared_consumer_is_still_realisable():
    stage, _ = calibrate.rebuild_stage(
        'B.taxi.max_wait_min', _field(matsim_param='taxi.maxWaitMin'))
    assert stage == 'none'


def test_an_unknown_consumer_without_a_binding_is_still_excluded():
    """The conservative default over a NAME is right and stays: the permissive
    one once put the OSM harvest margins in the movable set, where a --set
    would have been recorded in the run's provenance and changed nothing."""
    stage, why = calibrate.rebuild_stage(
        'A.osm.harvest_margin_m',
        _field(consumers=['cities/newcastle/extract/overpass.py']))
    assert stage == 'excluded' and 'does not classify' in why


def test_a_field_with_no_consumer_and_no_binding_is_excluded():
    stage, why = calibrate.rebuild_stage('A.some.orphan', _field())
    assert stage == 'excluded' and 'no declared consumer' in why


def test_measurement_apparatus_is_excluded_even_with_a_binding():
    """A field the analysis layer consumes describes how the model is MEASURED.
    Tuning it would move the yardstick, not the model."""
    stage, why = calibrate.rebuild_stage(
        'CAL.something', _field(matsim_param='x',
                                consumers=['src/analyse/report.py']))
    assert stage == 'excluded'


def test_the_schedule_mapper_stays_forbidden():
    """DECISIONS.md 3.5: re-running pt2matsim moves ~18% of route link
    sequences, so a field needing it is uncalibratable INSIDE a comparison
    whatever its sweep says - and a binding must not override that."""
    stage, why = calibrate.rebuild_stage(
        'A.lightrail.corridor_speed_kmh',
        _field(consumers=['cities/newcastle/build/build_scenario_schedules.py']))
    assert stage == 'forbidden' and '3.5' in why


# --------------------------------------------------------------------------
# a stage the loop claims it can carry out, it must actually carry out
# --------------------------------------------------------------------------
def test_every_implemented_stage_is_one_the_loop_can_really_do():
    """`run_inputs` is in this list because `evaluate()` now re-assembles the
    scenario x day per candidate. If that rebuild is ever removed, this list
    must shrink with it - otherwise the loop silently compares a parameter
    against itself."""
    assert set(calibrate.STAGES_IMPLEMENTED) == {'none', 'run_inputs'}
    src = open(calibrate.__file__, encoding='utf-8').read()
    assert 'def rebuild_run_inputs' in src
    assert 'build_matsim_run_inputs.py' in src


def test_the_loop_uses_the_registry_override_channel_not_the_raw_matsim_one():
    """`--config-set` takes a registry key, validates it against its declared
    sweep and refuses a held-fixed field. `--set` takes a raw MATSim key and
    splits it on the first dot. The loop used `--set` and therefore died on its
    first candidate, for as long as it had existed."""
    src = open(calibrate.__file__, encoding='utf-8').read()
    assert "'--config-set'" in src
    assert "sets += ['--set'" not in src


def test_free_parameters_carry_the_stage_they_need():
    """`evaluate()` decides whether to re-assemble from this, so it has to be
    on every free parameter, not derived a second time somewhere else."""
    class _Cfg(dict):
        def keys(self):
            return ['B.taxi.max_wait_min']

        def field(self, key):
            return _field(matsim_param='taxi.maxWaitMin', units='minutes')

    free = calibrate.free_parameters(_Cfg())
    assert len(free) == 1
    assert free[0]['stage'] == 'none'
    assert free[0]['key'] == 'B.taxi.max_wait_min'


# --------------------------------------------------------------------------
# the reading point has to be able to resolve the answer
# --------------------------------------------------------------------------
def test_the_loop_refuses_a_reading_that_cannot_resolve_the_goal_band():
    """Iteration 100 was adopted as the reading point on COST and never tested
    for stability. Measured within-run on all six 25% arms that reached it, the
    worst scored mode's deviation drifts 15.72-24.88 points between iteration 80
    and 100 with nothing changed - two and a half times the 10% band a mode is
    asked to sit inside, and three modes clear the whole band inside that window
    (heavy_rail on 6 of 6, bike on 4, taxi on 3). A search scored there ranks
    how far the run had got, not the parameters, and hands back a `best_tag`
    that looks exactly like a result - so the loop refuses to start one."""
    src = open(calibrate.__file__, encoding='utf-8').read()
    assert "CAL.search.reading_drift_pct" in src
    assert "refusing to search on a reading that cannot resolve" in src
    # and it refuses only --execute: --plan must still cost the search, because
    # knowing what it WOULD cost is how the reading gets fixed
    assert "if a.execute:" in src


def test_the_stopping_rule_is_derived_from_the_reading_noise():
    """A stopping rule smaller than the reading's own drift cannot tell an
    improvement from noise. It was 0.25 pp against a measured 0.272-0.418 pp on
    the old folded objective - smaller on every one of the six arms, and the
    drift ran UPWARD on all six, so it is systematic movement toward relaxation
    rather than seed scatter. The rule is now derived from the measurement
    rather than chosen beside it."""
    import json
    import os
    here = os.path.dirname(os.path.abspath(calibrate.__file__))
    repo = os.path.abspath(os.path.join(here, '..', '..'))
    path = os.path.join(repo, 'cities', 'newcastle', 'registry',
                        'CAL_calibration.json')
    fields = json.load(open(path, encoding='utf-8'))['fields']
    delta = fields['CAL.search.convergence_delta']
    drift = fields['CAL.search.reading_drift_pct']
    assert delta['source'] == 'derived'
    assert 'CAL.search.reading_drift_pct' in delta['derived_from']['fields']
    assert delta['value'] == drift['value']
    assert delta['units'] == drift['units'] == 'per cent'
    # the measurement carries its own spread, as a measurement must
    assert drift['source'] == 'measured' and drift['sweep_role'] == 'measurement'
