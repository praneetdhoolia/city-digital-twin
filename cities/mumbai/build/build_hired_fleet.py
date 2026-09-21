"""Derive a labelled development fleet proxy; not observed operating supply."""
import csv
import json
import math
from pathlib import Path

import city
import registry
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'params/baseline/hired_fleet.json': [
        'registry/A_hired_fleet.json', 'data/processed/observed/rto_2025_vehicle_categories.csv',
        'data/processed/acquisition/baseline_population.json'],
}


def main():
    cfg = registry.load()
    paths = OUTPUT_INPUTS['params/baseline/hired_fleet.json']
    population = json.loads(Path(city.path(paths[-1])).read_text(encoding='utf-8'))
    with Path(city.path(paths[1])).open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    offices = cfg.get('A.hired.office_labels')
    categories = cfg.get('A.hired.categories')
    active_fraction = cfg.get('A.hired.active_fraction')
    denominator = population['source_historical_persons_count']
    if denominator <= 0 or not 0 <= active_fraction <= 1:
        raise ValueError('Invalid population denominator or operating-fraction proxy')
    ratio = population['persons_count'] / denominator
    audit = {}
    counts = {}
    for mode, codes in sorted(categories.items()):
        stock = 0
        selected = []
        for office in offices:
            for code in codes:
                matches = [r for r in rows if r['office_label'] == office and r['category_code'] == code
                           and r['office_level'] == 'office' and r['measure'] == 'registered_stock_20250331']
                if len(matches) != 1:
                    raise ValueError(f'Expected one registration observation: {office}/{code}')
                row = matches[0]
                count = int(row['vehicles_count'])
                if count < 0: raise ValueError('Negative stock')
                stock += count
                selected.append(dict(office=office, category=code, vehicles_count=count,
                                     source_sha256=row['source_sha256']))
        expected = stock * active_fraction * ratio
        counts[mode] = math.floor(expected + 0.5)
        audit[mode] = dict(registered_stock_vehicles_count=stock,
            unrounded_simulated_vehicles_count=expected,
            rounding_error_vehicles_count=counts[mode] - expected, observations=selected)
    result = dict(source='derived_provisional_stock_and_historical_population_proxy',
        vehicles_by_mode=counts, active_fraction_assumed=active_fraction,
        explicit_residents_count=population['persons_count'], historical_persons_count=denominator,
        cohort_to_historical_population_ratio=ratio, modes=audit,
        input_sha256={p: fingerprint(Path(city.path(p))) for p in paths},
        limitations=['Registration stock is not observed simultaneous operating supply.',
            'RTO offices and historical census geography are not reconciled catchments; dates differ.',
            'Tourist/luxury cabs are grouped with metered taxis as a provisional local-supply proxy.',
            'Integer rounding may remove rare fleets; zero is preserved, never forced to one.',
            'Cohort scaling is independent of road capacity but is not validated physical scaling.',
            'Pool has no spatial dispatch, service shifts or empty road movements.'])
    output = Path(city.path('params/baseline/hired_fleet.json'))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(vehicles_by_mode=counts, cohort_ratio=ratio)))


if __name__ == '__main__':
    main()
