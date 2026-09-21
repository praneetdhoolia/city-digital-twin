"""Check explicit turn-relation structure without inferring legal permissions."""
from build.ordered_route_geometry import orient_ordered_ways


def inspect_relation(tags, members, ways):
    """Return geometry checks and verbatim scope; never authorise a model turn.

    ``ways`` maps native way identities to ordered node identities. Via-way
    paths use ordered endpoint checks; touching a way is not sufficient to
    prove that a directed vehicle path exists.
    """
    issues = []
    groups = {role: [m for m in members if m['role'] == role]
              for role in ('from', 'via', 'to')}
    values = {k: v for k, v in tags.items()
              if k == 'restriction' or k.startswith('restriction:')}
    static_values = {v for k, v in values.items() if ':conditional' not in k}
    for role in ('from', 'to'):
        group = groups[role]
        if not group:
            issues.append('missing_' + role)
        if any(m['type'] != 'way' for m in group):
            issues.append(role + '_member_not_way')
        # Multiple sources/destinations are valid for no_entry/no_exit only.
        allowed = 'no_entry' if role == 'from' else 'no_exit'
        if len(group) > 1 and static_values != {allowed}:
            issues.append('multiple_' + role + '_requires_scope_review')
    via = groups['via']
    if not via:
        issues.append('missing_via')
    elif not (len(via) == 1 and via[0]['type'] == 'node') and not all(
            m['type'] == 'way' for m in via):
        issues.append('unsupported_via_member_structure')
    if any(m['role'] not in groups for m in members):
        issues.append('unrecognised_member_role')
    missing = sorted({m['ref'] for m in members
                      if m['type'] == 'way' and m['ref'] not in ways})
    if missing:
        issues.append('way_member_outside_road_geometry')
    junction_checks = []
    if len(via) == 1 and via[0]['type'] == 'node':
        node = via[0]['ref']
        for role in ('from', 'to'):
            for member in groups[role]:
                if member['type'] != 'way' or member['ref'] not in ways:
                    continue
                refs = ways[member['ref']]
                occurrences = [i for i, ref in enumerate(refs) if ref == node]
                junction_checks.append(dict(role=role, osm_way_id=member['ref'],
                    via_node_indices=occurrences,
                    via_at_way_endpoint=bool(refs) and node in (refs[0], refs[-1])))
                if not occurrences:
                    issues.append('via_node_absent_from_' + role + '_way')
    scope_review = []
    if not values:
        scope_review.append('missing_restriction_value')
    recognised = {'no_right_turn', 'no_left_turn', 'no_u_turn', 'no_straight_on',
                  'only_right_turn', 'only_left_turn', 'only_u_turn', 'only_straight_on',
                  'no_entry', 'no_exit'}
    if static_values - recognised:
        scope_review.append('unrecognised_static_restriction_value')
    if tags.get('type', '') != 'restriction':
        scope_review.append('legacy_or_unknown_relation_type')
    if any(k != 'restriction' for k in values):
        scope_review.append('qualified_restriction_requires_vehicle_or_condition_resolution')
    if 'except' in tags:
        scope_review.append('vehicle_exceptions_require_mode_hierarchy_resolution')
    if any(k in tags for k in ('day_on', 'day_off', 'hour_on', 'hour_off')):
        scope_review.append('legacy_time_condition')
    via_way_chain = None
    if via and all(m['type'] == 'way' for m in via):
        if not issues and len(groups['from']) == len(groups['to']) == 1:
            ordered = groups['from'] + via + groups['to']
            via_way_chain = orient_ordered_ways([ways[m['ref']] for m in ordered])
            via_way_chain['ordered_way_ids'] = [m['ref'] for m in ordered]
            if via_way_chain['orientation_count'] != 1:
                scope_review.append('via_way_geometry_' + via_way_chain['status'])
        else:
            scope_review.append('via_way_orientation_and_continuity_unresolved')
    return dict(structural_issues=sorted(set(issues)),
                restriction_tags=dict(sorted(values.items())),
                exception_tokens=[s.strip() for s in tags.get('except', '').split(';') if s.strip()],
                scope_review=scope_review, junction_checks=junction_checks,
                via_way_chain=via_way_chain,
                missing_road_way_ids=missing, model_turns_exported=0,
                simulation_permission_established=False)
