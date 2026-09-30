# Motorbike, truck and freight rail — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 30 September 2026 (sixty-fourth session) · **Record read through:** §9.219 · **Written against family:** `F39`

## What is built

- **The freight trains at the two boom-gated crossings are derived from a published survey, not assumed zero** (§9.167, #184): the Cobbora Coal Project EA (EMM J11030RP5, ch. 13) reports a March 2012 five-day survey of St James Road and Clyde Street — 130 and 142 daily train movements, 432 and 463 minutes closed. Adamstown carries no coal (§9.70), so 130 − 86 passenger = **44 general-freight movements a day**; Clyde Street takes the same share, **48**, a stated assumption (`A.crossings.freight_closures_per_day`).
- The rebuilt events close Adamstown 416 min/day against the survey's 432; the `freight_train` representation counts **405 a weekday** (110 + 203 scheduled, 44 + 48 freight) (§9.167).
- **Motorcycles are 5.93 % of the light fleet by registration** (§9.167, #185): BITRE's Road Vehicles tables by postal area (CC-BY 3.0 AU) joined to the 44 postal areas inside the boundary — a constraint, never a target.

**Motorbike is CHOSEN** (§9.214, D22, #257): `B.motorbike.representation` = `choice`; `carve` (the person-level locked carve of §9.52) is the other member and reproduces F37 byte-identically.

- **Who can ride** (§9.214; [population-and-demand](population-and-demand.md)): a rider licence from the TfNSW snapshot's Rider class, learners included (NSW learner riders ride unaccompanied), over ERP by age band and LGA (`B.population.rider_licence_rate_by_age_band`, derived); household motorcycle possession from BITRE's garaging-postcode registrations over census dwellings by the Poisson at-least-one identity (`B.population.household_motorcycle_share` 0.1254, derived).
- **Coupling** (§9.214): `B.motorbike.rider_coupling` = `riders_first` (assumed; `independent` the other member) — riders drawn at their observed rate, then possession only in households holding a rider, at the rate that keeps each postcode's observed possessing households. **35,416** persons available (5.78 %); ceiling **6.05 %** of weekday trips against the **0.3785 %** target.
- **In the choice set** (§9.214): `motorbikeAvail` is honoured by `citysim.AvailabilityModesCalculator`; motorbike joins the subtour choice set as chain-based (the smoke `20260927T133104_2it_1pct` logs chainBasedModes [car, bike, motorbike]).
- **Priced** (§9.214): `C.scoring.motorbike_fuel_ratio` **0.5351** (derived, ABS SMVU 2020 Table 6, NSW total fuel: motor cycles 6.1 over passenger vehicles 11.4 l/100 km) prices motorbike at the car rate times that ratio, under `choice` only. **Motorbike parking stays unpriced**: no observation of motorcycle parking charges.
- Target: G62 one-method motorbike/scooter journeys over one-method driver journeys on the target LGA's own SA1s — `CAL.mode_split.motorbike_driver_journey_share` = 0.0064151 (282 of 43,959), × `CAL.mode_split.vehicle_driver_level` 0.59 = 0.3785 % (§9.122, §9.115).
- The carve member, kept for `carve`: `B.motorbike.trip_share` = 0.0037849 by `B.motorbike.carve_resolution` = `sa1_thinned`, each LGA conserved to its own identity (§9.122, §9.140, #93); `_plans_report.json` records it `retired_by` `B.motorbike.representation = choice`.
- Physics: `B.motorbike.pce` = 0.4 (literature, sweep 0.3–0.75); `B.motorbike.length_m` = 2.2 held fixed as cosmetic in the queue model (§9.52).

**Resident truck drivers** are a person-level locked carve on the car-driver pool (§9.125): `CAL.mode_split.truck_driver_journey_share` = 0.0050729 (G62 Truck, 223 of 43,959, measured) and `B.truck.resident_trip_share` = 0.002993, `derived`; the pool excludes a person the binders named as a driver or as someone's passenger (§9.146, #93). Their trips count as `truck` in the twelve-mode table and at the count stations with the freight tier's vehicles.

**Freight** is a physical `truck` mode, a declared and sweepable background load rather than a freight demand model (§9.49).

- Vehicle: `B.freight.pce` = 2.0 (literature, sweep 1.5–3.5), `B.freight.max_speed_kmh` = 100 (definition), `B.freight.length_m` = 12.5 held fixed; `qsim.mainMode` carries `truck`, the vehicles file re-emitted per run (§9.49).
- Through tier: each cordon gate's volume splits car/truck by its own station's observed heavy share where classified (Hunter Expressway 0.1529) and `B.counts.heavy_vehicle_share` 0.0652 elsewhere, with the measured freight day factor (§9.49).
- Internal tier: `B.freight.trip_ratio` = 0.0697 (assumed, sweep 0.0–0.14; zero switches the tier off) × the observed car-driver share × the day's core person trips; origins and destinations on the census place-of-work attractor over `B.freight.attractor_divisions` with `B.freight.gravity_beta_per_km` = 0.08 (assumed, sweep 0.03–0.20); one agent is one one-way trip; `lockedMode=truck` in subpopulation `freight` (§9.49).
- Departure profile and weekend factors are measured from the classified hourly counts; truck routing is unconstrained — no truck-route, curfew or bridge-limit layer exists (§9.49).

**Freight rail** is deliberately not a mobsim vehicle: the coal chain runs on dedicated grade-separated track since 2006 and putting it on the passenger network would fabricate an interaction (§9.70). Its only road interaction — the two boom-gated level crossings — is built as time-variant link closures (§9.90).

- `A.crossings.representation` = `change_events`; `A.crossings.freight_road_names` = Saint James Road, Clyde Street (held fixed, §9.70); the Stewart Avenue tram crossing is excluded by `A.crossings.corridor_exclusion_m` = 500 (§9.90, §9.75).
- `A.crossings.closure_source` = `schedule_derived`: one closure per scheduled train whose mapped route traverses the crossing's rail links, timed from the nearest rail stop, read from the already-mapped feed, never a re-mapping; `assumed_uniform` with `A.crossings.closures_per_day` = 30 is the comparison member (§9.90).
- `A.crossings.freight_closures_per_day` = Saint James Road **44**, Clyde Street **48**, derived from the Cobbora survey (§9.167, #184), on top of the scheduled closures; every run's `_config.json` carries the values it loaded (§9.169).
- Durations are the survey's: `A.crossings.closure_duration_passenger_s` = 160 s per scheduled passenger train and `A.crossings.closure_duration_s` = 277 s per freight movement (§9.167), superseding the 60 s and 240 s of §9.90 and §9.70.

## What is measured

- **Motorbike reaches its target on F39's control, a RESULT at iteration 250** (§9.219, `report_mode_ridership.py --run 20260929T072135_250it_25pct --it 250`): **0.3629 % against 0.3785 %, −4.1 %** on 583 trips at a mean 12.38 km (+21 % against the observation), chosen at `C.asc.motorbike` 0.0 with availability by daily use (`B.motorbike.daily_use_ratio` 0.1801, ABS SMVU NSW Table 4; 6,368 persons, §9.218) and one household motorcycle (`RUN.qsim.motorcycle_roster`, 60 shared in the smoke). F38's +465.7 % on possession (§9.217) is the direction; truck **5.4694 %** network-wide, level only.
- **All three on F37's arm 0, a RESULT at iteration 250** (§9.214, `report_mode_ridership.py --run 20260926T002526_250it_25pct --it 250`): motorbike **0.3512 % against 0.3785 %, −7.2 %** on 532 trips at a mean 9.75 km, still the carve (coverage 0.23 %, a locked carve's riders holding no alternative); truck **6.0712 %** network-wide road-vehicle share, level only (24,025 departures; the target's basis is the count stations, `--truck-stations`, §9.101); freight rail **405 against 405**. Against F35's motorbike −5.6 % (§9.169) a direction, never a comparison (§3.5).
- **The carve delivers what it solves for** (§9.129, §9.140): the trip-weighted cell share conserves each LGA's own identity; the carve's reading moves by sampling alone, a −50 % at 10 % being a sampling statement, not a defect (§9.122).
- The reader counts the scheduled 313 PLUS the freight closures THE RUN carried (its own `_config.json`), 266 merged closure spans (§9.169).
- The truck basis (`--truck-stations`): link entries against `road_aadt_targets.csv`'s own heavy shares, 3 calibration stations, 20 of 24 classifying stations holdout and never opened (§9.101); the station target row is 15.4698% (sweep 13.7256–17.4013) of weekday vehicles at classified stations (`mode_targets_by_mode.csv`).
- **Freight rail:** 405 movements per weekday — Clyde Street 203 scheduled plus 48 freight, Saint James Road 110 plus 44 — peaked with the service (§9.90, §9.167); a representation check, not a fit (§9.90).

## What is open

- **`C.asc.motorbike` stays at 0.0, a placeholder never fitted** (§9.218, #258): the target is met with no constant; the open quantity is the trip length (12.38 km against the survey's, §9.219), which the next calibrated base reads, not a constant.
- **The truck yardstick is holdout-bound** (§9.101): scoring at the classifying stations spends holdout stations, and whether to open them for freight is the operator's decision. Counts themselves remain unfitted (#82).
- **The crossings' closure effect has never been measured** (§9.77, §9.90): every result carries the closures ON and no paired arm has carried them off.
- The target CSV's `freight_train` basis text says each closure is 240 s, while the registry closes a passenger train for 160 s and a freight movement for 277 s (§9.167) — the registry wins; the CSV text should be regenerated.
- Truck routing is unconstrained; the Mayfield precinct cap (1,268 movements/day) is recorded as an upper bound only, never a target (§9.70).

## Refused — do not re-raise

- **A truck choice model.** No preference observation exists; the share is declared, derived and swept; the day locks (§9.125). Motorbike is chosen by the user's decision on observed availability, with no invented constant (§9.214).
- **A separate motorbike network layer** (filtering, lane-splitting): inside the PCE sweep (§9.52).
- **Coal trains on the simulated rail network.** Grade-separated since 2006; adding them fabricates an interaction the real network does not have (§9.70).
- **Scoring truck on the network-wide share.** The target's own basis says it is not comparable (§9.101).
- **Pinning `freight_closures_per_day` on no evidence.** The 44 and 48 are derived from the published Cobbora survey (§9.167, #184).
- **A freight tour or depot structure.** No local observation supports one; one agent is one one-way trip (§9.49).
- **The core's G62 cell as the motorbike yardstick.** Every other target is the target LGA's (§9.122).

## History

- §9.219 — motorbike at its target
- §9.214 — motorbike chosen in F38
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
