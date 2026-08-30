# Brief for the next agent

**Written:** 30 August 2026, eighteenth session · **Open family:** `F20-bucket-rule-carve-pool` · **Commit:** the PR that carries §9.133
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session changed no model value and opened no family. It finished the build
the sixteenth session interrupted: the demand chain — chains, plans, the 30
run-input sets, the manifest — is rebuilt on the licence-rate population of
§9.131, `tests/check_package.py` passes, a registry `consumers` claim that the
package check had exposed is made true, the F21 overlay is written and a smoke
has run on the rebuilt inputs (§9.133). **The model lane is one approval away
from the F21 arm.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **No arm is running; the machine is idle.** The last run is the smoke `20260830T213149_2it_1pct` (2 iterations, 1 %, rc 0 — a plumbing test, not a result). The F20 arm `aborted_20260830T184955_300it_10pct` stays the scoreboard's reading at iteration 10. | `python src/run/session_gate.py --digest` (the MACHINE line) · `ls -t results/ \| head` |
| **The package on disk is consistent.** Population 612,634 persons (`_population_report.json`); chains, plans and the 30 run-input sets rebuilt on it 30 Aug 21:05–21:27; manifest 503 files; `check_package.py` ALL CHECKS PASSED (§9.133). | `python tests/check_package.py` (about ten minutes) · `ls -la cities/newcastle/demand/plans/B2_activity_trips_WEEKDAY.csv` |
| **This session's PR** is open at handoff, or merged — check. | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues: #86, #93 and #96 carry this session's measured comment (§9.133); no issue was closed or opened. | `gh issue list --state open` |
| Registry 414 fields, manifest 503 files, 30 run-input sets, family `F20-bucket-rule-carve-pool` open — all generated into the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Approvals are spent on use. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — every check on one line; it
skips the toolchain compile only while an arm runs.

## §1 The lane

**The F21 arm** — S2, WEEKDAY, 10 %, 300 iterations, innovation off at 240,
launched detached:

```bash
python run.py --run-config f21_gate_10pct --detach
```

**Needs a stated-cost approval: ~9–15 h** at the measured 100–200 s/it
([positions/runs-and-economics](positions/runs-and-economics.md)); none
stands. The overlay exists (`cities/newcastle/overlays/runs/f21_gate_10pct.json`)
and the smoke has already run, so the launch is one command. At the launch,
declare **F21** in `docs/run_families.json` with `from_launch` = that stamp
and `decisions_ref` 9.131, and add its row to
[positions/sampling-and-families](positions/sampling-and-families.md).

**Before believing iteration 0**, read the sample's composition: person count
in the arm's `plans.xml.gz` against the F20 arm's (the 1 % smoke drew 6,428
against 6,263 — a different seeded draw once the couplings changed, §9.127).

**Gate it at 100, 200 and 300** with `python src/analyse/report_mode_ridership.py
--run results/<arm> --trend` — every mode, trend before level, iterations 0–6
are the unscored seeds. Stop on any mode past 20 % or heading there; fix the
cause from the root ([`GOAL.md`](GOAL.md), the loop). After every reading:
`python src/analyse/build_status_board.py` so the board carries it.

What the F21 arm must answer, in order: does car reach its share once workers
hold licences (§9.131 — the F20 reading was −17.7 % at iteration 10); does heavy
rail fall from five times its disclosed boardings (#98); does ride realise what
the demand binds — 57,758 shared bindings and a shortfall of 0 on the rebuilt
WEEKDAY (§9.133), against the ~11 % ceiling and 20.6 % observed (#86); where
do walk, bike and bus settle with the car-less quarter served
([positions/walk-and-bike](positions/walk-and-bike.md)).

**While the arm runs (no approval needed):** rerun the #96 subtour scan on the
rebuilt plans (§9.119).

**Decisions required from the user** (also on the board):
1. Enable the Task Scheduler operational log (`wevtutil sl
   Microsoft-Windows-TaskScheduler/Operational /e:true`, elevated) so a
   console-stop death can name its trigger (#66).
2. The fraction and cost of a confirmation arm after the 10 % loop — the bucket
   rule keeps pairs inside any sample at a multiple of 0.05; 25 % × 300 ≈ 25 h.
3. Whether bus moves to a boardings basis once a regional count is acquired (#99).
4. **Whether the S2 base grants the tram signal priority.** The emitted S2 config
   carries `tramPriority.mode=green_extension` while the record's S2 probe ran
   with it off; the S2 and S2b signal systems are byte-identical
   ([positions/signals-and-crossings](positions/signals-and-crossings.md)).
   It must be declared before any S2-versus-S2b comparison.

## §2 Traps — newest first, at most ten

1. **A registry `consumers` claim can be untrue and invisible until the local
   package check runs** (this session, §9.133). `B.population.licence_rate_by_age_band`
   named its producing script as a consumer and the script never spelled the
   key; only `check_package.py` (local) tests the claim, and it was hidden behind
   two expected failures. When a declared value is copied from a script's
   output, make the script assert against the field (§9.116's pattern).
2. **The gate recompiled `.tools/classes` under a running arm** (seventeenth
   session). The gate script now skips the compile while an arm runs. Never run
   `bootstrap_toolchain.py --verify` with a big `java.exe` up.
3. **A run's identity includes the population it sampled from** (§9.127). A
   rebuilt demand must never resume an earlier probe; `inputs_sha256` is in the
   run key. Read `plans.xml.gz`'s person count against the previous arm's before
   believing an iteration.
4. **A coupling between households is a sampling unit** (§9.127, §9.129). The
   first F18 arm ran on half a sample; the at-or-below rule then biased every
   sub-sample. Check the sample's composition at iteration 0 after any binder change.
5. **A mode's excess is often another mode's deficit** (§9.123). Bike +250 % was
   the car-less quarter with no lift; every bike parameter was innocent. Split
   the population by car availability before touching a constant.
6. **A beeline crosses water; a network walk does not** (§9.121, #94). Any
   router shortcut that reasons on straight lines must be checked against the
   network it executes on.
7. **A choice set is scored under whatever traffic its iteration carried**
   (§9.121). Read per-mode plan scores in memory before believing a share.
8. **The heavy-rail target basis changed to boardings** (§9.130); readings on
   the trip-share basis do not compare with readings on the boardings basis.
9. **A cause must carry its measurement.** Seven mechanisms were argued from
   plausibility and refuted across three sessions; the walking meeting point
   was measured out on a 1 % smoke before it reached an arm (§9.128).
10. **A heredoc in git-bash eats quotes and backslashes** — write Python,
    Markdown and JSON with a file tool, then run the file.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The F21 arm's approval
  has **not** been given. Every earlier approval is **SPENT**. The smoke this
  session ran was a two-iteration plumbing test, not a run needing one.
- **The goal directive lives in [`GOAL.md`](GOAL.md)** and is not re-issued
  per session: twelve modes physical, monitored and scored; <10 % each; gate
  every 100 iterations; stop on >20 % or heading there; fix from the root;
  converge in ≤250; derive, never assume; disclosed values exact.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
