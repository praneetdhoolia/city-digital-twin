#!/usr/bin/env python
"""The lane ledger: the single next task and the decisions it waits on.

    python src/analyse/lane.py                       # print the lane as the board shows it
    python src/analyse/lane.py --ask                 # the unanswered decisions, as JSON for AskUserQuestion
    python src/analyse/lane.py --answer D1 "<label>" [--note "..."]
    python src/analyse/lane.py --done routers-pair --ref 9.172
    python src/analyse/lane.py --check               # exit 1 if the ledger is malformed

`docs/lane.json` is the one home of "what is next" (DECISIONS.md 9.171): the
board's Next section and the brief's section 1 are generated from it by
`build_status_board.py`, and `/onboard` puts its unanswered decisions to the
user as clickable choices, the recommended option first. `/handoff` records
an answer here with `--answer`, then in DECISIONS.md 14 and on the issue's
AWAITING-DECISION line. A decision with an answer is never asked again; a
task marked done names the record section that closed it.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

import city as _city

PATH = _city.docs('lane.json')
TASK_KEYS = ('id', 'title', 'kind', 'status', 'recommended', 'cost', 'blocked_on',
             'opens_family', 'answers_issues', 'evidence')
DECISION_KEYS = ('id', 'question', 'options', 'recommended', 'issues', 'evidence',
                 'asked', 'answer', 'answered')
STATUSES = ('open', 'held', 'done', 'dropped')


def load() -> dict:
    with open(PATH, encoding='utf-8') as fh:
        return json.load(fh)


def save(doc: dict) -> None:
    doc['updated'] = _dt.date.today().isoformat()
    with open(PATH, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write('\n')


def problems(doc: dict) -> list[str]:
    out = []
    ids = set()
    for t in doc.get('tasks', []):
        missing = [k for k in TASK_KEYS if k not in t]
        if missing:
            out.append('task %s: missing %s' % (t.get('id', '?'), ', '.join(missing)))
        if t.get('status') not in STATUSES:
            out.append('task %s: status %r is not one of %s' % (t.get('id'), t.get('status'), STATUSES))
        if t.get('status') == 'done' and not t.get('done_ref'):
            out.append('task %s: done without a done_ref (the record section that closed it)' % t.get('id'))
        if t['id'] in ids:
            out.append('task id %s repeats' % t['id'])
        ids.add(t['id'])
    rec = [t for t in doc.get('tasks', []) if t.get('status') == 'open' and t.get('recommended')]
    if len(rec) > 1:
        out.append('more than one open task is recommended: %s' % ', '.join(t['id'] for t in rec))
    for d in doc.get('decisions', []):
        missing = [k for k in DECISION_KEYS if k not in d]
        if missing:
            out.append('decision %s: missing %s' % (d.get('id', '?'), ', '.join(missing)))
        if not d.get('options') or len(d['options']) < 2:
            out.append('decision %s: fewer than two options' % d.get('id'))
        if (d.get('answer') is None) != (d.get('answered') is None):
            out.append('decision %s: answer and answered must be set together' % d.get('id'))
        if d.get('answer') is not None and d['answer'] not in [o['label'] for o in d['options']]:
            out.append('decision %s: answer %r is not one of its options' % (d.get('id'), d['answer']))
    return out


def open_decisions(doc: dict) -> list[dict]:
    return [d for d in doc.get('decisions', []) if d.get('answer') is None]


def render(doc: dict) -> str:
    """The generated `lane` block: what is next, then the decisions required."""
    lines = []
    open_tasks = [t for t in doc.get('tasks', []) if t['status'] in ('open', 'held')]
    open_tasks.sort(key=lambda t: (not t.get('recommended'), t['status'] != 'open'))
    for i, t in enumerate(open_tasks, 1):
        flag = ' **(recommended)**' if t.get('recommended') else ''
        held = ' - HELD' if t['status'] == 'held' else ''
        issues = (' ' + ' '.join('#%d' % n for n in t['answers_issues'])) if t['answers_issues'] else ''
        fam = 'opens a family' if t.get('opens_family') else 'no family boundary'
        lines.append('%d. **%s**%s%s - %s; %s; blocked on: %s (%s;%s)'
                     % (i, t['title'], flag, held, t['cost'], fam, t['blocked_on'],
                        t['evidence'], issues))
    pend = open_decisions(doc)
    if pend:
        lines.append('')
        lines.append('**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):')
        for d in pend:
            opts = ' · '.join(o['label'] for o in d['options'])
            issues = (' ' + ' '.join('#%d' % n for n in d['issues'])) if d['issues'] else ''
            lines.append('- **%s.** %s Options: %s (%s;%s)' % (d['id'], d['question'], opts, d['evidence'], issues))
    done = [d for d in doc.get('decisions', []) if d.get('answer') is not None]
    if done:
        lines.append('')
        lines.append('Decided: ' + ' · '.join('%s = %s (%s)' % (d['id'], d['answer'], d['answered']) for d in done[-5:]))
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ask', action='store_true', help='print the unanswered decisions as JSON')
    ap.add_argument('--answer', nargs=2, metavar=('ID', 'LABEL'), help='record an answer')
    ap.add_argument('--note', default=None, help='a note stored with the answer')
    ap.add_argument('--done', metavar='TASK', help='mark a task done')
    ap.add_argument('--ref', default=None, help='the record section that closed the task, e.g. 9.172')
    ap.add_argument('--check', action='store_true', help='validate the ledger; exit 1 on a problem')
    ap.add_argument('--add-task', metavar='FILE', help='append a task from a JSON file with the task keys')
    ap.add_argument('--add-decision', metavar='FILE',
                    help='append a decision from a JSON file (id, question, options, recommended, '
                         'issues, evidence; asked defaults to today, answer to none)')
    a = ap.parse_args(argv)
    if a.add_task or a.add_decision:
        # 9.176: the fifty-third session added D5-D7 and re-aimed a task by
        # editing the JSON with an ad-hoc script; the ledger's shape is checked
        # here on the way in, so a malformed entry never reaches the board
        doc = load()
        with open(a.add_task or a.add_decision, encoding='utf-8') as fh:
            entry = json.load(fh)
        if a.add_task:
            entry.setdefault('status', 'open')
            entry.setdefault('recommended', False)
            entry.setdefault('opens_family', False)
            entry.setdefault('answers_issues', [])
            if any(t['id'] == entry.get('id') for t in doc['tasks']):
                print('task %s already exists' % entry.get('id'))
                return 1
            doc['tasks'].append(entry)
        else:
            entry.setdefault('asked', _dt.date.today().isoformat())
            entry.setdefault('answer', None)
            entry.setdefault('answered', None)
            entry.setdefault('issues', [])
            if any(d['id'] == entry.get('id') for d in doc['decisions']):
                print('decision %s already exists' % entry.get('id'))
                return 1
            doc['decisions'].append(entry)
        bad = problems(doc)
        if bad:
            print('refused - the entry would leave the ledger malformed: ' + '; '.join(bad))
            return 1
        save(doc)
        print('added %s %s' % ('task' if a.add_task else 'decision', entry['id']))
        return 0
    doc = load()
    bad = problems(doc)
    if a.check:
        for p in bad:
            print('  ' + p)
        print('LANE %s' % ('MALFORMED' if bad else 'ok: %d task(s), %d decision(s) open'
                            % (len([t for t in doc['tasks'] if t['status'] == 'open']),
                               len(open_decisions(doc)))))
        return 1 if bad else 0
    if bad:
        print('lane.json is malformed: ' + '; '.join(bad))
        return 1
    if a.ask:
        # The console is cp1252 on Windows and a decision's text carries en
        # dashes, arrows and minus signs; /onboard reads this JSON, so it is
        # written as UTF-8 whatever the console (session_gate.py does the same)
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')
        print(json.dumps(open_decisions(doc), indent=1, ensure_ascii=False))
        return 0
    if a.answer:
        did, label = a.answer
        for d in doc['decisions']:
            if d['id'] == did:
                if label not in [o['label'] for o in d['options']]:
                    print('%s is not an option of %s: %s' % (label, did, [o['label'] for o in d['options']]))
                    return 1
                d['answer'] = label
                d['answered'] = _dt.date.today().isoformat()
                if a.note:
                    d['note'] = a.note
                save(doc)
                print('recorded %s = %s' % (did, label))
                return 0
        print('no decision %s' % did)
        return 1
    if a.done:
        for t in doc['tasks']:
            if t['id'] == a.done:
                if not a.ref:
                    print('--ref <section> is required: the record section that closed it')
                    return 1
                t['status'] = 'done'
                t['done_ref'] = a.ref
                t['recommended'] = False
                save(doc)
                print('task %s done at %s' % (a.done, a.ref))
                return 0
        print('no task %s' % a.done)
        return 1
    print(render(doc))
    return 0


if __name__ == '__main__':
    sys.exit(main())
