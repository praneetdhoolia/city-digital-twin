"""An arm is priced on the iteration it REPEATS, not on a median over all of them.

`arm_cost.py` used the record's `median_iteration_s`, which is a median over
every iteration a run ran. On a short probe most of those are iterations an arm
pays once: iteration 0 warms the JIT, `dump all plans` fires at iterations 0
and 1 only, and the last iteration writes the run's final output. Measured on
`20260908T014214_4it_25pct`: the record said 282.6 s while the two iterations
that pay only what every iteration pays took 213 s and 219 s - so a 300-
iteration arm was quoted 23.7 h against a measured 18.2 h.

This is trap 4 of the brief, "a median over a phase that fires in some
iterations is not a cost". 9.155 taught `compare_runs.py` to flag it and left
it in the pricer, where it sets what an operator is asked to approve.
"""
import io
import os

import pytest

from src.analyse import arm_cost


HEAD = ('iteration;BEGIN iteration;BEGIN replanning;BEGIN dump all plans;'
        ';iterationStartsListeners;replanning;dump all plans;mobsim;iteration')


def _stopwatch(tmp_path, rows):
    """A run directory holding just the stopwatch the pricer reads."""
    out = os.path.join(str(tmp_path), 'output')
    os.makedirs(out, exist_ok=True)
    with io.open(os.path.join(out, 'stopwatch.csv'), 'w',
                 encoding='utf-8', newline='\n') as fh:
        fh.write(HEAD + '\n')
        for r in rows:
            fh.write(';'.join(r) + '\n')
    return str(tmp_path)


def _row(it, total, dump='', mobsim='00:02:30'):
    return [str(it), '00:00:00', '00:00:00', '00:00:00', '',
            '00:00:00', '00:00:20', dump, mobsim, total]


def test_the_one_off_iterations_are_not_priced_as_recurring(tmp_path):
    d = _stopwatch(tmp_path, [
        _row(0, '00:05:26', dump='00:00:59'),   # warm-up + first dump
        _row(1, '00:04:42', dump='00:01:01'),   # the second and last dump
        _row(2, '00:03:33'),                    # plain
        _row(3, '00:03:39'),                    # plain
        _row(4, '00:05:50'),                    # the final output write
    ])
    pace = arm_cost.plain_iteration_pace(d)
    assert pace['plain_iterations'] == [2, 3]
    assert pace['plain_median_s'] == 216.0
    assert sorted(int(k) for k in pace['one_off_s']) == [0, 1, 4]
    assert pace['last_iteration'] == 4
    # the median the record would have carried, for contrast
    allin = sorted([326, 282, 213, 219, 350])[2]
    assert allin == 282 and pace['plain_median_s'] < allin


def test_a_run_with_no_plain_iteration_prices_nothing(tmp_path):
    """Two iterations that both dump leave nothing that recurs."""
    d = _stopwatch(tmp_path, [
        _row(0, '00:05:26', dump='00:00:59'),
        _row(1, '00:04:42', dump='00:01:01'),
    ])
    assert arm_cost.plain_iteration_pace(d) is None


def test_a_missing_stopwatch_is_not_an_error(tmp_path):
    assert arm_cost.plain_iteration_pace(str(tmp_path)) is None


def test_the_duration_columns_are_read_not_the_clock_stamps(tmp_path):
    """The header repeats its phase names; every lookup must take the LAST."""
    d = _stopwatch(tmp_path, [
        _row(0, '00:05:26', dump='00:00:59'),
        _row(1, '00:04:42', dump='00:01:01'),
        _row(2, '00:03:33'),
        _row(3, '00:03:39'),
        _row(4, '00:05:50'),
    ])
    pace = arm_cost.plain_iteration_pace(d)
    # 00:00:00 is the FIRST 'BEGIN iteration' stamp; reading it would make
    # every iteration look free and every one of them plain.
    assert pace['plain_median_s'] == 216.0
