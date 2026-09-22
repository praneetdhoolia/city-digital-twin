"""Assemble the BASE x WEEKDAY run inputs for the harness (9.204, #238).

Until 21 September 2026 the city ran through its own launcher
(`run.py --baseline-smoke`, `src/run/baseline_smoke.py`), which prepared the
network, repaired the schedule and wrote the vehicle types at every launch and
called the harness's close-out from outside it. This step does that
preparation ONCE, into the layout every city's runs read:

    scenarios/matsim/BASE/network.xml.gz            the mapped regional network with
                                                    the declared mode permissions
    scenarios/matsim/BASE/parking_prices.tsv        header only: no priced parking
    scenarios/matsim/BASE/boarding_fares.csv        the transcribed per-route fares
    scenarios/matsim/BASE/hired_fleet.json          the hired-fleet derivation
    scenarios/matsim/BASE/WEEKDAY/transitSchedule.xml.gz   the repaired combined feed
    scenarios/matsim/BASE/WEEKDAY/transitVehicles.xml.gz
    scenarios/matsim/BASE/WEEKDAY/vehicles.xml      per-mode types from A.vehicle.*
    scenarios/matsim/BASE/WEEKDAY/config.xml        the shipped emission (the harness
                                                    re-emits per run)
    scenarios/matsim/_run_inputs_report.json        the assembly's own record
    demand/plans/matsim/population_WEEKDAY.xml.gz   the explicit population with its
                                                    initial mode alternatives

after which `python run.py BASE --day WEEKDAY --run-config <overlay>` runs it
under the harness's own gates, watchers and record. Everything here is the
explicit 1,000-person development case; nothing it produces is a result.
"""
from collections import Counter
import gzip
import json
import math
import os
from pathlib import Path
import shutil
import sys

from lxml import etree

import city
import registry
from build.extract_osm_network import fingerprint
from build.repair_transit_order import repair_schedule
from build import transit_fleet
import build_matsim_run_inputs as build_inputs
from build_matsim_run_inputs import (add_nonmotor_reverse_links, node_elevations_from_dem,
                                     stamp_gradients_body, strip_unreachable_mode_links)

SCENARIO = city.descriptor()['intervention']['base_scenario']
DAY = city.descriptor()['day_types'][0]
OUT = Path(city.path('scenarios', 'matsim'))
PLANS = Path(city.path('demand', 'plans', 'matsim'))
REPORT = OUT / '_run_inputs_report.json'

OUTPUT_INPUTS = {
    'scenarios/matsim/BASE/network.xml.gz': [
        'networks/matsim/schedules/baseline_regional/network.xml.gz',
        'data/raw/geospatial/copernicus_dsm_*.tif',
        'networks/matsim/schedules/baseline_regional/transitVehicles.xml.gz'],
    'scenarios/matsim/BASE/parking_prices.tsv': [],
    'scenarios/matsim/BASE/boarding_fares.csv': ['params/baseline/boarding_fares.csv'],
    'scenarios/matsim/BASE/hired_fleet.json': ['params/baseline/hired_fleet.json'],
    'scenarios/matsim/BASE/WEEKDAY/transitSchedule.xml.gz': [
        'networks/matsim/schedules/baseline_regional/transitSchedule.xml.gz',
        'networks/matsim/schedules/baseline_regional/network.xml.gz',
        'networks/matsim/schedules/baseline_regional/transitVehicles.xml.gz'],
    'scenarios/matsim/BASE/WEEKDAY/transitVehicles.xml.gz': [
        'networks/matsim/schedules/baseline_regional/transitVehicles.xml.gz',
        'networks/matsim/schedules/baseline_regional/transitSchedule.xml.gz',
        'networks/matsim/schedules/baseline_regional/fleet_assignments.json',
        'registry/A_transit_fleet.json'],
    'scenarios/matsim/BASE/WEEKDAY/vehicles.xml': [],
    'scenarios/matsim/BASE/WEEKDAY/config.xml': [],
    'scenarios/matsim/_run_inputs_report.json': [
        'networks/matsim/schedules/baseline_regional/network.xml.gz',
        'networks/matsim/schedules/baseline_regional/transitSchedule.xml.gz',
        'networks/matsim/schedules/baseline_regional/transitVehicles.xml.gz',
        'demand/baseline/plans_core_sample.xml.gz',
        'params/baseline/boarding_fares.csv',
        'params/baseline/hired_fleet.json'],
    'demand/plans/matsim/population_WEEKDAY.xml.gz': ['demand/baseline/plans_core_sample.xml.gz'],
    'demand/plans/matsim/_plans_report.json': ['demand/baseline/_plans_core_sample_report.json'],
}


def population_audit(path):
    """Freeze the explicit input demand before routing adds access stages."""
    groups = {}
    initial_plan_counts = Counter()
    with gzip.open(path, 'rb') as stream:
        for _, person in etree.iterparse(stream, events=('end',), tag='person'):
            plans = person.findall('plan')
            initial_plan_counts[len(plans)] += 1
            selected = [p for p in plans if p.get('selected') == 'yes']
            if not selected and len(plans) == 1:
                selected = plans
            if len(selected) != 1:
                raise ValueError('Input person must have one selected plan: ' + person.get('id'))
            group = person.findtext("attributes/attribute[@name='subpopulation']", default='')
            counts = groups.setdefault(group, dict(persons_count=0, input_legs_count=0,
                                                   destination_activities=Counter()))
            counts['persons_count'] += 1
            counts['input_legs_count'] += len(selected[0].findall('leg'))
            counts['destination_activities'].update(a.get('type') for a in selected[0].findall('activity')[1:])
            person.clear()
    return dict(source_sha256=fingerprint(path), by_subpopulation=groups,
                persons_by_initial_plan_count=dict(sorted(initial_plan_counts.items())),
                maximum_initial_plans_per_person_count=max(initial_plan_counts, default=0),
                note='Input legs and activity destinations before routing; no citywide expansion or completion claim.')


def prepare_network(source, destination, cfg, transit_vehicles):
    """Add the declared road mode permissions; preserve mapped transit links."""
    exclusions = cfg.get('A.baseline.road_mode_exclusions')
    inherited_modes = cfg.get('A.baseline.network_mode_sources')
    headways = cfg.get('A.baseline.dedicated_transit_headway_s')
    aliases = cfg.get('A.baseline.transit_mode_aliases')
    road_factors = cfg.get('A.baseline.road_capacity_factors')
    if any(not math.isfinite(value) or value <= 0 for value in road_factors.values()):
        raise ValueError('Road capacity factors must be positive and finite')
    with gzip.open(transit_vehicles, 'rb') as stream:
        fleet = etree.parse(stream)
    pcu = {}
    for vehicle in fleet.findall('{*}vehicleType'):
        mode = vehicle.find('{*}networkMode').get('networkMode')
        equivalent = float(vehicle.find('{*}passengerCarEquivalents').get('pce'))
        pcu[mode] = max(pcu.get(mode, 0), equivalent)
    with gzip.open(source, 'rb') as stream:
        root = etree.parse(stream)
    changed = 0
    transit_capacity_changes = Counter()
    road_capacity_changes = Counter()
    for link in root.findall('links/link'):
        modes = set(link.get('modes', '').split(','))
        tags = {a.get('name'): a.text for a in link.findall('attributes/attribute')}
        highway = tags.get('osm:way:highway', '')
        if highway in road_factors and road_factors[highway] != 1:
            link.set('capacity', str(float(link.get('capacity')) * road_factors[highway]))
            road_capacity_changes[highway] += 1
        inherited = {mode for mode, source_mode in inherited_modes.items() if source_mode in modes}
        if inherited - modes:
            modes |= inherited
            link.set('modes', ','.join(sorted(modes)))
        if 'car' not in modes:
            for mode in sorted(modes & headways.keys()):
                # MATSim's link flow uses PCU/hour, whereas a train's service
                # interval is in seconds/train. Preserve any greater source
                # capacity; the declared interval is a provisional envelope.
                capacity = pcu[aliases.get(mode, mode)] * 3600 / headways[mode]
                if capacity > float(link.get('capacity')):
                    link.set('capacity', str(capacity))
                    transit_capacity_changes[mode] += 1
            continue
        before = set(modes)
        for mode, denied in exclusions.items():
            if highway not in denied:
                modes.add(mode)
        if modes != before:
            link.set('modes', ','.join(sorted(modes)))
            changed += 1
    text = etree.tostring(root, encoding='unicode',
        doctype='<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">')
    del root
    applied = Counter()
    text = add_nonmotor_reverse_links(text, cfg.get('A.transit.walk_speed_ms'), applied)
    for mode in sorted(set(exclusions) | set(inherited_modes)):
        text = strip_unreachable_mode_links(text, mode, applied)
    # gradient into link travel time (A.gradient.representation = link_speed,
    # 9.209): the DEM sampled at every node, a signed grade_pct on every link,
    # stamped after every other network patch so nothing overwrites it
    gradient = {}
    if cfg.get('A.gradient.representation') == 'link_speed':
        import glob as _glob
        tiles = sorted(_glob.glob(city.path(cfg.get('A.gradient.dem_tiles'))))
        if not tiles:
            raise SystemExit('A.gradient.representation is link_speed but no DEM tile matches A.gradient.dem_tiles')
        elevations = node_elevations_from_dem(text, tiles, city.descriptor()['crs']['epsg'])
        text, gradient = stamp_gradients_body(text, float(cfg.get('A.gradient.grade_clamp_pct')), elevations)
        gradient['nodes_with_elevation'] = len(elevations)
        gradient['dem_tiles'] = [os.path.basename(t) for t in tiles]
    with open(destination, 'wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
            zipped.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            zipped.write(text.encode('utf-8'))
    return dict(road_links_receiving_modes=changed, connectivity=dict(applied),
                road_capacity_changes=dict(road_capacity_changes),
                dedicated_transit_capacity_changes=dict(transit_capacity_changes),
                gradient=gradient)


def write_fleet(inputs, repaired_schedule, destination, cfg):
    """The mapped vehicles with every capacity resolved through the registry (9.206).

    Until 21 September 2026 the mapped file was copied byte for byte, and it
    carries pt2matsim's defaults (Bus 70, Rail 400, Subway 300, Ferry 250
    seats, no standing room). The framework's explicit representation
    (docs/transit_fleet.md) assigns each vehicle the profile
    build_transit_fleet.py derived for the line it serves and reads the
    profile's seats and standing places from `A.transit.*`; the assignment is
    bound to the mapped build by hash, so a remapped feed refuses an old file.
    """
    if cfg.get('A.transit.fleet_assignment_mode') != 'explicit_vehicle':
        raise SystemExit('this city assigns capacities per vehicle; declare '
                         'A.transit.fleet_assignment_mode = explicit_vehicle and run build_transit_fleet.py')
    assignment = transit_fleet.load_assignment(str(inputs['fleet_assignments']),
                                               str(inputs['transit_vehicles']), str(inputs['schedule']))
    with gzip.open(repaired_schedule, 'rb') as f:
        used = set(etree.parse(f).xpath('//departure/@vehicleRefId'))
    # the framework's own parser and writer for the vehicles file, as
    # build_matsim_run_inputs.py uses them, so both cities ship one shape
    import xml.etree.ElementTree as ET
    with gzip.open(inputs['transit_vehicles'], 'rb') as f:
        vtree = ET.parse(f)
    root, audit = transit_fleet.prepare_fleet(vtree.getroot(), used, cfg, {}, assignment)
    vtree._setroot(root)
    from det_io import gzip_writer
    with gzip_writer(str(destination), text=False) as f:
        vtree.write(f, encoding='utf-8', xml_declaration=True)
    return dict(audit, vehicle_refs=len(used))


def copy_bytes(src, dst):
    shutil.copyfile(src, dst)
    return fingerprint(dst)


def main():
    cfg = registry.load(scenario=SCENARIO, day=DAY)
    if build_inputs.scoring_translation(cfg) != 'bound_fields':
        raise SystemExit('this city declares RUN.scoring.translation = %r; this assembly '
                         'emits bound scoring fields only' % cfg.get('RUN.scoring.translation'))
    inputs = {key: Path(city.path(value)).resolve() for key, value in cfg.get('A.baseline.inputs').items()}
    for key, path in inputs.items():
        if not path.is_file():
            raise SystemExit('missing prepared input: %s: %s' % (key, path))
    demand = population_audit(inputs['plans'])
    if demand['maximum_initial_plans_per_person_count'] > cfg.get('RUN.replanning.max_agent_plan_memory'):
        raise SystemExit('plan memory would discard supplied initial choices; declare '
                         'RUN.replanning.max_agent_plan_memory at or above %d'
                         % demand['maximum_initial_plans_per_person_count'])

    base = OUT / SCENARIO
    day_dir = base / DAY
    day_dir.mkdir(parents=True, exist_ok=True)
    PLANS.mkdir(parents=True, exist_ok=True)

    print('network: declared mode permissions on the mapped regional network', flush=True)
    network = prepare_network(inputs['network'], base / 'network.xml.gz', cfg, inputs['transit_vehicles'])
    print('schedule: repaired against the run network', flush=True)
    schedule = repair_schedule(inputs['schedule'], base / 'network.xml.gz',
                               day_dir / 'transitSchedule.xml.gz',
                               cfg.get('A.baseline.transit_timing'))
    fleet = write_fleet(inputs, day_dir / 'transitSchedule.xml.gz', day_dir / 'transitVehicles.xml.gz', cfg)
    print('fleet: %d vehicles on %d capacity profiles' % (fleet['vehicle_refs'], len(fleet['vehicle_capacity_patched'])), flush=True)
    build_inputs.write_mode_vehicles(str(day_dir / 'vehicles.xml'), cfg)
    # No parking price is observed for this city: a header-only table prices
    # every link free, which the parking module reads as a run with no charge.
    # The harness requires the file so a scenario that LOST its table is told
    # apart from one that never priced anything (#33).
    with open(base / 'parking_prices.tsv', 'w', encoding='utf-8', newline='\n') as f:
        f.write('link_id\tprice_%s_hr\tsearch_min\n' % city.descriptor().get('currency', 'money').lower())
    tables = {}
    if cfg.get('A.fare.boarding_representation') == 'table':
        tables['boarding_fares'] = copy_bytes(inputs['boarding_fares'], base / 'boarding_fares.csv')
    if 'hired_fleet' in inputs:
        tables['hired_fleet'] = copy_bytes(inputs['hired_fleet'], base / 'hired_fleet.json')
    plans_dst = PLANS / ('population_%s.xml.gz' % DAY)
    copy_bytes(inputs['plans'], plans_dst)
    # the plans report the launcher reads for the build fraction (9.205): the
    # plans builder's own report, or a report saying everyone is in the file
    plans_report = Path(str(inputs['plans']).replace('plans_core_sample.xml.gz', '_plans_core_sample_report.json'))
    if plans_report.is_file():
        (PLANS / '_plans_report.json').write_text(plans_report.read_text(encoding='utf-8'),
                                                  encoding='utf-8', newline='\n')
    else:
        (PLANS / '_plans_report.json').write_text(
            json.dumps(dict(build_fraction=1.0, note='an explicit population: everyone is in the file'), indent=2) + '\n',
            encoding='utf-8', newline='\n')

    # The shipped emission, through the same emitter and closure test the
    # harness uses per run; the paths are relative to the day directory.
    paths = dict(
        output='output',
        network=os.path.relpath(base / 'network.xml.gz', day_dir).replace('\\', '/'),
        plans=os.path.relpath(plans_dst, day_dir).replace('\\', '/'),
        schedule='transitSchedule.xml.gz',
        vehicles='transitVehicles.xml.gz',
        mode_vehicles='vehicles.xml',
        parking_prices=os.path.relpath(base / 'parking_prices.tsv', day_dir).replace('\\', '/'),
        fraction=cfg.get('RUN.sample.fraction'))
    if 'boarding_fares' in tables:
        paths['boarding_fares'] = os.path.relpath(base / 'boarding_fares.csv', day_dir).replace('\\', '/')
    if cfg.get('B.hired_fleet.representation') == 'pooled_queue':
        paths['hired_fleet'] = str(base / 'hired_fleet.json')
    build_inputs.check_scoring_order(cfg)
    build_inputs.write_config(str(day_dir / 'config.xml'), cfg, None, DAY, paths)

    report = dict(
        city=city.descriptor()['id'], scenario=SCENARIO, day_types=[DAY],
        scoring_translation='bound_fields',
        purpose_share=None,
        purpose_share_note='no C1 translation for this city: every scoring parameter is a bound '
                           'registry field, so no purpose-weighted value of time is averaged',
        inputs=dict(cfg.get('A.baseline.inputs')),
        inputs_sha256={key: fingerprint(path) for key, path in inputs.items()},
        demand=demand, network=network, schedule=schedule, fleet=fleet, tables_sha256=tables,
        parking='header only: no parking price is observed for this city; every link is free',
        note='The explicit 1,000-person development case assembled for the harness (9.204). '
             'No citywide expansion, no target, no result.')
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + '\n',
                      encoding='utf-8', newline='\n')
    print('assembled', base, 'and', plans_dst, flush=True)
    print('run it: CITYSIM_CITY=%s python run.py --scenario %s --day %s --run-config smoke_two_iterations'
          % (city.descriptor()['id'], SCENARIO, DAY), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
