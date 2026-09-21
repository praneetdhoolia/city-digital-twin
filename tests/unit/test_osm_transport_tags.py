import gzip
import json
from pathlib import Path

import pytest

from build.audit_osm_transport_tags import audit, normalise, write


UNIT_CASES = json.loads((Path(__file__).parents[1] / 'fixtures' /
                        'osm_transport_units.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('key,raw,expected,unit', UNIT_CASES)
def test_units_and_directional_zero(key, raw, expected, unit):
    result = normalise(key, raw)
    assert result[0] == pytest.approx(expected)
    assert result[1:] == (unit, 'normalised')


@pytest.mark.parametrize('key,raw', [
    ('maxspeed', '20;30'), ('maxspeed', 'walk'), ('maxspeed', 'IN:urban'),
    ('maxspeed', 'nan'), ('maxspeed', '-1'), ('maxspeed', '30 kph'),
    ('width', '3-4'), ('width', '0'), ('width', '2,5'), ('width', '12\'14"'),
    ('lanes', '1.5'), ('lanes', '2;3'), ('lanes', '0'),
])
def test_ambiguous_numeric_tags_are_never_truncated(key, raw):
    assert normalise(key, raw)[::2] == (None, 'unresolved')


def test_audit_preserves_asymmetry_conditions_and_first_source(tmp_path):
    first = tmp_path / 'first.osm.gz'
    second = tmp_path / 'second.osm'
    first.write_bytes(gzip.compress(b'''<osm>
      <node id="1" lat="0" lon="0"/>
      <way id="1"><nd ref="1"/><nd ref="2"/>
        <tag k="highway" v="primary"/><tag k="lanes" v="3"/>
        <tag k="lanes:forward" v="2"/><tag k="lanes:backward" v="1"/>
        <tag k="maxspeed" v="20 mph"/>
        <tag k="maxspeed:conditional" v="10 @ (wet)"/>
        <tag k="bicycle:conditional" v="no @ (Mo-Fr)"/></way>
      <way id="2"><nd ref="1"/><nd ref="2"/><tag k="highway" v="primary"/></way>
      <way id="3"><nd ref="1"/><nd ref="2"/><tag k="highway" v="pedestrian"/>
        <tag k="area" v="yes"/></way>
      <way id="4"><nd ref="1"/><tag k="highway" v="service"/></way>
    </osm>''', mtime=0))
    second.write_text('''<osm><way id="1"><nd ref="1"/><nd ref="2"/>
      <tag k="highway" v="primary"/><tag k="maxspeed" v="100"/></way></osm>''')
    report, rows = audit([first, second])
    primary = report['by_class']['highway=primary']
    assert primary['linear_ways'] == 2
    assert primary['tag_coverage']['maxspeed'] == 1
    assert primary['numeric_tags']['lanes']['median'] == 3
    assert primary['numeric_tags']['lanes:forward']['median'] == 2
    assert primary['numeric_tags']['lanes:backward']['median'] == 1
    assert primary['numeric_tags']['maxspeed']['median'] == pytest.approx(UNIT_CASES[0][2])
    assert report['counts'] == {
        'transport_ways': 4, 'duplicate_way_occurrences_skipped': 1,
        'area_ways_excluded_from_linear_statistics': 1,
        'short_ways_excluded_from_linear_statistics': 1,
    }
    conditional = next(row for row in rows if row['tag'] == 'maxspeed:conditional')
    assert conditional['raw_value'] == '10 @ (wet)'
    assert conditional['normalised_value'] is None
    assert conditional['status'] == 'retained_text'
    write(report, rows, tmp_path / 'output')
    snapshot = {p.name: p.read_bytes() for p in (tmp_path / 'output').iterdir()}
    write(*audit([first, second]), tmp_path / 'output')
    assert snapshot == {p.name: p.read_bytes() for p in (tmp_path / 'output').iterdir()}
