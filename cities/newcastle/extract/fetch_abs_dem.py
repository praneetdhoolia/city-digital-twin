#!/usr/bin/env python
"""ABS boundaries + Census DataPacks, and Copernicus DEM tiles."""

import city as _city
from fetch_with_provenance import fetch_all

ABS = "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files/"
DP = "https://www.abs.gov.au/census/find-census-data/datapacks/download/"
COP = "https://copernicus-dem-30m.s3.amazonaws.com/"
M = [
 ("boundaries/SA1_2021_AUST_SHP_GDA2020.zip",ABS+"SA1_2021_AUST_SHP_GDA2020.zip","ABS ASGS Ed3 SA1 2021 digital boundaries","CC-BY 4.0"),
 ("boundaries/SA2_2021_AUST_SHP_GDA2020.zip",ABS+"SA2_2021_AUST_SHP_GDA2020.zip","ABS ASGS Ed3 SA2 2021 digital boundaries","CC-BY 4.0"),
 ("boundaries/SA3_2021_AUST_SHP_GDA2020.zip",ABS+"SA3_2021_AUST_SHP_GDA2020.zip","ABS ASGS Ed3 SA3 2021 digital boundaries","CC-BY 4.0"),
 ("boundaries/DZN_2021_AUST_GDA2020_SHP.zip",ABS+"DZN_2021_AUST_GDA2020_SHP.zip","ABS Destination Zones 2021 (workplace geography)","CC-BY 4.0"),
 ("boundaries/LGA_2021_AUST_GDA2020_SHP.zip",ABS+"LGA_2021_AUST_GDA2020_SHP.zip","ABS LGA 2021 boundaries","CC-BY 4.0"),
 # the postal areas, so a registrations-by-postcode publication (BITRE, #185)
 # can be joined to the study area by geometry rather than by a typed list
 ("boundaries/POA_2021_AUST_GDA2020_SHP.zip",ABS+"POA_2021_AUST_GDA2020_SHP.zip","ABS ASGS Ed3 Postal Areas 2021 digital boundaries","CC-BY 4.0"),
 ("boundaries/MB_2021_NSW_SHP_GDA2020.zip",ABS+"MB_2021_NSW_SHP_GDA2020.zip","ABS Mesh Blocks 2021 NSW","CC-BY 4.0"),
 ("census/2021_GCP_SA1_for_NSW_short-header.zip",DP+"2021_GCP_SA1_for_NSW_short-header.zip","ABS Census 2021 General Community Profile, SA1, NSW","CC-BY 4.0"),
 ("census/2021_GCP_SA2_for_NSW_short-header.zip",DP+"2021_GCP_SA2_for_NSW_short-header.zip","ABS Census 2021 GCP, SA2, NSW","CC-BY 4.0"),
 ("census/2021_PEP_SA2_for_NSW_short-header.zip",DP+"2021_PEP_SA2_for_NSW_short-header.zip","ABS Census 2021 Place of Enumeration Profile, SA2, NSW","CC-BY 4.0"),
 ("census/2021_WPP_DZN_for_NSW_short-header.zip",DP+"2021_WPP_DZN_for_NSW_short-header.zip","ABS Census 2021 Working Population Profile by Destination Zone, NSW (jobs by industry/occupation at workplace)","CC-BY 4.0"),
]


def _dem_licence():
    """The DEM licence as the city DECLARES it (city.json sources), not a
    literal typed here: the record once said 'ESA / open' while the
    descriptor said 'ESA, free and open' (#117)."""
    for s in _city.descriptor().get('sources') or []:
        if 'data/raw/dem' in (s.get('provides') or []):
            return s.get('licence', '')
    return ''


def dem_tiles():
    """Copernicus GLO-30 1-degree cells covering the DERIVED study extent.

    The list used to be typed in with the comment 'study area spans lat
    -32.55..-33.20, lon 151..152' - the same stale-extent class as the issue
    #32 harvest box: when the harvest extent was corrected to the dissolved
    LGA boundary plus A.osm.harvest_margin_m, the road network grew past
    151..152 and 6.5% of edges silently lost their gradient source. The cells
    are now derived from the same boundary + margin the harvest itself uses.
    If the processed boundary does not exist yet the fetch REFUSES and says
    which build comes first (the zones, from the boundary download); a typed
    fallback rectangle stood here until 3 September 2026 and is gone (#118).
    Cold start: run the boundary download, build the zones, then this.
    """
    import math
    try:
        import geopandas as gpd
        import registry as _registry
        margin = _registry.load().get('A.osm.harvest_margin_m')
        lga = gpd.read_file(_city.path('data/processed/zones/zones_LGA.gpkg'))
        if 'zone_tier' in lga.columns:
            lga = lga[lga.zone_tier == 'core']
        w, s, e, n = lga.to_crs(4326).total_bounds
        deg = margin / 111000.0
        s, w, n, e = s - deg, w - deg, n + deg, e + deg
    except Exception as exc:                                   # noqa: BLE001
        raise SystemExit(
            'DEM extent cannot be derived (%s). The cells come from the '
            'dissolved LGA boundary in data/processed/zones/zones_LGA.gpkg '
            'plus A.osm.harvest_margin_m: build the zones first, then re-run. '
            'No typed rectangle stands in for a boundary that is not there '
            '(#118).' % exc)
    cells = []
    for lat0 in range(int(math.floor(s)), int(math.ceil(n))):
        for lon0 in range(int(math.floor(w)), int(math.ceil(e))):
            name = 'Copernicus_DSM_COG_10_S%02d_00_E%03d_00_DEM' % (-lat0, lon0)
            cells.append(('dem/%s.tif' % name, COP + '%s/%s.tif' % (name, name),
                          'Copernicus GLO-30 DEM tile S%02dE%03d (cell derived '
                          'from the dissolved LGA boundary + harvest margin)'
                          % (-lat0, lon0), _dem_licence()))
    return cells


def main():
    # a held file keeps the day it was retrieved; a held file with no earlier
    # record is stamped today, as this fetcher always did
    fetch_all(M + dem_tiles(), _city.path('data/raw'), 'provenance_abs_dem.json',
              min_bytes=1000, timeout=1800, undated='today')


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
