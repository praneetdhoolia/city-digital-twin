# Runs, harness and economics — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Two runs are results - F32's `20260909T015217_300it_25pct` and F35's arm 0 `20260912T202242_300it_25pct`, each `completion` `ran_to_last_iteration` at iteration 300 (§9.162, §9.169); nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 14 September 2026 (forty-eighth session) · **Record read through:** §9.171 · **Written against family:** `F35`

## What is built

- **The horizon is declared 250** (§9.169): `RUN.controler.last_iteration` 1000 → **250**, cutoff 200 (fraction 0.8), on arm 0's post-settle drift ≤ 0.128 pp; saves 3.8–4.6 h per 25 % arm; supersedes §9.142; the 30 run-input sets re-assembled.
- **A second arm is refused at preflight; a harness killed under a live JVM no longer aborts the run** (§9.169, §9.170): `refuse_concurrent_arm` in `src/run/run_matsim.py`; `reconcile_stale` tests `jvm_pid`; `CITYSIM_LAUNCH_STAMP` names a detached run after its task; an unjudged milestone is written to `_readings.jsonl`. Unit suite 469.
- **The engines route what they re-mode** (§9.168, F35): a null-route leg had `PersonPrepareForSim` re-route every plan that ever carried a refused taxi request (24 % of CPU). `RemodeRestore.Remode` routes the re-moded trip on `global.numberOfThreads` workers and restores the original after the mobsim.
- **A 25 % footpath-network iteration decomposed** (§9.168, `20260912T162831_4it_25pct`): routing 54 %, mobsim 24 %, events 13.6 %; `NetworkDirectWalkPtRouter.calcRoute` 16.0 % - 203,447 of 300,000 pt requests had no transit route (#162, awaiting-run).
- **The heap rule re-measured on the footpath network** (§9.167, #183): `citysim.SharedModeNetworks` seeds one routing copy per distinct link set; `RUN.machine.heap_floor_gib` 9.6 → **15.6**; the 1 % overlays carry 18g, `f34_baseline_25pct` **48g**.
- **A stall is priced as neither pace nor setup** (§9.167); `run.py --detach` runs every refusal before the Task Scheduler; the ceiling, stall and reconcile markers carry the last iteration that ENDED.
- **Refusals and one kill** (§9.166; §9.161, #169): a heap below `RUN.machine.heap_floor_gib` + `RUN.machine.heap_per_fraction_gib` 87 × fraction; an overlay changing nothing emitted (`refuse_unrealised_overrides`); no `RUN.gate.wall_ceiling_h`, no launch; a log silent for `RUN.gate.stall_kill_s` = 1800 s → `stopped_at_stall`. `RUN.machine.gc_log` on by default; a warm start re-derives `RUN.replanning.fraction_to_disable_innovation` (#192); Task Scheduler log on (§9.136).
- **Dependencies pinned** at `==` in `requirements.txt`, `tests/check_requirements.py` parsing the repository's imports in CI (§9.158). **Build wall time** lands in `cities/<city>/data/_build_timing.json`, outside the hashed set (§9.158).
- **The store refuses to delete a run nobody can reconstruct** (`results_store.trim`, §9.158); `run.py --stop` extracts metrics (§9.158); `--stop` and `--list` need no valid registry (§9.141, #126); `RUN.storage.extract_grace_s` = 3600; `RUN.storage.raw_cap_gb` is gibibytes (§9.155, #132).
- **A run that ends at a DEFINED BOUNDARY closes itself out** (§9.143): last iteration, gate stop or `--stop` write `_run.json` and the findings; a crash writes none. `completion` is the result gate; only `ran_to_last_iteration` satisfies resume or anchors a base; `reached_iteration` is the last iteration that ENDED.
- **Three by-hand operations are scripts** (§9.155): `session_gate.py --fix` regenerates stale artefacts; `compare_runs.py` refuses a cross-family, cross-fraction or profiled/unprofiled pair unless `--anyway`; `verify_launch.py` executes the #70 sentence.
- **`arm_cost.py` prices the iteration an arm REPEATS** (§9.154, §9.155, §9.156): excludes profiled runs, reads the run's own `output/stopwatch.csv`, warns when the priced run met no milestone, compares `controler_sha256` (§9.160); the unprofiled pricing probe is the overlay `f30_plain_probe_25pct`.
- **One front door.** `run.py` resolves a scenario × day-type set through `src/city.py`, applies a `--run-config` overlay and `--set` overrides; `--iterations` has no default (§9.43); runs are named `<launch>_<iterations>it_<pct>pct` (§9.65). **Resume identity**: `find_completed` matches every parameter plus `controler_sha256`, `values_sha256` (§9.104) and `inputs_sha256` (§9.127); no hash, no match.
- **Three records per run.** `_meta.json`, the status card (§9.66; a refused launch writes a `failed` card under `aborted_`, §9.141, #127, #128); `_progress.json` every `RUN.monitor.progress_interval_s` = 30 s against `RUN.monitor.pace_band_s` = [217, 253] and `RUN.monitor.solo_check_iterations` = [2, 5] (§9.72, #76); `_run.json` at a defined boundary (§9.143).
- **The results store** (§9.137): `results/raw/<run>` under `RUN.storage.raw_cap_gb` = 500, trimmed oldest-first, never live runs; `results/processed/<run>` keeps the findings forever; nobody edits `results/` by hand. Trim is off the launch path (§9.141, #132, #137).
- **The runner gates its own run** (§9.137): every `RUN.gate.interval_iterations` = 100 the watcher reads the twelve modes and at `CAL.gate.stop_deviation_pct` kills the JVM, writing `_gate_stop.json`; iteration source `_progress.json` (§9.139); keyed on the reporter's verdict file, retried every `RUN.gate.retry_interval_s` = 300 s (§9.141, #112, #131). `run.py --stop <name> --cause` is the one manual path.
- **Detached launch** `run.py ... --detach` registers the task `citysim_run_<stamp>` (#70, §9.72). **A dead run says why**: the watcher, `--stop` or the next harness start writes the cause (§9.66, §9.137); `run_failure.py --check` gates every terminal record from the log's last 64 MiB (§9.136).
- **Warm restart** `--warm-start` resumes from the newest plans checkpoint; crash recovery, not a continuation (#75, §9.76). **Live view** on `RUN.monitor.port` = 8731 (§9.36).
- **The toolchain** is pinned by sha256 in `.tools/toolchain.json`: JDK 25.0.4+7, pt2matsim 26.6 embedding MATSim 2027.0-2026w25 (§9.73), Maven 3.9.9, the 201-jar signals run stack (§9.76); `--verify` recompiles both class trees (§9.156).
- **F33's four 1 % probes are citable for a yes/no only** (§9.164). **F33's first arm died on a heap nobody set** (§9.165): `aborted_20260910T222830_300it_25pct`, `OutOfMemoryError` at iteration 98 on the registry's 14g; a 4-iteration probe prices TIME, not HEAP; `reconcile_stale()` reads the run's own log first.

## What is measured — what a run costs

- **Arm 0 landed in 30.35 h against a 39.0 h quote and a 44 h ceiling** (§9.168, §9.169, `20260912T202242_300it_25pct`: wall 109,260.8 s, rc 0). Recurring iteration **346.0 s** over 287 plain iterations (`median_iteration_s` 347.34); the pace fell from ~400 s to ~255 s and the band [217, 253] was not met. The next 300-iteration arm is quoted **30.4 h** (`arm_cost.py --run-config f35_baseline_25pct`), ~25.5 h at 250; the 44 h approval is SPENT.
- **The heap is measured on a full arm, and it does not slope** (§9.169, `gc.log`, #66): live heap after a full collection 21.2 GB at 8.9 h, peak 26,863 MB at 22.9 h, 21.4 GB at 30.2 h; GC under 1 % of wall. The rule (`RUN.machine.heap_floor_gib` 15.6 + `RUN.machine.heap_per_fraction_gib` 87 × 0.25 = 37.4 GiB) holds 11 GiB over the peak; the slope is not re-declared on one arm; no stall.
- **The footpath network costs 555.5 s a recurring 25 % iteration on F34's controler and 460.0 s on F35's** (§9.168; `20260912T135825_4it_25pct` → `20260912T185005_4it_25pct`) against F33's 244.5 s: prepareForMobsim 92 → **2** s, mobsim 328 → **262** s; +88 % at 25 % against +35 % at 1 %.
- **The longest window the stall will ever get, and it did not kill the arm** (§9.163, #66, `20260909T015217_300it_25pct`): 300 iterations in 21.5 h; one pace excursion (running median 301.5 s over it.120–190, closing at 244.05 s) was a false alarm. 37.4 % of all machine hours bought no citable reading; this arm had no automatic stop, now refused (#169).
- **The first run since F4 to execute its declared horizon** (§9.162, `20260909T015217_300it_25pct`): wall 77,309 s, `median_iteration_s` 244.05, quoted 22.3 h against a 32 h ceiling, 3.6 % under; the pace rose to 308.2 s over it.160–180 and recovered, so `RUN.monitor.pace_band_s` brackets the whole-run median, not the middle third.
- **The store's two biggest tenants were reclaimed** (§9.159, #164): 336.4 GiB, raw 467.1 → 130.7 GiB; `results_store` gained `reclaim()` and `report()`. A 25 % arm's log is ~51 GiB by its gate (§9.156).
- **Memory.** 25 % arms peaked ~27 GiB under the two-arm pattern (§9.62) and 33–38 GiB on 40g alone (§9.43); ≈ 24 GiB fixed + 0.09–0.3 MB/agent, so 100 % does not fit the 63.5 GiB machine (§9.43, §9.5). The registry default `RUN.machine.xmx` = 14g is the §9.5 model; every arm overrides it.
- **Threads.** `RUN.machine.threads` = 16 (qsim, run identity, §9.147), `RUN.machine.replanning_threads` = 20 (§9.59), `RUN.machine.event_handler_threads` = 4 (wall-time only; 1 saturated, 12 buys nothing, 2 is 44.5 % slower, §9.56, §9.59, §9.155). **A run is NOT bit-reproducible** (§9.142): three runs of one build gave 5,620,710 / 5,620,410 / 5,620,710 iteration-0 events; shares identical, so an A/B claim needs a band, not a diff.
- **Wall-time-only controler fields.** `RUN.controler.write_events_interval` / `write_plans_interval` = **100** in the registry (`write_trips_interval` stays at 10; §9.147); `RUN.controler.create_graphs` off for long arms (§9.56, §9.59). `RUN.controler.last_iteration` = **250** since 14 September 2026 (§9.169; 1000 measured relaxed under the uniform seed, §9.43).

## Rules that stand

- **No multi-hour run without explicit approval; approvals are spent on use** (§9.57, §9.62, §9.72): the 2 Sep directive was SPENT on `20260901T165115_300it_25pct` (§9.139), arm 0's 44 h on `20260912T202242_300it_25pct` (§9.169). **No approval stands.** **25 % runs only** (user, 1 Sep).
- **One arm at a time** (#66): the stall hit both concurrent arms at once; three arms on 63.5 GiB grew the pagefile 8.1 → 19.1 GiB (§9.5). Enforced by `refuse_concurrent_arm` (§9.169).
- **Never recompile `.tools/classes` while an arm runs; `--verify` IS a recompile** (§9.156): breached 8 September, so `aborted_20260908T012355_4it_25pct` is citable for nothing. No earlier arm's bytecode is on disk (§9.158).
- **No open issue behind a run, and a label is not evidence** (GOAL.md requirement 10, §9.140): `run.py` refuses while an open issue in the run's lane lacks an `AWAITING-RUN: <measurement>` line (`src/run/issue_gate.py`); the lane is what the overlay declares. `--allow-open-issues` needs `--override-reason` and is ledgered; used once (§9.156).
- **Launch detached** (§9.72, #70). **Never compare across fractions or families** (§9.12, `docs/run_families.json`); a probe under 250 iterations is never a result (§9.7, §9.43). **A toolchain change is a model change** (§9.76). **Read the trend, not the level** (§9.108, §9.120). Watch a run by stamp glob, not by path (`NEXT_AGENT_BRIEF.md` trap 4).

## What is open

- **A surrogate/emulator calibration route is held in reserve** (Bayesian optimisation over a random-forest surrogate of parameters → aggregate shares): ~150 evaluations at 7.66 h to a gate (`aborted_20260908T100009_300it_25pct`, §9.157) is ~48 days at 25 %; start only if the ASC contraction test shows a multi-parameter residual. **The published result behind ~150 is not yet cited here.**
- **#66 — the machine-level stall**: a 10 % iteration once took 2,415 s against ~20 s; unattributed. The F21 arm's iteration 30 (355 s) is one more candidate (§9.134); arm 0's 30.35 h showed none (§9.169).
- `src/run/run_failure.py` quotes the first exception it finds: the F20 arm's `cause_detail` names a benign Guice/ASM warning beside a stop by direction.
- `RUN.monitor.pace_band_s` = [217, 253] is the 25 % × 1000 band (§9.72); F28 ran above it, the unprofiled plain iteration 216.0 s below, arm 0's median 347.34 s above throughout (§9.169), so the flag means nothing until re-measured (`departure_requires`).

## Refused — do not re-raise

- **Migration off MATSim** (BEAM, POLARIS, Hermes, DSim) (§9.73).
- **~10× per-iteration speed-up** without shrinking the physical work (§9.59).
- **`oneThreadPerHandler`** (measured fatal) and **`synchronizeOnSimSteps=false`** (measured regression) (§9.59).
- **FIFO link dynamics** for speed — `PassingQ` stands on correctness at ~42 s/it (§9.59).
- **A larger settle margin** to pass the drift-tolerance sweep (§9.43).
- **Hand-named runs**, **`_aborted_<date>` quarantine parents** (§9.65, §9.66) and any by-hand rename, delete or edit under `results/` (§9.137).
- **Resuming a record without `values_sha256` or `inputs_sha256`** (§9.104, §9.127).
- **Deleting anything from `results/processed`** — findings are permanent (§9.137).

## History

- §9.170 — concurrent arm refused at preflight
- §9.169 — arm 0 lands at 30.35 h; the horizon declared 250
- §9.168 — footpath iteration profiled; engines route re-modes
- §9.167 — the heap floor re-measured; a stall is not setup
- §9.166 — heap rule, stall kill, override refusal
- §9.165 — arm 0 dies at 98 on a 14g heap
- §9.164 — four probes; the ceiling watcher's first stop
- §9.163 — 21.5 h uninterrupted; stall unattributed
- §9.161 — the runner enforces its approved ceiling
- §9.160 — the new stack priced: +3.0 s
- §9.159 — 336.4 GiB reclaimed; `reclaim()` is the verb
- §9.157 — F31 gate: the band true, the point not
- §9.153 — F30 arm 45 % slower; `--stop` tested live
- §9.149 — F28 arm to its gate at 260 s
- §9.147 — milestone iterations cost double; threads probed
