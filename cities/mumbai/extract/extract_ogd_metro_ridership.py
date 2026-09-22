"""Extract MMRDA's daily ridership of Metro Lines 2A/7 and the Monorail from the OGD CSVs.

The two files (`ogd_metro_2a_7_ridership_daily_2024_2025`, 1 January 2024 -
19 September 2025; `ogd_monorail_ridership_daily_2024_2025`, 1 October 2024 -
21 September 2025), published by MMRDA on the Open Government Data platform
and downloaded by the user from its logged-in portal, give one row a day with
the ticket channels (paper QR, mobile application, WhatsApp, NCMC and other)
and the total. Every row is kept with its date in ISO form; the channel sum is
checked against the printed total; the audit prints the weekday mean of the
latest full three months per line, which `build_mode_targets.py` reads as the
observed daily ridership of those lines. `Total Ridership` is the operator's
count of trips; whether it is entries or journeys is not stated.
"""
from collections import defaultdict
import csv
import json
from datetime import date
from pathlib import Path
from statistics import mean

import city
from extract_census_controls import source, write

SOURCES = {
    'ogd_metro_2a_7_ridership_daily_2024_2025': 'Metro Lines 2A and 7',
    'ogd_monorail_ridership_daily_2024_2025': 'Monorail',
}
OUTPUT_INPUTS = {
    'data/processed/observed/ogd_metro_daily_ridership.csv': [
        'data/raw/transit/ogd_metro_2a_7_ridership_daily_*.csv', 'data/raw/transit/ogd_monorail_ridership_daily_*.csv'],
    'data/processed/acquisition/ogd_metro_ridership_audit.json': [
        'data/raw/transit/ogd_metro_2a_7_ridership_daily_*.csv', 'data/raw/transit/ogd_monorail_ridership_daily_*.csv'],
}


def main():
    rows, audit = [], {}
    for source_id, line in SOURCES.items():
        record, path = source(source_id, 'transit')
        with path.open(encoding='utf-8-sig', newline='') as stream:
            table = list(csv.DictReader(stream))
        channels = [c for c in table[0] if c not in ('Date', 'Line', 'Total Ridership')]
        mismatched, days = 0, defaultdict(list)
        for r in table:
            d, m, y = (int(x) for x in r['Date'].split('-'))
            day = date(y, m, d)
            total = int(r['Total Ridership'])
            parts = {c: int(r[c] or 0) for c in channels}
            if sum(parts.values()) != total:
                mismatched += 1
            rows.append(dict(line=line, date=day.isoformat(), weekday=day.weekday() < 5,
                             **{c.lower().replace(' ', '_').replace('whatspp', 'whatsapp'): v for c, v in parts.items()},
                             total_ridership=total, channel_sum_equals_total=sum(parts.values()) == total,
                             source='observed', source_id=source_id, source_sha256=record['sha256'],
                             printed_line=r['Line']))
            days[(day.year, day.month)].append((day.weekday() < 5, total))
        months = sorted(days)
        latest_full = [m for m in months if len(days[m]) >= 28][-3:]
        weekday_latest = [t for m in latest_full for wd, t in days[m] if wd]
        weekend_latest = [t for m in latest_full for wd, t in days[m] if not wd]
        audit[source_id] = dict(
            line=line, rows=len(table), first_date=rows[-len(table)]['date'], last_date=rows[-1]['date'],
            channels=channels, channel_sum_mismatches=mismatched,
            latest_full_months=['%d-%02d' % m for m in latest_full],
            weekday_mean_latest_three_months=round(mean(weekday_latest)),
            weekend_mean_latest_three_months=round(mean(weekend_latest)) if weekend_latest else None,
            weekday_mean_by_month={'%d-%02d' % m: round(mean(t for wd, t in days[m] if wd)) for m in months
                                   if any(wd for wd, _ in days[m])})
    write('ogd_metro_daily_ridership.csv', rows)
    out = dict(source='observed', purpose='MMRDA daily ridership on the OGD platform, per line',
               lines=audit,
               limitations=['The count is the operator\'s trips; entries or linked journeys is not stated.',
                            'Line 2A and Line 7 are one series; the two lines are not separated.',
                            'The Monorail series begins 1 October 2024 (the line reopened after its suspension).'])
    Path(city.path('data/processed/acquisition/ogd_metro_ridership_audit.json')).write_text(
        json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: {kk: v[kk] for kk in ('rows', 'first_date', 'last_date', 'channel_sum_mismatches',
                                                'latest_full_months', 'weekday_mean_latest_three_months')}
                      for k, v in audit.items()}, indent=1))


if __name__ == '__main__':
    main()
