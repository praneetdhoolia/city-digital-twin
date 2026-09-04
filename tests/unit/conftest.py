"""Put `src/` on the path the way the whole-package check scripts do.

The unit layer imports the modules under test directly - `import fit`, not
`from src.calibrate import fit` - because that is how every script in this
repository imports its neighbours (`src/` is not a package and the run scripts
insert these same directories themselves). Doing it once here keeps each test
module free of path plumbing.

Nothing in this directory reads the data package, opens a network connection or
touches `results/`: a unit test builds its own inputs. The two exceptions are
declared where they occur - `src/calibrate/fit.py` and `src/run/run_matsim.py`
resolve the ACTIVE CITY at import time, so the tests that import them need a
city to exist, and they still pass no city value in and assert none.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))

for _sub in ('run', 'analyse', 'registry', 'calibrate', ''):
    _path = os.path.join(REPO, 'src', _sub) if _sub else os.path.join(REPO, 'src')
    if _path not in sys.path:
        sys.path.insert(0, _path)
