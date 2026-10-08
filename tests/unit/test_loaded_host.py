"""A loaded host is refused at preflight and remembered across the run
(sixteenth report, performance rank 2; 8 October 2026).

F39's control carried a 2.09 h band of full-GC pauses while the host paged
and F37 lost 5.56 h the same way; every progress write recorded the host and
nothing refused on it, and only the LAST sample survived, so the band could
not be attributed. Now: `refuse_loaded_host` refuses free memory below the
heap plus `RUN.machine.free_ram_margin_gib` and another process over
`RUN.machine.other_process_max_cores`; the digest appends every sample to
`_host.jsonl` under the outputs contract; `arm_cost` refuses to quote from a
probe whose host read above `RUN.machine.probe_max_host_cpu_pct` and carries
the family's control wall as the pair quote.
"""
import json
import os

import pytest

import arm_cost
import outputs
import progress_digest
import run_matsim as rm


class Cfg(dict):
    get = dict.get


BASE = {'RUN.machine.xmx': '48g', 'RUN.machine.free_ram_margin_gib': 6.0,
        'RUN.machine.other_process_max_cores': 1.0}


def _host(free=20.0, cores=None, name='chrome.exe'):
    top = None if cores is None else dict(pid=4242, name=name, cores=cores)
    return dict(at='2026-10-08T10:00:00', cpu_pct=70.0, span_s=3.0,
                ram_free_gb=free, ram_total_gb=63.46, top_other_process=top)


# ------------------------------------------------------------ the refusal

def test_free_memory_below_heap_plus_margin_is_refused():
    with pytest.raises(SystemExit, match='54.0 GiB') as e:
        rm.refuse_loaded_host(Cfg(BASE), _host(free=50.0, cores=0.2, name='Code.exe'))
    assert 'free_ram_margin_gib' in str(e.value) and 'Code.exe' in str(e.value)


def test_free_memory_at_the_margin_launches():
    rm.refuse_loaded_host(Cfg(BASE), _host(free=54.0))


def test_a_process_over_the_core_bar_is_refused():
    with pytest.raises(SystemExit, match='chrome.exe'):
        rm.refuse_loaded_host(Cfg(BASE), _host(free=60.0, cores=1.7))


def test_a_process_under_the_core_bar_launches():
    rm.refuse_loaded_host(Cfg(BASE), _host(free=60.0, cores=0.9))


def test_zero_switches_each_bar_off():
    off = Cfg(dict(BASE, **{'RUN.machine.free_ram_margin_gib': 0,
                            'RUN.machine.other_process_max_cores': 0}))
    rm.refuse_loaded_host(off, _host(free=1.0, cores=20.0))


def test_a_reading_the_host_would_not_give_is_no_reason_to_refuse():
    rm.refuse_loaded_host(Cfg(BASE), dict(ram_free_gb=None, top_other_process=None))
    rm.refuse_loaded_host(Cfg(BASE), None)


def test_an_undeclared_field_asks_nothing():
    rm.refuse_loaded_host(Cfg({'RUN.machine.xmx': '48g'}), _host(free=1.0, cores=9.0))


def test_the_host_refusal_sits_inside_refuse_unsafe_host(monkeypatch):
    import procs
    monkeypatch.setattr(procs, 'restart_pending', lambda: False)
    monkeypatch.setattr(rm, 'host_sample', lambda cfg: _host(free=10.0))
    with pytest.raises(SystemExit, match='GiB free'):
        rm.refuse_unsafe_host(Cfg(BASE))


# ------------------------------------------------------------ the history

def test_every_sample_is_appended_and_meets_the_contract(tmp_path):
    run_dir = str(tmp_path)
    assert progress_digest.append_host_sample(run_dir, _host(cores=0.4), 12)
    assert progress_digest.append_host_sample(run_dir, _host(cores=1.6), 13)
    assert not progress_digest.append_host_sample(run_dir, dict(cpu_pct=1.0), 14), \
        'a reading with no clock is not history'
    rows = progress_digest.read_host_history(run_dir)
    assert [r['iteration'] for r in rows] == [12, 13]
    assert rows[1]['top_other_process']['cores'] == 1.6
    path = os.path.join(run_dir, progress_digest.HOST_HISTORY)
    assert outputs.kind_of(path) == 'host'
    assert outputs.validate_file(path) == []


def test_a_line_that_breaks_the_contract_is_named_by_its_line(tmp_path):
    path = tmp_path / '_host.jsonl'
    path.write_text(json.dumps(progress_digest.host_history_line(_host(), 1)) + '\n'
                    + '{"at": "x", "iteration": 2}\n' + 'not json\n', encoding='utf-8')
    problems = outputs.validate_file(str(path))
    assert any(p.startswith('line 3') for p in problems)
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        return
    assert any(p.startswith('line 2') for p in problems)


# ---------------------------------------------------------- the pricing

def _arm(name, cpu_max=None, completion='ran_to_last_iteration', reached=4,
         wall=4000.0, median=400.0):
    # cpu_max is the CPU OUTSIDE the run (9.221): the whole-host figure includes the
    # run's own JVM and is carried as information only
    host = None if cpu_max is None else dict(samples=8, cpu_pct_max=min(99.0, cpu_max + 60.0),
                                              cpu_pct_median=min(99.0, cpu_max + 50.0),
                                              other_cpu_pct_max=cpu_max,
                                              other_cpu_pct_median=max(0.0, cpu_max - 10),
                                              top_other_process=None)
    import city
    return dict(name=name, city=city.CITY, plain=None, wall_s=wall, host=host,
                profiled=False, fraction=0.25, median_iteration_s=median,
                reached_iteration=reached, setup_s=600.0, stalls_s={},
                completion=completion, family=None, controler_sha256=None)


def test_a_probe_on_a_loaded_host_is_refused_as_a_price():
    loaded = _arm('20260930T140500_4it_25pct', cpu_max=97.0, median=729.5)
    idle = _arm('20260929T060320_4it_25pct', cpu_max=82.0, median=429.3)
    quote = arm_cost.price(250, 0.25, [loaded, idle], max_host_cpu_pct=90.0)
    assert quote['priced_on']['name'] == idle['name']
    assert quote['refused_loaded_host'] == [loaded['name']]
    assert '97' in quote['host_warning'] and 'probe_max_host_cpu_pct' in quote['host_warning']


def test_a_probe_with_no_history_is_not_refused_on_what_it_cannot_say():
    unknown = _arm('20260930T140500_4it_25pct', cpu_max=None)
    quote = arm_cost.price(250, 0.25, [unknown], max_host_cpu_pct=90.0)
    assert quote['priced_on']['name'] == unknown['name']
    assert quote['host_warning'] is None


def test_the_bar_at_100_refuses_nothing():
    loaded = _arm('20260930T140500_4it_25pct', cpu_max=99.0)
    assert arm_cost.price(250, 0.25, [loaded], max_host_cpu_pct=100.0)['refused_loaded_host'] == []


def test_the_controls_own_wall_is_the_pair_quote():
    probe = _arm('20260930T140500_4it_25pct', cpu_max=80.0)
    control = _arm('20260929T072135_250it_25pct', reached=250, wall=100268.6)
    quote = arm_cost.price(250, 0.25, [probe, control], control=control)
    assert quote['pair_quote']['name'] == control['name']
    assert quote['pair_quote']['wall'] == '27.9 h'


def test_only_loaded_probes_leave_the_pair_quote_standing():
    loaded = _arm('20260930T140500_4it_25pct', cpu_max=97.0)
    control = _arm('20260929T072135_250it_25pct', reached=250, wall=100268.6)
    quote = arm_cost.price(250, 0.25, [loaded], max_host_cpu_pct=90.0, control=control)
    assert quote.get('error') and 'loaded host' in quote['error']
    assert quote['pair_quote']['wall'] == '27.9 h'


def test_host_summary_reads_the_busiest_iteration_and_the_top_process(tmp_path):
    run_dir = str(tmp_path)
    for it, cpu, cores in ((None, 40.0, 0.1), (1, 88.0, 0.3), (2, 96.0, 2.4), (3, 90.0, 0.5)):
        progress_digest.append_host_sample(
            run_dir, dict(_host(cores=cores), cpu_pct=cpu), it)
    s = arm_cost.host_summary(run_dir)
    assert s['samples'] == 3, 'the sample before iteration 0 is setup, not pace'
    assert s['cpu_pct_max'] == 96.0 and s['cpu_pct_median'] == 90.0
    assert s['top_other_process']['cores'] == 2.4 and s['top_other_process']['iteration'] == 2
    assert arm_cost.host_summary(str(tmp_path / 'none')) is None


def test_the_runs_own_jvm_does_not_price_the_host():
    """9.221: the first probe priced under the rule read 98 % whole-host CPU for its own 16
    mobsim threads; the bar is on the CPU outside the run."""
    own_work = _arm('20261008T114753_4it_25pct', cpu_max=6.0, median=531.0)
    own_work['host']['cpu_pct_max'] = 98.0
    quote = arm_cost.price(250, 0.25, [own_work], max_host_cpu_pct=90.0)
    assert quote['refused_loaded_host'] == [] and quote['priced_on']['name'] == own_work['name']


def test_an_old_history_is_judged_on_its_busiest_co_tenant():
    """A history written before other_cpu_pct existed carries the whole-host figure and the
    top other process; the co-tenant's cores against RUN.machine.other_process_max_cores decide."""
    old = _arm('20260930T140500_4it_25pct', cpu_max=None)
    old['host'] = dict(samples=8, cpu_pct_max=97.0, cpu_pct_median=90.0,
                       top_other_process=dict(pid=1, name='chrome.exe', cores=2.5))
    idle = _arm('20260929T060320_4it_25pct', cpu_max=8.0, median=429.3)
    assert arm_cost.price(250, 0.25, [old, idle], max_host_cpu_pct=90.0, max_other_cores=2.0)['refused_loaded_host'] == [old['name']]
    old['host']['top_other_process']['cores'] = 1.5
    assert arm_cost.price(250, 0.25, [old, idle], max_host_cpu_pct=90.0, max_other_cores=2.0)['refused_loaded_host'] == []
