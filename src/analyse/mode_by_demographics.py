"""The modelled mode x demographics table from a completed run (issue #50).

Joins a finished run's realised trips (`output_trips.csv.gz`) to the run's OWN
persons table (`output_persons.csv.gz`: age, employment, licence, car
availability, household vehicles) and tabulates per-demographic mode shares -
every mode individually, never an umbrella row - with the mean trip length
per cell, which is what #107 reads bike by. This is the MODELLED half of #50;
the observed mode x age counterpart is an acquisition item and no observed
value appears here.

Usage:
    python src/analyse/mode_by_demographics.py results/<run-dir>

Writes `_mode_by_demographics.json` into the run directory and prints the
tables. Sex is the one attribute the run's persons table does not carry; it
is joined from the run's residents map when the run has one and otherwise
from the city's B1 through src/city.py, and the report says which (#213).
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from city import path as city_path

AGE_BANDS = ((0, 4), (5, 11), (12, 17), (18, 24), (25, 34), (35, 44),
             (45, 54), (55, 64), (65, 74), (75, 84), (85, 200))
DIMS = ('age_band', 'sex', 'employment', 'licence', 'car_availability',
        'household_vehicles')


def age_band(age):
    try:
        a = int(float(age))
    except (TypeError, ValueError):
        return 'unknown'
    for lo, hi in AGE_BANDS:
        if lo <= a <= hi:
            return '%d-%d' % (lo, hi) if hi < 200 else '85+'
    return 'unknown'


def load_sex():
    """person_id -> sex, from the city's B1 (the run's persons table carries
    no sex attribute). Returns ({}, 'absent') when B1 is not on disk."""
    p = city_path('demand/population/B1_synthetic_population.csv')
    if not os.path.exists(p):
        return {}, 'absent'
    out = {}
    with open(p, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            out[r['person_id']] = r['sex']
    return out, "the city's B1 (sex is not in the run's persons table)"


def load_run_persons(run_dir):
    """person -> the attributes the run itself carried, from output_persons."""
    out = {}
    with gzip.open(run_dir / 'output' / 'output_persons.csv.gz', 'rt',
                   encoding='utf-8') as fh:
        for r in csv.DictReader(fh, delimiter=';'):
            if r.get('subpopulation') not in (None, '', 'person'):
                continue
            out[r['person']] = dict(
                age_band=age_band(r.get('age')),
                employment=r.get('employment') or 'unknown',
                licence='1' if (r.get('hasLicense') or '').lower() == 'yes'
                else '0',
                car_availability=r.get('carAvail') or 'unknown',
                household_vehicles=(r.get('householdVehicles') or 'unknown'))
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run_dir = Path(sys.argv[1])
    persons = load_run_persons(run_dir)
    sex, sex_source = load_sex()

    tables = {dim: defaultdict(Counter) for dim in DIMS}
    km = {dim: defaultdict(lambda: defaultdict(float)) for dim in DIMS}
    totals = Counter()
    unmatched = 0
    with gzip.open(run_dir / 'output' / 'output_trips.csv.gz', 'rt',
                   encoding='utf-8') as fh:
        rd = csv.DictReader(fh, delimiter=';')
        mode_col = ('main_mode' if 'main_mode' in rd.fieldnames
                    else 'longest_distance_mode')
        for r in rd:
            mode = r[mode_col] or 'unknown'
            attrs = persons.get(r['person'])
            if attrs is None:
                unmatched += 1          # external / through / freight tiers
                continue
            try:
                dist_km = float(r.get('traveled_distance') or 0.0) / 1000.0
            except ValueError:
                dist_km = 0.0
            totals[mode] += 1
            groups = dict(attrs, sex=sex.get(r['person'], 'unknown'))
            for dim in DIMS:
                g = groups[dim]
                tables[dim][g][mode] += 1
                km[dim][g][mode] += dist_km

    def shares(counter):
        n = sum(counter.values())
        return {m: round(c / n, 4) for m, c in sorted(counter.items())} \
            if n else {}

    def mean_km(dim, group, counter):
        return {m: round(km[dim][group][m] / c, 2)
                for m, c in sorted(counter.items()) if c}

    report = {
        'run': run_dir.name,
        'trips_tabulated': sum(totals.values()),
        'trips_outside_b1': unmatched,
        'mode_totals': dict(sorted(totals.items())),
        'persons_source': "the run's own output_persons.csv.gz (#213)",
        'sex_source': sex_source,
        'note': ('modelled table only (issue #50); the observed mode x age '
                 'counterpart is an acquisition item - no observed value '
                 'appears here, and no umbrella pt row: every mode is its '
                 'own column; mean_km is the mean traveled_distance of the '
                 "cell's trips"),
        'by': {dim: {group: {'n': sum(c.values()), 'share': shares(c),
                             'mean_km': mean_km(dim, group, c)}
                     for group, c in sorted(t.items())}
               for dim, t in tables.items()},
    }
    out_path = run_dir / '_mode_by_demographics.json'
    out_path.write_text(json.dumps(report, indent=1), encoding='utf-8')

    modes = sorted(totals)
    for dim, t in tables.items():
        print(f'\n== mode share by {dim} ({run_dir.name})')
        print('  ' + f'{dim:>18} ' + ''.join(f'{m:>10}' for m in modes)
              + f'{"n":>10}')
        for group, c in sorted(t.items()):
            n = sum(c.values())
            print('  ' + f'{group:>18} '
                  + ''.join(f'{c.get(m, 0) / n:>10.3f}' for m in modes)
                  + f'{n:>10}')
        if dim == 'car_availability':
            print(f'  {"mean km":>18} ' + ' '.join(
                f'{group}: ' + ', '.join(f'{m} {v}' for m, v in
                                         mean_km(dim, group, c).items()
                                         if m in ('bike', 'walk', 'ride'))
                for group, c in sorted(t.items())))
    print(f'\nwrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
