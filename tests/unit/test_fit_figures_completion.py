"""A missing `completion` is not evidence of success (front-door figures).

The README's fit figures may only be drawn from a run that executed the horizon
it declared (9.143). The test for that was `_load(path).get('completion') or
RAN_TO_LAST` - an unconditional fallback, so a record missing the field passed
for ANY reason it might be missing, on the one artefact the front door draws
from. The project's own result gate read vacuously true in its most public
place.

The fallback exists for a real case and keeps working: the 21 August F4 arm the
calibrated base rests on predates the field, carries `rc = 0` and executed all
1000 of its declared iterations. What it may no longer do is cover a record
that is missing the field for some other reason - so the evidence the
pre-schema case supplies is now required, and every arm this project has
stopped fails it (`rc` of 1 or none, and a short `reached_iteration`).
"""
import json
import os

import pytest

import build_fit_figures as bff


def _run_dir(tmp_path, **record):
    d = tmp_path / 'run'
    d.mkdir()
    (d / '_run.json').write_text(json.dumps(record), encoding='utf-8')
    return str(d)


def test_pre_schema_record_still_passes(tmp_path, capsys):
    """rc = 0 and the full declared horizon: the case the fallback is for."""
    d = _run_dir(tmp_path, rc=0, iterations=1000)
    assert bff._refuse_unless_ran_to_last(d) == d
    # it must SAY it fired - a fallback nobody sees is a fallback nobody audits
    assert 'predates' in capsys.readouterr().out


def test_missing_completion_with_a_nonzero_rc_is_refused(tmp_path):
    with pytest.raises(SystemExit) as exc:
        bff._refuse_unless_ran_to_last(_run_dir(tmp_path, rc=1, iterations=300))
    assert 'not evidence of success' in str(exc.value)


def test_missing_completion_with_no_rc_is_refused(tmp_path):
    """Every arm this project stopped by hand carries rc = None."""
    with pytest.raises(SystemExit):
        bff._refuse_unless_ran_to_last(
            _run_dir(tmp_path, iterations=300, reached_iteration=23))


def test_missing_completion_that_stopped_short_is_refused(tmp_path):
    """rc = 0 is not enough on its own: the horizon has to have been executed."""
    with pytest.raises(SystemExit) as exc:
        bff._refuse_unless_ran_to_last(
            _run_dir(tmp_path, rc=0, iterations=300, reached_iteration=100))
    assert 'reached 100 of 300' in str(exc.value)


def test_a_stopped_arm_is_refused_on_its_stated_completion(tmp_path):
    with pytest.raises(SystemExit) as exc:
        bff._refuse_unless_ran_to_last(
            _run_dir(tmp_path, rc=1, iterations=300, reached_iteration=100,
                     completion='stopped_at_gate'))
    assert 'stopped_at_gate' in str(exc.value)


def test_a_completed_arm_passes(tmp_path):
    d = _run_dir(tmp_path, rc=0, iterations=300, reached_iteration=300,
                 completion='ran_to_last_iteration')
    assert bff._refuse_unless_ran_to_last(d) == d


def test_a_run_with_no_record_at_all_is_refused(tmp_path):
    d = tmp_path / 'bare'
    d.mkdir()
    with pytest.raises(SystemExit) as exc:
        bff._refuse_unless_ran_to_last(str(d))
    assert 'no _run.json' in str(exc.value)
