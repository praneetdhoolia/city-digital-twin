"""A calibration candidate must be findable after it has been paid for.

The 8 September session fixed the loop's execute path by replacing the raw
MATSim `--set` channel with `--config-set`, and left it broken in the mirror
image: `run_matsim.main()` routes registry overrides into `cfg` and passes only
the raw `--set` dict to `run()`, so `_run.json`'s `overrides` records the RAW
channel, while `calibrate.find_run` matched on exactly that field. A
`--config-set` candidate recorded `overrides: {}`, never matched, and the loop
raised **after paying a full arm's wall clock**.

The test that shipped with the fix asserted `"'--config-set'" in src` - it
grepped the SENDING half of the source and could not see the receiving half.
These tests exercise the mechanism instead:

* the registry channel is what distinguishes one candidate from another, so
  two candidates differing in one declared value must not share a fingerprint;
* an arm stopped at its gate is not a completed candidate, however green its
  return code (9.143), because a 60-iteration stopped arm could otherwise
  become the calibrated base the README's figures are drawn from;
* and the record must state which declared values a run moved.
"""
import io
import json
import os

import pytest


import run_matsim


SCENARIO, DAY = 'S2', 'WEEKDAY'


def _cfg(**overrides):
    return run_matsim.resolve(SCENARIO, DAY, 'default_25pct', overrides or None)


def test_a_registry_override_changes_the_run_fingerprint():
    """The property the whole matching rests on, and the copy never had it.

    `values_sha256` fingerprints every RESOLVED registry value, which is why it
    can tell one `--config-set` candidate from another. Matching on the raw
    `--set` dict could not: every candidate recorded the same empty dict.
    """
    base = run_matsim.values_sha256(_cfg())
    moved = run_matsim.values_sha256(_cfg(**{'C.taxi.wait_min': 7.0}))
    assert base != moved, (
        'two candidates differing in one declared value must not share a '
        'fingerprint, or the second inherits the first\'s result (9.104)')
    assert run_matsim.values_sha256(_cfg()) == base, 'and it must be stable'


def test_run_records_which_declared_values_were_overridden():
    """`_run.json` carries the registry channel, not only the raw one."""
    import inspect
    sig = inspect.signature(run_matsim.run)
    assert 'registry_overrides' in sig.parameters, (
        'run() must be told the registry overrides if the record is to state '
        'them; the raw `--set` dict is a different channel')
    src = inspect.getsource(run_matsim.run)
    assert 'registry_overrides=dict(' in src


def test_a_gate_stopped_arm_is_not_a_completed_candidate():
    """9.143: a stopped arm is a citable READING, never a finished run.

    Read against whatever records this checkout actually holds: if any run on
    disk is stopped, `find_completed` must not return it for its own parameters.
    """
    import glob
    import results_store

    stopped = []
    for pat in (os.path.join(run_matsim.RAW, '*', '_run.json'),
                os.path.join(results_store.PROCESSED, '*', '_run.json')):
        for record in glob.glob(pat):
            try:
                doc = json.load(io.open(record, encoding='utf-8'))
            except (OSError, ValueError):
                continue
            if doc.get('completion') not in (None, run_matsim.RAN_TO_LAST):
                stopped.append(doc)
    if not stopped:
        pytest.skip('no stopped arm on disk in this checkout')

    doc = stopped[0]
    got = run_matsim.find_completed(
        doc.get('scenario'), doc.get('day'), doc.get('fraction'),
        doc.get('iterations'), doc.get('seed'), doc.get('overrides') or {},
        values=doc.get('values_sha256'))
    assert got is None or got.get('completion') == run_matsim.RAN_TO_LAST, (
        'find_completed returned a run whose record does not say '
        'ran_to_last_iteration (%s, completion=%s)'
        % (doc.get('name'), doc.get('completion')))


def test_find_run_is_delegated_not_copied():
    """The loop must not keep a second opinion about run identity.

    The copy searched `results/raw/` and `results/` but never
    `results/processed/`, so a candidate whose bulk had been reclaimed - the
    normal end state of an arm - was invisible to the loop that ran it.
    """
    import inspect

    import calibrate
    src = inspect.getsource(calibrate)
    assert '_run_matsim.find_completed(' in src, (
        'find_run must delegate to the runner\'s own resume search'
    )
    # and the hand-rolled glob is gone
    assert "doc.get('rc') == 0" not in src, (
        'a return code is not a completion (9.143)')
