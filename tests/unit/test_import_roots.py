"""Every module imports its neighbours through the installed import roots.

`src/` and its subdirectories are import roots, installed once per interpreter
by `src/setup/install_paths.py` (#181), so a script imports `results_store`,
never `src.run.results_store`. The repository root is deliberately NOT a root:
a `from src.run import ...` works only when the caller happens to run from the
repository root - `python -m pytest` does, a detached launcher and a script
run by path do not. The #181 sweep left two scripts and three tests on the old
spelling; `verify_launch.py` was found failing with `No module named 'src'`
the first time it was run after a detached launch (12 September 2026). This
test is the guard the sweep did not have.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
PATTERN = re.compile(r'^\s*(from|import)\s+src[.\s]', re.M)
ROOTS = ('src', 'tests', 'run.py', '.claude')


def _py_files():
    for root in ROOTS:
        path = os.path.join(REPO, root)
        if os.path.isfile(path):
            yield path
            continue
        for d, _dirs, files in os.walk(path):
            for f in files:
                if f.endswith('.py'):
                    yield os.path.join(d, f)


def test_no_module_imports_through_the_repository_root():
    offenders = []
    for path in _py_files():
        with open(path, encoding='utf-8', errors='replace') as fh:
            for n, line in enumerate(fh, 1):
                if PATTERN.match(line):
                    offenders.append('%s:%d: %s' % (os.path.relpath(path, REPO), n, line.strip()))
    assert not offenders, 'imports through the repository root (use the import roots, #181):\n' + '\n'.join(offenders)
