# Walk and bike — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 8 September 2026 (thirty-sixth session) · **Record read through:** §9.158 · **Written against family:** `F31`

## What is built

- **Both modes are physical in the qsim** (§9.54). `walk` and `bike` are qsim main modes routed and simulated on the road graph, which stands in for the footpath network because §3.5 forbids a remap. A pedestrian is `B.walk.pce` 0.0, speed-capped at `A.transit.walk_speed_ms` 1.25: present on every link, exchanging no capacity with motor traffic. A cyclist is `B.bike.pce` 0.2 (literature, swept 0.1–0.4) at `B.bike.speed_ms` 4.2 (§9.54). The router's estimate (`CappedSpeedTravelTime`) and the mobsim read the same loaded vehicle type, so estimate and physics cannot drift.
- **Link dynamics** are `RUN.qsim.link_dynamics` = `PassingQ` (§9.59). Under MATSim's silent FIFO default a walker at the head of a shared link's queue held every car behind it whatever its PCE; a car now overtakes a walker, at about 42 s per iteration (§9.59).
- **Road rules**: `A.network.pedestrian_excluded_classes` and `A.network.bicycle_excluded_classes` are both `[motorway, motorway_link]` — §9.58 corrected the walk list from §9.54's trunk exclusion, which mis-stated the law and severed the walkable city. Each mode is stripped from links outside its largest strongly connected component, and a one-way carriageway carries a walk/bike reverse complement (16,603 on S2, §9.58).
- **The walk wedge is repaired** (§9.58): `ActivityLinkAssigner` pins each activity to a link carrying every mode its person can use; `RUN.replanning.strategy_subpopulations` withholds `SubtourModeChoice` from boundary agents. #60's filed suspicion was refuted in the pinned engine's bytecode (§9.58).
- **Access/egress stubs** stay teleported at `RUN.routing.access_walk_beeline_factor` 1.6902 (measured); main walk detours at the road graph's own geometry (§9.54). **That teleportation is a live gap against GOAL requirement 1**: of 1,978 teleported walk legs on a 1 % run, **70.9 % end at a `pt interaction`** and only **67** have no pt leg on either side (§9.156).
- **Gradient reaches link travel time as physics, and only as physics** (§9.84, §9.140, #21 closed). `A.gradient.representation` = `link_speed` (`absent` recovers the flat network exactly). A signed `grade_pct` is stamped on run-network links from A1/A6 node elevations (81.9 % of walk/bike-capable links) and clamped at `A.gradient.grade_clamp_pct` 20.0. Walk takes Tobler's hiking function; bike takes a linear Parkin & Rotheram slowdown — `A.gradient.bike_uphill_slowdown_per_pct` 0.065, `bike_downhill_speedup_per_pct` 0.015, `bike_speed_floor_factor` 0.2, `bike_speed_ceiling_factor` 1.3 (§9.84). `citysim.GradientLinkSpeed` serves router and mobsim from one formula, now through a per-link table filled once (§9.154).
- **Motor-traffic stress is priced for bike** (§9.138, #107): every bike-capable link carries a `bike_stress_factor` from `A.bike_stress.aadt_class_by_highway` and the three declared Broach, Dill & Gliebe 2012 felt-distance factors (1.30 / 2.39 / 7.68 by AADT proxy band; 47,652 stamped links on S2). `citysim.BikeStressScoring` charges the felt surplus in scoring and `citysim.BikeStressDisutility` applies the same factor in the router's bike link cost. `A.bike_stress.representation = absent` recovers the fearless bike.
- **A dense-zone car trip pays a derived parking search time** (§9.138): a charged parking spell in a §9.31 priced zone costs `A.parking.search_min_max` (8.1 min, Shoup 2006; swept 3.5–14) × the zone's own `density_weight` ramp, once at arrival, at the transfer-penalty identity. Same home exemption as the price (§9.31).
- **Bike availability is drawn** per person at `B.population.bike_available_rate` 0.493 (literature, CWANZ; swept 0.30–1.00) and gated at `B.population.bike_min_age` 12 (assumed, swept 0–16, zero disables; §9.84). `AvailabilityModesCalculator` strips bike from the choice set of a person without one; external boundary agents keep it (§9.39).
- **THE CALIBRATION LOOP CAN NOW REACH BIKE, WHERE BEFORE IT REACHED NOTHING** (§9.158). `rebuild_stage` classified a field by its consumer's BASENAME and excluded anything it did not recognise — including fields carrying a declared `matsim_param` binding, which reach the emitted config on EVERY run. A binding is now evidence of run-time realisability, and the movable set went **5 → 21**: it now includes `B.population.bike_min_age`, `A.gradient.bike_speed_floor_factor` and `A.gradient.bike_speed_ceiling_factor`. Verify with `python src/calibrate/calibrate.py --run-config f29_gate_25pct --plan`.
- **`C.asc.cycle` is OPENED to a sweep and `C.asc.walk` is NOT** (§9.158). `C.asc.cycle` −1.35 takes the interval [−4.0, −1.35] **verbatim from the solve range its own held_fixed rule already named at §9.28** — the top is the §8.5 prior, the bottom is past the AToM walk–bike gap of 3.418, and the solve is CONSTRAINED against the observed trip lengths in `C.constraint.trip_length_km.*`, never against a mode share. `C.asc.walk` +0.35 stays FROZEN with a per-mode reason: walk's modelled mean trip is 4.58 km against an observed 0.70 (`_fit.json`, Newcastle LGA both ends) while **60.5 % of all pt routing requests come back as a walk** (§9.157, §9.158), so **walk is absorbing a routing failure** and its constant would absorb the failure with it.
- **Short trips get their observed distribution** (§9.69, #30): the gravity draw is a two-component mixture per purpose; the short kernel's mean `B.activity.short_trip_mean_km` 0.7 is derived from `C.constraint.trip_length_km.walk`, and its weight is solved to `B.activity.short_trip_band_share` (HTS Sydney 2012/13 Table 4.4.7, 18.8 % up to 1 km; swept ±25 %).
- **A denied lift drives**: `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (§9.105). Only a passenger who cannot drive is left on foot; `walk` is the control member.

## What is measured

- **Gate reading, F31 iteration 100** (`results/raw/aborted_20260908T100009_300it_25pct`, §9.157): **bike 5.4627 % against 2.2084 % (+147.4 %)** and **walk 11.9095 % against 13.4000 % (−11.1 %)** — walk is the second-closest mode on the board and the only one besides car within 15 %. Read on its own terms: three family boundaries separate this from F28, so no earlier gate is a comparison (§3.5).
- **WALK IS PRICED AS A TRANSIT RIDE, AND THAT IS WHY ITS GEOMETRY IS WRONG** (§9.158). Inside the pt router, `(marginalUtilityOfTraveling − performing)/3600` makes **one second walking cost 1.0400 seconds riding**, with `RUN.transit_router.direct_walk_factor` = 1.0. Measured on the F31 arm: **2,553,357 pt routing requests**, **33.4 % with no transit route at all**, **40.6 % of the answered choosing the network walk** — **60.5 % of all pt routing requests come back as a walk**, and those walk-answered trips have a **beeline mean of 7.81 km (p90 12.43)**. Walk's modelled mean of **4.58 km against an observed 0.70** (`_fit.json`, Newcastle LGA both ends; §9.157 quotes 4.51 on the resident-trip basis) is substantially that. Sweeping the factor: 1.5 → 27.3 % walk-answered, 2.0 → 21.7 %, 3.0 → 16.2 % (§9.158).
- **THE READING POINT ITSELF CANNOT RESOLVE BIKE** (§9.158). Between iteration 80 and 100 of the SAME run, with nothing changed, bike's deviation moves further than the whole 10 % acceptance band on **4 of the 6** arms that ever reached 100 (max 17.76 points; `CAL.search.reading_drift_pct`, `python src/analyse/measure_reading_stability.py --all --from 80 --to 100`). On the F31 arm itself bike moved 8.66 points in that window. A bike level read at 100 is partly a statement about how far the run had got.
- **Gate reading, F23 iteration 100** (§9.139): bike 4.66 % (+111.2 %), from +185.5 % at F22's gate — the stress channel's first measured effect — still falling at the stop; walk 9.76 % (−27.2 %). The walk/car pair crossed their targets near iteration 45–50 under the parking search time and kept going.
- **The stress channel is live, not just declared**: smoke `20260901T132710_2it_1pct` iteration 0 holds 406 `bikeStress` personScore charges totalling −24,500 utils and 1,139 `parkingSearch` charges totalling −1,171.8 utils (§9.138). A smoke is plumbing evidence, never a result.
- **The imbalance lives inside the car-available group** (§9.135, F21 arm at iteration 100): car-available residents make 78.3 % of target-LGA trips and put 86.4 % on car, 2.9 % on walk; licensed-no-car residents (5.8 % of trips) bike 36.0 % and walk 34.7 %; no-licence residents (15.9 %) ride 41.3 %, walk 26.6 %, bike 16.5 %. A short car trip costs almost nothing (`accessEgressType` `none`, §9.54; car constant 0; parking free outside the 150 priced zones).
- **`accessEgressType = none` is load-bearing, so the short-car-trip cost is a design decision, not a revert** (§9.136): §9.54's `TolerantAgentSource`/`GenericRouteTeleporter` and §9.58's activity-link repair are built on it.
- **Who cycles**: of 913 residents whose best-scored plan is bike, 95.4 % have no car available; car-less residents (24.7 % of trips) walk 48.1 %, cycle 16.7 % and ride 18.5 % (§9.123).
- **Work trips by home LGA against census G62** (§9.131): walk 18.7 / 16.1 / 19.2 % against 4.4 / 1.6 / 1.4 %; bike 8.9 / 9.0 / 8.9 % against 1.4 / 0.16 / 0.18 % (Newcastle / Lake Macquarie / Maitland, F19 iteration 20).
- **The feasibility bound**: `B.mode.walk_feasible_km` at its derived p99 of 3.22 km made the fit worse (sum of deviations 509.9 % to 577.1 %) and moved walk's mean 8.84 to 8.72 km (§9.106); `B.mode.bike_feasible_km` likewise. Both held at 0.0.
- **Gradient's motivation**: 30.5 % of 50,182 road edges exceed 4 % grade, and modelled bike trips ran 9.21 km / 41.7 min against a measured 5.2 / 19.2 before the channel existed (§9.84). No paired arm has measured the channel's effect.

## What is open

- **Walk's geometry now has a NAMED mechanism and an undecided remedy** (§9.158). `RUN.transit_router.direct_walk_factor` is a declared field with a sweep to 2.0 and moving it is a family boundary and a FIDELITY decision — it must not be picked to land walk's share. Filed with its measured numbers; the operator decides.
- **#30** — the sub-1 km trips are generated (§9.107) and the short-trip band shares still match their observed values to three decimals after the 4 Sep rebuild (§9.142). The walk/car allocation of those trips is unchanged as the open question (§9.107).
- **The gradient channel's effect is unmeasured**: no paired arm differing only in `A.gradient.representation` has read bike's mean trip and time against the observed 5.2 km / 19.2 min (§9.84).
- **#50** — the bike age gate is assumed; no mode × age cell is held (§9.84). It is one of the three issues BLOCKING the launcher today because it states no measurement, and its real next step is an ACQUISITION, not a run (§9.158).
- **Bike's residual after the stress channel**: the remaining excess is the car-less quarter's missing alternatives (§9.123: 95.4 % of bike-choosers have no car). `C.asc.cycle`'s newly opened interval is a CONSTRAINED solve against observed trip length (§9.28, §9.158), never a fit against bike's share.
- **Walk detour**: main walk at the road graph's ~1.34 rather than the measured 1.6902 flatters walk slightly less than truth; stated, not corrected (§9.54).

## Refused — do not re-raise

- A per-trip feasibility bound on walk or bike in the replanner (§9.106): it cannot remove seeded behaviour. Held at 0.0.
- Tuning bike's own time rates against its excess (§9.123): the excess is the car-less quarter's missing lifts.
- **Solving `C.asc.walk` against walk's share or its trip length** (§9.158): walk is absorbing a PT routing failure and its constant would absorb that failure too.
- Destination placement as the cause of walk's geometry (§9.107 corrected §9.103 and §9.106).
- Bike as displaced ride, asserted without measurement (§9.114 corrected §9.109 and §9.112); §9.123 carries the measurement.
- A gradient utility term in scoring, or an access-decay curve: MATSim has neither, link speed is the chosen representation (§9.84, §9.140, #21).
- Teleported walk or bike as main modes, re-added access/egress stubs, and the trunk-road pedestrian exclusion (§9.54, §9.58).
- Walk as the fallback for a licensed, car-available passenger whose lift fails (§9.105).

## History

- §9.158 — walk is priced as a transit ride; `C.asc.cycle` opened, `C.asc.walk` frozen
- §9.157 — F31 gate: bike +147.4 %, walk −11.1 %
- §9.142 — short trips drawn against balanced arrivals; bands unmoved
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
