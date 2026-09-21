"""Extract selected native OSM geometry with complete turn-restriction closure.

The caller supplies spatially selected IDs. Whole ways retain every node;
restriction relations bring in all members, including nested relations. Other
relations are not a schedule or a boundary input to this network extraction.
"""
from collections import Counter
import gzip
import hashlib
import os
from pathlib import Path
import tempfile

from lxml import etree


def entities(source):
    opener = gzip.open if str(source).endswith('.gz') else open
    with opener(source, 'rb') as stream:
        for _, element in etree.iterparse(stream, events=('end',), tag=('node', 'way', 'relation')):
            yield element
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]


def fingerprint(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract(source, output, *, node_ids, way_ids):
    """Refuse missing selected entities; publish only a reference-closed output."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Input and output must be different files')
    source_hash = fingerprint(source)
    wanted = {'node': {int(n) for n in node_ids}, 'way': {int(n) for n in way_ids}, 'relation': set()}
    seed_counts = {kind: len(ids) for kind, ids in wanted.items()}
    if not wanted['way']:
        raise ValueError('Network selection contains no ways')
    relations, counts, relation_types = {}, Counter(), Counter()
    known_ways = set()
    passes = 0
    while True:
        passes += 1
        for element in entities(source):
            kind, identity = element.tag, int(element.get('id'))
            if passes == 1:
                counts[kind] += 1
            if kind == 'way' and identity in wanted['way'] and identity not in known_ways:
                wanted['node'].update(int(n.get('ref')) for n in element.findall('nd'))
                known_ways.add(identity)
            elif kind == 'relation' and passes == 1:
                if identity in relations:
                    raise ValueError('Duplicate relation identifier: ' + str(identity))
                tags = {tag.get('k'): tag.get('v') for tag in element.findall('tag')}
                members = [(member.get('type'), int(member.get('ref')))
                           for member in element.findall('member')]
                relations[identity] = (tags, members)
                relation_types[tags.get('type', '(missing)')] += 1
        # Relations can precede ways or reference relations in either order.
        # Iterate to a fixed point, then read newly required whole ways.
        changed = True
        while changed:
            changed = False
            for identity, (tags, members) in relations.items():
                restriction = tags.get('type', '').split(':', 1)[0] == 'restriction'
                intersects = any(ref in wanted.get(kind, set()) for kind, ref in members)
                if identity not in wanted['relation'] and not (restriction and intersects):
                    continue
                if identity not in wanted['relation']:
                    wanted['relation'].add(identity)
                    changed = True
                for kind, ref in members:
                    if kind not in wanted:
                        raise ValueError('Invalid member type in selected relation: ' + str(identity))
                    if ref not in wanted[kind]:
                        wanted[kind].add(ref)
                        changed = True
        if wanted['relation'] - relations.keys():
            raise ValueError('Selected relation has absent nested relations')
        unread = wanted['way'] - known_ways
        if not unread:
            break
        if passes > 1 and unread == previous_unread:
            raise ValueError('Selected ways absent from source: ' + str(sorted(unread)))
        previous_unread = unread.copy()

    output.parent.mkdir(parents=True, exist_ok=True)
    emitted = {kind: set() for kind in wanted}
    emitted_relation_types = Counter()
    with tempfile.TemporaryDirectory(prefix='osm_network_', dir=output.parent) as work:
        staged = Path(work) / output.name
        with staged.open('wb') as stream:
            with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as zipped:
                zipped.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6">\n')
                for element in entities(source):
                    kind, identity = element.tag, int(element.get('id'))
                    if identity not in wanted[kind]:
                        continue
                    if identity in emitted[kind]:
                        raise ValueError('Duplicate selected ' + kind + ': ' + str(identity))
                    if kind == 'way':
                        refs = {int(n.get('ref')) for n in element.findall('nd')}
                        if not refs <= wanted['node']:
                            raise ValueError('Way reference closure failed')
                    elif kind == 'relation':
                        for member in element.findall('member'):
                            if int(member.get('ref')) not in wanted[member.get('type')]:
                                raise ValueError('Relation reference closure failed')
                        emitted_relation_types[relations[identity][0].get('type', '(missing)')] += 1
                    emitted[kind].add(identity)
                    zipped.write(etree.tostring(element, encoding='utf-8', with_tail=False))
                    zipped.write(b'\n')
                zipped.write(b'</osm>\n')
        for kind in wanted:
            missing = wanted[kind] - emitted[kind]
            if missing:
                raise ValueError('Selected ' + kind + ' entities absent: ' + str(sorted(missing)))
        if fingerprint(source) != source_hash:
            raise ValueError('Source changed during network extraction')
        output_hash = fingerprint(staged)
        os.replace(staged, output)
    return dict(source_sha256=source_hash, output_sha256=output_hash,
                source_counts=dict(sorted(counts.items())), seed_counts=seed_counts,
                output_counts={kind: len(ids) for kind, ids in emitted.items()},
                reference_closure_passes=passes,
                source_relation_types=dict(sorted(relation_types.items())),
                output_relation_types=dict(sorted(emitted_relation_types.items())),
                selected_entities_unique=True, complete_selected_references=True,
                selection='Whole seeded ways and nodes, plus touching restrictions and complete nested members',
                limits='Native geometric network input; not modal access, routability, capacities, schedules or a calibrated simulation')
