# Brief for the next agent

**Written:** 7 September 2026, thirty-second session · **Open family:** `F30-an-escort-is-priced-as-an-escort` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/rule-on-the-five-blocking-defects`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

No arm ran. **The five defects that were blocking every launch are ruled on and
closed** (§9.151, issues #147–#151): the issue gate is green, the toolchain is
bootstrapped, and **the lane is now the F29/F30 arm itself**. Four of the five
moved no run value; the fifth — the escort listener's seeded draw, which was
made in `HashMap` order and therefore was not stable across sample fractions —
does, and **family `F30` opens on it alone**. Fixing the duplicated purpose map
(#147) exposed a second half nobody had asked about: `C.vot.by_purpose` was
still keyed on the old vocabulary, so the HX weight was dropped from the
value-of-time average and the collapse moved **16.96 → 17.317 AUD/h** against a
declared 16.96. Re-keyed, and **140 of the 141 files under `scenarios/matsim/`
came back byte-identical**.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **An arm RUNS**: `20260907T150816_300it_25pct`, F30's first, launched 15:08 7 Sep (25 %, 300 it, 16 threads, 40 g) at ~375 s an iteration; its iteration-100 gate is due about 01:30 8 Sep. The newest CITABLE reading is still F28's gate (`aborted_20260907T030352_300it_25pct`); the board's blocks now read the running arm every ten iterations. | `python src/run/session_gate.py --digest` (MACHINE line) · `results/raw/20260907T150816_300it_25pct/_progress.json` |
| **The package on disk is the F29 demand with the F30 run stack.** `check_package.py` ALL CHECKS PASSED this session, after the run inputs were re-assembled twice and the manifest regenerated. | `python tests/check_package.py` (~10 min) |
| **The session gate: 16 pass, board blocks regenerated 17:50, toolchain SKIPPED under the running arm.** `.tools/` is bootstrapped in this checkout and the Java run stack compiled with both changes before the launch. | `python src/run/session_gate.py` |
| **The issue gate is GREEN**: #147–#151 are closed, and every remaining open issue carries `awaiting-run`. **This is what was blocking the launch.** | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry **477** fields, **512** manifest files, `F30-an-escort-is-priced-as-an-escort` newest in the ledger. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT, the F30 arm's included. **25 % runs only.** | assume none; ask |

## §1 The lane

**Read the running `F30` arm at its iteration-100 gate.** It was launched at
15:08 with `python run.py --run-config f29_gate_25pct --detach` and entered
iterations; at ~375 s an iteration (F28 ran 260) the gate is due about 01:30 on
8 Sep. The 17:34 assessment ([docs/reports/README.md](../../../docs/reports/README.md))
measured the demand itself — evening departures 3× observed, the PT day
inverted, income age-flat, commute flows too inter-LGA — and those are the
root causes to take after the gate, not constants. Read, in order:

1. **Iteration 0's `legHistogram`** — car departures near F28's 231,607 and
   stuck near 3,145 say the car-only handler still does its one job; tens of
   thousands stuck means stop (§9.148).
2. **Placement** (§9.149): the share of declared bound trips ridden against
   F28's 0.560 and the walked-bound median against 1.08 km; the shared pass's
   `bound_mean_straight_km` against the HTS passenger 9.3–9.8 km. Ride against
   −42.8 %, read TOGETHER with bike (+157 %), bus (+65 %) and taxi (+161 %),
   whose long car-less trips this placement should draw down.
3. **Car must STAY inside** (+6.6 % at F28); walk against −11.9 %, motorbike
   +16.1 %.
4. **The counts, on their corrected basis** (§9.150). Both sides changed:
   `heavy_vehicle_share` 0.0652 → 0.1120 and the modelled side now sums car,
   motorbike and taxi. **#82's −91.8 % is not the figure to expect.**
5. Controls: `householdCar: N waited` near 15,582; pair rate near 0.9965; 0
   ride legs without a declared driver. The escort listener's draw order changed
   (§9.151), so its per-household proposals will differ from F28's; the
   aggregate proposal and decohere counts should not.

**Decisions the user must take:** a stated-cost approval for the arm; whether a
fifth binder pass is needed once F30 reports the bound-trip lengths; the Task
Scheduler log (#66); the S2 tram signal priority. **Left deliberately undone**
by §9.151, each worth an issue if it is wanted: the 11 road classes that take
the footway width fallback have no declared width of their own (830 edges);
`params/C1_*` and `C5_calibration.json` carry no manifest `source` because they
have no raw-data ancestry; the 15 GTFS feed records carry no retrieval date at
source and cannot honestly acquire one now.

## §2 Traps — newest first, at most ten

1. **Fixing one half of a vocabulary leaves the other half silently wrong**
   (§9.151). Making `Serve passenger` → HX everywhere put HX in the purpose
   share while `C.vot.by_purpose` still said NHB — so the weight matched no key,
   was dropped, the rest renormalised, and the value of time rose 16.96 →
   17.317 with nothing declaring it. **After a rename, grep for the old key.**
2. **A defect can be real and numerically nil** (§9.151). The purpose map had
   disagreed since §9.15; both names carried the same 15.2, so the configs came
   back byte-identical. State what a fix MEASURED, not what the issue predicted.
3. **A check can be green on a rule it cannot test** (§9.150). Three were.
   **Widen a check before trusting its zero.**
4. **`--stop` used to end every arm on the machine** and the harness overwrote
   the operator's cause (§9.150). Fixed, but untested against a live arm.
5. **`qsim.vehicleBehavior` is GLOBAL** (§9.148). `wait` strands walk and taxi:
   55,862 car agents stuck at iteration 0, an arm wasted.
6. **Insert vehicles BEFORE creating the agent** (§9.148). MATSim 26 builds the
   agent from a copy of the plan elements.
7. **A binder change can be inert** (§9.149), and so can a builder change: a fix
   in `src/build` reaches nothing until the artefact is rebuilt.
8. **A sampling rule can decide the demand** (§9.149). The 0.05 hash bucket cut
   every shared passenger's driver supply to 5 %.
9. **`--set` is the scoring-parameter override; `--config-set` is the registry
   override** (§9.147).
10. **A dry run that resolves is not a launch that runs** — though since §9.151
    the telemetry refusal at least fires in the dry run too.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to date
  is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep); the shared-ride bucket is that
  fraction since §9.149.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py`, **GREEN at handoff** for the first
  time since it was introduced.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **Ensure iterations have no inefficiencies and take as little time as
  possible** (user directive, 6 Sep) — §9.147 is the record; the F28 arm's
  260 s median is the measurement, and §9.151 declined to put atomics on the
  event path for that reason.
- **Fix the defects according to the report** (user directive, 7 Sep) — §9.150
  and §9.151 are the record; **SPENT**: all 34 are now closed.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
