"""The ASC round proposes, refuses, and measures its own contraction.

This is the instrument for the one question eleven comparability families have
not answered: is the residual a taste the constants were never set to, or a
mechanism the model does not contain? The two look identical on the board and
have opposite remedies. What is asserted here is therefore not that the steps
are right - they are whatever the shares say - but that the loop CANNOT do the
three things that would make the answer worthless:

  * move a constant the registry froze (the answer would be an artefact of
    fitting away the very effect under test);
  * silently clip a step too large to be a taste parameter (which would hide
    the signal the experiment exists to read);
  * count a boardings-basis proxy as though it were the exact logit inversion.

Synthetic fits and a synthetic registry: no run, no `results/`, no package.
"""
import json
import math

import asc_fixed_point as afp


class _Cfg:
    """The registry surface this module uses, and nothing else."""

    def __init__(self, fields, values):
        self._fields, self._values = fields, values

    def get(self, key):
        return self._values[key]

    def field(self, key):
        return self._fields.get(key)


def _cfg(fields=None, damping=0.6, max_step=1.5, mapping=None):
    # every movable constant carries a scalar sweep, because that IS the
    # registry's movability contract and this loop asks the same question of it
    # that `calibrate.free_parameters` does
    fields = fields if fields is not None else {
        'C.asc.car_driver': dict(value=0.0, sweep=[-2.0, 2.0]),
        'C.asc.bus': dict(value=-1.05, sweep=[-8.0, 8.0]),
        'C.asc.rail': dict(value=-0.75, sweep=[-8.0, 8.0],
                           held_fixed=dict(rule='8.5: no crowding disutility '
                                                'reaches scoring',
                                           decisions_ref='8.5')),
    }
    mapping = mapping if mapping is not None else {
        'car': 'C.asc.car_driver', 'bus': 'C.asc.bus',
        'heavy_rail': 'C.asc.rail'}
    return _Cfg(fields, {
        'CAL.asc.mode_to_constant': mapping,
        'CAL.asc.damping': damping,
        'CAL.asc.max_step_utils': max_step})


def _fit(rows, **kw):
    doc = dict(run='r', completion='ran_to_last_iteration',
               reached_iteration=100, is_a_result=True,
               goal_modes=dict(iteration=100, max_abs_rel_pct=1.0,
                               worst_mode='bus', n_inside_pass_band=0,
                               modes=rows))
    doc.update(kw)
    return doc


def _row(mode, dev, basis='share of resident linked trips'):
    return dict(mode=mode, modelled=1.0, target=1.0, deviation_pct=dev,
                basis=basis, flag='ok', count=1, optimised=True)


# --------------------------------------------------------------------------
# the refusals, which are the reason this can be trusted at all
# --------------------------------------------------------------------------
def test_a_held_fixed_constant_is_refused_structurally():
    out = afp.propose(_fit([_row('car', 0.0), _row('bus', 50.0),
                            _row('heavy_rail', 247.2)]), _cfg())
    moved = {p['mode'] for p in out['proposals']}
    assert 'heavy_rail' not in moved
    refused = {r['mode']: r for r in out['refused']}
    assert refused['heavy_rail']['held_fixed'] is True
    # the registry's own reason is carried out, not one this module invents
    assert 'crowding' in refused['heavy_rail']['reason']


def test_the_reference_mode_is_never_moved():
    out = afp.propose(_fit([_row('car', 5.0), _row('bus', 50.0)]), _cfg())
    assert 'car' not in {p['mode'] for p in out['proposals']}
    assert any(r['mode'] == 'car' for r in out['refused'])


def test_a_mode_with_no_declared_constant_is_refused_not_invented():
    out = afp.propose(
        _fit([_row('car', 0.0), _row('ferry', -65.0)]),
        _cfg(mapping={'car': 'C.asc.car_driver', 'ferry': 'C.asc.ferry'}))
    refused = {r['mode']: r for r in out['refused']}
    assert 'no such registry field' in refused['ferry']['reason']


def test_an_oversized_step_is_refused_rather_than_clipped():
    """Clipping would hide the signal: a constant asked to move further than a
    taste parameter plausibly is, is absorbing a mechanism."""
    out = afp.propose(_fit([_row('car', 0.0), _row('bus', 5000.0)]),
                      _cfg(max_step=0.5))
    assert out['proposals'] == []
    r = [x for x in out['refused'] if x['mode'] == 'bus'][0]
    assert r['refused_step'] is True and r['proposed'] is None
    assert 'REFUSED rather than clipped' in r['reason']


# --------------------------------------------------------------------------
# the step itself
# --------------------------------------------------------------------------
def test_the_step_is_the_damped_log_ratio_against_the_reference():
    out = afp.propose(_fit([_row('car', 25.0), _row('bus', 100.0)]),
                      _cfg(damping=0.5))
    p = [x for x in out['proposals'] if x['mode'] == 'bus'][0]
    expected_raw = math.log(1 / 2.0) - math.log(1 / 1.25)
    # the proposal rounds to 6 decimals so the document a human reads and the
    # --config-set line it prints carry a sane number of digits; the tolerance
    # is that rounding, not a looser claim about the arithmetic
    tol = 5e-7
    assert abs(p['raw_step'] - expected_raw) < tol
    assert abs(p['step'] - 0.5 * expected_raw) < tol
    assert abs(p['proposed'] - (-1.05 + 0.5 * expected_raw)) < tol


def test_a_mode_over_target_is_pushed_down_and_under_target_pushed_up():
    out = afp.propose(_fit([_row('car', 0.0), _row('bus', 100.0)]), _cfg())
    assert [p for p in out['proposals'] if p['mode'] == 'bus'][0]['step'] < 0
    out = afp.propose(_fit([_row('car', 0.0), _row('bus', -50.0)]), _cfg())
    assert [p for p in out['proposals'] if p['mode'] == 'bus'][0]['step'] > 0


def test_nothing_is_written_and_the_overrides_are_only_proposed():
    out = afp.propose(_fit([_row('car', 0.0), _row('bus', 50.0)]), _cfg())
    assert set(out['overrides']) == {'C.asc.bus'}
    assert 'PROPOSED ONLY' in out['note']


def test_a_run_with_no_scorable_board_reading_raises_rather_than_guessing():
    import pytest
    bad = _fit([])
    bad['goal_modes'] = dict(max_abs_rel_pct=None, reason='no rows', modes=[])
    with pytest.raises(SystemExit):
        afp.propose(bad, _cfg())


# --------------------------------------------------------------------------
# the contraction, which is the actual measurement
# --------------------------------------------------------------------------
def test_a_shrinking_step_reads_as_contracting():
    prev = dict(proposals=[dict(mode='bus', abs_step=1.0,
                                basis_is_boardings=False)])
    cur = dict(proposals=[dict(mode='bus', abs_step=0.4,
                               basis_is_boardings=False)])
    c = afp.contraction(prev, cur)
    assert c['n_shrank'] == 1 and c['mean_step_ratio_share_basis'] == 0.4
    assert c['verdict'].startswith('CONTRACTING')


def test_a_step_that_does_not_shrink_reads_as_a_mechanism():
    prev = dict(proposals=[dict(mode='bus', abs_step=0.4,
                                basis_is_boardings=False)])
    cur = dict(proposals=[dict(mode='bus', abs_step=0.9,
                               basis_is_boardings=False)])
    c = afp.contraction(prev, cur)
    assert c['n_grew'] == 1
    assert c['verdict'].startswith('NOT CONTRACTING')
    assert 'mechanism the model does not contain' in c['verdict']


def test_a_boardings_basis_mode_is_reported_but_kept_out_of_the_verdict():
    """The logit inversion is exact for a SHARE. Heavy and light rail are
    stated as weekday boardings, so their ratio is a monotone proxy - right
    sign, right order, not the contraction itself."""
    prev = dict(proposals=[dict(mode='light_rail', abs_step=1.0,
                                basis_is_boardings=True),
                           dict(mode='bus', abs_step=1.0,
                                basis_is_boardings=False)])
    cur = dict(proposals=[dict(mode='light_rail', abs_step=0.1,
                               basis_is_boardings=True),
                          dict(mode='bus', abs_step=2.0,
                               basis_is_boardings=False)])
    c = afp.contraction(prev, cur)
    assert [r['mode'] for r in c['modes']] == ['light_rail', 'bus']
    # the verdict follows bus alone, not the flattering rail proxy
    assert c['mean_step_ratio_share_basis'] == 2.0
    assert c['verdict'].startswith('NOT CONTRACTING')


def test_no_comparable_mode_is_undetermined_rather_than_a_verdict():
    c = afp.contraction(dict(proposals=[]), dict(proposals=[]))
    assert c['verdict'].startswith('UNDETERMINED')


def test_a_constant_the_registry_declares_unmovable_is_refused_in_its_words():
    """Not every refusal is a freeze. C.asc.motorbike ships `definition` with
    no sweep because motorbike is a locked person-level carve and is not in
    RUN.mode_choice.modes at all - its constant cannot change any choice, so a
    step for it would have a band of exactly zero. Reusing the movability
    contract means a constant declared unmovable for ANY reason is refused for
    that reason, rather than this loop keeping its own list."""
    out = afp.propose(
        _fit([_row('car', 0.0), _row('motorbike', 22.8)]),
        _cfg(fields={'C.asc.car_driver': dict(value=0.0, sweep=[-2.0, 2.0]),
                     'C.asc.motorbike': dict(
                         value=0.0, source='definition', sweep=None,
                         description='motorbike is not in '
                                     'RUN.mode_choice.modes')},
             mapping={'car': 'C.asc.car_driver',
                      'motorbike': 'C.asc.motorbike'}))
    assert out['proposals'] == []
    r = [x for x in out['refused'] if x['mode'] == 'motorbike'][0]
    assert r['no_sweep'] is True
    assert 'not in RUN.mode_choice.modes' in r['reason']


def test_a_proposal_outside_the_declared_sweep_is_refused_here_not_hours_later():
    """--config-set would refuse it at apply time, after the operator had
    committed to an arm. A fixed point asking for a value outside the declared
    range is saying the residual is not this constant, and that is worth
    reading now."""
    out = afp.propose(_fit([_row('car', 0.0), _row('bus', 60.0)]),
                      _cfg(fields={
                          'C.asc.car_driver': dict(value=0.0, sweep=[-2.0, 2.0]),
                          'C.asc.bus': dict(value=-1.05, sweep=[-1.1, -1.0])},
                          mapping={'car': 'C.asc.car_driver',
                                   'bus': 'C.asc.bus'}))
    assert out['proposals'] == []
    r = [x for x in out['refused'] if x['mode'] == 'bus'][0]
    assert r['outside_sweep'] is True
    assert 'outside the declared sweep' in r['reason']
