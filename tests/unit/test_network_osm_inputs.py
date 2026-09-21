"""Cities may provide one native source or several themed extracts."""
import gzip
from pathlib import Path

import pytest

import city


def test_default_input_order_and_explicit_combined_source(monkeypatch, tmp_path):
    monkeypatch.setattr(city, 'CITY_DIR', str(tmp_path))
    monkeypatch.setattr(city, 'descriptor', lambda: {})
    assert [Path(p).name for p in city.network_osm_inputs()] == [
        'roads.osm', 'railways.osm', 'signals.osm', 'footways.osm']
    monkeypatch.setattr(city, 'descriptor', lambda: {'osm_network_inputs': ['networks/osm/combined.osm.gz']})
    assert city.network_osm_inputs() == [str(tmp_path / 'networks' / 'osm' / 'combined.osm.gz')]


@pytest.mark.parametrize('values', [[], 'network.osm', ['../outside.osm'],
                                   ['network.pbf'], ['networks/osm/x.osm', 'networks/osm/./x.osm'],
                                   ['data/raw/x.osm'], [None]])
def test_invalid_sources_never_fall_back(monkeypatch, tmp_path, values):
    monkeypatch.setattr(city, 'CITY_DIR', str(tmp_path))
    monkeypatch.setattr(city, 'descriptor', lambda: {'osm_network_inputs': values})
    with pytest.raises(city.CityError):
        city.network_osm_inputs()


def test_merger_reads_plain_and_compressed_sources_identically(monkeypatch, tmp_path):
    import build_matsim_network as builder
    plain = tmp_path / 'input.osm'
    compressed = tmp_path / 'input.osm.gz'
    payload = b'<osm><node id="1" lat="0" lon="0"/><way id="2"><nd ref="1"/><tag k="highway" v="steps"/></way><relation id="3"><member type="way" ref="2" role="from"/><tag k="type" v="restriction"/></relation></osm>'
    plain.write_bytes(payload)
    compressed.write_bytes(gzip.compress(payload, mtime=0))
    monkeypatch.setattr(builder, 'OSM_INPUTS', [str(plain)])
    plain_output = tmp_path / 'plain_merged.osm'
    builder.merge_osm(str(plain_output))
    monkeypatch.setattr(builder, 'OSM_INPUTS', [str(compressed)])
    gzip_output = tmp_path / 'gzip_merged.osm'
    builder.merge_osm(str(gzip_output))
    assert gzip_output.read_bytes() == plain_output.read_bytes()


def test_readiness_inventory_includes_declared_native_input(monkeypatch, tmp_path, capsys):
    from registry import check_city
    monkeypatch.setattr(check_city, 'read_json', lambda _: {'artefacts': {}})
    check_city.check_layers(str(tmp_path), 'fixture', {'osm_network_inputs': ['networks/osm/all.osm.gz']})
    assert 'absent - networks/osm/all.osm.gz' in capsys.readouterr().out


def test_access_reader_accepts_compressed_input_and_keeps_source_precedence(monkeypatch, tmp_path):
    import build_matsim_network as builder
    first = b'<osm><node id="1"/><way id="2"><tag k="foot" v=" no "/><tag k="bicycle" v="dismount"/><tag k="name" v="fixture"/></way><way id="3"><tag k="foot" v="yes"/></way></osm>'
    second = b'<osm><way id="2"><tag k="foot" v="yes"/></way><way id="4"><tag k="bicycle" v="no"/></way></osm>'
    plain = tmp_path / 'first.osm'
    zipped = tmp_path / 'first.osm.gz'
    later = tmp_path / 'second.osm.gz'
    plain.write_bytes(first)
    zipped.write_bytes(gzip.compress(first, mtime=0))
    later.write_bytes(gzip.compress(second, mtime=0))
    expected = {'2': {'foot': 'no', 'bicycle': 'dismount'},
                '3': {'foot': 'yes'}, '4': {'bicycle': 'no'}}
    for source in (plain, zipped):
        monkeypatch.setattr(builder, 'OSM_INPUTS', [str(source), str(later)])
        assert builder.osm_access_tags(['foot', 'bicycle']) == expected


def test_osm_stage_needs_neither_java_nor_model_parameters(monkeypatch, tmp_path):
    import build_matsim_network as builder
    import sys
    source = tmp_path / 'native.osm'
    source.write_text('<osm><node id="1" lat="0" lon="0"/></osm>', encoding='utf-8')
    monkeypatch.setattr(builder, 'OSM_INPUTS', [str(source)])
    monkeypatch.setattr(builder, 'WORK', str(tmp_path / 'work'))
    monkeypatch.setattr(sys, 'argv', ['build_matsim_network.py', '--stage', 'osm'])
    def unexpected():
        raise AssertionError('Native XML preparation must not require the model runtime')
    monkeypatch.setattr(builder.tc, 'require', unexpected)
    monkeypatch.setattr(builder._registry, 'load', unexpected)
    builder.main()
    assert (tmp_path / 'work' / 'multimodal.osm').exists()
