"""The progress digest reads the bytes that arrived, not the log (#131).

The digest called a whole-file reader twice every thirty seconds. On a 25 % arm
whose log reaches tens of gigabytes that is a decoded read of the entire log per
cycle, competing with the JVM for the same disk - and the gate watcher shares
the reader, so the cost is paid twice.

`run_view._read_markers` was made incremental. Issue #131 then asked for the
close condition to be MEASURED on a 25 % arm: bytes read against the log's
growth over the same interval. That is a property of the reader, not of any
city, any sample fraction or any arm, so it is measured here instead - by
counting the bytes the reader actually pulls off disk. An arm can confirm it; it
is not needed to establish it, and waiting for one left a fixed defect open.
"""

from __future__ import annotations

import builtins
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]

import run_view                                                   # noqa: E402


BEGIN = ('2026-09-09T02:%02d:00,000  INFO AbstractController:1 '
         '### ITERATION %d BEGINS\n')
ENDS = ('2026-09-09T02:%02d:30,000  INFO AbstractController:1 '
        '### ITERATION %d ENDS\n')
FILLER = 'x' * 200 + '\n'


def _write_iterations(path, first, last, filler_lines=200):
    """Append iterations to a log, padded so growth is measurable in bytes."""
    with open(path, 'a', encoding='utf-8', newline='\n') as fh:
        for n in range(first, last + 1):
            fh.write(BEGIN % (n % 60, n))
            fh.write(FILLER * filler_lines)
            fh.write(ENDS % (n % 60, n))


class _CountingOpen(object):
    """Wraps builtins.open and totals every byte handed back by read()."""

    def __init__(self):
        self.bytes_read = 0
        self._real = builtins.open

    def __call__(self, *a, **kw):
        fh = self._real(*a, **kw)
        if 'b' not in (a[1] if len(a) > 1 else kw.get('mode', 'r')):
            return fh
        counter = self

        class _Counting(object):
            def __getattr__(self, name):
                return getattr(fh, name)

            def read(self, *ra, **rkw):
                data = fh.read(*ra, **rkw)
                counter.bytes_read += len(data)
                return data

            def __enter__(self):
                fh.__enter__()
                return self

            def __exit__(self, *e):
                return fh.__exit__(*e)

        return _Counting()


@pytest.fixture(autouse=True)
def _clear_cache():
    with run_view._ITER_LOCK:
        run_view._ITER_CACHE.clear()
    yield
    with run_view._ITER_LOCK:
        run_view._ITER_CACHE.clear()


def test_the_second_read_costs_only_what_was_appended(tmp_path, monkeypatch):
    log = tmp_path / 'matsim.log'
    _write_iterations(log, 0, 39)
    first_size = log.stat().st_size

    counter = _CountingOpen()
    monkeypatch.setattr(builtins, 'open', counter)

    run_view.read_iterations(str(log))
    first_pass = counter.bytes_read
    assert first_pass >= first_size, 'the first call must walk the whole log'

    _write_iterations(log, 40, 41)
    growth = log.stat().st_size - first_size
    counter.bytes_read = 0
    run_view.read_iterations(str(log))
    second_pass = counter.bytes_read

    # The close condition, stated as an inequality rather than a ratio so it
    # does not depend on the fixture's size: a cycle reads the GROWTH, not the
    # log. The old whole-file reader would have read first_size + growth here.
    assert second_pass <= growth + 4096, (
        'a later call read %d bytes against %d bytes of growth (the log is %d '
        'bytes): the reader is walking the whole file again'
        % (second_pass, growth, log.stat().st_size))
    assert second_pass < first_pass


def test_an_unchanged_log_is_not_read_at_all(tmp_path, monkeypatch):
    """The common case on a 30 s cycle: nothing was appended since the last
    tick, and the answer is already held."""
    log = tmp_path / 'matsim.log'
    _write_iterations(log, 0, 9)
    run_view.read_iterations(str(log))

    counter = _CountingOpen()
    monkeypatch.setattr(builtins, 'open', counter)
    run_view.read_iterations(str(log))
    assert counter.bytes_read == 0


def test_both_readers_share_one_walk(tmp_path, monkeypatch):
    """The digest reads iterations and the gate watcher reads spans. If they
    did not share a cache the cost would be paid twice per cycle, which is the
    other half of what #131 measured."""
    log = tmp_path / 'matsim.log'
    _write_iterations(log, 0, 9)
    run_view.read_iterations(str(log))

    counter = _CountingOpen()
    monkeypatch.setattr(builtins, 'open', counter)
    run_view.read_iteration_spans(str(log))
    assert counter.bytes_read == 0


def test_a_restarted_log_is_re_read_from_the_top(tmp_path):
    """A new run in the same directory shrinks the log; a saved offset into the
    old one would silently skip the new run's first iterations."""
    log = tmp_path / 'matsim.log'
    _write_iterations(log, 0, 19)
    assert run_view.read_iterations(str(log))

    log.write_text('', encoding='utf-8')
    _write_iterations(log, 0, 2)
    again = run_view.read_iterations(str(log))
    assert [n for n, _ in again] == [0, 1, 2]


def test_the_incremental_answer_equals_the_whole_file_answer(tmp_path):
    """Cheaper is only better if it is the same. Read a log in one pass, then
    read the same log in three, and require identical output."""
    one = tmp_path / 'one.log'
    _write_iterations(one, 0, 29)
    whole = run_view.read_iterations(str(one))

    piece = tmp_path / 'piece.log'
    _write_iterations(piece, 0, 9)
    run_view.read_iterations(str(piece))
    _write_iterations(piece, 10, 19)
    run_view.read_iterations(str(piece))
    _write_iterations(piece, 20, 29)
    incremental = run_view.read_iterations(str(piece))

    assert [n for n, _ in incremental] == [n for n, _ in whole]
