"""PT submodes as alternatives A PLAN CAN HOLD, not one `pt` a router splits.

`RUN.mode_choice.modes` offers `pt` as ONE alternative and SwissRailRaptor
decides the submode downstream, so over the F31 arm's whole plan memory only
974 of 154,347 persons (0.63 %) ever held plans differing in which submode they
use (DECISIONS.md 9.160). A scoring constant reallocates between plans an agent
already holds, so for 99.37 % of the population `C.asc.bus` and
`C.asc.light_rail` are plan-choice levers and never submode levers - the
structural half of light rail at -57.3 % against heavy rail at +225.0 %.

`citysim.PtSubmodeChoiceConfigGroup` + `citysim.SubmodeRaptorProvider` give
that layer a control (#49). The invariants below are what make it safe to ship:

* it is bound ONLY under the gate, and the gate ships `aggregate`;
* it filters the SCHEDULE, never the answer - refusing an itinerary because it
  used the wrong submode would report a submode as infeasible exactly where it
  competes hardest;
* it does not leave a seeded `pt` leg on a mode outside the choice set, which
  is the absorbing state `RUN.mode_choice.modes` already records for `ride`;
* it declares no value of its own.

There is no Java test harness in this repository, so the source invariants are
asserted on the source with comment lines stripped first - a check a comment
can satisfy is the defect DECISIONS.md 9.160 was written about. The wiring
invariants are asserted against the real registry.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
GROUP = os.path.join(REPO, 'src', 'java', 'citysim', 'PtSubmodeChoiceConfigGroup.java')
PROVIDER = os.path.join(REPO, 'src', 'java', 'citysim', 'SubmodeRaptorProvider.java')
CONTROLER = os.path.join(REPO, 'src', 'java', 'citysim', 'CitysimControler.java')

if os.path.join(REPO, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(REPO, 'src'))


def _code(path):
    """The source with comment-only lines dropped."""
    out = []
    for line in open(path, encoding='utf-8').read().split('\n'):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or s.startswith('/*'):
            continue
        out.append(line)
    return '\n'.join(out)


def _fields():
    import registry
    fields, _origin = registry.load_registry(
        os.path.join(REPO, 'cities', os.environ.get('CITYSIM_CITY', 'newcastle'),
                     'registry'))
    return fields


def test_the_gate_is_declared_and_ships_aggregate():
    """The registry decides it, not the code, and the shipped model is unchanged."""
    field = _fields()['RUN.mode_choice.pt_submode_alternatives']
    assert field['matsim_param'] == 'ptSubmodeChoice.representation'
    assert field['value'] == 'aggregate', (
        'the gate does not ship at `aggregate`, so declaring it would change '
        'the model rather than give it a control')
    assert set(field['sweep']['categorical']) == {'aggregate', 'alternatives'}
    assert field['sweep_role'] == 'answer'


def test_the_seed_submode_is_declared_and_the_java_holds_no_default():
    """A default in the Java would be the same value decided in two places."""
    field = _fields()['RUN.mode_choice.pt_submode_seed']
    assert field['matsim_param'] == 'ptSubmodeChoice.seedSubmode'
    code = _code(GROUP)
    assert 'private String seedSubmode = "";' in code, (
        'the config group carries a literal seed submode, which shadows '
        'RUN.mode_choice.pt_submode_seed (check_hardcoding.py category 6)')
    assert 'seedSubmode.isEmpty()' in code, (
        'an unsupplied seed submode is not refused, so the gate could run '
        'with no seed at all and rewrite every pt leg to the empty mode')


def test_the_binding_is_only_under_the_gate():
    """`aggregate` must recover the previous model exactly."""
    code = _code(CONTROLER)
    m = re.search(r'if\s*\(\s*ptSubmodeChoice\.isAlternatives\(\)\s*\)\s*\{(.*?)\n        \}',
                  code, re.S)
    assert m, 'no `if (ptSubmodeChoice.isAlternatives())` block in CitysimControler'
    assert 'addRoutingModuleBinding' in m.group(1), (
        'the per-submode routing modules are not bound inside the gate')
    outside = code.replace(m.group(0), '')
    assert 'SubmodeRaptorProvider' not in outside, (
        'SubmodeRaptorProvider is referenced outside the gate, so `aggregate` '
        'would not recover the previous model')


def test_the_umbrella_leaves_the_choice_set_with_the_submodes():
    """Both halves, or the constants are unidentifiable."""
    code = _code(GROUP)
    m = re.search(r'static String\[\] applyChoiceSet\(.*?\n    \}', code, re.S)
    assert m, 'applyChoiceSet is gone'
    body = m.group(0)
    assert 'TransportMode.pt.equals(mode)' in body and 'continue;' in body, (
        'the umbrella mode is not removed from the choice set, so an agent '
        "would choose between 'bus' and 'any pt including bus'")
    assert 'setModes(modes)' in body, 'the derived choice set is never applied'
    assert 'hadUmbrella' in body, (
        'a choice set that never carried `pt` is not refused, so the gate '
        'would silently apply to a vocabulary it was not designed against')


def test_the_seeded_pt_leg_is_rewritten_and_counted():
    """A seeded subtour on a mode outside the choice set is absorbing."""
    code = _code(PROVIDER)
    m = re.search(r'static void reseedPtLegs\(.*?\n    \}', code, re.S)
    assert m, 'reseedPtLegs is gone'
    body = m.group(0)
    assert 'leg.setMode(seedSubmode)' in body
    assert 'leg.setRoutingMode(seedSubmode)' in body, (
        'the routing mode is not moved with the leg mode, so the rewritten '
        'trip would carry two routing modes and PersonPrepareForSim would '
        'reject it - the 9.161 failure in a new costume')
    assert 'leg.setRoute(null)' in body, (
        'the stale pt route survives the rewrite, so the mobsim would be '
        'handed a transit route on a leg the router never answered')
    assert 'LOG.info' in body, 'the rewrite is not counted or logged'


def test_the_schedule_is_filtered_not_the_answer():
    """Filtering the answer reports a submode infeasible where it competes."""
    code = _code(PROVIDER)
    m = re.search(r'static TransitSchedule filter\(.*?\n    \}', code, re.S)
    assert m, 'filter() is gone'
    body = m.group(0)
    assert 'route.getTransportMode()' in body, (
        'the filter does not key on the route transport mode')
    assert 'addStopFacility' in body, (
        'the filtered schedule carries no stop facilities, so the raptor '
        'would build an empty access quadtree and answer nothing')
    assert 'routes == 0' in body, (
        'a submode with no route in the mapped schedule is not refused, so '
        'it would be an alternative every agent is refused and the gate '
        'would read that refusal as a taste')


def test_the_provider_declares_no_number_of_its_own():
    """Every numeric literal is structural, never a taste."""
    for path in (GROUP, PROVIDER):
        literals = re.findall(r'(?<![\w.])\d+\.\d+', _code(path))
        assert not literals, (
            '%s carries numeric literal(s) %s - a value in the code is a '
            'modelling choice nobody can see or sweep'
            % (os.path.basename(path), literals))
