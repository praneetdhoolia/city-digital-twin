# STATUS — the board

*One page: how far the twin is from [the goal](GOAL.md), what runs, and what is
next. The blocks between `generated` markers are written by
`python src/analyse/build_status_board.py` from the artefacts; the hand-written
rest is capped by `tests/check_doc_shape.py`. The current truth per topic is in
[`positions/`](positions); the history and every rationale in
[`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 16 September 2026 (fifty-third session). Newest reading: the routers pair `20260915T000704_250it_25pct`, the third RESULT (250 of 250, 27.39 h) - **2 of 12 inside 10 %**, six past the stop bar, nothing moved against arm 0 outside one build's noise (§9.176).
Its harness died at iteration 34 and the JVM ran alone to the horizon; the run was closed out through the new `run.py --close-out` (D5, §9.176, #225). D6 (the launch default) and D7 (what runs next) await the user.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **Built and measured at 25 %, twice in F35.** Every mode represented; pt access, egress and transfer walks are network legs the qsim executed (27,765 on arm 0, 0 teleported); freight trains remain crossing closures, not mobsim vehicles (§9.70) | [walk-and-bike](positions/walk-and-bike.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.169, §9.176 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis; the run viewer shows them against their targets | [monitoring-and-gates](positions/monitoring-and-gates.md), §9.120, §9.170 |
| Every mode inside 10 % | **2 of 12** on both F35 results (§9.169, §9.176): car and motorbike. Six past the 20 % bar on both; ride's 20.60 % target exceeds its 19.11 % choice-set coverage on both, fixed at the seed — out of reach of any constant; the routers control moved nothing | the scoreboard below, §9.176, §9.169, §9.163 |
| Convergence in ≤ 250 iterations | **Measured three times, met in the weak sense; the first arm run ON the 250 horizon relaxed** (§9.169, §9.176): the pair drifts 0.14 pp over it.210–250 against 0.5 pp, with a +1.774 pp cutoff snap on car (arm 0: 0.128 pp, +1.683). Convergence still moves car away from target on both (#172) | [seed-and-choice-set](positions/seed-and-choice-set.md), §9.176, §9.169 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); fares from the Opal schedule (§9.135); still swept: transfer penalty, charging dwell, SCATS offsets | [network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `20260915T000704_250it_25pct` at **iteration 250** (family `F35-the-engines-route-what-they-remode`, status `completed`, 25% sample, launched 2026-09-15T00:07:08, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 250, the only completion that means the run executed the horizon it declared.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260915T000704_250it_25pct --it 250` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 63.5564 | 58.3222 | +9.0% | ok | share of resident linked trips |
| 2 | ride | 12.1902 | 20.6000 | -40.8% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 11.8059 | 13.4000 | -11.9% | over 10% | share of resident linked trips |
| 4 | taxi | 2.4056 | 0.9916 | +142.6% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.5771 | 2.2084 | +197.8% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.3577 | 0.3785 | -5.5% | ok | share of resident linked trips |
| 7 | bus | 2.0895 | 2.3819 | -12.3% | over 10% | share of resident linked trips |
| 8 | heavy_rail | 10,476 | 6,529 | +60.5% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 856 | 2,954 | -71.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0473 | 0.1429 | -66.9% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6474 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 405.0000 | 405.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car, motorbike**. Past the 20% stop bar: **ride, taxi, bike, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs derived or swept with the reason stated ([network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164); the 30 run-input sets on the 250-iteration horizon (§9.169); `check_package.py` passed |
| P4 calibration | 🟡 | the newest run on disk is `20260915T000704_250it_25pct`, which is **RAN TO ITS LAST ITERATION** - the routers pair (`f35_routers_mode_constant_25pct`, `C.raptor.mode_cost_representation` = `mode_constant`, 250 it, 25 %), a result at 27.39 h, closed out by `run.py --close-out` after its harness died at iteration 34 (§9.176, #225); read against arm 0 of F35 (`20260912T202242_300it_25pct`, the control half of the five pairs, §9.169, #172): nothing moved outside one build's noise. Machine idle; no approval stands |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F35-the-engines-route-what-they-remode` (opened `20260912T184108`, §9.168) - nothing run before it compares with anything after it |
| Input registry | **558 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **959 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (16 September 2026 (fifty-third session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (16 September 2026 (fifty-third session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (16 September 2026 (fifty-third session)) · [network-and-inputs](positions/network-and-inputs.md) (16 September 2026 (fifty-third session)) · [population-and-demand](positions/population-and-demand.md) (16 September 2026 (fifty-third session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (16 September 2026 (fifty-third session)) · [ride-and-pairing](positions/ride-and-pairing.md) (16 September 2026 (fifty-third session)) · [runs-and-economics](positions/runs-and-economics.md) (16 September 2026 (fifty-third session)) · [sampling-and-families](positions/sampling-and-families.md) (16 September 2026 (fifty-third session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (16 September 2026 (fifty-third session)) · [signals-and-crossings](positions/signals-and-crossings.md) (16 September 2026 (fifty-third session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (16 September 2026 (fifty-third session)) · [walk-and-bike](positions/walk-and-bike.md) (16 September 2026 (fifty-third session)) |
<!-- generated:state end -->

F35 is open with arm 0 and the routers pair as its readings; nothing before
`20260912T184108` compares with them. The network is F34's footpath rebuild, the demand and plans
those of `20260910T203622` (§9.164). The manifest holds
**721 CC-BY / 220 ODbL** plus 18 bespoke files, every one hashed. The heap rule reads 37.4 GiB at
25 % against a measured live peak of 26.2 GiB on arm 0 (§9.169).

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260915T000704_250it_25pct` | completed | F35-the-engines-route-what-they-remode | 250 | ran_to_last_iteration `_run.json` |
| `20260914T195207_4it_25pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |
| `20260914T150700_2it_1pct` | completed | F35-the-engines-route-what-they-remode | 2 | ran_to_last_iteration `_run.json` |
| `20260912T202242_300it_25pct` | completed | F35-the-engines-route-what-they-remode | 300 | ran_to_last_iteration `_run.json` |
| `20260912T185005_4it_25pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |
| `20260912T184134_4it_1pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |

193 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

<!-- generated:lane start -->
1. **The roots first: one demand rebuild that seeds ride at the HTS share (#86), gives destination placement an observed short-trip shape (#30), gives bike a distance cost (#107) and consumes the household-size top-band mean (#196)** **(recommended)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at the same price as above; opens a family; blocked on: D7 (the pair's reading is in: the routers change moved nothing past the band, so the roots are next unless the user chooses the scoring pair or the bike test first); the build needs no approval, the new arm 0 a stated cost - ~28 h at 250 iterations from the pair's 362 s median (§9.176) (§9.169: ride's 20.60 % target sits above its 19.11 % coverage, fixed at the seed; walk trips average 3.74 km against 0.70; bike carries no distance cost; §9.176: the routers pair read - pt coverage 15.78 % against 17.53 % on arm 0, light rail -71.0 %, ride -40.8 % at a 19.11 % ceiling on both arms; #86 #30 #107 #196 #145)
2. **The eleventh project report, after the next reading** - one /project-report pass; no family boundary; blocked on: nothing - the pair is the reading (§9.176); one /project-report pass, no run (docs/reports/README.md;)
3. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D6.** The harness is a child of the shell that launches it, and the fifty-second session's end killed the routers pair's harness at iteration 34 while its JVM ran on. What should the launch default be? Options: Detach by default (recommended) · Refuse a foreground launch under a Claude session · Leave the default; the operator remembers --detach (§9.176: the one launch since §9.72 not made `--detach` is the one whose harness died with the shell; no ceiling, stall or gate watcher ran from iteration ~35 to 250; #225)
- **D7.** The routers pair moved nothing past the band (car -0.35 pp, ride +0.17 pp, light rail 772 → 856 boardings, heavy rail 10,092 → 10,476 against arm 0; 2 of 12 inside and 6 past the bar on both; pt coverage 17.53 → 15.78 %). What runs next? Options: The roots rebuild (recommended) · The scoring pair next · The ASC contraction test for bike alone (§9.176: the pair's reading against arm 0; §9.169: ride's 20.60 % target above its 19.11 % coverage, fixed at the seed, on both arms; #86 #30 #107 #196 #172 #174 #98 #49)

Decided: D1 = Routers pair first (recommended) (2026-09-14) · D2 = Search first, online and via the TfNSW API (2026-09-14) · D3 = Require them (recommended) (2026-09-14) · D4 = Inside F35, read against arm 0 (recommended) (2026-09-15) · D5 = Add run.py --close-out; it is a RESULT (recommended) (2026-09-16)
<!-- generated:lane end -->

## Open work

*The deviations are the scoreboard's, above; a row here names the mechanism, the issue and the next measurement, not the number (§9.176).*

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **Choice-set coverage is an arithmetic ceiling.** On arm 0: car 75.86 %, walk 63.54 %, taxi 53.72 %, bike 27.12 %, pt 17.53 %, ride 19.11 % — ride's 20.60 % target is above its coverage, fixed at the seed from it.27 (§9.169) | #86 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on both arms of the first pair |
| **Five one-field controls; the routers pair is read and moved nothing** (§9.164, §9.169, §9.176): scoring, choice set, service quality (#175) and pt submodes (#49) remain unrun; arm 0 is the control half. Against arm 0 the pair moved car −0.35 pp, light rail +84 and heavy rail +384 boardings; pt coverage 17.53 → 15.78 %. What runs next is D7 | #172 #174 #49 | [seed-and-choice-set](positions/seed-and-choice-set.md) | D7, then the next pair's or the rebuilt arm 0's reading |
| **The reading point is a convergence problem**; the windowed remedy measured worse (§9.159). The objective's denominator `CAL.objective.replication_band_pp` is 0.0 until a band is measured (§9.164) | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the band |
| **Ride, past the bar on both results**: the demand seeds ride below the target (`B.mode.bound_passenger_placement` = `every_plan`, seeded share 0.1114), and a household drives more cars than it owns (wait count 18,767 on arm 0, §9.169) | #86 #145 | [ride-and-pairing](positions/ride-and-pairing.md), [population-and-demand](positions/population-and-demand.md) | a demand that seeds ride at the HTS share |
| **Light rail under and heavy rail over, past the bar on both results**, are one split, and the router's mode constant is NOT what decides it (§9.176). Crowding has never had a control (`C.crowding.representation` `in_vehicle_time` on every arm, §9.158) | #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the crowding or service-quality control, or the rebuilt demand |
| **Ferry, past the bar on both results**, with its market present (3.60 % of trip ends within 1 km of a wharf against 5.18 % of observed POI weight, §9.163); the router's constant exonerated (§9.176); weekday tap-ons 234–1,347 at the Newcastle wharf are bounds, never targets (#185) | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split on the next arm |
| **Taxi, past the bar on both results** with 51 pp of headroom; the fleet's refusals fell to one in five (2,065 an iteration) and are no longer the mechanism (§9.169) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | the cause of the excess, on the next arm |
| **Bike, the worst mode on both results** at 8.13 km against 5.2, no distance or traffic cost in its score; both feasibility bounds ship at 0.0 (§9.163). The ASC contraction test (~15 h, no family) is decisive for bike alone: 20.46 pp of headroom; its hold lapsed with the first pair (D7) | #107 #30 | [walk-and-bike](positions/walk-and-bike.md) | D7 |
| **Walk, over 10 % on both results** on the footpath network, off the stop bar, at a 3.74 km mean against 0.70 observed; the sub-1 km share (11.13 %) is set by the gravity kernel at build time and the HTS publishes a mean, not a distribution | #30 | [walk-and-bike](positions/walk-and-bike.md) | the sub-1 km share on the next demand rebuild |
| **Headway and reliability reach MATSim** behind a gate shipped `absent` (`citysim.ServiceQualityScoring`, §9.164) | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired arm at `headway` and `headway_and_reliability` |
| **The TfNSW bespoke-table request** (mode × age, trip length by mode, occupancy by purpose, the unfolded "Other") is drafted and held; the four cells were searched on every public channel and API and found on none (§9.172); the modelled mode × demographics table exists (§9.163) | #50 | [population-and-demand](positions/population-and-demand.md) | the lodgement, then TfNSW's answer |
| **The harness dies with the shell that launched it** (§9.176, #225): the pair's watchers, record writer and viewer died at iteration 34 while its JVM ran 27.39 h to the horizon with no stall; `run.py --close-out` recovers a finished orphan, nothing yet prevents one (D6) | #225 #66 | [runs-and-economics](positions/runs-and-economics.md) | D6 - a decision, no run |
| Surrogate calibration held in reserve: ~150 evaluations at 21.5 h each is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | only if the residual proves multi-parameter |
| **The tenth report's open items** (§9.170, §9.171): #196 folds into the roots rebuild (a decision, D1); the main ruleset requires the nine test jobs (D3, §9.172); the position pages are capped and trimmed, the rule files split, the report ordinals recorded (#203 #204 #205 #207 #208 closed) | #196 #202 #209-#217 | [monitoring-and-gates](positions/monitoring-and-gates.md) | none - decisions and no-run fixes |

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
