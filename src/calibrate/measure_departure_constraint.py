#!/usr/bin/env python
"""Measure the B2 departure-hour profile against the observed traffic profile
(#63 item 6: the constraint that makes 144 assumed numbers falsifiable).

`B.activity.departure_profile` declares six per-purpose 24-hour shapes - 144
numbers, all assumed, previously falsifiable by nothing: no observed
per-purpose departure distribution exists for this city. What IS observed is
the RMS classified hourly traffic profile (`light_hourly_profile.csv`, per
day type). The counts cannot replace the per-purpose shapes - they see
vehicles in motion, all purposes mixed - but they CAN falsify the shapes'
weighted sum: if the demand the declared profiles actually generated peaks in
the wrong hours, no purpose-level story rescues it.

So this measures, per day type, the realised departure-hour distribution of
the built B2 person trips (freight excluded - the freight tier's departures
were MEASURED from the freight profile, 9.49, and comparing them here would
test an identity) against the observed light-vehicle hourly share, and writes
`params/C6_departure_profile_check.json`: both profiles, per-hour deltas, and
summary statistics. A CONSTRAINT, never a target (9.8/9.13): nothing is
fitted to it, and the pre-registered 210 do not grow.

Stated limitations of the comparison, in the artefact itself:
  * counts see traversals across the whole trip duration, departures are an
    instant - the observed profile is a smeared version of the departure one;
  * counts see light VEHICLES, the B2 table is person trips before mode
    assignment - the mix differs by the non-car share.
Both smear, neither inverts a peak: the constraint is on gross shape.

    python src/calibrate/measure_departure_constraint.py
"""
import csv
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import city as _city  # noqa: E402

OBSERVED = _city.path('data/processed/observed/light_hourly_profile.csv')
PLANS = _city.path('demand', 'plans')
OUT = _city.path('params', 'C6_departure_profile_check.json')


def observed_profiles():
    out = {}
    with open(OBSERVED, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out.setdefault(r['day_type'], [0.0] * 24)
            out[r['day_type']][int(r['hour'])] = float(r['share'])
    return out


def modelled_profile(day):
    counts = [0] * 24
    path = os.path.join(PLANS, 'B2_activity_trips_%s.csv' % day)
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r.get('agent_tier') == 'freight':
                continue
            hour = int(float(r['dep_time_s'])) // 3600
            counts[hour % 24] += 1
    total = sum(counts)
    return [c / total for c in counts], total


def main():
    obs = observed_profiles()
    doc = dict(
        purpose='the observed-profile CONSTRAINT on the weighted sum of the '
                'declared B.activity.departure_profile shapes (#63 item 6)',
        rule='a CONSTRAINT, never a target (9.8/9.13): reported, not fitted; '
             'the pre-registered target set does not grow',
        limitations=[
            'counts see traversals across the trip duration; departures are '
            'an instant - the observed profile is a smeared departure profile',
            'counts see light VEHICLES; the B2 table is person trips before '
            'mode assignment - composition differs by the non-car share'],
        day_types={})
    for day in sorted(obs):
        model, n = modelled_profile(day)
        deltas = [round(m - o, 5) for m, o in zip(model, obs[day])]
        overlap = sum(min(m, o) for m, o in zip(model, obs[day]))
        doc['day_types'][day] = dict(
            b2_person_trips=n,
            modelled_share_by_hour=[round(x, 5) for x in model],
            observed_light_vehicle_share_by_hour=obs[day],
            delta_by_hour=deltas,
            max_abs_delta=max(abs(d) for d in deltas),
            profile_overlap=round(overlap, 4),
            modelled_peak_hour=model.index(max(model)),
            observed_peak_hour=obs[day].index(max(obs[day])))
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, indent=2)
        f.write('\n')
    for day, d in doc['day_types'].items():
        print('%-8s %8d trips  overlap %.3f  max|delta| %.4f  peak modelled '
              '%02d:00 vs observed %02d:00'
              % (day, d['b2_person_trips'], d['profile_overlap'],
                 d['max_abs_delta'], d['modelled_peak_hour'],
                 d['observed_peak_hour']))
    print('-> %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
