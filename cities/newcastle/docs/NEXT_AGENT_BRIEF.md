# Brief for the next agent

**Written:** 7 September 2026, thirty-second session · **Open family:** `F30-an-escort-is-priced-as-an-escort` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/rule-on-the-five-blocking-defects`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**The five defects that had blocked every launch are closed** (§9.151,
#147–#151), so the issue gate is green for the first time since it was
introduced. **F30's first arm ran and was stopped at iteration 23** (§9.153) —
not on a fault, but on its own cost: 376 s an iteration against the 260 s its
~22 h approval was priced on. Along the way the toolchain gate was caught green
on a checkout that could not launch, and now refuses (§9.152). **The lane is the
cost question, then the arm.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle, no arm running.** F30's arm is closed out: `aborted_20260907T150816_300it_25pct`, `completion` `stopped_by_operator`, `reached_iteration` **23**. | `python src/run/session_gate.py --digest` (MACHINE line) · `results/raw/aborted_20260907T150816_300it_25pct/_run.json` |
| **The last GATE reading is still F28's at iteration 100** (§9.149). The board's scoreboard block shows F30 at it.20 — exploration, not a gate, and citable only at that iteration. | `python src/analyse/report_mode_ridership.py --run aborted_20260907T030352_300it_25pct --it 100` |
| **The package on disk is the F29 demand with the F30 run stack.** `check_package.py` ALL CHECKS PASSED this session. | `python tests/check_package.py` (~10 min) |
| **The session gate passed 17/17**, toolchain included — `.tools/` is bootstrapped AND the signals run stack is built (201 jars). | `python src/run/session_gate.py` |
| **The issue gate is GREEN**: #147–#151 closed, every remaining open issue carries `awaiting-run`. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry **477** fields, **512** manifest files, `F30-an-escort-is-priced-as-an-escort` newest in the ledger. | `python src/analyse/build_status_board.py --check` |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **No run approval stands.** Every approval is SPENT, the F30 arm's included. **25 % runs only.** | assume none; ask |

## §1 The lane

**Explain 376 s against 260 s, then relaunch F30's arm and read it at 100.**

F30's arm was healthy — iteration 0 passed every control (car departures 232,972
against F28's 231,607, stuck 3,786 against 3,145; 8,167 declared passengers
paired on 7,771 detours, 0 unroutable; 291 unpaired ride legs all restored;
8,549 drivers waiting for a household car) — and it was stopped only because
`_run.json` read `median_iteration_s` **376.42** against F28's **260**, which
puts 300 iterations near **31 h** against the ~22 h the approval was priced on.
**The 45 % is not diagnosed** (#66). Three candidates, none measured: machine
contention (observed while the arm ran, gone by the time it was stopped), the
thread settings this launch resolved, the freshly built signals run stack.
**A short timing probe on F28's own overlay on an idle machine settles it
cheaply, and it should come before any horizon is quoted again.**

Then: `python run.py --run-config f29_gate_25pct --detach`, verify per #70 that
`matsim.log` enters iterations, and read at the gate, in order:

1. **Iteration 0's `legHistogram`** against the F30 numbers above (§9.153).
2. **Placement** (§9.149): declared bound trips ridden against F28's 0.560, the
   walked-bound median against 1.08 km, the shared pass's
   `bound_mean_straight_km` against the HTS passenger 9.3–9.8 km. Ride against
   −42.8 %, read TOGETHER with bike (+157 %), bus (+65 %) and taxi (+161 %).
3. **Car must STAY inside** (+6.6 % at F28); walk −11.9 %, motorbike +16.1 %.
4. **The counts on their corrected basis** (§9.150): `heavy_vehicle_share`
   0.0652 → 0.1120 and the modelled side now sums car, motorbike and taxi.
   **#82's −91.8 % is not the figure to expect.**
5. Controls: `householdCar: N waited`; pair rate near 0.9965; 0 ride legs
   without a declared driver. The escort draw order changed (§9.151), so
   per-household proposals differ from F28's; the aggregates should not.

**Decisions the user must take:** a fresh stated-cost approval priced on the
newest median, and whether the timing probe comes first; whether a fifth binder
pass is needed once an arm reports the bound-trip lengths; the Task Scheduler
log (#66); the S2 tram signal priority. **Left deliberately undone** by §9.151,
each worth an issue if wanted: the 11 road classes taking the footway width
fallback have no declared width of their own (830 edges); `params/C1_*` and
`C5_calibration.json` carry no manifest `source` because they have no raw-data
ancestry; the 15 GTFS records carry no retrieval date at source. The fourth
assessment's demand findings (17:34,
[docs/reports/README.md](../../../docs/reports/README.md)) are root causes for
modes the gate keeps failing and are worth issues before an arm measures around
them.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A gate can be green on a checkout that cannot run** (§9.152). `verify()`
   checks the components RECORDED in `toolchain.json`; a run stack `--run-stack`
   never resolved is never recorded, so the loop could not report it. Cost: one
   refused launch. **Fixed — but ask of any check: what can it not see?**
2. **A stated cost is a boundary, not an estimate** (§9.153). 260 s came from
   F28's own stopwatch and still missed by 45 %. **Price the next arm on the
   newest arm's median and re-measure before quoting a horizon.**
3. **Fixing one half of a vocabulary leaves the other half silently wrong**
   (§9.151). `Serve passenger` → HX everywhere put HX in the purpose share while
   `C.vot.by_purpose` still said NHB, so the weight matched no key, was dropped,
   the rest renormalised, and the value of time rose 16.96 → 17.317 with nothing
   declaring it. **After a rename, grep for the old key.**
4. **A defect can be real and numerically nil** (§9.151). The purpose map had
   disagreed since §9.15; both names carried 15.2, so 140 of 141 files came back
   byte-identical. **State what a fix MEASURED, not what the issue predicted.**
5. **A verification script can be wrong in the dangerous direction.** A checker
   that grepped `matsim.log` for `Exception` flagged a HEALTHY arm as dead on
   Guice's benign one-off "Unsupported class file major version 69" warning
   (its ASM cannot read Java 25 bytecode for line numbers; every arm logs it).
   **Key liveness on the process, not on any stack trace in a log.**
6. **`qsim.vehicleBehavior` is GLOBAL** (§9.148). `wait` strands walk and taxi:
   55,862 car agents stuck at iteration 0, an arm wasted.
7. **Insert vehicles BEFORE creating the agent** (§9.148). MATSim 26 builds the
   agent from a copy of the plan elements.
8. **A binder change can be inert** (§9.149), and so can a builder change: a fix
   in `src/build` reaches nothing until the artefact is rebuilt.
9. **A sampling rule can decide the demand** (§9.149). The 0.05 hash bucket cut
   every shared passenger's driver supply to 5 %.
10. **`--set` is the scoring-parameter override; `--config-set` is the registry
    override** (§9.147).

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval is
  **SPENT**, the F30 arm's included. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep); the shared-ride bucket is that
  fraction since §9.149.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — `src/run/issue_gate.py`, **GREEN at handoff**.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **Ensure iterations have no inefficiencies and take as little time as
  possible** (user directive, 6 Sep) — §9.147 is the record and §9.153 is the
  open question: 376 s against 260 s, undiagnosed.
- **Fix the defects according to the report** (user directive, 7 Sep) — §9.150
  and §9.151; **SPENT**: all 34 are closed.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
