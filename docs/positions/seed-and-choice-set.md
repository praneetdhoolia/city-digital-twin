# Seed and choice set — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Two runs are results - F32's `20260909T015217_300it_25pct` and F35's arm 0 `20260912T202242_300it_25pct`, each `completion` `ran_to_last_iteration` at iteration 300 (§9.162, §9.169); nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 14 September 2026 (forty-eighth session) · **Record read through:** §9.171 · **Written against family:** `F35`

## What is built

- **Both plan-removal paths honour `RUN.replanning.plan_selector_for_removal`** (§9.166, #174): `EscortCoherenceListener.trim()` injects the selector MATSim binds and re-selects at random if it took the selected plan (`tests/unit/test_plan_removal_one_selector.py`); `GatedSubtourModeChoice` treats a plan whose subtour decomposition throws as MIXED.
- **A seeded plan carries PER-TRIP modes** (§9.143): a partially bound tour rides its covered leg while the rest takes `B.mode.partial_bind_base` = `pt`, so §9.119's chain/non-chain mix is unreachable. Plan memory peaks at 7 of `RUN.replanning.max_agent_plan_memory` = 8; `check_package.py` reads the cap from the registry.
- **The seed is the choice set.** `B.mode.seed_method` = `full_choice_set` (§9.120): `src/build/build_matsim_plans.py` writes one plan per mode the person may use plus one riding the covered tours where a driver is named; each mode once. WEEKDAY carries 2–6 plans per person, 9,880,427 seeded legs against 2,343,321 selected (§9.126).
- **`uniform_draw` is retained as the sweep alternative** (tour modes from `B.mode.seed_split`), and `B.mode.seed_split_informed` survives as a declared alternative, never the default (§9.120).
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
- **Choice-set coverage is an instrument, and the gate carries its bound** (§9.163): `src/analyse/report_choice_set_coverage.py` reads `modeChoiceCoverage1x.txt`; `coverage − share` is the most any constant can add, printed beside every verdict. Locked carves and boardings targets get no bound.
- **Score averaging is declared and shipped OFF** (§9.163): `RUN.replanning.score_msa_representation` = `absent` (`absent` | `at_innovation_cutoff`, `sweep_role: answer`), `RUN.replanning.score_msa_fraction` bound to `scoring.fractionOfIterationsToStartScoreMSA`; `at_innovation_cutoff` introduces no new number.
- **The choice-set branch has a control** (§9.164, #174, #155): `RUN.replanning.plan_selector_for_removal` = `WorstPlanSelector`, sweep over MATSim's five (`SelectRandom` the control that breaks the scoring-to-membership feedback), `RUN.scoring.path_size_logit_beta` declared beside it.
- **The declared passenger is put on `ride` at the seed** (§9.164, #86, #48): `B.mode.bound_passenger_placement` = `every_plan` (sweep `alternative`, `sweep_role: answer`); duplicate plans are FOLDED, and a person left with ONE plan keeps an alternative on their first base mode.
- **A gate-stopped arm is readable by the fit pipeline** (§9.158): `extract_metrics` falls back to `ITERS/it.<reached>/`.

## What is measured

- **Arm 0 relaxes, and car still moves away from target after it.100** (§9.169, `20260912T202242_300it_25pct`, `_summary.json`): drift over it.250–300 car **+0.128 pp** max, taxi −0.097, walk −0.040 → **relaxed** at 0.5 pp. Snap at 240→241: car **+1.683 pp**, walk −1.245, taxi −0.679, ride +0.449. Planned car (`modestats.csv`): 41.44 % at it.0, 62.26 at it.100, 64.71 at it.200, 66.94 at it.300 — convergence moves car AWAY from target, and #172 stands.
- **Coverage at 300 on arm 0** (§9.169, `output/modeChoiceCoverage1x.txt`): car **75.86 %**, walk 63.54, taxi 53.72, bike 27.12, ride **19.11**, pt **17.53**; motorbike 0.23 and truck 4.09 never move. Ride's coverage is fixed at the seed from it.27, so its 20.60 % target sits above it and NO constant reaches it; pt was still opening at it.240.
- **Two twelve-mode readings are RESULTS** (§9.162, §9.169). F32's `20260909T015217_300it_25pct`: 0 of 12 inside, 8 past the stop bar. F35's arm 0: **2 of 12 inside** (car +9.6 %, motorbike −5.6 %), 6 past the bar (ride −41.6 %, taxi +131.4 %, bike +201.6 %, heavy rail +54.6 %, light rail −73.9 %, ferry −63.3 %). Different families, not differenced (§3.5).
- **Requirement 8 is measured on F32: the run relaxes, and relaxing is not converging** (§9.162): `relaxed: true` over it.250–300, max drift **0.261 pp** (car) at 0.5; the snap at 240 was car **+2.211 pp**, walk −0.941, taxi −0.583, ride −0.489, pt −0.153 — the distance the search had not travelled. Requirement 8's 250 is met in the weak sense only.
- **The relaxed state is worth less than the state it relaxed from** (§9.162, `output/scorestats.csv`): average plan score 11.7500 at it.100, **19.2049** at 240, **14.5679** at 300; best 32.0315 → 26.4472; executed 12.5211 → 24.8780. The §9.160 extrapolation was right on direction, wrong on level.
- **The choice set closes early and PT barely opens** (§9.160, §9.162): F32 coverage at 300 car **77.55 %**, walk 63.95, taxi 54.62, bike 29.03, **pt 25.78**, ride **20.05**; motorbike 0.00236 and truck 0.04158 are locked carves. First iteration within 1 pp of final / last move over 0.01 pp: ride 5 / 17, bike 7 / 16, walk 7 / 14, car 8 / 16, taxi 10 / 27, **pt 123 / 233** (§9.163).
- **Ride's target is above its own coverage** (§9.163): 20.60 % target, 20.05 % coverage, share 12.1553 %; the only such mode, so ride's −41.0 % is a choice-set finding, not a taste (#48, #86).
- **The seed carries the binding on every plan** (§9.164, `_plans_report.json` `bound_placement`): WEEKDAY **194,131** fully and **59,705** partially bound tours over 199,329 persons, 268,306 duplicates folded, 90,134 persons kept an alternative; SAT 167,389 / 34,624; SUN 148,686 / 26,239. Seeded ride share 0.1114 of weekday legs = `seed_ride_covered_share`.
- **The demand's own mixed subtours**: 0 leaf on every day type on the rebuilt plans - WEEKDAY 338, SAT 222, SUN 181, all spanning (`citysim.SubtourChainScan`, §9.140, #96). On arm 0 `STOOD ASIDE` reads **5**, all in the first two iterations, against 0 on the 1 % probes (§9.169, §9.164): #96's close condition is met at 5, not 0.
- **The mechanism that would produce the coverage ranking is an undeclared default** (#174, #155): `WorstPlanSelector` against `RUN.replanning.max_agent_plan_memory` = 8 deletes the worst-scoring plan, a positive feedback between scoring and membership - consistent with, not evidence for; a paired arm on the selector separates it.

## What is open

- **Why convergence makes the fit worse is the open question of the project** (§9.162, §9.169, #172): the post-cutoff level is car-heavier than any gate read; whether the cause is the scoring, the choice set (pt reaches 25.78 % on F32, 17.53 % on arm 0) or the routers is what the pairs must separate.
- **Five one-field controls, one control arm, and the order is the operator's** (§9.164, §9.169, #172): scoring (`RUN.replanning.score_msa_representation`), the choice set (`RUN.replanning.plan_selector_for_removal`), the routers (`C.raptor.mode_cost_representation`), the demand (`B.mode.bound_passenger_placement`, SPENT at `every_plan`), service quality (`C.time_weights.service_quality_representation`, #175). Arm 0 is the CONTROL HALF; no arm was chosen and no approval stands; the recommendation is the routers pair first.
- **Superseded** (§9.163): the scoring branch `at_innovation_cutoff` is the one candidate predicting both the +2.211 pp snap and the score peak-then-fall; the router branch `C.raptor.mode_cost_representation` = `mode_constant` is built and never run (§9.162, #49).
- **A crowding or raptor arm can move coverage as a side effect** (#174, #98, #49): read coverage on both arms of any pair, or the difference is not attributable.
- **Superseded: the horizon is declared 250** (§9.169): §9.142's refusal rested on §9.7's pre-rebuild, 1 %, uniform-seed measurement; the field reads 250 on a result's evidence.
- **Whether 200 iterations of SEARCH suffice stays unmeasured** (§9.169): the pairs cut at 200 where arm 0 cut at 240; the ≤ 0.42 pp movement between those points bounds the difference without testing it.
- **The `full_choice_set` against `uniform_draw` sweep** has not been run on one family (`B.mode.seed_method`).
- **Each seeded plan is scored once** under the traffic of its iteration; how fast selection refines that is what a gate reads (§9.121).
- **Whether choice-set decay is a defect or MATSim's ordinary memory** is the next arm's question (§9.140): a plan trailing by a few utils is dropped and must be re-proposed - not a constant to move.
- **Ride's ceiling is the demand's seeded ride share** (#86, §9.169): coverage 19.11 % against a 20.60 % target — the ride position, not this page.

## Refused — do not re-raise

- **Seeding at the answer**: `B.mode.seed_split_informed` makes every fit a restatement of the seed (§9.92); each mode is one plan, once (§9.120).
- **Moving `RUN.mode_choice.proba_random_single_trip_mode`** to buy fit: worth ~4 pp of a 22 pp car deficit, an exploration parameter (§9.92).
- **Re-scoring, warming up or ordering the choice set** in place of the uniform first-execution draw (§9.121).
- **Passing relaxation by widening `RUN.relaxation.settle_margin_iterations`** to 50 or 100 (§9.43).
- **Reading a level while innovation runs as a verdict**, or a gate that stops on that level (§9.92, §9.108, §9.120).
- **A ~500-iteration horizon on the uniform seed** truncated the search mid-slope (§9.57); §9.120 is the newer entry.
- **Re-applying a fixed mechanism when the same exception recurs**: the mixed-subtour crash had three refuted causes (§9.118, §9.119).

## History

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
- §9.142 — the 250-iteration horizon reviewed and not declared
- §9.140 — leaf mix repaired; memory census
- §9.126 — choice-set seed converges car, walk
- §9.121 — first-executed plan drawn uniformly
