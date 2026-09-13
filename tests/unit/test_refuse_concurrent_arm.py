"""ONE ARM AT A TIME is refused by the launcher, not remembered by a person.

Two 48 GB heaps on a 63 GB host is the #66 stall class with both arms lost,
and until 14 September 2026 nothing in the launch path asked whether a JVM
big enough to be an arm was already running (ninth report, recommendation 5).
`procs.arm_running` answers; UNKNOWN COUNTS AS BUSY, the rule the compile
guard already applies.
"""
import pytest

import procs
import run_matsim


def test_a_running_arm_refuses_the_launch(monkeypatch):
    monkeypatch.setattr(procs, 'arm_running',
                        lambda *a, **k: ['java.exe pid 4242 rss 41.0 GB'])
    with pytest.raises(SystemExit) as e:
        run_matsim.refuse_concurrent_arm()
    assert 'one arm at a time' in str(e.value)
    assert '4242' in str(e.value)


def test_an_unlistable_process_table_counts_as_busy(monkeypatch):
    monkeypatch.setattr(procs, 'arm_running', lambda *a, **k: None)
    with pytest.raises(SystemExit) as e:
        run_matsim.refuse_concurrent_arm()
    assert 'unknown counts as busy' in str(e.value)


def test_an_idle_machine_launches(monkeypatch):
    monkeypatch.setattr(procs, 'arm_running', lambda *a, **k: [])
    run_matsim.refuse_concurrent_arm()
