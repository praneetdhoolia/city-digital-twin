"""Rank native transit link traversal times without inferring a congestion cause."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from iteration_reading import events, open_table
import results_store
from run_matsim import _iteration_times_from_log


def analyse(name, iteration, top):
    run = Path(results_store.resolve_or_die(name))
    if iteration not in _iteration_times_from_log(str(run / 'matsim.log')):
        raise ValueError('Iteration has no native ENDS marker')
    fleet_path = next((run / 'output').glob('output_allVehicles.xml*'))
    with open_table(str(fleet_path)) as stream:
        fleet = ET.parse(stream)
    modes = {v.get('id'): v.find('{*}networkMode').get('networkMode')
             for v in fleet.findall('{*}vehicleType')}
    vehicles = {v.get('id'): modes[v.get('type')] for v in fleet.findall('{*}vehicle')}
    with gzip.open(run / 'transitSchedule.xml.gz', 'rb') as stream:
        transit = {v.get('vehicleRefId') for _, v in ET.iterparse(stream, events=('end',))
                   if v.tag == 'departure'}
    with gzip.open(run / 'network.xml.gz', 'rb') as stream:
        links = {}
        for _, link in ET.iterparse(stream, events=('end',)):
            if link.tag == 'link':
                links[link.get('id')] = {k: float(link.get(k)) for k in ('length', 'freespeed', 'capacity', 'permlanes')}
                link.clear()
    path = next((run / 'output/ITERS' / f'it.{iteration}').glob(f'{iteration}.events.xml*'))
    active, stats, unmatched = {}, {}, Counter()
    for kind, event in events(path, {'entered link', 'left link', 'vehicle enters traffic', 'vehicle leaves traffic'}):
        vehicle = event.get('vehicle', '')
        if vehicle not in transit:
            continue
        mode, link, time = vehicles[vehicle], event['link'], float(event['time'])
        if kind in ('entered link', 'vehicle enters traffic'):
            if vehicle in active:
                unmatched['entry_without_previous_exit'] += 1
            active[vehicle] = (link, time)
            continue
        start = active.pop(vehicle, None)
        if start is None or start[0] != link:
            unmatched['exit_without_matching_entry'] += 1
            continue
        duration = time - start[1]
        row = stats.setdefault((mode, link), dict(mode=mode, link_id=link, traversals_count=0,
            total_time_s=0, max_time_s=0, min_time_s=float('inf'), **links[link]))
        row['traversals_count'] += 1
        row['total_time_s'] += duration
        row['min_time_s'] = min(row['min_time_s'], duration)
        if duration > row['max_time_s']:
            row.update(max_time_s=duration, max_vehicle_id=vehicle, max_entry_time_s=start[1])
    for row in stats.values():
        row['mean_time_s'] = row['total_time_s'] / row['traversals_count']
        row['link_freeflow_time_s'] = row['length'] / row['freespeed']
        row['excess_over_link_freeflow_s'] = row['total_time_s'] - row['traversals_count'] * row['link_freeflow_time_s']
    rows = sorted(stats.values(), key=lambda r: (-r['excess_over_link_freeflow_s'], r['mode'], r['link_id']))
    report = dict(run=run.name, iteration=iteration, completed_traversals_count=sum(r['traversals_count'] for r in rows),
        mode_link_pairs_count=len(rows), unmatched_events=dict(unmatched), unfinished_traversals_count=len(active),
        ranked_links=rows[:top], limitations=[
            'Link times include stop dwell and queues; excess is not automatically traffic congestion.',
            'The link free speed ignores vehicle maximum speed; this is a diagnostic baseline only.',
            'Origin and destination links can be traversed only partly; the native link attributes retain MATSim units.',
            'Ranks describe completed traversals only; unfinished and unmatched counts are separate.'])
    destination = Path(results_store.processed_dir(run.name))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f'_transit_link_delays_it{iteration}.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({**report, 'ranked_links': rows[:10]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--iteration', required=True, type=int)
    parser.add_argument('--top', type=int, required=True, help='Number of ranked links to retain')
    args = parser.parse_args()
    if args.top <= 0:
        parser.error('--top must be positive')
    analyse(args.run, args.iteration, args.top)
