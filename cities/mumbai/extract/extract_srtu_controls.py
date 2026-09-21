"""Preserve MoRTH's historical operator cells, missing values and inconsistencies."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/srtu_historical_controls.csv': [
        'data/raw/transit/morth_srtu_review_2019_2022_*.pdf'],
    'data/processed/acquisition/srtu_controls_audit.json': [
        'data/raw/transit/morth_srtu_review_2019_2022_*.pdf'],
}
SOURCE_ID = 'morth_srtu_review_2019_2022'
OPERATORS = {11: 'Maharashtra SRTC', 46: 'BEST Undertaking', 48: 'Navi Mumbai MT',
             51: 'Thane MT', 52: 'Kalyan Dombivali MT'}
YEARS = ('2021-22', '2020-21', '2019-20')
# PDF page numbers and the ordered Annexure I column headings, not model values.
TABLES = {
    110: [('average_fleet_held', 'buses_count', 'Average Fleet Held'),
          ('average_fleet_operated', 'buses_count', 'Average Fleet Operated'),
          ('fleet_utilisation', 'percent', 'Fleet Utilisation')],
    111: [('average_fleet_age', 'years', 'Avg Age of Fleet'),
          ('overaged_vehicles', 'percent', 'Over aged vehicles'),
          ('fuel_efficiency_cng', 'km_per_kg', 'of CNG')],
    112: [('fuel_efficiency_hsd', 'km_per_litre', 'litre of HSD'),
          ('effective_revenue_kilometres', 'lakh_km', 'Effective Kilometres'),
          ('staff_strength', 'persons_count', 'Staff Strength')],
    113: [('staff_bus_ratio', 'staff_per_bus', 'Staff/Bus Ratio'),
          ('staff_productivity', 'km_per_staff_per_day', 'Staff Productivity'),
          ('vehicle_productivity', 'km_per_bus_per_day', 'Vehicle Productivity')],
    114: [('passenger_kilometres_offered', 'lakh_passenger_km', 'Passenger Kilometres Offered'),
          ('passenger_kilometres_performed', 'lakh_passenger_km', 'Passenger KMS Performed'),
          ('occupancy_ratio', 'percent', 'Occupancy Ratio')],
    115: [('passengers_carried', 'lakh_passengers', 'Passengers Carried'),
          ('passengers_carried_per_bus_day', 'passengers_per_bus_per_day', 'Passengers carried per Bus/Day')],
}


def extract():
    record, path = source(SOURCE_ID, 'transit')
    rows = []
    for page, metrics in TABLES.items():
        text = subprocess.run(['pdftotext', '-layout', '-f', str(page), '-l', str(page),
                               str(path), '-'], check=True, capture_output=True,
                              encoding='utf-8').stdout
        compact = ' '.join(text.split())
        if ' '.join(YEARS) not in compact or any(label not in compact for _, _, label in metrics):
            raise ValueError(f'Source table headings changed on page {page}')
        for serial, operator in OPERATORS.items():
            matches = re.findall(r'^\s*' + str(serial) + r'\s+' + re.escape(operator)
                                 + r'\s+(.+)$', text, re.MULTILINE)
            if len(matches) != 1:
                raise ValueError(f'Expected one row for {operator} on page {page}')
            cells = matches[0].split()
            if len(cells) != len(metrics) * len(YEARS):
                raise ValueError(f'Unexpected column count for {operator} on page {page}')
            for i, (metric, unit, _) in enumerate(metrics):
                for j, year in enumerate(YEARS):
                    raw = cells[i * len(YEARS) + j]
                    if raw != 'NR' and not re.fullmatch(r'\d[\d,]*(?:\.\d+)?', raw):
                        raise ValueError('Unknown cell syntax: ' + raw)
                    value = '' if raw == 'NR' else str(Decimal(raw.replace(',', '')))
                    rows.append(dict(operator_name=operator, source_row_serial=serial,
                                     financial_year=year, metric=metric, value_as_printed=raw,
                                     numeric_value=value, unit=unit,
                                     reported_status='not_reported' if raw == 'NR' else 'reported',
                                     source='operator_reported_in_official_compilation',
                                     source_id=SOURCE_ID, source_sha256=record['sha256'],
                                     source_page_1_based=page, model_ready=False,
                                     geography_scope='statewide_not_mmr' if serial == 11 else 'operator_network'))
    return rows


def interval(row):
    """Half a printed unit bounds rounding; it is not a calibration tolerance."""
    value = Decimal(row['numeric_value'])
    half_unit = Decimal(10) ** value.as_tuple().exponent / 2
    return max(Decimal(0), value - half_unit), value + half_unit


def audit(rows):
    indexed = {(r['operator_name'], r['financial_year'], r['metric']): r for r in rows}
    if len(indexed) != len(rows):
        raise ValueError('Duplicate source cell')
    checks = []
    identities = [('fleet_utilisation', 'average_fleet_operated', 'average_fleet_held'),
                  ('occupancy_ratio', 'passenger_kilometres_performed', 'passenger_kilometres_offered')]
    for operator in OPERATORS.values():
        for year in YEARS:
            for ratio, numerator, denominator in identities:
                selected = [indexed[(operator, year, m)] for m in (ratio, numerator, denominator)]
                check = dict(operator_name=operator, financial_year=year, metric=ratio,
                             identity=f'100 * {numerator} / {denominator}')
                if any(r['reported_status'] != 'reported' for r in selected):
                    check['status'] = 'not_checkable_missing_source_cell'
                else:
                    printed, num, den = (interval(r) for r in selected)
                    if den[0] <= 0:
                        check['status'] = 'not_checkable_nonpositive_denominator'
                    else:
                        lower, upper = 100 * num[0] / den[1], 100 * num[1] / den[0]
                        check.update(derived_percent_lower=str(lower), derived_percent_upper=str(upper),
                                     printed_percent=selected[0]['numeric_value'],
                                     status='compatible_at_printed_precision' if
                                     lower <= printed[1] and upper >= printed[0] else 'source_disagreement')
                checks.append(check)
    return dict(status='historical_operator_evidence_not_current_targets', rows=len(rows),
                reported_status_counts=dict(Counter(r['reported_status'] for r in rows)),
                arithmetic_check_counts=dict(Counter(c['status'] for c in checks)),
                arithmetic_checks=checks,
                unresolved_source_issues=[
                    'Navi Mumbai MT passengers carried in 2021-22 is printed as 1.34 lakh, versus 337.44 and 670.34 lakh in the adjacent columns. It is retained without rescaling.',
                    'Navi Mumbai MT fleet age is NR in Annexure I; Annexure VI prints zero. Zero must not replace the missing age.',
                    'Lakh passenger-kilometres for Navi Mumbai MT require independent unit and denominator confirmation.',
                    'Zero CNG efficiency for Kalyan Dombivali MT is retained as printed, not interpreted as an operating vehicle fuel-efficiency coefficient.'],
                limitations=[
                    'Financial years include pandemic restrictions and cannot stand in for the 2026 operating year.',
                    'Maharashtra SRTC totals cover its entire network and cannot be assigned to MMR.',
                    'Fleet averages are not peak availability, vehicle capacity, seated/standing composition or route allocations.',
                    'Passenger counts are operator-reported carriage; unique journeys and transfers need separate definitions.',
                    'NR means not reported and remains distinct from zero.',
                    'Rounding intervals only audit printed arithmetic; no original cell is changed.',
                    'Repetition elsewhere in the same publication is not independent corroboration.'])


def main():
    rows = extract()
    result = audit(rows)
    write('srtu_historical_controls.csv', rows)
    Path(city.path('data/processed/acquisition/srtu_controls_audit.json')).write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('rows', 'reported_status_counts', 'arithmetic_check_counts')}))


if __name__ == '__main__':
    main()
