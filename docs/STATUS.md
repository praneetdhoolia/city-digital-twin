# STATUS — the board

*One page: how far the twin is from [the goal](GOAL.md), what runs, and what is
next. The blocks between `generated` markers are written by
`python src/analyse/build_status_board.py` from the artefacts; the hand-written
rest is capped by `tests/check_doc_shape.py`. The current truth per topic is in
[`positions/`](positions); the history and every rationale in
[`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 8 October 2026 (sixty-fifth session). **The sixteenth report read F39's control** (§9.220): 2 of 12 inside 10 %, four defects, all in the instruments and all fixed; the gates read every city; the treatment arm is bound to #175 (reopened) and waits on D29 and a host that can launch.
The scoreboard below is F39's control at iteration 250 (§9.219); F38's result (1 of 12) is a direction only. Mumbai waits on the D15 host.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **Built and measured at 25 %**: every mode represented, motorbike chosen by daily use from one household motorcycle (§9.218); pt access, egress and transfer walks are network legs, and a no-route walk beyond walking's reach is an unexecutable plan (§9.219); freight trains remain crossing closures (§9.70) | [walk-and-bike](positions/walk-and-bike.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.218, §9.219 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis; the run viewer shows them against their targets | [monitoring-and-gates](positions/monitoring-and-gates.md), §9.120, §9.170 |
| Every mode inside 10 % | **2 of 12** on F39's control (car and motorbike); 1 of 12 on F38's. Walk's error is short trips driven and car-less trips with no alternative; pt's is a split with no frequency term (the treatment, D29) and 47.6 % of pt requests with no transit route (§9.219) | F39 (§9.219), F38 (§9.217), F37 (§9.214) |
| Convergence in ≤ 250 iterations | **Measured three times, met in the weak sense; the first arm run ON the 250 horizon relaxed** (§9.169, §9.176): the pair drifts 0.14 pp over it.210–250 against 0.5 pp, with a +1.774 pp cutoff snap on car (arm 0: 0.128 pp, +1.683). Convergence still moves car away from target on both (#172) | [seed-and-choice-set](positions/seed-and-choice-set.md), §9.176, §9.169 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail, tram and now **ferry** on disclosed boardings (§9.130, §9.211); licence rates from the published count (§9.131); fares from the Opal schedule (§9.135); bike's distance cost and the household tail derived, not assumed (§9.211); still swept: transfer penalty, charging dwell, SCATS offsets | [network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `20260929T072135_250it_25pct` at **iteration 250** (family `F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk`, status `completed`, 25% sample, launched 2026-09-29T07:21:43, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 250, the only completion that means the run executed the horizon it declared.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260929T072135_250it_25pct --it 250` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 63.2999 | 58.3222 | +8.5% | ok | share of resident linked trips |
| 2 | ride | 15.4418 | 20.6000 | -25.0% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 10.0835 | 13.4000 | -24.7% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 2.5892 | 0.9916 | +161.1% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 5.5021 | 2.2084 | +149.1% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.3629 | 0.3785 | -4.1% | ok | share of resident linked trips |
| 7 | bus | 1.6498 | 2.3819 | -30.7% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 14,320 | 6,529 | +119.3% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 768 | 2,954 | -74.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 1,544 | 790.2850 | +95.4% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 11 | truck | 5.4694 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 405.0000 | 405.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car, motorbike**. Past the 20% stop bar: **ride, walk, taxi, bike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs derived or swept with the reason stated ([network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164); the 30 run-input sets on the 250-iteration horizon (§9.169); `check_package.py` passed |
| P4 calibration | 🟡 | **F39 has its control's result** (§9.219) and the sixteenth report's reading of it (§9.220): the four corrections worked as built; the headway treatment is rebuilt (line at its stop, ATAP M1), bound to #175 and unrun - D29 and the host (a restart pending, §9.220). The newest run on disk is `20261008T114753_4it_25pct`, which **RAN TO ITS LAST ITERATION** — the treatment's pricing probe on the ATAP build at a 38g heap, citable for its clock only (plain iterations 360-390 s beside the operator's Blender; the control's own wall is the pair quote). 2 of 12 inside 10 %. |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk` (opened `20260929T053207`, §9.218) - nothing run before it compares with anything after it |
| Input registry | **604 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **968 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (8 October 2026 (sixty-fifth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (8 October 2026 (sixty-fifth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (8 October 2026 (sixty-fifth session)) · [network-and-inputs](positions/network-and-inputs.md) (8 October 2026 (sixty-fifth session)) · [population-and-demand](positions/population-and-demand.md) (8 October 2026 (sixty-fifth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (8 October 2026 (sixty-fifth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (8 October 2026 (sixty-fifth session)) · [runs-and-economics](positions/runs-and-economics.md) (8 October 2026 (sixty-fifth session)) · [sampling-and-families](positions/sampling-and-families.md) (8 October 2026 (sixty-fifth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (8 October 2026 (sixty-fifth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (8 October 2026 (sixty-fifth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (8 October 2026 (sixty-fifth session)) · [walk-and-bike](positions/walk-and-bike.md) (30 September 2026 (sixty-fourth session)) |
<!-- generated:state end -->

F38 closed with one result: arm 0 ran to 250 across warm-start joins at 75 (a session-owned launch), 175 (a host crash after an NVMe controller error) and 225 (a Start-menu shutdown), §9.215-§9.217. The open family is the State block's: F39 opened at its plans and run-inputs rebuild on the four corrections of D28 and, on the treatment arm only, `C.time_weights.service_quality_representation` = `headway` (§9.218). The network is still F34's footpath rebuild. The manifest holds
**733 CC-BY / 220 ODbL** plus 15 bespoke files, every one hashed. The heap rule reads 37.4 GiB at
25 % against a measured live peak of 30.0 GiB (fifteenth report).

The separate package audit passes since §9.220 (PASS 2,061, WARN 2): a run card is judged against its own city's vocabulary (#253) and the framework documents resolve through `city.docs()` (#234).

## Runs on disk

<!-- generated:runs start -->
| run | city | status | family | reached | cause / note |
|---|---|---|---|---:|---|
| `20261008T114753_4it_25pct` | newcastle | completed | F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk | 4 | ran_to_last_iteration `_run.json` |
| `20260930T140500_4it_25pct` | newcastle | completed | F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk | 4 | ran_to_last_iteration `_run.json` |
| `20260930T123858_4it_25pct` | newcastle | completed | F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk | 4 | ran_to_last_iteration `_run.json` |
| `20260930T111836_4it_25pct` | newcastle | completed | F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk | 4 | ran_to_last_iteration `_run.json` |
| `20260929T072135_250it_25pct` | newcastle | completed | F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk | 250 | ran_to_last_iteration `_run.json` |
| `20260929T060320_4it_25pct` | newcastle | completed | F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk | 4 | ran_to_last_iteration `_run.json` |

251 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

<!-- generated:lane start -->
1. **Run F39's treatment arm: f39_control_25pct plus the service-interval charge on the boarded line's interval at the boarding stop, valued by ATAP M1 (C.time_weights.service_interval_function = atap_m1, #175), and read it against the control 20260929T072135_250it_25pct with compare_runs.py --modes** **(recommended)** - a 25 % probe on the ATAP build (f39_headway_probe_25pct, ~1 h), then one 25 % arm at RUN.gate.wall_ceiling_h 40: the pair quote is the control's 27.9 h wall (band 24.5-27.9 h); the daytime probes of 30 September quoted 37.0-50.5 h on a loaded host; no family boundary; blocked on: the host: Windows Update paused past the 40 h ceiling and no restart pending (D19; the launcher refuses otherwise), then the probe f39_headway_probe_25pct in the host's quiet hours pricing inside 40 h; D29 answered 8 October 2026: ATAP M1 function, 40 h cap - the stated-cost approval (9.219: the probe found the approved charge keyed on route variants (1,080 of 1,270 once-a-day) and a once-a-day line-stop charged 900 IVT-minutes; fixed, and ATAP M1 eq 4.3.2 declared; #94 #98 #175)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **Design, from observed inputs, the two mechanisms walk's error traces to on F39's control: (1) a car terminal time - the walk to and from a parked car and the manoeuvre - so the car-available stop driving 75.9 % of sub-kilometre trips (walk 7.6 %); (2) the car-less' alternative on a trip no driver is bound to and no transit serves (they walk 14-24 % of 10-20+ km trips; ride is reachable only on bound trips, coverage 19.02 % below its 20.60 % target)** - no run: the literature and data search (ATAP M1 and the HTS for terminal time; the NSW HTS passenger tables for lifts outside the household), a registry proposal with sweeps and a representation gate each, and a probe; opens the next family when built; opens a family; blocked on: nothing - design work; an arm only after F39's treatment (9.219: mode_by_demographics.py distance bands and _bound_trips.json on 20260929T072135_250it_25pct (sub-1 km trips 13.5 % of trips, 59.2 % driven; chosen walks in no-ride tours 26,721 at 6.21 km); #30 #86 #162)
7. **Measure the replication band: three 25 % arms of f39_control_25pct at RUN.controler.last_iteration 100 under seeds 20260810, 20260811 and 20260812 (overlays f39_seed_<n>_100it_25pct), read against each other with compare_runs.py --modes, then set CAL.objective.replication_band_pp from their spread** - three 25 % arms of 100 iterations, ~11 h each at the control's 345 s pace (~33 h in all), one at a time; the first seed is the control's own and reads from its record where the horizons agree; no family boundary; blocked on: the F39 pair read (f39-headway-arm) - D30 answered 8 October 2026: run the three seeds after the pair; the host paused past each arm's ceiling (D30 (8 October 2026); the sixteenth report's recommendation 16 and ten earlier issuances; CAL.objective.replication_band_pp ships 0.0 so a pair difference is read as a diff; #163)
8. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

Decided: D28 = Pair: fixes vs fixes+headway (Recommended) (2026-09-29) · D29 = ATAP M1 function, 40 h cap (Recommended) (2026-10-08) · D30 = Run the three seeds after the F39 pair (Recommended) (2026-10-08) · D31 = Send it to opendataprogram@transport.nsw.gov.au (Recommended) (2026-10-08) · D32 = Take the recommended defaults for all three (Recommended) (2026-10-08)
<!-- generated:lane end -->

## Open work

*The deviations are the scoreboard's, above; a row here names the mechanism, the issue and the next measurement, not the number (§9.176).*

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **Motorbike's constant is a placeholder at its target** (§9.219): chosen by daily use at `C.asc.motorbike` 0.0, trips 12.38 km long against the survey | #260 | [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) | motorbike trip length on the next calibrated base |
| **The pt submode split has no frequency term** (§9.217); the charge that adds it read route variants until §9.219 and is rebuilt with ATAP M1's valuation, unrun | #175 (reopened) #98 #94 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | F39's treatment against its control, after D29 |
| **Walk loses short trips to the car and wins long car-less ones** (§9.219): no car terminal time; a car-less trip no driver is bound to and no transit serves has walk, bike or taxi only; 47.6 % of pt requests find no transit route | #30 #162 #86 | [walk-and-bike](positions/walk-and-bike.md) | the `short-trip-and-carless-choice` design |
| **The car time tail did not follow the trip ends** (§9.219): capacity-bounded activity links moved 9,503 activities, and car trips still average 27.6 min against the HTS 17.2 with 36.7 % of car time under 15 km/h (`_metrics.json`) | #145 | [network-and-inputs](positions/network-and-inputs.md) | where the slow car time accrues (`transit_link_delays.py --road`) |
| **Ride is volume-bound** (§9.219): coverage 19.02 % below its 20.60 % target, occupancy 0.2426 against 0.3503; the car-less lack a driver on unbound trips | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | the `short-trip-and-carless-choice` design |
| **Bike and taxi carry the car-less long trip** (§9.219): the car-less take bike on 11.8 % and taxi on 5.6 % of trips against 2.4 % and 0.9 % for the car-available (`_mode_by_demographics.json`) | #107 #49 | [walk-and-bike](positions/walk-and-bike.md), [taxi-and-rideshare](positions/taxi-and-rideshare.md) | the same, after the car-less alternative |
| **No change is ever measured alone** (the fifteenth report): F39's pair is the first control since F35; the replication band is still unmeasured, so `CAL.objective.replication_band_pp` is 0.0 - now the lane's D30 (§9.220) | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F39's treatment; three seeds at a short horizon |
| **The host is the arm's weakest part**: 1 of the last 3 arms ran clean (Windows Update, a co-tenant, a session-owned launch, an NVMe-driven crash, a shutdown); since §9.220 the launcher refuses a loaded host and every run keeps `_host.jsonl` | - | [runs-and-economics](positions/runs-and-economics.md) | the next arm's `_host.jsonl` |
| **The TfNSW bespoke-table request** (mode x age, trip length by mode, occupancy by purpose) is drafted and held | #50 | [population-and-demand](positions/population-and-demand.md) | the lodgement (the lane's D31, §9.220) |
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
