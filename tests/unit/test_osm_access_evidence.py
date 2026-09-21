"""Tag inheritance must not erase modal exceptions or imply public through access."""
import pytest

from build.osm_access_evidence import ACCESS_CHAINS, access_tags, resolve


def test_private_way_can_have_public_pedestrian_exception():
    tags = {'access': 'private', 'foot': 'yes'}
    assert resolve(tags, 'foot')['baseline_interpretation'] == 'tagged_public_access'
    assert resolve(tags, 'motorcar')['baseline_interpretation'] == 'requires_user_purpose_or_permission'


def test_bus_exception_does_not_grant_motorcycles_or_cars():
    tags = {'access': 'no', 'psv': 'yes', 'bus': 'no'}
    assert resolve(tags, 'taxi')['baseline_raw_value'] == 'yes'
    assert resolve(tags, 'bus')['baseline_source_key'] == 'bus'
    assert resolve(tags, 'bus')['baseline_raw_value'] == 'no'
    assert resolve(tags, 'motorcycle')['baseline_raw_value'] == 'no'
    assert resolve(tags, 'motorcar')['baseline_raw_value'] == 'no'


def test_vehicle_restriction_does_not_include_pedestrians():
    tags = {'access': 'yes', 'vehicle': 'no'}
    assert resolve(tags, 'foot')['baseline_raw_value'] == 'yes'
    assert all(resolve(tags, c)['baseline_raw_value'] == 'no' for c in ACCESS_CHAINS if c != 'foot')


@pytest.mark.parametrize('value', ['unknown', '', 'yes;no', 'private19.0,73.0', 'bus', 'conditional'])
def test_invalid_specific_value_never_falls_back_to_general_grant(value):
    r = resolve({'access': 'yes', 'motorcycle': value}, 'motorcycle')
    assert r['baseline_source_key'] == 'motorcycle'
    assert r['baseline_interpretation'] == 'unrecognised_or_ambiguous_value'


@pytest.mark.parametrize('value', ['private', 'destination', 'customers', 'delivery', 'permit', 'military'])
def test_restricted_purpose_is_not_a_generic_allow_or_deny(value):
    assert resolve({'access': value}, 'motorcar')['baseline_interpretation'] == 'requires_user_purpose_or_permission'


def test_parent_qualifier_survives_specific_static_permission():
    tags = {'access:conditional': 'no @ (Mo-Fr 08:00-10:00)', 'bus': 'yes'}
    r = resolve(tags, 'bus')
    assert r['qualified_tags'] == {'access:conditional': tags['access:conditional']}
    assert r['resolution_status'] == 'qualified_or_scope_review_required'


def test_directional_and_lane_tags_are_retained_without_collapsing():
    tags = {'bicycle': 'yes', 'bicycle:forward': 'no', 'bicycle:lanes': 'no|yes', 'hgv:conditional': 'no @ (wet)'}
    r = resolve(tags, 'bicycle')
    assert r['qualified_tags'] == {'bicycle:forward': 'no', 'bicycle:lanes': 'no|yes'}
    assert r['baseline_raw_value'] == 'yes'


def test_motorcar_scope_does_not_invent_permissions_for_autos_or_trucks():
    for c in ('hgv', 'goods', 'bus', 'auto_rickshaw', 'taxi'):
        r = resolve({'motorcar': 'no'}, c)
        assert r['baseline_interpretation'] == 'not_tagged'
        assert r['scope_warnings']
        assert r['resolution_status'] == 'qualified_or_scope_review_required'
    assert not resolve({'motorcar': 'no'}, 'motorcycle')['scope_warnings']


def test_no_highway_class_or_oneway_default_is_fabricated():
    for c in ACCESS_CHAINS:
        r = resolve({'highway': 'motorway', 'oneway': 'yes'}, c)
        assert r['baseline_interpretation'] == 'not_tagged'
        assert r['simulation_permission_established'] is False


def test_plain_designated_is_ambiguous_but_mode_designation_is_interpretable():
    assert resolve({'access': 'designated'}, 'bus')['baseline_interpretation'] == 'unrecognised_or_ambiguous_value'
    assert resolve({'psv': 'designated'}, 'bus')['baseline_interpretation'] == 'tagged_designated_access'


def test_access_profile_ignores_parking_restrictions_and_keeps_nonstandard_access_qualifiers():
    tags = {'access:hgv': 'no', 'parking:both:access:conditional': 'private @ (Mo-Fr)', 'motor_vehicle': 'yes'}
    assert access_tags(tags) == {'access:hgv': 'no', 'motor_vehicle': 'yes'}
    assert resolve(tags, 'hgv')['resolution_status'] == 'qualified_or_scope_review_required'


def test_unknown_mode_is_refused():
    with pytest.raises(ValueError, match='Unsupported'):
        resolve({'access': 'yes'}, 'invented_vehicle')
