#!/usr/bin/env python
"""The RMS permanent-station hourly counts, one classification at a time.

`extract_freight_profile.py` (HEAVY VEHICLES, 9.49) and
`extract_daytype_factors.py` (LIGHT VEHICLES, 9.61) read the same 871 MB raw
archive by the same rules and each carried the loader; this is the one copy.
The rules are definitional, not tuned:

* the classification's code is resolved through the ``classification_seq ->
  classification_type`` pairing observed in the AADT slice - the hourly file
  carries only the code;
* stations restricted to the study slice (``traffic_count_stations_newcastle``);
* public holidays excluded: the model's day types are typical WEEKDAY/SAT/SUN
  and a public-holiday Monday is none of them;
* complete days only: rows whose 24 hourly cells sum to their own
  ``daily_total`` (blank hourly cells are zero counts in this format; a row
  whose hours do not reconcile is a partial day);
* no year filter: every classified year in the raw download contributes.

Deterministic: pure aggregation of a hashed raw download, no randomness.
"""
import city as _city

import zipfile

import pandas as pd

RAW_ZIP = _city.path('data/raw/counts/rms_hourly_permanent.zip')
STATIONS = _city.path('data/processed/observed/traffic_count_stations_newcastle.csv')
AADT = _city.path('data/processed/observed/traffic_aadt.csv')

HOUR_COLS = ['hour_%02d' % h for h in range(24)]
# The model's service week (cities/<city>/city.json day_types) named over
# ISO day-of-week, which the raw data carries as 1=Monday..7=Sunday.
DAY_TYPE_OF_DOW = {1: 'WEEKDAY', 2: 'WEEKDAY', 3: 'WEEKDAY', 4: 'WEEKDAY',
                   5: 'WEEKDAY', 6: 'SAT', 7: 'SUN'}


def classification_seq(label):
    """The classification code for `label` (e.g. 'HEAVY VEHICLES'), read
    from the AADT slice, which carries both the code and its label."""
    a = pd.read_csv(AADT, usecols=['classification_seq', 'classification_type'])
    pairs = a.drop_duplicates()
    m = pairs[pairs.classification_type == label]
    if len(m) != 1:
        raise SystemExit('expected exactly one %s classification code in %s, found %d'
                         % (label, AADT, len(m)))
    return int(m.classification_seq.iloc[0])


def load_days(label, what):
    """Every complete, non-holiday station-day of classification `label` at
    the study stations, hourly cells filled and `day_type` named; `what` is
    the phrase the refusal prints ('heavy-vehicle')."""
    seq = classification_seq(label)
    slice_keys = set(pd.read_csv(STATIONS, usecols=['station_key'])
                     .station_key.astype(str))
    usecols = (['station_key', 'classification_seq', 'day_of_week',
                'public_holiday', 'daily_total'] + HOUR_COLS)
    z = zipfile.ZipFile(RAW_ZIP)
    frames = []
    for name in sorted(z.namelist()):
        df = pd.read_csv(z.open(name), usecols=usecols)
        df = df[(df.classification_seq == seq)
                & df.station_key.astype(str).isin(slice_keys)
                & (~df.public_holiday.astype(bool))]
        if len(df):
            frames.append(df)
    if not frames:
        raise SystemExit('no classified %s hourly rows found for the study '
                         'slice - the raw download or the slice changed' % what)
    df = pd.concat(frames, ignore_index=True)
    hours = df[HOUR_COLS].fillna(0.0)
    complete = hours.sum(axis=1).round(0) == df.daily_total.fillna(-1).round(0)
    df = df[complete & (df.daily_total > 0)].reset_index(drop=True)
    df[HOUR_COLS] = df[HOUR_COLS].fillna(0.0)
    df['day_type'] = df.day_of_week.map(DAY_TYPE_OF_DOW)
    return df
