"""Extract printed rail timetable cells with explicit unresolved semantics.

Multiple vertically stacked tables are separated by train-number header bands.
These are source cells, not service-day times or validated station associations.
Supplements overlap base timetables and must not be added as extra trains.
"""
from collections import Counter
import json
from pathlib import Path
import re

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar
import city
from extract_census_controls import source, write
from extract_wr_timetable import lines, matches

OUTPUT_INPUTS = {
    'data/processed/observed/cr_printed_timetable_cells.csv': ['data/raw/transit/cr_public_*.pdf'],
    'data/processed/observed/_cr_timetable_audit.json': ['data/raw/transit/cr_public_*.pdf'],
}


def time_matches(line):
    pattern = r'\d{1,2}:\d{2}'
    characters = list(line)
    text = ''.join(c.get_text() for c in characters)
    index = [c for c in characters for _ in c.get_text()]
    for match,cell in zip(re.finditer(pattern,text),matches(line,pattern)):
        glyphs = [c for c in index[match.start():match.end()] if isinstance(c,LTChar)]
        colours = [c.graphicstate.ncolor for c in glyphs]
        cell['has_white_glyphs'] = any(c in (1, (1,1,1), (0,0,0,0)) for c in colours)
        cell['glyph_fill_colours'] = [json.loads(v) for v in sorted({json.dumps(c) for c in colours})]
        yield cell


def main():
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    entries = [e for e in catalogue['sources'] if e['id'].startswith('cr_public_') and
               e['format']=='pdf' and e['id'] not in ('cr_public_abbreviations','cr_public_holidays_2026')]
    rows, audits = [], []
    for entry in entries:
        record, path = source(entry['id'],entry['category'])
        pages = []
        for number,page in enumerate(extract_pages(str(path)),start=1):
            page_lines = list(lines(page))
            headers = sorted([m for line in page_lines for m in matches(line,r'\d{5}')],key=lambda m:-m['y'])
            bands = []
            for cell in headers:
                if not bands or abs(cell['y']-bands[-1][0]['y']) > cell['height']/2:
                    bands.append([cell])
                else:
                    bands[-1].append(cell)
            if not bands:
                pages.append(dict(page=number,status='no_train_header',text=[l.get_text().strip() for l in page_lines]))
                continue
            all_times = [m for line in page_lines for m in time_matches(line)]
            # The 15-car PDF contains white 00:00 text on a white background.
            # Visual inspection confirms these are not printed departure times.
            # Quarantine white text for review rather than creating ghost trips.
            white_times = [m for m in all_times if m['has_white_glyphs']]
            times = [m for m in all_times if not m['has_white_glyphs']]
            page_bands, handled = [], set()
            for band_index,band in enumerate(bands):
                trains = sorted(band,key=lambda m:m['x'])
                if len(trains)<2 or len({m['text'] for m in trains})!=len(trains):
                    raise ValueError('Ambiguous train header: '+entry['id']+' page '+str(number))
                top = min(m['y'] for m in trains)
                bottom = bands[band_index+1][0]['y'] if band_index+1<len(bands) else 0
                left = trains[0]['x']
                label_edge = left-(trains[1]['x']-left)/2
                stations = []
                for line in page_lines:
                    if not (line.x0<label_edge and bottom<line.y1<top):
                        continue
                    # PDF text lines can merge a long station name with its
                    # first time or a passing marker. Read the name prefix;
                    # the time keeps its own glyph coordinates above.
                    name = re.split(r'\d|\u2026|\ufffd|\.\.\.',line.get_text(),maxsplit=1)[0].strip()
                    if not name or not re.search('[A-Za-z]',name) or re.search(r'TRAINS|CAR|SERVICE|TIME TABLE|TR.CODE',name,re.I):
                        continue
                    stations.append(dict(name=name,y=(line.y0+line.y1)/2,height=line.height))
                stations.sort(key=lambda m:-m['y'])
                if not stations:
                    raise ValueError('No station labels')
                used, emitted, unassigned = set(), 0, []
                for cell_index,cell in enumerate(times):
                    if not bottom<cell['y']<top:
                        continue
                    handled.add(cell_index)
                    station = min(stations,key=lambda s:abs(s['y']-cell['y']))
                    train_index = min(range(len(trains)),key=lambda i:abs(trains[i]['x']-cell['x']))
                    train = trains[train_index]
                    spacing = min(abs(train['x']-other['x']) for i,other in enumerate(trains) if i!=train_index)
                    if abs(station['y']-cell['y'])>max(station['height'],cell['height'])/2 or abs(train['x']-cell['x'])>spacing/2:
                        unassigned.append(cell)
                        continue
                    key = (train['text'],station['name'])
                    if key in used:
                        raise ValueError('Duplicate aligned train/station cell: '+repr((entry['id'],number,key)))
                    used.add(key)
                    hour,minute = map(int,cell['text'].split(':'))
                    if hour>23 or minute>59:
                        raise ValueError('Invalid printed clock time')
                    rows.append(dict(source_id=entry['id'],source_sha256=record['sha256'],source_page=number,
                                     table_band=band_index+1,train_number=train['text'],
                                     aligned_station_row_label=station['name'],station_row_order=stations.index(station)+1,
                                     printed_local_hhmm=cell['text'],source_x_pdf_pt=round(cell['x'],6),
                                     source_y_pdf_pt=round(cell['y'],6),source='published_timetable_cell',
                                     validation_status='station_calendar_vehicle_stopping_and_service_day_unresolved'))
                    emitted += 1
                page_bands.append(dict(train_numbers=[m['text'] for m in trains],station_rows=len(stations),
                                       extracted_cells=emitted,unassigned_time_cells=unassigned))
            notes = [dict(text=l.get_text().strip(),bbox_pdf_pt=list(l.bbox)) for l in page_lines
                     if re.search(r'SUN|SAT|HOLIDAY|NON AC|ONLY|AC#|LADIES|W\.?E\.?F|^X{1,2}$|^AC\s*#?$',l.get_text(),re.I)]
            pages.append(dict(page=number,bands=page_bands,source_time_text_cells=len(all_times),
                              nonwhite_time_text_cells=len(times),white_time_text_cells=white_times,
                              times_outside_bands=[m for i,m in enumerate(times) if i not in handled],calendar_and_vehicle_notes=notes))
        audits.append(dict(source_id=entry['id'],source_sha256=record['sha256'],pages=pages))
    rows.sort(key=lambda r:(r['source_id'],r['source_page'],r['table_band'],r['train_number'],r['station_row_order']))
    if not rows:
        raise ValueError('No printed timetable cells')
    write('cr_printed_timetable_cells.csv',rows)
    counts = dict(sorted(Counter(r['source_id'] for r in rows).items()))
    result = dict(status='evidence_only',extracted_cells_by_source=counts,sources=audits,
                  limitations=['AC and 15-car supplements overlap the base tables; do not add them as extra services.',
                               'White text cells are quarantined; PDF text extraction alone does not prove visual visibility.',
                               'Printed row alignment does not establish station identity or a stopping time.',
                               'Sunday/holiday and vehicle-substitution rules require train-specific joins.',
                               'Clock times still require service-day conversion and continuity validation.',
                               'Older base schedules require reconciliation with all later amendments.'])
    Path(city.path('data/processed/observed/_cr_timetable_audit.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(counts))


if __name__=='__main__':
    main()
