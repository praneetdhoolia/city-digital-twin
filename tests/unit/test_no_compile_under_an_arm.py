"""`.tools/classes` must not be recompiled while an arm is running.

"One arm at a time; never recompile `.tools/classes` while one runs" (#66) is a
hard constraint in `.claude/CLAUDE.md`, and until 9 September 2026 there was
nothing behind it. `session_gate.py` skips its toolchain step while an arm is
up, but that guard lives in the CALLER: running
`src/setup/bootstrap_toolchain.py --verify` directly recompiled under a live
arm, and "verify" reads as a read-only word - the trap DECISIONS.md 9.156
already recorded. It was breached on 8 September at the cost of a probe.

The predicate now lives in the thing that does the damage. These tests pin the
two behaviours that decide whether it helps: that a running arm refuses, and
that an UNKNOWN process list also refuses. The second is the one that matters -
treating "I could not tell" as "idle" is exactly how the compile ran.
"""
import sys

import pytest


import bootstrap_toolchain as bt


@pytest.fixture(autouse=True)
def _no_force(monkeypatch):
    """The override must not be in argv while the default is under test."""
    monkeypatch.setattr(sys, 'argv', ['bootstrap_toolchain.py', '--verify'])


def test_a_running_arm_refuses_the_compile(monkeypatch, capsys):
    monkeypatch.setattr(bt, 'arm_running', lambda: ['pid 30748 (31229 MB)'])
    assert bt.refuse_if_arm_running('compile the citysim classes') is True
    out = capsys.readouterr().out
    assert 'REFUSING' in out and '30748' in out, (
        'the refusal must name the process, so an operator can tell an arm '
        'from a language server')


def test_an_unknown_process_list_counts_as_busy(monkeypatch, capsys):
    """The failure mode that produced the breach."""
    monkeypatch.setattr(bt, 'arm_running', lambda: None)
    assert bt.refuse_if_arm_running('compile the citysim classes') is True
    assert 'UNKNOWN COUNTS AS BUSY' in capsys.readouterr().out


def test_an_idle_machine_compiles(monkeypatch):
    monkeypatch.setattr(bt, 'arm_running', lambda: [])
    assert bt.refuse_if_arm_running('compile the citysim classes') is False


def test_force_compile_is_the_deliberate_override(monkeypatch):
    """An operator who knows the big JVM is not an arm must still be able to
    build - the guard is a default, not a lock."""
    monkeypatch.setattr(sys, 'argv',
                        ['bootstrap_toolchain.py', '--force-compile'])
    monkeypatch.setattr(bt, 'arm_running', lambda: ['pid 1 (99999 MB)'])
    assert bt.refuse_if_arm_running('compile the citysim classes') is False


def test_the_threshold_separates_an_arm_from_a_language_server():
    """A classifier, not a model value - and it must sit between the two."""
    assert 1_000_000 < bt.ARM_RSS_KB < 8_000_000
