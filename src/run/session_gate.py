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
sys.path.insert(0, os.path.join(ROOT, 'src'))
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


def arm_running():
    """A MATSim arm is up when a java process holds more than ~2 GB.

    VS Code's own java (the language server) sits under 1 GB; an arm sits in
    the tens of GB. The threshold is a classifier, not a model value.
    """
    if os.name == 'nt':
        rc, out = _run(['tasklist', '/FI', 'IMAGENAME eq java.exe', '/FO', 'CSV'], 30)
        if rc != 0:
            return None
        big = []
        for line in out.splitlines()[1:]:
            cells = [c.strip('"') for c in line.split('","')]
            if len(cells) >= 5:
                kb = int(re.sub(r'[^\d]', '', cells[4]) or 0)
                if kb > 2_000_000:
                    big.append('pid %s (%d MB)' % (cells[1], kb // 1024))
        return big
    rc, out = _run(['ps', '-eo', 'pid,rss,comm'], 30)
    if rc != 0:
        return None
    return ['pid %s (%d MB)' % (l.split()[0], int(l.split()[1]) // 1024)
            for l in out.splitlines()[1:]
            if 'java' in l and int(l.split()[1]) > 2_000_000]


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
    path = _city.path('docs', 'STATUS.md')
    if not os.path.exists(path):
        return {}
    text = open(path, encoding='utf-8').read()
    return dict(re.findall(r'<!-- generated:(\w+) start -->\n(.*?)<!-- generated:\1 end -->',
                           text, re.S))


def digest():
    goal = _city.path('docs', 'GOAL.md')
    print('=' * 78)
    print('SESSION DIGEST - city %s' % _city.CITY)
    print('=' * 78)
    if os.path.exists(goal):
        first = [l for l in open(goal, encoding='utf-8').read().splitlines()
                 if l.startswith('# ')]
        print('GOAL  %s' % (first[0][2:] if first else goal))
        print('      read it: %s' % os.path.relpath(goal, ROOT))
    else:
        print('GOAL  no GOAL.md under the city docs - write one before anything else')
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
    print('=' * 78)


GATES = [
    # (label, command, needs_toolchain)
    ('manifest', [PY, 'tests/check_manifest.py'], False),
    ('compile', [PY, '-m', 'compileall', '-q', 'src', 'tests'], False),
    ('hardcoding', [PY, 'src/registry/check_hardcoding.py', '--strict'], False),
    ('doc currency', [PY, 'tests/check_doc_currency.py', '--strict'], False),
    ('doc shape', [PY, 'tests/check_doc_shape.py', '--strict'], False),
    ('board blocks', [PY, 'src/analyse/build_status_board.py', '--check'], False),
    ('city contract', [PY, 'src/registry/check_city.py', '--all'], False),
    ('schema current', [PY, 'src/registry/render_schema.py', '--check'], False),
    ('city agnostic', [PY, 'tests/check_city_agnostic.py'], False),
    ('dead runs say why', [PY, 'src/run/run_failure.py', '--check'], False),
    ('gate watcher', [PY, 'tests/check_gate_watcher.py'], False),
    ('launch refusal', [PY, 'tests/check_launch_refusal.py'], False),
    ('registry rules', [PY, 'tests/check_registry_rules.py'], False),
    # 9.154: what the FRAMEWORK is deciding in the modules the model writes
    # into. Runs WITHOUT --strict deliberately: 31 of MATSim's own defaults are
    # still unreviewed, so strict would block every session on a backlog rather
    # than on a regression. The line reports the count each session; it becomes
    # a gate when the backlog is worked down, exactly as check_hardcoding did.
    ('matsim defaults', [PY, 'src/registry/check_matsim_defaults.py'], False),
    # #133: the functions that decide correctness, on synthetic inputs
    ('unit tests', [PY, '-m', 'pytest', '-q', 'tests/unit'], False),
    ('fit figures', [PY, 'src/analyse/build_fit_figures.py', '--check'], False),
    # GOAL.md requirement 10: every open issue closed or awaiting a run
    ('issues gated', [PY, 'src/run/issue_gate.py'], False),
    ('toolchain', [PY, 'src/setup/bootstrap_toolchain.py', '--verify'], True),
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
    a = ap.parse_args()
    if a.digest:
        digest()
        return 0
    if a.fix:
        return fix(quick=a.quick)
    return 1 if gates(quick=a.quick) else 0


if __name__ == '__main__':
    sys.exit(main())
