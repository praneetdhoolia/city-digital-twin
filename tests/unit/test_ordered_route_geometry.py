"""Route members must not gain invented junctions or replacement platforms."""
from itertools import product

import pytest

from build.ordered_route_geometry import locate_ordered_stops, match_ordered_candidates, orient_ordered_ways, shared_boarding_joins


def test_reversed_native_way_is_oriented_by_shared_endpoint():
    result = orient_ordered_ways([(1, 2, 3), (5, 4, 3), (5, 6)])
    assert result['orientations'] == (True, False, True)
    assert result['nodes'] == (1, 2, 3, 4, 5, 6)


def test_internal_intersection_does_not_repair_member_order():
    result = orient_ordered_ways([(1, 2, 3), (4, 2, 5)])
    assert result['status'] == 'disconnected_ordered_members'
    assert result['first_disconnected_way_index'] == 1
    assert result['nodes'] == ()


def test_loop_ambiguity_is_counted_without_arbitrary_orientation():
    result = orient_ordered_ways([(0, 1)] + [(1, 2, 1)] * 40 + [(1, 3)])
    assert result['orientation_count'] == 2 ** 40
    assert result['status'] == 'ambiguous_way_orientation'
    assert result['nodes'] == ()


def test_repeated_member_preserves_reversal_and_both_stop_visits():
    result = orient_ordered_ways([(0, 1), (1, 2), (1, 2), (1, 3)])
    assert result['nodes'] == (0, 1, 2, 1, 3)
    assert [r['node_index'] for r in locate_ordered_stops(result['nodes'], [1, 2, 1])] == [1, 2, 3]


def test_absent_platform_and_out_of_order_stop_remain_unresolved():
    rows = locate_ordered_stops((1, 2, 3, 4), [1, 99, 3, 2, 4])
    assert [r['status'] for r in rows] == ['present_in_order', 'absent_from_way_chain',
        'present_in_order', 'out_of_order', 'present_in_order']
    assert rows[1]['node_index'] is None and rows[3]['node_index'] is None


def test_unanchored_single_way_is_ambiguous_and_invalid_way_rejected():
    assert orient_ordered_ways([(1, 2, 3)])['status'] == 'ambiguous_way_orientation'
    assert orient_ordered_ways([])['status'] == 'no_way_members'
    with pytest.raises(ValueError):
        orient_ordered_ways([(1,)])


def test_complete_sequence_prunes_locally_plausible_platform():
    result = match_ordered_candidates([1, 2, 3, 4], [{1, 3}, {2}, {4}])
    assert result['assignment_count'] == 1
    assert result['candidate_positions'][0] == (0, 2)
    assert result['viable_positions'] == ((0,), (1,), (3,))
    assert result['unique_positions'] == (0, 1, 3)


def test_ambiguous_platform_assignments_are_preserved_without_selection():
    result = match_ordered_candidates([1, 2, 3, 4, 5], [{1}, {2, 3}, {4, 5}])
    assert result['assignment_count'] == 4
    assert result['viable_positions'] == ((0,), (1, 2), (3, 4))
    assert result['unique_positions'] == ()
    assert result == match_ordered_candidates([1, 2, 3, 4, 5], [[1], [3, 2], [5, 4]])


def test_boarding_identity_cannot_be_reused_without_a_later_visit():
    assert match_ordered_candidates([1, 2, 3], [{2}, {2}])['status'] == 'boarding_order_conflict'
    result = match_ordered_candidates([1, 2, 3, 2, 4], [{2}, {3}, {2}])
    assert result['unique_positions'] == (1, 2, 3)


def test_missing_node_is_distinct_from_reversed_order():
    result = match_ordered_candidates([1, 2, 3], [{1}, {99}, {3}])
    assert result['missing_stop_indices'] == (1,)
    assert result['status'] == 'boarding_nodes_absent_from_chain'
    assert match_ordered_candidates([1, 2, 3], [{3}, {1}])['status'] == 'boarding_order_conflict'
    with pytest.raises(ValueError):
        match_ordered_candidates([1, 2, 3], [])


def test_assignment_counts_and_viable_positions_match_exhaustive_loop_enumeration():
    nodes = (1, 2, 3, 2)
    subsets = [set(n for n, selected in zip((1, 2, 3), flags) if selected)
               for flags in product((False, True), repeat=3)]
    for candidates in product(subsets, repeat=3):
        exact = [positions for positions in product(range(len(nodes)), repeat=3)
                 if positions[0] < positions[1] < positions[2]
                 and all(nodes[p] in allowed for p, allowed in zip(positions, candidates))]
        result = match_ordered_candidates(nodes, candidates)
        assert result['assignment_count'] == len(exact)
        assert result['viable_positions'] == tuple(tuple(sorted({p[i] for p in exact})) for i in range(3))
        assert result['unique_positions'] == (exact[0] if len(exact) == 1 else ())


def test_composite_join_requires_the_same_boarding_node():
    assert shared_boarding_joins([1, 2], [3, 4], [{1}, {2, 3}], [{2, 3}, {4}]) == []
    result = shared_boarding_joins([1, 2, 3], [2, 4, 5], [{1}, {2}], [{2}, {5}])
    assert len(result) == 1 and result[0]['join_node_id'] == 2
    assert result[0]['left_unique_positions'] == (0, 1)
    assert result[0]['right_unique_positions'] == (0, 2)


def test_composite_join_rejects_wrong_stop_order_on_either_side():
    assert shared_boarding_joins([2, 1], [2, 3], [{1}, {2}], [{2}, {3}]) == []
    assert shared_boarding_joins([1, 2], [3, 2], [{1}, {2}], [{2}, {3}]) == []


def test_repeated_shared_node_visits_remain_distinct_joins():
    result = shared_boarding_joins([1, 2, 3, 2], [2, 4], [{1}, {2}], [{2}, {4}])
    assert [r['left_join_position'] for r in result] == [1, 3]
    assert all(r['assignment_count'] == 1 for r in result)


def test_composite_ambiguity_is_counted_without_platform_selection():
    result = shared_boarding_joins([1, 3, 2], [2, 4, 5], [{1, 3}, {2}], [{2}, {4, 5}])
    assert len(result) == 1 and result[0]['assignment_count'] == 4
    assert result[0]['left_unique_positions'] == () and result[0]['right_unique_positions'] == ()
    with pytest.raises(ValueError):
        shared_boarding_joins([1], [1, 2], [{1}], [{1}, {2}])
