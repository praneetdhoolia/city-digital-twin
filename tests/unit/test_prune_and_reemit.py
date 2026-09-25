"""The run-directory tools' decisions: what `prune_run` refuses, what `reemit_config` reads.

`prune_run.prune` deletes a run's `output/ITERS/` - the per-iteration plans,
events and trips tables - and a deletion in the wrong order is how a result
becomes unreproducible in practice. Its refusals are the whole of its safety,
so each is pinned on a run directory built in a temporary path:

  * no `_run.json` or no `_metrics.json` -> skipped, nothing deleted;
  * already pruned -> left alone;
  * `_meta.json` says `running` -> skipped, whatever the records say (a gate
    reader loses its trips table between milestones; ninth report, finding 19);
  * a dry run reports and deletes nothing, and writes no `_pruned.json`;
  * a real prune removes `output/ITERS/` only, keeps every `output_*` file, and
    records what it removed.

`reemit_config.reemit` re-emits a finished run's config through the current
emitter; what it must get right is READING the run - the scenario and day from
`_meta.json`, the run overlay from `_config.json`'s `run:` layer, and each
path the reference config named. The emitter itself is stood in for, so the
test pins what reaches it; `main` returns 0 on IDENTICAL and 1 on a diff.
"""
import json
import shutil

import pytest

import prune_run
import reemit_config


def _run_dir(tmp_path, records=('_run.json', '_metrics.json'), meta=None):
    run = tmp_path / 'run1'
    iters = run / 'output' / 'ITERS' / 'it.10'
    iters.mkdir(parents=True)
    (iters / '10.trips.csv.gz').write_bytes(b'x' * 1000)
    (run / 'output' / 'output_trips.csv.gz').write_bytes(b'y' * 10)
    for r in records:
        (run / r).write_text('{}', encoding='utf-8')
    if meta is not None:
        (run / '_meta.json').write_text(json.dumps(meta), encoding='utf-8')
    return run


@pytest.mark.parametrize('records, missing', [
    (('_metrics.json',), '_run.json'),
    (('_run.json',), '_metrics.json'),
    ((), '_run.json, _metrics.json'),
])
def test_prune_refuses_a_run_without_its_records(tmp_path, records, missing):
    run = _run_dir(tmp_path, records=records)
    assert prune_run.prune(str(run)) == ('skipped: no %s' % missing, 0)
    assert (run / 'output' / 'ITERS').is_dir()


def test_prune_refuses_a_running_run(tmp_path):
    run = _run_dir(tmp_path, meta={'status': 'running'})
    assert prune_run.prune(str(run)) == ('skipped: the run is still running', 0)
    assert (run / 'output' / 'ITERS').is_dir()
    assert not (run / '_pruned.json').exists()


def test_prune_does_not_prune_twice(tmp_path):
    run = _run_dir(tmp_path, meta={'status': 'completed'})
    (run / '_pruned.json').write_text('{}', encoding='utf-8')
    assert prune_run.prune(str(run)) == ('already pruned', 0)
    assert (run / 'output' / 'ITERS').is_dir()


def test_prune_dry_run_deletes_nothing(tmp_path):
    run = _run_dir(tmp_path, meta={'status': 'completed'})
    status, freed = prune_run.prune(str(run), dry_run=True)
    assert status.startswith('would free')
    assert freed == 1000
    assert (run / 'output' / 'ITERS' / 'it.10' / '10.trips.csv.gz').exists()
    assert not (run / '_pruned.json').exists()


def test_prune_removes_only_the_iteration_scratch_and_records_it(tmp_path):
    # an unreadable _meta.json is not a refusal: the records decide
    run = _run_dir(tmp_path)
    (run / '_meta.json').write_text('not json', encoding='utf-8')
    status, freed = prune_run.prune(str(run))
    assert status.startswith('freed') and freed == 1000
    assert not (run / 'output' / 'ITERS').exists()
    assert (run / 'output' / 'output_trips.csv.gz').exists()
    record = json.loads((run / '_pruned.json').read_text(encoding='utf-8'))
    assert record['run'] == 'run1'
    assert record['removed'] == [{'path': 'output/ITERS', 'bytes': 1000}]
    assert record['bytes_freed'] == 1000
    assert record['produced_by'] == 'src/run/prune_run.py'


def test_prune_with_no_scratch_writes_no_record(tmp_path):
    run = _run_dir(tmp_path, meta={'status': 'completed'})
    shutil.rmtree(run / 'output' / 'ITERS')
    assert prune_run.prune(str(run)) == ('nothing to prune', 0)
    assert not (run / '_pruned.json').exists()


# --------------------------------------------------------------------------
# reemit_config
# --------------------------------------------------------------------------
CONFIG = '''<config>
  <module name="controler">
    <param name="outputDirectory" value="results/raw/run1/output" />
  </module>
  <module name="network">
    <param name="inputNetworkFile" value="schedules/S0/network.xml.gz" />
  </module>
  <module name="plans">
    <param name="inputPlansFile" value="plans_25pct.xml.gz" />
  </module>
  <module name="transit">
    <param name="transitScheduleFile" value="schedules/S0/schedule.xml.gz" />
    <param name="vehiclesFile" value="schedules/S0/transit_vehicles.xml.gz" />
  </module>
  <module name="vehicles">
    <param name="vehiclesFile" value="mode_vehicles.xml" />
  </module>
</config>
'''


def test_param_reads_one_module_s_parameter():
    assert reemit_config.param(CONFIG, 'transit', 'vehiclesFile') == \
        'schedules/S0/transit_vehicles.xml.gz'
    # the same parameter name in another module is a different value
    assert reemit_config.param(CONFIG, 'vehicles', 'vehiclesFile') == 'mode_vehicles.xml'
    assert reemit_config.param(CONFIG, 'parking', 'priceFile') is None


class _Cfg(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)


@pytest.fixture
def reemit_run(tmp_path, monkeypatch):
    run = tmp_path / 'run1'
    run.mkdir()
    (run / '_meta.json').write_text(json.dumps({'scenario': 'S0', 'day': 'WEEKDAY'}),
                                    encoding='utf-8')
    (run / '_config.json').write_text(json.dumps(
        {'layers': ['registry', 'scenario:S0', 'day:WEEKDAY', 'run:arm_f37']}),
        encoding='utf-8')
    (run / 'config.xml').write_text(CONFIG, encoding='utf-8')
    seen = {}

    def resolve(scenario, day, overlay, sets):
        seen['resolve'] = (scenario, day, overlay, sets)
        return _Cfg({'RUN.sample.fraction': 0.25,
                     'B.hired_fleet.representation': 'absent'})

    def config_runtime(cfg, scoring, day, paths):
        seen['runtime'] = (scoring, day, dict(paths))
        return 'runtime'

    def emit(tool, cfg, runtime):
        seen['emit'] = (tool, runtime)
        return seen.get('emitted', CONFIG)

    monkeypatch.setattr(reemit_config.run_matsim, 'resolve', resolve)
    monkeypatch.setattr(reemit_config.run_matsim, 'purpose_share_for', lambda cfg: 'shares')
    monkeypatch.setattr(reemit_config.bi, 'c1_scoring', lambda cfg, share: ('scoring', share))
    monkeypatch.setattr(reemit_config.bi, 'config_runtime', config_runtime)
    monkeypatch.setattr(reemit_config.param_config, 'emit', emit)
    monkeypatch.setattr(reemit_config.results_store, 'resolve',
                        lambda name: str(run) if name == 'run1' else None)
    return run, seen


def test_reemit_reads_the_run_s_own_scenario_overlay_and_paths(reemit_run):
    run, seen = reemit_run
    reference, emitted = reemit_config.reemit(str(run))
    assert reference == CONFIG and emitted == CONFIG
    assert seen['resolve'] == ('S0', 'WEEKDAY', 'arm_f37', {})
    scoring, day, paths = seen['runtime']
    assert scoring == ('scoring', 'shares') and day == 'WEEKDAY'
    assert paths == {
        'fraction': 0.25,
        'output': 'results/raw/run1/output',
        'network': 'schedules/S0/network.xml.gz',
        'plans': 'plans_25pct.xml.gz',
        'schedule': 'schedules/S0/schedule.xml.gz',
        'vehicles': 'schedules/S0/transit_vehicles.xml.gz',
        'mode_vehicles': 'mode_vehicles.xml',
    }
    assert seen['emit'] == ('matsim', 'runtime')


def test_reemit_without_a_run_overlay_passes_none(reemit_run):
    run, seen = reemit_run
    (run / '_config.json').write_text(json.dumps({'layers': ['registry']}),
                                      encoding='utf-8')
    reemit_config.reemit(str(run))
    assert seen['resolve'][2] is None


def test_main_returns_zero_on_identical_and_one_on_a_diff(reemit_run, capsys):
    run, seen = reemit_run
    assert reemit_config.main(['--run', 'run1']) == 0
    assert 'IDENTICAL' in capsys.readouterr().out
    seen['emitted'] = CONFIG.replace('plans_25pct', 'plans_10pct')
    assert reemit_config.main(['--run', 'run1']) == 1
    out = capsys.readouterr().out
    assert out.startswith('DIFFERS')
    assert '+    <param name="inputPlansFile" value="plans_10pct.xml.gz" />' in out


def test_main_refuses_an_unknown_run(reemit_run):
    with pytest.raises(SystemExit):
        reemit_config.main(['--run', 'no-such-run'])
