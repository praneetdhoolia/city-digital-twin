"""Extract published registration stock and flows, preserving source conflicts."""
from collections import defaultdict
import json
from pathlib import Path
import re

from pypdf import PdfReader
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/rto_2025_vehicle_categories.csv': ['data/raw/vehicles/vehicle_stock_2025_*.pdf'],
    'data/processed/observed/rto_2025_summary.csv': ['data/raw/vehicles/vehicle_stock_2025_*.pdf'],
    'data/processed/acquisition/rto_2025_audit.json': ['data/raw/vehicles/vehicle_stock_2025_*.pdf'],
}


def main():
    layout = json.loads(Path(city.path('extract/transcriptions/rto_2025_table_layout.json')).read_text(encoding='utf-8'))
    record, path = source(layout['source_id'], 'vehicles')
    if record['sha256'] != layout['source_sha256']:
        raise ValueError('Table layout transcription belongs to another PDF')
    pages = PdfReader(path).pages
    rows, summary, checks = [], [], []
    for page_index in (0, 1):
        for line in pages[page_index].extract_text(extraction_mode='layout').splitlines():
            match = re.fullmatch(r'\s*(?:\d+\s+)?([A-Za-z].*?)\s{2,}(\d+)\s+(\d+)\s*', line)
            if match:
                summary.append(dict(office_label=match[1].strip(), registered_stock_20250331_count=int(match[2]),
                                    new_registrations_2024_25_count=int(match[3]), source_page=page_index+1,
                                    source='published_registration_statistics', source_sha256=record['sha256']))
    for table in layout['tables']:
        number_columns = len(table['columns']) + bool(table.get('repeated_unlabelled_final_column'))
        pattern = re.compile(r'\s*(.*?)\s{2,}((?:\d+\s+){'+str(number_columns-1)+r'}\d+)\s*')
        extracted = []
        for line in pages[table['page_1_based']-1].extract_text(extraction_mode='layout').splitlines():
            match = pattern.fullmatch(line)
            if not match or not re.search('[A-Za-z]', match[1]):
                continue
            label = ' '.join(match[1].split())
            numbers = [int(x) for x in match[2].split()]
            if table.get('repeated_unlabelled_final_column'):
                if numbers[-1] != numbers[-2]:
                    raise ValueError('Unlabelled repeat differs from State Total')
                numbers.pop()
            if label.startswith('Total'):
                category = 'subtotal_two_wheelers' if 'Two Wheelers' in label else 'total_all_vehicles'
            else:
                code = re.match(r'(\d+)\s*([ab])?', label)
                if not code:
                    raise ValueError('Unrecognised category row')
                category = code[1]+(code[2] or '')
            extracted.append((category, label, numbers))
        expected = {str(n) for n in range(1, 22)} - {'7'} | {'7a', '7b', 'subtotal_two_wheelers', 'total_all_vehicles'}
        if len(extracted) != len(expected) or {r[0] for r in extracted} != expected:
            raise ValueError('Incomplete category table on page '+str(table['page_1_based']))
        for index, office in enumerate(table['columns']):
            values = {category: numbers[index] for category, _, numbers in extracted}
            for category, label, numbers in extracted:
                rows.append(dict(office_label=office, column_1_based=index+1, measure=table['measure'],
                                 office_level=('state' if office == 'Maharashtra State' else 'region' if office.endswith('Region') or office == 'Gr. Mumbai' else 'office'),
                                 category_code=category, printed_category_label=label, vehicles_count=numbers[index],
                                 aggregate_row=category.startswith(('subtotal', 'total')),
                                 source_page=table['page_1_based'], source='published_provisional_registration_statistics',
                                 source_sha256=record['sha256']))
            checks.append(dict(page=table['page_1_based'], office_label=office, check='category_sum',
                               calculated=sum(v for k,v in values.items() if not k.startswith(('subtotal', 'total'))),
                               printed=values['total_all_vehicles']))
            checks.append(dict(page=table['page_1_based'], office_label=office, check='two_wheeler_sum',
                               calculated=sum(values[k] for k in ('1', '2', '3')), printed=values['subtotal_two_wheelers']))
    by_measure_category = defaultdict(list)
    for row in rows:
        by_measure_category[(row['measure'], row['category_code'])].append(row)
    for (measure, category), cells in by_measure_category.items():
        region_sum = 0
        for cell in cells:
            if cell['office_level'] == 'office':
                region_sum += cell['vehicles_count']
            elif cell['office_level'] == 'region':
                checks.append(dict(page=cell['source_page'], office_label=cell['office_label'],
                                   check='region_office_sum_'+measure+'_'+category,
                                   calculated=region_sum, printed=cell['vehicles_count']))
                region_sum = 0
        state = [r for r in cells if r['office_level'] == 'state']
        if len(state) != 1:
            raise ValueError('Missing or repeated state total')
        checks.append(dict(page=state[0]['source_page'], office_label='Maharashtra State',
                           check='office_sum_'+measure+'_'+category,
                           calculated=sum(r['vehicles_count'] for r in cells if r['office_level'] == 'office'),
                           printed=state[0]['vehicles_count']))
    summary_by_name = {r['office_label']: r for r in summary}
    comparable = 0
    for row in rows:
        if row['category_code'] != 'total_all_vehicles' or row['office_label'] not in summary_by_name:
            continue
        name, measure = row['office_label'], row['measure']
        checks.append(dict(page=row['source_page'], office_label=name, check='summary_agreement_'+measure,
                           calculated=row['vehicles_count'], printed=summary_by_name[name][measure+'_count']))
        comparable += 1
    conflicts = [c for c in checks if c['calculated'] != c['printed']]
    conflicted = {(c['page'], c['office_label']) for c in conflicts}
    for row in rows:
        row['validation_status'] = 'source_conflict' if (row['source_page'], row['office_label']) in conflicted else 'arithmetic_checked_not_spatially_validated'
    write('rto_2025_vehicle_categories.csv', rows)
    write('rto_2025_summary.csv', summary)
    audit = dict(schema_version=1, category_cells=len(rows), summary_rows=len(summary), checks=len(checks),
                 matching_name_summary_comparisons=comparable, conflicts=conflicts,
                 source_sha256=record['sha256'], transcription_notes=layout['notes'],
                 limits='Registered stock and new registrations are different measures. Region/subtotal rows overlap their children and must not be summed together. RTO labels are not jurisdiction polygons, resident household ownership, active fleet or traffic. Name-exact summary comparisons only; no inferred office alias joins or East/Borivali correction. No 2026 projection applied.')
    target = Path(city.path('data/processed/acquisition/rto_2025_audit.json'))
    target.write_text(json.dumps(audit, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(dict(category_cells=len(rows), summary_rows=len(summary), checks=len(checks),
                          conflicts=len(conflicts), conflict_offices=sorted({c['office_label'] for c in conflicts}))))


if __name__ == '__main__':
    main()
