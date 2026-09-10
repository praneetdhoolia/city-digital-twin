# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 10 September 2026 - **a deviation no constant can reach**
(§9.163). MATSim has written the choice-set coverage table on every arm this
project ever ran and nothing read it. It bounds the whole calibration: a
scoring constant reallocates between plans an agent already holds, so a mode's
coverage is a ceiling on its share. On the landed result at iteration 300 the
bound bites once and decisively - **ride's target of 20.6000 % sits ABOVE the
20.05 % of agents who have ever held a ride plan**, against a 12.1553 % share,
so no value of any constant closes ride's -41.0 %. Every mode's choice set is
within a point of its final coverage by iteration 5-10 and shut by 16-27,
**except pt**, still opening at 233 and reaching only **25.78 %**. **THE COUNTS
RUNG HAD BEEN MEASURING THE WRONG ROADS FOR 25 DAYS** - the station-to-link map
was written 47 minutes before the network it keys was rewritten, **0 of 195 rows
still named their road** - and on the repaired map counts read **+16.30 % mean,
-1.1 % median, 0 modelled zeros** against -89.35 % / -98.7 % / 7. Fourteen of
sixteen issues marked `awaiting-run` were measured from a run that had already
finished. **No arm ran and no approval was sought or spent.**

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **PARTIAL — 12 of 12 modes, but not every leg.** Every mode has a mobsim representation (freight rail as timetable-derived crossing closures, not a vehicle), and **pt access/egress walk legs are still TELEPORTED**: 70.9 % of 1,978 teleported walk legs on a 1 % run end at a `pt interaction` (§9.156). Requirement 1 says no teleportation, so this row is not met until they are network legs; **still unfiled** | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70, §9.156 |
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
| 8 | heavy_rail | 21,220 | 6,529 | +225.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,260 | 2,954 | -57.3% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0571 | 0.1429 | -60.1% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6321 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **none**. Past the 20% stop bar: **ride, walk, taxi, bike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | six gate firings F21-F26, 7-8 modes out each; **F28 with 7 out and car inside**; F30 stopped at 23 on cost (§9.149, §9.153). The newest arm `20260909T015217_300it_25pct` is **RAN TO ITS LAST ITERATION** - 300 of 300 in **21.5 h**, the FIRST result since F4 on 21 August. It **RELAXED** (drift 0.261 pp over it.250-300 against 0.5) and reads **0 of 12 inside 10 %, 8 past the stop bar**: the cutoff at 240 snapped car **+2.211 pp**. *Pinned by `check_doc_currency.py`.* |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F32-crowding-reaches-scoring` (opened `20260909T011135`, §9.158, 9.160) - nothing run before it compares with anything after it |
| Input registry | **499 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (10 September 2026 (fortieth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (10 September 2026 (fortieth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (10 September 2026 (fortieth session)) · [network-and-inputs](positions/network-and-inputs.md) (10 September 2026 (fortieth session)) · [population-and-demand](positions/population-and-demand.md) (8 September 2026 (thirty-sixth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (10 September 2026 (fortieth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (10 September 2026 (fortieth session)) · [runs-and-economics](positions/runs-and-economics.md) (10 September 2026 (fortieth session)) · [sampling-and-families](positions/sampling-and-families.md) (9 September 2026 (thirty-ninth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (10 September 2026 (fortieth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (10 September 2026 (fortieth session)) · [walk-and-bike](positions/walk-and-bike.md) (10 September 2026 (fortieth session)) |
<!-- generated:state end -->

**No arm ran this session either, and the next one opens a family.** The machine
stayed idle throughout, no approval was sought or spent, and no family row was
added - a family opens at a LAUNCH or a REBUILD. But the CONTROLER IS RECOMPILED
AND GREEN, so the deployed bytecode carries `citysim.RaptorModeCostCalculator`
(at `absent`), `citysim.PtCrowdingScoring`, an escort listener that stops
proposing at the innovation cutoff, a mode-aware teleport refusal, and the
running counts on both mixed-subtour diagnostics that were capped at five dumps
(§9.163). Nothing on disk from an earlier arm was produced by this controler.
`check_package.py` last passed on 7 Sep; **one derived artefact changed** -
`data/processed/validation/count_station_links.csv`, regenerated against the
network it is scored on and re-hashed in the manifest (§9.163, #82) - and the
manifest still holds 512 files, **279 CC-BY / 218 ODbL** plus 15 bespoke, with
undetermined lineage at 0. The registry is **499** fields after two behaviour-
neutral declarations, and undeclared MATSim defaults fell **31 -> 21**.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260909T015217_300it_25pct` | completed | F32-crowding-reaches-scoring | 300 | ran_to_last_iteration `_run.json` |
| `20260909T011135_4it_25pct` | completed | F32-crowding-reaches-scoring | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260908T232051_4it_1pct` | failed | F31-the-car-router-reads-only-cars | 0 | RuntimeException: Exception while processing persons. Cannot guarantee that all persons have been fully processed. |
| `aborted_20260908T231109_4it_1pct` | failed | F31-the-car-router-reads-only-cars | 0 | TransitQSimEngine$TransitAgentTriesToTeleportException: Agent 355102 tries to enter a transit stop at link 128983 but really is at 158102! |
| `aborted_20260908T100009_300it_25pct` | aborted | F31-the-car-router-reads-only-cars | 100 | Stopped automatically by the gate watcher at iteration 100 under the GOAL.md loop (RUN.gate.interval_iterations=100): GATE: 7 mode(s) at ... |
| `20260908T014214_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |

166 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **THE CHOICE SET IS THE CEILING, AND ONE TARGET IS ALREADY ABOVE IT** (§9.163,
   #174, #86). Ride cannot reach 20.6000 % because only 20.05 % of agents have
   ever held a ride plan; every other mode's set is shut by iteration 27 and pt's
   reaches 25.78 %. **Read coverage on both arms of every pair from now on** - a
   crowding or raptor arm makes a mode's plans score worse, and the worst plan is
   the one MATSim deletes, so a share fall can be a smaller choice set rather
   than a changed preference.
2. **THREE ONE-FIELD CONTROLS EXIST AND EACH OPENS A FAMILY** (§9.163, #172).
   Scoring: `RUN.replanning.score_msa_representation` = `at_innovation_cutoff`,
   the only candidate that predicts BOTH measured symptoms. Router:
   `C.raptor.mode_cost_representation` = `mode_constant`, built and never run.
   Choice set: `replanning.planSelectorForRemoval`, which has no control until it
   is declared (#155, #174). **The order they are spent in is the decision** -
   all three move the same quantity, and no approval stands.
3. **#169 - the ceiling watcher is BUILT and UNPROVEN** (§9.161). The 1 % smoke
   probe needs only an idle machine, which it has. A launch with no automatic
   stop of either kind is now refused before the JVM starts (§9.163).
4. **#167 - ONE ATTRIBUTE, AND A REBUILD** (§9.161). Emit `routingMode` per leg
   in `build_matsim_plans.py` and rebuild the demand and the 30 run-input sets in
   the SAME change, then re-run the 1 % intermodal probe. The same field
   (`routing.accessEgressType` = `none`) is why a car trip costs only its travel
   time and 18 c/km, which is why car takes 63.12 % of sub-kilometre trips.
5. **The ASC contraction test stays HELD** (§9.160). Of its four modes only bike
   sits on an alternative the mode-choice operator can switch to - and bike is
   now confirmed to have 24.32 pp of headroom, so it is the one it can answer.

**Decisions required:** the ORDER the three one-field controls are spent in, and
at what stated cost, since **no approval stands** (§9.163); whether
`replanning.planSelectorForRemoval` and the other 20 undeclared MATSim defaults
become registry fields (#155, #174); whether `C.time_weights.beta_headway` and
`beta_reliability` are wired or retired - the gradient precedent does NOT
transfer, because a MATSim agent has perfect timetable knowledge and so pays no
schedule-delay cost at all (#175); whether the declared passenger of an escort
pair is PUT on `ride` at the demand (#86, #48); the three product calls behind
#49, #50 and #155; whether the real Newcastle corridor operates transit signal
priority (`A.lightrail.tsp_enabled` is `source: assumed`, settled on evidence
about the corridor and never on light rail's -57.3 %); and whether the Windows
Task Scheduler operational log is enabled, without which #66 stays
unattributable. Taken this session: fourteen of sixteen `awaiting-run` issues
measured from the landed arm rather than a new one, #82 and #93 closed on
evidence, and `beta_headway` NOT retired on the record's own precedent.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **THE CHOICE SET IS AN ARITHMETIC CEILING AND IT IS NOW READ.** Coverage on the landed arm: car 77.55 %, walk 63.95 %, taxi 54.62 %, bike 29.03 %, pt 25.78 %, ride 20.05 %. **Ride's 20.60 % target is above its own coverage**, so no constant reaches it; every other set shut by iteration 27, pt still opening at 233 (§9.163) | #86 #48 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on BOTH arms of the next pair - a mode whose plans score worse is the one deleted, so a share fall can be a smaller choice set |
| **THREE ONE-FIELD CONTROLS, EACH OPENING A FAMILY, AND THE ORDER IS THE DECISION** (§9.163): scoring (`RUN.replanning.score_msa_representation`), router (`C.raptor.mode_cost_representation`), choice set (`replanning.planSelectorForRemoval`, undeclared). No approval stands | #172 #174 #155 #49 | [seed-and-choice-set](positions/seed-and-choice-set.md) | which is spent first, and at what stated cost |
| **THE READING POINT IS A CONVERGENCE PROBLEM.** The windowed remedy is built and MEASURED WORSE (§9.159); #163 now awaits a DECISION on scale-normalising a per-mode deviation, which no arm settles, and the denominator is blocked on measuring a replication band | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | the replication band: 2-3 short arms, then the objective's denominator |
| **The ASC contraction test, built and NOT run** (~15 h, opens no family). Of its four modes only **bike** sits on an alternative the operator can switch to - now confirmed, at 24.32 pp of headroom against a 29.03 % coverage | #98 #94 #107 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | whether \|Δasc\| SHRINKS between round 1 and round 2 |
| **The issue gate is GREEN unscoped**: 22 open - **9** awaiting a run with a stated measurement (each a PAIRED arm or a probe), 6 awaiting implementation, 7 awaiting a decision, 0 blocking. Sixteen were `awaiting-run` at session start and fourteen were measured from a run that had already finished (§9.163) | #172 | [monitoring-and-gates](positions/monitoring-and-gates.md) | the next arm, whichever control it carries |
| **Pt access/egress teleportation: fixed at the router, refused by the mobsim.** Teleports fall 520,385 -> 6 with the raptor's intermodal branch on, and then the agent cannot board because 675 of 4,123 stops (16.4 %) sit on a link walk cannot use (§9.159). The same field decides whether a car trip carries any fixed cost at all | #167 #30 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | a mechanism for the last hop onto a platform, then probe 1 re-run: teleports near zero AND four iterations completed |
| **Ride's loss is the passenger's MODE ASSIGNMENT, not pairing and not selection** (§9.163): of 20,902 declared escort pairs in sample, 10,224 have the passenger driving their own car against 7,821 co-assigned, with 99.6 % of tours realised and the windows ample | #86 #48 #145 | [ride-and-pairing](positions/ride-and-pairing.md) | whether a demand fix drives `modes_car_car` toward zero WITHOUT the roster's wait count rising to hold it |
| A household drives more cars than it owns: the roster's wait count runs **8,550 -> 15,580** across the landed arm, binding harder as car converges (§9.163) | #145 | [population-and-demand](positions/population-and-demand.md) | the roster counter and the co-assignment split at the next arm's gate |
| Heavy rail **+225.0 %** at the landed result, with a brake that has never had a control: `C.crowding.representation` was `in_vehicle_time` on this arm and no arm in this family has run it `absent` (§9.158, §9.163) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired crowding arm, reading coverage on both sides |
| Light rail **-57.3 %** and heavy rail **+225.0 %** are two halves of ONE split decided by a router that read no mode constant until PR #173 | #30 #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the paired raptor arm at `mode_constant` against `absent` |
| Ferry **-60.1 %** with its market present: 3.60 % of modelled trip ends within 1 km of a wharf against 5.18 % of observed POI weight, and pt coverage well above the submode targets (§9.163) | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the next arm's gate |
| Taxi **+202.2 %** with **51.62 pp of headroom** - the largest on the board, so the excess is a level a constant can move (§9.163) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals at the next arm's gate |
| Bike **+113.0 %**, ridden 7.32 km against an observed 5.2, and **8.8 % of trips among non-licence-holders against 2.5 %** among holders; both distance feasibility bounds ship at 0.0, which is their consumer's off switch (§9.163) | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | bike by car availability at the next arm's gate |
| Walk **-26.5 %** with a supply ceiling: sub-1 km trips move 11.06 % -> 10.97 % across 200 iterations while car's share of them rises 60.67 % -> 63.12 % (§9.163) | #30 | [walk-and-bike](positions/walk-and-bike.md) | a demand rebuild; no equilibrium moves a quantity fixed at build time |
| Traffic counts: **#82 CLOSED**. The map was orphaned by a network rebuild and 0 of 195 rows named their road; repaired, counts read **+16.30 % mean, -1.1 % median, 0 zeros** (§9.163) | — | [network-and-inputs](positions/network-and-inputs.md) | check 7b holds the map to the network it is scored on |
| Leaf subtour mixes repaired at the seed (0 on every day type); the stand-aside diagnostic was capped at five dumps and now carries a running count (§9.163) | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside total on a full arm - decidable for the first time |
| Mode fidelity by age, sex and employment: the MODELLED table exists (§9.163); the observed counterpart is the blocked acquisition | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| **The TfNSW unit-record request for the NSW HTS is OUTSTANDING** — the published HTS is AGGREGATE ONLY, so no discrete-choice model can be estimated on this city's own behaviour. Named on the board since 8 Sep and asked for by three consecutive assessments; still not lodged, no owner, no date | #50 #49 | [population-and-demand](positions/population-and-demand.md) | the request's lodgement, then TfNSW's answer |
| **Surrogate/emulator calibration, held in reserve** — Bayesian optimisation over a random-forest surrogate needs only the aggregate mode shares this project already scores; ~150 evaluations at 21.5 h is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | the ASC contraction test: worth starting only if the residual is genuinely multi-parameter |
| **Thirty-one MATSim defaults decided the model unreviewed; 21 remain and every one decides queue physics, route choice, scoring or the choice set** (§9.163) | #155 #174 | [network-and-inputs](positions/network-and-inputs.md) | each ACCEPTED with a reason or DECLARED with units, provenance and a sweep |
| **Headway and reliability are declared, swept and never reach MATSim** — and the gradient precedent does not transfer, because a MATSim agent has perfect timetable knowledge and pays no schedule-delay cost at all | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | wired at a hook whose signature was read first, or retired with that reason recorded |
| Iteration wall time and unexplained arm deaths: the landed arm ran 21.5 h uninterrupted with a recovered mid-run excursion to 301.5 s, closing at 244.05 s (§9.163) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the Task Scheduler operational log, which is off and records nothing until enabled |
| **No deviation on the board carries an error bar**, and a MATSim run is not bit-reproducible: within the landed arm the folded objective moves 0.272-0.418 pp between iterations 80 and 100. Asked for by three consecutive assessments | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the objective's denominator |
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
