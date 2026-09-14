# Brief for the next agent

**Written:** 14 September 2026, forty-sixth session · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/arm-0-read-and-reader-fixes`.
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**YOUR LANE IS THE FIRST PAIR ARM, OR THE FIRST ROOT FIX - THE USER DECIDES
WHICH.** Arm 0 of F35 has landed as the project's second RESULT (§9.169):
`20260912T202242_300it_25pct`, 300 of 300 in 30.35 h, **2 of 12 inside 10 %**
(car +9.6 %, motorbike -5.6 %), six past the stop bar. No arm is running, no
approval stands, and the machine is idle. Nothing was tuned.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **MACHINE IDLE, NO ARM RUNNING.** Arm 0 `20260912T202242_300it_25pct` is `completed`, `ran_to_last_iteration` at 300, wall 109,260.8 s, rc 0; its `_metrics.json` and `_fit.json` (`is_a_result: true`) are written. | `python src/run/session_gate.py --digest` · `Get-Process java` · `python src/analyse/build_run_index.py` |
| **NO APPROVAL STANDS.** Arm 0's 44 h ceiling was spent on its launch; the user chose NO ARM in the forty-sixth session. A pair arm or a re-baseline needs a fresh stated-cost approval, priced by `arm_cost.py` on arm 0's clock: **30.4 h** at 300 iterations, **~25.5 h at the declared 250**, spread 21.7–46.9 h. | `python src/analyse/arm_cost.py --run-config f35_baseline_25pct --iterations 250` |
| **F35 HAS ITS READING.** The ledger's F35 row carries arm 0 as its reading; the board's scoreboard reads it. Nothing before `20260912T184108` compares with it. | `results/INDEX.md` · `python src/analyse/report_mode_ridership.py --run 20260912T202242_300it_25pct --it 300` (`--trend` for the direction) |
| **THE HORIZON IS 250.** `RUN.controler.last_iteration` = 250 (cutoff 200) since 14 Sep (§9.169); the 30 run-input sets carry it. A pair overlay that declares 300 must say why. | `python src/registry/render_docs.py --check` · `grep -c 'lastIteration" value="250"' cities/newcastle/scenarios/matsim/*/*/config.xml` (30) |
| **THE READER READS THE RUN'S OWN SCHEDULE** (§9.169). A pt-submode reading of any run is taken through `output/output_transitSchedule.xml.gz`; a warning names the fallback. The F32 result reads heavy rail 20,932 / +220.6 % again. | `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` |
| The issue ledger after this session's grooming: the overtaken issues closed on evidence (#48 #96 #167 #175 #183 #184 #185 #189 #192), #86 and #30 moved to `awaiting-implementation`, the rest re-aimed at the pair that measures them, five filed from the ninth report. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| This session's PR: open until merged; its branch is deleted when it is. | `gh pr list --state open` |
| Registry **553** fields (`RUN.controler.last_iteration` changed), manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke; 30 config hashes and 15 re-gzipped era schedule hashes moved, content identical), unit tests **469**. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` · `python -m pytest -q tests/unit` |

Then: `python src/run/session_gate.py`. The machine is idle, so the toolchain
step compiles `.tools/classes`; it is a recompile, and one arm at a time
means it never runs under an arm.

## §1 The lane

**Two roads, and the user picks one. Neither has an approval yet.**

1. **THE FIRST PAIR ARM** (#172, §9.169): ONE field against arm 0, **250
   iterations at 25 %** (~25.5 h quoted), the gate watcher on, a ceiling set
   at the approved cost, `answers_issues` declared, coverage read on BOTH
   sides (#174). The decided sequence is scoring
   (`RUN.replanning.score_msa_representation` = `at_innovation_cutoff`) →
   choice set (`RUN.replanning.plan_selector_for_removal` = `SelectRandom`)
   → service quality (`C.time_weights.service_quality_representation`) →
   routers (`C.raptor.mode_cost_representation` = `mode_constant`) →
   submodes (`RUN.mode_choice.pt_submode_alternatives`). **On arm 0's
   evidence the routers pair is recommended first**: light rail -73.9 %,
   heavy rail +54.6 % and ferry -63.3 % are three of the six STOP modes and
   all three are split by the raptor, which reads no submode constant. Each
   pair opens a family and differences against arm 0's it.300 reading.
2. **OR THE ROOTS FIRST** (§9.169): ride's 20.60 % target sits above its own
   19.11 % choice-set coverage, fixed at the seed - the demand seeds ride
   below the target (#86); walk trips average 3.74 km against 0.70 at the
   demand's destination placement (#30); bike rides 8.10 km at +201.6 % with
   no distance or traffic cost in its score (#107). Each is a demand rebuild
   that opens a family and needs a new baseline before any pair.
3. **The tenth report runs after the next reading**, never before (§9.166).
4. **The ASC contraction test** stays HELD; bike is the mode it can answer.

**Decisions the user must take:** which road, and the arm's stated-cost
approval; whether to send the drafted TfNSW bespoke-table request (#50,
HELD on 14 Sep). Taken on 14 Sep on clickable choices (§9.169): no arm that
session; `RUN.controler.last_iteration` 250 for the pairs; #50 held.

## §2 Traps — newest first, each with what it cost

1. **A READER THAT RESOLVES THROUGH THE CITY'S ARTEFACT READS TODAY'S
   BUILD, NOT THE RUN'S.** The reader took every run's stops from the
   assembled schedule under `scenarios/matsim/`, which the F34 rebuild
   overwrote; the only result read heavy rail 0 / -100 % on the board for
   two days with every gate green (§9.169). Read a run through its OWN
   outputs; a city artefact is a different build the moment anything rebuilds.
2. **A LIKE-FOR-LIKE ROW CAN BE OFF BY ITS OWN DEFINITION.** The freight
   row counted the scheduled closures against a target that included the
   freight ones: -22.7 % on every run, all bookkeeping (§9.169).
3. **THE TREND READER HELD 39.8 GB.** An unbounded per-iteration table
   cache in a `--trend` pass over a 25 % arm; it is bounded now, and a reader
   that grows with the run is a stall in waiting (§9.169).
4. **A BOARD BLOCK THAT PINS A LIVE COUNT IS STALE WHEN WRITTEN**: the runs
   block carried a running arm's iteration and the gate was red for the
   life of every arm (§9.169); it prints `live` now.
5. **A NULL ROUTE IS A WHOLE-PLAN RE-ROUTE** (§9.168): never leave a route
   null in plan memory; route it yourself.
6. **A PRICE FROM ANOTHER BUILD IS NOT A PRICE** (§9.168): the pricer says
   "PRICED ON A DIFFERENT BUILD"; spend the probe before the arm.
7. **A 4-ITERATION PROBE CARRIES NO PLAN MEMORY** (§9.168): its heap is a
   lower bound; arm 0's `gc.log` read 26.2 GiB live at the peak with no slope.
8. **A BOARD BLOCK GENERATED FROM A FAILED RUN IS STILL A FALSE CLAIM**
   (§9.168), and so is one generated through a wrong reader (§9.169).
9. **A RECORDED OVERRIDE CAN EXECUTE NOTHING**; dry-run before spending an
   arm (§9.166). **A GATE INTERVAL IS NOT A GATE** (§9.164, #131).
10. **A REPORT PER SESSION REPEATS ITSELF** (§9.166). One per reading; the
    ninth ran at iteration 288, before arm 0 read, and its rail cells were
    taken through the wrong reader.

## §3 Standing directives and approvals

- **NO APPROVAL STANDS.** Arm 0's approval was SPENT on
  `20260912T202242_300it_25pct`. A pair arm or a re-baseline needs its own,
  priced on arm 0 at the fraction and set as `RUN.gate.wall_ceiling_h`.
- **Never compare across a family boundary.** F35 opened at `20260912T184108`
  (§9.168); arm 0 is its reading. A run is a result only if `_run.json` says
  `ran_to_last_iteration` (a warm-completed arm included, #192); a stopped
  arm is citable at its `reached_iteration`; a FAILED arm is citable for nothing.
- **25 % runs only** (user directive, 1 September 2026) for ARMS; a
  structural smoke probe may run at 1 %, says so, and is read for nothing.
- **One arm at a time** - the launcher now REFUSES a concurrent arm (§9.169);
  never recompile `.tools/classes` or `.tools/classes-signals` under one.
- **A launch with no automatic stop is refused**; so is one whose heap is
  below the registry's rule, one whose overlay changes nothing the run reads,
  and now one while another arm runs.
- **No launch while an open issue in the RUN'S LANE lacks a stated
  measurement** (GOAL requirement 10); `decision-needed` /
  `awaiting-implementation` with an `AWAITING-DECISION:` line is reported,
  never blocking. Declare `answers_issues` on a new overlay.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`** —
  FROZEN. `C.asc.ferry` and `C.asc.cycle` are `placeholder`.
- **Nothing may be tuned on arm 0** until the separation of #172 has run —
  §9.159's scoped departure, still in force.
- **The 67/143 holdout stays shut until the end** (§12); all 26 station rows
  are holdout and the heavy-rail target keeps summing them, saying so (#189).
- **Never commit to `main`**; the session's ONE PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
