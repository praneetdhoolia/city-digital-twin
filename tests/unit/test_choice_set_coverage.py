"""The choice-set coverage bound, and the two ways it can be quoted wrongly.

`report_choice_set_coverage.py` states an ARITHMETIC bound: a scoring constant
reallocates between plans an agent already holds, so a mode's plan-holding
coverage is the most its share can ever be. Two things make that bound a lie if
they are not handled, and both are here as tests because both were live in this
repository when the reader was written:

1. A mode that is a person-level LOCKED carve (motorbike, truck) is not a member
   of the mode-choice strategy's alternative set, so the coverage table never
   describes it and its share legitimately exceeds its "coverage". Printing a
   negative headroom there would be an instrument reporting on something it is
   not attached to.

2. A target stated on a different denominator (heavy rail and light rail are
   boardings per weekday) cannot be bounded by a coverage percentage at all.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src' / 'analyse'))
sys.path.insert(0, str(REPO / 'src'))

import report_choice_set_coverage as cov                          # noqa: E402


COVERAGE = (
    'Iteration\tbike\tcar\tmotorbike\tpt\tride\ttaxi\ttruck\twalk\n'
    '0\t0.05\t0.40\t0.0023\t0.05\t0.04\t0.11\t0.0415\t0.26\n'
    '1\t0.10\t0.51\t0.0023\t0.11\t0.10\t0.22\t0.0415\t0.42\n'
    '2\t0.29\t0.77\t0.0023\t0.25\t0.20\t0.54\t0.0415\t0.63\n'
)


@pytest.fixture()
def run_dir(tmp_path):
    out = tmp_path / 'output'
    out.mkdir(parents=True)
    (out / 'modeChoiceCoverage1x.txt').write_text(COVERAGE, encoding='utf-8')
    (tmp_path / '_metrics.json').write_text(json.dumps({
        'reached_iteration': 2,
        'mode_share': {'target_lga_pct': {
            'bike': 4.70, 'car': 64.91, 'motorbike': 0.43, 'pt': 4.64,
            'ride': 12.16, 'taxi': 3.00, 'truck': 0.31, 'walk': 9.85}},
    }), encoding='utf-8')
    return tmp_path


def test_reads_matsims_own_table(run_dir):
    table = cov.read_coverage(str(run_dir))
    assert sorted(table) == [0, 1, 2]
    assert table[2]['car'] == pytest.approx(0.77)


def test_headroom_is_coverage_minus_share(run_dir, capsys):
    out = cov.report(str(run_dir))
    assert out['modes']['ride']['coverage_pct'] == pytest.approx(20.0)
    assert out['modes']['ride']['share_pct'] == pytest.approx(12.16)
    assert out['modes']['ride']['headroom_pct'] == pytest.approx(7.84)


def test_a_locked_carve_gets_no_bound(run_dir):
    """motorbike's share (0.43 %) exceeds its 'coverage' (0.23 %) because the
    rider holds no alternative. The reader must say so, not print -0.19 %."""
    out = cov.report(str(run_dir))
    for mode in cov.LOCKED_MODES:
        assert out['modes'][mode]['locked_carve'] is True
        assert 'headroom_pct' not in out['modes'][mode], (
            '%s is a locked carve: mode-choice coverage does not bound it'
            % mode)
    assert out['modes']['car']['locked_carve'] is False


def test_share_and_coverage_must_come_from_one_iteration(run_dir):
    """A coverage reading at one iteration beside a share reading from another
    is the defect the reader exists to report, one layer up."""
    shares, at = cov.read_shares(str(run_dir), 1)
    assert shares is None and at == 2


def test_a_boardings_target_is_not_bounded_by_a_percentage():
    # Synthetic values throughout: this is framework test, and no city's own
    # target belongs in it (the city-agnostic rule, and `check_hardcoding.py`
    # reads a bare decimal pair here as a coordinate typed into a script).
    bus_target, ferry_target = 2.0, 1.0
    targets = {
        'bus': {'target': bus_target, 'denominator': cov.SHARE_DENOMINATOR,
                'on_trip_share': True},
        'ferry': {'target': ferry_target, 'denominator': cov.SHARE_DENOMINATOR,
                  'on_trip_share': True},
        'heavy_rail': {'target': 6000.0,
                       'denominator': 'boardings per weekday',
                       'on_trip_share': False},
    }
    verdict = cov._reachable('pt', 25.0, targets)
    # only the two trip-share submodes may enter the sum
    assert verdict['target'] == pytest.approx(bus_target + ferry_target)
    assert verdict['reachable'] is True
    assert 'boardings' in verdict['text']


def test_an_unreachable_target_is_reported_as_unreachable():
    targets = {'ride': {'target': 30.0, 'denominator': cov.SHARE_DENOMINATOR,
                        'on_trip_share': True}}
    verdict = cov._reachable('ride', 20.0, targets)
    assert verdict['reachable'] is False
    assert 'NO' in verdict['text']


def test_a_run_with_no_coverage_table_refuses(tmp_path):
    (tmp_path / 'output').mkdir()
    with pytest.raises(SystemExit) as e:
        cov.read_coverage(str(tmp_path))
    assert 'modeChoiceCoverage1x.txt' in str(e.value)
