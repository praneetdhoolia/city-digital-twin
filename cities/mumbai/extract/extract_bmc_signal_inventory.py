"""Extract the tender's reference junctions without inventing signal plans."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

SID = 'bmc_signal_upgrade_spec_2021'
OUTPUT_INPUTS = {
    'data/processed/observed/bmc_2021_signal_junctions.csv': ['data/raw/traffic/bmc_signal_upgrade_spec_2021_*.pdf'],
    'data/processed/acquisition/bmc_2021_signal_inventory_audit.json': ['data/raw/traffic/bmc_signal_upgrade_spec_2021_*.pdf'],
}
# Source table pages/columns in PDF points; these are not model coordinates.
PAGES = ((63, 1, 24), (64, 25, 49), (65, 50, 70))
COLUMNS = {'name': (239, 378), 'type': (378, 430), 'coordinates': (433, 531)}


def dms(raw, hemisphere):
    match = re.fullmatch(r'(\d+)\s*\u00b0\s*(\d+)\s*\x27\s*(\d+(?:\.\d+)?)"' + hemisphere + r',?', raw)
    if not match:
        raise ValueError('Unrecognised source DMS coordinate: ' + raw)
    degrees, minutes, seconds = map(Decimal, match.groups())
    if minutes >= 60 or seconds >= 60 or degrees > (90 if hemisphere == 'N' else 180):
        raise ValueError('Out-of-range source DMS coordinate')
    return str(degrees + minutes / 60 + seconds / 3600)


def main():
    record, path = source(SID, 'traffic')
    if '5.11 List of Signal Junctions:' not in page_text(path, 63):
        raise ValueError('Signal inventory heading changed')
    rows = []
    for page, first, last in PAGES:
        xml = subprocess.run(['pdftotext', '-bbox-layout', '-f', str(page), '-l', str(page),
                              str(path), '-'], capture_output=True, encoding='utf-8', check=True).stdout
        root = ET.fromstring(xml)
        words = [(float(e.attrib['xMin']), float(e.attrib['yMin']), e.text)
                 for e in root.iter() if e.tag.endswith('}word')]
        serials = [(int(t), y) for x, y, t in words if 110 <= x <= 130 and t.isdigit()]
        serials.sort()
        if [n for n, _ in serials] != list(range(first, last + 1)):
            raise ValueError('Signal inventory serial coverage changed')
        cells = {n: {c: [] for c in COLUMNS} for n, _ in serials}
        for x, y, token in words:
            n, centre = min(serials, key=lambda row: abs(row[1] - y))
            if abs(centre - y) > 13:
                continue
            for column, (left, right) in COLUMNS.items():
                if left <= x < right:
                    cells[n][column].append((y, x, token))
        for n, _ in serials:
            cell = {key: ' '.join(token for _, _, token in sorted(value)) for key, value in cells[n].items()}
            coord = cell['coordinates']
            pair = re.fullmatch(r'(.+?N,?)\s+(.+E)', coord)
            if not pair:
                raise ValueError('Coordinate pair missing for row ' + str(n))
            latitude, longitude = pair.groups()
            if cell['type'] not in ('3-arm', '4-arm', '5-arm', 'Ped', '3-arm +ped', '4-arm +ped') or not cell['name']:
                raise ValueError('Signal type/name unrecognised at row ' + str(n))
            rows.append(dict(source='published_tender_inventory', source_id=SID,
                             source_sha256=record['sha256'], source_pdf_page=page, source_serial=n,
                             junction_name_as_printed=cell['name'], junction_type_as_printed=cell['type'],
                             latitude_dms_as_printed=latitude, longitude_dms_as_printed=longitude,
                             latitude_degrees=dms(latitude, 'N'), longitude_degrees=dms(longitude, 'E'),
                             coordinate_datum='not_stated_in_table',
                             coordinate_derivation='degrees + minutes/60 + seconds/3600; datum unchanged',
                             evidence_scope='70_junction_upgrade_tender_not_citywide_signal_census',
                             operating_plan_status='cycles_splits_offsets_and_phases_not_supplied_by_inventory',
                             model_binding_status='unmatched_reference_point_not_assigned_to_OSM'))
    write('bmc_2021_signal_junctions.csv', rows)
    audit = dict(source_id=SID, source_sha256=record['sha256'], rows=len(rows),
                 type_counts=dict(sorted(Counter(r['junction_type_as_printed'] for r in rows).items())),
                 unique_coordinate_pairs=len({(r['latitude_degrees'], r['longitude_degrees']) for r in rows}),
                 limitations=[
                     'The list identifies tender reference junctions; completion of an upgrade and current operational status are not established.',
                     'Pedestrian-only and combined vehicle/pedestrian source types are preserved, not converted to vehicle arms.',
                     'The source calls these reference coordinates and does not identify a geodetic datum or positional accuracy.',
                     'Decimal degree conversion changes notation only; it does not establish WGS84, improve precision or locate individual stop lines.',
                     'No OSM snapping, approach directions, crossing paths, controller assignment or phasing is inferred.',
                     'Merged arterial road labels remain in the source and have not been reconstructed as a road-to-signal crosswalk.',
                 ])
    Path(city.path('data/processed/acquisition/bmc_2021_signal_inventory_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('rows', 'type_counts', 'unique_coordinate_pairs')}))


if __name__ == '__main__':
    main()
