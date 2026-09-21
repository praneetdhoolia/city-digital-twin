# Configuration reference

**Generated from `cities/<city>/registry/` by `src/registry/render_docs.py`. Do not edit by hand** - edit the registry and regenerate, or the two will disagree and `check_package.py` will say so.

Every value the model consumes that is not read from an immutable raw download is declared here with its units, its provenance, and either a sweep range or an explicit rule holding it fixed. That is proposal 8.1 - *"every parameter chosen without direct empirical support must be recorded with its rationale and its sweep range"* - enforced as a schema constraint rather than a convention.

## How to control any of it

```bash
# a run overlay - the committed way to vary a run
cp cities/<city>/overlays/runs/example.json cities/<city>/overlays/runs/my_run.json
python src/run/run_matsim.py --scenario S2 --day WEEKDAY --run-config my_run

# a one-off override, checked against the same rules
python src/run/run_matsim.py --scenario S2 --day WEEKDAY \
    --set RUN.sample.fraction=0.10 --set RUN.controler.last_iteration=500

# or from the environment
CITYSIM_RUN_SAMPLE_FRACTION=0.10 python src/run/run_matsim.py --scenario S2 ...
```

Resolution order, lowest precedence first: `cities/<city>/registry/*.json` -> `overlays/scenarios/<S>.json` -> `overlays/day/<DAY>.json` -> `overlays/runs/<tag>.json` -> `CITYSIM_*` environment -> `--set`. The resolved snapshot is written into every run directory as `_config.json`, so a result always carries the exact inputs that produced it.

Three things are refused at every layer:

1. **An unobtained input cannot acquire a point value by being read.** `get()` raises; the caller must select a sweep member explicitly.
2. **An overlay cannot invent a field.** A key that is not already declared is rejected.
3. **A value cannot silently leave its sweep, and a held-fixed value cannot move at all.** Escaping a range requires `allow_outside_sweep` plus a written justification in a committed overlay - never a flag typed at a shell.

## What the 411 fields are made of

| Provenance | Fields | Meaning |
|---|---:|---|
| `observed` | 8 | read directly from a raw download |
| `measured` | 9 | computed from observed data in this package |
| `derived` | 22 | follows from another registry field by identity |
| `literature` | 36 | a published value, not specific to this city |
| `assumed` | 160 | chosen without direct empirical support |
| `definition` | 176 | fixed by the formulation, not an empirical quantity |

| Status | Fields | Meaning |
|---|---:|---|
| `active` | 369 | usable point value |
| `computed` | 6 | written at run time from other fields; do not hand-edit |
| `placeholder` | 35 | a structural stand-in; the model runs but the field is not defensible |
| `unobtained` | 1 | the datum does not exist in the package; must be swept, never pinned |

### The 1 fields with no value

These carry `value: null` and the resolver refuses to return a point value for them. They are the project's honest edge: what it does not know, declared rather than guessed.

| Field | Sweep | Why it has no value |
|---|---|---|
| `B.population.tertiary_attendance_rate_20_24` | 0 - 0.35 | Unobtained: null, and the synthesiser makes nobody in that age range a student, which the report says. |

### What the 196 sweeps are for

A sweep is one word for two things (#134): the sensitivity CURVE DECISIONS.md 8.1 says must be reported rather than a headline at a single value, and the honesty BRACKET DECISIONS.md 15 requires before an assumed value may validate. Every sweep carries a `sweep_role` saying which, and the resolver refuses one that does not. `python src/registry/sweep_ledger.py` prints the ledger with whether any overlay has ever set each field.

| Role | Sweeps | Meaning |
|---|---:|---|
| `answer` | 5 | a P6 deliverable - the record says the curve across this sweep decides the answer, and an arm plan with a stated cost is owed once the twin passes its gate |
| `uncertainty` | 183 | a declared bracket the resolver enforces; no run is scheduled over it, and the basis says whether its leverage is measured or unknown |
| `measurement` | 8 | an observed spread on a measured or derived value; it describes the data, not a run to make |

The `answer` sweeps - the runs the study owes after the gate:

| Field | Value | Sweep |
|---|---|---|
| `B.ride.pairing_rule` | `both_links` | `both_links`, `route_contains`, `origin_link`, `dest_link`, `window_only` |
| `RUN.mode_choice.pt_submode_alternatives` | `aggregate` | `aggregate`, `alternatives` |
| `RUN.replanning.plan_selector_for_removal` | `WorstPlanSelector` | `WorstPlanSelector`, `SelectRandom`, `SelectExpBetaForRemoval`, `ChangeExpBetaForRemoval`, `PathSizeLogitSelectorForRemoval` |
| `RUN.replanning.score_msa_representation` | `absent` | `absent`, `at_innovation_cutoff` |
| `RUN.routing.access_egress_consistency_check` | `reroute` | `reroute`, `disable`, `abortOnInconsistency` |

### The 11 fields held fixed

Not tunable. DECISIONS.md 8.5 holds the mode constants fixed because calibrating them would fit away the effect under test - proposal 9 names ASC absorption as the primary threat to validity.

- `B.activity.detour_factor` - the reference city's measurement, adopted; no Mumbai measurement exists and the field is not varied
- `B.activity.short_trip_band_km` - the published band boundary of the source table (HTS Sydney 2012/13 Table 4.4.7, 'Up to 1km'). Changing it means citing a different row of the same table, not sweeping a belief - t
- `B.targets.goods_vehicle_traffic_share_pct` - a published screenline observation (CMP for Greater Mumbai executive summary, traffic composition), never varied
- `B.taxi.daily_trips_band` - A CONSTRAINT, NEVER A TARGET (9.8/9.13): the pre-registered 67/143 target split cannot grow. The modelled taxi volume is REPORTED against this band; nothing is fitted to it.
- `B.taxi.fleet_size` - adopted from the reference city, where it is derived from B.taxi.daily_trips_band, B.taxi.vehicle_trips_per_day; those fields are not declared for this city, so the value is held
- `CAL.asc.max_step_utils` - A REFUSAL THRESHOLD, not a model input, and so not swept - the A.signals.scats_match_radius_m precedent for a build guard's tolerance. It is the point past which a proposed step st
- `CAL.objective.include_counts` - adopted from the reference city, where it is derived from B.external.interaction_rate; those fields are not declared for this city, so the value is held
- `CAL.search.reading_drift_pct` - the reference city's measurement, adopted; no Mumbai measurement exists and the field is not varied
- `RUN.machine.heap_floor_gib` - the LIVE SET after the last full collection of a case with no population to speak of, read from its gc.log (Pause Full N->M: M), never the pre-collection peak - under ParallelGC wi
- `RUN.machine.heap_per_fraction_gib` - persons in the core (27.06 M) x RUN.replanning.max_agent_plan_memory x the live heap a routed plan holds at steady state - 19 KB on the reference city's 25 % arm 20260916T063903_25
- `RUN.monitor.pace_band_s` - the reference city's measurement, adopted; no Mumbai measurement exists and the field is not varied

## Broad baseline boarding fares

*`cities/mumbai/registry/A_baseline_fares.json` - 4 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.baseline_fares.ac_route_pattern` | `(^A[- ]|\bAS\b|\bAC\b)` | regular_expression | `assumed` | `(^A[- ]|\bAS\b|\bAC\b)`, `(?!)`, `.*` |
| `A.baseline_fares.fallback_rate_money_per_m` | `{"bus": 0.001, "rail": 0.001, "subway": 0.001, "ferry": 0.001}` | INR_per_metre | `assumed` | plus/minus 50% |
| `A.baseline_fares.published_agency_id` | `BEST` | GTFS_agency_id | `definition` | - |
| `A.baseline_fares.rider_class` | `adult` | published_fare_column_suffix | `assumed` | `adult`, `concessional` |

#### `A.baseline_fares.ac_route_pattern`

Provisional class inference from acquired route labels. This does not prove the assigned departure is air-conditioned.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Explicit class-assignment sensitivity pending verified route vehicle assignments and passenger eligibility.

#### `A.baseline_fares.fallback_rate_money_per_m`

Retain the previous baseline PT rate on unpriced operators/submodes; these are explicit proxies, not observed tariffs.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional uncovered-tariff uncertainty; replace with acquired and validated operator tables.

#### `A.baseline_fares.published_agency_id`

Acquired operator tariff scope; do not assign this tariff to another agency.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.baseline_fares.rider_class`

Adult-priced development population pending verified concessions and pass ownership; not an observed eligibility assignment.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Explicit class-assignment sensitivity pending verified route vehicle assignments and passenger eligibility.

## Provisional broad transit services

*`cities/mumbai/registry/A_baseline_services.json` - 10 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.baseline_transit.commercial_speed_kmh` | `{"train": 35, "subway": 32, "ferry": 15}` | km/h | `assumed` | 8 - 60 |
| `A.baseline_transit.directory_crossings` | `{"1": {"from": "1640461450", "to": "4306257482", "profile": "ferry_versova_madh"}, "3": {"from": "627734256...` | crossing_table | `definition` | - |
| `A.baseline_transit.distance_multiplier` | `{"train": 1.25, "subway": 1.15, "ferry": 1.0}` | factor | `assumed` | 1 - 1.75 |
| `A.baseline_transit.gtfs_route_types` | `{"train": 2, "subway": 1, "ferry": 4}` | GTFS_route_type_codes | `definition` | - |
| `A.baseline_transit.networks` | `{"train": ["Mumbai Suburban Railway", "IR"], "subway": ["Mumbai Metro", "Navi Mumbai Metro"]}` | OSM_network_tags | `definition` | - |
| `A.baseline_transit.offpeak_headway_s` | `{"train": 900, "subway": 600, "ferry": 1800}` | seconds | `assumed` | 300 - 5400 |
| `A.baseline_transit.peak_headway_s` | `{"train": 600, "subway": 360, "ferry": 1800}` | seconds | `assumed` | 180 - 3600 |
| `A.baseline_transit.peak_windows_s` | `[[25200, 36000], [61200, 72000]]` | seconds_after_midnight | `assumed` | 21600 - 75600 |
| `A.baseline_transit.service_window_s` | `[18000, 86400]` | seconds_after_midnight | `assumed` | 14400 - 90000 |
| `A.baseline_transit.stop_dwell_s` | `{"train": 30, "subway": 30, "ferry": 120}` | seconds | `assumed` | 15 - 300 |

#### `A.baseline_transit.commercial_speed_kmh`

Provisional movement speeds between mapped stops; explicit dwell is added separately.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

#### `A.baseline_transit.directory_crossings`

The Maharashtra Maritime Board's passenger crossings (water_service_directory.csv, keyed by its directory_route_id) that the feed generates beside the two OSM ferry relations, each between the two OSM ferry terminals its named jetties are (osm_transport_points.csv node ids: Versova Jetty 1640461450, Madh Jetty 4306257482, Marve Jetty 627734256, Manori Jetty 564906271, Gorai 564878691 (the node named Gorai Ferry, 814439568, sits 47 m from the Borivali jetty on the Borivali bank), Borivali 593916996, Essel World 627733109, Bhaucha Dhakka / Ferry Wharf 6813413581, Uran (Mora) 2236784797, Gateway of India 870449150, Mandwa RoRo Ferry Terminal 1186542661, M2M Ro-Ro Terminal 8360488232), and the fleet profile carrying its vessel capacity. Both directions are generated; directory route 2 is route 1's return. Not included, and why: 9 (Ferry Wharf-Rewas) has no capacity in the directory; 12 (Karanja-Rewas), 13 (Mora-Sassoon Dock) and 15 (Belapur-Nerul/Vashi) have a terminal OSM names only by coordinate, not by name; 6 (Marve-Esselworld) has no capacity; 7 (Arnala) and 17-21 are outside the core or carry no departure. Identifiers of the mapped terminals, not values (9.207).

***definition** · status **active** · DECISIONS.md §9.207*

#### `A.baseline_transit.distance_multiplier`

Provisional path/geodesic ratio for rail stops; ferry distance comes from mapped water geometry.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

#### `A.baseline_transit.gtfs_route_types`

GTFS mode vocabulary.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.baseline_transit.networks`

Select regional suburban and metro relation networks; other long-distance services are excluded from the initial resident choice set.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.baseline_transit.offpeak_headway_s`

Provisional per-direction off-peak headways.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

#### `A.baseline_transit.peak_headway_s`

Provisional per-direction route-pattern peak headways; not observed schedules.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

#### `A.baseline_transit.peak_windows_s`

Provisional morning and evening service peaks.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

#### `A.baseline_transit.service_window_s`

Provisional operating window for generated rail, metro and ferry services.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

#### `A.baseline_transit.stop_dwell_s`

Provisional stop dwell applied to generated schedules.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service assumptions; test service supply sensitivity, not fitted ridership shares.

## Provisional broad Mumbai supply

*`cities/mumbai/registry/A_baseline_supply.json` - 45 fields*

First runnable baseline; provisional parameters are explicit and are not calibrated observations.

| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.baseline.dedicated_transit_headway_s` | `{"rail": 90, "light_rail": 90, "subway": 90, "ferry": 900}` | seconds_per_vehicle | `assumed` | plus/minus 50% |
| `A.baseline.inputs` | `{"network": "networks/matsim/schedules/baseline_regional/network.xml.gz", "schedule": "networks/matsim/sche...` | city_relative_paths | `definition` | - |
| `A.baseline.network_mode_sources` | `{"truck": "car", "freight_rail": "rail"}` | mode_mapping | `definition` | - |
| `A.baseline.road_capacity_factors` | `{"motorway": 1.0, "motorway_link": 1.0, "trunk": 1.0, "trunk_link": 1.0, "primary": 1.0, "primary_link": 1....` | dimensionless_flow_capacity_factor | `assumed` | 0.5 - 3 |
| `A.baseline.road_mode_exclusions` | `{"car": [], "ride": [], "walk": ["motorway", "motorway_link"], "bike": ["motorway", "motorway_link"], "moto...` | highway_classes_by_mode | `definition` | - |
| `A.baseline.transit_mode_aliases` | `{"light_rail": "subway"}` | mode_mapping | `definition` | - |
| `A.baseline.transit_timing` | `{"speed_ms": {"bus": 8.333333333333334, "rail": 16.666666666666668, "subway": 16.666666666666668, "ferry": ...` | metres_per_second_and_seconds | `assumed` | plus/minus 50% |
| `A.fare.boarding_representation` | `table` | enum | `definition` | - |
| `A.fare.boarding_route_choice` | `true` | boolean | `definition` | - |
| `A.network.freespeed_factor` | `1.0` | factor | `definition` | - |
| `A.network.keep_paths` | `false` | boolean | `definition` | - |
| `A.network.keep_tags_as_attributes` | `true` | boolean | `definition` | - |
| `A.network.keep_ways_with_public_transit` | `true` | boolean | `definition` | - |
| `A.network.max_link_length_m` | `500` | metres | `assumed` | 100 - 1000 |
| `A.network.parse_turn_restrictions` | `true` | boolean | `definition` | - |
| `A.network.path_access_overrides` | `{"keys": {"access": "all", "foot": "walk", "bicycle": "bike"}, "grant": ["yes", "designated", "permissive",...` | osm_access_vocabulary | `definition` | - |
| `A.network.path_lane_capacity_veh_h` | `10000` | vehicles_per_hour | `assumed` | 1000 - 20000 |
| `A.network.path_modes_by_class` | `{"bridleway": ["walk", "bike"], "corridor": ["walk"], "cycleway": ["bike", "walk"], "footway": ["walk"], "p...` | mode_names_by_osm_highway_class | `definition` | - |
| `A.network.railway_lane_capacity_veh_h` | `120` | vehicles_per_hour | `assumed` | 30 - 240 |
| `A.network.railway_speed_default_kmh` | `{"rail": 60, "subway": 60, "light_rail": 40, "tram": 25, "monorail": 40}` | km_per_hour | `assumed` | 15 - 100 |
| `A.network.routable_subnetworks` | `{"car": ["car"], "bus": ["bus", "car"], "rail": ["rail", "light_rail"], "walk": ["walk"], "bike": ["bike"]}` | mode_names_by_subnetwork | `definition` | - |
| `A.network.scale_max_speed` | `false` | boolean | `definition` | - |
| `A.network.way_default_oneway` | `{"motorway": true, "motorway_link": true}` | boolean_by_way_class | `definition` | - |
| `A.network.write_crs` | `true` | boolean | `definition` | - |
| `A.road.capacity_default` | `{"motorway": 1800, "motorway_link": 600, "trunk": 1800, "trunk_link": 600, "primary": 1200, "primary_link":...` | vehicles_per_hour_per_lane | `assumed` | 300 - 2400 |
| `A.road.lanes_default` | `{"motorway": 2, "motorway_link": 1, "trunk": 2, "trunk_link": 1, "primary": 2, "primary_link": 1, "secondar...` | lanes_per_direction | `assumed` | 1 - 4 |
| `A.road.speed_default` | `{"motorway": 80, "motorway_link": 40, "trunk": 60, "trunk_link": 35, "primary": 50, "primary_link": 30, "se...` | km_per_hour | `assumed` | 5 - 100 |
| `A.schedule_mapping.bounded_search` | `true` | boolean | `definition` | - |
| `A.schedule_mapping.candidate_distance_multiplier` | `2.0` | factor | `assumed` | 1 - 4 |
| `A.schedule_mapping.max_link_candidate_distance_m` | `150.0` | metres | `assumed` | 75 - 300 |
| `A.schedule_mapping.max_travel_cost_factor` | `8.0` | factor | `assumed` | 4 - 16 |
| `A.schedule_mapping.mode_specific_rules` | `true` | boolean | `definition` | - |
| `A.schedule_mapping.modes_to_keep_on_cleanup` | `["car", "bus", "walk", "bike", "rail", "light_rail"]` | mode_names | `definition` | - |
| `A.schedule_mapping.n_link_threshold` | `8` | links | `assumed` | 4 - 16 |
| `A.schedule_mapping.network_router` | `SpeedyALT` | router_name | `definition` | - |
| `A.schedule_mapping.remove_not_used_stop_facilities` | `true` | boolean | `definition` | - |
| `A.schedule_mapping.routing_with_candidate_distance` | `true` | boolean | `definition` | - |
| `A.schedule_mapping.schedule_freespeed_modes` | `["artificial"]` | mode_names | `definition` | - |
| `A.schedule_mapping.strict_link_rule` | `false` | boolean | `definition` | - |
| `A.schedule_mapping.thread_chunk_size` | `100` | routes | `assumed` | 50 - 200 |
| `A.schedule_mapping.transport_mode_assignment` | `{"bus": ["car", "bus"], "rail": ["rail"], "light_rail": ["light_rail"], "tram": ["light_rail"], "ferry": ["...` | network_modes_by_schedule_mode | `definition` | - |
| `A.schedule_mapping.travel_cost_type` | `linkLength` | cost_basis | `definition` | - |
| `A.transit.walk_speed_ms` | `1.2` | metres_per_second | `assumed` | 0.6 - 1.8 |
| `B.bike.speed_ms` | `4.0` | m/s | `assumed` | 2 - 7 |
| `RUN.machine.build_xmx` | `16g` | jvm_heap | `definition` | - |

#### `A.baseline.dedicated_transit_headway_s`

Provisional dedicated-link service envelope. Flow capacity derives as maximum mapped vehicle PCU times 3600/headway, preserving any greater mapped capacity. This avoids interpreting a train headway as car-equivalent flow and is not a validated signalling capacity. Moved from RUN.smoke.dedicated_transit_headway_s on 21 September 2026 (9.204): the launch path is the harness, and the field is read by the build step that assembles the scenario.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Dedicated-mode headway sensitivity; replace with observed sectional signalling and vessel constraints.

#### `A.baseline.inputs`

The prepared baseline inputs the scenario assembly reads: the mapped regional network and combined feed (one pt2matsim build), the citywide plans written at B.population.plans_build_fraction from the synthesised core population (build_plans.py, 9.205), the boarding-fare table and the hired-fleet derivation. The assembly writes scenarios/matsim/BASE/, demand/plans/matsim/population_WEEKDAY.xml.gz and the plans report the launcher reads for the build fraction. fleet_assignments is the per-vehicle capacity assignment build_transit_fleet.py writes beside the mapped feed (9.206): the assembly resolves every mapped vehicle's seats and standing places through it, never copying the mapper's default capacities.

***definition** · status **active** · DECISIONS.md §9.205, 9.206*

#### `A.baseline.network_mode_sources`

Provisional goods modes share their source network, with connected components audited. Detailed HGV and freight operating restrictions remain incomplete. Moved from RUN.smoke.network_mode_sources on 21 September 2026 (9.204): the launch path is the harness, and the field is read by the build step that assembles the scenario.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.baseline.road_capacity_factors`

Declared class sensitivity factors on the already mapped network. Identity preserves source capacities; this is not population sampling or evidence of correct road capacity. Geometry, lanes, speed and service departures are retained. Moved from RUN.smoke.road_capacity_factors on 21 September 2026 (9.204): the launch path is the harness, and the field is read by the build step that assembles the scenario.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional flow-capacity sensitivity envelope, not fitted or observed Mumbai capacities.

#### `A.baseline.road_mode_exclusions`

Coarse class-based availability pending refined corridor access rules. Moved from RUN.smoke.road_mode_exclusions on 21 September 2026 (9.204): the launch path is the harness, and the field is read by the build step that assembles the scenario.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.baseline.transit_mode_aliases`

Mapped metro track permission uses light_rail; mapped metro vehicle profiles use subway. Moved from RUN.smoke.transit_mode_aliases on 21 September 2026 (9.204): the launch path is the harness, and the field is read by the build step that assembles the scenario.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.baseline.transit_timing`

Provisional moving-speed caps and intermediate-stop dwell derive physically feasible timetable offsets from the mapped path. Later source times are retained; no observed timetable is overwritten. Moved from RUN.smoke.transit_timing on 21 September 2026 (9.204): the launch path is the harness, and the field is read by the build step that assembles the scenario.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `A.fare.boarding_representation`

Whether pt boardings are charged from a per-route boarding-fare table (citysim.BoardingFareHandler; `table`) assembled beside the scenario network as boarding_fares.csv, or not (`absent`). `table` for this city: the published BEST, NMMT, suburban-rail, metro and ferry tariffs are transcribed per route into params/baseline/boarding_fares.csv (build_baseline_fares.py) and the harness refuses a scenario that lost its table.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.fare.boarding_route_choice`

Price each candidate transit boarding with the same city fare table and person-specific money utility as executed scoring, before RAPTOR prunes paths. This enables a mechanism, not a calibrated preference. Moved from RUN.smoke.boardingFare.routeChoice on 21 September 2026 (9.204): one key per MATSim parameter, under the framework's fare vocabulary.

***definition** · status **active** · DECISIONS.md §9.204 · MATSim `boardingFare.routeChoice`*

#### `A.network.freespeed_factor`

Use declared or tagged free speed without an extra multiplier.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.keep_paths`

Baseline converter switch. Geometry reduction is permitted for the broad behavioural prototype; detailed node controls remain a declared limitation.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.keep_tags_as_attributes`

Converter representation switch for the broad baseline.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.keep_ways_with_public_transit`

Converter representation switch for the broad baseline.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.max_link_length_m`

Provisional maximum reduced link length; whole source geometry remains available.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.network.parse_turn_restrictions`

Converter representation switch for the broad baseline.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.path_access_overrides`

Existing explicit path-tag parser vocabulary. Conditional and purpose-specific restrictions remain separate evidence.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.path_lane_capacity_veh_h`

Provisional nonbinding active-path capacity for the first baseline.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.network.path_modes_by_class`

Baseline active-travel graph vocabulary; explicit path access tags are applied afterwards.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.railway_lane_capacity_veh_h`

Coarse track queue throughput for baseline; block signalling and corridor capacity deferred.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.network.railway_speed_default_kmh`

Provisional track free speeds; scheduled travel times will provide service timing. Not observed train operating speeds.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.network.routable_subnetworks`

Retain distinct active and transit subnetworks for later mode assembly.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.scale_max_speed`

Converter representation switch for the broad baseline.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.way_default_oneway`

Motorway carriageway direction convention; explicit OSM direction overrides it.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.network.write_crs`

Converter representation switch for the broad baseline.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.road.capacity_default`

Provisional class queue capacities. Used to enable congestion feedback to traveller decisions; not calibrated saturation flows.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.road.lanes_default`

Provisional per-direction lane counts where OSM lacks lane tags. Tagged values take precedence; corridor refinement deferred.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.road.speed_default`

Provisional class free speeds where OSM has no usable speed. Broad supply baseline authorised on 19 September 2026; not observed speeds. Tagged OSM speed takes precedence.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `A.schedule_mapping.bounded_search`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.candidate_distance_multiplier`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional mapper search sensitivity around the baseline, not a measured transport parameter.

#### `A.schedule_mapping.max_link_candidate_distance_m`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional mapper search sensitivity around the baseline, not a measured transport parameter.

#### `A.schedule_mapping.max_travel_cost_factor`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional mapper search sensitivity around the baseline, not a measured transport parameter.

#### `A.schedule_mapping.mode_specific_rules`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.modes_to_keep_on_cleanup`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.n_link_threshold`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional mapper search sensitivity around the baseline, not a measured transport parameter.

#### `A.schedule_mapping.network_router`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.remove_not_used_stop_facilities`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.routing_with_candidate_distance`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.schedule_freespeed_modes`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.strict_link_rule`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.thread_chunk_size`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional mapper search sensitivity around the baseline, not a measured transport parameter.

#### `A.schedule_mapping.transport_mode_assignment`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.schedule_mapping.travel_cost_type`

Broad-baseline schedule mapping rule. Mapping diagnostics must identify artificial links and stop offsets; this setting does not establish observed operational accuracy.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.transit.walk_speed_ms`

Provisional walking speed; individual mobility differences will enter the decision model.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `B.bike.speed_ms`

Provisional cycling free speed for the initial active network.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad-baseline range; not a measured Mumbai calibration interval.

#### `RUN.machine.build_xmx`

Memory ceiling for network preprocessing on the current workstation; throughput setting, not model supply.

***definition** · status **active** · DECISIONS.md §9.187*

## The study extent: the notified MMR reconciled to the census leaves (D13, 9.204)

*`cities/mumbai/registry/A_extent.json` - 2 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.extent.municipal_name_aliases` | `{"Kalyan-Dombiwali": "Kalyan-Dombivli", "Bhiwandi": "Bhiwandi Nizampur", "Vasai-Virar": "Vasai-Virar City"}` | name_map | `definition` | - |
| `A.extent.village_name_aliases` | `{"alibag/barghar": "borghar", "alibag/durgadarva": "durgadarya", "alibag/fanaspur": "fanasapur", "alibag/ga...` | name_map | `definition` | - |

#### `A.extent.municipal_name_aliases`

Spelling reconciliation between the municipality names of the public MMR GIS (WRI layers 2 and 3) and the town names of the Census 2011 ward rows, for the three that differ after case, punctuation and type suffixes are removed: the GIS writes Dombiwali where the census writes Dombivli, Bhiwandi where the census writes Bhiwandi Nizampur, and Vasai-Virar where the census writes Vasai-Virar City. A name reconciliation, not a modelling value; every match is listed in mmr_extent_audit.json.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.extent.village_name_aliases`

Transliteration reconciliation between the village names of the MMR extended-notified-area SPA notification (9 July 2024) and the Census 2011 village names, keyed taluka/notification-name (normalised) -> census name (normalised). Declared only where the notification name has exactly ONE census village within its taluka at a difflib similarity of 0.8 or better (mmr_extent_audit.json lists the candidates for every unmatched name); the four names with two or more candidates (Alibag Chincholi; Palghar Kardai, Paragaon, Sawari) stay unmatched until the village directory is acquired (census_maharashtra_villages, unobtained). A name reconciliation, not a modelling value.

***definition** · status **active** · DECISIONS.md §9.204*

## Framework run-side fields: moved from the private baseline namespace or adopted from the reference city (9.202)

*`cities/mumbai/registry/A_framework.json` - 35 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.bike_stress.representation` | `absent` | enum | `assumed` | `absent`, `felt_time` |
| `A.crossings.freight_closures_per_day` | `{}` | closures_per_day_per_site | `derived` | derived: no boom-gated crossing is represented (A.crossings.representation = ab |
| `A.crossings.representation` | `absent` | enum | `assumed` | `absent`, `change_events` |
| `A.gradient.bike_downhill_speedup_per_pct` | `0.015` | share_of_flat_speed_per_pct | `literature` | 0 - 0.03 |
| `A.gradient.bike_speed_ceiling_factor` | `1.3` | share | `assumed` | 1 - 1.5 |
| `A.gradient.bike_speed_floor_factor` | `0.2` | share | `assumed` | 0.1 - 0.3 |
| `A.gradient.bike_uphill_slowdown_per_pct` | `0.065` | share_of_flat_speed_per_pct | `literature` | 0.03 - 0.1 |
| `A.gradient.representation` | `absent` | enum | `assumed` | `absent`, `link_speed` |
| `A.gradient.walk_tobler_offset` | `0.05` | gradient_fraction | `literature` | 0.03 - 0.07 |
| `A.gradient.walk_tobler_slope_coeff` | `3.5` | dimensionless | `literature` | 2.5 - 4.5 |
| `A.parking.charged_end_hour` | *(null - unobtained)* | hour_of_day | `derived` | derived: A.parking.charged_hours_by_day_type[day][1], 0 for a day with no windo |
| `A.parking.charged_hours_by_day_type` | `{"WEEKDAY": null}` | hour_of_day | `definition` | - |
| `A.parking.charged_modes` | `["car"]` | enum | `definition` | - |
| `A.parking.charged_start_hour` | *(null - unobtained)* | hour_of_day | `derived` | derived: A.parking.charged_hours_by_day_type[day][0], 0 for a day with no windo |
| `A.parking.exempt_activity_types` | `["home"]` | enum | `assumed` | `['home']`, `[]` |
| `A.parking.max_stay_min` | `120.0` | minutes | `assumed` | 60 - 180 |
| `A.parking.search_time_representation` | `absent` | enum | `definition` | - |
| `A.signals.control_regime` | `fixed_time` | enum | `definition` | - |
| `A.signals.min_green_s` | `6.0` | seconds | `literature` | 4 - 10 |
| `A.signals.representation` | `implicit_delay` | enum | `assumed` | `implicit_delay`, `explicit_signals` |
| `A.signals.saturation_flow_veh_h_lane` | `1900.0` | vehicles_per_hour_per_lane | `literature` | 1800 - 2050 |
| `A.signals.scats.cycle_step_s` | `6.0` | s | `literature` | 3 - 12 |
| `A.signals.scats.ds_deadband` | `0.05` | ratio | `assumed` | 0.02 - 0.1 |
| `A.signals.scats.ds_smoothing` | `0.5` | weight | `assumed` | 0.1 - 0.9 |
| `A.signals.scats.max_cycle_s` | `150.0` | s | `literature` | 110 - 180 |
| `A.signals.scats.min_cycle_s` | `30.0` | s | `literature` | 20 - 60 |
| `A.signals.scats.target_degree_saturation` | `0.9` | ratio | `literature` | 0.8 - 0.98 |
| `A.signals.tsp.compensation_enabled` | `true` | boolean | `literature` | `True`, `False` |
| `A.signals.tsp.detection_distance_m` | `120.0` | metres | `assumed` | 60 - 250 |
| `A.signals.tsp.extension_window_s` | `12.0` | seconds | `assumed` | 5 - 20 |
| `A.signals.tsp.lateness_threshold_s` | `60.0` | seconds | `assumed` | 0 - 300 |
| `A.signals.tsp.mode` | `green_extension` | enum | `literature` | `off`, `green_extension`, `extension_recall`, `conditional` |
| `A.signals.tsp.priority_budget_share` | `0.2` | share_of_cycle | `literature` | 0.1 - 0.3 |
| `A.signals.tsp.priority_group` | `tram` | enum | `definition` | - |
| `A.taxi.fleet_representation` | `absent` | enum | `definition` | - |

#### `A.bike_stress.representation`

The representation gate for motor-traffic cycling stress (the Mode-Choice Ledger's rank-2 gap; issue #107). Switched off for this baseline ("absent"): no motor-traffic stress classes are attached to the mapped network yet.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `bikeStress.representation` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Whether motor-traffic stress reaches cycling at all. absent: the pre-9.138 state - a six-lane arterial cycles exactly like a cul-de-sac, while the route-choice literature's dominant cycling deterrent is adjacent traffic (Broach, Dill & Gliebe 2012) and modelled bike stood at +185.5% at the F22 iteration-100 gate. felt_time: every bike-capable run-network link carries a felt-distance multiplier for its road class (bike_stress_factor), a cyclist pays the extra felt time in score (citysim.BikeStressScoring, PersonScoreEvent) and sees the same multiplier in router link cost, so stressed streets are both avoided en route and felt in mode choice. One-gate discipline mirroring A.gradient.representation.

#### `A.crossings.freight_closures_per_day`

Non-timetabled freight movements a day at each boom-gated crossing. Empty: none is represented in this baseline.

***derived** · status **active** · DECISIONS.md §9.202*

> **Derived from** `A.crossings.representation`: no boom-gated crossing is represented (A.crossings.representation = absent), so the closure table is empty

#### `A.crossings.representation`

The representation gate for the two boom-gated freight level crossings. Switched off for this baseline ("absent"): no boom-gated freight crossing is represented.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Whether the freight-rail level-crossing closures (9.70, issue #68) reach the model at all. absent: the crossings are not represented (the pre-9.77 state - closures were a stated, unmodelled limitation). change_events: the derived crossing_change_events.xml enters every run input as a time-variant network, closing the crossing links for the swept closure pattern. The closure PATTERN stays swept on its own fields (closures_per_day, closure_duration_s); this switch is the representation gate, mirroring A.signals.representation's one-gate discipline.

#### `A.gradient.bike_downhill_speedup_per_pct`

Fraction of flat cycling speed gained per percent of downhill grade. Adopted from the reference city and INERT here: A.gradient.representation = "absent" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `gradient.bikeDownhillSpeedupPerPct` · sweep role **uncertainty***

> **Sweep basis.** Downhill gains are much smaller than uphill losses in the same on-road measurements (braking and control dominate); zero - no downhill gain at all - is inside the sweep.

#### `A.gradient.bike_speed_ceiling_factor`

Upper clamp on the bike gradient speed factor. Adopted from the reference city and INERT here: A.gradient.representation = "absent" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `gradient.bikeCeilingFactor` · sweep role **uncertainty***

> **Sweep basis.** Upper clamp on downhill gain over the declared cap; 1.0 - no downhill gain past the cap - is inside the sweep.

#### `A.gradient.bike_speed_floor_factor`

Lower clamp on the bike gradient speed factor. Adopted from the reference city and INERT here: A.gradient.representation = "absent" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `gradient.bikeFloorFactor` · sweep role **uncertainty***

> **Sweep basis.** The slowest a climbing cyclist goes before dismounting; no observation held, so declared and swept. 0.2 of the 4.2 m/s cap is 0.84 m/s - slow walking pace, a dismounted push.

#### `A.gradient.bike_uphill_slowdown_per_pct`

Fraction of flat cycling speed lost per percent of uphill grade, applied multiplicatively to the declared bike speed cap on each graded link. Adopted from the reference city and INERT here: A.gradient.representation = "absent" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `gradient.bikeUphillSlowdownPerPct` · sweep role **uncertainty***

> **Sweep basis.** Parkin & Rotheram 2010 (Ergonomics 53(8), on-road cyclist speeds) measure mean speed falling ~1.4 km/h per 1% of uphill grade against a ~21.6 km/h flat mean, i.e. ~6.5% of flat speed per grade percent; the sweep spans the spread of published grade-speed slopes.

#### `A.gradient.representation`

The representation gate for link gradient in walk and bike travel time (issue #21, reopened by measurement in 9.83). Switched off for this baseline ("absent"): no elevation is attached to the mapped network yet.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `gradient.representation` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Whether the attached gradients (50,182 road edges and the footway layer, all carrying copernicus_glo30 grades) reach the model at all. absent: the pre-9.84 state - gradient reaches mode choice through nothing, recorded honestly in not_representable and measured as material in 9.83 (modelled bike trips 9.21 km / 41.7 min against a measured 5.2 / 19.2 on a network where 30.5% of edges exceed 4% grade). link_speed: each run network link carries its signed grade_pct and walk/bike traverse it at a grade-adjusted speed on BOTH the router and the mobsim side - physics, not a behavioural weight. One-gate discipline mirrors A.signals.representation and A.crossings.representation.

#### `A.gradient.walk_tobler_offset`

Grade offset of the Tobler hiking function (the downgrade at which walking is fastest). Adopted from the reference city and INERT here: A.gradient.representation = "absent" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `gradient.walkToblerOffset` · sweep role **uncertainty***

> **Sweep basis.** The published Tobler offset: maximum walking speed occurs on a slight (-5%) downgrade. Swept narrowly around the published value.

#### `A.gradient.walk_tobler_slope_coeff`

Slope coefficient of the Tobler hiking function, normalised so a flat link keeps the declared walk speed cap unchanged. Adopted from the reference city and INERT here: A.gradient.representation = "absent" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `gradient.walkToblerSlopeCoeff` · sweep role **uncertainty***

> **Sweep basis.** Tobler 1993 (Three presentations on geographical analysis and modeling): W = 6 exp(-3.5 |dh/dx + 0.05|) km/h. The same function already produced walk_speed_factor_fwd/_rev on the A6 footway layer, so the run-time formula and the P2 data layer share one published source. Swept around the published coefficient.

#### `A.parking.charged_end_hour`

Hour at which parking stops being charged, derived at launch from the day type's window as in the reference city.

***derived** · status **computed** · DECISIONS.md §9.204 · MATSim `parking.chargedEndHour`*

> **Derived from** `A.parking.charged_hours_by_day_type`: A.parking.charged_hours_by_day_type[day][1], 0 for a day with no window; the harness supplies it under the derived runtime role

#### `A.parking.charged_hours_by_day_type`

The charged parking window per day type. None for the one day type: no parking price is observed for this city, the assembled price table beside the scenario network is empty (every link free), and a free day is written as a window of (0, 0) exactly as the reference city writes its Sunday.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.parking.charged_modes`

Leg modes that occupy a parking space and are charged for it. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `parking.chargedModes`*

#### `A.parking.charged_start_hour`

Hour at which parking begins to be charged, derived at launch from the day type's window as in the reference city.

***derived** · status **computed** · DECISIONS.md §9.204 · MATSim `parking.chargedStartHour`*

> **Derived from** `A.parking.charged_hours_by_day_type`: A.parking.charged_hours_by_day_type[day][0], 0 for a day with no window; the harness supplies it under the derived runtime role

#### `A.parking.exempt_activity_types`

Activity types at which a parked car is not charged. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `parking.exemptActivityTypes` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: the alternative arm charges parking at every activity including home, which is the behaviour this field exists to rule out.

#### `A.parking.max_stay_min`

Maximum charged parking duration. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `parking.maxStayMinutes` · sweep role **uncertainty***

> **Sweep basis.** +/-50% of the point value.

#### `A.parking.search_time_representation`

Whether a derived parking search time reaches the car's score. `absent` for this city: no parking price or occupancy is observed, the assembled price table is empty and there is no search time to derive.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.signals.control_regime`

Adaptive signalling disabled for the coarse smoke; this base controller has no detailed signal systems. Moved from RUN.smoke.scats.regime on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `scats.regime`*

#### `A.signals.min_green_s`

Minimum green time in a generated SUMO signal program. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.minGreenS` · sweep role **uncertainty***

> **Sweep basis.** TfNSW Traffic Signal Design TTD 2018/002 (Traffic Signals in Microsimulation Modelling) actuated practice: minimum green 5 s vehicle / 6 s pedestrian (dossier 01 table, URL in dossier 01; dossier 03/09); SYLVIA and Laemmer default 5 s. The declared 6 s IS the standard's pedestrian minimum, so the value is a published one, not a guess; the band brackets the practice range.

#### `A.signals.representation`

Which representation carries the corridor signal effect. Switched off for this baseline ("implicit_delay"): no signal inventory is modelled; the corridor-signal effect stays implicit.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: ONE REPRESENTATION PER EFFECT (the signalling dossier 04 7.5, DECISIONS 9.75/9.76): either the implicit per-intersection delay shapes the schedule and metered link capacities stand, OR explicit signals meter saturation-flow approaches and the implicit delay comes OUT of the same movements. Never both. Flipped to explicit_signals at the 9.77 activation boundary; implicit_delay remains the sweep's other arm and reproduces the pre-boundary family's inputs.

#### `A.signals.saturation_flow_veh_h_lane`

Stop-line saturation flow used to RE-CAPACITATE signalised approaches when signals are explicit. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.saturationFlowVehHLane` · sweep role **uncertainty***

> **Sweep basis.** HCM/Austroads urban saturation flow band ~1800-2050 veh/h/lane (dossier 04 6.1; 05 6 uses s=1800). No Newcastle stop-line survey exists, so the class band is swept.

#### `A.signals.scats.cycle_step_s`

The most the cycle length may move in ONE cycle. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.cycleStepS` · sweep role **uncertainty***

#### `A.signals.scats.ds_deadband`

The band around the target degree of saturation inside which the cycle is left alone. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.dsDeadband` · sweep role **uncertainty***

> **Sweep basis.** DECISIONS.md 9.88 declares 0.05 swept 0.02-0.10: the published SCATS descriptions establish that the cycle is not re-timed on every small departure from the target degree of saturation, but not the width of that band, so the interval is a chosen bracket of two fifths to twice the value. No observed spread.

#### `A.signals.scats.ds_smoothing`

Exponential smoothing weight on the newest cycle's measured degree of saturation. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.dsSmoothing` · sweep role **uncertainty***

> **Sweep basis.** DECISIONS.md 9.88 declares 0.5 swept 0.1-0.9: the filter exists in the real system and its constant is unpublished, so the interval spans nearly the whole admissible range, from a filter that barely reacts to one that nearly follows the last cycle. No observed spread.

#### `A.signals.scats.max_cycle_s`

Longest cycle the controller may choose - the upper end of the documented SCATS user limits (dossier 03/09). Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.maxCycleS` · sweep role **uncertainty***

#### `A.signals.scats.min_cycle_s`

Shortest cycle the controller may choose. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.minCycleS` · sweep role **uncertainty***

#### `A.signals.scats.target_degree_saturation`

The degree of saturation SCATS holds the CRITICAL (busiest) movement near by lengthening or shortening the cycle. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `scats.targetDegreeSaturation` · sweep role **uncertainty***

#### `A.signals.tsp.compensation_enabled`

Whether green borrowed for the tram is returned to the phase it came from in the next cycle. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.compensationEnabled` · sweep role **uncertainty***

> **Sweep basis.** The Melbourne machinery returns borrowed green to cut phases in the following cycle - without compensation the plan's long-run splits drift and any later adaptive layer pollutes its own statistics (dossier 05 8).

#### `A.signals.tsp.detection_distance_m`

How far upstream a tram is detected. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.detectionDistanceM` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: The standing S2b assumption (A2 tsp_detection_distance_m = 120); the Melbourne two-detector scheme puts the mid-link detector ~60 m past the previous stop, and 250 m is a whole corridor block. MATSim has no intra-link position, so detection is realised at the tram approach link boundary nearest this distance - an approximation the controller documents.

#### `A.signals.tsp.extension_window_s`

How long a green may be held for a detected tram. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.extensionWindowS` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: The standing S2b assumption (A2 tsp_max_extension_s = 12) bracketed by practice: short extensions ~5 s barely carry a tram through, ~20 s approaches a whole phase at the operated 72-81 s corridor cycles (PPSHCC-137 evidence).

#### `A.signals.tsp.lateness_threshold_s`

Schedule delay beyond which conditional priority grants; read only when A.signals.tsp.mode = conditional. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.latenessThresholdS` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Conditional (PTIPS-style) priority grants only to late trams; the operated threshold is not public (dossier 02 2 [gap]). 0 makes conditional identical to its unconditional parent; 300 s effectively disables priority at NLR headways.

#### `A.signals.tsp.mode`

The tram-priority controller's regime. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.mode` · sweep role **uncertainty***

> **Sweep basis.** The Melbourne/VicRoads tram-priority ladder (dossier 05 8): partial priority (green extension, the PU practice default) keeps nearly all tram benefit at a fraction of the cost to general traffic; extension_recall adds red truncation / phase recall (AU); conditional gates on lateness (PC/AC, PTIPS-faithful). Sweeping the mode replaces the scalar E.s2b.signal_delay_removed_share as the priority-aggressiveness axis on the explicit arm.

#### `A.signals.tsp.priority_budget_share`

The most green the controller may borrow for the tram in one cycle, as a share of cycle time. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***literature** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.priorityBudgetShare` · sweep role **uncertainty***

> **Sweep basis.** VicRoads partial-priority practice budgets priority phases at most 20% of the cycle, taken from the nominal split of the biggest competing phase (dossier 05 8). Swept around that operated value.

#### `A.signals.tsp.priority_group`

Which signal group the priority controller serves and watches for detections - the stage that carries the priority-detected transit vehicle. Adopted from the reference city and INERT here: A.signals.representation = "implicit_delay" switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***definition** · status **placeholder** · DECISIONS.md §9.202 · MATSim `tramPriority.priorityGroupId`*

#### `A.taxi.fleet_representation`

Taxi trips use vehicle proxies before finite-fleet dispatch is introduced. Moved from RUN.smoke.taxiFleet.representation on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `taxiFleet.representation`*

## Provisional hired-vehicle supply

*`cities/mumbai/registry/A_hired_fleet.json` - 6 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.hired.active_fraction` | `0.5` | fraction_of_registered_stock | `assumed` | 0.25 - 0.75 |
| `A.hired.categories` | `{"taxi": ["7a", "7b"], "auto_rickshaw": ["8"]}` | published_category_codes | `definition` | - |
| `A.hired.office_labels` | `["Mumbai (C)", "Mumbai (W)", "Mumbai (E)", "Borivali", "Thane", "Kalyan", "Vashi N.mumbai", "Vasai", "Panve...` | published_office_labels | `definition` | - |
| `B.hired_fleet.max_wait_s` | `900.0` | seconds | `assumed` | 300 - 1800 |
| `B.hired_fleet.representation` | `absent` | enum | `definition` | - |
| `B.hired_fleet.turnaround_s` | `300.0` | seconds | `assumed` | 0 - 900 |

#### `A.hired.active_fraction`

Provisional simultaneous service availability, before explicit cohort scaling. Not measured operating supply.

***assumed** · status **active** · DECISIONS.md §9.199 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad development proxy; no fleet calibration or scaling-equivalence claim.

#### `A.hired.categories`

Metered and luxury/tourist cabs form a broad taxi stock proxy; not all tourist cabs provide local hired trips.

***definition** · status **active** · DECISIONS.md §9.199*

#### `A.hired.office_labels`

Broad regional registration-stock proxy; office catchments do not match the historical research-population envelope exactly.

***definition** · status **active** · DECISIONS.md §9.199*

#### `B.hired_fleet.max_wait_s`

Provisional patience limit; a timed-out request aborts and receives native stuck scoring. Moved from RUN.smoke.hiredFleet.maxWaitSeconds on 21 September 2026 (9.204): the framework's key for the pooled hired fleet.

***assumed** · status **active** · DECISIONS.md §9.204 · MATSim `hiredFleet.maxWaitSeconds` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad development proxy; no fleet calibration or scaling-equivalence claim.

#### `B.hired_fleet.representation`

Whether hired road modes (taxi, auto-rickshaw) are served from a pooled queue of finite vehicles by mode (citysim.HiredFleetQueue, 9.199; `pooled_queue`, the counts in hired_fleet.json beside the scenario network) or not (`absent`, unlimited vehicle proxies - the control). Absent at the base; the run overlays that exercise the fleet declare pooled_queue. Moved from RUN.smoke.hiredFleet.representation on 21 September 2026 (9.204): the framework's key for the pooled hired fleet.

***definition** · status **active** · DECISIONS.md §9.204 · MATSim `hiredFleet.representation`*

#### `B.hired_fleet.turnaround_s`

Provisional unavailable turnaround after actual arrival. No spatial dispatch or empty road movements. Moved from RUN.smoke.hiredFleet.turnaroundSeconds on 21 September 2026 (9.204): the framework's key for the pooled hired fleet.

***assumed** · status **active** · DECISIONS.md §9.204 · MATSim `hiredFleet.turnaroundSeconds` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad development proxy; no fleet calibration or scaling-equivalence claim.

## Regional bus evidence integration

*`cities/mumbai/registry/A_regional_buses.json` - 7 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.regional_bus.agency_urls` | `{"NMMT": "https://nmmtservice.infinium.management", "MBMT": "https://mbmc.gov.in"}` | URLs | `definition` | - |
| `A.regional_bus.allocation_day_label` | `Monday.to.Friday.` | source_label | `definition` | - |
| `A.regional_bus.max_published_segment_s` | `3600` | seconds | `assumed` | 1800 - 7200 |
| `A.regional_bus.running_time` | `{"speed_ms": 8.333333333333334, "distance_multiplier": 1.25, "dwell_s": 20, "maximum_delay_ratio": 4}` | metres_per_second_ratio_seconds | `assumed` | plus/minus 50% |
| `A.regional_bus.service_window_s` | `[18000, 86400]` | seconds_after_midnight | `assumed` | 14400 - 90000 |
| `A.regional_bus.terminal_layover_s` | `300` | seconds_per_directed_pattern | `assumed` | 120 - 900 |
| `A.regional_bus.timezone` | `Asia/Kolkata` | IANA_timezone | `definition` | - |

#### `A.regional_bus.agency_urls`

Operator publication attribution in the generated GTFS agency table.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.regional_bus.allocation_day_label`

Exact weekday label in acquired MBMT municipal route-bus allocation cells. Sum route cells; do not substitute the inconsistent printed subtotal.

***definition** · status **active** · DECISIONS.md §9.187*

#### `A.regional_bus.max_published_segment_s`

Reject implausibly long single-stop clock differences; negative/zero clock differences are derived from other trips or geometry.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service sensitivity, not calibrated ridership or corridor precision.

#### `A.regional_bus.running_time`

Geographic minimum running time and dwell where published segment times are unusable; longer usable median published intervals take precedence. Mapped-path feasibility is checked by the native run preparation. Published segment medians exceeding four times the distance-derived interval are flagged and replaced by geographic derivation; source clocks remain unchanged.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service sensitivity, not calibrated ridership or corridor precision.

#### `A.regional_bus.service_window_s`

Provisional MBMT departure window. NMMT retains acquired departure clocks.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service sensitivity, not calibrated ridership or corridor precision.

#### `A.regional_bus.terminal_layover_s`

Terminal allowance in the pooled MBMT fleet-hours frequency derivation; not observed vehicle circulation.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad service sensitivity, not calibrated ridership or corridor precision.

#### `A.regional_bus.timezone`

Local clock basis for published departures.

***definition** · status **active** · DECISIONS.md §9.187*

## Transit vehicle passenger capacities per operated configuration (9.206)

*`cities/mumbai/registry/A_transit_fleet.json` - 30 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.transit.bus_capacity_seated` | `36` | persons_per_vehicle | `observed` | - |
| `A.transit.bus_capacity_standing` | `30` | persons_per_vehicle | `assumed` | 20 - 45 |
| `A.transit.ferry_borivali_esselworld_capacity_seated` | `423` | persons_per_vehicle | `measured` | 186 - 423 |
| `A.transit.ferry_capacity_standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.transit.ferry_creek_capacity_seated` | `100` | persons_per_vehicle | `observed` | - |
| `A.transit.ferry_elephanta_capacity_seated` | `80` | persons_per_vehicle | `observed` | - |
| `A.transit.ferry_gateway_mandwa_capacity_seated` | `390` | persons_per_vehicle | `measured` | 80 - 390 |
| `A.transit.ferry_gorai_borivali_capacity_seated` | `290` | persons_per_vehicle | `measured` | 186 - 290 |
| `A.transit.ferry_m2m_mandwa_capacity_seated` | `780` | persons_per_vehicle | `measured` | 520 - 780 |
| `A.transit.ferry_marve_manori_capacity_seated` | `313` | persons_per_vehicle | `measured` | 201 - 313 |
| `A.transit.ferry_versova_madh_capacity_seated` | `60` | persons_per_vehicle | `measured` | 37 - 70 |
| `A.transit.ferry_wharf_mora_capacity_seated` | `1635` | persons_per_vehicle | `measured` | 300 - 1635 |
| `A.transit.fleet_assignment_mode` | `explicit_vehicle` | enum | `definition` | - |
| `A.transit.fleet_profiles` | `{"rail_emu_12car": {"base_type": "Rail", "seats_field": "A.transit.rail_capacity_seated", "standing_field":...` | profile_table | `definition` | - |
| `A.transit.metro_beml_capacity_seated` | `239` | persons_per_vehicle | `derived` | derived: round(A.transit.metro_beml_capacity_total x A.transit.metro_seated_sha |
| `A.transit.metro_beml_capacity_standing` | `1561` | persons_per_vehicle | `derived` | derived: A.transit.metro_beml_capacity_total - A.transit.metro_beml_capacity_se |
| `A.transit.metro_beml_capacity_total` | `1800` | persons_per_vehicle | `observed` | - |
| `A.transit.metro_line1_capacity_seated` | `200` | persons_per_vehicle | `derived` | derived: round(A.transit.metro_line1_capacity_total x A.transit.metro_seated_sh |
| `A.transit.metro_line1_capacity_standing` | `1300` | persons_per_vehicle | `derived` | derived: A.transit.metro_line1_capacity_total - A.transit.metro_line1_capacity_ |
| `A.transit.metro_line1_capacity_total` | `1500` | persons_per_vehicle | `observed` | - |
| `A.transit.metro_line3_capacity_seated` | `399` | persons_per_vehicle | `derived` | derived: round(A.transit.metro_line3_capacity_total x A.transit.metro_seated_sh |
| `A.transit.metro_line3_capacity_standing` | `2601` | persons_per_vehicle | `derived` | derived: A.transit.metro_line3_capacity_total - A.transit.metro_line3_capacity_ |
| `A.transit.metro_line3_capacity_total` | `3000` | persons_per_vehicle | `observed` | - |
| `A.transit.metro_navi_capacity_seated` | `150` | persons_per_vehicle | `literature` | 140 - 160 |
| `A.transit.metro_navi_capacity_standing` | `950` | persons_per_vehicle | `derived` | derived: A.transit.metro_navi_capacity_total - A.transit.metro_navi_capacity_se |
| `A.transit.metro_navi_capacity_total` | `1100` | persons_per_vehicle | `literature` | 1000 - 1200 |
| `A.transit.metro_seated_share` | `0.133` | ratio | `literature` | 0.1 - 0.25 |
| `A.transit.rail_capacity_seated` | `1168` | persons_per_vehicle | `literature` | 1028 - 1168 |
| `A.transit.rail_capacity_standing` | `3816` | persons_per_vehicle | `derived` | derived: A.transit.rail_capacity_total - A.transit.rail_capacity_seated = 4984  |
| `A.transit.rail_capacity_total` | `4984` | persons_per_vehicle | `literature` | 3504 - 5964 |

#### `A.transit.bus_capacity_seated`

Seats in one city bus: 'Min 36 + Driver' for the 12 m electric buses in the MBMT gross-cost contract (mbmt_contract_capacities.csv), the one operator-side specification in the package; BEST's 12 m Tata order is 35-seater and the 9 m midi 31 (bus_manufacturer_seating_claims.csv). One profile serves every operator (BEST, NMMT, MBMT and the rest of the regional feed) until a per-operator vehicle assignment is evidenced.

***observed** · status **active** · DECISIONS.md §9.206*

#### `A.transit.bus_capacity_standing`

Standing places in one city bus. Assumed and swept: the only transit capacity in this file that no publication states.

***assumed** · status **active** · DECISIONS.md §9.206 · sweep role **uncertainty***

> **Sweep basis.** No operator or manufacturer in the package states a standing capacity (bus_capacity_evidence_audit.json: 'All standing capacities remain missing'); the MBMT contract defers it to the AIS-052 bus body code's area rule (0.125 square metres a standee), whose input - the net standing floor area of each body - is not published, so the derivation GOAL.md requirement 6 asks for is blocked on that one unpublished figure and this is the fallback it permits. 30 is a 12 m low-floor city bus at the AIS-052 rule on the 4-6 square metres of aisle and platform such a body leaves beside 36 seats; the bracket runs from a 9 m midi (20) to a licensed-capacity 12 m body (45). Replaced the moment a body drawing or a licence certificate is acquired.

#### `A.transit.ferry_borivali_esselworld_capacity_seated`

Passengers one vessel on the borivali-esselworld crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory route 5: 'Fair 423'; the foul-season capacity is not printed, so the sweep floor is the neighbouring Gorai crossing's foul figure (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.ferry_capacity_standing`

Standing places on a licensed passenger launch: none, the directory's capacity is the licensed passenger count.

***definition** · status **active** · DECISIONS.md §9.206*

#### `A.transit.ferry_creek_capacity_seated`

Passengers one Vasai - Bhayander creek ferry carries: 100 in the Maharashtra Maritime Board's route service directory (water_service_directory.csv, route 16); the mapped OSM ferry relation 16777766 is that crossing (its endpoints at 19.339 N 72.844 E and 19.342 N 72.841 E).

***observed** · status **active** · DECISIONS.md §9.206*

#### `A.transit.ferry_elephanta_capacity_seated`

Passengers one Gateway of India - Elephanta launch carries: 'Min. 40 Max. 80' in the Maharashtra Maritime Board's route service directory (water_service_directory.csv, route 10); the maximum is the vessel's capacity. Launches carry seated passengers.

***observed** · status **active** · DECISIONS.md §9.206*

#### `A.transit.ferry_gateway_mandwa_capacity_seated`

Passengers one vessel on the gateway-mandwa crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory route 11: 'Min. 80 Max. 390' - the largest vessel, swept to the smallest (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.ferry_gorai_borivali_capacity_seated`

Passengers one vessel on the gorai-borivali crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory route 4: 'Fair 290 / Foul 186' (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.ferry_m2m_mandwa_capacity_seated`

Passengers one vessel on the m2m-mandwa crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory route 14 (the Ro-Ro): '780/520' passengers (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.ferry_marve_manori_capacity_seated`

Passengers one vessel on the marve-manori crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory route 3: 'Fair 313 / Foul 201' - the fair-season vessel for the base weekday, the foul-season one the sweep floor (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.ferry_versova_madh_capacity_seated`

Passengers one vessel on the versova-madh crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory routes 1 and 2 (Versova-Madh, Madh-Versova): '37 (fair season)' and '60-70 (fair season)' - the two directions' printed capacities; the larger vessel's lower figure, swept over both (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.ferry_wharf_mora_capacity_seated`

Passengers one vessel on the wharf-mora crossing carries, from the Maritime Board's directory; launches carry seated passengers.

***measured** · status **active** · DECISIONS.md §9.207 · sweep role **measurement***

> **Sweep basis.** directory route 8: '1635' as printed - larger than any launch on the Mora run, so read as the licensed capacity of the route's vessels together; the sweep floor is a single large launch (water_service_directory.csv, the Maharashtra Maritime Board's route service directory, mmb_routes).

#### `A.transit.fleet_assignment_mode`

How the run-input assembly resolves transit passenger capacities (docs/transit_fleet.md). explicit_vehicle: every mapped vehicle is assigned a capacity profile by build_transit_fleet.py from the route relation it serves, so a 12-car EMU, a 4-car Line 1 train, a 6-car BEML train, an 8-car Line 3 train, a 3-car Navi Mumbai train, a creek ferry and a city bus each carry their own evidenced capacity. Until 9.206 the assembly copied the mapper's own defaults (Bus 70, Rail 400, Subway 300, Ferry 250 seats, no standing room), so a suburban train that carries about 5,000 was simulated as 400 seats.

***definition** · status **active** · DECISIONS.md §9.206*

#### `A.transit.fleet_profiles`

The capacity profiles build_transit_fleet.py assigns to the mapped vehicles (docs/transit_fleet.md): each names the mapper's base type it clones, the two registry fields that carry its seats and standing places, and EITHER the transport mode every line of that mode falls to (rail, bus) OR the OSM route relations it serves, read from the transit line id the feed builder writes as BASE_<relation>_<direction> (build_baseline_transit_feed.py). The relation ids are the identifiers of the mapped lines - Line 1 (3808111, 7684032), Lines 2A/2B/7/9 on BEML 6-car stock, Line 3 (7898597, 17876723), Navi Mumbai Line 1 (16533435, 16533436), the Gateway-Elephanta launch (19764205) and the Vasai-Bhayander creek ferry (16777766) - not values; a line with no profile refuses the build. The mapper typed the Central main-line and the Nerul-Uran patterns as their own base types (C, U) beside Rail; the three rail profiles carry one capacity and differ only in the base type each clones, because an assignment cannot change a vehicle's mapped type. A profile may instead name the Maritime Board directory routes it serves (`directory_routes`): the feed builder writes those lines as BASE_MMB_<directory route>_<direction> (9.207).

***definition** · status **active** · DECISIONS.md §9.206*

#### `A.transit.metro_beml_capacity_seated`

Seats in one BEML 6-car train (Lines 2A, 2B, 7, 9), by Line 1's seated share.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_beml_capacity_total`, `A.transit.metro_seated_share`: round(A.transit.metro_beml_capacity_total x A.transit.metro_seated_share) = round(1800 x 0.133) = 239

#### `A.transit.metro_beml_capacity_standing`

Standing places in one BEML 6-car train.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_beml_capacity_total`, `A.transit.metro_beml_capacity_seated`: A.transit.metro_beml_capacity_total - A.transit.metro_beml_capacity_seated = 1800 - 239

#### `A.transit.metro_beml_capacity_total`

Passengers one 6-car BEML train carries on Lines 2A, 2B, 7 and 9: 300 a car in PIB's 22 November 2018 order release (metro_fleet_publication_claims.csv, 'nominal_unspecified_density') x 6 cars. The density the 300 is stated at is not published.

***observed** · status **active** · DECISIONS.md §9.206*

#### `A.transit.metro_line1_capacity_seated`

Seats in one Line 1 train.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_line1_capacity_total`, `A.transit.metro_seated_share`: round(A.transit.metro_line1_capacity_total x A.transit.metro_seated_share) = round(1500 x 0.133) = 200

#### `A.transit.metro_line1_capacity_standing`

Standing places in one Line 1 train.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_line1_capacity_total`, `A.transit.metro_line1_capacity_seated`: A.transit.metro_line1_capacity_total - A.transit.metro_line1_capacity_seated = 1500 - 200

#### `A.transit.metro_line1_capacity_total`

Passengers one Line 1 (Versova-Ghatkopar, MMOPL) 4-coach train carries: 'Train Capacity is 1500 commuters in a 4 coach train' on the operator's Features page (catalogue mmopl_features_page).

***observed** · status **active** · DECISIONS.md §9.206*

#### `A.transit.metro_line3_capacity_seated`

Seats in one Line 3 train, by Line 1's seated share.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_line3_capacity_total`, `A.transit.metro_seated_share`: round(A.transit.metro_line3_capacity_total x A.transit.metro_seated_share) = round(3000 x 0.133) = 399

#### `A.transit.metro_line3_capacity_standing`

Standing places in one Line 3 train.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_line3_capacity_total`, `A.transit.metro_line3_capacity_seated`: A.transit.metro_line3_capacity_total - A.transit.metro_line3_capacity_seated = 3000 - 399

#### `A.transit.metro_line3_capacity_total`

Passengers one Line 3 (Aqua Line, MMRCL) 8-car Alstom train carries: 'at least 3,000' in Alstom's 5 October 2024 opening release (metro_fleet_publication_claims.csv). The lower bound is used; the density is not published.

***observed** · status **active** · DECISIONS.md §9.206*

#### `A.transit.metro_navi_capacity_seated`

Seats in one Navi Mumbai Metro 3-car train.

***literature** · status **active** · DECISIONS.md §9.206 · sweep role **uncertainty***

> **Sweep basis.** 150 seats a 3-car train in the trade-press report of the CRRC trains' entry into service (rollingstockworld_navi_mumbai_crrc); the bracket is one longitudinal bench a car either way.

#### `A.transit.metro_navi_capacity_standing`

Standing places in one Navi Mumbai Metro train.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.metro_navi_capacity_total`, `A.transit.metro_navi_capacity_seated`: A.transit.metro_navi_capacity_total - A.transit.metro_navi_capacity_seated = 1100 - 150

#### `A.transit.metro_navi_capacity_total`

Passengers one Navi Mumbai Metro Line 1 (Belapur-Pendhar) 3-car train carries.

***literature** · status **active** · DECISIONS.md §9.206 · sweep role **uncertainty***

> **Sweep basis.** 'each train can accommodate 1,100 people, has 150 seats' in the trade-press report of the CRRC trains' entry into service (catalogue rollingstockworld_navi_mumbai_crrc); the project profile railway_technology_navi_mumbai_metro confirms the 3-car CRRC formation but states no capacity; CIDCO and Maha Metro publish none in the acquired reports. The bracket is the rounding the source states.

#### `A.transit.metro_seated_share`

The share of a metro train's published passenger capacity that is seated, from the Mumbai line whose split is reported by its operator (Line 1); Navi Mumbai's reported split (150 of 1,100) agrees. Applied to the other lines' published totals to derive their seats and standing places; superseded line by line as an operator publishes a split.

***literature** · status **active** · DECISIONS.md §9.206 · sweep role **uncertainty***

> **Sweep basis.** Line 1's operator states a 4-coach train carries 1,500 (reliancemumbaimetro.com, Features) and its 2019 seat-removal notice, as reported, left 1,300 standees - 200 seats, 0.133 of the load; 48-52 longitudinal seats a coach is the reported range. No Mumbai metro operator publishes the seated/standing split of the BEML 6-car, or the Alstom 8-car trains (metro_fleet_publication_claims.csv: 'not_stated_in_publication'), so Line 1's share is applied to their published totals until one does (Navi Mumbai's 150 of 1,100, 0.136, is reported and agrees); 0.25 is the upper end of longitudinal-seat metro cars at 6 standees a square metre.

#### `A.transit.rail_capacity_seated`

Seats in one suburban EMU rake (every Mumbai Suburban Railway and MEMU pattern in the provisional feed). Twelve-car non-AC formation: 1,168 (IRIMEE). The MEMU patterns (Diva-Panvel, Diva-Roha) are 3 of 31 rail patterns and carry the same profile for want of a MEMU figure; a 15-car formation (54 marked services, cr_service_markers.csv) is not yet assigned per departure.

***literature** · status **active** · DECISIONS.md §9.206 · sweep role **uncertainty***

> **Sweep basis.** 1,168 is the 12-car non-AC rake's seating in Indian Railways' own EMU primer (IRIMEE, Basics of EMU: 'A 12-car train can seat 1,168 and accommodate 2,336 standees'); 1,028 is the 12-car AC rake's seating in PIB's 24 December 2017 release (suburban_first_ac_capacity_2017.csv). The feed does not yet say which departures run AC stock (13 of 238 daily rakes in 2024-25, economic_survey_suburban_rail_controls.csv), so every suburban departure carries the non-AC figure.

#### `A.transit.rail_capacity_standing`

Standing places in one suburban EMU rake: the rake's carried capacity less its seats. 3,816 at 12 cars; the sample scaler multiplies it by RUN.sample.fraction.

***derived** · status **active** · DECISIONS.md §9.206*

> **Derived from** `A.transit.rail_capacity_total`, `A.transit.rail_capacity_seated`: A.transit.rail_capacity_total - A.transit.rail_capacity_seated = 4984 - 1168

#### `A.transit.rail_capacity_total`

Passengers one suburban EMU rake carries when boarding is refused (seated plus standing): the Siemens 12-car rake's stated capacity, the middle of the three published figures. Not the design capacity (3,504, at which every peak train would deny boarding to a third of its real load) and not the newest rake's (5,964).

***literature** · status **active** · DECISIONS.md §9.206 · sweep role **uncertainty***

> **Sweep basis.** The three published capacities of a 12-car rake in Indian Railways' EMU primer (IRIMEE, Basics of EMU): 3,504 is the design capacity (1,168 seated + 2,336 standees), 4,984 the stated capacity of the Siemens 12-car rake and 5,964 the Bombardier rake's (which PIB 2017 splits as 1,028 seated + 4,936 standing for the AC rake). MATSim denies boarding at seats + standing, so the value is the load a rake physically carries at peak, not the comfort design; the same primer records 5,000 in a 9-car rake at super-dense crush.

## Vehicle types per routed mode (RUN.qsim.mode_vehicle_fields; 9.204)

*`cities/mumbai/registry/A_vehicles.json` - 54 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.vehicle.auto_rickshaw.length_m` | `3.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.auto_rickshaw.max_speed_ms` | `15.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.auto_rickshaw.pce` | `0.7` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.auto_rickshaw.seats` | `3` | persons_per_vehicle | `assumed` | 1 - 5 |
| `A.vehicle.auto_rickshaw.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.auto_rickshaw.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.bike.length_m` | `2.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.bike.max_speed_ms` | `4.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.bike.pce` | `0.2` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.bike.seats` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.bike.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.bike.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.car.length_m` | `5.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.car.max_speed_ms` | `30.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.car.pce` | `1.0` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.car.seats` | `4` | persons_per_vehicle | `assumed` | 1 - 6 |
| `A.vehicle.car.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.car.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.freight_rail.length_m` | `700.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.freight_rail.max_speed_ms` | `16.666666666666668` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.freight_rail.pce` | `93.33333333333333` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.freight_rail.seats` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.freight_rail.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.freight_rail.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.motorbike.length_m` | `2.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.motorbike.max_speed_ms` | `25.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.motorbike.pce` | `0.4` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.motorbike.seats` | `1` | persons_per_vehicle | `assumed` | 1 - 3 |
| `A.vehicle.motorbike.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.motorbike.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.ride.length_m` | `5.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.ride.max_speed_ms` | `30.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.ride.pce` | `1.0` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.ride.seats` | `4` | persons_per_vehicle | `assumed` | 1 - 6 |
| `A.vehicle.ride.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.ride.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.taxi.length_m` | `5.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.taxi.max_speed_ms` | `30.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.taxi.pce` | `1.0` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.taxi.seats` | `4` | persons_per_vehicle | `assumed` | 1 - 6 |
| `A.vehicle.taxi.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.taxi.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.truck.length_m` | `12.0` | m | `assumed` | plus/minus 50% |
| `A.vehicle.truck.max_speed_ms` | `20.0` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.truck.pce` | `2.5` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.truck.seats` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.truck.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.truck.width_m` | `1.0` | m | `definition` | - |
| `A.vehicle.walk.length_m` | `0.5` | m | `assumed` | plus/minus 50% |
| `A.vehicle.walk.max_speed_ms` | `1.2` | m/s | `assumed` | plus/minus 50% |
| `A.vehicle.walk.pce` | `0.1` | passenger_car_equivalents | `assumed` | plus/minus 50% |
| `A.vehicle.walk.seats` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.walk.standing` | `0` | persons_per_vehicle | `definition` | - |
| `A.vehicle.walk.width_m` | `1.0` | m | `definition` | - |

#### `A.vehicle.auto_rickshaw.length_m`

Length of a auto_rickshaw in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.auto_rickshaw.max_speed_ms`

Speed cap of a auto_rickshaw, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.auto_rickshaw.pce`

Road space a auto_rickshaw consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.auto_rickshaw.seats`

Passenger seats of a auto_rickshaw excluding the driver.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** The permitted passenger seating of the class under the Maharashtra Motor Vehicles Rules as commonly stated (auto-rickshaw 3, taxi and car 4, motorcycle 1 pillion); to be pinned to the transcribed permit source. Inert while B.ride.pairing_enabled is false and the hired fleet counts vehicles, not seats.

#### `A.vehicle.auto_rickshaw.standing`

Standing places in a auto_rickshaw: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.auto_rickshaw.width_m`

Width of a auto_rickshaw, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.bike.length_m`

Length of a bike in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.bike.max_speed_ms`

Speed cap of a bike, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.bike.pce`

Road space a bike consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.bike.seats`

Passenger seats of a bike: none, it carries no passenger.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.bike.standing`

Standing places in a bike: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.bike.width_m`

Width of a bike, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.car.length_m`

Length of a car in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.car.max_speed_ms`

Speed cap of a car, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.car.pce`

Road space a car consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.car.seats`

Passenger seats of a car excluding the driver.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** The permitted passenger seating of the class under the Maharashtra Motor Vehicles Rules as commonly stated (auto-rickshaw 3, taxi and car 4, motorcycle 1 pillion); to be pinned to the transcribed permit source. Inert while B.ride.pairing_enabled is false and the hired fleet counts vehicles, not seats.

#### `A.vehicle.car.standing`

Standing places in a car: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.car.width_m`

Width of a car, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.freight_rail.length_m`

Length of a freight_rail in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.freight_rail.max_speed_ms`

Speed cap of a freight_rail, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.freight_rail.pce`

Road space a freight_rail consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.freight_rail.seats`

Passenger seats of a freight_rail: none, it carries no passenger.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.freight_rail.standing`

Standing places in a freight_rail: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.freight_rail.width_m`

Width of a freight_rail, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.motorbike.length_m`

Length of a motorbike in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.motorbike.max_speed_ms`

Speed cap of a motorbike, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.motorbike.pce`

Road space a motorbike consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.motorbike.seats`

Passenger seats of a motorbike excluding the driver.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** The permitted passenger seating of the class under the Maharashtra Motor Vehicles Rules as commonly stated (auto-rickshaw 3, taxi and car 4, motorcycle 1 pillion); to be pinned to the transcribed permit source. Inert while B.ride.pairing_enabled is false and the hired fleet counts vehicles, not seats.

#### `A.vehicle.motorbike.standing`

Standing places in a motorbike: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.motorbike.width_m`

Width of a motorbike, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.ride.length_m`

Length of a ride in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.ride.max_speed_ms`

Speed cap of a ride, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.ride.pce`

Road space a ride consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.ride.seats`

Passenger seats of a ride excluding the driver.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** The permitted passenger seating of the class under the Maharashtra Motor Vehicles Rules as commonly stated (auto-rickshaw 3, taxi and car 4, motorcycle 1 pillion); to be pinned to the transcribed permit source. Inert while B.ride.pairing_enabled is false and the hired fleet counts vehicles, not seats.

#### `A.vehicle.ride.standing`

Standing places in a ride: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.ride.width_m`

Width of a ride, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.taxi.length_m`

Length of a taxi in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.taxi.max_speed_ms`

Speed cap of a taxi, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.taxi.pce`

Road space a taxi consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.taxi.seats`

Passenger seats of a taxi excluding the driver.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** The permitted passenger seating of the class under the Maharashtra Motor Vehicles Rules as commonly stated (auto-rickshaw 3, taxi and car 4, motorcycle 1 pillion); to be pinned to the transcribed permit source. Inert while B.ride.pairing_enabled is false and the hired fleet counts vehicles, not seats.

#### `A.vehicle.taxi.standing`

Standing places in a taxi: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.taxi.width_m`

Width of a taxi, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.truck.length_m`

Length of a truck in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.truck.max_speed_ms`

Speed cap of a truck, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.truck.pce`

Road space a truck consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.truck.seats`

Passenger seats of a truck: none, it carries no passenger.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.truck.standing`

Standing places in a truck: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.truck.width_m`

Width of a truck, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.walk.length_m`

Length of a walk in the queue, metres. Provisional (9.187), carried from the per-launch vehicle writer of the city's own launcher.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline vehicle body; not measured for this city (was RUN.smoke.vehicle_length_m).

#### `A.vehicle.walk.max_speed_ms`

Speed cap of a walk, metres per second; each link's own limit applies below it. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional per-mode movement cap; not calibrated to observed speeds (was RUN.smoke.vehicle_speed_ms).

#### `A.vehicle.walk.pce`

Road space a walk consumes, in passenger-car equivalents. Provisional (9.187).

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** Provisional passenger-car equivalent; the mixed-traffic PCE of this city is to be taken from the arterial capacity literature acquired (extract_arterial_capacity_literature.py) before calibration (was RUN.smoke.vehicle_pcu).

#### `A.vehicle.walk.seats`

Passenger seats of a walk: none, it carries no passenger.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.walk.standing`

Standing places in a walk: none, a road vehicle carries seated passengers only.

***definition** · status **active** · DECISIONS.md §9.204*

#### `A.vehicle.walk.width_m`

Width of a walk, metres: MATSim's own default vehicle width. The queue runs on length and PCE; the width is read by the visualiser and the lane model only, neither of which this model uses.

***definition** · status **active** · DECISIONS.md §9.204*

## Provisional daily activities and mapped destinations

*`cities/mumbai/registry/B_baseline_activities.json` - 12 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `B.activities.departure_spread_s` | `3600` | seconds | `assumed` | 900 - 7200 |
| `B.activities.discretionary_departure_s` | `39600` | seconds_after_midnight | `assumed` | 32400 - 50400 |
| `B.activities.distance_scale_m` | `{"work": 12000, "education": 2500, "shopping": 3000, "social": 4000, "leisure": 6000}` | metres | `assumed` | plus/minus 50% |
| `B.activities.home_break_s` | `1800` | seconds | `assumed` | 300 - 5400 |
| `B.activities.location_tags` | `{"work": {"office": ["*"], "shop": ["*"], "amenity": ["school", "college", "university", "hospital", "clini...` | OSM_tag_values | `definition` | - |
| `B.activities.max_optional_tours` | `2` | tours_per_person_day | `assumed` | 1 - 3 |
| `B.activities.optional_min_age_years` | `18` | years | `definition` | - |
| `B.activities.out_of_home_fraction` | `{"shopping": 0.5, "social": 0.35, "leisure": 0.2}` | probabilities | `assumed` | plus/minus 50% |
| `B.activities.out_of_home_time_fraction` | `{"shopping": 0.25, "social": 0.5, "leisure": 0.5}` | fractions | `assumed` | plus/minus 50% |
| `B.activities.poi_probability` | `{"work": 0.75, "education": 0.9, "shopping": 0.9, "social": 0.6, "leisure": 0.9}` | probabilities | `assumed` | plus/minus 50% |
| `B.activities.seed` | `20260810` | integer_seed | `definition` | - |
| `B.activities.time_use_activities` | `{"shopping": "Unpaid domestic services for household members", "social": "Socializing and communication, co...` | source_activity_labels | `definition` | - |

#### `B.activities.departure_spread_s`

Spread around the discretionary-only first-departure anchor.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.discretionary_departure_s`

Departure anchor for adults without a work or education tour.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.distance_scale_m`

Provisional distance decay for purpose-specific destination opportunity choice.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.home_break_s`

Minimum modelled at-home interval between successive tours; departure follows actual return travel time.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.location_tags`

Positive mapping of acquired point and area tags to modelled activity purposes; each location is a proxy, not measured attraction capacity.

***definition** · status **active** · DECISIONS.md §9.194*

#### `B.activities.max_optional_tours`

Provisional limit on discretionary tours, selected without imposing any mode target.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.optional_min_age_years`

Independent discretionary tours are adult-only until household escort schedules are represented.

***definition** · status **active** · DECISIONS.md §9.193*

#### `B.activities.out_of_home_fraction`

Assumed proportion of benchmark activity participants making an out-of-home outing. Applied to existing adults as a provisional proxy; not an observed adult trip rate.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.out_of_home_time_fraction`

Assumed allocation of benchmark per-participant minutes to one out-of-home episode; minutes include other activities within the source division.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.poi_probability`

Provisional mixture of mapped point opportunities and historical zone proxies. Retains demand where point coverage is incomplete.

***assumed** · status **active** · DECISIONS.md §9.193 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad activity model; not inferred trip diaries or fitted mode shares. Validate out-of-home demand and location coverage separately.

#### `B.activities.seed`

Deterministic activities stream; the existing resident cohort is read unchanged.

***definition** · status **active** · DECISIONS.md §9.193*

#### `B.activities.time_use_activities`

State time-use benchmark rows. These broad divisions include in-home activity, and are not trip purposes measured locally.

***definition** · status **active** · DECISIONS.md §9.193*

## Provisional behavioural baseline population

*`cities/mumbai/registry/B_baseline_demand.json` - 15 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `B.baseline.activity_duration_s` | `{"work": 28800, "education": 21600, "other": 3600}` | seconds | `assumed` | 1800 - 36000 |
| `B.baseline.activity_start_s` | `{"work": 32400, "education": 28800, "other": 39600}` | seconds_after_midnight | `assumed` | 21600 - 50400 |
| `B.baseline.adult_age_years` | `18` | years | `definition` | - |
| `B.baseline.departure_spread_s` | `3600` | seconds | `assumed` | 900 - 7200 |
| `B.baseline.gravity_distance_scale_m` | `{"work": 12000, "education": 2500, "other": 4000}` | metres | `assumed` | 1000 - 30000 |
| `B.baseline.income_log_sigma` | `0.7` | dimensionless | `assumed` | 0.3 - 1.2 |
| `B.baseline.income_median_monthly_inr` | `30000` | INR/month | `assumed` | 10000 - 90000 |
| `B.baseline.income_minimum_monthly_inr` | `3000` | INR/month | `assumed` | 1000 - 10000 |
| `B.baseline.initial_choice_modes` | `["walk", "pt", "car", "bike", "motorbike", "taxi", "ride", "auto_rickshaw"]` | mode_names | `definition` | - |
| `B.baseline.licence_given_vehicle_probability` | `0.8` | probability | `assumed` | 0.5 - 1 |
| `B.baseline.open_age_upper_years` | `95` | years | `assumed` | 85 - 105 |
| `B.baseline.persons` | `1000` | persons | `definition` | - |
| `B.baseline.school_min_age_years` | `6` | years | `assumed` | 5 - 7 |
| `B.baseline.seed` | `20260810` | integer_seed | `definition` | - |
| `B.baseline.work_max_age_years` | `65` | years | `assumed` | 60 - 75 |

#### `B.baseline.activity_duration_s`

Provisional activity durations.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.activity_start_s`

Provisional activity departure anchors.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.adult_age_years`

Baseline adult motor-vehicle eligibility threshold.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.baseline.departure_spread_s`

Uniform spread either side of the departure anchor.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.gravity_distance_scale_m`

Provisional destination distance decay by activity; resident workers proxy employment locations.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.income_log_sigma`

Provisional dispersion of personal monthly budgets.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.income_median_monthly_inr`

Provisional personal budget distribution, not observed income.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.income_minimum_monthly_inr`

Positive minimum personal budget for scoring stability.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.initial_choice_modes`

Unbiased exploration among personally available alternatives; no target mode shares used.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.baseline.licence_given_vehicle_probability`

Provisional adult driving eligibility conditional on household vehicle access.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.open_age_upper_years`

Upper support of the census open-ended age band.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.persons`

Small representative-person smoke population; not a calibrated full-city sample or experiment arm.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.baseline.school_min_age_years`

School activity starts at this provisional age.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

#### `B.baseline.seed`

Deterministic master seed.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.baseline.work_max_age_years`

Provisional age boundary for employed-person activity generation.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural baseline; sensitivity range, not an observed joint distribution.

## Provisional port freight background

*`cities/mumbai/registry/B_baseline_freight.json` - 9 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `B.freight.car_equivalent_movements_per_person_day` | `1.0` | vehicle_movements_per_person_day | `assumed` | plus/minus 50% |
| `B.freight.gate_axes` | `["north", "east"]` | projected_extent_directions | `definition` | - |
| `B.freight.goods_count_classes` | `["LCV", "Trucks"]` | published_class_labels | `definition` | - |
| `B.freight.movement_window_s` | `[0, 86400]` | seconds_after_midnight | `assumed` | plus/minus 50% |
| `B.freight.port_osm_node_id` | `1650416453` | OSM_node_id | `observed` | - |
| `B.freight.port_snap_limit_m` | `10000` | metres | `assumed` | plus/minus 50% |
| `B.freight.rake_movements_per_handled_rake` | `2.0` | movements_per_handled_rake | `assumed` | plus/minus 50% |
| `B.freight.reference_car_class` | `Cars` | published_class_label | `definition` | - |
| `B.freight.seed` | `20260810` | integer_seed | `definition` | - |

#### `B.freight.car_equivalent_movements_per_person_day`

Smoke intensity proxy for applying the observed classified-site goods/car ratio to the explicit small resident population.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional background freight sensitivity; not a calibrated regional freight forecast.

#### `B.freight.gate_axes`

Research-network extremities proxy external gates; they are not observed freight destinations.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.freight.goods_count_classes`

Use unambiguous goods groups; the mixed Others/MAV group is excluded.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.freight.movement_window_s`

Provisional all-day release window; actual dispatch and road time restrictions still require integration.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional background freight sensitivity; not a calibrated regional freight forecast.

#### `B.freight.port_osm_node_id`

Acquired OSM locality point named Jawaharlal Nehru Port Trust; nearest connected modal link is a provisional port access anchor.

***observed** · status **active** · DECISIONS.md §9.187*

#### `B.freight.port_snap_limit_m`

Fail if the port locality is too far from a connected modal network; snapping is a provisional access representation.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional background freight sensitivity; not a calibrated regional freight forecast.

#### `B.freight.rake_movements_per_handled_rake`

Stationary port-operation proxy: one inbound and one outbound movement per handled rake; handled-day reports are not themselves movement counts.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional background freight sensitivity; not a calibrated regional freight forecast.

#### `B.freight.reference_car_class`

Denominator of the historical goods/car ratio.

***definition** · status **active** · DECISIONS.md §9.187*

#### `B.freight.seed`

Fixed background movement seed.

***definition** · status **active** · DECISIONS.md §9.187*

## Framework run-side fields: moved from the private baseline namespace or adopted from the reference city (9.202)

*`cities/mumbai/registry/B_framework.json` - 29 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `B.activity.detour_factor` | `1.3276` | ratio | `assumed` | **held fixed** |
| `B.activity.short_trip_band_km` | `1.0` | km_network | `literature` | **held fixed** |
| `B.census.thin_cell_min_journeys` | `100` | journeys | `definition` | - |
| `B.counts.station_match_radius_m` | `120.0` | metres | `assumed` | 60 - 120 |
| `B.mode.bike_feasible_km` | `0.0` | km_straight_line | `definition` | - |
| `B.mode.walk_feasible_km` | `0.0` | km_straight_line | `definition` | - |
| `B.population.age_bands` | `[[0, 4], [5, 9], [10, 14], [15, 19], [20, 24], [25, 29], [30, 34], [35, 39], [40, 44], [45, 49], [50, 54], ...` | years | `definition` | - |
| `B.population.bike_min_age` | `6` | years | `definition` | - |
| `B.population.vehicle_roster` | `per_person` | enum | `assumed` | `census`, `per_person` |
| `B.ride.bound_pairing_window_min` | `60.0` | minutes | `derived` | derived: bound_pairing_window_min = 2 * time_mutation_range_s / 60 |
| `B.ride.coherence_scope` | `declared` | enum | `assumed` | `declared`, `inferred` |
| `B.ride.declared_pair_meeting` | `driver_detour` | enum | `assumed` | `driver_detour`, `passenger_links` |
| `B.ride.escort_coherence_rate` | `0.4` | share_per_iteration | `assumed` | 0 - 0.5 |
| `B.ride.joint_coherence_rate` | `0.4` | share_per_iteration | `assumed` | 0 - 0.5 |
| `B.ride.max_passengers_per_vehicle` | `4` | persons | `assumed` | 1 - 4 |
| `B.ride.pairing_enabled` | `false` | boolean | `definition` | - |
| `B.ride.pairing_rule` | `both_links` | enum | `assumed` | `both_links`, `route_contains`, `origin_link`, `dest_link`, `window_only` |
| `B.ride.pairing_window_min` | `15.0` | minutes | `assumed` | 5 - 60 |
| `B.ride.physical_boarding` | `true` | boolean | `definition` | - |
| `B.ride.pickup_dwell_s` | `0.0` | seconds | `assumed` | 0 - 120 |
| `B.ride.remode_unpaired` | `true` | boolean | `definition` | - |
| `B.ride.unpaired_fallback` | `licensed_drive_else_walk` | enum | `assumed` | `licensed_drive_else_walk`, `walk` |
| `B.ride.wait_for_driver` | `true` | boolean | `definition` | - |
| `B.seed.master` | `20260810` | integer_seed | `definition` | - |
| `B.taxi.daily_trips_band` | `[15000, 25000]` | trips_per_day | `literature` | **held fixed** |
| `B.taxi.deadhead_min` | `12.0` | minutes | `assumed` | 0 - 30 |
| `B.taxi.fleet_size` | `800` | vehicles | `assumed` | **held fixed** |
| `B.taxi.max_wait_min` | `20.0` | minutes | `assumed` | 10 - 45 |
| `B.taxi.min_unaccompanied_age` | `18` | years | `definition` | - |

#### `B.activity.detour_factor`

Straight-line to network distance, routed over the observed A1 road graph, re-measured on the CURRENT network 4 Sep 2026 (9.142): 1.3376 over 551 routed pairs became 1.3276 over 595, the extra pairs being zone pairs the pre-16-August network could not route between. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202*

> **Sweep basis.** the interquartile range of the per-pair ratios over 595 population-weighted zone pairs, re-measured on the current network 4 Sep 2026 (9.142); the 551-pair figure it replaces was routed over the network as it stood before the 16 August rebuild

> **Held fixed.** the reference city's measurement, adopted; no Mumbai measurement exists and the field is not varied
>
> *Departure requires: a Mumbai measurement of the same quantity*

#### `B.activity.short_trip_band_km`

The network-distance edge of the short-trip band whose observed share short_trip_band_share carries. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202*

> **Held fixed.** the published band boundary of the source table (HTS Sydney 2012/13 Table 4.4.7, 'Up to 1km'). Changing it means citing a different row of the same table, not sweeping a belief - the band share and its edge are one observation and move together.
>
> *Departure requires: a logged decision*

#### `B.census.thin_cell_min_journeys`

Reporting flag for the demographic mode-share measurement (issue #50): an observed census cell under this many journeys is marked too thin to constrain anything - ABS randomly perturbs small cells, so tiny aggregates carry perturbation noise on top of sampling noise. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `B.counts.station_match_radius_m`

Radius within which a permanent traffic count station may be attached to a network link it is taken to count. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** measured on data/processed/validation/count_station_links.csv: the largest ACCEPTED match is 119.7 m, so 120 m is exactly binding. Tightening costs targets at a measured rate - at 100 m six of the 116 matched stations lose their link and at 60 m twenty-three do - which is the lower bound. The upper bound is the current value because loosening cannot gain anything already in the file; whether a larger radius would resolve the three stations that match nothing (issue 10) has NOT been tested, and testing it means re-running the mapper and regenerating a committed artefact.

#### `B.mode.bike_feasible_km`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.modeAvailability.bikeFeasibleKm on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `modeAvailability.bikeFeasibleKm`*

#### `B.mode.walk_feasible_km`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.modeAvailability.walkFeasibleKm on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `modeAvailability.walkFeasibleKm`*

#### `B.population.age_bands`

Age banding for population synthesis: the five-year bands of the Census of India 2011 C-14 table the package holds (data/processed/observed/census_2011_age_sex.csv), 80+ open.

***definition** · status **active** · DECISIONS.md §9.202*

#### `B.population.bike_min_age`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.modeAvailability.bikeMinAge on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `modeAvailability.bikeMinAge`*

#### `B.population.vehicle_roster`

Whether a household's drivers share the cars the census gives it: `census` - every driver is mapped to one of the household's `householdVehicles` shared cars and waits for it when it is out; `per_person` - each person drives a car of their own (MATSim's default, pre-9.146). Switched off for this baseline ("per_person"): the baseline population carries no households; car access is a person attribute.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `householdVehicles.roster` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Whether a household's drivers share the cars the census says it owns. `per_person` is MATSim's own behaviour and every arm before 9.146: PrepareForSim gives each person a car of their own under qsim.vehiclesSource=modeVehicleTypesFromVehiclesData, so a household can put more cars on the road than it holds. `census` maps every licensed, car-available member of a household with n >= 1 vehicles (B1 `household_vehicles`, stamped on the population as `householdVehicles`) to one of n shared vehicles hh<id>_car<k>, assigned round-robin in person-id order, at the first iteration after PrepareForSim; the agent source parks each shared car once, where the first member starts; whoever wants it while it is out waits for it under RUN.qsim.vehicle_behavior. Measured at the F26 iteration-100 gate (aborted_20260906T100429_300it_25pct): 12,317 car legs, 3.28 % of resident car legs across 5,279 households, began while every vehicle the household owns was already out - 4,265 of them a one-car household with two members driving at once - and the census holds 81,384 households (33.0 %) with more licensed drivers than vehicles. A one-car household is EXACT under `census`; a multi-car household is assigned rather than pooled, because MATSim maps a person to one vehicle per mode, and that limit is stated rather than hidden. The sweep is over the MECHANISM: running both measures how much of car's excess and ride's deficit the second car supplied.

#### `B.ride.bound_pairing_window_min`

SINCE 9.120 THIS IS NOT A PAIRING TOLERANCE. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***derived** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.boundWindowMinutes`*

> **Derived from** `RUN.replanning.time_mutation_range_s`: bound_pairing_window_min = 2 * time_mutation_range_s / 60

#### `B.ride.coherence_scope`

Whom the coherence listener may re-propose a ride pair for: `declared` - only a demand-bound trip with its named driver (boundRideTrips / boundDriver); `inferred` - any household member matching a household car leg on endpoints and clock (pre-9.146). Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.coherenceScope` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Whom EscortCoherenceListener may re-propose a pair for. `inferred` is the behaviour of every arm before 9.146 and is kept as the control: any household member whose trip matches a household car leg on endpoints and clock is offered `ride`, and a drifted household driver whose non-car trip matches a member's ride is offered `car`, whether or not the demand bound them. `declared` restricts both passes to the identity every other ride mechanism has used since 9.120 - a trip in the person's `boundRideTrips`, with a driver in their `boundDriver` - so the listener keeps DECLARED pairs coherent and invents none. Measured at the F26 iteration-100 gate (aborted_20260906T100429_300it_25pct): 12,461 of 66,909 selected ride legs sat on persons the demand never bound, the listener re-proposing ~5,000 inferred ride plans an iteration while GatedSubtourModeChoice refused 192,000 proposals of exactly that kind; the inferred legs were the ones that never paired (miss_window + miss_endpoints 13,168 against miss_declared_absent 719), executed as walk or drive, and held plan-memory slots against real alternatives. The sweep is over the MECHANISM: running both measures how much of the pairing loss and the walk/car residue the inferred proposals supplied.

#### `B.ride.declared_pair_meeting`

Where a declared ride pair meets when the two members' links differ: `driver_detour` routes the driver's car leg through the passenger's origin and destination links and the passenger boards and alights at their own; `passenger_links` requires the driver to satisfy the pairing rule on the passenger's links (pre-9.128). Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.declaredMeeting` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Where a DECLARED ride pair meets when the passenger's and the driver's links differ. `passenger_links` is the behaviour before 9.128: the named driver must still satisfy B.ride.pairing_rule on the passenger's own two links, so a shared ride bound on a suburb-to-suburb trip (9.124) is never realised - two households in one SA2 do not share a link, and the valid F18 arm's iteration 0 refused 2,053 of 6,966 ride legs on endpoints for exactly that reason. `driver_detour` routes the driver's car leg, at BeforeMobsim and with the run's own car router, through each carried passenger's origin link (in departure order) and then each destination link, and on to the driver's own destination; the passenger boards at their own link as the car passes it and alights at their own, and the pairing books the pass time. The detour is driven on the network and the driver's score pays for it, so a passenger too far out of the driver's way costs the driver what it costs and no threshold decides who is served. A walking meeting point was built first and measured on a 1% smoke at a mean 8-11 km walked to and from the driver's links - nobody walks that to a lift - and was replaced by this. The sweep is over the MECHANISM: running both measures how much of the realised ride share the detour itself supplies.

#### `B.ride.escort_coherence_rate`

Rate at which an escort driver and the household member they were generated to carry are re-offered the coherent state after MATSim's per-agent replanning has split them. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.escortCoherenceRate` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: A SEARCH parameter, not a preference: how often a DECOHERED escort pair is offered the coherent plan back, never how attractive riding is. ZERO RECOVERS TODAY'S BEHAVIOUR EXACTLY, which is what makes the mechanism's effect measurable rather than assumed, and is the reason the interval starts there. The upper bound is where re-proposal would start to dominate the declared innovation weights (SubtourModeChoice 0.1, ReRoute 0.15) and the search would be re-proposing faster than it explores. The value is not fitted to any target and cannot be: the proposed plan is scored like any other and ChangeExpBeta keeps it only if it earns its place, so this field moves how QUICKLY a coherent pair can be rediscovered, not whether it survives.

#### `B.ride.joint_coherence_rate`

Rate at which a joint-tour driver and their bound household companion are re-offered the coherent car+ride state after per-agent replanning has split them. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.jointCoherenceRate` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: The same SEARCH parameter as B.ride.escort_coherence_rate, pointed at joint (non-escort) household pairs: how often a decohered driver-companion pair is offered the coherent state back, never how attractive riding is. ZERO RECOVERS THE ESCORT-ONLY BEHAVIOUR EXACTLY, so the joint extension is measurable on its own. The upper bound mirrors the escort rate: above it, re-proposal would dominate the declared innovation weights and the search would re-propose faster than it explores. Not fitted to any target and cannot be - ChangeExpBeta keeps a proposed plan only if it earns its place.

#### `B.ride.max_passengers_per_vehicle`

How many passengers one driver's leg may carry. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.maxPassengersPerVehicle` · sweep role **uncertainty***

> **Sweep basis.** The upper bound is the physical one: a five-seat car minus the driver, which is what the overwhelming majority of the registered light fleet is. The lower bound is one passenger per driver, the most conservative reading of a household lift. No observation splits household lifts by party size - HTS reports Vehicle passenger as a share of trips, not an occupancy distribution - so the cap is assumed within physical bounds and swept. It is not binding at the measured pairing rates and the diagnostic reports how often it refuses, so a run in which it starts to bind is visible rather than silent.

#### `B.ride.pairing_enabled`

Whether a `ride` leg may NAME the household member who drives it, and take that driver's realised travel time instead of its own routed one. Switched off for this baseline (false): the baseline population carries no households, so no ride can name its driver.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `ridePairing.enabled`*

#### `B.ride.pairing_rule`

The spatial coincidence a pairing requires, expressed on LINK IDENTITY rather than on distance - no coordinate, no radius and no place enters the model, so the rule reads identically for a city the framework has never seen. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.rule` · sweep role **answer***

> **Sweep basis.** adopted from the reference city: Which of the driver's links the passenger's must coincide with. `both_links` is the declared value: the driver's leg starts and ends on the passenger's own two links, so the two are the same trip and handing the driver's realised travel time to the passenger is correct rather than merely closer. `route_contains` (added 9.102) requires the passenger's two links to lie ON the driver's routed path in the order the driver drives them, and the engine apportions the driver's time by the carried segment's share of route length - unity when the segment is the whole route, so both_links is the special case and the two are directly comparable. It is the only rule that CAN represent a drop-off en route, which is the commonest car-passenger trip there is, and it was built because 64.4% of pairing failures are the `miss_endpoints` class. **It is not the declared value, because it was measured and it does not help**: a paired 1%/40-iteration diagnostic differing in this field alone (ride_rule_control_1pct vs ride_rule_contains_1pct) moved the pair rate 0.5069 -> 0.5113 (+0.44 pp) and miss_endpoints 1,257 -> 1,233, while ride mode share went 9.6748 -> 9.4513 and walk 37.6154 -> 39.2871 - the wrong way, and at a size indistinguishable from one seed's noise. The reason is upstream: a driver routed home-to-work has no escort stop, so the router has no reason to pass the passenger's destination either, and relaxing the test from identity to containment finds almost nothing more. That CONFIRMS 9.92's conclusion that both_links stays. The three loosest rules match trips that need not overlap at all and remain sensitivities, never results. Their spread is large and measured (9.44): on the relaxed 25% arm at +-30 min the pairable share is 0.001% under both_links, 1.5% under origin_link, 1.4% under dest_link and 5.6% under window_only.

#### `B.ride.pairing_window_min`

How far apart a passenger's and a driver's PLANNED departures may be and still be treated as one trip. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.windowMinutes` · sweep role **uncertainty***

> **Sweep basis.** No local observation of how far apart a household lift's two departures may be exists, and HTS carries no household-linked trip records at all, so the tolerance is assumed and swept rather than fitted. The lower bound is a tight coincidence; the upper is an hour, beyond which calling two departures one trip stops being credible. MEASURED SENSITIVITY on the relaxed 25% pilot arm (9.44): the share of ride legs with ANY household car leg in the window runs 1.1% at +-5 min, 3.1% at +-15, 5.6% at +-30 and 15.1% at +-120, so this field moves the pairing rate by an order of magnitude and may not be pinned.

#### `B.ride.physical_boarding`

Whether a PAIRED ride passenger physically BOARDS the driver's vehicle in the mobsim (a real PersonEntersVehicleEvent, every link ridden, alighting at the shared destination link) instead of inheriting the driver's clock by teleport. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***definition** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.physicalBoarding`*

#### `B.ride.pickup_dwell_s`

Seconds added to a PAIRED passenger's travel time for the act of being picked up. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.pickupDwellSeconds` · sweep role **uncertainty***

> **Sweep basis.** No measurement of pickup dwell exists for this city, or for any comparable one in the package, so the value is swept and NEVER fitted. The default is deliberately NEUTRAL. The car-minus-ride residual this lane exists to remove was MEASURED from the pilot arms' own output_legs at about 5 s at 25% and 13 s at 10%, flat across every distance bin below 50 km; a one-minute friction would therefore be five to twelve times the entire quantity it was meant to explain. Sizing this to close that gap is calibration wearing a mechanism's clothes and was REFUSED. The upper bound is two minutes, which is already far beyond what the residual can bear, and exists so the sweep can show that.

#### `B.ride.remode_unpaired`

Whether an UNPAIRED ride leg is re-moded to network-simulated walk at the BeforeMobsim boundary - the 9.51 standing directive's own ruling (every ride physically in a car, no exceptions, no teleportation) enacted without inventing a parameter: a ride trip no household driver can physically serve is not a ride trip, it walks, scores accordingly, and co-evolution reassigns the tour - so the surviving ride share is EMERGENT from the physical driver supply rather than declared. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***definition** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.remodeUnpaired`*

#### `B.ride.unpaired_fallback`

How a ride leg that no household driver can serve is physically executed for the iteration in which it failed. Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.unpairedFallback` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: What an unpairable ride leg is EXECUTED as for that mobsim. `walk` was the only behaviour before 9.105 and reproduces every earlier arm exactly, which is why it is kept. It was never argued for as a behaviour - 9.55 chose it so that a failed lift would SCORE badly and co-evolution would reassign the tour, and the walk was a means to that end. Measured, the means dominates: at iteration 100 of 20260829T172145_1000it_10pct, 16,153 unpaired ride legs and 1,602 refused taxi legs are forced to walk in a single iteration - 31% of all walk trips - and walk's mean trip length is 8.75 km against the 0.7 km this package already declares as observed (C.constraint.trip_length_km.walk), with 46% of walk trips over 5 km and the longest 91.4 km, a twenty-hour walk. Of walk trips over 5 km, 14,910 belong to agents holding BOTH a licence and a car, so this is not people without options. `licensed_drive_else_walk` executes the leg as CAR when the passenger holds a licence and has a car available, and leaves everyone else walking: a household whose lift falls through drives, and only someone who cannot drive is left on foot. It is a behavioural claim, not a fit device - it is chosen because a 10 km forced walk is not a behaviour any person exhibits, and it must be measured against the `walk` arm like any other declared value. The ride alternative is restored at AfterMobsim under BOTH members; 9.81's one-way ratchet must not return.

#### `B.ride.wait_for_driver`

Whether a booked passenger whose car is not at the meeting point yet physically WAITS for it, bounded by the declared pairing window (B.ride.pairing_window_min - the same tolerance the booking was made under, so no second number is invented). Adopted from the reference city and INERT here: B.ride.pairing_enabled = false switches the mechanism off for this baseline, so the value reaches the config and nothing acts on it.

***definition** · status **placeholder** · DECISIONS.md §9.202 · MATSim `ridePairing.waitForDriver`*

#### `B.seed.master`

The one seed everything synthetic derives from; city.json declares it.

***definition** · status **active** · DECISIONS.md §9.202*

#### `B.taxi.daily_trips_band`

The inferred central band of daily point-to-point trips in the study area (IPART 2025 incidence x usage-rate assumptions; HTS Hunter "Other" ceiling 35,000/weekday). Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202*

> **Held fixed.** A CONSTRAINT, NEVER A TARGET (9.8/9.13): the pre-registered 67/143 target split cannot grow. The modelled taxi volume is REPORTED against this band; nothing is fitted to it.
>
> *Departure requires: the levy trip counts, if ever requested*

#### `B.taxi.deadhead_min`

Empty running between setting one passenger down and reaching the next - the part of a vehicle’s day that carries nobody, and the reason a fleet of N serves fewer trips than the arithmetic of fare durations alone suggests. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `taxiFleet.deadheadMinutes` · sweep role **uncertainty***

> **Sweep basis.** DECISIONS.md 9.99: the deadhead stands in for the average cost of reaching the next fare and is declared as unavailable time rather than routed. Zero (a fleet that teleports between fares) is the lower bound so the effect of empty running is itself a sweep member; 30 minutes is a generous suburban repositioning. No Newcastle operator data; no observed spread.

#### `B.taxi.fleet_size`

Taxi and rideshare vehicles serving the study area, AT FULL SCALE - the engine scales it by qsim.flowCapacityFactor for the same reason the SCATS saturation flow is scaled (9.88): a sampled run is a city whose capacities were scaled, and a full-scale fleet serving a tenth of the demand would constrain nothing. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `taxiFleet.fleetSize`*

> **Held fixed.** adopted from the reference city, where it is derived from B.taxi.daily_trips_band, B.taxi.vehicle_trips_per_day; those fields are not declared for this city, so the value is held
>
> *Departure requires: declaring B.taxi.daily_trips_band, B.taxi.vehicle_trips_per_day for this city*

#### `B.taxi.max_wait_min`

How long a passenger waits for a vehicle before abandoning the taxi trip. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `taxiFleet.maxWaitMinutes` · sweep role **uncertainty***

> **Sweep basis.** DECISIONS.md 9.99: no Newcastle abandonment figure is published, so the wait at which a passenger gives up is assumed and bracketed from a tolerant 10 minutes to a patient 45; half to a little over twice the value. No observed spread.

#### `B.taxi.min_unaccompanied_age`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.modeAvailability.taxiMinAge on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `modeAvailability.taxiMinAge`*

## The household population from the census controls at the core extent (9.204)

*`cities/mumbai/registry/B_population.json` - 4 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `B.population.household_size_open_band_max` | `12` | persons | `assumed` | 9 - 15 |
| `B.population.plans_build_fraction` | `0.05` | fraction | `definition` | - |
| `B.population.projection_district_names` | `{"519": "Mumbai", "518": "Mumbai Suburban", "517": "Thane", "520": "Raigarh"}` | name_map | `definition` | - |
| `B.population.tertiary_attendance_rate_20_24` | *(null - unobtained)* | probability | `assumed` | 0 - 0.35 |

#### `B.population.household_size_open_band_max`

The largest household size drawn for the open 9+ band of the HL-14 household-size distribution; sizes within the 6-8 and 9+ bands are drawn uniform.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** HL-14 publishes household sizes in bands and the top band is 9+; the largest size a 9+ household is drawn at, uniform from 9. The projected mean household size is compared with HL-1's published mean in _population_report.json

#### `B.population.plans_build_fraction`

The share of core households whose plans are written (build_plans.py), by the framework's nested inclusion hash (sample_population.keep on the household id and B.seed.master), so a run at RUN.sample.fraction f at or below it keeps exactly the households a file of everyone would give and the capacity factors stay identities on f. A definition of what the file holds, not a modelling value: the plans report carries it and the launcher refuses a run fraction above the report's. 0.05 of 27.06 M persons is 1.35 M agents, the largest plans file the machine reads at launch in minutes.

***definition** · status **active** · DECISIONS.md §9.205*

#### `B.population.projection_district_names`

Census 2011 district code -> the district name as printed in the IIPS district projections 2012-2031 (data/processed/observed/district_age_population_projections.csv): 519 is Mumbai (the island city, 3.09 M in 2011), 518 Mumbai Suburban (9.36 M), 517 the 2011 Thane district whole (with today's Palghar), 520 Raigad, which the projections spell Raigarh. A name reconciliation, not a modelling value; the report shows each district's factor.

***definition** · status **active** · DECISIONS.md §9.204*

#### `B.population.tertiary_attendance_rate_20_24`

The share of persons aged 20-24 attending an educational institution. Unobtained: null, and the synthesiser makes nobody in that age range a student, which the report says.

***assumed** · status **unobtained** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** unobtained: the C-12 attendance table the package holds covers ages 5-19 and no district attendance rate for ages 20-24 is acquired; the range spans nobody attending to the age-19 attendance rate of the four districts, and the value stays null until the C-12 age-20-24 cells or a published tertiary rate is acquired

## The first per-mode targets from the published splits (9.205)

*`cities/mumbai/registry/B_targets.json` - 5 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `B.targets.active_share_sweep_pp` | `3.0` | percentage_points | `assumed` | 1 - 5 |
| `B.targets.ferry_port_groups` | `["Bandra", "Mora"]` | port_group_names | `definition` | - |
| `B.targets.goods_vehicle_traffic_share_pct` | `11.5` | percent_of_vehicles | `observed` | **held fixed** |
| `B.targets.published_split_area` | `Mumbai Metropolitan Region` | area_name | `definition` | - |
| `B.targets.published_split_year` | `2017` | year | `definition` | - |

#### `B.targets.active_share_sweep_pp`

How far the printed "about 47 %" active share may sit from 47 in either direction; propagated to every target derived from the motorised split.

***assumed** · status **active** · DECISIONS.md §9.205 · sweep role **uncertainty***

> **Sweep basis.** the CTS prints the active share as "about 47 %"; the sweep on every derived target carries the rounding of that statement, and its own width is the reading of "about"

#### `B.targets.ferry_port_groups`

The Maharashtra Maritime Board port groups whose routes lie in the MMR (Bandra: Versova-Madh and the Mumbai creek routes; Mora: the harbour routes to Uran and Elephanta); Rajpuri, Ratnagiri and Vengurla are outside the study extent.

***definition** · status **active** · DECISIONS.md §9.205*

#### `B.targets.goods_vehicle_traffic_share_pct`

Goods vehicles as a share of screenline traffic, the CMP for Greater Mumbai's traffic composition (buses 4.4 %, goods vehicles 11.5 %): the level the truck row prints beside the modelled network-wide road-vehicle share.

***observed** · status **active** · DECISIONS.md §9.205*

> **Held fixed.** a published screenline observation (CMP for Greater Mumbai executive summary, traffic composition), never varied
>
> *Departure requires: a newer classified count at the screenlines*

#### `B.targets.published_split_area`

Which published daily mode split (data/processed/observed/published_mode_splits.csv) the targets derive from: the MMR, the study core (D13), as the CTS Updation surveyed it.

***definition** · status **active** · DECISIONS.md §9.205*

#### `B.targets.published_split_year`

The survey year of the published split used: 2017, the CTS Updation household survey - the newest all-mode observation of the MMR the package holds.

***definition** · status **active** · DECISIONS.md §9.205*

## Framework run-side fields: moved from the private baseline namespace or adopted from the reference city (9.202)

*`cities/mumbai/registry/CAL_framework.json` - 14 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `CAL.asc.damping` | `0.6` | share_of_the_log_ratio_step | `literature` | 0.3 - 1 |
| `CAL.asc.max_step_utils` | `1.5` | utility | `definition` | **held fixed** |
| `CAL.asc.mode_to_constant` | `{}` | board_mode_to_registry_key | `definition` | - |
| `CAL.gate.pass_deviation_pct` | `10.0` | per cent | `definition` | - |
| `CAL.gate.reading_window_iterations` | `40` | iterations | `assumed` | 20 - 80 |
| `CAL.gate.stop_deviation_pct` | `20.0` | per cent | `definition` | - |
| `CAL.objective.components` | `{"goal_modes.max_abs_rel_pct": 1.0}` | weight_per_fit_component | `definition` | - |
| `CAL.objective.include_counts` | `false` | boolean | `assumed` | **held fixed** |
| `CAL.objective.independent_targets` | `10` | count | `derived` | derived: The objective is now the twelve-mode board, so the count is the number |
| `CAL.objective.replication_band_pp` | `0.0` | relative_percent | `assumed` | 0 - 2 |
| `CAL.search.convergence_delta` | `24.88` | per cent | `derived` | derived: convergence_delta = reading_drift_pct. A coordinate pass that 'improve |
| `CAL.search.max_rounds` | `3` | count | `assumed` | 1 - 6 |
| `CAL.search.points_per_parameter` | `3` | count | `assumed` | 3 - 7 |
| `CAL.search.reading_drift_pct` | `24.88` | per cent | `assumed` | **held fixed** |

#### `CAL.asc.damping`

How much of the raw log-ratio step an ASC round applies. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** The two published implementations of this update rule bracket the interval. matsim-vsp/matsim-python-tools applies the log-ratio step under `linear_scheduler(start=0.6, end=1, interval=3)` - damped to 0.6 of the raw step at first and relaxed toward the full step as the rounds proceed - and the ActivitySim agency practice uses a flat 0.5 dampener on the same ln(observed/modelled) adjustment. The interval runs from below the more cautious of the two to the undamped step, which is what a fixed point converges to when it converges at all. Undamped (1.0) is included deliberately: it is the boundary case, and whether the step needs damping AT ALL in this model is one of the things the two-round test measures.

#### `CAL.asc.max_step_utils`

The largest single-round |delta ASC| this loop will propose before it refuses outright and says the mode needs a mechanism rather than a constant. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

> **Held fixed.** A REFUSAL THRESHOLD, not a model input, and so not swept - the A.signals.scats_match_radius_m precedent for a build guard's tolerance. It is the point past which a proposed step stops being a calibration and becomes an admission that the residual is not a taste parameter at all: a shift of 1.5 utils against a marginal utility of travel time of order 1 util/hour is worth more than an hour of travel time, which no alternative-specific constant should have to carry. A proposal above it is REFUSED and the mode is reported as needing a mechanism, never silently clipped - clipping would hide exactly the signal this experiment exists to read.
>
> *Departure requires: a logged decision*

#### `CAL.asc.mode_to_constant`

Which declared alternative-specific constant carries which board mode. Empty: the baseline scores one constant for every mode (C.scoring.mode_constant) and no ASC loop runs for this city.

***definition** · status **active** · DECISIONS.md §9.202*

#### `CAL.gate.pass_deviation_pct`

The per-mode deviation the model must be INSIDE for every mode before the standing directive is satisfied. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `CAL.gate.reading_window_iterations`

How deep behind the reading point the gate reading is AVERAGED, in iterations. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** The window is an INSTRUMENT setting, not a model value, so its bracket is what the evidence can bound rather than what a literature reports. The floor of 20 is two readings at the 10-iteration write interval - the narrowest thing that is an average rather than a point. The ceiling of 80 is where the window reaches back to iteration 20 and begins averaging in the run's early transient: past it the reading would look steadier because it is measuring a different regime, which is the one way this field could pass by measuring less. Nothing in the store reaches past iteration 104, so no window ending deeper than 100 can be tested at all today; a first arm past its gate would let the bracket be re-derived at depth.

#### `CAL.gate.stop_deviation_pct`

The per-mode deviation from its real-life target at which the standing gate-loop directive says to STOP the run rather than let it converge on a wrong answer. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `CAL.objective.components`

Dotted paths into _fit.json that form the scalar objective, with their weights. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `CAL.objective.include_counts`

Whether traffic counts may enter the calibration objective. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202*

> **Held fixed.** adopted from the reference city, where it is derived from B.external.interaction_rate; those fields are not declared for this city, so the value is held
>
> *Departure requires: declaring B.external.interaction_rate for this city*

#### `CAL.objective.independent_targets`

How many independent numbers the objective actually contains. Adopted from the reference city's declaration; not a Mumbai observation.

***derived** · status **active** · DECISIONS.md §9.202*

> **Derived from** `CAL.objective.components`: The objective is now the twelve-mode board, so the count is the number of INDEPENDENT numbers that board contains. Twelve rows, less truck (scored 'level only' - a network-wide vehicle share against a freight-route observation, not the target's own basis, 9.101) and less freight_train (representation: the crossing closures ARE the timetable, so its 0.0% is a tautology), leaves TEN scored modes. All ten are independent: EIGHT are shares of resident linked trips (car, ride, walk, taxi, bike, motorbike, bus, ferry) and TWO are weekday boardings (heavy_rail, light_rail) on a different basis entirely. The adding-up identity that removed one degree of freedom from the old five folded shares DOES NOT BIND here: the eight share targets sum to 98.42%, and the residual is taken up by the two rail modes, whose SHARE is not itself a declared target - they are targeted on boardings. So no linear constraint ties the ten together and the count is ten, not nine. It was 4, which was correct for the OLD objective (five HTS mode shares summing to one, hence four independent) and is the reason the loop refused to move five parameters: it was refusing to fit the twelve-mode goal with the four-number folded objective's budget.

#### `CAL.objective.replication_band_pp`

The replication band the calibration objective is divided by (#163) - the spread the objective takes across runs of the SAME configuration differing only in seed. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **measurement***

> **Sweep basis.** adopted from the reference city: 0.0 is NO BAND - the objective is the raw maximum over the twelve modes, exactly as every reading so far has been scored - and it is the shipped value because THE BAND HAS NOT BEEN MEASURED. The upper bound is 2.0 relative per cent, twice the largest within-run movement anyone has observed: inside 20260909T015217_300it_25pct, with nothing changed, the folded objective moves 0.272-0.418 pp between iterations 80 and 100 (9.162). WHAT THE SWEEP ANSWERS: how much of what the calibration loop is chasing is seed scatter rather than misfit. A MATSim run is not bit-reproducible and no deviation on the board carries an error bar - asked for by three consecutive assessments (#163) - so a mode 3 % out and a mode 30 % out are today treated as the same KIND of evidence. THIS VALUE MUST NOT BE PINNED FROM THE SWEEP. It is measured: three arms at a short horizon differing only in RUN.machine.seed, and the band is the spread of the objective across them. Choosing a denominator from the interval instead would be inventing the observation the denominator exists to represent, which is the one failure this project cannot absorb - so the sweep is the honesty bracket for an unmeasured quantity and never a value to select.

#### `CAL.search.convergence_delta`

A coordinate pass that improves the objective by less than this ends the search, in the units of the objective - which is now the maximum relative deviation across the twelve modes, in per cent. Adopted from the reference city's declaration; not a Mumbai observation.

***derived** · status **active** · DECISIONS.md §9.202*

> **Derived from** `CAL.search.reading_drift_pct`: convergence_delta = reading_drift_pct. A coordinate pass that 'improves' the objective by less than the reading's own noise has not been shown to improve anything: the same run read twenty iterations later moves further than that by itself, on all six arms measured. So the stopping rule is the noise floor, and it is derived from it rather than chosen beside it. IT WAS 0.25 pp, in the units of the OLD folded objective, and it was SMALLER THAN THE MEASURED DRIFT ON EVERY ARM (by 1.09x to 1.67x) - a search under it would have stopped, or failed to stop, on noise. Its stated floor of 0.1 pp cited the seed spread 9.7 measured; that was the right instinct pointed at the wrong quantity, because seed spread is the spread BETWEEN runs and this is the drift WITHIN one.

#### `CAL.search.max_rounds`

Maximum coordinate-descent passes over the free parameters. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** DECISIONS.md 9.16 names this a control of the search loop itself, and calibrating the search against itself is the failure it guards; the interval runs from a single pass to twice the declared three. No observed spread.

#### `CAL.search.points_per_parameter`

Points evaluated along each parameter's declared sweep interval in one coordinate pass, endpoints included. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** DECISIONS.md 9.16: three is the smallest number of points that can show curvature along a sweep interval and each point is a full run, so the interval runs from that floor to seven. A control of the calibration search, never of the model. No observed spread.

#### `CAL.search.reading_drift_pct`

How much the objective moves between iteration 80 and iteration 100 OF THE SAME RUN, in the objective's own units - the noise floor of a gate-point reading. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202*

> **Held fixed.** the reference city's measurement, adopted; no Mumbai measurement exists and the field is not varied
>
> *Departure requires: a Mumbai measurement of the same quantity*

## Framework run-side fields: moved from the private baseline namespace or adopted from the reference city (9.202)

*`cities/mumbai/registry/C_framework.json` - 23 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `C.asc.car_passenger` | `0.0` | utils | `assumed` | -2 - 2 |
| `C.crowding.penalty_utils_per_h` | `6.0` | utility_per_hour | `assumed` | plus/minus 50% |
| `C.crowding.representation` | `in_vehicle_time` | enum | `definition` | - |
| `C.crowding.seated_multiplier` | `1.1` | ratio | `assumed` | plus/minus 50% |
| `C.crowding.standing_multiplier` | `1.8` | ratio | `assumed` | plus/minus 50% |
| `C.income.exponent` | `1.0` | exponent | `definition` | - |
| `C.income.representation` | `person_marginal_utility_of_money` | enum | `definition` | - |
| `C.raptor.mode_cost_representation` | `absent` | enum | `assumed` | `absent`, `mode_constant` |
| `C.scoring.activity_minimal_applied_s` | *(null - unobtained)* | seconds | `derived` | derived: min(C.scoring.activity_minimal_duration_s, typical duration) per activ |
| `C.scoring.activity_minimal_duration_s` | `0` | seconds | `definition` | - |
| `C.scoring.activity_typical_duration_s` | `{"home": 43200, "work": 28800, "education": 21600, "other": 3600, "freight_start": 86400, "freight_end": 86...` | seconds | `assumed` | plus/minus 50% |
| `C.scoring.marginal_utility_of_money` | `0.05` | utils_per_INR | `assumed` | plus/minus 50% |
| `C.scoring.marginal_utility_of_traveling` | `{"car": -6.0, "ride": -6.0, "walk": -6.0, "bike": -6.0, "motorbike": -6.0, "taxi": -6.0, "auto_rickshaw": -...` | utils_per_hour | `assumed` | plus/minus 50% |
| `C.scoring.mode_constant` | `{"car": 0.0, "ride": 0.0, "walk": 0.0, "bike": 0.0, "motorbike": 0.0, "taxi": 0.0, "auto_rickshaw": 0.0, "p...` | utils | `definition` | - |
| `C.scoring.monetary_distance_rate` | `{"car": -0.007, "ride": -0.003, "walk": 0.0, "bike": 0.0, "motorbike": -0.0025, "taxi": -0.018, "auto_ricks...` | INR_per_metre | `assumed` | plus/minus 50% |
| `C.scoring.performing_utils_per_h` | `6.0` | utils_per_hour | `assumed` | plus/minus 50% |
| `C.scoring.utility_of_line_switch` | `-0.5` | utils | `assumed` | plus/minus 50% |
| `C.scoring.waiting_pt` | `-12.0` | utils_per_hour | `assumed` | plus/minus 50% |
| `C.time_weights.beta_headway` | `0.5` | ratio_to_ivt | `literature` | 0.35 - 0.65 |
| `C.time_weights.beta_reliability` | `1.3` | ratio_to_ivt | `literature` | 0.8 - 1.8 |
| `C.time_weights.headway_utils_per_min` | `0.05` | utility_per_minute | `assumed` | plus/minus 50% |
| `C.time_weights.reliability_utils_per_min` | `0.13` | utility_per_minute | `assumed` | plus/minus 50% |
| `C.time_weights.service_quality_representation` | `headway_and_reliability` | categorical | `definition` | - |

#### `C.asc.car_passenger`

Car-passenger constant. Placeholder at zero: the baseline scores one constant for every mode and no ASC round has run for this city.

***assumed** · status **placeholder** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** the baseline has one constant for every mode; a passenger-specific constant is not solved for this city

#### `C.crowding.penalty_utils_per_h`

Provisional price of additional perceived in-vehicle time due to crowding. Bound directly because RUN.scoring.translation is bound_fields: the harness derives this price from the trip-weighted value of time only under the C1 translation (9.204). Renamed from C.smoke.crowding_price on 21 September 2026.

***assumed** · status **active** · DECISIONS.md §9.204 · MATSim `ptCrowding.penaltyUtilsPerHour` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.crowding.representation`

Enable the existing behavioural mechanism in the broad provisional baseline. Moved from RUN.smoke.crowding on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `ptCrowding.representation`*

#### `C.crowding.seated_multiplier`

Provisional full-load seated time multiplier. Moved from C.smoke.crowding_seated on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `ptCrowding.seatedMultiplier` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.crowding.standing_multiplier`

Provisional standing time multiplier. Moved from C.smoke.crowding_standing on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `ptCrowding.standingMultiplier` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.income.exponent`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.incomeScoring.incomeExponent on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `incomeScoring.incomeExponent`*

#### `C.income.representation`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.incomeScoring.representation on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `incomeScoring.representation`*

#### `C.raptor.mode_cost_representation`

The representation gate for the PT mode constant in the TRANSIT ROUTER's cost. Switched off for this baseline ("absent"): the transit router carries no per-mode constant in the baseline.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `raptorModeCost.representation` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: Whether a PT SUBMODE'S OWN CONSTANT reaches the router that picks the submode. absent: the pre-change state - SwissRailRaptor prices a boarded leg as DefaultRaptorInVehicleCostCalculator does, in-vehicle seconds times one coefficient and nothing else, so the constants C.asc.bus/-.rail/-.light_rail/-.ferry reach SCORING and not the ROUTER, and the one per-submode value RaptorUtils.createParameters does copy across (marginalUtilityOfTraveling) is emitted identically for all four submodes; over the F31 arm's whole plan memory only 974 of 154,347 persons (0.63%) held plans differing in PT submode at all (9.160). mode_constant: citysim.RaptorModeCostCalculator adds the boarded submode's own scoring.modeParams constant to the raptor's in-vehicle cost, once per boarded leg. It introduces NO NEW VALUE - the constants are already declared as C.asc.* - so this gate is not a taste to calibrate but a consistency between the router's objective and the scoring function the plan is judged by. It also makes PT dearer against the raptor's direct walk, which is a real behavioural change and is why `absent` is shipped. One-gate discipline mirroring C.crowding.representation and A.bike_stress.representation - `absent` recovers the previous model exactly.

#### `C.scoring.activity_minimal_applied_s`

The minimal activity duration written per activity type, derived at launch as in the reference city; 0 s for every type while C.scoring.activity_minimal_duration_s is 0.

***derived** · status **computed** · DECISIONS.md §9.204*

> **Derived from** `C.scoring.activity_minimal_duration_s`, `C.scoring.activity_typical_duration_s`: min(C.scoring.activity_minimal_duration_s, typical duration) per activity type; the harness supplies it under the derived runtime role

#### `C.scoring.activity_minimal_duration_s`

The minimal duration an activity must reach before it scores, in seconds. 0 for this city: the baseline applies no minimal duration, which is what MATSim's own undefined default means, written as a zero floor so the harness's min(minimal, typical) identity holds for every activity type.

***definition** · status **active** · DECISIONS.md §9.204*

#### `C.scoring.activity_typical_duration_s`

Provisional typical activity duration. Moved from C.smoke.activity_duration on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.activityParams[*].typicalDuration` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.scoring.marginal_utility_of_money`

Provisional mean money sensitivity, varied by personal budget. Moved from C.smoke.money on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.marginalUtilityOfMoney` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.scoring.marginal_utility_of_traveling`

Provisional travel time disutility. Moved from C.smoke.travel on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.modeParams[*].marginalUtilityOfTraveling_util_hr` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.scoring.mode_constant`

Zero mode constants: no target shares encoded. Moved from C.smoke.mode_constant on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.modeParams[*].constant`*

#### `C.scoring.monetary_distance_rate`

Provisional distance-based user costs, not observed fare schedules. PT distance money is zero because the boarding fare handler charges each completed ride; double pricing is refused at startup. Moved from C.smoke.distance_money on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.modeParams[*].monetaryDistanceRate` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.scoring.performing_utils_per_h`

Provisional activity utility. Moved from C.smoke.performing on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.performing` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.scoring.utility_of_line_switch`

Provisional inconvenience per PT transfer, separate from experienced wait and walk. Moved from C.smoke.transfer on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.utilityOfLineSwitch` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.scoring.waiting_pt`

Provisional waiting penalty greater than the in-vehicle travel penalty. Moved from C.smoke.waiting_pt on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.waitingPt` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.time_weights.beta_headway`

Weight on service headway, as a ratio to in-vehicle time. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

#### `C.time_weights.beta_reliability`

Weight on travel time variability, as a ratio to in-vehicle time - the RELIABILITY RATIO in its standard form, the standard deviation of journey time valued as a multiple of its mean. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

#### `C.time_weights.headway_utils_per_min`

Provisional schedule-delay price: half an in-vehicle minute per headway minute. Bound directly because RUN.scoring.translation is bound_fields: the harness derives this price from the trip-weighted value of time only under the C1 translation (9.204). Renamed from C.smoke.headway_price on 21 September 2026.

***assumed** · status **active** · DECISIONS.md §9.204 · MATSim `serviceQuality.headwayUtilsPerMin` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.time_weights.reliability_utils_per_min`

Provisional price of delay standard deviation measured from the preceding iteration. Bound directly because RUN.scoring.translation is bound_fields: the harness derives this price from the trip-weighted value of time only under the C1 translation (9.204). Renamed from C.smoke.reliability_price on 21 September 2026.

***assumed** · status **active** · DECISIONS.md §9.204 · MATSim `serviceQuality.reliabilityUtilsPerMin` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.time_weights.service_quality_representation`

Enable the existing behavioural mechanism in the broad provisional baseline. Moved from RUN.smoke.service_quality on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `serviceQuality.representation`*

## Baseline run settings the city declares itself (9.187, 9.204)

*`cities/mumbai/registry/RUN_baseline.json` - 2 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `RUN.replanning.strategy_subpopulations` | `{"SubtourModeChoice": ["person"]}` | subpopulation_names_per_strategy | `definition` | - |
| `RUN.replanning.subpopulations` | `["person", "freight"]` | subpopulation_names | `definition` | - |

#### `RUN.replanning.strategy_subpopulations`

Apply baseline choice strategies to residents.

***definition** · status **active** · DECISIONS.md §9.204*

#### `RUN.replanning.subpopulations`

The subpopulations the plans carry, in the framework's vocabulary (src/build/subpopulations.py): `person` for a resident, `freight` for a goods movement. Until 21 September 2026 (9.204) this city wrote `resident`, which the framework's readers and its income-scoring exclusion did not know.

***definition** · status **active** · DECISIONS.md §9.204*

## Framework run-side fields: moved from the private baseline namespace or adopted from the reference city (9.202)

*`cities/mumbai/registry/RUN_framework.json` - 105 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `RUN.controler.compression_type` | `gzip` | enum | `definition` | - |
| `RUN.controler.create_graphs` | `false` | boolean | `definition` | - |
| `RUN.controler.first_iteration` | `0` | iterations | `definition` | - |
| `RUN.controler.last_iteration` | `8` | iterations | `definition` | - |
| `RUN.controler.overwrite_files` | `failIfDirectoryExists` | policy | `definition` | - |
| `RUN.controler.write_events_interval` | `1` | iterations | `definition` | - |
| `RUN.controler.write_plans_interval` | `1` | iterations | `definition` | - |
| `RUN.controler.write_trips_interval` | `1` | iterations | `definition` | - |
| `RUN.gate.ceiling_poll_s` | `60` | seconds | `definition` | - |
| `RUN.gate.interval_iterations` | `0` | iterations | `definition` | - |
| `RUN.gate.reader_timeout_s` | `1800` | seconds | `definition` | - |
| `RUN.gate.retry_interval_s` | `300` | seconds | `definition` | - |
| `RUN.gate.stall_kill_s` | `1800` | seconds | `definition` | - |
| `RUN.gate.wall_ceiling_h` | `0` | hours | `definition` | - |
| `RUN.machine.event_handler_threads` | `4` | threads | `definition` | - |
| `RUN.machine.events_one_thread_per_handler` | `false` | boolean | `definition` | - |
| `RUN.machine.events_synchronize_on_simsteps` | `true` | boolean | `definition` | - |
| `RUN.machine.gc_collector` | `ParallelGC` | enum | `assumed` | `ParallelGC`, `G1GC` |
| `RUN.machine.gc_log` | `true` | boolean | `definition` | - |
| `RUN.machine.heap_floor_gib` | `7.4` | GiB | `measured` | **held fixed** |
| `RUN.machine.heap_per_fraction_gib` | `2400.0` | GiB_per_unit_fraction | `measured` | **held fixed** |
| `RUN.machine.jfr_profile` | `false` | boolean | `definition` | - |
| `RUN.machine.replanning_threads` | `2` | threads | `definition` | - |
| `RUN.machine.seed` | `20260810` | integer_seed | `definition` | - |
| `RUN.machine.telemetry_requires_simstep_barrier` | `true` | boolean | `definition` | - |
| `RUN.machine.threads` | `2` | threads | `definition` | - |
| `RUN.machine.xmx` | `16g` | jvm_heap | `definition` | - |
| `RUN.mode_choice.chain_based_modes` | `["car", "bike", "motorbike"]` | enum | `definition` | - |
| `RUN.mode_choice.consider_car_availability` | `true` | boolean | `definition` | - |
| `RUN.mode_choice.coord_distance_m` | `100.0` | metres | `literature` | 0 - 100 |
| `RUN.mode_choice.modes` | `["car", "ride", "walk", "bike", "motorbike", "taxi", "auto_rickshaw", "pt"]` | enum | `definition` | - |
| `RUN.mode_choice.proba_random_single_trip_mode` | `0.5` | probability | `definition` | - |
| `RUN.mode_choice.pt_submode_alternatives` | `aggregate` | categorical | `assumed` | `aggregate`, `alternatives` |
| `RUN.mode_choice.pt_submode_seed` | `bus` | enum | `assumed` | `bus`, `rail`, `tram`, `ferry` |
| `RUN.mode_choice.subtour_behavior` | `betweenAllAndFewerConstraints` | enum | `literature` | `betweenAllAndFewerConstraints`, `fromSpecifiedModesToSpecifiedModes` |
| `RUN.monitor.live_poll_s` | `0.5` | seconds | `definition` | - |
| `RUN.monitor.pace_band_s` | `[217, 253]` | seconds_per_iteration | `assumed` | **held fixed** |
| `RUN.monitor.poll_s` | `3` | seconds | `definition` | - |
| `RUN.monitor.port` | `8731` | tcp_port | `definition` | - |
| `RUN.monitor.progress_interval_s` | `30` | seconds | `definition` | - |
| `RUN.monitor.solo_check_iterations` | `[2, 5]` | iteration_range | `definition` | - |
| `RUN.monitor.stall_s` | `300` | seconds | `definition` | - |
| `RUN.qsim.end_time_h` | `36` | hours | `definition` | - |
| `RUN.qsim.link_dynamics` | `PassingQ` | enum | `definition` | - |
| `RUN.qsim.main_mode` | `["car", "ride", "walk", "bike", "motorbike", "taxi", "auto_rickshaw", "truck", "freight_rail"]` | enum | `definition` | - |
| `RUN.qsim.mode_vehicle_fields` | `{"car": {"length_m_field": "A.vehicle.car.length_m", "width_m_field": "A.vehicle.car.width_m", "pce_field":...` | registry_field_mapping | `definition` | - |
| `RUN.qsim.remove_stuck_vehicles` | `true` | boolean | `definition` | - |
| `RUN.qsim.snapshot_period` | `00:00:00` | hh:mm:ss | `definition` | - |
| `RUN.qsim.start_time_h` | `0` | hours | `definition` | - |
| `RUN.qsim.stuck_time_s` | `3600.0` | s | `definition` | - |
| `RUN.qsim.traffic_dynamics` | `queue` | enum | `definition` | - |
| `RUN.qsim.vehicle_behavior` | `teleport` | enum | `definition` | - |
| `RUN.qsim.vehicles_source` | `modeVehicleTypesFromVehiclesData` | policy | `definition` | - |
| `RUN.relaxation.drift_tolerance_pp` | `0.5` | percentage_points | `assumed` | 0.1 - 1 |
| `RUN.relaxation.settle_margin_iterations` | `10` | iterations | `assumed` | 1 - 100 |
| `RUN.replanning.fraction_to_disable_innovation` | `0.8` | share_of_iterations | `definition` | - |
| `RUN.replanning.max_agent_plan_memory` | `5` | plans | `literature` | 3 - 10 |
| `RUN.replanning.plan_selector_for_removal` | `WorstPlanSelector` | enum | `assumed` | `WorstPlanSelector`, `SelectRandom`, `SelectExpBetaForRemoval`, `ChangeExpBetaForRemoval`, `PathSizeLogitSelectorForRemoval` |
| `RUN.replanning.score_msa_fraction` | *(null - unobtained)* | share_of_iterations | `derived` | derived: the literal MATSim writes for its own default when the representation  |
| `RUN.replanning.score_msa_representation` | `absent` | categorical | `assumed` | `absent`, `at_innovation_cutoff` |
| `RUN.replanning.time_mutation_range_s` | `1800.0` | seconds | `literature` | 600 - 1800 |
| `RUN.replanning.weights` | `{"ChangeExpBeta": 0.7, "SubtourModeChoice": 0.3}` | strategy_weight | `definition` | - |
| `RUN.routing.access_egress_consistency_check` | `reroute` | enum | `assumed` | `reroute`, `disable`, `abortOnInconsistency` |
| `RUN.routing.access_egress_type` | `accessEgressModeToLink` | policy | `definition` | - |
| `RUN.routing.access_walk_beeline_factor` | `1.3` | ratio | `assumed` | plus/minus 50% |
| `RUN.routing.access_walk_speed_ms` | `1.2` | m/s | `assumed` | plus/minus 50% |
| `RUN.routing.activity_link_assignment` | `mode_specific_access` | policy | `definition` | - |
| `RUN.routing.clear_default_teleported_params` | `true` | boolean | `definition` | - |
| `RUN.routing.network_modes` | `["car", "ride", "walk", "bike", "motorbike", "taxi", "auto_rickshaw", "truck", "freight_rail"]` | enum | `definition` | - |
| `RUN.routing.pt_submode_scoring` | `aggregate` | enum | `definition` | - |
| `RUN.routing.routing_randomness` | `3.0` | dimensionless | `literature` | 0 - 5 |
| `RUN.sample.flow_capacity_factor` | *(null - unobtained)* | share_of_capacity | `derived` | derived: flowCapacityFactor = RUN.sample.fraction, the standard MATSim scaling  |
| `RUN.sample.fraction` | `1.0` | share_of_population | `assumed` | 0.001 - 1 |
| `RUN.sample.storage_capacity_exponent` | `1.0` | exponent | `derived` | derived: storageCapacityFactor = fraction ** 1.0 = flowCapacityFactor. MATSim e |
| `RUN.sample.storage_capacity_factor` | *(null - unobtained)* | share_of_capacity | `derived` | derived: storageCapacityFactor = RUN.sample.fraction ** RUN.sample.storage_capa |
| `RUN.sample.transit_capacity_floor` | `1` | seats | `assumed` | 1 - 4 |
| `RUN.sample.transit_capacity_scaling` | `true` | boolean | `derived` | derived: seats = max(floor, round(seats x RUN.sample.fraction)); not scaling it |
| `RUN.sample.transit_pce_scaling` | `true` | boolean | `derived` | derived: pce = pce x RUN.sample.fraction for every transit vehicle type, no flo |
| `RUN.sample.unit` | `household` | enum | `derived` | derived: the citywide plans carry householdId (build_plans.py writes the househ |
| `RUN.scoring.brain_exp_beta` | `1.0` | logit_scale | `literature` | 0.5 - 2 |
| `RUN.scoring.early_departure_utils_per_h` | `0.0` | utils_per_hour | `assumed` | -18 - 0 |
| `RUN.scoring.late_arrival_utils_per_h` | `-18.0` | utils_per_hour | `literature` | -36 - -6 |
| `RUN.scoring.learning_rate` | `1.0` | share | `definition` | - |
| `RUN.scoring.path_size_logit_beta` | `1.0` | dimensionless | `literature` | 0.5 - 2 |
| `RUN.scoring.translation` | `bound_fields` | policy | `definition` | - |
| `RUN.scoring.waiting_utils_per_h` | `0.0` | utils_per_hour | `assumed` | -6 - 0 |
| `RUN.storage.extract_grace_s` | `3600` | seconds | `definition` | - |
| `RUN.storage.raw_cap_gb` | `500` | gibibytes | `definition` | - |
| `RUN.storage.reader_timeout_s` | `3600` | seconds | `definition` | - |
| `RUN.telemetry.live_interval_s` | `3600.0` | seconds | `definition` | - |
| `RUN.transit.transit_modes` | `["pt"]` | mode_names | `definition` | - |
| `RUN.transit.use_transit` | `true` | boolean | `definition` | - |
| `RUN.transit_router.access_egress_basis` | `beeline` | enum | `assumed` | `beeline`, `network` |
| `RUN.transit_router.additional_transfer_time_s` | `0.0` | s | `assumed` | 0 - 120 |
| `RUN.transit_router.direct_walk_basis` | `network` | enum | `definition` | - |
| `RUN.transit_router.direct_walk_factor` | `1.0` | ratio | `literature` | 1 - 2 |
| `RUN.transit_router.extension_radius_m` | `200.0` | metres | `literature` | 100 - 500 |
| `RUN.transit_router.max_beeline_walk_connection_m` | `300.0` | metres | `literature` | 100 - 500 |
| `RUN.transit_router.search_radius_m` | `1000.0` | metres | `literature` | 500 - 2000 |
| `RUN.travel_time.aggregator` | `optimistic` | enum | `assumed` | `optimistic`, `experimental_LastMile` |
| `RUN.travel_time.analysed_modes` | `["car"]` | mode_names | `definition` | - |
| `RUN.travel_time.bin_size_s` | `300` | seconds | `literature` | 60 - 900 |
| `RUN.travel_time.filter_modes` | `true` | boolean | `definition` | - |
| `RUN.travel_time.getter` | `average` | enum | `assumed` | `average`, `linearinterpolation` |
| `RUN.travel_time.separate_modes` | `false` | boolean | `definition` | - |

#### `RUN.controler.compression_type`

Output compression. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.compressionType`*

#### `RUN.controler.create_graphs`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.controler.createGraphs on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.createGraphs`*

#### `RUN.controler.first_iteration`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.controler.firstIteration on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.firstIteration`*

#### `RUN.controler.last_iteration`

Bounded nine-iteration learning check of the explicit small population; no convergence or citywide scaling claim. The existing automatic JVM ceiling remains in force. Moved from RUN.smoke.controler.lastIteration on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.lastIteration`*

#### `RUN.controler.overwrite_files`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.controler.overwriteFiles on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.overwriteFiles`*

#### `RUN.controler.write_events_interval`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.controler.writeEventsInterval on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.writeEventsInterval`*

#### `RUN.controler.write_plans_interval`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.controler.writePlansInterval on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.writePlansInterval`*

#### `RUN.controler.write_trips_interval`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.controler.writeTripsInterval on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `controler.writeTripsInterval`*

#### `RUN.gate.ceiling_poll_s`

How often the ceiling watcher looks at the clock. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.gate.interval_iterations`

How often the gate watcher reads the modes against their targets. 0 for this city: no target exists to judge a mode by, so the only automatic stop is the wall ceiling every run overlay declares (RUN.gate.wall_ceiling_h).

***definition** · status **active** · DECISIONS.md §9.204*

#### `RUN.gate.reader_timeout_s`

How long the gate watcher gives one milestone reading (report_mode_ridership.py --gate-json) before it gives up and retries at RUN.gate.retry_interval_s. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.gate.retry_interval_s`

How long the runner's gate watcher waits before trying a milestone again whose per-iteration tables are not written yet (#131). Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.gate.stall_kill_s`

How long the run's own log may go silent before the runner stops the JVM, writing `stopped_at_stall` with the silence and the last ended iteration. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.gate.wall_ceiling_h`

The wall-clock ceiling the runner enforces on its own run, in hours. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.machine.event_handler_threads`

Threads for MATSim's parallel events manager. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `eventsManager.numberOfThreads`*

#### `RUN.machine.events_one_thread_per_handler`

Give each registered event handler its own thread instead of sharing RUN.machine.event_handler_threads workers. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `eventsManager.oneThreadPerHandler`*

#### `RUN.machine.events_synchronize_on_simsteps`

Whether the qsim waits for the events pipeline at every sim-step. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `eventsManager.synchronizeOnSimSteps`*

#### `RUN.machine.gc_collector`

The JVM garbage collector the launcher passes (-XX:+Use<collector>). Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: The two collectors the pinned JDK offers for a 48 GB heap. WALL TIME ONLY: the collector changes no model state (the twelfth report's performance pass: one full collection per iteration under ParallelGC, 2.5-4.0 % of an arm's wall). A change is a toolchain change priced by a 25 % probe before any arm carries it (DECISIONS.md 9.153).

#### `RUN.machine.gc_log`

Whether the JVM writes a GC log to <run>/gc.log. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.machine.heap_floor_gib`

The sample-independent part of the heap rule. MEASURED as the live set after the last full collection: 7.36 GiB in the gc.log of 20260921T182708_2it_100pct (the explicit 1,000-person case: the mapped regional network, the combined feed and the routers) and 7.81 GiB in 20260921T220701_2it_0.1pct with 26,884 agents at one or two plans - 18 KB an agent, the reference city's per-plan rate. 9.205 read 13.74 from the pre-collection peak of a 16g heap, which is the heap size, not the need (9.206).

***measured** · status **active** · DECISIONS.md §9.206*

> **Held fixed.** the LIVE SET after the last full collection of a case with no population to speak of, read from its gc.log (Pause Full N->M: M), never the pre-collection peak - under ParallelGC with -Xms = -Xmx the peak tracks the heap GIVEN (16g peaked at 13.74, 24g at 17.30), not the heap needed; re-read from every longer case
>
> *Departure requires: a higher live set after a full collection at a negligible population in a later Mumbai gc.log*

#### `RUN.machine.heap_per_fraction_gib`

The sample-dependent part of the heap rule, per unit of RUN.sample.fraction of the 27.06 M-person core, at plan memory 5: 2,400 GiB - so 1 % of the core (270,000 agents) needs 31.4 GiB with the floor, 2 % 55 GiB (the last this 63 GB host holds) and 5 % (1.35 M agents) 127 GiB. The 3,600 of 9.205 was the slope between two PRE-collection peaks of differently sized heaps (9.206). The fraction a defensible reading needs is the open question of docs/scaling.md; the memory is no longer the first constraint below 2 %, the flow identity is.

***measured** · status **active** · DECISIONS.md §9.206*

> **Held fixed.** persons in the core (27.06 M) x RUN.replanning.max_agent_plan_memory x the live heap a routed plan holds at steady state - 19 KB on the reference city's 25 % arm 20260916T063903_250it_25pct (20-28.6 GiB after a full collection for 155,000 agents at 8 plans over a 5 GiB floor), the same Java stack; 27.06 M x 5 x 19 KB = 2,400 GiB per unit fraction; re-read from the 1 % case's own live set once its plan memory has filled
>
> *Departure requires: a live set after a full collection at another fraction, or a per-plan rate read from a Mumbai gc.log whose plan memory has filled*

#### `RUN.machine.jfr_profile`

Whether the JVM records a Java Flight Recorder profile of the run into <run>/profile.jfr. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.machine.replanning_threads`

Replanning threads for the baseline case.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `global.numberOfThreads`*

#### `RUN.machine.seed`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.global.randomSeed on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `global.randomSeed`*

#### `RUN.machine.telemetry_requires_simstep_barrier`

Whether RunTelemetry depends on the sim-step barrier for memory visibility. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.machine.threads`

qsim threads for the baseline case; the explicit population is small enough that two threads keep the machine free.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.numberOfThreads`*

#### `RUN.machine.xmx`

JVM heap for the baseline case (-Xms = -Xmx). 16g served the 1,000-person population; the heap rule fields carry the reference city's measurement until a Mumbai peak is measured.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.mode_choice.chain_based_modes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.subtourModeChoice.chainBasedModes on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `subtourModeChoice.chainBasedModes`*

#### `RUN.mode_choice.consider_car_availability`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.subtourModeChoice.considerCarAvailability on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `subtourModeChoice.considerCarAvailability`*

#### `RUN.mode_choice.coord_distance_m`

Distance within which two activity coordinates count as the same subtour location. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `subtourModeChoice.coordDistance` · sweep role **uncertainty***

> **Sweep basis.** 0 is the MATSim default and was live here unset; 100 is Open Berlin's value.

#### `RUN.mode_choice.modes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.subtourModeChoice.modes on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `subtourModeChoice.modes`*

#### `RUN.mode_choice.proba_random_single_trip_mode`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.subtourModeChoice.probaForRandomSingleTripMode on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `subtourModeChoice.probaForRandomSingleTripMode`*

#### `RUN.mode_choice.pt_submode_alternatives`

The representation gate for plan-level PT submode choice (#49; the 20 August 2026 individualise-every-mode directive, Tier C). Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `ptSubmodeChoice.representation` · sweep role **answer***

> **Sweep basis.** adopted from the reference city: Whether the four scheduled PT submodes are ALTERNATIVES A PLAN CAN HOLD, or one `pt` alternative whose submode a router picks. `aggregate` is the pre-change state and every arm this project has run: RUN.mode_choice.modes offers `pt`, SwissRailRaptor decides bus against rail against tram against ferry downstream, and a whole-file pass over the F31 arm's plan memory found 974 of 154,347 persons - 0.63 % - holding plans that differ in which submode they use (9.160). So a declared submode constant reallocates between submodes for under one per cent of the population, and C.asc.bus and C.asc.light_rail are plan-choice levers (pt against car) rather than submode levers. `alternatives` installs one SwissRailRaptor per submode over that submode's own routes and binds each as the routing module for a plan-level mode of the same name, so SubtourModeChoice proposes `bus` against `rail` the way it proposes `car` against `bike`. WHAT THE SWEEP ANSWERS: how much of light rail's -57.3 % against heavy rail's +225.0 % - two halves of one split - is a preference and how much is a choice set that never held the alternative. IT COSTS SOMETHING REAL AND THE ARM MUST READ IT: under `alternatives` no single plan-level trip can combine two submodes, because the umbrella that represented a bus-then-train journey is out of the choice set. Multi-leg pt trips must be read on BOTH arms of the pair, and the gate ships at `aggregate` for that reason.

#### `RUN.mode_choice.pt_submode_seed`

The submode a seeded `pt` leg is rewritten to when RUN.mode_choice.pt_submode_alternatives is `alternatives`. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `ptSubmodeChoice.seedSubmode` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: The declared submode vocabulary. `bus` is the value because it is the only submode with network-wide coverage - 1,448 of the 2,139 mapped transit vehicles - so a seeded pt leg rewritten to it is a plan the router can answer almost anywhere, while a rewrite to `ferry` (107 vehicles, one crossing) would be refused for nearly every seeded trip and the person would start the search with no pt plan at all. WHAT THE SWEEP ANSWERS: whether the submode split the search settles at depends on where it starts. It is inert unless RUN.mode_choice.pt_submode_alternatives is `alternatives`, and the seed biases where the search starts, never what selection keeps.

#### `RUN.mode_choice.subtour_behavior`

How subtour mode choice treats tours it cannot close. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `subtourModeChoice.behavior` · sweep role **uncertainty***

> **Sweep basis.** the two values MATSim offers. Open Berlin, Leipzig and Kelheim all set the former; the latter is the MATSim default and was live here unset.

#### `RUN.monitor.live_poll_s`

How often the live view re-reads status WHILE THE MOBSIM IS SWEEPING. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.monitor.pace_band_s`

The measured s/iteration band a healthy 25% x 1000 WEEKDAY arm paces inside on this machine (median 234 s through iteration 135 on the arm itself; 217-253 s across the closed family's solo iterations 2-5, DECISIONS.md 9.72). Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202*

> **Held fixed.** the reference city's measurement, adopted; no Mumbai measurement exists and the field is not varied
>
> *Departure requires: a Mumbai measurement of the same quantity*

#### `RUN.monitor.poll_s`

How often the page re-reads status. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.monitor.port`

Loopback port for the live run view. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.monitor.progress_interval_s`

How often the machine-readable _progress.json digest is refreshed (issue #76). Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.monitor.solo_check_iterations`

Which solo iterations the conditional-replication rule reads (DECISIONS.md 9.72: arm B launches only if arm A's SOLO ITERATIONS 2-5 pace inside RUN.monitor.pace_band_s). Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.monitor.stall_s`

How long the log may go untouched before the live view calls a run stalled rather than running. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.qsim.end_time_h`

Observe overnight completion after the all-day departure window. The freight prototype measured nearly ten-hour road movements, which a 30-hour horizon censored for late departures. This is an observation horizon, not a speed or demand adjustment. Moved from RUN.smoke.qsim.endTime on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.endTime`*

#### `RUN.qsim.link_dynamics`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.linkDynamics on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.linkDynamics`*

#### `RUN.qsim.main_mode`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.mainMode on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.mainMode`*

#### `RUN.qsim.mode_vehicle_fields`

Explicit network-mode vehicle definitions: one profile per routed mode, each naming the A.vehicle.<mode>.* scalar fields (registry/A_vehicles.json) for its length, width, PCE, seats, standing room and speed cap. Replaces the per-launch vehicle writer of the city's own launcher (9.204).

***definition** · status **active** · DECISIONS.md §9.204*

#### `RUN.qsim.remove_stuck_vehicles`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.removeStuckVehicles on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.removeStuckVehicles`*

#### `RUN.qsim.snapshot_period`

Interval between mobsim vehicle-position snapshots. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.snapshotperiod`*

#### `RUN.qsim.start_time_h`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.startTime on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.startTime`*

#### `RUN.qsim.stuck_time_s`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.stuckTime on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.stuckTime`*

#### `RUN.qsim.traffic_dynamics`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.trafficDynamics on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.trafficDynamics`*

#### `RUN.qsim.vehicle_behavior`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.vehicleBehavior on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.vehicleBehavior`*

#### `RUN.qsim.vehicles_source`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.qsim.vehiclesSource on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `qsim.vehiclesSource`*

#### `RUN.relaxation.drift_tolerance_pp`

Largest absolute mode-share movement, in percentage points, that a run may still show after innovation is disabled and still be reported as settled. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: There is no standard for how flat a MATSim mode-share trace must be before a run may be called settled, so the tolerance is swept rather than asserted. The lower bound is about the resolution a 10% sample can support; the upper bound is loose enough that a run failing it is unarguably still moving. The verdict is always reported WITH the tolerance beside it and with the two iteration numbers it was measured between, so a reader can apply their own.

#### `RUN.relaxation.settle_margin_iterations`

Iterations to skip AFTER the innovation cutoff before drift is measured, so the relaxation verdict scores relaxation and not the selection snap. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: the lower bound is the MEASURED duration of the snap itself - one iteration, at both fractions - so it is the smallest margin that can exclude it. The upper bound is where the excluded window starts to be a meaningful share of a 200-iteration post-cutoff tail: beyond it the metric passes by measuring less rather than by the run being flatter, which is the failure mode this field must not have

#### `RUN.replanning.fraction_to_disable_innovation`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.replanning.fractionOfIterationsToDisableInnovation on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `replanning.fractionOfIterationsToDisableInnovation`*

#### `RUN.replanning.max_agent_plan_memory`

Plans an agent keeps: MATSim's own default, the leanest choice set the reference city's sweep admits with room to innovate. The citywide plans carry ONE initial plan a person (build_plans.py; the assembly refuses a memory below the supplied count), so the 9 the retired explicit 1,000-person case needed for its eight seeded alternatives (9.204) bought nothing but heap: the reference city's 25 % arm lives at about 19 KB a plan (20-28.6 GiB after a full collection for 155,000 agents at 8 plans over a 5 GiB floor), so at 9 plans 1 % of the 27.06 M core needs 51 GiB against 63 GB and at 5 plans 32 GiB (9.206, D14). Inside the declared 3-10 sweep; the choice-set width it costs is what the equivalence experiments of docs/scaling.md measure.

***literature** · status **active** · DECISIONS.md §9.206 · MATSim `replanning.maxAgentPlanMemorySize` · sweep role **uncertainty***

#### `RUN.replanning.plan_selector_for_removal`

Which of an agent's plans is deleted when a new one arrives and plan memory (RUN.replanning.max_agent_plan_memory = 8) is full. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `replanning.planSelectorForRemoval` · sweep role **answer***

> **Sweep basis.** adopted from the reference city: MATSim's own five shipped selectors, and its own comment on the parameter: "The current default, WorstPlanSelector is not a good choice from a discrete choice theoretical perspective. Alternatives, however, have not been systematically tested." WHAT THE SWEEP ANSWERS: whether a mode's choice-set coverage is a preference or an artefact of deletion (#174). Coverage at iteration 300 of 20260909T015217_300it_25pct ranks the modes in the SAME ORDER as their attractiveness under the current scoring - car 77.55 %, walk 63.95 %, taxi 54.62 %, bike 29.03 %, pt 25.78 %, ride 20.05 % - which is exactly the pattern WorstPlanSelector would produce, since a mode whose plans score badly is evicted before it can be chosen, and its low share is then read at the gate as taste. `SelectRandom` breaks that feedback and is the control arm. The correlation has an innocent explanation too (an unattractive mode is proposed less often), and separating them is what the paired arm is for.

#### `RUN.replanning.score_msa_fraction`

The iteration fraction at which a plan score becomes a moving average. Derived at launch from the representation gate, as in the reference city.

***derived** · status **computed** · DECISIONS.md §9.202 · MATSim `scoring.fractionOfIterationsToStartScoreMSA`*

> **Derived from** `RUN.replanning.score_msa_representation`: the literal MATSim writes for its own default when the representation is absent; the launcher supplies it under the derived runtime role

#### `RUN.replanning.score_msa_representation`

The representation gate for score averaging after the innovation cutoff. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **answer***

> **Sweep basis.** adopted from the reference city: Whether a plan's score is a MOVING AVERAGE over its executions once innovation stops, or the single most recent execution. absent: the pre-change state and MATSim's own default - scoring.fractionOfIterationsToStartScoreMSA is `null`, every plan carries the score of its last execution, and at the innovation cutoff every agent selects the maximum of noisy single-execution scores simultaneously. at_innovation_cutoff: the fraction is set to RUN.replanning.fraction_to_disable_innovation, so score averaging begins exactly where new-plan creation ends, which is the pairing the MATSim reference text describes. It introduces NO NEW NUMBER - the fraction is the innovation cutoff already declared - so this gate is not a value to calibrate but a consistency between what the search stops doing and what the score starts meaning. `absent` is shipped because switching it on is a real change to how every plan is scored and belongs to an arm that declares it. Named as the one-field candidate cause of the convergence penalty by the 10 September 2026 assessment: it predicts BOTH measured symptoms of `20260909T015217_300it_25pct` - the +2.211 pp car snap at the cutoff and the average plan score peaking at 19.2049 and then falling to 14.5679 - and no other single field predicts either. One-gate discipline mirroring C.crowding.representation and C.raptor.mode_cost_representation: `absent` recovers the previous model exactly, and it is emitted as the literal MATSim writes for its own default, so the recovery is byte-identical rather than asserted. WHAT THE SWEEP ANSWERS: Which of the three candidate causes of the convergence penalty - the scoring function, the choice set, or the routers - is responsible is the open question (#163, #172). This gate tests the scoring-function branch at the cost of one arm and is the only one of the three that is a single field.

#### `RUN.replanning.time_mutation_range_s`

The half-width of the uniform departure-time mutation TimeAllocationMutator applies. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `timeAllocationMutator.mutationRange` · sweep role **uncertainty***

> **Sweep basis.** MATSim ships 1800 s and this model inherited it SILENTLY - the value reached the mobsim through no declaration at all until 9.85, which is exactly the undeclared modelling choice this registry exists to prevent. It is swept rather than pinned because it is MEASURED to be load-bearing on a quantity that is not its own: it sets how far the two members of a DECLARED joint pair drift apart, and at 1800 s the measured median gap between a companion and their declared driver is 10.3 min with p90 at 45.1 min, against a pairing tolerance of 15 min. The lower bound is the coarsest bin the travel-time calculator resolves (RUN.travel_time.bin_size_s = 300) doubled; the upper is MATSim's own default. Narrowing it is NOT a way to buy pairings - B.ride.bound_pairing_window_min is derived from it, so the tolerance follows the drift rather than chasing it.

#### `RUN.replanning.weights`

Score-based selection and mode exploration. Moved from RUN.smoke.strategy_weights on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `replanning.strategysettings[*].weight`*

#### `RUN.routing.access_egress_consistency_check`

What MATSim does with an input plan whose trips carry no access or egress legs. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `routing.accessEgressConsistencyCheck` · sweep role **answer***

> **Sweep basis.** adopted from the reference city: MATSim's own three settings for what happens when an input plan's trips do not carry the access and egress legs the routing configuration says they should. It was one of the 21 undeclared MATSim defaults (#155) and it was ACCEPTED there, on the reasoning that RUN.routing.access_egress_type was `none` so no leg was expected to carry an access stub and the check had nothing to find - with the entry stating in terms that it becomes a decision the moment that field stops being `none`. It has. WHAT THE SWEEP ANSWERS: whether MATSim's own repair of an input plan is the mechanism that produces the trips PersonPrepareForSim then rejects. `reroute` repairs rather than aborts and is the conservative setting when nothing is expected to be wrong; `abortOnInconsistency` refuses instead of repairing, which is the diagnostic setting - it names the trips rather than rewriting them; `disable` leaves input plans alone and lets the ordinary router build the access legs on its own first pass.

#### `RUN.routing.access_egress_type`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.routing.accessEgressType on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `routing.accessEgressType`*

#### `RUN.routing.access_walk_beeline_factor`

Explicit routing helper configuration for the provisional network-mode smoke; main walk and bike use network routing. Moved from RUN.smoke.stub_walk_distance_factor on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `routing.teleportedModeParameters[non_network_walk].beelineDistanceFactor` · sweep role **uncertainty***

> **Sweep basis.** Provisional access stub sensitivity.

#### `RUN.routing.access_walk_speed_ms`

Explicit routing helper configuration for the provisional network-mode smoke; main walk and bike use network routing. Moved from RUN.smoke.stub_walk_speed_ms on 21 September 2026: one key per MATSim parameter.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `routing.teleportedModeParameters[non_network_walk].teleportedModeSpeed` · sweep role **uncertainty***

> **Sweep basis.** Provisional access stub sensitivity.

#### `RUN.routing.activity_link_assignment`

Each mode uses its own permitted network and retains MATSim access/egress connectors, including boarding links off the walk network. Moved from RUN.smoke.activityLinks.assignment on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `activityLinks.assignment`*

#### `RUN.routing.clear_default_teleported_params`

Explicit routing helper configuration for the provisional network-mode smoke; main walk and bike use network routing. Moved from RUN.smoke.clear_default_teleported_params on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `routing.clearDefaultTeleportedModeParams`*

#### `RUN.routing.network_modes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.routing.networkModes on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `routing.networkModes`*

#### `RUN.routing.pt_submode_scoring`

Whether each scheduled transport mode is scored as a passenger mode of its own (per_submode) or every pt leg as one pt mode (aggregate). `aggregate` for this city: the transit router combines bus, suburban rail, metro and ferry under one pt mode (RUN.transit.transit_modes = [pt]) and one bound constant; splitting them is a declared change of its own once a ridership series per operator exists to score it by.

***definition** · status **active** · DECISIONS.md §9.204*

#### `RUN.routing.routing_randomness`

The width of the random utility the least-cost-path router draws per agent, so that two agents with the same origin, destination and departure time need not take the same road. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `routing.routingRandomness` · sweep role **uncertainty***

> **Sweep basis.** 0.0 is a deterministic least-cost router - every agent between one pair of links takes the identical path - and 3.0 is the value MATSim's own comment recommends ("3.0 seems to be a good value"), the width parameter of the log-normal distribution the money-versus-time trade-off is drawn from. WHAT THE SWEEP ANSWERS: how much of the route spread on this network is heterogeneous taste and how much is the network's own geometry. It bears on the count rung directly, because a deterministic router concentrates flow onto single links and a random one spreads it across parallel ones.

#### `RUN.sample.flow_capacity_factor`

Road flow capacity scaled to the sample. Derived at launch, as in the reference city. Moved from RUN.smoke.qsim.flowCapacityFactor on 21 September 2026: one key per MATSim parameter.

***derived** · status **computed** · DECISIONS.md §9.202 · MATSim `qsim.flowCapacityFactor`*

> **Derived from** `RUN.sample.fraction`: flowCapacityFactor = RUN.sample.fraction, the standard MATSim scaling rule

#### `RUN.sample.fraction`

Share of the population simulated. 1.0 for the explicit 1,000-person development case; a citywide case runs the plans built at B.population.plans_build_fraction at a fraction at or below it, declared on its overlay.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** the synthesised core population is 27.06 M persons (9.204) and the plans are written at B.population.plans_build_fraction (9.205); a fraction below one has no measured fidelity for this city (docs/scaling.md), and the floor admits the first citywide case the machine can run

#### `RUN.sample.storage_capacity_exponent`

The exponent relating storage capacity to the sample fraction. Adopted from the reference city's declaration; not a Mumbai observation.

***derived** · status **active** · DECISIONS.md §9.202*

> **Derived from** `RUN.sample.fraction`: storageCapacityFactor = fraction ** 1.0 = flowCapacityFactor. MATSim enforces the equality: GlobalConfigGroup.checkConsistency throws when the two differ by more than global.relativeTolerance, which defaults to 0.0

#### `RUN.sample.storage_capacity_factor`

Link storage capacity scaled to the sample. Derived at launch, as in the reference city. Moved from RUN.smoke.qsim.storageCapacityFactor on 21 September 2026: one key per MATSim parameter.

***derived** · status **computed** · DECISIONS.md §9.202 · MATSim `qsim.storageCapacityFactor`*

> **Derived from** `RUN.sample.fraction`, `RUN.sample.storage_capacity_exponent`: storageCapacityFactor = RUN.sample.fraction ** RUN.sample.storage_capacity_exponent, which at the declared exponent of 1.0 equals flowCapacityFactor exactly. MATSim's GlobalConfigGroup.checkConsistency throws when the two differ by more than global.relativeTolerance, which defaults to 0.0

#### `RUN.sample.transit_capacity_floor`

Minimum seats after scaling, so a vehicle never becomes unusable. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · sweep role **uncertainty***

> **Sweep basis.** chosen interval: 1 seat is the smallest usable vehicle, and the floor binds below about a 1.5% sample, where it makes capacity systematically too generous; the top of 4 tests whether a larger floor changes anything while crowding scoring is off (issue 12). No observed spread.

#### `RUN.sample.transit_capacity_scaling`

Scale transit vehicle seats by the sample fraction. Adopted from the reference city's declaration; not a Mumbai observation.

***derived** · status **active** · DECISIONS.md §9.202*

> **Derived from** `RUN.sample.fraction`: seats = max(floor, round(seats x RUN.sample.fraction)); not scaling it would give every vehicle 1/fraction times its real capacity

#### `RUN.sample.transit_pce_scaling`

Scale every transit vehicle type's passenger-car equivalent by the sample fraction, as the road flow capacities are. Adopted from the reference city's declaration; not a Mumbai observation.

***derived** · status **active** · DECISIONS.md §9.202*

> **Derived from** `RUN.sample.fraction`: pce = pce x RUN.sample.fraction for every transit vehicle type, no floor: the vehicle's share of a scaled link's flow is then the share it has of the real link's

#### `RUN.sample.unit`

Whether the population subsample keeps whole households or independent persons. `household` since the citywide plans (9.205); the explicit 1,000-person development population had none.

***derived** · status **active** · DECISIONS.md §9.205*

> **Derived from** `B.seed.master`: the citywide plans carry householdId (build_plans.py writes the households the nested hash keeps), so the sampler keeps whole households, as the reference city does

#### `RUN.scoring.brain_exp_beta`

The logit scale in the ChangeExpBeta plan-selection rule: how sharply an agent's probability of switching plans responds to the score difference between them. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.BrainExpBeta` · sweep role **uncertainty***

> **Sweep basis.** MATSim's own default is 1.0 and the manual treats it as the conventional starting point rather than a measured quantity. The interval spans the range in common use: below 1 agents respond more softly to a utility difference and mode shares flatten, above 1 they respond more sharply and the model can lock in. Nothing about Newcastle bears on it.

#### `RUN.scoring.early_departure_utils_per_h`

Penalty for leaving an activity before its earliest end time. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.earlyDeparture` · sweep role **uncertainty***

> **Sweep basis.** Zero is an assumption that leaving an activity early costs nothing beyond the activity utility already forgone, which is the usual MATSim treatment and avoids charging the same shortfall twice. The interval allows an explicit penalty up to the late-arrival rate for a sensitivity arm.

#### `RUN.scoring.late_arrival_utils_per_h`

Penalty for arriving at an activity after its latest start time. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.lateArrival` · sweep role **uncertainty***

> **Sweep basis.** MATSim's conventional value is -18 utils/h, three times a typical performing rate, and the manual presents it as a convention rather than an estimate. The interval spans one third to twice that. No Newcastle observation bears on it: the HTS held is aggregate and carries no schedule-adherence measure.

#### `RUN.scoring.learning_rate`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.scoring.learningRate on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.learningRate`*

#### `RUN.scoring.path_size_logit_beta`

The path-size logit's beta. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.pathSizeLogitBeta` · sweep role **uncertainty***

> **Sweep basis.** The path-size correction's exponent in the path-size logit of Ben-Akiva and Bierlaire (1999); 1.0 is the standard formulation and the framework default. WHAT THE SWEEP ANSWERS: how strongly two plans that overlap are treated as one alternative rather than two. It reads only under a path-size-logit selector, which is why it is declared in the same change as RUN.replanning.plan_selector_for_removal: `PathSizeLogitSelectorForRemoval` is one of that field's sweep members, and an arm that spent it would otherwise be spending this undeclared value with it.

#### `RUN.scoring.translation`

Where this city's MATSim scoring parameters come from. `bound_fields`: this city has no C1 nested-logit table; every scoring parameter is a bound registry field (C.scoring.mode_constant, C.scoring.marginal_utility_of_traveling, C.scoring.waiting_pt, C.scoring.utility_of_line_switch, the crowding and service-quality prices) and the harness translates nothing (9.204).

***definition** · status **active** · DECISIONS.md §9.204*

#### `RUN.scoring.waiting_utils_per_h`

Disutility of general waiting, over and above the opportunity cost of the time. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `scoring.waiting` · sweep role **uncertainty***

> **Sweep basis.** Zero avoids double-counting: general waiting is already priced through the forgone performing utility of the time. The interval allows an additional explicit disutility for a sensitivity arm. Distinct from scoring.waitingPt, which is DERIVED from the C1 beta_wait and is not this field.

#### `RUN.storage.extract_grace_s`

How long after a run's record was last written the store still treats it as inside its extraction window, and so refuses to trim it. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.storage.raw_cap_gb`

GIBIBYTES, not gigabytes, despite the `_gb` in the key: src/run/results_store.py multiplies this by 2^30, so 500 here is 500 GiB = 536.9 GB. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.storage.reader_timeout_s`

How long the results store gives each close-out reader (the --trend extraction, the final --json reading) before it records the extraction as failed. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202*

#### `RUN.telemetry.live_interval_s`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.telemetry.liveIntervalS on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `telemetry.liveIntervalS`*

#### `RUN.transit.transit_modes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.transit.transitModes on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `transit.transitModes`*

#### `RUN.transit.use_transit`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion. Moved from RUN.smoke.transit.useTransit on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `transit.useTransit`*

#### `RUN.transit_router.access_egress_basis`

How a pt trip reaches its first stop and leaves its last. `beeline` for the fold: the previous cases' behaviour, to be switched to `network` by a declared change of its own.

***assumed** · status **active** · DECISIONS.md §9.204 · sweep role **uncertainty***

> **Sweep basis.** beeline reproduces the pre-fold cases exactly (the raptor draws access and egress straight); network routes them on the walk network, which GOAL.md requirement 1 asks for and which is switched on once the walk network's reach to the boarding links is measured for this city

#### `RUN.transit_router.additional_transfer_time_s`

Extra seconds the transit router allocates at a line switch, MATSim's own "safety time that agents need to safely transfer from one line to another". Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `transitRouter.additionalTransferTime` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: 0.0 is the framework default this model has been running - a transferring passenger is assumed to need no time at all beyond the walk between stops. The upper bound is two minutes, the order of a safety margin a real passenger allows at an interchange. WHAT THE SWEEP ANSWERS: whether the raptor's willingness to build multi-leg itineraries is an artefact of costless transferring. It is NOT the same quantity as C.time_weights.beta_transfer_penalty_min, which prices the DISUTILITY of a transfer in the scoring function; this one changes which itineraries the router will return at all. #175 names it as the parameter anything charged in the raptor layer would interact with.

#### `RUN.transit_router.direct_walk_basis`

Compare transit with network walking, not a direct geographical chord. Moved from RUN.smoke.ptDirectWalk.basis on 21 September 2026: one key per MATSim parameter.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `ptDirectWalk.basis`*

#### `RUN.transit_router.direct_walk_factor`

Multiplier on the direct-walk cost the PT router compares every transit route against. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `transitRouter.directWalkFactor` · sweep role **uncertainty***

> **Sweep basis.** MATSim ships 1.0 and it was live here UNSET until 9.121: the PT router returns a direct walk whenever walk time x this factor x the walk disutility undercuts the best transit route. Declared so the comparison the ferry lost (#94) is visible; the value is unchanged. The upper bound is the largest value MATSim scenarios use to discourage long direct walks; the repair for the ferry is RUN.transit_router.direct_walk_basis, not this factor.

#### `RUN.transit_router.extension_radius_m`

When no stop lies within RUN.transit_router.search_radius_m of a trip end, the router searches out to the nearest stop's distance plus this margin. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `transitRouter.extensionRadius` · sweep role **uncertainty***

> **Sweep basis.** MATSim ships 200 m and it was live here UNSET until 9.120. Leipzig and Kelheim set 500 m, the upper bound.

#### `RUN.transit_router.max_beeline_walk_connection_m`

Maximum stop-to-stop distance at which the PT router will create a transfer. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `transitRouter.maxBeelineWalkConnectionDistance` · sweep role **uncertainty***

> **Sweep basis.** 100 m is the MATSim default that was live here unset; 300 m is the value Open Berlin, Leipzig and Kelheim all set. The upper bound spans Leipzig and Kelheim's 500 m extensionRadius.

#### `RUN.transit_router.search_radius_m`

Radius around a trip end within which the PT router considers stop facilities as access or egress points. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `transitRouter.searchRadius` · sweep role **uncertainty***

> **Sweep basis.** MATSim ships 1000 m and it was live here UNSET until 9.120 - the emitted config carried it as a jar default no reader could see. The sweep spans half to twice the default: the ferry's two wharves have 8,243 residents within 1 km and the value decides which of them the router lets walk to a wharf at all.

#### `RUN.travel_time.aggregator`

How a congested time bin with no link entry event is priced for the router. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `travelTimeCalculator.travelTimeAggregator` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: MATSim's own two alternatives, with its own comment naming the flaw in each: "`optimistic' assumes free speed (too optimistic); 'experimental_LastMile' is experimental and probably too pessimistic." WHAT THE SWEEP ANSWERS: what the router believes a link costs in a five-minute bin no vehicle entered. Under `optimistic` a link that is jammed solid - so jammed that nothing entered it in the bin - is priced at FREE SPEED, which is the worst possible estimate at exactly the moment the estimate matters. #154 names this and travelTimeGetter as the two unstated defaults that would otherwise sit inside the filter_modes paired difference.

#### `RUN.travel_time.analysed_modes`

Which modes contribute observed link travel times. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `travelTimeCalculator.analyzedModes`*

#### `RUN.travel_time.bin_size_s`

The travel-time calculator's aggregation bin. Adopted from the reference city's declaration; not a Mumbai observation.

***literature** · status **active** · DECISIONS.md §9.202 · MATSim `travelTimeCalculator.travelTimeBinSize` · sweep role **uncertainty***

> **Sweep basis.** MATSim's own default is 900 s. The level-crossing closures (#68) last 60-600 s (A.crossings.closure_duration_s), and the router only sees a closure that spans a travel-time bin - so the crossings activation needs <=300 s. Lowered to 300 at the batched family boundary (9.77), exactly as the 9.76 checklist recorded.

#### `RUN.travel_time.filter_modes`

Whether the travel-time calculator RESTRICTS itself to RUN.travel_time.analysed_modes. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `travelTimeCalculator.filterModes`*

#### `RUN.travel_time.getter`

How a link entry time inside a travel-time bin is turned into a travel time for the router. Adopted from the reference city's declaration; not a Mumbai observation.

***assumed** · status **active** · DECISIONS.md §9.202 · MATSim `travelTimeCalculator.travelTimeGetter` · sweep role **uncertainty***

> **Sweep basis.** adopted from the reference city: MATSim's own two alternatives. `average` returns one number for the whole RUN.travel_time.bin_size_s bin, so a departure at the start of a bin and one at its end are told the same travel time; `linearinterpolation` interpolates between adjacent bins. WHAT THE SWEEP ANSWERS: how much of the peak-shoulder behaviour in this model is a 300-second step function. It matters most where the gradient is steepest - the shoulders of the morning peak, which is where the departure-time mutator is doing its work.

#### `RUN.travel_time.separate_modes`

Whether travel times are accumulated per mode rather than once for the network. Adopted from the reference city's declaration; not a Mumbai observation.

***definition** · status **active** · DECISIONS.md §9.202 · MATSim `travelTimeCalculator.separateModes`*
