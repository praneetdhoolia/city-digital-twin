"""Extract dated control-system claims without adopting project targets as supply."""
from decimal import Decimal
import json
from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pypdf import PdfReader
import city
from extract_census_controls import source, write
from extract_suburban_fleet_claims import one

OUTPUT_INPUTS = {
    'data/processed/observed/mrvc_rail_control_claims_2023_24.csv': ['data/raw/rail/mrvc_annual_2023_24_*.pdf'],
    'data/processed/acquisition/rail_control_evidence_audit.json': ['data/raw/rail/mrvc_annual_2023_24_*.pdf'],
    'data/processed/acquisition/cr_signalling_page_dependencies.json': ['data/raw/rail/cr_signalling_assets_page_*.html'],
}


def main():
    sid = 'mrvc_annual_2023_24'
    record, path = source(sid, 'rail')
    pdf = PdfReader(path)
    page_number = 134
    text = ' '.join(pdf.pages[page_number - 1].extract_text().split())
    required = ('Annual Report 2023-24', 'between Kalyan-Badlapur',
                'existing two lines between KYN-BUD',
                'carry mix traffic of Mail/Express, Goods and suburban services',
                'in the process of indigenous development of CBTC',
                'Further action will be taken as per the directives received from Railway Board.')
    if not all(anchor in text for anchor in required):
        raise ValueError('Reviewed annual-report page or status wording changed')
    common = dict(source='observed_historical_publication_claim', source_id=sid,
                  source_sha256=record['sha256'], source_pdf_page=page_number,
                  source_printed_page=10, reporting_period='2023-24',
                  current_model_parameter_adopted=False)
    rows = []

    def claim(metric, value, unit, scope, status, qualifier, anchor):
        rows.append(dict(**common, metric=metric, reported_value=value, units=unit,
                         geographic_scope=scope, status_scope=status,
                         qualifier=qualifier, source_anchor=anchor))

    trains, capacity = one(r'about (\d+) trains are run against a capacity of (\d+)', text)
    scope = 'Kalyan-Badlapur existing mixed-traffic section'
    claim('existing_lines', 2, 'lines', scope, 'historical_existing_infrastructure_claim',
          'as_reported_not_verified_current', 'existing two lines between KYN-BUD')
    claim('trains_run', int(trains), 'trains_period_and_direction_basis_unspecified', scope,
          'historical_operating_aggregate', 'about', 'about ' + trains + ' trains are run')
    claim('stated_line_capacity', int(capacity), 'trains_period_and_direction_basis_unspecified', scope,
          'historical_capacity_aggregate_method_unspecified', 'as_reported', 'capacity of ' + capacity)
    coverage = re.findall(r'\b(CR|WR)-(\d+) R-Km/(\d+) T-Km\b', text)
    if len(coverage) != 2 or {row[0] for row in coverage} != {'CR', 'WR'}:
        raise ValueError('CBTC project coverage changed')
    for operator, route, track in coverage:
        for metric, value, unit in (('cbtc_project_route_length', route, 'route_km'),
                                    ('cbtc_project_track_length', track, 'track_km')):
            claim(metric, int(value), unit, operator + ' CBTC project',
                  'project_extent_not_commissioned_supply', 'project_features',
                  operator + '-' + route + ' R-Km/' + track + ' T-Km')
    headway = one(r'Reduction of headway to ([\d.]+) minutes', text)
    claim('cbtc_target_headway', headway, 'minutes', 'CR and WR CBTC project',
          'project_target_not_observed_operating_headway', 'reduction_target',
          'Reduction of headway to ' + headway + ' minutes')
    write('mrvc_rail_control_claims_2023_24.csv', rows)
    audit = dict(source_id=sid, source_sha256=record['sha256'], claim_rows=len(rows),
                 source_pdf_page=page_number, source_printed_page=10,
                 derived_project_target_headway_seconds=str(Decimal(headway) * 60),
                 derived_from='reported project headway minutes multiplied by 60 seconds per minute',
                 model_parameters_adopted=False, limitations=[
                     'The CBTC scope and headway are project features, followed by a statement that development and further directives are pending.',
                     'No current commissioning date, block geometry, interlocking, braking curve or platform clearance is established.',
                     'The mixed-traffic train and capacity counts omit a time period and direction basis. They are not converted to trains per day or per hour.',
                     'Two existing lines are a historical section-level claim, not a per-link track-count assignment.',
                     'The translated copy is not counted as a second observation; the English page was checked against the rendered PDF.',
                 ])
    out = Path(city.path('data/processed/acquisition/rail_control_evidence_audit.json'))
    out.write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')

    page_record, page_path = source('cr_signalling_assets_page', 'rail')
    soup = BeautifulSoup(page_path.read_bytes(), 'html.parser')
    images = [urljoin(page_record['url'], image['src']) for image in soup.find_all('img', src=True)
              if 'signalling-assets' in image['src']]
    if len(images) != 1 or 'Last Reviewed : 14-05-2026' not in soup.get_text(' ', strip=True):
        raise ValueError('Reviewed signalling page image dependency or date changed')
    dependencies = dict(source_id='cr_signalling_assets_page', source_sha256=page_record['sha256'],
        page_review_date='2026-05-14', asset_observation_date=None,
        asset_table_image_urls=images, asset_values_extracted=0,
        interpretation='The acquired HTML embeds an external asset-table image. HTML acquisition does not include that image or establish asset counts.',
        model_parameters_adopted=False)
    Path(city.path('data/processed/acquisition/cr_signalling_page_dependencies.json')).write_text(
        json.dumps(dependencies, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(audit))
    print(json.dumps(dependencies))


if __name__ == '__main__':
    main()
