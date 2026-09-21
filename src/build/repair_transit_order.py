"""Repair mapped stop-order defects using connected paths on the same network."""
import gzip
import heapq
import math
from collections import defaultdict
from lxml import etree


def shortest_path(edges, origin, destination):
    queue = [(0.0, origin)]
    distances = {origin: 0.0}
    previous = {}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != distances[node]:
            continue
        if node == destination:
            path = []
            while node != origin:
                node, link = previous[node]
                path.append(link)
            return path[::-1]
        for target, length, link in edges.get(node, ()):
            candidate = cost + length
            if candidate < distances.get(target, float('inf')):
                distances[target] = candidate
                previous[target] = (node, link)
                heapq.heappush(queue, (candidate, target))
    raise ValueError(f'No connected transit repair path: {origin} -> {destination}')


def repair_schedule(source, network, destination, timing=None):
    with gzip.open(source, 'rb') as stream:
        tree = etree.parse(stream)
    facilities = {s.get('id'): s.get('linkRefId')
                  for s in tree.findall('transitStops/stopFacility')}
    defects = []
    for route in tree.findall('transitLine/transitRoute'):
        links = [l.get('refId') for l in route.findall('route/link')]
        position = 0
        for stop in route.findall('routeProfile/stop'):
            link = facilities[stop.get('refId')]
            try:
                position = links.index(link, position)
            except ValueError:
                defects.append(route)
                break
    audit = []
    if defects or timing:
        with gzip.open(network, 'rb') as stream:
            ntree = etree.parse(stream)
        attributes = {l.get('id'): dict(l.attrib) for l in ntree.findall('links/link')}
        del ntree
    if defects:
        for route in defects:
            mode = route.findtext('transportMode')
            edges = defaultdict(list)
            for lid, link in sorted(attributes.items()):
                if mode in link['modes'].split(','):
                    edges[link['from']].append((link['to'], float(link['length']), lid))
            element = route.find('route')
            links = [l.get('refId') for l in element]
            position = 0
            for stop in route.findall('routeProfile/stop'):
                target = facilities[stop.get('refId')]
                try:
                    position = links.index(target, position)
                except ValueError:
                    origin = attributes[links[position]]['to']
                    before = shortest_path(edges, origin, attributes[target]['from'])
                    after = shortest_path(edges, attributes[target]['to'], origin)
                    added = before + [target] + after
                    links[position + 1:position + 1] = added
                    audit.append(dict(route=route.get('id'), stop=stop.get('refId'),
                                      inserted_links=added,
                                      added_distance_m=sum(float(attributes[l]['length']) for l in added)))
                    position += len(before) + 1
            for child in list(element):
                element.remove(child)
            for link in links:
                etree.SubElement(element, 'link', refId=link)
            for left, right in zip(links, links[1:]):
                if attributes[left]['to'] != attributes[right]['from']:
                    raise ValueError('Transit repair produced disconnected links')
    timing_audit = []
    if timing:
        for route in tree.findall('transitLine/transitRoute'):
            mode = route.findtext('transportMode')
            speed = timing['speed_ms'][mode]
            dwell = timing['dwell_s'][mode]
            links = [l.get('refId') for l in route.findall('route/link')]
            elapsed = [0.0]
            for lid in links:
                link = attributes[lid]
                elapsed.append(elapsed[-1] + float(link['length']) /
                               min(speed, float(link['freespeed'])))
            stops = route.findall('routeProfile/stop')
            position, previous_position, previous_departure = 0, 0, 0
            changed = 0
            for index, stop in enumerate(stops):
                position = links.index(facilities[stop.get('refId')], position)
                arrival = parse_seconds(stop.get('arrivalOffset', '00:00:00'))
                departure = parse_seconds(stop.get('departureOffset', '00:00:00'))
                minimum = previous_departure + elapsed[position + 1] - elapsed[previous_position + 1]
                new_arrival = max(arrival, math.ceil(minimum)) if index else arrival
                new_departure = max(departure, new_arrival + (dwell if 0 < index < len(stops) - 1 else 0))
                if (new_arrival, new_departure) != (arrival, departure):
                    changed += 1
                stop.set('arrivalOffset', format_seconds(new_arrival))
                stop.set('departureOffset', format_seconds(new_departure))
                previous_position, previous_departure = position, new_departure
            if changed:
                timing_audit.append(dict(route=route.get('id'), adjusted_stops=changed,
                                         final_arrival_s=new_arrival))
    with open(destination, 'wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            tree.write(stream, encoding='UTF-8', xml_declaration=True)
    return dict(repaired_routes=len(defects), repairs=audit,
                timing_adjustments=timing_audit)


def parse_seconds(value):
    hours, minutes, seconds = map(float, value.split(':'))
    return hours * 3600 + minutes * 60 + seconds


def format_seconds(value):
    value = math.ceil(value)
    return f'{value // 3600:02d}:{value % 3600 // 60:02d}:{value % 60:02d}'
