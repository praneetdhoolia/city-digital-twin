"""A detached launch runs the city the launching shell resolved (9.206).

The Task Scheduler starts the wrapper with the machine's environment, not the
shell's, so `CITYSIM_CITY=mumbai python run.py --detach` priced and preflighted
Mumbai and then ran the default city inside the task, which died on its missing
BASE overlay. The wrapper now sets the city itself.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
for p in (ROOT, os.path.join(ROOT, 'src')):
    if p not in sys.path:
        sys.path.insert(0, p)

import city                                                     # noqa: E402
import run as front_door                                        # noqa: E402


def test_the_wrapper_sets_the_launching_shells_city(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(front_door, 'HERE', str(tmp_path))
    monkeypatch.setattr(os, 'name', 'nt')
    monkeypatch.setattr(city, 'CITY', 'mumbai')
    monkeypatch.setattr(sys, 'argv', ['run.py', '--scenario', 'BASE', '--detach'])
    import subprocess
    monkeypatch.setattr(subprocess, 'check_call', lambda args: calls.append(args))
    front_door._detach()
    launch = tmp_path / 'results' / '_launch'
    wrappers = list(launch.glob('*.cmd'))
    assert len(wrappers) == 1
    text = wrappers[0].read_bytes().decode('ascii')
    assert 'set CITYSIM_CITY=mumbai\r\n' in text
    assert 'set CITYSIM_LAUNCH_STAMP=' in text
    # the city line precedes the python line that reads it
    assert text.index('set CITYSIM_CITY=') < text.index('run.py')
    assert '--detach' not in text.split('run.py', 1)[1]
    assert len(calls) == 2  # /create then /run
