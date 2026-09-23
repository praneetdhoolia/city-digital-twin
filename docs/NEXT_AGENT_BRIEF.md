# Brief for the next agent

**Written:** 23 September 2026 (sixty-second session) · **Open family:** `F36-the-passenger-is-held-and-bike-pays-for-distance` · **Commit:** this handoff's
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **F36's arm 0 `20260923T034632_250it_25pct` is RUNNING** (launched 03:46 on 23 September, 250 iterations, 42 h ceiling approved and SPENT on it; at handoff it had ended iteration 126 at 14.04 h, median 411 s). It is NOT a result until `_run.json` says `ran_to_last_iteration`. Do not recompile `.tools/classes` and launch nothing while it runs. | `python src/run/watch_run.py --run 20260923T034632_250it_25pct` · `python src/run/session_gate.py --digest` |
| If its harness died while the JVM reached 250 and shut down cleanly, it is closed out, not re-run. | `python run.py --close-out 20260923T034632_250it_25pct` |
| The probe `20260923T022419_4it_25pct` ran to iteration 4 and is citable for its clock and heap only (§9.212). | `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25` |
| Newcastle's manifest verifies at **959** files. Mumbai's does NOT: 11 gitignored bulk files hash differently from the committed manifest (#252). | `python src/run/session_gate.py` · `CITYSIM_CITY=mumbai python tests/check_manifest.py` |
| This session's one PR (`praneetdhoolia/f36-probe-and-arm-0`): open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/f36-probe-and-arm-0` · `git status --short --branch` |
| 32 open issues; the arm answers #30 #86 #94 #107 #145 #172 #187 #196 #237. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered; the recommended task is `read-f36-arm-0`. | `python src/analyse/lane.py --ask` |
| Registry **575** fields for Newcastle; manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke); Mumbai **428** fields; 19 report recommendations open. | `python src/registry/render_schema.py --check` · `python src/analyse/report_recs.py` |
| The TUS 2024 unit files have still not arrived (the user's browser download). | `ls temp/` |

Then: `python src/run/session_gate.py` (it skips the toolchain compile while the arm runs).

## §1 The lane

<!-- generated:lane start -->
1. **Read F36's arm 0 `20260923T034632_250it_25pct` at its record - all twelve modes with choice-set coverage, and the five measurements the roots rebuild owes: the held passengers (#86, #145), bike's distance cost (#107), the household tail (#196), the ferry on its disclosed tap-ons (#94) and crowding with scaled standing room (#237)** **(recommended)** - no run: `report_mode_ridership.py --run 20260923T034632_250it_25pct --it 250` and `--trend`, `report_choice_set_coverage.py`, `measure_bound_trips.py`, `measure_near_wharf.py`, bike's mean trip by car availability, peak standing occupancy per vehicle type from the it.250 events, the routed short-trip split (#30), the fold's retime counters (#187); then `build_run_index.py` and the board; no family boundary; blocked on: the arm reaching its record - launched 03:46 on 23 September at a 42 h ceiling, ~27-34 h expected; `python src/run/watch_run.py --run 20260923T034632_250it_25pct` says where it is, and `run.py --close-out` applies only if its harness dies while the JVM reaches 250 (9.212: priced by 20260923T022419_4it_25pct at 469.5 s a recurring iteration (+35 %), quote 33.2 h with no milestone; launched at the approved 42 h, mode gate off as the control half (#172); running at handoff, no reading cited; #30 #86 #94 #107 #145 #172 #174 #187 #196 #237)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21) · D14 = Measure a leaner agent first on a 1 % case, then decide the host (recommended) (2026-09-21) · D15 = A larger host (cloud or workstation, 384-512 GB) for a 10 % core, after the merge diagnostic (recommended) (2026-09-22) · D16 = Register a free OGD account at data.gov.in and put its key in .env as OGD_API_KEY (recommended) (2026-09-22) · D17 = Capture them in a browser and import each through import_browser_acquisition.py (recommended) (2026-09-22)
<!-- generated:lane end -->

Watch the arm with ONE monitor on `python src/run/watch_run.py --run 20260923T034632_250it_25pct
--events --read`, re-armed at its 30-minute expiry. Its readings are every 10th iteration; none is
cited before the record (§9.108). When `_run.json` lands, `read-f36-arm-0` is the whole session:
nothing in F36 compares with F35, and this arm is the control every pair is differenced against.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A heredoc hangs the shell, not only corrupts the file** (§9.209, §9.212): this session a
   `cat << 'X'` held a Bash call for its full 120 s timeout. Write any payload to the scratchpad
   with the Write tool and run the file — including JSON rows and record sections.
2. **A lane's cost estimate is not the launcher's** (§9.212): the lane priced the probe at 20-35 min;
   the launcher quoted ~68 min and it took 76 min (setup 29 min, it.0 776 s). Quote the launcher's
   figure to the user, never the lane's.
3. **A four-iteration probe prices high, not low** (§9.212, §9.169): it recurred at 469.5 s while the
   arm's median settled near 411 s. Set the ceiling on the quote plus the milestones; do not tighten
   it to a mid-run projection.
4. **A "byte-identical" refactor that was never executed end to end** (§9.211): the 16 September
   staging of `build_matsim_plans.py` raised `UnboundLocalError` on the first external person six
   days later. A refactor's proof is a RUN of it.
5. **A patch prepared on an issue must be re-anchored before it is applied** (§9.211): one of five
   prepared anchors no longer matched. Check every `old = ...` literal against today's source.
6. **A keyed failure quotes its URL** (§9.209): never print a request URL; `acquire_sources.py`
   redacts.
7. **`render_schema.py` writes the contract from the ACTIVE city** (§9.209): run schema and
   registry tools under `CITYSIM_CITY=newcastle`.
8. **A converted feed is not a mapped feed, and the conversion overwrites the fleet** (§9.207):
   follow a feed change with the mapping, `build_transit_fleet.py` and `build_baseline_run_inputs.py`.
9. **A deleted branch leaves its BUILT BYTES behind** (§9.207): that is how Mumbai's 11 manifest
   failures got there (#252).
10. **A pre-collection heap peak measures the heap you GAVE** (§9.206): read the live set after
    `Pause Full`, as `gc.log` states it in MB.

Retired by checks: a launch verified against the previous run (`verify_launch.py --stamp`, printed
by `run.py --detach`), a watcher reporting a run in setup as dead or dying on a half-written table
(`watch_run.py`, §9.212), the position pages' caps and family stamps, the board's generated blocks,
concurrent arms, missing automatic stops, repeated lane questions.

## §3 Standing directives and approvals

- **No run approval stands.** The 42 h of 23 September is SPENT on `20260923T034632_250it_25pct`.
  Every earlier approval is SPENT. The next arm (a pair differenced against this one) needs its own
  stated-cost approval, quoted by `arm_cost.py` from THIS arm's stopwatch once it lands.
- **25 % arms only** for Newcastle; a structural smoke may use 1 %. One arm at a time; never
  recompile `.tools/classes` under one; run anything heavy at below-normal priority, or not at all,
  while an arm runs (§9.177).
- **The user's direction of 23 September:** continue tuning and benchmarking Newcastle; keep
  monitoring the arm and report each substantive reading; hand off with the arm still running.
- **The user's standing goal** (21-22 September): a full Mumbai twin with every mode's data acquired;
  the broad executable baseline first (§9.187); Mumbai's 10 % probe waits on the D15 host.
- Compare only within a family, fraction and network build. **F35 is closed**: its three results
  compare with nothing after `20260922T210005`. The 67/143 holdout stays shut. No invented data.
- D6-D17 are settled in [lane.json](lane.json); none open. The TfNSW request is the user's to send
  (D2); the TUS unit files are the user's browser download.
- Never commit to `main`. Land a session through one PR targeting `main`; delete its branch after
  merge.
