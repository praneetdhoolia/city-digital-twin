# Monitoring, scoring and the gate — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Two runs are results - F32's `20260909T015217_300it_25pct` and F35's arm 0 `20260912T202242_300it_25pct`, each `completion` `ran_to_last_iteration` at iteration 300 (§9.162, §9.169); nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 14 September 2026 (forty-ninth session) · **Record read through:** §9.172 · **Written against family:** `F35`

## What is built

- **The reader reads a run through its own schedule**: `extract_metrics.schedule_path` takes `output/output_transitSchedule.xml.gz` first, `SCHEDULE_SOURCE` recorded; the city copy the F34 rebuild overwrote had printed heavy rail **0 / −100.0 %** on F32 (§9.169).
- **Reader fixes** (§9.169): freight_train = scheduled + the run's own `_config.json` freight closures; `iteration_reading.innovation_off_after` shared by `summarise_run` and `run_view`; a boardings reading with no sample fraction refused; `_CACHE` bounded to `CACHE_TABLES` = 6. Unit suite **469**.
- **The eighth report's #180–#192 are fixed or await a run** (§9.167): `check_hardcoding` category 9 gates inline literals (124 → 0, #188); `session_gate` checks the import roots (#181); all 99 modules are imported by a test (#190); `build_fit_figures --check` refuses a drifted C5 objective.
- **The main ruleset requires the nine test jobs as status checks** (§9.172, #202; ruleset 21121872, the user's decision D3): a red run is no longer mergeable.
- **PT boardings come from one source** — the legs table first, the experienced plans only where no table exists (`src/analyse/iteration_trips.py`, §9.166); `station_of` matches the station name whole.
- **A run with no automatic stop is refused before the JVM starts**: `run_matsim.py` refuses when the gate watcher AND `RUN.gate.wall_ceiling_h` are both off (§9.163, #169).
- **A gate-stopped arm is read** at `ITERS/it.<reached>/<reached>.<table>`, never past `reached_iteration`; `output_links` has no per-iteration twin, so the counts block reports `unavailable` (§9.158).
- **The objective measures the goal**: `CAL.objective.components` = `{"goal_modes.max_abs_rel_pct": 1.0}` via `fit.score_goal_modes()` on the board's own reader; `CAL.objective.independent_targets` = 10 (§9.158).
- **The reading point cannot score a candidate**: `CAL.search.reading_drift_pct` = 24.88 (`measured`, sweep [15.72, 24.88]), `CAL.search.convergence_delta` derived from it; `calibrate.py --execute` refuses while the drift exceeds `CAL.gate.pass_deviation_pct` (§9.158, `measure_reading_stability.py`).
- **The search can run**: `calibrate.py` uses `--config-set`; any field with a `matsim_param` binding is movable (5 → 21: `B.ride.*`, `B.taxi.*`, `B.population.bike_min_age`, `A.gradient.bike_speed_*`); `evaluate()` re-assembles per candidate from the mapped schedule (§9.158).
- **Profiling**: `RUN.machine.jfr_profile` writes `<run>/profile.jfr`, `RUN.machine.gc_log` a GC log, read by `profile_run.py --run <run> --iterations 2:3`; observation only, no family opens, `arm_cost.py` excludes it. `_progress.json` carries `iteration_seconds` (§9.154).
- **`tests/unit/`** runs on synthetic inputs, a CI job and a `session_gate.py` line; six Java probes (`GatedSubtourProbe`, `PtFareProbe`) run on the signals stack (§9.142, #133).
- **The gate watcher in `run_matsim.py`** reads all twelve modes every `RUN.gate.interval_iterations` = 100 and stops the JVM at `CAL.gate.stop_deviation_pct` (§9.137); its source is the progress digest, never a log tail (§9.139); its stop is keyed on `--gate-json`, never the printed `GATE:` line (§9.141, #112); retry every `RUN.gate.retry_interval_s` = 300 s (#131); `tests/check_gate_watcher.py` in CI.
- **`RUN.monitor.stall_s` = 300** is five `MemoryObserver` heartbeats at 60 s, so it does not go stale with the pace (§9.156).
- **The issue gate** (requirement 10, §9.140, §9.158, §9.160): `src/run/issue_gate.py` refuses a launch while an in-lane `awaiting-run` issue lacks a real `AWAITING-RUN: <measurement>` line; the lane is the overlay's `answers_issues`; `AWAITING-DECISION:` reports without blocking; `--allow-open-issues` needs `--override-reason`, ledgered. #49, #50 and #155 are the operator's decision.
- **The reader** `src/analyse/report_mode_ridership.py` prints twelve rows, never an umbrella `pt` row, submodes through the run's own schedule, and writes nothing (§9.87); `--it N`, `--trend` (`toward` / `AWAY` / `flat`), `--watch SECONDS`, `--truck-stations`.
- **Any written iteration is readable** (§9.120): trips and legs every `RUN.controler.write_trips_interval` = 10 (§9.147, §9.148), plans and events every `write_plans_interval` / `write_events_interval` = 100; `iteration_trips.py` derives trips from `<n>.experienced_plans.xml.gz` where no table exists (`--validate`).
- **The scoreboard is the newest ARM's, never a `failed` run's** (`build_status_board.py`, §9.168): it skips a run under the sweep floor on `RUN.controler.last_iteration` (§9.133), a family marked `"readings": "none"` (§9.148) and F33's `aborted_20260910T222830_300it_25pct`.
- **Targets**: `mode_targets_by_mode.csv` (`build_mode_targets.py`, §9.87) and `pt_boardings_targets.json` (§9.130), never `validation_targets.csv` (§12). `CAL.gate.stop_deviation_pct` = 20.0 and `CAL.gate.pass_deviation_pct` = 10.0 are `definition`, not swept (§9.87).
- **`src/calibrate/fit.py`**: `score_mode_share` folds `bike+taxi` to Other and `car+motorbike` to Vehicle driver (§9.87), unscorable targets listed with reasons (§9.80); `measure_iteration_modes.py` uses the same function (§9.83).
- **The run viewer** `src/analyse/run_view.py` (§9.170): every run from one picker, the iteration bar with cutoff and gate milestones, each mode as modelled, target and deviation coloured by the 10 % goal and 20 % stop bar, a congestion map in a map-app layout (§9.172); readings from `_readings.jsonl`, appended by the gate watcher.
- **The ceiling watcher is proven**: `aborted_20260910T205517_20it_1pct` declared `RUN.gate.wall_ceiling_h` 0.05 and stopped with `completion` `stopped_at_ceiling` at `reached_iteration` 3 (§9.164, #169). A gate interval is not a gate: `start_gate_watch` refuses without `RUN.monitor` (#131).
- **`CAL.objective.replication_band_pp` = 0.0** (`sweep_role: measurement`, bracket [0.0, 2.0]) is the objective's denominator, MEASURED before it is set by three arms differing only in `RUN.machine.seed` (§9.164, #163).

## How a reading is taken

- **The quantity is linked main-mode trips of target-LGA residents** (§9.83): `modestats.csv` counts PLANNED modes and events give LEGS across five LGAs; neither is a gate reading.
- **Heavy rail and light rail are read on modelled boardings per weekday**, all subpopulations × 1/fraction, heavy rail at its 24 disclosed stations only, × `CAL.pt.weekday_factor` = 1.0727 (§9.130); bus keeps its composition-derived trip share.
- **Truck is not on the person-trip denominator**: without `--truck-stations` the heavy-vehicle share is a level with no deviation (§9.101); with it, link entries at the classifying stations against `road_aadt_targets.csv`. Ferry's deviation is not printed (§9.87); freight rail is representation, not a fit (§9.91).
- **Read the trend, not the level** (§9.108, §9.120): a level read under innovation is not a statement about the model. Gated every 100 iterations, read every ten (§9.126); a cause on the yardstick or the demand is repaired between arms.
- **A milestone is MATSim's own tables** (§9.147): rail and tram boardings from the legs table (`transit_line`, `transit_route`, `access_stop_id`) where the plans are absent (§9.148); readable only when its experienced plans decompress to the end (§9.143).
- **The pairing funnel is read with the code** (§9.145, §9.146): `miss_window` in `output/ride_pairing.csv` never describes a declared pair; `miss_declared_absent` counts unpaired legs whose named driver brought no car leg; the rest have no `boundDriver`, seen only in the experienced plans.
- **Nothing is compared across a family, a sample fraction or a network build**; a boardings reading does not compare with an earlier trip-share reading (§9.130).

## What is measured

- **Arm 0 of F35 is a result, the first with a mode inside the band** (§9.169, `20260912T202242_300it_25pct`, `ran_to_last_iteration` at 300, 30.35 h; 158,442 linked resident trips): **2 of 12 inside 10 %** — car **+9.6 %**, motorbike **−5.6 %**; **6 at or past the stop bar** — bike +201.6 %, taxi +131.4 %, light rail −73.9 % (772 vs 2,954), ferry −63.3 %, heavy rail +54.6 % (10,092 vs 6,529), ride −41.6 %; walk −12.2 % and bus −15.8 % over 10 %; truck 5.6251 % level only; freight rail 405 of 405.
- **Ride's target is above its coverage** (§9.169): 20.60 % against **19.11 %** in the run's `modeChoiceCoverage1x.txt`, 19.11 % from it.27 on — fixed at the seed, unreachable by any constant (#86 superseded); pt coverage 17.53 %. A direction against the F32 result, not a comparison: walk −26.5 → −12.2, bus +44.8 → −15.8, heavy rail +220.6 → +54.6, car +11.3 → +9.6, motorbike +12.5 → −5.6 toward; bike +113.0 → +201.6 and light rail −58.6 → −73.9 away.
- **The fit pipeline ran on arm 0** (§9.169, `_fit.json` `is_a_result: true`): counts at 31 stations mean **+14.2 %**; occupancy **0.1871** against 0.3503, outside [0.2493, 0.394]; trip-geometry ratios bike 1.56, car 1.16, pt 0.56, ride 1.03, walk **5.34**, none in range; 31 targets unscorable.
- **The counts rung had measured the wrong roads for 25 days** (§9.163, #82 closed): `count_station_links.csv` regenerated, **197 rows, 0 unresolved**; `20260909T015217_300it_25pct` then reads counts at mean **+16.30 %**, median **−1.1 %**, **no station at zero**, against −89.35 % / −98.7 % / 7 zeros before.
- **The gate reports what a constant could reach** (§9.163): beside every breaching mode its choice-set coverage, a target ABOVE it marked unreachable — on both results only ride (20.05 % on F32, 19.11 % on arm 0).
- **The progress digest reads the bytes that arrived** (§9.163, #131): `run_view._read_markers` keeps a per-log offset (`tests/unit/test_incremental_log_read.py`). The board reads `_run.json` to call a run a result (§9.162); the `status.newest-arm-state` claim caught a stale RUNNING by a check.
- **The fit pipeline ran on the F32 result** (§9.162, `fit.py --run 20260909T015217_300it_25pct`): 5 survey targets at mean absolute error **4.734 pp**; 30 count stations at **91.69 %** with **7 modelled zeros** (before the #82 repair); occupancy **0.1860**; **32 targets unscorable**.
- **The reading point is a CONVERGENCE problem, not a measurement one** (§9.159, #163): the window (`CAL.gate.reading_window_iterations` = 40, sweep [20, 80], `report_mode_ridership.report_window`) measured worse than the point because the in-run movement is a monotone trend (`results/processed/_reading_window_measurement.json`); arm 0's drift it.250→300 is at most **0.128 pp** against a cutoff snap of **+1.683 pp** (§9.169).
- **The calibrated base is F4, arm `20260821T175907_1000it_25pct`**: 35 of 67 targets scorable, MAE 10.65 pp, `feasible=False`, ASCs at their priors (§9.64, §9.50); `params/C5_calibration.json` names it `best_tag` (§9.80); its light rail 1,260 boardings is a level (#84). Seed noise floor from the F4 pair: 0.11 pp per mode (§9.64).
- **Every arm between F4 and the F32 result ended at a gate reading**; the board's runs table says where (`results/INDEX.md`).

## What is open

- **The light rail's shortfall** is not supply and not the transfer; where its riders are is the open question at the next gate (§9.130, #30).
- **`--truck-stations` is holdout-bound**: whether to spend holdout on freight is the operator's decision (§9.101, #82).
- **`fit.py` folds for the SURVEY targets and not for the OBJECTIVE** (§9.87, §9.158): `score_mode_share` the five folded categories as a diagnostic, `score_goal_modes` the twelve modes; distinct by design.
- **The calibration search is built, wired and blocked** (§9.158): `--execute` refuses because iteration 100 cannot resolve the goal band; until the reading point changes the search is priced with `--plan` and not run.

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

- §9.172 — viewer in a map-app layout; checks required
- §9.170 — the run viewer, live twelve modes
- §9.169 — arm 0 a result; reader reads own schedule
- §9.168 — scoreboard skips a failed run
- §9.167 — the eighth report worked down
- §9.166 — one boardings source; eighth report
- §9.164 — ceiling watcher fires; gate needs monitor
- §9.163 — counts rung repaired; coverage bound reported
- §9.160 — gate stops passing on prose
- §9.158 — objective measures the goal; search blocked
- §9.157 — a third of pt routing unserved
