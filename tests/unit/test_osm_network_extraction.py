"""A spatial selection must not destroy turn restrictions at its edge."""
import gzip

import pytest
from lxml import etree

from extract_osm_network import extract


def test_restriction_expands_way_and_nested_reference_closure(tmp_path):
    source = tmp_path / 'all.osm'
    # Deliberately unsorted, overlapping ID namespaces, and a nested cycle.
    source.write_text('''<osm>
      <relation id="2"><member type="relation" ref="1" role="back"/></relation>
      <relation id="1"><tag k="type" v="restriction"/>
        <tag k="restriction:conditional" v="no_left_turn @ (Mo-Fr 08:00-10:00)"/>
        <member type="way" ref="1" role="from"/><member type="way" ref="2" role="to"/>
        <member type="node" ref="2" role="via"/><member type="relation" ref="2" role="child"/>
      </relation>
      <way id="2"><nd ref="2"/><nd ref="3"/><tag k="railway" v="rail"/></way>
      <way id="1"><nd ref="1"/><nd ref="2"/><tag k="highway" v="footway"/></way>
      <node id="3" lat="3" lon="3"/><node id="2" lat="2" lon="2"/>
      <node id="1" lat="1" lon="1"><tag k="barrier" v="gate"/></node>
      <way id="4"><nd ref="4"/></way><node id="4" lat="4" lon="4"/>
      <relation id="9"><tag k="type" v="route"/><member type="way" ref="1" role=""/></relation>
    </osm>''', encoding='utf-8')
    output = tmp_path / 'selected.osm.gz'
    report = extract(source, output, node_ids=[], way_ids=[1])
    assert report['output_counts'] == {'node': 3, 'way': 2, 'relation': 2}
    assert report['complete_selected_references']
    root = etree.fromstring(gzip.decompress(output.read_bytes()))
    assert root.xpath('string(relation[@id="1"]/tag[@k="restriction:conditional"]/@v)') == 'no_left_turn @ (Mo-Fr 08:00-10:00)'
    assert root.xpath('string(node[@id="1"]/tag/@v)') == 'gate'
    assert root.xpath('relation[@id="1"]/member/@role') == ['from', 'to', 'via', 'child']
    assert root.xpath('way[@id="2"]/nd/@ref') == ['2', '3']
    before = output.read_bytes()
    extract(source, output, node_ids=[], way_ids=[1])
    assert output.read_bytes() == before


@pytest.mark.parametrize('body,message', [
    ('<way id="1"><nd ref="8"/></way>', 'node entities absent'),
    ('<node id="1" lat="0" lon="0"/>', 'ways absent'),
    ('<node id="1" lat="0" lon="0"/><node id="1" lat="1" lon="1"/><way id="1"><nd ref="1"/></way>', 'Duplicate selected node'),
    ('<node id="1" lat="0" lon="0"/><way id="1"><nd ref="1"/></way><relation id="1"><tag k="type" v="restriction"/><member type="way" ref="1"/><member type="relation" ref="8"/></relation>', 'absent nested relations'),
])
def test_incomplete_selection_does_not_replace_existing_output(tmp_path, body, message):
    source, output = tmp_path / 'input.osm', tmp_path / 'output.osm.gz'
    source.write_text('<osm>' + body + '</osm>', encoding='utf-8')
    output.write_bytes(b'previous successful build')
    with pytest.raises(ValueError, match=message):
        extract(source, output, node_ids=[], way_ids=[1])
    assert output.read_bytes() == b'previous successful build'
