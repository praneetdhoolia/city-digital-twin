"""Check ordered native ways without repairing, snapping or rerouting them.

PTv2 lists ways in traversal order. Connectivity determines orientation where
unique; direction permissions and current service applicability are separate.
"""


def orient_ordered_ways(way_nodes):
    """Return a unique full-way chain, or a diagnostic preserving ambiguity.

    States count orientation histories by endpoint rather than enumerating an
    exponential number of loop orientations. A witness is exported only if the
    entire chain has exactly one history. Shared internal nodes are not silently
    substituted for the endpoints prescribed by the ordered member sequence.
    """
    sequences = [tuple(nodes) for nodes in way_nodes]
    if not sequences:
        return dict(status='no_way_members', orientation_count=0, orientations=(), nodes=())
    if any(len(nodes) < 2 for nodes in sequences):
        raise ValueError('Every native way needs at least two node references')
    states = {None: (1, ())}
    for index, nodes in enumerate(sequences):
        next_states = {}
        for last, (count, history) in states.items():
            for forward, ordered in ((True, nodes), (False, nodes[::-1])):
                if last is not None and last != ordered[0]:
                    continue
                endpoint = ordered[-1]
                old_count, old_history = next_states.get(endpoint, (0, ()))
                next_states[endpoint] = (old_count + count,
                    old_history if old_count else history + (forward,))
        if not next_states:
            return dict(status='disconnected_ordered_members', orientation_count=0,
                        first_disconnected_way_index=index, orientations=(), nodes=())
        states = next_states
    count = sum(item[0] for item in states.values())
    if count != 1:
        return dict(status='ambiguous_way_orientation', orientation_count=count, orientations=(), nodes=())
    history = next(iter(states.values()))[1]
    nodes = []
    for sequence, forward in zip(sequences, history):
        oriented = sequence if forward else sequence[::-1]
        nodes.extend(oriented if not nodes else oriented[1:])
    return dict(status='unique_ordered_way_chain', orientation_count=count,
                orientations=history, nodes=tuple(nodes))


def locate_ordered_stops(nodes, stop_nodes):
    """Keep absent and out-of-order stops distinct; never substitute a stop.

    The earliest available occurrence makes subsequence matching deterministic.
    A repeated stop needs a later occurrence in the chain. Positions are indexes
    into the concatenated native node sequence, not distances or station IDs.
    """
    nodes = tuple(nodes)
    last = -1
    out = []
    for stop in stop_nodes:
        try:
            position = nodes.index(stop, last + 1)
        except ValueError:
            out.append(dict(node_id=stop, node_index=None,
                            status='out_of_order' if stop in nodes else 'absent_from_way_chain'))
        else:
            out.append(dict(node_id=stop, node_index=position, status='present_in_order'))
            last = position
    return out


def match_ordered_candidates(nodes, candidate_nodes):
    """Count all strictly ordered boarding assignments on one fixed chain.

    Retain every position belonging to a complete assignment. Prefix/suffix
    counts prune locally plausible platforms that cannot fit the whole trip.
    Ambiguous assignments are counted, never resolved by nearest distance or
    arbitrary iteration order. Only a unique assignment exports positions.
    """
    nodes = tuple(nodes)
    candidate_sets = [set(candidates) for candidates in candidate_nodes]
    choices = [tuple(i for i, node in enumerate(nodes) if node in candidates)
               for candidates in candidate_sets]
    if not choices:
        raise ValueError('At least one boarding stop is required')
    forward = []
    previous = {-1: 1}
    for options in choices:
        current = {position: sum(count for before, count in previous.items() if before < position)
                   for position in options}
        forward.append(current)
        previous = current
    total = sum(previous.values())
    backward = [{} for _ in choices]
    following = {len(nodes): 1}
    for index in range(len(choices) - 1, -1, -1):
        current = {position: sum(count for after, count in following.items() if after > position)
                   for position in choices[index]}
        backward[index] = current
        following = current
    viable = tuple(tuple(p for p in options if forward[i][p] and backward[i][p])
                   for i, options in enumerate(choices))
    missing = tuple(i for i, options in enumerate(choices) if not options)
    return dict(assignment_count=total, candidate_positions=tuple(choices), viable_positions=viable,
                unique_positions=tuple(options[0] for options in viable) if total == 1 else (),
                missing_stop_indices=missing,
                status='unique_ordered_boarding_assignment' if total == 1 else
                       'ambiguous_ordered_boarding_assignments' if total else
                       'boarding_nodes_absent_from_chain' if missing else 'boarding_order_conflict')


def shared_boarding_joins(left_nodes, right_nodes, left_candidates, right_candidates):
    """Join two ordered stop sequences only at an identical native boarding node.

    Both halves must contain a leg. Repeated visits to the same native node are
    distinct join positions. All complete assignments through each join are
    counted; ambiguous halves retain their counts and export no chosen positions.
    No coordinate proximity, platform transfer or operating permission is inferred.
    """
    left_nodes, right_nodes = tuple(left_nodes), tuple(right_nodes)
    left_candidates = tuple(set(nodes) for nodes in left_candidates)
    right_candidates = tuple(set(nodes) for nodes in right_candidates)
    if len(left_candidates) < 2 or len(right_candidates) < 2:
        raise ValueError('A composite route needs a nonempty leg on each side of its join')
    left = match_ordered_candidates(left_nodes, left_candidates)
    right = match_ordered_candidates(right_nodes, right_candidates)
    if not left['assignment_count'] or not right['assignment_count']:
        return []
    joins = []
    for a in left['viable_positions'][-1]:
        for b in right['viable_positions'][0]:
            if left_nodes[a] != right_nodes[b]:
                continue
            left_positions = list(left['candidate_positions'])
            right_positions = list(right['candidate_positions'])
            left_positions[-1], right_positions[0] = (a,), (b,)
            before = match_ordered_candidates(range(len(left_nodes)), left_positions)
            after = match_ordered_candidates(range(len(right_nodes)), right_positions)
            joins.append(dict(join_node_id=left_nodes[a], left_join_position=a, right_join_position=b,
                assignment_count=before['assignment_count'] * after['assignment_count'],
                left_assignment_count=before['assignment_count'], right_assignment_count=after['assignment_count'],
                left_unique_positions=before['unique_positions'], right_unique_positions=after['unique_positions']))
    return joins
