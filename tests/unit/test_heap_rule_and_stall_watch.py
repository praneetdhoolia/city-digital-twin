"""The heap rule is evaluated at launch, a silent JVM is stopped, and a warm
start keeps its cutoff (eighth project report, 11 September 2026; #66, #192).

Three findings from one dead arm. `aborted_20260910T222830_300it_25pct` launched
on the registry's 14g default at 25 % although `RUN.machine.xmx`'s own
description carried the rule "9.6 GiB + 87 GiB x fraction" — nothing read it;
it then spent 13.1 h inside iteration 89 on an awake machine with the digest
reporting the stall and nothing having the job of killing it; and had it been
resumed from a plans dump, the pinned jar's `first + f x (last - first)` would
have moved its innovation cutoff from 240 to 260. These tests exercise the
three mechanisms, not their source text, and pin the defaults: a heap that
satisfies the rule launches, a run with `stall_kill_s` = 0 starts no watcher,
and a warm start whose derived fraction stays inside the sweep is admitted.
"""
import json
import os
import sys
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (os.path.join(REPO, 'src'), os.path.join(REPO, 'src', 'run')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_matsim as rm  # noqa: E402


class Cfg(dict):
    def get(self, key, default=None):
        if key not in self:
            raise KeyError(key)
        return dict.get(self, key)


class FakeProc:
    def __init__(self):
        self.killed = False

    def poll(self):
        return 0 if self.killed else None

    def kill(self):
        self.killed = True


RULE = {'RUN.machine.heap_floor_gib': 9.6, 'RUN.machine.heap_per_fraction_gib': 87}


# ------------------------------------------------------------- the heap rule

@pytest.mark.parametrize('xmx,gib', [('40g', 40.0), ('14g', 14.0), ('14336m', 14.0),
                                     ('2t', 2048.0), ('1.5G', 1.5)])
def test_a_jvm_heap_string_is_read_in_gib(xmx, gib):
    assert abs(rm.parse_heap_gib(xmx) - gib) < 1e-9


def test_a_heap_that_is_not_a_heap_is_refused():
    with pytest.raises(SystemExit, match='not a JVM heap size'):
        rm.refuse_small_heap(Cfg(RULE), 'forty', 0.25)


def test_the_rule_at_a_quarter_sample_is_the_one_the_dead_arm_broke():
    assert abs(rm.heap_floor_gib(Cfg(RULE), 0.25) - 31.35) < 1e-9


def test_fourteen_gig_at_a_quarter_sample_is_refused_and_names_the_fields():
    with pytest.raises(SystemExit) as e:
        rm.refuse_small_heap(Cfg(RULE), '14g', 0.25)
    msg = str(e.value)
    assert 'RUN.machine.xmx = 14g' in msg and '31.4 GiB' in msg
    assert 'RUN.machine.heap_floor_gib' in msg and 'heap_per_fraction_gib' in msg


def test_forty_gig_at_a_quarter_sample_launches():
    rm.refuse_small_heap(Cfg(RULE), '40g', 0.25)


def test_fourteen_gig_at_one_percent_launches():
    """The default is a probe's heap: 9.6 + 0.87 = 10.5 GiB is under 14g."""
    rm.refuse_small_heap(Cfg(RULE), '14g', 0.01)


# ---------------------------------------------------------- the stall watcher

FAST = 0.01


def _wait(proc, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if proc.killed:
            return True
        time.sleep(0.01)
    return False


def test_zero_disables_the_stall_watcher(tmp_path):
    log = tmp_path / 'matsim.log'
    log.write_text('x')
    t = rm.start_stall_watch(str(tmp_path), Cfg({'RUN.gate.stall_kill_s': 0,
                                                 'RUN.gate.ceiling_poll_s': FAST}),
                             FakeProc(), str(log))
    assert t is None


def test_a_log_that_keeps_writing_is_left_alone(tmp_path):
    log = tmp_path / 'matsim.log'
    log.write_text('x')
    proc = FakeProc()
    rm.start_stall_watch(str(tmp_path), Cfg({'RUN.gate.stall_kill_s': 5,
                                             'RUN.gate.ceiling_poll_s': FAST}),
                         proc, str(log))
    time.sleep(0.1)
    assert not proc.killed
    proc.killed = True   # let the daemon exit


def test_a_silent_log_stops_the_run_and_leaves_the_marker(tmp_path):
    log = tmp_path / 'matsim.log'
    log.write_text('x')
    old = time.time() - 3600
    os.utime(log, (old, old))
    proc = FakeProc()
    rm.start_stall_watch(str(tmp_path), Cfg({'RUN.gate.stall_kill_s': 1800,
                                             'RUN.gate.ceiling_poll_s': FAST}),
                         proc, str(log))
    assert _wait(proc), 'a log silent for an hour against a half-hour bound is a stop'
    marker = json.load(open(tmp_path / rm.STALL_STOP, encoding='utf-8'))
    assert marker['stall_kill_s'] == 1800 and marker['silent_s'] >= 3000
    cause, completion = rm._stop_marker(str(tmp_path))
    assert completion == rm.STOPPED_AT_STALL
    assert 'silent' in cause and 'NOT a complete arm' in cause


def test_the_ceiling_is_read_before_the_stall(tmp_path):
    """A run that hit both boundaries is described by the cost boundary,
    which sits above the liveness boundary in `_stop_marker`'s order."""
    json.dump(dict(stopped='x', ceiling_h=1, wall_s=4000, reached_iteration=3),
              open(tmp_path / rm.CEILING_STOP, 'w', encoding='utf-8'))
    json.dump(dict(stopped='x', stall_kill_s=1800, silent_s=3000, reached_iteration=3),
              open(tmp_path / rm.STALL_STOP, 'w', encoding='utf-8'))
    _, completion = rm._stop_marker(str(tmp_path))
    assert completion == rm.STOPPED_AT_CEILING


# ------------------------------------------------------ the warm-start cutoff

def test_a_warm_start_keeps_the_cutoff_iteration(monkeypatch):
    """f = 0.8 over 0..300 puts the cutoff at 240; resumed at 100 the jar would
    innovate to 100 + 0.8 x 200 = 260, so the fraction is re-derived to 0.7."""
    class Base(dict):
        def get(self, k):
            return self[k]
    base = Base({'RUN.controler.first_iteration': 0,
                 'RUN.controler.last_iteration': 300,
                 'RUN.replanning.fraction_to_disable_innovation': 0.8})
    monkeypatch.setattr(rm.registry, 'load', lambda **kw: base)
    out = rm.warm_start_overrides({'iteration': 100, 'run': 'dead'}, {}, 'S2', 'WEEKDAY', None)
    assert out['RUN.controler.first_iteration'] == 100
    assert abs(out['RUN.replanning.fraction_to_disable_innovation'] - 0.7) < 1e-9


def test_a_checkpoint_at_or_past_the_horizon_is_refused(monkeypatch):
    class Base(dict):
        def get(self, k):
            return self[k]
    base = Base({'RUN.controler.first_iteration': 0,
                 'RUN.controler.last_iteration': 300,
                 'RUN.replanning.fraction_to_disable_innovation': 0.8})
    monkeypatch.setattr(rm.registry, 'load', lambda **kw: base)
    with pytest.raises(SystemExit, match='not below'):
        rm.warm_start_overrides({'iteration': 300, 'run': 'dead'}, {}, 'S2', 'WEEKDAY', None)
