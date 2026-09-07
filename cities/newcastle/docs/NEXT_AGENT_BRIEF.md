# Brief for the next agent

**Written:** 7 September 2026, thirty-third session · **Open family:** `F30-an-escort-is-priced-as-an-escort` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/report-recommendations-and-iteration-speed`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**The iteration was decomposed to the method for the first time, and a third of
it was ours** (§9.154). Per-link tables took a plain probe iteration from
**310 to 205.5 s** and startup from **13m47s to 7m00s**, proved identical to the
formula over 3,266,754 comparisons. **The 2-minute iteration the directive asked
for is not reached** — ~190 s unprofiled against 120 — and what remains is
MATSim's own. Separately, `RUN.travel_time.analysed_modes` had been inert since
it was declared (#154), and 31 more MATSim defaults decide this model undeclared
(#155). **The lane is the arm: it is priced, gated and unlaunched.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle, no arm running.** Two four-iteration PROFILING probes ran and completed: `20260907T182742_4it_25pct` and `20260907T192715_4it_25pct`. Their clocks are citable; nothing else about them is. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The last GATE reading is still F28's at iteration 100** (§9.149); the board's scoreboard block shows F30 at it.20 — exploration, not a gate. No arm has run since. | `python src/analyse/report_mode_ridership.py --run aborted_20260907T030352_300it_25pct --it 100` |
| **The next arm opens a NEW family**: `RUN.travel_time.filter_modes` = true moves results (§9.154, #154). The ledger's newest key is still F30 because nothing has launched under it. | `python src/analyse/build_status_board.py --check` · `cities/newcastle/docs/run_families.json` |
| **The package on disk is unchanged** — no data artefact moved this session. | `python tests/check_package.py` (~10 min) |
| **The session gate passed 18/18**, one check newer than last session (`matsim defaults`). | `python src/run/session_gate.py` |
| **The issue gate is GREEN**: 17 open, all `awaiting-run`, including the two opened this session. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry **480** fields, **512** manifest files. | `python src/registry/render_docs.py --check` |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **No run approval stands.** Every approval is SPENT. **25 % runs only.** | assume none; ask |

## §1 The lane

**Price the arm, get the approval, launch it, read it at 100.**

The cost is no longer quoted from a document. `python src/analyse/arm_cost.py
--run-config f29_gate_25pct` reads the newest median at the same sample
fraction, adds that run's own measured setup and prints the spread behind it;
`run.py` prints the same line before every launch. A PROFILED run is excluded
from pricing — the recorder is ~8 % of its clock — so today it prices on F30's
stopped arm at 376.4 s. **The next arm should beat that**: §9.154 cut a plain
probe iteration by 34 % on a like-for-like comparison, so read the arm's own
first iterations and re-price before quoting a horizon.

Then: `python run.py --run-config f29_gate_25pct --detach`, verify per #70 that
`matsim.log` enters iterations, and read at the gate, in order:

1. **Iteration 0's `legHistogram`** against F30's iteration-0 controls (§9.153):
   car departures 232,972, stuck 3,786, 8,167 declared passengers paired on
   7,771 detours, 291 unpaired ride legs restored, 8,549 drivers waiting.
2. **Placement** (§9.149): declared bound trips ridden against F28's 0.560, the
   walked-bound median against 1.08 km. Ride against −42.8 %, read TOGETHER with
   bike (+157 %), bus (+65 %) and taxi (+161 %).
3. **Car must STAY inside** (+6.6 % at F28); walk −11.9 %, motorbike +16.1 %.
   **Expect movement from #154**: every mode's router has been reading link
   travel times a pedestrian helped set, and that is now car-only.
4. **The counts on their corrected basis** (§9.150). **#82's −91.8 % is not the
   figure to expect.**
5. Controls: `householdCar: N waited`; pair rate near 0.9965; 0 ride legs
   without a declared driver.

**Decisions the user must take:** a fresh stated-cost approval; whether the 31
unreviewed MATSim defaults (#155) are worked down before the arm or after it;
whether a fifth binder pass is needed; the Task Scheduler log (#66); the S2 tram
signal priority. **Left deliberately undone** by §9.154, each worth doing when
it is the lane: `NetworkDirectWalkPtRouter.calcRoute` is 8.2 % of a plain
iteration and routes a full network walk beside every transit request — a
provably choice-preserving shortcut needs the maximum walk speed-up factor,
which the downhill Tobler term makes greater than one; the assessment's
network-stamping and day-table rewrites are NOT done and the reason is written
in §9.154; the 17:34 assessment's demand findings (evening departures, the
inverted PT day, age-flat income, inter-LGA commute flows) are root causes for
modes the gate keeps failing and are still without issues.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A performance claim in a report may be reasoned, not measured** (§9.154).
   Three of the 17:34 assessment's ranked IO items measure at 0.1 s, 1.5 s and
   1.8 s respectively. **Measure the thing before optimising it**; two of the
   three were implemented and reverted this session.
2. **The profile is dominated by what happens before iteration 0.** MATSim
   routes every agent once in `PersonPrepareForSim`, which was 61.6 % of the
   first recording. **Always pass `--iterations FIRST:LAST` to
   `profile_run.py`** for anything about an arm.
3. **A profiled run's clock prices nothing.** The recorder costs ~8 %.
   `arm_cost.py` excludes profiled runs; do not quote one as an arm's pace.
4. **Do not judge a code change by diffing two runs** (§9.142): three runs of one
   build disagree by ~300 of 5.6 M iteration-0 events. Prove it where it can be
   proved — `citysim.GradientTableProbe` compares a table against its formula
   over the real network, which is what settled §9.154.
5. **A declared value can be voided by an undeclared one** (§9.154, #154).
   `analysed_modes` was declared, swept, rendered and PROVEN to reach the config,
   and meant nothing because `filterModes` defaults false. **Ask of any declared
   field: what else has to be true for it to bite?**
   `src/registry/check_matsim_defaults.py` is that question, asked mechanically.
6. **A gate can be green on a checkout that cannot run** (§9.152). Ask of any
   check: what can it not see?
7. **A stated cost is a boundary, not an estimate** (§9.153).
8. **`qsim.vehicleBehavior` is GLOBAL** (§9.148): `wait` strands walk and taxi.
9. **Insert vehicles BEFORE creating the agent** (§9.148).
10. **`--set` is the scoring-parameter override; `--config-set` is the registry
    override** (§9.147).

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval is
  **SPENT**. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep).
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — `src/run/issue_gate.py`, **GREEN at handoff**.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **Ensure iterations have no inefficiencies and take as little time as
  possible** (user directive, 6 Sep; restated 7 Sep as "under 2 minutes") —
  §9.154 is the newest work and the target is NOT met: ~190 s against 120.
- **Codify manual operations** (user directive, 7 Sep) — §9.154 added
  `arm_cost.py`, the launcher's cost line, `profile_run.py`,
  `dump_matsim_params.py` and `check_matsim_defaults.py`; the gate is 18 checks.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
