"""The PT submode's own constant reaches the router that picks the submode.

`SwissRailRaptor` decides which service a PT traveller takes, and therefore
WHICH SUBMODE they end up on: the mode-choice operator proposes `pt`, and the
raptor alone turns that into a bus, a train, a tram or a ferry. Its stock
objective is `DefaultRaptorInVehicleCostCalculator` - in-vehicle seconds times
one coefficient - so the per-submode constants `scoring.modeParams` carries
reach SCORING and never the ROUTER. Over the F31 arm's whole plan memory only
974 of 154,347 persons (0.63 %) held plans differing in PT submode at all.

`citysim.RaptorModeCostCalculator` closes that, and the invariants below are
what make it a CONSISTENCY rather than a second set of tastes:

* it introduces no number of its own - the constants are already declared as
  `C.asc.*` and already emitted into `scoring.modeParams`;
* it restates the default's time cost exactly, so `absent` and `mode_constant`
  differ by the constant alone;
* it is bound ONLY under the gate, and the gate ships `absent`.

There is no Java test harness in this repository (`tests/unit` is Python and
`src/java` compiles against `.tools/`), so the source invariants are asserted
on the source the way `test_direct_walk_counters.py` asserts its own - with
comment lines stripped first, because a check a comment can satisfy is the
defect DECISIONS.md 9.160 was written about. The wiring invariants are
asserted against the real registry and the real binding resolver.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
CALC = os.path.join(REPO, 'src', 'java', 'citysim', 'RaptorModeCostCalculator.java')
GROUP = os.path.join(REPO, 'src', 'java', 'citysim', 'RaptorModeCostConfigGroup.java')
CONTROLER = os.path.join(REPO, 'src', 'java', 'citysim', 'CitysimControler.java')

if os.path.join(REPO, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(REPO, 'src'))


def _src(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _code(path):
    """The source with comment-only lines dropped, so prose cannot satisfy a rule."""
    out = []
    for line in _src(path).split('\n'):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*') \
                or stripped.startswith('/*'):
            continue
        out.append(line)
    return '\n'.join(out)


def test_the_added_cost_is_the_declared_constant_negated():
    """The value added is -modeParams.getConstant(), not a number of its own."""
    code = _code(CALC)
    assert re.search(r'costs\.put\(\s*mode\s*,\s*-\s*params\.getConstant\(\)\s*\)', code), (
        'the priced cost is not -params.getConstant(): a mode constant is a '
        'UTILITY and getInVehicleCost returns a COST, so the sign must flip '
        'and the value must come from the declared scoring constant')


def test_the_calculator_declares_no_number_of_its_own():
    """Every numeric literal in the class is a structural 0.0, never a taste."""
    code = _code(CALC)
    literals = re.findall(r'(?<![\w.])\d+\.\d+', code)
    assert set(literals) <= {'0.0'}, (
        'numeric literal(s) %s in RaptorModeCostCalculator - the constants are '
        'declared as C.asc.* and emitted into scoring.modeParams; a number '
        'typed here is a taste nobody can sweep' % sorted(set(literals)))


def test_the_time_cost_restates_the_stock_calculator():
    """`absent` and `mode_constant` must differ by the constant alone."""
    code = _code(CALC)
    assert re.search(
        r'inVehicleTime\s*\*\s*-\s*marginalUtilityOfTravelTime_utl_s', code), (
        'the time term is not DefaultRaptorInVehicleCostCalculator restated '
        '(inVehicleTime * -marginalUtilityOfTravelTime_utl_s), so the gate '
        'would change more than the constant it claims to add')
    assert re.search(r'return\s+timeCost\s*\+\s*modeCost\(vehicle\)\s*;', code), (
        'the returned cost is not the stock time cost plus the mode cost')


def test_the_submode_is_read_from_the_vehicle_not_typed():
    """No city's mode names are written into the calculator."""
    code = _code(CALC)
    assert 'vehicle.getType().getNetworkMode()' in code, (
        'the submode must come from the transit vehicle type\'s own '
        'networkMode - the vocabulary scoring.modeParams is keyed by')
    for typed in ('"bus"', '"rail"', '"tram"', '"ferry"'):
        assert typed not in code, (
            '%s is typed into RaptorModeCostCalculator; the mode vocabulary is '
            'the schedule\'s, not the framework\'s' % typed)


def test_the_price_table_is_immutable_and_the_only_mutable_field_is_concurrent():
    """One injected instance serves every routing thread."""
    code = _code(CALC)
    assert 'Collections.unmodifiableMap' in code, (
        'the price table is not unmodifiable; MATSim routes on many threads '
        'against ONE injected RaptorInVehicleCostCalculator')
    mutable = re.findall(r'^\s*private\s+(?!static)(?!final)\w[\w<>, .]*\s+\w+\s*;',
                         code, re.M)
    assert not mutable, 'non-final instance field(s): %s' % mutable
    assert 'ConcurrentHashMap.newKeySet()' in code, (
        'the log-once set must be concurrent')


def test_the_umbrella_mode_is_not_priced():
    """One constant on every leg alike separates no two submodes."""
    code = _code(GROUP)
    assert re.search(r'modes\.remove\(TransportMode\.pt\)', code), (
        'pt is not removed from the priced set, so under the aggregate '
        'vocabulary the gate would shift PT against direct walk and control '
        'nothing between submodes')
    assert 'IllegalStateException' in code and 'pt_submode_scoring' in code, (
        'a config carrying only the umbrella mode must be REFUSED, not run '
        'with a gate that controls nothing')


def test_a_submode_without_a_constant_is_refused_not_priced_at_zero():
    """A silent asymmetric zero is the failure the check exists to stop."""
    group = _code(GROUP)
    assert 'scoring.modeParams' in group and 'missing' in group, (
        'checkConsistency does not refuse a declared transit mode that has no '
        'scoring.modeParams block')
    calc = _code(CALC)
    assert re.search(r'if\s*\(\s*params\s*==\s*null\s*\)', calc), (
        'the calculator does not refuse a mode with no constant; it would '
        'price it at 0.0 beside its priced neighbours')


def test_getOrCreateModeParams_is_never_used():
    """It MUTATES the config and invents a 0.0 constant for a mode never declared."""
    for path in (CALC, GROUP):
        assert 'getOrCreateModeParams' not in _code(path), (
            '%s calls getOrCreateModeParams, which would create the very '
            'silent zero the consistency check refuses' % os.path.basename(path))


def test_the_binding_is_installed_only_under_the_gate():
    """`absent` must leave SwissRailRaptorModule's own calculator in place."""
    code = _code(CONTROLER)
    m = re.search(
        r'if\s*\(\s*raptorModeCost\.isModeConstant\(\)\s*\)\s*\{(.*?)\n        \}',
        code, re.S)
    assert m, 'no `if (raptorModeCost.isModeConstant())` block in CitysimControler'
    assert 'RaptorInVehicleCostCalculator.class' in m.group(1), (
        'the RaptorInVehicleCostCalculator binding is not inside the gate')
    outside = code.replace(m.group(0), '')
    assert 'RaptorInVehicleCostCalculator' not in outside, (
        'RaptorInVehicleCostCalculator is bound outside the gate, so `absent` '
        'would not recover the previous model')


def test_the_group_is_registered_on_every_stack():
    """An unmaterialised config module fails MATSim's own consistency check.

    The assertion is STRUCTURAL, not a pinned index. It used to read
    ``groups[16] = raptorModeCost`` against ``ConfigGroup[17 + ...]``, which
    made every later module's arrival a failure of THIS test rather than of
    anything about the raptor gate - the test asserting its neighbours'
    positions instead of its own invariant. What actually has to hold is that
    the group is assigned a slot, that the array is exactly big enough for
    every fixed slot, and that the extra groups start immediately after the
    last of them.
    """
    code = _code(CONTROLER)
    assert 'new RaptorModeCostConfigGroup()' in code
    slots = {int(i): name for i, name
             in re.findall(r'groups\[(\d+)\]\s*=\s*(\w+)\s*;', code)}
    assert 'raptorModeCost' in slots.values(), (
        'raptorModeCost is not assigned a slot in the groups array')
    fixed = max(slots) + 1
    assert sorted(slots) == list(range(fixed)), (
        'the groups array has a hole in it: %s' % sorted(slots))
    size = re.search(r'ConfigGroup\[(\d+)\s*\+\s*extraGroups\.size\(\)\]', code)
    assert size and int(size.group(1)) == fixed, (
        'the groups array is sized for %s fixed slot(s) against %d assigned'
        % (size.group(1) if size else 'no', fixed))
    offset = re.search(r'groups\[(\d+)\s*\+\s*i\]\s*=\s*extraGroups\.get\(i\)', code)
    assert offset and int(offset.group(1)) == fixed, (
        'the extra groups start at %s against %d fixed slot(s), so one would '
        'overwrite a materialised module'
        % (offset.group(1) if offset else 'no offset', fixed))


def test_the_gate_is_declared_and_ships_absent():
    """The registry decides it, not the code."""
    import registry
    fields, _origin = registry.load_registry(
        os.path.join(REPO, 'cities', os.environ.get('CITYSIM_CITY', 'newcastle'),
                     'registry'))
    field = fields['C.raptor.mode_cost_representation']
    assert field['matsim_param'] == 'raptorModeCost.representation'
    assert field['value'] == 'absent', (
        'the gate must SHIP absent: it changes PT against direct walk as well '
        'as between submodes, so it is a family-opening change a run compares')
    assert field['sweep']['categorical'] == ['absent', 'mode_constant']


def test_the_gate_reaches_the_emitted_config():
    """A declared value that reaches nothing is the defect, not the fix."""
    from registry import param_config
    assert 'C.raptor.mode_cost_representation' in param_config.bound_fields('matsim')
    assert param_config.targets_of(
        {'matsim_param': 'raptorModeCost.representation'}, 'matsim_param') == [
            ('raptorModeCost', None, None, 'representation')]
