#!/usr/bin/env python
"""Measure a run's mode x demographic distributions against held observed cells (issue #50).

DIAGNOSTIC MEASUREMENT OF AN EXISTING RUN - NOT A RESULT ABOUT THE LIGHT
RAIL. It tabulates one completed run's realised trips against the observed
mode x demographic cells the project actually holds, so the divergences are
on record before the next repair family runs. Nothing here evaluates a
scenario against another scenario.

Two halves, in one report:

1. INVENTORY - which mode x demographic cells are OBSERVED in held data.
   Today that is exactly one family of cells: journey-to-work mode x sex at
   SA1 (census G62, one-method journeys, core tier). The held HTS slices
   (`hts_mode.csv`, `hts_purpose.csv`) carry NO demographic column, so
   mode x age / mode x employment are not observable from held data - an
   acquisition item, not a modelling gap (issue #50, issue #63,
   `docs/archived/design/mode-individualisation.md` section 3). The holdout split
   under `data/processed/validation/` is never opened here.

2. MEASUREMENT - the run's realised trips (`output_trips.csv.gz`, the same
   source `mode_by_demographics.py` and the metrics extraction read) joined
   to the B1 synthetic population's per-person attributes, giving mode
   shares per age band / sex / employment status / licence. Where an
   observed cell exists (G62: mode x sex, commute only) the modelled cell
   is restricted to the comparable slice - trips ending at a work activity
   - and the two are printed side by side, labelled with geography and
   caveats (2021 was a COVID census; observed shares are structure, not
   level targets). Every mode appears individually - never a `pt` or
   `Other` umbrella on the observed side; the model's single `pt` qsim mode
   is compared against the union of the four observed PT modes, with the
   four listed.

Usage:
    python src/analyse/measure_demographic_modes.py results/<run-dir>

Writes `_demographic_modes.json` into the run directory (read-only over
everything else) and prints the tables. City inputs are resolved through
src/city.py; the run's comparability family is read from the declared
`docs/run_families.json` via build_run_index, never re-derived.
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from city import path as city_path  # noqa: E402
from build_run_index import load_families, family_of  # noqa: E402
import registry as _registry  # noqa: E402

# --- observed side -----------------------------------------------------------
# G62 one-method journey-to-work column stems (ABS 2021 DataPack naming) and
# the model mode each observed category corresponds to. `None` = no modelled
# counterpart in this run family: taxi/rideshare is not modelled
# (DECISIONS.md 9.42), the model's truck tier is freight demand with no B1
# person attached, and `Other` is undefined. These rows still appear -
# observed, with the gap stated - rather than being silently dropped.
G62_MODES = [
    ('One_method_Train', 'Train', 'pt'),
    ('One_method_Bus', 'Bus', 'pt'),
    ('One_method_Ferry', 'Ferry', 'pt'),
    ('One_met_Tram_or_lt_rail', 'Tram/light rail', 'pt'),
    ('One_met_Taxi_or_Rideshare', 'Taxi/Rideshare', None),
    ('One_method_Car_as_driver', 'Car as driver', 'car'),
    ('One_method_Car_as_passenger', 'Car as passenger', 'ride'),
    ('One_method_Truck', 'Truck', None),
    ('One_method_Motorbike_scootr', 'Motorbike/scooter', 'motorbike'),
    ('One_method_Bicycle', 'Bicycle', 'bike'),
    ('One_method_Other', 'Other', None),
    ('One_method_Walked_only', 'Walked only', 'walk'),
]
# Context columns: journeys the one-method share denominator excludes.
G62_CONTEXT = ['One_method_Tot_one_method', 'Two_methods_Tot_two_methods',
               'Three_meth_Tot_three_meth', 'Worked_home',
               'Did_not_go_to_work', 'Tot']
# Reporting flag only (not a model value): an observed cell under this many
# journeys is marked too thin to constrain anything - ABS randomly perturbs
# small SA1 cells, so tiny aggregates carry perturbation noise on top of
# sampling noise. Declared, like every other controllable value (9.77).
THIN_CELL_MIN = _registry.load().get('B.census.thin_cell_min_journeys')
# The modelled slice comparable to a journey-to-work observation: trips
# arriving at a work activity (B2 activity vocabulary).
COMMUTE_END_ACTIVITY = 'work'


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


def load_g62():
    """Observed one-method JTW journeys by (mode, sex) over the core tier."""
    cells = Counter()
    context = Counter()
    n_sa1 = 0
    with open(city_path('data/processed/census/census2021_G62_SA1.csv'),
              newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['zone_tier'] != 'core':
                continue
            n_sa1 += 1
            for stem, label, _ in G62_MODES:
                for s in ('M', 'F'):
                    cells[(label, s)] += int(r[f'{stem}_{s}'])
            for stem in G62_CONTEXT:
                for s in ('M', 'F', 'P'):
                    context[(stem, s)] += int(r[f'{stem}_{s}'])
    return cells, context, n_sa1


def hts_inventory():
    """Held HTS tables: confirm (mechanically) they carry no demographic
    column - the reason no HTS mode x demographic cell appears below."""
    inv = {}
    for name in ('hts_mode.csv', 'hts_purpose.csv'):
        with open(city_path(f'data/processed/hts/{name}'), newline='',
                  encoding='utf-8') as fh:
            cols = next(csv.reader(fh))
        demographic = [c for c in cols if any(
            k in c.lower() for k in ('age', 'sex', 'gender', 'employ',
                                     'income', 'occupation', 'licence'))]
        inv[name] = {'columns': cols, 'demographic_columns': demographic}
    return inv


def tabulate_trips(run_dir, pop):
    """All-trip and commute-only mode counters per demographic dimension."""
    dims = ('age_band', 'sex', 'employment', 'licence')
    all_t = {d: defaultdict(Counter) for d in dims}
    com_t = {d: defaultdict(Counter) for d in dims}
    totals, com_totals = Counter(), Counter()
    unmatched = 0
    with gzip.open(run_dir / 'output' / 'output_trips.csv.gz', 'rt',
                   encoding='utf-8') as fh:
        rd = csv.DictReader(fh, delimiter=';')
        mode_col = ('main_mode' if 'main_mode' in rd.fieldnames
                    else 'longest_distance_mode')
        for r in rd:
            attrs = pop.get(r['person'])
            if attrs is None:
                unmatched += 1          # freight / external tiers - no B1 row
                continue
            mode = r[mode_col] or 'unknown'
            commute = r['end_activity_type'] == COMMUTE_END_ACTIVITY
            totals[mode] += 1
            if commute:
                com_totals[mode] += 1
            for d, v in zip(dims, attrs):
                all_t[d][v][mode] += 1
                if commute:
                    com_t[d][v][mode] += 1
    return all_t, com_t, totals, com_totals, unmatched


def shares(counter):
    n = sum(counter.values())
    return {m: round(c / n, 4) for m, c in sorted(counter.items())} if n else {}


def table_json(tables):
    return {dim: {group: {'n': sum(c.values()), 'share': shares(c)}
                  for group, c in sorted(t.items())}
            for dim, t in tables.items()}


def print_table(title, t, modes):
    print(f'\n== {title}')
    print('  ' + ' ' * 14 + ''.join(f'{m:>10}' for m in modes) + f'{"n":>10}')
    for group, c in sorted(t.items()):
        n = sum(c.values())
        print('  ' + f'{group:>14}'
              + ''.join(f'{c.get(m, 0) / n:>10.3f}' for m in modes)
              + f'{n:>10}')


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run_dir = Path(sys.argv[1])

    fams, overrides = load_families()
    family, fam_note = family_of(run_dir.name, fams, overrides)
    fam_label = next((f['label'] for k, f in fams if k == family), '')

    pop = load_population()
    g62, g62_ctx, n_sa1 = load_g62()
    hts = hts_inventory()
    all_t, com_t, totals, com_totals, unmatched = tabulate_trips(run_dir, pop)

    # --- observed mode x sex shares (within each sex, one-method journeys) --
    obs_tot = {s: sum(g62[(label, s)] for _, label, _ in G62_MODES)
               for s in ('M', 'F')}
    observed_rows = []
    for _, label, model_mode in G62_MODES:
        row = {'observed_mode': label, 'model_mode': model_mode}
        for s in ('M', 'F'):
            n = g62[(label, s)]
            row[f'n_{s}'] = n
            row[f'share_{s}'] = round(n / obs_tot[s], 5)
            row[f'thin_{s}'] = n < THIN_CELL_MIN
        observed_rows.append(row)
    pt_union = {s: sum(g62[(label, s)] for _, label, m in G62_MODES
                       if m == 'pt') for s in ('M', 'F')}

    # --- modelled commute mode x sex, restricted to comparable modes -------
    # Model modes with an observed one-method JTW counterpart. The observed
    # rows without a counterpart (Taxi/Rideshare, Truck, Other) stay in the
    # observed table; here the modelled denominator is all commute trips.
    comparison = []
    model_sex = com_t['sex']
    model_sex_n = {s: sum(model_sex.get(s, Counter()).values())
                   for s in ('M', 'F')}
    grouped = defaultdict(list)
    for _, label, m in G62_MODES:
        if m is not None:
            grouped[m].append(label)
    for model_mode in sorted(grouped):
        obs_n = {s: sum(g62[(lab, s)] for lab in grouped[model_mode])
                 for s in ('M', 'F')}
        row = {'model_mode': model_mode,
               'observed_modes': grouped[model_mode]}
        for s in ('M', 'F'):
            o = obs_n[s] / obs_tot[s] if obs_tot[s] else 0.0
            mn = model_sex.get(s, Counter()).get(model_mode, 0)
            mo = mn / model_sex_n[s] if model_sex_n[s] else 0.0
            row[f'observed_share_{s}'] = round(o, 5)
            row[f'modelled_share_{s}'] = round(mo, 5)
            row[f'delta_pp_{s}'] = round((mo - o) * 100, 2)
            row[f'observed_n_{s}'] = obs_n[s]
            row[f'modelled_n_{s}'] = mn
            row[f'observed_thin_{s}'] = obs_n[s] < THIN_CELL_MIN
        comparison.append(row)

    report = {
        'title': 'mode x demographic cells: observed inventory and one '
                 'run measured against them (issue #50)',
        'diagnostic_notice': (
            'DIAGNOSTIC MEASUREMENT OF AN EXISTING RUN - NOT A RESULT ABOUT '
            'THE LIGHT RAIL. The run measured is an arm of a CLOSED, '
            'pre-repair comparability family; nothing here is current model '
            'output and nothing compares scenario against scenario.'),
        'run': {
            'dir': run_dir.name,
            'family': family or 'unattributed',
            'family_label': fam_label,
            'family_note': fam_note,
        },
        'inventory': {
            'held': {
                'jtw_mode_x_sex_sa1': {
                    'source': 'census2021_G62_SA1.csv (2021 Census G62, '
                              'one-method journeys to work)',
                    'geography': f'{n_sa1} core-tier SA1s',
                    'denominator': 'sum of the twelve identified one-method '
                                   'mode cells per sex; this sits below the '
                                   'One_method_Tot column because ABS '
                                   'perturbs/suppresses small SA1 cells - '
                                   'shares are mode-conditional on an '
                                   'identified method',
                    'identified_one_method_journeys_M': obs_tot['M'],
                    'identified_one_method_journeys_F': obs_tot['F'],
                    'thin_cell_min': THIN_CELL_MIN,
                    'context_journeys': {
                        f'{stem}_{s}': g62_ctx[(stem, s)]
                        for stem in G62_CONTEXT for s in ('M', 'F', 'P')},
                },
                'population_age_x_employment_sa1': {
                    'source': 'census2021_G46A/B_SA1.csv - population '
                              'structure, already consumed by B1; carries '
                              'no mode dimension',
                },
                'occupation_x_age_x_sex_sa1': {
                    'source': 'census2021_G60A/B_SA1.csv - no mode '
                              'dimension; unconsumed',
                },
                'industry_x_age_x_sex_sa1': {
                    'source': 'census2021_G54A/B_SA1.csv - no mode '
                              'dimension; unconsumed',
                },
            },
            'not_held': {
                'mode_x_age': 'no held table observes it (G62 has no age '
                              'dimension; held HTS slices carry no '
                              'demographic column) - an ACQUISITION item '
                              '(issue #63), not a modelling gap',
                'mode_x_employment': 'not observed directly; G62 is '
                                     'implicitly workers-only, which is the '
                                     'only employment conditioning held',
                'mode_x_income': 'not observed in held data',
            },
            'hts_held_slices': hts,
            'holdout_untouched': 'data/processed/validation/ (67/143 '
                                 'holdout) not read by this script',
        },
        'observed': {
            'table': 'G62 one-method journey-to-work mode x sex, core-tier '
                     'SA1s, shares within each sex',
            'rows': observed_rows,
            'pt_union_n': pt_union,
            'caveats': [
                '2021 was a COVID census: car share is WFH-inflated and PT '
                'collapsed; treat these shares as structure, not level '
                'targets (docs/archived/design/mode-individualisation.md section 1)',
                'commute-only: journeys to work, one method; multi-method '
                'and worked-at-home journeys excluded (counts in '
                'context_journeys)',
                'ABS randomly perturbs small SA1 cells; thin cells carry '
                'perturbation noise on top of sampling noise',
                'shares are within the sum of identified mode cells, which '
                'is ~2.5% below the One_method_Tot column (small-cell '
                'perturbation/suppression) - so these shares differ '
                'slightly from tables that divide by One_method_Tot',
            ],
        },
        'modelled': {
            'source': 'output_trips.csv.gz main_mode joined to B1 person '
                      'attributes; trips by persons outside B1 (freight, '
                      'external tiers) excluded',
            'trips_tabulated': sum(totals.values()),
            'trips_outside_b1': unmatched,
            'sample_note': 'the run is a population sample; counts are '
                           'sample counts, shares are the comparable '
                           'quantity',
            'mode_totals_all_trips': dict(sorted(totals.items())),
            'mode_totals_commute_trips': dict(sorted(com_totals.items())),
            'all_trips_by': table_json(all_t),
            'commute_trips_by': table_json(com_t),
            'commute_definition': f'trips with end_activity_type == '
                                  f'{COMMUTE_END_ACTIVITY!r}',
        },
        'comparison': {
            'cell': 'commute mode x sex: modelled work-arriving trip shares '
                    'vs observed G62 one-method JTW shares, within each sex',
            'note': 'the model\'s single pt qsim mode is compared against '
                    'the union of the four observed PT modes (listed per '
                    'row); observed Taxi/Rideshare, Truck and Other have no '
                    'modelled counterpart and appear only in the observed '
                    'table',
            'rows': comparison,
        },
    }

    out_path = run_dir / '_demographic_modes.json'
    out_path.write_text(json.dumps(report, indent=1), encoding='utf-8')

    modes = sorted(totals)
    print(report['diagnostic_notice'])
    print(f"run {run_dir.name}  family {family} ({fam_label})")
    for dim in ('age_band', 'sex', 'employment', 'licence'):
        print_table(f'ALL trips: mode share by {dim}', all_t[dim], modes)
    for dim in ('age_band', 'sex', 'employment'):
        print_table(f'COMMUTE trips (end={COMMUTE_END_ACTIVITY}): mode share '
                    f'by {dim}', com_t[dim], modes)
    print('\n== commute mode x sex: modelled vs observed (G62, one-method '
          'JTW, core SA1s; shares within sex)')
    hdr = (f'{"model mode":>12} {"obs M":>8} {"mod M":>8} {"d_pp M":>8}'
           f' {"obs F":>8} {"mod F":>8} {"d_pp F":>8}')
    print('  ' + hdr)
    for row in comparison:
        print('  ' + f"{row['model_mode']:>12}"
              + f" {row['observed_share_M']:>8.4f}"
              + f" {row['modelled_share_M']:>8.4f}"
              + f" {row['delta_pp_M']:>8.2f}"
              + f" {row['observed_share_F']:>8.4f}"
              + f" {row['modelled_share_F']:>8.4f}"
              + f" {row['delta_pp_F']:>8.2f}")
    print(f'\nwrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
