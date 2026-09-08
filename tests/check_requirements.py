#!/usr/bin/env python
"""Every third-party import this repository makes is pinned in requirements.txt.

    python tests/check_requirements.py            report
    python tests/check_requirements.py --strict   exit 1 if anything is unpinned

The JDK, pt2matsim, Maven and the MATSim run stack are pinned by sha256 in
`.tools/toolchain.json`, and the conventions say a toolchain change is a model
change. The Python that builds every input the simulator reads was pinned
nowhere at all until `requirements.txt` was written, so a geopandas release
that changed a spatial predicate could move the zone joins and nothing would
record that anything had moved.

This is the ledger for that pin, and it is deliberately mechanical rather than
a list somebody maintains: it PARSES the imports out of the source, so a new
dependency that nobody wrote down fails the build on the diff that added it.
Three questions:

  1. every third-party top-level module imported under the scanned roots has a
     line in requirements.txt;
  2. every line in requirements.txt is EXACTLY pinned (`==`), because a range
     is not a pin and a package built from a range is not reproducible;
  3. no line is a duplicate, which would leave the effective version to pip's
     resolution order.

It does not check that the pinned versions are INSTALLED - that is the CI job
that installs the file and runs the tests against it, and a workstation may
legitimately be mid-upgrade.

Standard library only. Names no city: the roots are the repository's own, and
the module -> distribution map holds only the names that genuinely differ.
"""
import argparse
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REQUIREMENTS = os.path.join(REPO, 'requirements.txt')
ROOTS = ('src', 'tests', 'cities', 'run.py')
SKIP_DIRS = {'.git', '__pycache__', '.tools', 'results', 'node_modules',
             '.venv', 'archived'}

# Import name -> distribution name, for the few where they differ. Everything
# else is assumed to be the same word, which is the common case; a wrong guess
# shows up as an unpinned import rather than passing silently.
DISTRIBUTION = {
    'dateutil': 'python-dateutil',
    'yaml': 'PyYAML',
    'PIL': 'Pillow',
    'sklearn': 'scikit-learn',
    'osgeo': 'GDAL',
}


def normalise(name):
    """PEP 503 name normalisation, so `rpds-py` and `rpds_py` are one name."""
    out = []
    for ch in name.lower():
        out.append(ch if ch.isalnum() else '-')
    while '--' in ''.join(out):
        out = list(''.join(out).replace('--', '-'))
    return ''.join(out).strip('-')


def local_modules():
    """Module names this repository itself provides, which are never pinned."""
    names = set()
    for base, _dirs, files in os.walk(REPO):
        parts = set(base.replace(os.sep, '/').split('/'))
        if parts & SKIP_DIRS:
            continue
        rel = os.path.relpath(base, REPO).replace(os.sep, '/')
        if rel != '.' and not rel.split('/')[0] in ('src', 'tests', 'cities',
                                                    'config'):
            continue
        names |= {f[:-3] for f in files if f.endswith('.py')}
        names |= {d for d in _dirs if d not in SKIP_DIRS}
    return names


def source_files():
    for root in ROOTS:
        p = os.path.join(REPO, root)
        if os.path.isfile(p):
            yield p
            continue
        for base, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f.endswith('.py'):
                    yield os.path.join(base, f)


def imported_modules():
    """Top-level module -> the files that import it."""
    stdlib = set(getattr(sys, 'stdlib_module_names', ()))
    local = local_modules()
    found = {}
    for path in source_files():
        try:
            tree = ast.parse(io.open(path, encoding='utf-8',
                                     errors='replace').read())
        except SyntaxError:
            continue
        rel = os.path.relpath(path, REPO).replace(os.sep, '/')
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split('.')[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 \
                    and node.module:
                mods = [node.module.split('.')[0]]
            for m in mods:
                if m in stdlib or m in local or m.startswith('_'):
                    continue
                found.setdefault(m, set()).add(rel)
    return found


def pinned():
    """Normalised distribution -> (version, raw line number)."""
    out, problems = {}, []
    if not os.path.exists(REQUIREMENTS):
        return out, ['requirements.txt is missing - the Python half of the '
                     'toolchain is pinned nowhere']
    with io.open(REQUIREMENTS, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            line = line.split('#')[0].strip()
            if not line:
                continue
            if '==' not in line:
                problems.append('requirements.txt:%d: "%s" is not an exact pin '
                                '(a range is not a pin)' % (n, line))
                continue
            name, _, version = line.partition('==')
            key = normalise(name.strip())
            if key in out:
                problems.append('requirements.txt:%d: %s is pinned twice'
                                % (n, name.strip()))
                continue
            out[key] = (version.strip(), n)
    return out, problems


def main(argv=None):
    args = argparse.ArgumentParser(description=__doc__).parse_known_args(argv)[0]
    strict = '--strict' in (argv if argv is not None else sys.argv[1:])
    del args
    pins, problems = pinned()
    imports = imported_modules()
    unpinned = []
    for module in sorted(imports):
        dist = normalise(DISTRIBUTION.get(module, module))
        if dist not in pins:
            unpinned.append((module, sorted(imports[module])))
    print('requirements: %d pinned, %d third-party module(s) imported'
          % (len(pins), len(imports)))
    for module, files in unpinned:
        problems.append('%s is imported (%s%s) and pinned nowhere'
                        % (module, files[0],
                           ', +%d more' % (len(files) - 1) if len(files) > 1
                           else ''))
    for p in problems:
        print('FAIL  ' + p)
    if not problems:
        print('OK    every third-party import is exactly pinned')
        return 0
    print('\n%d problem(s). A dependency change is a MODEL change: pin it in '
          'requirements.txt, re-run the builders it touches and log it in the '
          'record beside the toolchain entries.' % len(problems))
    return 1 if strict else 0


if __name__ == '__main__':
    sys.exit(main())
