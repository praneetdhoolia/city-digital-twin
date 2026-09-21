"""Join visible supplement headers to trains; retain conditional calendar rules."""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar
import city
from extract_census_controls import source, write
from extract_population_projections import page_text
from extract_wr_timetable import lines, matches

SOURCES = ('cr_public_main_ac_20250416', 'cr_public_harbour_ac_20260501',
           'cr_public_main_15_car_20260815')
OUTPUT_INPUTS = {
    'data/processed/observed/cr_service_markers.csv': [
        'data/raw/transit/cr_public_main_ac_*.pdf', 'data/raw/transit/cr_public_harbour_ac_*.pdf',
        'data/raw/transit/cr_public_main_15_car_*.pdf', 'data/raw/transit/cr_public_abbreviations_*.pdf',
        'data/processed/observed/cr_printed_timetable_cells.csv'],
    'data/processed/acquisition/cr_service_marker_audit.json': [
        'data/raw/transit/cr_public_main_ac_*.pdf', 'data/raw/transit/cr_public_harbour_ac_*.pdf',
        'data/raw/transit/cr_public_main_15_car_*.pdf', 'data/raw/transit/cr_public_abbreviations_*.pdf',
        'data/processed/observed/cr_printed_timetable_cells.csv'],
}


def main():
    legend_record, legend_path = source('cr_public_abbreviations', 'transit')
    legend = ' '.join(page_text(legend_path, 2).split())
    for rule in ('will not run on Sunday / Holiday', 'will not run on Saturday / Sunday / Holiday'):
        if rule not in legend:
            raise ValueError('CR calendar legend changed')
    with Path(city.path('data/processed/observed/cr_printed_timetable_cells.csv')).open(encoding='utf-8') as stream:
        times = list(csv.DictReader(stream))
    by_page = defaultdict(list)
    for row in times:
        by_page[(row['source_id'], int(row['source_page']))].append(row)
    rows, page_audits = [], []
    for sid in SOURCES:
        record, path = source(sid, 'transit')
        for number, page in enumerate(extract_pages(str(path)), 1):
            page_lines = list(lines(page))
            text = ' '.join(' '.join(line.get_text().split()) for line in page_lines)
            trains = sorted([m for line in page_lines for m in matches(line, r'\b\d{5}\b')], key=lambda m: m['x'])
            if not trains or len({t['text'] for t in trains}) != len(trains):
                raise ValueError('Missing or duplicate train header')
            if max(t['y'] for t in trains) - min(t['y'] for t in trains) > min(t['height'] for t in trains) / 2:
                raise ValueError('More than one train header band needs separate handling')
            time_rows = by_page[(sid, number)]
            if {r['train_number'] for r in time_rows} != {t['text'] for t in trains}:
                raise ValueError('Supplement headers do not match extracted timetable trains')
            if {r['source_sha256'] for r in time_rows} != {record['sha256']}:
                raise ValueError('Stale timetable extraction source hash')
            bottom = max(float(r['source_y_pdf_pt']) for r in time_rows)
            top = min(t['y'] for t in trains)
            cells = {t['text']: {'vehicle': [], 'calendar': []} for t in trains}
            for line in page_lines:
                for kind, pattern in (('vehicle', r'\b(?:AC\s*#?|\d{1,2}\s*C\b)'),
                                      ('calendar', r'\bX{1,2}\b')):
                    for cell in matches(line, pattern):
                        if not bottom < cell['y'] < top:
                            continue
                        glyphs = [c for c in line if isinstance(c, LTChar)
                                  and c.x0 <= cell['x'] <= c.x1]
                        if any(c.graphicstate.ncolor in (1, (1, 1, 1), (0, 0, 0, 0)) for c in glyphs):
                            raise ValueError('White marker text requires visual review')
                        train = min(trains, key=lambda t: abs(t['x'] - cell['x']))
                        spacing = min(abs(train['x'] - t['x']) for t in trains if t is not train)
                        if abs(train['x'] - cell['x']) >= spacing / 2:
                            raise ValueError('Ambiguous train marker column')
                        cells[train['text']][kind].append(cell)
            harbour = sid == 'cr_public_harbour_ac_20260501'
            fifteen = sid == 'cr_public_main_15_car_20260815'
            if harbour:
                if not all(part in text for part in ('will not run on Sundays/Nominated Holidays',
                                                      'All of the above services running on Sunday/ Nominated Holidays will run',
                                                      'with Non AC rake.')):
                    raise ValueError('Harbour substitution/cancellation wording changed')
            elif not fifteen:
                if 'services running on Saturday/Sunday/Nominated Holidays will run as Non AC.' not in text:
                    raise ValueError('Main-line AC substitution wording changed')
            for train in trains:
                markers = cells[train['text']]
                if len(markers['vehicle']) != 1 or len(markers['calendar']) > 1:
                    raise ValueError('Missing or duplicate marker: ' + sid + ' ' + train['text'])
                vehicle = re.sub(r'\s+', '', markers['vehicle'][0]['text'])
                calendar = markers['calendar'][0]['text'] if markers['calendar'] else ''
                if vehicle not in (('15C',) if fifteen else ('AC', 'AC#')):
                    raise ValueError('Unexpected supplement vehicle marker')
                substitutions = ('Sunday;nominated_holiday' if harbour else
                                 'Saturday;Sunday;nominated_holiday' if vehicle == 'AC#' else '')
                rows.append(dict(source='published_service_marker', source_id=sid,
                                 source_sha256=record['sha256'], source_page=number,
                                 train_number=train['text'], vehicle_marker_as_printed=markers['vehicle'][0]['text'],
                                 calendar_marker_as_printed=calendar, formation_cars=15 if fifteen else '',
                                 climate_control_as_printed='AC' if vehicle.startswith('AC') else 'not_stated_by_marker',
                                 excludes_saturday_by_marker=int(calendar == 'XX'),
                                 excludes_sunday_by_marker=int(bool(calendar)),
                                 excludes_nominated_holiday_by_marker=int(bool(calendar)),
                                 non_ac_substitution_days_when_running=substitutions,
                                 exclusion_precedence='cancellation_precedes_rake_substitution',
                                 calendar_legend_source_id=sid if harbour else 'cr_public_abbreviations',
                                 calendar_legend_sha256=record['sha256'] if harbour else legend_record['sha256'],
                                 source_header_x_pdf_pt=round(train['x'], 6),
                                 effective_date_status='retain_source_vintage_reconcile_later_amendments',
                                 service_identity_status='supplement_overlay_not_additional_departure',
                                 operational_calendar_status='holiday_dates_and_complete_calendar_not_expanded'))
            page_audits.append(dict(source_id=sid, page=number, train_headers=len(trains),
                                    vehicle_markers=sum(len(v['vehicle']) for v in cells.values()),
                                    cancellation_markers=sum(len(v['calendar']) for v in cells.values())))
    rows.sort(key=lambda r: (r['source_id'], r['source_page'], r['train_number']))
    seen = set()
    for row in rows:
        key = (row['source_id'], row['train_number'])
        if key in seen:
            raise ValueError('Duplicate train within supplement')
        seen.add(key)
    write('cr_service_markers.csv', rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['train_number']].append(row['source_id'])
    audit = dict(rows=len(rows), rows_by_source=dict(sorted(Counter(r['source_id'] for r in rows).items())),
                 pages=page_audits,
                 cross_supplement_train_overlaps={k: v for k, v in sorted(grouped.items()) if len(v) > 1},
                 limitations=[
                     'These records overlay timetables; they must not be appended as new departures.',
                     'No cancellation marker means only that these footnotes do not exclude that day, not proof of daily operation.',
                     'AC# substitution applies only when the service operates; X/XX cancellation takes precedence.',
                     'An AC label does not specify coach count, seating, standing density or rake serial number.',
                     'A 15C label establishes the published formation only; it does not establish an AC/non-AC design or compartment capacity.',
                     'Main-line AC effective date is in its download filename; the printed pages do not establish it independently.',
                     'Nominated holiday dates, later amendments, base-timetable reconciliation and service-day time conversion remain unresolved.',
                 ])
    Path(city.path('data/processed/acquisition/cr_service_marker_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('rows', 'rows_by_source', 'cross_supplement_train_overlaps')}))


if __name__ == '__main__':
    main()
