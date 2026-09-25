"""A JVM alive under a dead harness is a run nobody is watching, and the gate says so.

The routers pair `20260915T000704_250it_25pct` ran 22 hours with its harness
dead (DECISIONS.md 9.176, #225): the digest said BUSY because a java process
was alive, `stale_running` stayed quiet because the JVM's pid counted as the
run being alive, and the harness's own heartbeat (`_progress.json`) had stopped
at iteration 34 with nobody comparing its age to its interval. Meanwhile no
ceiling, stall or gate watcher ran and nothing was going to write the record.

`run_failure.orphaned_running` is the direct test - the harness pid is dead
and the log is fresh - and `--check` goes red on it, so the next session sees
it first. These tests pin what it reports and what it leaves alone.
"""
import json
import os
import time

import pytest

import run_failure


def _run(tmp_path, name, status='running', pid=999999991, log_age_s=10):
    d = tmp_path / 'raw' / name
    d.mkdir(parents=True)
    (d / '_meta.json').write_text(json.dumps(dict(status=status, pid=pid)),
                                  encoding='utf-8')
    log = d / 'matsim.log'
    log.write_text('2026-09-15T00:08:12,068  INFO MemoryObserver:43 used RAM\n',
                   encoding='utf-8')
    t = time.time() - log_age_s
    os.utime(log, (t, t))
    return d


def test_a_dead_harness_under_a_fresh_log_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(run_failure, 'card_pid_alive',
                        lambda card, key: False)
    _run(tmp_path, '20260915T000704_250it_25pct', log_age_s=10)
    found = run_failure.orphaned_running(str(tmp_path))
    assert [(n, pid) for n, pid, _ in found] == [
        ('20260915T000704_250it_25pct', 999999991)]


def test_a_live_harness_is_left_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(run_failure, 'card_pid_alive',
                        lambda card, key: True)
    _run(tmp_path, '20260915T000704_250it_25pct', log_age_s=10)
    assert run_failure.orphaned_running(str(tmp_path)) == []


def test_a_dead_harness_under_a_silent_log_is_the_stale_case_not_this_one(tmp_path, monkeypatch):
    # the JVM stopped writing too: that is `stale_running`'s finding (both
    # dead), settled by reconcile or a close-out, and must not be reported twice
    monkeypatch.setattr(run_failure, 'card_pid_alive',
                        lambda card, key: False)
    _run(tmp_path, '20260915T000704_250it_25pct',
         log_age_s=run_failure.LOG_FRESH_S + 60)
    assert run_failure.orphaned_running(str(tmp_path)) == []
    assert [n for n, _ in run_failure.stale_running(str(tmp_path))] == [
        '20260915T000704_250it_25pct']


def test_a_completed_record_is_not_looked_at(tmp_path, monkeypatch):
    monkeypatch.setattr(run_failure, 'card_pid_alive',
                        lambda card, key: False)
    _run(tmp_path, '20260915T000704_250it_25pct', status='completed')
    assert run_failure.orphaned_running(str(tmp_path)) == []
