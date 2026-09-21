"""Extract dated port-rake times and reconcile printed cargo totals.

Blank departures stay missing. TEUs count cargo units, not vehicles or wagons.
These handled-rake samples do not establish a complete train operating plan.
"""
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/jnpa_rake_observations.csv': ['data/raw/freight/jnpa_daily_icd_*.pdf'],
    'data/processed/acquisition/jnpa_rake_audit.json': ['data/raw/freight/jnpa_daily_icd_*.pdf'],
}


def main():
    rows, checks = [], []
    date_pattern = r'\d{2}-[A-Za-z]{3}-\d{4}\s+\d{1,2}:\d{2}'
    for provenance in sorted(Path(city.path('data/raw/freight')).glob('provenance_jnpa_daily_icd_*.json')):
        source_id = provenance.stem.removeprefix('provenance_')
        record, path = source(source_id, 'freight')
        result = subprocess.run(['pdftotext', '-f', '2', '-l', '2', '-layout', str(path), '-'],
                                check=True, capture_output=True, encoding='utf-8')
        text = result.stdout
        report_day = re.search(r'RAKES HANDLED ON\s+(\d+)\s*-\s*([A-Z]+)\s*-\s*(\d{4})', text)
        if report_day is None:
            raise ValueError('Missing handled-date header: ' + source_id)
        month_format = '%b' if len(report_day.group(2)) == 3 else '%B'
        handled_date = datetime.strptime('-'.join(report_day.groups()), '%d-' + month_format + '-%Y').date().isoformat()
        grand_rows = [line for line in text.splitlines() if 'Grand Total' in line]
        if len(grand_rows) != 1:
            raise ValueError('Expected one grand-total row: ' + source_id)
        grand_values = [int(v) for v in grand_rows[0].split() if v.isdigit()]
        if not grand_values or len(grand_values) % 2:
            raise ValueError('Cargo column counts are not paired')
        width = len(grand_values) // 2
        source_rows, column_sums = [], [0] * len(grand_values)
        for line in text.splitlines():
            match = re.search(r'\bR\d{6}\b', line)
            if not match:
                continue
            dates = list(re.finditer(date_pattern, line))
            if len(dates) not in (2, 3):
                raise ValueError('Expected arrival, completion and optional departure: ' + line)
            before_times = line[match.end():dates[0].start()]
            cargo = [int(v) for v in before_times.split() if v.isdigit()]
            if len(cargo) != len(grand_values):
                raise ValueError('Rake cargo cells differ from grand-total width: ' + match.group())
            outgoing, incoming = cargo[:width], cargo[width:]
            sums_agree = sum(outgoing[:-1]) == outgoing[-1] and sum(incoming[:-1]) == incoming[-1]
            parsed = [datetime.strptime(d.group(), '%d-%b-%Y %H:%M') for d in dates]
            ordered = parsed == sorted(parsed)
            values = dict(source_id=source_id, source_sha256=record['sha256'], source_page=2,
                          handled_date=handled_date, rake_id=match.group(),
                          arrival_local_raw=dates[0].group(), completion_local_raw=dates[1].group(),
                          departure_local_raw=dates[2].group() if len(dates) == 3 else '',
                          export_discharged_teu_count=outgoing[-1], import_loaded_teu_count=incoming[-1],
                          cargo_subtotals_agree=sums_agree, timestamp_order_agrees=ordered,
                          arrival_to_completion_minutes=(parsed[1] - parsed[0]).total_seconds() / 60,
                          arrival_to_departure_minutes=(parsed[2] - parsed[0]).total_seconds() / 60 if len(parsed) == 3 else '',
                          prefix_on_rake_line_raw=line[:dates[0].start()].strip(),
                          source='operator_reported_handled_rake',
                          validation_status='source_totals_checked_route_clock_and_operating_universe_unresolved')
            source_rows.append(values)
            column_sums = [a+b for a,b in zip(column_sums, cargo)]
        if not source_rows or len({r['rake_id'] for r in source_rows}) != len(source_rows):
            raise ValueError('Empty or duplicate rake records: ' + source_id)
        check = dict(source_id=source_id, handled_date=handled_date, extracted_rakes=len(source_rows),
                     cargo_columns=len(grand_values), printed_column_totals=grand_values,
                     calculated_column_totals=column_sums, grand_totals_agree=column_sums == grand_values,
                     rake_subtotal_disagreements=sum(not r['cargo_subtotals_agree'] for r in source_rows),
                     timestamp_order_disagreements=sum(not r['timestamp_order_agrees'] for r in source_rows),
                     missing_departures=sum(not r['departure_local_raw'] for r in source_rows))
        checks.append(check)
        rows.extend(source_rows)
    if not rows:
        raise ValueError('No acquired daily rake reports')
    write('jnpa_rake_observations.csv', rows)
    audit = dict(schema_version=1, reports=checks, rake_rows=len(rows),
                 limits='Only rakes on each printed handled-date table. Arrival/departure can fall outside that day. No timezone is assigned. Blank departures remain missing. Multiline origin/destination and train-label cells are not resolved; the retained line prefix is partial text, not a route assignment. Terminal TEU columns differ between report layouts and are reconciled within each report only. TEUs are not wagons, vehicles or persons. No inference of complete traffic, network paths, rake length or line occupation.')
    Path(city.path('data/processed/acquisition/jnpa_rake_audit.json')).write_text(json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
