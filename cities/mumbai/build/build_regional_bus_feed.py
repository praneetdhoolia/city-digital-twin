"""Extend the broad baseline with operator-published regional bus evidence.

NMMT departure clocks and stop sequences are retained. Pattern running times
combine usable published segment times with a geographic feasibility floor.
MBMT frequency is a pooled-fleet derivation, not an observed timetable.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import zipfile

from pyproj import Geod

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'schedules/baseline_regional.zip': [
        'schedules/baseline_multimodal.zip', 'registry/A_regional_buses.json',
        'data/raw/transit/nmmt_current_stops_*.json',
        'data/processed/observed/nmmt_departures.csv',
        'data/processed/observed/nmmt_stop_times.csv',
        'data/processed/observed/nmmt_route_stop_snapshots.csv',
        'data/processed/observed/mbmt_route_stops.csv',
        'data/processed/observed/mbmt_published_bus_allocations.csv'],
    'data/processed/acquisition/baseline_regional_buses.json': [
        'schedules/baseline_multimodal.zip', 'registry/A_regional_buses.json',
        'data/raw/transit/nmmt_current_stops_*.json',
        'data/processed/observed/nmmt_departures.csv',
        'data/processed/observed/nmmt_stop_times.csv',
        'data/processed/observed/nmmt_route_stop_snapshots.csv',
        'data/processed/observed/mbmt_route_stops.csv',
        'data/processed/observed/mbmt_published_bus_allocations.csv'],
}


def rows(path):
    with Path(city.path(path)).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def clock(seconds):
    hour, rest = divmod(round(seconds), 3600)
    minute, second = divmod(rest, 60)
    return f'{hour:02d}:{minute:02d}:{second:02d}'


def segment_seconds(previous, current, maximum):
    """Keep positive same-day differences; ambiguous clock reversals stay missing.

    An overnight trip can still be represented: its affected segment is derived
    from other trips on the pattern, or from distance, and offsets exceed 24h.
    This avoids interpreting a small source reversal as a 24-hour bus journey.
    """
    if not previous or not current:
        return None
    difference = int(current) - int(previous)
    return difference if 0 < difference <= maximum else None


def pattern_offsets(stops, observations, geod, cfg):
    offsets = [0]
    sources = Counter()
    for i, (before, after) in enumerate(zip(stops, stops[1:])):
        distance = geod.inv(before['stop_lon'], before['stop_lat'],
                            after['stop_lon'], after['stop_lat'])[2]
        floor = distance * cfg['distance_multiplier'] / cfg['speed_ms'] + cfg['dwell_s']
        candidates = observations[i] if observations else []
        published = statistics.median(candidates) if candidates else None
        if published is not None and published > floor * cfg['maximum_delay_ratio']:
            sources['published_timing_rejected_as_outlier'] += 1
            published = None
        interval = max(floor, published or 0)
        sources['published_median' if published is not None and published >= floor
                else 'geographic_floor_over_published' if published is not None
                else 'geographic_derivation'] += 1
        offsets.append(offsets[-1] + math.ceil(interval))
    return offsets, sources


def pooled_headway(durations, fleet, terminal_dwell):
    """Equal pattern frequency whose total vehicle-hours fit the stated fleet.

    Directions are already separate patterns. Sum each one-way duration once;
    multiplying by two again would halve the provided service incorrectly.
    """
    if fleet <= 0 or not durations or any(t <= 0 for t in durations):
        raise ValueError('Fleet and all directed pattern durations must be positive')
    return math.ceil(sum(t + terminal_dwell for t in durations) / fleet)


def append_table(content, name, additions):
    reader = csv.DictReader(io.StringIO(content[name].decode('utf-8-sig')))
    fields = list(reader.fieldnames)
    existing = list(reader)
    for row in additions:
        for key in row:
            if key not in fields:
                fields.append(key)
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(existing + additions)
    content[name] = out.getvalue().encode('utf-8')


def main():
    if Path(city.path()).resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError('Select the city owning this adapter')
    cfg = registry.load()
    running = cfg.get('A.regional_bus.running_time')
    maximum = cfg.get('A.regional_bus.max_published_segment_s')
    geod = Geod(ellps='WGS84')
    with zipfile.ZipFile(city.path('schedules/baseline_multimodal.zip')) as archive:
        content = {n: archive.read(n) for n in archive.namelist()}
    calendars = list(csv.DictReader(io.StringIO(content['calendar.txt'].decode('utf-8-sig'))))
    if len(calendars) != 1:
        raise ValueError('Broad baseline must identify one explicit model calendar')
    service_id = calendars[0]['service_id']
    provenance = json.loads(Path(city.path('data/raw/transit/provenance_nmmt_current_stops.json'))
                            .read_text(encoding='utf-8'))['files'][0]
    station_path = Path(city.path(provenance['path']))
    if fingerprint(station_path) != provenance['sha256']:
        raise ValueError('Acquired station bytes changed')
    station_data = json.loads(station_path.read_text(encoding='utf-8'))['data']
    stations = {}
    for row in station_data:
        identity = str(row['stationid'])
        value = dict(stop_id='NMMT_' + identity, stop_name=row['displaysationname'],
                     stop_lon=float(row['longitude']), stop_lat=float(row['lattitude']))
        if identity in stations and stations[identity] != value:
            raise ValueError('Conflicting operator station identity: ' + identity)
        if not (-180 <= value['stop_lon'] <= 180 and -90 <= value['stop_lat'] <= 90):
            raise ValueError('Invalid operator station coordinate: ' + identity)
        stations[identity] = value
    times = defaultdict(list)
    for row in rows('data/processed/observed/nmmt_stop_times.csv'):
        times[row['route_id'], row['trip_id']].append(row)
    patterns = defaultdict(list)
    snapshots = defaultdict(list)
    for row in rows('data/processed/observed/nmmt_route_stop_snapshots.csv'):
        if row['queried_route_id'] == row['returned_route_id']:
            snapshots[row['queried_route_id'], row['direction']].append(row)
    route_sequences = defaultdict(list)
    for (route, _), sequence in sorted(snapshots.items()):
        sequence.sort(key=lambda r: int(r['response_sequence']))
        route_sequences[route].append(tuple(r['station_id'] for r in sequence))
    skipped = []
    for trip in rows('data/processed/observed/nmmt_departures.csv'):
        identity = trip['route_id'], trip['trip_id']
        sequence = sorted(times.get(identity, []), key=lambda r: int(r['stop_sequence']))
        if len(sequence) < 2 or any(r['station_id'] not in stations for r in sequence):
            skipped.append(dict(operator='NMMT', identity=identity, reason='incomplete_stop_geometry'))
            continue
        if not trip['departure_clock_s']:
            skipped.append(dict(operator='NMMT', identity=identity, reason='missing_departure_clock'))
            continue
        candidates = [s for s in route_sequences[trip['route_id']]
                      if s[0] == trip['from_station_id'] and s[-1] == trip['to_station_id']]
        if len(candidates) != 1 or any(s not in stations for s in candidates[0]):
            skipped.append(dict(operator='NMMT', identity=identity,
                reason='no_unique_operator_route_sequence_matching_published_endpoints'))
            continue
        patterns[trip['route_id'], candidates[0]].append((trip, sequence))
    additions = {n: [] for n in ('agency.txt', 'routes.txt', 'trips.txt', 'stop_times.txt')}
    used_stops = {}
    report = []

    def add_pattern(operator, rid, label, stops, offsets, departures):
        additions['routes.txt'].append(dict(route_id=rid, agency_id=operator,
            route_short_name=label, route_long_name=label, route_type=3))
        for stop in stops:
            used_stops[stop['stop_id']] = stop
        for trip_id, departure in departures:
            additions['trips.txt'].append(dict(route_id=rid, service_id=service_id, trip_id=trip_id))
            for index, (stop, offset) in enumerate(zip(stops, offsets), start=1):
                time = clock(departure + offset)
                additions['stop_times.txt'].append(dict(trip_id=trip_id, arrival_time=time,
                    departure_time=time, stop_id=stop['stop_id'], stop_sequence=index))

    for (route, station_ids), trips in sorted(patterns.items()):
        signature = hashlib.sha256(','.join(station_ids).encode('utf-8')).hexdigest()[:16]
        rid = f'NMMT_{route}_{signature}'
        stops = [stations[s] for s in station_ids]
        observations = [[] for _ in station_ids[1:]]
        rejected = 0
        differing_sequences = 0
        for _, sequence in trips:
            differing_sequences += tuple(r['station_id'] for r in sequence) != station_ids
            by_pair = defaultdict(list)
            for a, b in zip(sequence, sequence[1:]):
                duration = segment_seconds(a['stop_clock_s'], b['stop_clock_s'], maximum)
                if duration is None:
                    rejected += 1
                else:
                    by_pair[a['station_id'], b['station_id']].append(duration)
            for i, pair in enumerate(zip(station_ids, station_ids[1:])):
                observations[i].extend(by_pair[pair])
        offsets, sources = pattern_offsets(stops, observations, geod, running)
        departures = [(f'NMMT_{t["route_id"]}_{t["trip_id"]}', int(t['departure_clock_s']))
                      for t, _ in trips]
        add_pattern('NMMT', rid, trips[0][0]['route_number'], stops, offsets, departures)
        report.append(dict(operator='NMMT', route_id=rid, source_route_id=route,
            departures_count=len(departures), stops_count=len(stops), duration_s=offsets[-1],
            rejected_segment_clock_differences=rejected, segment_timing_sources=dict(sources),
            trip_sequences_reconciled_to_operator_route=differing_sequences,
            departure_source='published_departure_clock', calendar_source='provisional_baseline_calendar'))

    mbmt = defaultdict(list)
    for row in rows('data/processed/observed/mbmt_route_stops.csv'):
        mbmt[row['route_id']].append(row)
    directed = []
    for rid, sequence in sorted(mbmt.items()):
        sequence.sort(key=lambda r: int(r['response_sequence']))
        if len(sequence) < 2:
            skipped.append(dict(operator='MBMT', identity=rid, reason='fewer_than_two_stops'))
            continue
        stops = [dict(stop_id=f'MBMT_{rid}_{r["response_sequence"]}',
                      stop_name=r['station_name_raw'], stop_lon=float(r['api_long1_deg']),
                      stop_lat=float(r['api_lat1_deg'])) for r in sequence]
        offsets, sources = pattern_offsets(stops, None, geod, running)
        directed.append((rid, sequence[0]['route_name_raw'], stops, offsets, sources))
    day = cfg.get('A.regional_bus.allocation_day_label')
    allocations = [r for r in rows('data/processed/observed/mbmt_published_bus_allocations.csv')
                   if r['day_type_raw'] == day and r['is_subtotal'] == 'False']
    fleet = sum(int(r['buses_count']) for r in allocations)
    layover = cfg.get('A.regional_bus.terminal_layover_s')
    headway = pooled_headway([d[3][-1] for d in directed], fleet, layover)
    start, end = cfg.get('A.regional_bus.service_window_s')
    for rid, label, stops, offsets, sources in directed:
        route_id = 'MBMT_' + rid
        departures = [(f'{route_id}_{t}', t) for t in range(start, end, headway)]
        add_pattern('MBMT', route_id, label, stops, offsets, departures)
        report.append(dict(operator='MBMT', route_id=route_id, source_route_id=rid,
            departures_count=len(departures), stops_count=len(stops), duration_s=offsets[-1],
            segment_timing_sources=dict(sources), departure_source='derived_equal_frequency_pooled_fleet',
            calendar_source='provisional_baseline_calendar'))
    for operator, url in cfg.get('A.regional_bus.agency_urls').items():
        additions['agency.txt'].append(dict(agency_id=operator, agency_name=operator,
            agency_url=url, agency_timezone=cfg.get('A.regional_bus.timezone')))
    additions['stops.txt'] = list(used_stops.values())
    for name, data in additions.items():
        append_table(content, name, data)
    output = Path(city.path('schedules/baseline_regional.zip'))
    with zipfile.ZipFile(output, 'w') as archive:
        for name, data in sorted(content.items()):
            entry = zipfile.ZipInfo(name)
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    inputs = [p for p in OUTPUT_INPUTS['schedules/baseline_regional.zip'] if '*' not in p]
    inputs.append(provenance['path'])
    audit = dict(source='derived_provisional_regional_supply',
        input_sha256={p: fingerprint(Path(city.path(p))) for p in inputs},
        output_sha256=fingerprint(output), generated_patterns=report, skipped=skipped,
        route_counts=dict(Counter(r['operator'] for r in report)),
        departure_counts={op: sum(r['departures_count'] for r in report if r['operator'] == op)
                          for op in ('NMMT', 'MBMT')},
        mbmt_pooled_fleet=dict(published_allocation_sum_buses=fleet, allocation_day=day,
            directed_patterns=len(directed), terminal_layover_s=layover, derived_headway_s=headway,
            rule='sum_one_way_pattern_cycle_times_divided_by_published_allocation_sum'),
        limitations=[
            'Published calendars and actual current operation are unverified; baseline day use is provisional.',
            'NMMT route snapshots define stop order; trip lists without matching route endpoints are quarantined explicitly.',
            'NMMT pattern times are derived, not exact trip timetables or observed running times; timing outliers use geography.',
            'MBMT published allocation sum differs from its printed subtotal; route-level allocation crosswalk unresolved.',
            'MBMT pooled equal frequency constrains approximate input fleet-hours, not mapped runtime, actual allocations or vehicle circulation.',
            'Full regional operator coverage, stop placement, capacities and ridership remain unvalidated.'])
    Path(city.path('data/processed/acquisition/baseline_regional_buses.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('route_counts', 'departure_counts', 'mbmt_pooled_fleet')}))
    print('Quarantined departures:', len(skipped), dict(Counter(r['reason'] for r in skipped)))


if __name__ == '__main__':
    main()
