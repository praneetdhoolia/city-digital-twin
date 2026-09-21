# Brief for the next agent

**Written:** 18 September 2026 (fifty-fifth session) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `722bfe9` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle; newest arm `20260916T063903_250it_25pct` completed its declared horizon at iteration 250. | `python src/run/session_gate.py --digest` · `python src/run/watch_run.py --run 20260916T063903_250it_25pct` |
| The onboarding gate passed. The separate package audit has 1,198 passes, two warnings and six failures: obsolete document roots (#234), incomplete run-input report coverage (#235). Full package consistency is unverified. | `python src/run/session_gate.py` · `python tests/check_package.py` |
| Previous PR #233 merged. This session lands `praneetdhoolia/codex-skills`; verify its PR and branch state before starting work. | `gh pr list --state all --head praneetdhoolia/codex-skills` · `git status --short --branch` · `git log origin/main..HEAD --oneline` |
| GitHub has 31 open issues. #234 and #235 record the package-audit defects. #210 remains open; Codex startup checks do not complete its hook/CI requirements. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` · `gh issue view 210` |
| No unanswered lane decisions. D6–D12 remain recorded. | `python src/analyse/lane.py --ask` |
| The recommendation ledger has 19 open rows; this tooling migration does not complete a model recommendation. | `python src/analyse/report_recs.py` |
| Registry **571** fields, manifest **959** files (**721 CC-BY / 220 ODbL** + 18 bespoke). The registry now declares the transit fleet representation (?9.179); no scenario package has been rebuilt. | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| Codex loads the project instructions and skills. The native browser connection passed after its dedicated Chrome profile started. Availability is session-specific. | `python .agents/scripts/configure_codex.py --check` · `codex debug prompt-input` · `codex mcp list` |
| The latest result's fit and supporting readings are preserved under processed results. | `python src/analyse/compare_runs.py 20260912T202242_300it_25pct 20260916T063903_250it_25pct --modes` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **Fold the Mumbai launch path into the harness: `run.py BASE --day WEEKDAY` instead of `run.py --baseline-smoke` - a city-declared scoring source (`RUN.scoring.translation`: the C1 translation with the HTS purpose share, or the bound scoring fields), the prepare-network / repair-schedule / write-vehicles assembly moved to `cities/mumbai/build/build_baseline_run_inputs.py` producing `scenarios/matsim/BASE/WEEKDAY/`, the plans at `demand/plans/matsim/population_WEEKDAY.xml.gz`; then delete `src/run/baseline_smoke.py`** **(recommended)** - no arm; a few hours of harness work, a Newcastle 1 % smoke of a few minutes to prove the harness unchanged, and the Mumbai `smoke_two_iterations` case (~10 min) on the folded path; no family boundary; blocked on: nothing - the registry namespace is unified (9.202); the harness couplings are named there: scoring_from_c1 + purpose_share, the SETS/PLANS layout, the parking price file, the residents map and the no-targets close-out (9.202: Mumbai passes the city contract on the framework's keys; the emitted config of the structural check declares what the previous cases left to defaults; the launcher is the one remaining parallel path; #238)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **Add coherent Mumbai households and realistic hired-trip responses** - Hired-supply case completed in 910.5 s including preparation. No new run launched; multi-hour arms still require stated-cost approval.; opens a family; blocked on: D13 (the study extent) - a coherent household population is synthesised from the census controls at the chosen extent, not added to the 1,000-person explicit list; and the launcher fold, so the case runs through the harness with its gates and records (9.202) (9.200: the bounded fleet case completed with native waits, balanced request accounting and finite retained scores. Timeouts still abort the day; no operating-fleet or ridership calibration is claimed.;)
5. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D13.** Mumbai's study extent. city.json declares the four Census 2011 districts (Mumbai, Mumbai Suburban, Thane incl. today's Palghar, Raigad) - the acquisition's overcoverage, not a chosen area; the notified MMR takes only parts of three of them and 1,053 of 4,813 census leaves have no source polygon yet. Which extent does the population, the targets and every count basis follow? Options: The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) · The four 2011 census districts as declared · Greater Mumbai (BMC) alone (9.202: the declaration; census_geography_audit.json: 1,053 leaves without geometry, 8.4 M of Thane's 11.1 M persons without geometry; the previous agent's README: 'the user has not yet confirmed this geographical choice'; #239)

Decided: D8 = Re-derive the ferry target from the disclosed TPA tap-on series (recommended) (2026-09-16) · D9 = A literature marginal utility of distance for bike, with its sweep (recommended) (2026-09-16) · D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16) · D12 = Hold escort members and joint companions to ride on their bound tours; car-less lift and shared passengers keep walk/bike/pt (recommended) (2026-09-16)
<!-- generated:lane end -->

Do the Java work first, then the roots rebuild: D12 needs both the plans builder and its Java gate.
The rebuild opens a family. Its own probe prices the next arm, which requires stated-cost approval.
The scoring representation ships as `absent` (§9.177). The earlier scratch patches are gone;
the lane and position pages specify the work. The Codex migration is documented in [`.agents/README.md`](../.agents/README.md).

## §2 Traps — newest first, at most ten, each with what it cost

1. **Configured MCP does not mean a live browser** (§9.178): the first tab check failed because CDP was offline.
   Use browser-harness to check the endpoint and start its dedicated profile. Claude hooks do not run in Codex.
2. **Builds and tests compete with an arm** (§9.177): verification stretched iterations from the idle probe's
   383 s to 400–510 s. Batch work and do not price an arm from a busy-machine reading.
3. **Mode-choice coverage counts trips** (§9.177): older records called these agents and misread ride's ceiling.
   Read the coverage reader's wording and the bound-trip evidence together.
4. **The cutoff snap survived score averaging** (§9.177): another long arm did not remove it.
   Do not repeat a scoring remedy without new evidence.
5. **Scratch work is not durable** (§9.177): seven prepared patches were lost.
   Preserve authorised work on the branch or in the record before handoff.
6. **Extraction by line number shifts later ranges** (§9.177): a refactor broke explicit-signals configuration.
   Extract bottom-up and verify the resulting artefact.
7. **Imports can acquire and rewrite data** (§9.177, #232): an import sweep executed nine extract adapters.
   Compile these adapters for syntax checks until their entry points are guarded.
8. **Pipelines can hide failed checks** (§9.177): three commits needed repairs after tail masked failures.
   Inspect each check's own exit status.
9. **CPU contention changes an arm's price** (§9.176, §9.174): a game stretched iterations to 405–561 s.
   Account for competing processes when reading pace.
10. **The launched viewer retains imported code** (§9.175): edits were invisible on the harness's port.
    Develop the viewer with `--reload` on a separate port.

Retired by checks: dead-harness detection (`run_failure.py`), concurrent arms and missing automatic stops
(launcher), residents resolved through today's population (run snapshot), stale family stamps and oversized
pages (document gates), and repeated lane questions (`lane.json`). See [monitoring-and-gates](positions/monitoring-and-gates.md).

## §3 Standing directives and approvals

- **No run approval stands.** Previous approvals are SPENT (§9.169, §9.176, §9.177).
  Quote the next arm from its own build's probe and set its approved wall ceiling.
- **25 % arms only.** A structural smoke may use 1 %. One arm at a time; no recompilation under an arm.
- Compare only within a family, sample fraction and network build. A result requires
  `_run.json` to say `ran_to_last_iteration`; stopped readings are limited to `reached_iteration`.
- The 67/143 holdout stays shut until the end. No invented data or unsupported coefficients.
- D6–D12 remain settled in [lane.json](lane.json). The TfNSW request is the user's to send (D2).
- #30 concerns allocation, not a new short-trip kernel (§9.177). The frozen constants remain governed by §8.5.
- No run while an issue in its lane lacks its required declaration. Declare `answers_issues`.
- Keep Codex support in `.agents/`; global skills and MCP credentials stay in user configuration.
  Use the active git identity, verify the tracked hooks path, and inspect commits and PR bodies for attribution.
- Never commit to `main`. Land the session through one PR targeting `main` and remove its branch after merge.
- The model lane remains separate from this tooling close-out. Start it only under its own authorised scope.
