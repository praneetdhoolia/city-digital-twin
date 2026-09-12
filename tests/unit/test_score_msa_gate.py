"""Score averaging is declared, and declaring it changed nothing.

`scoring.fractionOfIterationsToStartScoreMSA` decided how every plan in every
arm was scored and no layer of this project stated it: MATSim's default of
`null` means each plan carries the score of its LAST execution, so at the
innovation cutoff every agent selects the maximum of noisy single-execution
scores at once. The 10 September 2026 assessment named it as the only one-field
candidate cause of the convergence penalty, and the only one that predicts both
measured symptoms of `20260909T015217_300it_25pct`.

It is now a gate, and the point of these tests is that turning the gate on is an
EXPERIMENT and declaring it was not: at `absent` the emitted value is the literal
MATSim writes for its own default, so the shipped model is byte-identical to the
one that ran.
"""

from __future__ import annotations

import json
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]

import registry                                                   # noqa: E402
import build_matsim_run_inputs as build                           # noqa: E402

GATE = 'RUN.replanning.score_msa_representation'
CUTOFF = 'RUN.replanning.fraction_to_disable_innovation'


def _cfg(**overrides):
    pairs = ['%s=%s' % kv for kv in overrides.items()]
    return registry.load(scenario='S2', day='WEEKDAY',
                         set=registry.parse_set(pairs) if pairs else None)


def test_the_gate_ships_absent():
    assert _cfg().get(GATE) == 'absent'


def test_absent_emits_matsims_own_default_literal():
    """Not 'about the same' - the same string MATSim's parameter dump records,
    so declaring the field cannot have moved the model."""
    defaults = json.loads(
        (REPO / 'config' / 'schema' / 'matsim_defaults.json').read_text(
            encoding='utf-8'))
    matsim_default = defaults['groups']['scoring'][
        'fractionOfIterationsToStartScoreMSA']
    value, role, note = build._score_msa(_cfg())
    assert value == matsim_default
    assert role == 'derived'
    assert 'absent' in note


def test_the_cutoff_setting_introduces_no_new_number():
    """The only value the gate can emit when it is on is the innovation cutoff
    that is already declared. A third number here would be a new free parameter
    arriving without a sweep."""
    cfg = _cfg(**{GATE: 'at_innovation_cutoff'})
    value, role, note = build._score_msa(cfg)
    assert value == cfg.get(CUTOFF)
    assert role == 'derived'
    assert CUTOFF in note


def test_the_resolver_refuses_a_value_outside_the_gate():
    """The first line of defence: an overlay or a --config-set cannot invent a
    third mode, because the declared categorical sweep is the whole domain."""
    with pytest.raises(registry.RegistryError) as e:
        _cfg(**{GATE: 'sometimes'})
    assert GATE in str(e.value)


def test_the_emitter_refuses_rather_than_guesses():
    """The second line: if a value ever reached the builder from somewhere the
    resolver does not police, it must stop rather than emit a default."""
    class _Fake(object):
        def get(self, key):
            return 'sometimes' if key == GATE else 0.8

    with pytest.raises(SystemExit) as e:
        build._score_msa(_Fake())
    assert 'score_msa_representation' in str(e.value)


def test_the_two_fields_agree_on_what_they_derive_from():
    """The computed companion must name the gate and the cutoff, or a reader of
    the registry alone cannot tell where the emitted number comes from."""
    fields, _origin = registry.load_registry()
    companion = fields['RUN.replanning.score_msa_fraction']
    assert companion['status'] == 'computed'
    assert companion['matsim_param'] == \
        'scoring.fractionOfIterationsToStartScoreMSA'
    assert set(companion['derived_from']['fields']) == {GATE, CUTOFF}
