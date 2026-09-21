import gzip

import pytest

import importlib.util
from pathlib import Path

# the assembly lives with its city (9.204); the functions under test are pure
PATH = Path(__file__).resolve().parents[2] / 'cities/mumbai/build/build_baseline_run_inputs.py'
SPEC = importlib.util.spec_from_file_location('baseline_run_inputs', PATH)
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)
population_audit = assembly.population_audit


def test_only_selected_demand_counts_and_home_only_people_are_retained(tmp_path):
    path = tmp_path / 'population.xml.gz'
    with gzip.open(path, 'wt') as stream:
        stream.write('''<population><person id="a"><attributes>
        <attribute name="subpopulation">person</attribute></attributes>
        <plan selected="no"><activity type="home"/><leg mode="walk"/><activity type="other"/></plan>
        <plan selected="yes"><activity type="home"/></plan></person>
        <person id="b"><attributes><attribute name="subpopulation">freight</attribute></attributes>
        <plan><activity type="depot"/><leg mode="truck"/><activity type="delivery"/></plan>
        </person></population>''')
    audit = population_audit(path)
    groups = audit['by_subpopulation']
    assert audit['maximum_initial_plans_per_person_count'] == 2
    assert audit['persons_by_initial_plan_count'] == {1: 1, 2: 1}
    assert groups['person'] == dict(persons_count=1, input_legs_count=0, destination_activities={})
    assert groups['freight'] == dict(persons_count=1, input_legs_count=1,
                                   destination_activities={'delivery': 1})


def test_ambiguous_selection_is_refused_instead_of_double_counting(tmp_path):
    path = tmp_path / 'population.xml.gz'
    with gzip.open(path, 'wt') as stream:
        stream.write('<population><person id="a"><plan/><plan/></person></population>')
    with pytest.raises(ValueError, match='one selected plan'):
        population_audit(path)
