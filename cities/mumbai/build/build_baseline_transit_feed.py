"""Combine acquired bus trips with provisional suburban, metro and ferry supply.

Generated service frequencies and running times are model assumptions from the
registry, not recovered operating timetables. Native stop order is retained;
the output is intended for broad behavioural development before corridor work.
"""
from collections import Counter
import csv
import io
import json
from pathlib import Path
import zipfile

import pyogrio
from pyproj import Geod

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'schedules/baseline_multimodal.zip': [
        'schedules/baseline_bus.zip', 'registry/A_baseline_services.json',
        'data/processed/observed/osm_transport_relations.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_research.gpkg'],
    'data/processed/acquisition/baseline_transit_feed.json': [
        'schedules/baseline_bus.zip', 'registry/A_baseline_services.json',
        'data/processed/observed/osm_transport_relations.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/observed/water_service_directory.csv',
        'data/processed/geospatial/osm_research.gpkg'],
}
for _k in OUTPUT_INPUTS:
    if 'data/processed/observed/water_service_directory.csv' not in OUTPUT_INPUTS[_k]:
        OUTPUT_INPUTS[_k].append('data/processed/observed/water_service_directory.csv')


def directory_clock(raw, default):
    """A directory departure string as seconds after midnight, or the default.

    The Maritime Board prints '05.30 AM', '12.00 AM' (the last sailing, so
    midnight is the END of the day), '06:30 HRS', '09:00 PM (BHAYANDER)' and
    'In-between 07:00 HRS to 09:00 HRS' (the first of a pair of windows); the
    first clock in the string is read, in the 12-hour or the 24-hour form.
    """
    import re as _re
    m = _re.search(r'(\d{1,2})[.:](\d{2})\s*(AM|PM|HRS)?', raw or '', _re.I)
    if not m:
        return default
    h, mi, suffix = int(m.group(1)), int(m.group(2)), (m.group(3) or '').upper()
    if suffix == 'PM' and h != 12:
        h += 12
    if suffix == 'AM' and h == 12:
        h = 24
    return h * 3600 + mi * 60


def rows(name):
    with Path(city.path(name)).open(encoding='utf-8', newline='') as stream:
        yield from csv.DictReader(stream)


def clock(seconds):
    h, rest = divmod(round(seconds), 3600)
    m, s = divmod(rest, 60)
    return f'{h:02d}:{m:02d}:{s:02d}'


def table(rows_, fields):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows_)
    return out.getvalue().encode('utf-8')


def main():
    csv.field_size_limit(10_000_000)
    cfg = registry.load()
    inputs = OUTPUT_INPUTS['schedules/baseline_multimodal.zip']
    hashes = {p: fingerprint(Path(city.path(p))) for p in inputs}
    geod = Geod(ellps='WGS84')
    points = {r['osm_node_id']: r for r in rows('data/processed/observed/osm_transport_points.csv')}
    networks, types = cfg.get('A.baseline_transit.networks'), cfg.get('A.baseline_transit.gtfs_route_types')
    selected = []
    for row in rows('data/processed/observed/osm_transport_relations.csv'):
        tags = json.loads(row['all_tags_json'])
        mode = tags.get('route')
        if (mode == 'ferry' or tags.get('network') in networks.get(mode, [])) and not any(
                k in tags for k in ('construction', 'proposed', 'disused', 'abandoned')):
            selected.append(row)
    new_stops, new_routes, new_trips, new_times = {}, [], [], []
    report, skipped = [], []
    start, end = cfg.get('A.baseline_transit.service_window_s')
    line_windows = cfg.get('A.baseline_transit.line_windows_s')   # published first/last trains, per relation (9.208)
    peaks, peak_headway, offpeak = cfg.get('A.baseline_transit.peak_windows_s'), cfg.get('A.baseline_transit.peak_headway_s'), cfg.get('A.baseline_transit.offpeak_headway_s')
    speed, dwell, factor = cfg.get('A.baseline_transit.commercial_speed_kmh'), cfg.get('A.baseline_transit.stop_dwell_s'), cfg.get('A.baseline_transit.distance_multiplier')
    with zipfile.ZipFile(city.path('schedules/baseline_bus.zip')) as incoming:
        content = {n: incoming.read(n) for n in incoming.namelist()}
    calendars = list(csv.DictReader(io.StringIO(content['calendar.txt'].decode('utf-8-sig'))))
    if len(calendars) != 1:
        raise ValueError('Expected one baseline calendar to make provisional service dates explicit')
    service_id = calendars[0]['service_id']
    for row in sorted(selected, key=lambda r: int(r['osm_relation_id'])):
        identity, mode = row['osm_relation_id'], row['route_tag']
        members = json.loads(row['ordered_members_json'])
        stops = [m for m in members if m['role'].startswith('stop')]
        if len(stops) < 2:
            stops = [m for m in members if m['role'].startswith('platform')]
        sequence = []
        ferry_length = None
        if mode == 'ferry':
            way_ids = [m['ref'] for m in members if m['type'] == 'way']
            if len(way_ids) != 1 or not way_ids[0].isdigit():
                raise ValueError('Ferry requires a single native route way in this baseline')
            shapes = pyogrio.read_dataframe(city.path('data/processed/geospatial/osm_research.gpkg'),
                layer='lines', where="osm_id = '" + way_ids[0] + "'")
            if len(shapes) != 1:
                raise ValueError('Ferry geometry missing or duplicated')
            shape = shapes.iloc[0].geometry
            coords = list(shape.coords)
            ferry_length = abs(geod.line_length(*zip(*coords)))
            for index, (lon, lat) in enumerate((coords[0], coords[-1])):
                sid = f'BASE_FERRY_{identity}_{index}'
                new_stops[sid] = dict(stop_id=sid, stop_name=f'Mapped ferry endpoint {identity}/{index}',
                                     stop_lon=lon, stop_lat=lat)
                sequence.append(sid)
        else:
            for member in stops:
                if member['type'] != 'node' or member['ref'] not in points:
                    raise ValueError('Selected transit stop has no acquired coordinate')
                point = points[member['ref']]
                sid = 'BASE_OSM_' + member['ref']
                new_stops[sid] = dict(stop_id=sid, stop_name=point['name'] or sid,
                    stop_lon=float(point['longitude_deg']), stop_lat=float(point['latitude_deg']))
                if not sequence or sequence[-1] != sid:
                    sequence.append(sid)
        if len(sequence) < 2:
            skipped.append(dict(osm_relation_id=identity, reason='fewer_than_two_stops'))
            continue
        # Ferry ways describe a water connection rather than separate directed
        # PTv2 trips; the provisional service explicitly operates both ways.
        directions = [sequence, sequence[::-1]] if mode == 'ferry' else [sequence]
        for direction, stop_ids in enumerate(directions):
            rid = f'BASE_{identity}_{direction}'
            new_routes.append(dict(route_id=rid, agency_id='BASELINE', route_short_name=row['ref'],
                                   route_long_name=row['name'] or rid, route_type=types[mode]))
            offsets, elapsed = [(0, 0)], 0
            for before, after in zip(stop_ids, stop_ids[1:]):
                a, b = new_stops[before], new_stops[after]
                length = ferry_length if ferry_length is not None else geod.inv(
                    a['stop_lon'], a['stop_lat'], b['stop_lon'], b['stop_lat'])[2] * factor[mode]
                if length <= 0:
                    raise ValueError('Distinct consecutive stops have zero separation')
                arrival = elapsed + length / (speed[mode] / 3.6)
                elapsed = arrival + dwell[mode]
                offsets.append((round(arrival), round(elapsed)))
            first, last = line_windows.get(identity, [start, end])
            departure, departures = first, 0
            while departure < last:
                tid = f'{rid}_{departure}'
                new_trips.append(dict(route_id=rid, service_id=service_id, trip_id=tid,
                                      direction_id=direction))
                for index, (sid, (arr, dep)) in enumerate(zip(stop_ids, offsets)):
                    new_times.append(dict(trip_id=tid, arrival_time=clock(departure + arr),
                        departure_time=clock(departure + dep), stop_id=sid, stop_sequence=index))
                headway = peak_headway[mode] if any(a <= departure < b for a, b in peaks) else offpeak[mode]
                if headway <= 0:
                    raise ValueError('Headway must be positive')
                departure += headway
                departures += 1
            report.append(dict(route_id=rid, osm_relation_id=identity, mode=mode,
                stops_count=len(stop_ids), departures_count=departures, duration_s=round(elapsed),
                window_s=[first, last],
                geometry_source='mapped_native_stops_or_ferry_way',
                timetable_source=('published_window_provisional_headway' if identity in line_windows
                                  else 'modelled_from_provisional_registry')))
    # The Maritime Board's crossings (9.207): a directory route between the two OSM
    # terminals the registry names, on the straight water line between them (the
    # extract holds no route=ferry way for these), its window the directory's first
    # and last departure, the headway the provisional ferry headway, its vessel the
    # fleet profile the crossing table names.
    directory = {r['directory_route_id']: r for r in rows('data/processed/observed/water_service_directory.csv')}
    for route_id, spec in sorted(cfg.get('A.baseline_transit.directory_crossings').items(), key=lambda kv: int(kv[0])):
        entry = directory[route_id]
        sequence = []
        for node in (spec['from'], spec['to']):
            if node not in points:
                raise ValueError('directory crossing %s names OSM terminal %s, which the transport points do not hold' % (route_id, node))
            point = points[node]
            sid = 'BASE_OSM_' + node
            new_stops[sid] = dict(stop_id=sid, stop_name=point['name'] or sid,
                                  stop_lon=float(point['longitude_deg']), stop_lat=float(point['latitude_deg']))
            sequence.append(sid)
        a, b = new_stops[sequence[0]], new_stops[sequence[1]]
        length = geod.inv(a['stop_lon'], a['stop_lat'], b['stop_lon'], b['stop_lat'])[2] * factor['ferry']
        if length <= 0:
            raise ValueError('directory crossing %s has coincident terminals' % route_id)
        first = directory_clock(entry['first_departure_raw'], start)
        last = directory_clock(entry['last_departure_raw'], end)
        if last <= first:
            last = end
        for direction, stop_ids in enumerate([sequence, sequence[::-1]]):
            rid = f'BASE_MMB_{route_id}_{direction}'
            new_routes.append(dict(route_id=rid, agency_id='BASELINE', route_short_name='MMB ' + route_id,
                                   route_long_name=entry['route_name'], route_type=types['ferry']))
            arrival = length / (speed['ferry'] / 3.6)
            offsets = [(0, 0), (round(arrival), round(arrival + dwell['ferry']))]
            departure, departures = first, 0
            while departure < last:
                tid = f'{rid}_{departure}'
                new_trips.append(dict(route_id=rid, service_id=service_id, trip_id=tid, direction_id=direction))
                for index, (sid, (arr, dep)) in enumerate(zip(stop_ids, offsets)):
                    new_times.append(dict(trip_id=tid, arrival_time=clock(departure + arr),
                                          departure_time=clock(departure + dep), stop_id=sid, stop_sequence=index))
                headway = peak_headway['ferry'] if any(p <= departure < q for p, q in peaks) else offpeak['ferry']
                departure += headway
                departures += 1
            report.append(dict(route_id=rid, directory_route_id=route_id, mode='ferry', stops_count=2,
                               departures_count=departures, duration_s=round(arrival + dwell['ferry']),
                               window_s=[first, last], length_m=round(length),
                               geometry_source='straight_water_line_between_osm_terminals',
                               timetable_source='directory_window_provisional_headway'))
    additions = {'agency.txt': [dict(agency_id='BASELINE', agency_name='Provisional model services',
                    agency_url='https://www.openstreetmap.org', agency_timezone='Asia/Kolkata')],
                 'stops.txt': list(new_stops.values()), 'routes.txt': new_routes,
                 'trips.txt': new_trips, 'stop_times.txt': new_times}
    for name, extra in additions.items():
        reader = csv.DictReader(io.StringIO(content[name].decode('utf-8-sig')))
        fields = list(reader.fieldnames)
        for row in extra:
            for key in row:
                if key not in fields:
                    fields.append(key)
        content[name] = table([*reader, *extra], fields)
    output = Path(city.path('schedules/baseline_multimodal.zip'))
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(content.items()):
            entry = zipfile.ZipInfo(name)
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    audit = dict(source='modelled_provisional_service_supply', input_sha256=hashes,
        output_sha256=fingerprint(output), generated_routes=report, skipped=skipped,
        generated_route_counts=dict(Counter(r['mode'] for r in report)),
        limitation='Operating frequencies/times are provisional; historical/current operation and corridor details require later refinement. No ridership targets were used.')
    Path(city.path('data/processed/acquisition/baseline_transit_feed.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('generated_route_counts', 'skipped')}))


if __name__ == '__main__':
    main()
