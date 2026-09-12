#!/usr/bin/env python
"""Newcastle's daily Opal tap-ons by mode, as BOUNDS, from the raw Opal Patronage files (#185).

The publication rounds every hourly cell to the nearest 100 and prints `<100`
below it (Opal Tap Data documentation v2.0, May 2026), so a cell is an
interval, not a number: `<100` is [0, 49] and `N00` is [N00-50, N00+49]. A
day's total for a mode is the sum of its hourly intervals, and THAT is what
this writes - a lower and an upper bound per date and mode - so nothing
downstream can quote a centre value the publication never gave.

Why it matters: "Newcastle and surrounds" (Newcastle Interchange, the light
rail, bus stops in postcodes 2293 and 2300) is the only DISCLOSED count of
the Stockton ferry's Newcastle-side wharf the package holds; every ferry
target before this was derived from a lockdown-month census cell. The
weekday mean of the ferry bounds is the observation the ferry target can be
held against (a bound, and stated as one).

Reads data/raw/opal/opal_patronage/*.txt; writes
data/processed/observed/opal_patronage_newcastle_daily.csv and a report.
"""
import city as _city
import csv
import datetime
import glob
import json
import os

RAW = _city.path('data/raw/opal/opal_patronage')
OUT = _city.path('data/processed/observed/opal_patronage_newcastle_daily.csv')
REPORT = _city.path('data/processed/observed/_opal_patronage_report.json')
REGION = _city.descriptor().get('opal_patronage_region', 'Newcastle and surrounds')
import registry as _registry  # noqa: E402
# the publication's rounding unit, declared as the definition it is (#188)
ROUND = int(_registry.load().get('CAL.pt.opal_patronage_rounding'))


def bounds(cell):
    """The interval a published cell stands for."""
    s = str(cell).strip()
    if s.startswith('<'):
        return 0, ROUND // 2 - 1
    v = int(float(s))
    return max(0, v - ROUND // 2), v + ROUND // 2 - 1


def main():
    files = sorted(glob.glob(os.path.join(RAW, 'Opal_Patronage_*.txt')))
    if not files:
        raise SystemExit('no raw Opal Patronage files under %s - run '
                         'cities/<city>/extract/fetch_tpa_daily.py opal_patronage first' % RAW)
    rows = {}
    for f in files:
        with open(f, encoding='utf-8') as fh:
            rd = csv.DictReader(fh, delimiter='|')
            for r in rd:
                if r['ti_region'] != REGION:
                    continue
                key = (r['trip_origin_date'], r['mode_name'])
                lo_on, hi_on = bounds(r['Tap_Ons'])
                lo_off, hi_off = bounds(r['Tap_Offs'])
                d = rows.setdefault(key, dict(date=key[0], mode=key[1], hours=0,
                                               tap_ons_lower=0, tap_ons_upper=0,
                                               tap_offs_lower=0, tap_offs_upper=0))
                d['hours'] += 1
                d['tap_ons_lower'] += lo_on
                d['tap_ons_upper'] += hi_on
                d['tap_offs_lower'] += lo_off
                d['tap_offs_upper'] += hi_off
    out = []
    for key in sorted(rows):
        d = rows[key]
        day = datetime.date.fromisoformat(d['date'])
        d['day_type'] = 'WEEKDAY' if day.weekday() < 5 else ('SAT' if day.weekday() == 5 else 'SUN')
        out.append(d)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cols = ['date', 'day_type', 'mode', 'hours', 'tap_ons_lower', 'tap_ons_upper',
            'tap_offs_lower', 'tap_offs_upper']
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator='\n')
        w.writeheader()
        w.writerows(out)
    # the report: per mode and day type, the mean of the bounds
    summary = {}
    for d in out:
        s = summary.setdefault(d['mode'], {}).setdefault(d['day_type'], dict(days=0, lo=0.0, hi=0.0))
        s['days'] += 1
        s['lo'] += d['tap_ons_lower']
        s['hi'] += d['tap_ons_upper']
    for mode in summary:
        for dt, s in summary[mode].items():
            s['tap_ons_mean_lower'] = round(s.pop('lo') / s['days'], 1)
            s['tap_ons_mean_upper'] = round(s.pop('hi') / s['days'], 1)
    report = dict(
        region=REGION, files=len(files), first=out[0]['date'], last=out[-1]['date'],
        rounding='hourly cells rounded to the nearest %d, "<%d" below; a day is the sum of '
                 'the hourly intervals, so every figure here is a BOUND' % (ROUND, ROUND),
        source='TfNSW Open Data Hub - Opal Patronage (CC-BY 4.0); see data/raw/opal/opal_patronage/provenance.json',
        tap_ons_by_mode_and_day_type=summary)
    with open(REPORT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(report, fh, indent=1)
        fh.write('\n')
    print('wrote %s (%d rows, %s..%s)' % (_city.rel(OUT), len(out), out[0]['date'], out[-1]['date']))
    for mode, by in sorted(summary.items()):
        wd = by.get('WEEKDAY', {})
        print('  %-11s weekday tap-ons %8.0f .. %-8.0f over %d days'
              % (mode, wd.get('tap_ons_mean_lower', 0), wd.get('tap_ons_mean_upper', 0), wd.get('days', 0)))


if __name__ == '__main__':
    main()
