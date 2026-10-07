# Seed and choice set — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 8 October 2026 (sixty-fifth session) · **Record read through:** §9.220 · **Written against family:** `F39`

## What is built

- **Both plan-removal paths honour `RUN.replanning.plan_selector_for_removal`** (§9.166, #174): `EscortCoherenceListener.trim()` injects the selector MATSim binds and re-selects at random if it took the selected plan (`tests/unit/test_plan_removal_one_selector.py`); `GatedSubtourModeChoice` treats a plan whose subtour decomposition throws as MIXED.
- **A seeded plan carries PER-TRIP modes** (§9.143): a partially bound tour rides its covered leg while the rest takes `B.mode.partial_bind_base` = `pt`, so §9.119's chain/non-chain mix is unreachable. Plan memory peaks at 7 of `RUN.replanning.max_agent_plan_memory` = 8; `check_package.py` reads the cap from the registry.
- **The seed is the choice set.** `B.mode.seed_method` = `full_choice_set` (§9.120): `src/build/build_matsim_plans.py` writes one plan per mode the person may use plus one riding the covered tours where a driver is named; each mode once. WEEKDAY carries 2–6 plans per person, 9,880,427 seeded legs against 2,343,321 selected (§9.126).
- **`uniform_draw` is the sweep alternative** (`B.mode.seed_split`); `B.mode.seed_split_informed` is declared, never the default (§9.120).
- **The first-executed plan is drawn uniformly** by sha256 of `seedorder|<pid>|20260810` (`src/build/build_matsim_plans.py`), carried as `selected="yes"`, so iteration 0 is a mixed traffic state (§9.121).
- **Plan memory** `RUN.replanning.max_agent_plan_memory` = 8 (sweep 3–10, §9.120): MATSim executes an unscored plan first and `WorstPlanForRemovalSelector` drops an unscored plan first, so memory must exceed the seeded plan count.
- **Mode choice** is `SubtourModeChoice` wrapped by `citysim.GatedSubtourModeChoice`: `RUN.mode_choice.modes` car, ride, pt, bike, walk, taxi; `chain_based_modes` car, bike; `consider_car_availability` true; `subtour_behavior` betweenAllAndFewerConstraints; `proba_random_single_trip_mode` 0.5 (§9.92); `coord_distance_m` 100 (§9.119).
- **Strategy mix** `RUN.replanning.weights`: ChangeExpBeta 0.7, ReRoute 0.15, SubtourModeChoice 0.1, TimeAllocationMutator 0.05 (`RUN.replanning.time_mutation_range_s` 1800; `strategy_subpopulations` limits SubtourModeChoice to `person`); the gate and the listeners propose, never impose (§9.92).
- **A leaf subtour mix is repaired at the seed** (§9.140, #96): `leaf_mixed_tours()` reproduces `TripStructureUtils.getSubtours` and drives the offending free tour of a car-available person's variant. Rebuilt plans: WEEKDAY 3 tours on 1 person, SAT 9 on 2, SUN 0 (`_plans_report.json`).
- **The gate refuses a proposal whole** and restores the pre-innovation plan: a trip beyond `B.mode.walk_feasible_km` / `bike_feasible_km` (0.0, inert, §9.106); a subtour mixing chain and non-chain modes (§9.119); `ride` outside `boundRideTrips` or a declared driver off `car` in `boundDriveTrips` (§9.120); a plan that ARRIVES mixed is stood aside while `ReRoute` still runs (#96).
- **Escort and joint coherence listeners** offer a decohered bound pair its coherent plan at `B.ride.escort_coherence_rate` / `B.ride.joint_coherence_rate` = 0.4 (§9.93), converting at the ROOT subtour (§9.118).
- **Innovation cutoff** `RUN.replanning.fraction_to_disable_innovation` = 0.8, sweep 0.7–0.9 (§9.7); at the cutoff selection concentrates onto the best remembered plan in ONE iteration (§9.43).
- **The escort listener no longer innovates past the cutoff** (§9.158): it reads `getFractionOfIterationsToDisableInnovation()` and past it measures decoherence and proposes nothing, so `summarise_run.relaxation`'s tail is genuinely innovation-free; arm 0's verdict rests on it (§9.169). No earlier verdict is retracted.
- **Iteration count** `RUN.controler.last_iteration` = **250** (§9.169; sweep 250–2000, §9.43): innovation off at 200, on arm 0's post-settle drift ≤ 0.128 pp; every result since F35's pairs ran 250 (§9.176–§9.219). `run_matsim.py --iterations` has no default.
- **A pt request with no transit route is bounded** (§9.218, §9.219): `RUN.transit_router.no_route_walk` = `refused_beyond_reach` scores a no-route walk over 3,223.6 m as an unexecutable plan, so selection drops it (plans holding one 9,517 → 398 over F39's control); the no-route share itself (47.6 %) is geography ([public-transport-and-yardsticks](public-transport-and-yardsticks.md)).
- **Relaxation instrument**: `RUN.relaxation.settle_margin_iterations` = 10 (sweep 1–100), `RUN.relaxation.drift_tolerance_pp` = 0.5 (sweep 0.1–1.0); `src/analyse/summarise_run.py` reports `snap_pp`, `drift_pp` (the verdict) and `cutoff_to_final_pp` (§9.43).
- **The gate is read on the trend, not the level**, against a scored choice set (§9.108, §9.120): `src/analyse/report_mode_ridership.py` over `src/analyse/iteration_trips.py`.
- **Choice-set coverage is an instrument, and the gate carries its bound** (§9.163, §9.177): `src/analyse/report_choice_set_coverage.py` reads `modeChoiceCoverage1x.txt`, which counts the share of TRIPS that ever executed a mode (at iteration 0 the pair's file reads ride 0.1415, the seeded plans' share — not a share of agents, as §9.163 and §9.169 read it); `coverage − share` is the most any constant can add, printed beside every verdict. Locked carves and boardings targets get no bound.
- **Score averaging is declared, shipped OFF, and measured to move nothing** (§9.163, §9.177, D7): `RUN.replanning.score_msa_representation` = `absent` (`absent` | `at_innovation_cutoff`, `sweep_role: answer`), `RUN.replanning.score_msa_fraction` bound to `scoring.fractionOfIterationsToStartScoreMSA`; the scoring pair ran `at_innovation_cutoff` as its one field and the roots rebuild's arm 0 keeps `absent`.
- **The choice-set branch has a control** (§9.164, #174, #155): `RUN.replanning.plan_selector_for_removal` = `WorstPlanSelector`, sweep over MATSim's five (`SelectRandom` the control that breaks the scoring-to-membership feedback), `RUN.scoring.path_size_logit_beta` declared beside it.
- **The declared passenger is put on `ride` at the seed** (§9.164, #86, #48): `B.mode.bound_passenger_placement` = `every_plan` (sweep `alternative`, `sweep_role: answer`); duplicate plans are FOLDED, and a person left with ONE plan keeps an alternative on their first base mode.
- **A gate-stopped arm is readable** (§9.158): `extract_metrics` falls back to `ITERS/it.<reached>/`.

## What is measured

- **F39's control relaxes, and the cutoff snap is car-ward on a fourth family** (§9.219, `20260929T072135_250it_25pct`, `_summary.json` `relaxation`; #172): innovation off at 200, settle point 210; the 200→201 snap is car **+1.405 pp** (walk −0.896, taxi −0.438, pt −0.162, ride +0.156); the post-settle drift over it.210–250 is at most **0.093 pp** (car) against the 0.5 pp tolerance; cutoff-to-final car **+1.498 pp**.
- F35's three results snapped car +1.683 / +1.774 / +1.76 and drifted ≤ 0.151 pp (§9.169, §9.176, §9.177): selection concentrating onto the best remembered plan, not score noise — the level it lands on is car +8.5 % on F39 (§9.219).
- **Six twelve-mode readings are RESULTS**, each its own family, never differenced (§3.5): F32 0 of 12 inside (§9.162); F35's arm 0, routers pair and scoring pair 2 of 12 each (car and motorbike; §9.169, §9.176, §9.177); F37 2 of 12 (car +3.7 %, motorbike −7.2 %, §9.214); F38 1 of 12 (car +6.3 %, motorbike +465.7 % on possession, §9.217); F39's control **2 of 12** (car +8.5 %, motorbike −4.1 %, §9.219), 8 past the stop bar.
- **F35's two one-field controls each moved nothing outside one build's noise** (§9.176, §9.177; D4, D7): the routers pair (`C.raptor.mode_cost_representation` = `mode_constant`) within 0.35 pp per trip-share mode of arm 0, the scoring pair (`RUN.replanning.score_msa_representation` = `at_innovation_cutoff`) within 0.3 pp; the F4 seed pair's noise floor was 0.11 pp (§9.64) and the replication band is unmeasured (#163; whether to measure it is D30, a lane decision for the next `/onboard`, §9.220), so none of it is attributable.
- **Coverage on F39's control** (§9.219, `report_choice_set_coverage.py`, `output/modeChoiceCoverage1x.txt`): pt **19.43 %**, ride **19.02 %** against a 20.60 % target — ride's is the bound trips' share, fixed at the seed, so no constant adds to ride past it (§9.177; the ride position owns why). F35's arm 0 read car 75.86 %, walk 63.54, taxi 53.72, bike 27.12, ride 19.11, pt 17.53 (§9.169); motorbike's and truck's never move.
- **The seed carries the binding on every plan** (§9.164, §9.211, F39's `demand/plans/matsim/_plans_report.json` `bound_placement`): WEEKDAY **220,144** ride tours and **17,722** partial over 181,392 persons, 277,906 duplicate plans folded, 56,506 persons kept an alternative; **232,162** held ride trips on 106,642 persons (D12); seeded ride share **0.1048** of weekday legs (`seed_ride_covered_share`).
- **The mechanism that would produce the coverage ranking is an undeclared default** (#174, #155): `WorstPlanSelector` against `RUN.replanning.max_agent_plan_memory` = 8 deletes the worst-scoring plan, a positive feedback between scoring and membership - consistent with, not evidence for; a paired arm on the selector separates it.

## What is open

- **Why convergence makes the fit worse is the open question of the project** (§9.162, §9.169, §9.219, #172): the post-cutoff level is car-heavier than any gate read on every result; whether the cause is the choice set, the service-quality term or the demand is what the pairs must separate — the scoring and the routers are exonerated (§9.176, §9.177).
- **F39 is the first control pair since F35** (D28, §9.218): its control is a result (§9.219) and its treatment — service quality (`C.time_weights.service_quality_representation` = `headway`, `service_interval_function` = `atap_m1`, #175 reopened 8 October 2026) — is built and unrun, the lane's recommended task, waiting on D29.
- After the treatment, the next family is the demand's (`short-trip-and-carless-choice`: a car terminal time and the car-less' alternative, §9.219); the choice-set pair (`RUN.replanning.plan_selector_for_removal` = `SelectRandom`, #174) and the crowding control (#174, #98) are re-aimed at F39's control as the arm they are read against.
- **The `full_choice_set` against `uniform_draw` sweep** has not been run on one family (`B.mode.seed_method`).
- **Whether choice-set decay is a defect or MATSim's ordinary memory** is the choice-set pair's question (§9.140, #174): a plan trailing by a few utils is dropped and must be re-proposed - not a constant to move.
- **Ride's coverage is the bound trips' share at the target, and the loss is where bound trips go** (#86, §9.219): coverage 19.02 % below the 20.60 % target on F39's control; the mechanism (the car-less' alternative on unbound trips) is the ride position's, not this page's.

## Refused — do not re-raise

- **Seeding at the answer**: `B.mode.seed_split_informed` makes every fit a restatement of the seed (§9.92); each mode is one plan, once (§9.120).
- **Moving `RUN.mode_choice.proba_random_single_trip_mode`** to buy fit: worth ~4 pp of a 22 pp car deficit, an exploration parameter (§9.92).
- **Re-scoring, warming up or ordering the choice set** in place of the uniform first-execution draw (§9.121).
- **Passing relaxation by widening `RUN.relaxation.settle_margin_iterations`** to 50 or 100 (§9.43).
- **Reading a level while innovation runs as a verdict**, or a gate that stops on that level (§9.92, §9.108, §9.120).
- **Re-applying a fixed mechanism when the same exception recurs**: the mixed-subtour crash had three refuted causes (§9.118, §9.119).

## History

- §9.220 — six results; D30 a lane decision
- §9.177 — coverage is trips; scoring pair running
- §9.176 — the routers pair a result; moves nothing
- §9.174 — the routers pair launched; ceiling near it.215
- §9.172 — the routers pair chosen first, priced 30.0 h
- §9.170 — the tenth report: every control still unrun
- §9.169 — second result; horizon declared 250
- §9.167 — no change to the seed; the network under it is F34's
- §9.166 — plan removal honours the selector on both paths (#174)
- §9.164 — the passenger is put on ride; the selector is declared
- §9.163 — coverage bounds the constants; ride's target unreachable
- §9.162 — the first result: it relaxes, 0 of 12 inside
- §9.160 — convergence ~200-210 derived; choice set closes at 74
- §9.158 — a listener innovated past the cutoff
- §9.157 — the F31 gate, still stopped at 100
