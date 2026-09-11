# Brief for the next agent

**Written:** 11 September 2026, forty-second session · **Open family:** `F33-the-passenger-is-put-on-ride` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/arm-0-died-on-heap`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**F33'S FIRST ARM DIED AT ITERATION 98 ON A HEAP THE OVERLAY FAILED TO SET, AND
THE FAMILY STILL HAS NO READING.** `aborted_20260910T222830_300it_25pct` threw
`OutOfMemoryError: Java heap space` after 97 completed iterations and 6.5 h. Its
overlay copied the landed arm's horizon and gate departure and not its 40 GB
heap, so it inherited the registry's 14 GB while the landed arm had peaked at
36.2 GB. There is no warm-start point (`write_plans_interval` = 100) and the 6.5 h
is lost. The overlay now states 40g; **no approval stands** — the 26 h one was
spent on the arm that died.

Everything the forty-first session closed out stands (§9.164): every open issue
is closed, awaiting a paired arm, or awaiting one stated decision. The operator
has since **ordered the five controls** (#172) and chosen a **baseline arm with no
control on** as arm 0 — that arm is what died, and it is what the next session
relaunches.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE MACHINE IS IDLE and NO APPROVAL STANDS.** The 26 h approval of 10 September was spent on `aborted_20260910T222830_300it_25pct`, which died at iteration 98. Any relaunch needs a fresh stated-cost approval. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **`F33-the-passenger-is-put-on-ride` IS OPEN AND HAS NO READING.** Its one arm is `failed` (OOM at it.98) and nothing it wrote is citable for any mode; its pricing probe `20260910T215129_4it_25pct` is citable for its clock alone (225.0 s recurring, 19.0 h quoted). | `python -c "import json;print(list(json.load(open('cities/newcastle/docs/run_families.json'))['families'])[-1])"` |
| **THE NEWEST CITABLE READING IS STILL `20260909T015217_300it_25pct` at iteration 300**, and it belongs to the family BEFORE the open one: 0 of 12 inside 10 %, 8 past the stop bar. None of this session's four probes may be read for any share, count or fit. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| **THE DEAD ARM'S RECORD SAYS WHY**: `failed`, `OutOfMemoryError: Java heap space`, chain at log line 40265. `reconcile_stale` now reads the log before blaming a dead harness. | `python -c "import json;m=json.load(open('results/raw/aborted_20260910T222830_300it_25pct/_meta.json'));print(m['status'],m['cause'])"` |
| **THE OVERLAY IS CORRECTED**: `f33_baseline_25pct.json` states `RUN.machine.xmx` = 40g. | `python run.py --run-config f33_baseline_25pct --dry-run` (read the `RUN.machine.xmx` line) |
| **The Task Scheduler operational log is ENABLED** for the first time (#66). | `wevtutil gl Microsoft-Windows-TaskScheduler/Operational` reads `enabled: true` |
| The issue ledger after #131, #155 and #169 closed on evidence. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **514** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke), undeclared MATSim defaults **0**, unit tests **324**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python src/registry/check_matsim_defaults.py` · `python -m pytest tests/unit -q` |
| `check_package.py` passed on the rebuilt demand (10 September). | `python tests/check_package.py` (LOCAL) |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle.

## §1 The lane

**Relaunch arm 0 — the F33 baseline with no control on — on the corrected
overlay, with a fresh approval. The order after it is already decided.**

0. **ARM 0 IS DECIDED, PRICED, CORRECTED AND UNRUN** (§9.165, #172). The operator
   chose it on 10 September: `f33_baseline_25pct.json`, no control on, the
   control half of all five later pairs, and the measurement of the demand fix
   already spent (#86, #48, #145). It is priced at **19.0 h** on F33's own
   bytecode (225.0 s recurring), observed spread 20.5–24.7 h; the arm that died
   projected 21.1 h before it ran out of heap. **Ask for the approval, then
   launch it; do not redesign it.**

1. **THE ORDER OF THE FIVE CONTROLS IS DECIDED** (#172, 10 September): scoring →
   choice set → service quality → routers → submodes. Each is one paired arm
   against arm 0.
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

**Decisions the user must take:** a stated-cost approval for arm 0 (no approval
stands); whether any of the nine newly declared MATSim
defaults is worth spending an arm on; the product calls behind #49 and #50;
whether the real Newcastle corridor operates transit signal priority
(`A.lightrail.tsp_enabled` is `source: assumed`); The Task Scheduler operational log IS enabled (#66); the next stall is
attributable for the first time.

## §2 Traps — newest first, each with what it cost

1. **AN OVERLAY WRITTEN AGAINST ANOTHER OVERLAY COPIES WHAT ITS AUTHOR WAS
   LOOKING AT.** `f33_baseline_25pct.json` took the landed arm's horizon, gate
   departure and justification shape and not its `RUN.machine.xmx` = 40g. The
   arm ran 6.5 h on 14 GB and died at iteration 98 with no warm-start point. **A
   pricing probe prices time and cannot price heap**, which grows with plan
   memory over the first hundred iterations (§9.165).
2. **A RECORD IS WRITTEN BY WHOEVER IS LEFT STANDING.** The harness that launched
   the arm had died with an earlier session, and `reconcile_stale` was going to
   headline *the harness is no longer running* over a JVM that died of heap. It
   now reads the log first (§9.165).
3. **A RECORDED DIAGNOSIS CAN BE HALF A DIAGNOSIS, AND THE HALF THAT IS RIGHT
   HIDES THE HALF THAT IS NOT.** §9.161 established, correctly and with
   measurement, that #167's failure was our plans declaring no `routingMode`. It
   was half the cause. The fix landed, the failure halved, and the run still died.
   **A cause that explains part of a count is not the cause** (§9.164).
4. **A GATE INTERVAL IS NOT A GATE.** `RUN.gate.interval_iterations` = 2 beside
   `RUN.monitor.enabled` = false produced no verdict, no gate line and no warning
   over a run that reached iteration 3, while the launch banner said the run had
   a modelling stop. The watcher now refuses to arm and the launch refusal reads
   all three fields (§9.164, #131).
5. **A BANNER THAT ROUNDS IS A BANNER THAT LIES.** The launch line printed
   `%.1f h`, so a 0.05 h ceiling was announced as 0.1 h; and a run stopped on cost
   announced itself as `STOPPED BY THE OPERATOR` while its own record said
   `stopped_at_ceiling` (§9.164).
6. **DECLARING A VALUE IN JAVA SHADOWS THE REGISTRY, AND THE CHECKER CATCHES IT.**
   A `seedSubmode = "bus"` default in a config group is the same value decided in
   two places; `check_hardcoding.py` category 6 refused it within a minute of it
   being written (§9.164).
7. **A CHECK A COMMENT CAN SATISFY IS NOT A CHECK.** A new test asserting that a
   `break` was gone passed against the comment explaining that the `break` used to
   be there. Strip comment lines first (§9.164, §9.160).
8. **AN ISSUE CAN WAIT FOR A RUN THAT HAS ALREADY HAPPENED.** Sixteen carried
   `awaiting-run`; fourteen were takeable from an arm that had finished. **Sweep
   the ledger after every landed arm, before designing the next one** (§9.163).
9. **A COVERAGE PERCENTAGE CANNOT BOUND A BOARDINGS COUNT.** Heavy and light rail
   are boardings per weekday; motorbike and truck are locked carves. **Both
   refusals are in the reader — do not remove them** (§9.163).
10. **A LINK ID IS NOT A ROAD.** MATSim re-issues link ids on every network
   rebuild; the count-station map measured the wrong roads for 25 days with every
   gate green. Check 7b enforces it for that one (§9.163).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** The 26 h approval of 10 September was SPENT on the arm
  that died. Arm 0 is priced on F33's own bytecode at 19.0 h (225.0 s recurring,
  `20260910T215129_4it_25pct`); quote the 20.5–24.7 h spread beside it and set
  `RUN.gate.wall_ceiling_h` to what is approved.
- **Never compare across a family boundary.** `F33` opened at `20260910T203622`
  (§3.5, §9.164). A run is a result only if `_run.json` says
  `ran_to_last_iteration`; a stopped arm is citable at its `reached_iteration`;
  a FAILED arm is citable for nothing (§9.143, §9.165).
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
