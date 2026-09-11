# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 11 September 2026 - **the eighth report, and a launcher that
refuses what the dead arm did** (§9.166). Arm 0's 6.5 h was 20.9 h: 13.1 h of it
inside iteration 89 on an awake machine, the Task Scheduler log (live at last)
ruling out a sleep and a scheduled job (#66). The launcher now refuses a heap
below the registry's own rule (31.4 GiB at 25 %), stops a JVM silent for 30 min
(`stopped_at_stall`), writes a GC log by default, keeps a warm start's cutoff,
and refuses an overlay that changes nothing the run reads - which found the
`C.asc.*` constants reaching the config from the built C1 table, so the ASC
contraction test would have measured nothing; they reach the run now. `trim()`
removes through the declared selector (#174's control was half-switched) and the
controler is recompiled with F33 unread. The report's own audit: 76 of 105 prior
recommendations taken, the goal count unmoved - every model-side control is
built and none has run. 13 issues filed (#180-#192), 8 groomed. **F33 still has
no reading; arm 0 is not relaunched; no approval stands.**

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **PARTIAL — every mode represented, not every leg simulated.** **Pt access/egress walk legs are still TELEPORTED** - 1,401 on `20260910T204747_4it_1pct`, every one `walk via pt` - so requirement 1 is unmet until they are network legs (#167). Half that fix landed: every leg states its `routingMode`, taking the failure **40 agents -> 20** (§9.164) | [positions/public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.70, §9.164 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12 at the first RESULT** (§9.162, iteration 300) - nearest are motorbike **+12.5 %** and car **+11.3 %**. Eight modes past the 20 % stop bar, and **one of them is out of reach of any constant**: ride's target exceeds its own choice-set coverage (§9.163) | below, §9.162, §9.163 |
| Convergence in ≤ 250 iterations | **MEASURED, and met only in the weak sense** (§9.162): the run RELAXES - drift **0.261 pp** over it.250-300 against a 0.5 pp tolerance - but the cutoff snap of **+2.211 pp** on car says the search was still 2.2 pp from its own optimum at 240. The §9.160 derivation it supersedes (settling ~200-210) was right on the plateau and wrong on the level | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.162, §9.160 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260910T222830_300it_25pct` at **iteration 90** (family `F33-the-passenger-is-put-on-ride`, status `failed`, 25% sample, launched 2026-09-10T22:28:30, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and this reading is citable at its `reached_iteration` and nowhere past it.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260910T222830_300it_25pct --it 90` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 58.8585 | 58.3222 | +0.9% | ok | share of resident linked trips |
| 2 | ride | 15.5705 | 20.6000 | -24.4% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 13.0363 | 13.4000 | -2.7% | ok | share of resident linked trips |
| 4 | taxi | 2.6201 | 0.9916 | +164.2% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 4.3623 | 2.2084 | +97.5% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.3614 | 0.3785 | -4.5% | ok | share of resident linked trips |
| 7 | bus | 3.7408 | 2.3819 | +57.0% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 23,984 | 6,529 | +267.4% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,340 | 2,954 | -54.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0263 | 0.1429 | -81.6% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 6.1748 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car, walk, motorbike**. Past the 20% stop bar: **ride, taxi, bike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | the newest run on disk is `aborted_20260910T222830_300it_25pct`, which is **DEAD AND ITS RECORD SAYS WHY** - F33's arm 0, `OutOfMemoryError` in iteration 98 on a 14 GB heap its overlay failed to raise to the landed arm's 40 GB, 13.1 h of its 20.9 h stalled inside iteration 89 (§9.165, §9.166); no warm-start point. **F33 has no reading.** The newest RESULT is `20260909T015217_300it_25pct`, **0 of 12 inside 10 %, 8 past the stop bar** (§9.162), in the family before the open one. *Pinned by `check_doc_currency.py`.* |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F33-the-passenger-is-put-on-ride` (opened `20260910T203622`, §9.164) - nothing run before it compares with anything after it |
| Input registry | **521 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (11 September 2026 (forty-third session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (11 September 2026 (forty-third session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (11 September 2026 (forty-third session)) · [network-and-inputs](positions/network-and-inputs.md) (11 September 2026 (forty-third session)) · [population-and-demand](positions/population-and-demand.md) (11 September 2026 (forty-third session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (11 September 2026 (forty-third session)) · [ride-and-pairing](positions/ride-and-pairing.md) (11 September 2026 (forty-third session)) · [runs-and-economics](positions/runs-and-economics.md) (11 September 2026 (forty-third session)) · [sampling-and-families](positions/sampling-and-families.md) (11 September 2026 (forty-third session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (11 September 2026 (forty-third session)) · [signals-and-crossings](positions/signals-and-crossings.md) (11 September 2026 (forty-third session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (11 September 2026 (forty-third session)) · [walk-and-bike](positions/walk-and-bike.md) (11 September 2026 (forty-third session)) |
<!-- generated:state end -->

**F33 IS OPEN, HAS NO READING, AND ITS CONTROLER WAS RECOMPILED WITHOUT COST**
(§9.166): `trim()` and the mode-choice guard changed bytecode, and because no
F33 arm has a reading there is nothing for the new bytecode to be incomparable
with - the family stands. The demand, the plans and the 30 run-input sets are
those of `20260910T203622` (§9.164); the population was not rebuilt (the
mobility draw's four new fields evaluate the expression it always did). The
manifest still holds **512** files, **279 CC-BY / 218 ODbL** plus 15 bespoke,
undetermined lineage 0. The registry is **521** fields, undeclared MATSim
defaults **0** and now a CI gate, the unit suite **349** tests. The emitted
config for the shipped values is byte-identical to the one arm 0 ran on; what
changed is what a launch REFUSES and what the reader COUNTS (pt boardings from
the legs table: light rail 1,224 / heavy rail 20,932 on the landed result).

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `aborted_20260910T222830_300it_25pct` | failed | F33-the-passenger-is-put-on-ride | 98 | OutOfMemoryError: Java heap space |
| `20260910T215129_4it_25pct` | completed | F33-the-passenger-is-put-on-ride | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260910T205517_20it_1pct` | aborted | F33-the-passenger-is-put-on-ride | 3 | Stopped automatically by the ceiling watcher at 0.05 h against an approved ceiling of 0.05 h (RUN.gate.wall_ceiling_h), at iteration 4. T... |
| `20260910T204747_4it_1pct` | completed | F33-the-passenger-is-put-on-ride | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260910T204626_4it_1pct` | failed | F33-the-passenger-is-put-on-ride | 0 | RuntimeException: Exception while processing persons. Cannot guarantee that all persons have been fully processed. |
| `aborted_20260910T204513_4it_1pct` | failed | F33-the-passenger-is-put-on-ride | - | launch refused before MATSim started: no modeParams/RUN/routing.access_egress_type in the config |

173 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **RELAUNCH ARM 0 ON A FRESH APPROVAL - IT IS PRICED, CORRECTED, AND EVERY
   REFUSAL IS IN PLACE** (§9.165, §9.166, #172). `f33_baseline_25pct.json`: no
   control on, 40 g, GC log on, `create_graphs` off, a stall kill at 1800 s; 19.0
   h at 225.0 s recurring, spread 20.5-24.7 h. Its 26 h ceiling line encodes an
   approval that is SPENT; ask, set the ceiling to what is approved, launch with
   `--detach`. It measures the demand fix (#86, #48, #145, #30) and is the
   control half of all five pairs.
2. **THEN THE FIVE PAIRS IN THE DECIDED ORDER** (#172): scoring -> choice set ->
   service quality -> routers -> submodes, one arm each, coverage read on both
   sides (#174). The choice-set pair now switches BOTH removal paths.
3. **READ `gc.log` AGAINST `_progress.json` ON ARM 0** (#66). The first stall
   with a collector's account decides whether 11 September was a heap event.
4. **#167 IS A DIAGNOSIS, NOT A REBUILD** (§9.164): name where inside MATSim's
   pre-sim pass the mixed-routing-mode trip is made; until then a car trip
   carries no fixed cost.
5. **The ASC contraction test can now measure something** (§9.166): the
   constants reach the run from the registry. It stays HELD until arm 0 reads.
6. **The next project report runs after arm 0's gate**, not before (the skill's
   cadence rule, §9.166).

**Decisions required:** a stated-cost approval for arm 0 (none stands); the
footpath network - one deliberate rebuild or a recorded acceptance (#183); the
freight trains at the two crossings - an ARTC request or a count at the gates
(#184); whether a warm-completed arm is a result (#192); the heavy-rail target's
holdout sum (#189); the ride engine's plan mutation (#187); when the four large
consolidations (#180, #181, #182, #191) get their session - after the F33 pairs
by the 11 September decision. Taken this session: Java defect fixes now and the
refactors later; the reports move under the city.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **THE CHOICE SET IS AN ARITHMETIC CEILING AND IT IS NOW READ.** Coverage on the landed arm: car 77.55 %, walk 63.95 %, taxi 54.62 %, bike 29.03 %, pt 25.78 %, ride 20.05 %. **Ride's 20.60 % target is above its own coverage**, so no constant reaches it; every other set shut by iteration 27, pt still opening at 233 (§9.163) | #86 #48 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on BOTH arms of the next pair - a mode whose plans score worse is the one deleted, so a share fall can be a smaller choice set |
| **FIVE ONE-FIELD CONTROLS, EACH OPENING A FAMILY, AND THE ORDER IS THE DECISION** (§9.164): scoring, choice set (`RUN.replanning.plan_selector_for_removal`, declared this session), routers, service quality (#175) and pt submodes (#49). A sixth is already SPENT - the demand's `B.mode.bound_passenger_placement`. No approval stands | #172 #174 #49 #175 | [seed-and-choice-set](positions/seed-and-choice-set.md) | which is spent first, and at what stated cost |
| **THE READING POINT IS A CONVERGENCE PROBLEM.** The windowed remedy is built and MEASURED WORSE (§9.159); #163 now awaits a DECISION on scale-normalising a per-mode deviation, which no arm settles, and the denominator is blocked on measuring a replication band | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | the replication band: 2-3 short arms, then the objective's denominator |
| **The ASC contraction test, built and NOT run** (~15 h, opens no family). Of its four modes only **bike** sits on an alternative the operator can switch to - now confirmed, at 24.32 pp of headroom against a 29.03 % coverage | #98 #94 #107 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | whether \|Δasc\| SHRINKS between round 1 and round 2 |
| **The issue gate is GREEN unscoped**: **32** open after #180-#192 were filed on the eighth report's findings, 0 blocking; 17 await a paired arm with a stated measurement, 15 await a decision or a session (§9.166) | #172 | [monitoring-and-gates](positions/monitoring-and-gates.md) | arm 0, then the pairs |
| **Pt access/egress teleportation: HALF fixed.** Every leg states its `routingMode`, taking the `accessEgressModeToLink` failure **40 agents -> 20** at 1 %; the input is clean (0 mixed trips over 6,347 persons) and the consistency check is not the mechanism, so the residual is made inside MATSim's own pre-sim pass (§9.164). The same field decides whether a car trip carries any fixed cost at all | #167 #30 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | where in the pre-sim pass the mixed trip is created |
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
| Stalls and heap: 13.1 h of arm 0 was one iteration on an awake machine (Task Scheduler log: ~450 launches, no gap, no sleep); the JVM at a 14 g ceiling is what remains, and only a GC log settles it (§9.166) | #66 | [runs-and-economics](positions/runs-and-economics.md) | `gc.log` against `_progress.json` on arm 0 |
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
