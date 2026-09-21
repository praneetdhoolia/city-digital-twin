"""Extract published map vertices and audit route coverage without map matching."""
from collections import Counter
import json
import math
from pathlib import Path

from pyproj import Geod
import city
import harvest
from acquire_nmmt_schedules import read
from acquire_nmmt_paths import ALIGNMENTS
from extract_census_controls import write

OUTPUT_INPUTS = {
    'data/processed/observed/nmmt_route_vertices.csv': ['data/raw/transit/nmmt_route_alignments.zip'],
    'data/processed/acquisition/nmmt_path_audit.json': [
        'data/raw/transit/nmmt_route_alignments.zip', 'data/raw/transit/nmmt_current_routes_*.json'],
}


def main():
    routes = read('nmmt_current_routes')
    alignments = harvest.members(ALIGNMENTS.id, ALIGNMENTS.category)
    geod = Geod(ellps='WGS84')
    rows, checks = [], []
    for route in sorted(routes, key=lambda r: int(r['strRouteId'])):
        route_id = int(route['strRouteId'])
        source_id = 'nmmt_route_path_'+str(route_id)
        if source_id not in alignments:
            checks.append(dict(route_id=route_id, status='unobtained'))
            continue
        record, data = harvest.source(ALIGNMENTS.id, ALIGNMENTS.category, source_id, alignments)
        payload = json.loads(data.decode('utf-8-sig'))
        points = payload.get('Data')
        if (payload.get('IsSuccess') is not True or not isinstance(points, list)
                or payload.get('RowCount') != len(points)):
            checks.append(dict(route_id=route_id, status='invalid_response', source_sha256=record['sha256']))
            continue
        coordinates, invalid, wrong_route, identifiers = [], [], [], []
        for sequence, point in enumerate(points, start=1):
            try:
                lat, lon = float(point['routelat']), float(point['routelong'])
            except (KeyError, TypeError, ValueError):
                lat, lon = math.nan, math.nan
            valid = math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180
            if not valid or (lat == 0 and lon == 0):
                invalid.append(sequence)
            if str(point.get('routeid')) != str(route_id):
                wrong_route.append(sequence)
            identifiers.append(str(point.get('routepathmapid')))
            coordinates.append((lon, lat) if valid else None)
            rows.append(dict(route_id=route_id, response_sequence=sequence,
                             route_path_map_id=point.get('routepathmapid'),
                             latitude_deg=point.get('routelat'), longitude_deg=point.get('routelong'),
                             coordinate_status='invalid_or_null_island' if sequence in invalid else 'valid_range',
                             source='operator_published_map', source_id=source_id, source_sha256=record['sha256']))
        distances = [geod.inv(*a, *b)[2] for a, b in zip(coordinates, coordinates[1:]) if a is not None and b is not None]
        checks.append(dict(route_id=route_id, status='published_geometry' if points else 'empty_geometry',
                           vertices=len(points), invalid_vertex_sequences=invalid,
                           wrong_route_sequences=wrong_route,
                           repeated_map_ids=[k for k, n in Counter(identifiers).items() if n > 1],
                           repeated_adjacent_coordinates=sum(a == b for a, b in zip(coordinates, coordinates[1:])),
                           geodesic_polyline_length_m=sum(distances),
                           maximum_adjacent_vertex_distance_m=max(distances, default=None),
                           source_sha256=record['sha256']))
    if rows:
        write('nmmt_route_vertices.csv', rows)
    totals = dict(directory_routes=len(routes), vertices=len(rows), statuses=dict(Counter(r['status'] for r in checks)),
                  invalid_vertices=sum(len(r.get('invalid_vertex_sequences', [])) for r in checks),
                  wrong_route_vertices=sum(len(r.get('wrong_route_sequences', [])) for r in checks))
    audit = dict(schema_version=1, summary=totals, routes=checks,
                 ordering='Public map client preserves the response array order; extraction does the same.',
                 limits='Published alignment only. No road or stop matching, route direction validation, operating calendar, fleet capacity or actual service proof. Distances are WGS84 ellipsoidal polyline sums, not operator route kilometre observations.')
    target = Path(city.path('data/processed/acquisition/nmmt_path_audit.json'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(totals))


if __name__ == '__main__':
    main()
