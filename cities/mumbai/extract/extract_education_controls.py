"""Preserve public state education statistics with API coverage checks.

These are state controls and published estimates, not local facility records
or evidence of daily attendance. Aggregate and component categories overlap.
"""
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/state_education_controls.csv': [
        'data/raw/education/mospi_*.json'],
    'data/processed/observed/_education_controls_audit.json': [
        'data/raw/education/mospi_*.json'],
}


def main():
    descriptor = json.loads(Path(city.path('city.json')).read_text(encoding='utf-8'))
    region = descriptor['jurisdiction']['subdivision']
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    rows, queries, gender_groups = [], [], defaultdict(dict)
    for entry in catalogue['sources']:
        if entry['category'] != 'education' or not entry['id'].startswith('mospi_'):
            continue
        parsed = urlparse(entry['url'])
        if parsed.hostname != 'api.mospi.gov.in':
            continue
        query = parse_qs(parsed.query)
        if 'indicator_code' not in query or 'state_code' not in query:
            continue
        record, path = source(entry['id'], entry['category'])
        response = json.loads(path.read_text(encoding='utf-8'))
        metadata = response['meta_data']
        if response.get('statusCode') is not True:
            raise ValueError('API did not report success')
        # Multi-page selections must be collected and reconciled before extension.
        if metadata['totalPages'] != 1 or metadata['page'] != 1:
            raise ValueError('Incomplete multi-page education selection')
        if len(response['data']) != metadata['totalRecords'] or not response['data']:
            raise ValueError('API record count mismatch or empty response')
        seen = set()
        dataset = parsed.path.split('/')[2]
        for original in response['data']:
            if original['state'] != region or original['year'] != query['year'][0]:
                raise ValueError('API ignored requested geographical or temporal filter')
            value = Decimal(original['value'])
            if not value.is_finite() or value < 0 or value != int(value):
                raise ValueError('Expected a reported nonnegative whole count')
            dimensions = {k:v for k,v in original.items() if k not in ('indicator', 'year', 'state', 'value')}
            key = json.dumps(dimensions, sort_keys=True)
            if key in seen:
                raise ValueError('Duplicate education dimensions')
            seen.add(key)
            rows.append(dict(dataset=dataset, indicator_code=query['indicator_code'][0],
                             indicator=original['indicator'], observation_year=original['year'],
                             region=region, dimensions_json=key, reported_count=int(value),
                             source='published_statistic', source_id=entry['id'],
                             source_sha256=record['sha256'], status='state_aggregate_not_local_trip_demand'))
            if 'gender' in dimensions:
                others = {k:v for k,v in dimensions.items() if k!='gender'}
                gender_groups[(entry['id'], json.dumps(others, sort_keys=True))][dimensions['gender']] = int(value)
        queries.append(dict(source_id=entry['id'], rows=len(response['data']),
                            all_pages_acquired=True, requested_state_and_year_match=True))
    if not queries:
        raise ValueError('No acquired education selections')
    for key, values in gender_groups.items():
        if set(values) == {'Boys', 'Girls', 'Total'}:
            left, right, total = 'Boys', 'Girls', 'Total'
        elif set(values) == {'Male', 'Female', 'Both'}:
            left, right, total = 'Male', 'Female', 'Both'
        else:
            raise ValueError('Unrecognised or incomplete gender categories: '+str(key))
        if values[left]+values[right] != values[total]:
            raise ValueError('Published gender counts do not reconcile: '+str(key))
    write('state_education_controls.csv', rows)
    audit = dict(rows=len(rows), queries=queries, gender_groups_reconciled=len(gender_groups),
                 status='publication_checks_passed_local_allocation_unresolved',
                 limitations=[
                     'State API codes differ by dataset; geography was selected by metadata label and checked in every response.',
                     'State totals cannot substitute for metropolitan or school-level controls.',
                     'Enrolments do not establish attendance, travel days, mode or daily trip rates.',
                     'Combined education levels and all-management categories overlap components.',
                     'AISHE enrolment is labelled estimated by its publisher.',
                     'The returned reference years differ and do not establish 2026 conditions.'])
    Path(city.path('data/processed/observed/_education_controls_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='queries'}, indent=2))


if __name__ == '__main__':
    main()
