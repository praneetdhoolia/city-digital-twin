from build.mode_connectivity import largest_strong_component


def test_gate_network_excludes_one_way_dead_ends_and_isolated_components():
    edges = [('a', 'b'), ('b', 'c'), ('c', 'a'), ('c', 'dead'),
             ('x', 'y'), ('y', 'x')]
    assert largest_strong_component(edges) == {'a', 'b', 'c'}
    assert largest_strong_component([]) == set()


def test_component_selection_is_repeatable_with_equal_size_components():
    edges = [('a', 'b'), ('b', 'a'), ('x', 'y'), ('y', 'x')]
    assert largest_strong_component(edges) == largest_strong_component(iter(edges))
