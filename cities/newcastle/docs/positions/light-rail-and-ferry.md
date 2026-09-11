# Light rail and ferry — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. The depth arm `20260909T015217_300it_25pct` IS a result - `completion` `ran_to_last_iteration` at iteration 300 (§9.162), the first since family F4; nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 10 September 2026 (forty-first session) · **Record read through:** §9.164 · **Written against family:** `F33`

## What is built

**Light rail — the intervention (S2 and its variants).**

- Vehicle: `A.lightrail.capacity_total` = 270 (observed, the published Urbos 100 maximum), `A.lightrail.capacity_seated` = 60 (assumed, sweep 50–80), `A.lightrail.capacity_standing` = 210 (derived, total minus seated); applied over the already-mapped fleet in `src/build/build_matsim_run_inputs.py`, the mapper never re-run (§9.18).
- Run time: `A.lightrail.line_speed_kmh` = 40 (measured ceiling, the regulated corridor speed; sweep 30–50), `A.lightrail.dwell_fixed_s` = 8 (assumed, sweep 5–15), `A.lightrail.corridor_speed_kmh` = 60 (assumed, sweep 40–70), `A.lightrail.tsp_enabled` false in S2 and true in S2b (§9.76, §9.77).
- Charging dwell: `A.lightrail.dwell_charging_s` is set per scenario — 20 s in `cities/newcastle/overlays/scenarios/S2.json`, S2b, S2c, S4 and S5; 0 s in S2a, which is the counterfactual by definition — swept 10–35 s, with `A.lightrail.dwell_sweep_grid` = [0, 10, 20, 35] (§4.3, §9.76).
- Native dwell: `src/build/build_charging_dwell_offsets.py` derives `transitSchedule_dwell.xml.gz` from each scenario's own mapped schedule; every intermediate stop holds departure = arrival + max(existing gap, resolved dwell) with `awaitDeparture` on; charging is concurrent with boarding, not additive, and the 12.00 min end-to-end anchor is unchanged by construction (§9.76, §9.77).
- Supply: the mapped WEEKDAY schedule carries 252 tram departures on two routes, equal to the GTFS weekday count; the route ids are tagged SAT/SUN because pt2matsim names a grouped route after one representative trip — count departures, never route ids (§9.113).
- Target: the line's own disclosed Opal series, 1,005,033 boardings over 2025-07 to 2026-06 = 2,754 a day, × `CAL.pt.weekday_factor` = 1.0727 (assumed, sweep 1.0–1.3) = 2,954 boardings per weekday, all travellers; row `light_rail` of `cities/newcastle/data/processed/validation/mode_targets_by_mode.csv`, status measured, sweep 2,754–3,580 (§9.130).
- Scoring: `src/analyse/report_mode_ridership.py` counts modelled boardings of every subpopulation × 1/fraction against that count; the composition-derived 0.6444% trip share it replaces is retired (§9.130).
- Fares: both modes are priced from §9.135 — the tram on the published light rail table (0–3 km $3.30/$2.31), the ferry on the Stockton crossing's own published row ($3.30/$2.31 adult) — charged by `citysim.PtFareChargeHandler` with every other pt journey (§9.135).

**Ferry — the Stockton crossing.**

- Vehicle: `A.transit.ferry_capacity_total` = 200, `A.transit.ferry_capacity_seated` = 149 (literature), `A.transit.ferry_capacity_standing` = 51 (derived) (§9.30).
- Supply: 107 WEEKDAY departures on two routes, exact to GTFS; the same route-id trap applies (§9.113).
- Target: no Newcastle ferry patronage is published, so the target is derived — the census G62 one-method ferry share within public transport on the target LGA's cell (34 of 904 PT journeys) scaled by the HTS PT level = 0.1429% of resident trips, status derived, sweep 0–0.2858% (§9.89, §9.122; row `ferry` of `mode_targets_by_mode.csv`).
- Router: `citysim.NetworkDirectWalkPtRouter` (`src/java/citysim/NetworkDirectWalkPtRouter.java`) wraps SwissRailRaptor — the raptor answers with its best transit route, the wrapper routes the direct walk on the walk network, prices it by the raptor's own rule × `RUN.transit_router.direct_walk_factor` = 1.0 (literature, sweep 1.0–2.0), and returns the cheaper; `RUN.transit_router.direct_walk_basis` = `network` (derived; `beeline` recovers the stock raptor exactly); registered as the `ptDirectWalk` config module (§9.121).
- Reach: `RUN.transit_router.search_radius_m` = 1000, `RUN.transit_router.extension_radius_m` = 200 and `RUN.transit_router.max_beeline_walk_connection_m` = 300, declared literature values that had reached every config as undeclared jar defaults (§9.120). **The radius cannot by itself refuse a route** (§9.158): `DefaultRaptorStopFinder.findNearbyStops` falls back to the nearest stop plus the extension radius when fewer than two are inside, verified in the pinned jar.

**The constants, and what they can and cannot reach.**

- **`C.asc.ferry` DID NOT EXIST until §9.158.** Ferry is a scored pt submode under `RUN.routing.pt_submode_scoring` = `per_submode` (§9.78) and it silently inherited `asc_bus`, so the run-input report stated an inheritance rather than a declared value. It is now declared at −1.05 — the inherited value, so creating it is behaviour-neutral — with a sweep [−2.05, −0.05]. `C.asc.light_rail` −0.75 moves from `held_fixed` to [−1.75, 0.25]. Half-width derived two ways: `C.taxi.asc` (§9.76) is the registry's only other mode-ASC sweep at 2.0 utils wide, and one util is 3.54 minutes of in-vehicle time at this model's own scale. **The §8.5 departure for both is logged at §9.158, before any run reads them.**
- **A PT constant is a PLAN-CHOICE lever and never a SUBMODE lever** (§9.158, §9.130). SwissRailRaptor's cost carries **no mode constant, no fare and no distance term** — `RaptorUtils.createParameters` prices travel time, waiting and a line switch and nothing else, read out of the pinned jar. So `C.asc.light_rail` can make a person choose pt over car; it cannot make the raptor choose the tram over the bus. **The interval is a BRACKET, not a licence to fit**: light rail is the mode the intervention runs through, and §8.5's refusal binds hardest here.

- **THE PT SUBMODES CAN BECOME PLAN-LEVEL ALTERNATIVES** (§9.164, #49). `RUN.mode_choice.modes` offers `pt` as ONE alternative and the raptor picks the submode downstream, which is why only **974 of 154,347 persons (0.63 %)** ever held plans differing in submode (§9.160) - so a scoring constant reallocates between bus, rail, tram and ferry for under one per cent of the population, and light rail's -57.3 % against heavy rail's +225.0 % is decided in a layer with almost no control. `citysim.SubmodeRaptorProvider` builds one SwissRailRaptor per submode over a schedule FILTERED to that submode's own routes and binds each as a plan-level routing module, behind `RUN.mode_choice.pt_submode_alternatives` (`aggregate` shipped; `alternatives`). It filters the SCHEDULE and not the ANSWER on purpose: refusing an itinerary because it used the wrong submode would report a submode as infeasible exactly where it competes hardest.
- **What turning it on COSTS is stated, not hidden** (§9.164): under `alternatives` the umbrella leaves the choice set, so no single plan-level trip can combine two submodes and a bus-then-train journey is no longer representable. **The arm that spends it must read multi-leg pt trips on both sides**, which is why the gate ships at `aggregate`. Seeded `pt` legs are rewritten to `RUN.mode_choice.pt_submode_seed` (`bus`) with a count in the log, because a seeded subtour on a mode outside the choice set is the absorbing state `RUN.mode_choice.modes` already records for `ride`.

## What is measured

- **THE FERRY'S MARKET IS THERE AND THE MODE IS NOT CHOSEN** (§9.163, #94). `corridor_market.py --mode ferry --radius-m 1000` on `20260909T015217_300it_25pct` (2 stop points): **84,293 of 2,343,637** modelled weekday trip ends within 1 km of a wharf — **3.60 %** — against an observed **5.18 %** of POI attraction weight and **5.12 %** of jobs, and by purpose shopping 7.59 %, other 5.86 %, work 4.84 %. Food POI weight is **11.88 %** within the same radius. So the demand builder has put trips near the wharves at the same order as the attraction layer implies, not the near-zero the "20 km road detour" framing suggested.
- **And it is not a choice-set bound either** (§9.163). Ferry rides on the single `pt` alternative, whose coverage is **25.78 %** of agents, against pt submode trip-share targets summing to 2.52 %. Ferry's **−60.1 %** (0.0571 % against 0.1429 %) is therefore neither a missing market nor an unreachable target: agents with a wharf at both ends are not choosing it. The three live candidates are the router never offering it (#162: 31.09 % of pt requests find no route), the plan being evicted from memory (#174), and `C.asc.ferry`, which is `placeholder` and outside the movable set.
Every arm below was stopped at or before its gate; these are readings, not results.

**Both modes, at the newest citable reading.**

- **The first RESULT** (`20260909T015217_300it_25pct` at iteration 300, `ran_to_last_iteration`, §9.162): light rail **1,260 boardings against 2,954, −57.3 %**; ferry **0.0571 % of resident trips against 0.1429 %, −60.1 %**. **Light rail moved AWAY across the whole run** - 2,720 boardings at iteration 0, 1,436 at 200, 1,260 at 300 - so depth did not help it and the DIRECTION is the finding. Comparable with no earlier family (§3.5); F31's gate read −47.2 % and −65.6 % at iteration 100 (§9.157) and is not differenced against this.
- **The ASC fixed point PROPOSES a step for both, and it has NOT been run** (§9.158, `src/calibrate/asc_fixed_point.py`). Read off that gate at `CAL.asc.damping` 0.6: **ferry +0.6713 (to −0.3787)** and **light_rail +0.4143 (to −0.3357)**, both inside their declared sweeps and both under the `CAL.asc.max_step_utils` 1.5 refusal bound. The light-rail row is marked `basis_is_boardings`: the logit inversion is exact for a share and only a monotone proxy for a boardings target, and the contraction verdict is reported with and without it. **The test is whether |Δasc| SHRINKS between round 1 and round 2**, not whether the shares move — contraction means the residual is taste, no contraction means it is mechanism and no constant will ever close it.

**Light rail.**

- F23 arm `aborted_20260901T165115_300it_25pct`, the iteration-100 gate: 2,056 → 1,000 boardings a weekday over iterations 0–100 against 2,954 — −66.1% and AWAY on its own trend, unmoved by any of the three behaviour channels (§9.139). The F22 gate read 860 under flat fares (§9.136); the F21 gate 780 on the 10% sample (§9.134).
- **The corridor deficit is structural in the home-anchored distance bands** (§9.136, #30): on the rebuilt demand the corridor share of shopping ends RISES with trip distance — 5.01% under 1 km, 6.04% at 1–3, 6.78% at 3–8, 9.77% beyond 8 km against the 11.38% attraction share (other: 4.31 → 7.11% against 8.07%); only 1.72% of population lives within 800 m of a tram stop. With decay calibrated to the observed HTS means (realised = target per purpose, `_activity_chains_report.json`), a size × distance gravity cannot reach the corridor's attraction share; the two derivable repairs are floorspace-weighted attraction from the harvested OSM building footprints, or a declared agglomeration term (§9.136).
- Supply is ruled out on departures: 252 a weekday carry 28 corridor trips; §9.103's "550 trips a day" was an unfiltered GTFS count and §9.113 supersedes it, with the conclusion unchanged (§9.113).
- Out of reach, not out-competed: at iteration 100 of `20260829T172145_1000it_10pct`, 1.063% of all trips (2,350) had both ends within 800 m of a stop; of those, 28 chose light rail, 1,010 car and 928 walk; the mean modelled tram leg is 1.60 km (§9.103).
- Corridor market against observation (`src/analyse/corridor_market.py`): work ends are placed where the jobs are (8.80% of work ends vs 8.04% of jobs within 800 m); shopping and other ends at roughly two-thirds of the observed attraction rate (6.84% vs 11.38%; 5.69% vs 8.07%); the home end is only 1.7–2.3% corridor, so a two-ended corridor market is small even at observed rates (§9.120, #30).
- Not the tram's cause, F19 iteration 20: the Interchange transfer works (rail-to-tram walk 54–58 m; 44 of 74 CBD-bound rail alighters take the tram; 16 tram vs 8 bus departures to the CBD in 07–09); the corridor-internal market of 1,127 trips has a mean beeline of 500 m and goes car 59% and walk 27% — a tram cannot beat a 500 m walk, and a mode constant is invisible to the raptor (§9.130).
- The pre-pandemic V001/V002 count (3,417 boardings a day, 2019–20) is marked unscorable in `src/calibrate/fit.py` and no error is quoted against it (§9.80, #84).

**Ferry.**

- F23 iteration 100 (the gate): 0.0286% of resident trips against 0.143% (−80.0%), flat at 0.02–0.03% across the arm — untouched by all three behaviour channels, as by the fare before them (§9.139, #94). F22's gate read 0.0285% (§9.136); F21's 0.027% (§9.134).
- The market, by bank: B2 generates 4,956 harbour-crossing trips a weekday (0.211% of all trips) by 2,593 persons; 7,490 residents live on the Stockton side; 59,458 WEEKDAY trip ends lie within 1,000 m of the two wharves (§9.121, §9.120).
- **The F23 gate's crossings, re-measured by bank** (§9.140, #94): 790 peninsula-to-south-side trips by 413 persons at iteration 100 — car 495, pt 129 (84 with a ferry leg), ride 95, walk 31, bike 15, truck 12, taxi 11; the derived target needs ~28% of that market and the ferry carries ~11%. Hour of service is not it (04:55–23:05, ~9% of crossings outside it). Only 205 of 790 crossings have both ends within the raptor's 1 km search radius, and the peninsula has no bus stop or line in the mapped schedule; in that near-wharf market the split is car 124 / pt 41 / ride 27 / walk 9 (§9.140).
- **The ferry plan is competitive and then forgotten** (§9.140): 270 of the 413 crossing persons hold no pt plan at all at iteration 100; 100 hold a ferry plan and 62 select it; where a ferry plan exists and loses it trails by a median 2.8 utils (p25 −68.7, p75 +0.2). The seeded choice set decays under innovation for every mode — see [seed-and-choice-set](seed-and-choice-set.md).
- The defect: the raptor's direct walk was a beeline across the harbour that the network executed as the ~20 km road detour; on F16 iteration 10, 174 of 256 crossing trips in residents' pt plans were walk-only (median 19.4 km) and 38.3% of all residents' pt-plan trips were walk-only (§9.121).
- After the repair, F17 arm `20260830T141222_300it_10pct`, iteration 10: 209 of 359 crossing trips routed with a ferry leg (58%), walk-only down to 17%; realised ferry 30 trips, 0.048% against the then-target 0.1013%, from 3 trips on F16; the remaining walk-only crossings are trips at hours the ferry does not run (§9.121).
- Before the repair, at iteration 100 of the committed arm: 450 trips with crow-fly under 3 km and road distance over 12 km took the detour, 118 of them on foot and 3 by public transport (§9.112).

## What is open

- Light rail: where the missing ~1,400 boardings a weekday are — longer corridor trips, rail transferees, visitors — is the mode's question at the next gate (§9.130, §9.157).
- **A THIRD OF ALL PT ROUTING FINDS NO SERVICE, AND THAT NOW BEARS ON BOTH MODES** (§9.158). Over **2,553,357** pt routing requests on the F31 arm, **33.4 %** got no transit route at all and **40.6 %** of the answered took the network walk — **60.5 % of every pt routing request came back as a walk**, because `(marginalUtilityOfTraveling − performing)/3600` prices **one second walking at 1.0400 seconds riding**. A tram or ferry leg cannot be chosen inside a journey the router answered with a walk. Supply, radius and schedule integrity are all exonerated (252 tram and 107 ferry weekday departures, §9.113; 1,270 routes with 0 lacking departures, §9.158), so this is the first mechanism proposed for either shortfall that is neither pricing-of-the-mode nor demand.
- **#30 is repaired at the demand level** (§9.142). The deficit had survived two rebuilds unchanged (shopping 0.59x, other 0.69x, work 1.09x of the attraction share, §9.136) and was measured structural: a size x distance gravity constrained only at the ORIGIN end cannot concentrate arrivals the way an agglomeration does, at any decay. Destination choice is now constrained at the destination end too, and the CBD SA2 receives its own attraction share of non-home weekday core trip ends: **work 1.02x, shopping 0.99x, other 0.99x**, education 0.91x. Shopping is the one purpose whose WORST-ZONE gap does not reach the declared tolerance (0.37 against 0.01, the inner cap binding in all three passes): one destination multiplier cannot match the column shares of a two-component mixture, and a multiplier per component is the next demand lane (§9.142). Whether that reaches the tram is the F24 gate's reading, not a claim this page makes: the corridor's stops are a subset of the CBD and the mode still has to be chosen.
- #94 (awaiting-run) — supply, hour of service and routing are exonerated (§9.140); the residual is the reach bound (three quarters of the market beyond the 1 km walk radius with no feeder — a declared, swept field, not a constant to guess) and a competitive-but-losing plan the memory drops; the next gate reads the near-wharf split on the F24 package (§9.140).
- The ferry target's vintage: the census cell is a lockdown month, which is why the sweep runs from 0 to twice the point value (§9.89).
- Both modes have now been re-read at three successive gates (F21 §9.134, F22 §9.136, F23 §9.139) and moved no closer under any repair; the corridor attraction (#30) and the ferry's residual (#94) stand as the causes to attack, and neither is a pricing or behaviour-channel question.
- The seated/standing split of the Urbos stays assumed; the acquisition route is field observation at Civic or Crown Street, or GTFS-Realtime dwell distributions (§4.3, §9.18).

## Refused — do not re-raise

- **Switching on transit signal priority to close light rail's shortfall** (§9.156). The fifth assessment ranked it as "the shortest distance in the factor ledger between existing code and a number on the board" — light rail is the only pt mode below target and `TramPriorityConfigGroup` is written and registered with `A.lightrail.tsp_enabled` false. That is exactly why it must not be done: the field's `sweep_role` is `answer` and it IS the S2b intervention, the 38 % corridor swing S2b exists to measure (`cities/newcastle/registry/E_scenario.json`). Turning it on in the base would put the intervention inside the base, destroy the S2/S2b comparison, and close a gap with the very compensating constant GOAL loop step 3 forbids.
- **The FIDELITY question underneath it is real, is NOT this, and is open** (§9.156). `A.lightrail.tsp_enabled` is `source: assumed`, and GOAL requirement 6 says an unobtained value is derived rather than assumed. Whether the Newcastle corridor actually operates signal priority today is a question about the real world; if it does, the S2 base is wrong and S2b is mis-specified. It is the board's standing operator decision and it is settled with evidence about the corridor, never with the deficit on the scoreboard (−30 % when this was written, −57.3 % at the landed result).


- Lowering the light rail target on the corridor-market measurement: the market is modelled, and that would fit the yardstick to the answer (§9.103, §9.92).
- Quoting a light rail error against the 2019–20 V001/V002 boardings: pre-pandemic and unscorable (§9.80, #84).
- Rebuilding the schedule because tram and ferry route ids read SAT/SUN: the departures are present and exact (§9.113).
- Choosing a standing capacity for any vehicle without a published figure: closed by published figures, never by a number chosen here (§9.18, §9.30).
- Re-running pt2matsim to produce a per-scenario dwell schedule: it is derived from the mapped schedule (§3.5, §9.76).
- Reading charging dwell as additive to boarding dwell: double-counts boarding (§9.76).
- Naming the ferry's residual cause before measuring it: three asserted mechanisms reached committed entries in one session and were refuted (§9.112, #94).
- A light rail mode constant to move the ROUTER: SwissRailRaptor chooses on time, waiting and line-switch cost, and its parameters carry no constant, no fare and no distance term at all (§9.130, §9.158 verified in the pinned jar). Opening `C.asc.light_rail` changes pt-against-car, never tram-against-bus.
- **Solving `C.asc.light_rail` against light rail's own patronage target** (§8.5, §9.158): that would fit away the very effect the study exists to measure. The sweep is a bracket and the ASC loop is a two-round CONTRACTION TEST, not a solve.
- Counting ferry or tram trips off `main_mode`: a public-transport trip carries `pt`; submodes come from the legs table (§9.112).

## History

- §9.164 — the pt submodes get a plan-level control
- §9.163 — the ferry market is present at 3.60 %; the mode is not chosen
- §9.158 — a ferry constant declared, light rail's opened; the raptor prices no constant
- §9.162 — the first result: light rail −57.3 %, moving away
- §9.157 — the F31 gate: light rail −47.2 %, ferry −65.6 %
- §9.156 — tsp refused as a lever; the fidelity question separated
- §9.142 — the corridor gets its arrivals: destination choice constrained at both ends
- §9.140 — ferry market and memory measured
- §9.139 — F23 gate: both unmoved again
- §9.136 — corridor deficit structural by band
- §9.134 — F21 gate: tram away, ferry flat
- §9.131 — licence rebuild pending; F21 next
- §9.130 — disclosed boardings target 2,954
- §9.122 — ferry target moves to LGA cell
- §9.121 — network direct walk repairs ferry
- §9.120 — corridor market measured; router reach declared
