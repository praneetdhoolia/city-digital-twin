"""Resume detection matches a run's IDENTITY, never its directory label.

`src/run/run_matsim.py:find_completed` decides whether a launch is a no-op. A
false match hands back somebody else's result under this launch's parameters,
and nothing downstream can tell the two apart afterwards - which is why the
identity grew from the parameter set to the controler source (issue #28), the
resolved registry values (9.104) and the population the run sampled from
(9.127). Each of those was added because a match on too little had already
produced an untraceable result once.

The tests lay out fake run directories under `tmp_path` with realistic
`_run.json` records and point the module's three search roots at them, so
nothing under `results/` is read or written. No MATSim, no package.
"""
import json
import os

import pytest

import results_store
import run_matsim


CONTROLER = 'c' * 64
VALUES = 'v' * 64
INPUTS = 'i' * 64


def record(**over):
    """A completed run's record, as the runner writes it."""
    doc = dict(name='a-stale-label', scenario='S0', day='WEEKDAY',
               fraction=0.25, iterations=300, seed=20260810, threads=1,
               overrides={}, rc=0, wall_s=1.0,
               controler_sha256=CONTROLER, values_sha256=VALUES,
               inputs_sha256=INPUTS,
               config_snapshot='_config.json')
    doc.update(over)
    return doc


@pytest.fixture
def store(tmp_path, monkeypatch):
    """The three roots `find_completed` searches, all inside tmp_path."""
    raw = tmp_path / 'raw'
    processed = tmp_path / 'processed'
    legacy = tmp_path / 'legacy'
    for d in (raw, processed, legacy):
        d.mkdir()
    monkeypatch.setattr(run_matsim, 'RAW', str(raw))
    monkeypatch.setattr(run_matsim, 'RESULTS', str(legacy))
    monkeypatch.setattr(results_store, 'PROCESSED', str(processed))

    def put(where, name, doc):
        run_dir = os.path.join(str(where), name)
        os.makedirs(run_dir, exist_ok=True)
        with open(os.path.join(run_dir, '_run.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(doc, f)
        return run_dir

    put.raw, put.processed, put.legacy = raw, processed, legacy
    return put


def find(**over):
    """The query the runner makes for the fixture record's own parameters."""
    kw = dict(scenario='S0', day='WEEKDAY', fraction=0.25, iterations=300,
              seed=20260810, overrides={}, controler=CONTROLER,
              warm_key=None, values=VALUES, inputs=INPUTS)
    kw.update(over)
    return run_matsim.find_completed(**kw)


# --------------------------------------------------------------------------
# the match itself
# --------------------------------------------------------------------------
def test_an_identical_record_matches(store):
    store(store.raw, '20260901T000000_300it_25pct', record())
    assert find() is not None


def test_the_returned_name_is_the_directory_that_holds_the_record(store):
    # directories are renameable labels; a record must never point a caller at
    # a name its directory no longer carries
    store(store.raw, '20260901T000000_300it_25pct', record(name='a-stale-label'))
    assert find()['name'] == '20260901T000000_300it_25pct'


def test_a_record_in_processed_is_found(store):
    store(store.processed, '20260901T000000_300it_25pct', record())
    assert find() is not None


def test_a_record_under_the_legacy_root_is_found(store):
    store(store.legacy, '20260901T000000_300it_25pct', record())
    assert find() is not None


def test_no_record_at_all_is_no_match(store):
    assert find() is None


def test_an_unreadable_record_is_skipped_not_raised(store):
    run_dir = os.path.join(str(store.raw), 'broken')
    os.makedirs(run_dir)
    with open(os.path.join(run_dir, '_run.json'), 'w', encoding='utf-8') as f:
        f.write('{ this is not json')
    store(store.raw, '20260901T000000_300it_25pct', record())
    assert find() is not None


# --------------------------------------------------------------------------
# every part of the parameter set is part of the identity
# --------------------------------------------------------------------------
@pytest.mark.parametrize('field,value', [
    ('scenario', 'S1'),
    ('day', 'SAT'),
    ('fraction', 0.10),
    ('iterations', 100),
    ('seed', 1),
])
def test_a_different_parameter_is_a_different_run(store, field, value):
    store(store.raw, '20260901T000000_300it_25pct', record(**{field: value}))
    assert find() is None


def test_a_different_override_set_is_a_different_run(store):
    store(store.raw, '20260901T000000_300it_25pct',
          record(overrides={'X.fixture.field': -1.0}))
    assert find() is None


def test_an_empty_override_set_and_none_are_the_same_run(store):
    store(store.raw, '20260901T000000_300it_25pct', record(overrides=None))
    assert find(overrides=None) is not None


def test_a_warm_started_run_does_not_answer_a_cold_query(store):
    # the RNG stream and the travel-time memory reset at the checkpoint, so the
    # two are different results
    store(store.raw, '20260901T000000_300it_25pct',
          record(warm_started_from='20260801T000000_300it_25pct'))
    assert find(warm_key=None) is None


def test_a_cold_run_does_not_answer_a_warm_query(store):
    store(store.raw, '20260901T000000_300it_25pct', record())
    assert find(warm_key='20260801T000000_300it_25pct') is None


def test_only_a_completed_run_can_be_resumed(store):
    store(store.raw, '20260901T000000_300it_25pct', record(rc=1))
    assert find() is None


# --------------------------------------------------------------------------
# the hashes: 9.104 (the resolved values) and 9.127 (the population)
# --------------------------------------------------------------------------
def test_a_changed_values_hash_does_not_match(store):
    # two run overlays differing in ONE declared value are the same parameter
    # set here, and the second would otherwise inherit the first's result
    store(store.raw, '20260901T000000_300it_25pct',
          record(values_sha256='0' * 64))
    assert find() is None


def test_a_changed_inputs_hash_does_not_match(store):
    # a rebuilt demand under the same parameters is a different run
    store(store.raw, '20260901T000000_300it_25pct',
          record(inputs_sha256='0' * 64))
    assert find() is None


@pytest.mark.parametrize('missing', ['values_sha256', 'inputs_sha256'])
def test_a_record_that_carries_no_hash_never_matches(store, missing):
    # a record written before the hash was tracked cannot PROVE it used the same
    # inputs: a re-run costs time, a false resume costs a finding
    doc = record()
    doc.pop(missing)
    store(store.raw, '20260901T000000_300it_25pct', doc)
    assert find() is None


def test_a_hash_the_caller_does_not_ask_about_is_not_compared(store):
    doc = record()
    doc.pop('values_sha256')
    doc.pop('inputs_sha256')
    store(store.raw, '20260901T000000_300it_25pct', doc)
    assert find(values=None, inputs=None) is not None


# --------------------------------------------------------------------------
# the controler source, which no parameter set can see
# --------------------------------------------------------------------------
def test_a_changed_controler_is_offered_only_as_a_fallback(store):
    store(store.raw, '20260901T000000_300it_25pct',
          record(controler_sha256='0' * 64))
    prior = find()
    assert prior is not None
    assert prior['controler_sha256'] != CONTROLER, (
        'the caller re-runs on this, and only knows to because the record says '
        'the controler changed')


def test_a_matching_controler_wins_over_a_newer_record_that_does_not_match(store):
    store(store.raw, '20260902T000000_300it_25pct',
          record(controler_sha256='0' * 64))
    store(store.raw, '20260901T000000_300it_25pct', record())
    prior = find()
    assert prior['name'] == '20260901T000000_300it_25pct'
    assert prior['controler_sha256'] == CONTROLER


def test_the_newest_matching_record_supersedes_an_older_one(store):
    store(store.raw, '20260901T000000_300it_25pct', record(wall_s=1.0))
    store(store.raw, '20260902T000000_300it_25pct', record(wall_s=2.0))
    assert find()['name'] == '20260902T000000_300it_25pct'


def test_a_caller_that_asks_about_no_controler_takes_the_newest(store):
    store(store.raw, '20260901T000000_300it_25pct',
          record(controler_sha256='0' * 64))
    assert find(controler=None) is not None


# --------------------------------------------------------------------------
# only a run that REACHED ITS HORIZON can be resumed
#
# A run stopped at a GOAL.md gate is now closed out with a `_run.json` of its
# own, so presence alone stopped being the test. Without the `completion`
# filter, relaunching the very overlay whose arm the gate stopped would print
# `resume: already complete` and run nothing - the session would read a stopped
# arm as a finished one, which is the failure the whole record exists to
# prevent.
# --------------------------------------------------------------------------
@pytest.mark.parametrize('completion', ['stopped_at_gate',
                                        'stopped_by_operator'])
def test_a_stopped_run_never_satisfies_resume(store, completion):
    store(store.raw, '20260901T000000_300it_25pct',
          record(completion=completion, reached_iteration=100,
                 stop_cause='ride -40.1% at the iteration-100 gate'))
    assert find() is None, (
        'a %s arm answered a launch of the same parameters: the relaunch '
        'would have run nothing' % completion)


def test_a_run_that_reached_its_horizon_still_resumes(store):
    store(store.raw, '20260901T000000_300it_25pct',
          record(completion='ran_to_last_iteration', reached_iteration=300))
    assert find() is not None


def test_a_record_written_before_the_field_existed_still_resumes(store):
    # every record without `completion` was written on rc=0 and only on rc=0,
    # so a missing value reads as ran_to_last_iteration - the historical
    # records on disk must not stop matching because the field was added
    doc = record()
    assert 'completion' not in doc
    store(store.raw, '20260901T000000_300it_25pct', doc)
    assert find() is not None


def test_a_stopped_run_does_not_shadow_a_complete_one(store):
    # newest first: the stopped arm is the newer directory, and skipping it
    # must not also skip the completed run behind it
    store(store.raw, '20260901T000000_300it_25pct', record())
    store(store.raw, '20260902T000000_300it_25pct',
          record(completion='stopped_at_gate', reached_iteration=100))
    prior = find()
    assert prior is not None
    assert prior['name'] == '20260901T000000_300it_25pct'
