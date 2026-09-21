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

## What the 178 fields are made of

| Provenance | Fields | Meaning |
|---|---:|---|
| `observed` | 1 | read directly from a raw download |
| `assumed` | 75 | chosen without direct empirical support |
| `definition` | 102 | fixed by the formulation, not an empirical quantity |

| Status | Fields | Meaning |
|---|---:|---|
| `active` | 178 | usable point value |

### The 0 fields with no value

These carry `value: null` and the resolver refuses to return a point value for them. They are the project's honest edge: what it does not know, declared rather than guessed.

| Field | Sweep | Why it has no value |
|---|---|---|

### What the 75 sweeps are for

A sweep is one word for two things (#134): the sensitivity CURVE DECISIONS.md 8.1 says must be reported rather than a headline at a single value, and the honesty BRACKET DECISIONS.md 15 requires before an assumed value may validate. Every sweep carries a `sweep_role` saying which, and the resolver refuses one that does not. `python src/registry/sweep_ledger.py` prints the ledger with whether any overlay has ever set each field.

| Role | Sweeps | Meaning |
|---|---:|---|
| `uncertainty` | 75 | a declared bracket the resolver enforces; no run is scheduled over it, and the basis says whether its leverage is measured or unknown |

The `answer` sweeps - the runs the study owes after the gate:

| Field | Value | Sweep |
|---|---|---|

### The 0 fields held fixed

Not tunable. DECISIONS.md 8.5 holds the mode constants fixed because calibrating them would fit away the effect under test - proposal 9 names ASC absorption as the primary threat to validity.


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

*`cities/mumbai/registry/A_baseline_services.json` - 9 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.baseline_transit.commercial_speed_kmh` | `{"train": 35, "subway": 32, "ferry": 15}` | km/h | `assumed` | 8 - 60 |
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

*`cities/mumbai/registry/A_baseline_supply.json` - 36 fields*

First runnable baseline; provisional parameters are explicit and are not calibrated observations.

| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.network.freespeed_factor` | `1.0` | factor | `definition` | - |
| `A.network.keep_paths` | `false` | boolean | `definition` | - |
| `A.network.keep_tags_as_attributes` | `true` | boolean | `definition` | - |
| `A.network.keep_ways_with_public_transit` | `true` | boolean | `definition` | - |
| `A.network.max_link_length_m` | `500` | metres | `assumed` | 100 - 1000 |
| `A.network.parse_turn_restrictions` | `true` | boolean | `definition` | - |
| `A.network.path_access_overrides` | `{"keys": {"access": "all", "foot": "walk", "bicycle": "bike"}, "grant": ["yes", "designated", "permissive",...` | osm_access_vocabulary | `definition` | - |
| `A.network.path_lane_capacity_veh_h` | `10000` | travellers/h | `assumed` | 1000 - 20000 |
| `A.network.path_modes_by_class` | `{"bridleway": ["walk", "bike"], "corridor": ["walk"], "cycleway": ["bike", "walk"], "footway": ["walk"], "p...` | mode_names_by_osm_highway_class | `definition` | - |
| `A.network.railway_lane_capacity_veh_h` | `120` | vehicles/h | `assumed` | 30 - 240 |
| `A.network.railway_speed_default_kmh` | `{"rail": 60, "subway": 60, "light_rail": 40, "tram": 25, "monorail": 40}` | km/h | `assumed` | 15 - 100 |
| `A.network.routable_subnetworks` | `{"car": ["car"], "bus": ["bus", "car"], "rail": ["rail", "light_rail"], "walk": ["walk"], "bike": ["bike"]}` | mode_names_by_subnetwork | `definition` | - |
| `A.network.scale_max_speed` | `false` | boolean | `definition` | - |
| `A.network.way_default_oneway` | `{"motorway": true, "motorway_link": true}` | boolean_by_way_class | `definition` | - |
| `A.network.write_crs` | `true` | boolean | `definition` | - |
| `A.road.capacity_default` | `{"motorway": 1800, "motorway_link": 600, "trunk": 1800, "trunk_link": 600, "primary": 1200, "primary_link":...` | vehicles/h/lane | `assumed` | 300 - 2400 |
| `A.road.lanes_default` | `{"motorway": 2, "motorway_link": 1, "trunk": 2, "trunk_link": 1, "primary": 2, "primary_link": 1, "secondar...` | lanes_per_direction | `assumed` | 1 - 4 |
| `A.road.speed_default` | `{"motorway": 80, "motorway_link": 40, "trunk": 60, "trunk_link": 35, "primary": 50, "primary_link": 30, "se...` | km/h | `assumed` | 5 - 100 |
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
| `A.transit.walk_speed_ms` | `1.2` | m/s | `assumed` | 0.6 - 1.8 |
| `B.bike.speed_ms` | `4.0` | m/s | `assumed` | 2 - 7 |
| `RUN.machine.build_xmx` | `16g` | JVM_heap | `definition` | - |

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

## Provisional hired-vehicle supply

*`cities/mumbai/registry/A_hired_fleet.json` - 6 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `A.hired.active_fraction` | `0.5` | fraction_of_registered_stock | `assumed` | 0.25 - 0.75 |
| `A.hired.categories` | `{"taxi": ["7a", "7b"], "auto_rickshaw": ["8"]}` | published_category_codes | `definition` | - |
| `A.hired.office_labels` | `["Mumbai (C)", "Mumbai (W)", "Mumbai (E)", "Borivali", "Thane", "Kalyan", "Vashi N.mumbai", "Vasai", "Panve...` | published_office_labels | `definition` | - |
| `RUN.smoke.hiredFleet.maxWaitSeconds` | `900.0` | seconds | `assumed` | 300 - 1800 |
| `RUN.smoke.hiredFleet.representation` | `absent` | enum | `definition` | - |
| `RUN.smoke.hiredFleet.turnaroundSeconds` | `300.0` | seconds | `assumed` | 0 - 900 |

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

#### `RUN.smoke.hiredFleet.maxWaitSeconds`

Provisional patience limit; a timed-out request aborts and receives native stuck scoring.

***assumed** · status **active** · DECISIONS.md §9.199 · MATSim `hiredFleet.maxWaitSeconds` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad development proxy; no fleet calibration or scaling-equivalence claim.

#### `RUN.smoke.hiredFleet.representation`

Bounded pooled availability is opt-in; original unlimited vehicle proxies remain the control.

***definition** · status **active** · DECISIONS.md §9.199 · MATSim `hiredFleet.representation`*

#### `RUN.smoke.hiredFleet.turnaroundSeconds`

Provisional unavailable turnaround after actual arrival. No spatial dispatch or empty road movements.

***assumed** · status **active** · DECISIONS.md §9.199 · MATSim `hiredFleet.turnaroundSeconds` · sweep role **uncertainty***

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

## Bounded behavioural smoke

*`cities/mumbai/registry/RUN_baseline_smoke.json` - 80 fields*



| Field | Value | Units | Provenance | Sweep |
|---|---|---|---|---|
| `C.smoke.activity_duration` | `{"home": 43200, "work": 28800, "education": 21600, "other": 3600, "freight_start": 86400, "freight_end": 86...` | seconds | `assumed` | plus/minus 50% |
| `C.smoke.crowding_price` | `6.0` | utility_per_hour | `assumed` | plus/minus 50% |
| `C.smoke.crowding_seated` | `1.1` | ratio | `assumed` | plus/minus 50% |
| `C.smoke.crowding_standing` | `1.8` | ratio | `assumed` | plus/minus 50% |
| `C.smoke.distance_money` | `{"car": -0.007, "ride": -0.003, "walk": 0.0, "bike": 0.0, "motorbike": -0.0025, "taxi": -0.018, "auto_ricks...` | INR/m | `assumed` | plus/minus 50% |
| `C.smoke.headway_cap` | `120.0` | minutes | `assumed` | plus/minus 50% |
| `C.smoke.headway_price` | `0.05` | utility_per_minute | `assumed` | plus/minus 50% |
| `C.smoke.mode_constant` | `{"car": 0.0, "ride": 0.0, "walk": 0.0, "bike": 0.0, "motorbike": 0.0, "taxi": 0.0, "auto_rickshaw": 0.0, "p...` | utils/trip | `definition` | - |
| `C.smoke.money` | `0.05` | utils/INR | `assumed` | plus/minus 50% |
| `C.smoke.performing` | `6.0` | utils/h | `assumed` | plus/minus 50% |
| `C.smoke.reliability_price` | `0.13` | utility_per_minute | `assumed` | plus/minus 50% |
| `C.smoke.transfer` | `-0.5` | utility_per_transfer | `assumed` | plus/minus 50% |
| `C.smoke.travel` | `{"car": -6.0, "ride": -6.0, "walk": -6.0, "bike": -6.0, "motorbike": -6.0, "taxi": -6.0, "auto_rickshaw": -...` | utils/h | `assumed` | plus/minus 50% |
| `C.smoke.waiting_pt` | `-12.0` | utility_per_hour | `assumed` | plus/minus 50% |
| `RUN.replanning.strategy_subpopulations` | `{"SubtourModeChoice": ["resident"]}` | strategy_membership | `definition` | - |
| `RUN.replanning.subpopulations` | `["resident", "freight"]` | subpopulation_names | `definition` | - |
| `RUN.smoke.activityLinks.assignment` | `mode_specific_access` | enum | `definition` | - |
| `RUN.smoke.boardingFare.routeChoice` | `true` | boolean | `definition` | - |
| `RUN.smoke.clear_default_teleported_params` | `true` | boolean | `definition` | - |
| `RUN.smoke.controler.createGraphs` | `false` | boolean | `definition` | - |
| `RUN.smoke.controler.firstIteration` | `0` | iterations | `definition` | - |
| `RUN.smoke.controler.lastIteration` | `8` | iterations | `definition` | - |
| `RUN.smoke.controler.overwriteFiles` | `failIfDirectoryExists` | enum | `definition` | - |
| `RUN.smoke.controler.writeEventsInterval` | `1` | iterations | `definition` | - |
| `RUN.smoke.controler.writePlansInterval` | `1` | iterations | `definition` | - |
| `RUN.smoke.controler.writeTripsInterval` | `1` | iterations | `definition` | - |
| `RUN.smoke.crowding` | `in_vehicle_time` | enum | `definition` | - |
| `RUN.smoke.dedicated_transit_headway_s` | `{"rail": 90, "light_rail": 90, "subway": 90, "ferry": 900}` | seconds_per_vehicle | `assumed` | plus/minus 50% |
| `RUN.smoke.global.numberOfThreads` | `2` | threads | `definition` | - |
| `RUN.smoke.global.randomSeed` | `20260810` | integer_seed | `definition` | - |
| `RUN.smoke.incomeScoring.excludeSubpopulations` | `freight` | subpopulation_names | `definition` | - |
| `RUN.smoke.incomeScoring.incomeExponent` | `1.0` | dimensionless | `definition` | - |
| `RUN.smoke.incomeScoring.representation` | `person_marginal_utility_of_money` | enum | `definition` | - |
| `RUN.smoke.inputs` | `{"network": "networks/matsim/schedules/baseline_regional/network.xml.gz", "schedule": "networks/matsim/sche...` | city_relative_paths | `definition` | - |
| `RUN.smoke.modeAvailability.bikeFeasibleKm` | `0.0` | kilometres | `definition` | - |
| `RUN.smoke.modeAvailability.bikeMinAge` | `6` | years | `definition` | - |
| `RUN.smoke.modeAvailability.taxiMinAge` | `18` | years | `definition` | - |
| `RUN.smoke.modeAvailability.walkFeasibleKm` | `0.0` | kilometres | `definition` | - |
| `RUN.smoke.network_mode_sources` | `{"truck": "car", "freight_rail": "rail"}` | mode_mapping | `definition` | - |
| `RUN.smoke.ptDirectWalk.basis` | `network` | enum | `definition` | - |
| `RUN.smoke.qsim.endTime` | `36:00:00` | time_hh:mm:ss | `definition` | - |
| `RUN.smoke.qsim.flowCapacityFactor` | `1.0` | dimensionless | `definition` | - |
| `RUN.smoke.qsim.linkDynamics` | `PassingQ` | enum | `definition` | - |
| `RUN.smoke.qsim.mainMode` | `["car", "ride", "walk", "bike", "motorbike", "taxi", "auto_rickshaw", "truck", "freight_rail"]` | mode_names | `definition` | - |
| `RUN.smoke.qsim.numberOfThreads` | `2` | threads | `definition` | - |
| `RUN.smoke.qsim.removeStuckVehicles` | `true` | boolean | `definition` | - |
| `RUN.smoke.qsim.startTime` | `00:00:00` | time_hh:mm:ss | `definition` | - |
| `RUN.smoke.qsim.storageCapacityFactor` | `1.0` | dimensionless | `definition` | - |
| `RUN.smoke.qsim.stuckTime` | `3600.0` | seconds | `definition` | - |
| `RUN.smoke.qsim.trafficDynamics` | `queue` | enum | `definition` | - |
| `RUN.smoke.qsim.vehicleBehavior` | `teleport` | enum | `definition` | - |
| `RUN.smoke.qsim.vehiclesSource` | `modeVehicleTypesFromVehiclesData` | enum | `definition` | - |
| `RUN.smoke.replanning.fractionOfIterationsToDisableInnovation` | `0.8` | iterations | `definition` | - |
| `RUN.smoke.replanning.maxAgentPlanMemorySize` | `5` | plans_per_person | `definition` | - |
| `RUN.smoke.road_capacity_factors` | `{"motorway": 1.0, "motorway_link": 1.0, "trunk": 1.0, "trunk_link": 1.0, "primary": 1.0, "primary_link": 1....` | dimensionless_flow_capacity_factor | `assumed` | 0.5 - 3 |
| `RUN.smoke.road_mode_exclusions` | `{"car": [], "ride": [], "walk": ["motorway", "motorway_link"], "bike": ["motorway", "motorway_link"], "moto...` | highway_classes_by_mode | `definition` | - |
| `RUN.smoke.routing.accessEgressType` | `accessEgressModeToLink` | enum | `definition` | - |
| `RUN.smoke.routing.networkModes` | `["car", "ride", "walk", "bike", "motorbike", "taxi", "auto_rickshaw", "truck", "freight_rail"]` | mode_names | `definition` | - |
| `RUN.smoke.scats.regime` | `fixed_time` | enum | `definition` | - |
| `RUN.smoke.scoring.brainExpBeta` | `1.0` | dimensionless | `definition` | - |
| `RUN.smoke.scoring.learningRate` | `1.0` | dimensionless | `definition` | - |
| `RUN.smoke.service_quality` | `headway_and_reliability` | enum | `definition` | - |
| `RUN.smoke.strategy_weights` | `{"ChangeExpBeta": 0.7, "SubtourModeChoice": 0.3}` | probability | `definition` | - |
| `RUN.smoke.stub_walk_distance_factor` | `1.3` | factor | `assumed` | plus/minus 50% |
| `RUN.smoke.stub_walk_speed_ms` | `1.2` | m/s | `assumed` | plus/minus 50% |
| `RUN.smoke.subtourModeChoice.chainBasedModes` | `["car", "bike", "motorbike"]` | mode_names | `definition` | - |
| `RUN.smoke.subtourModeChoice.considerCarAvailability` | `true` | boolean | `definition` | - |
| `RUN.smoke.subtourModeChoice.modes` | `["car", "ride", "walk", "bike", "motorbike", "taxi", "auto_rickshaw", "pt"]` | mode_names | `definition` | - |
| `RUN.smoke.subtourModeChoice.probaForRandomSingleTripMode` | `0.5` | dimensionless | `definition` | - |
| `RUN.smoke.taxiFleet.representation` | `absent` | enum | `definition` | - |
| `RUN.smoke.telemetry.liveIntervalS` | `3600.0` | seconds | `definition` | - |
| `RUN.smoke.transit.transitModes` | `["pt"]` | mode_names | `definition` | - |
| `RUN.smoke.transit.useTransit` | `true` | boolean | `definition` | - |
| `RUN.smoke.transit_mode_aliases` | `{"light_rail": "subway"}` | mode_mapping | `definition` | - |
| `RUN.smoke.transit_timing` | `{"speed_ms": {"bus": 8.333333333333334, "rail": 16.666666666666668, "subway": 16.666666666666668, "ferry": ...` | metres_per_second_and_seconds | `assumed` | plus/minus 50% |
| `RUN.smoke.vehicle_length_m` | `{"car": 5.0, "ride": 5.0, "walk": 0.5, "bike": 2.0, "motorbike": 2.0, "taxi": 5.0, "auto_rickshaw": 3.0, "t...` | metres | `assumed` | plus/minus 50% |
| `RUN.smoke.vehicle_pcu` | `{"car": 1.0, "ride": 1.0, "walk": 0.1, "bike": 0.2, "motorbike": 0.4, "taxi": 1.0, "auto_rickshaw": 0.7, "t...` | passenger_car_units | `assumed` | plus/minus 50% |
| `RUN.smoke.vehicle_speed_ms` | `{"car": 30.0, "ride": 30.0, "walk": 1.2, "bike": 4.0, "motorbike": 25.0, "taxi": 30.0, "auto_rickshaw": 15....` | m/s | `assumed` | plus/minus 50% |
| `RUN.smoke.wall_ceiling_s` | `900` | seconds | `definition` | - |
| `RUN.smoke.xmx` | `16g` | JVM_heap | `definition` | - |

#### `C.smoke.activity_duration`

Provisional typical activity duration.

***assumed** · status **active** · DECISIONS.md §9.193 · MATSim `scoring.activityParams[*].typicalDuration` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.smoke.crowding_price`

Provisional price of additional perceived in-vehicle time due to crowding.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `ptCrowding.penaltyUtilsPerHour` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.crowding_seated`

Provisional full-load seated time multiplier.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `ptCrowding.seatedMultiplier` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.crowding_standing`

Provisional standing time multiplier.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `ptCrowding.standingMultiplier` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.distance_money`

Provisional distance-based user costs, not observed fare schedules. PT distance money is zero because the boarding fare handler charges each completed ride; double pricing is refused at startup.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.modeParams[*].monetaryDistanceRate` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.smoke.headway_cap`

Provisional cap for sparse/single-departure service headway scoring.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `serviceQuality.headwayCapMin` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.headway_price`

Provisional schedule-delay price: half an in-vehicle minute per headway minute.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `serviceQuality.headwayUtilsPerMin` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.mode_constant`

Zero mode constants: no target shares encoded.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.modeParams[*].constant`*

#### `C.smoke.money`

Provisional mean money sensitivity, varied by personal budget.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.marginalUtilityOfMoney` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.smoke.performing`

Provisional activity utility.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.performing` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.smoke.reliability_price`

Provisional price of delay standard deviation measured from the preceding iteration.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `serviceQuality.reliabilityUtilsPerMin` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.transfer`

Provisional inconvenience per PT transfer, separate from experienced wait and walk.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.utilityOfLineSwitch` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `C.smoke.travel`

Provisional travel time disutility.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.modeParams[*].marginalUtilityOfTraveling_util_hr` · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `C.smoke.waiting_pt`

Provisional waiting penalty greater than the in-vehicle travel penalty.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.waitingPt` · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `RUN.replanning.strategy_subpopulations`

Apply baseline choice strategies to residents.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.replanning.subpopulations`

Smoke traveller population.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.smoke.activityLinks.assignment`

Each mode uses its own permitted network and retains MATSim access/egress connectors, including boarding links off the walk network.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `activityLinks.assignment`*

#### `RUN.smoke.boardingFare.routeChoice`

Price each candidate transit boarding with the same city fare table and person-specific money utility as executed scoring, before RAPTOR prunes paths. This enables a mechanism, not a calibrated preference.

***definition** · status **active** · DECISIONS.md §9.192 · MATSim `boardingFare.routeChoice`*

#### `RUN.smoke.clear_default_teleported_params`

Explicit routing helper configuration for the provisional network-mode smoke; main walk and bike use network routing.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `routing.clearDefaultTeleportedModeParams`*

#### `RUN.smoke.controler.createGraphs`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `controler.createGraphs`*

#### `RUN.smoke.controler.firstIteration`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `controler.firstIteration`*

#### `RUN.smoke.controler.lastIteration`

Bounded nine-iteration learning check of the explicit small population; no convergence or citywide scaling claim. The existing automatic JVM ceiling remains in force.

***definition** · status **active** · DECISIONS.md §9.193 · MATSim `controler.lastIteration`*

#### `RUN.smoke.controler.overwriteFiles`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `controler.overwriteFiles`*

#### `RUN.smoke.controler.writeEventsInterval`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `controler.writeEventsInterval`*

#### `RUN.smoke.controler.writePlansInterval`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `controler.writePlansInterval`*

#### `RUN.smoke.controler.writeTripsInterval`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `controler.writeTripsInterval`*

#### `RUN.smoke.crowding`

Enable the existing behavioural mechanism in the broad provisional baseline.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `ptCrowding.representation`*

#### `RUN.smoke.dedicated_transit_headway_s`

Provisional dedicated-link service envelope. Flow capacity derives as maximum mapped vehicle PCU times 3600/headway, preserving any greater mapped capacity. This avoids interpreting a train headway as car-equivalent flow and is not a validated signalling capacity.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Dedicated-mode headway sensitivity; replace with observed sectional signalling and vessel constraints.

#### `RUN.smoke.global.numberOfThreads`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `global.numberOfThreads`*

#### `RUN.smoke.global.randomSeed`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `global.randomSeed`*

#### `RUN.smoke.incomeScoring.excludeSubpopulations`

Background goods movements are exogenous volumes, not passenger budgets.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `incomeScoring.excludeSubpopulations`*

#### `RUN.smoke.incomeScoring.incomeExponent`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `incomeScoring.incomeExponent`*

#### `RUN.smoke.incomeScoring.representation`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `incomeScoring.representation`*

#### `RUN.smoke.inputs`

Prepared broad regional baseline including acquired NMMT departures and derived MBMT service supply.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.smoke.modeAvailability.bikeFeasibleKm`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `modeAvailability.bikeFeasibleKm`*

#### `RUN.smoke.modeAvailability.bikeMinAge`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `modeAvailability.bikeMinAge`*

#### `RUN.smoke.modeAvailability.taxiMinAge`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `modeAvailability.taxiMinAge`*

#### `RUN.smoke.modeAvailability.walkFeasibleKm`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `modeAvailability.walkFeasibleKm`*

#### `RUN.smoke.network_mode_sources`

Provisional goods modes share their source network, with connected components audited. Detailed HGV and freight operating restrictions remain incomplete.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.smoke.ptDirectWalk.basis`

Compare transit with network walking, not a direct geographical chord.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `ptDirectWalk.basis`*

#### `RUN.smoke.qsim.endTime`

Observe overnight completion after the all-day departure window. The freight prototype measured nearly ten-hour road movements, which a 30-hour horizon censored for late departures. This is an observation horizon, not a speed or demand adjustment.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.endTime`*

#### `RUN.smoke.qsim.flowCapacityFactor`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.flowCapacityFactor`*

#### `RUN.smoke.qsim.linkDynamics`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.linkDynamics`*

#### `RUN.smoke.qsim.mainMode`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.mainMode`*

#### `RUN.smoke.qsim.numberOfThreads`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.numberOfThreads`*

#### `RUN.smoke.qsim.removeStuckVehicles`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.removeStuckVehicles`*

#### `RUN.smoke.qsim.startTime`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.startTime`*

#### `RUN.smoke.qsim.storageCapacityFactor`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.storageCapacityFactor`*

#### `RUN.smoke.qsim.stuckTime`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.stuckTime`*

#### `RUN.smoke.qsim.trafficDynamics`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.trafficDynamics`*

#### `RUN.smoke.qsim.vehicleBehavior`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.vehicleBehavior`*

#### `RUN.smoke.qsim.vehiclesSource`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `qsim.vehiclesSource`*

#### `RUN.smoke.replanning.fractionOfIterationsToDisableInnovation`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `replanning.fractionOfIterationsToDisableInnovation`*

#### `RUN.smoke.replanning.maxAgentPlanMemorySize`

Native plan-memory limit; must retain supplied alternatives while exploration adds new plans.

***definition** · status **active** · DECISIONS.md §9.197 · MATSim `replanning.maxAgentPlanMemorySize`*

#### `RUN.smoke.road_capacity_factors`

Declared class sensitivity factors on the already mapped network. Identity preserves source capacities; this is not population sampling or evidence of correct road capacity. Geometry, lanes, speed and service departures are retained.

***assumed** · status **active** · DECISIONS.md §9.196 · sweep role **uncertainty***

> **Sweep basis.** Provisional flow-capacity sensitivity envelope, not fitted or observed Mumbai capacities.

#### `RUN.smoke.road_mode_exclusions`

Coarse class-based availability pending refined corridor access rules.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.smoke.routing.accessEgressType`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `routing.accessEgressType`*

#### `RUN.smoke.routing.networkModes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `routing.networkModes`*

#### `RUN.smoke.scats.regime`

Adaptive signalling disabled for the coarse smoke; this base controller has no detailed signal systems.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `scats.regime`*

#### `RUN.smoke.scoring.brainExpBeta`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.brainExpBeta`*

#### `RUN.smoke.scoring.learningRate`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `scoring.learningRate`*

#### `RUN.smoke.service_quality`

Enable the existing behavioural mechanism in the broad provisional baseline.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `serviceQuality.representation`*

#### `RUN.smoke.strategy_weights`

Score-based selection and mode exploration.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `replanning.strategysettings[*].weight`*

#### `RUN.smoke.stub_walk_distance_factor`

Explicit routing helper configuration for the provisional network-mode smoke; main walk and bike use network routing.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `routing.teleportedModeParameters[non_network_walk].beelineDistanceFactor` · sweep role **uncertainty***

> **Sweep basis.** Provisional access stub sensitivity.

#### `RUN.smoke.stub_walk_speed_ms`

Explicit routing helper configuration for the provisional network-mode smoke; main walk and bike use network routing.

***assumed** · status **active** · DECISIONS.md §9.187 · MATSim `routing.teleportedModeParameters[non_network_walk].teleportedModeSpeed` · sweep role **uncertainty***

> **Sweep basis.** Provisional access stub sensitivity.

#### `RUN.smoke.subtourModeChoice.chainBasedModes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `subtourModeChoice.chainBasedModes`*

#### `RUN.smoke.subtourModeChoice.considerCarAvailability`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `subtourModeChoice.considerCarAvailability`*

#### `RUN.smoke.subtourModeChoice.modes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `subtourModeChoice.modes`*

#### `RUN.smoke.subtourModeChoice.probaForRandomSingleTripMode`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `subtourModeChoice.probaForRandomSingleTripMode`*

#### `RUN.smoke.taxiFleet.representation`

Taxi trips use vehicle proxies before finite-fleet dispatch is introduced.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `taxiFleet.representation`*

#### `RUN.smoke.telemetry.liveIntervalS`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `telemetry.liveIntervalS`*

#### `RUN.smoke.transit.transitModes`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `transit.transitModes`*

#### `RUN.smoke.transit.useTransit`

Explicit setting for bounded provisional smoke only; full capacities serve the small explicit population without a full-city expansion.

***definition** · status **active** · DECISIONS.md §9.187 · MATSim `transit.useTransit`*

#### `RUN.smoke.transit_mode_aliases`

Mapped metro track permission uses light_rail; mapped metro vehicle profiles use subway.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.smoke.transit_timing`

Provisional moving-speed caps and intermediate-stop dwell derive physically feasible timetable offsets from the mapped path. Later source times are retained; no observed timetable is overwritten.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional broad behavioural baseline; validate with observed choices before calibration.

#### `RUN.smoke.vehicle_length_m`

Provisional vehicle lengths.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `RUN.smoke.vehicle_pcu`

Provisional network occupancy; ride uses an independent vehicle proxy in this smoke.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `RUN.smoke.vehicle_speed_ms`

Provisional per-mode movement caps.

***assumed** · status **active** · DECISIONS.md §9.187 · sweep role **uncertainty***

> **Sweep basis.** Provisional behavioural smoke coefficient; not calibrated to ridership.

#### `RUN.smoke.wall_ceiling_s`

Automatic short smoke ceiling; this path refuses multi-hour budgets.

***definition** · status **active** · DECISIONS.md §9.187*

#### `RUN.smoke.xmx`

Smoke heap ceiling.

***definition** · status **active** · DECISIONS.md §9.187*
