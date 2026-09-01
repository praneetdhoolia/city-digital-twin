# Brief for the next agent

**Written:** 1 September 2026, twenty-first session · **Open family:** `F22-pt-fares-priced` · **Commit:** the PR that carries §9.136–§9.137
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session ran the first F22 arm to its iteration-100 gate — **bus came
inside its band (+8.0%), the first of the twelve at any gate; heavy rail fell
37,540 → 16,512 boardings and was still falling; the walk/car seesaw survived
the fare** — measured the no-run lanes (#93 carve aggregation, #30 corridor
structure, #86 ride ledger), and then, on a user directive, landed the
**results store** (§9.137): run bulk is now a 500 GB budgeted cache under
`results/raw`, findings live forever under `results/processed`, the runner
gates and stops its own runs, and **nobody touches `results/` by hand**.
**The next lane is the user's pick of the next family's cause from §9.136's
measured set.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **No arm is running; the machine is idle.** The newest arm is `aborted_20260831T165127_300it_25pct`, stopped at its iteration-100 gate (§9.136) — the scoreboard's reading. | `python src/run/session_gate.py --digest` (the MACHINE line) |
| **The results store is live** (§9.137): all runs under `results/raw`, findings under `results/processed`, raw at or under `RUN.storage.raw_cap_gb` = 500; deletions in `results/processed/_trim_log.json`. | `python -c "import sys;sys.path.insert(0,'src/run');import results_store as s;print('%.1f GiB' % (s.raw_size_bytes()/2**30))"` |
| **The package on disk is consistent** — nothing in it changed this session; the fare-era ALL CHECKS PASSED of 31 Aug stands. | `python tests/check_package.py` (about ten minutes) |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/f22-fare-arm`. | `gh pr list --state open` · `gh pr checks <n>` |
| Issues #98, #99, #93, #30, #86, #82, #96 and #66 carry this session's measured comments (§9.136–§9.137); no issue was closed or opened. | `gh issue list --state open` |
| Registry 452 fields, manifest 509 files, 30 run-input sets, family `F22-pt-fares-priced` open from `20260831T164923` — all in the board's *State* block. The NEXT family is declared only at its arm's launch. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** The F22 approval (25% × 300, ~25 h stated) was SPENT on the 31 Aug 16:51 launch, stopped at its gate. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — every check on one line; it
skips the toolchain compile only while an arm runs.

## §1 The lane

**The user picks the next family's cause from the measured set (§9.136)**;
the chosen fix opens its family at its arm's launch, under a fresh
stated-cost approval — costed at the measured pace: 10% ~18–21 h (§9.134),
25% ~45–50 h (§9.136), never a stated guess. The candidates, each measured
and waiting on its position page:

1. **Walk/car cost channel** — the seesaw (walk −36.6% under car +15.2%)
   survived pt pricing; `accessEgressType = none` is load-bearing, so the
   choice is physical car access/egress vs a derived parking search/access
   time extending §9.31 ([positions/walk-and-bike](positions/walk-and-bike.md)).
2. **Carve conservation** (#93) — the `sa1_thinned` cell shares aggregate
   +12% over the target LGA identity before any draw; fix is per-LGA
   conservation in `build_matsim_plans.py`, both carves, demand rebuild
   ([positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md)).
3. **Corridor attraction** (#30) — structural in the home-anchored bands;
   floorspace-weighted attraction from the harvested OSM footprints, or a
   declared agglomeration term
   ([positions/light-rail-and-ferry](positions/light-rail-and-ferry.md)).
4. **Ride binder reach** (#86) — generated 19.13% / bound 16.0% / realised
   12.1%; the passes structurally miss licensed car-available riders between
   households ([positions/ride-and-pairing](positions/ride-and-pairing.md)).

Also open, no run needed: the #96 leaf trace (a `SubtourChainScan` example
tag + recompile, machine idle now).

**Decisions required from the user** (also on the board):
1. The next family's cause — the pick above.
2. The next arm's stated-cost approval at the measured pace.
3. Enable the Task Scheduler operational log (`wevtutil sl
   Microsoft-Windows-TaskScheduler/Operational /e:true`, elevated) (#66 —
   the 1 Sep PC crash is again unattributed without it).
4. Whether bus moves to a boardings basis once a regional count is acquired
   (#99).
5. Whether the S2 base grants the tram signal priority — the emitted config
   says `green_extension` while the record's S2 probe ran with it off
   ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **A trimmed run's bulk is gone for good** (§9.137): only what the
   processor extracted survives in `results/processed`. A diagnostic worth
   keeping must be written by the processor at run end, never fetched by
   hand later — extend `results_store.extract_snapshots` if a new reading
   class is needed.
2. **Never touch `results/` by hand** (§9.137): stop a run with
   `python run.py --stop <name> --cause "..."`; the gate watcher stops the
   hard bar itself. The §9.134-era kill/rename/mark_dead sequence is dead.
3. **A launch costing understates a long arm** (§9.134, §9.136): the F22
   arm was stated ~25 h and measured ~45–50 h (630–670 s/it at 25% by
   iteration 70). Cost at the measured pace; a gate is also a cost boundary.
4. **`run_failure` reads only the log's last 64 MiB** (§9.136): its
   whole-file read exhausted memory on a 6.9 GB log while a death was being
   recorded. Do not "fix" a missing early-log exception by widening it —
   a terminating exception is at the end.
5. **A raw file written on Windows hashes CRLF while git stores LF** —
   `normalise_eol.py` → `build_manifest.py` → `normalise_eol.py`, in that
   order (§9.135's close-out).
6. **The scorer counts boardings; the rail target counts entries** (§9.135):
   9.8% of rail journeys re-board. The gap is real but small; the excess is
   demand.
7. **The board's scoreboard holds back a running arm's newest iteration**
   (`build_status_board.py`): with iterations {0, 10} on disk it reads 0.
8. **`citysim` analysis tools run on `.tools/run-stack/lib/*.jar` plus
   `.tools/classes-signals`** — the wrong classpath fails only at runtime
   (§9.134). Never recompile `.tools/classes` while an arm runs (#66).
9. **A run's identity includes its population and its price system**
   (§9.127, §9.135): nothing before §9.135 compares with anything after,
   and a 25% reading never compares with a 10% one (§9.10, §9.12).
10. **A mode's excess is often another mode's deficit** (§9.123, §9.134):
    split by car availability before touching any constant; a cause carries
    its measurement (§9.128).

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The F22 approval
  (25% × 300, ~25 h stated, granted 31 Aug) is **SPENT** on the arm stopped
  at its gate; every earlier approval is **SPENT**. No approval stands.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes
  physical, monitored, scored; <10% each; gate every 100 iterations (the
  hard bar now the runner's own, §9.137); stop on >20% or heading there;
  fix from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in
  every table; **one arm at a time** (#66); launch detached; never commit
  to `main`; the session's one PR opens at `/handoff`.
