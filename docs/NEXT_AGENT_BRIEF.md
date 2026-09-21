# Brief for the next agent

**Written:** 22 September 2026 (fifty-ninth session, continued) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `cccd64c` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle. The newest run on disk is the 0.1 % Mumbai check `20260922T041420_2it_0.1pct` (`ran_to_last_iteration` at 2; the feed with the seven commuter crossings and Metro 2A/7's published windows). The earlier check `20260922T031226_2it_0.1pct` ran all 430 crossing departures. The 1 % cases of §9.206 remain the flow-identity measurement. Newcastle's newest result is `20260916T063903_250it_25pct`. | `python src/run/session_gate.py --digest` |
| The gate passes; both manifests verify (Mumbai 1,397 rows); the separate package audit (#234, #235) is unchanged and unverified. Mumbai's own hardcoding ledger reads 225, all pre-existing (the CI gate runs the reference city only). | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` · `python tests/check_package.py` |
| This session landed two PRs: #247 (`praneetdhoolia/mumbai-ferry-crossings`, merged) and the branch `praneetdhoolia/mumbai-archived-sources-and-metro-windows`: open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/mumbai-archived-sources-and-metro-windows` · `git status --short --branch` |
| 35 open issues after this handoff: #245 closed (the crossings are in the feed, §9.207); #239 carries D15's answer. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered: D15, D16 and D17 were taken 22 September 2026. D16's key (`OGD_API_KEY` in `.env`) and D17's network are the user's to supply. | `python src/analyse/lane.py --ask` |
| 25 report recommendations open. | `python src/analyse/report_recs.py` |
| Registry **574** fields for Newcastle, manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke); Mumbai **412** fields (9 new: the crossing table, seven vessel capacities, the line windows), 1,397 manifest rows, 549 of 597 catalogue sources acquired (22 of them dated Internet Archive copies of refusing publishers, §9.208; 43 unobtained, of which 17 have no capture, 2 wait on the OGD key, 1 is an HTML page where a PDF is published; 5 unusable). | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| The Mumbai run inputs are assembled with the crossings, the 2A/7 windows and the explicit fleet (115,048 vehicles on 17 profiles); a changed capacity field needs `build_transit_fleet.py` then `build_baseline_run_inputs.py`, never a remap. | `CITYSIM_CITY=mumbai PYTHONPATH=src python cities/mumbai/build/build_transit_fleet.py` · `python cities/mumbai/build/build_baseline_run_inputs.py` |
| `src/build/merge_pass_through_nodes.py` is a measurement tool, wired into no build: the network is kept exactly as converted (the user's decision, §9.207). | `python src/build/merge_pass_through_nodes.py cities/mumbai/networks/matsim/base/network.xml.gz <out> --max-length 500` prints the counts |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** **(recommended)** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **Acquire the two OGD daily ridership series (Metro Lines 2A and 7 from 1 January 2024, the Monorail from 1 October 2024) with the registered key, extract them into an observed operator series and re-derive the metro target from them** - minutes once the key is in .env: `acquire_sources.py --id ogd_metro_2a_7_ridership_daily_2024_2025 --id ogd_monorail_ridership_daily_2024_2025`, an extractor, `build_mode_targets.py`; no run; no family boundary; blocked on: D16: the OGD API key (a free registration at data.gov.in) in .env as OGD_API_KEY (9.207: the catalog listing is acquired (ogd_mmrda_ridership_catalog_20260922: two daily CSV resources published by MMRDA on 23 September 2025); the platform sample key answers 429 to everyone;)
5. **Acquire the 17 catalogued sources whose hosts refuse this machine and which the Internet Archive does not hold (the Western Railway attachments, the NMMC plan, MMMOCL ridership, the RDSO 2022 and 2014 specifications, the MRVC CBTC terms, the Maritime Board 2023-24 passenger PDF, the paper hosts, MMRCL station search and train trials, the MahaMetro annual report, the Mumbai City DES page, the census villages download) by a browser capture from a network the hosts admit, imported through import_browser_acquisition.py** - an hour of captures or one scripted pass from the chosen network; no run; no family boundary; blocked on: D17 (taken): a browser capture from a network the hosts admit - a scratch Edge on this machine is refused at the address too (ERR_CONNECTION_TIMED_OUT / REFUSED), so the browser needs an Indian VPN endpoint (9.208: 22 of the 41 refusing sources acquired as dated Internet Archive copies (4 of them empty of content, kept unusable); 17 have no capture; 9.207: the hosts refuse this address under Python, Windows TLS and a real browser;)
6. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21) · D14 = Measure a leaner agent first on a 1 % case, then decide the host (recommended) (2026-09-21) · D15 = A larger host (cloud or workstation, 384-512 GB) for a 10 % core, after the merge diagnostic (recommended) (2026-09-22) · D16 = Register a free OGD account at data.gov.in and put its key in .env as OGD_API_KEY (recommended) (2026-09-22) · D17 = Capture them in a browser and import each through import_browser_acquisition.py (recommended) (2026-09-22)
<!-- generated:lane end -->

The reading Mumbai needs is on the D15 host; nothing on this host reads it. Until the host exists, the
lane's work on this machine is data: D16's key lands the two OGD series in one command; D17's capture
needs a browser on a network the hosts admit (this machine's own browser is refused). **The next
Newcastle 25 % arm opens a family** (standing room and transit PCE scaled, §9.203, §9.206) and needs a
stated-cost approval.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A converted feed is not a mapped feed, and the conversion overwrites the fleet** (§9.207): `--stage schedules`
   writes `transitVehicles.xml.gz` from pt2matsim's defaults at the GTFS step; a session that stops between the
   conversion and the mapping leaves the evidenced fleet gone on disk. Always follow a feed change with the mapping,
   `build_transit_fleet.py` and `build_baseline_run_inputs.py`, in one sitting.
2. **Uncommitted work after a handoff is invisible** (§9.207): the previous session started the next lane item
   after its PR merged and left it in the tree, citing a record section that did not exist. Cost: the onboarding
   had to reconstruct what had run from timestamps. Work after a handoff goes on a branch and its issue, or not at all.
3. **A `<city>` register entry is judged against the reference city's file, not the active city's** (§9.207):
   Mumbai's hardcoding ledger carried 43 "stale" entries for Newcastle-only files. The check now consults the
   reference city; a genuinely stale entry still reports.
4. **A refusing host is refused for the address, not the client** (§9.207): the Mumbai sources time out under
   Python, Windows TLS and a real browser on this machine. Do not retry them from here; the pass takes an hour
   and lands nothing. Ask the Internet Archive first (§9.208: 22 of 41 held); D17's capture needs another network
   for the 17 it does not.
5. **The OGD platform's sample key is everyone's** (§9.207): every call with it answers 429. A keyed entry
   (`api_key_env`) stays unobtained until the registered key is in `.env`.
6. **A pre-collection heap peak measures the heap you GAVE, not the heap you need** (§9.206): read the live set
   after `Pause Full`. A heap rule built on peaks cost a session's decision.
7. **Transit vehicles at their full PCE on sampled links** (§9.206): `RUN.sample.transit_pce_scaling` retires it;
   at 1 % the fraction, not the PCE, is the wall.
8. **The mapper's vehicle types are defaults, not observations** (§9.206): a city assembly that copies
   `transitVehicles.xml.gz` copies pt2matsim's guesses; declare the fleet.
9. **A tiny sample fraction is a queue pathology, not a small city** (§9.205, §9.206): read nothing from a
   fraction the flow identity cannot carry; the merge cannot fix it (median 62.7 → 69.0 m).
10. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): run the PDF extractors from PowerShell.
Retired by checks: the decimal run name, the detached launch's city, the unscaled transit PCE, the second
city's parallel launcher, a stale framework file on a contract change, CRLF under `data/raw/`, dead-harness
detection, concurrent arms and missing automatic stops, stale family stamps and oversized pages, repeated
lane questions, a false stale register entry under a second city.

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT (§9.169, §9.176, §9.177, §9.206). The 0.1 %
  check of this session (8 min) was the lane's structural check, no approval beyond it. The next arm is quoted
  from its own build's probe (`arm_cost.py`, per city) and needs a stated-cost approval; it opens a family.
- **25 % arms only** for Newcastle. A structural smoke may use 1 % (Newcastle) or the 0.1 % `smoke_two_iterations`
  (Mumbai; two ran this session, 8 min each, the lane's structural checks); the 1 % `lean_agent_one_percent` case is a measurement, not a reading, and has been run twice - do
  not run it again on this host. A Mumbai run above the plans' 0.05 build fraction is refused. One arm at a
  time; no recompilation under an arm.
- **The user's standing goal (21 September 2026, restated 22 September):** a full Mumbai twin, every mode's
  data acquired, nothing left unused, unnecessary data and algorithms discarded; the twelve-mode requirements
  are the validation standard, the broad executable baseline first (§9.187). The user's directions of
  22 September: the network stays exactly as converted (no merge); probe the user only with clickable choices.
- Compare only within a family, sample fraction and network build. A result requires `_run.json` to say
  `ran_to_last_iteration`; a stopped reading is citable at its `reached_iteration` only.
- The 67/143 holdout stays shut. No invented data; the one assumed transit capacity (`A.transit.bus_capacity_standing`)
  carries its sweep and the reason its derivation is blocked.
- D6–D17 settled in [lane.json](lane.json); none open. The TfNSW request is the user's to send (D2); the OGD
  key (D16) and the capture network (D17) are the user's to supply.
- Mumbai's `registry/*_framework.json` are regenerated by `cities/mumbai/build/adopt_framework_fields.py`; its
  fleet by `build_transit_fleet.py`; its feed by `build_baseline_transit_feed.py` then ONE mapping
  (`build_matsim_network.py --stage schedules --only baseline_regional`); Mumbai runs through
  `run.py --scenario BASE --day WEEKDAY --run-config <overlay>` after `build_baseline_run_inputs.py`.
- No run while an issue in its lane lacks its required declaration; #237 blocks the Newcastle launcher until
  the first arm after the fix reads it. Declare `answers_issues`.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch after merge.
