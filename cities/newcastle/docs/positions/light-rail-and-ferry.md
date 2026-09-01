# Light rail and ferry — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 1 September 2026 · **Record read through:** §9.136 · **Open family:** F22

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
- Reach: `RUN.transit_router.search_radius_m` = 1000, `RUN.transit_router.extension_radius_m` = 200 and `RUN.transit_router.max_beeline_walk_connection_m` = 300, declared literature values that had reached every config as undeclared jar defaults (§9.120).

## What is measured

Every arm below was stopped at or before its gate; these are readings, not results.

**Light rail.**

- F22 arm `aborted_20260831T165127_300it_25pct`, the iteration-100 gate: 2,048 → 860 boardings a weekday over iterations 0–100 against 2,954 — −70.9% and AWAY on its own trend, under fares as it was free (§9.136). The F21 gate read 780 at its own iteration 100 on the 10% sample (§9.134).
- **The corridor deficit is structural in the home-anchored distance bands** (§9.136, #30): on the rebuilt demand the corridor share of shopping ends RISES with trip distance — 5.01% under 1 km, 6.04% at 1–3, 6.78% at 3–8, 9.77% beyond 8 km against the 11.38% attraction share (other: 4.31 → 7.11% against 8.07%); only 1.72% of population lives within 800 m of a tram stop. With decay calibrated to the observed HTS means (realised = target per purpose, `_activity_chains_report.json`), a size × distance gravity cannot reach the corridor's attraction share; the two derivable repairs are floorspace-weighted attraction from the harvested OSM building footprints, or a declared agglomeration term (§9.136).
- Supply is ruled out on departures: 252 a weekday carry 28 corridor trips; §9.103's "550 trips a day" was an unfiltered GTFS count and §9.113 supersedes it, with the conclusion unchanged (§9.113).
- Out of reach, not out-competed: at iteration 100 of `20260829T172145_1000it_10pct`, 1.063% of all trips (2,350) had both ends within 800 m of a stop; of those, 28 chose light rail, 1,010 car and 928 walk; the mean modelled tram leg is 1.60 km (§9.103).
- Corridor market against observation (`src/analyse/corridor_market.py`): work ends are placed where the jobs are (8.80% of work ends vs 8.04% of jobs within 800 m); shopping and other ends at roughly two-thirds of the observed attraction rate (6.84% vs 11.38%; 5.69% vs 8.07%); the home end is only 1.7–2.3% corridor, so a two-ended corridor market is small even at observed rates (§9.120, #30).
- Not the tram's cause, F19 iteration 20: the Interchange transfer works (rail-to-tram walk 54–58 m; 44 of 74 CBD-bound rail alighters take the tram; 16 tram vs 8 bus departures to the CBD in 07–09); the corridor-internal market of 1,127 trips has a mean beeline of 500 m and goes car 59% and walk 27% — a tram cannot beat a 500 m walk, and a mode constant is invisible to the raptor (§9.130).
- The pre-pandemic V001/V002 count (3,417 boardings a day, 2019–20) is marked unscorable in `src/calibrate/fit.py` and no error is quoted against it (§9.80, #84).

**Ferry.**

- F22 iteration 100 (the gate): 0.0285% of resident trips against 0.143% (−80.0%), flat at 0.02–0.03% across the arm — the fare moved it nowhere (§9.136, #94). F21's gate read 0.027% (§9.134).
- The market, by bank: B2 generates 4,956 harbour-crossing trips a weekday (0.211% of all trips) by 2,593 persons; 7,490 residents live on the Stockton side; 59,458 WEEKDAY trip ends lie within 1,000 m of the two wharves (§9.121, §9.120).
- The defect: the raptor's direct walk was a beeline across the harbour that the network executed as the ~20 km road detour; on F16 iteration 10, 174 of 256 crossing trips in residents' pt plans were walk-only (median 19.4 km) and 38.3% of all residents' pt-plan trips were walk-only (§9.121).
- After the repair, F17 arm `20260830T141222_300it_10pct`, iteration 10: 209 of 359 crossing trips routed with a ferry leg (58%), walk-only down to 17%; realised ferry 30 trips, 0.048% against the then-target 0.1013%, from 3 trips on F16; the remaining walk-only crossings are trips at hours the ferry does not run (§9.121).
- Before the repair, at iteration 100 of the committed arm: 450 trips with crow-fly under 3 km and road distance over 12 km took the detour, 118 of them on foot and 3 by public transport (§9.112).

## What is open

- Light rail: where the missing ~1,300 boardings a weekday are — longer corridor trips, rail transferees, visitors — is the mode's question at the next gate (§9.130, `NEXT_AGENT_BRIEF.md`).
- #30 — the deficit survives the licence-rate rebuild unchanged (shopping 0.59×, other 0.69×, work 1.09× of the attraction share, §9.136) and is measured structural (the band gradient above); the repair choice — floorspace-weighted attraction vs an agglomeration term — is a decision at B2's own family boundary (§9.120, §9.136).
- #84 — the disclosed boardings basis of §9.130 answers the issue's substance; it stays open until closed on evidence.
- #94 — the beeline defect is repaired, but the ferry reads −75.3% at F20 iteration 10 and has not been re-measured by bank since F17 (§9.121); whether the residual is hour of service, headway or scoring is not established (§9.112).
- The ferry target's vintage: the census cell is a lockdown month, which is why the sweep runs from 0 to twice the point value (§9.89).
- Both modes were re-read at the F21 gate and moved no closer on the licence-rate demand's own trend (§9.134); the corridor attraction (#30) and the ferry's residual (#94) stand as the causes to attack.
- The seated/standing split of the Urbos stays assumed; the acquisition route is field observation at Civic or Crown Street, or GTFS-Realtime dwell distributions (§4.3, §9.18).

## Refused — do not re-raise

- Lowering the light rail target on the corridor-market measurement: the market is modelled, and that would fit the yardstick to the answer (§9.103, §9.92).
- Quoting a light rail error against the 2019–20 V001/V002 boardings: pre-pandemic and unscorable (§9.80, #84).
- Rebuilding the schedule because tram and ferry route ids read SAT/SUN: the departures are present and exact (§9.113).
- Choosing a standing capacity for any vehicle without a published figure: closed by published figures, never by a number chosen here (§9.18, §9.30).
- Re-running pt2matsim to produce a per-scenario dwell schedule: it is derived from the mapped schedule (§3.5, §9.76).
- Reading charging dwell as additive to boarding dwell: double-counts boarding (§9.76).
- Naming the ferry's residual cause before measuring it: three asserted mechanisms reached committed entries in one session and were refuted (§9.112, #94).
- A light rail mode constant to move the router: SwissRailRaptor chooses on time and line-switch cost, not on an ASC (§9.130).
- Counting ferry or tram trips off `main_mode`: a public-transport trip carries `pt`; submodes come from the legs table (§9.112).

## History

- §9.136 — corridor deficit structural by band
- §9.134 — F21 gate: tram away, ferry flat
- §9.131 — licence rebuild pending; F21 next
- §9.130 — disclosed boardings target 2,954
- §9.122 — ferry target moves to LGA cell
- §9.121 — network direct walk repairs ferry
- §9.120 — corridor market measured; router reach declared
- §9.113 — supply ruled out; count departures
- §9.112 — ferry market walks the detour
- §9.103 — out of reach, not out-competed
- §9.89 — ferry gets a derived target
- §9.87 — folded target left ferry ungated
- §9.80 — V001 unscorable; no error quoted
- §9.77 — native dwell live in inputs
- §9.76 — charging dwell concurrent with boarding
- §9.30 — ferry fleet gets published capacity
- §9.18 — tram carries published 270
