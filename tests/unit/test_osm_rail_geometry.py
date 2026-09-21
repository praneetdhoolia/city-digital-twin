"""Rail geometry preserves native topology across modes, levels and XML inputs."""
import json

import pytest

from build.osm_rail_geometry import build, collect


def source(tmp_path, body, name='source.osm'):
    path = tmp_path/name
    path.write_text('<osm version="0.6">'+body+'</osm>', encoding='utf-8')
    return path


def geometry(tmp_path, extra=''):
    return source(tmp_path, '''
        <node id="1" lon="0" lat="0"><tag k="railway" v="switch"/></node>
        <node id="2" lon="0.001" lat="0"/>
        <node id="3" lon="0.001" lat="0.001"/>
        <node id="4" lon="0.001" lat="0"/>
        <node id="5" lon="0.002" lat="0"/>
        <way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/>
          <tag k="railway" v="rail"/><tag k="oneway" v="-1"/><tag k="gauge" v="1676"/></way>
        <way id="11"><nd ref="4"/><nd ref="5"/>
          <tag k="railway" v="subway"/><tag k="layer" v="1"/></way>
        '''+extra)


def test_native_identity_separates_coincident_crossings_and_preserves_order(tmp_path):
    nodes, ways, segments, audit = collect([geometry(tmp_path)], 'EPSG:3857')
    assert audit['ways'] == 2 and audit['segments'] == 3 and audit['nodes'] == 5
    assert [(r['from_osm_node_id'], r['to_osm_node_id']) for r in segments] == [(1, 2), (2, 3), (4, 5)]
    assert nodes[1]['longitude_deg'] == nodes[3]['longitude_deg']
    assert nodes[1]['osm_node_id'] != nodes[3]['osm_node_id']
    assert json.loads(ways[0]['source_tags_json'])['oneway'] == '-1'
    assert json.loads(nodes[0]['source_tags_json']) == {'railway': 'switch'}
    assert all(r['orientation'] == 'source_node_order_not_operating_direction' for r in segments)
    assert segments[0]['length_projected_m'] == pytest.approx(111.319490793)
    assert ways[0]['length_projected_m'] == pytest.approx(sum(r['length_projected_m'] for r in segments[:2]))


def test_areas_inactive_tracks_and_zero_length_are_retained_without_routing_claim(tmp_path):
    path = geometry(tmp_path, '''
      <way id="12"><nd ref="2"/><nd ref="4"/><nd ref="2"/>
        <tag k="railway" v="platform"/><tag k="area" v="yes"/></way>
      <way id="13"><nd ref="3"/><nd ref="5"/><tag k="disused:railway" v="rail"/></way>''')
    _, ways, segments, audit = collect([path], 'EPSG:3857')
    assert audit['zero_length_segments'] == 2
    assert ways[2]['geometry_role'] == 'area_boundary'
    assert ways[3]['railway_tag'] == ''
    assert json.loads(ways[3]['source_tags_json']) == {'disused:railway': 'rail'}
    assert all('unresolved' in r['model_input_status'] for r in ways)


def test_identical_copies_deduplicate_but_conflicting_copies_fail(tmp_path):
    path = geometry(tmp_path)
    _, _, _, audit = collect([path, path], 'EPSG:3857')
    assert audit['identical_way_copies_deduplicated'] == 2
    assert audit['identical_node_copies_deduplicated'] == 5
    other = source(tmp_path, path.read_text().split('<osm version="0.6">')[1].split('</osm>')[0].replace('v="-1"', 'v="yes"'), 'other.osm')
    with pytest.raises(ValueError, match='Conflicting railway way'):
        collect([path, other], 'EPSG:3857')
    other.write_text(path.read_text().replace('lon="0.002"', 'lon="0.003"'))
    with pytest.raises(ValueError, match='Conflicting railway node'):
        collect([path, other], 'EPSG:3857')


def test_missing_reference_leaves_previous_outputs_untouched(tmp_path):
    output = tmp_path/'output'
    output.mkdir()
    (output/'nodes.csv').write_text('prior')
    path = source(tmp_path, '<way id="1"><nd ref="1"/><nd ref="2"/><tag k="railway" v="rail"/></way>')
    with pytest.raises(ValueError, match='missing native nodes'):
        build([path], output, 'EPSG:3857')
    assert (output/'nodes.csv').read_text() == 'prior'
    assert list(output.iterdir()) == [output/'nodes.csv']


@pytest.mark.parametrize('extra,kind', [
    ('<node id="2" lon="0.001" lat="0"/>', 'node'),
    ('<way id="11"><nd ref="4"/><nd ref="5"/><tag k="railway" v="subway"/><tag k="layer" v="1"/></way>', 'way'),
])
def test_duplicate_ids_within_one_source_are_invalid_even_when_identical(tmp_path, extra, kind):
    with pytest.raises(ValueError, match='Repeated railway '+kind+' ID within one input'):
        collect([geometry(tmp_path, extra)], 'EPSG:3857')


@pytest.mark.parametrize('crs', ['EPSG:4326', 'EPSG:2263'])
def test_geographic_and_nonmetre_output_crs_refused(tmp_path, crs):
    with pytest.raises(ValueError, match='metre axes'):
        collect([geometry(tmp_path)], crs)


def test_projected_crs_changes_only_projected_quantities_and_build_repeats(tmp_path):
    path = geometry(tmp_path)
    a = collect([path], 'EPSG:3857')
    b = collect([path], 'EPSG:32631')
    assert a[2][0]['length_geodesic_m'] == b[2][0]['length_geodesic_m']
    assert a[2][0]['length_projected_m'] != b[2][0]['length_projected_m']
    output = tmp_path/'output'
    build([path], output, 'EPSG:32631')
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    build([path], output, 'EPSG:32631')
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
