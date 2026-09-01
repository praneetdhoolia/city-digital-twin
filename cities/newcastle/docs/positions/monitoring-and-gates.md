# Monitoring, scoring and the gate — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 1 September 2026 · **Record read through:** §9.137 · **Open family:** F22

## What is built

- **The hard bar of the gate is the runner's own** (§9.137): a watcher inside `run_matsim.py` reads all twelve modes every `RUN.gate.interval_iterations` = 100 iterations with the same reporter below and stops the JVM itself when any mode is at or past `CAL.gate.stop_deviation_pct`, recording the gate table as the abort cause. The trend judgement ("or heading there") stays with the session.
- **The gate reader** is `src/analyse/report_mode_ridership.py`. It prints every one of the twelve simulated modes on its own row against its own target, never an umbrella `pt` row: the pt submodes are resolved from each boarded route's `transportMode` through the run's own schedule (§9.87). It reads the run directory and the city's target artefact and writes nothing.
- **Any iteration the run has written is readable** (§9.120). Where MATSim wrote `<n>.trips.csv.gz` the reader uses it; between those, `src/analyse/iteration_trips.py` derives the same linked main-mode trips from `<n>.experienced_plans.xml.gz`, which is written every `RUN.controler.write_plans_interval` = 10 iterations. The derivation is validated exactly against the trips table wherever both exist (`--validate`), and the trips table wins any disagreement (§9.120).
- **Three views**: `--it N` for one iteration, `--trend` for one row per mode across every readable iteration with a direction verdict (`toward`, `AWAY`, `flat`), and `--watch SECONDS` to keep printing each newly readable iteration until the run ends. `--truck-stations` scores truck on its target's basis (below).
- **The board's scoreboard is the newest ARM's reading** (`src/analyse/build_status_board.py`): a run whose `_meta.json` declares fewer iterations than the lower bound of the sweep on `RUN.controler.last_iteration` (250) is a plumbing test and is skipped, so a smoke launched after an arm cannot displace that arm's last gate reading (§9.133).
- **Targets** come from `data/processed/validation/mode_targets_by_mode.csv`, written by `cities/newcastle/build/build_mode_targets.py` (§9.87), and `pt_boardings_targets.json` for the two disclosed rail modes (§9.130). They are deliberately NOT rows of `validation_targets.csv`, so the pre-registered 67/143 split is untouched (§9.87, §12).
- **The thresholds are registry fields**, source `definition`, not swept: `CAL.gate.stop_deviation_pct` = 20.0 and `CAL.gate.pass_deviation_pct` = 10.0 (§9.87). A mode at or beyond the stop bar is flagged `STOP`; between the two it is flagged `over 10%` and rounded to neither; inside the pass bar it is `ok`.
- **The calibration fit** is `src/calibrate/fit.py`: it scores the survey's six categories from `_metrics.json` through `score_mode_share`, with `bike+taxi` folded to Other and `car+motorbike` to Vehicle driver — folds the HTS data document's own lists evidence (§9.87). It lists every target it cannot score as `unscorable` with the reason (§9.80). The per-iteration survey-basis reader `src/analyse/measure_iteration_modes.py` hands the trips table to that same function (§9.83).

## How a reading is taken

- **The quantity is linked main-mode trips of target-LGA residents** (§9.83). `modestats.csv` counts PLANNED modes after the `AfterMobsim` restore, so a ride leg that was executed as a drive or a walk still counts as ride there; events give LEGS across five LGAs including freight. Neither is what `fit.py` scores, and neither is a gate reading.
- **Heavy rail and light rail are read on modelled boardings per weekday**, all travellers of every subpopulation, x 1/fraction, against the disclosed counts — heavy rail at its 24 disclosed stations only — scaled by `CAL.pt.weekday_factor` = 1.0727 (§9.130). Bus keeps its composition-derived trip share; the pt total stays against the HTS level (§9.130, superseding the §9.87 station-entries split for those two modes).
- **Truck is not on the person-trip denominator.** Without `--truck-stations` the reader prints the network-wide heavy-vehicle share as a level with no deviation, because the target's own basis says it is not comparable (§9.101). With the flag it scores link entries at the classifying stations' own links against those stations' own heavy share, both from `road_aadt_targets.csv`.
- **Ferry's level is printed and its deviation is not**: nothing is published for this city, and the target stays unobtained and swept (§9.87). **Freight rail is representation, not a fit**: the modelled 314 closures are the timetable (§9.91).
- **Read the trend, not the level** (§9.108, §9.120). Every gate to date has been read on a moving curve; a level read while innovation runs is not a statement about the model. The `--trend` verdict compares the first and last readable iterations and states a rate. Under the full-choice-set seed (§9.120) car and walk reached their targets inside fifty iterations on the F17 arm `20260830T141222_300it_10pct` (§9.126); the 250-iteration horizon is no longer the constraint it was under the uniform seed.
- **Cadence.** The goal directive asks for all twelve modes printed continuously and gated every 100 iterations (§9.120); the F17 arm onward is read every ten (§9.126), and a cause found on the yardstick or the demand is repaired between arms rather than waited for.
- **Nothing is compared across a family, a sample fraction or a network build.** A boardings-basis reading does not compare with an earlier trip-share reading of the same mode (§9.130).

## What is measured

- **The calibrated base is F4, arm `20260821T175907_1000it_25pct`**: 35 of 67 calibration targets scorable, MAE 10.65 pp, `feasible=False` with five stated violations, ASCs held at their priors (§9.64, §9.50). `params/C5_calibration.json` names it as `best_tag`, and `README.md`'s fit figures still draw it via `src/analyse/build_fit_figures.py` (§9.80). Its light rail 1,260 boardings is a LEVEL, not an error (§9.80, #84).
- **The seed noise floor** from the F4 pair: at most 0.11 pp per mode at fit level, light rail boardings within 3.9% (§9.64).
- **The gate has now fired twice, and the second reading holds the first mode inside its band (§9.136).** The F22 arm `aborted_20260831T165127_300it_25pct` read all twelve at iteration 100: 7 at or past 20% (bike +185.5%, heavy rail +152.9%, ferry −80.0%, light rail −70.9% AWAY, taxi +70.9%, ride −41.3%, walk −36.6%), car +15.2% and motorbike +13.3% over 10%, and **bus INSIDE at +8.0%** — the run was stopped under the GOAL.md loop. The F21 gate (§9.134) had read 8 out with none inside; truck at its stations read −45.7% on F22 against F21's −51.0% (§9.136, #82).
- **Truck at its own basis**: +5.4% on 3 calibration stations and 23 modelled heavy traversals at iteration 100 of `aborted_20260829T172145_1000it_10pct`; 20 of the 24 classifying stations are holdout and were not opened (§9.101).

## What is open

- **The machine is idle and the package on disk is consistent** (§9.133, §9.135). Family F22 is open; its first arm is read and stopped at the iteration-100 gate (§9.136). The next family follows the user's pick of root cause, under a fresh run approval.
- **Heavy rail's over-boarding has halved at two successive gates and still stands**: 36,340 → 17,090 inside F21 (§9.134), 37,540 → 16,512 inside F22 under fares, still falling at the stop (§9.136, #98). The licence fix and the fare were the first two repairs, not the last.
- **The light rail's shortfall** is not supply and not the transfer; where its riders are is the open question at the next gate (§9.130, #30).
- **No arm has reached its innovation cutoff since F4**, so no post-cutoff twelve-mode level exists (§9.108).
- **`--trend` omits `freight_train`** and its header still says resident linked trips for every row, while heavy rail and light rail rows now carry boardings (§9.130) — the header is behind the basis.
- **`--truck-stations` is holdout-bound**: whether to spend holdout on freight is the operator's decision, not the reader's (§9.101, #82).
- **#84 stays open** until every surviving quotation of a light rail per-cent error against the unscorable 2019–20 target is found.
- **`fit.py` still folds** (§9.87): the calibration fit scores the survey's categories, the gate scores twelve modes, and the two are distinct instruments by design.

## Refused — do not re-raise

- **Sweeping the gate thresholds**: they are the acceptance criterion, and sweeping them would sweep the question (§9.87).
- **Adding the per-mode targets to `validation_targets.csv`**: it would double-count and disturb the 67/143 split (§9.87, §12).
- **Quoting a light rail error against V001/V002**: `fit.py` marks them unscorable; the modelled figure is a level (§9.80, #84).
- **Printing a truck deviation on the network-wide basis**: two populations, not an error statistic (§9.101).
- **Reading `modestats.csv` or events legs as the gate quantity** (§9.83).
- **Treating a level read mid-innovation as a defect** — four transients were chased in one session on that reading (§9.108).
- **A short probe as convergence evidence**: an eight-iteration reversal was the innovation cutoff's selection snap (§9.83 correcting §9.82).
- **Re-solving a mode constant against the gate**: ASCs stay priors; a violation is reported, never absorbed (§9.50, §9.64).

## History

- §9.134 — first gate since F4; stop fired
- §9.133 — board skips plumbing tests
- §9.137 — the hard bar becomes the runner's
- §9.136 — second gate fires; bus first inside
- §9.131 — licence rate rebuilt; F21 opens
- §9.130 — rail modes on disclosed boardings
- §9.126 — F17 car and walk converged
- §9.120 — every written iteration readable; trend
- §9.108 — read the trend, not level
- §9.101 — truck scored on its own basis
- §9.100 — PT yardstick's three defects found
- §9.92 — seed is a bad guess deliberately
- §9.91 — gate fired; taxi target wrong
- §9.87 — twelve modes, twelve targets, thresholds
- §9.83 — gate quantity is linked trips
- §9.80 — light rail error banned; #84
- §9.64 — F4 base, C5, noise floor
- §9.50 — constrain and report, ASCs held
- §9.16 — calibration loop; counts never optimised
