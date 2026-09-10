"""What a passenger pays for a service's frequency and its variability.

`C.time_weights.beta_headway` (0.5) and `C.time_weights.beta_reliability` (1.3)
are declared with units, literature provenance and sweeps, written into
`params/C1_parameters.json` by `build_params.py`, and read by NOTHING after
that. `check_hardcoding.py` reported 0 items and both fields passed it, because
its test for "wired" is that the key appears as a value somewhere in the source
tree - which it does, in the builder. The two were recommendation 7 of the
9 September assessment and recommendation 13 of the 10 September one, both
phrased *"wire them, or retire them"*, and neither landed (#175).

They are now wired, and the invariants below are what make the wiring a
faithful reading of the two literature definitions rather than a lever:

* the gate ships `absent`, so the shipped model is unchanged;
* neither price is a number in the code - both are DERIVED by the emitter from
  the trip-weighted VOT identity every other derived scoring value uses;
* the standard deviation is MEASURED from the run's own arrival delays and is
  never seeded, so the first scored iteration carries no reliability charge;
* the driver of a transit vehicle is not charged as its passenger.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
GROUP = os.path.join(REPO, 'src', 'java', 'citysim', 'ServiceQualityConfigGroup.java')
SCORING = os.path.join(REPO, 'src', 'java', 'citysim', 'ServiceQualityScoring.java')
CONTROLER = os.path.join(REPO, 'src', 'java', 'citysim', 'CitysimControler.java')
EMITTER = os.path.join(REPO, 'src', 'build', 'build_matsim_run_inputs.py')

if os.path.join(REPO, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(REPO, 'src'))


def _code(path):
    out = []
    for line in open(path, encoding='utf-8').read().split('\n'):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or s.startswith('/*') \
                or s.startswith('#'):
            continue
        out.append(line)
    return '\n'.join(out)


def _fields():
    import registry
    fields, _origin = registry.load_registry(
        os.path.join(REPO, 'cities', os.environ.get('CITYSIM_CITY', 'newcastle'),
                     'registry'))
    return fields


def test_the_gate_is_declared_and_ships_absent():
    field = _fields()['C.time_weights.service_quality_representation']
    assert field['matsim_param'] == 'serviceQuality.representation'
    assert field['value'] == 'absent', (
        'the gate does not ship at `absent`, so wiring the two weights would '
        'change the model rather than give it a control')
    assert set(field['sweep']['categorical']) == {
        'absent', 'headway', 'headway_and_reliability'}


def test_both_weights_now_name_a_consumer_that_reaches_matsim():
    """The whole point: they reached a JSON file and stopped."""
    fields = _fields()
    for key in ('C.time_weights.beta_headway', 'C.time_weights.beta_reliability'):
        consumers = fields[key].get('consumers') or []
        assert 'src/build/build_matsim_run_inputs.py' in consumers, (
            '%s does not name the emitter as a consumer, so it still reaches '
            'params/C1_parameters.json and stops there' % key)


def test_the_prices_are_derived_by_the_emitter_and_absent_from_the_java():
    """A default in the config group would be a taste typed into the code."""
    code = _code(GROUP)
    for setter in ('headwayUtilsPerMin', 'reliabilityUtilsPerMin', 'headwayCapMin'):
        assert re.search(r'private double %s = Double\.NaN;' % setter, code), (
            '%s carries a literal default, which is a price decided in the '
            'code rather than derived from the declared weights' % setter)
    emitter = _code(EMITTER)
    assert "runtime['serviceQuality.headwayUtilsPerMin']" in emitter
    assert "runtime['serviceQuality.reliabilityUtilsPerMin']" in emitter
    assert "runtime['serviceQuality.headwayCapMin']" in emitter
    # the identity, not a number
    assert re.search(r"serviceQuality\.headwayUtilsPerMin.*?beta_headway",
                     emitter, re.S)
    assert re.search(r"serviceQuality\.reliabilityUtilsPerMin.*?beta_reliability",
                     emitter, re.S)


def test_a_gate_turned_on_without_its_prices_is_refused():
    code = _code(GROUP)
    assert 'require(this.headwayUtilsPerMin' in code
    assert 'require(this.headwayCapMin' in code
    assert 'require(this.reliabilityUtilsPerMin' in code
    assert 'Double.isNaN(value)' in code, (
        'an unsupplied price is not refused, so the mobsim would charge NaN '
        'and every score would be NaN with it')
    assert 'value < 0.0' in code, (
        'a negative price is not refused, so the model would PAY a passenger '
        'for an infrequent or unreliable service')


def test_the_reliability_measurement_is_never_seeded():
    """A seeded standard deviation would be an invented observation."""
    code = _code(SCORING)
    assert 'event.getDelay()' in code, (
        'the spread is not measured from the run\'s own arrival delays')
    assert 'this.sdMin.clear()' in code and 'notifyAfterMobsim' in code, (
        'the measured spread is not recomputed per mobsim')
    assert 'firstMobsim' in code, (
        'the first scored iteration does not report that it carries no '
        'reliability charge, so a zero would read as a measurement')
    # no literal standard deviation anywhere
    assert not re.search(r'sdMin\.put\(\s*[^,]+,\s*\d', code), (
        'a standard deviation is written from a literal')


def test_the_driver_is_not_charged_as_a_passenger():
    code = _code(SCORING)
    assert 'event.getPersonId().equals(service.driver)' in code, (
        "the transit driver is not excluded, so every vehicle's own driver "
        'would be charged for the service they are operating')


def test_the_binding_is_only_under_the_gate():
    code = _code(CONTROLER)
    m = re.search(r'if\s*\(\s*serviceQuality\.isEnabled\(\)\s*\)\s*\{(.*?)\n        \}',
                  code, re.S)
    assert m, 'no `if (serviceQuality.isEnabled())` block in CitysimControler'
    assert 'ServiceQualityScoring.class' in m.group(1)
    assert 'Singleton.class' in m.group(1), (
        'the scoring handler is not a singleton, so the measured spread would '
        'not survive from one iteration to the next')
    outside = code.replace(m.group(0), '')
    assert 'ServiceQualityScoring' not in outside, (
        'ServiceQualityScoring is referenced outside the gate, so `absent` '
        'would not recover the previous model')


def test_the_scoring_class_declares_no_taste_of_its_own():
    literals = re.findall(r'(?<![\w.])\d+\.\d+', _code(SCORING))
    assert set(literals) <= {'60.0', '0.0'}, (
        'ServiceQualityScoring carries numeric literal(s) %s beyond the '
        'seconds-per-minute conversion and the zero comparison' % literals)
