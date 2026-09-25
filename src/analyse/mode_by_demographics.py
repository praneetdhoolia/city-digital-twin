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

import registry as _registry
from city import path as city_path

# the model's own banding, declared once (B.population.age_bands) and
# labelled as the population builder labels it (build_population.BAND_LABEL)
AGE_BANDS = [tuple(b) for b in _registry.load().get('B.population.age_bands')]
DIMS = ('age_band', 'sex', 'employment', 'licence', 'car_availability',
        'household_vehicles')


def age_band(age):
    try:
        a = int(float(age))
    except (TypeError, ValueError):
        return 'unknown'
    last = AGE_BANDS[-1][0]
    for lo, hi in AGE_BANDS:
        if lo <= a <= hi:
            return '%d+' % lo if lo == last else '%d-%d' % (lo, hi)
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
    """person -> the attributes the run itself carried: output_persons, or a
    stopped arm's own input plans (iteration_reading.person_attributes)."""
    import iteration_reading
    out = {}
    for pid, r in iteration_reading.person_attributes(
            str(run_dir), ('subpopulation', 'age', 'employment', 'hasLicense',
                           'carAvail', 'householdVehicles')).items():
        if r.get('subpopulation') not in (None, '', 'person'):
            continue
        out[pid] = dict(
            age_band=age_band(r.get('age')),
            employment=r.get('employment') or 'unknown',
            licence='1' if (r.get('hasLicense') or '').lower() == 'yes'
            else '0',
            car_availability=r.get('carAvail') or 'unknown',
            household_vehicles=(r.get('householdVehicles') or 'unknown'))
    return out


def person_attributes(run_dir):
    """person -> (age_band, sex, employment, licence) for a run: age,
    employment and licence from the run's OWN persons table (#213), sex from
    the city's B1 (the one attribute the persons table lacks). The one
    reader for every mode x demographics measurement; measure_demographic_modes
    carried its own copy reading everything from B1 (twelfth report)."""
    persons = load_run_persons(Path(run_dir))
    sex, _ = load_sex()
    return {pid: (a['age_band'], sex.get(pid, 'unknown'), a['employment'], a['licence'])
            for pid, a in persons.items()}


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
    # the final trips table, or - for a stopped arm - the iteration its
    # close-out read (`_metrics.json` read_at_iteration)
    import iteration_reading
    read_at = None
    metrics = run_dir / '_metrics.json'
    if metrics.exists():
        read_at = json.loads(metrics.read_text(encoding='utf-8')).get('read_at_iteration')
    rows = iteration_reading.table(str(run_dir), 'trips', read_at)
    mode_col = ('main_mode' if rows and 'main_mode' in rows[0]
                else 'longest_distance_mode')
    for r in rows:
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
        'persons_source': "the run's own persons (output_persons, or its input plans for a stopped arm; #213)",
        'trips_read_at': 'final output' if read_at is None else 'iteration %d' % read_at,
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
