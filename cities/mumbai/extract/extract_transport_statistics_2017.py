"""Extract the Transport Commissioner's Maharashtra transport statistics 2016-17.

Two tables of `maharashtra_transport_statistics_2016_17` (Motor Vehicles
Department, Government of Maharashtra) are the vehicle-stock history the
package otherwise lacks:

  * Table 24 (six pages): office, region and category-wise vehicles on road as
    on 31 March 2017 - the same 21 categories and the same RTO offices as the
    31 March 2025 stock in `rto_2025_vehicle_categories.csv`, eight years
    earlier, so an office's two-wheeler and car stock growth is observed;
  * Tables 15 and 16: category-wise state vehicle population at 31 March
    1971 ... 2011 and 1987 ... 2017 - the only stock the package holds for the
    census year 2011, at the state level.

The 2011 household vehicle possession (Census HL-14) is the base the
population synthesiser draws from; `derive_vehicle_possession_growth.py`
carries it to the base year from these two tables and the 2025 stock. Every
printed row is kept with its page; the column totals and the two-wheeler
subtotals are checked against the printed ones; nothing is interpolated.
"""
from collections import defaultdict
import json
import re
from pathlib import Path

from pypdf import PdfReader
import city
from extract_census_controls import source, write

SOURCE_ID = 'maharashtra_transport_statistics_2016_17'
OUTPUT_INPUTS = {
    'data/processed/observed/mts_2017_office_category_stock.csv': ['data/raw/vehicles/maharashtra_transport_statistics_2016_17_*.pdf'],
    'data/processed/observed/mts_state_category_stock_series.csv': ['data/raw/vehicles/maharashtra_transport_statistics_2016_17_*.pdf'],
    'data/processed/acquisition/mts_2017_audit.json': ['data/raw/vehicles/maharashtra_transport_statistics_2016_17_*.pdf'],
}
LAYOUT = json.loads(Path(city.path('extract/transcriptions/mts_2016_17_table_layout.json')).read_text(encoding='utf-8'))
TABLE_24 = LAYOUT['table_24']
CATEGORY_ROW = re.compile(r'\s*(\d+\(?[AB]?\)?|Total)\s+(.*?)\s*((?:\d+\s+)+\d+)\s*$')
STATE_TABLES = {name: (spec['title'], spec['years']) for name, spec in LAYOUT['state_tables'].items()}
STATE_CATEGORIES = ['Two Wheelers', 'Cars/Jeeps/ St. Wagons', 'Taxi Cabs', 'Auto-Rickshaws',
                    'Stage/Contact Carriages', 'School Buses', 'Private Service Vehicles', 'Ambulances',
                    'Arti/ Multi Axel Veh., Trucks/ Lorries, Tankers & Delivery Vans', 'Tractors', 'Trailors',
                    'Others', 'Total State']


def layout_lines(page):
    return (page.extract_text(extraction_mode='layout') or '').splitlines()


def parse_table_24(pages, record):
    """Every office column of the six Table 24 pages: (office, category) -> count."""
    rows, checks, seen_pages = [], [], 0
    for page_index, page in enumerate(pages):
        lines = layout_lines(page)
        text = ' '.join('\n'.join(lines).split())
        if TABLE_24['title'] not in text or 'Table No. 24' not in text:
            continue
        seen_pages += 1
        # the header block runs from the `Sr.  Category` line to the line of
        # column numbers; every word in it belongs to the column whose printed
        # number sits nearest below it (an office name wraps over three lines)
        header_i = next(i for i, l in enumerate(lines) if l.strip().startswith('Sr.') and 'Category' in l)
        numbers_i = next(i for i in range(header_i + 1, header_i + 1 + TABLE_24['header_lines_at_most'])
                         if re.fullmatch(r'\s*1\s+2(\s+\d+)+\s*', lines[i]))
        anchors = [(m.start(), int(m.group())) for m in re.finditer(r'\d+', lines[numbers_i])][2:]
        words = {a[1]: [] for a in anchors}
        for l in lines[header_i:numbers_i]:
            for m in re.finditer(r'\S+', l):
                if m.group() in ('Sr.', 'No.', 'Category'):
                    continue
                centre = (m.start() + m.end()) / 2
                nearest = min(anchors, key=lambda a: abs(a[0] + 1 - centre))
                words[nearest[1]].append(m.group())
        offices = [' '.join(words[a[1]]).replace('- ', '-') for a in anchors]
        extracted = []
        for line in lines[numbers_i + 1:]:
            m = CATEGORY_ROW.match(line)
            if not m:
                continue
            code, label, numbers = m.group(1), (m.group(2) or '').strip(), [int(x) for x in m.group(3).split()]
            if len(numbers) != len(offices):
                raise ValueError('Table 24 page %d: %d numbers for %d offices on %r'
                                 % (page_index + 1, len(numbers), len(offices), line))
            key = ('subtotal_two_wheelers' if code == 'Total' and 'wheeler' in label.lower()
                   else 'total_all_vehicles' if code == 'Total'
                   else code.replace('(', '').replace(')', '').lower())
            extracted.append((key, (code + ' ' + label).strip(), numbers))
        expected = {str(n) for n in range(1, 22)} - {'7'} | {'7a', '7b', 'subtotal_two_wheelers', 'total_all_vehicles'}
        if {e[0] for e in extracted} != expected:
            raise ValueError('Table 24 page %d: categories %s' % (page_index + 1, sorted({e[0] for e in extracted} ^ expected)))
        for column, office in enumerate(offices):
            values = {k: n[column] for k, _, n in extracted}
            level = ('state' if office.startswith('Maharashtra') else
                     'region' if office.endswith('Region') or office == 'Greater Mumbai' else 'office')
            for key, label, numbers in extracted:
                rows.append(dict(office_label=office, column_1_based=column + 1,
                                 measure='registered_stock_' + TABLE_24['stock_date'].replace('-', ''),
                                 office_level=level, category_code=key, printed_category_label=label,
                                 vehicles_count=numbers[column], aggregate_row=key.startswith(('subtotal', 'total')),
                                 source_page=page_index + 1, source='published_transport_statistics_2016_17',
                                 source_sha256=record['sha256']))
            checks.append(dict(page=page_index + 1, office_label=office, check='category_sum',
                               calculated=sum(v for k, v in values.items() if not k.startswith(('subtotal', 'total'))),
                               printed=values['total_all_vehicles']))
            checks.append(dict(page=page_index + 1, office_label=office, check='two_wheeler_sum',
                               calculated=values['1'] + values['2'] + values['3'], printed=values['subtotal_two_wheelers']))
    if seen_pages != TABLE_24['pages']:
        raise ValueError('Table 24 has %d pages; found %d' % (TABLE_24['pages'], seen_pages))
    return rows, checks


def parse_state_series(pages, record):
    """Tables 15 and 16: the state's category stock at each printed 31 March.

    A category label wraps over up to four lines; the printed serial number
    names the row and the first words of the label are checked against the
    category list, so a wrapped label never becomes a row of its own."""
    rows, checks = [], []
    row_pattern = re.compile(r'\s*(\d+|Total State)\s+([A-Za-z][-A-Za-z/.,& ]*?)?\s+((?:\d+\s+)+\d+)\s+((?:\d+\.\d+\s*)+)$')
    for page_index, page in enumerate(pages):
        lines = layout_lines(page)
        text = ' '.join(' '.join(lines).split())
        for table, (title, years) in STATE_TABLES.items():
            if table not in text or ' '.join(title.split()) not in text:
                continue
            body = []
            for line in lines:
                m = row_pattern.match(line)
                if m:
                    numbers = [int(x) for x in m.group(3).split()]
                    serial = 'total' if m.group(1) == 'Total State' else m.group(1)
                    body.append((serial, ' '.join((m.group(2) or '').split()), numbers, [float(x) for x in m.group(4).split()]))
            serials = [b[0] for b in body]
            if serials != [str(n) for n in range(1, 13)] + ['total']:
                raise ValueError('%s: rows %s' % (table, serials))
            for serial, label, numbers, cagr in body:
                if len(numbers) != len(years):
                    raise ValueError('%s: %d values for %d years on %r' % (table, len(numbers), len(years), label))
                category = STATE_CATEGORIES[-1] if serial == 'total' else STATE_CATEGORIES[int(serial) - 1]
                if serial != 'total' and label.split()[0] not in category:
                    raise ValueError('%s: row %s prints %r, expected %r' % (table, serial, label, category))
                for year, value in zip(years, numbers):
                    rows.append(dict(table=table.replace('Table No ', 'table_'), category_serial=serial,
                                     category=category, stock_year_31_march=year, vehicles_count=value,
                                     source_page=page_index + 1, source='published_transport_statistics_2016_17',
                                     source_sha256=record['sha256']))
            for year_i, year in enumerate(years):
                checks.append(dict(table=table, year=year, check='category_sum',
                                   calculated=sum(b[2][year_i] for b in body if b[0] != 'total'),
                                   printed=next(b for b in body if b[0] == 'total')[2][year_i]))
    if not rows:
        raise ValueError('Tables 15 and 16 not found')
    return rows, checks


def main():
    record, path = source(SOURCE_ID, 'vehicles')
    if record['sha256'] != LAYOUT['source_sha256']:
        raise ValueError('Table layout transcription belongs to another PDF')
    pages = PdfReader(path).pages
    office_rows, office_checks = parse_table_24(pages, record)
    state_rows, state_checks = parse_state_series(pages, record)
    # the Greater Mumbai and regional columns are printed sums of their offices
    by_key = defaultdict(dict)
    for r in office_rows:
        by_key[(r['category_code'])][r['office_label']] = r['vehicles_count']
    region_checks = []
    for category, cells in by_key.items():
        for region, members in (('Greater Mumbai', ['Mumbai (C)', 'Mumbai (W)', 'Mumbai (E)', 'Borivali']),
                                ('Thane Region', ['Thane', 'Kalyan', 'Vashi N.Mumbai', 'Vasai']),
                                ('Panvel Region', ['Panvel', 'Pen Raigad', 'Sindhudurg', 'Ratnagiri'])):
            if region in cells and all(m in cells for m in members):
                region_checks.append(dict(category_code=category, region=region, check='region_sum',
                                          calculated=sum(cells[m] for m in members), printed=cells[region]))
    failed = [c for c in office_checks + state_checks + region_checks if c['calculated'] != c['printed']]
    write('mts_2017_office_category_stock.csv', office_rows)
    write('mts_state_category_stock_series.csv', state_rows)
    audit = dict(source_id=SOURCE_ID, source_sha256=record['sha256'],
                 office_rows=len(office_rows), offices=sorted({r['office_label'] for r in office_rows}),
                 state_rows=len(state_rows), checks=len(office_checks) + len(state_checks) + len(region_checks),
                 failed_checks=failed,
                 status='arithmetic_checked' if not failed else 'printed_totals_disagree',
                 limitations=['Stock on record at the RTO office of registration, not vehicles in use or garaged '
                              'in the district; scrapped and migrated vehicles stay on record.',
                              'The 2011 stock is the state total (Table 15); no office-level 2011 stock is printed.'])
    out = Path(city.path('data/processed/acquisition/mts_2017_audit.json'))
    out.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Table 24: %d rows, %d offices; state series: %d rows; %d checks, %d failed'
          % (len(office_rows), len(audit['offices']), len(state_rows), audit['checks'], len(failed)))
    if failed:
        for f in failed[:10]:
            print('  ', f)


if __name__ == '__main__':
    main()
