"""`transit_link_delays.py --road` and `--access`: road links ranked by excess
vehicle-hours over free flow from the telemetry payload, and road-vehicle trip
ends per link against the link's own sampled capacity.

A synthetic network of four links (one self-closing, one with no attributes),
a telemetry payload in the [id, volume, typical, mean] form, and a trips table.
"""
import gzip

import pytest

import transit_link_delays as tld

NETWORK = '''<?xml version="1.0" encoding="UTF-8"?>
<network>
	<links>
		<link id="a" from="n0" to="n1" length="100.0" freespeed="10.0" capacity="600.0" permlanes="1.0" oneway="1" modes="car" >
			<attributes>
				<attribute name="osm:way:highway" class="java.lang.String">residential</attribute>
				<attribute name="osm:way:name" class="java.lang.String">Short Street</attribute>
			</attributes>
		</link>
		<link id="b" from="n1" to="n2" length="300.0" freespeed="15.0" capacity="1800.0" permlanes="2.0" oneway="1" modes="car" >
			<attributes>
				<attribute name="osm:way:highway" class="java.lang.String">primary</attribute>
			</attributes>
		</link>
		<link id="c" from="n2" to="n1" length="50.0" freespeed="5.0" capacity="300.0" permlanes="1.0" oneway="1" modes="car" />
		<link id="d" from="n2" to="n3" length="200.0" freespeed="10.0" capacity="1000.0" permlanes="1.0" oneway="1" modes="car" >
			<attributes>
				<attribute name="type" class="java.lang.String">service</attribute>
			</attributes>
		</link>
	</links>
</network>
'''
PAYLOAD = dict(iteration=5, scope='iteration', window_from='00:00:00', window_to='30:00:00',
               tolerance_s=1, min_stretch_m=150,
               links=[['a', 36, 1, 3.0],          # 36 x 2 x 150/10 s = 0.3 h
                      ['b', 72, 1, 2.0],          # 72 x 1 x 300/15 s = 0.4 h
                      ['c', 10, 1, 1.0],          # no delay
                      ['d', 9, 1, 1.5],           # 9 x 0.5 x 200/10 s = 0.025 h
                      ['zz', 5, 1, 4.0]])         # not in the network


@pytest.fixture
def net(tmp_path):
    path = tmp_path / 'net.xml.gz'
    with gzip.open(path, 'wt', encoding='utf-8') as fh:
        fh.write(NETWORK)
    return tld.road_network(str(path))


def test_network_is_parsed_with_class_name_and_capacity(net):
    assert net['a'] == dict(to='n1', length=100.0, freespeed=10.0, capacity=600.0,
                            lanes=1.0, highway='residential', name='Short Street')
    assert net['c']['to'] == 'n1' and 'highway' not in net['c']
    assert tld.road_class(net['d']) == 'service' and tld.road_class(net['c']) == '?'


def test_road_delays_rank_excess_vehicle_hours(net):
    r = tld.road_delays(PAYLOAD, net, top=2)
    assert r['delayed_links'] == 3
    assert r['excess_vehicle_hours_sampled'] == pytest.approx(0.7, abs=0.05)
    assert [l['link'] for l in r['top_links']] == ['b', 'a']
    assert r['top_links'][1]['excess_vehicle_hours'] == pytest.approx(0.3, abs=0.05)
    total = 0.3 + 0.4 + 0.025
    assert r['top_k_share_pct']['10'] == 100.0
    classes = {c['road_class']: c for c in r['by_class']}
    assert classes['primary']['excess_share_pct'] == pytest.approx(100 * 0.4 / total, abs=0.01)
    assert classes['primary']['capacity_per_lane_seen'] == [900.0]
    # traversals count every joined link, delayed or not
    assert classes['residential']['traversals'] == 36
    assert r['top_nodes'][0] == dict(node='n2', excess_vehicle_hours=0.4)
    nodes = {n['node']: n['excess_vehicle_hours'] for n in r['top_nodes']}
    assert nodes['n1'] == pytest.approx(0.3, abs=0.05)


def test_an_old_payload_is_refused(net):
    old = dict(PAYLOAD, tolerance_s=None, links=[['a', 36, 3.0]])
    with pytest.raises(SystemExit, match='predates'):
        tld.road_delays(old, net, top=1)


def _trip(mode, start, end, secs, metres):
    return dict(main_mode=mode, start_link=start, end_link=end,
                trav_time='%02d:%02d:%02d' % (secs // 3600, secs // 60 % 60, secs % 60),
                traveled_distance=str(metres))


def test_access_load_bands_trips_by_the_worse_end(net):
    # link c: capacity 300 x 0.25 = 75 an hour; 450 ends on it need 6 h.
    # link a: 150 an hour; b: 450 an hour; d: 250 an hour.
    trips = ([_trip('car', 'c', 'b', 1200, 4000)] * 225
             + [_trip('taxi', 'b', 'c', 600, 3000)] * 225
             + [_trip('truck', 'a', 'd', 360, 6000)] * 10
             + [_trip('walk', 'c', 'c', 60, 100)] * 1000)      # not a road vehicle
    r = tld.access_load(trips, net, 0.25, top=2)
    assert r['road_vehicle_trips'] == 460
    bands = {b['band']: b for b in r['bands']}
    assert bands['4-12h']['trips'] == 450
    assert bands['4-12h']['mean_time_min'] == 15.0
    assert bands['4-12h']['speed_kmh'] == pytest.approx(3.5 * 1000 * 450 / (900 * 450) * 3.6, abs=0.01)
    assert bands['<1h']['trips'] == 10 and bands['<1h']['speed_kmh'] == 60.0
    assert bands['>=12h']['trips'] == 0
    assert r['offending_by_class'] == [dict(road_class='?', links=1, trip_ends=450)]
    assert r['worst_links'][0] == dict(link='c', road_class='?', capacity=300.0,
                                       trip_ends=450, hours_needed=6.0)


def test_load_bands():
    assert [tld.load_band(h) for h in (0.99, 1, 3.99, 4, 11.99, 12)] == [
        '<1h', '1-4h', '1-4h', '4-12h', '4-12h', '>=12h']
