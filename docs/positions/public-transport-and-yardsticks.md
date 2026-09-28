# Public transport and its yardsticks — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 29 September 2026 (sixty-fourth session) · **Record read through:** §9.217 · **Written against family:** `F38`

## What is built

- **Mumbai's suburban schedule is the printed timetable** (§9.209): 3,289 trains from nine WR and CR sheets (`build_suburban_timetable_feed.py`; WR 1,394 / CR 1,895 against 1,414 / 1,820 published), 255 AC and 54 fifteen-car trains on their own profiles; Metro 2A/7/9/2B in live windows at the April 2026 headways, within 8.3 % of the printed weekday trips (`baseline_transit_feed.json`). The Line 7–9 through corridor still runs as two lines (`docs/lane.json`).

- **The access ceiling reaches every stop the beeline finder reaches** (§9.213, §9.214): `RUN.transit_router.access_max_radius_m` **55,900 m**, `measured` (farthest nearest-stop + 200 m), re-measured on F38's demand when the assembler refused 55,600 m against a 55,668 m Saturday reach; the old 1,200 m cut the raptor's nearest-stop fallback.
- **The access leg is a network leg** (§9.167, #167): `RemodeRestore.remodeTrip` replaces a five-leg ride trip whole; `NetworkDirectWalkPtRouter` routes the raptor's transfer beelines; `RUN.routing.access_egress_type` = `accessEgressModeToLink`, `RUN.transit_router.access_egress_basis` = `network`; teleports **1,572 → 554 → 0** an iteration on the 1 % probes.
- **The first disclosed ferry observation** (§9.167, §9.211, #185): TfNSW's daily Opal Patronage series (`cities/newcastle/extract/fetch_tpa_daily.py`) gives ferry tap-ons of **234–1,347 a weekday**, the target the mean midpoint (hourly cells rounded to 100, `CAL.pt.opal_patronage_rounding`), and light rail **2,090–3,751**, bracketing the 2,954 target.
- **The nine `C.asc.*` constants reach the run from the registry** (§9.166): `tests/unit/test_override_reaches_the_run.py`.
- **The router that picks the submode has a constant to pick it with, behind a gate** (§9.162, #49): `citysim.RaptorModeCostCalculator` adds the boarded submode's own `scoring.modeParams` constant to the stock in-vehicle cost, gated by `C.raptor.mode_cost_representation`, **shipped `absent`**.
- **Four scheduled submodes, score-distinct** (§9.78): SwissRailRaptor with `useModeMappingForPassengers`, one `scoring.modeParams` block each, behind `RUN.routing.pt_submode_scoring` = `per_submode`; plan-level choice stays `pt` (`citysim.PtSubmodeMainModeIdentifier`).
- **The raptor's cost carries no mode constant, no fare and no distance term** (§9.158): `RaptorUtils.createParameters` prices travel time, waiting and a line switch — the split inside a pt trip is decided on TRAVEL TIME ALONE (§9.130).
- **Crowding reaches scoring** (§9.158): `citysim.PtCrowdingScoring` charges each passenger `m(n) − 1` against the vehicle's runtime seat count at `ptCrowding.penaltyUtilsPerHour` = 16.961; `C.crowding.seated_multiplier` 1.0 (sweep 1.0–1.15), `C.crowding.standing_multiplier` 1.45 (sweep 1.2–1.8); `C.crowding.representation` = `absent` recovers the previous model.
- **Two constants opened, one created** (§9.158): `C.asc.bus` −1.05 to sweep [−2.05, −0.05]; `C.asc.ferry` −1.05 CREATED; `C.asc.rail` −0.65 STAYS FROZEN — heavy rail's excess is a missing mechanism.
- **Fleet capacities are the published ones** (§9.30): bus `A.transit.bus_capacity_seated` 44 / `_standing` 18; rail `A.transit.rail_capacity_total` 146 (seated 98 assumed, swept 80–120); ferry `A.transit.ferry_capacity_total` 200 / 149; light rail `A.lightrail.capacity_total` 270 / 60 (§9.18).
- **Weekday supply on departures** (§9.113): bus 1,448, rail 332, tram 252, ferry 107; 1,270 mapped routes, **0 without departures** (§9.158). Access: `RUN.transit_router.search_radius_m` 1000, `RUN.transit_router.extension_radius_m` 200 (#94).
- **The heavy-rail target's basis names its censoring rule** (§9.142, #129): a censored Opal cell counts as `CAL.pt.censored_cell_value` in the SUM; the one censored cell lies outside the series.
- **Twelve-mode target table** `data/processed/validation/mode_targets_by_mode.csv` by `build_mode_targets.py`; rail per-station counts in `pt_boardings_targets.json` (§9.130); scored by `src/analyse/report_mode_ridership.py`, submodes from the LEGS table (§9.112); the 67/143 split untouched (§9.87, §12).
- **Every pt journey is charged its published Opal fare, and an unfared submode is refused** (§9.135, §9.214): `citysim.PtFareChargeHandler` prices each leg from `data/raw/fares/` (36 `A.fare.*` fields) as `PersonMoneyEvent`s; a boarded submode with no declared fare is REFUSED instead of charged the bus table (the 9.78 fallback retired; no Newcastle schedule carries another submode).
- **Headway and reliability reach MATSim** (§9.164, #175): `citysim.ServiceQualityScoring` charges `C.time_weights.beta_headway` (0.5) × headway minutes and `C.time_weights.beta_reliability` (1.3) × the route's own arrival-delay sd, behind `C.time_weights.service_quality_representation` (`absent` shipped).

## The twelve targets and their bases

Bases from `data/processed/validation/mode_targets_by_mode.csv`; the PT rows are the topic, the rest listed so the table is complete.

| mode | target | basis | status | source |
|---|---:|---|---|---|
| car | 58.32% of resident trips | HTS Vehicle driver 59.0% × G62 car-as-driver share | derived | `mode_targets_by_mode.csv`, §9.87 |
| ride | 20.60% | HTS Vehicle passenger, read directly | observed | `mode_targets_by_mode.csv` |
| walk | 13.40% | HTS Walk only, read directly | observed | `mode_targets_by_mode.csv` |
| taxi | 0.99% | `B.taxi.daily_trips_band` over study-area weekday trips | derived | `mode_targets_by_mode.csv`, §9.91 |
| bike | 2.21% | HTS Other 3.2% minus the point-to-point share | derived | `mode_targets_by_mode.csv` |
| motorbike | 0.3785% | HTS Vehicle driver × G62 motorbike/scooter share | derived | `mode_targets_by_mode.csv`, §9.112 |
| bus | 2.38% of resident trips | HTS PT 3.8% × Opal/station boardings share 62.681% | derived | `mode_targets_by_mode.csv`, §9.100 |
| heavy_rail | 6,529 boardings/weekday | disclosed entries at 24 stations, 6,086/day × `CAL.pt.weekday_factor` 1.0727 | measured | `pt_boardings_targets.json`, §9.130 |
| light_rail | 2,954 boardings/weekday | the line's disclosed Opal series, 2,754/day × `CAL.pt.weekday_factor` | measured | `pt_boardings_targets.json`, §9.130 |
| ferry | 790 boardings/weekday | TPA daily Opal tap-ons, mean of each weekday's bound midpoint (234–1,347) | measured | `mode_targets_by_mode.csv`, §9.211 |
| truck | 15.47% of weekday vehicles at classified stations | TfNSW classified counts; not a person-trip share | derived | `mode_targets_by_mode.csv`, §9.101 |
| freight_train | 405 closures/weekday | 313 timetable plus 92 freight (Cobbora survey) | derived | `mode_targets_by_mode.csv`, §9.90, §9.167 |

- **Bus** is the only PT mode on the composition basis, its series one contract region with an 88% break at 2025-04 (§9.100): the window by `CAL.pt_split.break_ratio` 0.5, stations by `CAL.pt_split.station_scope` = `target_lga`, light rail's one stop scaled by `CAL.pt_split.lr_observed_stop_share` 0.3696.

## What is measured

Latest twelve-mode reading: F38's arm 0 `20260929T012258_250it_25pct` at iteration 250, `ran_to_last_iteration` across warm-start joins (§9.217); reproduce with `python src/analyse/report_mode_ridership.py --run 20260929T012258_250it_25pct --it 250`; F37's arm 0 beside it (§9.214) as a direction, never a comparison (§3.5).

| mode | F38 arm 0 it.250 | F37 arm 0 it.250 | target | deviation (F38) | source |
|---|---:|---:|---:|---:|---|
| bus | 1.6621% | 2.1143% | 2.3819% | −30.2% | §9.217, §9.214, #99 |
| heavy_rail | 14,236 bdg | 18,788 bdg | 6,529 bdg | +118.1% | §9.217, §9.214, #98 |
| light_rail | 812 bdg | 1,252 bdg | 2,954 bdg | −72.5% | §9.217, §9.214, §9.130 |
| ferry | 1,704 bdg | 1,732 bdg | 790 bdg | +115.6% | §9.217, §9.214, #94 |

- **Pt coverage 19.09 %** at iteration 250 against a 3.07 % share (`report_choice_set_coverage.py`); pt is ONE alternative in `RUN.mode_choice.modes`, so every submode shares that bound (§9.160).
- **Rail-to-rail transfers are not the rail excess** (§9.214, item 1): of 18,788 boardings at the 24 disclosed stations, **1,772** are rail-to-rail transfers (1,620 at Hamilton); station ENTRIES alone are **17,016** against 6,529. The external tier boards 140 of 21,436 rail boardings.
- **Rail is reached on long walks by the car-less** (§9.214, item 1): **19.5 %** of resident entries walk more than 2 km to the station (14.2 % more than 5 km; Metford median 5.6 km, Awaba 6.0 km); car-less residents make 17.8 % of trips and **52 %** of rail entries (26.6 rail trips per 1,000 trips against 5.2 for the car-available).
- **No transit route is geography, not the clock** (§9.214, item 4, #162): the run's own counter — **1,407,916 of 2,699,993** pt requests (**52.1 %**, 66.3 % on F36) had no transit route; 28.5 % of the answered were beaten by the network walk. Re-routed offline (`diagnose_pt_routing.py --sample 3000`, `_pt_routing.json`): **39.2–39.8 %**, 78.1 % of them unconnected at 15:00 too; nearest stop p50 285 m, p90 6.8 km, p99 16.0 km; 31.0 % of origins have no stop within 1 km. The residual is rural trip ends (recommendation 4 of the fourteenth report, answered).
- **The four PT modes are decided in a layer with no control variable** (§9.160, §9.158): only **974 of 154,347 persons (0.63 %)** ever held plans differing in submode; the raptor's submode constant moved the split inside one build's noise (§9.176).
- **Bus is read against a target its own basis doubts**: the HTS level and the operator series differ by 3–10× (#99); two indications put bus nearer 75–78 % of PT boardings than 62.7 % (§9.100).

## What is open

- **#98 — heavy rail +187.8 %** (§9.214): entries 17,016 against 6,529, carried by car-less residents on long access walks. F38's arm 0 reads entries against **17,016** and access walks over 2 km against **19.5 %** with the car-less sent to nearer destinations; the walk-access weight is not changed until then (§9.214). The crowding control (`C.crowding.representation` = `absent`, #174) has never run.
- **#162 — the no-route residual is rural trip ends** (§9.214): 39.2–39.8 % offline, walked because the car-less have nothing else; re-read on F38.
- **#94 — the ferry reads +119.2 % on its disclosed tap-ons** (§9.214, §9.211); the near-wharf market is `measure_near_wharf.py`'s to read on F38.
- **Light rail −57.6 %** (§9.214): the line's 252 weekday departures are present (§9.113); see [light-rail-and-ferry](light-rail-and-ferry.md).
- **The pt layer's unrun controls**: the SERVICE-QUALITY pair (#175, §9.164) and the crowding control (#174); any arm needs a stated-cost approval, none standing.
- **#49** — a standing product directive, not a run question: `decision-needed` with an `AWAITING-DECISION:` line; reported at every gate, blocking nothing (§9.160).
- **Bus stays on the composition basis as a recorded limitation** (§9.140, #99 closed): the Opal `NISC 1` series falls 88 % in April 2025 and no allowlisted source publishes Newcastle's bus boardings; REOPEN #99 if one appears.

## Refused — do not re-raise

- **Re-mapping the schedule to fix the light rail or the ferry**: 252 tram and 107 ferry weekday departures are present (§9.113).
- **A ferry target from the NSW-wide Opal ferry row**: Sydney-dominated (§9.87, §9.89).
- **Adding the per-mode rows to `validation_targets.csv`**: they disaggregate observations already there (§9.87, §12).
- **Quoting the pre-pandemic 3,417/day light rail figure or the 20.8 % share as a fit** (#84, §12).
- **Scoring a boardings-built target against linked trips** (§9.100); **counting submodes off `main_mode`** (§9.112).
- **Sweeping the ferry's capacity or the gate bar** (§9.30, §9.87).
- **Solving `C.asc.rail` against heavy rail's excess** (§8.5, §9.158): a missing mechanism, now traced to the demand (§9.214).
- **Charging an unfared submode the bus table** (§9.214): refused at run time.

## History

- §9.214 — rail entries, rural no-route
- §9.213 — access ceiling measured, not derived
- §9.209 — printed timetables; possession; grades
- §9.177 — no transit route for 67 %
- §9.176 — the routers pair: raptor constant not the lever
- §9.170 — router-scorer consistency unrun
- §9.169 — arm 0's reading; reader fixed
- §9.167 — access leg walks the network
- §9.166 — C.asc.* reach the run
- §9.164 — headway and reliability reach the model
- §9.163 — walk fallback holds at depth
- §9.162 — a control for the router
- §9.161 — #167 diagnosed
- §9.160 — pt submode has no control
- §9.158 — walking priced as riding
