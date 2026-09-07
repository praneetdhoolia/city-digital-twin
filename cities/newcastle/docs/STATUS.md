# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 8 September 2026 — **the 2-minute iteration is priced as
unreachable by any measured lever, and the events knob is bracketed on both
sides** (§9.155). The arithmetic answers the ask before a knob turns: the mobsim
alone is **143 s** of a 205.5 s iteration, so **zeroing every other phase still
lands above 120 s**, and all three measured levers taken at their full CPU share
land near **171 s**. The one untested value of `RUN.machine.event_handler_threads`
was probed — 1 was saturated (§9.56), 12 bought nothing (§9.59), **2 had never
been run** — and it is **44.5 % SLOWER** (205.5 → 297.0 s, mobsim 143 → 226 s).
So the 11.6 % of CPU that §9.154's recording found in `LinkedBlockingQueue.offer`
is **the price of keeping each pipeline stage short enough not to throttle the
16 qsim threads, not waste to be recovered**, and 4 stands on evidence.
The next lever is bounded exactly: `timeVariantNetwork` makes all **143,891**
links time-variant to represent **2,441 change events on 16**. From the fifth
assessment: the **72.8 GiB** permanently-untrimmable leak is closed
(`RUN.storage.extract_grace_s`; 13 directories, 16 % of a 90 %-full cache, all
already mirrored, while the store deleted younger complete runs instead). It
frees nothing today - the store is under its cap - it makes the space
RECLAIMABLE at the next trim that needs it, the
`raw_cap_gb` units corrected to gibibytes, and `check_legacy_drift.py`'s false
"the constant is gone" corrected — `dwell_charging_s=20.0` is live and writes a
manifest artefact. One recommendation was **REFUSED after checking**: `fit.py`'s
patronage scorer is correct and self-declaring, not empty. Three manual
operations are codified: `session_gate.py --fix`, `src/analyse/compare_runs.py`
and `src/run/verify_launch.py`. Registry 480 → 481, unit tests 125 → 139.
**No arm ran to a gate; the scoreboard below is unchanged from F30's stopped arm
at iteration 20.**

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
Read from `aborted_20260907T150816_300it_25pct` at **iteration 20** (family `F30-an-escort-is-priced-as-an-escort`, status `aborted`, 25% sample, launched 2026-09-07T15:08:16, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run aborted_20260907T150816_300it_25pct --it 20` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 50.7348 | 58.3222 | -13.0% | over 10% | share of resident linked trips |
| 2 | ride | 11.2981 | 20.6000 | -45.2% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 22.0726 | 13.4000 | +64.7% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 2.0384 | 0.9916 | +105.6% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.5895 | 2.2084 | +198.4% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4383 | 0.3785 | +15.8% | over 10% | share of resident linked trips |
| 7 | bus | 4.9284 | 2.3819 | +106.9% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 33,756 | 6,529 | +417.1% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 2,068 | 2,954 | -30.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0518 | 0.1429 | -63.7% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 7.3520 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
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
| P4 calibration | 🟡 | the gate loop has fired six times, F21-F26, with 7-8 modes out each (§9.134, §9.136, §9.139, §9.143, §9.146). F27's one arm was stopped at 19 under a global `wait` that stranded the non-chain modes, citable for nothing (§9.148); **F28 with 7 out and car inside** (§9.149). **F29 and F30 are built and unlaunched**: F29 the demand (§9.149), F30 one run-stack line, the escort draw ordered by household id (§9.151). Every gate blocking a launch is now green |
| P5 scenario runs · P6 analysis · P7 write-up | ⬜ | blocked until the twin passes its gate; the 143 holdout targets open once, at the end (§12) |

## State

<!-- generated:state start -->
| | |
|---|---|
| Open comparability family | `F30-an-escort-is-priced-as-an-escort` (opened `20260907T144147`, §9.151) - nothing run before it compares with anything after it |
| Input registry | **482 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (4 September 2026 (twenty-seventh session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (7 September 2026 (thirty-third session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (7 September 2026 (thirtieth session)) · [network-and-inputs](positions/network-and-inputs.md) (7 September 2026 (thirty-third session)) · [population-and-demand](positions/population-and-demand.md) (7 September 2026 (thirty-second session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (4 September 2026 (twenty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (7 September 2026 (thirty-second session)) · [runs-and-economics](positions/runs-and-economics.md) (8 September 2026 (thirty-fourth session)) · [sampling-and-families](positions/sampling-and-families.md) (7 September 2026 (thirty-second session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (5 September 2026 (twenty-eighth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026 (twenty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (4 September 2026 (twenty-seventh session)) |
<!-- generated:state end -->

**Family F30 is open and its first arm is STOPPED** (§9.153).
`aborted_20260907T150816_300it_25pct` ran from 15:08 and was stopped by the
operator at **iteration 23**: `completion` `stopped_by_operator`,
`median_iteration_s` **376.42** against the **260 s** its ~22 h approval was
priced on (§9.149), 9,634 s of wall clock. It was stopped on cost, not on a
fault — iteration 0 passed every control. The boundary is ONE line of the run
stack, the escort listener's draw order, on the F29 demand rebuilt 7 Sep.
`check_package.py` ALL CHECKS PASSED; the manifest holds 512 files. **The 45 %
is not diagnosed** and belongs to #66.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260907T233540_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260907T215740_4it_25pct` | aborted | F30-an-escort-is-priced-as-an-escort | 3 | Stopped by the operator: the session was reset to the merged PR #156. The probe was measuring an uncommitted PT-router bound and event_ha... |
| `20260907T192715_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |
| `20260907T182742_4it_25pct` | completed | F30-an-escort-is-priced-as-an-escort | 4 | ran_to_last_iteration `_run.json` |
| `aborted_20260907T150816_300it_25pct` | aborted | F30-an-escort-is-priced-as-an-escort | 23 | Stopped by the operator at iteration ~24 under the GOAL.md loop, before the iteration-100 gate. The arm was healthy - iteration 0 control... |
| `aborted_20260907T145929_300it_25pct` | failed | F30-an-escort-is-priced-as-an-escort | - | launch refused before MATSim started: A.signals.representation is explicit_signals but the signals run stack is not built. Run: python sr... |

159 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Relaunch F30's arm and read it at 100 — this is still the lane.** Every
   gate is green and the cost is read, not quoted: `python
   src/analyse/arm_cost.py --run-config f29_gate_25pct`, and the launcher prints
   the same line. **It needs a fresh stated-cost approval.** The arm opens a NEW
   family: §9.154 declared `RUN.travel_time.filter_modes` = true, which moves
   results (#154). **Price it on an UNPROFILED probe first** — `arm_cost.py:131`
   excludes every profiled run, and the only runs carrying the §9.154 repair are
   profiled probes, so at HEAD it still prices on F30's pre-repair 376.4 s.
2. **Iteration wall time is closed as a lane until the arm runs** (§9.155, #66).
   The 120 s target is priced as **unreachable by any measured lever**: the
   mobsim alone is 143 s of a 205.5 s iteration, and all three levers at their
   full CPU share land near 171 s. The events knob is bracketed and 4 is optimal.
   The one remaining named cut is the **time-variant link factory** — all 143,891
   links pay a synchronised binary search for 2,441 change events on 16 — worth
   ~7 % of CPU and needing a rebuild and its own probe. Reaching 120 s would take
   FIFO link dynamics or teleported walk, and both are already refused (§9.59,
   GOAL requirement 1).
3. **What the arm answers, in order** (§9.149): placement — the share of
   declared bound trips ridden against 0.560 and the walked-bound median against
   1.08 km; ride against −42.8 % read with bike (+157 %), bus (+65 %) and taxi
   (+161 %); car must STAY inside (+6.6 %); the roster and the listener as
   controls. **Read the counts on the §9.150 basis**, not #82's −91.8 %.
4. **The assessments' demand findings are root causes, not constants**
   ([docs/reports/README.md](../../../docs/reports/README.md)): evening
   departures, the inverted PT day, age-flat income, inter-LGA commute flows.
   They bear on modes the gate keeps failing and are worth issues before an arm
   is spent measuring around them.
5. **Convergence is still unmeasured** (requirement 8): no arm has passed 100
   since F4, across 158 runs and 29 days.

**Decisions required:** a fresh stated-cost approval for the next F30 arm,
priced with `python src/analyse/arm_cost.py --run-config f29_gate_25pct`;
whether the 31 unreviewed MATSim defaults (#155) are worked down before the arm
or after it; whether a fifth binder pass is needed once an arm reports the
bound-trip lengths; the Task Scheduler log (#66); whether the S2 base grants the
tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).
Taken this session (§9.154): the iteration profiled from inside the JVM rather
than reasoned from the source; three hot paths tabled and proved rather than
diffed; a declared value found inert and its companion declared; what the
framework decides undeclared enumerated and reported rather than silenced; an
arm's price read from the runs; and three ranked IO items measured and REFUSED
because the saving is not there.

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
| Iteration wall time: decomposed to the method from a flight recording, three hot paths tabled, a plain probe iteration 310 → 205.5 s and startup 13m47s → 7m00s (§9.154) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the next arm's own stopwatch, against 205.5 s profiled / ~190 s unprofiled |
| The 7 Sep assessment: 29 of 34 defects closed without a run (§9.150); the holdout stops informing the count targets and both sides of the count comparison share one basis | #82 #131 | [network-and-inputs](positions/network-and-inputs.md) · [monitoring-and-gates](positions/monitoring-and-gates.md) | counts at the F29 arm's gate, on the corrected basis |
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
