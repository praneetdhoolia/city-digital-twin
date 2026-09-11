# Brief for the next agent

**Written:** 11 September 2026, forty-third session · **Open family:** `F33-the-passenger-is-put-on-ride` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/project-report-and-fixes`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS THE RUN.** This session wrote the eighth report
([`reports/`](reports/README.md)), filed and groomed the issues it found, and
fixed everything fixable without a run (§9.166). What is left strictly needs
arm 0: F33 is open, has no reading, and its baseline overlay is corrected,
priced and refused-on-everything-that-killed-it. Ask for the approval, launch,
and read.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE MACHINE IS IDLE and NO APPROVAL STANDS.** The 26 h line on `f33_baseline_25pct.json` encodes an approval SPENT on the arm that died; a relaunch needs a fresh stated-cost approval. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **F33 IS OPEN AND HAS NO READING.** Its one arm is `failed`; its pricing probe `20260910T215129_4it_25pct` is citable for its clock alone (225.0 s recurring, 19.0 h quoted, spread 20.5–24.7 h). The controler was recompiled this session with nothing to be incomparable with. | `python -c "import json;print(list(json.load(open('cities/newcastle/docs/run_families.json'))['families'])[-1])"` |
| **THE NEWEST CITABLE READING IS `20260909T015217_300it_25pct` at 300**, family F32: 0 of 12 inside 10 %, 8 past the stop bar. On the legs-table basis the reader now uses, light rail reads 1,224 (−58.6 %) and heavy rail 20,932 (+220.6 %). | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| **THE DEAD ARM'S TRUE COST**: `wall_s` 75,388 (20.9 h), 13.1 h of it inside iteration 89 with the machine awake; §9.165's "6.5 h" is superseded by §14. | `python -c "import json;m=json.load(open('results/raw/aborted_20260910T222830_300it_25pct/_meta.json'));print(m['status'],m['wall_s'],m['cause'])"` |
| **THE LAUNCHER REFUSES**: a heap below 9.6 + 87 × fraction GiB, a run overlay that changes nothing the run reads, a launch with no automatic stop; and it **kills** a log silent for 1800 s. Dry-run the overlay and read the `heap:` line. | `python run.py --run-config f33_baseline_25pct --dry-run` |
| The Task Scheduler operational log is ENABLED and has its first reading (#66). | `wevtutil gl Microsoft-Windows-TaskScheduler/Operational` reads `enabled: true` |
| The issue ledger: 32 open, 0 blocking; 13 filed this session (#180–#192). | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **521** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke), undeclared MATSim defaults **0** (strict in CI), unit tests **349**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python src/registry/check_matsim_defaults.py --strict` · `python -m pytest tests/unit -q` |
| `check_package.py` passed on the rebuilt demand (10 September); the population was not rebuilt this session. | `python tests/check_package.py` (LOCAL) |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle.

## §1 The lane

**Relaunch arm 0 on a fresh approval, then the five pairs in the decided
order. Do not redesign it, and do not run a report before it reads.**

0. **ARM 0** (§9.165, §9.166, #172): `f33_baseline_25pct.json` — no control on,
   40 g, GC log on, `create_graphs` off, stall kill at 1800 s, 26 h ceiling
   line to be set to whatever is approved. Launch with `--detach` so the arm
   outlives the session; the watchers ride with the JVM. It measures the demand
   fix (#86, #48, #145, #30) and is the control half of all five pairs. Read at
   its gates: all twelve modes with coverage beside each; `modes_car_car`
   against the roster's wait count; the sub-1 km share against 11.17 %; the
   cutoff snap beside the level; and **`gc.log` against `_progress.json`** — the
   first stall with a collector's account (#66).
1. **THE FIVE PAIRS** (#172): scoring (`RUN.replanning.score_msa_representation`
   = `at_innovation_cutoff`) → choice set (`plan_selector_for_removal` =
   `SelectRandom`, now switching BOTH removal paths, #174) → service quality
   (#175) → routers (`C.raptor.mode_cost_representation` = `mode_constant`) →
   submodes (`RUN.mode_choice.pt_submode_alternatives`, #49). Coverage on both
   sides of every pair. Each opens a family; each needs its own approval.
2. **#167 IS A DIAGNOSIS** (§9.164): where inside MATSim's pre-sim pass the
   mixed-routing-mode trip is made. Until then a car trip carries no fixed cost.
3. **The ASC contraction test can now measure something** — the `C.asc.*`
   constants reach the run from the registry (§9.166). It stays HELD until arm
   0 has read; bike is the mode it can answer (24.32 pp of headroom).
4. **After arm 0's gate, the ninth report** — the skill's cadence rule is one
   report per reading. It will find the four consolidations (#180, #181, #182,
   #191) still open; that is by decision, not neglect.

**Decisions the user must take:** the approval for arm 0; the footpath network
(#183); the freight trains at the crossings (#184); whether a warm-completed
arm is a result (#192); the heavy-rail target's holdout sum (#189); the ride
engine's plan mutation (#187); the session for the consolidations.

## §2 Traps — newest first, each with what it cost

1. **A RULE IN A DESCRIPTION IS NOT A RULE.** `RUN.machine.xmx` said "must
   exceed 9.6 GiB + 87 GiB × fraction or the run dies" for six weeks and nothing
   read it; 20.9 h (§9.166). The launcher evaluates it now — declare a rule as
   fields, never as prose.
2. **AN OBSERVER IS NOT A STOP.** `RUN.monitor.stall_s` observed a 13.1 h stall
   and the digest reported it at 05:13; nothing killed it. Every boundary needs
   an owner that acts (`stopped_at_stall`, §9.166).
3. **A RECORDED OVERRIDE CAN EXECUTE NOTHING.** `C.asc.bus` in a run overlay
   was validated, recorded and read from the built C1 table instead; the ASC
   contraction test would have measured nothing (§9.166). The launcher now
   re-emits with each override at its registry value and refuses if nothing
   moves — use that test before spending an arm on any candidate.
4. **TWO READERS OF ONE RUN GIVE TWO NUMBERS.** Plans vs legs table: 1,260 vs
   1,224 light-rail boardings on one page. One source at every iteration now
   (§9.166); if you add a reader, make it read the table.
5. **A FUNCTION THAT CANNOT RUN PASSES EVERY GATE.** `build_matsim_network.py`
   unpacked four values from a two-tuple for seventeen days; 62 of 81 `src/`
   modules are imported by no test (#190).
6. **A PRIVATE RULE IN A LISTENER BYPASSES A DECLARED FIELD.** `trim()`'s
   worst-score removal beside `planSelectorForRemoval`; `param_config.reach()`
   cannot see it because the config text does change (§9.166, #174).
7. **AN OVERLAY WRITTEN AGAINST ANOTHER OVERLAY COPIES WHAT ITS AUTHOR WAS
   LOOKING AT** (§9.165): the heap. A pricing probe prices time, not heap.
8. **A REPORT PER SESSION REPEATS ITSELF.** Nine in eight days, 125 findings in
   consecutive chains, 76 of 105 recommendations taken and the goal count
   unmoved — between readings a report can add instruments and nothing else
   (§9.166). One per reading.
9. **A RECORDED DIAGNOSIS CAN BE HALF A DIAGNOSIS** (§9.164): #167's
   `routingMode` fix halved the failure and the run still died.
10. **A GATE INTERVAL IS NOT A GATE** (§9.164, #131): an interval beside a
    disabled monitor produced no verdict; the launcher refuses it now.

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** The 26 h approval of 10 September was SPENT on the
  arm that died. Arm 0 is priced on F33's own bytecode at 19.0 h (225.0 s
  recurring, `20260910T215129_4it_25pct`); quote the 20.5–24.7 h spread and set
  `RUN.gate.wall_ceiling_h` to what is approved.
- **Never compare across a family boundary.** F33 opened at `20260910T203622`
  (§9.164); its controler was recompiled at §9.166 with no reading to lose. A
  run is a result only if `_run.json` says `ran_to_last_iteration`; a stopped
  arm (gate, ceiling, stall, operator) is citable at its `reached_iteration`;
  a FAILED arm is citable for nothing (§9.143, §9.165).
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural
  smoke probe may run at 1 %, says so, and is read for nothing (§9.159).
- **One arm at a time**; never recompile `.tools/classes` or
  `.tools/classes-signals` under one — both paths refuse now (§9.166).
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
- **Java defect fixes may land while F33 has no reading; the consolidations
  (#180, #181, #182, #191) wait for the F33 pairs** (user decision, 11
  September 2026).
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`** (the ruleset requires a PR now); the session's ONE
  PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
