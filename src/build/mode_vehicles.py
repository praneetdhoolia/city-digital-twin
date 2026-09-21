"""Resolve city-declared vehicle types without substituting another mode's body."""
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import city


def quantity(cfg, key, units, *, zero_allowed=False, integer=False):
    """Read a resolved scalar, including run overlays, and reject unit mistakes."""
    if cfg.field(key)['units'] not in units:
        raise ValueError('Vehicle field has incompatible units: ' + key)
    value = cfg.get(key)
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0 or (not zero_allowed and value == 0)):
        raise ValueError('Vehicle field must be a finite ' +
                         ('nonnegative' if zero_allowed else 'positive') + ' number: ' + key)
    if integer and int(value) != value:
        raise ValueError('Vehicle passenger capacity must be an integer: ' + key)
    return int(value) if integer else value


def explicit_vehicle_xml(cfg, profiles):
    """Build complete XML in memory before the caller changes any file.

    A profile covers one mode, including a routed passenger mode whose type is
    needed during MATSim preparation. No access, dispatch, occupancy, scoring,
    routing-time binding or demand is inferred from the presence of a type.
    """
    schema = json.loads(Path(city.REPO, 'config/schema/mode_vehicles.schema.json').read_text(encoding='utf-8'))
    import jsonschema   # the explicit path's dependency, not the assembler's
    jsonschema.Draft202012Validator(schema).validate(profiles)
    if not profiles:
        raise ValueError('Explicit vehicle types require a nonempty profile mapping')
    modes = cfg.get('RUN.routing.network_modes')
    if (not isinstance(modes, list) or any(not isinstance(mode, str) for mode in modes)
            or len(modes) != len(set(modes))):
        raise ValueError('Network routing modes must be a list of distinct strings')
    missing, extra = set(modes) - set(profiles), set(profiles) - set(modes)
    if missing or extra:
        raise ValueError('Vehicle type coverage mismatch; missing modes=%s; unused modes=%s'
                         % (sorted(missing), sorted(extra)))
    root = ET.Element('vehicleDefinitions', {
        'xmlns': 'http://www.matsim.org/files/dtd',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': 'http://www.matsim.org/files/dtd '
                              'http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd'})
    for mode, profile in sorted(profiles.items()):
        element = ET.SubElement(root, 'vehicleType', id=mode)
        seats = quantity(cfg, profile['seats_field'], ('persons_per_vehicle', 'persons'), zero_allowed=True, integer=True)
        standing = quantity(cfg, profile['standing_field'], ('persons_per_vehicle', 'persons'), zero_allowed=True, integer=True)
        ET.SubElement(element, 'capacity', seats=str(seats), standingRoomInPersons=str(standing))
        for property_name in ('length', 'width'):
            value = quantity(cfg, profile[property_name + '_m_field'], ('m', 'metres'))
            ET.SubElement(element, property_name, meter=str(value))
        if 'maximum_speed_ms_field' in profile:
            speed = quantity(cfg, profile['maximum_speed_ms_field'], ('m/s', 'metres_per_second'))
            ET.SubElement(element, 'maximumVelocity', meterPerSecond=str(speed))
        elif 'maximum_speed_kmh_field' in profile:
            speed = quantity(cfg, profile['maximum_speed_kmh_field'], ('km/h',)) / 3.6
            ET.SubElement(element, 'maximumVelocity', meterPerSecond=str(speed))
        pce = quantity(cfg, profile['pce_field'], ('passenger_car_equivalents',), zero_allowed=True)
        ET.SubElement(element, 'passengerCarEquivalents', pce=str(pce))
        ET.SubElement(element, 'networkMode', networkMode=mode)
    ET.indent(root, space='\t')
    return "<?xml version='1.0' encoding='utf-8'?>\n" + ET.tostring(root, encoding='unicode') + '\n'
