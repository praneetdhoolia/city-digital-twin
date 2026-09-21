"""Trace native aborts and late departures at an iteration that actually ended."""
import argparse
from collections import Counter
import json
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from iteration_reading import events, open_table, table
import results_store
from run_matsim import _iteration_times_from_log


def diagnose(name, iteration):
    run = Path(results_store.resolve_or_die(name))
    if iteration not in _iteration_times_from_log(str(run / 'matsim.log')):
        raise ValueError('The native log does not show this iteration ending')
    base = run / 'output/ITERS' / f'it.{iteration}' / f'{iteration}.events.xml'
    candidates = [Path(str(base) + suffix) for suffix in ('.gz', '.zst', '')]
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        raise FileNotFoundError('Native event file unavailable for completed iteration')
    try:
        people = {r['person']: r for r in table(str(run), 'persons')}
    except FileNotFoundError:
        plans_base = run / 'output/ITERS' / f'it.{iteration}' / f'{iteration}.plans.xml'
        plan_path = next((Path(str(plans_base) + suffix) for suffix in ('.gz', '.zst', '')
                          if Path(str(plans_base) + suffix).is_file()), None)
        if plan_path is None:
            raise FileNotFoundError('Neither final person table nor this iteration plan snapshot is available')
        people = {}
        with open_table(str(plan_path)) as stream:
            for _, person in ET.iterparse(stream, events=('end',)):
                if person.tag == 'person':
                    people[person.get('id')] = {'subpopulation': person.findtext(
                        "attributes/attribute[@name='subpopulation']", default='')}
                    person.clear()
    trips = table(str(run), 'trips', iteration)
    last_trip = {}
    late = []
    for trip in trips:
        identity = trip['person']
        if identity not in last_trip or int(trip['trip_number']) > int(last_trip[identity]['trip_number']):
            last_trip[identity] = trip
        if int(trip['dep_time'].split(':')[0]) >= 24:
            late.append(trip)
    stuck = []
    for _, event in events(path, {'stuckAndAbort'}):
        identity = event.get('person', '')
        person = people.get(identity, {})
        trip = last_trip.get(identity)
        stuck.append(dict(person_id=identity, time_s=float(event['time']),
                          mode=event.get('legMode', ''), link_id=event.get('link', ''),
                          native_reason=event.get('reason', ''),
                          subpopulation=person.get('subpopulation', 'not_in_person_table'),
                          last_recorded_trip=trip))
    report = dict(run=run.name, iteration=iteration, iteration_ended=True,
                  scope='Diagnostic reading at this iteration; not a run completion or calibrated finding.',
                  stuck_event_count=len(stuck), stuck_by_mode=dict(Counter(r['mode'] for r in stuck)),
                  stuck_by_native_reason=dict(Counter(r['native_reason'] for r in stuck)),
                  stuck_by_time_s=dict(Counter(str(r['time_s']) for r in stuck)),
                  departures_after_24h_count=len(late),
                  late_by_destination_activity=dict(Counter(r['end_activity_type'] for r in late)),
                  late_by_main_mode=dict(Counter(r['main_mode'] for r in late)),
                  stuck_events=stuck, late_trips=late,
                  limitations=['Native reason is retained verbatim; an absent reason is not inferred.',
                               'The last trip is table context and may itself be incomplete.',
                               'A departure after midnight is not automatically an invalid journey.'])
    destination = Path(results_store.processed_dir(run.name))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f'_day_schedule_it{iteration}.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('stuck_events', 'late_trips')}, indent=2))
    return report


def trace_vehicle(name, iteration, vehicle):
    run = Path(results_store.resolve_or_die(name))
    if iteration not in _iteration_times_from_log(str(run / 'matsim.log')):
        raise ValueError('The native log does not show this iteration ending')
    base = run / 'output/ITERS' / f'it.{iteration}' / f'{iteration}.events.xml'
    path = next((Path(str(base) + suffix) for suffix in ('.gz', '.zst', '')
                 if Path(str(base) + suffix).is_file()), None)
    if path is None:
        raise FileNotFoundError('No native events for this completed iteration')
    selected = [row for _, row in events(path, attribute_values={'vehicle': {vehicle}})]
    gaps = sorted((dict(duration_s=float(after['time'])-float(before['time']), before=before, after=after)
                   for before, after in zip(selected, selected[1:])),
                  key=lambda row: row['duration_s'], reverse=True)
    report = dict(run=run.name, iteration=iteration, vehicle_id=vehicle,
                  scope='Native events for this vehicle at a completed iteration; gaps are not inferred causes.',
                  event_count=len(selected), events=selected, longest_gaps=gaps[:10])
    destination = Path(results_store.processed_dir(run.name))
    destination.mkdir(parents=True, exist_ok=True)
    token = hashlib.sha256(vehicle.encode('utf-8')).hexdigest()[:16]
    (destination / f'_vehicle_trace_it{iteration}_{token}.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'events'}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--iteration', type=int, required=True)
    parser.add_argument('--vehicle', help='Trace one vehicle instead of the daily abort summary')
    args = parser.parse_args()
    if args.vehicle:
        trace_vehicle(args.run, args.iteration, args.vehicle)
    else:
        diagnose(args.run, args.iteration)
