#!/usr/bin/env python
"""Download TfNSW's daily Transport Performance & Analytics (TPA) series with provenance (#185).

Two series live behind the Open Data Hub's "Data Browser", which needs a hub
login - but the same CloudFront distribution serves each daily file to a
plain request that carries the hub as its Referer (documented on the hub's
own forum, opendataforum.transport.nsw.gov.au/t/opal-patronage/2087, and
measured 12 September 2026: 200 with the header, 403 without). No API key.

  * Opal Patronage  - tap-ons/offs by mode, hour and key commercial centre,
    January 2020 onwards, one file a day. "Newcastle and surrounds" is a
    centre: Newcastle Interchange, the light rail and the bus stops of
    postcodes 2293 and 2300 - and its FERRY rows are the only disclosed
    count of the Stockton ferry's Newcastle-side wharf the package holds.
    Counts are ROUNDED TO THE NEAREST 100 and printed `<100` below it, so a
    daily total is a BOUND, not a figure (documentation v2.0, May 2026).
  * BOAM (Bus Opal Assignment Model) - occupancy range per bus trip per stop,
    state-wide, ~400 MB a day. The Hunter depots (Hamilton, Belmont, Toronto,
    Cessnock, Anna Bay) are in it. One representative week is acquired, not
    the series: 7 x 400 MB is a raw acquisition, 2,000 x 400 MB is not.

Raw files land unmodified under data/raw/<series>/ with a provenance record
(data/raw/provenance_<series>.json, the tracked location) carrying the URL
pattern, retrieval date, licence and every file's sha256.
Re-running skips files already held (raw downloads are immutable).
"""
import sys as _sys
import city as _city
import argparse
import datetime
import hashlib
import json
import os
import urllib.request

BASE = 'https://opendata-tpa.transport.nsw.gov.au'
HEADERS = {'Referer': 'https://opendata.transport.nsw.gov.au/',
           'User-Agent': 'city-digital-twin/0.1 (research)'}
LICENCE = 'CC-BY 4.0'
SERIES = {
    'opal_patronage': dict(
        folder='Opal_Patronage', prefix='Opal_Patronage_',
        raw_dir='data/raw/opal/opal_patronage',
        source='TfNSW Open Data Hub - Opal Patronage (Opal Tap Data), daily files',
        dataset='https://opendata.transport.nsw.gov.au/data/dataset/opal-patronage',
        note='hourly tap-ons/offs by mode and key commercial centre; values rounded '
             'to the nearest 100, "<100" below; "Newcastle and surrounds" = Newcastle '
             'Interchange, the light rail and bus stops in postcodes 2293 and 2300'),
    'boam': dict(
        folder='BOAM', prefix='BOAM_',
        raw_dir='data/raw/boam',
        source='TfNSW Open Data Hub - BOAM Bus Opal Assignment Model, daily files',
        dataset='https://opendata.transport.nsw.gov.au/data/dataset/boam-bus-opal-assignment-model',
        note='occupancy range (bands of 20) per bus trip at each stop, state-wide; '
             'from 25 Feb 2026 the OAM allocation model, per documentation v2.0'),
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def days(start, end):
    d = start
    while d <= end:
        yield d
        d += datetime.timedelta(days=1)


def fetch(series, start, end):
    spec = SERIES[series]
    root = _city.path(spec['raw_dir'])
    os.makedirs(root, exist_ok=True)
    # the record sits where the repository tracks provenance - data/raw/provenance_*.json
    # - and names its files relative to `base`, the series' own directory
    prov_path = _city.path('data/raw/provenance_%s.json' % series)
    prov = {}
    if os.path.exists(prov_path):
        prov = {r['path']: r for r in json.load(open(prov_path, encoding='utf-8'))['files']}
    got = failed = skipped = 0
    for d in days(start, end):
        name = '%s%s.txt' % (spec['prefix'], d.strftime('%Y%m%d'))
        url = '%s/%s/%s/%s' % (BASE, spec['folder'], d.strftime('%Y-%m'), name)
        p = os.path.join(root, name)
        rel = name                        # relative to this record's own directory
        if os.path.exists(p) and os.path.getsize(p) > 100:
            skipped += 1
            if rel not in prov:
                prov[rel] = dict(path=rel, url=url, bytes=os.path.getsize(p),
                                 sha256=_sha256(p), retrieved=None)
            continue
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=1800) as r, open(p + '.part', 'wb') as f:
                while True:
                    c = r.read(1 << 20)
                    if not c:
                        break
                    f.write(c)
            os.replace(p + '.part', p)
        except Exception as e:                                       # noqa: BLE001
            failed += 1
            print('  FAIL %s: %s' % (name, e), flush=True)
            if os.path.exists(p + '.part'):
                os.remove(p + '.part')
            continue
        got += 1
        prov[rel] = dict(path=rel, url=url, bytes=os.path.getsize(p), sha256=_sha256(p),
                         retrieved=datetime.date.today().isoformat())
        print('  GET  %s  %12s B' % (name, format(prov[rel]['bytes'], ',')), flush=True)
    doc = dict(source=spec['source'], dataset=spec['dataset'], licence=LICENCE,
               base=spec['raw_dir'],
               access='%s/%s/<YYYY-MM>/%s<YYYYMMDD>.txt with header Referer: '
                      'https://opendata.transport.nsw.gov.au/ (no login, no API key)'
                      % (BASE, spec['folder'], spec['prefix']),
               note=spec['note'],
               files=[prov[k] for k in sorted(prov)])
    with open(prov_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, indent=2)
        f.write('\n')
    print('%s: %d fetched, %d already held, %d failed -> %s'
          % (series, got, skipped, failed, _city.rel(prov_path)), flush=True)
    return failed == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('series', choices=sorted(SERIES))
    ap.add_argument('--start', required=True, help='first day, YYYY-MM-DD')
    ap.add_argument('--end', required=True, help='last day, YYYY-MM-DD')
    a = ap.parse_args()
    ok = fetch(a.series, datetime.date.fromisoformat(a.start),
               datetime.date.fromisoformat(a.end))
    return 0 if ok else 1


if __name__ == '__main__':
    _sys.exit(main())
