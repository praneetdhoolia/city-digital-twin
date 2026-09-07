"""The trim guard keeps a run inside its extraction window and no longer (9.155).

The #132 guard - keep any raw directory that has a `_run.json` and no
`_metrics.json` - was written for a race that lasts seconds and had no expiry,
so it protected forever every run that will NEVER get a `_metrics.json`:
`run.py` writes that file after `run()` returns, and an operator stop or a gate
stop kills the harness before it does. Measured 7 September 2026: 13
directories, 72.8 GiB, 16% of a 90%-full cache, and when the cap was hit the
store skipped all thirteen and deleted younger COMPLETE runs instead.

Both halves are pinned here, because fixing the leak must not re-open the race.
"""
import json
import os
import time

import pytest

from src.run import results_store


def _run_dir(root, name, *, metrics, age_s, completion='stopped_by_operator'):
    """A raw run directory with a record written `age_s` ago."""
    d = os.path.join(root, name)
    os.makedirs(d)
    with open(os.path.join(d, '_meta.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(status='aborted', pid=None), fh)
    with open(os.path.join(d, '_run.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(name=name, completion=completion), fh)
    if metrics:
        with open(os.path.join(d, '_metrics.json'), 'w', encoding='utf-8') as fh:
            json.dump({}, fh)
    # bulk, so the directory has something to reclaim
    with open(os.path.join(d, 'matsim.log'), 'w', encoding='utf-8') as fh:
        fh.write('x' * 4096)
    when = time.time() - age_s
    for fname in os.listdir(d):
        os.utime(os.path.join(d, fname), (when, when))
    return d


@pytest.fixture()
def store(tmp_path, monkeypatch):
    raw = tmp_path / 'raw'
    processed = tmp_path / 'processed'
    raw.mkdir()
    processed.mkdir()
    monkeypatch.setattr(results_store, 'RAW', str(raw))
    monkeypatch.setattr(results_store, 'PROCESSED', str(processed))
    monkeypatch.setattr(results_store, 'RESULTS', str(tmp_path))
    # trim() mirrors and extracts before deleting; neither is under test here
    monkeypatch.setattr(results_store, 'process', lambda name, extract=False: None)
    return raw


def test_record_age_reads_the_record_not_the_directory(store):
    d = _run_dir(str(store), 'r_old', metrics=False, age_s=7200)
    age = results_store._record_age_s(d)
    assert age is not None
    assert age >= 7000, 'the age comes from the record files, not the dir mtime'


def test_a_fresh_stop_is_kept_the_132_race(store):
    """A run whose harness may still be writing _metrics.json is never deleted."""
    _run_dir(str(store), 'r_fresh', metrics=False, age_s=5)
    deleted = results_store.trim(0, log=lambda *a: None, grace_s=3600)
    assert deleted == [], 'a run inside its extraction window must survive'
    assert os.path.isdir(os.path.join(str(store), 'r_fresh'))


def test_a_closed_out_stop_is_reclaimed_past_the_grace(store):
    """The measured leak: a stop that will never get _metrics.json."""
    _run_dir(str(store), 'r_stale', metrics=False, age_s=7200)
    deleted = results_store.trim(0, log=lambda *a: None, grace_s=3600)
    assert [d['name'] for d in deleted] == ['r_stale']
    assert not os.path.isdir(os.path.join(str(store), 'r_stale'))


def test_the_guard_does_not_outrank_a_younger_complete_run(store):
    """What the leak actually cost: the store deleted the young and kept the old.

    Oldest-first, both past the grace, so the stopped arm goes first - it is
    older - and the complete run survives to the next call.
    """
    _run_dir(str(store), '20260101T000000_a', metrics=False, age_s=7200)
    _run_dir(str(store), '20260601T000000_b', metrics=True, age_s=7200)
    deleted = results_store.trim(0.000001, log=lambda *a: None, grace_s=3600)
    assert deleted, 'something must be reclaimable'
    assert deleted[0]['name'] == '20260101T000000_a', (
        'the oldest goes first; the guard must not make an unextractable run '
        'outrank a younger complete one')


def test_trim_refuses_to_invent_the_grace(store):
    """The store resolves no declared value itself; its caller supplies them."""
    with pytest.raises(TypeError, match='extract_grace_s'):
        results_store.trim(0, log=lambda *a: None)
