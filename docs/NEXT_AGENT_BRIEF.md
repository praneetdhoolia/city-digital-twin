# Brief for the next agent

**Written:** 22 September 2026 (sixtieth session) · **Open family:** `F35-the-engines-route-what-they-remode` · **Commit:** `4e53cfa8` plus this handoff's commits
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle. The newest run on disk is the 0.1 % Mumbai check `20260922T162633_2it_0.1pct` (`ran_to_last_iteration` at 2: the timetable feed, the projected vehicles, the weighted destinations and the graded network, §9.209). The 1 % cases of §9.206 remain the flow-identity measurement. Newcastle's newest result is `20260916T063903_250it_25pct`. | `python src/run/session_gate.py --digest` |
| The gate passes; both manifests verify (Mumbai 1,453 rows). The separate package audit (#234, #235) is unchanged and unverified. Mumbai's hardcoding ledger reads 225, all pre-existing (the CI gate runs the reference city only). | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` · `python tests/check_package.py` |
| This session's PR from `praneetdhoolia/mumbai-acquisitions-and-data-use`: open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/mumbai-acquisitions-and-data-use` · `git status --short --branch` |
| 35 open issues after this handoff; #239 carries §9.209's state. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered: D15, D16 and D17 were taken 22 September 2026. D16 is done (`OGD_API_KEY` in `.env`); D17 is done for 20 of 41 sources through the user's Indian VPN endpoint. | `python src/analyse/lane.py --ask` |
| 25 report recommendations open. | `python src/analyse/report_recs.py` |
| Registry **574** fields for Newcastle, manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke); Mumbai **428** fields, 1,453 manifest rows, 600 catalogue sources: 570 acquired, 24 unobtained (each with the host's answer), 6 unusable; **0 unread** (`source_use.json`). | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` · `CITYSIM_CITY=mumbai python cities/mumbai/extract/audit_source_use.py` |
| The Mumbai run inputs are assembled on the printed-timetable feed (3,289 trains, 3,798 routes, 116,183 vehicles on 17 profiles) with 788,523 graded links. A feed or registry change needs `build_baseline_transit_feed.py` → `build_regional_bus_feed.py` → ONE mapping → `build_transit_fleet.py` → `build_baseline_run_inputs.py`, in one sitting. | `CITYSIM_CITY=mumbai PYTHONPATH=src python cities/mumbai/build/build_baseline_run_inputs.py` |
| The user's browser downloads (`Downloads/city-twin-captures/`: the two OGD ridership CSVs, the TUS 2024 unit files) have not arrived. | `ls "C:/Users/Praneet Dhoolia/Downloads/city-twin-captures"` |
| The `.env` holds `TFNSW_API_KEY`, `OGD_API_KEY`, `MOSPI_MICRODATA_EMAIL`, `MOSPI_MICRODATA_PASSWORD`; none is ever written into a log or the catalogue (`redact_api_keys`). | `grep -o '^[A-Z_]*=' .env` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** **(recommended)** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **Import the two OGD daily ridership series (Metro Lines 2A and 7 from 1 January 2024, the Monorail from 1 October 2024) from the user's logged-in browser download, extract them into an observed operator series and re-derive the metro target from them** - minutes once the two CSVs are in Downloads/city-twin-captures: an import path for a portal download, an extractor, build_mode_targets.py; no run; no family boundary; blocked on: the user's browser: the OGD platform serves the two resources as datafiles (is_api_available 0) behind a logged-in download form with a captcha; the API answers 502 for them with the registered key (D16 done: OGD_API_KEY is in .env) (9.209: the key is registered and in .env; api.data.gov.in answers 502 after 62 s for both resource ids at any page size, and the resource listing says is_api_available 0; the two CSVs (13 KB) download only from the logged-in portal; 9.207: the catalog listing is acquired (ogd_mmrda_ridership_catalog_20260922: two daily CSV resources published by MMRDA on 23 September 2025); the platform sample key answers 429 to everyone;)
5. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the NADA portal login form carries an image captcha; the account exists (MOSPI_MICRODATA_EMAIL in .env) (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
6. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
7. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
8. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21) · D14 = Measure a leaner agent first on a 1 % case, then decide the host (recommended) (2026-09-21) · D15 = A larger host (cloud or workstation, 384-512 GB) for a 10 % core, after the merge diagnostic (recommended) (2026-09-22) · D16 = Register a free OGD account at data.gov.in and put its key in .env as OGD_API_KEY (recommended) (2026-09-22) · D17 = Capture them in a browser and import each through import_browser_acquisition.py (recommended) (2026-09-22)
<!-- generated:lane end -->

The Mumbai reading is on the D15 host; nothing on this host reads it. The user chose four scopes on
22 September 2026 (the data-use ledger, the source research, the Java fold, the three inputs); the
fold was not started and is the unblocked next item. Do OGD and MoSPI work with the user's VPN OFF and
Indian-host acquisitions with it ON, batched, asking the user to toggle.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A heredoc payload with a backslash silently corrupts the file** (§9.209): a `python - <<'EOF'` patch
   whose regex held `\b` wrote literal backspace characters, so `NODE_RE` matched nothing and the gradient
   stamp stamped 0 links; found only by reading the assembly report. Every patch whose payload contains a
   backslash goes through the Write tool as a scratchpad `.py` and runs as a file.
2. **A keyed failure quotes its URL** (§9.209): the first OGD attempt wrote the API key into
   `_acquisition_attempts.json`; scrubbed, and `acquire_sources.py` now redacts. Never print a request URL.
3. **`render_schema.py` writes the contract from the ACTIVE city** (§9.209): run under `CITYSIM_CITY=mumbai`
   it rewrote `required_fields.json` from Mumbai's registry (574 → 428 keys); restored from git. The contract
   is the reference city's - run schema tools under `newcastle`.
4. **An id-level trace of "which source is read" overcounts** (§9.209): adapters read by glob and by path, and
   `data/raw/<category>/` as a literal matches everything. `audit_source_use.py` matches OUTPUT_INPUTS globs,
   whole ids, basenames and globs with six fixed characters; an audit script's read is `audited`, not consumed.
5. **The harness refuses TLS-weakening code** (§9.209): a hostname waiver or `verify=False` for the mahades and
   mcap certificates is denied by the classifier; leave such hosts unobtained with the reason.
6. **A converted feed is not a mapped feed, and the conversion overwrites the fleet** (§9.207): always follow a
   feed change with the mapping, `build_transit_fleet.py` and `build_baseline_run_inputs.py`, in one sitting.
7. **Uncommitted work after a handoff is invisible** (§9.207): work after a handoff goes on a branch and its
   issue, or not at all.
8. **A pre-collection heap peak measures the heap you GAVE** (§9.206): read the live set after `Pause Full`.
9. **A tiny sample fraction is a queue pathology, not a small city** (§9.205, §9.206): read nothing from a
   fraction the flow identity cannot carry.
10. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): run the PDF extractors from PowerShell.
Retired by checks: a `<city>` structural entry stale under the other city (the register is judged against
every city's file, §9.209), the decimal run name, the detached launch's city, the unscaled transit PCE,
the second city's parallel launcher, a stale framework file on a contract change, CRLF under `data/raw/`,
dead-harness detection, concurrent arms and missing automatic stops, stale family stamps and oversized
pages, repeated lane questions.

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT (§9.169, §9.176, §9.177, §9.206). The two
  0.1 % checks of this session (8 min each) were the lane's structural checks, no approval beyond them. The
  next arm is quoted from its own build's probe (`arm_cost.py`, per city) and needs a stated-cost approval; it
  opens a family.
- **25 % arms only** for Newcastle. A structural smoke may use 1 % (Newcastle) or the 0.1 %
  `smoke_two_iterations` (Mumbai); the 1 % `lean_agent_one_percent` case is a measurement, run twice - do not
  run it again on this host. A Mumbai run above the plans' 0.05 build fraction is refused. One arm at a time;
  no recompilation under an arm.
- **The user's standing goal (21 September 2026, restated 22 September):** a full Mumbai twin, every mode's
  data acquired, nothing left unused, unnecessary data and algorithms discarded; the twelve-mode requirements
  are the validation standard, the broad executable baseline first (§9.187). The user's directions of
  22 September: the network stays exactly as converted (no merge); probe the user only with clickable choices;
  the four scopes above.
- Compare only within a family, sample fraction and network build. A result requires `_run.json` to say
  `ran_to_last_iteration`; a stopped reading is citable at its `reached_iteration` only.
- The 67/143 holdout stays shut. No invented data; the assumed values introduced this session
  (`B.activities.attraction_radius_m`, `A.gradient.grade_clamp_pct` for Mumbai) carry sweeps; the derived ones
  (`B.activities.own_account_job_share`, the possession growth table, the 15-car capacities) their identities.
- D6–D17 settled in [lane.json](lane.json); none open. The TfNSW request is the user's to send (D2); the OGD
  CSVs and the TUS unit files are the user's browser downloads.
- Mumbai's `registry/*_framework.json` are regenerated by `cities/mumbai/build/adopt_framework_fields.py`
  (its GATES turn a mechanism on or off: `A.gradient.representation` is `link_speed` now); its fleet by
  `build_transit_fleet.py`; its suburban trains by `build_suburban_timetable_feed.py`; its feed by
  `build_baseline_transit_feed.py` then ONE mapping; Mumbai runs through `run.py --scenario BASE --day WEEKDAY
  --run-config <overlay>` after `build_baseline_run_inputs.py`.
- No run while an issue in its lane lacks its required declaration; #237 blocks the Newcastle launcher until
  the first arm after the fix reads it. Declare `answers_issues`.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch after merge.
