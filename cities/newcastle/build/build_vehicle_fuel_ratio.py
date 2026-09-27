#!/usr/bin/env python
"""Motorcycle-to-car fuel-consumption ratio, observed (DECISIONS.md 9.214, D22, #257).

Source: ABS Survey of Motor Vehicle Use, Australia, 12 months ended 30 June
2020 (cat. 9208.0), data cube data/raw/abs/92080DO001_202006.xls, Table 6
"Average rate of fuel consumption, by state/territory of registration by type
of vehicle by type of fuel" (l/100 km). Read BY LABEL, never by row number:
the block headed by the city's own state/territory (city.json
jurisdiction.subdivision), its "Passenger vehicles" and "Motor cycles" rows,
and the "Total fuel" column.

ratio = motor cycles l/100 km / passenger vehicles l/100 km. The car's
running cost C.scoring.monetary_distance_rate['car'] covers fuel and tyres;
only the FUEL ratio is observed, so the motorbike rate assumes tyres scale
with fuel (stated in C.scoring.motorbike_fuel_ratio). The plans' run config
applies it under B.motorbike.representation = choice only
(src/build/build_matsim_run_inputs.py).

Writes data/processed/observed/vehicle_fuel_ratio.json and asserts the
declared C.scoring.motorbike_fuel_ratio equals the derived ratio.
"""
import sys as _sys
import city as _city
import registry as _registry
import json, math, os

SMVU = _city.path('data/raw/abs/92080DO001_202006.xls')
OUT = _city.path('data/processed/observed/vehicle_fuel_ratio.json')
# the cube's own vocabulary - its sheet, row and column labels - not values
SHEET = 'Table_6'
CAR_ROW = 'Passenger vehicles'
MOTORCYCLE_ROW = 'Motor cycles'
COLUMN = 'Total fuel'

OUTPUT_INPUTS = {
    'data/processed/observed/vehicle_fuel_ratio.json': [
        'data/raw/abs/92080DO001_202006.xls'],
}


def _label(v):
    return '' if v is None or (isinstance(v, float) and math.isnan(v)) else str(v).strip()


def read_rates(frame, state):
    """{row label: l/100 km} for the rows of `state`'s block in the column
    labelled COLUMN. `frame` is the sheet as a header-less table: the column
    is found by its header cell, the block by its heading cell in the first
    column (a row whose other cells are empty) and it ends at the next
    heading. Raises on a missing label rather than guessing."""
    rows = [[_label(v) for v in r] for r in frame.values.tolist()]
    col = None
    for r in rows:
        if COLUMN in r:
            col = r.index(COLUMN)
            break
    if col is None:
        raise SystemExit('no %r column header in %s' % (COLUMN, SHEET))
    start = next((i for i, r in enumerate(rows) if r[0] == state), None)
    if start is None:
        raise SystemExit('no %r block in %s' % (state, SHEET))
    out = {}
    for r in rows[start + 1:]:
        if r[0] and not any(r[1:]):
            break                        # the next state's heading
        if r[0] and r[col]:
            out[r[0]] = float(r[col])
    return out


def main():
    import pandas as pd
    cfg = _registry.load(strict=True)
    state = _city.descriptor()['jurisdiction']['subdivision']
    rates = read_rates(pd.read_excel(SMVU, sheet_name=SHEET, header=None), state)
    car, moto = rates[CAR_ROW], rates[MOTORCYCLE_ROW]
    # carried at full precision: the declared value is this quotient exactly,
    # so the assert below needs no tolerance and no rounding rule
    ratio = moto / car
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(dict(decisions_ref='9.214',
                       source='ABS 9208.0 Survey of Motor Vehicle Use, 12 months ended 30 June '
                              '2020, 92080DO001_202006.xls %s, %s, column %r'
                              % (SHEET, state, COLUMN),
                       units='l_per_100km', state=state,
                       passenger_vehicles_l_per_100km=car,
                       motor_cycles_l_per_100km=moto,
                       motorbike_fuel_ratio=ratio), fh, indent=2)
        fh.write('\n')
    print('%s: passenger vehicles %.1f, motor cycles %.1f l/100 km -> ratio %s'
          % (state, car, moto, ratio))
    declared = cfg.get('C.scoring.motorbike_fuel_ratio')
    if float(declared) != ratio:
        print('DRIFT: C.scoring.motorbike_fuel_ratio declares %s but the survey derives %s - '
              'update the registry field in the same change' % (declared, ratio))
        _sys.exit(1)
    print('C.scoring.motorbike_fuel_ratio matches the derived ratio')


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
