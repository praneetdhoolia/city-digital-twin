# Network, inputs and the data package — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 22 September 2026 (fifty-ninth session) · **Record read through:** §9.208 · **Written against family:** `F35`

## What is built

- **The contract says who reads a field** (§9.202): `required_fields.json` carries `required_by` — `run` (220), builders (239), `reference_city` (112) — derived from `check_hardcoding.key_uses`; Newcastle's 571 stay required of Newcastle (PASS 41).
- **Mumbai's transit vehicles carry evidenced capacities** (§9.206): `explicit_vehicle`; `build_transit_fleet.py` gives every mapped vehicle a profile — 12-car EMU 1,168 + 3,816, Line 1 200 + 1,300, BEML 239 + 1,561, Line 3 399 + 2,601, Navi Mumbai 150 + 950, launches 80 and 100, bus 36 + 30 (standing assumed, swept) — not the mapper's defaults every earlier case ran on.
- **Mumbai's feed holds the Maritime Board's seven commuter crossings** (§9.207, #245): `A.baseline_transit.directory_crossings` names each route's two OSM terminals and fleet profile; both directions run as `BASE_MMB_<route>_<direction>` on the water line between them in the directory's sailing window; seven `A.transit.ferry_*_capacity_seated` fields carry the printed capacities (60–1,635, swept). One mapping: **18,116 stops, 1,865 routes, 0 unmapped**; **115,100 vehicles, 17 profiles**; `20260922T031226_2it_0.1pct` ran the 430 crossing departures; four crossings stay out (no named terminal).
- **Metro Lines 2A and 7 run in their published windows** (§9.208): `A.baseline_transit.line_windows_s` (`observed`, MMMOCL's archived timetable) keys a window by OSM relation; the four patterns fall 552 → 500 departures. RDSO's coach loads at 16 standing/m² raise `A.transit.rail_capacity_total`'s sweep top to 6,072; the value stands.
- **The pass-through merge is measured and not applied** (§9.207, D15): `src/build/merge_pass_through_nodes.py` merges 37,122 of 377,443 nodes (33,923 more held by the 500 m cap) and moves the median link 62.7 → 69.0 m at 101,306 km unchanged; the user keeps the network as converted. Nothing wires it into a build.
- **The heap rule reads the live set; plan memory is 5** (§9.206): §9.205's 140 KB an agent came from pre-collection peaks that track the heap given; live after a full collection is 7.4 GiB empty and ~19 KB a plan. Rule 7.4 + 2,400 × fraction GiB (1 % 31, 5 % 127, 10 % 247).
- **The second city runs citywide plans through the harness against derived targets** (§9.201–§9.205, D13): the notified MMR core (2,538 leaves), 27.06 M persons for 2026, plans at a 0.05 build fraction (1.35 M), thirteen targets; a 0.1 % case is a check, not a reading (D14). See [`cities/mumbai/docs/README.md`](../../cities/mumbai/docs/README.md).
- **A provenance record is the package's own metadata** (§9.203): `build_manifest.record_for` no longer lets a `provenance_*.json` inherit a neighbour's source, licence and date — **724 CC-BY / 220 ODbL / 15 bespoke**; `normalise_eol.py` walks `data/raw/**/provenance*.json`.
- **The 30 run-input sets are re-assembled at 250 iterations** (§9.169): `RUN.controler.last_iteration` = 250, cutoff at 200 plus a 50-iteration tail; only `lastIteration` changed, pt2matsim NOT re-run.
- **A reading is taken through the run's own schedule** (§9.169): `extract_metrics.schedule_path` opens the run's `output_transitSchedule.xml.gz` first.
- **The network is rebuilt with its footpaths and every feed re-mapped once on it** (§9.167, #183): **181,892 → 368,230 links, 84,242 → 153,237 nodes**; remap drift stop-link 100 %, route sequences 82.3 % (§3.5); signals, crossings, dwells, run inputs, counts map and targets re-derived. Family **F34**.
- **A rebuild costs 4 minutes** (§9.167); the heap floor rose 9.6 → 15.6 GiB with the footpath network.
- **MATSim defaults**: `config/schema/matsim_defaults_accepted.json` holds **29** accepted, none deciding the transport system; undeclared **0** (§9.163, §9.164, #155).
- **Three declared fields reach the config off** — `B.mode.walk_feasible_km`, `B.mode.bike_feasible_km`, `C.crowding.seated_multiplier` — declaring `inert_at` (§9.163); the GitHub Actions are pinned to SHAs.
- **Extent** derived, never typed (§9.35, #32): the five-LGA boundary plus `A.osm.harvest_margin_m` (5000 m); 4,086 km², 1,500 core SA1s (§1).
- **OSM harvest**: ten layers over tiles ≤ `A.osm.harvest_tile_deg` (0.4), merged by element id (§9.35); `data/raw/provenance_osm.json` (§9.141, #118).
- **Road and active layers**: 50,182 road edges / 11,434 km, 40,195 active / 7,920 km (`README.md`), GLO-30 gradient under `A.gradient.representation` = `link_speed` (§3.3, §9.84); TfNSW speed zones within 10 m; class defaults from the city's own tags (§9.33, §9.34).
- **Corridor**: trunk within `A.corridor.trunk_buffer_m` (60 m) of the tram shape, cross streets 40 m, comparators 1500 m — 714 edges in `A1_corridor_road_edges.csv` (§3.4, §9.34); `A.corridor.pre_lr_lanes_per_dir` = 1, sweep [1, 2], from OSM attic 2016–17 (§9.71).
- **MATSim network and schedules**: one base network (368,230 links, §9.167), E1 patches per scenario by `osm:way:id`; 15 GTFS feeds mapped in ONE pt2matsim build, 0 unmapped stops; day-type and variant schedules filtered, never remapped (§3.5, §11, §9.76, §9.90).
- **Parking and land use**: `A.parking.price_hr_max` 3.2 AUD/h at the p99 of the job-density ramp, max stay 120 min (§9.31); 7,710 facilities, 4,861 observed capacities (§6); 498 frontage segments, jobs by POI index (§7).
- **Scenarios**: S0–S6 from `schedules/base2026.zip` by explicit transformation (§3.4, §10); 30 run-input sets by `build_matsim_run_inputs.py`, the config emitted from the registry (§9.38).
- **Registry**: **574 fields** (`cities/newcastle/docs/reference/CONFIG_REFERENCE.md`; §9.167, §9.179, #198); `check_hardcoding.py --strict` at 0; non-observed fields carry a sweep, `held_fixed` or `derived_from`; three unobtained fields `value: null` (§15). A `<city>` register entry is judged against the reference city's file where the active city lacks it (§9.207): Mumbai's ledger reads 225, none a stale excuse.
- **Manifest**: 959 files in `data/MANIFEST.csv`, hashed and licensed — **724 CC-BY 4.0, 220 ODbL 1.0 and 15 bespoke** (§9.167) — from declared sources and `derived_licences` globs (§9.141, #117); the resolver refuses a bad `derived_from` or an out-of-sweep value (#124); `check_manifest.py` in CI (§9.79).
- **The input contract is city-free**: HTS, counts and census read through `reader_shapes.py` against `config/schema/reader_shapes.json`, no ABS column named (§9.140, #62).
- **Two assumptions measured** (§9.140, #63): `E.s0.heavy_rail_detour_factor` 1.037 (1.0–1.1); `B.external.interaction_rate` 0.0900, derived.
- **Producers**: `tests/check_package.py` asserts every processed row's producer names it and refuses a builder no longer reproducing the committed demand (§9.141, #115, #116, #119, #120).
- **Toolchain**: `.tools/toolchain.json` pins Temurin JDK 25.0.4+7, pt2matsim 26.6 (MATSim 2027.0-2026w25, §9.73), Maven 3.9.9, the signals stack; SUMO descoped (§9.74).

## What is observed, derived, and still unobtained

| Layer | Observed or measured | Derived | Assumed and swept | Unobtained |
|---|---|---|---|---|
| Road network | geometry, class, regulated speed, turn restrictions, gradient (§3, §9.34) | class defaults from the city's tags (§9.33) | `A.road.capacity_default` ±20% (§3.2) | — |
| Corridor | trunk lanes and speed in OSM (§2.5); pre-LR lanes from OSM history (§9.71) | extent from the tram shape (§3.4) | kerbside, lane width, capacity, turn lanes (§9.34); `A.corridor.extension_lane_take` 1 [0, 1] | a street-level survey (#27) |
| Signals | 14 corridor sites (§5, §9.24) | splits re-timed from measured saturation, `A.signals.control_regime` = `scats_adaptive` (§9.88) | `A.signals.scats.*`, `A.signals.tsp.*` bands (§9.75) | the offset library (§9.88); `A.signals.scats_phasing` |
| Light rail | 270-place fleet, alignment, `A.lightrail.line_speed_kmh` 40 ceiling (§9.18, §9.76) | crossing closures from the timetable (§9.90) | `A.lightrail.dwell_fixed_s` 8 [5, 15] (§4.4) | charging dwell: `A.lightrail.dwell_charging_s` null, swept 10–35 s (§9.76, §15) |
| Transfers | EPV Table 2.7 penalties 3.8 bus–LR, 4.1 train–LR (§9.71) | — | `C.transfer.beta_transfer_penalty_min` 8.0, swept 3–15 (§9.32) | journey-linked Opal (§9.32) |
| Parking | 7,710 facilities, 4,861 capacities (§6) | price zone from job density (§9.31) | price, max stay, hours, occupancy (§6, §9.31) | meter transactions, occupancy (§13) |
| Land use | POI, buildings, jobs by SA2 (§7) | jobs to SA1 by POI index, floorspace (§7) | ground-floor coefficient 0.35, POI weights (§7) | pedestrian counts, floorspace, vacancy (§13) |
| PT supply | 4 real GTFS eras and the 2026 base (§11) | day-type calendars, scenario feeds (§10, §11) | S2b 75% delay removed, S3 BRT, S4/S5 sitings (§10) | pre-2014 timetable (§11) |

- **Not one MATSim default decides this model unreviewed** (§9.164, #155): nine are registry fields at the framework's value; twelve accepted.
- **`RUN.routing.access_egress_consistency_check` is a declared field, three settings swept** (§9.164), since its premise (`access_egress_type` = `none`) left the accepted ledger.

## What is measured

- **The count-station map is regenerated with the network** (§9.163, #82 closed): 197 rows, 0 unresolved; `20260909T015217_300it_25pct` read counts at mean +16.30 %, median −1.1 %.
- **The `networks/matsim/*` ODbL glob is narrowed on content** (§9.159, #165): 110 of 111 rows confirmed ODbL.
- **The 15 `transitVehicles.xml.gz` are CC-BY 4.0 on internal evidence** (§9.159): `check_manifest.py` read **512 rows agree, 0 undetermined**.
- **Four typed network fallbacks are declared, three never fired** (§9.151, #148): only `A.active.footway_width_unknown_class_m` fires, on **830 of 40,195 active edges**.
- **A derived file's provenance is resolved from its lineage** (§9.151, §9.158, #149): `retrieved` is the latest ancestor date, never a build time.
- Corridor trunk: 87.5% of lanes and 97.5% of speeds observed (§2.5); kerbside, lane width and capacity of the 714 edges still imputed; speed-zone join 74.9% at 10 m (§9.34). Pre-LR: 9 of 21 segments tagged, one lane per direction (§9.71).
- Circuity walk 1.6938, bike 1.5570, road 1.3276 (§9.142); walk speed 1.25 m/s (§9.33); SAT:SUN 1.1473 (§9.61); bike availability 0.493 (§9.78).
- Crossings 110 and 204 a day against an assumed 30 (§9.90); ferry 107, tram 252 weekday departures (§9.113).
- **Lineage is resolved per output and the licence boundary is checked** (§9.156, §9.158, #159): `OUTPUT_INPUTS` read statically; `share_alike_ancestor` undetermined **0**.
- **The demand DOES carry OSM geometry** (§9.158): 3,000 of 3,000 sampled `dest_placement=poi` destinations within 5 m of an OSM POI or building — the demand rows are ODbL.

## What is open

- **The 25 % heap is measured on the footpath network; the slope is NOT re-declared** (§9.169): arm 0's `gc.log` peaks at 26.2 GiB; the rule (37.4 GiB) holds 11 GiB over it.
- **Every vehicle has been setting the car router's link travel times** (§9.154, #154): `RUN.travel_time.filter_modes` = true is declared, MOVES RESULTS and belongs with the next family boundary.
- A CRLF producer passes `check_manifest.py` locally and fails in CI (§9.142): a Windows rebuild is followed by `normalise_eol.py`, which now reaches nested provenance records (§9.201).
- **Mumbai's refusing hosts are reached through the Internet Archive where it holds them** (§9.208, D17): 22 of the 41 sources whose hosts refuse this address (§9.207) are dated Wayback copies (`<id>_archived_<date>`; 4 empty captures kept unusable); 17 have no capture and wait on a network the hosts admit; two wait on the OGD key (`OGD_API_KEY` in `.env`, D16).
- The 2021 journey-to-work table stays an attended ABS extract (`B.external.commute_share_to_core`, §9.140). Not built: the event-demand overlay (§1); era-1 validation (§11); LiDAR, pedestrian counts, the floorspace audit (§13); two ABS DataPack URLs 404 (`STATUS.md`).

## Refused — do not re-raise

- Re-running pt2matsim per day type or variant, or comparing scenarios across builds (§3.5).
- Manual aerial correction of corridor lane counts: they are observed (§2.5).
- Inventing SCATS offsets; migrating off MATSim; reinstating SUMO (§9.88, §9.73, §9.74).
- Deriving `A.lightrail.line_speed_kmh` from GTFS alone — unidentifiable (§9.76).
- Reclassifying assumed fields to improve the count (§9.33); a typed rectangle or coordinate anywhere (§9.29, §9.31, §9.35).
- Storage above flow capacity (§15); a GTFS-Realtime collector (§9.23); a service day from a route id (§9.113); fitting the counts (#82).

## History

- §9.208 — archive copies; 2A/7 windows
- §9.207 — crossings in; merge measured
- §9.206 — evidenced fleet; live-set heap 
- §9.205 — citywide plans, targets, the fraction
- §9.204 — Mumbai through the harness; the MMR extent
- §9.201 — harvests; §9.202 — contract tiers, second city
- §9.177 — 567 fields; builders read the registry
- §9.176 — intro fixed: which runs are results is the board's
- §9.170 — documents at `docs/`; five defaults
- §9.169 — run inputs at 250
- §9.167 — footpath rebuild; F34
- §9.166 — 521 fields
- §9.164 — no MATSim default unreviewed
- §9.163 — counts map repaired
- §9.158 — lineage per output
