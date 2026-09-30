"""The choice-set bound reads what THIS run ran (9.217).

F38's arm 0 finished as a run warm-started at iteration 225, and the bound
printed pt coverage 1.69 % and "target unreachable" because MATSim counts
coverage from the run's own first iteration; it also still called motorbike
a locked carve although the run chose it.
"""
import json

import report_choice_set_coverage as cov


def _run(tmp_path, **values):
    (tmp_path / '_config.json').write_text(json.dumps({'values': values}),
                                           encoding='utf-8')
    return str(tmp_path)


def test_motorbike_is_locked_only_under_the_carve(tmp_path):
    assert 'motorbike' in cov.locked_modes(_run(tmp_path, **{'B.motorbike.representation': 'carve'}))
    chosen = tmp_path / 'c'
    chosen.mkdir()
    assert cov.locked_modes(_run(chosen, **{'B.motorbike.representation': 'choice'})) == ('truck',)


def test_a_warm_started_run_is_known_by_its_first_iteration(tmp_path):
    assert cov.warm_start_iteration(_run(tmp_path, **{'RUN.controler.first_iteration': 225})) == 225
    cold = tmp_path / 'cold'
    cold.mkdir()
    assert cov.warm_start_iteration(_run(cold, **{'RUN.controler.first_iteration': 0})) is None


def test_a_run_without_a_snapshot_keeps_the_old_reading(tmp_path):
    assert cov.locked_modes(str(tmp_path)) == cov.LOCKED_MODES
    assert cov.warm_start_iteration(str(tmp_path)) is None
