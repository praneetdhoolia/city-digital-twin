"""Read printed train/station cells without inventing calendars or stop times.

The result is an evidence table, not a runnable timetable. Calendar notes and
continuations remain attached to their source page for subsequent validation.
"""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
from statistics import median

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextLine
import city

OUTPUT_INPUTS = {
    'data/processed/observed/wr_printed_timetable_cells.csv': ['data/raw/rail/wr_public_timetable_attachment_*.pdf'],
    'data/processed/observed/_wr_timetable_audit.json': ['data/raw/rail/wr_public_timetable_attachment_*.pdf'],
}


def lines(node):
    if isinstance(node, LTTextLine):
        yield node
    elif hasattr(node, '__iter__'):
        for child in node:
            yield from lines(child)


def matches(line, pattern):
    characters = list(line)
    text = ''.join(c.get_text() for c in characters)
    # LTAnno contributes a space or newline; index these alongside real glyphs.
    index = [c for c in characters for _ in c.get_text()]
    for match in re.finditer(pattern, text):
        glyphs = [c for c in index[match.start():match.end()] if isinstance(c, LTChar)]
        if glyphs:
            yield dict(text=match.group(), x=(min(c.x0 for c in glyphs)+max(c.x1 for c in glyphs))/2,
                       y=median((c.y0+c.y1)/2 for c in glyphs), height=median(c.height for c in glyphs))


def main():
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    sources = [s for s in catalogue['sources'] if s['id'].startswith('wr_public_timetable_attachment_')]
    rows, audits = [], []
    for source in sources:
        # the pocket timetable (1, 2), the AC supplements (3, 4) and the Dahanu
        # Road services (5) print one layout: train numbers across, stations
        # down, a time per cell; the Harbour services sheet (6) is the older
        # 2022 layout and is read the same way where its cells align
        record_path = Path(city.path('data/raw/rail/provenance_' + source['id'] + '.json'))
        if not record_path.exists():
            audits.append(dict(source_id=source['id'], status='unobtained'))
            continue
        record = json.loads(record_path.read_text(encoding='utf-8'))['files'][0]
        path = Path(city.path(record['path']))
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                raise ValueError('Source hash mismatch: ' + source['id'])
        page_audits = []
        for number, page in enumerate(extract_pages(str(path)), start=1):
            page_lines = list(lines(page))
            trains = sorted([m for line in page_lines for m in matches(line, r'\b\d{5}\b')], key=lambda t:t['x'])
            if not trains:
                page_audits.append(dict(page=number, status='no_train_columns', text=[l.get_text().strip() for l in page_lines]))
                continue
            top = max(t['y'] for t in trains)
            trains = [t for t in trains if top-t['y'] < t['height']]
            if len({t['text'] for t in trains}) != len(trains):
                raise ValueError('Repeated train number on page ' + str(number))
            left = min(t['x'] for t in trains)
            header_y = min(t['y'] for t in trains)
            station_lines = [line for line in page_lines if line.x1 < left-trains[0]['height']
                             and line.y1 < header_y and not re.search(r'\d|TRAINS|CAR', line.get_text())]
            stations = sorted([dict(name=l.get_text().strip(), y=(l.y0+l.y1)/2, height=l.height)
                               for l in station_lines if l.get_text().strip()], key=lambda s:-s['y'])
            if not stations:
                raise ValueError('No station rows on page ' + str(number))
            time_cells = [m for line in page_lines for m in matches(line, r'\b\d{2}:\d{2}\b')]
            time_cells = [m for m in time_cells if m['y'] < header_y]
            used, page_rows, unassigned = set(), [], []
            for cell in time_cells:
                station = min(stations, key=lambda s:abs(s['y']-cell['y']))
                train = min(trains, key=lambda t:abs(t['x']-cell['x']))
                if abs(station['y']-cell['y']) > station['height']/2:
                    unassigned.append(cell)
                    continue
                # a station label can print twice on a sheet (arrival and
                # departure rows, or a station served twice); the row is the key
                key = (train['text'], stations.index(station))
                if key in used:
                    raise ValueError('Ambiguous duplicate train/station cell: ' + repr(key))
                used.add(key)
                hour, minute = map(int, cell['text'].split(':'))
                if hour > 23 or minute > 59:
                    raise ValueError('Invalid printed clock time')
                page_rows.append(dict(source_id=source['id'], source_sha256=record['sha256'], source_page=number,
                                      train_number=train['text'], aligned_station_row_label=station['name'],
                                      station_row_order=stations.index(station)+1, printed_local_hhmm=cell['text'],
                                      source_x_pdf_pt=round(cell['x'],6), source_y_pdf_pt=round(cell['y'],6),
                                      source='observed', stopping_status='unresolved',
                                      validation_status='printed_cell_only_calendar_and_stopping_unresolved'))
            notes = [dict(text=l.get_text().strip(), bbox_pdf_pt=list(l.bbox)) for l in page_lines
                     if re.search(r'SUN|SAT|HOLIDAY|NON AC|Condition|ONLY|NOT ON|HALT|CSMT|CSTM|^P\*?\s*$',l.get_text(),re.I)]
            page_audits.append(dict(page=number, train_columns=len(trains), station_rows=len(stations),
                                   printed_time_cells=len(time_cells), extracted_time_cells=len(page_rows),
                                   unassigned_time_cells=unassigned,
                                   calendar_and_vehicle_notes=notes,
                                   train_numbers=[t['text'] for t in trains]))
            rows.extend(page_rows)
        audits.append(dict(source_id=source['id'], source_sha256=record['sha256'], pages=page_audits))
    rows.sort(key=lambda r:(r['source_id'],r['source_page'],r['train_number'],r['station_row_order']))
    output = Path(city.path('data/processed/observed'))
    output.mkdir(parents=True,exist_ok=True)
    if not rows:
        raise ValueError('No printed timetable cells extracted')
    with (output/'wr_printed_timetable_cells.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    counts=Counter(r['source_id'] for r in rows)
    result=dict(schema_version=1, status='evidence_only', extracted_cells_by_source=dict(sorted(counts.items())),
                limitations=['Calendar exceptions are not yet assigned to individual trains.',
                             'Printed passing times and stopping times are not yet distinguished.',
                             'A row alignment is not proof of a station-time association: through-service notes can occupy the same row.',
                             'Clock times are not yet converted to service-day offsets across midnight.',
                             'Some services continue outside the printed station span; join continuation schedules.',
                             'Printed times are scheduled observations, not realised running times.',
                             'Train lengths, AC status and station coordinates still require validated joins.'], sources=audits)
    (output/'_wr_timetable_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result['extracted_cells_by_source']))


if __name__=='__main__':
    main()
