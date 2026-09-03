# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 3 September 2026 — every open issue worked to closed or
`awaiting-run` (GOAL.md requirement 10, §9.140) and the package rebuilt,
opening F24 at its first launch; the first whole-repository assessment
lodged (`docs/reports/20260903T134517_project_report.html`): 14 defects confirmed
at HEAD and filed as #112–#137, none needing a run — the gate watcher
(#112) would record a passing arm as aborted, so it is fixed first.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **12 of 12** — freight rail as timetable-derived crossing closures, not a mobsim vehicle | [positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md), §9.70 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis | [positions/monitoring-and-gates](positions/monitoring-and-gates.md), §9.120 |
| Every mode inside 10 % | **0 of 12** at the F23 iteration-100 gate (car +14.8 %, motorbike +13.9 %, bus +16.2 % closest); bus's F22 +8.0 % stays the only mode ever inside | below, §9.139, §9.136 |
| Convergence in ≤ 250 iterations | **Unmeasured** — the deepest arms (F21, F22) each stopped at their iteration-100 gate, before the 240 cutoff; `RUN.controler.last_iteration` still declares 1000 | [positions/seed-and-choice-set](positions/seed-and-choice-set.md), §9.136 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); pt fares from the published Opal schedule (§9.135); the external interaction rate from the 2011 journey-to-work flow and the S0 detour from the alignment (§9.140); still swept: transfer penalty, charging dwell, SCATS offsets | [positions/network-and-inputs](positions/network-and-inputs.md) |

## Scoreboard

<!-- generated:scoreboard start -->
Read from `aborted_20260901T165115_300it_25pct` at **iteration 100** (family `F23-behaviour-channels`, status `aborted`, 25% sample, launched 2026-09-01T16:51:15, trips table). **Not a result** - a run without `_run.json` is a reading, and every arm since F4 stopped before its gate.
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
| P4 calibration | 🟡 | the gate loop has fired three times: F21 with 8 out (§9.134); F22 with 7 out and bus inside (§9.136); F23, on the behaviour channels, with 7 out and none inside (§9.139); every open issue is awaiting a run and the F24 package waits for its arm (§9.140) |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F23-behaviour-channels` (opened `20260901T133356`, §9.138) - nothing run before it compares with anything after it |
| Input registry | **457 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **511 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (3 September 2026) · [monitoring-and-gates](positions/monitoring-and-gates.md) (3 September 2026) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (3 September 2026) · [network-and-inputs](positions/network-and-inputs.md) (3 September 2026) · [population-and-demand](positions/population-and-demand.md) (3 September 2026) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (3 September 2026) · [ride-and-pairing](positions/ride-and-pairing.md) (3 September 2026) · [runs-and-economics](positions/runs-and-economics.md) (3 September 2026) · [sampling-and-families](positions/sampling-and-families.md) (3 September 2026) · [seed-and-choice-set](positions/seed-and-choice-set.md) (3 September 2026) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026) · [walk-and-bike](positions/walk-and-bike.md) (3 September 2026) |
<!-- generated:state end -->

**The package on disk is consistent and is the F24 build** (§9.140): chains,
plans and the 30 run-input sets rebuilt 3 Sep on the derived external
interaction rate, the LGA-conserved motorbike carve and the leaf-subtour
repair, manifest 511 files; family F24 is declared at its first launch. No arm
runs; every open issue is labelled `awaiting-run` (`python
src/run/issue_gate.py`), and the launcher refuses otherwise.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260901T165115_300it_25pct` | aborted | F23-behaviour-channels | - | Stopped by the session at the iteration-100 gate under the GOAL.md loop: 7 modes at or past 20% deviation (heavy_rail +193.2%, bike +111.... |
| `aborted_20260901T165115_300it_25pct` | aborted | F23-behaviour-channels | 104 | Stopped by the session at the iteration-100 gate under the GOAL.md loop: 7 modes at or past 20% deviation (heavy_rail +193.2%, bike +111.... |
| `aborted_20260901T152548_300it_25pct` | aborted | F23-behaviour-channels | - | Stopped at the user's direction (1 Sep): stop the run - no reading taken, stopped before any gate |
| `aborted_20260901T133404_300it_10pct` | aborted | F23-behaviour-channels | 34 | User directive (1 Sep): 25% runs only - the F23 read moves to a 25% x 300 arm; this 10% arm stopped before its first gate |
| `20260901T132710_2it_1pct` | completed | F22-pt-fares-priced | 2 | has `_run.json` |
| `20260901T113040_2it_1pct` | completed | F22-pt-fares-priced | 2 | has `_run.json` |

128 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Fix the assessment's defects before any arm** (#112–#127; none needs
   a run): #112 first, then the taxi restore (#113), the board's truck
   deviation (#114) and the two data producers that cannot rebuild their
   layer (#115, #116). The launcher refuses while they are open (requirement 10).
2. **The first F24 arm** under a fresh stated-cost approval (~45–50 h at
   25% × 300, §9.136): it reads all twelve modes at its gate and, on top,
   the carve at its identity (#93), the leaf stand-aside log (#96), the
   ferry's near-wharf split and the choice-set survival (#94, §9.140).
3. **The user picks the next root cause** (§9.139, §9.140): the corridor's
   missing CBD end (#30, floorspace-weighted attraction vs an agglomeration
   term); the income channel's disposition (#108); the fifth binder pass
   for the unbindable ride classes or a stated limitation (#86).

**Decisions required:** the root-cause pick, the income-channel
disposition and the #86 binder decision above; enable the Task Scheduler
operational log (#66); whether the S2 base grants the tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The F24 arm's gate, every issue awaiting it | #48 #86 #49 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
| Ride: generated 19.1 / bound 16.0 / realised 12.1 % against 20.6 % observed | #86 | [ride-and-pairing](positions/ride-and-pairing.md) | the fifth binder pass decision, then the F24 gate (§9.136, §9.140) |
| Heavy rail +193 % at the F23 gate; income scaling blunts the fare (§9.139) | #98 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | where rail settles once the corridor's CBD end (#30) is repaired |
| Light rail out of reach: the corridor holds two-thirds of the observed attraction | #30 #84 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the destination solver against the D1 layers |
| Ferry: the market beyond the walk radius and a plan the memory drops | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split at the F24 gate (§9.140) |
| Taxi above target | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | fleet refusals on F21 |
| Bike, bus and walk residues — the car-less quarter | #49 #50 #30 #107 | [walk-and-bike](positions/walk-and-bike.md) | F24 shares by car availability |
| Traffic counts far below observation at 30 stations | #82 | [monitoring-and-gates](positions/monitoring-and-gates.md) | F21 counts |
| Leaf subtour mixes repaired at the seed (0 on every day type); the choice set decays in memory | #96 | [seed-and-choice-set](positions/seed-and-choice-set.md) | the stand-aside log and mode survival on a full F24 arm (§9.140) |
| Mode fidelity by age, sex and employment | #50 | [population-and-demand](positions/population-and-demand.md) | the mode × age acquisition |
| The 3 Sep assessment's 26 findings: 14 defects, 9 risks and gaps, 3 document drifts | #112 #113 #114 #115 #116 #117 #118 #119 #120 #121 #122 #123 #124 #125 #126 #127 #128 #129 #130 #131 #132 #133 #134 #135 #136 #137 | [runs-and-economics](positions/runs-and-economics.md) · [network-and-inputs](positions/network-and-inputs.md) | none — every one is fixable without a run (`docs/reports/20260903T134517_project_report.html`) |
| Machine-level stalls and unexplained arm deaths | #66 | [runs-and-economics](positions/runs-and-economics.md) | the scheduler log |
| Convergence horizon: 250 asked, 1000 declared | — | [seed-and-choice-set](positions/seed-and-choice-set.md) | the first arm past the 240 cutoff |

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
