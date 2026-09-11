"""The three demand-layer changes of DECISIONS.md 9.164, each on its own defect.

**#167 - every leg states its routing mode.** Under
`routing.accessEgressType = accessEgressModeToLink` the router turns a one-leg
trip into three by inserting access and egress walk legs. This project's plans
declared no `routingMode` on any leg - zero lines mentioned it - so MATSim
inferred each inserted leg's from its OWN mode, read `walk` beside a `car` main
leg, and `PersonPrepareForSim` rejected the trip the router had just built on
40 agents (9.161). Stating it is a no-op at `none` and the whole of what was
missing.

**#86 / #48 - the declared passenger is put on `ride`.** A serving tour reads
`car` in EVERY seeded plan, because the demand declares that the driver drives;
the passenger they carry got a ride variant as ONE alternative and drew a mode
in the rest. Of 20,902 declared escort pairs in sample, 10,224 have the
passenger driving their own car against 7,821 co-assigned (9.163).

**#30 - a tour that will not fit does not discard its successors.** The
placement loop used to `break`, dropping every tour still to be placed, four
lines above a branch that reaches the same state and `continue`s.
"""
import ast
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
CITY = os.path.join(REPO, 'cities', os.environ.get('CITYSIM_CITY', 'newcastle'))
PLANS = os.path.join(REPO, 'src', 'build', 'build_matsim_plans.py')
CHAINS = os.path.join(REPO, 'src', 'build', 'build_activity_chains.py')


def _src(path):
    return io.open(path, encoding='utf-8').read()


def _code(path):
    """The source with comment-only lines dropped.

    A check a comment can satisfy is the defect DECISIONS.md 9.160 was written
    about - and this file caught itself: the comment explaining that the branch
    USED to `break` satisfied a test asserting that it no longer does.
    """
    return '\n'.join(line for line in _src(path).splitlines()
                     if not line.strip().startswith('#'))


def _fields():
    import registry
    fields, _origin = registry.load_registry(os.path.join(CITY, 'registry'))
    return fields


# -- #167 ------------------------------------------------------------------
def test_every_leg_states_its_routing_mode():
    src = _src(PLANS)
    assert 'name="routingMode"' in src, (
        'no leg carries a routingMode attribute, so an inserted access leg '
        'would infer `walk` beside a `car` main leg and the trip would be '
        'rejected (9.161)')
    m = re.search(r"w\.write\('\\t\\t\\t<leg mode=.*?% \((\w+), (\w+)\)\)", src, re.S)
    assert m, 'the leg write no longer matches the expected shape'
    assert m.group(1) == m.group(2), (
        "the routing mode is not the leg's own mode: a single-leg trip's "
        'INFERRED routing mode already equals its mode, and any other value '
        'would change the model at access_egress_type = none rather than '
        'being the no-op this is meant to be')


def test_the_access_egress_gate_is_declared_with_both_alternatives():
    field = _fields()['RUN.routing.access_egress_type']
    assert field['matsim_param'] == 'routing.accessEgressType'
    assert 'none' in field['sweep']['categorical'], (
        'the pre-change value is not in the sweep, so the arm that turns this '
        'on would have no control to run against')


# -- #86 / #48 -------------------------------------------------------------
def test_the_bound_passenger_placement_is_declared():
    field = _fields()['B.mode.bound_passenger_placement']
    assert set(field['sweep']['categorical']) == {'every_plan', 'alternative'}
    assert field['sweep_role'] == 'answer'
    assert 'src/build/build_matsim_plans.py' in (field.get('consumers') or [])


def test_the_passenger_is_placed_the_way_the_driver_is():
    """Symmetry is the whole claim: `car` in every plan, so `ride` in every plan."""
    src = _src(PLANS)
    m = re.search(r'bound_every = \(BOUND_PASSENGER_PLACEMENT ==.*?plan_set\.append\(\(p, over\)\)',
                  src, re.S)
    assert m, 'the every-plan branch is gone from the seed'
    body = m.group(0)
    assert "p[tid] = 'car'" in body and "p[tid] = 'ride'" in body, (
        'the seeded plan no longer holds the serving tour at `car` and the '
        'bound tour at `ride` in the same loop, which is the symmetry claimed')
    assert 'CHAIN_BASED_MODES' in body, (
        'a partially bound tour can take a chain-based base, which mixes the '
        'subtour - the state ChooseRandomLegModeForSubtour refuses and that '
        'crashed two arms (9.119)')


def test_the_old_variant_blocks_are_skipped_under_every_plan():
    """Otherwise plan memory fills with copies of the same assignment."""
    src = _src(PLANS)
    assert 'if ride_tours and not bound_every:' in src
    assert 'if partial_tours and not bound_every:' in src
    assert "bound_placement['plans_folded']" in src, (
        'duplicate seeded plans are not folded, so a person whose whole day '
        'is bound would spend several of their eight memory slots on copies')


def test_the_committed_plans_were_rebuilt_with_the_builder():
    """A builder changed without a rebuild cannot reproduce the package."""
    report = json.load(io.open(
        os.path.join(CITY, 'demand', 'plans', 'matsim', '_plans_report.json'),
        encoding='utf-8'))
    for day, block in report['by_day'].items():
        bp = block.get('bound_placement')
        assert bp, '%s carries no bound_placement block' % day
        assert bp['placement'] == 'every_plan', (
            '%s was built at placement %r, so the committed plans are not the '
            'ones the declared value produces' % (day, bp['placement']))
        assert bp['ride_tours'] > 0, (
            '%s reached no bound tour at all' % day)


# -- #30 -------------------------------------------------------------------
def test_a_tour_that_will_not_fit_does_not_discard_its_successors():
    src = _code(CHAINS)
    m = re.search(r'if legs_m is None:(.*?)\n        if arr_home > DAY_HORIZON_S:',
                  src, re.S)
    assert m, 'the placement failure branch is gone'
    body = m.group(1)
    assert 'break' not in body, (
        'the branch still breaks out of the placement loop, discarding every '
        'tour still to be placed - four lines above a branch that reaches the '
        'same state and continues')
    assert 'continue' in body
    assert 'dropped[2]' in body, (
        'the tours the old break would have discarded unattempted are not '
        'counted, so the fix could not be measured')


def test_the_recovered_tours_are_reported():
    report = json.load(io.open(
        os.path.join(CITY, 'demand', 'plans', '_activity_chains_report.json'),
        encoding='utf-8'))
    for day, block in report['by_day'].items():
        assert 'tours_reattempted_after_a_failed_tour' in block, (
            '%s does not report what the fix recovered' % day)


def test_the_placement_loop_still_parses_as_one_loop():
    """A `continue` in the wrong block would silently change the day's shape."""
    tree = ast.parse(_src(CHAINS))
    fns = [n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name == 'build_day']
    assert len(fns) == 1
