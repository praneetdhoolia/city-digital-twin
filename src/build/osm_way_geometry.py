"""Preserve native way/node geometry without inventing operating links.

OSM node identity, not coordinate proximity, defines junction membership. Areas,
inactive infrastructure and non-routing features remain labelled evidence.
No source direction, speed, gauge or service tag is converted into a default.
"""
from collections import Counter
import csv
import json
import math
import os
from pathlib import Path
import tempfile

from pyproj import CRS, Transformer
from build.extract_osm_network import entities, fingerprint


def serial(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def tags_of(element):
    tags = {}
    for tag in element.findall('tag'):
        key, value = tag.get('k'), tag.get('v')
        if key is None or value is None or key in tags:
            raise ValueError('Missing or repeated OSM tag key/value')
        tags[key] = value
    return tags


def collect(inputs, projected_crs, *, feature_key):
    """Read complete native geometries; reject conflicting copies and missing refs."""
    if feature_key not in ('highway', 'railway'):
        raise ValueError('Unsupported native geometry feature key')
    inputs = [Path(p) for p in inputs]
    if not inputs:
        raise ValueError('At least one native OSM input is required')
    target = CRS(projected_crs)
    if not target.is_projected or any(a.unit_conversion_factor != 1 for a in target.axis_info):
        raise ValueError('Geometry needs a projected CRS with metre axes')
    geographic = CRS('EPSG:4326')  # OSM coordinate standard, not a city parameter.
    transform = Transformer.from_crs(geographic, target, always_xy=True)
    geod = geographic.get_geod()
    hashes = [fingerprint(p) for p in inputs]
    ways, wanted = {}, set()
    duplicate_ways = duplicate_nodes = 0
    for path, digest in zip(inputs, hashes):
        seen_in_input = set()
        for element in entities(path):
            if element.tag != 'way':
                continue
            tags = tags_of(element)
            if not any(k == feature_key or k.endswith(':' + feature_key) for k in tags):
                continue
            identity = int(element.get('id'))
            if identity in seen_in_input:
                raise ValueError('Repeated ' + feature_key + ' way ID within one input: ' + str(identity))
            seen_in_input.add(identity)
            refs = [int(n.get('ref')) for n in element.findall('nd')]
            if len(refs) < 2:
                raise ValueError(feature_key + ' way has fewer than two node references: ' + str(identity))
            if identity in ways:
                existing = ways[identity]
                if existing['refs'] != refs or existing['tags'] != tags:
                    raise ValueError('Conflicting ' + feature_key + ' way copies: ' + str(identity))
                existing['hashes'].add(digest)
                duplicate_ways += 1
            else:
                ways[identity] = dict(refs=refs, tags=tags, hashes={digest})
            wanted.update(refs)
    if not ways:
        raise ValueError('No ' + feature_key + '-tagged native ways found')
    nodes = {}
    for path, digest in zip(inputs, hashes):
        seen_in_input = set()
        for element in entities(path):
            if element.tag != 'node' or int(element.get('id')) not in wanted:
                continue
            identity = int(element.get('id'))
            if identity in seen_in_input:
                raise ValueError('Repeated ' + feature_key + ' node ID within one input: ' + str(identity))
            seen_in_input.add(identity)
            lon, lat = float(element.get('lon')), float(element.get('lat'))
            if not math.isfinite(lon) or not math.isfinite(lat) or not -180 <= lon <= 180 or not -90 <= lat <= 90:
                raise ValueError('Invalid OSM geographic coordinate: ' + str(identity))
            tags = tags_of(element)
            if identity in nodes:
                existing = nodes[identity]
                if (existing['lon'], existing['lat'], existing['tags']) != (lon, lat, tags):
                    raise ValueError('Conflicting ' + feature_key + ' node copies: ' + str(identity))
                existing['hashes'].add(digest)
                duplicate_nodes += 1
            else:
                x, y = transform.transform(lon, lat, errcheck=True)
                if not all(map(math.isfinite, (x, y))):
                    raise ValueError('Non-finite projected coordinate')
                nodes[identity] = dict(lon=lon, lat=lat, x=x, y=y, tags=tags, hashes={digest})
    missing = wanted - nodes.keys()
    if missing:
        raise ValueError(feature_key + ' ways reference missing native nodes: ' + str(sorted(missing)))
    node_rows = [dict(osm_node_id=identity, longitude_deg=n['lon'], latitude_deg=n['lat'],
                      projected_x_m=n['x'], projected_y_m=n['y'], projected_crs=target.to_string(),
                      source_tags_json=serial(n['tags']), source_sha256_json=serial(sorted(n['hashes'])))
                 for identity, n in sorted(nodes.items())]
    way_rows, segment_rows = [], []
    for identity, way in sorted(ways.items()):
        refs, tags = way['refs'], way['tags']
        geometry_role = 'area_boundary' if tags.get('area') == 'yes' else 'native_way_geometry'
        projected_lengths, geodesic_lengths = [], []
        for index, (a, b) in enumerate(zip(refs, refs[1:])):
            na, nb = nodes[a], nodes[b]
            projected = math.hypot(nb['x']-na['x'], nb['y']-na['y'])
            _, _, geodesic = geod.inv(na['lon'], na['lat'], nb['lon'], nb['lat'])
            if not math.isfinite(geodesic) or geodesic < 0:
                raise ValueError('Invalid geodesic segment length')
            projected_lengths.append(projected)
            geodesic_lengths.append(geodesic)
            segment_rows.append(dict(osm_way_id=identity, segment_index_zero_based=index,
                                     from_osm_node_id=a, to_osm_node_id=b,
                                     length_projected_m=projected, length_geodesic_m=geodesic,
                                     **{feature_key + '_tag': tags.get(feature_key, '')}, geometry_role=geometry_role,
                                     geometry_status='zero_length_retained_for_review' if geodesic == 0 else 'nonzero',
                                     orientation='source_node_order_not_operating_direction'))
        way_rows.append(dict(osm_way_id=identity, **{feature_key + '_tag': tags.get(feature_key, '')},
                             geometry_role=geometry_role, node_count=len(refs), segment_count=len(refs)-1,
                             length_projected_m=math.fsum(projected_lengths), length_geodesic_m=math.fsum(geodesic_lengths),
                             ordered_node_ids_json=serial(refs), source_tags_json=serial(tags),
                             source_sha256_json=serial(sorted(way['hashes'])),
                             model_input_status='geometry_only_operating_access_direction_speed_and_capacity_unresolved'))
    if hashes != [fingerprint(p) for p in inputs]:
        raise ValueError('Native OSM input changed during geometry extraction')
    audit = dict(source='derived_native_osm_geometry', input_sha256=hashes, projected_crs=target.to_string(),
                 nodes=len(node_rows), ways=len(way_rows), segments=len(segment_rows),
                 identical_way_copies_deduplicated=duplicate_ways, identical_node_copies_deduplicated=duplicate_nodes,
                 **{'by_' + feature_key + '_tag': dict(sorted(Counter(r[feature_key + '_tag'] for r in way_rows).items()))},
                 by_geometry_role=dict(sorted(Counter(r['geometry_role'] for r in way_rows).items())),
                 zero_length_segments=sum(r['geometry_status'] != 'nonzero' for r in segment_rows),
                 limitations=[
                     'All railway-tagged ways are evidence; station outlines, platforms, inactive tracks and construction are not operating links.',
                     'Adjacent native node references are preserved without snapping, simplification, clipping or a minimum length.',
                     'Geodesic lengths use the OSM WGS84 ellipsoid; projected lengths use the supplied metre CRS. Neither includes vertical grade.',
                     'Source node order is not an operating direction. Missing directions, speeds, gauge and capacity remain unspecified.',
                     'Node and way tags retain signal, switch, level and service evidence without supplying a block or train-control model.',
                     'Only nodes referenced by retained ways are included; standalone railway features need their separate inventory.',
                 ])
    if feature_key == 'highway':
        audit['referenced_node_tags'] = {
            key: dict(sorted(Counter(n['tags'][key] for n in nodes.values() if key in n['tags']).items()))
            for key in ('barrier', 'highway', 'railway', 'crossing', 'access', 'locked')
        }
        audit['limitations'] = [
            'All highway-tagged ways are evidence; areas, inactive roads and construction are not declared operating links.',
            'Adjacent native node references are preserved without snapping, simplification, clipping or a minimum length.',
            'Geodesic lengths use the OSM WGS84 ellipsoid; projected lengths use the supplied metre CRS. Neither includes vertical grade.',
            'Source node order is not an operating direction. Missing access, lane allocation, speed and capacity remain unspecified.',
            'Node and way tags retain crossings, barriers, signals and level evidence without deciding passability or signal timing.',
            'Only nodes referenced by retained ways are included; standalone highway features need their separate inventory.',
        ]
    return node_rows, way_rows, segment_rows, audit


def build(inputs, output_dir, projected_crs, *, feature_key):
    """Publish validated tables, then their audit; failed collection changes no files."""
    nodes, ways, segments, audit = collect(inputs, projected_crs, feature_key=feature_key)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=feature_key + '_geometry_', dir=output_dir) as temporary:
        stage = Path(temporary)
        for name, rows in (('nodes.csv', nodes), ('ways.csv', ways), ('segments.csv', segments)):
            with (stage/name).open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
        (stage/'audit.json').write_text(json.dumps(audit, indent=2)+'\n', encoding='utf-8', newline='\n')
        for name in ('nodes.csv', 'ways.csv', 'segments.csv', 'audit.json'):
            os.replace(stage/name, output_dir/name)
    return audit
