"""Audit OSM identity uniqueness and reference closure with disk-backed ID arrays.

No network is clipped, repaired or simplified. Node, way and relation IDs have
separate namespaces. Forward and nested relation references are supported.
"""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile

import numpy as np

from osm_parse import parse


def audit(source, output_directory, *, batch_size=io.DEFAULT_BUFFER_SIZE):
    """Write complete missing-reference and duplicate-ID tables plus their audit."""
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')
    source, output_directory = Path(source), Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as stream:
        source_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    kinds = ('node', 'way', 'relation')
    counts, duplicate_counts, missing_counts, checked_counts = Counter(), Counter(), Counter(), Counter()
    indexes = {}
    with tempfile.TemporaryDirectory(prefix='osm-reference-audit-', dir=output_directory) as temporary:
        root = Path(temporary)
        handles = {kind: (root / (kind + '.ids')).open('wb') for kind in kinds}
        try:
            for entity in parse(source):
                kind = 'relation' if entity[0] == 'rel' else entity[0]
                handles[kind].write(struct.pack('<q', int(entity[1])))
                counts[kind] += 1
        finally:
            for handle in handles.values():
                handle.close()
        try:
            with (root / 'osm_duplicate_ids.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['entity_type', 'entity_id', 'duplicate_occurrence'])
                for kind in kinds:
                    ids = (np.memmap(root / (kind + '.ids'), dtype='<i8', mode='r+')
                           if counts[kind] else np.empty(0, dtype='<i8'))
                    indexes[kind] = ids
                    ids.sort()
                    # Include the preceding item when a chunk starts so repeats
                    # at chunk boundaries cannot disappear from the count.
                    for start in range(1, len(ids), batch_size):
                        end = min(start + batch_size, len(ids))
                        equal = ids[start:end] == ids[start - 1:end - 1]
                        for offset in np.flatnonzero(equal):
                            duplicate_counts[kind] += 1
                            writer.writerow([kind, int(ids[start + offset]), duplicate_counts[kind]])

            with (root / 'osm_missing_references.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['parent_type', 'parent_id', 'parent_relation_type', 'member_sequence',
                                 'member_role', 'referenced_type', 'referenced_id', 'reason'])
                pending = {kind: [] for kind in kinds}

                def flush(kind):
                    rows = pending[kind]
                    if not rows:
                        return
                    ids = indexes[kind]
                    requested = np.fromiter((row[6] for row in rows), dtype='<i8', count=len(rows))
                    offsets = np.searchsorted(ids, requested)
                    found = offsets < len(ids)
                    if len(ids):
                        found[found] = ids[offsets[found]] == requested[found]
                    for row, present in zip(rows, found):
                        key = row[0] + '->' + kind
                        checked_counts[key] += 1
                        if not present:
                            missing_counts[key] += 1
                            writer.writerow([*row, 'absent_entity'])
                    rows.clear()

                second_counts = Counter()
                for entity in parse(source):
                    kind = 'relation' if entity[0] == 'rel' else entity[0]
                    second_counts[kind] += 1
                    if kind == 'node':
                        continue
                    parent_id = int(entity[1])
                    members = (('node', ref, '') for ref in entity[2]) if kind == 'way' else iter(entity[2])
                    for sequence, (target_kind, ref, role) in enumerate(members, start=1):
                        row = (kind, parent_id, entity[-1].get('type', '') if kind == 'relation' else '',
                               sequence, role, target_kind, int(ref))
                        if target_kind not in pending:
                            checked_counts['invalid_member_type'] += 1
                            missing_counts['invalid_member_type'] += 1
                            writer.writerow([*row, 'invalid_member_type'])
                        else:
                            pending[target_kind].append(row)
                            if len(pending[target_kind]) >= batch_size:
                                flush(target_kind)
                for kind in kinds:
                    flush(kind)
                if counts != second_counts:
                    raise ValueError('OSM entity counts changed between audit passes')
            with source.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != source_hash:
                    raise ValueError('OSM source changed while being audited')
            result = dict(schema_version=1, source_sha256=source_hash,
                          counts={kind: counts[kind] for kind in kinds},
                          duplicate_occurrences={kind: duplicate_counts[kind] for kind in kinds},
                          checked_references=dict(sorted(checked_counts.items())),
                          missing_references=dict(sorted(missing_counts.items())),
                          identity_and_reference_checks_pass=bool(counts['node']) and not duplicate_counts and not missing_counts,
                          limits='Whole supplied source extent. Identity and reference checks only; no connectivity, geometry, legal access, current operation, capacity or calibration validation.')
            (root / 'osm_reference_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            for name in ('osm_duplicate_ids.csv', 'osm_missing_references.csv', 'osm_reference_audit.json'):
                (root / name).replace(output_directory / name)
            return result
        finally:
            # Explicitly release Windows mappings before TemporaryDirectory cleanup.
            for ids in indexes.values():
                if isinstance(ids, np.memmap):
                    ids._mmap.close()
