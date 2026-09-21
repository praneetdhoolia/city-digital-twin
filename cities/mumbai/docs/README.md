# Mumbai acquisition and model development

**A small Mumbai behavioural baseline now runs; it is not calibrated.**
People choose modes from available alternatives,
and ridership emerges from those choices. Corridor precision follows later.
The provisional supply registry labels assumptions and their sweeps explicitly.

The research extent is provisionally the Mumbai Metropolitan Region. The user
has not yet confirmed this geographical choice. The notified extent, changing
administrative boundaries and external journeys must be reconciled before the
final simulation boundary and population are built. The native OSM input uses
the acquired administrative envelope for research overcoverage and retains
whole ways and complete selected turn restrictions.

- [Requirements ledger](requirements.json): data, representation, derivation
  method and unresolved evidence for every identified transport mode and input.
- [Source catalogue](../extract/sources.json): acquisition URLs and reuse limits.
- [Acquisition inventory](../data/processed/acquisition/source_inventory.json):
  verified hashes, acquired files, missing files and duplicate content.
- [Bus feed audit](../data/processed/acquisition/bus_gtfs_audit.json): structural
  checks and operator coverage. Passing these checks does not establish that
  buses operate as advertised.
- [Scaling evidence required](scaling.md): tests that must precede an accuracy
  claim for a reduced population.
- [Evidence notes](evidence_notes.md): source definitions, conflicts and gaps
  that prevent acquired files from being used directly as model inputs.

## Broad behavioural development case

The first completed case is `20260919T124247_2it_100pct-mumbai-smoke`: its
`_run.json` records `ran_to_last_iteration` at iteration 2. This covers the
initial simulated day and two subsequent iterations. The capacity correction
was verified in `20260919T125115_2it_100pct-mumbai-smoke` (329.7 s, also
completed). The passenger/freight case
`20260919T131342_2it_100pct-mumbai-smoke` also completed at iteration 2;
all truck and freight-train journeys finished within its 36-hour window.
The regional extension was executed in
`20260919T133154_2it_100pct-mumbai-smoke` (372.8 s, iteration 2 completed).
The boarding-fare case
`20260919T134746_2it_100pct-mumbai-smoke` also completed at iteration 2
(381.3 s); its permanent report includes charged fares by profile.
The fare-aware routing case
`20260919T140521_2it_100pct-mumbai-smoke` completed at iteration 2
(379.8 s), with declared ticket prices in both path choice and scoring.
The daily-activity case `20260919T141947_2it_100pct-mumbai-smoke` completed
at iteration 2 (391.9 s). It exposed late and unfinished tours; it is not a
validated daily schedule. The longer case `20260919T142650_8it_100pct-mumbai-smoke` completed at
iteration 8 (856.6 s), with unresolved service delays and overnight tours.
The point-and-area case `20260919T145000_8it_100pct-mumbai-smoke` also
completed at iteration 8 (857.4 s), with late and unfinished journeys remaining.
The development default runs iterations 0 to 8
under the same automatic JVM ceiling to examine learning.
Read the execution and choice diagnostics with
`python src/analyse/baseline_behaviour.py --run <name>`. The bounded development
entry point is:

```powershell
$env:CITYSIM_CITY = 'mumbai'
python run.py --baseline-smoke --run-config smoke_hired_fleet
```

A declared development sensitivity can use
`python run.py --baseline-smoke --run-config smoke_low_capacity_double`.
This tests provisional road-flow capacities on the same mapped geometry and
schedules. It changes no population expansion weight and is not a scaling
validation or an adopted calibration. The base factors remain one.

`python run.py --baseline-smoke --run-config smoke_mode_coverage` tests
unscored eligible mode alternatives alongside each original selected plan.
It uses base road capacities and sufficient plan memory. Prepared alternatives
are not evidence that the traveller has evaluated them; inspect the permanent
report's first-trip choice coverage and retained-plan scores after execution.
This case completed as `20260919T152454_8it_100pct-mumbai-smoke` at iteration
8 (904.6 s including preparation). It remains the choice-only control.
Omit `--run-config` to reproduce the single-plan control.
All retained plans had finite scores and recorded mode exploration broadened.
Late/unfinished journeys and zero ferry use remain; see decision 9.198.

The broad development case `--run-config smoke_hired_fleet` adds separate taxi and auto
supply pools. Requests wait until capacity becomes available after actual
arrivals. Its stock-based counts and pickup turnaround are provisional. This
does not yet model spatial dispatch or empty vehicle movements. It completed
as `20260919T155059_8it_100pct-mumbai-smoke` at iteration 8 in 910.5 seconds,
including preparation. Refused requests currently abort the traveller's day.
See decision 9.200 before interpreting its ridership or waiting times.

It uses the prepared mapped network, multimodal schedule and small synthetic
population. This is a development case, not a calibrated city forecast. The
population has no full-city expansion weight, and road/transit capacity scaling
has not been validated. Each launch records its inputs, configuration and
completion status under the managed results store.

The initial choice set includes walking, cycling, car, vehicle passenger,
motorbike, taxi, auto-rickshaw and public transport. The transit router can
combine bus, suburban rail, metro and ferry services. Age, licence and vehicle
access restrict alternatives; home/activity geography, travel time, monetary
cost and income affect their scores. Crowding, transfers, waiting, frequency
and measured iteration-to-iteration reliability are enabled provisionally.
Ridership targets do not set the initial modes or quotas.

Community buses and OSM-derived services are incomplete supply. Provisional
port trucks and freight trains now supplement residents, using fixed modes
and connected road/rail gates. Their volume and OD proxies require validation.
Household vehicle sharing, finite taxi fleets, concession/pass eligibility and
current population calibration still need integration. Short non-network
access connectors remain where the walking network does not reach a boarding
link. See [scaling evidence](scaling.md) before interpreting any mode share.

To rebuild the development demand and combined feed after changing their
registries:

```powershell
$env:PYTHONPATH = 'src'
python cities/mumbai/build/build_baseline_bus_feed.py
python cities/mumbai/build/build_baseline_transit_feed.py
python cities/mumbai/build/build_regional_bus_feed.py
python cities/mumbai/build/build_baseline_fares.py
python cities/mumbai/build/build_baseline_population.py
python cities/mumbai/extract/extract_activity_areas.py
python cities/mumbai/build/build_baseline_activities.py
python cities/mumbai/build/build_baseline_freight.py
python cities/mumbai/build/build_baseline_choices.py
python cities/mumbai/build/build_hired_fleet.py
```

The regional extension adds the following provisional input services. Counts
come from `data/processed/acquisition/baseline_regional_buses.json`; published
operation and calendars remain unverified.

| Regional input | Count |
|---|---:|
| NMMT directed patterns | 566 |
| NMMT published departures included | 8,806 |
| MBMT directed patterns | 116 |
| MBMT derived departures | 1,972 |

NMMT trips without a unique operator route sequence matching their published
endpoints remain in the acquisition audit but are excluded from this feed.
MBMT frequency is derived from the published weekday allocation total and
approximate route cycle times; it is not an observed departure timetable.

Map a changed feed once with the shared MATSim builder. Reuse that mapped
network for comparisons; do not remap separate arms.

```powershell
python src/build/build_matsim_network.py --stage schedules --only baseline_regional --workers 1 --threads 2
python cities/mumbai/build/build_baseline_freight.py
python cities/mumbai/build/build_baseline_choices.py
```

Run the city-owned acquisition and audit tools from the repository root:

```powershell
$env:CITYSIM_CITY = 'mumbai'
$env:PYTHONPATH = 'src'
python cities/mumbai/extract/acquire_sources.py
python cities/mumbai/extract/acquire_nmmt_schedules.py --details
python cities/mumbai/extract/acquire_nmmt_paths.py
python cities/mumbai/extract/audit_nmmt_paths.py
python cities/mumbai/extract/acquire_nmmt_route_stops.py --snapshot-label 20260918
python cities/mumbai/extract/audit_nmmt_route_stops.py
python cities/mumbai/extract/acquire_nmmt_vehicle_details.py --snapshot-label 20260918
python cities/mumbai/extract/audit_nmmt_vehicle_details.py
python cities/mumbai/extract/audit_gtfs.py
python cities/mumbai/extract/audit_boundary_sources.py
python cities/mumbai/extract/extract_extended_area_villages.py
python cities/mumbai/extract/audit_scheduled_area_names.py
python cities/mumbai/extract/extract_census_controls.py
python cities/mumbai/extract/build_census_geographies.py
python cities/mumbai/extract/extract_bmc_population_estimates.py
python cities/mumbai/extract/extract_population_projections.py
python cities/mumbai/extract/extract_district_population_projections.py
python cities/mumbai/extract/extract_economic_survey_transport.py
python cities/mumbai/extract/extract_economic_survey_metro_ports.py
python cities/mumbai/extract/extract_metro_fleet_claims.py
python cities/mumbai/extract/extract_household_assets.py
python cities/mumbai/extract/extract_demographic_controls.py
python cities/mumbai/extract/extract_age_work_controls.py
python cities/mumbai/extract/extract_education_controls.py
python cities/mumbai/extract/extract_time_use_controls.py
python cities/mumbai/extract/extract_employment_controls.py
python cities/mumbai/extract/extract_vehicle_controls.py
python cities/mumbai/extract/register_raster_sources.py
python cities/mumbai/extract/audit_raster_sources.py
python cities/mumbai/extract/convert_osm_source.py
python cities/mumbai/extract/audit_osm_topology.py
python cities/mumbai/extract/audit_osm_references.py
python cities/mumbai/extract/build_osm_network_source.py
python cities/mumbai/extract/audit_osm_network_source.py
python cities/mumbai/extract/audit_transport_tags.py
python cities/mumbai/extract/build_road_attribute_evidence.py
python cities/mumbai/extract/build_road_access_evidence.py
python cities/mumbai/extract/build_rail_geometry.py
python cities/mumbai/extract/build_road_geometry.py
python cities/mumbai/extract/audit_road_geometry.py
python cities/mumbai/extract/build_protected_road_chains.py
python cities/mumbai/extract/build_turn_restriction_evidence.py
python cities/mumbai/extract/audit_coastal_access.py
python cities/mumbai/extract/extract_jvlr_controls.py
python cities/mumbai/extract/extract_coastal_travel_times.py
python cities/mumbai/extract/extract_coastal_traffic_counts.py
python cities/mumbai/extract/extract_tbtt_base_counts.py
python cities/mumbai/extract/extract_tbtt_travel_times.py
python cities/mumbai/extract/extract_bmc_signal_inventory.py
python cities/mumbai/extract/extract_jvlr_journal.py
python cities/mumbai/extract/extract_jvlr_inventory.py
python cities/mumbai/extract/extract_arterial_capacity_literature.py
python src/build/build_matsim_network.py --stage osm
python cities/mumbai/extract/extract_osm_research_layers.py
python cities/mumbai/extract/extract_transport_points.py
python cities/mumbai/extract/extract_transport_areas.py
python cities/mumbai/extract/extract_transport_relations.py
python cities/mumbai/extract/register_traffic_notices.py --acquire
python cities/mumbai/extract/audit_traffic_notices.py
python cities/mumbai/extract/audit_arcgis_boundaries.py
python cities/mumbai/extract/audit_nmmt_schedules.py
python cities/mumbai/extract/extract_best_controls.py
python cities/mumbai/extract/extract_srtu_controls.py
python cities/mumbai/extract/extract_bus_capacity_evidence.py
python cities/mumbai/extract/acquire_mbmt_sources.py
python cities/mumbai/extract/audit_mbmt_routes.py
python cities/mumbai/extract/extract_mbmt_controls.py
python cities/mumbai/extract/extract_water_transport.py
python cities/mumbai/extract/register_port_rail_sources.py --acquire
python cities/mumbai/extract/extract_port_rake_observations.py
python cities/mumbai/extract/extract_port_rail_controls.py
python cities/mumbai/extract/extract_wr_timetable.py
python cities/mumbai/extract/extract_cr_timetable.py
python cities/mumbai/extract/extract_cr_service_markers.py
python cities/mumbai/extract/build_harbour_service_evidence.py
python cities/mumbai/extract/build_harbour_identity_evidence.py
python cities/mumbai/extract/match_harbour_station_geometry.py
python cities/mumbai/extract/build_harbour_track_evidence.py
python cities/mumbai/extract/build_harbour_path_candidates.py
python cities/mumbai/extract/extract_suburban_fleet_claims.py
python cities/mumbai/extract/extract_holiday_evidence.py
python cities/mumbai/extract/extract_mmrcl_stations.py
python cities/mumbai/extract/extract_mmrcl_journeys.py
python cities/mumbai/extract/extract_metro3_fares.py
python cities/mumbai/extract/extract_navi_metro_controls.py
python cities/mumbai/extract/inventory_sources.py --sync-descriptor
python src/build/build_manifest.py
```

Acquisitions are immutable and have per-file provenance. An unsuccessful
download stays unobtained. An HTML error page cannot be accepted as a PDF.
Repeated source URLs with identical bytes are one observation, not independent
corroboration. A publication date and the year measured are separate facts.
When a public PDF fails through the ordinary downloader, the connected browser
can capture the same verified HTTPS GET. `extract/import_browser_acquisition.py`
validates that captured response against the catalogue, file type, byte count
and immutable hash before importing it. It accepts no credentials or account
metadata and does not accept a data-use agreement on the user's behalf.
Run the raster registration after the boundary audit, then acquire its selected
IDs with `acquire_sources.py --id <source_id>`. Registration derives the download
extent from the acquired administrative data and does not set a model boundary.

The current `city.json` is an incomplete acquisition descriptor. City readiness
checks must continue to fail until the registry, boundaries, inputs, adapters
and runnable contract are complete. No model result or all-mode accuracy claim
can be made from this directory's existence.

The descriptor's `osm_network_inputs` names the combined native XML source.
The shared MATSim builder accepts it directly, including gzip compression.
This removes the need to create four artificial themed files. Network
conversion still requires evidenced speed, capacity and access settings.

Government publication does not establish an open reuse licence. Source rights
remain separate from the package's original records. Any OSM-derived layer must
retain its ODbL provenance and applicable share-alike terms.
