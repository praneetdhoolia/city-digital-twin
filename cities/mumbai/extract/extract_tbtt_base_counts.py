"""Separate 2018 site counts from the tunnel DPR's derived traffic aggregates."""
from decimal import Decimal
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

SID = 'mmrda_thane_borivali_tunnel_dpr'
OUTPUT_INPUTS = {
    'data/processed/observed/tbtt_2018_site_counts.csv': ['data/raw/traffic/mmrda_thane_borivali_tunnel_dpr_*.pdf'],
    'data/processed/observed/tbtt_2018_reported_aggregates.csv': ['data/raw/traffic/mmrda_thane_borivali_tunnel_dpr_*.pdf'],
    'data/processed/acquisition/tbtt_2018_count_audit.json': ['data/raw/traffic/mmrda_thane_borivali_tunnel_dpr_*.pdf'],
}
CLASSES = ('Cars', 'LCV', 'Trucks', 'Bus', 'Others/MAV')


def main():
    record, path = source(SID, 'traffic')
    survey = page_text(path, 36)
    normal = ' '.join(survey.split())
    if 'continuous period of seven days in the year 2018' not in normal:
        raise ValueError('Traffic survey year or duration changed')
    locations = re.findall(r'^\s*([1-4])\.\s+(.+?)\s*$', survey, re.M)
    if [n for n, _ in locations] != ['1', '2', '3', '4']:
        raise ValueError('Traffic station list changed')
    sites = {int(n): name for n, name in locations}
    site_detail = ' '.join(page_text(path, 44).split())
    if 'Classified Traffic Volume Count (CVC1) was conducted on Dattapada Road' not in site_detail:
        raise ValueError('First station detailed description changed')
    text = page_text(path, 48)
    body = text.split('Table 2 Traffic volume at four Mid Blocks for Base Year', 1)[1].split('Annual Average Daily Traffic', 1)[0]
    if not re.search(r'Locations\s+Cars\s+LCV\s+Trucks\s+Bus\s+Others/MAV', body):
        raise ValueError('Traffic count categories changed')
    parsed = re.findall(r'^\s*([1-4]|Average)\s+((?:\d[\d,]*\s+){4}\d[\d,]*)\s*$', body, re.M)
    if [name for name, _ in parsed] != ['1', '2', '3', '4', 'Average']:
        raise ValueError('Traffic table row coverage changed')
    values = {name: [int(value.replace(',', '')) for value in raw.split()] for name, raw in parsed}
    common = dict(source_id=SID, source_sha256=record['sha256'], source_pdf_page=48,
                  survey_year=2018, count_survey_days=7, exact_survey_dates='not_stated_in_count_section',
                  units_as_described='average_daily_traffic_counts',
                  class_universe='five_published_groups_not_proven_all_vehicles',
                  target_status='historical_evidence_not_current_target')
    observations, aggregates, checks = [], [], []
    for index, category in enumerate(CLASSES):
        parts = []
        for site_id, name in sites.items():
            count = values[str(site_id)][index]
            parts.append(count)
            observations.append(dict(**common, source='observed', source_table='2',
                                     site_id=site_id, location_as_listed=name,
                                     location_detail='CVC1 on Dattapada Road according to PDF page 44' if site_id == 1 else 'see_source_location_map',
                                     class_as_printed=category, reported_daily_count=count,
                                     direction_scope='not_disaggregated_in_table'))
        printed = values['Average'][index]
        calculated = Decimal(sum(parts)) / len(parts)
        delta = Decimal(printed) - calculated
        # Four rounded site means and a separately rounded mean of them.
        bound = Decimal('0.5') + sum(Decimal('0.5') for _ in parts) / len(parts)
        checks.append(dict(class_as_printed=category, mean_of_printed_sites=str(calculated),
                           printed_mean=printed, residual_daily_count=str(delta),
                           propagated_integer_rounding_envelope=str(bound),
                           status='exact' if delta == 0 else 'rounding_compatible' if abs(delta) <= bound else 'source_disagreement'))
        aggregates.append(dict(**common, source='derived_by_report', source_table='2 Average row',
                               aggregate_kind='equal_mean_of_four_different_sites',
                               class_as_printed=category, reported_daily_count=printed,
                               reference_label='2018 survey',
                               caveat='not_a_link_count_or_unique_regional_total'))
    following = ' '.join(text.split('Annual Average Daily Traffic (AADT)', 1)[1].split())
    if not all(fragment in following for fragment in (
        'average of ADT at four locations', 'Seasonality factor of 1 was applied', '31-Mar-18')):
        raise ValueError('Derived AADT description changed')
    base_classes = ('Car/Van/Jeep', 'Buses', 'LCV', 'Truck 2 Axle', 'Multi Axle Truck', 'Total')
    base = []
    for category in base_classes:
        match = re.findall(r'^\s*' + re.escape(category) + r'\s+(\d[\d,]*)\s*$', text, re.M)
        if len(match) != 1:
            raise ValueError('Ambiguous base-case aggregate category: ' + category)
        count = int(match[0].replace(',', ''))
        base.append(count)
        aggregates.append(dict(**common, source='derived_by_report', source_table='Base Case Traffic Numbers',
                               aggregate_kind='report_AADT_from_four_site_mean_and_seasonality_one',
                               class_as_printed=category, reported_daily_count=count,
                               reference_label='31-Mar-18 printed base-case label, not an established survey date',
                               caveat='class_relabelling_and_seasonality_require_validation'))
    if sum(base[:-1]) != base[-1]:
        raise ValueError('Base-case aggregate sum changed')
    write('tbtt_2018_site_counts.csv', observations)
    write('tbtt_2018_reported_aggregates.csv', aggregates)
    audit = dict(source_id=SID, source_sha256=record['sha256'], site_rows=len(observations),
                 aggregate_rows=len(aggregates), mean_checks=checks,
                 aggregate_sum_daily_count=base[-1], aggregate_sum_status='exact',
                 source_seasonality_factor=1, source_seasonality_status='report_assumption_not_adopted',
                 limitations=[
                     'Report hosted in 2024 and dated October 2022 contains a count survey from 2018.',
                     '31-Mar-18 labels a base case; exact seven-day survey dates remain unresolved.',
                     'The four-site average is neither a single link flow nor a regional traffic total.',
                     'Location 1 is listed as Magathane Midblock (WEH), but page 44 places CVC1 on Dattapada Road. Do not assign it to the WEH mainline without resolving the map.',
                     'Others/MAV and Trucks are relabelled Multi Axle Truck and Truck 2 Axle in the report aggregate. That crosswalk has not been independently established.',
                     'The five published groups do not establish coverage of motorcycles, three-wheelers, walking or cycling; no absent mode is assigned zero.',
                     'FY2023 and FY2029 traffic is projected using the later growth table; it is not a new count survey.',
                     'No proposed tunnel geometry, seasonality factor or growth rate is adopted as an operational model input.',
                 ])
    Path(city.path('data/processed/acquisition/tbtt_2018_count_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('site_rows', 'aggregate_rows', 'mean_checks', 'aggregate_sum_status')}))


if __name__ == '__main__':
    main()
