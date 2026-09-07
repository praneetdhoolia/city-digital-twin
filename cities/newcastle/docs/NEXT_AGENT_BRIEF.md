# Brief for the next agent

**Written:** 7 September 2026, thirty-first session · **Open family:** `F29-lifts-are-the-long-trips` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/assessment-and-defect-fixes`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

No arm ran. The repository was assessed whole and 29 of its 34 defects were
closed (§9.150; the report is [`docs/reports/`](../../../docs/reports/README.md)).
**None of the 34 would have failed CI.** One of them was crossing the 67/143
split: the heavy-vehicle share converting 31 of 34 calibration count targets was
a median over 23 classified stations of which **20 are holdout**. It is now
calibration-only — **`heavy_vehicle_share` 0.0652 → 0.1120** — and the modelled
side of the same comparison stopped counting `vol_car` alone. **F29 is still
built and unlaunched**; no simulation input moved, so no family opened.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The newest reading is F28's at its iteration-100 gate (`aborted_20260907T030352_300it_25pct`). | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F29 build** (§9.149) — chains, plans and the 30 run-input sets rebuilt 7 Sep. `check_package.py` was NOT re-run this session; the C3 target artefact and the manifest changed after it last passed. | `python tests/check_package.py` (~10 min) |
| **The session gate is 16 PASS, 1 FAIL: `toolchain`** — `.tools/` has never been bootstrapped in this checkout, so the run stack is absent. **No arm can launch until it is.** | `python src/setup/bootstrap_toolchain.py` (no `--verify` first), then `python src/run/session_gate.py` |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **THE ISSUE GATE NOW BLOCKS A LAUNCH.** 20 open issues, 15 `awaiting-run`, **5 blocking** — #147–#151, the defects §9.150 left open. Four need a ruling (`decision-needed`), one is a data job. Two of them (#150, #151) **open a family**, so they are cheaper before the F29 arm than after it. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry **472** fields, 512 manifest files, `F29-lifts-are-the-long-trips` newest in the ledger. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT. **25 % runs only.** | assume none; ask |

## §1 The lane

**Clear the five blocking issues, bootstrap the toolchain, then launch F29's
first arm and read it at 100.** The issue gate refuses a launch until #147–#151
are closed or labelled `awaiting-run`; that is GOAL.md requirement 10 doing its
job, and the ruling is the user's.
`python run.py --run-config f29_gate_25pct --detach`, then verify per #70 that
`matsim.log` enters iterations. Cost: the F28 arm ran at a **median 260 s an
iteration, 27,657 s to its gate** (§9.149), so ~22 h for 300 iterations; needs a
stated-cost approval. Read, in order:

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
   motorbike and taxi. **#82's −91.8 % is not the figure to expect**, and the
   first reading on the new basis is what tells you whether #82 was ever as bad
   as it looked.
5. Controls: `householdCar: N waited` near 15,582; pair rate near 0.9965; 0
   ride legs without a declared driver.

**Decisions the user must take** (the board's *Next*): a stated-cost approval
for the F29 arm; whether to close the five defects §9.150 deliberately left
open, two of which open a family; whether a fifth binder pass is needed once
F29 reports the bound-trip lengths; the Task Scheduler log (#66); the S2 tram
signal priority.

## §2 Traps — newest first, at most ten

1. **A check can be green on a rule it cannot test** (§9.150). Three were: the
   hardcoding scanner read module level and ALL-CAPS only, the sweep check saw
   one dict level, and a test fixture counted as a consumer. All three were at
   0 and all three were blind. **Widen a check before trusting its zero.**
2. **`--stop` used to end every arm on the machine** and the harness overwrote
   the operator's cause (§9.150). Fixed, with `_operator_stop.json` written
   before the kill — but the fix is untested against a live arm.
3. **`qsim.vehicleBehavior` is GLOBAL** (§9.148). `wait` strands walk and taxi,
   which are network modes with per-person vehicles and not chain-based:
   55,862 car agents stuck at iteration 0, an arm wasted.
4. **Insert vehicles BEFORE creating the agent** (§9.148). MATSim 26 builds the
   agent from a copy of the plan elements; a vehicle id stamped afterwards
   never reaches it.
5. **A binder change can be inert** (§9.149). The longest-first ordering
   rebuilt the demand and moved nothing, because the pass thins nothing on
   the weekday (`thin_p` 0.9926). Read the pass's own counters before
   rebuilding; a rebuild is ~35 min.
6. **A sampling rule can decide the demand** (§9.149). The 0.05 hash bucket
   cut every shared passenger's driver supply to 5 %.
7. **The B2 report described a file that had been rewritten three times**
   (§9.150): it counted legs before the binder passes. Fixed in the producer,
   but **the committed `_activity_chains_report.json` still carries the old
   counts until the next rebuild** — 2,189,888 against 2,225,838 on disk.
8. **`miss_window` is not a window** (§9.145): a declared pair faces no clock;
   the column means the declared driver was absent.
9. **`--set` is the scoring-parameter override; `--config-set` is the registry
   override** (§9.147). Three probes were refused at launch before that was read.
10. **A dry run that resolves is not a launch that runs** — a probe overlay
    outside a field's sweep needs `allow_outside_sweep` with a justification.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to date
  is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep); the shared-ride bucket is that
  fraction since §9.149.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py`, **RED at handoff**: #147–#151
  block, by design. Fix or rule on them; do not label them `awaiting-run` to
  get past the gate, because none of them is waiting on a measurement.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **Ensure iterations have no inefficiencies and take as little time as
  possible** (user directive, 6 Sep) — §9.147 is the record; the F28 arm's
  260 s median is the measurement.
- **Fix the defects according to the report** (user directive, 7 Sep) — §9.150
  is the record; **SPENT** on the 29 closed there. The five left open are named
  in that section with the reason each was left.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
