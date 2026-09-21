"""A run named at a fraction below 1 % is still a run (9.206).

The runner names a directory `<stamp>_<it>it_<%g of fraction x 100>pct`, so
`RUN.sample.fraction` 0.001 gives `..._0.1pct`. The board's runs block and the
issue gate's run-name reader both required `\\d+pct`, so the first citywide
Mumbai case was invisible to the board for a session while the board said
`results/INDEX.md` labelled every run.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
for p in (ROOT, os.path.join(ROOT, 'src'), os.path.join(ROOT, 'src', 'analyse'),
          os.path.join(ROOT, 'src', 'run')):
    if p not in sys.path:
        sys.path.insert(0, p)

import build_status_board                                       # noqa: E402
import issue_gate                                               # noqa: E402


def test_the_board_sees_a_decimal_percentage_run():
    for name in ('20260921T220701_2it_0.1pct', 'aborted_20260921T220524_2it_0.1pct',
                 '20260921T231313_4it_1pct', '20260916T063903_250it_25pct',
                 '20260921T165718_2it_100pct-mumbai-smoke'):
        assert build_status_board.RUN_DIR.match(name), name
    assert not build_status_board.RUN_DIR.match('20260921T220701_2it_pct')
    assert not build_status_board.RUN_DIR.match('20260921T220701_2it_.1pct')


def test_the_issue_gate_reads_a_decimal_percentage_run_name():
    text = 'AWAITING-RUN: read on 20260921T220701_2it_0.1pct and 20260916T063903_250it_25pct'
    assert issue_gate.RUN_NAME.findall(text) == ['20260921T220701_2it_0.1pct',
                                                 '20260916T063903_250it_25pct']
