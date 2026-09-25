"""A run the host will restart under is not launched.

Windows Update restarted the host at 04:30 on 24 September 2026 and killed
F36's arm 0 at iteration 237 of 250. The launcher refuses a staged restart,
and a run whose cost ceiling outlasts the update pause.
"""
import time

import pytest

import procs
import run_matsim


class Cfg(dict):
    get = dict.get


def test_a_pending_restart_is_refused(monkeypatch):
    monkeypatch.setattr(procs, 'restart_pending', lambda: True)
    with pytest.raises(SystemExit, match='restart pending'):
        run_matsim.refuse_unsafe_host(Cfg({'RUN.gate.wall_ceiling_h': 1.0}))


def test_a_pause_shorter_than_the_ceiling_is_refused(monkeypatch):
    monkeypatch.setattr(procs, 'restart_pending', lambda: False)
    monkeypatch.setattr(procs, 'updates_paused_until', lambda: time.time() + 3600)
    with pytest.raises(SystemExit, match='paused only until'):
        run_matsim.refuse_unsafe_host(Cfg({'RUN.gate.wall_ceiling_h': 34.0}))


def test_no_pause_is_refused_and_says_what_to_click(monkeypatch):
    monkeypatch.setattr(procs, 'restart_pending', lambda: False)
    monkeypatch.setattr(procs, 'updates_paused_until', lambda: 0)
    with pytest.raises(SystemExit, match='Pause updates'):
        run_matsim.refuse_unsafe_host(Cfg({'RUN.gate.wall_ceiling_h': 1.0}))


def test_a_pause_past_the_ceiling_launches(monkeypatch):
    monkeypatch.setattr(procs, 'restart_pending', lambda: False)
    monkeypatch.setattr(procs, 'updates_paused_until', lambda: time.time() + 7 * 86400)
    run_matsim.refuse_unsafe_host(Cfg({'RUN.gate.wall_ceiling_h': 34.0}))


def test_a_host_without_windows_update_has_nothing_to_guard(monkeypatch):
    monkeypatch.setattr(procs, 'restart_pending', lambda: None)
    monkeypatch.setattr(procs, 'updates_paused_until', lambda: None)
    run_matsim.refuse_unsafe_host(Cfg({'RUN.gate.wall_ceiling_h': 34.0}))
