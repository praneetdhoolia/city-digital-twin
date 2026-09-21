"""Verify a bounded road-capacity experiment preserves its other physical inputs."""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import zip_longest
import json
import math
from pathlib import Path

from lxml import etree
import results_store


def fingerprint(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def network_rows(path):
    with gzip.open(path, 'rb') as stream:
        for event, element in etree.iterparse(stream, events=('start', 'end'),
                                             tag=('network', 'nodes', 'links', 'node', 'link')):
            if element.tag in ('network', 'nodes', 'links'):
                if event == 'start':
                    yield element.tag, dict(element.attrib), ()
                continue
            if event != 'end':
                continue
            children = tuple((child.get('name'), child.get('class'), child.text)
                             for child in element.findall('attributes/attribute'))
            yield element.tag, dict(element.attrib), children
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]


def compare(control, candidate, field):
    left, right = [Path(results_store.resolve_or_die(name)) for name in (control, candidate)]
    inputs = [json.loads((path / '_baseline_inputs.json').read_text(encoding='utf-8')) for path in (left, right)]
    if inputs[0] != inputs[1]:
        raise ValueError('Prepared source inputs differ; this is not a capacity-only experiment')
    snapshots = [json.loads((path / '_config.json').read_text(encoding='utf-8'))['values'] for path in (left, right)]
    changed_fields = {key for key in snapshots[0].keys() | snapshots[1].keys()
                      if snapshots[0].get(key) != snapshots[1].get(key)}
    if changed_fields != {field}:
        raise ValueError('Unexpected configuration differences: ' + str(sorted(changed_fields)))
    stable_files = {}
    for name in ('transitSchedule.xml.gz', 'vehicles.xml'):
        hashes = [fingerprint(path / name) for path in (left, right)]
        if hashes[0] != hashes[1]:
            raise ValueError('Prepared runtime file differs: ' + name)
        stable_files[name] = hashes[0]
    counts, capacity_changes = Counter(), Counter()
    factors_by_id = {}
    before_factors, after_factors = snapshots[0].get(field, {}), snapshots[1][field]
    for a, b in zip_longest(network_rows(left / 'network.xml.gz'), network_rows(right / 'network.xml.gz')):
        if a is None or b is None or a[0] != b[0] or a[2] != b[2]:
            raise ValueError('Network structure or source attributes differ')
        kind, before, children = a
        after = b[1]
        counts[kind] += 1
        if kind == 'link':
            old_capacity, new_capacity = float(before.pop('capacity')), float(after.pop('capacity'))
            tags = {name: value for name, _, value in children}
            highway = tags.get('osm:way:highway', '')
            identity = before['id']
            factor = after_factors.get(highway, 1) / before_factors.get(highway, 1)
            # Reverse active-mode links inherit their forward road's capacity.
            # This is the existing add_nonmotor_reverse_links naming contract.
            if not children and identity.startswith('nmr_'):
                factor = factors_by_id[identity.removeprefix('nmr_')]
            factors_by_id[identity] = factor
            if not math.isclose(new_capacity, old_capacity * factor):
                raise ValueError('Capacity does not match declared factor: ' + identity)
            if new_capacity != old_capacity:
                capacity_changes[highway or 'inherited_reverse_active_link'] += 1
        if before != after:
            raise ValueError('A non-capacity network attribute changed')
    report = dict(control=left.name, candidate=right.name, verified_capacity_only=True,
        field=field, source_hashes=inputs[0], stable_runtime_file_hashes=stable_files,
        network_element_counts=dict(counts), changed_link_capacities_by_class=dict(capacity_changes),
        limitation='Input isolation only; does not establish execution, calibration or correct road capacities.')
    destination = Path(results_store.processed_dir(right.name))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / '_capacity_input_comparison.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--field', required=True)
    args = parser.parse_args()
    compare(args.control, args.candidate, args.field)
