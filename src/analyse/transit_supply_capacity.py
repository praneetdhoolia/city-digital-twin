"""Audit scheduled transit flow against the run's declared link capacities."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from iteration_reading import open_table
import results_store


def audit(name, top):
    run = Path(results_store.resolve_or_die(name))
    fleet_path = next((run / 'output').glob('output_allVehicles.xml*'))
    with open_table(str(fleet_path)) as stream:
        fleet = ET.parse(stream)
    types = {v.get('id'): float(v.find('{*}passengerCarEquivalents').get('pce'))
             for v in fleet.findall('{*}vehicleType')}
    vehicles = {v.get('id'): types[v.get('type')] for v in fleet.findall('{*}vehicle')}
    with gzip.open(run / 'transitSchedule.xml.gz', 'rb') as stream:
        schedule = ET.parse(stream)
    passes, pcu = Counter(), defaultdict(float)
    for route in schedule.findall('transitLine/transitRoute'):
        links = [link.get('refId') for link in route.findall('route/link')][1:-1]
        departures = route.findall('departures/departure')
        equivalents = sum(vehicles[d.get('vehicleRefId')] for d in departures)
        for link, occurrences in Counter(links).items():
            passes[link] += occurrences * len(departures)
            pcu[link] += occurrences * equivalents
    rows = []
    with gzip.open(run / 'network.xml.gz', 'rb') as stream:
        for event, link in ET.iterparse(stream, events=('start', 'end')):
            if event == 'start' and link.tag == 'links':
                hours, minutes, seconds = map(float, link.get('capperiod').split(':'))
                period_h = hours + minutes / 60 + seconds / 3600
            if event != 'end' or link.tag != 'link':
                continue
            identity = link.get('id')
            if identity in passes:
                capacity = float(link.get('capacity')) / period_h
                if capacity <= 0:
                    raise ValueError('Scheduled transit uses a link with nonpositive capacity')
                rows.append(dict(link_id=identity, scheduled_interior_traversals_count=passes[identity],
                    scheduled_flow_pcu=pcu[identity], link_capacity_pcu_h=capacity,
                    required_capacity_time_h=pcu[identity] / capacity))
            link.clear()
    rows.sort(key=lambda r: (-r['required_capacity_time_h'], r['link_id']))
    report = dict(run=run.name, scheduled_interior_traversals_count=sum(passes.values()),
        used_interior_links_count=len(rows), ranked_links=rows[:top], limitations=[
            'A flow-budget diagnostic, not measured road capacity or proof of a queue cause.',
            'First and last route links are excluded to avoid partial traversals.',
            'Combines scheduled transit modes; other traffic, stop dwell and storage constraints are excluded.',
            'Does not impose a shared operating window or assume every departure crosses a link in its departure hour.'])
    destination = Path(results_store.processed_dir(run.name))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / '_transit_supply_capacity.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({**report, 'ranked_links': rows[:10]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--top', type=int, required=True)
    args = parser.parse_args()
    if args.top <= 0:
        parser.error('--top must be positive')
    audit(args.run, args.top)
