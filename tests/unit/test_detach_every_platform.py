"""An arm can launch on every platform, and its proof is locale-free
(sixteenth report, 8 October 2026).

The fifteenth report's repair made the foreground proof a live scheduled
task - and asked for it on every platform, while `--detach` was refused off
Windows, so on POSIX no arm could launch at all. The proof also read the
word `Running` in `schtasks`' verbose CSV, which a German host prints as
`Wird ausgeführt`. Now the Windows proof reads the task's numeric state
through Get-ScheduledTask, POSIX launches in its own session with a proof
file, and an arm below the campaign's fraction is refused unless the reason
is stated and ledgered (#209's non-decision half).
"""
import json
import os
import subprocess
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
for p in (ROOT, os.path.join(ROOT, 'src')):
    if p not in sys.path:
        sys.path.insert(0, p)

import run as front_door                                        # noqa: E402

STAMP = '20261008T101010'
NONCE = 'cd' * 16


def _env():
    return {'CITYSIM_LAUNCH_STAMP': STAMP, 'SCHEDULED_LAUNCH_NONCE': NONCE}


# -------------------------------------------------- the locale-free proof

def _ps(stdout, rc=0):
    def run(cmd, **kw):
        assert cmd[0] == 'powershell' and 'Get-ScheduledTask' in cmd[-1]
        return types.SimpleNamespace(returncode=rc, stdout=stdout, stderr='')
    return run


def test_the_windows_proof_reads_the_numeric_state(monkeypatch):
    doc = {'state': 4, 'actions': ['C:\\x\\citysim_run_%s.cmd %s' % (STAMP, NONCE)]}
    monkeypatch.setattr(subprocess, 'run', _ps(json.dumps(doc)))
    info = front_door._query_task_windows('citysim_run_%s' % STAMP)
    assert info == dict(running=True, nonce_text=doc['actions'][0])
    assert front_door.scheduler_launched(_env(), lambda t: info) == (True, '')


def test_a_ready_task_is_not_running_whatever_the_locale_prints(monkeypatch):
    doc = {'state': 3, 'actions': 'C:\\x\\citysim_run_%s.cmd %s' % (STAMP, NONCE)}
    monkeypatch.setattr(subprocess, 'run', _ps(json.dumps(doc)))
    info = front_door._query_task_windows('citysim_run_%s' % STAMP)
    ok, why = front_door.scheduler_launched(_env(), lambda t: info)
    assert not ok and 'not running' in why


def test_no_task_is_no_proof(monkeypatch):
    monkeypatch.setattr(subprocess, 'run', _ps('', rc=1))
    assert front_door._query_task_windows('citysim_run_x') is None
    ok, why = front_door.scheduler_launched(_env(), lambda t: None)
    assert not ok and 'no task named' in why


def test_the_state_is_a_number_not_a_word():
    assert front_door.TASK_STATE_RUNNING == 4
    src = open(os.path.join(ROOT, 'run.py'), encoding='utf-8').read()
    assert "'Running' not in" not in src, 'the localised word is not the proof'


# -------------------------------------------------------- the POSIX launch

def test_posix_detach_starts_its_own_session_and_writes_the_proof(tmp_path, monkeypatch):
    calls = []

    class Proc:
        pid = 4321

    def popen(cmd, **kw):
        calls.append((cmd, kw))
        return Proc()

    monkeypatch.setattr(front_door, 'HERE', str(tmp_path))
    monkeypatch.setattr(os, 'name', 'posix')
    monkeypatch.setattr(sys, 'argv', ['run.py', '--run-config', 'x', '--detach'])
    monkeypatch.setattr(subprocess, 'Popen', popen)
    assert front_door._detach() == 0
    launch = tmp_path / 'results' / '_launch'
    wrapper = next(p for p in launch.iterdir() if p.suffix == '.sh').read_text(encoding='utf-8')
    proof = json.loads(next(p for p in launch.iterdir() if p.suffix == '.json')
                       .read_text(encoding='utf-8'))
    cmd, kw = calls[0]
    assert kw['start_new_session'] is True, 'setsid: the run outlives the shell'
    assert kw['stdin'] is subprocess.DEVNULL
    assert cmd[0] == '/bin/sh' and cmd[2] == proof['nonce']
    assert proof['sid'] == 4321 and proof['stamp'] == STAMP[:0] + proof['stamp']
    assert 'export SCHEDULED_LAUNCH_NONCE="$1"' in wrapper
    assert proof['nonce'] not in wrapper, 'the nonce is the launch\'s argument, never the file\'s'
    assert '--foreground' in wrapper and '--issue-gate-passed' in wrapper
    assert '--detach' not in wrapper.split('run.py', 1)[1]


def test_the_posix_proof_is_the_session(tmp_path, monkeypatch):
    launch = tmp_path / 'results' / '_launch'
    launch.mkdir(parents=True)
    task = 'citysim_run_%s' % STAMP
    (launch / (task + '.json')).write_text(json.dumps(dict(sid=777, nonce=NONCE)),
                                           encoding='utf-8')
    monkeypatch.setattr(front_door, 'HERE', str(tmp_path))
    monkeypatch.setattr(os, 'getsid', lambda pid: 777, raising=False)
    info = front_door._query_task_posix(task)
    assert info == dict(running=True, nonce_text=NONCE)
    assert front_door.scheduler_launched(_env(), front_door._query_task_posix) == (True, '')
    # a copied command line runs in the copier's session
    monkeypatch.setattr(os, 'getsid', lambda pid: 778, raising=False)
    ok, why = front_door.scheduler_launched(_env(), front_door._query_task_posix)
    assert not ok and 'not running' in why
    assert front_door._query_task_posix('citysim_run_none') is None


def test_the_foreground_refusal_names_the_platforms_launch(monkeypatch):
    class Cfg(dict):
        get = dict.get
    fields, _ = front_door.registry.load_registry()
    lo = front_door.registry._sweep_interval(
        fields['RUN.controler.last_iteration'].get('sweep'))
    a = types.SimpleNamespace(foreground=True)
    cfg = Cfg({'RUN.controler.last_iteration': int(lo[0])})
    monkeypatch.setattr(os, 'name', 'posix')
    with pytest.raises(SystemExit, match='setsid'):
        front_door.refuse_foreground_arm(a, cfg, launched=lambda: (False, 'no proof'))
    monkeypatch.setattr(os, 'name', 'nt')
    with pytest.raises(SystemExit, match='Task Scheduler'):
        front_door.refuse_foreground_arm(a, cfg, launched=lambda: (False, 'no proof'))


# ------------------------------------------------------ the arm's fraction

class Cfg(dict):
    get = dict.get


def _arm_cfg(fraction, floor=0.25):
    fields, _ = front_door.registry.load_registry()
    lo = front_door.registry._sweep_interval(
        fields['RUN.controler.last_iteration'].get('sweep'))
    return Cfg({'RUN.controler.last_iteration': int(lo[0]),
                'RUN.sample.fraction': fraction,
                'RUN.sample.arm_fraction_floor': floor}), int(lo[0])


def test_an_arm_below_the_campaign_fraction_is_refused():
    cfg, last = _arm_cfg(0.10)
    with pytest.raises(SystemExit, match='arm_fraction_floor'):
        front_door.refuse_arm_fraction(types.SimpleNamespace(override_reason=None), cfg)


def test_an_arm_at_the_campaign_fraction_launches():
    cfg, _ = _arm_cfg(0.25)
    front_door.refuse_arm_fraction(types.SimpleNamespace(override_reason=None), cfg)


def test_a_probe_is_never_asked():
    cfg, last = _arm_cfg(0.01)
    cfg['RUN.controler.last_iteration'] = 4
    front_door.refuse_arm_fraction(types.SimpleNamespace(override_reason=None), cfg)


def test_a_floor_of_zero_asks_nothing():
    cfg, _ = _arm_cfg(0.01, floor=0)
    front_door.refuse_arm_fraction(types.SimpleNamespace(override_reason=None), cfg)


def test_the_override_is_stated_and_ledgered(tmp_path, monkeypatch, capsys):
    import issue_gate
    monkeypatch.setattr(issue_gate, '_ledger_path', lambda: str(tmp_path / 'ledger.json'))
    cfg, _ = _arm_cfg(0.10)
    front_door.refuse_arm_fraction(
        types.SimpleNamespace(override_reason='a 10 % sensitivity the user approved'),
        cfg, run_config='x')
    entries = json.loads((tmp_path / 'ledger.json').read_text(encoding='utf-8'))
    assert 'arm_fraction_floor' in entries[-1]['reason'] and entries[-1]['run_config'] == 'x'
    assert 'OVERRIDDEN' in capsys.readouterr().out
