"""Rank link delay without inferring a congestion cause.

Three readings, each written beside the run's processed findings:

  (default)  native transit link traversal times from the iteration's events
  --road     road links by EXCESS VEHICLE-HOURS over free flow, from the run's
             `telemetry_links.json` joined to the output network's class, name,
             capacity and lanes: how concentrated the delay is, by road class,
             by node, and the worst links (`road_delays`)
  --access   road-vehicle trip ENDS per link against that link's own sampled
             hourly capacity - the hours of capacity its trip ends need - and
             the trips by their worse end's load band with mean time, km and
             speed (`access_load`)

`--road` and `--access` may run together; the network is parsed once.

    python src/analyse/transit_link_delays.py --run <run> --iteration 250 --top 25
    python src/analyse/transit_link_delays.py --run <run> --road --access --iteration 250 --top 25
"""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from iteration_reading import open_table
import iteration_reading
import results_store
from run_matsim import _iteration_times_from_log


def run_input(run, name):
    """A run's schedule, network or vehicles file: the output copy MATSim
    wrote (`output/output_<name>`), else the copy beside the run directory.
    The reader looked only beside the run and no launch since 9.137 puts the
    schedule or the network there, so the transit reading could not open the
    F39 control run (sixteenth report)."""
    for candidate in (run / 'output' / ('output_' + name), run / name):
        if candidate.exists():
            return candidate
    raise SystemExit('%s holds neither output/output_%s nor %s' % (run, name, name))


class TransitLinkTraversals:
    """The scan_events handler of the transit reading: every transit vehicle's
    completed traversal of a link, per (mode, link) - count, total, min and
    max time with the vehicle and entry time of the max - and the unmatched
    entries and exits. One handler, so the close-out's single pass over the
    events file (summarise_run) and this reader's own pass accumulate the
    same thing and the report reads the same either way."""
    events = ('entered link', 'left link', 'vehicle enters traffic', 'vehicle leaves traffic')

    def __init__(self, transit, vehicles):
        self.transit, self.vehicles = transit, vehicles
        self.active, self.stats, self.unmatched = {}, {}, Counter()

    def __call__(self, kind, event):
        vehicle = event.get('vehicle', '')
        if vehicle not in self.transit:
            return
        mode, link, time = self.vehicles[vehicle], event['link'], float(event['time'])
        if kind in ('entered link', 'vehicle enters traffic'):
            if vehicle in self.active:
                self.unmatched['entry_without_previous_exit'] += 1
            self.active[vehicle] = (link, time)
            return
        start = self.active.pop(vehicle, None)
        if start is None or start[0] != link:
            self.unmatched['exit_without_matching_entry'] += 1
            return
        duration = time - start[1]
        row = self.stats.setdefault((mode, link), dict(mode=mode, link_id=link, traversals_count=0,
            total_time_s=0, max_time_s=0, min_time_s=float('inf')))
        row['traversals_count'] += 1
        row['total_time_s'] += duration
        row['min_time_s'] = min(row['min_time_s'], duration)
        if duration > row['max_time_s']:
            row.update(max_time_s=duration, max_vehicle_id=vehicle, max_entry_time_s=start[1])

    def result(self):
        """What the pass found, JSON-serialisable: the per-(mode, link) rows,
        the unmatched counts and the traversals still open at the end."""
        return dict(rows=list(self.stats.values()), unmatched=dict(self.unmatched),
                    unfinished=len(self.active))


def transit_fleet(run):
    """(the ids of the vehicles the schedule's departures name, vehicle id ->
    network mode) from the run's own vehicles and schedule."""
    with open_table(str(run_input(run, 'allVehicles.xml.gz'))) as stream:
        fleet = ET.parse(stream)
    modes = {v.get('id'): v.find('{*}networkMode').get('networkMode')
             for v in fleet.findall('{*}vehicleType')}
    vehicles = {v.get('id'): modes[v.get('type')] for v in fleet.findall('{*}vehicle')}
    with gzip.open(run_input(run, 'transitSchedule.xml.gz'), 'rb') as stream:
        transit = {v.get('vehicleRefId') for _, v in ET.iterparse(stream, events=('end',))
                   if v.tag == 'departure'}
    return transit, vehicles


def traversal_handler(run_dir):
    """This reading's handler for a shared events pass (summarise_run)."""
    transit, vehicles = transit_fleet(Path(run_dir))
    return TransitLinkTraversals(transit, vehicles)


def events_path(run, iteration):
    return next((run / 'output/ITERS' / f'it.{iteration}').glob(f'{iteration}.events.xml*'))


def traversals_reading(run, iteration):
    """The handler's result for this iteration: the close-out's recorded pass
    when `_summary.json` carries one for the same iteration (one decode of
    the events file serves every reader), else this reader's own pass."""
    import summarise_run                                        # noqa: PLC0415
    recorded = summarise_run.recorded_events_pass(str(run), iteration)
    if recorded and 'transit_link_traversals' in recorded:
        return recorded['transit_link_traversals'], 'close-out events pass (output/_events_pass_it%d.json)' % iteration
    handler = traversal_handler(run)
    iteration_reading.scan_events(events_path(run, iteration), handler)
    return handler.result(), 'this reading\'s own events pass'


def analyse(name, iteration, top):
    run = Path(results_store.resolve_or_die(name))
    iteration_reading.refuse_past_record(str(run), iteration)
    if iteration not in _iteration_times_from_log(str(run / 'matsim.log')):
        raise ValueError('Iteration has no native ENDS marker')
    with gzip.open(run_input(run, 'network.xml.gz'), 'rb') as stream:
        links = {}
        for _, link in ET.iterparse(stream, events=('end',)):
            if link.tag == 'link':
                links[link.get('id')] = {k: float(link.get(k)) for k in ('length', 'freespeed', 'capacity', 'permlanes')}
                link.clear()
    found, basis = traversals_reading(run, iteration)
    stats = [dict(row, **links[row['link_id']]) for row in found['rows']]
    for row in stats:
        row['mean_time_s'] = row['total_time_s'] / row['traversals_count']
        row['link_freeflow_time_s'] = row['length'] / row['freespeed']
        row['excess_over_link_freeflow_s'] = row['total_time_s'] - row['traversals_count'] * row['link_freeflow_time_s']
    rows = sorted(stats, key=lambda r: (-r['excess_over_link_freeflow_s'], r['mode'], r['link_id']))
    report = dict(run=run.name, iteration=iteration, completed_traversals_count=sum(r['traversals_count'] for r in rows),
        mode_link_pairs_count=len(rows), unmatched_events=found['unmatched'], unfinished_traversals_count=found['unfinished'],
        events_basis=basis,
        ranked_links=rows[:top], limitations=[
            'Link times include stop dwell and queues; excess is not automatically traffic congestion.',
            'The link free speed ignores vehicle maximum speed; this is a diagnostic baseline only.',
            'Origin and destination links can be traversed only partly; the native link attributes retain MATSim units.',
            'Ranks describe completed traversals only; unfinished and unmatched counts are separate.'])
    _write(run.name, f'_transit_link_delays_it{iteration}.json', report)
    print(json.dumps({**report, 'ranked_links': rows[:10]}, indent=2))


def _write(run_name, filename, report):
    destination = Path(results_store.processed_dir(run_name))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / filename).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


# ------------------------------------------------------------------ road links
#
# One streamed read of the network the run drove, for both road readings: the
# numeric link attributes on the <link> line and the three OSM attributes
# under it. Line regexes, not ElementTree - the output network is 200k+ links
# and this is read while an arm may be running.

_LINK = re.compile(r'<link id="([^"]+)" from="([^"]+)" to="([^"]+)" length="([^"]+)" '
                   r'freespeed="([^"]+)" capacity="([^"]+)" permlanes="([^"]+)"')
_ATTR = re.compile(r'<attribute name="([^"]+)"[^>]*>([^<]*)<')
_LINK_ATTRS = {'osm:way:highway': 'highway', 'type': 'type', 'osm:way:name': 'name'}


def network_path(run_dir):
    """The run's output network, else the input network its config names."""
    out = os.path.join(run_dir, 'output', 'output_network.xml.gz')
    if os.path.exists(out):
        return out
    import extract_metrics                                   # noqa: PLC0415
    path = extract_metrics._run_network(run_dir)
    if path and not os.path.isabs(path):
        path = os.path.join(run_dir, path)
    if not path or not os.path.exists(path):
        raise SystemExit('%s holds neither output/output_network.xml.gz nor the '
                         'input network its config names' % run_dir)
    return path


def road_network(path):
    """{link id: dict(to, length, freespeed, capacity, lanes, highway, type,
    name)} - capacity in vehicles per hour at full population, as MATSim holds
    it."""
    net, cur = {}, None
    with open_table(str(path)) as fh:
        for line in fh:
            m = _LINK.search(line)
            if m:
                cur = m.group(1)
                net[cur] = dict(to=m.group(3), length=float(m.group(4)),
                                freespeed=float(m.group(5)), capacity=float(m.group(6)),
                                lanes=float(m.group(7)))
                if line.rstrip().endswith('/>'):
                    cur = None
                continue
            if cur is None:
                continue
            if '<attribute' in line:
                a = _ATTR.search(line)
                if a and a.group(1) in _LINK_ATTRS:
                    net[cur][_LINK_ATTRS[a.group(1)]] = a.group(2)
            elif '</link>' in line:
                cur = None
    return net


def road_class(link):
    """The OSM highway tag, else the network's own `type`, else '?'."""
    return link.get('highway') or link.get('type') or '?'


def road_delays(payload, net, top):
    """Road links ranked by excess vehicle-hours over free flow.

    From the telemetry's per-link [id, volume, typical, mean]: the mean
    traversal's delay ratio is `1 + excess / max(free-flow, free-flow of
    min_stretch_m)` (the payload states it), so a link's excess vehicle-hours
    are volume x (mean - 1) x that denominator. Volumes are the run's SAMPLED
    road-vehicle traversals; nothing is scaled.
    """
    if payload.get('tolerance_s') is None or any(len(r) < 4 for r in payload['links'][:1]):
        raise SystemExit('telemetry_links.json predates the [id, volume, typical, mean] '
                         'payload (15 September 2026); it carries no mean delay')
    stretch = float(payload['min_stretch_m'])
    rows, traversals = [], Counter()
    for lid, vol, _typical, mean in (r[:4] for r in payload['links']):
        link = net.get(lid)
        if link is None:
            continue
        traversals[road_class(link)] += vol
        if mean <= 1 or link['freespeed'] <= 0:
            continue
        excess_h = vol * (mean - 1) * max(link['length'], stretch) / link['freespeed'] / 3600.0
        rows.append((excess_h, lid, vol, mean, link))
    rows.sort(key=lambda r: (-r[0], r[1]))
    total = sum(r[0] for r in rows)

    def share(x):
        return round(100.0 * x / total, 2) if total else None
    by_class, cap_lane = Counter(), defaultdict(set)
    by_node = Counter()
    for excess_h, _lid, _vol, _mean, link in rows:
        c = road_class(link)
        by_class[c] += excess_h
        cap_lane[c].add(round(link['capacity'] / max(link['lanes'], 1.0), 1))
        by_node[link['to']] += excess_h
    return dict(
        iteration=payload.get('iteration'), scope=payload.get('scope'),
        window=[payload.get('window_from'), payload.get('window_to')],
        min_stretch_m=stretch, tolerance_s=payload.get('tolerance_s'),
        delayed_links=len(rows), excess_vehicle_hours_sampled=round(total, 1),
        top_k_share_pct={str(k): share(sum(r[0] for r in rows[:k])) for k in (10, 50, 200, 1000)},
        by_class=[dict(road_class=c, excess_share_pct=share(v), excess_vehicle_hours=round(v, 1),
                       traversals=traversals[c], capacity_per_lane_seen=sorted(cap_lane[c])[:4])
                  for c, v in by_class.most_common()],
        top_nodes=[dict(node=n, excess_vehicle_hours=round(v, 1)) for n, v in by_node.most_common(10)],
        top_links=[dict(link=lid, excess_vehicle_hours=round(x, 1), volume=vol, mean_ratio=mean,
                        road_class=road_class(link), name=link.get('name', ''),
                        capacity=link['capacity'], lanes=link['lanes'],
                        freespeed=link['freespeed'], length=round(link['length'], 1), to=link['to'])
                   for x, lid, vol, mean, link in rows[:top]],
        note='excess over free flow of the mean traversal, sampled volumes; a queue, a '
             'signal and a merge all read as excess - the class and node tables say '
             'where, not why')


def load_band(hours):
    """The REPORTING band of a link's trip-end load, in hours of its own sampled
    capacity: under 1, 1-4, 4-12, at least 12."""
    if hours < 1:
        return '<1h'
    if hours < 4:
        return '1-4h'
    if hours < 12:
        return '4-12h'
    return '>=12h'


LOAD_BANDS = ('<1h', '1-4h', '4-12h', '>=12h')
# the trips columns access_load reads (iteration_reading.table's projection)
ACCESS_COLUMNS = ('main_mode', 'start_link', 'end_link', 'trav_time', 'traveled_distance')
# the bands from which a link's trip ends are the offending ones
OFFENDING_BANDS = frozenset(LOAD_BANDS[2:])


def access_load(trips, net, fraction, top):
    """Road-vehicle trip ends per link against the link's own sampled hourly
    capacity (capacity x fraction): the hours of that capacity its starts and
    ends need. Every trip is banded by its WORSE end, with mean time, km and
    speed per band; the offending links (4 h and over) by class; the worst
    links. A link absent from the network needs nothing."""
    import extract_metrics as em                                 # noqa: PLC0415
    starts, ends, kept = Counter(), Counter(), []
    for t in trips:
        if t['main_mode'] not in em.ROAD_VEHICLE_MODES:
            continue
        s, e = t['start_link'], t['end_link']
        starts[s] += 1
        ends[e] += 1
        kept.append((s, e, em.trip_seconds(t['trav_time']), float(t['traveled_distance'] or 0)))
    need = {}
    for lid in set(starts) | set(ends):
        cap = net[lid]['capacity'] * fraction if lid in net else 0.0
        need[lid] = (starts[lid] + ends[lid]) / cap if cap > 0 else 0.0
    agg = {b: [0, 0.0, 0.0] for b in LOAD_BANDS}
    for s, e, secs, metres in kept:
        a = agg[load_band(max(need[s], need[e]))]
        a[0] += 1
        a[1] += secs
        a[2] += metres
    n = len(kept)
    bands = [dict(band=b, trips=c, share_pct=round(100.0 * c / n, 2) if n else None,
                  mean_time_min=round(secs / c / 60.0, 2) if c else None,
                  mean_km=round(metres / c / 1000.0, 3) if c else None,
                  speed_kmh=round(metres / secs * 3.6, 2) if secs else None)
             for b, (c, secs, metres) in agg.items()]
    cls_links, cls_ends = Counter(), Counter()
    for lid, x in need.items():
        if load_band(x) in OFFENDING_BANDS:
            c = road_class(net.get(lid, {}))
            cls_links[c] += 1
            cls_ends[c] += starts[lid] + ends[lid]
    worst = sorted(need.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return dict(
        road_vehicle_trips=n, fraction=fraction, bands=bands,
        offending_bands=sorted(OFFENDING_BANDS, key=LOAD_BANDS.index),
        offending_by_class=[dict(road_class=c, links=cls_links[c], trip_ends=v)
                            for c, v in cls_ends.most_common()],
        worst_links=[dict(link=lid, road_class=road_class(net.get(lid, {})),
                          capacity=net[lid]['capacity'] if lid in net else None,
                          trip_ends=starts[lid] + ends[lid], hours_needed=round(x, 2))
                     for lid, x in worst],
        note='hours = (trip starts + ends on the link) / (capacity x sample fraction): '
             'the hours of its own capacity the link needs just to let its trips on '
             'and off, before any through traffic; bands are reporting bands')


def road_readings(name, iteration, top, road, access):
    """`--road` and/or `--access` over one parse of the network."""
    run_dir = results_store.resolve_or_die(name)
    run_name = os.path.basename(os.path.normpath(run_dir))
    net = road_network(network_path(run_dir))
    if road:
        path = os.path.join(run_dir, 'output', 'telemetry_links.json')
        if not os.path.exists(path):
            raise SystemExit('%s has no output/telemetry_links.json - the run predates '
                             'the telemetry module' % run_name)
        with open(path, encoding='utf-8') as fh:
            payload = json.load(fh)
        if iteration is not None and payload.get('iteration') != iteration:
            raise SystemExit('telemetry_links.json holds iteration %s, not %s: it keeps '
                             'only the newest window' % (payload.get('iteration'), iteration))
        report = dict(run=run_name, **road_delays(payload, net, top))
        _write(run_name, '_road_link_delays_it%s.json' % report['iteration'], report)
        print_road_delays(report)
    if access:
        if iteration is None:
            raise SystemExit('--access reads one iteration\'s trips table: give --iteration')
        import report_mode_ridership as rmr                      # noqa: PLC0415
        fraction = rmr.sample_fraction(run_dir)
        if not fraction:
            raise SystemExit('REFUSED: %s carries no sample fraction in _meta.json or '
                             '_run.json, so a link\'s sampled capacity is unknown' % run_name)
        try:
            trips = iteration_reading.table(run_dir, 'trips', iteration, columns=ACCESS_COLUMNS)
        except FileNotFoundError as exc:
            raise SystemExit(str(exc))
        report = dict(run=run_name, iteration=iteration, **access_load(trips, net, fraction, top))
        _write(run_name, '_access_load_it%d.json' % iteration, report)
        print_access_load(report)


def print_road_delays(r):
    print('ROAD LINK DELAY  %s  it.%s  %s-%s  (sampled volumes)'
          % (r['run'], r['iteration'], r['window'][0], r['window'][1]))
    print('links with delay %d; excess vehicle-hours %.0f; top-k share %s'
          % (r['delayed_links'], r['excess_vehicle_hours_sampled'],
             ', '.join('%s %.1f %%' % kv for kv in r['top_k_share_pct'].items())))
    for c in r['by_class'][:14]:
        print('  %-16s %5.1f %%  traversals %9d  cap/lane %s'
              % (c['road_class'][:16], c['excess_share_pct'], c['traversals'],
                 c['capacity_per_lane_seen']))
    print('top nodes: %s' % ', '.join('%s %.0f' % (n['node'], n['excess_vehicle_hours'])
                                      for n in r['top_nodes']))
    for l in r['top_links']:
        print('  %-10s %7.0f veh-h  vol %6d  x%-7.1f %-14s %-24s cap %5.0f lanes %.0f'
              % (l['link'], l['excess_vehicle_hours'], l['volume'], l['mean_ratio'],
                 l['road_class'][:14], l['name'][:24], l['capacity'], l['lanes']))


def print_access_load(r):
    print('TRIP-END LOAD  %s  it.%d  %d road-vehicle trips, by the worse end\'s hours of '
          'its link\'s own sampled capacity' % (r['run'], r['iteration'], r['road_vehicle_trips']))
    for b in r['bands']:
        if b['trips']:
            print('  %-6s %7d trips (%4.1f %%)  mean %5.1f min  %5.2f km  %4.1f km/h'
                  % (b['band'], b['trips'], b['share_pct'], b['mean_time_min'],
                     b['mean_km'], b['speed_kmh']))
    print('offending links (%s) by class:' % ', '.join(r['offending_bands']))
    for c in r['offending_by_class'][:8]:
        print('  %-14s %5d links %7d ends' % (c['road_class'][:14], c['links'], c['trip_ends']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--run', required=True)
    parser.add_argument('--iteration', type=int,
                        help='required for the transit reading and --access; --road '
                             'checks it against the telemetry\'s own iteration')
    parser.add_argument('--top', type=int, required=True, help='Number of ranked links to retain')
    parser.add_argument('--road', action='store_true',
                        help='road links by excess vehicle-hours from telemetry_links.json '
                             '(road_delays)')
    parser.add_argument('--access', action='store_true',
                        help='road-vehicle trip ends per link against its sampled '
                             'capacity (access_load)')
    args = parser.parse_args()
    if args.top <= 0:
        parser.error('--top must be positive')
    if args.road or args.access:
        road_readings(args.run, args.iteration, args.top, args.road, args.access)
    else:
        if args.iteration is None:
            parser.error('the transit reading needs --iteration')
        analyse(args.run, args.iteration, args.top)
