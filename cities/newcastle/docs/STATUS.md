# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 8 September 2026 - **a window cannot flatten a trend, the
store gets its two biggest tenants back, and the teleported access leg is fixed
at the router and refused by the mobsim** (§9.159). **NO ARM RAN**: the
scoreboard below is unchanged, still `aborted_20260908T100009_300it_25pct` at
iteration 100, 1 of 12 inside. Two 1 % smoke probes ran and are readings of
nothing. **THE REMEDY §9.158 LEFT OPEN WAS BUILT AND IS MEASURED WORSE THAN THE
POINT IT REPLACES**: over the same six arms the windowed reading puts heavy rail
at **41.46** points against 24.88, bike at **6/6** arms against 4/6, and **four**
modes past the whole 10 % band instead of three. The cause retires the remedy -
every scored mode's series over it.40-it.100 is MONOTONE without a reversal (car
59.78 -> 66.94, heavy rail 27,948 -> 19,140), so the movement is a TREND and a
mean over a monotone series is its centre. **The reading point is a CONVERGENCE
problem**, and it cannot be settled while nothing is read past iteration 104.
**#164 CLOSED BY DOING IT**: both arms extracted, their cited figures verified
against the extract, **336.4 GiB** reclaimed, the store **93.4 % -> 26.1 %**, and
`results_store` gained `reclaim()`. **#165 CLOSED ON A CONTENT PASS** whose first
two forms were each wrong in opposite directions; 15 vehicle files move to CC-BY
because the assembled copies cut from them already were - **279/218**, 512 rows
agree. **#167 FILED AND ITS FIX BUILT**: teleports **520,385 -> 6**, then the
mobsim refuses the landing link because **675 of 4,123 stops (16.4 %)** sit where
walk cannot go. It ships at `beeline`. **THE ISSUE GATE IS GREEN UNSCOPED for the
first time** - 20 open, every one awaiting a stated measurement, 0 blocking.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **PARTIAL — 12 of 12 modes, but not every leg.** Every mode has a mobsim representation (freight rail as timetable-derived crossing closures, not a vehicle), and **pt access/egress walk legs are still TELEPORTED**: 70.9 % of 1,978 teleported walk legs on a 1 % run end at a `pt interaction` (§9.156). Requirement 1 says no teleportation, so this row is not met until they are network legs; **still unfiled** | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70, §9.156 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **1 of 12 at the F31 iteration-100 gate** - **car +5.4 %**; walk -11.1 % and motorbike +13.7 % next. Read on its own terms: three family boundaries separate this from F28, so no earlier gate is a comparison, including for car | below, §9.157 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22, F23) each stopped at their iteration-100 gate. `RUN.controler.last_iteration` stays 1000 and was deliberately NOT re-declared to 250: §9.7 measured 250 insufficient. The instrument exists — a 300-iteration arm switches innovation off at 240, so its post-cutoff window straddles 250 — and the first arm to pass its gate measures it | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.142, §9.7 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260908T100009_300it_25pct` at **iteration 100** (family `F31-the-car-router-reads-only-cars`, status `aborted`, 25% sample, launched 2026-09-08T10:00:09, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260908T100009_300it_25pct --it 100` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 61.4469 | 58.3222 | +5.4% | ok | share of resident linked trips |
| 2 | ride | 12.7702 | 20.6000 | -38.0% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 11.9095 | 13.4000 | -11.1% | over 10% | share of resident linked trips |
| 4 | taxi | 2.7605 | 0.9916 | +178.4% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 5.4627 | 2.2084 | +147.4% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4303 | 0.3785 | +13.7% | over 10% | share of resident linked trips |
| 7 | bus | 3.6825 | 2.3819 | +54.6% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 22,668 | 6,529 | +247.2% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,560 | 2,954 | -47.2% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0492 | 0.1429 | -65.6% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.9823 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car**. Past the 20% stop bar: **ride, taxi, bike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | six gate firings F21-F26, 7-8 modes out each; F27 citable for nothing; **F28 with 7 out and car inside**; F30 stopped at 23 on cost (§9.149, §9.153). The newest arm `20260909T015217_300it_25pct` is **RUNNING** - the DEPTH arm (§9.160), the first since F4 allowed past iteration 100 and the first ever to run `citysim.PtCrowdingScoring`; **22.3 h** against a **32 h** ceiling. It reads nothing yet, so the arm that READS is still `aborted_20260908T100009_300it_25pct` at its gate (§9.157). *Pinned by `check_doc_currency.py`.* |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F31-the-car-router-reads-only-cars` (opened `20260908T095937`, §9.154, 9.156) - nothing run before it compares with anything after it |
| Input registry | **494 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (8 September 2026 (thirty-sixth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (8 September 2026 (thirty-seventh session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (7 September 2026 (thirtieth session)) · [network-and-inputs](positions/network-and-inputs.md) (8 September 2026 (thirty-seventh session)) · [population-and-demand](positions/population-and-demand.md) (8 September 2026 (thirty-sixth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (8 September 2026 (thirty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (8 September 2026 (thirty-sixth session)) · [runs-and-economics](positions/runs-and-economics.md) (8 September 2026 (thirty-seventh session)) · [sampling-and-families](positions/sampling-and-families.md) (8 September 2026 (thirty-sixth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (8 September 2026 (thirty-sixth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (8 September 2026 (thirty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (8 September 2026 (thirty-sixth session)) |
<!-- generated:state end -->

**No arm ran on 8 September's second session, and the next one opens a family**
(§9.158). The machine stayed idle, no approval was sought or spent, and no family
row was added - a family opens at a LAUNCH or a REBUILD. But the CONTROLER IS
RECOMPILED AND GREEN (86 class files under `.tools/classes`, newest 21:12:04
against Java sources at 20:47:40), so the deployed bytecode now carries
`citysim.PtCrowdingScoring`, an escort listener that stops proposing at the
innovation cutoff and a mode-aware teleport refusal. Nothing on disk from an
earlier arm was produced by this controler. `check_package.py` last passed on
7 Sep; no data artefact was rebuilt, and the manifest still holds 512 files -
now **279 CC-BY / 218 ODbL** plus 15 bespoke, with undetermined lineage at 0
(the 15 mapped-schedule vehicle files moved on a content pass, #165).

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260909T015217_300it_25pct` | running | F31-the-car-router-reads-only-cars | - | - |
| `20260909T011135_4it_25pct` | completed | F31-the-car-router-reads-only-cars | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260908T232051_4it_1pct` | failed | F31-the-car-router-reads-only-cars | 0 | RuntimeException: Exception while processing persons. Cannot guarantee that all persons have been fully processed. |
| `aborted_20260908T231109_4it_1pct` | failed | F31-the-car-router-reads-only-cars | 0 | TransitQSimEngine$TransitAgentTriesToTeleportException: Agent 355102 tries to enter a transit stop at link 128983 but really is at 158102! |
| `aborted_20260908T100009_300it_25pct` | aborted | F31-the-car-router-reads-only-cars | 100 | Stopped automatically by the gate watcher at iteration 100 under the GOAL.md loop (RUN.gate.interval_iterations=100): GATE: 7 mode(s) at ... |
| `20260908T014214_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |

166 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **THE READING POINT NEEDS DEPTH, NOT AN AVERAGE, AND DEPTH COSTS AN ARM**
   (§9.159, #163). The window is built, declared and MEASURED WORSE: heavy rail
   **41.46** points against the point reading's 24.88, bike 4/6 arms -> **6/6**,
   four modes past the whole band instead of three, objective drift
   **0.081-0.5395 pp** and still one-signed on every arm. It cannot work,
   because the movement is a monotone TREND and an average of a monotone series
   is its centre. **The instrument is kept and its own field says it does not
   work.** What remains is to read one arm past 100 and see where each mode's
   series flattens - which is also requirement 8, unmeasured since F4.
2. **THE DEPTH ARM IS WRITTEN, COSTED, APPROVED AND NOT LAUNCHED** (§9.159).
   `depth_convergence_25pct`: 300 iterations at 25 %, innovation off at 240 so
   the post-cutoff window straddles 250, **22.2 h quoted against a measured
   22.0-31.7 h spread** and a **32 h approved ceiling**. It needs a scoped
   departure - `RUN.gate.interval_iterations = 0`, because the watcher killing
   every arm at its first gate is exactly why nothing has been read past
   iteration 104 - and that departure is justified on the overlay and recorded.
   **It was HELD at the operator's direction until this record existed to read.**
3. **#167 IS HALF FIXED AND THE HALF THAT REMAINS IS NAMED** (§9.159). The
   routing works - teleports **520,385 -> 6**, the two raptor switches coexist -
   and the mobsim then refuses the landing link, because **675 of 4,123 stop
   facilities (16.4 %)** sit on a link walk cannot use, the heavy-rail and
   light-rail platforms among them. `accessEgressModeToLink` dies at
   `PersonPrepareForSim` on 40 agents, a different failure from §9.54's. It
   ships at `beeline` and requirement 1 stays PARTIAL until the last hop onto a
   platform has a mechanism.
4. **The ASC contraction test is STILL built and not run** (§9.158, ~15 h, opens
   no family). Round 1 is proposed off the F31 gate - bike **-0.5121**, bus
   **-0.2301**, ferry **+0.6713**, light rail **+0.4143**. It was blocked by the
   reading point and still is: the depth arm is what unblocks it.
5. **Heavy rail is +247.2 % and its brake has still never run** (§9.158, #98).
   `citysim.PtCrowdingScoring` is implemented and bound; no arm has run with it
   on. The depth arm would be the first.
6. **Convergence is still unmeasured** (requirement 8): the newest reading arm
   stopped at 100, as every arm since F4 has.

**Decisions required:** **whether the depth arm launches** (item 2 - approved at
a 32 h ceiling, held for this record); how the last hop onto a platform is made
(item 3 - neither stock MATSim mechanism does it in this scenario); whether
**the real Newcastle corridor operates transit signal priority** -
`A.lightrail.tsp_enabled` is `source: assumed` and requirement 6 says derive it,
settled on evidence about the corridor and never on light rail's -47.2 %
([positions/light-rail-and-ferry](positions/light-rail-and-ferry.md), §9.156);
and the Task Scheduler log (#66). Taken this session (§9.159): the windowed
reading built, measured and refused on its own evidence; #164 and #165 closed by
doing the work; #167 filed and its fix built to the point where the remaining
gap is named; and no arm launched, because the approval was held for the record.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **THE READING POINT IS A CONVERGENCE PROBLEM.** The windowed remedy is built and MEASURED WORSE - heavy rail 41.46 points against 24.88, four modes past the whole band instead of three - because every mode's series over it.40-it.100 is monotone and an average of a trend is its centre (§9.159) | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | one arm read past iteration 100: where does each mode's series flatten, and by which iteration? |
| **The ASC contraction test, built and NOT run** (~15 h, opens no family): two damped rounds settle whether the residual is a TASTE or a MECHANISM. Round 1 is proposed off the F31 gate - bike -0.5121, bus -0.2301, ferry +0.6713, light rail +0.4143 (§9.158). Blocked by the reading point | #98 #94 #107 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | whether \|Δasc\| SHRINKS between round 1 and round 2 |
| **The issue gate is GREEN unscoped for the first time**: 20 open, every one awaiting a STATED measurement, 0 blocking. #164 and #165 were closed by doing the work rather than by labelling it (§9.159) | - | [monitoring-and-gates](positions/monitoring-and-gates.md) | it stays green only if each new defect is fixed or states its measurement |
| **Pt access/egress teleportation: fixed at the router, refused by the mobsim.** Teleports fall 520,385 -> 6 with the raptor's intermodal branch on, and then the agent cannot board because 675 of 4,123 stops (16.4 %) sit on a link walk cannot use (§9.159) | #167 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | a mechanism for the last hop onto a platform, then probe 1 re-run: teleports near zero AND four iterations completed |
| The first arm of the family the next launch opens, every issue awaiting it | #48 #86 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
| Ride VOLUME, and placement is answered: at the F31 gate the modelled mean ride trip is 9.17 km against an observed 9.76 (-6 %) while the share is -38.0 %, so the lifts the binder places are the right length and there are too few of them (§9.157) | #86 #48 | [ride-and-pairing](positions/ride-and-pairing.md) | the next arm's gate: the declared-bound-trip funnel - bound trips declared, surviving into plan memory, and selected |
| A household drives more cars than it owns: 12,317 car legs at the F26 gate with every household car out; the roster is built and enforced car-only after a global `wait` stranded the non-chain modes (§9.146, §9.148) | #145 | [population-and-demand](positions/population-and-demand.md) | the next arm's iteration 0 and gate: car departures and stuck against F26's 232,394 / 2,699 (0 expected for one-car households), `householdCar: N waited`, where the self-driven bound trips settle |
| Heavy rail +247.2 % at the F31 gate, and it now HAS a brake: `citysim.PtCrowdingScoring` charges the load-factor surplus and `C.crowding.*` are bound to `ptCrowding.*`; the fleet always carried standing room (bus 44/18, ferry 149/51, rail 98/48) and it was the DISUTILITY that was missing (§9.158) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the next arm's gate with `C.crowding.representation` = `in_vehicle_time`, against its `absent` control |
| Light rail and heavy rail: the corridor's arrivals are repaired at the demand (work 1.02x, shopping 0.99x, other 0.99x of attraction, §9.142) | #30 #98 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | both modes at the next arm's gate: the stops are a subset of the CBD and the mode is still chosen |
| Ferry: the market beyond the walk radius and a plan the memory drops | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the next arm's gate (§9.140) |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals at the next arm's gate |
| Bike, bus and walk residues — the car-less quarter | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | shares by car availability at the next arm's gate, now that a car-less escorter no longer drives (§9.144) |
| Traffic counts far below observation at 30 stations, both sides of the comparison now on one basis (§9.150) | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) · [network-and-inputs](positions/network-and-inputs.md) | counts at the next arm's gate, on the corrected basis |
| Leaf subtour mixes repaired at the seed (0 on every day type); the choice set decays in memory | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside log and mode survival on a full arm (§9.140) |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| **The TfNSW unit-record request for the NSW HTS is OUTSTANDING and had no home in this repository until now** — the published HTS is AGGREGATE ONLY, so no discrete-choice model can be estimated on this city's own observed behaviour and every behavioural coefficient is transferred or solved. Not lodged; no owner, date or reference recorded | #50 #49 | [population-and-demand](positions/population-and-demand.md) | the request's lodgement, then TfNSW's answer |
| **Surrogate/emulator calibration, held in reserve** — Bayesian optimisation over a random-forest surrogate needs only the aggregate mode shares this project already scores, which is why it is the one machine-learning route the aggregate-only data does not block; ~150 objective evaluations at the F31 arm's measured 7.66 h to a gate is ~48 days of wall clock at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | the ASC contraction test: worth starting only if the residual is genuinely multi-parameter |
| The 3 and 7 Sep assessments: 14 then 29 defects closed without a run (§9.141, §9.150); the digest's disk read is still unmeasured | #131 | [runs-and-economics](positions/runs-and-economics.md) · [network-and-inputs](positions/network-and-inputs.md) | the digest's disk read on the next arm (#131) |
| Iteration wall time and unexplained arm deaths: the F31 arm ran a median **261.03 s**, **0.5 %** from the quoted band's top anchor while the short probe's 216.0 s was 17 % optimistic, so the band is confirmed and the point never was (§9.157) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the Task Scheduler operational log once enabled - the machine-level stall is still unattributed |
| Lineage is resolved PER OUTPUT and the licence boundary is checked: OSM-in-source-while-CC-BY 129 → 0, ODbL without an OSM ancestor 21 → 0, undetermined 512 → 0 with the ratchet at 0 (§9.158, #159 closed). The blanket `networks/matsim/*` ODbL glob HAS had its content pass (§9.159, #165): 110 of 111 rows are confirmed ODbL on their own content and the 15 `transitVehicles.xml.gz` moved to CC-BY. What remains is a correctness problem and not a breach | — | [network-and-inputs](positions/network-and-inputs.md) | a content pass over those ~111 rows |
| Convergence horizon: 250 asked, 1000 declared and deliberately not re-declared (§9.142, §9.7) | — | [seed-and-choice-set](positions/seed-and-choice-set.md) | the first arm past the 240 cutoff |

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
