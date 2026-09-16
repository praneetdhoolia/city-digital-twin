"""Append a session's record section, its topical-index row and its §14 row.

    python src/analyse/record.py --next                       # the next section number
    python src/analyse/record.py --append --file section.md \\
        --index "| **title** | **§9.NNN** — summary |" \\
        --change "| 2026-09-16 | **Title (§9.NNN; #...; session).** what changed |"

DECISIONS.md is over 16,000 lines and append-only, and every session places
three things in it: one `## 9.NNN` section before `## 14.`, one row in the
topical index at the top, and one row at the head of the §14 change log. The
fifty-third session found the anchors and the next number by grep and placed
them with an ad-hoc script (DECISIONS.md 9.176); a mis-count or a misplaced
row is a frozen document's error. This finds the number, refuses a section
whose heading does not carry it, refuses a duplicate, and places all three.

The section file is the session's prose on the contract's template (What was
wrong / What changed / Measured / Deliberately not done / Consequences); its
first line must be `## 9.NNN <title> (...)` with the number `--next` printed.
The index row is placed directly below the previous section's row (the index
runs oldest-first within its block); the change-log row directly under the table head.
Nothing here edits an existing section: the record is frozen.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
import city  # noqa: E402  (the import roots come from the installed .pth, #181)

SECTION_RE = re.compile(r'^## 9\.(\d+) ', re.M)
CHANGE_HEAD = '## 14. Change log\n\n| Date | Change |\n|---|---|\n'


def record_path():
    return os.path.join(city.docs(), 'DECISIONS.md')


def last_number(text):
    nums = [int(m.group(1)) for m in SECTION_RE.finditer(text)]
    if not nums:
        raise SystemExit('no ## 9.NNN section in the record')
    return max(nums)


def append(text, section, index_row, change_row):
    n = last_number(text) + 1
    head = section.split('\n', 1)[0]
    m = re.match(r'## 9\.(\d+) \S', head)
    if not m or int(m.group(1)) != n:
        raise SystemExit('the section must start "## 9.%d <title> (...)"; got: %s' % (n, head[:80]))
    if ('## 9.%d ' % n) in text:
        raise SystemExit('9.%d already exists; the record is append-only' % n)
    anchor = '## 14. Change log'
    if anchor not in text:
        raise SystemExit('no "## 14. Change log" heading to place the section before')
    if not section.endswith('\n'):
        section += '\n'
    if not section.endswith('\n\n'):
        section += '\n'
    i = text.index(anchor)
    text = text[:i] + section + text[i:]
    # the index row goes directly BELOW the previous section's row: the
    # topical index runs oldest-first within its block
    prev = '**§9.%d**' % (n - 1)
    j = text.find(prev)
    if j == -1 or text.rfind('\n| ', 0, j) == -1:
        raise SystemExit('no topical-index row for §9.%d to place the new row below' % (n - 1))
    end = text.index('\n', j) + 1
    if not index_row.endswith('\n'):
        index_row += '\n'
    if ('**§9.%d**' % n) not in index_row:
        raise SystemExit('the index row must carry **§9.%d**' % n)
    text = text[:end] + index_row + text[end:]
    if CHANGE_HEAD not in text:
        raise SystemExit('the §14 table head is not the expected shape')
    k = text.index(CHANGE_HEAD) + len(CHANGE_HEAD)
    if not change_row.endswith('\n'):
        change_row += '\n'
    if ('§9.%d' % n) not in change_row:
        raise SystemExit('the change-log row must cite §9.%d' % n)
    text = text[:k] + change_row + text[k:]
    return text, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--next', action='store_true', help='print the next section number')
    ap.add_argument('--append', action='store_true', help='place the section, the index row and the §14 row')
    ap.add_argument('--file', help='the section text, first line "## 9.NNN <title> (...)"')
    ap.add_argument('--index', help='the topical-index row, carrying **§9.NNN**')
    ap.add_argument('--change', help='the §14 row, citing §9.NNN')
    a = ap.parse_args()
    path = record_path()
    text = open(path, encoding='utf-8').read()
    if a.next:
        print('9.%d' % (last_number(text) + 1))
        return 0
    if a.append:
        if not (a.file and a.index and a.change):
            raise SystemExit('--append needs --file, --index and --change')
        section = open(a.file, encoding='utf-8').read()
        new, n = append(text, section, a.index, a.change)
        open(path, 'w', encoding='utf-8', newline='\n').write(new)
        print('appended 9.%d: %d section lines, one index row, one change-log row'
              % (n, section.count('\n')))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
