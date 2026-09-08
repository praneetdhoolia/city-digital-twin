"""The issue gate must not be satisfied by prose describing the issue gate.

Measured at `781cf41`: the unscoped gate read *"20 open, every one awaiting a
stated measurement, 0 blocking"* while three of those issues opened with the
line **"This issue BLOCKS the launcher"** and said in terms that they state no
measurement. Replaying `evidence()` over their text showed why - three separate
ways for a sentence about the check to satisfy the check:

1. **A mention inside a code span read as a use.** The allowed-prefix class
   contained a backtick, so ``Writing an `AWAITING-RUN:` line on it would be
   inventing a measurement to turn the gate green`` matched, and the captured
   statement was *"line on it would be inventing a measurement..."* - the gate
   was green because the issue had explained why it should not be.
2. **The template read as an instance.** ``requires an `AWAITING-RUN:
   <measurement>` line with real content`` captured the literal placeholder
   plus the rest of the sentence, comfortably past `MIN_EVIDENCE_CHARS`.
3. **A superseded statement outliving its own supersession.** `evidence()`
   returned the FIRST match over body-then-comments, so an issue that stated a
   measurement, had it measured, and then wrote *"AWAITING-RUN: nothing further
   from a 25 % arm - what this needs next is a mechanism"* kept answering with
   the statement it had already discharged.

Each is pinned below, because each was green and none was visible: the gate's
own output said the opposite of what its inputs said.
"""
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (os.path.join(REPO, 'src'), os.path.join(REPO, 'src', 'run')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import issue_gate  # noqa: E402


def _issue(number=1, body='', comments=(), labels=('awaiting-run',)):
    return {'number': number, 'title': 't', 'labels': list(labels),
            'body': body, 'comments': list(comments)}


# --------------------------------------------------------------- 1. mentions

MENTION_BODY = (
    'This issue BLOCKS the launcher, and it should not be closed by a session.\n'
    '\n'
    'Writing an `AWAITING-RUN:` line on it would be inventing a measurement to '
    'turn the gate green, which is exactly the defect the evidence check was '
    'built to stop.\n')

TEMPLATE_BODY = (
    '`src/run/issue_gate.py` now requires an `AWAITING-RUN: <measurement>` line '
    'with real content rather than a bare label, because a label anyone could '
    'attach made GOAL requirement 10 satisfiable for ever by labelling.\n')


@pytest.mark.parametrize('body,why', [
    (MENTION_BODY, 'a backticked mention is not an invocation'),
    (TEMPLATE_BODY, 'the template is not an instance of itself'),
])
def test_prose_about_the_gate_is_not_evidence(body, why):
    assert issue_gate.evidence(_issue(body=body)) is None, why
    assert issue_gate._why_blocking(_issue(body=body)) is not None, why


def test_the_prose_form_the_repository_actually_uses_still_counts():
    """The class exists to admit this form; narrowing it must not break it."""
    body = ("Labelled awaiting-run: the next arm's gate reads the near-wharf "
            "market split and the ferry plan's survival in memory.")
    assert issue_gate.evidence(_issue(body=body)) is not None


# ---------------------------------------------------------- 2. non-statements

@pytest.mark.parametrize('stated,ok', [
    ('<measurement>` line with real content rather than a bare label, because', False),
    ('<the measurement that would settle this> - a placeholder, not a reading', False),
    ('nothing. **This issue does not await a run** - it awaits an operator '
     'decision plus ~70 minutes of extract_snapshots on an idle machine', False),
    ('nothing further from a 25 % arm. What this issue needs next is a '
     'mechanism for the last hop onto a platform, then probe 1 re-run', False),
    ('short', False),
    ("the declared-bound-trip funnel at the next arm's iteration-100 gate - "
     "bound trips declared, surviving into plan memory, and selected", True),
])
def test_what_counts_as_a_measurement(stated, ok):
    assert issue_gate._is_a_measurement(stated) is ok


# ------------------------------------------------------------ 3. the latest wins

def test_the_most_recent_statement_is_the_current_one():
    """An issue's state is what it most recently says about itself."""
    i = _issue(
        body='AWAITING-RUN: the teleported-leg count on a four-iteration probe '
             'at 1 %, read from the run\'s own genericRouteTeleporter line.',
        comments=['AWAITING-RUN: nothing further from a 25 % arm. What this '
                  'issue needs next is a mechanism for the last hop onto a '
                  'platform, then probe 1 re-run.'])
    assert issue_gate.evidence(i) is None, (
        'the discharged statement must not outlive its own supersession')

    j = _issue(
        body='AWAITING-RUN: nothing yet, this is a placeholder while the cause '
             'is still being narrowed down by hand on the existing outputs.',
        comments=['AWAITING-RUN: walk\'s modelled mean resident trip length at '
                  'the next arm\'s iteration-100 gate, against the HTS 0.70 km.'])
    assert issue_gate.evidence(j) is not None, (
        'an issue that later states a real measurement is awaiting a run')


# ------------------------------------------------------------------- 4. the lane

def test_a_declared_lane_beats_a_scraped_one():
    """A description must be able to say an issue is NOT in the lane.

    Prose scraping cannot read a negation: correcting the depth arm's
    description to record that #167 is deliberately excluded put #167 straight
    back into its lane, because the scraper sees only `#167`.
    """
    import json
    import io
    import city as city_module

    overlay = os.path.join(city_module.CITY_DIR, 'overlays', 'runs',
                           'depth_convergence_25pct.json')
    if not os.path.isfile(overlay):
        pytest.skip('this city declares no depth_convergence_25pct overlay')
    doc = json.load(io.open(overlay, encoding='utf-8'))
    assert 'answers_issues' in doc, (
        'a gated arm must declare the lane it is scoped by, not leave it to a '
        'regular expression over its own prose')
    lane = issue_gate.lane('depth_convergence_25pct')
    assert lane == set(doc['answers_issues'])
    assert 167 not in lane, (
        '#167 is named in the description in order to be EXCLUDED - it ships '
        'at access_egress_basis = beeline and carries neither half of the '
        'routing repair, so this arm cannot settle it')
