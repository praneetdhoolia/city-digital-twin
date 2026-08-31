# Brief for the next agent

**Written:** 31 August 2026, nineteenth session · **Open family:** `F21-licence-rate-demand` · **Commit:** the PR that carries §9.134
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session changed no model value and no data artefact. It launched the F21
arm under a stated-cost approval, watched it to its iteration-100 gate, and
**the loop in GOAL.md fired for the first time since F4**: 8 modes at or past
20 %, the arm stopped, the reading recorded (§9.134). Car crossed its target
for the first time (+16.0 %); ride plateaued at its ~12 % demand ceiling; light
rail was the one mode moving AWAY. The #96 subtour scan was rerun on the
rebuilt plans (rate unchanged). **The next lane starts at the user's pick of
root cause.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **No arm is running; the machine is idle.** The last run is `aborted_20260830T222642_300it_10pct` — the F21 arm, stopped at its iteration-100 gate under the loop, cause in its `_meta.json`. It is the scoreboard's reading. | `python src/run/session_gate.py --digest` (the MACHINE line) · `ls -t results/ \| head` |
| **The package on disk is consistent.** Chains, plans and the 30 run-input sets are the §9.133 rebuild on the 612,634-person licence-rate population; `check_package.py` ALL CHECKS PASSED, re-run 30 Aug 22:20. | `python tests/check_package.py` (about ten minutes) |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/f21-arm-launch`. | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues #86, #93, #94, #96, #98, #30 and #66 carry this session's measured comments (§9.134); no issue was closed or opened. | `gh issue list --state open` |
| Registry 414 fields, manifest 503 files, 30 run-input sets, family `F21-licence-rate-demand` open from `20260830T222641` — all generated into the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** The F21 approval (~9–15 h) was spent on the arm above. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — every check on one line; it
skips the toolchain compile only while an arm runs.

## §1 The lane

**The user picks the root cause the next family attacks** — the gate stop
names five candidates, each with its measurement (§9.134, the position pages):

1. **The ride demand ceiling** (#86): the arm plateaued at 12.0–12.3 % from
   iteration 30 against 20.6 % observed; the binder binds 57,758 WEEKDAY
   shared trips with shortfall 0 (§9.133). More ride needs more bound demand
   — the generation side, not the pairing side
   ([positions/ride-and-pairing](positions/ride-and-pairing.md)).
2. **The corridor attraction** (#30): light rail fell 1,680 → 780 boardings
   across the arm, the only mode moving AWAY; shopping/other ends sit at
   two-thirds of the observed corridor rate — the destination solver's lane
   ([positions/light-rail-and-ferry](positions/light-rail-and-ferry.md)).
3. **Heavy rail's residual excess** (#98): halved inside the arm
   (36,340 → 17,090) but +161.8 % at the gate; the per-station split of the
   F21 outputs is unread — read it before proposing anything
   ([positions/public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md)).
4. **The walk/car balance**: walk crossed its target near iteration 38 and
   kept falling (−36.6 %) as car overshot (+16.0 %) — one movement; the
   short-trip walk/car allocation (#30) is the standing suspect
   ([positions/walk-and-bike](positions/walk-and-bike.md)).
5. **The motorbike carve identity** (#93): first gate-depth reading +24.6 %
   on the rebuilt demand; compare `_plans_report.json`'s solve against the
   gate's 0.4715 % before touching any value
   ([positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md)).

**A new arm needs a fresh stated-cost approval at the measured pace**: the F21
arm ran ~250 s/it by iteration 100, so a 300-iteration 10 % arm is **~18–21 h**,
not the 9–15 h the last launch was costed at (§9.134,
[positions/runs-and-economics](positions/runs-and-economics.md)).

**Cheap diagnostics needing no run and no approval**, in the stopped arm's own
outputs: the heavy-rail per-station split; the iteration-100 shares by car
availability; `--truck-stations`; the iteration-0 `ridePairing` counts.

**Decisions required from the user** (also on the board):
1. Enable the Task Scheduler operational log (`wevtutil sl
   Microsoft-Windows-TaskScheduler/Operational /e:true`, elevated) so a
   console-stop death can name its trigger (#66).
2. The fraction and cost of a confirmation arm after the 10 % loop — 25 % × 300
   ≈ 25 h stated (§9.129).
3. Whether bus moves to a boardings basis once a regional count is acquired
   (#99) — bus read +15.6 % at the gate, the closest PT mode.
4. **Whether the S2 base grants the tram signal priority.** The emitted S2
   config carries `tramPriority.mode=green_extension` while the record's S2
   probe ran with it off
   ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **A launch costing understates a long arm** (§9.134). Iteration time rises
   with route-set growth: solo iterations ran 171–182 s and iteration 100 ran
   ~250 s. Cost a 300-iteration arm at the LATE pace (~18–21 h at 10 %), not
   the solo pace.
2. **The board's scoreboard holds back a running arm's newest iteration**
   (`build_status_board.py`) as possibly half-written: with iterations
   {0, 10} on disk it reads 0. Wait for the next milestone before
   regenerating, or the board shows the seed pass.
3. **`citysim` analysis tools run on `.tools/run-stack/lib/*.jar` plus
   `.tools/classes-signals`** — the `<run-stack>` in usage comments means the
   `lib` subdirectory. The wrong classpath fails only at runtime
   (`NoClassDefFoundError`), after minutes of reading (§9.134).
4. **A registry `consumers` claim can be untrue and invisible until the local
   package check runs** (§9.133). When a declared value is copied from a
   script's output, make the script assert against the field.
5. **The gate recompiled `.tools/classes` under a running arm** (seventeenth
   session). The gate script now skips the compile while an arm runs; never
   run `bootstrap_toolchain.py --verify` with a big `java.exe` up.
6. **A run's identity includes the population it sampled from** (§9.127). A
   rebuilt demand must never resume an earlier probe; read `plans.xml.gz`'s
   person count against the previous arm's before believing an iteration
   (F21: 61,953 vs F20's 62,134, §9.134).
7. **A mode's excess is often another mode's deficit** (§9.123, §9.134). Walk
   −36.6 % under car +16.0 % is one movement; ride's missing 8 % sits in
   car's overshoot. Split the population by car availability before touching
   a constant.
8. **The heavy-rail and light-rail bases are boardings** (§9.130); readings on
   the trip-share basis do not compare with boardings-basis readings.
9. **A cause must carry its measurement** (§9.128). Seven mechanisms were
   argued from plausibility and refuted; measure on the stopped arm's outputs
   before proposing the fix.
10. **A heredoc in git-bash eats quotes and backslashes** — write Python,
    Markdown and JSON with a file tool, then run the file.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The F21 arm's
  approval (~9–15 h) is **SPENT** on `aborted_20260830T222642_300it_10pct`.
  Every earlier approval is **SPENT**. No approval stands.
- **The goal directive lives in [`GOAL.md`](GOAL.md)** and is not re-issued
  per session: twelve modes physical, monitored and scored; <10 % each; gate
  every 100 iterations; stop on >20 % or heading there; fix from the root;
  converge in ≤250; derive, never assume; disclosed values exact.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
