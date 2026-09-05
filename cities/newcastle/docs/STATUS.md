# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 6 September 2026 — no arm ran. **#142 is fixed and closed, so
nothing blocks a launch** (GOAL.md requirement 10): the escort binder and the
lift pass chose a ride driver on a licence alone, where the joint and shared
passes also require a household vehicle, so 9,319 WEEKDAY bindings named a
driver with no car and the seed then walked, bussed or taxied **85,993 legs the
same person was declared to drive — now 0** (§9.144). The demand was rebuilt on
it and **family F26 is open**. The freed volume is re-let by the occupancy
identity to drivers who can drive, so no ride demand is lost. The scoreboard
below is still F25's iteration-100 reading and may not be differenced against
anything F26 produces. No mode is inside 10 %. No approval stands.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12** at the F25 iteration-100 gate — motorbike left the band (−5.7 % at F24 → −12.3 %); car +11.4 % and motorbike are the closest, walk −19.0 %. Only bus's F22 +8.0 % and F24's motorbike have ever been inside | below, §9.143, §9.136 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22, F23) each stopped at their iteration-100 gate. `RUN.controler.last_iteration` stays 1000 and was deliberately NOT re-declared to 250: §9.7 measured 250 insufficient. The instrument exists — a 300-iteration arm switches innovation off at 240, so its post-cutoff window straddles 250 — and the first arm to pass its gate measures it | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.142, §9.7 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260905T125612_300it_25pct` at **iteration 100** (family `F25-ride-reaches-plan-memory`, status `aborted`, 25% sample, launched 2026-09-05T12:56:12, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260905T125612_300it_25pct --it 100` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 64.9927 | 58.3222 | +11.4% | over 10% | share of resident linked trips |
| 2 | ride | 11.7249 | 20.6000 | -43.1% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 10.8527 | 13.4000 | -19.0% | over 10% | share of resident linked trips |
| 4 | taxi | 2.4306 | 0.9916 | +145.1% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 4.9169 | 2.2084 | +122.6% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.3319 | 0.3785 | -12.3% | over 10% | share of resident linked trips |
| 7 | bus | 3.2777 | 2.3819 | +37.6% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 22,368 | 6,529 | +242.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,288 | 2,954 | -56.4% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0391 | 0.1429 | -72.6% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6565 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **none**. Past the 20% stop bar: **ride, taxi, bike, bus, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | the gate loop has fired five times: F21 with 8 out (§9.134); F22 with 7 out and bus inside (§9.136); F23 with 7 out (§9.139); F24 with 7 out and motorbike inside; F25 with 7 out and none (§9.143). F24 and F25 are the first arms whose readings are citable from their own records, and F25 the first stopped by the watcher itself. **F26 is built and unlaunched** (§9.144) |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F26-a-driver-owns-a-car` (opened `20260906T013531`, §9.144) - nothing run before it compares with anything after it |
| Input registry | **466 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (4 September 2026 (twenty-seventh session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (5 September 2026 (twenty-eighth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (3 September 2026) · [network-and-inputs](positions/network-and-inputs.md) (4 September 2026 (twenty-seventh session)) · [population-and-demand](positions/population-and-demand.md) (6 September 2026 (twenty-ninth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (4 September 2026 (twenty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (6 September 2026 (twenty-ninth session)) · [runs-and-economics](positions/runs-and-economics.md) (5 September 2026 (twenty-eighth session)) · [sampling-and-families](positions/sampling-and-families.md) (6 September 2026 (twenty-ninth session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (5 September 2026 (twenty-eighth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026 (twenty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (4 September 2026 (twenty-seventh session)) |
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
| `aborted_20260905T125612_300it_25pct` | aborted | F25-ride-reaches-plan-memory | 101 | Stopped automatically by the gate watcher at iteration 100 under the GOAL.md loop (RUN.gate.interval_iterations=100): GATE: 7 mode(s) at ... |
| `20260905T115355_2it_1pct` | completed | F24-balanced-destinations | 2 | ran_to_last_iteration `_run.json` |
| `aborted_20260904T181203_300it_25pct` | aborted | F24-balanced-destinations | 100 | Stopped by the operator during iteration 100, at the approved boundary: the stated-cost approval for this arm was given TO THE ITERATION-... |
| `20260904T164057_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T164039_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T162807_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |

139 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Nothing blocks a launch** (§9.144): #142 is fixed and closed, and every
   other open issue carries `awaiting-run`, so `issue_gate.py` passes. The next
   arm is F26's first and would be the first reading on this demand.
2. **Ride is lost downstream of the choice set — the next lane is pairing and
   selection** (§9.143, #86). F25 settles that the demand is not the cause: the
   seeded ride share rose 31 % and the realised share did not move. The arm's
   own `ride_pairing.csv` puts **21.7 %** of selected ride legs on a pairing
   that never happens, the dominant miss being the TIME window and growing
   (`miss_window` 1 → 5,339 → 7,921 across iterations 0/50/100) while the median
   gap closes 301.8 → 50.0 min. Indicatively ~3 pp of the 8.9 pp gap is
   execution and ~6 pp is ride never being selected, which is scoring.
3. **§9.98's refusal to widen the pairing window has new evidence against it**
   (§9.143). It was refused because residual gaps had a median of 344 min and
   were "different trips"; the median gap is now 50 min. Requirement 2 allows a
   recorded decision to be superseded on evidence — but the cause is MATSim
   having no joint replanning, so widening a window may treat the symptom. A
   decision, and it needs an arm to test.
4. **Convergence is still unmeasured** (requirement 8). F25 was approved for its
   full horizon to measure it, and the gate and the horizon collided at
   iteration 100; the loop won, by the user's decision. It waits for an arm with
   a chance of being inside the bars.

**Decisions required:** the root-cause pick between pairing execution and
selection; whether §9.98's window refusal is superseded; whether a
fifth binder pass is needed now the reachable binding volume is ~18.7 % rather
than 20.13 %; a stated-cost approval for any next arm (~26–27 h at 25 % × 300,
measured); enable the Task Scheduler operational log (#66); whether the S2 base
grants the tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).
## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The first F26 arm's gate, every issue awaiting it | #48 #86 #49 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
| Ride: the demand cause is falsified (§9.143) and every declared driver now owns a car (§9.144); the loss is pairing execution and selection | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | the F26 gate's `ride_pairing.csv`: pair rate and `miss_window` against F25's 0.7827 and 7,921 |
| Heavy rail +193 % at the F23 gate; income scaling blunts the fare (§9.139) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | where rail settles once the corridor's CBD end (#30) is repaired |
| Light rail and heavy rail: the corridor's arrivals are repaired at the demand (work 1.02x, shopping 0.99x, other 0.99x of attraction, §9.142) | #30 #84 #98 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | both modes at the F26 gate: the stops are a subset of the CBD and the mode is still chosen |
| Ferry: the market beyond the walk radius and a plan the memory drops | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the F26 gate (§9.140) |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals on F21 |
| Bike, bus and walk residues — the car-less quarter | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | F26 shares by car availability, now that a car-less escorter no longer drives (§9.144) |
| Traffic counts far below observation at 30 stations | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F21 counts |
| Leaf subtour mixes repaired at the seed (0 on every day type); the choice set decays in memory | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside log and mode survival on a full F26 arm (§9.140) |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| The 3 Sep assessment: 14 defects closed (§9.141) and its three decisions taken (§9.142) | #131 | [runs-and-economics](positions/runs-and-economics.md) · [network-and-inputs](positions/network-and-inputs.md) | the digest's disk read on the F26 arm (#131) |
| Iteration wall time: 60% of it is one hoistable `tripRouter.get()`, and 164 GiB per run is one warning (§9.142) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the phase table on the first F26 arm |
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
