# Brief for the next agent

**Written:** 2 September 2026, twenty-third session · **Open family:** `F23-behaviour-channels` · **Commit:** the PR that carries §9.139
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session took family F23 to its first gate. The 25% × 300 arm
(`20260901T165115_300it_25pct`, launched under the user's 2 Sep continue
directive) was read at iteration 100 and stopped by the session: 7 modes at
or past 20% (§9.139). The channels answered the §9.138 questions — bike
+185.5% → +111.2% and still falling (the stress channel works, #107); the
walk/car seesaw now over-swings THROUGH its targets; income scaling BLUNTS
the fare (heavy rail +193.2% vs F22's +152.9% at the same milestone, bus
loses its inside place, #108, #98); ferry and light rail untouched (#94,
#30). The §9.137 gate watcher did not fire — measured blind (its 64 KiB
log-tail read vs a 51 GiB log) and fixed to read `_progress.json` — the fix
has never fired live. **The next lane is the user's root-cause pick.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The F23 gate arm is `aborted_20260901T165115_300it_25pct`, stopped at iteration 100 by the session with the gate table as cause (§9.139). | `python src/run/session_gate.py --digest` (MACHINE line); the run's `_meta.json` |
| **The package on disk is consistent**: ALL CHECKS PASSED re-run 2 Sep; nothing in the package changed at the gate. | `python tests/check_package.py` (~10 min) |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/f23-25pct-gate-read`. | `gh pr list --state open` · `gh pr checks <n>` |
| Issues #107/#108/#98/#94 carry the gate's measured numbers as comments; #96 open, no run needed; no issue closed this session. | `gh issue list --state open` |
| Registry 462 fields, manifest 509 files, 30 run-input sets, family `F23-behaviour-channels` — the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** The 2 Sep continue directive was SPENT on the stopped gate arm; **25% runs only** (1 Sep directive) governs any future launch. | assume none; ask |
| **Untracked `cities/nagpur/` sits in the tree** — the Nagpur SECR program's work, deliberately NOT in this session's PR. Do not commit it into a Newcastle change. | `git status` |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too.

## §1 The lane

**The user picks the next family's root cause from the F23 gate reading
(§9.139), then a fresh stated-cost approval launches its arm** (~45–50 h at
25% × 300, §9.136; 25%-only stands). The candidates, in the order the
reading ranks them:

1. **Rail's residual is not a price question** (#98, §9.139): two price
   repairs each moved it and neither closed it, and income scaling moves it
   the wrong way. The corridor's missing CBD end (#30) is the standing
   structural candidate — floorspace-weighted attraction vs a declared
   agglomeration term is the recorded repair choice (§9.136).
2. **The income channel's disposition** (#108): kept as built, swept on its
   declared members, or gated `absent` next family. It measurably blunts
   the fare on rail (+152.9% → +193.2% at the same milestone), bus
   (+8.0% → +16.2%) and taxi (+70.9% → +76.6%) (§9.139).
3. **The walk/car overshoot** (§9.139): under the parking-search channel
   the pair passes THROUGH its targets ~iteration 45–50 and keeps going
   (walk −27.2% low, car +14.8% high at the stop). Diagnose before
   touching `A.parking.search_min_max` — split by car availability first
   (§9.123).

Open with no run needed: the #96 leaf trace (a `SubtourChainScan` example
tag + `.tools/classes` recompile — machine idle, allowed now; **never while
an arm runs**, #66). Decisions also pending (board): Task Scheduler
operational log (#66); bus boardings basis (#99); S2 tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **The fixed gate watcher has never fired live** (§9.139): the F23 gate
   ran 3+ iterations past 100 unnoticed before the session stopped it. At
   the next arm's iteration-100 milestone, verify `_gate_stop.json` appears
   — if it does not, the watcher is still broken and the session owns the
   stop.
2. **A 25% arm's log is ~51 GiB by its gate** (§9.139): never grep or
   `Select-String` the whole `matsim.log` — a foreground scan timed out and
   its open handle blocked the runner's own `aborted_` rename. Scan bounded
   byte windows from EOF, or read `_progress.json`.
3. **Read `cause`, never `cause_detail`, for why a run died**:
   `aborted_20260901T152548_300it_25pct`'s `cause_detail` quotes the benign
   ASM warning (`Unsupported class file major version 69`) as if it were
   the terminating exception; the `cause` (user-directed stop) is correct.
   The reader defect is recorded on
   [positions/runs-and-economics](positions/runs-and-economics.md).
4. **The board's scoreboard reads the newest ARM's newest reading** — now
   iteration 100 of the aborted F23 arm, labelled not-a-result. Do not
   quote it as a result; no run since F4 has `_run.json`.
5. **The three channels are gated, not global** (§9.138):
   `A.bike_stress.representation`, `A.parking.search_time_representation`,
   `C.income.representation` — each `absent` recovers the F22 model; a
   sweep arm toggles the field, never edits code.
6. **Never touch `results/` by hand** (§9.137): stop a run only with
   `python run.py --stop <name> --cause "..."`. If its rename fails on a
   held file handle, close the handle and re-check before doing anything —
   this session completed the runner's own printed rename intent once,
   after `--stop` had recorded the abort.
7. **Cost at the measured pace and treat a gate as a cost boundary**
   (§9.136, §9.139): the F23 arm confirmed ~18.1 h to iteration 100 at 25%
   (median 664.9 s/it), ~45–50 h per 300.
8. **`run_failure` reads only the log's last 64 MiB** (§9.136); the
   terminating exception is at the end.
9. **A run's identity includes its plans, network, price system AND
   fraction** (§9.127, §9.135, §9.138): the two F23 arms (10% and 25%)
   never compare with each other (§9.10, §9.12), and nothing before the
   F23 boundary compares with anything after.
10. **A mode's excess is often another mode's deficit** (§9.123, §9.134):
    split by car availability before touching any constant.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The 2 Sep
  "continue running and tuning" directive is **SPENT** on the stopped F23
  gate arm; every earlier approval is **SPENT**. No approval stands.
- **25% runs only** (user directive, 1 Sep) — the 10% pace tables are
  history, not options.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes
  physical, monitored, scored; <10% each; gate every 100 iterations (the
  hard bar the runner's own, §9.137, §9.139); stop on >20% or heading
  there; fix from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in
  every table; **one arm at a time** (#66); launch detached; never commit
  to `main`; the session's one PR opens at `/handoff`.
