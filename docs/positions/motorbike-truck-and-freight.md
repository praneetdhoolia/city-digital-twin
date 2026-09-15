# Motorbike, truck and freight rail — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 16 September 2026 (fifty-third session) · **Record read through:** §9.176 · **Written against family:** `F35`

## What is built

- **The freight trains at the two boom-gated crossings are derived from a published survey, not assumed zero** (§9.167, #184): the Cobbora Coal Project EA (EMM J11030RP5, ch. 13) reports a March 2012 five-day survey of St James Road and Clyde Street — 130 and 142 daily train movements, 432 and 463 minutes closed. Adamstown carries no coal (§9.70), so 130 − 86 passenger = **44 general-freight movements a day**; Clyde Street takes the same share, **48**, a stated assumption (`A.crossings.freight_closures_per_day`).
- The rebuilt events close Adamstown 416 min/day against the survey's 432; the `freight_train` representation counts **405 a weekday** (110 + 203 scheduled, 44 + 48 freight) (§9.167).
- **Motorcycles are 5.93 % of the light fleet by registration** (§9.167, #185): BITRE's Road Vehicles tables by postal area (CC-BY 3.0 AU) joined to the 44 postal areas inside the boundary — a constraint on the carve, never a target.

**Motorbike** is a person-level locked carve from car-driver demand, not a choice mode (§9.52): a licensed, car-available resident is drawn by a hash of person id and master seed and the whole day locks to `motorbike`; car loses exactly what motorbike gains.

- Anchor: census G62 one-method motorbike/scooter journeys over one-method driver journeys on the target LGA's own SA1s — `CAL.mode_split.motorbike_driver_journey_share` = 0.0064151 (282 of 43,959), measured and asserted on every build (§9.122).
- Share: `B.motorbike.trip_share` = 0.0037849, `derived` = `CAL.mode_split.vehicle_driver_level` 0.59 × the cell above; the carve share and the fit target are one observation (§9.115, §9.122).
- Resolution: `B.motorbike.carve_resolution` = `sa1_thinned` — the identity per home SA1, falling back to the SA2 under `B.census.thin_cell_min_journeys`; `region` is the sweep member (§9.122).
- Pool: the probability is solved on the persons who will actually be carved — not escorters that day and not named as a driver by any binder pass (§9.122, §9.129); `cells_at_sa1` 902, `cells_at_sa2` 799, core-wide trip-weighted cell share 0.002439 beside the declared 0.0037849 (`cities/newcastle/demand/plans/matsim/_plans_report.json`, §9.140).
- **Each LGA's cell shares are conserved to the LGA's own identity** (§9.140, #93): one factor per LGA makes the trip-weighted mean of its cells equal `CAL.mode_split.vehicle_driver_level` × the LGA's G62 ratio — Newcastle 0.8862, Maitland 0.9071, Lake Macquarie 0.9740, Cessnock 0.7244, Port Stephens 1.0649 (`_plans_report.json`, `lga_conservation`); the target LGA conserves to the DECLARED `B.motorbike.trip_share`, its SA1 cells summing to 0.0038289 (+1.2%, ABS perturbation, refused only beyond 5%).
- Physics: `B.motorbike.pce` = 0.4 (literature, sweep 0.3–0.75); `B.motorbike.length_m` = 2.2 held fixed as cosmetic in the queue model (§9.52).

**Resident truck drivers** are carved by the same mechanism on the same pool, on their own hash namespace so the motorbike draws stay byte-identical; one lock per person, never both (§9.125).

- **Neither carve draws a bound PASSENGER** (§9.146, #93): the pool excludes a person the binders named as a driver (§9.125) or as someone's passenger, before the draw, as §9.122 requires.
- `CAL.mode_split.truck_driver_journey_share` = 0.0050729 (G62 Truck, 223 of 43,959, measured) and `B.truck.resident_trip_share` = 0.002993, `derived` by the motorbike identity (§9.125); the carve's solve `q` 0.013358 against `declared_share` 0.002993 (`_plans_report.json`, `truck_carve`). Their trips count as `truck` in the twelve-mode table and at the count stations with the freight tier's vehicles.

**Freight** is a physical `truck` mode, a declared and sweepable background load rather than a freight demand model (§9.49).

- Vehicle: `B.freight.pce` = 2.0 (literature, sweep 1.5–3.5), `B.freight.max_speed_kmh` = 100 (definition), `B.freight.length_m` = 12.5 held fixed; `qsim.mainMode` carries `truck`, the vehicles file re-emitted per run (§9.49).
- Through tier: each cordon gate's volume splits car/truck by its own station's observed heavy share where classified (Hunter Expressway 0.1529) and `B.counts.heavy_vehicle_share` 0.0652 elsewhere, with the measured freight day factor (§9.49).
- Internal tier: `B.freight.trip_ratio` = 0.0697 (assumed, sweep 0.0–0.14; zero switches the tier off) × the observed car-driver share × the day's core person trips; origins and destinations on the census place-of-work attractor over `B.freight.attractor_divisions` with `B.freight.gravity_beta_per_km` = 0.08 (assumed, sweep 0.03–0.20); one agent is one one-way trip; `lockedMode=truck` in subpopulation `freight` (§9.49).
- Departure profile and weekend factors are measured from the classified hourly counts; truck routing is unconstrained — no truck-route, curfew or bridge-limit layer exists (§9.49).

**Freight rail** is deliberately not a mobsim vehicle: the coal chain runs on dedicated grade-separated track since 2006 and putting it on the passenger network would fabricate an interaction (§9.70). Its only road interaction — the two boom-gated level crossings — is built as time-variant link closures (§9.90).

- `A.crossings.representation` = `change_events`; `A.crossings.freight_road_names` = Saint James Road, Clyde Street (held fixed, §9.70); the Stewart Avenue tram crossing is excluded by `A.crossings.corridor_exclusion_m` = 500 (§9.90, §9.75).
- `A.crossings.closure_source` = `schedule_derived`: one closure per scheduled train whose mapped route traverses the crossing's rail links, timed from the nearest rail stop, read from the already-mapped feed, never a re-mapping; `assumed_uniform` with `A.crossings.closures_per_day` = 30 is the comparison member (§9.90).
- `A.crossings.freight_closures_per_day` = Saint James Road **44**, Clyde Street **48**, derived from the Cobbora survey (§9.167, #184), on top of the scheduled closures; every run's `_config.json` carries the values it loaded — arm 0 `20260912T202242_300it_25pct` at {Clyde Street 48, Saint James Road 44} (§9.169). The earlier 0 (assumed, sweep 0–30, §9.90) is superseded.
- Durations are the survey's: `A.crossings.closure_duration_passenger_s` = 160 s per scheduled passenger train and `A.crossings.closure_duration_s` = 277 s per freight movement (§9.167), superseding the 60 s and 240 s of §9.90 and §9.70.

## What is measured

- **All three on arm 0, F35's result** (§9.169, `20260912T202242_300it_25pct` at iteration 300, `ran_to_last_iteration`): motorbike **0.3572 % against 0.3785 %, −5.6 %** — INSIDE the 10 % bar for the first time on a result, 566 trips, a locked carve at 0.23 % coverage; truck **5.6251 %** network-wide road-vehicle share, level only (23,891 departures, 0 stuck; the target's basis is the count stations, `--truck-stations`, §9.101); freight rail **405 against 405**. Against the F32 result's motorbike +12.5 % (§9.163) a direction, not a comparison.
- The reader counts the scheduled 313 PLUS the 92 freight closures THE RUN carried (its own `_config.json`), where before it read 313 against 405 on every run — a 22.7 % bookkeeping shortfall (fixed §9.169); the run loaded 266 merged closure spans.
- **Motorbike's basis defect is measured fixed and #93 is closed** (§9.163): on `20260909T015217_300it_25pct` at iteration 300, motorbike reads **0.4259 %** of resident linked trips against the **0.3785 %** target-LGA identity the carve is conserved to — **+12.5 %**, a level difference on one shared basis; generation and scoring describe the same quantity.
- **It is the most stable mode on the board, and the choice-set table says why** (§9.163): motorbike holds **0.24 %** coverage against a **0.4259 %** share — the share EXCEEDS the coverage, possible only because a locked carve's riders hold no alternative for the mode-choice operator to switch them off; `report_choice_set_coverage.py` refuses to print a headroom for it and for truck. Its `snap_pp` at the innovation cutoff is exactly **0.000** where car moved +2.211; it drifts 0.2406 % → 0.2391 % across iterations 100–300 on the all-resident denominator.
- **All three at the F32 result** (`20260909T015217_300it_25pct` at iteration 300, §9.162): motorbike **0.4259 % against 0.3785 %, +12.5 %**, holding 0.4259–0.4674 % across all 300 iterations; truck **5.6321 %** network-wide, NOT its target basis (§9.101); freight rail **314 movements**, the timetable by construction. Motorbike and truck are locked carves outside `RUN.mode_choice.modes` and the depth arm confirms it — `snap_pp` **0.000** for both where every choosable mode moved.
- **The carve delivers what it solves for** (§9.129): 5,937 trips on 1,687 persons = 0.2666% of WEEKDAY resident trips against 0.2654% solved; before the pool repair it delivered 0.153%, 58% of the solve, because named drivers held 42.1% of the pool's trips.
- **Precision:** a 10% arm reads motorbike off a few tens of persons; a −50% at that depth was a sampling statement, not a defect (§9.122).
- The truck basis (`--truck-stations`): link entries against `road_aadt_targets.csv`'s own heavy shares, 3 calibration stations, 20 of 24 classifying stations holdout and never opened (§9.101); the station target row is 15.4698% (sweep 13.7256–17.4013) of weekday vehicles at classified stations (`mode_targets_by_mode.csv`).
- **Freight rail:** 405 movements per weekday — Clyde Street 203 scheduled plus 48 freight, Saint James Road 110 plus 44 — peaked with the service (§9.90, §9.167; Clyde Street read 204 on the previous mapping, the mapper's own drift, §3.5). The `freight_train` target row is 405 on that denominator and the reader reads each run's own closures against it (405 against 405 on arm 0, §9.169); a representation check, not a fit (§9.90).

## What is open

- **The truck yardstick is holdout-bound** (§9.101): scoring at the classifying stations spends holdout stations, and whether to open them for freight is the operator's decision. Counts themselves remain unfitted (#82).
- **The crossings' closure effect has never been measured** (§9.77, §9.90): #68 is closed on its build scope; both results carry the closures ON (arm 0 at 405 movements, §9.169) and no paired arm has carried them off, so what is left is a paired reading.
- The target CSV's `freight_train` basis text says each closure is 240 s, while the registry closes a passenger train for `A.crossings.closure_duration_passenger_s` = 160 s and a freight movement for 277 s (§9.167) — the registry is the newer statement and wins; the CSV text should be regenerated.
- Truck routing is unconstrained; no port-gate constraint is enforced — the Mayfield precinct cap (1,268 movements/day) is recorded as an upper bound only, never a target (§9.70).

## Refused — do not re-raise

- **A motorbike or truck choice model.** No preference observation exists; an invented constant is what §8.5 forbids. The share is declared, derived and swept; the day locks (§9.52, §9.125).
- **A separate motorbike network layer** (filtering, lane-splitting): inside the PCE sweep (§9.52).
- **Coal trains on the simulated rail network.** Grade-separated since 2006; adding them fabricates an interaction the real network does not have (§9.70).
- **Scoring truck on the network-wide share.** The target's own basis says it is not comparable; a −49.6% quoted on it was two populations, not an error (§9.101).
- **Pinning `freight_closures_per_day` on no evidence.** ARTC publishes no movement log; the 44 and 48 are derived from the published Cobbora survey with the Clyde Street share a stated assumption (§9.167, #184).
- **A freight tour or depot structure.** No local observation supports one; one agent is one one-way trip (§9.49).
- **The core's G62 cell as the motorbike yardstick.** Every other target is the target LGA's; the split reads the LGA's own SA1s (§9.122).

## History

- §9.176 — intro fixed: which runs are results is the board's
- §9.170 — tenth report re-reads arm 0 unchanged
- §9.169 — motorbike inside; freight like-for-like
- §9.167 — freight movements from Cobbora survey; BITRE acquired
- §9.166 — #93's closed bullet retired
- §9.163 — motorbike on one basis at +12.5 %; #93 closed
- §9.146 — F26 gate +11.1 %; carve draws no bound passenger
- §9.140 — carve conserved per LGA, rebuilt
- §9.136 — F22 gate; carve bias is the cell aggregation
- §9.134 — F21 gate: motorbike +24.6%
- §9.131 — licence rate rebuilt, carves await rebuild
- §9.129 — carves solved on drawn pool
- §9.126 — F18 built both carves
- §9.125 — resident truck-driver carve built
- §9.122 — escort denial before draw; LGA cell
