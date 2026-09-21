"""Many public queries, one immutable archive, one provenance record.

A harvest is a family of requests generated from one acquired parent - every
NMMT route's timetable, every published trip's stop times, every traffic-police
notice in an index. Kept one file per response, the transit folder alone held
11,956 responses beside 11,956 provenance records, and the catalogue, the
descriptor and the inventory each repeated all 14,230 of them. A harvest keeps
the same bytes as members of ONE zip under `data/raw/<category>/<harvest>.zip`,
its member listing (`_members.csv`: id, name, sha256, bytes, url, request,
retrieval time) inside the archive, and ONE `provenance_<harvest>.json` that
pins the archive's sha256, the member count and the retrieval window. The
catalogue carries one entry per harvest (`kind: harvest`), so the descriptor
and the inventory do too.

Determinism: members are written in id order with a fixed timestamp, so the
archive's hash depends only on its bytes. Resume: a member already in the
archive is not fetched again; a member still held as a loose file from before
this rule (its `provenance_<member>.json` beside it) is adopted and the loose
pair retired once the archive is written. Identity: a member whose url or
request changed under the same id is refused, as `acquire_sources` refuses it.

Reading: `members()` for the listing, `read()` / `read_json()` for one member,
verified against its listed sha256 on every read.
"""
import contextlib
import csv
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tempfile
import time
import zipfile

import requests
import city
from acquire_sources import check_request, fetch

LISTING = '_members.csv'
LISTING_COLUMNS = ('member_id', 'name', 'format', 'sha256', 'bytes', 'url', 'final_url', 'method',
                   'request_json', 'request_form', 'retrieved', 'content_type', 'source',
                   'discovered_from', 'transport')
# One fixed archive timestamp: a member's retrieval time is in the listing, and
# a zip whose entry dates moved with the wall clock would never hash the same
# twice (the manifest rule that also removed the build's wall time, #211).
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


class Harvest:
    """The catalogue-facing identity of one harvest and where it lives."""

    def __init__(self, harvest_id, category, title, licence, coverage, url, method='GET',
                 discovered_from=None, harvester=None, compress=True):
        self.id, self.category = harvest_id, category
        self.title, self.licence, self.coverage = title, licence, coverage
        self.url, self.method, self.discovered_from = url, method, discovered_from
        self.harvester = harvester
        # PDFs and JPEGs do not deflate; storing them keeps a 3.5 GB notices
        # archive writable in the time it takes to copy it
        self.compress = compress

    @property
    def directory(self):
        return Path(city.path('data/raw', self.category))

    @property
    def archive(self):
        return self.directory / (self.id + '.zip')

    @property
    def provenance(self):
        return self.directory / ('provenance_' + self.id + '.json')

    def entry(self, member_count=None):
        """The one catalogue entry this harvest occupies in extract/sources.json."""
        item = dict(id=self.id, kind='harvest', category=self.category, format='zip',
                    url=self.url, method=self.method, title=self.title, licence=self.licence,
                    coverage=self.coverage, harvester=self.harvester)
        if self.discovered_from is not None:
            item['discovered_from'] = self.discovered_from
        if member_count is not None:
            item['member_count'] = member_count
        return item


def _sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _listing_rows(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open(LISTING) as stream:
            return list(csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8', newline='')))


def record(harvest_id, category):
    """The harvest's provenance record, its archive verified against the record."""
    provenance = Path(city.path('data/raw', category, 'provenance_' + harvest_id + '.json'))
    rec = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
    archive = Path(city.path(rec['path']))
    if _sha256(archive) != rec['sha256']:
        raise ValueError('Harvest archive hash mismatch: ' + harvest_id)
    return rec, archive


def members(harvest_id, category, verify=True):
    """member_id -> listing row. `verify=False` skips hashing the archive."""
    if verify:
        _, archive = record(harvest_id, category)
    else:
        archive = Path(city.path('data/raw', category, harvest_id + '.zip'))
    rows = {}
    for row in _listing_rows(archive):
        if row['member_id'] in rows:
            raise ValueError('Duplicate harvest member: ' + row['member_id'])
        rows[row['member_id']] = row
    return rows


_OPEN = {}


def _archive(harvest_id, category):
    """One open handle per archive: a reader walking 9,522 members must not
    parse the central directory 9,522 times (the first audit took four minutes)."""
    path = Path(city.path('data/raw', category, harvest_id + '.zip'))
    key = str(path)
    handle = _OPEN.get(key)
    if handle is None or handle.fp is None:
        handle = _OPEN[key] = zipfile.ZipFile(path)
    return handle


def read(harvest_id, category, member_id, listing=None):
    """One member's bytes, verified against its listed sha256."""
    listing = members(harvest_id, category, verify=False) if listing is None else listing
    row = listing.get(member_id)
    if row is None:
        raise KeyError('Harvest %s has no member %s' % (harvest_id, member_id))
    data = _archive(harvest_id, category).read(row['name'])
    if hashlib.sha256(data).hexdigest() != row['sha256']:
        raise ValueError('Harvest member hash mismatch: %s/%s' % (harvest_id, member_id))
    return data


def read_json(harvest_id, category, member_id, listing=None):
    return json.loads(read(harvest_id, category, member_id, listing).decode('utf-8-sig'))


def _identity(row):
    return (row.get('url'), row.get('method') or 'GET',
            row.get('request_json') or '', row.get('request_form') or '')


def _entry_identity(entry):
    return (entry['url'], entry.get('method', 'GET'),
            json.dumps(entry['request_json'], sort_keys=True) if entry.get('request_json') is not None else '',
            json.dumps(entry['request_form'], sort_keys=True) if entry.get('request_form') is not None else '')


def _adopt_loose(harvest, entry):
    """A member acquired as a loose file before the harvest rule: its verified
    bytes and record, and the two paths to retire once the archive is written."""
    provenance = harvest.directory / ('provenance_' + entry['id'] + '.json')
    if not provenance.exists():
        return None
    rec = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
    if (rec['url'], rec.get('method', 'GET'), rec.get('request_json'), rec.get('request_form')) != \
            (entry['url'], entry.get('method', 'GET'), entry.get('request_json'), entry.get('request_form')):
        raise ValueError('Loose acquisition identity differs from the harvest member: ' + entry['id'])
    path = Path(city.path(rec['path']))
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != rec['sha256']:
        raise ValueError('Loose acquisition hash mismatch: ' + entry['id'])
    return data, rec, (provenance, path)


def _row(entry, rec):
    return dict(member_id=entry['id'], name=entry['id'] + '.' + entry['format'], format=entry['format'],
                sha256=rec['sha256'], bytes=rec['bytes'], url=rec['url'], final_url=rec.get('final_url', ''),
                method=rec.get('method', 'GET'),
                request_json=json.dumps(rec['request_json'], sort_keys=True) if rec.get('request_json') is not None else '',
                request_form=json.dumps(rec['request_form'], sort_keys=True) if rec.get('request_form') is not None else '',
                retrieved=rec['retrieved'], content_type=rec.get('content_type') or '',
                source=rec.get('source', entry.get('title', '')),
                discovered_from=json.dumps(entry['discovered_from']) if isinstance(entry.get('discovered_from'), list)
                else entry.get('discovered_from', ''),
                transport=rec.get('transport', ''))


def pack(harvest, entries, session, allowed, pause_seconds=0.25, check=None, log=print):
    """Bring the archive to hold every entry in `entries`; fetch only the new.

    `check(entry, data)` may raise ValueError for a response that is HTTP-OK
    but not the answer asked for; the bytes are still kept (they are what the
    publisher returned) and the member is reported as unresolved. Returns
    (member_count, unresolved ids).
    """
    if not entries:
        raise ValueError('A harvest needs at least one member')
    ids = [e['id'] for e in entries]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate harvest member ids')
    for entry in entries:
        if entry['category'] != harvest.category:
            raise ValueError('Harvest member in another category: ' + entry['id'])
        check_request(entry, allowed)
    harvest.directory.mkdir(parents=True, exist_ok=True)
    existing, old_archive = {}, None
    if harvest.provenance.exists():
        _, old_archive = record(harvest.id, harvest.category)
        existing = {row['member_id']: row for row in _listing_rows(old_archive)}
    rows, unresolved, retire, fetched = [], [], [], 0
    started = time.time()
    with tempfile.TemporaryDirectory(prefix='harvest-', dir=harvest.directory) as temporary:
        staged = Path(temporary, harvest.id + '.zip')
        mode = zipfile.ZIP_DEFLATED if harvest.compress else zipfile.ZIP_STORED
        with zipfile.ZipFile(staged, 'w') as out, \
                (zipfile.ZipFile(old_archive) if old_archive else _NoArchive()) as old:
            for index, entry in enumerate(sorted(entries, key=lambda e: e['id']), start=1):
                row = existing.get(entry['id'])
                if row is not None:
                    if _identity(row) != _entry_identity(entry):
                        raise ValueError('Harvest member identity changed under its id: ' + entry['id'])
                    data = old.read(row['name'])
                    if hashlib.sha256(data).hexdigest() != row['sha256']:
                        raise ValueError('Archived member hash mismatch: ' + entry['id'])
                else:
                    adopted = _adopt_loose(harvest, entry)
                    if adopted is not None:
                        data, rec, paths = adopted
                        retire.append(paths)
                    else:
                        try:
                            with tempfile.TemporaryFile() as sink:
                                rec = fetch(entry, session, allowed, sink)
                                sink.seek(0)
                                data = sink.read()
                        except (requests.RequestException, ValueError, OSError,
                                subprocess.TimeoutExpired) as exc:
                            # an unobtained member stays out of the archive and
                            # is reported; the rest of the harvest still lands
                            unresolved.append(entry['id'])
                            log('UNOBTAINED', entry['id'], type(exc).__name__, str(exc)[:200])
                            time.sleep(pause_seconds)
                            continue
                        fetched += 1
                        time.sleep(pause_seconds)
                    row = _row(entry, rec)
                if check is not None:
                    try:
                        check(entry, data)
                    except ValueError as exc:
                        unresolved.append(entry['id'])
                        log('UNRESOLVED', entry['id'], str(exc)[:200])
                info = zipfile.ZipInfo(row['name'], date_time=FIXED_TIME)
                info.compress_type = mode
                info.external_attr = 0o644 << 16
                out.writestr(info, data)
                rows.append(row)
                if index % 250 == 0 or index == len(entries):
                    log('HARVEST', harvest.id, index, '/', len(entries), 'fetched', fetched,
                        'unresolved', len(unresolved))
            listing = io.StringIO()
            writer = csv.DictWriter(listing, fieldnames=LISTING_COLUMNS, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
            info = zipfile.ZipInfo(LISTING, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            out.writestr(info, listing.getvalue().encode('utf-8'))
        cached = _OPEN.pop(str(harvest.archive), None)
        if cached is not None:
            cached.close()
        os.replace(staged, harvest.archive)
    retrieved = sorted(r['retrieved'] for r in rows)
    rec = dict(path=city.rel(str(harvest.archive)), url=harvest.url, source=harvest.title,
               licence=harvest.licence, retrieved=retrieved[-1], retrieved_first=retrieved[0],
               sha256=_sha256(harvest.archive), bytes=harvest.archive.stat().st_size,
               content_type='application/zip', producing_script='extract/' + (harvest.harvester or 'harvest.py'),
               validation_status='acquired_unvalidated', coverage=harvest.coverage,
               method=harvest.method, harvest=True, member_count=len(rows),
               members_listing=LISTING, formats=sorted({r['format'] for r in rows}),
               packed=datetime.now(timezone.utc).isoformat())
    harvest.provenance.write_text(json.dumps({'files': [rec]}, indent=2, ensure_ascii=False) + '\n',
                                  encoding='utf-8')
    # the loose pairs now live in the archive with the same bytes and hashes
    for provenance, path in retire:
        provenance.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
    log('PACKED', harvest.id, len(rows), 'members', rec['bytes'], 'bytes',
        'adopted', len(retire), 'fetched', fetched, '%.0fs' % (time.time() - started))
    return len(rows), unresolved


class _NoArchive:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, name):
        raise KeyError(name)


def register(harvest, entries):
    """The harvest's single catalogue entry; loose entries for its members are retired."""
    path = Path(city.path('extract/sources.json'))
    catalogue = json.loads(path.read_text(encoding='utf-8'))
    entry = harvest.entry(len(entries))
    member_ids = {e['id'] for e in entries}
    kept, replaced, retired = [], False, 0
    for item in catalogue['sources']:
        if item['id'] == harvest.id:
            if item.get('kind') != 'harvest' or item['url'] != entry['url'] or item.get('method', 'GET') != entry['method']:
                raise ValueError('Immutable harvest identity changed: ' + harvest.id)
            kept.append(entry)
            replaced = True
        elif item['id'] in member_ids and item.get('kind') != 'harvest':
            retired += 1
        else:
            kept.append(item)
    if not replaced:
        kept.append(entry)
    catalogue['sources'] = kept
    path.write_text(json.dumps(catalogue, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return retired


def allowed_domains():
    return set(json.loads(Path(city.REPO, '.claude/settings.json').read_text(encoding='utf-8'))
               ['sandbox']['network']['allowedDomains'])


def member_record(row):
    """A listing row in the shape of a loose acquisition's provenance record."""
    record = dict(row)
    record['bytes'] = int(row['bytes'])
    for key in ('request_json', 'request_form'):
        record[key] = json.loads(row[key]) if row.get(key) else None
        if record[key] is None:
            del record[key]
    if record.get('discovered_from', '').startswith('['):
        record['discovered_from'] = json.loads(record['discovered_from'])
    return record


def source(harvest_id, category, member_id, listing=None):
    """(record, bytes) for one member - the harvest counterpart of
    extract_census_controls.source, which returns (record, path) for a loose file."""
    listing = members(harvest_id, category, verify=False) if listing is None else listing
    return member_record(listing[member_id]), read(harvest_id, category, member_id, listing)


def harvests(category, prefix):
    """The harvest ids of one family present under data/raw/<category>/ - every
    snapshot label of the NMMT route-stop census, for example - in id order."""
    directory = Path(city.path('data/raw', category))
    found = []
    for provenance in sorted(directory.glob('provenance_' + prefix + '*.json')):
        record = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
        if record.get('harvest'):
            found.append(provenance.stem.removeprefix('provenance_'))
    return found


@contextlib.contextmanager
def as_file(harvest_id, category, member_id, listing=None):
    """One member as a temporary file path, for tools that take a path (pdftotext)."""
    listing = members(harvest_id, category, verify=False) if listing is None else listing
    row = listing[member_id]
    with tempfile.TemporaryDirectory(prefix='harvest-member-') as temporary:
        path = Path(temporary, row['name'])
        path.write_bytes(read(harvest_id, category, member_id, listing))
        yield path
