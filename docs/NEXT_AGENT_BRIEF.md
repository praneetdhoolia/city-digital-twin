# Brief for the next agent

**Written:** 21 September 2026 (fifty-sixth session) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `7286de1` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle. The newest run on disk is the Mumbai structural check `20260921T165718_2it_100pct-mumbai-smoke` (`ran_to_last_iteration` at 2, 579.7 s); Newcastle's newest result is `20260916T063903_250it_25pct`. | `python src/run/session_gate.py --digest` |
| The gate passes for both cities (`check_city --all` PASS 66 FAIL 0); Newcastle's manifest regenerates identical; the separate package audit (#234, #235) is unchanged and unverified. | `python src/run/session_gate.py` · `python src/registry/check_city.py --all` · `python tests/check_package.py` |
| This session's PR is the branch `praneetdhoolia/mumbai-digital-twin`: open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/mumbai-digital-twin` · `git status --short --branch` |
| 34 open issues. New: #237 (standing room never scaled at 25 %, `awaiting-run`, blocks the launcher until the first arm after the fix measures it), #238 (the Mumbai launcher fold), #239 (D13, the study extent). | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| One lane decision unanswered: D13, Mumbai's study extent. D6–D12 recorded. | `python src/analyse/lane.py --ask` |
| 25 report recommendations open (20260918T182209:1 and :2 taken this session). | `python src/analyse/report_recs.py` |
| Registry **571** fields, manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke) for Newcastle; Mumbai 313 fields. The contract carries `required_by` (run 220 / builders 239 / reference_city 112). | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| Mumbai's manifest: 1,293 files, eleven harvest archives; 889 files tracked under `cities/mumbai/`. | `CITYSIM_CITY=mumbai python tests/check_manifest.py` · `git ls-files cities/mumbai \| wc -l` |

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

The launcher fold is verified on a Newcastle 1 % smoke before the Mumbai case; it touches the harness the arms
run on. Put D13 to the user at `/onboard`; the population synthesis, the mode targets and every count basis
follow the extent. **The next Newcastle 25 % arm opens a family** (standing room scaled, §9.203) and needs a
stated-cost approval; nothing after it compares with F35.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A framework builder change is verified by regenerating the reference artefact and diffing it** (§9.203):
   two `build_manifest.py` regressions (thirty rows mislabelled ODbL, five provenance rows stripped) sat in the
   tree for two days; the manifest takes 14 s to regenerate and found both.
2. **A regex over MATSim XML scales what it matches first** (§9.203, #237): standing room ran at full size on every
   25 % arm since the fleet gained standing places. Parse the XML; verify old against new on the real population.
3. **A second city declares the framework's keys, never a parallel namespace** (§9.202): 59 `RUN.smoke.*` twins
   bound the same MATSim parameters as framework fields, one to a parameter MATSim does not have
   (`brainExpBeta`). The contract's `required_by` says which keys a city must declare.
4. **A per-response API harvest is one archive** (§9.201): 13,500 loose files and 14,230 catalogue entries cost
   a 22 MB manifest and four-minute readers. `harvest.py`; readers import the harvester's `Harvest` constant.
5. **A per-vehicle audit map in a committed report** (§9.203): 2,139 ids a set times thirty sets, for no reader.
   Report a count per profile.
6. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): it mangles the port-rail table and the extractor
   refuses the blanks; PowerShell resolves MiKTeX's 24.04, which parses it. Run the PDF extractors from PowerShell.
7. **Python `write_text` writes CRLF on Windows** (§9.201): all 514 Mumbai provenance records would have failed
   their own hashes on a Linux checkout. `normalise_eol.py` now walks `data/raw/**/provenance*.json` and `city.json`;
   run it before and after `build_manifest.py`.
8. **A session without a handoff leaves the brief describing the session before it** (§9.203): 22 record
   sections and 131 uncommitted paths arrived with §0 stale. `/onboard` re-derives §0 by command for this reason.
9. **Builds and tests compete with an arm** (§9.177): verification stretched iterations 383 → 400–510 s.
   Batch work; never price an arm from a busy-machine reading.
10. **Mode-choice coverage counts trips** (§9.177): older records called these agents and misread ride's ceiling.

Retired by checks: the contract's Newcastle shape for another city (`required_by`, `check_city --all` green),
CRLF under `data/raw/` (`normalise_eol.py`), dead-harness detection (`run_failure.py`), concurrent arms and
missing automatic stops (the launcher), stale family stamps and oversized pages (the document gates), repeated
lane questions (`lane.json`). See [monitoring-and-gates](positions/monitoring-and-gates.md).

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT (§9.169, §9.176, §9.177). The next arm is
  quoted from its own build's probe (`arm_cost.py`) and needs a stated-cost approval; it opens a family.
- **25 % arms only.** A structural smoke may use 1 % (Newcastle) or the explicit population (Mumbai,
  `smoke_two_iterations`). One arm at a time; no recompilation under an arm.
- Compare only within a family, sample fraction and network build. A result requires `_run.json` to say
  `ran_to_last_iteration`; a stopped reading is citable at its `reached_iteration` only.
- The 67/143 holdout stays shut. No invented data; an adopted value is labelled adopted and a switched-off
  mechanism's parameters are placeholders (§9.202).
- D6–D12 settled in [lane.json](lane.json); D13 open. The TfNSW request is the user's to send (D2).
- Mumbai's `registry/*_framework.json` are regenerated by `cities/mumbai/build/adopt_framework_fields.py`
  after a contract change, never edited by hand; Mumbai runs through `run.py --baseline-smoke` until #238 lands.
- No run while an issue in its lane lacks its required declaration; #237 blocks the Newcastle launcher until
  the first arm after the fix reads it. Declare `answers_issues`.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch after merge.
