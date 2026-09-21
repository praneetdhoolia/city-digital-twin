"""Reference audits must find broken topology without conflating ID namespaces."""
import csv

from audit_osm_references import audit


def test_forward_nested_references_and_distinct_namespaces(tmp_path):
    source = tmp_path / 'input.osm'
    source.write_text('''<osm>
      <relation id="1"><member type="relation" ref="2" role="child"/>
        <member type="way" ref="1" role="from"/><member type="node" ref="1" role="via"/></relation>
      <way id="1"><nd ref="2"/><nd ref="1"/></way>
      <node id="2" lat="0" lon="0"/><node id="1" lat="0" lon="0"/>
      <relation id="2"><member type="relation" ref="1" role="parent"/></relation>
    </osm>''', encoding='utf-8')
    result = audit(source, tmp_path / 'output', batch_size=2)
    assert result['identity_and_reference_checks_pass']
    assert result['checked_references'] == {'way->node': 2, 'relation->node': 1,
                                           'relation->way': 1, 'relation->relation': 2}


def test_missing_restriction_members_and_duplicates_across_chunks(tmp_path):
    source = tmp_path / 'input.osm'
    source.write_text('''<osm>
      <node id="1" lat="0" lon="0"/><node id="2" lat="0" lon="0"/>
      <node id="3" lat="0" lon="0"/><node id="3" lat="0" lon="0"/>
      <way id="9"><nd ref="1"/><nd ref="8"/></way>
      <relation id="8"><tag k="type" v="restriction"/>
        <member type="way" ref="9" role="from"/>
        <member type="node" ref="8" role="via"/>
        <member type="way" ref="10" role="to"/>
        <member type="relation" ref="99" role="child"/>
        <member type="bogus" ref="1" role="bad"/>
      </relation>
    </osm>''', encoding='utf-8')
    output = tmp_path / 'output'
    result = audit(source, output, batch_size=2)
    assert not result['identity_and_reference_checks_pass']
    assert result['duplicate_occurrences'] == {'node': 1, 'way': 0, 'relation': 0}
    assert sum(result['missing_references'].values()) == 5
    with (output / 'osm_missing_references.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert any(r['member_role'] == 'via' and r['referenced_id'] == '8'
               and r['parent_relation_type'] == 'restriction' for r in rows)


def test_empty_target_namespace_reports_missing_node(tmp_path):
    source = tmp_path / 'input.osm'
    source.write_text('<osm><way id="1"><nd ref="1"/></way></osm>', encoding='utf-8')
    result = audit(source, tmp_path / 'output')
    assert not result['identity_and_reference_checks_pass']
    assert result['missing_references'] == {'way->node': 1}
