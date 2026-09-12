# Brief for the next agent

**Written:** 12 September 2026, forty-fourth session · **Open family:** `F34-walk-has-a-footpath-network` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/report-eight-findings-and-decisions`.
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS THE RUN, AND NOTHING ELSE IS LEFT IN FRONT OF IT.** This
session worked every defect, risk and smell of the eighth report and every
open issue to fixed or awaiting-run (§9.167): the pt access leg walks a
network (#167), the network is rebuilt with its footpaths and every feed
re-mapped once (#183, family F34), the four consolidations landed
byte-identical, and the freight, ferry and fleet observations are in the
package. Arm 0 is `f34_baseline_25pct`. Ask for the approval, launch, read.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE MACHINE IS IDLE and NO APPROVAL STANDS.** The 26 h line on `f34_baseline_25pct.json` is the 10 September approval carried over from F33's overlay, SPENT on the arm that died; a launch needs a fresh stated-cost approval. | `python src/run/session_gate.py --digest` · `Get-Process java` |
| **F34 IS OPEN AND HAS NO READING.** It opened at the network rebuild (`20260912T062457`, §9.167); its five 1 % probes are citable for a yes or a no and for nothing else; `20260912T065939_4it_1pct` ran 4 of 4 at **40 s an iteration** (29.5 s on the road graph), `teleported=0`. | `python src/analyse/build_run_index.py` · `results/INDEX.md` |
| **ARM 0's COST IS UNPRICED ON THIS NETWORK.** The last priced arm at 25 % is F33's (225.0 s recurring, `20260910T215129_4it_25pct`); the 1 % pace rose 35 %. The launcher prices on the newest arm at the fraction - read its quote, do not carry the 19.0 h forward. | `python run.py --run-config f34_baseline_25pct --dry-run` |
| **THE HEAP RULE IS 15.6 + 87 × fraction GiB** (re-measured at 1 %, §9.167): 37.4 GiB at 25 %, the overlay carries **48g** on a 63 GB machine; the 25 % slope is unmeasured on this network and arm 0's `gc.log` is its reading. | `python run.py --run-config f34_baseline_25pct --dry-run` prints the rule beside the heap |
| **THE NEWEST CITABLE READING IS STILL `20260909T015217_300it_25pct` at 300**, family F32: 0 of 12 inside 10 %, 8 past the stop bar. Nothing in F33 or F34 has a reading. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| The issue ledger: every open issue is awaiting a run or a decision; #183 and #184 closed to awaiting-run, #50 awaits the operator sending the drafted request. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **553** fields, **959** manifest files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **455**, `check_package.py` passed on the rebuilt package (12 September). | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |
| The import roots are installed for the interpreter (`.pth`, #181); a fresh clone's first `run.py` or `session_gate.py` installs them. | `python src/setup/install_paths.py --check` |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle.

## §1 The lane

**Launch arm 0 on a fresh approval, then the five pairs in the decided
order. Do not redesign it, and do not run a report before it reads.**

0. **ARM 0** (§9.167, #172): `f34_baseline_25pct.json` — no control on, 48 g,
   GC log on, `create_graphs` off, stall kill at 1800 s, plans dumped every 25
   iterations, the ceiling line to be set to whatever is approved. Launch with
   `--detach` so the arm outlives the session. It measures the demand fix
   (#86, #48, #145, #30) on a walk network with footpaths for the first time,
   and is the control half of all five pairs. Read at its gates: all twelve
   modes with coverage beside each (#174); `modes_car_car` against the
   roster's wait count; the sub-1 km share against 11.17 %; the pt access and
   egress leg lengths and the stub count (#167, #183); the cutoff snap beside
   the level; and **`gc.log` against `_progress.json`** (#66) — and re-derive
   `RUN.machine.heap_per_fraction_gib` from its heap after a full collection.
1. **THE FIVE PAIRS** (#172): scoring (`RUN.replanning.score_msa_representation`
   = `at_innovation_cutoff`) → choice set (`plan_selector_for_removal` =
   `SelectRandom`, switching BOTH removal paths, #174) → service quality
   (#175) → routers (`C.raptor.mode_cost_representation` = `mode_constant`) →
   submodes (`RUN.mode_choice.pt_submode_alternatives`, #49). Coverage on both
   sides of every pair. Each opens a family; each needs its own approval.
2. **The ASC contraction test** — the `C.asc.*` constants reach the run from
   the registry (§9.166). It stays HELD until arm 0 has read; bike is the mode
   it can answer (24.32 pp of headroom).
3. **After arm 0's gate, the ninth report** — one report per reading.
4. **If arm 0 dies of heap**, the slope is the finding: a longer route on a
   finer graph is plan memory; re-measure both fields from the `gc.log` and
   relaunch warm from the newest plans dump (`--warm-start`, a result by #192).

**Decisions the user must take:** the approval for arm 0; whether to send the
drafted TfNSW bespoke-table request (#50, `docs/requests/`); the ninth
report's timing (after arm 0's gate, by the cadence rule).

## §2 Traps — newest first, each with what it cost

1. **A CACHED MERGE THAT CANNOT SAY WHAT IT MERGED IS A STALE BUILD.**
   `merge_osm` reused `multimodal.osm` whenever it existed; the footway harvest
   would have been silently absent. Keyed on its inputs' hashes now (§9.167).
2. **ONE ROUTING NETWORK PER MODE IS SEVEN COPIES OF A TIME-VARIANT NETWORK.**
   The first probe on the footpath network died at 10.1 GiB; five of the seven
   copies were the same link set (`SharedModeNetworks`, §9.167). Measure heap
   with a histogram (`jcmd <pid> GC.class_histogram`), not by guessing.
3. **THE REFUSAL WAS OURS.** `PrepareForMobsim`, not `PrepareForSim`; the ride
   engine re-moding one leg of a five-leg trip; "20 agents" was the thread
   count (§9.167, #167). Replay the framework's steps on the dead probe's own
   inputs before blaming the framework.
4. **A BUILDER THAT WROTE ITS ARTEFACT ONCE AND CHANGED ITS WRITER LEAVES AN
   ARTEFACT NOBODY CAN REPRODUCE.** The ten signal schedules sat unreproducible
   from 7 to 12 September; rebuilding on a whim found it (§9.167).
5. **A BUILD ORDER HIDES UNTIL A REBUILD.** The crossings read the assembled
   run-input set while the assembler refused to run without the crossings; the
   signals builder prefers a dwell schedule the README never listed, ran before
   it, and derived from the PREVIOUS mapping's file. `check_package.py` is the
   net; run it after any rebuild, in the README's order (§9.167).
6. **A REGEX THAT MATCHES `sys` MISSES `_sys_t`.** The first import-root sweep
   left 46 files; the second removed a nested tuple assignment nobody used
   "elsewhere" (`bearing()` in the signals builder). Audit a mechanical edit's
   diff for lines that are not the pattern.
7. **A RULE IN A DESCRIPTION IS NOT A RULE** (§9.166): declare a rule as
   fields. **AN OBSERVER IS NOT A STOP** (§9.166). **A RECORDED OVERRIDE CAN
   EXECUTE NOTHING** (§9.166): dry-run before spending an arm.
8. **AN OVERLAY WRITTEN AGAINST ANOTHER OVERLAY COPIES WHAT ITS AUTHOR WAS
   LOOKING AT** (§9.165): the heap. A pricing probe prices time, not heap.
9. **A REPORT PER SESSION REPEATS ITSELF** (§9.166). One per reading.
10. **A GATE INTERVAL IS NOT A GATE** (§9.164, #131).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Quote the launcher's price on the newest arm at the
  fraction and set `RUN.gate.wall_ceiling_h` to what is approved.
- **Never compare across a family boundary.** F34 opened at `20260912T062457`
  (§9.167); every family before it ran walk on the road graph. A run is a
  result only if `_run.json` says `ran_to_last_iteration` — a warm-completed
  arm included (#192); a stopped arm (gate, ceiling, stall, operator) is
  citable at its `reached_iteration`; a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural
  smoke probe may run at 1 %, says so, and is read for nothing (§9.159).
- **One arm at a time**; never recompile `.tools/classes` or
  `.tools/classes-signals` under one — both paths refuse (§9.166).
- **A launch with no automatic stop is refused**; so is one whose heap is below
  the registry's rule, and one whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated
  measurement** (GOAL requirement 10); `decision-needed` /
  `awaiting-implementation` with an `AWAITING-DECISION:` line is reported,
  never blocking. Declare `answers_issues` on a new overlay.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** —
  FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder`.
- **Nothing may be tuned on the landed arm** until the separation of #172 has
  run — §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12); all 26 station rows
  are holdout and the heavy-rail target keeps summing them, saying so (#189).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
