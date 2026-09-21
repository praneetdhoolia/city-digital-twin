# Brief for the next agent

**Written:** 21 September 2026 (fifty-seventh session) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `f35c5f0` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle. The newest run on disk is the Mumbai case `20260921T182708_2it_100pct` through the framework harness (`ran_to_last_iteration` at 2, 410.1 s); Newcastle's newest smoke is `20260921T180105_2it_1pct`, its newest result `20260916T063903_250it_25pct`. | `python src/run/session_gate.py --digest` |
| The gate passes for both cities (`check_city --all` PASS 66 FAIL 0); both manifests verify (Mumbai 1,314 rows); the separate package audit (#234, #235) is unchanged and unverified. | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` · `python tests/check_package.py` |
| This session's PR is the branch `praneetdhoolia/mumbai-twin-extent-and-launcher`: open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/mumbai-twin-extent-and-launcher` · `git status --short --branch` |
| 35 open issues after this handoff: #238 (the launcher fold) closed on `20260921T182708_2it_100pct`; #239 re-aimed at the plans and targets now D13 is taken; new #241 (the contract misses run-path keys read through the assembler) and #242 (the residents map reads one city's columns). | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered: D13 recorded 21 September 2026 (the notified MMR core, the four-district external tier). D6–D12 recorded. | `python src/analyse/lane.py --ask` |
| 25 report recommendations open. | `python src/analyse/report_recs.py` |
| Registry **574** fields, manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke) for Newcastle; Mumbai **374** fields, 1,314 manifest rows, 515 of 567 catalogue sources acquired (51 unobtained, 1 unusable). | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| The Mumbai synthesised population (27,057,132 persons, 6,068,786 households, `demand/population/B1_*.csv`, 3.3 GB, gitignored) regenerates in two minutes; its report is committed. | `CITYSIM_CITY=mumbai PYTHONPATH=src python cities/mumbai/build/build_population.py` · `demand/population/_population_report.json` |
| The Newcastle emitter reproduces the reference smoke's config but for the new gate's own default (`hiredFleet.representation = absent`); the Mumbai case re-emits identically. | `python src/run/reemit_config.py --run 20260921T180105_2it_1pct` · `CITYSIM_CITY=mumbai python src/run/reemit_config.py --run 20260921T182708_2it_100pct` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **Build the Mumbai activity chains and plans from the synthesised core population (27.06 M persons, 6.07 M households, B1 in demand/population/) at scale, with the framework's household sample unit; then derive the first per-mode targets (mode_targets_by_mode.csv) from the Census B-28 commute series, the operator ridership controls and the CMP** **(recommended)** - builds: the chains and plans at full scale are hours and tens of GB (the reference city writes 517,936 agents; this one is 52x that) - design the plans builder to write the harness's sample fraction of households directly; then a Mumbai case through the harness at a declared small fraction, minutes to an hour; no arm; opens a family; blocked on: nothing a decision settles - the extent (D13) and the population (9.204) are built; the work is a plans builder that scales past the 1,000-person development chain (activities, tours and destinations for 27 M persons, written for the harness's household sample) and the target derivation (#239) (9.204: 27,057,132 persons synthesised at the core extent for 2026 (_population_report.json); the executable case still runs the explicit 1,000-person population; docs/scaling.md: no sample fraction is shown to preserve behaviour, so the first citywide case states what it measures; #239)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D9 = A literature marginal utility of distance for bike, with its sweep (recommended) (2026-09-16) · D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16) · D12 = Hold escort members and joint companions to ride on their bound tours; car-less lift and shared passengers keep walk/bike/pt (recommended) (2026-09-16) · D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21)
<!-- generated:lane end -->

The Mumbai plans builder is the next task: the 1,000-person chain (`build_baseline_activities.py`, eight whole-day
alternatives a person) does not scale to 27 M persons - write the harness's household sample directly, at a declared
fraction, and say what the first citywide case measures (`cities/mumbai/docs/scaling.md`: no fraction has been shown to
preserve behaviour). The targets derive from `data/processed/observed/published_mode_splits.csv` with the record settling the
rickshaw/taxi, metro and active-mode mappings. **The next Newcastle 25 % arm opens a family** (standing room scaled,
§9.203) and needs a stated-cost approval; nothing after it compares with F35.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A one-byte EOL drift is a manifest failure on every Linux checkout** (§9.204): `osm_activity_areas.geojson` carried
   one CRLF at its tail, hashed as written, committed as LF - a byte short of its row. `normalise_eol.py` now walks
   `.geojson` and `.tsv`; run it before AND after `build_manifest.py`, for the city whose artefact changed.
2. **The contract's `required_by` misses keys read on the run path through `config_runtime`** (§9.204): it classes
   them as the assembler's, so a second city passes the contract and fails at launch on a `RegistryError`. Six such keys
   are declared for Mumbai by hand; derive the run-path closure function by function before the next city.
3. **A registry key that no longer exists in a builder's lineage stops the whole chain** (§9.204): renaming
   `RUN_baseline_smoke.json` broke `build_baseline_choices.py`'s `OUTPUT_INPUTS` two steps downstream. Grep the city's
   `build/` and `extract/` for a registry file name before moving it.
4. **A framework change is proven by re-emitting a finished run's config** (§9.204, `reemit_config.py`): the fold was
   proven on the Newcastle 1 % smoke in seconds; IDENTICAL or the diff names the parameter.
5. **`Path.write_text` writes CRLF on Windows** (§9.201, §9.204): the adopter wrote every `*_framework.json` CRLF; every
   writer passes `newline='\n'`.
6. **A regex over MATSim XML scales what it matches first** (§9.203, #237): standing room ran at full size on every
   25 % arm since the fleet gained standing places. Parse the XML; verify old against new on the real population.
7. **A second city declares the framework's keys, never a parallel namespace** (§9.202): one key per MATSim parameter;
   the contract's `required_by` says which keys a city must declare; a Mumbai fact goes in the adopter's OVERRIDES.
8. **A per-response API harvest is one archive** (§9.201): `harvest.py`; readers import the harvester's `Harvest` constant.
9. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): run the PDF extractors from PowerShell (MiKTeX 24.04).
10. **Builds and tests compete with an arm** (§9.177): verification stretched iterations 383 → 400–510 s. Batch work; never
    price an arm from a busy-machine reading.

Retired by checks: the second city's parallel launcher (`test_scoring_translation.py` asserts it is gone), a stale
framework file on a contract change (the adopter merges), CRLF under `data/raw/` and in GeoJSON (`normalise_eol.py`),
the contract's Newcastle shape for another city (`required_by`, `check_city --all` green), dead-harness detection
(`run_failure.py`), concurrent arms and missing automatic stops (the launcher), stale family stamps and oversized pages
(the document gates), repeated lane questions (`lane.json`). See [monitoring-and-gates](positions/monitoring-and-gates.md).

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT (§9.169, §9.176, §9.177). The next arm is
  quoted from its own build's probe (`arm_cost.py`, per city since §9.204) and needs a stated-cost approval; it opens a family.
- **25 % arms only** for Newcastle. A structural smoke may use 1 % (Newcastle) or the explicit population (Mumbai,
  `smoke_two_iterations`). One arm at a time; no recompilation under an arm.
- **The user's standing goal (21 September 2026):** a full Mumbai twin, every mode's data acquired; the twelve-mode
  requirements are the validation standard, the broad executable baseline comes first (§9.187).
- Compare only within a family, sample fraction and network build. A result requires `_run.json` to say
  `ran_to_last_iteration`; a stopped reading is citable at its `reached_iteration` only.
- The 67/143 holdout stays shut. No invented data; an adopted value is labelled adopted, an unobtained one takes a
  sweep member explicitly (`B.population.tertiary_attendance_rate_20_24`).
- D6–D13 settled in [lane.json](lane.json). The TfNSW request is the user's to send (D2).
- Mumbai's `registry/*_framework.json` are regenerated by `cities/mumbai/build/adopt_framework_fields.py`
  (OVERRIDES hold its facts); Mumbai runs through `run.py --scenario BASE --day WEEKDAY --run-config <overlay>` after
  `build_baseline_run_inputs.py`.
- No run while an issue in its lane lacks its required declaration; #237 blocks the Newcastle launcher until
  the first arm after the fix reads it. Declare `answers_issues`.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch after merge.
