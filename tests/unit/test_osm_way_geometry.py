"""Native road topology keeps modes, barriers and grade-separated crossings."""
import gzip
import json

import pytest

from build.osm_way_geometry import build, collect


def network(tmp_path):
    path = tmp_path / 'native.osm.gz'
    with gzip.open(path, 'wt', encoding='utf-8') as stream:
        stream.write('''<osm version="0.6">
          <node id="1" lon="0" lat="0"><tag k="highway" v="traffic_signals"/></node>
          <node id="2" lon="0.001" lat="0"><tag k="barrier" v="gate"/><tag k="access" v="private"/></node>
          <node id="3" lon="0.001" lat="0.001"><tag k="railway" v="level_crossing"/></node>
          <node id="4" lon="0.001" lat="0"/>
          <node id="5" lon="0.002" lat="0"/>
          <way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/>
            <tag k="highway" v="primary"/><tag k="motorcycle" v="no"/><tag k="oneway" v="-1"/></way>
          <way id="11"><nd ref="4"/><nd ref="5"/><tag k="highway" v="footway"/><tag k="layer" v="1"/></way>
          <way id="12"><nd ref="3"/><nd ref="5"/><tag k="highway" v="cycleway"/></way>
          <way id="13"><nd ref="3"/><nd ref="5"/><tag k="railway" v="rail"/></way>
          <way id="14"><nd ref="2"/><nd ref="4"/><nd ref="2"/>
            <tag k="highway" v="pedestrian"/><tag k="area" v="yes"/></way>
          <way id="15"><nd ref="1"/><nd ref="5"/><tag k="proposed:highway" v="service"/></way>
        </osm>''')
    return path


def test_real_shared_nodes_join_but_coincident_nodes_do_not(tmp_path):
    nodes, ways, segments, audit = collect([network(tmp_path)], 'EPSG:3857', feature_key='highway')
    assert audit['nodes'] == 5 and audit['ways'] == 5 and audit['segments'] == 7
    by_way = {r['osm_way_id']: json.loads(r['ordered_node_ids_json']) for r in ways}
    assert set(by_way) == {10, 11, 12, 14, 15}
    assert set(by_way[10]) & set(by_way[12]) == {3}
    assert not set(by_way[10]) & set(by_way[11])
    assert (nodes[1]['longitude_deg'], nodes[1]['latitude_deg']) == (nodes[3]['longitude_deg'], nodes[3]['latitude_deg'])
    assert [(r['from_osm_node_id'], r['to_osm_node_id']) for r in segments if r['osm_way_id'] == 10] == [(1, 2), (2, 3)]


def test_barriers_and_rail_crossings_survive_with_source_tags(tmp_path):
    nodes, ways, _, audit = collect([network(tmp_path)], 'EPSG:3857', feature_key='highway')
    by_node = {r['osm_node_id']: json.loads(r['source_tags_json']) for r in nodes}
    assert by_node[2] == {'access': 'private', 'barrier': 'gate'}
    assert by_node[3] == {'railway': 'level_crossing'}
    assert audit['referenced_node_tags']['barrier'] == {'gate': 1}
    assert audit['referenced_node_tags']['railway'] == {'level_crossing': 1}
    road = next(r for r in ways if r['osm_way_id'] == 10)
    assert json.loads(road['source_tags_json'])['motorcycle'] == 'no'
    assert 'unresolved' in road['model_input_status']


def test_areas_proposals_and_zero_lengths_remain_distinct(tmp_path):
    _, ways, _, audit = collect([network(tmp_path)], 'EPSG:3857', feature_key='highway')
    assert audit['zero_length_segments'] == 2
    assert audit['by_geometry_role'] == {'area_boundary': 1, 'native_way_geometry': 4}
    area = next(r for r in ways if r['osm_way_id'] == 14)
    proposal = next(r for r in ways if r['osm_way_id'] == 15)
    assert area['geometry_role'] == 'area_boundary'
    assert proposal['highway_tag'] == ''
    assert json.loads(proposal['source_tags_json']) == {'proposed:highway': 'service'}


def test_shared_road_rail_nodes_have_identical_coordinates(tmp_path):
    path = network(tmp_path)
    roads = collect([path], 'EPSG:32631', feature_key='highway')[0]
    rail = collect([path], 'EPSG:32631', feature_key='railway')[0]
    road_by_id = {r['osm_node_id']: r for r in roads}
    for node in rail:
        assert node == road_by_id[node['osm_node_id']]


def test_road_build_repeats_and_refuses_unknown_selectors(tmp_path):
    path = network(tmp_path)
    destination = tmp_path / 'output'
    build([path], destination, 'EPSG:32631', feature_key='highway')
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    build([path], destination, 'EPSG:32631', feature_key='highway')
    assert before == {p.name: p.read_bytes() for p in destination.iterdir()}
    with pytest.raises(ValueError, match='Unsupported'):
        collect([path], 'EPSG:32631', feature_key='anything')
