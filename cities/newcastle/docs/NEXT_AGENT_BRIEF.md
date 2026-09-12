# Brief for the next agent

**Written:** 12 September 2026, forty-fifth session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/arm-0-launch-and-report-skill`.
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS READING ARM 0.** It is running (§9.168): `20260912T202242_300it_25pct`,
`f35_baseline_25pct`, 300 iterations at 25 %, no control on, quoted 39.0 h +
33 min on the controler it executes, approved and enforced at a 44 h ceiling,
launched 12 September 20:22:42. Nothing else stands in front of the reading.
Read it at its gates; do not tune, do not launch a pair, do not run a report
before it reads.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **ARM 0 IS RUNNING** (`20260912T202242_300it_25pct`, pid in its `_meta.json`, started 20:22:42, iteration 0 when this was written). If it is `completed`, its `_run.json` says `ran_to_last_iteration` or names the boundary it stopped at; if `failed`, its `_meta.json` names the cause and `--warm-start` from the newest plans dump (every 25 iterations) is the relaunch (#192). | `python src/run/session_gate.py --digest` · `Get-Process java` · `python src/analyse/build_run_index.py` |
| **THE APPROVAL IS SPENT.** The 44 h ceiling on `f35_baseline_25pct.json` was approved for THIS launch; a relaunch, warm or cold, needs a fresh stated-cost approval. | `gh pr list --state open` · the overlay's `RUN.gate.wall_ceiling_h` |
| **F35 IS OPEN AND HAS NO READING.** It opened at the controler fix (`20260912T184108`, §9.168). Its probes: `20260912T184134_4it_1pct` (4 of 4, structural), `20260912T185005_4it_25pct` (**460.0 s** a recurring iteration, the price). F34 closed with no arm. | `results/INDEX.md` · `python src/analyse/compare_runs.py 20260912T135825_4it_25pct 20260912T185005_4it_25pct --anyway` |
| **THE NEWEST CITABLE READING IS STILL `20260909T015217_300it_25pct` at 300**, family F32: 0 of 12 inside 10 %, 8 past the stop bar. It compares with nothing after `20260912T184108`. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| The heap at 25 %: live 19.9-20.3 GB after a full collection on the two probes under 48 g; `RUN.machine.heap_per_fraction_gib` (87) is NOT re-declared on a 4-iteration probe. Arm 0's `gc.log` is the measurement. | `grep "Pause Full" results/raw/20260912T202242_300it_25pct/gc.log` |
| The issue ledger: 25 open, 24 `awaiting-run` with a measurement, #50 `decision-needed` (send the drafted TfNSW request). None filed or closed this session. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **553** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **457**; no data artefact changed this session. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle - **it will skip
while arm 0 runs; do not force it.**

## §1 The lane

**Read arm 0 at its gates, then the five pairs. Nothing else.**

0. **ARM 0'S GATES** (§9.168, #172). Every 100 iterations, and at 300:
   `python src/analyse/report_mode_ridership.py --run 20260912T202242_300it_25pct --it <n>`
   (`--trend` for the direction) - all twelve modes with coverage beside each
   (#174); `modes_car_car` against the roster's wait count (#86, #145); the
   sub-1 km share against 11.17 % (#30); the pt access and egress leg lengths
   and the count of stub walks over 1 km (#167, #183); the cutoff snap beside
   the level (§9.162); **`gc.log` against `_progress.json`** (#66) and the
   re-derivation of `RUN.machine.heap_per_fraction_gib` from the heap after a
   full collection at iteration 100+; taxi's refusal count against 81 % (#49).
   A reading is citable at `reached_iteration` and nowhere past it; only
   `ran_to_last_iteration` is a result (a warm-completed arm included, #192).
1. **THE NINTH REPORT after arm 0's first gate** - one report per reading.
   The skill now states its follow-on: file the upcoming risks, close the
   overtaken on evidence, fix everything fixable without a run, hand off.
2. **THE FIVE PAIRS** (#172): scoring (`RUN.replanning.score_msa_representation`
   = `at_innovation_cutoff`) → choice set (`plan_selector_for_removal` =
   `SelectRandom`, #174) → service quality (#175) → routers
   (`C.raptor.mode_cost_representation` = `mode_constant`) → submodes
   (`RUN.mode_choice.pt_submode_alternatives`, #49). Coverage on both sides.
   Each opens a family; each needs its own stated-cost approval, priced by
   `arm_cost.py` on arm 0's own clock (its milestones included).
3. **The ASC contraction test** stays HELD until arm 0 has read; bike is the
   mode it can answer (24.32 pp of headroom, §9.163).
4. **If arm 0 dies**: the cause from its `_meta.json`; if heap, the slope from
   `gc.log`; relaunch warm on a fresh approval.

**Decisions the user must take:** each pair's approval; whether to send the
drafted TfNSW bespoke-table request (#50, `docs/requests/`); the ninth
report's timing (after arm 0's first gate, by the cadence rule).

## §2 Traps — newest first, each with what it cost

1. **A NULL ROUTE IS A WHOLE-PLAN RE-ROUTE.** MATSim's `PersonPrepareForSim`
   hands the WHOLE plan to `PlanRouter` when ANY leg has no route, for EVERY
   plan the person holds. The engines' "leave it null and the router rebuilds
   it" cost 24 % of every CPU sample for as long as the taxi fleet has existed
   (§9.168). Never leave a route null in plan memory; route it yourself.
2. **A PRICE FROM ANOTHER BUILD IS NOT A PRICE.** The launcher quoted 21.7 h
   on a run that executed a different controler and stalled; the probe read
   555.5 s and 47 h. The pricer says "PRICED ON A DIFFERENT BUILD" - when it
   does, spend the 1.5 h probe before the 40 h arm (§9.168, §9.153).
3. **A PROFILE BEFORE A FIX, AND THE JAR BEFORE A THEORY.** The 2.2x was read
   as "the footpath network" until `profile_run.py` put a quarter of it in
   one MATSim method and `javap` on the pinned jar said why (§9.168). Replay
   the engine's own steps before paying six arms for a guess.
4. **A 4-ITERATION PROBE CARRIES NO PLAN MEMORY.** Its heap is a lower bound
   on the arm's; the slope is re-derived from the arm's `gc.log`, never from
   the probe (§9.168).
5. **A 1 % PROBE WITH A DIFFERENT THREAD COUNT COMPARES WITH NOTHING.** The
   F35 structural probe ran 8 qsim threads against the F34 probe's 16, and
   its "+30 % mobsim" was the threads (§9.168).
6. **A BOARD BLOCK GENERATED FROM A FAILED RUN IS STILL A FALSE CLAIM.** The
   scoreboard read a `failed` arm at iteration 90 for two days (§9.168).
7. **AN IMPORT THROUGH THE REPOSITORY ROOT WORKS ONLY FROM THE ROOT.**
   `verify_launch.py` failed on its first use after #181 (§9.168); the guard
   is `tests/unit/test_import_roots.py`.
8. **A CACHED MERGE THAT CANNOT SAY WHAT IT MERGED IS A STALE BUILD** (§9.167).
9. **A RECORDED OVERRIDE CAN EXECUTE NOTHING**; dry-run before spending an
   arm (§9.166). **A GATE INTERVAL IS NOT A GATE** (§9.164, #131).
10. **A REPORT PER SESSION REPEATS ITSELF** (§9.166). One per reading.

## §3 Standing directives and approvals

- **ARM 0's APPROVAL IS SPENT** on `20260912T202242_300it_25pct` (44 h ceiling,
  `RUN.gate.wall_ceiling_h`, enforced by the runner). No other approval
  stands; a relaunch or a pair arm needs its own, priced on the newest arm at
  the fraction and set as the ceiling.
- **Never compare across a family boundary.** F35 opened at `20260912T184108`
  (§9.168); F34 (the footpath rebuild) and everything before it compare with
  nothing after. A run is a result only if `_run.json` says
  `ran_to_last_iteration` (a warm-completed arm included, #192); a stopped arm
  is citable at its `reached_iteration`; a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural
  smoke probe may run at 1 %, says so, and is read for nothing (§9.159).
- **One arm at a time**; never recompile `.tools/classes` or
  `.tools/classes-signals` under one - `session_gate.py` skips the toolchain
  step while arm 0 runs, and `bootstrap_toolchain.py --verify` IS a recompile.
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
