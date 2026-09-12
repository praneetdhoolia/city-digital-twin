#!/usr/bin/env python
"""Make the repository's modules importable by name, once per interpreter (#181).

Every script in this repository imports its neighbours by bare name - `import
city`, `import registry`, `import extract_metrics as em` - because `src/` and
its six subdirectories are the import roots, not packages. Until 12 September
2026 each of 122 scripts put those roots on `sys.path` itself: 238 pasted
edits in eleven spellings, and a change to how a city is resolved had to be
right in every one of them (eighth project report, area 1; issue #181).

This module is the ONE place that knows the roots. `activate()` writes them
into a `.pth` file in the running interpreter's site-packages - the same
mechanism `pip install -e .` uses - so every script under `src/`, `cities/<city>/`
and `tests/` imports its neighbours with no path plumbing of its own. It also
puts the roots on the current process's `sys.path`, so the caller that
installed them can go on to import in the same run.

    python src/setup/install_paths.py           # install (idempotent)
    python src/setup/install_paths.py --check   # 0 if installed and current

`bootstrap_toolchain.py`, `run.py` and `session_gate.py` call `activate()`
themselves, so a fresh clone's first `run.py` or session gate installs the
roots before anything else is imported. CI runs the install step once per job.
The unit suite's `conftest.py` activates for its process only (`persist=False`):
a test never writes outside the repository.

The roots are appended after site-packages rather than inserted first, as
the pasted edits did. `--check` refuses if any root's module names collide
with the standard library or an installed package, so the order cannot
change what a name resolves to.
"""
import os
import site
import sys
import sysconfig

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# `src` first so the `registry` PACKAGE wins over nothing else; the rest are the
# flat roots whose modules every script imports by bare name.
ROOTS = ('src', 'src/analyse', 'src/build', 'src/calibrate', 'src/registry',
         'src/run', 'src/setup')
PTH_NAME = 'city_digital_twin.pth'


def root_paths():
    return [os.path.normpath(os.path.join(REPO, r)) for r in ROOTS]


def _site_dirs():
    """Candidate site-packages directories, the interpreter's own first."""
    dirs = []
    purelib = sysconfig.get_paths().get('purelib')
    if purelib:
        dirs.append(purelib)
    for d in site.getsitepackages() if hasattr(site, 'getsitepackages') else []:
        if d not in dirs:
            dirs.append(d)
    if site.ENABLE_USER_SITE:
        u = site.getusersitepackages()
        if u not in dirs:
            dirs.append(u)
    return dirs


def pth_path():
    """Where the .pth is (or would be) written: the first writable site dir."""
    for d in _site_dirs():
        p = os.path.join(d, PTH_NAME)
        if os.path.exists(p):
            return p
    for d in _site_dirs():
        try:
            os.makedirs(d, exist_ok=True)
            if os.access(d, os.W_OK):
                return os.path.join(d, PTH_NAME)
        except OSError:
            continue
    return None


def _expected_text():
    return ''.join(p + '\n' for p in root_paths())


def installed():
    """True when the .pth exists and names exactly this checkout's roots."""
    p = pth_path()
    if p is None or not os.path.exists(p):
        return False
    with open(p, encoding='utf-8') as f:
        return f.read() == _expected_text()


def activate(persist=True, quiet=False):
    """Put the roots on `sys.path` now and, unless `persist=False`, in the
    interpreter's site-packages for every later process."""
    for p in reversed(root_paths()):
        if p not in sys.path:
            # after the script's own directory, before site-packages - the
            # order the .pth gives a fresh process is 'after site-packages';
            # neither order changes a resolution (see collisions())
            sys.path.insert(1 if sys.path and sys.path[0] != '' else 0, p)
    if not persist or installed():
        return pth_path()
    p = pth_path()
    if p is None:
        raise SystemExit('install_paths: no writable site-packages directory for %s'
                         % sys.executable)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(_expected_text())
    if not quiet:
        print('install_paths: wrote %s (%d roots)' % (p, len(ROOTS)))
    return p


def collisions():
    """Module names under the roots that the standard library or an installed
    package also provides - none today, and the check keeps it so."""
    std = set(sys.stdlib_module_names)
    sitedirs = _site_dirs()
    hits = []
    for r in root_paths():
        for f in sorted(os.listdir(r)):
            if f.endswith('.py') and f != '__init__.py':
                name = f[:-3]
            elif os.path.exists(os.path.join(r, f, '__init__.py')):
                name = f
            else:
                continue
            if name in std:
                hits.append('%s (stdlib) at %s' % (name, os.path.join(r, f)))
            for d in sitedirs:
                for cand in (os.path.join(d, name + '.py'), os.path.join(d, name, '__init__.py')):
                    if os.path.exists(cand):
                        hits.append('%s (site-packages %s) at %s' % (name, cand, os.path.join(r, f)))
    return hits


def check():
    ok = True
    p = pth_path()
    if installed():
        print('PASS  import roots installed: %s' % p)
    else:
        ok = False
        print('FAIL  import roots not installed for %s - run '
              'python src/setup/install_paths.py' % sys.executable)
    hits = collisions()
    if hits:
        ok = False
        print('FAIL  module names collide with the interpreter:')
        for h in hits:
            print('      ' + h)
    else:
        print('PASS  no module name under the roots collides with the interpreter')
    return ok


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true',
                    help='report whether the roots are installed; change nothing')
    a = ap.parse_args(argv)
    if a.check:
        return 0 if check() else 1
    activate()
    return 0 if check() else 1


if __name__ == '__main__':
    sys.exit(main())
