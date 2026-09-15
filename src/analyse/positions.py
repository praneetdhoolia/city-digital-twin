"""Stamp a position page at handoff; keep its history capped; check its caps.

    python src/analyse/positions.py --stamp <topic> --session "16 September 2026 (fifty-third session)" \\
        --ref 9.176 --history "§9.176 — the pair a result; moves nothing"
    python src/analyse/positions.py --check [<topic> ...]

A `/handoff` rewrites every position page a session touched, and three parts
of that rewrite are the same on every page every time: the `**Updated:**`
line (the date, the session, the record section read through), the History
list (one new line at the top, at most fifteen kept) and the caps the shape
check enforces (130 lines, 14,000 bytes, 600 characters a line). The
fifty-third session did those by hand on five pages and hit the byte cap
three times (DECISIONS.md 9.176). This does the mechanical part; the prose -
what is built, measured, open - stays the session's.

`--stamp` never touches the family stamp: a page is stamped with the family
it was WRITTEN AGAINST (tests/doc_shape.json), which the session states when
it rewrites the page against a new family.

`--check` prints each page's lines, bytes and longest line against the caps
and exits 1 past any of them - seconds, so it runs after every page edit,
where the full gate runs once at the end.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'src'))
import city  # noqa: E402

HISTORY_CAP = 15


def _shape():
    with open(os.path.join(REPO, 'tests', 'doc_shape.json'), encoding='utf-8') as fh:
        return json.load(fh)['positions']


def positions_dir():
    return os.path.join(city.docs(), 'positions')


def page_path(topic):
    name = topic if topic.endswith('.md') else topic + '.md'
    return os.path.join(positions_dir(), os.path.basename(name))


def stamp(path, session, ref, history=None):
    s = open(path, encoding='utf-8').read()
    n = s.count('**Updated:**')
    if n != 1:
        raise SystemExit('%s: expected one **Updated:** line, found %d' % (path, n))
    s = re.sub(r'\*\*Updated:\*\* [^·\n]*·\s*\*\*Record read through:\*\* §[\d.]+',
               '**Updated:** %s · **Record read through:** §%s' % (session, ref), s, count=1)
    if history:
        head, sep, tail = s.partition('## History\n')
        if not sep:
            raise SystemExit('%s: no ## History section' % path)
        lines = tail.split('\n')
        # the section starts with a blank line; the entries follow
        entries = [l for l in lines if l.startswith('- §')]
        rest = [l for l in lines if not l.startswith('- §')]
        entry = history if history.startswith('- ') else '- ' + history
        if entry not in entries:
            entries.insert(0, entry)
        entries = entries[:HISTORY_CAP]
        # rebuild: keep the leading blank, then the entries, then any trailing blank
        tail = '\n' + '\n'.join(entries) + ('\n' if rest and rest[-1] == '' else '')
        s = head + sep + tail
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
    return s


def check(paths):
    shape = _shape()
    bad = 0
    for path in paths:
        s = open(path, encoding='utf-8').read()
        lines = s.split('\n')
        n_bytes = len(s.encode('utf-8'))
        longest = max(len(l) for l in lines)
        flags = []
        if len(lines) > shape['max_lines']:
            flags.append('%d lines > %d' % (len(lines), shape['max_lines']))
        if n_bytes > shape['max_bytes']:
            flags.append('%d bytes > %d (over by %d)' % (n_bytes, shape['max_bytes'], n_bytes - shape['max_bytes']))
        if longest > shape['max_line_chars']:
            flags.append('a line of %d chars > %d' % (longest, shape['max_line_chars']))
        hist = [l for l in lines if l.startswith('- §')]
        if len(hist) > HISTORY_CAP:
            flags.append('%d history entries > %d' % (len(hist), HISTORY_CAP))
        print('%-40s %4d lines %6d bytes  longest %3d  %s'
              % (os.path.basename(path), len(lines), n_bytes, longest,
                 'OVER: ' + '; '.join(flags) if flags else 'ok'))
        bad += bool(flags)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stamp', metavar='TOPIC', help='the page to stamp (a topic name or path)')
    ap.add_argument('--session', metavar='TEXT', help='e.g. "16 September 2026 (fifty-third session)"')
    ap.add_argument('--ref', metavar='9.NNN', help='the record section read through')
    ap.add_argument('--history', metavar='LINE', help='the new History entry, e.g. "§9.176 — five words"')
    ap.add_argument('--check', nargs='*', metavar='TOPIC', help='check caps on these pages (default: all)')
    a = ap.parse_args()
    if a.stamp:
        if not (a.session and a.ref):
            raise SystemExit('--stamp needs --session and --ref')
        stamp(page_path(a.stamp), a.session, a.ref, a.history)
        return check([page_path(a.stamp)])
    if a.check is not None:
        paths = [page_path(t) for t in a.check] if a.check else sorted(
            os.path.join(positions_dir(), f) for f in os.listdir(positions_dir()) if f.endswith('.md'))
        return check(paths)
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
