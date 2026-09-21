"""The published daily mode splits of the MMR and of Greater Mumbai (9.204).

Two acquired executive summaries publish the observed main-mode split of
daily trips - the series the first per-mode targets are derived from:

  * the Updation of the Comprehensive Transportation Study for the MMR
    (`cts_2021_mirror`): Table 6-8, the 2017 daily motorised mode split of the
    MMR in trips per day (18.78 million) with its shares, and the household
    survey finding that the active modes (walking and cycling) are about 47 %
    of all trips (section 2);
  * the Comprehensive Mobility Plan for Greater Mumbai (`mumbai_cmp_summary`):
    Table 4-9, the daily motorised mode split of Greater Mumbai for 2005 (the
    CTS for MMR study) and 2014 (the CMP survey), trips per day and shares.

The tables are read from the PDF text (`pdftotext -layout`, poppler 24 or
later - run from PowerShell, 9.201), every cell as printed, and written one
row per (area, year, mode). Nothing is rescaled: the shares are the
publications' own, over MOTORISED trips; the active share is over ALL trips
and is its own row. Deriving a target per simulated mode from these - which
publication, which year, how the taxi/rickshaw and metro rows map, how the
active share splits into walk and bicycle - is the target builder's, with the
record; this step only transcribes.
"""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import city

_spec = importlib.util.spec_from_file_location(
    'extract_census_controls', Path(__file__).with_name('extract_census_controls.py'))
_controls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_controls)
source = _controls.source

OUTPUT_INPUTS = {
    'data/processed/observed/published_mode_splits.csv': [
        'data/raw/planning/cts_2021_mirror_*.pdf', 'data/raw/demand/mumbai_cmp_summary_*.pdf'],
    'data/processed/observed/_published_mode_splits_audit.json': [
        'data/raw/planning/cts_2021_mirror_*.pdf', 'data/raw/demand/mumbai_cmp_summary_*.pdf'],
}
OUT = 'data/processed/observed/published_mode_splits.csv'
AUDIT = 'data/processed/observed/_published_mode_splits_audit.json'
COLUMNS = ['source_id', 'source_sha256', 'source_pdf_page', 'table', 'area', 'survey_year', 'mode_raw',
           'trips_per_day', 'share_pct', 'share_basis', 'status']
CTS_MODES = ('Metro & Mono', 'Train', 'Bus', 'Rickshaw', 'Taxi', 'Two-Wheeler', 'Car', 'Total',
             'PV (Car & TW)', 'IPT (Auto & Taxi)', 'PT (Train & Bus)')
CMP_MODES = ('Car', 'Two Wheeler', 'Auto Rickshaw', 'Taxi', 'BUS', 'Suburban', 'Metro & Mono', 'Total', 'PV', 'IPT', 'PT')


def pages(path):
    text = subprocess.run(['pdftotext', '-layout', str(path), '-'], check=True,
                          capture_output=True).stdout.decode('utf-8', errors='replace')
    return text.split('\f')


def number(cell):
    return float(cell.replace(',', ''))


def cts_table(pages_text, sid, sha):
    """Table 6-8: '<mode> <trips millions> <share%>' rows on the page that holds it."""
    rows, page_no = [], None
    for i, page in enumerate(pages_text):
        if 'Table 6-8' in page and 'Motorized Mode Split' in page:
            page_no = i + 1
            for mode in CTS_MODES:
                m = re.search(r'^\s*%s\s+([\d.,]+)\s+([\d.]+)%%' % re.escape(mode), page, re.M)
                if not m:
                    raise SystemExit('CTS Table 6-8: no row for %r on page %d' % (mode, page_no))
                rows.append(dict(source_id=sid, source_sha256=sha, source_pdf_page=page_no,
                                 table='Table 6-8 Daily Mode Split, Mumbai Metropolitan Region, 2017 (CTS Updation)',
                                 area='Mumbai Metropolitan Region', survey_year=2017, mode_raw=mode,
                                 trips_per_day=int(round(number(m.group(1)) * 1_000_000)),
                                 share_pct=number(m.group(2)), share_basis='motorised main-mode trips per day',
                                 status='observed_published_table'))
            break
    if page_no is None:
        raise SystemExit('CTS Table 6-8 not found')
    # the household survey's active share, section 2: "about 47%"
    for i, page in enumerate(pages_text):
        m = re.search(r'major transportation mode in MMR \(about (\d+)%\) was noted to be the active modes', page)
        if m:
            rows.append(dict(source_id=sid, source_sha256=sha, source_pdf_page=i + 1,
                             table='Section 2 household interview survey findings',
                             area='Mumbai Metropolitan Region', survey_year=2017, mode_raw='Active modes (walking / cycling)',
                             trips_per_day='', share_pct=float(m.group(1)), share_basis='all main-mode trips (approximate, as printed)',
                             status='observed_published_statement'))
            break
    else:
        raise SystemExit('CTS active-mode statement not found')
    return rows


def cmp_table(pages_text, sid, sha):
    """Table 4-9: '<mode> <trips 2005> <%> <trips 2014> <%>' (Metro & Mono has 2014 only)."""
    rows, page_no = [], None
    for i, page in enumerate(pages_text):
        if 'Table 4-9' in page and 'Daily Mode Split, Greater Mumbai' in page and 'Trips per day' in page:
            page_no = i + 1
            for mode in CMP_MODES:
                m = re.search(r'^\s*%s\s+([\d,]+)\s+([\d.]+)%%\s+([\d,]+)\s+([\d.]+)%%' % re.escape(mode), page, re.M)
                if m:
                    cells = [(2005, m.group(1), m.group(2)), (2014, m.group(3), m.group(4))]
                else:
                    m = re.search(r'^\s*%s\s+([\d,]+)\s+([\d.]+)%%' % re.escape(mode), page, re.M)
                    if not m:
                        raise SystemExit('CMP Table 4-9: no row for %r on page %d' % (mode, page_no))
                    cells = [(2014, m.group(1), m.group(2))]
                for year, trips, share in cells:
                    rows.append(dict(source_id=sid, source_sha256=sha, source_pdf_page=page_no,
                                     table='Table 4-9 Daily Mode Split, Greater Mumbai: CTS for MMR (2005-08) and CMP (2014-16)',
                                     area='Greater Mumbai', survey_year=year, mode_raw=mode,
                                     trips_per_day=int(number(trips)), share_pct=number(share),
                                     share_basis='motorised main-mode trips per day', status='observed_published_table'))
            break
    if page_no is None:
        raise SystemExit('CMP Table 4-9 not found')
    return rows


def main():
    rows, audit_sources = [], []
    for sid, category, reader in (('cts_2021_mirror', 'planning', cts_table),
                                  ('mumbai_cmp_summary', 'demand', cmp_table)):
        record, path = source(sid, category)
        audit_sources.append(dict(source_id=sid, sha256=record['sha256'], path=record['path']))
        rows.extend(reader(pages(path), sid, record['sha256']))
    out = Path(city.path(OUT))
    with out.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    # the table's own arithmetic, checked as printed
    checks = {}
    for area, year in (('Mumbai Metropolitan Region', 2017), ('Greater Mumbai', 2005), ('Greater Mumbai', 2014)):
        parts = [r for r in rows if r['area'] == area and r['survey_year'] == year and r['trips_per_day'] != ''
                 and r['mode_raw'] not in ('Total', 'PV (Car & TW)', 'IPT (Auto & Taxi)', 'PT (Train & Bus)', 'PV', 'IPT', 'PT')]
        total = [r for r in rows if r['area'] == area and r['survey_year'] == year and r['mode_raw'] == 'Total']
        checks['%s %d' % (area, year)] = dict(
            modes=len(parts), sum_of_mode_trips=sum(r['trips_per_day'] for r in parts),
            printed_total=total[0]['trips_per_day'] if total else None,
            sum_of_mode_shares_pct=round(sum(r['share_pct'] for r in parts), 1))
    audit = dict(source='observed', rows=len(rows), sources=audit_sources, arithmetic_as_printed=checks,
                 limitations=['Shares are the publications\' own over MOTORISED main-mode trips; the active (walk/cycle) '
                              'share is a separate statement over all trips and is approximate as printed.',
                              'A multimodal trip is classified by its main mode (train or metro when one is boarded), as the '
                              'CTS states; access and egress legs are not trips here.',
                              'The MMR 2017 and Greater Mumbai 2014 surveys are different areas and years; neither is the '
                              'base year, and no projection is applied here.',
                              'No target is derived here: the mapping of Rickshaw/Taxi, Metro & Mono and the active share '
                              'onto the simulated modes is the target builder\'s, with the record.'])
    Path(city.path(AUDIT)).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n',
                                      encoding='utf-8', newline='\n')
    print(json.dumps(checks, indent=1))
    print('wrote %d rows to %s' % (len(rows), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
