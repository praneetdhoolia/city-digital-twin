# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 14 September 2026 - **arm 0 landed as the project's
second result, the reader got its rail back, and the horizon is declared at
250** (§9.169). `20260912T202242_300it_25pct` ran 300 of 300 in 30.35 h against
a 39.0 h quote: **2 of 12 inside 10 %** (car +9.6 %, motorbike -5.6 %) and six
past the stop bar, ride's target above its own 19.11 % coverage. The ninth
report found the reader resolving every run's stops through the CITY's
rebuilt schedule - the F32 result read heavy rail 0 on the board while its own
fit said +225 % - and it reads the run's own schedule now. **No arm was
launched and no approval stands**: the user chose to close out; the five
pairs, each on its own approval at 250 iterations, are next.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **BUILT AND MEASURED AT 25 %.** Every mode represented; pt access, egress and the raptor's transfer walks are NETWORK LEGS the qsim executed on arm 0 - 27,765 of them, 0 teleported (§9.169, #167, #183); freight trains remain crossing closures, not mobsim vehicles (§9.70) | [positions/walk-and-bike](positions/walk-and-bike.md), [positions/public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.70, §9.169 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **2 of 12 at the second RESULT** (§9.169, arm 0 at iteration 300): car **+9.6 %** and motorbike **-5.6 %**. Six modes past the 20 % stop bar, and **one of them is out of reach of any constant**: ride's 20.60 % target exceeds its 19.11 % choice-set coverage, fixed at the seed (§9.169) | below, §9.169, §9.163 |
| Convergence in ≤ 250 iterations | **MEASURED TWICE, met in the weak sense, and the horizon is now DECLARED** (§9.169): arm 0 drifts **0.128 pp** over it.250-300 against the 0.5 pp tolerance with a cutoff snap of **+1.683 pp** on car, and the innovated state moved 0.42 pp between it.200 and 240 - so `RUN.controler.last_iteration` is 250 (cutoff 200) for the pair arms; whether 200 iterations of SEARCH suffice stays unmeasured (§9.43) | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.169, §9.162 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `20260912T202242_300it_25pct` at **iteration 300** (family `F35-the-engines-route-what-they-remode`, status `completed`, 25% sample, launched 2026-09-12T20:22:42, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 300, the only completion that means the run executed the horizon it declared.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260912T202242_300it_25pct --it 300` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 63.9092 | 58.3222 | +9.6% | ok | share of resident linked trips |
| 2 | ride | 12.0233 | 20.6000 | -41.6% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 11.7677 | 13.4000 | -12.2% | over 10% | share of resident linked trips |
| 4 | taxi | 2.2948 | 0.9916 | +131.4% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.6605 | 2.2084 | +201.6% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.3572 | 0.3785 | -5.6% | ok | share of resident linked trips |
| 7 | bus | 2.0045 | 2.3819 | -15.8% | over 10% | share of resident linked trips |
| 8 | heavy_rail | 10,092 | 6,529 | +54.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 772 | 2,954 | -73.9% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0524 | 0.1429 | -63.3% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6251 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 405.0000 | 405.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **car, motorbike**. Past the 20% stop bar: **ride, taxi, bike, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds re-mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164), the 30 run-input sets re-assembled on the footpath network 12 Sep (§9.167) and again on the 250-iteration horizon 14 Sep (§9.169), `check_package.py` passed |
| P4 calibration | 🟡 | the newest run on disk is `20260912T202242_300it_25pct`, which **RAN TO ITS LAST ITERATION** - arm 0 of F35 (`f35_baseline_25pct`, 300 it, 25 %, no control on, 48 g), 30.35 h under a 44 h ceiling, the project's second RESULT and F35's reading (§9.169). It is the control half of the five pairs (#172); no pair is approved |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F35-the-engines-route-what-they-remode` (opened `20260912T184108`, §9.168) - nothing run before it compares with anything after it |
| Input registry | **553 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **959 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (14 September 2026 (forty-sixth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (14 September 2026 (forty-sixth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (14 September 2026 (forty-sixth session)) · [network-and-inputs](positions/network-and-inputs.md) (14 September 2026 (forty-sixth session)) · [population-and-demand](positions/population-and-demand.md) (14 September 2026 (forty-sixth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (14 September 2026 (forty-sixth session)) · [ride-and-pairing](positions/ride-and-pairing.md) (14 September 2026 (forty-sixth session)) · [runs-and-economics](positions/runs-and-economics.md) (14 September 2026 (forty-sixth session)) · [sampling-and-families](positions/sampling-and-families.md) (14 September 2026 (forty-sixth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (14 September 2026 (forty-sixth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (14 September 2026 (forty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (14 September 2026 (forty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (14 September 2026 (forty-sixth session)) |
<!-- generated:state end -->

**F35 IS OPEN AND HAS ITS READING** (§9.169): arm 0 is the newest citable
reading and a RESULT; nothing before `20260912T184108` compares with it. The
network is F34's footpath rebuild, the demand and plans those of
`20260910T203622` (§9.164); the 30 run-input sets carry the declared
250-iteration horizon (one line per config). The manifest holds **959** files,
**721 CC-BY / 220 ODbL** plus 18 bespoke, every one hashed. The registry is
**553** fields, undeclared MATSim defaults **0**, inline literals **0**, the
unit suite **469** tests. The heap rule reads 37.4 GiB at 25 % against a
measured live peak of 26.2 GiB on arm 0's `gc.log` (§9.169).

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260912T202242_300it_25pct` | completed | F35-the-engines-route-what-they-remode | 300 | ran_to_last_iteration `_run.json` |
| `20260912T185005_4it_25pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |
| `20260912T184134_4it_1pct` | completed | F35-the-engines-route-what-they-remode | 4 | ran_to_last_iteration `_run.json` |
| `20260912T162831_4it_25pct` | completed | F34-walk-has-a-footpath-network | 4 | ran_to_last_iteration `_run.json` |
| `20260912T135825_4it_25pct` | completed | F34-walk-has-a-footpath-network | 4 | ran_to_last_iteration `_run.json` |
| `20260912T065939_4it_1pct` | completed | F34-walk-has-a-footpath-network | 4 | ran_to_last_iteration `_run.json` |

190 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **THE FIRST PAIR ARM, ON ITS OWN APPROVAL** (#172, §9.169): one field
   against arm 0, 250 iterations at 25 % (~25.5 h quoted on arm 0's clock,
   spread 21.7-46.9 h at 300), coverage read on both sides (#174), the
   overlay declaring `answers_issues`. The ORDER is the user's: the decided
   sequence is scoring -> choice set -> service quality -> routers ->
   submodes; on arm 0's evidence the routers pair (`C.raptor.mode_cost_representation`
   = `mode_constant`) answers three of the six STOP modes and is recommended first.
2. **OR THE ROOTS FIRST** (§9.169): ride is seeded below its own target's
   coverage (#86), walk trips are five times too long at the demand's
   destination placement (#30), bike carries no distance or traffic cost
   (#107). Each is a demand rebuild that opens a family and re-baselines;
   the pairs would then difference against that baseline, not arm 0.
3. **The tenth report runs after the next reading**, not before (§9.166);
   the ninth's follow-on is done - its fixable findings fixed, the overtaken
   issues closed, the rest re-aimed at the pair that measures them.
4. **The ASC contraction test** stays HELD; bike is the mode it can answer
   (24.32 pp of headroom on F32, 20.46 pp on arm 0's 27.12 % coverage, §9.169).

**Decisions required:** which pair (or which root) is next, and its
stated-cost approval; whether to send the drafted TfNSW bespoke-table
request (#50, HELD this session). Taken this session on clickable choices
(§9.169): no arm; `RUN.controler.last_iteration` 250 for the pairs; #50 held.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **THE CHOICE SET IS AN ARITHMETIC CEILING, READ ON BOTH RESULTS.** Coverage on arm 0: car 75.86 %, walk 63.54 %, taxi 53.72 %, bike 27.12 %, pt 17.53 %, ride 19.11 %. **Ride's 20.60 % target is above its coverage**, which is fixed at the seed from it.27, so no constant reaches it; pt was still opening at 240 (§9.169) | #86 #48 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on BOTH arms of the first pair - a mode whose plans score worse is the one deleted |
| **FIVE ONE-FIELD CONTROLS, EACH OPENING A FAMILY, AND THE ORDER IS THE DECISION** (§9.164, §9.169): scoring, choice set (`RUN.replanning.plan_selector_for_removal`), routers, service quality (#175) and pt submodes (#49); arm 0 is the control half of all five. A sixth is SPENT - the demand's `B.mode.bound_passenger_placement`. No approval stands | #172 #174 #49 #175 | [seed-and-choice-set](positions/seed-and-choice-set.md) | which is spent first, at 250 iterations and at what stated cost |
| **THE READING POINT IS A CONVERGENCE PROBLEM.** The windowed remedy is built and MEASURED WORSE (§9.159); #163 now awaits a DECISION on scale-normalising a per-mode deviation, which no arm settles, and the denominator is blocked on measuring a replication band | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | the replication band: 2-3 short arms, then the objective's denominator |
| **The ASC contraction test, built and NOT run** (~15 h, opens no family). Of its four modes only **bike** sits on an alternative the operator can switch to - now confirmed, at 24.32 pp of headroom against a 29.03 % coverage | #98 #94 #107 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | whether \|Δasc\| SHRINKS between round 1 and round 2 |
| **The engines route what they re-mode, and the fleet's refusals fell to one in five** (§9.169): 2,065 refused an iteration at it.300 of arm 0 (~18 % of 11,409 requests), each routed as a network walk in 1.3 s, against 47,797 of 58,558 on the F34 profile probe - and taxi still reads +131.4 %, so the refusals are no longer the mechanism | #49 #172 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | taxi's share on the first pair |
| **Pt access, egress and transfer walks are NETWORK LEGS, MEASURED ON A RESULT** (§9.169, #167): 8,687 pt trips on arm 0 carry 27,765 network walk legs (median 461 m, 5,748 over 1 km) and 41,243 coordinate stubs (median 19 m, 18 over 1 km against the 1 % probe's 388); no teleported leg in the legs table | #167 #183 | [walk-and-bike](positions/walk-and-bike.md) | closed on this evidence |
| **WALK AND BIKE HAVE A FOOTPATH NETWORK, AND ITS FIRST READING IS IN** (§9.169, #183): walk **-12.2 %** on arm 0 (off the stop bar) at a 3.74 km mean trip against 0.70 observed (4.58 on the road graph); bike **+201.6 %** at 8.10 km against 5.2 | #183 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | the sub-1 km share and the bike cost on the next demand rebuild |
| **The ferry has a disclosed observation, as bounds, and light rail is BELOW its bound** (§9.167, §9.169, #185): weekday tap-ons 234-1,347 at the Newcastle wharf; light rail 2,090-3,751 brackets the 2,954 target, and arm 0 reads **772** - under the lower bound. Constraints, never targets | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split and the rail split on the routers pair |
| **The demand STATES that the passenger rides, and it seeds ride below the target** (§9.164, §9.169): `B.mode.bound_passenger_placement` = `every_plan` puts a bound tour on `ride` in every seeded plan - 194,131 fully bound weekday tours, seeded ride share 0.1114 - and arm 0's ride coverage is 19.11 % from it.27 against a 20.60 % target: the ceiling is the seed, not plan memory | #86 #48 #145 | [ride-and-pairing](positions/ride-and-pairing.md) | a demand that seeds ride at the HTS share, a rebuild that opens a family |
| A household drives more cars than it owns: the roster's wait count runs **8,550 -> 15,580** across the F32 result and reads **18,767** on arm 0, binding harder as car converges (§9.163, §9.169) | #145 | [population-and-demand](positions/population-and-demand.md) | the roster counter and the co-assignment split on the first pair |
| Heavy rail **+54.6 %** on arm 0 (10,092 boardings against 6,529, §9.169; +220.6 % on the F32 result before the pt access leg became a network walk) with a brake that has never had a control: `C.crowding.representation` was `in_vehicle_time` on both and no arm has run it `absent` (§9.158) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired crowding arm, reading coverage on both sides |
| Light rail **-73.9 %** (772 boardings) and heavy rail **+54.6 %** on arm 0 are two halves of ONE split decided by a router that reads no mode constant (§9.169); `C.raptor.mode_cost_representation` = `mode_constant` is built, unrun, and the recommended first pair | #30 #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the paired raptor arm at `mode_constant` against `absent` |
| Ferry **-63.3 %** on arm 0 (83 resident trips, 328 sampled boardings, §9.169) with its market present: 3.60 % of modelled trip ends within 1 km of a wharf against 5.18 % of observed POI weight on the F32 result (§9.163) | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split on the routers pair |
| Taxi **+131.4 %** on arm 0 with 51 pp of headroom (coverage 53.72 %, §9.169) - the excess is a level a constant can move, and the fleet's refusals are no longer behind it (2,065 an iteration, ~18 %) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | the cause of the excess, on the first pair |
| Bike **+201.6 %** on arm 0, ridden 8.10 km against an observed 5.2 (§9.169; +113.0 % at 7.32 km on the F32 result), with no distance or traffic cost in its score (#107); both distance feasibility bounds ship at 0.0, which is their consumer's off switch (§9.163) | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | bike by car availability on the first pair |
| Walk **-12.2 %** on arm 0, off the stop bar on the footpath network (§9.169), with a supply ceiling: the sub-1 km share reads 11.13 % (11.17 % on F32; the demand is unchanged), because the short-end SHAPE is a property of the gravity kernel and the published HTS carries a mean and no distribution | #30 | [walk-and-bike](positions/walk-and-bike.md) | the sub-1 km share on the next demand rebuild |
| Traffic counts: **#82 CLOSED**. The map was orphaned by a network rebuild and 0 of 195 rows named their road; repaired, counts read **+16.30 % mean, -1.1 % median, 0 zeros** (§9.163) | — | [network-and-inputs](positions/network-and-inputs.md) | check 7b holds the map to the network it is scored on |
| Leaf subtour mixes repaired at the seed (0 on every day type); the stand-aside counter reads **5** on the whole of arm 0, all in its first two iterations - the first full-arm reading (§9.169) | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | closed on this evidence if 5 is the floor the demand's spanning mixes set |
| Mode fidelity by age, sex and employment: the MODELLED table exists (§9.163); the observed counterpart is the blocked acquisition | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| **The TfNSW acquisition is OBTAINABLE as bespoke tables** (§9.166, #50): TfNSW refuses unit records and supplies aggregate tables on request; the request is re-aimed at mode × age, trip-length distribution by mode, occupancy by purpose and the unfolded "Other" | #50 #49 | [population-and-demand](positions/population-and-demand.md) | the lodgement, then TfNSW's answer |
| **Surrogate/emulator calibration, held in reserve** — Bayesian optimisation over a random-forest surrogate needs only the aggregate mode shares this project already scores; ~150 evaluations at 21.5 h is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | the ASC contraction test: worth starting only if the residual is genuinely multi-parameter |
| **Not one MATSim default decides this model unreviewed** (§9.164): 21 -> 0, nine DECLARED at the framework's own values and twelve ACCEPTED with a written reason. #155 CLOSED | — | [network-and-inputs](positions/network-and-inputs.md) | whether any of the nine new sweeps is worth an arm |
| **Headway and reliability REACH MATSim** (§9.164): `citysim.ServiceQualityScoring` charges the boarded route's service interval and its MEASURED arrival-delay spread, both at their literature definitions, behind a gate shipped `absent` | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired arm at `headway` and at `headway_and_reliability` |
| Stalls and heap: 13.1 h of F33's arm 0 was one iteration on an awake machine (§9.166); arm 0 of F35 ran 30.35 h under 48 g with no stall, its live heap peaking at 26.2 GiB with no slope over 300 iterations (§9.169); the launcher now refuses a concurrent arm | #66 | [runs-and-economics](positions/runs-and-economics.md) | a second full arm's `gc.log` at 25 % |
| **The objective HAS a denominator now and it is set to none** (§9.164): `CAL.objective.replication_band_pp` = 0.0 divides nothing until a band is measured, because choosing one from its own sweep would invent the observation it represents | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the band |
| Convergence horizon: 250 asked and now **250 declared** (§9.169, superseding §9.142's refusal on §9.7's pre-rebuild measurement); the second arm past a cutoff has run and drifts 0.128 pp | — | [seed-and-choice-set](positions/seed-and-choice-set.md) | the it.200-250 drift band on the first pair against arm 0's |

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
