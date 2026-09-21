"""The network parser accepts compressed topology without changing entities."""
import gzip
import pytest

from osm_parse import parse


@pytest.mark.parametrize('compressed', [False, True])
def test_path_input_preserves_references_and_restriction_roles(tmp_path, compressed):
    content = b'''<osm version="0.6">
      <node id="5000000001" lat="0" lon="0"><tag k="barrier" v="bollard"/></node>
      <way id="6"><nd ref="5000000001"/><nd ref="7"/><nd ref="5000000001"/>
        <tag k="oneway" v="-1"/></way>
      <relation id="9"><member type="way" ref="6" role="from"/>
        <member type="node" ref="5000000001" role="via"/>
        <member type="way" ref="8" role="to"/>
        <tag k="type" v="restriction"/><tag k="restriction" v="no_left_turn"/>
      </relation></osm>'''
    path = tmp_path / ('network.osm.gz' if compressed else 'network.osm')
    path.write_bytes(gzip.compress(content, mtime=0) if compressed else content)
    assert list(parse(path)) == [
        ('node', '5000000001', 0., 0., {'barrier': 'bollard'}),
        ('way', '6', ['5000000001', '7', '5000000001'], {'oneway': '-1'}),
        ('rel', '9', [('way', '6', 'from'), ('node', '5000000001', 'via'), ('way', '8', 'to')],
         {'type': 'restriction', 'restriction': 'no_left_turn'}),
    ]
