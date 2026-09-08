# Brief for the next agent

**Written:** 8 September 2026, thirty-fifth session · **Open family:** `F31-the-car-router-reads-only-cars` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/an-honest-price-and-a-log-that-can-count`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**AN ARM IS RUNNING AND ITS GATE READING IS YOUR FIRST JOB.**
`20260908T100009_300it_25pct` launched 8 Sep 10:00 under an **18.2-21.8 h**
stated-cost approval, S2 x WEEKDAY, 25 %, 300 iterations, innovation off at 240.
The watcher stops it at iteration 100 while any mode is past 20 %, so the likely
spend is ~6.1 h. **It is the first arm of family F31** and the first run ever to
carry `RUN.travel_time.filter_modes` = true, so **expect movement in every mode**:
until now every mode's router read link travel times a pedestrian, a cyclist and
a stopped bus helped set (§9.154, #154).

## §0 Verify first - facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **An arm is RUNNING**: `20260908T100009_300it_25pct`. Do NOT recompile `.tools/classes` under it - and note `bootstrap_toolchain.py --verify` IS a recompile. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The last GATE reading is still F28's at iteration 100** (§9.149) until this arm reaches 100. The board's scoreboard is F30's stopped arm at it.20 - exploration, not a gate. **No arm has passed 100 since F4.** | `python src/analyse/report_mode_ridership.py --run 20260908T100009_300it_25pct --it 100` |
| **The approval is SPENT on this arm.** If it stops at the gate, the next one needs a fresh stated cost. | `python src/analyse/arm_cost.py --run-config f29_gate_25pct` |
| **#159 is open and NOT `awaiting-run`**; the launcher was overridden once with `--allow-open-issues` on the operator's decision. The issue gate will refuse the NEXT launch until #159 is fixed or the operator overrides again. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **This session's PR** - check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| Registry **482** fields, **512** manifest files (40 licences moved, ODbL 161 -> 201). | `python src/registry/render_docs.py --check` |
| **The package on disk is unchanged** - no data artefact was rebuilt this session. | `python tests/check_package.py` (~10 min) |
| Unit tests **147**. | `python -m pytest tests/unit -q` |

Then: `python src/run/session_gate.py` (it skips the toolchain compile while an
arm runs, for exactly the reason above).

## §1 The lane

**Read the arm at 100, in this order** (§9.149, §9.156):

1. **Iteration 0's `legHistogram`** against F30's iteration-0 controls (§9.153):
   car departures 232,972, stuck 3,786, 8,167 declared passengers paired on
   7,771 detours, 291 unpaired ride legs restored, 8,549 drivers waiting.
2. **Placement**: declared bound trips ridden against F28's **0.560**, the
   walked-bound median against **1.08 km**.
3. **Ride with the modes it feeds.** Ride's **-8.822 pp** deficit at F28 is
   essentially the WHOLE of the excess in the modes that beat it - car +3.840,
   bike +3.474, taxi +1.597, bus +1.548, motorbike +0.061, **10.521 pp** - and
   the twelve deviations sum to +0.008 pp as they must. A full pro-rata recovery
   would put car at **+1.1 %**, motorbike at **+2.6 %** and bus at **+10.5 %**.
   **That is an arithmetic upper bound on what ride placement alone can do, not
   a prediction.** The geometry agrees independently: bike's modelled mean is
   9.12 km against an observed 5.21, taxi 9.52 against 5.20, walk 5.26 against
   0.70 - long car-less trips that should be RIDDEN are walked, cycled and
   taxied (§9.156).
4. **Car must STAY inside** (+6.6 % at F28); walk -11.9 %, motorbike +16.1 %.
5. **The counts on their corrected basis** (§9.150). **#82's -91.8 % is not the
   figure to expect.**
6. Controls: `householdCar: N waited`; pair rate near 0.9965; 0 ride legs
   without a declared driver.
7. **Confirm the router statistic** (§9.156). The direct-walk router's progress
   line fires now, and on its first firing reported ~40 % of pt routing requests
   finding NO transit route and ~43 % of the rest taking the network walk. That
   came from a pricing probe and is not a reading of any mode. Confirm it here
   before acting on it; it bears on walk's 5.26 km mean and on bus, light rail
   and ferry.

**Decisions the user must take:** whether the crowding disutility against heavy
rail's +295 % is built before the next arm (designed, not built - §9.156);
**whether the real Newcastle corridor operates transit signal priority**
(`A.lightrail.tsp_enabled` is `source: assumed`, requirement 6 says derive it,
and it must be settled on evidence about the corridor, never on light rail's
-30 %); whether the 31 unreviewed MATSim defaults (#155) are ruled on; output-
level lineage (#159); the Task Scheduler operational log (#66).

## §2 Traps - newest first, each with what it cost

1. **`bootstrap_toolchain.py --verify` RECOMPILES.** It reads as a read-only
   word and is not. Run under the first pricing probe on 8 Sep it rewrote
   `.tools/classes` and `.tools/classes-signals` at 01:38:36 beneath the live
   JVM: the javac burst was CPU the probe's own stopwatch charged to its
   iterations, and the tree on disk stopped matching the tree the JVM had
   loaded. `aborted_20260908T012355_4it_25pct` is citable for NOTHING - not even
   the clock it existed to measure (§9.156).
2. **A median over every iteration is not what an arm pays.** Iteration 0 warms
   the JIT, `dump all plans` fires at iterations 0 and 1 only, and the last
   iteration writes the final output. On a 4-iteration probe that is three of
   five, and the median read 282.6 s against a recurring 216.0 s - a 31 %
   overstatement, in the tool that sets what an operator approves (§9.156).
3. **A counter on an unscoped Guice provider counts nothing.**
   `addRoutingModuleBinding(...).toProvider(...)` with no scope builds a new
   object per thread per iteration, so "log the first 3" wrote 19,469 lines and
   `% 100000` never fired once. Fix the binding's consequence, not the symptom
   (§9.156).
4. **Verify an assessment finding before fixing it.** Tram priority was ranked
   the cheapest way to move the board; it IS the S2b intervention
   (`sweep_role: answer`), and switching it on would have destroyed the
   comparison the study exists to make (§9.156). `fit.py`'s patronage scorer was
   called empty and is correct (§9.155).
5. **Ancestry that is right for a one-output script is wrong for a many-output
   one.** `_script_inputs` credits every path a SCRIPT mentions to every file it
   writes, so 129 rows claim an OSM ancestor; relabelling their licences on that
   basis would have moved 169 rows and given the licence column the defect the
   source column has (§9.156, #159).
6. **A silent exclusion is how a stale price survives** (§9.155).
7. **A guard written for a race needs an expiry** - 13 directories and 72.8 GiB
   protected forever (§9.155).
8. **A profile shows where CPU goes, not what to cut.** Halving the event
   threads to halve the hops made the iteration 44.5 % slower (§9.155).
9. **`RUN.storage.raw_cap_gb` is GIBIBYTES** despite its name (§9.155).
10. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** A
    stopped arm's reading is citable at its `reached_iteration` and nowhere past
    it (§9.143).

## §3 Standing directives and approvals

- **The 18.2-21.8 h approval is SPENT on `20260908T100009_300it_25pct`.** No
  other approval stands. Quote the next one as a RANGE from `arm_cost.py`, which
  now prices the recurring iteration and warns when the run it priced never met
  a milestone.
- **25 % runs only** (user directive, 1 September 2026).
- **One arm at a time**; never recompile `.tools/classes` under one.
- **No launch while an open issue lacks `awaiting-run`** (GOAL requirement 10;
  `issue_gate.py` enforces it). It has been overridden ONCE, deliberately, for
  #159 - an override is the operator's call and is recorded in the run.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is bannered and pointed past.
