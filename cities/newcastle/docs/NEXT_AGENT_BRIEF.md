# Brief for the next agent

**Written:** 1 September 2026, twenty-second session · **Open family:** `F23-behaviour-channels` · **Commit:** the PR that carries §9.138
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session read the two research artifacts against the repository, verified
their claims (down to the pinned jar's bytecode and the matsim-libs source),
and — on the user's 1 Sep goal directive — built the three channels they
ranked above everything remaining (§9.138): **bike traffic stress** (Broach
et al. 2012 felt-distance factors per link, in score and router, #107), the
**derived parking search time** (§9.136's measured walk/car candidate, Shoup
2006 × the §9.31 density ramp), and **income-scaled money sensitivity** (the
G17 band midpoint through MATSim core, #108). Plans and the 30 sets rebuilt,
smoke-verified live, family F23 declared, and the first arm **launched and
left running** at the 10% pace. **The next lane is reading that arm at its
gates.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **The F23 arm `20260901T133404_300it_10pct` is RUNNING** (launched 13:34, ~18–21 h to 300; the §9.137 watcher stops the hard bar at 100/200/300 itself). This handover was written mid-run by design — the arm outlives the session. | `python src/run/session_gate.py --digest` (the MACHINE line); `results/raw/20260901T133404_300it_10pct/_progress.json` |
| **The package on disk is consistent**: plans + 30 sets rebuilt 1 Sep with the three channels; ALL CHECKS PASSED same day. | `python tests/check_package.py` (~10 min) |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/f23-behaviour-channels`. | `gh pr list --state open` · `gh pr checks <n>` |
| Issues #107 and #108 opened and carry the build; #98 carries the crowding deferral (§9.138). No issue closed. | `gh issue list --state open` |
| Registry 462 fields, manifest 509 files, 30 run-input sets, family `F23-behaviour-channels` open from `20260901T133356` — all in the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** The user's 1 Sep goal directive (incorporate + test) was SPENT on the 13:34 launch. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — it skips the toolchain
compile while the arm runs.

## §1 The lane

**Read the first F23 arm at its iteration-100 gate** (~6–8 h after launch;
the watcher stops the hard bar itself and writes `_gate_stop.json` — §9.137).
Read with `python src/analyse/report_mode_ridership.py --run
20260901T133404_300it_10pct --it 100 --trend`, every mode individually,
trend not level (§9.108). What the arm must answer, in order (§9.138):

1. **Bike** from +185.5%: does the stress channel move it toward 2.21%, and
   where do its trips land — walk (−36.6%) and ride (−41.3%) are the
   candidates (§9.123: 95.4% of bike-choosers have no car).
2. **The walk/car seesaw** under the parking search time: does the short
   dense-zone car trip finally pay enough to walk.
3. **Taxi (+70.9%) and the fare's rail residual** under income scaling
   (#98): richer agents feel fares less, poorer more — where do rail and
   taxi settle.
4. **Crowding stays deferred** until this gate says where fares alone
   settle rail (§9.138) — wiring it earlier conflates the two.

If the gate stops the arm: find the cause from the root, never a
compensating constant; a mode's excess is another's deficit — split by car
availability first (§9.123, §9.134). If readings pass the gate, the arm
continues to 200/300 on its own.

**Decisions required from the user** (also on the board): enable the Task
Scheduler operational log (`wevtutil sl
Microsoft-Windows-TaskScheduler/Operational /e:true`, elevated) (#66);
whether bus moves to a boardings basis once a regional count is acquired
(#99); whether the S2 base grants the tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).
Also open, no run needed: the #96 leaf trace (a `SubtourChainScan` example
tag + recompile — **never recompile `.tools/classes` while the arm runs**).

## §2 Traps — newest first, at most ten

1. **The board's scoreboard reads the RUNNING arm's newest held-back
   iteration** — at handoff that is F23 iteration 0, seeded chaos (walk
   +155.6%, rail +500%). It is labelled not-a-result; do not quote it.
2. **A benign ASM warning looks like a launch failure** (§9.134, §9.138):
   `Unsupported class file major version 69` and the `VehicleAbortsEvent`
   handler-registration INFO lines appear in every healthy log. Verify a
   launch by `ITERATION 1 BEGINS`, never by grepping "Exception".
3. **The three channels are gated, not global** (§9.138):
   `A.bike_stress.representation`, `A.parking.search_time_representation`,
   `C.income.representation` — each `absent` recovers the F22 model; a
   sweep arm toggles the field, never edits code.
4. **`parking_prices.tsv` has three columns now**; a parser that
   `partition`s on the first tab dies on it — `check_package.py` was fixed
   for exactly this (§9.138). Check any other consumer before writing one.
5. **A trimmed run's bulk is gone for good** (§9.137): extend
   `results_store.extract_snapshots` for any new reading class; never fetch
   by hand later.
6. **Never touch `results/` by hand** (§9.137): stop a run only with
   `python run.py --stop <name> --cause "..."`.
7. **A launch costing understates a long arm** (§9.134, §9.136): cost at
   the measured pace (10% ~18–21 h, 25% ~45–50 h per 300); a gate is also a
   cost boundary.
8. **`run_failure` reads only the log's last 64 MiB** (§9.136); the
   terminating exception is at the end.
9. **A run's identity includes its plans, its network and its price
   system** (§9.127, §9.135, §9.138): nothing before the F23 boundary
   compares with anything after, and a 10% reading never compares with a
   25% one (§9.10, §9.12).
10. **A mode's excess is often another mode's deficit** (§9.123, §9.134):
    split by car availability before touching any constant.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The user's 1 Sep
  goal directive (incorporate the artifact findings and test) is **SPENT**
  on the running F23 arm; every earlier approval is **SPENT**. No approval
  stands for any further launch.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes
  physical, monitored, scored; <10% each; gate every 100 iterations (the
  hard bar the runner's own, §9.137); stop on >20% or heading there; fix
  from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in
  every table; **one arm at a time** (#66); launch detached; never commit
  to `main`; the session's one PR opens at `/handoff`.
