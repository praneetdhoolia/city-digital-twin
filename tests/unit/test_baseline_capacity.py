import gzip
import xml.etree.ElementTree as ET

import pytest

import importlib.util
from pathlib import Path

# the assembly lives with its city (9.204); the functions under test are pure
PATH = Path(__file__).resolve().parents[2] / 'cities/mumbai/build/build_baseline_run_inputs.py'
SPEC = importlib.util.spec_from_file_location('baseline_run_inputs', PATH)
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)
prepare_network = assembly.prepare_network


@pytest.mark.parametrize('road_factor', [1.0, 2.0])
def test_dedicated_flow_and_road_sensitivity_preserve_other_attributes(tmp_path, road_factor):
    source, output, vehicles = [tmp_path / name for name in
                                ('source.xml.gz', 'output.xml.gz', 'vehicles.xml.gz')]
    with gzip.open(source, 'wt') as stream:
        stream.write('''<network><nodes><node id="a" x="0" y="0"/>
        <node id="b" x="1" y="0"/></nodes><links>
        <link id="track" from="a" to="b" length="1" freespeed="10" capacity="120" permlanes="1" modes="rail"/>
        <link id="road" from="b" to="a" length="1" freespeed="10" capacity="600" permlanes="1" modes="car,rail">
        <attributes><attribute name="osm:way:highway" class="java.lang.String">motorway_link</attribute></attributes></link>
        </links></network>''')
    with gzip.open(vehicles, 'wt') as stream:
        stream.write('''<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd">
        <vehicleType id="train"><networkMode networkMode="rail"/>
        <passengerCarEquivalents pce="27.1"/></vehicleType></vehicleDefinitions>''')
    cfg = {'A.baseline.road_mode_exclusions': {},
           'A.baseline.road_capacity_factors': {'motorway_link': road_factor},
           'A.baseline.network_mode_sources': {},
           'A.baseline.dedicated_transit_headway_s': {'rail': 90},
           'A.baseline.transit_mode_aliases': {}, 'A.transit.walk_speed_ms': 1.2}
    original = source.read_bytes()
    audit = prepare_network(source, output, cfg, vehicles)
    links = {x.get('id'): x for x in ET.parse(gzip.open(output)).findall('links/link')}
    assert float(links['track'].get('capacity')) == pytest.approx(1084)
    assert float(links['road'].get('capacity')) == 600 * road_factor
    assert {k: links['road'].get(k) for k in ('length', 'freespeed', 'permlanes', 'from', 'to')} == {
        'length': '1', 'freespeed': '10', 'permlanes': '1', 'from': 'b', 'to': 'a'}
    assert audit['road_capacity_changes'] == ({} if road_factor == 1 else {'motorway_link': 1})
    assert source.read_bytes() == original
    assert audit['dedicated_transit_capacity_changes'] == {'rail': 1}


def test_goods_modes_inherit_only_their_declared_physical_network(tmp_path):
    source, output, vehicles = [tmp_path / name for name in
                                ('source.xml.gz', 'output.xml.gz', 'vehicles.xml.gz')]
    root = ET.Element('network')
    nodes = ET.SubElement(root, 'nodes')
    for index, name in enumerate(('a', 'b', 'c', 'd')):
        ET.SubElement(nodes, 'node', id=name, x=str(index), y='0')
    links = ET.SubElement(root, 'links')
    for name, origin, destination, mode in [('rail1', 'a', 'b', 'rail'), ('rail2', 'b', 'a', 'rail'),
                                          ('road1', 'c', 'd', 'car'), ('road2', 'd', 'c', 'car')]:
        ET.SubElement(links, 'link', id=name, attrib={'from': origin, 'to': destination,
            'length': '100', 'freespeed': '10', 'capacity': '600', 'permlanes': '1', 'modes': mode})
    with gzip.open(source, 'wb') as stream:
        stream.write(ET.tostring(root))
    with gzip.open(vehicles, 'wt') as stream:
        stream.write('<vehicleDefinitions/>')
    cfg = {'A.baseline.road_mode_exclusions': {}, 'A.baseline.dedicated_transit_headway_s': {},
           'A.baseline.road_capacity_factors': {},
           'A.baseline.transit_mode_aliases': {}, 'A.transit.walk_speed_ms': 1.2,
           'A.baseline.network_mode_sources': {'truck': 'car', 'freight_rail': 'rail'}}
    prepare_network(source, output, cfg, vehicles)
    modes = {x.get('id'): set(x.get('modes').split(','))
             for x in ET.parse(gzip.open(output)).findall('links/link')}
    assert modes['rail1'] == modes['rail2'] == {'rail', 'freight_rail'}
    assert modes['road1'] == modes['road2'] == {'car', 'truck'}
