"""The reference city's reader-shape adapter returns the shapes the framework declares.

`config/schema/reader_shapes.json` declares what the framework's demand and
measurement readers consume; `cities/<city>/extract/reader_shapes.py` maps the
city's published vocabulary to it at read time. The plans builder's
`hts_mode_share` and the population synthesiser read nothing else, so a
mapping slip here moves the calibration target or the synthetic population
with no error anywhere. Pinned on tiny CSVs spelled as the published files are:

  mode_share_table()
    * only the base-year vintage at the survey's geography level is read;
    * the survey's significance asterisks and case are stripped before the
      label maps to a framework category, and an unmapped label is kept as
      `unmapped:<label>` so it still counts toward totals;
    * trips are summed per (area, category), and the linked share is the one
      published value, or None where there is not exactly one.

  residence_marginals(zone)
    * the declared keys, in the declared shapes and orders;
    * an unpublished column is None (ages) or 0 (cells), never invented;
    * occupation and income sum both sexes and every published age band;
    * a zone absent from any table is None.

The adapter's own label constants are read from the module rather than typed,
so the test holds the mapping, not the spelling. The module is loaded fresh
from its file for each test, with its city path resolver pointed at a
temporary directory; no package data is read.
"""
import importlib.util
import json
import os
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ADAPTER = os.path.join(REPO, 'cities', 'newcastle', 'extract', 'reader_shapes.py')
SHAPES = os.path.join(REPO, 'config', 'schema', 'reader_shapes.json')


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('reader_shapes_under_test', ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, '_city', types.SimpleNamespace(
        path=lambda rel: os.path.join(str(tmp_path), *rel.split('/'))))
    return mod


def _csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(','.join(header) + '\n')
        for r in rows:
            fh.write(','.join('' if v is None else str(v) for v in r) + '\n')


def _declared():
    with open(SHAPES, encoding='utf-8') as fh:
        return json.load(fh)['families']


# --------------------------------------------------------------------------
# mode_share_table
# --------------------------------------------------------------------------
def test_mode_share_table_maps_labels_and_filters_vintage(adapter, tmp_path):
    lab = adapter.mode_category_labels()
    vintage = adapter.survey_vintage()
    geo = adapter.SURVEY_GEOGRAPHY
    header = ['FINANCIAL_YEAR', 'geography', 'area_name', 'TRAVEL_MODE',
              'TRIPS_BY_MODE', 'MODE_SHARE']
    rows = [
        (vintage, geo, 'AreaA', lab['car_driver'] + '*', 100, 55.5),
        (vintage, geo, 'AreaA', '  ' + lab['car_driver'].upper(), 20, None),
        (vintage, geo, 'AreaA', lab['walk_only'], 30, 12.0),
        (vintage, geo, 'AreaA', 'Teleport', 5, None),
        (vintage, geo, 'AreaB', lab['public_transport'] + '**', 7, 4.5),
        ('1999/00', geo, 'AreaA', lab['car_driver'], 9999, 99.0),   # other vintage
        (vintage, 'sa3', 'AreaA', lab['car_driver'], 8888, 88.0),   # other level
    ]
    _csv(str(tmp_path / 'data' / 'processed' / 'hts' / 'hts_mode.csv'), header, rows)
    table = adapter.mode_share_table()
    by = {(r['area_name'], r['mode_category']): r for r in table}
    assert set(by) == {('AreaA', 'car_driver'), ('AreaA', 'walk_only'),
                       ('AreaA', 'unmapped:teleport'), ('AreaB', 'public_transport')}
    assert by[('AreaA', 'car_driver')]['trips'] == 120.0
    assert by[('AreaA', 'car_driver')]['linked_share_pct'] == 55.5
    assert by[('AreaA', 'walk_only')]['linked_share_pct'] == 12.0
    assert by[('AreaA', 'unmapped:teleport')]['linked_share_pct'] is None
    assert by[('AreaB', 'public_transport')]['trips'] == 7.0
    declared = _declared()['hts_mode_share']
    for r in table:
        assert set(r) == set(declared['columns'])
        cat = r['mode_category']
        assert cat in declared['mode_categories'] or cat.startswith('unmapped:')


def test_two_published_shares_for_one_category_are_not_a_share(adapter, tmp_path):
    lab = adapter.mode_category_labels()
    header = ['FINANCIAL_YEAR', 'geography', 'area_name', 'TRAVEL_MODE',
              'TRIPS_BY_MODE', 'MODE_SHARE']
    rows = [(adapter.survey_vintage(), adapter.SURVEY_GEOGRAPHY, 'AreaA',
             lab['other'], 1, 2.0),
            (adapter.survey_vintage(), adapter.SURVEY_GEOGRAPHY, 'AreaA',
             lab['other'] + '*', 1, 3.0)]
    _csv(str(tmp_path / 'data' / 'processed' / 'hts' / 'hts_mode.csv'), header, rows)
    (row,) = adapter.mode_share_table()
    assert row['mode_category'] == 'other'
    assert row['trips'] == 2.0
    assert row['linked_share_pct'] is None


def test_every_declared_category_has_a_label(adapter):
    assert sorted(adapter.mode_category_labels()) == \
        sorted(_declared()['hts_mode_share']['mode_categories'])


# --------------------------------------------------------------------------
# residence_marginals
# --------------------------------------------------------------------------
def _census(adapter, tmp_path):
    key = adapter.CENSUS_ZONE_KEY
    d = str(tmp_path / 'data' / 'processed' / 'census')

    def table(name, cols, rows):
        _csv(os.path.join(d, 'census2021_%s_SA1.csv' % name),
             [key, 'zone_tier'] + cols, rows)

    edu_att = [g[3] for g in adapter.EDU_GROUPS]
    edu_pop = [g[4] for g in adapter.EDU_GROUPS]
    table('G01', edu_att + edu_pop + [adapter.EDU_25OV_ATT] + adapter.EDU_25OV_POP,
          [(101, 'core') + tuple(range(1, 5)) + tuple(range(10, 50, 10)) + (6,)
           + (1,) * len(adapter.EDU_25OV_POP)])
    table('G04A', ['Age_yr_0_M', 'Age_yr_0_F', 'Age_yr_1_M'],
          [(101, 'core', 5, 6, None)])
    table('G04B', [adapter.G04_GROUPED[0][2] % 'M', adapter.G04_GROUPED[0][2] % 'F'],
          [(101, 'core', 2, 3)])
    table('G34', adapter.VEHICLE_COLS[:2], [(101, 'core', 40, 50)])
    table('G35', adapter.HOUSEHOLD_SIZE_COLS[:1], [(101, 'core', 10)])
    table('G36', [c for _, c in adapter.DWELLING_TYPES], [(101, 'core', 1, 2, 3, 4)])
    band = adapter.LF_BANDS[0][0]
    table('G46A', ['M_Tot_Emp_%s' % band, 'M_Tot_LF_%s' % band],
          [(101, 'core', 3, 4), (202, 'ring', 100, 100)])
    table('G46B', ['F_Tot_Emp_%s' % band], [(101, 'core', 7), (202, 'ring', 100)])
    inc0, inc_top = adapter.INCOME_BANDS[0], adapter.INCOME_BANDS[-1]
    ab = adapter.INCOME_AGE_BANDS
    table('G17A', ['M_%s_income_%s' % (inc0, ab[0])], [(101, 'core', 4)])
    table('G17B', ['F_%s_%s' % (inc_top, ab[2]), 'M_%s_%s' % (inc_top, ab[3])],
          [(101, 'core', 1, 2)])
    occ = adapter.OCCUPATION_LABELS[0]
    ob = adapter.OCCUPATION_BANDS
    table('G60A', ['M%s_%s' % (ob[0], occ)], [(101, 'core', 1)])
    table('G60B', ['F%s_%s' % (ob[2], occ), 'F%s_%s' % (ob[3], occ)],
          [(101, 'core', 2, None)])


def test_residence_marginals_has_the_declared_shape(adapter, tmp_path):
    _census(adapter, tmp_path)
    m = adapter.residence_marginals('101')
    declared = _declared()['census_attributes']['residence_marginals_shape']
    assert set(m) == set(declared)
    assert len(m['age_single_year']) == 80
    assert len(m['age_grouped']) == len(adapter.G04_GROUPED)
    assert len(m['household_size']) == 6 and len(m['vehicles']) == 5
    assert len(m['dwellings']) == len(adapter.dwelling_types())
    assert len(m['occupation']) == len(adapter.occupation_labels())
    assert len(m['income']) == len(adapter.income_band_labels())
    assert set(m['labour_force']) == {(s, b) for s in 'MF'
                                      for b, _, _ in adapter.labour_force_bands()}
    assert set(m['education']) == {g for g, _, _ in adapter.education_groups()}


def test_residence_marginals_reports_counts_as_published(adapter, tmp_path):
    _census(adapter, tmp_path)
    m = adapter.residence_marginals('101')
    # ages: published, blank-in-a-published-column and unpublished are distinct
    assert m['age_single_year'][0] == (0, 5.0, 6.0)
    assert m['age_single_year'][1] == (1, None, None)
    assert m['age_single_year'][2] == (2, None, None)
    lo, hi = adapter.G04_GROUPED[0][:2]
    assert m['age_grouped'][0] == (lo, hi, 2.0, 3.0)
    assert m['age_over'] == (100, None, None)
    # dwelling-level counts: an unpublished column is 0, not None
    assert list(m['household_size']) == [10, 0, 0, 0, 0, 0]
    assert list(m['vehicles']) == [40, 50, 0, 0, 0]
    assert list(m['dwellings']) == [1, 2, 3, 4]
    band = adapter.LF_BANDS[0][0]
    assert m['labour_force'][('M', band)] == (3.0, 4.0, 0.0, 0.0, 0.0, 0.0)
    assert m['labour_force'][('F', band)] == (7.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert m['education'][adapter.EDU_GROUPS[0][0]] == (1.0, 10.0)
    assert m['education']['25_ov'] == (6.0, float(len(adapter.EDU_25OV_POP)))
    # both sexes, every band, a blank cell adds nothing
    assert m['occupation'] == [3.0] + [0.0] * (len(adapter.OCCUPATION_LABELS) - 1)
    assert m['income'][0] == 4.0 and m['income'][-1] == 3.0
    assert sum(m['income'][1:-1]) == 0.0


def test_an_absent_zone_is_none(adapter, tmp_path):
    _census(adapter, tmp_path)
    assert adapter.residence_marginals('999') is None
    # present in the labour-force table only: absent from the others, so None
    assert adapter.residence_marginals('202') is None


def test_region_fallback_sums_the_core_zones_only(adapter, tmp_path):
    _census(adapter, tmp_path)
    band = adapter.LF_BANDS[0][0]
    totals = adapter.region_labour_force_totals()
    assert totals[('M', band)][:2] == (3.0, 4.0)
    assert totals[('F', band)][0] == 7.0
