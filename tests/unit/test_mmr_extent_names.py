"""The MMR extent is derived from published lists by name and code, never by a
rectangle or a guess (D13, 9.204). The pure pieces of that derivation:

* a census ward row resolves to its town without the printed type suffix,
  so a municipality named by the public GIS matches every ward it has;
* a notification's village name loses the same suffixes before matching;
* normalisation touches case, punctuation and whitespace only - a
  transliteration difference is NOT normalised away, it is declared in
  `A.extent.village_name_aliases` or left unmatched with candidates.
"""
import importlib.util
from pathlib import Path

import pytest

pytest.importorskip('geopandas')

PATH = Path(__file__).resolve().parents[2] / 'cities/mumbai/extract/build_mmr_extent.py'
SPEC = importlib.util.spec_from_file_location('build_mmr_extent', PATH)
extent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extent)


def test_a_ward_row_resolves_to_its_town_without_the_type_suffix():
    assert extent.town_name('Thane (M Corp.) WARD NO.-0012') == 'Thane'
    assert extent.town_name('Greater Mumbai (M Corp.) (Part) WARD NO.-0101') == 'Greater Mumbai'
    assert extent.town_name('Vasai-Virar City (M Corp) WARD NO.-0003') == 'Vasai-Virar City'
    assert extent.town_name('Ambarnath(M Cl) WARD NO.-0001') == 'Ambarnath'
    assert extent.town_name('Boisar (CT) WARD NO.-0001') == 'Boisar'
    assert extent.town_name('Ghesar (N.V.)') == 'Ghesar'


def test_normalisation_is_case_punctuation_and_whitespace_only():
    assert extent.normal('Kalyan-Dombivli') == extent.normal('kalyan dombivli')
    assert extent.normal("Nandiwali Tarf Pachanand") == 'nandiwalitarfpachanand'
    # a transliteration is not the same name to this step
    assert extent.normal('Dombiwali') != extent.normal('Dombivli')
    assert extent.normal('Borghar') != extent.normal('Barghar')


def test_greater_mumbai_is_the_two_census_districts():
    assert extent.GREATER_MUMBAI_DISTRICTS == ('518', '519')
