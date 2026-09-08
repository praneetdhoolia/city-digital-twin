#!/usr/bin/env python
"""No open issue behind a run (GOAL.md requirement 10).

Before the simulator is tuned or tested - before any arm is launched - every
GitHub issue must be either closed or **awaiting a run**: the only thing left
on it is a measurement the run itself makes. An issue that can be fixed
without a run is fixed first. This module asks GitHub through the ``gh`` CLI
and refuses a launch while an issue in the run's lane is neither.

Used by ``src/run/session_gate.py`` (one gate line) and by ``run.py`` before a
launch. It names no city and no issue: the rule is the framework's, the issues
are whatever the repository's tracker holds, the lane is whatever the run's own
committed overlay declares.

**A label is not evidence, and the first version of this gate tested only a
label.** ``awaiting-run`` was a string anyone could attach, so requirement 10
was satisfiable for ever by labelling: two of the eighteen open issues on
8 September 2026 were product directions ("Align modelled mode distributions
with demographics", "Individualise modes") that no single run settles, and both
carried the label. Meanwhile a measured defect - PT walk legs teleported,
70.9 % of 1,978 teleported walk legs on a 1 % run ending at a ``pt
interaction`` - was deliberately LEFT UNFILED, because filing it would have
turned the launcher red. **A gate that makes filing a defect costly is
selecting against being told.** So this gate now asks for three things instead
of one:

  EVIDENCE   an issue claiming the label states the measurement it waits on,
             in the repository's own wording - a line reading
             ``AWAITING-RUN: <the measurement that would settle this>``
             (case-insensitive, so the existing prose "Labelled awaiting-run:
             the next gate reads heavy rail on the F24 package" counts) in the
             issue body or any comment, carrying at least
             ``MIN_EVIDENCE_CHARS`` of statement. What the gate can check is
             that a measurement was NAMED; whether it is the right one is a
             reader's judgement, and this file does not pretend otherwise.

  LANE       an arm is blocked by the issues it is meant to settle, not by
             every issue in the tracker. A run's lane is DECLARED by its run
             overlay - the committed ``cities/<city>/overlays/runs/<name>.json``
             whose description names the issues the arm answers (the F29
             overlay's clause (g) is the established form). **Nothing else in
             this repository identifies a run's lane**: neither ``_run.json``,
             nor ``run_families.json``, nor any issue label carries a topic,
             and the phase label (``P4``) is on every open issue at once. So the
             lane is read from the one artefact that states it, and when an
             overlay declares none the gate falls back to the WHOLE open set -
             the strict behaviour, unchanged. Narrowing a lane is therefore a
             visible edit to a committed file, never a silent bypass, and the
             out-of-lane blockers are still printed at every launch.

  OVERRIDE   ``--allow-open-issues`` is a first-class, COUNTED act. It needs a
             stated reason (without one the launch is still refused), it is
             appended to an override ledger beside the run records, and its
             running total is printed by this gate every session. It was used
             once, deliberately, on 8 September 2026; a bypass nobody counts is
             a bypass that becomes the habit.

Where ``gh`` is not installed or not authenticated the gate cannot see the
tracker and says so rather than pretending the tracker is empty - a launch then
needs the same explicit, reasoned override.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for _p in (os.path.join(REPO, 'src'), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

LABEL = 'awaiting-run'

# The measurement statement. Case-insensitive so the repository's existing
# prose form ("Labelled awaiting-run: the next arm's gate reads ...") is
# evidence exactly as the structured "AWAITING-RUN: ..." form is - a convention
# already in use is not broken to make a check easier to write.
# NOTE the absence of a backtick in the allowed-prefix class, and it is
# deliberate: `AWAITING-RUN:` inside a code span is how this repository REFERS
# to the convention, not how it invokes it. Allowing it made the gate green on
# three issues whose own text said "writing an `AWAITING-RUN:` line on it would
# be inventing a measurement to turn the gate green" - the check was satisfied
# by the sentence explaining why it should not be. The prose form the class
# exists to protect ("Labelled awaiting-run: the next arm's gate reads ...") is
# preceded by a space and still matches.
EVIDENCE = re.compile(r'(?:^|[\s*_(\[>-])awaiting[ -]run\s*:[ \t]*(\S.*)',
                      re.IGNORECASE | re.MULTILINE)
# How much statement counts as a statement. A bare "awaiting-run:" with nothing
# after it is the label again under another name.
MIN_EVIDENCE_CHARS = 40

# Two statements that clear MIN_EVIDENCE_CHARS and are still not measurements.
# Both were measured green at 781cf41 while the issues carrying them said in
# terms that they block the launcher, so the length rule alone is not enough.
#
# TEMPLATE: the gate's own documentation matches the gate's own regex. A comment
# reading `requires an "AWAITING-RUN: <measurement>" line with real content`
# captures "<measurement>" plus the rest of the sentence. A statement that opens
# with a <placeholder> is the template, not an instance of it.
TEMPLATE_EVIDENCE = re.compile(r'^<[^>]{0,80}>')
# NOTHING: "AWAITING-RUN: nothing. **This issue does not await a run** - it
# awaits an operator decision / a content pass / a mechanism." The issue is
# telling the truth; an issue whose stated measurement is "nothing" is not
# awaiting a run, and requirement 10 is about issues that ARE.
NOTHING_EVIDENCE = re.compile(r'^nothing\b', re.IGNORECASE)


def _is_a_measurement(stated):
    """Whether a captured statement states something a run could measure."""
    if len(stated) < MIN_EVIDENCE_CHARS:
        return False
    if TEMPLATE_EVIDENCE.match(stated):
        return False
    if NOTHING_EVIDENCE.match(stated):
        return False
    return True

# THE THIRD STATE. An issue that awaits a DECISION, an ACQUISITION or a
# MECHANISM is not awaiting a run, and requirement 10 is about the ones that
# are. Before this existed the rule was binary and four open issues were
# neither: the only ways to go green were to invent a measurement, which is the
# failure the evidence check exists to stop, or to strip the label and make the
# issue invisible to the launcher again. A declared one is REPORTED at every
# gate and every launch - never silently ignored - and does not block.
# Reusing the vocabulary this tracker already has rather than adding a
# near-duplicate: `decision-needed` is a call somebody has to make,
# `awaiting-implementation` is a call already made whose work is not
# built. Both are 'not a run', and neither carried any evidence
# discipline before this - no open issue used either.
DECISION_LABELS = ('decision-needed', 'awaiting-implementation')
DECISION_EVIDENCE = re.compile(
    r'(?:^|[\s*_(\[>-])awaiting[ -]decision\s*:[ \t]*(\S.*)',
    re.IGNORECASE | re.MULTILINE)


def decision_evidence(issue):
    """What an issue says it awaits, when what it awaits is not a run.

    Same discipline as `evidence()`: a label anyone can attach is not a
    statement, the LAST statement is the current one, and a <placeholder> or
    the word "nothing" is not a statement at all.
    """
    latest = None
    for text in [issue.get('body', '')] + list(issue.get('comments', [])):
        for match in DECISION_EVIDENCE.finditer(text or ''):
            latest = match.group(1).strip().strip('*_`').strip()
    if latest is not None and _is_a_measurement(latest):
        return latest
    return None


def awaiting_decision(issues):
    """Open issues that declare they await something other than a run."""
    return [dict(i, awaits=decision_evidence(i)) for i in issues
            if _declares_not_a_run(i) and decision_evidence(i)]


def _declares_not_a_run(issue):
    return any(l in issue['labels'] for l in DECISION_LABELS)


# An issue reference inside a run overlay's declaration of what the arm answers.
LANE_REF = re.compile(r'#(\d+)')

# The override ledger: one JSON list beside the run records, appended to and
# never rewritten. `results/processed/` is the half of the store that is kept
# for ever (DECISIONS.md 9.137), and `_trim_log.json` already lives at its root.
OVERRIDE_LEDGER = '_issue_gate_overrides.json'


# ------------------------------------------------------------------ the tracker

def open_issues():
    """(status, issues): status is 'ok', 'no-gh' or 'error'; issues is the
    list of open issues as dicts with number, title, labels, body and
    comments."""
    gh = shutil.which('gh')
    if not gh:
        return 'no-gh', []
    try:
        out = subprocess.run(
            [gh, 'issue', 'list', '--state', 'open', '--limit', '500',
             '--json', 'number,title,labels,body,comments'],
            capture_output=True, text=True, timeout=120, cwd=REPO)
    except (OSError, subprocess.SubprocessError):
        return 'error', []
    if out.returncode != 0:
        return 'error', []
    try:
        issues = json.loads(out.stdout or '[]')
    except ValueError:
        return 'error', []
    return 'ok', [dict(number=i['number'], title=i['title'],
                       labels=sorted(l['name'] for l in i.get('labels', [])),
                       body=i.get('body') or '',
                       comments=[(c.get('body') or '')
                                 for c in (i.get('comments') or [])])
                  for i in issues]


def evidence(issue):
    """The measurement an issue says it is waiting on, else None.

    Read from the issue body and every comment, so an issue that was labelled
    first and explained afterwards is evidenced by the explanation.
    """
    latest = None
    for text in [issue.get('body', '')] + list(issue.get('comments', [])):
        for match in EVIDENCE.finditer(text or ''):
            # the LAST statement wins, not the first. Comments are
            # chronological, so an issue that stated a measurement, had it
            # measured, and then said it now awaits a mechanism is not still
            # awaiting the measurement it already has.
            latest = match.group(1).strip().strip('*_`').strip()
    if latest is not None and _is_a_measurement(latest):
        return latest
    return None


# --------------------------------------------------------------------- the lane

def lane(run_config):
    """The issue numbers a run's own overlay declares it will settle, or None.

    None means the overlay declares no lane - there is nothing to scope by, so
    every open issue is in scope. The overlay is resolved through `src/city.py`,
    the one module that knows where a city lives.
    """
    if not run_config:
        return None
    try:
        import city as city_module  # noqa: PLC0415
        overlay = os.path.join(city_module.CITY_DIR, 'overlays', 'runs',
                               '%s.json' % run_config)
    except Exception:
        return None
    if not os.path.isfile(overlay):
        return None
    try:
        with io.open(overlay, encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    # DECLARED beats scraped. An overlay that names its lane is read exactly;
    # nothing else in the file can widen or narrow it, and a description is
    # then free to explain why an issue is NOT in the lane without putting it
    # back in - which is what prose scraping did when the depth arm's
    # description was corrected to exclude #167.
    declared_lane = doc.get('answers_issues')
    if isinstance(declared_lane, list) and declared_lane:
        return set(int(n) for n in declared_lane)

    # Fallback for the overlays that declare nothing, and it is a WEAK one:
    # `#(\d+)` over free prose cannot tell a claim from a mention. Measured on
    # `default_25pct.json`, what a bare `python run.py` selects, it yields the
    # lane {5} from the sentence "issue #5 re-measures relaxation" and defers
    # every other open issue. Say so rather than scope silently.
    declared = ' '.join(str(doc.get(k, '')) for k in ('overlay', 'description'))
    numbers = set(int(n) for n in LANE_REF.findall(declared))
    if numbers:
        sys.stderr.write(
            'issue gate: %s declares no `answers_issues`, so its lane is '
            'SCRAPED from its prose and reads %s. A scraped lane cannot tell a '
            'claim from a mention - declare the lane on the overlay.\n'
            % (run_config, sorted(numbers)))
    return numbers or None


def blocking(issues, in_lane=None):
    """The open issues that stand between this repository and a launch.

    An issue blocks when it carries no `awaiting-run` label, or carries the
    label without stating the measurement it waits on. `in_lane`, when given,
    is the set of issue numbers the run declares it answers; issues outside it
    are deferred rather than blocking, and `deferred()` reports them.
    """
    out = []
    for i in issues:
        why = _why_blocking(i)
        if why is None:
            continue
        if in_lane is not None and i['number'] not in in_lane:
            continue
        out.append(dict(i, why=why))
    return out


def deferred(issues, in_lane):
    """Issues that would block but sit outside the run's declared lane."""
    if in_lane is None:
        return []
    return [dict(i, why=_why_blocking(i)) for i in issues
            if _why_blocking(i) is not None and i['number'] not in in_lane]


def _why_blocking(issue):
    # An issue that DECLARES it awaits something other than a run, and says
    # what, is reported rather than blocking. The declaration is checked, not
    # taken on the label alone.
    if _declares_not_a_run(issue):
        if decision_evidence(issue):
            return None
        return ('labelled %s but does not say what it awaits - add a line '
                '"AWAITING-DECISION: " naming the decision, the acquisition '
                'or the mechanism, and who takes it'
                % '/'.join(l for l in DECISION_LABELS if l in issue['labels']))
    if LABEL not in issue['labels']:
        return 'not labelled %s, and not labelled %s either' % (
            LABEL, ' or '.join(DECISION_LABELS))
    if evidence(issue) is None:
        return ('labelled %s but states no measurement a run could make - add '
                'a line "AWAITING-RUN: " naming the observable and where it is '
                'read. A <placeholder> and the word "nothing" are both refused: '
                'an issue that awaits a decision, an acquisition or a mechanism '
                'is not awaiting a run, and requirement 10 is about the ones '
                'that are' % LABEL)
    return None


# ----------------------------------------------------------------- the override

def _ledger_path():
    try:
        import results_store  # noqa: PLC0415
        root = results_store.PROCESSED
    except Exception:
        root = os.path.join(REPO, 'results', 'processed')
    return os.path.join(root, OVERRIDE_LEDGER)


def override_log():
    """Every recorded override, oldest first. An empty list when none."""
    path = _ledger_path()
    if not os.path.isfile(path):
        return []
    try:
        with io.open(path, encoding='utf-8') as fh:
            entries = json.load(fh)
    except (OSError, ValueError):
        return []
    return entries if isinstance(entries, list) else []


def record_override(reason, overridden, run_config=None):
    """Append one override to the ledger and return its number in the series.

    Append-only: a bypass of a hard requirement is a decision, and a decision
    that is not counted is a decision nobody can audit later.
    """
    entries = override_log()
    entry = {
        'n': len(entries) + 1,
        'when': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'run_config': run_config,
        'reason': reason,
        'issues': [{'number': i['number'], 'title': i['title'],
                    'why': i.get('why', '')} for i in overridden],
    }
    entries.append(entry)
    path = _ledger_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(entries, fh, indent=2, ensure_ascii=False)
            fh.write('\n')
    except OSError as exc:
        print('issue gate: the override could NOT be recorded (%s) - it is '
              'still the operator\'s to write into the run record' % exc,
              flush=True)
    return entry['n']


# ------------------------------------------------------------------- the checks

def check(verbose=True, run_config=None):
    """0 when nothing blocks, 1 when something does, 2 when the tracker could
    not be read."""
    status, issues = open_issues()
    if status != 'ok':
        if verbose:
            print('issue gate: cannot read the tracker (%s) - install and '
                  'authenticate the gh CLI, then re-run' % (
                      'gh CLI not installed' if status == 'no-gh'
                      else 'gh issue list failed'))
        return 2
    in_lane = lane(run_config)
    bad = blocking(issues, in_lane)
    later = deferred(issues, in_lane)
    if verbose:
        scope = ('the whole open set' if in_lane is None
                 else '%d issue(s) the %s overlay declares'
                      % (len(in_lane), run_config))
        evidenced = sum(1 for i in issues
                        if LABEL in i['labels'] and evidence(i) is not None)
        decisions = awaiting_decision(issues)
        print('issue gate: %d open issue(s), %d awaiting a run WITH a stated '
              'measurement, %d awaiting a decision, %d blocking (scope: %s)'
              % (len(issues), evidenced, len(decisions), len(bad), scope))
        for i in bad:
            print('  #%-4d %s' % (i['number'], i['title'][:88]))
            print('        %s' % i['why'])
        for i in later:
            print('  #%-4d %s   [deferred: outside this run\'s lane]'
                  % (i['number'], i['title'][:70]))
        # Always printed, in or out of lane, blocking or not: the point of the
        # third state is that it is visible, not that it is quiet.
        for i in awaiting_decision(issues):
            print('  #%-4d %s   [awaits a decision, not a run]'
                  % (i['number'], i['title'][:70]))
            print('        %s' % (i['awaits'] or '')[:150])
        if bad:
            print('  GOAL.md requirement 10: fix these without a run, or say '
                  'on the issue what only a run can settle -')
            print('  a line "AWAITING-RUN: <the measurement>" beside the %s '
                  'label - or, if what it awaits is a decision, an acquisition '
                  'or a mechanism rather than a run, the %s label and a line '
                  '"AWAITING-DECISION: <what, and who takes it>".'
                  % (LABEL, ' or '.join(DECISION_LABELS)))
        overrides = override_log()
        if overrides:
            last = overrides[-1]
            print('  overrides recorded: %d (last %s, %s)'
                  % (len(overrides), last.get('when', '?'),
                     (last.get('reason') or '')[:70]))
    return 1 if bad else 0


def refuse_launch(allow_open_issues=False, reason=None, run_config=None):
    """Called by the launcher. Returns None to proceed, else the reason to
    refuse. The override needs a stated reason of its own and is counted."""
    status, issues = open_issues()
    if status != 'ok':
        msg = ('the issue tracker could not be read (%s), so GOAL.md '
               'requirement 10 cannot be verified' % (
                   'gh CLI not installed' if status == 'no-gh'
                   else 'gh issue list failed'))
        if allow_open_issues:
            stated = (reason or '').strip()
            if not stated:
                return _needs_reason(msg)
            n = record_override(stated, [], run_config)
            print('issue gate OVERRIDDEN (override %d in this repository\'s '
                  'history): %s\n  reason: %s' % (n, msg, stated), flush=True)
            return None
        return msg + '; pass --allow-open-issues with --override-reason to ' \
                     'launch regardless'

    in_lane = lane(run_config)
    bad = blocking(issues, in_lane)
    for i in deferred(issues, in_lane):
        print('issue gate: #%d is open and not awaiting a run, but sits '
              'outside the lane the %s overlay declares - it does not block '
              'this arm and it is not closed either'
              % (i['number'], run_config), flush=True)
    if not bad:
        return None
    lines = ['#%d %s (%s)' % (i['number'], i['title'][:70], i['why'])
             for i in bad]
    if allow_open_issues:
        stated = (reason or '').strip()
        if not stated:
            return _needs_reason(
                '%d open issue(s) in this run\'s lane are neither closed nor '
                'awaiting a stated measurement: %s' % (len(bad), '; '.join(lines)))
        n = record_override(stated, bad, run_config)
        print('issue gate OVERRIDDEN (override %d in this repository\'s '
              'history): %d open issue(s) not awaiting a run: %s\n  reason: %s'
              % (n, len(bad), '; '.join(lines), stated), flush=True)
        return None
    return ('%d open issue(s) in this run\'s lane are neither closed nor '
            'labelled %s with a stated measurement (GOAL.md requirement 10): '
            '%s. Fix them first, state on each what only a run can settle '
            '("AWAITING-RUN: <the measurement>"), or pass --allow-open-issues '
            'with --override-reason and repeat that reason in the run record.'
            % (len(bad), LABEL, '; '.join(lines)))


def _needs_reason(msg):
    return (msg + '. --allow-open-issues needs --override-reason "<why this '
            'arm launches anyway>": the override is recorded and counted, not '
            'an ad-hoc bypass.')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--overrides' in argv:
        entries = override_log()
        print('issue gate: %d override(s) recorded' % len(entries))
        for e in entries:
            print('  %-3d %s  run-config %s' % (e.get('n', 0),
                                                e.get('when', '?'),
                                                e.get('run_config') or '-'))
            print('      %s' % (e.get('reason') or ''))
            for i in e.get('issues', []):
                print('      overrode #%s %s' % (i.get('number'),
                                                 (i.get('title') or '')[:70]))
        return 0
    run_config = None
    if '--run-config' in argv:
        idx = argv.index('--run-config')
        if idx + 1 < len(argv):
            run_config = argv[idx + 1]
    return check(run_config=run_config)


if __name__ == '__main__':
    sys.exit(main())
