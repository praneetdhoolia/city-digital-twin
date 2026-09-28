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

The motorcycle-to-car USE ratio (D28, F39) from the same cube: Table 4
"Motor vehicle use, by state/territory of registration by type of vehicle",
the same state block, its "Passenger vehicles" and "Motor cycles" rows, the
columns "Total kilometres travelled" (million) and "Number of vehicles".
km per vehicle = total km / number of vehicles, and

    use ratio = motor cycles km per vehicle / passenger vehicles km per vehicle,

computed from the two totals rather than from the published "Average
kilometres travelled" column, which the cube rounds to 0.1 thousand km (that
column is carried into the output beside it as a cross-check). A vehicle
driven on a fraction of the days a car is driven offers itself as a trip
option on that fraction of days, so under B.motorbike.daily_use = use_ratio
the plans builder makes a possessed motorcycle available to its rider on the
simulated day with this probability. Its limits are stated on the field
(B.motorbike.daily_use_ratio): a fleet-average annual distance, not a count
of days in use, recreational riding included. Writes
data/processed/observed/vehicle_use_ratio.json and asserts the declared
B.motorbike.daily_use_ratio equals the derived ratio.
"""
import sys as _sys
import city as _city
import registry as _registry
import json, math, os

SMVU = _city.path('data/raw/abs/92080DO001_202006.xls')
OUT = _city.path('data/processed/observed/vehicle_fuel_ratio.json')
USE_OUT = _city.path('data/processed/observed/vehicle_use_ratio.json')
# the cube's own vocabulary - its sheet, row and column labels - not values
SHEET = 'Table_6'
CAR_ROW = 'Passenger vehicles'
MOTORCYCLE_ROW = 'Motor cycles'
COLUMN = 'Total fuel'
USE_SHEET = 'Table_4'
KM_COLUMN = 'Total kilometres travelled'
VEHICLES_COLUMN = 'Number of vehicles'
AVERAGE_COLUMN = 'Average kilometres travelled'

OUTPUT_INPUTS = {
    'data/processed/observed/vehicle_fuel_ratio.json': [
        'data/raw/abs/92080DO001_202006.xls'],
    'data/processed/observed/vehicle_use_ratio.json': [
        'data/raw/abs/92080DO001_202006.xls'],
}


def _label(v):
    return '' if v is None or (isinstance(v, float) and math.isnan(v)) else str(v).strip()


def read_rates(frame, state, column=COLUMN, sheet=SHEET):
    """{row label: value} for the rows of `state`'s block in the column
    labelled `column` (Table 6's l/100 km by default). `frame` is the sheet as
    a header-less table: the column is found by its header cell, the block by
    its heading cell in the first column (a row whose other cells are empty)
    and it ends at the next heading. Raises on a missing label rather than
    guessing."""
    rows = [[_label(v) for v in r] for r in frame.values.tolist()]
    col = None
    for r in rows:
        if column in r:
            col = r.index(column)
            break
    if col is None:
        raise SystemExit('no %r column header in %s' % (column, sheet))
    start = next((i for i, r in enumerate(rows) if r[0] == state), None)
    if start is None:
        raise SystemExit('no %r block in %s' % (state, sheet))
    out = {}
    for r in rows[start + 1:]:
        if r[0] and not any(r[1:]):
            break                        # the next state's heading
        if r[0] and r[col]:
            out[r[0]] = float(r[col])
    return out


def read_use(frame, state):
    """The motorcycle-to-car use ratio from Table 4's `state` block, by label:
    each type's km per vehicle is its total kilometres (million) over its
    number of vehicles, and the ratio is motor cycles' over passenger
    vehicles'. Returns the four totals, the two published (rounded) averages
    and the ratio at full precision."""
    km = read_rates(frame, state, KM_COLUMN, USE_SHEET)
    n = read_rates(frame, state, VEHICLES_COLUMN, USE_SHEET)
    avg = read_rates(frame, state, AVERAGE_COLUMN, USE_SHEET)
    for row in (CAR_ROW, MOTORCYCLE_ROW):
        if row not in km or row not in n or not n[row]:
            raise SystemExit('no %r row with a vehicle count in %s %s'
                             % (row, USE_SHEET, state))
    car = km[CAR_ROW] / n[CAR_ROW]
    moto = km[MOTORCYCLE_ROW] / n[MOTORCYCLE_ROW]
    return dict(passenger_vehicles_km_million=km[CAR_ROW],
                passenger_vehicles_number=n[CAR_ROW],
                motor_cycles_km_million=km[MOTORCYCLE_ROW],
                motor_cycles_number=n[MOTORCYCLE_ROW],
                passenger_vehicles_published_average_km_thousand=avg.get(CAR_ROW),
                motor_cycles_published_average_km_thousand=avg.get(MOTORCYCLE_ROW),
                daily_use_ratio=moto / car)


def write_use(cfg, pd, state):
    """Write vehicle_use_ratio.json; True when the declared
    B.motorbike.daily_use_ratio equals the derived ratio."""
    use = read_use(pd.read_excel(SMVU, sheet_name=USE_SHEET, header=None), state)
    with open(USE_OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(dict(decisions_ref='9.217',
                       source='ABS 9208.0 Survey of Motor Vehicle Use, 12 months ended 30 June '
                              '2020, 92080DO001_202006.xls %s, %s, columns %r / %r'
                              % (USE_SHEET, state, KM_COLUMN, VEHICLES_COLUMN),
                       units='ratio', state=state, **use), fh, indent=2)
        fh.write('\n')
    print('%s: passenger vehicles %.0f million km / %d, motor cycles %.0f million km / %d '
          '-> km per vehicle ratio %s (published averages %s and %s thousand km)'
          % (state, use['passenger_vehicles_km_million'], use['passenger_vehicles_number'],
             use['motor_cycles_km_million'], use['motor_cycles_number'],
             use['daily_use_ratio'],
             use['passenger_vehicles_published_average_km_thousand'],
             use['motor_cycles_published_average_km_thousand']))
    declared = cfg.get('B.motorbike.daily_use_ratio')
    if float(declared) != use['daily_use_ratio']:
        print('DRIFT: B.motorbike.daily_use_ratio declares %s but the survey derives %s - '
              'update the registry field in the same change'
              % (declared, use['daily_use_ratio']))
        return False
    print('B.motorbike.daily_use_ratio matches the derived ratio')
    return True


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
    fuel_ok = float(declared) == ratio
    if not fuel_ok:
        print('DRIFT: C.scoring.motorbike_fuel_ratio declares %s but the survey derives %s - '
              'update the registry field in the same change' % (declared, ratio))
    else:
        print('C.scoring.motorbike_fuel_ratio matches the derived ratio')
    use_ok = write_use(cfg, pd, state)
    if not (fuel_ok and use_ok):
        _sys.exit(1)


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
