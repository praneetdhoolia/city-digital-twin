# Taxi and rideshare — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. The depth arm `20260909T015217_300it_25pct` IS a result - `completion` `ran_to_last_iteration` at iteration 300 (§9.162), the first since family F4; nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 12 September 2026 (forty-fourth session) · **Record read through:** §9.167 · **Written against family:** `F34`

## What is built

- **A refused request walks the WHOLE trip, and the engine finds its trips by routing mode** (§9.167, #167): under `accessEgressModeToLink` `TaxiFleetEngine.refuse` found no taxi trip at all (it matched the leg's mode, and the trip's identity is its routing mode) and re-moded one leg where it did; both go through `RemodeRestore.remodeTrip` now.
- **One mode, `taxi`, standing for taxi and rideshare together.** It blends the two services at `B.taxi.rideshare_trip_share` 0.66 (IPART 2025 last-trip split, swept 0.4–0.8, §9.76). The two are never separate modes: no observation splits them (§9.21, §9.42).
- **It is a physical vehicle on the road.** `taxi` is in `RUN.qsim.main_mode`, `RUN.mode_choice.modes` and `RUN.routing.network_modes`; its body restates `RUN.qsim.car_vehicle` exactly, PCE 1.0, because a hired car is a car (§9.86, family F11). Travel time is bound to the congested car network so a taxi cannot out-run the traffic it rides in (§9.77).
- **It is served by a finite fleet.** `A.taxi.fleet_representation` = `finite_fleet` (members `absent`, `finite_fleet`; `absent` reproduces every arm before §9.99). `citysim.TaxiFleetEngine` (`src/java/citysim/TaxiFleetEngine.java`) collects every taxi leg at `BeforeMobsim`, sorts by departure, and serves greedily from the earliest-free vehicle, which is the fleet's best case (§9.99, family F13).
- **A refused request walks this iteration, and the mode is restored at `AfterMobsim`** — a refusal never deletes the alternative (§9.99, carrying §9.81's rule). The restore RE-FINDS the trip in the selected plan by its endpoints through `citysim.RemodeRestore`, shared with the ride engine, and logs what it found (§9.141, #113 closed): the engine once restored through the leg object it had stored, which the router had replaced, so every refused trip stayed walk in plan memory. Nothing caps the share; the constraint is supply and the price (§9.99).
- **The fleet is derived, not declared.** `B.taxi.fleet_size` 800 at full scale = mean of `B.taxi.daily_trips_band` [15000, 25000] trips/day divided by `B.taxi.vehicle_trips_per_day` 25 (literature, swept 15–35, the one free quantity) (§9.99). The engine scales the fleet by `qsim.flowCapacityFactor`, for the reason the SCATS saturation flow is scaled (§9.99, §9.88).
- **Fleet timing:** `B.taxi.max_wait_min` 20 (assumed, swept 10–45) is the abandonment tail that makes the fleet bind; `B.taxi.deadhead_min` 12 (assumed, swept 0–30) is empty running as unavailable time, not a routed leg (§9.99).
- **Fares** (`cities/newcastle/registry/B_demand.json`): taxi `B.taxi.flagfall_taxi` 5.00 and `B.taxi.fare_per_km_taxi` 2.52, both `measured` from the Point to Point Transport (Fares) Order 2025 urban schedule archived at `data/raw/p2p/` (§9.76); rideshare `B.taxi.flagfall_rideshare` 1.95 and `B.taxi.fare_per_km_rideshare` 1.50, `literature`, swept (§9.76). Surge, night rates, the peak surcharge and the passenger service levy are recorded and deliberately not charged (§9.76).
- **Choice constants:** `C.taxi.wait_min` 5.0 (the typical wait priced into the constant, swept 2–12) and `C.taxi.asc` 0.0 swept over the negative half-axis (§9.76). With a fleet, waiting beyond that constant now emerges from supply (§9.94, §9.99).
- **Age gate:** `B.taxi.min_unaccompanied_age` 18 (assumed, swept [0, 18], zero disables), consumed through the `modeAvailability` module and, since §9.120, by the plans builder (§9.84). `GatedSubtourModeChoice` closes the stock single-trip seam that let under-18s hail 5.5% of taxi trips (§9.84).
- **Target:** `taxi` 0.9916% of resident linked trips, status `derived`, sweep 0.7437–1.2395%, in `data/processed/validation/mode_targets_by_mode.csv`: the IPART band against 2,017,000 study-area weekday trips, times `CAL.taxi.lga_concentration` 1.0 (assumed, swept upward only to 2.0) (§9.91). Bike takes the residual of the HTS "Other" fold, so the two targets move together (§9.91, §9.87).

- **THE CALIBRATION LOOP CAN NOW REACH TAXI, WHERE BEFORE IT REACHED NOTHING** (§9.158). `rebuild_stage` excluded any field whose consumer's basename it did not classify, including fields carrying a declared `matsim_param` binding that reach the emitted config on every run; a binding is now evidence of run-time realisability and the movable set went **5 → 21**. It includes `B.taxi.deadhead_min`, `B.taxi.max_wait_min`, `B.taxi.min_unaccompanied_age`, `C.taxi.asc` and `C.taxi.wait_min` — the whole supply-and-price axis §9.99 named as the lever. Verify with `python src/calibrate/calibrate.py --run-config f29_gate_25pct --plan`.
- **TAXI IS DELIBERATELY ABSENT FROM THE ASC FIXED POINT** (§9.158). `CAL.asc.mode_to_constant` maps board modes to constants and omits taxi on purpose: `C.taxi.asc` exists, but `fit.py` folds bike and taxi into one survey category, so **taxi has no independent target**, there is no ratio to invert, and a fixed-point step would fit a constant to a number that is not there. Truck and freight rail are absent because neither is a mode choice.

## What is measured

- **TAXI IS AVAILABLE TO HALF THE POPULATION AND CHOSEN BY THREE PER CENT OF TRIPS** (§9.163). On `20260909T015217_300it_25pct` at iteration 300, taxi's choice-set coverage is **54.62 %** of agents against a **2.9971 %** share — a headroom of **51.62 pp**, the largest of any mode on the board. Taxi's **+202.2 %** is therefore comfortably inside what a constant could move in either direction, and is not a choice-set finding. Its choice set closed at iteration **27**.
- **The excess is a level, not a basis or a supply artefact** (§9.163). 11,633 modelled taxi trips scale to **46,532** daily against a constraint band of 15,000–25,000, outside it; modelled mean trip **8.6463 km** on 4,639 target-LGA trips. Taxi's `snap_pp` at the innovation cutoff is **−0.583**, so it is one of the modes the cutoff moved TOWARD its target rather than away.
- **THE FIRST RESULT: taxi 2.9971 % against 0.9916 %, +202.2 %, mean modelled trip 8.58 km** (`20260909T015217_300it_25pct` at iteration 300, `ran_to_last_iteration`, §9.162). **Taxi is one of only two modes whose direction was AWAY across the run** (the other is light rail): it rose from +88.5 % at iteration 0 through +178.7 % at 200 to +202.2 % at 300, and the cutoff took **−0.583 pp** off it without reversing the trend. Depth makes taxi worse, so its excess is not an unconverged search. Comparable with no earlier family (§3.5).
- **TAXI IS ONE OF THE THREE MODES THE READING POINT CANNOT RESOLVE** (§9.158). Between iteration 80 and 100 of the SAME run, with nothing changed, taxi's deviation moves further than the WHOLE 10 % acceptance band on **3 of the 6** arms that ever reached 100 — **15.72 points on the F31 arm itself**, the largest single-mode drift that arm shows (`CAL.search.reading_drift_pct`, `python src/analyse/measure_reading_stability.py --all --from 80 --to 100`). A taxi level read at 100 is partly a statement about how far the run had got.
- **Gate reading, F23 iteration 100: taxi 1.75% against 0.99%, +76.6%, flat at 1.52–1.75% across the arm, mean trip 12.82 km** (`results/processed/aborted_20260901T165115_300it_25pct/modes_final.json`, §9.139 - the arm's bulk was reclaimed once its findings were extracted, #164). The flat band has now widened slightly at each pricing change it did not share in: F21 +67.4% (§9.134), F22 +70.9% under pt fares (§9.136), F23 +76.6% under income-scaled money sensitivity (§9.139, #108) — everything else got costlier or its cost got lighter for the rich; taxi's meter did not move.
- **F17 iteration 50 read 1.51% (+52%)**, flat while car and walk converged (§9.126); every arm since F15 reads taxi flat between +36% and +67% (§9.120, §9.126, §9.134).
- **The fleet binds under load and relaxes when it does not:** probe `20260829T171626_2it_1pct` refused 24 of 274 requests (8.8%) at iteration 1 and none of 177 at iteration 2 (§9.99). Under the full-choice-set seed the iteration-0 flood is 34,870 requests with 85.7% refused, decaying as plans are scored (§9.121).
- **The fare binds, hard.** The per-kilometre rate moved taxi elevenfold on the `taxi_fare_stress_1pct` / `taxi_fare_control_1pct` pair (`cities/newcastle/overlays/runs/`), while the innovation cutoff moved it about 11% (§9.91).
- **Before the fleet, price alone left taxi at about 6% at 1% sample, 7.52% even among agents holding a car and a licence**: car is chain-based, so a perturbed subtour cannot use it, and taxi won the trips where nothing else said no (§9.91, §9.94).
- **Physicality:** 197 of 197 taxi departures enter traffic on `20260828T220751_2it_1pct`, against 0 before F11 (§9.86).
- **The median modelled taxi trip is 13,072 m**, which contradicts the premise of the held-fixed rule on `B.taxi.fare_per_km_taxi` (§9.91); see Refused.

## What is open

- **The fare stress probe DID reach the run** (§9.166): `taxi_fare_stress_1pct` set both per-km fares in a run overlay, and the emission test of the new override refusal confirms `config_runtime`'s blend carries them into `monetaryDistanceRate` at launch — the calibrator's stage table, which classes every field `build_matsim_run_inputs.py` consumes as needing the run inputs rebuilt, is too coarse for the fields `config_runtime` derives. A study-area trip COUNT remains the observation taxi lacks: the P2P Commissioner's levy counts are unpublished and were refused as a request at §9.42; the IPART consultant report is acquirable into `data/raw/p2p/` (eighth report, factor lane).

- **The remaining excess is a fleet-size question, and the loop can now reach it** (§9.99, §9.158): `B.taxi.max_wait_min` and `B.taxi.deadhead_min` are movable, and `B.taxi.vehicle_trips_per_day` remains the lever §9.99 named — a sweep, not a fit. **But the reading point cannot yet score a candidate on taxi** (15.72 points of within-run drift at the F31 gate, §9.158), so a search over them is refused until the reading changes. `B.taxi.vehicle_trips_per_day` is the lever, and it is a sweep, not a fit: it moves the fleet by a factor of 2.3 (§9.99). No arm since F13 has been run with `absent` to measure the fleet's own effect (§9.99).
- **The refused-request fallback is still walk.** §9.105 replaced ride's unpaired fallback with `B.ride.unpaired_fallback` = `licensed_drive_else_walk` and named the same walk for a refused taxi; the taxi engine still walks a refusal (`src/java/citysim/TaxiFleetEngine.java`). Whether taxi should take the same member is undecided.
- **Two stated simplifications:** empty running loads no link, and there is no spatial dispatch; `B.taxi.deadhead_min` stands in for both (§9.99). A full demand-responsive fleet would add the routed empty legs (§9.86, §9.99).
- **The IPART user incidence is consumed outside the package** to build `B.taxi.daily_trips_band`; `data/raw/p2p/` holds the Fares Order and nothing else (§9.94). Acquiring the incidence is the honest route to any person-level availability.
- **The target is derived and weak** — a band, not a count — and the mean-distance yardstick (5.2 km) is the folded HTS "Other" figure shared with bike, so a deviation against it is not independent evidence about taxi (`data/processed/validation/mode_targets_by_mode.csv`, §9.42).
- Umbrella issue #49 stays open for the converged measurements; #88 (physicality) and #90 (supply) are closed.
- **Every taxi reading to date was taken under the orphaned-restore defect** (#113 closed, §9.141): a refused trip stayed walk permanently, so the F21–F23 taxi levels (+67 % to +77 %, §9.134–§9.139) were read with the alternative amputated; the F24 arm is the first reading with the restore working, and `citysim.RemodeRestoreProbe` (`python src/run/run_signal_probes.py`) proves the re-find without a run.

## Refused — do not re-raise

- **Separate taxi, rideshare or carshare modes.** No observation decomposes them (§9.21, §9.42).
- **A data request to the Point to Point Transport Commissioner for levy counts.** The project infers the volume from open sources; the band constrains, it does not become a measured count (§9.42).
- **A person-level `taxiAvail` sized to land the target.** That is fitting the availability to the answer, §9.92's error in another costume (§9.94).
- **The DRT/DVRP contrib.** A toolchain change, absent from the pinned stack; the fleet was built at the `BeforeMobsim` boundary instead, and §9.94's "blocked" conclusion is withdrawn (§9.99).
- **Reaching for the beyond-12 km fare tail as a lever.** The rule's departure condition is met (median 13,072 m, §9.91), but the tail is 2.29 against 2.52 AUD/km, so modelling it makes a long trip cheaper and moves taxi away from target; it is a fidelity change to be made deliberately, not a fit (§9.91).
- **A separate taxi vehicle body, or an assumed empty-running multiplier.** Neither has an observation behind it (§9.86).
- **Reading a moving curve as a level.** Two readings in one investigation were wrong this way (§9.91).
- **A refusal that deletes the alternative.** The one-way ratchet (§9.81, §9.99).

## History

- §9.167 — the refusal re-modes the whole trip
- §9.166 — the fare probe did reach the run (config_runtime); P2P counts refused by 9.42
- §9.163 — taxi has 51.6 pp of headroom; the excess is a level
- §9.158 — the loop reaches taxi's supply and price; no ASC step, no independent target
- §9.162 — the first result: taxi +202.2 %, and still moving away
- §9.157 — F31 gate: taxi +178.4 %
- §9.141 — refused trip restored by endpoints
- §9.139 — F23 gate: band widens to +77%
- §9.134 — F21 gate: taxi flat at +67%
- §9.126 — F17 held taxi at +52%
- §9.121 — seed flood refused, then decays
- §9.120 — taxi is a fleet-size question
- §9.105 — refused taxi walked into walk excess
- §9.99 — finite fleet, refused request walks
- §9.94 — supply is the cause; fleet blocked
- §9.91 — IPART band replaces census target
