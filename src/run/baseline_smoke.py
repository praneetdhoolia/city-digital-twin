"""Execute a bounded, explicitly provisional behavioural case for a new city.

This development entry point consumes prepared city inputs and registry-bound
scoring. It does not require a calibrated C1 translation or offer multi-hour
arms. The normal run harness still owns status, stopping and completion records.
"""
import gzip
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

from lxml import etree

import city
import registry
from registry import param_config
from build.extract_osm_network import fingerprint
from build.repair_transit_order import repair_schedule
from build_matsim_run_inputs import add_nonmotor_reverse_links, strip_unreachable_mode_links
import bootstrap_toolchain as tc
import run_matsim as harness
import results_store


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
    """Add coarse road mode permissions; preserve mapped transit links."""
    exclusions = cfg.get('RUN.smoke.road_mode_exclusions')
    inherited_modes = cfg.get('RUN.smoke.network_mode_sources')
    headways = cfg.get('RUN.smoke.dedicated_transit_headway_s')
    aliases = cfg.get('RUN.smoke.transit_mode_aliases')
    road_factors = cfg.get('RUN.smoke.road_capacity_factors')
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
    with open(destination, 'wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
            zipped.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            zipped.write(text.encode('utf-8'))
    return dict(road_links_receiving_modes=changed, connectivity=dict(applied),
                road_capacity_changes=dict(road_capacity_changes),
                dedicated_transit_capacity_changes=dict(transit_capacity_changes))


def write_vehicles(path, cfg):
    speeds = cfg.get('RUN.smoke.vehicle_speed_ms')
    pcu = cfg.get('RUN.smoke.vehicle_pcu')
    lengths = cfg.get('RUN.smoke.vehicle_length_m')
    if set(speeds) != set(pcu) or set(speeds) != set(lengths):
        raise ValueError('Every network mode needs a complete vehicle profile')
    root = ET.Element('vehicleDefinitions', attrib={
        'xmlns': 'http://www.matsim.org/files/dtd',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'http://www.matsim.org/files/dtd '
                              'http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd'})
    for mode in sorted(speeds):
        vehicle = ET.SubElement(root, 'vehicleType', id=mode)
        ET.SubElement(vehicle, 'length', meter=str(lengths[mode]))
        ET.SubElement(vehicle, 'maximumVelocity', meterPerSecond=str(speeds[mode]))
        ET.SubElement(vehicle, 'passengerCarEquivalents', pce=str(pcu[mode]))
        ET.SubElement(vehicle, 'networkMode', networkMode=mode)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def main(run_config=None):
    cfg = registry.load(run=run_config)
    ceiling = cfg.get('RUN.smoke.wall_ceiling_s')
    if not 0 < ceiling < 3600:
        raise SystemExit('Development smoke requires a positive sub-hour ceiling')
    harness.refuse_concurrent_arm()
    paths = {key: Path(city.path(value)).resolve() for key, value in cfg.get('RUN.smoke.inputs').items()}
    for key, path in paths.items():
        if not path.is_file():
            raise SystemExit('Missing prepared input: ' + key + ': ' + str(path))
    demand_audit = population_audit(paths['plans'])
    if demand_audit['maximum_initial_plans_per_person_count'] > cfg.get('RUN.smoke.replanning.maxAgentPlanMemorySize'):
        raise SystemExit('Plan memory would discard supplied initial choices; declare sufficient memory before launch')
    java, jar = tc.require()
    tc.compile_java()
    iterations = cfg.get('RUN.smoke.controler.lastIteration')
    name = time.strftime('%Y%m%dT%H%M%S') + f'_{iterations}it_100pct-{city.descriptor()["id"]}-smoke'
    run_dir = Path(results_store.raw_dir(name))
    run_dir.mkdir(parents=True, exist_ok=False)
    meta = dict(status='running', scenario=city.descriptor()['intervention']['base_scenario'],
        city=city.descriptor()['id'], run_kind='behavioural_smoke',
        day=city.descriptor()['day_types'][0], fraction=1.0, sample_pct=100.0,
        iterations=iterations, seed=cfg.get('RUN.smoke.global.randomSeed'),
        threads=cfg.get('RUN.smoke.global.numberOfThreads'), xmx=cfg.get('RUN.smoke.xmx'),
        started=harness._now(), pid=os.getpid(),
        notes='Provisional behavioural smoke of the explicit small input population. No full-city expansion, calibration or physical-fidelity claim. Ride is a vehicle proxy; household pairing and detailed controls remain incomplete.')
    input_hashes = {key: fingerprint(path) for key, path in paths.items()}
    meta['inputs_sha256'] = hashlib.sha256(json.dumps(input_hashes, sort_keys=True).encode()).hexdigest()
    meta['controler_sha256'] = harness.controler_sha256()
    meta['values_sha256'] = harness.values_sha256(cfg)
    meta['config_snapshot'] = '_config.json'
    meta['run_config'] = run_config
    harness.write_meta(str(run_dir), meta)
    (run_dir / '_baseline_inputs.json').write_text(json.dumps(input_hashes, indent=2) + '\n', encoding='utf-8')
    cfg.write_snapshot(str(run_dir / '_config.json'))
    started = time.monotonic()
    print('Preparing bounded behavioural smoke:', run_dir, flush=True)
    try:
        (run_dir / '_baseline_demand.json').write_text(
            json.dumps(demand_audit, indent=2) + '\n', encoding='utf-8')
        changed = prepare_network(paths['network'], run_dir / 'network.xml.gz', cfg,
                                  paths['transit_vehicles'])
        (run_dir / '_baseline_network.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
        schedule_audit = repair_schedule(paths['schedule'], run_dir / 'network.xml.gz',
                                         run_dir / 'transitSchedule.xml.gz',
                                         cfg.get('RUN.smoke.transit_timing'))
        (run_dir / '_baseline_schedule.json').write_text(json.dumps(schedule_audit, indent=2) + '\n', encoding='utf-8')
        write_vehicles(run_dir / 'vehicles.xml', cfg)
        runtime = {key: (str(value).replace(os.sep, '/'), 'path', 'prepared baseline input')
                   for key, value in {
                       'network.inputNetworkFile': run_dir / 'network.xml.gz',
                       'plans.inputPlansFile': paths['plans'],
                       'transit.transitScheduleFile': run_dir / 'transitSchedule.xml.gz',
                       'transit.vehiclesFile': paths['transit_vehicles'],
                       'vehicles.vehiclesFile': run_dir / 'vehicles.xml',
                       'controler.outputDirectory': run_dir / 'output'}.items()}
        runtime['global.coordinateSystem'] = (city.crs(), 'identity', 'city descriptor CRS')
        if 'boarding_fares' in paths:
            runtime['boardingFare.tableFile'] = (
                str(paths['boarding_fares']).replace(os.sep, '/'), 'path', 'city boarding fare table')
        if 'hired_fleet' in paths:
            fleet = json.loads(paths['hired_fleet'].read_text(encoding='utf-8'))
            vehicles = fleet['vehicles_by_mode']
            if not vehicles or any(not isinstance(mode, str) or not mode or ':' in mode or ',' in mode
                                   or type(count) is not int or count < 0 for mode, count in vehicles.items()):
                raise ValueError('Hired fleet requires nonnegative integer counts by mode')
            runtime['hiredFleet.vehiclesByMode'] = (
                ','.join(f'{mode}:{count}' for mode, count in sorted(vehicles.items())),
                'derived', 'vehicles in the explicit population from the hashed city fleet derivation')
            (run_dir / '_hired_fleet_input.json').write_text(json.dumps(fleet, indent=2) + '\n', encoding='utf-8')
        config = param_config.write(str(run_dir / 'config.xml'), 'matsim', cfg, runtime)
        print('Road links receiving baseline modes:', changed, flush=True)
        command = [java, '-Xmx' + cfg.get('RUN.smoke.xmx'), '-cp', os.pathsep.join((jar, tc.CLASSES)),
                   'citysim.CitysimControler', config]
        with (run_dir / 'matsim.log').open('w', encoding='utf-8') as log:
            with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT) as proc:
                harness.update_meta(str(run_dir), java_pid=proc.pid)
                try:
                    rc = proc.wait(timeout=ceiling)
                except subprocess.TimeoutExpired:
                    log.write('\nAutomatic behavioural smoke wall ceiling reached\n')
                    log.flush()
                    proc.kill()
                    proc.wait()
                    raise RuntimeError('Automatic behavioural smoke wall ceiling reached')
        elapsed = time.monotonic() - started
        if rc:
            tail = (run_dir / 'matsim.log').read_text(encoding='utf-8', errors='replace').splitlines()[-35:]
            raise RuntimeError('MATSim exited ' + str(rc) + '\n' + '\n'.join(tail))
        reached = harness._last_ended_in_tail(str(run_dir / 'matsim.log'))
        if reached != iterations:
            raise RuntimeError(f'JVM exited without completing declared horizon: {reached} != {iterations}')
        harness.update_meta(str(run_dir), status='completed', rc=rc, wall_s=elapsed, ended=harness._now())
        record = harness.close_out(str(run_dir), 'ran_to_last_iteration', rc, elapsed,
            reached_iteration=reached, extra={'city': city.descriptor()['id'],
                'run_kind': 'behavioural_smoke', 'calibrated': False,
                'run_config': run_config,
                'population_basis': 'explicit_small_provisional_population_no_city_expansion',
                'notes': meta['notes']})
        if record is None:
            raise RuntimeError('Completed JVM but run record failed validation')
        from baseline_behaviour import analyse
        try:
            analyse(name, summary=True)
        except (Exception, SystemExit) as exc:
            print('Run completed; behavioural diagnostics need repair:', exc, flush=True)
        print('Completed provisional smoke:', run_dir, flush=True)
        return 0
    except Exception as exc:
        harness.update_meta(str(run_dir), status='failed', ended=harness._now(),
                            wall_s=time.monotonic() - started, cause=str(exc))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
