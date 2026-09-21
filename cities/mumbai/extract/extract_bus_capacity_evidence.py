"""Extract manufacturer seating claims without creating an operational fleet."""
import json
from pathlib import Path
import re
import subprocess

import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/bus_manufacturer_seating_claims.csv': [
        'data/raw/transit/tata_best_bus_delivery_20210807_*.pdf',
        'data/raw/transit/switch_eiv22_brochure_*.pdf',
        'data/raw/transit/olectra_product_presentation_20210906_*.pdf'],
    'data/processed/acquisition/bus_capacity_evidence_audit.json': [
        'data/raw/transit/tata_best_bus_delivery_20210807_*.pdf',
        'data/raw/transit/switch_eiv22_brochure_*.pdf',
        'data/raw/transit/olectra_product_presentation_20210906_*.pdf'],
}


def page(source_id, number):
    record, path = source(source_id, 'transit')
    text = subprocess.run(['pdftotext', '-layout', '-f', str(number), '-l', str(number),
                           str(path), '-'], check=True, capture_output=True,
                          encoding='utf-8').stdout
    return record, text


def one(pattern, text):
    matches = re.findall(pattern, text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError('Manufacturer statement missing or ambiguous: ' + pattern)
    return matches[0]


def claim(source_id, record, page_number, model, length, seats, raw, context):
    return dict(source_id=source_id, source_sha256=record['sha256'], source_page_1_based=page_number,
                source='manufacturer_publication', model_as_printed=model,
                length_m=length, seated_passengers_count=int(seats), capacity_text_as_printed=raw,
                standing_passengers_count='', standing_status='unobtained_not_zero',
                claim_context=context, current_fleet_count='', route_assignment='',
                model_ready=False, status='licensed_configuration_and_operating_allocation_unresolved')


def main():
    rows = []
    sid = 'tata_best_bus_delivery_20210807'
    record, text = page(sid, 1)
    # This sentence is the order's model mix; it is not the delivered or active fleet.
    text = ' '.join(text.split())
    total, count_a, length_a, seats_a, count_b, length_b, seats_b = one(
        r'total order of (\d+) e-buses include (\d+) units of (\d+)-metre (\d+)-seater model '
        r'and (\d+) units of (\d+)-metre (\d+)-seater model', text)
    if int(count_a) + int(count_b) != int(total):
        raise ValueError('Tata order mix does not sum to its total')
    for length, seats in ((length_a, seats_a), (length_b, seats_b)):
        rows.append(claim(sid, record, 1, 'Tata electric AC bus', length, seats,
                          seats + '-seater', 'BEST order configuration described 7 August 2021'))

    sid = 'switch_eiv22_brochure'
    record, text = page(sid, 1)
    raw, seats = one(r'Seating Capacity\s+((\d+)\s*\+\s*D)', text)
    length_mm = one(r'Length \(mm\)\s+(\d+)', text)
    length_m = int(length_mm) / 1000
    rows.append(claim(sid, record, 1, 'SWITCH EiV22', length_m, seats, raw,
                      'Technical table; certification in progress and customer choices noted'))
    record, text = page(sid, 2)
    seats = one(r'optimized seating for (\d+) passengers', ' '.join(text.split()))
    rows.append(claim(sid, record, 2, 'SWITCH EiV22', '', seats, seats + ' passengers',
                      'Descriptive maximum seating claim; conflicts with technical table'))

    sid = 'olectra_product_presentation_20210906'
    record, text = page(sid, 5)
    models = re.findall(r'E-Buzz-\s+(\w+)\s+\((\d+)m\)', text)
    line = one(r'^Seating Capacity\s+(.+)$', text)
    # The layout extraction retains the table's left-to-right model order.
    cells = re.findall(r'(\d+)\+Driver', line)
    if len(models) != len(cells) or not models or len(set(models)) != len(models):
        raise ValueError('Olectra model/capacity columns do not align')
    for (model, length), seats in zip(models, cells, strict=True):
        rows.append(claim(sid, record, 5, 'Olectra ' + model, length, seats, seats + '+Driver',
                          'Historical product range; BEST configuration not established'))
    result = dict(status='manufacturer_claims_not_operating_capacity', rows=len(rows),
                  conflicts=[dict(model='SWITCH EiV22',
                                  claims=[{k: r[k] for k in ('source_page_1_based', 'capacity_text_as_printed',
                                                            'seated_passengers_count', 'claim_context')}
                                          for r in rows if r['source_id'] == 'switch_eiv22_brochure'])],
                  limitations=[
                      'All standing capacities remain missing; blank must not become zero or a default.',
                      'Driver places are separate from passenger seats where the table explicitly says +D or +Driver.',
                      'Orders, deliveries, registered stock, available fleet and actual route assignments are different quantities.',
                      'No manufacturer model is assigned to a scheduled departure here.',
                      'The Switch technical table and descriptive claim are retained without choosing one.',
                      'Brochure range and charging times depend on duty and configuration; they are not operational charging-dwell observations.',
                      'A smaller simulation must preserve separate configurations before applying its capacity scaling rule.'])
    write('bus_manufacturer_seating_claims.csv', rows)
    Path(city.path('data/processed/acquisition/bus_capacity_evidence_audit.json')).write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'rows': len(rows), 'unresolved_capacity_conflicts': len(result['conflicts'])}))


if __name__ == '__main__':
    main()
