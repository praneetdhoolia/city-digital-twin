# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 7 September 2026 — the first F26 arm ran to its
iteration-100 gate and the watcher stopped it with **8 modes out**, walk newly
past the bar (−22.7 %) and car at +11.5 %; no mode inside 10 %. The column
built that morning (§9.145) answered at once: **the declared pairs hold**
(`miss_declared_absent` 719 of 77,399) and the pairing loss is **12,461 ride
legs on persons the demand never bound**, proposed by the coherence listener's
inference while the gate refused 192,000 of the same kind. Selection measured
at the trip level for the first time: **45.5 % of declared bound trips ride;
29,827 are driven by the passenger** — and **12,317 car legs began while every
car the household owns was already out** (§9.146, #145). Three roots, all
physical identities with a control member: the listener re-proposes declared
pairs only; a household drives the cars the census gives it and the second
driver waits; a carve never draws a bound passenger. **Then the iteration
itself was cut** (§9.147: a milestone cost twice a plain one; trips every 10,
plans and events at the gate; the detour routing parallel, 41 s → 2 s; 16
mobsim threads on a probe) **and the first F27 arm exposed my own error**
(§9.148): `wait` is global in MATSim and stranded walk and taxi — 55,862 car
agents stuck at iteration 0 — so the arm was stopped at 19, the constraint
is now car-only in a handler of our own, and **F28 opens at the fix**. The
scoreboard below is F26's reading at 100 and compares with nothing after it.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12** at the F26 iteration-100 gate — car +11.5 % and motorbike +11.1 % are the closest, and car was INSIDE at +0.4 % at iteration 40 before overshooting as walk fell through its target to −22.7 %. Only bus's F22 +8.0 % and F24's motorbike have ever been inside at a gate | below, §9.146, §9.136 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22, F23) each stopped at their iteration-100 gate. `RUN.controler.last_iteration` stays 1000 and was deliberately NOT re-declared to 250: §9.7 measured 250 insufficient. The instrument exists — a 300-iteration arm switches innovation off at 240, so its post-cutoff window straddles 250 — and the first arm to pass its gate measures it | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.142, §9.7 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260906T100429_300it_25pct` at **iteration 100** (family `F26-a-driver-owns-a-car`, status `aborted`, 25% sample, launched 2026-09-06T10:04:29, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260906T100429_300it_25pct --it 100` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 65.0395 | 58.3222 | +11.5% | over 10% | share of resident linked trips |
| 2 | ride | 12.0327 | 20.6000 | -41.6% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 10.3526 | 13.4000 | -22.7% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 2.5480 | 0.9916 | +157.0% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 4.8166 | 2.2084 | +118.1% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4207 | 0.3785 | +11.1% | over 10% | share of resident linked trips |
| 7 | bus | 3.3459 | 2.3819 | +40.5% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 21,852 | 6,529 | +234.7% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,304 | 2,954 | -55.9% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0421 | 0.1429 | -70.5% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.7617 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
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
| P4 calibration | 🟡 | the gate loop has fired six times: F21 with 8 out (§9.134); F22 with 7 out and bus inside (§9.136); F23 with 7 out (§9.139); F24 with 7 out and motorbike inside; F25 with 7 out and none (§9.143); F26 with 8 out and none, walk newly past the bar (§9.146). F27's one arm was stopped at 19 under a global `wait` that stranded the non-chain modes, citable for nothing (§9.148). **F28 is built and unlaunched** — the listener declared-only, the household vehicle roster enforced car-only, the carve off bound passengers, the iteration cut (§9.146–§9.148) |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F28-the-car-waits-only-for-a-car` (opened `20260907T025531`, §9.148) - nothing run before it compares with anything after it |
| Input registry | **470 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (4 September 2026 (twenty-seventh session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (6 September 2026 (thirtieth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (6 September 2026 (thirtieth session)) · [network-and-inputs](positions/network-and-inputs.md) (4 September 2026 (twenty-seventh session)) · [population-and-demand](positions/population-and-demand.md) (7 September 2026 (thirtieth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (4 September 2026 (twenty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (6 September 2026 (thirtieth session)) · [runs-and-economics](positions/runs-and-economics.md) (7 September 2026 (thirtieth session)) · [sampling-and-families](positions/sampling-and-families.md) (6 September 2026 (thirtieth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (5 September 2026 (twenty-eighth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026 (twenty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (4 September 2026 (twenty-seventh session)) |
<!-- generated:state end -->

**Family F26 is open and NO arm has run in it** (§9.144): chains, plans and the
30 run-input sets were rebuilt 6 Sep so that every declared ride driver owns a
car — escort bindings 127,073 → 120,971, lift 47,496 → 44,180, shared 116,760 →
126,402, so all four passes total 375,007 → 375,307 and the seeded ride share
0.0444 → 0.0448. `check_package.py` ALL CHECKS PASSED; the manifest holds 512
files. The boundary is on the DEMAND only — the run side, the network and
`controler_sha256` are F25 unchanged. Pace is MEASURED at ~306–325 s an
iteration on the F25 arm, so 300 iterations is ~26–27 h. No arm runs.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260907T025531_2it_1pct` | completed | F28-the-car-waits-only-for-a-car | 2 | ran_to_last_iteration `_run.json` |
| `aborted_20260907T025046_2it_1pct` | failed | F27-a-household-drives-the-cars-it-owns | 0 | RuntimeException: could not find requested vehicle 271437 in simulation for agent BasicPlanAgentImpl{plan=[score=undefined][nof_acts_legs... |
| `aborted_20260907T024623_2it_1pct` | failed | F27-a-household-drives-the-cars-it-owns | 0 | RuntimeException: could not find requested vehicle 271437 in simulation for agent BasicPlanAgentImpl{plan=[score=undefined][nof_acts_legs... |
| `aborted_20260907T002431_300it_25pct` | aborted | F27-a-household-drives-the-cars-it-owns | 20 | Stopped by the operator at iteration ~21 under the GOAL.md loop, step 3 (fix from the root): RUN.qsim.vehicle_behavior=wait is GLOBAL in ... |
| `20260906T233901_4it_25pct` | completed | F27-a-household-drives-the-cars-it-owns | 4 | ran_to_last_iteration `_run.json` |
| `20260906T225712_4it_25pct` | completed | F27-a-household-drives-the-cars-it-owns | 4 | ran_to_last_iteration `_run.json` |

152 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Launch F28's first arm** (§9.148): every open issue carries
   `awaiting-run` (#145 opened on this session's own measurement), so
   `issue_gate.py` passes. Cost: the F27 arm's own stopwatch read a plain
   iteration at **322–349 s** and a milestone at +15 s (§9.147, §9.148), so
   300 iterations is nearer **28 h**. Read its iteration-0 `legHistogram`
   FIRST: car departures near F26's 232,394 and stuck near 2,699 say the
   handler is car-only; tens of thousands stuck means stop.
2. **What the arm answers, in order** (§9.146): the roster — car legs starting
   with every household car out (12,317 at F26, 0 expected for one-car
   households) and where the 29,827 self-driven bound trips settle; the
   listener — ride legs on unbound persons (12,461 at F26, ~0 expected) and the
   pair rate against 0.7865; then ride itself against −41.6 %, with car
   (+11.5 %), walk (−22.7 %), bike and taxi read together as the seesaw.
3. **The selection half is the larger one and is now measured**: 45.5 % of
   declared bound trips ride; 18,495 walk and 4,993 bike on a trip a driver
   was declared for. Once the second car is gone, what remains is the score
   of a lift against a walk for a car-less person — the next root if the
   roster does not move it.
4. **Convergence is still unmeasured** (requirement 8). F25 was approved for its
   full horizon to measure it, and the gate and the horizon collided at
   iteration 100; the loop won, by the user's decision. It waits for an arm with
   a chance of being inside the bars.

**Decisions required:** whether a fifth binder pass is needed now
the reachable binding volume is ~18.7 % rather than 20.13 %; enable the Task
Scheduler operational log (#66); whether the S2 base grants the tram signal
priority ([positions/signals-and-crossings](positions/signals-and-crossings.md)).
Taken this session: §9.98's window refusal stands (§9.145); extending the
listener cross-household is moot — `miss_declared_absent` 719 says the declared
pairs hold (§9.146).
## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The first F26 arm's gate, every issue awaiting it | #48 #86 #49 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
| Ride: declared pairs hold at the F26 gate (`miss_declared_absent` 719); the loss is 12,461 ride legs without a driver (listener now declared-only) and 45.5 % selection on bound trips (§9.146) | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | the F27 gate: ride legs on unbound persons (~0 expected), pair rate against 0.7865, the bound-trip selection rate against 0.455 |
| A household drives more cars than it owns: 12,317 car legs at the F26 gate with every household car out; the roster is built and enforced car-only after a global `wait` stranded the non-chain modes (§9.146, §9.148) | #145 | [population-and-demand](positions/population-and-demand.md) | the F28 arm's iteration 0: car departures and stuck against F26's 232,394 / 2,699; then the gate: that count (0 expected for one-car households), `householdCar: N waited`, where the self-driven bound trips settle |
| Heavy rail +193 % at the F23 gate; income scaling blunts the fare (§9.139) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | where rail settles once the corridor's CBD end (#30) is repaired |
| Light rail and heavy rail: the corridor's arrivals are repaired at the demand (work 1.02x, shopping 0.99x, other 0.99x of attraction, §9.142) | #30 #84 #98 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | both modes at the F26 gate: the stops are a subset of the CBD and the mode is still chosen |
| Ferry: the market beyond the walk radius and a plan the memory drops | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the F26 gate (§9.140) |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals on F21 |
| Bike, bus and walk residues — the car-less quarter | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | F26 shares by car availability, now that a car-less escorter no longer drives (§9.144) |
| Traffic counts far below observation at 30 stations | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F21 counts |
| Leaf subtour mixes repaired at the seed (0 on every day type); the choice set decays in memory | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside log and mode survival on a full F26 arm (§9.140) |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| The 3 Sep assessment: 14 defects closed (§9.141) and its three decisions taken (§9.142) | #131 | [runs-and-economics](positions/runs-and-economics.md) · [network-and-inputs](positions/network-and-inputs.md) | the digest's disk read on the F26 arm (#131) |
| Iteration wall time: a plain iteration 319 s and a milestone 569–715 s on F26's stopwatch; the trips cadence declared, plans and events moved to the gate, the detour routing parallel, the mobsim's threads probed (§9.147) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the first F27 arm's stopwatch: a plain iteration against 319 s, a milestone against 569 s |
| Machine-level stalls and unexplained arm deaths | #66 | [runs-and-economics](positions/runs-and-economics.md) | the scheduler log |
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
