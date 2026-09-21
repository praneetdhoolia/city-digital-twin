"""Rebuild the acquisition ledger from the catalogue and verified raw hashes."""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path

import city

OUTPUT_INPUTS = {
    'data/processed/acquisition/source_inventory.json': ['extract/sources.json', 'data/raw/**/provenance_*.json'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sync-descriptor', action='store_true',
                        help='Regenerate descriptor source declarations from the catalogue.')
    args = parser.parse_args()
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    records = []
    hashes = defaultdict(list)
    for entry in catalogue['sources']:
        provenance = Path(city.path('data/raw', entry['category'], 'provenance_' + entry['id'] + '.json'))
        row = {key: entry[key] for key in ('id', 'title', 'url', 'category', 'licence', 'coverage')}
        if provenance.exists():
            record = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
            path = Path(city.path(record['path']))
            with path.open('rb') as stream:
                actual_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual_hash != record['sha256'] or record['url'] != entry['url']:
                raise ValueError('Source integrity mismatch: ' + entry['id'])
            if (record.get('method', 'GET') != entry.get('method', 'GET') or
                    record.get('request_json') != entry.get('request_json') or
                    record.get('request_form') != entry.get('request_form')):
                raise ValueError('Source request mismatch: ' + entry['id'])
            row.update(status='acquired_unvalidated', path=record['path'], sha256=actual_hash,
                       bytes=record['bytes'], retrieved=record['retrieved'])
            review = entry.get('content_review')
            if review is not None:
                if (review.get('sha256') != actual_hash or
                        review.get('status') != 'acquired_unusable' or not review.get('reason')):
                    raise ValueError('Invalid content review: ' + entry['id'])
                row.update(status=review['status'], content_review_reason=review['reason'])
            if row['status'] == 'acquired_unvalidated':
                hashes[actual_hash].append(entry['id'])
        else:
            row['status'] = 'unobtained'
        records.append(row)
    if args.sync_descriptor:
        descriptor_path = Path(city.path('city.json'))
        descriptor = json.loads(descriptor_path.read_text(encoding='utf-8'))
        descriptor['sources'] = [dict(
            name=entry['title'], url=entry['url'], licence=entry['licence'],
            share_alike=entry.get('share_alike', False),
            provides=[row['path']] if 'path' in row else [])
            for entry, row in zip(catalogue['sources'], records)]
        descriptor_path.write_text(json.dumps(descriptor, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    output = Path(city.path('data/processed/acquisition/source_inventory.json'))
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        'schema_version': 1,
        'completion': 'Acquisition inventory only. No claim of validated inputs or a runnable city.',
        'sources': records,
        'identical_bytes_groups': sorted(ids for ids in hashes.values() if len(ids) > 1),
    }
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'catalogued': len(records), 'acquired': len([r for r in records if r['status'] == 'acquired_unvalidated']),
                      'acquired_unusable': len([r for r in records if r['status'] == 'acquired_unusable']),
                      'unique_acquired_contents': len(hashes)}))


if __name__ == '__main__':
    main()
