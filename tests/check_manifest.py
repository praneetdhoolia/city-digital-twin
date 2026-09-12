#!/usr/bin/env python
"""Verify committed data files against data/MANIFEST.csv.

Offline, dependency-free counterpart to tests/check_package.py. The bulk of the
package is gitignored (see .gitignore), so a CI checkout holds only a subset of
the manifest; this checks exactly that subset:

  1. every manifest row whose file is present hashes to its recorded sha256 and
     matches its recorded byte count;
  2. every tracked file under data/processed appears in the manifest.

Absent files are reported and skipped, not failed — that is the normal state of a
fresh clone. Run tests/check_package.py locally, against the full package, for the
cross-layer integrity checks that need the bulk data.

Exits non-zero on any mismatch or unmanifested tracked file.
"""
import csv
import hashlib
import os
import subprocess
import sys

import city

# Manifest rows are CITY-RELATIVE (`data/processed/...`), so they are resolved
# against the city directory rather than the working directory. The same row in
# two cities' manifests describes the same layer.
MANIFEST = city.path('data', 'MANIFEST.csv')
CITY_REL = os.path.relpath(city.CITY_DIR, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))).replace(os.sep, '/')
CHUNK = 1 << 20


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def norm(path):
    return path.replace(os.sep, '/')


def tracked_files():
    """Tracked files under this city's processed data, as city-relative paths."""
    out = subprocess.run(['git', 'ls-files', '-z', CITY_REL + '/data/processed'],
                         capture_output=True, text=True, check=True).stdout
    prefix = CITY_REL + '/'
    return {norm(p)[len(prefix):] for p in out.split(chr(0)) if p}


# The share-alike licence labels THIS city declares, from the sources it
# marked `share_alike`. Nothing here names a licence, a source or a city.
SHARE_ALIKE = tuple(sorted({
    s['licence'] for s in (city.descriptor().get('sources') or [])
    if s.get('share_alike') and s.get('licence')}))
# What an undetermined row costs. It is a RATCHET, not a target: a row whose
# ancestry the evidence does not decide is an honest outcome, but the number
# may only fall. The cap is the city's, beside its other document rules.
UNDETERMINED_CAP = city.descriptor().get('manifest_undetermined_lineage_max')


def check_lineage_licence(rows):
    """The manifest's two provenance claims must agree, row by row (#159).

    A row states an ancestry (`share_alike_ancestor`, resolved from the
    producing scripts' declared per-output inputs) and a licence (resolved
    from the city's declaration). They are arrived at independently, and
    nothing in this repository compared them until now - so 129 rows named an
    OpenStreetMap ancestor while carrying a CC-BY licence and nobody saw it.

    Both directions are failures. A share-alike ancestor under a permissive
    licence UNDER-restricts, which is a licence breach; a share-alike licence
    with no such ancestor OVER-restricts a file the package is free to
    publish. `undetermined` is neither: the row says the evidence does not
    decide, and it is counted against a ratchet rather than asserted.
    """
    if not SHARE_ALIKE:
        return []
    out, undetermined = [], []
    for row in rows:
        verdict = (row.get('share_alike_ancestor') or '').strip()
        licence = row.get('licence') or ''
        share_alike = any(lic in licence for lic in SHARE_ALIKE)
        if verdict == 'yes' and not share_alike:
            out.append('%s: ancestry is share-alike (%s) but the licence is '
                       '"%s"' % (norm(row['path']), SHARE_ALIKE[0],
                                 licence[:60]))
        elif verdict == 'no' and share_alike:
            out.append('%s: licence is share-alike but no share-alike '
                       'ancestor was found' % norm(row['path']))
        elif verdict == 'undetermined':
            undetermined.append(norm(row['path']))
        elif verdict not in ('yes', 'no'):
            out.append('%s: no share_alike_ancestor verdict - regenerate the '
                       'manifest' % norm(row['path']))
    cap = UNDETERMINED_CAP
    print('lineage/licence: %d row(s) agree, %d undetermined%s'
          % (len(rows) - len(out) - len(undetermined), len(undetermined),
             '' if cap is None else ' (cap %d)' % cap))
    if cap is not None and len(undetermined) > cap:
        producers = sorted({r['produced_by'] for r in rows
                            if norm(r['path']) in set(undetermined)})
        out.append('%d manifest row(s) have an undetermined share-alike '
                   'ancestry, above the declared cap of %d. The producing '
                   'script must declare OUTPUT_INPUTS: %s'
                   % (len(undetermined), cap, ', '.join(producers[:4])))
    return out


def main():
    if not os.path.exists(MANIFEST):
        print('FAIL  %s not found' % MANIFEST)
        return 1

    checked = absent = unhashed = 0
    failures = []
    manifested = set()
    unlicensed = []
    rows = []

    with open(MANIFEST, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows.append(row)
            path = norm(row['path'])
            manifested.add(path)
            # every row carries a licence (#117): a blank is a file nobody
            # declared a source for, and the OSM share-alike boundary is
            # invisible when 472 rows say nothing
            if not (row.get('licence') or '').strip():
                unlicensed.append(path)
            full = city.path(path)
            if not os.path.exists(full):
                absent += 1
                continue
            checked += 1
            # build_manifest.py records a sentinel (e.g. `skipped_large`) instead of a
            # digest for files it declined to hash; size is still authoritative there.
            recorded = (row['sha256'] or '').strip()
            if len(recorded) == 64 and all(c in '0123456789abcdef' for c in recorded):
                actual = sha256(full)
                if actual != recorded:
                    failures.append('%s: sha256 %s, manifest says %s'
                                    % (path, actual[:16], recorded[:16]))
                    continue
            else:
                unhashed += 1
            if row['bytes']:
                size = os.path.getsize(full)
                if size != int(row['bytes']):
                    failures.append('%s: %d bytes, manifest says %s'
                                    % (path, size, row['bytes']))

    for path in sorted(tracked_files() - manifested):
        failures.append('%s: tracked but absent from %s' % (path, MANIFEST))

    failures += check_lineage_licence(rows)

    print('verified %d present file(s) (%d size-only, no digest recorded); '
          '%d manifest entr(ies) not in this checkout (gitignored bulk data)'
          % (checked, unhashed, absent))
    for line in failures:
        print('FAIL  ' + line)
    if unlicensed:
        failures.append('%d manifest row(s) carry no licence: %s%s'
                        % (len(unlicensed), ', '.join(unlicensed[:6]),
                           ' ...' if len(unlicensed) > 6 else ''))
    if failures:
        print('\n%d failure(s)' % len(failures))
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
