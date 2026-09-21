"""Keep published corridor observations and their internal disagreements visible."""
import base64
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/jvlr_poster_road_controls.csv': [
        'data/raw/traffic/jvlr_conference_poster_2026_response_*.json',
        'extract/jvlr_poster_transcription.json'],
    'data/processed/acquisition/jvlr_poster_audit.json': [
        'data/raw/traffic/jvlr_conference_poster_2026_response_*.json',
        'extract/jvlr_poster_transcription.json'],
}


def main():
    transcription = Path(city.path('extract/jvlr_poster_transcription.json'))
    spec = json.loads(transcription.read_text(encoding='utf-8'))
    record, path = source(spec['source_id'], 'traffic')
    response = json.loads(path.read_text(encoding='utf-8'))
    pdf = base64.b64decode(response['fileContent'], validate=True)
    if not pdf.startswith(b'%PDF-') or hashlib.sha256(pdf).hexdigest() != spec['poster_sha256']:
        raise ValueError('Transcription does not match the acquired poster')
    rows, checks = [], []
    for cells in spec['rows']:
        if len(cells) != len(spec['columns']):
            raise ValueError('Incomplete source row')
        row = dict(zip(spec['columns'], cells))
        lanes, speed, flow = (Decimal(row[k]) for k in ('lanes', 'speed_kmh', 'flow_pcu_h'))
        if lanes <= 0 or lanes != lanes.to_integral_value() or speed <= 0 or flow < 0:
            raise ValueError('Invalid printed physical quantity')
        expectations = {
            'flow_pcu_h_lane': flow / lanes,
            'density_pcu_km': flow / speed,
            'density_pcu_km_lane': flow / speed / lanes,
        }
        for key, expected in expectations.items():
            printed = Decimal(row[key])
            quantum = Decimal(1).scaleb(printed.as_tuple().exponent)
            delta = printed - expected
            # Per-lane density can be calculated after rounding the printed
            # total density. Carry that source precision through the division.
            intermediate = Decimal(0)
            if key == 'density_pcu_km_lane':
                density = Decimal(row['density_pcu_km'])
                intermediate = Decimal(1).scaleb(density.as_tuple().exponent) / 2 / lanes
            checks.append(dict(row_id=row['row_id'], field=key,
                               printed=str(printed), calculated=str(expected),
                               delta=str(delta), printed_half_quantum=str(quantum / 2),
                               intermediate_rounding_bound=str(intermediate),
                               status='exact' if delta == 0 else 'rounding_compatible'
                               if abs(delta) <= quantum / 2 else 'intermediate_rounding_compatible'
                               if abs(delta) <= quantum / 2 + intermediate else 'source_disagreement'))
        row.update(source='literature', source_id=spec['source_id'], source_sha256=record['sha256'],
                   poster_sha256=spec['poster_sha256'], source_pdf_page=spec['source_pdf_page'],
                   survey_date=spec['survey_date'], survey_time_window=spec['survey_time_window'],
                   speed_measurement_method=spec['speed_measurement_method'],
                   pcu_conversion_factors=spec['pcu_conversion_factors'],
                   validation_status='published_derived_quantities_with_unresolved_methods_and_locations',
                   calibration_eligible=False)
        rows.append(row)
    if len({row['row_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate source row identifiers')
    for disagreement in spec['figure_differences']:
        row = next(row for row in rows if row['row_id'] == disagreement['row_id'])
        if row[disagreement['field']] != disagreement['table']:
            raise ValueError('Disagreement no longer matches the source table')
    bad_density = sum(row['los_density'] in ('D', 'E', 'F') for row in rows)
    bad_flow = sum(row['los_flow'] in ('D', 'E', 'F') for row in rows)
    out = Path(city.path('data/processed/observed'))
    write(out / 'jvlr_poster_road_controls.csv', rows)
    report = dict(source='derived', source_id=spec['source_id'], source_sha256=record['sha256'],
                  poster_sha256=spec['poster_sha256'], transcription_sha256=hashlib.sha256(transcription.read_bytes()).hexdigest(),
                  rows=len(rows), checks=checks, check_status_counts=dict(Counter(c['status'] for c in checks)),
                  figure_differences=spec['figure_differences'],
                  below_los_c=dict(density_table=bad_density, flow_table=bad_flow,
                                   poster_narrative=spec['poster_narrative_below_los_c_count'],
                                   status='unresolved_source_disagreement' if bad_density != spec['poster_narrative_below_los_c_count'] else 'agrees'),
                  limitations=spec['limitations'], calibration_eligible=False)
    Path(city.path('data/processed/acquisition/jvlr_poster_audit.json')).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('rows', 'check_status_counts', 'below_los_c')}))


if __name__ == '__main__':
    main()
