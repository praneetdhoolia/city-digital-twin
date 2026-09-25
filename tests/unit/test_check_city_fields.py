"""`check_city.check_fields` refuses a city registry that cannot run, before it runs.

The check compares a city's registry with `required_fields.json` and its own
`city.json`. Each narrowing and each refusal it makes is a rule a second city
depends on, so each is pinned on a minimal fixture - a two-file registry in a
temporary directory and a contract of a handful of fields - rather than on the
reference city, whose registry passes every rule and so proves none of them:

  * a required field left undeclared is a FAIL, naming the field;
  * a field pinned to a mode (`required_if_mode`) is not required of a city
    that does not run the mode, and DECLARING it there is a FAIL;
  * a field only builders read (`required_by`) is required only where the
    city's manifest names one of those builders as a producer, and a field only
    the reference city reads is required of no one;
  * units must equal the contract's, with `{currency}`/`{base_year}` expanded
    from THIS city's descriptor;
  * `consumers` must name files that exist;
  * city.json and the registry must agree on modes and the seed, and a field
    city.json declares unobtained may carry no point value.

The contract is swapped by pointing `SCHEMA_DIR` at the fixture; the registry's
own field schema is the real one.
"""
import json

import pytest

from registry import check_city


def _field(units, value=1, **extra):
    f = dict(value=value, units=units, source='definition', status='active',
             description='fixture field')
    f.update(extra)
    return f


CONTRACT = {
    'X.core.speed_mps': {'units': 'metres_per_second'},
    'X.core.fare': {'units': '{currency}_{base_year}'},
    'X.bike.stress': {'units': 'ratio', 'required_if_mode': 'bike'},
    'X.build.only': {'units': 'metres', 'required_by': ['src/build/builder_a.py']},
    'X.reference.only': {'units': 'metres', 'required_by': 'reference_city'},
}

DOC = {'id': 'fixturecity', 'modes': ['car', 'walk'], 'currency': 'EUR',
       'base_year': 2030}


@pytest.fixture
def city(tmp_path, monkeypatch):
    schema = tmp_path / 'schema'
    schema.mkdir()
    (schema / 'required_fields.json').write_text(
        json.dumps({'fields': CONTRACT}), encoding='utf-8')
    monkeypatch.setattr(check_city, 'SCHEMA_DIR', str(schema))
    monkeypatch.setattr(check_city, '_state', {'pass': 0, 'fail': 0, 'note': 0})
    city_dir = tmp_path / 'fixturecity'
    (city_dir / 'registry').mkdir(parents=True)
    return city_dir


def _write(city_dir, fields, name='X_fields.json'):
    (city_dir / 'registry' / name).write_text(json.dumps({'fields': fields}),
                                              encoding='utf-8')


def _complete():
    return {'X.core.speed_mps': _field('metres_per_second'),
            'X.core.fare': _field('EUR_2030')}


def _run(city_dir, capsys, doc=DOC):
    check_city.check_fields(str(city_dir), 'fixturecity', doc)
    fails = [l for l in capsys.readouterr().out.splitlines() if l.startswith('FAIL')]
    return fails


def test_a_complete_registry_passes(city, capsys):
    _write(city, _complete())
    assert _run(city, capsys) == []
    assert check_city._state['fail'] == 0
    assert check_city._state['pass'] > 0


def test_a_missing_required_field_is_named(city, capsys):
    fields = _complete()
    del fields['X.core.speed_mps']
    _write(city, fields)
    fails = _run(city, capsys)
    assert any('required field not declared: X.core.speed_mps' in f for f in fails)


def test_units_are_held_to_this_citys_own_currency_and_year(city, capsys):
    fields = _complete()
    fields['X.core.fare'] = _field('AUD_2026')
    _write(city, fields)
    fails = _run(city, capsys)
    assert any("X.core.fare declared in 'AUD_2026', contract says 'EUR_2030'" in f
               for f in fails)


def test_a_mode_this_city_does_not_run_is_neither_required_nor_allowed(city, capsys):
    _write(city, _complete())
    assert _run(city, capsys) == []                 # bike not run, not required
    fields = _complete()
    fields['X.bike.stress'] = _field('ratio')
    _write(city, fields)
    fails = _run(city, capsys)
    assert any('declared for a mode this city does not run: X.bike.stress' in f
               for f in fails)


def test_a_city_running_the_mode_must_declare_its_field(city, capsys):
    _write(city, _complete())
    fails = _run(city, capsys, doc=dict(DOC, modes=['car', 'walk', 'bike']))
    assert any('required field not declared: X.bike.stress' in f for f in fails)


def test_builder_fields_are_required_only_where_the_builder_produced(city, capsys):
    _write(city, _complete())
    assert _run(city, capsys) == []                 # no manifest: not required
    (city / 'data').mkdir()
    (city / 'data' / 'MANIFEST.csv').write_text(
        'path,produced_by\n'
        'networks/a.xml,src/build/builder_a.py (tool 1.0) + src/build/other.py\n',
        encoding='utf-8')
    assert check_city.manifest_producers(str(city)) == {
        'src/build/builder_a.py', 'src/build/other.py'}
    fails = _run(city, capsys)
    assert any('required field not declared: X.build.only' in f for f in fails)
    # the reference city's own field stays unrequired either way
    assert not any('X.reference.only' in f for f in fails)


def test_a_consumer_that_does_not_exist_fails(city, capsys):
    fields = _complete()
    fields['X.core.speed_mps']['consumers'] = ['src/no_such_module_anywhere.py']
    _write(city, fields)
    fails = _run(city, capsys)
    assert any('every consumers path exists' in f and 'no_such_module_anywhere' in f
               for f in fails)


def test_descriptor_and_registry_must_agree_on_modes_and_seed(city, capsys):
    fields = _complete()
    fields['RUN.mode_choice.modes'] = _field('enum', value=['car', 'pt'])
    fields['B.seed.master'] = _field('dimensionless', value=7)
    _write(city, fields)
    fails = _run(city, capsys, doc=dict(DOC, seed=8))
    assert any('city.json modes match RUN.mode_choice.modes' in f for f in fails)
    assert any('city.json seed matches B.seed.master' in f for f in fails)


def test_a_descriptor_seed_needs_a_registry_seed(city, capsys):
    _write(city, _complete())
    fails = _run(city, capsys, doc=dict(DOC, seed=8))
    assert any('declares a seed, so the registry declares B.seed.master' in f
               for f in fails)


def test_an_unobtained_field_may_not_carry_a_value(city, capsys):
    _write(city, _complete())
    fails = _run(city, capsys, doc=dict(DOC, unobtained=[{'field': 'X.core.fare'}]))
    assert any('X.core.fare is declared unobtained and carries NO point value' in f
               for f in fails)


def test_a_registry_that_does_not_load_fails_once(city, capsys):
    # an empty registry directory is a RegistryError, reported rather than raised
    fails = _run(city, capsys)
    assert len(fails) == 1 and 'registry loads' in fails[0]


def test_expand_units_leaves_an_unexpandable_token_in_place():
    assert check_city._expand_units('{currency}_{base_year}_per_hour',
                                    {'currency': 'EUR', 'base_year': 2030}) \
        == 'EUR_2030_per_hour'
    assert check_city._expand_units('{currency}_per_trip', {'base_year': 2030}) \
        == '{currency}_per_trip'
    assert check_city._expand_units('metres', None) == 'metres'


def test_expand_layer_path_uses_the_citys_own_vocabulary():
    doc = {'intervention': {'scenarios': ['S0', 'S9']}, 'day_types': ['MON']}
    assert check_city._expand_layer_path('x/{scenario}/{day_type}.gz', doc) == [
        'x/S0/MON.gz', 'x/S9/MON.gz']
    # no vocabulary: the template stays as it is rather than vanishing
    assert check_city._expand_layer_path('x/{scenario}.gz', {}) == ['x/{scenario}.gz']
