#!/usr/bin/env python
"""Measure the heavy-vehicle temporal profile from the classified hourly counts.

The freight background layer (issue #24, DECISIONS.md 9.49) needs two temporal
facts: WHEN heavy vehicles move within a day, and HOW MUCH lighter weekend
freight is than weekday freight. Both are MEASURED here rather than assumed -
the RMS permanent hourly counts carry a HEAVY VEHICLES classification, and the
study slice holds classified rows for stations inside the study area.

Outputs, both consumed by ``src/build/build_activity_chains.py``:

* ``data/processed/observed/freight_hourly_profile.csv`` -
  ``day_type,hour,share``: the share of a day's heavy volume departing in each
  hour, per day type. Shares sum to 1 within a day type.
* ``data/processed/observed/freight_day_factors.csv`` -
  ``day_type,factor,stations,station_days``: heavy daily volume relative to the
  same station's weekday mean (WEEKDAY = 1.0 by identity). The factor is the
  median across stations of each station's own SAT/SUN-to-weekday ratio, so a
  station that counts more days does not dominate the level.

Selection rules, all definitional rather than tuned, are the shared loader's
(``rms_hourly.load_days``): HEAVY VEHICLES classification only, resolved
through the observed ``classification_seq -> classification_type`` pairing;
stations restricted to the study slice; public holidays excluded; complete
days only; no year filter - a cutoff would be an undeclared modelling choice;
the profile is a SHAPE, and the volume it scales is declared and swept
elsewhere (``B.freight.trip_ratio``).

Deterministic: pure aggregation of a hashed raw download, no randomness.
"""

import city as _city

import pandas as pd

from rms_hourly import HOUR_COLS, load_days

OUT_PROFILE = _city.path('data/processed/observed/freight_hourly_profile.csv')
OUT_FACTORS = _city.path('data/processed/observed/freight_day_factors.csv')


def load_heavy_days():
    return load_days('HEAVY VEHICLES', 'heavy-vehicle')


def main():
    df = load_heavy_days()
    day_types = sorted(df.day_type.unique())

    # hourly shape: total heavy volume per hour over total heavy volume,
    # per day type - a volume-weighted profile, which is what a background
    # load samples departures from
    rows = []
    for dt in day_types:
        d = df[df.day_type == dt]
        hour_sums = d[HOUR_COLS].sum()
        total = float(hour_sums.sum())
        for h in range(24):
            rows.append(dict(day_type=dt, hour=h,
                             share=round(float(hour_sums.iloc[h]) / total, 6)))
    profile = pd.DataFrame(rows)

    # day factors: each station's own SAT/SUN mean daily heavy volume over its
    # own weekday mean, median across stations - paired within station so the
    # mix of large and small stations cancels
    per = (df.groupby(['station_key', 'day_type']).daily_total.mean()
             .unstack('day_type'))
    per = per[per.get('WEEKDAY', pd.Series(dtype=float)).notna()]
    factors = []
    for dt in day_types:
        if dt == 'WEEKDAY':
            factors.append(dict(day_type=dt, factor=1.0,
                                stations=int(per.WEEKDAY.notna().sum()),
                                station_days=int((df.day_type == dt).sum())))
            continue
        ratio = (per[dt] / per.WEEKDAY).dropna()
        factors.append(dict(day_type=dt, factor=round(float(ratio.median()), 4),
                            stations=int(ratio.size),
                            station_days=int((df.day_type == dt).sum())))
    factors = pd.DataFrame(factors)

    profile.to_csv(OUT_PROFILE, index=False, lineterminator='\n')
    factors.to_csv(OUT_FACTORS, index=False, lineterminator='\n')
    print('freight_hourly_profile.csv: %d rows from %d station-days at %d stations'
          % (len(profile), len(df), df.station_key.nunique()))
    print('freight_day_factors.csv:')
    print(factors.to_string(index=False))
    peak = profile[profile.day_type == 'WEEKDAY'].nlargest(3, 'share')
    print('weekday peak hours: %s'
          % ', '.join('%02d:00 %.1f%%' % (r.hour, 100 * r.share)
                      for r in peak.itertuples()))


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
