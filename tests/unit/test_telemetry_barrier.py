"""Telemetry has no memory barrier of its own, so the run refuses to lose it.

`RunTelemetry` writes its per-vehicle array and its per-mode maps from the
event-handler threads and reads and clears them from the QSim thread, with no
`volatile`, no `synchronized` and no `java.util.concurrent` type anywhere in
its 731 lines. The only thing that publishes those writes is the sim-step
barrier - `RUN.machine.events_synchronize_on_simsteps`, MATSim's
`eventsManager.synchronizeOnSimSteps`. A committed overlay turned it off.

The failure that would cause is the worst shape a defect takes here: no crash,
just torn or stale counters that the progress digest reports as a measurement.
So the combination is refused before the JVM starts, and again in the dry run,
rather than made safe with atomics on the highest-frequency path in the
simulation - the barrier is measured FASTER on this model anyway (9.59).

These tests pin the refusal and, as importantly, pin that it does NOT fire on
an ordinary run (#151, DECISIONS.md 9.151).
"""
import pytest

import run_matsim


class Cfg:
    """The smallest thing that answers `.get` the way the resolver does."""

    def __init__(self, **values):
        self._values = values

    def get(self, key):
        return self._values.get(key)


def test_refuses_when_the_barrier_is_off():
    cfg = Cfg(**{'RUN.machine.telemetry_requires_simstep_barrier': True,
                 'RUN.machine.events_synchronize_on_simsteps': False})
    with pytest.raises(SystemExit) as exc:
        run_matsim.refuse_unsafe_telemetry(cfg)
    message = str(exc.value)
    # The refusal has to name both fields: whoever hits it is holding an
    # overlay and needs to know which knob to put back.
    assert 'RUN.machine.events_synchronize_on_simsteps' in message
    assert 'RUN.machine.telemetry_requires_simstep_barrier' in message
    assert '#151' in message


def test_allows_the_ordinary_run():
    """The declared value of the barrier is true, and that must stay silent."""
    cfg = Cfg(**{'RUN.machine.telemetry_requires_simstep_barrier': True,
                 'RUN.machine.events_synchronize_on_simsteps': True})
    assert run_matsim.refuse_unsafe_telemetry(cfg) is None


def test_allows_the_barrier_off_once_telemetry_is_made_safe():
    """The refusal is not a ban on the async path - it is a ban on the async
    path WHILE the telemetry depends on the barrier. Declaring the dependency
    false is the documented way through, and it must actually work, or the
    field is decoration."""
    cfg = Cfg(**{'RUN.machine.telemetry_requires_simstep_barrier': False,
                 'RUN.machine.events_synchronize_on_simsteps': False})
    assert run_matsim.refuse_unsafe_telemetry(cfg) is None
