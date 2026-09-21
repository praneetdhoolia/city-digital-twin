"""The second city's population synthesiser (9.204) reads published bands and
draws households from them; the pure pieces that decide what a count means:

* a published age label resolves to the single years it covers, and an open
  top band folds into the declared open age;
* household sizes drawn from the HL-14 band shares cover exactly the persons
  asked for, every household at least one person, sizes inside their bands;
* the person columns are the declared ones, in the declared order.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('pandas')

PATH = Path(__file__).resolve().parents[2] / 'cities/mumbai/build/build_population.py'
SPEC = importlib.util.spec_from_file_location('build_population', PATH)
synth = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(synth)


def test_age_labels_resolve_to_their_years():
    assert synth.band_bounds('7', 95) == (7, 7)
    assert synth.band_bounds('15-19', 95) == (15, 19)
    assert synth.band_bounds('80+', 95) == (80, 95)


def test_household_sizes_cover_the_persons_asked_for_and_stay_in_band():
    profile = {'household_size_1_pct': 5, 'household_size_2_pct': 10, 'household_size_3_pct': 20,
               'household_size_4_pct': 30, 'household_size_5_pct': 15, 'household_size_6_to_8_pct': 15,
               'household_size_9_plus_pct': 5, 'area_name': 'x'}
    rng = np.random.default_rng(20260810)
    for n in (1, 7, 100, 12345):
        sizes = synth.draw_sizes(rng, profile, n, 12)
        assert int(sizes.sum()) == n
        assert sizes.min() >= 1
        assert sizes.max() <= 12


def test_the_person_columns_are_declared_once():
    assert synth.PERSON_COLUMNS[:3] == ['person_id', 'household_id', 'geography_id']
    assert 'weight' in synth.PERSON_COLUMNS and 'car_available' in synth.PERSON_COLUMNS
    assert len(synth.PERSON_COLUMNS) == len(set(synth.PERSON_COLUMNS))
