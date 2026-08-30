# Network, inputs and the data package — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has reached its gate.*

**Updated:** 30 August 2026 · **Record read through:** §9.131 · **Open family:** F20

## What is built

- **Extent.** Every harvest and clip extent is derived: the study area from the dissolved five-LGA boundary in `zones_LGA.gpkg` plus `A.osm.harvest_margin_m` (5000 m), the CBD building extent from the observed light rail stop set plus `A.osm.buildings_margin_m` (3500 m). No rectangle is typed anywhere (§9.35, #32 closed). Study area 4,086 km², 1,500 core SA1s, external tier at SA2 (§1).
- **OSM harvest.** Ten layers fetched over a tile grid no larger than `A.osm.harvest_tile_deg` (0.4), rotated across three Overpass mirrors, merged by element id and verified before any tile is deleted (§9.35). The 16 August re-harvest grew the extent 2.02x; core SA1s without a road node went 99 → 4, with no agents in them (§9.35, `STATUS.md`). `networks/osm_pre_issue32/` is the pre-repair reference copy.
- **Road and active layers.** 50,182 road edges / 11,434 km and 40,195 active edges / 7,920 km (`README.md`), every edge carrying a Copernicus GLO-30 gradient from a boundary-derived DEM tile set (§3.3). Gradient reaches link travel time as physics under `A.gradient.representation` = `link_speed` (§9.84). Speed is the TfNSW regulated zone where one matches within `A.road.speed_zone_match_m` (10 m), `service` excluded by class; class defaults are measured from the city's own tags — `A.road.lane_width_default_m` 3.5 m, trunk 60 km/h, motorway 110 km/h (§9.33, §9.34). One copy of every default, resolved from the registry; the network takes the declared speed (§9.34, §9.38).
- **Corridor.** Extent is geometric: trunk within `A.corridor.trunk_buffer_m` (60 m) of the tram's own GTFS shape, cross streets within `A.corridor.cross_buffer_m` (40 m), comparators within `A.corridor.parallel_buffer_m` (1500 m) — 714 edges in `data/processed/network/A1_corridor_road_edges.csv`, each attribute paired with a `*_source` (§3.4, §9.34). Turn restrictions are the observed OSM relations resolved to coordinates (§3.4). The pre-LR cross-section is `A.corridor.pre_lr_lanes_per_dir` = 1, source `literature`, sweep [1, 2], from OSM attic queries at 2016 and 2017 (§9.71 supersedes the assumed 2 of §3.4).
- **MATSim network and schedules.** One base network (181,892 links, `STATUS.md`) with the E1 patches re-applied per scenario by `osm:way:id`; 15 GTFS feeds (5 eras + 10 scenario variants) mapped in ONE pt2matsim build with 0 unmapped stops in every feed (§3.5, §11). Day-type and variant schedules are filtered from the mapped schedule, never remapped (§3.5). Explicit signals, tram priority, level crossings timed from the mapped rail timetable and charging-dwell offsets are all generated from that one build (§9.76, §9.77, §9.90).
- **Parking and land use.** Price is a density ramp over the city's own core-zone job distribution — `A.parking.price_aud_hr_max` 3.2 AUD/h at the p99, `A.parking.max_stay_min` 120, charged hours by day type, `A.parking.charged_modes` car only, home exempt — and it reaches the scoring (§9.31). 7,710 facilities, 4,861 with an observed capacity, `A.parking.capacity_default` by type for the rest (§6). Land use: 498 frontage segments, modelled retail floorspace, jobs from WPP SA2 disaggregated by a POI index (§7).
- **Scenarios.** S0–S6 (ten feeds) derive from `schedules/base2026.zip` by explicit transformation; S0/S2c/S4/S5 alignments are routed over observed geometry, with S4/S5 stops anchored on observed features (§3.4, §10). 30 run-input sets = 10 scenarios × WEEKDAY/SAT/SUN, assembled by `build_matsim_run_inputs.py`; the MATSim config is emitted from the registry, never templated (§9.38, §15).
- **Registry and checks.** 414 fields, `check_hardcoding.py --strict` at 0 and gating CI; every `assumed`/`literature`/`measured`/`derived` field carries a sweep, a `held_fixed` rule or a `derived_from` identity, and the three unobtained fields hold `value: null` so `get()` raises (§15). 501 files in `data/MANIFEST.csv`; `check_manifest.py` in CI, `check_package.py` local over city-owned expectations (#62), `check_doc_currency.py --strict` pinning every live-state figure in `README.md` and `STATUS.md` (§9.79).
- **Toolchain.** `.tools/toolchain.json` pins Temurin JDK 25.0.4+7, pt2matsim 26.6 (embedding MATSim 2027.0-2026w25, §9.73), Maven 3.9.9 and the signals run stack at 2027.0-2026w25 (201 jars, each hashed). SUMO left the toolchain with the descope (§9.74, §9.76, #72 closed); §3.6's SUMO row is history, and `networks/sumo/` is a leftover directory, not an input.

## What is observed, derived, and still unobtained

| Layer | Observed or measured | Derived | Assumed and swept | Unobtained, and how it is handled now |
|---|---|---|---|---|
| Road network | geometry, class, regulated speed, turn restrictions, gradient (§3, §9.34) | class defaults from the city's own tags (§9.33) | `A.road.capacity_default` by class ±20% (§3.2) | — |
| Corridor | trunk lanes and speed in OSM (§2.5); pre-LR lanes from OSM history (§9.71) | corridor extent from the tram shape (§3.4) | kerbside, lane width, capacity, turn lanes (§9.34); `A.corridor.extension_lane_take` 1 [0, 1] (§3.4) | a street-level survey; B3 must carry it as uncertainty (#27 closed as cannot-close) |
| Signals | 14 corridor sites, identities and install dates (§5, §9.24) | cycle and splits re-timed every cycle from measured degree of saturation under `A.signals.control_regime` = `scats_adaptive` (§9.88) | `A.signals.scats.*` and `A.signals.tsp.*` bands, informed by operated history at two non-modelled sites (§9.75) | **only the per-subsystem offset library** (§9.88); `A.signals.scats_phasing` stays `unobtained`; SCATS is an algorithm here, not a swept constant |
| Light rail | 270-place fleet, alignment, `A.lightrail.line_speed_kmh` 40 as a regulated ceiling (§9.18, §9.76) | crossing closures 110 and 204 a day from the rail timetable (§9.90) | `A.lightrail.dwell_fixed_s` 8 [5, 15] (§4.4) | measured charging dwell: `A.lightrail.dwell_charging_s` null, swept 10–35 s on `A.lightrail.dwell_sweep_grid`, concurrent with boarding, S2a is the 0 identity (§9.76, §15) |
| Transfers | EPV Table 2.7 penalties 3.8 bus–LR, 4.1 train–LR as an anchor (§9.71) | — | `C.transfer.beta_transfer_penalty_min` 8.0, swept 3–15 on `C.transfer.penalty_sweep_grid`, and proven to reach `utilityOfLineSwitch` (§9.32) | journey-linked Opal: every held Opal source is monthly, the estimate is undefined (§9.32) |
| Parking | 7,710 facilities, 4,861 capacities (§6) | price zone from the job-density percentiles (§9.31) | price, max stay, charged hours, occupancy profile (§6, §9.31) | meter transactions, occupancy (§13) |
| Land use | POI, buildings, jobs by SA2 (§7) | jobs to SA1 by POI index, floorspace from footprints (§7) | ground-floor coefficient 0.35, POI weights (§7) | pedestrian counts, floorspace, vacancy (§13) |
| PT supply | 4 real GTFS eras and the 2026 base (§11) | day-type calendars, scenario feeds (§10, §11) | S2b 75% delay removed, S3 BRT, S4/S5 sitings (§10) | pre-2014 timetable: era 1 is reconstructed from 2016 service (§11) |

## What is measured

- pt2matsim agrees with itself on stop-to-link assignment 100% and on route link sequences 81.9–82.3% between builds; hence one build per comparison and `stop_link_fingerprint` asserted exactly (§3.5).
- Corridor trunk: 87.5% of lanes and 97.5% of speeds observed in OSM (§2.5); with speed zones, 669 of 714 corridor edges and 25,109 of 43,112 network edges carry a regulated speed, and imputation on driven roads is 2.6% (§9.34). Still imputed on the corridor: kerbside 678, lane width 704, capacity 714 of 714 (§9.34).
- Speed-zone join: agreement 74.9% over 18,473 validated edges at 10 m; it collapses to 30% beyond 10 m, which set the radius (§9.34).
- Pre-LR corridor: 9 of 21 named segments carried a lanes tag in 2016–17 and every one read one lane per direction; the assumed 2 had doubled the counterfactual's capacity (§9.71).
- Circuity: walk 1.6902, bike 1.5231, road 1.3376 — two active factors, not one (§9.33). Walk speed 1.25 m/s is one number, not two (§9.33).
- Harvest defect closed: 87 core SA1s and 31,940 agents (5.2%) had been outside the network (§9.35).
- 0b: 136 assumed fields enumerated; SAT:SUN 1.1473 and a 1 h weekend shift measured (§9.61); seven source upgrades including `B.population.bike_available_rate` 0.493 (§9.78); the VoT set sits inside ±30% of EPV 2025 except education and the concession factor, recorded not moved (§9.71).
- Level crossings: 110 and 204 closures a day against an assumed 30 at both (§9.90). A transitRoute's day tag is not its service day: ferry 107 and tram 252 weekday departures (§9.113).
- 477 of 4,374 base-feed trips (10.9%) carry a short GTFS shape, identical in every scenario feed (§3.4).

## What is open

- **The package on disk is inconsistent** (§9.131): `demand/population/B1_synthetic_population.csv` was rebuilt with measured licence rates, WEEKDAY chains are absent, and the plans and 30 run-input sets are the F20 build on the old population. The next session's first build is the demand chain, then the manifest and `check_package.py` (`STATUS.md`).
- No gate compares a builder against the artefact it produced; a committed builder had stopped reproducing the committed demand (§9.116), and the local suite was failing on `main` while three documents said it passed (§9.117). Run the suite before believing the board.
- **#63** (0b backlog): the board says only the attended ABS TableBuilder extract for `B.external.interaction_rate` remains; the issue body still lists reclassification edits and held-data items — reconcile at the next grooming.
- **#62**: the input contract's remaining city-bound follow-ups are currency-bearing key names and census-family readers.
- **#82**: counts run −91.8% across 30 stations with 6 carrying no modelled traffic; whether the through tier's gates route over the count-station links is untested and run-gated.
- Not built: the event-demand overlay (§1); era-1 validation against a 2014 timetable (§11); LiDAR for the CBD, pedestrian counts, the floorspace audit (§13). Two ABS DataPack URLs 404 upstream and were never held (`STATUS.md`).

## Refused — do not re-raise

- Re-running pt2matsim per day type or variant, or comparing scenarios across builds (§3.5).
- Manual aerial correction of corridor lane counts: they are observed; the counterfactual is what cannot be seen (§2.5).
- Inventing SCATS offsets; migrating off MATSim; reinstating SUMO (§9.88, §9.73, §9.74).
- Deriving `A.lightrail.line_speed_kmh` from GTFS alone — unidentifiable without pinning the swept terms (§9.76).
- Reclassifying assumed fields to improve the count (§9.33); a typed rectangle or coordinate anywhere (§9.29, §9.31, §9.35).
- Storage capacity above flow capacity — MATSim rejects it (§15). A GTFS-Realtime collector (§9.23). Reading a service day from a route id (§9.113). Fitting the counts as a target (#82).

## History

- §9.131 — licence rate measured, package inconsistent
- §9.130 — rail boardings held to disclosed
- §9.117 — local suite failing on main
- §9.116 — builder stopped reproducing committed demand
- §9.113 — count departures, not route tags
- §9.90 — crossings timed from rail timetable
- §9.88 — SCATS becomes an implemented algorithm
- §9.84 — gradient reaches link speed physically
- §9.79 — documents drifted; currency check added
- §9.78 — seven 0b source upgrades landed
- §9.76 — SUMO out; signals run stack pinned
- §9.71 — pre-LR cross-section from OSM history
- §9.61 — 0b backlog enumerated, three measured
- §9.38 — config emitted from the registry
- §9.35 — harvest extent derived from boundary
