"""Geometry reduction must preserve native segments and all protected controls."""
from itertools import product

import pytest

from build.protected_way_segments import partition, protected_nodes


def test_tagged_controls_are_kept_while_untagged_shape_nodes_can_be_internal():
    ways = {10: [1, 2, 3, 4, 5, 6]}
    retained, absent = protected_nodes(ways, {2, 3, 4}, {})
    assert set(retained) == {1, 2, 3, 4, 6}
    assert partition(ways[10], retained) == [(0, 1), (1, 2), (2, 3), (3, 5)]
    assert absent == {}


def test_shared_way_nodes_and_cross_layer_anchors_split_without_new_connections():
    ways = {10: [1, 2, 3, 4], 11: [5, 3, 6], 12: [7, 8, 9]}
    retained, absent = protected_nodes(ways, set(), {'rail_layer': [2, 999]})
    assert 'shared_between_ways' in retained[3]
    assert 'rail_layer' in retained[2]
    assert absent == {'rail_layer': [999]}
    assert 8 not in retained and 999 not in retained
    assert partition(ways[10], retained) == [(0, 1), (1, 2), (2, 3)]


def test_repeat_visits_and_closed_chains_keep_the_original_walk():
    refs = [1, 2, 3, 4, 2, 5]
    retained, _ = protected_nodes({10: refs}, set(), {})
    assert 'repeated_within_way' in retained[2]
    assert any('closed_chain_anchor' in reasons for reasons in retained.values())
    spans = partition(refs, retained)
    expanded = [(refs[i], refs[i + 1]) for start, end in spans for i in range(start, end)]
    assert expanded == list(zip(refs, refs[1:]))
    assert all(refs[start] != refs[end] for start, end in spans)


def test_zero_length_native_adjacency_is_not_dropped():
    refs = [1, 1, 2]
    retained, _ = protected_nodes({10: refs}, set(), {})
    assert partition(refs, retained) == [(0, 1), (1, 2)]


def test_all_short_repeated_paths_keep_every_native_edge_once():
    for refs in product(range(3), repeat=5):
        retained, _ = protected_nodes({10: refs}, {1}, {'fixture_control': [2]})
        spans = partition(refs, retained)
        assert [i for start, end in spans for i in range(start, end)] == list(range(len(refs) - 1))
        for start, end in spans:
            assert not set(refs[start + 1:end]) & retained.keys()
            assert start < end


def test_order_of_ways_and_anchor_sets_does_not_change_retention():
    ways = {20: [4, 3, 5], 10: [1, 2, 3]}
    expected = protected_nodes(ways, {2, 4}, {'signal': {5, 99}})
    assert expected == protected_nodes(dict(reversed(list(ways.items()))), [4, 2], {'signal': [99, 5]})


def test_short_way_is_refused():
    with pytest.raises(ValueError, match='at least two'):
        protected_nodes({10: [1]}, set(), {})
    with pytest.raises(ValueError, match='at least two'):
        partition([], set())
