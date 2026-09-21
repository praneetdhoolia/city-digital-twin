"""Describe native transport tags without treating mapper coverage as ground truth.

Numeric values are unit-normalised only when the entire value is understood.
Directional, conditional and mode-specific tags remain separate observations.
No untagged way receives a default, and no lane split or capacity is inferred.
"""
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import re

import numpy as np

from build.extract_osm_network import entities, fingerprint


NUMBER = r'\d+(?:\.\d+)?'
SPEED_KEYS = {'maxspeed', 'maxspeed:forward', 'maxspeed:backward'}
LANE_KEYS = {'lanes', 'lanes:forward', 'lanes:backward', 'lanes:both_ways'}
WIDTH_KEYS = {'width', 'width:carriageway'}
# Exact unit identities, not empirical parameters. International mile is
# 1,609,344 mm, nautical mile is 1,852 m, foot is 304.8 mm, inch is 25.4 mm.
UNIT_SCALES = {
    'km/h': {None: 1, 'km/h': 1, 'mph': 1609344 / 1000000, 'knots': 1852 / 1000},
    'm': {None: 1, 'm': 1, 'km': 1000, 'cm': 1 / 100, 'mm': 1 / 1000,
          'ft': 3048 / 10000, 'mi': 1609344 / 1000, 'in': 254 / 10000},
}
TAG_ROOTS = {
    'maxspeed', 'lanes', 'width', 'est_width', 'maxwidth', 'maxheight',
    'maxweight', 'maxaxleload', 'oneway', 'access', 'vehicle', 'motor_vehicle',
    'motorcar', 'motorcycle', 'moped', 'hgv', 'goods', 'bus', 'psv', 'taxi',
    'foot', 'bicycle', 'cycleway', 'sidewalk', 'surface', 'smoothness',
    'lane_markings', 'junction', 'tracktype', 'service', 'toll', 'bridge',
    'tunnel', 'layer', 'incline', 'lit', 'crossing', 'turn', 'change',
    'traffic_sign', 'source', 'check_date', 'survey', 'railway', 'route',
}


def normalise(key, raw):
    """Return (number, unit, status); never truncate ranges or symbolic values."""
    value = raw.strip()
    if key in SPEED_KEYS:
        unit = 'km/h'
        match = re.fullmatch('(' + NUMBER + r')(?:\s+(km/h|mph|knots))?', value)
        if match:
            factor = UNIT_SCALES[unit][match[2]]
            number = float(match[1]) * factor
        else:
            return None, unit, 'unresolved'
    elif key in LANE_KEYS:
        unit = 'lanes'
        if not re.fullmatch(r'\d+', value):
            return None, unit, 'unresolved'
        number = int(value)
        if key == 'lanes' and number == 0:
            return None, unit, 'unresolved'
    elif key in WIDTH_KEYS:
        unit = 'm'
        match = re.fullmatch('(' + NUMBER + r')(?:\s+(m|km|cm|mm|ft|mi))?', value)
        imperial = re.fullmatch(r'(\d+)\'(\d+(?:\.\d+)?)"', value)
        if match:
            factor = UNIT_SCALES[unit][match[2]]
            number = float(match[1]) * factor
        elif imperial and float(imperial[2]) < 12:
            number = (int(imperial[1]) * UNIT_SCALES[unit]['ft'] +
                      float(imperial[2]) * UNIT_SCALES[unit]['in'])
        else:
            return None, unit, 'unresolved'
        if number <= 0:
            return None, unit, 'unresolved'
    else:
        return None, '', 'retained_text'
    if not math.isfinite(number):
        return None, unit, 'unresolved'
    return number, unit, 'normalised'


def summarise(values):
    """Way-weighted descriptions only; split ways are not independent surveys."""
    return dict(n_tagged_ways=len(values), minimum=min(values), maximum=max(values),
                q25=float(np.percentile(values, 25)), median=float(np.median(values)),
                q75=float(np.percentile(values, 75)))


def audit(inputs):
    inputs = [Path(path) for path in inputs]
    before = [fingerprint(path) for path in inputs]
    seen, counts, classes = set(), Counter(), Counter()
    histogram = Counter()
    measurements = defaultdict(lambda: defaultdict(list))
    tag_coverage = defaultdict(Counter)
    for path in inputs:
        for element in entities(path):
            if element.tag != 'way':
                continue
            identity = element.get('id')
            if identity in seen:
                counts['duplicate_way_occurrences_skipped'] += 1
                continue
            seen.add(identity)
            tags = {tag.get('k'): tag.get('v', '') for tag in element.findall('tag')}
            if not any(key in tags for key in ('highway', 'railway')) and tags.get('route') != 'ferry':
                continue
            counts['transport_ways'] += 1
            if tags.get('area') == 'yes':
                counts['area_ways_excluded_from_linear_statistics'] += 1
                continue
            if len(element.findall('nd')) < 2:
                counts['short_ways_excluded_from_linear_statistics'] += 1
                continue
            # Keep compound classifications: no silent rail/highway priority.
            classification = '|'.join(key + '=' + tags[key] for key in
                                      ('highway', 'railway', 'route') if key in tags)
            classes[classification] += 1
            for key, raw in sorted(tags.items()):
                if key.split(':', 1)[0] not in TAG_ROOTS:
                    continue
                number, unit, status = normalise(key, raw)
                histogram[(classification, key, raw, number, unit, status)] += 1
                tag_coverage[classification][key] += 1
                if number is not None:
                    measurements[classification][key].append(number)
    after = [fingerprint(path) for path in inputs]
    if before != after:
        raise ValueError('An OSM source changed during tag measurement')
    rows = [dict(transport_class=key[0], tag=key[1], raw_value=key[2],
                 normalised_value=key[3], unit=key[4], status=key[5], way_count=count)
            for key, count in sorted(histogram.items(), key=lambda item: item[0][:3])]
    report = dict(
        source='derived', input_sha256=before, counts=dict(sorted(counts.items())),
        unique_source_ways=len(seen), linear_transport_ways=sum(classes.values()),
        histogram_rows=len(rows),
        by_class={key: dict(linear_ways=classes[key],
                           tag_coverage=dict(sorted(tag_coverage[key].items())),
                           numeric_tags={tag: summarise(values) for tag, values in
                                         sorted(measurements[key].items())})
                  for key in sorted(classes)},
        interpretation=[
            'Mapper-reported tags, not independently verified field measurements.',
            'Quantiles weight native ways equally; mapping splits affect this distribution.',
            'No missing value imputation or class default selection.',
            'Speed tags describe legal limits, not observed free-flow speeds.',
            'Lane totals are not halved; directional and shared lanes remain separate.',
            'Width includes the carriageway and may include cycle and parking lanes; no lane width inferred.',
            'Conditional and mode-specific tags are retained as text, not applied to a simulation.',
            'Tag coverage does not establish network access, connectivity or physical capacity.',
        ],
        tagging_references=[
            'https://wiki.openstreetmap.org/wiki/Key:maxspeed',
            'https://wiki.openstreetmap.org/wiki/Key:lanes',
            'https://wiki.openstreetmap.org/wiki/Key:width',
        ])
    return report, rows


def write(report, rows, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'transport_tag_values.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            'transport_class', 'tag', 'raw_value', 'normalised_value', 'unit', 'status', 'way_count'],
            lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    (directory / 'transport_tag_audit.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
