"""Apply declared capacities without losing vehicle-specific transit assignments."""
import collections
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import jsonschema
import city


def local_tag(element):
    return element.tag.rsplit('}', 1)[-1]


def load_assignment(path, mapped_vehicles, mapped_schedule):
    """An assignment belongs to exactly one mapped input pair, before day filtering."""
    schema = json.loads(Path(city.REPO, 'config/schema/transit_fleet.schema.json').read_text(encoding='utf-8'))
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate key in transit fleet assignment: ' + key)
            result[key] = value
        return result
    assignment = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    jsonschema.Draft202012Validator(schema).validate(assignment)
    for name, source in (('mapped_vehicles_sha256', mapped_vehicles),
                         ('mapped_schedule_sha256', mapped_schedule)):
        actual = hashlib.sha256(Path(source).read_bytes()).hexdigest()
        if assignment[name] != actual:
            raise ValueError('Transit fleet assignment does not belong to this mapped build: ' + name)
    return assignment


def passenger_count(value, field):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0 or int(value) != value):
        raise ValueError('Transit passenger capacity must be a nonnegative integer: ' + field)
    return int(value)


def capacity_value(cfg, field):
    if cfg.field(field).get('units') != 'persons_per_vehicle':
        raise ValueError('Transit capacity field has incompatible units: ' + field)
    return passenger_count(cfg.get(field), field)


def capacity_pair(cap):
    children = {local_tag(e): e.get('persons') for e in cap}
    return (cap.get('seats', children.get('seats')),
            cap.get('standingRoomInPersons', children.get('standingRoom')))


def set_capacity(vehicle_type, seated, standing):
    capacities = [e for e in vehicle_type if local_tag(e) == 'capacity']
    if len(capacities) != 1:
        raise ValueError('Expected exactly one capacity on vehicle type ' + str(vehicle_type.get('id')))
    cap = capacities[0]
    children = list(cap)
    if children:
        if ('seats' in cap.attrib or 'standingRoomInPersons' in cap.attrib or
                any(local_tag(e) not in ('seats', 'standingRoom') for e in children) or
                len({local_tag(e) for e in children}) != len(children)):
            raise ValueError('Ambiguous legacy transit capacity encoding')
        namespace = cap.tag[:-len('capacity')]
        by_tag = {local_tag(e): e for e in children}
        for tag, value in (('seats', seated), ('standingRoom', standing)):
            child = by_tag.get(tag)
            if child is None:
                child = ET.Element(namespace + tag)
                cap.insert(0, child) if tag == 'seats' else cap.append(child)
            child.set('persons', str(value))
    else:
        cap.set('seats', str(seated))
        cap.set('standingRoomInPersons', str(standing))


def prepare_fleet(root, used_vehicles, cfg, mode_fields, assignment=None):
    """Return a new XML root; input objects remain intact even on validation failure.

    Explicit profiles clone their declared mapped base type. Capacity changes
    do not change its physical dimensions, doors, speed, PCU or engine data.
    Those properties still need an evidenced source type in the mapped input.
    """
    types, vehicles = {}, {}
    for element in root:
        target = types if local_tag(element) == 'vehicleType' else vehicles if local_tag(element) == 'vehicle' else None
        if target is None:
            continue
        key = element.get('id')
        if not key or key in target:
            raise ValueError('Missing or duplicate transit ' + local_tag(element) + ' ID: ' + str(key))
        target[key] = element
    missing = set(used_vehicles) - set(vehicles)
    if missing:
        raise ValueError('Scheduled transit vehicle definitions are missing: ' + ', '.join(sorted(missing)))
    active = {vid: vehicles[vid].get('type') for vid in sorted(used_vehicles)}
    missing_types = set(active.values()) - set(types)
    if missing_types:
        raise ValueError('Active transit vehicle types are undefined: ' + repr(sorted(missing_types, key=str)))

    profiles, assignments = {}, {}
    if assignment is not None:
        assignments = assignment['vehicles']
        missing = set(used_vehicles) - set(assignments)
        extra = set(assignments) - set(vehicles)
        if missing or extra:
            raise ValueError('Transit assignment coverage mismatch; missing active vehicles=%s; unknown vehicles=%s'
                             % (sorted(missing), sorted(extra)))
        declared = assignment['profiles']
        unknown = set(assignments.values()) - set(declared)
        collision = set(declared) & set(types)
        if unknown or collision:
            raise ValueError('Unknown assignment profiles or colliding type IDs: %s; %s'
                             % (sorted(unknown), sorted(collision)))
        for vid, profile_id in assignments.items():
            if vehicles[vid].get('type') != declared[profile_id]['base_type']:
                raise ValueError('Assigned profile base type differs from mapped vehicle: ' + vid)
        for profile_id in sorted(set(assignments[vid] for vid in used_vehicles)):
            spec = declared[profile_id]
            profiles[profile_id] = (spec['base_type'], spec['seats_field'], spec['standing_field'])
    else:
        unknown = set(active.values()) - set(mode_fields)
        if unknown:
            raise ValueError('Active transit types have no declared capacity: ' + ', '.join(sorted(unknown)))
        profiles = {tid: (tid, *mode_fields[tid]) for tid in types if tid in mode_fields}

    resolved = {}
    for profile_id, (base_type, seated_field, standing_field) in profiles.items():
        seats = capacity_value(cfg, seated_field)
        standing = capacity_value(cfg, standing_field)
        if seats + standing == 0:
            raise ValueError('Transit passenger type has zero total capacity: ' + profile_id)
        clone = deepcopy(types[base_type])
        clone.set('id', profile_id)
        set_capacity(clone, seats, standing)
        resolved[profile_id] = clone

    output = deepcopy(root)
    patched = []
    if assignment is not None:
        for element in list(output):
            if local_tag(element) in ('vehicleType', 'vehicle'):
                output.remove(element)
        for profile_id in sorted(resolved):
            output.append(resolved[profile_id])
        for vid in sorted(active):
            clone = deepcopy(vehicles[vid])
            clone.set('type', assignments[vid])
            output.append(clone)
    else:
        # Retain mapped ordering and unused type definitions in the existing
        # mode-capacity path so a guard does not rewrite unrelated inputs.
        for index, element in enumerate(list(output)):
            if local_tag(element) == 'vehicleType' and element.get('id') in resolved:
                output.remove(element)
                output.insert(index, resolved[element.get('id')])
        for element in list(output):
            if local_tag(element) == 'vehicle' and element.get('id') not in used_vehicles:
                output.remove(element)
    for profile_id, (base_type, seated_field, standing_field) in profiles.items():
        old = next(e for e in types[base_type] if local_tag(e) == 'capacity')
        new = next(e for e in resolved[profile_id] if local_tag(e) == 'capacity')
        patched.append((profile_id, *capacity_pair(old), *capacity_pair(new)))
    # The audit counts active vehicles per profile. A per-vehicle map would put
    # every vehicle id of every scenario x day-type set into the committed
    # run-inputs report (2,139 ids a set on the reference city) for no reader.
    by_profile = collections.Counter(assignments[vid] if assignment is not None else tid
                                     for vid, tid in active.items())
    return output, dict(vehicles=len(active), vehicle_capacity_patched=patched,
                        vehicle_types_unpatched=[] if assignment is not None else [tid for tid in types if tid not in resolved],
                        fleet_assignment_mode='explicit_vehicle' if assignment is not None else 'mode_capacity',
                        active_vehicles_by_profile=dict(sorted(by_profile.items())))
