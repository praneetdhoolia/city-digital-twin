"""`measure_bound_trips.held_tour_spill`: the other trips of a tour holding a
held ride trip, by executed main mode and routing mode, beside ride tours and
tours with no ride; and `iteration_trips.trip_routing_modes`, which supplies
the routing mode only the experienced plans carry."""
import gzip


import iteration_trips
import measure_bound_trips as mbt


def _t(person, n, start, main, metres):
    return {'person': person, 'trip_number': str(n), 'start_activity_type': start,
            'main_mode': main, 'traveled_distance': str(metres)}


TRIPS = [
    # a: tour 1 = trips 1-3 (trip 1 held ride), tour 2 = trip 4-5 (no ride)
    _t('a', 1, 'home', 'ride', 4000),
    _t('a', 2, 'education', 'walk', 3000),
    _t('a', 3, 'other', 'walk', 1000),
    _t('a', 4, 'home', 'car', 6000),
    _t('a', 5, 'work', 'car', 6000),
    # b: one tour with a ride trip that is not held
    _t('b', 1, 'home', 'ride', 2000),
    _t('b', 2, 'work', 'pt', 8000),
    # v: a visitor is not a resident
    _t('v', 1, 'home', 'walk', 500),
]
ATTRS = {'a': {'subpopulation': 'person', 'heldRideTrips': '1', 'carAvail': 'never'},
         'b': {'subpopulation': 'person', 'carAvail': 'always'},
         'v': {'subpopulation': 'visitor'}}
ROUTING = {('a', 1): 'ride', ('a', 2): 'pt', ('a', 3): 'walk', ('a', 4): 'car',
           ('a', 5): 'car', ('b', 1): 'ride', ('b', 2): 'pt'}


def test_the_held_tour_spill_counts_the_other_trips():
    out = mbt.held_tour_spill(TRIPS, ATTRS, ROUTING)
    held = out['held_ride_tour']
    assert held['trips'] == 2                            # the held trip excluded
    assert held['by_main_and_routing_mode']['walk|pt'] == dict(
        trips=1, share_pct=50.0, mean_km=3.0)            # pt answered with a walk
    assert held['by_main_and_routing_mode']['walk|walk']['mean_km'] == 1.0
    assert held['by_car_availability'] == {'never': 2}
    assert out['ride_tour']['trips'] == 2
    assert out['no_ride_tour']['trips'] == 2
    assert out['no_ride_tour']['by_main_and_routing_mode']['car|car']['share_pct'] == 100.0


def test_without_plans_the_routing_mode_is_unknown():
    out = mbt.held_tour_spill(TRIPS, ATTRS, None)
    assert set(out['held_ride_tour']['by_main_and_routing_mode']) == {'walk|unknown'}


PLANS = '''<?xml version="1.0" encoding="utf-8"?>
<population>
	<person id="a">
		<attributes>
			<attribute name="subpopulation" class="java.lang.String">person</attribute>
		</attributes>
		<plan score="1.0" selected="yes">
			<activity type="home" link="1" x="0" y="0" end_time="08:00:00" >
			</activity>
			<leg mode="walk" dep_time="08:00:00">
				<attributes>
					<attribute name="routingMode" class="java.lang.String">pt</attribute>
				</attributes>
				<route type="generic" start_link="1" end_link="2" distance="3000.0"></route>
			</leg>
			<activity type="education" link="2" x="0" y="0" end_time="15:00:00" >
			</activity>
			<leg mode="non_network_walk" dep_time="15:00:00">
				<attributes>
					<attribute name="routingMode" class="java.lang.String">car</attribute>
				</attributes>
			</leg>
			<activity type="car interaction" link="2" x="0" y="0" end_time="15:00:00" >
			</activity>
			<leg mode="car" dep_time="15:00:00">
				<attributes>
					<attribute name="routingMode" class="java.lang.String">car</attribute>
				</attributes>
			</leg>
			<activity type="home" link="1" x="0" y="0" >
			</activity>
		</plan>
	</person>
	<person id="z">
		<plan selected="yes">
			<activity type="home" link="1" x="0" y="0" end_time="08:00:00" >
			</activity>
			<leg mode="walk" dep_time="08:00:00">
				<attributes>
					<attribute name="routingMode" class="java.lang.String">walk</attribute>
				</attributes>
			</leg>
			<activity type="work" link="1" x="0" y="0" >
			</activity>
		</plan>
	</person>
</population>
'''


def test_routing_modes_are_read_per_trip_from_the_plans(tmp_path):
    p = tmp_path / 'x.experienced_plans.xml.gz'
    with gzip.open(p, 'wt', encoding='utf-8') as fh:
        fh.write(PLANS)
    assert iteration_trips.trip_routing_modes(str(p)) == {
        ('a', 1): 'pt', ('a', 2): 'car', ('z', 1): 'walk'}
    assert iteration_trips.trip_routing_modes(str(p), {'a'}) == {
        ('a', 1): 'pt', ('a', 2): 'car'}


def test_tours_are_cut_at_home():
    tours = mbt._tours([_t('a', 1, 'home', 'x', 0), _t('a', 2, 'work', 'x', 0),
                        _t('a', 3, 'home', 'x', 0)])
    assert [len(t) for t in tours] == [2, 1]
