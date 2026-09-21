"""Extract public route stop snapshots, retaining identity and distance semantics."""
from collections import Counter
import json
import math
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point
import city
import harvest
from acquire_nmmt_paths import ALIGNMENTS
from extract_census_controls import write

OUTPUT_INPUTS = {
    'data/processed/observed/nmmt_route_stop_snapshots.csv': ['data/raw/transit/nmmt_route_stop_snapshot_*.zip', 'data/raw/transit/nmmt_route_alignments.zip'],
    'data/processed/observed/nmmt_vehicle_indications.csv': ['data/raw/transit/nmmt_route_stop_snapshot_*.zip'],
    'data/processed/acquisition/nmmt_route_stop_audit.json': ['data/raw/transit/nmmt_route_stop_snapshot_*.zip', 'data/raw/transit/nmmt_route_alignments.zip'],
}


def valid_coordinate(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180 and (lat, lon) != (0, 0)


def main():
    rows, checks, vehicle_rows = [], [], []
    vehicle_keys = Counter()
    descriptor = json.loads(Path(city.path('city.json')).read_text(encoding='utf-8'))
    projection = Transformer.from_crs('EPSG:4326', descriptor['crs']['epsg'], always_xy=True)
    geometries = {}
    alignments = harvest.members(ALIGNMENTS.id, ALIGNMENTS.category)

    def geometry(route_id):
        if route_id not in geometries:
            source_id = 'nmmt_route_path_'+str(route_id)
            line, digest = None, None
            if source_id in alignments:
                record, data = harvest.source(ALIGNMENTS.id, ALIGNMENTS.category, source_id, alignments)
                payload = json.loads(data.decode('utf-8-sig'))
                points = payload.get('Data')
                if (payload.get('IsSuccess') is True and isinstance(points, list) and len(points) >= 2
                        and all(valid_coordinate(p.get('routelat'), p.get('routelong')) for p in points)):
                    line = LineString([projection.transform(float(p['routelong']), float(p['routelat'])) for p in points])
                    digest = record['sha256']
            geometries[route_id] = line, digest
        return geometries[route_id]
    snapshots = [(hid, harvest.members(hid, 'transit')) for hid in harvest.harvests('transit', 'nmmt_route_stop_snapshot_')]
    for source_id, harvest_id, listing in sorted((mid, hid, listing) for hid, listing in snapshots for mid in listing):
        record, data = harvest.source(harvest_id, 'transit', source_id, listing)
        payload = json.loads(data.decode('utf-8-sig'))
        query_route = record['request_json']['routeid']
        check = dict(source_id=source_id, queried_route_id=query_route, retrieved=record['retrieved'],
                     source_sha256=record['sha256'], success=payload.get('issuccess'), directions={})
        for direction in ('up', 'down'):
            stops = payload.get(direction, {}).get('data')
            if not isinstance(stops, list):
                check['directions'][direction] = dict(status='invalid_structure')
                continue
            invalid, vehicles, decreasing = [], 0, []
            previous_distance = None
            for sequence, stop in enumerate(stops, start=1):
                valid = valid_coordinate(stop.get('centerlat'), stop.get('centerlong'))
                if not valid:
                    invalid.append(sequence)
                indications = stop.get('vehicleDetails', [])
                if not isinstance(indications, list):
                    raise ValueError('Unexpected vehicle indication structure: '+source_id)
                vehicles += len(indications)
                for indication in indications:
                    vehicle_keys.update(indication.keys())
                    vehicle_rows.append(dict(
                        source_id=source_id, queried_route_id=query_route,
                        returned_route_id=stop.get('routeid'), direction=direction,
                        station_id=stop.get('stationid'), response_stop_sequence=sequence,
                        vehicle_id=indication.get('vehicleid'), tracking_trip_id=indication.get('tripid'),
                        service_type_id=indication.get('servicetypeid'),
                        reported_latitude_deg=indication.get('centerlat'),
                        reported_longitude_deg=indication.get('centerlong'),
                        refresh_time_raw=indication.get('lastrefreshon'),
                        refresh_flag_raw=indication.get('lastreceiveddatetimeflag'),
                        scheduled_arrival_raw=indication.get('sch_arrivaltime'),
                        scheduled_departure_raw=indication.get('sch_departuretime'),
                        actual_arrival_raw=indication.get('actual_arrivaltime'),
                        actual_departure_raw=indication.get('actual_departuretime'),
                        scheduled_trip_start_raw=indication.get('sch_tripstarttime'),
                        scheduled_trip_end_raw=indication.get('sch_tripendtime'),
                        eta_raw=indication.get('eta'), stop_covered_status_raw=indication.get('stopCoveredStatus'),
                        current_location_id=indication.get('currentlocationid'),
                        next_location_id=indication.get('nextlocationid'),
                        retrieved_utc=record['retrieved'], source='operator_reported_vehicle_indication',
                        source_sha256=record['sha256']))
                distance = stop.get('cumulative_km')
                if isinstance(distance, (int, float)):
                    if previous_distance is not None and distance < previous_distance:
                        decreasing.append(sequence)
                    previous_distance = distance
                line, geometry_hash = geometry(stop.get('routeid'))
                point = Point(projection.transform(float(stop['centerlong']), float(stop['centerlat']))) if valid else None
                offset = point.distance(line) if point is not None and line is not None else None
                along = line.project(point) if point is not None and line is not None else None
                rows.append(dict(source_id=source_id, queried_route_id=query_route, direction=direction,
                                 response_sequence=sequence, returned_route_id=stop.get('routeid'),
                                 station_id=stop.get('stationid'), station_name=stop.get('stationname'),
                                 route_number=stop.get('routeno'), latitude_deg=stop.get('centerlat'),
                                 longitude_deg=stop.get('centerlong'), coordinate_valid=valid,
                                 distance_on_station_raw=stop.get('distance_on_station'),
                                 distance_between_stops_raw=stop.get('distance_between_stops'),
                                 cumulative_distance_km=distance, vehicle_indications_count=len(indications),
                                 stop_to_published_geometry_m=offset, projected_along_geometry_m=along,
                                 geometry_source_sha256=geometry_hash, projected_epsg=descriptor['crs']['epsg'],
                                 retrieved=record['retrieved'], source='operator_passenger_snapshot',
                                 source_sha256=record['sha256']))
            check['directions'][direction] = dict(status='published_stops' if stops else 'empty',
                                                 stops=len(stops), invalid_coordinate_sequences=invalid,
                                                 decreasing_cumulative_distance_sequences=decreasing,
                                                 vehicle_indications_count=vehicles)
        checks.append(check)
    if rows:
        write('nmmt_route_stop_snapshots.csv', rows)
    if vehicle_rows:
        write('nmmt_vehicle_indications.csv', vehicle_rows)
    summary = dict(acquired_queries=len(checks), stop_rows=len(rows),
                   unsuccessful_application_responses=sum(c['success'] is not True for c in checks),
                   queries_with_both_directions_empty=sum(all(d.get('status') == 'empty' for d in c['directions'].values()) for c in checks),
                   invalid_coordinates=sum(not r['coordinate_valid'] for r in rows),
                   vehicle_indications=sum(r['vehicle_indications_count'] for r in rows),
                   distinct_indicated_vehicle_ids=len({r['vehicle_id'] for r in vehicle_rows}),
                   distinct_indicated_vehicle_trip_pairs=len({(r['vehicle_id'],r['tracking_trip_id']) for r in vehicle_rows}),
                   stops_with_geometry=sum(r['stop_to_published_geometry_m'] is not None for r in rows),
                   maximum_stop_offset_m=max((r['stop_to_published_geometry_m'] for r in rows if r['stop_to_published_geometry_m'] is not None), default=None))
    audit = dict(schema_version=1, summary=summary, queries=checks, vehicle_field_occurrences=dict(vehicle_keys),
                 limits='Source response order retained. Up/down may refer to paired route identities; queried and returned IDs remain separate. Repeated vehicle indications are not unique vehicles or ridership. Observation timestamp freshness is unvalidated. Distance units are retained only where explicit in the source field name; raw fields require confirmation. Stop offsets use the declared projected CRS and nearest published polyline point, which is ambiguous on loops and is not road/platform matching. No service calendar or inferred timetable corrections.')
    target = Path(city.path('data/processed/acquisition/nmmt_route_stop_audit.json'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
