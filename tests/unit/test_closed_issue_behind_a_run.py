"""The mirror of requirement 10: no CLOSED issue behind a run either
(sixteenth report, 8 October 2026).

#175 was closed on 13 September and still named by the F39 treatment overlay
and the lane's recommended task, so the issue gate - which reads the OPEN
set - found nothing blocking and requirement 10 was satisfied vacuously: the
arm's reading would have had no issue to land on. Now the gate asks GitHub
for the state of every issue in the overlay's lane and refuses a closed one,
flags an AWAITING-RUN line that names a run of a family the ledger has
closed, prints the lane task bound to the overlay, and `lane.py --check`
fails when the lane's family is not the ledger's newest or an open task
answers a closed issue. Every test here is a fixture; nothing reaches the
network.
"""
import json

import issue_gate
import lane


def _issue(number, labels=('awaiting-run',), body='AWAITING-RUN: the four pt '
           'submodes against the control arm 20260929T072135_250it_25pct'):
    return dict(number=number, title='issue %d' % number, labels=list(labels),
                body=body, comments=[])


def _fix(monkeypatch, open_numbers, lane_numbers, states):
    monkeypatch.setattr(issue_gate, 'open_issues',
                        lambda: ('ok', [_issue(n) for n in open_numbers]))
    monkeypatch.setattr(issue_gate, 'lane', lambda rc: set(lane_numbers))
    monkeypatch.setattr(issue_gate, 'issue_states', lambda nums: ('ok', states))
    monkeypatch.setattr(issue_gate, 'lane_tasks_for', lambda rc, nums: [])


# --------------------------------------------------------------- the launch

def test_a_closed_issue_in_the_lane_refuses_the_launch(monkeypatch):
    _fix(monkeypatch, [94, 98], [94, 98, 175],
         {94: None, 98: None, 175: '2026-09-13T18:14:23Z'})
    why = issue_gate.refuse_launch(run_config='f39_headway_25pct')
    assert why and '#175' in why and 'CLOSED (2026-09-13)' in why


def test_an_open_lane_launches(monkeypatch):
    _fix(monkeypatch, [94, 98, 175], [94, 98, 175], {94: None, 98: None, 175: None})
    assert issue_gate.refuse_launch(run_config='f39_headway_25pct') is None


def test_a_lane_whose_states_cannot_be_read_is_not_a_pass(monkeypatch):
    _fix(monkeypatch, [94], [94, 175], {})
    monkeypatch.setattr(issue_gate, 'issue_states', lambda nums: ('error', {}))
    why = issue_gate.refuse_launch(run_config='f39_headway_25pct')
    assert why and 'could not be read' in why


def test_the_closed_issue_override_is_counted_like_the_others(monkeypatch, tmp_path):
    _fix(monkeypatch, [94], [94, 175], {94: None, 175: '2026-09-13T18:14:23Z'})
    monkeypatch.setattr(issue_gate, '_ledger_path',
                        lambda: str(tmp_path / 'ledger.json'))
    assert issue_gate.refuse_launch(allow_open_issues=True, reason='the reopen is '
                                    'on its way', run_config='x') is None
    entries = json.loads((tmp_path / 'ledger.json').read_text(encoding='utf-8'))
    assert entries[-1]['issues'][0]['number'] == 175


def test_the_lane_task_bound_to_the_overlay_is_found():
    doc = {'tasks': [
        {'id': 'f39-headway-arm', 'status': 'open', 'recommended': True,
         'answers_issues': [94, 98, 175], 'title': 'run the treatment'},
        {'id': 'other', 'status': 'open', 'answers_issues': [30], 'title': 'x'},
        {'id': 'done-one', 'status': 'done', 'answers_issues': [94, 98, 175], 'title': 'y'},
        {'id': 'by-name', 'status': 'held', 'answers_issues': [],
         'cost': 'priced by f39_headway_probe_25pct', 'title': 'z'}]}
    import types
    fake = types.SimpleNamespace(load=lambda: doc)
    import sys
    saved = sys.modules.get('lane')
    sys.modules['lane'] = fake
    try:
        found = issue_gate.lane_tasks_for('f39_headway_25pct', {94, 98, 175})
        assert [t['id'] for t in found] == ['f39-headway-arm']
        found = issue_gate.lane_tasks_for('f39_headway_probe_25pct', set())
        assert [t['id'] for t in found] == ['by-name']
    finally:
        if saved is not None:
            sys.modules['lane'] = saved
        else:
            del sys.modules['lane']


# ----------------------------------------------------- the closed family

def test_an_awaiting_line_on_a_closed_family_is_flagged(monkeypatch):
    monkeypatch.setattr(lane, 'newest_family_key', lambda: 'F39-newest')
    monkeypatch.setattr(lane, 'family_key_for',
                        lambda p: {'F35': 'F35-old', 'F39': 'F39-newest'}.get(p))
    import iteration_reading
    monkeypatch.setattr(iteration_reading, 'run_family',
                        lambda name: ('F35-old' if name.startswith('20260912')
                                      else 'F39-newest', '', ''))
    issues = [_issue(49, body="AWAITING-RUN: the submodes pair against F35's arm 0 "
                              "and 20260912T202242_300it_25pct"),
              _issue(94, body='AWAITING-RUN: f39_headway_25pct against '
                              '20260929T072135_250it_25pct'),
              _issue(50, labels=('decision-needed',), body='AWAITING-DECISION: x')]
    stale = issue_gate.awaiting_closed_family(issues)
    assert [i['number'] for i in stale] == [49]
    assert set(stale[0]['stale'].values()) == {'F35-old'}


# ---------------------------------------------------------- lane --check

def _doc(family='F39-newest', issues=(94, 98, 175)):
    return {'description': 't', 'updated': '2026-10-08', 'family': family,
            'tasks': [{'id': 'a', 'title': 'first', 'kind': 'run', 'status': 'open',
                       'recommended': True, 'cost': '1 h', 'blocked_on': 'D29',
                       'opens_family': False, 'answers_issues': list(issues),
                       'evidence': '9.219'},
                      {'id': 'b', 'title': 'done', 'kind': 'run', 'status': 'done',
                       'done_ref': '9.1', 'recommended': False, 'cost': '', 'blocked_on': '',
                       'opens_family': False, 'answers_issues': [258], 'evidence': ''}],
            'decisions': []}


def test_a_lane_on_the_previous_family_is_a_problem():
    assert lane.family_problems(_doc(family='F38-previous'), 'F39-newest')
    assert lane.family_problems(_doc(), 'F39-newest') == []
    assert lane.family_problems(_doc(family='x'), None) == [], 'no ledger, no claim'


def test_an_open_task_answering_a_closed_issue_is_a_problem():
    states = {94: None, 98: None, 175: '2026-09-13T18:14:23Z', 258: '2026-09-30T01:00:00Z'}
    bad = lane.closed_issue_problems(_doc(), states)
    assert len(bad) == 1 and '#175' in bad[0] and 'task a' in bad[0]
    assert lane.open_issue_numbers(_doc()) == {94, 98, 175}, 'a done task is not asked'


def test_check_fails_on_the_family_and_the_closed_issue(tmp_path, monkeypatch, capsys):
    p = tmp_path / 'lane.json'
    p.write_text(json.dumps(_doc(family='F38-previous')), encoding='utf-8')
    monkeypatch.setattr(lane, 'PATH', str(p))
    monkeypatch.setattr(lane, 'newest_family_key', lambda: 'F39-newest')
    monkeypatch.setattr(issue_gate, 'issue_states',
                        lambda nums: ('ok', {94: None, 98: None, 175: '2026-09-13T00:00:00Z'}))
    assert lane.main(['--check']) == 1
    out = capsys.readouterr().out
    assert 'not the ledger\'s newest' in out and '#175' in out


def test_check_offline_warns_and_never_passes_silently(tmp_path, monkeypatch, capsys):
    p = tmp_path / 'lane.json'
    p.write_text(json.dumps(_doc()), encoding='utf-8')
    monkeypatch.setattr(lane, 'PATH', str(p))
    monkeypatch.setattr(lane, 'newest_family_key', lambda: 'F39-newest')
    monkeypatch.setattr(issue_gate, 'issue_states', lambda nums: ('no-gh', {}))
    assert lane.main(['--check']) == 0
    assert 'WARN' in capsys.readouterr().out


def test_check_passes_a_current_lane(tmp_path, monkeypatch):
    p = tmp_path / 'lane.json'
    p.write_text(json.dumps(_doc()), encoding='utf-8')
    monkeypatch.setattr(lane, 'PATH', str(p))
    monkeypatch.setattr(lane, 'newest_family_key', lambda: 'F39-newest')
    monkeypatch.setattr(issue_gate, 'issue_states',
                        lambda nums: ('ok', {94: None, 98: None, 175: None}))
    assert lane.main(['--check']) == 0
