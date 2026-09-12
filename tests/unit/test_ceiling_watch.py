"""An approved cost ceiling that the runner enforces (#169).

Every multi-hour arm is launched against a stated-cost approval, and nothing
enforced it: no `RUN.*` field declared a wall-clock limit and nothing read one.
The only mechanism that ever stopped an arm was `start_gate_watch`, which stops
on a MODELLING condition and knows nothing about clocks — so
`20260909T015217_300it_25pct`, which disables that watcher by a scoped and
correct departure, ran for twenty hours with no automatic stop of any kind.

These tests exercise the watcher itself rather than its source text: a fake
process, a clock already past its ceiling, and the marker and completion that
result. The poll cadence comes from config exactly as it does in a real run, so
the test shrinks it the same way an overlay would. The one that matters most is the default — a run that names no ceiling
must behave exactly as it did before, or this becomes a mechanism that stops
runs nobody asked it to stop.
"""
import io
import json
import os
import time


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import run_matsim as rm  # noqa: E402


class FakeProc:
    """A process that is alive until something kills it."""

    def __init__(self):
        self.killed = False

    def poll(self):
        return 0 if self.killed else None

    def kill(self):
        self.killed = True


class Cfg(dict):
    def get(self, key, default=None):
        if key not in self:
            raise KeyError(key)
        return dict.get(self, key)


FAST = 0.01   # the cadence the watcher reads from config, shrunk for the test


def _wait(proc, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if proc.killed:
            return True
        time.sleep(0.01)
    return False


def test_no_ceiling_is_the_default_and_starts_nothing(tmp_path):
    """A run that names no ceiling must behave exactly as it did before."""
    proc = FakeProc()
    t = rm.start_ceiling_watch(str(tmp_path), Cfg({'RUN.gate.wall_ceiling_h': 0, 'RUN.gate.ceiling_poll_s': FAST}),
                               proc, time.time() - 10_000_000)
    assert t is None, 'zero means no ceiling, so no thread at all'
    time.sleep(0.05)
    assert not proc.killed


def test_a_passed_ceiling_stops_the_run_and_says_so(tmp_path):
    proc = FakeProc()
    started = time.time() - 3600 * 33          # 33 h against a 32 h ceiling
    t = rm.start_ceiling_watch(str(tmp_path), Cfg({'RUN.gate.wall_ceiling_h': 32, 'RUN.gate.ceiling_poll_s': FAST}),
                               proc, started)
    assert t is not None
    assert _wait(proc), 'the watcher must kill a run past its ceiling'

    marker = tmp_path / rm.CEILING_STOP
    assert marker.exists(), 'the marker is written BEFORE the kill (9.143)'
    doc = json.loads(io.open(marker, encoding='utf-8').read())
    assert doc['ceiling_h'] == 32
    assert doc['wall_s'] > 32 * 3600


def test_a_ceiling_not_yet_reached_leaves_the_run_alone(tmp_path):
    proc = FakeProc()
    t = rm.start_ceiling_watch(str(tmp_path), Cfg({'RUN.gate.wall_ceiling_h': 32, 'RUN.gate.ceiling_poll_s': FAST}),
                               proc, time.time() - 60)
    assert t is not None
    time.sleep(0.1)
    assert not proc.killed, 'one minute in is not thirty-two hours in'
    assert not (tmp_path / rm.CEILING_STOP).exists()


def test_the_stop_is_read_back_as_its_own_boundary(tmp_path):
    """A run stopped on COST is not a crash, a gate stop or an operator stop."""
    io.open(tmp_path / rm.CEILING_STOP, 'w', encoding='utf-8').write(json.dumps(
        {'stopped': '2026-09-09T12:00:00', 'ceiling_h': 32,
         'wall_s': 118800.0, 'reached_iteration': 214}))
    cause, completion = rm._stop_marker(str(tmp_path))
    assert completion == rm.STOPPED_AT_CEILING
    assert 'ceiling' in cause and '32' in cause
    assert '214' in cause, 'the cause names where it got to, so it can be cited'


def test_a_gate_breach_is_described_before_a_budget(tmp_path):
    """A run that hit both is described by the more informative boundary."""
    io.open(tmp_path / rm.CEILING_STOP, 'w', encoding='utf-8').write(json.dumps(
        {'ceiling_h': 32, 'wall_s': 118800.0, 'reached_iteration': 214}))
    io.open(tmp_path / rm.GATE_STOP, 'w', encoding='utf-8').write(json.dumps(
        {'iteration': 200, 'interval': 100, 'breaches': ['heavy_rail'],
         'gate': ['GATE: 1 mode(s) at or past the stop bar']}))
    _, completion = rm._stop_marker(str(tmp_path))
    assert completion == rm.STOPPED_AT_GATE


def test_a_ceiling_stop_can_never_satisfy_resume(tmp_path, monkeypatch):
    """9.143: only ran_to_last_iteration is a complete arm."""
    assert rm.STOPPED_AT_CEILING != rm.RAN_TO_LAST


def test_the_completion_is_in_the_output_schema():
    """A record the schema rejects is a record nobody can validate."""
    schema = json.loads(io.open(
        os.path.join(REPO, 'config', 'schema', 'outputs', 'run.schema.json'),
        encoding='utf-8').read())
    enum = schema['properties']['completion']['enum']
    assert rm.STOPPED_AT_CEILING in enum
