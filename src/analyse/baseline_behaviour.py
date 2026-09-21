"""Summarise an executed development case without claiming calibration."""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
import math
import re
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

from iteration_reading import open_table, table
import results_store


def retained_plan_scores(path, people):
    """Count finite native scores, without treating stored plans as convergence."""
    groups = {}
    seen = set()
    with open_table(str(path)) as stream:
        for _, person in ET.iterparse(stream, events=('end',)):
            if person.tag != 'person':
                continue
            identity = person.get('id')
            if identity not in people or identity in seen:
                raise ValueError(f'Unexpected or duplicate output person: {identity}')
            seen.add(identity)
            group = people[identity].get('subpopulation', '')
            values = groups.setdefault(group, dict(persons_count=0,
                persons_with_unscored_plans_count=0, unscored_plans_count=0,
                selected_unscored_plans_count=0, plans_per_person=Counter(), scores=[]))
            plans = person.findall('plan')
            if sum(p.get('selected') == 'yes' for p in plans) != 1:
                raise ValueError(f'Expected one selected output plan: {identity}')
            unscored = 0
            for plan in plans:
                score = float(plan.get('score', 'nan'))
                if math.isfinite(score):
                    values['scores'].append(score)
                else:
                    unscored += 1
                    values['selected_unscored_plans_count'] += plan.get('selected') == 'yes'
            values['persons_count'] += 1
            values['persons_with_unscored_plans_count'] += unscored > 0
            values['unscored_plans_count'] += unscored
            values['plans_per_person'][len(plans)] += 1
            person.clear()
    if seen != set(people):
        raise ValueError('Output plans and person table contain different populations')
    for values in groups.values():
        scores = values.pop('scores')
        values['finite_stored_scores'] = dict(count=len(scores),
            minimum=min(scores) if scores else None,
            median=statistics.median(scores) if scores else None,
            maximum=max(scores) if scores else None)
        values['plans_per_person'] = dict(sorted(values['plans_per_person'].items()))
    return groups


def analyse(name, summary=False):
    run = Path(results_store.resolve_or_die(name))
    record = json.loads((run / '_run.json').read_text(encoding='utf-8'))
    if record.get('completion') != 'ran_to_last_iteration':
        raise ValueError('Behavioural completion report requires a finished run')
    # the run's own schedule: the harness writes it to output/ (9.169), the
    # retired city launcher copied it beside the record
    schedule_path = run / 'output' / 'output_transitSchedule.xml.gz'
    if not schedule_path.is_file():
        schedule_path = run / 'transitSchedule.xml.gz'
    with gzip.open(schedule_path) as stream:
        schedule = ET.parse(stream).getroot()
    modes = {(line.get('id'), route.get('id')): route.findtext('transportMode')
             for line in schedule.findall('transitLine')
             for route in line.findall('transitRoute')}
    telemetry = {r['iteration']: r for r in map(json.loads,
        (run / 'output/telemetry.jsonl').read_text(encoding='utf-8').splitlines())}
    readings = []
    people = {r['person']: r for r in table(str(run), 'persons')}
    first_choices = None
    first_trip_modes = defaultdict(set)
    for iteration in range(record['reached_iteration'] + 1):
        trips = table(str(run), 'trips', iteration)
        legs = table(str(run), 'legs', iteration)
        choices = {r['trip_id']: r['main_mode'] for r in trips}
        by_subpopulation = {}
        by_activity = {}
        departures_after_midnight = Counter()
        for trip in trips:
            group = people[trip['person']].get('subpopulation', '')
            if trip['trip_number'] == '1':
                first_trip_modes[trip['person']].add(trip['main_mode'])
            by_subpopulation.setdefault(group, Counter())[trip['main_mode']] += 1
            by_activity.setdefault(trip['end_activity_type'], Counter())[trip['main_mode']] += 1
            if int(trip['dep_time'].split(':')[0]) >= 24:
                departures_after_midnight[group] += 1
        if first_choices is None:
            first_choices = choices
        boardings = Counter({mode: 0 for mode in sorted(set(modes.values()))})
        by_line = Counter()
        for leg in legs:
            if leg.get('transit_route'):
                boardings[modes[(leg['transit_line'], leg['transit_route'])]] += 1
                by_line[leg['transit_line']] += 1
        tel = telemetry[iteration]
        readings.append(dict(iteration=iteration,
            recorded_trips=len(trips), trip_modes=dict(Counter(choices.values())),
            trip_modes_by_subpopulation={k: dict(v) for k, v in by_subpopulation.items()},
            trip_modes_by_destination_activity={k: dict(v) for k, v in sorted(by_activity.items())},
            recorded_trip_departures_after_24h=dict(departures_after_midnight),
            transit_ride_legs=dict(boardings),
            transit_ride_legs_by_line=dict(sorted(by_line.items())),
            changed_trip_modes_from_iteration_zero=sum(
                mode != first_choices.get(key) for key, mode in choices.items()
                if key in first_choices),
            non_network_access_legs=sum(r['mode'] == 'non_network_walk' for r in legs),
            network_departures_by_mode=tel['departures'],
            network_arrivals_by_mode=tel['arrivals'],
            stuck_events_by_departure_mode=tel['stuck'],
            note='Trip/leg tables include journeys with execution problems. Transit drivers appear as car in raw telemetry; these are not resident car counts.'))
    coverage = {}
    for group in sorted({p.get('subpopulation', '') for p in people.values()}):
        members = {identity: person for identity, person in people.items() if person.get('subpopulation', '') == group}
        seen = {identity: first_trip_modes[identity] for identity in members if identity in first_trip_modes}
        joint = Counter((len(set(members[identity].get('permittedModes', '').split(',')) - {''}), len(values))
                        for identity, values in seen.items())
        coverage[group] = dict(persons_with_recorded_first_trip_count=len(seen),
            persons_without_recorded_first_trip_count=len(members) - len(seen),
            persons_by_distinct_first_trip_modes=dict(sorted(Counter(len(v) for v in seen.values()).items())),
            eligibility_vs_tried=[dict(eligible_modes_count=eligible, tried_modes_count=tried, persons_count=count)
                                  for (eligible, tried), count in sorted(joint.items())])
    report = dict(run=run.name, city=record.get('city'), completion=record['completion'],
        reached_iteration=record['reached_iteration'], calibrated=False,
        population_basis=record.get('population_basis'),
        persons_by_subpopulation=dict(Counter(r.get('subpopulation', '') for r in people.values())),
        scheduled_route_patterns=dict(Counter(modes.values())),
        iterations=readings,
        first_trip_choice_coverage=coverage,
        limitations=['Small explicit population with no citywide expansion.',
                     'First-trip coverage is across recorded trips; absent trips include stay-home plans and failures. It does not prove utility convergence.',
                     'Initial exploration and short learning horizon; mode shares are not forecasts.',
                     'Supply, joint demographics, capacity and money/time trade-offs remain provisional.'])
    destination = Path(results_store.processed_dir(run.name))
    fleet_input = run / '_hired_fleet_input.json'
    if fleet_input.exists():
        report['hired_fleet_input'] = json.loads(fleet_input.read_text(encoding='utf-8'))
        pattern = re.compile(r'hiredFleet: mode=(\S+) vehicles=(\d+) requested=(\d+) dispatched=(\d+) '
                             r'timedOut=(\d+) queuedAtEnd=(\d+) activeAtEnd=(\d+) servedWaitSeconds=([\d.Ee+-]+)')
        fleet_readings = defaultdict(list)
        with (run / 'matsim.log').open(encoding='utf-8', errors='replace') as stream:
            for line in stream:
                match = pattern.search(line)
                if match:
                    mode, *values = match.groups()
                    fleet_readings[mode].append(dict(zip(
                        ('vehicles_count', 'requested_count', 'dispatched_count', 'timed_out_count',
                         'queued_at_end_count', 'active_at_end_count', 'served_wait_seconds'),
                        [*map(int, values[:-1]), float(values[-1])]), iteration=len(fleet_readings[mode])))
        expected_modes = set(report['hired_fleet_input']['vehicles_by_mode'])
        if set(fleet_readings) != expected_modes or any(len(v) != record['reached_iteration'] + 1 for v in fleet_readings.values()):
            raise ValueError('Missing or duplicated hired-fleet iteration readings')
        for mode, rows in fleet_readings.items():
            for row in rows:
                if row['vehicles_count'] != report['hired_fleet_input']['vehicles_by_mode'][mode]:
                    raise ValueError('Native hired fleet differs from its input audit')
                if row['requested_count'] != row['dispatched_count'] + row['timed_out_count'] + row['queued_at_end_count']:
                    raise ValueError('Hired-fleet request accounting does not balance')
                if row['active_at_end_count'] > row['dispatched_count']:
                    raise ValueError('Unfinished hired legs exceed dispatched legs')
                row['completed_network_legs_count'] = row['dispatched_count'] - row['active_at_end_count']
                row['mean_served_wait_seconds'] = (row['served_wait_seconds'] / row['dispatched_count']
                                                   if row['dispatched_count'] else None)
        report['hired_fleet_iterations'] = dict(fleet_readings)
        report['limitations'].append('Hired supply is a mode-specific pool with experienced waiting; spatial dispatch, service shifts and empty road movements remain unmodelled. Timeouts abort the day.')
    plan_files = [run / ('output/output_plans.xml' + suffix) for suffix in ('.gz', '.zst', '')]
    plan_path = next((p for p in plan_files if p.exists()), None)
    if plan_path is not None:
        report['retained_plan_scores'] = retained_plan_scores(plan_path, people)
        report['limitations'].append('Finite retained-plan scores describe stored evaluations, potentially from different iterations; they are not a convergence or welfare comparison.')
    else:
        report['limitations'].append('Final retained-plan output is unavailable; unscored alternatives cannot be counted.')
    demand_audit = run / '_baseline_demand.json'
    if demand_audit.exists():
        report['input_demand'] = json.loads(demand_audit.read_text(encoding='utf-8'))
    fare_audit = run / 'output/boarding_fares.csv'
    if fare_audit.exists():
        with fare_audit.open(encoding='utf-8', newline='') as stream:
            report['boarding_fares'] = [
                {key: (int(value) if key == 'iteration' or key.endswith('_count')
                       else float(value) if key in ('travelled_distance_m', 'charged_money')
                       else value) for key, value in row.items()}
                for row in csv.DictReader(stream)]
        config = ET.parse(run / 'config.xml').getroot()
        route_choice = config.find("./module[@name='boardingFare']/param[@name='routeChoice']")
        report['boarding_fares_in_route_choice'] = (
            route_choice is not None and route_choice.get('value', '').lower() == 'true')
        if report['boarding_fares_in_route_choice']:
            report['limitations'].append('Declared boarding tariffs enter routing and scoring; tariff coverage, eligibility and transfer products remain provisional.')
        else:
            report['limitations'].append('Boarding fares enter scoring; exact operator ticket prices are not yet optimised by the transit path router.')
    destination.mkdir(parents=True, exist_ok=True)
    (destination / '_baseline_behaviour.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if summary:
        print(json.dumps(dict(run=run.name, completion=record['completion'], reached_iteration=record['reached_iteration'],
            final_trip_modes=readings[-1]['trip_modes'],
            final_mode_labelled_stuck=readings[-1]['stuck_events_by_departure_mode'],
            first_trip_choice_coverage=coverage), indent=2))
    else:
        print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--summary', action='store_true', help='Print compact results; retain the full permanent report')
    args = parser.parse_args()
    analyse(args.run, summary=args.summary)
