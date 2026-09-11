"""Both paths that remove a plan honour `RUN.replanning.plan_selector_for_removal`.

MATSim removes a plan through the selector `replanning.planSelectorForRemoval`
names. `citysim.EscortCoherenceListener` also removes plans - whenever a
coherence proposal pushes a person over `maxAgentPlanMemorySize` - and until
11 September 2026 it did so by its own worst-score rule (eighth project
report, area 6). #174's paired control, `SelectRandom` against the shipped
`WorstPlanSelector`, would then have switched one of the two removal paths
and the arm would have measured half a control. The listener now injects the
selector MATSim binds (un-named, as `PlanSelector<Plan, Person>`) and asks
it, re-selecting at random if it took the selected plan - what
`GenericStrategyManagerImpl.removePlans` does.

Source-text invariants, comments stripped first (a check a comment can
satisfy is not a check, DECISIONS.md 9.164).
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
LISTENER = os.path.join(REPO, 'src', 'java', 'citysim', 'EscortCoherenceListener.java')
MODE_CHOICE = os.path.join(REPO, 'src', 'java', 'citysim', 'GatedSubtourModeChoice.java')


def _code(path):
    out = []
    for line in open(path, encoding='utf-8').read().split('\n'):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or s.startswith('/*'):
            continue
        out.append(line)
    return '\n'.join(out)


def _trim_body():
    code = _code(LISTENER)
    m = re.search(r'private void trim\(final Person person\) \{(.*?)\n    \}\n', code, re.S)
    assert m, 'trim() is gone or renamed'
    return m.group(1)


def test_the_listener_injects_matsims_removal_selector():
    code = _code(LISTENER)
    assert 'import org.matsim.core.replanning.selectors.PlanSelector;' in code
    assert re.search(r'@Inject\s+EscortCoherenceListener\(final Scenario scenario,\s*'
                     r'final PlanSelector<Plan, Person> removal\)', code), (
        'the selector must arrive by injection, un-named, exactly as '
        'StrategyManagerModule binds it')


def test_trim_asks_the_selector_and_never_ranks_scores_itself():
    body = _trim_body()
    assert 'removal.selectPlan(person)' in body
    assert 'getScore()' not in body, (
        'trim() ranks plans by score itself again - that is the bypass #174 '
        'measured against')


def test_trim_reselects_at_random_when_the_selector_took_the_selected_plan():
    body = _trim_body()
    assert 'RandomPlanSelector' in body and 'setSelectedPlan' in body


def test_an_undecomposable_plan_is_treated_as_mixed():
    code = _code(MODE_CHOICE)
    m = re.search(r'private boolean isAnySubtourMixed\(final Plan plan\) \{(.*?)\n        \}\n', code, re.S)
    assert m
    body = m.group(1)
    i = body.find('catch (final RuntimeException')
    assert i >= 0, 'the decomposition is no longer guarded'
    catch_block = body[i:body.find('return false;', i)]
    assert 'return true;' in catch_block and 'return false;' not in catch_block, (
        'a plan whose decomposition throws must take the conservative branch, '
        'not pass as clean')
    assert 'DECOMPOSE_FAILED.incrementAndGet()' in body
