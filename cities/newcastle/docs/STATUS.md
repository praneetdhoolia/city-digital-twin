# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 8 September 2026 — **the arm is priced on the iteration it
repeats, and a log guard that had never once counted is counting** (§9.156).
`arm_cost.py` was quoting a median over EVERY iteration a run ran, and on a
probe most of those are iterations an arm pays once: **282.6 s** quoted against
a recurring **216.0 s** (`20260908T014214_4it_25pct`, iterations 2 and 3 at 213
and 219 s; the one-offs are iteration 0 at 326 s, iteration 1 at 282 s and the
final iteration at 350 s). The next 300-iteration arm therefore prices at
**18.2 h bottom / 21.8 h top** with the iteration-100 gate at **6.1 h**, against
**31.5 h** quoted at HEAD before the probe. `NetworkDirectWalkPtRouter` counted
in instance fields under an UNSCOPED Guice provider, so its "log the first 3"
sample wrote **19,469** lines on the F28 arm — about 36 % of its log — while its
progress line had fired **0** times in the project's history; run-lifetime
atomics give **3** lines and the first firing ever. **40** manifest rows moved
CC-BY → ODbL on **357,893** OSM route link references and `link_id`-keyed
parking tables (ODbL rows **161 → 201**); the other **129** were REFUSED and
filed as **#159**. Two assessment recommendations refused after checking: tram
priority IS the S2b intervention, and the build report already churns on the
mapping. Unit tests **139 → 147**. **Family `F31-the-car-router-reads-only-cars`
is open and its first arm is RUNNING** — `20260908T100009_300it_25pct`, 300
iterations at 25 %, under an 18.2–21.8 h stated-cost approval. The scoreboard
below is unchanged and is still F30's stopped arm at iteration 20.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **1 of 12** at the F28 iteration-100 gate — **car +6.6 %**, the first time car has been inside at a gate; walk −11.9 % and motorbike +16.1 % next. Before it only bus's F22 +8.0 % and F24's motorbike had been inside | below, §9.149, §9.136 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22, F23) each stopped at their iteration-100 gate. `RUN.controler.last_iteration` stays 1000 and was deliberately NOT re-declared to 250: §9.7 measured 250 insufficient. The instrument exists — a 300-iteration arm switches innovation off at 240, so its post-cutoff window straddles 250 — and the first arm to pass its gate measures it | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.142, §9.7 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `20260908T100009_300it_25pct` at **iteration 0** (family `F31-the-car-router-reads-only-cars`, status `running`, 25% sample, launched 2026-09-08T10:00:09, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260908T100009_300it_25pct --it 0` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 43.5320 | 58.3222 | -25.4% | **STOP** >=20% | share of resident linked trips |
| 2 | ride | 4.6609 | 20.6000 | -77.4% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 34.5165 | 13.4000 | +157.6% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 1.8764 | 0.9916 | +89.2% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.4754 | 2.2084 | +193.2% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4674 | 0.3785 | +23.5% | **STOP** >=20% | share of resident linked trips |
| 7 | bus | 6.5429 | 2.3819 | +174.7% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 37,792 | 6,529 | +478.9% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 2,720 | 2,954 | -7.9% | ok | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0338 | 0.1429 | -76.4% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 9.0841 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **light_rail**. Past the 20% stop bar: **car, ride, walk, taxi, bike, motorbike, bus, heavy_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | six gate firings, F21-F26, 7-8 modes out each (§9.134, §9.136, §9.139, §9.143, §9.146); F27's arm citable for nothing (§9.148); **F28 with 7 out and car inside** (§9.149); F30's only arm stopped at 23 on cost (§9.153). **F31 opened at the arm 8 Sep and is RUNNING** — the first run carrying `RUN.travel_time.filter_modes` = true (§9.156, #154) |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F31-the-car-router-reads-only-cars` (opened `20260908T095937`, §9.154, 9.156) - nothing run before it compares with anything after it |
| Input registry | **482 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (8 September 2026 (thirty-fifth session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (8 September 2026 (thirty-fifth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (7 September 2026 (thirtieth session)) · [network-and-inputs](positions/network-and-inputs.md) (8 September 2026 (thirty-fifth session)) · [population-and-demand](positions/population-and-demand.md) (7 September 2026 (thirty-second session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (4 September 2026 (twenty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (8 September 2026 (thirty-fifth session)) · [runs-and-economics](positions/runs-and-economics.md) (8 September 2026 (thirty-fifth session)) · [sampling-and-families](positions/sampling-and-families.md) (8 September 2026 (thirty-fifth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (5 September 2026 (twenty-eighth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026 (twenty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (4 September 2026 (twenty-seventh session)) |
<!-- generated:state end -->

**Family F31 is open and its first arm is RUNNING** (§9.156).
`20260908T100009_300it_25pct` launched 8 Sep at 10:00, S2 × WEEKDAY, 25 %, 300
iterations, innovation off at 240, under a stated-cost approval of **18.2–21.8 h**
priced from `20260908T014214_4it_25pct`'s recurring iteration — with the
watcher's iteration-100 gate at **6.1 h**, which is where it will stop while any
mode is past 20 %. The boundary is `RUN.travel_time.filter_modes` = true plus a
recompiled controler. **#159 was filed and the launcher overridden with
`--allow-open-issues`** on the operator's decision — the first deliberate
override of GOAL requirement 10. `check_package.py` last passed on 7 Sep; the
manifest holds 512 files, 40 of whose licences moved this session.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260908T100009_300it_25pct` | running | F31-the-car-router-reads-only-cars | 1 | - |
| `20260908T014214_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260908T012355_4it_25pct` | aborted | F30-an-escort-is-priced-as-an-escort | 0 | Stopped by the agent, and the run is citable for NOTHING - not even its clock, which is the only thing it existed to measure. It was the ... |
| `20260907T233540_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260907T215740_4it_25pct` | aborted | F30-an-escort-is-priced-as-an-escort | 3 | Stopped by the operator: the session was reset to the merged PR #156. The probe was measuring an uncommitted PT-router bound and event_ha... |
| `20260907T192715_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |

162 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Read the F31 arm at iteration 100 — that reading is the lane.**
   `20260908T100009_300it_25pct` is running; the watcher stops it at 100 while
   any mode is past 20 %, so ~6.1 h is the likely spend of an 18.2–21.8 h
   approval. Read with `python src/analyse/report_mode_ridership.py --run
   20260908T100009_300it_25pct --it 100`.
2. **What the arm answers, in order** (§9.149, §9.156): placement — declared
   bound trips ridden against **0.560** and the walked-bound median against
   **1.08 km**; **ride against −42.8 % read TOGETHER with bike (+157.3 %), taxi
   (+161.1 %) and bus (+65.0 %)**, because ride's **−8.822 pp** deficit is the
   whole of their **10.521 pp** excess and a full pro-rata recovery would put car
   at +1.1 %, motorbike at +2.6 % and bus at +10.5 % (§9.156); car must STAY
   inside (+6.6 %). **Expect movement everywhere from #154** — every mode's
   router had been reading link travel times a pedestrian helped set. Read the
   counts on the §9.150 basis, not #82's −91.8 %.
3. **Confirm the router statistic the log can finally report** (§9.156). On its
   first firing the progress line said roughly **40 %** of pt routing requests
   find no transit route at all and roughly **43 %** of the rest take the network
   walk. It came from a pricing probe and is not a reading of any mode; it bears
   on walk's 5.26 km modelled mean against an observed 0.70 km and on the three
   failing pt modes. **Confirm at the gate before acting.**
4. **The assessments' demand findings are root causes, not constants**
   ([docs/reports/README.md](../../../docs/reports/README.md)): evening
   departures, the inverted PT day, age-flat income, inter-LGA commute flows.
   They bear on modes the gate keeps failing and are worth issues before an arm
   is spent measuring around them.
5. **Convergence is still unmeasured** (requirement 8): no arm has passed 100
   since F4, across 160 runs and 29 days. F31 is the first arm since F25 with a
   horizon rather than a gate, so it is the first that CAN measure it — but only
   if every mode clears the 20 % bar at 100.

**Decisions required:** whether the crowding disutility against heavy rail's
+295 % (designed, not built, §9.156) is built before the next arm; whether the
31 unreviewed MATSim defaults (#155) are worked down; **whether the real
Newcastle corridor operates transit signal priority** — `A.lightrail.tsp_enabled`
is `source: assumed` and requirement 6 says derive it, and it must be settled on
evidence about the corridor rather than on light rail's −30 %
([positions/light-rail-and-ferry](positions/light-rail-and-ferry.md), §9.156);
the Task Scheduler log (#66); output-level lineage (#159).
Taken this session (§9.156): the arm priced on the iteration it repeats rather
than on a median that includes the ones it does not; a log guard fixed at the
binding rather than at the symptom; forty licence crossings closed on
demonstrated content and 129 refused rather than guessed; two ranked
recommendations refused after checking; and requirement 10 overridden once,
deliberately and on the record.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The first arm of the family the next launch opens, every issue awaiting it | #48 #86 #49 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
| Ride: pairing solved at the F28 gate (0.9965, 0 undeclared ride legs) and 56.0 % of bound trips ridden; the walked lifts are the shared pass's 2.5-km trips against an observed 9.5-km passenger trip — it now binds the longest tours first (§9.149) | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | the F29 gate: bound trips ridden against 0.560, the walked-bound median against 1.08 km, ride with bike, bus and taxi |
| A household drives more cars than it owns: 12,317 car legs at the F26 gate with every household car out; the roster is built and enforced car-only after a global `wait` stranded the non-chain modes (§9.146, §9.148) | #145 | [population-and-demand](positions/population-and-demand.md) | the F28 arm's iteration 0: car departures and stuck against F26's 232,394 / 2,699; then the gate: that count (0 expected for one-car households), `householdCar: N waited`, where the self-driven bound trips settle |
| Heavy rail +193 % at the F23 gate; income scaling blunts the fare (§9.139) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | where rail settles once the corridor's CBD end (#30) is repaired |
| Light rail and heavy rail: the corridor's arrivals are repaired at the demand (work 1.02x, shopping 0.99x, other 0.99x of attraction, §9.142) | #30 #84 #98 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | both modes at the F29 arm's gate: the stops are a subset of the CBD and the mode is still chosen |
| Ferry: the market beyond the walk radius and a plan the memory drops | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the F29 arm's gate (§9.140) |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals at the F29 arm's gate |
| Bike, bus and walk residues — the car-less quarter | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | F29 shares by car availability, now that a car-less escorter no longer drives (§9.144) |
| Traffic counts far below observation at 30 stations | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) | counts at the F29 arm's gate |
| Leaf subtour mixes repaired at the seed (0 on every day type); the choice set decays in memory | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside log and mode survival on a full F29 arm (§9.140) |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| The 3 Sep assessment: 14 defects closed (§9.141) and its three decisions taken (§9.142) | #131 | [runs-and-economics](positions/runs-and-economics.md) · [network-and-inputs](positions/network-and-inputs.md) | the digest's disk read on the F29 arm (#131) |
| Iteration wall time: closed as a lane (§9.155). The measured UNPROFILED plain iteration is **216.0 s** and the arm prices at 18.2–21.8 h (§9.156) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the F31 arm's own stopwatch, against 216.0 s |
| The 7 Sep assessment: 29 of 34 defects closed without a run (§9.150); the holdout stops informing the count targets and both sides of the count comparison share one basis | #82 #131 | [network-and-inputs](positions/network-and-inputs.md) · [monitoring-and-gates](positions/monitoring-and-gates.md) | counts at the F29 arm's gate, on the corrected basis |
| The manifest credits a producing script's inputs to every output it writes, so 129 rows claim an OSM ancestor they may not have; 40 rows whose OSM content is demonstrable are fixed (§9.156) | #159 | [network-and-inputs](positions/network-and-inputs.md) | output-level lineage, then the share-alike check recommendation 11 asked for |
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
