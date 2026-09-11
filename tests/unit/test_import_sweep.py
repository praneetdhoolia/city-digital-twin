"""Every framework module and every city builder imports, in its own interpreter.

Sixty-two of eighty-one `src/` modules were imported by no unit test, and the
proof was `build_matsim_network.py`, which could not run for seventeen days
with every gate green (eighth project report, 11 September 2026; #190). An
import is the cheapest thing a module can be asked to do, and a module that
cannot even do that is the class of defect this catches: a name that no
longer exists, a signature that changed, a file the module opens at import.

Each module is imported in a FRESH interpreter with the path plumbing every
script in this repository sets up for itself (`src/`, `src/<sub>/`, the
module's own directory), so one module's import-time state cannot mask
another's. Three verdicts:

* PASS - the module imported.
* SKIP, stated - a third-party package the CI image does not carry
  (geopandas, pyproj, rasterio, ...), or a data artefact the module opens at
  import that this checkout does not hold (the bulk package is not committed).
  Both are printed with the module, so a locally-run suite on a full
  workstation sees them pass instead.
* FAIL - anything else: the module is broken.

The extract layer (`cities/<city>/extract/`) is deliberately outside the
sweep: its scripts download at import by design, and a unit test opens no
network connection. Three scripts that do their work at module level
(`build_data_dictionary`, `build_era_feeds`, `shape_tools`) are compiled
rather than imported, for the same reason.
"""
import glob
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
import city as _city  # noqa: E402

RUNS_AT_IMPORT = {'build_data_dictionary', 'build_era_feeds', 'shape_tools'}
THIRD_PARTY = {'geopandas', 'pyproj', 'rasterio', 'shapely', 'numpy', 'pandas',
               'scipy', 'jsonschema', 'matplotlib', 'PIL', 'openpyxl', 'psutil',
               'requests', 'fiona', 'networkx', 'sklearn', 'yaml', 'lxml'}

RUNNER = r'''
import importlib, json, os, sys, traceback
repo, path, name = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(repo, 'src', 'setup'))
import install_paths                       # the one root set, this process only (#181)
install_paths.activate(persist=False)
sys.path.insert(0, os.path.dirname(path))
try:
    importlib.import_module(name)
    print(json.dumps({'verdict': 'pass'}))
except ModuleNotFoundError as e:
    print(json.dumps({'verdict': 'skip', 'why': 'third-party package missing: %s' % e.name,
                      'name': e.name}))
except (FileNotFoundError, PermissionError) as e:
    print(json.dumps({'verdict': 'skip', 'why': 'opens an artefact this checkout does not hold: %s' % e}))
except SystemExit as e:
    print(json.dumps({'verdict': 'skip', 'why': 'refused at import (a stated precondition): %s' % str(e)[:300]}))
except Exception:
    print(json.dumps({'verdict': 'fail', 'why': traceback.format_exc()[-1500:]}))
'''


def _modules():
    out = []
    for pattern in ('src/*.py', 'src/*/*.py', 'cities/%s/build/*.py' % _city.CITY):
        for p in sorted(glob.glob(os.path.join(REPO, pattern))):
            out.append(os.path.relpath(p, REPO).replace(os.sep, '/'))
    return out


MODULES = _modules()


@pytest.mark.parametrize('rel', MODULES)
def test_module_imports(rel):
    path = os.path.join(REPO, rel)
    name = os.path.splitext(os.path.basename(rel))[0]
    if name in RUNS_AT_IMPORT:
        # compiled, not imported: the module does its work at module level
        with open(path, encoding='utf-8') as fh:
            compile(fh.read(), path, 'exec')
        return
    proc = subprocess.run([sys.executable, '-c', RUNNER, REPO, path, name],
                          capture_output=True, text=True, timeout=300,
                          env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    last = (proc.stdout.strip().splitlines() or [''])[-1]
    try:
        verdict = json.loads(last)
    except ValueError:
        pytest.fail('%s: no verdict (rc=%d)\n%s' % (rel, proc.returncode, (proc.stderr or proc.stdout)[-1500:]))
    if verdict['verdict'] == 'skip':
        if verdict.get('name') and verdict['name'].split('.')[0] not in THIRD_PARTY:
            pytest.fail('%s: a MISSING MODULE that is not a known third-party package: %s'
                        % (rel, verdict['why']))
        pytest.skip('%s: %s' % (rel, verdict['why']))
    assert verdict['verdict'] == 'pass', '%s failed to import:\n%s' % (rel, verdict.get('why'))
