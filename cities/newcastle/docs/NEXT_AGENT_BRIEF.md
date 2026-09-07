# Brief for the next agent

**Written:** 8 September 2026, thirty-fourth session · **Open family:** `F30-an-escort-is-priced-as-an-escort` · **Commit:** see `git log -1 origin/main` after the session's PR merges; the branch was `praneetdhoolia/fifth-project-assessment`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**The 2-minute iteration is answered, and the answer is no** (§9.155). It was
answered with arithmetic before a knob was turned: the mobsim alone is **143 s**
of a 205.5 s iteration, so **zeroing every other phase still lands above 120 s**,
and all three measured levers taken at their full CPU share land near **171 s**.
The one untested value of the events knob was probed and is **44.5 % slower**, so
the 11.6 % of CPU §9.154 found in the events queue is the price of short pipeline
stages, not waste. **Iteration wall time is closed as a lane until an arm runs.**
The lane is what it was: **the arm is priced, gated and unlaunched.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle, no arm running.** One 4-iteration profiling probe ran and completed: `20260907T233540_4it_25pct`, `ran_to_last_iteration`, median 376.78 s, 2,579.9 s wall. Its clock is citable; nothing else about it is. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The last GATE reading is still F28's at iteration 100** (§9.149). The board's scoreboard is F30's stopped arm at it.20 — exploration, not a gate. **No arm has run since, and none has passed 100 since F4.** | `python src/analyse/report_mode_ridership.py --run aborted_20260907T030352_300it_25pct --it 100` |
| **The next arm opens a NEW family**: `RUN.travel_time.filter_modes` = true moves results (§9.154, #154). The ledger's newest key is still `F30` because nothing has launched under it. | `python src/analyse/build_status_board.py --check` · `cities/newcastle/docs/run_families.json` |
| **The session gate passes 18/18**, and `--fix` is new: it regenerates every stale GENERATED artefact and re-checks. | `python src/run/session_gate.py` · `--fix` |
| **The package on disk is unchanged** — no data artefact moved this session. | `python tests/check_package.py` (~10 min) |
| **The issue gate is GREEN**: 17 open, all `awaiting-run`. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry **481** fields, **512** manifest files. | `python src/registry/render_docs.py --check` |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **No run approval stands.** Every approval is SPENT. **25 % runs only.** | assume none; ask |

## §1 The lane

**Price the arm on an UNPROFILED probe, get the approval, launch it, read it at 100.**

`arm_cost.py` now tells you why this matters. It excludes profiled runs — the
recorder is ~8 % of their clock — and did so silently, so after §9.154 (when the
only runs carrying the repair were profiled probes) it quoted **26.3 h** off a
pre-repair arm at 376.4 s. It now names the newer runs it threw away and the gap.
**One unprofiled 4-iteration probe, about 35 minutes, corrects the quote before
an approval is spent on it** — the measured plain iteration is 205.5 s profiled /
~190 s unprofiled, so the honest band for 250 iterations is **13.5–18 h**, not 26.

Then: `python run.py --run-config f29_gate_25pct --detach`, and
`python src/run/verify_launch.py` — which now performs the #70 check the launcher
used to print for a person. Read at the gate, in order:

1. **Iteration 0's `legHistogram`** against F30's iteration-0 controls (§9.153):
   car departures 232,972, stuck 3,786, 8,167 declared passengers paired on
   7,771 detours, 291 unpaired ride legs restored, 8,549 drivers waiting.
2. **Placement** (§9.149): declared bound trips ridden against F28's 0.560, the
   walked-bound median against 1.08 km. Ride against −42.8 %, read TOGETHER with
   bike (+157 %), bus (+65 %) and taxi (+161 %).
3. **Car must STAY inside** (+6.6 % at F28); walk −11.9 %, motorbike +16.1 %.
   **Expect movement from #154**: every mode's router had been reading link
   travel times a pedestrian helped set, and that is now car-only.
4. **The counts on their corrected basis** (§9.150). **#82's −91.8 % is not the
   figure to expect.**
5. Controls: `householdCar: N waited`; pair rate near 0.9965; 0 ride legs
   without a declared driver.

**Decisions the user must take:** a fresh stated-cost approval for the next arm,
priced after an unprofiled probe; whether the **31 unreviewed MATSim defaults**
(#155) are ruled on before the arm or after it; whether the S2 base grants the
tram signal priority ([positions/signals-and-crossings](positions/signals-and-crossings.md));
the Task Scheduler operational log (#66).

## §2 Traps — newest first, each with what it cost

1. **A silent exclusion is how a stale price survives.** `arm_cost.py` threw away
   the only runs carrying the current stack and said nothing, quoting 26.3 h
   against a measured 13.5–18 h — an operator would have approved 8–12 hours the
   model no longer needs (§9.155).
2. **A guard written for a race needs an expiry.** The #132 guard kept any run
   with `_run.json` and no `_metrics.json`; an operator or gate stop never gets
   one, so 13 directories and **72.8 GiB** were protected forever while the store
   deleted younger COMPLETE runs instead (§9.155).
3. **A profile shows where CPU goes, not what to cut.** 11.6 % of all CPU sat in
   the events queue; halving the threads to halve the hops made the iteration
   **44.5 % slower**, because each stage then throttled the 16 qsim threads. A
   profile raises hypotheses; only a probe settles one (§9.155).
4. **A median over a phase that fires in some iterations is not a cost.**
   `dump all plans` fires at iterations 0 and 1; a median over 1–3 reported 59 s
   of a 206 s iteration that does not pay it. `compare_runs.py` flags it (§9.155).
5. **A check can state a falsehood in prose and stay green.**
   `check_legacy_drift.py` said the `dwell_charging_s` constant "is gone"; it is
   live at `build_corridor_layers.py:125` and writes manifest row 99, invisible
   because the scanner evaluates `dict(...)` to `Ellipsis` (§9.155).
6. **An assessment finding can be wrong.** `fit.py`'s patronage scorer was
   reported as structurally empty; it is correct and self-declaring — `n=0`
   beside 32 listed unscorable targets with reasons. **Verify before fixing**
   (§9.155).
7. **The recorder is in a profiled run's clock** (~8 %). Never compare a profiled
   run with an unprofiled one; `compare_runs.py` refuses it (§9.154, §9.155).
8. **`RUN.storage.raw_cap_gb` is GIBIBYTES** despite its name — the code
   multiplies by 2^30 (§9.155).
9. **Never recompile `.tools/classes` while an arm or probe runs**; the session
   gate skips the toolchain check for exactly this reason (#66).
10. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** A
    stopped arm's reading is citable at its `reached_iteration` and nowhere past
    it (§9.143).

## §3 Standing directives and approvals

- **No approval stands. Every approval is SPENT.** No multi-hour run without a
  fresh stated-cost approval, quoted as a RANGE from `arm_cost.py` after an
  unprofiled probe.
- **25 % runs only** (user directive, 1 September 2026).
- **One arm at a time**; never recompile `.tools/classes` under one.
- **No launch while an open issue lacks `awaiting-run`** (GOAL requirement 10;
  `issue_gate.py` enforces it).
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is bannered and pointed past.
