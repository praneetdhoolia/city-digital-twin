# STATUS — the board

*One page: how far the twin is from [the goal](GOAL.md), what runs, and what is
next. The blocks between `generated` markers are written by
`python src/analyse/build_status_board.py` from the artefacts; the hand-written
rest is capped by `tests/check_doc_shape.py`. The current truth per topic is in
[`positions/`](positions); the history and every rationale in
[`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 22 September 2026 (fifty-eighth session). Mumbai's transit vehicles carry evidenced capacities and the sampler scales their road space; two 1 % cases measured the heap on the live set and a gridlock the fraction cannot carry (§9.206).
The scoreboard is Newcastle's; Mumbai's 1 % cases are structural measurements, not readings: 43 % of their agents were removed stuck. D14 is taken; D15 (the host or a merged network) is asked.

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
Read from `20260916T063903_250it_25pct` at **iteration 250** (family `F35-the-engines-route-what-they-remode`, status `completed`, 25% sample, launched 2026-09-16T06:39:07, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 250, the only completion that means the run executed the horizon it declared.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260916T063903_250it_25pct --it 250` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 63.9166 | 58.3222 | +9.6% | ok | share of resident linked trips |
| 2 | ride | 12.3163 | 20.6000 | -40.2% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 11.7538 | 13.4000 | -12.3% | over 10% | share of resident linked trips |
| 4 | taxi | 2.3136 | 0.9916 | +133.3% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.3684 | 2.2084 | +188.4% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.3579 | 0.3785 | -5.4% | ok | share of resident linked trips |
| 7 | bus | 1.9494 | 2.3819 | -18.2% | over 10% | share of resident linked trips |
| 8 | heavy_rail | 10,092 | 6,529 | +54.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 928 | 2,954 | -68.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0556 | 0.1429 | -61.1% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6457 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
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
| P4 calibration | 🟡 | the newest run on disk is `20260922T005949_4it_1pct`, which **RAN TO ITS LAST ITERATION**: the corrected 1 % Mumbai case (evidenced fleet, scaled transit PCE), a structural measurement of the flow identity at 0.01 — 81,722 agents still en route at 36:00 and 114,414 removed stuck of 269,690 in iteration 0 (§9.206). Newcastle remains at `20260916T063903_250it_25pct`, completed inside F35 (§9.177). **The next 25 % arm is the first with standing room and transit PCE scaled (§9.203, §9.206, #237) and opens a new family.** No run approval stands. |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F35-the-engines-route-what-they-remode` (opened `20260912T184108`, §9.168) - nothing run before it compares with anything after it |
| Input registry | **574 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **959 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (17 September 2026 (fifty-fourth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (22 September 2026 (fifty-eighth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (16 September 2026 (fifty-third session)) · [network-and-inputs](positions/network-and-inputs.md) (22 September 2026 (fifty-eighth session)) · [population-and-demand](positions/population-and-demand.md) (17 September 2026 (fifty-fourth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (17 September 2026 (fifty-fourth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (17 September 2026 (fifty-fourth session)) · [runs-and-economics](positions/runs-and-economics.md) (17 September 2026 (fifty-fourth session)) · [sampling-and-families](positions/sampling-and-families.md) (22 September 2026 (fifty-eighth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (17 September 2026 (fifty-fourth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (16 September 2026 (fifty-third session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (16 September 2026 (fifty-third session)) · [walk-and-bike](positions/walk-and-bike.md) (17 September 2026 (fifty-fourth session)) |
<!-- generated:state end -->

F35 is open with arm 0 and the routers pair as its readings; nothing before
`20260912T184108` compares with them. The network is F34's footpath rebuild, the demand and plans
those of `20260910T203622` (§9.164). The manifest holds
**724 CC-BY / 220 ODbL** plus 15 bespoke files, every one hashed. The heap rule reads 37.4 GiB at
25 % against a measured live peak of 26.2 GiB on arm 0 (§9.169).

The separate package audit fails on stale document paths (#234) and incomplete run-input report coverage (#235); full package consistency is unverified (§9.178).

## Runs on disk

<!-- generated:runs start -->
| run | city | status | family | reached | cause / note |
|---|---|---|---|---:|---|
| `20260922T005949_4it_1pct` | mumbai | completed | - | 4 | ran_to_last_iteration `_run.json` |
| `20260921T231313_4it_1pct` | mumbai | completed | - | 4 | ran_to_last_iteration `_run.json` |
| `20260921T220701_2it_0.1pct` | mumbai | completed | - | 2 | ran_to_last_iteration `_run.json` |
| `aborted_20260921T220524_2it_0.1pct` | mumbai | failed | - | - | launch refused before MATSim started: C:\Users\Praneet Dhoolia\work\city-digital-twin\cities\mumbai\data/processed/zones/sa1_to_lga.csv m... |
| `20260921T182708_2it_100pct` | mumbai | completed | - | 2 | ran_to_last_iteration `_run.json` |
| `20260921T180105_2it_1pct` | newcastle | completed | F35-the-engines-route-what-they-remode | 2 | ran_to_last_iteration `_run.json` |

225 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

<!-- generated:lane start -->
1. **Merge the mapped network's degree-2 link chains (length, capacity, lanes, modes and mapped stops preserved) and re-run the 1 % lean-agent case: if the stuck share falls from 43 % to the reference city's order, the equivalence series of scaling.md (0.5 / 1 / 2 %) follows on this host; if not, the fraction needs D15's host** **(recommended)** - a network merge and one remap of the combined feed (~1 h of builds), then the 1 % case at 1.3 h (`python src/analyse/arm_cost.py --run-config lean_agent_one_percent --iterations 4` prices it on 20260922T005949_4it_1pct); no arm; opens no family (no result compares yet); no family boundary; blocked on: D15 for anything above 2 %; nothing for the merge and the 1 % case (9.206: both 1 % cases removed 114,414-122,192 of 269,690 agents stuck with 81,722-154,759 still en route at 36:00; the network's median link is 65 m and 41 % are under 50 m, so at 0.01 a link stores under a tenth of a vehicle; the live heap is 31 GiB at 1 % and 55 at 2 %; #239)
2. **The Java fold on the idle machine: the held-ride refusal in `GatedSubtourModeChoice` (D12's gate half, #86), the taxi fleet's own sample fraction (#215), the ride engine's thread pools (#216), the zero-second timed-out ride (#217), #187's restore counters and the telemetry twins - one recompile of `.tools/classes`, verified on a 1 % smoke** - no arm; one recompile (`bootstrap_toolchain.py --verify`) and a 1 % smoke of a few minutes; no family until the roots rebuild ships it; no family boundary; blocked on: nothing - the machine is idle (the scoring pair landed 17 September 2026) (9.177: prepared and held under the arm because .tools/classes is never recompiled under one; report #12's ledger rows on the Java; #86 #187 #215 #216 #217)
3. **The roots rebuild, re-scoped by report #12: hold escort members and joint companions to ride on their bound tours (#86, D12), consume the household-size top-band mean (#196), give bike a distance cost derived from its observed mean trip length (#107, D9), re-derive the ferry target from the disclosed TPA tap-on series (#94, D8) and report the short-trip band on placed coordinates (#30)** - a demand rebuild (~2 h of builds) that opens a family and re-baselines every pair; then a new arm 0 at a probe-priced stated cost (25.1 h for 250 iterations on the scoring pair's stopwatch, spread 24.5-32.8 h; `python src/analyse/arm_cost.py --iterations 250 --fraction 0.25`); opens a family; blocked on: the Java fold landing first (one recompile of .tools/classes on the idle machine: the held-ride gate is half of D12), then a 25 % probe on the rebuilt inputs for the price and a stated-cost approval (9.177: 20.62 % of core legs bound, 59.0-59.3 % of bound trips ride on both pairs, the seed at 14.9 %; the 17.70 % short-trip supply at the seed; the scoring pair moved nothing, so the new arm 0 ships with RUN.replanning.score_msa_representation = absent; D8-D12 taken 16 September 2026; #30 #86 #94 #107 #145 #196)
4. **Bring the commuter ferry crossings into Mumbai's feed from the Maritime Board directory (Ferry Wharf-Mora/Rewas/Mandwa, Gateway-Mandwa, Versova-Madh, Marve-Manori, Gorai-Borivali, Belapur-Nerul), each on its OSM ferry way or the water line between its jetties, its window from the directory's first and last departures, its vessel capacity through a fleet profile** - a feed-builder change and one mapping of the combined feed (build_matsim_network.py --stage schedules, ~30 min); no arm; the 0.1 % structural check afterwards (6 min); no family boundary; blocked on: nothing (9.206: the extract holds two route=ferry relations (Elephanta, Vasai-Bhayander); the target's port groups (9.205) are the crossings the directory lists and the feed lacks; #245)
5. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D15.** Both 1 % Mumbai cases gridlock with the transit fleet's road space scaled (114,414-122,192 of 269,690 agents removed stuck): at 0.01 every link is a gate of one vehicle per 200 s with storage for one, and 41.5 % of the network's nodes are pass-through, so merging them doubles a 65 m median link to about 130 m - still a sixth of a vehicle's storage at 1 %. Memory is no longer the first constraint (31 GiB at 1 %, 55 at 2 %, 247 at 10 % on this 63 GB host). Which way to a fraction a reading can stand on? Options: Merge the degree-2 link chains and re-run the 1 % case as the diagnostic, then take the host if the stuck share holds · A larger host (cloud or workstation, 384-512 GB) for a 10 % core, after the merge diagnostic (recommended) · Hold Mumbai at the structural checks and finish the reference city first (9.206: two 1 % cases (20260921T231313_4it_1pct, 20260922T005949_4it_1pct); the link-length distribution of scenarios/matsim/BASE/network.xml.gz; the live-set heap rule; #239)

Decided: D10 = Document the scoped departure: gate off while a control is differenced against its arm 0 (recommended) (2026-09-16) · D11 = Yes - set the strict policy (recommended) (2026-09-16) · D12 = Hold escort members and joint companions to ride on their bound tours; car-less lift and shared passengers keep walk/bike/pt (recommended) (2026-09-16) · D13 = The notified Mumbai Metropolitan Region as the core, the four-district envelope as the external tier (recommended) (2026-09-21) · D14 = Measure a leaner agent first on a 1 % case, then decide the host (recommended) (2026-09-21)
<!-- generated:lane end -->

## Open work

*The deviations are the scoreboard's, above; a row here names the mechanism, the issue and the next measurement, not the number (§9.176).*

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **Choice-set coverage is an arithmetic ceiling, and it is a share of TRIPS.** Identical on three results (ride 19.11 %, pt 15.78–17.53 %); ride's coverage is the bound trips' share sitting AT its target, so its deficit is what bound trips execute as (§9.177) | #86 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on the roots rebuild's arm 0 |
| **Two one-field controls are run and both moved nothing** (§9.176, §9.177): the routers and the scoring branches are exonerated; the choice set (#174), service quality (#175) and pt submodes (#49) remain unrun; the cutoff snap (car +1.68 to +1.77 pp on three results) is selection, not scoring. The roots rebuild goes at the demand first | #172 #174 #49 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the rebuilt arm 0's reading, then the choice-set pair |
| **The reading point is a convergence problem**; the windowed remedy measured worse (§9.159). The objective's denominator `CAL.objective.replication_band_pp` is 0.0 until a band is measured (§9.164) | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the band |
| **Ride, past the bar on three results**: the binders bind the observed share (20.62 % of core legs) and 59 % of bound trips ride — car-available escort members and joint companions drive themselves on half and a third of theirs (`measure_bound_trips.py`, §9.177). D12 holds them to ride at the roots rebuild | #86 #145 | [ride-and-pairing](positions/ride-and-pairing.md), [population-and-demand](positions/population-and-demand.md) | `measure_bound_trips.py` on the rebuilt arm 0 |
| **Light rail under and heavy rail over, past the bar on both results**, are one split, and the router's mode constant is NOT what decides it (§9.176). Crowding has never had a control (`C.crowding.representation` `in_vehicle_time` on every arm, §9.158) | #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the crowding or service-quality control, or the rebuilt demand |
| **Ferry, past the bar on three results against a derived target the disclosed bound contradicts**: the cross-harbour market is 305 trips and the ferry takes a sixth of it; modelled boardings (1,148–1,236) sit inside the 234–1,347 tap-on bound (`measure_near_wharf.py`, §9.177). D8 re-derives the target from the TPA series at the rebuild | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the re-derived target and the wharf split on the rebuilt arm 0 |
| **Taxi, past the bar on both results** with 51 pp of headroom; the fleet's refusals fell to one in five (2,065 an iteration) and are no longer the mechanism (§9.169) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | the cause of the excess, on the next arm |
| **Bike, the worst mode on three results** at 8.10–8.13 km against 5.2, ridden 2.9 % by the car-available and 14.6–14.8 % by the car-less at 10–11 km (`mode_by_demographics.py`, §9.177); no distance cost in its score. D9 derives one from the observed mean, swept on its spread, at the rebuild | #107 | [walk-and-bike](positions/walk-and-bike.md) | bike's mean trip on the rebuilt arm 0 |
| **Walk, over 10 % on three results**, at a 3.74 km mean against 0.70 observed; the short trips are AT the seed (17.70 % against the 18.8 % band) and car takes half of them at execution (`extract_metrics.trip_geometry`, §9.177) — #30 is re-aimed at allocation, no new kernel | #30 | [walk-and-bike](positions/walk-and-bike.md) | the routed short-trip split on the rebuilt arm 0 |
| **Headway and reliability reach MATSim** behind a gate shipped `absent` (`citysim.ServiceQualityScoring`, §9.164) | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired arm at `headway` and `headway_and_reliability` |
| **The TfNSW bespoke-table request** (mode × age, trip length by mode, occupancy by purpose, the unfolded "Other") is drafted and held; the four cells were searched on every public channel and API and found on none (§9.172); the modelled mode × demographics table exists (§9.163) | #50 | [population-and-demand](positions/population-and-demand.md) | the lodgement, then TfNSW's answer |
| Surrogate calibration held in reserve: ~150 evaluations at 21.5 h each is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | only if the residual proves multi-parameter |
| **Report #12's open items** (20260916T062246; §9.177): the Java fold (#215 #216 #217, #187's counters, the held-ride gate) waits for an idle machine - it is idle now; nine extract adapters work at import (#232); the mobsim's parallel efficiency is unmeasured (#231); 25 %-only and the stated cost are enforced by nobody (#209) | #187 #209 #215 #216 #217 #231 #232 | [monitoring-and-gates](positions/monitoring-and-gates.md) | none - no-run fixes, then the rebuild |
| **Standing room was never scaled at 25 %, and transit vehicles' road space never was** (§9.203, §9.206): every F35 arm ran trams with 210 standing places and buses at four times their share of a 25 %-scaled lane; both fixed in the sampler, so every arm after opens a family | #237 | [sampling-and-families](positions/sampling-and-families.md) | peak standing occupancy per vehicle type and the count-station reading on the first arm after the fix |
| **The second city** (§9.201–§9.206): the mapped vehicles carry evidenced capacities (a 12-car EMU 1,168 + 3,816, not the mapper's 400 seats); both 1 % cases gridlock — 114,414–122,192 of 269,690 agents removed stuck — on a network whose median link is 65 m, so a 1 % link stores under a tenth of a vehicle; the live heap is 7.4 GiB + ~19 KB a plan | #239 #245 | [network-and-inputs](positions/network-and-inputs.md), [`cities/mumbai/docs/scaling.md`](../cities/mumbai/docs/scaling.md) | the 1 % case on a degree-2-merged network (D15), then the fraction the host holds |

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
