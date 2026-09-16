# Brief for the next agent

**Written:** 16 September 2026, fifty-third session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** the merge of the branch `praneetdhoolia/routers-pair-closeout` (`git log -1 origin/main`).
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md), [the lane](lane.json) and
the [position pages](positions) win wherever this disagrees with them.*

**THE MACHINE IS IDLE.** The routers pair `20260915T000704_250it_25pct` ran all 250 iterations (27.39 h) and is
the third RESULT, closed out through the new `run.py --close-out` after its harness died at iteration 34
(§9.176, D5, #225). Read against arm 0 inside F35 it moved nothing outside one build's noise: 2 of 12 inside,
6 past the bar on both. **Two decisions await the user** — D6 (the launch default) and D7 (what runs next);
`/onboard` asks them. No approval stands. The eleventh report is due (one per reading, §9.166).

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **NO ARM IS RUNNING.** The newest run `20260915T000704_250it_25pct` is `completed`, `_run.json` `ran_to_last_iteration` at 250, `closed_out_by` `run.py --close-out`. | `python src/run/session_gate.py --digest` · `Get-Process java` · `python src/analyse/report_mode_ridership.py --run 20260915T000704_250it_25pct --it 250` |
| **`.tools/classes` was rebuilt by this session's gate** on the idle machine (the toolchain step); the committed build is `3a547df08516` and NO priced arm has run on it — the newest priced controler is `64bf91ada0ef`. A quote needs a 25 % probe on this build first. | `python src/analyse/arm_cost.py --run-config f35_routers_mode_constant_25pct --iterations 250` (its own PRICE warning) |
| **NO APPROVAL STANDS.** The pair's 30.0 h was spent on `20260915T000704_250it_25pct`. | `python src/analyse/arm_cost.py ...` |
| **TWO DECISIONS ARE OPEN**: D6 — detach by default / refuse a foreground launch under a Claude session / leave it (#225); D7 — the roots rebuild / the scoring pair / the bike ASC test. D5 was taken (the orphan is a RESULT). | `python src/analyse/lane.py --ask` |
| **ELEVEN REPORT RECOMMENDATIONS ARE OPEN** of the tenth report's twenty; none taken this session. | `python src/analyse/report_recs.py` |
| The issue ledger: 28 open, 0 blocking; #225 filed this session (`decision-needed`, the harness and the orphan). | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **567** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **508**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |
| The pair's `_fit.json`, `_metrics.json`, `_summary.json` and `modes_final.json` are mirrored under `results/processed/20260915T000704_250it_25pct/`; its reading against arm 0 is one command. | `python src/analyse/compare_runs.py 20260912T202242_300it_25pct 20260915T000704_250it_25pct --modes` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **The roots first: one demand rebuild that seeds ride at the HTS share (#86), gives destination placement an observed short-trip shape (#30), gives bike a distance cost (#107) and consumes the household-size top-band mean (#196)** **(recommended)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at the same price as above; opens a family; blocked on: D7 (the pair's reading is in: the routers change moved nothing past the band, so the roots are next unless the user chooses the scoring pair or the bike test first); the build needs no approval, the new arm 0 a stated cost - ~28 h at 250 iterations from the pair's 362 s median (§9.176) (§9.169: ride's 20.60 % target sits above its 19.11 % coverage, fixed at the seed; walk trips average 3.74 km against 0.70; bike carries no distance cost; §9.176: the routers pair read - pt coverage 15.78 % against 17.53 % on arm 0, light rail -71.0 %, ride -40.8 % at a 19.11 % ceiling on both arms; #86 #30 #107 #196 #145)
2. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D7 = The scoring pair next (2026-09-16) · D8 = Re-derive the ferry target from the disclosed TPA tap-on series (recommended) (2026-09-16) · D9 = A literature marginal utility of distance for bike, with its sweep (recommended) (2026-09-16) · D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16)
<!-- generated:lane end -->

The eleventh report is due now, not after another arm: the pair is the reading (§9.166). Take D7 before
pricing anything; whichever arm it chooses needs a 25 % probe on the committed build for its quote and then
its own stated cost. The roots rebuild opens a family and re-baselines every pair.

## §2 Traps — newest first, at most ten, each with what it cost

1. **THE HARNESS DIES WITH THE SHELL THAT LAUNCHED IT** (§9.176, #225): a foreground `run.py` launch is a child
   of the session; the fifty-second session's end killed the pair's harness at iteration 34 and the JVM ran
   27 h with no ceiling, stall or gate watcher and no record writer. Launch with `--detach` until D6 lands.
2. **`from_log` NAMES A THROWABLE THE RUN SURVIVED** (§9.176): Guice's `Unsupported class file major version 69`
   is in every log; on a run with no other throwable `reconcile_stale()` would mark a finished result `failed`.
   `run.py --close-out` reads the shutdown first; the reconcile does not yet.
3. **A GAME ON THE ARM'S MACHINE IS PART OF THE ARM'S PRICE** (§9.176, §9.174): iterations ran 405–561 s
   against ~350 while `RobloxPlayerBeta` shared the CPU, twice; the tail absorbed it this time.
4. **THE LAUNCHER'S VIEWER IS FROZEN AT LAUNCH** (§9.175): 8731 is served from inside the harness with the
   `run_view.py` it imported; edit on 8732 with `--reload`.
5. **A PROMISED OPACITY IS AN APPLIED ONE** (§9.175): `will-change: opacity` made the sidebar a backdrop root.
6. **THE TERRAIN'S TEXTURE CACHE OUTLIVES A PAINT CHANGE** (§9.175): `freeRtt()` then `triggerRepaint()`.
7. **THE QSIM'S SECOND IS NOT DELAY** (§9.175): measure delay past the step over a map app's segment.
8. **THE CEILING IS HELD IN THE LAUNCHER'S MEMORY** (§9.174): it cannot be raised on a running arm — and it
   dies with the harness.
9. **A HIDDEN BROWSER TAB NEVER FIRES `requestAnimationFrame`** (§9.173): launch the scratch Edge with
   occlusion backgrounding off.
10. **A `--trend` READ GREW WITH THE RUN** (§9.176): ten minutes at 25 readable iterations, paid twenty
    times under the arm; it is memoised per iteration now (`_trend/`), so a warm read is a second — but a
    cold one on a rebuilt reader still re-derives everything: run it in the background under an arm.

Retired because a gate or the launcher enforces them: a JVM alive under a dead harness and a stale
running record under dead pids (`run_failure.py --check` goes red and the digest says `ORPHANED`, §9.176),
a results list on a position page (`intro_no_run_names`, §9.176), a concurrent arm (the launcher, §9.170), a result living only in
`raw/` (`session_gate.py --handoff`), a launch with no automatic stop (§9.163), a red CI run merging (the
ruleset, §9.172), a coordinate typed into a script (`check_hardcoding.py`), a report per session (one per
reading, `report_recs.py`, §9.166), a decision asked twice (`lane.json`, §9.171).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's 44 h was SPENT on `20260912T202242_300it_25pct` (§9.169); the pair's
  30.0 h was SPENT on `20260915T000704_250it_25pct` (§9.174, §9.176). A further arm needs its own stated
  cost set as `RUN.gate.wall_ceiling_h` on its overlay, quoted from a probe on the committed build.
- **Never compare across a family boundary.** F35 opened at `20260912T184108` (§9.168); arm 0 and the pair
  are its readings, the pair read against arm 0 inside F35 (D4, §9.175). A run is a result only if
  `_run.json` says `ran_to_last_iteration`; an orphaned run that reached its horizon is closed out by
  `run.py --close-out` (D5, §9.176); a stopped arm is citable at its `reached_iteration`; a FAILED arm for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural smoke probe may run at 1 %.
- **One arm at a time**; never recompile `.tools/classes` under one. **Launch `--detach`** until D6 lands.
- **A launch with no automatic stop is refused**; so is one whose heap is below the registry's rule and one
  whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement** (GOAL requirement 10);
  `AWAITING-DECISION:` reports, never blocks. Declare `answers_issues`.
- **The TfNSW request is the user's to send** (D2, §9.172): do not re-search, do not send unasked.
- **The viewer is checked in a browser by measurement before it is done** (§9.172–§9.175): one issue at a
  time, a clickable choice after each fix, zero console errors, both themes, the numbers before the probe.
- **The viewer's tile, terrain, building and name providers are the reader's browser's** (§9.173–§9.175);
  nothing they serve enters the package but the three map-type snapshots under the city's figures.
- **The simulator's documents live at `docs/`, the city's at `cities/<city>/docs/`** (§9.171); a position
  page is at most 130 lines and 14,000 bytes; the lane is edited in `lane.json`; a decision is asked once.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — FROZEN.
- **Nothing may be tuned on arm 0** until the separation of #172 has run (§9.159); the routers pair separated
  one of five and moved nothing (§9.176).
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position page with a §14 row.
