# Monitoring, scoring and the gate — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 8 October 2026 (sixty-fifth session) · **Record read through:** §9.220 · **Written against family:** `F39`

## What is built

- **The city contract is a gate for every city and passes for both** (§9.202, §9.203): `check_city.py --all` PASS 66 FAIL 0; a framework builder change is verified by regenerating the reference city's artefact against the committed one (`build_manifest.py --verify-producer`).
- **One launch path for every city; readers say what a city lacks** (§9.204, §9.205, #238 #242): the second city's launcher is deleted; a record carries `city`; no home-zone table → residents by subpopulation label and no residents map at launch; no count map or C3 → an empty count side; no survey reader → an empty HTS map; a run above the plans' build fraction is refused (`refuse_fraction_above_build`).
- **The main ruleset requires the test jobs as status checks, and CI reads the commits and the Java** (§9.172, #202, D3; §9.220, #210): a red run is not mergeable; `commit-trailers.yml` reads every commit of a pull request for a trailer or a session link and the title against the 72-character cap (`hooks/block-long-pr-title.sh` refuses one at `gh pr create`); `java-probes.yml` bootstraps the pinned toolchain on Ubuntu and runs the thirteen probes.
- **PT boardings come from one source** — the legs table first, the experienced plans only where no table exists (`src/analyse/iteration_trips.py`, §9.166); `station_of` matches the station name whole.
- **A run with no automatic stop is refused before the JVM starts** (§9.163, #169): the gate watcher AND `RUN.gate.wall_ceiling_h` both off is refused; every watcher lives in the harness, so a harness that dies takes them with it (§9.176, #225).
- **An orphaned run that reached its horizon is closed out as a result** (§9.176, §9.177, D5): `run.py --close-out <run>` accepts a stale `running` card with dead pids, a log ending in MATSim's clean shutdown and a last ENDED iteration (from the log, never the digest) equal to the horizon; refuses a live, short or unclean run; the next launch's `reconcile_stale()` reads the clean shutdown first and calls the same close-out. `run_failure.py --check` is the gate that turns red on the state.
- **A watcher reads a run's in-progress states as progress, not faults** (§9.212): `watch_run.py` reports a run with no `_meta.json` as `NOT STARTED YET`, fires HARNESS DEAD / JVM GONE only on a recorded pid that is gone, and retries an iteration still being written (`NotWrittenYet`); `tests/unit/test_harness_readers.py`.
- **Every reader is clamped to a run's `reached_iteration`** (§9.158, §9.220): `iteration_reading.citable_iterations` / `refuse_past_record` clamp five readers (`tests/unit/test_reader_clamp.py`) at `ITERS/it.<reached>/`, never past it; `output_links` has no per-iteration twin, so the counts block reports `unavailable`.
- **The objective measures the goal**: `CAL.objective.components` = `{"goal_modes.max_abs_rel_pct": 1.0}` via `fit.score_goal_modes()` on the board's own reader; `CAL.objective.independent_targets` = 10 (§9.158).
- **The reading point cannot score a candidate**: `CAL.search.reading_drift_pct` = 24.88 (`measured`, sweep [15.72, 24.88]), `CAL.search.convergence_delta` derived from it; `calibrate.py --execute` refuses while the drift exceeds `CAL.gate.pass_deviation_pct`, so the search is priced with `--plan` and not run (§9.158, `measure_reading_stability.py`).
- **The search can run**: `calibrate.py --config-set`; any field with a `matsim_param` binding is movable (5 → 21, §9.158).
- **Profiling**: `RUN.machine.jfr_profile` and `RUN.machine.gc_log`, read by `profile_run.py`; observation only (§9.154).
- **The local gate runs every check CI runs, and every check reads every city** (§9.219, §9.220; `tests/unit/test_gate_covers_ci.py`): `check_manifest`, `render_docs --check`, `check_hardcoding --strict`, `check_doc_currency` and `check_doc_shape` each run `--all-cities` through `city.run_per_city` (Mumbai's front page had drifted 428 → 446 fields unseen); no tracked text file may hold a NUL byte (`test_sources_are_text.py`); the thirteen Java probes run on the signals stack (§9.142, #133).
- **Hardcoding debt is a per-city ledger whose ceiling only falls** (§9.220, #212): `cities/<city>/tests/hardcoding_debt.json` under `src/registry/debt_ledger.py`, the one shape shared with `manifest_debt.json`; a raise needs `"raised": true` with its reason (`check_ceilings` once admitted any logged rise); vendored raw downloads are excluded by rule; the ALL-CAPS and `dict(...)` visitor and a wall-clock / unseeded-random scan run over the build layers (0 in both).
- **The handoff gate reads the pages** (§9.220): `positions.py --check --stale` names a page more than three sections behind `record.py --next` (STALE) or whose *What is measured* names no result of the newest family (WARN); `--second-homes` names every page or brief line restating a figure the board generates.
- **The gate watcher in `run_matsim.py`** reads all twelve modes every `RUN.gate.interval_iterations` = 100 and stops the JVM at `CAL.gate.stop_deviation_pct` (§9.137) from the progress digest, never a log tail (§9.139), keyed on `--gate-json` (§9.141, #112); retry every `RUN.gate.retry_interval_s` = 300 s (#131); `tests/check_gate_watcher.py` in CI.
- **Every arm since F35's pairs runs with the gate OFF by overlay** (`interval_iterations` 0 under `allow_outside_sweep`, justified; `f36_baseline_25pct` §9.212 through `f39_control_25pct` §9.218): a watcher stop at 100 would leave no control for the pairs, and a control differenced against arm 0 is read at arm 0's horizon — a scoped departure GOAL.md's loop now states (D10, 16 September 2026, #227). The ceiling and the stall kill stay armed.
- **The issue gate** (requirement 10, §9.140, §9.158, §9.160, §9.177, §9.220): `src/run/issue_gate.py` refuses a launch while an in-lane `awaiting-run` issue lacks a real `AWAITING-RUN: <measurement>` line, refuses an overlay whose `answers_issues` names a CLOSED issue (requirement 10 was once met vacuously on #175) and flags an `AWAITING-RUN` line naming a closed family's run; `AWAITING-DECISION:` reports without blocking; `--allow-open-issues` needs `--override-reason`, ledgered; `[MEASUREMENT DUE: ...]` when the line's run, overlay or value has since completed.
- **The lane is pinned to the ledger** (§9.220): `lane.py --check` fails when `lane.json`'s `family` is not the ledger's newest or an open task answers a closed issue; `build_status_board.py` writes the lane's family and the brief's `Commit` sha, so neither is typed.
- **The reader** `src/analyse/report_mode_ridership.py` prints twelve rows, never an umbrella `pt` row, submodes through the run's own schedule, and writes nothing (§9.87); `--it N`, `--trend` (`toward` / `AWAY` / `flat`), `--watch SECONDS`, `--truck-stations`.
- **Any written iteration is readable** (§9.120): trips and legs every `RUN.controler.write_trips_interval` = 10, plans and events every 100; `iteration_trips.py` derives trips from the experienced plans where no table exists.
- **The scoreboard is the newest ARM's, never a `failed` run's** (`build_status_board.py`, §9.168): it skips a run under the sweep floor on `RUN.controler.last_iteration` (§9.133), a family marked `"readings": "none"` (§9.148) and F33's `aborted_20260910T222830_300it_25pct`.
- **Targets**: `mode_targets_by_mode.csv` (`build_mode_targets.py`, §9.87) and `pt_boardings_targets.json` (§9.130), never `validation_targets.csv` (§12). `CAL.gate.stop_deviation_pct` = 20.0 and `CAL.gate.pass_deviation_pct` = 10.0 are `definition`, not swept (§9.87).
- **`src/calibrate/fit.py`**: `score_mode_share` folds `bike+taxi` to Other and `car+motorbike` to Vehicle driver (§9.87), unscorable targets listed with reasons (§9.80); `measure_iteration_modes.py` uses the same function (§9.83).
- **The run viewer** `src/analyse/run_view.py` (§9.170–§9.175, §9.206): serves on EVERY run (`RUN.monitor.enabled` retired) and on any finished one (`--run <name>`); every run from one picker, each mode against the 10 % goal and 20 % stop bar, every transit route of the run's own schedule by transport mode; the CRS and the basemap are the RUN's city's, from its record; MapLibre GL 5.24.0; nothing from a city by name.
- **`CAL.objective.replication_band_pp` = 0.0** (`sweep_role: measurement`, bracket [0.0, 2.0]) is the objective's denominator, MEASURED before it is set by three arms differing only in `RUN.machine.seed` (§9.164, #163).

## How a reading is taken

- **The quantity is linked main-mode trips of target-LGA residents** (§9.83): `modestats.csv` counts PLANNED modes and events give LEGS across five LGAs; neither is a gate reading.
- **Heavy rail and light rail are read on modelled boardings per weekday**, all subpopulations × 1/fraction, heavy rail at its 24 disclosed stations only, × `CAL.pt.weekday_factor` = 1.0727 (§9.130); bus keeps its composition-derived trip share.
- **Truck is not on the person-trip denominator** (§9.101): a level without `--truck-stations`, link entries at the classifying stations with it; ferry's deviation is not printed (§9.87); freight rail is representation, not a fit (§9.91).
- **Read the trend, not the level** (§9.108, §9.120): a level read under innovation is not a statement about the model. Gated every 100 iterations, read every ten (§9.126); a cause on the yardstick or the demand is repaired between arms.
- **A milestone is MATSim's own tables** (§9.147): rail and tram boardings from the legs table (`transit_line`, `transit_route`, `access_stop_id`) where the plans are absent (§9.148); readable only when its experienced plans decompress to the end (§9.143).
- **Nothing is compared across a family, a sample fraction or a network build**; a boardings reading does not compare with an earlier trip-share reading (§9.130).

## What is measured

- **The gate today** (§9.220): 26 checks PASS; the unit suite **1,296** passed (1,129 before); `issue_gate.py` 33 open, 17 awaiting a run with a measurement, 16 awaiting a decision, 0 blocking; `positions.py --check --stale` 0 STALE, 4 WARN (pages with no per-result reading to add); `check_hardcoding --all-cities` Mumbai 233 → **0** outside its ledger (207 rows recorded), Newcastle 0 outside (15 recorded); `check_doc_currency --all-cities` 0 drifted in both cities; `check_package.py` PASS 2,061, FAIL 1 (the session's record number cited before it existed), WARN 2.
- **A stopped arm is readable end to end** (§9.213, §9.217): the extractor and `fit.py` read the newest table at or below `reached_iteration`, the ridership reader clamps to it, the persons readers fall back to the run's input plans (`iteration_reading.person_attributes`); on a warm-started run the choice-set bound is not read, because MATSim counts coverage from the run's own first iteration.
- **The gate reports what a constant could reach** (§9.163): beside every breaching mode its choice-set coverage, a target ABOVE it marked unreachable — on every F35 result only ride (19.11 % on arm 0).
- **The reading point is a CONVERGENCE problem, not a measurement one** (§9.159, #163): the window (`CAL.gate.reading_window_iterations` = 40, sweep [20, 80]) measured worse than the point because the in-run movement is a monotone trend (`results/processed/_reading_window_measurement.json`); arm 0's drift it.250→300 is at most **0.128 pp** against a cutoff snap of **+1.683 pp** (§9.169).

## What is open

- **The light rail's shortfall** is not supply and not the transfer; where its riders are is the open question at the next gate (§9.130, #30).
- **`--truck-stations` is holdout-bound**: whether to spend holdout on freight is the operator's decision (§9.101, #82).
- **`fit.py` folds for the SURVEY targets and not for the OBJECTIVE** (§9.87, §9.158): `score_mode_share` the five folded categories as a diagnostic, `score_goal_modes` the twelve modes; distinct by design.

## Refused — do not re-raise

- **Sweeping the gate thresholds**: they are the acceptance criterion (§9.87).
- **Raising `CAL.search.convergence_delta` past the measured drift** (§9.158): the delta IS the noise floor; the reading point is what must change.
- **Adding the per-mode targets to `validation_targets.csv`**: it would disturb the 67/143 split (§9.87, §12).
- **Quoting a light rail error against V001/V002**: unscorable; the modelled figure is a level (§9.80, #84).
- **Printing a truck deviation on the network-wide basis** (§9.101).
- **Reading `modestats.csv` or events legs as the gate quantity** (§9.83).
- **Treating a level read mid-innovation as a defect** (§9.108).
- **A short probe as convergence evidence**: a reversal was the cutoff's selection snap (§9.83 correcting §9.82).
- **Re-solving a mode constant against the gate**: ASCs stay priors (§9.50, §9.64).

## History

- §9.220 — the gates read every city
- §9.219 — the gate covers CI
- §9.213 — a stopped arm read end to end
- §9.212 — watchers tell setup from death
- §9.206 — viewer on every run 
- §9.205 — build-fraction refusal
- §9.204 — one launch path; readers degrade
- §9.203 — both cities pass the contract
- §9.178 — native Codex skills and workflow
- §9.177 — detach by default; residents per run
- §9.176 — the pair a result; orphan close-out
- §9.175 — congestion measured as a map app does
