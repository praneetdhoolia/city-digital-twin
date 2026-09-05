"""A run that ends at a DEFINED BOUNDARY closes itself out; a crash does not.

`src/run/run_matsim.py:close_out` writes the record and the summary for a run
that ended rather than died - one that reached its declared last iteration, one
the gate watcher stopped under the GOAL.md loop, and one the operator stopped
through `run.py --stop`. Before it existed the record was written on rc=0 alone,
so every arm since family F4 - each of which stopped at its gate, which is what
the gate is FOR - left a directory holding a real reading and nothing that could
cite it, and the next session re-derived its figures from a 51 GiB log.

What the record's presence means is therefore narrower than it was, and these
tests pin the narrowing: presence means THIS RUN CAN BE CITED, `completion`
says which boundary ended it, and only `ran_to_last_iteration` means the run
executed the horizon it declared. The record is written through the declared
output schema, so a close-out that cannot state its identity fails here rather
than producing a record nothing downstream can trust.

The tests build a run directory under `tmp_path` from the launch card the
runner actually writes. Nothing under `results/` is read or written: the two
post-run side effects (`summarise_run`, `results_store`) are stubbed, because
what is under test is the RECORD, not the summary it triggers.
"""
import json
import os
import pathlib
import time
from types import SimpleNamespace

import pytest

import run_matsim


# Real controller lines: the timestamp carries milliseconds after a COMMA, which
# is what `TS_RE` matches. A fixture without them parses to no iterations at all
# and every pace and reached-iteration assertion below silently tests the
# fallback instead of the thing it names.
LOG = """
2026-09-04T10:00:00,000  INFO AbstractController:137 ### ITERATION 0 BEGINS
2026-09-04T10:05:00,000  INFO AbstractController:184 ### ITERATION 0 ENDS
2026-09-04T10:05:00,000  INFO AbstractController:137 ### ITERATION 1 BEGINS
2026-09-04T10:10:00,000  INFO AbstractController:184 ### ITERATION 1 ENDS
2026-09-04T10:10:00,000  INFO AbstractController:137 ### ITERATION 2 BEGINS
"""


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    """A launched run's directory: the card the runner writes, and a log.

    The card carries everything the record needs (`config_snapshot`,
    `values_sha256`, `sample`) because the process that closes a stopped run out
    cannot reach the locals `build_config` produced - for an operator stop it is
    a different process entirely.
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
    (d / '_meta.json').write_text(json.dumps(card), encoding='utf-8')
    (d / 'matsim.log').write_text(LOG, encoding='utf-8')
    # The digest reports an iteration that has BEGUN. Here it claims 100 while
    # the log's ENDS markers stop at 1 - exactly the state the first arm closed
    # out this way was stopped in, and the record must say 1, not 100.
    (d / '_progress.json').write_text(json.dumps({'iteration': 100}),
                                      encoding='utf-8')
    # the record is what is under test; the summary and the store are not
    monkeypatch.setattr(run_matsim.summarise_run, 'summarise',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'process',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'trim', lambda *a, **k: None)
    return d


def written(d):
    return json.loads((d / '_run.json').read_text(encoding='utf-8'))


# --------------------------------------------------------------------------
# the boundary is recorded, and it is recorded as what it was
# --------------------------------------------------------------------------
def test_a_gate_stop_is_closed_out_with_a_record(run_dir):
    doc = run_matsim.close_out(str(run_dir), run_matsim.STOPPED_AT_GATE,
                               rc=1, wall_s=3600.0,
                               stop_cause='ride -40.1% at iteration 100')
    assert doc is not None
    assert (run_dir / '_run.json').exists(), (
        'the gate stop left no record: the reading the gate was taken for '
        'cannot be cited')
    assert written(run_dir)['completion'] == 'stopped_at_gate'


def test_the_record_states_the_LAST_ENDED_iteration_never_the_one_in_flight(run_dir):
    # The progress digest says 100; the log's ENDS markers stop at 1. Recording
    # the digest's figure would claim the run reached a milestone whose tables
    # were never written and send a reader somewhere that holds nothing - which
    # is exactly what happened to the first arm closed out this way, stopped
    # while iteration 100 was in flight with 90 the newest readable milestone.
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_AT_GATE, rc=1,
                         wall_s=3600.0, stop_cause='past the bar')
    assert written(run_dir)['reached_iteration'] == 1


def test_the_stop_cause_is_carried_verbatim(run_dir):
    cause = 'Stopped automatically by the gate watcher at iteration 100'
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_AT_GATE, rc=1,
                         wall_s=1.0, stop_cause=cause)
    assert written(run_dir)['stop_cause'] == cause


def test_an_operator_stop_is_recorded_as_one(run_dir):
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_BY_OPERATOR,
                         rc=None, wall_s=None, stop_cause='stopped by hand')
    doc = written(run_dir)
    assert doc['completion'] == 'stopped_by_operator'
    # --stop kills the harness holding the clock, so no process observed a
    # return code; recording a made-up one would state what the run did not
    assert doc['rc'] is None


def test_an_operator_stop_takes_its_wall_clock_from_the_launch_stamp(run_dir):
    # the elapsed time is the cost the arm actually spent, not zero
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_BY_OPERATOR,
                         rc=None, wall_s=None, stop_cause='stopped by hand')
    assert written(run_dir)['wall_s'] >= 0.0


# --------------------------------------------------------------------------
# the record still states the run's full identity
# --------------------------------------------------------------------------
def test_a_stopped_run_states_the_same_identity_a_complete_one_does(run_dir):
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_AT_GATE, rc=1,
                         wall_s=1.0, stop_cause='past the bar')
    doc = written(run_dir)
    # a reading that cannot say what produced it is not citable either
    for key in ('scenario', 'day', 'fraction', 'iterations', 'threads', 'seed',
                'controler_sha256', 'values_sha256', 'inputs_sha256',
                'config_snapshot'):
        assert doc.get(key) is not None, '%s missing from a stopped record' % key
    assert doc['controler_sha256'] == 'c' * 64
    assert doc['persons_kept'] == 250


def test_the_record_is_named_for_the_directory_that_holds_it(run_dir):
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_AT_GATE, rc=1,
                         wall_s=1.0, stop_cause='past the bar')
    assert written(run_dir)['name'] == run_dir.name


def test_the_declared_horizon_is_kept_beside_what_was_reached(run_dir):
    # `iterations` stays what the run DECLARED; `reached_iteration` is what it
    # got to. Collapsing the two would hide that the arm was cut short.
    run_matsim.close_out(str(run_dir), run_matsim.STOPPED_AT_GATE, rc=1,
                         wall_s=1.0, stop_cause='past the bar')
    doc = written(run_dir)
    assert doc['iterations'] == 300
    assert doc['reached_iteration'] == 1


# --------------------------------------------------------------------------
# a run that cannot state what it was gets no record
# --------------------------------------------------------------------------
def test_a_directory_without_a_card_is_not_closed_out(tmp_path, monkeypatch):
    d = tmp_path / 'no-card'
    d.mkdir()
    monkeypatch.setattr(run_matsim.summarise_run, 'summarise',
                        lambda *a, **k: None)
    assert run_matsim.close_out(str(d), run_matsim.STOPPED_AT_GATE, rc=1,
                                wall_s=1.0) is None
    assert not (d / '_run.json').exists(), (
        'a record was manufactured for a directory that cannot say what it ran')


def test_the_record_must_meet_its_declared_schema(run_dir):
    # `completion` is an ENUM, so a close-out that cannot name its boundary
    # writes nothing rather than a record readers cannot classify.
    #
    # The enum lives in the JSON schema, and `src/registry/outputs.py` treats
    # jsonschema as OPTIONAL - the unit job installs only pytest and pandas, so
    # there the structural rules run and the schema does not. Skipping keeps
    # this test about close_out's behaviour rather than about which optional
    # dependency the runner happens to have.
    pytest.importorskip('jsonschema')
    assert run_matsim.close_out(str(run_dir), 'not-a-boundary', rc=1,
                                wall_s=1.0) is None
    assert not (run_dir / '_run.json').exists()


# --------------------------------------------------------------------------
# the operator stop, end to end
#
# `--stop` is the one sanctioned way a person ends an arm (9.137), and it is the
# path an arm approved only as far as its gate is ended on. It runs in its OWN
# process - it kills the harness's pid as well as the JVM, so nothing survives
# there to write a record - which is why the close-out has to happen inside
# stop_run rather than in the harness's unwind.
# --------------------------------------------------------------------------
@pytest.fixture
def stoppable(run_dir, monkeypatch):
    """`run_dir` wired so stop_run can act on it without killing anything."""
    killed = []
    monkeypatch.setattr(run_matsim.results_store, 'resolve',
                        lambda name: str(run_dir))
    monkeypatch.setattr(run_matsim.results_store, 'rename',
                        lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.results_store, 'mirror', lambda *a, **k: None)
    monkeypatch.setattr(run_matsim.subprocess, 'run',
                        lambda cmd, **k: killed.append(cmd))
    monkeypatch.setattr(run_matsim.time, 'sleep', lambda s: None)
    return SimpleNamespace(dir=run_dir, killed=killed,
                           name='20260904T100000_300it_25pct')


def read_json(run_dir, filename):
    return json.loads(
        (pathlib.Path(run_dir) / filename).read_text(encoding='utf-8'))


def test_stop_run_closes_the_arm_out(stoppable):
    cause = 'stopped at the approved iteration-100 gate'
    dead = run_matsim.stop_run(stoppable.name, cause)
    doc = read_json(dead, '_run.json')
    assert doc['completion'] == 'stopped_by_operator'
    assert doc['stop_cause'] == cause
    assert doc['reached_iteration'] == 1, (
        'the reading has to say which iteration it belongs to, and that is the '
        'last one that ENDED - not the one the digest saw begin')


def test_stop_run_kills_the_jvm_and_the_harness(stoppable):
    run_matsim.stop_run(stoppable.name, 'stopped')
    # both pids: killing the harness alone once left the JVM running (#128)
    assert len(stoppable.killed) == 2


def test_stop_run_records_the_cause_on_the_card_too(stoppable):
    cause = 'stopped at the approved gate'
    dead = run_matsim.stop_run(stoppable.name, cause)
    meta = read_json(dead, '_meta.json')
    assert meta['status'] == 'aborted'
    assert cause in (meta.get('cause') or '')


def test_stop_run_refuses_a_run_that_is_not_running(stoppable):
    card = read_json(stoppable.dir, '_meta.json')
    card['status'] = 'completed'
    (stoppable.dir / '_meta.json').write_text(json.dumps(card),
                                              encoding='utf-8')
    with pytest.raises(SystemExit):
        run_matsim.stop_run(stoppable.name, 'stopped')
