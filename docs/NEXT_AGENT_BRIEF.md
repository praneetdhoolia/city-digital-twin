# Brief for the next agent

**Written:** 27 September 2026 (sixty-fourth session) · **Open family:** `F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen` · **Commit:** this handoff's
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **F38's arm 0 `20260927T145839_250it_25pct` is RUNNING** (launched 14:58 on 27 September, overlay `f38_baseline_25pct`, 250 iterations, 34 h ceiling approved by D23 and SPENT on it; the probe quoted 32.0 h, F37's identical quote delivered 31.4 h). NOT a result until `_run.json` says `ran_to_last_iteration`. Do not recompile `.tools/classes`, launch nothing, and keep heavy work at below-normal priority while it runs. | `python src/run/watch_run.py --run 20260927T145839_250it_25pct` · `python src/run/session_gate.py --digest` |
| **F37's arm 0 `20260926T002526_250it_25pct` is a RESULT** (`ran_to_last_iteration` at 250): 2 of 12 inside 10 %, read in §9.214 and on the board. | `python src/analyse/report_mode_ridership.py --run 20260926T002526_250it_25pct --it 250` |
| Windows Update is paused until **2 October 2026 21:28 AEST** (the user's pause, D19); the launcher refuses any launch whose ceiling outlasts it. | `python -c "import sys; sys.path.insert(0,'src/run'); import procs,time; print(time.ctime(procs.updates_paused_until()))"` |
| The F38 probe `20260927T133754_4it_25pct` (454.0 s recurring) and smoke `20260927T133104_2it_1pct` are citable for clock, heap and plumbing only. | `python src/analyse/arm_cost.py --run-config f38_baseline_25pct` |
| Registry **587** fields for Newcastle; manifest **967** files (**732 CC-BY / 220 ODbL** + 15 bespoke), verifying. Mumbai's manifest still does not verify (#252). | `python src/run/session_gate.py` · `python src/registry/render_schema.py --check` |
| This session's one PR (`praneetdhoolia/f37-quality-to-four`): open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/f37-quality-to-four` |
| 31 open issues; 15 await a run with a stated measurement, re-aimed at F38's arm 0 (#30 #86 #94 #107 #145 #162). | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered (D23 answered this session); the recommended task is `read-f38-arm-0`. | `python src/analyse/lane.py --ask` |

Then: `python src/run/session_gate.py` (it skips the toolchain compile and the Java probes while the arm runs).

## §1 The lane

<!-- generated:lane start -->
1. **Read F38's arm 0 at its record: all twelve modes with choice-set coverage against F37's result as a direction; walk's mean trip against 4.08 km and walk km inside held-ride tours against 35.6 %; the car-less split and trip lengths (bike 11.8 km, walk 6.0 km); heavy-rail station entries against 17,016 and access walks over 2 km against 19.5 %; motorbike CHOSEN against 0.3785 %; ride with the doubled lifts against -13.5 %; taxi against +129.6 %; the no-route share against 52.1 %** **(recommended)** - no run: `report_mode_ridership.py --run 20260927T145839_250it_25pct --it 250` and `--trend`, `report_choice_set_coverage.py --against-targets`, `mode_by_demographics.py`, `measure_bound_trips.py`, `diagnose_pt_routing.py --sample 3000`, `fit.py`; then `build_run_index.py`, the board and a fresh /project-report; no family boundary; blocked on: the arm reaching its record (overlay `f38_baseline_25pct`, 34 h ceiling approved 27 September 2026, D23) (9.214; #30 #86 #94 #98 #107 #145 #162 #257)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **Attach trip ends to links that can carry them: on F37's arm 0, 29 links (28 service lanes, one living street) carry 23,161 sampled road-vehicle trip ends needing up to 38 hours of their own sampled capacity, and the 2.7 % of road trips touching them average 72.6 min at 13.4 km/h against 25.5 min elsewhere; 73 % of the run's excess vehicle-hours sit on residential and service links carrying ~13 % of traversals. Design a capacity-aware citysim.ActivityLinkAssigner rule (no link receives more trip ends than it can move in the modelled day, excess moved to the next-nearest eligible links), derived, behind a representation gate, and measure the car time tail against the HTS 17.2 min** - no run to design: the trip-end load per link and the car time by load band from any finished arm's trips table and output network (scratch access_load.py and delay_links.py, to be folded into an existing reader); the Java change compiles only on an idle machine and opens a family; opens a family; blocked on: F38's arm 0 reading (the car time tail on the new demand), then a user decision on the next family's contents (9.214 (F37 arm 0: car mean 25.0 min for 11.88 km against the HTS 17.2 min for 10.2 km; median 12.6 min; 9.8 % of car trips under 15 km/h carry 32.4 % of car time, spread over the whole day); #145)
7. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D19 = I pause updates; launcher checks (recommended) (2026-09-25) · D20 = Move to settings.local.json (recommended) (2026-09-25) · D21 = Before the F37 launch (recommended) (2026-09-25) · D22 = In F38, after F37 reads (recommended) (2026-09-25) · D23 = All three, then the arm (Recommended) (2026-09-27)
<!-- generated:lane end -->

Watch the arm with ONE monitor on `python src/run/watch_run.py --run 20260927T145839_250it_25pct
--events --read`, re-armed at its 30-minute expiry. When `_run.json` lands, `read-f38-arm-0` is the
session, then a fresh `/project-report` on that reading. The scratch diagnostics that traced F37
(walk trips by tour context, rail entries by car access and access-walk band) are in §9.214; if
they are needed again, codify them in `iteration_reading.py` rather than re-writing them.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A demand rebuild moves the measured access reach** (§9.214): the assembler refused the F38 run
   inputs because a Saturday activity sat 55,668 m from its nearest stop; re-measure over every
   scenario and day and re-declare `RUN.transit_router.access_max_radius_m` (reach + 200).
2. **The chains build doubles under the mobility kernel** (§9.214): ~85 min, not ~90 s; a `timeout`
   wrapper killed it after the weekday and left SAT and SUN stale. Never wrap a build in `timeout`.
3. **A shell that reads stdin hangs for its full timeout** (§9.213, again §9.214): no heredoc, no
   `python -`, `< /dev/null` on every python call; payloads through the Write tool or the Edit tool.
4. **A module can redefine a name further down** (§9.213): grep the module for a name before adding one.
5. **A JSON writer at the wrong indent rewrites the whole file** (§9.213): read the file's own indent.
6. **A refactor is proven by a run, and only the integers are exact** (§9.213, §9.211): diff
   counters and bytes, never floats, and say so.
7. **A probe prices high, not low** (§9.212, §9.213): set the ceiling on the quote plus milestones.
8. **A patch prepared on an issue must be re-anchored before it is applied** (§9.211).
9. **A keyed failure quotes its URL** (§9.209): never print a request URL.
10. **`render_schema.py` writes the contract from the ACTIVE city** (§9.209): run it under
    `CITYSIM_CITY=newcastle`.

Retired by checks this session: a host restart under an arm (`refuse_unsafe_host`), a stop that kills
a recycled pid (`procs.card_pid_alive`), a close-out that cannot read a stopped arm
(`iterations_with`), a price inflated by a dead host (`launch_to_first_iteration_s`), a credential in
a tracked file (`tests/check_secrets.py`, `.githooks/pre-commit`), Java probes nobody ran (the gate's
`java probes`), a plan that loses a tier (the plans builder refuses).

## §3 Standing directives and approvals

- **No run approval stands.** The 34 h of 27 September (D23) is SPENT on `20260927T145839_250it_25pct`.
  The next arm needs its own stated-cost approval, quoted by `arm_cost.py` from this arm's stopwatch.
- **25 % arms only** for Newcastle; a structural smoke may use 1 %. One arm at a time.
- **The user pauses Windows Update before a launch** (D19); never change the update settings yourself.
- **The user's goal (25 September 2026):** the simulator tuned as close as possible to a real-life
  replica from real data; every report criterion at 4/5 or better; modes chosen by the simulated
  population, never thrown in. Motorbike is a choice since F38 (D22, §9.214).
- Compare only within a family, fraction and network build. F37's result is read against F38's as a
  direction only; F36 closed with no result. The 67/143 holdout stays shut.
- Never commit to `main`; one PR per session, based on `main`.
