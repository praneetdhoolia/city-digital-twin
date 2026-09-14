# Brief for the next agent

**Written:** 14 September 2026, forty-ninth session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** the merge of the branch `praneetdhoolia/viewer-map-app-layout-and-pair-priced` (`git log -1 origin/main`).
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md), [the lane](lane.json) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS THE ROUTERS PAIR, CHOSEN AND PRICED, WAITING ON AN APPROVAL.**
Nothing ran this session but one 25 % pricing probe. Arm 0 of F35
(`20260912T202242_300it_25pct`, 300 of 300, a RESULT) is the newest reading:
**2 of 12 inside 10 %** (car +9.6 %, motorbike −5.6 %), six past the stop bar.
The session took the three decisions the ledger held (D1 routers pair first, D2
search first, D3 require the status checks), applied D3 to the ruleset, priced
the pair on the committed controler, searched every public channel for the four
HTS cells and found them on none, and rebuilt the run viewer in a map-app layout
(§9.172). Asked for the pair's stated-cost approval, the user chose the
handoff instead: **no approval stands.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **MACHINE IDLE, NO ARM RUNNING.** The newest run on disk is the 25 % pricing probe `20260914T195207_4it_25pct` (4 of 4, read for its clock and heap only); the newest reading is arm 0. | `python src/run/session_gate.py --digest` · `Get-Process java` |
| **NO APPROVAL STANDS.** The pair is priced on the build it would run: 30.0 h at 250 iterations plus 32 min of setup, 422.0 s a recurring iteration, spread 18.2–39.2 h. An approval is a number set as `RUN.gate.wall_ceiling_h` on the pair's overlay, which is not yet written. | `python src/analyse/arm_cost.py --run-config f35_baseline_25pct --iterations 250` |
| **NO DECISION IS OPEN.** D1, D2 and D3 are answered in the ledger; `/onboard` asks nothing. | `python src/analyse/lane.py --ask` |
| **TWELVE REPORT RECOMMENDATIONS ARE OPEN** of the tenth report's twenty (recommendation 5, the ruleset, taken this session). | `python src/analyse/report_recs.py` |
| **THE MAIN RULESET REQUIRES THE NINE `test` JOBS** (21121872): a red CI run cannot merge. | `gh api repos/praneetdhoolia/city-digital-twin/rulesets/21121872 --jq '.rules[].type'` |
| The issue ledger: 28 open before this session's actions — #202 CLOSES here, #220 (the viewer's typed initial centre) is FILED; 13 `awaiting-run` with a measurement, the rest `AWAITING-DECISION:`, 0 blocking. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **558** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **484**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |

Then: `python src/run/session_gate.py`. The machine is idle, so the toolchain
step compiles `.tools/classes`; one arm at a time means it never runs under an arm.

## §1 The lane

<!-- generated:lane start -->
1. **The first pair arm: the routers control (`C.raptor.mode_cost_representation` = `mode_constant`) against arm 0** **(recommended)** - 30.0 h at 250 iterations, 25 % plus 32 min of setup, priced on the committed controler (`20260914T195207_4it_25pct`, 422.0 s a recurring iteration; spread 18.2-39.2 h over the last five arms); opens a family; blocked on: a stated-cost approval set as RUN.gate.wall_ceiling_h; the overlay `f35_routers_mode_constant_25pct` (C.raptor.mode_cost_representation = mode_constant, 250 it, answers_issues #98 #94 #49 #172 #174) is written at launch (§9.169; the tenth report's factor ledger names router-scorer consistency the top mover: light rail -73.9 %, heavy rail +54.6 %, ferry -63.3 % are decided in the raptor and no control has run; §9.172: D1 taken, the pair priced; #98 #94 #49 #172 #174)
2. **The roots first: one demand rebuild that seeds ride at the HTS share (#86), gives destination placement an observed short-trip shape (#30), gives bike a distance cost (#107) and consumes the household-size top-band mean (#196)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at the same price as above; opens a family; blocked on: D1 chose the routers pair first (§9.172); the rebuild follows the pair's reading, or a new decision to take the roots before it (§9.169: ride's 20.60 % target sits above its 19.11 % coverage, fixed at the seed; walk trips average 3.74 km against 0.70; bike carries no distance cost; #86 #30 #107 #196 #145)
3. **The eleventh project report, after the next reading** - one /project-report pass; no family boundary; blocked on: the next reading - a pair arm's gate or horizon (§9.166: one report per reading) (docs/reports/README.md;)
4. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: held by the user until the first pair has run (§9.159) (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D1 = Routers pair first (recommended) (2026-09-14) · D2 = Search first, online and via the TfNSW API (2026-09-14) · D3 = Require them (recommended) (2026-09-14)
<!-- generated:lane end -->

The pair's overlay does not exist yet: write `f35_routers_mode_constant_25pct`
on `f35_baseline_25pct`'s justification (`C.raptor.mode_cost_representation` =
`mode_constant`, `RUN.controler.last_iteration` 250, the approved hours as
`RUN.gate.wall_ceiling_h`, `answers_issues` #98 #94 #49 #172 #174), dry-run it,
then launch `--detach` and `verify_launch.py`. Read coverage on BOTH arms of the
pair (§9.163); the price already sits on the committed controler, so no probe
comes first unless the Java changes again.

## §2 Traps — newest first, each with what it cost

1. **A TILE PROVIDER CAN TURN ITS FREE TILES INTO A WATERMARK** (§9.172): CARTO's
   basemaps now print "API KEY REQUIRED" across every tile; the viewer's street
   base is Esri's label-free canvas. Check a new provider in the browser, not by
   its documentation.
2. **A MENU INSIDE A MASKED SCROLL PANEL IS CLIPPED BY THE MASK** (§9.172): the
   viewer's pickers live at the document body, positioned from their button.
3. **A DOCUMENT CAN CITE A RECORD SECTION BEFORE IT EXISTS** — a gate
   (`check_doc_shape.py`, citations); write the section first.
4. **A SWEPT VALUE WITH A TYPED TWIN IS A SWEEP THAT MOVES NOTHING** (§9.170,
   #212): the hardcoding ledger skips ALL-CAPS assignments and `dict(...)` keywords.
5. **A READER THAT RESOLVES THROUGH THE CITY'S ARTEFACT READS TODAY'S BUILD,
   NOT THE RUN'S** (§9.169, #213): `home_lga()` still does it for residents.
6. **A PRICE FROM ANOTHER BUILD IS NOT A PRICE** (§9.168): the digest's PRICE
   line says so. This session's price IS on the committed build.
7. **A REPORT PER SESSION REPEATS ITSELF** (§9.166): one per reading.
8. **A MOVE RETARGETED BY HAND LEAVES LINES BEHIND** (§9.171): `check_doc_links.py`
   is a gate.

Retired because a gate or the launcher enforces them: a concurrent arm (the
launcher, §9.170), a result living only in `raw/` (`session_gate.py --handoff`),
a launch with no automatic stop (§9.163), a red CI run merging (the ruleset, §9.172).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's 44 h was SPENT on `20260912T202242_300it_25pct`.
  The pair arm needs its own, on the 30.0 h quote of `20260914T195207_4it_25pct`,
  set as `RUN.gate.wall_ceiling_h`; the user declined to give one this session.
- **Never compare across a family boundary.** F35 opened at `20260912T184108`
  (§9.168); arm 0 is its reading; the pair opens a family. A run is a result only
  if `_run.json` says `ran_to_last_iteration`; a stopped arm is citable at its
  `reached_iteration`; a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a structural
  smoke probe may run at 1 %, says so, and is read for nothing.
- **One arm at a time**; never recompile `.tools/classes` under one.
- **A launch with no automatic stop is refused**; so is one whose heap is below
  the registry's rule and one whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated measurement**
  (GOAL requirement 10); `AWAITING-DECISION:` reports, never blocks. Declare
  `answers_issues` on a new overlay.
- **The TfNSW request is the user's to send** (D2, §9.172): the search is done and
  recorded on the draft; do not re-search, do not send unasked.
- **The simulator's documents live at `docs/`, the city's at `cities/<city>/docs/`**
  (§9.171); a position page is at most 130 lines and 14,000 bytes; the lane is
  edited in `lane.json`, never in the board; a decision is asked once (§9.171).
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** — FROZEN.
- **Nothing may be tuned on arm 0** until the separation of #172 has run (§9.159).
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
