#!/usr/bin/env python
"""The one gate both session skills run, and the digest a session opens with.

    python src/run/session_gate.py --digest    what a session needs to know (2 s)
    python src/run/session_gate.py             every gate; exit 1 on any failure
    python src/run/session_gate.py --quick     the gates that need no toolchain

Before this existed, `/onboard` and `/handoff` each listed the gate commands
in their own words, and the two lists disagreed: the onboarding list ran
`bootstrap_toolchain.py --verify` - which recompiles `.tools/classes` - while
the brief's first trap said never to do that while an arm runs. One script,
called by both, ends that: it looks for a running arm and SKIPS the compile
when one is up, and it prints each gate's verdict on one line so a session
reads a digest rather than six commands' output.

`--digest` prints the goal, the generated blocks of the board (the scoreboard,
the state, the runs on disk), whether the machine is busy, how far the branch
is ahead of `origin/main`, and the open pull requests when `gh` answers. It
computes nothing about the model; the board's blocks are what
`build_status_board.py` last wrote, and the digest says so.
"""
import argparse
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
# the session opener installs the import roots before anything else is
# imported, so a fresh clone's first gate works (#181)
sys.path.insert(0, os.path.join(ROOT, 'src', 'setup'))
import install_paths                                              # noqa: E402
install_paths.activate()
from procs import arm_running                                     # noqa: E402
import city as _city                                              # noqa: E402

PY = sys.executable
for _stream in (sys.stdout, sys.stderr):      # the digest carries UTF-8 punctuation; a cp1252 console must not mangle it
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')


def _run(cmd, timeout):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 124, 'timed out after %ss' % timeout
    except OSError as exc:
        return 127, str(exc)


def git_ahead():
    rc, out = _run(['git', 'rev-list', '--count', 'origin/main..HEAD'], 30)
    branch = _run(['git', 'branch', '--show-current'], 30)[1].strip()
    return (int(out.strip()) if rc == 0 and out.strip().isdigit() else None), branch


def open_prs():
    rc, out = _run(['gh', 'pr', 'list', '--state', 'open', '--json',
                    'number,title,headRefName', '--jq',
                    '.[] | "#\\(.number) \\(.title) [\\(.headRefName)]"'], 20)
    return out.strip().splitlines() if rc == 0 else None


def board_blocks():
    path = _city.docs('STATUS.md')
    if not os.path.exists(path):
        return {}
    text = open(path, encoding='utf-8').read()
    return dict(re.findall(r'<!-- generated:(\w+) start -->\n(.*?)<!-- generated:\1 end -->',
                           text, re.S))


def digest():
    goal = _city.docs('GOAL.md')
    print('=' * 78)
    print('SESSION DIGEST - city %s' % _city.CITY)
    print('=' * 78)
    if os.path.exists(goal):
        first = [l for l in open(goal, encoding='utf-8').read().splitlines()
                 if l.startswith('# ')]
        print('GOAL  %s' % (first[0][2:] if first else goal))
        print('      read it: %s' % os.path.relpath(goal, ROOT))
    else:
        print('GOAL  no docs/GOAL.md - write one before anything else')
    blocks = board_blocks()
    for name in ('scoreboard', 'state', 'runs'):
        body = blocks.get(name)
        print()
        print('-- %s (from the board; regenerate with build_status_board.py) --' % name.upper())
        print(body.rstrip() if body else '   (no generated block on the board)')
    print()
    busy = arm_running()
    if busy is None:
        print('MACHINE  could not list processes')
    elif busy:
        print('MACHINE  BUSY - an arm is running: %s. Do not recompile .tools/classes; '
              'one arm at a time.' % ', '.join(busy))
        # 9.176, #225: a JVM alive under a dead harness is a run nobody is
        # watching, and BUSY alone said nothing about it for 22 hours
        try:
            import run_failure
            for name, pid, age in run_failure.orphaned_running(
                    os.path.join(ROOT, 'results')):
                print('         ORPHANED: %s - its harness (pid %s) is DEAD; the '
                      'JVM writes on (log %d s old) with no ceiling, stall or '
                      'gate watcher. `run.py --stop %s --cause "..."` now, or '
                      '`run.py --close-out %s` once it reaches its horizon.'
                      % (name, pid, age, name, name))
        except Exception as exc:                          # noqa: BLE001
            print('         (orphan check unavailable: %s)' % exc)
    else:
        print('MACHINE  idle (no java process above 2 GB)')
    ahead, branch = git_ahead()
    print('BRANCH   %s, %s commit(s) ahead of origin/main%s'
          % (branch or '?', '?' if ahead is None else ahead,
             ' - unmerged work; the session PR carries it' if ahead else ''))
    prs = open_prs()
    if prs is None:
        print('PRS      gh unavailable - run: gh pr list --state open')
    elif prs:
        print('PRS      OPEN: ' + ' | '.join(prs))
    else:
        print('PRS      none open')
    for label, line in lane_lines():
        print('%-8s %s' % (label, line))
    print('=' * 78)


def lane_lines():
    """The lane's top task, the open decisions, the open recommendations and
    whether the newest arm's price still describes the committed build (9.171)."""
    out = []
    try:
        import lane as _lane
        doc = _lane.load()
        top = [t for t in doc['tasks'] if t['status'] == 'open']
        top.sort(key=lambda t: not t.get('recommended'))
        if top:
            t = top[0]
            out.append(('LANE', '%s%s - %s; blocked on: %s'
                        % (t['title'][:110], ' (recommended)' if t.get('recommended') else '',
                           t['cost'][:80], t['blocked_on'][:80])))
        pend = _lane.open_decisions(doc)
        out.append(('DECIDE', '%d decision(s) unanswered%s - `python src/analyse/lane.py --ask`, then '
                    'AskUserQuestion with its options' % (len(pend), ': ' + ', '.join(d['id'] for d in pend) if pend else '')))
    except Exception as e:                                     # noqa: BLE001
        out.append(('LANE', 'docs/lane.json unreadable (%s)' % e))
    try:
        import report_recs as _rr
        rows = [r for r in _rr.load()['rows'] if r['status'] == 'open']
        gap = _rr.missing(_rr.load())
        out.append(('RECS', '%d report recommendation(s) open%s - `python src/analyse/report_recs.py`'
                    % (len(rows), '; the newest report is UNSYNCED (--sync)' if gap else '')))
    except Exception as e:                                     # noqa: BLE001
        out.append(('RECS', 'recommendation ledger unreadable (%s)' % e))
    try:
        import arm_cost as _ac
        import run_matsim as _rm
        arms = _ac.observed_arms()
        # the price that matters is the one at the ARM fraction - the largest
        # fraction any observed arm ran at - not a 1 % smoke probe's clock
        top = max((float(a.get('fraction') or 0) for a in arms), default=0)
        arms = [a for a in arms if float(a.get('fraction') or 0) == top]
        newest = arms[0] if arms else None
        current = _rm.controler_sha256()
        priced = (newest or {}).get('controler_sha256')
        if newest and priced and current and priced != current:
            out.append(('PRICE', 'the newest priced arm %s ran controler %s; the committed build is %s - '
                        'a quote from it is NOT a price until a 25 %% probe runs on this build'
                        % (newest.get('name'), priced[:12], current[:12])))
        elif newest:
            out.append(('PRICE', 'the newest priced arm %s ran the committed controler build; '
                        '`python src/analyse/arm_cost.py --run-config <cfg> --iterations 250` quotes it'
                        % newest.get('name')))
    except Exception as e:                                     # noqa: BLE001
        out.append(('PRICE', 'could not compare the priced build with the committed one (%s)' % e))
    return out


GATES = [
    # (label, command, needs_toolchain)
    ('import roots', [PY, 'src/setup/install_paths.py', '--check'], False),
    ('manifest', [PY, 'tests/check_manifest.py'], False),
    ('compile', [PY, '-m', 'compileall', '-q', 'src', 'tests', 'cities', 'run.py'], False),
    ('hardcoding', [PY, 'src/registry/check_hardcoding.py', '--strict'], False),
    ('doc currency', [PY, 'tests/check_doc_currency.py', '--strict'], False),
    ('doc shape', [PY, 'tests/check_doc_shape.py', '--strict'], False),
    ('doc links', [PY, 'tests/check_doc_links.py', '--strict'], False),
    # a credential in a tracked file is published by the next push (the
    # fourteenth report, 25 September 2026)
    ('no secrets', [PY, 'tests/check_secrets.py'], False),
    ('board blocks', [PY, 'src/analyse/build_status_board.py', '--check'], False),
    # 9.171: the lane ledger is the one home of "what is next"; the board and
    # the brief render it, and a malformed ledger renders nothing
    ('lane ledger', [PY, 'src/analyse/lane.py', '--check'], False),
    ('report recs', [PY, 'src/analyse/report_recs.py', '--check'], False),
    ('city contract', [PY, 'src/registry/check_city.py', '--all'], False),
    ('schema current', [PY, 'src/registry/render_schema.py', '--check'], False),
    # CI's city-contract job checks the generated reference; the gate only
    # regenerated it under --fix, so a stale one passed here and failed there
    # (PR #256)
    ('config reference', [PY, 'src/registry/render_docs.py', '--check'], False),
    ('city agnostic', [PY, 'tests/check_city_agnostic.py'], False),
    ('dead runs say why', [PY, 'src/run/run_failure.py', '--check'], False),
    ('gate watcher', [PY, 'tests/check_gate_watcher.py'], False),
    ('launch refusal', [PY, 'tests/check_launch_refusal.py'], False),
    ('registry rules', [PY, 'tests/check_registry_rules.py'], False),
    # 9.154: what the FRAMEWORK is deciding in the modules the model writes
    # into. STRICT since 11 September 2026: the backlog it deferred strict for
    # (31 unreviewed defaults) was worked to 0 at 9.164, and the rule this line
    # stated - it becomes a gate when the backlog is worked down, exactly as
    # check_hardcoding did - is now applied. A new default decided unreviewed
    # is a regression, not a backlog.
    ('matsim defaults', [PY, 'src/registry/check_matsim_defaults.py', '--strict'], False),
    # #133: the functions that decide correctness, on synthetic inputs
    ('unit tests', [PY, '-m', 'pytest', '-q', 'tests/unit'], False),
    ('fit figures', [PY, 'src/analyse/build_fit_figures.py', '--check'], False),
    # GOAL.md requirement 10: every open issue closed or awaiting a run
    ('issues gated', [PY, 'src/run/issue_gate.py'], False),
    ('toolchain', [PY, 'src/setup/bootstrap_toolchain.py', '--verify'], True),
    # the Java engines' probes: two of them died in checkConsistency for a
    # week because nothing ran them (fourteenth report, 25 September 2026)
    ('java probes', [PY, 'src/run/run_signal_probes.py'], True),
]


# What `--fix` may regenerate, in dependency order (9.155).
#
# EVERY entry regenerates a GENERATED artefact from the artefacts it derives
# from, and nothing else. Prose is never on this list: a number in a living
# document is a claim a person wrote, and `check_doc_currency` deliberately
# reports it rather than rewriting it - the record must never be edited to keep
# a check green, and a claim whose pattern stopped matching wants re-aiming, not
# substituting. So `doc currency`, `doc shape`, `hardcoding`, `unit tests`,
# `city agnostic`, `registry rules`, `issues gated`, `dead runs say why` and the
# toolchain are all deliberately absent: each reports a defect a person fixes.
#
# The order matters. The board reads the run index, so the index is rebuilt
# first; the schema and the config reference read the registry, so a registry
# addition regenerates both before the board is re-checked.
FIXES = [
    ('run index', [PY, 'src/analyse/build_run_index.py'],
     'the board reads it, and a run that finished after the last session '
     'leaves it one row short'),
    ('config reference', [PY, 'src/registry/render_docs.py'],
     'regenerated from the registry on every field change'),
    ('schema', [PY, 'src/registry/render_schema.py'],
     'required_fields.json and layers.json, regenerated from the registry'),
    ('fit figures', [PY, 'src/analyse/build_fit_figures.py'],
     'drawn from the run the calibrated base was written from'),
    ('board blocks', [PY, 'src/analyse/build_status_board.py'],
     "the board's generated blocks, rewritten from the artefacts"),
]
# The gates each regenerator can turn green. A gate not named here is never a
# reason to run one.
FIXES_FOR = {
    'board blocks': ('run index', 'board blocks'),
    'schema current': ('schema',),
    'config reference': ('config reference',),
    'city contract': ('config reference', 'schema'),
    # the portable contract is GENERATED from the registry, so a registry
    # addition makes it stale and it reads as a city-agnosticism failure
    'city agnostic': ('schema',),
    'fit figures': ('fit figures',),
}


def fix(quick=False):
    """Regenerate every stale GENERATED artefact, then re-run the gates.

    This is the sequence a session otherwise types by hand every time a run
    finishes or a registry field is added, and typing it by hand is how a
    session starts by rediscovering which script rebuilds which file. It never
    edits prose and never silences a defect - a gate that reports one is listed
    afterwards as needing a person.
    """
    print('=' * 78)
    print('GATE --fix: regenerating what is stale, then re-checking')
    print('=' * 78)
    before = gates(quick=quick, quiet_header=True)
    stale = [g for g in before if g in FIXES_FOR]
    if not before:
        print('\nnothing to fix: every gate already passes.')
        return 0
    if not stale:
        print('\nno failing gate is a stale generated artefact; nothing to '
              'regenerate.')
    else:
        wanted, seen = [], set()
        for g in stale:
            for name in FIXES_FOR[g]:
                if name not in seen:
                    seen.add(name)
                    wanted.append(name)
        print('\nregenerating for: %s' % ', '.join(stale))
        for label, cmd, why in FIXES:
            if label not in seen:
                continue
            rc, out = _run(cmd, 900)
            tail = [l for l in out.strip().splitlines() if l.strip()][-2:]
            print('  %-18s %s  (%s)' % (label, 'ok' if rc == 0 else 'FAILED rc=%s' % rc, why))
            for l in tail:
                print('      ' + l[:150])
        print('\n' + '=' * 78)
        print('RE-CHECKING')
        print('=' * 78)
    after = gates(quick=quick, quiet_header=True)
    fixed = [g for g in before if g not in after]
    if fixed:
        print('\nfixed by regeneration: %s' % ', '.join(fixed))
    # "needs a person" is what is STILL failing - never what failed before and
    # then passed. Reporting a gate as both fixed and needing attention is a
    # tool contradicting itself, which is the thing this mode exists to stop.
    if after:
        print('\nSTILL FAILING - each of these is a defect a person fixes, not '
              'a stale file: %s' % ', '.join(after))
        return 1
    print('\nGATE PASSED after regeneration.')
    return 0


def gates(quick=False, quiet_header=False):
    busy = arm_running()
    # UNKNOWN COUNTS AS BUSY. arm_running() returns None when it could not list
    # processes at all - the one case where we do not know whether an arm is up.
    # Treating that as idle ran the toolchain compile, which rewrites
    # .tools/classes under a running arm: the single thing the rule above this
    # forbids. A skipped gate is recoverable; a recompiled class tree under a
    # 22-hour arm is not.
    unknown = busy is None
    failed = []
    for label, cmd, needs_toolchain in GATES:
        if needs_toolchain and (quick or busy or unknown):
            why = ('an arm is running - never recompile .tools/classes under it' if busy
                   else 'could not tell whether an arm is running - treating as busy'
                   if unknown else '--quick')
            print('  %-18s SKIPPED  (%s)' % (label, why))
            continue
        rc, out = _run(cmd, 900)      # fifteen minutes: the toolchain compile is the slowest gate
        if rc == 0:
            print('  %-18s PASS' % label)
        else:
            failed.append(label)
            tail = [l for l in out.strip().splitlines() if l.strip()][-4:]
            print('  %-18s FAIL  rc=%s' % (label, rc))
            for l in tail:
                print('      ' + l[:160])
    print()
    if failed:
        print('GATE FAILED: %s - a failing gate is the session\'s first work item.'
              % ', '.join(failed))
        if not quiet_header:
            print('  `--fix` regenerates any of these that is a stale GENERATED '
                  'artefact and re-checks; it never edits prose.')
    else:
        print('GATE PASSED. (tests/check_package.py is LOCAL and separate: run it on a '
              'workstation before declaring a data phase complete.)')
    return failed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--digest', action='store_true', help='print the session digest only')
    ap.add_argument('--quick', action='store_true',
                    help='skip the toolchain compile')
    ap.add_argument('--fix', action='store_true',
                    help='regenerate every stale GENERATED artefact (run '
                         'index, config reference, schema, fit figures, board '
                         'blocks) and re-check. Never edits prose and never '
                         'silences a defect.')
    ap.add_argument('--handoff', action='store_true',
                    help='the close-out checks on top of the gates: every '
                         'completed run has its findings under processed/, '
                         'every brief section-0 row carries its command, the '
                         'position pages touched today carry today\'s stamp')
    a = ap.parse_args()
    if a.digest:
        digest()
        return 0
    if a.fix:
        return fix(quick=a.quick)
    failed = gates(quick=a.quick)
    if a.handoff:
        failed += handoff_checks()
    return 1 if failed else 0


def handoff_checks():
    """What only a close-out can get wrong (9.171). Each is one line, like a gate."""
    import datetime as _dt
    import json
    import re
    failed = []
    print('-- handoff --')
    # 1. a completed run's findings live in processed/, not only in the raw cache
    #    (the tenth report: arm 0's _fit.json existed only in raw/ and one trim
    #    would have deleted the second result)
    #    An ARM, not a probe: the run index classes every directory, and a
    #    probe is read for a clock or a yes/no, never for a fit.
    missing = []
    index = os.path.join(ROOT, 'results', 'INDEX.csv')
    if os.path.exists(index):
        import csv
        with open(index, encoding='utf-8', newline='') as fh:
            for row in csv.DictReader(fh):
                if row.get('class') != 'arm' or row.get('status') != 'completed':
                    continue
                name = row.get('name', '')
                rec = os.path.join(ROOT, 'results', 'raw', name, '_run.json')
                try:
                    done = json.load(open(rec, encoding='utf-8')).get('completion') == 'ran_to_last_iteration'
                except Exception:                              # noqa: BLE001
                    done = False
                if done and not os.path.exists(os.path.join(ROOT, 'results', 'processed', name, '_fit.json')):
                    missing.append(name)
    _line('results processed', not missing, 'no _fit.json under processed/ for: ' + ', '.join(missing), failed)
    # 2. every expiring fact in the brief's section 0 carries the command that re-derives it
    brief = _city.docs('NEXT_AGENT_BRIEF.md')
    rows_without = []
    if os.path.exists(brief):
        in_s0 = False
        for l in open(brief, encoding='utf-8').read().splitlines():
            if l.startswith('## '):
                in_s0 = l.startswith('## §0')
                continue
            if in_s0 and l.startswith('|') and not l.startswith('|---') and 'Re-derive with' not in l:
                cells = [c.strip() for c in l.strip('|').split('|')]
                if len(cells) >= 2 and '`' not in cells[1]:
                    rows_without.append(cells[0][:50])
    _line('brief §0 commands', not rows_without, 'rows with no command: ' + ' / '.join(rows_without), failed)
    # 3. a position page changed today is stamped today
    today = _dt.date.today()
    stale = []
    try:
        rc, out = _run(['git', 'diff', '--name-only', 'origin/main...HEAD', '--', 'docs/positions'], 60)
        rc2, out2 = _run(['git', 'status', '--porcelain', '--', 'docs/positions'], 60)
        changed = set(out.split()) | {l[3:].strip() for l in out2.splitlines() if l.strip()}
    except Exception:                                          # noqa: BLE001
        changed = set()
    for rel in sorted(changed):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        text = open(p, encoding='utf-8').read()
        m = re.search(r'\*\*Updated:\*\*\s*(\d{1,2} \w+ \d{4})', text)
        try:
            stamped = _dt.datetime.strptime(m.group(1), '%d %B %Y').date() if m else None
        except ValueError:
            stamped = None
        if stamped != today:
            stale.append(os.path.basename(rel))
    _line('positions stamped', not stale, 'changed but not stamped today: ' + ', '.join(stale), failed)
    print()
    if failed:
        print('HANDOFF CHECKS FAILED: %s' % ', '.join(failed))
    else:
        print('HANDOFF CHECKS PASSED.')
    return failed


def _line(label, ok, why, failed):
    if ok:
        print('  %-18s PASS' % label)
    else:
        failed.append(label)
        print('  %-18s FAIL  %s' % (label, why[:150]))


if __name__ == '__main__':
    sys.exit(main())
