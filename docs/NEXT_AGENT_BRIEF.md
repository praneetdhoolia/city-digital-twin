# Brief for the next agent

**Written:** 25 September 2026 (sixty-third session) · **Open family:** `F37-the-boundary-tier-returns-and-pt-reaches-every-stop` · **Commit:** this handoff's
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **F37's arm 0 `20260925T230246_250it_25pct` is RUNNING** (launched 23:02 on 25 September, overlay `f37_baseline_25pct`, 250 iterations, 34 h ceiling approved and SPENT on it; the probe quoted 32.0 h, and probes have over-priced by 18–26 %). NOT a result until `_run.json` says `ran_to_last_iteration`. Do not recompile `.tools/classes`, launch nothing, and keep heavy work at below-normal priority while it runs. | `python src/run/watch_run.py --run 20260925T230246_250it_25pct` · `python src/run/session_gate.py --digest` |
| Windows Update is paused until **2 October 2026 21:28 AEST** (the user's pause, D19); the launcher refuses any launch whose ceiling outlasts it. | `python -c "import sys; sys.path.insert(0,'src/run'); import procs,time; print(time.ctime(procs.updates_paused_until()))"` |
| F36 closed with NO result: arm 0 `20260923T034632_250it_25pct` was stopped at 237 by a host restart and is read at iteration 230. | `cat results/processed/20260923T034632_250it_25pct/_run.json` |
| The F37 probe `20260925T214314_4it_25pct` ran to 4 and is citable for its clock and heap only. | `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25` |
| Registry **579** fields for Newcastle; manifest **959** files (**724 CC-BY / 220 ODbL** + 15 bespoke), verifying. Mumbai's manifest still does not verify (#252). | `python src/run/session_gate.py` · `python src/registry/render_schema.py --check` |
| This session's one PR (`praneetdhoolia/f36-read-and-gold-standard`): open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/f36-read-and-gold-standard` |
| 30 open issues; 15 await a run with a stated measurement, most of them F37's arm 0. | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered (D18–D22 answered this session); the recommended task is `read-f37-arm-0`. | `python src/analyse/lane.py --ask` |

Then: `python src/run/session_gate.py` (it skips the toolchain compile and the Java probes while the arm runs).

## §1 The lane

<!-- generated:lane start -->
1. **Read F37's arm 0 at its record: all twelve modes with choice-set coverage; the no-route share of pt requests against 66.3 % on F36 (the `ptDirectWalk` counter); walk's and pt's mean trip; the car-less split; taxi with its wait executed; the external tier's boundary trips** **(recommended)** - no run: `report_mode_ridership.py --run <arm> --it 250` and `--trend`, `report_choice_set_coverage.py`, `mode_by_demographics.py`, `measure_bound_trips.py`, `diagnose_pt_routing.py --sample 3000`; then `build_run_index.py` and the board; no family boundary; blocked on: the arm reaching its record (overlay `f37_baseline_25pct`, 34 h ceiling approved 25 September 2026) (9.213; #30 #86 #94 #107 #145 #162 #172 #187 #237)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **Explain the ~39 % of pt trips with no connection even without the access cap: split the no-route requests by trip-end distance band and by transfer-walk radius (300/500/800 m) in `diagnose_pt_routing.py`, read-only on F37 arm 0** - no run; ~1 h offline re-route of 3,000 trips per radius; no family boundary; blocked on: F37 arm 0 for the plans it reads (F36 arm 0 works today) (9.213: 78 % of the offline no-routes persist at 15:00; #162)
7. **Make motorbike a choice (D22): motorbike availability from the registration stock per household, then chosen like any mode; retire the target-share carve of 9.52** - a build change and a plans rebuild (~1 h), a 1 % smoke; opens F38; opens a family; blocked on: F37 arm 0 read first (D22) (9.213, D22; 9.52;)
8. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D18 = Open F37 on the fixes (recommended) (2026-09-25) · D19 = I pause updates; launcher checks (recommended) (2026-09-25) · D20 = Move to settings.local.json (recommended) (2026-09-25) · D21 = Before the F37 launch (recommended) (2026-09-25) · D22 = In F38, after F37 reads (recommended) (2026-09-25)
<!-- generated:lane end -->

Watch the arm with ONE monitor on `python src/run/watch_run.py --run 20260925T230246_250it_25pct
--events --read`, re-armed at its 30-minute expiry. When `_run.json` lands, `read-f37-arm-0` is the
session: the no-route share (66.3 % on F36; 56.0 % at the probe's first 200,000 requests), walk's
mean trip (4.54 km on F36), taxi with its wait executed, and the external tier's boundary trips.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A shell that reads stdin hangs for its full timeout** (§9.213): four hangs this session - two
   heredocs, a bare `python -`, a bare `cat`. No heredoc, no `python -`; `< /dev/null` on every python
   call; payloads with quotes go through the Write tool and a script file, or the Edit tool.
2. **A module can redefine a name further down** (§9.213): a new `_ATTR` regex in
   `iteration_reading.py` was overwritten by the events parser's own `_ATTR` at import and every person
   read came back empty. Grep the module for the name before adding one.
3. **A JSON writer at the wrong indent rewrites the whole file** (§9.213): the families ledger became a
   487-line diff at `indent=1`; it is `indent=2`. Read the file's own indent before dumping.
4. **A refactor is proven by a run, and only the integers are exact** (§9.213, §9.211): the ride split
   matched the pre-split engine on every iteration-0 counter, while detour means moved by a second
   within MATSim's routing noise. Diff counters, never floats, and say so.
5. **A probe prices high, not low** (§9.212, §9.213): F36's probe 469.5 s against its arm's 349.5 s.
   Set the ceiling on the quote plus the milestones.
6. **A lane's cost estimate is not the launcher's** (§9.212): quote the launcher's figure.
7. **A patch prepared on an issue must be re-anchored before it is applied** (§9.211).
8. **A keyed failure quotes its URL** (§9.209): never print a request URL.
9. **`render_schema.py` writes the contract from the ACTIVE city** (§9.209): run it under
   `CITYSIM_CITY=newcastle`.
10. **A converted feed is not a mapped feed** (§9.207): follow a feed change with the mapping,
    `build_transit_fleet.py` and `build_baseline_run_inputs.py`.

Retired by checks this session: a host restart under an arm (`refuse_unsafe_host`), a stop that kills
a recycled pid (`procs.card_pid_alive`), a close-out that cannot read a stopped arm
(`iterations_with`), a price inflated by a dead host (`launch_to_first_iteration_s`), a credential in
a tracked file (`tests/check_secrets.py`, `.githooks/pre-commit`), Java probes nobody ran (the gate's
`java probes`), a plan that loses a tier (the plans builder refuses).

## §3 Standing directives and approvals

- **No run approval stands.** The 34 h of 25 September is SPENT on `20260925T230246_250it_25pct`.
  The next arm needs its own stated-cost approval, quoted by `arm_cost.py` from this arm's stopwatch.
- **25 % arms only** for Newcastle; a structural smoke may use 1 %. One arm at a time.
- **The user pauses Windows Update before a launch** (D19); never change the update settings yourself.
- **The user's goal (25 September 2026):** the simulator tuned as close as possible to a real-life
  replica from real data; every report criterion at 4/5 or better; modes chosen by the simulated
  population, never thrown in. Motorbike becomes a choice in F38 (D22), after F37 reads.
- Compare only within a family, fraction and network build. F36 closed with no result; F35's three
  results compare with nothing after `20260922T210005`. The 67/143 holdout stays shut.
- Never commit to `main`; one PR per session, based on `main`.
