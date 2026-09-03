# Public transport and its yardsticks — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 3 September 2026 · **Record read through:** §9.140 · **Open family:** F23 (the package on disk opens F24 at its first launch)

## What is built

- **Four scheduled submodes, score-distinct (Tier C, §9.78).** Bus, heavy rail, light rail and ferry are routed by SwissRailRaptor with `useModeMappingForPassengers`, one `scoring.modeParams` block per submode, behind `RUN.routing.pt_submode_scoring` = `per_submode`. The constants are C1's: `C.asc.bus` −1.05, `C.asc.light_rail` −0.75, `C.asc.rail` −0.65, all held fixed (§8.5, §9.78). Ferry has no C1 constant and keeps the pt aggregate's `asc_bus`, stated in the run-inputs report rather than invented (§9.78).
- Plan-level choice stays `pt`; only the router assigns submode legs, and `citysim.PtSubmodeMainModeIdentifier` folds them back to `pt` for every main-mode analysis (§9.78). `RUN.transit.transit_modes` carries the submode vocabulary so the QSim serves a `tram` or `ferry` departure instead of teleporting it; `split_schedule` refuses a route whose `transportMode` is outside it.
- **Fleet capacities are the published ones (§9.30).** Bus `A.transit.bus_capacity_seated` 44 / `_standing` 18 (Volvo B12BLE, swept to the B10B's 51 seats); heavy rail `A.transit.rail_capacity_total` 146 (two-car Hunter set, seated 98 assumed at two-thirds, swept 80–120); ferry `A.transit.ferry_capacity_total` 200 / seated 149, both held fixed because the split is published; light rail `A.lightrail.capacity_total` 270 / seated 60 (§9.18). Every vehicle carries standing room, so the C1 crowding multipliers can bind (§9.30).
- **Weekday supply, counted on departures (§9.113):** bus 1,448, rail 332, tram 252, ferry 107 in the mapped weekday schedule (§9.113). Supply is ruled out as the cause of the light rail and ferry deficits.
- **Twelve-mode target table** at `data/processed/validation/mode_targets_by_mode.csv` (13 rows, one per mode plus header), written by `cities/newcastle/build/build_mode_targets.py`; the two rail modes' per-station disclosed counts are in `data/processed/validation/pt_boardings_targets.json` (`decisions_ref` 9.130). Scored by `src/analyse/report_mode_ridership.py` — submodes are read from the LEGS table by the route each leg boarded, never from `main_mode`, which is `pt` for every PT trip (§9.112).
- The table is a **disaggregation** of targets already in `validation_targets.csv`; it is not added to the pre-registered 210 and the 67/143 calibration/holdout split is untouched (§9.87, §12).
- PT access: `RUN.transit_router.search_radius_m` 1000 and `RUN.transit_router.extension_radius_m` 200 govern every submode's reach, including whether a Stockton resident can be routed onto the ferry (#94).
- **Every pt journey is charged its published Opal fare (§9.135).** `citysim.PtFareChargeHandler` prices each fare leg from the archived schedule (`data/raw/fares/`, 36 `A.fare.*` fields, all observed but two literature): distance-banded peak/off-peak tables per submode, the Stockton ferry's own row, the $2/$1 transfer discount, child (4–15) and Gold Senior/Pensioner (60+, not full-time employed; capped $2.50/fare and $2.50/day) classes, and the published daily caps — as `PersonMoneyEvent`s at journey close. Until §9.135 every pt trip was free while car paid fuel and parking and taxi the meter. The raptor still routes without seeing the fare; plan choice pays it.

## The twelve targets and their bases

Bases from `data/processed/validation/mode_targets_by_mode.csv`; the PT rows are the topic, the rest are listed so the table is complete.

| mode | target | basis | status | source |
|---|---:|---|---|---|
| car | 58.32% of resident trips | HTS Vehicle driver 59.0% × census G62 car-as-driver share of driver journeys | derived | `mode_targets_by_mode.csv`, §9.87 |
| ride | 20.60% | HTS Vehicle passenger, read directly | observed | `mode_targets_by_mode.csv` |
| walk | 13.40% | HTS Walk only, read directly | observed | `mode_targets_by_mode.csv` |
| taxi | 0.99% | `B.taxi.daily_trips_band` over study-area weekday trips, not the census | derived | `mode_targets_by_mode.csv`, §9.91 |
| bike | 2.21% | HTS Other 3.2% minus the point-to-point share | derived | `mode_targets_by_mode.csv` |
| motorbike | 0.3785% | HTS Vehicle driver × G62 motorbike/scooter share of driver journeys | derived | `mode_targets_by_mode.csv`, §9.112 |
| bus | 2.38% of resident trips | HTS PT 3.8% × Opal/station boardings share 62.681% over 2024-10..2025-03 | derived | `mode_targets_by_mode.csv`, §9.100 |
| heavy_rail | 6,529 boardings/weekday | disclosed station entries at the 24 mapped stations, 6,086/day × `CAL.pt.weekday_factor` 1.0727 | measured | `pt_boardings_targets.json`, §9.130 |
| light_rail | 2,954 boardings/weekday | the line's own disclosed Opal series, 2,754/day × `CAL.pt.weekday_factor` | measured | `pt_boardings_targets.json`, §9.130 |
| ferry | 0.143% of resident trips | census G62 ferry share within PT (34 of 904) × HTS PT 3.8%; nothing is published | derived | `mode_targets_by_mode.csv`, §9.89 |
| truck | 15.47% of weekday vehicles at classified stations | TfNSW classified counts; not a person-trip share | derived | `mode_targets_by_mode.csv`, §9.101 |
| freight_train | 314 crossing closures/weekday | timetable-derived; the train is not a mobsim vehicle | derived | `mode_targets_by_mode.csv`, §9.90 |

- **Bus** is the only PT mode still on the composition basis, because its published series is one contract region with an 88% structural break at 2025-04 (§9.100); the window is the contiguous break-free overlap chosen by `CAL.pt_split.break_ratio` 0.5, stations are scoped by `CAL.pt_split.station_scope` = `target_lga` (15 excluded, all named in the csv basis), and light rail's one reported stop is scaled to the line by `CAL.pt_split.lr_observed_stop_share` 0.3696 (§9.100). Its sweep runs to the census commute composition's 81.3% at `mode_targets_by_mode.csv`.
- **Heavy rail and light rail** are disclosed counts, used exactly: every traveller who boards, all subpopulations, × 1/fraction, heavy rail at the 24 disclosed stations only (§9.130). The PT total is still read against the HTS 3.8% level (§9.130).
- **Ferry** is derived and its sweep is 0 to twice the point value, because the only city-specific observation is a lockdown-vintage census count (§9.89). It is never labelled observed.

## What is measured

Latest twelve-mode reading: the F23 gate at iteration 100 (`results/raw/aborted_20260901T165115_300it_25pct`, §9.139) — the first gate on the income-scaled fare-priced model, 25% sample; the session stopped the run on it; not a result. Reproduce with `python src/analyse/report_mode_ridership.py --run aborted_20260901T165115_300it_25pct --it 100` (`--trend` for the arc).

| mode | F23 it.100 | target | deviation | F23 it.0 | source |
|---|---:|---:|---:|---:|---|
| bus | 2.77% | 2.38% | +16.2%, toward | 6.29% | §9.139, #99 |
| heavy_rail | 19,140 bdg | 6,529 bdg | +193.2%, falling all arm | 37,568 bdg | §9.139, #98 |
| light_rail | 1,000 bdg | 2,954 bdg | −66.1%, AWAY | 2,056 bdg | §9.139, §9.130 |
| ferry | 0.029% | 0.143% | −80.0%, flat | 0.032% | §9.139, #94 |

- **Income scaling weakened the fare where the fare was working** (§9.139, #108): at the same gate of the prior family the flat-fare model read bus +8.0% INSIDE and heavy rail +152.9% (§9.136); with the G17 income through marginalUtilityOfMoney the same gate reads bus +16.2% and heavy rail +193.2% — the over-boarders are disproportionately higher-income, so their fare deterrent shrank. Taxi likewise +70.9% → +76.6% (§9.139, #49). Each pair is a within-family gate-to-gate diagnostic across the F22→F23 boundary, stated as such, never a fit.

- **The PT total is right and its composition is wrong.** At F19 it.20 PT was 3.55% of resident trips against HTS 3.8%; boardings split bus 67.7 / rail 30.1 / tram 1.3 / ferry 1.0 against the Opal 62.7 / 20.4 / 17.0 (§9.130).
- **Heavy rail's excess is at the suburban stations, not the Interchange (§9.130, #98), and it is genuine demand, not the yardstick (§9.135).** The F21 per-station split: 9.8% of rail journeys re-board (Hamilton); even scored as entries the mode read +131%; **Newcastle Interchange is UNDER at 610 vs 1,683 entries** — the missing CBD end is #30's corridor attraction, measured structural in the home-anchored distance bands (§9.135, §9.136).
- **Two measured causes have each moved rail, neither closed it.** The licence rate (§9.131, measured from the TfNSW snapshot) took the F21 gate to +161.8% (§9.134); the fare (§9.135) took the F22 gate to +152.9% with the fall still running at the stop (§9.136). Light rail and ferry moved no closer under either (§9.134, §9.136).
- **The light rail's shortfall is not supply, not the destination market and not the Interchange transfer (§9.130).** The tram runs 252 weekday departures (§9.113); work ends within 400 m of a tram stop are 5.8% of all work ends (§9.130); the rail-to-tram walk is 54–58 m (§9.130). Where the missing riders are — longer corridor trips, rail transferees, visitors — is the open question.
- **The ferry's market exists and walks around it.** 450 trips a day take the road detour around the water the ferry crosses, and 3 of them take public transport (§9.112, #94).
- **Bus is read against a target its own basis doubts.** The HTS level and the operator series differ by roughly 3–10× by mode (#99); two independent indications put bus nearer 75–78% of PT boardings than the 62.7% point value (§9.100).

## What is open

- **#98** — the fare is measured (+152.9% at F22's gate, §9.136) and income scaling measurably worsens it (+193.2% at F23's, §9.139): the residual excess's cause once price is paid — the corridor's missing CBD end (#30) is the standing candidate — now outranks any further price work; crowding stays deferred behind it (§9.138).
- **Bus stays on the composition basis as a recorded limitation** (§9.140, #99 closed): the Opal `NISC 1` series falls 88% in April 2025 (319,770 → 37,414 trips a month), uniformly across card types, absorbed by no other region, recovering only to 226,956 by May 2026 (`data/raw/opal/bus_trips_by_contract_region.csv`); no allowlisted source publishes Newcastle's bus boardings. The HTS data document defines Public Transport as train, metro, bus, light rail and ferry with no exclusion of school services, so a school-bus trip is a PT trip in the survey while Opal counts taps (`data/raw/hts/hts_data_document_2020_2024.pdf`, §9.140). REOPEN #99 if a regional count becomes obtainable.
- **#94** — the ferry captures a hundredth of its captive market; the raptor's reason is not established and no candidate has been measured (§9.112).
- **#49** — the standing directive: every mode individually. Reporting and scoring are individual; the <10% bar is not met for any PT mode.
- #84 is closed (§9.140): the disclosed basis of §9.130 is the scoreable target, and no living document quotes an error against the pre-pandemic count.
- The composition's own coverage: the three operator series total 14,858 boardings a day against an HTS-implied 76,646 PT trips, so the sweep on bus is live, not decorative (§9.100).
- The light rail's missing riders (§9.130) — the light rail's open question at the F20 gate.
- Time is priced at the one declared `beta_ivt` for every submode; C1 declares no per-submode time weight (§9.78).

## Refused — do not re-raise

- **Re-mapping the schedule to fix the light rail or the ferry.** Supply is present and exact: 252 tram and 107 ferry weekday departures (§9.113). A `transitRoute` id's day tag is a label, not a calendar — never read service from it, count departures.
- **A ferry target from the NSW-wide Opal ferry row.** It is Sydney-dominated and identifies nothing here (§9.87, §9.89). Ferry is derived and stays labelled so.
- **Adding the per-mode rows to `validation_targets.csv`.** They disaggregate observations already there; scoring both counts one observation twice and disturbs the 67/143 split (§9.87, §12).
- **A contemporary bus level in the pre-registered set (§12.4).** Reported as a labelled post-hoc diagnostic outside the 210 in `validation_targets.csv`.
- **Quoting the pre-pandemic 3,417/day light rail figure or the 20.8% share as a fit (#84, §12).** Both are unscorable against a 2026 base; the 20.8% is a boardings upper bound, not hypothesis A1's metric.
- **Scoring a boardings-built target against linked trips.** The linked-trip basis is hostile to the shortest mode, which is the intervention (mean tram leg 1.60 km against 18.73 km for rail, §9.100).
- **Sweeping the ferry's capacity or the gate bar.** A vessel capacity is a fact about the boat (§9.30); `CAL.gate.stop_deviation_pct` 20 and `pass_deviation_pct` 10 state the bar and sweeping them would sweep the question (§9.87).
- **Counting submodes off `main_mode`.** It is `pt` for every PT trip; read the legs (§9.112).

## History

- §9.140 — bus count unobtainable; #84, #99 closed
- §9.139 — F23 gate: income scaling blunts fare
- §9.136 — F22 gate: fare lands, bus inside
- §9.135 — the published Opal fare priced in
- §9.134 — F21 gate: rail halved, tram away
- §9.131 — licence rate now measured, rail cause
- §9.130 — rail modes held to disclosed boardings
- §9.113 — day tag is not service; supply exonerated
- §9.112 — ferry market walks the detour
- §9.101 — truck target not a person share
- §9.100 — Sydney stop, three LGAs, broken series
- §9.91 — check the yardstick before the model
- §9.90 — crossing closures from the timetable
- §9.89 — ferry gets a derived target
- §9.87 — twelve modes get twelve targets
- §9.78 — submodes score-distinct via raptor mapping
- §9.30 — fleet carries published capacities
- §9.18 — light rail vehicle corrected
- §9.3 — one pt mode, not representable then
- §12 — 67/143 split fixed, never opened
