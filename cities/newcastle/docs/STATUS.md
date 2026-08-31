# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 31 August 2026 — the F21 arm ran to its iteration-100 gate
and was stopped under the GOAL.md loop: 8 modes at or past 20 %. Car crossed
its target for the first time (+16.0 % at 100); family F21 stays open.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12** at the F21 iteration-100 gate — car (+16.0 %) and bus (+15.6 %) closest, both having crossed their targets; see the scoreboard | below, §9.134 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arm (F21) stopped at its iteration-100 gate, before the 240 cutoff; `RUN.controler.last_iteration` still declares 1000 | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.134 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260830T222642_300it_10pct` at **iteration 100** (family `F21-licence-rate-demand`, status `aborted`, 10% sample, launched 2026-08-30T22:26:42, trips table). **Not a result** - a run without `_run.json` is a reading, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run results/aborted_20260830T222642_300it_10pct --it 100` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 67.6729 | 58.3222 | +16.0% | over 10% | share of resident linked trips |
| 2 | ride | 12.0828 | 20.6000 | -41.3% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 8.4961 | 13.4000 | -36.6% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 1.6603 | 0.9916 | +67.4% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 5.6827 | 2.2084 | +157.3% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4715 | 0.3785 | +24.6% | **STOP** >=20% | share of resident linked trips |
| 7 | bus | 2.7527 | 2.3819 | +15.6% | over 10% | share of resident linked trips |
| 8 | heavy_rail | 17,090 | 6,529 | +161.8% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 780 | 2,954 | -73.6% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0265 | 0.1429 | -81.5% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 5.6483 | 15.4698 | -63.5% | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | +0.0% | representation | train movements represented by crossing closures |

Inside 10%: **none**. Past the 20% stop bar: **ride, walk, taxi, bike, motorbike, heavy_rail, light_rail, ferry**.
<!-- generated:scoreboard end -->

## Where the build is

| Phase | State | Evidence |
|---|---|---|
| P0 scoping | ✅ | base year 2026, five LGAs, 1,500 core SA1s (§1) |
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs are derived or swept with the reason stated ([positions/network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 16 Aug on the boundary-derived extent; 15 feeds mapped, 0 unmapped stops; one build per comparison (§3.5, §9.35) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains, plans and the 30 run-input sets rebuilt on it 30 Aug, `check_package.py` ALL CHECKS PASSED (§9.133) |
| P4 calibration | 🟡 | the gate loop of GOAL.md fired for the first time since F4: the F21 arm stopped at its iteration-100 gate, 8 modes out (§9.134) |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F21-licence-rate-demand` (opened `20260830T222641`, §9.131) - nothing run before it compares with anything after it |
| Input registry | **414 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **503 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (31 August 2026) · [monitoring-and-gates](positions/monitoring-and-gates.md) (31 August 2026) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (31 August 2026) · [network-and-inputs](positions/network-and-inputs.md) (30 August 2026) · [population-and-demand](positions/population-and-demand.md) (30 August 2026) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (31 August 2026) · [ride-and-pairing](positions/ride-and-pairing.md) (31 August 2026) · [runs-and-economics](positions/runs-and-economics.md) (31 August 2026) · [sampling-and-families](positions/sampling-and-families.md) (31 August 2026) · [seed-and-choice-set](positions/seed-and-choice-set.md) (31 August 2026) · [signals-and-crossings](positions/signals-and-crossings.md) (30 August 2026) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (31 August 2026) · [walk-and-bike](positions/walk-and-bike.md) (31 August 2026) |
<!-- generated:state end -->

**The package on disk is consistent** (§9.133): chains, plans and run inputs
were rebuilt on the licence-rate population on 30 Aug and
`tests/check_package.py` reports ALL CHECKS PASSED (re-run 30 Aug 22:20). The
F21 arm's sample holds 61,953 persons against the F20 arm's 62,134 (§9.127).

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `aborted_20260830T222642_300it_10pct` | aborted | F21-licence-rate-demand | 102 | Stopped by the session at the iteration-100 gate under the GOAL.md loop: 8 modes at or past 20% deviation (heavy_rail +161.8%, bike +157.... |
| `20260830T213149_2it_1pct` | completed | F20-bucket-rule-carve-pool | 2 | has `_run.json` |
| `aborted_20260830T184955_300it_10pct` | aborted | F20-bucket-rule-carve-pool | 12 | Stopped by the session at iteration 11 at the users direction at handoff (a clean, idle machine): the F21 demand - licence rates measured... |
| `20260830T184637_2it_1pct` | completed | F19-driver-detour | 2 | has `_run.json` |
| `aborted_20260830T170743_300it_10pct` | aborted | F19-driver-detour | 28 | Stopped by the session at iteration 27 for the F20 arm (DECISIONS.md 9.129): its 10% sample, drawn under the 9.127 at-or-below coupling r... |
| `aborted_20260830T170153_300it_10pct` | aborted | F19-driver-detour | 0 | Stopped by the session at iteration 0, six minutes after launch: launched inline (a child of the session) by mistake where every arm is l... |

120 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Fix from the root what the gate stop names** (the loop in GOAL.md):
   ride plateaued at its ~12 % demand ceiling from iteration 30 (#86); light
   rail AWAY at −73.6 % (#30, #84); heavy rail +161.8 % still falling (#98);
   walk overshot to −36.6 % while car overshot to +16.0 % — one movement;
   bike +157.3 % falling slowly (#30); ferry −81.5 % (#94). Needs the user's
   pick of lane; no run approval stands.
2. **Read the stopped arm before changing anything**: per-mode plan scores,
   shares by car availability, boardings by station — the diagnostics the
   position pages name, none needing a run.
3. **The #96 scan is rerun on the rebuilt plans**: 341 mixed subtours, 3 leaf,
   in 110 of 621,364 persons — unchanged in rate by the rebuild (on #96).

**Decisions required:** enable the Task Scheduler operational log so a
console-stop death can name its trigger (#66); the fraction and cost of a
confirmation arm after the 10 % loop (25 % × 300 ≈ 25 h); whether bus moves to
a boardings basis once a regional count is acquired (#99); whether the S2 base
grants the tram signal priority — the emitted config says `green_extension`
while the record's S2 probe ran with it off ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The next family's root cause, after the F21 gate stop | #48 #86 #91 #49 #30 #93 #94 #82 | all | the next arm's iteration-100 gate |
| Ride: the demand binds ~11 % of trips against 20.6 % observed | #86 #91 | [ride-and-pairing](positions/ride-and-pairing.md) | what the F21 arm realises of the 57,758 shared bindings (§9.133) |
| Heavy rail boards five times the disclosed entries at suburban stations | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | F21 boardings at the disclosed stations after the licence fix |
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
