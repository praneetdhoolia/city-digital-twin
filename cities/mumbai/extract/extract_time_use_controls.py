"""Extract published state time-use estimates, retaining their denominators.

State averages are benchmarks, not local diaries or travel-time observations.
The report allocates simultaneous activities within time slots; participants
and all persons are different denominators and must remain separate.
"""
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
import re

from pypdf import PdfReader
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/state_time_use_controls.csv': ['data/raw/demand/tus_2024_report_*.pdf'],
    'data/processed/observed/_time_use_controls_audit.json': ['data/raw/demand/tus_2024_report_*.pdf'],
}
STATEMENTS = {
    '3.1': ('major_activity', 'participation', 'percent'),
    '4.1': ('major_activity', 'per_participant', 'minutes_per_day'),
    '5.1': ('all_activities', 'participation', 'percent'),
    '6.1': ('all_activities', 'per_participant', 'minutes_per_day'),
    '7.1': ('all_activities', 'per_person', 'minutes_per_day'),
}


def main():
    descriptor = json.loads(Path(city.path('city.json')).read_text(encoding='utf-8'))
    region = descriptor['jurisdiction']['subdivision']
    record, path = source('tus_2024_report', 'demand')
    reader = PdfReader(path)
    rows, found, headers = [], set(), {}
    values = {}
    for page_index, page in enumerate(reader.pages):
        plain = page.extract_text() or ''
        match = re.search(r'Statement (\d+\.\d+):', plain)
        if not match or match[1] not in STATEMENTS or region not in plain:
            continue
        statement = match[1]
        lines = [line.strip() for line in page.extract_text(extraction_mode='layout').splitlines()]
        positions = [i for i, line in enumerate(lines) if line == region]
        if len(positions) != 1 or statement in found:
            raise ValueError('Ambiguous regional table')
        found.add(statement)
        header = ' '.join(lines[:positions[0]])
        if not all(word in header for word in ('rural', 'urban', 'rural+urban', 'male', 'female', 'person')):
            raise ValueError('Unrecognised table dimensions')
        # Retain the complete statement title without the preceding states.
        headers[statement] = ' '.join(plain[match.start():].splitlines()[:3])
        table_rows = [line for line in lines[positions[0]+1:] if line][:9]
        if len(table_rows) != 9:
            raise ValueError('Incomplete activity classification')
        scope, denominator, unit = STATEMENTS[statement]
        for line in table_rows:
            cells = re.fullmatch(r'(.+?)\s+((?:\d+(?:\.\d+)?\s+){8}\d+(?:\.\d+)?)', line)
            if not cells:
                raise ValueError('Unexpected activity row: '+line)
            activity = cells[1].strip()
            for index, raw in enumerate(cells[2].split()):
                value = Decimal(raw)
                if not value.is_finite() or not 0 <= value <= (100 if unit == 'percent' else 1440):
                    raise ValueError('Out-of-range estimate')
                residence = ('rural', 'urban', 'rural+urban')[index//3]
                sex = ('male', 'female', 'person')[index%3]
                key = (statement, activity, residence, sex)
                if key in values:
                    raise ValueError('Duplicate table cell')
                values[key] = value
                rows.append(dict(region=region, observation_year=2024, minimum_age_years=6,
                                 activity=activity, residence=residence, sex=sex,
                                 activity_scope=scope, denominator=denominator, value=str(value), unit=unit,
                                 source='published_survey_estimate', source_id='tus_2024_report',
                                 source_sha256=record['sha256'], statement=statement, pdf_page=page_index+1,
                                 status='state_benchmark_not_local_diary'))
    if found != set(STATEMENTS) or len(rows) != 405:
        raise ValueError('Incomplete selected statement coverage')
    totals, reconciled = defaultdict(Decimal), 0
    for (statement, activity, residence, sex), value in values.items():
        if statement != '7.1':
            continue
        rate = values[('5.1', activity, residence, sex)]
        participant = values[('6.1', activity, residence, sex)]
        # Exact rounding intervals: rates to 0.1 percentage point and time to
        # whole minutes. This tolerance follows published precision, not fit.
        low = max(Decimal(0), rate-Decimal('.05'))*max(Decimal(0), participant-Decimal('.5'))/100
        high = min(Decimal(100), rate+Decimal('.05'))*(participant+Decimal('.5'))/100
        if high < value-Decimal('.5') or low > value+Decimal('.5'):
            raise ValueError('Denominator reconciliation failed')
        totals[(residence, sex)] += value
        reconciled += 1
    # Nine rounded activity durations may differ from 1440 by at most 4.5 min.
    if any(abs(total-1440) > Decimal('4.5') for total in totals.values()):
        raise ValueError('Daily activity duration does not reconcile')
    write('state_time_use_controls.csv', rows)
    audit = dict(source_sha256=record['sha256'], rows=len(rows), statement_headers=headers,
                 rate_duration_reconciliations=reconciled,
                 daily_minutes=[dict(residence=k[0], sex=k[1], minutes=int(v)) for k,v in totals.items()],
                 limitations=['State averages do not establish local diary sequences or trip lengths.',
                              'Survey age coverage excludes children under six.',
                              'Activity participation is not workforce participation or a trip rate.',
                              'Combined geography and sex categories overlap their components.'])
    Path(city.path('data/processed/observed/_time_use_controls_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('statement_headers','limitations')}))


if __name__ == '__main__':
    main()
