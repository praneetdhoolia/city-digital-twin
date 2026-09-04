"""The output contract's rules about MEANING, which no JSON Schema can state.

`src/registry/outputs.py:_semantic_errors` holds the four rules that are about
what a document claims rather than what shape it has: a fit statistic must name
the targets it was computed over, scored plus explained must reconcile to the
targets available, a dead run must say why it died, and a completed run must be
able to state what inputs produced it. They are enforced in Python rather than
in the schema because `jsonschema` is optional and CI installs nothing - so if
these rules are not tested here they are only tested when a real run happens to
produce a malformed document, which is exactly how three failed runs reached a
later session unable to explain themselves.

Minimal documents built by hand against `config/schema/outputs/`; no city, no
run, no package.
"""
import outputs


def semantic(kind, doc):
    return outputs._semantic_errors(kind, doc)


def fit_doc(**over):
    """A fit document that satisfies every semantic rule, to break one at a time."""
    doc = dict(
        run='fixture', scenario='S0', day='WEEKDAY',
        calibration_targets_available=3,
        scored=2,
        unscorable=[dict(target_id='T3', metric='fixture_metric',
                         reason='no modelled counterpart in a single day-type run')],
        mode_share=dict(targets=['T1'], n=1, errors=[]),
        patronage=dict(targets=[], n=0, errors=[]),
        counts=dict(targets=['T2'], n=1, errors=[]),
        headline='a fixture')
    doc.update(over)
    return doc


# --------------------------------------------------------------------------
# fit: every statistic names its targets, and every target is scored or explained
# --------------------------------------------------------------------------
def test_a_wellformed_fit_document_raises_nothing():
    assert semantic('fit', fit_doc()) == []


def test_a_fit_block_that_names_no_targets_is_an_error():
    doc = fit_doc(counts=dict(n=1, errors=[]))
    errors = semantic('fit', doc)
    assert any('counts' in e and 'no target ids' in e for e in errors)


def test_a_fit_block_whose_count_disagrees_with_its_target_list_is_an_error():
    doc = fit_doc(counts=dict(targets=['T2'], n=7, errors=[]))
    errors = semantic('fit', doc)
    assert any('counts' in e and 'n=7' in e and 'must agree' in e
               for e in errors)


def test_a_block_that_is_not_a_dict_is_skipped_rather_than_crashing():
    # a run written before a block existed carries None there
    assert semantic('fit', fit_doc(patronage=None)) == []


def test_reconciliation_failure_is_an_error():
    # 2 scored + 1 explained != 5 available: the failure that let an earlier cut
    # score 35 and explain 16 of 67, leaving 16 targets neither
    errors = semantic('fit', fit_doc(calibration_targets_available=5))
    assert any('reconciliation failed' in e for e in errors)


def test_reconciliation_is_not_asserted_when_a_side_is_absent():
    doc = fit_doc()
    doc.pop('scored')
    assert not any('reconciliation' in e for e in semantic('fit', doc))


def test_an_unscorable_target_without_a_reason_is_an_error():
    doc = fit_doc(unscorable=[dict(target_id='T3', metric='fixture_metric')])
    errors = semantic('fit', doc)
    assert any('T3' in e and 'no reason' in e for e in errors)


def test_a_blank_reason_does_not_count_as_a_reason():
    doc = fit_doc(unscorable=[dict(target_id='T3', reason='')])
    assert any('carries no reason' in e for e in semantic('fit', doc))


# --------------------------------------------------------------------------
# meta: a dead run must say why it died
# --------------------------------------------------------------------------
def meta_doc(**over):
    doc = dict(status='completed', scenario='S0', day='WEEKDAY', fraction=0.25,
               sample_pct=25.0, iterations=2, seed=20260810,
               started='2026-09-04T00:00:00')
    doc.update(over)
    return doc


def test_a_completed_run_needs_no_cause():
    assert semantic('meta', meta_doc()) == []


def test_a_failed_run_with_no_cause_is_an_error():
    errors = semantic('meta', meta_doc(status='failed', rc=1))
    assert any('carries no cause' in e for e in errors)


def test_an_aborted_run_with_no_cause_is_an_error():
    errors = semantic('meta', meta_doc(status='aborted'))
    assert any('carries no cause' in e for e in errors)


def test_a_failed_run_that_quotes_its_own_log_passes():
    cause = ('java.lang.IllegalStateException: Subtour contains a mix of chain- '
             'and non-chainbased modes')
    assert semantic('meta', meta_doc(status='failed', rc=1, cause=cause)) == []


def test_an_empty_cause_is_no_cause():
    errors = semantic('meta', meta_doc(status='failed', rc=1, cause=''))
    assert any('carries no cause' in e for e in errors)


# --------------------------------------------------------------------------
# run: a completed run must be able to state what produced it
# --------------------------------------------------------------------------
def run_doc(**over):
    doc = dict(name='20260904T000000_2it_25pct', scenario='S0', day='WEEKDAY',
               fraction=0.25, iterations=2, threads=1, seed=20260810,
               rc=0, wall_s=1.0,
               config_snapshot='raw/20260904T000000_2it_25pct/_config.json')
    doc.update(over)
    return doc


def test_a_run_snapshot_that_names_its_config_passes():
    assert semantic('run', run_doc()) == []


def test_a_completed_run_without_a_config_snapshot_is_an_error():
    errors = semantic('run', run_doc(config_snapshot=None))
    assert any('no config_snapshot' in e for e in errors)


def test_a_failed_run_record_is_not_asked_for_a_config_snapshot():
    # only rc == 0 carries the claim; a non-zero record is not a result
    assert semantic('run', run_doc(rc=1, config_snapshot=None)) == []


# --------------------------------------------------------------------------
# metrics: a mode share that does not sum to the whole is not a mode share
# --------------------------------------------------------------------------
def test_a_mode_share_that_sums_to_one_hundred_passes():
    doc = dict(mode_share=dict(target_lga_pct={'car': 60.0, 'pt': 10.0,
                                               'walk': 20.0, 'bike': 10.0}))
    assert semantic('metrics', doc) == []


def test_a_mode_share_that_does_not_sum_to_one_hundred_is_an_error():
    doc = dict(mode_share=dict(target_lga_pct={'car': 60.0, 'pt': 10.0}))
    errors = semantic('metrics', doc)
    assert any('sums to 70.00, not 100' in e for e in errors)


def test_a_metrics_document_with_no_shares_yet_is_not_judged():
    assert semantic('metrics', dict(mode_share={})) == []


def test_an_unknown_kind_carries_no_semantic_rules():
    assert semantic('summary', dict(anything=1)) == []
