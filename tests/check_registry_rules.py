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
                description='fixture', sweep=[0.0, 2.0], decisions_ref='0',
                sweep_role='uncertainty', sweep_basis='fixture: a chosen interval')
    base.update(kw)
    if base.get('sweep') is None:
        # a role names what a sweep is for; a field with no sweep carries none
        base.pop('sweep_role', None)
        base.pop('sweep_basis', None)
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

# The sweep-role rules (#134): a sweep says what it is for, an assumed sweep
# says where it came from. The fixture's own `field()` carries both, so the
# clean case above already proves the rules stay quiet on a well-formed field.
noroles = {'X.a': field(sweep_role=None)}
noroles['X.a'].pop('sweep_role')
errs = registry._intrinsic_errors(noroles)
check(any('no sweep_role' in e for e in errs),
      'a swept field without a sweep_role is an error')

badrole = {'X.a': field(sweep_role='sensitivity')}
errs = registry._intrinsic_errors(badrole)
check(any('no sweep_role' in e and "'sensitivity'" in e for e in errs),
      'a sweep_role outside answer/uncertainty/measurement is an error')

stray = {'X.h': field(sweep=None, held_fixed=dict(rule='fixture', decisions_ref='0'))}
stray['X.h']['sweep_role'] = 'uncertainty'
errs = registry._intrinsic_errors(stray)
check(any('sweep_role but no sweep' in e for e in errs),
      'a sweep_role on a field with no sweep is an error')

nobasis = {'X.a': field()}
nobasis['X.a'].pop('sweep_basis')
errs = registry._intrinsic_errors(nobasis)
check(any('no sweep_basis' in e for e in errs),
      'an assumed field with a sweep but no sweep_basis is an error')

blank = {'X.a': field(sweep_basis='   ')}
errs = registry._intrinsic_errors(blank)
check(any('no sweep_basis' in e for e in errs),
      '... and a blank sweep_basis does not count')

inner = {'X.a': field(sweep={'interval': [0.0, 2.0], 'basis': 'fixture: inside the sweep'})}
inner['X.a'].pop('sweep_basis')
check(not registry._intrinsic_errors(inner),
      'a basis written inside the sweep object satisfies the rule')

lit = {'X.l': field(source='literature')}
lit['X.l'].pop('sweep_basis')
check(not registry._intrinsic_errors(lit),
      'a literature field without a sweep_basis is not an error (the rule is for assumed)')

for role in registry.SWEEP_ROLES:
    ok = {'X.a': field(sweep_role=role)}
    check(not registry._intrinsic_errors(ok), 'sweep_role %r is accepted' % role)

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
