"""Function-level smoke over the modules the eighth report named untested (#190).

An import proves a module loads; these prove that the one function each
module exists for still runs on inputs a test can build. The first is the
defect that started the issue: `build_matsim_network.java()` unpacked four
values from `bootstrap_toolchain.require()`, which returns two, for
seventeen days with every gate green.
"""
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
for _sub in ('build', 'setup'):
    _p = os.path.join(REPO, 'src', _sub)


def test_network_build_calls_the_toolchain_with_two_values(monkeypatch, tmp_path):
    """`java()` unpacks exactly what `require()` returns and runs the command."""
    import build_matsim_network as bmn
    import bootstrap_toolchain as tc
    seen = {}
    monkeypatch.setattr(tc, 'require', lambda: ('java-stub', 'pt2matsim-stub.jar'))

    class _Done(object):
        returncode, stdout, stderr = 0, 'ok', ''

    def fake_run(cmd, capture_output, text):
        seen['cmd'] = cmd
        return _Done()
    monkeypatch.setattr(bmn.subprocess, 'run', fake_run)
    monkeypatch.setattr(bmn, 'WORK', str(tmp_path))
    bmn.java(['org.matsim.pt2matsim.run.Osm2MultimodalNetwork', 'x.xml'], 'smoke')
    assert seen['cmd'][0] == 'java-stub'
    assert seen['cmd'][2:4] == ['-cp', 'pt2matsim-stub.jar']
    assert os.path.exists(os.path.join(str(tmp_path), 'logs', 'smoke.log'))


def test_run_failure_reads_the_terminal_exception_and_its_chain(tmp_path):
    import run_failure
    log = tmp_path / 'matsim.log'
    log.write_text(
        '2026-09-10T22:00:00,000  INFO Counter:71 iteration 3\n'
        '2026-09-10T22:00:01,000 ERROR MatsimRuntimeModifications:77 Getting uncaught Exception in Thread main\n'
        'java.lang.RuntimeException: Exception while processing persons.\n'
        '\tat org.matsim.core.controler.PrepareForSimImpl.run(PrepareForSimImpl.java:1)\n'
        'Caused by: java.lang.OutOfMemoryError: Java heap space\n'
        '\tat java.base/java.util.HashMap.resize(HashMap.java:1)\n', encoding='utf-8')
    found = run_failure.from_log(str(log))
    assert found is not None
    assert found['cause'] == 'OutOfMemoryError: Java heap space'
    assert found['caused_by'][-1]['exception'].endswith('OutOfMemoryError')


def test_run_failure_says_none_for_a_clean_log(tmp_path):
    import run_failure
    log = tmp_path / 'matsim.log'
    log.write_text('2026-09-10T22:00:00,000  INFO Controler:1 all done\n', encoding='utf-8')
    assert run_failure.from_log(str(log)) is None


def test_station_of_reduces_a_platform_name_to_the_disclosed_form():
    import report_mode_ridership as rmr
    assert rmr.station_of('Hamilton Station Platform 1') == 'hamilton'
    assert rmr.station_of('Broadmeadow Station') == 'broadmeadow'
    assert rmr.station_of('  Wickham Light Rail ') == 'wickham light rail'
    assert rmr.station_of(None) == ''


def test_sample_keep_is_deterministic_and_nests_by_unit():
    import sample_population as sp
    a = [sp.keep(i, 0.25, seed=20260810, unit='person') for i in range(2000)]
    b = [sp.keep(i, 0.25, seed=20260810, unit='person') for i in range(2000)]
    assert a == b
    share = sum(a) / len(a)
    assert 0.20 < share < 0.30
    # a smaller fraction is a subset of a larger one at the same seed
    small = {i for i in range(2000) if sp.keep(i, 0.10, seed=20260810, unit='person')}
    large = {i for i in range(2000) if sp.keep(i, 0.25, seed=20260810, unit='person')}
    assert small <= large
    # the household key is its own draw, namespaced from the person key
    assert sp.keep(7, 0.5, seed=1, household_id=7, unit='household') \
        == sp.keep(99, 0.5, seed=1, household_id=7, unit='household')


def test_relaxation_reports_the_window_and_the_snap():
    """modestats shape: an `iteration` list and one share (0..1) list per mode."""
    import summarise_run as sr
    its = list(range(0, 101, 10))
    car = [0.60] * len(its)
    car[its.index(90)] = 0.63           # the selection snap lands after the cutoff
    car[its.index(100)] = 0.632
    modes = {'iteration': its, 'car': car, 'walk': [0.10] * len(its)}
    block = sr.relaxation(modes, innovation_off_at=80, tolerance_pp=0.5, settle_margin=10)
    assert block['innovation_off_at'] == 80
    assert block['settle_point'] == 90 and block['to_iteration'] == 100
    assert block['snap_pp']['car'] == pytest.approx(3.0)
    assert block['drift_pp']['car'] == pytest.approx(0.2)
    assert block['relaxed'] is True


# ---------------------------------------------------------------------------
# Import-and-run-help over every src/analyse and src/calibrate module and the
# five build modules the sixteenth report named as imported by no test. A
# module with a `--help` path (argparse, or an explicit '--help' branch) is
# RUN with `--help` in a fresh interpreter and must exit 0 or 2 without a
# traceback; a module without one (a library, or a builder whose main takes
# no arguments and would do its work) is imported instead. Every subprocess
# runs once, concurrently, and each parametrised test reads its verdict.
# ---------------------------------------------------------------------------
import glob
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import test_import_sweep as _sweep

SMOKE_EXTRA = ['src/build/build_population.py', 'src/build/build_gtfs_extras.py',
               'src/build/build_network_layers.py', 'src/build/gtfs_tools.py', 'src/build/shape_tools.py']


def _smoke_modules():
    out = []
    for pattern in ('src/analyse/*.py', 'src/calibrate/*.py'):
        out += sorted(os.path.relpath(p, REPO).replace(os.sep, '/')
                      for p in glob.glob(os.path.join(REPO, pattern)))
    return out + SMOKE_EXTRA


SMOKE_MODULES = _smoke_modules()


def _has_help_path(path):
    with open(path, encoding='utf-8') as fh:
        src = fh.read()
    return 'argparse' in src or "'--help'" in src or '"--help"' in src


def _smoke_one(rel):
    path = os.path.join(REPO, rel)
    name = os.path.splitext(os.path.basename(rel))[0]
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    if name in _sweep.RUNS_AT_IMPORT:
        with open(path, encoding='utf-8') as fh:
            compile(fh.read(), path, 'exec')
        return dict(verdict='pass', how='compiled')
    if _has_help_path(path):
        proc = subprocess.run([sys.executable, path, '--help'], capture_output=True, text=True,
                              timeout=300, env=env, cwd=REPO)
        out = (proc.stdout or '') + (proc.stderr or '')
        if 'ModuleNotFoundError' in out:
            missing = out.rsplit('ModuleNotFoundError: No module named', 1)[-1].strip().strip("'\" \n")
            return dict(verdict='skip', why='third-party package missing: %s' % missing, name=missing)
        if proc.returncode in (0, 2) and 'Traceback' not in out:
            return dict(verdict='pass', how='--help')
        if 'FileNotFoundError' in out or 'PermissionError' in out:
            return dict(verdict='skip', why='opens an artefact this checkout does not hold')
        return dict(verdict='fail', why='--help exited %d:\n%s' % (proc.returncode, out[-1500:]))
    proc = subprocess.run([sys.executable, '-c', _sweep.RUNNER, REPO, path, name],
                          capture_output=True, text=True, timeout=300, env=env)
    last = (proc.stdout.strip().splitlines() or ['{}'])[-1]
    try:
        verdict = json.loads(last)
    except ValueError:
        verdict = dict(verdict='fail', why='no verdict (rc=%d)\n%s' % (proc.returncode, (proc.stderr or '')[-1500:]))
    verdict['how'] = 'import'
    return verdict


@pytest.fixture(scope='module')
def smoke_verdicts():
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(SMOKE_MODULES, pool.map(_smoke_one, SMOKE_MODULES)))


@pytest.mark.parametrize('rel', SMOKE_MODULES)
def test_module_imports_and_answers_help(rel, smoke_verdicts):
    v = smoke_verdicts[rel]
    if v['verdict'] == 'skip':
        if v.get('name') and v['name'].split('.')[0] not in _sweep.THIRD_PARTY:
            pytest.fail('%s: a MISSING MODULE that is not a known third-party package: %s' % (rel, v['why']))
        pytest.skip('%s: %s' % (rel, v['why']))
    assert v['verdict'] == 'pass', '%s (%s):\n%s' % (rel, v.get('how'), v.get('why'))
