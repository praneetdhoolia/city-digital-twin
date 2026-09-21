"""Directional road evidence must not create lanes or discard speed qualifiers."""
import json
from pathlib import Path

import pytest

from build.osm_road_attributes import resolve

UNIT_CASES = json.loads((Path(__file__).parents[1] / 'fixtures' /
                        'osm_transport_units.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('oneway,side', [('yes', 'forward'), ('-1', 'backward')])
def test_oneway_total_follows_native_orientation(oneway, side):
    r = resolve({'oneway': oneway, 'lanes': '3'})
    assert r['lanes_resolved_' + side + '_count'] == 3
    assert r['lanes_resolved_' + ('backward' if side == 'forward' else 'forward') + '_count'] == 0
    assert r['lanes_status'] == 'oneway_total_identity'


@pytest.mark.parametrize('total', ['1', '2', '3', '4'])
def test_two_way_total_is_never_halved(total):
    r = resolve({'oneway': 'no', 'lanes': total})
    assert r['lanes_total_count'] == int(total)
    assert r['lanes_resolved_forward_count'] is None
    assert r['lanes_resolved_backward_count'] is None


def test_explicit_asymmetry_and_shared_lane_preserved():
    r = resolve({'oneway': 'no', 'lanes': '4', 'lanes:forward': '2',
                 'lanes:backward': '1', 'lanes:both_ways': '1'})
    assert (r['lanes_resolved_forward_count'], r['lanes_resolved_backward_count'], r['lanes_shared_count']) == (2, 1, 1)


@pytest.mark.parametrize('tags', [
    {'lanes': '3', 'lanes:forward': '2', 'lanes:backward': '2'},
    {'lanes': '4', 'lanes:forward': '1', 'lanes:backward': '1', 'lanes:both_ways': '0'},
    {'oneway': 'yes', 'lanes': '2', 'lanes:forward': '1'},
    {'oneway': '-1', 'lanes': '2', 'lanes:forward': '1'},
    {'lanes': '2;3'},
])
def test_conflicts_do_not_produce_directional_lane_inputs(tags):
    r = resolve(tags)
    assert r['lanes_status'] == 'conflict_or_invalid'
    assert r['lanes_resolved_forward_count'] is None
    assert r['lanes_resolved_backward_count'] is None


def test_contraflow_prevents_assigning_total_to_one_direction():
    r = resolve({'oneway': 'yes', 'lanes': '3', 'oneway:bus': 'no'})
    assert r['lanes_resolved_forward_count'] is None
    assert r['lane_or_direction_qualifier_keys'] == 'oneway:bus'


def test_missing_direction_is_not_an_observed_two_way_road():
    assert resolve({'highway': 'residential'})['oneway_direction'] == 'unresolved'
    assert resolve({'highway': 'motorway_link'})['oneway_direction'] == 'unresolved'
    assert resolve({'highway': 'motorway'})['oneway_basis'] == 'implied_by_osm_definition'
    assert resolve({'highway': 'motorway', 'oneway': 'no'})['oneway_direction'] == 'both'


def test_units_and_directional_precedence():
    r = resolve({'maxspeed': '20 mph', 'maxspeed:forward': '30', 'width': "12'6\""})
    assert r['speed_limit_forward_kmh'] == 30
    expected = next(value for key, raw, value, unit in UNIT_CASES if key == 'maxspeed' and raw == '20 mph')
    assert r['speed_limit_backward_kmh'] == pytest.approx(expected)
    assert r['width_m'] == pytest.approx(3.81)
    r = resolve({'maxspeed': '50', 'maxspeed:forward': 'signals'})
    assert r['speed_limit_forward_kmh'] is None
    assert r['speed_limit_forward_status'] == 'unresolved'


def test_conditions_and_vehicle_specific_limits_remain_visible():
    tags = {'maxspeed': '60', 'maxspeed:hgv': '40', 'maxspeed:conditional': '30 @ (wet)',
            'oneway': 'reversible', 'lanes': '2'}
    r = resolve(tags)
    assert r['oneway_direction'] == 'unresolved'
    assert r['unresolved_speed_qualifier_keys'] == 'maxspeed:conditional;maxspeed:hgv'
    assert json.loads(r['source_tags_json']) == tags
