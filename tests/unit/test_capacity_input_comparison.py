import gzip
import json

import pytest

import compare_capacity_inputs as reader


@pytest.mark.parametrize('fault', [None, 'speed', 'period', 'schedule'])
def test_capacity_pair_refuses_unrelated_physical_changes(tmp_path, monkeypatch, fault):
    field = 'capacity_factors'
    for name, capacity, factor in [('control', 600, 1), ('candidate', 1200, 2)]:
        directory = tmp_path / name
        directory.mkdir()
        (directory / '_baseline_inputs.json').write_text(json.dumps({'plans': 'same', 'network': 'same'}))
        (directory / '_config.json').write_text(json.dumps({'values': {field: {'tertiary': factor}, 'other': 1}}))
        (directory / 'vehicles.xml').write_text('<vehicleDefinitions/>')
        (directory / 'transitSchedule.xml.gz').write_bytes(
            b'changed' if name == 'candidate' and fault == 'schedule' else b'same immutable schedule bytes')
        speed = 20 if name == 'candidate' and fault == 'speed' else 10
        period = '02:00:00' if name == 'candidate' and fault == 'period' else '01:00:00'
        with gzip.open(directory / 'network.xml.gz', 'wt') as stream:
            stream.write(f'''<network><nodes><node id="a" x="0" y="0"/><node id="b" x="1" y="0"/></nodes>
            <links capperiod="{period}"><link id="road" from="a" to="b" capacity="{capacity}" freespeed="{speed}">
            <attributes><attribute name="osm:way:highway" class="java.lang.String">tertiary</attribute></attributes></link>
            <link id="nmr_road" from="b" to="a" capacity="{capacity}" freespeed="1"/></links></network>''')
    monkeypatch.setattr(reader.results_store, 'resolve_or_die', lambda name: tmp_path / name)
    monkeypatch.setattr(reader.results_store, 'processed_dir', lambda name: tmp_path / 'reports' / name)
    if fault:
        with pytest.raises(ValueError):
            reader.compare('control', 'candidate', field)
    else:
        reader.compare('control', 'candidate', field)
        report = json.loads((tmp_path / 'reports/candidate/_capacity_input_comparison.json').read_text())
        assert report['verified_capacity_only']
        assert report['changed_link_capacities_by_class'] == {'tertiary': 1, 'inherited_reverse_active_link': 1}
