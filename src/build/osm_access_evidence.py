"""Read explicit OSM access inheritance without creating a routable permission.

The documented tag hierarchy is a vocabulary, not a country's traffic law:
https://wiki.openstreetmap.org/wiki/Key:access
https://wiki.openstreetmap.org/wiki/Key:psv
https://wiki.openstreetmap.org/wiki/Key:motorcar

No highway-class defaults, direction, physical suitability or traveller-purpose
rules are supplied here. A tagged grant alone does not establish traversability.
"""

# Generic documented OSM categories. Consumers must establish their relationship
# to local vehicle/permit classes before using them in a simulation.
ACCESS_CHAINS = {
    'foot': ('access', 'foot'),
    'bicycle': ('access', 'vehicle', 'bicycle'),
    'motorcar': ('access', 'vehicle', 'motor_vehicle', 'motorcar'),
    'motorcycle': ('access', 'vehicle', 'motor_vehicle', 'motorcycle'),
    'moped': ('access', 'vehicle', 'motor_vehicle', 'moped'),
    'auto_rickshaw': ('access', 'vehicle', 'motor_vehicle', 'auto_rickshaw'),
    'bus': ('access', 'vehicle', 'motor_vehicle', 'psv', 'bus'),
    'taxi': ('access', 'vehicle', 'motor_vehicle', 'psv', 'taxi'),
    'minibus': ('access', 'vehicle', 'motor_vehicle', 'psv', 'minibus'),
    'share_taxi': ('access', 'vehicle', 'motor_vehicle', 'psv', 'share_taxi'),
    'goods': ('access', 'vehicle', 'motor_vehicle', 'goods'),
    'hgv': ('access', 'vehicle', 'motor_vehicle', 'hgv'),
}
ACCESS_ROOTS = frozenset(key for chain in ACCESS_CHAINS.values() for key in chain)
PURPOSE_VALUES = frozenset(('private', 'destination', 'customers', 'delivery',
                            'agricultural', 'forestry', 'military', 'permit'))
AMBIGUOUS_MOTORCAR_SCOPE = frozenset(('auto_rickshaw', 'bus', 'taxi', 'minibus',
                                     'share_taxi', 'goods', 'hgv'))


def access_tags(tags):
    """Keep recognised access roots and all their qualifiers, without repair."""
    return {key: value for key, value in sorted(tags.items())
            if key.split(':', 1)[0] in ACCESS_ROOTS}


def resolve(tags, transport_class):
    """Return baseline tag evidence plus unresolved qualification, never a bool.

    Every qualifier on a relevant inheritance branch is retained for review.
    No conditional expression, lane allocation or directional rule is evaluated.
    Even when a more specific baseline exists, a qualified parent cannot silently
    disappear from the evidence. Unknown child values override known parents.
    """
    if transport_class not in ACCESS_CHAINS:
        raise ValueError('Unsupported OSM transport class: ' + str(transport_class))
    chain = ACCESS_CHAINS[transport_class]
    candidates = [dict(key=key, value=tags[key]) for key in chain if key in tags]
    key = candidates[-1]['key'] if candidates else ''
    raw = candidates[-1]['value'] if candidates else ''
    value = raw.strip()
    if not key:
        baseline = 'not_tagged'
    elif value == 'yes':
        baseline = 'tagged_public_access'
    elif value == 'permissive':
        baseline = 'tagged_revocable_permission'
    elif value == 'designated' and key != 'access':
        baseline = 'tagged_designated_access'
    elif value == 'no':
        baseline = 'tagged_prohibition'
    elif value in PURPOSE_VALUES:
        baseline = 'requires_user_purpose_or_permission'
    elif value in ('dismount', 'use_sidepath') and key != 'access':
        baseline = 'requires_travel_behaviour_or_parallel_way'
    elif value == 'discouraged':
        baseline = 'tagged_access_discouraged'
    else:
        baseline = 'unrecognised_or_ambiguous_value'
    qualifiers = {k: v for k, v in access_tags(tags).items()
                  if ':' in k and k.split(':', 1)[0] in chain}
    warnings = []
    if transport_class in AMBIGUOUS_MOTORCAR_SCOPE and any(
            k == 'motorcar' or k.startswith('motorcar:') for k in tags):
        warnings.append('motorcar_scope_for_other_double_tracked_vehicles_requires_local_evidence')
    return dict(transport_class=transport_class, inheritance_chain=list(chain),
                baseline_source_key=key, baseline_raw_value=raw,
                baseline_interpretation=baseline, contributing_tags=candidates,
                qualified_tags=qualifiers, scope_warnings=warnings,
                resolution_status='qualified_or_scope_review_required' if qualifiers or warnings else baseline,
                simulation_permission_established=False)
