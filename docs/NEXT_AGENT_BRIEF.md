# Brief for the next agent

**Written:** 15 September 2026, fifty-first session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** the merge of the branch `praneetdhoolia/routers-pair-arm` (`git log -1 origin/main`).
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md), [the lane](lane.json) and
the [position pages](positions) win wherever this disagrees with them.*

**AN ARM IS RUNNING: THE ROUTERS PAIR.** `20260915T000704_250it_25pct` launched at 00:07 on
15 September on `f35_routers_mode_constant_25pct` (`C.raptor.mode_cost_representation` =
`mode_constant`, 250 iterations, 25 %, 48g) on a 30.0 h approval, now SPENT (§9.174). Its
recurring iterations run 427–568 s against the 422 s price, so the 30.0 h ceiling lands between
iteration ~215 and the horizon; the user chose to let it run. A ceiling stop is citable at its
`reached_iteration` and is NOT a result. Your lane is its READING, at its end. Do not recompile
`.tools/classes`, do not launch a second arm, and keep the browser off this machine's CPU: with
one open, the arm's iterations ran 20 % slower (§9.174).

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **THE ARM IS RUNNING** (or has ended): `20260915T000704_250it_25pct`, iteration 15 of 250 at handoff, 427–568 s an iteration, ceiling 30.0 h. Its end writes `_run.json` with `completion` `ran_to_last_iteration` (a result) or `stopped_at_ceiling` (a reading at `reached_iteration`). | `python src/run/session_gate.py --digest` · `Get-Process java` · `python src/analyse/report_mode_ridership.py --run 20260915T000704_250it_25pct --trend` |
| **NO APPROVAL STANDS.** The 30.0 h was spent on this launch. A second approval, if the ceiling stopped the arm short and the user wants the horizon, is a new stated cost. | `python src/analyse/arm_cost.py --run-config f35_routers_mode_constant_25pct --iterations 250` |
| **ONE DECISION IS OPEN: D4** — does a one-field control open a family, or is it read against arm 0 inside F35? `/onboard` asks it. | `python src/analyse/lane.py --ask` |
| **ELEVEN REPORT RECOMMENDATIONS ARE OPEN** of the tenth report's twenty; #3 (the routers pair) was taken this session. | `python src/analyse/report_recs.py` |
| The issue ledger: 27 open, 13 `awaiting-run` with a measurement, the rest `AWAITING-DECISION:`, 0 blocking; none closed this session. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **558** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **484**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |
| The viewer serves a run at `python src/analyse/run_view.py --run <run> --port 8731`; its endpoints are `status.json`, `modes.json`, `hotspot.json[?meta=1]`, `traffic.geojson`, `network.bin`, `basemap.bin` (§9.174). | `curl -s -o /dev/null -w "%{time_total}" http://127.0.0.1:8731/status.json` |

Then: `python src/run/session_gate.py`. While the arm runs the toolchain step is skipped; it
compiles `.tools/classes` only on an idle machine.

## §1 The lane

<!-- generated:lane start -->
1. **Read the routers pair: `20260915T000704_250it_25pct` against arm 0, all twelve modes with choice-set coverage on both sides** **(recommended)** - no run: `report_mode_ridership.py --run 20260915T000704_250it_25pct --it <reached>` and `report_choice_set_coverage.py`, then the fit pipeline; the arm itself is running on a spent 30.0 h approval (iterations 2-14 at 427-568 s against the 422 s price); no family boundary; blocked on: the arm's end - the 250 horizon, or the 30.0 h ceiling projected near iteration 215 (a stop there is citable at its reached_iteration, not a result; the pair's verdict may then need the horizon re-declared or a second approval) (§9.174: launched, pace measured; §9.169: the pairs difference against arm 0's it.300 reading; #98 #94 #49 #172 #174)
2. **The roots first: one demand rebuild that seeds ride at the HTS share (#86), gives destination placement an observed short-trip shape (#30), gives bike a distance cost (#107) and consumes the household-size top-band mean (#196)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at the same price as above; opens a family; blocked on: D1 chose the routers pair first (§9.172); the rebuild follows the pair's reading, or a new decision to take the roots before it (§9.169: ride's 20.60 % target sits above its 19.11 % coverage, fixed at the seed; walk trips average 3.74 km against 0.70; bike carries no distance cost; #86 #30 #107 #196 #145)
3. **The eleventh project report, after the next reading** - one /project-report pass; no family boundary; blocked on: the next reading - a pair arm's gate or horizon (§9.166: one report per reading) (docs/reports/README.md;)
4. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: held by the user until the first pair has run (§9.159) (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D4.** Does a one-field control arm (the routers pair, and the four pairs after it) open a comparability family, or is it read against arm 0 inside F35? Options: Inside F35, read against arm 0 (recommended) · Each control opens a family (§9.174: the lane's pair task carried opens_family: true while §9.169 reads the pairs within F35; #172 #174)

Decided: D1 = Routers pair first (recommended) (2026-09-14) · D2 = Search first, online and via the TfNSW API (2026-09-14) · D3 = Require them (recommended) (2026-09-14)
<!-- generated:lane end -->

When the arm ends, read it with coverage on BOTH sides (§9.163) and difference against arm 0's
it.300 reading inside F35 unless D4 says otherwise; then the eleventh report (one per reading).

## §2 Traps — newest first, each with what it cost

1. **A MASK OR FILTER ON AN ANCESTOR MAKES IT THE BACKDROP ROOT** (§9.174): the panel's fade
   mask made every card's glass blur the panel's empty box instead of the map — an invisible
   blur nobody could name until it was measured. A fade lives on each card, in the panel's
   coordinates; `clip-path` does not do this, a mask does.
2. **A BROWSER ON THE ARM'S MACHINE IS PART OF THE ARM'S PRICE** (§9.174): iterations ran
   505–568 s with a scratch Edge open and 427 s once it closed, against a 422 s price; the
   ceiling was set with 0.5 h of room and now lands short of the horizon.
3. **THE CEILING IS HELD IN THE LAUNCHER'S MEMORY** (§9.174): it cannot be raised on a running
   arm by design. Price the milestone iterations a four-iteration probe never meets before
   setting it, or accept a reading short of the horizon.
4. **A SERVER THAT READS THE REGISTRY PER POLL** (§9.174): `summarise_run.relaxation()`
   resolved and validated the whole registry twice on every status poll - 0.585 s of a 0.628 s
   scan, polled every 0.5 s. Pass the declared values in; profile with `cProfile` before
   guessing where a poll goes.
5. **A HIDDEN BROWSER TAB NEVER FIRES `requestAnimationFrame`, AND A WEBGL MAP NEVER FINISHES
   LOADING IN IT** (§9.173): launch the scratch Edge with occlusion backgrounding off
   (`--disable-backgrounding-occluded-windows --disable-renderer-backgrounding
   --disable-features=CalculateNativeWinOcclusion,msEdgeSleepingTabs`) onto the viewer's URL.
6. **A TILE PROVIDER CAN TURN ITS FREE TILES INTO A WATERMARK** (§9.172): CARTO prints "API KEY
   REQUIRED"; every provider is checked in the browser, not by its documentation.
7. **A DOCUMENT CAN CITE A RECORD SECTION BEFORE IT EXISTS** — a gate (`check_doc_shape.py`);
   write the section first.
8. **A SWEPT VALUE WITH A TYPED TWIN IS A SWEEP THAT MOVES NOTHING** (§9.170, #212): the
   hardcoding ledger skips ALL-CAPS assignments and `dict(...)` keywords.
9. **A READER THAT RESOLVES THROUGH THE CITY'S ARTEFACT READS TODAY'S BUILD, NOT THE RUN'S**
   (§9.169, #213): `home_lga()` still does it for residents.
10. **A PRICE FROM ANOTHER BUILD IS NOT A PRICE** (§9.168): the digest's PRICE line says so.

Retired because a gate or the launcher enforces them: a concurrent arm (the launcher, §9.170),
a result living only in `raw/` (`session_gate.py --handoff`), a launch with no automatic stop
(§9.163), a red CI run merging (the ruleset, §9.172), a coordinate typed into a script
(`check_hardcoding.py`, category 9), a move that leaves links behind (`check_doc_links.py`),
a menu clipped by a masked scroll panel (the pickers live at the document body, §9.172), a
report per session (one per reading, `report_recs.py`, §9.166).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's 44 h was SPENT on `20260912T202242_300it_25pct`; the pair's
  30.0 h was SPENT on `20260915T000704_250it_25pct` (§9.174). A further arm needs its own
  stated cost set as `RUN.gate.wall_ceiling_h` on its overlay.
- **Never compare across a family boundary.** F35 opened at `20260912T184108` (§9.168); arm 0
  is its reading; the pair is read against it inside F35 unless D4 decides otherwise. A run is a
  result only if `_run.json` says `ran_to_last_iteration`; a stopped arm is citable at its
  `reached_iteration`; a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural smoke probe may
  run at 1 %, says so, and is read for nothing.
- **One arm at a time**; never recompile `.tools/classes` under one.
- **A launch with no automatic stop is refused**; so is one whose heap is below the registry's
  rule and one whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement** (GOAL
  requirement 10); `AWAITING-DECISION:` reports, never blocks. Declare `answers_issues`.
- **The TfNSW request is the user's to send** (D2, §9.172): do not re-search, do not send unasked.
- **The viewer is checked in a browser by measurement before it is done** (§9.172–§9.174):
  `node --check` the script, zero console errors, both themes, 420 px, frame gaps through a
  zoom, and for a data change the fetch timings and the main thread's long tasks.
- **The viewer's tile, terrain and building providers are the reader's browser's** (§9.173,
  §9.174): Esri, AWS Terrarium, Overture PMTiles; nothing they serve enters the package.
- **The simulator's documents live at `docs/`, the city's at `cities/<city>/docs/`**
  (§9.171); a position page is at most 130 lines and 14,000 bytes; the lane is edited in
  `lane.json`, never in the board; a decision is asked once (§9.171).
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — FROZEN.
- **Nothing may be tuned on arm 0** until the separation of #172 has run (§9.159).
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position page with a §14
  row, never by editing the dated section.
