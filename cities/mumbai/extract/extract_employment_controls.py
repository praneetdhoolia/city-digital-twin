"""Extract historical Economic Census controls with table reconciliation.

Counts are establishments and persons engaged at establishments, not employed
residents, unique commuters or daily trips. Historical districts are retained.
"""
import json
from pathlib import Path
import re

from pypdf import PdfReader
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/ec6_district_controls.csv': ['data/raw/employment/maharashtra_ec6_final_*.pdf'],
    'data/processed/observed/_ec6_controls_audit.json': [
        'data/raw/employment/maharashtra_ec6_final_*.pdf',
        'data/raw/employment/mospi_ec6_maharashtra_detail_page_1_*.json'],
}
TABLES = {'2.8': ('rural', 'urban', 'combined'),
          '2.9': ('without_hired_worker', 'with_at_least_one_hired_worker', 'combined')}


def parse_table(text, table):
    pattern = r'(?m)^(\d{2})\s*-?\s*([A-Za-z][A-Za-z\s]*?)\s+(?=\d)(.+?)(?=\n\d{2}\s*-?\s*[A-Za-z]|\nTotal )'
    districts = []
    for match in re.finditer(pattern, text, re.S):
        code, name, body = match.groups()
        name = ' '.join(name.split())
        tokens = body.split()
        if not all(re.fullmatch(r'[\d,]+(?:\.\d+)?', t) for t in tokens):
            raise ValueError('Unexpected district row: '+repr(match[0]))
        # Urban-only districts have blank rural cells in table 2.8. Preserve
        # their derived status rather than claiming a printed observed zero.
        derived = set()
        if table == '2.8' and len(tokens) == 6:
            tokens.insert(0, str(int(tokens[1].replace(',',''))-int(tokens[0].replace(',',''))))
            tokens.insert(4, str(int(tokens[5].replace(',',''))-int(tokens[4].replace(',',''))))
            derived = {0,4}
        if len(tokens) != 8:
            raise ValueError('Unexpected table width')
        counts = [int(tokens[i].replace(',','')) for i in (0,1,2,4,5,6)]
        if any(v < 0 for v in counts) or counts[0]+counts[1]!=counts[2] or counts[3]+counts[4]!=counts[5]:
            raise ValueError('District components do not reconcile')
        districts.append((code,name,counts,{0,3} if derived else set()))
    if [int(d[0]) for d in districts] != list(range(1,36)):
        raise ValueError('Expected all historical district codes exactly once')
    total = re.search(r'(?m)^Total ([\d, .]+)$', text)
    if not total:
        raise ValueError('Missing printed state total')
    tokens = total[1].split()
    totals = [int(tokens[i].replace(',','')) for i in (0,1,2,4,5,6)]
    if any(sum(d[2][i] for d in districts)!=v for i,v in enumerate(totals)):
        raise ValueError('District counts do not sum to published state totals')
    return districts, totals


def main():
    record, path = source('maharashtra_ec6_final', 'employment')
    reader = PdfReader(path)
    rows, found, district_totals, state_totals = [], set(), {}, {}
    region = json.loads(Path(city.path('city.json')).read_text(encoding='utf-8'))['jurisdiction']['subdivision']
    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        match = re.match(r'Table (2\.[89])\s*:', text)
        if not match:
            continue
        table = match[1]
        if table in found:
            raise ValueError('Duplicate selected table')
        found.add(table)
        districts, totals = parse_table(text, table)
        state_totals[table] = totals
        for code, name, counts, derived in districts+[('',region,totals,set())]:
            level = 'historical_district' if code else 'state'
            district_totals[(table,code)] = (counts[2],counts[5])
            for i,value in enumerate(counts):
                category = TABLES[table][i%3]
                rows.append(dict(observation_year=2013, geography_level=level, ec_district_code=code,
                                 geography_name=name, table=table,
                                 dimension='residence' if table=='2.8' else 'establishment_type',
                                 category=category, measure='establishments' if i<3 else 'persons_engaged',
                                 value_count=value,
                                 source='derived' if i in derived else 'published_census_count',
                                 derivation='combined minus urban; rural cell printed blank' if i in derived else '',
                                 source_id='maharashtra_ec6_final', source_sha256=record['sha256'],
                                 pdf_page=page_index+1, status='historical_control_not_current_trip_demand'))
    if found != set(TABLES):
        raise ValueError('Missing selected tables')
    for (table,code), totals in district_totals.items():
        if totals != district_totals[('2.9' if table=='2.8' else '2.8',code)]:
            raise ValueError('Independent tables disagree on district totals')
    api_record, api_path = source('mospi_ec6_maharashtra_detail_page_1', 'employment')
    api = json.loads(api_path.read_text(encoding='utf-8'))
    for field,index in [('counter',2),('wcounter',5)]:
        if int(str(api[field]).replace(',','')) != state_totals['2.8'][index]:
            raise ValueError('Public dashboard and report totals differ')
    write('ec6_district_controls.csv',rows)
    audit = dict(rows=len(rows), district_count=35, tables=sorted(found),
                 state_totals_reconciled=True, district_totals_reconciled_between_tables=True,
                 public_dashboard_state_totals_reconciled=True, dashboard_sha256=api_record['sha256'],
                 derived_blank_cells=sum(r['source']=='derived' for r in rows),
                 limitations=['District boundaries are those of the historical census; no separate Palghar control.',
                              'Excludes crop production, plantation, public administration, defence and compulsory social security.',
                              'Establishment workers are not unique resident commuters or daily trips.',
                              'Combined categories and the two tables overlap; never sum across them.',
                              'Dashboard detail page contains only its first page, not the whole establishment dataset.'])
    Path(city.path('data/processed/observed/_ec6_controls_audit.json')).write_text(
        json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
