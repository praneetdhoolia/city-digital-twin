# Brief for the next agent

**Written:** 21 September 2026 (fifty-seventh session, continued) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `79fc127` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle. The newest run on disk is the first citywide Mumbai case `20260921T220701_2it_0.1pct` (`ran_to_last_iteration` at 2, 354.3 s, 26,884 persons - a structural check, not a reading: §9.205); Newcastle's newest smoke is `20260921T180105_2it_1pct`, its newest result `20260916T063903_250it_25pct`. | `python src/run/session_gate.py --digest` |
| The gate passes for both cities (`check_city --all` PASS 66 FAIL 0); both manifests verify (Mumbai 1,314 rows); the separate package audit (#234, #235) is unchanged and unverified. | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` · `python tests/check_package.py` |
| This session's second PR is the branch `praneetdhoolia/mumbai-plans-at-scale`: open, or merged and the branch deleted (#243 merged the first). | `gh pr list --state all --head praneetdhoolia/mumbai-plans-at-scale` · `git status --short --branch` |
| 35 open issues after this handoff: #238 (the launcher fold) closed on `20260921T182708_2it_100pct`; #239 re-aimed at the plans and targets now D13 is taken; new #241 (the contract misses run-path keys read through the assembler) and #242 (the residents map reads one city's columns). | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| One lane decision unanswered: D14, the fraction Mumbai can be read at (a leaner agent measured on a 1 % case first, or a larger host). D6–D13 recorded. | `python src/analyse/lane.py --ask` |
| 25 report recommendations open. | `python src/analyse/report_recs.py` |
| Registry **574** fields, manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke) for Newcastle; Mumbai **380** fields, 1,319 manifest rows, 515 of 567 catalogue sources acquired (51 unobtained, 1 unusable). | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| The Mumbai synthesised population (27,057,132 persons, `demand/population/B1_*.csv`, 3.3 GB, gitignored) regenerates in two minutes; the citywide plans (1,352,144 persons at the 0.05 build fraction, `demand/baseline/plans_core_sample.xml.gz`, 51 MB, gitignored) in three; both reports are committed; the assembly then takes two. | `CITYSIM_CITY=mumbai PYTHONPATH=src python cities/mumbai/build/build_population.py` · `python cities/mumbai/build/build_plans.py` · `python cities/mumbai/build/build_baseline_run_inputs.py` |
| The Newcastle emitter reproduces the reference smoke's config but for the new gate's own default (`hiredFleet.representation = absent`); the Mumbai case re-emits identically. | `python src/run/reemit_config.py --run 20260921T180105_2it_1pct` · `CITYSIM_CITY=mumbai python src/run/reemit_config.py --run 20260921T182708_2it_100pct` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **Give Mumbai a fraction it can be read at: measure the agent's memory (plan memory, events, telemetry) on a 1 % core case, then either a leaner agent or a larger host (D14), then the equivalence experiments of scaling.md at the fraction that fits; meanwhile the pt trips of 13 h and the 5,454 stuck agents of the 0.1 % case are read for what is granularity and what is the schedule** **(recommended)** - a 1 % core case of a few iterations (270,000 agents, xmx 50g on the 63 GB host; ~1 h by the 0.1 % case's 88 s an iteration scaled) to measure the per-agent memory and the pt trip times; no arm; opens no family (no result compares yet); no family boundary; blocked on: D14 (the host or the agent) for anything above 1 %; nothing for the 1 % measurement itself (9.205: 17.30 GiB at 0.001 against 13.74 at a negligible population (140 KB an agent), so 1 % needs 50 GiB and 5 % 194 GiB; at 0.001 the flow-capacity identity gives 1.8 veh/h a lane and a 4.5 km car trip 194 min; cities/mumbai/docs/scaling.md; #239)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D14.** Mumbai cannot be read on this host: 140 KB an agent means 1 % of the 27.06 M-person core needs 50 GiB and 5 % 194 GiB against 63 GB, while at 1 % the flow-capacity identity gives a lane 6-18 vehicles an hour (the 0.1 % case's 4.5 km car trip took 194 min). Which way to a fraction a reading can stand on? Options: Measure a leaner agent first on a 1 % case, then decide the host (recommended) · A larger host now (cloud or workstation, 256-512 GB) at the reference city's 25 % · Hold Mumbai at the structural check and finish the reference city first (9.205: the measured heap rule (13.7 + 3,600 x fraction GiB) and the 0.1 % case's trip times; docs/scaling.md; the reference city's 25 % arms peak at 26.2 GiB for 155,000 agents (9.169); #239)

Decided: D9 = A literature marginal utility of distance for bike, with its sweep (recommended) (2026-09-16) · D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16) · D12 = Hold escort members and joint companions to ride on their bound tours; car-less lift and shared passengers keep walk/bike/pt (recommended) (2026-09-16) · D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21)
<!-- generated:lane end -->

Mumbai's instrument exists (plans, targets, the reporter through the harness) and cannot yet stand on a reading: at 0.001
the flow identity passes a lane 1.8 vehicles an hour, and 1 % needs 50 GiB of this host's 63 (`cities/mumbai/docs/scaling.md`).
Put D14 to the user at `/onboard`; a 1 % case at xmx 50g is the one measurement that needs no decision. The 0.1 % case's
13-hour pt trips are granularity first and the schedule second - read them only at a fraction that can be read.
**The next Newcastle 25 % arm opens a family** (standing room scaled, §9.203) and needs a stated-cost approval.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A tiny sample fraction is a queue pathology, not a small city** (§9.205): at 0.001 the capacity identity gives a
   1,800 veh/h lane 1.8 vehicles an hour; the 0.1 % case's 4.5 km car trip took 194 min and 5,454 agents were removed
   stuck. Read nothing from a fraction the flow identity cannot carry; the launcher prices it, the reader does not refuse it.
2. **A one-byte EOL drift is a manifest failure on every Linux checkout** (§9.204): `osm_activity_areas.geojson` carried
   one CRLF at its tail, hashed as written, committed as LF - a byte short of its row. `normalise_eol.py` now walks
   `.geojson` and `.tsv`; run it before AND after `build_manifest.py`, for the city whose artefact changed.
3. **The contract's `required_by` misses keys read on the run path through `config_runtime`** (§9.204): it classes
   them as the assembler's, so a second city passes the contract and fails at launch on a `RegistryError`. Six such keys
   are declared for Mumbai by hand; derive the run-path closure function by function before the next city.
4. **A registry key that no longer exists in a builder's lineage stops the whole chain** (§9.204): renaming
   `RUN_baseline_smoke.json` broke `build_baseline_choices.py`'s `OUTPUT_INPUTS` two steps downstream. Grep the city's
   `build/` and `extract/` for a registry file name before moving it.
5. **A framework change is proven by re-emitting a finished run's config** (§9.204, `reemit_config.py`): the fold was
   proven on the Newcastle 1 % smoke in seconds; IDENTICAL or the diff names the parameter.
6. **`Path.write_text` writes CRLF on Windows** (§9.201, §9.204): the adopter wrote every `*_framework.json` CRLF; every
   writer passes `newline='\n'`.
7. **A regex over MATSim XML scales what it matches first** (§9.203, #237): standing room ran at full size on every
   25 % arm since the fleet gained standing places. Parse the XML; verify old against new on the real population.
8. **A second city declares the framework's keys, never a parallel namespace** (§9.202): one key per MATSim parameter;
   the contract's `required_by` says which keys a city must declare; a Mumbai fact goes in the adopter's OVERRIDES.
9. **A per-response API harvest is one archive** (§9.201): `harvest.py`; readers import the harvester's `Harvest` constant.
10. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): run the PDF extractors from PowerShell (MiKTeX 24.04).
Retired by checks: the second city's parallel launcher (`test_scoring_translation.py` asserts it is gone), a stale
framework file on a contract change (the adopter merges), CRLF under `data/raw/` and in GeoJSON (`normalise_eol.py`),
the contract's Newcastle shape for another city (`required_by`, `check_city --all` green), dead-harness detection
(`run_failure.py`), concurrent arms and missing automatic stops (the launcher), stale family stamps and oversized pages
(the document gates), repeated lane questions (`lane.json`). See [monitoring-and-gates](positions/monitoring-and-gates.md).

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT (§9.169, §9.176, §9.177). The next arm is
  quoted from its own build's probe (`arm_cost.py`, per city since §9.204) and needs a stated-cost approval; it opens a family.
- **25 % arms only** for Newcastle. A structural smoke may use 1 % (Newcastle) or the explicit population (Mumbai,
  `smoke_two_iterations`, now 0.1 % of the core). A Mumbai run above the plans' 0.05 build fraction is refused. One arm at a time; no recompilation under an arm.
- **The user's standing goal (21 September 2026):** a full Mumbai twin, every mode's data acquired; the twelve-mode
  requirements are the validation standard, the broad executable baseline comes first (§9.187).
- Compare only within a family, sample fraction and network build. A result requires `_run.json` to say
  `ran_to_last_iteration`; a stopped reading is citable at its `reached_iteration` only.
- The 67/143 holdout stays shut. No invented data; an adopted value is labelled adopted, an unobtained one takes a
  sweep member explicitly (`B.population.tertiary_attendance_rate_20_24`).
- D6–D13 settled in [lane.json](lane.json); D14 open. The TfNSW request is the user's to send (D2).
- Mumbai's `registry/*_framework.json` are regenerated by `cities/mumbai/build/adopt_framework_fields.py`
  (OVERRIDES hold its facts); Mumbai runs through `run.py --scenario BASE --day WEEKDAY --run-config <overlay>` after
  `build_baseline_run_inputs.py`.
- No run while an issue in its lane lacks its required declaration; #237 blocks the Newcastle launcher until
  the first arm after the fix reads it. Declare `answers_issues`.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch after merge.
