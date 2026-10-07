"""Every manifest row can say where its data came from, and from a host the
sandbox admits.

Two claims over the committed manifests of every city under cities/, read
offline (no bulk data, no network):

  * every provenance URL - the manifest's `source_url` column and the sources
    each city.json declares - names a host inside `.claude/settings.json`'s
    sandbox allowlist. A source the sandbox cannot reach is a source nobody
    can re-acquire from this repository, and the allowlist is the one record
    of where the package may fetch from (CLAUDE.md: a new source means adding
    its domain there and a provenance record);
  * every processed row carries a `source`, or is recorded as debt under
    `processed_without_source` in the city's `tests/manifest_debt.json` -
    53 rows across the two cities said nothing (sixteenth report), and the
    ledger's ceiling lets that number only fall.
"""
import json
import os
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
CITIES = os.path.join(REPO, 'cities')

from manifest_io import manifest_reader  # noqa: E402


def _cities():
    for name in sorted(os.listdir(CITIES)):
        manifest = os.path.join(CITIES, name, 'data', 'MANIFEST.csv')
        if os.path.exists(manifest):
            yield name, manifest


def _rows(manifest):
    with open(manifest, encoding='utf-8') as f:
        return list(manifest_reader(f))


def _allowed_hosts():
    with open(os.path.join(REPO, '.claude', 'settings.json'), encoding='utf-8') as f:
        return set(json.load(f)['sandbox']['network']['allowedDomains'])


def _inside(host, allowed):
    return any(host == d or host.endswith('.' + d) for d in allowed)


def test_every_provenance_url_host_is_inside_the_sandbox_allowlist():
    allowed = _allowed_hosts()
    outside = {}
    for name, manifest in _cities():
        urls = {u.strip() for r in _rows(manifest)
                for u in (r.get('source_url') or '').split(' + ') if u.strip()}
        with open(os.path.join(CITIES, name, 'city.json'), encoding='utf-8') as f:
            urls |= {s['url'] for s in json.load(f).get('sources') or [] if s.get('url')}
        for url in sorted(urls):
            host = urlsplit(url).hostname
            if host and not _inside(host, allowed):
                outside.setdefault(name, set()).add(host)
    assert not outside, ('provenance hosts outside .claude/settings.json sandbox.network.'
                         'allowedDomains: %s' % outside)


def test_every_processed_row_has_a_source_or_is_recorded_debt():
    for name, manifest in _cities():
        blank = sorted(r['path'] for r in _rows(manifest)
                       if r.get('stage') == 'processed' and not (r.get('source') or '').strip())
        ledger = os.path.join(CITIES, name, 'tests', 'manifest_debt.json')
        recorded = set()
        if os.path.exists(ledger):
            with open(ledger, encoding='utf-8') as f:
                entry = (json.load(f).get('rules') or {}).get('processed_without_source') or {}
            recorded = set(entry.get('paths') or ())
            assert entry.get('ceiling', 0) == len(recorded), name
        unrecorded = sorted(set(blank) - recorded)
        assert not unrecorded, '%s: processed rows with no source and no debt entry: %s' % (
            name, unrecorded[:8])
        healed = sorted(recorded - set(blank))
        assert not healed, '%s: recorded debt that no longer fails - lower the ceiling: %s' % (
            name, healed[:8])
