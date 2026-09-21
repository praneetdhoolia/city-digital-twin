"""Audit passenger-directory joins, cumulative fields and both map axis orders."""
from collections import Counter
import json
import math
from pathlib import Path
from statistics import median

from pyproj import Geod
import city
import harvest
from acquire_mbmt_sources import HARVEST_OF_KIND
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/mbmt_route_details.csv': [
        'data/raw/transit/mbmt_route_details.zip', 'data/raw/transit/mbmt_routes_*.json',
        'data/raw/transit/mbmt_routes_page_*.html'],
    'data/processed/observed/mbmt_route_stops.csv': [
        'data/raw/transit/mbmt_route_stops.zip', 'data/raw/transit/mbmt_routes_*.json'],
    'data/processed/observed/mbmt_route_vertices.csv': [
        'data/raw/transit/mbmt_route_alignments.zip', 'data/raw/transit/mbmt_routes_*.json'],
    'data/processed/acquisition/mbmt_route_audit.json': [
        'data/raw/transit/mbmt_routes_*.json', 'data/raw/transit/mbmt_route_details.zip',
        'data/raw/transit/mbmt_route_stops.zip', 'data/raw/transit/mbmt_route_alignments.zip',
        'data/raw/transit/mbmt_routes_page_*.html', 'data/raw/transit/mbmt_public_map_script_*.js'],
}
LISTINGS = {kind: harvest.members(which.id, which.category) if which.provenance.exists() else {}
            for kind, which in HARVEST_OF_KIND.items()}


def read(sid):
    """A loose directory acquisition (mbmt_routes) or one harvest member."""
    kind = next((k for k in HARVEST_OF_KIND if sid.startswith(f'mbmt_route_{k}_')), None)
    if kind is None:
        if not Path(city.path('data/raw/transit', 'provenance_' + sid + '.json')).exists():
            return None, None
        record, path = source(sid, 'transit')
        raw = path.read_bytes()
    else:
        if sid not in LISTINGS[kind]:
            return None, None
        which = HARVEST_OF_KIND[kind]
        record, raw = harvest.source(which.id, which.category, sid, LISTINGS[kind])
    data = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(data, list):
        raise ValueError('Expected a passenger information list: ' + sid)
    return record, data


def number(value):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def point(lon, lat):
    lon, lat = number(lon), number(lat)
    if lon is None or lat is None or not -180 <= lon <= 180 or not -90 <= lat <= 90:
        return None
    return (lon, lat) if lon != 0 or lat != 0 else None


def separation(geod, stops, vertices):
    """Nearest sampled vertex distance, not road matching or stop snapping."""
    stops, vertices = [p for p in stops if p], [p for p in vertices if p]
    if not stops or not vertices:
        return None
    lons, lats = zip(*vertices)
    distances = []
    for lon, lat in stops:
        _, _, values = geod.inv([lon] * len(vertices), [lat] * len(vertices), lons, lats)
        distances.append(min(values))
    return dict(stops_compared=len(stops), vertices_compared=len(vertices),
                median_nearest_vertex_distance_m=median(distances),
                maximum_nearest_vertex_distance_m=max(distances))


def main():
    _, routes = read('mbmt_routes')
    if routes is None:
        raise ValueError('Route directory is missing')
    ids = [r['RouteId'] for r in routes]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate directory IDs')
    # The public client renders cumulative distance as km and time as minutes.
    _, page_path = source('mbmt_routes_page', 'transit')
    client = page_path.read_text(encoding='utf-8-sig')
    if 'data[i].totaltime + " min' not in client or 'totalkm.toFixed(2) + " km' not in client:
        raise ValueError('Client unit evidence changed')
    geod = Geod(ellps='WGS84')
    details_out, stops_out, vertices_out, checks = [], [], [], []
    for route in sorted(routes, key=lambda r: r['RouteId']):
        rid = route['RouteId']
        check = dict(route_id=rid, directory_name=route['RouteName'])
        selected = {}
        for kind in ('details', 'stops', 'path'):
            sid = f'mbmt_route_{kind}_{rid}'
            record, values = read(sid)
            selected[kind] = values
            check[kind + '_status'] = 'unobtained' if values is None else 'empty' if not values else 'published'
            check[kind + '_rows'] = None if values is None else len(values)
            if values is None:
                continue
            for seq, value in enumerate(values, start=1):
                common = dict(route_id=rid, response_sequence=seq, source_id=sid,
                              source_sha256=record['sha256'], source='operator_passenger_query', model_ready=False)
                if kind == 'details':
                    details_out.append(dict(**common, station_id_raw=value.get('stationid'),
                                            station_name_raw=value.get('stationname'),
                                            published_cumulative_distance_km=value.get('totaldistance'),
                                            published_cumulative_time_min=value.get('totaltime')))
                elif kind == 'stops':
                    stops_out.append(dict(**common, response_route_id=value.get('RouteId'),
                                          route_name_raw=value.get('RouteName'), station_name_raw=value.get('StationName'),
                                          api_lat1_deg=value.get('Lat1'), api_long1_deg=value.get('Long1'),
                                          direction_raw=value.get('route_type_name')))
                else:
                    vertices_out.append(dict(**common, response_route_id=value.get('RouteId'),
                                             source_serial=value.get('SrNo'), route_name_raw=value.get('RouteName'),
                                             api_latitude_field_deg=value.get('Latitude'),
                                             api_longitude_field_deg=value.get('longitude'), depot_id=value.get('Depotid')))
        details, stops, vertices = (selected[k] for k in ('details', 'stops', 'path'))
        if details:
            distances = [number(r.get('totaldistance')) for r in details]
            times = [number(r.get('totaltime')) for r in details]
            check['nonnumeric_distance_sequences'] = [i for i, v in enumerate(distances, 1) if v is None]
            check['nonnumeric_time_sequences'] = [i for i, v in enumerate(times, 1) if v is None]
            check['distance_decrease_sequences'] = [i for i, (a, b) in enumerate(zip(distances, distances[1:]), 2)
                                                     if a is not None and b is not None and b < a]
            check['time_decrease_sequences'] = [i for i, (a, b) in enumerate(zip(times, times[1:]), 2)
                                                 if a is not None and b is not None and b < a]
            check['all_times_equal_zero_based_stop_index'] = all(value == i for i, value in enumerate(times))
        if details is not None and stops is not None:
            check['equal_detail_stop_counts'] = len(details) == len(stops)
            check['same_position_name_disagreements'] = [i for i, (a, b) in enumerate(zip(details, stops), 1)
                                                        if a.get('stationname') != b.get('StationName')]
        for name, values in (('stops', stops), ('path', vertices)):
            if values is not None:
                check[name + '_wrong_route_sequences'] = [i for i, v in enumerate(values, 1)
                                                         if str(v.get('RouteId')) != str(rid)]
        if stops is not None and vertices is not None:
            stop_points = [point(s.get('Long1'), s.get('Lat1')) for s in stops]
            declared = [point(v.get('longitude'), v.get('Latitude')) for v in vertices]
            swapped = [point(v.get('Latitude'), v.get('longitude')) for v in vertices]
            check['invalid_stop_coordinates'] = sum(p is None for p in stop_points)
            check['invalid_declared_path_coordinates'] = sum(p is None for p in declared)
            check['invalid_swapped_path_coordinates'] = sum(p is None for p in swapped)
            check['as_labelled_axis_comparison'] = a = separation(geod, stop_points, declared)
            check['swapped_axis_comparison'] = b = separation(geod, stop_points, swapped)
            check['closer_axis_interpretation'] = (
                'not_comparable' if a is None or b is None else
                'swapped' if b['median_nearest_vertex_distance_m'] < a['median_nearest_vertex_distance_m'] else
                'as_labelled' if a['median_nearest_vertex_distance_m'] < b['median_nearest_vertex_distance_m'] else 'tie')
        checks.append(check)
    totals = dict(directory_routes=len(routes), detail_rows=len(details_out), stop_rows=len(stops_out),
                  vertices=len(vertices_out),
                  responses={k: dict(Counter(c[k + '_status'] for c in checks)) for k in ('details', 'stops', 'path')},
                  axis_interpretations=dict(Counter(c.get('closer_axis_interpretation', 'not_comparable') for c in checks)),
                  routes_with_times_equal_stop_index=sum(c.get('all_times_equal_zero_based_stop_index', False) for c in checks),
                  detail_stop_count_disagreements=sum(c.get('equal_detail_stop_counts') is False for c in checks),
                  position_name_disagreements=sum(len(c.get('same_position_name_disagreements', [])) for c in checks))
    result = dict(status='passenger_information_not_validated_operating_schedule', summary=totals, routes=checks,
                  limitations=[
                      'Route directory entries need not all operate on the selected date.',
                      'Cumulative fields are not departures, headways, observed running times or service calendars.',
                      'A time equal to every stop index suggests a mechanical sequence; it must not be accepted as observed one-minute running times.',
                      'Stop-detail pairing is audited by position and exact name; it is not silently assumed.',
                      'Both map axis interpretations are compared against published stops using WGS84 ellipsoidal distances.',
                      'The comparison uses nearest sampled vertices, not the nearest point on a line or a legal road network.',
                      'A closer axis interpretation does not validate stop placement, route direction, vertex order or road matching.',
                      'Raw coordinate fields retain their original labels; no swapped coordinates are supplied as validated network geometry.',
                      'No vehicle configuration, fleet allocation or current ridership is inferred from this directory.'])
    for name, rows in [('mbmt_route_details.csv', details_out), ('mbmt_route_stops.csv', stops_out),
                       ('mbmt_route_vertices.csv', vertices_out)]:
        if rows:
            write(name, rows)
    Path(city.path('data/processed/acquisition/mbmt_route_audit.json')).write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(totals))


if __name__ == '__main__':
    main()
