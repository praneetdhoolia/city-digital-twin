#!/usr/bin/env python
"""The recommendation ledger: what the project reports asked for, and what became of it.

    python src/analyse/report_recs.py                  # the open recommendations, newest report first
    python src/analyse/report_recs.py --sync           # pull the newest report's recommendations into the ledger
    python src/analyse/report_recs.py --taken 20260914T152907:2 --evidence "9.170: processed/ holds arm 0's _fit.json"
    python src/analyse/report_recs.py --declined 20260914T152907:14 --evidence "the user's decision, 14 Sep"
    python src/analyse/report_recs.py --check          # exit 1 if the newest report has recommendations the ledger lacks

`docs/reports/recommendations.json` holds one row per recommendation a dated
report made (DECISIONS.md 9.171): its report stamp and rank, the text as the
report wrote it, what it repeats, and its status - `open`, `taken` (with the
record section or PR that did it) or `declined` (with who decided). Until now
each report re-derived this by reading its predecessors, and the untaken rows
were the same user decisions re-issued six times; `/onboard` now lists the
open rows in its briefing, `/handoff` marks the ones the session took, and the
next report's audit reads this file instead of guessing.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

import city as _city

REPORTS = _city.docs('reports')
PATH = os.path.join(REPORTS, 'recommendations.json')
STAMP = re.compile(r'^(\d{8}T\d{6})_project_report\.html$')
DATA = re.compile(r'<script type="application/json" id="report-data">(.*?)</script>', re.S)


def load() -> dict:
    if not os.path.exists(PATH):
        return {'description': 'see src/analyse/report_recs.py', 'rows': []}
    with open(PATH, encoding='utf-8') as fh:
        return json.load(fh)


def save(doc: dict) -> None:
    with open(PATH, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write('\n')


def newest_report() -> tuple[str, list[dict]] | None:
    """(stamp, recommendations) of the newest dated report on disk, or None."""
    if not os.path.isdir(REPORTS):
        return None
    names = sorted(n for n in os.listdir(REPORTS) if STAMP.match(n))
    if not names:
        return None
    name = names[-1]
    with open(os.path.join(REPORTS, name), encoding='utf-8') as fh:
        m = DATA.search(fh.read())
    if not m:
        return STAMP.match(name).group(1), []
    return STAMP.match(name).group(1), json.loads(m.group(1)).get('recommendations', [])


def missing(doc: dict) -> list[dict]:
    got = newest_report()
    if not got:
        return []
    stamp, recs = got
    have = {r['id'] for r in doc['rows']}
    out = []
    for i, r in enumerate(recs, 1):
        rid = '%s:%d' % (stamp, i)
        if rid not in have:
            out.append({'id': rid, 'report': stamp, 'rank': i, 'what': r.get('what', ''),
                        'repeat_of': r.get('repeat_of'), 'opens_family': bool(r.get('opens_family')),
                        # model | data | code | process - the report's own tag (9.176);
                        # a row synced from an older report carries none
                        'category': r.get('category'),
                        'status': 'open', 'evidence': None, 'updated': None})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--sync', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--taken', metavar='ID')
    ap.add_argument('--declined', metavar='ID')
    ap.add_argument('--evidence', default=None)
    a = ap.parse_args(argv)
    doc = load()
    if a.check:
        gap = missing(doc)
        for r in gap:
            print('  %s not in the ledger: %s' % (r['id'], r['what'][:90]))
        n_open = len([r for r in doc['rows'] if r['status'] == 'open'])
        print('RECOMMENDATIONS %s (%d open)' % ('UNSYNCED' if gap else 'synced', n_open))
        return 1 if gap else 0
    if a.sync:
        gap = missing(doc)
        doc['rows'] += gap
        save(doc)
        print('added %d recommendation(s); %d open' % (len(gap), len([r for r in doc['rows'] if r['status'] == 'open'])))
        return 0
    for flag, status in ((a.taken, 'taken'), (a.declined, 'declined')):
        if flag:
            if not a.evidence:
                print('--evidence is required: the record section, PR or decision')
                return 1
            for r in doc['rows']:
                if r['id'] == flag:
                    r['status'] = status
                    r['evidence'] = a.evidence
                    r['updated'] = _dt.date.today().isoformat()
                    save(doc)
                    print('%s -> %s' % (flag, status))
                    return 0
            print('no recommendation %s' % flag)
            return 1
    rows = [r for r in doc['rows'] if r['status'] == 'open']
    rows.sort(key=lambda r: (r['report'], r['rank']), reverse=True)
    print('OPEN RECOMMENDATIONS - %d of %d' % (len(rows), len(doc['rows'])))
    for r in rows:
        rep = (' [repeats %s]' % r['repeat_of']) if r.get('repeat_of') else ''
        fam = ' [opens a family]' if r.get('opens_family') else ''
        cat = (' [%s]' % r['category']) if r.get('category') else ''
        print('  %-20s %s%s%s%s' % (r['id'], r['what'][:150], rep, fam, cat))
    return 0


if __name__ == '__main__':
    sys.exit(main())
