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

**An interval is not a gate (9.164, #131).** The gate watcher reads what the
monitor maintains and refuses to arm without it, so an interval declared beside
`RUN.monitor.enabled = false` is a stop that does not exist. It was measured
that way: `20260910T205517_20it_1pct` declared an interval of 2, reached
iteration 3, and wrote no verdict, no gate line and no warning of any kind.
This refusal counted such a run as protected because it read the interval
alone, so the third field is now part of the same question.
"""
import pytest

import run_matsim


class _Cfg:
    """The three fields the refusal reads, in the shape `cfg.get` returns them."""

    def __init__(self, interval, ceiling, monitor=True):
        self._d = {'RUN.gate.interval_iterations': interval,
                   'RUN.gate.wall_ceiling_h': ceiling,
                   'RUN.monitor.enabled': monitor}

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


def test_a_gate_interval_without_the_monitor_is_not_a_stop():
    """The measured state: interval declared, monitor off, nothing judged."""
    with pytest.raises(SystemExit) as exc:
        run_matsim.refuse_if_no_automatic_stop(_Cfg(2, 0, monitor=False))
    msg = str(exc.value)
    assert 'RUN.monitor.enabled' in msg, (
        'the refusal does not name the field that made the gate inert, so the '
        'operator is told to fix the wrong one')
    assert '#131' in msg


def test_the_ceiling_alone_still_protects_a_run_with_no_monitor():
    """A probe may legitimately run unmonitored and unjudged, on a budget."""
    run_matsim.refuse_if_no_automatic_stop(_Cfg(2, 0.05, monitor=False))


def test_unreadable_fields_are_treated_as_off_not_as_present():
    """A missing or malformed field must not be read as a stop that exists.

    Defaulting an unparseable value to "a stop is configured" would let a typo
    buy back exactly the state this refusal exists to prevent.
    """
    for interval, ceiling in ((None, None), ('', ''), ('abc', 'xyz')):
        with pytest.raises(SystemExit):
            run_matsim.refuse_if_no_automatic_stop(_Cfg(interval, ceiling))
