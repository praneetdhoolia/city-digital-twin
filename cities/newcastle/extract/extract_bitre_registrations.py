#!/usr/bin/env python
"""Registered road vehicles by type for the study area's postcodes (BITRE, #185).

BITRE's Road Vehicles Australia (31 January 2025, CC-BY 3.0 AU) counts
registered vehicles by vehicle type and registered postcode. The study
area's postcodes are found by GEOMETRY - the ABS Postal Area polygons
intersected with the dissolved core LGA boundary, kept where more than half
the postal area's land lies inside - so no postcode is typed anywhere.

Writes data/processed/observed/bitre_registrations_study_area.csv (postcode,
vehicle type, count, the postal area's share inside the study area) and a
report with the motorcycle share of the light fleet, which is the second
anchor for the motorbike carve beside census G62 (B.motorbike.trip_share).
A constraint on the fleet, never a target (DECISIONS.md 9.8, 9.13).
"""
import city as _city
import csv
import json
import os

RAW = _city.path('data/raw/bitre/rva-2025-mvs-vehtype-streg-poareg-rpc.csv')
POA = _city.path('data/raw/boundaries/POA_2021_AUST_GDA2020_SHP.zip')
OUT = _city.path('data/processed/observed/bitre_registrations_study_area.csv')
REPORT = _city.path('data/processed/observed/_bitre_registrations_report.json')
STATE = _city.descriptor()['jurisdiction']['subdivision']
LIGHT = ('Passenger vehicles', 'Light commercial vehicles', 'Motorcycles')


def study_area_postcodes():
    """{postcode: share of its area inside the core study boundary}, share > 0.5."""
    import geopandas as gpd
    lga = gpd.read_file(_city.path('data/processed/zones/zones_LGA.gpkg'))
    if 'zone_tier' in lga.columns:
        lga = lga[lga.zone_tier == 'core']
    crs = _city.crs()
    boundary = lga.to_crs(crs).geometry.union_all()
    poa = gpd.read_file('zip://' + POA).to_crs(crs)
    code_col = next(c for c in poa.columns if c.upper().startswith('POA_CODE'))
    poa = poa[poa.geometry.intersects(boundary)].copy()
    poa['inside'] = poa.geometry.intersection(boundary).area / poa.geometry.area
    return {str(r[code_col]): round(float(r['inside']), 4)
            for _, r in poa.iterrows() if r['inside'] > 0.5}


def main():
    if not os.path.exists(RAW):
        raise SystemExit('no BITRE table at %s - run cities/<city>/extract/fetch_open_data.py' % RAW)
    abbrev = {'New South Wales': 'NSW'}.get(STATE, STATE)
    inside = study_area_postcodes()
    rows = []
    with open(RAW, encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            if r['state_abb'] != abbrev or r['registered_postcode'] not in inside:
                continue
            rows.append(dict(postcode=r['registered_postcode'], vehicle_type=r['vehicle_type'],
                             vehicles=int(r['no_vehicles']),
                             postal_area_share_inside=inside[r['registered_postcode']]))
    rows.sort(key=lambda r: (r['postcode'], r['vehicle_type']))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=['postcode', 'vehicle_type', 'vehicles',
                                           'postal_area_share_inside'], lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    by_type = {}
    for r in rows:
        by_type[r['vehicle_type']] = by_type.get(r['vehicle_type'], 0) + r['vehicles']
    light = sum(by_type.get(t, 0) for t in LIGHT)
    report = dict(
        source='BITRE Road Vehicles Australia, 31 January 2025 (data.gov.au, CC-BY 3.0 AU); '
               'see data/raw/provenance_open_data.json',
        postcodes=len(inside), rows=len(rows), vehicles_by_type=by_type,
        light_fleet=light,
        motorcycle_share_of_light_fleet=round(by_type.get('Motorcycles', 0) / light, 5) if light else None,
        note='postal areas kept where more than half their area lies inside the core LGA boundary; '
             'a registration is where the owner lives, not where the vehicle is used. A constraint '
             'on the fleet beside census G62, never a target (9.8, 9.13).')
    with open(REPORT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(report, fh, indent=1)
        fh.write('\n')
    print('wrote %s: %d postcodes, %d rows; motorcycles %s of a light fleet of %s (%.2f %%)'
          % (_city.rel(OUT), len(inside), len(rows), format(by_type.get('Motorcycles', 0), ','),
             format(light, ','), 100.0 * (report['motorcycle_share_of_light_fleet'] or 0)))


if __name__ == '__main__':
    main()
