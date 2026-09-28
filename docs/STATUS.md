# STATUS — the board

*One page: how far the twin is from [the goal](GOAL.md), what runs, and what is
next. The blocks between `generated` markers are written by
`python src/analyse/build_status_board.py` from the artefacts; the hand-written
rest is capped by `tests/check_doc_shape.py`. The current truth per topic is in
[`positions/`](positions); the history and every rationale in
[`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 29 September 2026 (sixty-fourth session). **F38 has its result** (§9.217): 1 of 12 inside 10 % (car); motorbike chosen at a zero constant +466 %; the fifteenth report (`docs/reports/20260929T045645_project_report.html`) ranks the fixes. **F39 is decided as a PAIR** (D28): control = four corrections, treatment = + the headway charge; nothing runs yet.
The scoreboard below is F38 arm 0 at iteration 250, a result across three warm-start joins; F37's result (2 of 12) is a direction only. Mumbai waits on the D15 host.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **Built and measured at 25 %**: every mode represented, motorbike chosen since F38 (§9.214); pt access, egress and transfer walks are network legs; a pt request with no transit route is still answered by a network walk of any length (the F39 correction); freight trains remain crossing closures (§9.70) | [walk-and-bike](positions/walk-and-bike.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.214, §9.217 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis; the run viewer shows them against their targets | [monitoring-and-gates](positions/monitoring-and-gates.md), §9.120, §9.170 |
| Every mode inside 10 % | **1 of 12** on F38's result (car); **2 of 12** on F37's and on all three F35 results (car and motorbike). F38's demand changes worked as built and exposed what the choice lacks - motorbike possession read as daily availability, no frequency term in the pt submode split (§9.217) | F38 (§9.217), F37 (§9.214), F35 (§9.169, §9.176, §9.177) |
| Convergence in ≤ 250 iterations | **Measured three times, met in the weak sense; the first arm run ON the 250 horizon relaxed** (§9.169, §9.176): the pair drifts 0.14 pp over it.210–250 against 0.5 pp, with a +1.774 pp cutoff snap on car (arm 0: 0.128 pp, +1.683). Convergence still moves car away from target on both (#172) | [seed-and-choice-set](positions/seed-and-choice-set.md), §9.176, §9.169 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail, tram and now **ferry** on disclosed boardings (§9.130, §9.211); licence rates from the published count (§9.131); fares from the Opal schedule (§9.135); bike's distance cost and the household tail derived, not assumed (§9.211); still swept: transfer penalty, charging dwell, SCATS offsets | [network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `20260929T012258_250it_25pct` at **iteration 250** (family `F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen`, status `completed`, 25% sample, launched 2026-09-29T01:23:07, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 250, the only completion that means the run executed the horizon it declared.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260929T012258_250it_25pct --it 250` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 61.9914 | 58.3222 | +6.3% | ok | share of resident linked trips |
| 2 | ride | 15.3604 | 20.6000 | -25.4% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 9.7378 | 13.4000 | -27.3% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 2.6666 | 0.9916 | +168.9% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 5.3799 | 2.2084 | +143.6% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 2.1412 | 0.3785 | +465.7% | **STOP** >=20% | share of resident linked trips |
| 7 | bus | 1.6621 | 2.3819 | -30.2% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 14,236 | 6,529 | +118.1% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 812 | 2,954 | -72.5% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 1,704 | 790.2850 | +115.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 11 | truck | 5.4462 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 405.0000 | 405.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car**. Past the 20% stop bar: **ride, walk, taxi, bike, motorbike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs derived or swept with the reason stated ([network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164); the 30 run-input sets on the 250-iteration horizon (§9.169); `check_package.py` passed |
| P4 calibration | 🟡 | **F38 is open and has its result** (§9.214, §9.217): destinations by each person's own mobility, one-way escorts released into round-trip lifts, motorbike chosen. The newest run on disk is `20260929T012258_250it_25pct`, which **RAN TO ITS LAST ITERATION** — F38's arm 0, completed across warm-start joins at 75, 175 and 225 (§9.215-§9.217). 1 of 12 inside 10 % (car); motorbike chosen at a zero constant +466 %; heavy rail +118 % (F37 +188 %). |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen` (opened `20260927T125424`, §9.214) - nothing run before it compares with anything after it |
| Input registry | **594 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **967 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (22 September 2026 (sixty-first session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (29 September 2026 (sixty-fourth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (27 September 2026 (sixty-fourth session)) · [network-and-inputs](positions/network-and-inputs.md) (25 September 2026 (sixty-third session)) · [population-and-demand](positions/population-and-demand.md) (27 September 2026 (sixty-fourth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (29 September 2026 (sixty-fourth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (27 September 2026 (sixty-fourth session)) · [runs-and-economics](positions/runs-and-economics.md) (27 September 2026 (sixty-fourth session)) · [sampling-and-families](positions/sampling-and-families.md) (29 September 2026 (sixty-fourth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (17 September 2026 (fifty-fourth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (16 September 2026 (fifty-third session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (27 September 2026 (sixty-fourth session)) · [walk-and-bike](positions/walk-and-bike.md) (27 September 2026 (sixty-fourth session)) |
<!-- generated:state end -->

F38 is open at the chains and plans rebuild `20260927T125424` and has its result: arm 0 ran to 250 across warm-start joins at 75 (a session-owned launch), 175 (a host crash after an NVMe controller error) and 225 (a Start-menu shutdown), §9.215-§9.217. F39 opens at its rebuild: the four corrections of D28 and, on the treatment arm only, `C.time_weights.service_quality_representation` = `headway`. The network is still F34's footpath rebuild. The manifest holds
**732 CC-BY / 220 ODbL** plus 15 bespoke files, every one hashed. The heap rule reads 37.4 GiB at
25 % against a measured live peak of 30.0 GiB (fifteenth report).

The separate package audit still fails on stale document paths (#234) and on Mumbai run cards judged against the reference city's scenario vocabulary (#253).

## Runs on disk

<!-- generated:runs start -->
| run | city | status | family | reached | cause / note |
|---|---|---|---|---:|---|
| `20260929T012258_250it_25pct` | newcastle | completed | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 250 | ran_to_last_iteration `_run.json` |
| `aborted_20260928T163345_250it_25pct` | newcastle | aborted | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 229 | died at iteration 229 when the user shut the host down from the Start menu at 23:29 on 28 September 2026 (System event 1074, StartMenuExp... |
| `aborted_20260928T042107_250it_25pct` | newcastle | aborted | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 188 | died at iteration 188 when the host crashed: Windows bugcheck 0x13A (kernel-mode heap corruption) at about 16:18 on 28 September 2026 aft... |
| `20260928T041917_250it_25pct` | newcastle | ? | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | - | - |
| `aborted_20260927T145839_250it_25pct` | newcastle | aborted | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 79 | killed at iteration 79 (04:07:47 on 28 September 2026) with its harness: the arm was launched with --foreground inside a Claude Code sess... |
| `20260927T133754_4it_25pct` | newcastle | completed | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 4 | ran_to_last_iteration `_run.json` |

244 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

<!-- generated:lane start -->
1. **Build F39 and run it as a PAIR (D28): the control arm carries four corrections - motorcycle possession scaled to daily use from ABS SMVU (#258), a motorcycle in the household vehicle roster, trip ends attached to links that can carry them (#145), the pt no-route walk bounded to walking's reach (#162, #30) - and the treatment arm adds C.time_weights.service_quality_representation = headway (#175); read each against the other inside the family and both against F38 as a direction** **(recommended)** - the rebuild (chains unchanged; plans ~3 min; run inputs ~18 min), a 1 % smoke, a 25 % probe per arm, then two 25 % arms of ~27-32 h each at a 34 h ceiling (approved by D28), one after the other; opens a family; blocked on: the four corrections built, compiled and probed; a full gate green; each arm priced on its own probe (the fifteenth report (docs/reports/20260929T045645_project_report.html), recommendations 1, 2, 8, 9, 14; 9.217; #30 #86 #94 #98 #107 #145 #162 #175 #258)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D24 = Keep using the PC; accept the risk (2026-09-27) · D25 = Warm start at 75, 34 h cap (Recommended) (2026-09-28) · D26 = Warm start at 175, 18 h cap (Recommended) (2026-09-28) · D27 = Resume at 225, 4 h cap (Recommended) (2026-09-29) · D28 = Pair: fixes vs fixes+headway (Recommended) (2026-09-29)
<!-- generated:lane end -->

## Open work

*The deviations are the scoreboard's, above; a row here names the mechanism, the issue and the next measurement, not the number (§9.176).*

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **Motorbike possession is read as daily availability** (§9.217): chosen at a zero constant it runs five times its share; ABS SMVU puts a motorcycle at ~1.9k km a year against 11.1k for a car. F39 scales possession to daily use and puts the motorcycle in the household roster | #258 | [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) | motorbike on F39's control arm |
| **The pt submode split has no frequency term** (§9.217, the fifteenth report): infrequent heavy rail and ferry run double, frequent bus and tram under; `citysim.ServiceQualityScoring` is built and has never run | #175 #98 #94 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | F39's treatment arm against its control |
| **A pt request with no transit route becomes a walk of any length**: walk averages 3.61 km against 0.70; 51.9 % of pt requests on F38's last segment had no route (rural trip ends) | #162 #30 | [walk-and-bike](positions/walk-and-bike.md) | walk's mean trip on F39's control arm |
| **Trip ends on links that cannot carry them** (F37: 29 service lanes, car trips touching them 72.6 min) drive the car time tail (25.0 min mean against the HTS 17.2) | #145 | [network-and-inputs](positions/network-and-inputs.md) | the car time tail on F39's control arm |
| **Ride fell as its supply grew** (§9.217): the released escorts exist as round-trip lifts (44,632 -> 93,318), bound trips executed as ride fell to 76.6 % and occupancy to 0.24 | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | `measure_bound_trips.py` by binding type on F39 |
| **Bike and taxi carry the car-less long trip** (bike +143.6 % at 7.36 km, taxi +168.9 %) | #107 #49 | [walk-and-bike](positions/walk-and-bike.md), [taxi-and-rideshare](positions/taxi-and-rideshare.md) | bike and taxi by car availability on F39 |
| **No change is ever measured alone** (the fifteenth report): one arm per family since F35; the replication band is still unmeasured, so `CAL.objective.replication_band_pp` is 0.0 | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F39's pair; three seeds at a short horizon |
| **The host is the arm's weakest part**: 1 of the last 3 arms ran clean (Windows Update, a co-tenant, a session-owned launch, an NVMe-driven crash, a shutdown) | - | [runs-and-economics](positions/runs-and-economics.md) | the next arm with host load recorded |
| **The TfNSW bespoke-table request** (mode x age, trip length by mode, occupancy by purpose) is drafted and held | #50 | [population-and-demand](positions/population-and-demand.md) | the lodgement (the user's D2) |
| **Standing room and transit road space scaled** since F36; peak standing occupancy still has no reader | #237 | [sampling-and-families](positions/sampling-and-families.md) | a peak-occupancy reader on F39 |
| **The second city**: both 1 % cases gridlock on the flow identity, so the reading needs D15's host; the TUS unit files wait on the user's browser | #239 | [network-and-inputs](positions/network-and-inputs.md), [`cities/mumbai/docs/README.md`](../cities/mumbai/docs/README.md) | the 10 % probe on the D15 host |

## Do not re-raise

- The 143 holdout targets stay closed until the end; no target is deleted after the fact (§12).
- The record is never rewritten; superseded text is bannered and pointed past (§9.79).
- SCATS is implemented, not assumed (§9.88); the operated plans and the offset library are what remains unobtained.
- No multi-hour run without a stated-cost approval, spent on use; no launch while an open issue lacks `awaiting-run` (GOAL.md requirement 10).
- One arm at a time; never recompile `.tools/classes` while one runs (#66).
- The taxi fare is not a lever (§9.91); freight trains are not mobsim vehicles (§9.70); SCATS offsets are not adapted (§9.88).

## How to resume

Run `/onboard`. By hand: `python src/run/session_gate.py --digest`, then
[`GOAL.md`](GOAL.md), this board, the brief
([`NEXT_AGENT_BRIEF.md`](NEXT_AGENT_BRIEF.md)) and the position page for the
lane. `python src/run/session_gate.py` runs every gate.
