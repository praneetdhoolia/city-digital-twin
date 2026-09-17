# Public transport and its yardsticks — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 17 September 2026 (fifty-fourth session) · **Record read through:** §9.177 · **Written against family:** `F35`

## What is built

- **The reader resolves every run through its own schedule** (§9.169): the F34 rebuild had overwritten the city schedule the board read heavy rail **0 / −100 %** through; `extract_metrics.schedule_path` reads the run's own `output/output_transitSchedule.xml.gz` first (F32 reads **20,932 / +220.6 %**). A boardings reading with no sample fraction is REFUSED.
- **The access leg is a network leg** (§9.167, #167): `RemodeRestore.remodeTrip` replaces a five-leg ride trip whole; `NetworkDirectWalkPtRouter` routes the raptor's transfer beelines; `RUN.routing.access_egress_type` = `accessEgressModeToLink`, `RUN.transit_router.access_egress_basis` = `network`; teleports **1,572 → 554 → 0** an iteration on the 1 % probes.
- **The first disclosed ferry observation, as bounds** (§9.167, #185): TfNSW's daily Opal Patronage series (`cities/newcastle/extract/fetch_tpa_daily.py`) gives ferry tap-ons of **234–1,347 a weekday** and light rail **2,090–3,751**, bracketing the 2,954 target — bounds because hourly cells are rounded to 100 (`CAL.pt.opal_patronage_rounding`). Constraints, never targets (§9.8).
- **The nine `C.asc.*` constants reach the run from the registry** (§9.166): `scoring_from_c1` had read the build-time `params/C1_parameters.json`, so a `--config-set` override never executed; `tests/unit/test_override_reaches_the_run.py`.
- **The router that picks the submode has a constant to pick it with, behind a gate** (§9.162, #49): `citysim.RaptorModeCostCalculator` adds the boarded submode's own `scoring.modeParams` constant to the stock in-vehicle cost — a CONSISTENCY with scoring, no value of its own; gated by `C.raptor.mode_cost_representation`, **shipped `absent`**; **built, NEVER RUN** — it opens a family.
- **Where the constant lands** (§9.162): `getInVehicleCost` is called once per candidate alighting stop, so the constant is charged **once per boarded leg**; the fare and a distance term CANNOT go there (`RouteSegmentIterator` exposes no distance), so the fare stays in scoring.
- **Four scheduled submodes, score-distinct** (§9.78): SwissRailRaptor with `useModeMappingForPassengers`, one `scoring.modeParams` block each, behind `RUN.routing.pt_submode_scoring` = `per_submode`; plan-level choice stays `pt` (`citysim.PtSubmodeMainModeIdentifier`).
- **The raptor's cost carries no mode constant, no fare and no distance term** (§9.158): `RaptorUtils.createParameters` prices travel time, waiting and a line switch, nothing else — the split inside a pt trip is decided on TRAVEL TIME ALONE (§9.130); its one per-submode input is emitted as **-10.9608 for all four** (§9.162, `results/raw/20260909T015217_300it_25pct/config.xml`).
- **Crowding reaches scoring** (§9.158): `citysim.PtCrowdingScoring` charges each passenger `m(n) − 1` against the vehicle's runtime seat count at `ptCrowding.penaltyUtilsPerHour` = 16.961; `C.crowding.seated_multiplier` 1.0 (sweep 1.0–1.15), `C.crowding.standing_multiplier` 1.45 (sweep 1.2–1.8); `C.crowding.representation` = `absent` recovers the previous model. `standingRoomInPersons` was never 0: bus 44 / 18, ferry 149 / 51, rail 98 / 48 (§9.30).
- **Two constants opened, one created, the §8.5 departure logged** (§9.158): `C.asc.bus` −1.05 to sweep [−2.05, −0.05]; `C.asc.ferry` −1.05 CREATED; `C.asc.rail` −0.65 STAYS FROZEN — heavy rail's excess is a missing mechanism. Half-width from `C.taxi.asc`'s sweep (§9.76).
- **Fleet capacities are the published ones** (§9.30): bus `A.transit.bus_capacity_seated` 44 / `_standing` 18; rail `A.transit.rail_capacity_total` 146 (seated 98 assumed, swept 80–120); ferry `A.transit.ferry_capacity_total` 200 / 149; light rail `A.lightrail.capacity_total` 270 / 60 (§9.18).
- **Weekday supply on departures** (§9.113): bus 1,448, rail 332, tram 252, ferry 107; 1,270 mapped routes, **0 without departures** (§9.158). Access: `RUN.transit_router.search_radius_m` 1000, `RUN.transit_router.extension_radius_m` 200 (#94).
- **The heavy-rail target's basis names its censoring rule** (§9.142, #129): a censored Opal cell counts as `CAL.pt.censored_cell_value` in the SUM; the one censored cell lies outside the series, so the sweep moves nothing.
- **Twelve-mode target table** `data/processed/validation/mode_targets_by_mode.csv` by `build_mode_targets.py`; rail per-station counts in `pt_boardings_targets.json` (§9.130); scored by `src/analyse/report_mode_ridership.py`, submodes from the LEGS table (§9.112); the 67/143 split untouched (§9.87, §12).
- **Every pt journey is charged its published Opal fare** (§9.135): `citysim.PtFareChargeHandler` prices each leg from `data/raw/fares/` (36 `A.fare.*` fields) as `PersonMoneyEvent`s; the raptor never sees it.
- **Headway and reliability reach MATSim** (§9.164, #175): `citysim.ServiceQualityScoring` charges `C.time_weights.beta_headway` (0.5) × headway minutes and `C.time_weights.beta_reliability` (1.3) × the route's own arrival-delay sd, behind `C.time_weights.service_quality_representation` (`absent` shipped); the sd is measured over the previous mobsim, never seeded.

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
| ferry | 0.143% of resident trips | G62 ferry share within PT (34 of 904) × HTS PT 3.8% | derived | `mode_targets_by_mode.csv`, §9.89 |
| truck | 15.47% of weekday vehicles at classified stations | TfNSW classified counts; not a person-trip share | derived | `mode_targets_by_mode.csv`, §9.101 |
| freight_train | 405 closures/weekday | 313 timetable plus 92 freight (Cobbora survey) | derived | `mode_targets_by_mode.csv`, §9.90, §9.167 |

- **Bus** is the only PT mode on the composition basis, its series one contract region with an 88% break at 2025-04 (§9.100): the window by `CAL.pt_split.break_ratio` 0.5, stations by `CAL.pt_split.station_scope` = `target_lga`, light rail's one stop scaled by `CAL.pt_split.lr_observed_stop_share` 0.3696. **Ferry** is derived, sweep 0 to twice the point value (§9.89).

## What is measured

- **Two in three PT routing requests find no transit route on the footpath network, up from one in three** (§9.177, #162, `matsim.log` of `20260915T000704_250it_25pct`): **2,084,847 of 3,100,000** `ptDirectWalk` requests (**67.3 %**) had no transit route at all, against **31.09 %** of 4,800,000 on F32's `20260909T015217_300it_25pct` (§9.163) — doubled across the footpath rebuild and the engines' routing (pt coverage 17.53 → 15.78 %, §9.176). The pricing half stands: a second walking costs 1.0400 seconds riding at `RUN.transit_router.direct_walk_factor` = 1.0 (§9.158).
- **The routers pair's reading, F35's second result** (§9.176, `20260915T000704_250it_25pct`, iteration 250, `C.raptor.mode_cost_representation` = `mode_constant`): heavy rail **10,476** boardings against 6,529 (**+60.5 %**), light rail **856** against 2,954 (**−71.0 %**), bus **2.0895 %** against 2.3819 (**−12.3 %**), ferry **0.0473 %** against 0.1429 (**−66.9 %**); pt coverage **15.78 %**. Against arm 0 (+384 train boardings, +84 tram, +0.09 pp bus, −0.005 pp ferry) nothing moved outside the noise of one build (§9.142): the raptor's constant is not the pt layer's lever.
- **Arm 0's reading, F35's first result** (§9.169, `20260912T202242_300it_25pct`, iteration 300): heavy rail **10,092** boardings (+54.6 %), light rail **772** (−73.9 %), bus **2.0045 %** (−15.8 %), ferry **0.0524 %** (−63.3 %); pt coverage 17.53 %.
- **Pt is the only mode whose choice set is still opening at the cutoff** (§9.163, §9.169): coverage **25.78 %** at 300 on F32, still moving at **233** where every other mode closed by 27; **17.53 %** on arm 0. Boardings sampled on arm 0: bus 9,135, rail 3,036, tram 193, ferry 328. The submode targets sum to 2.52 %, inside either coverage.
- **The four PT modes are decided in a layer with no control variable** (§9.160, §9.158): `pt` is ONE alternative in `RUN.mode_choice.modes`; only **974 of 154,347 persons (0.63 %)** ever held plans differing in submode. The ASC contraction test is undecidable for the three pt modes, HELD until the raptor has a control (§9.160).

Latest twelve-mode reading: `results/raw/20260915T000704_250it_25pct` at iteration 250, `is_a_result: true` (§9.176); reproduce with `python src/analyse/report_mode_ridership.py --run 20260915T000704_250it_25pct --it 250`; arm 0's beside it (§9.169). Comparable with no earlier family (§3.5).

| mode | pair it.250 | arm 0 it.300 | target | deviation (pair) | source |
|---|---:|---:|---:|---:|---|
| bus | 2.0895% | 2.0045% | 2.3819% | −12.3% | §9.176, §9.169, #99 |
| heavy_rail | 10,476 bdg | 10,092 bdg | 6,529 bdg | +60.5% | §9.176, §9.169, #98 |
| light_rail | 856 bdg | 772 bdg | 2,954 bdg | −71.0% | §9.176, §9.169, §9.130 |
| ferry | 0.0473% | 0.0524% | 0.1429% | −66.9% | §9.176, §9.169, #94 |

- **Bus is read against a target its own basis doubts**: the HTS level and the operator series differ by 3–10× (#99); two indications put bus nearer 75–78 % of PT boardings than 62.7 % (§9.100).

## What is open

- **The raptor's submode constant is measured and is not the lever** (§9.176): `C.raptor.mode_cost_representation` = `mode_constant` moved the split by +384 train and +84 tram boardings against arm 0, inside one build's noise (§9.142). The SERVICE-QUALITY pair (#175, §9.164) and the crowding control (#174) are the pt layer's unrun controls; what runs next is D7 (§9.176), and any arm needs a stated-cost approval, none standing.
- **#98 — heavy rail +60.5 % on the pair and +54.6 % on arm 0** (§9.176, §9.169) after +225.0 % on F32; the crowding disutility is its first brake (§9.158): F32 ran WITH `C.crowding.representation` = `in_vehicle_time` and the `absent` control has never run (#174).
- **#94** — the ferry captures a hundredth of its captive market; the reach bound and a competitive-but-losing plan remain (§9.112, §9.140, §9.158).
- **#49** — a standing product directive, not a run question: `decision-needed` with an `AWAITING-DECISION:` line; reported at every gate, blocking nothing (§9.160).
- **Bus stays on the composition basis as a recorded limitation** (§9.140, #99 closed): the Opal `NISC 1` series falls 88 % in April 2025 and no allowlisted source publishes Newcastle's bus boardings; REOPEN #99 if one appears. The operator series total 14,858 boardings a day against an HTS-implied 76,646 PT trips (§9.100).

## Refused — do not re-raise

- **Re-mapping the schedule to fix the light rail or the ferry**: 252 tram and 107 ferry weekday departures are present (§9.113).
- **A ferry target from the NSW-wide Opal ferry row**: Sydney-dominated (§9.87, §9.89).
- **Adding the per-mode rows to `validation_targets.csv`**: they disaggregate observations already there (§9.87, §12).
- **Quoting the pre-pandemic 3,417/day light rail figure or the 20.8 % share as a fit** (#84, §12).
- **Scoring a boardings-built target against linked trips** (§9.100); **counting submodes off `main_mode`** (§9.112).
- **Sweeping the ferry's capacity or the gate bar** (§9.30, §9.87).
- **Solving `C.asc.rail` against heavy rail's excess** (§8.5, §9.158): a missing mechanism; frozen until the crowding disutility is MEASURED.

## History

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
- §9.157 — F31 gate: heavy rail +247.2 %
- §9.142 — censoring rule named
- §9.140 — bus count unobtainable
