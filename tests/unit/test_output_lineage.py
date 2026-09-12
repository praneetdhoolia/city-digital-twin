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

import pytest


import build_manifest as bm


# --------------------------------------------------------------------------
# the declaration is READ, never executed
# --------------------------------------------------------------------------
def _script(tmp_path, body):
    p = tmp_path / 'a_builder.py'
    p.write_text(textwrap.dedent(body), encoding='utf-8')
    bm._declared_cache.clear()
    bm._script_inputs_cache.clear()
    return str(p)


def test_declaration_is_read_without_importing_the_module(tmp_path):
    """A builder that would blow up on import still yields its declaration."""
    path = _script(tmp_path, """
        raise SystemExit('this module must never be executed')
        OUTPUT_INPUTS = {'out/a.csv': ['data/raw/x', 'data/raw/y']}
    """)
    assert bm._script_declarations(path) == {
        'out/a.csv': ('data/raw/x', 'data/raw/y')}


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
