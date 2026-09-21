import gzip
import xml.etree.ElementTree as ET

import pytest

from build.repair_transit_order import repair_schedule, shortest_path


def test_repair_keeps_stop_order_and_connected_original_path(tmp_path):
    network = tmp_path / 'network.xml.gz'
    schedule = tmp_path / 'schedule.xml.gz'
    output = tmp_path / 'output.xml.gz'
    with gzip.open(network, 'wt') as stream:
        stream.write('''<network><links>
          <link id="a" from="0" to="1" length="1" modes="bus"/>
          <link id="b" from="1" to="2" length="1" modes="bus"/>
          <link id="c" from="2" to="3" length="1" modes="bus"/>
          <link id="d" from="3" to="1" length="2" modes="bus"/>
          <link id="e" from="3" to="4" length="1" modes="bus"/>
        </links></network>''')
    with gzip.open(schedule, 'wt') as stream:
        stream.write('''<transitSchedule><transitStops>
          <stopFacility id="first" linkRefId="c"/>
          <stopFacility id="second" linkRefId="b"/>
          <stopFacility id="last" linkRefId="e"/>
        </transitStops><transitLine id="l"><transitRoute id="r">
          <transportMode>bus</transportMode><routeProfile>
          <stop refId="first"/><stop refId="second"/><stop refId="last"/>
          </routeProfile><route><link refId="a"/><link refId="b"/>
          <link refId="c"/><link refId="e"/></route>
        </transitRoute></transitLine></transitSchedule>''')
    audit = repair_schedule(schedule, network, output)
    root = ET.parse(gzip.open(output)).getroot()
    assert [x.get('refId') for x in root.findall('.//route/link')] == ['a', 'b', 'c', 'd', 'b', 'c', 'e']
    assert [x.get('refId') for x in root.findall('.//routeProfile/stop')] == ['first', 'second', 'last']
    assert audit['repairs'][0]['added_distance_m'] == 4
    assert audit['repaired_routes'] == 1
    second = tmp_path / 'second.xml.gz'
    assert repair_schedule(output, network, second)['repaired_routes'] == 0
    assert second.read_bytes() == output.read_bytes()

    # A source with zero offsets must not advertise travel faster than its
    # network path. Co-located or reversed source stop IDs do not bypass this.
    with gzip.open(network, 'rt') as stream:
        text = stream.read().replace('modes="bus"', 'modes="bus" freespeed="1"')
    with gzip.open(network, 'wt') as stream:
        stream.write(text)
    timed = tmp_path / 'timed.xml.gz'
    report = repair_schedule(schedule, network, timed,
                             {'speed_ms': {'bus': 2}, 'dwell_s': {'bus': 5}})
    stops = ET.parse(gzip.open(timed)).findall('.//routeProfile/stop')
    assert stops[1].get('arrivalOffset') == '00:00:03'
    assert stops[1].get('departureOffset') == '00:00:08'
    assert stops[2].get('arrivalOffset') == '00:00:10'
    assert report['timing_adjustments'][0]['adjusted_stops'] == 2


def test_unreachable_repair_fails_instead_of_dropping_stop():
    with pytest.raises(ValueError, match='No connected transit repair path'):
        shortest_path({}, 'origin', 'destination')
