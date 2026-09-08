# Brief for the next agent

**Written:** 9 September 2026, thirty-eighth session · **Open family:** `F32-crowding-reaches-scoring` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/the-loop-that-closes-on-twelve-numbers`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**AN ARM IS RUNNING.** `20260909T015217_300it_25pct` — 300 iterations at 25 %,
launched 01:52 and verified into iteration 0 at 02:00. It is **the first arm
since F4 on 21 August permitted past iteration 100** and the first ever to run a
crowding disutility. Everything else this session found waits on what it reads.

The session's finding, in one sentence: **four of the twelve modes are decided
in a layer that has no control variable**, so the calibration search was never
the binding constraint.

## §0 Verify first - facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE DEPTH ARM IS RUNNING.** Quoted **22.3 h** from 01:52, so it should land about **00:10 on 10 September**; the approved ceiling is **32 h**, which falls at **09:52 on 10 September**. | `python src/run/session_gate.py --digest` (MACHINE line) · `python src/run/run_view.py` |
| **ITS CEILING IS ENFORCED BY NOBODY** (#169). It disables the gate watcher by a scoped departure, so it has no automatic stop on deviation OR on cost. If it overruns, stop it by hand. | `python run.py --stop 20260909T015217_300it_25pct --cause "past the approved 32 h ceiling"` |
| **NOTHING IT PRODUCES IS A READING UNTIL IT LANDS**, and no parameter may be tuned on anything it reads (§9.159's scoped departure). The newest CITABLE reading is still F31's iteration-100 gate. | `python src/analyse/report_mode_ridership.py --run aborted_20260908T100009_300it_25pct --it 100` |
| **Family `F32-crowding-reaches-scoring` opened at `20260909T011135`** — at the probe's LAUNCH, not the arm. Nothing before it compares with anything after it. | `python -c "import json;print(list(json.load(open('cities/newcastle/docs/run_families.json'))['families'])[-1])"` |
| The issue gate reads **21 open, 16 awaiting a run with a stated measurement, 5 awaiting a decision, 0 blocking**. The five are #49, #50, #155, #167, #169. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **494** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke). | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| The store, now carrying the probe and the running arm. | `python src/run/results_store.py --report` |

Then: `python src/run/session_gate.py`. **It skips the toolchain step while an
arm runs** — and since this session `bootstrap_toolchain.py` refuses to compile
under one by itself, so the rule finally has a mechanism.

## §1 The lane

**Read the arm. Then give layer 3 a control.**

1. **WHEN THE ARM LANDS, IT TESTS THREE FALSIFIABLE PREDICTIONS** (§9.160). This
   session derived them at zero machine cost from the F31 arm's own trajectory,
   and they are the point of the exercise:
   - the system settles about **iteration 200–210** (Aitken extrapolation: car
     within 1 % of its asymptote by ~130, bike by ~208, average plan score by
     ~195, which is **24 % below its asymptote at iteration 100**);
   - **`ride` does not move** — it is already converged at **−38.0 %**, decay
     r **0.054**, asymptote equal to its it-100 value to five decimals;
   - **`car`, the only mode inside the band, drifts further out** (+2.41 %
     relative still to come).
   Any of them being wrong is worth as much as its being right. Read with
   `report_mode_ridership.py --run <arm> --it <n>` at several `n`, and
   `--trend`.
2. **GIVE LAYER 3 A CONTROL — decided, designed, NOT built** (§9.160, user
   decision). The mode constant, the fare and a distance term go into the
   raptor's cost. Established against the pinned jar by `javap`:
   `RaptorInVehicleCostCalculator.getInVehicleCost(...)` is handed the
   `Vehicle`, so the submode is recoverable from the vehicle type and the call
   is **once per boarding** — where an ASC belongs in a router — and
   `CapacityDependentInVehicleCostCalculator` is SBB's own precedent for the
   shape. Ship it behind a new `C.raptor.mode_cost_representation` = `absent`,
   the one-gate discipline `C.crowding.representation` already uses. **It is
   what finally gives `C.time_weights.beta_headway` (0.5) and
   `beta_reliability` (1.3) a consumer** — both reach
   `params/C1_parameters.json` at `build_params.py:99-100` and reach MATSim
   through nothing. Java, so it opens a family; it could not be compiled this
   session because an arm was running.
3. **The ASC contraction test stays HELD** until that control exists (§9.160,
   user decision). Of its four modes only **bike** sits on an alternative the
   mode-choice operator can switch to; on bus, light rail and ferry a null
   result proves nothing, because only **974 of 154,347 agents (0.63 %)** hold
   plans that differ in pt submode.
4. **#169 — build the wall-clock ceiling watcher on an idle machine.** A
   declared `RUN.gate.wall_ceiling_h`, a watcher beside `start_gate_watch` that
   stops through the existing marker path, and a 1 % smoke probe with a
   deliberately tiny ceiling to prove it fires. Minutes of work; it could not be
   done this session because it sits in the launch path of the arm it protects.

**Decisions the user must take:** how the last hop onto a platform is made
(#167); whether to build #169's watcher; the three product calls behind #49,
#50 and #155; whether the **real Newcastle corridor operates transit signal
priority** (`A.lightrail.tsp_enabled` is `source: assumed`, requirement 6 says
derive it, and it is settled on evidence about the corridor, never on light
rail's −47.2 %); #66's Task Scheduler log.

## §2 Traps - newest first, each with what it cost

1. **A CHECK CAN BE SATISFIED BY PROSE DESCRIBING THE CHECK.** The issue gate
   read *"0 blocking"* while three issues opened *"This issue BLOCKS the
   launcher"*: its regex matched `` `AWAITING-RUN:` `` inside a **code span** —
   how every document here refers to the convention rather than invokes it — and
   captured the sentence explaining why writing one would be inventing a
   measurement. It also matched its own `<measurement>` placeholder. **A token
   inside a code span is a mention, not a use** (§9.160).
2. **A FIX VERIFIED AGAINST THE HALF OF THE CODE IT CHANGED IS NOT VERIFIED.**
   `evaluate()` was fixed to send `--config-set` and its new test asserted
   `"'--config-set'" in src` — the SENDING half. `_run.json` still recorded the
   raw `--set` channel, so a candidate would have died **after paying a full
   arm's wall clock** (§9.160).
3. **PROSE CANNOT READ A NEGATION.** The lane was scraped with `#(\d+)` over an
   overlay's description, so writing "#167 is deliberately NOT in this lane" put
   #167 straight back in — and `default_25pct`, what a bare `python run.py`
   selects, had a lane of **{5}** from the sentence "issue #5 re-measures
   relaxation" (§9.160). Declare `answers_issues`.
4. **AN OVERLAY CAN DESCRIBE AN ARM IT IS NOT.** The depth arm's description
   asserted it carried the #167 repair at `access_egress_basis = network`; its
   `set` block never set it, and §9.159 had ruled that basis fatal. **Resolve
   the overlay and read the value, never the prose** (§9.160).
5. **A PRICE IS FOR A STACK.** `arm_cost` filters on fraction and profiled and
   nothing else, so it quoted 22.2 h from five arms that all predated the new
   bytecode. It now compares `controler_sha256` — but the lesson stands:
   **probe the build before spending an approval on it** (§9.160, §9.153).
6. **A PROBE THAT "STARTS" HAS NOT PASSED.** Read it to its end and read its
   record, not its exit code (§9.159).
7. **AVERAGING REMOVES NOISE, NOT TREND.** The windowed reading was built and
   measured worse than the point it replaced, because every mode's series is
   monotone (§9.159).
8. **Do not compare across a family boundary**, however tempting the story.
   `F32` opened at `20260909T011135` (§3.5, §9.160).
9. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** A
   stopped arm is a citable reading at its `reached_iteration` and nowhere past
   it (§9.143).

## §3 Standing directives and approvals

- **THE 32 h APPROVAL IS SPENT.** It was spent on `20260909T015217_300it_25pct`
  at 01:52 on 9 September, on a re-priced quote of **22.3 h** after a 39.6-minute
  probe of the same bytecode. **No approval stands.** Any further multi-hour run
  needs a new stated-cost approval.
- **25 % runs only** (user directive, 1 September 2026) — for ARMS. A structural
  smoke probe whose whole output is a yes or a no may run at 1 %, says so in its
  overlay, and may not be read for any share, count or fit (§9.159).
- **One arm at a time**; never recompile `.tools/classes` under one — and since
  §9.160 `bootstrap_toolchain.py` refuses to, with `--force-compile` as the
  deliberate override.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement**
  (GOAL requirement 10). It now has a third state: an issue may carry
  `decision-needed` or `awaiting-implementation` and a line
  `AWAITING-DECISION: <what, and who takes it>`, which is reported at every gate
  and launch and does not block (§9.160).
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`.** Three
  constants were opened at §9.158 with the departure logged; these three stay
  FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder` in the registry and
  are out of the movable set for that reason, which is a modelling judgement.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
