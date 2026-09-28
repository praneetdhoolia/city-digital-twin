# Brief for the next agent

**Written:** 29 September 2026 (sixty-fourth session) · **Open family:** `F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk` · **Commit:** this handoff's
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **F39's control arm `20260929T072135_250it_25pct` RUNS** (launched detached 07:21 on 29 September; priced 27.7 h on its probe; stops itself at 34 h, D28). Its treatment `f39_headway_25pct` launches only after the control's record, priced on `f39_headway_probe_25pct` first. | `python src/run/watch_run.py --run 20260929T072135_250it_25pct` |
| **F38's arm 0 is a RESULT**: `20260929T012258_250it_25pct` `ran_to_last_iteration` at 250 across warm-start joins; read in §9.217 - 1 of 12 inside 10 %, motorbike +466 %. F39 compares with it as a direction only. | `python src/analyse/report_mode_ridership.py --run 20260929T012258_250it_25pct --it 250` |
| **F37's arm 0 `20260926T002526_250it_25pct` is a RESULT** (`ran_to_last_iteration` at 250): 2 of 12 inside 10 %, read in §9.214 and on the board. | `python src/analyse/report_mode_ridership.py --run 20260926T002526_250it_25pct --it 250` |
| Windows Update is paused until **2 October 2026 21:28 AEST** (the user's pause, D19); the launcher refuses any launch whose ceiling outlasts it. | `python -c "import sys; sys.path.insert(0,'src/run'); import procs,time; print(time.ctime(procs.updates_paused_until()))"` |
| The F39 control probe `20260929T060320_4it_25pct` (390.0 s recurring) and smoke `20260929T055640_2it_1pct` (all four corrections logged: 726 activities moved, 60 shared motorcycles, ~420 unserved plans charged an iteration at 1 %) are citable for clock, heap and plumbing only. | `python src/analyse/arm_cost.py --run-config f39_control_25pct` |
| Registry **594** fields for Newcastle; manifest **968** files (**733 CC-BY / 220 ODbL** + 15 bespoke), verifying. Mumbai's manifest still does not verify (#252). | `python src/run/session_gate.py` · `python src/registry/render_schema.py --check` |
| This session's one PR (`praneetdhoolia/f37-quality-to-four`): open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/f37-quality-to-four` |
| 31 open issues (#257 closed on §9.217, #258 filed); the six F38 measurements are posted and re-aimed at F39's control arm (#30 #86 #94 #107 #145 #162). | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |
| No lane decision unanswered (D23-D28 answered this session; D28 = F39 as a pair, both arms approved at 34 h each); the recommended task is `f39-pair`. | `python src/analyse/lane.py --ask` |

Then: `python src/run/session_gate.py` (it skips the toolchain compile and the Java probes while the arm runs).

## §1 The lane

<!-- generated:lane start -->
1. **Build F39 and run it as a PAIR (D28): the control arm carries four corrections - motorcycle possession scaled to daily use from ABS SMVU (#258), a motorcycle in the household vehicle roster, trip ends attached to links that can carry them (#145), the pt no-route walk bounded to walking's reach (#162, #30) - and the treatment arm adds C.time_weights.service_quality_representation = headway (#175); read each against the other inside the family and both against F38 as a direction** **(recommended)** - the rebuild (chains unchanged; plans ~3 min; run inputs ~18 min), a 1 % smoke, a 25 % probe per arm, then two 25 % arms of ~27-32 h each at a 34 h ceiling (approved by D28), one after the other; opens a family; blocked on: the four corrections built, compiled and probed; a full gate green; each arm priced on its own probe (the fifteenth report (docs/reports/20260929T045645_project_report.html), recommendations 1, 2, 8, 9, 14; 9.217; #30 #86 #94 #98 #107 #145 #162 #175 #258)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D24 = Keep using the PC; accept the risk (2026-09-27) · D25 = Warm start at 75, 34 h cap (Recommended) (2026-09-28) · D26 = Warm start at 175, 18 h cap (Recommended) (2026-09-28) · D27 = Resume at 225, 4 h cap (Recommended) (2026-09-29) · D28 = Pair: fixes vs fixes+headway (Recommended) (2026-09-29)
<!-- generated:lane end -->

The fifteenth report ranked F38's reading (§9.218); F39's control arm runs its four corrections, then the treatment adds the headway charge. At the control's record read all twelve modes, `--stations`, the bound trips and the unserved-walk count against F38 as a direction; after both, `compare_runs.py <control> <treatment> --modes`, then a fresh `/project-report`. The road, rail, held-tour and trip-end diagnostics that traced F37 and F38 are modes of existing tools (`report_mode_ridership.py --stations`, `measure_bound_trips.py`, `transit_link_delays.py --road --access --top N`, `extract_metrics` road speed).

## §2 Traps — newest first, at most ten, each with what it cost

1. **An arm launched `--foreground` from a session dies with the session** (§9.215): F38's arm 0
   was killed at iteration 79, 13 h in, when the Claude Code process that owned its shell ended.
   Never pass `--foreground` (or `--issue-gate-passed`) by hand; the launcher now refuses an
   arm-length run in the foreground, and `run.py --stop` records a run found dead as `died`,
   which `--warm-start` resumes.
2. **A demand rebuild moves the measured access reach** (§9.214): the assembler refused the F38 run
   inputs because a Saturday activity sat 55,668 m from its nearest stop; re-measure over every
   scenario and day and re-declare `RUN.transit_router.access_max_radius_m` (reach + 200).
3. **The chains build doubles under the mobility kernel** (§9.214): ~85 min, not ~90 s; a `timeout`
   wrapper killed it after the weekday and left SAT and SUN stale. Never wrap a build in `timeout`.
4. **A shell that reads stdin hangs for its full timeout** (§9.213, again §9.214): no heredoc, no
   `python -`, `< /dev/null` on every python call; payloads through the Write tool or the Edit tool.
5. **A module can redefine a name further down** (§9.213): grep the module for a name before adding one.
6. **A JSON writer at the wrong indent rewrites the whole file** (§9.213): read the file's own indent.
7. **A refactor is proven by a run, and only the integers are exact** (§9.213, §9.211): diff
   counters and bytes, never floats, and say so.
8. **A probe prices high, not low** (§9.212, §9.213): set the ceiling on the quote plus milestones.
9. **A patch prepared on an issue must be re-anchored before it is applied** (§9.211).
10. **A keyed failure quotes its URL** (§9.209): never print a request URL.
Retired by checks this session: a host restart under an arm (`refuse_unsafe_host`), a stop that kills
a recycled pid (`procs.card_pid_alive`), a close-out that cannot read a stopped arm
(`iterations_with`), a price inflated by a dead host (`launch_to_first_iteration_s`), a credential in
a tracked file (`tests/check_secrets.py`, `.githooks/pre-commit`), Java probes nobody ran (the gate's
`java probes`), a plan that loses a tier (the plans builder refuses).

## §3 Standing directives and approvals

- **D28 approves two 25 % arms at 34 h each**: the control's is SPENT on `20260929T072135_250it_25pct`; the
  treatment's STANDS for `f39_headway_25pct` alone, after the control's record and its own probe. A warm
  start of either needs a fresh approval. D23, D25, D26 and D27 are spent.
- **25 % arms only** for Newcastle; a structural smoke may use 1 %. One arm at a time.
- **The user pauses Windows Update before a launch** (D19); never change the update settings yourself.
- **The user's goal (25 September 2026):** the simulator tuned as close as possible to a real-life
  replica from real data; every report criterion at 4/5 or better; modes chosen by the simulated
  population, never thrown in. Motorbike is a choice since F38 (D22, §9.214).
- Compare only within a family, fraction and network build. F37's result is read against F38's as a
  direction only; F36 closed with no result. The 67/143 holdout stays shut.
- Never commit to `main`; one PR per session, based on `main`.
