# Brief for the next agent

**Written:** 14 September 2026, forty-seventh session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/docs-home-viewer-and-tenth-report`.
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS THE FIRST PAIR ARM, OR THE FIRST ROOT FIX - THE USER DECIDES
WHICH.** Nothing ran this session. Arm 0 of F35 (`20260912T202242_300it_25pct`,
300 of 300, a RESULT) is still the newest reading: **2 of 12 inside 10 %**
(car +9.6 %, motorbike −5.6 %), six past the stop bar. The session moved the
documents to `docs/`, cut the framing documents, rebuilt the run viewer, fixed
#197–#200 and lodged the tenth report (§9.170). No approval stands.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **MACHINE IDLE, NO ARM RUNNING.** The newest run on disk is the 1 % smoke `20260914T150700_2it_1pct` (2 of 2, rc 0, read for nothing); the newest reading is arm 0. | `python src/run/session_gate.py --digest` · `Get-Process java` |
| **NO APPROVAL STANDS.** A pair arm or a re-baseline needs a fresh stated-cost approval priced on arm 0: ~25.5 h at 250 iterations (24.5–26.0 h on the innovating/tail split), band 21.7–46.9 h. The controler was recompiled (#197) and the pricer will say PRICED ON A DIFFERENT BUILD until a 25 % probe runs on it. | `python src/analyse/arm_cost.py --run-config f35_baseline_25pct --iterations 250` |
| **THE DOCUMENTS ARE AT `docs/`.** `cities/newcastle/docs/` does not exist; `city.docs()` resolves the tree; a `docs/` path in `cities/newcastle/tests/doc_*.json` resolves at the repository root. | `ls docs` · `python tests/check_doc_currency.py --strict` |
| **THE VIEWER READS THE TWELVE MODES.** `python src/analyse/run_view.py` (any run from the picker) shows each mode against its target; no run on disk carries `_readings.jsonl` yet - the gate watcher writes it from the next arm on. | `python src/analyse/run_view.py --run 20260912T202242_300it_25pct` |
| **ARM 0's FINDINGS ARE IN `results/processed`** (`_fit.json`, `_metrics.json`, `modes_final.json`, `modes_trend.txt`) - extracted this session after the tenth report found them only in `raw/`. | `ls results/processed/20260912T202242_300it_25pct` |
| The issue ledger: 21 open at the report; #197 #198 #199 #200 are fixed on this branch and CLOSE WHEN THE PR MERGES; #196 awaits a decision; the eleven risks the tenth report named are filed. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **558** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke; the three A4 corridor rows moved bytes, not values), unit tests **474**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |

Then: `python src/run/session_gate.py`. The machine is idle, so the toolchain
step compiles `.tools/classes`; one arm at a time means it never runs under an arm.

## §1 The lane

**Two roads, and the user picks one. Neither has an approval yet.**

1. **THE FIRST PAIR ARM** (#172, §9.169): ONE field against arm 0, **250
   iterations at 25 %**, the gate watcher on, a ceiling set at the approved
   cost, `answers_issues` declared, coverage read on BOTH sides (#174). The
   decided sequence is scoring → choice set → service quality → routers →
   submodes; **on arm 0's evidence and the tenth report's factor ledger the
   routers pair (`C.raptor.mode_cost_representation` = `mode_constant`) is
   recommended first** - light rail −73.9 %, heavy rail +54.6 % and ferry
   −63.3 % are decided in the raptor and no control has run. Take one 25 %
   probe on the recompiled controler before spending the approval on a price.
2. **OR THE ROOTS FIRST** (§9.169): ride's 20.60 % target sits above its own
   19.11 % coverage, fixed at the seed (#86); walk trips average 3.74 km
   against 0.70 at the demand's destination placement (#30); bike carries no
   distance cost (#107). Each is a demand rebuild that opens a family; #196
   (consume the household-size top-band mean) folds into the same rebuild.
3. **The eleventh report runs after the next reading**, never before (§9.166).
4. **The ASC contraction test** stays HELD; bike is the mode it can answer.

**Decisions the user must take:** which road, and the arm's stated-cost
approval; whether to send the drafted TfNSW bespoke-table request (#50, held
five reports running); whether to require the nine test-workflow jobs as
status checks on `main` (ruleset 21121872 - the agent's API call was refused;
the prepared JSON is one `gh api -X PUT` away); #196 consume or retire.

## §2 Traps — newest first, each with what it cost

1. **A VIEWER INSIDE THE RUNNER'S PROCESS MUST NOT TOUCH `sys.stdout`** (§9.170):
   the first build of the reading redirected stdout on a daemon thread - in a
   detached arm that swallows the gate, ceiling and stall watchers' prints.
   It runs the reporter as a subprocess now; keep it that way.
2. **A SWEPT VALUE WITH A TYPED TWIN IS A SWEEP THAT MOVES NOTHING** (§9.170):
   0.6 sat beside `B.population.home_jitter_radius_factor` at three sites, and
   the corridor builder carried the tram's dwell with a different sweep. The
   hardcoding ledger skips ALL-CAPS assignments and `dict(...)` keywords - a
   value there is invisible to it.
3. **A RESULT CAN LIVE ONLY IN THE RAW CACHE** (§9.170): arm 0's `_fit.json`
   never reached `processed/` because the close-out's trend extraction did not
   finish; a trim would have deleted the second result. Check `processed/`
   after every close-out.
4. **A DOCUMENT CAN CITE A RECORD SECTION BEFORE IT EXISTS**: the board and
   two pages cited §9.170 for half a day while the record ended at §9.169;
   the tenth report counted it a contradiction. Write the section before the
   citation, or say "this session" until the section is appended.
5. **A READER THAT RESOLVES THROUGH THE CITY'S ARTEFACT READS TODAY'S BUILD,
   NOT THE RUN'S** (§9.169): the reader took every run's stops from the
   rebuilt schedule and read heavy rail 0 for two days. The same class stands
   open for residents: `extract_metrics.home_lga()` reads today's B1 table.
6. **A LIKE-FOR-LIKE ROW CAN BE OFF BY ITS OWN DEFINITION** (§9.169): the
   freight row counted scheduled closures against a target that included the
   freight ones, −22.7 % on every run, all bookkeeping.
7. **THE TREND READER HELD 39.8 GB** (§9.169); it is bounded now, and a reader
   that grows with the run is a stall in waiting.
8. **A NULL ROUTE IS A WHOLE-PLAN RE-ROUTE** (§9.168): never leave a route
   null in plan memory; route it yourself.
9. **A PRICE FROM ANOTHER BUILD IS NOT A PRICE** (§9.168): the controler was
   recompiled this session; spend a 25 % probe before the arm.
10. **A REPORT PER SESSION REPEATS ITSELF** (§9.166): ten reports in eleven
    days, 141 of 177 recommendations taken, the goal count moved only on a
    rebuild. One per reading.

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's approval was SPENT on
  `20260912T202242_300it_25pct`. A pair arm or a re-baseline needs its own,
  priced on arm 0 at the fraction and set as `RUN.gate.wall_ceiling_h`.
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
- **The project's documents live at `docs/`** (user decision, 14 September
  2026, §9.170); nothing goes back under `cities/<city>/docs/`.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** —
  FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder`.
- **Nothing may be tuned on arm 0** until the separation of #172 has run —
  §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
