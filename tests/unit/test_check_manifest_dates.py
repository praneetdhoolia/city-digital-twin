"""The manifest check refuses an undated raw row and a scope-none row, with a debt that only shrinks.

`tests/check_manifest.py` records, per city, the exact paths that failed each
rule when it was introduced. The rule is exercised here on a synthetic
manifest: a new failing path outside the debt fails, a listed path that has
been fixed fails (so the list must shrink), and a debt that matches exactly
passes. No city's manifest is read; the module resolves the active city at
import time, as every check does, and nothing here depends on which one.
"""
import importlib.util
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
    row('data/processed/undated_but_processed.csv', stage='processed',
        retrieved=''),
    row('data/processed/no_scope.csv', stage='processed', scope='none'),
]


def test_an_exact_debt_passes_and_counts_what_fails():
    debt = dict(raw_without_retrieved={'data/raw/undated.json'},
                lineage_scope_none={'data/processed/no_scope.csv'})
    failures, counts = check_manifest.check_recorded_debt(ROWS, debt)
    assert failures == []
    assert counts == dict(raw_without_retrieved=(1, 1),
                          lineage_scope_none=(1, 1))


def test_a_processed_row_without_a_date_is_not_a_raw_date_failure():
    failures, counts = check_manifest.check_recorded_debt(
        ROWS, dict(raw_without_retrieved={'data/raw/undated.json'},
                   lineage_scope_none={'data/processed/no_scope.csv'}))
    assert counts['raw_without_retrieved'][0] == 1


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


def test_the_debt_block_parses_one_path_per_line():
    assert check_manifest._paths('\n a/b.csv\n\nc/d.json \n') == frozenset(
        {'a/b.csv', 'c/d.json'})


def test_the_recorded_debt_names_only_the_declared_rules():
    rules = {r[0] for r in check_manifest.DATE_AND_SCOPE_RULES}
    for city_id, debt in check_manifest.RECORDED_DEBT.items():
        assert set(debt) <= rules, city_id
