"""The viewer's congestion measure on a payload written before the telemetry
measured delay this way: the qsim's one-second step is not delay, a stub is
judged over a map app's segment, and a real queue stays red."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'analyse'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import run_view  # noqa: E402


def test_one_second_on_a_stub_is_flowing():
    # a 10 m stub at 50 km/h: free-flow 0.72 s; a mean traversal of 1.7 s is the step, not a queue
    ff, v = 10 / 13.9, 13.9
    assert run_view.delay_ratio(1.7 / ff, ff, v) == 1.0


def test_a_queue_on_a_stub_is_judged_over_a_segment():
    ff, v = 10 / 13.9, 13.9
    # 30 s per traversal on the same stub: 29 s of delay over the 10.8 s a 150 m stretch takes
    r = run_view.delay_ratio(30 / ff, ff, v)
    assert abs(r - (1 + (30 - ff - 1) / (150 / 13.9))) < 1e-9
    assert r > run_view.RAMP_MAX * 0.6   # deep into red: a real queue stays a queue


def test_a_long_link_uses_its_own_free_flow():
    ff, v = 1000 / 27.8, 27.8          # a kilometre of 100 km/h road, 36 s free-flow
    assert abs(run_view.delay_ratio(2.0, ff, v) - (1 + (ff - 1) / ff)) < 1e-9


def test_no_speed_reads_flowing():
    assert run_view.delay_ratio(5.0, 0.0, 0.0) == 1.0
