"""The calibration objective's missing denominator (#163).

History matching's implausibility statistic is `|observed - modelled|` over a
denominator that includes model discrepancy and observational noise. This
project's objective is a bare maximum over twelve modes with NO DENOMINATOR AT
ALL - and a MATSim run is not bit-reproducible, so some part of every deviation
the loop chases is seed scatter: within `20260909T015217_300it_25pct`, with
nothing changed, the folded objective moves 0.272-0.418 pp between iterations
80 and 100 (DECISIONS.md 9.162).

The band is now a declared field and the objective divides by it. It ships at
**zero**, which divides by nothing, because THE BAND HAS NOT BEEN MEASURED -
choosing one from its own sweep would be inventing the observation the
denominator exists to represent.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
for _sub in ('calibrate', 'registry', ''):
    _p = os.path.join(REPO, 'src', _sub) if _sub else os.path.join(REPO, 'src')

import calibrate  # noqa: E402

FIT = {'goal_modes': {'max_abs_rel_pct': 41.0}}
COMPONENTS = {'goal_modes.max_abs_rel_pct': 1.0}


def test_a_band_of_zero_is_the_raw_maximum():
    """Declaring the field must not move a single existing reading."""
    obj, parts = calibrate.objective(FIT, COMPONENTS, 0.0)
    assert obj == pytest.approx(41.0)
    assert parts['goal_modes.max_abs_rel_pct'] == pytest.approx(41.0)


def test_a_band_makes_the_objective_count_bands_out():
    obj, _ = calibrate.objective(FIT, COMPONENTS, 0.5)
    assert obj == pytest.approx(82.0), (
        'the objective is not |deviation| / band, so a deviation inside the '
        'noise would still score as though it were a misfit')


def test_a_deviation_inside_the_band_scores_below_one():
    """The whole point: stop chasing what the seed produced."""
    obj, _ = calibrate.objective({'goal_modes': {'max_abs_rel_pct': 0.3}},
                                 COMPONENTS, 0.5)
    assert obj < 1.0


def test_a_negative_band_is_refused_rather_than_absolute_valued():
    with pytest.raises(SystemExit) as e:
        calibrate.objective(FIT, COMPONENTS, -0.5)
    assert 'replication band' in str(e.value)
    assert 'CAL.objective.replication_band_pp' in str(e.value)


def test_the_argument_has_no_default():
    """A default here would be the same value decided in two places."""
    import inspect
    sig = inspect.signature(calibrate.objective)
    assert sig.parameters['band_pp'].default is inspect.Parameter.empty, (
        'objective() carries a default band, so a caller that forgot to read '
        'the registry would silently score on a band nobody declared')


def test_the_band_is_declared_and_ships_at_zero():
    import registry
    fields, _origin = registry.load_registry(
        os.path.join(REPO, 'cities', os.environ.get('CITYSIM_CITY', 'newcastle'),
                     'registry'))
    field = fields['CAL.objective.replication_band_pp']
    assert field['value'] == 0.0, (
        'the band does not ship at zero, so a denominator nobody measured is '
        'already dividing every reading')
    assert field['sweep_role'] == 'measurement', (
        "the sweep is not marked `measurement`, so it reads as a range to "
        'select a value from rather than an honesty bracket for an unmeasured '
        'quantity')
