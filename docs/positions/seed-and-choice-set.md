# Seed and choice set — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 17 September 2026 (fifty-fourth session) · **Record read through:** §9.177 · **Written against family:** `F35`

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
- **Iteration count** `RUN.controler.last_iteration` = **250** (§9.169; sweep 250–2000, §9.43): innovation off at 200, on arm 0's post-settle drift ≤ 0.128 pp. `run_matsim.py --iterations` has no default; arm 0 and every gate arm since F15 ran 300 with the cutoff at 240 (§9.120).
- **Relaxation instrument**: `RUN.relaxation.settle_margin_iterations` = 10 (sweep 1–100), `RUN.relaxation.drift_tolerance_pp` = 0.5 (sweep 0.1–1.0); `src/analyse/summarise_run.py` reports `snap_pp`, `drift_pp` (the verdict) and `cutoff_to_final_pp` (§9.43).
- **The gate is read on the trend, not the level**, against a scored choice set (§9.108, §9.120): `src/analyse/report_mode_ridership.py` over `src/analyse/iteration_trips.py`.
- **Choice-set coverage is an instrument, and the gate carries its bound** (§9.163, §9.177): `src/analyse/report_choice_set_coverage.py` reads `modeChoiceCoverage1x.txt`, which counts the share of TRIPS that ever executed a mode (at iteration 0 the pair's file reads ride 0.1415, the seeded plans' share — not a share of agents, as §9.163 and §9.169 read it); `coverage − share` is the most any constant can add, printed beside every verdict. Locked carves and boardings targets get no bound.
- **Score averaging is declared, shipped OFF, and measured to move nothing** (§9.163, §9.177, D7): `RUN.replanning.score_msa_representation` = `absent` (`absent` | `at_innovation_cutoff`, `sweep_role: answer`), `RUN.replanning.score_msa_fraction` bound to `scoring.fractionOfIterationsToStartScoreMSA`; the scoring pair ran `at_innovation_cutoff` as its one field and the roots rebuild's arm 0 keeps `absent`.
- **The choice-set branch has a control** (§9.164, #174, #155): `RUN.replanning.plan_selector_for_removal` = `WorstPlanSelector`, sweep over MATSim's five (`SelectRandom` the control that breaks the scoring-to-membership feedback), `RUN.scoring.path_size_logit_beta` declared beside it.
- **The declared passenger is put on `ride` at the seed** (§9.164, #86, #48): `B.mode.bound_passenger_placement` = `every_plan` (sweep `alternative`, `sweep_role: answer`); duplicate plans are FOLDED, and a person left with ONE plan keeps an alternative on their first base mode.
- **A gate-stopped arm is readable** (§9.158): `extract_metrics` falls back to `ITERS/it.<reached>/`.

## What is measured

- **The scoring pair is a RESULT and moves nothing; the cutoff snap stands under score averaging** (§9.177, `20260916T063903_250it_25pct`, `ran_to_last_iteration` at 250, 25.77 h; `compare_runs.py --modes` against arm 0): car **+0.007 pp**, ride +0.293, bike **−0.292**, bus −0.055, light rail 772 → **928** boardings, heavy rail 10,092 on both; **2 of 12 inside, 6 past the bar on both**. 
- **The snap survives score averaging** (§9.177, `_summary.json`): with MSA from it.200 the 200→201 snap is car **+1.76 pp** (arm 0 +1.683, routers pair +1.774), drift 0.151 pp — selection concentrating onto the best remembered plan, not score noise.
- **The routers pair is a RESULT and moves nothing outside noise** (§9.176, `20260915T000704_250it_25pct`, `ran_to_last_iteration` at 250, 27.39 h; `_fit.json` on both arms): against arm 0, car 63.56 vs 63.91 % (**−0.35 pp**), ride +0.17, walk +0.04, taxi +0.11, bike −0.08, bus +0.09 pp; heavy rail 10,476 vs 10,092 boardings, light rail 856 vs 772; **2 of 12 inside and 6 past the bar on both**. The F4 seed pair's noise floor was 0.11 pp per mode (§9.64) and the replication band is unmeasured (#163), so none of it is attributable; the pair cut innovation at 200, arm 0 at 240 (§9.169).
- **Both results relax, and car moves away from target after it.100 on both** (§9.169, §9.176, `_summary.json`): arm 0 drift over it.250–300 car **+0.128 pp** max, snap at 240→241 car **+1.683 pp**, walk −1.245, taxi −0.679, ride +0.449; the pair drift over it.210–250 car **+0.14 pp** max, snap at 200→201 car **+1.774**, walk −1.344, taxi −0.640, ride +0.364. On the pair the it.100 gate read car +3.0 %, walk +9.9 %, bus −0.3 % inside, and convergence took car to +9.0 % and walk to −11.9 % — #172 stands on two arms.
- **Coverage on both arms** (§9.169, §9.176, `output/modeChoiceCoverage1x.txt`): arm 0 at 300 car **75.86 %**, walk 63.54, taxi 53.72, bike 27.12, ride **19.11**, pt **17.53**; the pair at 250 car 75.46, walk 63.37, taxi 53.33, bike 26.59, ride **19.11**, pt **15.78** — pt's coverage fell 1.75 pp under the routers change or under 40 fewer innovating iterations, ride's is identical and fixed at the seed from it.27 — it is the bound trips' share, so no constant adds to ride past it (§9.177; the ride position owns why); motorbike 0.23 and truck 4.09 never move.
- **Three twelve-mode readings are RESULTS** (§9.162, §9.169, §9.176). F32's `20260909T015217_300it_25pct`: 0 of 12 inside, 8 past the stop bar. F35's arm 0: **2 of 12 inside** (car +9.6 %, motorbike −5.6 %), 6 past the bar (ride −41.6 %, taxi +131.4 %, bike +201.6 %, heavy rail +54.6 %, light rail −73.9 %, ferry −63.3 %). F35's routers pair: 2 of 12 inside (car +9.0 %, motorbike −5.5 %), 6 past (ride −40.8, taxi +142.6, bike +197.8, heavy rail +60.5, light rail −71.0, ferry −66.9 %). F32 is a different family, not differenced (§3.5).
- **The seed carries the binding on every plan** (§9.164, `_plans_report.json` `bound_placement`): WEEKDAY **194,131** fully and **59,705** partially bound tours over 199,329 persons, 268,306 duplicates folded, 90,134 persons kept an alternative; SAT 167,389 / 34,624; SUN 148,686 / 26,239. Seeded ride share 0.1114 of weekday legs = `seed_ride_covered_share`; the sampled seed's SELECTED plans carry ride on **14.91 %** of legs (`_bound_trips.json` on `20260915T000704_250it_25pct`, §9.177).
- **The mechanism that would produce the coverage ranking is an undeclared default** (#174, #155): `WorstPlanSelector` against `RUN.replanning.max_agent_plan_memory` = 8 deletes the worst-scoring plan, a positive feedback between scoring and membership - consistent with, not evidence for; a paired arm on the selector separates it.

## What is open

- **Why convergence makes the fit worse is the open question of the project** (§9.162, §9.169, #172): the post-cutoff level is car-heavier than any gate read; whether the cause is the scoring, the choice set (pt reaches 25.78 % on F32, 17.53 % on arm 0) or the routers is what the pairs must separate.
- **Five one-field controls, one control arm, and the order is the operator's** (§9.164, §9.169, #172): scoring (`RUN.replanning.score_msa_representation`), the choice set (`RUN.replanning.plan_selector_for_removal`), the routers (`C.raptor.mode_cost_representation`), the demand (`B.mode.bound_passenger_placement`, SPENT at `every_plan`), service quality (`C.time_weights.service_quality_representation`, #175). Arm 0 is the CONTROL HALF.
- **The routers control is measured and moves nothing** (§9.176, D4 §9.175: inside F35, against arm 0): `C.raptor.mode_cost_representation` = `mode_constant` is not what decides the rail split or the car excess. **The scoring control is measured and moves nothing either** (§9.177, D7): three results of one family agree within 0.35 pp on every trip-share mode; what remains of #172 is the choice set (`RUN.replanning.plan_selector_for_removal`, #174), service quality (#175) and the demand — the roots rebuild goes at the demand first (the lane).
- **The `full_choice_set` against `uniform_draw` sweep** has not been run on one family (`B.mode.seed_method`).
- **Whether choice-set decay is a defect or MATSim's ordinary memory** is the next arm's question (§9.140): a plan trailing by a few utils is dropped and must be re-proposed - not a constant to move.
- **Ride's coverage is the bound trips' share at the target, and the loss is where bound trips go** (#86, §9.177): 59.0 % of the pair's bound trips rode at it.250; the mechanism (D12's hold) is the ride position's, not this page's.

## Refused — do not re-raise

- **Seeding at the answer**: `B.mode.seed_split_informed` makes every fit a restatement of the seed (§9.92); each mode is one plan, once (§9.120).
- **Moving `RUN.mode_choice.proba_random_single_trip_mode`** to buy fit: worth ~4 pp of a 22 pp car deficit, an exploration parameter (§9.92).
- **Re-scoring, warming up or ordering the choice set** in place of the uniform first-execution draw (§9.121).
- **Passing relaxation by widening `RUN.relaxation.settle_margin_iterations`** to 50 or 100 (§9.43).
- **Reading a level while innovation runs as a verdict**, or a gate that stops on that level (§9.92, §9.108, §9.120).
- **Re-applying a fixed mechanism when the same exception recurs**: the mixed-subtour crash had three refuted causes (§9.118, §9.119).

## History

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
- §9.143 — per-trip seeded modes
