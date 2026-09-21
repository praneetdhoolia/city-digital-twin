"""Extract the published arterial study and expose its numerical disagreements.

These are literature evidence from other cities, not adopted model parameters.
Table values remain unchanged even where an identity or equation disagrees.
"""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

SID = 'urban_arterial_operating_speed_capacity_2017_pdf'
OUTPUT_INPUTS = {
    'data/processed/literature/arterial_2017_sites.csv': ['data/raw/research/urban_arterial_operating_speed_capacity_2017_pdf_*.pdf'],
    'data/processed/literature/arterial_2017_vehicle_dimensions.csv': ['data/raw/research/urban_arterial_operating_speed_capacity_2017_pdf_*.pdf'],
    'data/processed/literature/arterial_2017_pcu.csv': ['data/raw/research/urban_arterial_operating_speed_capacity_2017_pdf_*.pdf'],
    'data/processed/literature/arterial_2017_capacity.csv': ['data/raw/research/urban_arterial_operating_speed_capacity_2017_pdf_*.pdf'],
    'data/processed/literature/arterial_2017_validation.csv': ['data/raw/research/urban_arterial_operating_speed_capacity_2017_pdf_*.pdf'],
    'data/processed/acquisition/arterial_2017_audit.json': ['data/raw/research/urban_arterial_operating_speed_capacity_2017_pdf_*.pdf'],
}
VEHICLE_CODES = ('CS', 'CB', 'HV', '3W', '2W')
SECTION = r'([DJBC]-[46]-\d+)'
NUMBER = r'(\d+(?:\.\d+)?)'


def audit(checks, name, key, published, calculated, bound=Decimal(0)):
    difference = Decimal(published) - calculated
    checks.append(dict(check=name, key=key, published=str(published),
                       calculated=str(calculated), difference=str(difference),
                       rounding_bound=str(bound), status='exact' if difference == 0
                       else 'rounding_compatible' if abs(difference) <= bound
                       else 'source_disagreement'))


def main():
    record, path = source(SID, 'research')
    pages = {p: page_text(path, p) for p in (2, 3, 4, 7, 9, 10)}
    for table, page in ((1, 2), (2, 3), (3, 4), (4, 7), (5, 9), (6, 10)):
        if not re.search(r'Table\s+' + str(table) + r'\b', pages[page]):
            raise ValueError('Missing source table heading')

    def evidence(page, table):
        return dict(source='literature', source_id=SID, source_sha256=record['sha256'],
                    source_pdf_page=page, source_table=table,
                    model_assignment_status='not_adopted_requires_local_evidence')

    sites, dimensions, pcus, capacities, validation, checks = [], [], [], [], [], []
    pattern = re.compile(r'^\s*' + SECTION + r'\s+(\w+)\s+([46])\s+' + r'\s+'.join([NUMBER] * 5) + r'\s*$')
    for line in pages[2].splitlines():
        match = pattern.fullmatch(line)
        if match:
            row = dict(**evidence(2, 1), section_id=match[1], city_name=match[2],
                       total_road_lanes=int(match[3]))
            row.update({code + '_traffic_share_percent': match[i + 4] for i, code in enumerate(VEHICLE_CODES)})
            sites.append(row)
            # Each of five two-decimal shares can differ by half its quantum.
            audit(checks, 'composition_sums_to_100_percent', match[1], '100',
                  sum(Decimal(match[i]) for i in range(4, 9)), Decimal('0.005') * len(VEHICLE_CODES))
    if len(sites) != 12 or len({r['section_id'] for r in sites}) != len(sites):
        raise ValueError('Unexpected study site table')

    pattern = re.compile(r'^\s*(.+?)\s+\((CS|CB|HV|3 W|2 W)\)\s+(.+?)\s+' + r'\s+'.join([NUMBER] * 3) + r'\s*$')
    for line in pages[3].splitlines():
        match = pattern.fullmatch(line)
        if match:
            dimensions.append(dict(**evidence(3, 2), vehicle_code=match[2].replace(' ', ''),
                                   vehicle_type=match[1], vehicles_included=match[3],
                                   length_m=match[4], width_m=match[5], projected_area_m2=match[6]))
            audit(checks, 'published_area_equals_length_times_width_m2', match[2], match[6],
                  Decimal(match[4]) * Decimal(match[5]), Decimal('0.005'))
    if {r['vehicle_code'] for r in dimensions} != set(VEHICLE_CODES) or len(dimensions) != len(VEHICLE_CODES):
        raise ValueError('Unexpected vehicle dimension table')

    pattern = re.compile(r'^\s*' + SECTION + r'\s+(\w+)\s+' + r'\s+'.join([NUMBER] * 8) + r'\s*$')
    for line in pages[4].splitlines():
        match = pattern.fullmatch(line)
        if match:
            for i, code in enumerate(VEHICLE_CODES[1:]):
                pcus.append(dict(**evidence(4, 3), section_id=match[1], city_name=match[2], vehicle_code=code,
                                 mean_pcu=match[i + 3], standard_deviation_pcu=match[i + 7],
                                 basis='speed_and_projected_area_relative_to_standard_small_car'))
    if len(pcus) != len(sites) * (len(VEHICLE_CODES) - 1):
        raise ValueError('Unexpected PCU table')
    expected_pcu_keys = {(r['section_id'], code) for r in sites for code in VEHICLE_CODES[1:]}
    if {(r['section_id'], r['vehicle_code']) for r in pcus} != expected_pcu_keys:
        raise ValueError('PCU table has duplicate or missing site/category pairs')
    site_cities = {r['section_id']: r['city_name'] for r in sites}
    if any(r['city_name'] != site_cities[r['section_id']] for r in pcus):
        raise ValueError('PCU site names disagree with the site table')

    # Table 4 occupies the right column, beside prose and Equation 2.
    pattern = re.compile(SECTION + r'\s+' + r'\s+'.join([NUMBER] * 3) + r'(?:\s+' + NUMBER + r')?\s*$')
    site_by_id = {r['section_id']: r for r in sites}
    for line in pages[7].splitlines():
        match = pattern.search(line)
        if match:
            capacities.append(dict(**evidence(7, 4), section_id=match[1],
                                   directional_capacity_pcu_h=match[2], operating_speed_km_h=match[3],
                                   lane_capacity_pcu_h_lane=match[4], group_average_capacity_pcu_h_lane=match[5],
                                   capacity_basis='Greenshields_fit_to_speed_density_data_not_observed_maximum',
                                   speed_basis='85th_percentile_free_flow_standard_car'))
            directional_lanes = Decimal(site_by_id[match[1]]['total_road_lanes']) / 2
            audit(checks, 'directional_capacity_equals_lane_capacity_times_directional_lanes', match[1],
                  match[2], Decimal(match[4]) * directional_lanes, (1 + directional_lanes) / 2)
    if len(capacities) != len(sites) or {r['section_id'] for r in capacities} != set(site_by_id):
        raise ValueError('Unexpected capacity table')

    eq = re.search(r'Lane capacity\s*=\s*' + NUMBER + r'\s*−\s*' + NUMBER + r'\s+Vos\s*\+\s*' + NUMBER, pages[7])
    if not eq:
        raise ValueError('Equation 2 extraction changed')
    intercept, linear_magnitude, quadratic = [Decimal(eq[i]) for i in (1, 2, 3)]
    coefficient_patterns = (
        ('intercept', r'^Intercept\s+', intercept),
        ('linear_magnitude', r'^Operating speed \(Vos\)\s+', linear_magnitude),
        ('quadratic', r'^\(Operating speed\)2\s+', quadratic),
    )
    coefficients = []
    for name, prefix, equation_value in coefficient_patterns:
        match = re.search(prefix + NUMBER + r'\s+' + NUMBER + r'\s+' + NUMBER, pages[9], re.MULTILINE)
        if not match:
            raise ValueError('Coefficient table extraction changed: ' + name)
        coefficients.append(dict(term=name, equation_2_value=str(equation_value), table_5_value=match[1],
                                 table_5_t_statistic=match[2], table_5_p_value=match[3]))
        audit(checks, 'equation_and_coefficient_table_agree', name, match[1], equation_value)

    pattern = re.compile(r'^\s*' + SECTION + r'\s+' + r'\s+'.join([NUMBER] * 5) + r'\s+')
    for line in pages[10].splitlines():
        match = pattern.match(line)
        if match:
            row = dict(**evidence(10, 6), section_id=match[1], operating_speed_km_h=match[2],
                       directional_capacity_pcu_h=match[3], lane_capacity_from_field_fit_pcu_h_lane=match[4],
                       lane_capacity_from_equation_reported_pcu_h_lane=match[5], reported_difference_percent=match[6])
            speed, field, predicted = (Decimal(match[i]) for i in (2, 4, 5))
            equation_prediction = intercept - linear_magnitude * speed + quadratic * speed * speed
            row['equation_2_recomputed_capacity_pcu_h_lane'] = str(equation_prediction)
            row['table_capacities_recomputed_absolute_difference_percent'] = str(abs(predicted - field) / field * 100)
            validation.append(row)
            # Printed coefficients are reproduced exactly; this tests the
            # displayed equation, not unknown full-precision regression output.
            audit(checks, 'printed_equation_reproduces_table_6_capacity', match[1], match[5], equation_prediction, Decimal('0.5'))
            audit(checks, 'table_6_relative_error_percent_from_printed_capacities', match[1], match[6],
                  abs(predicted - field) / field * 100, Decimal('0.005'))
    if len(validation) != 2:
        raise ValueError('Unexpected validation table')
    narrative = re.search(r'sections are estimated\s+' + NUMBER + r'\s+and\s+' + NUMBER + r'\s+km/h', pages[7])
    if not narrative:
        raise ValueError('Validation narrative extraction changed')
    for i, row in enumerate(validation, 1):
        audit(checks, 'narrative_and_table_6_speed_km_h', row['section_id'], narrative[i], Decimal(row['operating_speed_km_h']))

    out = Path(city.path('data/processed/literature'))
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (('sites', sites), ('vehicle_dimensions', dimensions), ('pcu', pcus),
                       ('capacity', capacities), ('validation', validation)):
        write(out / ('arterial_2017_' + name + '.csv'), rows)
    report = dict(source='derived', source_id=SID, source_sha256=record['sha256'],
                  row_counts=dict(sites=len(sites), vehicle_dimensions=len(dimensions), pcu=len(pcus),
                                  capacity=len(capacities), validation=len(validation)),
                  equation_2_coefficients=coefficients, checks=checks,
                  check_status_counts=dict(Counter(c['status'] for c in checks)),
                  applicability=[
                      'Other Indian cities; no observed Mumbai road capacities or assigned model values.',
                      'Four- and six-lane divided, flat midblocks selected to exclude junctions, stops, parking and other side friction.',
                      'Capacity was estimated by fitting speed-density curves; most sites did not reach capacity during observation.',
                      'Operating speed is a measured 85th percentile for standard cars in free flow, not a posted speed limit.',
                      'PCU factors depend on measured relative speeds and projected areas; they are not universal vehicle constants.',
                      'Printed equations, validation claims and capacity cells disagree; retain alternatives pending corroboration.',
                      'Table 5 prints the linear coefficient magnitude without the negative sign used in Equation 2.',
                  ])
    Path(city.path('data/processed/acquisition/arterial_2017_audit.json')).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('row_counts', 'check_status_counts')}))


if __name__ == '__main__':
    main()
