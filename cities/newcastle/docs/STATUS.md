# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 1 September 2026 — the first F22 arm ran to its
iteration-100 gate and was stopped under the loop (§9.136): **bus is the
first mode ever inside its band (+8.0 %)**, heavy rail fell 37,540 → 16,512
boardings and was still falling, and the walk/car seesaw survived the fare.
Seven modes stand past 20 %; the next family follows the user's pick among
the measured causes.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **1 of 12** at the F22 iteration-100 gate — bus (+8.0 %), the first ever inside; car (+15.2 %) and motorbike (+13.3 %) next closest; see the scoreboard | below, §9.136 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22) each stopped at their iteration-100 gate, before the 240 cutoff; `RUN.controler.last_iteration` still declares 1000 | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.136 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260831T165127_300it_25pct` at **iteration 100** (family `F22-pt-fares-priced`, status `aborted`, 25% sample, launched 2026-08-31T16:51:27, trips table). **Not a result** - a run without `_run.json` is a reading, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260831T165127_300it_25pct --it 100` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 67.1877 | 58.3222 | +15.2% | over 10% | share of resident linked trips |
| 2 | ride | 12.0993 | 20.6000 | -41.3% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 8.4995 | 13.4000 | -36.6% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 1.6943 | 0.9916 | +70.9% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.3049 | 2.2084 | +185.5% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4287 | 0.3785 | +13.3% | over 10% | share of resident linked trips |
| 7 | bus | 2.5726 | 2.3819 | +8.0% | ok | share of resident linked trips |
| 8 | heavy_rail | 16,512 | 6,529 | +152.9% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 860 | 2,954 | -70.9% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0285 | 0.1429 | -80.0% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6074 | 15.4698 | -63.8% | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | +0.0% | representation | train movements represented by crossing closures |

Inside 10%: **bus**. Past the 20% stop bar: **ride, walk, taxi, bike, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | the gate loop has fired twice: F21 stopped with 8 modes out and none inside (§9.134); F22, on the fare-priced model, with 7 out and bus inside (§9.136) |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F22-pt-fares-priced` (opened `20260831T164923`, §9.135) - nothing run before it compares with anything after it |
| Input registry | **452 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **509 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (1 September 2026) · [monitoring-and-gates](positions/monitoring-and-gates.md) (1 September 2026) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (1 September 2026) · [network-and-inputs](positions/network-and-inputs.md) (30 August 2026) · [population-and-demand](positions/population-and-demand.md) (30 August 2026) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (1 September 2026) · [ride-and-pairing](positions/ride-and-pairing.md) (1 September 2026) · [runs-and-economics](positions/runs-and-economics.md) (1 September 2026) · [sampling-and-families](positions/sampling-and-families.md) (1 September 2026) · [seed-and-choice-set](positions/seed-and-choice-set.md) (31 August 2026) · [signals-and-crossings](positions/signals-and-crossings.md) (30 August 2026) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (31 August 2026) · [walk-and-bike](positions/walk-and-bike.md) (1 September 2026) |
<!-- generated:state end -->

**The package on disk is consistent** (§9.133, §9.135): the 30 run-input sets
carry the `ptFare` module and `tests/check_package.py` reports ALL CHECKS
PASSED (re-run 31 Aug, after the fare change; nothing in the package changed
since). The F22 arm sampled at 25 % under the §9.129 bucket rule (§9.136).

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260901T113040_2it_1pct` | completed | F22-pt-fares-priced | 2 | has `_run.json` |
| `aborted_20260831T165127_300it_25pct` | aborted | F22-pt-fares-priced | 101 | Stopped by the session at the iteration-100 gate under the GOAL.md loop: 7 modes at or past 20% deviation (bike +185.5%, heavy_rail +152.... |
| `20260831T145828_2it_1pct` | completed | F21-licence-rate-demand | 2 | has `_run.json` |
| `aborted_20260830T222642_300it_10pct` | aborted | F21-licence-rate-demand | 102 | Stopped by the session at the iteration-100 gate under the GOAL.md loop: 8 modes at or past 20% deviation (heavy_rail +161.8%, bike +157.... |
| `20260830T213149_2it_1pct` | completed | F20-bucket-rule-carve-pool | 2 | has `_run.json` |
| `aborted_20260830T184955_300it_10pct` | aborted | F20-bucket-rule-carve-pool | 12 | Stopped by the session at iteration 11 at the users direction at handoff (a clean, idle machine): the F21 demand - licence rates measured... |

123 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **The user picks the next family's cause from the measured set** (§9.136):
   the walk/car cost channel (car access/egress or derived parking time,
   [positions/walk-and-bike](positions/walk-and-bike.md)); the carve's per-LGA
   conservation fix (#93); the corridor attraction repair — floorspace-weighted
   attraction or an agglomeration term (#30); the ride binder's reach (#86).
   The chosen fix opens its family at the next arm's launch, under a fresh
   stated-cost approval at the measured pace (§9.136).
2. **Rail's residual under fares is the F22 gate's open reading** (#98): rail
   was still falling when stopped; where it settles, and the per-station split
   under fares, are the next arm's measurements.
3. **The #96 leaf trace needs a `SubtourChainScan` extension** (mark leaf vs
   spanning in examples) and a `.tools/classes` recompile — the machine is
   idle now; small, no run needed.

**Decisions required:** the next family's cause, from §9.136's measured set
(above); the next arm's stated-cost approval at the measured 25 % pace
(~45–50 h per 300, §9.136) or the 10 % pace (~18–21 h, §9.134); enable the
Task Scheduler operational log so a machine-level death can name its trigger
(#66, again unattributed after the 1 Sep crash); whether bus moves to a
boardings basis once a regional count is acquired (#99); whether the S2 base
grants the tram signal priority ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The next family's root cause, after the F21 gate stop | #48 #86 #91 #49 #30 #93 #94 #82 | all | the next arm's iteration-100 gate |
| Ride: the demand binds ~11 % of trips against 20.6 % observed | #86 #91 | [ride-and-pairing](positions/ride-and-pairing.md) | what the F21 arm realises of the 57,758 shared bindings (§9.133) |
| Heavy rail +131 % on the entries basis; every ride was free until §9.135 | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the F22 arm's iteration-100 gate under fares |
| The HTS PT level and the operator counts differ by a factor the targets cannot see | #99 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | a regional bus count |
| Light rail out of reach: the corridor holds two-thirds of the observed attraction | #30 #84 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the destination solver against the D1 layers |
| Ferry at a quarter of its derived target after the beeline repair | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | crossings routed with a ferry leg on F21 |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals on F21 |
| Bike, bus and walk residues — the car-less quarter and the licence fix | #49 #50 #30 | [walk-and-bike](positions/walk-and-bike.md) | F21 shares by car availability |
| Traffic counts far below observation at 30 stations | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F21 counts |
| Mixed chain/non-chain subtours in the demand (341 on the F21 plans, 3 leaf) | #96 #30 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the three leaf subtours traced to their placement |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| Assumed values still replaceable by held data | #63 #62 | [network-and-inputs](positions/network-and-inputs.md) | the TableBuilder extract |
| Machine-level stalls and unexplained arm deaths | #66 | [runs-and-economics](positions/runs-and-economics.md) | the scheduler log |
| Convergence horizon: 250 asked, 1000 declared | — | [seed-and-choice-set](positions/seed-and-choice-set.md) | the first arm past the 240 cutoff |

## Do not re-raise

- The 143 holdout targets stay closed until the end, and no target is deleted after the fact (§12).
- The record is never rewritten; superseded text is bannered and pointed past (§9.79).
- SCATS is implemented, not assumed (§9.88); the operated plans and the offset library are what remains unobtained.
- No multi-hour run without a stated-cost approval, and approvals are spent on use.
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
