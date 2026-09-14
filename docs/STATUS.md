# STATUS — the board

*One page: how far the twin is from [the goal](GOAL.md), what runs, and what is
next. The blocks between `generated` markers are written by
`python src/analyse/build_status_board.py` from the artefacts; the hand-written
rest is capped by `tests/check_doc_shape.py`. The current truth per topic is in
[`positions/`](positions); the history and every rationale in
[`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 14 September 2026 (forty-seventh session) — the documents
moved to `docs/`, the run viewer rebuilt, the ninth report's no-run findings
worked, the tenth report lodged (§9.170). The newest reading is arm 0 of F35,
`20260912T202242_300it_25pct`, the project's second RESULT: 300 of 300 in
30.35 h, **2 of 12 inside 10 %** (car +9.6 %, motorbike −5.6 %), six past the
stop bar, ride's target above its own 19.11 % coverage (§9.169). No arm was
launched and no approval stands.

## The goal

Twelve modes, each physically simulated, monitored and scored against its
real-life target; every mode inside 10 %; convergence in at most 250
iterations; nothing assumed that can be derived ([`GOAL.md`](GOAL.md)).

| Requirement | Where it stands | Evidence |
|---|---|---|
| Twelve modes physically simulated | **Built and measured at 25 %.** Every mode represented; pt access, egress and transfer walks are network legs the qsim executed (27,765 on arm 0, 0 teleported); freight trains remain crossing closures, not mobsim vehicles (§9.70) | [walk-and-bike](positions/walk-and-bike.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md), §9.169 |
| Monitored live, every mode individually | **Met** — every 10th iteration readable, all twelve on their own basis; the run viewer shows them against their targets | [monitoring-and-gates](positions/monitoring-and-gates.md), §9.120, §9.170 |
| Every mode inside 10 % | **2 of 12** at the second result (§9.169). Six past the 20 % bar, and ride's 20.60 % target exceeds its 19.11 % choice-set coverage, fixed at the seed — out of reach of any constant | the scoreboard below, §9.169, §9.163 |
| Convergence in ≤ 250 iterations | **Measured twice, met in the weak sense, horizon declared 250** (§9.169): arm 0 drifts 0.128 pp over it.250–300 against a 0.5 pp tolerance, with a +1.683 pp cutoff snap on car; `RUN.controler.last_iteration` is 250 (cutoff 200). Whether 200 iterations of search suffice is unmeasured (§9.43) | [seed-and-choice-set](positions/seed-and-choice-set.md), §9.169 |
| Unobtained data derived, not assumed | SCATS as its published algorithm (§9.88); rail and tram on disclosed boardings (§9.130); licence rates from the published count (§9.131); fares from the Opal schedule (§9.135); still swept: transfer penalty, charging dwell, SCATS offsets | [network-and-inputs](positions/network-and-inputs.md) |

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
| P1 data | ✅ | every raw download hashed with provenance; the unobtained inputs derived or swept with the reason stated ([network-and-inputs](positions/network-and-inputs.md)) |
| P2 network | ✅ | rebuilt 12 Sep with the footway harvest as walk/bike links (368,230 links); 15 feeds mapped once, 0 unmapped stops; one build per comparison (§3.5, §9.167) |
| P3 demand | ✅ | population on measured licence rates (§9.131); chains and plans of 10 Sep (§9.164); the 30 run-input sets on the 250-iteration horizon (§9.169); `check_package.py` passed |
| P4 calibration | 🟡 | the newest run on disk is `20260912T202242_300it_25pct`, which **RAN TO ITS LAST ITERATION**: arm 0 of F35 (`f35_baseline_25pct`, 300 it, 25 %, no control on), the second result and F35's reading (§9.169). It is the control half of the five pairs (#172); no pair is approved |
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

F35 is open with arm 0 as its reading; nothing before `20260912T184108`
compares with it. The network is F34's footpath rebuild, the demand and plans
those of `20260910T203622` (§9.164). The manifest holds
**721 CC-BY / 220 ODbL** plus 18 bespoke files, every one hashed. The heap rule reads 37.4 GiB at
25 % against a measured live peak of 26.2 GiB on arm 0 (§9.169).

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

1. **The first pair arm, on its own approval** (#172, §9.169): one field
   against arm 0, 250 iterations at 25 % (~25.5 h quoted on arm 0's clock,
   band 21.7–46.9 h), coverage read on both sides (#174), the overlay
   declaring `answers_issues`. The decided sequence is scoring → choice set →
   service quality → routers → submodes; on arm 0's evidence the routers pair
   (`C.raptor.mode_cost_representation` = `mode_constant`) answers three of the
   six STOP modes and is recommended first.
2. **Or the roots first** (§9.169): ride is seeded below its target's coverage
   (#86), walk trips are five times too long at the demand's destination
   placement (#30), bike carries no distance cost (#107). Each is a demand
   rebuild that opens a family and re-baselines.
3. **The eleventh report runs after the next reading**, not before (§9.166).
4. **The ASC contraction test** stays held; bike is the mode it can answer.

**Decisions required:** which pair or root is next and its stated-cost
approval; whether to send the drafted TfNSW bespoke-table request (#50).

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| **Choice-set coverage is an arithmetic ceiling.** On arm 0: car 75.86 %, walk 63.54 %, taxi 53.72 %, bike 27.12 %, pt 17.53 %, ride 19.11 % — ride's 20.60 % target is above its coverage, fixed at the seed from it.27 (§9.169) | #86 #174 | [seed-and-choice-set](positions/seed-and-choice-set.md) | coverage on both arms of the first pair |
| **Five one-field controls, each opening a family; the order is the decision** (§9.164, §9.169): scoring, choice set, routers, service quality (#175), pt submodes (#49). Arm 0 is the control half of all five | #172 #174 #49 | [seed-and-choice-set](positions/seed-and-choice-set.md) | which is spent first, at 250 iterations |
| **The reading point is a convergence problem**; the windowed remedy measured worse (§9.159). The objective's denominator `CAL.objective.replication_band_pp` is 0.0 until a band is measured (§9.164) | #163 | [monitoring-and-gates](positions/monitoring-and-gates.md) | three seeds at a short horizon, then the band |
| **Ride −41.6 %**: the demand seeds ride below the target (`B.mode.bound_passenger_placement` = `every_plan`, seeded share 0.1114), and a household drives more cars than it owns (wait count 18,767 on arm 0, §9.169) | #86 #145 | [ride-and-pairing](positions/ride-and-pairing.md), [population-and-demand](positions/population-and-demand.md) | a demand that seeds ride at the HTS share |
| **Light rail −73.9 % and heavy rail +54.6 %** are one split decided by a router that reads no mode constant; `C.raptor.mode_cost_representation` = `mode_constant` is built and unrun. Crowding has never had a control (`C.crowding.representation` `in_vehicle_time` on every arm, §9.158) | #98 #49 | [light-rail-and-ferry](positions/light-rail-and-ferry.md), [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the routers pair, coverage on both sides |
| **Ferry −63.3 %** with its market present (3.60 % of trip ends within 1 km of a wharf against 5.18 % of observed POI weight, §9.163); weekday tap-ons 234–1,347 at the Newcastle wharf are bounds, never targets (#185) | #94 | [light-rail-and-ferry](positions/light-rail-and-ferry.md) | the near-wharf split on the routers pair |
| **Taxi +131.4 %** with 51 pp of headroom; the fleet's refusals fell to one in five (2,065 an iteration) and are no longer the mechanism (§9.169) | #49 | [taxi-and-rideshare](positions/taxi-and-rideshare.md) | the cause of the excess, on the first pair |
| **Bike +201.6 %** at 8.10 km against 5.2, no distance or traffic cost in its score; both feasibility bounds ship at 0.0 (§9.163). The ASC contraction test (~15 h, no family) is decisive for bike alone: 20.46 pp of headroom | #107 #30 | [walk-and-bike](positions/walk-and-bike.md) | bike by car availability on the first pair |
| **Walk −12.2 %** on the footpath network, off the stop bar, at a 3.74 km mean against 0.70 observed; the sub-1 km share (11.13 %) is set by the gravity kernel at build time and the HTS publishes a mean, not a distribution | #30 | [walk-and-bike](positions/walk-and-bike.md) | the sub-1 km share on the next demand rebuild |
| **Headway and reliability reach MATSim** behind a gate shipped `absent` (`citysim.ServiceQualityScoring`, §9.164) | #175 | [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) | the paired arm at `headway` and `headway_and_reliability` |
| **The TfNSW bespoke-table request** (mode × age, trip length by mode, occupancy by purpose, the unfolded "Other") is drafted and held; the modelled mode × demographics table exists (§9.163) | #50 | [population-and-demand](positions/population-and-demand.md) | the lodgement, then TfNSW's answer |
| Stalls and heap: arm 0 ran 30.35 h under 48 g with no stall, live heap peaking at 26.2 GiB (§9.169); the launcher refuses a concurrent arm | #66 | [runs-and-economics](positions/runs-and-economics.md) | a second full arm's `gc.log` at 25 % |
| Surrogate calibration held in reserve: ~150 evaluations at 21.5 h each is ~134 days at 25 % | — | [runs-and-economics](positions/runs-and-economics.md) | only if the residual proves multi-parameter |
| Code findings of the ninth report still open: dict-valued registry leaves unchecked (#200), the ride engine's worker-thread plan writes (#197) | #197 #200 | [network-and-inputs](positions/network-and-inputs.md) | a 1 % probe band after the Java change |

## Do not re-raise

- The 143 holdout targets stay closed until the end; no target is deleted after the fact (§12).
- The record is never rewritten; superseded text is bannered and pointed past (§9.79).
- SCATS is implemented, not assumed (§9.88); the operated plans and the offset library are what remains unobtained.
- No multi-hour run without a stated-cost approval, spent on use; no launch while an open issue lacks `awaiting-run` (GOAL.md requirement 10).
- One arm at a time; never recompile `.tools/classes` while one runs (#66).
- The taxi fare is not a lever (§9.91); freight trains are not mobsim vehicles (§9.70); SCATS offsets are not adapted (§9.88).

## How to resume

Run `/onboard`. By hand: `python src/run/session_gate.py --digest`, then
[`GOAL.md`](GOAL.md), this board, the brief
([`NEXT_AGENT_BRIEF.md`](NEXT_AGENT_BRIEF.md)) and the position page for the
lane. `python src/run/session_gate.py` runs every gate.
