import gzip

import pytest

from iteration_reading import events


XML = b'''<?xml version="1.0"?><events>
<event time="1" type="entered link" person="irrelevant" vehicle="v1" />
<event time="2" type="stuckAndAbort" person="a&amp;b" legMode="walk" />
<event time="3" type="custom&amp;type" person="x" />
</events>'''


@pytest.mark.parametrize('suffix', ['.xml', '.xml.gz', '.xml.zst'])
def test_compression_filter_and_escaped_values(tmp_path, suffix):
    path = tmp_path / ('events' + suffix)
    if suffix.endswith('.gz'):
        path.write_bytes(gzip.compress(XML))
    elif suffix.endswith('.zst'):
        zstd = pytest.importorskip('zstandard')
        path.write_bytes(zstd.ZstdCompressor().compress(XML))
    else:
        path.write_bytes(XML)
    complete = list(events(path))
    assert len(complete) == 3
    assert list(events(path, {'stuckAndAbort'})) == [complete[1]]
    assert complete[1][1]['person'] == 'a&b'
    assert list(events(path, {'custom&type'})) == [complete[2]]
    assert list(events(path, set())) == []
    assert list(events(path, attribute_values={'vehicle': {'v1'}})) == [complete[0]]
    assert list(events(path, {'stuckAndAbort'}, {'vehicle': {'v1'}})) == []
    assert list(events(path, attribute_values={'person': {'a&b'}})) == [complete[1]]
