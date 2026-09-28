"""A dead arm is recorded as dead, crash recovery may resume it, and an arm is
never launched where its shell can take it down (9.215).

F38's arm 0 was launched with --foreground from a session's background shell
and died with that session at iteration 79. --stop then closed it out as
`stopped_by_operator`, which the warm start refuses because a deliberate stop
is not a crash. These tests pin the three repairs: --stop records a run whose
processes were already gone as `died`; the warm start resumes `died`, and
resumes an operator stop only with a stated reason; the launcher refuses an
arm-length run in the foreground unless the scheduler's own wrapper asks.
"""
import json
import os
import types

import pytest

import run_matsim as rm


def _dead_run(tmp_path, completion=None, checkpoint=75):
    d = tmp_path / '20260927T145839_250it_25pct'
    it = d / 'output' / 'ITERS' / ('it.%d' % checkpoint)
    it.mkdir(parents=True)
    (it / ('%d.plans.xml.gz' % checkpoint)).write_bytes(b'')
    (d / '_meta.json').write_text(json.dumps(dict(status='aborted')), encoding='utf-8')
    if completion:
        (d / '_run.json').write_text(json.dumps(dict(completion=completion)),
                                     encoding='utf-8')
    return str(d)


def test_a_died_record_is_crash_recoverys(tmp_path):
    w = rm.resolve_warm_start(_dead_run(tmp_path, rm.DIED))
    assert w['iteration'] == 75 and w['death'] == 'recorded as died'


def test_an_operator_stop_is_refused_without_a_reason(tmp_path):
    with pytest.raises(SystemExit, match='stopped-was-death'):
        rm.resolve_warm_start(_dead_run(tmp_path, rm.STOPPED_BY_OPERATOR))


def test_an_operator_stop_that_closed_a_death_resumes_with_its_reason(tmp_path):
    w = rm.resolve_warm_start(_dead_run(tmp_path, rm.STOPPED_BY_OPERATOR),
                              stopped_was_death='the session took the harness')
    assert w['death'] == 'the session took the harness'


def test_a_reason_does_not_open_a_gate_stop_or_a_finished_run(tmp_path):
    for completion in (rm.STOPPED_AT_GATE, rm.RAN_TO_LAST):
        sub = tmp_path / completion
        sub.mkdir()
        with pytest.raises(SystemExit):
            rm.resolve_warm_start(_dead_run(sub, completion), stopped_was_death='x')


def test_a_run_with_no_record_is_still_a_crash(tmp_path):
    w = rm.resolve_warm_start(_dead_run(tmp_path))
    assert w['iteration'] == 75 and w['death'] is None


def _stub_stop(monkeypatch, tmp_path, alive):
    d = tmp_path / 'r'
    d.mkdir()
    (d / '_meta.json').write_text(json.dumps(dict(status='running', pid=1, jvm_pid=2)),
                                  encoding='utf-8')
    seen = {}
    monkeypatch.setattr(rm.results_store, 'resolve', lambda name: str(d))
    monkeypatch.setattr(rm, 'card_pid_alive', lambda meta, key: alive)
    monkeypatch.setattr(rm.subprocess, 'run', lambda *a, **k: None)
    monkeypatch.setattr(rm.time, 'sleep', lambda s: None)
    monkeypatch.setattr(rm, 'mark_dead', lambda run_dir, status, cause=None: run_dir)

    def close_out(dead, completion, **kw):
        seen['completion'] = completion
        return None
    monkeypatch.setattr(rm, 'close_out', close_out)
    monkeypatch.setattr(rm.registry, 'load', lambda: {})
    monkeypatch.setattr(rm.results_store, 'trim', lambda *a, **k: None)
    return seen


def test_stop_records_a_run_already_dead_as_died(monkeypatch, tmp_path):
    seen = _stub_stop(monkeypatch, tmp_path, alive=False)
    rm.stop_run('r', 'killed with its session')
    assert seen['completion'] == rm.DIED


def test_stop_records_a_live_run_as_stopped_by_the_operator(monkeypatch, tmp_path):
    seen = _stub_stop(monkeypatch, tmp_path, alive=True)
    rm.stop_run('r', 'the operator stopped it')
    assert seen['completion'] == rm.STOPPED_BY_OPERATOR


def test_the_death_reason_meets_both_record_contracts():
    """The first warm start of 9.215 was refused by the meta contract: the
    code wrote `warm_started_from.death` and the schema did not allow it."""
    from registry import outputs
    key = dict(run='aborted_x', iteration=75, death='recorded as died')
    for kind in ('meta', 'run'):
        schema = outputs._schema(kind)
        props = schema['properties']['warm_started_from']['properties']
        assert set(key) <= set(props), kind


def test_the_resumed_cutoff_survives_the_jars_truncation(monkeypatch):
    """The jar computes the cutoff as int(first + f x (last - first)) (d2i);
    a fraction rounded to nearest put a resume at 175 on iteration 199."""
    class Base(dict):
        def get(self, k):
            return self[k]
    base = Base({'RUN.controler.first_iteration': 0,
                 'RUN.controler.last_iteration': 250,
                 'RUN.replanning.fraction_to_disable_innovation': 0.8})
    monkeypatch.setattr(rm.registry, 'load', lambda **kw: base)
    for n in range(1, 200):
        out = rm.warm_start_overrides({'iteration': n, 'run': 'dead'}, {}, 'S2', 'WEEKDAY', None)
        f = out['RUN.replanning.fraction_to_disable_innovation']
        assert int(n + f * (250 - n)) == 200, n


def test_a_resume_overlay_is_not_re_derived(monkeypatch):
    class Base(dict):
        def get(self, k):
            return self[k]
    base = Base({'RUN.controler.first_iteration': 175,
                 'RUN.controler.last_iteration': 250,
                 'RUN.replanning.fraction_to_disable_innovation': 0.333334})
    monkeypatch.setattr(rm.registry, 'load', lambda **kw: base)
    assert rm.warm_start_overrides({'iteration': 175, 'run': 'dead'}, {}, 'S2', 'WEEKDAY', None) == {}


class _Cfg(dict):
    get = dict.get


def _run_py():
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        'run_py', os.path.join(here, '..', '..', 'run.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_an_arm_is_refused_in_the_foreground():
    run_py = _run_py()
    a = types.SimpleNamespace(foreground=True, scheduled_child=False)
    with pytest.raises(SystemExit, match='REFUSED'):
        run_py.refuse_foreground_arm(a, _Cfg({'RUN.controler.last_iteration': 250}))


def test_a_probe_and_the_schedulers_child_may_run_in_the_foreground():
    run_py = _run_py()
    probe = types.SimpleNamespace(foreground=True, scheduled_child=False)
    run_py.refuse_foreground_arm(probe, _Cfg({'RUN.controler.last_iteration': 4}))
    child = types.SimpleNamespace(foreground=True, scheduled_child=True)
    run_py.refuse_foreground_arm(child, _Cfg({'RUN.controler.last_iteration': 250}))
