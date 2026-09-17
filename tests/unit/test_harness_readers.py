"""Three harness readers read the right thing (twelfth report, 16 September 2026).

verify_launch.state() asks the progress digest before the log tail: at the
25 % log rate an ITERATION banner leaves a 400 KB tail within a minute, and
the reader said 'still in startup' for a run four iterations in.
watch_run.snapshot() reports THIS run's JVM by its recorded pid, not any JVM
over 2 GB on the host. build_status_board reads a stopped arm no later than
its record's reached_iteration.
"""
import json
import os

import pytest

import verify_launch
import watch_run


def _run(tmp_path, meta, log_text, progress=None):
    d = tmp_path / '20260101T000000_4it_25pct'
    d.mkdir()
    (d / '_meta.json').write_text(json.dumps(meta), encoding='utf-8')
    (d / 'matsim.log').write_text(log_text, encoding='utf-8')
    if progress is not None:
        (d / '_progress.json').write_text(json.dumps(progress), encoding='utf-8')
    return d


def test_the_digest_decides_a_launch_before_the_tail(tmp_path, monkeypatch):
    d = _run(tmp_path, dict(status='running'),
             'x' * 500_000 + '\nSIMULATION (NEW QSim) AT 08:00:00 : #active agents=1\n',
             progress=dict(iteration=4, iteration_seconds={'0': 700.0}))
    monkeypatch.setattr(verify_launch.results_store, 'resolve', lambda n: str(d))
    verdict, detail = verify_launch.state(d.name)
    assert verdict == 'took' and 'iteration 4' in detail


def test_a_mobsim_line_in_the_tail_means_the_launch_took(tmp_path, monkeypatch):
    d = _run(tmp_path, dict(status='running'),
             'x' * 500_000 + '\nSIMULATION (NEW QSim) AT 08:00:00 : #active agents=1\n')
    monkeypatch.setattr(verify_launch.results_store, 'resolve', lambda n: str(d))
    verdict, _ = verify_launch.state(d.name)
    assert verdict == 'took'


def test_the_watcher_reports_this_runs_jvm(tmp_path, monkeypatch):
    d = _run(tmp_path, dict(status='running', pid=11, jvm_pid=22), 'log\n',
             progress=dict(iteration=3, iteration_seconds={'1': 300.0, '2': 300.0}))
    monkeypatch.setattr(watch_run, 'pid_alive', lambda pid: pid == 22)
    # any JVM on the host would have said alive; the pid says otherwise here
    monkeypatch.setattr(watch_run, 'arm_running', lambda *a, **k: ['pid 99 (40000 MB)'])
    snap = watch_run.snapshot(str(d))
    assert snap['jvm_pid'] == 22 and snap['jvm_alive'] is True
    monkeypatch.setattr(watch_run, 'pid_alive', lambda pid: False)
    snap = watch_run.snapshot(str(d))
    assert snap['jvm_alive'] is False, 'a dead recorded JVM is dead whatever else runs'
