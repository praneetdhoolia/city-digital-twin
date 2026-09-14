"""Every host a provenance record names is one the sandbox lets the agent reach.

The ninth report found 434 provenance records naming a host the sandbox
allowlist did not (the daily Opal series), so an adapter re-run from a session
would have failed on a source the package already depends on. A new source is
added to `.claude/settings.json` in the same change as its first provenance
record; this test is what makes that a rule rather than a courtesy.
"""

from __future__ import annotations

import json
import pathlib
import re

import city  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
HOST = re.compile(r'https?://([A-Za-z0-9.-]+)')


def _allowed():
    settings = json.loads((REPO / '.claude' / 'settings.json').read_text(encoding='utf-8'))
    return set(settings['sandbox']['network']['allowedDomains'])


def _provenance_hosts():
    hosts = set()
    roots = [pathlib.Path(city.path('data', 'raw')), pathlib.Path(city.path('schedules', 'raw'))]
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob('provenance*.json'):
            hosts.update(HOST.findall(p.read_text(encoding='utf-8', errors='replace')))
    return hosts


def test_every_provenance_host_is_in_the_sandbox_allowlist():
    allowed = _allowed()
    missing = sorted(h for h in _provenance_hosts()
                     if h not in allowed and not any(h.endswith('.' + a) for a in allowed))
    assert not missing, ('provenance names a host the sandbox cannot reach; add it to '
                         '.claude/settings.json sandbox.network.allowedDomains: %s' % missing)
