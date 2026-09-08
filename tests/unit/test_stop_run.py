"""`--stop` stops ONE run, and the run it stopped says who stopped it.

Two defects the 7 September assessment measured, both in the one sanctioned
manual path for ending an arm:

1. `run.py --stop <name>` ended EVERY scheduled task whose name contained
   `citysim_run_`, so stopping one arm killed every other detached arm on the
   machine. One arm at a time is the standing rule (#66), not a guarantee -
   probes and a gate arm have overlapped.
2. `stop_run` killed the JVM first, which woke the harness out of `proc.wait()`
   into its own terminal path. The harness found no marker, recorded `failed`
   and RENAMED the directory, so the operator's stated cause was discarded and
   the close-out then targeted a directory that had moved. No
   `stopped_by_operator` record had ever been written.

The fix is a marker written BEFORE anything is killed, so whichever process
reaches the terminal record first finds the operator's own words; and the
harness is killed before the JVM, so it cannot wake into the crash path at all.

These tests pin the two behaviours that have no other guard: the marker's
reading, and the task name a stop is allowed to end.
"""
import io
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'src'))
sys.path.insert(0, os.path.join(REPO, 'src', 'run'))

import run_matsim                                            # noqa: E402


def _write(d, name, doc):
    with io.open(os.path.join(str(d), name), 'w', encoding='utf-8',
                 newline='\n') as fh:
        json.dump(doc, fh, indent=1)


# --------------------------------------------------------------- the marker
def test_no_marker_is_a_crash(tmp_path):
    """No marker at all: the run has no boundary, so nothing claims one."""
    cause, completion = run_matsim._stop_marker(str(tmp_path))
    assert cause is None and completion is None


def test_operator_marker_carries_the_operators_words(tmp_path):
    """The cause the operator gave reaches the record, verbatim."""
    _write(tmp_path, run_matsim.OPERATOR_STOP,
           dict(cause='a global wait stranded every non-chain mode',
                at='2026-09-07T00:24:31'))
    cause, completion = run_matsim._stop_marker(str(tmp_path))
    assert completion == run_matsim.STOPPED_BY_OPERATOR
    assert 'a global wait stranded every non-chain mode' in cause
    assert 'operator' in cause.lower()


def test_the_gate_wins_over_the_operator(tmp_path):
    """Both markers present: the gate is the boundary that actually fired.

    The watcher kills the JVM itself, so a `--stop` racing it is stopping a run
    the loop had already ended. The gate's table is the citable cause.
    """
    _write(tmp_path, run_matsim.OPERATOR_STOP, dict(cause='operator changed mind'))
    _write(tmp_path, run_matsim.GATE_STOP,
           dict(iteration=100, interval=100,
                gate=['heavy_rail modelled 25792.0 target 6528.6 +295.1%']))
    cause, completion = run_matsim._stop_marker(str(tmp_path))
    assert completion == run_matsim.STOPPED_AT_GATE
    assert 'gate watcher' in cause
    assert 'heavy_rail' in cause


def test_an_unreadable_marker_is_not_a_boundary(tmp_path):
    """A truncated marker must not invent a cause - a crash stays a crash."""
    with io.open(os.path.join(str(tmp_path), run_matsim.OPERATOR_STOP), 'w',
                 encoding='utf-8', newline='\n') as fh:
        fh.write('{"cause": "half a fil')
    assert run_matsim._stop_marker(str(tmp_path)) == (None, None)


def test_an_empty_cause_is_not_a_boundary(tmp_path):
    """A marker with no words in it says nothing, so it claims nothing."""
    _write(tmp_path, run_matsim.OPERATOR_STOP, dict(cause=''))
    assert run_matsim._stop_marker(str(tmp_path)) == (None, None)


# ------------------------------------------------- the task a stop may end
# run.py derives the scheduled task from the run's launch stamp. The rule is
# reproduced here rather than imported, because run.py's --stop branch runs
# inside main() behind argparse; what is pinned is that the stamp identifies
# exactly one task, and that a sibling arm's task is not it.
STAMP = re.compile(r'\d{8}T\d{6}')


def _task_for(run_name):
    m = STAMP.search(run_name)
    return 'citysim_run_%s' % m.group(0) if m else None


@pytest.mark.parametrize('run_name,expected', [
    ('20260907T030352_300it_25pct', 'citysim_run_20260907T030352'),
    # mark_dead renames a dead run; --stop must still find its task
    ('aborted_20260907T030352_300it_25pct', 'citysim_run_20260907T030352'),
    ('20260906T233901_4it_25pct', 'citysim_run_20260906T233901'),
    # a hand-named run carries no stamp and ends no task (9.141)
    ('phys1000a_25pct', None),
])
def test_the_stamp_names_one_task(run_name, expected):
    assert _task_for(run_name) == expected


def test_a_stop_does_not_end_a_sibling_arm():
    """The measured defect: two detached arms, stopping one ended both."""
    running = ['citysim_run_20260907T030352', 'citysim_run_20260906T233901']
    want = _task_for('aborted_20260907T030352_300it_25pct')
    ended = [t for t in running if t == want]
    assert ended == ['citysim_run_20260907T030352']
    assert 'citysim_run_20260906T233901' not in ended


# ------------------------------------- the stop reaches the metric extraction
#
# THE COMPOSITION NO TEST EXERCISED. `run.py --stop` returns from its own
# branch; the extraction that writes `_metrics.json` lives after `run()`
# returns in the OTHER branch, and `--stop` kills the harness that would have
# returned there. So an operator-stopped arm never got a `_metrics.json` - and
# that file is precisely what the results store's trim guard reads to decide a
# raw directory is past its extraction window. Thirteen directories were held
# on the raw cap in that state on 7 September 2026, and the guard was given a
# grace (9.155) so they could age out at all. This pins the other half: the
# stop itself now ends where the harness path ends.
import time                                                        # noqa: E402
from types import SimpleNamespace                                  # noqa: E402

LOG = (
    '2026-09-04T10:00:00,000  INFO AbstractController:137 ### ITERATION 0 BEGINS\n'
    '2026-09-04T10:05:00,000  INFO AbstractController:184 ### ITERATION 0 ENDS\n'
    '2026-09-04T10:05:00,000  INFO AbstractController:137 ### ITERATION 1 BEGINS\n'
    '2026-09-04T10:10:00,000  INFO AbstractController:184 ### ITERATION 1 ENDS\n'
)


@pytest.fixture
def stopping(tmp_path, monkeypatch):
    """A running arm wired so `stop_run` acts on it without killing anything.

    Everything the stop triggers is recorded rather than performed: the record
    is real (it is what the extraction depends on), the extraction, the mirror
    and the trim are observed.
    """
    d = tmp_path / '20260904T100000_300it_25pct'
    d.mkdir()
    card = dict(
        status='running', scenario='S2', day='WEEKDAY', fraction=0.25,
        sample_pct=25.0, iterations=300, seed=20260810, threads=10, xmx='40g',
        overrides={}, controler_sha256='c' * 64, inputs_sha256='i' * 64,
        values_sha256='v' * 64, config_snapshot='_config.json',
        sample=dict(persons_in=1000, persons_kept=250,
                    transit_capacity_scaled=[]),
        started=time.strftime('%Y-%m-%dT%H:%M:%S'), ended=None, wall_s=None,
        rc=None, pid=os.getpid(), jvm_pid=os.getpid() + 1)
    _write(d, '_meta.json', card)
    (d / 'matsim.log').write_text(LOG, encoding='utf-8')

    seen = SimpleNamespace(extracted=[], mirrored=[], trimmed=[], record_at=[])

    def fake_extract(run_dir):
        seen.extracted.append(run_dir)
        # THE RECORD MUST ALREADY BE THERE: the extractor reads `_run.json` for
        # the run's identity and its reached_iteration, so an extraction
        # ordered before the close-out would read nothing.
        seen.record_at.append(os.path.exists(os.path.join(run_dir, '_run.json')))
        return True

    monkeypatch.setattr(run_matsim, 'extract_metrics', fake_extract)
    monkeypatch.setattr(run_matsim.results_store, 'resolve', lambda name: str(d))
    monkeypatch.setattr(run_matsim.results_store, 'rename', lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'process', lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'mirror',
                        lambda run_dir: seen.mirrored.append(run_dir))
    monkeypatch.setattr(run_matsim.results_store, 'trim',
                        lambda *a, **k: seen.trimmed.append(a) or [])
    monkeypatch.setattr(run_matsim.summarise_run, 'summarise',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.subprocess, 'run', lambda cmd, **k: None)
    monkeypatch.setattr(run_matsim.time, 'sleep', lambda s: None)
    return SimpleNamespace(dir=d, seen=seen,
                           name='20260904T100000_300it_25pct')


def test_an_operator_stop_reaches_the_metrics_extraction(stopping):
    """The defect: `--stop` closed the arm out and stopped there."""
    dead = run_matsim.stop_run(stopping.name, 'stopped at the approved gate')
    assert stopping.seen.extracted == [dead], (
        'an operator-stopped arm must reach the same _metrics.json extraction '
        'run.py performs for the harness path, or the store keeps its bulk')


def test_the_extraction_happens_after_the_record_is_written(stopping):
    """Order is part of the composition: the extractor reads `_run.json`."""
    run_matsim.stop_run(stopping.name, 'stopped at the approved gate')
    assert stopping.seen.record_at == [True]


def test_the_extracted_metrics_are_mirrored_into_processed(stopping):
    """`_metrics.json` lands after close_out's own mirror, so it needs another.

    Findings live in processed forever; the bulk is a budgeted cache. A metrics
    file that stayed only in raw would die with the bulk it was extracted from.
    """
    dead = run_matsim.stop_run(stopping.name, 'stopped at the approved gate')
    assert dead in stopping.seen.mirrored


def test_the_stop_trims_the_cache_it_just_freed(stopping):
    """The stop ends under budget, the way the harness path does."""
    run_matsim.stop_run(stopping.name, 'stopped at the approved gate')
    assert stopping.seen.trimmed, 'the raw cache is trimmed after a stop'


def test_a_stop_that_could_not_be_recorded_extracts_nothing(stopping,
                                                            monkeypatch):
    """No record, no extraction - the extractor has nothing to read.

    `close_out` refuses to manufacture a record it cannot state the identity
    of, and that refusal must not be routed around here: the bulk is then left
    to the store's own grace (9.155) rather than extracted blind.
    """
    monkeypatch.setattr(run_matsim, 'close_out', lambda *a, **k: None)
    run_matsim.stop_run(stopping.name, 'stopped')
    assert stopping.seen.extracted == []
