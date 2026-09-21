"""Extract the two historical observed peak travel-time triangles, not forecasts."""
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write

SID = 'bmc_coastal_traffic_peer_review_2016'
OUTPUT_INPUTS = {
    'data/processed/observed/coastal_2016_travel_times.csv': [
        'data/raw/traffic/bmc_coastal_traffic_peer_review_2016_*.pdf'],
    'data/processed/acquisition/coastal_2016_travel_time_audit.json': [
        'data/raw/traffic/bmc_coastal_traffic_peer_review_2016_*.pdf'],
}
# PDF-page crop boxes in PDF points, not geographical or model coordinates.
TABLES = (
    ('4-10', 'North Bound', 'Evening Peak', 0, 'upper'),
    ('4-11', 'South Bound', 'Morning Peak', 420, 'lower'),
)


def table(path, number, direction, period, left, triangle, record):
    text = subprocess.run([
        'pdftotext', '-layout', '-f', '59', '-l', '59', '-x', str(left),
        '-y', '0', '-W', '420', '-H', '600', str(path), '-'],
        capture_output=True, encoding='utf-8', check=True).stdout
    heading = f'Table {number} {direction} Time Matrix in hour ({period})'
    if heading not in text:
        raise ValueError('Travel-time table identity changed: ' + number)
    body = text.split(heading, 1)[1].split('Peer Review', 1)[0]
    header = re.findall(r'^\s*((?:\d+\s+)+\d+)\s*$', body, re.M)
    if len(header) != 1:
        raise ValueError('Ambiguous destination headers')
    zones = [int(value) for value in header[0].split()]
    if len(zones) != len(set(zones)) or zones != sorted(zones):
        raise ValueError('Destination identifiers not unique and increasing')
    parsed = re.findall(r'^\s*(\d+)\s+((?:\d+\.\d+\s*)+)\s*$', body, re.M)
    if [int(origin) for origin, _ in parsed] != zones:
        raise ValueError('Origin row coverage differs from destination columns')
    rows = []
    for index, (origin_text, values_text) in enumerate(parsed):
        origin = int(origin_text)
        destinations = zones[index:] if triangle == 'upper' else zones[:index + 1]
        values = values_text.split()
        if len(values) != len(destinations):
            raise ValueError('Travel-time triangle column coverage changed')
        for destination, raw in zip(destinations, values):
            hours = Decimal(raw)
            diagonal = origin == destination
            if (diagonal and hours != 0) or (not diagonal and hours <= 0):
                raise ValueError('Unexpected diagonal or nonpositive travel time')
            rows.append(dict(source='observed' if not diagonal else 'structural_table_cell',
                             source_id=SID, source_sha256=record['sha256'], source_pdf_page=59,
                             source_printed_page=42, source_table=number,
                             report_edition='November 2016',
                             survey_date='not_stated_in_speed_delay_section',
                             origin_source_zone_id=origin, destination_source_zone_id=destination,
                             direction=direction, peak_period=period,
                             period_clock_bounds='not_stated_in_table',
                             travel_time_hours=raw, travel_time_seconds=str(hours * 3600),
                             cell_status='structural_diagonal_not_observed_zero_trip' if diagonal else 'reported_observation',
                             mode_definition='survey_vehicle_class_not_stated_in_section',
                             zone_mapping_status='study_zone_ids_not_georeferenced',
                             target_status='historical_evidence_not_current_calibration_target'))
    return rows, zones


def main():
    record, path = source(SID, 'traffic')
    rows, summaries = [], []
    for args in TABLES:
        cells, zones = table(path, *args, record)
        rows.extend(cells)
        summaries.append(dict(table=args[0], zone_ids=zones, supplied_cells=len(cells),
                              blank_cells_not_imputed=len(zones) ** 2 - len(cells)))
    write('coastal_2016_travel_times.csv', rows)
    audit = dict(source_id=SID, source_sha256=record['sha256'], tables=summaries,
                 rows=len(rows), observed_off_diagonal_rows=sum(r['source'] == 'observed' for r in rows),
                 zero_diagonal_rows=sum(r['source'] != 'observed' for r in rows),
                 extraction_review='Source page 59 visually checked; upper and lower triangles remain separate.',
                 limitations=[
                     'Travel times include delays; they do not identify free-flow speeds or road capacities.',
                     'Morning southbound and evening northbound are different periods, not symmetric paired trips.',
                     'Blank reverse-direction cells remain absent; diagonal zeroes are structural, not zero-duration journeys.',
                     'The traffic-count section dates its own survey to January 2016; that does not establish an exact date for these speed-delay measurements.',
                     'Study-zone polygons, exact route, vehicle class, clock windows and sample counts remain unresolved.',
                 ])
    Path(city.path('data/processed/acquisition/coastal_2016_travel_time_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('rows', 'observed_off_diagonal_rows', 'zero_diagonal_rows')}))


if __name__ == '__main__':
    main()
