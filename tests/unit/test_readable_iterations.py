"""The live viewer and the watcher list a run's iterations through the one clamp.

`run_view.readable_iterations` and `watch_run.readable_iterations` each kept
a readable-iterations rule of their own beside `iteration_reading`'s
`citable_iterations` (sixteenth report). Both call it now. A run in flight has
no `_run.json`, so the clamp sets no ceiling and the watcher still sees a
trips table the moment it lands; a stopped run's record clamps what either
offers to its `reached_iteration`. The fixture: trips tables at iterations 1
and 2, experienced plans alone at 3, and a record that arrives later.
"""
import gzip
import json
import os

import pytest

import iteration_reading as reading


@pytest.fixture
def live_run(tmp_path):
    run = tmp_path / '20260101T000000_3it_1pct'
    for it in (1, 2):
        d = run / 'output' / 'ITERS' / ('it.%d' % it)
        d.mkdir(parents=True)
        with gzip.open(str(d / ('%d.trips.csv.gz' % it)), 'wt', encoding='utf-8') as fh:
            fh.write('person;trip_id;main_mode\n')
    d = run / 'output' / 'ITERS' / 'it.3'
    d.mkdir(parents=True)
    with gzip.open(str(d / '3.experienced_plans.xml.gz'), 'wt', encoding='utf-8') as fh:
        fh.write('<population/>\n')
    reading.clear()
    yield str(run)
    reading.clear()


def _stop_at(run, reached):
    with open(os.path.join(run, '_run.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(completion='stopped_by_operator', reached_iteration=reached,
                       iterations=3, rc=0), fh)


def test_watcher_lists_every_landed_table_until_the_record_clamps_it(live_run):
    import watch_run
    assert watch_run.readable_iterations(live_run) == [1, 2]
    # a table that lands mid-watch is listed at the next poll, unclamped
    d = os.path.join(live_run, 'output', 'ITERS', 'it.4')
    os.makedirs(d)
    with gzip.open(os.path.join(d, '4.trips.csv.gz'), 'wt', encoding='utf-8') as fh:
        fh.write('person;trip_id;main_mode\n')
    assert watch_run.readable_iterations(live_run) == [1, 2, 4]
    _stop_at(live_run, 2)
    assert watch_run.readable_iterations(live_run) == [1, 2]


def test_viewer_lists_tables_and_plans_at_or_below_the_record(live_run):
    import run_view
    assert run_view.readable_iterations(live_run) == [1, 2, 3]
    _stop_at(live_run, 1)
    assert run_view.readable_iterations(live_run) == [1]
    # the clamp is iteration_reading's, not a second rule of the viewer's
    assert run_view.readable_iterations(live_run) == reading.citable_iterations(
        live_run, iterations=[1, 2, 3])


def test_progress_digest_resolves_the_run_through_the_store(monkeypatch):
    """`--run` means the same thing in every reader (results_store.resolve_or_die):
    a run the store does not know is refused before any read."""
    import sys
    import progress_digest
    monkeypatch.setattr(sys, 'argv', ['progress_digest.py', '--run', 'no_such_run_20990101', '--once'])
    with pytest.raises(SystemExit, match='no such run'):
        progress_digest.main()
