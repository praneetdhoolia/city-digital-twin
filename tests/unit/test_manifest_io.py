"""Large-city lineage must survive the manifest decoder intact."""
import csv
import json
import pytest

from manifest_io import atomic_manifest_writer, manifest_reader


def test_large_unicode_lineage_and_multiline_source_are_preserved(tmp_path):
    path = tmp_path/'manifest.csv'
    expected = [dict(path='data/processed/aggregate.csv',
                     inputs=json.dumps(['data/raw/source_'+str(i)+'.json' for i in range(10000)]),
                     source='प्रवास\nTwo source lines, one record'),
                dict(path='data/processed/second.csv',inputs='[]',source='Second source')]
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(expected[0]))
        writer.writeheader()
        writer.writerows(expected)
    previous = csv.field_size_limit()
    try:
        csv.field_size_limit(131072)
        with path.open(encoding='utf-8',newline='') as stream:
            assert list(manifest_reader(stream)) == expected
    finally:
        csv.field_size_limit(previous)


def test_manifest_readers_see_previous_file_until_complete_replacement(tmp_path):
    path = tmp_path/'MANIFEST.csv'
    path.write_text('path,source\nold,complete\n', encoding='utf-8')
    with atomic_manifest_writer(path, newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['path', 'source'])
        stream.flush()
        with path.open(encoding='utf-8', newline='') as reader:
            assert list(manifest_reader(reader)) == [{'path': 'old', 'source': 'complete'}]
        writer.writerow(['new', 'प्रवास\ncomplete'])
    with path.open(encoding='utf-8', newline='') as reader:
        assert list(manifest_reader(reader)) == [{'path': 'new', 'source': 'प्रवास\ncomplete'}]
    assert list(tmp_path.iterdir()) == [path]


def test_failed_manifest_serialisation_preserves_old_bytes(tmp_path):
    path = tmp_path/'MANIFEST.json'
    original = b'{"complete": true}\n'
    path.write_bytes(original)
    with pytest.raises(TypeError):
        with atomic_manifest_writer(path, newline='\n') as stream:
            json.dump({'partial': 'written before error', 'bad': object()}, stream)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]
