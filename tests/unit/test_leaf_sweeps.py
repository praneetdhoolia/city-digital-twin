"""A per-mode table's entries are range-checked one by one, in an overlay too.

The declaration check walked a dict-valued field's numeric leaves against its
sweep; the overlay check tested scalars only (#200). An overlay that set one
mode's entry of a per-mode table outside the declared interval was accepted,
emitted, and reported inside its range by the sweep ledger. One walk now serves
both, and it sees lists as well as dicts.
"""

from __future__ import annotations

import registry  # noqa: E402


def _fields():
    fields, _origin = registry.load_registry()
    return fields


def _a_dict_valued_swept_field(fields):
    for key, f in sorted(fields.items()):
        if isinstance(f.get('value'), dict) and registry._sweep_interval(f.get('sweep')) \
                and not f.get('sweep_keys') and 'held_fixed' not in f \
                and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        for v in f['value'].values()):
            return key, f
    raise AssertionError('the registry holds no flat dict-valued swept field to test on')


def test_overlay_leaf_outside_sweep_is_refused():
    fields = _fields()
    key, f = _a_dict_valued_swept_field(fields)
    lo, hi = registry._sweep_interval(f['sweep'])
    value = dict(f['value'])
    entry = sorted(value)[0]
    value[entry] = hi * 10 + 1
    _values, errors = registry._check_values({key: value}, fields, 'test')
    assert errors and ('%s[%s]' % (key, entry)) in errors[0], errors


def test_overlay_leaf_inside_sweep_is_accepted():
    fields = _fields()
    key, f = _a_dict_valued_swept_field(fields)
    lo, hi = registry._sweep_interval(f['sweep'])
    value = dict(f['value'])
    value[sorted(value)[0]] = (lo + hi) / 2.0
    _values, errors = registry._check_values({key: value}, fields, 'test')
    assert errors == []


def test_list_leaves_are_walked():
    leaves = registry._numeric_leaves({'a': [1, 2.5, {'b': 3}], 'c': True})
    assert leaves == [('[a][0]', 1), ('[a][1]', 2.5), ('[a][2][b]', 3)]


def test_sweep_keys_scope_the_overlay_check_too():
    field = {'value': {'car': 1.0, 'walk': 9.0}, 'sweep': [0.0, 2.0], 'sweep_keys': ['car']}
    out = registry._leaves_outside_sweep(field, {'car': 1.5, 'walk': 99.0})
    assert out == []
    out = registry._leaves_outside_sweep(field, {'car': 5.0, 'walk': 99.0})
    assert [o[0] for o in out] == ['[car]']
