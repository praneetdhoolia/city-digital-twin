# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 12 September 2026 - **the footpath iteration profiled, the
engines route what they re-mode, and F35's arm 0 is running on a measured
price** (§9.168). The footpath network cost 555.5 s a recurring iteration at
25 % against 244.5 on the road graph (`20260912T135825_4it_25pct`); the JFR
profile (`20260912T162831_4it_25pct`) put a quarter of every CPU sample under
`PersonPrepareForSim`, which re-routes a WHOLE plan over any null route - and
the taxi engine's ~48,000 refusals an iteration left one in every plan they
touched. Both engines now route the trip they re-mode and restore the
original, `JointRideEngine` caches the driver's vehicle, and **family F35
opens at the controler**; its probe reads **460.0 s** (-17 %). **Arm 0
`20260912T202242_300it_25pct` launched 20:22:42 on a 39.0 h quote under a
44 h ceiling; the approval is spent; F35 has no reading.**

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **BUILT, UNMEASURED AT 25 %.** Every mode represented; pt access, egress and the raptor's transfer walks are NETWORK LEGS the qsim executes on the footpath network - `teleported=0` on the 1 % probes of both networks (§9.167, #167, #183); freight trains remain crossing closures, not mobsim vehicles (§9.70). The first 25 % reading of the access legs is arm 0's | [positions/walk-and-bike](positions/walk-and-bike.md), [positions/public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.70, §9.167 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12 at the first RESULT** (§9.162, iteration 300) - nearest are motorbike **+12.5 %** and car **+11.3 %**. Eight modes past the 20 % stop bar, and **one of them is out of reach of any constant**: ride's target exceeds its own choice-set coverage (§9.163) | below, §9.162, §9.163 |
| Convergence in ≤ 250 iterations | **MEASURED, and met only in the weak sense** (§9.162): the run RELAXES - drift **0.261 pp** over it.250-300 against a 0.5 pp tolerance - but the cutoff snap of **+2.211 pp** on car says the search was still 2.2 pp from its own optimum at 240. The §9.160 derivation it supersedes (settling ~200-210) was right on the plateau and wrong on the level | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.162, §9.160 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `20260909T015217_300it_25pct` at **iteration 300** (family `F32-crowding-reaches-scoring`, status `completed`, 25% sample, launched 2026-09-09T01:52:17, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 300, the only completion that means the run executed the horizon it declared.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260909T015217_300it_25pct --it 300` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 64.9110 | 58.3222 | +11.3% | over 10% | share of resident linked trips |
| 2 | ride | 12.1553 | 20.6000 | -41.0% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 9.8490 | 13.4000 | -26.5% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 2.9971 | 0.9916 | +202.2% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 4.7045 | 2.2084 | +113.0% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4259 | 0.3785 | +12.5% | over 10% | share of resident linked trips |
| 7 | bus | 3.4480 | 2.3819 | +44.8% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 0 | 6,529 | -100.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,224 | 2,954 | -58.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0571 | 0.1429 | -60.1% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6321 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 313.0000 | 405.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **none**. Past the 20% stop bar: **ride, walk, taxi, bike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds re-mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164), the 30 run-input sets re-assembled on the footpath network 12 Sep, `check_package.py` passed (§9.167) |
| P4 calibration | 🟡 | the newest run on disk is `20260912T202242_300it_25pct`, which is **RUNNING** - arm 0 of F35 (`f35_baseline_25pct`, 300 it, 25 %, no control on, 48 g), launched 12 Sep 20:22:42 at a 44 h ceiling on a 39.0 h quote (§9.168); its gates are the next reading. The newest completed ARM is F32's `20260909T015217_300it_25pct`, the only RESULT |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F35-the-engines-route-what-they-remode` (opened `20260912T184108`, §9.168) - nothing run before it compares with anything after it |
| Input registry | **553 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **959 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (12 September 2026 (forty-fourth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (12 September 2026 (forty-fifth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (12 September 2026 (forty-fourth session)) · [network-and-inputs](positions/network-and-inputs.md) (12 September 2026 (forty-fourth session)) · [population-and-demand](positions/population-and-demand.md) (12 September 2026 (forty-fourth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (12 September 2026 (forty-fourth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (12 September 2026 (forty-fifth session)) · [runs-and-economics](positions/runs-and-economics.md) (12 September 2026 (forty-fifth session)) · [sampling-and-families](positions/sampling-and-families.md) (12 September 2026 (forty-fifth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (12 September 2026 (forty-fourth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (12 September 2026 (forty-fourth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (12 September 2026 (forty-fifth session)) · [walk-and-bike](positions/walk-and-bike.md) (12 September 2026 (forty-fourth session)) |
<!-- generated:state end -->

**F35 IS OPEN, ARM 0 IS RUNNING, AND IT HAS NO READING** (§9.168): it opened at
the controler fix of 12 September (`20260912T184108`), and nothing before it
compares with anything after it. The network is F34's footpath rebuild, the
demand and plans those of `20260910T203622` (§9.164); the 30 run-input sets
are unchanged. The manifest holds **959** files, **721 CC-BY / 220 ODbL** plus
18 bespoke, every one hashed. The registry is **553** fields, undeclared
MATSim defaults **0**, inline literals **0**, the unit suite **457** tests. The
heap rule reads 37.4 GiB at 25 %; the probes' live heap is 19.9-20.3 GB under
48 g and arm 0's `gc.log` is the 25 % slope's measurement.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260912T202242_300it_25pct` | running | F35-the-engines-route-what-they-remode | 0 | - |
| `20260912T185005_4it_25pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |
| `20260912T184134_4it_1pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |
| `20260912T162831_4it_25pct` | completed | F34-walk-has-a-footpath-network | 4 | ran_to_last_iteration `_run.json` |
| `20260912T135825_4it_25pct` | completed | F34-walk-has-a-footpath-network | 4 | ran_to_last_iteration `_run.json` |
| `20260912T065939_4it_1pct` | completed | F34-walk-has-a-footpath-network | 4 | ran_to_last_iteration `_run.json` |

190 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **READ ARM 0 AT ITS GATES** (§9.168, #172): `20260912T202242_300it_25pct`,
   quoted 39.0 h + 33 min, ceiling 44 h, stall kill 1800 s, plans every 25.
   Every 100 iterations: all twelve modes with coverage beside each (#174);
   `modes_car_car` against the roster's wait count (#86, #145); the sub-1 km
   share against 11.17 % (#30); the pt access and egress leg lengths and the
   stub count (#167, #183); the cutoff snap beside the level (§9.162). It is
   the control half of all five pairs. If it dies, relaunch warm from the
   newest plans dump (`--warm-start`, #192).
2. **READ `gc.log` AGAINST `_progress.json` ON ARM 0** (#66, §9.168): the heap
   after a full collection over 300 iterations re-derives
   `RUN.machine.heap_per_fraction_gib` (the probes read 19.9-20.3 GB, a lower
   bound); the first stall with a collector's account decides #66.
3. **THEN THE FIVE PAIRS IN THE DECIDED ORDER** (#172): scoring -> choice set ->
   service quality -> routers -> submodes, one arm each, its own approval and
   family each, coverage read on both sides (#174).
4. **The ASC contraction test can measure something** (§9.166) and stays HELD
   until arm 0 reads. **The ninth report runs after arm 0's gate**, not before.

**Decisions required:** whether to send the drafted TfNSW bespoke-table
request (#50); each pair arm's approval when arm 0 has read. Taken this
session on clickable choices (§9.168): price arm 0 on a probe before
approving; profile before paying 47 h six times; fix both the whole-plan
re-route and the vehicle cache; open F35 at the fix rather than annotate F34;
fix both board drifts; approve arm 0 at a 44 h ceiling on the 39.0 h quote.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **THE CHOICE SET IS AN ARITHMETIC CEILING AND IT IS NOW READ.** Coverage on the landed arm: car 77.55 %, walk 63.95 %, taxi 54.62 %, bike 29.03 %, pt 25.78 %, ride 20.05 %. **Ride's 20.60 % target is above its own coverage**, so no constant reaches it; every other set shut by iteration 27, pt still opening at 233 (§9.163) | #86 #48 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on BOTH arms of the next pair - a mode whose plans score worse is the one deleted, so a share fall can be a smaller choice set |
| **FIVE ONE-FIELD CONTROLS, EACH OPENING A FAMILY, AND THE ORDER IS THE DECISION** (§9.164): scoring, choice set (`RUN.replanning.plan_selector_for_removal`, declared this session), routers, service quality (#175) and pt submodes (#49). A sixth is already SPENT - the demand's `B.mode.bound_passenger_placement`. No approval stands | #172 #174 #49 #175 | [seed-and-choice-set](positions/seed-and-choice-set.md) | which is spent first, and at what stated cost |
| **THE READING POINT IS A CONVERGENCE PROBLEM.** The windowed remedy is built and MEASURED WORSE (§9.159); #163 now awaits a DECISION on scale-normalising a per-mode deviation, which no arm settles, and the denominator is blocked on measuring a replication band | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | the replication band: 2-3 short arms, then the objective's denominator |
| **The ASC contraction test, built and NOT run** (~15 h, opens no family). Of its four modes only **bike** sits on an alternative the operator can switch to - now confirmed, at 24.32 pp of headroom against a 29.03 % coverage | #98 #94 #107 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | whether \|Δasc\| SHRINKS between round 1 and round 2 |
| **The engines route what they re-mode, and the taxi fleet refuses four requests in five** (§9.168): 47,797 of 58,558 refused at fleet 200, each now a network walk routed by the engine (~60 s of a 460 s iteration) where before each nulled a route and `PersonPrepareForSim` re-routed the whole plan every iteration | #49 #172 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | taxi's share and the refusal count at arm 0's gates |
| **Pt access, egress and transfer walks are NETWORK LEGS the qsim executes** (§9.167, #167): the refusal was the ride and taxi engines re-moding one leg of a five-leg trip; whole-trip re-mode, the raptor's transfer beelines routed, `teleported=0` on the 1 % probes of both networks; MATSim's coordinate-to-link stubs remain (median 54 m, 388 over 1 km on the footpath network against 511) | #167 #183 | [walk-and-bike](positions/walk-and-bike.md) | the access and egress leg lengths and the stub count on arm 0 |
| **WALK AND BIKE HAVE A FOOTPATH NETWORK** (§9.167, #183): 40,203 harvested ways as walk/bike links, S2 weekday walk on 363,818 links (35,381 km, 168,550 footpath-only); the modelled mean walk trip was 4.58 km against 0.70 on the road graph and its first reading on footpaths is arm 0's | #183 #30 | [walk-and-bike](positions/walk-and-bike.md) | the sub-1 km share and the mean walk trip at arm 0's gate |
| **The ferry has a disclosed observation, as bounds** (§9.167, #185): weekday tap-ons 234–1,347 at the Newcastle wharf under the publication's rounding to 100; light rail 2,090–3,751 brackets the 2,954 target. Constraints, never targets | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at arm 0's gate against the bounds |
| **The demand now STATES that the passenger rides** (§9.164): `B.mode.bound_passenger_placement` = `every_plan` puts a bound tour on `ride` in every seeded plan, as the driver has always been put on `car` - 194,131 fully bound weekday tours over 199,329 persons, seeded ride share 0.1114, every seeded ride leg a declared binding | #86 #48 #145 | [ride-and-pairing](positions/ride-and-pairing.md) | whether it drives `modes_car_car` toward zero WITHOUT the roster's wait count rising to hold it |
| A household drives more cars than it owns: the roster's wait count runs **8,550 -> 15,580** across the landed arm, binding harder as car converges (§9.163) | #145 | [population-and-demand](positions/population-and-demand.md) | the roster counter and the co-assignment split at the next arm's gate |
| Heavy rail **+220.6 %** at the landed result on the legs-table basis (+225.0 % from the plans, §9.166), with a brake that has never had a control: `C.crowding.representation` was `in_vehicle_time` on this arm and no arm in this family has run it `absent` (§9.158, §9.163) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired crowding arm, reading coverage on both sides |
| Light rail **-58.6 %** (1,224 boardings, the basis `fit.py` scores) and heavy rail **+220.6 %** are two halves of ONE split decided by a router that read no mode constant until PR #173 - and the constants now reach the run from the registry (§9.166) | #30 #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the paired raptor arm at `mode_constant` against `absent` |
| Ferry **-60.1 %** with its market present: 3.60 % of modelled trip ends within 1 km of a wharf against 5.18 % of observed POI weight, and pt coverage well above the submode targets (§9.163) | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the next arm's gate |
| Taxi **+202.2 %** with **51.62 pp of headroom** - the largest on the board, so the excess is a level a constant can move (§9.163) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals at the next arm's gate |
| Bike **+113.0 %**, ridden 7.32 km against an observed 5.2, and **8.8 % of trips among non-licence-holders against 2.5 %** among holders; both distance feasibility bounds ship at 0.0, which is their consumer's off switch (§9.163) | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | bike by car availability at the next arm's gate |
| Walk **-26.5 %** with a supply ceiling. The demand IS rebuilt (§9.164) and 547 weekday tours the whole-day discard threw away are back, but the short-end SHAPE is a property of the gravity kernel and the published HTS carries a mean and no distribution | #30 | [walk-and-bike](positions/walk-and-bike.md) | the sub-1 km share at the first F33 arm, against 11.17 % |
| Traffic counts: **#82 CLOSED**. The map was orphaned by a network rebuild and 0 of 195 rows named their road; repaired, counts read **+16.30 % mean, -1.1 % median, 0 zeros** (§9.163) | — | [network-and-inputs](positions/network-and-inputs.md) | check 7b holds the map to the network it is scored on |
| Leaf subtour mixes repaired at the seed (0 on every day type); the running counter reads **0 stand-asides** on both 1 % probes of §9.164, the first reading the cap used to hide | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside total on a FULL arm, which is the close condition |
| Mode fidelity by age, sex and employment: the MODELLED table exists (§9.163); the observed counterpart is the blocked acquisition | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| **The TfNSW acquisition is OBTAINABLE as bespoke tables** (§9.166, #50): TfNSW refuses unit records and supplies aggregate tables on request; the request is re-aimed at mode × age, trip-length distribution by mode, occupancy by purpose and the unfolded "Other" | #50 #49 | [population-and-demand](positions/population-and-demand.md) | the lodgement, then TfNSW's answer |
| **Surrogate/emulator calibration, held in reserve** — Bayesian optimisation over a random-forest surrogate needs only the aggregate mode shares this project already scores; ~150 evaluations at 21.5 h is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | the ASC contraction test: worth starting only if the residual is genuinely multi-parameter |
| **Not one MATSim default decides this model unreviewed** (§9.164): 21 -> 0, nine DECLARED at the framework's own values and twelve ACCEPTED with a written reason. #155 CLOSED | — | [network-and-inputs](positions/network-and-inputs.md) | whether any of the nine new sweeps is worth an arm |
| **Headway and reliability REACH MATSim** (§9.164): `citysim.ServiceQualityScoring` charges the boarded route's service interval and its MEASURED arrival-delay spread, both at their literature definitions, behind a gate shipped `absent` | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired arm at `headway` and at `headway_and_reliability` |
| Stalls and heap: 13.1 h of F33's arm 0 was one iteration on an awake machine (§9.166); the 25 % probes' live heap is 19.9-20.3 GB under 48 g with GC ~1 % of the wall (§9.168), a lower bound on the slope that a 4-iteration probe cannot see | #66 | [runs-and-economics](positions/runs-and-economics.md) | `gc.log` against `_progress.json` on arm 0 |
| **The objective HAS a denominator now and it is set to none** (§9.164): `CAL.objective.replication_band_pp` = 0.0 divides nothing until a band is measured, because choosing one from its own sweep would invent the observation it represents | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the band |
| Convergence horizon: 250 asked, 1000 declared and deliberately not re-declared (§9.142, §9.7); the first arm past the 240 cutoff has now run (§9.162) | — | [seed-and-choice-set](positions/seed-and-choice-set.md) | the second arm past a cutoff, in whatever family opens next |

## Do not re-raise

- The 143 holdout targets stay closed until the end, and no target is deleted after the fact (§12).
- The record is never rewritten; superseded text is bannered and pointed past (§9.79).
- SCATS is implemented, not assumed (§9.88); the operated plans and the offset library are what remains unobtained.
- No multi-hour run without a stated-cost approval, and approvals are spent on use; no launch while an open issue lacks `awaiting-run` (GOAL.md requirement 10).
- One arm at a time; never recompile `.tools/classes` while one runs (#66).
- The taxi fare is not a lever (§9.91); freight trains are not mobsim vehicles (§9.70); SCATS offsets are not adapted (§9.88).

Where the old board went: the batch tables 4.1–4.15, the P1/P2 delivery
tables, the run-cost history and every narrative section are archived verbatim
in [`archived/SESSION_LOG.md`](archived/SESSION_LOG.md) under *Board narrative
retired 30 August 2026*; the origin proposal's deliverables are recorded in
[`GOAL.md`](GOAL.md) as superseded.

## How to resume

Run `/onboard`. By hand: `python src/run/session_gate.py --digest` prints the
goal, the scoreboard, the state and whether the machine is busy; then read
[`GOAL.md`](GOAL.md), this board, the brief
([`NEXT_AGENT_BRIEF.md`](NEXT_AGENT_BRIEF.md)) and the
position page for the lane. `python src/run/session_gate.py` runs every gate.
