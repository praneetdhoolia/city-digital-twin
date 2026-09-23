# Runs, harness and economics — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 23 September 2026 (sixty-second session) · **Record read through:** §9.212 · **Written against family:** `F36`

## What is built

- **The horizon is declared 250** (§9.169): `RUN.controler.last_iteration` 1000 → **250**, cutoff 200 (fraction 0.8), on arm 0's post-settle drift ≤ 0.128 pp; saves 3.8–4.6 h per 25 % arm; supersedes §9.142; the 30 run-input sets re-assembled.
- **A second arm is refused at preflight; a harness killed under a live JVM no longer aborts the run** (§9.169, §9.170, §9.177): `refuse_concurrent_arm` in `src/run/run_matsim.py` (it also asks the store whether a run is live); `reconcile_stale` reads a clean shutdown first and closes out a finished orphan, else tests `jvm_pid`; `CITYSIM_LAUNCH_STAMP` names a detached run after its task; an unjudged milestone is written to `_readings.jsonl`.
- **The launch detaches by default on Windows** (§9.177, D6, #225): `run.py` re-invokes itself detached; `--foreground` opts out; the scheduled child runs `--foreground`. **A run carries its own residents** (`_residents.csv.gz`, §9.177, #213), so a later demand rebuild changes no reading of it.
- **An orphaned run that reached its horizon is closed out as a result** (§9.176, D5, #225): `run.py --close-out <run>` (`close_out_orphan`) accepts a stale `running` card whose pids are dead, whose log ends in MATSim's clean shutdown with no unexpected-shutdown request, and whose last ENDED iteration - read from the log, never the digest - is the declared horizon; it writes `ran_to_last_iteration` through `close_out()`. A live, short or unclean run is refused. `tests/unit/test_close_out_orphan.py`.
- **The engines route what they re-mode** (§9.168, F35): a null-route leg had `PersonPrepareForSim` re-route every plan that ever carried a refused taxi request (24 % of CPU). `RemodeRestore.Remode` routes the re-moded trip on `global.numberOfThreads` workers and restores the original after the mobsim.
- **The heap rule re-measured on the footpath network** (§9.167, #183): `citysim.SharedModeNetworks` seeds one routing copy per distinct link set; `RUN.machine.heap_floor_gib` 9.6 → **15.6**; the 1 % overlays carry 18g, `f34_baseline_25pct` **48g**.
- **A stall is priced as neither pace nor setup** (§9.167); `--detach` runs every refusal first; the ceiling, stall and reconcile markers carry the last iteration that ENDED. The ceiling is held in the launcher's memory: it cannot be raised on a running arm (§9.174) - and a harness that dies takes the ceiling, stall and gate watchers with it (§9.176, #225).
- **Refusals and one kill** (§9.166; §9.161, #169): a heap below `RUN.machine.heap_floor_gib` + `RUN.machine.heap_per_fraction_gib` 87 × fraction; an overlay changing nothing emitted (`refuse_unrealised_overrides`); no `RUN.gate.wall_ceiling_h`, no launch; a log silent for `RUN.gate.stall_kill_s` = 1800 s → `stopped_at_stall`. `RUN.machine.gc_log` on by default; a warm start re-derives `RUN.replanning.fraction_to_disable_innovation` (#192); Task Scheduler log on (§9.136).
- **Dependencies pinned** at `==`, `tests/check_requirements.py` in CI; **build wall time** in `cities/<city>/data/_build_timing.json`, outside the hashed set (§9.158).
- **The store refuses to delete a run nobody can reconstruct** (`results_store.trim`, §9.158); `run.py --stop` extracts metrics (§9.158); `--stop` and `--list` need no valid registry (§9.141, #126); `RUN.storage.extract_grace_s` = 3600; `RUN.storage.raw_cap_gb` is gibibytes (§9.155, #132).
- **A run that ends at a DEFINED BOUNDARY closes itself out** (§9.143): last iteration, gate stop or `--stop` write `_run.json` and the findings; a crash writes none. `completion` is the result gate; only `ran_to_last_iteration` satisfies resume or anchors a base; `reached_iteration` is the last iteration that ENDED.
- **`arm_cost.py` prices the iteration an arm REPEATS** (§9.154, §9.155, §9.156, §9.177): excludes profiled runs, reads the run's own `output/stopwatch.csv`, warns when the priced run met no milestone, compares `controler_sha256` (§9.160); setup is read from the JVM's stopwatch when the harness memo is short (the orphaned pair had quoted 48.8 h with 22.8 h of setup; 26.6 h after); each family is priced by its own unprofiled probe overlay (F36: `f36_pricing_probe_25pct`, §9.212).
- **One front door.** `run.py` resolves a scenario × day-type set through `src/city.py`, applies a `--run-config` overlay and `--set` overrides; `--iterations` has no default (§9.43); runs are named `<launch>_<iterations>it_<pct>pct` (§9.65). **Resume identity**: `find_completed` matches every parameter plus `controler_sha256`, `values_sha256` (§9.104) and `inputs_sha256` (§9.127); no hash, no match.
- **Three records per run.** `_meta.json`, the status card (§9.66; a refused launch writes a `failed` card under `aborted_`, §9.141, #127, #128); `_progress.json` every `RUN.monitor.progress_interval_s` = 30 s against `RUN.monitor.pace_band_s` = [217, 253] and `RUN.monitor.solo_check_iterations` = [2, 5] (§9.72, #76); `_run.json` at a defined boundary (§9.143).
- **The results store** (§9.137): `results/raw/<run>` under `RUN.storage.raw_cap_gb` = 500, trimmed oldest-first, never live runs; `results/processed/<run>` keeps the findings forever; nobody edits `results/` by hand. Trim is off the launch path (§9.141, #132, #137).
- **The runner gates its own run** (§9.137): every `RUN.gate.interval_iterations` = 100 the watcher reads the twelve modes and at `CAL.gate.stop_deviation_pct` kills the JVM, writing `_gate_stop.json`; iteration source `_progress.json` (§9.139); keyed on the reporter's verdict file, retried every `RUN.gate.retry_interval_s` = 300 s (§9.141, #112, #131). `run.py --stop <name> --cause` is the one manual path.
- **Detached launch** `run.py ... --detach` registers the task `citysim_run_<stamp>` (#70, §9.72) and is verified by `verify_launch.py --stamp <stamp>`, which waits for THAT run's directory: during setup the bare form took the newest directory - the previous, completed run - and answered TOOK (§9.212). **A dead run says why**: the watcher, `--stop` or the next harness start writes the cause (§9.66, §9.137); `run_failure.py --check` gates every terminal record from the log's last 64 MiB (§9.136).
- **Warm restart** `--warm-start` resumes from the newest plans checkpoint; crash recovery, not a continuation (#75, §9.76). **Live view** on `RUN.monitor.port` = 8731 (§9.36).
- **The toolchain** is pinned by sha256 in `.tools/toolchain.json`: JDK 25.0.4+7, pt2matsim 26.6 embedding MATSim 2027.0-2026w25 (§9.73), Maven 3.9.9, the 201-jar signals run stack (§9.76); `--verify` recompiles both class trees (§9.156).

## What is measured — what a run costs

- **F36 is priced on its own build: the recurring iteration is 469.5 s, +35 %** (§9.212, `20260923T022419_4it_25pct`, `ran_to_last_iteration` at 4, wall 4,542 s, controler `cbc97779cea8827a`): iterations 2–3 against 348.5 s on the scoring pair; it.0 776 s (532 before), it.1 625 s (440), setup 29 min (22). 250 iterations quote **33.2 h** with NO milestone in it, ~34 h with the milestones carried at +35 %, spread 24.8–34.0 h (`arm_cost.py`). A four-iteration probe cannot separate the Java fold's in-mobsim work (§9.210) from the rebuilt demand (§9.211).
- **F36's arm 0 is running at the approved 42 h ceiling** (§9.212, `20260923T034632_250it_25pct`, overlay `f36_baseline_25pct`, 48g): launched 03:46 on 23 September; not a result until its record. Its pace is the board's runs block and `watch_run.py`, not this page.
- **The scoring pair landed in 25.77 h against a 33.0 h ceiling and a 27.2 h quote** (§9.177, D7; `20260916T063903_250it_25pct`, 48g: wall 92,774.9 s; recurring iteration **348.5 s** over 244 plain iterations; the probe `20260916T053153_4it_25pct` priced it at 383 s/it): iterations ran 400–510 s while that session's rebuilds and test suites shared the CPU and ~264 s in the innovation-off tail (`output/stopwatch.csv`); the it.100/150/200/250 dumps 628–862 s.
- **The heap is measured on a full arm, and it does not slope** (§9.169, `gc.log`, #66): live heap after a full collection 21.2 GB at 8.9 h, peak 26,863 MB at 22.9 h, 21.4 GB at 30.2 h; GC under 1 % of wall. The rule (`RUN.machine.heap_floor_gib` 15.6 + `RUN.machine.heap_per_fraction_gib` 87 × 0.25 = 37.4 GiB) holds 11 GiB over the peak; the slope is not re-declared on one arm; no stall. F36's probe read 15,585 MB live after its last full collection at iteration 4 (§9.212, `gc.log`) - too short to re-measure the slope.
- **Wall-time-only controler fields.** `RUN.controler.write_events_interval` / `write_plans_interval` = **100** in the registry (`write_trips_interval` stays at 10; §9.147); `RUN.controler.create_graphs` off for long arms (§9.56, §9.59). `RUN.controler.last_iteration` = **250** since 14 September 2026 (§9.169).
- **Threads.** `RUN.machine.threads` = 16 (qsim, run identity, §9.147), `RUN.machine.replanning_threads` = 20, `RUN.machine.event_handler_threads` = 4 (§9.56, §9.59, §9.155). **A run is NOT bit-reproducible** (§9.142): three runs of one build gave 5,620,710 / 5,620,410 / 5,620,710 iteration-0 events, so an A/B claim needs a band, not a diff.

## Rules that stand

- **No multi-hour run without explicit approval; approvals are spent on use** (§9.57, §9.62, §9.72): every earlier approval is SPENT (§9.139, §9.169, §9.174, §9.177); the 42 h of 23 September is SPENT on `20260923T034632_250it_25pct` (§9.212). **No approval stands.** **25 % runs only** (user, 1 Sep).
- **One arm at a time** (#66): the stall hit both concurrent arms at once; three arms on 63.5 GiB grew the pagefile 8.1 → 19.1 GiB (§9.5). Enforced by `refuse_concurrent_arm` (§9.169).
- **Never recompile `.tools/classes` while an arm runs; `--verify` IS a recompile** (§9.156): breached 8 September, so `aborted_20260908T012355_4it_25pct` is citable for nothing. No earlier arm's bytecode is on disk (§9.158).
- **No open issue behind a run, and a label is not evidence** (GOAL.md requirement 10, §9.140): `run.py` refuses while an open issue in the run's lane lacks an `AWAITING-RUN: <measurement>` line (`src/run/issue_gate.py`); the lane is what the overlay declares. `--allow-open-issues` needs `--override-reason` and is ledgered; used once (§9.156).
- **Launch detached** (§9.72, #70). **Never compare across fractions or families** (§9.12, `docs/run_families.json`); a probe under 250 iterations is never a result (§9.7, §9.43). **A toolchain change is a model change** (§9.76). **Read the trend, not the level** (§9.108, §9.120). Watch a run by stamp glob, not by path (`NEXT_AGENT_BRIEF.md` trap 4).

## What is open

- **A surrogate/emulator calibration route is held in reserve** (Bayesian optimisation over a random-forest surrogate of parameters → aggregate shares): ~150 evaluations at 7.66 h to a gate (`aborted_20260908T100009_300it_25pct`, §9.157) is ~48 days at 25 %; start only if the ASC contraction test shows a multi-parameter residual. **The published result behind ~150 is not yet cited here.**
- **#66 — the machine-level stall**: a 10 % iteration once took 2,415 s against ~20 s; unattributed. The F21 arm's iteration 30 (355 s) is one more candidate (§9.134); arm 0's 30.35 h showed none (§9.169).
- **Builds and test suites under an arm stretch its iterations** (§9.177, `20260916T063903_250it_25pct`): 383 s on the idle probe against 400–510 s under this session's rebuilds — batch them, run them at below-normal priority, and never read a pace taken under them as the arm's price.
- `RUN.monitor.pace_band_s` = [217, 253] is the 25 % × 1000 band (§9.72); F28 ran above it, the unprofiled plain iteration 216.0 s below, arm 0's median 347.34 s above throughout (§9.169), so the flag means nothing until re-measured (`departure_requires`).

## Refused — do not re-raise

- **Migration off MATSim** (BEAM, POLARIS, Hermes, DSim) (§9.73).
- **~10× per-iteration speed-up** without shrinking the physical work (§9.59).
- **`oneThreadPerHandler`** (measured fatal) and **`synchronizeOnSimSteps=false`** (measured regression) (§9.59).
- **FIFO link dynamics** for speed — `PassingQ` stands on correctness at ~42 s/it (§9.59).
- **Hand-named runs**, **`_aborted_<date>` quarantine parents** (§9.65, §9.66) and any by-hand rename, delete or edit under `results/` (§9.137).
- **Resuming a record without `values_sha256` or `inputs_sha256`** (§9.104, §9.127).
- **Deleting anything from `results/processed`** — findings are permanent (§9.137).

## History

- §9.212 — F36 priced; arm 0 launched
- §9.177 — scoring pair launched; detach default
- §9.176 — the pair lands at 27.4 h; its harness died at it.34
- §9.174 — the routers pair launched at 30.0 h; 498 s/it
- §9.172 — the recompiled controler priced: 422 s
- §9.170 — concurrent arm refused at preflight
- §9.169 — arm 0 lands at 30.35 h; the horizon declared 250
- §9.168 — footpath iteration profiled; engines route re-modes
- §9.167 — the heap floor re-measured; a stall is not setup
- §9.166 — heap rule, stall kill, override refusal
- §9.164 — four probes; the ceiling watcher's first stop
- §9.163 — 21.5 h uninterrupted; stall unattributed
