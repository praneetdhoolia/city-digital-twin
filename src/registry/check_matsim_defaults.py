"""What the FRAMEWORK is deciding, in the modules this model writes into.

Every other check in this repository asks the same question from one side:
does a DECLARED value reach the model? `check_hardcoding.py` proves each bound
field moves the config; `check_legacy_drift.py` pins the build layer to the
registry; the closure check refuses a parameter no field claims.

None of them can ask the question from the other side - **what is deciding the
model's behaviour that nobody declared?** That gap had a cost. The registry
declared `RUN.travel_time.analysed_modes = ["car"]`, swept it, rendered it into
the reference and PROVED it reached the config. It meant nothing: MATSim reads
`analyzedModes` only when `travelTimeCalculator.filterModes` is true, that
parameter was never emitted, and its framework default is false - so every
pedestrian, cyclist and bus on the network fed the link travel times the car
router read (#154). A declared value was voided by an undeclared one, and every
gate was green.

This check reads the pinned framework's own parameter surface
(`config/schema/matsim_defaults.json`, written by
`src/setup/dump_matsim_params.py`) and reports, for every module the model
writes into, the parameters it does NOT set. Each one is a value the framework
is choosing.

It does not demand that every default be declared - most are irrelevant to this
model, and declaring them would be noise pretending to be rigour. It demands
that each one be **looked at once and written down**: an entry in
`config/schema/matsim_defaults_accepted.json` saying why the framework's choice
is accepted. A parameter that appears in a written module and is not in that
ledger FAILS, which is exactly the moment a new MATSim version, or a module the
model starts writing into, brings an undeclared decision with it.

    python src/registry/check_matsim_defaults.py
    python src/registry/check_matsim_defaults.py --strict   # CI
    python src/registry/check_matsim_defaults.py --seed     # write the ledger
"""

from __future__ import annotations

import argparse
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULTS = os.path.join(REPO, 'config', 'schema', 'matsim_defaults.json')
ACCEPTED = os.path.join(REPO, 'config', 'schema',
                        'matsim_defaults_accepted.json')

# A parameter whose name matches one of these is a PATH or an IDENTITY the
# launcher supplies per run, never a model value. They are recognised by shape
# rather than listed one by one so a new input file does not read as a new
# undeclared decision.
RUNTIME_SHAPES = (
    re.compile(r'File$'), re.compile(r'Directory$'), re.compile(r'^outputDirectory$'),
    re.compile(r'^coordinateSystem$'), re.compile(r'^randomSeed$'),
    re.compile(r'^inputCRS$'), re.compile(r'^outputCRS$'),
)

SET_TARGET = re.compile(r'^([A-Za-z0-9_]+)\.[A-Za-z0-9_]+\[.*\]\.')


def _load(path, what):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except OSError:
        raise SystemExit(
            'missing %s (%s).\nWrite it with: python '
            'src/setup/dump_matsim_params.py' % (os.path.relpath(path, REPO),
                                                 what))
    except ValueError as e:
        raise SystemExit('%s is not valid JSON: %s'
                         % (os.path.relpath(path, REPO), e))


def emitted_targets():
    """(modules written, module-level params set) from the registry itself."""
    from registry import param_config
    from registry import __init__ as _registry            # noqa: F401
    import registry as _reg
    fields = _reg.load_registry()[0]
    modules, params = set(), set()
    for key in param_config.bound_fields('matsim', fields):
        raw = str(fields[key].get('matsim_param') or '')
        for target in raw.split(','):
            target = target.strip()
            if not target:
                continue
            m = SET_TARGET.match(target)
            if m:
                # a parameterset member: the module counts as written, but the
                # set's own parameters are a different surface from the
                # module's and are not compared here
                modules.add(m.group(1))
                continue
            if '.' not in target:
                continue
            module, param = target.split('.', 1)
            if '.' in param or '[' in param:
                modules.add(module)
                continue
            modules.add(module)
            # Case-insensitive: MATSim accepts `BrainExpBeta` and renders the
            # same parameter as `brainExpBeta`, and a field that reaches the
            # model under one spelling is not an undeclared default under the
            # other. The closure check is what proves it reaches.
            params.add((module, param.lower()))
    return modules, params


def is_runtime(param: str) -> bool:
    return any(p.search(param) for p in RUNTIME_SHAPES)


def audit():
    defaults = _load(DEFAULTS, 'the pinned framework parameter surface')
    accepted = _load(ACCEPTED, 'the accepted-defaults ledger') \
        if os.path.exists(ACCEPTED) else {'accepted': {}}
    ledger = accepted.get('accepted', {})
    groups = defaults.get('groups', {})
    modules, params = emitted_targets()

    unreviewed, reviewed, runtime, stale = [], [], [], []
    for module in sorted(modules):
        for param in sorted(groups.get(module, {})):
            if (module, param.lower()) in params:
                continue
            key = '%s.%s' % (module, param)
            if is_runtime(param):
                runtime.append((key, groups[module][param]))
            elif key in ledger:
                reviewed.append((key, groups[module][param], ledger[key]))
            else:
                unreviewed.append((key, groups[module][param]))

    live = {'%s.%s' % (m, p)
            for m in modules for p in groups.get(m, {})}
    for key in sorted(ledger):
        if key not in live:
            stale.append(key)

    return dict(matsim_version=defaults.get('matsim_version'),
                modules=sorted(modules), set_params=sorted(params),
                unreviewed=unreviewed, reviewed=reviewed,
                runtime=runtime, stale=stale)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--strict', action='store_true',
                    help='exit non-zero on an unreviewed default or a stale '
                         'ledger entry')
    ap.add_argument('--seed', action='store_true',
                    help='write every currently unreviewed default into the '
                         'ledger with a placeholder reason, for a human to '
                         'replace. Refuses to overwrite a written reason.')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)

    a = audit()

    if args.seed:
        doc = _load(ACCEPTED, 'the ledger') if os.path.exists(ACCEPTED) else {}
        doc.setdefault('$comment', (
            'PORTABLE. Every parameter the pinned framework decides for itself '
            'in a module this model writes into, with the reason its default '
            'is accepted. It carries no model value: a value the model chooses '
            'is declared in a city registry, not accepted here. An entry is a '
            'claim - "the framework\'s choice here is right, or irrelevant, '
            'for this model" - and it is reviewable because it had to be '
            'written down. Read by src/registry/check_matsim_defaults.py.'))
        doc.setdefault('matsim_version', a['matsim_version'])
        led = doc.setdefault('accepted', {})
        added = 0
        for key, value in a['unreviewed']:
            if key not in led:
                led[key] = 'UNREVIEWED - default %r' % value
                added += 1
        with open(ACCEPTED, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write('\n')
        print('seeded %d new entr(ies) into %s'
              % (added, os.path.relpath(ACCEPTED, REPO)))
        return 0

    if args.json:
        print(json.dumps(a, indent=2, sort_keys=True))
        return 1 if (a['unreviewed'] or a['stale']) else 0

    print('MATSIM DEFAULTS IN THE MODULES THIS MODEL WRITES - MATSim %s'
          % a['matsim_version'])
    print('%d module(s) written, %d module-level parameter(s) set by a '
          'declared field' % (len(a['modules']), len(a['set_params'])))
    print()
    print('1. UNREVIEWED - the framework decides it and nobody has said why '
          'that is acceptable')
    for key, value in a['unreviewed']:
        print('     %-52s default %s' % (key, value if value != '' else "''"))
    print('     %d' % len(a['unreviewed']))
    print()
    print('2. ACCEPTED - looked at once, with the reason written down')
    print('     %d' % len(a['reviewed']))
    print()
    print('3. RUNTIME - a path or the city\'s identity, supplied per run')
    print('     %d' % len(a['runtime']))
    print()
    print('4. STALE LEDGER ENTRIES - the parameter is gone from the framework')
    for key in a['stale']:
        print('     %s' % key)
    print('     %d' % len(a['stale']))
    print()
    total = len(a['unreviewed']) + len(a['stale'])
    print('TOTAL %d item(s). A parameter nobody declared is still deciding '
          'something.' % total)
    if total and args.strict:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
