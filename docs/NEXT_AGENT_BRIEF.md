# Brief for the next agent

**Written:** 15 September 2026, fifty-second session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** the merge of the branch `praneetdhoolia/viewer-layers-labels-congestion` (`git log -1 origin/main`).
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md), [the lane](lane.json) and
the [position pages](positions) win wherever this disagrees with them.*

**AN ARM IS RUNNING: THE ROUTERS PAIR.** `20260915T000704_250it_25pct` launched at 00:07 on
15 September on `f35_routers_mode_constant_25pct` (`C.raptor.mode_cost_representation` =
`mode_constant`, 250 iterations, 25 %, 48g) on a 30.0 h approval, now SPENT (§9.174). At handoff it
was at iteration 34, iterations 30–33 at 423–467 s against the 422 s price, so the 30.0 h ceiling lands
between iteration ~215 and the horizon; the user chose to let it run. A ceiling stop is citable at its
`reached_iteration` and is NOT a result. Your lane is its READING, at its end, against arm 0 INSIDE F35
(D4, §9.175). Do not recompile `.tools/classes`, do not launch a second arm, and keep the browser off
this machine's CPU while it runs (§9.174).

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE ARM IS RUNNING** (or has ended): `20260915T000704_250it_25pct`, iteration 34 of 250 at handoff, ceiling 30.0 h. Its end writes `_run.json` with `completion` `ran_to_last_iteration` (a result) or `stopped_at_ceiling` (a reading at `reached_iteration`). | `python src/run/session_gate.py --digest` · `Get-Process java` · `python src/analyse/report_mode_ridership.py --run 20260915T000704_250it_25pct --trend` |
| **`.tools/classes` IS STALE against `src/java`**: `RunTelemetry.java` changed this session (§9.175) and was compiled only into a scratch directory. The next `bootstrap_toolchain.py` on an idle machine rebuilds it; the gate's toolchain step does this itself once no arm runs. | `python src/run/session_gate.py` (its `toolchain` line, once the arm has ended) |
| **NO APPROVAL STANDS.** The 30.0 h was spent on this launch. | `python src/analyse/arm_cost.py --run-config f35_routers_mode_constant_25pct --iterations 250` |
| **NO DECISION IS OPEN.** D4 was taken this session: a one-field control is read against arm 0 inside F35. | `python src/analyse/lane.py --ask` |
| **ELEVEN REPORT RECOMMENDATIONS ARE OPEN** of the tenth report's twenty; none taken this session. | `python src/analyse/report_recs.py` |
| The issue ledger: 27 open, 0 blocking; #172's waiting line now names the pair's reading. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **558** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **488**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |
| The viewer on the arm's own port 8731 serves the `run_view.py` the launcher imported at 00:07 - THREE COMMITS OLD until the arm ends. Edit and verify the viewer on a standalone server: `python src/analyse/run_view.py --run <run> --port 8732 --reload` (§9.175). | `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8731/basemap.bin` (404 there, 200 on 8732) |

Then: `python src/run/session_gate.py`. While the arm runs the toolchain step is skipped; it
compiles `.tools/classes` only on an idle machine.

## §1 The lane

<!-- generated:lane start -->
1. **Read the routers pair: `20260915T000704_250it_25pct` against arm 0, all twelve modes with choice-set coverage on both sides** **(recommended)** - no run: `report_mode_ridership.py --run 20260915T000704_250it_25pct --it <reached>` and `report_choice_set_coverage.py`, then the fit pipeline; the arm itself is running on a spent 30.0 h approval (iterations 30-33 at 423-467 s against the 422 s price); no family boundary; blocked on: the arm's end - the 250 horizon, or the 30.0 h ceiling projected near iteration 215 (a stop there is citable at its reached_iteration, not a result; the pair's verdict may then need the horizon re-declared or a second approval) (§9.174: launched, pace measured; §9.169: the pairs difference against arm 0's it.300 reading; §9.175: D4 - read inside F35, no family flag; #98 #94 #49 #172 #174)
2. **The roots first: one demand rebuild that seeds ride at the HTS share (#86), gives destination placement an observed short-trip shape (#30), gives bike a distance cost (#107) and consumes the household-size top-band mean (#196)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at the same price as above; opens a family; blocked on: D1 chose the routers pair first (§9.172); the rebuild follows the pair's reading, or a new decision to take the roots before it (§9.169: ride's 20.60 % target sits above its 19.11 % coverage, fixed at the seed; walk trips average 3.74 km against 0.70; bike carries no distance cost; #86 #30 #107 #196 #145)
3. **The eleventh project report, after the next reading** - one /project-report pass; no family boundary; blocked on: the next reading - a pair arm's gate or horizon (§9.166: one report per reading) (docs/reports/README.md;)
4. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: held by the user until the first pair has run (§9.159) (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D1 = Routers pair first (recommended) (2026-09-14) · D2 = Search first, online and via the TfNSW API (2026-09-14) · D3 = Require them (recommended) (2026-09-14) · D4 = Inside F35, read against arm 0 (recommended) (2026-09-15)
<!-- generated:lane end -->

When the arm ends, read it with coverage on BOTH sides (§9.163) and difference against arm 0's
it.300 reading inside F35 (D4); then the eleventh report (one per reading, §9.166). The congestion
picture of that reading is the viewer's new measure (§9.175): the arm's own payload carries the
old row shape and is corrected server-side; a payload with `"statistic": "median"` is the
telemetry's own, and the two are not compared.

## §2 Traps — newest first, each with what it cost

1. **THE LAUNCHER'S VIEWER IS FROZEN AT LAUNCH** (§9.175): 8731 is served from inside the arm's own
   process, which holds the `run_view.py` it imported; the page it served was newer and asked for
   endpoints the server lacked - "no layers", reported as a viewer bug. The server now reads its
   page once at start; edit on 8732 with `--reload`.
2. **A PROMISED OPACITY IS AN APPLIED ONE** (§9.175): `will-change: opacity` on the sidebar made
   it a backdrop root, so every card's glass blurred an empty box - the §9.174 mask trap in a
   second dress. Promise `transform` only.
3. **THE TERRAIN'S TEXTURE CACHE OUTLIVES A PAINT CHANGE** (§9.175): with terrain on, a retheme
   reached only tiles drawn after it; `map.terrain.tileManager.freeRtt()` then `triggerRepaint()`.
   And anything `build()` calls before `ready` that checks `ready` is a no-op - `setBase` was.
4. **A TRANSFORM CAN SUMMON A SCROLLBAR** (§9.175): a card turning toward the reader projected
   15 px sideways, `overflow-y: auto` gave the panel a horizontal bar, its height fell 15 px and
   the last card sat under a fade. `overflow-x: hidden`; fold AWAY (`rotateX(+90deg)`).
5. **AN EMPTY `catch` HID A ONE-BYTE ALIGNMENT** (§9.175): `basemap.bin`'s header length varied
   with a float's printed digits; an odd offset threw in `Uint32Array` and the map lost its ground.
   Pad binary headers to four bytes; never swallow.
6. **THE QSIM'S SECOND IS NOT DELAY** (§9.175): a 0.7 s turn stub with 1 s of step read as a ratio
   of 2.4, and 35 % of a city's links were "stopped". Measure delay past the step over a map app's
   segment, on road vehicles, on the median traversal.
7. **A MASK OR FILTER ON AN ANCESTOR MAKES IT THE BACKDROP ROOT** (§9.174): a fade lives on each
   card, in the panel's coordinates; `clip-path` does not do this, a mask does.
8. **A BROWSER ON THE ARM'S MACHINE IS PART OF THE ARM'S PRICE** (§9.174): iterations ran
   505–568 s with a scratch Edge open and 427 s once it closed.
9. **THE CEILING IS HELD IN THE LAUNCHER'S MEMORY** (§9.174): it cannot be raised on a running arm.
10. **A HIDDEN BROWSER TAB NEVER FIRES `requestAnimationFrame`** (§9.173): launch the scratch Edge
    with occlusion backgrounding off, onto the viewer's URL.

Retired because a gate or the launcher enforces them: a concurrent arm (the launcher, §9.170),
a result living only in `raw/` (`session_gate.py --handoff`), a launch with no automatic stop
(§9.163), a red CI run merging (the ruleset, §9.172), a coordinate typed into a script
(`check_hardcoding.py`, category 9), a move that leaves links behind (`check_doc_links.py`),
a server that reads the registry per poll (memoised by stamp, §9.174), a report per session
(one per reading, `report_recs.py`, §9.166).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's 44 h was SPENT on `20260912T202242_300it_25pct`; the pair's
  30.0 h was SPENT on `20260915T000704_250it_25pct` (§9.174). A further arm needs its own
  stated cost set as `RUN.gate.wall_ceiling_h` on its overlay.
- **Never compare across a family boundary.** F35 opened at `20260912T184108` (§9.168); arm 0
  is its reading; the pair is read against it inside F35 (D4, §9.175). A run is a result only if
  `_run.json` says `ran_to_last_iteration`; a stopped arm is citable at its `reached_iteration`;
  a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural smoke probe may
  run at 1 %, says so, and is read for nothing.
- **One arm at a time**; never recompile `.tools/classes` under one.
- **A launch with no automatic stop is refused**; so is one whose heap is below the registry's
  rule and one whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement** (GOAL
  requirement 10); `AWAITING-DECISION:` reports, never blocks. Declare `answers_issues`.
- **The TfNSW request is the user's to send** (D2, §9.172): do not re-search, do not send unasked.
- **The viewer is checked in a browser by measurement before it is done** (§9.172–§9.175): the
  user works through viewer issues ONE AT A TIME and is asked a clickable choice after each fix;
  `node --check` the script, zero console errors, both themes, and the numbers - computed styles
  and paint values per frame, a pixel clip for a fade - before the probe.
- **The viewer's tile, terrain, building and name providers are the reader's browser's** (§9.173–
  §9.175): Esri imagery, AWS Terrarium, Overture PMTiles, OpenFreeMap names; nothing they serve
  enters the package, with one recorded exception - the three map-type snapshots under the city's
  figures (§9.175). No night imagery exists finer than ~600 m per pixel; none is wired.
- **The simulator's documents live at `docs/`, the city's at `cities/<city>/docs/`**
  (§9.171); a position page is at most 130 lines and 14,000 bytes; the lane is edited in
  `lane.json`, never in the board; a decision is asked once (§9.171).
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — FROZEN.
- **Nothing may be tuned on arm 0** until the separation of #172 has run (§9.159).
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position page with a §14
  row, never by editing the dated section.
