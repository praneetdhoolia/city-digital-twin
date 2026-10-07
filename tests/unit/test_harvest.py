"""The harvest archive and the data-use ledger on fixtures (sixteenth report).

`harvest.pack` brings an archive to hold every member of a family of public
responses; here two members are adopted from loose files beside a temporary
city directory, so nothing is fetched. `audit_source_use.disposition_of`
is the one rule that gives every catalogue entry its disposition.
"""
import hashlib
import json
import os
import sys
import types
import zipfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MUMBAI_EXTRACT = os.path.join(REPO, 'cities', 'mumbai', 'extract')
if MUMBAI_EXTRACT not in sys.path:
    sys.path.insert(0, MUMBAI_EXTRACT)

pytest.importorskip('requests')
import harvest  # noqa: E402
import audit_source_use  # noqa: E402


def _loose(tmp_path, member_id, payload):
    """A member held as a loose file with its provenance record, before the harvest rule."""
    path = tmp_path / 'data' / 'raw' / 'transit' / (member_id + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    rec = dict(path='data/raw/transit/' + member_id + '.json', url='https://example.test/' + member_id,
               sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
               retrieved='2026-09-2%dT00:00:00+00:00' % (int(member_id[-1]) + 1), content_type='application/json')
    (path.parent / ('provenance_' + member_id + '.json')).write_text(json.dumps({'files': [rec]}), encoding='utf-8')
    return rec


@pytest.fixture
def city_dir(tmp_path, monkeypatch):
    fake = types.SimpleNamespace(
        path=lambda *parts: str(tmp_path.joinpath(*parts)),
        rel=lambda absolute: os.path.relpath(absolute, str(tmp_path)).replace(os.sep, '/'),
        REPO=str(tmp_path))
    monkeypatch.setattr(harvest, 'city', fake)
    monkeypatch.setattr(harvest, 'check_request', lambda entry, allowed: None)
    return tmp_path


def _entries():
    return [dict(id='route_1', category='transit', format='json', url='https://example.test/route_1'),
            dict(id='route_2', category='transit', format='json', url='https://example.test/route_2')]


def test_pack_adopts_two_loose_members_into_one_deterministic_archive(city_dir):
    a = _loose(city_dir, 'route_1', b'{"route": 1}')
    b = _loose(city_dir, 'route_2', b'{"route": 2}')
    h = harvest.Harvest('nmmt_routes', 'transit', 'NMMT routes', 'public', 'all routes', 'https://example.test/')
    n, unresolved = harvest.pack(h, _entries(), session=None, allowed=set(), log=lambda *a: None)
    assert (n, unresolved) == (2, [])
    assert h.archive.exists() and h.provenance.exists()
    # the loose pair is retired once the archive holds the same bytes
    assert not (city_dir / 'data/raw/transit/route_1.json').exists()
    assert not (city_dir / 'data/raw/transit/provenance_route_1.json').exists()
    rec = json.loads(h.provenance.read_text(encoding='utf-8'))['files'][0]
    assert rec['member_count'] == 2 and rec['harvest'] is True
    assert rec['retrieved_first'] == a['retrieved'] and rec['retrieved'] == b['retrieved']
    assert rec['sha256'] == hashlib.sha256(h.archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(h.archive) as z:
        assert z.namelist() == ['route_1.json', 'route_2.json', harvest.LISTING]
        assert all(i.date_time == harvest.FIXED_TIME for i in z.infolist())
    first = h.archive.read_bytes()
    # packing again fetches nothing, adopts nothing and writes the same bytes
    n, unresolved = harvest.pack(h, _entries(), session=None, allowed=set(), log=lambda *a: None)
    assert n == 2 and h.archive.read_bytes() == first


def test_members_and_read_verify_every_hash(city_dir):
    _loose(city_dir, 'route_1', b'{"route": 1}')
    _loose(city_dir, 'route_2', b'{"route": 2}')
    h = harvest.Harvest('nmmt_routes', 'transit', 'NMMT routes', 'public', 'all routes', 'https://example.test/')
    harvest.pack(h, _entries(), session=None, allowed=set(), log=lambda *a: None)
    listing = harvest.members('nmmt_routes', 'transit')
    assert sorted(listing) == ['route_1', 'route_2']
    assert listing['route_2']['name'] == 'route_2.json' and listing['route_2']['bytes'] == '12'
    assert harvest.read('nmmt_routes', 'transit', 'route_1') == b'{"route": 1}'
    assert harvest.read_json('nmmt_routes', 'transit', 'route_2') == {'route': 2}
    with pytest.raises(KeyError):
        harvest.read('nmmt_routes', 'transit', 'route_9', listing)
    # a member whose bytes no longer match its listed hash is refused
    harvest._OPEN.clear()
    with zipfile.ZipFile(h.archive, 'a') as z:
        z.writestr('route_1.json', b'{"route": 1, "tampered": true}')
    harvest._OPEN.clear()
    with pytest.raises(ValueError, match='hash mismatch'):
        harvest.read('nmmt_routes', 'transit', 'route_1')
    with pytest.raises(ValueError, match='archive hash mismatch'):
        harvest.record('nmmt_routes', 'transit')


def test_pack_refuses_a_member_whose_identity_changed_under_its_id(city_dir):
    _loose(city_dir, 'route_1', b'{"route": 1}')
    _loose(city_dir, 'route_2', b'{"route": 2}')
    h = harvest.Harvest('nmmt_routes', 'transit', 'NMMT routes', 'public', 'all routes', 'https://example.test/')
    harvest.pack(h, _entries(), session=None, allowed=set(), log=lambda *a: None)
    changed = _entries()
    changed[0]['url'] = 'https://example.test/other'
    with pytest.raises(ValueError, match='identity changed'):
        harvest.pack(h, changed, session=None, allowed=set(), log=lambda *a: None)
    with pytest.raises(ValueError, match='Duplicate'):
        harvest.pack(h, _entries() + _entries()[:1], session=None, allowed=set(), log=lambda *a: None)


NO_READERS = {'scripts': [], 'transcriptions': [], 'registry': []}


@pytest.mark.parametrize('entry, status, readers, cited, expected', [
    (dict(id='x'), 'unobtained', NO_READERS, False, 'unobtained'),
    (dict(id='x'), 'acquired_unusable', NO_READERS, True, 'unusable'),
    (dict(id='x', use=dict(disposition='not_needed', reason='a road-safety report')), 'acquired', NO_READERS, True, 'not_needed'),
    (dict(id='x', use=dict(disposition='reference', reason='read by a person')), 'acquired', NO_READERS, False, 'reference'),
    (dict(id='x', use=dict(disposition='not_needed')), 'acquired', NO_READERS, False, 'unread'),   # no reason: not declared
    (dict(id='x'), 'acquired', dict(scripts=['cities/mumbai/build/build_plans.py'], transcriptions=[], registry=[]), False, 'consumed'),
    (dict(id='x'), 'acquired', dict(scripts=[], transcriptions=['extract/transcriptions/t.json'], registry=[]), False, 'consumed'),
    (dict(id='x'), 'acquired', dict(scripts=['cities/mumbai/extract/audit_gtfs.py'], transcriptions=[], registry=[]), False, 'audited'),
    (dict(id='x', kind='harvest'), 'acquired', NO_READERS, True, 'unread'),
    (dict(id='nmmt_index_page', format='html'), 'acquired', NO_READERS, True, 'discovery'),
    (dict(id='x', format='md'), 'acquired', NO_READERS, True, 'discovery'),
    (dict(id='x', format='pdf'), 'acquired', NO_READERS, True, 'cited'),
    (dict(id='x', format='pdf'), 'acquired', NO_READERS, False, 'unread'),
])
def test_disposition_of_gives_each_catalogue_entry_one_disposition(entry, status, readers, cited, expected):
    assert audit_source_use.disposition_of(entry, status, readers, cited) == expected


def test_literal_reads_names_a_file_by_path_basename_or_a_long_enough_glob():
    assert audit_source_use.literal_reads('data/raw/transit/nmmt_routes.json', 'data/raw/transit/nmmt_routes.json')
    assert audit_source_use.literal_reads('nmmt_routes.json', 'data/raw/transit/nmmt_routes.json')
    assert audit_source_use.literal_reads('data/raw/transit/nmmt_routes_*.json', 'data/raw/transit/nmmt_routes_2026.json')
    assert not audit_source_use.literal_reads('*.json', 'data/raw/transit/nmmt_routes.json')
    assert not audit_source_use.literal_reads('', 'data/raw/transit/nmmt_routes.json')
