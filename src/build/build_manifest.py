#!/usr/bin/env python
"""Build the data package manifest: every file, its provenance and its lineage.

Deliverable 2 of the proposal is an open data package with every derived input,
its provenance, licence status and processing lineage. This walks the tree,
hashes everything, counts rows, and merges the per-stage provenance records.
"""
import os
import csv
import glob
import json
import fnmatch
import hashlib
import datetime
import zipfile
import sys

# The manifest describes ONE CITY. Its paths stay city-relative - `data/...`,
# not `cities/newcastle/data/...` - so the manifest does not repeat the city's
# own name on all 376 of its rows, and a second city's manifest is comparable
# to this one row for row.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'src'))
import city as _city  # noqa: E402

ROOT = _city.CITY_DIR
SCAN = ['data/raw', 'data/processed', 'schedules', 'demand', 'params',
        'scenarios', 'networks/osm', 'networks/matsim']
SKIP_EXT = {'.pyc'}
# Per-stage provenance records: whatever the city's own adapters landed, found
# by convention rather than by a hardcoded list of one city's file names -
# RECURSIVELY under data/raw (#117: five records in subdirectories were never
# read, and 472 of 511 rows carried no licence).
PROVENANCE_FILES = (sorted(glob.glob(os.path.join(ROOT, 'data', 'raw', '**',
                                                  'provenance*.json'),
                                     recursive=True))
                    + sorted(glob.glob(os.path.join(ROOT, 'schedules', 'raw',
                                                    'provenance*.json'))))

# The city's declared sources (city.json `sources`): the licence a raw file
# carries is the licence its DECLARED source carries, resolved by the longest
# `provides` prefix. The record beside the download describes the download;
# the descriptor is canonical for the licence, so one source is never spelt
# three ways across its files.
SOURCES = _city.descriptor().get('sources') or []
# The city's declared licences for DERIVED layers (city.json
# `derived_licences`: city-relative glob -> licence), and the licence of
# everything else it built (`package_licence`). A share-alike source (OSM's
# ODbL) reaches into every layer built from it, and which layers those are is
# a fact about the city's build the city declares - the framework names no
# artefact of any city.
DERIVED_LICENCES = _city.descriptor().get('derived_licences') or {}
PACKAGE_LICENCE = _city.descriptor().get('package_licence') or ''

# Which script produced what, for the lineage graph. THE FRAMEWORK HALF ONLY:
# the generic pipeline scripts under src/build/. Everything a particular city
# acquires or builds for itself is declared by that city - its `adapters` block
# (acquisition) and its `lineage` block (city-owned builders) in city.json -
# and merged in below. No acquisition script and no city build script is named
# here (issue #62 B1).
LINEAGE = {
    'data/processed/network': 'src/build/build_network_layers.py + src/build/attach_gradient.py',
    'data/processed/schedule_extras': 'src/build/build_gtfs_extras.py',
    'data/processed/basemap.json': 'src/analyse/build_basemap.py',
    'data/processed/network/_speed_zone_report.json': 'src/build/attach_speed_zones.py',
    'data/processed/validation/count_station_links.csv': 'src/analyse/map_count_stations.py',
    'demand/population': 'src/build/build_population.py',
    'demand/plans': 'src/build/build_activity_chains.py',
    'demand/plans/matsim': 'src/build/build_matsim_plans.py',
    'params': 'src/build/build_params.py',
    # the measured and calibrated parameter files have their own producers
    # (tests/check_package.py asserts every producer names its artefact)
    'params/C2_network_factors.json': 'src/build/measure_network_factors.py',
    'params/C2_osm_defaults.json': 'src/build/measure_osm_defaults.py',
    'params/C4_mode_constraints.json': 'src/calibrate/measure_mode_constraints.py',
    'params/C5_calibration.json': 'src/calibrate/calibrate.py',
    'params/C6_departure_profile_check.json': 'src/calibrate/measure_departure_constraint.py',
    'scenarios/matsim': 'src/build/build_matsim_run_inputs.py',
    'networks/matsim': 'src/build/build_matsim_network.py (pt2matsim 26.6)',
}


def _city_script(token):
    """A lineage token to its repo-relative form: city-relative scripts gain
    the cities/<city>/ prefix, framework scripts (src/...) pass through."""
    token = token.strip()
    return token if token.startswith('src/') else 'cities/%s/%s' % (_city.CITY, token)


# The city's own `lineage` block: city-relative artefact prefix -> the
# script(s) that build it (`build/...` for that city's builders; a ` + `-joined
# entry names each contributing script, framework ones included).
for _prefix, _entry in (_city.descriptor().get('lineage') or {}).items():
    LINEAGE[_prefix] = ' + '.join(_city_script(t) for t in _entry.split(' + '))

# Every adapter's own `produces` declaration overlays the map above, so an
# adapter that produces a SPECIFIC FILE inside a directory another adapter
# owns (extract_freight_profile.py writing two CSVs into the observed layer)
# is attributed to the script that actually wrote it - longest prefix wins in
# lineage_for().
for _spec in _city.descriptor().get('adapters', {}).values():
    if _spec.get('script'):
        for _prefix in _spec.get('produces', []):
            LINEAGE[_prefix] = _city_script(_spec['script'])

# P2 build intermediates: large, regenerable, and not part of the package.
SKIP_DIRS = ('networks/matsim/_work',)


def sha256(p, limit=None):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def count_rows(p):
    if p.endswith('.csv'):
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                return max(0, sum(1 for _ in f) - 1)
        except Exception:
            return None
    if p.endswith('.jsonl'):
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                return sum(1 for _ in f)
        except Exception:
            return None
    if p.endswith('.zip'):
        try:
            z = zipfile.ZipFile(p)
            return len(z.namelist())
        except Exception:
            return None
    return None


def lineage_for(rel):
    best = ''
    for k, v in LINEAGE.items():
        if rel.replace('\\', '/').startswith(k) and len(k) > len(best):
            best = k
    return LINEAGE.get(best, '')


def source_for(rel):
    """The declared source whose `provides` prefix covers the path, or None."""
    best, best_len = None, -1
    for s in SOURCES:
        for prefix in s.get('provides') or []:
            p = prefix.strip('/')
            if (rel == p or rel.startswith(p + '/')) and len(p) > best_len:
                best, best_len = s, len(p)
    return best


def _resolve_record_path(key, here, base):
    """A record's file key to a city-relative path.

    Records name their files three ways: relative to a `base` directory the
    record declares, relative to the directory the record sits in (the dict
    form's `files` map), or relative to the layer root - `data/raw` or
    `schedules/raw` - as the list-form writers do. The candidate that exists
    on disk wins; the first is kept if none does, so an absent file still
    joins its record and the manifest shows what it was.
    """
    key = key.replace('\\', '/').lstrip('./')
    root = 'schedules/raw' if here.startswith('schedules') else 'data/raw'
    cands = []
    if base:
        cands.append('%s/%s' % (base.strip('/'), key))
    cands.append(('%s/%s' % (here, key)) if here not in ('', '.') else key)
    cands.append('%s/%s' % (root, key))
    for c in cands:
        if os.path.exists(os.path.join(ROOT, c)):
            return c
    return cands[0]


def provenance_records():
    """city-relative path -> provenance record, from every record file.

    Two record forms are landed by the adapters: a LIST of per-file dicts
    (`path`, `url`, `licence`, `retrieved`, ...; the GTFS list names `era` and
    `feed` instead of a path), and a DICT with a header (`source`, `licence`,
    `retrieved`, `purpose`) and a `files` map whose entries inherit the header
    and may override it. Both are read; a record that cannot be parsed is
    reported and skipped, never silently dropped (#117).
    """
    prov = {}
    for pf in PROVENANCE_FILES:
        if not os.path.exists(pf):
            continue
        here = os.path.relpath(os.path.dirname(pf), ROOT).replace('\\', '/')
        try:
            doc = json.load(open(pf, encoding='utf-8'))
        except Exception as e:                               # noqa: BLE001
            print('warn: %s (%s)' % (pf, e))
            continue
        if isinstance(doc, list):
            for r in doc:
                if not isinstance(r, dict):
                    continue
                key = r.get('path')
                if not key and r.get('feed'):
                    key = '%s/%s.zip' % (r.get('era', ''), r['feed'])
                if not key:
                    continue
                prov[_resolve_record_path(key, here, r.get('base'))] = r
        elif isinstance(doc, dict):
            header = {k: v for k, v in doc.items() if k != 'files'}
            entries = doc.get('files') or {}
            items = (entries.items() if isinstance(entries, dict)
                     else [(e.get('path'), e) for e in entries if isinstance(e, dict)])
            for name, e in items:
                if not name:
                    continue
                rec = dict(header)
                rec.update(e if isinstance(e, dict) else {})
                if rec.get('harvested'):
                    rec['retrieved'] = rec['harvested']   # per file, not the header's max
                rec.setdefault('description', rec.get('document') or rec.get('note')
                               or header.get('purpose') or header.get('source', ''))
                prov[_resolve_record_path(name, here, doc.get('base'))] = rec
        else:
            print('warn: %s is neither a list nor a dict of records' % pf)
    return prov


def licence_for(rel, stage, pr):
    """The licence a manifest row carries, by declaration (#117).

    raw: the declared source's licence where a source covers the path (the
    descriptor is canonical); else the record's own; else, for the package's
    own record files (provenance*.json, the `_`-prefixed logs and listings),
    the package licence. processed: the longest matching `derived_licences`
    glob, else the package licence. A blank is a row nobody declared, and
    tests/check_manifest.py refuses it.
    """
    src = source_for(rel)
    if stage == 'raw':
        if src and src.get('licence'):
            return src['licence']
        if pr.get('licence'):
            return pr['licence']
        name = os.path.basename(rel)
        if name.startswith('provenance') or name.startswith('_'):
            return PACKAGE_LICENCE
        return ''
    best = ''
    for pat in DERIVED_LICENCES:
        if fnmatch.fnmatch(rel, pat) and len(pat) > len(best):
            best = pat
    return DERIVED_LICENCES.get(best) or PACKAGE_LICENCE


def main():
    prov = provenance_records()

    files = []
    for base in SCAN:
        base = os.path.join(ROOT, base)
        if not os.path.isdir(base):
            continue
        for dirpath, _, names in os.walk(base):
            for n in sorted(names):
                p = os.path.join(dirpath, n)
                ext = os.path.splitext(n)[1].lower()
                if ext in SKIP_EXT or '__pycache__' in dirpath:
                    continue
                rel = os.path.relpath(p, ROOT).replace('\\', '/')
                if rel.startswith(SKIP_DIRS):
                    continue
                sz = os.path.getsize(p)
                stage = 'raw' if rel.startswith(('data/raw', 'networks/osm', 'schedules/raw')) \
                    else 'processed'
                pr = prov.get(rel, {})
                src = source_for(rel) if stage == 'raw' else None
                files.append(dict(
                    path=rel, bytes=sz, rows=count_rows(p),
                    sha256=sha256(p) if sz < 300 * 1 << 20 else 'skipped_large',
                    stage=stage,
                    produced_by=lineage_for(rel),
                    source=(pr.get('description') or pr.get('source')
                            or (src or {}).get('name', '')),
                    source_url=(pr.get('url') or pr.get('s3_key')
                                or (src or {}).get('url', '')),
                    licence=licence_for(rel, stage, pr),
                    retrieved=pr.get('retrieved', '')))

    total = sum(f['bytes'] for f in files)
    man = dict(
        project=_city.descriptor().get('description') or _city.descriptor()['name'],
        generated=datetime.datetime.now().replace(microsecond=0).isoformat(),
        base_year=_city.base_year(),
        crs=_city.crs_label(),
        n_files=len(files),
        total_bytes=total,
        total_gib=round(total / (1 << 30), 2),
        by_stage={s: sum(1 for f in files if f['stage'] == s) for s in ('raw', 'processed')},
        bytes_by_stage={s: sum(f['bytes'] for f in files if f['stage'] == s)
                        for s in ('raw', 'processed')},
        files=files)
    json.dump(man, open(os.path.join(ROOT, 'data', 'MANIFEST.json'), 'w'), indent=2)
    cols = ['path', 'stage', 'bytes', 'rows', 'produced_by', 'source', 'source_url',
            'licence', 'retrieved', 'sha256']
    with open(os.path.join(ROOT, 'data', 'MANIFEST.csv'), 'w', newline='',
          encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(files)
    print('files=%d  total=%.2f GiB' % (len(files), man['total_gib']))
    print('by stage:', man['by_stage'], man['bytes_by_stage'])
    print('\nlargest 12:')
    for f in sorted(files, key=lambda x: -x['bytes'])[:12]:
        print('  %10.1f MB  %s' % (f['bytes'] / 1e6, f['path']))


if __name__ == '__main__':
    main()
