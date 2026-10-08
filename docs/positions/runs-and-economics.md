# Runs, harness and economics — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 8 October 2026 (sixty-fifth session) · **Record read through:** §9.222 · **Written against family:** `F39`

## What is built

- **The horizon is declared 250** (§9.169): `RUN.controler.last_iteration` 1000 → **250**, cutoff 200 (fraction 0.8), on arm 0's post-settle drift ≤ 0.128 pp; saves 3.8–4.6 h per 25 % arm; supersedes §9.142; the 30 run-input sets re-assembled.
- **A second arm is refused at preflight; a harness killed under a live JVM no longer aborts the run** (§9.169, §9.170, §9.177): `refuse_concurrent_arm` in `src/run/run_matsim.py` (it also asks the store whether a run is live); `reconcile_stale` reads a clean shutdown first and closes out a finished orphan, else tests `jvm_pid`; `CITYSIM_LAUNCH_STAMP` names a detached run after its task; an unjudged milestone is written to `_readings.jsonl`.
- **A loaded host is refused before the JVM starts** (§9.220, §9.221): `refuse_unsafe_host` refuses while free RAM is below `RUN.machine.xmx` + `RUN.machine.free_ram_margin_gib` (**6** GiB, assumed, sweep 2–12; overridable at launch, recorded on the run) or a process holds more than `RUN.machine.other_process_max_cores` (**2.0**, assumed, sweep 0–4; the WMI provider host at 1.8 cores is this host's baseline); `run.py` refuses an arm below `RUN.sample.arm_fraction_floor` (**0.25**) without `--override-reason`.
- **Every host sample is a run output** (§9.220, §9.221): `progress_digest` appends each 30 s sample to `_host.jsonl` (`host.schema.json`) with `other_cpu_pct`, the CPU of every process outside the run (the whole-host figure holds the run's own threads and refused the first probe at 98 %); `arm_cost.py` refuses a probe whose outside-the-run CPU exceeded `RUN.machine.probe_max_host_cpu_pct` (**90**, assumed, sweep 75–100; an older history by its busiest co-tenant), names the process, and prints the control's wall as the pair quote.
- **One innovation cutoff, one watcher skeleton** (§9.220): `iteration_reading.innovation_off_after` serves `run_matsim`, `watch_run` and `run_view` (`watch_run.projection` had computed it without `first_iteration`, 200 against 83 on the F38 resume); the ceiling, stall and gate watchers share `_start_bound_watch`. The scheduler proof reads the task's numeric state; `--detach` on POSIX launches in its own session with a proof file (`tests/unit/test_detach_every_platform.py`).
- **The heap rule re-measured on the footpath network** (§9.167, #183): `citysim.SharedModeNetworks` seeds one routing copy per distinct link set; `RUN.machine.heap_floor_gib` 9.6 → **15.6**; the 1 % overlays carry 18g, `f34_baseline_25pct` **48g**.
- **A stall is priced as neither pace nor setup** (§9.167); `--detach` runs every refusal first; the ceiling, stall and reconcile markers carry the last iteration that ENDED. The ceiling is held in the launcher's memory: it cannot be raised on a running arm (§9.174).
- **Refusals and one kill** (§9.166; §9.161, #169): a heap below `RUN.machine.heap_floor_gib` + `RUN.machine.heap_per_fraction_gib` 87 × fraction; an overlay changing nothing emitted (`refuse_unrealised_overrides`); no `RUN.gate.wall_ceiling_h`, no launch; a log silent for `RUN.gate.stall_kill_s` = 1800 s → `stopped_at_stall`. `RUN.machine.gc_log` on by default; a warm start re-derives `RUN.replanning.fraction_to_disable_innovation` (#192).
- **Dependencies pinned** at `==` (`tests/check_requirements.py`, §9.158, §9.219).
- **The store refuses to delete a run nobody can reconstruct** (`results_store.trim`, §9.158); `run.py --stop` extracts metrics (§9.158); `--stop` and `--list` need no valid registry (§9.141, #126); `RUN.storage.extract_grace_s` = 3600; `RUN.storage.raw_cap_gb` is gibibytes (§9.155, #132).
- **A run that ends at a DEFINED BOUNDARY closes itself out** (§9.143): last iteration, gate stop or `--stop` write `_run.json` and the findings; a crash writes none. `completion` is the result gate; only `ran_to_last_iteration` satisfies resume or anchors a base; `reached_iteration` is the last iteration that ENDED.
- **A run the host will restart under is not launched** (§9.213, user decision): `run_matsim.refuse_unsafe_host` refuses while Windows has a restart pending or its update pause ends before the run's `RUN.gate.wall_ceiling_h` (`procs.restart_pending`, `procs.updates_paused_until`); active hours cap at 18 h and an arm runs 25–42 h, so the user pauses updates before a launch. A card's pids are dead once the host booted after its `started` (`procs.card_pid_alive`), so `--stop` never kills a recycled pid.
- **`arm_cost.py` prices the iteration an arm REPEATS** (§9.154, §9.156, §9.177): excludes profiled runs, reads the run's own `output/stopwatch.csv`, warns when the priced run met no milestone, compares `controler_sha256` (§9.160); setup is launch to the stopwatch's BEGIN of iteration 0 (`launch_to_first_iteration_s`, §9.213); each family is priced by its own probe overlay, and its control's wall once it has one (§9.220).
- **One front door.** `run.py` resolves a scenario × day-type set through `src/city.py`, applies a `--run-config` overlay and `--set` overrides; `--iterations` has no default (§9.43); runs are named `<launch>_<iterations>it_<pct>pct` (§9.65). **Resume identity**: `find_completed` matches every parameter plus `controler_sha256`, `values_sha256` (§9.104) and `inputs_sha256` (§9.127); no hash, no match.
- **Three records per run.** `_meta.json`, the status card (§9.66; a refused launch writes a `failed` card under `aborted_`, §9.141, #127, #128); `_progress.json` every `RUN.monitor.progress_interval_s` = 30 s against `RUN.monitor.pace_band_s` = [217, 253] and `RUN.monitor.solo_check_iterations` = [2, 5] (§9.72, #76); `_run.json` at a defined boundary (§9.143).
- **The results store** (§9.137): `results/raw/<run>` under `RUN.storage.raw_cap_gb` = 500, trimmed oldest-first, never live runs; `results/processed/<run>` keeps the findings forever; nobody edits `results/` by hand. Trim is off the launch path (§9.141, #132, #137).
- **The runner gates its own run** (§9.137, §9.139, §9.141): the gate watcher is the monitoring page's ([monitoring-and-gates](monitoring-and-gates.md)); `run.py --stop <name> --cause` is the one manual path.
- **Detached launch is the only arm launch, and the default on Windows** (#70, §9.72, §9.177, §9.215, D6, #225): `run.py` re-invokes itself detached (`--foreground` opts out; the scheduled child runs `--foreground`), registers `citysim_run_<stamp>` and refuses an arm in `--foreground` (F38 arm 0 died with its session at 79); `verify_launch.py --stamp <stamp>` waits for its run (§9.212).
- **A dead run says why** (§9.66, §9.137): `--stop` records a run found dead as `died`, which `--warm-start` resumes from the newest plans checkpoint (crash recovery, not a continuation, #75, §9.76); `run_failure.py --check` gates every terminal record (§9.136).
- **The toolchain** is pinned by sha256 in `.tools/toolchain.json`: JDK 25.0.4+7, pt2matsim 26.6 embedding MATSim 2027.0-2026w25 (§9.73), Maven 3.9.9, the 201-jar signals run stack (§9.76); `--verify` recompiles both class trees (§9.156). The engines' routing of what they re-mode is the ride and taxi pages' (§9.168).

## What is measured — what a run costs

- **F39's treatment arm is RUNNING under D29** (§9.221, §9.222; the run name and state are the board's): relaunched 14:48 after two Start-menu restarts killed it, at a 40 h ceiling, `RUN.machine.xmx` **38g** (the heap rule's floor at 25 %) with the memory margin overridden to **2** GiB on a host holding 39–46 GiB free; the guards first refused it on memory, the one-core bar and an overlay with no declared lane.
- **The ATAP probe `20261008T114753_4it_25pct`** (38g, §9.221): plain iterations **359 and 387 s**, the fourth 537 s beside the operator's Blender (1.0–2.14 cores, 8.1 GiB free); 18 full collections, the longest 10.6 s. Pair quote the control's **27.9 h**, the band's top **37 h**; the pricer refuses the probe as a price for its co-tenant.
- **F39's control landed within 1 % of its probe's quote** (§9.219, `20260929T072135_250it_25pct`): probe `20260929T060320_4it_25pct` at 390.0 s, the median settled near 347 s; the 30 September daytime probes quoted 27.7–50.5 h on a loaded host - the control's own wall is the quote for its pair.
- **The sixteenth report's performance verdict** (§9.220): the horizon is reachable at the measured pace; the result-preserving levers sum to about 3 h of 27.85, and halving an arm needs the mobsim profiled first (#231).
- **The heap is measured on a full arm, and it does not slope** (§9.169, `gc.log`, #66): live heap after a full collection 21.2 GB at 8.9 h, peak 26,863 MB at 22.9 h, 21.4 GB at 30.2 h; GC under 1 % of wall. The rule (`RUN.machine.heap_floor_gib` 15.6 + `RUN.machine.heap_per_fraction_gib` 87 × 0.25 = 37.4 GiB) holds 11 GiB over the peak; the slope is not re-declared on one arm; no stall.
- **Wall-time-only controler fields.** `RUN.controler.write_events_interval` / `write_plans_interval` = **100** in the registry (`write_trips_interval` stays at 10; §9.147); `RUN.controler.create_graphs` off for long arms (§9.56, §9.59). `RUN.controler.last_iteration` = **250** since 14 September 2026 (§9.169).
- **Threads.** `RUN.machine.threads` = 16 (qsim, run identity, §9.147), `RUN.machine.replanning_threads` = 20, `RUN.machine.event_handler_threads` = 4 (§9.56, §9.59, §9.155). **A run is NOT bit-reproducible** (§9.142): three runs of one build gave 5,620,710 / 5,620,410 / 5,620,710 iteration-0 events, so an A/B claim needs a band, not a diff.

## Rules that stand

- **No multi-hour run without explicit approval; approvals are spent on use** (§9.57, §9.62, §9.72): every approval to date is SPENT on its arm (§9.139 through §9.219; D28's control approval on F39's control). **No approval stands.** **25 % runs only** (user, 1 September 2026; `RUN.sample.arm_fraction_floor`, §9.220).
- **One arm at a time** (#66): the stall hit both concurrent arms at once; three arms on 63.5 GiB grew the pagefile 8.1 → 19.1 GiB (§9.5). Enforced by `refuse_concurrent_arm` (§9.169).
- **Never recompile `.tools/classes` while an arm runs; `--verify` IS a recompile** (§9.156): breached 8 September, so `aborted_20260908T012355_4it_25pct` is citable for nothing. No earlier arm's bytecode is on disk (§9.158).
- **No open issue behind a run, and a label is not evidence** (GOAL.md requirement 10, §9.140): `run.py` refuses while an open issue in the run's lane lacks an `AWAITING-RUN: <measurement>` line (`src/run/issue_gate.py`); the lane is what the overlay declares. `--allow-open-issues` needs `--override-reason` and is ledgered; used once (§9.156).
- **Never compare across fractions or families** (§9.12, `docs/run_families.json`); a probe under 250 iterations is never a result (§9.7, §9.43). **A toolchain change is a model change** (§9.76). **Read the trend, not the level** (§9.108, §9.120). Watch a run by stamp glob, not by path (`NEXT_AGENT_BRIEF.md` trap 4).

## What is open

- **A surrogate/emulator calibration route is held in reserve** (§9.157): ~150 evaluations at 7.66 h to a gate (`aborted_20260908T100009_300it_25pct`) is ~48 days at 25 %; start only if the ASC contraction test shows a multi-parameter residual; the published result behind ~150 is not yet cited here.
- **#66 — the machine-level stall**: a 10 % iteration once took 2,415 s against ~20 s; unattributed. The F21 arm's iteration 30 (355 s) is one more candidate (§9.134); arm 0's 30.35 h showed none (§9.169).
- **Builds and test suites under an arm stretch its iterations** (§9.177, `20260916T063903_250it_25pct`): 383 s on the idle probe against 400–510 s under this session's rebuilds — batch them, run them at below-normal priority, and never read a pace taken under them as the arm's price.
- `RUN.monitor.pace_band_s` = [217, 253] is the 25 % × 1000 band (§9.72); arm 0's median 347.34 s sat above it throughout (§9.169), so the flag means nothing until re-measured (`departure_requires`).

## Refused — do not re-raise

- **Migration off MATSim** (BEAM, POLARIS, Hermes, DSim) (§9.73).
- **~10× per-iteration speed-up** without shrinking the physical work (§9.59).
- **`oneThreadPerHandler`** (measured fatal) and **`synchronizeOnSimSteps=false`** (measured regression) (§9.59).
- **FIFO link dynamics** for speed — `PassingQ` stands on correctness at ~42 s/it (§9.59).
- **Hand-named runs**, **`_aborted_<date>` quarantine parents** (§9.65, §9.66) and any by-hand rename, delete or edit under `results/` (§9.137).
- **Resuming a record without `values_sha256` or `inputs_sha256`** (§9.104, §9.127).
- **Deleting anything from `results/processed`** — findings are permanent (§9.137).

## History

- §9.222 — two restarts; the arm relaunched
- §9.221 — the arm launched; bars measured
- §9.220 — a loaded host is refused
- §9.219 — a probe prices the host
- §9.214 — F37 lands; F38 priced
- §9.213 — a host restart cannot take an arm
- §9.212 — F36 priced; arm 0 launched
- §9.177 — scoring pair launched; detach default
- §9.176 — the pair lands at 27.4 h; its harness died at it.34
- §9.174 — the routers pair launched at 30.0 h; 498 s/it
- §9.172 — the recompiled controler priced: 422 s
- §9.170 — concurrent arm refused at preflight
- §9.169 — arm 0 lands at 30.35 h; the horizon declared 250
- §9.168 — footpath iteration profiled; engines route re-modes
