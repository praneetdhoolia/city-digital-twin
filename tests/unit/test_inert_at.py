"""A field can reach the config and still do nothing, and now it says so.

`check_hardcoding.py` proves a bound field's value reaches the config by nudging
it and watching the emitted bytes move. That proves the value ARRIVES. It cannot
prove the consumer acts on it, and the headline it prints - "N of N proven to
reach" - reads as though it does.

Three fields in this city are live counter-examples: their consumer treats the
shipped value as an off switch. `inert_at` declares that value, `inert_reason`
says why it is the shipped one, and the checker reports them WITHOUT counting
them - switching a mechanism off is a decision with a record behind it, while a
reader mistaking "reaches" for "does something" is not.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'src' / 'registry'))

import registry                                                   # noqa: E402
import check_hardcoding                                            # noqa: E402


def _fields():
    fields, _origin = registry.load_registry()
    return fields


def test_every_inert_at_carries_a_reason():
    """Enforced by the schema too; asserted here so the rule is visible where
    the behaviour is, and so a city that bypasses the schema still fails."""
    missing = [k for k, f in _fields().items()
               if isinstance(f, dict) and 'inert_at' in f
               and not (f.get('inert_reason') or '').strip()]
    assert not missing, (
        'inert_at without inert_reason turns a switched-off mechanism back '
        'into an invisible one: %s' % missing)


def test_switched_off_finds_a_field_shipped_at_its_off_value():
    rows = check_hardcoding.switched_off(_fields())
    assert rows, 'no field is declared inert_at; the section would be vacuous'
    for key, shipped, off, why in rows:
        assert float(shipped) == float(off)
        assert why.strip()


def test_a_field_away_from_its_off_value_is_not_reported():
    fields = {
        'X.on': {'value': 2.0, 'inert_at': 0.0, 'inert_reason': 'r'},
        'X.off': {'value': 0.0, 'inert_at': 0.0, 'inert_reason': 'r'},
        'X.plain': {'value': 0.0},
    }
    keys = [row[0] for row in check_hardcoding.switched_off(fields)]
    assert keys == ['X.off']


def test_a_non_numeric_off_value_compares_by_equality():
    fields = {
        'X.gate': {'value': 'absent', 'inert_at': 'absent',
                   'inert_reason': 'r'},
        'X.live': {'value': 'mode_constant', 'inert_at': 'absent',
                   'inert_reason': 'r'},
    }
    keys = [row[0] for row in check_hardcoding.switched_off(fields)]
    assert keys == ['X.gate']


def test_the_schema_requires_the_reason():
    schema = json.loads(
        (REPO / 'config' / 'schema' / 'field.schema.json').read_text(
            encoding='utf-8'))
    rules = [r for r in schema['allOf']
             if r.get('if', {}).get('required') == ['inert_at']]
    assert rules, 'the schema does not tie inert_at to inert_reason'
    assert rules[0]['then']['required'] == ['inert_reason']


def test_reporting_them_does_not_count_them_as_defects():
    """The gate is at 0 and stays at 0. A switched-off mechanism is reported so
    it cannot be forgotten, and is not a defect to be worked down by changing a
    model value without an arm."""
    _corpus, _fields_, led, _n, _owned, _pending = check_hardcoding.audit()
    assert sum(len(v) for v in led.values()) == 0
