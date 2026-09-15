"""`--trend` takes a finished iteration from the run's own memo, never a stale one.

A --trend read used to re-derive every readable iteration on every call - ten
minutes of the arm's own CPU at 25 iterations, paid twenty times by the
session that monitored the routers pair (DECISIONS.md 9.176). An iteration's
reading does not change once its tables are written, so it is memoised on
disk under `<run>/_trend/`, keyed by the tables' stamps and the reader's own
source. These tests pin the keying: a rewritten table or a changed reader
re-derives; an unchanged one is served; --no-cache is the caller's override.
"""
import json
import os
import time

import report_mode_ridership as rmr


def _run(tmp_path, it=5):
    d = tmp_path / '20260915T000704_250it_25pct'
    iters = d / 'output' / 'ITERS' / ('it.%d' % it)
    iters.mkdir(parents=True)
    (iters / ('%d.trips.csv.gz' % it)).write_bytes(b'x' * 10)
    return d


def _fill_last():
    rmr.LAST.clear()
    rmr.LAST.update(dict(
        iteration=5, modelled={'car': 60.0, 'walk': 12.0},
        targets={'car': 50.0, 'walk': 10.0}, truck_target=None,   # synthetic, not a target
        run='20260915T000704_250it_25pct', fraction=0.25, source='trips table',
        rows=[dict(mode='car', basis='share'), dict(mode='walk', basis='share')]))


def test_a_memo_is_written_and_served_back(tmp_path):
    d = _run(tmp_path)
    _fill_last()
    doc = rmr.write_memo(str(d), 5, False, 'reader-a')
    assert (d / '_trend' / 'it.5.json').exists()
    back = rmr.read_memo(str(d), 5, False, 'reader-a')
    assert back is not None
    assert back['modelled'] == doc['modelled'] == {'car': 60.0, 'walk': 12.0}
    assert back['basis'] == {'car': 'share', 'walk': 'share'}


def test_a_changed_reader_invalidates_the_memo(tmp_path):
    d = _run(tmp_path)
    _fill_last()
    rmr.write_memo(str(d), 5, False, 'reader-a')
    assert rmr.read_memo(str(d), 5, False, 'reader-b') is None


def test_a_rewritten_table_invalidates_the_memo(tmp_path):
    d = _run(tmp_path)
    _fill_last()
    rmr.write_memo(str(d), 5, False, 'reader-a')
    table = d / 'output' / 'ITERS' / 'it.5' / '5.trips.csv.gz'
    table.write_bytes(b'y' * 20)                       # a different size
    assert rmr.read_memo(str(d), 5, False, 'reader-a') is None


def test_the_stations_basis_has_its_own_memo(tmp_path):
    d = _run(tmp_path)
    _fill_last()
    rmr.write_memo(str(d), 5, True, 'reader-a')
    assert rmr.read_memo(str(d), 5, False, 'reader-a') is None
    assert rmr.read_memo(str(d), 5, True, 'reader-a') is not None


def test_the_reader_stamp_is_a_hash_of_the_reader(tmp_path):
    a = rmr._reader_stamp()
    assert len(a) == 16 and a == rmr._reader_stamp()
