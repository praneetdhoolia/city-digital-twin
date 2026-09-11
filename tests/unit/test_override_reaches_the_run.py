"""A run overlay that changes nothing the run reads is refused, and the mode
constants reach the run from the registry (eighth project report, 11 Sep 2026).

No registry field carries a stage, so the resolver admitted any field into a
run overlay on membership alone. Two consequences were measured this pass:
`A.parking.search_min_max` is baked into the run inputs at assembly, so an
overlay moving it was recorded as moved and executed the base; and the nine
`C.asc.*` constants reached the emitted config through `params/C1_parameters.json`,
a table built from the registry, so `--config-set C.asc.bus=...` — which the
calibrator's stage table classes as run-time realisable — changed nothing. The
ASC contraction test built at 9.160 would have measured that nothing.

The launcher now tests the exact question with the emitted artefacts in hand:
put back to its registry value, does the key change the config or the vehicle
types? These tests drive that function on real resolutions with placeholder
paths, so no plans are sampled and nothing is launched.
"""
import json
import os
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (os.path.join(REPO, 'src'), os.path.join(REPO, 'src', 'run')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import registry  # noqa: E402
import run_matsim as rm  # noqa: E402
from registry import param_config  # noqa: E402

SIG = {k: '%s.xml.gz' % k for k in ('signal_systems', 'signal_groups', 'signal_control',
                                     'lanes', 'ambertimes', 'change_events')}


def _emitted(cfg, day='WEEKDAY'):
    bi = rm.build_inputs
    scoring = bi.scoring_from_c1(cfg, json.load(open(bi.PARAMS, encoding='utf-8')),
                                 rm.purpose_share())
    paths = dict(output='o', network='n.xml.gz', plans='p.xml.gz', schedule='s.xml.gz',
                 vehicles='v.xml.gz', mode_vehicles='mv.xml', parking_prices='pp.tsv',
                 fraction=cfg.get('RUN.sample.fraction'), **SIG)
    runtime = bi.config_runtime(cfg, scoring, day, paths)
    text = param_config.emit('matsim', cfg, runtime)
    with tempfile.TemporaryDirectory() as td:
        veh = bi.write_mode_vehicles(os.path.join(td, 'vehicles.xml'), cfg)
        veh_text = open(veh, encoding='utf-8').read()
    return scoring, paths, dict(config=text, vehicles=veh_text)


def _load(**extra):
    return registry.load(scenario='S2', day='WEEKDAY', run='f33_baseline_25pct', set=extra)


@pytest.mark.skipif(not os.path.exists(os.path.join(REPO, 'cities', 'newcastle', 'params', 'C1_parameters.json')),
                    reason='needs the built C1 params table')
class TestOverrideReachesTheRun:

    def test_an_overlay_with_only_run_keys_is_allowed(self):
        cfg = _load()
        scoring, paths, em = _emitted(cfg)
        rm.refuse_unrealised_overrides(cfg, scoring, 'WEEKDAY', paths, em)

    def test_a_field_baked_at_assembly_is_refused_by_name(self):
        cfg = _load(**{'A.parking.search_min_max': 9.0})
        scoring, paths, em = _emitted(cfg)
        with pytest.raises(SystemExit) as e:
            rm.refuse_unrealised_overrides(cfg, scoring, 'WEEKDAY', paths, em)
        assert 'A.parking.search_min_max' in str(e.value)
        assert 'RECORD a change it cannot EXECUTE' in str(e.value)

    def test_a_mode_constant_reaches_the_run(self):
        """`C.asc.bus` from the registry, not from the built C1 table."""
        cfg = _load(**{'C.asc.bus': -1.5})
        scoring, paths, em = _emitted(cfg)
        rm.refuse_unrealised_overrides(cfg, scoring, 'WEEKDAY', paths, em)
        assert scoring['modes']['bus']['constant'] == -1.5
        assert 'value="-1.5"' in em['config']

    def test_the_shipped_constants_equal_the_built_table(self):
        """The change is byte-neutral for the shipped values: the C1 table was
        written from the same registry."""
        bi = rm.build_inputs
        cfg = _load()
        scoring, _, _ = _emitted(cfg)
        c1 = json.load(open(bi.PARAMS, encoding='utf-8'))['asc']
        from asc_fields import ASC_FIELDS
        for name, key in ASC_FIELDS:
            assert abs(float(cfg.get(key)) - c1[name][0]) < 1e-12, (name, key)

    def test_a_vehicle_type_field_reaches_the_run(self):
        cfg = _load(**{'B.freight.pce': 2.5})
        scoring, paths, em = _emitted(cfg)
        rm.refuse_unrealised_overrides(cfg, scoring, 'WEEKDAY', paths, em)
