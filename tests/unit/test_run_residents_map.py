"""A run carries its own residents map (#213).

`extract_metrics.home_lga()` resolved every run's residents through the city's
CURRENT `B1_synthetic_population.csv`, so a demand rebuild changed what an
older run's readings counted as a Newcastle resident. The launcher now writes
`_residents.csv.gz` beside the sampled plans and the readers prefer it.
"""
import gzip
import os

import extract_metrics as em


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
    monkeypatch.setattr(em, 'POP', str(tmp_path / 'B1.csv'))
    monkeypatch.setattr(em, 'SA1_LGA', str(tmp_path / 'sa1_to_lga.csv'))
    (tmp_path / 'B1.csv').write_text('person_id,home_sa1\n7,1\n', encoding='utf-8')
    (tmp_path / 'sa1_to_lga.csv').write_text('SA1_CODE21,lga_name\n1,Newcastle\n', encoding='utf-8')
    assert em.home_lga(str(run)) == {'7': 'Newcastle'}
    em.home_lga(str(run))
    out = capsys.readouterr().out
    assert out.count('WARNING') == 1 and '#213' in out


def test_write_residents_restricts_to_the_sample(tmp_path, monkeypatch):
    run = tmp_path / 'r'
    run.mkdir()
    monkeypatch.setattr(em, 'POP', str(tmp_path / 'B1.csv'))
    monkeypatch.setattr(em, 'SA1_LGA', str(tmp_path / 'sa1_to_lga.csv'))
    (tmp_path / 'B1.csv').write_text('person_id,home_sa1\n7,1\n8,1\n9,2\n', encoding='utf-8')
    (tmp_path / 'sa1_to_lga.csv').write_text('SA1_CODE21,lga_name\n1,Newcastle\n2,Maitland\n', encoding='utf-8')
    path, n = em.write_residents(str(run), {'7', '9'})
    assert n == 2 and os.path.exists(path)
    em._HOME_LGA_CACHE.clear()
    assert em.home_lga(str(run)) == {'7': 'Newcastle', '9': 'Maitland'}
