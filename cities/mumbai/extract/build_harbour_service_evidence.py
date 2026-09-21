"""Resolve overlapping Harbour tables into one traceable service candidate each.

This is a dated evidence assembly, not an operating calendar or MATSim feed.
Original glyph cells stay unchanged. Source references accompany every resolved
time, and incomplete external branches remain ineligible for schedule export.
"""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
from statistics import median

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar
import city
from extract_census_controls import source, write
from extract_wr_timetable import lines, matches

DOWN = 'cr_public_harbour_down_20260501'
UP = 'cr_public_harbour_up_20260501'
AC = 'cr_public_harbour_ac_20260501'
THB = 'cr_public_trans_harbour_20240113'

# These names identify the same seven shared stations in the overlapping
# official tables. Every shared train/time pair is checked below.
SHARED_STATIONS = {
    'nerul': 'NEU', 'seawoods darave karave': 'SWDV', 'seawood darave karave': 'SWDV',
    'belapur cbd': 'BEPR', 'kharghar': 'KHAG', 'mansarovar': 'MANR',
    'khandeshwar': 'KNDS', 'panvel': 'PNVL',
}

OUTPUT_INPUTS = {
    'data/processed/observed/cr_harbour_layout_annotations.csv': [
        'data/raw/transit/cr_public_harbour_*.pdf', 'data/processed/observed/cr_printed_timetable_cells.csv'],
    'data/processed/observed/cr_harbour_semantic_resolutions.csv': [
        'data/raw/transit/cr_public_harbour_*.pdf', 'data/raw/transit/cr_public_trans_harbour_*.pdf',
        'data/processed/observed/cr_printed_timetable_cells.csv'],
    'data/processed/transit/cr_harbour_service_candidates.csv': [
        'data/raw/transit/cr_public_harbour_*.pdf', 'data/raw/transit/cr_public_trans_harbour_*.pdf',
        'data/processed/observed/cr_printed_timetable_cells.csv'],
    'data/processed/transit/cr_harbour_stop_candidates.csv': [
        'data/raw/transit/cr_public_harbour_*.pdf', 'data/raw/transit/cr_public_trans_harbour_*.pdf',
        'data/processed/observed/cr_printed_timetable_cells.csv'],
    'data/processed/acquisition/cr_harbour_service_evidence_audit.json': [
        'data/raw/transit/cr_public_harbour_*.pdf', 'data/raw/transit/cr_public_trans_harbour_*.pdf',
        'data/processed/observed/cr_printed_timetable_cells.csv'],
}


def normalise(name):
    return ' '.join(name.casefold().split())


def reference(row):
    return {k: row[k] for k in ('source_id', 'source_sha256', 'source_page',
                               'train_number', 'aligned_station_row_label', 'printed_local_hhmm')}


def clock_seconds(clock):
    hour, minute = map(int, clock.split(':'))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError('Invalid printed clock')
    return hour * 3600 + minute * 60


def grid_annotations(rows):
    """Read non-time glyphs within the station grid, excluding page footnotes."""
    annotations, page_checks, branch_codes = [], [], {}
    for sid in (DOWN, UP, AC):
        record, path = source(sid, 'transit')
        sid_rows = [r for r in rows if r['source_id'] == sid]
        names = {normalise(r['aligned_station_row_label']) for r in sid_rows}
        for page_number, page in enumerate(extract_pages(str(path)), 1):
            observed = [r for r in sid_rows if int(r['source_page']) == page_number]
            if {r['source_sha256'] for r in observed} != {record['sha256']}:
                raise ValueError('Stale source cells')
            page_lines = list(lines(page))
            trains = sorted([m for line in page_lines for m in matches(line, r'\b\d{5}\b')], key=lambda t: t['x'])
            if len(trains) < 2 or len({t['text'] for t in trains}) != len(trains):
                raise ValueError('Ambiguous Harbour train header')
            if max(t['y'] for t in trains) - min(t['y'] for t in trains) > min(t['height'] for t in trains) / 2:
                raise ValueError('Multiple header bands need separate handling')
            edge = trains[0]['x'] - (trains[1]['x'] - trains[0]['x']) / 2
            labels = []
            for line in page_lines:
                glyphs = [c for c in line if isinstance(c, LTChar) and c.x1 < edge]
                if not glyphs:
                    continue
                name = ''.join(c.get_text() for c in glyphs).strip()
                if normalise(name) in names:
                    labels.append(dict(name=name, y=median((c.y0+c.y1)/2 for c in glyphs),
                                       height=median(c.height for c in glyphs)))
            labels.sort(key=lambda r: -r['y'])
            if not labels or len({normalise(r['name']) for r in labels}) != len(labels):
                raise ValueError('Missing or duplicate station grid row')
            for line in page_lines:
                for code in matches(line, r'\b(?:PLGN|GNPL)\s*\d+\b'):
                    if not labels[0]['y'] < code['y'] < min(t['y'] for t in trains):
                        continue
                    train = min(trains, key=lambda t: abs(t['x']-code['x']))
                    spacing = min(abs(train['x']-other['x']) for other in trains if other is not train)
                    if abs(train['x']-code['x']) >= spacing/2 or (sid, train['text']) in branch_codes:
                        raise ValueError('Ambiguous cross-branch service code')
                    branch_codes[(sid, train['text'])] = re.sub(r'\s+', '', code['text'])
            cells = defaultdict(list)
            for line in page_lines:
                for char in line:
                    if not isinstance(char, LTChar):
                        continue
                    x, y = (char.x0+char.x1)/2, (char.y0+char.y1)/2
                    if x <= edge:
                        continue
                    index = min(range(len(labels)), key=lambda i: abs(labels[i]['y']-y))
                    if abs(labels[index]['y']-y) > labels[index]['height']/2:
                        continue
                    train = min(range(len(trains)), key=lambda i: abs(trains[i]['x']-x))
                    spacing = min(abs(trains[train]['x']-other['x']) for i, other in enumerate(trains) if i != train)
                    if abs(trains[train]['x']-x) >= spacing/2:
                        raise ValueError('Glyph outside a train column')
                    if char.graphicstate.ncolor in (1, (1, 1, 1), (0, 0, 0, 0)):
                        raise ValueError('White Harbour grid glyph needs visual review')
                    cells[(train, index)].append(char)
            numeric, nonnumeric = {}, 0
            for (train, index), glyphs in sorted(cells.items()):
                text = ' '.join(''.join(c.get_text() for c in sorted(glyphs, key=lambda c: c.x0)).split())
                if not text:
                    continue
                key = (trains[train]['text'], normalise(labels[index]['name']))
                if re.fullmatch(r'\d{1,2}:\d{2}', text):
                    numeric[key] = text
                else:
                    nonnumeric += 1
                    annotations.append(dict(source='published_layout_annotation', source_id=sid,
                                             source_sha256=record['sha256'], source_page=page_number,
                                             train_number=trains[train]['text'],
                                             aligned_station_row_label=labels[index]['name'],
                                             annotation_as_printed=text,
                                             source_x_pdf_pt=round(median((c.x0+c.x1)/2 for c in glyphs), 6),
                                             source_y_pdf_pt=round(labels[index]['y'], 6)))
            expected = {(r['train_number'], normalise(r['aligned_station_row_label'])): r['printed_local_hhmm'] for r in observed}
            if numeric != expected or len(expected) != len(observed):
                raise ValueError('Independent glyph grid does not reproduce the original time cells')
            page_checks.append(dict(source_id=sid, page=page_number, time_cells=len(numeric), annotations=nonnumeric))
    return annotations, page_checks, branch_codes


def write_transit(name, rows):
    path = Path(city.path('data/processed/transit', name))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    with Path(city.path('data/processed/observed/cr_printed_timetable_cells.csv')).open(encoding='utf-8') as stream:
        rows = [r for r in csv.DictReader(stream) if r['source_id'] in (DOWN, UP, AC, THB)]
    record, _ = source(THB, 'transit')
    if {r['source_sha256'] for r in rows if r['source_id'] == THB} != {record['sha256']}:
        raise ValueError('Stale Trans-Harbour cells')
    annotations, page_checks, branch_codes = grid_annotations(rows)
    write('cr_harbour_layout_annotations.csv', annotations)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['source_id'], row['train_number'])].append(row)
    for group in grouped.values():
        group.sort(key=lambda r: (int(r['source_page']), int(r['table_band']), int(r['station_row_order'])))
        if len({(r['source_page'], r['table_band']) for r in group}) != 1:
            raise ValueError('A service spans multiple table bands')
    annotations_by_train = defaultdict(list)
    for row in annotations:
        annotations_by_train[(row['source_id'], row['train_number'])].append(row)
    accepted_annotation_texts = {'TNA', 'BVI', 'R/O', 'VVD 2', 'PLVD24', 'VVD 14'}
    if set(r['annotation_as_printed'] for r in annotations) != accepted_annotation_texts:
        raise ValueError('New grid annotation needs explicit interpretation')

    def station(row):
        name = row['aligned_station_row_label']
        if row['source_id'] == THB:
            return 'CR_THB_CODE:' + name
        norm = normalise(name)
        return 'CR_THB_CODE:' + SHARED_STATIONS[norm] if norm in SHARED_STATIONS else 'CR_HB_LABEL:' + norm

    resolutions = []
    candidates = defaultdict(dict)
    sequences = {}
    external = set()
    comparisons = Counter()
    # The fuller Trans-Harbour sequence is retained; overlapping Harbour cells
    # corroborate its shared portion, not its unobserved current validity.
    for (sid, train), group in sorted(grouped.items(), key=lambda p: (p[0][0] != THB, p[0])):
        if sid == AC:
            continue
        keys = []
        marks = annotations_by_train[(sid, train)]
        codes = {r['annotation_as_printed']: r for r in marks}
        # Cross-branch services are split between the UP approach and DOWN
        # departure tables. Their shared boundary has two different times.
        raw_keys = [station(row) for row in group]
        old_sequence = sequences.get(train, [])
        branch_join = (sid == UP and old_sequence and
                       raw_keys[-1] == old_sequence[0] == 'CR_HB_LABEL:vadala road' and
                       set(raw_keys) & set(old_sequence) == {raw_keys[-1]} and
                       {ref['source_id'] for ref in candidates[train][old_sequence[0]]['references']} == {DOWN})
        if branch_join and (branch_codes.get((UP, train)) is None or
                            branch_codes[(UP, train)] != branch_codes.get((DOWN, train))):
            raise ValueError('Branch fragments need the same printed train and service code')
        for row in group:
            key = station(row)
            annotation = None
            if 'TNA' in codes and row['aligned_station_row_label'] == 'Masjid':
                annotation = codes['TNA']
                if sid != DOWN or annotation['aligned_station_row_label'] != 'Mumbai CSMT' or (THB, train) not in grouped:
                    raise ValueError('Unexpected Thane origin-reference layout')
                key = 'CR_THB_CODE:TNA'
            elif 'BVI' in codes and row['aligned_station_row_label'] == 'Tilaknagar':
                annotation = codes['BVI']
                if sid != DOWN or annotation['aligned_station_row_label'] != 'Kurla':
                    raise ValueError('Unexpected external destination-reference layout')
                key = 'CR_EXTERNAL_CODE:BVI'
                external.add(train)
            if annotation:
                resolutions.append(dict(source='derived_layout_interpretation', train_number=train,
                                        action='station_reference_replaces_row_alignment',
                                        original_cell=json.dumps(reference(row), sort_keys=True),
                                        supporting_annotation=json.dumps(annotation, sort_keys=True),
                                        resolved_station_key=key,
                                        corroboration='same_train_and_clock_in_Trans_Harbour' if key.endswith(':TNA') else 'printed_BVI_reference_only_branch_incomplete'))
            keys.append(key)
            if key in candidates[train]:
                previous = candidates[train][key]
                if branch_join and key == raw_keys[-1]:
                    previous['arrival_clock'] = row['printed_local_hhmm']
                    previous['departure_clock'] = previous['clock']
                    resolutions.append(dict(source='derived_layout_interpretation', train_number=train,
                                            action='join_branch_fragments_preserve_both_boundary_times',
                                            original_cell=json.dumps(reference(row), sort_keys=True),
                                            supporting_annotation=json.dumps(previous['references'], sort_keys=True),
                                            resolved_station_key=key,
                                            corroboration='same_train_and_service_code_' + branch_codes[(UP, train)] + '_UP_endpoint_matches_DOWN_origin'))
                elif previous['clock'] != row['printed_local_hhmm']:
                    raise ValueError('Overlapping timetable clocks disagree: ' + train + ' ' + key)
                previous['references'].append(reference(row))
                comparisons['branch_boundary_pairs' if branch_join else 'base_overlap_cells'] += 1
            else:
                candidates[train][key] = dict(clock=row['printed_local_hhmm'], references=[reference(row)])
        if len(set(keys)) != len(keys):
            raise ValueError('Repeated station needs separate arrival/departure treatment')
        if train in sequences:
            old = sequences[train]
            if branch_join:
                sequences[train] = keys[:-1] + old
                comparisons['joined_branch_services'] += 1
            else:
                if not all(k in old for k in keys) or [k for k in old if k in keys] != keys:
                    raise ValueError('Overlapping stop order differs')
                comparisons['overlapping_base_services'] += 1
        else:
            sequences[train] = keys

    for (sid, train), group in sorted(grouped.items()):
        if sid != AC:
            continue
        if train not in candidates:
            raise ValueError('AC supplement has no base train')
        comparisons['ac_services'] += 1
        for row in group:
            key = station(row)
            if key not in candidates[train]:
                marks = annotations_by_train[(sid, train)]
                if (row['aligned_station_row_label'] != 'Reay Road' or
                        not any(r['annotation_as_printed'] == 'R/O' for r in marks) or
                        not any(r['annotation_as_printed'] in {'VVD 2', 'PLVD24', 'VVD 14'} for r in marks)):
                    raise ValueError('Unexplained AC-only timetable cell')
                resolutions.append(dict(source='derived_layout_interpretation', train_number=train,
                                        action='quarantined_return_reference_not_added_as_stop',
                                        original_cell=json.dumps(reference(row), sort_keys=True),
                                        supporting_annotation=json.dumps(marks, sort_keys=True), resolved_station_key='',
                                        corroboration='absent_from_same_vintage_base_table_semantics_require_rake_diagram'))
                comparisons['quarantined_ac_only_cells'] += 1
                continue
            previous = candidates[train][key]
            if previous['clock'] != row['printed_local_hhmm']:
                raise ValueError('AC supplement clock differs from base')
            previous['references'].append(reference(row))
            comparisons['ac_matched_cells'] += 1
    write('cr_harbour_semantic_resolutions.csv', resolutions)

    services, stops = [], []
    for train, sequence in sorted(sequences.items()):
        day, previous, first = 0, None, None
        service_sources = set()
        for index, key in enumerate(sequence, 1):
            item = candidates[train][key]
            clock = clock_seconds(item.get('arrival_clock', item['clock']))
            if previous is not None and clock < previous:
                day += 1
            elapsed = clock + day * 86400
            if first is None:
                first = elapsed
            arrival_elapsed, arrival_day = elapsed, day
            departure_clock = item.get('departure_clock')
            dwell = ''
            if departure_clock is not None:
                departure = clock_seconds(departure_clock)
                if departure < clock:
                    day += 1
                elapsed = departure + day * 86400
                dwell = elapsed - arrival_elapsed
                clock = departure
            for ref in item['references']:
                service_sources.add(ref['source_id'])
            stops.append(dict(source='derived_published_service_candidate', train_number=train, stop_sequence=index,
                              station_key=key, printed_local_hhmm=item['clock'] if departure_clock is None else '',
                              local_clock_seconds=clock_seconds(item['clock']) if departure_clock is None else '',
                              boundary_arrival_hhmm=item.get('arrival_clock', ''), boundary_departure_hhmm=departure_clock or '',
                              boundary_dwell_seconds=dwell,
                              relative_day_offset_from_first_printed_time=arrival_day,
                              departure_relative_day_offset=day if departure_clock is not None else '',
                              elapsed_seconds_since_first_printed_time=arrival_elapsed-first,
                              source_references=json.dumps(item['references'], sort_keys=True),
                              stop_time_role='derived_boundary_arrival_and_departure' if departure_clock is not None else 'published_time_arrival_departure_split_unresolved',
                              service_day_status='relative_clock_unwrap_only_calendar_origin_unresolved'))
            previous = clock
        if day > 1:
            raise ValueError('Multiple clock reversals need source review')
        services.append(dict(source='derived_published_service_candidate', train_number=train,
                             candidate_stop_count=len(sequence), first_station_key=sequence[0], last_station_key=sequence[-1],
                             printed_span_seconds=elapsed-first, midnight_crossings=day,
                             source_ids=';'.join(sorted(service_sources)),
                             coverage_status='external_branch_incomplete' if train in external else 'published_table_coverage_not_geographic_validation',
                             applicability='mixed_2024_and_2026_vintages_reconcile_amendments',
                             calendar_status='not_assembled', physical_station_mapping_status='unresolved',
                             schedule_export_eligible=False))
    input_cells = Counter(json.dumps(reference(row), sort_keys=True) for row in rows)
    retained_cells = Counter(json.dumps(ref, sort_keys=True) for stop in stops for ref in json.loads(stop['source_references']))
    for resolution in resolutions:
        if resolution['action'] == 'quarantined_return_reference_not_added_as_stop':
            retained_cells[resolution['original_cell']] += 1
    if retained_cells != input_cells:
        raise ValueError('A source time cell was lost, duplicated or changed during service assembly')
    boundary_dwells = Counter(stop['boundary_dwell_seconds'] for stop in stops if stop['boundary_dwell_seconds'] != '')
    write_transit('cr_harbour_service_candidates.csv', services)
    write_transit('cr_harbour_stop_candidates.csv', stops)
    audit = dict(status='service_evidence_not_runnable_timetable', source_time_cells=len(rows),
                 glyph_grid_page_checks=page_checks, layout_annotations=len(annotations),
                 semantic_resolutions=len(resolutions), comparisons=dict(comparisons),
                 source_cell_conservation='all_input_cells_retained_once_in_references_or_quarantine',
                 boundary_dwell_seconds_distribution=dict(sorted(boundary_dwells.items())),
                 joined_branch_codes={train: code for (sid, train), code in sorted(branch_codes.items()) if sid == UP},
                 unique_service_candidates=len(services), stop_candidates=len(stops),
                 external_branch_services=sorted(external),
                 limitations=[
                     'Train-number unions apply only to these editions; numbers are not globally unique across calendar dates.',
                     'Matching 2026 shared cells does not establish current validity of the rest of a 2024 train route.',
                     'BVI is an explicit external endpoint reference; its intervening stations and later WR timetable still require reconciliation.',
                     'R/O reference times are quarantined, not asserted to be passenger stops or complete rake circulations.',
                     'Shared-endpoint branch times supply derived arrival/departure pairs; the physical reversal and current rake working still require verification.',
                     'Station keys preserve source vocabularies and require physical stop, track and platform mapping.',
                     'Clock unwrapping is relative to the first printed time, not an adopted operating-day boundary.',
                     'Arrival/departure roles, dwell, calendars, vehicle assignments, amendments and train-control conflicts remain unresolved.',
                 ])
    Path(city.path('data/processed/acquisition/cr_harbour_service_evidence_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('glyph_grid_page_checks', 'limitations')}))


if __name__ == '__main__':
    main()
