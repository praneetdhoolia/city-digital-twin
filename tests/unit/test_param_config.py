"""Rendering a declared value, and reading the binding that says where it goes.

`src/registry/param_config.py` is the only place that turns a registry value
into the text a tool reads back, and the only place that parses a binding into
a target. Both are one-line-looking functions that decide correctness: the
defect they exist to end was a template writing the string `30:00:00` beside a
field declaring the number 30, and a binding the emitter could not read is a
declared value that silently reaches nothing.

Synthetic inputs only, no city and no schema file: `render`, `hhmmss`,
`parse_target` and `targets_of` are pure.
"""
import pytest

import param_config


# --------------------------------------------------------------------------
# render: the value as the tool reads it back
# --------------------------------------------------------------------------
def test_render_scalars():
    assert param_config.render(42) == '42'
    assert param_config.render('outside') == 'outside'
    assert param_config.render(True) == 'true'
    assert param_config.render(False) == 'false'


def test_render_float_is_a_plain_decimal_not_scientific():
    # %r would give 1e-05, which the config reader does not parse as a number
    assert param_config.render(0.00001) == '0.00001'
    assert param_config.render(1.0) == '1.0'
    assert param_config.render(16.96) == '16.96'


def test_render_list_is_comma_separated():
    assert param_config.render(['car', 'pt', 'walk']) == 'car,pt,walk'
    assert param_config.render((1, 2.5, True)) == '1,2.5,true'


def test_render_refuses_a_null_value():
    with pytest.raises(param_config.ConfigError) as e:
        param_config.render(None)
    assert 'null value' in str(e.value)


# --------------------------------------------------------------------------
# render: the hh:mm:ss conversion, which is where the two representations of
# one value used to drift apart
# --------------------------------------------------------------------------
def test_render_hhmmss_converts_from_the_field_s_own_units():
    fmt = param_config.HHMMSS
    assert param_config.render(30, fmt, 'hours') == '30:00:00'
    assert param_config.render(1.5, fmt, 'hours') == '01:30:00'
    assert param_config.render(90, fmt, 'minutes') == '01:30:00'
    assert param_config.render(90, fmt, 'seconds') == '00:01:30'


def test_render_hhmmss_keeps_hours_past_midnight():
    # wrapping 30 h to 06:00:00 would silently halve the simulated day
    assert param_config.render(30, param_config.HHMMSS, 'h') == '30:00:00'
    assert param_config.hhmmss(30 * 3600) == '30:00:00'


def test_render_hhmmss_rounds_rather_than_truncating():
    assert param_config.hhmmss(59.6) == '00:01:00'
    assert param_config.hhmmss(0) == '00:00:00'


@pytest.mark.parametrize('units', [None, '', 'km', 'AUD/h', 'minutes_per_trip'])
def test_render_hhmmss_refuses_to_guess_the_units(units):
    with pytest.raises(param_config.ConfigError) as e:
        param_config.render(30, param_config.HHMMSS, units)
    assert 'time' in str(e.value) and 'guessed' in str(e.value)


# --------------------------------------------------------------------------
# parse_target: module.param, module.setType[selector].param, and the refusals
# --------------------------------------------------------------------------
def test_parse_target_plain_parameter():
    assert param_config.parse_target('qsim.endTime') == \
        ('qsim', None, None, 'endTime')


def test_parse_target_parameter_set():
    assert param_config.parse_target('scoring.modeParams[bike].constant') == \
        ('scoring', 'modeParams', 'bike', 'constant')


def test_parse_target_keeps_a_star_selector_as_the_selector():
    # `[*]` is expanded by the emitter, not here: it must survive parsing
    assert param_config.parse_target('network.wayDefault[*].freespeedFactor') == \
        ('network', 'wayDefault', '*', 'freespeedFactor')


def test_parse_target_strips_whitespace_and_the_leading_dot():
    assert param_config.parse_target('  scoring.modeParams[pt].constant ') == \
        ('scoring', 'modeParams', 'pt', 'constant')


def test_parse_target_selector_may_hold_a_dotted_key():
    module, set_type, selector, param = param_config.parse_target(
        'strategy.strategysettings[ChangeExpBeta.v2].weight')
    assert (module, set_type, selector, param) == \
        ('strategy', 'strategysettings', 'ChangeExpBeta.v2', 'weight')


@pytest.mark.parametrize('target,fragment', [
    ('qsim', 'not module.param'),
    ('scoring.modeParams.bike.constant', 'nested path but no [selector]'),
    ('scoring.modeParams[].constant', 'not module.setType[selector].param'),
    ('scoring.modeParams[bike]', 'not module.setType[selector].param'),
])
def test_parse_target_refuses_a_binding_it_cannot_read(target, fragment):
    # a binding the emitter cannot read is a value that would silently not be
    # written, which is the failure this module exists to end
    with pytest.raises(param_config.ConfigError) as e:
        param_config.parse_target(target)
    assert fragment in str(e.value)


# --------------------------------------------------------------------------
# targets_of: a field may write to more than one parameter
# --------------------------------------------------------------------------
def test_targets_of_reads_every_target_a_field_names():
    field = {'matsim_param': 'qsim.startTime, qsim.endTime'}
    assert param_config.targets_of(field, 'matsim_param') == [
        ('qsim', None, None, 'startTime'),
        ('qsim', None, None, 'endTime'),
    ]


def test_targets_of_is_empty_for_a_field_with_no_binding():
    assert param_config.targets_of({}, 'matsim_param') == []
    assert param_config.targets_of({'matsim_param': ''}, 'matsim_param') == []


def test_targets_of_ignores_a_trailing_separator():
    field = {'matsim_param': 'qsim.endTime,'}
    assert param_config.targets_of(field, 'matsim_param') == [
        ('qsim', None, None, 'endTime')]
