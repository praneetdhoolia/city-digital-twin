"""City-specific road bodies must reach vehicle XML through real resolutions."""
from copy import deepcopy
import xml.etree.ElementTree as ET

import jsonschema
import pytest
import registry
from build_matsim_run_inputs import write_mode_vehicles
from mode_vehicles import explicit_vehicle_xml


def configuration(overrides=None):
    # Synthetic test dimensions, not measurements or production defaults.
    values = {
        'RUN.routing.network_modes': (['compact', 'cargo'], 'enum'),
        'V.compact.length': (3, 'm'), 'V.compact.width': (1.5, 'm'),
        'V.compact.pce': (.6, 'passenger_car_equivalents'),
        'V.compact.speed': (36, 'km/h'),
        'V.compact.seats': (2, 'persons_per_vehicle'),
        'V.compact.standing': (0, 'persons_per_vehicle'),
        'V.cargo.length': (8, 'metres'), 'V.cargo.width': (2.5, 'metres'),
        'V.cargo.pce': (2, 'passenger_car_equivalents'),
        'V.cargo.speed': (12, 'metres_per_second'),
        'V.cargo.seats': (0, 'persons_per_vehicle'),
        'V.cargo.standing': (0, 'persons_per_vehicle'),
    }
    profiles = {mode: {name + '_field': 'V.' + mode + '.' + attr
                       for name, attr in [('length_m', 'length'), ('width_m', 'width'), ('pce', 'pce'),
                                          ('seats', 'seats'), ('standing', 'standing')]}
                for mode in ('compact', 'cargo')}
    profiles['compact'].update(maximum_speed_kmh_field='V.compact.speed',
                               seats_field='V.compact.seats', standing_field='V.compact.standing')
    profiles['cargo']['maximum_speed_ms_field'] = 'V.cargo.speed'
    values['RUN.qsim.mode_vehicle_fields'] = (profiles, 'registry_field_mapping')
    fields = {key: dict(value=value, units=units, source='definition', status='active', description='test fixture')
              for key, (value, units) in values.items()}
    return registry.Config(fields, {key: 'fixture' for key in fields}, [('run', overrides or {})])


def types(text):
    root = ET.fromstring(text)
    return {e.get('id'): {c.tag.rsplit('}', 1)[-1]: c.attrib for c in e} for e in root}


def test_new_modes_keep_distinct_bodies_and_resolved_run_overrides(tmp_path):
    cfg = configuration({'V.compact.pce': .8, 'V.compact.speed': 54})
    target = tmp_path / 'vehicles.xml'
    write_mode_vehicles(target, cfg)
    result = types(target.read_text())
    assert set(result) == {'compact', 'cargo'}
    assert result['compact']['width'] == {'meter': '1.5'}
    assert result['cargo']['width'] == {'meter': '2.5'}
    assert result['compact']['passengerCarEquivalents'] == {'pce': '0.8'}
    assert result['cargo']['passengerCarEquivalents'] == {'pce': '2'}
    assert result['compact']['maximumVelocity'] == {'meterPerSecond': '15.0'}
    assert result['cargo']['maximumVelocity'] == {'meterPerSecond': '12'}
    assert result['compact']['capacity'] == {'seats': '2', 'standingRoomInPersons': '0'}
    assert result['cargo']['capacity'] == {'seats': '0', 'standingRoomInPersons': '0'}
    assert result['compact']['networkMode'] == {'networkMode': 'compact'}
    assert 'V.compact.speed' in cfg._reads and 'V.compact.pce' in cfg._reads
    # Sorting declarations does not change the emitted vehicle data.
    profiles = cfg.get('RUN.qsim.mode_vehicle_fields')
    reversed_profiles = dict(reversed(list(profiles.items())))
    assert explicit_vehicle_xml(cfg, profiles) == explicit_vehicle_xml(cfg, reversed_profiles)


@pytest.mark.parametrize('bad', [True, -1, 0, float('nan'), float('inf'), '3'])
def test_invalid_dimensions_fail_before_replacing_existing_file(tmp_path, bad):
    target = tmp_path / 'vehicles.xml'
    target.write_text('previous valid input')
    with pytest.raises(ValueError):
        write_mode_vehicles(target, configuration({'V.compact.width': bad}))
    assert target.read_text() == 'previous valid input'


@pytest.mark.parametrize('field,value', [('V.compact.seats', 1.5), ('V.compact.standing', -1),
                                        ('V.compact.pce', -1), ('V.compact.speed', 0)])
def test_invalid_capacity_pce_or_speed_is_refused(field, value, tmp_path):
    with pytest.raises(ValueError):
        write_mode_vehicles(tmp_path/'vehicles.xml', configuration({field: value}))


def test_zero_pce_and_zero_passenger_capacity_are_preserved(tmp_path):
    cfg = configuration({'V.compact.pce': 0, 'V.compact.seats': 0})
    p = tmp_path/'vehicles.xml'
    write_mode_vehicles(p, cfg)
    row = types(p.read_text())['compact']
    assert row['passengerCarEquivalents']['pce'] == '0'
    assert row['capacity'] == {'seats': '0', 'standingRoomInPersons': '0'}


def test_units_are_checked_before_speed_conversion(tmp_path):
    cfg = configuration()
    cfg._fields['V.compact.speed']['units'] = 'metres_per_second'
    with pytest.raises(ValueError, match='incompatible units'):
        write_mode_vehicles(tmp_path/'vehicles.xml', cfg)


@pytest.mark.parametrize('defect', ['missing', 'extra', 'double_speed', 'partial_capacity', 'literal_value', 'bad_id'])
def test_incomplete_or_ambiguous_mapping_is_refused(tmp_path, defect):
    cfg = configuration()
    profiles = deepcopy(cfg.get('RUN.qsim.mode_vehicle_fields'))
    if defect == 'missing': del profiles['cargo']
    elif defect == 'extra': profiles['unused'] = deepcopy(profiles['cargo'])
    elif defect == 'double_speed': profiles['compact']['maximum_speed_ms_field'] = 'V.cargo.speed'
    elif defect == 'partial_capacity': del profiles['compact']['standing_field']
    elif defect == 'literal_value': profiles['compact']['pce_field'] = .5
    elif defect == 'bad_id': profiles['bad,mode'] = profiles.pop('cargo')
    cfg = configuration({'RUN.qsim.mode_vehicle_fields': profiles})
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        write_mode_vehicles(tmp_path/'vehicles.xml', cfg)


def test_unobtained_field_cannot_become_a_default_vehicle_value(tmp_path):
    cfg = configuration({'V.compact.width': None})
    cfg._fields['V.compact.width']['status'] = 'unobtained'
    with pytest.raises(registry.RegistryError, match='UNOBTAINED'):
        write_mode_vehicles(tmp_path/'vehicles.xml', cfg)
