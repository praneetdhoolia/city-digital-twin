"""Function-level smoke over the modules the eighth report named untested (#190).

An import proves a module loads; these prove that the one function each
module exists for still runs on inputs a test can build. The first is the
defect that started the issue: `build_matsim_network.java()` unpacked four
values from `bootstrap_toolchain.require()`, which returns two, for
seventeen days with every gate green.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
for _sub in ('build', 'setup'):
    _p = os.path.join(REPO, 'src', _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)


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
