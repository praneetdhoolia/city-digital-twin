# Brief for the next agent

**Written:** 10 September 2026, forty-first session · **Open family:** `F33-the-passenger-is-put-on-ride` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/resolve-every-open-issue`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**EVERY OPEN ISSUE IS NOW EITHER CLOSED, AWAITING ONE PAIRED ARM, OR AWAITING ONE
STATED DECISION — AND NO ARM RAN TO GET THERE.** The session spent under five
minutes of JVM on four 1 % structural probes and no approval. What it changed is
the demand: **a declared passenger is now put on `ride` in every seeded plan**,
as the declared driver has always been put on `car`, and that is the only layer
that can reach ride's target at all, because 20.6000 % sits above the 20.05 % of
agents who have ever held a ride plan.

The session's other finding, in one sentence: **§9.161's diagnosis of #167 was
half right.** Emitting `routingMode` on every leg — which that record named as
the whole fix — takes the `accessEgressModeToLink` failure from 40 agents to 20,
and the residual is measured to be nowhere in this project's own plans.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE MACHINE IS IDLE and NO APPROVAL STANDS.** Four 1 % probes ran and nothing else; any multi-hour run needs a new stated-cost approval. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **`F33-the-passenger-is-put-on-ride` IS OPEN AND HAS NO ARM.** It opened at `20260910T203622`. The demand, the plans and the 30 run-input sets were all rebuilt, so nothing before it compares with anything after it. | `python -c "import json;print(list(json.load(open('cities/newcastle/docs/run_families.json'))['families'])[-1])"` |
| **THE NEWEST CITABLE READING IS STILL `20260909T015217_300it_25pct` at iteration 300**, and it belongs to the family BEFORE the open one: 0 of 12 inside 10 %, 8 past the stop bar. None of this session's four probes may be read for any share, count or fit. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| **THE CEILING WATCHER IS PROVEN**: `aborted_20260910T205517_20it_1pct` closed `stopped_at_ceiling` at `reached_iteration` 3. | `python -c "import json;print(json.load(open('results/raw/aborted_20260910T205517_20it_1pct/_run.json'))['completion'])"` |
| The issue ledger after #131, #155 and #169 closed on evidence. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **514** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke), undeclared MATSim defaults **0**, unit tests **324**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python src/registry/check_matsim_defaults.py` · `python -m pytest tests/unit -q` |
| The demand artefacts changed; `check_package.py` has not been run since. | `python tests/check_package.py` (LOCAL) |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle.

## §1 The lane

**Decide the ORDER the five one-field controls are spent in. Then run one arm in
F33.**

1. **FIVE CONTROLS NOW EXIST, A SIXTH IS SPENT, AND THEY ALL MOVE THE SAME
   QUANTITY** (§9.164, #172). §9.163 counted three and said the choice-set branch
   had none; it has one now.
   - **scoring** — `RUN.replanning.score_msa_representation` =
     `at_innovation_cutoff`. Still the only candidate that predicts BOTH measured
     symptoms — the +2.211 pp car snap and the average plan score peaking at
     19.2049 then falling to 14.5679 — and it introduces no new number;
   - **the choice set** — `RUN.replanning.plan_selector_for_removal` =
     `SelectRandom` against the shipped `WorstPlanSelector` (#174). Coverage ranks
     the modes in the same order as their attractiveness, which is what a
     positive feedback between scoring and membership looks like;
   - **the routers** — `C.raptor.mode_cost_representation` = `mode_constant`,
     built, deployed and never run;
   - **service quality** — `C.time_weights.service_quality_representation`
     (#175). Bus +44.8 % against light rail −57.3 % is a service-quality
     inversion and these are the only declared parameters that push both the way
     they need to go;
   - **pt submodes** — `RUN.mode_choice.pt_submode_alternatives` (#49). Note what
     turning it ON costs: the umbrella leaves the choice set, so no plan-level
     trip can combine two submodes. **Read multi-leg pt trips on both arms.**
   - **SPENT: the demand.** `B.mode.bound_passenger_placement` = `every_plan`
     ships and the rebuilt package carries it. The first F33 arm measures it.
2. **THE FIRST F33 ARM ANSWERS #86 AND #145 TOGETHER.** The observable is whether
   `modes_car_car` falls toward zero **WITHOUT** the household roster's wait count
   rising to hold it — the roster ran 8,550 → 15,580 across the landed arm.
3. **READ COVERAGE ON BOTH ARMS OF EVERY PAIR** (#174). Making a mode's plans
   score worse makes them the ones MATSim deletes, so a crowding arm (#98), a
   raptor arm (#49) or a service-quality arm (#175) can report a share fall that
   is a smaller choice set rather than a changed preference. The reader exists.
4. **#167 IS NOW A DIAGNOSIS, NOT A REBUILD.** `routingMode` is emitted; the
   failure is 40 → 20 agents; the input has 0 multi-leg and 0 mixed trips over
   6,347 persons; `RUN.routing.access_egress_consistency_check` = `disable`
   changes nothing. What remains is to find where inside MATSim's own pre-sim
   pass the mixed-routing-mode trip is created. Until then a car trip carries no
   fixed cost at all, which is the sharpest single mechanism on the board.
5. **The ASC contraction test stays HELD** (§9.160) — bike is the one mode it can
   answer, at 24.32 pp of headroom against a 29.03 % coverage.

**Decisions the user must take:** the order of the five controls and at what
stated cost (no approval stands); whether any of the nine newly declared MATSim
defaults is worth spending an arm on; the product calls behind #49 and #50;
whether the real Newcastle corridor operates transit signal priority
(`A.lightrail.tsp_enabled` is `source: assumed`); and whether the Windows Task
Scheduler operational log is enabled — the elevated command was issued this
session and its UAC prompt was not accepted, so #66 stays unattributable.

## §2 Traps — newest first, each with what it cost

1. **A RECORDED DIAGNOSIS CAN BE HALF A DIAGNOSIS, AND THE HALF THAT IS RIGHT
   HIDES THE HALF THAT IS NOT.** §9.161 established, correctly and with
   measurement, that #167's failure was our plans declaring no `routingMode`. It
   was half the cause. The fix landed, the failure halved, and the run still died.
   **A cause that explains part of a count is not the cause** (§9.164).
2. **A GATE INTERVAL IS NOT A GATE.** `RUN.gate.interval_iterations` = 2 beside
   `RUN.monitor.enabled` = false produced no verdict, no gate line and no warning
   over a run that reached iteration 3, while the launch banner said the run had
   a modelling stop. The watcher now refuses to arm and the launch refusal reads
   all three fields (§9.164, #131).
3. **A BANNER THAT ROUNDS IS A BANNER THAT LIES.** The launch line printed
   `%.1f h`, so a 0.05 h ceiling was announced as 0.1 h; and a run stopped on cost
   announced itself as `STOPPED BY THE OPERATOR` while its own record said
   `stopped_at_ceiling` (§9.164).
4. **DECLARING A VALUE IN JAVA SHADOWS THE REGISTRY, AND THE CHECKER CATCHES IT.**
   A `seedSubmode = "bus"` default in a config group is the same value decided in
   two places; `check_hardcoding.py` category 6 refused it within a minute of it
   being written (§9.164).
5. **A CHECK A COMMENT CAN SATISFY IS NOT A CHECK.** A new test asserting that a
   `break` was gone passed against the comment explaining that the `break` used to
   be there. Strip comment lines first (§9.164, §9.160).
6. **AN ISSUE CAN WAIT FOR A RUN THAT HAS ALREADY HAPPENED.** Sixteen carried
   `awaiting-run`; fourteen were takeable from an arm that had finished. **Sweep
   the ledger after every landed arm, before designing the next one** (§9.163).
7. **A COVERAGE PERCENTAGE CANNOT BOUND A BOARDINGS COUNT.** Heavy and light rail
   are boardings per weekday; motorbike and truck are locked carves. **Both
   refusals are in the reader — do not remove them** (§9.163).
8. **A LINK ID IS NOT A ROAD.** MATSim re-issues link ids on every network
   rebuild; the count-station map measured the wrong roads for 25 days with every
   gate green. Check 7b enforces it for that one (§9.163).
9. **A HOOK'S ARGUMENTS DECIDE WHAT CAN BE PRICED THERE.** `getInVehicleCost` is
   handed no distance and no stop identity. Read the signature before designing
   the mechanism (§9.162) — it is why #175's prices are charged in scoring off
   `TransitDriverStartsEvent`, which does carry the route.
10. **Do not compare across a family boundary**, however tempting the story.
    `F33` opened at `20260910T203622` (§3.5, §9.164). **A run is a result only if
    `_run.json` says `ran_to_last_iteration`**; a stopped arm is a citable reading
    at its `reached_iteration` and nowhere past it (§9.143).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Any multi-hour run needs a new stated-cost approval,
  priced on the landed arm's `median_iteration_s` of 244.05 s and on a probe of
  whatever bytecode it will run. **Price it on F33's own bytecode**, which no arm
  has executed.
- **25 % runs only** (user directive, 1 September 2026) — for ARMS. A structural
  smoke probe whose whole output is a yes or a no may run at 1 %, says so in its
  overlay, and may not be read for any share, count or fit (§9.159).
- **One arm at a time**; never recompile `.tools/classes` under one —
  `bootstrap_toolchain.py` refuses, with `--force-compile` as the deliberate
  override.
- **A launch with no automatic stop of either kind is refused** before the JVM
  starts, and since §9.164 a gate interval declared beside a disabled monitor
  does not count as a stop.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement**
  (GOAL requirement 10), with the third state (`decision-needed` /
  `awaiting-implementation` + `AWAITING-DECISION:`) reported and never blocking.
  **Declare `answers_issues` on a new overlay** — a scraped lane cannot tell a
  claim from a mention, and every probe this session was scraped.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — these
  three stay FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder`.
- **Nothing may be tuned on the landed arm** until the separation in §1.1 is
  designed — §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
