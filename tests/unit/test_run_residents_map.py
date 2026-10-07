"""A run carries its own residents map (#213), in the city's own vocabulary (#242).

`extract_metrics.home_lga()` resolved every run's residents through the city's
CURRENT `B1_synthetic_population.csv`, so a demand rebuild changed what an
older run's readings counted as a Newcastle resident. The launcher now writes
`_residents.csv.gz` beside the sampled plans and the readers prefer it. Since
8 October 2026 the table's columns, the zone-to-area join and the target area
come from the city's reader adapter (`residents_shape`), so the map is written
for any city that declares one and read by position for every city.
"""
import gzip
import os

import extract_metrics as em

SHAPE = dict(population='B1.csv', person_id='person_id', home_zone='home_sa1',
             zone_areas='sa1_to_lga.csv', zone='SA1_CODE21', area='lga_name',
             target='Newcastle', map_columns=('person_id', 'home_sa1', 'home_lga'))


def _city_tables(tmp_path, monkeypatch, shape=SHAPE):
    monkeypatch.setattr(em, '_RESIDENTS', shape)
    monkeypatch.setattr(em, 'POP', str(tmp_path / shape['population']))
    monkeypatch.setattr(em, 'ZONE_AREAS', str(tmp_path / shape['zone_areas']))


def test_the_runs_own_map_wins_over_the_city_table(tmp_path, monkeypatch):
    run = tmp_path / '20260101T000000_4it_25pct'
    run.mkdir()
    with gzip.open(run / em.RESIDENTS_FILE, 'wt', encoding='utf-8') as w:
        w.write('# backfilled 2026-01-01: a test\n')
        w.write('person_id,home_sa1,home_lga\n7,1,Newcastle\n8,2,Cessnock\n')
    em._HOME_LGA_CACHE.clear()
    got = em.home_lga(str(run))
    assert got == {'7': 'Newcastle', '8': 'Cessnock'}


def test_a_run_without_a_map_says_so_once(tmp_path, capsys, monkeypatch):
    run = tmp_path / '20260101T000000_4it_25pct'
    run.mkdir()
    em._HOME_LGA_CACHE.clear()
    em._RESIDENTS_WARNED.clear()
    _city_tables(tmp_path, monkeypatch)
    (tmp_path / 'B1.csv').write_text('person_id,home_sa1\n7,1\n', encoding='utf-8')
    (tmp_path / 'sa1_to_lga.csv').write_text('SA1_CODE21,lga_name\n1,Newcastle\n', encoding='utf-8')
    assert em.home_lga(str(run)) == {'7': 'Newcastle'}
    em.home_lga(str(run))
    out = capsys.readouterr().out
    assert out.count('WARNING') == 1 and '#213' in out


def test_write_residents_restricts_to_the_sample(tmp_path, monkeypatch):
    run = tmp_path / 'r'
    run.mkdir()
    _city_tables(tmp_path, monkeypatch)
    (tmp_path / 'B1.csv').write_text('person_id,home_sa1\n7,1\n8,1\n9,2\n', encoding='utf-8')
    (tmp_path / 'sa1_to_lga.csv').write_text('SA1_CODE21,lga_name\n1,Newcastle\n2,Maitland\n', encoding='utf-8')
    path, n = em.write_residents(str(run), {'7', '9'})
    assert n == 2 and os.path.exists(path)
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        assert f.readline() == 'person_id,home_sa1,home_lga\n'
    em._HOME_LGA_CACHE.clear()
    assert em.home_lga(str(run)) == {'7': 'Newcastle', '9': 'Maitland'}


def test_a_second_city_writes_its_own_vocabulary_and_reads_it_by_position(tmp_path, monkeypatch):
    """A leaf-keyed population and a tier table: the map says geography_id /
    tier, the readers see the same person -> target-area answer."""
    shape = dict(population='pop.csv', person_id='person_id', home_zone='geography_id',
                 zone_areas='extent.csv', zone='geography_id', area='tier', target='core',
                 map_columns=('person_id', 'geography_id', 'tier'))
    _city_tables(tmp_path, monkeypatch, shape)
    (tmp_path / 'pop.csv').write_text('person_id,household_id,geography_id\n1,1,27:519\n2,1,27:999\n',
                                      encoding='utf-8')
    (tmp_path / 'extent.csv').write_text('geography_id,tier\n27:519,core\n27:999,external\n',
                                         encoding='utf-8')
    run = tmp_path / 'r'
    run.mkdir()
    assert em.has_home_zone_table()
    path, n = em.write_residents(str(run))
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        assert f.read() == 'person_id,geography_id,tier\n1,27:519,core\n2,27:999,external\n'
    em._HOME_LGA_CACHE.clear()
    assert em.home_lga(str(run)) == {'1': 'core', '2': 'external'}


def test_a_city_without_a_residents_shape_has_no_home_zone_table(monkeypatch):
    monkeypatch.setattr(em, '_RESIDENTS', None)
    monkeypatch.setattr(em, 'POP', None)
    monkeypatch.setattr(em, 'ZONE_AREAS', None)
    assert em.has_home_zone_table() is False
