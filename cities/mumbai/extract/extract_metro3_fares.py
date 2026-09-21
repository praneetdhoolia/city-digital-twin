"""Transcribe the published fare image; retain image/API disagreements."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

import city
from extract_mmrcl_stations import read

OUTPUT_INPUTS = {
    'data/processed/observed/metro3_chart_fares.csv': [
        'data/raw/transit/metro3_fare_chart_*.png',
        'extract/metro3_fare_chart_layout.json'],
    'data/processed/observed/_metro3_fare_audit.json': [
        'data/raw/transit/metro3_fare_chart_*.png',
        'data/raw/transit/mmrcl_fare_*.json',
        'data/raw/transit/mmrcl_journey_*.json',
        'extract/metro3_fare_chart_layout.json'],
}


def main():
    layout = json.loads(Path(__file__).with_name('metro3_fare_chart_layout.json').read_text(encoding='utf-8'))
    source_id = layout['source_id']
    record = json.loads(Path(city.path('data/raw/transit', 'provenance_' + source_id + '.json')).read_text(encoding='utf-8'))['files'][0]
    path = Path(city.path(record['path']))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record['sha256'] or not digest.startswith(layout['source_sha256']):
        raise ValueError('Source image changed; review its transcription layout')
    source = Image.open(path).convert('RGB')
    if list(source.size) != layout['image_size_px']:
        raise ValueError('Unexpected image dimensions')
    im = np.asarray(source)
    width, height = source.size
    codes = layout['station_codes']
    count = len(codes)
    directory, _ = read('mmrcl_all_stations')
    if set(codes) != {station['code'] for station in directory} or len(set(codes)) != count:
        raise ValueError('Fare matrix station universe differs from operator directory')
    x0, y0 = layout['table_origin_px']
    dx, dy = layout['crop_half_size_px']

    def glyph(row, col):
        x = int(x0 + (col + .5) * (width - x0) / count)
        y = int(y0 + (row + .5) * (height - y0) / count)
        crop = im[y-dy:y+dy, x-dx:x+dx]
        mask = (crop[:, :, 1] < layout['foreground_green_threshold']) if row != col else np.all(crop > layout['diagonal_white_threshold'], axis=2)
        yy, xx = np.where(mask)
        if not len(xx):
            raise ValueError('Empty glyph')
        mask = mask[yy.min():yy.max()+1, xx.min():xx.max()+1]
        return np.asarray(Image.fromarray(mask.astype('uint8') * 255).resize(tuple(layout['normalised_glyph_size_px']))).astype(float) / 255

    templates = np.array([glyph(0, col) for col in layout['template_first_row_columns_zero_based']])
    fares, rows, checks = {}, [], []
    for i, origin in enumerate(codes):
        for j, destination in enumerate(codes):
            errors = np.mean((templates - glyph(i, j)) ** 2, axis=(1, 2))
            ranking = np.argsort(errors)
            fare = layout['template_fares_inr'][int(ranking[0])]
            fares[origin, destination] = fare
            rows.append(dict(from_station_code=origin, to_station_code=destination,
                             chart_fare_inr=fare, template_mse=float(errors[ranking[0]]),
                             template_margin=float(errors[ranking[1]] - errors[ranking[0]]),
                             source='derived', status='transcribed_evidence_not_validated_model_input',
                             source_id=source_id, source_sha256=digest))
    # Check every already-acquired adjacent journey and both end-to-end journeys.
    catalogue = json.loads(Path(__file__).with_name('sources.json').read_text(encoding='utf-8'))['sources']
    for entry in catalogue:
        sid = entry['id']
        if not sid.startswith(('mmrcl_journey_', 'mmrcl_fare_')):
            continue
        if not Path(city.path('data/raw/transit', 'provenance_' + sid + '.json')).exists():
            continue
        response, provenance = read(sid)
        origin, destination = sid.split('_')[2:4]
        origin, destination = origin.upper(), destination.upper()
        if (origin, destination) not in fares:
            raise ValueError('Unknown station in source identity')
        published = response['fare_amount'] if sid.startswith('mmrcl_fare_') else response['fare']
        checks.append(dict(source_id=sid, source_sha256=provenance['sha256'],
                           from_station_code=origin, to_station_code=destination,
                           api_fare_inr=published, chart_fare_inr=fares[origin, destination],
                           matches=float(published) == fares[origin, destination]))
    asymmetries = [dict(from_station_code=a, to_station_code=b, chart_forward_inr=fares[a,b], chart_reverse_inr=fares[b,a])
                  for i,a in enumerate(codes) for b in codes[i+1:] if fares[a,b] != fares[b,a]]
    audit = dict(schema_version=1, status='evidence_with_conflicts', source='derived',
                 cells=len(rows), source_sha256=digest, station_codes=codes,
                 maximum_template_mse=max(r['template_mse'] for r in rows),
                 minimum_template_margin=min(r['template_margin'] for r in rows),
                 source_asymmetries=asymmetries, api_checks=checks,
                 api_disagreements=[c for c in checks if not c['matches']],
                 limitations=[
                     'Template classification is reproducible transcription, not complete independent verification.',
                     'The visually checked asymmetric cell is preserved; calculator evidence is separate.',
                     'Diagonal fares remain as published, without assuming a zero-cost same-station journey.',
                     'Chart publication/effective date and concession products are unresolved.',
                     'No model tariff is selected by this script.'])
    output = Path(city.path('data/processed/observed'))
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'metro3_chart_fares.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    (output / '_metro3_fare_audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('api_checks', 'station_codes', 'limitations')}))


if __name__ == '__main__':
    main()
