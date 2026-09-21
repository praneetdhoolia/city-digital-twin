"""Output-level lineage decides, refuses, or says it cannot (#159).

The defect this guards was invisible for three phases because the only thing
that exercised `build_manifest.py` was a 2.3 GiB rebuild: a script's whole
input list was credited to every file it wrote, so 129 rows named an
OpenStreetMap ancestor while carrying a CC-BY licence and nothing compared the
two columns. These drive the three functions that decide it on synthetic
inputs - a declaration, an ancestor set, a scope - so a regression shows up in
the diff that caused it rather than in a rebuild nobody runs.
"""
import textwrap
import json
from pathlib import Path

import pytest


import build_manifest as bm


@pytest.mark.parametrize('present', [True, False])
def test_city_relative_provenance_preserves_metadata(tmp_path, monkeypatch, present):
    relative = 'data/raw/provider/download.csv'
    folder = tmp_path / 'data/raw/provider'
    folder.mkdir(parents=True)
    if present:
        (tmp_path / relative).write_text('value\n1\n', encoding='utf-8')
    record = {'path': relative, 'licence': 'source terms',
              'retrieved': '2026-01-01', 'url': 'https://example.org/data'}
    provenance = folder / 'provenance_download.json'
    provenance.write_text(json.dumps({'files': [record]}), encoding='utf-8')
    monkeypatch.setattr(bm, 'ROOT', str(tmp_path))
    monkeypatch.setattr(bm, 'PROVENANCE_FILES', [str(provenance)])
    assert bm.provenance_records()[relative]['licence'] == record['licence']
    assert bm.provenance_records()[relative]['retrieved'] == record['retrieved']


@pytest.mark.parametrize('key, here, base', [
    ('download.csv', 'data/raw/provider', None),
    ('provider/download.csv', 'data/raw', None),
    ('download.csv', 'data/raw/records', 'data/raw/provider'),
])
def test_legacy_provenance_paths_still_resolve(tmp_path, monkeypatch, key, here, base):
    relative = 'data/raw/provider/download.csv'
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_text('value\n1\n', encoding='utf-8')
    monkeypatch.setattr(bm, 'ROOT', str(tmp_path))
    assert bm._resolve_record_path(key, here, base) == relative


def test_raw_input_pattern_keeps_declared_absent_source(tmp_path, monkeypatch):
    selected = 'data/raw/maps/roads_123.osm.pbf'
    other = 'data/raw/maps/places_456.csv'
    monkeypatch.setattr(bm, 'ROOT', str(tmp_path))
    monkeypatch.setattr(bm, 'SOURCES', [
        {'name': 'Road source', 'url': 'https://example.org/roads',
         'provides': [selected], 'share_alike': True},
        {'name': 'Other source', 'provides': [other]},
    ])
    proven, possible, scope = bm.ancestry('data/raw/maps/roads_*.osm.pbf')
    assert proven == possible == {selected}
    assert bm.share_alike_verdict(proven, possible, scope) == 'yes'
    assert bm.derived_provenance('output', {
        selected: {'retrieved': '2026-01-01'}}, proven) == (
            'Road source', 'https://example.org/roads', '2026-01-01')


def test_package_record_does_not_inherit_neighbouring_download_licence():
    prov = {'data/raw/maps/roads.pbf': {
        'licence': 'share-alike data licence', 'retrieved': '2026-01-01'}}
    assert bm.record_for('data/raw/maps/provenance_roads.json', prov) == {}
    assert bm.record_for('data/raw/maps/_acquisition_log.json', prov) == {}
    # Archive members retain the legacy directory inheritance behaviour.
    assert bm.record_for('data/raw/maps/roads.shp', prov) == prov['data/raw/maps/roads.pbf']


def test_source_index_preserves_overlaps_ties_and_directory_boundaries(monkeypatch):
    sources = [
        {'name': 'Area', 'provides': ['/data/raw/maps/'], 'share_alike': True},
        {'name': 'Exact first', 'provides': ['data/raw/maps/roads.pbf']},
        {'name': 'Exact second', 'provides': ['data/raw/maps/roads.pbf'], 'share_alike': True},
        {'name': 'Distinct directory', 'provides': ['data/raw/maps_extra']},
        {'name': 'No files', 'provides': []},
    ]
    monkeypatch.setattr(bm, 'SOURCES', sources)
    index = bm.SourceIndex(sources)
    paths = ['data/raw/maps', 'data/raw/maps/roads.pbf', 'data/raw/maps/roads.pbf/member',
             'data/raw/maps/other', 'data/raw/maps_extra/file', 'data/raw/map', 'absent', '']
    for path in paths:
        assert bm.source_for(path, index) is bm.source_for(path)
    assert bm.source_for('data/raw/maps/roads.pbf', index) is sources[1]
    assert bm.share_alike_sources({'data/raw/maps/roads.pbf'}, index) == [sources[0], sources[2]]
    assert bm.share_alike_sources({'data/raw/maps_extra/file'}, index) == []


def test_indexed_derived_provenance_preserves_source_order_and_latest_date(monkeypatch):
    sources = [
        {'name': 'Broad', 'url': 'https://example.org/broad', 'provides': ['data/raw/a']},
        {'name': 'Narrow', 'url': 'https://example.org/narrow', 'provides': ['data/raw/a/one']},
        {'name': 'Broad', 'url': 'https://example.org/duplicate', 'provides': ['data/raw/b']},
        {'name': 'Unrelated', 'url': 'https://example.org/other', 'provides': ['data/raw/ab']},
    ]
    monkeypatch.setattr(bm, 'SOURCES', sources)
    ancestors = {'data/raw/b', 'data/raw/a/one'}
    provenance = {
        'data/raw/a/one': {'retrieved': '2026-01-01'},
        'data/raw/b/member': {'retrieved': '2026-02-01'},
        'data/raw/ab/unrelated': {'retrieved': '2026-12-01'},
        'data/raw/b_extra': {'retrieved': '2026-12-02'},
    }
    expected = ('Broad + Narrow', 'https://example.org/broad + https://example.org/narrow', '2026-02-01')
    assert bm.derived_provenance('output', provenance, ancestors) == expected
    assert bm.derived_provenance('output', provenance, ancestors, bm.SourceIndex(sources)) == expected


def test_source_indexes_are_independent_between_builds():
    first = bm.SourceIndex([{'name': 'First', 'provides': ['same/path']}])
    second = bm.SourceIndex([{'name': 'Second', 'provides': ['same/path']}])
    assert first.nearest('same/path')['name'] == 'First'
    assert second.nearest('same/path')['name'] == 'Second'


# --------------------------------------------------------------------------
# the declaration is READ, never executed
# --------------------------------------------------------------------------
def _script(tmp_path, body):
    p = tmp_path / 'a_builder.py'
    p.write_text(textwrap.dedent(body), encoding='utf-8')
    bm._declared_cache.clear()
    bm._script_inputs_cache.clear()
    return str(p)


@pytest.mark.parametrize('present', [False, True])
def test_built_native_osm_follows_raw_ancestry_even_through_a_glob(tmp_path, monkeypatch, present):
    raw = 'data/raw/maps/source.pbf'
    derived = 'networks/osm/native.osm.gz'
    script = _script(tmp_path, """
        OUTPUT_INPUTS = {'networks/osm/native.osm.gz': ['data/raw/maps/source.pbf']}
    """)
    monkeypatch.setattr(bm, 'ROOT', str(tmp_path))
    monkeypatch.setattr(bm, 'LINEAGE', {derived: script})
    monkeypatch.setattr(bm, 'SOURCES', [
        {'name': 'Immutable map source', 'url': 'https://example.org/source.pbf',
         'licence': 'ODbL 1.0', 'share_alike': True, 'provides': [raw]}])
    monkeypatch.setattr(bm, 'DERIVED_LICENCES', {derived: 'ODbL 1.0'})
    if present:
        target = tmp_path / derived
        target.parent.mkdir(parents=True)
        target.write_bytes(b'not a new download')
    assert bm.artifact_stage(derived) == 'processed'
    assert bm.artifact_stage(raw) == 'raw'
    assert bm.artifact_stage('networks/osm/legacy.osm') == 'raw'
    assert bm.ancestry(derived) == ({raw}, {raw}, 'output')
    assert bm.ancestry('networks/osm/*.osm.gz') == ({raw}, {raw}, 'output')
    assert bm.derived_provenance(derived, {raw: {'retrieved': '2026-01-01'}}, {raw}) == (
        'Immutable map source', 'https://example.org/source.pbf', '2026-01-01')


def test_network_descriptor_selector_excludes_unselected_neighbouring_files(tmp_path, monkeypatch):
    selected, unselected = 'networks/osm/roads.osm', 'networks/osm/parking.osm'
    script = _script(tmp_path, """
        OUTPUT_INPUTS = {'networks/matsim/base/network.xml.gz': ['city.json#osm_network_inputs']}
    """)
    monkeypatch.setattr(bm, 'ROOT', str(tmp_path))
    monkeypatch.setattr(bm, 'LINEAGE', {'networks/matsim': script})
    monkeypatch.setattr(bm._city, 'network_osm_inputs', lambda: [str(tmp_path / selected)])
    monkeypatch.setattr(bm._city, 'rel', lambda p: Path(p).relative_to(tmp_path).as_posix())
    for name in (selected, unselected):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('<osm/>', encoding='utf-8')
    assert bm.ancestry('networks/matsim/base/network.xml.gz') == ({selected}, {selected}, 'output')


def test_declaration_is_read_without_importing_the_module(tmp_path):
    """A builder that would blow up on import still yields its declaration."""
    path = _script(tmp_path, """
        raise SystemExit('this module must never be executed')
        OUTPUT_INPUTS = {'out/a.csv': ['data/raw/x', 'data/raw/y']}
    """)
    assert bm._script_declarations(path) == {
        'out/a.csv': ('data/raw/x', 'data/raw/y')}


def test_output_wildcard_selects_its_own_feed(tmp_path):
    path = _script(tmp_path, """
        OUTPUT_INPUTS = {'mapped/*/vehicles.xml': ['feeds/{match}.zip']}
    """)
    assert bm._declared_inputs('mapped/one/vehicles.xml', path) == ({'feeds/one.zip'}, True)
    assert bm._declared_inputs('mapped/two/vehicles.xml', path) == ({'feeds/two.zip'}, True)


def test_a_non_literal_declaration_is_refused_not_half_read(tmp_path):
    path = _script(tmp_path, """
        SHARED = ['data/raw/x']
        OUTPUT_INPUTS = {'out/a.csv': SHARED}
    """)
    assert bm._script_declarations(path) == {}


def test_no_declaration_is_an_empty_mapping_not_an_error(tmp_path):
    assert bm._script_declarations(_script(tmp_path, 'X = 1\n')) == {}


# --------------------------------------------------------------------------
# the extractor sees a path built by a call, not only a literal
# --------------------------------------------------------------------------
def test_a_multi_argument_city_path_call_is_an_input(tmp_path):
    """The charging-dwell builder named its only OSM-descended input this way
    and the manifest could not see it at all."""
    path = _script(tmp_path, """
        SCHEDULES = _city.path('networks', 'matsim', 'schedules')
        OTHER = _city.path('data/processed/zones/zones_SA1.gpkg')
    """)
    found = bm._script_inputs(path)
    assert 'networks/matsim/schedules' in found
    assert 'data/processed/zones/zones_SA1.gpkg' in found


def test_a_call_that_is_not_a_layer_path_is_not_an_input(tmp_path):
    path = _script(tmp_path, "X = something.path('tmp', 'scratch')\n")
    assert bm._script_inputs(path) == set()


# --------------------------------------------------------------------------
# the verdict: yes needs proof, no needs no possibility, undetermined is the
# honest answer in between
# --------------------------------------------------------------------------
OSM = 'networks/osm/roads.osm'
ABS = 'data/raw/census'


@pytest.mark.parametrize('proven, possible, scope, expected', [
    # proven share-alike ancestor, resolved output-level: decided
    ({OSM}, {OSM, ABS}, 'output', 'yes'),
    # the file IS the share-alike download
    ({OSM}, {OSM}, 'raw', 'yes'),
    # nothing share-alike anywhere in the over-approximation: decided
    (set(), {ABS}, 'script', 'no'),
    ({ABS}, {ABS}, 'output', 'no'),
    # share-alike is POSSIBLE but reached only through a script-level union -
    # this is the case #159 was mis-asserting as fact
    (set(), {OSM, ABS}, 'script', 'undetermined'),
    # no producing script at all: nothing is known
    (set(), set(), 'none', 'undetermined'),
])
def test_share_alike_verdict(proven, possible, scope, expected):
    assert bm.share_alike_verdict(proven, possible, scope) == expected


def test_a_yes_never_rests_on_the_script_level_union():
    """The one rule the licence boundary depends on: an ancestor that is only
    possible may not create a share-alike obligation."""
    assert bm.share_alike_verdict(set(), {OSM}, 'script') != 'yes'


def test_a_reference_is_not_an_ancestor():
    """The assembler's ruling, pinned: a config that merely NAMES the network,
    plans and schedule files in relative paths declares none of them, because a
    path carries no content. If someone later adds them to make a row 'resolve',
    31 rows silently acquire a share-alike obligation they do not carry."""
    decl = bm._script_declarations('src/build/build_matsim_run_inputs.py')
    config = decl.get('scenarios/matsim/*/config.xml')
    assert config is not None, 'the assembler must declare its config outputs'
    assert not bm.holds_share_alike(set(config))
    # and the outputs that DO carry content still say so
    for key in ('scenarios/matsim/*/network.xml.gz',
                'scenarios/matsim/*/transitSchedule.xml.gz',
                'scenarios/matsim/*/parking_prices.tsv'):
        assert bm.holds_share_alike(set(decl[key])), key


def test_the_city_declares_which_licences_are_share_alike():
    """The framework names no licence: the labels come from the city's own
    sources block, so a city harvesting a different share-alike source is
    checked against ITS label."""
    for label in bm.SHARE_ALIKE_LICENCES:
        assert bm.is_share_alike(label)
    assert not bm.is_share_alike('a licence this city declares nowhere')
