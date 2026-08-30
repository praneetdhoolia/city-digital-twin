# Brief for the next agent

**Written:** 30 August 2026, seventeenth session · **Open family:** `F20-bucket-rule-carve-pool` · **Commit:** the PR that carries §9.132
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session changed no model value and opened no family. It put the project on
one page (§9.132): the goal is a tracked document, the board is generated where
a run or a build decides it, the record is frozen through §9.131 behind thirteen
position pages, and the two session skills read about 600 lines instead of
fourteen thousand. **The model lane is exactly where the sixteenth session left
it** — the licence-rate population is rebuilt and its demand chain is not.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **No arm is running; the machine is idle.** The F20 arm `aborted_20260830T184955_300it_10pct` was stopped at iteration 11 at the user's direction (cause in its `_meta.json`). | `python src/run/session_gate.py --digest` (the MACHINE line) · `ls -t results/ \| head` |
| **The package on disk is inconsistent.** `demand/population/` was rebuilt 30 Aug 19:31 with the measured licence rates (§9.131, 612,634 persons in `_population_report.json`); the WEEKDAY chains are absent and the plans and the 30 run-input sets are the F20 ones. `tests/check_package.py` fails until the chain in §1 is rerun. | `ls -la cities/newcastle/demand/plans/B2_activity_trips_WEEKDAY.csv` (absent) · `python tests/check_package.py` |
| **This session's PR** is open at handoff, or merged — check. | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues: #73 and #68 were **closed** this session on the evidence the position pages cite; #21 carries a measured comment (its scoring-weight half still reaches nothing); no other issue changed. | `gh issue list --state open` |
| Registry 414 fields, manifest 501 files, 30 run-input sets, family `F20-bucket-rule-carve-pool` open — all generated into the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Approvals are spent on use. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — every check on one line; it
skips the toolchain compile only while an arm runs.

## §1 The lane

**First build (~1 h CPU, not a run):** the demand chain the last handoff
interrupted, on the F21 population —

```bash
python src/build/build_activity_chains.py       # four binder passes incl. shared rides
python src/build/build_matsim_plans.py          # choice-set seed, carves on the drawn pool
python src/build/build_matsim_run_inputs.py     # 30 sets
python src/build/normalise_eol.py && python src/build/build_manifest.py && python src/build/normalise_eol.py
python tests/check_package.py                   # must be ALL PASSED before any launch
```

Read `_activity_chains_report.json` → `by_day.WEEKDAY.shared_binding`
(servable / bound / shortfall; last value 73,509 / 59,701 / 0 on the OLD
population, §9.129) and `_plans_report.json` → `motorbike_carve` /
`truck_carve`. Declare **F21** in `docs/run_families.json` at the arm's
launch stamp, with `decisions_ref` 9.131.

**Then the F21 arm** — S2, WEEKDAY, 10 %, 300 iterations, innovation off at 240,
launched detached (`python run.py --run-config f21_gate_10pct --detach` after
adding the overlay by copying `f20_gate_10pct.json`). **Needs a stated-cost
approval: ~9–15 h** at the measured 100–200 s/it
([positions/runs-and-economics](positions/runs-and-economics.md)). Smoke it
first (`--run-config smoke`, rc 0).

**Gate it at 100, 200 and 300** with `python src/analyse/report_mode_ridership.py
--run results/<arm> --trend` — every mode, trend before level, iterations 0–6
are the unscored seeds. Stop on any mode past 20 % or heading there; fix the
cause from the root ([`GOAL.md`](GOAL.md), the loop). After every reading:
`python src/analyse/build_status_board.py` so the board carries it.

What the F21 arm must answer, in order: does car reach its share once workers
hold licences (§9.131 — the F20 reading was −17.7 % at iteration 10); does heavy
rail fall from five times its disclosed boardings (#98); does ride realise what
the demand binds (§9.121 measured 88.8 % pairing on identity; the ceiling is
~11 % bound vs 20.6 % observed, #86); where do walk, bike and bus settle with the
car-less quarter served ([positions/walk-and-bike](positions/walk-and-bike.md)).

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

1. **The gate recompiled `.tools/classes` under a running arm** (this session,
   from the old `/onboard` list). The arm survived; the gate script now skips
   the compile while an arm runs. Never run `bootstrap_toolchain.py --verify`
   with a big `java.exe` up.
2. **A run's identity includes the population it sampled from** (§9.127). A
   rebuilt demand must never resume an earlier probe; `inputs_sha256` is in the
   run key. Read `plans.xml.gz`'s person count against the previous arm's before
   believing an iteration.
3. **A coupling between households is a sampling unit** (§9.127, §9.129). The
   first F18 arm ran on half a sample; the at-or-below rule then biased every
   sub-sample. Check the sample's composition at iteration 0 after any binder change.
4. **A mode's excess is often another mode's deficit** (§9.123). Bike +250 % was
   the car-less quarter with no lift; every bike parameter was innocent. Split
   the population by car availability before touching a constant.
5. **A beeline crosses water; a network walk does not** (§9.121, #94). Any
   router shortcut that reasons on straight lines must be checked against the
   network it executes on.
6. **A choice set is scored under whatever traffic its iteration carried**
   (§9.121). Read per-mode plan scores in memory before believing a share.
7. **The heavy-rail target basis changed to boardings** (§9.130); readings on
   the trip-share basis do not compare with readings on the boardings basis.
8. **A cause must carry its measurement.** Seven mechanisms were argued from
   plausibility and refuted across three sessions; the walking meeting point
   was measured out on a 1 % smoke before it reached an arm (§9.128).
9. **`modestats.csv` is planned, the trips table is realised** (§9.83); a
   planned ride executed as a drive scores like a car plan (§9.120).
10. **A heredoc in git-bash eats quotes and backslashes** — write Python,
    Markdown and JSON with a file tool, then run the file.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The F21 arm's approval
  has **not** been given. Every earlier approval is **SPENT**.
- **The goal directive lives in [`GOAL.md`](GOAL.md)** and is not re-issued
  per session: twelve modes physical, monitored and scored; <10 % each; gate
  every 100 iterations; stop on >20 % or heading there; fix from the root;
  converge in ≤250; derive, never assume; disclosed values exact.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
