"""Assign every mapped transit vehicle its evidenced capacity profile (9.206).

Until 21 September 2026 the run-input assembly copied the mapped
`transitVehicles.xml.gz` byte for byte, and that file carries pt2matsim's own
defaults: Bus 70 seats, Rail 400, Subway 300, Ferry 250, no standing room. A
12-car suburban rake that carries about 5,000 people at peak was simulated as
400 seats, a Line 3 train that carries 3,000 as 300, and every vehicle refused
boarding at its seats. Under the sample scaler that is worse still: 400 x 0.01
is 4 seats a train.

This step writes `fleet_assignments.json` beside the mapped schedule and
vehicles (the framework's explicit representation, docs/transit_fleet.md):
one capacity profile per operated configuration the registry declares in
`A.transit.fleet_profiles`, each mapped vehicle assigned to the profile of the
line it serves. A profile is chosen by the transit line's OSM route relation
(the feed builder writes generated lines as `BASE_<relation>_<direction>`) or,
for a mode with one profile, by the route's transport mode. Every active
vehicle must land on a profile; a line nothing covers refuses the build.

The capacities themselves are registry fields (`A.transit.*_capacity_*`):
seated and standing places per vehicle, each with its published source or its
derivation, the one assumed value (bus standing room) carrying its sweep and
the reason the derivation is blocked. The assembly resolves the profiles
through the registry at build time (`transit_fleet.prepare_fleet`), so a
changed declaration changes the shipped vehicles without a remap.

    CITYSIM_CITY=mumbai PYTHONPATH=src python cities/mumbai/build/build_transit_fleet.py
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

import city
import registry

MAPPED = Path(city.path('networks', 'matsim', 'schedules', 'baseline_regional'))
SCHEDULE = MAPPED / 'transitSchedule.xml.gz'
VEHICLES = MAPPED / 'transitVehicles.xml.gz'
ASSIGNMENTS = MAPPED / 'fleet_assignments.json'
REPORT = Path(city.path('data', 'processed', 'acquisition', 'transit_fleet_assignment.json'))

OUTPUT_INPUTS = {
    'networks/matsim/schedules/baseline_regional/fleet_assignments.json': [
        'networks/matsim/schedules/baseline_regional/transitSchedule.xml.gz',
        'networks/matsim/schedules/baseline_regional/transitVehicles.xml.gz',
        'registry/A_transit_fleet.json'],
    'data/processed/acquisition/transit_fleet_assignment.json': [
        'networks/matsim/schedules/baseline_regional/transitSchedule.xml.gz',
        'networks/matsim/schedules/baseline_regional/transitVehicles.xml.gz',
        'registry/A_transit_fleet.json'],
}

# The capacity fields each profile reads, named here so the hardcoding ledger
# sees every declared field wired to this producer (docs/transit_fleet.md:
# a reference inside bulk assignment JSON alone is invisible to it).
CAPACITY_FIELDS = (
    'A.transit.ferry_versova_madh_capacity_seated', 'A.transit.ferry_marve_manori_capacity_seated',
    'A.transit.ferry_gorai_borivali_capacity_seated', 'A.transit.ferry_borivali_esselworld_capacity_seated',
    'A.transit.ferry_wharf_mora_capacity_seated', 'A.transit.ferry_gateway_mandwa_capacity_seated',
    'A.transit.ferry_m2m_mandwa_capacity_seated',
    'A.transit.rail_capacity_seated', 'A.transit.rail_capacity_standing', 'A.transit.rail_capacity_total',
    'A.transit.rail_ac_capacity_seated', 'A.transit.rail_ac_capacity_standing',
    'A.transit.rail_15car_capacity_seated', 'A.transit.rail_15car_capacity_standing',
    'A.transit.bus_capacity_seated', 'A.transit.bus_capacity_standing',
    'A.transit.metro_seated_share',
    'A.transit.metro_line1_capacity_total', 'A.transit.metro_line1_capacity_seated', 'A.transit.metro_line1_capacity_standing',
    'A.transit.metro_beml_capacity_total', 'A.transit.metro_beml_capacity_seated', 'A.transit.metro_beml_capacity_standing',
    'A.transit.metro_line3_capacity_total', 'A.transit.metro_line3_capacity_seated', 'A.transit.metro_line3_capacity_standing',
    'A.transit.metro_navi_capacity_total', 'A.transit.metro_navi_capacity_seated', 'A.transit.metro_navi_capacity_standing',
    'A.transit.ferry_elephanta_capacity_seated', 'A.transit.ferry_creek_capacity_seated', 'A.transit.ferry_capacity_standing',
)

LINE_RE = re.compile(r'<transitLine id="([^"]*)"')
ROUTE_RE = re.compile(r'<transitRoute id="[^"]*">(.*?)</transitRoute>', re.S)
MODE_RE = re.compile(r'<transportMode>([^<]*)</transportMode>')
VEH_RE = re.compile(r'vehicleRefId="([^"]*)"')
VEHICLE_RE = re.compile(r'<vehicle id="([^"]*)" type="([^"]*)"')
GENERATED_LINE_RE = re.compile(r'^BASE_(\d+)_\d+$')
DIRECTORY_LINE_RE = re.compile(r'^BASE_MMB_(\d+)_\d+$')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lines_of(schedule_text):
    """(line id, transport mode, vehicle ids) per transit line of the mapped schedule."""
    starts = [(m.start(), m.group(1)) for m in LINE_RE.finditer(schedule_text)]
    for i, (start, line_id) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(schedule_text)
        body = schedule_text[start:end]
        modes, vehicles = set(), []
        for route in ROUTE_RE.finditer(body):
            modes.update(MODE_RE.findall(route.group(1)))
            vehicles.extend(VEH_RE.findall(route.group(1)))
        if not modes and not vehicles:
            continue    # an empty line: the mapped feed keeps lines whose every route was dropped
        if len(modes) != 1:
            raise SystemExit('transit line %s carries %d transport modes; one expected' % (line_id, len(modes)))
        yield line_id, modes.pop(), vehicles


def profile_for(line_id, mode, base_type, by_relation, by_mode, by_directory=None, by_substring=None):
    m = GENERATED_LINE_RE.match(line_id)
    if m and m.group(1) in by_relation:
        return by_relation[m.group(1)]
    for needle, profile_id in sorted((by_substring or {}).items(), key=lambda kv: -len(kv[0])):
        if needle in line_id:               # the timetable's AC and 15-car routes
            return profile_id
    m = DIRECTORY_LINE_RE.match(line_id)
    if m and m.group(1) in (by_directory or {}):
        return by_directory[m.group(1)]
    if base_type in by_mode.get(mode, {}):
        return by_mode[mode][base_type]
    raise SystemExit('transit line %s (%s, mapped type %s) falls to no capacity profile: declare it in '
                     'A.transit.fleet_profiles by relation or by transport mode' % (line_id, mode, base_type))


def main():
    cfg = registry.load(scenario=city.descriptor()['intervention']['base_scenario'],
                        day=city.descriptor()['day_types'][0])
    if cfg.get('A.transit.fleet_assignment_mode') != 'explicit_vehicle':
        raise SystemExit('A.transit.fleet_assignment_mode is not explicit_vehicle; nothing to assign')
    for field in CAPACITY_FIELDS:
        # every capacity is resolved once here, so an unobtained or malformed
        # declaration refuses the assignment before the assembly reads it
        if cfg.field(field).get('units') not in ('persons_per_vehicle', 'ratio'):
            raise SystemExit('%s: units must be persons_per_vehicle or ratio' % field)
        cfg.get(field)
    declared = cfg.get('A.transit.fleet_profiles')
    cfg.get('A.baseline_transit.directory_crossings')   # the crossings the directory lines come from
    profiles, by_relation, by_mode, by_directory, by_substring = {}, {}, {}, {}, {}
    for profile_id, spec in declared.items():
        if spec.get('route_id_contains'):
            if spec['route_id_contains'] in by_substring:
                raise SystemExit('route id substring %s is claimed by two profiles' % spec['route_id_contains'])
            by_substring[spec['route_id_contains']] = profile_id
        profiles[profile_id] = dict(base_type=spec['base_type'], seats_field=spec['seats_field'],
                                    standing_field=spec['standing_field'])
        for rel in spec.get('relations', []):
            if rel in by_relation:
                raise SystemExit('relation %s is claimed by two profiles' % rel)
            by_relation[rel] = profile_id
        for route in spec.get('directory_routes', []):
            if route in by_directory:
                raise SystemExit('directory route %s is claimed by two profiles' % route)
            by_directory[route] = profile_id
        if spec.get('transport_mode'):
            # one profile per (mode, mapped base type): the mapper typed the
            # Central and Uran patterns C and U beside Rail
            slot = by_mode.setdefault(spec['transport_mode'], {})
            if spec['base_type'] in slot:
                raise SystemExit('transport mode %s, base type %s is claimed by two profiles'
                                 % (spec['transport_mode'], spec['base_type']))
            slot[spec['base_type']] = profile_id

    with gzip.open(VEHICLES, 'rt', encoding='utf-8') as f:
        vehicle_types = dict(VEHICLE_RE.findall(f.read()))
    with gzip.open(SCHEDULE, 'rt', encoding='utf-8') as f:
        schedule_text = f.read()

    vehicles, per_profile, per_line = {}, {}, {}
    for line_id, mode, line_vehicles in lines_of(schedule_text):
        mapped_types = sorted(set(vehicle_types.get(v) for v in line_vehicles))
        if len(mapped_types) != 1:
            raise SystemExit('transit line %s runs %d mapped vehicle types; one expected' % (line_id, len(mapped_types)))
        profile_id = profile_for(line_id, mode, mapped_types[0], by_relation, by_mode, by_directory, by_substring)
        base = profiles[profile_id]['base_type']
        for vid in line_vehicles:
            if vid not in vehicle_types:
                raise SystemExit('scheduled vehicle %s is not defined in the mapped vehicles' % vid)
            if vehicle_types[vid] != base:
                raise SystemExit('vehicle %s of line %s is mapped as %s, profile %s clones %s'
                                 % (vid, line_id, vehicle_types[vid], profile_id, base))
            if vehicles.get(vid, profile_id) != profile_id:
                raise SystemExit('vehicle %s is shared by lines on different profiles' % vid)
            vehicles[vid] = profile_id
        per_profile[profile_id] = per_profile.get(profile_id, 0) + len(line_vehicles)
        per_line[line_id] = profile_id
    unassigned = sorted(set(vehicle_types) - set(vehicles))

    assignment = dict(
        schema_version=1,
        mapped_vehicles_sha256=sha256(VEHICLES),
        mapped_schedule_sha256=sha256(SCHEDULE),
        description='Capacity profiles per operated configuration, assigned by route relation or '
                    'transport mode from A.transit.fleet_profiles (build_transit_fleet.py, 9.206).',
        profiles=profiles,
        vehicles=dict(sorted(vehicles.items())))
    ASSIGNMENTS.write_text(json.dumps(assignment, indent=1, ensure_ascii=False) + '\n',
                           encoding='utf-8', newline='\n')
    capacities = {}
    for profile_id, spec in profiles.items():
        capacities[profile_id] = dict(seats=cfg.get(spec['seats_field']), standing=cfg.get(spec['standing_field']),
                                      seats_field=spec['seats_field'], standing_field=spec['standing_field'])
    report = dict(
        source='derived',
        assignment='networks/matsim/schedules/baseline_regional/fleet_assignments.json',
        mapped_vehicles=len(vehicle_types), assigned_vehicles=len(vehicles),
        unassigned_mapped_vehicles=len(unassigned),
        lines=len(per_line), vehicles_by_profile=dict(sorted(per_profile.items())),
        capacities_per_vehicle=capacities,
        limitations=[
            'One suburban profile: which departures run AC, 15-car or MEMU stock is not yet assigned per departure.',
            'One bus profile for every operator; the standing room is the one assumed capacity (A.transit.bus_capacity_standing, swept).',
            'Metro seated/standing splits other than Line 1 follow Line 1 seated share (A.transit.metro_seated_share).',
            'Physical dimensions, doors and speeds stay the mapper base types; capacities only.'])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('mapped_vehicles', 'assigned_vehicles', 'unassigned_mapped_vehicles',
                                             'lines', 'vehicles_by_profile')}, indent=1))
    for profile_id, c in capacities.items():
        print('%-24s seats %5d standing %5d' % (profile_id, c['seats'], c['standing']))


if __name__ == '__main__':
    main()
