# Taxi and rideshare — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Two runs are results - F32's `20260909T015217_300it_25pct` and F35's arm 0 `20260912T202242_300it_25pct`, each `completion` `ran_to_last_iteration` at iteration 300 (§9.162, §9.169); nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 14 September 2026 (forty-eighth session) · **Record read through:** §9.171 · **Written against family:** `F35`

## What is built

- **A refused request is routed as a walk by the engine itself, and the taxi trip comes back whole** (§9.168, F35): a NULL-route walk leg had `PersonPrepareForSim` re-route the WHOLE plan every iteration (24 % of CPU, `20260912T162831_4it_25pct`). `TaxiFleetEngine.remodeRefused` routes the refused trips on `global.numberOfThreads` workers after the fleet pass (45,573 in 61 s at 25 %, `20260912T185005_4it_25pct`), inserts them in refusal order and restores the original taxi trip after the mobsim. Under `accessEgressModeToLink` the trip is found by routing mode and replaced whole (§9.167, #167).
- **One mode, `taxi`, standing for taxi and rideshare together**, blended at `B.taxi.rideshare_trip_share` 0.66 (IPART 2025 last-trip split, swept 0.4–0.8, §9.76); no observation splits them (§9.21, §9.42).
- **It is a physical vehicle on the road**: `taxi` is in `RUN.qsim.main_mode`, `RUN.mode_choice.modes` and `RUN.routing.network_modes`; its body restates `RUN.qsim.car_vehicle`, PCE 1.0 (§9.86, F11); travel time is bound to the congested car network (§9.77).
- **It is served by a finite fleet.** `A.taxi.fleet_representation` = `finite_fleet` (`absent` reproduces every arm before §9.99). `citysim.TaxiFleetEngine` (`src/java/citysim/TaxiFleetEngine.java`) collects every taxi leg at `BeforeMobsim`, sorts by departure and serves greedily from the earliest-free vehicle (§9.99, F13).
- **A refused request walks this iteration, and the mode is restored at `AfterMobsim`** — a refusal never deletes the alternative (§9.99, §9.81). The restore RE-FINDS the trip by its endpoints through `citysim.RemodeRestore`, shared with the ride engine (§9.141, #113). Nothing caps the share; the constraint is supply and price (§9.99).
- **The fleet is derived**: `B.taxi.fleet_size` 800 at full scale = mean of `B.taxi.daily_trips_band` [15000, 25000] / `B.taxi.vehicle_trips_per_day` 25 (literature, swept 15–35, the one free quantity), scaled by `qsim.flowCapacityFactor` (§9.99, §9.88).
- **Fleet timing**: `B.taxi.max_wait_min` 20 (assumed, swept 10–45), the abandonment tail that makes the fleet bind; `B.taxi.deadhead_min` 12 (assumed, swept 0–30), empty running as unavailable time (§9.99).
- **Fares** (`cities/newcastle/registry/B_demand.json`): `B.taxi.flagfall_taxi` 5.00 and `B.taxi.fare_per_km_taxi` 2.52, `measured` from the Point to Point Transport (Fares) Order 2025 at `data/raw/p2p/`; `B.taxi.flagfall_rideshare` 1.95 and `B.taxi.fare_per_km_rideshare` 1.50, `literature`, swept. Surge, night rates, the peak surcharge and the levy are recorded and not charged (§9.76).
- **Choice constants**: `C.taxi.wait_min` 5.0 (swept 2–12) and `C.taxi.asc` 0.0 swept over the negative half-axis (§9.76); with a fleet, waiting beyond that constant emerges from supply (§9.94, §9.99).
- **Age gate**: `B.taxi.min_unaccompanied_age` 18 (assumed, swept [0, 18], zero disables), through `modeAvailability` and the plans builder (§9.84, §9.120); `GatedSubtourModeChoice` closes the single-trip seam that let under-18s hail 5.5 % of taxi trips (§9.84).
- **Target**: `taxi` 0.9916 % of resident linked trips, `derived`, sweep 0.7437–1.2395 % (`data/processed/validation/mode_targets_by_mode.csv`): the IPART band against 2,017,000 study-area weekday trips × `CAL.taxi.lga_concentration` 1.0 (assumed, swept to 2.0) (§9.91). Bike takes the residual of the HTS "Other" fold, so the two targets move together (§9.91, §9.87).
- **The calibration loop reaches taxi** (§9.158): a declared `matsim_param` binding is evidence of run-time realisability, and the movable set (5 → 21) includes `B.taxi.deadhead_min`, `B.taxi.max_wait_min`, `B.taxi.min_unaccompanied_age`, `C.taxi.asc` and `C.taxi.wait_min` (`python src/calibrate/calibrate.py --run-config f29_gate_25pct --plan`).
- **Taxi is deliberately absent from the ASC fixed point** (§9.158): `CAL.asc.mode_to_constant` omits taxi because `fit.py` folds bike and taxi into one survey category, so taxi has no independent target to invert.

## What is measured

- **The F35 result: taxi 2.2948 % against 0.9916 %, +131.4 %, stop** (`20260912T202242_300it_25pct` at iteration 300, §9.169): **3,636** resident trips at a mean **9.34 km (+80 % on the HTS category)**, coverage **53.72 %** — 2.3× target with 51 pp of headroom, so not a choice-set finding. The planned share fell **9.67 → 2.00 %** over the run (`modestats.csv`) and drifted −0.097 pp between 250 and 300: a relaxed level, not a moving curve. A direction, not a comparison with F32 (§3.5).
- **Refusals are no longer the mechanism behind taxi's excess** (§9.169): at iteration 300 the fleet of 200 refused **2,065 requests an iteration, about 18 % of 11,409**, every one routed as a network walk in **1.3 s**, against 47,797 of 58,558 (81.6 %) on the F34 probe `20260912T162831_4it_25pct`. Four requests in five served, and taxi still reads 2.3× its target.
- **Taxi is available to half the population, on both results** (§9.163, §9.169): F32 coverage **54.62 %** against a **2.9971 %** share, headroom 51.62 pp, the largest on the board; arm 0 53.72 % against 2.2948 %. Its choice set closed at iteration **27**.
- **The excess is a level, not a basis or a supply artefact** (§9.163): 11,633 modelled trips on F32 scale to **46,532** daily against a band of 15,000–25,000; mean trip **8.6463 km** on 4,639 target-LGA trips; `snap_pp` **−0.583**, so the cutoff moved taxi TOWARD its target.
- **The F32 result: taxi 2.9971 % against 0.9916 %, +202.2 %, mean trip 8.58 km** (`20260909T015217_300it_25pct` at iteration 300, §9.162): one of two modes whose direction was AWAY across the run (+88.5 % at it.0, +178.7 % at 200, +202.2 % at 300); depth makes taxi worse, so the excess is not an unconverged search. Comparable with no earlier family (§3.5).

## What is open

- **The cause of the remaining excess is open** (§9.169, #49). Arm 0 rules out refusals (18 %) and an unconverged search (planned share settled at 2.00 %), and the fare is not a lever (§9.91, Refused). Left: `B.taxi.max_wait_min` and `B.taxi.deadhead_min` are movable and `B.taxi.vehicle_trips_per_day` is the sweep §9.99 named — it moves the fleet by 2.3×, and a smaller fleet can only refuse more. No arm since F13 has run `absent` to measure the fleet's own effect (§9.99). A result at 300 reads relaxed (drift −0.097 pp), so the within-run drift of §9.158 no longer bars scoring a candidate.
- **The refused-request fallback is still walk**, costing 1.3 s an iteration at 18 % refusal on arm 0 (§9.169), down from ~60 s at 81 % on the F34 probe (§9.168, §9.105). Whether taxi should take `B.ride.unpaired_fallback`'s member is undecided.
- **Two stated simplifications**: empty running loads no link, and there is no spatial dispatch; `B.taxi.deadhead_min` stands in for both (§9.99). A full demand-responsive fleet would add the routed empty legs (§9.86, §9.99).
- **The IPART user incidence is consumed outside the package** to build `B.taxi.daily_trips_band`; `data/raw/p2p/` holds the Fares Order only (§9.94). Acquiring the incidence is the honest route to person-level availability.
- **The target is derived and weak** — a band, not a count — and the mean-distance yardstick (5.2 km) is the folded HTS "Other" figure shared with bike (`data/processed/validation/mode_targets_by_mode.csv`, §9.42).
- Umbrella issue #49 stays open for the converged measurements; #88 (physicality) and #90 (supply) are closed.

## Refused — do not re-raise

- **Separate taxi, rideshare or carshare modes.** No observation decomposes them (§9.21, §9.42).
- **A data request to the Point to Point Transport Commissioner for levy counts.** The band constrains; it does not become a measured count (§9.42).
- **A person-level `taxiAvail` sized to land the target**: fitting the availability to the answer (§9.94).
- **The DRT/DVRP contrib**: a toolchain change absent from the pinned stack; the fleet was built at `BeforeMobsim` instead (§9.99).
- **Reaching for the beyond-12 km fare tail as a lever**: the departure condition is met (median 13,072 m, §9.91), but the tail is 2.29 against 2.52 AUD/km, so it moves taxi away from target; a fidelity change, not a fit (§9.91).
- **A separate taxi vehicle body, or an assumed empty-running multiplier.** Neither has an observation behind it (§9.86).
- **Reading a moving curve as a level.** Two readings in one investigation were wrong this way (§9.91).
- **A refusal that deletes the alternative.** The one-way ratchet (§9.81, §9.99).

## History

- §9.170 — the tenth report re-reads arm 0 unchanged
- §9.169 — arm 0: taxi +131.4 %, refusals 18 %
- §9.168 — the refused walk is routed by the engine; 81 % refused at 25 %
- §9.167 — the refusal re-modes the whole trip
- §9.166 — the fare probe did reach the run; P2P counts refused by 9.42
- §9.163 — taxi has 51.6 pp of headroom; the excess is a level
- §9.162 — the first result: taxi +202.2 %, still moving away
- §9.158 — the loop reaches taxi's supply and price; reading point drifts
- §9.157 — F31 gate: taxi +178.4 %
- §9.141 — refused trip restored by endpoints
- §9.139 — F23 gate: band widens to +77 %
- §9.134 — F21 gate: taxi flat at +67 %
- §9.126 — F17 held taxi at +52 %
- §9.121 — seed flood refused, then decays
- §9.120 — taxi is a fleet-size question
