# Walk and bike — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 25 September 2026 (sixty-third session) · **Record read through:** §9.213 · **Written against family:** `F37`

## What is built

- **The two distance feasibility bounds are declared, reach the config, and are OFF** (§9.163): `B.mode.walk_feasible_km` and `B.mode.bike_feasible_km` ship at **0.0** with `inert_at: 0.0`, and `citysim.GatedSubtourModeChoice.beyondReach` returns false on any limit ≤ 0; their derived values are 3.22 km and 23.95 km (§9.106).
- **Walk and bike have a footpath network** (§9.167, #183): 40,203 harvested path ways are walk- and bike-capable links of the one rebuilt network; `A.network.path_modes_by_class` says which modes a class admits and a way's own access=, foot= and bicycle= tags override it (`A.network.path_access_overrides`: 4,484 rewritten, 2,252 dropped); a path link is uncongested (`A.network.path_lane_capacity_veh_h`). On the S2 weekday network walk is permitted on **363,818 links (35,381 km, 168,550 footpath-only)** and bike on **265,523**.
- **Both modes are physical in the qsim** (§9.54): a pedestrian is `B.walk.pce` 0.0 at `A.transit.walk_speed_ms` 1.25, exchanging no capacity with motor traffic; a cyclist is `B.bike.pce` 0.2 (literature, swept 0.1–0.4) at `B.bike.speed_ms` 4.2. Router (`CappedSpeedTravelTime`) and mobsim read the same vehicle type.
- **Link dynamics** `RUN.qsim.link_dynamics` = `PassingQ` (§9.59): a car overtakes a walker, at about 42 s per iteration.
- **Road rules**: `A.network.pedestrian_excluded_classes` and `A.network.bicycle_excluded_classes` are both `[motorway, motorway_link]` (§9.58 corrected §9.54's trunk exclusion); each mode is stripped outside its largest strongly connected component, and a one-way carriageway carries a walk/bike reverse complement (16,603 on S2, §9.58).
- **The walk wedge is repaired** (§9.58): `ActivityLinkAssigner` pins each activity to a link carrying every mode its person can use; `RUN.replanning.strategy_subpopulations` withholds `SubtourModeChoice` from boundary agents; #60's suspicion was refuted in the pinned bytecode.
- **PT access, egress and transfer walks are network legs the qsim executes** (§9.167, #167): `RUN.routing.access_egress_type` = `accessEgressModeToLink`, `RUN.transit_router.access_egress_basis` = `network`, and `citysim.NetworkDirectWalkPtRouter` splices the walk router's answer over every beeline walk leg, transfers included; `teleported=0` on the 1 % probes (388 stubs over 1 km on the footpath network against 511 on the road graph, `20260912T065939_4it_1pct`) and on arm 0 (§9.169). `RUN.routing.access_walk_beeline_factor` 1.6902 prices only the beeline basis.
- **Gradient reaches link travel time as physics only** (§9.84, §9.140, #21): `A.gradient.representation` = `link_speed` (`absent` recovers the flat network); `grade_pct` is stamped from A1/A6 node elevations, clamped at `A.gradient.grade_clamp_pct` 20.0; walk takes Tobler, bike a linear Parkin & Rotheram slowdown (`A.gradient.bike_uphill_slowdown_per_pct` 0.065, `bike_downhill_speedup_per_pct` 0.015, `bike_speed_floor_factor` 0.2, `bike_speed_ceiling_factor` 1.3); `citysim.GradientLinkSpeed` serves router and mobsim from one per-link table (§9.154).
- **Motor-traffic stress is priced for bike** (§9.138, #107): every bike-capable link carries a `bike_stress_factor` from `A.bike_stress.aadt_class_by_highway` and the Broach, Dill & Gliebe 2012 factors (1.30 / 2.39 / 7.68; 47,652 stamped links on S2); `citysim.BikeStressScoring` charges the felt surplus and `citysim.BikeStressDisutility` applies it in the router; `A.bike_stress.representation = absent` recovers the fearless bike.
- **A dense-zone car trip pays a derived parking search time** (§9.138): `A.parking.search_min_max` (8.1 min, Shoup 2006; swept 3.5–14) × the zone's `density_weight` ramp, once at arrival, at the transfer-penalty identity; same home exemption as the price (§9.31).
- **Bike availability is drawn** at `B.population.bike_available_rate` 0.493 (literature, CWANZ; swept 0.30–1.00), gated at `B.population.bike_min_age` 12 (assumed, swept 0–16; §9.84); `AvailabilityModesCalculator` strips bike from a person without one; boundary agents keep it (§9.39).
- **The calibration loop reaches bike** (§9.158): a declared `matsim_param` binding is evidence of realisability, and the movable set (5 → 21) includes `B.population.bike_min_age`, `A.gradient.bike_speed_floor_factor` and `A.gradient.bike_speed_ceiling_factor` (`python src/calibrate/calibrate.py --run-config f29_gate_25pct --plan`).
- **`C.asc.cycle` is OPENED to a sweep and `C.asc.walk` is NOT** (§9.158): `C.asc.cycle` −1.35 takes [−4.0, −1.35] from the solve range its held_fixed rule named at §9.28, CONSTRAINED against `C.constraint.trip_length_km.*`, never a share. `C.asc.walk` +0.35 stays FROZEN: walk's modelled mean trip is 3.74 km against 0.70 observed (arm 0, §9.169; 3.28 km on F32) while 60.5 % of pt routing requests came back as a walk on the F31 arm (§9.157), so walk is absorbing a routing failure and its constant would absorb it too.
- **Short trips get their observed distribution** (§9.69, #30): a two-component gravity mixture per purpose; `B.activity.short_trip_mean_km` 0.7 derives from `C.constraint.trip_length_km.walk`, its weight solved to `B.activity.short_trip_band_share` (HTS Sydney 2012/13, 18.8 % up to 1 km; swept ±25 %).
- **A denied lift drives**: `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (§9.105); `walk` is the control member.

## What is measured

- **The F35 result, the first read on the footpath network** (`20260912T202242_300it_25pct` at iteration 300, §9.169): walk **11.7677 % against 13.4000 % (−12.2 %)**, over 10 % and no longer past the stop bar, on **18,645** trips at a mean **3.74 km against 0.70 (+434 %)**, coverage **63.54 %**; walk stuck 1,661 of 1,115,677 departures. Bike **6.6605 % against 2.2084 % (+201.6 %, STOP)** on **10,553** trips at **8.10 km (+56 %)**, coverage **27.12 %**, geometry ratio 1.56 (`_fit.json`). A direction, not a comparison with F32 (§3.5): walk toward target, bike AWAY from +113.0 %.
- **The short-trip supply IS at the seed; the run reads it on another basis** (§9.177, #30): the seed's core legs are **17.70 %** at ≤ 0.748 km straight (1 km at detour 1.3376; `B2_activity_trips_WEEKDAY.csv`, 2,225,609 legs) against the Sydney 18.8 % band; the routers pair reads **20.02 %** of resident linked trips on the straight × detour basis and **13.82 %** ROUTED (arm 0 11.13 %, §9.169), and car carries **51.5 %** of the routed short trips, walk **29.5 %** (`extract_metrics.trip_geometry`). The loss is allocation, not the kernel.
- **The car-less choose between long walks, long rides and bikes** (§9.213, F36 arm 0 at iteration 230, not a result, `_mode_by_demographics.json`): ride 49.1 %, walk 29.4 %, bike 12.2 % at a mean **11.9 km**, pt **5.1 %**; bike 9.8 km among the car-available.
- **Bike by car availability on the routers pair** (§9.177, `_mode_by_demographics.json` on `20260915T000704_250it_25pct`, #107): **2.9 %** of the car-available's 448,807 trips at a **10.58 km** routed mean; **14.8 %** of the car-less's 98,880 at **11.48 km**; walk 4.25 % / 31.67 % at 4.94 / 5.99 km.
- **PT access, egress and transfer walks executed on a result** (§9.169, #167, #183): 8,687 pt trips on arm 0 carry **27,765 network walk legs** (median 461 m, mean 576 m, 5,748 over 1 km) and 41,243 coordinate-to-link stubs (median 19 m, 18 over 1 km); no teleported leg mode appears. Both issues are measured, to be closed.
- **Walk is used as a long-distance mode** (§9.163): F32 mean walk trip **3.283 km** against 0.70 (4.69×), median 1.249 km, duration **49.0 min** against 12.3; the all-trips mean fell 6.94 → 5.17 km between iterations 100 and 300.
- **Bike is ridden too far and concentrated in the car-less quarter** (§9.163, #107): F32 bike **+113.0 %** at 4.7045 %; mean **7.3217 km** against 5.2, **43.71 min** against 19.2; no licence 8.8 % of trips against licence 2.5 % (`mode_by_demographics.py`); age 12–17 **15.4 %**, everyone else 2.5–4.9 %.
- **The F32 result, and walk fell past the stop bar on the way to it** (`20260909T015217_300it_25pct`, §9.162): **bike 4.7045 % (+113.0 %)**, **walk 9.8490 % (−26.5 %)**; walk was inside the band at iteration 110 (−9.6 %), left it by 200 (−14.4 %) and the cutoff took **−0.941 pp** off it — it descends THROUGH its target.
- **Walk is priced as a transit ride, and that is why its geometry is wrong** (§9.158): inside the pt router `(marginalUtilityOfTraveling − performing)/3600` makes one second walking cost 1.0400 seconds riding at `RUN.transit_router.direct_walk_factor` = 1.0; on the F31 arm 2,553,357 pt requests, 33.4 % with no transit route, **60.5 % answered as a walk** with a beeline mean of 7.81 km.
- **The supply half of walk's deficit moved a little; the shape half cannot without an observation** (§9.164, #30): the placement loop no longer discards every tour still to be placed when one will not fit — **547** weekday, 241 Saturday and 77 Sunday tours attempted, the week trip rate **3.398 against the HTS 3.473**; **18,446** weekday tours are still dropped by a different mechanism. The sub-1 km share is the gravity kernel's SHAPE, and the HTS gives a mean and no distribution (§9.8, §9.13).

## What is open

- **Walk's long trips are pt requests the router could not route** (§9.213, #30, #162): F36 arm 0 walked **4.54 km against 0.70** (iteration 230) while 73.7 % of pt requests came back as a walk under a 1,200 m access ceiling, now the measured reach. F37 arm 0 reads walk's mean trip first: a walk distance cost laid on routing fallbacks would be a compensating constant. Not represented: the pedestrian crossing WAIT and road links' foot=/bicycle= tags (§9.167).
- **Bike's distance cost is BUILT and unread** (§9.211, D9, #107): `C.scoring.marginal_utility_of_distance_per_m` is declared and `derived` — bike **−0.000192308 utils/m** = −1/(`C.constraint.trip_length_km.bike` × 1000), since a utility linear in distance decays the choice with mean 1/|β|, so the observed 5.2 km mean fixes it; the sweep is that mean's own spread over the survey years (3.1–5.2 km). Every other mode stays at MATSim's 0.0. Measured by bike's mean trip and its share by car availability on F36's arm 0.
- **Walk's geometry has a NAMED mechanism and an undecided remedy** (§9.158): `RUN.transit_router.direct_walk_factor` has a sweep to 2.0; moving it is a family boundary and a FIDELITY decision, never picked to land walk's share.
- **#30 is re-aimed at allocation** (§9.177, user decision): the band shares match at the zone matrix (§9.142) and on placed coordinates (17.70 % vs 18.8 %); the chains report will state the placed-coordinate band beside the matrix one at the rebuild.
- **The gradient channel's effect is unmeasured**: no paired arm differing only in `A.gradient.representation` has read bike's mean trip and time against 5.2 km / 19.2 min (§9.84).
- **#50** — the bike age gate is assumed; no mode × age cell is held (§9.84); it carries `decision-needed` and does not block the launcher (§9.160).
- **Bike's residual after the stress channel** is the car-less quarter's missing alternatives (§9.123: 95.4 % of bike-choosers have no car); `C.asc.cycle`'s interval is a constrained solve against observed trip length (§9.28, §9.158), never a fit against share.
- **Walk detour**: main walk at the road graph's ~1.34 rather than the measured 1.6902 flatters walk slightly less than truth; stated, not corrected (§9.54).

## Refused — do not re-raise

- A per-trip feasibility bound on walk or bike in the replanner (§9.106): it cannot remove seeded behaviour. Held at 0.0.
- Tuning bike's own time rates against its excess (§9.123): the excess is the car-less quarter's missing lifts.
- **Solving `C.asc.walk` against walk's share or its trip length** (§9.158): walk is absorbing a PT routing failure.
- Destination placement as the cause of walk's geometry (§9.107 corrected §9.103 and §9.106).
- Bike as displaced ride, asserted without measurement (§9.114 corrected §9.109 and §9.112); §9.123 carries the measurement.
- A gradient utility term in scoring, or an access-decay curve: link speed is the representation (§9.84, §9.140, #21).
- Teleported walk or bike as main modes, re-added access/egress stubs, and the trunk-road pedestrian exclusion (§9.54, §9.58).

## History

- §9.213 — long walks are routing fallbacks
- §9.211 — bike's distance cost built
- §9.177 — short trips at the seed; #30 is allocation
- §9.170 — the tenth report re-reads arm 0 unchanged
- §9.169 — arm 0 on footpaths: walk −12.2 %, bike +201.6 %
- §9.167 — footpath network built, F34 opened
- §9.166 — footpath network filed as a decision (#183)
- §9.164 — the whole-day discard repaired; the short end is unobserved
- §9.163 — short-trip supply flat, car takes 63 % of it; bike too far
- §9.162 — the first result: walk −26.5 %, descending through target
- §9.158 — walk priced as a transit ride; `C.asc.cycle` opened
- §9.157 — F31 gate: bike +147.4 %, walk −11.1 %
- §9.142 — short trips drawn against balanced arrivals; bands unmoved
- §9.140 — gradient weights and decay retired
- §9.139 — both channels' first gate reading
