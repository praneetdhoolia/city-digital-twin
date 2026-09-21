from build.osm_turn_evidence import inspect_relation


def members():
    return [dict(type='way', ref=10, role='from'),
            dict(type='node', ref=2, role='via'),
            dict(type='way', ref=20, role='to')]


def check(tags=None, entries=None, ways=None):
    return inspect_relation(tags or {'type': 'restriction', 'restriction': 'no_right_turn'},
                            members() if entries is None else entries,
                            {10: [1, 2], 20: [2, 3]} if ways is None else ways)


def test_valid_geometry_does_not_establish_permission():
    result = check()
    assert result['structural_issues'] == []
    assert not result['simulation_permission_established']
    assert all(x['via_at_way_endpoint'] for x in result['junction_checks'])


def test_via_only_relation_cannot_be_repaired_by_geometry():
    assert check(entries=[members()[1]])['structural_issues'] == ['missing_from', 'missing_to']


def test_grade_separated_or_missing_way_is_flagged():
    result = check(ways={10: [1, 4]})
    assert result['missing_road_way_ids'] == [20]
    assert 'via_node_absent_from_from_way' in result['structural_issues']


def test_condition_and_exceptions_are_not_flattened():
    result = check(tags={'type': 'restriction', 'restriction:bus:conditional':
                        'no_right_turn @ (Mo-Fr 07:00-09:00)', 'except': 'bicycle; psv'})
    assert result['exception_tokens'] == ['bicycle', 'psv']
    assert len(result['scope_review']) == 2
    assert result['restriction_tags']['restriction:bus:conditional'].endswith('09:00)')


def test_via_way_is_not_claimed_connected():
    entries = members(); entries[1] = dict(type='way', ref=30, role='via')
    result = check(entries=entries, ways={10: [1, 2], 20: [4, 5], 30: [2, 3]})
    assert result['junction_checks'] == []
    assert result['via_way_chain']['status'] == 'disconnected_ordered_members'
    assert 'via_way_geometry_disconnected_ordered_members' in result['scope_review']


def test_via_chain_uses_native_endpoints_without_granting_direction_permission():
    entries = members(); entries[1] = dict(type='way', ref=30, role='via')
    result = check(entries=entries, ways={10: [1, 2], 20: [4, 5], 30: [4, 3, 2]})
    assert result['via_way_chain']['orientations'] == (True, False, True)
    assert result['via_way_chain']['nodes'] == (1, 2, 3, 4, 5)
    assert not result['simulation_permission_established']


def test_multiple_from_allowed_only_for_no_entry():
    entries = members() + [dict(type='way', ref=20, role='from')]
    assert 'multiple_from_requires_scope_review' in check(entries=entries)['structural_issues']
    assert check(tags={'type': 'restriction', 'restriction': 'no_entry'}, entries=entries)['structural_issues'] == []


def test_repeated_node_occurrences_remain_distinct():
    result = check(ways={10: [2, 1, 2], 20: [2, 3]})
    assert result['junction_checks'][0]['via_node_indices'] == [0, 2]


def test_unknown_rule_cannot_pass_scope_review():
    result = check(tags={'type': 'restriction', 'restriction': 'unrecognised'})
    assert result['scope_review'] == ['unrecognised_static_restriction_value']
