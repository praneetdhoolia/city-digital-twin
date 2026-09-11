"""Put the repository's import roots on the path for this process.

The unit layer imports the modules under test directly - `import fit`, not
`from src.calibrate import fit` - because that is how every script in this
repository imports its neighbours: `src/` and its subdirectories are import
roots, installed once per interpreter by `src/setup/install_paths.py` (#181).
The suite activates them for its own process rather than relying on the
install, and never persists: a test writes nothing outside the repository.

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

sys.path.insert(0, os.path.join(REPO, 'src', 'setup'))
import install_paths  # noqa: E402
install_paths.activate(persist=False)
