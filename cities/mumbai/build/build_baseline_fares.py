"""Price broad-baseline transit boardings with declared coverage and proxies."""
from collections import Counter
import csv
import io
import json
from pathlib import Path
import re
import zipfile

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'params/baseline/boarding_fares.csv': [
        'schedules/baseline_regional.zip', 'registry/A_baseline_fares.json',
        'data/processed/observed/best_published_fares.csv'],
    'data/processed/acquisition/baseline_fares.json': [
        'schedules/baseline_regional.zip', 'registry/A_baseline_fares.json',
        'data/processed/observed/best_published_fares.csv'],
}


def main():
    cfg = registry.load()
    with Path(city.path('data/processed/observed/best_published_fares.csv')).open(
            encoding='utf-8', newline='') as stream:
        published = list(csv.DictReader(stream))
    with zipfile.ZipFile(city.path('schedules/baseline_regional.zip')) as archive:
        routes = list(csv.DictReader(io.StringIO(archive.read('routes.txt').decode('utf-8-sig'))))
    agency = cfg.get('A.baseline_fares.published_agency_id')
    ac = re.compile(cfg.get('A.baseline_fares.ac_route_pattern'))
    suffix = cfg.get('A.baseline_fares.rider_class')
    result, counts = [], Counter()
    for route in routes:
        if route['agency_id'] != agency:
            continue
        profile = ('ac_' if ac.search(route['route_short_name']) else 'non_ac_') + suffix
        fares = sorted((r for r in published if r['fare_class'] == profile),
                       key=lambda r: float(r['stage_distance_as_printed_km']))
        if len(fares) < 2:
            raise ValueError('A published profile needs at least two distance stages')
        bounds = [float(r['stage_distance_as_printed_km']) * 1000 for r in fares]
        values = [float(r['base_fare_inr']) for r in fares]
        if any(b <= a for a, b in zip(bounds, bounds[1:])):
            raise ValueError('Published fare bounds are not unique/increasing')
        tail_rate = (values[-1] - values[-2]) / (bounds[-1] - bounds[-2])
        result.append(dict(match_kind='line', match_id=route['route_id'],
            profile_id=agency + '_' + profile, upper_bounds_m='|'.join(map(str, bounds)),
            fares_money='|'.join(map(str, values)), linear_rate_money_per_m=tail_rate,
            currency_code=city.descriptor()['currency'],
            source='published_bands_with_provisional_route_class_and_modelled_tail',
            source_id=fares[0]['source_id']))
        counts[profile] += 1
    for mode, rate in sorted(cfg.get('A.baseline_fares.fallback_rate_money_per_m').items()):
        result.append(dict(match_kind='mode', match_id=mode, profile_id='provisional_' + mode,
            upper_bounds_m='', fares_money='', linear_rate_money_per_m=rate,
            currency_code=city.descriptor()['currency'], source='assumed_prior_baseline_rate',
            source_id='registry/A_baseline_fares.json'))
    output = Path(city.path('params/baseline/boarding_fares.csv'))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(result)
    audit = dict(source='derived_baseline_boarding_fares', currency_code=city.descriptor()['currency'],
        input_sha256={p: fingerprint(Path(city.path(p))) for p in OUTPUT_INPUTS['params/baseline/boarding_fares.csv']},
        output_sha256=fingerprint(output), published_line_profiles=dict(counts),
        fallback_modes=sorted(cfg.get('A.baseline_fares.fallback_rate_money_per_m')),
        distance_basis='network_links_entered_between_boarding_and_alighting',
        limitations=[
            'Published bands do not verify current route vehicle class, operation or operator fare-stage distances.',
            'AC class is inferred from a declared route-label convention; other labels take the provisional non-AC class.',
            'All travellers use the declared baseline rider class; concession eligibility and passes are not yet modelled.',
            'Beyond the last published distance, the final marginal rate is extrapolated and counted separately.',
            'Uncovered operators and rail/metro/ferry retain explicit provisional per-metre prices.',
            'Completed boarding fares enter income-sensitive scoring; the transit path router does not yet optimise exact ticket prices.',
            'Transfers are separately charged; unfinished boardings have no invented alighting fare.'])
    Path(city.path('data/processed/acquisition/baseline_fares.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('currency_code', 'published_line_profiles', 'fallback_modes')}))


if __name__ == '__main__':
    main()
