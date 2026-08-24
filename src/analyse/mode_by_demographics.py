"""The modelled mode x demographics table from a completed run (issue #50).

Joins a finished run's realised trips (`output_trips.csv.gz`) to the B1
synthetic population (age band, sex, employment, licence) and tabulates
per-demographic mode shares - every mode individually, never an umbrella
row. This is the MODELLED half of #50; the observed mode x age counterpart
is an acquisition item and no observed value appears here.

Usage:
    python src/analyse/mode_by_demographics.py results/<run-dir>

Writes `_mode_by_demographics.json` into the run directory and prints the
tables. Reads the city's B1 through src/city.py like every other consumer.
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from city import path as city_path  # noqa: E402


def load_population():
    """person_id -> (age_band, sex, employment_status, licence)."""
    out = {}
    with open(city_path('demand/population/B1_synthetic_population.csv'),
              newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            out[r['person_id']] = (r['age_band'], r['sex'],
                                   r['employment_status'],
                                   r['licence_holder'])
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run_dir = Path(sys.argv[1])
    pop = load_population()

    # trips: one row per realised trip; main_mode from the run's own record
    tables = {dim: defaultdict(Counter)
              for dim in ('age_band', 'sex', 'employment', 'licence')}
    totals = Counter()
    unmatched = 0
    with gzip.open(run_dir / 'output' / 'output_trips.csv.gz', 'rt',
                   encoding='utf-8') as fh:
        rd = csv.DictReader(fh, delimiter=';')
        mode_col = ('main_mode' if 'main_mode' in rd.fieldnames
                    else 'longest_distance_mode')
        for r in rd:
            mode = r[mode_col] or 'unknown'
            person = r['person']
            attrs = pop.get(person)
            if attrs is None:
                unmatched += 1          # external / through / freight tiers
                continue
            age_band, sex, employment, licence = attrs
            totals[mode] += 1
            tables['age_band'][age_band][mode] += 1
            tables['sex'][sex][mode] += 1
            tables['employment'][employment][mode] += 1
            tables['licence'][licence][mode] += 1

    def shares(counter):
        n = sum(counter.values())
        return {m: round(c / n, 4) for m, c in sorted(counter.items())} \
            if n else {}

    report = {
        'run': run_dir.name,
        'trips_tabulated': sum(totals.values()),
        'trips_outside_b1': unmatched,
        'mode_totals': dict(sorted(totals.items())),
        'note': ('modelled table only (issue #50); the observed mode x age '
                 'counterpart is an acquisition item - no observed value '
                 'appears here, and no umbrella pt row: every mode is its '
                 'own column'),
        'by': {dim: {group: {'n': sum(c.values()), 'share': shares(c)}
                     for group, c in sorted(t.items())}
               for dim, t in tables.items()},
    }
    out_path = run_dir / '_mode_by_demographics.json'
    out_path.write_text(json.dumps(report, indent=1), encoding='utf-8')

    for dim, t in tables.items():
        print(f'\n== mode share by {dim} ({run_dir.name})')
        modes = sorted(totals)
        print('  ' + f'{dim:>12} ' + ''.join(f'{m:>10}' for m in modes)
              + f'{"n":>10}')
        for group, c in sorted(t.items()):
            n = sum(c.values())
            print('  ' + f'{group:>12} '
                  + ''.join(f'{c.get(m, 0) / n:>10.3f}' for m in modes)
                  + f'{n:>10}')
    print(f'\nwrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
