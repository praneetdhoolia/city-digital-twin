#!/usr/bin/env python
"""Measure the light-vehicle day-type factors from the classified hourly counts.

Three demand-generation quantities were assumed for want of this measurement,
and DECISIONS.md 9.61 replaces them with it (deliverable 0b): the
Saturday-to-Sunday level split inside the weekend (the weekend-to-weekday
LEVEL was already measured in C2; the split within it was not), the external
boundary tier's weekend scaling, and the weekend departure-time shift. The
same raw download that measured the freight profile (9.49) carries LIGHT
VEHICLES classified hourly rows for the study slice, so all three are
measurable by exactly the method ``extract_freight_profile.py`` proved.

Outputs, both consumed by ``src/build/build_activity_chains.py``:

* ``data/processed/observed/light_hourly_profile.csv`` -
  ``day_type,hour,share``: the share of a day's light volume moving in each
  hour, per day type. Shares sum to 1 within a day type.
* ``data/processed/observed/light_day_factors.csv`` -
  ``day_type,factor,depart_shift_h,stations,station_days``: light daily
  volume relative to the same station's weekday mean (WEEKDAY = 1.0 by
  identity; median across stations of each station's own ratio), and the
  integer-hour circular shift of that day type's hourly profile that best
  matches the weekday profile (the measured counterpart of the assumed
  weekend departure shift).

Selection rules follow the freight extraction verbatim, all definitional,
and the loader is the one both share (``rms_hourly.load_days``): LIGHT
VEHICLES classification resolved through the observed ``classification_seq``
pairing; stations restricted to the study slice; public holidays excluded;
complete days only; no year filter.

Deterministic: pure aggregation of a hashed raw download, no randomness.
"""

import city as _city

import numpy as np
import pandas as pd

from rms_hourly import HOUR_COLS, load_days

OUT_PROFILE = _city.path('data/processed/observed/light_hourly_profile.csv')
OUT_FACTORS = _city.path('data/processed/observed/light_day_factors.csv')


def load_light_days():
    return load_days('LIGHT VEHICLES', 'light-vehicle')


def best_shift(weekday_profile, day_profile):
    """Integer-hour circular shift of `day_profile` best matching the weekday.

    argmax over shifts of the dot product of the weekday profile with the
    day profile rolled LATER by the shift - i.e. how many hours later the
    weekend day moves to look most like a weekday. Ties break to the
    smallest shift, and the search covers the full circle so nothing about
    the answer is presumed.
    """
    w = np.asarray(weekday_profile, dtype=float)
    p = np.asarray(day_profile, dtype=float)
    scores = [float(np.dot(w, np.roll(p, -s))) for s in range(24)]
    return int(np.argmax(scores))


def main():
    df = load_light_days()
    day_types = sorted(df.day_type.unique())

    profiles = {}
    rows = []
    for dt in day_types:
        d = df[df.day_type == dt]
        hour_sums = d[HOUR_COLS].sum()
        share = (hour_sums / hour_sums.sum()).to_numpy()
        profiles[dt] = share
        for h in range(24):
            rows.append(dict(day_type=dt, hour=h, share=round(float(share[h]), 6)))
    pd.DataFrame(rows).to_csv(OUT_PROFILE, index=False, lineterminator='\n')

    per_station = (df.groupby(['station_key', 'day_type'])
                   .daily_total.mean().unstack())
    out = []
    for dt in day_types:
        if dt == 'WEEKDAY':
            factor, n_st = 1.0, int(per_station['WEEKDAY'].notna().sum())
        else:
            both = per_station[[dt, 'WEEKDAY']].dropna()
            ratio = both[dt] / both['WEEKDAY']
            factor, n_st = float(ratio.median()), len(both)
        shift = 0 if dt == 'WEEKDAY' else best_shift(profiles['WEEKDAY'],
                                                     profiles[dt])
        out.append(dict(day_type=dt, factor=round(factor, 4),
                        depart_shift_h=shift, stations=n_st,
                        station_days=int((df.day_type == dt).sum())))
    pd.DataFrame(out).to_csv(OUT_FACTORS, index=False, lineterminator='\n')

    f = {r['day_type']: r for r in out}
    sat, sun = f.get('SAT', {}), f.get('SUN', {})
    print('light day factors: ' + '  '.join(
        '%s=%.4f (shift %dh, %d stations)' % (r['day_type'], r['factor'],
                                              r['depart_shift_h'],
                                              r['stations'])
        for r in out))
    if sat and sun and sun['factor'] > 0:
        print('SAT:SUN split = %.4f (was assumed 1.1875)'
              % (sat['factor'] / sun['factor']))
    print('wrote %s and %s' % (OUT_PROFILE, OUT_FACTORS))


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
