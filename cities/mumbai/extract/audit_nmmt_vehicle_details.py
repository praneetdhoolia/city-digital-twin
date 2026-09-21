"""Retain operator-reported trip times without mistaking skipped stops for observations."""
from collections import Counter
import json
from pathlib import Path

import city
import harvest
from extract_census_controls import write

OUTPUT_INPUTS = {
    'data/processed/observed/nmmt_vehicle_stop_details.csv': ['data/raw/transit/nmmt_vehicle_snapshot_*.zip'],
    'data/processed/observed/nmmt_vehicle_locations.csv': ['data/raw/transit/nmmt_vehicle_snapshot_*.zip'],
    'data/processed/acquisition/nmmt_vehicle_detail_audit.json': [
        'data/raw/transit/nmmt_vehicle_snapshot_*.zip', 'data/raw/transit/nmmt_bus_tracking_component_*.js'],
}


def main():
    rows, locations, checks = [], [], []
    statuses = Counter()
    snapshots = [(hid, harvest.members(hid, 'transit')) for hid in harvest.harvests('transit', 'nmmt_vehicle_snapshot_')]
    for source_id, harvest_id, listing in sorted((mid, hid, listing) for hid, listing in snapshots for mid in listing):
        record, data = harvest.source(harvest_id, 'transit', source_id, listing)
        payload = json.loads(data.decode('utf-8-sig'))
        stops, live = payload.get('RouteDetails'), payload.get('LiveLocation')
        if not isinstance(stops, list) or not isinstance(live, list):
            raise ValueError('Unexpected vehicle response structure: '+source_id)
        check = dict(source_id=source_id, success=payload.get('Issuccess'), stop_rows=len(stops),
                     location_rows=len(live), declared_row_count=payload.get('RowCount'),
                     count_agrees=payload.get('RowCount') == len(stops)+len(live))
        checks.append(check)
        for sequence, stop in enumerate(stops, start=1):
            status = str(stop.get('stopstatus') or '').lower()
            statuses[status] += 1
            arrival, departure = stop.get('actual_arrivaltime2'), stop.get('actual_departudetime')
            rows.append(dict(source_id=source_id, queried_vehicle_id=record['request_json']['vehicleId'],
                             returned_vehicle_id=stop.get('vehicleid'), tracking_trip_id=stop.get('tripid'),
                             route_id=stop.get('routeid'), station_id=stop.get('stationid'),
                             response_sequence=sequence, published_sequence=stop.get('srno'),
                             trip_status_raw=stop.get('tripstatus'), stop_status_raw=stop.get('stopstatus'),
                             scheduled_arrival_raw=stop.get('sch_arrivaltime'), scheduled_departure_raw=stop.get('sch_departuretime'),
                             scheduled_arrival_datetime_raw=stop.get('scharrivaltime'),
                             actual_arrival_field_raw=arrival, actual_departure_field_raw=departure,
                             covered_with_both_actual_fields=(status == 'covered' and bool(arrival) and bool(departure)),
                             actual_arrival_equals_schedule=bool(arrival) and arrival == stop.get('sch_arrivaltime'),
                             reported_trip_start_raw=stop.get('tripstarttime'), reported_trip_end_raw=stop.get('tripendtime'),
                             last_updated_raw=stop.get('lastupdatedat'), refresh_flag_raw=stop.get('lastreceiveddatetimeflag'),
                             source='operator_reported_trip_stop', retrieved_utc=record['retrieved'], source_sha256=record['sha256']))
        for location in live:
            locations.append(dict(source_id=source_id, vehicle_id=location.get('vehicleid'),
                                  reported_latitude_deg=location.get('latitude'), reported_longitude_deg=location.get('longitude'),
                                  last_refresh_raw=location.get('lastrefreshon'), refresh_flag_raw=location.get('lastreceiveddatetimeflag'),
                                  speed_raw=location.get('speed'), fuel_type_raw=location.get('fueltype'),
                                  source='operator_reported_vehicle_location', retrieved_utc=record['retrieved'], source_sha256=record['sha256']))
    if rows:
        write('nmmt_vehicle_stop_details.csv', rows)
    if locations:
        write('nmmt_vehicle_locations.csv', locations)
    summary = dict(acquired_queries=len(checks), stop_rows=len(rows), location_rows=len(locations),
                   stop_status_counts=dict(statuses), count_disagreements=sum(not c['count_agrees'] for c in checks),
                   covered_with_both_actual_fields=sum(r['covered_with_both_actual_fields'] for r in rows),
                   skipped_with_actual_equal_scheduled=sum(str(r['stop_status_raw']).lower() == 'skipped' and r['actual_arrival_equals_schedule'] for r in rows))
    audit = dict(schema_version=1, summary=summary, queries=checks,
                 client_semantics='Public client displays actual_arrivaltime2 and actual_departudetime as arrival/departure only when stopstatus is covered. Other statuses cannot be treated as observed stops merely because an actual-named field is populated.',
                 limits='Clock timezone and device freshness remain unverified. Tracking trip IDs have not been joined to timetable trip IDs. Reported covered times are not independent ground truth. One sequential snapshot is not a dwell/running-time distribution, operating calendar, complete fleet or ridership count.')
    Path(city.path('data/processed/acquisition/nmmt_vehicle_detail_audit.json')).write_text(json.dumps(audit, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
