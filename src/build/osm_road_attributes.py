"""Resolve tagged road quantities without imputing lane splits or traffic speeds.

Semantics: https://wiki.openstreetmap.org/wiki/Key:lanes,
https://wiki.openstreetmap.org/wiki/Key:oneway and
https://wiki.openstreetmap.org/wiki/Key:maxspeed.
Directions refer to native OSM node order, never compass direction.
"""
import json

from build.audit_osm_transport_tags import normalise


def direction(tags):
    raw = tags.get('oneway', '').strip()
    if raw in ('yes', '1', 'true'):
        return 'forward', 'explicit'
    if raw == '-1':
        return 'backward', 'explicit'
    if raw in ('no', '0', 'false'):
        return 'both', 'explicit'
    if raw:
        return 'unresolved', 'non_static_or_unrecognised_oneway'
    if tags.get('junction') == 'roundabout' or tags.get('highway') == 'motorway':
        return 'forward', 'implied_by_osm_definition'
    return 'unresolved', 'not_tagged'


def lanes(tags, flow):
    keys = {'total': 'lanes', 'forward': 'lanes:forward',
            'backward': 'lanes:backward', 'shared': 'lanes:both_ways'}
    values, problems = {}, []
    for name, key in keys.items():
        values[name] = None
        if key in tags:
            values[name], _, status = normalise(key, tags[key])
            if status != 'normalised':
                problems.append('invalid_' + name)
    total, forward, backward, shared = (values[key] for key in keys)
    parts = [value for key, value in values.items() if key != 'total' and value is not None]
    if total is not None and sum(parts) > total:
        problems.append('parts_exceed_total')
    if total is not None and all(values[key] is not None for key in ('forward', 'backward', 'shared')):
        if sum(parts) != total:
            problems.append('parts_disagree_with_total')
    # A total may include reserved or contraflow lanes. Their existence must
    # not be hidden by assigning the entire total to the base oneway direction.
    special = sorted(key for key in tags if key.startswith(('oneway:', 'lanes:'))
                     and key not in keys.values())
    derived = dict(forward=forward, backward=backward)
    status = 'explicit_directional' if forward is not None or backward is not None else 'unsplit_total' if total is not None else 'missing'
    if flow in ('forward', 'backward') and not special:
        opposite = 'backward' if flow == 'forward' else 'forward'
        if values[opposite] not in (None, 0) or shared not in (None, 0):
            problems.append('oneway_with_opposing_or_shared_lanes')
        if total is not None and values[flow] is not None and values[flow] != total:
            problems.append('oneway_direction_disagrees_with_total')
        if total is not None and not problems:
            derived[flow] = total
            derived[opposite] = 0
            status = 'oneway_total_identity'
    if problems:
        derived = dict(forward=None, backward=None)
        status = 'conflict_or_invalid'
    return dict(lanes_total_count=total, lanes_tagged_forward_count=forward,
                lanes_tagged_backward_count=backward, lanes_shared_count=shared,
                lanes_resolved_forward_count=derived['forward'],
                lanes_resolved_backward_count=derived['backward'],
                lanes_status=status, lanes_problems=';'.join(problems),
                lane_or_direction_qualifier_keys=';'.join(special))


def speed(tags, side):
    directional = 'maxspeed:' + side
    key = directional if directional in tags else 'maxspeed'
    if key not in tags:
        return None, '', 'missing'
    value, _, status = normalise(key, tags[key])
    # Invalid directional data must not silently fall back to the general tag.
    return value, key, status


def resolve(tags):
    flow, basis = direction(tags)
    result = dict(oneway_direction=flow, oneway_basis=basis, **lanes(tags, flow))
    for side in ('forward', 'backward'):
        value, key, status = speed(tags, side)
        result.update({f'speed_limit_{side}_kmh': value,
                       f'speed_limit_{side}_source_key': key,
                       f'speed_limit_{side}_status': status})
    for key in ('width', 'width:carriageway'):
        value, _, status = normalise(key, tags[key]) if key in tags else (None, 'm', 'missing')
        prefix = 'width' if key == 'width' else 'carriageway_width'
        result.update({prefix + '_m': value, prefix + '_status': status})
    # Keep every source tag, including restrictions not interpreted here.
    result['source_tags_json'] = json.dumps(tags, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    result['unresolved_speed_qualifier_keys'] = ';'.join(sorted(
        key for key in tags if key.startswith('maxspeed:')
        and key not in ('maxspeed:forward', 'maxspeed:backward')))
    result['source'] = 'derived_from_mapper_reported_tags'
    result['model_input_status'] = 'requires_access_capacity_and_source_currency_validation'
    return result
