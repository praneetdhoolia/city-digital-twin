"""`compare_runs` refuses the comparisons the project's own rules refuse.

The tool exists because every timing decision in the record was assembled by
hand out of `stopwatch.csv`, and a hand comparison is how a figure quietly gets
made across a family boundary and quoted without the caveat. The blockers are
the point of the tool, so they are pinned here.
"""
import pytest

from src.analyse import compare_runs as C


def run(**kw):
    base = dict(name='r', family='F30-x', fraction=0.25, threads=16,
                event_handler_threads=4, profiled=False, completion=None,
                iterations=4, scenario='S2', day='WEEKDAY')
    base.update(kw)
    return base


def test_same_family_same_fraction_same_recorder_is_comparable():
    assert C.blockers(run(), run(name='b')) == []


def test_a_family_boundary_blocks_the_comparison():
    """DECISIONS.md 3.5 - nothing before a boundary compares with anything after."""
    out = C.blockers(run(family='F28-a'), run(family='F30-b'))
    assert len(out) == 1
    assert 'DIFFERENT COMPARABILITY FAMILIES' in out[0]
    assert '3.5' in out[0]


def test_a_different_sample_fraction_blocks_the_comparison():
    out = C.blockers(run(fraction=0.10), run(fraction=0.25))
    assert any('SAMPLE FRACTIONS' in b for b in out)


def test_a_profiled_side_against_an_unprofiled_one_blocks():
    """The recorder is ~8% of the clock - larger than most knobs measured."""
    out = C.blockers(run(profiled=True), run(profiled=False))
    assert any('PROFILED' in b for b in out)


def test_blockers_accumulate():
    out = C.blockers(run(family='F28-a', fraction=0.10, profiled=True),
                     run(family='F30-b', fraction=0.25, profiled=False))
    assert len(out) == 3


def test_an_unknown_family_does_not_invent_a_blocker():
    """A run whose family the index cannot attribute is not silently blocked -
    the tool reports what it knows and says nothing it does not."""
    assert C.blockers(run(family=None), run(family='F30-b')) == []


def test_differences_name_the_knob_being_measured():
    diffs = C.differences(run(event_handler_threads=4),
                          run(event_handler_threads=2))
    assert diffs == ['event handler threads: 4 -> 2']


def test_the_iteration_index_survives_the_phase_of_the_same_name():
    """`iteration` is both column 0 (the index) and the last column (the total);
    a reader that keys by name silently loses the index."""
    rows = [{'index': 0, 'iteration': 443}, {'index': 1, 'iteration': 394},
            {'index': 2, 'iteration': 310}]
    assert [r['index'] for r in C.window(rows, None)] == [1, 2], \
        'iteration 0 pays JIT warm-up and is dropped by default'
    assert [r['index'] for r in C.window(rows, '0:1')] == [0, 1]


def test_median_ignores_missing_phases():
    assert C.median([None, 4, None, 6]) == 5
    assert C.median([None, None]) is None
