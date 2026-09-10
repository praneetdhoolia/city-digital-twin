# Brief for the next agent

**Written:** 10 September 2026, fortieth session · **Open family:** `F32-crowding-reaches-scoring` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/equilibrium-project-report`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**THE MACHINE IS IDLE, NO ARM RAN, AND THE CALIBRATION HAS A CEILING NOBODY HAD
MEASURED.** MATSim writes the choice-set coverage table on every arm and nothing
in this repository read it. A scoring constant reallocates between plans an agent
already holds, so a mode's coverage is an arithmetic ceiling on its share — and
on the landed result **ride's target of 20.6000 % sits above the 20.05 % of
agents who have ever held a ride plan**. No value of any constant closes ride's
−41.0 %.

The session's other finding, in one sentence: **fourteen of the sixteen issues
marked `awaiting-run` were waiting for a run that had already finished**, and
their measurements were takeable from `20260909T015217_300it_25pct` without
launching anything.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE MACHINE IS IDLE and NO APPROVAL STANDS.** No arm ran this session; the 32 h was spent on the landed arm two sessions ago. Any multi-hour run needs a new stated-cost approval. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **THE NEWEST CITABLE READING IS STILL `20260909T015217_300it_25pct` at iteration 300**: 0 of 12 inside 10 %, 8 past the stop bar. Its `_fit.json` is the only one with `is_a_result: true`. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| **THE CHOICE-SET BOUND is now printed beside every gate verdict**, and ride is the only mode whose target exceeds its coverage. | `python src/analyse/report_choice_set_coverage.py --run 20260909T015217_300it_25pct --against-targets` (`--trend` for where each set closed) |
| **THE DEPLOYED BYTECODE CHANGED AGAIN and no family opened.** `.tools/classes` now carries running counts on both mixed-subtour diagnostics. **The next launch opens a family whatever it carries.** | `python -c "import json;print(list(json.load(open('cities/newcastle/docs/run_families.json'))['families'])[-1])"` |
| The issue gate reads **22 open, 9 awaiting a run, 6 awaiting implementation, 7 awaiting a decision, 0 blocking**. Every one of the nine is a PAIRED arm or a probe. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **499** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke), undeclared MATSim defaults **21**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python src/registry/check_matsim_defaults.py` |
| One derived artefact changed: `data/processed/validation/count_station_links.csv`. | `python tests/check_package.py` (LOCAL; check 7b is the new one) |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle.

## §1 The lane

**Decide the ORDER the three one-field controls are spent in. Then run one arm.**

1. **THREE CONTROLS EXIST, EACH OPENS A FAMILY, AND THEY ALL MOVE THE SAME
   QUANTITY** (§9.163, #172). The open question is still why running to
   convergence made the fit worse, and the three candidate causes now have
   unequal footing:
   - **scoring** — `RUN.replanning.score_msa_representation` =
     `at_innovation_cutoff`. Declared this session at `absent`, which emits the
     literal MATSim's own dump records for its default, so the shipped model is
     byte-identical to the one that ran. Turning it on introduces **no new
     number** (it emits the innovation cutoff already declared) and it is the
     only candidate that predicts BOTH measured symptoms — the +2.211 pp car
     snap and the average plan score peaking at 19.2049 then falling to 14.5679;
   - **the routers** — `C.raptor.mode_cost_representation` = `mode_constant`,
     built, deployed and never run. Ceiling: pt reaches 25.78 % of agents;
   - **the choice set** — `replanning.planSelectorForRemoval` is
     `WorstPlanSelector` against a plan memory of 8, an undeclared MATSim
     default (#174, #155). It has **no control** until it is declared.
   **Design the separation before spending an arm.** Nothing may be tuned on the
   landed reading until it exists — §9.159's scoped departure, still in force.
2. **READ COVERAGE ON BOTH ARMS OF EVERY PAIR FROM NOW ON** (#174). Making a
   mode's plans score worse makes them the ones MATSim deletes, so a crowding
   arm (#98) or a raptor arm (#49) can report a share fall that is a smaller
   choice set rather than a changed preference. The reader exists; use it.
3. **#169 — the ceiling watcher is BUILT and UNPROVEN, and the machine is idle**
   (§9.161). The 1 % smoke probe with a deliberately tiny
   `RUN.gate.wall_ceiling_h`; the observable is that the run stops inside it and
   closes out `stopped_at_ceiling`. Cheap, and it clears an
   `awaiting-implementation`.
4. **#167 — ONE ATTRIBUTE, AND A REBUILD** (§9.161). Emit `routingMode` per leg
   in `build_matsim_plans.py` and rebuild the demand and the 30 run-input sets in
   the SAME change, then re-run `intermodal_access_probe_1pct`. The same field
   (`routing.accessEgressType` = `none`) is why a car trip costs only its travel
   time and 18 c/km, which is why car takes **63.12 %** of sub-kilometre trips.
5. **The ASC contraction test stays HELD** (§9.160) — but bike is now *confirmed*
   to be the one mode it can answer, at 24.32 pp of headroom.

**Decisions the user must take:** the order of the three controls and at what
stated cost (no approval stands); whether `planSelectorForRemoval` and the other
20 undeclared MATSim defaults become registry fields (#155, #174); whether
`beta_headway` / `beta_reliability` are wired or retired (#175 — the gradient
precedent does NOT transfer); whether the declared passenger of an escort pair is
put on `ride` at the demand (#86, #48); the three product calls behind #49, #50
and #155; whether the real Newcastle corridor operates transit signal priority
(`A.lightrail.tsp_enabled` is `source: assumed`, settled on corridor evidence and
never on light rail's −57.3 %); and whether the Task Scheduler operational log is
enabled, without which #66 stays unattributable (#66).

## §2 Traps — newest first, each with what it cost

1. **AN ISSUE CAN WAIT FOR A RUN THAT HAS ALREADY HAPPENED.** Sixteen issues
   carried `awaiting-run` with a stated measurement, and fourteen were takeable
   from an arm that finished the day before. `awaiting-run` marks what an issue
   needs, not whether it has it. **After every landed arm, sweep the ledger
   before designing the next one** (§9.163).
2. **A COVERAGE PERCENTAGE CANNOT BOUND A BOARDINGS COUNT.** The first draft of
   the gate's choice-set line printed "coverage 25.78 % < target 6528.5551" and
   called heavy rail unreachable. Heavy and light rail are boardings per weekday;
   motorbike and truck are locked carves whose share legitimately exceeds their
   coverage. **Both refusals are in the reader — do not remove them** (§9.163).
3. **A DIAGNOSTIC CAPPED AT N DUMPS CANNOT DECIDE A CLOSE CONDITION.** #96 asks
   that the stand-aside path log nothing on a full arm; it logged exactly five,
   because the dump was capped at five. The issue was undecidable by any arm at
   any horizon and nobody noticed for weeks (§9.163).
4. **"PROVEN TO REACH" IS NOT "DOING SOMETHING".** `check_hardcoding` nudges a
   field and watches the config bytes move. Three fields pass that test and are
   switched off at their shipped value. They now declare `inert_at` (§9.163).
5. **A LINK ID IS NOT A ROAD.** MATSim re-issues link ids on every network
   rebuild. The count-station map was written 47 minutes before its network was
   rewritten and measured the wrong roads for 25 days with every gate green.
   **Any artefact keyed on link ids must be rebuilt with the network** — check 7b
   now enforces it for this one (§9.163).
6. **A GENERATED BLOCK CAN ASSERT SOMETHING NO CHECK READS**, and prose outside
   `check_doc_currency`'s claims can be false for weeks: twelve position pages
   said "Nothing here is a result" for a day after one landed (§9.162, §9.163).
7. **RELAXED IS NOT CONVERGED.** `relaxed: true` says mode share stops moving
   after innovation is off. The cutoff snap says how far the search still was —
   2.2 pp of car (§9.162).
8. **A HOOK'S ARGUMENTS DECIDE WHAT CAN BE PRICED THERE.** `getInVehicleCost` is
   handed no distance and no stop identity, so the fare and a distance term could
   not be built. **Read the signature before designing the mechanism** (§9.162) —
   this applies directly to #175.
9. **A MID-RUN PACE READING IS NOT THE RUN'S PACE.** The median went to 301.5 s
   between iterations 120 and 190 and closed at 244.05 s, inside the band
   (§9.162).
10. **Do not compare across a family boundary**, however tempting the story.
    `F32` opened at `20260909T011135` (§3.5, §9.160). **A run is a result only if
    `_run.json` says `ran_to_last_iteration`**; a stopped arm is a citable
    reading at its `reached_iteration` and nowhere past it (§9.143).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Any multi-hour run needs a new stated-cost approval,
  priced on the landed arm's `median_iteration_s` of 244.05 s and on a probe of
  whatever bytecode it will run.
- **25 % runs only** (user directive, 1 September 2026) — for ARMS. A structural
  smoke probe whose whole output is a yes or a no may run at 1 %, says so in its
  overlay, and may not be read for any share, count or fit (§9.159).
- **One arm at a time**; never recompile `.tools/classes` under one —
  `bootstrap_toolchain.py` refuses, with `--force-compile` as the deliberate
  override.
- **A launch with no automatic stop of either kind is refused** before the JVM
  starts (§9.163, #169). Turning the gate watcher off stays legitimate; it costs
  one more line on the overlay, beside the approval that line encodes.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement**
  (GOAL requirement 10), with the third state from §9.160
  (`decision-needed` / `awaiting-implementation` + `AWAITING-DECISION:`) reported
  at every gate and never blocking.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — these
  three stay FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder` in the
  registry and are out of the movable set for that reason.
- **Nothing may be tuned on the landed arm** until the separation in §1.1 is
  designed — §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
