"""Deterministic geometry witnesses through ordered boarding candidates.

These paths are not operating permissions. A static-oneway screen is optional;
unknown/conditional directions remain flagged, and preferred direction alone is
not a prohibition (OSM Key:railway:preferred_direction).
"""
from collections import defaultdict
from dataclasses import dataclass
import heapq
import math


@dataclass(frozen=True)
class Arc:
    start: int
    end: int
    way: int
    segment: int
    forward: bool
    length_m: float
    direction_status: str


def orientations(tags, *, screen_static_oneway):
    raw = tags.get('oneway', '').strip()
    qualified = any(k.startswith('oneway:') for k in tags)
    if qualified:
        return [(True, 'qualified_direction_unresolved'), (False, 'qualified_direction_unresolved')]
    if raw in ('yes', '1', 'true'):
        return [(True, 'explicit_oneway')] if screen_static_oneway else [(True, 'explicit_oneway'), (False, 'against_explicit_oneway')]
    if raw == '-1':
        return [(False, 'explicit_oneway')] if screen_static_oneway else [(True, 'against_explicit_oneway'), (False, 'explicit_oneway')]
    if raw in ('no', '0', 'false'):
        return [(True, 'explicit_two_way'), (False, 'explicit_two_way')]
    status = 'missing_direction_unresolved' if not raw else 'nonstatic_or_unknown_direction_unresolved'
    return [(True, status), (False, status)]


def graph_from_segments(segments, way_tags, *, screen_static_oneway):
    """The caller selects mode and lifecycle; every supplied segment is retained."""
    graph = defaultdict(list)
    identities = set()
    for row in segments:
        way, segment = int(row['osm_way_id']), int(row['segment_index_zero_based'])
        if (way, segment) in identities:
            raise ValueError('Repeated native segment identity')
        identities.add((way, segment))
        start, end = int(row['from_osm_node_id']), int(row['to_osm_node_id'])
        length = float(row['length_geodesic_m'])
        if not math.isfinite(length) or length < 0:
            raise ValueError('Path lengths must be finite and nonnegative')
        graph.setdefault(start, [])
        graph.setdefault(end, [])
        for forward, status in orientations(way_tags[way], screen_static_oneway=screen_static_oneway):
            a, b = (start, end) if forward else (end, start)
            graph[a].append(Arc(a, b, way, segment, forward, length, status))
    return {node: sorted(arcs, key=lambda a: (a.end, a.way, a.segment, a.forward)) for node, arcs in sorted(graph.items())}


def shortest_path(graph, start, end):
    if start not in graph or end not in graph:
        return None
    queue, best, previous, settled = [(0.0, start)], {start: 0.0}, {}, set()
    while queue:
        distance, node = heapq.heappop(queue)
        if node in settled:
            continue
        settled.add(node)
        if node == end:
            path = []
            while node != start:
                arc = previous[node]
                path.append(arc)
                node = arc.start
            path.reverse()
            return math.fsum(a.length_m for a in path), tuple(path)
        for arc in graph[node]:
            candidate = distance + arc.length_m
            if arc.end not in settled and candidate < best.get(arc.end, math.inf):
                best[arc.end] = candidate
                previous[arc.end] = arc
                heapq.heappush(queue, (candidate, arc.end))
    return None


class CandidateRouter:
    def __init__(self, graph):
        self.graph = graph
        self.paths = {}

    def path(self, start, end):
        key = (start, end)
        if key not in self.paths:
            self.paths[key] = shortest_path(self.graph, start, end)
        return self.paths[key]

    def through_stops(self, candidates):
        """Choose one common arrival/departure node at every intermediate stop."""
        if not candidates or any(not nodes for nodes in candidates):
            return None
        costs = {node: 0.0 for node in sorted(set(candidates[0])) if node in self.graph}
        layers = []
        for targets in candidates[1:]:
            following, previous = {}, {}
            for end in sorted(set(targets)):
                options = []
                for start, cost in sorted(costs.items()):
                    path = self.path(start, end)
                    if path is not None:
                        options.append((cost + path[0], start))
                if options:
                    following[end], previous[end] = min(options)
            if not following:
                return None
            costs = following
            layers.append(previous)
        if not costs:
            return None
        end = min(costs, key=lambda n: (costs[n], n))
        nodes = [end]
        for previous in reversed(layers):
            nodes.append(previous[nodes[-1]])
        nodes.reverse()
        legs = tuple(self.path(a, b)[1] for a, b in zip(nodes, nodes[1:]))
        return dict(boarding_nodes=tuple(nodes), legs=legs,
                    length_m=math.fsum(a.length_m for leg in legs for a in leg))
