#!/usr/bin/env python
"""Bus occupancy for the city's own depots from the raw BOAM week (#185).

BOAM (Bus Opal Assignment Model) gives, for every bus trip at every stop,
the occupancy RANGE the model assigns (bands of 20 passengers) beside the
vehicle's seated and standing capacity. State-wide it is ~400 MB a day; the
raw week under data/raw/boam/ is reduced here to the depots the city's bus
contract runs from, which are found from the data - a depot whose stops sit
inside the study area's postcodes is the city's - so no depot name is typed.

Written per (service date, route, direction, hour band, trip point,
occupancy range): the count of stop observations, the mean seated and total
capacity. It is an OBSERVATION of bus loading for the bus-vs-light-rail
split and the crowding multiplier (#185), entered as a constraint, never a
target (DECISIONS.md 9.8, 9.13).
"""
import city as _city
import collections
import csv
import glob
import json
import os

RAW = _city.path('data/raw/boam')
OUT = _city.path('data/processed/observed/boam_bus_occupancy_week.csv')
REPORT = _city.path('data/processed/observed/_boam_report.json')


def inside_boundary():
    """A point-in-boundary test over the dissolved LGA boundary (city CRS)."""
    import geopandas as gpd
    import shapely
    from pyproj import Transformer
    lga = gpd.read_file(_city.path('data/processed/zones/zones_LGA.gpkg'))
    if 'zone_tier' in lga.columns:
        lga = lga[lga.zone_tier == 'core']
    geom = lga.to_crs(_city.crs()).geometry.union_all()
    tf = Transformer.from_crs('EPSG:4326', _city.crs(), always_xy=True)

    def test(lat, lon):
        x, y = tf.transform(lon, lat)
        return shapely.contains(geom, shapely.points(x, y))
    return test


def main():
    files = sorted(glob.glob(os.path.join(RAW, 'BOAM_*.txt')))
    if not files:
        raise SystemExit('no raw BOAM files under %s - run '
                         'cities/<city>/extract/fetch_tpa_daily.py boam first' % RAW)
    inside = inside_boundary()
    depot_votes = collections.Counter()
    depot_seen = collections.Counter()
    # pass 1 (first file): which depots' stops lie inside the study area
    with open(files[0], encoding='utf-8', errors='replace') as fh:
        rd = csv.DictReader(fh, delimiter='|')
        stop_cache = {}
        for r in rd:
            depot = r.get('DEPOT') or ''
            if not depot:
                continue
            tsn = r.get('TRANSIT_STOP')
            if tsn not in stop_cache:
                try:
                    stop_cache[tsn] = bool(inside(float(r['LATITUDE']), float(r['LONGITUDE'])))
                except (TypeError, ValueError):
                    stop_cache[tsn] = False
            depot_seen[depot] += 1
            if stop_cache[tsn]:
                depot_votes[depot] += 1
    depots = sorted(d for d in depot_seen if depot_votes[d] / depot_seen[d] > 0.5)
    print('depots with most stops inside the study area:', depots)
    agg = collections.Counter()
    cap = collections.defaultdict(lambda: [0.0, 0.0, 0])
    days = set()
    for f in files:
        with open(f, encoding='utf-8', errors='replace') as fh:
            rd = csv.DictReader(fh, delimiter='|')
            for r in rd:
                if (r.get('DEPOT') or '') not in depots:
                    continue
                key = (r['SERVICE_DATE'][:10], r['ROUTE'], r['DIRECTION'], r['SCHD_HOUR_BAND'],
                       r['TRIP_POINT'], r['OCCUPANCY_RANGE'] or 'unknown')
                agg[key] += 1
                c = cap[key]
                try:
                    c[0] += float(r['SEATED_CAPACITY'] or 0)
                    c[1] += float(r['TOTAL_CAPACITY'] or 0)
                    c[2] += 1
                except ValueError:
                    pass
                days.add(key[0])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(['service_date', 'route', 'direction', 'hour_band', 'trip_point',
                    'occupancy_range', 'observations', 'mean_seated_capacity', 'mean_total_capacity'])
        for key in sorted(agg):
            c = cap[key]
            w.writerow(list(key) + [agg[key],
                                    round(c[0] / c[2], 1) if c[2] else '',
                                    round(c[1] / c[2], 1) if c[2] else ''])
    report = dict(files=len(files), days=sorted(days), depots=depots,
                  depot_share_of_stops_inside={d: round(depot_votes[d] / depot_seen[d], 3) for d in depot_seen},
                  rows=len(agg), observations=sum(agg.values()),
                  source='TfNSW Open Data Hub - BOAM (CC-BY 4.0); see data/raw/boam/provenance.json',
                  note='occupancy ranges are the assignment model\'s bands of 20, at stop arrivals; '
                       'a constraint on bus loading, never a target (9.8, 9.13)')
    with open(REPORT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(report, fh, indent=1)
        fh.write('\n')
    print('wrote %s (%d rows, %d observations, %d days)'
          % (_city.rel(OUT), len(agg), sum(agg.values()), len(days)))


if __name__ == '__main__':
    main()
