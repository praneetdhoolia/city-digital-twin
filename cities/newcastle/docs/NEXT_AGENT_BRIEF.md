# Brief for the next agent

**Written:** 9 September 2026, thirty-ninth session · **Open family:** `F32-crowding-reaches-scoring` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/the-raptor-learns-the-submode`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**THE MACHINE IS IDLE AND THE PROJECT HAS ITS FIRST RESULT.**
`20260909T015217_300it_25pct` closed `ran_to_last_iteration` at iteration 300 —
the first run since F4 on 21 August to execute the horizon it declared.

The session's finding, in one sentence: **the twin relaxes, and relaxing makes
the fit worse** — 0 of 12 modes inside 10 % against 1 of 12 at the gate that
preceded it, because when innovation stops every agent settles onto a best plan
that was always more car-heavy than the behaviour the search was sampling.

## §0 Verify first - facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE MACHINE IS IDLE.** No arm is running and **no approval stands** — the 32 h was spent on the landed arm. Any multi-hour run needs a new stated-cost approval. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **THE NEWEST CITABLE READING IS A RESULT**, `20260909T015217_300it_25pct` at iteration **300**: 0 of 12 inside 10 %, 8 past the stop bar. Its `_fit.json` is the first with `is_a_result: true`. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` (`--trend` for the direction) |
| **IT RELAXED**: window it.250–300, max drift **0.261 pp** against a 0.5 pp tolerance; the cutoff at 240 snapped car **+2.211 pp**. | `python -c "import json;d=json.load(open('results/raw/20260909T015217_300it_25pct/_summary.json'));print(d['relaxation'])"` |
| **THE DEPLOYED BYTECODE CHANGED and no family opened.** `.tools/classes` now carries `citysim.RaptorModeCostCalculator` at `absent`. **The next launch opens a family whatever it carries.** | `ls .tools/classes/citysim/ \| grep -i raptor` · `python -c "import json;print(list(json.load(open('cities/newcastle/docs/run_families.json'))['families'])[-1])"` |
| The issue gate reads **22 open, 16 awaiting a run with a stated measurement, 6 awaiting a decision, 0 blocking**. The six are #49, #50, #155, #167, #169 and #172 (filed this session). | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR. | `gh pr list --state open` |
| Registry **497** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke). | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| The store, now carrying the landed arm. | `python src/run/results_store.py --report` |

Then: `python src/run/session_gate.py`. The toolchain step compiles
`.tools/classes` and runs only while the machine is idle.

## §1 The lane

**Separate the three candidate causes of the convergence penalty, then run one arm.**

1. **THE OPEN QUESTION IS WHY CONVERGENCE MAKES THE FIT WORSE** (§9.162, #163).
   Every gate reading this project has ever taken was of a model still
   searching, and the snap measures how much that flattered it: at iteration
   240 the sampled behaviour and the agents' own best plans differed by
   **2.2 pp of car**. Three candidate causes, and this arm separates none of
   them:
   - **the scoring function** — car's utility is too high, or every
     alternative's too low;
   - **the choice set** — pt reaches only **25.78 %** of agents at iteration
     300 (car 77.55, walk 63.95, taxi 54.62, bike 29.03, ride 20.05), so most
     agents have no pt plan to settle onto;
   - **the routers** — 60.5 % of pt routing requests still come back as a walk
     (§9.158), and the submode-picking router had no constant until this
     session.
   **Design the separation before spending an arm on it.** No parameter may be
   tuned on the landed reading until it is designed.
2. **THE RAPTOR CONTROL IS BUILT, DEPLOYED AND NEVER RUN** (§9.162, #49).
   `citysim.RaptorModeCostCalculator` adds the boarded submode's own
   `scoring.modeParams` constant to SwissRailRaptor's in-vehicle cost, once per
   boarded leg, behind `C.raptor.mode_cost_representation` = `absent`. It
   declares **no value of its own**. Running `mode_constant` against its
   `absent` control **opens a family** and needs a stated-cost approval. Note
   the ceiling on what it can do: three quarters of agents hold no pt plan.
3. **#169 — the ceiling watcher is BUILT and UNPROVEN, and the machine is now
   idle** (§9.161). What remains is the 1 % smoke probe with a deliberately
   tiny `RUN.gate.wall_ceiling_h`; the observable is that the run stops inside
   it and closes out `stopped_at_ceiling`. Cheap, and it clears a
   `decision-needed`.
4. **#167 — the fix is ONE ATTRIBUTE and it needs a rebuild** (§9.161). Emit
   `routingMode` per leg in `build_matsim_plans.py` — a no-op at
   `access_egress_type = none` — and rebuild the demand and the 30 run-input
   sets in the SAME change, or the committed builder can no longer reproduce
   the package. Then re-run `intermodal_access_probe_1pct`.
5. **The ASC contraction test stays HELD** (§9.160). Of its four modes only
   **bike** sits on an alternative the mode-choice operator can switch to.

**Decisions the user must take:** what the next arm carries and at what stated
cost (no approval stands); the three product calls behind #49, #50 and #155;
whether the **real Newcastle corridor operates transit signal priority**
(`A.lightrail.tsp_enabled` is `source: assumed`, requirement 6 says derive it,
and it is settled on evidence about the corridor, never on light rail's
−57.3 %); #66's Task Scheduler log.

## §2 Traps - newest first, each with what it cost

1. **A GENERATED BLOCK CAN ASSERT SOMETHING NO CHECK READS.** The board's
   scoreboard header said *"Not a result"* of every reading it ever wrote —
   correct for nineteen days, false the moment an arm reached its horizon.
   `check_doc_currency.py` pins PROSE against artefacts and does not look
   inside a generated block, so the first result in the project made the
   board's own front block wrong with every gate green (§9.162).
2. **RELAXED IS NOT CONVERGED.** `relaxed: true` says mode share stops moving
   after innovation is switched off. It says nothing about whether the search
   had found its answer — the cutoff snap does, and it read 2.2 pp of car
   (§9.162).
3. **A MID-RUN PACE READING IS NOT THE RUN'S PACE.** The median went to
   301.5 s against a band of [217, 253] between iterations 120 and 190 and
   closed at **244.05 s**, inside it. One false alarm this session (§9.162).
4. **A HOOK'S ARGUMENTS DECIDE WHAT CAN BE PRICED THERE.** The raptor cost
   change was designed to carry a constant, a fare and a distance term;
   `getInVehicleCost` is handed no distance and no stop identity, and Opal is
   banded in km, so two of the three could not be built. **Read the signature
   before designing the mechanism** (§9.162).
5. **A CHECK CAN BE SATISFIED BY PROSE DESCRIBING THE CHECK.** The issue gate
   read *"0 blocking"* while three issues opened *"This issue BLOCKS the
   launcher"*: its regex matched a token inside a **code span** (§9.160).
6. **A FIX VERIFIED AGAINST THE HALF OF THE CODE IT CHANGED IS NOT VERIFIED**
   (§9.160).
7. **PROSE CANNOT READ A NEGATION.** Writing "#167 is deliberately NOT in this
   lane" put #167 back in the lane. Declare `answers_issues` (§9.160).
8. **A PRICE IS FOR A STACK** — probe the build before spending an approval on
   it (§9.160, §9.153).
9. **Do not compare across a family boundary**, however tempting the story.
   `F32` opened at `20260909T011135` (§3.5, §9.160).
10. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** A
    stopped arm is a citable reading at its `reached_iteration` and nowhere
    past it (§9.143).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** The 32 h was spent on `20260909T015217_300it_25pct`
  and that arm has landed. Any further multi-hour run needs a new stated-cost
  approval, priced on **this** arm's `median_iteration_s` of 244.05 s and on a
  probe of whatever bytecode it will run.
- **25 % runs only** (user directive, 1 September 2026) — for ARMS. A
  structural smoke probe whose whole output is a yes or a no may run at 1 %,
  says so in its overlay, and may not be read for any share, count or fit
  (§9.159).
- **One arm at a time**; never recompile `.tools/classes` under one —
  `bootstrap_toolchain.py` refuses, with `--force-compile` as the deliberate
  override.
- **No launch while an open issue in the RUN'S LANE lacks a stated
  measurement** (GOAL requirement 10), with the third state from §9.160
  (`decision-needed` / `awaiting-implementation` + `AWAITING-DECISION:`)
  reported at every gate and never blocking.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** —
  these three stay FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder`
  in the registry and are out of the movable set for that reason.
- **Nothing may be tuned on the landed arm** until the separation in §1.1 is
  designed — §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
