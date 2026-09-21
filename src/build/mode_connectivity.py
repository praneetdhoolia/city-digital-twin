"""Directed connectivity for choosing mutually reachable activity links."""


def largest_strong_component(edges):
    forward, reverse = {}, {}
    for origin, destination in edges:
        forward.setdefault(origin, []).append(destination)
        reverse.setdefault(destination, []).append(origin)
    seen, order = set(), []
    for start in forward:
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, iter(forward.get(start, ())))]
        while stack:
            node, neighbours = stack[-1]
            for neighbour in neighbours:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append((neighbour, iter(forward.get(neighbour, ()))))
                    break
            else:
                order.append(node)
                stack.pop()
    visited, largest = set(), set()
    for start in reversed(order):
        if start in visited:
            continue
        component, stack = {start}, [start]
        visited.add(start)
        while stack:
            for neighbour in reverse.get(stack.pop(), ()):
                if neighbour not in visited:
                    visited.add(neighbour)
                    component.add(neighbour)
                    stack.append(neighbour)
        if len(component) > len(largest):
            largest = component
    return largest
