"""Activity evidence must not silently become demand or lose distant options."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[2] / 'cities/mumbai/build/build_baseline_activities.py'
SPEC = importlib.util.spec_from_file_location('baseline_activities', PATH)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def test_inactive_or_missing_tags_cannot_generate_attractions():
    rules = {'work': {'office': ['*']}, 'school': {'amenity': ['school']}}
    assert adapter.eligible_purposes({}, rules) == []
    assert adapter.eligible_purposes({'office': 'vacant'}, rules) == []
    assert adapter.eligible_purposes({'office': 'company', 'disused': 'yes'}, rules) == []
    assert adapter.eligible_purposes({'office': 'company', 'disused': 'no'}, rules) == ['work']


def test_benchmark_refuses_mixed_population_units_and_duplicate_rows():
    row = dict(activity='example', residence='urban', sex='female', activity_scope='major_activity',
               denominator='participation', unit='percent', value='25', source_id='source')
    assert adapter.benchmark([row], 'example', 'urban', 'female', 'participation') == (25, 'source')
    for rows in ([row, row], [dict(row, unit='minutes_per_day')], [dict(row, sex='person')]):
        with pytest.raises(ValueError):
            adapter.benchmark(rows, 'example', 'urban', 'female', 'participation')


def test_gravity_keeps_support_when_every_destination_is_far_away():
    # Direct exp(-distance/scale) underflows here and destroys all alternatives.
    choices = [dict(x_m=1e7, y_m=0, weight=1, identity='a'),
               dict(x_m=1e7+1, y_m=0, weight=1, identity='b')]
    first = adapter.select_destination(np.random.default_rng(8), np.array([0, 0]), choices, 1)
    second = adapter.select_destination(np.random.default_rng(8), np.array([0, 0]), choices, 1)
    assert first == second and first in choices
