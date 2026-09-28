"""The manifest check refuses an undated raw row, a scope-none row and drifted
bytes, with a per-city debt whose ceiling may only fall.

`tests/check_manifest.py` states the rules; each city records, in
`cities/<city>/tests/manifest_debt.json`, the exact paths that fail a rule and
a ceiling beside them. The rules are exercised here on a synthetic manifest
and synthetic ledgers: a new failing path outside the debt fails, a listed path
that has been fixed fails (so the list must shrink), a path added without
raising the ceiling fails, a raise without a logged reason fails, and a
provenance record is exempt from the date rule while its own contents are
checked for a date. No city's manifest is read.
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'check_manifest', os.path.join(HERE, '..', 'check_manifest.py'))
check_manifest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_manifest)


def row(path, stage='raw', retrieved='2026-09-01', scope='output'):
    return dict(path=path, stage=stage, retrieved=retrieved,
                lineage_scope=scope)


ROWS = [
    row('data/raw/dated.json'),
    row('data/raw/undated.json', retrieved=''),
    row('data/raw/sub/provenance_thing.json', retrieved=''),
    row('data/processed/undated_but_processed.csv', stage='processed',
        retrieved=''),
    row('data/processed/no_scope.csv', stage='processed', scope='none'),
]
EXACT = dict(raw_without_retrieved={'data/raw/undated.json'},
             lineage_scope_none={'data/processed/no_scope.csv'})


def entry(paths, ceiling=None, log=None):
    paths = sorted(paths)
    ceiling = len(paths) if ceiling is None else ceiling
    return dict(paths=paths, ceiling=ceiling, ceiling_log=log if log is not None else
                [dict(date='2026-09-29', ceiling=ceiling, reason='measured')])


# -- the rules against the listed paths ---------------------------------------

def test_an_exact_debt_passes_and_counts_what_fails():
    failures, counts = check_manifest.check_recorded_debt(ROWS, EXACT)
    assert failures == []
    assert counts == dict(raw_without_retrieved=(1, 1),
                          lineage_scope_none=(1, 1))


def test_a_processed_row_without_a_date_is_not_a_raw_date_failure():
    _, counts = check_manifest.check_recorded_debt(ROWS, EXACT)
    assert counts['raw_without_retrieved'][0] == 1


def test_a_provenance_record_is_exempt_from_the_date_rule_by_rule():
    assert check_manifest.is_provenance_record('data/raw/sub/provenance_thing.json')
    assert check_manifest.is_provenance_record('schedules/raw/provenance.json')
    assert not check_manifest.is_provenance_record('data/raw/_osm_fetch.log')
    failures, _ = check_manifest.check_recorded_debt(ROWS, EXACT)
    assert not any('provenance_thing' in f for f in failures)


def test_a_provenance_record_in_the_checkout_must_carry_a_dated_retrieval(tmp_path):
    good = tmp_path / 'provenance_good.json'
    good.write_text(json.dumps({'files': [{'retrieved': '2026-09-18T08:46:01Z'}]}),
                    encoding='utf-8')
    bad = tmp_path / 'provenance_bad.json'
    bad.write_text(json.dumps({'url': 'https://example.org'}), encoding='utf-8')
    rows = [row('provenance_good.json', retrieved=''),
            row('provenance_bad.json', retrieved=''),
            row('provenance_absent.json', retrieved='')]
    out = check_manifest.check_provenance_dated(
        rows, resolve=lambda p: str(tmp_path / p))
    assert len(out) == 1 and 'provenance_bad.json' in out[0]


def test_a_new_undated_raw_row_outside_the_debt_is_refused():
    failures, _ = check_manifest.check_recorded_debt(
        ROWS, dict(lineage_scope_none={'data/processed/no_scope.csv'}))
    assert len(failures) == 1
    assert 'no retrieval date' in failures[0]
    assert 'data/raw/undated.json' in failures[0]


def test_a_new_scope_none_row_outside_the_debt_is_refused():
    failures, _ = check_manifest.check_recorded_debt(
        ROWS, dict(raw_without_retrieved={'data/raw/undated.json'}))
    assert len(failures) == 1
    assert 'lineage_scope none' in failures[0]
    assert 'data/processed/no_scope.csv' in failures[0]


def test_a_fixed_path_still_listed_is_refused_so_the_debt_shrinks():
    debt = dict(raw_without_retrieved={'data/raw/undated.json',
                                       'data/raw/dated.json',
                                       'data/raw/gone_from_manifest.json'},
                lineage_scope_none={'data/processed/no_scope.csv'})
    failures, _ = check_manifest.check_recorded_debt(ROWS, debt)
    assert len(failures) == 1
    assert 'no longer fail' in failures[0]
    assert 'data/raw/dated.json' in failures[0]
    assert 'data/raw/gone_from_manifest.json' in failures[0]


def test_a_city_with_no_recorded_debt_refuses_every_hole():
    failures, counts = check_manifest.check_recorded_debt(ROWS, {})
    assert len(failures) == 2
    assert counts == dict(raw_without_retrieved=(1, 0),
                          lineage_scope_none=(1, 0))


# -- byte drift ------------------------------------------------------------------

def test_recorded_drift_passes_and_new_drift_fails():
    debt = dict(EXACT, sha256_drift={'a.zip'})
    ok, counts = check_manifest.check_recorded_debt(
        ROWS, debt, drifted={'a.zip'}, present={'a.zip'})
    assert ok == [] and counts['sha256_drift'] == (1, 1)
    bad, _ = check_manifest.check_recorded_debt(
        ROWS, debt, drifted={'a.zip', 'b.zip'}, present={'a.zip', 'b.zip'})
    assert len(bad) == 1 and 'b.zip' in bad[0]


def test_a_drift_path_absent_from_the_checkout_is_not_judged_but_a_healed_one_is():
    debt = dict(EXACT, sha256_drift={'absent.zip', 'healed.zip'})
    failures, _ = check_manifest.check_recorded_debt(
        ROWS, debt, drifted=set(), present={'healed.zip'})
    assert len(failures) == 1
    assert 'healed.zip' in failures[0] and 'absent.zip' not in failures[0]


# -- the ceiling may only fall ---------------------------------------------------

def test_an_exact_ceiling_passes():
    assert check_manifest.check_ceilings(
        dict(lineage_scope_none=entry({'a', 'b'}))) == []


def test_a_path_added_without_raising_the_ceiling_is_refused():
    e = entry({'a', 'b'})
    e['paths'].append('c')
    out = check_manifest.check_ceilings(dict(lineage_scope_none=e))
    assert len(out) == 1 and 'above the ceiling' in out[0]


def test_a_path_removed_without_lowering_the_ceiling_is_refused():
    out = check_manifest.check_ceilings(
        dict(lineage_scope_none=entry({'a'}, ceiling=2,
                                      log=[dict(date='d', ceiling=2, reason='r')])))
    assert len(out) == 1 and 'lower the ceiling to 1' in out[0]


def test_the_newest_log_entry_must_state_the_ceiling_with_a_reason():
    stale = entry({'a', 'b'}, log=[dict(date='d', ceiling=1, reason='r')])
    assert any('newest ceiling_log' in f for f in
               check_manifest.check_ceilings(dict(lineage_scope_none=stale)))
    unexplained = entry({'a'}, log=[dict(date='d', ceiling=1, reason='')])
    assert any('date and a' in f for f in
               check_manifest.check_ceilings(dict(lineage_scope_none=unexplained)))


def test_a_raise_against_main_needs_a_new_log_entry():
    base = dict(lineage_scope_none=entry({'a'}))
    raised = entry({'a', 'b'}, log=[dict(date='d', ceiling=2, reason='r')])
    out = check_manifest.check_ceilings(dict(lineage_scope_none=raised), base)
    assert len(out) == 1 and 'rose from 1' in out[0]
    logged = entry({'a', 'b'}, log=base['lineage_scope_none']['ceiling_log']
                   + [dict(date='d2', ceiling=2, reason='a new source, #999')])
    assert check_manifest.check_ceilings(dict(lineage_scope_none=logged), base) == []


def test_an_unknown_rule_is_refused():
    out = check_manifest.check_ceilings(dict(not_a_rule=entry({'a'})))
    assert len(out) == 1 and 'unknown rule' in out[0]


def test_every_city_ledger_names_only_declared_rules_and_holds_its_ceilings():
    root = os.path.join(HERE, '..', '..', 'cities')
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name, 'tests', 'manifest_debt.json')
        if not os.path.exists(path):
            continue
        ledger = check_manifest.load_ledger(path)
        assert set(ledger) <= set(check_manifest.RULES), name
        assert check_manifest.check_ceilings(ledger) == [], name
