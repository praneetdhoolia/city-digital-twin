"""A train cannot teleport between candidate platforms at an intermediate stop."""
import pytest

from build.rail_path_candidates import CandidateRouter, graph_from_segments, orientations, shortest_path


def graph(edges, tags=None, screened=True):
    rows = [dict(osm_way_id=i, segment_index_zero_based=0, from_osm_node_id=a,
                 to_osm_node_id=b, length_geodesic_m=length) for i, (a,b,length) in enumerate(edges)]
    return graph_from_segments(rows, {i: (tags or {}).get(i,{}) for i in range(len(rows))}, screen_static_oneway=screened)


def test_platform_continuity_prevents_disconnected_independent_leg_choices():
    g = graph([(1,2,1),(3,4,1)])
    assert shortest_path(g,1,2) is not None and shortest_path(g,3,4) is not None
    assert CandidateRouter(g).through_stops([{1},{2,3},{4}]) is None


def test_joint_optimisation_chooses_continuous_longer_first_leg():
    g = graph([(1,2,1),(1,3,4),(2,4,20),(3,4,2)])
    result = CandidateRouter(g).through_stops([{1},{2,3},{4}])
    assert result['boarding_nodes']==(1,3,4)
    assert result['length_m']==6
    assert result['legs'][0][-1].end == result['legs'][1][0].start


@pytest.mark.parametrize('tag,forward', [('yes',True),('-1',False)])
def test_static_oneway_and_unscreened_counterfactual(tag,forward):
    g = graph([(1,2,1)],{0:{'oneway':tag}})
    a,b=(1,2) if forward else (2,1)
    assert shortest_path(g,a,b) is not None and shortest_path(g,b,a) is None
    loose=graph([(1,2,1)],{0:{'oneway':tag}},screened=False)
    assert shortest_path(loose,b,a)[1][0].direction_status=='against_explicit_oneway'


def test_unknown_conditional_and_preferred_direction_are_not_static_permissions():
    for tags in ({},{'oneway':'reversible'},{'oneway':'yes','oneway:conditional':'no @ (night)'},
                 {'railway:preferred_direction':'forward'}):
        options=orientations(tags,screen_static_oneway=True)
        assert len(options)==2 and all('unresolved' in status for _,status in options)


def test_zero_length_cycles_and_equal_paths_are_deterministic():
    g=graph([(1,2,0),(2,1,0),(2,3,1),(1,3,1)])
    a=CandidateRouter(g).through_stops([{2,1},{3}])
    b=CandidateRouter(dict(reversed(list(g.items())))).through_stops([{1,2},{3}])
    assert a==b and a['length_m']==1
    assert shortest_path(g,1,1)==(0.0,())


def test_missing_boarding_identity_and_invalid_lengths_are_refused():
    router=CandidateRouter(graph([(1,2,1)]))
    assert router.through_stops([{1},set(),{2}]) is None
    assert router.through_stops([{999},{2}]) is None
    for bad in (-1,float('nan'),float('inf')):
        with pytest.raises(ValueError,match='finite and nonnegative'):
            graph([(1,2,bad)])
