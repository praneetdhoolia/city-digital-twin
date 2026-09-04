# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 4 September 2026 — the three decisions that held the
launcher are taken (#129, #133, #134) and the corridor's missing CBD end is
repaired at its cause (§9.142): destination choice is now constrained at the
destination end as well as the origin, so a zone receives the arrivals its own
attraction states. C2 is re-measured on the network that runs and the demand
rebuilt on it. The iteration's own cost is profiled for the first time: 60 % of
it is one hoistable line. No arm has run and no approval stands.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12** at the F23 iteration-100 gate (car +14.8 %, motorbike +13.9 %, bus +16.2 % closest); bus's F22 +8.0 % stays the only mode ever inside | below, §9.139, §9.136 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22, F23) each stopped at their iteration-100 gate. `RUN.controler.last_iteration` stays 1000 and was deliberately NOT re-declared to 250: §9.7 measured 250 insufficient. The instrument exists — a 300-iteration arm switches innovation off at 240, so its post-cutoff window straddles 250 — and the first arm to pass its gate measures it | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.142, §9.7 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260901T165115_300it_25pct` at **iteration 100** (family `F23-behaviour-channels`, status `aborted`, 25% sample, launched 2026-09-01T16:51:15, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260901T165115_300it_25pct --it 100` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 66.9432 | 58.3222 | +14.8% | over 10% | share of resident linked trips |
| 2 | ride | 12.3367 | 20.6000 | -40.1% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 9.7602 | 13.4000 | -27.2% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 1.7514 | 0.9916 | +76.6% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 4.6638 | 2.2084 | +111.2% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4313 | 0.3785 | +13.9% | over 10% | share of resident linked trips |
| 7 | bus | 2.7686 | 2.3819 | +16.2% | over 10% | share of resident linked trips |
| 8 | heavy_rail | 19,140 | 6,529 | +193.2% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 1,000 | 2,954 | -66.1% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0286 | 0.1429 | -80.0% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6357 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **none**. Past the 20% stop bar: **ride, walk, taxi, bike, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | the gate loop has fired three times: F21 with 8 out (§9.134); F22 with 7 out and bus inside (§9.136); F23 with 7 out and none inside (§9.139). The F24 package is built and its three blocking decisions are taken (§9.142); the arm waits only on a stated-cost approval |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F23-behaviour-channels` (opened `20260901T133356`, §9.138) - nothing run before it compares with anything after it |
| Input registry | **464 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (4 September 2026 (twenty-seventh session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (4 September 2026 (twenty-seventh session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (3 September 2026) · [network-and-inputs](positions/network-and-inputs.md) (4 September 2026 (twenty-seventh session)) · [population-and-demand](positions/population-and-demand.md) (4 September 2026 (twenty-seventh session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (4 September 2026 (twenty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (4 September 2026 (twenty-seventh session)) · [runs-and-economics](positions/runs-and-economics.md) (4 September 2026 (twenty-seventh session)) · [sampling-and-families](positions/sampling-and-families.md) (4 September 2026 (twenty-seventh session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (4 September 2026 (twenty-seventh session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026 (twenty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (4 September 2026 (twenty-seventh session)) |
<!-- generated:state end -->

**The package on disk is consistent and is the F24 build** (§9.142): chains,
plans and the 30 run-input sets rebuilt 4 Sep on destination choice constrained
at both ends and on circuity re-measured on the current network (detour 1.3276
over 595 routed pairs, walk 1.6938, bike 1.5570). Family F24 is declared at its
first launch. No arm runs. The three decisions that held
`python src/run/issue_gate.py` are taken (#129, #133, #134), so the launcher's
requirement-10 refusal clears when they close.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260904T164057_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T164039_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T162807_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T162301_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T161721_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |
| `20260904T161108_2it_1pct` | completed | F23-behaviour-channels | 2 | ran_to_last_iteration `_run.json` |

136 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **The first F24 arm, under a fresh stated-cost approval** (~24 h at
   25% × 300 on the repaired iteration, projected from a 9.6x fall in the detour
   pass; the F23 arm measured 45–50 h, §9.136, §9.142). It is the first arm to read a balanced corridor, and it reads
   all twelve modes at its gate plus what the `awaiting-run` issues name (#93,
   #96, #94, #98, #108, #107, #82, #131). Two readings are repairs working, not
   regressions: taxi should read HIGHER than F23's +76.6 % because a refused trip
   now keeps taxi (#113), and light rail and heavy rail move on the corridor
   (#30, #98).
2. **A run of this model is not reproducible bit for bit** (§9.142): three runs
   of one unmodified build, same package and seed, gave 5,620,710 / 5,620,410 /
   5,620,710 iteration-0 events. MATSim's own RNG counter is unsynchronised under
   20 threads. Mode shares were identical, so a gate reading is safe, but the
   determinism constraint as written does not hold. **A decision, not run-gated.**
3. **The user picks the next root cause** after the F24 gate: the ride plan
   variant #86 now names (46,345 bound trips that never reach plan memory), the
   income channel's disposition (#108), or the ferry's reach bound (#94).

**Decisions required:** a stated-cost approval for the first F24 arm (~24 h
projected); whether to make a run reproducible, given that three runs of one
build disagree (§9.142); the root-cause pick after its gate; enable the Task Scheduler operational log
(#66); whether the S2 base grants the tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).
The three that held the launcher are taken (§9.142).

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The F24 arm's gate, every issue awaiting it | #48 #86 #49 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
| Ride: the binders reach 20.13% of core trips but 46,345 bound trips never become a ride alternative in plan memory (§9.142) | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | the F24 gate, then the per-trip plan variant behind `GatedSubtourProbe` |
| Heavy rail +193 % at the F23 gate; income scaling blunts the fare (§9.139) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | where rail settles once the corridor's CBD end (#30) is repaired |
| Light rail and heavy rail: the corridor's arrivals are repaired at the demand (work 1.02x, shopping 0.99x, other 0.99x of attraction, §9.142) | #30 #84 #98 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | both modes at the F24 gate: the stops are a subset of the CBD and the mode is still chosen |
| Ferry: the market beyond the walk radius and a plan the memory drops | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the F24 gate (§9.140) |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals on F21 |
| Bike, bus and walk residues — the car-less quarter | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | F24 shares by car availability |
| Traffic counts far below observation at 30 stations | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F21 counts |
| Leaf subtour mixes repaired at the seed (0 on every day type); the choice set decays in memory | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside log and mode survival on a full F24 arm (§9.140) |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| The 3 Sep assessment: 14 defects closed (§9.141) and its three decisions taken (§9.142) | #131 | [runs-and-economics](positions/runs-and-economics.md) · [network-and-inputs](positions/network-and-inputs.md) | the digest's disk read on the F24 arm (#131) |
| Iteration wall time: 60% of it is one hoistable `tripRouter.get()`, and 164 GiB per run is one warning (§9.142) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the phase table on the first F24 arm |
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
