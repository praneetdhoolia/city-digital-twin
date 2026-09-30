"""Every check CI runs is also a line of the local session gate (9.219).

CI ran `tests/check_requirements.py` and `session_gate.py` did not, so a new
`import psutil` passed a green gate and would have failed only on the pull
request. A script CI runs that is not a check is exempt here by name, with
the reason.
"""
import os
import re

import session_gate

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WORKFLOWS = os.path.join(ROOT, '.github', 'workflows')

EXEMPT = {
    # builds and deploys the Pages site; it checks nothing
    '.github/scripts/build_pages.py',
    # compares nothing since the build-layer migration closed (it says so);
    # check_hardcoding holds the line and is in the gate
    'src/registry/check_legacy_drift.py',
}


def _ci_scripts():
    out = set()
    for name in os.listdir(WORKFLOWS):
        if name.endswith(('.yml', '.yaml')):
            with open(os.path.join(WORKFLOWS, name), encoding='utf-8') as fh:
                out.update(re.findall(r'python\s+([\w./-]+\.py)', fh.read()))
    return out


def test_every_ci_check_is_in_the_gate():
    gated = {arg for _, cmd, _ in session_gate.GATES for arg in cmd
             if isinstance(arg, str) and arg.endswith('.py')}
    missing = sorted(_ci_scripts() - gated - EXEMPT)
    assert not missing, 'CI runs these and the session gate does not: %s' % missing


def test_the_exemptions_are_still_in_ci():
    assert EXEMPT <= _ci_scripts(), 'an exemption names a script CI no longer runs'
