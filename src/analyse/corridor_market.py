"""Modelled activity ends near an intervention's stops, against the observed
attractions the package holds (DECISIONS.md 9.103's next lane, measured 9.120).

A corridor market is a MODELLED quantity - where the demand builder put
destinations, measured against where the schedule puts the stops. Whether that
market is a defect or a fact is decided by comparing it with an observation the
package already carries: the SA1 attraction layer (jobs, retail, food, ...) and
the POI layer. This prints both sides, by purpose, inside a radius of the stops
served by one transit mode of one run's own schedule.

    python src/analyse/corridor_market.py --run <run dir> --mode tram --radius-m 800

Every input is the run's own or the city's: the schedule is the one the run's
config names, the stops are those its routes of `--mode` serve, the demand is
the city's B2 trip table for the run's day type, the observed layers are the
city's D1 files. The radius is an argument, never a constant, so the number a
reader quotes is the one they chose. Reads only; writes nothing. Nothing here
is a result: it describes the inputs, not a run.
"""
import argparse
import collections
import csv
import gzip
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import city as _city                                              # noqa: E402


def schedule_path(run_dir):
    cfg = open(os.path.join(run_dir, 'config.xml'), encoding='utf-8').read()
    m = re.search(r'name="transitScheduleFile" value="([^"]+)"', cfg)
    if not m:
        raise SystemExit('the run config names no transitScheduleFile')
    path = m.group(1)
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(run_dir, path))
    return path


def day_type(run_dir):
    import json
    meta = json.load(open(os.path.join(run_dir, '_meta.json'), encoding='utf-8'))
    return meta['day']


def stop_points(schedule, mode):
    """Distinct (x, y) of every stop facility a route of `mode` serves."""
    facilities = {}
    served = set()
    opener = gzip.open if schedule.endswith('.gz') else open
    with opener(schedule, 'rb') as fh:
        line_mode = None
        in_route = []
        for ev, el in ET.iterparse(fh, events=('start', 'end')):
            if ev == 'start':
                if el.tag == 'stopFacility':
                    facilities[el.get('id')] = (float(el.get('x')), float(el.get('y')))
                elif el.tag == 'transitRoute':
                    in_route = []
                elif el.tag == 'stop':
                    in_route.append(el.get('refId'))
                continue
            if el.tag == 'transportMode':
                line_mode = (el.text or '').strip()
            elif el.tag == 'transitRoute':
                if line_mode == mode:
                    served.update(in_route)
                line_mode = None
                el.clear()
    return sorted(set(facilities[s] for s in served if s in facilities))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True, help='a run directory; its config names the schedule')
    ap.add_argument('--mode', required=True, help='the schedule transportMode whose stops define the corridor')
    ap.add_argument('--radius-m', type=float, required=True, help='corridor radius around a stop, metres')
    a = ap.parse_args()

    pts = stop_points(schedule_path(a.run), a.mode)
    r2 = a.radius_m * a.radius_m
    print('%s stop points served: %d' % (a.mode, len(pts)))
    if not pts:
        raise SystemExit('no stop of mode %s in the schedule' % a.mode)

    def near(x, y):
        for px, py in pts:
            if (x - px) ** 2 + (y - py) ** 2 <= r2:
                return True
        return False

    day = day_type(a.run)
    b2 = _city.path('demand/plans/B2_activity_trips_%s.csv' % day)
    tot = collections.Counter()
    corr = collections.Counter()
    with open(b2, newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            act = row['dest_activity_type']
            tot[act] += 1
            if near(float(row['dest_x']), float(row['dest_y'])):
                corr[act] += 1
    print('\nMODELLED %s trip ends within %.0f m of a %s stop, by activity'
          % (day, a.radius_m, a.mode))
    for act in sorted(tot, key=lambda k: -tot[k]):
        print('  %-10s %9d of %9d  %6.2f%%' % (act, corr[act], tot[act], 100.0 * corr[act] / tot[act]))
    n, t = sum(corr.values()), sum(tot.values())
    print('  %-10s %9d of %9d  %6.2f%%' % ('ALL', n, t, 100.0 * n / t if t else 0))

    zones = _city.path('data/processed/landuse/D1_zone_attractions_SA1.csv')
    with open(zones, newline='', encoding='utf-8') as fh:
        rd = csv.DictReader(fh)
        cols = [c for c in rd.fieldnames
                if c in ('population', 'jobs') or c.startswith('attr_')
                or c in ('office', 'retail', 'food', 'civic', 'health', 'leisure')]
        zt = collections.Counter()
        zc = collections.Counter()
        for row in rd:
            try:
                x, y = float(row['x_mga56']), float(row['y_mga56'])
            except (KeyError, ValueError):
                continue
            inside = near(x, y)
            for c in cols:
                try:
                    v = float(row.get(c) or 0)
                except ValueError:
                    continue
                zt[c] += v
                if inside:
                    zc[c] += v
    print('\nOBSERVED / DERIVED SA1 attractions with centroid within %.0f m of a %s stop'
          % (a.radius_m, a.mode))
    for c in cols:
        print('  %-12s %12.1f of %12.1f  %6.2f%%'
              % (c, zc[c], zt[c], 100.0 * zc[c] / zt[c] if zt[c] else 0))

    try:
        from pyproj import Transformer
    except ImportError:
        print('\n(pyproj not installed - the POI layer is lat/lon and was not projected)')
        return
    tr = Transformer.from_crs('EPSG:4326', _city.crs(), always_xy=True)
    poi = _city.path('data/processed/landuse/D1_poi.csv')
    pw = collections.Counter()
    pc = collections.Counter()
    with open(poi, newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            x, y = tr.transform(float(row['lon']), float(row['lat']))
            g = row['category_group']
            w = float(row['attraction_weight'] or 0)
            pw[g] += w
            if near(x, y):
                pc[g] += w
    print('\nOBSERVED POI attraction weight within %.0f m of a %s stop, by group'
          % (a.radius_m, a.mode))
    for g in sorted(pw, key=lambda k: -pw[k]):
        print('  %-12s %10.1f of %10.1f  %6.2f%%' % (g, pc[g], pw[g], 100.0 * pc[g] / pw[g]))
    n, t = sum(pc.values()), sum(pw.values())
    print('  %-12s %10.1f of %10.1f  %6.2f%%' % ('ALL', n, t, 100.0 * n / t if t else 0))


if __name__ == '__main__':
    main()
