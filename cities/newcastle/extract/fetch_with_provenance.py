#!/usr/bin/env python
"""Fetch a list of published files into data/raw/ and write their provenance.

Three fetchers (fetch_abs_dem.py, fetch_open_data.py, fetch_licences.py)
carried the same loop with small differences typed three times: skip a file
already held above a size floor, stream the download in 1 MB chunks under a
research user agent, hash it chunked, keep the day a held file was retrieved
rather than restamping it with today, and write one provenance record per
file. One loop here; each fetcher is its manifest and its rules.

Rules the loop keeps, each from the record (#199, 9.151): a file fetched THIS
run is stamped today; a file already held keeps the date its earlier record
carried; a held file with no earlier date takes the date it was written to
disk (`undated='disk'`, the record saying so) or today (`undated='today'`).
Raw downloads are immutable: a held file is never re-fetched.
"""
import datetime
import hashlib
import json
import os
import urllib.request

USER_AGENT = 'city-digital-twin/0.1 (research)'


def sha256(path):
    """Chunked, so peak memory is one buffer rather than one download: the
    871 MB hourly counts archive was once read whole to hash it."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def retrieved_from_disk(path):
    """The day a held file was written - urlretrieve and the streamed
    download both write it at retrieval."""
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def earlier_records(provenance_path):
    """{relative path: record} of an earlier provenance file, or {}."""
    if not os.path.exists(provenance_path):
        return {}
    try:
        with open(provenance_path, encoding='utf-8') as fh:
            return {r['path']: r for r in json.load(fh)}
    except (OSError, ValueError, TypeError, KeyError):
        return {}


def download(url, dest, timeout):
    """Stream `url` to `dest` in 1 MB chunks."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, 'wb') as f:
        while True:
            c = r.read(1 << 20)
            if not c:
                break
            f.write(c)


def fetch_all(manifest, root, provenance_name, min_bytes, timeout, undated='disk',
              continue_on_error=True):
    """Fetch every (relative path, url, description, licence) of `manifest`
    under `root` and write `root/<provenance_name>`; returns the records.

    `min_bytes`: a held file at or under this size is fetched again (a
    truncated download). `continue_on_error`: a failed fetch is printed and
    skipped (the rest of the manifest still lands) rather than raised.
    """
    provenance_path = os.path.join(root, provenance_name)
    prev = earlier_records(provenance_path)
    today = datetime.date.today().isoformat()
    records = []
    for rel, url, desc, lic in manifest:
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fetched = False
        if os.path.exists(p) and os.path.getsize(p) > min_bytes:
            print('SKIP %s (%s)' % (rel, format(os.path.getsize(p), ',')), flush=True)
        else:
            fetched = True
            print('GET  %s' % rel, flush=True)
            try:
                download(url, p, timeout)
            except Exception as e:                                 # noqa: BLE001
                if not continue_on_error:
                    raise
                print('  FAIL %s' % e, flush=True)
                continue
        sz = os.path.getsize(p)
        print('  %13s B' % format(sz, ','), flush=True)
        rec = {'path': rel, 'url': url, 'description': desc, 'licence': lic,
               'bytes': sz, 'sha256': sha256(p)}
        retrieved = today if fetched else (prev.get(rel) or {}).get('retrieved')
        if not retrieved:
            if undated == 'disk':
                retrieved = retrieved_from_disk(p)
                rec['retrieved_basis'] = ('file modification time on disk (written at '
                                          'download); no earlier record')
            else:
                retrieved = today
        rec['retrieved'] = retrieved
        records.append(rec)
    with open(provenance_path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(records, fh, indent=2)
    print('wrote %s (%d files)' % (provenance_name, len(records)), flush=True)
    return records
