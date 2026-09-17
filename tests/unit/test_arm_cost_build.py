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


def test_an_orphans_setup_is_read_from_its_own_stopwatch():
    """The routers pair's memo held 34 of 250 iterations (DECISIONS.md 9.176);
    `wall - sum(memo)` booked the other 216 as 22.8 h of setup and quoted the
    next arm at 48.8 h against a 27.4 h run. The JVM's stopwatch covers them."""
    wall = 98590.8
    memo = {i: 360.0 for i in range(34)}
    plain = dict(plain_median_s=360.0, last_iteration=250,
                 iteration_total_s=96700.0)
    setup = arm_cost.setup_seconds(wall, 250, 362.3, memo, plain)
    assert setup is not None and setup < 3600, (
        'a 27.4 h run whose stopwatch timed 26.9 h of iterations has minutes '
        'of setup, not 22.8 h: %r' % setup)
    assert abs(setup - (wall - 96700.0)) < 1e-6


def test_a_complete_memo_is_the_setup_clock():
    memo = {i: 300.0 for i in range(5)}
    assert arm_cost.setup_seconds(2000.0, 4, 300.0, memo, None) == 500.0


def test_no_clock_falls_back_to_the_median():
    assert arm_cost.setup_seconds(2000.0, 4, 300.0, {}, None) == 500.0
    assert arm_cost.setup_seconds(None, 4, 300.0, {}, None) is None
