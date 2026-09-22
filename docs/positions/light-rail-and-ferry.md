# Light rail and ferry — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 22 September 2026 (sixty-first session) · **Record read through:** §9.211 · **Written against family:** `F35`

## What is built

- **Mumbai's metro target is the operators' observed daily ridership** (§9.210): MMRDA's OGD daily series for Lines 2A/7 (628 days) and the Monorail (356), imported from the user's logged-in browser, plus the Economic Survey's Line 1, 3 and Navi Mumbai averages - 906,988 a weekday of the CTS's 35.4 M trips, **2.5597 %** (sweep 2.3634–2.6283; the 2017 split gave 1.166 %; `mode_targets_by_mode.csv`).

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
- **The ferry's cross-harbour market is small and the ferry takes a sixth of it** (§9.177, #94, `_near_wharf.json` on `20260915T000704_250it_25pct`, `measure_near_wharf.py`): **305** resident trips (**0.19 %**) have both ends within `RUN.transit_router.search_radius_m` of two DIFFERENT wharves; ferry **15.7 %** of them, car 51.8 %; boardings scale to **1,148 a weekday**, inside the 234–1,347 tap-on bound; the scoring pair `20260916T063903_250it_25pct` reads 304 trips, ferry 16.1 %, 1,236 boardings (§9.177). §9.163's one-wharf market (3.60 %) counted trips that need no ferry.
- **THE ROUTERS PAIR, F35's second result** (`20260915T000704_250it_25pct`, iteration 250, `ran_to_last_iteration`, §9.176; `C.raptor.mode_cost_representation` = `mode_constant`, against arm 0 inside F35): light rail **856 boardings against 2,954, −71.0 %, STOP** (arm 0 772); ferry **0.0473 %, −66.9 %, STOP** (arm 0 0.0524); heavy rail **10,476, +60.5 %** (arm 0 10,092); bus −12.3 %; pt coverage **15.78 %** (arm 0 17.53). The raptor's constants move 84 boardings onto the tram and 384 onto the train: the split is NOT the router's constants; the tram sits below its 2,090–3,751 bracket (#185).
- **ARM 0, F35's first result** (`20260912T202242_300it_25pct`, iteration 300, `ran_to_last_iteration`, §9.169): light rail **772 boardings a weekday against 2,954, −73.9 %, STOP** (193 sampled); ferry **0.0524 % against 0.1429 %, −63.3 %, STOP** (83 trips); heavy rail **10,092 against 6,529 (+54.6 %)**, bus 2.0045 % (−15.8 %); pt choice-set coverage **17.53 %** (F32 25.78 %); **752** pt trips board more than one submode. Not a comparison with F32 (§3.5) but a direction: light rail moved AWAY (F32 −58.6 %) when the pt access leg became a network walk (§9.167).
- The pre-pandemic V001/V002 count (3,417 boardings a day, 2019–20) is unscorable in `src/calibrate/fit.py`; no error is quoted against it (§9.80, #84).

## What is open

- **The routers control is run and exonerated** (§9.176): giving the raptor the submode constants (`C.raptor.mode_cost_representation` = `mode_constant`) leaves light rail at −71.0 % against −73.9 %, heavy rail at +60.5 % against +54.6 % and ferry at −66.9 % against −63.3 % — inside the noise of two runs of one build (§9.142, #163). What decides the split is still open: the crowding control (`C.crowding.representation` `absent`, never run, #174), the service-quality pair (#175), the seed (pt coverage 15.78–17.53 %, §9.176), or the demand's placement of pt trips (#30).
- Light rail: where the boardings between arm 0's 772 and the 2,954 target are — longer corridor trips, rail transferees, visitors — is the question at the next arm (§9.130, §9.169).
- **A third of all PT routing finds no service** (§9.158): of **2,553,357** pt routing requests on the F31 arm, **33.4 %** got no transit route and **40.6 %** of the answered took the network walk — **60.5 %** came back as a walk, because `(marginalUtilityOfTraveling − performing)/3600` prices a second walking at 1.0400 seconds riding. A tram or ferry leg cannot be chosen inside a journey answered with a walk. Supply, radius and schedule integrity are exonerated (§9.113; 1,270 routes with 0 lacking departures, §9.158).
- **#94 — D8 is BUILT: the ferry is scored against its disclosed tap-ons** (§9.211): `build_mode_targets.py` reads the TPA daily Opal series over **300 weekdays**, taking each day's midpoint between its published bounds (hourly cells rounded to 100, so a day is an interval, never a point) — **790.285 boardings per weekday**, `measured`, sweep **234–1,347**, on the boardings basis the rail targets use. The census G62 lockdown cell (§9.89) is superseded. A BASIS change: the next reading is an error statistic against an observation. The reach mechanism stays open on #94.
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

- §9.211 — the ferry target on its tap-ons
- §9.169 — F32 result: light rail −58.6 %
- §9.210 — the Java fold; the metro target
- §9.177 — cross-harbour market 305 trips; D8
- §9.176 — the routers pair: tram 856, ferry −66.9 %
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
