"""The direct-walk router's counters describe the RUN, not one routing thread.

`NetworkDirectWalkPtRouter` is bound in `CitysimControler` as
`addRoutingModuleBinding(pt).toProvider(RouterProvider.class)` with NO scope,
so Guice builds a NEW router for every routing thread in every iteration.
Instance counters therefore restart at zero perhaps 1,600 times in a
100-iteration arm, and two things followed from that:

* the "log the first 3" sample became "the first 3 PER THREAD PER ITERATION"
  and emitted 19,469 lines on the F28 arm - about 36% of its log;
* the `decided % 100000` progress line has never fired once, because no single
  thread-iteration ever reaches 100,000 decisions.

The fix is run-lifetime static `AtomicLong`s, and the progress line evaluated
on every decision rather than hung off the branch that returns the walk. This
file pins the shape, because the defect is invisible in behaviour - the router
returns exactly the same routes either way, and only the log says otherwise.
There is no Java test harness in this repository (`tests/unit` is Python and
`src/java` compiles against `.tools/`), so the invariant is asserted on the
source, the way `check_hardcoding.py` asserts its own.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ROUTER = os.path.join(REPO, 'src', 'java', 'citysim', 'NetworkDirectWalkPtRouter.java')
CONTROLER = os.path.join(REPO, 'src', 'java', 'citysim', 'CitysimControler.java')


def _src(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _code_lines(text):
    """The source with comment-only lines dropped, so prose cannot satisfy a rule."""
    out = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
            continue
        out.append(line)
    return out


def test_counters_are_run_lifetime_atomics():
    """No mutable primitive counter may survive on the instance."""
    code = '\n'.join(_code_lines(_src(ROUTER)))
    stray = re.findall(r'^\s*private\s+(?!static)(?:final\s+)?(int|long)\s+(\w+)\s*=',
                       code, re.M)
    assert not stray, (
        'instance counter field(s) %s are reset every time the unscoped provider '
        'builds a router - use a static AtomicLong' % [n for _, n in stray])
    for name in ('DECIDED', 'WALKED', 'NO_TRANSIT'):
        assert re.search(r'private\s+static\s+final\s+AtomicLong\s+%s\b' % name, code), (
            '%s is not a run-lifetime AtomicLong' % name)


def test_progress_line_is_not_hung_off_the_walk_branch():
    """The 100,000th decision must log even when that decision chooses the walk."""
    code = '\n'.join(_code_lines(_src(ROUTER)))
    progress = code.index('% 100000')
    branch = code.index('if (walkCost < transitCost)')
    assert progress < branch, (
        'the progress line sits after the walk branch returns, so the run skips '
        'it whenever its 100,000th decision is a walk')


def test_the_sample_reads_the_value_its_own_increment_returned():
    """A count that is incremented and then re-read can report a number that never was."""
    code = '\n'.join(_code_lines(_src(ROUTER)))
    assert 'WALKED.incrementAndGet() <= 3' in code, (
        'the 3-line sample must test the value incrementAndGet() returned, not a '
        'separate WALKED.get()')
    assert 'DECIDED.incrementAndGet()' in code


def test_the_binding_that_makes_static_necessary_still_looks_like_this():
    """If the provider is ever scoped, this file's reasoning needs revisiting."""
    controler = '\n'.join(_code_lines(_src(CONTROLER)))
    assert 'NetworkDirectWalkPtRouter.RouterProvider.class' in controler, (
        'the router is no longer bound through RouterProvider - re-read '
        'test_direct_walk_counters.py, whose whole premise is that binding')
