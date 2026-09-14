# Light rail and ferry — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Two runs are results - F32's `20260909T015217_300it_25pct` and F35's arm 0 `20260912T202242_300it_25pct`, each `completion` `ran_to_last_iteration` at iteration 300 (§9.162, §9.169); nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 14 September 2026 (forty-eighth session) · **Record read through:** §9.171 · **Written against family:** `F35`

## What is built

**Light rail — the intervention (S2 and its variants).**

- Vehicle: `A.lightrail.capacity_total` = 270 (observed), `A.lightrail.capacity_seated` = 60 (assumed, sweep 50–80), `A.lightrail.capacity_standing` = 210 (derived); applied over the mapped fleet in `src/build/build_matsim_run_inputs.py`, the mapper never re-run (§9.18).
- Run time: `A.lightrail.line_speed_kmh` = 40 (measured ceiling, sweep 30–50), `A.lightrail.dwell_fixed_s` = 8 (assumed, sweep 5–15), `A.lightrail.corridor_speed_kmh` = 60 (assumed, sweep 40–70), `A.lightrail.tsp_enabled` false in S2 and true in S2b (§9.76, §9.77).
- Charging dwell: `A.lightrail.dwell_charging_s` per scenario — 20 s in `cities/newcastle/overlays/scenarios/S2.json`, S2b, S2c, S4 and S5; 0 s in S2a, the counterfactual — swept 10–35 s, `A.lightrail.dwell_sweep_grid` = [0, 10, 20, 35] (§4.3, §9.76).
- Native dwell: `src/build/build_charging_dwell_offsets.py` derives `transitSchedule_dwell.xml.gz` from each scenario's mapped schedule — departure = arrival + max(existing gap, resolved dwell), `awaitDeparture` on; charging is concurrent with boarding; the 12.00 min end-to-end anchor is unchanged (§9.76, §9.77).
- Supply: 252 tram departures on two routes in the mapped WEEKDAY schedule, equal to GTFS; route ids read SAT/SUN because pt2matsim names a grouped route after one trip — count departures, never route ids (§9.113).
- Target: the line's disclosed Opal series, 1,005,033 boardings over 2025-07 to 2026-06 = 2,754 a day, × `CAL.pt.weekday_factor` = 1.0727 (assumed, sweep 1.0–1.3) = 2,954 boardings per weekday; row `light_rail` of `cities/newcastle/data/processed/validation/mode_targets_by_mode.csv`, measured, sweep 2,754–3,580 (§9.130).
- Scoring: `src/analyse/report_mode_ridership.py` counts modelled boardings of every subpopulation × 1/fraction against that count; the composition-derived 0.6444% trip share is retired (§9.130).
- Fares: the tram on the published light rail table (0–3 km $3.30/$2.31), the ferry on the Stockton crossing's published row ($3.30/$2.31 adult), charged by `citysim.PtFareChargeHandler` with every other pt journey (§9.135).

**Ferry — the Stockton crossing.**

- Vehicle: `A.transit.ferry_capacity_total` = 200, `A.transit.ferry_capacity_seated` = 149 (literature), `A.transit.ferry_capacity_standing` = 51 (derived) (§9.30).
- Supply: 107 WEEKDAY departures on two routes, exact to GTFS; the same route-id trap applies (§9.113).
- Target: no Newcastle ferry patronage is published, so it is derived — the census G62 one-method ferry share within PT on the target LGA's cell (34 of 904) × the HTS PT level = 0.1429% of resident trips, sweep 0–0.2858% (§9.89, §9.122; row `ferry` of `mode_targets_by_mode.csv`).
- Router: `citysim.NetworkDirectWalkPtRouter` wraps SwissRailRaptor — routes the direct walk on the walk network, prices it by the raptor's rule × `RUN.transit_router.direct_walk_factor` = 1.0 (literature, sweep 1.0–2.0) and returns the cheaper of walk and transit; `RUN.transit_router.direct_walk_basis` = `network` (`beeline` recovers the stock raptor); config module `ptDirectWalk` (§9.121).
- Reach: `RUN.transit_router.search_radius_m` = 1000, `RUN.transit_router.extension_radius_m` = 200, `RUN.transit_router.max_beeline_walk_connection_m` = 300 (literature, §9.120). The radius cannot refuse a route: `DefaultRaptorStopFinder.findNearbyStops` falls back to the nearest stop plus the extension radius (§9.158).

**The constants, and what they can and cannot reach.**

- `C.asc.ferry` = −1.05, declared at §9.158 at the `asc_bus` value it inherited under `RUN.routing.pt_submode_scoring` = `per_submode` (§9.78), behaviour-neutral; sweep [−2.05, −0.05]. `C.asc.light_rail` = −0.75, sweep [−1.75, 0.25]. Half-width from `C.taxi.asc`'s 2.0-util sweep (§9.76); one util = 3.54 min in-vehicle. The §8.5 departure is logged at §9.158, before any run reads them.
- A PT constant is a PLAN-CHOICE lever, never a SUBMODE lever (§9.158, §9.130): `RaptorUtils.createParameters` prices travel time, waiting and a line switch only — no constant, fare or distance term. `C.asc.light_rail` moves pt against car, never tram against bus. The interval is a bracket, not a licence to fit (§8.5).
- The PT submodes can become plan-level alternatives (§9.164, #49): `pt` is one alternative in `RUN.mode_choice.modes` and the raptor picks the submode, so only 974 of 154,347 persons (0.63 %) ever held plans differing in submode (§9.160). `citysim.SubmodeRaptorProvider` builds one raptor per submode over a schedule FILTERED to its routes, each a plan-level routing module, behind `RUN.mode_choice.pt_submode_alternatives` (`aggregate` shipped; `alternatives`). It filters the schedule, not the answer.
- Its cost (§9.164): under `alternatives` bus-then-train is unrepresentable, so the arm that spends it must read multi-leg pt trips on both sides, hence `aggregate` ships. Seeded `pt` legs are rewritten to `RUN.mode_choice.pt_submode_seed` (`bus`), counted in the log.
- The corridor builder reads the tram's values from the registry (§9.170): `A.lightrail.capacity_seated` 60 / `capacity_standing` 210, `line_speed_kmh` 40 and `dwell_fixed_s` 8.0 (sweep 5–15), replacing second copies in `build_corridor_layers.py`; the A4 dwell model's sweep column moved 12 → 15 and no value changed.

## What is measured

- **The ferry's first disclosed observation is a pair of bounds** (§9.167, #185): TfNSW's daily Opal Patronage files (427 days, `extract_opal_patronage.py`) put ferry tap-ons at the Newcastle wharf at **234–1,347 a weekday**, every hourly cell rounded to 100 or printed `<100` (`CAL.pt.opal_patronage_rounding`). Light rail reads **2,090–3,751**, bracketing the 2,954 target. A constraint, never a target (§9.8): the 0.1429 % ferry share stands.
- **The ferry's market is there and the mode is not chosen** (§9.163, #94). `corridor_market.py --mode ferry --radius-m 1000` on `20260909T015217_300it_25pct`: **84,293 of 2,343,637** weekday trip ends within 1 km of a wharf — **3.60 %** — against **5.18 %** of POI attraction weight and **5.12 %** of jobs: the order the attraction layer implies.
- **Not a choice-set bound either** (§9.163): ferry rides on the single `pt` alternative, coverage **25.78 %** of agents against pt submode targets summing to 2.52 %, so its **−60.1 %** is neither a missing market nor an unreachable target. Live candidates: the router never offering it (#162: 31.09 % of pt requests find no route), the plan evicted from memory (#174), and `C.asc.ferry`, `placeholder` and outside the movable set.
- **THE F35 RESULT** (`20260912T202242_300it_25pct`, iteration 300, `ran_to_last_iteration`, §9.169): light rail **772 boardings a weekday against 2,954, −73.9 %, STOP** (193 sampled); ferry **0.0524 % against 0.1429 %, −63.3 %, STOP** (83 trips); heavy rail **10,092 against 6,529 (+54.6 %)**, bus 2.0045 % (−15.8 %); pt choice-set coverage **17.53 %** (F32 25.78 %); **752** pt trips board more than one submode. Not a comparison with F32 (§3.5) but a direction: light rail moved AWAY (F32 −58.6 %) when the pt access leg became a network walk (§9.167).
- **Arm 0's light rail sits below the disclosed lower bound** (§9.169, #185): 772 against the **2,090–3,751** weekday tap-on bracket (§9.167) — a constraint breached, not a target missed by a margin. The ferry's 234–1,347 bracket stays a constraint, never a target (§9.8).
- **The reader read every run through the city's current schedule until §9.169**: `extract_metrics._schedule_index` opened the config's path under `scenarios/matsim/S2/WEEKDAY/`, overwritten by the F34 footpath rebuild, so the F32 result's 22,769 transit legs resolved 22,487 to no stop name and the board printed heavy rail **0 / −100.0 %**. Fixed: the run's own `output/output_transitSchedule.xml.gz` is read first, `SCHEDULE_SOURCE` recorded.
- **The F32 RESULT** (`20260909T015217_300it_25pct`, iteration 300, `ran_to_last_iteration`): light rail **1,224 boardings against 2,954, −58.6 %** through its own schedule (§9.169; §9.162 recorded 1,260 / −57.3 %); ferry **0.0571 % against 0.1429 %, −60.1 %**. Light rail moved AWAY across the run — 2,720 boardings at iteration 0, 1,436 at 200 (§9.162) — so the DIRECTION is the finding. Comparable with no earlier family (§3.5).
- Supply is ruled out on departures: 252 a weekday; §9.103's "550 trips a day" was an unfiltered GTFS count, superseded with the conclusion unchanged (§9.113).
- The pre-pandemic V001/V002 count (3,417 boardings a day, 2019–20) is unscorable in `src/calibrate/fit.py`; no error is quoted against it (§9.80, #84).

## What is open

- **Three of the six stop modes are split by a router that reads no submode constant** (§9.169): light rail −73.9 %, heavy rail +54.6 % and ferry −63.3 % on arm 0 are decided inside the raptor (§9.158). `C.raptor.mode_cost_representation` = `absent` is built and unrun, so the routers pair is the recommended next arm; none was launched, the user's decision, and it needs its own stated-cost approval (§9.169).
- Light rail: where the boardings between arm 0's 772 and the 2,954 target are — longer corridor trips, rail transferees, visitors — is the question at the next arm (§9.130, §9.169).
- **A third of all PT routing finds no service** (§9.158): of **2,553,357** pt routing requests on the F31 arm, **33.4 %** got no transit route and **40.6 %** of the answered took the network walk — **60.5 %** came back as a walk, because `(marginalUtilityOfTraveling − performing)/3600` prices a second walking at 1.0400 seconds riding. A tram or ferry leg cannot be chosen inside a journey answered with a walk. Supply, radius and schedule integrity are exonerated (§9.113; 1,270 routes with 0 lacking departures, §9.158).
- #94 (awaiting-run) — supply, hour of service and routing are exonerated (§9.140); the residual is the reach bound (three quarters of the market beyond the 1 km walk radius, no feeder) and a competitive-but-losing plan the memory drops; arm 0 read −63.3 % (§9.169) and the routers pair next measures it.
- The ferry target's vintage: the census cell is a lockdown month, which is why the sweep runs from 0 to twice the point value (§9.89).
- The seated/standing split of the Urbos stays assumed; the acquisition route is field observation at Civic or Crown Street, or GTFS-Realtime dwell distributions (§4.3, §9.18).

## Refused — do not re-raise

- **Switching on transit signal priority to close light rail's shortfall** (§9.156): `A.lightrail.tsp_enabled` has `sweep_role` `answer` and IS the S2b intervention, the 38 % corridor swing S2b measures (`cities/newcastle/registry/E_scenario.json`); on in the base it is the compensating constant GOAL loop step 3 forbids.
- **The FIDELITY question underneath it is real, is NOT this, and is open** (§9.156): `A.lightrail.tsp_enabled` is `source: assumed`; whether the corridor operates signal priority today is settled with evidence about the corridor, never with the scoreboard deficit (−73.9 % at F35's arm 0, §9.169).
- Lowering the light rail target on the corridor-market measurement: the market is modelled, and that would fit the yardstick to the answer (§9.103, §9.92).
- Quoting a light rail error against the 2019–20 V001/V002 boardings: pre-pandemic and unscorable (§9.80, #84).
- Rebuilding the schedule because tram and ferry route ids read SAT/SUN: the departures are present and exact (§9.113).
- Choosing a standing capacity without a published figure: closed by published figures only (§9.18, §9.30).
- Re-running pt2matsim to produce a per-scenario dwell schedule: it is derived from the mapped schedule (§3.5, §9.76).
- Reading charging dwell as additive to boarding dwell: double-counts boarding (§9.76).
- Naming the ferry's residual cause before measuring it: three asserted mechanisms were committed in one session and refuted (§9.112, #94).
- A light rail mode constant to move the ROUTER: the raptor's parameters carry no constant, fare or distance term (§9.130, §9.158); `C.asc.light_rail` changes pt-against-car, never tram-against-bus.
- **Solving `C.asc.light_rail` against light rail's own target** (§8.5, §9.158): it would fit away the effect the study measures; the sweep is a bracket and the ASC loop a two-round CONTRACTION TEST, not a solve.
- Counting ferry or tram trips off `main_mode`: a public-transport trip carries `pt`; submodes come from the legs table (§9.112).

## History

- §9.170 — corridor builder reads registry tram values
- §9.169 — arm 0: light rail −73.9 %, ferry −63.3 %
- §9.167 — ferry's first observation, as bounds
- §9.166 — tsp bullet re-aimed at −57.3 %
- §9.164 — pt submodes get a plan-level control
- §9.163 — ferry market present at 3.60 %
- §9.162 — first result: light rail −57.3 %
- §9.158 — ferry constant declared; raptor prices no constant
- §9.157 — F31 gate: light rail −47.2 %, ferry −65.6 %
- §9.156 — tsp refused as a lever
- §9.142 — corridor gets its arrivals
- §9.140 — ferry market and memory measured
- §9.139 — F23 gate: both unmoved
- §9.136 — corridor deficit structural by band
- §9.134 — F21 gate: tram away, ferry flat
