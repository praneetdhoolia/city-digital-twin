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

    python tests/check_manifest.py                the active city (CITYSIM_CITY)
    python tests/check_manifest.py --all-cities   every city under cities/ - what
                                                  the session gate and CI run

A hole the city has not yet fixed is recorded in its own
`cities/<city>/tests/manifest_debt.json`, per rule, with a ceiling that may only
fall (see check_ceilings).
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys

import city
from manifest_io import manifest_reader

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


# A provenance record IS the retrieval record: its manifest row has no
# retrieval date of its own because the dates live inside it, one per file it
# describes. So `provenance*.json` under raw/ is exempt from the undated-raw
# rule BY RULE - and in exchange its contents are checked for a dated
# retrieval key whenever the file is in the checkout. Exempting by rule
# removed 590 listed paths of debt across the two cities (29 September 2026)
# rather than hiding them: the date is verified where it actually lives.
RETRIEVAL_KEY = re.compile(
    r'"(?:retrieved|retrieval|fetched|downloaded|accessed)\w*"\s*:\s*"\d{4}-\d\d-\d\d')


def is_provenance_record(path):
    base = norm(path).rsplit('/', 1)[-1]
    return base.startswith('provenance') and base.endswith('.json')


def check_provenance_dated(rows, resolve=None):
    """Every provenance record in the checkout carries a dated retrieval key."""
    resolve = resolve or city.path
    out = []
    for row in rows:
        if (row.get('stage') or '').strip() != 'raw' or not is_provenance_record(row['path']):
            continue
        full = resolve(norm(row['path']))
        if not os.path.exists(full):
            continue
        with open(full, encoding='utf-8', errors='replace') as f:
            if not RETRIEVAL_KEY.search(f.read()):
                out.append('%s: a provenance record with no dated retrieval key '
                           '(retrieved/retrieval_*/fetched/downloaded/accessed)'
                           % norm(row['path']))
    return out


# Two provenance holes a row may not carry. A RAW download with no retrieval
# date is an acquisition nobody can date (CLAUDE.md: every acquisition carries
# its retrieval timestamp), and a `lineage_scope` of `none` is a row whose
# ancestry the producing script never declared at any scope, so the licence
# claim beside it rests on nothing.
DATE_AND_SCOPE_RULES = (
    ('raw_without_retrieved',
     lambda row: ((row.get('stage') or '').strip() == 'raw'
                  and not (row.get('retrieved') or '').strip()
                  and not is_provenance_record(row['path'])),
     'raw row(s) carry no retrieval date'),
    ('lineage_scope_none',
     lambda row: (row.get('lineage_scope') or '').strip() == 'none',
     'row(s) carry lineage_scope none'),
)
# Byte drift: a file in the checkout whose sha256 or size is not the
# manifest's. Unlike the two rules above it is judged on the bytes, so a
# listed path ABSENT from the checkout (every gitignored file in CI) is not
# judged either way.
DRIFT_RULE = 'sha256_drift'
RULES = tuple(r[0] for r in DATE_AND_SCOPE_RULES) + (DRIFT_RULE,)

# The debt ledger is the CITY's, beside its other test expectations
# (cities/<city>/tests/): the framework states the rules, a city states the
# rows it has not yet fixed.
DEBT_FILE = ('tests', 'manifest_debt.json')


def load_ledger(path=None):
    """{rule: {ceiling, paths, ceiling_log, ...}} for this city ({} if none)."""
    # beside doc_currency.json, located the way check_doc_currency.py locates it
    path = path or os.path.join(city.CITY_DIR, *DEBT_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f).get('rules') or {}


def base_ledger():
    """The same ledger on origin/main, or None where that ref is not here
    (a shallow CI checkout). Read from the LOCAL ref; nothing is fetched."""
    rel = '%s/%s' % (CITY_REL, '/'.join(DEBT_FILE))
    try:
        p = subprocess.run(['git', 'show', 'origin/main:' + rel],
                           capture_output=True, text=True, encoding='utf-8')
    except OSError:
        return None
    if p.returncode != 0:
        ok = subprocess.run(['git', 'rev-parse', '--verify', '-q', 'origin/main'],
                            capture_output=True, text=True).returncode == 0
        return {} if ok else None      # the ref is here but the file is new: no base
    return (json.loads(p.stdout).get('rules') or {})


def check_ceilings(ledger, base=None):
    """The count beside each list, and the rule that it may only fall.

    - a rule's `ceiling` equals the number of listed paths: a path added
      without raising the ceiling fails, and a path removed without lowering
      it fails;
    - the ceiling equals the newest `ceiling_log` entry, and every entry
      carries a date and a reason - so a raise cannot be made silently;
    - against origin/main (when the ref is here), a ceiling that ROSE must
      bring a new log entry in the same change.
    """
    out = []
    for rule, entry in sorted(ledger.items()):
        if rule not in RULES:
            out.append('manifest debt names an unknown rule %r (known: %s)'
                       % (rule, ', '.join(RULES)))
            continue
        paths = entry.get('paths') or []
        ceiling = entry.get('ceiling')
        log = entry.get('ceiling_log') or []
        if not isinstance(ceiling, int):
            out.append('%s: the debt carries no integer ceiling' % rule)
            continue
        if len(set(paths)) != len(paths):
            out.append('%s: the debt lists a path twice' % rule)
        if len(paths) > ceiling:
            out.append('%s: %d path(s) listed above the ceiling of %d - a new '
                       'entry needs the ceiling raised in the same change, '
                       'with a dated ceiling_log entry giving the reason'
                       % (rule, len(paths), ceiling))
        elif len(paths) < ceiling:
            out.append('%s: %d path(s) listed under a ceiling of %d - the debt '
                       'shrank; lower the ceiling to %d and log it'
                       % (rule, len(paths), ceiling, len(paths)))
        if not log or log[-1].get('ceiling') != ceiling:
            out.append('%s: the newest ceiling_log entry must state the '
                       'current ceiling (%d)' % (rule, ceiling))
        for item in log:
            if not str(item.get('date') or '').strip() or not str(item.get('reason') or '').strip():
                out.append('%s: every ceiling_log entry carries a date and a '
                           'reason' % rule)
                break
        if base is not None:
            was = (base.get(rule) or {})
            was_ceiling = was.get('ceiling', 0)
            if ceiling > was_ceiling and len(log) <= len(was.get('ceiling_log') or []):
                out.append('%s: the ceiling rose from %d (origin/main) to %d '
                           'without a new ceiling_log entry giving the reason'
                           % (rule, was_ceiling, ceiling))
    return out


def check_recorded_debt(rows, debt, drifted=None, present=None):
    """Refuse each hole, except the paths recorded as debt - which may only SHRINK.

    `debt` maps a rule name to the exact paths that fail it. A failing path
    outside that list is a NEW hole and fails. A listed path that no longer
    fails (its row was fixed, or it left the manifest) also fails, so the entry
    must be deleted and the list can only get shorter. `drifted` is the set of
    present paths whose bytes are not the manifest's; `present` the set of
    manifest paths in this checkout (a listed drift path that is absent is not
    judged). Returns (failures, {rule: (failing, allowlisted)}).
    """
    failures, counts = [], {}
    judged = [(rule, {norm(r['path']) for r in rows if failing_row(r)}, what, None)
              for rule, failing_row, what in DATE_AND_SCOPE_RULES]
    if drifted is not None:
        judged.append((DRIFT_RULE, set(drifted),
                       'present file(s) differ from the manifest (sha256 or size)',
                       present))
    for rule, failing, what, seen in judged:
        allowed = set(debt.get(rule, ()))
        new = sorted(failing - allowed)
        fixed = sorted(p for p in allowed - failing if seen is None or p in seen)
        counts[rule] = (len(failing), len(allowed))
        if new:
            failures.append('%d %s outside the recorded debt: %s%s'
                            % (len(new), what, ', '.join(new[:6]),
                               ' ...' if len(new) > 6 else ''))
        if fixed:
            failures.append('%d path(s) in the recorded %s debt no longer fail '
                            'it - delete them from %s/%s and lower its ceiling: '
                            '%s%s'
                            % (len(fixed), rule, CITY_REL, '/'.join(DEBT_FILE),
                               ', '.join(fixed[:6]),
                               ' ...' if len(fixed) > 6 else ''))
    return failures, counts


def main():
    if not os.path.exists(MANIFEST):
        print('FAIL  %s not found' % MANIFEST)
        return 1

    checked = absent = unhashed = 0
    failures = []
    drift = {}                      # path -> what differs
    manifested = set()
    present = set()
    unlicensed = []
    rows = []

    with open(MANIFEST, encoding='utf-8') as f:
        for row in manifest_reader(f):
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
            present.add(path)
            # build_manifest.py records a sentinel (e.g. `skipped_large`) instead of a
            # digest for files it declined to hash; size is still authoritative there.
            recorded = (row['sha256'] or '').strip()
            if len(recorded) == 64 and all(c in '0123456789abcdef' for c in recorded):
                actual = sha256(full)
                if actual != recorded:
                    drift[path] = ('sha256 %s, manifest says %s'
                                   % (actual[:16], recorded[:16]))
                    continue
            else:
                unhashed += 1
            if row['bytes']:
                size = os.path.getsize(full)
                if size != int(row['bytes']):
                    drift[path] = ('%d bytes, manifest says %s'
                                   % (size, row['bytes']))

    for path in sorted(tracked_files() - manifested):
        failures.append('%s: tracked but absent from %s' % (path, MANIFEST))

    failures += check_lineage_licence(rows)
    failures += check_provenance_dated(rows)

    ledger = load_ledger()
    debt = {rule: frozenset(norm(p) for p in (e.get('paths') or ()))
            for rule, e in ledger.items()}
    failures += check_ceilings(ledger, base_ledger())
    debt_failures, debt_counts = check_recorded_debt(rows, debt, set(drift), present)
    for rule, (failing, allowed) in debt_counts.items():
        print('%s: %d row(s) fail, %d recorded as debt (ceiling %s)'
              % (rule, failing, allowed,
                 (ledger.get(rule) or {}).get('ceiling', 0)))
    # a drifted file inside the debt is still SHOWN, named as the debt it is
    for path in sorted(set(drift) & debt.get(DRIFT_RULE, frozenset())):
        issue = (ledger.get(DRIFT_RULE) or {}).get('issue')
        print('DEBT  %s: %s (recorded drift%s)'
              % (path, drift[path], ', #%s' % issue if issue else ''))
    for path in sorted(set(drift) - debt.get(DRIFT_RULE, frozenset())):
        print('FAIL  %s: %s' % (path, drift[path]))
    failures += debt_failures

    print('verified %d present file(s) (%d size-only, no digest recorded); '
          '%d manifest entr(ies) not in this checkout (gitignored bulk data)'
          % (checked, unhashed, absent))
    if unlicensed:
        failures.append('%d manifest row(s) carry no licence: %s%s'
                        % (len(unlicensed), ', '.join(unlicensed[:6]),
                           ' ...' if len(unlicensed) > 6 else ''))
    for line in failures:
        print('FAIL  ' + line)
    if failures:
        print('\n%d failure(s)' % len(failures))
        return 1
    print('OK')
    return 0


def all_cities():
    """Run this check once per city under cities/ and fail if any city fails
    (the gate and CI both call this; #252)."""
    return city.run_per_city(__file__, needs=os.path.join('data', 'MANIFEST.csv'))


if __name__ == '__main__':
    sys.exit(all_cities() if '--all-cities' in sys.argv[1:] else main())
