# Brief for the next agent

**Written:** 22 September 2026 (sixty-first session) · **Open family:** `F36-the-passenger-is-held-and-bike-pays-for-distance` · **Commit:** this handoff's
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| Machine idle; **no run has executed on F36's demand**. The newest run on disk is the 1 % Newcastle smoke `20260922T172813_4it_1pct` (`ran_to_last_iteration` at 4, §9.210), which belongs to F35 and reads nothing here. Newcastle's newest RESULT is `20260916T063903_250it_25pct` inside the CLOSED F35. | `python src/run/session_gate.py --digest` · `python src/run/watch_run.py --run <name>` |
| The gate passes. Newcastle's manifest verifies at **959** files. **Mumbai's manifest does NOT**: 11 gitignored bulk files (the schedules, the mapped `baseline_regional` set, `population_WEEKDAY`, `BASE/network`, the WEEKDAY config/schedule/vehicles) were rebuilt at 18:07–18:14 on 22 September by an abandoned branch and hash differently from the committed manifest. | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` |
| The package audit's run-input report coverage is RESTORED (#235: S0–S6 and every day type). It still fails on stale document paths (#234) and on Mumbai run cards judged against the reference city's scenario list. | `python tests/check_package.py` |
| This session's one PR (`praneetdhoolia/roots-rebuild`): open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/roots-rebuild` · `git status --short --branch` |
| 32 open issues; #30 #86 #94 #107 #145 #196 #237 all now carry their measurement on F36's arm 0. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered. The lane's recommendation moved from the blocked Mumbai host probe to `f36-probe-and-arm-0`. | `python src/analyse/lane.py --ask` |
| Registry **575** fields for Newcastle (the new one is `C.scoring.marginal_utility_of_distance_per_m`); manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke); Mumbai **428** fields, 1,459 manifest rows, 0 unread sources. | `python src/registry/render_schema.py --check` · `python src/registry/render_docs.py --check` |
| The rebuilt WEEKDAY demand: 616,040 persons, 2,331,650 selected-plan legs, 1,095,994 tours; 276,816 held ride trips on 141,633 persons; the ferry target 790.285 boardings/weekday. | `python -c "import json;print(json.load(open('cities/newcastle/demand/plans/matsim/_plans_report.json'))['by_day']['WEEKDAY']['bound_placement'])"` |
| The TUS 2024 UNIT files have still not arrived (the user's first download held the documentation only). | `ls temp/` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **Price F36's arm 0 on the rebuilt demand: a 25 % probe of a few iterations for the per-iteration clock and the live-set heap, then the arm at a stated cost - the first run to read the held passengers (#86), bike's distance cost (#107), the derived household tail (#196), the ferry on its disclosed tap-ons (#94) and scaled standing room (#237)** **(recommended)** - a 25 % probe of 2-4 iterations (about 20-35 min on the scoring pair's clock) for the price, then arm 0 at 250 iterations - quoted 25.1 h, spread 24.5-32.8 h, on the PREVIOUS build's stopwatch, which is not a price for this one (`python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); no family boundary; blocked on: a stated-cost approval from the user for the arm; the probe itself is short and is what produces the quote (9.211: the demand is rebuilt and F36 is open at 20260922T210005; 276,816 held ride trips on 141,633 persons, bike at -0.000192308 utils/m, the drawn top band 6.596 against 6.6, the ferry target 790 boardings/weekday (sweep 234-1,347), the placed short-trip band 17.81 %; no run has executed on these inputs; #30 #86 #94 #107 #145 #172 #196 #237)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21) · D14 = Measure a leaner agent first on a 1 % case, then decide the host (recommended) (2026-09-21) · D15 = A larger host (cloud or workstation, 384-512 GB) for a 10 % core, after the merge diagnostic (recommended) (2026-09-22) · D16 = Register a free OGD account at data.gov.in and put its key in .env as OGD_API_KEY (recommended) (2026-09-22) · D17 = Capture them in a browser and import each through import_browser_acquisition.py (recommended) (2026-09-22)
<!-- generated:lane end -->

F36 is open at the demand rebuild and has no reading, so its first act is **its own 25 % probe**: the
committed controler differs from the newest priced arm's, so no existing quote is a price for this
build. The arm then carries five measurements at once. Mumbai's 10 % probe stays blocked on the D15
host the user is procuring; its task keeps its place and returns to the top when the host lands.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A "byte-identical" refactor that was never executed end to end** (§9.211): the 16 September
   staging of `build_matsim_plans.py` returned three locals bound only on the resident branch, so
   the builder raised `UnboundLocalError` on the first external, motorbike or freight person — six
   days after the commit said byte-identical. A refactor's proof is a RUN of it, not its diff; the
   audit that found all three at once is an AST pass for a returned name assigned only inside a
   branch.
2. **A heredoc payload with a backslash silently corrupts the file** (§9.209, hit again this
   session): a `python - <<'EOF'` patch carrying `\n` inside a string wrote a literal `\n` into the
   source. Every patch whose payload contains a backslash goes through the Write tool as a
   scratchpad `.py` and runs as a file.
3. **A patch prepared on an issue must be re-anchored before it is applied** (§9.211): of the five
   prepared F-scripts, one anchor (`F3`'s end marker) no longer matched the file. Check every
   `old = ...` literal against today's source before running any of them.
4. **A keyed failure quotes its URL** (§9.209): never print a request URL; `acquire_sources.py`
   redacts.
5. **`render_schema.py` writes the contract from the ACTIVE city** (§9.209): run schema and registry
   tools under `CITYSIM_CITY=newcastle`, or `required_fields.json` is rewritten from Mumbai's 428.
6. **The harness refuses TLS-weakening code** (§9.209): leave a mis-certificated host unobtained
   with the reason.
7. **A converted feed is not a mapped feed, and the conversion overwrites the fleet** (§9.207):
   follow a feed change with the mapping, `build_transit_fleet.py` and `build_baseline_run_inputs.py`,
   in one sitting.
8. **Uncommitted work after a handoff is invisible** (§9.207) — and worse, a deleted branch leaves
   its BUILT BYTES behind: that is exactly how Mumbai's 11 manifest failures got there.
9. **A pre-collection heap peak measures the heap you GAVE** (§9.206): read the live set after
   `Pause Full`.
10. **`pdftotext` on Git Bash's PATH is poppler 4.00** (§9.201): run the PDF extractors from
    PowerShell.

Retired by checks: the position pages' caps and family stamps, the board's generated blocks, a
stale `<city>` register entry, the decimal run name, the detached launch's city, the unscaled
transit PCE, dead-harness detection, concurrent arms, missing automatic stops, repeated lane
questions.

## §3 Standing directives and approvals

- **No run approval stands.** Every previous approval is SPENT. F36's arm needs a stated-cost
  approval, quoted from F36's OWN probe (`python src/analyse/arm_cost.py --iterations 250
  --fraction 0.25` reads the previous build's stopwatch and is not a price for this one).
- **25 % arms only** for Newcastle; a structural smoke may use 1 %. Mumbai's `smoke_two_iterations`
  is 0.1 %; a Mumbai run above the plans' 0.05 build fraction is refused. One arm at a time; never
  recompile `.tools/classes` under one.
- **The user's standing goal** (21 September, restated 22 September): a full Mumbai twin, every
  mode's data acquired, nothing unused; the twelve-mode requirements are the validation standard and
  the broad executable baseline comes first (§9.187). The user's direction of 22 September evening:
  **continue tuning the Newcastle simulator** — which is what §9.211 is.
- Compare only within a family, fraction and network build. **F35 is closed**: its three results
  compare with nothing after `20260922T210005`. A result requires `_run.json` to say
  `ran_to_last_iteration`.
- The 67/143 holdout stays shut. No invented data: this session's new values are DERIVED with their
  identities (bike's distance cost from the observed mean; the household tail from the declared
  top-band mean) or MEASURED (the ferry target from 300 disclosed weekdays).
- D6–D17 are settled in [lane.json](lane.json); none open. The TfNSW request is the user's to send
  (D2); the TUS unit files are the user's browser download.
- Never commit to `main`. Land the session through one PR targeting `main` and delete its branch
  after merge.
