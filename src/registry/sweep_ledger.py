#!/usr/bin/env python
"""The sweep ledger: what every declared sweep is for, and whether a run ever moved it.

    python src/registry/sweep_ledger.py            print the ledger for the selected city
    python src/registry/sweep_ledger.py --check    exit 1 if a swept field lacks a role
                                                   or an assumed sweep lacks a basis
    python src/registry/sweep_ledger.py --role answer      one role only
    python src/registry/sweep_ledger.py --never-set        only fields no overlay has set

The registry used one word for two things (#134). A sweep in DECISIONS.md 8.1's
sense is the sensitivity CURVE the study reports at P6 - no headline at a single
value. A sweep in 15's sense is the honesty BRACKET that lets an assumed value
validate at all. 238 of 254 declared sweeps had never been set by any overlay,
and nothing in the registry could say which of them were owed a run and which
were brackets that never would be. `sweep_role` says which; this prints it
beside the one fact that decides whether a sweep is a sweep in name only -
whether any overlay under the city's `overlays/` has ever set the field.

The rule is the resolver's (`registry.sweep_role_errors`), called here rather
than restated, so `--check` and a strict `load()` cannot disagree. This script
is a readable ledger, not a second gate: it is not in CI because the resolver
already refuses a breach at every strict load.
"""
import argparse
import collections
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))

import city as _city                                          # noqa: E402
import registry                                               # noqa: E402


def overlay_setters(fields):
    """{key: sorted overlay names} for every field any overlay of this city sets.

    Reads the three overlay kinds the resolver knows (`registry.OVERLAY_DIRS`)
    and nothing else, so a run overlay that never resolved still counts - it is
    the record of an intent to move the field, which is what the ledger asks.
    """
    setters = collections.defaultdict(set)
    for kind, folder in sorted(registry.OVERLAY_DIRS.items()):
        for path in sorted(glob.glob(os.path.join(folder, '*.json'))):
            with io.open(path, encoding='utf-8') as f:
                doc = json.load(f)
            name = '%s:%s' % (kind, os.path.splitext(os.path.basename(path))[0])
            for key in (doc.get('set') or {}):
                if key in fields:
                    setters[key].add(name)
    return {k: sorted(v) for k, v in setters.items()}


def sweep_kind(field):
    sweep = field.get('sweep')
    if isinstance(sweep, list):
        return 'interval'
    if isinstance(sweep, dict):
        for k in ('interval', 'categorical', 'proportional'):
            if k in sweep:
                return k
    return '?'


def rows_for(fields, setters):
    out = []
    for key in sorted(fields):
        f = fields[key]
        if f.get('sweep') is None:
            continue
        out.append({
            'field': key,
            'source': f.get('source'),
            'role': f.get('sweep_role') or '(none)',
            'kind': sweep_kind(f),
            'basis': bool(registry.sweep_basis_of(f)),
            'set_by': setters.get(key, []),
        })
    return out


def print_ledger(rows, out=sys.stdout):
    width = max(len(r['field']) for r in rows) if rows else 5
    out.write('%-*s  %-11s  %-12s  %-12s  %-5s  %s\n'
              % (width, 'field', 'source', 'role', 'sweep', 'basis', 'ever set by'))
    for r in rows:
        out.write('%-*s  %-11s  %-12s  %-12s  %-5s  %s\n'
                  % (width, r['field'], r['source'], r['role'], r['kind'],
                     'yes' if r['basis'] else 'NO',
                     '%d: %s' % (len(r['set_by']), ', '.join(r['set_by']))
                     if r['set_by'] else 'never'))


def print_summary(rows, out=sys.stdout):
    by_role = collections.Counter(r['role'] for r in rows)
    never = collections.Counter(r['role'] for r in rows if not r['set_by'])
    out.write('\nby role (swept fields / never set by any overlay):\n')
    for role in list(registry.SWEEP_ROLES) + ['(none)']:
        if by_role.get(role):
            out.write('  %-12s %4d / %4d\n' % (role, by_role[role], never.get(role, 0)))
    out.write('by role x source:\n')
    cross = collections.Counter((r['role'], r['source']) for r in rows)
    for (role, source), n in sorted(cross.items()):
        out.write('  %-12s %-11s %4d\n' % (role, source, n))
    no_basis = [r['field'] for r in rows if r['source'] == 'assumed' and not r['basis']]
    out.write('assumed sweeps without a basis: %d%s\n'
              % (len(no_basis), (' - ' + ', '.join(no_basis)) if no_basis else ''))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true',
                    help='exit 1 on a swept field without a role, or an assumed '
                         'sweep without a basis (the resolver\'s own rule)')
    ap.add_argument('--role', choices=registry.SWEEP_ROLES,
                    help='print only sweeps carrying this role')
    ap.add_argument('--never-set', action='store_true',
                    help='print only sweeps no overlay has ever set')
    a = ap.parse_args()

    fields, _origin = registry.load_registry()
    setters = overlay_setters(fields)
    rows = rows_for(fields, setters)
    if a.role:
        rows = [r for r in rows if r['role'] == a.role]
    if a.never_set:
        rows = [r for r in rows if not r['set_by']]

    print('city %s: %d fields, %d swept, %d set by at least one overlay\n'
          % (_city.CITY, len(fields), sum(1 for f in fields.values()
                                          if f.get('sweep') is not None),
             sum(1 for r in rows_for(fields, setters) if r['set_by'])))
    print_ledger(rows)
    print_summary(rows_for(fields, setters))

    if a.check:
        errors = registry.sweep_role_errors(fields)
        for e in errors:
            print('FAIL  ' + e)
        if errors:
            print('\n%d sweep-role breach(es)' % len(errors))
            return 1
        print('\nevery sweep carries a role and every assumed sweep a basis')
    return 0


if __name__ == '__main__':
    sys.exit(main())
