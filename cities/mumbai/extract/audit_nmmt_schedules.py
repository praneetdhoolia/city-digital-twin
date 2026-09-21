"""Audit acquired NMMT departures and stop timetables, retaining all gaps."""
from collections import defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path

import city
import harvest
from acquire_nmmt_schedules import read, read_member, SCHEDULES, TRIPS

OUTPUT_INPUTS = {
    'data/processed/observed/nmmt_departures.csv': [
        'data/raw/transit/nmmt_current_routes_*.json', 'data/raw/transit/nmmt_route_schedules.zip'],
    'data/processed/observed/nmmt_stop_times.csv': [
        'data/raw/transit/nmmt_current_routes_*.json', 'data/raw/transit/nmmt_current_stops_*.json',
        'data/raw/transit/nmmt_route_schedules.zip', 'data/raw/transit/nmmt_trip_timetables.zip'],
    'data/processed/acquisition/nmmt_schedule_audit.json': [
        'data/raw/transit/nmmt_current_routes_*.json', 'data/raw/transit/nmmt_current_stops_*.json',
        'data/raw/transit/nmmt_route_schedules.zip', 'data/raw/transit/nmmt_trip_timetables.zip'],
}


def clock_seconds(value):
    try:
        parsed = datetime.strptime(value.strip(), '%I:%M %p')
    except (ValueError, AttributeError):
        return None
    return parsed.hour*3600+parsed.minute*60


def write(name, rows, fields):
    path=Path(city.path('data/processed/observed',name))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def main():
    if Path(city.path()).resolve()!=Path(__file__).resolve().parents[1]:
        raise ValueError('CITYSIM_CITY must select the city that owns this script')
    routes=read('nmmt_current_routes')
    stations=read('nmmt_current_stops')
    schedules=harvest.members(SCHEDULES.id, SCHEDULES.category)
    trip_details=harvest.members(TRIPS.id, TRIPS.category) if TRIPS.provenance.exists() else {}
    names=defaultdict(set)
    for station in stations:
        for field in ('displaysationname','sationname'):
            if station.get(field):
                names[station[field].strip()].add(str(station['stationid']))
    departures,stop_times=[],[]
    missing_routes,missing_trips,empty_routes,conflicts=[],[],[],[]
    seen=set()
    for route in sorted(routes,key=lambda row:int(row['strRouteId'])):
        route_id=route['strRouteId'];source_id='nmmt_schedule_'+route_id
        if source_id not in schedules:
            missing_routes.append(route_id);continue
        trips=read_member(SCHEDULES,source_id,schedules)
        if not trips:
            empty_routes.append(route_id)
        for trip in trips:
            trip_id=int(trip['intTripId']);identity=(route_id,trip_id)
            if identity in seen:
                raise ValueError('Duplicate route/trip identity: '+repr(identity))
            seen.add(identity)
            if str(trip['strRouteId'])!=route_id:
                raise ValueError('Trip belongs to another route')
            start=clock_seconds(trip['strScheduelTime'])
            departures.append(dict(route_id=route_id,trip_id=trip_id,route_number=trip['strRouteNo'],
                                   from_station_id=trip['strFromStationId'],to_station_id=trip['strToStationId'],
                                   published_departure_time=trip['strScheduelTime'],departure_clock_s=start,
                                   calendar_status='unresolved',source='observed',source_id=source_id))
            if start is None:
                conflicts.append(dict(route_id=route_id,trip_id=trip_id,issue='unparseable departure time'))
            detail_id=f'nmmt_trip_{route_id}_{trip_id}'
            if detail_id not in trip_details:
                missing_trips.append(detail_id);continue
            matching=[row for row in read_member(TRIPS,detail_id,trip_details) if str(row['strRouteId'])==route_id and int(row['intTripId'])==trip_id]
            if len(matching)!=1:
                conflicts.append(dict(route_id=route_id,trip_id=trip_id,issue='trip detail has no unique matching record'));continue
            stops=matching[0].get('lstSheduelStation')
            if not stops:
                conflicts.append(dict(route_id=route_id,trip_id=trip_id,issue='no stop sequence'));continue
            previous=None
            for sequence,stop in enumerate(stops,start=1):
                label=stop['strStationName'].strip();candidates=sorted(names[label],key=int)
                seconds=clock_seconds(stop.get('strStationScheduelTime'))
                if seconds is None:
                    conflicts.append(dict(route_id=route_id,trip_id=trip_id,sequence=sequence,issue='unparseable stop time'))
                if previous is not None and seconds is not None and seconds<previous:
                    conflicts.append(dict(route_id=route_id,trip_id=trip_id,sequence=sequence,issue='clock reverses; midnight or source error unresolved'))
                if sequence==1 and seconds!=start:
                    conflicts.append(dict(route_id=route_id,trip_id=trip_id,issue='first stop and published departure differ'))
                previous=seconds
                stop_times.append(dict(route_id=route_id,trip_id=trip_id,stop_sequence=sequence,
                                       published_stop_name=label,published_stop_time=stop.get('strStationScheduelTime'),
                                       stop_clock_s=seconds,station_id=candidates[0] if len(candidates)==1 else None,
                                       candidate_station_ids='|'.join(candidates),
                                       station_match_status='unique_exact_name' if len(candidates)==1 else 'ambiguous' if candidates else 'unmatched',
                                       calendar_status='unresolved',source='observed',source_id=detail_id))
    write('nmmt_departures.csv',departures,['route_id','trip_id','route_number','from_station_id','to_station_id',
          'published_departure_time','departure_clock_s','calendar_status','source','source_id'])
    write('nmmt_stop_times.csv',stop_times,['route_id','trip_id','stop_sequence','published_stop_name',
          'published_stop_time','stop_clock_s','station_id','candidate_station_ids','station_match_status',
          'calendar_status','source','source_id'])
    audit=dict(schema_version=1,source='derived',status='evidence_only',listed_routes=len(routes),
               acquired_route_responses=len(routes)-len(missing_routes),published_trips=len(departures),
               acquired_stop_time_rows=len(stop_times),missing_route_ids=missing_routes,missing_trip_source_ids=missing_trips,
               routes_with_empty_timetable=empty_routes,conflicts=conflicts,
               unmatched_stop_rows=sum(row['station_match_status']=='unmatched' for row in stop_times),
               ambiguous_stop_rows=sum(row['station_match_status']=='ambiguous' for row in stop_times),
               acquisition_complete=not missing_routes and not missing_trips,
               limitations=['Neither endpoint supplies an effective service calendar. No seven-day calendar is assumed.',
                            'Published times are timetable information, not measured arrival or departure observations.',
                            'Exact name matches are candidate stop identities, not verified platform or road-link assignments.',
                            'Midnight wrap, short turns, depot movements and active service require further checks.',
                            'Empty schedules do not establish that a route has no passenger demand.'])
    Path(city.path('data/processed/acquisition/nmmt_schedule_audit.json')).write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:audit[key] for key in ['listed_routes','acquired_route_responses','published_trips',
                      'acquired_stop_time_rows','acquisition_complete','unmatched_stop_rows','ambiguous_stop_rows']}))


if __name__=='__main__':
    main()
