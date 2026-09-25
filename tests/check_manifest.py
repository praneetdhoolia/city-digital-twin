#!/usr/bin/env python
"""Verify committed data files against data/MANIFEST.csv.

Offline, dependency-free counterpart to tests/check_package.py. The bulk of the
package is gitignored (see .gitignore), so a CI checkout holds only a subset of
the manifest; this checks exactly that subset:

  1. every manifest row whose file is present hashes to its recorded sha256 and
     matches its recorded byte count;
  2. every tracked file under data/processed appears in the manifest.

Absent files are reported and skipped, not failed — that is the normal state of a
fresh clone. Run tests/check_package.py locally, against the full package, for the
cross-layer integrity checks that need the bulk data.

Exits non-zero on any mismatch or unmanifested tracked file.
"""
import csv
import hashlib
import os
import subprocess
import sys

import city
from manifest_io import manifest_reader

# Manifest rows are CITY-RELATIVE (`data/processed/...`), so they are resolved
# against the city directory rather than the working directory. The same row in
# two cities' manifests describes the same layer.
MANIFEST = city.path('data', 'MANIFEST.csv')
CITY_REL = os.path.relpath(city.CITY_DIR, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))).replace(os.sep, '/')
CHUNK = 1 << 20


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def norm(path):
    return path.replace(os.sep, '/')


def tracked_files():
    """Tracked files under this city's processed data, as city-relative paths."""
    out = subprocess.run(['git', 'ls-files', '-z', CITY_REL + '/data/processed'],
                         capture_output=True, text=True, check=True).stdout
    prefix = CITY_REL + '/'
    return {norm(p)[len(prefix):] for p in out.split(chr(0)) if p}


# The share-alike licence labels THIS city declares, from the sources it
# marked `share_alike`. Nothing here names a licence, a source or a city.
SHARE_ALIKE = tuple(sorted({
    s['licence'] for s in (city.descriptor().get('sources') or [])
    if s.get('share_alike') and s.get('licence')}))
# What an undetermined row costs. It is a RATCHET, not a target: a row whose
# ancestry the evidence does not decide is an honest outcome, but the number
# may only fall. The cap is the city's, beside its other document rules.
UNDETERMINED_CAP = city.descriptor().get('manifest_undetermined_lineage_max')


def check_lineage_licence(rows):
    """The manifest's two provenance claims must agree, row by row (#159).

    A row states an ancestry (`share_alike_ancestor`, resolved from the
    producing scripts' declared per-output inputs) and a licence (resolved
    from the city's declaration). They are arrived at independently, and
    nothing in this repository compared them until now - so 129 rows named an
    OpenStreetMap ancestor while carrying a CC-BY licence and nobody saw it.

    Both directions are failures. A share-alike ancestor under a permissive
    licence UNDER-restricts, which is a licence breach; a share-alike licence
    with no such ancestor OVER-restricts a file the package is free to
    publish. `undetermined` is neither: the row says the evidence does not
    decide, and it is counted against a ratchet rather than asserted.
    """
    if not SHARE_ALIKE:
        return []
    out, undetermined = [], []
    for row in rows:
        verdict = (row.get('share_alike_ancestor') or '').strip()
        licence = row.get('licence') or ''
        share_alike = any(lic in licence for lic in SHARE_ALIKE)
        if verdict == 'yes' and not share_alike:
            out.append('%s: ancestry is share-alike (%s) but the licence is '
                       '"%s"' % (norm(row['path']), SHARE_ALIKE[0],
                                 licence[:60]))
        elif verdict == 'no' and share_alike:
            out.append('%s: licence is share-alike but no share-alike '
                       'ancestor was found' % norm(row['path']))
        elif verdict == 'undetermined':
            undetermined.append(norm(row['path']))
        elif verdict not in ('yes', 'no'):
            out.append('%s: no share_alike_ancestor verdict - regenerate the '
                       'manifest' % norm(row['path']))
    cap = UNDETERMINED_CAP
    print('lineage/licence: %d row(s) agree, %d undetermined%s'
          % (len(rows) - len(out) - len(undetermined), len(undetermined),
             '' if cap is None else ' (cap %d)' % cap))
    if cap is not None and len(undetermined) > cap:
        producers = sorted({r['produced_by'] for r in rows
                            if norm(r['path']) in set(undetermined)})
        out.append('%d manifest row(s) have an undetermined share-alike '
                   'ancestry, above the declared cap of %d. The producing '
                   'script must declare OUTPUT_INPUTS: %s'
                   % (len(undetermined), cap, ', '.join(producers[:4])))
    return out


# Two provenance holes a row may not carry. A RAW download with no retrieval
# date is an acquisition nobody can date (CLAUDE.md: every acquisition carries
# its retrieval timestamp), and a `lineage_scope` of `none` is a row whose
# ancestry the producing script never declared at any scope, so the licence
# claim beside it rests on nothing.
DATE_AND_SCOPE_RULES = (
    ('raw_without_retrieved',
     lambda row: ((row.get('stage') or '').strip() == 'raw'
                  and not (row.get('retrieved') or '').strip()),
     'raw row(s) carry no retrieval date'),
    ('lineage_scope_none',
     lambda row: (row.get('lineage_scope') or '').strip() == 'none',
     'row(s) carry lineage_scope none'),
)


def _paths(block):
    """One recorded-debt list, one city-relative path per line."""
    return frozenset(line.strip() for line in block.splitlines() if line.strip())


def check_recorded_debt(rows, debt):
    """Refuse the two holes, except the paths recorded as debt - which may only SHRINK.

    `debt` maps a rule name to the exact paths that failed it when the rule
    was introduced. A failing path outside that list is a NEW hole and fails.
    A listed path that no longer fails (its row was fixed, or it left the
    manifest) also fails, so the entry must be deleted and the list can only
    get shorter. Returns (failures, {rule: (failing, allowlisted)}).
    """
    failures, counts = [], {}
    for rule, failing_row, what in DATE_AND_SCOPE_RULES:
        failing = {norm(r['path']) for r in rows if failing_row(r)}
        allowed = set(debt.get(rule, ()))
        new = sorted(failing - allowed)
        fixed = sorted(allowed - failing)
        counts[rule] = (len(failing), len(allowed))
        if new:
            failures.append('%d %s outside the recorded debt: %s%s'
                            % (len(new), what, ', '.join(new[:6]),
                               ' ...' if len(new) > 6 else ''))
        if fixed:
            failures.append('%d path(s) in the recorded %s debt no longer fail '
                            'it - delete them from RECORDED_DEBT in '
                            'tests/check_manifest.py: %s%s'
                            % (len(fixed), rule, ', '.join(fixed[:6]),
                               ' ...' if len(fixed) > 6 else ''))
    return failures, counts


def main():
    if not os.path.exists(MANIFEST):
        print('FAIL  %s not found' % MANIFEST)
        return 1

    checked = absent = unhashed = 0
    failures = []
    manifested = set()
    unlicensed = []
    rows = []

    with open(MANIFEST, encoding='utf-8') as f:
        for row in manifest_reader(f):
            rows.append(row)
            path = norm(row['path'])
            manifested.add(path)
            # every row carries a licence (#117): a blank is a file nobody
            # declared a source for, and the OSM share-alike boundary is
            # invisible when 472 rows say nothing
            if not (row.get('licence') or '').strip():
                unlicensed.append(path)
            full = city.path(path)
            if not os.path.exists(full):
                absent += 1
                continue
            checked += 1
            # build_manifest.py records a sentinel (e.g. `skipped_large`) instead of a
            # digest for files it declined to hash; size is still authoritative there.
            recorded = (row['sha256'] or '').strip()
            if len(recorded) == 64 and all(c in '0123456789abcdef' for c in recorded):
                actual = sha256(full)
                if actual != recorded:
                    failures.append('%s: sha256 %s, manifest says %s'
                                    % (path, actual[:16], recorded[:16]))
                    continue
            else:
                unhashed += 1
            if row['bytes']:
                size = os.path.getsize(full)
                if size != int(row['bytes']):
                    failures.append('%s: %d bytes, manifest says %s'
                                    % (path, size, row['bytes']))

    for path in sorted(tracked_files() - manifested):
        failures.append('%s: tracked but absent from %s' % (path, MANIFEST))

    failures += check_lineage_licence(rows)

    debt_failures, debt_counts = check_recorded_debt(
        rows, RECORDED_DEBT.get(city.CITY, {}))
    for rule, (failing, allowed) in debt_counts.items():
        print('%s: %d row(s) fail, %d recorded as debt'
              % (rule, failing, allowed))
    failures += debt_failures

    print('verified %d present file(s) (%d size-only, no digest recorded); '
          '%d manifest entr(ies) not in this checkout (gitignored bulk data)'
          % (checked, unhashed, absent))
    if unlicensed:
        failures.append('%d manifest row(s) carry no licence: %s%s'
                        % (len(unlicensed), ', '.join(unlicensed[:6]),
                           ' ...' if len(unlicensed) > 6 else ''))
    for line in failures:
        print('FAIL  ' + line)
    if failures:
        print('\n%d failure(s)' % len(failures))
        return 1
    print('OK')
    return 0


# RECORDED DEBT, keyed by the city's id (`city.CITY`), measured 25 September
# 2026 against each city's committed MANIFEST.csv. These are the exact paths
# that failed a rule in DATE_AND_SCOPE_RULES when it was introduced. It may
# only SHRINK: check_recorded_debt() fails on a path outside it and on a
# listed path that has been fixed. Never add a path here - fix the row (its
# provenance record's retrieval date, or its producer's declared lineage) and
# delete the line. A city with no entry carries no debt.
RECORDED_DEBT = {
    'mumbai': {
        'raw_without_retrieved': _paths('''
data/raw/_acquisition_attempts.json
data/raw/boundaries/provenance_iitb_boundary_downloads.json
data/raw/boundaries/provenance_iitb_boundary_mumbai_city.json
data/raw/boundaries/provenance_iitb_boundary_mumbai_suburban.json
data/raw/boundaries/provenance_iitb_boundary_palghar.json
data/raw/boundaries/provenance_iitb_boundary_raigad.json
data/raw/boundaries/provenance_iitb_boundary_thane.json
data/raw/boundaries/provenance_iitb_census_attributes.json
data/raw/boundaries/provenance_iitb_census_downloads.json
data/raw/boundaries/provenance_iitb_census_map_index.json
data/raw/boundaries/provenance_iitb_census_missing_geometry.json
data/raw/boundaries/provenance_iitb_census_mumbaicity.json
data/raw/boundaries/provenance_iitb_census_palghar.json
data/raw/boundaries/provenance_iitb_census_raigad.json
data/raw/boundaries/provenance_iitb_census_thane.json
data/raw/boundaries/provenance_maharashtra_scheduled_areas_order_1985.json
data/raw/boundaries/provenance_maharashtra_scheduled_areas_statistical_index.json
data/raw/boundaries/provenance_maharashtra_scheduled_areas_statistical_index_archived_20260414.json
data/raw/boundaries/provenance_maharashtra_tribal_administration_2017_18.json
data/raw/boundaries/provenance_mmr_boundary_2019.json
data/raw/boundaries/provenance_mmr_ena_palghar_plan_notice_20250918.json
data/raw/boundaries/provenance_mmr_ena_raigad_plan_notice_20250918.json
data/raw/boundaries/provenance_mmr_ena_spa_notification_20240709.json
data/raw/boundaries/provenance_mmr_extended_notified_area_documents.json
data/raw/boundaries/provenance_mmr_extended_notified_area_index.json
data/raw/boundaries/provenance_mmr_gis_page.json
data/raw/boundaries/provenance_mmr_official_map_2025_11.json
data/raw/boundaries/provenance_mmrda_gis_index.json
data/raw/boundaries/provenance_mmrena_overview.json
data/raw/boundaries/provenance_mmrena_raigad_notice_20250918.json
data/raw/boundaries/provenance_palghar_zp_administrative_setup.json
data/raw/boundaries/provenance_wri_mmr_item.json
data/raw/boundaries/provenance_wri_mmr_layer_0_features.json
data/raw/boundaries/provenance_wri_mmr_layer_0_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_0_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_1_features.json
data/raw/boundaries/provenance_wri_mmr_layer_1_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_1_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_2_features.json
data/raw/boundaries/provenance_wri_mmr_layer_2_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_2_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_3_features.json
data/raw/boundaries/provenance_wri_mmr_layer_3_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_3_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_4_features.json
data/raw/boundaries/provenance_wri_mmr_layer_4_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_4_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_5_features.json
data/raw/boundaries/provenance_wri_mmr_layer_5_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_5_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_6_features.json
data/raw/boundaries/provenance_wri_mmr_layer_6_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_6_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_7_features.json
data/raw/boundaries/provenance_wri_mmr_layer_7_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_7_metadata.json
data/raw/boundaries/provenance_wri_mmr_layer_8_features.json
data/raw/boundaries/provenance_wri_mmr_layer_8_ids.json
data/raw/boundaries/provenance_wri_mmr_layer_8_metadata.json
data/raw/boundaries/provenance_wri_mmr_service.json
data/raw/calendar/provenance_cr_wall_calendar_2026_cag.json
data/raw/calendar/provenance_maha_public_holidays_2026.json
data/raw/demand/provenance_census_b28_index.json
data/raw/demand/provenance_census_b28_india.json
data/raw/demand/provenance_census_b28_maharashtra.json
data/raw/demand/provenance_census_b28_maharashtra_index.json
data/raw/demand/provenance_census_b28_search.json
data/raw/demand/provenance_mrvc_gender_tiss_study.json
data/raw/demand/provenance_mumbai_cmp_summary.json
data/raw/demand/provenance_nhts_2025_26_instructions.json
data/raw/demand/provenance_nhts_2025_26_schedule.json
data/raw/demand/provenance_tus_2024_access.json
data/raw/demand/provenance_tus_2024_catalogue.json
data/raw/demand/provenance_tus_2024_codes.json
data/raw/demand/provenance_tus_2024_data_layout.json
data/raw/demand/provenance_tus_2024_instructions.json
data/raw/demand/provenance_tus_2024_materials.json
data/raw/demand/provenance_tus_2024_metadata.json
data/raw/demand/provenance_tus_2024_nmds.json
data/raw/demand/provenance_tus_2024_readme.json
data/raw/demand/provenance_tus_2024_report.json
data/raw/demand/provenance_tus_2024_sample_design.json
data/raw/demand/provenance_tus_2024_user_note.json
data/raw/demand/provenance_tus_2024_volume_ii.json
data/raw/education/provenance_mospi_aishe_2021-22_maharashtra_indicator_1_page_1.json
data/raw/education/provenance_mospi_aishe_2021-22_maharashtra_indicator_2_page_1.json
data/raw/education/provenance_mospi_aishe_2021-22_maharashtra_indicator_3_page_1.json
data/raw/education/provenance_mospi_aishe_2021-22_maharashtra_indicator_9_page_1.json
data/raw/education/provenance_mospi_udise_2024-25_maharashtra_indicator_1_page_1.json
data/raw/education/provenance_mospi_udise_2024-25_maharashtra_indicator_28_page_1.json
data/raw/education/provenance_mospi_udise_2024-25_maharashtra_indicator_2_page_1.json
data/raw/education/provenance_mospi_udise_2024-25_maharashtra_indicator_3_page_1.json
data/raw/employment/provenance_ec_2013_catalogue.json
data/raw/employment/provenance_ec_2013_district_codes.json
data/raw/employment/provenance_ec_2013_instructions.json
data/raw/employment/provenance_ec_2013_materials.json
data/raw/employment/provenance_ec_2013_nic_codes.json
data/raw/employment/provenance_ec_2013_report.json
data/raw/employment/provenance_maharashtra_ec6_final.json
data/raw/employment/provenance_maharashtra_ec6_provisional.json
data/raw/employment/provenance_maharashtra_economic_census_reports.json
data/raw/employment/provenance_mospi_aishe_api_spec_92a5af0.json
data/raw/employment/provenance_mospi_aishe_filters_1.json
data/raw/employment/provenance_mospi_aishe_filters_2.json
data/raw/employment/provenance_mospi_aishe_filters_3.json
data/raw/employment/provenance_mospi_aishe_filters_9.json
data/raw/employment/provenance_mospi_aishe_indicators.json
data/raw/employment/provenance_mospi_client_92a5af0.json
data/raw/employment/provenance_mospi_ec6_maharashtra_detail_page_1.json
data/raw/employment/provenance_mospi_ec_api_spec_92a5af0.json
data/raw/employment/provenance_mospi_mcp_catalogue_archived_20260511.json
data/raw/employment/provenance_mospi_readme_92a5af0.json
data/raw/employment/provenance_mospi_tus_api_spec_92a5af0.json
data/raw/employment/provenance_mospi_tus_filters_37.json
data/raw/employment/provenance_mospi_tus_filters_38.json
data/raw/employment/provenance_mospi_tus_filters_4.json
data/raw/employment/provenance_mospi_tus_filters_41.json
data/raw/employment/provenance_mospi_tus_filters_42.json
data/raw/employment/provenance_mospi_tus_filters_5.json
data/raw/employment/provenance_mospi_tus_filters_8.json
data/raw/employment/provenance_mospi_tus_indicators.json
data/raw/employment/provenance_mospi_udise_api_spec_92a5af0.json
data/raw/employment/provenance_mospi_udise_filters_1.json
data/raw/employment/provenance_mospi_udise_filters_2.json
data/raw/employment/provenance_mospi_udise_filters_28.json
data/raw/employment/provenance_mospi_udise_filters_3.json
data/raw/employment/provenance_mospi_udise_indicators.json
data/raw/environment/provenance_mmr_environment.json
data/raw/fares/provenance_mmmocl_fare_products_archived_20250610.json
data/raw/fares/provenance_mmr_auto_tariff_20260901.json
data/raw/fares/provenance_mmr_metered_taxi_tariff_20260901.json
data/raw/fares/provenance_mmr_tariff_index_20260918.json
data/raw/freight/provenance_jnpa_administration_2024_25.json
data/raw/freight/provenance_jnpa_administration_2024_25_index.json
data/raw/freight/provenance_jnpa_aug_2026_commodities.json
data/raw/freight/provenance_jnpa_aug_2026_terminal_teus.json
data/raw/freight/provenance_jnpa_central_parking_20260918.json
data/raw/freight/provenance_jnpa_daily_icd_20260317.json
data/raw/freight/provenance_jnpa_daily_icd_20260917.json
data/raw/freight/provenance_jnpa_daily_index_20260918.json
data/raw/freight/provenance_jnpa_daily_status_20260917.json
data/raw/freight/provenance_jnpa_dfc_first_long_haul_20260821.json
data/raw/freight/provenance_jnpa_operating_profile_20260918.json
data/raw/freight/provenance_jnpa_operations.json
data/raw/freight/provenance_jnpa_performance_202608.json
data/raw/freight/provenance_jnpa_press_index_20260918.json
data/raw/freight/provenance_mumbai_port_administration_2024_25.json
data/raw/freight/provenance_mumbai_port_annual_index.json
data/raw/freight/provenance_mumbai_port_rail_statistics.json
data/raw/freight/provenance_mumbai_port_rail_traffic_index_20260918.json
data/raw/freight/provenance_ports_statistics_2024_25.json
data/raw/geospatial/provenance_cop_dem_product.json
data/raw/geospatial/provenance_cop_dem_readme.json
data/raw/geospatial/provenance_cop_dem_tile_list.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n17_00_e073_00_dem.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n18_00_e072_00_dem.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n18_00_e073_00_dem.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n19_00_e072_00_dem.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n19_00_e073_00_dem.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n20_00_e072_00_dem.json
data/raw/geospatial/provenance_copernicus_dsm_cog_10_n20_00_e073_00_dem.json
data/raw/geospatial/provenance_ghs_built_h_agbh_e2018_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_h_anbh_e2018_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_s_e2020_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_s_e2025_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_s_nres_e2020_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_s_nres_e2025_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_v_e2020_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_v_e2025_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_v_nres_e2020_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_built_v_nres_e2025_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_pop_e2020_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghs_pop_e2025_globe_r2023a_54009_100_v1_0_r7_c26.json
data/raw/geospatial/provenance_ghsl_download_page.json
data/raw/geospatial/provenance_ghsl_licence.json
data/raw/geospatial/provenance_ghsl_methodology_2023.json
data/raw/geospatial/provenance_ghsl_tile_grid.json
data/raw/metro/provenance_metro1_faq.json
data/raw/metro/provenance_metro1_schedule.json
data/raw/metro/provenance_metro_timetable_april2026.json
data/raw/metro/provenance_metro_timetable_april2026_index.json
data/raw/osm/provenance_osm_western_zone_20260915.json
data/raw/osm/provenance_osm_western_zone_index.json
data/raw/planning/provenance_bmc_climate_budget_2025_26_archived_20250808.json
data/raw/planning/provenance_bmc_climate_budget_2025_26_opencity_copy.json
data/raw/planning/provenance_bmc_climate_portal_20260919_archived_20260510.json
data/raw/planning/provenance_bmc_cmp_coastal_annexure_2017_archived_20221010.json
data/raw/planning/provenance_bmc_yearbook_2025.json
data/raw/planning/provenance_cts_2021_mirror.json
data/raw/planning/provenance_jica_metro11_2026.json
data/raw/planning/provenance_maharashtra_infrastructure_2023_archived_20251209.json
data/raw/planning/provenance_mmr_cts_index.json
data/raw/planning/provenance_mmr_historical_regional_plan_1996_2011.json
data/raw/planning/provenance_mmr_ntda_notice_20240304.json
data/raw/planning/provenance_mmr_plan_2016_36.json
data/raw/planning/provenance_mmr_plan_map_index.json
data/raw/planning/provenance_mmr_plan_sanction_20210420.json
data/raw/planning/provenance_mmr_proposed_landuse_overview.json
data/raw/planning/provenance_mmr_ref_landuse_overview.json
data/raw/planning/provenance_mmr_regional_plan_index.json
data/raw/planning/provenance_mmrda_2024.json
data/raw/planning/provenance_opencity_mumbai_parking_lots_kml.json
data/raw/population/provenance_bmc_civic_diary_2025.json
data/raw/population/provenance_bmc_civic_diary_2026.json
data/raw/population/provenance_bmc_environment_report_2024_25.json
data/raw/population/provenance_census_b01_maharashtra.json
data/raw/population/provenance_census_b01_maharashtra_index.json
data/raw/population/provenance_census_b01_maharashtra_search.json
data/raw/population/provenance_census_c12_maharashtra.json
data/raw/population/provenance_census_c12_maharashtra_index.json
data/raw/population/provenance_census_c12_maharashtra_search.json
data/raw/population/provenance_census_c13_maharashtra.json
data/raw/population/provenance_census_c13_maharashtra_index.json
data/raw/population/provenance_census_c13_maharashtra_search.json
data/raw/population/provenance_census_c14_maharashtra.json
data/raw/population/provenance_census_c14_maharashtra_index.json
data/raw/population/provenance_census_c14_maharashtra_search.json
data/raw/population/provenance_census_hh1_cities_maharashtra.json
data/raw/population/provenance_census_hh1_cities_maharashtra_index.json
data/raw/population/provenance_census_hh1_maharashtra.json
data/raw/population/provenance_census_hh1_maharashtra_index.json
data/raw/population/provenance_census_hl12_suburban_search.json
data/raw/population/provenance_census_hl14_city.json
data/raw/population/provenance_census_hl14_city_index.json
data/raw/population/provenance_census_hl14_raigad.json
data/raw/population/provenance_census_hl14_raigad_index.json
data/raw/population/provenance_census_hl14_raigad_search.json
data/raw/population/provenance_census_hl14_suburban.json
data/raw/population/provenance_census_hl14_suburban_index.json
data/raw/population/provenance_census_hl14_thane.json
data/raw/population/provenance_census_hl14_thane_index.json
data/raw/population/provenance_census_hl14_thane_search.json
data/raw/population/provenance_census_maharashtra_towns.json
data/raw/population/provenance_census_maharashtra_villages.json
data/raw/population/provenance_census_mumbai_pca.json
data/raw/population/provenance_census_mumbai_pca_index.json
data/raw/population/provenance_census_mumbai_pca_search.json
data/raw/population/provenance_census_raigarh_pca.json
data/raw/population/provenance_census_raigarh_pca_index.json
data/raw/population/provenance_census_raigarh_pca_search.json
data/raw/population/provenance_census_suburban_handbook.json
data/raw/population/provenance_census_suburban_handbook_index.json
data/raw/population/provenance_census_suburban_pca.json
data/raw/population/provenance_census_suburban_pca_index.json
data/raw/population/provenance_census_thane_pca.json
data/raw/population/provenance_census_thane_pca_index.json
data/raw/population/provenance_census_thane_pca_search.json
data/raw/population/provenance_des_district_mumbai_suburban_archived_20191230.json
data/raw/population/provenance_des_district_palghar_archived_20260418.json
data/raw/population/provenance_des_district_raigad_archived_20240819.json
data/raw/population/provenance_des_district_thane_archived_20260418.json
data/raw/population/provenance_district_review_2025_mumbai_city.json
data/raw/population/provenance_district_review_2025_mumbai_suburban.json
data/raw/population/provenance_district_review_2025_palghar.json
data/raw/population/provenance_district_review_2025_raigad.json
data/raw/population/provenance_district_review_2025_thane.json
data/raw/population/provenance_iips_district_projections_2012_2031.json
data/raw/population/provenance_iips_district_projections_index.json
data/raw/population/provenance_konkan_statistics_index.json
data/raw/population/provenance_maha_economic_highlights_2025_26.json
data/raw/population/provenance_maha_economic_survey_2025_26.json
data/raw/population/provenance_maha_economic_survey_index_2026.json
data/raw/population/provenance_maha_economic_survey_index_2026_en.json
data/raw/population/provenance_mmr_population_employment.json
data/raw/population/provenance_mohfw_population_projections_2011_2036_archived_20251213.json
data/raw/population/provenance_mumbai_city_census_handbook.json
data/raw/population/provenance_mumbai_city_census_index.json
data/raw/population/provenance_mumbai_suburban_census_index.json
data/raw/population/provenance_mumbai_suburban_census_summary.json
data/raw/population/provenance_nfhs4_maharashtra_report_2015_16.json
data/raw/population/provenance_nfhs5_maharashtra_report_2019_21.json
data/raw/population/provenance_nhm_population_projection_2019.json
data/raw/population/provenance_nhm_population_projections_2011_2036.json
data/raw/rail/provenance_central_railway_timetable_index.json
data/raw/rail/provenance_central_railway_timetable_root.json
data/raw/rail/provenance_cr_line_capacity_page.json
data/raw/rail/provenance_cr_mumbai_carsheds_page.json
data/raw/rail/provenance_cr_mumbai_signal_telecom_page.json
data/raw/rail/provenance_cr_mumbai_signal_telecom_page_archived_20230819.json
data/raw/rail/provenance_cr_signalling_assets_chart_20260514.json
data/raw/rail/provenance_cr_signalling_assets_page.json
data/raw/rail/provenance_cr_suburban_operations_page.json
data/raw/rail/provenance_cr_suburban_operations_page_archived_20240424.json
data/raw/rail/provenance_cr_system_map_2019.json
data/raw/rail/provenance_cr_system_map_2019_archived_20240629.json
data/raw/rail/provenance_cr_timetable_20260918_index.json
data/raw/rail/provenance_cr_timetable_20260918_index_archived_20240710.json
data/raw/rail/provenance_irimee_emu_basics.json
data/raw/rail/provenance_mrvc_annual_2023_24.json
data/raw/rail/provenance_mrvc_cbtc_terms_reference_2018.json
data/raw/rail/provenance_mrvc_csmt_panvel_fast_dpr_summary_2016.json
data/raw/rail/provenance_mrvc_trespass_midsection_executive_summary.json
data/raw/rail/provenance_mrvc_trespass_midsection_executive_summary_archived_20240525.json
data/raw/rail/provenance_pib_first_ac_emu_2017.json
data/raw/rail/provenance_pib_mumbai_rail_capacity_projects_20260325.json
data/raw/rail/provenance_pib_suburban_services_20260402.json
data/raw/rail/provenance_rdso_emu_memu_spec_2022.json
data/raw/rail/provenance_rdso_harbour_emu_draft_spec_2014.json
data/raw/rail/provenance_rdso_mrvc3_emu_spec_2017.json
data/raw/rail/provenance_rdso_mrvc3_emu_spec_2017_archived_20240709.json
data/raw/rail/provenance_western_railway_timetable_index.json
data/raw/rail/provenance_wr_bct_disaster_plan_part1_2025.json
data/raw/rail/provenance_wr_disaster_plan_part2_2025.json
data/raw/rail/provenance_wr_public_timetable_attachment_1.json
data/raw/rail/provenance_wr_public_timetable_attachment_2.json
data/raw/rail/provenance_wr_public_timetable_attachment_3.json
data/raw/rail/provenance_wr_public_timetable_attachment_4.json
data/raw/rail/provenance_wr_public_timetable_attachment_5.json
data/raw/rail/provenance_wr_public_timetable_attachment_6.json
data/raw/rail/provenance_wr_timetable_20260901_index.json
data/raw/research/provenance_crri_indo_hcm_snippets.json
data/raw/research/provenance_osm_wiki_access_20260919.json
data/raw/research/provenance_osm_wiki_motorcar_20260919.json
data/raw/research/provenance_osm_wiki_oneway_20260919.json
data/raw/research/provenance_osm_wiki_psv_20260919.json
data/raw/research/provenance_osm_wiki_restriction_20260919.json
data/raw/research/provenance_suri_cropper_mumbai_2024.json
data/raw/research/provenance_urban_arterial_operating_speed_capacity_2017_html.json
data/raw/research/provenance_urban_arterial_operating_speed_capacity_2017_pdf.json
data/raw/research/provenance_worldbank_mumbai_gender_transport_2021.json
data/raw/research/provenance_worldbank_mumbai_poverty_transport_2005.json
data/raw/roads/provenance_atal_setu_ev_toll_notification_20250821.json
data/raw/roads/provenance_atal_setu_faq_20240315.json
data/raw/roads/provenance_maharashtra_taxi_auto_committee_part1.json
data/raw/roads/provenance_maharashtra_taxi_auto_committee_part2.json
data/raw/roads/provenance_maharashtra_taxi_auto_committee_part3.json
data/raw/roads/provenance_mtp_notifications_20260101_20260918.json
data/raw/roads/provenance_mtp_notifications_20260918.json
data/raw/roads/provenance_mtp_road_safety_2023.json
data/raw/roads/provenance_mtp_traffic_notices_20260101_20260918.json
data/raw/roads/provenance_mumbai_road_safety_2020.json
data/raw/roads/provenance_mumbai_road_safety_2021.json
data/raw/roads/provenance_mumbai_road_safety_2022.json
data/raw/roads/provenance_mumbai_road_safety_2023.json
data/raw/roads/provenance_mumbai_traffic_annual_index.json
data/raw/roads/provenance_osm_relation_11179935_history_20260919.json
data/raw/roads/provenance_osm_relation_11179941_history_20260919.json
data/raw/roads/provenance_osm_relation_11179942_history_20260919.json
data/raw/roads/provenance_osm_relation_13445818_history_20260919.json
data/raw/roads/provenance_osm_relation_15518938_history_20260919.json
data/raw/roads/provenance_osm_relation_15518975_history_20260919.json
data/raw/roads/provenance_osm_relation_15519081_history_20260919.json
data/raw/roads/provenance_osm_relation_16357332_history_20260919.json
data/raw/roads/provenance_osm_relation_17889178_history_20260919.json
data/raw/roads/provenance_osm_relation_17915360_history_20260919.json
data/raw/roads/provenance_osm_relation_17934702_history_20260919.json
data/raw/roads/provenance_osm_relation_19344103_history_20260919.json
data/raw/roads/provenance_osm_relation_20594805_history_20260919.json
data/raw/roads/provenance_vm_lal_committee_report_2000.json
data/raw/traffic/provenance_bmc_coastal_traffic_peer_review_2016.json
data/raw/traffic/provenance_bmc_signal_upgrade_spec_2021.json
data/raw/traffic/provenance_crri_indohcm_index.json
data/raw/traffic/provenance_jvlr_conference_poster_2026_response.json
data/raw/traffic/provenance_jvlr_traffic_study_2026_pdf.json
data/raw/traffic/provenance_mmrda_thane_borivali_tunnel_dpr.json
data/raw/traffic/provenance_mpcb_mumbai_emissions_source_apportionment_2023.json
data/raw/traffic/provenance_mumbai_road_capacity_study_2016_archived_20220505.json
data/raw/traffic/provenance_shakti_traffic_signal_operations_2016.json
data/raw/transit/provenance_alstom_metro3_opening_2024.json
data/raw/transit/provenance_best_budget_manual_2021.json
data/raw/transit/provenance_best_bus_pass_2025.json
data/raw/transit/provenance_best_depots_20260919.json
data/raw/transit/provenance_best_disaster_plan_2022_23.json
data/raw/transit/provenance_best_facilities_20260919.json
data/raw/transit/provenance_best_faq_20260919.json
data/raw/transit/provenance_best_home_20260919.json
data/raw/transit/provenance_best_landmarks_20260919.json
data/raw/transit/provenance_best_mmr_connect_20260919.json
data/raw/transit/provenance_best_mutp_20260919.json
data/raw/transit/provenance_best_reservation_20260919.json
data/raw/transit/provenance_best_route_network_20260919_archived_20250126.json
data/raw/transit/provenance_best_rti_publication_index_20260919.json
data/raw/transit/provenance_best_schemes_20260919.json
data/raw/transit/provenance_best_traffic_manual_2021.json
data/raw/transit/provenance_best_transport_20260919.json
data/raw/transit/provenance_best_transport_engineering_manual.json
data/raw/transit/provenance_bmc_best_public_map.json
data/raw/transit/provenance_bus_gtfs_20260918.json
data/raw/transit/provenance_bus_gtfs_licence.json
data/raw/transit/provenance_bus_gtfs_readme.json
data/raw/transit/provenance_cidco_media_20260918.json
data/raw/transit/provenance_cidco_metro_home.json
data/raw/transit/provenance_cidco_metro_project.json
data/raw/transit/provenance_cidco_metro_qr_ticketing_20250617.json
data/raw/transit/provenance_cidco_navi_naina_transport_plan_20250731.json
data/raw/transit/provenance_cidco_press_releases_20260918.json
data/raw/transit/provenance_cidco_smart_travel_notice_20260918.json
data/raw/transit/provenance_cr_public_abbreviations.json
data/raw/transit/provenance_cr_public_harbour_ac_20260501.json
data/raw/transit/provenance_cr_public_harbour_down_20260501.json
data/raw/transit/provenance_cr_public_harbour_up_20260501.json
data/raw/transit/provenance_cr_public_holidays_2026.json
data/raw/transit/provenance_cr_public_main_15_car_20260815.json
data/raw/transit/provenance_cr_public_main_ac_20250416.json
data/raw/transit/provenance_cr_public_main_down_2024.json
data/raw/transit/provenance_cr_public_main_up_2024.json
data/raw/transit/provenance_cr_public_port_line_20251215.json
data/raw/transit/provenance_cr_public_services_20250113.json
data/raw/transit/provenance_cr_public_trans_harbour_20240113.json
data/raw/transit/provenance_cr_transharbour_named_reference_2021.json
data/raw/transit/provenance_mahametro_annual_2024_25.json
data/raw/transit/provenance_mahametro_annual_directory_20260918.json
data/raw/transit/provenance_mahametro_annual_index_20260918.json
data/raw/transit/provenance_mahametro_current_annual_2023_24.json
data/raw/transit/provenance_mahametro_current_annual_2024_25.json
data/raw/transit/provenance_mahametro_public_site_bundle_20260918.json
data/raw/transit/provenance_mbmt_budget_2024_25.json
data/raw/transit/provenance_mbmt_bus_maintenance_agreement.json
data/raw/transit/provenance_mbmt_diesel_bus_work_order.json
data/raw/transit/provenance_mbmt_electric_bus_agreement.json
data/raw/transit/provenance_mbmt_operator_profile.json
data/raw/transit/provenance_mbmt_public_map_script.json
data/raw/transit/provenance_mbmt_route_alignments.json
data/raw/transit/provenance_mbmt_route_details.json
data/raw/transit/provenance_mbmt_route_stops.json
data/raw/transit/provenance_mbmt_routes.json
data/raw/transit/provenance_mbmt_routes_page.json
data/raw/transit/provenance_mbmt_service_notice_20240314.json
data/raw/transit/provenance_mbmt_stops.json
data/raw/transit/provenance_mbmt_ticket_monitoring_agreement.json
data/raw/transit/provenance_mbmt_timing_page.json
data/raw/transit/provenance_mbmt_unique_routes.json
data/raw/transit/provenance_metro1_fare_chart_20260918.json
data/raw/transit/provenance_metro1_fare_products_card_20260918.json
data/raw/transit/provenance_metro1_metro_faq_20260918.json
data/raw/transit/provenance_metro1_metro_train_schedule_20260918.json
data/raw/transit/provenance_metro1_performance_20260918.json
data/raw/transit/provenance_metro1_performance_chart_20260918.json
data/raw/transit/provenance_metro1_ticket_fares_20260918.json
data/raw/transit/provenance_metro3_fare_chart_20260918.json
data/raw/transit/provenance_metro_lastmile_20260319.json
data/raw/transit/provenance_mmmocl_fares_20260918.json
data/raw/transit/provenance_mmmocl_fares_20260918_archived_20250713.json
data/raw/transit/provenance_mmmocl_press_73.json
data/raw/transit/provenance_mmmocl_ridership_20260918.json
data/raw/transit/provenance_mmmocl_schedule_20260918.json
data/raw/transit/provenance_mmmocl_schedule_20260918_archived_20250917.json
data/raw/transit/provenance_mmopl_features_page.json
data/raw/transit/provenance_mmr_line9_sept_2026_block.json
data/raw/transit/provenance_mmr_line9_sept_2026_block_index.json
data/raw/transit/provenance_mmr_metro_april_2026_timetable.json
data/raw/transit/provenance_mmr_metro_april_2026_timetable_index.json
data/raw/transit/provenance_mmr_metro_dpr_10_metro_line_10_gaimukh_to_shivaji_chowk.json
data/raw/transit/provenance_mmr_metro_dpr_11_metro_line_11_wadala_to_cstm_download.json
data/raw/transit/provenance_mmr_metro_dpr_12_metro_line_12_kalyan_to_taloja_download.json
data/raw/transit/provenance_mmr_metro_dpr_1_metro_line_1.json
data/raw/transit/provenance_mmr_metro_dpr_2_metro_line_2a.json
data/raw/transit/provenance_mmr_metro_dpr_3_metro_line_2b.json
data/raw/transit/provenance_mmr_metro_dpr_4_metro_line_4.json
data/raw/transit/provenance_mmr_metro_dpr_5_metro_line_4_a_extension_of_line_4_from_kasarvadavali_to_gaimukh_download.json
data/raw/transit/provenance_mmr_metro_dpr_6_metro_line_5.json
data/raw/transit/provenance_mmr_metro_dpr_7_metro_line_6.json
data/raw/transit/provenance_mmr_metro_dpr_8_metro_line_7.json
data/raw/transit/provenance_mmr_metro_dpr_9_metro_line_7a_9_andheri.json
data/raw/transit/provenance_mmr_metro_dpr_index.json
data/raw/transit/provenance_mmrcl_all_stations.json
data/raw/transit/provenance_mmrcl_faq_product.json
data/raw/transit/provenance_mmrcl_faq_rules.json
data/raw/transit/provenance_mmrcl_faq_safety.json
data/raw/transit/provenance_mmrcl_faq_stations.json
data/raw/transit/provenance_mmrcl_faq_trains.json
data/raw/transit/provenance_mmrcl_fare_aryj_cup_20260918.json
data/raw/transit/provenance_mmrcl_fare_mnk_scmu_20260918.json
data/raw/transit/provenance_mmrcl_fare_scmu_mnk_20260918.json
data/raw/transit/provenance_mmrcl_journey_aca_scmu_20260918.json
data/raw/transit/provenance_mmrcl_journey_aryj_cup_20260918.json
data/raw/transit/provenance_mmrcl_journey_aryj_sepz_20260918.json
data/raw/transit/provenance_mmrcl_journey_bdrm_dhav_20260918.json
data/raw/transit/provenance_mmrcl_journey_chgm_vidb_20260918.json
data/raw/transit/provenance_mmrcl_journey_ciad_stzm_20260918.json
data/raw/transit/provenance_mmrcl_journey_csia_shrr_20260918.json
data/raw/transit/provenance_mmrcl_journey_cstm_huc_20260918.json
data/raw/transit/provenance_mmrcl_journey_cup_aryj_20260918.json
data/raw/transit/provenance_mmrcl_journey_ddrm_sidv_20260918.json
data/raw/transit/provenance_mmrcl_journey_dhav_sdit_20260918.json
data/raw/transit/provenance_mmrcl_journey_girg_klbd_20260918.json
data/raw/transit/provenance_mmrcl_journey_gtrm_girg_20260918.json
data/raw/transit/provenance_mmrcl_journey_huc_chgm_20260918.json
data/raw/transit/provenance_mmrcl_journey_klbd_cstm_20260918.json
data/raw/transit/provenance_mmrcl_journey_mclm_gtrm_20260918.json
data/raw/transit/provenance_mmrcl_journey_midc_mnk_20260918.json
data/raw/transit/provenance_mmrcl_journey_mlxm_mclm_20260918.json
data/raw/transit/provenance_mmrcl_journey_mnk_csia_20260918.json
data/raw/transit/provenance_mmrcl_journey_scmu_mlxm_20260918.json
data/raw/transit/provenance_mmrcl_journey_sdit_ddrm_20260918.json
data/raw/transit/provenance_mmrcl_journey_sepz_midc_20260918.json
data/raw/transit/provenance_mmrcl_journey_shrr_ciad_20260918.json
data/raw/transit/provenance_mmrcl_journey_sidv_wor_20260918.json
data/raw/transit/provenance_mmrcl_journey_stzm_vidn_20260918.json
data/raw/transit/provenance_mmrcl_journey_vidb_cup_20260918.json
data/raw/transit/provenance_mmrcl_journey_vidn_bdrm_20260918.json
data/raw/transit/provenance_mmrcl_journey_wor_aca_20260918.json
data/raw/transit/provenance_mmrcl_passenger_booklet.json
data/raw/transit/provenance_mmrcl_passenger_facilities.json
data/raw/transit/provenance_mmrcl_passenger_faqs.json
data/raw/transit/provenance_mmrcl_passenger_home_20260918.json
data/raw/transit/provenance_mmrcl_public_app_bundle_20260918.json
data/raw/transit/provenance_mmrcl_public_menu.json
data/raw/transit/provenance_mmrcl_public_notices.json
data/raw/transit/provenance_mmrcl_station_aca.json
data/raw/transit/provenance_mmrcl_station_aryj.json
data/raw/transit/provenance_mmrcl_station_bdrm.json
data/raw/transit/provenance_mmrcl_station_chgm.json
data/raw/transit/provenance_mmrcl_station_ciad.json
data/raw/transit/provenance_mmrcl_station_csia.json
data/raw/transit/provenance_mmrcl_station_cstm.json
data/raw/transit/provenance_mmrcl_station_cup.json
data/raw/transit/provenance_mmrcl_station_ddrm.json
data/raw/transit/provenance_mmrcl_station_dhav.json
data/raw/transit/provenance_mmrcl_station_girg.json
data/raw/transit/provenance_mmrcl_station_gtrm.json
data/raw/transit/provenance_mmrcl_station_huc.json
data/raw/transit/provenance_mmrcl_station_klbd.json
data/raw/transit/provenance_mmrcl_station_mclm.json
data/raw/transit/provenance_mmrcl_station_midc.json
data/raw/transit/provenance_mmrcl_station_mlxm.json
data/raw/transit/provenance_mmrcl_station_mnk.json
data/raw/transit/provenance_mmrcl_station_scmu.json
data/raw/transit/provenance_mmrcl_station_sdit.json
data/raw/transit/provenance_mmrcl_station_sepz.json
data/raw/transit/provenance_mmrcl_station_shrr.json
data/raw/transit/provenance_mmrcl_station_sidv.json
data/raw/transit/provenance_mmrcl_station_stzm.json
data/raw/transit/provenance_mmrcl_station_vidb.json
data/raw/transit/provenance_mmrcl_station_vidn.json
data/raw/transit/provenance_mmrcl_station_wor.json
data/raw/transit/provenance_monorail_safety_20260221.json
data/raw/transit/provenance_monorail_status_official_20260918.json
data/raw/transit/provenance_morth_srtu_review_2019_2022.json
data/raw/transit/provenance_mrvc_fare_rationalisation_report.json
data/raw/transit/provenance_nmmt_bus_list_20260918.json
data/raw/transit/provenance_nmmt_bus_tracking_bundle.json
data/raw/transit/provenance_nmmt_bus_tracking_component.json
data/raw/transit/provenance_nmmt_current_app_bundle.json
data/raw/transit/provenance_nmmt_current_portal.json
data/raw/transit/provenance_nmmt_current_routes.json
data/raw/transit/provenance_nmmt_current_service_types.json
data/raw/transit/provenance_nmmt_current_stops.json
data/raw/transit/provenance_nmmt_pilot_schedule_5577.json
data/raw/transit/provenance_nmmt_pilot_shape.json
data/raw/transit/provenance_nmmt_pilot_stations.json
data/raw/transit/provenance_nmmt_platform_eta_bundle.json
data/raw/transit/provenance_nmmt_public_app_config.json
data/raw/transit/provenance_nmmt_route_alignments.json
data/raw/transit/provenance_nmmt_route_schedules.json
data/raw/transit/provenance_nmmt_route_stop_snapshot_20260918.json
data/raw/transit/provenance_nmmt_route_tracking_bundle.json
data/raw/transit/provenance_nmmt_route_tracking_component.json
data/raw/transit/provenance_nmmt_routes.json
data/raw/transit/provenance_nmmt_service_documentation.json
data/raw/transit/provenance_nmmt_stop_tracking_bundle.json
data/raw/transit/provenance_nmmt_stop_tracking_component.json
data/raw/transit/provenance_nmmt_stops.json
data/raw/transit/provenance_nmmt_timetable_bundle.json
data/raw/transit/provenance_nmmt_timetable_component.json
data/raw/transit/provenance_nmmt_trip_timetables.json
data/raw/transit/provenance_nmmt_vehicle_snapshot_20260918.json
data/raw/transit/provenance_ogd_metro_2a_7_ridership_daily_2024_2025.json
data/raw/transit/provenance_ogd_mmrda_ridership_catalog_20260922.json
data/raw/transit/provenance_ogd_monorail_ridership_daily_2024_2025.json
data/raw/transit/provenance_olectra_product_presentation_20210906.json
data/raw/transit/provenance_pib_beml_mumbai_order_2018.json
data/raw/transit/provenance_pib_suburban_capacity_20260313.json
data/raw/transit/provenance_railway_technology_navi_mumbai_metro.json
data/raw/transit/provenance_rinfra_annual_2024_25.json
data/raw/transit/provenance_rollingstockworld_navi_mumbai_crrc.json
data/raw/transit/provenance_switch_eiv22_brochure.json
data/raw/transit/provenance_tata_best_bus_delivery_20210807.json
data/raw/vehicles/provenance_maharashtra_bike_taxi_gr_2025.json
data/raw/vehicles/provenance_maharashtra_bike_taxi_rules_20250704.json
data/raw/vehicles/provenance_maharashtra_ev_policy_2025.json
data/raw/vehicles/provenance_maharashtra_transport_statistics_2016_17.json
data/raw/vehicles/provenance_vehicle_registrations_2024_25.json
data/raw/vehicles/provenance_vehicle_stock_2025.json
data/raw/water/provenance_mmb_ogd_catalogue.json
data/raw/water/provenance_mmb_performance.json
data/raw/water/provenance_mmb_public_app.json
data/raw/water/provenance_mmb_route_information.json
data/raw/water/provenance_mmb_routes.json
'''),
        'lineage_scope_none': _paths('''
data/processed/derived/_vehicle_possession_growth_report.json
data/processed/derived/vehicle_possession_growth.csv
data/processed/geospatial/_activity_location_attraction_report.json
data/processed/geospatial/activity_location_attraction.csv
data/processed/observed/mts_2017_office_category_stock.csv
data/processed/observed/mts_state_category_stock_series.csv
data/processed/observed/nfhs_household_vehicle_possession.csv
data/processed/observed/ogd_metro_daily_ridership.csv
schedules/baseline_suburban_timetable.zip
'''),
    },
    'newcastle': {
        'raw_without_retrieved': _paths('''
data/raw/_osm_fetch.log
data/raw/_s3_historical_gtfs_listing.txt
data/raw/fares/provenance_fares.json
data/raw/osm_attic/provenance_osm_attic.json
data/raw/p2p/provenance_p2p.json
data/raw/planning_tia/provenance_planning_tia.json
data/raw/provenance_abs_dem.json
data/raw/provenance_boam.json
data/raw/provenance_licences.json
data/raw/provenance_opal_patronage.json
data/raw/provenance_open_data.json
data/raw/provenance_osm.json
data/raw/speedzones/provenance_speed_zones.json
schedules/raw/provenance.json
'''),
    },
}


if __name__ == '__main__':
    sys.exit(main())
