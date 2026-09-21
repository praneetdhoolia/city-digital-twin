"""Read the source table's column positions, symbols and dated variability."""
from collections import Counter
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

SID = 'jvlr_traffic_study_2026_pdf'
OUTPUT_INPUTS = {
    'data/processed/observed/jvlr_journal_road_inventory.csv': [
        'data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf',
        'data/processed/observed/jvlr_journal_classified_counts.csv'],
    'data/processed/observed/jvlr_journal_temporal_variability.csv': [
        'data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf',
        'data/processed/observed/jvlr_journal_classified_counts.csv'],
    'data/processed/acquisition/jvlr_inventory_audit.json': [
        'data/raw/traffic/jvlr_traffic_study_2026_pdf_*.pdf',
        'data/processed/observed/jvlr_journal_classified_counts.csv'],
}
HEADERS = (
    ('Name/No.', 'road_label_unused'),
    ('Marking', 'lane_marking_reported'), ('Shoulders', 'shoulders_reported'),
    ('Median', 'median_reported'), ('Bay/Line', 'parking_reported'),
    ('Service', 'service_lane_reported'), ('Bicycle', 'bicycle_facility_reported'),
    ('Pathways', 'pedestrian_pathway_reported'), ('Crossing', 'zebra_crossing_reported'),
    ('Zones', 'vending_zones_reported'), ('Corridor', 'utility_corridor_reported'),
    ('Plantation', 'plantation_reported'), ('Furniture', 'street_hardware_reported'),
    ('Land', 'additional_land_reported'), ('ROW', 'exclusive_row_reported'),
)


def words(path, page):
    result = subprocess.run(['pdftotext', '-f', str(page), '-l', str(page),
                             '-bbox-layout', str(path), '-'], check=True,
                            capture_output=True, encoding='utf-8')
    elements = ET.fromstring(result.stdout).findall('.//{*}word')
    return [dict(text=word.text, **{key: float(value) for key, value in word.attrib.items()})
            for word in elements]


def xcentre(word):
    return (word['xMin'] + word['xMax']) / 2


def ycentre(word):
    return (word['yMin'] + word['yMax']) / 2


def inventory_cells(path, identifiers):
    items = words(path, 15)
    anchors = {identity: [word for word in items if word['text'] == identity]
               for identity in identifiers}
    if any(len(matches) != 1 for matches in anchors.values()):
        raise ValueError('Ambiguous inventory row labels')
    anchors = {key: matches[0] for key, matches in anchors.items()}
    first = min(word['yMin'] for word in anchors.values())
    last = max(word['yMax'] for word in anchors.values())
    centres = []
    for label, field in HEADERS:
        candidates = [word for word in items if word['text'] == label and word['yMax'] < first]
        if len(candidates) != 1:
            raise ValueError('Ambiguous column heading: ' + label)
        centres.append(xcentre(candidates[0]))
    if centres != sorted(centres):
        raise ValueError('Inventory column order changed')
    boundaries = [(left + right) / 2 for left, right in zip(centres, centres[1:])]
    # Section headings are centred across several columns. Their numeric label
    # is in the row-ID column; exclude the whole heading's vertical band.
    id_right = max(word['xMax'] for word in anchors.values())
    groups = [word for word in items if word['text'].isdigit() and word['xMax'] <= id_right]
    cells = {key: {field: [] for _, field in HEADERS[1:]} for key in anchors}
    for word in items:
        if not (first <= ycentre(word) <= last) or xcentre(word) <= boundaries[0]:
            continue
        if any(word['yMin'] < group['yMax'] and word['yMax'] > group['yMin'] for group in groups):
            continue
        row = min(anchors, key=lambda key: abs(ycentre(anchors[key]) - ycentre(word)))
        column = sum(xcentre(word) > boundary for boundary in boundaries)
        cells[row][HEADERS[column][1]].append(word)
    output = {}
    for identity, fields in cells.items():
        output[identity] = {}
        for field, values in fields.items():
            # Words on a line share their y coordinate in this PDF. Retain line
            # order before word order so wrapped cells join naturally.
            text = ' '.join(word['text'] for word in sorted(values, key=lambda word: (word['yMin'], word['xMin'])))
            if not text:
                raise ValueError('Empty inventory cell: ' + identity + '/' + field)
            output[identity][field] = text
    return output


def main():
    record, path = source(SID, 'traffic')
    with Path(city.path('data/processed/observed/jvlr_journal_classified_counts.csv')).open(encoding='utf-8', newline='') as stream:
        counts = {row['row_id']: row for row in csv.DictReader(stream)}
    if any(row['source_sha256'] != record['sha256'] for row in counts.values()):
        raise ValueError('Count metadata comes from a different paper version')
    cells = inventory_cells(path, counts)
    inventory = []
    for identity in sorted(cells):
        fields = cells[identity]
        # Reject layout shifts which could turn a column neighbour into a value.
        for key, text in fields.items():
            if key in ('parking_reported', 'street_hardware_reported', 'exclusive_row_reported'):
                continue
            if not re.fullmatch(r'(?:✅|❌|Faded)(?: \(\d+(?:\.\d+)? m\))?', text):
                raise ValueError('Unexpected inventory cell: ' + identity + '/' + key + ': ' + text)
        row = dict(source='observed', source_id=SID, source_sha256=record['sha256'],
                   source_pdf_page=15, source_table='6', row_id=identity,
                   site=counts[identity]['site'], road_label=counts[identity]['road_label'],
                   survey_start_date=counts[identity]['survey_start_date'],
                   survey_end_date=counts[identity]['survey_end_date'], **fields)
        for field in ('median', 'service_lane', 'pedestrian_pathway'):
            match = re.search(r'\((\d+(?:\.\d+)?) m\)', fields[field + '_reported'])
            row[field + '_reported_width_m'] = match[1] if match else None
        width = re.fullmatch(r'(\d+(?:\.\d+)?)\s*m', fields['exclusive_row_reported'])
        if not width:
            raise ValueError('Unrecognised reported right-of-way width')
        row['exclusive_right_of_way_width_m'] = width[1]
        row['model_assignment_status'] = 'unassigned_requires_location_and_2026_condition_check'
        inventory.append(row)
    table5 = page_text(path, 12).split('Table 5.', 1)[1].split('Note:', 1)[0]
    pattern = re.compile(r'^\s*(\d+\.\d+)\s+.*?\s*(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(Low|Acceptable) variability\s*$')
    variability, checks = [], []
    for line in table5.splitlines():
        match = pattern.fullmatch(line)
        if not match:
            continue
        identity = match[1]
        mean, sd, cv = (Decimal(match[i]) for i in (2, 3, 4))
        if mean <= 0 or sd < 0:
            raise ValueError('Invalid temporal summary')
        expected = sd / mean * 100
        half_quantum = Decimal(1).scaleb(cv.as_tuple().exponent) / 2
        checks.append(dict(row_id=identity, check='cv_equals_sd_over_mean_percent',
                           published=str(cv), calculated=str(expected), printed_half_quantum=str(half_quantum),
                           status='exact' if cv == expected else 'rounding_compatible'
                           if abs(cv - expected) <= half_quantum else 'source_disagreement'))
        variability.append(dict(source='derived', source_id=SID, source_sha256=record['sha256'],
                                source_pdf_page=12, source_table='5', row_id=identity,
                                site=counts[identity]['site'], road_label=counts[identity]['road_label'],
                                survey_start_date=counts[identity]['survey_start_date'],
                                survey_end_date=counts[identity]['survey_end_date'],
                                mean_flow_pcu_h_lane=match[2], sd_flow_pcu_h_lane=match[3],
                                coefficient_of_variation_percent=match[4], interpretation=match[5] + ' variability',
                                statistic_scope='published_peak_period_summary_not_daily_microdata'))
    if {row['row_id'] for row in variability} != set(counts) or len(variability) != len(counts):
        raise ValueError('Temporal summaries do not cover every count location')
    out = Path(city.path('data/processed/observed'))
    write(out / 'jvlr_journal_road_inventory.csv', inventory)
    write(out / 'jvlr_journal_temporal_variability.csv', variability)
    report = dict(source='derived', source_id=SID, source_sha256=record['sha256'],
                  road_inventory_rows=len(inventory), inventory_source_cells=sum(len(row) for row in cells.values()),
                  temporal_summary_rows=len(variability), checks=checks,
                  check_status_counts=dict(Counter(check['status'] for check in checks)),
                  reported_pathway_widths_m=sorted({row['pedestrian_pathway_reported_width_m'] for row in inventory
                                                   if row['pedestrian_pathway_reported_width_m'] is not None}),
                  limitations=[
                      'Inventory is dated to the survey period; no claim of current corridor condition.',
                      'A reported missing footpath does not establish that pedestrians are prohibited.',
                      'Right-of-way width includes space beyond the carriageway; it is not a lane-width measurement.',
                      'A present service lane or median with no numeric width remains width-unknown.',
                      'Temporal statistics describe the published survey week; raw daily counts remain unobtained.',
                      'No causal capacity adjustment is inferred from the inventory or the variability.',
                  ])
    Path(city.path('data/processed/acquisition/jvlr_inventory_audit.json')).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('road_inventory_rows', 'inventory_source_cells', 'temporal_summary_rows', 'check_status_counts')}))


if __name__ == '__main__':
    main()
