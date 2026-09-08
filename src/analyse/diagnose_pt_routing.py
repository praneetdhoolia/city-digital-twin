#!/usr/bin/env python
"""Why the PT router hands back a walk, and whether that is the model or a bug.

`NetworkDirectWalkPtRouter` logs one line per 100,000 comparisons:

    ptDirectWalk: 1700000 decisions, 690635 network walks chosen,
                  853357 without any transit route

and the line is easy to read wrongly, because its three counters do NOT share a
denominator. Read the class: `DECIDED` is incremented only AFTER the raptor has
returned a boarding itinerary whose `totalRouteCost` is readable, so a request
the raptor could not answer never reaches it. `NO_TRANSIT` counts exactly those
requests, and it is DISJOINT from `DECIDED`. So the population of requests is
`DECIDED + NO_TRANSIT` (plus the handful whose cost attribute was unreadable,
which the class counts nowhere), and the run above put 33.4% of its PT routing
requests in the no-route bucket and answered a further 40.6% of the rest with a
walk - together, three PT routing requests in five came back as a walk.

That is the whole reason this script exists. Two numbers that large are either
a defect in the router or a fact about the city's timetable against the city's
demand, and the difference cannot be argued: it has to be measured. So this
re-derives both counters OFF the run, from the run's own artefacts, by asking
the same question the raptor asks and counting the same way:

  * the run's own emitted `config.xml` supplies every value - the search and
    extension radii, the transfer walk distance, the direct-walk factor, the
    walk/pt/waiting marginal utilities, the line-switch penalty and the
    teleported walk speed. NOT the live registry: a diagnosis of a finished run
    that reads today's declared values is a diagnosis of a run nobody executed;
  * the run's own `transitSchedule.xml.gz` supplies the supply;
  * the run's own `plans.xml.gz` supplies the demand - every trip of every
    all-`pt` plan, which is the population the router is handed.

It then replicates MATSim's own rules, read from the pinned jar rather than
assumed. `DefaultRaptorStopFinder.findNearbyStops` takes the stops inside the
search radius and, when fewer than two are there, falls back to the NEAREST
stop plus the extension radius - so an access stop is ALWAYS found and the
radius can never by itself produce a no-route. `SwissRailRaptor.calcRoute`
returns null when no boarding itinerary exists, and `SwissRailRaptorRoutingModule`
then substitutes a walk, which is the only way `NO_TRANSIT` can fire.
`RaptorUtils.createParameters` prices a second of travel at
`(marginalUtilityOfTraveling - performing) / 3600`, per mode, and adds waiting
and a fixed transfer penalty - and NOTHING else: no mode constant, no fare, no
distance term. That last fact is reported here because it decides the whole PT
submode split.

The reachability answer is reported as a BRACKET, not a point, and deliberately:

  `no_route_upper`  a least-generalised-cost scan, which can be blocked at a
                    stop by a cheap-but-late label and so misses some routes;
  `no_route_lower`  an earliest-arrival scan with unbounded transfers, which
                    finds every route the timetable admits and some the raptor's
                    own cost bound would reject.

The run's own counter must sit inside that bracket. If it does not, the router
is doing something the timetable does not explain, and that IS the defect.

    python src/analyse/diagnose_pt_routing.py --run <run> --sample 3000
    python src/analyse/diagnose_pt_routing.py --run <run> --sample 8000 --json out.json

Reads a run directory and the city's declared inputs. Writes nothing unless
asked. **Nothing here is a result** - it is an account of one run's routing.
"""

import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.abspath(_os.path.realpath(__file__)))
for _p in (_os.path.join(_HERE, '..'), _os.path.join(_HERE, '..', 'run')):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse                                                   # noqa: E402
import bisect                                                     # noqa: E402
import collections                                                # noqa: E402
import gzip                                                       # noqa: E402
import io                                                         # noqa: E402
import json                                                       # noqa: E402
import math                                                       # noqa: E402
import random                                                     # noqa: E402
import re                                                         # noqa: E402
import xml.etree.ElementTree as ET                                # noqa: E402

import city as _city                                              # noqa: E402
import results_store as _store                                    # noqa: E402

# Two spellings of the same line. The FIRST is what every arm up to and
# including the F31 gate wrote, and its "decisions" total excluded the
# requests the raptor could not answer; the SECOND reports the requests
# themselves. Both are read, because a diagnosis that only understands the
# current spelling cannot look back at the arm that raised the question.
PROGRESS_OLD = re.compile(
    r'ptDirectWalk:\s+(\d+) decisions,\s+(\d+) network walks chosen,'
    r'\s+(\d+) without any transit route')
PROGRESS_NEW = re.compile(
    r'ptDirectWalk:\s+(\d+) pt routing requests,\s+(\d+) without any '
    r'transit route,\s+(\d+) compared, of which\s+(\d+) chose the network walk')
# How far back from the end of a matsim.log the last progress line is looked
# for. The logs run to tens of gigabytes, so the file is never read whole; a
# progress line is emitted every 100,000 comparisons, which on every arm on
# disk is far more often than this window is long.
LOG_TAIL_BYTES = 4 << 20


class Missing(Exception):
    """An artefact this diagnosis needs is not on disk. Always fatal."""


# --------------------------------------------------------------------------
# the run's own declared values


def _params(config_xml):
    """Every `<param name= value=>` of the run's emitted config, by module.

    Returned as {module: {name: value}} so a caller asks for the value the RUN
    executed rather than the value the registry declares today.
    """
    out = collections.defaultdict(dict)
    module = None
    setname = None
    for ev, el in ET.iterparse(config_xml, events=('start', 'end')):
        if ev == 'start':
            if el.tag == 'module':
                module = el.get('name')
                setname = None
            elif el.tag == 'parameterset':
                setname = el.get('type')
            elif el.tag == 'param' and module:
                key = el.get('name')
                if setname:
                    out[module].setdefault('_sets', [])
                    if key in ('mode', 'activityType'):
                        out[module]['_sets'].append({key: el.get('value')})
                    elif out[module]['_sets']:
                        out[module]['_sets'][-1][key] = el.get('value')
                else:
                    out[module][key] = el.get('value')
        else:
            if el.tag == 'parameterset':
                setname = None
            elif el.tag == 'module':
                module = None
            el.clear()
    return out


def _mode_param(params, module, mode, key):
    for s in params.get(module, {}).get('_sets', []):
        if s.get('mode') == mode and key in s:
            return float(s[key])
    raise Missing('the run declared no %s.%s for mode %s' % (module, key, mode))


def _rehome(recorded):
    """A path the run recorded, re-rooted onto this checkout's city if moved.

    A run's config carries absolute paths from the machine that executed it.
    The city-relative tail is what identifies the artefact (the same rule the
    manifest follows), so a recorded path that no longer exists is looked up
    again under the city this session resolves.
    """
    if not recorded:
        return None
    if _os.path.exists(recorded):
        return recorded
    norm = recorded.replace('\\', '/')
    marker = '/' + _os.path.basename(_city.CITY_DIR) + '/'
    if marker in norm:
        return _city.path(norm.split(marker, 1)[1])
    return None


# --------------------------------------------------------------------------
# the run's own supply and demand


def _hms(text):
    h, m, s = text.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def read_schedule(path):
    """Stop coordinates and the timetable as a departure-sorted connection list.

    A connection is one vehicle's run between two consecutive stops. This is
    the whole of the supply the raptor can offer, so a reachability answer
    derived from it is an answer about the timetable and not about a router.
    """
    stops = {}
    conns = []
    seq = offsets = departures = None
    with gzip.open(path, 'rb') as fh:
        for ev, el in ET.iterparse(fh, events=('start', 'end')):
            if ev == 'start':
                if el.tag == 'transitRoute':
                    seq, offsets, departures = [], [], []
                continue
            if el.tag == 'stopFacility':
                stops[el.get('id')] = (float(el.get('x')), float(el.get('y')))
                el.clear()
            elif el.tag == 'stop' and seq is not None:
                seq.append(el.get('refId'))
                arr, dep = el.get('arrivalOffset'), el.get('departureOffset')
                arr = _hms(arr) if arr else None
                dep = _hms(dep) if dep else None
                offsets.append((arr if arr is not None else dep,
                                dep if dep is not None else arr))
            elif el.tag == 'departure' and departures is not None:
                departures.append(_hms(el.get('departureTime')))
                el.clear()
            elif el.tag == 'transitRoute':
                rid = el.get('id')
                for start in departures:
                    for i in range(len(seq) - 1):
                        if offsets[i][1] is None or offsets[i + 1][0] is None:
                            continue
                        conns.append((start + offsets[i][1],
                                      start + offsets[i + 1][0],
                                      seq[i], seq[i + 1], rid))
                seq = offsets = departures = None
                el.clear()
    conns.sort(key=lambda c: c[0])
    return stops, conns


def read_pt_trips(path, pt_mode):
    """Every trip of every all-`pt` plan in the run's input population.

    That plan is what the router is handed: the demand builder writes one plan
    per mode, so the trips of the pt plan are, trip for trip, the requests the
    PT routing module answers - the same origins, destinations and departure
    times, before any replanning has moved them.
    """
    trips = []
    seq = None
    with gzip.open(path, 'rb') as fh:
        for ev, el in ET.iterparse(fh, events=('start', 'end')):
            if ev == 'start':
                if el.tag == 'plan':
                    seq = []
                continue
            if seq is not None and el.tag in ('activity', 'act'):
                seq.append(('a', float(el.get('x')), float(el.get('y')),
                            el.get('end_time')))
            elif seq is not None and el.tag == 'leg':
                seq.append(('l', el.get('mode')))
            elif el.tag == 'plan':
                modes = set(s[1] for s in seq if s[0] == 'l')
                if modes == {pt_mode}:
                    for i in range(1, len(seq) - 1, 2):
                        origin, dest = seq[i - 1], seq[i + 1]
                        if origin[3] is None:
                            continue
                        trips.append((origin[1], origin[2], dest[1], dest[2],
                                      _hms(origin[3])))
                seq = None
                el.clear()
            elif el.tag == 'person':
                el.clear()
    return trips


def last_progress(run_dir):
    """The run's own last `ptDirectWalk` counters, read from its log tail.

    Never the whole file: an arm's `matsim.log` reaches tens of gigabytes and
    reading one to find a line that repeats every 100,000 comparisons is a way
    to lose an afternoon.
    """
    path = _os.path.join(run_dir, 'matsim.log')
    if not _os.path.exists(path):
        return None
    size = _os.path.getsize(path)
    with io.open(path, 'rb') as fh:
        fh.seek(max(0, size - LOG_TAIL_BYTES))
        tail = fh.read().decode('utf-8', 'replace')
    found = PROGRESS_NEW.findall(tail)
    if found:
        _requests, no_transit, decided, walked = (int(v) for v in found[-1])
        return dict(decided=decided, network_walks=walked,
                    no_transit=no_transit)
    found = PROGRESS_OLD.findall(tail)
    if not found:
        return None
    decided, walked, no_transit = (int(v) for v in found[-1])
    return dict(decided=decided, network_walks=walked, no_transit=no_transit)


# --------------------------------------------------------------------------
# MATSim's own stop finding, replicated


class StopIndex(object):
    """A radius index over the stops, standing in for MATSim's QuadTree.

    The bucket size is the search radius the run declared, so the index is a
    function of the run and carries no number of its own.
    """

    def __init__(self, stops, cell):
        self.cell = float(cell)
        self.buckets = collections.defaultdict(list)
        self.empty = not stops
        for sid, (x, y) in stops.items():
            self.buckets[(int(x // self.cell), int(y // self.cell))].append(
                (sid, x, y))

    def disk(self, x, y, radius):
        out = []
        r2 = radius * radius
        cell = self.cell
        for i in range(int((x - radius) // cell), int((x + radius) // cell) + 1):
            for j in range(int((y - radius) // cell),
                           int((y + radius) // cell) + 1):
                for sid, sx, sy in self.buckets.get((i, j), ()):
                    d2 = (sx - x) ** 2 + (sy - y) ** 2
                    if d2 <= r2:
                        out.append((sid, math.sqrt(d2)))
        return out

    def closest(self, x, y):
        if self.empty:
            return None
        radius = self.cell
        while True:
            got = self.disk(x, y, radius)
            if got:
                return min(got, key=lambda t: t[1])
            radius *= 2

    def nearby(self, x, y, search_radius, extension_radius):
        """`DefaultRaptorStopFinder.findNearbyStops`, rule for rule.

        Fewer than two stops inside the search radius and the finder takes the
        NEAREST stop and re-queries at that distance plus the extension radius.
        So the search radius never removes a trip's access to the network; it
        only decides how many stops the raptor gets to try. Any account of the
        no-route counter that blames the radius is wrong before it is measured.
        """
        got = self.disk(x, y, search_radius)
        if len(got) < 2:
            nearest = self.closest(x, y)
            if nearest is None:
                return []
            got = self.disk(x, y, nearest[1] + extension_radius)
        return got


# --------------------------------------------------------------------------
# the two scans


class Router(object):
    def __init__(self, stops, conns, cfg):
        self.stops = stops
        self.conns = conns
        self.departures = [c[0] for c in conns]
        self.cfg = cfg
        self.index = StopIndex(stops, cfg['search_radius'])
        self.transfers = collections.defaultdict(list)
        for sid, (x, y) in stops.items():
            for other, dist in self.index.disk(x, y, cfg['transfer_walk_m']):
                if other != sid:
                    self.transfers[sid].append(
                        (other, dist / cfg['beeline_walk_speed']))

    def _ends(self, ox, oy, dx, dy):
        access = self.index.nearby(ox, oy, self.cfg['search_radius'],
                                   self.cfg['extension_radius'])
        egress = self.index.nearby(dx, dy, self.cfg['search_radius'],
                                   self.cfg['extension_radius'])
        return access, egress

    def walk_cost(self, ox, oy, dx, dy):
        """The direct walk priced exactly as `createDirectWalk` prices it.

        Beeline over the raptor's own beeline walk speed, times the walk
        marginal disutility. The network walk the run actually compares is
        LONGER than this, so a walk that wins here wins in the run too.
        """
        seconds = math.hypot(dx - ox, dy - oy) / self.cfg['beeline_walk_speed']
        return -self.cfg['u_walk'] * seconds * self.cfg['direct_walk_factor']

    def least_cost(self, ox, oy, dx, dy, depart):
        """Cheapest boarding itinerary's generalised cost, or None.

        One label per stop, minimal in cost, carrying the arrival time that
        cost was reached at. A cheap-but-late label can block a connection a
        multi-criteria search would have taken, so this UNDERSTATES
        reachability - which is why it is reported as the upper bound of the
        no-route bracket and never on its own.
        """
        access, egress = self._ends(ox, oy, dx, dy)
        if not access or not egress:
            return None
        speed = self.cfg['beeline_walk_speed']
        u_walk, u_pt, u_wait = (self.cfg['u_walk'], self.cfg['u_pt'],
                                self.cfg['u_wait'])
        switch = self.cfg['line_switch']
        labels = {}
        for sid, dist in access:
            seconds = dist / speed
            labels[sid] = (depart + seconds, -u_walk * seconds, False, None)
        first = bisect.bisect_left(self.departures,
                                   min(v[0] for v in labels.values()))
        conns = self.conns
        for k in range(first, len(conns)):
            cdep, carr, cfrom, cto, route = conns[k]
            here = labels.get(cfrom)
            if here is None or here[0] > cdep:
                continue
            cost = here[1] - u_wait * (cdep - here[0]) - u_pt * (carr - cdep)
            if here[2] and here[3] != route:
                cost += switch
            known = labels.get(cto)
            if known is None or cost < known[1]:
                labels[cto] = (carr, cost, True, route)
                for other, seconds in self.transfers.get(cto, ()):
                    reached = labels.get(other)
                    walked = cost - u_walk * seconds
                    if reached is None or walked < reached[1]:
                        labels[other] = (carr + seconds, walked, True, route)
        best = None
        for sid, dist in egress:
            label = labels.get(sid)
            if label is None or not label[2]:
                continue
            cost = label[1] - u_walk * (dist / speed)
            if best is None or cost < best:
                best = cost
        return best

    def reachable(self, ox, oy, dx, dy, depart):
        """Whether ANY boarding itinerary exists - earliest arrival, no bound.

        Unbounded transfers and unbounded waiting, so it finds every itinerary
        the timetable admits and a few the raptor's cost bound would refuse.
        The lower bound of the no-route bracket.
        """
        access, egress = self._ends(ox, oy, dx, dy)
        if not access or not egress:
            return False
        speed = self.cfg['beeline_walk_speed']
        targets = set(sid for sid, _d in egress)
        best = {}
        for sid, dist in access:
            best[sid] = depart + dist / speed
        first = bisect.bisect_left(self.departures, min(best.values()))
        conns = self.conns
        for k in range(first, len(conns)):
            cdep, carr, cfrom, cto, _route = conns[k]
            here = best.get(cfrom)
            if here is None or here > cdep:
                continue
            if best.get(cto, float('inf')) > carr:
                best[cto] = carr
                if cto in targets:
                    return True
                for other, seconds in self.transfers.get(cto, ()):
                    if best.get(other, float('inf')) > carr + seconds:
                        best[other] = carr + seconds
                        if other in targets:
                            return True
        return False

    def access_distance(self, x, y):
        nearest = self.index.closest(x, y)
        return None if nearest is None else nearest[1]


# --------------------------------------------------------------------------


def _quantile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(q * (len(ordered) - 1))]


def busiest_hour(conns):
    """The hour the run's own timetable puts the most departures in.

    Used as the control: a pair with no route AT THE HOUR THE CITY RUNS THE
    MOST SERVICE has none at any hour, so the no-route is structural - the two
    ends are not connected - rather than a consequence of when the traveller
    asked. Derived from the timetable rather than named, because the peak of a
    city nobody has modelled yet is not something this script can know.
    """
    hours = collections.Counter(int(c[0] // 3600) for c in conns)
    return hours.most_common(1)[0][0] if hours else 0


def diagnose(run_dir, sample_size):
    config_xml = _os.path.join(run_dir, 'config.xml')
    if not _os.path.exists(config_xml):
        raise Missing('%s has no emitted config.xml; the run cannot be '
                      'diagnosed from anything else' % run_dir)
    params = _params(config_xml)

    scoring = params.get('scoring', {})
    performing = float(scoring['performing'])
    transit_router = params.get('transitRouter', {})
    routing = params.get('routing', {})
    transit_modes = params.get('transit', {}).get('transitModes', '').split(',')
    pt_mode = transit_modes[0] if transit_modes else 'pt'

    walk_speed = walk_factor = None
    for candidate in ('transit_walk', 'non_network_walk', pt_mode, 'walk'):
        try:
            walk_speed = _mode_param(params, 'routing', candidate,
                                     'teleportedModeSpeed')
            walk_factor = _mode_param(params, 'routing', candidate,
                                      'beelineDistanceFactor')
            break
        except Missing:
            continue
    if walk_speed is None:
        raise Missing('the run declared no teleported walk speed, so the '
                      "raptor's beeline walk speed cannot be recovered")

    cfg = dict(
        search_radius=float(transit_router['searchRadius']),
        extension_radius=float(transit_router['extensionRadius']),
        transfer_walk_m=float(transit_router['maxBeelineWalkConnectionDistance']),
        direct_walk_factor=float(transit_router['directWalkFactor']),
        beeline_walk_speed=walk_speed / walk_factor,
        u_walk=(_mode_param(params, 'scoring', 'walk',
                            'marginalUtilityOfTraveling_util_hr')
                - performing) / 3600.0,
        u_pt=(_mode_param(params, 'scoring', pt_mode,
                          'marginalUtilityOfTraveling_util_hr')
              - performing) / 3600.0,
        u_wait=(float(scoring['waitingPt']) - performing) / 3600.0,
        line_switch=-float(scoring['utilityOfLineSwitch']),
        direct_walk_basis=params.get('ptDirectWalk', {}).get('basis'),
    )

    schedule = _rehome(params.get('transit', {}).get('transitScheduleFile'))
    if schedule is None:
        raise Missing('the run\'s transit schedule is not on disk')
    plans = _os.path.join(run_dir, 'plans.xml.gz')
    if not _os.path.exists(plans):
        plans = _rehome(params.get('plans', {}).get('inputPlansFile'))
    if plans is None or not _os.path.exists(plans):
        raise Missing('the run\'s input plans are not on disk')

    stops, conns = read_schedule(schedule)
    trips = read_pt_trips(plans, pt_mode)
    if not trips:
        raise Missing('the input population carries no all-%s plan, so the '
                      'router\'s request population cannot be recovered'
                      % pt_mode)

    seed = None
    record = _os.path.join(run_dir, '_run.json')
    if _os.path.exists(record):
        with io.open(record, encoding='utf-8') as fh:
            seed = json.load(fh).get('seed')
    if seed is None:
        raise Missing('the run records no seed, and an unseeded sample is not '
                      'a measurement anyone can repeat')
    chosen = (trips if len(trips) <= sample_size
              else random.Random(seed).sample(trips, sample_size))

    router = Router(stops, conns, cfg)
    peak_hour = busiest_hour(conns)
    peak = peak_hour * 3600.0

    by_hour = collections.Counter()
    no_route_hour = collections.Counter()
    walk_won_hour = collections.Counter()
    no_route = walk_won = found = structural = 0
    lower_no_route = 0
    access_m = []
    beyond_radius = 0
    walk_won_km = []
    transit_won_km = []
    no_route_km = []
    sweep = collections.Counter()
    factors = (1.0, 1.5, 2.0, 2.5, 3.0)

    for ox, oy, dx, dy, depart in chosen:
        hour = int(depart // 3600.0)
        by_hour[hour] += 1
        beeline_km = math.hypot(dx - ox, dy - oy) / 1000.0
        near = router.access_distance(ox, oy)
        if near is not None:
            access_m.append(near)
            if near > cfg['search_radius']:
                beyond_radius += 1
        cost = router.least_cost(ox, oy, dx, dy, depart)
        if cost is None:
            no_route += 1
            no_route_hour[hour] += 1
            no_route_km.append(beeline_km)
            if not router.reachable(ox, oy, dx, dy, depart):
                lower_no_route += 1
            if router.least_cost(ox, oy, dx, dy, peak) is None:
                structural += 1
            continue
        found += 1
        walk = router.walk_cost(ox, oy, dx, dy)
        for factor in factors:
            if walk * factor / cfg['direct_walk_factor'] < cost:
                sweep[factor] += 1
        if walk < cost:
            walk_won += 1
            walk_won_hour[hour] += 1
            walk_won_km.append(beeline_km)
        else:
            transit_won_km.append(beeline_km)

    total = len(chosen)
    # Two threshold-free cuts. The first is the group that CANNOT have a
    # route whatever the router does - it asks for a vehicle after the last
    # one of the modelled day has gone; the second is the small-hours tail the
    # demand profile is already known to overfill. Neither is a tuned band:
    # one comes from the timetable, the other from the clock. The per-hour
    # table below lets a reader take any other cut they want.
    last_departure_h = int(max(c[0] for c in conns) // 3600)
    late = sorted(h for h in by_hour if h > last_departure_h)
    after_midnight = sorted(h for h in by_hour if h >= 24)

    return dict(
        run=_os.path.basename(_os.path.normpath(run_dir)),
        counters_in_log=last_progress(run_dir),
        declared=cfg,
        supply=dict(stop_facilities=len(stops), connections=len(conns),
                    schedule=_city.rel(schedule)
                    if schedule.startswith(_city.CITY_DIR) else schedule),
        demand=dict(pt_plan_trips=len(trips), sampled=total, seed=seed),
        control_hour=peak_hour,
        no_route=dict(
            upper_pct=100.0 * no_route / total,
            lower_pct=100.0 * lower_no_route / total,
            structural_share_pct=(100.0 * structural / no_route
                                  if no_route else None),
            last_departure_hour=last_departure_h,
            after_last_departure_request_share_pct=(
                100.0 * sum(by_hour[h] for h in late) / total),
            after_last_departure_share_of_no_route_pct=(
                100.0 * sum(no_route_hour[h] for h in late) / no_route
                if no_route else None),
            after_midnight_request_share_pct=(
                100.0 * sum(by_hour[h] for h in after_midnight) / total),
            after_midnight_share_of_no_route_pct=(
                100.0 * sum(no_route_hour[h] for h in after_midnight) / no_route
                if no_route else None)),
        walk_wins=dict(
            of_found_pct=100.0 * walk_won / found if found else None,
            of_all_requests_pct=100.0 * walk_won / total,
            walk_answered_pct=100.0 * (no_route + walk_won) / total,
            walk_cost_per_pt_second=cfg['u_walk'] / cfg['u_pt'],
            factor_sweep={str(f): (100.0 * sweep[f] / found if found else None)
                          for f in factors}),
        lengths_km=dict(
            walk_won_p50=_quantile(walk_won_km, 0.5),
            walk_won_p90=_quantile(walk_won_km, 0.9),
            transit_won_p50=_quantile(transit_won_km, 0.5),
            no_route_p50=_quantile(no_route_km, 0.5),
            walk_answered_mean=((sum(walk_won_km) + sum(no_route_km))
                                / max(1, len(walk_won_km) + len(no_route_km)))),
        access_m=dict(beyond_search_radius_pct=100.0 * beyond_radius / total,
                      p50=_quantile(access_m, 0.5),
                      p90=_quantile(access_m, 0.9),
                      p99=_quantile(access_m, 0.99),
                      max=max(access_m) if access_m else None),
        by_hour=[dict(hour=h, requests=by_hour[h],
                      no_route_pct=100.0 * no_route_hour[h] / by_hour[h],
                      walk_won_pct=(100.0 * walk_won_hour[h]
                                    / max(1, by_hour[h] - no_route_hour[h])))
                 for h in sorted(by_hour)])


def _print(report):
    log = report['counters_in_log']
    print('run %s' % report['run'])
    if log:
        requests = log['decided'] + log['no_transit']
        print('\nWHAT THE RUN ITSELF COUNTED (last ptDirectWalk line)')
        print('  requests answered with a boarding itinerary : %d' % log['decided'])
        print('  requests the raptor could not answer         : %d' % log['no_transit'])
        print('  PT routing requests (the real denominator)   : %d' % requests)
        print('  no transit route            : %.1f%% of requests'
              % (100.0 * log['no_transit'] / requests))
        print('  network walk beat transit   : %.1f%% of the answered, '
              '%.1f%% of requests'
              % (100.0 * log['network_walks'] / log['decided'],
                 100.0 * log['network_walks'] / requests))
        print('  answered with a walk        : %.1f%% of requests'
              % (100.0 * (log['no_transit'] + log['network_walks']) / requests))
    else:
        print('\n  (no ptDirectWalk progress line in this run\'s log tail)')

    d, s = report['declared'], report['supply']
    print('\nWHAT THE RUN DECLARED')
    print('  search radius %.0f m, extension %.0f m, transfer walk %.0f m'
          % (d['search_radius'], d['extension_radius'], d['transfer_walk_m']))
    print('  direct-walk factor %.3f, basis %s' % (d['direct_walk_factor'],
                                                   d['direct_walk_basis']))
    print('  a second walking costs %.4f of a second riding'
          % (d['u_walk'] / d['u_pt']))
    print('  supply: %d stop facilities, %d connections'
          % (s['stop_facilities'], s['connections']))

    n = report['no_route']
    print('\nNO TRANSIT ROUTE, re-derived off the run (%d of %d trips sampled)'
          % (report['demand']['sampled'], report['demand']['pt_plan_trips']))
    print('  bracket %.1f%% .. %.1f%% of requests'
          % (n['lower_pct'], n['upper_pct']))
    if n['structural_share_pct'] is not None:
        print('  still no route at %02d:00 (the pair is simply not connected): '
              '%.1f%% of them' % (report['control_hour'],
                                  n['structural_share_pct']))
    print('  requests after the last departure of the modelled day (h%02d): '
          '%.1f%% of all, carrying %.1f%% of the no-routes'
          % (n['last_departure_hour'],
             n['after_last_departure_request_share_pct'],
             n['after_last_departure_share_of_no_route_pct'] or 0.0))
    print('  requests after midnight: %.1f%% of all, carrying %.1f%% of the '
          'no-routes' % (n['after_midnight_request_share_pct'],
                         n['after_midnight_share_of_no_route_pct'] or 0.0))

    a = report['access_m']
    print('  distance to the nearest stop: p50 %.0f m, p90 %.0f m, p99 %.0f m, '
          'max %.0f m' % (a['p50'], a['p90'], a['p99'], a['max']))
    print('  origins with no stop inside the search radius: %.1f%% (the finder '
          'falls back to the nearest stop, so this removes no trip)'
          % a['beyond_search_radius_pct'])

    w = report['walk_wins']
    print('\nWALK BEATS TRANSIT, re-derived off the run')
    print('  %.1f%% of answered requests, %.1f%% of all requests'
          % (w['of_found_pct'] or 0.0, w['of_all_requests_pct']))
    print('  answered with a walk overall: %.1f%%' % w['walk_answered_pct'])
    print('  direct-walk factor sweep (share of answered that still walk):')
    for factor, share in sorted(w['factor_sweep'].items(), key=lambda kv: float(kv[0])):
        print('    x%-4s  %.1f%%' % (factor, share or 0.0))

    length = report['lengths_km']
    print('  beeline km: walk-won p50 %.2f p90 %.2f | transit-won p50 %.2f | '
          'no-route p50 %.2f'
          % (length['walk_won_p50'] or 0.0, length['walk_won_p90'] or 0.0,
             length['transit_won_p50'] or 0.0, length['no_route_p50'] or 0.0))
    print('  mean beeline of every walk-answered request: %.2f km'
          % length['walk_answered_mean'])

    print('')
    print('BY DEPARTURE HOUR   requests  no-route pct  walk-won pct')
    for row in report['by_hour']:
        print('  %02d %20d %9.1f %10.1f'
              % (row['hour'], row['requests'], row['no_route_pct'],
                 row['walk_won_pct']))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run', required=True,
                    help='run name or directory (resolved by results_store)')
    ap.add_argument('--sample', type=int, required=True,
                    help='PT trips to route offline, drawn deterministically '
                         "in the run's own seed. Required and deliberately "
                         'undefaulted: how much of a population to measure is '
                         'a choice the person making the measurement owns, and '
                         'a few thousand already pins a 30%% rate to about a '
                         'point. Routing all of them takes hours.')
    ap.add_argument('--json', help='write the report here as JSON')
    args = ap.parse_args(argv)

    run_dir = _store.resolve(args.run)
    if run_dir is None:
        run_dir = _store.resolve_records(args.run)
    if run_dir is None:
        print('no run named %s in the results store' % args.run)
        return 2
    try:
        report = diagnose(run_dir, args.sample)
    except Missing as exc:
        print('cannot diagnose %s: %s' % (args.run, exc))
        return 2
    _print(report)
    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
        print('\nwrote %s' % args.json)
    return 0


if __name__ == '__main__':
    _sys.exit(main())
