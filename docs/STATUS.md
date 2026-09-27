# STATUS — the board

*One page: how far the twin is from [the goal](GOAL.md), what runs, and what is
next. The blocks between `generated` markers are written by
`python src/analyse/build_status_board.py` from the artefacts; the hand-written
rest is capped by `tests/check_doc_shape.py`. The current truth per topic is in
[`positions/`](positions); the history and every rationale in
[`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 25 September 2026 (sixty-third session). F36 closed with no result (a host restart at 237); the fourteenth report found three defects under it, fixed in **F37**: the external tier restored, the pt access ceiling measured, the taxi wait executed (§9.213). **F37's arm 0 is RUNNING** at a 34 h ceiling.
The scoreboard below is F36's reading at iteration 230 - not a result, and nothing in it compares with F37. Mumbai waits on the D15 host.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **Built and measured at 25 %, twice in F35.** Every mode represented; pt access, egress and transfer walks are network legs the qsim executed (27,765 on arm 0, 0 teleported); freight trains remain crossing closures, not mobsim vehicles (§9.70) | [walk-and-bike](positions/walk-and-bike.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.169, §9.176 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis; the run viewer shows them against their targets | [monitoring-and-gates](positions/monitoring-and-gates.md), §9.120, §9.170 |
| Every mode inside 10 % | **2 of 12** on all three F35 results and on F36's reading at 230 (car and motorbike). F36 ran on three defects the tuning never touched - two in three pt requests found no route under a misderived access ceiling, so walk ran 6.5× its observed length (§9.213); **unread on F37 until its arm 0 lands** | F35's three results (§9.177, §9.176, §9.169); F36 at 230 (§9.213) |
| Convergence in ≤ 250 iterations | **Measured three times, met in the weak sense; the first arm run ON the 250 horizon relaxed** (§9.169, §9.176): the pair drifts 0.14 pp over it.210–250 against 0.5 pp, with a +1.774 pp cutoff snap on car (arm 0: 0.128 pp, +1.683). Convergence still moves car away from target on both (#172) | [seed-and-choice-set](positions/seed-and-choice-set.md), §9.176, §9.169 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail, tram and now **ferry** on disclosed boardings (§9.130, §9.211); licence rates from the published count (§9.131); fares from the Opal schedule (§9.135); bike's distance cost and the household tail derived, not assumed (§9.211); still swept: transfer penalty, charging dwell, SCATS offsets | [network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260927T145839_250it_25pct` at **iteration 75** (family `F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen`, status `aborted`, 25% sample, launched 2026-09-27T14:58:39, experienced plans (derived; validated against the trips table)). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and this reading is citable at its `reached_iteration` and nowhere past it.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260927T145839_250it_25pct --it 75` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 58.6273 | 58.3222 | +0.5% | ok | share of resident linked trips |
| 2 | ride | 15.6085 | 20.6000 | -24.2% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 13.0719 | 13.4000 | -2.4% | ok | share of resident linked trips |
| 4 | taxi | 2.3436 | 0.9916 | +136.3% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 5.6388 | 2.2084 | +155.3% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 1.6171 | 0.3785 | +327.2% | **STOP** >=20% | share of resident linked trips |
| 7 | bus | 1.9923 | 2.3819 | -16.4% | over 10% | share of resident linked trips |
| 8 | heavy_rail | 16,768 | 6,529 | +156.8% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,096 | 2,954 | -62.9% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 1,628 | 790.2850 | +106.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 11 | truck | 5.8103 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 405.0000 | 405.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car, walk**. Past the 20% stop bar: **ride, taxi, bike, motorbike, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs derived or swept with the reason stated ([network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164); the 30 run-input sets on the 250-iteration horizon (§9.169); `check_package.py` passed |
| P4 calibration | 🟡 | **F38 is open** (§9.214): destinations by each person's own mobility, one-way escorts released into round-trip lifts, motorbike chosen. The newest run on disk is `20260928T042107_250it_25pct`, which is **RUNNING** — F38's arm 0 warm-started from iteration 75 after the first launch died with its session at 79 (§9.215), 34 h ceiling (SPENT, D25); not a result until its record. The newest RESULT is `20260926T002526_250it_25pct`, F37's arm 0 (2 of 12 inside 10 %). |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen` (opened `20260927T125424`, §9.214) - nothing run before it compares with anything after it |
| Input registry | **587 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **967 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (22 September 2026 (sixty-first session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (25 September 2026 (sixty-third session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (27 September 2026 (sixty-fourth session)) · [network-and-inputs](positions/network-and-inputs.md) (25 September 2026 (sixty-third session)) · [population-and-demand](positions/population-and-demand.md) (27 September 2026 (sixty-fourth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (27 September 2026 (sixty-fourth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (27 September 2026 (sixty-fourth session)) · [runs-and-economics](positions/runs-and-economics.md) (27 September 2026 (sixty-fourth session)) · [sampling-and-families](positions/sampling-and-families.md) (27 September 2026 (sixty-fourth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (17 September 2026 (fifty-fourth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (16 September 2026 (fifty-third session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (27 September 2026 (sixty-fourth session)) · [walk-and-bike](positions/walk-and-bike.md) (27 September 2026 (sixty-fourth session)) |
<!-- generated:state end -->

F36 is open at the demand rebuild `20260922T210005` and has NO reading until arm 0 lands; F35 closes with three
results, each citable inside it and against nothing after it. The network is still F34's footpath
rebuild, re-mapped for nothing; the demand and plans are the rebuild's (§9.211). The manifest holds
**732 CC-BY / 220 ODbL** plus 15 bespoke files, every one hashed. The heap rule reads 37.4 GiB at
25 % against a measured live peak of 26.2 GiB on F35's arm 0 (§9.169).

The separate package audit's run-input report coverage is restored by the rebuild (#235: S0–S6 and every day type against the committed S2/WEEKDAY-only file). It still fails on stale document paths (#234) and on Mumbai run cards judged against the reference city's scenario vocabulary.

## Runs on disk

<!-- generated:runs start -->
| run | city | status | family | reached | cause / note |
|---|---|---|---|---:|---|
| `20260928T042107_250it_25pct` | newcastle | running | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | live | - |
| `20260928T041917_250it_25pct` | newcastle | ? | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | - | - |
| `aborted_20260927T145839_250it_25pct` | newcastle | aborted | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 79 | killed at iteration 79 (04:07:47 on 28 September 2026) with its harness: the arm was launched with --foreground inside a Claude Code sess... |
| `20260927T133754_4it_25pct` | newcastle | completed | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 4 | ran_to_last_iteration `_run.json` |
| `20260927T133104_2it_1pct` | newcastle | completed | F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen | 2 | ran_to_last_iteration `_run.json` |
| `20260926T002526_250it_25pct` | newcastle | completed | F37-the-boundary-tier-returns-and-pt-reaches-every-stop | 250 | ran_to_last_iteration `_run.json` |

242 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

<!-- generated:lane start -->
1. **Read F38's arm 0 at its record: all twelve modes with choice-set coverage against F37's result as a direction; walk's mean trip against 4.08 km and walk km inside held-ride tours against 35.6 %; the car-less split and trip lengths (bike 11.8 km, walk 6.0 km); heavy-rail station entries against 17,016 and access walks over 2 km against 19.5 %; motorbike CHOSEN against 0.3785 %; ride with the doubled lifts against -13.5 %; taxi against +129.6 %; the no-route share against 52.1 %** **(recommended)** - no run: `report_mode_ridership.py --run 20260927T145839_250it_25pct --it 250` and `--trend`, `report_choice_set_coverage.py --against-targets`, `mode_by_demographics.py`, `measure_bound_trips.py`, `diagnose_pt_routing.py --sample 3000`, `fit.py`; then `build_run_index.py`, the board and a fresh /project-report; no family boundary; blocked on: the arm reaching its record (overlay `f38_baseline_25pct`, 34 h ceiling approved 27 September 2026, D23) (9.214; #30 #86 #94 #98 #107 #145 #162 #257)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **Attach trip ends to links that can carry them: on F37's arm 0, 29 links (28 service lanes, one living street) carry 23,161 sampled road-vehicle trip ends needing up to 38 hours of their own sampled capacity, and the 2.7 % of road trips touching them average 72.6 min at 13.4 km/h against 25.5 min elsewhere; 73 % of the run's excess vehicle-hours sit on residential and service links carrying ~13 % of traversals. Design a capacity-aware citysim.ActivityLinkAssigner rule (no link receives more trip ends than it can move in the modelled day, excess moved to the next-nearest eligible links), derived, behind a representation gate, and measure the car time tail against the HTS 17.2 min** - no run to design: the trip-end load per link and the car time by load band from any finished arm's trips table and output network (scratch access_load.py and delay_links.py, to be folded into an existing reader); the Java change compiles only on an idle machine and opens a family; opens a family; blocked on: F38's arm 0 reading (the car time tail on the new demand), then a user decision on the next family's contents (9.214 (F37 arm 0: car mean 25.0 min for 11.88 km against the HTS 17.2 min for 10.2 km; median 12.6 min; 9.8 % of car trips under 15 km/h carry 32.4 % of car time, spread over the whole day); #145)
7. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D21 = Before the F37 launch (recommended) (2026-09-25) · D22 = In F38, after F37 reads (recommended) (2026-09-25) · D23 = All three, then the arm (Recommended) (2026-09-27) · D24 = Keep using the PC; accept the risk (2026-09-27) · D25 = Warm start at 75, 34 h cap (Recommended) (2026-09-28)
<!-- generated:lane end -->

## Open work

*The deviations are the scoreboard's, above; a row here names the mechanism, the issue and the next measurement, not the number (§9.176).*

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **Choice-set coverage is an arithmetic ceiling, and it is a share of TRIPS.** Identical on three results (ride 19.11 %, pt 15.78–17.53 %); ride's coverage is the bound trips' share sitting AT its target, so its deficit is what bound trips execute as (§9.177) | #86 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on the roots rebuild's arm 0 |
| **Two one-field controls are run and both moved nothing** (§9.176, §9.177): the routers and the scoring branches are exonerated; the choice set (#174), service quality (#175) and pt submodes (#49) remain unrun; the cutoff snap (car +1.68 to +1.77 pp on three results) is selection, not scoring. The roots rebuild goes at the demand first | #172 #174 #49 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the rebuilt arm 0's reading, then the choice-set pair |
| **The reading point is a convergence problem**; the windowed remedy measured worse (§9.159). The objective's denominator `CAL.objective.replication_band_pp` is 0.0 until a band is measured (§9.164) | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the band |
| **Ride: D12 is BUILT and unread** (§9.211) — the binders bind the observed share (20.62 % of core legs) and the held passenger no longer keeps a plan that takes them off `ride`: 276,816 trips on 141,633 persons carry `heldRideTrips`, and the gate refuses car on them | #86 #145 | [ride-and-pairing](positions/ride-and-pairing.md), [population-and-demand](positions/population-and-demand.md) | `measure_bound_trips.py` on F36's arm 0 |
| **Light rail under and heavy rail over, past the bar on both results**, are one split, and the router's mode constant is NOT what decides it (§9.176). Crowding has never had a control (`C.crowding.representation` `in_vehicle_time` on every arm, §9.158) | #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the crowding or service-quality control, or the rebuilt demand |
| **Ferry: the TARGET is re-derived** (§9.211, D8) — 790 boardings a weekday over 300 TPA weekdays, sweep 234–1,347, on the boardings basis the rail targets use; the census G62 lockdown cell is superseded. A basis change, so the next reading is an error statistic against an observation | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the wharf split and the new deviation on F36's arm 0 |
| **Taxi, past the bar on both results** with 51 pp of headroom; the fleet's refusals fell to one in five (2,065 an iteration) and are no longer the mechanism (§9.169) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | the cause of the excess, on the next arm |
| **Bike: a distance cost is BUILT** (§9.211, D9) — `marginal_utility_of_distance_per_m` bike −0.000192308 utils/m, derived as −1/(observed 5.2 km mean) and swept on that mean's spread; it had none at all while running 8.10–8.13 km against 5.2 | #107 | [walk-and-bike](positions/walk-and-bike.md) | bike's mean trip and share by car availability on F36's arm 0 |
| **Walk: the supply is at the seed and the band is now reported on PLACED coordinates** (§9.211, #30) — 17.81 % of core legs under 1 km against the 18.8 % band; the loss is at allocation, where car takes half the routed short trips | #30 | [walk-and-bike](positions/walk-and-bike.md) | the routed short-trip split on F36's arm 0 |
| **Headway and reliability reach MATSim** behind a gate shipped `absent` (`citysim.ServiceQualityScoring`, §9.164) | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired arm at `headway` and `headway_and_reliability` |
| **The TfNSW bespoke-table request** (mode × age, trip length by mode, occupancy by purpose, the unfolded "Other") is drafted and held; the four cells were searched on every public channel and API and found on none (§9.172); the modelled mode × demographics table exists (§9.163) | #50 | [population-and-demand](positions/population-and-demand.md) | the lodgement, then TfNSW's answer |
| Surrogate calibration held in reserve: ~150 evaluations at 21.5 h each is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | only if the residual proves multi-parameter |
| **Report #12's open items** (20260916T062246; §9.177, §9.210): the Java fold is landed and verified on a 1 % smoke; #187's second half (the end-time comparison on an arm) and the `timeoutClock` counts read on the first 25 % arm after; nine extract adapters work at import (#232); the mobsim's parallel efficiency is unmeasured (#231); 25 %-only and the stated cost are enforced by nobody (#209) | #187 #209 #215 #216 #217 #231 #232 | [monitoring-and-gates](positions/monitoring-and-gates.md) | the first 25 % arm after the fold |
| **Standing room and transit road space are scaled, and F36 is the first family to run with them** (§9.203, §9.206, §9.211) — every F35 arm ran trams with 210 standing places and buses at four times their share of a 25 %-scaled lane | #237 | [sampling-and-families](positions/sampling-and-families.md) | peak standing occupancy per vehicle type and the count-station reading on F36's arm 0 |
| **The second city** (§9.201–§9.210): printed timetables, published metro windows and headways, vehicles projected from the registration stock, destinations by built volume, grades on every link, a use for every catalogue entry, the metro target from observed ridership; both 1 % cases gridlock on the flow identity, so the reading needs D15's host; the TUS unit files wait on the user's browser | #239 | [network-and-inputs](positions/network-and-inputs.md), [`cities/mumbai/docs/README.md`](../cities/mumbai/docs/README.md) | the 10 % probe on the D15 host, priced by `arm_cost.py` |

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
