"""The ninth report's reader defects, each with the failure it names.

Three instruments read something other than the run they were pointed at
(14 September 2026, findings 1, 3 and 4), and none of them failed a check:

  * the transit schedule was resolved through the CITY's assembled copy,
    which a network rebuild overwrites, so the only result read heavy rail 0
    after the F34 footpath rebuild while its own `_fit.json` said +225 %;
  * the innovation cutoff was `fraction x last`, which is MATSim's formula
    only when `firstIteration` is 0 - a warm-started arm was judged relaxed
    sixty iterations before innovation stopped;
  * the freight_train row counted the scheduled closures against a target
    that includes the derived freight movements, a 22.7 % shortfall on every
    run that was bookkeeping.

Each test builds its own run directory; nothing here reads `results/`.
"""
import gzip
import io
import json
import os

import pytest

import extract_metrics as em
import iteration_reading as reading


SCHEDULE = '''<?xml version="1.0" encoding="UTF-8"?>
<transitSchedule>
 <transitStops>
  <stopFacility id="s1" x="0" y="0" name="Hamilton Station Platform 1"/>
 </transitStops>
 <transitLine id="L1">
  <transitRoute id="R1"><transportMode>rail</transportMode></transitRoute>
 </transitLine>
</transitSchedule>
'''


def _run_dir(tmp_path, own_schedule, config_path):
    run = tmp_path / 'run'
    (run / 'output').mkdir(parents=True)
    with io.open(str(run / 'config.xml'), 'w', encoding='utf-8') as fh:
        fh.write('<config><param name="transitScheduleFile" value="%s"/></config>'
                 % config_path)
    if own_schedule:
        with gzip.open(str(run / 'output' / 'output_transitSchedule.xml.gz'),
                       'wt', encoding='utf-8') as fh:
            fh.write(SCHEDULE)
    return str(run)


def test_the_schedule_is_the_run_s_own_before_the_city_s(tmp_path):
    """A run that reached its end carries its schedule; the city's copy - the
    one a rebuild overwrites - is not opened even when the config names it."""
    run = _run_dir(tmp_path, own_schedule=True,
                   config_path=str(tmp_path / 'does-not-exist.xml.gz'))
    em._SCHEDULE_CACHE.clear()
    stops, modes = em._schedule_index(run)
    assert stops == {'s1': 'Hamilton Station Platform 1'}
    assert modes == {('L1', 'R1'): 'rail'}
    assert em.SCHEDULE_SOURCE[run] == 'run'


def test_a_stopped_run_falls_back_to_the_config_path_and_says_so(tmp_path, capsys):
    """A run stopped before its end has no output schedule; the config path is
    read and the fallback is announced, because a stop that fails to resolve
    through it is a rebuild, not a modelled zero."""
    city = tmp_path / 'city_schedule.xml.gz'
    with gzip.open(str(city), 'wt', encoding='utf-8') as fh:
        fh.write(SCHEDULE)
    run = _run_dir(tmp_path, own_schedule=False, config_path=str(city))
    em._SCHEDULE_CACHE.clear()
    stops, _ = em._schedule_index(run)
    assert stops == {'s1': 'Hamilton Station Platform 1'}
    assert em.SCHEDULE_SOURCE[run] == 'city'
    assert 'CITY' in capsys.readouterr().err


@pytest.mark.parametrize('first,last,fraction,expected', [
    (0, 300, 0.8, 240),      # the cold arm: unchanged
    (300, 600, 0.8, 540),    # the warm-started arm the report names
    (100, 300, 0.8, 260),    # #192's own example
    (0, 250, 0.8, 200),      # the horizon declared 14 September 2026
])
def test_innovation_off_after_counts_from_first_iteration(first, last, fraction, expected):
    assert reading.innovation_off_after(first, last, fraction) == expected


def test_innovation_off_after_is_none_without_its_inputs():
    assert reading.innovation_off_after(None, 300, 0.8) is None
    assert reading.innovation_off_after(0, None, 0.8) is None


def test_the_table_cache_is_bounded(tmp_path):
    """Thirty iterations of a 25 % arm's trips table would otherwise sit in
    one process for the gate watcher's lifetime."""
    reading.clear()
    run = tmp_path / 'run'
    for it in range(reading.CACHE_TABLES + 3):
        d = run / 'output' / 'ITERS' / ('it.%d' % it)
        d.mkdir(parents=True)
        with gzip.open(str(d / ('%d.trips.csv.gz' % it)), 'wt', encoding='utf-8') as fh:
            fh.write('person;trip_id\np;%d\n' % it)
    for it in range(reading.CACHE_TABLES + 3):
        reading.table(str(run), 'trips', it)
    assert len(reading._CACHE) == reading.CACHE_TABLES
    newest = (os.path.abspath(str(run)), 'trips', reading.CACHE_TABLES + 2)
    assert newest in reading._CACHE
    reading.clear()


def test_freight_train_counts_scheduled_plus_the_run_s_own_freight(tmp_path, monkeypatch):
    """The modelled movements are the scheduled closures plus the freight
    closures THE RUN carried, read from its own values snapshot."""
    import report_mode_ridership as rmr
    report = tmp_path / '_crossings_report.json'
    report.write_text(json.dumps({
        'closures_per_site': {'A': 110, 'B': 203},
        'freight_closures_per_day': {'A': 44, 'B': 48}}), encoding='utf-8')
    monkeypatch.setattr(rmr._city, 'path', lambda rel: str(report))
    # the run that carried the freight closures
    run = tmp_path / 'run'
    run.mkdir()
    (run / '_config.json').write_text(json.dumps({
        'values': {'A.crossings.freight_closures_per_day': {'A': 44, 'B': 48}}}),
        encoding='utf-8')
    assert rmr.crossing_movements(str(run)) == 405.0
    # a run made when the registry said no freight crossed: scored on what it ran
    old = tmp_path / 'old'
    old.mkdir()
    (old / '_config.json').write_text(json.dumps({
        'values': {'A.crossings.freight_closures_per_day': 0}}), encoding='utf-8')
    assert rmr.crossing_movements(str(old)) == 313.0
    # no snapshot at all: the report's own value
    assert rmr.crossing_movements(None) == 405.0
