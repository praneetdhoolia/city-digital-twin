"""Extract Mumbai Port's loaded/empty monthly rake controls with subtotal checks."""
import json
from pathlib import Path
import re
import subprocess

import city
import harvest
from register_port_rail_sources import STATISTICS
from extract_census_controls import write

OUTPUT_INPUTS = {
    'data/processed/observed/mumbai_port_monthly_rakes.csv': ['data/raw/freight/mumbai_port_rail_statistics.zip'],
    'data/processed/acquisition/mumbai_port_monthly_rakes_audit.json': ['data/raw/freight/mumbai_port_rail_statistics.zip'],
}


def main():
    source_id = 'mumbai_port_rail_1778075791'
    record, _ = harvest.source(STATISTICS.id, STATISTICS.category, source_id)
    with harvest.as_file(STATISTICS.id, STATISTICS.category, source_id) as path:
        text = subprocess.run(['pdftotext', '-layout', str(path), '-'], check=True,
                              capture_output=True, encoding='utf-8').stdout
    headers = list(re.finditer(r'(\d{4}-\d{2}) (Inward|Outward) Traffic', text))
    if [m.group(2) for m in headers] != ['Inward', 'Outward']:
        raise ValueError('Expected separate inward and outward tables')
    rows, checks, derivations = [], [], []
    for index, header in enumerate(headers):
        body = text[header.end():headers[index+1].start() if index+1 < len(headers) else len(text)]
        lines = body.splitlines()
        total_lines = [line for line in lines if re.match(r'\s*TOTAL\b', line)]
        if len(total_lines) != 1:
            raise ValueError('Expected one annual subtotal per direction')
        totals = list(re.finditer(r'\b\d+\b', total_lines[0]))
        loaded_labels = (['cement', 'hr_coils_iron_steel', 'car', 'other'] if header.group(2) == 'Inward'
                         else ['muriate_of_potash', 'wheat', 'hr_coils', 'other'])
        labels = ['loaded_rakes'] + ['loaded_' + label for label in loaded_labels] + [
            'empty_rakes', 'empty_boxnhl_box', 'empty_bcn_bcnhl', 'empty_nmg', 'empty_bost_brn_bfn_bosm', 'total_rakes']
        if len(totals) != len(labels):
            raise ValueError('Unexpected cargo/wagon column count')
        centres = [(m.start()+m.end()) / 2 for m in totals]
        periods = {}
        current = None
        for line in lines:
            month = re.match(r'^([A-Za-z]{3}-\d{2})\b', line)
            if month:
                current = month.group(1)
                if current in periods:
                    raise ValueError('Repeated month in direction table')
                periods[current] = [None] * len(labels)
                line = ' ' * month.end() + line[month.end():]
            if re.match(r'\s*TOTAL\b', line):
                current = None
            if current is None:
                continue
            for match in re.finditer(r'\b\d+\b', line):
                centre = (match.start()+match.end()) / 2
                column = min(range(len(centres)), key=lambda c: abs(centres[c] - centre))
                spacing = min(abs(centres[column]-v) for c,v in enumerate(centres) if c != column)
                if abs(centres[column]-centre) > spacing / 2 or periods[current][column] is not None:
                    raise ValueError('Ambiguous positioned numeric cell')
                periods[current][column] = int(match.group())
        annual = [int(m.group()) for m in totals]
        for period, values in periods.items():
            derived = {}
            for subtotal, members in [(0, range(1, 5)), (5, range(6, 10))]:
                missing = [c for c in members if values[c] is None]
                if len(missing) == 1 and values[subtotal] is not None:
                    column = missing[0]
                    values[column] = values[subtotal] - sum(values[c] for c in members if c != column)
                    if values[column] < 0:
                        raise ValueError('Negative residual from printed subtotal')
                    derived[column] = labels[subtotal] + ' - (' + ' + '.join(labels[c] for c in members if c != column) + ')'
                    derivations.append(dict(direction=header.group(2).lower(), period=period,
                                            field=labels[column], value_count=values[column], derived_from=derived[column]))
            if any(v is None for v in values):
                raise ValueError('Unresolved blank table cells')
            for label, observed, calculated in [('loaded', values[0], sum(values[1:5])),
                                               ('empty', values[5], sum(values[6:10])),
                                               ('all', values[10], values[0] + values[5])]:
                checks.append(dict(direction=header.group(2).lower(), period=period, check=label,
                                   reported=observed, calculated=calculated, agrees=observed == calculated))
            for column, label in enumerate(labels):
                rows.append(dict(source_id=source_id, source_sha256=record['sha256'], source_page=1,
                                 direction=header.group(2).lower(), fiscal_year=header.group(1), month_label=period,
                                 measure=label, value_count=values[column],
                                 source='derived_from_printed_subtotal' if column in derived else 'operator_reported',
                                 derived_from=derived.get(column, ''), raw_cell_blank=column in derived,
                                 is_subtotal=column in (0, 5, 10)))
        for column, label in enumerate(labels):
            calculated = sum(v[column] for v in periods.values())
            checks.append(dict(direction=header.group(2).lower(), period=header.group(1), check=label,
                               reported=annual[column], calculated=calculated, agrees=annual[column] == calculated))
    write('mumbai_port_monthly_rakes.csv', rows)
    result = dict(schema_version=1, cells=len(rows), checks=len(checks),
                  disagreements=sum(not c['agrees'] for c in checks), derivations=derivations, reconciliation=checks,
                  limits='Port railway rakes, not citywide freight trains or wagons. Monthly inward/outward loaded/empty counts can differ; no balance is imposed. Commodity and wagon classes are source categories, not vehicle capacity. No operating times or network paths are inferred. Subtotals must not be added to their components.')
    Path(city.path('data/processed/acquisition/mumbai_port_monthly_rakes_audit.json')).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'reconciliation'}))


if __name__ == '__main__':
    main()
