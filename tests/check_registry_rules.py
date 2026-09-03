"""The registry resolver's integrity rules fire on the breaks they exist for (#124).

Four holes passed every gate at commit 9c99e54: a `derived_from` naming a
field that does not exist, a field deriving from itself, a value outside its
own sweep, and a categorical overlay value that is not a member of its sweep;
a fifth - a named run overlay that is absent - was silently skipped and ran
the base under the tag's name. The rules now live in the resolver
(`src/registry/__init__.py`), so a broken registry fails at its first strict
load. This check feeds each rule the break it guards and asserts it fires,
and feeds it a clean case and asserts it does not. Stdlib only, sub-second,
no package. Exit 1 on any failure.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))
import registry  # noqa: E402

FAILS = []


def check(cond, msg):
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        FAILS.append(msg)


def field(**kw):
    base = dict(value=1.0, units='u', source='assumed', status='active',
                description='fixture', sweep=[0.0, 2.0], decisions_ref='0')
    base.update(kw)
    return base


clean = {'X.a': field(), 'X.b': field(source='derived', sweep=None,
                                      derived_from=dict(fields=['X.a'], identity='b = a'))}
check(not registry._intrinsic_errors(clean), 'a clean pair of fields raises nothing')

dangling = {'X.b': field(source='derived', sweep=None,
                         derived_from=dict(fields=['X.missing'], identity='b = ?'))}
errs = registry._intrinsic_errors(dangling)
check(any('X.missing' in e and 'not a registry field' in e for e in errs),
      'a derived_from naming a field that does not exist is an error')

selfref = {'X.b': field(source='derived', sweep=None,
                        derived_from=dict(fields=['X.b'], identity='b = b'))}
errs = registry._intrinsic_errors(selfref)
check(any('names the field itself' in e for e in errs),
      'a field deriving from itself is an error')

outside = {'X.a': field(value=5.0)}
errs = registry._intrinsic_errors(outside)
check(any('outside its own sweep' in e for e in errs),
      'a numeric value outside its own sweep is an error')

leaf = {'X.a': field(value={'k1': 1.0, 'k2': 6.0})}
errs = registry._intrinsic_errors(leaf)
check(any('X.a[k2]' in e and 'outside its own sweep' in e for e in errs),
      'a dict-valued field is checked leaf by leaf')
check(not any('X.a[k1]' in e for e in errs), '... and an inside leaf is not flagged')

inside = {'X.a': field(value=2.0)}
check(not registry._intrinsic_errors(inside), 'a value on the sweep bound is inside')

cat = {'X.c': field(value='on', sweep={'categorical': ['on', 'off'], 'basis': 'fixture'})}
_, errs = registry._check_values({'X.c': 'onn'}, cat, 'fixture overlay')
check(any('categorical' in e for e in errs),
      'a categorical overlay value outside the declared members is an error')
_, errs = registry._check_values({'X.c': 'off'}, cat, 'fixture overlay')
check(not errs, 'a categorical overlay value that is a member passes')

try:
    registry.load(run='__no_such_overlay_fixture__')
    check(False, 'a named run overlay that is absent raises')
except registry.RegistryError as e:
    check('no run overlay' in str(e), 'a named run overlay that is absent raises: %s' % e)

try:
    registry.load()
    check(True, 'the committed registry loads strictly under the new rules')
except registry.RegistryError as e:
    check(False, 'the committed registry loads strictly under the new rules: %s' % str(e)[:300])

if FAILS:
    print('\n%d check(s) failed' % len(FAILS))
    sys.exit(1)
print('\nALL CHECKS PASSED')
