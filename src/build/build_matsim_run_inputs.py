#!/usr/bin/env python
"""Assemble a runnable MATSim scenario per (scenario x day type).

Three things have to come together, and each has a constraint attached.

1. **The schedule, filtered to one day type.** Every mapped feed carries all
   three day types at once - S2 has 1,714 routes, 1,231 WEEKDAY + 291 SAT +
   192 SUN, and 4,269 departures against 2,188 weekday GTFS trips. Running the
   unfiltered schedule would put roughly twice the real PT supply on the
   network. The filter works on the **already mapped** schedule, selecting
   `transitRoute` ids by their day-type token, so no feed is ever re-mapped:
   route link sequences are copied through untouched. That matters because
   pt2matsim is not reproducible run to run (DECISIONS.md 3.5) and every
   scenario comparison must sit on one build.

2. **The run network.** It is *not* `networks/matsim/variants/`. Those are
   patched over the base network, which has no mapped transit links. The
   network a scenario actually runs on is its own mapped
   `schedules/<S>/network.xml.gz` - 151,594 links against the base 157,678,
   with 928 artificial transit links added and 7,012 pre-mapping rail
   placeholders removed (all of them pt-mode; no car link is lost). The E1 road
   variant is re-applied on top of that by `osm:way:id`, which every link
   carries, so the variant means the same thing on the run network as it does
   on the base.

3. **Scoring, translated from C1.** C1 is a nested-logit specification and
   MATSim's scoring is not. What does not survive the translation is stated in
   the report rather than quietly dropped.

Nothing here runs a scenario. It writes the inputs a run would consume.
"""

# City-relative paths resolve through src/city.py: `data/...` names a
# location inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', 'src'))
import city as _city  # noqa: E402
import os
import re
import csv
import gzip
import json
import argparse
import collections
import xml.etree.ElementTree as ET

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from det_io import gzip_writer

# Model inputs come from cities/<city>/registry/, not from literals here. Every
# value below carries its units, provenance and either a sweep, a held-fixed rule
# or a derived-from identity there. See DECISIONS.md 15.
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import registry as _registry  # noqa: E402
from registry import param_config as _param_config  # noqa: E402

MATSIM = _city.path('networks/matsim')
PATCHES = _city.path('data/processed/network/A1_road_variant_patches.csv')
# DECISIONS.md 9.84 (issue #21): the P2 elevation layers, read for their node
# elevations so every run-network link can carry a signed grade - matching by
# node identity survives pt2matsim's re-segmentation, where matching whole
# edges (measured) reached only 34.9% of links against 78.6% by node.
ROAD_EDGES = _city.path('data/processed/network/A1_road_edges.csv')
FOOTWAY_EDGES = _city.path('data/processed/network/A6_footway_edges.csv')
E1 = _city.path('scenarios/E1_scenarios.csv')
PARAMS = _city.path('params/C1_parameters.json')
PLANS = _city.path('demand/plans/matsim')
OUT = _city.path('scenarios/matsim')
PARK_PRICE_ZONES = _city.path('data/processed/landuse/A5_parking_price_zones.csv')
PARK_PRICE_FILE = 'parking_prices.tsv'

# The day types come from the city's own descriptor. They were a list literal
# here, which meant a city with a different service week could not be built
# without editing the framework.
DAY_TYPES = list(_city.descriptor()['day_types'])

# NOTHING IS RESOLVED AT IMPORT. Twenty-two values used to be read into module
# constants here, and a value read at import is a value fixed BEFORE the
# scenario, day and run overlays are known - so a run overlay setting one of
# them was accepted by the resolver, recorded in the run's provenance snapshot,
# and could not possibly reach the config. Every read below happens inside a
# function, against the configuration that run actually resolved.


def check_scoring_order(cfg):
    """The one ordering that is a finding rather than an incidental.

    Cycling time is dearer per hour than walking time in every calibrated model.
    The model had it inverted (walk 2.0, bike 1.3), and that inversion conceded
    every short trip to bike (DECISIONS.md 9.28). Checked against the resolved
    configuration, so an overlay cannot reintroduce it either.
    """
    walk = cfg.get('C.time_weights.beta_walk_mode')
    bike = cfg.get('C.time_weights.beta_bike_mode')
    if bike < walk:
        raise SystemExit('C.time_weights.beta_bike_mode (%s) must be >= '
                         'beta_walk_mode (%s): cycling time is dearer per hour than '
                         'walking time in every calibrated model, and inverting that '
                         'ordering is the DECISIONS.md 9.28 defect' % (bike, walk))

LINK_BLOCK_RE = re.compile(r'<link\b.*?(?:/>|</link>)', re.S)
WAY_ID_RE = re.compile(r'name="osm:way:id"[^>]*>(\d+)<')
ATTR_RE = re.compile(r'(\w[\w:]*)="([^"]*)"')


# A route id carries its day type as a delimited token. The era and scenario
# feeds namespace it with a dot (`nisc001:WEEKDAY.2302960`); the S1 shuttle and
# S3 BRT that this script generates use underscores (`S1SHUTTLE_WEEKDAY_0_1`).
# Matching only the dotted form silently dropped both from every day type -
# which would have run S1 with no shuttle and S3 with no BRT, i.e. each
# scenario without the intervention it exists to test.
# built from the CITY's own day-type vocabulary: a fixed WEEKDAY|SAT|SUN
# alternation could never recognise another city's trip-id tokens
DAY_TOKEN_RE = re.compile(r'(?:^|[.:_])(%s)(?:[._]|$)'
                          % '|'.join(re.escape(d) for d in DAY_TYPES))

# MATSim picks its reader from the doctype, so a schedule written without one
# cannot be loaded at all - the parser fails at line 2 with a null delegate.
# ElementTree drops the doctype on a parse/write round trip, so it is written
# back explicitly. See DECISIONS.md 9.4.
XML_DECL = b"<?xml version='1.0' encoding='utf-8'?>\n"
SCHEDULE_DOCTYPE = (b'<!DOCTYPE transitSchedule SYSTEM '
                    b'"http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n')


def day_of_route(route_id):
    m = DAY_TOKEN_RE.search(route_id)
    return m.group(1) if m else None


def split_schedule(src_dir, dst_dir, day, cfg, src_schedule=None):
    """Filter a mapped schedule to one day type. No re-mapping, ever.

    `src_schedule` names an alternative DERIVED schedule to filter (the
    signals/dwell transform of the same mapped build - never a re-map): under
    `A.signals.representation == explicit_signals` the caller passes the
    scenario's `transitSchedule_signals.xml.gz`, which carries the dwell
    transform (#74) and the implicit-delay removal (#73) over the identical
    route link sequences.

    Returns counts so the caller can assert that link sequences were copied
    rather than regenerated.
    """
    os.makedirs(dst_dir, exist_ok=True)
    src = src_schedule or os.path.join(src_dir, 'transitSchedule.xml.gz')
    with gzip.open(src, 'rb') as f:
        tree = ET.parse(f)
    root = tree.getroot()

    kept_routes = dropped_routes = 0
    kept_dep = dropped_dep = 0
    mixed_routes = 0
    vehicles_used = set()
    stops_served = set()
    transport_modes = set()   # the kept routes' own scheduled submodes
    for line in list(root.findall('transitLine')):
        for route in list(line.findall('transitRoute')):
            # Filter DEPARTURES, not routes. pt2matsim groups trips into a
            # transitRoute by stop sequence, not by service, so a route is not
            # day-type homogeneous: 233 of S2's 1,714 routes carry departures
            # from more than one service. Keying the filter on the route id put
            # 1,261 of 4,269 departures (29.5%) in the wrong day type and
            # removed the light rail from every weekday run outright, because
            # both of its routes happen to be named after a weekend trip.
            # See DECISIONS.md 9.9.
            deps = route.find('departures')
            keep_here = []
            for dep in list(deps.findall('departure') if deps is not None else []):
                if day_of_route(dep.get('id', '')) == day:
                    keep_here.append(dep)
                else:
                    deps.remove(dep)
                    dropped_dep += 1
            if not keep_here:
                line.remove(route)
                dropped_routes += 1
                continue
            if day_of_route(route.get('id', '')) != day:
                mixed_routes += 1
            kept_routes += 1
            kept_dep += len(keep_here)
            tm = (route.findtext('transportMode') or '').strip()
            if tm:
                transport_modes.add(tm)
            for stop in route.findall('./routeProfile/stop'):
                stops_served.add(stop.get('refId'))
            for dep in keep_here:
                v = dep.get('vehicleRefId')
                if v:
                    vehicles_used.add(v)
        if not line.findall('transitRoute'):
            root.remove(line)

    # Under the per_submode representation (9.78) every kept route's
    # transportMode must be in the declared vocabulary: SwissRailRaptor's
    # mode mapping hands an unmapped route a NULL passenger mode (a plain
    # map get in RaptorStaticConfig, read from the pinned jar), which is the
    # unpatched-vehicle-type defect class - a metro or cable car in a future
    # feed must fail HERE, by name, not deep in the JVM.
    mapped = pt_passenger_submodes(cfg)
    if mapped:
        stray = sorted(transport_modes - set(mapped))
        if stray:
            raise SystemExit(
                '%s carries transportMode(s) %s outside the declared '
                'RUN.transit.transit_modes vocabulary. Declare them (and '
                'their C1 treatment) before mapping PT submodes '
                '(DECISIONS.md 9.78).' % (src, stray))

    # Dropping two thirds of the routes orphans the stops and the transfer
    # relations that only they used, and SwissRailRaptor dereferences a null
    # array on the first of those it meets - so the schedule has to be left
    # referentially closed, not merely smaller. See DECISIONS.md 9.4.
    facilities = root.find('transitStops')
    dropped_fac = 0
    for fac in list(facilities.findall('stopFacility')):
        if fac.get('id') not in stops_served:
            facilities.remove(fac)
            dropped_fac += 1
    kept_fac = len(facilities.findall('stopFacility'))

    mtt = root.find('minimalTransferTimes')
    kept_rel = dropped_rel = 0
    if mtt is not None:
        for rel in list(mtt.findall('relation')):
            if (rel.get('fromStop') not in stops_served
                    or rel.get('toStop') not in stops_served):
                mtt.remove(rel)
                dropped_rel += 1
        kept_rel = len(mtt.findall('relation'))

    out_sched = os.path.join(dst_dir, 'transitSchedule.xml.gz')
    with gzip_writer(out_sched, text=False) as f:
        f.write(XML_DECL)
        f.write(SCHEDULE_DOCTYPE)
        tree.write(f, encoding='utf-8', xml_declaration=False)

    with gzip.open(os.path.join(src_dir, 'transitVehicles.xml.gz'), 'rb') as f:
        vtree = ET.parse(f)
    vroot = vtree.getroot()
    tag = lambda e: e.tag.split('}')[-1]
    kept_veh = 0
    for veh in list(vroot):
        if tag(veh) != 'vehicle':
            continue
        if veh.get('id') in vehicles_used:
            kept_veh += 1
        else:
            vroot.remove(veh)
    # The mapped fleet is pt2matsim's generic defaults, and every one of them
    # overstates the real vehicle: tram 180 seats against a published 270 total,
    # rail 400 against a 146 two-car set (roughly 2.7x), ferry 250 against 200,
    # bus 70 seats against 44. None of them carried ANY standing room, which
    # left the C1 crowding multipliers inert by construction - crowding cannot
    # bind if nobody can stand (issue 18, DECISIONS.md 9.12, 9.18, 9.21).
    #
    # All four are now corrected from published figures (DECISIONS.md 9.30).
    # Where a published split exists it is used (ferry, bus); where only a total
    # is published the seated share is assumed and swept and the standing room
    # is derived by identity (tram, rail). Nothing here is observed for
    # Newcastle operations - these are manufacturer and operator figures.
    # The type ids are pt2matsim's OWN route-type vocabulary (it names the
    # generic vehicle type for each GTFS route type Bus/Tram/Rail/Ferry), not
    # this feed's - so the keys are tool structure, not a city value. What
    # MUST NOT be silent is a type outside the map (a metro, a cable car):
    # its pt2matsim default capacity would sail through unpatched and leave
    # crowding inert for that mode - the 9.12 defect class - so unpatched
    # types are reported by name below.
    FLEET_CAPACITY = {
        'Tram':  ('A.lightrail.capacity_seated', 'A.lightrail.capacity_standing'),
        'Bus':   ('A.transit.bus_capacity_seated', 'A.transit.bus_capacity_standing'),
        'Ferry': ('A.transit.ferry_capacity_seated', 'A.transit.ferry_capacity_standing'),
        'Rail':  ('A.transit.rail_capacity_seated', 'A.transit.rail_capacity_standing'),
    }
    patched_types = []
    unpatched_types = []
    for vt in vroot:
        if tag(vt) != 'vehicleType':
            continue
        keys = FLEET_CAPACITY.get(vt.get('id'))
        if keys is None:
            unpatched_types.append(vt.get('id'))
            continue
        seated, standing = cfg.get(keys[0]), cfg.get(keys[1])
        for cap in vt:
            if tag(cap) != 'capacity':
                continue
            patched_types.append((vt.get('id'), cap.get('seats'),
                                  cap.get('standingRoomInPersons'),
                                  str(seated), str(standing)))
            cap.set('seats', str(seated))
            cap.set('standingRoomInPersons', str(standing))
    out_veh = os.path.join(dst_dir, 'transitVehicles.xml.gz')
    with gzip_writer(out_veh, text=False) as f:
        vtree.write(f, encoding='utf-8', xml_declaration=True)

    return dict(routes_kept=kept_routes, routes_dropped=dropped_routes,
                departures=kept_dep, departures_dropped=dropped_dep,
                routes_kept_under_a_foreign_day_id=mixed_routes,
                transport_modes=sorted(transport_modes),
                vehicles=kept_veh,
                vehicle_capacity_patched=patched_types,
                vehicle_types_unpatched=unpatched_types,
                vehicle_refs=len(vehicles_used),
                stop_facilities_kept=kept_fac, stop_facilities_dropped=dropped_fac,
                transfer_relations_kept=kept_rel,
                transfer_relations_dropped=dropped_rel)


ATTRIBUTE_EL = ('<attribute name="%s" class="java.lang.String">%s</attribute>')
NAMED_ATTR_RE = r'<attribute name="%s"[^>]*>.*?</attribute>'


def set_link_attribute(tail, name, value):
    """Set one `<attribute>` inside a link's existing `<attributes>` block.

    Every mapped link already carries an `<attributes>` block (`osm:way:id` is
    how the E1 patch finds it at all), so appending a second one before
    `</link>` produces `More than one instance of element <attributes>` and
    MATSim refuses to read the network. Six of the ten run networks were built
    that way. See DECISIONS.md 9.4.
    """
    el = ATTRIBUTE_EL % (name, value)
    existing = re.search(NAMED_ATTR_RE % re.escape(name), tail, re.S)
    if existing:
        return tail[:existing.start()] + el + tail[existing.end():]
    if '</attributes>' in tail:
        return tail.replace('</attributes>', el + '</attributes>', 1)
    if '</link>' in tail:
        return tail.replace('</link>', '<attributes>' + el + '</attributes></link>', 1)
    return tail


MODES_ATTR_RE = re.compile(r'modes="([^"]*)"')

# The modes a car link also carries, and why each is there. `ride` is ROUTED
# on the road network but not simulated (a passenger is not a second vehicle;
# PAIRED passengers physically board, DECISIONS.md 9.53); `truck` (9.49),
# `motorbike` (9.52), `walk` and `bike` (9.54) are ROUTED AND SIMULATED at
# their declared PCE - a pedestrian at PCE 0.0 occupies the network without
# consuming road capacity (the sidewalk, in queue arithmetic). All ride on
# the car network because no mode-specific route layer is part of the one
# mapped build (3.5 forbids a remap); the road rules still hold: walk and
# bike are excluded from the declared prohibited classes.
CAR_COMPANION_MODES = ('ride', 'truck', 'motorbike', 'taxi')
LAWFUL_COMPANIONS = (('walk', 'A.network.pedestrian_excluded_classes'),
                     ('bike', 'A.network.bicycle_excluded_classes'))
HIGHWAY_ATTR_RE = re.compile(r'name="osm:way:highway"[^>]*>([^<]+)<')


def allow_car_companions(link_xml, excluded_of_mode):
    """One link's modes attribute, extended with every mode the law allows.

    The mapped network permits `car` alone, so a config that declared `ride` a
    network mode produced `checking 0 nodes and 0 links for dead-ends` and
    then threw during `PrepareForSim` - the run inputs could not be used even
    once the schedules were fixed (DECISIONS.md 9.4, defect 4). The simulated
    modes need the same permission outright: a link that does not carry a
    qsim main mode refuses its vehicles.

    Walk and bike are withheld from their declared prohibited road classes
    (pedestrians on motorways are not a modelling choice to leave open); a
    link with no highway class keeps them, which errs on connectivity.
    """
    m = MODES_ATTR_RE.search(link_xml)
    if m is None:
        return link_xml, False
    modes = [x for x in m.group(1).split(',') if x]
    if 'car' not in modes:
        return link_xml, False
    hw = HIGHWAY_ATTR_RE.search(link_xml)
    highway = hw.group(1).strip() if hw else ''
    add = [x for x in CAR_COMPANION_MODES if x not in modes]
    for mode, excluded in excluded_of_mode.items():
        if mode not in modes and highway not in excluded:
            add.append(mode)
    if not add:
        return link_xml, False
    new = 'modes="%s"' % ','.join(sorted(modes + add))
    return link_xml[:m.start()] + new + link_xml[m.end():], True


def write_mode_vehicles(dst_path, cfg):
    """The vehicles file `qsim.vehiclesSource=modeVehicleTypesFromVehiclesData` reads.

    One vehicle type per qsim main mode, keyed by the mode's own name - that is
    the contract of the vehicles source. `car` restates MATSim's default
    vehicle EXACTLY (RUN.qsim.car_vehicle - equality is what keeps the car
    fleet's physics unchanged by the freight change); `truck` carries the
    declared PCE and the regulated speed cap (DECISIONS.md 9.49). Written by
    the assembly AND re-written per run by run_matsim.build_config against
    that run's own resolution, so a swept B.freight.pce reaches the mobsim.

    Capacity is omitted: a private vehicle boards nobody in the qsim, and a
    seat count here would be a literal doing nothing.
    """
    car = cfg.get('RUN.qsim.car_vehicle')
    # A car's PASSENGER capacity is the declared ride cap (DECISIONS.md 9.53):
    # the qsim's boarding refusal and the pairing's own capacity rule must be
    # the same number or one of them is decoration. MATSim counts capacity as
    # seats + standing EXCLUDING the driver (verified against the jar:
    # QVehicleImpl's constructor), so seats = the cap itself. Left implicit,
    # the qsim would default to 4 - equal to the declared value today, which
    # is this repository's named right-by-accident defect.
    car_seats = int(cfg.get('B.ride.max_passengers_per_vehicle'))

    def car_bodied(mode):
        # `ride` needs a type because PrepareForSim demands one for every
        # NETWORK mode, not only the main modes - and a ride vehicle IS a car
        # by identity (a passenger rides in one), so it restates the car type
        # rather than declaring a second value. It never enters the mobsim:
        # ride is not a main mode, so the type is inert beyond loading.
        return ['\t<vehicleType id="%s">' % mode,
                '\t\t<capacity seats="%d" standingRoomInPersons="0">' % car_seats,
                '\t\t</capacity>',
                '\t\t<length meter="%s" />' % car['length_m'],
                '\t\t<width meter="%s" />' % car['width_m'],
                '\t\t<passengerCarEquivalents pce="%s" />' % car['pce'],
                '\t\t<networkMode networkMode="%s" />' % mode,
                '\t</vehicleType>']

    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.matsim.org/files/dtd '
        'http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd">',
    ] + car_bodied('car') + car_bodied('ride') + (
        # taxi (issue #49, #88; DECISIONS.md 9.86): a taxi IS a car by
        # identity - the passenger rides in one - so it restates the car type
        # rather than declaring a second body. Since 9.86 taxi is also a qsim
        # MAIN mode, so this type is what the mobsim loads and queues: the
        # length, width and PCE here are the road space a hired car actually
        # takes. Emitted only when the declared routing vocabulary carries
        # the mode.
        car_bodied('taxi') if 'taxi' in cfg.get('RUN.routing.network_modes')
        else []
    ) + [
        '\t<vehicleType id="truck">',
        '\t\t<length meter="%s" />' % cfg.get('B.freight.length_m'),
        '\t\t<width meter="%s" />' % car['width_m'],
        # declared in km/h because that is what the regulation states;
        # MATSim reads metres per second
        '\t\t<maximumVelocity meterPerSecond="%.4f" />'
        % (float(cfg.get('B.freight.max_speed_kmh')) / 3.6),
        '\t\t<passengerCarEquivalents pce="%s" />' % cfg.get('B.freight.pce'),
        '\t\t<networkMode networkMode="truck" />',
        '\t</vehicleType>',
        # a motorbike consumes LESS than a car (DECISIONS.md 9.52); no speed
        # cap - it takes each link's own limit like a car does
        '\t<vehicleType id="motorbike">',
        '\t\t<length meter="%s" />' % cfg.get('B.motorbike.length_m'),
        '\t\t<width meter="%s" />' % car['width_m'],
        '\t\t<passengerCarEquivalents pce="%s" />' % cfg.get('B.motorbike.pce'),
        '\t\t<networkMode networkMode="motorbike" />',
        '\t</vehicleType>',
        # walk and bike (DECISIONS.md 9.54): a pedestrian at PCE 0.0 occupies
        # the network without consuming road capacity; a cyclist at the
        # declared PCE takes real carriageway space. Both are speed-capped by
        # the same declared value the router reads (CappedSpeedTravelTime),
        # so estimate and physics cannot drift. Length and width are omitted:
        # at these PCEs the queue runs entirely on the equivalents, and the
        # constructor defaults are cosmetic.
        '\t<vehicleType id="walk">',
        '\t\t<maximumVelocity meterPerSecond="%.4f" />'
        % float(cfg.get('A.transit.walk_speed_ms')),
        '\t\t<passengerCarEquivalents pce="%s" />' % cfg.get('B.walk.pce'),
        '\t\t<networkMode networkMode="walk" />',
        '\t</vehicleType>',
        '\t<vehicleType id="bike">',
        '\t\t<maximumVelocity meterPerSecond="%.4f" />'
        % float(cfg.get('B.bike.speed_ms')),
        '\t\t<passengerCarEquivalents pce="%s" />' % cfg.get('B.bike.pce'),
        '\t\t<networkMode networkMode="bike" />',
        '\t</vehicleType>',
        '</vehicleDefinitions>',
        '']
    with open(dst_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))
    return dst_path


LINK_HEAD_RE = re.compile(
    r'<link id="([^"]+)" from="([^"]+)" to="([^"]+)"[^>]*?modes="([^"]*)"')


def strip_unreachable_mode_links(body, mode, applied):
    """Keep `mode` only on its largest strongly-connected subnetwork.

    Withholding walk from the trunk classes severs pockets whose only
    connection to the rest of the network is an excluded link, and MATSim
    REFUSES a mode whose subnetwork has unreachable links ("Network for mode
    'walk' has unreachable links and nodes... Aborting" - the first 9.54
    probe died on it). This is MATSim's own MultimodalNetworkCleaner rule,
    applied at build time where the network is text: find the largest
    strongly-connected component of the mode's subgraph (iterative Kosaraju)
    and strip the mode from every link outside it. The stripped count is
    reported - a silent strip would hide how much of the city the exclusion
    disconnects.
    """
    links = []          # (link_id, from, to) carrying the mode
    adj = {}
    radj = {}
    for m in LINK_HEAD_RE.finditer(body):
        lid, frm, to, modes = m.group(1), m.group(2), m.group(3), m.group(4)
        if mode in modes.split(','):
            links.append((lid, frm, to))
            adj.setdefault(frm, []).append(to)
            radj.setdefault(to, []).append(frm)
    if not links:
        return body
    # iterative Kosaraju: finishing order on the forward graph, then reverse
    # sweeps in reverse finishing order; the largest component wins
    seen = set()
    order = []
    for start in adj:
        if start in seen:
            continue
        stack = [(start, iter(adj.get(start, ())))]
        seen.add(start)
        while stack:
            node, it = stack[-1]
            advanced = False
            for nxt in it:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, iter(adj.get(nxt, ()))))
                    advanced = True
                    break
            if not advanced:
                order.append(node)
                stack.pop()
    comp = {}
    seen2 = set()
    best_id, best_size = None, 0
    for start in reversed(order):
        if start in seen2:
            continue
        size = 0
        stack = [start]
        seen2.add(start)
        while stack:
            node = stack.pop()
            comp[node] = start
            size += 1
            for nxt in radj.get(node, ()):
                if nxt not in seen2:
                    seen2.add(nxt)
                    stack.append(nxt)
        if size > best_size:
            best_id, best_size = start, size
    drop = {lid for lid, frm, to in links
            if comp.get(frm) != best_id or comp.get(to) != best_id}
    if not drop:
        return body

    def strip(m):
        s = m.group(0)
        lid = re.search(r'id="([^"]+)"', s).group(1)
        if lid not in drop:
            return s
        mm = MODES_ATTR_RE.search(s)
        modes = [x for x in mm.group(1).split(',') if x != mode]
        applied['%s_stripped_unreachable' % mode] += 1
        return s[:mm.start()] + 'modes="%s"' % ','.join(modes) + s[mm.end():]

    return LINK_BLOCK_RE.sub(strip, body)


NONMOTOR_MODES = ('walk', 'bike')
LINK_TAG_RE = re.compile(r'<link\b[^>]*>')


def add_nonmotor_reverse_links(body, reverse_speed_ms, applied):
    """A walk/bike reverse complement for every one-way street (9.58).

    MATSim's network is directed, so a one-way carriageway is walkable in one
    direction only - which is false: a pedestrian walks both sides of every
    street, and a cyclist dismounts and wheels. Without the complements, the
    per-mode SCC strip severed 16,726 walk links and 5,177 bike links into
    unreachable pockets, 6.8% of activities landed on walk-less links, and
    every walk/bike leg touching one was silently routed from the NEAREST
    in-network link instead - the qsim then refused the disconnected first
    hop and ABORTED the agent mid-day (measured: 491,349 refusals over 135
    iterations, ~11.6k broken legs per iteration at 25%).

    For each node pair (a, b) where some link carries walk or bike and no
    link (b, a) carries it, ONE reverse link is added carrying exactly the
    missing non-motor modes: length, capacity and lane count inherited from
    the forward link (nothing new is decided), free speed = the declared
    walking speed (`A.transit.walk_speed_ms` - a dismounted cyclist is a
    pedestrian). Complements carry no osm attributes, so an E1 patch can
    never touch one, and no car mode, so the motor network is unchanged.
    Parallel forward links share one complement. Runs BEFORE the SCC strip,
    which afterwards removes only true islands.
    """
    covered = {}           # (from, to) -> set of nonmotor modes carried
    heads = []             # attr dicts of links carrying a nonmotor mode
    for m in LINK_TAG_RE.finditer(body):
        a = dict(ATTR_RE.findall(m.group(0)))
        if 'id' not in a or 'from' not in a:
            continue
        nm = set((a.get('modes') or '').split(',')) & set(NONMOTOR_MODES)
        if nm:
            covered.setdefault((a['from'], a['to']), set()).update(nm)
            heads.append(a)
    new_links = []
    index_of = {}          # (to, from) -> index into new_links
    for a in heads:
        rev = (a['to'], a['from'])
        need = sorted((set((a.get('modes') or '').split(','))
                       & set(NONMOTOR_MODES)) - covered.get(rev, set()))
        if not need:
            continue
        if rev in index_of:
            merged = index_of[rev]
            new_links[merged]['modes'] = sorted(set(new_links[merged]['modes'])
                                                | set(need))
        else:
            index_of[rev] = len(new_links)
            new_links.append(dict(id='nmr_%s' % a['id'], frm=a['to'],
                                  to=a['from'], length=a['length'],
                                  capacity=a['capacity'],
                                  permlanes=a['permlanes'], modes=need))
        covered.setdefault(rev, set()).update(need)
    if not new_links:
        return body
    parts = ['<link id="%s" from="%s" to="%s" length="%s" freespeed="%.4f" '
             'capacity="%s" permlanes="%s" oneway="1" modes="%s" />'
             % (L['id'], L['frm'], L['to'], L['length'],
                float(reverse_speed_ms), L['capacity'], L['permlanes'],
                ','.join(L['modes']))
             for L in new_links]
    applied['nonmotor_reverse_links'] = len(new_links)
    return body.replace('</links>',
                        '\t\t' + '\n\t\t'.join(parts) + '\n\t</links>', 1)


def patch_network(src_net, dst_net, patches, drop_turns, excluded_of_mode,
                  reverse_speed_ms):
    """Re-apply an E1 road variant to a mapped schedule network by osm:way:id."""
    with gzip.open(src_net, 'rt', encoding='utf-8') as f:
        xml = f.read()
    applied = collections.Counter()

    def patch_link(m):
        s = m.group(0)
        wid = WAY_ID_RE.search(s)
        p = patches.get(wid.group(1)) if wid else None
        if not p:
            # No E1 patch, but EVERY car link still carries the companion
            # modes (the first form of this refactor put the extension after
            # this early return, which silently produced a network with zero
            # walkable links - caught by the probe, not by reading).
            merged, extended = allow_car_companions(s, excluded_of_mode)
            if extended:
                applied['companion_mode_links'] += 1
            return merged
        head_end = s.index('>')
        head, tail = s[:head_end], s[head_end:]
        a = dict(ATTR_RE.findall(head))
        changed = (p.get('fields_changed') or '').split(';')
        if 'num_lanes_per_dir' in changed and p.get('field_num_lanes_per_dir_to'):
            try:
                old = float(a.get('permlanes', '1') or 1)
                new = float(p['field_num_lanes_per_dir_to'])
                if old > 0 and new > 0:
                    cap = float(a.get('capacity', '0') or 0)
                    a['capacity'] = '%.1f' % (cap / old * new)
                    a['permlanes'] = '%.1f' % new
                    head = '<link ' + ' '.join('%s="%s"' % kv for kv in a.items())
                    applied['num_lanes_per_dir'] += 1
            except (ValueError, ZeroDivisionError):
                pass
        if 'kerbside_use' in changed and p.get('field_kerbside_use_to'):
            new_tail = set_link_attribute(tail, 'osm:way:kerbside',
                                          p['field_kerbside_use_to'])
            if new_tail != tail:
                applied['kerbside_use'] += 1
                tail = new_tail
        merged, extended = allow_car_companions(head + tail, excluded_of_mode)
        if extended:
            applied['companion_mode_links'] += 1
            head_end2 = merged.index('>')
            head, tail = merged[:head_end2], merged[head_end2:]
        if drop_turns and 'disallowedNextLinks' in tail:
            # E1's "no banned turns" applies to the corridor without the tram,
            # not to the whole study area. Stripping the attribute network-wide
            # would delete 1,235 observed restrictions instead of the handful on
            # the corridor, and quietly hand every scenario a freer road network.
            new_tail = re.sub(r'<attribute name="disallowedNextLinks".*?</attribute>',
                              '', tail, flags=re.S)
            if new_tail != tail:
                applied['banned_turns_removed'] += 1
                tail = new_tail
        return head + tail

    body = LINK_BLOCK_RE.sub(patch_link, xml)
    body = add_nonmotor_reverse_links(body, reverse_speed_ms, applied)
    for mode in excluded_of_mode:
        body = strip_unreachable_mode_links(body, mode, applied)
    os.makedirs(os.path.dirname(dst_net), exist_ok=True)
    with gzip_writer(dst_net) as f:
        f.write(body)
    return dict(applied)


def stamp_gradients(net_path, clamp_pct):
    """Stamp a signed `grade_pct` attribute on every run-network link whose
    endpoint elevations the P2 layers hold (DECISIONS.md 9.84, issue #21).

    The grade is DERIVED per link from the node elevations the A1/A6 edge
    tables already carry (copernicus_glo30): (elev[to] - elev[from]) /
    length, positive climbing in the link's direction of travel, clamped by
    the declared `A.gradient.grade_clamp_pct` (node differencing over very
    short links produces outliers no street sustains). A link without both
    endpoint elevations gets NO attribute and is flat to the consumer -
    counted, never hidden. Near-flat links (|grade| < 0.05%) are left
    unstamped: the factor is 1 to four decimal places and the attribute
    would only grow the file.

    Consumed by citysim.GradientLinkSpeed on both the router and the mobsim
    side when `gradient.representation = link_speed`.
    """
    elev = {}
    for path in (ROAD_EDGES, FOOTWAY_EDGES):
        with open(path, encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                for node, key in ((r['from_node'], 'elev_start_m'),
                                  (r['to_node'], 'elev_end_m')):
                    v = r.get(key)
                    if v:
                        try:
                            elev.setdefault(node, float(v))
                        except ValueError:
                            pass
    with gzip.open(net_path, 'rt', encoding='utf-8') as f:
        xml = f.read()
    counts = collections.Counter()

    def stamp(m):
        s = m.group(0)
        head_end = s.index('>')
        head = s[:head_end]
        a = dict(ATTR_RE.findall(head))
        counts['links'] += 1
        f_e = elev.get(a.get('from'))
        t_e = elev.get(a.get('to'))
        if f_e is None or t_e is None:
            counts['no_elevation'] += 1
            return s
        try:
            length = float(a.get('length') or 0)
        except ValueError:
            length = 0.0
        if length <= 0:
            counts['no_elevation'] += 1
            return s
        grade = (t_e - f_e) / length * 100.0
        grade = max(-clamp_pct, min(clamp_pct, grade))
        if abs(grade) < 0.05:
            counts['flat'] += 1
            return s
        counts['stamped'] += 1
        tail = s[head_end:]
        return head + set_link_attribute(tail, 'grade_pct', '%.2f' % grade)

    body = LINK_BLOCK_RE.sub(stamp, xml)
    with gzip_writer(net_path) as f:
        f.write(body)
    return dict(counts)


def patch_signal_capacities(net_path, patch_csv):
    """The re-capacitation half of the double-count rule (#73), applied to the
    emitted run network.

    Under `explicit_signals` every signalised approach link takes the declared
    saturation flow x lanes from the generated patch
    (`signals_capacity_patch.csv`, per scenario), replacing the metered
    capacity that carried the intersection effect under `implicit_delay` - one
    representation per effect, both halves together (DECISIONS.md 9.76).
    Applied AFTER the E1 variant patch so a variant's lane arithmetic cannot
    silently overwrite the saturation re-raise. A patch row whose link is not
    in the network is refused: it means the patch was generated against a
    different build than the one being assembled (3.5).
    """
    cap_of = {}
    for r in csv.DictReader(open(patch_csv, encoding='utf-8')):
        cap_of[r['link']] = float(r['capacity_saturation_veh_h'])
    with gzip.open(net_path, 'rt', encoding='utf-8') as f:
        xml = f.read()
    patched = set()

    def recap(m):
        s = m.group(0)
        head_end = s.index('>')
        head = s[:head_end]
        a = dict(ATTR_RE.findall(head))
        cap = cap_of.get(a.get('id'))
        if cap is None:
            return s
        a['capacity'] = '%.1f' % cap
        patched.add(a['id'])
        return ('<link ' + ' '.join('%s="%s"' % kv for kv in a.items())
                + s[head_end:])

    body = LINK_BLOCK_RE.sub(recap, xml)
    missing = sorted(set(cap_of) - patched)
    if missing:
        raise SystemExit(
            '%d signal capacity-patch link(s) are not in %s (first: %s). The '
            'patch was generated against a different network build - '
            're-run build_matsim_signals.py on this build (DECISIONS.md 3.5).'
            % (len(missing), net_path, missing[:3]))
    with gzip_writer(net_path) as f:
        f.write(body)
    return len(patched)


def check_change_event_links(net_path, events_xml):
    """Refuse a change-events file that names links this network lacks.

    MATSim would only warn, and a warned-away closure looks exactly like an
    open crossing. The crossings are derived on the BASE network; every
    scenario's mapped network keeps road link ids, and this check is where
    that assumption is enforced rather than assumed.
    """
    wanted = set()
    for _, el in ET.iterparse(events_xml, events=('end',)):
        if el.tag.endswith('link'):
            wanted.add(el.get('refId'))
        el.clear()
    if not wanted:
        raise SystemExit('%s names no links' % events_xml)
    present = set()
    with gzip.open(net_path, 'rb') as fh:
        for _, el in ET.iterparse(fh, events=('end',)):
            if el.tag == 'link':
                if el.get('id') in wanted:
                    present.add(el.get('id'))
                el.clear()
    missing = sorted(wanted - present)
    if missing:
        raise SystemExit(
            '%d crossing change-event link(s) missing from %s (first: %s) - '
            'the crossings were derived on a different network build.'
            % (len(missing), net_path, missing[:3]))
    return len(wanted)


ZONES_SA1 = _city.path('data/processed/zones/zones_SA1.gpkg')


def write_parking_prices(net_path, dst_path):
    """Join the run network's car links to the zone parking price.

    A link is priced by the zone its midpoint falls in. Only PRICED links are
    written - roughly 22k of the run network's ~144k car links - because a link
    absent from the table is free, and writing 144k rows to say so 30 times over
    is bytes for nothing.

    The join happens here rather than in Java for the reason CLAUDE.md gives:
    the price of a place has to be derived from a boundary, and a boundary is a
    build-time object. Java gets two columns.
    """
    import geopandas as gpd

    prices = {}
    for r in csv.DictReader(open(PARK_PRICE_ZONES, encoding='utf-8')):
        p = float(r['price_aud_hr'])
        if p > 0:
            prices[r['SA1_CODE21']] = p
    nodes, links = {}, []
    with gzip.open(net_path, 'rb') as fh:
        for _, el in ET.iterparse(fh, events=('end',)):
            if el.tag == 'node':
                nodes[el.get('id')] = (float(el.get('x')), float(el.get('y')))
                el.clear()
            elif el.tag == 'link':
                if 'car' in el.get('modes', '').split(','):
                    links.append((el.get('id'), el.get('from'), el.get('to')))
                el.clear()
    if not links:
        raise SystemExit('%s carries no car links' % net_path)
    xs = [(nodes[a][0] + nodes[b][0]) / 2.0 for _, a, b in links]
    ys = [(nodes[a][1] + nodes[b][1]) / 2.0 for _, a, b in links]
    zones = gpd.read_file(ZONES_SA1).to_crs(_city.crs())[['SA1_CODE21', 'geometry']]
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xs, ys), crs=_city.crs())
    j = gpd.sjoin(pts, zones, how='left', predicate='within')
    j = j[~j.index.duplicated(keep='first')].sort_index()
    codes = list(j['SA1_CODE21'])

    rows = []
    for (link_id, _, _), code in zip(links, codes):
        # NaN for a link outside the zone system - beyond the study area, and
        # free, which is what an absent row already means.
        price = prices.get('' if code != code or code is None else str(code))
        if price:
            rows.append((link_id, price))
    rows.sort(key=lambda r: r[0])
    with open(dst_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('link_id\tprice_aud_hr\n')
        for link_id, price in rows:
            fh.write('%s\t%.4f\n' % (link_id, price))
    return dict(car_links=len(links), priced_links=len(rows),
                priced_zones=len(prices))


def parking_window(cfg, day):
    """The charged window for one day type, as (start_h, end_h).

    A day type with no window - Sunday - resolves to (0, 0), and the handler
    reads an end at or before the start as `charge nothing`. Expressing a free
    day that way rather than with a separate flag keeps one code path.
    """
    win = (cfg.get('A.parking.charged_hours_by_day_type') or {}).get(day)
    if not win:
        return 0.0, 0.0
    return float(win[0]), float(win[1])


def _weight_sweep(cfg, strategy):
    """The declared range for one replanning strategy weight, as [lo, hi].

    `RUN.replanning.weights` carries a PROPORTIONAL sweep over the whole table,
    so a single strategy's range is that proportion applied to its own weight -
    derived rather than typed, which is what removed the literal
    `SUBTOUR_MODE_CHOICE_WEIGHT_SWEEP = (0.05, 0.20)` that used to sit beside
    the table and could drift from it.
    """
    weight = cfg.get('RUN.replanning.weights')[strategy]
    sweep = cfg.sweep('RUN.replanning.weights')
    share = sweep['proportional'] if isinstance(sweep, dict) else float(sweep[0])
    return [round(weight * (1.0 - share), 6), round(weight * (1.0 + share), 6)]


# The C1 constant each scheduled PT submode carries once the declared
# RUN.routing.pt_submode_scoring representation maps it to a passenger mode
# of its own name (issue #49 Tier C, DECISIONS.md 9.78). The keys are the
# schedule's per-route transportMode vocabulary - pt2matsim writes the GTFS
# route type as bus/tram/rail/ferry, so like FLEET_CAPACITY's these are tool
# structure, not a city value; the values are C1's own alternative names.
# FERRY IS ABSENT DELIBERATELY: C1 declares no ferry constant, so a ferry
# keeps the pt aggregate's constant and the report SAYS so - stating the gap
# is the rule, inventing a value would be the violation this project cannot
# absorb.
PT_SUBMODE_ASC = {'bus': 'asc_bus', 'tram': 'asc_lr', 'rail': 'asc_rail'}


def pt_passenger_submodes(cfg):
    """The scheduled submode vocabulary, from the declared transit modes.

    The non-`pt` entries of RUN.transit.transit_modes: `pt` is the plan-level
    umbrella every PT trip keeps, the rest are the transportModes the mapper
    wrote per route (bus/tram/rail/ferry across the five TfNSW feeds).
    Derived from the declared field rather than re-parsed from each schedule
    so the builder and the run harness cannot disagree about the vocabulary;
    `split_schedule` still refuses a schedule whose routes carry a
    transportMode outside it, which is where a metro or a cable car would
    otherwise sail through to SwissRailRaptor's mode mapping and take a null
    passenger mode (RaptorStaticConfig.getPassengerMode is a plain map get -
    read from the pinned jar, DECISIONS.md 9.78).

    Empty under the `aggregate` representation, which is what keeps every
    per-submode branch below inert and the emission byte-identical to the
    pre-9.78 state on that arm.
    """
    if cfg.get('RUN.routing.pt_submode_scoring') != 'per_submode':
        return []
    return [m for m in cfg.get('RUN.transit.transit_modes') if m != 'pt']


def scoring_from_c1(cfg, c1, purpose_share):
    """Translate the C1 nested-logit parameters into MATSim scoring.

    MATSim scores with a Charypar-Nagel utility: one marginal utility of
    travelling per mode, one alternative-specific constant per mode, and an
    opportunity cost of time shared by every activity. Two things in C1 have no
    representation in it, and are reported rather than silently dropped:

      * the **nest structure** (`nesting_coefficient_pt = 0.65`). MATSim's mode
        choice is a co-evolutionary search, not a closed-form nested logit;
        there is nowhere to put a nest coefficient.
      * the **per-purpose value of time**. C1 prices a commute minute at
        18.6 AUD/h and a work-business minute at 55.4; MATSim's scoring is per
        mode, not per purpose. A trip-weighted average is used, so a scenario
        that shifts the purpose mix will not shift the value of time with it.

    The identity used is the conventional one:
        VOT = (performing - traveling_mode) / marginalUtilityOfMoney
    """
    vot = c1['vot_aud_hr']
    wsum = sum(purpose_share.get(p, 0.0) for p in vot)
    vot_avg = (sum(vot[p] * purpose_share.get(p, 0.0) for p in vot) / wsum
               if wsum > 0 else sum(vot.values()) / len(vot))
    w = c1['weights']
    asc = c1['asc']
    perf = cfg.get('C.scoring.performing_utils_per_h')
    mm = cfg.get('C.scoring.marginal_utility_of_money')

    def traveling(weight):
        return round(perf - vot_avg * weight * mm, 4)

    modes = {
        'car': dict(constant=asc['asc_car_driver'][0],
                    marginalUtilityOfTraveling=traveling(1.0)),
        'ride': dict(constant=asc['asc_car_passenger'][0],
                     marginalUtilityOfTraveling=traveling(1.0)),
        'pt': dict(constant=asc['asc_bus'][0],
                   marginalUtilityOfTraveling=traveling(w['beta_ivt']['base'])),
        # walk and bike are scored as MODES here, so they take their own
        # mode-time weights - NOT beta_walk_access, which is the appraisal
        # weight on walking to a stop INSIDE a PT journey. Using the access
        # weight priced a whole walking trip at 2x car time and put the
        # walk-bike indifference distance at 174 m against an observed mean
        # walk trip of 700 m (DECISIONS.md 9.28). MATSim also scores PT
        # access, egress and transfer legs with these same walk params, in the
        # scoring function and again in the raptor router, so this one value
        # governs walk AND half the cost of every PT trip.
        'walk': dict(constant=asc['asc_walk'][0],
                     marginalUtilityOfTraveling=traveling(cfg.get('C.time_weights.beta_walk_mode'))),
        'bike': dict(constant=asc['asc_cycle'][0],
                     marginalUtilityOfTraveling=traveling(cfg.get('C.time_weights.beta_bike_mode'))),
        # truck (DECISIONS.md 9.49) and motorbike (9.52): scoring params must
        # exist for any leg mode MATSim scores, but these agents' modes are
        # LOCKED - the choice this block prices never happens for them. The
        # car time rate is carried so the values are unremarkable, and the
        # constants are zero because there is no alternative to be relative to.
        'truck': dict(constant=0.0, marginalUtilityOfTraveling=traveling(1.0)),
        'motorbike': dict(constant=0.0,
                          marginalUtilityOfTraveling=traveling(1.0)),
        # the teleported access/egress stub (DECISIONS.md 9.54): its time IS
        # walking time, so it carries walk's marginal rate BY IDENTITY, and a
        # zero constant - the mode constant belongs to the MAIN mode of the
        # trip, and a constant here would be paid once per stub. Without this
        # declaration MATSim scores the stubs with its own built-in
        # non_network_walk defaults - a value nobody declared, reaching every
        # PT trip: the right-by-accident defect class.
        'non_network_walk': dict(
            constant=0.0,
            marginalUtilityOfTraveling=traveling(cfg.get('C.time_weights.beta_walk_mode'))),
    }
    # PT submodes score-distinct (issue #49 Tier C, DECISIONS.md 9.78):
    # under the declared per_submode representation each scheduled
    # transportMode routes as a passenger mode of its own name (the
    # swissRailRaptor mapping config_runtime emits), so its legs are scored
    # with the constant C1 declares FOR THAT SUBMODE - the constants that
    # collapse into the single pt entry above under `aggregate`. The pt
    # entry itself stays: it is the plan-level mode subtour mode choice runs
    # over, and the raptor's direct-walk fallback still produces pt-routed
    # trips. Time is priced at the one declared beta_ivt for every submode
    # because C1 declares no per-submode in-vehicle time weight; a submode
    # without a C1 constant (ferry) keeps the pt aggregate's, and the
    # not_representable list below states it.
    submodes = pt_passenger_submodes(cfg)
    for sm in submodes:
        asc_key = PT_SUBMODE_ASC.get(sm)
        modes[sm] = dict(
            constant=(asc[asc_key][0] if asc_key
                      else modes['pt']['constant']),
            marginalUtilityOfTraveling=traveling(w['beta_ivt']['base']))
    # taxi (issue #49, 4.7.8): the point-to-point priced mode, scored only
    # when the declared choice vocabulary carries it (INERT until the batch
    # boundary adds 'taxi' to RUN.mode_choice.modes). Its constant folds the
    # declared wait/booking time in at the trip-weighted VOT - a teleported
    # mode has no physical wait, so the wait is priced, not simulated - and
    # its per-km fare enters as monetaryDistanceRate in config_runtime. The
    # ASC is swept, never fitted: no taxi target exists, and the realised
    # volume is reported against B.taxi.daily_trips_band as a CONSTRAINT.
    if 'taxi' in cfg.get('RUN.mode_choice.modes'):
        wait_cost = (cfg.get('C.taxi.wait_min') / 60.0) * vot_avg * mm
        modes['taxi'] = dict(
            constant=round(cfg.get('C.taxi.asc') - wait_cost, 4),
            marginalUtilityOfTraveling=traveling(1.0))
    tp = c1['transfer_penalty']['base']
    # What survives the translation and what does not is REPRESENTATION-
    # dependent now (9.78): under per_submode the asc_lr/asc_rail collapse is
    # gone from this list because it is gone from the config; under aggregate
    # it is stated instead of silently absorbed. Ferry's missing constant is
    # a gap in C1 itself and is stated on the arm that would otherwise hide
    # it behind a value nobody declared.
    if submodes:
        no_c1_constant = sorted(sm for sm in submodes
                                if sm not in PT_SUBMODE_ASC)
        submode_notes = [
            'per-submode constant for %s: C1 declares none, so it keeps the '
            'pt aggregate\'s constant (asc_bus=%s) - stated, not invented. '
            'Every submode shares the one declared beta_ivt time weight; '
            'only the constants differ'
            % ('/'.join(no_c1_constant), asc['asc_bus'][0])
        ] if no_c1_constant else []
    else:
        submode_notes = [
            'per-submode constants (asc_bus=%s, asc_lr=%s, asc_rail=%s): '
            'RUN.routing.pt_submode_scoring is `aggregate`, so every PT leg '
            'scores as one pt mode carrying asc_bus and the bus/tram/rail '
            'distinction reaches scoring through nothing (DECISIONS.md 9.3)'
            % (asc['asc_bus'][0], asc['asc_lr'][0], asc['asc_rail'][0])]
    return dict(
        performing_utils_per_h=perf,
        performing_sweep=list(cfg.sweep('C.scoring.performing_utils_per_h')),
        monetary_distance_rate=cfg.get('C.scoring.monetary_distance_rate'),
        monetary_distance_rate_sweep=list(cfg.sweep('C.scoring.monetary_distance_rate')),
        strategies=cfg.get('RUN.replanning.weights'),
        # The mode-choice innovation weight is the one that bounds how far the
        # co-evolution can move mode share, so it is reported as its own range.
        # It was a literal tuple beside the strategy table; it is DERIVED from
        # the field's own proportional sweep now, so the two cannot disagree.
        subtour_mode_choice_weight_sweep=_weight_sweep(cfg, 'SubtourModeChoice'),
        marginal_utility_of_money=mm,
        vot_aud_hr_used=round(vot_avg, 3),
        vot_aud_hr_by_purpose=vot,
        purpose_weights=purpose_share,
        waiting_pt=traveling(w['beta_wait']['base']),
        utility_of_line_switch=round(-(tp / 60.0) * vot_avg * mm, 4),
        transfer_penalty_min=tp,
        transfer_penalty_sweep=[c1['transfer_penalty']['low'],
                                c1['transfer_penalty']['high']],
        modes=modes,
        pt_submode_scoring=cfg.get('RUN.routing.pt_submode_scoring'),
        pt_submodes=list(submodes),
        not_representable=submode_notes + [
            'nesting_coefficient_pt=%s and the nested-logit structure: MATSim '
            'mode choice is a co-evolutionary search with no nest parameter'
            % c1['nesting']['nesting_coefficient_pt'],
            'per-purpose value of time: MATSim scores per mode, so a '
            'trip-weighted average (%.2f AUD/h) is used in place of the six '
            'purpose-specific values' % vot_avg,
            'crowding multipliers (beta_crowding_*): require an explicit '
            'capacity-dependent scoring extension, not enabled here',
            'gradient UTILITY penalties (beta_gradient_uphill=%s, '
            'beta_gradient_downhill=%s): MATSim scores a leg from time and '
            'distance and has no gradient utility term, so these two '
            'behavioural weights reach nothing. %s (9.84, issue 21)'
            % (w['beta_gradient_uphill']['base'],
               w['beta_gradient_downhill']['base'],
               'The gradient DATA now reaches mode choice through link '
               'travel time instead - grade_pct on the run network, walk '
               'and bike slowed by the declared published relations on '
               'both the router and the mobsim side'
               if cfg.get('A.gradient.representation') == 'link_speed' else
               'With A.gradient.representation=absent the attached '
               'gradient reaches mode choice through nothing; it remains '
               'used for corridor grades'),
            'PT walk-access decay (walk_decay, beta_per_m=%s): the access and '
            'egress walk that actually happens is routing.accessEgressType '
            'plus SwissRailRaptor own radius handling, neither of which reads '
            'a decay curve, so the declared curve reaches nothing (issue 21)'
            % c1['walk_decay']['params']['beta_per_m'],
        ])


# --------------------------------------------------------------------------
# the config, BUILT from the registry rather than substituted into a template
# --------------------------------------------------------------------------
# This used to be a 100-line XML template with `{substitution}` holes. Every
# parameter nobody had cut a hole for stayed a literal, and forty-seven of them
# did - including the innovation cutoff the entire relaxation measurement hinges
# on, the four strategy weights that govern how far co-evolution can move mode
# share, and the logit scale, which had no registry field at all.
#
# There is no template now. `src/registry/param_config.py` builds the document
# from the fields that declare a `matsim_param` binding, so a parameter exists
# only if a field claims it or the caller supplies it under a declared runtime
# role. The three roles are the three things a registry cannot hold: a path on
# this machine, the city's own identity, and a value DERIVED from declared
# fields. Everything else is a leak, and `closure()` returns it.


def config_runtime(cfg, scoring, day, paths):
    """What the registry cannot hold, each entry carrying the role that justifies it.

    `scoring` is the C1 translation: MATSim scores with a Charypar-Nagel utility
    and C1 is a nested logit, so the mode constants and per-mode time rates are
    computed rather than declared. Each one names the identity that produced it,
    and the registry declares the same identity on the matching `computed` field
    - so the value is derived in one place and its provenance is recorded in
    another that a reader can find without opening a builder.
    """
    start_h, end_h = parking_window(cfg, day)
    typical = cfg.get('C.scoring.activity_typical_duration_s')
    minimal = cfg.get('C.scoring.activity_minimal_duration_s')
    runtime = {
        'global.coordinateSystem': (_city.crs(), 'identity', 'city.json crs.epsg'),
        'controler.outputDirectory': (paths['output'], 'path', 'run output'),
        'network.inputNetworkFile': (paths['network'], 'path', 'scenario run network'),
        'plans.inputPlansFile': (paths['plans'], 'path', 'day-type plans'),
        'transit.transitScheduleFile': (paths['schedule'], 'path', 'filtered schedule'),
        'transit.vehiclesFile': (paths['vehicles'], 'path', 'transit vehicles'),
        'vehicles.vehiclesFile': (paths['mode_vehicles'], 'path',
                                  'per-main-mode vehicle types (car restates the '
                                  'MATSim default; truck carries B.freight.pce)'),
        'parking.priceFile': (paths['parking_prices'], 'path', 'per-link price table'),
        # The two capacity factors are identities on the sample fraction, not
        # choices. Both registry fields are declared `computed`, so the emitter
        # REFUSES to write them from a declared value and requires them here.
        'qsim.flowCapacityFactor': (
            paths['fraction'], 'derived', 'flowCapacityFactor = RUN.sample.fraction'),
        'qsim.storageCapacityFactor': (
            paths['fraction'] ** cfg.get('RUN.sample.storage_capacity_exponent'),
            'derived', 'storageCapacityFactor = fraction ** '
                       'RUN.sample.storage_capacity_exponent'),
        # The charged parking window is one field carrying a window per day type;
        # MATSim reads two parameters. Which day this set is for is not a
        # registry value, so the selection happens here.
        'parking.chargedStartHour': (
            start_h, 'derived',
            'A.parking.charged_hours_by_day_type[%s][0]' % day),
        'parking.chargedEndHour': (
            end_h, 'derived',
            'A.parking.charged_hours_by_day_type[%s][1]' % day),
        'scoring.waitingPt': (
            scoring['waiting_pt'], 'derived',
            'performing - trip-weighted VOT * beta_wait * marginalUtilityOfMoney'),
        'scoring.utilityOfLineSwitch': (
            scoring['utility_of_line_switch'], 'derived',
            '-(C.transfer.penalty_min / 60) * trip-weighted VOT * '
            'marginalUtilityOfMoney'),
        'scoring.modeParams[*].constant': (
            {m: v['constant'] for m, v in scoring['modes'].items()},
            'derived', 'the C1 alternative-specific constant for each mode'),
        'scoring.modeParams[*].marginalUtilityOfTraveling_util_hr': (
            {m: v['marginalUtilityOfTraveling'] for m, v in scoring['modes'].items()},
            'derived',
            'performing - trip-weighted VOT * beta[mode] * marginalUtilityOfMoney'),
        # Applied as min(minimal, typical): a 15-minute floor over a 5-minute
        # drop-off would be self-contradictory, and MATSim would hold the
        # vehicle there.
        'scoring.activityParams[*].minimalDuration': (
            {a: min(minimal, d) for a, d in typical.items()},
            'derived',
            'min(C.scoring.activity_minimal_duration_s, typical duration) per activity',
            _param_config.HHMMSS, 'seconds'),
    }
    # taxi (issue #49): the fare reaches scoring in two parts. The per-km
    # part is native (monetaryDistanceRate on the taxi modeParams; negative,
    # AUD per METRE); the flagfall is a per-trip charge no scoring parameter
    # expresses, so it goes through the `fare` module to FareChargeHandler
    # (the ParkingChargeHandler PersonMoneyEvent pattern). Both are BLENDS of
    # the measured taxi schedule and the literature rideshare rates at the
    # declared rideshare share - one mode honestly carrying two services.
    if 'taxi' in cfg.get('RUN.mode_choice.modes'):
        s_ride = cfg.get('B.taxi.rideshare_trip_share')
        blend_km = ((1 - s_ride) * cfg.get('B.taxi.fare_per_km_taxi_aud')
                    + s_ride * cfg.get('B.taxi.fare_per_km_rideshare_aud'))
        blend_flag = ((1 - s_ride) * cfg.get('B.taxi.flagfall_taxi_aud')
                      + s_ride * cfg.get('B.taxi.flagfall_rideshare_aud'))
        runtime['scoring.modeParams[taxi].monetaryDistanceRate'] = (
            round(-blend_km / 1000.0, 8), 'derived',
            '-((1-B.taxi.rideshare_trip_share) x B.taxi.fare_per_km_taxi_aud '
            '+ share x B.taxi.fare_per_km_rideshare_aud) / 1000, AUD per '
            'metre')
        runtime['fare.flagfallAud'] = (
            round(blend_flag, 4), 'derived',
            '(1-B.taxi.rideshare_trip_share) x B.taxi.flagfall_taxi_aud + '
            'share x B.taxi.flagfall_rideshare_aud')
        runtime['fare.mode'] = (
            'taxi', 'derived', 'the mode FareChargeHandler charges')

    # PT submodes score-distinct (issue #49 Tier C, DECISIONS.md 9.78):
    # under the declared per_submode representation the swissRailRaptor
    # module maps each scheduled route transportMode to a passenger mode of
    # the same name. Module name, parameter and parameterset structure were
    # verified against the PINNED jar's bytecode, not memory (the recorded
    # trap): ch.sbb.matsim.config.SwissRailRaptorConfigGroup - module
    # `swissRailRaptor`, boolean `useModeMappingForPassengers`, parameterset
    # `modeMapping` carrying `routeMode`/`passengerMode`; RaptorUtils.
    # createStaticConfig copies the mappings into the router, and
    # createParameters prices each passenger mode from its own scoring
    # modeParams entry - which is why scoring_from_c1 emits one per submode.
    # Under `aggregate` no module is emitted and the config is byte-identical
    # to the pre-9.78 emission.
    submodes = pt_passenger_submodes(cfg)
    if submodes:
        runtime['swissRailRaptor.useModeMappingForPassengers'] = (
            True, 'derived',
            "RUN.routing.pt_submode_scoring == 'per_submode'")
        runtime['swissRailRaptor.modeMapping[*].passengerMode'] = (
            {sm: sm for sm in submodes}, 'derived',
            'each scheduled transportMode routes as a passenger mode of the '
            'same name; vocabulary = RUN.transit.transit_modes minus the pt '
            'umbrella')

    # Explicit corridor signals (#73): the signals contrib's module and its
    # three data files enter ONLY when the declared representation says so -
    # A.signals.representation is the one-representation-per-effect switch
    # (dossier 04 7.5), and under implicit_delay the config carries no signal
    # module at all, byte-identical to the pre-#73 emission.
    if cfg.get('A.signals.representation') == 'explicit_signals':
        for target, key, note in (
                ('signalsystems.signalsystems', 'signal_systems',
                 'generated signal systems (build_matsim_signals.py)'),
                ('signalsystems.signalgroups', 'signal_groups',
                 'generated signal groups'),
                ('signalsystems.signalcontrol', 'signal_control',
                 'generated fixed-time/priority control plans')):
            if key not in paths:
                raise SystemExit(
                    'A.signals.representation is explicit_signals but the '
                    'caller supplied no %r path. Run '
                    'build_matsim_signals.py and pass its outputs.' % key)
            runtime[target] = (paths[key], 'path', note)
        runtime['signalsystems.useSignalsystems'] = (
            True, 'derived', 'A.signals.representation == explicit_signals')
        # The contrib refuses fast capacity update at module-install time
        # ("Fast flow capacity update does not support signals"). Written
        # here so every signal config states it, rather than each run
        # discovering it in the JVM (DECISIONS.md 9.76 activation checklist).
        runtime['qsim.usingFastCapacityUpdate'] = (
            False, 'derived',
            'the signals contrib refuses fast capacity update; forced false '
            'while A.signals.representation == explicit_signals')
    # Taxi as a finite fleet (DECISIONS.md 9.99, #90). remodeRefused is a
    # DEFINITION rather than a registry value, exactly like the ride engine's
    # own remode switch: a refused request that did not walk would be a
    # constraint with no price, and the whole point of the fleet is that the
    # constraint IS the price.
    runtime['taxiFleet.remodeRefused'] = (
        True, 'derived',
        'a refused taxi request walks this iteration and has the mode restored '
        'at AfterMobsim (9.55, 9.81, 9.99)')

    # Level crossings (#68): the closures reach the router only as a
    # time-variant network, and only when the declared representation gate
    # says so - under `absent` the emission is byte-identical to pre-#68.
    if cfg.get('A.crossings.representation') == 'change_events':
        if 'change_events' not in paths:
            raise SystemExit(
                'A.crossings.representation is change_events but the caller '
                'supplied no change_events path. Run the city\'s '
                'build_level_crossings.py and pass its output.')
        runtime['network.timeVariantNetwork'] = (
            True, 'derived', 'A.crossings.representation == change_events')
        runtime['network.inputChangeEventsFile'] = (
            paths['change_events'], 'path',
            'derived freight level-crossing closures '
            '(build_level_crossings.py)')
    return runtime


def write_config(path, cfg, scoring, day, paths):
    """Emit one scenario x day-type config, and refuse a leak."""
    runtime = config_runtime(cfg, scoring, day, paths)
    leaks = _param_config.closure('matsim', cfg, runtime)
    if leaks:
        raise SystemExit('the emitted config carries %d parameter(s) that came '
                         'from neither a registry field nor a declared runtime '
                         'role: %s' % (len(leaks), leaks))
    return _param_config.write(path, 'matsim', cfg, runtime)


def hts_purpose_share():
    import pandas as pd
    pur = pd.read_csv(_city.path('data/processed/hts/hts_purpose.csv'))
    pur = pur[pur.geography == 'lga']
    yr = sorted(pur.FINANCIAL_YEAR.unique())[-1]
    pur = pur[pur.FINANCIAL_YEAR == yr]
    pmap = {'Commute': 'HW', 'Education/childcare': 'HE', 'Shopping': 'HS',
            'Personal business': 'HO', 'Social/recreation': 'HO',
            'Serve passenger': 'NHB', 'Work related business': 'WB', 'Other': 'HO'}
    pur = pur.assign(p=pur.TRAVEL_PURPOSE.str.rstrip('*').map(pmap))
    pur = pur[pur.p.notna()]
    j = pur.groupby('p').JOURNEYS_BY_MODE.sum()
    return (j / j.sum()).to_dict()


def shipped_iterations(cfg):
    """The iteration count written into a SHIPPED config.

    This builder used to supply 100 from an argparse default, which walked
    straight past the resolver's refusal and shipped a known-wrong number into
    all thirty configs. While `RUN.controler.last_iteration` was `unobtained` it
    shipped the LOWER BOUND OF THE DECLARED SWEEP instead - the largest value
    measured to be insufficient - so a config run outside the harness was short
    rather than plausible.

    The field is now MEASURED and active (DECISIONS.md 9.43, issue 5): two full
    arms at 1000 iterations settle after the selection snap at both sample
    fractions. So a shipped config carries the declared value, resolved through
    the registry like any other - not a floor, and still not a literal typed
    here. The harness continues to resolve per run and re-emit, and
    `run_matsim.py` still gives `--iterations` no default so every run states
    the horizon it actually used.

    It falls back to the sweep floor if the field is ever returned to
    `unobtained`, so making the value provisional again cannot silently ship a
    number that is no longer declared.
    """
    try:
        value = cfg.get('RUN.controler.last_iteration')
    except Exception:                                     # noqa: BLE001
        value = None
    if value is not None:
        return int(value)
    sweep = cfg.sweep('RUN.controler.last_iteration')
    interval = sweep['interval'] if isinstance(sweep, dict) else sweep
    return int(interval[0])


def main(day_types=None, scenarios=None, set_overrides=None):
    day_types = day_types or DAY_TYPES
    os.makedirs(OUT, exist_ok=True)
    c1 = json.load(open(PARAMS, encoding='utf-8'))
    purpose_share = hts_purpose_share()

    rows = list(csv.DictReader(open(E1, encoding='utf-8')))
    if scenarios:
        rows = [r for r in rows if r['scenario_id'] in scenarios]

    patch_rows = list(csv.DictReader(open(PATCHES, encoding='utf-8')))
    by_variant = collections.defaultdict(dict)
    for p in patch_rows:
        by_variant[p['road_variant_ref']][p['edge_id'][1:]] = p
    road_variants = {r['road_variant_ref']: r for r in
                     csv.DictReader(open(_city.path('scenarios/E1_road_variants.csv'),
                                         encoding='utf-8'))}

    # The shipped configs carry the sweep's lower bound, set EXPLICITLY through
    # the resolver rather than substituted past it, so `_config.json` records
    # where the number came from and the value is checked against its own
    # declared range like any other.
    base_cfg = _registry.load(strict=True)
    shipped = {'RUN.controler.last_iteration': shipped_iterations(base_cfg)}
    shipped.update(set_overrides or {})
    # The road-rule exclusions are base declarations (which classes a
    # pedestrian or cyclist may use is law, not a scenario property), and the
    # network is patched once per scenario before any day resolution exists.
    excluded_of_mode = {mode: frozenset(base_cfg.get(key))
                        for mode, key in LAWFUL_COMPANIONS}

    # The two representation gates (DECISIONS.md 9.77 activation boundary).
    # Under the inert values every branch below is skipped and the assembly
    # is byte-identical to the pre-boundary emission.
    explicit_signals = (base_cfg.get('A.signals.representation')
                        == 'explicit_signals')
    crossings_on = (base_cfg.get('A.crossings.representation')
                    == 'change_events')
    change_events_xml = _city.path(
        'networks/matsim/crossings/crossing_change_events.xml')
    if crossings_on and not os.path.exists(change_events_xml):
        raise SystemExit(
            'A.crossings.representation is change_events but %s does not '
            'exist. Run the city\'s build_level_crossings.py first.'
            % change_events_xml)

    # Recorded so the HARNESS can recompute the C1 translation against its own
    # resolution without re-reading the HTS. Without this the derived scoring
    # would be frozen at build time, and a run overlay moving the transfer
    # penalty - the field deliverable 8 sweeps 3-15 min - would not move
    # utilityOfLineSwitch, which is the only parameter it acts through.
    report = dict(scenarios={}, purpose_share=purpose_share)
    for r in rows:
        sid = r['scenario_id']
        sched_dir = os.path.join(MATSIM, 'schedules', sid)
        if not os.path.isdir(sched_dir):
            print('   %-5s SKIP - no mapped schedule' % sid, flush=True)
            continue
        ref = r['road_variant_ref']
        pat = by_variant.get(ref, {})
        drop = road_variants.get(ref, {}).get('banned_turn_movements') == '0'
        net_dst = os.path.join(OUT, sid, 'network.xml.gz')
        touched = patch_network(os.path.join(sched_dir, 'network.xml.gz'),
                                net_dst, pat, drop, excluded_of_mode,
                                base_cfg.get('A.transit.walk_speed_ms'))
        # Explicit signals (#73): the scenario's generated signal data model,
        # the saturation-flow re-capacitation and the transformed schedule
        # (dwell #74 + implicit-delay removal) all come from ONE derived set
        # per scenario - build_matsim_signals.py against this build.
        sig_dir = os.path.join(MATSIM, 'signals', sid)
        sig_sched = None
        recap_links = 0
        if explicit_signals:
            for name in ('signal_systems.xml', 'signal_groups.xml',
                         'signal_control.xml', 'signals_capacity_patch.csv',
                         'transitSchedule_signals.xml.gz'):
                if not os.path.exists(os.path.join(sig_dir, name)):
                    raise SystemExit(
                        'A.signals.representation is explicit_signals but '
                        '%s is missing for %s. Run the city\'s '
                        'build_matsim_signals.py first.'
                        % (os.path.join(sig_dir, name), sid))
            recap_links = patch_signal_capacities(
                net_dst, os.path.join(sig_dir, 'signals_capacity_patch.csv'))
            sig_sched = os.path.join(sig_dir, 'transitSchedule_signals.xml.gz')
        if crossings_on:
            check_change_event_links(net_dst, change_events_xml)
        # Gradient into link travel time (DECISIONS.md 9.84, #21): stamped
        # after every other network patch so nothing overwrites it.
        gradient_stamp = {}
        if base_cfg.get('A.gradient.representation') == 'link_speed':
            gradient_stamp = stamp_gradients(
                net_dst, base_cfg.get('A.gradient.grade_clamp_pct'))
        price_dst = os.path.join(OUT, sid, PARK_PRICE_FILE)
        parking = write_parking_prices(net_dst, price_dst)
        entry = dict(road_variant=ref, patch_rows=len(pat),
                     links_touched=touched, parking=parking,
                     signal_capacity_links=recap_links,
                     gradient=gradient_stamp, days={})
        for d in day_types:
            # RESOLVED PER SCENARIO AND DAY TYPE. The scenario and day overlays
            # are layers of the registry, so S2b's signal priority and Sunday's
            # parking window are properties of THIS resolution rather than
            # arguments threaded through a template.
            cfg = _registry.load(scenario=sid, day=d, set=shipped)
            check_scoring_order(cfg)
            scoring = scoring_from_c1(cfg, c1, purpose_share)
            dst = os.path.join(OUT, sid, d)
            counts = split_schedule(sched_dir, dst, d, cfg,
                                    src_schedule=sig_sched)
            write_mode_vehicles(os.path.join(dst, 'vehicles.xml'), cfg)
            paths = dict(
                output='output',
                network=os.path.relpath(net_dst, dst).replace('\\', '/'),
                plans=os.path.relpath(os.path.join(PLANS, 'population_%s.xml.gz' % d),
                                      dst).replace('\\', '/'),
                schedule='transitSchedule.xml.gz',
                vehicles='transitVehicles.xml.gz',
                mode_vehicles='vehicles.xml',
                parking_prices=os.path.relpath(price_dst, dst).replace('\\', '/'),
                fraction=cfg.get('RUN.sample.fraction'))
            if explicit_signals:
                paths.update(
                    signal_systems=os.path.relpath(
                        os.path.join(sig_dir, 'signal_systems.xml'),
                        dst).replace('\\', '/'),
                    signal_groups=os.path.relpath(
                        os.path.join(sig_dir, 'signal_groups.xml'),
                        dst).replace('\\', '/'),
                    signal_control=os.path.relpath(
                        os.path.join(sig_dir, 'signal_control.xml'),
                        dst).replace('\\', '/'))
            if crossings_on:
                paths['change_events'] = os.path.relpath(
                    change_events_xml, dst).replace('\\', '/')
            write_config(os.path.join(dst, 'config.xml'), cfg, scoring, d, paths)
            entry['days'][d] = counts
            report.setdefault('scoring', scoring)
        report['scenarios'][sid] = entry
        print('   %-5s %-38s %s | parking %d/%d links priced' % (sid, ref,
              ' '.join('%s:%d routes/%d dep' % (d, v['routes_kept'], v['departures'])
                       for d, v in sorted(entry['days'].items())),
              parking['priced_links'], parking['car_links']), flush=True)

    if 'scoring' in report:
        print('scoring: VOT %.2f AUD/h (trip-weighted), performing %.1f utils/h'
              % (report['scoring']['vot_aud_hr_used'],
                 report['scoring']['performing_utils_per_h']), flush=True)
        for line in report['scoring']['not_representable']:
            print('   does not survive translation: %s' % line, flush=True)

    json.dump(report, open(os.path.join(OUT, '_run_inputs_report.json'), 'w'),
              indent=2)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # NO VALUE DEFAULTS. --seed, --iterations, --capacity-factor, --plan-memory
    # and --threads all used to sit here with a number beside them, and every
    # one of those numbers was a registry field being supplied past the
    # resolver. `--iterations 100` was the worst: the registry declares that
    # field UNOBTAINED because 100 is MEASURED to be too low, and this default
    # shipped it into all thirty configs anyway. Vary a value with --set, which
    # is checked against the field's declared sweep.
    ap.add_argument('--day-types', default=','.join(DAY_TYPES))
    ap.add_argument('--scenarios', default='')
    ap.add_argument('--set', action='append', default=[], metavar='KEY=VALUE',
                    help='registry override, e.g. RUN.machine.threads=8. Checked '
                         'against the declared sweep like any other layer')
    a = ap.parse_args()
    main([d for d in a.day_types.split(',') if d],
         [s for s in a.scenarios.split(',') if s] or None,
         _registry.parse_set(a.set))
