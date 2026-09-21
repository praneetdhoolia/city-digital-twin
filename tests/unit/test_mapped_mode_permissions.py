"""Assembly must not broaden access or remove legal islands in preserved mode."""
import gzip
import xml.etree.ElementTree as ET

import pytest
from build_matsim_run_inputs import check_mapped_mode_coverage, patch_network, patch_network_body


NETWORK = '''<network><nodes>
<node id="a" x="0" y="0"/><node id="b" x="1" y="0"/>
<node id="c" x="2" y="0"/><node id="x" x="4" y="0"/><node id="y" x="5" y="0"/>
</nodes><links>
<link id="one_way" from="a" to="b" length="100" freespeed="10" capacity="1800" permlanes="2" oneway="1" modes="car,walk">
<attributes><attribute name="osm:way:id" class="java.lang.String">101</attribute>
<attribute name="osm:way:highway" class="java.lang.String">residential</attribute>
<attribute name="disallowedNextLinks" class="java.lang.String">restriction-evidence</attribute></attributes></link>
<link id="restricted" from="b" to="c" length="100" freespeed="10" capacity="1800" permlanes="2" oneway="1" modes="car">
<attributes><attribute name="osm:way:id" class="java.lang.String">102</attribute>
<attribute name="osm:way:highway" class="java.lang.String">residential</attribute></attributes></link>
<link id="hire_only" from="c" to="a" length="100" freespeed="10" capacity="1800" permlanes="1" oneway="1" modes="local_hire"/>
<link id="island" from="x" to="y" length="100" freespeed="1" capacity="100" permlanes="1" oneway="1" modes="walk,bike"/>
</links></network>'''


def permissions(xml):
    return {e.get('id'): (e.get('from'), e.get('to'), e.get('modes'))
            for e in ET.fromstring(xml).findall('./links/link')}


def patch(xml=NETWORK, **kwargs):
    return patch_network_body(xml, kwargs.pop('patches', {}), kwargs.pop('drop_turns', False),
                              {'walk': set(), 'bike': set()}, None,
                              mode_access_strategy=kwargs.pop('strategy', 'preserve_mapped'),
                              network_modes=kwargs.pop('network_modes', ['car', 'walk', 'bike', 'local_hire']), **kwargs)


def test_preserves_prohibitions_one_way_permissions_and_disconnected_island():
    result, audit = patch()
    assert result == NETWORK
    assert permissions(result) == permissions(NETWORK)
    assert audit == {'mapped_permission_links_preserved': 4, 'mapped_mode_permission_links:bike': 1,
                     'mapped_mode_permission_links:car': 2, 'mapped_mode_permission_links:local_hire': 1,
                     'mapped_mode_permission_links:walk': 2}
    assert 'truck' not in result and 'nmr_' not in result


@pytest.mark.parametrize('drop_turns', [False, True])
def test_declared_lane_patch_still_applies_without_changing_mode_permissions(drop_turns):
    result, audit = patch(patches={'101': {'fields_changed': 'num_lanes_per_dir',
                                         'field_num_lanes_per_dir_to': '3'}}, drop_turns=drop_turns)
    assert permissions(result) == permissions(NETWORK)
    link = ET.fromstring(result).find('./links/link[@id="one_way"]')
    assert link.get('permlanes') == '3.0'
    assert link.get('capacity') == '2700.0'
    assert audit['num_lanes_per_dir'] == 1
    assert ('restriction-evidence' not in result) == drop_turns


def test_missing_mode_is_refused_instead_of_inventing_car_link_access(tmp_path):
    src, dst = tmp_path/'network.xml.gz', tmp_path/'assembled.xml.gz'
    with gzip.open(src, 'wt', encoding='utf-8') as stream:
        stream.write(NETWORK)
    dst.write_bytes(b'previous input')
    with pytest.raises(ValueError, match='no permitted links.*missing_mode'):
        patch_network(src, dst, {}, False, {}, None, mode_access_strategy='preserve_mapped',
                      network_modes=['missing_mode'])
    assert dst.read_bytes() == b'previous input'


def test_legacy_branch_retains_its_existing_companions_and_reverse_link_policy():
    result, audit = patch_network_body(NETWORK, {}, False, {'walk': set(), 'bike': set()}, 1.25,
                                       mode_access_strategy='legacy_companions',
                                       network_modes=['car', 'walk', 'bike'])
    assert 'truck' in result
    assert audit['nonmotor_reverse_links'] > 0
    assert audit['walk_stripped_unreachable'] > 0
    assert 'mapped_permission_links_preserved' not in audit


@pytest.mark.parametrize('modes', [['car', 'car'], [''], ['car,walk'], [None], 'car'])
def test_invalid_routing_mode_list_is_refused(modes):
    with pytest.raises(ValueError, match='distinct nonempty'):
        patch(network_modes=modes)


def test_unknown_strategy_fails_instead_of_selecting_legacy_rewrites():
    with pytest.raises(ValueError, match='Unknown'):
        patch(strategy='typo')


def test_coverage_reads_valid_xml_without_double_quote_or_attribute_order_assumptions():
    links, counts = check_mapped_mode_coverage(
        "<network><links><link modes='new_mode, walk' to='b' from='a' id='1'/></links></network>",
        ['new_mode', 'walk'])
    assert links == 1 and counts == {'new_mode': 1, 'walk': 1}
