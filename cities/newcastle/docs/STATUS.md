# STATUS — city-digital-twin (Newcastle study)

*The board: one page that says how far the twin is from [the goal](GOAL.md),
what runs, and what is next. The blocks between `generated` markers are written
by `python src/analyse/build_status_board.py` from the artefacts; the
hand-written rest is capped by `tests/check_doc_shape.py`. The current truth
per topic is in [`positions/`](positions); the dated history and every
rationale are in [`DECISIONS.md`](DECISIONS.md). Nothing here is a result.*

**Last updated:** 7 September 2026 — **the five defects that were blocking
every launch are ruled on and closed** (§9.151, #147–#151), so **the issue gate
is green for the first time since it was introduced** and the toolchain is
bootstrapped. Four of the five moved no run value. The fifth does:
`EscortCoherenceListener` drew a seeded rng in `HashMap` order — the order the
sample fraction changes — and is a `TreeMap` now, so **family `F30` opens on
that one line**, on the F29 demand and network. Repairing the duplicated HTS
purpose map (#147) exposed a second half: `C.vot.by_purpose` was still keyed on
the old vocabulary, so the HX weight was dropped from the value-of-time average
and the collapse moved **16.96 → 17.317 AUD/h** against a declared 16.96. Once
re-keyed, **140 of the 141 files under `scenarios/matsim/` came back
byte-identical** — the disagreement had changed no number the model ever
scored. Registry 472 → 477, unit tests 118 → 125, `check_hardcoding` still 0,
manifest `source` 82 → 508 of 512 and `retrieved` 59 → 443. **The first F30
arm launched at 15:08 and is running; the scoreboard below is its iteration-10
reading — exploration, not a gate — and F28's gate reading (§9.149) stays the
last citable one.** A fourth assessment, lodged 17:34, measured the synthetic
demand against the package's own observations: a fifth of departures after
20:00 against 6 % observed, a PT day inverted against the Hunter's taps, income
age-flat, car-less households the wrong households, commute flows too
inter-LGA ([docs/reports/README.md](../../../docs/reports/README.md)).

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
Read from `20260907T150816_300it_25pct` at **iteration 10** (family `F30-an-escort-is-priced-as-an-escort`, status `running`, 25% sample, launched 2026-09-07T15:08:16, trips table). **Not a result** - only a run whose `_run.json` says `ran_to_last_iteration` is one, and every arm since F4 stopped before its gate.
Reproduce: `python src/analyse/report_mode_ridership.py --run 20260907T150816_300it_25pct --it 10` (`--trend` for the direction).

| # | mode | modelled | target | deviation | gate | basis |
|---|---|---:|---:|---:|---|---|
| 1 | car | 48.3143 | 58.3222 | -17.2% | over 10% | share of resident linked trips |
| 2 | ride | 9.2614 | 20.6000 | -55.0% | **STOP** >=20% | share of resident linked trips |
| 3 | walk | 26.1100 | 13.4000 | +94.9% | **STOP** >=20% | share of resident linked trips |
| 4 | taxi | 1.9942 | 0.9916 | +101.1% | **STOP** >=20% | share of resident linked trips |
| 5 | bike | 6.6622 | 2.2084 | +201.7% | **STOP** >=20% | share of resident linked trips |
| 6 | motorbike | 0.4417 | 0.3785 | +16.7% | over 10% | share of resident linked trips |
| 7 | bus | 5.2684 | 2.3819 | +121.2% | **STOP** >=20% | share of resident linked trips |
| 8 | heavy_rail | 34,796 | 6,529 | +433.0% | **STOP** >=20% | boardings per weekday, all travellers, x1/fraction |
| 9 | light_rail | 2,556 | 2,954 | -13.5% | over 10% | boardings per weekday, all travellers, x1/fraction |
| 10 | ferry | 0.0344 | 0.1429 | -75.9% | **STOP** >=20% | share of resident linked trips |
| 11 | truck | 7.7585 | 15.4698 | - | level only | network-wide road-vehicle share (not the target basis; --truck-stations scores it) |
| 12 | freight_train | 314.0000 | 314.0000 | - | representation | train movements represented by crossing closures |

Inside 10%: **none**. Past the 20% stop bar: **ride, walk, taxi, bike, bus, heavy_rail, ferry**.
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
| Input registry | **477 fields**, each with units, provenance and a sweep or a held-fixed rule; `check_hardcoding.py --strict` is a CI gate at 0 |
| Data package | **512 files** in `data/MANIFEST.csv` with hash, rows, producing script, source, licence and retrieval date |
| Run inputs assembled | **30** scenario x day-type sets under `scenarios/matsim/` (per the manifest) |
| Position pages | [light-rail-and-ferry](positions/light-rail-and-ferry.md) (4 September 2026 (twenty-seventh session)) · [monitoring-and-gates](positions/monitoring-and-gates.md) (7 September 2026 (thirtieth session)) · [motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md) (7 September 2026 (thirtieth session)) · [network-and-inputs](positions/network-and-inputs.md) (4 September 2026 (twenty-seventh session)) · [population-and-demand](positions/population-and-demand.md) (7 September 2026 (thirtieth session)) · [public-transport-and-yardsticks](positions/public-transport-and-yardsticks.md) (4 September 2026 (twenty-seventh session)) · [ride-and-pairing](positions/ride-and-pairing.md) (7 September 2026 (thirtieth session)) · [runs-and-economics](positions/runs-and-economics.md) (7 September 2026 (thirtieth session)) · [sampling-and-families](positions/sampling-and-families.md) (7 September 2026 (thirty-second session)) · [seed-and-choice-set](positions/seed-and-choice-set.md) (5 September 2026 (twenty-eighth session)) · [signals-and-crossings](positions/signals-and-crossings.md) (3 September 2026 (twenty-sixth session)) · [taxi-and-rideshare](positions/taxi-and-rideshare.md) (3 September 2026 (twenty-sixth session)) · [walk-and-bike](positions/walk-and-bike.md) (4 September 2026 (twenty-seventh session)) |
<!-- generated:state end -->

**Family F30 is open and its first arm, `20260907T150816_300it_25pct`, has run
since 15:08** (§9.151; F29 never ran one). The boundary is ONE line of the run
stack — the escort listener's draw order — on the F29 demand rebuilt 7 Sep.
`check_package.py` ALL CHECKS PASSED; the manifest holds 512 files. The arm runs
at ~375 s an iteration against F28's 260, beside a stray report-session python
burning a core since 6 Sep; its iteration-100 gate is due about 01:30 on 8 Sep.

## Runs on disk

<!-- generated:runs start -->
| run | status | family | reached | cause / note |
|---|---|---|---:|---|
| `20260907T150816_300it_25pct` | running | F30-an-escort-is-priced-as-an-escort | 24 | - |
| `aborted_20260907T145929_300it_25pct` | failed | F30-an-escort-is-priced-as-an-escort | - | launch refused before MATSim started: A.signals.representation is explicit_signals but the signals run stack is not built. Run: python sr... |
| `aborted_20260907T030352_300it_25pct` | aborted | F28-the-car-waits-only-for-a-car | 100 | Stopped automatically by the gate watcher at iteration 100 under the GOAL.md loop (RUN.gate.interval_iterations=100): GATE: 7 mode(s) at ... |
| `20260907T025531_2it_1pct` | completed | F28-the-car-waits-only-for-a-car | 2 | ran_to_last_iteration `_run.json` |
| `aborted_20260907T025046_2it_1pct` | failed | F27-a-household-drives-the-cars-it-owns | 0 | RuntimeException: could not find requested vehicle 271437 in simulation for agent BasicPlanAgentImpl{plan=[score=undefined][nof_acts_legs... |
| `aborted_20260907T024623_2it_1pct` | failed | F27-a-household-drives-the-cars-it-owns | 0 | RuntimeException: could not find requested vehicle 271437 in simulation for agent BasicPlanAgentImpl{plan=[score=undefined][nof_acts_legs... |

155 run directories on disk; `results/INDEX.md` labels every one. A dead run states its cause in its own `_meta.json`.
<!-- generated:runs end -->

## Next

1. **Read the running F30 arm at its iteration-100 gate** (due about 01:30,
   8 Sep). It was launched on a green issue gate and a built toolchain; the
   board's blocks regenerate from its trips table every ten iterations, and a
   level read while innovation runs is exploration, not a verdict (§9.108).
   **Read the counts differently**: both sides of the count comparison changed
   basis in §9.150, so #82's −91.8 % is not the figure to expect. After the
   gate, the demand findings above are the causes to fix from the root.
2. **What the arm answers, in order** (§9.149): placement — the share of
   declared bound trips ridden against 0.560 and the walked-bound median against
   1.08 km; ride against −42.8 % read with bike (+157 %), bus (+65 %) and taxi
   (+161 %), whose long car-less trips the longest-first pass should draw down;
   car must STAY inside (+6.6 %); the roster (15,582 waiting) and the listener
   (pair rate 0.9965, 0 undeclared ride legs) as controls. The listener's
   per-household proposals will differ from F28's — the draw order changed
   (§9.151) — but its aggregate counts should not.
3. **What F28 settled**: the ride loss is not pairing (solved), not the second
   car (physical), not the volume — it is where the shared pass could put its
   lifts, which the 0.05 bucket decided (§9.149).
4. **Convergence is still unmeasured** (requirement 8). It waits for an arm with
   a chance of being inside the bars.

**Decisions required:** whether to kill the stray python (pid 25480) the
assessment found burning a core beside every arm since 6 Sep; whether a fifth
binder pass is needed now the reachable binding volume is ~18.7 %; enable the
Task Scheduler operational log (#66); whether the S2 base grants the tram signal
priority ([positions/signals-and-crossings](positions/signals-and-crossings.md)).
Taken this session (§9.151): the purpose map reconciled on HX; the four network
fallbacks declared, not refused; the escort draw ordered now rather than after
an arm; telemetry protected by a refusal rather than by atomics; a derived
file's manifest provenance resolved from its lineage rather than declared.

## Open work

| Work | Issues | Position page | Next measurement |
|---|---|---|---|
| The first F29 arm's gate, every issue awaiting it | #48 #86 #49 #30 #93 #94 #96 #82 #107 #108 | all | the next arm's iteration-100 gate |
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
| Iteration wall time: a plain iteration 319 s and a milestone 569–715 s on F26's stopwatch; the trips cadence declared, plans and events moved to the gate, the detour routing parallel, the mobsim's threads probed (§9.147) | #66 | [runs-and-economics](positions/runs-and-economics.md) | the first F27 arm's stopwatch: a plain iteration against 319 s, a milestone against 569 s |
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
