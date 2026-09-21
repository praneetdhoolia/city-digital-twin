"""Population layout must not determine household inclusion or data survival."""
import gzip
import xml.etree.ElementTree as ET

import pytest
from lxml import etree as XML

from sample_population import keep, lift_cluster_map, subsample_plans


SEED = 20260810


def source(tmp_path, text, name='source.xml.gz'):
    path = tmp_path / name
    with gzip.open(path, 'wt', encoding='utf-8') as stream:
        stream.write(text)
    return path


def read(path):
    with gzip.open(path, 'rb') as stream:
        return ET.parse(stream).getroot()


def person(identity, household=None, lift=None, shared=None):
    # Attribute names need not be first, nor householdId before its couplings.
    values = [('sharedDriverHousehold', shared), ('liftHousehold', lift), ('householdId', household)]
    attrs = ''.join(f"<attribute class='java.lang.String' name='{key}'>{value}</attribute>"
                    for key, value in values if value is not None)
    return (f"<person other='retained' id='{identity}'><attributes>{attrs}</attributes>"
            "<plan selected='yes'><act type='home' x='0' y='0'/><leg mode='compact'>"
            "<route type='links'>alpha beta</route></leg><act type='work' x='1' y='1'/></plan></person>")


def test_full_sample_retains_people_plans_and_population_metadata(tmp_path):
    xml = ("<?xml version='1.0'?><!DOCTYPE population SYSTEM 'https://example.invalid/never-fetch.dtd'>"
           "<population name='synthetic'><attributes><attribute name='description'>A &amp; B</attribute></attributes>"
           + person('one', 'family') + person('two', 'family') + person('external') + '</population>')
    src = source(tmp_path, xml)
    dst = tmp_path / 'sample.xml.gz'
    ids = set()
    assert subsample_plans(src, dst, 1, SEED, 'household', ids) == (3, 3, 1)
    out = read(dst)
    assert ids == {'one', 'two', 'external'}
    assert out.attrib == {'name': 'synthetic'}
    assert out.find('attributes/attribute').text == 'A & B'
    assert [(p.get('id'), p.find('plan/leg').get('mode'), p.find('plan/leg/route').text)
            for p in out.findall('person')] == [('one', 'compact', 'alpha beta'),
                                               ('two', 'compact', 'alpha beta'),
                                               ('external', 'compact', 'alpha beta')]
    assert b'never-fetch.dtd' in gzip.open(dst, 'rb').read()
    first = dst.read_bytes()
    subsample_plans(src, dst, 1, SEED, 'household')
    assert dst.read_bytes() == first


def test_order_and_whitespace_do_not_break_lift_clusters_or_nesting(tmp_path):
    people = person('one', '1', '2,3', '3') + person('two', '2') + person('three', '3')
    people += ''.join(person(f'p{number}', str(number)) + person(f'q{number}', str(number))
                      for number in range(4, 104))
    compact = '<population>' + people + '</population>'
    pretty = XML.tostring(XML.fromstring(compact), pretty_print=True).decode()
    paths = [source(tmp_path, compact, 'compact.xml.gz'), source(tmp_path, pretty, 'pretty.xml.gz')]
    for path in paths:
        assert lift_cluster_map(path) == {'2': '1'}
    previous = set()
    for fraction in (.01, .1, .25, 1):
        results = []
        for index, path in enumerate(paths):
            dst = tmp_path / f'sample{index}.xml.gz'
            kept = set()
            subsample_plans(path, dst, fraction, SEED, 'household', kept)
            assert kept == {p.get('id') for p in read(dst).findall('person')}
            results.append(kept)
        assert results[0] == results[1]
        selected = results[0]
        assert previous <= selected
        assert ('one' in selected) == ('two' in selected)
        assert ('three' in selected) == keep('three', fraction, SEED, '3', 'household')
        for number in range(4, 104):
            assert (f'p{number}' in selected) == (f'q{number}' in selected)
        previous = selected


def test_namespaced_xml_and_escaped_ids_use_decoded_identity(tmp_path):
    src = source(tmp_path, '<population xmlns="urn:fixture">' + person('one&amp;two', 'a&amp;b') + '</population>')
    dst = tmp_path / 'out.xml.gz'
    kept = set()
    assert subsample_plans(src, dst, 1, SEED, 'household', kept) == (1, 1, 0)
    assert kept == {'one&two'}
    assert read(dst).find('{urn:fixture}person').get('id') == 'one&two'


@pytest.mark.parametrize('fraction,unit', [(0, 'household'), (-1, 'household'), (1.01, 'household'),
                                        (float('nan'), 'household'), (float('inf'), 'household'),
                                        (True, 'household'), (.25, 'typo')])
def test_invalid_sampling_cannot_replace_output(tmp_path, fraction, unit):
    src = source(tmp_path, '<population>' + person('one', '1') + '</population>')
    dst = tmp_path / 'out.xml.gz'; dst.write_bytes(b'previous file')
    with pytest.raises(ValueError):
        subsample_plans(src, dst, fraction, SEED, unit)
    assert dst.read_bytes() == b'previous file'


@pytest.mark.parametrize('bad', [
    '<population>' + person('one') + '<person id="late">',
    '<population>' + person('one') + person('one') + '</population>',
    '<population>' + person('one', '') + '</population>',
    '<population><person><plan/></person></population>',
    '<population><person id="one"><attributes><attribute name="householdId">1</attribute>'
    '<attribute name="householdId">2</attribute></attributes></person></population>',
    '<!DOCTYPE population [<!ENTITY local "1">]><population>' + person('one', '&local;') + '</population>',
])
def test_invalid_input_fails_atomically_in_person_sampling_too(tmp_path, bad):
    src = source(tmp_path, bad)
    dst = tmp_path / 'out.xml.gz'; dst.write_bytes(b'previous file')
    kept = {'previous-id'}
    with pytest.raises((ValueError, XML.XMLSyntaxError)):
        subsample_plans(src, dst, 1, SEED, 'person', kept)
    assert dst.read_bytes() == b'previous file'
    assert kept == {'previous-id'}


def test_source_population_cannot_be_overwritten(tmp_path):
    src = source(tmp_path, '<population>' + person('one') + '</population>')
    before = src.read_bytes()
    with pytest.raises(ValueError, match='source population'):
        subsample_plans(src, src, 1, SEED, 'person')
    assert src.read_bytes() == before
