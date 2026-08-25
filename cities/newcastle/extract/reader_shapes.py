#!/usr/bin/env python
"""Newcastle's reader-shape adapter (issue #62 A5).

The framework's demand and measurement readers consume the declared shapes in
`config/schema/reader_shapes.json`; this module maps Newcastle's PUBLISHED
shapes - the NSW Household Travel Survey labels and the RMS/TfNSW classified
traffic-count vocabulary - to that schema AT READ TIME. Nothing is rewritten:
the processed artefacts keep their published column names and this module is
the only place the framework's readers meet them. The framework resolves it
through `city.readers()` (src/city.py, the only module that knows where a
city lives); a second city supplies its own copy speaking its own agency's
vocabulary.

Only the two thin families are adapted (HTS mode-share aggregates and
classified counts). The census family and the remaining HTS readers are
declared but still source-shaped - `config/schema/reader_shapes.json` lists
exactly which.
"""
import city as _city

# --------------------------------------------------------------------------
# HTS mode-share aggregates
# --------------------------------------------------------------------------
HTS_MODE_FILE = 'data/processed/hts/hts_mode.csv'
# The NSW HTS financial-year label of the base-year survey, exactly as the
# published files and the derived validation targets spell it.
SURVEY_VINTAGE = '2024/25'
# The geography level of the published series the mode-share target uses.
SURVEY_GEOGRAPHY = 'lga'
# framework mode_category -> the label the NSW HTS prints for it. The survey
# decorates labels with significance asterisks ('Vehicle passenger*'); those
# are stripped before matching, so these are the clean spellings.
MODE_CATEGORY_LABELS = {
    'car_driver': 'Vehicle driver',
    'car_passenger': 'Vehicle passenger',
    'walk_only': 'Walk only',
    'walk_linked': 'Walk linked',
    'public_transport': 'Public transport',
    'other': 'Other',
}


def survey_vintage():
    """The base-year survey vintage, in the survey's own spelling."""
    return SURVEY_VINTAGE


def mode_category_labels():
    """framework mode_category -> this survey's printed label."""
    return dict(MODE_CATEGORY_LABELS)


def mode_share_table():
    """The base-year mode-share rows, one per (area_name, mode_category).

    A list of dicts with the declared columns: `area_name`, `mode_category`
    (a framework category, or 'unmapped:<label>' for a published category the
    framework does not consume - it still counts toward totals), `trips`
    (unlinked TRIPS_BY_MODE, summed) and `linked_share_pct` (the published
    linked MODE_SHARE, None where not published as a single row).
    """
    import pandas as pd
    h = pd.read_csv(_city.path(HTS_MODE_FILE))
    h = h[(h['FINANCIAL_YEAR'] == SURVEY_VINTAGE)
          & (h['geography'] == SURVEY_GEOGRAPHY)].copy()
    cleaned = (h['TRAVEL_MODE'].str.replace('*', '', regex=False)
               .str.strip().str.lower())
    label_to_cat = {v.lower(): k for k, v in MODE_CATEGORY_LABELS.items()}
    h['mode_category'] = [label_to_cat.get(m, 'unmapped:%s' % m)
                          for m in cleaned]
    out = []
    for (area, cat), grp in h.groupby(['area_name', 'mode_category'],
                                      sort=True):
        share = grp['MODE_SHARE'].dropna()
        out.append(dict(
            area_name=area,
            mode_category=cat,
            trips=float(grp['TRIPS_BY_MODE'].sum()),
            linked_share_pct=(float(share.iloc[0]) if len(share) == 1
                              else None)))
    return out


# --------------------------------------------------------------------------
# classified traffic counts
# --------------------------------------------------------------------------
COUNTS_FILE = 'data/processed/observed/traffic_aadt.csv'
# The RMS classification labels that mean TOTAL volume - a station publishes
# either a classified ALL VEHICLES total or an UNCLASSIFIED count, never both
# meanings under one label.
TOTAL_VOLUME_CLASSES = ('ALL VEHICLES', 'UNCLASSIFIED')
# RMS period label -> the framework's day-type period vocabulary. The other
# published periods (peaks, ALL DAYS, PUBLIC HOLIDAYS) are not consumed by
# the framework and are dropped here.
PERIOD_LABELS = {'WEEKDAYS': 'weekday', 'WEEKENDS': 'weekend'}


def total_volume_counts():
    """Total-vehicle-volume observations as a DataFrame with the declared
    columns: station_key, year, period ('weekday'/'weekend'), volume.

    One row per published observation (directions and total-classification
    variants stay separate rows, exactly as published) - the framework does
    its own aggregation, so the adapter adds none.
    """
    import pandas as pd
    t = pd.read_csv(_city.path(COUNTS_FILE), low_memory=False)
    t = t[t['classification_type'].isin(TOTAL_VOLUME_CLASSES)
          & t['period'].isin(PERIOD_LABELS)].copy()
    return pd.DataFrame(dict(
        station_key=t['station_key'],
        year=t['year'],
        period=t['period'].map(PERIOD_LABELS),
        volume=t['traffic_count']))
