"""Three harness readers read the right thing (twelfth report, 16 September 2026).

verify_launch.state() asks the progress digest before the log tail: at the
25 % log rate an ITERATION banner leaves a 400 KB tail within a minute, and
the reader said 'still in startup' for a run four iterations in.
watch_run.snapshot() reports THIS run's JVM by its recorded pid, not any JVM
over 2 GB on the host. build_status_board reads a stopped arm no later than
its record's reached_iteration.

The last two pin the SETUP WINDOW (sixty-second session). A detached launch
returns as soon as the Task Scheduler accepts the job, and the harness then
subsamples the population - minutes at 25 % - before it creates the run
directory, writes `_meta.json` or starts a JVM. Both readers called that
window death: `watch_run` read the absent card's absent pids as dead ones and
printed `harness DEAD; JVM gone` at a healthy probe, and `verify_launch`,
having no directory to find, took the NEWEST run under raw/ - the previous,
completed one - and answered TOOK about a launch that had written nothing.
A false green on the guard that exists because two launches once died
silently (#70) is worse than no guard.
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


def test_a_run_still_in_setup_is_not_a_dead_run(tmp_path, monkeypatch):
    """No `_meta.json` means NOT STARTED, and must not read as death."""
    d = tmp_path / '20260101T000000_4it_25pct'
    d.mkdir()          # exactly what the runner leaves during the subsample
    # nothing else on the host may answer for a run that has not started
    monkeypatch.setattr(watch_run, 'pid_alive', lambda pid: False)
    monkeypatch.setattr(watch_run, 'arm_running', lambda *a, **k: ['pid 99 (40000 MB)'])
    snap = watch_run.snapshot(str(d))
    assert snap['card_present'] is False
    assert snap['harness_alive'] is None, 'an unrecorded pid is unknown, not dead'
    assert snap['jvm_alive'] is None, 'a JVM that has not started yet has not gone'
    line = watch_run.one_line(snap)
    assert 'NOT STARTED YET' in line
    assert 'DEAD' not in line and 'gone' not in line


def test_a_recorded_pid_that_is_gone_is_still_dead(tmp_path, monkeypatch):
    """The setup window must not blind the reader to a real death (9.176)."""
    d = _run(tmp_path, dict(status='running', pid=11, jvm_pid=22), 'log\n')
    monkeypatch.setattr(watch_run, 'pid_alive', lambda pid: False)
    snap = watch_run.snapshot(str(d))
    assert snap['card_present'] is True
    assert snap['harness_alive'] is False and snap['jvm_alive'] is False
    assert 'DEAD' in watch_run.one_line(snap)


def test_verify_launch_binds_to_the_stamp_not_the_newest_run(tmp_path, monkeypatch):
    """The stamp names the run before the run exists; the newest is the wrong one."""
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / '20260101T000000_250it_25pct').mkdir()      # the PREVIOUS, finished run
    monkeypatch.setattr(verify_launch.results_store, 'RAW', str(raw))

    # during setup the stamped directory does not exist yet
    assert verify_launch.run_for_stamp('20260102T111111') is None
    assert verify_launch.await_stamp('20260102T111111', 0, 0, wait=False) is None, \
        'it must report nothing found rather than fall back to the newest run'

    (raw / '20260102T111111_4it_25pct').mkdir()        # the runner creates it
    assert verify_launch.run_for_stamp('20260102T111111') == '20260102T111111_4it_25pct'
    assert verify_launch.await_stamp('20260102T111111', 0, 0, wait=False) == \
        '20260102T111111_4it_25pct'
