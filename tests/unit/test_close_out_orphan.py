"""A run whose harness died while its JVM ran to the horizon is a RESULT.

`20260915T000704_250it_25pct` ran all 250 of its iterations and shut down
cleanly at 03:30 on 16 September 2026, but the harness that launched it had
died at iteration 34 the morning before, so nothing wrote `_run.json`,
`_meta.json` still said `running`, and the only path the framework had for the
state - `reconcile_stale()` at the next launch - would have recorded a 27.4 h
result as `failed`, with Guice's survivable `Unsupported class file major
version` as its cause (DECISIONS.md 9.176, D5).

`run.py --close-out` is the one sanctioned way to close that state out, and
these tests pin what it accepts and what it refuses: the record it writes says
`ran_to_last_iteration` at the declared horizon, with the pace read from the
LOG (the digest stops where the harness died); a run that is alive, that did
not shut down cleanly, or that ended short of its horizon is refused - a short
run is a reading, never a result, and this must not be a way of promoting one.
"""
import json
import os
import pathlib
import time

import pytest

import run_matsim


def _log(last_it, clean=True, unexpected=False):
    lines = []
    for i in range(last_it + 1):
        h = 10 + i // 12
        m = (i % 12) * 5
        lines.append('2026-09-15T%02d:%02d:00,000  INFO AbstractController:137 '
                     '### ITERATION %d BEGINS' % (h, m, i))
        lines.append('2026-09-15T%02d:%02d:00,000  INFO AbstractController:184 '
                     '### ITERATION %d ENDS' % (h, m + 4, i))
    # the survivable throwable every one of these logs carries
    lines.insert(0, 'java.lang.IllegalArgumentException: Unsupported class '
                    'file major version 69')
    if unexpected:
        lines.append('2026-09-15T20:00:00,000  ERROR MatsimRuntimeModifications:'
                     '80 S H U T D O W N   ---   unexpected shutdown request')
    if clean:
        lines.append('2026-09-15T20:00:00,000  INFO MatsimRuntimeModifications:'
                     '105 S H U T D O W N   ---   shutdown completed.')
    return '\n'.join(lines) + '\n'


@pytest.fixture
def orphan(tmp_path, monkeypatch):
    d = tmp_path / '20260915T000704_12it_25pct'
    d.mkdir()
    card = dict(
        status='running', scenario='S2', day='WEEKDAY', fraction=0.25,
        sample_pct=25.0, iterations=12, seed=20260810, threads=16, xmx='48g',
        overrides={}, controler_sha256='c' * 64, inputs_sha256='i' * 64,
        values_sha256='v' * 64, config_snapshot='_config.json',
        sample=dict(persons_in=1000, persons_kept=250,
                    transit_capacity_scaled=[]),
        started='2026-09-15T10:00:00', ended=None, wall_s=None,
        rc=None, pid=999999991, jvm_pid=999999992)
    (d / '_meta.json').write_text(json.dumps(card), encoding='utf-8')
    (d / 'matsim.log').write_text(_log(12), encoding='utf-8')
    # the digest stopped where the harness died
    (d / '_progress.json').write_text(
        json.dumps({'iteration': 3, 'iteration_seconds': {'1': 240.0}}),
        encoding='utf-8')
    monkeypatch.setattr(run_matsim.results_store, 'resolve',
                        lambda name: str(d))
    monkeypatch.setattr(run_matsim, '_pid_alive', lambda pid: False)
    monkeypatch.setattr(run_matsim.summarise_run, 'summarise',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'process',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'mirror',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'trim', lambda *a, **k: None)
    monkeypatch.setattr(run_matsim, 'extract_metrics', lambda *a, **k: True)
    monkeypatch.setattr(run_matsim.registry, 'load', lambda *a, **k: {})
    return d


def record(d):
    return json.loads((d / '_run.json').read_text(encoding='utf-8'))


def test_a_clean_shutdown_at_the_horizon_is_a_result(orphan):
    doc = run_matsim.close_out_orphan(orphan.name)
    assert doc is not None
    rec = record(orphan)
    assert rec['completion'] == run_matsim.RAN_TO_LAST
    assert rec['reached_iteration'] == 12
    assert rec['rc'] == 0
    assert rec['closed_out_by'] == 'run.py --close-out'
    meta = json.loads((orphan / '_meta.json').read_text(encoding='utf-8'))
    assert meta['status'] == 'completed'
    assert meta['ended'] is not None and meta['wall_s'] > 0


def test_the_pace_is_read_from_the_log_not_the_digest(orphan):
    # the digest holds one 240 s iteration from before the harness died; the
    # log holds twelve 240 s ones - the record must not be built from the
    # digest's horizon, and the median must come from every iteration that ran
    run_matsim.close_out_orphan(orphan.name)
    assert record(orphan)['median_iteration_s'] == pytest.approx(240.0)
    per = run_matsim._iteration_times_from_log(str(orphan / 'matsim.log'))
    assert max(per) == 12


def test_a_survivable_throwable_does_not_refuse_a_clean_run(orphan):
    # Guice's `Unsupported class file major version` is in the log and is the
    # only throwable there; `run_failure.from_log` names it, and it killed
    # nothing - the shutdown marker decides, not the throwable
    assert run_matsim.run_failure.from_log(str(orphan / 'matsim.log'))
    assert run_matsim.close_out_orphan(orphan.name) is not None


def test_a_live_run_is_refused(orphan, monkeypatch):
    monkeypatch.setattr(run_matsim, '_pid_alive', lambda pid: True)
    with pytest.raises(SystemExit, match='still running'):
        run_matsim.close_out_orphan(orphan.name)
    assert not (orphan / '_run.json').exists()


def test_a_run_short_of_its_horizon_is_refused(orphan):
    (orphan / 'matsim.log').write_text(_log(9), encoding='utf-8')
    with pytest.raises(SystemExit, match='short of its declared 12'):
        run_matsim.close_out_orphan(orphan.name)
    assert not (orphan / '_run.json').exists()


def test_a_log_without_the_clean_shutdown_is_refused(orphan):
    (orphan / 'matsim.log').write_text(_log(12, clean=False), encoding='utf-8')
    with pytest.raises(SystemExit, match='clean shutdown'):
        run_matsim.close_out_orphan(orphan.name)


def test_an_unexpected_shutdown_is_refused_even_after_the_marker(orphan):
    (orphan / 'matsim.log').write_text(_log(12, unexpected=True),
                                       encoding='utf-8')
    with pytest.raises(SystemExit, match='clean shutdown'):
        run_matsim.close_out_orphan(orphan.name)


def test_a_record_that_is_not_running_is_left_alone(orphan):
    card = json.loads((orphan / '_meta.json').read_text(encoding='utf-8'))
    card['status'] = 'completed'
    (orphan / '_meta.json').write_text(json.dumps(card), encoding='utf-8')
    with pytest.raises(SystemExit, match='not a stale running record'):
        run_matsim.close_out_orphan(orphan.name)


def test_a_short_digest_is_overruled_by_the_logs_own_tail(orphan):
    """The digest stopped at iteration 1; the JVM ended 12. A record built
    from the digest said the run reached 1 (the pricer then booked the other
    eleven as setup, 16 September 2026)."""
    per = run_matsim.iteration_times(str(orphan / 'matsim.log'))
    assert max(per) == 12, per
    assert run_matsim._last_completed_iteration(str(orphan)) == 12


def test_reconcile_closes_out_a_finished_orphan(orphan, monkeypatch):
    """A run whose log ends in the clean shutdown is a RESULT, not a failure,
    whatever survivable throwable the log carries earlier (9.176)."""
    monkeypatch.setattr(run_matsim, 'RAW', str(orphan.parent))
    monkeypatch.setattr(run_matsim, 'RESULTS', str(orphan.parent / 'none'))
    monkeypatch.setattr(run_matsim, 'mark_dead',
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError('a finished orphan was marked dead')))
    run_matsim.reconcile_stale()
    rec = json.loads((orphan / '_run.json').read_text(encoding='utf-8'))
    assert rec['completion'] == 'ran_to_last_iteration'
    assert rec['reached_iteration'] == 12
