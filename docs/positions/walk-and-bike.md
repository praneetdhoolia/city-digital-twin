# Walk and bike — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 30 September 2026 (sixty-fourth session) · **Record read through:** §9.219 · **Written against family:** `F39`

## What is built

- **The two distance feasibility bounds are declared, reach the config, and are OFF** (§9.163): `B.mode.walk_feasible_km` and `B.mode.bike_feasible_km` ship at **0.0** with `inert_at: 0.0`, and `citysim.GatedSubtourModeChoice.beyondReach` returns false on any limit ≤ 0; their derived values are 3.22 km and 23.95 km (§9.106).
- **Walk and bike have a footpath network** (§9.167, #183): 40,203 harvested path ways are walk- and bike-capable links of the one rebuilt network; `A.network.path_modes_by_class` says which modes a class admits and a way's own access=, foot= and bicycle= tags override it (`A.network.path_access_overrides`: 4,484 rewritten, 2,252 dropped); a path link is uncongested (`A.network.path_lane_capacity_veh_h`). On the S2 weekday network walk is permitted on **363,818 links (35,381 km, 168,550 footpath-only)** and bike on **265,523**.
- **Both modes are physical in the qsim** (§9.54): a pedestrian is `B.walk.pce` 0.0 at `A.transit.walk_speed_ms` 1.25, exchanging no capacity with motor traffic; a cyclist is `B.bike.pce` 0.2 (literature, swept 0.1–0.4) at `B.bike.speed_ms` 4.2. Router (`CappedSpeedTravelTime`) and mobsim read the same vehicle type.
- **Link dynamics** `RUN.qsim.link_dynamics` = `PassingQ` (§9.59): a car overtakes a walker, at about 42 s per iteration.
- **Road rules**: `A.network.pedestrian_excluded_classes` and `A.network.bicycle_excluded_classes` are both `[motorway, motorway_link]` (§9.58 corrected §9.54's trunk exclusion); each mode is stripped outside its largest strongly connected component, and a one-way carriageway carries a walk/bike reverse complement (16,603 on S2, §9.58).
- **The walk wedge is repaired** (§9.58): `ActivityLinkAssigner` pins each activity to a link carrying every mode its person can use; `RUN.replanning.strategy_subpopulations` withholds `SubtourModeChoice` from boundary agents; #60's suspicion was refuted in the pinned bytecode.
- **PT access, egress and transfer walks are network legs the qsim executes** (§9.167, #167): `RUN.routing.access_egress_type` = `accessEgressModeToLink`, `RUN.transit_router.access_egress_basis` = `network`, and `citysim.NetworkDirectWalkPtRouter` splices the walk router's answer over every beeline walk leg, transfers included; `teleported=0` on the probes and on a full arm (§9.169). `RUN.routing.access_walk_beeline_factor` 1.6902 prices only the beeline basis.
- **Gradient reaches link travel time as physics only** (§9.84, §9.140, #21): `A.gradient.representation` = `link_speed` (`absent` recovers the flat network); `grade_pct` is stamped from A1/A6 node elevations, clamped at `A.gradient.grade_clamp_pct` 20.0; walk takes Tobler, bike a linear Parkin & Rotheram slowdown (`A.gradient.bike_uphill_slowdown_per_pct` 0.065, `bike_downhill_speedup_per_pct` 0.015, `bike_speed_floor_factor` 0.2, `bike_speed_ceiling_factor` 1.3); `citysim.GradientLinkSpeed` serves router and mobsim from one per-link table (§9.154).
- **Motor-traffic stress is priced for bike** (§9.138, #107): every bike-capable link carries a `bike_stress_factor` from `A.bike_stress.aadt_class_by_highway` and the Broach, Dill & Gliebe 2012 factors (1.30 / 2.39 / 7.68; 47,652 stamped links on S2); `citysim.BikeStressScoring` charges the felt surplus and `citysim.BikeStressDisutility` applies it in the router; `A.bike_stress.representation = absent` recovers the fearless bike.
- **Bike's distance cost is built and ran on F37's arm 0** (§9.211, D9, #107): `C.scoring.marginal_utility_of_distance_per_m` bike **−0.000192308 utils/m** = −1/(`C.constraint.trip_length_km.bike` × 1000), swept over the survey years' 3.1–5.2 km; every other mode stays at 0.0 (the run's own `config.xml`).
- **A dense-zone car trip pays a derived parking search time** (§9.138): `A.parking.search_min_max` (8.1 min, Shoup 2006; swept 3.5–14) × the zone's `density_weight` ramp, once at arrival; same home exemption as the price (§9.31).
- **Bike availability is drawn** at `B.population.bike_available_rate` 0.493 (literature, CWANZ; swept 0.30–1.00), gated at `B.population.bike_min_age` 12 (assumed, swept 0–16; §9.84); `AvailabilityModesCalculator` strips bike from a person without one; boundary agents keep it (§9.39).
- **The calibration loop reaches bike** (§9.158): the movable set (5 → 21) includes `B.population.bike_min_age`, `A.gradient.bike_speed_floor_factor` and `A.gradient.bike_speed_ceiling_factor`.
- **`C.asc.cycle` is OPENED to a sweep and `C.asc.walk` is NOT** (§9.158, §9.214): `C.asc.cycle` −1.35 takes [−4.0, −1.35], CONSTRAINED against `C.constraint.trip_length_km.*`, never a share. `C.asc.walk` +0.35 stays FROZEN: walk's long trips trace to held-ride tours and car-less destinations (below), which a constant would absorb.
- **Short trips get their observed distribution** (§9.69, #30): a two-component gravity mixture per purpose; `B.activity.short_trip_mean_km` 0.7 derives from `C.constraint.trip_length_km.walk`, its weight solved to `B.activity.short_trip_band_share` (HTS Sydney 2012/13, 18.8 % up to 1 km; swept ±25 %).
- **F38's two demand changes aim at walk's and bike's geometry** (§9.214; [population-and-demand](population-and-demand.md)): `B.activity.escort_oneway_scope` = `cannot_drive` releases a one-way escort binding on a member who could drive (one-way tours 70,591 → 20,365 weekday), and `B.activity.destination_mobility` = `own_speed` sends the car-less to destinations at their own planning speed (car-less realised trips 10-25 % shorter per purpose).
- **A denied lift drives**: `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (§9.105); `walk` is the control member.

## What is measured

- **F39's control arm, a RESULT at iteration 250** (§9.219, `report_mode_ridership.py --run 20260929T072135_250it_25pct --it 250`): walk **10.0835 % against 13.4000 % (−24.7 %, STOP)** on **16,197** trips at a mean **3.75 km against 0.70** (`_fit.json` ratio 5.36), coverage **52.51 %**; bike **5.5021 % against 2.2084 % (+149.1 %, STOP)** on **8,838** trips at **7.54 km against 5.2**, coverage **23.12 %**. F38 and F37 (walk 4.08 km, §9.214) are a direction, never a comparison (§3.5).
- **Walk loses the short trips and wins the long ones** (§9.219, `mode_by_demographics.py`, `_mode_by_demographics.json`): trips under 1 km are **13.5 %** of residents' trips — walk's whole observed share — and **59.2 %** of them are driven, **15.7 %** walked; the car-available drive **75.9 %** and walk **7.6 %** of theirs. The car-less walk **44.5 %** under 1 km, **24.1 %** at 5–10 km and **14.0 %** over 20 km, beside ride 44–53 % (bound trips only) and pt 0–15 %.
- **The long walks are chosen, not routed** (§9.219, `_bound_trips.json`): in tours with no ride, chosen walks (`walk|walk`) are **26,721** trips at a mean **6.21 km**; pt requests answered by a walk (`walk|pt`) **10,903** at **2.00 km** — the no-route bound (§9.218) left the chosen walks where they were.
- **One-way escort bindings strand the tour they hold** (§9.214, item 2): residents' walk-only trips inside a held-ride tour are **25.0 %** of walk trips and **35.6 %** of walk km at a mean **11.1 km** — the car stays home with the escorted member's bound direction and the tour's other trips have walk, pt, bike or taxi only.
- **Destinations ignored mobility** (§9.214, item 3): the car-less (23.4 % of production) made **57 %** of bike trips at a mean **11.8 km** and walked a mean **6.0 km**; one kernel per purpose sent them as far as a driver.
- **Walk's long trips are not only routing fallbacks** (§9.214, item 5): walks chosen as walk run a median **2.8–3.1 km**; unpaired rides re-moded to walk are 277 an iteration. The no-route share fell to 52.1 % of pt requests with the access ceiling measured (§9.214, item 4; [public-transport-and-yardsticks](public-transport-and-yardsticks.md)).
- **The short-trip supply IS at the seed; the run reads it on another basis** (§9.177, #30): the seed's core legs are **17.70 %** at ≤ 0.748 km straight (1 km at detour 1.3376; `B2_activity_trips_WEEKDAY.csv`) against the Sydney 18.8 % band; car carried **51.5 %** of the routed short trips, walk **29.5 %** (`extract_metrics.trip_geometry`). The loss is allocation, not the kernel.
- **Walk is priced as a transit ride inside the pt router** (§9.158): one second walking costs 1.0400 seconds riding at `RUN.transit_router.direct_walk_factor` = 1.0; 28.5 % of answered pt requests on F37's arm 0 were beaten by the network walk (§9.214).
- **PT access walks executed on a result** (§9.169, #167, #183): 27,765 network walk legs (median 461 m) and no teleported leg; on F37's arm 0 **19.5 %** of resident rail entries walk more than 2 km to the station (§9.214).
- **The week trip rate** (§9.164, §9.214): 3.398 against the HTS 3.473 on F37's demand; **3.470** on F38's, as fewer tours overran the day. The sub-1 km share is the kernel's SHAPE; the HTS gives a mean and no distribution (§9.8, §9.13).

## What is open

- **Two mechanisms, one next family** (§9.219, #30): (1) the car-available drive three quarters of sub-kilometre trips — no car terminal time (the walk to and from a parked car, the parking manoeuvre) makes an 800 m drive cheap; (2) a car-less trip with no bound driver and no transit route has walk, bike or taxi only, so the long walk IS the choice. The lane's `short-trip-and-carless-choice` task designs both from observed inputs. Not represented: the pedestrian crossing WAIT and road links' foot=/bicycle= tags (§9.167).
- **No walk distance cost, on new evidence** (§9.219): held-ride tours (F38), car-less destinations (F38) and the no-route walk (F39) are all addressed and walk still runs 3.75 km; a distance term would shorten the car-less' walks by leaving them no alternative at all and would not move a single short car trip to foot — still a compensating constant.
- **Walk's router pricing has a NAMED mechanism and an undecided remedy** (§9.158): `RUN.transit_router.direct_walk_factor` has a sweep to 2.0; moving it is a family boundary and a FIDELITY decision, never picked to land walk's share.
- **#30 is re-aimed at allocation** (§9.177, user decision): the band shares match at the zone matrix (§9.142) and on placed coordinates (17.70 % vs 18.8 %).
- **The gradient channel's effect is unmeasured**: no paired arm differing only in `A.gradient.representation` has read bike's mean trip and time against 5.2 km / 19.2 min (§9.84).
- **#50** — the bike age gate is assumed; no mode × age cell is held (§9.84); it carries `decision-needed` and does not block the launcher (§9.160).
- **Walk detour**: main walk at the road graph's ~1.34 rather than the measured 1.6902 flatters walk slightly less than truth; stated, not corrected (§9.54).

## Refused — do not re-raise

- A per-trip feasibility bound on walk or bike in the replanner (§9.106): it cannot remove seeded behaviour. Held at 0.0.
- Tuning bike's own time rates against its excess (§9.123): the excess is the car-less quarter's missing alternatives.
- **Solving `C.asc.walk` against walk's share or its trip length** (§9.158, §9.214).
- **A walk distance cost** (§9.214, item 5; §9.219): the long walks are a missing alternative and the short ones a missing car cost.
- Bike as displaced ride, asserted without measurement (§9.114 corrected §9.109 and §9.112); §9.123 carries the measurement.
- A gradient utility term in scoring, or an access-decay curve: link speed is the representation (§9.84, §9.140, #21).
- Teleported walk or bike as main modes, re-added access/egress stubs, and the trunk-road pedestrian exclusion (§9.54, §9.58).

## History

- §9.219 — short trips driven; car-less walk
- §9.214 — long walks trace to demand
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
