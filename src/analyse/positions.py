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

`--check --stale` (the sixteenth report, 8 October 2026) adds the two things
a cap cannot see: a page whose `Record read through` is more than
STALE_SECTIONS behind the next record number is STALE (exit 1) - two pages
described F35 under F39 for three families because nothing compared the
stamp with the record; and, when the ledger's newest family has a result in
the board's runs block, a page whose *What is measured* names no run of that
family gets a WARN (exit 0) - the handoff rule "What is measured holds the
newest result" applied by a tool rather than by memory.

`--second-homes` prints every position page and the brief line that restates
a figure the board's generated blocks own - the result run name, `N of 12`,
the registry and manifest counts, the licence split, the control's wall hours.
A fact with two homes goes stale in one of them (the F39 run name had
seventeen homes in seven files); the list is what the handoff self-check
"did any fact acquire a second home" used to answer by hand. Informational:
exit 0.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
import city  # noqa: E402  (the import roots come from the installed .pth, #181)

HISTORY_CAP = 15
STALE_SECTIONS = 3          # a page may trail the record by this many sections

READ_THROUGH = re.compile(r'\*\*Record read through:\*\*\s*§9\.(\d+)')
RUN_NAME = re.compile(r'\d{8}T\d{6}_\d+it_\d+(?:\.\d+)?pct')
GENERATED = re.compile(r'<!-- generated:(\w+) start -->\n(.*?)<!-- generated:\1 end -->', re.S)


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
        # the caps bound the HAND-WRITTEN page; a generated block (the families
        # table from the ledger, #229) is the artefact's and is not counted,
        # as the board's hand-line cap already excludes its generated blocks
        s = GENERATED.sub('', s)
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


def section(text, heading):
    """The body of one `## <heading>` section of a page ('' when absent)."""
    # the heading may carry a suffix ("## What is measured — what a run costs")
    m = re.search(r'^## %s[^\n]*\n(.*?)(?=^## |\Z)' % re.escape(heading), text, re.S | re.M)
    return m.group(1) if m else ''


def generated_blocks(board_text):
    return {name: body for name, body in GENERATED.findall(board_text)}


def newest_family_result_runs(board_text, newest_family):
    """The newest family's RESULT as the board reads it: the scoreboard block's
    run when that block names the newest family and says it is a result. The
    runs block also lists the family's probes (four iterations, citable for
    their clock only), which no page is asked to name; the scoreboard skips
    them by the registry's horizon floor, so the scoreboard's run is the one
    that counts."""
    sb = generated_blocks(board_text).get('scoreboard', '')
    head = sb.split('\n', 1)[0]
    m = RUN_NAME.search(head)
    if not m or ('family `%s`' % newest_family) not in head or '**A RESULT**' not in head:
        return []
    return [m.group(0)]


def stale_report(pages, next_section, newest_family, result_runs):
    """[(page, level, message)] - level STALE for a stamp too far behind the
    record, WARN for a page whose What is measured names none of the newest
    family's results."""
    out = []
    for path in pages:
        text = open(path, encoding='utf-8').read()
        name = os.path.basename(path)
        m = READ_THROUGH.search(text)
        if not m:
            out.append((name, 'STALE', 'no "Record read through" stamp'))
            continue
        behind = next_section - int(m.group(1))
        if behind > STALE_SECTIONS:
            out.append((name, 'STALE', 'read through §9.%s, %d sections behind the record (cap %d)'
                        % (m.group(1), behind, STALE_SECTIONS)))
        if result_runs:
            measured = section(text, 'What is measured')
            if not any(r in measured for r in result_runs):
                out.append((name, 'WARN', 'What is measured names no result of %s (%s)'
                            % (newest_family, ', '.join(result_runs))))
    return out


def board_figures(board_text):
    """The figures the board's generated blocks (and its one hand split) own:
    {label: figure text}. Missing pieces are left out, never guessed."""
    blocks = generated_blocks(board_text)
    out = {}
    sb = blocks.get('scoreboard', '')
    m = RUN_NAME.search(sb)
    if m:
        out['result run'] = m.group(0)
    m = re.search(r'Inside \d+%: \*\*([^*]+)\*\*', sb)
    if m:
        inside = [x.strip() for x in m.group(1).split(',') if x.strip()]
        n = 0 if inside == ['none'] else len(inside)
        out['N of 12'] = '%d of 12' % n
    st = blocks.get('state', '')
    m = re.search(r'\*\*(\d[\d,]*) fields\*\*', st)
    if m:
        out['registry fields'] = m.group(1)
    m = re.search(r'\*\*(\d[\d,]*) files\*\*', st)
    if m:
        out['manifest files'] = m.group(1)
    hand = GENERATED.sub('', board_text)
    m = re.search(r'(\d[\d,]*) CC-BY / (\d[\d,]*) ODbL', hand)
    if m:
        out['licence split'] = '%s CC-BY / %s ODbL' % (m.group(1), m.group(2))
    m = re.search(r'ran (\d+\.\d) h', blocks.get('lane', ''))
    if m:
        out['wall hours'] = '%s h' % m.group(1)
    return out


def second_homes(figures, docs):
    """[(label, figure, 'file:line', line text)] for every line of `docs` that
    restates one of the board's figures."""
    out = []
    for label, fig in figures.items():
        if label == 'N of 12':
            pat = re.compile(re.escape(fig))
        elif label in ('registry fields', 'manifest files'):
            pat = re.compile(r'(?<![\d,.])%s(?![\d,])\s*(?:\*\*)?\s*(?:fields|files|registry|declared)' % re.escape(fig))
        else:
            pat = re.compile(re.escape(fig))
        for path in docs:
            for i, line in enumerate(open(path, encoding='utf-8').read().split('\n'), 1):
                if pat.search(line):
                    out.append((label, fig, '%s:%d' % (os.path.relpath(path, REPO).replace('\\', '/'), i),
                                line.strip()[:110]))
    return out


def _all_pages():
    return sorted(os.path.join(positions_dir(), f) for f in os.listdir(positions_dir()) if f.endswith('.md'))


def _newest_family():
    fam = os.path.join(city.docs(), 'run_families.json')
    doc = json.load(open(fam, encoding='utf-8'))
    fams = sorted(doc['families'].items(), key=lambda kv: kv[1]['from_launch'])
    return fams[-1][0] if fams else None


def run_stale(paths):
    import record
    text = open(record.record_path(), encoding='utf-8').read()
    nxt = record.last_number(text) + 1
    newest = _newest_family()
    board = open(os.path.join(city.docs(), 'STATUS.md'), encoding='utf-8').read()
    runs = newest_family_result_runs(board, newest)
    rows = stale_report(paths, nxt, newest, runs)
    for name, level, msg in rows:
        print('%-5s %-40s %s' % (level, name, msg))
    stale = [r for r in rows if r[1] == 'STALE']
    print('positions --stale: next record 9.%d, newest family %s with %d result(s); %d STALE, %d WARN'
          % (nxt, newest, len(runs), len(stale), len(rows) - len(stale)))
    return 1 if stale else 0


def run_second_homes():
    board = open(os.path.join(city.docs(), 'STATUS.md'), encoding='utf-8').read()
    figures = board_figures(board)
    docs = _all_pages() + [os.path.join(city.docs(), 'NEXT_AGENT_BRIEF.md')]
    rows = second_homes(figures, [d for d in docs if os.path.exists(d)])
    for label, fig in figures.items():
        hits = [r for r in rows if r[0] == label]
        print('%-16s %-32s %d second home(s)' % (label, fig, len(hits)))
        for _, _, where, line in hits:
            print('    %-48s %s' % (where, line))
    print('positions --second-homes: %d figure(s) the board owns, %d restatement(s)' % (len(figures), len(rows)))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stamp', metavar='TOPIC', help='the page to stamp (a topic name or path)')
    ap.add_argument('--session', metavar='TEXT', help='e.g. "16 September 2026 (fifty-third session)"')
    ap.add_argument('--ref', metavar='9.NNN', help='the record section read through')
    ap.add_argument('--history', metavar='LINE', help='the new History entry, e.g. "§9.176 — five words"')
    ap.add_argument('--check', nargs='*', metavar='TOPIC', help='check caps on these pages (default: all)')
    ap.add_argument('--stale', action='store_true',
                    help='with --check: a stamp more than %d sections behind the record is STALE (exit 1); '
                         'What is measured naming none of the newest family\'s results is a WARN' % STALE_SECTIONS)
    ap.add_argument('--second-homes', action='store_true',
                    help='print every page and brief line that restates a figure the board generates')
    a = ap.parse_args()
    if a.stamp:
        if not (a.session and a.ref):
            raise SystemExit('--stamp needs --session and --ref')
        stamp(page_path(a.stamp), a.session, a.ref, a.history)
        return check([page_path(a.stamp)])
    rc = None
    if a.check is not None:
        paths = [page_path(t) for t in a.check] if a.check else _all_pages()
        rc = check(paths)
        if a.stale:
            rc = rc or run_stale(paths)
    if a.second_homes:
        rc = (rc or 0) | run_second_homes()
    if rc is not None:
        return rc
    ap.print_help()
    return 2


if __name__ == '__main__':
    # the pages carry UTF-8 punctuation; a cp1252 console (the gate's capture on
    # Windows) must not make a check die on the first arrow it prints
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
