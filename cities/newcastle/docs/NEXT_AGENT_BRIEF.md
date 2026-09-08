# Brief for the next agent

**Written:** 8 September 2026, thirty-fifth session (after the F31 gate) · **Open family:** `F31-the-car-router-reads-only-cars` · **Commit:** see `git log -1 origin/main` after the session's second PR merges; the branch was `praneetdhoolia/the-f31-gate-ride-places-right-lengths`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**THE F31 GATE IS READ AND THE LANE HAS MOVED.** `aborted_20260908T100009_300it_25pct`
was stopped by the watcher at **iteration 100** with 7 modes at or past 20 %;
**1 of 12 inside** (car +5.4 %). The finding that changes the plan: **ride's mean
modelled trip is 9.17 km against an observed 9.76 (-6 %)**, the closest geometry
on the board, while its share is -38.0 %. **Ride's gap is VOLUME, not placement**
- which is what F29 and F30 were both built to fix, so that question is answered
and closed.

## §0 Verify first - facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **The machine is IDLE.** No arm is running; F31's first arm stopped at its gate. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The newest citable reading is F31's iteration-100 gate**, citable there and nowhere past it. **No arm has passed 100 since F4**, across 161 runs. | `python src/analyse/report_mode_ridership.py --run aborted_20260908T100009_300it_25pct --it 100` |
| **No approval stands.** The 18.2-21.8 h approval was SPENT on that arm (it used 7.66 h). | `python src/analyse/arm_cost.py --run-config f29_gate_25pct` |
| **#159 is open and NOT `awaiting-run`**, so the issue gate is RED and the launcher will refuse. It was overridden once by operator decision for the F31 arm. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **This session's PRs** - #160 merged; the second one carries the gate close-out. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| Registry **482** fields, **512** manifest files. Unit tests **147**. | `python src/registry/render_docs.py --check` · `python -m pytest tests/unit -q` |
| **The package on disk is unchanged** - no data artefact was rebuilt this session. | `python tests/check_package.py` (~10 min) |

Then: `python src/run/session_gate.py`.

## §1 The lane

**Three root causes are on the table and none is fixed. Pick with the operator.**

1. **RIDE VOLUME** (#86, #48). Placement is solved: the lifts are the right
   length (9.17 km against an observed 9.76). What is short is how many. The next
   measurement is the declared-bound-trip funnel - how many bound trips the
   demand declares, how many survive into plan memory, how many are selected.
   **Why it matters most:** inside F31's own reading the twelve deviations sum to
   +0.086 pp, ride is **-7.830 pp**, and the modes beating it total **+9.500 pp**
   (car +3.125, bike +3.254, taxi +1.769, bus +1.301, motorbike +0.052). A
   pro-rata recovery would put car (+0.9 %), bus (+9.6 %) and motorbike (+2.4 %)
   **all inside 10 %**. It is an arithmetic upper bound, not a prediction, but no
   other single change on the table moves three modes.
2. **A THIRD OF PT ROUTING FINDS NO SERVICE** (§9.157). Over 1,700,000 decisions:
   **853,357 requests with no transit route at all (33.4 % of all)** and
   **690,635 of the rest choosing the network walk (40.6 %)**. It sits beside
   walk's modelled mean of **4.51 km against an observed 0.70** and the three
   failing pt modes. **The cause is not established.** This is the largest
   unexplained signal on the board and it did not exist as a measurement before
   §9.156 restored the log line that reports it.
3. **HEAVY RAIL HAS NO BRAKE** (#98, +247.2 %). Capacity binds physically; the
   crowding disutility is declared (`C.crowding.seated_multiplier`,
   `standing_multiplier`) and carried into no scoring. Designed, **not built**.

**Decisions the user must take:** which of the three above is worked first;
whether the **pt-walk teleportation** is filed (1,978 teleported walk legs on a
1 % run, **70.9 % ending at a `pt interaction`**, only **67** with no pt leg
either side - a narrow but real gap against GOAL requirement 1, unfiled only
because a new non-`awaiting-run` issue blocks the launcher); **whether the real
Newcastle corridor operates transit signal priority** (`A.lightrail.tsp_enabled`
is `source: assumed`, requirement 6 says derive it, and it must be settled on
evidence about the corridor, never on light rail's -47.2 %); #159; #155; #66.

## §2 Traps - newest first, each with what it cost

1. **Do not compare across a family boundary, however tempting the story.** F28
   and F31 are separated by three boundaries, and "ride improved from -42.8 % to
   -38.0 %" is exactly the sentence §3.5 exists to prevent. Read a gate on its
   own terms and do the arithmetic inside it (§9.157).
2. **`bootstrap_toolchain.py --verify` RECOMPILES.** It reads as a read-only word
   and is not. Run under a live probe on 8 Sep it rewrote both class trees at
   01:38:36 beneath the JVM; that probe is citable for NOTHING, not even the
   clock it existed to measure (§9.156).
3. **A median over every iteration is not what an arm pays**, and the arm proved
   it from the other side: the probe's recurring 216.0 s was **17 % optimistic**
   while the long-arm top anchor of 259.6 s was right to **0.5 %** (261.03 s
   measured). **Quote the band, never the point** (§9.156, §9.157).
4. **A counter on an unscoped Guice provider counts nothing** - "log the first 3"
   wrote 19,469 lines and `% 100000` never fired once (§9.156).
5. **Verify an assessment finding before fixing it.** Tram priority IS the S2b
   intervention; switching it on would have destroyed the comparison the study
   exists to make (§9.156).
6. **Ancestry right for a one-output script is wrong for a many-output one**
   (§9.156, #159).
7. **A watch that polls a run's ORIGINAL path misses its close-out**: a stopped
   run is renamed with an `aborted_` prefix, so a 7 h watch reported nothing
   while the arm had finished hours earlier (this session).
8. **A silent exclusion is how a stale price survives** (§9.155).
9. **A profile shows where CPU goes, not what to cut** (§9.155).
10. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** F31's
    arm says `stopped_at_gate`: its reading is citable at iteration 100 and
    nowhere past it (§9.143).

## §3 Standing directives and approvals

- **No approval stands. Every approval is SPENT**, including the 18.2-21.8 h one.
  Quote the next as a RANGE from `arm_cost.py`.
- **25 % runs only** (user directive, 1 September 2026).
- **One arm at a time**; never recompile `.tools/classes` under one.
- **No launch while an open issue lacks `awaiting-run`** (GOAL requirement 10).
  The gate is RED on #159 right now. It has been overridden ONCE, deliberately;
  an override is the operator's call and is recorded in the run.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's PR opens at `/handoff`.
- The record is never rewritten; superseded text is bannered and pointed past.
