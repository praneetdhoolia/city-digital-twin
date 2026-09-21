import collections
"""Different active vehicle configurations must survive build and sampling."""
from copy import deepcopy
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET

import pytest

from transit_fleet import load_assignment, prepare_fleet
from sample_population import scale_transit_capacity


def fleet():
    return ET.fromstring('''<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd">
      <vehicleType id="Bus"><capacity seats="70" standingRoomInPersons="0"/>
        <length meter="12"/><width meter="2.5"/><passengerCarEquivalents pce="3"/>
        <accessTime secondsPerPerson="0.8"/><egressTime secondsPerPerson="0.7"/>
      </vehicleType>
      <vehicleType id="Metro"><capacity seats="400" standingRoomInPersons="0"/>
        <length meter="90"/></vehicleType>
      <vehicle id="b1" type="Bus"/><vehicle id="b2" type="Bus"/>
      <vehicle id="other_day" type="Bus"/><vehicle id="r1" type="Metro"/>
    </vehicleDefinitions>''')


VALUES = {'A.small.seats': 20, 'A.small.standing': 0,
          'A.large.seats': 40, 'A.large.standing': 60,
          'A.rail.seats': 100, 'A.rail.standing': 900}


class Config:
    def __init__(self, values=None):
        self.values = VALUES if values is None else values

    def get(self, key):
        return self.values[key]

    def field(self, key):
        return {'units': 'persons_per_vehicle'}


def assignment():
    return {'profiles': {
        'small': {'base_type': 'Bus', 'seats_field': 'A.small.seats', 'standing_field': 'A.small.standing'},
        'large': {'base_type': 'Bus', 'seats_field': 'A.large.seats', 'standing_field': 'A.large.standing'},
        'train': {'base_type': 'Metro', 'seats_field': 'A.rail.seats', 'standing_field': 'A.rail.standing'}},
        'vehicles': {'b1': 'small', 'b2': 'large', 'other_day': 'small', 'r1': 'train'}}


def elements(root, tag):
    return {e.get('id'): e for e in root if e.tag.rsplit('}', 1)[-1] == tag}


def capacities(root):
    return {key: {k: int(v) for k, v in next(e for e in t if e.tag.endswith('capacity')).attrib.items()}
            for key, t in elements(root, 'vehicleType').items()}


def test_heterogeneous_fleet_survives_filtering_and_quarter_sample(tmp_path):
    original = fleet()
    before = ET.tostring(original)
    result, audit = prepare_fleet(original, {'b1', 'b2', 'r1'}, Config(), {}, assignment())
    assert ET.tostring(original) == before
    assert {k: v.get('type') for k, v in elements(result, 'vehicle').items()} == {
        'b1': 'small', 'b2': 'large', 'r1': 'train'}
    assert audit['vehicles'] == 3
    assert capacities(result)['small'] == {'seats': 20, 'standingRoomInPersons': 0}
    types = elements(result, 'vehicleType')
    original_bus = elements(original, 'vehicleType')['Bus']
    for name in ('small', 'large'):
        assert [ET.tostring(e) for e in types[name] if not e.tag.endswith('capacity')] == [
            ET.tostring(e) for e in original_bus if not e.tag.endswith('capacity')]
    source, target = tmp_path/'full.xml.gz', tmp_path/'sampled.xml.gz'
    with gzip.open(source, 'wb') as stream:
        stream.write(ET.tostring(result))
    scale_transit_capacity(source, target, .25, 1)
    with gzip.open(target, 'rb') as stream:
        sampled = ET.parse(stream).getroot()
    assert capacities(sampled) == {'small': {'seats': 5, 'standingRoomInPersons': 0},
                                  'large': {'seats': 10, 'standingRoomInPersons': 15},
                                  'train': {'seats': 25, 'standingRoomInPersons': 225}}
    assert dict(collections.Counter(v.get('type') for v in elements(sampled, 'vehicle').values())) == audit['active_vehicles_by_profile']


@pytest.mark.parametrize('defect', ['missing_assignment', 'unknown_vehicle', 'unknown_profile',
                                   'wrong_base', 'type_collision', 'missing_capacity_field'])
def test_incomplete_or_conflicting_assignments_fail_without_mutating_source(defect):
    root, plan, values = fleet(), assignment(), dict(VALUES)
    before = ET.tostring(root)
    if defect == 'missing_assignment': del plan['vehicles']['b1']
    elif defect == 'unknown_vehicle': plan['vehicles']['ghost'] = 'small'
    elif defect == 'unknown_profile': plan['vehicles']['b1'] = 'absent'
    elif defect == 'wrong_base': plan['vehicles']['b1'] = 'train'
    elif defect == 'type_collision': plan['profiles']['Bus'] = deepcopy(plan['profiles']['small'])
    elif defect == 'missing_capacity_field': del values['A.small.standing']
    with pytest.raises((ValueError, KeyError)):
        prepare_fleet(root, {'b1', 'r1'}, Config(values), {}, plan)
    assert ET.tostring(root) == before


@pytest.mark.parametrize('value', [None, True, -1, 2.5, float('nan'), float('inf'), '20'])
def test_invalid_capacities_are_not_coerced(value):
    values = dict(VALUES, **{'A.small.seats': value})
    with pytest.raises(ValueError, match='nonnegative integer'):
        prepare_fleet(fleet(), {'b1'}, Config(values), {}, assignment())


def test_zero_total_capacity_and_missing_scheduled_vehicle_fail():
    with pytest.raises(ValueError, match='zero total'):
        prepare_fleet(fleet(), {'b1'}, Config(dict(VALUES, **{'A.small.seats': 0})), {}, assignment())
    with pytest.raises(ValueError, match='definitions are missing'):
        prepare_fleet(fleet(), {'ghost'}, Config(), {}, assignment())


def test_non_capacity_registry_field_is_refused():
    cfg = Config()
    cfg.field = lambda key: {'units': 'metres'}
    with pytest.raises(ValueError, match='incompatible units'):
        prepare_fleet(fleet(), {'b1'}, cfg, {}, assignment())


def test_duplicate_json_vehicle_assignment_is_not_silently_overwritten(tmp_path):
    path = tmp_path/'assignments.json'
    path.write_text('{"vehicles":{"bus":"first", "bus":"second"}}')
    with pytest.raises(ValueError, match='Duplicate key'):
        load_assignment(path, tmp_path/'not-read', tmp_path/'not-read-either')


def test_unrecognised_active_mode_cannot_keep_mapper_default():
    with pytest.raises(ValueError, match='no declared capacity.*Metro'):
        prepare_fleet(fleet(), {'r1'}, Config(), {'Bus': ('A.small.seats', 'A.small.standing')})


@pytest.mark.parametrize('tag', ['vehicle', 'vehicleType'])
def test_duplicate_mapped_definition_fails(tag):
    root = fleet()
    root.append(deepcopy(next(iter(elements(root, tag).values()))))
    with pytest.raises(ValueError, match='duplicate'):
        prepare_fleet(root, {'b1'}, Config(), {}, assignment())


def test_existing_mode_capacity_path_retains_xml_order_and_values():
    root = fleet()
    result, audit = prepare_fleet(root, {'b1'}, Config(), {'Bus': ('A.large.seats', 'A.large.standing')})
    expected = deepcopy(root)
    cap = next(e for e in expected[0] if e.tag.endswith('capacity'))
    cap.set('seats', '40'); cap.set('standingRoomInPersons', '60')
    for e in list(expected):
        if e.tag.endswith('vehicle') and e.get('id') != 'b1': expected.remove(e)
    assert ET.tostring(result) == ET.tostring(expected)
    assert audit['vehicle_types_unpatched'] == ['Metro']  # unused, never operated


def test_legacy_capacity_encoding_is_preserved():
    root = ET.fromstring('<vehicleDefinitions><vehicleType id="Bus"><capacity><seats persons="70"/>'
                        '</capacity></vehicleType><vehicle id="b1" type="Bus"/></vehicleDefinitions>')
    plan = assignment(); plan['vehicles'] = {'b1': 'large'}
    result, _ = prepare_fleet(root, {'b1'}, Config(), {}, plan)
    assert result.find('.//seats').get('persons') == '40'
    assert result.find('.//standingRoom').get('persons') == '60'
    assert result.find('.//capacity').attrib == {}


def test_assignment_is_bound_to_the_original_mapped_pair(tmp_path):
    paths = [tmp_path/'vehicles.gz', tmp_path/'schedule.gz']
    for p in paths: p.write_bytes(p.name.encode())
    plan = assignment(); plan.update(schema_version=1,
        mapped_vehicles_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
        mapped_schedule_sha256=hashlib.sha256(paths[1].read_bytes()).hexdigest())
    target = tmp_path/'assignments.json'; target.write_text(json.dumps(plan), encoding='utf-8')
    assert load_assignment(target, *paths) == plan
    paths[1].write_bytes(b'different mapped build')
    with pytest.raises(ValueError, match='mapped build'):
        load_assignment(target, *paths)


def mapped_fixture(tmp_path, builder):
    source = tmp_path/'mapped'; source.mkdir()
    day = builder.DAY_TYPES[0]
    schedule = f'''<transitSchedule><transitStops><stopFacility id="a" linkRefId="x"/>
      <stopFacility id="b" linkRefId="y"/></transitStops><transitLine id="line">
      <transitRoute id="feed.{day}.route"><transportMode>bus</transportMode>
      <routeProfile><stop refId="a" departureOffset="00:00:00"/>
      <stop refId="b" arrivalOffset="00:10:00"/></routeProfile>
      <route><link refId="x"/><link refId="y"/></route><departures>
      <departure id="feed.{day}.one" departureTime="08:00:00" vehicleRefId="b1"/>
      <departure id="feed.{day}.two" departureTime="08:05:00" vehicleRefId="b2"/>
      <departure id="other-day" departureTime="09:00:00" vehicleRefId="other_day"/>
      </departures></transitRoute></transitLine></transitSchedule>'''
    for name, contents in [('transitSchedule.xml.gz', schedule.encode()),
                           ('transitVehicles.xml.gz', ET.tostring(fleet()))]:
        with gzip.open(source/name, 'wb') as stream: stream.write(contents)
    plan = assignment(); plan.update(schema_version=1,
        mapped_vehicles_sha256=hashlib.sha256((source/'transitVehicles.xml.gz').read_bytes()).hexdigest(),
        mapped_schedule_sha256=hashlib.sha256((source/'transitSchedule.xml.gz').read_bytes()).hexdigest())
    (source/'fleet_assignments.json').write_text(json.dumps(plan), encoding='utf-8')
    return source, day


def test_run_input_builder_uses_assignments_without_changing_routes_or_clocks(tmp_path, monkeypatch):
    import build_matsim_run_inputs as builder
    monkeypatch.setattr(builder, 'pt_passenger_submodes', lambda cfg: {})
    source, day = mapped_fixture(tmp_path, builder)
    target = tmp_path/'output'
    cfg = Config(dict(VALUES, **{'A.transit.fleet_assignment_mode': 'explicit_vehicle'}))
    audit = builder.split_schedule(str(source), str(target), day, cfg)
    assert audit['departures'] == 2 and audit['departures_dropped'] == 1
    assert audit['active_vehicles_by_profile'] == {'large': 1, 'small': 1}
    with gzip.open(target/'transitSchedule.xml.gz', 'rb') as stream:
        schedule = ET.parse(stream)
    assert [d.get('departureTime') for d in schedule.findall('.//departure')] == ['08:00:00', '08:05:00']
    assert [d.get('refId') for d in schedule.findall('.//route/link')] == ['x', 'y']
    with gzip.open(target/'transitVehicles.xml.gz', 'rb') as stream:
        vehicles = ET.parse(stream).getroot()
    assert capacities(vehicles) == {'small': {'seats': 20, 'standingRoomInPersons': 0},
                                   'large': {'seats': 40, 'standingRoomInPersons': 60}}


def test_run_input_builder_refuses_missing_assignment_before_writing_xml(tmp_path, monkeypatch):
    import build_matsim_run_inputs as builder
    monkeypatch.setattr(builder, 'pt_passenger_submodes', lambda cfg: {})
    source, day = mapped_fixture(tmp_path, builder)
    target = tmp_path/'output'
    path = source/'fleet_assignments.json'; plan = json.loads(path.read_text())
    del plan['vehicles']['b2']; path.write_text(json.dumps(plan))
    cfg = Config(dict(VALUES, **{'A.transit.fleet_assignment_mode': 'explicit_vehicle'}))
    with pytest.raises(ValueError, match='coverage mismatch'):
        builder.split_schedule(str(source), str(target), day, cfg)
    assert not (target/'transitSchedule.xml.gz').exists()
    assert not (target/'transitVehicles.xml.gz').exists()
