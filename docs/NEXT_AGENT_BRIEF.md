# Brief for the next agent

**Written:** 14 September 2026, forty-eighth session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** the merge of the branch `praneetdhoolia/docs-split-and-lane-ledger` (`git log -1 origin/main`).
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md), [the lane](lane.json) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS WHATEVER `docs/lane.json` SAYS, AND ITS FIRST DECISION IS
STILL THE USER'S.** Nothing ran this session. Arm 0 of F35
(`20260912T202242_300it_25pct`, 300 of 300, a RESULT) is the newest reading:
**2 of 12 inside 10 %** (car +9.6 %, motorbike −5.6 %), six past the stop bar.
The session split the documents between the simulator (`docs/`) and the city
(`cities/newcastle/docs/`), made the lane a ledger the board and this brief
render, capped the position pages by bytes, and closed #203 #204 #205 #207 #208
(§9.171). No approval stands.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **MACHINE IDLE, NO ARM RUNNING.** The newest run on disk is the 1 % smoke `20260914T150700_2it_1pct` (read for nothing); the newest reading is arm 0. | `python src/run/session_gate.py --digest` · `Get-Process java` |
| **NO APPROVAL STANDS**, and the price is NOT a price: the controler was recompiled (#197) after arm 0, so the digest's PRICE line says the priced build differs from the committed one until a 25 % probe runs on it. | `python src/analyse/arm_cost.py --run-config f35_baseline_25pct --iterations 250` |
| **THREE DECISIONS ARE UNANSWERED** (D1 which road, D2 the TfNSW request, D3 the ruleset's status checks). `/onboard` asks them as clickable choices; an answer is recorded with `--answer`, never in prose. | `python src/analyse/lane.py --ask` |
| **THIRTEEN REPORT RECOMMENDATIONS ARE OPEN** of the tenth report's twenty; seven are taken with evidence. | `python src/analyse/report_recs.py` |
| **THE DOCUMENTS ARE SPLIT.** `docs/` is the simulator's; `cities/newcastle/docs/` holds the city's front page, `targets.md`, the generated `reference/`, `requests/` and `archived/`. `city.docs()` and `city.city_docs()` resolve them. | `ls docs cities/newcastle/docs` · `python tests/check_doc_links.py --strict` |
| The issue ledger: 33 open - 13 `awaiting-run` with a measurement, 20 with an `AWAITING-DECISION:` line, 0 blocking; #203 #204 #205 #207 #208 CLOSE WHEN THE PR MERGES. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **558** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke), unit tests **484**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |

Then: `python src/run/session_gate.py`. The machine is idle, so the toolchain
step compiles `.tools/classes`; one arm at a time means it never runs under an arm.

## §1 The lane

<!-- generated:lane start -->
1. **The first pair arm: the routers control (`C.raptor.mode_cost_representation` = `mode_constant`) against arm 0** **(recommended)** - ~25.5 h at 250 iterations, 25 % (band 21.7-46.9 h on arm 0's clock); one 25 % probe first because the controler was recompiled (#197); opens a family; blocked on: decision D1, then a stated-cost approval set as RUN.gate.wall_ceiling_h (§9.169; the tenth report's factor ledger names router-scorer consistency the top mover: light rail -73.9 %, heavy rail +54.6 %, ferry -63.3 % are decided in the raptor and no control has run; #98 #94 #49 #172 #174)
2. **The roots first: one demand rebuild that seeds ride at the HTS share (#86), gives destination placement an observed short-trip shape (#30), gives bike a distance cost (#107) and consumes the household-size top-band mean (#196)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at the same price as above; opens a family; blocked on: decision D1 (§9.169: ride's 20.60 % target sits above its 19.11 % coverage, fixed at the seed; walk trips average 3.74 km against 0.70; bike carries no distance cost; #86 #30 #107 #196 #145)
3. **The eleventh project report, after the next reading** - one /project-report pass; no family boundary; blocked on: the next reading - a pair arm's gate or horizon (§9.166: one report per reading) (docs/reports/README.md;)
4. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: held by the user until the first pair has run (§9.159) (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D1.** Which road is next: the first pair arm on arm 0, or the demand rebuild for the roots? Options: Routers pair first (recommended) · Roots rebuild first · Scoring pair first (§9.164, §9.169, the tenth report's factor ledger; #172 #86 #30)
- **D2.** Send the drafted TfNSW bespoke-table request (mode x age, trip length by mode, occupancy by purpose, the unfolded Other)? Options: Send it under the operator's name (recommended) · Hold it (§9.163, §9.167; #50)
- **D3.** Require the nine test-workflow jobs as status checks in the main ruleset (21121872)? Options: Require them (recommended) · Leave the ruleset as it is (the tenth report, recommendation 5; #202)
<!-- generated:lane end -->

Take ONE 25 % probe on the recompiled controler before spending any approval on
a price (§9.168). The operator's decided sequence of 10 September was scoring →
choice set → service quality → routers → submodes; the tenth report's evidence
puts the routers pair first, and D1 is where that is settled.

## §2 Traps — newest first, each with what it cost

1. **A DOCUMENT CAN CITE A RECORD SECTION BEFORE IT EXISTS** — now a gate
   (`check_doc_shape.py`, citations): the board and two pages cited §9.170 for
   half a day while the record ended at §9.169. Write the section first.
2. **A SWEPT VALUE WITH A TYPED TWIN IS A SWEEP THAT MOVES NOTHING** (§9.170,
   #212): the hardcoding ledger skips ALL-CAPS assignments and `dict(...)`
   keywords - a value there is invisible to it.
3. **A READER THAT RESOLVES THROUGH THE CITY'S ARTEFACT READS TODAY'S BUILD,
   NOT THE RUN'S** (§9.169, #213): the reader took every run's stops from the
   rebuilt schedule and read heavy rail 0 for two days; `home_lga()` still does
   it for residents.
4. **A PRICE FROM ANOTHER BUILD IS NOT A PRICE** (§9.168): the digest's PRICE
   line says so; spend a 25 % probe before the arm.
5. **A REPORT PER SESSION REPEATS ITSELF** (§9.166): one per reading; the
   recommendations it repeats are decisions in `lane.json`, not paragraphs.
6. **A MOVE RETARGETED BY HAND LEAVES FOUR LINES BEHIND** (§9.171): the
   14 September move left four position-page paths pointing at the old tree;
   `check_doc_links.py` is now a gate.

Retired this session because a gate or the launcher enforces them: the viewer
touching `sys.stdout` (subprocess, §9.170), a result living only in `raw/`
(`session_gate.py --handoff`), the trend reader's heap (bounded, §9.169), a
null route in plan memory (§9.168), the freight row's own definition (§9.169),
a concurrent arm (the launcher refuses it, §9.170).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's approval was SPENT on
  `20260912T202242_300it_25pct`. A pair arm or a re-baseline needs its own,
  priced on a 25 % probe of the committed build and set as `RUN.gate.wall_ceiling_h`.
- **Never compare across a family boundary.** F35 opened at `20260912T184108`
  (§9.168); arm 0 is its reading. A run is a result only if `_run.json` says
  `ran_to_last_iteration`; a stopped arm is citable at its `reached_iteration`;
  a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a
  structural smoke probe may run at 1 %, says so, and is read for nothing.
- **One arm at a time** - the launcher refuses a concurrent arm at preflight
  and at run (§9.170); never recompile `.tools/classes` under one.
- **A launch with no automatic stop is refused**; so is one whose heap is
  below the registry's rule and one whose overlay changes nothing the run reads.
- **No launch while an open issue in the RUN'S LANE lacks a stated
  measurement** (GOAL requirement 10); `decision-needed` /
  `awaiting-implementation` with an `AWAITING-DECISION:` line is reported,
  never blocking. Declare `answers_issues` on a new overlay.
- **The simulator's documents live at `docs/`, the city's at
  `cities/<city>/docs/`** (user decision, 14 September 2026, §9.171); a
  position page is at most 130 lines and 14,000 bytes; the lane is edited in
  `lane.json`, never in the board.
- **A decision is asked once, as options, and recorded** (§9.171): never
  re-ask one `lane.json` holds an answer for.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** —
  FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder`.
- **Nothing may be tuned on arm 0** until the separation of #172 has run —
  §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
