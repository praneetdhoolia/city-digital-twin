#!/usr/bin/env python
"""Per-SA1 attraction terms for destination choice, and jobs disaggregated
from the census place-of-work geography down to SA1.

The 2021 Working Population Profile is published at POW SA2. The model needs
job counts at SA1 to build accessibility surfaces at the granularity the
proposal asks for (A4: Hansen accessibility per SA1). Jobs are therefore
disaggregated within each SA2 in proportion to a workplace-weighted POI index,
and the result is flagged source='modelled'.
"""

# City-relative paths resolve through src/city.py: `data/...` names a
# location inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', 'src'))
import city as _city  # noqa: E402
import os
import json
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd

# Model inputs come from cities/<city>/registry/, not from literals here. Every
# value below carries its units, provenance and either a sweep, a held-fixed rule
# or a derived-from identity there. See DECISIONS.md 15.
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import registry as _registry  # noqa: E402
CFG = _registry.load()

warnings.filterwarnings('ignore')

ZON = _city.path('data/processed/zones')
LU = _city.path('data/processed/landuse')
# The census is read through the city's reader adapter (issue #62 A5).
READERS = _city.readers()
OUT = _city.path('data/processed/landuse')

# relative workplace intensity per POI group (jobs per establishment, indicative)
JOB_WEIGHT = CFG.get('D.attraction.job_weight_by_category')
# relative pull for each trip purpose
PURPOSE_WEIGHT = CFG.get('D.attraction.purpose_weight')


def main(out_dir=None):
    global OUT
    OUT = out_dir or OUT
    sa1 = gpd.read_file(os.path.join(ZON, 'zones_SA1.gpkg'))
    sa1['SA1_CODE21'] = sa1['SA1_CODE21'].astype(str)
    poi = pd.read_csv(os.path.join(LU, 'D1_poi.csv'))
    g = gpd.GeoDataFrame(poi, geometry=gpd.points_from_xy(poi.lon, poi.lat), crs='EPSG:4326')
    j = gpd.sjoin(g, sa1[['SA1_CODE21', 'SA2_CODE21', 'geometry']],
                  how='inner', predicate='within')
    print('POI joined to SA1: %d of %d' % (len(j), len(poi)))

    grp = j.groupby(['SA1_CODE21', 'category_group']).size().unstack(fill_value=0)
    for c in JOB_WEIGHT:
        if c not in grp.columns:
            grp[c] = 0
    grp = grp.reset_index()

    base = sa1[['SA1_CODE21', 'SA2_CODE21', 'SA2_NAME21', 'zone_tier', 'area_km2',
                'x_mga56', 'y_mga56', 'lon', 'lat']].copy()
    d = base.merge(grp, on='SA1_CODE21', how='left').fillna(
        {c: 0 for c in JOB_WEIGHT})

    # ---- residential side: population and dwellings per zone, through the
    # city's reader adapter (issue #62 A5, DECISIONS.md 9.140) ----
    res = READERS.residence_counts().rename(columns={'zone_id': 'SA1_CODE21'})
    d = d.merge(res, on='SA1_CODE21', how='left')
    d['population'] = pd.to_numeric(d['population'], errors='coerce').fillna(0).astype(int)
    for c in ['dwellings_total', 'dwellings_occupied']:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors='coerce').fillna(0).astype(int)

    # ---- jobs: place-of-work totals disaggregated to SA1 by workplace POI
    # index; the industry division table is the census's own vocabulary ----
    jobs_sa2, industry, n_ind = READERS.workplace_jobs()
    jobs_sa2 = jobs_sa2.rename(columns={'workplace_zone': 'SA2_CODE21', 'jobs': 'jobs_sa2'})
    if industry is not None:
        emp = industry.reset_index().rename(columns={'workplace_zone': 'SA2_CODE21'})
        emp = emp.merge(jobs_sa2, on='SA2_CODE21', how='left')
        emp['year'] = 2021
        emp.to_csv(os.path.join(OUT, 'D1_employment_by_anzsic_POW_SA2.csv'), index=False)
        print('wrote D1_employment_by_anzsic_POW_SA2.csv: %d SA2 x %d industry columns'
              % (len(emp), n_ind))

    d['job_index'] = sum(d[c] * w for c, w in JOB_WEIGHT.items())
    d['SA2_CODE21'] = d['SA2_CODE21'].astype(str)
    d = d.merge(jobs_sa2, on='SA2_CODE21', how='left')
    d['jobs_sa2'] = d['jobs_sa2'].fillna(0)
    sa2sum = d.groupby('SA2_CODE21')['job_index'].transform('sum')
    # where an SA2 has no POI at all, fall back to population share
    popsum = d.groupby('SA2_CODE21')['population'].transform('sum')
    share = np.where(sa2sum > 0, d['job_index'] / sa2sum.replace(0, np.nan),
                     np.where(popsum > 0, d['population'] / popsum.replace(0, np.nan), 0))
    d['jobs'] = (d['jobs_sa2'] * pd.Series(share).fillna(0)).round(1)
    d['jobs_source'] = 'modelled_from_WPP_SA2'

    # ---- purpose-specific attraction terms ----
    for pur, wts in PURPOSE_WEIGHT.items():
        d['attr_' + pur] = sum(d.get(c, 0) * w for c, w in wts.items())
    # commute attraction is the disaggregated job count, not the POI proxy
    d['attr_HW'] = d['jobs']
    # education uses school/university POIs, floored so residential SA1s can still
    # host primary schools that OSM has not mapped
    d['attr_HE'] = d['attr_HE'] + d['population'] * 0.02

    cols = (['SA1_CODE21', 'SA2_CODE21', 'SA2_NAME21', 'zone_tier', 'area_km2',
             'x_mga56', 'y_mga56', 'lon', 'lat', 'population'] +
            [c for c in ['dwellings_total', 'dwellings_occupied'] if c in d.columns] +
            list(JOB_WEIGHT) + ['job_index', 'jobs_sa2', 'jobs', 'jobs_source'] +
            ['attr_' + p for p in PURPOSE_WEIGHT])
    d[cols].to_csv(os.path.join(OUT, 'D1_zone_attractions_SA1.csv'), index=False)

    rep = dict(sa1_zones=len(d),
               population_total=int(d['population'].sum()),
               population_core=int(d.loc[d.zone_tier == 'core', 'population'].sum()),
               jobs_total=int(d['jobs'].sum()),
               jobs_core=int(d.loc[d.zone_tier == 'core', 'jobs'].sum()),
               jobs_sa2_control_total=int(jobs_sa2['jobs_sa2'].sum()),
               poi_joined=len(j),
               top10_job_sa1=d.nlargest(10, 'jobs')[
                   ['SA1_CODE21', 'SA2_NAME21', 'jobs']].to_dict('records'))
    json.dump(rep, open(os.path.join(OUT, '_attractions_report.json'), 'w', newline='\n'), indent=2)
    print(json.dumps(rep, indent=2)[:2500])


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=None,
                    help='override the landuse output directory (a verification '
                         'build writes beside the canonical one, never over it)')
    main(ap.parse_args().out)
