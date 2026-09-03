# Motorbike, truck and freight rail — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 3 September 2026 · **Record read through:** §9.140 · **Open family:** F23 (the package on disk opens F24 at its first launch)

## What is built

**Motorbike** is a person-level locked carve from car-driver demand, not a choice mode (§9.52). A licensed, car-available resident is drawn by a hash of person id and master seed, and the whole day locks to `motorbike`; the escort-day fallback of §9.52 is retained. The carve draws no new trip: car loses exactly what motorbike gains (§9.52).

- Anchor: census G62 one-method motorbike/scooter journeys over one-method driver journeys, on the target LGA's own SA1s — `CAL.mode_split.motorbike_driver_journey_share` = 0.0064151 (282 of 43,959), measured and asserted against the extract on every build (§9.122).
- Share: `B.motorbike.trip_share` = 0.0037849, `derived` = `CAL.mode_split.vehicle_driver_level` 0.59 x the cell above; the carve share and the fit target are the same observation transferred by the same identity (§9.115, §9.122).
- Resolution: `B.motorbike.carve_resolution` = `sa1_thinned` — the identity applied per home SA1, falling back to the SA2 where the driver cell is under `B.census.thin_cell_min_journeys`; `region` is the sweep member (§9.122).
- Pool: the probability is solved on the persons who will actually be carved — eligible persons who are not escorters that day AND were not named as a driver by any binder pass (§9.122, §9.129). The current plans report `cells_at_sa1` 902, `cells_at_sa2` 799, core-wide trip-weighted cell share 0.002439 beside the declared target-LGA share 0.0037849 (`cities/newcastle/demand/plans/matsim/_plans_report.json`, §9.140).
- **Each LGA's cell shares are conserved to the LGA's own identity** (§9.140, #93): one factor per LGA makes the trip-weighted mean of its cells equal `CAL.mode_split.vehicle_driver_level` × the LGA's G62 ratio — Newcastle 0.8862 (intended 0.004271 → identity 0.003785), Maitland 0.9071, Lake Macquarie 0.9740, Cessnock 0.7244, Port Stephens 1.0649 (`_plans_report.json`, `lga_conservation`). The target LGA conserves to the DECLARED `B.motorbike.trip_share`; its SA1 cells summed read 0.0038289 (+1.2%, ABS small-cell perturbation), stated and refused only beyond 5%. The truck carve is a flat region probability that delivers its solve exactly and needs none (§9.140).
- Physics: `B.motorbike.pce` = 0.4 (literature, sweep 0.3–0.75); `B.motorbike.length_m` = 2.2 held fixed as cosmetic in the queue model (§9.52).

**Resident truck drivers** are carved by the same mechanism on the same pool, on their own hash namespace so the motorbike draws stay byte-identical; one lock per person, never both (§9.125).

- `CAL.mode_split.truck_driver_journey_share` = 0.0050729 (G62 Truck, 223 of 43,959, measured, asserted on every build) and `B.truck.resident_trip_share` = 0.002993, `derived` by the motorbike identity (§9.125).
- The carve's current solve: `q` 0.013358 against `declared_share` 0.002993 (`_plans_report.json`, `truck_carve`). Their trips count as `truck` in the twelve-mode table and at the count stations with the freight tier's vehicles (§9.125).

**Freight** is a physical `truck` mode, a declared and sweepable background load rather than a freight demand model (§9.49).

- Vehicle: `B.freight.pce` = 2.0 (literature, sweep 1.5–3.5), `B.freight.max_speed_kmh` = 100 (definition), `B.freight.length_m` = 12.5 held fixed; `qsim.mainMode` carries `truck`, the vehicles file is re-emitted per run from the run's own resolution (§9.49).
- Through tier: each cordon gate's volume splits car/truck by its own station's observed heavy share where classified (Hunter Expressway 0.1529) and `B.counts.heavy_vehicle_share` 0.0652 elsewhere, with the measured freight day factor (§9.49).
- Internal tier: `B.freight.trip_ratio` = 0.0697 (assumed, sweep 0.0–0.14; zero switches the tier off) x the observed car-driver share x the day's core person trips; origins and destinations on the census place-of-work attractor over `B.freight.attractor_divisions` with `B.freight.gravity_beta_per_km` = 0.08 (assumed, sweep 0.03–0.20); one agent is one one-way trip; `lockedMode=truck` in subpopulation `freight` (§9.49).
- Departure profile and weekend factors are measured from the classified hourly counts (§9.49). Truck routing is unconstrained: no truck-route, curfew or bridge-limit layer exists (§9.49).

**Freight rail** is deliberately not a mobsim vehicle. The coal chain runs on dedicated grade-separated track since 2006 and putting it on the passenger network would fabricate an interaction (§9.70). Its only road interaction — the two boom-gated level crossings — is built as time-variant link closures (§9.90).

- `A.crossings.representation` = `change_events`; `A.crossings.freight_road_names` = Saint James Road, Clyde Street (held fixed as the identity of the set, §9.70); the Stewart Avenue tram crossing is excluded by `A.crossings.corridor_exclusion_m` = 500 (§9.90 registry, rule of §9.75).
- `A.crossings.closure_source` = `schedule_derived`: one closure per scheduled train whose mapped route traverses the crossing's rail links, timed from that service's stop time at the nearest rail stop, read from the scenario's already-mapped feed, never a re-mapping (§9.90). `assumed_uniform` with `A.crossings.closures_per_day` = 30 is kept as the comparison member (§9.90).
- `A.crossings.freight_closures_per_day` = 0 (assumed, sweep 0–30): non-timetabled freight is declared on top and is zero on the recorded evidence, not for want of a number (§9.90).
- Durations: `A.crossings.closure_duration_passenger_s` = 60 per scheduled passenger train (literature, sweep 30–120); `A.crossings.closure_duration_s` = 240 for a freight movement (assumed, sweep 60–600, §9.70's "up to ten minutes").

## What is measured

- **Motorbike, the F22 gate** (`aborted_20260831T165127_300it_25pct`, iteration 100, 25% sample): 0.4287% against 0.3785% (+13.3%), flat across the arm (§9.136, #93). The F21 gate's +24.6% at 10% (§9.134) carried more sampling noise; the 25% reading sits near the plans' own 0.4459% delivery.
- **The per-LGA split #93 asked for is taken, and it explains the over-delivery** (§9.136): the draw and the §9.129 pool solve are exact per LGA (delivered/intended 0.94–1.13, ~1.00 everywhere), but the `sa1_thinned` cell shares themselves aggregate **above** the LGA identity when weighted by synthetic trips — intended 0.4271% against Newcastle's 0.3829% identity (+12%), +10% Maitland, +38% Cessnock, +9% core-wide. The bias is the cell aggregation, not the draw; the fix is per-LGA conservation of the cell shares, covering the truck carve identically (§9.125) — a demand rebuild, queued behind the F22 gate's own cause.
- **The carve now delivers what it solves for:** 5,937 trips on 1,687 persons = 0.2666% of WEEKDAY resident trips against 0.2654% solved, the per-cell identity's core-wide trip-weighted value (§9.129). Before the pool repair it delivered 0.153%, 58% of the solve, because named drivers held 42.1% of the pool's trips (§9.129).
- **Precision:** a 10% arm reads motorbike off a few tens of persons; a −50% at that depth was a sampling statement, not a defect (§9.122).
- **Truck, network-wide:** 5.61% of modelled road vehicles at the F22 gate (iteration 100, §9.136), falling as resident car trips grew. That basis is NOT the target's and no deviation is printed for it (§9.101).
- **Truck at the classifying stations, F22 gate** (§9.136): 6.14% modelled against the 3 calibration stations' own observed 11.31% (−45.7%) on the 25% sample — thicker n than F21's −51.0% at 10% (§9.135) and still far below the F13 like-for-like +5.4% (§9.101); the freight tier under the fare-priced demand is #82's open question.
- The basis (`--truck-stations`): link entries against `road_aadt_targets.csv`'s own heavy shares, 3 calibration stations, 20 of 24 classifying stations holdout and never opened (§9.101); the station target row is 15.4698% (sweep 13.7256–17.4013) of weekday vehicles at classified stations (`mode_targets_by_mode.csv`). The F13 like-for-like read +5.4% at iteration 100 of `20260829T172145_1000it_10pct` (§9.101).
- **Freight rail:** 314 closures per weekday — Clyde Street 204, Saint James Road 110 — 3,014 change events, peaked with the service (§9.90). The `freight_train` target row is 314 on that same denominator; it is a representation check, not a fit (§9.90).

## What is open

- **#93 (awaiting-run)** — the conservation fix is built and the plans rebuilt on it (§9.140); what closes it is a gate reading at or under the identity on the F24 package.
- **The truck yardstick is holdout-bound** (§9.101): scoring at the classifying stations spends holdout stations, and whether to open them for freight is the operator's decision. Counts themselves remain unfitted (#82).
- **#68 is still open on GitHub** though the crossings are built and activated (§9.77, §9.90); it should close on the record or state what remains.
- The target CSV's `freight_train` basis text says each closure is 240 s, while the registry closes a passenger train for `A.crossings.closure_duration_passenger_s` = 60 s — the registry is the newer statement and wins; the CSV text should be regenerated.
- Truck routing unconstrained; no port-gate constraint is enforced — the Mayfield precinct cap (1,268 movements/day) is recorded as an upper bound only, never a target (§9.70).

## Refused — do not re-raise

- **A motorbike or truck choice model.** No preference observation exists; an invented constant is what §8.5 forbids. The share is declared, derived and swept; the day locks (§9.52, §9.125).
- **A separate motorbike network layer** (filtering, lane-splitting): inside the PCE sweep (§9.52).
- **Coal trains on the simulated rail network.** Grade-separated since 2006; adding them fabricates an interaction the real network does not have (§9.70).
- **Scoring truck on the network-wide share.** The target's own basis says it is not comparable; a −49.6% quoted on it was two populations, not an error (§9.101).
- **Pinning `freight_closures_per_day` above zero without a log.** ARTC publishes none; the remainder is swept, not asserted (§9.90).
- **A freight tour or depot structure.** No local observation supports one; one agent is one one-way trip (§9.49).
- **The core's G62 cell as the motorbike yardstick.** Every other target is the target LGA's; the split reads the LGA's own SA1s (§9.122).

## History

- §9.140 — carve conserved per LGA, rebuilt
- §9.136 — carve bias is the cell aggregation
- §9.134 — F21 gate: motorbike +24.6%
- §9.131 — licence rate rebuilt, carves await rebuild
- §9.129 — carves solved on drawn pool
- §9.126 — F18 built both carves
- §9.125 — resident truck-driver carve built
- §9.122 — escort denial before draw; LGA cell
- §9.116 — carve fix committed without rebuild
- §9.115 — carve and target one identity
- §9.112 — carve told one share, scored another
- §9.101 — truck scored at its own stations
- §9.90 — crossings derived from the timetable
- §9.77 — crossing closures activated in runs
- §9.70 — coal chain scoped out; crossings named
- §9.52 — motorbike carved as physical mode
- §9.49 — freight enters as physical truck
