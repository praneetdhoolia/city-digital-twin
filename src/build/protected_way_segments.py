"""Partition native ways without losing selected nodes or adjacent segments.

This constructs geometry chains, not operating MATSim links. It makes no claim
that queue dynamics remain equivalent after combining segments.
"""
from collections import Counter, defaultdict


def protected_nodes(ways, tagged_nodes, anchors):
    """Retain endpoints, shared/repeated nodes, every tagged node and anchors.

    `ways` maps native way IDs to ordered native node IDs. `anchors` maps a
    caller's evidence reason to node IDs; absent anchors are reported separately.
    Source tags are never interpreted as permission to discard a control.
    """
    reasons = defaultdict(set)
    owners = Counter()
    for identity, refs in ways.items():
        if len(refs) < 2:
            raise ValueError('Way needs at least two native nodes: ' + str(identity))
        reasons[refs[0]].add('way_endpoint')
        reasons[refs[-1]].add('way_endpoint')
        counts = Counter(refs)
        owners.update(counts.keys())
        for node, count in counts.items():
            if count > 1:
                reasons[node].add('repeated_within_way')
    for node, count in owners.items():
        if count > 1:
            reasons[node].add('shared_between_ways')
    for node in tagged_nodes:
        if node in owners:
            reasons[node].add('source_node_has_tags')
    absent = {}
    for reason, nodes in sorted(anchors.items()):
        if not reason or not isinstance(reason, str):
            raise ValueError('Anchor evidence needs a nonempty reason')
        missing = set()
        for node in nodes:
            if node in owners:
                reasons[node].add(reason)
            else:
                missing.add(node)
        absent[reason] = sorted(missing)
    # A closed chain with only one retained identity would become a self-loop.
    # Keep an existing interior node so positive geometry is not represented as
    # a zero-displacement link. Never invent a node or discard the closed path.
    initial = set(reasons)
    for refs in ways.values():
        for start, end in partition(refs, initial):
            if refs[start] == refs[end]:
                interior = next((node for node in refs[start + 1:end] if node != refs[start]), None)
                if interior is not None:
                    reasons[interior].add('closed_chain_anchor')
    return {node: sorted(value) for node, value in sorted(reasons.items())}, absent


def partition(refs, protected):
    """Return contiguous native index intervals, each covering edges [start,end).

    All occurrences of a retained node split the chain. Endpoint identities are
    mandatory even if the caller's protected set omitted them. Repeated or
    coincident source nodes remain represented rather than removed as noise.
    """
    if len(refs) < 2:
        raise ValueError('Way needs at least two native nodes')
    start = 0
    spans = []
    for end in range(1, len(refs)):
        if refs[end] in protected or end == len(refs) - 1:
            spans.append((start, end))
            start = end
    return spans
