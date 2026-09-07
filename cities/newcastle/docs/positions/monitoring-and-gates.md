# Monitoring, scoring and the gate — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 7 September 2026 (thirtieth session) · **Record read through:** §9.149 · **Written against family:** `F29`

## What is built

- **The functions that decide correctness have their own tests** (§9.142, #133): `tests/unit/` runs 89 pytest cases on synthetic inputs in 0.13 s - `param_config`'s rendering and target parsing, `outputs._semantic_errors`, `run_matsim.find_completed`'s identity matching, and `fit.py`'s scoring including the issue-19 modelled-zero regression. It is a CI job and a `unit tests` line in `session_gate.py`, which now runs 17 checks. Six Java probes run on the signals stack, `GatedSubtourProbe` and `PtFareProbe` added; the latter measured a latent `Long`-age adult-fare defect on its first day, now fixed and asserted.

- **The hard bar of the gate is the runner's own** (§9.137): a watcher inside `run_matsim.py` reads all twelve modes every `RUN.gate.interval_iterations` = 100 iterations with the same reporter below and stops the JVM itself when any mode is at or past `CAL.gate.stop_deviation_pct`, recording the gate table as the abort cause. The trend judgement ("or heading there") stays with the session. **Its iteration source is the progress digest, not a log tail** (§9.139): the original 64 KiB tail read was measured blind at the 25% arm's log rate — the ENDS marker sat 611 MiB behind EOF — and the watcher idled through the F23 gate; fixed 2 Sep. **Its stop is keyed on the reporter's verdict file** (`--gate-json`), never on the printed `GATE:` line, which the reporter prints on a pass too (§9.141, #112 closed): a passing milestone is logged and the run continues; a milestone whose tables are not written yet is retried every `RUN.gate.retry_interval_s` = 300 s (§9.141, #131); without the digest it reads the log incrementally through `run_view.read_iterations`, never a tail (§9.141). `tests/check_gate_watcher.py` drives it against canned breach, pass and no-verdict reporters in CI. First live firing still unobserved.
- **No open issue behind a run** (GOAL.md requirement 10, §9.140): `src/run/issue_gate.py` reads the tracker through `gh` and refuses while any open issue lacks the `awaiting-run` label; `session_gate.py` carries it as the `issues gated` line and `run.py` refuses to launch (`--allow-open-issues` overrides, to be justified in the run record). Where `gh` cannot read the tracker the gate says so rather than pretending it is empty. As of 4 Sep the tracker is clear of blockers: the three issues that were decisions (#129, #133, #134) are closed and all 14 open issues carry `awaiting-run` (§9.142).
- **The gate reader** is `src/analyse/report_mode_ridership.py`. It prints every one of the twelve simulated modes on its own row against its own target, never an umbrella `pt` row: the pt submodes are resolved from each boarded route's `transportMode` through the run's own schedule (§9.87). It reads the run directory and the city's target artefact and writes nothing.
- **Any iteration the run has written is readable** (§9.120). MATSim writes `<n>.trips.csv.gz` and `<n>.legs.csv.gz` every `RUN.controler.write_trips_interval` = 10 iterations and the reader uses them, rail and tram boardings included (§9.147, §9.148); the full plans, the experienced plans and the events are written every `RUN.controler.write_plans_interval` / `write_events_interval` = 100 — the gate — and `src/analyse/iteration_trips.py` derives the same linked main-mode trips from `<n>.experienced_plans.xml.gz` wherever a table is absent. The derivation is validated exactly against the trips table wherever both exist (`--validate`), and the trips table wins any disagreement (§9.120).
- **Three views**: `--it N` for one iteration, `--trend` for one row per mode across every readable iteration with a direction verdict (`toward`, `AWAY`, `flat`), and `--watch SECONDS` to keep printing each newly readable iteration until the run ends. `--truck-stations` scores truck on its target's basis (below).
- **The board's scoreboard is the newest ARM's reading** (`src/analyse/build_status_board.py`): a run whose `_meta.json` declares fewer iterations than the lower bound of the sweep on `RUN.controler.last_iteration` (250) is a plumbing test and is skipped, so a smoke launched after an arm cannot displace that arm's last gate reading (§9.133); so is an arm of a family the ledger declares `"readings": "none"` — F27's, which ran a model broken at the root (§9.148) — which the runs block still lists with its cause.
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
- **A milestone is MATSim's own tables since §9.147**: `RUN.controler.write_trips_interval` = 10 writes the trips and legs tables the readers take first; the full plans, the experienced plans and the events are gate artefacts (`write_plans_interval`, `write_events_interval` = 100). Rail and tram boardings come from the legs table (`transit_line`, `transit_route`, `access_stop_id`) where the experienced plans are absent (§9.148) — the reader had silently dropped such milestones until it did.
- **The pairing funnel is read with the code, not by its labels** (§9.145, §9.146). A declared pair faces no clock test, so `miss_window` in `output/ride_pairing.csv` never describes one; `miss_declared_absent` (appended last since §9.145) counts unpaired legs whose named driver brought no car leg — 719 at the F26 gate — and the rest of the unpaired legs are on persons with no `boundDriver` at all, which only the experienced plans reveal (12,461 at F26). The watcher stopped F26 at iteration 100 exactly as it stopped F25: the loop's instrument has now fired live twice.
- **Nothing is compared across a family, a sample fraction or a network build.** A boardings-basis reading does not compare with an earlier trip-share reading of the same mode (§9.130).

## What is measured

- **The gate watcher stopped an arm by itself, for the first time** (§9.143, #112). On `aborted_20260905T125612_300it_25pct` it read all twelve modes at iteration 100, found seven at or past `CAL.gate.stop_deviation_pct`, killed the JVM and wrote the gate table as the run's cause - and the arm then closed itself out with `completion` = `stopped_at_gate` and `reached_iteration` = 100, so the reading is citable without re-deriving it from a log. Every arm before it had to be stopped by a person.
- **A milestone is readable only when its experienced plans decompress to the end** (§9.143). Three weaker signals were tried this session and all three mean STARTED, not finished: the progress digest's iteration counter, the `it.N` directory, and the file's mere existence. The runner's own watcher already had this right - it retries the reporter until it succeeds.
- **The calibrated base is F4, arm `20260821T175907_1000it_25pct`**: 35 of 67 calibration targets scorable, MAE 10.65 pp, `feasible=False` with five stated violations, ASCs held at their priors (§9.64, §9.50). `params/C5_calibration.json` names it as `best_tag`, and `README.md`'s fit figures still draw it via `src/analyse/build_fit_figures.py` (§9.80). Its light rail 1,260 boardings is a LEVEL, not an error (§9.80, #84).
- **The seed noise floor** from the F4 pair: at most 0.11 pp per mode at fit level, light rail boardings within 3.9% (§9.64).
- **Every arm since F4 has ended at a gate reading rather than at its horizon; how many, and where each stopped, is the board's runs table** (`results/INDEX.md`, `python src/analyse/build_run_index.py`). The reading that first showed the channels was F23's (§9.139). The F23 arm `aborted_20260901T165115_300it_25pct` read all twelve at iteration 100: 7 at or past 20% (heavy rail +193.2%, bike +111.2%, ferry −80.0%, taxi +76.6%, light rail −66.1%, ride −40.1%, walk −27.2%), with car +14.8%, motorbike +13.9% and bus +16.2% over 10% and none inside — stopped by the session under the GOAL.md loop because the watcher stayed silent (§9.139). Against the questions §9.138 posed at F22's gate: bike +185.5% → +111.2% (the stress channel works, still falling 6.55 → 4.66 in-run), walk −36.6% → −27.2% but the walk/car pair overshot their targets ~it.50 and kept going, bus +8.0% → +16.2% (lost its inside place), heavy rail +152.9% → +193.2% (income scaling weakened the fare's bite), taxi +70.9% → +76.6%, ferry unmoved at −80.0%.
- **Truck at its own basis**: +5.4% on 3 calibration stations and 23 modelled heavy traversals at iteration 100 of `aborted_20260829T172145_1000it_10pct`; 20 of the 24 classifying stations are holdout and were not opened (§9.101).

## What is open

- **Whether the machine is idle, which build is on disk, and how many issues are open are all facts that expire**, and each has one home and one command: the board's state block, `python tests/check_package.py`, and `python src/run/issue_gate.py`. This page used to assert them — "the machine is idle; the package on disk is the F24 build; 13 open issues" — and every one of those was false within four days. The standing rule is what belongs here: **the next arm follows the user's root-cause pick under a fresh stated-cost approval**, and no arm launches while an open issue lacks `awaiting-run` (§9.140).
- **The fix that made the watcher able to fire** was reading `_progress.json` rather than a log tail (§9.139): the original 64 KiB tail was measured blind at the 25 % log rate, with the ENDS marker 611 MiB behind EOF, and it idled straight through the F23 gate.
- **Heavy rail's over-boarding has halved inside every arm and still stands**: 36,340 → 17,090 inside F21 (§9.134), 37,540 → 16,512 inside F22 under fares (§9.136), 37,568 → 19,140 inside F23 under income-scaled fares (§9.139, #98) — the F23 level at the same gate is HIGHER because income scaling weakens the fare deterrent for high-income boarders (#108).
- **The light rail's shortfall** is not supply and not the transfer; where its riders are is the open question at the next gate (§9.130, #30).
- **No arm has reached its innovation cutoff since F4**, so no post-cutoff twelve-mode level exists (§9.108).
- **`--trend` omits `freight_train`** and its header still says resident linked trips for every row, while heavy rail and light rail rows now carry boardings (§9.130) — the header is behind the basis.
- **`--truck-stations` is holdout-bound**: whether to spend holdout on freight is the operator's decision, not the reader's (§9.101, #82).
- **`fit.py` still folds** (§9.87): the calibration fit scores the survey's categories, the gate scores twelve modes, and the two are distinct instruments by design.
- The board prints `-` for truck and freight rail where it printed −63.6 % and +0.0 % against a non-target basis, and the shape check refuses a percentage beside `level only` or `representation` (§9.141, #114 closed).

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

- §9.149 — the F28 gate: 7 out, car inside for the first time
- §9.148 — rail boardings from the legs table; a no-readings family off the board
- §9.147 — the trips cadence declared; plans and events at the gate
- §9.145 — `miss_declared_absent`; the funnel read with the code
- §9.143 — the watcher stopped an arm itself, and it closed itself out
- §9.142 — 89 unit tests, two probes, the tracker clear of blockers
- §9.141 — watcher keyed on a verdict; retry bounded
- §9.140 — issue gate; requirement 10
- §9.139 — third gate; watcher blind, fixed
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
