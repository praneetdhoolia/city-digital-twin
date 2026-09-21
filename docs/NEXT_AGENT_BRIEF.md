# Brief for the next agent

**Written:** 22 September 2026 (fifty-eighth session) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `077ec83` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle. The newest run on disk is the corrected 1 % Mumbai case `20260922T005949_4it_1pct` (`ran_to_last_iteration` at 4; evidenced fleet, transit PCE scaled); before it `20260921T231313_4it_1pct` (the same case at the mapper's fleet and full PCE). Both are structural measurements of the flow identity at 0.01, not readings (§9.206). Newcastle's newest result is `20260916T063903_250it_25pct`. | `python src/run/session_gate.py --digest` |
| The gate passes for both cities (`check_city --all` PASS 63 FAIL 0); both manifests verify (Mumbai 1,349 rows); the separate package audit (#234, #235) is unchanged and unverified. Mumbai's own hardcoding ledger (`CITYSIM_CITY=mumbai check_hardcoding.py --strict`) reads 268 items, all pre-existing — the CI gate runs the reference city only. | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` · `python tests/check_package.py` |
| This session's PR is the branch `praneetdhoolia/mumbai-fleet-capacities-and-scaling`: open, or merged and the branch deleted (#244, last session's, was merged at this session's start). | `gh pr list --state all --head praneetdhoolia/mumbai-fleet-capacities-and-scaling` · `git status --short --branch` |
| 36 open issues after this handoff: #245 filed (the commuter ferry crossings are not in Mumbai's feed); #239 carries D15; #237 now also carries the transit-PCE scaling that opens its family. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| One lane decision unanswered: D15 (merge the degree-2 link chains and re-run the 1 % case, or a 384–512 GB host for a 10 % core, or hold). D14 recorded 21 September 2026 from the user's goal directive. | `python src/analyse/lane.py --ask` |
| 25 report recommendations open. | `python src/analyse/report_recs.py` |
| Registry **574** fields (`RUN.sample.transit_pce_scaling` in, `RUN.monitor.enabled` retired), manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke) for Newcastle; Mumbai **403** fields (23 new: `A_transit_fleet.json`), 1,349 manifest rows, 529 of 572 catalogue sources acquired (42 unobtained, 1 unusable): 14 acquired this session, of which 5 newly catalogued. | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| The Mumbai run inputs are assembled with the explicit fleet (`scenarios/matsim/_run_inputs_report.json` carries `fleet`); a changed capacity field needs `build_transit_fleet.py` then `build_baseline_run_inputs.py` (3 min), never a remap. | `CITYSIM_CITY=mumbai PYTHONPATH=src python cities/mumbai/build/build_transit_fleet.py` · `python cities/mumbai/build/build_baseline_run_inputs.py` |
| The Newcastle emitter reproduces the reference smoke's config but for the hired-fleet gate's own default (as at §9.204); the Mumbai case re-emits IDENTICAL. `RUN.sample.transit_pce_scaling` reaches the sampled `transitVehicles.xml.gz` (PCE = fraction × mapped), not the config. | `python src/run/reemit_config.py --run 20260921T180105_2it_1pct` · `CITYSIM_CITY=mumbai python src/run/reemit_config.py --run 20260922T005949_4it_1pct` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **Merge the mapped network's degree-2 link chains (length, capacity, lanes, modes and mapped stops preserved) and re-run the 1 % lean-agent case: if the stuck share falls from 43 % to the reference city's order, the equivalence series of scaling.md (0.5 / 1 / 2 %) follows on this host; if not, the fraction needs D15's host** **(recommended)** - a network merge and one remap of the combined feed (~1 h of builds), then the 1 % case at 1.3 h (`python src/analyse/arm_cost.py --run-config lean_agent_one_percent --iterations 4` prices it on 20260922T005949_4it_1pct); no arm; opens no family (no result compares yet); no family boundary; blocked on: D15 for anything above 2 %; nothing for the merge and the 1 % case (9.206: both 1 % cases removed 114,414-122,192 of 269,690 agents stuck with 81,722-154,759 still en route at 36:00; the network's median link is 65 m and 41 % are under 50 m, so at 0.01 a link stores under a tenth of a vehicle; the live heap is 31 GiB at 1 % and 55 at 2 %; #239)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **Bring the commuter ferry crossings into Mumbai's feed from the Maritime Board directory (Ferry Wharf-Mora/Rewas/Mandwa, Gateway-Mandwa, Versova-Madh, Marve-Manori, Gorai-Borivali, Belapur-Nerul), each on its OSM ferry way or the water line between its jetties, its window from the directory's first and last departures, its vessel capacity through a fleet profile** - a feed-builder change and one mapping of the combined feed (build_matsim_network.py --stage schedules, ~30 min); no arm; the 0.1 % structural check afterwards (6 min); no family boundary; blocked on: nothing (9.206: the extract holds two route=ferry relations (Elephanta, Vasai-Bhayander); the target's port groups (9.205) are the crossings the directory lists and the feed lacks; #245)
5. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D15.** Both 1 % Mumbai cases gridlock with the transit fleet's road space scaled (114,414-122,192 of 269,690 agents removed stuck): at 0.01 every link is a gate of one vehicle per 200 s with storage for one, and 41.5 % of the network's nodes are pass-through, so merging them doubles a 65 m median link to about 130 m - still a sixth of a vehicle's storage at 1 %. Memory is no longer the first constraint (31 GiB at 1 %, 55 at 2 %, 247 at 10 % on this 63 GB host). Which way to a fraction a reading can stand on? Options: Merge the degree-2 link chains and re-run the 1 % case as the diagnostic, then take the host if the stuck share holds · A larger host (cloud or workstation, 384-512 GB) for a 10 % core, after the merge diagnostic (recommended) · Hold Mumbai at the structural checks and finish the reference city first (9.206: two 1 % cases (20260921T231313_4it_1pct, 20260922T005949_4it_1pct); the link-length distribution of scenarios/matsim/BASE/network.xml.gz; the live-set heap rule; #239)

Decided: D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16) · D12 = Hold escort members and joint companions to ride on their bound tours; car-less lift and shared passengers keep walk/bike/pt (recommended) (2026-09-16) · D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21) · D14 = Measure a leaner agent first on a 1 % case, then decide the host (recommended) (2026-09-21)
<!-- generated:lane end -->

Both 1 % cases gridlock (§9.206): the memory is fixed (31 GiB at 1 %) and the flow identity is not — a 65 m median link stores
under a tenth of a vehicle at 0.01. The recommended task merges the degree-2 chains and re-runs the same case; put D15 to the
user at `/onboard`. **The next Newcastle 25 % arm opens a family** (standing room and transit PCE scaled, §9.203, §9.206)
and needs a stated-cost approval.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A pre-collection heap peak measures the heap you GAVE, not the heap you need** (§9.206): under ParallelGC with
   `-Xms = -Xmx`, 16g peaked at 13.74 and 24g at 17.30 on the same population; read the live set after `Pause Full`
   (`N->M`: M). A heap rule built on peaks cost a session's decision.
2. **Transit vehicles at their full PCE on sampled links** (§9.206): a bus took 2.8 of a 1 % lane's 18 vehicles an hour;
   Mumbai's first 1 % case gridlocked on 110,000 bus departures. `RUN.sample.transit_pce_scaling` retires it — but at 1 %
   the second case still lost 43 % of its agents: the fraction, not the PCE, is the wall.
3. **The mapper's vehicle types are defaults, not observations** (§9.206): Bus 70, Rail 400, Subway 300, Ferry 250 seats
   and no standing room shipped in every Mumbai case for two sessions. A city assembly that copies `transitVehicles.xml.gz`
   copies pt2matsim's guesses; declare the fleet.
4. **A detached launch runs under the MACHINE's environment** (§9.206): `CITYSIM_CITY=mumbai python run.py --detach` ran
   Newcastle inside the scheduled task. The wrapper now sets the city; verify a detached launch's `_meta.json` says `city`.
5. **`\d+pct` is not a run name** (§9.206): a fraction below 1 % writes `0.1pct`, and the board and the issue gate could
   not see the first citywide case. Cost: a session's board claiming it labelled every run.
6. **A tiny sample fraction is a queue pathology, not a small city** (§9.205, §9.206): at 0.01 on a 65 m median link one
   car fills the link. Read nothing from a fraction the flow identity cannot carry; the launcher prices it, the reader does
   not refuse it.
7. **A one-byte EOL drift is a manifest failure on every Linux checkout** (§9.204): `normalise_eol.py` before AND after
   `build_manifest.py`, for the city whose artefact changed.
8. **The contract's `required_by` misses keys read on the run path through `config_runtime`** (§9.204): a second city
   passes the contract and fails at launch on a `RegistryError`.
9. **A registry key that no longer exists in a builder's lineage stops the whole chain** (§9.204): grep the city's
   `build/` and `extract/` for a registry file name before moving it.
10. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): run the PDF extractors from PowerShell (MiKTeX 24.04).
Retired by checks: the decimal run name (`test_run_names_admit_a_decimal_percentage.py`), the detached launch's city
(`test_detached_launch_carries_the_city.py`), the unscaled transit PCE (`test_transit_capacity_sampling.py`), the second
city's parallel launcher, a stale framework file on a contract change, CRLF under `data/raw/`, dead-harness detection,
concurrent arms and missing automatic stops, stale family stamps and oversized pages, repeated lane questions.

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT (§9.169, §9.176, §9.177). The two 1 % Mumbai cases
  (1.6 h each) were the lane's measurement under D14, no approval beyond it. The next arm is quoted from its own
  build's probe (`arm_cost.py`, per city) and needs a stated-cost approval; it opens a family.
- **25 % arms only** for Newcastle. A structural smoke may use 1 % (Newcastle) or the 0.1 % `smoke_two_iterations`
  (Mumbai); the 1 % `lean_agent_one_percent` case is a measurement, not a reading. A Mumbai run above the plans'
  0.05 build fraction is refused. One arm at a time; no recompilation under an arm.
- **The user's standing goal (21 September 2026):** a full Mumbai twin, every mode's data acquired; the twelve-mode
  requirements are the validation standard, the broad executable baseline comes first (§9.187). D14 was taken from
  that directive (scale down without compromising any mode's integrity): the leaner agent is measured; D15 is next.
- Compare only within a family, sample fraction and network build. A result requires `_run.json` to say
  `ran_to_last_iteration`; a stopped reading is citable at its `reached_iteration` only.
- The 67/143 holdout stays shut. No invented data; the one assumed transit capacity (`A.transit.bus_capacity_standing`)
  carries its sweep and the reason its derivation is blocked.
- D6–D14 settled in [lane.json](lane.json); D15 open. The TfNSW request is the user's to send (D2).
- Mumbai's `registry/*_framework.json` are regenerated by `cities/mumbai/build/adopt_framework_fields.py` (OVERRIDES hold
  its facts); its fleet by `build_transit_fleet.py`; Mumbai runs through `run.py --scenario BASE --day WEEKDAY
  --run-config <overlay>` after `build_baseline_run_inputs.py`.
- No run while an issue in its lane lacks its required declaration; #237 blocks the Newcastle launcher until the first arm
  after the fix reads it. Declare `answers_issues`.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch after merge.
