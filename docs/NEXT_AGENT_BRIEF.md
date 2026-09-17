# Brief for the next agent

**Written:** 17 September 2026 (fifty-fourth session) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `fd0674c` plus this handoff's commits
*A pointer, not a source: [`GOAL.md`](GOAL.md), the board ([`STATUS.md`](STATUS.md)) and the position pages win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **NO ARM IS RUNNING; THE MACHINE IS IDLE.** The newest run `20260916T063903_250it_25pct` (the scoring pair, D7) is `completed`, `_run.json` `ran_to_last_iteration` at 250, 25.77 h. It is the fourth RESULT of F35 and moved nothing against arm 0 (§9.177). | `python src/run/session_gate.py --digest` · `python src/run/watch_run.py --run 20260916T063903_250it_25pct` · `python src/analyse/compare_runs.py 20260912T202242_300it_25pct 20260916T063903_250it_25pct --modes` |
| **The machine being idle, `.tools/classes` MAY be recompiled now** — the Java fold (lane task 2) is the first thing to do before any rebuild. The committed controler has NOT been rebuilt since the gate last compiled it under no arm; the next `session_gate.py` run compiles it. | `python src/setup/bootstrap_toolchain.py --verify` · `python src/run/session_gate.py` |
| **NO APPROVAL STANDS.** The 16 September approval (one probe + one arm ≤ 35 h) was SPENT on `20260916T053153_4it_25pct` and `20260916T063903_250it_25pct`. The next arm quotes 25.1 h for 250 it at 25 % (spread 24.5–32.8 h) on the scoring pair's stopwatch — but the roots rebuild changes the plans, so its arm 0 needs its OWN 25 % probe first. | `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25` |
| **NO DECISION IS OPEN.** D6–D12 were taken on 16 September (detach by default; the scoring pair; the TPA ferry target; bike's distance cost derived from the observed mean, swept on its spread; the gate's scoped departure documented; the strict status-check policy; escort members and joint companions held to ride). | `python src/analyse/lane.py --ask` |
| **19 REPORT RECOMMENDATIONS ARE OPEN** (report #12's 2, 7, 8, 9, 12, 14, 15, 18, 19, 20 and report #11's carried rows); nine of #12's twenty were taken this session (§9.177). | `python src/analyse/report_recs.py` |
| The issue ledger: **32 open, 0 blocking**; #172 reads `MEASUREMENT DUE` because the scoring pair has run — its comment carries the reading (§9.177). Filed this session: #227–#232. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch `praneetdhoolia/eleventh-report-scoring-pair` is deleted when it is. | `gh pr list --state open` |
| Registry **567** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **547 passed, 1 skipped**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |
| The three F35 results' record files (`_fit.json`, `_summary.json`, `_bound_trips.json`, `_near_wharf.json`, `_mode_by_demographics.json`, `_residents.csv.gz`) are mirrored under `results/processed/<run>/`; each reader is one command on any run. | `python src/analyse/measure_bound_trips.py --run <run> --it 250` · `python src/analyse/measure_near_wharf.py --run <run> --it 250` · `python src/analyse/mode_by_demographics.py results/raw/<run>` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** **(recommended)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D8 = Re-derive the ferry target from the disclosed TPA tap-on series (recommended) (2026-09-16) · D9 = A literature marginal utility of distance for bike, with its sweep (recommended) (2026-09-16) · D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16) · D12 = Hold escort members and joint companions to ride on their bound tours; car-less lift and shared passengers keep walk/bike/pt (recommended) (2026-09-16)
<!-- generated:lane end -->

Do the Java fold (task 2) FIRST — the machine is idle and it is one recompile — then the roots rebuild
(task 1): D12's hold lives half in the plans builder and half in `GatedSubtourModeChoice`, so the rebuild
is not whole without the Java. The rebuild opens a family: a 25 % probe on the rebuilt inputs prices its
arm 0, which ships with `RUN.replanning.score_msa_representation` = `absent` (the scoring pair settled it,
§9.177). The patch scripts this session prepared for F1–F5 and E1–E2 lived in a session scratchpad and are
GONE; §9.177 and the lane state what each does, and the position pages carry the values to derive.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A BUILD OR A TEST SUITE UNDER AN ARM STRETCHES ITS ITERATIONS** (§9.177): the scoring pair ran 400–510 s
   an iteration under this session's verification rebuilds against 383 s on the idle probe; batch them, run
   them at below-normal priority, and never read a pace taken under them as the arm's price.
2. **MATSim'S MODE-CHOICE COVERAGE IS A SHARE OF TRIPS, NOT AGENTS** (§9.177): §9.163 and §9.169 read it as
   agents and concluded ride's target was above its ceiling; the ceiling IS the bound trips' share (20.62 %),
   sitting at the target. Read `report_choice_set_coverage.py`'s wording, not the older record text.
3. **THE CUTOFF SNAP IS SELECTION, NOT SCORING** (§9.177): score averaging from the cutoff left the 200→201
   snap at car +1.76 pp (arm 0 +1.683, routers pair +1.774). Do not propose MSA, a longer tail or a scoring
   tweak against it again.
4. **A SESSION SCRATCHPAD DOES NOT SURVIVE THE SESSION**: seven prepared patch scripts (F1–F5, E1, E2) were
   held there for the arm to end, and it ended after the handoff began. Prepared work goes on the branch as
   a commit that changes nothing yet, or into the record — never into the scratchpad alone.
5. **`extract_loop_body.py` REWRITES BY LINE NUMBER** (§9.177): extracting stages top-down shifted every
   later range and broke `config_runtime` for explicit signals, caught only by the hardcoding probe; extract
   bottom-up, and verify every stage by a byte-identical rebuild of the artefact.
6. **AN IMPORT SWEEP EXECUTES MODULE-LEVEL WORK** (§9.177, #232): `test_import_sweep.py` once imported nine
   extract adapters that fetch and write at import — provenance dates rewritten, a gpkg regenerated; the
   sweep now compiles them, and the adapters are #232's to fix.
7. **`&&`-CHAINED CHECKS WITH `| tail -1` RETURN THE TAIL'S EXIT CODE** (§9.177): three commits landed red
   that way and needed follow-ups; run each check on its own line and read its last line.
8. **THE PRICER BOOKS A DEAD HARNESS'S MISSING ITERATIONS AS SETUP** (§9.177, fixed): `wall − Σmemo` quoted
   48.8 h with 22.8 h of setup on the orphaned pair; `setup_seconds()` now reads the JVM's stopwatch when the
   memo is short. If a quote's setup exceeds an hour, read the stopwatch before believing it.
9. **A GAME ON THE ARM'S MACHINE IS PART OF THE ARM'S PRICE** (§9.176, §9.174): iterations ran 405–561 s
   against ~350 while another process shared the CPU; the tail absorbed it.
10. **THE LAUNCHER'S VIEWER IS FROZEN AT LAUNCH** (§9.175): 8731 is served from inside the harness with the
    `run_view.py` it imported; edit on 8732 with `--reload`.

Retired because a gate or the launcher enforces them: a harness that dies with its shell (`run.py` detaches
by default, D6, §9.177); a finished orphan marked `failed` by the reconcile (`reconcile_stale` reads the clean
shutdown first, §9.177); a run's residents resolved through today's population (`_residents.csv.gz`, #213);
an `awaiting-run` issue whose run has run going unread (`issue_gate.py` prints `MEASUREMENT DUE`, §9.177); a
JVM alive under a dead harness (`run_failure.py --check`, §9.176); a run name on a position page's intro
(`intro_no_run_names`, §9.176); a concurrent arm (the launcher, §9.170); a launch with no automatic stop
(§9.163); a red CI run merging (the ruleset, §9.172); a coordinate typed into a script (`check_hardcoding.py`);
a report per session (one per reading, `report_recs.py`); a decision asked twice (`lane.json`).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's 44 h was SPENT on `20260912T202242_300it_25pct` (§9.169); the routers
  pair's 30.0 h on `20260915T000704_250it_25pct` (§9.176); the scoring pair's 33.0 h on
  `20260916T063903_250it_25pct` (§9.177). A further arm needs its own stated cost set as
  `RUN.gate.wall_ceiling_h` on its overlay, quoted from a 25 % probe on the build it will run.
- **Never compare across a family boundary.** F35 opened at `20260912T184108` (§9.168); arm 0, the routers
  pair and the scoring pair are its results, each pair read against arm 0 inside F35 (D4, §9.175). The roots
  rebuild OPENS A FAMILY: nothing before it compares with anything after. A run is a result only if `_run.json`
  says `ran_to_last_iteration`; a stopped arm is citable at its `reached_iteration`; a FAILED arm for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural smoke probe may run at 1 %.
- **One arm at a time**; never recompile `.tools/classes` under one. A launch detaches by default
  (`--foreground` opts out).
- **A launch with no automatic stop is refused**; so is one whose heap is below the registry's rule and one
  whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement** (GOAL requirement 10);
  `AWAITING-DECISION:` reports, never blocks. Declare `answers_issues`.
- **The user's decisions of 16 September are settled** (D6–D12, `lane.json`, §14): do not re-ask them; the
  ferry target's re-derivation (D8) is a target change and gets its own record section when it lands.
- **The TfNSW request is the user's to send** (D2, §9.172): do not re-search, do not send unasked.
- **#30 is allocation, not the kernel** (user decision, §9.177): no new short-trip kernel is proposed.
- **The simulator's documents live at `docs/`, the city's at `cities/<city>/docs/`** (§9.171); a position
  page is at most 130 lines and 14,000 bytes; the lane is edited in `lane.json`; a decision is asked once.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — FROZEN.
- **Nothing may be tuned on arm 0** until the separation of #172 has run (§9.159); two of five controls
  have run and moved nothing (§9.176, §9.177); the rebuild goes at the demand first.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position page with a §14 row.
