# Brief for the next agent

**Written:** 7 September 2026, thirtieth session · **Open family:** `F29-lifts-are-the-long-trips` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/history-check-and-pre-run-fixes`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

Three gates in one session. F26 stopped at 100 with 8 out and found the ride
loss in ride proposed without a driver and a second car the household does not
own (§9.146); F27 was stopped at 19 by the operator because a global `wait`
stranded every non-chain mode (§9.148); F28 stopped at 100 with 7 out and
**car inside the band for the first time (+6.6 %)**, pairing solved, the roster
live, and the ride still lost traced to a sampling-hash bucket that let the
shared pass serve only short trips (§9.149). The iteration itself was cut from
384 s to a median 260 s (§9.147). **F29 is built and unlaunched.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The newest reading is F28's at its watcher's iteration-100 gate (`aborted_20260907T030352_300it_25pct`). | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F29 build** (§9.149): chains, plans and the 30 run-input sets rebuilt 7 Sep with `B.ride.shared_lift_hash_bucket` = 0.25 and `B.ride.shared_lift_priority` = longest_first; `check_package.py` ALL CHECKS PASSED at handoff; manifest 512 files. | `python tests/check_package.py` (~10 min) |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **Nothing blocks a launch.** All 15 open issues carry `awaiting-run` (#145 opened this session). | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry 471 fields, 30 run-input sets, `F29-lifts-are-the-long-trips` newest in the ledger. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT. **25 % runs only.** | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too. Every line should be green.

## §1 The lane

**Launch F29's first arm and read it at 100.** `python run.py --run-config
f29_gate_25pct --detach`, then verify per #70 that `matsim.log` enters
iterations. Cost: the F28 arm ran at a **median 260 s an iteration, 27,657 s
to its gate** (§9.149), so ~22 h for 300 iterations; needs a stated-cost
approval. Read, in order:

1. **Iteration 0's `legHistogram`** — car departures near F28's 231,607 and
   stuck near 3,145 say the car-only handler still does its one job; tens of
   thousands stuck means stop (§9.148).
2. **Placement** (§9.149): the share of declared bound trips ridden against
   F28's 0.560 and the walked-bound median against 1.08 km; the shared pass's
   bound-trip mean in `_activity_chains_report.json` (`bound_mean_straight_km`)
   against the HTS passenger 9.3–9.8 km. Ride against −42.8 %, read TOGETHER
   with bike (+157 %), bus (+65 %) and taxi (+161 %), whose long car-less
   trips this placement should draw down.
3. **Car must STAY inside** (+6.6 % at F28); walk against −11.9 %, motorbike
   +16.1 %.
4. Controls: `householdCar: N waited` near 15,582; pair rate near 0.9965; 0
   ride legs without a declared driver.

The reader to use is `python src/analyse/report_mode_ridership.py --run <run>
--trend`; the trip-level measurements are the scripts recorded in §9.146 and
§9.149 (experienced plans at the gate iteration only — plans and events are
gate artefacts since §9.147).

**Decisions the user must take** (the board's *Next*): a stated-cost approval
for the F29 arm; whether a fifth binder pass is needed once F29 reports the
bound-trip lengths; the Task Scheduler log (#66); the S2 tram signal priority.

## §2 Traps — newest first, at most ten

1. **`qsim.vehicleBehavior` is GLOBAL** (§9.148). `wait` strands walk and taxi,
   which are network modes with per-person vehicles and not chain-based:
   55,862 car agents stuck at iteration 0, an arm wasted. The household car
   constraint is car-only in `HouseholdCarDepartureHandler`.
2. **Insert vehicles BEFORE creating the agent** (§9.148). MATSim 26 builds the
   agent from a copy of the plan elements; a vehicle id stamped afterwards
   never reaches it. The old order only worked while the ids coincided.
3. **A binder change can be inert** (§9.149). The longest-first ordering
   rebuilt the demand and moved nothing, because the pass thins nothing on
   the weekday (`thin_p` 0.9926). Read the pass's own counters before
   rebuilding; a rebuild is ~35 min today.
4. **A sampling rule can decide the demand** (§9.149). The 0.05 hash bucket
   cut every shared passenger's driver supply to 5 %; 94 % of the unserved
   long tours had a driver in the window.
5. **A milestone cost twice a plain iteration** (§9.147) until the trips
   cadence was declared; the readers take MATSim's tables where they exist.
   The experienced plans exist only at the gate now — the trip-level scripts
   must run on it.100.
6. **The experienced-plan "car legs with every household car out" metric is
   invalid under a wait** (§9.149): a waiting driver's leg records its planned
   departure with the wait inside `trav_time`. Use the handler's own count.
7. **`miss_window` is not a window** (§9.145): a declared pair faces no clock;
   the column means the declared driver was absent.
8. **Count only what would otherwise have happened** (§9.144): a counter that
   does not reconcile against an existing total is wrong.
9. **`--set` is the scoring-parameter override; `--config-set` is the registry
   override** (§9.147). Three probes were refused at launch before that was
   read.
10. **A dry run that resolves is not a launch that runs** — a probe overlay
    outside a field's sweep needs `allow_outside_sweep` with a justification.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to date
  is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep); the shared-ride bucket is that
  fraction since §9.149.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py`, GREEN at handoff.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **Ensure iterations have no inefficiencies and take as little time as
  possible** (user directive, 6 Sep) — §9.147 is the record; the F28 arm's 260 s
  median is the measurement; the next inefficiency is whatever its stopwatch
  shows at scale.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
