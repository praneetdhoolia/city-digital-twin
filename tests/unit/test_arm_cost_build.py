"""A price is for a stack. The pricer must notice when the stack has changed.

`observed_arms()` filters on FRACTION and PROFILED and on nothing else. It
already warns when it prices on a run that is not the newest - DECISIONS.md
9.155 taught it that after a pre-repair arm quoted 26.3 h against a measured
13.5-18 h - and it had no notion of the controler at all.

So on 9 September 2026 it quoted 22.2 h for the depth arm from five arms that
ALL predated `citysim.PtCrowdingScoring`, the mode-aware teleport refusal and
the router's request counter: a price for a stack that no longer existed, on an
arm whose whole risk was a new scoring term landing on the two highest-volume
event classes inside a mobsim that is three quarters of an iteration. A person
caught it by hand and spent 46 minutes on a probe. §9.153 records what happens
when nobody catches it: the F30 arm ran 45 % over a price read from a stack
differing by one line.

The record already carried what was needed - `controler_sha256`, which resume
detection has refused to match across since issue #28. The pricer just never
looked.
"""


import arm_cost
import run_matsim


def _arm(**kw):
    base = dict(name='20260101T000000_300it_25pct', fraction=0.25,
                median_iteration_s=260.0, reached_iteration=100, setup_s=600.0,
                profiled=False, completion='stopped_at_gate', family='F',
                plain=None, controler_sha256=run_matsim.controler_sha256())
    base.update(kw)
    return base


def test_a_matching_build_says_nothing():
    q = arm_cost.price(300, 0.25, [_arm()])
    assert q.get('build_warning') is None, (
        'the common case must stay quiet, or the warning is noise')


def test_a_changed_build_is_named_and_priced_as_unknown():
    q = arm_cost.price(300, 0.25, [_arm(controler_sha256='0' * 40)])
    w = q.get('build_warning') or ''
    assert 'PRICED ON A DIFFERENT BUILD' in w
    assert run_matsim.controler_sha256()[:16] in w, (
        'name both builds, so a reader can tell which is which')
    assert 'probe' in w, 'and say what would settle it'


def test_a_record_without_a_build_is_a_lower_bound():
    """A run that does not record its build cannot prove it ran this one."""
    q = arm_cost.price(300, 0.25, [_arm(controler_sha256=None)])
    w = q.get('build_warning') or ''
    assert 'DOES NOT RECORD ITS BUILD' in w
    assert 'lower bound' in w


def test_the_hash_is_the_one_resume_already_trusts():
    """Not a second opinion about identity - the same function.

    It hashes the committed Java SOURCE of both trees, not the compiled
    classes: javac output is not guaranteed byte-identical across JDK builds,
    and the source is what is committed and reviewable.
    """
    h = run_matsim.controler_sha256()
    assert len(h) == 64 and int(h, 16) >= 0, 'a sha256 hexdigest'
    assert h == run_matsim.controler_sha256(), 'and a stable one'
