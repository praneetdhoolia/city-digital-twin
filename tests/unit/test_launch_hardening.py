"""The fifteenth report's launch and stop repairs (29 September 2026).

1. An arm's foreground exemption is a proof the scheduler launched it - a
   live task named by the launch stamp that carries the per-launch nonce -
   never a flag in the child's copyable argv.
2. (test_warm_start_after_death.py) a resume overlay's cutoff is checked.
3. A pid the kernel will not describe is 'unknown', never dead; `--stop`
   records `died` only when the run's own log confirms it stopped writing.
4. A died run's wall time stops at its log's last line.
5. A warm start is priced from its checkpoint.
6. Every progress write carries the host's load.
"""
import json
import os
import time
import types

import pytest

import arm_cost
import procs
import progress_digest
import run_matsim as rm


def _run_py():
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        'run_py', os.path.join(here, '..', '..', 'run.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------ 1. the scheduler's proof
STAMP = '20260929T101010'
NONCE = 'ab' * 16


def _env(**kw):
    env = {'CITYSIM_LAUNCH_STAMP': STAMP, 'SCHEDULED_LAUNCH_NONCE': NONCE}
    env.update(kw)
    return {k: v for k, v in env.items() if v is not None}


def _task(status='Running', action='"C:\\x\\citysim_run_%s.cmd" %s' % (STAMP, NONCE)):
    """What `_query_task` answers for the launch's task: its state as the
    scheduler's NUMBER (the word is localised, sixteenth report) and the
    text of its registered action, which carries the nonce."""
    states = {'Running': 4, 'Ready': 3, 'Queued': 2, 'Disabled': 1}

    def query(task):
        assert task == 'citysim_run_%s' % STAMP
        return dict(running=states[status] == 4, nonce_text=action)
    return query


def test_the_live_task_carrying_the_nonce_is_proof():
    run_py = _run_py()
    assert run_py.scheduler_launched(_env(), _task()) == (True, '')


def test_a_copied_command_line_carries_no_stamp_or_nonce():
    run_py = _run_py()
    ok, why = run_py.scheduler_launched({}, _task())
    assert not ok and 'not started by' in why


def test_the_wrapper_run_by_hand_carries_no_nonce():
    run_py = _run_py()
    ok, _ = run_py.scheduler_launched(_env(SCHEDULED_LAUNCH_NONCE=''), _task())
    assert not ok


def test_a_task_that_is_not_running_is_no_proof():
    run_py = _run_py()
    ok, why = run_py.scheduler_launched(_env(), _task(status='Ready'))
    assert not ok and 'not running' in why


def test_a_task_that_ended_and_deleted_itself_is_no_proof():
    run_py = _run_py()
    ok, why = run_py.scheduler_launched(_env(), lambda task: [])
    assert not ok and 'no task named' in why


def test_a_forged_nonce_is_no_proof():
    run_py = _run_py()
    ok, why = run_py.scheduler_launched(_env(SCHEDULED_LAUNCH_NONCE='f' * 32),
                                        _task())
    assert not ok and 'nonce' in why


def test_the_nonce_env_is_not_read_as_a_registry_field():
    """Every CITYSIM_* variable is a registry override; the nonce is not one."""
    run_py = _run_py()
    assert not run_py.NONCE_ENV.startswith('CITYSIM_')


def test_the_childs_argv_no_longer_carries_the_flag(monkeypatch, tmp_path):
    """`_detach` writes the wrapper; the child's argv must not self-certify."""
    run_py = _run_py()
    calls = []
    monkeypatch.setattr(run_py, 'HERE', str(tmp_path))
    monkeypatch.setattr(run_py.os, 'name', 'nt')
    monkeypatch.setattr('sys.argv', ['run.py', '--run-config', 'x', '--detach'])
    import subprocess
    monkeypatch.setattr(subprocess, 'check_call', lambda cmd, **k: calls.append(cmd))
    run_py._detach()
    wrapper = next(p for p in (tmp_path / 'results' / '_launch').iterdir()
                   if p.suffix == '.cmd').read_text(encoding='ascii')
    assert '--scheduled-child' not in wrapper
    assert '--foreground' in wrapper
    assert 'set SCHEDULED_LAUNCH_NONCE=%~1' in wrapper
    create = calls[0]
    tr = create[create.index('/tr') + 1]
    nonce = tr.rsplit(' ', 1)[1]
    assert len(nonce) == 32 and nonce not in wrapper, (
        'the nonce is the task\'s argument, never a line of the copyable file')


# ------------------------------------------------------- 3. tri-state liveness
class _FakeK32:
    def __init__(self, handle, wait=procs._WAIT_TIMEOUT):
        self.handle, self.wait = handle, wait

    def OpenProcess(self, access, inherit, pid):
        return self.handle

    def WaitForSingleObject(self, h, ms):
        return self.wait

    def CloseHandle(self, h):
        return 1


def _fake_ctypes(err):
    return types.SimpleNamespace(get_last_error=lambda: err)


@pytest.mark.parametrize('handle,err,wait,expected', [
    (0, procs._ERROR_INVALID_PARAMETER, None, procs.DEAD),   # no such pid
    (0, 5, None, procs.UNKNOWN),                             # access denied
    (0, 31, None, procs.UNKNOWN),                            # anything else
    (7, 0, procs._WAIT_TIMEOUT, procs.ALIVE),
    (7, 0, procs._WAIT_OBJECT_0, procs.DEAD),                # exited
])
def test_openprocess_is_read_three_ways(monkeypatch, handle, err, wait, expected):
    monkeypatch.setattr(procs.os, 'name', 'nt')
    monkeypatch.setattr(procs, '_kernel32',
                        lambda: (_FakeK32(handle, wait), _fake_ctypes(err)))
    assert procs.pid_state(4242) == expected


def test_access_denied_is_not_dead_to_any_caller(monkeypatch):
    monkeypatch.setattr(procs.os, 'name', 'nt')
    monkeypatch.setattr(procs, '_kernel32',
                        lambda: (_FakeK32(0), _fake_ctypes(5)))
    assert procs.pid_alive(4242) is True


LOG = ('2026-09-28T10:00:00,000  INFO AbstractController:137 ### ITERATION 5 BEGINS\n'
       '2026-09-28T10:05:00,000  INFO AbstractController:184 ### ITERATION 5 ENDS\n'
       '2026-09-28T10:06:40,500  INFO Something: last line\n')


def _running(tmp_path, log=LOG, iteration_seconds=None):
    d = tmp_path / '20260928T095000_250it_25pct'
    d.mkdir()
    (d / '_meta.json').write_text(json.dumps(dict(
        status='running', pid=1, jvm_pid=2, started='2026-09-28T09:50:00')),
        encoding='utf-8')
    (d / 'matsim.log').write_text(log, encoding='utf-8')
    if iteration_seconds is not None:
        (d / '_progress.json').write_text(json.dumps(dict(
            iteration_seconds=iteration_seconds)), encoding='utf-8')
    return d


def _stub(monkeypatch, d, states):
    seen = {}
    monkeypatch.setattr(rm.results_store, 'resolve', lambda name: str(d))
    monkeypatch.setattr(rm, 'card_pid_state', lambda meta, key: states[key])
    monkeypatch.setattr(rm.subprocess, 'run', lambda *a, **k: None)
    monkeypatch.setattr(rm.time, 'sleep', lambda s: None)

    def mark_dead(run_dir, status, cause=None, wall_s=None):
        seen['mark_wall_s'] = wall_s
        return run_dir
    monkeypatch.setattr(rm, 'mark_dead', mark_dead)

    def close_out(dead, completion, **kw):
        seen['completion'] = completion
        seen['wall_s'] = kw.get('wall_s')
        return None
    monkeypatch.setattr(rm, 'close_out', close_out)
    monkeypatch.setattr(rm.registry, 'load', lambda: {})
    monkeypatch.setattr(rm.results_store, 'trim', lambda *a, **k: None)
    return seen


def _log_ending(seconds_ago):
    stamp = time.strftime('%Y-%m-%dT%H:%M:%S',
                          time.localtime(time.time() - seconds_ago))
    return LOG + '%s,000  INFO Something: newest line\n' % stamp


def test_an_unknown_pid_with_a_fresh_log_is_not_recorded_as_died(monkeypatch, tmp_path):
    """Access denied on a live JVM: the stop is the operator's, not a death."""
    d = _running(tmp_path, log=_log_ending(60), iteration_seconds={'5': 300.0})
    seen = _stub(monkeypatch, d, {'pid': procs.DEAD, 'jvm_pid': procs.UNKNOWN})
    rm.stop_run(d.name, 'stop')
    assert seen['completion'] == rm.STOPPED_BY_OPERATOR


def test_an_unknown_pid_silent_past_its_longest_iteration_died(monkeypatch, tmp_path):
    d = _running(tmp_path, log=_log_ending(3600), iteration_seconds={'5': 300.0})
    seen = _stub(monkeypatch, d, {'pid': procs.UNKNOWN, 'jvm_pid': procs.UNKNOWN})
    rm.stop_run(d.name, 'stop')
    assert seen['completion'] == rm.DIED


def test_an_unknown_pid_with_no_recorded_pace_is_not_called_dead(monkeypatch, tmp_path):
    d = _running(tmp_path)
    seen = _stub(monkeypatch, d, {'pid': procs.UNKNOWN, 'jvm_pid': procs.DEAD})
    rm.stop_run(d.name, 'stop')
    assert seen['completion'] == rm.STOPPED_BY_OPERATOR


def test_a_growing_log_is_not_a_death():
    ok, why = rm.log_confirms_death(__file__, {'pid': procs.DEAD}, 1, None)
    assert not ok and 'grew' in why


# --------------------------------------------- 4. a died run's wall time
def test_a_died_runs_wall_stops_at_its_logs_last_line(monkeypatch, tmp_path):
    """aborted_20260928T163345 carried 1.8 h past its death on its record."""
    d = _running(tmp_path)
    seen = _stub(monkeypatch, d, {'pid': procs.DEAD, 'jvm_pid': procs.DEAD})
    rm.stop_run(d.name, 'died with the host')
    assert seen['completion'] == rm.DIED
    # 09:50:00 -> 10:06:40.5 is 1000.5 s, whatever the close-out's clock says
    assert seen['wall_s'] == 1000.5
    assert seen['mark_wall_s'] == 1000.5


def test_the_last_timestamp_is_read_from_the_tail(tmp_path):
    p = tmp_path / 'matsim.log'
    p.write_text('x' * 200000 + '\n' + LOG, encoding='utf-8')
    got = rm.log_last_timestamp(str(p), nbytes=4096)
    assert got == time.mktime(time.strptime('2026-09-28T10:06:40',
                                            '%Y-%m-%dT%H:%M:%S')) + 0.5


# ------------------------------------------------- 5. a warm start's price
def _arm(**kw):
    base = dict(name='20260101T000000_300it_25pct', fraction=0.25,
                median_iteration_s=400.0, reached_iteration=100, setup_s=0.0,
                profiled=False, completion='died', plain=None,
                controler_sha256=None)
    base.update(kw)
    return base


def test_a_warm_start_is_priced_from_its_checkpoint():
    """F38's 175-iteration resume was quoted at the price of all 250."""
    cold = arm_cost.price(250, 0.25, [_arm()])
    warm = arm_cost.price(250, 0.25, [_arm()], first_iteration=175)
    assert cold['quote_s'] == 250 * 400.0
    assert warm['quote_s'] == 75 * 400.0
    assert warm['iterations'] == 75 and warm['first_iteration'] == 175
    assert warm['last_iteration'] == 250


def test_a_warm_starts_first_gate_is_the_next_milestone():
    warm = arm_cost.price(250, 0.25, [_arm()], gate_every=50, first_iteration=175)
    assert warm['first_gate_iteration'] == 200
    assert warm['first_gate_s'] == 25 * 400.0


# ------------------------------------------------------ 6. the host's load
def test_the_host_load_carries_cpu_ram_and_the_top_other_process(monkeypatch):
    samples = iter([(100.0, 1000.0), (400.0, 1600.0)])
    monkeypatch.setattr(procs, '_cpu_times', lambda: next(samples))
    monkeypatch.setattr(procs, '_memory', lambda: (8 * 2 ** 30, 64 * 2 ** 30))
    tables = iter([{10: ('java.exe', 50.0), 11: ('MsMpEng.exe', 5.0)},
                   {10: ('java.exe', 500.0), 11: ('MsMpEng.exe', 35.0)}])
    monkeypatch.setattr(procs, '_process_cpu', lambda: next(tables))
    clock = iter([1000.0, 1030.0])
    # a stand-in module, never the global `time.time`: other tests' daemon
    # threads read the real clock
    monkeypatch.setattr(procs, 'time', types.SimpleNamespace(
        time=lambda: next(clock), strftime=time.strftime,
        localtime=time.localtime))
    first, prev = procs.host_load(None, exclude_pids=(10,))
    assert first['cpu_pct'] is None, 'one reading of a counter is not a rate'
    doc, _ = procs.host_load(prev, exclude_pids=(10,))
    assert doc['cpu_pct'] == 50.0
    assert doc['ram_free_gb'] == 8.0 and doc['ram_total_gb'] == 64.0
    assert doc['top_other_process'] == dict(pid=11, name='MsMpEng.exe', cores=1.0)


def test_the_host_load_never_raises(monkeypatch):
    monkeypatch.setattr(procs, '_cpu_times', lambda: None)
    monkeypatch.setattr(procs, '_memory', lambda: None)
    monkeypatch.setattr(procs, '_process_cpu', lambda: None)
    doc, _ = procs.host_load({'at': 0.0, 'cpu': None, 'procs': None})
    assert doc['cpu_pct'] is None and doc['ram_free_gb'] is None


def test_every_progress_write_carries_the_host(monkeypatch, tmp_path):
    monkeypatch.setattr(progress_digest.run_view, 'scan',
                        lambda run_dir: dict(name='r', state='running',
                                             scenario='S2', day='WEEKDAY'))
    monkeypatch.setattr(progress_digest.run_view, 'read_iterations', lambda log: [])
    monkeypatch.setattr(progress_digest.run_view, 'read_iteration_spans',
                        lambda log: {})
    host = dict(cpu_pct=12.5, ram_free_gb=20.0)
    doc = progress_digest.digest(str(tmp_path), solo_iters=(2,), host=host)
    assert doc['host'] == host
    from registry import outputs
    assert not outputs.validate_doc('progress', doc)
    # and a write that was handed none reads the host itself
    doc = progress_digest.digest(str(tmp_path), solo_iters=(2,))
    assert 'ram_free_gb' in doc['host'] or 'error' in doc['host']
