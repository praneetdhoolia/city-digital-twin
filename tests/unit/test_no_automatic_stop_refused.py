"""A run that can stop itself on nothing is refused before the JVM starts (#169).

Two independent stops exist and they have different owners: the gate watcher
stops on the MODEL being wrong (`RUN.gate.interval_iterations`), the ceiling
watcher on the RUN being expensive (`RUN.gate.wall_ceiling_h`). Either is a
boundary. Neither is one when both are off, and that state is not hypothetical:
`depth_convergence_25pct` disabled the gate watcher for a recorded and
defensible reason (9.159) and declared no ceiling, so its approved 32 h was
held by a person watching a clock while the arm ran 21.5 h unattended.

The launcher otherwise never refuses a launch, and these tests pin that: every
configuration that keeps ONE stop must still be allowed, because turning the
gate watcher off stays entirely legitimate. Only the state with no stop at all
is refused.

**An interval is a gate again (9.206).** From 9.164 (#131) the refusal also
read `RUN.monitor.enabled`, because the watcher reads what the monitor
maintains and an interval declared beside a disabled monitor was a stop that
did not exist (`20260910T205517_20it_1pct`). Since 9.206 the monitor serves on
every run and the field is retired, so the question is the two stops again.
"""
import pytest

import run_matsim


class _Cfg:
    """The two fields the refusal reads, in the shape `cfg.get` returns them."""

    def __init__(self, interval, ceiling):
        self._d = {'RUN.gate.interval_iterations': interval,
                   'RUN.gate.wall_ceiling_h': ceiling}

    def get(self, key):
        return self._d.get(key)


def test_no_stop_of_either_kind_is_refused():
    with pytest.raises(SystemExit) as exc:
        run_matsim.refuse_if_no_automatic_stop(_Cfg(0, 0))
    msg = str(exc.value)
    # the refusal has to say WHICH stops are off, or the operator cannot act
    assert 'RUN.gate.interval_iterations' in msg
    assert 'RUN.gate.wall_ceiling_h' in msg
    assert '#169' in msg


@pytest.mark.parametrize('interval,ceiling,why', [
    (100, 0, 'the default: the gate watcher stops it on the model'),
    (0, 32.0, 'the depth-arm shape, now with the ceiling its approval named'),
    (100, 32.0, 'both stops declared'),
    (100, 0.0, 'a float zero ceiling is still no ceiling, gate carries it'),
])
def test_one_stop_is_enough(interval, ceiling, why):
    # must not raise: the launcher refuses only the state with no stop at all
    run_matsim.refuse_if_no_automatic_stop(_Cfg(interval, ceiling)), why


def test_a_gate_interval_is_a_stop_on_its_own():
    """The monitor serves on every run (9.206), so the interval alone protects."""
    run_matsim.refuse_if_no_automatic_stop(_Cfg(2, 0))


def test_the_ceiling_alone_still_protects_an_unjudged_run():
    """A probe may legitimately run unjudged, on a budget."""
    run_matsim.refuse_if_no_automatic_stop(_Cfg(0, 0.05))
