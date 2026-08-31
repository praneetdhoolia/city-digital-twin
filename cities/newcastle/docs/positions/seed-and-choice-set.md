# Seed and choice set — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 31 August 2026 · **Record read through:** §9.134 · **Open family:** F21

## What is built

- **The seed is the choice set.** `B.mode.seed_method` = `full_choice_set` (§9.120). `src/build/build_matsim_plans.py` writes one plan per mode the person may use — car where a car is available, walk, bike where one is available and the person is old enough, pt, taxi where old enough — each mode on every tour it may take, serving tours held at car, and one further plan riding the covered tours where the demand named a driver. No mode is favoured: each is one plan, once. WEEKDAY carries 2–6 plans per person and 9,880,427 seeded legs against 2,343,321 in the selected plans (§9.126).
- **`uniform_draw` is retained as the sweep alternative** — the pre-§9.120 single plan, tour modes drawn from `B.mode.seed_split` (uniform over the usable modes, deliberately a bad guess) — so how much the search decided is a measurement, not a claim. `B.mode.seed_split_informed` (approximately the observed split) also survives as a declared alternative, never the default.
- **The first-executed plan is drawn uniformly** over the person's seeded plans by a sha256 hash of the person id and the master seed (`seedorder|<pid>|20260810` in `src/build/build_matsim_plans.py`), carried as the `selected="yes"` flag, so iteration 0 is a mixed traffic state like every later one (§9.121). No rng stream, no new value, no re-scoring or warm-up.
- **Plan memory** `RUN.replanning.max_agent_plan_memory` = 8, raised from 5 inside its 3–10 sweep (§9.120): MATSim executes an unscored plan before it consults the selector, and `WorstPlanForRemovalSelector` drops an unscored plan first on overflow, so memory must exceed the seeded plan count or seeded modes are discarded before they are ever executed.
- **Mode choice** is MATSim's `SubtourModeChoice` wrapped by `citysim.GatedSubtourModeChoice` (`src/java/citysim/GatedSubtourModeChoice.java`). Declared: `RUN.mode_choice.modes` car, ride, pt, bike, walk, taxi; `RUN.mode_choice.chain_based_modes` car, bike; `RUN.mode_choice.consider_car_availability` true; `RUN.mode_choice.subtour_behavior` betweenAllAndFewerConstraints; `RUN.mode_choice.proba_random_single_trip_mode` 0.5 (§9.92); `RUN.mode_choice.coord_distance_m` 100 (§9.119).
- **Strategy mix** `RUN.replanning.weights`: ChangeExpBeta 0.7, ReRoute 0.15, SubtourModeChoice 0.1, TimeAllocationMutator 0.05 (`RUN.replanning.time_mutation_range_s` 1800; `RUN.replanning.strategy_subpopulations` limits SubtourModeChoice to `person`). Selection is ChangeExpBeta on score: the gate and the listeners propose, never impose (§9.92).
- **The gate refuses a proposal whole** and restores the pre-innovation plan; it never replaces a draw and never edits a memory. Four refusals: a trip beyond the declared reach (bounds 0.0 since §9.106, so inert); a proposal that would leave a subtour mixing chain- and non-chain modes (§9.119); `ride` on a trip outside the person's `boundRideTrips`, or a declared driver taken off `car` on a trip in `boundDriveTrips` — per-trip attributes written from the binding tables (§9.120); and a plan that ARRIVES mixed is stood aside from mode choice altogether while `ReRoute` still runs — a refusal to crash on #96, not its repair.
- **Escort and joint coherence listeners** offer a decohered bound pair its coherent plan back at `B.ride.escort_coherence_rate` / `B.ride.joint_coherence_rate` = 0.4 (§9.93); the conversion walks to the ROOT subtour so no enclosing subtour is left mixed (§9.118).
- **Innovation cutoff** `RUN.replanning.fraction_to_disable_innovation` = 0.8, sweep 0.7–0.9 (§9.7). At the cutoff selection concentrates every agent onto its best remembered plan in ONE iteration — a property of the structure, not drift (§9.43).
- **Iteration count** `RUN.controler.last_iteration` = 1000, `measured`, sweep 250–2000 (§9.43); shipped scenario configs carry it, and `run_matsim.py --iterations` has no default. Every gate arm since F15 overrides it to 300 — innovation off at 240, gates at 100 / 200 / 300 — in `cities/newcastle/overlays/runs/f15_gate_10pct.json` through `cities/newcastle/overlays/runs/f20_gate_10pct.json`, sized so the goal's 250-iteration horizon is what the run tests (§9.120).
- **Relaxation instrument**: `RUN.relaxation.settle_margin_iterations` = 10 (sweep 1–100, §9.43) opens the drift window after the one-iteration snap; `RUN.relaxation.drift_tolerance_pp` = 0.5 (sweep 0.1–1.0). `src/analyse/summarise_run.py` reports `snap_pp`, `drift_pp` (the verdict) and `cutoff_to_final_pp` (the old instrument, kept auditable).
- **The gate is read on the trend, not the level**, against a scored choice set: iterations 0–6 execute the unscored seeds, 10–30 are exploration (§9.108, §9.120; brief directive 3). The reader is `src/analyse/report_mode_ridership.py` over `src/analyse/iteration_trips.py`, validated against `<n>.trips.csv.gz` wherever both exist (§9.120).

## What is measured

- **The deepest reading of any family**, F17 `aborted_20260830T141222_300it_10pct` (every seed scored, one traffic state, network direct walk), residents' linked trips at 10% (§9.126): car 36.26 → 59.32% and walk 42.27 → 14.88% by iteration 50 — +1.7% and +11.0% of target — ride 2.23 → 10.09% (the demand's ceiling, #86), bike flat at 8.29%. Stopped at iteration 60 when F18 built. The 250-iteration horizon is not the constraint it looked like under the uniform seed.
- **Under the uniform seed the same modes needed hundreds of iterations**: at iteration 100 of the F12 arm car moved +0.001019 per iteration with ~136 more needed, walk ~100 more, pt ~248 more; ride and bike diverging (§9.108). At F14 iteration 30, 65.1% of cyclists held no bike-free plan in memory — the level was random innovation's progress through the seed, not the model (§9.120).
- **Two-state scoring**: with the car plan written first, F15 iteration 0 executed car for 74.74% of residents (162,812 departures, 6,820 cars still on the road at 30:00) and every other mode's plan was scored under a quarter of that traffic; bike beat car for 48.7% of car-available residents (§9.121). After the uniform draw, F16 iteration 0 had 81,332 car departures and 246 stuck, and car is the best-scored plan for 61.1% against 47.8% (§9.121).
- **Selection lags scoring**: F16 iteration 10 had car selected by 38.0% of car-available residents against 61.1% for whom it scored best — ChangeExpBeta compares the selected plan with one random other each round, and 30% of agents execute a fresh plan each iteration (§9.121).
- **The mixed-subtour crash** killed five arms at five different iterations. Measured in one replanning round: 20 plans clean before and mixed after MATSim's own strategy, against 8 arriving mixed (§9.119). The shape is a one-trip child subtour — consecutive activities within `RUN.mode_choice.coord_distance_m` — handed a non-chain mode by the single-trip draw, dormant until the parent is selected. `20260830T083019_1000it_25pct` cleared iteration 6 with 5 refusals and 5 stand-asides, where five arms had died at 3 (§9.119).
- **The demand's own mixed subtours**: 99 in the F14 WEEKDAY population, all spanning several excursions, none leaf (#96); 334 in the F15 population — 3 leaf, 331 spanning, in 328 plans of 114 persons, 0.015% of plans (§9.120); **341 in the F21 population** (rebuilt on the licence-rate population, §9.133) — 3 leaf, 338 spanning, in 329 plans of 110 persons out of 621,364 persons, 2,337,850 plans and 4,667,170 subtours; `car+walk` 112, `car+pt` 112, `car+taxi` 111, `car+ride` 6, every example `closed=false` (`citysim.SubtourChainScan`, 30 Aug, recorded on #96). The rebuild moved the count by 7 and the rate not at all; the three leaf subtours persist.
- **Relaxation at 1000** (`20260816T022250_1000it_10pct`, `20260817T011703_1000it_25pct`): post-snap drift +0.22 / +0.17 pp, fraction-independent, passes at 0.25, 0.5 and 1.0 pp and fails the 0.1 pp floor; pre-cutoff search creep decaying ×0.73 per 100 iterations with roughly 2 pp unfinished (§9.43).
- **The latest twelve-mode reading**, F20 `aborted_20260830T184955_300it_10pct` iteration 10: car 48.01, ride 9.22, walk 25.60, bike 7.77 — exploration, not a gate (brief §2). F19 `aborted_20260830T170743_300it_10pct` iteration 20 read car 56.76, walk 18.05, ahead of F17 at equal depth on every mode.

## What is open

- **No arm on the choice-set seed has passed iteration 60**, and no arm since F4 has reached an innovation cutoff or a 100-iteration gate; a post-cutoff level for twelve modes has never been read on this seed (§9.108, §9.126).
- **The declared horizon and the arms' horizon differ**: `RUN.controler.last_iteration` declares 1000 (§9.43) while every gate arm runs 300 with the goal asking for at most 250 (§9.120). Re-declaring the field on a completed choice-set arm is a declaration not yet made.
- **Whether 1000 iterations are enough SEARCH** was never measured — the 1500-iteration arm was cancelled (§9.43, limit 1). It is moot if the choice-set seed converges inside 250, which is not yet shown.
- **The `full_choice_set` against `uniform_draw` sweep** has not been run on one family; how much the search decided remains unmeasured (`B.mode.seed_method` sweep basis).
- **Each seeded plan is scored once** under the traffic of the iteration it ran in; only re-execution updates it, and how fast selection refines that is what a gate reads (§9.121).
- **#96**: the spanning mixed subtours are days that never return home; stood-aside plans get no mode innovation while selected (the full choice set makes that moot for their owners, §9.120). The degenerate one-trip subtours belong to #30's destination placement, and the single-trip mode change is a weaker operator on those agents (§9.119).
- **The next arm is F21 on a rebuilt population**; the package on disk is inconsistent until the demand chain is rerun (brief §0), and a 25% confirmation arm's fraction is an open decision (`cities/newcastle/docs/NEXT_AGENT_BRIEF.md`).
- **Ride's ceiling is the demand's binding, not the seed** (#86, §9.120, §9.126) — the ride position, not this page.

## Refused — do not re-raise

- **Seeding at the answer** to close the gap: `B.mode.seed_split_informed` makes every fit a restatement of the seed (§9.92). The choice set supersedes "the seed stays uniform" without reintroducing that — each mode is one plan, once (§9.120).
- **Moving `RUN.mode_choice.proba_random_single_trip_mode`** to buy fit: measured worth ~4 pp of a 22 pp car deficit, an exploration parameter (§9.92).
- **Re-scoring, warming up or ordering the choice set** in place of the uniform first-execution draw (§9.121).
- **Passing relaxation by widening `RUN.relaxation.settle_margin_iterations`** to 50 or 100: passing by measuring less is not passing (§9.43).
- **Reading a level while innovation runs as a verdict**, or a gate that stops on that level: it stops on the seed (§9.92, §9.108, §9.120).
- **A ~500-iteration horizon in place of 1000 on the uniform seed** truncated the search mid-slope (§9.57); the 300-iteration gate arms are on the choice-set seed, and §9.120 is the newer entry.
- **Re-applying a fixed mechanism when the same exception recurs**: the mixed-subtour crash had three refuted causes before the diagnostic named the agent (§9.118, §9.119).

## History

- §9.126 — choice-set seed converges car, walk
- §9.121 — first-executed plan drawn uniformly
- §9.120 — seed becomes the full choice set
- §9.119 — mixed proposals refused, arrivals aside
- §9.118 — coherence listener converts root subtour
- §9.108 — read the trend, not level
- §9.96 — ride's seed share was the draw
- §9.94 — uniform seed recoverable for three
- §9.92 — seed stays uniform, deliberately bad
- §9.57 — horizon 1000 kept, 500 rejected
- §9.43 — 1000 declared; snap-aware drift window
- §9.7 — seed test; 250 not converged
- §9.6 — ride enters choice set; uninformed seed
