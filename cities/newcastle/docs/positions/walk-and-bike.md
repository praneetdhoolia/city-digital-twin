# Walk and bike — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 3 September 2026 · **Record read through:** §9.140 · **Open family:** F23 (the package on disk opens F24 at its first launch)

## What is built

- **Both modes are physical in the qsim** (§9.54). `walk` and `bike` are qsim main modes routed and simulated on the road graph, which stands in for the footpath network because §3.5 forbids a remap. A pedestrian is `B.walk.pce` 0.0, speed-capped at `A.transit.walk_speed_ms` 1.25: present on every link, exchanging no capacity with motor traffic. A cyclist is `B.bike.pce` 0.2 (literature, swept 0.1–0.4) at `B.bike.speed_ms` 4.2 (§9.54). The router's estimate (`CappedSpeedTravelTime`) and the mobsim read the same loaded vehicle type, so estimate and physics cannot drift.
- **Link dynamics** are `RUN.qsim.link_dynamics` = `PassingQ` (§9.59). Under MATSim's silent FIFO default a walker at the head of a shared link's queue held every car behind it whatever its PCE; a car now overtakes a walker. Measured price about 42 s per iteration over FIFO (§9.59).
- **Road rules**: `A.network.pedestrian_excluded_classes` and `A.network.bicycle_excluded_classes` are both `[motorway, motorway_link]` — §9.58 corrected the walk list from §9.54's trunk exclusion, which mis-stated the law and severed the walkable city. Each mode is stripped from links outside its largest strongly connected component, and a one-way carriageway carries a walk/bike reverse complement (16,603 on S2, §9.58).
- **The walk wedge is repaired** (§9.58): `ActivityLinkAssigner` pins each activity to a link carrying every mode its person can use, so the qsim's first hop connects; `RUN.replanning.strategy_subpopulations` withholds `SubtourModeChoice` from boundary agents. #60's filed suspicion (the walk router ignores `disallowedNextLinks`) was refuted in the pinned engine's bytecode (§9.58).
- **Access/egress stubs** stay teleported at `RUN.routing.access_walk_beeline_factor` 1.6902 (measured); main walk detours at the road graph's own geometry (§9.54).
- **Gradient reaches link travel time as physics, and only as physics** (§9.84, §9.140, #21 closed): the two `C.gradient.*` utility weights that reached nothing were retired on 3 Sep 2026, with the PT walk-access decay group (`C.walk.decay_*`, `gaussian_*`, `max_considered_m`) — the scored access walk is the continuous penalty proposal 6.3 asked for, and a swept field read by nothing was a sensitivity band of zero by construction (§9.140). `A.gradient.representation` = `link_speed` (`absent` recovers the flat network exactly). A signed `grade_pct` is stamped on run-network links from A1/A6 node elevations (81.9% of walk/bike-capable links) and clamped at `A.gradient.grade_clamp_pct` 20.0 (§9.84). Walk takes Tobler's hiking function — `A.gradient.walk_tobler_slope_coeff` 3.5, `A.gradient.walk_tobler_offset` 0.05 (literature, swept); bike takes a linear Parkin & Rotheram slowdown — `A.gradient.bike_uphill_slowdown_per_pct` 0.065, `A.gradient.bike_downhill_speedup_per_pct` 0.015, `A.gradient.bike_speed_floor_factor` 0.2, `A.gradient.bike_speed_ceiling_factor` 1.3 (§9.84). `citysim.GradientLinkSpeed` serves router and mobsim from one formula; `GradientSignalsNetworkFactory` keeps gradient and signals alive together.
- **The PT router's direct walk is the network walk**: `RUN.transit_router.direct_walk_basis` = `network`, `RUN.transit_router.direct_walk_factor` 1.0 (§9.121). The stock raptor compared a beeline walk, sent harbour crossings on a ~19 km road detour and counted them as realised walk; 38.3% of residents' PT-plan trips were walk-only on F16 (§9.121).
- **Motor-traffic stress is priced for bike** (§9.138, #107): every bike-capable run-network link carries a `bike_stress_factor` from `A.bike_stress.aadt_class_by_highway` and the three declared Broach, Dill & Gliebe 2012 felt-distance factors (1.30 / 2.39 / 7.68 by AADT proxy band, purpose-bound sweeps; 47,652 stamped links on S2). `citysim.BikeStressScoring` charges the felt surplus — (factor−1) × the mobsim's own traversal seconds — at trip-weighted VOT × `beta_bike_mode` × marginalUtilityOfMoney, and `citysim.BikeStressDisutility` applies the same factor in the router's bike link cost, so hostile roads are both fled en route and felt in mode choice. `A.bike_stress.representation = absent` recovers the fearless bike (§9.138).
- **A dense-zone car trip pays a derived parking search time** (§9.138): a charged parking spell in a §9.31 priced zone costs `A.parking.search_min_max` (8.1 min, Shoup 2006; swept 3.5–14) × the zone's own `density_weight` ramp, once at arrival, at the transfer-penalty identity — the §9.136 measured walk/car candidate chosen over physical access/egress stubs, which §9.58 refused. Same home exemption as the price (§9.31).
- **Bike availability is drawn** per person at `B.population.bike_available_rate` 0.493 (literature, CWANZ; swept 0.30–1.00 — §9.39 declared it at 0.50 assumed, and the registry's later source upgrade wins) and gated at `B.population.bike_min_age` 12 (assumed, swept 0–16, zero disables; §9.84). `AvailabilityModesCalculator` strips bike from the choice set of a person without one; external boundary agents keep it (§9.39).
- **Short trips get their observed distribution** (§9.69, #30): the gravity draw is a two-component mixture per purpose; the short kernel's mean `B.activity.short_trip_mean_km` 0.7 is derived from `C.constraint.trip_length_km.walk`, and its weight is solved to `B.activity.short_trip_band_share` (HTS Sydney 2012/13 Table 4.4.7, all purposes 18.8% up to 1 km; literature, swept ±25%).
- **A denied lift drives**: `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (§9.105). Only a passenger who cannot drive is left on foot; `walk` is the control member.
- **The licence rate is measured** (§9.131): `B.population.licence_rate_by_age_band` is TfNSW licence holders over ABS population by age and LGA (pooled 18–24 0.78, 35–44 1.00; Newcastle's 18–24 0.68), replacing a literature vector that left 14.2–14.8% of the employed unlicensed and so walking, cycling or riding rail. The population is rebuilt (612,634 persons); chains, plans and run inputs are not — the F21 arm's first build (§9.131).

## What is measured

- **Gate reading, F23 iteration 100** (`results/raw/aborted_20260901T165115_300it_25pct`, §9.139): **bike 4.66% against 2.21% (+111.2%), from +185.5% at F22's gate — the stress channel's first measured effect** — still falling (6.55% at it.0) at the stop. Walk 9.76% against 13.40% (−27.2%, from F22's −36.6%): the pair crossed their targets near iteration 45–50 under the parking search time and kept going — car reached 66.94% (+14.8%), walk kept falling. Bike's outflow landed on walk and car, not on ride (−40.1%, F22 −41.3%).
- **The stress channel is live, not just declared**: smoke `20260901T132710_2it_1pct` iteration 0 holds 406 `bikeStress` personScore charges totalling −24,500 utils — the seeded arterial-riding bike trips feel the full ×7.68 — and 1,139 `parkingSearch` charges totalling −1,171.8 utils (§9.138). A smoke is plumbing evidence, never a result.
- **Gate reading, F22 iteration 100** (`results/aborted_20260831T165127_300it_25pct`, §9.136): walk 8.50% against 13.40% (−36.6%) — it crossed its target near iteration 38 and kept falling as car rose to 67.2% (+15.2%); bike 6.30% against 2.21% (+185.5%), drifting down from 8.12% at iteration 20. **The seesaw reproduced F21's gate almost exactly under pt fares** (F21: walk −36.6%, car +16.0%, §9.134) — pricing pt does not price the short car trip.
- **The imbalance lives inside the car-available group** (§9.135, F21 arm at iteration 100): car-available residents make 78.3% of target-LGA trips and put 86.4% on car, 2.9% on walk; licensed-no-car residents (5.8% of trips) bike 36.0% and walk 34.7%; no-licence residents (15.9%) ride 41.3%, walk 26.6%, bike 16.5%. A short car trip costs almost nothing (`accessEgressType` `none`, §9.54; car constant 0; parking free outside the 150 priced zones).
- **`accessEgressType = none` is load-bearing, so the short-car-trip cost is a design decision, not a revert** (§9.136): §9.54's `TolerantAgentSource`/`GenericRouteTeleporter` and §9.58's activity-link repair are built on it, and §9.58 explicitly refused re-adding stubs. The derivable candidates: physical car access/egress walk, or a parking search/access time for dense zones extending §9.31's job-density derivation.
- **Deepest reading of any family**: F17 iteration 50 — walk 14.88% (+11.0%) with car at +1.7%; bike 8.29% and moving away (§9.126).
- **Walk geometry**: mean walk trip 6.66 km at iteration 100 against observed 0.70 km, falling from 8.12 at iteration 0 (§9.108). Walk and car are swapped at both ends: of resident trips under 1 km only 39.5% are walked and car takes 39.2% (§9.107). The sub-1 km trips exist in about the right number — 16.31% of resident trips against the 18.8% observed band share (§9.107, §9.69). Bike mean 10.04 km against observed 5.20 (§9.107).
- **Who cycles**: of 913 residents whose best-scored plan is bike, 95.4% have no car available; car-less residents (24.7% of trips) walk 48.1%, cycle 16.7% and ride 18.5% (§9.123). Under the F12 seed 51.6% of bike trips were by licensed, car-available residents (§9.114); §9.123 measures the scored choice set and is the newer finding.
- **Work trips by home LGA against census G62** (§9.131): walk 18.7 / 16.1 / 19.2% against 4.4 / 1.6 / 1.4%; bike 8.9 / 9.0 / 8.9% against 1.4 / 0.16 / 0.18% (Newcastle / Lake Macquarie / Maitland, F19 iteration 20).
- **The feasibility bound**: `B.mode.walk_feasible_km` at its derived p99 of 3.22 km made the fit worse (sum of deviations 509.9% to 577.1%) and moved walk's mean 8.84 to 8.72 km (§9.106); `B.mode.bike_feasible_km` (23.95 km derived) likewise. Both held at 0.0.
- **Two-state scoring** (§9.121): the F15 seed executed every car plan under gridlock, so bike scored +67.95 utils over car and 48.7% of car-available residents preferred it; under the uniform first-execution draw that fell to 14.1% at F16 iteration 10.
- **Gradient's motivation**: 30.5% of 50,182 road edges exceed 4% grade, and modelled bike trips ran 9.21 km / 41.7 min against a measured 5.2 / 19.2 before the channel existed (§9.84). No paired arm has measured the channel's effect.

## What is open

- **#30** — the sub-1 km trips are generated (§9.107); the walk/car allocation of short trips is the open question, a calibration of the relative cost of distance that has never been scored against a per-mode distance target (§9.107). Destination placement is measured present for the corridor (§9.130).
- **The gradient channel's effect is unmeasured**: no paired arm differing only in `A.gradient.representation` has read bike's mean trip and time against the observed 5.2 km / 19.2 min (§9.84); #21 is closed on the retirement, not on that measurement (§9.140).
- **#50** — the bike age gate is assumed; no mode by age cell is held (§9.84).
- **The seesaw now over-swings instead of sitting low** (§9.139): under the parking search time walk and car pass THROUGH their targets in-run and keep going (walk −27.2% low, car +14.8% high at the F23 gate; walk was momentarily +8.6% at it.40). Whether the equilibrium overshoots because the search minutes are one-shot at arrival (no within-day feedback) or because walk's own cost dominates past the crossing is the next family's question — not a constant to tune (§9.123 split first).
- **Bike's residual after the stress channel** (§9.139): +111.2% and falling at the stop; the remaining excess is the car-less quarter's missing alternatives (§9.123: 95.4% of bike-choosers have no car) — the stress factors' sweep members are the declared axis if the fall stalls, never an ASC.
- **Walk detour**: main walk at the road graph's ~1.34 rather than the measured 1.6902 flatters walk slightly less than truth; stated, not corrected (§9.54).

## Refused — do not re-raise

- A per-trip feasibility bound on walk or bike in the replanner (§9.106): it cannot remove seeded behaviour, and the whole-proposal rejection chain consistency forces traps agents. Held at 0.0.
- Tuning bike's own constants or time rates against its excess (§9.123): the excess is the car-less quarter's missing lifts, and moving them would fit the symptom.
- Destination placement as the cause of walk's geometry (§9.107 corrected §9.103 and §9.106).
- Bike as displaced ride, asserted without measurement (§9.114 corrected §9.109 and §9.112); §9.123 carries the measurement.
- A gradient utility term in scoring, or an access-decay curve: MATSim has neither, link speed is the chosen representation, and the fields are retired (§9.84, §9.140, #21).
- Teleported walk or bike, re-added access/egress stubs, and the trunk-road pedestrian exclusion (§9.54, §9.58).
- Walk as the fallback for a licensed, car-available passenger whose lift fails (§9.105).

## History

- §9.140 — gradient weights and decay retired
- §9.139 — both channels' first gate reading
- §9.138 — bike stress and parking search built
- §9.136 — seesaw survives fares; cost decision
- §9.134 — F21 gate: walk overshot downward
- §9.131 — licence rate measured from counts
- §9.126 — F17 converged car and walk
- §9.123 — car-less quarter explains bike
- §9.121 — direct walk becomes network walk
- §9.114 — most cyclists own cars
- §9.108 — walk geometry converging on trend
- §9.107 — walk and car swapped ends
- §9.106 — feasibility bound fails, disabled
- §9.105 — denied lift drives, not walks
- §9.84 — gradient as link speed built
- §9.69 — short-trip observed distribution added
- §9.59 — PassingQ link dynamics declared
- §9.58 — walk wedge repaired four ways
- §9.54 — walk and bike become physical
- §9.39 — bike availability drawn, declared
