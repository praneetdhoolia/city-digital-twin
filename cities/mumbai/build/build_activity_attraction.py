"""The attraction of every activity candidate: GHSL built volume around it.

`baseline_activity_locations.csv` lists OSM points and areas that can host a
work, education, shopping, social or leisure activity - locations, not
capacities: every candidate in a distance band drew a worker with the same
probability, so a kiosk attracted as many jobs as a business park. The Global
Human Settlement Layer (JRC, R2023A, epoch 2025, 100 m) measures the built
volume in every cell, total and non-residential; the volume around a
candidate is the observed proxy for what it can hold:

  work                  a mixture: a share 1 - s of the district's jobs in
                        proportion to the NON-RESIDENTIAL built volume
                        (GHS_BUILT_V_NRES_E2025), a share s in proportion to
                        the TOTAL built volume (GHS_BUILT_V_E2025), s the
                        district's own-account share of persons engaged in
                        the Sixth Economic Census (`B.activities.own_account_job_share`:
                        the shop in the home and the street-front trade the
                        non-residential layer does not see)
  education, shopping,  total built volume (GHS_BUILT_V_E2025)
  social, leisure

each summed over the cells within `B.activities.attraction_radius_m` of the
candidate (declared, swept). The builder writes one weight per candidate to
`data/processed/geospatial/activity_location_attraction.csv` (the two volumes
and the mixed work weight, normalised over the candidates of the purpose);
`build_plans.py` draws work destinations within the B-28 distance band in
proportion to the weight (`B.activities.work_attraction` = `ghsl_nres_volume`)
and multiplies the optional purposes' distance decay by it. A candidate with no built volume
within the radius keeps a weight of zero and is drawn only when its whole band
has none (counted in the plans report, never hidden). The 2020 epoch, the
built-surface and building-height layers and GHS_POP are the same product's
components and earlier epoch: not read, superseded by the 2025 volume and by
the census-based population.
"""
import csv
import glob
import json
from pathlib import Path

import numpy as np
import pyogrio
import rasterio
from rasterio.warp import transform

import city
import registry

OUTPUT_INPUTS = {
    'data/processed/geospatial/activity_location_attraction.csv': [
        'data/processed/geospatial/baseline_activity_locations.csv',
        'data/raw/geospatial/ghs_built_v_nres_e2025_*.zip',
        'data/raw/geospatial/ghs_built_v_e2025_*.zip',
        'data/processed/geospatial/census_2011_geographies.gpkg',
        'registry/B_baseline_activities.json',
    ],
    'data/processed/geospatial/_activity_location_attraction_report.json': [
        'data/processed/geospatial/baseline_activity_locations.csv',
        'data/raw/geospatial/ghs_built_v_nres_e2025_*.zip',
        'data/raw/geospatial/ghs_built_v_e2025_*.zip',
        'data/processed/geospatial/census_2011_geographies.gpkg',
        'registry/B_baseline_activities.json',
    ],
}
LAYERS = {'nres': 'data/raw/geospatial/ghs_built_v_nres_e2025_*.zip',
          'total': 'data/raw/geospatial/ghs_built_v_e2025_*.zip'}
PURPOSE_LAYER = {'work': 'nres', 'education': 'total', 'shopping': 'total', 'social': 'total', 'leisure': 'total'}


def open_layer(pattern):
    """The GeoTIFF inside the acquired GHSL zip, and the zip's source id."""
    paths = glob.glob(city.path(pattern))
    if len(paths) != 1:
        raise SystemExit('expected one acquisition for %s, found %d' % (pattern, len(paths)))
    import zipfile
    member = [n for n in zipfile.ZipFile(paths[0]).namelist() if n.endswith('.tif')][0]
    return rasterio.open('zip://%s!%s' % (paths[0], member)), Path(paths[0]).name, member


def volume_around(dataset, xs, ys, radius_m):
    """Built volume (m3) summed over the cells whose centre lies within radius_m
    of each point, the points in the raster's own CRS."""
    band = dataset.read(1)
    nodata = dataset.nodata
    cell = dataset.res[0]
    k = int(np.ceil(radius_m / cell))
    offsets = [(dr, dc) for dr in range(-k, k + 1) for dc in range(-k, k + 1)
               if (dr * cell) ** 2 + (dc * cell) ** 2 <= radius_m ** 2]
    inverse = ~dataset.transform
    cols_f, rows_f = inverse * (np.asarray(xs), np.asarray(ys))
    rows, cols = np.floor(rows_f).astype(int), np.floor(cols_f).astype(int)
    out = np.zeros(len(xs))
    for dr, dc in offsets:
        r, c = rows + dr, cols + dc
        inside = (r >= 0) & (r < band.shape[0]) & (c >= 0) & (c < band.shape[1])
        values = np.zeros(len(xs))
        values[inside] = band[r[inside], c[inside]]
        if nodata is not None:
            values[values == nodata] = 0
        out += values
    return out


def district_of(xs, ys):
    """The Census 2011 district each point falls in, by the leaf polygons
    (the nearest polygon for a point on the water or in a gap)."""
    import shapely
    leaves = pyogrio.read_dataframe(city.path('data/processed/geospatial/census_2011_geographies.gpkg'),
                                    layer='census_leaves', columns=['district_code'])
    leaves = leaves[leaves.geometry.notna() & ~leaves.geometry.is_empty]
    tree = shapely.STRtree(leaves.geometry.values)
    points = shapely.points(np.column_stack([xs, ys]))
    nearest = tree.nearest(points)
    return leaves['district_code'].astype(str).to_numpy()[nearest]


def main():
    cfg = registry.load()
    radius = float(cfg.get('B.activities.attraction_radius_m'))
    own_account = {str(k): float(v) for k, v in cfg.get('B.activities.own_account_job_share').items()}
    crs = 'EPSG:%d' % city.descriptor()['crs']['epsg']
    locations = list(csv.DictReader(open(city.path('data/processed/geospatial/baseline_activity_locations.csv'), encoding='utf-8')))
    xs = [float(r['x_m']) for r in locations]
    ys = [float(r['y_m']) for r in locations]
    weights, sources = {}, {}
    for key, pattern in LAYERS.items():
        dataset, archive, member = open_layer(pattern)
        with dataset:
            rx, ry = transform(crs, dataset.crs, xs, ys)
            weights[key] = volume_around(dataset, np.asarray(rx), np.asarray(ry), radius)
            sources[key] = dict(archive=archive, member=member, crs=str(dataset.crs), cell_m=dataset.res[0])
    districts = district_of(np.asarray(xs), np.asarray(ys))
    purposes = np.array([r['purpose'] for r in locations])
    # the work weight: the two volume distributions, each normalised over the
    # work candidates, mixed by the candidate's district's own-account share
    work = purposes == 'work'
    nres_share = weights['nres'] / max(weights['nres'][work].sum(), 1.0)
    total_share = weights['total'] / max(weights['total'][work].sum(), 1.0)
    s = np.array([own_account[d] for d in districts])
    work_weight = (1.0 - s) * nres_share + s * total_share
    rows = []
    for i, r in enumerate(locations):
        layer = PURPOSE_LAYER[r['purpose']]
        weight = work_weight[i] if layer == 'nres' else weights['total'][i]
        rows.append(dict(location_id=r['location_id'], purpose=r['purpose'], district_code=districts[i],
                         attraction_layer=layer, nres_volume_m3=int(round(weights['nres'][i])),
                         total_volume_m3=int(round(weights['total'][i])),
                         attraction_weight=('%.6g' % weight), radius_m=int(radius), source='derived'))
    out = Path(city.path('data/processed/geospatial/activity_location_attraction.csv'))
    with out.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    report = dict(source='derived', radius_m=radius, own_account_job_share=own_account, layers=sources,
                  candidates=len(rows), candidates_by_district=dict(zip(*np.unique(districts, return_counts=True))))
    report['candidates_by_district'] = {k: int(v) for k, v in report['candidates_by_district'].items()}
    for purpose in sorted(PURPOSE_LAYER):
        sel = purposes == purpose
        if sel.any():
            v = weights['nres' if purpose == 'work' else 'total'][sel]
            w = work_weight[sel] if purpose == 'work' else v
            report[purpose] = dict(candidates=int(sel.sum()), zero_volume=int((v == 0).sum()),
                                   zero_weight=int((w == 0).sum()),
                                   median_m3=float(np.median(v)), p90_m3=float(np.percentile(v, 90)),
                                   max_m3=float(v.max()))
    Path(city.path('data/processed/geospatial/_activity_location_attraction_report.json')).write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('layers',)}, indent=1))


if __name__ == '__main__':
    main()
