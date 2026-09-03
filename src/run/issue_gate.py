#!/usr/bin/env python
"""No open issue behind a run (GOAL.md requirement 10).

Before the simulator is tuned or tested - before any arm is launched - every
GitHub issue must be either closed or labelled ``awaiting-run``: the label
says the only thing left on it is a measurement the run itself makes. An
issue that can be fixed without a run is fixed first. This module asks
GitHub through the ``gh`` CLI and refuses when an open issue carries no
``awaiting-run`` label.

Used by ``src/run/session_gate.py`` (one gate line) and by ``run.py`` before
a launch. It names no city and no issue: the rule is the framework's, the
issues are whatever the repository's tracker holds. Where ``gh`` is not
installed or not authenticated the gate cannot see the tracker and says so
rather than pretending the tracker is empty - a launch then needs the
explicit override, which is recorded in the run's own record.
"""
import json
import os
import shutil
import subprocess
import sys

LABEL = 'awaiting-run'


def open_issues():
    """(status, issues): status is 'ok', 'no-gh' or 'error'; issues is the
    list of open issues as dicts with number, title and labels."""
    gh = shutil.which('gh')
    if not gh:
        return 'no-gh', []
    try:
        out = subprocess.run(
            [gh, 'issue', 'list', '--state', 'open', '--limit', '500',
             '--json', 'number,title,labels'],
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))))
    except (OSError, subprocess.SubprocessError):
        return 'error', []
    if out.returncode != 0:
        return 'error', []
    try:
        issues = json.loads(out.stdout or '[]')
    except ValueError:
        return 'error', []
    return 'ok', [dict(number=i['number'], title=i['title'],
                       labels=sorted(l['name'] for l in i.get('labels', [])))
                  for i in issues]


def blocking(issues):
    """The open issues that are not labelled awaiting-run."""
    return [i for i in issues if LABEL not in i['labels']]


def check(verbose=True):
    """0 when every open issue is closed or awaiting a run; 1 when one is
    not; 2 when the tracker could not be read."""
    status, issues = open_issues()
    if status != 'ok':
        if verbose:
            print('issue gate: cannot read the tracker (%s) - install and '
                  'authenticate the gh CLI, then re-run' % (
                      'gh CLI not installed' if status == 'no-gh'
                      else 'gh issue list failed'))
        return 2
    bad = blocking(issues)
    if verbose:
        print('issue gate: %d open issue(s), %d awaiting a run, %d blocking'
              % (len(issues), len(issues) - len(bad), len(bad)))
        for i in bad:
            print('  #%-4d %s   [%s]' % (i['number'], i['title'][:90],
                                         ', '.join(i['labels']) or 'no label'))
        if bad:
            print('  GOAL.md requirement 10: fix these without a run, or '
                  'label them %s when only a run can move them.' % LABEL)
    return 1 if bad else 0


def refuse_launch(allow_open_issues=False):
    """Called by the launcher. Returns None to proceed, else the reason to
    refuse. With the override, returns None but prints what was overridden."""
    status, issues = open_issues()
    if status != 'ok':
        msg = ('the issue tracker could not be read (%s), so GOAL.md '
               'requirement 10 cannot be verified' % (
                   'gh CLI not installed' if status == 'no-gh'
                   else 'gh issue list failed'))
        if allow_open_issues:
            print('issue gate OVERRIDDEN: ' + msg, flush=True)
            return None
        return msg + '; pass --allow-open-issues to launch regardless'
    bad = blocking(issues)
    if not bad:
        return None
    lines = ['#%d %s' % (i['number'], i['title'][:80]) for i in bad]
    if allow_open_issues:
        print('issue gate OVERRIDDEN: %d open issue(s) not awaiting a run: %s'
              % (len(bad), '; '.join(lines)), flush=True)
        return None
    return ('%d open issue(s) are neither closed nor labelled %s (GOAL.md '
            'requirement 10): %s. Fix them first, or pass --allow-open-issues '
            'and say why in the run record.'
            % (len(bad), LABEL, '; '.join(lines)))


if __name__ == '__main__':
    sys.exit(check())
