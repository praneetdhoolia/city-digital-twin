"""Passenger capacity must match the sampled demand, in every XML encoding."""
import gzip
import xml.etree.ElementTree as ET

import pytest
from sample_population import scale_transit_capacity


def scaled(tmp_path, xml, fraction=0.25, floor=1):
    src, dst = tmp_path / 'fleet.xml.gz', tmp_path / 'sample.xml.gz'
    with gzip.open(src, 'wt', encoding='utf-8') as stream:
        stream.write(xml)
    audit = scale_transit_capacity(src, dst, fraction, floor)
    with gzip.open(dst, 'rb') as stream:
        root = ET.parse(stream).getroot()
    return root, audit


@pytest.mark.parametrize('attributes', [
    'seats="100" standingRoomInPersons="900"',
    "standingRoomInPersons='900' seats='100'",
    'seats = "100"\n standingRoomInPersons = "900"',
])
def test_both_components_scale_regardless_of_attribute_layout(tmp_path, attributes):
    root, audit = scaled(tmp_path, '<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd">'
                         '<vehicleType id="train"><capacity '+attributes+'/>'
                         '<length meter="120"/></vehicleType></vehicleDefinitions>')
    capacity = next(e for e in root.iter() if e.tag.endswith('capacity'))
    assert capacity.attrib == {'seats': '25', 'standingRoomInPersons': '225'}
    assert sum(int(v) for v in capacity.attrib.values()) == 250
    assert set(audit) == {('seats', 100, 25), ('standingRoomInPersons', 900, 225)}
    assert next(e for e in root.iter() if e.tag.endswith('length')).get('meter') == '120'


def test_legacy_nested_capacity_and_zero_seats(tmp_path):
    root, audit = scaled(tmp_path, '<vehicleDefinitions><vehicleType id="standing">'
                         '<capacity><seats persons="0"/><standingRoom persons="80"/>'
                         '</capacity></vehicleType></vehicleDefinitions>')
    assert root.find('.//seats').get('persons') == '0'
    assert root.find('.//standingRoom').get('persons') == '20'
    assert audit == [('seats', 0, 0), ('standingRoomInPersons', 80, 20)]


def test_floor_is_applied_only_to_nonzero_components(tmp_path):
    root, _ = scaled(tmp_path, '<vehicleDefinitions><capacity seats="2" '
                     'standingRoomInPersons="0"/></vehicleDefinitions>', 0.01, 1)
    assert root.find('capacity').attrib == {'seats': '1', 'standingRoomInPersons': '0'}


@pytest.mark.parametrize('fraction', [0, -0.1, 1.1, float('nan'), float('inf')])
def test_invalid_fraction_is_rejected(tmp_path, fraction):
    with pytest.raises(ValueError, match='fraction'):
        scaled(tmp_path, '<vehicleDefinitions/>', fraction)


def test_unknown_capacity_cannot_silently_remain_full_size(tmp_path):
    with pytest.raises(ValueError, match='recognised'):
        scaled(tmp_path, '<vehicleDefinitions><capacity passengers="100"/></vehicleDefinitions>')
