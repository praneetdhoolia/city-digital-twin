# DECISIONS.md — modelling choices and their rationale

**city-digital-twin** (renamed 24 Aug 2026 from the earlier Newcastle-specific name, §9.67) —
counterfactual microsimulation of the Newcastle Light Rail
**Stage:** P4 calibration, in progress. **No counterfactual has been run and
nothing in this repository is a finding about the light rail.** The base model
has run and been measured; that measurement is a calibration diagnostic (the
figures in [`README.md`](../../../README.md), the full rows in
[`audit/CALIBRATION_REPORT.md`](audit/CALIBRATION_REPORT.md)), not a result.
**Started:** 10 August 2026 · **the newest entry is the last `## 9.x` section
before `## 10.`, and the last row of §14** — stated as a place rather than a
number, because a number here has to be rewritten to stay true and twice was
not (it read §9.75 while §9.79 was in the file).

Proposal §8.1: *"`DECISIONS.md` is not optional. Every parameter chosen without
direct empirical support must be recorded here with its rationale and its sweep
range. The credibility of this project rests on being more transparent about its
assumptions than the business case it examines."*

This file records every value in the data package whose `source` field reads
`assumed` or `modelled`, plus the scope decisions taken to close proposal §10.

---

## How to find something in this file

This file is **long and append-only** — several thousand lines. Two things about
its layout will otherwise cost you an hour:

1. **The section numbers are not in file order.** `§15` (the input registry) sits
   **before** `§14` (the change log), which is last. There is no `§16`.
2. **`§9` is not only about demand.** It is titled *Synthetic population and demand*,
   but `§9.3`–`§9.35` were appended chronologically as the build progressed, so a
   parking decision, a network decision and a toolchain decision all live under `§9`.
   **Look topics up in the table below, not by section title.** New entries should go
   under the topic section they belong to; if that is not possible, add the pointer
   here in the same change.

| Looking for | Read |
|---|---|
| **Scope, base year, zone system, S0–S6** | §1 |
| **Corrections to the proposal's own stated premises** | §2 (incl. **§2.6 — EPSG:28356 is GDA94, not GDA2020**) |
| **Road / active network, lanes, speeds, gradient** | §3, §9.28, §9.33, §9.34 |
| **pt2matsim is not reproducible run to run** | **§3.5** — one build of the network per comparison |
| **Light rail vehicle, dwell, charging** | §4, §9.18, §9.30; **§9.76 the dwell is native** — concurrent-with-boarding decided, derived offsets, anchors preserved (#74) |
| **Signals, SCATS** | §5, §9.24; refusal documented in §9.21; **§9.75 the signalling dossier ([`design/signalling/`](design/signalling/README.md)), the public operated-data discovery (TIA route, #78) and the directed by recorded decision native build (#73)**; **§9.76 the build itself** — explicit plans + tram-priority controller, probes passing, PPSHCC-137 archived — `scats_phasing` stays `unobtained` |
| **SUMO descoped; MATSim the single simulator** | **§9.74** — decision required 25 Aug; S-b native via #73 (a band regardless), reliability variance a stated limitation, deliverable 7/§9.16 retired, P5 5.1/5.2 deleted; **execution DONE §9.76 (#72)** |
| **Framework choice re-examined (MATSim vs the 2026 field)** | **§9.73** — migration rejected on a documented survey; the pinned jar embeds MATSim 2027.0-2026w25 (verified); DSim watch-only |
| **Parking supply, price, max stay** | §6, **§9.31** |
| **Land use, POI, frontage** | §7 |
| **Behavioural parameters, mode constants, VOT** | §8; **§8.5 is the rule on ASCs** — read before touching a constant |
| **Transfer penalty** | **§9.32** — not estimable from this package; the 3–15 min sweep stands |
| **Taxi / rideshare as modes** | §9.21 declined for want of a target; **§9.42 re-opened on new evidence**; §9.75 directed by recorded decision; **§9.76 BUILT INERT** — one blended priced mode on the archived Fares Order 2025 (which corrects §9.42's fare figures), band a constraint never a target (#49) |
| **Synthetic population (B1), activity chains (B2)** | §9, §9.1, §9.2, §9.15; **§9.46 binds the escort tour to the person escorted** (it was not, §9.44); **§9.47 repairs the age structure** — phantom elderly commuters, missing 75+, universal child students |
| **MATSim plans, C1 translation, what does not survive it** | §9.3 |
| **Run cost, memory, threads** | §9.5; **§9.56 the events-pipeline threads** — the all-physical model's wall-time knob, verified result-identical |
| **Convergence and the iteration count** | **§9.43 DECLARES 1000** (issue #5, two measured arms); **§9.57 re-affirms it against ~500 on both arms' trajectories**; §9.7, §9.27 are the history. **The drift window changed with it** — it starts after the cutoff, not at it |
| **The first all-physical arm (attempted, stopped) and its measurements** | **§9.57** — the 1000-vs-500 decision, the ~234 s pace, the walk-leg decomposition, the it-110 knot, the #60 turn-refusal defect |
| **The walk wedge (#60 verified and repaired)** | **§9.58** — the qsim never enforces turn restrictions (routers do, per mode); the refusals were first-hop breaks from activities on walk-less links; four repairs: the pedestrian exclusion corrected to the actual road rules, reverse walk/bike complements on one-ways, `ActivityLinkAssigner`, SubtourModeChoice person-only. NEW FAMILY BOUNDARY |
| **Iteration wall time: the declared knobs and their measurements** | **§9.59** — PassingQ link dynamics (a correctness repair of 9.54's declared PCE-0 semantics that FIFO violated), the events-pipeline and replanning-pool knobs, the probe measurements, and the honest statement against the 10x ask |
| **Non-household lifts (the reported gap, now mechanised)** | **§9.60** — M0 physical waiting at the meeting point; M1 re-targets unbound observed-rate escort tours to driverless-household passengers; pairing/boarding/sampling integrity; dossier [`design/non-household-lifts.md`](design/non-household-lifts.md) |
| **Deliverable 0b: assumptions replaced by held data** | **§9.61** — G15 tertiary full-time split (per SA1, observed), the light-vehicle day-type factors (SAT:SUN split, external weekend scaling, departure shift - all measured from the classified hourly counts), the chain-timing scaffold speeds declared, and the ranked remainder |
| **The two-arm relaunch (arm A base, arm B the seed replication)** | **§9.62** — the §9.59 concurrency pattern enacted (approved 21 Aug): qsim 8 + events 4 + xmx 30g per arm; arm B varies only `RUN.machine.seed` and is the seed-variance measurement `E.replication.n_replications` has waited on; the 50-iteration watch and its tripwires |
| **The relaunch crash: interleaved lift tours (#65)** | **§9.63** — both arms died at replanning 1 (mixed chain/non-chain subtours); the M1 busy check read stale sibling times, two lifts per driver overlapped, the splice interleaved them; repaired + contiguity assertion; B2/plans regenerated, 0 interleaved, weekday bindings 55,249 |
| **The first converged all-physical arms: C5, ride's collapse, the seed floor** | **§9.64** — both arms complete (rc=0, relaxed, accounting closes); fit MAE 10.65 pp (driver +14.2, passenger −20.5, walk −6.1, bike +8.0, pt +4.4); LR **1,260 boardings as a LEVEL** — the 3,417 target is unscorable against a 2026 base (§12.1, §9.80), never quote a per-cent error against it; ride collapses under SCORING not physics (100% of surviving requests pair) → M2 no-go; C5 written feasible=False (#14, #9 close); seed noise ≤0.11 pp/mode |
| **Batch 4.7 built inert: crossings, dwell, signals, taxi, harness safety; the activation checklist** | **§9.76** — the overnight build record; ONE boundary; warm-restart validity ruling OPEN; detached launch verified (#70) |
| **THE ACTIVATION BOUNDARY CROSSED: signals, crossings, dwell and taxi LIVE; family F6** | **§9.77** — the §9.76 checklist executed by directive; F5 closes UNMEASURED (recorded cost); the crossings-XML schema-order defect and the stale metrics line, both probe-caught; S3 bus-keyed priority via `A.signals.tsp.priority_group`; the 4.6.9 arm becomes an F6 arm, approval still required |
| **The runless lanes closed: Tier C submodes, 0b upgrades, the corridor answer, the sex-structure finding** | **§9.78** — PT submodes score-distinct via raptor mode mapping (bytecode-verified; the main-mode-identifier crash pre-empted); seven 0b source moves incl. CWANZ bike 0.493 (plans regenerated inside F6); COVERAGE carries the bus-over-tram composition (98.3% of corridor demand needs an interchange the buses don't); modelled mode split sex-invariant vs G62's real structure; the TIA sweep EMPTY; #66's capture armed |
| **The front door draws the fit; a dead run states its cause; two documents stop duplicating the record** | **§9.80** — `build_fit_figures.py` generates the README's modelled-vs-observed panels from the calibrated base's own run (`--check` gates them); the LR "−63%" **CORRECTED** — it was an error quoted against an unscorable target (#84); `_meta.json` now REQUIRES a `cause`, read from the run's own `matsim.log` by `run_failure.py`, all 14 dead runs backfilled; the currency check gains decimals and strings; `P4_CHECKPOINT.md` frozen as archive |
| **The documents drifted from the artefacts; document currency becomes a gate** | **§9.79** - `README.md` three phases stale (manifest 376 vs 489, registry 210 vs 356, road edges 43,112 vs 50,182) and two statements outright false; the cause was DUPLICATION; new `tests/check_doc_currency.py` + city-owned `doc_currency.json` pin every live figure to its artefact and gate CI; `docs/HANDOVER_CONTRACT.md` de-duplicates the two skills; **dated records stay frozen**; the superseded counts attribution becomes #82 |
| **Level crossings (freight-road interactions)** | §9.70 designed; **§9.76 built** — derived from OSM barrier tags, Stewart Avenue exclusion asserted, swept never pinned (#68) |
| **Run directories are named by the runner, never by hand** | **§9.65** — `<launch>_<iterations>it_<pct>pct` (standing directive 24 Aug); `--tag` removed; resume matches the recorded parameter set, not the name; all 35 existing directories renamed, mapping in the entry |
| **Every run carries an auto-updated status card; dead runs are `aborted_<name>`** | **§9.66** — `_meta.json` (status/started/ended/parameters, schema-checked) written at launch and updated at every transition; a dead run is renamed `aborted_<launch>_<iterations>it_<pct>pct` in place — the `_aborted_<date>` quarantine parents are dissolved; stale `running` states reconciled by pid at the next harness start; `_run.json` stays the result gate |
| **The project is `city-digital-twin`** | **§9.67** — renamed from the earlier Newcastle-specific repository name (standing directive 24 Aug): the framework is city-agnostic and the old name violated its own no-place-names rule; GitHub repo renamed (redirects stand), schema `$id`s and identity docs updated; `CITYSIM_*`/`citysim` stay tracked by the open naming issue |
| **The ride collapse decomposed and repaired: round-trip bindings, coherent seeds** | **§9.68** — of 77,626 ride-available persons 76,986 held NO ride plan (the ASC could flip 109); return legs paired at 0.0079, intermediate at 0.0, and the uniform seed's 0.2 car probability WAS the 0.196 outbound ceiling; §9.64's "supply not binding" was survivorship bias; repair: `escort_binding_directions=round_trip`, direct bound tours, serve tours seed car, covered passengers seed ride, `liftHousehold` a list; the §9.58–§9.63 family closes |
| **The short-trip mass gets its observed distribution** | **§9.69** — HTS Sydney 2012/13 Table 4.4.7 (only published AU distance-band-by-purpose table): 18.8% of trips ≤1 km vs the model's 4.45%; two-component gravity mixture per purpose, short kernel mean = the held observed walk mean (derived), weight solved to the band shares, long kernel re-solved so every observed mean stays exact |
| **Pre-LR cross-section measured from OSM history; VoT set checked against EPV 2025** | **§9.71** — Overpass attic: every lane-tagged pre-2017 Hunter/Scott segment was ONE lane per direction; `pre_lr_lanes_per_dir` 2 → 1 (B3's counterfactual onto evidence, sweep keeps 2); EPV Jan 2025: HW/WB/distance-rate supported, HE and concession divergent (flagged, unchanged), bus–LR transfer 3.8 equiv-min lands inside the 3–15 sweep |
| **Run launches, silent deaths of, and the conditional replication rule** | **§9.72** — two detached launches of the 4.6.9 arm died silently (attribution open, #70); launch arms from an interactive shell outside the agent session, verify past `PersonPrepareForSim`; no run approval standing; arm B only if arm A solo paces at 217–253 s/it |
| **Freight rail: coal chain deliberately not simulated; two crossings named** | **§9.70** — ~110 coal-train movements/day run on dedicated track grade-separated since 2006 (ARTC/PWCS/NCIG observed); adding them would fabricate an interaction; the REAL road interactions: St James Rd Adamstown + Clyde St Islington level crossings (closures "up to ten minutes", logs unpublished → swept closure parameters, backlog) and the Mayfield truck cap 1,268/day as an upper-bound constraint |
| **Sample fraction — why 1% is unusable** | **§9.10, §9.12** — never compare across fractions. **§9.45: the sampling UNIT is the household**, not the person, or every household mechanism varies with the fraction |
| **`ride`: the constant, the constraint, the free-flow defect** | §9.8, §9.11, §9.12, §9.17, §9.26; **§9.44 pairs a passenger to a household driver** — and measures that fewer than 1 ride trip in 1,000 can physically be carried; **§9.46 is the demand-side repair**; **§9.48 measures the repair on the re-measure arm — pairing 0.00004 → 0.0130, and the defect changes sign** |
| **The iteration-200 gate loop: two causes found and repaired, neither by moving a parameter** | **§9.81** the ride ratchet — a missed pairing was MUTATING THE PLAN, deleting the alternative (95.7% of iteration-0 misses gone by iteration 1); the forced walk becomes an EXECUTION restored at `AfterMobsim`. **§9.82** the empty escort tours — 84.53% of escort trips car against 11.45% of escort-bound members riding; `EscortCoherenceListener` PROPOSES the coherent plan back, `ChangeExpBeta` decides. Families **F7**, **F8** |
| **Which quantity a gate reading is taken on, and why the record's "car bias" was not one** | **§9.83** — `modestats` counts PLANNED modes; events give LEGS across five LGAs; `fit.py` scores linked main-mode TRIPS for target-LGA residents, and `<n>.trips.csv.gz` carries exactly that per iteration. Reading it inverts the car verdict (11.7% UNDER, not over) and shows bike+taxi fold into ONE target. `src/analyse/measure_iteration_modes.py`. **Corrects §9.82's probe reversal — it is the innovation cutoff at 0.8 × 8, not convergence** |
| **The ride gap is a DEMAND CEILING, not a mode-choice defect** | **§9.83** — every B2 trip has `party_size = 1`; escort-bound travel is 5.4% of trips against an observed 20.6%; occupancy 1.0013 modelled vs the **measured** 1.3503. This is the measurement **§9.55** named as decisive, and the displaced mass lands in bike, taxi, walk and pt. The declared, swept lever is `B.activity.escort_binding_nonhh_scope` (§9.60) |
| **The joint-tour binder, the gradient channel and the age gates (family F9)** | **§9.84** — the demand ceiling's mechanism: adult joint household travel generated as pairs, anchored on the measured occupancy ratio and the observed driver share, eligibility only; gradient into walk/bike link travel time on both router and mobsim sides; taxi/bike age gates, zero disables; the §9.60 scope lever measured as spent (98% consumed at `same_zone`); `--max-persons` probes are blind to household mechanisms |
| **A declared pair is re-found by a clock the model itself moves (family F10)** | **§9.85** — the B2 binding tables name the driver and `build_matsim_plans.py` read that identity for SEEDING and then threw it away, so `RidePairingEngine` re-discovered declared pairs from geometry and a 15-minute window while MATSim's `TimeAllocationMutator` — at an UNDECLARED ±1800 s default — moved the two members apart independently. The driver is present, on car, on the same trip, and refused on the clock. `boundDriver` carries the identity; the tolerance for a declared pair is DERIVED from the mutation range |
| **A hired car is a car on the road: taxi stops being a ghost in the mobsim (family F11)** | **§9.86** — `taxi` was routed on the network, permitted on 143,891 links, bound to the congested car travel time and given a car-bodied vehicle type, but was NOT in `RUN.qsim.main_mode`, so MATSim teleported it: **39,892 of 39,923 legs per iteration** never touched the carriageway (#88). One enum value fixes it; the body restates `RUN.qsim.car_vehicle` rather than inventing a second one. Probe-measured: 197 of 197 taxi departures now enter traffic, 29,994 link traversals. **Deadheading stays unmodelled and unassumed.** `ride`’s remaining 44.5% teleport is a DEMAND failure, not a mobsim one — never close it with a phantom vehicle per passenger |
| **Twelve modes get twelve targets: a folded survey category cannot answer a per-mode question** | **§9.87** — the HTS publishes SIX categories and this city simulates TWELVE modes, so four modes shared one 3.8% Public Transport row and a fold could hide an excess behind a deficit. The data document’s own lists EVIDENCE `fit.py`’s folds (bike+taxi → Other; motorbike appears in no other category, so it can only be a Vehicle driver). `build_mode_targets.py` disaggregates every level with census G62 composition and current Opal/station boardings, writes `mode_targets_by_mode.csv`, and is read by `report_mode_ridership.py`. **PT splits on CURRENT boardings, not the lockdown-vintage 2021 census — the census sets the sweep’s far end instead.** Ferry stays **unobtained and swept**: nothing is published for this city. The person-trip targets sum to 99.4037%, and the missing 0.596 pp is resident truck-driving, written out as a named deduction rather than folded into car. **NOT added to `validation_targets.csv`** — it would double-count and disturb the 67/143 split |
| **SCATS stops being an assumed constant and becomes an algorithm (family F12)** | **§9.88** — every arm to date ran 14 corridor intersections on a FIXED 110 s plan, because the unreleased phase data was handled by sweeping a cycle time. `citysim.ScatsSignalController` implements the published logic instead: degree of saturation measured at every stop line from `LinkLeaveEvent`, incremental cycle adaptation toward a target DS on the critical movement, splits equalising DS across stages, clearances preserved. **Offsets deliberately NOT adapted** — that library is the unreleased artefact and no algorithm replaces it. Two defects recorded: DS measured against FULL-SCALE capacity read 0.000 at a 1% sample (`qsim.flowCapacityFactor` belongs in the denominator), and modular cycle arithmetic cannot survive a variable cycle. Transit priority lives inside the controller, and **compensation becomes intrinsic** — a starved stage’s DS rises and the next split repays it |
| **The ferry gets a derived target instead of no target at all** | **§9.89** — no Newcastle ferry patronage is published anywhere (the Opal all-modes Ferry row is NSW-wide and Sydney-dominated), so §9.87 left mode 10 of 12 ungateable. The census G62 one-method count (40 of 1,501 PT journeys, 2.665%) sets the share WITHIN PT, which the HTS 3.8% scales to **0.1013%**. Defensible for THIS mode because the Stockton crossing is captive (a ~20 km road detour) and a within-PT share is far less lockdown-sensitive than a level. Sweep stays wide, 0 to 2x; the value is labelled `derived`, never `observed` |
| **A crossing closes for every train that crosses it, and the timetable says which** | **§9.90** — `A.crossings.closures_per_day` was 30, assumed, uniform across 24 h and identical at both sites. The city’s OWN mapped rail timetable was already in the package: `build_level_crossings.py` now counts every scheduled service whose mapped route traverses the rail links at each crossing and times each closure from that service’s stop time. **Adamstown 110/weekday, Islington 204** (541 → 3,014 change events), peaked at 17h rather than flat — and the shape matters more than the count, because uniform closures land where there is no traffic to delay. Freight stays declared and swept at ZERO on §9.70’s grade separation. Mode 12 gets a target: **314 closures/weekday**, so with §9.89 all twelve modes are gateable |
| **The gate fires at iteration 50, and the first defect is in the yardstick** | **§9.91** — ten of twelve modes past 20%, taxi DIVERGING (1.20% → 7.75% against a 0.19% target). The target was the defect: §9.87 sized taxi from the census JOURNEY-TO-WORK share, and taxi is overwhelmingly not a commute mode. `B.taxi.daily_trips_band` (IPART 2025, 15,000–25,000 point-to-point trips/day) gives **0.9916%**, ~5× higher, and **bike takes the residual 2.2084%** because the two share one survey category. Measured on the arm rather than reasoned: taxi costs 27.13 AUD per median 13.1 km trip, taxi plans score −128 vs −44, the flagfall fires, and taxi is 7.52% even among agents holding a car AND a licence — so scoring is not the culprit and it is not captive demand. Taxi is **seeded at exactly 0.0** and arrives entirely through innovation. Also recorded: the held-fixed fare rule’s own departure condition is now MET (median taxi trip 13.1 km against its “far under 12 km” premise), and `ride` legs are **23.33% zero-distance** against car’s 1.09% |
| **The seed is a bad guess ON PURPOSE, and the gate was read before the model had answered** | **§9.92** — three paired 1% diagnostics. The chain-breaking single-trip innovation is REAL but small (car 36.26% → 40.34% at p=0.0, about a sixth of a 22 pp deficit) and is not the lever. The deficit is inherited from the SEED, which is uniform **by recorded design** — "deliberately a bad guess… so that arriving there is evidence about the model rather than about the seed", with an `informed` table kept precisely because "seeding at the answer makes reaching the answer uninformative". **So the seed must NOT be changed to close the gap.** Both arms show car JUMPING at the innovation cutoff (31.96% → 35.90%), so a reading at iteration 50 of a 1000-iteration arm measures an innovation-dominated transient, not the model. And **ride −65% / walk +94% are ONE mechanism**: 44,044 of 84,609 ride legs (52.1%) fail to pair and, with `remodeUnpaired`, none departs as ride — they are realised as walk |
| **The uniform seed IS recoverable for three modes, and diverges for three others** | **§9.94** — the first F12 arm to reach a gate (`20260829T054941`, 10%, 108 s/it), stopped at iteration 102. Read on TREND rather than level, because §9.92 established the seed is deliberately bad. **CONVERGING**: car 34.09 → 44.22 (58.16), walk 28.88 → 15.22 (13.40), pt 6.88 → 5.30 (3.80) — walk has gone from +115% to +14% of target, and this is the FIRST evidence the co-evolution recovers from the seed at all. **DIVERGING**: taxi 0.00 → 8.81 (0.99), bike 7.08 → 8.24 (2.21), ride 19.03 → 14.19 (20.60). Ride is worst because it SEEDS almost exactly right and the model destroys it — a feedback loop where pairing failure walks the leg, the plan scores badly, the agent drops ride and thins the candidate pool. Taxi’s repair is a finite FLEET, recorded as NOT DONE with the reason: the pinned stack carries no DVRP/DRT and adding it is a toolchain change against a Maven host the sandbox does not list; the demand-side alternative needs a point-to-point user incidence the package does not hold |
| **The bound pairing window was HALF the drift it covers, and a third of ride demand names nobody** | **§9.95** — new `src/analyse/diagnose_ride_pairing.py` classifies every declared ride leg by what its named driver was doing. **The suspected cause was wrong**: `neither_endpoint` (the household drove elsewhere) is only **1.49%**. Two real defects instead. (1) `bound_pairing_window_min` was `time_mutation_range_s / 60` = 30 min, but the mutator moves each member INDEPENDENTLY, so two draws on ±1800 s land up to 3600 s apart — the window was half the drift, and 3,987 legs (13.13%) with BOTH endpoints matching were refused on the clock alone, median gap 53.6 min, **minimum exactly 30.0**. Identity corrected to `2 * range / 60` = 60 min. (2) **9,036 legs (29.76%) carry no `boundDriver` at all** — filed as #91 |
| **CORRECTION: ride’s seeded share is the uniform draw, not evidence about the binder** | **§9.96** — §9.94 and §9.95 both read ride seeding at 19.03% against a 20.60% target as "the demand is right". It is not. Ride’s initial mode comes from the DELIBERATELY UNIFORM `B.mode.seed_split` at p=0.20/0.25, and with 76.3% of trips car-available the uniform draw alone predicts **21.2%**. The near-match is a coincidence of 0.2 sitting close to 0.206. **Withdrawn**: that the seed vindicates §9.84’s binder. **Corrected**: #91’s 29.76% unbound is the expected consequence of a uniform seed, not a binder that forgot to bind. §9.95’s two measured defects stand unchanged |
| **A diagnostic that read today’s window into yesterday’s arm — and the THIRD instance of one error** | **§9.97** — `diagnose_ride_pairing.py` took the bound window from the LIVE REGISTRY rather than the run that executed it, so a historical arm was re-classified under today’s rule and the reclassification looked like a model improvement. It announced itself: a 30-minute arm reported a **minimum gap of 60.1 min**, which is impossible. Fixed to read the run’s own `config.xml`. Done properly, depth-matched at iteration 50 with each arm under its own window: paired_ok 40.07% → **42.02%**, window_only 10.68% → **8.37%**, everything else within 0.25 pp. **Real, but +1.95 pp against the ~7 pp §9.95 predicted.** Residual `window_only` legs now have a median gap of 344 min — different trips, not drift. **Three instances this session of one error: a comparison whose two sides were not the same kind of thing** |
| **The window correction at depth: real, and NOT the bottleneck** | **§9.98** — depth-matched at iteration 100, each arm under its own window: paired_ok 37.96% → **41.53%** (+3.57 pp), window_only 13.13% → **8.82%**, everything else within 0.4 pp. Larger at depth than at iteration 50 (+1.95 pp), as accumulating drift predicts — but still about HALF the ~7 pp §9.95 predicted. **It bought +0.19 pp of ride mode share.** The bottleneck is upstream: 30.16% of ride legs carry no declared driver, and the plan-level abandonment happens before pairing is attempted. Widening further is measurably pointless — residual `window_only` median gap is **344 minutes** |
| **Taxi gets a finite fleet, and a refused request walks** | **§9.99** — §9.94 recorded taxi as BLOCKED on the DRT contrib. The blocker was real; the inference was not. A fleet needs the `BeforeMobsim` boundary, not a dispatcher — **exactly where `RidePairingEngine` has paired ride legs since §9.44**. `TaxiFleetEngine` serves taxi legs greedily from the earliest-free vehicle and REFUSES any request beyond `max_wait_min`; a refusal WALKS and has taxi restored at `AfterMobsim` (§9.81’s correction). **Nothing caps the share — the constraint is the price.** Fleet DERIVED: `mean(daily_trips_band) / vehicle_trips_per_day` = 800, scaled by the sample factor. Probe: iteration 1 serves 250 of 274 and refuses 24 at 340 s mean wait, then requests fall to 177. Empty running is unavailable TIME, not routed legs — stated, not hidden |
| **`age` and `taxi` reach no availability gate; gradient reaches mode choice through nothing** | **§9.83** — `AvailabilityModesCalculator` gates `rideAvail`/`bikeAvail`/`lockedMode`, **taxi nothing**; 0–4 year olds take 31.1% of trips by bike and 19.5% by taxi, but this bounds at 19% of the excess. Gradient: 30.5% of 50,182 edges steeper than 4%, modelled bike 9.21 km/41.7 min against a measured 5.2/19.2. Both measured, NEITHER built (#21 was closed on the honest `not_representable` record) |
| **Trip length by mode** | §9.13; destination placement per home LGA **§9.40** |
| **External / boundary demand** | §9.14, §9.15, §9.20; through traffic **§9.41** |
| **Freight / heavy vehicles (`truck`)** | **§9.49** — a physical background load: measured profile and gate shares, assumed and swept volume ratio, PCE and decay; issue #24 |
| **The calibrated base (deliverable 5)** | **§9.50** — constrain-and-report, logged before the base run's results; ASCs stay §8.5 priors, #9 resolved by decision, the §9.48 occupancy excess reported not absorbed. **The base arm was stopped (§9.51) — C5 and the report await its relaunch** |
| **The four standing directives (20 Aug)** | **§9.51** — physical ride (no teleportation), 9+ modes individualised (G62 verified to carry them), the sub-1 km walk deficit (#30 re-opened), demographic-conditional mode fidelity. These set the value order |
| **Motorbike as a mode** | **§9.52** — a physical person-level locked carve from car-driver demand, anchored on the measured G62 JTW share (0.363%), swept 0–1%; fit compares car+motorbike against the Vehicle-driver target |
| **Physical ride boarding** | **§9.53** — a paired passenger enters the driver's car in the qsim (`JointRideEngine`); misses fall back to Tier 1 and are counted; **§9.55 re-modes the unpaired to physical walk — the ride share becomes EMERGENT from the driver supply** |
| **Walk and bike physical; the transit stubs** | **§9.54** — walk at PCE 0.0 / bike at PCE 0.2 in the qsim, road-rule exclusions + per-mode SCC cleaning, teleported fields retired (the measured 1.6902 survives as the access-stub factor), `TolerantAgentSource` + `GenericRouteTeleporter` for the transit router's generic walk stubs |
| **The 30-hour-day cap (issue #37)** | **§9.38** |
| **Bike availability (issue #29)** | **§9.39** |
| **Calibration loop, fit statistic, outer-loop tolerance** | §9.16, §12 |
| **The specification audit** | §9.25 and [`docs/audit/SPEC_AUDIT.md`](audit/SPEC_AUDIT.md) |
| **The input registry — every controllable value** | **§15**, and [`docs/reference/CONFIG_REFERENCE.md`](reference/CONFIG_REFERENCE.md) (generated) |
| **City portability, `cities/<city>/registry/`** | §9.29, §15 |
| **The OSM harvest extent, and the corrupt merge** | **§9.35** |
| **Scenario construction (E1), era variants (A3)** | §10, §11 |
| **Validation design, the 67/143 split** | §12 — the split is **pre-registered**; never calibrate on a holdout row |
| **Outstanding data tasks** | §13 |
| **Toolchain pins — a toolchain change is a model change** | §14 (change log) and `.tools/toolchain.json` |
| **Live view, telemetry, the congestion map** | **§9.36** |
| **Dated build narrative** | [`docs/handover/SESSION_LOG.md`](handover/SESSION_LOG.md) — archive; this file is authoritative |


---

## 0. Status summary

| Layer | Observed | Modelled / assumed | Not obtained |
|---|---|---|---|
| A1 road network | geometry, class, names | lanes, width, speed, kerbside, capacity | signal-level turn counts |
| A2 signals | 1,265 signal locations, 1,386 turn restrictions | cycle time, phasing, offsets, TSP | **SCATS phase data** |
| A3 PT supply | 4 GTFS eras, real feeds | pre-2014 era, stop/transfer attributes | pre-2014 timetable |
| A4 LR vehicle | length, mass, fleet, charging principle | accel, doors, dwell, **charging dwell** | measured dwell |
| A5 parking | 7,710 facilities, 4,861 capacities | price, max stay, occupancy | meter transactions |
| A6 active transport | geometry, gradient from DEM | width, lighting, crossing delay | footway widths |
| B demand | census, HTS, Opal, 119 traffic counts | synthetic population, plans | **journey-linked Opal** |
| C behaviour | VOT from published guidance | **transfer penalty**, walk decay, ASCs | local estimation |
| D land use | POI, buildings, jobs by SA2 | frontage floorspace, vacancy | retail floorspace, ped counts |

Three inputs the proposal named as critical remain unobtained and are handled by
sweep rather than assumption-as-fact: **SCATS phasing**, **journey-linked Opal**,
and **measured charging dwell**. Each is a formal data request (§7.2 fallbacks
are implemented below).

---

## 1. Scope decisions (closing proposal §10)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Base year | **2026**, using 2021 Census marginals with HTS 2024/25 behaviour | The 2026 Census is being collected now and will not release before mid-2027. Proceeding on 2021 marginals + current HTS, with the 2026 re-run scheduled as validation, is the proposal's recommended option (§7.3). |
| 2 | Zone granularity | **SA1 in the core, SA2 externally** | 1,500 core SA1s at ~400 persons each resolve the corridor; the external tier only carries Hunter Line through-demand and does not need SA1. |
| 3 | Study boundary | Five LGAs (Newcastle, Lake Macquarie, Maitland, Cessnock, Port Stephens) = 4,086 km², core. Remainder of SA4 *Hunter Valley exc Newcastle* = external boundary tier. | Selecting on SA4 alone dragged in Upper Hunter and Singleton (20,043 km²), far beyond any plausible influence on a 2.7 km corridor. The Hunter Line is cut at **Maitland**, with external SA2s as a boundary treatment. |
| 4 | S2c (Option A alignment) | **Built.** | Cheap to derive once the run-time decomposition exists — it is a speed and signal-conflict change on the same stop set. It is also the alignment with plurality public support, so its omission would be conspicuous. |
| 5 | Weekend modelling | **Full weekend day type built** (WEEKDAY / SAT / SUN in every feed) | Beach and event demand is arguably this system's strongest use case. Excluding it would bias against the light rail. |
| 6 | Event demand | **Not yet built.** Day types exist; an event overlay is not. | Requires venue-level attendance data not yet requested. Recorded as an open task, not silently dropped. |
| 7 | Publication venue | Deferred — not a data decision. | |
| 8 | Data request strategy | Open data harvested first; formal requests still required for SCATS, journey-linked Opal, parking transactions, pedestrian counts. | The open harvest turned out to cover far more than the proposal assumed (see §7), which reduces dependence on the requests. |

---

## 2. Corrections to the proposal's stated data hazards

Working the data changed three of the proposal's premises. Recorded here because
§9 requires that any change to the pre-registered position be logged.

**2.1 — There *is* a clean post-opening, pre-pandemic patronage baseline.**
Proposal §6.4 states the Opal Patronage dataset begins January 2020, "two months
before the pandemic", leaving "effectively no clean post-opening, pre-pandemic
baseline in the public data." The **Opal Trips – Light Rail** series in fact
begins **February 2019, the opening month**, and runs continuously to
September 2025 — 89 months. That yields a full 12-month clean baseline
(March 2019 – February 2020) of **3,417 boardings/day**, now the primary
calibration target. This materially strengthens the identification strategy.

> **Superseded on this last point (§12.1, and see §9.80).** The series is real
> and the correction to proposal §6.4 stands. Calling it *the primary calibration
> target* does not: §12.1 later established that March 2019 – February 2020 is a
> pre-pandemic PT market against a 2026 base year, so `fit.py` marks V001/V002
> **unscorable** and the modelled boardings are reported as a level. This
> sentence is the origin of a "−63% error" that was quoted for three handovers
> against a target nothing scores (issue #84). The record is left as written; the
> live position is §12.1.

**2.2 — The 1 July 2024 series break is real, and it is compounded by a second,
undocumented break.** NISC 1 bus boardings fall from ~292,000 (October 2024) to
~89,000 (October 2025). That is far larger than a methodology restatement should
produce. The historical GTFS archive shows a new feed,
`regionbuses-newcastlehunter`, first appearing in September 2024 — i.e. the
contract region was **re-scoped** at about the same moment the trip-counting
methodology changed. Any series crossing mid-2024 therefore carries **two**
confounded breaks, not one. All such series are flagged
`methodology_epoch` and are never compared across the boundary.

**2.3 — The published light rail GTFS cannot be used to infer dwell or run-time
variance.** The base feed reports a flat **12.00 minutes** end-to-end in both
directions for all 954 trips, with segment times of exactly 120 or 180 seconds
and **zero dwell at every intermediate stop**. It is an idealised planning
schedule, not an operational one. Consequently:
- observed run time and dwell must come from GTFS-Realtime or field measurement;
- the *scheduled* 12.00 min is retained only as a calibration reference;
- the run-time decomposition in §4 is the model's actual basis.

**2.4 — 2021 Census journey-to-work is unusable as a mode-share target.** Of the
core-area workforce, **56,619 worked from home and 45,289 did not go to work** —
about 34% of all responses. Public transport records 1,461 journeys total
(bus 1,178, train 231, tram/light rail 52), a 0.8% mode share against an HTS
figure of 7.3% pre-pandemic. G62 is retained for *spatial* structure only; the
mode-share calibration target is HTS.

**2.5 — The corridor is not 75–98% imputed; that was the network-wide rate.**
§3.1 measured imputation over all 43,112 road edges and concluded that
"manual correction from aerial imagery is required on the Hunter/Scott corridor".
Measured *on the corridor* — the 40 Hunter and Scott Street edges within 60 m of
the light rail alignment, 4.08 km — the rates invert:

| Field | Corridor trunk observed in OSM | Network-wide imputed (§3.1) |
|---|---:|---:|
| `num_lanes` | **87.5%** | 75.4% imputed |
| `speed_limit_kmh` | **97.5%** | 53.7% imputed |
| `oneway` | 87.5% | — |
| `kerbside_use` | 27.5% | 98.0% imputed |
| `lane_width_m` | 0% | 99.2% imputed |

The corridor is one of the best-mapped parts of the extract, not the worst — and
the imputation rate over the 84 corridor cross streets (23.8% lanes observed) is
much closer to the network-wide figure, which is what §3.1's average was actually
measuring. The as-built corridor reads `lanes=1, oneway=yes, maxspeed=40`,
consistent with NSW Movement and Place: *"one lane of traffic in each direction
on Hunter and Scott streets between Worth Place and Telford Street"*.

**Consequence.** The 30–40% of network-build effort the proposal budgeted for
manual aerial correction is not needed for the as-built lane counts, which are
observed. What is genuinely unavailable is the **counterfactual** — Hunter and
Scott *before* the tram — which no 2026 imagery can supply. That is now an
explicit swept assumption (§3.4) rather than a digitising task. The B3
net-arrivals test is therefore an observed-network-versus-assumed-network
comparison, and the assumed side is the one that is swept.

**2.6 — EPSG:28356 is GDA94 / MGA zone 56, not GDA2020.** The repo labels the
CRS "EPSG:28356 (GDA2020 / MGA Zone 56)" throughout. EPSG:28356 is
*GDA94* / MGA zone 56; GDA2020 / MGA zone 56 is EPSG:7856. The two differ by
about 1.8 m — immaterial to network topology, junction geometry or run time, and
well inside the positional error of the OSM geometry the network is built from,
so **the projection in use is not changed**. The label is wrong and is corrected
here rather than propagated. Note that the ABS boundary downloads *are* GDA2020
(their filenames say so), so the 1.8 m offset is real but absorbed at zone
resolution.

---

## 3. Network layers (A1, A6)

### 3.1 OSM completeness — imputation rates

Proposal §6.4 predicted OSM lane counts, turn restrictions and kerbside use
would be unreliable. Measured rates over 43,112 road edges (9,207 km):

| Field | Imputed | Share | Default rule |
|---|---:|---:|---|
| `lane_width_m` | 42,747 | 99.2% | 3.2 m |
| `kerbside_use` | 42,233 | 98.0% | `unknown` |
| `num_lanes` | 32,499 | 75.4% | by road class (2 motorway/trunk/primary, else 1, per direction) |
| `speed_limit_kmh` | 23,151 | 53.7% | by road class (NSW urban default 50) |

Footways (35,653 edges, 6,325 km): `width_m` imputed 98.4%, `lighting` 98.9%.

**Consequence.** Car delay results are only as good as the corridor lane counts.

> **Superseded by §2.5 and §3.4 (P2).** This section originally concluded that
> manual correction from aerial imagery was required on the Hunter/Scott corridor.
> Measured on the corridor rather than network-wide, 87.5% of trunk lane counts
> and 97.5% of trunk speed limits are observed in OSM, and the imagery correction
> is not needed for the as-built network. The counterfactual — the corridor
> *without* the tram — is what cannot be observed, and it is now an explicit swept
> assumption. The claim in the last line below was also wrong: corridor edges were
> **not** flagged via `scenario_variant_ref` (every one of the 43,112 A1 rows
> carries `base2026`); they are flagged in
> [`A1_corridor_road_edges.csv`](../data/processed/network/A1_corridor_road_edges.csv)
> as of P2.

### 3.2 Capacity

Mid-block capacity `veh/hr/lane` by class: motorway 2000, trunk 1800, primary
1600, secondary 1400, tertiary 1200, unclassified 1000, residential 800,
service 400, living_street 300. Austroads-style values, **assumed**. Sweep ±20%
where corridor results prove sensitive.

### 3.3 Gradient

Source: **Copernicus GLO-30 DEM**, tiles S33E151 and S34E151, sampled at each
edge's endpoints. Gradient is stored in the digitisation direction; the reverse
takes the negative, satisfying the proposal's asymmetry requirement (§6.3).
Footways additionally carry `walk_speed_factor_fwd` / `_rev` from a Tobler
hiking function normalised to 1.0 at zero grade.

Results: |gradient| median 2.07% (road), 1.68% (footway); p90 9.3% / 12.2%.

**Two caveats, both assumed away for now.**
1. GLO-30 is a **surface** model (DSM), not a terrain model. On short edges under
   tree canopy or beside buildings it overstates relief — visible in the p99
   pinning at the ±25% clip.
2. Gradient is endpoint-to-endpoint, so a way that dips and rises reports ~0.

Both are acceptable for network-wide accessibility and unacceptable for The Hill
and Newcastle East, which the proposal specifically names. **Action:** replace
with 5 m LiDAR DTM from ELVIS for the CBD, Cooks Hill, The Hill and Newcastle
East before publishing accessibility surfaces.

### 3.4 Corridor attribute provenance and the E1 road variants (P2)

`src/build/build_corridor_road_attributes.py` grades the corridor by evidence
rather than correcting it by hand, and turns `scenarios/E1_road_variants.csv`
into edge-level deltas. Three artefacts:

| File | What it holds |
|---|---|
| [`data/processed/network/A1_corridor_road_edges.csv`](../data/processed/network/A1_corridor_road_edges.csv) | 605 corridor / parallel edges, each attribute paired with a `*_source` of `osm`, `imputed_rule`, `assumed` or `absent` |
| [`data/processed/network/A2_turn_restrictions_resolved.csv`](../data/processed/network/A2_turn_restrictions_resolved.csv) | all 1,385 OSM restriction relations resolved to coordinates and to a distance from the alignment |
| [`data/processed/network/A1_road_variant_patches.csv`](../data/processed/network/A1_road_variant_patches.csv) | 195 rows: the only places any E1 variant departs from the observed network |

**Corridor extent is geometric, not drawn.** The alignment comes from the tram
route's own GTFS shapes. `corridor_trunk` = Hunter/Scott within 60 m of it (40
edges); `corridor_cross` = any other road within 40 m (84 edges, the cross
streets at the 14 signalised intersections); `parallel` = the named comparator
and diversion routes within 1.5 km (417 edges).

**Turn restrictions are observed, and now checkable.** `A2_turn_restrictions_osm.csv`
stored member strings with no geometry, so E1's `banned_turn_movements` could not
be verified. Resolving each relation through its via node, else its via way, else
its from way, locates 1,385 of 1,386 (one relation has no resolvable member) and
puts **10 within 40 m** of the alignment and 15 within 80 m, against E1's assumed
14. E1's figure is a reasonable summary of the observed restriction set, and the
network build uses the observed restrictions, not the number.

#### Assumed values introduced here

| Value | Assumed | Sweep | Why it cannot be observed |
|---|---|---|---|
| `pre_lr_lanes_per_direction` (Hunter/Scott without the tram) | **2** | **1–2** | The tram was built in 2017–19. A 2026 extract, and 2026 imagery, show only the post-tram cross-section. This is the counterfactual the whole B3 test rests on. |
| `pre_lr_kerbside_use` | `parking` | — | Same reason. E1 already asserts kerbside parking is restored in the no-tram network. |
| `extension_lane_take_per_direction` (S4/S5) | **1** | **0–1** | The extensions were never built. The rule mirrors what the tram did to Hunter/Scott: one running lane per direction, floored at one, and the kerbside where the street is already single-lane. |
| Extension corridor extent | derived from the S4/S5 **stop** sitings | — | See the defect below. |

#### A P1 defect this exposed

The S2c, S4 and S5 scenario feeds add or move stops but carry the **unmodified
275-point as-built shape** — all four tram feeds have byte-identical geometry.
So the Broadmeadow and John Hunter Hospital extensions have stops hanging off an
alignment that stops at Newcastle Interchange, and S2c's "reserved former-railway
alignment" is geometrically the as-built street alignment.

Handled, not hidden:

- the extension corridor (66 edges for S4, 89 for S5) is derived from the
  extension **stop coordinates**, which do exist, by interpolating through the
  stop sequence and buffering at 60 m. The stop sitings are themselves assumed
  (§10), so the extension corridor is assumed twice over and is labelled so;
- S2c is unaffected in road terms — it uses the full-capacity Hunter Street
  network either way — but its run-time advantage is a property of its GTFS
  timings, not of a modelled alignment, and should not be reported as though the
  reserved corridor had been traced;
- **Action:** rebuild the S2c/S4/S5 shapes in `build_scenario_schedules.py`
  before any extension result is published.

**Resolved at P3 (10 August 2026).** `src/build/shape_tools.py` builds the
missing geometry from layers the package already observes, and
`build_scenario_schedules.py` writes it into the feeds. The defect turned out
to extend one feed further than recorded above: **S0** extends heavy rail to
Civic and Newcastle without extending its shape either.

| Feed | Alignment now | Length | Evidence |
|---|---|---|---|
| S4 / S5 | Routed over the **observed OSM centreline** of the streets the 2020 NLR Extension Strategic Business Case names — Tudor, Belford, Lambton Rd, Turton Rd, Russell Rd, Lookout Rd | 7.00 km to JHH (S4 is this truncated at Broadmeadow, 2.58 km) | The SBC states **6.65 km**; the independently routed corridor lands **+5.3%** on that, over the published street sequence |
| S2c | The retained **harbour-side former-railway strip**, observed where it survives (Foreshore Footpath) and interpolated across the redeveloped gap | 2.93 km | 33% of the length is observed OSM geometry; the rest is interpolated and labelled so |
| S0 | The same corridor, to the former Newcastle station | 2.58 km | 21% observed |

**Stop sitings are still assumed, but no longer typed.** Each extension stop is
now anchored on an observed feature and then projected onto the routed
corridor:

| Stop | Anchor | Offset |
|---|---|---|
| Hamilton (Beaumont St) | observed Tudor St × Beaumont St intersection | 0 m |
| Broadmeadow | observed `railway=station` node, Broadmeadow Station | 98 m |
| Lambton | observed Lambton Rd × Turton Rd intersection | 0 m |
| John Hunter Hospital | observed POI `w1025992530`, `health:hospital` | 107 m |

The P1 coordinate for **Hamilton sat 548 m off the published corridor** — it
was near Beaumont St/Maitland Rd rather than on Tudor St. That is the one
siting the correction actually moves.

**Consequences, both material:**

1. **The extension corridor roughly doubled.** Derived from a real 7.0 km
   routed alignment rather than a straight-line interpolation through two to
   four stops, the E1 patch set grows from 195 rows to **414** (S5 89 → 240,
   S4 66 → 134). Corridor/parallel edges go from 605 to **714**. The extension
   lane take is applied to far more edges than at P2, and 85.4% of those lane
   counts are observed in OSM.
2. **S2c is now a different scenario in the model, not just in the timetable.**
   Its 11 tram stops move onto the reserved corridor (about 115 m north of
   Hunter Street) *before* the run-time decomposition, so its timetable
   describes the reserved alignment. Previously its stops sat on Hunter/Scott
   and pt2matsim mapped them to the street network — the alignment the
   scenario exists to avoid.

**One pre-existing source-feed limitation, measured rather than patched over.**
**477 of 4,374 base-feed trips (10.9%)** carry a GTFS shape that ends more than
500 m from the trip's own last stop — worst case 249 km, the intercity services
whose shapes cover only part of the run. It is identical in every scenario feed
so it cannot bias a comparison. The S0 corridor is therefore spliced only onto
shapes that actually reach the Interchange (`S0_JOIN_TOLERANCE_M = 1500 m`);
125 of the 254 extended trips keep their short source shape rather than gain
an invented 2.4 km of geometry.

### 3.5 pt2matsim is not reproducible run to run — measured, not assumed away

`PublicTransitMapper` does not produce byte-identical output from identical
inputs. Confirmed across `SpeedyALT`, `AStarLandmarks` and `CHRouter`, and at
`numOfThreads=1` as well as 3, so it is not thread scheduling — it is candidate
selection over a hash-ordered collection. This collides with the project's
determinism rule, so the drift is measured and published rather than waved
through (`--determinism-check` in `build_matsim_network.py`):

| Property | Repeat-build agreement |
|---|---|
| stop → link assignment | **100.000%** |
| transit route count | 1,714 = 1,714 |
| stop facility count | 4,171–4,178 (±0.17%) |
| **route link sequences** | **81.9–82.3%** |

So roughly **18% of transit routes take a different path between two builds of
the same feed**, while every stop attaches to the same link every time. That
matters for bus link loading, and therefore for B3.

**How this is handled.**

1. The mapped schedules are a **build of record**: hashed into
   `data/MANIFEST.csv`, and the artefacts P3+ consume. Regeneration reproduces
   the model statistically, not byte-for-byte.
2. `tests/check_package.py` asserts the reproducible half **exactly** — the
   `stop_link_fingerprint` must match the recorded build — and asserts the
   invariants that hold in every build (no unmapped stop, artificial link share
   under 5%).
3. `route_link_fingerprint` is recorded per feed to identify which build a result
   came from.
4. **Any scenario comparison must be run against one build of the network.**
   Comparing S2 mapped in one build against S0 mapped in another would put an
   18% route-path difference inside the treatment effect. This is a P5 run
   constraint, recorded here because it originates in P2.

Everything else in P2 *is* deterministic: the OSM merge, the variant patching and
netconvert are byte-identical on rebuild (verified by re-running and comparing
digests).

### 3.6 Toolchain, pinned

P2 needs a JVM, pt2matsim and SUMO, none of which the repo can regenerate.
`src/setup/bootstrap_toolchain.py` fetches all three into `.tools/` (gitignored)
and records version, source URL, sha256 and retrieval date in
`.tools/toolchain.json` — the provenance record for the tools, mirroring
`data/raw/provenance_*.json` for the data.

| Tool | Version | Source | Why this one |
|---|---|---|---|
| Eclipse Temurin JDK | 25.0.4+7 | github.com/adoptium | pt2matsim 26.6's pom sets `<release>25</release>`; a 21 JDK will not load it |
| pt2matsim | 26.6 (shaded jar) | repo.matsim.org | bundles MATSim and declares `PublicTransitMapper` as Main-Class, so no Maven and no build step |
| Eclipse SUMO | 1.27.1 | PyPI `eclipse-sumo` wheel | SUMO publishes no GitHub release assets; the wheel is the only pinnable Windows distribution |

A toolchain change is a model change: re-run, re-hash, and log it in §14. Two
domains were added to `sandbox.network.allowedDomains` for these
(`repo.matsim.org`, `pypi.org`/`files.pythonhosted.org`).

**Known tool defect.** `netconvert --osm.crossings` segfaults (exit 139) on this
extract in SUMO 1.27.1, reproducibly and on its own. Crossings and sidewalks are
therefore not imported into the SUMO corridor. Pedestrians are modelled in MATSim
on the A6 active-transport network, and the crossing inventory itself is
unaffected — it lives in `A2_crossings_osm.csv`.

---

## 4. Light rail vehicle and dwell (A4) — the highest-leverage assumptions

### 4.1 Vehicle

Published: CAF Urbos 100, 5 modules, **32.966 m**, **45 t**, 750 V DC overhead
in depot only, **ACR supercapacitor charging at each stop**, fleet of 6
(2151–2156), maximum capacity 270.

Assumed (class-typical for a 33 m 100% low-floor Urbos):

| Field | Value | Basis |
|---|---|---|
| `capacity_seated` | 60 | crush 270 published; seated/standing split assumed |
| `max_accel_ms2` | 1.2 | typical LRV service acceleration |
| `max_decel_ms2` | 1.3 | typical service braking |
| `line_speed_kmh` | 40 | on-street CBD running |
| `door_count_per_side` | 4 | Urbos 5-module typical |
| `door_width_mm` | 1300 | double-leaf |
| `boarding_rate_pax_s` | 0.6 | per door-stream |
| `alighting_rate_pax_s` | 0.8 | per door-stream |

### 4.2 Run-time decomposition — how the residual was derived

Rather than guess a dwell figure, the schedule was decomposed against vehicle
physics on the true alignment (2,729 m from the GTFS shape):

```
scheduled end-to-end        720.0 s   (12.00 min, both directions)
kinematic minimum           290.1 s   (trapezoidal accel/decel at 40 km/h)
------------------------------------
residual to explain         429.9 s
   of which dwell           112.0 s   (4 intermediate stops x (8 s + 20 s))
   signals and recovery     317.9 s   (~26 s per corridor intersection, n=14)
```

This makes every term inspectable and independently toggleable, which is what
scenarios S2a and S2b require.

### 4.3 `dwell_charging_s` — **assumed 20 s, sweep 10–35 s**

Not published anywhere. The proposal's own working estimate is ~20 s at each
stop. Adopted as the base value, as a **separate additive term** so it can be
switched off (S2a) without touching boarding dwell.

**A correction to the proposal's arithmetic.** §6.2 reasons "twenty seconds at
each of six stops … approximately two minutes on a ten-minute run: a run-time
penalty of around twenty per cent." Only **four** of the six stops are
intermediate; both termini charge during layover, which does not enter run time.
The correct figure is 4 × 20 s = **80 s on a 720 s run = 11.1%**, not ~20%.
Still large, still attributable entirely to a late amenity decision, but the
published claim should use 11%.

Sweep across 10 / 20 / 35 s changes end-to-end run time by ±5.6%, which is
carried into mode choice through the outer loop.

**Acquisition route:** field measurement at Civic or Crown Street (a few hours of
observation), or inference from GTFS-Realtime dwell distributions. Until then
this remains the single largest assumed number in the model.

### 4.4 Dwell — other terms

`dwell_fixed_s` = 8 s (sweep 5–12), door open/close plus driver reaction.
`dwell_sd_s` = 6 s, lognormal. Terminus layover 180 s. All **assumed**.

---

## 5. Signal control (A2) — the SCATS proxy

SCATS phase data was not obtained. The corridor inventory is constructed from
OSM: 1,265 signal nodes state-wide in the extract, of which those within 60 m of
the light rail alignment cluster (45 m radius, per-approach nodes merged) into
**14 intersections** on Hunter/Scott Street.

Assumed for every corridor intersection:

| Field | Value | Sweep |
|---|---|---|
| `control_type` | `adaptive` | — (SCATS is adaptive by definition) |
| `cycle_time_s` | 110 | 80–140 |
| `n_phases` | 4 | — |
| `phase_split_pct` | 45 \| 15 \| 30 \| 10 | — |
| `ped_clearance_s` | 8 | — |
| `tsp_enabled` (S2) | **0** | — |
| `mean_delay_to_tram_s` | 24.75 | follows cycle sweep |

**This is the assumption that most drives the headline result**, exactly as the
proposal warned. It is stated prominently, swept, and the S2b variant quantifies
the upper bound: full TSP (green extension + early start, 120 m detection, 12 s
maximum extension, 75% of tram signal delay removed) cuts end-to-end run time
from **12.00 to 7.45 minutes — a 38% reduction**.

That number is the argument for requesting SCATS data. It is also the reason no
run-time-dependent finding may be published as a point estimate.

#### The other three signal variants (added in P2)

`scenarios/E1_scenarios.csv` references **five** `signal_variant_ref` values;
`A2_signal_control_corridor.csv` contained two. The three scenarios pointing at
the missing ones had no signal layer at all. All three are now built, over the
same 14 intersections, and all three are **assumed**:

| Variant | Cycle | TSP | Tram delay | Basis |
|---|---:|---:|---:|---|
| `S0_no_tram` | **100 s** | 0 | **0 s** | E1 sets 100 s for the full-capacity network; there is no tram to delay |
| `S2c_reserved_alignment` | 110 s | 0 | **9.9 s** | the reserved alignment removes 60% of at-grade signal conflict (§10), so 0.40 × 24.75 |
| `S3_brt_priority` | 110 s | 1 | 6.2 s | BRT is given the *same* priority mechanism as S2b, so S2b and S3 differ in vehicle and dwell rather than in how generously each is signalled |

All three sweep on the same 80–140 s cycle range as S2. Giving BRT the same
priority as the tram is a deliberate choice against the light rail's favour: the
alternative — modelling BRT with priority the tram lacks — would let the signal
assumption decide the S2-versus-S3 comparison.

#### How the assumed timings reach SUMO

`netconvert` derives each junction's **phase structure** from its geometry. That
structure is kept; only the **durations** are replaced, distributing the A2 split
across the green phases and giving each intervening yellow/all-red phase the A2
pedestrian clearance. Structure and timing are never blended, and every emitted
program carries both provenances as parameters (`phase_structure_source`,
`timing_source`). All 14 A2 intersections match a signalised junction in every
variant, and the realised cycle lands within 1 s of the A2 value.


---

## 6. Parking (A5)

7,710 facilities from OSM; 4,861 carried a capacity tag, 2,849 were imputed by
type (on-street 12, off-street public 60, off-street private 40 spaces).

Price, maximum stay and hourly occupancy are **entirely assumed** — City of
Newcastle publishes neither meter transactions nor occupancy. Four zones:

| Zone | AUD/hr | Max stay | Peak occupancy | Facilities | Spaces |
|---|---:|---:|---:|---:|---:|
| CBD core | 3.20 | 120 min | 0.94 | 203 | 7,069 |
| CBD fringe | 2.40 | 180 min | 0.88 | 465 | 3,584 |
| Honeysuckle | 2.40 | 240 min | 0.86 | — | — |
| Beach / east | 2.00 | 240 min | 0.85 | 4 | 240 |
| Outer | free | — | 0.73 | 7,038 | 157,018 |

Price sweep ±50%. Occupancy profiles are 24-hour vectors, weekday shaped.

Corridor kerbside removal is modelled as a scenario variant, not a constant:
`park_2026` removes **210 on-street spaces** on the corridor (assumed);
`park_2026_pre_lr` retains them. Scenarios without a tram use the latter.

---

## 7. Land use (D1)

**Frontage segments.** 498 segments of 50 m across seven streets — Hunter and
Scott (corridor), Darby, King, Beaumont (off-corridor comparators), Honeysuckle
Drive and Wharf Road (waterfront). This set supports hypothesis B4 (generation
vs displacement) directly.

**Retail floorspace is modelled, not observed.** No frontage-level floorspace
data exists for Newcastle. Estimated as:

```
retail_floorspace_m2 = GFA_within_30m x 0.35 x (retail+food POI share of all POI)
```

where `GFA = building footprint x levels` and levels default by building type
when untagged. Yields 51,843 m² on Hunter St, 33,812 m² on Scott St,
16,444 m² on Darby St. The 0.35 ground-floor coefficient is **assumed**.
**Action:** field audit of the corridor replaces this (proposal §7.2 fallback).

`vacancy_rate` and `awning_coverage_pct` are **empty** — flagged
`not_available` rather than invented. Both are in the B1 metric set and both
require the field audit.

**Jobs.** The 2021 Working Population Profile is not published at Destination
Zone geography (confirmed: no WPP/DZN DataPack exists). Jobs are therefore taken
from **WPP at POW SA2** and disaggregated to SA1 in proportion to a
workplace-weighted POI index (office 12, civic 15, food 6, health 8, retail 4,
leisure 2, amenity 1 jobs per establishment — **assumed**), falling back to
population share where an SA2 contains no mapped POI. The SA2 control total is
preserved exactly: 296,471 modelled against 296,474 published. Flagged
`jobs_source = modelled_from_WPP_SA2`.

**POI attraction weights** (retail 1.0, food 1.2, civic 1.5, office 0.8,
tourism 1.1, leisure 0.9, health 1.0, amenity 0.4, landuse 0.1) are **assumed**
and feed both destination choice and frontage throughput.

---

## 8. Behavioural parameters (C1) — "this layer decides the answer"

30 parameter sets (5 segments × 6 purposes). Full table in
`params/C1_behavioural_parameters.csv`; sweep grid of 140 points in
`params/C1_sensitivity_sweep_grid.csv`.

### 8.1 `beta_transfer_penalty_min` — **assumed 8.0 min, sweep 3–15**

The parameter the policy question turns on. The proposal is explicit that
literature defaults must not be used and that every finding must be reported as
a curve. Implemented: the sweep grid crosses transfer penalty
{3, 5, 6.5, 8, 10, 12, 15} with walk decay and charging dwell, and **no headline
figure may be reported at a single value**.

Physical anchor now available: the Newcastle Interchange transfer table gives a
**mean 112 s and maximum 284 s** walk-plus-crossing time across 51 stop pairs
(35 of them cross-modal). The behavioural penalty sits *on top of* that measured
time.

**Estimation route:** NSW HTS interchange rates plus Opal tap sequencing at the
Interchange. Journey-linked Opal would settle it; the §7.2 fallback (tap-on /
tap-off timing plus a matching model) is the plan of record.

### 8.2 Walk access decay — **assumed negative exponential, β = 0.0018 /m**

Sweep 0.0010–0.0030. Weight 0.49 at 400 m, 0.24 at 800 m, 0.12 at 1,200 m;
considered to 2,500 m. A cumulative-Gaussian alternative (μ = 700 m, σ = 420 m)
is provided. **No 400 m threshold is used anywhere**, per §6.3.

### 8.3 Value of travel time — `literature`

2026 AUD/hr: commute 18.60, education 9.30, shopping/other 15.20, employer's
business 55.40. ATAP PV2 / TfNSW Economic Parameter Values conventions.
Sweep ±30%. Concession, student and car-unavailable segments take 0.75×.

### 8.4 Time weights

`beta_walk_access` / `_egress` 2.0 (1.5–2.5), `beta_wait` 2.0 (1.5–2.5),
`beta_headway` 0.5 (0.35–0.65), `beta_reliability` 1.3 (0.8–1.8),
crowding 1.00 seated / 1.45 standing. All `literature`.
Gradient penalties — uphill 0.09, downhill 0.02 per % grade — are **assumed**.

### 8.5 Alternative-specific constants — **assumed priors, must not be freely calibrated**

Relative to car driver = 0: car passenger −0.85, bus −1.05, light rail −0.75,
rail −0.65, walk +0.35, cycle −1.35.

**These are priors for the first calibration pass only.** Proposal §9 identifies
ASC absorption as the primary threat to validity: calibrating mode constants to
observed 2019 patronage would fit away the very effect under test. The rule
adopted is: **estimate ASCs on the pre-intervention period (era 3, 2018) and hold
them fixed across all scenarios**, or constrain them and report the constraint.
Any departure from this must be logged here before results are seen.

### 8.6 Nesting

Nested logit; PT nest {bus, lr, rail} coefficient 0.65, private 0.80,
active 0.70. **Assumed.**

---

## 9. Synthetic population and demand (B1, B2)

### 9.1 B1 — persons and households

**612,668 persons in 245,738 households.** Seed 20260810, deterministic.
Fitted to census marginals per SA1 — household size (G35), vehicles (G34),
dwelling structure (G36), age–sex (G04), labour force (G43/G46), income (G17),
occupation (G60). Validation of the fit:

| Statistic | Census | Synthetic |
|---|---:|---:|
| Mean household size | 2.49 (implied) | 2.493 |
| Zero-vehicle households | 5.71% | 5.95% |
| Mean vehicles per household | 1.818 | 1.806 |
| Employed as share of persons | ~50% | 50.4% |

Assumed elements: **licence holding by age band** (0.62 at 18–24 rising to 0.94
at 45–54, falling to 0.45 at 85+), NSW-typical; **home coordinates** jittered
within the SA1 at 0.6 × the equivalent-circle radius.

> **P3 note.** `build_population.py` no longer generates chains, so it no longer
> draws random numbers for them, and the person/household draw moved slightly:
> 612,680 → 612,668 persons, 246,022 → 245,738 households. Every fit statistic
> above is unchanged to within 0.02 pp. The file is a different sample of the
> same distribution, not a different distribution.

### 9.2 B2 — activity chains (rebuilt at P3)

The P1 chains were **not usable as MATSim plans**. Measured on the delivered
file before replacing it:

| Defect | Measured |
|---|---|
| Destinations were zone centroids | 1,452,065 activity legs landed on **1,481 distinct coordinates**; one centroid took **158,431 legs (10.9%)** |
| Chains were not tours | activities were shuffled and chained without returning home, so **684,125 legs (47%)** had a home-based purpose but did not start at home |
| Purposes were wrong | **all 568,631** closing legs were labelled NHB, making 70% of "NHB" simply going home |
| One subtour per agent | every day was a single home→…→home loop, so MATSim's `SubtourModeChoice` would fix one chain-based mode for the whole day |
| The day did not close | 1.77% of arrivals fell past 24 h, the latest at **36.0 h** |
| One generic day | though the schedules carry WEEKDAY/SAT/SUN |

`src/build/build_activity_chains.py` replaces them with home-anchored **tours**,
one file per day type. Realised over 612,668 persons:

| | WEEKDAY | SAT | SUN |
|---|---:|---:|---:|
| Legs | 2,177,684 | 1,991,493 | 1,688,002 |
| Tours | 970,065 | 887,526 | 751,564 |
| Legs per person | 3.554 | 3.251 | 2.755 |
| Persons with more than one tour | 56.7% | 56.2% | 49.9% |

Structural properties, verified on the full output: **100%** of tours close at
home; **zero** return-home legs are labelled NHB; **zero** legs arrive after the
30 h horizon; non-home destinations occupy **76,278** distinct coordinates on a
weekday and the busiest single coordinate takes **0.65%** of legs, against 10.9%
before. **95.5%** of activity ends are placed on an observed POI or CBD building
footprint; 4.5% fall back to a jittered point in zones that have neither.

The realised week trip rate is **3.397** against the HTS **3.473** (−2.2%; P1
was −5%). The residual is tours dropped for not fitting inside the day.

#### Assumed values introduced here

**Measured from Newcastle data** (`src/build/measure_network_factors.py` →
[`params/C2_network_factors.json`](../params/C2_network_factors.json)). Each of
these was a typed-in constant until P3:

| Value | Measured | Source | Was |
|---|---|---|---|
| `DETOUR_FACTOR` (straight-line → network) | **1.3376**, sweep 1.25–1.42 | Shortest path over the observed A1 road graph, 551 population-weighted zone pairs routed. Aggregate ratio of summed network to summed straight-line distance — the mean of per-pair ratios (1.43) is pulled up by short circuitous trips and would overstate the correction for the long trips that dominate a distance mean. | assumed 1.30 |
| Weekday vs weekend travel | **0.7521**, sweep 0.709–0.816 | RMS traffic counts, which publish a `WEEKDAYS` and a `WEEKENDS` figure per station-year — 551 station-years. | assumed (implied 0.825) |
| Lower bound on work attendance | **0.6508** | Census G62: of employed residents, the share who travelled to work on census night. | no bound |

**Still assumed, each now with a sweep range:**

| Value | Assumed | Sweep | Why it is not observed |
|---|---|---|---|
| Saturday : Sunday split *within* the weekend | 1.1875 | 1.00–1.45 | The traffic counts report one `WEEKENDS` figure and do not separate the two days. This is the only part of the day-type shape still assumed — the weekday/weekend ratio itself is measured. |
| Day-type purpose mix | commute and education collapse at the weekend, shopping and social rise | ±30% on each multiplier | The HTS carries no day-of-week dimension — confirmed in the raw workbook, whose only dimensions are financial year, LGA, mode and purpose. Renormalised against the HTS purpose share so it redistributes rather than inflates. |
| `P_MANDATORY` (work / education tour made on a given day) | 0.78 / 0.85 weekday | **0.65**–0.90 / 0.70–0.95 | The lower bound is now observed: census G62 says 65.1% of employed residents travelled to work on census night. It cannot set the *value* — that night was August 2021 with 19.2% working from home, so it carries the lockdown with it, and §2.4 already rules G62 out as a behavioural rate. It bounds the sweep from below instead. |
| `P_INTERMEDIATE_STOP` by purpose | 0.12–0.30 | 0.10–0.35 | Trip chaining rates are not in the published HTS tables. **This parameter decides how many sub-tours exist, and therefore how freely MATSim's mode choice can vary within a day.** |
| `P_SECOND_STOP` | 0.25 | 0.12–0.40 | Same reason. |
| `CHILD_TOUR_RETENTION` | 0.4 | 0.25–0.60 | Share of an under-12's secondary tours made independently. |
| `EXTERNAL_INTERACTION_RATE` | 0.08 | 0.04–0.15 | Share of external-tier residents entering the core on a weekday. **This one is not derivable from the package as it stands**: the census place-of-work tables (W01A…) give jobs *by* SA2 but there is no journey-to-work origin-destination table (SA2 usual residence × SA2 place of work), which is what would settle it. Added to §13. |
| Activity durations, departure profiles | carried from P1 | ±25% on each mean; ±30% lognormal within | Not Newcastle-specific in any observable sense. |

#### Destination choice is now tied to the HTS, not set by hand

P1 set the gravity decay to `1/mean-distance` directly, which left education and
shopping **60% too long** and work-related business **22% too short**. The decay
is now solved per purpose by bisection so the model's own expected journey
distance equals the HTS figure. Realised against target, all six purposes:

| Purpose | HTS network km | Model network km |
|---|---:|---:|
| HW | 17.76 | 17.76 |
| HE | 6.44 | 6.44 |
| HS | 7.13 | 7.13 |
| HO | 10.16 | 10.16 |
| WB | 23.02 | 23.02 |
| NHB | 7.84 | 7.84 |

#### External boundary demand

B1 synthesises the 1,500 core SA1s only, so the 201 external SA1s — the boundary
tier that exists to carry Hunter Line through-demand (§1, scope decision 3) —
generated no travel at all, though their **70,448** residents are a ninth of the
core population. A boundary treatment now generates **5,384** weekday agents
(2,254 Saturday, 1,697 Sunday), each making one home-based tour into the core,
reaching 828 distinct core zones at a mean 59.8 km. This is a boundary
treatment, not a second population synthesis: freight, the Port and full
external synthesis stay out of scope (proposal §5).

**Known limitation, unchanged from P1.** The plans are *seed* plans: departure
times are initial conditions for MATSim's co-evolutionary scoring, not
predictions. Mode is deliberately **not** assigned in B2 — assigning it here
would pre-empt the question the model exists to answer.

## 9.3 MATSim plans and the C1 translation (P3)

`build_matsim_plans.py` turns B2 into `population_v6` plans, one file per day
type; `build_matsim_run_inputs.py` assembles a runnable scenario per
(scenario × day type). 521,502 weekday persons, 2,237,373 legs, 2,758,875
activities.

**Mode is seeded here, and only here.** B2 still carries no mode (§9.2), but a
MATSim plan cannot omit one. A mode is drawn **per tour**, so a car that leaves
home comes home again and `SubtourModeChoice`'s mass conservation holds from
iteration 0. This only works because the P3 chains have several tours a day —
under the P1 chains every agent had exactly one subtour, so a per-tour draw
would have fixed one mode for the whole day.

| | Seeded | HTS 2024/25 |
|---|---:|---:|
| car | 55.7% | 57.5% |
| ride (car passenger) | 18.6% | 21.5% |
| walk | 19.3% | 16.1% |
| pt | 4.0% | 3.4% |
| bike / other | 2.4% | 1.6% |

The seed is set near the HTS aggregate because starting iteration 0 far from the
observed point wastes iterations without changing where the model converges.
**Seeding near HTS is not matching it** — mode share is a P4 calibration target
(§2.4), and this is the initial condition the calibration starts from. Assumed,
swept: car share among car-available 0.68–0.86, PT share among car-unavailable
0.05–0.20.

### What does not survive the C1 → MATSim translation

C1 is a nested-logit specification; MATSim scores with a Charypar–Nagel utility.
Three things have no representation and are recorded rather than dropped
quietly:

| C1 element | Fate |
|---|---|
| `nesting_coefficient_pt = 0.65` and the nest structure | **Not representable.** MATSim's mode choice is a co-evolutionary search, not a closed-form nested logit; there is nowhere to put a nest coefficient. |
| Per-purpose value of time (commute 18.6, work-business 55.4 AUD/h) | **Collapsed** to a trip-weighted **16.96 AUD/h**, because MATSim scores per mode, not per purpose. A scenario that shifts the purpose mix will not shift the value of time with it. |
| `beta_crowding_seated` / `_standing` | **Not enabled.** Capacity-dependent PT scoring needs an explicit extension. |

The identity used is the conventional
`VOT = (performing − traveling_mode) / marginalUtilityOfMoney`, with
`performing = 6.0` utils/h (assumed; the whole scoring scale is relative to it)
and `marginalUtilityOfMoney = 1.0` utils/AUD as the definitional anchor.
`utilityOfLineSwitch` carries the swept transfer penalty (§8.1).

### The one-build constraint, discharged structurally

Every feed's mapped schedule carries all three day types at once — S2 has 1,714
routes, 1,231 WEEKDAY + 291 SAT + 192 SUN, and 4,269 departures against 2,188
weekday GTFS trips. **Running an unfiltered schedule would put roughly twice the
real PT supply on the network.** The day-type filter therefore operates on the
*already mapped* schedule, selecting `transitRoute` ids by their day-type token.
Verified on S2: all **1,714** route link sequences byte-identical to the source,
the stop→link map for all **4,174** facilities unchanged, and the three day types
partition the route set exactly. No feed is ever re-mapped, so §3.5's constraint
holds by construction rather than by discipline.

**The run network is not `networks/matsim/variants/`.** Those are patched over
the *base* network, which has no mapped transit links, so they are a reference
artefact and not runnable. A scenario runs on its own mapped
`schedules/<S>/network.xml.gz` — 151,594 links against the base 157,678, with
928 artificial transit links added and 7,012 pre-mapping rail placeholders
removed, **all of them pt-mode; no car link is lost**. The E1 road variant is
re-applied on top by `osm:way:id`, which every link carries, and reproduces the
base build's patch counts exactly (54 lanes / 59 kerbside / 8 banned turns for
the full-capacity variant).

#### Three defects this stage caught

1. **The day-type token is not always dot-delimited.** The era and scenario
   feeds namespace it `nisc001:WEEKDAY.2302960`, but the S1 shuttle and S3 BRT
   that `build_scenario_schedules.py` generates use `S1SHUTTLE_WEEKDAY_0_1`.
   Matching only the dotted form dropped both from *every* day type — which
   would have run **S1 with no shuttle and S3 with no BRT**, each scenario
   without the intervention it exists to test. Caught by a package check
   asserting that the split partitions the mapped schedule exactly.
2. **Banned-turn removal was network-wide.** E1's "no banned turns" applies to
   the corridor without the tram; a first cut stripped `disallowedNextLinks`
   from the whole network, deleting **1,235** observed restrictions instead of
   **8**, and quietly handing four scenarios a freer road network.
3. **`gzip.open` writes the wall clock into the gzip header**, so two builds of
   identical content produced different bytes and different manifest digests -
   a direct breach of the determinism rule, and one that would have made every
   rebuild look like a data change. `src/build/det_io.py` pins the header mtime
   to 0; a repeat build of the plans and all 30 run-input sets is now
   byte-identical.

### Assumed values introduced here

**None of these is Newcastle-specific** — they are properties of MATSim's
scoring and replanning formulation, not observable quantities of this study
area, so there is nothing local to derive them from. All are swept.

| Value | Assumed | Sweep | Why |
|---|---|---|---|
| Seed mode split | see table above | car 0.68–0.86, PT 0.05–0.20 | Initial condition for co-evolution; P4 moves it. The *blend* is positioned against the observed HTS mode share. |
| `performing` | 6.0 utils/h | 4.0–8.0 | Conventional MATSim value; the whole scoring scale is relative to it. |
| `monetaryDistanceRate` car | −0.00018 AUD/m | −0.00025 to −0.00012 | Fuel and tyres only, not standing costs: a mode choice within the day does not re-decide car ownership. Varies with national fuel prices, not with Newcastle. |
| Typical activity durations | home 12 h, work 8 h, education 6 h, shopping 1 h, other 2 h, business 1 h | ±25% | MATSim scoring needs a typical duration per activity type. |
| `SubtourModeChoice` weight | 0.10 | 0.05–0.20 | The replanning weight that governs how far the co-evolution can move mode share. Innovation is switched off for the last 20% of iterations. |

## 9.4 The assembled run inputs did not load (P4 stage 0)

P3 delivered 30 scenario × day-type input sets and verified them thoroughly *as
data*: the day-type split partitions the mapped schedule exactly, all 1,714 route
link sequences are byte-identical to source, the stop→link map is unchanged, no
stop dangles, and the E1 patch reproduces the base build's counts. Every one of
those statements is true. **None of the 30 sets could be loaded by MATSim**, and
no check noticed, because every check treated the artefacts as tables to be
audited rather than as files a simulator has to read.

Found by launching one, not by re-reading the code. Three independent defects:

| # | Defect | Reach | Symptom |
|---|---|---|---|
| 1 | The day-type filter round-trips the schedule through `ElementTree`, which **drops the doctype** | **all 30** schedules | MATSim selects its reader *from* the doctype; without it the parse fails at line 2 with a null-delegate `SAXParseException` |
| 2 | Dropping two thirds of the routes **orphans the stop facilities and `minimalTransferTimes` relations only they used** — 113 facilities and 42 relations on S2/WEEKDAY, 2,193 and 1,034 on S0/SAT | **all 30** schedules | `SwissRailRaptorData.calculateRouteStopTransfers` dereferences a null array. The schedule stayed *smaller* but stopped being *referentially closed* |
| 3 | The kerbside patch appends a **second `<attributes>` block** to links that already have one — and every mapped link has one, since `osm:way:id` is how the patch finds it | **6 of 10** run networks: S0, S1, S2c 59 links each, S4 302, S5 498, S6 59 | `More than one instance of element <attributes>`; the network DTD rejects it. S2/S2a/S2b/S3 escaped only because `net_base2026` is the observed network and carries no patch rows |

Defect 3 is the one that would have been hardest to catch late: it strikes
exactly the six scenarios that carry an E1 road change, i.e. every counterfactual
that the corridor comparison depends on, and leaves the four that don't alone.

**Fixed** in `build_matsim_run_inputs.py`: the doctype is written back
explicitly, the filter prunes facilities and transfer relations down to what the
surviving routes serve, and `set_link_attribute()` writes into a link's existing
`<attributes>` block instead of adding another. The 30 sets rebuild
byte-identically, the patch counts are unchanged (54 lanes / 59 kerbside /
8 banned turns on the full-capacity variant), and all 30 now load and run in
MATSim. `check_package.py` 556 → **657 checks**: doctype, orphaned facilities,
dangling transfer relations and duplicate `<attributes>` are now asserted for
every one of the 30 sets.

**The lesson worth keeping:** "the artefact is internally consistent" and "the
tool can read the artefact" are different claims, and P3 only tested the first.
Nothing here changes a modelled value, a target or a falsification condition.

## 9.5 What a run costs on one workstation — measured

Measured, not estimated: S2 × WEEKDAY, nested deterministic subsamples (1% ⊂ 10%
⊂ 25%, blake2b on person id, seed 20260810), 16 threads, `ride` teleported,
peak working set sampled every 2 s. **24 cores, 63.5 GiB, no useful GPU** —
MATSim will not touch one. The probe was driven by a throwaway script; the
committed harness that reproduces these numbers lands with `src/run/`, which is
still empty.

| Sample | Persons | Iteration 0 | Steady per-iteration | Peak resident |
|---|---:|---:|---:|---:|
| 1% | 5,209 | 13.2 s | **9.8 s** | 9.8 GiB |
| 10% | 52,758 | 43.4 s | **29.9 s** | 18.4 GiB |
| 25% | 131,291 | 112.2 s | **~64 s** | 31.5 GiB |

Both curves are close to linear in the sample fraction with a large fixed cost —
the run network (**151,592 links / 70,146 nodes** for S2, of which 143,891 carry
car and ride) and the raptor transfer table (**970,047 entries** for S2/WEEKDAY)
are paid once regardless of how many agents exist:

- time ≈ **3.1 s + 268 s × fraction** per iteration → **~4.5 min/iteration at 100%**
- memory ≈ **9.6 GiB + 87 GiB × fraction** → **~97 GiB at 100%**

**A 100% weekday run does not fit in 63.5 GiB.** The practical ceiling on this
machine is about **40%** (≈45 GiB), and 25% is the largest fraction that leaves
room to do anything else. Demand is built at 100% so this stays a run-time
choice (§9.2), and this is that choice being made on measurement.

Consequence for the load recorded in `STATUS.md`: 1,400 sweep runs + 300
headline runs, each of which is really three day types, is 5,100 run-days. At
25% that is ~3.6 h each — **about 765 days of wall clock**. The shortfall is
roughly three orders of magnitude, so it is not closeable by tuning; it is
closeable only by cutting sweep breadth, replications and day types. Sample
fraction is the *weakest* of the available levers, because cost is sublinear in
it and precision is not.

## 9.6 Mode choice was not choosing, and the seed is now uninformed (P4 stage 0)

Three things about the shipped configuration only became visible by running it.

**Defect 4: `ride` was declared a network mode that no link permitted.** The
config set `qsim.mainMode=car,ride` and `routing.networkModes=car,ride`, but the
mapped network permits `car`, never `ride`. MATSim reports
`checking 0 nodes and 0 links for dead-ends` for mode `ride` and then throws in
`PrepareForSim`. **The shipped config could not run even after §9.4's three
schedule and network defects were fixed** — this is the fourth, and it lived in
the config rather than in the data, which is why the load test in §9.4 did not
see it: that test overrode the mode handling in order to exercise the artefacts.

**Defect 5: `ride` was not in MATSim's choice set, so its share was an output
equal to its seed.** `subtourModeChoice` was never configured, so MATSim's
default applied: `modes=car,pt,bike,walk` with
`behavior=fromSpecifiedModesToSpecifiedModes`. A subtour whose mode is `ride` is
not in the specified set, so it is never offered an alternative — an absorbing
state. Measured over 30 iterations at 1%, `ride` sat at **0.18311 in every single
iteration**, to five decimal places. **18.6% of legs were an input wearing the
costume of a result**, and the HTS vehicle-passenger target (20.6%) could only
ever have been "met" by whatever the seed happened to be.

**Defect 6: car availability was ignored.** `considerCarAvailability` defaults to
`false`, so an agent B1 records as having no car could be assigned one by mode
choice. B1 synthesises car availability and the seed was drawn conditional on it;
the choice model then discarded the structure.

### What changed

| | Was | Now |
|---|---|---|
| `qsim.mainMode` | `car,ride` | **`car`** — a car passenger is not a second vehicle |
| Link `modes` | `car` | **`car,ride`** on 143,891 links, so `ride` is *routed* on the road network and gets a congested travel time rather than a beeline guess |
| `travelTimeCalculator` | default (per-mode) | **`separateModes=false`, `analyzedModes=car`** — no ride vehicle is ever observed, so ride reads the car travel times instead of falling back to free speed |
| `subtourModeChoice.modes` | default `car,pt,bike,walk` | **`car,ride,pt,bike,walk`** |
| `subtourModeChoice.considerCarAvailability` | default `false` | **`true`** |
| Seed mode split | positioned near the HTS aggregate | **uninformed**, uniform over the modes each person can use |

Verified: the shipped config now runs unmodified, the ride subnetwork has 143,891
links, and `ride` moves — 0.1941 → 0.1975 → 0.1983 → 0.2048 over the first four
iterations, where before it did not move at all.

**Ride occupies no road capacity.** It is routed but teleported, so a car
passenger adds no vehicle. That is right when the driver is separately modelled
and wrong when they are not, and B2 does not generate escort trips, so modelled
link volumes are biased *low* against an observed all-vehicle count. Together
with the freight the model omits, this is why the traffic-count comparison
carries explicit corrections (§12.2a) rather than a fitted constant.

### The seed is now uninformed

The P3 seed was positioned so the blended share landed near the HTS aggregate
(car 55.7 against 57.5, pt 4.0 against 3.4), on the reasonable ground that
starting far from the observed point wastes iterations. That is a fine
convergence aid and a poor initial condition for a calibration whose target *is*
the HTS mode share.

The seed is now **uniform over the modes each person can use**, conditioned only
on B1 car availability — a population attribute, not a behavioural prior.
Realised: car **14.3%**, and about 21.4% each for bike, pt, ride and walk,
against an HTS car share of 59%. It is deliberately a bad guess.

| | Uninformed (default) | Informed (P3, retained) |
|---|---:|---:|
| car | 14.3% | 55.7% |
| ride | 21.4% | 18.5% |
| walk | 21.4% | 19.3% |
| pt | 21.5% | 4.0% |
| bike | 21.4% | 2.5% |

The informed seed is **kept**, selectable with
`build_matsim_plans.py --seed-mode informed`, so that "the answer does not depend
on the initial condition" is a claim that can be **tested by running both** rather
than asserted. §9.7 reports that test.

## 9.7 The seed test, and a model that does not converge (P4 stage 0)

Two 1% runs of 250 iterations, S2 × WEEKDAY, identical in every respect except
the initial mode draw. 2,205 s and 2,419 s wall, run concurrently.

| Iteration | Uninformed car / ride | Informed car / ride |
|---:|---|---|
| 0 | 0.143 / 0.223 | 0.564 / 0.183 |
| 50 | 0.182 / 0.401 | 0.374 / 0.375 |
| 100 | 0.178 / 0.508 | 0.291 / 0.491 |
| 150 | 0.166 / 0.573 | 0.241 / 0.561 |
| 200 | 0.153 / 0.619 | 0.202 / 0.609 |
| **250** | **0.147 / 0.664** | **0.201 / 0.649** |

**Finding 1 — the seed's influence decays but has not vanished.** The two starts
differ by **42.1 pp** on car share; at iteration 250 they differ by **5.4 pp**
(ride 1.5 pp, pt 1.0 pp, walk 1.1 pp, bike 1.8 pp). So 87% of the initial gap
closes, and the remaining 5.4 pp cannot be attributed to the seed rather than to
finding 2. The defensible statement is **"the seed's influence decays strongly and
is not yet eliminated at 250 iterations"** — not "the seed does not matter".

**Finding 2 — the model has not converged, and is not close.** MATSim switched
innovation off at iteration 200 (`fractionOfIterationsToDisableInnovation=0.8`),
after which no new plans are created and agents only re-select among the five
they already hold. Ride share still moved **0.619 → 0.664** over those last 50
iterations. A system that keeps drifting after its search is switched off has not
relaxed. **`lastIteration=100` is not merely unvalidated; it is far too low, and
250 is also too low.** The default is left at 100 rather than replaced with
another number that cannot be justified, and `check_package.py` now emits a
standing warning to that effect on every run of the suite.

**Finding 3 — the attractor is wrong, and it is a specification problem.** Both
runs converge toward **ride ≈ 65%, car ≈ 15–20%**, against an HTS calibration
target of ride 20.6% and car 59.0%. In MATSim, `ride`:

* has **no driver-availability constraint** — nothing requires a driver to exist,
  so every agent can be a passenger simultaneously;
* is charged **half** the distance cost of car (−9e-05 against −0.00018 AUD/m),
  on a cost-sharing assumption nothing else in the model represents;
* consumes no road capacity, so it never congests itself.

Against all that, the only thing restraining it is `asc_car_passenger = −0.85`.
Findings 2 and 3 are probably the same fact: a mode that strictly dominates
drives the co-evolution toward a corner, and corner solutions relax slowly.

**This runs directly into §8.5.** Pulling ride from 65% to 20.6% by fitting
`asc_car_passenger` is exactly the ASC absorption proposal §9 names as the
primary threat to validity, and §8.5 forbids it without a departure logged
**before results are seen** — which is now. The candidates, and none is chosen
here:

1. **Charge `ride` the same distance cost as car.** A passenger's trip burns the
   same fuel; halving it models an intra-household transfer the rest of the model
   does not have. A specification fix that leaves the ASCs alone and keeps §8.5
   intact.
2. **Estimate the ASCs on era 3 (2018) and hold them fixed**, which is what §8.5
   actually prescribes and what has never been attempted. Note that era 3
   predates the light rail, so it cannot identify `asc_lr` at all.
3. **Calibrate `asc_car_passenger` freely**, logging the departure from §8.5 here
   first.

Nothing downstream of this should be built until it is settled, because the
choice determines what the calibration loop is allowed to move.

## 9.8 The ride constant is constrained to observed vehicle occupancy

§9.7 left three options open and none chosen. This is the resolution, and it is
the second branch §8.5 already permits — *"or constrain them and report the
constraint"* — with the constraining quantity measured rather than picked.

### The model produced a physically impossible car

At `asc_car_passenger = −0.85` the model settled at **4.52 ride legs per car
leg**: an implied **5.52 people per vehicle**. A car has about five seats. The
observed Newcastle figure, from the HTS vehicle driver and vehicle passenger trip
counts, is **1.3503** — and it is stable:

| Financial year | Driver trips | Passenger trips | Occupancy |
|---|---:|---:|---:|
| 2016/17 | 334,000 | 106,000 | 1.3174 |
| 2017/18 | 303,000 | 86,000 | 1.2838 |
| 2018/19 | 337,000 | 84,000 | 1.2493 |
| 2019/20 | 348,000 | 99,000 | 1.2845 |
| 2022/23 | 335,000 | 132,000 | 1.3940 |
| 2023/24 | 317,000 | 109,000 | 1.3438 |
| **2024/25** | 334,000 | 117,000 | **1.3503** |

Both quantities are ratios of two published counts. `src/calibrate/measure_mode_constraints.py`
derives them into [`params/C4_mode_constraints.json`](../params/C4_mode_constraints.json);
the sweep is **1.2493–1.3940**, the observed spread across all seven survey years
in the file, not an interval anyone chose.

### First, a double charge removed

`ride` was charged **half** the car distance rate — −9e-05 against −0.00018. That
half was typed in, not derived, and it double-counts: a vehicle's operating cost
is paid once, and at an occupancy of 1.35 charging both driver and passenger
makes the model's aggregate vehicle operating cost about 1.35× the real one. The
only value derivable from the data is **zero** — the driver, who is separately
modelled, already carries it.

This makes `ride` free at the margin, and that is the point: it moves the whole
burden of pinning ride's share onto one constant, in the open, instead of
splitting it between a constant and a cost share that was invented.

### Then the constant, solved against the observed ratio

`src/calibrate/solve_asc_ride.py` runs candidate values of `asc_car_passenger`
and interpolates on log(ride ÷ car legs) — the scale on which a logit constant
acts linearly — to the observed passenger:driver ratio of **0.3503**. It reads
`C4` and its own runs' `modestats.csv`; **it never opens the validation targets
at all**, so it cannot touch a holdout row even by accident.

### Why this is not ASC absorption

Proposal §9 names ASC absorption as the primary threat: *calibrating mode
constants to observed patronage fits away the effect under test*. The distinction
that makes this admissible:

* the constrained constant is **car passenger**. `asc_lr`, `asc_bus` and
  `asc_rail` stay at their §8.5 priors and are not touched;
* the constraining quantity is **vehicle occupancy** — how many people fit in a
  car — not light rail patronage, not PT mode share, not any quantity the
  hypotheses in proposal §3 turn on;
* it is a **physical** constraint. The unconstrained model was not merely fitting
  badly, it was putting 5.5 people in a car.

The solved value is reported as a constraint, never presented as an estimate of
Newcastle's taste for being a passenger, and both the value and the observed
range it was solved against travel with every result that uses it.

### What this does not fix

The solve is run at a fixed 250-iteration protocol, which §9.7 shows is **not
equilibrium**. It must be re-solved once the iteration count is settled, and the
value below is provisional until then. Whether constraining ride also cures the
non-convergence — the two are plausibly the same problem, since a dominating mode
drives the co-evolution to a corner and corners relax slowly — is measured by the
same runs.

## 9.9 The with-tram scenario had no tram on a weekday (P4 stage 1)

Found while building `src/analyse/extract_metrics.py`: the extractor reported
**zero light rail boardings** for S2 × WEEKDAY. Not few — zero.

`S2.zip` carries 550 light rail trips, of which **252 are weekday** on a
`service_id=WEEKDAY` running Monday to Friday. The mapping keeps all 550. But
the mapped schedule has exactly **two** light rail `transitRoute`s, named
`lightrail:SAT.69659…` and `lightrail:SUN.72626…`, and **each carries 275
departures: 74 Saturday, 75 Sunday and 126 weekday.**

**pt2matsim groups trips into a `transitRoute` by stop sequence, not by
service.** A route is therefore *not day-type homogeneous*, and the day-type
filter keyed on the **route id**. So:

* every weekday run dropped both light rail routes — the **with-tram scenario
  had no tram** — and a weekday S2-versus-S0 comparison would have measured the
  effect of nothing at all;
* Saturday and Sunday each received all 275 departures, roughly **3.7×** the
  real light rail service.

It is not confined to the light rail. Across S2's 1,714 routes:

| | |
|---|---:|
| Routes whose departures span more than one day type | **233 (13.6%)** |
| Departures placed in the wrong day type | **1,261 of 4,269 (29.5%)** |
| True weekday departures vs delivered | 2,139 vs **1,747** (18% short) |
| True Saturday vs delivered | 1,128 vs **1,330** (18% over) |
| True Sunday vs delivered | 1,002 vs **1,192** (19% over) |

### Why the existing check passed

§9.3 called the one-build constraint "discharged structurally" and
`check_package.py` asserted that the split **partitions the route set exactly** —
1,231 + 291 + 192 = 1,714. That was true, and it was the wrong invariant.
Partitioning routes is not partitioning service when a route is not
day-type homogeneous. The check confirmed an arithmetic identity while 29.5% of
the service was in the wrong place.

### The fix

`split_schedule` now filters **departures** by their own day token and keeps a
route if it retains any, so a route named after a Saturday trip still carries its
126 weekday departures into the weekday run. This still operates on the
already-mapped schedule — no feed is re-mapped, no link sequence is touched — so
§3.5 holds exactly as before.

Verified: light rail now has **252 weekday, 148 Saturday, 150 Sunday**
departures, matching the GTFS calendar exactly, and every scenario's departures
partition its source total precisely.

Two checks replace the one that passed:

1. the split partitions **departures** exactly, and every departure is kept in
   exactly one day type and dropped from the other two;
2. **the intervention is present with departures in every day type** — per
   scenario, the light rail line for S2/S2a/S2b/S2c/S4/S5, the shuttle for S1,
   the BRT for S3, and correctly nothing for the S0 and S6 counterfactuals. A
   generic partition count cannot see a missing tram; this can.

**Nothing that had been run on the old inputs was kept.** The three
`asc_car_passenger` candidate runs in flight were discarded rather than reported,
because a solve calibrated on a network with no weekday tram is a solve of a
different model.

---

## 9.10 Is the 1% sample representative? Partly — and the answer splits (P4 stage 2)

Every P4 behavioural result had been measured at **1%** — 5,209 people, 0.85% of
the population. Two runs, identical but for the sample fraction, 250 iterations,
8 threads, S2 × WEEKDAY, uninformed seed, shipped constants.

| Mode | 1% (5,209) | 10% (52,758) | difference | HTS target |
|---|---:|---:|---:|---:|
| car | 0.1223 | 0.1913 | **+6.91 pp** | 0.590 |
| ride | 0.7213 | 0.7190 | **−0.23 pp** | 0.206 |
| pt | 0.0395 | 0.0044 | **−3.51 pp (9×)** | 0.038 |
| walk | 0.0315 | 0.0123 | −1.93 pp | 0.134 |
| bike | 0.0854 | 0.0730 | −1.24 pp | 0.032 |

**1. Ride dominance is a property of the model, not of the sample.** The two
trajectories track within 0.006 at *every* checkpoint — 0.2228/0.2167 at
iteration 0, 0.4034/0.4011 at 50, 0.6208/0.6192 at 150, 0.7213/0.7190 at 250.
Ten times the population reproduces the same curve. **The §9.7 finding is
confirmed at scale and is a specification problem**: `ride` has no
driver-availability constraint, consumes no road capacity, and since §9.8
carries no distance cost either, so only `asc_car_passenger` restrains it. At
0.7213 against a 0.206 target it is 3.5× observed, and the model puts 5.9 people
in every car.

**2. Non-convergence is likewise a model property.** Innovation stops at
iteration 200. Between 200 and 250, with no new plans being created, `ride` rose
**+0.0461 at 1% and +0.0474 at 10%** — the same drift at both fractions. This is
not slow relaxation toward an equilibrium; it is a corner still being approached
when the run stops.

**3. But 1% is NOT representative for `car` or `pt`, and that invalidates a hope.**
Car differs by 6.91 pp and PT by a factor of nine. Any statement about car or PT
*levels* measured at 1% does not transfer, so calibration against the mode-share
targets cannot be done at 1%. The hope that sweeps could run cheaply at 1% and
only headline runs at 25% is therefore **not available for car or PT**, which is
a direct cost to the §9.5 budget problem.

**4. The mechanism for the car/PT divergence is NOT established, and is recorded
as open rather than guessed.** Two candidate explanations were checked and
neither survives:

- *Transit capacity.* The fleet is seats-only (`standingRoomInPersons=0`
  throughout) and seats scale with the fraction, flooring at 1 below ~1.5%
  (issue #12), so 1% carries ~43% more PT capacity per capita than proportional.
  But at 10% the timetable offers roughly **20× more boarding capacity than the
  model uses**, so capacity is not binding and cannot explain a nine-fold
  collapse.
- *Small-sample spillback.* Ruled out separately: MATSim enforces
  `storageCapacityFactor == flowCapacityFactor` (§15), and the storage floor
  gives 1% *more* link storage than proportional, which would make car more
  attractive at 1% — the opposite of the observed direction.

**An unreconciled vehicle capacity, found while checking the above.** The MATSim
fleet gives the light rail **180** seats and no standing room. §4.1 records the
CAF Urbos 100 with a **published maximum capacity of 270** and an assumed
`capacity_seated` of **60**. 180 reconciles with neither. Because the fleet has
no standing room, the C1 crowding multipliers (1.00 seated / 1.45 standing) can
never apply to any vehicle in any scenario.

**What this settles for sequencing.** The dominant distortion is a specification
error that scale does not cure. Calibrating, sweeping or coupling SUMO to a
demand model in which 72% of legs are car passengers would propagate that error
into every downstream number, so the specification comes first.

---

## 9.11 `ride` requires a driver — a logged departure under §8.5 (P4 stage 2)

§9.10 established that ride dominance is specification, not sampling. This is the
fix, and §8.5 requires it to be recorded **before results are seen**, which is now.

**What was wrong.** MATSim's standard treatment lets any agent be a car passenger
on any trip. Riding as a passenger should only be available when another agent is
driving the same trip at the same time; it is usually modelled without that
requirement and teleported. That is the field's default weakness, not a
misconfiguration here.

**What was rejected.** Solving `asc_car_passenger` harder. That is ASC absorption,
the primary threat to validity in proposal §9: the constant would be doing the job
the missing rule should do, and would misbehave the moment a scenario changes —
which is the entire experiment.

**What was implemented.** A per-person availability flag, DERIVED from B1: a person
may be a car passenger only if their household holds a vehicle **and** contains at
least one *other* licence holder. **22.1% of the weekday population (115,034 of
521,502) may not ride.** Two pieces were needed, and the first alone did nothing:

1. `src/java/citysim/RideAvailabilityModesCalculator.java` — core MATSim honours
   `carAvail` but has no equivalent for `ride`, and `subtourModeChoice.modes` is
   global, so a custom `PermissibleModesCalculator` is the smallest structural fix.
   Bound by `citysim.CitysimControler`.
2. **The seed had to be fixed too.** `PermissibleModesCalculator` governs only
   *new* mode choices — it never strips a mode from a plan an agent already holds.
   Seeding a person who cannot ride with `ride` leaves an illegal plan in memory
   that `ChangeExpBeta` re-selects indefinitely. Measured: **4,723 illegal ride
   legs survived 30 iterations** with the calculator alone. After seeding
   correctly: **0**.

| | before | after |
|---|---:|---:|
| Illegal ride legs at iteration 30 | 4,723 | **0** |
| Seed ride share | 0.2228 | 0.1712 |
| Ride at iteration 25 | 0.3098 | **0.2548** |

**Toolchain.** The pinned digests are UNCHANGED: this adds a compiled artefact
beside the shaded jar rather than replacing it. It builds from committed source
with the pinned javac 25.0.4 — no Maven — which is what makes it reproducible.

**This is necessary and probably not sufficient, and that is stated now rather
than discovered later.** The constraint lowers the ceiling to the 77.9% who may
ride; the unconstrained attractor was 0.72, so it does not bind hard at the
corner. Ride was still climbing at iteration 30 (0.2787). Whether it now settles
near the observed 0.206 is unmeasured and needs a converged run.

**Residual limitation, stated not hidden.** This makes ride available or not per
*person*. It does not bind a passenger to a specific driver at a specific time, so
the model can still produce more passengers than there are drivers in any given
hour. That is the socnetsim joint-plans contrib (Dubernet & Axhausen, STRC 2013;
Transportation 2015), which is **absent from the pinned jar** and out of scope.

---

## 9.12 The ride constraint is necessary and not sufficient, and 1% is unusable (P4 stage 3)

§9.11 predicted the constraint would not bind at the corner and asked for a
converged run to settle it. Two runs of S2 × WEEKDAY, 250 iterations, uninformed
seed, **8 threads** (matching the §9.10 baselines exactly — thread count is part
of the run identity), driven by committed overlays and the declared pipeline
`run_matsim.py` → `extract_metrics.py` → `fit.py`. **Neither is a result**: §9.7
shows 250 iterations is measurably short of relaxation.

| | 1% (5,209 persons) | 10% (52,758 persons) |
|---|---:|---:|
| wall / median iteration | 2,636 s / 9.94 s | 8,176 s / 27.76 s |

**Mode share, Newcastle LGA — the reportable quantity** (§12.1), not the
five-LGA aggregate the seed was positioned against:

| | 1% | **10%** | HTS target |
|---|---:|---:|---:|
| Vehicle driver | 16.01 | **30.85** | 59.0 |
| **Vehicle passenger** | 61.06 | **50.94** | **20.6** |
| Public transport | 0.62 | 0.99 | 3.8 |
| Walk only | 1.59 | 0.80 | 13.4 |
| Other | 20.73 | 16.43 | 3.2 |
| mean absolute error | 23.19 pp | **17.43 pp** | |
| passengers per driver | 3.8140 | **1.6512** | 0.3503, range [0.2493, 0.394] |

**The constraint did the largest single piece of work any P4 change has done, and
it is still not enough.** On the five-LGA quantity §9.10 measured, ride fell from
0.7213 / 0.7190 to 0.6105 / 0.5592 and car rose from 0.1223 / 0.1913 to
0.2057 / 0.2743. At 10%, ride still lands at **2.5× the observed 20.6%** and
vehicle occupancy at **4.7×** the observed passenger:driver ratio, outside the
seven-year observed spread. §9.11's own prediction is confirmed: the ceiling is
0.779 and the model settles far below it, so the constraint never binds where it
would matter.

### Confirmed at 25% — the 10% reading was real (added after the run landed)

The 25% confirmation run the §8.5 decision was gated on. 131,291 persons, 16,365 s
wall, 56.4 s median iteration, same 8 threads and same declared pipeline.

| Newcastle LGA | 1% | 10% | **25%** | HTS |
|---|---:|---:|---:|---:|
| Vehicle driver | 16.01 | 30.85 | **32.48** | 59.0 |
| **Vehicle passenger** | 61.06 | 50.94 | **49.87** | **20.6** |
| mean absolute error | 23.19 pp | 17.43 pp | **16.80 pp** | |
| passengers per driver | 3.814 | 1.651 | **1.535** | 0.3503 |

**The fraction sensitivity has flattened.** 1% → 10% moved car **+14.8 pp**; 10% →
25% moves it **+1.6 pp** and ride **−1.1 pp**. The divergence really was the 1%
artefact, and 10% already behaves like 25% — so the answer stands where the
artefact is absent: **ride settles near 50%, about 2.4× the observed 20.6%, at
1.535 passengers per driver against an observed 0.3503.** §9.11's constraint was
necessary and is not sufficient, and that is now measured rather than suspected.

The §9.13 constraint says the same thing independently and more sharply, because
it is geography-robust and is scored into nothing:

| ride ÷ car trip length | 1% | 10% | **25%** | observed |
|---|---:|---:|---:|---:|
| | 1.075 | 1.346 | **1.372** | **0.961** |

Observed passenger trips are slightly *shorter* than driver trips; the model makes
them 43% longer, and **the gap widens with sample fraction rather than closing**.

Counts, by contrast, do not move with fraction at all — −72.9% / −73.8% / −73.1%
— which points at §9.14 rather than at sampling.

### Why the 1% column must not be read behaviourally

**1% does not deliver the simulated day.** Counting `stuckAndAbort` in each run's
own events:

| | 1% | 10% |
|---|---:|---:|
| car legs aborted at the 30 h horizon | **1,032** | **4** |
| walk / pt / bike / ride aborted | 19 / 41 / 1 / 0 | 253 / 183 / 9 / 2 |
| PT passengers who boarded and never alighted | **380** | **0** |

Every abort at 1% occurs at exactly 108,000 s — `qsim.endTime` — so these are
agents still travelling when the day ends. A tenfold population increase makes
car non-completion fall **258-fold**, which is not proportional to demand.

The mechanism is **flow**-capacity granularity, a different quantity from the
storage argument §9.10 correctly ruled out. `RUN.sample.flow_capacity_factor` is
derived to equal the sample fraction, so at 1% an 1,800 veh/h link discharges
**18 veh/h — one vehicle every 200 s**, and two sampled cars arriving inside that
window queue behind pure arithmetic with no congestion present. At 10% the same
link releases one every 20 s. Storage and flow are pinned equal (§15), so this
cannot be separated by configuration, only by fraction — which is what these two
runs do. It is the first mechanism offered for the §9.10 car/PT divergence that
survives measurement, after four died, and it explains the direction too: a fifth
of car legs missing from the completed-trip denominator inflates every other mode.

It also explains a gap that would otherwise look like a defect in the metric
extractor. `modestats.csv` records the mode agents **chose** (pt 4.69% at 1%);
`output_trips` records trips that **completed** (pt 0.357%). Both are correct.
Only the second is a mode share, and at 1% the simulation is not producing one.

**Consequence.** Every P4 behavioural measurement taken at 1% carries this
artefact, including the §9.7 seed test and the §9.10 fraction diagnostic. The
§9.10 conclusion nevertheless **stands**. It was nearly overturned on the apparent
fraction-sensitivity of ride (61.06 → 50.94), and most of that swing is the
artefact rather than sampling. Because a §8.5 departure cannot be un-logged, the
10% reading is being **confirmed at 25% before any specification change is
chosen**; the threshold between 10% and 25% is unmeasured.

### A defect found by computing the first fits, and it flattered the answer

`fit.py` collapsed two different situations into one branch — a station that
resolved to no link, and a station whose links carry a modelled volume of zero —
and emitted the *did not resolve to a link on the run network* reason for both.
Only one of the three affected targets fits that description.

| target | station | observed AADT | modelled | actual situation |
|---|---|---:|---:|---|
| V079 | 55717 Tarean Road (Karuah) | 1,270 | absent | genuinely outside the network (issue 10) |
| V096 | 55839 Raymond Terrace Rd | 11,810 | **0** | links resolve; the model routes nothing over them |
| V113 | 55888 **M1 Pacific Motorway (Wyee)** | **48,016** | **0** | links resolve; the model routes nothing over them |

**A modelled zero is a result, not an unscorable target**, and dropping it removed
the two stations where the model fails hardest from every aggregate — the
inversion of proposal §8 deliverable 3. Corrected: the two conditions carry
separate reasons, a zero is scored at −100% and flagged in
`counts.modelled_zero_stations`. The fit moves from 36 scored / 31 unscorable to
**38 / 29**, counts from 31 stations to 33, and the count error honestly worsens
(10%: mean −72.1% → **−73.8%**, RMSE 20,849 → **21,750**).

**This exposes a modelling gap, not a reporting question.** The model puts **zero
cars on the M1 at Wyee** — a 4,000-capacity, 110 km/h link with an observed 48,016
AADT on the southern study-area boundary. The likely cause is the external tier:
B2 synthesises 5,384 weekday boundary agents and evidently routes none onto the
motorway there. Until that is understood, every boundary-adjacent count is biased
low. Recorded rather than fixed.

### Three values that were governing the model from outside the registry

Found by auditing for literals rather than by a failure, and all three now resolve
through `config/registry/`:

- **`B.counts.station_match_radius_m` (new field, 120 m).** A CLI default in
  `map_count_stations.py` with no provenance and no range, and it decides which
  `road_aadt` targets are scorable **at all** — a lever on the reported fit, not a
  plotting tolerance. Swept 60–120 m on measurement: the largest accepted match is
  119.7 m, so 120 m is exactly binding; at 100 m six of the 116 matched stations
  lose their link and at 60 m twenty-three do. Gated as the build-layer migration
  was — `count_station_links.csv` rebuilds **byte-identical**.
- **`sample_population.SEED`** held its own copy of 20260810 and now resolves from
  `RUN.machine.seed`.
- **`solve_asc_ride.py`** carried five run parameters and the −0.85 prior as
  literals and — found while removing them — **called `run_matsim.run()` with the
  pre-registry positional signature, so it could not execute at all.** It is the
  tool #9 needs, so it was repaired rather than deleted: every run parameter now
  resolves through the registry, the candidate bracket is a required argument on
  the same principle as `--iterations`, and it reads the schema-validated
  `_metrics.json` rather than raw `modestats.csv`. `fit.py` is deliberately still
  not invoked, so it remains structurally unable to reach a validation target.

Two P1 exploratory probes (`src/extract/ckan_probe.py`, `src/extract/s3_list.py`)
were deleted: no docstring, no artefact in the manifest, referenced by nothing.

---

## 9.13 Trip length by mode — an observable the package always held (P4 stage 3)

The HTS mode table carries `TRIP_AVG_DISTANCE` and `TRIP_AVG_TIME` per mode, per
LGA, for fourteen survey years. **Nothing used them.** P4 read `MODE_SHARE` for
the targets and `TRIPS_BY_MODE` for the §9.8 occupancy constraint, and left the
two columns that say whether a mode is used over the right *range* untouched.

Mode share says how many people choose a mode. It cannot say whether they choose
it for the right journeys, and a model can hit a share exactly while using a mode
for trips it would never serve in reality.

### The constraint, measured

`src/calibrate/measure_mode_constraints.py` now derives it into
[`params/C4_mode_constraints.json`](../params/C4_mode_constraints.json) on the
same principle as occupancy: the value is the base-year figure and the sweep is
**the observed spread across every survey year for that mode**, not an interval
anyone chose.

| mode | HTS category | observed km | sweep | observed min | years |
|---|---|---:|---|---:|---:|
| car | Vehicle driver | 10.20 | 6.60 – 10.80 | 17.20 | 7 |
| ride | Vehicle passenger | 9.80 | 5.60 – 9.80 | 15.50 | 7 |
| pt | Public transport | 23.40 | 15.90 – 24.50 | 34.40 | 3 |
| walk | Walk only | 0.70 | 0.70 – 1.10 | 12.30 | 7 |
| bike | Other | 5.20 | 3.10 – 5.20 | 19.20 | 7 |

Ten registry fields declare it — one per mode per quantity, because the schema
takes an interval per field and **weakening the schema to accept a per-mode
mapping would have been the wrong repair**. `fit.py` reports the comparison
beside the fit and never counts it into one.

**It is a constraint, not a target.** The 67/143 split is pre-registered and
nothing here joins it; `check_package.py` asserts that no calibration metric
carries a trip-length name.

### It caught an error the moment it existed, and the error was mine

Before the constraint was wired up, the comparison was made by hand and reported
as *"car 10.16 modelled against 10.20 observed — essentially exact, and car is the
only mode with a distance cost"*. **That was wrong.** The modelled figure was the
**five-LGA** mean and the observed figure is **Newcastle LGA**. The study area
includes Cessnock, Maitland and Port Stephens, whose trips are far longer than
Newcastle's, so the two numbers were never comparable — the identical mismatch
§12.1 records for the seed.

Like for like, both sides Newcastle LGA, on `ride_sufficiency_10pct`:

| mode | modelled km | observed km | ratio |
|---|---:|---:|---:|
| car | 6.36 | 10.20 | **0.62** |
| ride | 8.56 | 9.80 | 0.87 |
| pt | 11.02 | 23.40 | 0.47 |
| walk | 2.90 | 0.70 | **4.14** |
| bike | 5.72 | 5.20 | 1.10 |

So the correct statement is nearly the opposite of the one first drawn: **car
trips are 38% too short, not exact**, and `ride` is closer to its observed length
than `car` is to its. The claim that ride was "41% too long" was an artefact of
the geography error.

### What survives the correction, and it is the part that matters

The **ratio between two modes is robust to geography** — it does not depend on
how long the study area's trips happen to be:

| | modelled | observed |
|---|---:|---:|
| ride ÷ car trip length | **1.346** | **0.961** |

Observed passenger trips are slightly **shorter** than driver trips. The model
makes them **35% longer**. That asymmetry is real, it is the signature the §9.8
zero distance rate would produce, and it is unaffected by the geography error
that damaged the levels.

It also puts a number on a second distortion nobody had looked at: modelled
**walk** trips are **4.1× their observed length** (2.90 km against 0.70 km, and a
median of 45.99 min), which is not walking behaviour under any reading.

### Why this is recorded before any specification change

§9.8 set `ride`'s monetary distance rate to zero and declared it *derived, not
assumed*, on an aggregate-cost identity. The observable that would have tested
that derivation was in the package the whole time. **A value declared `derived`
is only as good as the identity it was derived from, and this is the check that
catches one derived from the wrong identity.** It is in place before the §8.5
departure is chosen, so whichever candidate is taken can be judged against an
observable rather than against the mode share it was chosen to move.

**Also unused until now: `Serve passenger` is 15.7% of observed journeys** —
87,000 a day, average 6.4 km, the second-largest purpose in Newcastle and larger
than commuting. B2 generates none of them (issue 11). That is a measured demand
component, not the assumption the issue had recorded it as, and it is the driver
side of the same problem: with no escort trips, a car passenger costs nobody
anything.

---

## 9.14 The external tier is 0.43% of trips and does not drive (P4 stage 3)

§9.12's correction to `fit.py` stopped discarding count stations the model fails
on, and the first thing it surfaced was a modelled **zero** on the M1 Pacific
Motorway at Wyee against an observed 48,016 AADT. Investigating that turned out
not to be about one station.

### Every motorway station is short, and the error grows toward the boundary

| target | station | modelled | observed (light-vehicle) | error |
|---|---|---:|---:|---:|
| V113 | Pacific Motorway (Wyee) | **0** | 44,885 | **−100.0%** |
| V094 | Pacific Motorway (Freemans Waterhole) | 90 | 35,922 | −99.8% |
| V093 | Pacific Motorway (Freemans Waterhole) | 90 | 3,483 | −97.4% |
| V091 | Pacific Motorway (West Wallsend) | 200 | 3,076 | −93.5% |
| V081 | Pacific Motorway (Black Hill) | 3,590 | 31,356 | −88.5% |

**Motorway stations median −97.4%; every other calibration station −69.6%.**
Black Hill, nearest the urban core, is least wrong; Wyee at the far southern
boundary is exactly zero. The network is not at fault: **263 of 314 links named
"Motorway" carry traffic**, so the M1 is connected and routable. It carries a
median of 40 vehicles per link at a 10% sample — roughly 400/day scaled — where
one station observes ~45,000.

### The tier that should supply that traffic is 0.43% of trips

962 external boundary trips against 223,144 core trips, median length 68 km.
`B.external.interaction_rate` is **0.08, `assumed`**, swept 0.04–0.15, and its own
registry entry already records that it is *localisable but not yet available*: the
ABS journey-to-work SA2 × SA2 origin–destination table would settle it, and the
package holds the place-of-work side without the pairing (§13). A tier this size
cannot load a motorway whose observed flow at a single station exceeds the whole
modelled external demand roughly 45-fold.

### And the external agents that exist almost never drive

| mode | trips | median km | median hours |
|---|---:|---:|---:|
| **bike** | **478** | **96.1** | **6.35** |
| ride | 432 | 46.7 | 0.76 |
| pt | 46 | 110.3 | 3.20 |
| **car** | **6** | 50.0 | 0.74 |

**478 external agents cycle a median 96 km over 6.35 hours**, and that survived
250 iterations of a utility-maximising co-evolution. It is specific to the tier —
core agents at 60 km and beyond take car 24.5% and bike 3.7%, which is sensible.

**Ruled out by measurement:** not permission, since all 531 external agents carry
`carAvail=always` and `hasLicense=yes`; not connectivity, since all **586**
distinct start and end links they use exist in the run network and **every one
permits car**; not the network, which routes traffic on 84% of motorway links.

**The mechanism is not established and is recorded as open rather than guessed.**
On the shipped scoring a 96 km bike trip costs roughly −140 utils against about
−38 for the same trip by car, so mode choice moving agents *into* bike and *out
of* car inverts what the utilities imply. Something structural is doing it. Five
hypotheses have already died between this and §9.12; this one gets measured.

### Why it is recorded rather than fixed

Both halves — an undersized tier and a tier that does not drive — are B2 changes,
and B2 regenerates the P3 demand artefacts and **breaks comparability with every
run to date**. That is a planned break, not something to slip in beside a
specification change while a fraction series is still being measured.

**Consequence, and it is not small.** Until this is understood every
boundary-adjacent count is biased low, and the −73.8% overall count error carries
a large contribution from a demand tier that is both too small and not driving.
Calibrating the core network against those counts would be tuning it to
compensate for missing through traffic — the count analogue of the ASC absorption
proposal §9 names as the primary threat to validity. **No count-based calibration
should be attempted until §9.14 is resolved.**

---

## 9.15 The external tier walks to the network, and the escort trip is typed wrong (P4 stage 4)

§9.14 left the external tier's behaviour "recorded as open rather than guessed"
after six hypotheses died. The seventh was measured rather than guessed, and it
is structural: **the external tier is charged a walk that the modes it chooses
instead are exempt from.**

### The mechanism

`routing.accessEgressType = accessEgressModeToLink` with
`routing.networkModes = car,ride`. So `car` and `ride` are routed on the network
and pay an access and egress walk from the activity coordinate to the link;
`bike` and `walk` are teleported at a beeline speed and pay **nothing**.

That is harmless for the core population, whose activities sit on observed POIs
inside the network. It is not harmless for the external tier, because **all 201
external zones lie outside the modelled area**: their centroids sit a median
**21.3 km** beyond the five-LGA boundary, a top decile of 80.7 km and a maximum
of **128.7 km**, while the road network is clipped to the study area. B2 placed
the trip end by uniform area-jitter inside the external SA1, so it landed where
no modelled road exists and MATSim walked the agent to the edge of the network.

Access and egress walk per trip, iteration 0, from `0.legs.csv.gz`:

| tier | mode | trips | median walk km | median walk h | median main km |
|---|---|---:|---:|---:|---:|
| core | car | 31,197 | **0.097** | 0.026 | 8.8 |
| core | ride | 35,119 | 0.099 | 0.026 | 8.2 |
| core | bike | 47,108 | 0.000 | 0.000 | 7.1 |
| **external** | **car** | 134 | **2.656** | **0.703** | 46.9 |
| external | ride | 151 | 1.054 | 0.279 | 47.5 |
| external | bike | 188 | **0.000** | 0.000 | 72.0 |

The external car access walk is **27x the core's**, and its top three deciles are
**16.4 / 39.9 / 49.8 km — of walking**, at the 1.05 m/s teleport speed.

### It is monotone in the score, so it is not a coincidence

Iteration 0 is the clean test: the uninformed seed assigns modes uniformly, so
mode is exogenous and every agent is equally unrelaxed.

| mode | access-walk band | agents | median score | activities performed |
|---|---|---:|---:|---:|
| car | < 0.5 h | 24 | **+94.21** | 3 |
| car | 0.5 - 2 h | 13 | +72.91 | 3 |
| car | 2 - 6 h | 6 | -22.10 | 3 |
| car | **> 6 h** | **39 (48%)** | **-1165.01** | **2** |
| ride | < 0.5 h | 35 | **+111.67** | 3 |
| ride | > 6 h | 44 (47%) | -1169.82 | 2 |
| bike | < 0.5 h | **101 (all of them)** | -96.17 | 3 |

A well-connected external car tour scores **+94**. A badly-connected one scores
**-1165**, and **48%** of them are badly connected. The tour truncates - two
activities instead of three - because the agent spends the day walking to the car
and never gets home. Tours that never complete: **car 39.0%, ride 38.7%, pt
66.7%, walk 85.3%, bike 13.9%**.

Bike is the *worst* mode for a connected external agent and the *best* for a
disconnected one, and it is the only mode that is never disconnected, because it
is teleported door to door. Within-agent, over the 220 agents that realised both,
bike beats car by a median **+118.93** utils, and the difference is **bimodal at
plus or minus 1000** - the signature of a plan that does not complete, not of a
cost. **Mode choice was behaving correctly.** The 478 agents cycling 96 km were
choosing the only mode that did not require them to walk to a road.

**Why six hypotheses died.** Permission, connectivity, the network, replanning,
aborts and the seed all tested *the link*. Every one of them was sound. The
defect is *the distance to the link*, which none of them measured. §9.14's
utility arithmetic - "-140 by bike against -38 by car, so the choice inverts what
the utilities imply" - omitted the access leg, which is the structural thing it
correctly concluded must exist.

### A second defect, independent of the first

All 531 external agents carried `rideAvail=always`. `build_matsim_plans.py`
resolved the unknown that way on the ground that "external boundary agents are
not in B1, so household composition is unknown". But §9.11's rule is that a
person may be a car passenger only if their household holds a vehicle **and**
contains another licence holder, and an external agent is **household-less by
construction** - the generator's own words. A person with no household cannot
satisfy that condition, so the unknown was resolved in the wrong direction, and
**432 of 962 external trips were car-passenger trips with no possible driver.**

### A third, which is a scope consequence and not a defect

The external tier is not a ring. Every one of its 201 zones is in a single SA4:

| sector | N | NE | E | SE | S | SW | W | NW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| zones | 18 | 23 | 17 | **0** | **0** | **0** | 3 | **140** |

The southernmost external zone is at latitude -32.856; the M1 southern cordon is
at -33.218. **There is no external zone anywhere in the Sydney direction**, so no
interaction rate can put traffic on the M1 at Wyee. That is not an accident:
`extract_zones.py` defines the tier as "the remainder of SA4 'Hunter Valley exc
Newcastle' ... retained only as a boundary treatment for **Hunter Line**
through-demand", which is scope decision 3 in §1. The M1 gap therefore lies
**outside the tier's declared purpose**, and #20's framing of it as a tier-size
problem is corrected: raising `B.external.interaction_rate` would not have
touched it.

### The repair

The standard treatment of boundary demand is an **external station**: the trip
enters at the point where its corridor crosses the cordon, on a real link, and
the portion of the journey outside the study area is not modelled. That is what
is now built, and it removes the mechanism by construction rather than by
counterweight.

1. **Cordon anchoring.** The cordon set is *derived, not listed*: a node is an
   external station if it is the nearest node on a road capable of carrying
   boundary demand (`B.external.cordon_road_classes`) to at least one external
   zone, which by construction puts it on the outward-facing edge of the network.
   **42 crossings.** Testing distance to the study-area boundary instead picks up
   the **coastline**, which is a boundary but not a crossing. Each agent enters
   through the crossing that minimises `d(zone, cordon) + d(cordon, destination)`
   - the entry that is on the way, not merely the nearest to home.
2. **Destinations on observed attractors.** The external tour's core end was
   jittered inside the destination zone while the core population's was placed on
   a POI. It now uses the same routine.
3. **Ride withheld from the tier** (`B.external.agent_ride_available`, derived),
   and the placeholder attributes it used to type in are declared
   (`B.external.agent_profile`).
4. **`Serve passenger` given its own tour purpose, HX.** It was mapped to NHB and
   then folded into the discretionary tours, because NHB is not a tour purpose.
   That preserved the trip **rate** and lost the trip **type**: an escort became a
   two-hour discretionary stay made by anyone, rather than a five-minute drop-off
   made by a driver. It now carries its own rate, its own gravity decay against
   the observed serve-passenger journey distance, the education departure profile
   and attractor set (the school run being the dominant and most peaked
   component), a licence requirement on the traveller
   (`B.activity.escort_requires_licence`, derived), and a MATSim `escort` activity
   whose typical duration is minutes rather than hours - a longer one would hold
   the vehicle at the destination and displace the return trip out of the peak.
   **#11's premise is corrected: the demand was not absent, it was mistyped.**
5. **NHB removed from the destination-choice purposes.** With serve passenger
   moved out, nothing observed maps to NHB, so it had no journey distance to
   calibrate against - the check caught this immediately. It is a *leg* label, not
   a tour purpose, and carrying it built an attractor index and solved a decay
   that nothing drew from.

### What the repair does to the inputs

| | before | after |
|---|---:|---:|
| External leg length, median | 54.2 km | **21.6 km** |
| External leg length, top decile | 106.6 km | 43.0 km |
| External destination placement | 5,385 `jitter_external` | **5,408 `poi`**, 59 jitter |
| Serve-passenger share of weekday legs | **0** | **14.53%** (observed 15.7% of journeys) |
| Week trip rate vs HTS 3.473 | 3.397 (-2.2%) | **3.418 (-1.6%)** |
| Seed ride share | 0.1712 | 0.1620 |

### What is deliberately NOT repaired

- **The M1, and boundary through traffic generally.** Representing it needs an
  external-station matrix seeded from cordon counts, which is a scope decision
  about what the model is for, not a defect fix. **The §9.14 consequence stands
  unchanged: no count-based calibration until it is resolved.**
- **`B.external.interaction_rate` stays `assumed` and swept 0.04-0.15**, not
  pinned. It still needs the ABS journey-to-work SA2 x SA2 table (§13).
- **The escort trip is still only the driver's side.** No passenger is bound to
  the escorting driver; that is the socnetsim limitation §9.11 already records.
- **`WB` is not corrected for the employed fraction**, though `HX` is corrected
  for the licence-holding fraction. Both are secondary purposes drawn only for a
  subset of persons, and the rate solve accounts for neither. Logged rather than
  changed: it is pre-existing, it is not what this change is about, and altering
  it would move an existing calibration for no measured reason.

### This is a planned comparability break

B2 was regenerated, so the demand under every run to date has changed. **The
three `ride_sufficiency_*` runs are historical** and no earlier run shares this
demand. The re-measurement runs as `cordon_escort_10pct`, configured identically
to `ride_sufficiency_10pct` so the comparison isolates the demand change.

**Neither is a result.** 250 iterations remains measurably short of relaxation
(§9.7), and the §8.5 ride departure (#16) is still unchosen - it must be re-taken
on the repaired demand, because the ride share it was to be chosen against has
moved.

---

## 9.16 The calibration loop, the report, and the outer-loop tolerance (P4 stage 5)

P4 deliverables 4, 6 and 7. Deliverable 5, the calibrated base, needs the loop to
have run and is **not** met by this section.

### What the loop is allowed to move, and why almost nothing is

`src/calibrate/calibrate.py` **derives its search space from the registry rather
than listing one**. A field is movable only if it is `assumed`, carries a scalar
sweep, is not `held_fixed`, and — the clause that does most of the work — can
actually be *realised* by the pipeline the loop runs.

Thirty-eight registry fields carry a scalar sweep. **Twenty-one are excluded,
each with a stated reason**, and the exclusions are derived from the `consumers`
declaration rather than hand-maintained:

| excluded because | example | why it is not a calibration parameter |
|---|---|---|
| the loop's own controls | `CAL.search.max_rounds` | calibrating the search against itself |
| run identity or compute | `RUN.sample.fraction` | a machine choice, not a property of Newcastle |
| measurement apparatus | `B.counts.station_match_radius_m` | moving it changes what the fit can *see*, not what the model *does* — which is precisely the defect issue #19 was |
| needs the mapper re-run | `A.transit.era1_line_speed_kmh` | §3.5: ~18% of route link sequences differ between identical builds, so a scenario mapped in one build cannot be compared with one mapped in another |
| needs a demand rebuild | `B.activity.p_second_stop` | B2, the plans and the 30 run-input sets would have to be regenerated per candidate; possible, but not implemented, and therefore refused rather than silently skipped |
| no declared consumer | — | nothing would read a change |

That last mechanism matters more than it sounds. The loop runs
`run_matsim.py -> extract_metrics.py -> fit.py` and rebuilds nothing else. Passing
`--set` for a field that only a build script reads would change the **recorded
configuration** without changing a single **input** — a run that reports a
parameter it did not use. Refusing is the only honest option.

**The mode constants are unreachable by construction.** They carry `held_fixed`
under §8.5, so the filter removes them before any search begins. Proposal §9
names ASC absorption as the primary threat to validity, and this is that rule
made structural rather than remembered.

### The objective is mode share, and that is not an oversight

| block | targets scored | in the objective |
|---|---:|---|
| mode share | 5 | **yes** |
| patronage | **0** | no — nothing to score |
| counts | 33 | **no — forbidden by §9.14** |

**Patronage scores zero in a single day-type run.** The contemporary monthly
target needs WEEKDAY, SAT and SUN composed over a calendar month; the rest are a
pre-pandemic PT market against a 2026 base (§12). So it contributes nothing.

**Counts are scored and reported on every run but never optimised against**
(`CAL.objective.include_counts = false`, and the loop refuses to start if it is
set true without a recorded departure). §9.14 and §9.15: the external tier
carries no boundary through traffic, so every boundary-adjacent count is biased
low by construction and tuning the core network against them would compensate for
demand the model does not contain.

That leaves **five HTS mode shares, which sum to one — four independent
numbers.** `CAL.objective.independent_targets` records it and **the loop refuses
to move more than four free parameters**, printing the movable set instead of
producing a fit of more parameters than data. §12.1 reached the same number from
the other direction.

### Constraints stay constraints

The C4 occupancy and trip-length observables are **feasibility conditions, never
objective terms**. A candidate that violates one is marked infeasible and
reported; it is not penalised into the objective. Adding an observable to the
objective would convert a constraint into a target, and the 67/143 split is
pre-registered — new observables join as constraints or not at all.

### Two independent guards against reading a holdout row

`fit.py` filters to `split == 'calibration'` at read time and raises if anything
else survives, so a holdout value is never in memory. The loop **never opens the
targets file at all**; it reads the `_fit.json` that `fit` wrote, and
`audit_no_holdout()` re-checks that the fit output reconciles scored against
explained and that every block naming a count of targets also names the targets.
A leak would have to defeat both.

### Deliverable 7: the outer-loop tolerance is 5 seconds

Proposal §5.2 defers this — run the loop *"until the corridor run time is stable
within a tolerance to be defined at calibration"*. It is now defined, and
**derived from the resolution of the target rather than chosen**:

| quantity | value | source |
|---|---:|---|
| Corridor run-time target (V208/V209) | **720 s** | scheduled, not observed |
| Timetable quantum | **60 s** | every segment of `A4_segment_runtime_decomposition.csv` is a whole multiple; direction 0 sums to exactly 720 s |
| So the target is known to | **±30 s** | |
| Smallest declared corridor sensitivity | **≈79 s** | charging dwell, 11% of end-to-end run time |
| Largest | **≈274 s** | signal priority, S2 against S2b, 38% |
| **Tolerance** | **5 s** | 0.69% of the run time |

At 5 s the loop sits an order of magnitude inside the smallest declared
sensitivity and well inside the resolution of the target it is judged against, so
a converged loop cannot contribute materially to any reported difference. It is
`held_fixed` rather than swept because a convergence tolerance decides how many
outer iterations are *paid for*, not what the answer is.

**It carries a self-policing bound.** If any reported scenario comparison ever
turns on a corridor run-time difference smaller than **twice** the tolerance,
that difference is not resolvable by the loop that produced it: the tolerance
must be tightened and both scenarios re-run **before** the comparison is
reported. `check_package.py`'s assertion is the **inversion** of the one it
replaces — it used to assert the value was still null so that no loop could be
built on an unexamined default; it now asserts the value exists, is held fixed
with a rule, and carries that bound.

The SUMO run harness and the loop itself remain **P5**. This is the number they
must honour.

### Deliverable 6: the report leads with what the fit cannot do

`src/calibrate/report.py` computes nothing. Every number in it was produced by
`fit.py`. It opens with how many targets were scored, how many could not be and
why, and how much independent information the scored ones carry — because a
report that opens with a headline error invites the reader to treat it as a
score. Constraints are reported in their own section, apart from the targets, so
they cannot be counted as evidence of fit. Where no calibration search has run,
the provenance section **says so** rather than leaving it to inference.

### A finding the loop turned up: the C-layer values have two homes

Six behavioural fields resolve from the registry and are read by **nothing**:
`C.transfer.beta_transfer_penalty_min`, `C.walk.*`, `C.gradient.*`,
`C.crowding.*`, `C.nesting.*`. Two of those are documented as not surviving
translation to MATSim scoring (§9.3 — crowding and nesting). The others are read,
but from `params/C1_parameters.json`, which is what
`build_matsim_run_inputs.py` actually opens — the transfer penalty reaches the
model as `utilityOfLineSwitch = -2.2614`, which is 8 minutes at the trip-weighted
16.96 AUD/h.

So the registry copy is a **mirror**, and `check_legacy_drift.py` pins the
registry to source *constants*, not to a params file. **The pair was unpinned.**
All eleven comparable values agree today; a check now asserts it, because two
copies of a number is the drift this package cannot absorb.

---

## 9.17 The §8.5 departure: a car passenger pays for the kilometre (P4 stage 5, issue #16)

**Logged before the result it will be judged on.** §8.5 requires a departure to
be recorded *before* results are seen, and this section is written while the
`cordon_escort_10pct` run is still at iteration 161 of 250, before any fit has
been computed on it.

**What had been seen, stated rather than glossed:** the intermediate
`modestats.csv` of that run up to iteration 161. That file records the mode
agents *chose*, not trips that *completed* (§9.12), it is far short of
relaxation, and — the part that matters — **neither piece of evidence for this
departure comes from it.** Both were measured on the `ride_sufficiency_*` runs
and are recorded in §9.12 and §9.13, before the demand repair existed.

### The departure

`C.scoring.monetary_distance_rate['ride']` moves from **0.0** to **−0.00018
AUD/m**, the car rate.

### Why this is a correction, not a calibration

§9.8 set the rate to zero and declared it **derived, not assumed**, on this
identity: *a vehicle's operating cost is paid once, and at occupancy 1.35
charging both occupants makes aggregate vehicle operating cost 1.35× the real
one.*

**That identity is true, and it is about the wrong quantity.** It is a statement
about **aggregate system cost accounting** — do not count the same litre of fuel
twice when totting up what the region spends. `monetaryDistanceRate` is not that.
In MATSim it is the cost **perceived by one person weighing one alternative**.
The identity was applied to a term it does not govern.

Stated as the identity that now applies: **a kilometre in a car costs the same
kilometre whether you are in the driver's seat or beside it.** The rate is still
*derived* — derived from the car rate, because it is the same vehicle — rather
than assumed or fitted.

### The observable that falsified the old identity, and it is not a target

§9.13 measured trip length by mode against the HTS, as a **constraint** that is
reported and never scored:

| | modelled | observed |
|---|---:|---:|
| ride ÷ car trip length | **1.372** | **0.961** |

Observed passenger trips are slightly **shorter** than driver trips. The model
made them **43% longer**, and the distortion **widened with sample fraction**
(1.075 → 1.346 → 1.372). §9.13 named it at the time: *"the signature the §9.8
zero distance rate would produce."* A mode with no marginal cost of distance is
chosen disproportionately for long trips, which is exactly what was measured.

This matters for the integrity of the departure: the evidence is a **constraint**
in the C4 sense, not one of the 67 calibration targets and not a holdout row. The
correction is justified without reference to any target the model is scored
against, so it cannot be a case of fitting the answer.

§9.8's own field description also anticipated it: *"with ride at zero and no
driver-availability constraint, ride is cheaper than car on any trip longer than
about 4.7 km. That asymmetry is real."* It is now removed rather than left for
the constant to absorb.

### What this deliberately is NOT

**It is not solving `asc_car_passenger` harder.** The constant stays where §9.8
constrained it, at −0.85, tied to observed vehicle occupancy. Proposal §9 names
ASC absorption as the primary threat to validity, and moving a distance rate that
was mis-specified is the opposite of absorbing a specification error into a
constant. `calibrate.py` cannot reach the mode constants at all — they are
`held_fixed`.

**It is not the whole of #16.** The second candidate — a zero-PCE queued `ride`,
so that a car passenger experiences congestion instead of being teleported at the
router's free-flow estimate — remains **scoped and unapplied**. It addresses a
separately measured distortion: `ride` runs **15–22% faster per kilometre than
car in every distance band**, with identical leg composition and near-identical
routed detour (1.4490 against 1.4716). A passenger physically travels in a car
and cannot arrive sooner than one.

That candidate is deliberately **not** applied in the same change, for two
reasons. It alters the mobsim rather than the scoring, so it must ship with its
own measurement — `ride` minutes per kilometre must converge on `car`'s, and
`vol_car` at the 33 count stations must not move, or §12.2a's count identity
breaks. And applying two corrections at once makes neither attributable. This one
is the larger lever and the better evidenced; it goes first, and the second is
decided on what it leaves behind.

### What would falsify this departure

If `ride` overshoots **below** the observed 20.6% share, or if the ride ÷ car
trip-length ratio overshoots below the observed 0.961, the rate is doing more
work than the correction justifies and the second candidate must not be added on
top of it. Both are recorded here **before** the run that tests them.

---

## 9.18 The light rail vehicle carries the capacity that was published (P4 stage 6, issue #18)

**Three numbers described one vehicle and none of them agreed.** The mapped
fleet gave the tram **180 seats and no standing room**; `DECISIONS.md` §4.1
records a published CAF Urbos 100 maximum of **270** and an assumed
`capacity_seated` of **60**. 180 reconciles with neither.

180 is not a Newcastle figure at all — it is **pt2matsim's generic tram
default**, and the zero standing room is a flag the build never set. So was
every other vehicle's: bus, rail and ferry are all seats-only.

### Why the second half was worse than the first

Because **no vehicle in the fleet had standing room**, the C1 crowding
multipliers (1.00 seated / 1.45 standing) were **inert by construction**.
Standing never occurred, so a multiplier on standing could never apply, in any
scenario. That is the §9.3 pattern again and the issue #21 defect class: a
declared parameter that reaches nothing produces a sensitivity band of zero and
would be reported as "insensitive to crowding" when the truth is "crowding
cannot happen here".

### The decision

| field | value | source |
|---|---:|---|
| `A.lightrail.capacity_total` | **270** | **observed** — published, §4.1 |
| `A.lightrail.capacity_seated` | **60** | **assumed**, swept 50–80 |
| `A.lightrail.capacity_standing` | **210** | **derived** — total − seated |

Only the *split* is assumed; the total it is taken from is published. The
standing figure is not a free value and carries no sweep of its own, because it
is whatever the published maximum leaves once the seats are removed — the
`derived_from` identity the schema requires instead of an invented interval.

Applied in `build_matsim_run_inputs.py`, over the **already-mapped** fleet.
The schedule mapper is not re-run, so §3.5 holds unchanged.

### What is deliberately NOT done

**Bus, rail and ferry keep their pt2matsim defaults and keep no standing room.**
This package holds a published capacity for the light rail vehicle — the object
of study — and holds none for a Newcastle bus, a Hunter Line car or the Stockton
ferry. Setting a standing figure for those would be inventing an observation,
which is the one failure this project cannot absorb. **It is recorded as a
limitation and is the open half of issue #18**, to be closed by a source or by
an explicit swept assumption, not by a number chosen here.

**Consequence to carry:** light rail capacity rises 180 → 270 per vehicle, which
is +50%, and it moves the ceiling on hypothesis A1's own metric. No result
existed when this was taken.

---

## 9.19 A live view of a run, and why it is not a live map (P4 stage 6)

`src/analyse/run_monitor.py` serves a run in flight on loopback; `run_matsim.py`
prints the url as it launches MATSim.

**It is an observer.** It reads the run directory, holds no lock, opens nothing
the run is writing to and writes nothing itself. It is not in `_run.json` and
not part of the run identity: a run observed is byte-for-byte a run unobserved.
`RUN.monitor.enabled` turns it off.

### Why it shows progress and convergence rather than vehicles

A live *map* was measured and rejected on the measurement, not on effort.
Events are written only every `RUN.controler.write_events_interval` = **10**
iterations. When they are written, the file grows at **~5.2 MB/s** and the whole
30 h simulated day lands in about **50 s** of wall clock — roughly **2,000×
real time** — then nothing for ~3.5 minutes until the next events iteration.
A partial gzip does decode cleanly (a 10 MiB prefix yields 93.8 MB of XML to
simulated 07:15), so the *plumbing* would work; there is simply no steady stream
to watch. A live map would show a flicker and then a blank screen.

What changes at a human pace is **progress** and **convergence**, so that is what
is served: iteration against target with an ETA from the observed iteration
time, the mode trajectory, the score trajectory, and the drift after innovation
switches off — which is the direct read on the question issue #5 turns on.

**The mode trajectory is `modestats`, and the page says so on its face:** the
mode agents *chose*, not trips that *completed* (§9.12). `extract_metrics.py` →
`fit.py` remains the only route to a reportable number.

`replay_events.py` is unaffected and remains the instrument for what a finished
run did in space.

---

## 9.20 A count of one road is not a count of its neighbour (P4 stage 6, issues #20, #10)

`map_count_stations.py` matched a station on road name **and** proximity where a
name existed, and fell back to the **nearest link of any name** where it did
not. The fallback was doing more work than intended, and in two directions.

### It was rejecting matches that were the same road

| station | link it was attached to | distance | what it is |
|---|---|---:|---|
| Red Head Road | **Redhead** Road | 46.4 m | one road, spaced two ways |
| St James Road | **Saint** James Road | 25.9 m | RMS abbreviates, OSM does not |
| Werribi Street | Werribi Street **(West)** | 23.0 m | OSM carries a qualifier, the station does not |

All three were being recorded as `proximity_only` — a weaker claim than the
truth. `normalise` now folds `saint`→`st` as it already folded `street`, drops a
parenthetical qualifier, and a second naming tier compares with spaces removed.

### It was accepting matches that were a different road

The other nine fallbacks attached a station to a road it does not count. The
clearest is **Raymond Terrace Road** (V096, observed **11,810 AADT**), attached
at 107.9 m to **Dockyard Road** — one lane, 50 km/h, which is not a plausible
carrier of 11,810 vehicles a day — and then **scored against it**. Also
**Pacific Motorway** to a *George Booth Drive Offramp*, and **Nelson Bay Road**
to *Teal Street*.

**The rule now: a station that names its road may only be matched to a link
bearing that name.** Where none is in range the station is reported unmatched,
with the count of nearby links that were deliberately *not* taken. Proximity
alone still matches a station that names no road.

**Every one of the 195 matched links is now `name_and_proximity`; zero are
proximity-only.**

### This moves the reported count fit, and in which direction matters

| | before | after |
|---|---:|---:|
| stations matched | 116 | **111** |
| links | 203 | **195** |
| proximity-only | 14 | **0** |
| count stations scored | 33 | **30** |
| mean count error | −72.2% | **−69.9%** |
| modelled zeros | 2 (V096, V113) | **1 (V113)** |

The fit **improves by 2.3 pp, and that improvement is not the model getting
better** — it is a wrong comparison being withdrawn. This has to be stated
plainly because it is the shape of the #19 defect running backwards: #19 was a
station being dropped *because* the model failed on it, which flattered the fit.
Here a station leaves the scored set because the link was never its road. The
test that separates the two is whether the reason survives inspection without
reference to the model's answer, and V096's does: *Dockyard Road is not Raymond
Terrace Road*, which was true before any run existed.

**The M1 at Wyee (V113) is untouched and still scores −100%.** It matched by
name, on both carriageways, at 67.3 m and 68.3 m. That was the point of
separating the two halves of #20: the mis-match is a mapping fault and is now
fixed; **the modelled zero on the M1 is a demand fault and is not**, and it
stays visible in the fit. §9.14's consequence stands unchanged — no count-based
calibration until the boundary through-traffic question is settled.

**Issue #10 is answered rather than fixed.** Tarean Road, The Bucketts Way and
one Nelson Bay Road station have **no car link within 120 m in any direction**:
they lie outside the five-LGA clip, which is a scope decision (§1, decision 3),
not an oversight. Extending the clip would mean rebuilding the network and
re-running the schedule mapper, which §3.5 forbids for anything already run.
They are reported with that reason and are not dropped.

---

## 9.21 What a wide data search settled, and what it did not (P4 stage 7)

The three unobtained inputs (§0, §13) and the undeclared fleet capacities (§9.18)
were searched for exhaustively rather than assumed to be unavailable. The result
changes the *status* of two of them from "request outstanding" to something
firmer, and it produces real vehicle figures for the first time.

### SCATS phasing is refused by policy, and that is now citable

**This is no longer an outstanding request. It is a documented refusal.** In
April 2025 WalkSydney, Better Streets and Jake Coppinger formally requested
SCATS signal phasing data. Transport for NSW replied that it *"does not publish
the SCATS Signal Phasing data you requested and currently has no plans to make
this information publicly available"*, and maintained that position through
follow-up correspondence and a meeting in July 2025. **Western Australia
publishes the equivalent data freely.**

Two consequences, and the second is binding:

1. **Proposal §7.2's "No SCATS" contingency is the operative path, not a
   hypothetical.** It requires signal delay to be inferred from GTFS-Realtime
   run-time distributions, cycle time and priority to be **swept**, and — the
   part that binds every future headline — *"state the resulting uncertainty
   band explicitly in all headline figures."* `A.signals.scats_phasing` stays
   `unobtained` with its three-way categorical sweep, and the corridor result
   may never be quoted as a point estimate.
2. **It is a finding, not only a gap.** The proposal already argues that the
   absence of ex-post evaluation is a governance choice rather than a technical
   limit. A refusal to release the phasing data that would let anyone else check
   a corridor claim is the same argument with a citation attached, and it
   belongs in deliverable 6 (the method note on evaluation gaps).

### Journey-linked Opal is not published, and our own fallback was never built

Only aggregate trip counts are published, which is what the package already
holds. A privacy-preserving unit-record sample was released with CSIRO Data61,
but it is Sydney and pre-dates the light rail opening, so it cannot inform a
Newcastle transfer penalty.

**The more useful finding is about this project rather than about TfNSW.**
Proposal §7.2 specifies what to do when this request fails: *"estimate transfer
rates from tap-on/tap-off timing at the Interchange using aggregate stop-level
data plus a matching model, validate against the published interchange
percentages."* **That was never built.** `C.transfer.beta_transfer_penalty_min`
is consumed by `build_params.py` and `build_matsim_run_inputs.py` and is
estimated by nothing; the package holds `lr_tapon_share_by_stop` and the station
entry/exit series the method would need. The fallback was skipped in favour of
sweeping, and sweeping is what §7.2 permits only *after* the estimate is
attempted. **This is a missing deliverable, not a missing dataset.**

**One incidental confirmation.** TfNSW records that from 1 July 2024,
aggregations between line, agency and mode are no longer valid because a
passenger may use several lines on one trip. That is independent operator
confirmation of the §12 trap on hypothesis A1's denominator, which until now
rested on our own reading.

### Charging dwell has no published figure

WSP and Aurecon both describe the charge-bar system; neither publishes a
duration. §4.3's assessment — *"not published anywhere"* — survives the search.
`A.lightrail.dwell_charging_s` stays `unobtained`, swept 10–35 s.

**A false lead is recorded so it is not re-followed.** A search summary asserted
20–30 s at each stop and attributed it to the Newcastle Light Rail encyclopaedia
entry. **The page does not contain that figure.** It was not adopted. Anything
that reaches this model must be read from the source, not from a summary of it.

### The fleet, and every capacity in it was too generous

The mapped fleet is pt2matsim's generic defaults (§9.18). Published figures were
found for three of the four vehicle types:

| vehicle | published | model carried |
|---|---|---|
| Stockton ferry (MV Shortland / MV Hunter) | **200 total, 149 seated** | 250 seats, 0 standing |
| Hunter railcar | **77 (HM) / 69 (HMT) per car**, 7 two-car sets | 400 seats, 0 standing |
| Endeavour railcar | **95 (LE) / 82 (TE) per car** | *(same `Rail` type)* |
| Volvo B12BLE bus | **44 seated + 18 standing = 62** | 70 seats, 0 standing |
| Volvo B10B bus | **51 seated** | |

**Every one of them overstates capacity** — rail by roughly 2.7x on a two-car
set, ferry by 25%, bus seats by about 59%. That is consistent with, and
partially explains, §9.12's finding that transit capacity never binds: some of
the headroom was fictional. Newcastle still operates an almost entirely diesel
bus fleet — three battery-electric buses — so the Volvo figures are the right
basis rather than the zero-emission models now entering service elsewhere.

**Source grade, stated rather than glossed.** These are encyclopaedia and
enthusiast-maintained fleet pages, not operator or manufacturer publications;
the authoritative Australian fleet list refused automated access. They therefore
enter the registry as `literature` **with their urls**, and **swept** — not as
`observed`, which this package reserves for a value read from a source it
downloaded itself. That is a weaker claim than §9.18's light rail figure, whose
270 is a published manufacturer maximum, and the difference is deliberate.

### Taxi, motorcycle and rideshare cannot be separated

The HTS tables this package holds report **"Other" as a single bucket**. No
observed decomposition into taxi, motorcycle and rideshare exists in the
package or in the open data searched. IPART runs an annual Survey of Point to
Point Transport Use, but it measures *usage incidence* among NSW residents, not
trip mode share for Newcastle, so it can suggest a split and cannot validate
one.

**Adding three modes with no target for any of them would add structure that
cannot be falsified**, which is the opposite of what this project is for. The
single approximate mode stays, and stays labelled approximate in `fit.py`.

---

## 9.22 Three decisions taken, and the carried-over work re-prioritised (P4 stage 7)

Three questions that had been open for the user rather than for the code were
put and answered on 12 August 2026.

### 1. The §8.5 question is DEFERRED, not answered

Deliverable 5 needs a ruling on whether the mode constants may move, and there
were three ways forward (§9.16). **The decision is to take none of them yet, and
to revisit after deliverable 0a.**

The reasoning is that the fit is currently wrong in a way nobody has explained:
car **32.5%** against an observed **59.0%**, car passenger **50.0%** against
**20.6%**, and the §9.15 demand repair moved car by 1.69 pp. Seven defects have
already been found in this model and **every one produced a confident wrong
answer rather than an obvious failure**. If 0a finds an eighth, the fit may move
without touching a constant.

**Choosing branch (b) — re-opening §8.5 — to fix what turns out to be a bug
would be the exact failure proposal §9 names as the primary threat to
validity**, and it would be unrecoverable: once a constant has absorbed a
specification error, no later run can tell you it did. Deferring costs nothing,
because 0a has to happen regardless.

### 2. The run programme is cut, and one fifth of it was never doing anything

Issue #6. The specified load is 140 sweep points × 10 scenarios + 10 scenarios ×
30 replications, each over three day types = **5,100 run-days ≈ 765 days of wall
clock** at 25%.

**A fifth of it required no decision at all.** The grid was 7 × 5 × 4 over
`beta_transfer_penalty_min`, `walk_decay_beta_per_m` and `dwell_charging_s`.
**`walk_decay_beta_per_m` reaches the model through nothing** (issue #21): zero
occurrences in the generated config, and it is named in `not_representable` for
that reason. Sweeping it five ways produces a sensitivity band of exactly zero
**by construction**, which would be reported as *"insensitive to walk access"*
when the truth is *"walk decay is not in the model"*. That is a false negative in
a sensitivity analysis, and worse than an absent one.

**The grid is cut from 140 to 28 points**, and the axis returns the day the decay
curve reaches the model, not before. This is a defect fix, not a scope cut:
**112 of the 140 points could not have differed from another point for any reason
a reader would care about.**

The remaining cuts are scope decisions and were approved:

| cut | run-days | wall clock at 25% |
|---|---:|---:|
| as specified | 5,100 | ~765 days |
| drop the axis that reaches nothing | 1,740 | ~284 days |
| + sweep **weekday only** | 1,180 | ~193 days |
| + replications 30 → 5 | 430 | ~70 days |
| + sweep only the decisive contrasts (S2vS0, S2vS2b) | **262** | **~43 days** |

At 25% a run needs 31.5 GiB, so **two fit concurrently in 63.5 GiB** — roughly
**three weeks of wall clock**, which is the first version of this programme that
this machine can actually execute.

**Replications are to be measured, not assumed.** `E.replication.n_replications`
is 30 with a declared range of 5–30; the 5 above is a planning figure and the
value must come from **measured seed variance**, which is cheap. Until that
measurement exists the 5 is provisional and is recorded as such.

### 3. The two refusals are confirmed

Both were requested directly and both were declined; the user confirmed the
refusals stand.

- **The 143 holdout targets stay closed.** They are the only test the model has.
  The 67/143 split was fixed before any fitting precisely so that no target can
  move after a result is seen. They open **once**, at the end. A new observable
  becomes a **constraint** (the §9.8 / §9.13 pattern), never a target.
- **The 13 Opal card-type targets are not deleted.** They are calibration rows
  inside the pre-registered 210 and cannot be scored, because MATSim has no
  fare-product dimension. Deleting them retrospectively would change a set fixed
  in advance — the move that would let anyone quietly drop whatever the model
  fails at. They are reported with the reason instead.

### 4. Carried-over work from P0–P2, re-prioritised

Verifying the phase board (`STATUS.md`) found work carried from earlier phases
that no deliverable owned. Two items are now urgent for reasons that did not
apply when they were first listed.

**GTFS-Realtime collection was judged to be on the critical path here. That
judgement was overturned in §9.23 and this paragraph is superseded.** §13 item 10 says *"start now; it is the fallback for both dwell and
signal delay, and it accrues only forward."* **No collection exists** — verified,
the only reference in `src/` is a note naming it as an acquisition route. That
was tolerable while SCATS was merely unobtained. **§9.21 established that SCATS
is refused by policy**, which makes proposal §7.2's contingency the operative
path — and §7.2 requires signal delay to be *"inferred from GTFS-Realtime
run-time distributions."* **The fallback for the largest single uncertainty in
the model depends on a dataset nobody is collecting, and every day of delay is a
day of it permanently lost.** It is cheap to start and impossible to backfill.

**The corridor's road attributes are mostly imputed, and B3 rests on them.**
Measured over the 714 corridor and parallel edges:

| field | observed in OSM | imputed |
|---|---:|---:|
| speed limit | 639 | 75 |
| one-way | 475 | 239 |
| lane count | 435 | **279** |
| turn lanes | 70 | **644 absent** |
| kerbside | 36 | **678** |
| lane width | 10 | **704** |
| capacity | 0 | **714** |

§2.5's *"87.5% of as-built trunk lane counts are observed"* is true and is about
the **40 trunk edges**; it is not a statement about the 714. **Kerbside is 95%
imputed, lane width 98.6%, capacity 100%** — and B3, *"the decisive test of
Claim B"*, is precisely the hypothesis that turns on lane loss, banned turns and
kerbside parking removal. §13 item 4 named this and nothing owned it.

**Also carried, and now explicitly owned rather than floating:** the charging
dwell field measurement (§13 item 2, physical, one visit), pedestrian counts
(§13 item 6 — B1 has no observable at all without them), retail vacancy (§13
item 7 — `D.retail.vacancy_rate` is `unobtained` and B2 depends on it), the ABS
journey-to-work table (§13 item 11, obtainable, settles a swept parameter), and
the 2014 timetable (§13 item 8, validates the era-1 reconstruction).

**What this changes:** these are not P4 calibration work, and pretending
otherwise is how they stayed unowned. They are recorded in `STATUS.md` as
**carried-over deliverables with an explicit owning phase and priority**, and the
two urgent ones are issues rather than list items.

---

## 9.23 Own collection dropped, and what the published catalogue actually holds (P4 stage 8)

An Open Data Hub API key was obtained. That changed the option set that had made
own GTFS-Realtime collection look like the only path (§9.22), so the collector
built earlier in that stage was **reverted in full** and issue #26 closed as not
planned. This section records what the published catalogue was found to contain,
because the assessment is the thing that justifies the reversal.

### The archive that would have replaced collection covers the wrong modes

TfNSW publishes **Historical GTFS and GTFS Realtime** — trip updates, vehicle
positions and timetable — through `POST /v1/gtfs/historical`. Its documentation
says Metro and Ferry only. That was verified against the live API rather than
taken from the page:

| request | files returned |
|---|---|
| `FER` / `SydneyFerries` / `TripUpdate`, the documented sample dates | **3** |
| `MET` / `Metro` / `VehiclePosition`, 2024 and 2026 | **5** each |
| every light rail naming tried (`LRT`, `LR`, `NLR` × `NewcastleLightRail`, `LightRail`) | **0** |
| `BUS` / `Buses` | **0** |

The controls return files, so the empty light rail results are the archive's
content and not a malformed request. **The archive cannot backfill Newcastle.**

This leaves proposal §7.2's contingency for the SCATS refusal without a realtime
source. That is recorded as an **open gap**, not a solved one. What it does not
justify is standing up an unbounded rolling stream for months before the rest of
the catalogue has been worked: the published data settles several things the
stream never would, and it settles them today rather than in a quarter.

### The catalogue, enumerated

230 datasets, pulled from the CKAN endpoint
`/data/api/3/action/package_search` and matched against the registry's **6
unobtained** and **78 assumed** fields and the open issues.

### What it settles — verified against the data, not the title

**Traffic Lights Location — the strongest hit, and it lands on the corridor.**
4,582 signals statewide with `Equipment_ID`, cross streets, suburb, install date
and coordinates. **352 fall in the study area; all 14 distinct corridor
intersections in `A2_signal_control_corridor.csv` match one within 60 m** (most
within 10 m). Three consequences:

- `scats_site_id` in that artefact is a **declared but empty column** on all 70
  rows. `Equipment_ID` *is* the SCATS site number, so the column can be filled
  from an observed source.
- **8 of the 14 corridor signals were installed in 2018**, four of them in the
  September batch along Scott St and two named `LIGHT RAIL CROSSING`. The
  pre-light-rail corridor had **6** signalised intersections, not 14. That is an
  observed, dated basis for a counterfactual the model currently assumes.
- The signal inventory is currently OSM-inferred (`A2_signal_nodes_osm.csv`,
  1,265 nodes). This is an independent observed source to validate it against.

**Strategic Freight Model 2022 (SFM22).** NSW freight commodity movements on an
**origin-destination basis**, 20 commodity groups, road and rail, 2021–2061, as
a flat file with a data dictionary. Issue #24's freight layer currently has
nothing but a measured 6.52% heavy-vehicle share to work from.

**Reference Tables for TfNSW GTFS feeds.** Carries `IC-Hunter Line - Up` and
`- Dn` running-time tables (March 2026) and the turn-up-and-go frequency list.
Bears directly on `A.transit.era1_line_speed_kmh` and `era1_station_dwell_s`,
both assumed, and on the era-1 reconstruction that has no 2014 timetable.

**School and public holidays.** NSW public holidays and public-school term dates
as CSV. The RMS hourly counts carry dates, so this is the join that turns them
into a school-term / holiday / public-holiday stratification — which is what
`B.activity.sat_to_sun_rate` and the day-type shape need (§13 item 12).

**Covid-19 TfNSW Vehicle Capacity.** Vehicle capacity by transport class across
several restriction levels. Relevant to issue #18, with the obvious caveat that
a physical-distancing capacity is not a normal one; only a baseline column would
be usable, and it enters as `literature` with a url, swept — never `observed`.

**Opal Tap On and Tap Off, Release 3.** Tap counts by **time and location** for
four separate weeks in 2020, all four modes. Finer than the monthly series the
package holds. It is **not journey-linked** — there is no card-level chaining —
so `B.opal.journey_linked` stays `unobtained` and deliverable 8 keeps its §7.2
fallback.

### What it does not settle, recorded so it is not re-searched

- **No SCATS phase data anywhere in the catalogue.** §9.21 stands.
- **Kerbside, lane width, turn lanes and capacity for the corridor are still
  imputed.** The four datasets that look like the answer — Loading Zones
  Kerbside, Off-Street Parking, Bus Lanes, NSW Clearways and NSW Transit Lanes —
  are **Sydney-only** by their own descriptions, so the four fields #27 turns on
  still need their own survey. **One exception, verified since:** `speed_limit` is
  only 10.5% imputed (75 of 714 corridor edges) and Speed Zones is statewide, so
  that part is closable from published data.
- **Journey to Work 2016 was withdrawn by TfNSW** for re-identification risk and
  must come from the ABS. JTW 2006 and 2011 remain available with travel-zone
  geography, so `B.external.interaction_rate` can be settled on an older vintage
  or wait for the ABS extract.
- **Speed Zones** is statewide and covers Newcastle, but the CSV resource carries
  attributes with **no geometry**; the usable form is the shapefile.
- **Historic Roads Travel Time (TTDS)** is GPS speed traces with speed limits,
  which is the right shape for road signal delay — but only four weeks of 2016
  and two months of 2017, and its area coverage is unverified.

### What this does not do

No value has been changed. Nothing here has been acquired, written to
`data/raw/`, or entered in the registry: this is an assessment of what is
available and what it would settle. Each item above becomes an acquisition with
a provenance record and a registry field of its own, or it does not happen.
`A.lightrail.dwell_charging_s`, `A.signals.scats_phasing` and
`B.opal.journey_linked` all remain `unobtained` and swept.

---

## 9.24 The corridor signals acquire their real identity, and a dated counterfactual appears (P4 stage 9)

`A2_signal_control_corridor.csv` has declared a `scats_site_id` column since P2
and left it empty on all 70 rows. The corridor intersections are clusters of OSM
traffic-signal nodes, so they carried no identifier that anything outside this
package would recognise. TfNSW's **Traffic Lights Location** dataset (§9.23)
supplies one: `Equipment_ID` *is* the SCATS site number.

### The join, and why its tolerance is held fixed rather than swept

4,582 signals statewide, matched by distance to the 14 corridor intersections.
No bounding box is applied first — scanning the whole inventory is trivial, and a
bbox would be one more undeclared constant deciding which observations are
eligible.

**All 14 matched, at a mean of 8.0 m and a maximum of 26.4 m.** Nothing is
unmatched, and an unmatched intersection would have been written with
`scats_source='unmatched'` and blank fields rather than dropped or given a
neighbour's id.

`A.signals.scats_match_radius_m` is declared at 60 m and **held fixed**, not
swept. The rule is recorded in the registry: no behaviour, run time or score
reads it — only the identity written into the artefact — and every radius from
the 45 m OSM clustering distance up to roughly 100 m produces the identical
assignment, because the furthest true match is 26.4 m. Declaring a sweep
interval across which the output cannot vary is the defect this project has
already hit three times (issues #21, #12, and 112 wasted grid points). Departure
requires a re-measured distance distribution, not a preference.

This also migrates `build_corridor_layers.py` onto the registry, which it had
never read.

### Eight of the fourteen corridor signals were installed for the light rail

The inventory carries an installation date, now written to `signal_installed`:

| era | count | examples |
|---|---:|---|
| 2018 | **8** | 4762 *Stewart Av / light rail crossing* (Nov 2018), 4770 *Steel St / light rail crossing* (Nov 2018), 4766–4769 along Scott St (Sep 2018) |
| pre-2018 | 6 | 782 Hunter/Auckland (1973), 1655 Hunter/Darby (1981), 1875 Scott/Watt (1988) |

**The pre-intervention corridor carried 6 signalised intersections, not 14.**
That is an observed, dated fact about the counterfactual the B3 test rests on,
and the model currently assumes a corridor whose signal count does not vary by
era.

### What has deliberately NOT been changed

**Nothing downstream.** The date is recorded as an attribute and no scenario, no
variant and no parameter has been altered by it. `S0_no_tram` still carries all
14 intersections at a 100 s cycle, exactly as before.

**The decision was taken on 12 August 2026: no.** The pre-light-rail corridor
keeps all 14 signalised intersections in `S0_no_tram`, and the install dates
stay an attribute. Re-deriving the counterfactual from this observation would
reshape the same quantity that
`A.corridor.pre_lr_lanes_per_dir` encodes — and that constant *is* the B3
hypothesis, the decisive test of Claim B. Changing the hypothesis to fit an
observation discovered afterwards is the move proposal §9 names as the primary
threat to validity. It is held for an explicit decision, with the evidence now
on the table for that decision to be made against.

Note also what this does **not** supply: the inventory gives location, identity
and install date. It gives **no phase plan, no cycle time and no split**. SCATS
phasing remains refused (§9.21) and `A.signals.scats_phasing` remains
`unobtained` and swept. What has changed is that the corridor's signals can now
be named in a request, a citation or a SUMO controller — not that their
operation is known.

---

## 9.25 The specification audit: two inversions, not five miscalibrations (P4 deliverable 0a)

Deliverable 0a ran first because mode share was wrong in a way nobody had
explained, and calibrating on top of an unexplained error fits it into a
constant. The full ranked register is [`docs/audit/SPEC_AUDIT.md`](audit/SPEC_AUDIT.md);
this records what it changes.

**The symptom is two near-exact inversions, not five independent errors.** Car
-26.5 against ride +29.4, and walk -12.7 against bike +12.7. That pattern points
at structural asymmetries moving pairs of modes, not at five constants set
wrongly - which is why the audit looked at how modes are simulated rather than
at what they score.

**A1, and it is physically impossible.** `qsim.mainMode = car` while
`routing.networkModes = car,ride`, so `ride` is routed over the network and given
free-flow link times: it never queues and never contributes to congestion.
Measured over a completed 250-iteration run, **ride realises 55.7 km/h against
car's 49.3**. That aggregate overstates it - ride legs are longer and longer
trips use faster roads - and the corrected figure is **4-8%, present in every
distance bin from under 2 km to over 40 km**, which a composition artefact
would not survive. A car passenger arrives faster than the car carrying them.
The scoring config makes ride look *dominated* (identical time and money
disutility, and a -0.85 constant against car's 0.0), so nobody reading the
behavioural parameters would find this. It is worst exactly where car is most
congested, which is the peak and the corridor. Issue #28.

**A2 and A3 push the same way.** `ride` is not a chain-based mode while `car` is,
so a subtour adopts ride freely but must conserve a car; and the 9.11 ride
constraint is choice-set only, so one household driver can chauffeur unlimited
simultaneous passengers (#31). Separately, **car is the only mode whose ownership
is modelled** - bike is available to every agent always, and returns 15.86%
against an observed 3.2% (#29). A4 records that walk's 18x deficit may be a
trip-length problem rather than a scoring one, and names the test (#30).

**B1 is the finding that prevented damage.** Issue #24 states that work-related
business travel is an observed HTS purpose the model does not generate. **It
does.** B2 carries 47,612 weekday `WB` legs, **2.11%** of all legs, against an
HTS Newcastle figure of **2.0%**. Building it as scoped would have double-counted
an already-correct purpose and moved mode share for a reason no later run could
attribute. #24 is narrowed to freight, which does stand, as does #20 - external
legs are 0.48% of the total and every one terminates inside the study area.

**A caution about the registry's own defect detector.** `consumers` is generated
from read logging and is stale: three light rail capacity fields list no
consumers while `build_matsim_run_inputs.py` reads two of them. An empty
`consumers` means the generator has not seen the field, **not** that nothing
reads it, so it can neither confirm nor deny reach. Reach must be established by
changing a value and observing the output. This matters because "a declared,
swept parameter that reaches nothing" is a defect class this project has hit
three times and `consumers` is the mechanism used to catch it.

**Deliverable 0e is already satisfied** and its checklist entry was stale: the
`water` and `green` layers are annotated *"for the run replay basemap only"* in
`overpass.py` and are consumed by `build_basemap.py`.

**Nothing was changed by this audit.** No parameter, no target, no scenario. The
67/143 split is untouched and no holdout row was opened. The audit's product is
a register and four issues; the fixes are separate work, and #28 must land before
#9 is re-solved or #14 is attempted, because both would otherwise absorb it.

---

## 9.26 The passenger stops outrunning the driver, and the car–ride inversion mostly closes (P4 stage 10, issue #28)

> **CORRECTED BY §9.27.** The mode-share figures below were measured with both
> arms at 250 iterations, and that protocol is now known to sit ~13 percentage
> points of car share short of relaxation. The pre-fix model run to 1000
> iterations reaches a **better** fit (33.8 pp) than the post-fix model at 250
> (44.6 pp), so **most of the movement claimed here was the absence of
> relaxation, not the fix**. The physics defect and the fix stand; the claim that
> this was "the largest single correction" does not. Read §9.27 first.

§9.25 A1 found that `ride` sits in `routing.networkModes` but is not the qsim
`mainMode`, so MATSim routed it over the network on **free-flow** link times: a
car passenger never queued, never waited, and never met the congestion the
driver met. `CitysimControler` now binds `ride`'s travel time to
`networkTravelTime()` and its disutility to the car factory, so a passenger is
priced with the congested car times.

It deliberately does **not** put a ride vehicle in the mobsim. A passenger
travels in a car that is already there; a second vehicle would double-count the
traffic. So `ride` now *experiences* congestion without *causing* it — correct
only insofar as every ride trip is paired with a driver trip, and it is not.
That is issue #31, still open.

### What it moved

Two runs at 10%, 250 iterations, seed 20260810, 8 threads — **identical but for
the controler**. Newcastle LGA, linked trips, the figures comparable to the
target (§9.13):

| mode | before | after | change | target |
|---|---:|---:|---:|---:|
| car | 32.54% | **52.30%** | **+19.76** | 59.0% |
| ride | 50.03% | **29.45%** | **−20.58** | 20.6% |
| walk | 0.75% | 0.71% | −0.03 | 13.4% |
| bike | 15.86% | 16.67% | +0.81 | 3.2% |
| pt | 0.83% | 0.88% | +0.05 | 3.8% |

**Total absolute gap to target: 84.2 → 44.6 percentage points.** The largest
single correction this model has had, and it came from a defect rather than a
constant.

**It also confirms the audit's central claim.** §9.25 argued the symptom was
*two* inversions, not five miscalibrated constants. Fixing the car↔ride
mechanism moved car and ride by ±20 points and left walk↔bike **untouched**
(−0.03 / +0.81). Two independent mechanisms, exactly as the register predicted.
Walk and bike are #30 and #29.

### The defect is reduced, not eliminated

Ride is still faster than car at matched distance. Both runs, ride/car speed
ratio by leg distance:

| distance | before | after |
|---|---:|---:|
| 0–2 km | 1.08× | **1.11×** |
| 2–5 km | 1.08× | 1.07× |
| 5–10 km | 1.08× | 1.05× |
| 10–20 km | 1.06× | 1.04× |
| 20–40 km | 1.04× | 1.02× |
| 40 km+ | 1.04× | **1.01×** |

The advantage collapses on long trips and **grows on short ones**. Two
mechanisms are consistent with that and this section does not separate them: the
router prices `ride` from the *previous* iteration's travel times while `car`
realises the current one, which matters more the further from relaxation the run
is (#5); and a teleported leg never pays the junction queueing that dominates a
short trip. **#28 stays open on the residual.**

### Why the first verification was thrown away

It ran at 1% and was uninterpretable. §15 records that MATSim floors link storage
at one vehicle, so a 1% sample produces **spurious spillback that inflates car
delay** — and `ride`, being teleported, is immune to precisely that. It
penalises car by construction and widens the gap the fix exists to close. It
duly showed ride 1.14–1.25× faster, which says nothing. **A fraction-sensitive
artefact makes a cross-fraction comparison invalid**, so the verification was
re-run at the baseline's own 10%.

### Two reproducibility defects the fix exposed

**Nothing compiled the Java.** `run_matsim.py` runs `citysim.CitysimControler`,
the source is committed, `.tools/` is gitignored, and no script built one from
the other — the classes had been made by hand. A fresh clone held the source,
the jar, and no way to run. `bootstrap_toolchain.py` now compiles with the
pinned `javac` against the pinned jar, on the fetch path and the `--verify` path.

**A run record could not say which controler produced it.** The run name is built
from the scenario and the registry values, which cannot see the controler.
Re-running after this change would have found the old `_run.json` and returned
the **pre-fix** result silently, with nothing to tell the two apart. Records now
carry `controler_sha256` over the committed Java source, it is declared in the
run contract, and the harness re-runs rather than resuming across a change. It is
also why the verification ran under its own tag: the harness deletes a run
directory before repeating it, and the only pre-fix baseline in existence sat in
the directory the new run would have claimed.

### What this is not

**Not a result.** 250 iterations is measurably short of relaxation (§9.7), the
demand still lacks boundary through traffic and freight, and no count-based
calibration may be read from it (§9.14). **No target was fitted**: the mode share
moved because a defect was removed, not because anything was tuned. No parameter
value changed, the 67/143 split is untouched, and no holdout row was opened.

---

## 9.27 The model needs a thousand iterations, and most of §9.26 was measuring their absence (P4 stage 10, issue #5)

The 1000-iteration pilot at 10% finished: 41,860 s wall, median 34.2 s/iteration,
rc=0. It answers issue #5 and it **overturns the headline of §9.26**, which was
written before it landed.

### 250 iterations is not near relaxation, and every result to date used it

Largest single-mode change in the chosen-mode series across a window:

| window | max change | |
|---|---:|---|
| 100 → 250 | 0.1316 | |
| 250 → 500 | 0.0682 | |
| 500 → 800 | 0.0297 | |
| 800 → 900 | 0.0339 | innovation switches off at 800 |
| 900 → 950 | **0.00026** | flat |
| 950 → 1000 | **0.00032** | flat |
| 990 → 1000 | **0.00008** | flat |

The model relaxes about **100 iterations after innovation is disabled**, and is
flat from 900. Between the 250-iteration protocol and relaxation, chosen car
share moves **+0.1324** — thirteen percentage points.

**Every run this project has produced used 250 iterations.** DECISIONS.md §9.7
called that short; this measures how short.

### The correction to §9.26

§9.26 reported the #28 controler fix as *"the largest single correction this model
has had"*, on a 44.6 pp total gap against an 84.2 pp baseline. **Both figures were
taken at 250 iterations, and that baseline was broken.** Newcastle LGA, linked
trips:

| run | car | ride | walk | bike | pt | total gap |
|---|---:|---:|---:|---:|---:|---:|
| pre-fix, 250 iter | 32.54% | 50.03% | 0.75% | 15.86% | 0.83% | 84.2 |
| **pre-fix, 1000 iter** | **65.01%** | **22.25%** | 0.13% | 12.41% | 0.19% | **33.8** |
| post-fix, 250 iter | 52.30% | 29.45% | 0.71% | 16.67% | 0.88% | 44.6 |
| *target* | *59.0%* | *20.6%* | *13.4%* | *3.2%* | *3.8%* | |

**The pre-fix model, simply run to relaxation, fits better than the post-fix
model at 250 iterations.** So most of the ±20 point movement attributed to the
controler fix was the absence of relaxation, not the fix. The car↔ride inversion
was largely an artefact of reading an unconverged run.

This is the failure mode the specification audit exists to catch, produced by the
audit's own follow-up: a controlled comparison, correctly executed, at a protocol
that was itself invalid. **A comparison is only as good as the state both arms
are in.**

### What survives, and what changes

**The physics defect is not in question.** `ride` outran `car` at *every* matched
distance band, which is impossible for a passenger travelling in that car, and
the binding demonstrably narrows it (1.08→1.05 at 5–10 km, 1.04→1.01 above
40 km). The fix is correct and stays. What is withdrawn is the claim about how
much of the mode-share gap it closes; that is now being measured properly, by a
post-fix run at the same 1000 iterations, under its own tag so the pre-fix
relaxed baseline survives.

**The walk↔bike inversion is confirmed structural.** At relaxation it does not
improve — walk **0.13%** against 13.4% and bike **12.41%** against 3.2%, if
anything worse. Iterations do not touch it. §9.25's two-inversion reading holds,
but the two have different natures: car↔ride was mostly protocol, walk↔bike is
mechanism, and it is issues #30 and #29.

### Issue #5, and why it is not closed

The measured answer is **~1000 iterations**, with the caveat that
`fraction_to_disable_innovation` is a *fraction*, so a 900-iteration run would
disable innovation at 720 rather than 800 — this run shows that 1000 works, not
that 900 would.

`RUN.controler.last_iteration` **stays `unobtained`**. This measurement is on the
**pre-#28** model, and #29 and #30 will change the mode-choice landscape again.
Pinning a value measured on a specification that is being repaired would be
substituting one unjustified number for another, which is the whole reason the
field refuses a point value. It is re-measured once the mode-choice defects are
settled.

**The practical consequence is immediate regardless:** no run at 250 iterations
means anything, including every run in `results/` and both arms of §9.26.

---

## 9.28 Walking was priced with the parameter for walking to a bus stop (P4 stage 11, issues #29, #30)

**This section is written before the change it authorises and before any run on
the changed specification**, because it logs a departure from §8.5 and §8.5's own
rule is that a departure must be recorded before results are seen.

### The defect: one parameter, three broken mode shares

`src/build/build_matsim_run_inputs.py` translates C1 into MATSim scoring through
`traveling(weight) = performing − vot_avg × weight`. Two of its five calls are
wrong.

```python
'walk': marginalUtilityOfTraveling=traveling(w['beta_walk_access']['base'])   # 2.0
'bike': marginalUtilityOfTraveling=traveling(1.3)                             # a literal
```

**`C.time_weights.beta_walk_access` is the appraisal weight on walk access time
*inside a public transport journey*** — the penalty for walking to a stop, where
walking is an unwanted addition to a PT trip. It is not the value of time for a
walking trip. Applying it to the `walk` *mode* prices an entire walking journey
at twice in-vehicle time. This is the hazard §9.3 recorded as *"what C1 loses in
translation to MATSim scoring"*, realised.

MATSim's effective travel disutility is `performing + |marginalUtilityOfTraveling|`:

| mode | weight | effective util/hr | speed | **util per beeline-km** |
|---|---:|---:|---:|---:|
| car / ride / pt | 1.0 | 16.96 | measured | 0.61 (car) |
| bike | **1.3, a literal** | 22.05 | 15.12 km/h | **1.896** |
| walk | **2.0, the PT-access weight** | 33.92 | 3.78 km/h | **11.666** |

With `C.asc.walk = +0.35` and `C.asc.cycle = −1.35`, walk and bike are
indifferent at **174 m beeline (226 m network)**. `C.constraint.trip_length_km.walk`
records the observed mean walk trip as **0.7 km**. **Essentially no observed
walking trip falls inside the window where this model would choose to walk**, and
the resulting 0.13% share is arithmetic rather than behaviour.

### It is also half the PT collapse

MATSim scores access, egress and transfer walk legs with the **`walk` mode
parameters**, in the scoring function and again in the router's generalised cost.
A 5 km PT trip with 400 m access and egress, 10 min wait and one transfer costs
**−18.29 utils before any in-vehicle time**, of which **−9.33 (51%) is the walk
at each end**. That fixed cost equals 57 minutes of car driving. **Walk and PT
are one failure, not two**, which corrects §9.25's note that PT was "plausibly
downstream of A1–A3".

### The benchmark, from committed configs of calibrated scenarios

Effective travel disutility relative to car:

| scenario | car | pt | bike | walk |
|---|---:|---:|---:|---:|
| Open Berlin v6.4 | 1.00 | 1.00 | 1.00 | 1.00 |
| Leipzig v1.3.1 | 1.00 | 1.58 | 1.92 | 0.94 |
| Kelheim v3.1 | 1.00 | 1.00 | 1.50 | 1.00 |
| Düsseldorf v1.0 | 1.00 | 1.23 | 1.15 | 1.15 |
| **Melbourne AToM** (estimated on VISTA, n = 14,959) | 1.00 | 1.01 | **1.21** | **1.04** |
| **Newcastle, as built** | 1.00 | 1.00 | **1.30** | **2.00** |

**No published calibrated MATSim scenario prices walking above ~1.15× car.** The
Australian model estimated on Australian revealed preference uses 1.04×, and has
**cycling time dearer per hour than walking** — Newcastle has that ordering
inverted. Australian appraisal guidance is independently consistent: ATAP M1 and
the TfNSW Economic Parameter Values both put the walk *access* weight at **1.5**,
and Wardman's meta-analysis of 3,109 valuations at **1.45**. Even for the
quantity it was meant for, 2.0 sits at the top of the range.

### Why fixing destination placement first would have made it worse

Issue #30 is real — the model carries **4.9%** of trips under 1 km where national
travel surveys report 14–23% (US 2009 NHTS 19% under 1 mile; MiD 2023 ~23% under
1 km; ODiN 2024 14.4%). But at a 174 m crossover the recovered short trips would
go to **bike**, not walk. In every observed system walking takes the shortest
band — 61% of US sub-0.8 km trips, 81% of German sub-0.5 km trips, 62% of Dutch
sub-1 km trips, and NSW HTS puts walk at 71% of sub-1 km trips. **The scoring is
repaired first and #30 second.** This reverses the order §9.25 implied.

Recorded so it is not mistaken for a target error: roughly a quarter of sub-km
NSW trips *are* driven, and that behaviour is already inside the 13.4% walk
target. The target is not misread.

### Live MATSim defaults that no one set

`output_config.xml` from a completed run — MATSim's own fully resolved config,
which is the only place a live default is visible — shows the mode-choice and PT
router running entirely on defaults that every comparator scenario overrides:

| parameter | Newcastle | comparators | consequence |
|---|---|---|---|
| `maxBeelineWalkConnectionDistance` | **100 m** (default) | 300 m (Berlin, Leipzig, Kelheim) | see below |
| `probaForRandomSingleTripMode` | **0.0** (default) | 0.5 | no single-trip escape from a bike subtour |
| `subtourModeChoice.behavior` | `fromSpecifiedModesToSpecifiedModes` | `betweenAllAndFewerConstraints` | **an agent with an open subtour cannot change mode at all** |
| `coordDistance` | **0.0** (default) | 100 | two activities metres apart are not one subtour location |

**Measured consequence of the first, at Newcastle Interchange**, from the
S2 × WEEKDAY schedule:

| from light rail | to | distance | reachable |
|---|---|---:|---|
| Newcastle Interchange LR | Stand A, local bus | 49.0 m | yes |
| Newcastle Interchange LR | heavy rail platforms 1–3 | 53.9–57.8 m | yes |
| Newcastle Interchange LR | Stand B, local bus | 95.1 m | yes, by 4.9 m |
| **Newcastle Interchange LR** | **Stand C — `regionbuses`, `nswtrains`** | **119.2–139.0 m** | **no** |

Nothing backstops it: the schedule carries **zero** `minimalTransferTimes`, and
**none of the five raw TfNSW feeds contains a `transfers.txt`** — so this is a
source-data gap, and every interchange in the model is created by that one unset
parameter. **Claim A's hypothesis A3 falsifies on generalised journey time rising
for external-origin OD pairs, and Stand C is the external-origin connection.**
The Auditor-General's finding concerned travellers originating outside the city
centre specifically. `C.transfer.beta_transfer_penalty_min`, swept 3–15 as the
parameter the policy question turns on, has been priced against a transfer set
missing that connection.

### The §8.5 departure, logged before results

**Departed from:** §8.5 holds `C.asc.cycle` fixed at the prior −1.35.

**Departure:** `C.asc.cycle` opens a sweep of **[−4.0, −1.35]** and its status
becomes `placeholder`, to be **constrained** — not calibrated — against the
observed walk:bike split by distance band, on the pattern §9.8 established for
`C.asc.car_passenger`. The constraining quantity is an observed distributional
fact about which mode wins at which distance, not a patronage level and not a
mode share the hypotheses turn on.

**Why this is not ASC absorption.** The constant being opened is *cycle*.
`asc_light_rail`, `asc_bus` and `asc_rail` stay at their §8.5 priors and are
untouched, so no hypothesis in proposal §3 turns on it. The point value is **not
moved in this change** — only the sweep is opened and the departure recorded —
because a hand-set −3.0 would be substituting one unjustified number for another,
which is what §8.5 exists to prevent. The constrained solve is built after the
scoring repair, not before, since calibrating a constant against a known
structural error is exactly the failure proposal §9 names as the primary threat
to validity.

**Not departed from:** the 67/143 split is untouched, no holdout row was opened,
no target value changed and no falsification condition was altered.

### One research claim falsified during checking, and one of my own withdrawn

`accessEgressType` **is** active (`accessEgressModeToLink`), confirmed from the
resolved config, against a research finding that it defaulted to `none`. §9.15
stands and car does pay a walk to the network.

The claim that the teleported walk speed was set too slow is **withdrawn**. ATAP
M4 gives average walking at 4 km/h; `RUN.routing.teleported_walk_speed_ms` = 1.05
(3.78 km/h) is consistent with it. **The speeds are not the defect; the
coefficients are.** What survives is an internal inconsistency worth closing
separately: `A.transit.walk_speed_ms` is 1.25 while
`RUN.routing.teleported_walk_speed_ms` is 1.05, both labelled `literature`.

The teleported *bike* speed is left at 4.2 m/s with its sweep widened rather than
repinned, because the two sources disagree and neither was dismissed: published
MATSim practice is 3.14 m/s (Kelheim, Düsseldorf, eqasim) while ATAP M4 gives
average cycling at ~15 km/h, which is what 4.2 m/s encodes. The sweep is widened
to reach both rather than a value being chosen between them.

### Still open, and stated so

Car pays **no parking charge anywhere in the scoring** and carries no
`dailyMonetaryConstant`; its 0.18 utils/km is roughly half the Australian
estimate. In a study whose subject is city-centre access this is a real omission,
recorded here and not fixed in this change.

**Nothing in this section is a result.** No scenario has been run on the changed
specification.

---

## 9.29 The registry is named for the city it describes, and the harvest box was clipping the study area

### The naming

`config/registry/` held eight files of values, every one of them Newcastle's,
under a name that said nothing about that. `config/schema/` is the portable
half — what any city must supply and in what shape — so the instance is now
`cities/<city>/registry/`, selected by `CITYSIM_CITY` and defaulting to
`newcastle`. `load_registry()` already took a directory override, so the seam
existed; only the name was missing.

The distinction matters because it is easy to mistake a generic *key* for a
generic *value*. `A.road.speed_default` is a portable field name. 50 km/h
residential, 16.96 AUD/h and a 0.50 bicycle ownership rate are not portable
values, and a directory called `registry` invited exactly that confusion.

### The defect the naming exposed

Asked to declare parking prices "via schema inputs", the first attempt wrote
**four hand-drawn Newcastle lat/lon rectangles into the registry** and called it
a schema. That is not an input schema, it is a hardcoded constant that has moved
house. It was reverted, and the question — *where else is there a hand-drawn
rectangle?* — found one that matters.

`src/extract/overpass.py` harvests OSM inside a typed-in extent,
`STUDY = (-33.20, 151.10, -32.55, 151.95)`. Against the actual boundaries in
`data/processed/zones/zones_LGA.gpkg`:

| | study area, 5 LGAs | harvest box | |
|---|---:|---:|---|
| West | 150.8013 | **151.1000** | ~28 km cut off |
| East | 152.2055 | **151.9500** | ~24 km cut off |
| South | −33.2028 | −33.2000 | marginal |
| North | −32.5788 | −32.5500 | box larger, harmless |

The road layer reaches 151.0316–152.0118 because OSM returns whole ways that
cross the boundary. Measured against that true extent rather than the box:

**87 of 1,500 core SA1s (5.8%) lie outside the road network — 86 in Port
Stephens, 1 in Lower Hunter.** Core SA1 centroids span 150.9683 to 152.1766.

Core tier means full demand generation, so those zones synthesise population and
activities over ground that has no modelled road. That is the §9.15 pathology —
agents with no road to reach — and §9.15 was diagnosed as an *external-tier*
problem because nobody checked whether core zones had the same exposure.

### The behavioural consequence, now measured

Measured on `results/ride_fix_10pct` (10%, post-#28), comparing agents homed in
the 87 unreached SA1s against every other core agent. **31,940 agents live
there, 5.21% of 612,668.**

| | other core | **unreached** | ratio |
|---|---:|---:|---:|
| trips observed (10% sample) | 213,634 | 10,480 | |
| median trip length | 7.69 km | **24.86 km** | **3.2×** |
| mean trip length | 10.72 km | 27.05 km | 2.5× |
| access + egress walk on a car/ride trip, median | 0.095 km | **0.364 km** | **3.8×** |
| …mean | 0.131 km | 0.698 km | 5.3× |
| …90th percentile | 0.225 km | **1.454 km** | **6.5×** |

Mode split, same two groups:

| | car | ride | walk | bike | pt |
|---|---:|---:|---:|---:|---:|
| other core | 52.8% | 30.9% | 1.0% | **14.8%** | 0.5% |
| **unreached** | 33.6% | 26.7% | 3.1% | **36.5%** | 0.1% |

**This is the §9.15 signature exactly.** An agent with no road near home pays a
large access walk to reach one, and flees to the mode that is teleported and
therefore immune to the penalty. Bike at **36.5%** against 14.8% is that flight,
and car is depressed 19 points to pay for it.

**Blast radius, stated so it is not overstated.** None of the 87 zones is in
Newcastle LGA — 86 are Port Stephens, 1 Cessnock — so `newcastle_lga_pct`, the
reportable mode-share metric, is **untouched**. The contamination is on the
five-LGA aggregate, which §9.13 already says must not be reported, worth roughly
**+1 percentage point of bike**; and on network-wide count fit, since 60% of
these trips are car or ride and do load the network, at a median 24.86 km. The
corridor is ~50 km away and is not measurably affected.

So the defect is **real, confirmed and bounded**. It is not a reason to pull the
extent fix ahead of the demand batch, which was the condition set for doing so.

### Why a typed rectangle is worse than a wrong number

A wrong parameter is caught by a sweep, a drift check or a reviewer reading the
registry. **A typed-in rectangle is caught by nobody**, because it looks like
scope rather than like an input. The rule added to `CLAUDE.md` is therefore
about derivation, not declaration: an extent should come from a boundary file or
a tag that any city also has. `zones_LGA.gpkg` is already in the package, so the
harvest extent is `boundaries ∪ margin` and can be computed.

The same applies to parking. The reverted rectangles priced 646 facilities;
OSM's own `fee` tag observes **472 `yes` and 640 `no`** across the 7,710
facilities, so priced-ness moves from `assumed` to `observed` for 1,112 of them
and works in any city. The price *level* stays assumed and swept — `charge` is
tagged on **1** facility — but that is a smaller assumption than drawing the
zones by hand.

### Not fixed here

Deriving the harvest extent means **re-harvesting OSM and rebuilding the
network**, and §3.5 makes every existing run incomparable across a re-map. That
is a scope decision, not a defect fix, and it is recorded rather than taken. The
cost is at its lowest now — every run on disk is already invalidated by the
250-iteration protocol (§9.27) — and rises once the repaired-model run programme
starts.

**No value changed in this section.** The registry files moved; their contents
are byte-identical. `check_package.py` and the drift check pass unchanged.

---

## 9.30 The fleet carries the capacities that were published (P4 deliverable 0c, issue #18)

§9.18 corrected the light rail vehicle and left the other three on pt2matsim's
generic defaults, recorded at the time as *"a stated limitation, not an
oversight"*. §9.21 then found published figures for all of them. This applies
them, which closes deliverable 0c.

| vehicle | mapped default | published | now |
|---|---|---|---|
| Bus (Volvo B12BLE) | 70 seats, **0 standing** | 44 seated + 18 standing | **44 / 18 = 62** |
| Ferry (MV Shortland, MV Hunter) | 250 seats, **0 standing** | 200 total, 149 seated | **149 / 51 = 200** |
| Rail (Hunter two-car set) | 400 seats, **0 standing** | 77 + 69 = 146 | **98 / 48 = 146** |
| Tram (CAF Urbos 100) | 180 seats, 0 standing | 270 total | 60 / 210 = 270 (§9.18) |

**Every default overstated the real vehicle** — rail by roughly 2.7× on a
two-car set, ferry by 25%, bus seats by about 59%. That is consistent with
§9.12's finding that transit capacity never binds: some of the headroom was
fictional.

**The larger defect was that no vehicle in the fleet had standing room at all.**
The C1 crowding multipliers — seated 1.00, standing 1.45 — could therefore never
apply in any scenario, because standing never occurred anywhere. They were
declared, swept and unreachable, the #21 defect class. All four vehicle types
now carry standing room, so crowding can bind.

### What is published and what is not

Only the **ferry** split is published, so neither half of it is assumed and both
are `held_fixed` — a vessel capacity is a fact about the boat, not a behavioural
parameter, and sweeping it would assert an uncertainty that does not exist. The
schema enforced this: `literature` with no sweep and no `held_fixed` rule does
not validate, and the first attempt was rejected.

**Bus** carries a published seated *and* standing figure, swept across the two
Volvo models Newcastle actually runs — B12BLE 44 seated, B10B 51 — so the
interval is the observed spread of stock in service rather than a chosen range.

**Rail** publishes only per-car capacity, so the seated share is assumed at two
thirds and swept 80–120, and standing is derived by identity. Same treatment as
the tram at §9.18: only the *split* is assumed, and the total it comes from is
published.

**None of this is observed for Newcastle operations.** These are manufacturer
and operator figures, labelled `literature`, and the capacities are per vehicle
as scheduled — no allowance is made for a set running short.

**Registry 178 → 186 fields.** `check_package.py` 1,107 → **1,245 checks**: every
vehicle type in every one of the 30 run-input sets is asserted to carry standing
room, which is the property rather than the numbers, so the seated sweeps stay
free to move. **Nothing was run.**

---

## 9.31 A car stops parking for free, and the price stops being a drawn rectangle (P4 stage 13, issue #33)

Parking price is the prime competitive lever between car and public transport
for a city-centre trip, and this study is about city-centre access. The model
did not have one. Two defects met in the same file.

### The price was declared and reached nothing

`data/processed/landuse/A5_parking_facilities.csv` has carried `is_priced`
(646 of 7,710 facilities), `price_aud_hr`, `price_sweep_low`/`_high`,
`max_stay_min_modelled` and a `price_schedule` string since P1. **No script read
any of them.** `check_package.py` asserted only that the file existed. This is
the "declared, swept value that reaches nothing" class on its **sixth** instance
— after #12, #21, the walk decay, the gradient, and the seven config-template
literals at §9.28.

### The spatial basis was four hand-drawn rectangles, and one could never match

`build_landuse_parking.py` defined `PARK_ZONES`: four lat/lon boxes with place
names, each carrying a literal price, a literal max-stay and a hand-typed
24-value occupancy profile.

| zone | box (s, w, n, e) | AUD/h | max stay | facilities matched |
|---|---|---|---|---|
| `cbd_core` | -32.9320, 151.7680, -32.9200, 151.7880 | 3.20 | 120 | 203 |
| `cbd_fringe` | -32.9380, 151.7550, -32.9180, 151.7950 | 2.40 | 180 | 465 |
| `honeysuckle` | -32.9300, 151.7550, -32.9200, 151.7750 | 2.40 | 240 | **0** |
| `beach_east` | -32.9350, 151.7800, -32.9150, 151.8000 | 2.00 | 240 | 4 |

`honeysuckle` is **fully contained in `cbd_fringe` on all four edges**, and
`cbd_fringe` is tested first in the same first-match-wins loop. It could never
match a facility and never did. A declared parking zone with its own price,
max-stay and occupancy profile, geometrically dead, unnoticed for three phases —
because a typed rectangle cannot be wrong in a way anyone notices. That is the
#32 lesson and the CLAUDE.md hard constraint, both restated by the same file.

### What was not used

OSM `fee=yes` looks like observed pricing. **452 of the 472 tagged facilities
are University of Newcastle car parks** at Callaghan, a median 7.8 km from the
centre; the CBD's own paid parking is untagged. Reproduced on
`data/processed/network/A5_parking_osm.csv` before anything was built on it,
per the rule that a defect is reproduced before it is attributed.

### The replacement: the city's own job-density distribution

    price(zone) = A.parking.price_aud_hr_max
                  x clamp((dens - thr) / (sat - thr), 0, 1)

`dens` is jobs per km² from `data/processed/landuse/D1_zone_attractions_SA1.csv`;
`thr` and `sat` are percentiles of **that city's own core-zone distribution**, so
a new city computes its own thresholds and no extent is ever typed. `zone_tier`
is a tag any city's zone build produces.

| quantity | value |
|---|---|
| core-zone job density p50 | 103.0 jobs/km² |
| p90 → `thr` | 1,500.9 jobs/km² |
| p99 → `sat` | 8,710.5 jobs/km² |
| core zones priced | 150 of 1,500 |
| all zones priced | 162 of 1,701 |
| car links priced (per scenario) | 22,353 of 143,891 |
| car links inside any SA1 | 95.7% — the rest are outside the zone system and free |

New fields, all `assumed` and swept, in `config/registry/newcastle/A_supply.json`:
`A.parking.price_threshold_pctile` 90 [80, 95], `A.parking.price_saturation_pctile`
99 [95, 99.5], `A.parking.price_aud_hr_max` 3.20 [1.60, 4.80],
`A.parking.max_stay_min` 120 [60, 180], `A.parking.charged_hours_by_day_type`
(WEEKDAY 08–18, SAT 08–13, SUN none) and `A.parking.exempt_activity_types`
`["home"]`. `A.parking.charged_modes` is `definition` — only the driver parks.
`A.parking.free_occupancy_profile` became `A.parking.occupancy_profile`: it now
applies to every facility, because the four per-zone profiles it replaced were
hand-typed per drawn box, rested on no observation and reached no consumer.

**The charge cap.** `max_stay_min` doubles as the cap — `price × min(duration,
max_stay)`. This **under-charges** a long stay. Declared, not hidden: modelling
over-stay properly needs an infringement rate nobody has measured here.

### Two additions beyond the formula, both deliberate

**Charged hours.** SUN is one of three day types and charging Sunday at weekday
meter rates would be wrong. The assumption already existed — A5's own
`price_schedule` string asserted "Mon-Fri 08:00-18:00; Sat 08:00-13:00; else
free" where it reached nothing. It is now a swept registry field, and the
handler charges the overlap of the parking spell with that window.

**Home is exempt.** A car is parked from arrival until the *next car departure*,
so without an exemption every agent who drives home is charged the max-stay cap
every night for living in a dense zone — a standing levy on city-centre
residence rather than a price on a travel choice. Swept against the empty set.

### How it reaches the model

`ParkingChargeHandler` (`src/java/citysim/`) emits a `PersonMoneyEvent` per
parking spell, on the precedent of `RideAvailabilityModesCalculator`. A spell
runs from a **car arrival to the next car departure**, not merely for the
following activity, so an agent who parks and walks onward is charged for the
whole spell. Charges accumulate during the mobsim and are emitted in
`notifyAfterMobsim` — the pattern MATSim's roadpricing contrib uses, because
emitting from inside a handler re-enters the events manager. **roadpricing is
not in the pinned jar** (only its DTD ships), so the pattern is reproduced, not
reused. `ParkingConfigGroup` makes `parking` a real typed module, so an
unrecognised parameter fails the run and the module appears in the output config
dump. The link→price table is built once per scenario by
`build_matsim_run_inputs.py`; **Java does no spatial work at all**.

### Reach established by changing values, not by reading `consumers`

`consumers` is a read log and cannot prove reach. Four smoke arms on S0
(2 iterations at 1% — plumbing tests, **not results**, and no mode share from
them is quoted anywhere):

| arm | parking charges | total AUD | largest single |
|---|---|---|---|
| WEEKDAY, `price_aud_hr_max` 3.20 | 526 | −721.42 | −6.40 |
| WEEKDAY, `price_aud_hr_max` 1.60 | 527 | −361.62 | −3.20 |
| SUN, 3.20 | **0** | 0.00 | — |

Halving the price halved the total (ratio 0.5013; the residual is one extra
charged agent from replanning). The largest single charge is exactly
`price_max × 2 h`, the cap. Sunday charges nothing. Charges are 1:1 with car
arrivals at the charged link.

**The reach test caught a real defect.** The first arm charged 641 spells, **267
of them at links where the person's real activity was home** — the exemption was
matching nothing. `routing.accessEgressType` is `accessEgressModeToLink` by
MATSim's own default, so the activity immediately following a car arrival is the
synthetic `car interaction`, not the destination. The handler now skips stage
activities via `TripStructureUtils.isStageActivityType` and waits for the real
one. Charges fell 641 → 526 and `home` disappeared from the charged set. Had
this shipped, every agent living in a dense zone would have paid a nightly levy
that no observation supports.

### What this formula gets wrong, measured rather than supposed

Job density alone does not distinguish a city centre from a suburban shopping
centre. The ramp prices **Westfield Kotara (8,709 jobs/km²), Stockland Glendale
(13,338) and Charlestown** at or near the 3.20 maximum, and parking at all three
is free in reality.

A contiguity refinement was built and **rejected on the evidence**. Taking the
zones above `thr` and joining those that share a boundary gives a strikingly
bimodal result — one cluster of **80 zones / 62,770 jobs** centred on Newcastle –
Cooks Hill, and 49 clusters of **1 to 5 zones**, with nothing in between. A
minimum-cluster-size rule would therefore separate the centre cleanly. It was
not adopted because it also excludes **the University of Newcastle (a singleton,
3,015 mapped facilities) and John Hunter Hospital**, the two places outside the
centre that verifiably *do* charge. It trades one error for another, so it buys
complexity rather than correctness. The diagnostic is recorded here so a future
decision starts from the measurement.

**Bearing on the study.** Parking price is identical across S0–S6 — E1's parking
variants change corridor kerbside *supply*, not price — so a mispriced zone
largely differences out of the scenario comparison. It does affect the **base
calibration**, where the ASCs would absorb part of it. That is the reason to fix
it before deliverable 5, not after.

### Not fixed here, filed instead

`build_landuse_parking.py` carries a **fifth** hand-drawn rectangle,
`CBD = dict(s=-32.9450, w=151.7250, n=-32.9050, e=151.8050)`, driving the D1
frontage segments that hypothesis B1 rests on. Different blast radius, its own
decision: **issue #34**, which also records that the damage must be measured
before it is fixed. Noted for calibration: car still carries **no**
`dailyMonetaryConstant` and pays 0.18 utils/km against Melbourne AToM's
estimated 0.365.

### Guarded structurally, not by memory

`check_package.py` gains **187 checks** (1,248 → 1,435 passing, 1 standing
warning). The one that matters re-derives **every zone price from the registry
and the city's own job-density percentiles** and compares it to the shipped
artefact: a typed price, a re-drawn extent or a hand-edited artefact all fail it.
The four dead zone names are asserted absent from *code* — comments are stripped
first, deliberately, because a defect that stays explained does not come back by
accident.

**No scenario was run, no target value changed, the 67/143 split is untouched
and nothing here is a result.**

---

## 9.32 The transfer penalty cannot be estimated from this package, and the parameter it names was reaching nothing anyway (P4 deliverable 8, issues #25, #35)

Deliverable 8 asks for the estimate proposal §7.2 specified as its fallback when
journey-linked Opal is refused. Two findings, and the second was found while
establishing the first.

### The estimate cannot be made, on three independent grounds

§7.2's exact words: *"estimate transfer rates from tap-on/tap-off timing at the
Interchange using aggregate stop-level data plus a matching model; validate
against the published interchange percentages."*

**1. The timing does not exist.** Every Opal source in the package is a monthly
aggregate:

| file | columns | resolution |
|---|---|---|
| `opal_lr_newcastle_by_stop.csv` | Year_Month, Location, Card_type, Trip | month × stop |
| `opal_lr_newcastle_by_month_cardtype.csv` | Year_Month, Card_type, Line, Trip | month × line |
| `opal_bus_newcastle_hunter.csv` | Year_Month, Card_type, Contract_region, Trip | month × region |
| `station_entries_exits_newcastle.csv` | MonthYear, Station, Station_Type, Entry_Exit, Trip | month × station |

There is no timestamp, no tap-off paired to a tap-on, and no sub-monthly
resolution anywhere. A matching model matches a tap-off at one stop to a tap-on
at another **within a time window**. With monthly totals there is no window. The
method is not hard here; it is undefined.

**2. The data that would substitute is holdout.** `lr_tapon_share_by_stop` (6
rows) and `station_entry_monthly_mean` / `station_exit_monthly_mean` (26 + 26)
are all `split=holdout`. The 67 calibration rows contain **nothing** bearing on
interchange — the non-count calibration rows are light rail and bus boardings,
the light rail share of local PT boardings, scheduled run time and alignment
length. So the alternative route — constrain the penalty so the model reproduces
an observed transfer rate, the §9.8 / §9.13 pattern — has no non-holdout
observable to constrain against either. The HTS held is aggregate mode × purpose
with no interchange table, and its trips-to-journeys ratio cannot be split by
mode, so PT transfers cannot be isolated from it.

**3. The published validation source could not be located**, and the figures
that might have substituted are the wrong quantity. Three searches found no
published interchange percentage for Newcastle. More important: interchange
**times** — the kind of figure TfNSW does publish — are not the transfer
**penalty**. MATSim already simulates the interchange walk from the schedule and
scores the wait at `beta_wait` = 2.0 × in-vehicle time.
`C.transfer.beta_transfer_penalty_min` is explicitly the behavioural premium *on
top of* the measured Newcastle Interchange walk (mean 112 s over 51 stop pairs).
Substituting a published transfer time for it would double-count what the model
already computes. **This is the trap worth recording**: the available figure
looks like the answer and is a different quantity.

The issue's own bar anticipates this: *"If the estimate cannot be made, the
reason is recorded and the sweep stands, which is a better outcome than an
unexamined assumption."* The sweep stands, at 3–15 minutes, crossed at seven
points, and every headline remains bound to report as a curve across it
(proposal §3.4 S-d). `estimation_route` in `C1_parameters.json` now records the
impossibility rather than naming a route that does not exist.

**What would settle it:** journey-linked or timestamped Opal, which is a TfNSW
unit-record request, not a published dataset. Nothing in the open catalogue
closes it (§9.23).

### The parameter was reaching nothing, so the estimate could not have mattered

Establishing the above meant tracing where the parameter goes, which found that
it does not go anywhere. `build_params.py` read **one** registry field
(`C.vot.by_purpose`) and typed the other 26 behavioural values in as literals.
`params/C1_parameters.json` is what `build_matsim_run_inputs.py` reads, so the
registry declarations reached nothing.

Reproduced before attributing it — setting the value through the resolver's own
override path left C1 **byte-identical** at 8.0:

    CITYSIM_C_TRANSFER_BETA_TRANSFER_PENALTY_MIN=12.0 python src/build/build_params.py

Seventh instance of the class, after #12, #21, the walk decay, the gradient, the
seven config-template literals at §9.28 and the parking price at §9.31.

Two consequences sharper than the general case. **The ASCs are `held_fixed`
under §8.5** — the resolver refuses every overlay, environment variable and flag
— and the model was not reading the value being protected. Deliverable 5 (#14)
is "estimate the ASCs on era 3 and freeze them"; that work would have written
seven estimated constants into the registry and changed nothing, reporting
success. **And the sweep grid was a literal too**, so #25's own bar — move the
field to `measured` "with the sweep set from the estimate's own spread" — was
unmeetable by construction: a narrowed range would not have moved the 28-point
grid.

The existing check compared **bases only**, and its own comment conceded the
arrangement: *"The registry copy is a mirror; C1 is what reaches the model."*
Agreement was maintained by hand, which is what a check cannot detect. Three
ranges had already drifted apart unnoticed:

| field | C1 literal | registry |
|---|---|---|
| `beta_crowding_seated` | 1.00 – 1.10 | 1.00 – **1.15** |
| `beta_crowding_standing` | **1.15** – **1.85** | 1.20 – 1.80 |
| `beta_gradient_uphill` | **0.04** – **0.15** | 0.05 – 0.14 |

### The fix, and the proof it changed no result

The direction is inverted: **C1 is generated from the registry** rather than
checked against it. Every base comes from the field's `value`, every range from
its own `sweep`, every label from its `source`. Five declarations were missing
and are added, because a value absent from the registry cannot be generated from
it: `C.transfer.penalty_sweep_grid`, `A.lightrail.dwell_sweep_grid`,
`C.vot.car_unavailable_walk_factor` (1.15), `C.walk.max_considered_m` (2500) and
`E.matrix.reference_scenario`. The two grids are `definition` — a sampling design
is not an empirical quantity — and **declaring where to sample the charging dwell
did not pin it**: the field stays `unobtained` with a null value. The dwell
baseline is read by resolving the reference scenario's own overlay, which is
where §4.3 already said it lives.

**Value-neutral, and demonstrated.** Diffing all 30 rows of
`C1_behavioural_parameters.csv` column by column, the only columns that moved are
the five belonging to the three drifted ranges. No base changed, and regenerating
all 30 run-input sets produced no change at all.

**Reach demonstrated by changing a value**, not by reading `consumers`:

| | before | after |
|---|---|---|
| override → `transfer_penalty.base` | 8.0 (unchanged) | **12.0** |
| override → the 30 C1 rows | 8.0 | **12.0** |
| override → baseline grid row | 8.0 | **12.0** |
| override → `utilityOfLineSwitch` | −2.2613 | **−3.3922** |

−3.3922 is −(12/60) × 16.96, the VOT conversion, so the chain holds end to end.

### Guarded

`check_package.py` 1,435 → **1,440** passing. The new checks assert that the ASCs
agree, that every declared **range** reaches C1 (a base-only comparison read as
green while three ranges were wrong), that the sensitivity grid spans its declared
sweep exactly and contains its own base, that every non-zero dwell grid point lies
inside the declared sweep, and that declaring the grid did not pin the unobtained
field.

**No scenario was run, no target value changed, no holdout row was opened, the
67/143 split is untouched and nothing here is a result.**

---

## 9.33 Six defaults stop being guesses, and a suspected duplicate turns out to be two different numbers (P4 deliverable 0b, issue #23)

Deliverable 0b asks how many of the registry's `assumed` fields the data can
actually settle. **88 → 84 assumed**, **15 → 21 measured**, plus one field that
existed nowhere and should have. The realistic target was 15–25 fields of tour
structure and network defaults; what the data supports is the network half, and
the reason the other half resists is recorded rather than worked around.

### The suspected duplicate was not one, and both numbers were wrong

`RUN.routing.beeline_distance_factor` (assumed 1.30) and `B.activity.detour_factor`
(measured 1.3376) were flagged as "probably the same quantity declared twice". They
are not. The detour factor is the **road graph at multi-kilometre zone spacing**;
the beeline factor is the **active network at walk and bike trip lengths**, and
circuity falls with distance. Measuring it settles the question instead of
aliasing one to the other:

| | value | sweep (observed IQR) | measured at |
|---|---|---|---|
| walk | **1.6902** | 1.294 – 1.794 | 700 m, the observed walk trip length |
| bike | **1.5231** | 1.207 – 1.456 | 5.2 km, the observed bike trip length |
| road (unchanged) | 1.3376 | 1.25 – 1.423 | population-weighted zone pairs |

Walk and bike differ enough that one shared factor was wrong for both, so the
field is **split in two**. The network routed over is the A6 active layer
**unioned with every road class a pedestrian may use**: A6 alone is 23,808
footway edges, and OSM maps a footway beside a residential street only where
somebody drew one, so routing on it alone would report the mapping's circuity
rather than the city's.

**A first attempt was rejected on its own evidence.** Drawing a random bearing
from each origin gave walk 1.96 against a median of 1.52 — the gap being
destinations across the harbour and the motorway that nobody walks to. Sampling
observed **POI** destinations instead, which is where B2 places activities, gives
1.69 against a median of 1.46. The tail is smaller because the destinations are
real.

### The walk speed was one quantity declared twice, and that one WAS a duplicate

`A.transit.walk_speed_ms` (1.25, generating GTFS transfer times) and
`RUN.routing.teleported_walk_speed_ms` (1.05) each carried `literature` and each
described the other as a different quantity. The pinned jar disagrees.
`TeleportationRoutingModule` computes

    travelDistance = beelineDistance x beelineDistanceFactor    // dmul
    travelTime     = travelDistance / teleportedModeSpeed       // ddiv

so `teleportedModeSpeed` is the speed **along the walked path** — exactly what
the GTFS figure is. Verified in the bytecode, not from memory. The MATSim field
is now `derived` with that identity, at 1.25. The detour a walker makes is
carried by the measured beeline factor, which the speed no longer has to absorb.

Net effect on a walk leg: 1.6902/1.30 × 1.05/1.25 = **1.09**, about 9% slower,
with every component now measured or physically grounded rather than chosen.

### Defaults measured from the city's own OSM tags

The imputation is not a rounding error — `lane_width_m` is imputed on **99.2%**
of road edges, `num_lanes` on 75.4%, `speed_limit_kmh` on 53.7% — but the
complement is real data: 10,613 edges carry a `lanes` tag and 19,961 a
`maxspeed`. `measure_osm_defaults.py` takes each class's own median where at
least 30 edges are tagged, and its own interquartile range as the sweep.

| field | classes measured | notable corrections |
|---|---|---|
| `A.road.speed_default` | 13 of 16 | **trunk 80 → 60** (n=1,702), **motorway 100 → 110** (n=432), motorway_link 60 → 80, service 20 → 25 |
| `A.road.lanes_default` | 13 of 16 | every measured class confirmed its assumed value |
| `A.active.footway_width_default` | 3 of 8 | footway 1.8 → 2.0, cycleway 2.5 → 2.0, path 1.5 → 1.0 |

`busway`, `road` and `tertiary_link` keep their assumed values for want of
coverage and say so; `A.road.capacity_default` is **not** measured at all —
saturation flow is an engineering convention OSM does not record and this
package has no per-class count data to estimate it from.

**A field that existed nowhere.** `build_network_layers.py` carried a bare
`lw = 3.2` for lane width, applied to 99.2% of edges, in no registry at all.
It is now `A.road.lane_width_default_m`, **measured at 3.5 m** (IQR 2.5–4.5).

It could not be read off the `width` tag. On a road, OSM `width` is the whole
**carriageway**: measured straight it is 6.5 m, which is two lanes, and writing
that into a per-lane field would have doubled every carriageway in the model.
Per-lane width is derived as width ÷ lanes on the 265 edges carrying both tags.
The build script now divides a tagged width by its lane count for the same
reason.

### Three things the data looked able to settle and could not

Each is the same trap: **the available number looks like the answer and is a
different quantity.** Three instances in one session is a pattern worth naming.

1. **Parking capacity.** 4,861 of 7,710 facilities carry an observed
   `capacity`, which looks like ample coverage — and **4,623 of them are `1`.**
   They are individual bays, not car parks. Only 162 facilities carry a capacity
   of 5 or more. `A.parking.capacity_default` **stays assumed**; a measured
   default of 1.0 would have said every car park in Newcastle holds one car.
2. **The transfer penalty** (§9.32): a published interchange *time* is not a
   behavioural *penalty*.
3. **Parking price** (§9.31): `fee=yes` is 452 University car parks.

### The reclassification the issue proposed, reviewed and mostly declined

#23 suggests several `assumed` fields are really methodological choices
mislabelled, and that reclassifying them to `definition` would stop them
inflating the count. Reviewed one by one, that is **not** what they are. The
SUMO booleans each change a result — `junctions_join` moves a junction centroid
and interacts with `A.signals.junction_match_m`; `tls_join` changes how many
signal programs the corridor carries; `tls_default_type` is, in its own words,
"a real modelling choice standing in for information the project does not have".
The corridor buffers carry documented empirical consequences and would lose
their sweeps. Relabelling a real assumption to make a percentage look better is
the opposite of what deliverable 0b is for, so the count stays honest at 84.

### Guarded

`check_package.py` gains a pin from the registry to
`params/C2_osm_defaults.json`, class for class — the same two-copies-of-a-number
hazard §9.32 found in C1 — plus an assertion that the per-lane width is a lane
and not a carriageway.

**The measured speed defaults are in `A1_road_edges.csv` as of this change; the
MATSim network still carries the old ones and is rebuilt at #32, which
re-harvests the extent anyway. No scenario was run, no target value changed, the
67/143 split is untouched and nothing here is a result.**

---

## 9.34 The speed limit becomes the regulated one, and the rest of the corridor stays imputed and says so (P4, issue #27)

Issue #27 grades the corridor attributes hypothesis B3 rests on. One of them an
open dataset can settle; the others cannot, and the difference is now visible in
the artefact rather than only in the issue.

### What closed

TfNSW publishes **Speed Zones**: the regulated speed for every road in NSW, as
statewide linework. It is a stronger source than the OSM `maxspeed` tag - the
legal instrument rather than a mapper's transcription of a sign - and it covers
the whole network, not only the 714 corridor edges.

62 MB shapefile, 447,426 segments statewide, clipped to the dissolved LGA
boundary plus a declared margin - **the extent is derived, never typed** - which
leaves 35,688 segments in the study area.

| | before | after |
|---|---|---|
| corridor edges on a regulated speed | 0 | **669 of 714** |
| corridor edges on an imputed default | 75 | **41** |
| whole network on a regulated speed | 0 | 25,109 of 43,112 |
| whole network on an imputed default | 23,151 (53.7%) | 16,515 (38.3%) |

Of the 16,515 still on a class default, **15,804 are `service`** - driveways,
car-park aisles and alleys. Excluding those, imputation on the roads anyone
drives is 711 of 27,308, or **2.6%**.

### The join is validated, and the validation changed it

Where an edge carries both an OSM tag and a matched zone the two are compared.
The first attempt matched within 20 m and agreed only 73.5%, which is too low to
adopt blind. Two things came out of looking:

**Agreement collapses with distance** - 73-77% out to 5 m, 72% to 10 m, then
**30% at 10-20 m and 15% at 20-40 m**. Beyond 10 m the nearest line is a
different road. The match radius is now 10 m, and its sweep basis is that
measurement rather than a chosen interval.

**Service roads match the arterial beside them** - 37% agreement against 83% on
residential. TfNSW does not speed-zone a driveway, so the nearest zone line
belongs to the road it runs alongside. `service` is excluded by OSM class, which
is portable; excluding by measured agreement would be fitting the join to its own
validation.

After both, agreement is 74.9% over 18,473 validated edges. The residual is the
regulated zone disagreeing with an OSM tag on a well-matched road, and the
regulated zone is the one to believe.

### What did not close, and must be reported rather than assumed away

| attribute | corridor edges imputed | why it stays |
|---|---|---|
| kerbside use | 678 of 714 | TfNSW publishes **Sydney CBD loading zones** only - verified against the catalogue |
| lane width | 704 of 714 | no statewide inventory exists |
| capacity | 714 of 714 | saturation flow is an engineering convention nobody publishes per road |
| turn lanes | 644 absent | OSM `turn:lanes` is simply not mapped here |

These need street-level and aerial imagery, which is a survey and not a
download. Proposal §3.3 calls B3 *"the decisive test of Claim B"* and rests it on
lane loss, banned turns and kerbside parking removal - so **B3 must carry this
as a stated uncertainty**, and `check_package.py` now asserts each gap is still
labelled `imputed_rule` so it cannot be mistaken for something already closed.

### Two more copies of a number, found on the way

`build_corridor_road_attributes.py` kept its **own** `SPEED_DEFAULT`,
`LANES_DEFAULT` and `CAP_DEFAULT` dictionaries, "repeated here so a value that
came from a rule can be identified as such". Once §9.33 measured those defaults
the two copies **diverged** - the corridor file still said trunk 80 where the
measurement says 60 over 1,702 tagged edges. Both now resolve from the registry.

It also carried a second bare `3.2` lane width with the same carriageway-versus-lane
error §9.33 found in the road builder: it read the OSM `width` tag straight into
a per-lane field, and on a road that tag is the whole carriageway. Both now
divide by the lane count.

**No scenario was run, no target value changed, the 67/143 split is untouched
and nothing here is a result.**

---

## 9.35 The harvest extent is derived from the study area instead of drawn around it (P4, issue #32)

`src/extract/overpass.py` harvested OSM inside a typed rectangle, and the
rectangle did not cover the study area. Against `zones_LGA.gpkg` it cut **0.30
degrees off the west and 0.26 off the east** of the five declared LGAs, leaving
**87 of 1,500 core SA1s and 31,940 agents - 5.2% of the population - outside the
road network**. Measured on `results/ride_fix_10pct`, those agents made 3.2x
longer trips, walked 3.8x further to access a car, and cycled at **36.5% against
14.8%** - the DECISIONS.md 9.15 signature of no road near home. It survived
three phases, because a typed rectangle cannot be wrong in a way anyone notices.

### Both extents are now derived

| | derived from | margin |
|---|---|---|
| study area | the dissolved LGA boundary in `zones_LGA.gpkg` | `A.osm.harvest_margin_m` |
| CBD buildings | the observed light rail **stop set** in `A3_stop_extras.csv` | `A.osm.buildings_margin_m` |

The building extent feeds the D1 frontage segments hypothesis B1 is measured on,
and was the same rectangle issue #34 was filed against. Anchoring it on the stop
set works because the stops are **observed**, they come from the GTFS feed rather
than from OSM so they exist before any harvest, and every city with a corridor
has them. At the declared margin the derived extent **contains** the rectangle it
replaced - which needed 3,217 m - so no building previously harvested is lost,
and all seven pre-registered frontage comparators lie within 1,161 m of a stop.

Both derived extents strictly contain their predecessors. The study extent grows
**2.02x**.

### The growth broke the harvest, and that is now handled rather than worked around

A single Overpass query over the corrected extent returns **504 Gateway Timeout**
- measured twice on the roads layer, where the smaller rectangle had always
succeeded. Each layer is now fetched over a grid of tiles no larger than
`A.osm.harvest_tile_deg` and merged, **de-duplicating by element id**: Overpass
returns a whole way when any part of it matches a bbox, so a way crossing a tile
boundary arrives in both tiles and would otherwise be counted twice.

The endpoint also load-sheds unpredictably - one tile failed four consecutive
times on one mirror and was served in seconds by another - so a request rotates
across three Overpass mirrors with a declared attempt budget, and a tile that
does arrive is cached so an interrupted harvest resumes rather than restarting.
The tile size is declared as a **ceiling measured against what fails**, not a
chosen number.

### The merge was wrong, and arithmetic caught it rather than an error

The first tiled harvest completed four layers and **all four were corrupt**. The
merge resolved an element's end by taking the earlier of `/>` and `</way>`,
which looks equivalent and is not: a way with children contains
`<nd ref="..."/>`, whose `/>` comes long before `</way>`, so **every way was cut
off at its opening tag and lost all of its node references**.

Nothing would have complained. The files were well formed, every way id was
present, and only the geometry was missing; `build_network_layers.py` would have
accepted them and produced a road network with no shape. What exposed it was a
size comparison, not an exception: the merged roads layer came out at **21.2 MB
against the previous 35.8 MB, on an extent 2.02x larger**. A layer that shrinks
when its extent doubles is arithmetic that does not work, and that is the only
reason it was caught.

Fixed by resolving the opening tag first and only then the closing one.
`osm_tiles.verify()` now refuses a merged layer where fewer than 90% of sampled
ways carry a node reference, and the fetch calls it before discarding anything.
**Tiles are deleted only after the merge verifies** - deleting them first is what
made this expensive, because the merged files were corrupt and the inputs were
already gone, so four layers must be fetched again.

### Status

The extent derivation, the tiling, the mirror rotation and the merge fix have
landed. **The re-harvest, the network rebuild and the pt2matsim re-run have
not**, and until
they do the shipped network is still the one built inside the old rectangle.
Issue #32 stays open until that batch completes, because #32 is the defect in the
DATA, not in the code that acquires it.

Sequencing is deliberate: the re-harvest rebuilds the network, which re-runs
pt2matsim and makes every existing run incomparable (§3.5), and it regenerates
B2, which #30, #20 and #24 also require. It is done inside that one demand
rebuild, not standalone, or B2 is rebuilt twice.

**No scenario was run, no target value changed, the 67/143 split is untouched
and nothing here is a result.**

---

## 9.36 A run says what it is doing while it does it, and the event stream was never the obstacle (P4, live view rebuilt)

`run_monitor.py` was deleted and rebuilt as `run_view.py` plus a telemetry
handler inside the controler. The rebuild was asked for; what it exposed was not.

### The obstacle was assumed, not measured

The old view inferred everything from the log because the run published nothing,
and the apparent reason was that MATSim writes its event stream only every
`RUN.controler.write_events_interval` iterations — 10. Getting per-mode counts
every iteration therefore looked like it cost either a config change to
`writeEventsInterval = 1` (≈16 MB an iteration at 1%, far more at 10%, which is
the 51 GiB of `ITERS` scratch `prune_run.py` exists to delete) or nothing.

**Both premises were wrong, and the package already held the counter-example.**
MATSim's `EventsManager` fires every event to every registered handler on
**every** iteration; `writeEventsInterval` governs only whether
`EventWriterXML` — itself just another handler — is among them. The completed
250-iteration run holds **26 event files and 251 leg histograms**, and the
histogram is built by a handler. A registered handler therefore sees 100% of
events on 100% of iterations at **no disk cost**, and it sees them *as the
mobsim advances*, which is what makes the view live rather than retrospective.
`write_events_interval` is unchanged.

### What is published

`src/java/citysim/RunTelemetry.java`, installed only when the `telemetry` config
module is present, in the same on/off shape the parking price file uses:

- `telemetry_live.json` — rewritten every `RUN.telemetry.live_interval_s`
  **simulated** seconds. The boundary is simulated time, never wall clock, so a
  repeated run writes the same snapshots in the same places; the determinism rule
  applies to an observer as much as to a build script.
- `telemetry.jsonl` — one summary line an iteration.
- `telemetry_links.json` — the per-link congestion payload for the window
  that just closed, **overwritten** on every live boundary and once more
  with the whole day at iteration end.

All three sit outside `ITERS/`, so `prune_run.py` never removes them.

**The bus / rail / tram / ferry split cannot come from mode choice** — a
passenger's leg mode is `pt` for all four. It comes from the transit fleet's own
vehicle types, which §9.30 had already given real identities.

### Three defects, each found by measurement rather than by reading

1. **The per-link payload was 99.5% of the bytes.** Measured at 1.14 MB an
   iteration against a 6 KB summary: appending it would have put **1.2 GB** on
   disk over a 1000-iteration run at 1% — rebuilding the exact disease this
   design exists to avoid. Split out and overwritten: **5 MB** over the same run,
   a 240x reduction, and the map only ever shows the last completed iteration.
2. **The counts did not close.** The conservation identity
   *departures = arrivals + stuck* held **exactly** for car, bike, ride and walk
   and left a **pt residual of 305** — passengers still waiting at a stop at
   30:00:00, for whom MATSim emits no terminal event. Folded into `en_route` it
   would have read as traffic. It is now reported as `unresolved`, the identity
   is published per mode so it can be seen to close, and the page renames its own
   headings once the mobsim ends rather than calling a residual "en route".
3. **The delay ratio has no upper bound.** Over 59,399 loaded links: median
   **1.10**, p90 **2.58**, p95 **10.67**, max **56,805** — a short link with a
   stopped vehicle. A ramp fitted to the data in view would let one gridlocked
   hairline flatten the whole city to green, so the ramp is **fixed and
   saturating at 3.0**, and volume drives stroke width so a link carrying one
   vehicle stays a hairline whatever its ratio.

### The map is live too, and making it so found the worst defect in this work

The first cut regenerated the map only when an iteration ended, on the argument
that a per-link mean over a partial day is not a meaningful reading. That was a
judgement, not a limit, and it was the wrong one: the handler already sees every
link event as the mobsim advances. The map now publishes on the same
simulated-time boundary as the counts.

**A live map cannot be cumulative.** A running mean over the day converges and
stops moving, so the peak would build and then never dissipate. Each publication
is therefore the window that just closed — measured on a 1% probe, the morning
build reads 670 → 8,466 → 19,886 → 22,208 links moving between 00:00 and 09:00,
one simulated hour every ~0.4 s of wall clock. A window is also far smaller than
a day: ~13k–20k links against 60k, so the payload got cheaper, not dearer.

**⚠ THE OBSERVER KILLED THE RUN.** On Windows, `Files.move` with
`REPLACE_EXISTING` throws `FileSystemException: The process cannot access the
file because it is being used by another process` whenever a reader holds the
target open — and the live view polls that file twice a second. The exception
propagated out of the handler and **terminated the run at iteration 5 of 10**.
This class had claimed in its own header that *a run observed is byte-for-byte a
run unobserved*, and it was doing the exact opposite. Fixed by making telemetry
structurally unable to reach the mobsim: bounded retry, then an in-place write,
then give up and count the loss, with every publish path wrapped so no
`RuntimeException` can escape. `write_failures` is reported in the live payload,
so a silent loss is still visible. Verified by hammering the file with **1,987
concurrent reads during a live run: zero IO exceptions, 99.9% clean parses**, and
the 0.1% partial reads are the in-place fallback, which a reader simply retries.

The general lesson is worth keeping: **an instrument that can stop the experiment
is not an instrument.** Any future observer in this repo gets the same treatment.

Two smaller defects, both found by looking rather than reasoning:

- **Geometry came from `output_network.xml.gz`, which MATSim writes only when the
  run ENDS** — so the map appeared only after the thing it was built to watch was
  over. It now reads `inputNetworkFile` from the run's config: same 151,592 links,
  same ids, available before iteration 0.
- **`scope` was not passed through the server**, so a live window rendered under a
  "whole day" heading. Caught because 12,814 links is not a day's 60k.

`--run` with an empty string silently resolved to `results/` itself and reported
"no telemetry" for a run that had plenty; it now exits.

**Live cadence.** The page polls `RUN.monitor.live_poll_s` (0.5 s) while the
mobsim is sweeping and falls back to `RUN.monitor.poll_s` (3 s) between mobsims,
when nothing it shows changes. At 3 s throughout, a 15 s day sweep would be
sampled five times and the peak would pass between two reads.

### The clock reads a 24 h day, and asking why it did not found a demand defect (issue #37)

The view first showed the simulated clock as MATSim stores it, running to
`30:00:00`. That presents a 24 h day in a 30 h format, and the question *"why does
it go to 30?"* is the right one to ask of it. The clock now reads a real day —
`06:00:00 +1d` rather than `30:00:00` — with the raw seconds unchanged in the
payload so nothing downstream moves.

**Minutes and seconds are interpolated, and the page says so.** The run publishes
one sample per simulated hour, so a clock that only stepped on those samples
would jump. Between two samples the display advances at the rate measured from
the previous two, **clamped so it can never run past the next expected sample** —
a stalled feed must not be able to invent an hour that was never simulated. It
resets when the iteration does. This is a smoothing of real readings, never a
value the run reported, and the label under the clock states it.

**The window itself is correct and stays.** `qsim.endTime = 30:00:00` is not a
claim that a day is 30 hours; it is a 24 h day with a tail so a trip departing at
23:30 arrives rather than being truncated (§9.12 already records the aborts at
that horizon). Hours 24–30 are 00:00–06:00 the following morning.

**⚠ But checking it found something real.** On `results/live_demo` (S2 × WEEKDAY,
10%), iteration 30's event stream, 481,153 departures: **8,656 agents depart at or
after 24:00, 3,421 depart before 06:00, and 348 do both** — a trip at 02:00 and a
trip at 26:00 inside one modelled day, i.e. a person with two 2 a.m.s. That is
0.66% of the sample and it is not physical.

**It is in the seed, not in replanning.** Departures at or after 24:00 are
**25,210 at iteration 0** — before any plan has been mutated — and stay flat at
~25,500 through iteration 30 while their share falls 5.92% → 5.40% as total
departures grow. `TimeAllocationMutator` is not the cause.
`build_activity_chains.py` draws departure hours over **0..23**, so the seeded day
is a correct 24 h; what is missing is any cap or wrap at the 24 h boundary when a
chain seeded at 22:00 runs long.

**Recorded, not fixed.** The fix changes B2, which regenerates demand and breaks
comparability with every run to date (§3.5) — the rebuild #32, #30, #24 and #20
already require. 0.66% does not justify pulling that forward alone, so it goes in
that batch. It is stated here because those trips are in the completed-trip
counts and therefore in the reported mode share: small, non-zero, and previously
undeclared.

### The basemap was silently dropping every segment longer than 327 m

Reported as *"water is overlapping land"*. It was not an overlap: **the land was
never being drawn at all**, so the ocean colour showed everywhere and the
coastline vanished.

`build_basemap.pack()` encodes a polyline as an int32-centimetre anchor followed
by int16-centimetre deltas — 4 bytes a vertex at 1 cm precision, which is what
makes zooming to a 10 m view meaningful. An int16 centimetre delta caps a step at
**327.67 m**. On overflow the packer began a new anchored run, but the run that
would have carried the long step was then degenerate (`n == 1`) and skipped, so
**the segment was dropped entirely**.

On a road that is a missing link. On a polygon it is fatal, and it bites exactly
where it is least visible: `read_coast` **simplifies** the dissolved five-LGA
boundary, and simplification is precisely what manufactures straight segments
longer than 327 m.

Measured on the shipped basemap:

| | before | after |
|---|---:|---:|
| coast runs | 180 | **36** |
| of which closed rings | 33 (18%) | **36 (100%)** |
| largest ring span | 12.5 x 8.0 km | **129.4 x 69.5 km** |
| landmass fill, sampled across the view | **1 of 40 points** | full |

The boundary spans 131 km; the largest surviving fragment spanned 12.5 km. Water
and green were fragmented the same way — 3,525 and 5,671 rings, now 100% closed.

**Fixed by densifying rather than splitting**: a step longer than the bound is
divided into equal collinear sub-steps before packing. That changes no geometry,
needs no change to the wire format, and removes the failure mode rather than
detecting it. The layer counts and point counts the builder reports are unchanged.

**This defect is not confined to the live view.** `build_replay_page.py` decodes
the same payload and fills `coast`, `water`, `green` and `sand` from it, so every
replay page built before this change has the same broken area fills. Any published
replay must be rebuilt.

**How it was found, and why not sooner:** by arithmetic, not by reading. A
boundary that spans 131 km cannot have a largest fragment of 12.5 km, and a
landmass that fills 1 of 40 sampled points is not a landmass. Nothing in the
render code looks wrong, and the map looked plausible — dark, with roads on it —
which is the recurring shape of every defect in this project.

### A finished run closes itself out, and says whether it can be believed (`_summary.json`, `SUMMARY.md`)

A completed run used to leave a log, 9.8 GB of scratch and three JSON files, and
the question *"so what happened?"* was answered by reading them. It is now
answered in writing, in both dialects: `_summary.json` against a declared schema
in `config/schema/outputs/`, and `SUMMARY.md` for a person. `run_matsim.py` calls
`summarise_run.py` on success; the summariser also runs standalone on any
completed run.

**It answers three questions and refuses a fourth.**

1. **What was run** — scenario, day type, sample fraction, seed, iterations,
   threads, wall clock and the controler hash. A reading can never be separated
   from the run that produced it, and the page and the file both warn that at 1%
   the storage floor makes cross-fraction comparison invalid (§9.12, §15).
2. **Did it relax** — drift per mode between the innovation cutoff and the final
   iteration. After the cutoff MATSim creates no new plans, so what remains is
   relaxation rather than search: the question issue #5 turns on.
3. **Did its own accounting close** — departures = arrivals + stuck + unresolved,
   per mode, plus the telemetry write-failure count.

The fourth — *what does this say about Newcastle?* — is **refused, in the
document itself**, so the file cannot be quoted out of context. No mode share, no
patronage, no fit statistic, no validation target. `extract_metrics.py` →
`fit.py` → `report.py` remains the only route to a reportable number, and the
67/143 split stays enforced inside `fit.py`.

**Measured on the first run it closed out** (`live_demo`, S2 × WEEKDAY, 10%, 250
iterations, 2 h 43 m, rc=0, 52,877 agents):

| verdict | reading |
|---|---|
| relaxation | ❌ **did not settle** — car still moving **+3.21 pp** after innovation off at iteration 200 |
| accounting | ✅ closes on every mode; stuck 0.05% of 622,404 departures |
| telemetry | ✅ **0** write failures |

The relaxation verdict is an independent confirmation of §9.27 from a different
instrument: 250 iterations is far short, and the run's own drift says so without
anyone having to read `modestats.csv`. **That is what this file is for** — not to
report a finding, but to stop an unsettled run being mistaken for a settled one.

⚠ **One defect caught in the writing of it, and it is the recurring class.** The
first version read `RUN.replanning.fraction_innovation_off` — a key that does not
exist; the field is `RUN.replanning.fraction_to_disable_innovation` — and fell
back to a hard-coded `0.8`. That is the shipped value, so it produced the correct
cutoff **for the wrong reason**, and would have kept producing it after the field
moved. It now reads the parameter from the config the run **actually executed**,
with no fallback: unknown stays unknown. A silent default that happens to be
right is the same defect as a declared value that reaches nothing, and it is
harder to see.

### The map needs no basemap, and is therefore not blocked

The hotspot layer is drawn from the run's **own** `output_network.xml.gz`
(70,146 nodes, 151,592 links), not from `build_basemap.py`. That avoids two
problems at once: the basemap reads `networks/osm/`, which is **empty** until the
issue #32 re-harvest, and it is keyed by A1 road edges while telemetry is keyed
by MATSim link ids — a one-to-many join. The run's own network carries exactly
the links the telemetry names, so the map is guaranteed to agree with the run
that produced it. The basemap remains the right source for *context* — water,
coast, parkland — once it exists.

The default view is the box holding the middle **90%** of traversals, chosen by
measurement: 99.5% gives 187 x 565 km and 98% still gives 169 x 355, because a
fraction of a percent of very long external trips drags the frame off the city.
90% gives **52 x 49 km**, the scale of the 4,086 km² study area. Separately
measured and worth carrying forward: **86% of all traversals fall in a single
40 km northing band centred on Newcastle**.

### Verified by running it, not by reading it

A 1%, 2-iteration probe against the pinned toolchain: the module installs, all
three files appear, the identity closes for every mode, the fleet splits
Bus 596 / Rail 111 / Tram 151 / Ferry 0, and the page renders 59,399 loaded links
with no console error. **The probe also reproduced a known finding without being
asked to:** 1,079 of 5,363 car legs stuck, which is §15's storage floor at 1%
producing the spurious spillback that makes 1% unusable and cross-fraction
comparison invalid (§9.12). The page states the sample fraction on its face and
warns at or below 1% for that reason.

**Not a result.** These counts are legs in flight during one iteration — neither
the mode agents chose (`modestats.csv`) nor the trips that completed
(`_metrics.json`). The page says so on its face.

**Outstanding:** the 30 assembled run-input sets predate the `telemetry` module
and must be regenerated (and the manifest with them) before a real run publishes
anything; the four `RUN.monitor.*` fields are re-wired but `check_package.py`
coverage for the new view has not been written back.


## 9.37 One city moves into `cities/<city>/`, and the framework stops knowing which city it models (repository structure)

**No model or data value changed. Every relocated constant is byte-identical to
the one it replaced, and the manifest proves it.**

The repository claimed a portable/instance split and did not have one.
`config/schema/` stated the shape of a field; nothing stated **which** fields a
city must supply, or which artefacts it must produce. Meanwhile 338 path
literals across 46 framework scripts named `data/`, `networks/`, `schedules/`,
`demand/`, `scenarios/` and `params/` as though a repository could hold only one
city, seven builders encoded this city's intervention outright, and the CRS was
typed into seven modules.

**What moved.** `cities/newcastle/` now holds `registry/`, `overlays/{scenarios,
day,runs}/`, `extract/`, `build/`, `geometry/`, `data/`, `networks/`,
`schedules/`, `demand/`, `scenarios/` and `params/`. `config/` is
`config/schema/` alone. `src/city.py` resolves the city and is the only module
that knows; paths stay **city-relative inside a city**, so a manifest row means
the same thing in every city.

**The migration was verified arithmetically, not by reading.** The manifest was
regenerated and diffed against its pre-migration copy: **376 rows before, 376
after; no path added, none removed, and not one sha256 or byte count changed.**
The only column that moved was `produced_by`, on the 99 rows produced by the
acquisition adapters and the 7 relocated builders. That diff is the evidence the
move was value-preserving; nothing else offered here is.

**The input contract now exists.** `config/schema/city.schema.json` states a
city's identity, and requires the study extent to be **derived** from a boundary
dataset and a named selector - `bbox` is deliberately not a property of the
schema, because the typed rectangle of issue #32 clipped 87 of 1,500 core SA1s
out of the road network and survived three phases. `required_fields.json` (210
keys) and `layers.json` (119 artefacts) are **generated**: the first from the
reference city's registry, the second by statically reading the framework's own
`city.path(...)` calls, which is the stronger of the two derivations because it
asks the code what it needs rather than asking one city what it has.
`src/registry/check_city.py` gates a city **before** a run instead of failing one
`get()` at a time several hundred lines into a build, and CI runs it.

**What `required` does and does not mean is recorded in the file itself.** It
means the reference city declares the field and the framework will not run
without it. It does not mean every city needs it - a city with no light rail has
no use for `A.lightrail.dwell_fixed_s`. Narrowing the set per model layer is not
done, and the generated document says so rather than implying a stronger claim.

**Two defects, both found by measurement.**

1. **Four scripts assigned a bare directory name as a path** - `OUT =
   'schedules'`, `OUT = 'demand'`, `OUT = 'params'`, `OUT = 'scenarios'`. They
   carried no trailing slash, so they did not look like paths and the migration
   sweep missed them. One of them wrote **32 MB of rebuilt GTFS into the
   repository root**, beside the city that should have received it. The failure
   is silent in the worst way: the script succeeds, the manifest still passes,
   and the outputs are simply somewhere else. `check_city.py` now fails on the
   class, and the guard was verified the only way that counts - by
   reintroducing the defect and watching the check go red, then green again.
2. **`build_manifest.py` still labelled EPSG:28356 as GDA2020.** §2.6 corrected
   that label repo-wide and it never reached the one script that stamps the CRS
   into every manifest. Corrected to GDA94.

**The two typed extents are relocated, NOT fixed.** The `#34` CBD box and the
harbourside corridor search window are declared in
`cities/newcastle/geometry/analysis_extents.json` at exactly their previous
values, labelled `assumed`, with #34 still open. The CBD box sets a
**pre-registered denominator** - the buildings whose floorspace
`D1_frontage_segments.csv` attributes per 50 m, which is the unit of test for
hypothesis B1 - and the standing instruction is to measure what a change moves
before changing it. Relocating a constant is not fixing it, and mixing the two
would have confounded the B0 verification.

**#36 is closed.** `CITYSIM_*` replaces the `WICKHAM_*` environment prefix,
`src/java/citysim/` replaces `src/java/wickham/`, `CitysimControler` replaces
`WickhamControler`, and the Java recompiles under the pinned toolchain. The OSM
layers lose the city prefix (`roads.osm`, not `newcastle_roads.osm`), including
in the `osm_pre_issue32/` archive, which is the only surviving copy.

**One breaking output change, taken deliberately.** The metrics key
`newcastle_lga_pct` is now `target_lga_pct` (and `newcastle_lga_trips` ->
`target_lga_trips`), in `metrics.schema.json`, `extract_metrics.py`, `fit.py`
and `outputs.py`. **Run records written before this cannot be read by
`fit.py`.** Every run on disk was already superseded and the B0 re-harvest
invalidates the rest, so the cost is nil now and would not be later. The value
it filters on is declared in `city.json` as `mode_share_target.filter_value`
rather than typed into three modules as `TARGET_LGA = 'Newcastle'`.

**What did not change.** No registry value, no sweep, no validation target, no
holdout row, no scenario definition. `check_package.py` reports the same single
pre-existing failure as before the work - the `RUN.telemetry.live_interval_s`
consumers claim names `TelemetryConfigGroup.java`, which spells the parameter
`liveIntervalS` and never mentions the registry key. That claim was false
before this change and is left for a decision rather than quietly deleted.

**Second pass: the study's own documents moved with it.** The first pass left
the framework holding this city's *records* - the research design, the decision
log, the board, the audits, the handover notes and the two generated references.
All of it is now under `cities/newcastle/docs/`, and `docs/` documents the
framework alone. The three generators write into the city that owns the document
(`render_docs.py`, `build_data_dictionary.py`, `report.py`). Three further
builders followed their logic into the city: `build_landuse_parking.py` (the D1
frontage attribution that hypothesis B1 is tested on), `build_sumo_corridor.py`
(the corridor itself) and `map_sa1_to_lga.py` (ABS statistical geography, which
is a jurisdiction's construct, not a framework concept).

**And the portable half stopped quoting one city.** `required_fields.json` was
copying each field's DESCRIPTION out of the reference registry, which put this
city's suburbs, agencies and datasets inside `config/schema/` - 213 place
mentions in the one file that is supposed to be city-free. Descriptions are now
omitted: the contract states a key, its units, its value type and whether it must
carry a sweep, and *why a particular city chose a particular value* stays in that
city's `CONFIG_REFERENCE.md`. Measured across the framework, place and
jurisdiction mentions fell from **~2,900 to 262**, and within `config/schema/`
from 213 to 23 - of which 12 are the repository's own name in schema `$id` URLs.

**Still no scenario run; no falsification condition altered.**

---

## 9.38 The 30-hour day is capped, not wrapped (P4 batch 4.1, issue #37)

**Decision:** a person's chains are CAPPED at the 24 h boundary whenever they
would collide with that person's own early morning; nothing is wrapped. Taken
15 August 2026.

The qsim horizon (`B.activity.day_horizon_s`, 30 h) exists so a late-evening
tour can arrive after midnight — hours 24..30 are 00:00–06:00 the *following*
morning. That is coherent only for an agent who is not also travelling in those
same early-morning hours of the modelled day. Measured on the seed plans before
this change: **2,066 WEEKDAY / 358 SAT / 240 SUN persons** (0.394% / 0.080% /
0.058%) had a departure both before 06:00 and at or after 24:00 — one person
with two 2 a.m.s ([`docs/audit/ISSUE_VERDICTS.md`](audit/ISSUE_VERDICTS.md)).

`build_activity_chains.py` now drops, whole, any tour containing a departure at
or after 24:00 when the person also departs before the tail hour
(`day_horizon_s` − 24 h); the external tier applies the single-tour form of the
same rule. **Cap, not wrap, because wrapping the spilling chain onto the early
morning would create exactly the collision being removed.** The drop is counted
per day type in `_activity_chains_report.json`
(`tours_dropped_midnight_collision`) and touches well under 0.5% of agents, so
the solved trip rates are not re-derived. Late departures that do NOT collide —
the legitimate use of the tail — are untouched.

**Acceptance (all three day types): zero persons with a departure both before
06:00 and at or after 24:00.**

---

## 9.39 Bike availability is drawn, and the asymmetry is no longer silent (P4 batch 4.1, issue #29)

**Decision:** bike availability is a per-person draw at
`B.population.bike_available_rate` — **assumed 0.50, swept 0.30–1.00** — with
1.0 in the sweep reproducing the previous behaviour. Taken 15 August 2026.

Until this change car was the only mode whose ownership was modelled, so it was
the only mode that could be denied to an agent: the uninformed seed read
availability straight off (car 15.72%, bike 22.67% of legs), a structural bias
against car in the choice set itself, and **nothing in the registry or this file
said so** (SPEC_AUDIT A3). The census carries no bicycle-ownership variable, so
any rate is assumed; what was not defensible was the asymmetry being
undeclared.

Mechanics: `build_matsim_plans.py` draws per person from a seeded child stream
(`[seed, 1]`, so the mode-seed stream is unperturbed), writes `bikeAvail`, and
excludes bike from the seed draw of a person without one — the seed must respect
the constraint or ChangeExpBeta can re-select an illegal plan forever, the
defect class measured at 4,723 ride legs in §9.15.
`citysim.AvailabilityModesCalculator` (successor to
`RideAvailabilityModesCalculator`) strips bike from SubtourModeChoice's choice
set the same way it strips ride. **External boundary agents keep bike
available**: they are household-less by construction, so no ownership identity
exists to derive a denial from.

**The rate must not be sized against the old 5× finding** — that share was
measured on a model that no longer exists. Re-measure the modelled bike share on
the first post-rebuild run, then size, and log the sizing here.

---

## 9.40 The gravity decay is solved per purpose × home LGA (P4 batch 4.1, issue #30)

**Decision:** destination-choice decay is calibrated per (purpose × home LGA)
against that LGA's own HTS `JOURNEY_AVG_DISTANCE` row, with the five-LGA
aggregate solve retained for suppressed cells and for the external tier (a
boundary agent has no home LGA). Taken 15 August 2026.

The defect this closes is a frame mismatch inside the builder itself: one beta
per purpose was bisected against the five-LGA journey-weighted mean and **hit it
to two decimals** (education target 6.44 network km, realised 6.44) while
missing every LGA's own mean — the HTS publishes education at **3.0 km for a
Newcastle resident and 12.9 km for a Port Stephens one**, and a single decay
reproduces neither. Measured per home LGA on the old plans: education Newcastle
**1.86×** its own row, Maitland 1.41×, Cessnock 0.92×, Lake Macquarie 1.01×,
Port Stephens 0.54×. The five-LGA headline ("education 2.19×") in issue #30 was
itself produced by comparing all-core distances against the Newcastle-only row;
both framings are superseded by the per-LGA solve, whose per-cell
targets-vs-realised are recorded in `_activity_chains_report.json`
(`decay.<purpose>.by_lga`).

The intermediate-stop decay keys on the zone the traveller is currently in, not
their home LGA — the current zone is the origin of that leg, and its LGA is the
better proxy for the local opportunity surface.

This is a demand rebuild; every prior run comparison is already void under
§3.5. The sub-1-km scarcity (4.9% of legs under 1 km against an observed walk
share of 13.4% at mean 0.7 km) is expected to ease for Newcastle residents but
is **not** asserted fixed — re-measure the distribution, not just the means,
after the rebuild.

---

## 9.41 Through traffic enters the model at the cordon's own observed volumes (P4 batch 4.1, issue #20)

**Decision:** a through tier is added to B2 — trips that enter at one cordon
gate and exit at another without any activity inside the study area. Taken
15 August 2026.

The radial external tier (§9.14, §9.15) sends boundary residents *into* the
core and home again; by construction nothing crosses, so the M1 at Wyee —
**48,016 observed AADT, calibration target V113** — carried zero modelled
vehicles, and every boundary-adjacent count was biased low exactly where
through traffic dominates.

Mechanics, all declared and swept, none pinned:

- A **gate** is a major-road edge crossing the dissolved study boundary whose
  ROAD demonstrably continues outward: some same-named endpoint within
  corridor-match range of the crossing lies at least
  `B.external.through_outside_min_m` beyond the boundary (assumed 1 km, swept
  0.3–3). Road-level, not edge-level, because the crossing way itself often
  ends metres past the polygon — measured on the rebuilt layer: the Hunter
  Expressway's crossing edge ends 61 m out and the Pacific Highway's 31–96 m,
  while their roads continue 1–8 km; an edge-level test admitted only the M1
  and silenced the tier. The outside test exists because the dissolved boundary
  includes the coastline and the harbour, so Hannell Street's Hunter River
  bridge "crosses the boundary" without leaving the study area (nothing of the
  street reaches 3 m beyond the polygon) — the measured false positive that
  would otherwise have seeded through traffic entering in central Newcastle.
  The pre-existing cordon-crossing set could not serve: it is derived from the
  external zones, which lie only on the Hunter Valley side, so the M1 toward
  Sydney — the single most through-dominated road — had no crossing near it at
  all.
- The gate's volume is the nearest **calibration** count station **on the same
  named road** within `B.external.through_corridor_match_km` (assumed 30 km,
  swept 10–50). Measured motivation: only the M1 at Wyee has its station at the
  crossing itself (273 m); the other boundary corridors are counted 16–24 km
  inside (Pacific Highway at Tomago, New England Highway at Tarro), so the name
  carries the corridor identity and an inland station **overstates** the
  boundary volume by its local traffic — absorbed, stated, by the
  `through_share` sweep. The split filter is structural in `through_gates()`:
  **no holdout row can seed demand.** Same-corridor crossings within the match
  distance collapse to the highest-volume one.
- Inbound volume at gate *i* is `0.5 × B.external.through_share × AADT_i ×
  B.external.day_factor[day]`. The share of a boundary station's AADT that is
  through traffic is **unobserved** — no journey-linked source can separate it —
  so it is **assumed 0.35 and swept 0.15–0.60**. The 0.5 is an identity, not a
  parameter: AADT counts both directions, and the exiting half is generated by
  the opposite gate as its own inbound.
- The exit gate is drawn ∝ the candidate gates' observed volumes, restricted to
  gates at least `B.external.through_min_separation_km` away (assumed 30 km,
  swept 20–50), so a "through" trip genuinely crosses the area rather than
  hopping between two gates on the same corridor edge.
- Departure times use the declared HO profile — through traffic has no observed
  profile of its own, and inventing a bespoke one would be a second assumption
  doing the same job.
- **The mode is locked.** A volume anchored on a road count must stay on the
  road, so a through agent carries `lockedMode=car` and
  `AvailabilityModesCalculator` returns exactly {car} for it —
  SubtourModeChoice cannot leak the anchored volume onto another mode. The
  agents ride in subpopulation `external` (they are boundary-tier agents;
  `agent_tier=through` distinguishes them in every artefact).

**Known limitation, measured on the rebuilt layer:** the northern and
north-western exits are not yet gated. The Pacific Highway's outward
representation at Karuah reaches only 259 m beyond the boundary and the New
England Highway's 887 m — way-length luck in the harvest, not road truth — so
both fall short of the 1 km evidence minimum, while lowering it toward the
100–250 m range would admit the Hexham river bridge (Pacific Highway trunk,
31–96 m "outside" over the Hunter inside the study area) as a false gate. The
first build therefore gates the M1 (48,016), the southern Pacific Highway
(20,701) and the Hunter Expressway (33,882); the missing exits are reachable
through the `through_outside_min_m` sweep and should be revisited when the
tier is re-examined after issue #5.

**What this is not:** an estimate of through demand. It is a declared,
sweepable background load whose anchor is the cordon's own calibration counts,
built so the M1 can carry the traffic the observed data says it carries. V113
ceases to be an independent test of the model exactly to the extent the through
share is tuned against it — it is a calibration row, that use is what
calibration rows are for, and this note is the record of it. Count-based
calibration near the boundary remains gated on this tier being examined
(§9.14); freight remains absent and tracked by #24.

---

## 9.42 The taxi/rideshare separation is re-opened on new evidence; nothing is built yet (18 August 2026)

§9.21's subsection "Taxi, motorcycle and rideshare cannot be separated" declined
separate point-to-point modes because **no target existed**: the HTS reports
"Other" as one bucket, and IPART's survey measures usage incidence, not
Newcastle trip share. That reasoning stands. Two things about the evidence have
changed since it was written, and the rule this file lives by is that a settled
decision is re-examined exactly when new evidence appears:

1. **IPART's annual Survey of Point to Point Transport Use now samples
   "Newcastle and Hunter" as its own region**, with year-on-year trend
   (rideshare use growing ~18%/yr in Newcastle in the survey the Herald
   reported). Incidence × reported frequency × population yields an
   approximate regional daily point-to-point trip volume — an observable,
   though a derived and weak one.
2. **The NSW passenger service levy ($1.20/trip) means the Point to Point
   Transport Commissioner records every taxi, hire and rideshare trip.**
   Regional aggregates are not published, but they exist, and a data request is
   the same route this project already uses for TfNSW inputs. Levy counts for
   the five study LGAs would be a genuinely observed daily volume.

**Decision taken:** (a) **no data request is lodged.** The levy aggregates
exist, but the project's directive (18 August) is that this project infers the
volume from open sources rather than waiting on an agency response: a request
has a long lead time, an uncertain answer and no bearing on work that can
proceed now. The IPART survey incidence, the regulated fare schedule and the
published fleet size are open, and every value inferred from them is
**labelled with its grade and swept** — never quoted as observed. (b)
**nothing is built before deliverable 5** — a point-to-point mode is a
refinement inside the 3.2% "Other" bucket and sits behind three measured
multi-point defects (ride, walk, counts); (c) if built, it enters as a **priced
teleported mode** — IPART-regulated taxi fares as `measured`, rideshare base
rates as `literature`, surge and fleet unknowns swept — and is validated
against the IPART-derived volume band as a **constraint, never a target**: the
67/143 split is pre-registered and does not grow (§12). No fleet simulation —
a DRT contrib is a §14 toolchain change unjustified at this share. The HTS
decomposition remains impossible; that half of §9.21's finding is unchanged.

Recorded so the trade is visible: declining the request means the point-to-point
volume stays a **derived and weak** observable — an inferred band, not a
measured count. That is the accepted cost of not blocking on an agency, and it
is why the band constrains rather than targets.

Relevance recorded for honesty: rideshare competes with the light rail for
short CBD and night-time trips — the same trips hypotheses B1/B2 measure — so
the mode's absence is a stated limitation of the footfall analysis until this
lands.

---

## 9.43 The iteration count is declared at 1000, and the drift window it is scored on was measuring the wrong thing (18 August 2026)

Issue #5 — *how many iterations does this model need?* — has blocked every
downstream deliverable since §9.7. It is now closed on measurement, and closing
it required fixing the instrument first, because **the declared relaxation gate
could not have been passed by a run of any length.**

### What was run

Two full arms on the 16 August rebuild, one at a time, same network build
(§3.5), threads 10, seed 20260810:

| | `conv1000_10pct` | `conv1000_25pct` |
|---|---|---|
| fraction × iterations | 10% × 1000 | 25% × 1000 |
| agents | 54,617 | 136,068 |
| wall clock | 10 h 59 m | 30 h 47 m |
| median iteration | 33.3 s | 90.2 s |
| exit / accounting / telemetry | 0 / closes / clean | 0 / closes / clean |

Full evaluation, including the structural findings that are not about
convergence, in
[`docs/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md).

### The instrument was broken, and it was broken in a way that always failed

The declared gate measured per-mode mode-share movement **from the innovation
cutoff to the final iteration**, against `RUN.relaxation.drift_tolerance_pp`
= 0.5 pp. Both arms failed it identically: worst-mode drift **+3.54 pp** (10%)
and **+3.60 pp** (25%), car in both. Identical failure at two sample fractions
is not the signature of a run that needs longer; it is the signature of a
measurement artefact.

Reading the per-iteration trace rather than the 10-iteration grid identifies it
exactly. **The entire movement is one iteration wide.** At iteration 801 —
the first iteration after innovation is disabled — car jumps **+3.256 pp**
(10%) and **+3.380 pp** (25%), walk falls 3.97 → 1.02% and pt 1.08 → 0.25%.
Iteration 802 onward moves by hundredths of a point. When MATSim stops creating
new plans, exploration noise stops with it and selection concentrates every
agent onto its best-scoring remembered plan in a single step. That is a
property of the scoring and replanning structure — it would occur at iteration
201 of a 250-iteration run and at iteration 1201 of a 1500-iteration one — and
a window that begins at the cutoff swallows it whole.

**So the gate was unpassable by construction.** A perfectly relaxed run of any
horizon reports ~3.5 pp of "drift" and is declared unsettled. The pilots did
not fail to converge; the instrument failed to measure convergence. This is
recorded as a defect of the metric, not a finding about the model.

### The window now starts after the snap, and the snap is still reported

A new field, `RUN.relaxation.settle_margin_iterations`, declares how many
iterations after the cutoff the drift window opens. **Value 10, swept 1–100.**

- The **lower bound is the measured snap duration** — one iteration, at both
  fractions — so 1 is the smallest margin that can exclude it.
- **10 rather than 1** is a 10× guard on a one-iteration phenomenon, and matches
  the 10-iteration interval the outputs are written on. It is not tuned to pass:
  margin 1 already passes at both fractions.
- The **upper bound is where the excluded window becomes a meaningful share of
  the 200-iteration post-cutoff tail.** Beyond it the metric would pass by
  measuring less rather than by the run being flatter, which is the one failure
  mode this field must not have. That is also why the margin was NOT set to 50
  or 100 even though both pass more of the tolerance sweep (below).

`summarise_run.py` now reports three quantities instead of one, so the fix
hides nothing: `snap_pp` (the movement across the margin), `drift_pp` (the
settle point to the final iteration — **the verdict is scored on this**), and
`cutoff_to_final_pp` (**exactly what the old instrument reported**, kept so the
window change is auditable and the old verdict re-derivable without re-reading
the run). The re-derived old numbers reproduce +3.537 and +3.599, matching the
evaluation to the third decimal, which confirms this is a window change and not
a recomputation.

### The declaration

`RUN.controler.last_iteration` moves from `unobtained` / null to **`measured` /
1000**, and the corresponding entry leaves `city.json`'s `unobtained` list. The
sweep stays 250–2000, with a changed basis — see the honest limit below.

Measured at the declared margin:

| | 10% arm | 25% arm |
|---|---|---|
| snap at cutoff (worst mode) | +3.31 pp | +3.43 pp |
| **drift, iteration 810 → 1000** | **+0.22 pp** | **+0.17 pp** |
| verdict at tolerance 0.5 pp | ✅ settled | ✅ settled |

**Fraction-independence is established** — snap size, post-snap drift, creep
decay and stuck-agent profile replicate at both fractions — so the 10% arm is a
valid convergence probe for 25% conclusions.

### What is NOT measured, stated plainly

Three limits ride with this declaration and must be quoted with it.

1. **1000 is measured to leave the model RELAXED. It is not measured to be
   enough SEARCH.** Car mode share was still creeping at the cutoff: per 100
   iterations at 25%, +1.94, +1.43, +1.04, +0.76 across iterations 400→800, a
   geometric decay of ×0.73 per block, with the 10% arm showing the same +0.75
   at 700→800. Extrapolated, **roughly 2 pp of movement remained in the
   innovated state when innovation froze it.** The post-cutoff state is settled;
   what it settled *onto* is a state the search had not finished exploring.
2. **The arm that would have measured this directly was cancelled.**
   `conv1500_10pct` (cutoff at 1200) was launched to test the extrapolation and
   was **stopped by instruction for compute economy** — the two completed arms had
   already cost 42 hours, and the ride-scoring defect (§9.44 lane, issues #28
   #31 #9) was judged the better use of the machine. **This is a deliberate
   trade of certainty for compute, and it is recorded as such.** The residual is
   carried as declared uncertainty, not resolved. The sweep's upper bound is
   therefore no longer a budget limit: it is the open half of the question.
3. **The verdict does not survive the whole tolerance sweep.**
   `RUN.relaxation.drift_tolerance_pp` sweeps 0.1–1.0 pp. At the declared
   margin the arms pass at 0.25, 0.5 and 1.0 pp and **fail at the 0.1 pp
   floor**. The movement keeps decaying with margin — +0.089/+0.088 pp at 50,
   −0.008/+0.033 at 100 — which is the signature of genuine relaxation rather
   than a metric artefact, and a larger margin would pass the entire sweep. It
   was declined for the reason given above: passing by measuring a shorter
   window is not passing.

Anyone reporting a result from a 1000-iteration run states limit 1 beside it.

### Consequences

- Shipped scenario configs carry 1000 instead of the sweep floor of 250.
  `shipped_iterations()` resolves the declared value and falls back to the floor
  only if the field is ever returned to `unobtained`, so making it provisional
  again cannot silently ship an undeclared number. `run_matsim.py` still gives
  `--iterations` no default: a run states the horizon it used.
- The 25% × 1000 arm costs ~31 h on the current machine. **Run economics, not
  convergence, are now the binding constraint on the campaign** — memory model
  ≈ 24 GiB fixed + 0.09–0.3 MB/agent, so a 100% run needs ~80–160 GiB of heap
  (§9.5).
- Issue #5 closes. #9, #14 and the ride sitting are unblocked.


---

## 9.44 A car passenger names a driver — and the measurement says there is almost never one to name (18 August 2026, issue #31)

The standing goal asks that **every form of transport be in action physically**.
Five of nine modes already are (§9.36 measured them: 1,448 buses, 332 trains,
252 trams, 107 ferries, all sharing road links with cars where they should).
`ride` — a car passenger — was the one whose absence was structural rather than
missing: it is routed over the network, reads congested car travel times since
§9.26, and is then **teleported**, consuming no capacity and, decisively,
**bound to no driver**. Tier 1 of the pairing is built. What it measured on the
way is more important than what it does.

### The mechanism, and why it is a lookup rather than a search

A joint-plans implementation on socnetsim was built, measured and reverted by
recorded instruction: it ran **iteration 0 alone for over 16 minutes** against a
~42 s baseline, and the cost was not the group replanning but
`CourtesyEventsGenerator` firing an event for every social-contact pair at every
activity start and end — 16.7 M events by sim-hour 15 — which is joint-ACTIVITY
machinery answering a different research question.

What makes boarding a bus cheap in MATSim is that the timetable is **fixed
before routing**, so the passenger does a lookup. A household car can work the
same way. The pairing is made in a `BeforeMobsim` listener
([`RidePairingEngine`](../../../src/java/citysim/RidePairingEngine.java)):
MATSim's loop is `replan → all plans final → mobsim`, so at that boundary every
selected plan is stable and nothing will move until the mobsim runs. **That is
the timetable.** A pairing made there is re-made every iteration, exactly as a
public-transport connection is re-found on every re-route — which dissolves the
objection that sent the previous attempt to socnetsim, since a pairing baked
into *plans* is destroyed by `SubtourModeChoice` and a pairing made *after*
replanning is not.

**How a passenger takes the driver's time with no mobsim change.** Verified
against the pinned jar's bytecode rather than assumed from the API:
`DefaultTeleportationEngine.handleDeparture` asks the agent for
`getExpectedTravelTime()`, which is `TimeInterpretation.decideOnLegTravelTime`,
which is exactly `route.getTravelTime().or(leg.getTravelTime())`. The **route's**
time therefore wins — and both routing modules set the leg's and the route's
time *together*. So the engine writes **only the route's time and never the
leg's**, and that single choice buys three things with no bookkeeping:

- the router's own estimate survives in `leg.getTravelTime()` and is the baseline;
- an **unpaired leg is restored to exactly that baseline**, which is what makes
  "an unpaired leg behaves exactly as it does today" a guarantee rather than a hope;
- the baseline refreshes itself when the router re-routes, and survives the plan
  copying that replanning does, because it lives in the plan and not in a side map.

The driver's time is the one **realised in the previous mobsim** — that is where
the sample-dependent queueing lives, which a teleported passenger is structurally
immune to (§9.12), and it is the same one-iteration lag every travel time in
MATSim carries. Before the first mobsim the driver's routed time is used and the
fallback is counted.

**Verified at the consumer, not at the mechanism.** A three-iteration probe at 1%
(`ride_pairing_probe`, `window_only` so the paired path executes at all):
356 ride legs ended with a route time differing from their leg time, and for
every unambiguously testable case the **realised teleport duration equalled the
route time the engine wrote, never the baseline**. The realised-time lookup fires
from iteration 1 (284 of 336 pairings realised, 52 routed).

**And then tested at two horizons, because the probe could not see replanning.**
Three iterations proves a binding; it does not prove the binding survives
`ReRoute` replacing routes and `SubtourModeChoice` copying plans, which is
exactly where a pairing made at `BeforeMobsim` could rot. Two arms, each with a
committed overlay:

| | `ride_pairing_50_declared` | `ride_pairing_25pct_declared` |
|---|---|---|
| what it answers | durability over iterations | cost and behaviour AT SCALE |
| fraction × iterations | 1% × 50 | **25% × 10** |
| exit / accounting | 0 / closes | 0 / closes |
| median iteration | 7.2 s | 53.7 s |
| ride legs | 3,923 → 7,736 | 103,240 → 126,925 |
| **pairing cost per iteration** | **5–6 ms, flat** | **184–310 ms, flat** |
| driver time source | realised on every pairing after iteration 0 | same |
| capacity refusals | 0 | 0 |

**The blast radius was then MEASURED against a control**, because "an unpaired
leg behaves exactly as before" is a claim and not an observation.
`ride_pairing_25pct_control` is the same run with `B.ride.pairing_enabled`
false — which is what that field exists for. Against the declared arm:

| | result |
|---|---|
| per-iteration mode share, all 5 modes, all 11 iterations | **BIT-IDENTICAL to 17 significant figures** |
| ride legs whose route time was rewritten | **7 in the paired arm, 0 in the control** |
| `ride_pairing.csv` | present / **absent** — the module governs installation, so a config that does not want it never builds the listener |
| `scorestats`, max abs difference | **3.8e-05** utils |

The two halves matter together. The rewrite count and the score delta prove the
mechanism DID something, so the identical mode share is not a no-op hiding
behind a control. And the identical mode share proves it did that something to
**7 legs of ~120,000 and to nothing else** — which is what a bounded blast
radius looks like when it is measured rather than asserted.

**And the paired path was stressed at volume.** The declared rule pairs so
little that arm A barely exercises the arithmetic, so `ride_pairing_25pct_stress`
runs `window_only` at the sweep's upper bound: rc=0, and it pairs
**14,406 → 18,489 legs an iteration** (13.5–14.6%) instead of 3–5. The cost is
**192–310 ms after the first iteration — the same as the arm that paired five
legs.** That is the design's complexity showing itself honestly: the cost is the
plan WALK, O(persons × plan elements), and the pairing itself disappears into it.
The capacity cap also fired for the first time (7–21 refusals an iteration), so
that branch is exercised rather than merely written, and the realised-time
lookup carried 12,954 of 14,255 pairings at iteration 1 with the rest taking the
routed fallback, exactly as specified.

Iteration duration is NOT a clean reading here — 80.0 s against arm A's 53.7 s
and the control's 61.7 s, on a machine where the control did LESS work than arm A
and still ran slower. The listener's own cost is measured directly and is 0.3% of
an iteration; the rest is model state and machine variance, and §9.5's warning
that iteration duration does not survive contention applies.

The cost scales with the population and with nothing else — ~25× the agents for
~25× the cost — and it is **0.4% of a 25% iteration**. Neither arm drifts,
leaks or slows across its horizon. **1% was not sufficient on its own and is not
claimed to be:** it is a plumbing fraction whose flow-capacity granularity
strands car legs (§9.12), so a mechanism that transmits REALISED congestion
cannot be judged there. The 25% arm is the one that speaks to the shipping
configuration; the 1% arm is what makes the long horizon affordable.

### What was declared, and one thing that was refused

Five fields, all in `B.ride.*`: `pairing_enabled`, `pairing_window_min` (15,
swept 5–60), `pairing_rule` (`both_links`, swept over four), `pickup_dwell_s`
(**0.0**, swept 0–120) and `max_passengers_per_vehicle` (4, swept 1–4).

**A pickup friction is not a fitted parameter, and the default is neutral for a
reason.** The car-minus-ride residual this lane exists to remove was measured
from the arms' own `output_legs` at **≈5 s at 25% and ≈13 s at 10%**, flat across
every distance bin below 50 km — a fixed overhead, not a speed error. A
one-minute pickup friction would be **five to twelve times the entire quantity it
was meant to explain**. Sizing one to close that gap is calibration wearing a
mechanism's clothes, and it was refused. It is swept so the question stays open,
never pinned.

**Return trips pair independently**, not as round trips. `ride` is correctly not
chain-based — a chain constraint exists to bring a *vehicle* back to where it was
parked and a passenger owns none; asymmetric lifts are the realistic case; and
forcing symmetry would **manufacture car trips**, the direction of error this
project is most exposed to. The obligation that creates is to report the
asymmetry, which `ride_pairing.csv` does every iteration, split by direction.

### The measurement, which overturns the lane

[`measure_ride_pairability.py`](../../../src/analyse/measure_ride_pairability.py)
reads a completed run's own `output_trips.csv.gz`, joins each traveller to their
B1 household, and asks whether any household member made a car trip the passenger
could have been inside. On the two relaxed arms:

| | `conv1000_10pct` | `conv1000_25pct` |
|---|---:|---:|
| ride trips | 79,372 | 185,170 |
| in a household that drives **at all** that day | 32.6% | **43.1%** |
| sharing an origin–destination pair with a household car trip, **at any time** | **0.039%** | **0.104%** |
| pairable under the declared rule (`both_links`, ±15 min) | 0 | **7** |
| pairable with **no spatial constraint at all**, ±60 min (the sweep's upper bound) | 3.9% | **9.6%** |

**`ride` is 32.7% of trips in the relaxed 25% arm and essentially none of it can
physically happen.** The modelled passenger:driver ratio is 0.52 against an
observed 0.35, but the relevant number is not the ratio — it is that fewer than
one ride trip in a thousand coincides in space with a household car trip.

Two independent causes, and neither is the pairing's:

1. **The sampler was shredding households.** That is §9.45, and it is fixed.
2. **B2 generates every person's chain independently.** An escort (`HX`) tour
   *is* generated — 44,258 escort trips in the 25% arm — but its destination is
   drawn from the education attractor *distribution*, not from the actual
   destination of the person being escorted, and its departure is drawn
   independently too. So a parent escorts to *a* school while their child travels
   to *another* one. The registry's older note that "B2 generates no escort trip"
   is stale; the trips exist, and what is missing is the **binding between the
   escort and the escorted**. A second, smaller incoherence falls out of the same
   measurement: **4,791 escort trips are made by `ride`** — a passenger being
   driven in order to convey somebody — because `B.activity.escort_requires_licence`
   constrains generation while mode choice may still turn the tour into a ride.

**What Tier 1 therefore achieves today is small, and is stated rather than
dressed up.** It pairs almost nothing under the declared rule, so it removes
almost none of the ~5 s residual and almost none of the fraction dependence. It
is still the right thing to have built: it is the mechanism that makes the
unservable demand a **per-iteration, auditable model output** instead of a
one-off script, it costs 3–20 ms an iteration, it is a strict improvement with a
bounded blast radius, and it is ready the moment the demand can supply a driver.
The looser rules quantify what a laxer assumption would buy and are sensitivities,
never results — the probe shows why: under `window_only` a paired passenger
inherits a driver's *unrelated* trip and comes out **+493 to +725 s** against
their own routed time, which is not a correction but a corruption.

**Tier 2** — the passenger as a real `MobsimPassengerAgent` inside the vehicle,
seats binding physically — remains an increment on this, not a prerequisite, and
is not worth building before the demand can pair.

### Not re-litigated

Do **not** add `ride` to qsim main modes (B2 already generates the escort
driver's car, so a ride vehicle double-counts the traffic) or to
`chainBasedModes`. eqasim's `PassengerConstraint` is a trip-level biconditional
on `getInitialMode()` that consults no driver: it compiles, runs, constrains
nothing and reports success. Non-household lifts are **not built** — no target
exists anywhere for them, and the 26.2% of households that are lone-person make
`Vehicle passenger` trips in HTS that this model can never serve; that gap is a
stated limitation, not a defect to close by invention.

### Consequences

- **Tier 1 changes the model.** Post-pairing runs are a new comparison family;
  the two convergence arms remain valid baselines for the *pre*-pairing model.
- The next lane is the **escort↔escorted binding in B2** (§13). It is a demand
  change, not a coupling change, and it is what would make this mechanism bite.
- Issue #31 moves from "unmodelled" to "modelled, and measured to be starved of
  supply". It does not close.


---

## 9.45 The sample was drawn per person, so it dissolved the households (18 August 2026)

The standing goal is explicit that if the model simulates a **percentage** of a
population, *"whether that scaling actually predicts the correct ridership per
mode must be CHECKED, not assumed"*. This is the first thing that check caught,
and it was invisible for as long as nothing in the model was household-coupled.

### What was wrong

`sample_population.py` kept a person if `blake2b(person_id | seed)` fell below
the fraction. Every property that mattered at the time survived it: the sample
**nests** (1% is a strict subset of 10%), it is seeded and deterministic, and
per-person attributes are untouched. What does not survive it is the
**household**, because each member is kept or dropped independently.

The arithmetic is not subtle. At fraction *f*, a household of size *n* retains
*f·n* members on average, and the probability that a given retained person keeps
**any** co-member is `1 − (1−f)^(n−1)` — about **0.14 at f = 0.10** and **0.32 at
f = 0.25** for the mean household size here. So a household-coupled mechanism
does not merely weaken under sampling: **its strength is a function of the sample
fraction**, which is the one thing a sample fraction must never decide.

Measured on the two completed arms, exactly as predicted:

| | `conv1000_10pct` | `conv1000_25pct` |
|---|---:|---:|
| ride trips in a household that drives at all | **32.6%** | **43.1%** |

That is the sampler talking, not the demand.

**What the fix does NOT buy, measured rather than assumed.** The obvious
inference — that intact households would raise the pairing rate — was tested and
is **wrong at any rate that matters**. The 25% × 10 mechanism arm above runs on
a HOUSEHOLD-sampled population and pairs 3–5 legs of 103,000–127,000, a rate of
**0.00004: the same as the person-sampled arm**, not higher. An intermediate 1%
arm showed ~0.0004 and briefly looked like the fix appearing, but that is 3 legs
out of 7,736 at a plumbing fraction and it did not survive the larger sample.

The two facts are consistent and worth stating together, because only one of
them is about the sampler. Keeping households intact raises the share of ride
legs whose household drives **at all** — that is structural, fraction-dependent,
and is what this section fixes. It does **not** raise
**origin-destination coincidence**, because B2 never co-locates household
members in the first place (§9.44). So the sampler was a real defect and had to
be fixed on its own terms, and fixing it moves the pairing rate essentially not
at all. **The escort binding is the whole of the remaining problem.**

### What changed

A new declared field, `RUN.sample.unit`, `derived` (it follows from what a
fraction is meant to mean, so it carries a `derived_from` identity rather than a
sweep), value **`household`**. The hash is taken on the household id instead of
the person id, so:

- **whole households are kept**, and every household-coupled mechanism is
  fraction-independent by construction;
- the sample still **nests** — one household hashes to one number, so the 1%
  sample stays a strict subset of the 10%;
- it stays seeded and deterministic;
- the **external and through boundary tiers carry no household by construction**
  and continue to hash on their own id, which is the same identity that already
  denies them `ride` (§9.15);
- `unit = person` reproduces every earlier sample **byte for byte** — the person
  key is unchanged and the household key is namespaced, so a household id and a
  person id that happen to be the same integer are still two independent draws.

Household membership reaches both consumers through **one** mechanism: a
`householdId` person attribute written into the plans by `build_matsim_plans.py`,
read by the sampler out of the plan stream and by
`citysim.RidePairingEngine` out of the person's attributes. A side file was the
alternative and was rejected: two copies of the same membership is the drift this
package cannot absorb (§15).

### The price, stated rather than hidden

A household-clustered sample carries **more variance at a given sample size**
than a person-wise one — the standard design-effect penalty for cluster
sampling. Nothing here estimates that penalty, and no seed-variance measurement
exists yet (`n_replications` stays 30 until it does). It is recorded so that a
later comparison of two fractions does not mistake cluster variance for a
mechanism.

### Consequences

- **This invalidates the two convergence arms as baselines for anything run
  after it**, because the sampled population is a different set of people. It
  does not invalidate §9.43: the iteration count was measured on the *post-snap
  settling behaviour*, which is a property of the co-evolutionary search rather
  than of which agents were drawn, and the arms remain the evidence for it.
- Every run from here is a new comparison family, which it was going to be
  anyway because Tier 1 changes the model (§9.44). The two changes therefore land
  together, deliberately, rather than costing two comparability breaks.
- The plans were regenerated to carry `householdId` and the 30 run-input sets
  reassembled. Both are deterministic and produced by committed scripts; the
  mode seed split is unchanged (`ride` 0.183 on the weekday set, as before).

---

## 9.46 The escort tour binds to the person being escorted (18 August 2026, issue #31)

§9.44 measured the starvation and §9.45 ended with its cause: *"B2 never
co-locates household members in the first place. The escort binding is the
whole of the remaining problem."* This entry is that binding.

### What was wrong

B2 generated escort (`HX`) tours — 44,258 trips on the relaxed 25% arm, the
rate calibrated to the observed `Serve passenger` 10–19.5% — but two lines
made the escort and the escorted strangers:

- `ATTRACTION_ALIAS = {'HX': 'HE'}` — the escort's destination was drawn from
  the education attractor **distribution**, never the escorted child's actual
  school;
- `DEPART['HX'] = DEPART['HE']` — the hour from the profile, never the child's
  own departure.

So a parent escorted to *a* school at *a* plausible time while their own child
travelled to *another* school at *another* time. Measured consequence: **0.104%
of ride trips shared an OD with a household car trip at any time of day** — the
supply the Tier 1 pairing (§9.44) was starved of.

### What changed

B2 now generates **households whole**: members without an escort draw build
first, and an escorter's `HX` tour takes an already-drawn household trip's
**destination and departure, exactly** — same coordinates, same second. The
bound tour is **immovable** in the escorter's timeline; their other tours flow
around it (a movable tour that would overlap is pushed past the escort's end —
drop the child, then go to work). An HX tour with no bindable candidate stays
unbound and draws from the distribution exactly as before — lone-person
households (26.2%) have nobody to bind to and must keep their observed escort
rate. **No tour is added or removed**: binding re-targets the tours the
calibrated rate already draws.

Four declared fields govern it (all `B.activity.*`): `escort_binding_enabled`
(definition — `false` restores §9.44's demand for comparison within one
build), `escort_binding_scope` (**assumed, categorical sweep** — with no
observation of who-drives-whom, *which* household trips may be bound to is a
declared choice: `any_member_trip` in priority order school-run first, against
`unlicensed_or_education` as the sensitivity), `escort_binding_min_gap_s`
(assumed, swept — how closely one driver can stack two runs), and
`escort_excludes_ride` (derived — below).

### Measured on the rebuilt demand (full population, 612,687 persons)

| | WEEKDAY | SAT | SUN |
|---|---:|---:|---:|
| HX tours drawn (rate unchanged) | 177,370 | 99,613 | 69,294 |
| **bound to a household trip** | **121,621 (68.6%)** | 68,935 (69.2%) | 47,399 (68.4%) |
| — to an unlicensed member's education trip (the school run) | 20,425 | 531 | 171 |
| — to an unlicensed member's other trip | 24,010 | 23,261 | 16,467 |
| — to an education trip | 2,799 | 77 | 17 |
| — to any member trip (4th class) | 74,387 | 45,066 | 30,744 |
| unbound (no candidate — lone-person households etc.) | 55,749 | 30,678 | 21,895 |
| mean network km, bound / unbound / HTS observed | 11.58 / 7.74 / 7.84 | 9.97 / 7.78 / 7.84 | 10.00 / 7.78 / 7.84 |

A bound anchor leg's destination coordinates and departure second are the
escorted trip's own — verified on the artefact, not the mechanism: **all
120,980 bound weekday anchors coincide exactly with another household
member's trip** (0 exceptions). The school-run class collapses at
the weekend (20,425 → 531 → 171) with the education tours it binds to, which
is the §9.2 day-purpose-mix expectation showing up in a mechanism that never
read it. The realised week trip rate is 3.382 against the HTS 3.473 (−2.6%;
the pre-binding build realised −2.2%) — binding re-targeted, it did not
inflate.

The bound escort's trip length is **reported against the observed
serve-passenger distance and not tuned**: a bound escort's length is the
escorted trip's own, and under `any_member_trip` the fourth priority class
(licensed members' own trips) pulls the mean above the HTS 7.84 km aggregate.
That is what the scope sweep exists to expose, and the number stands in
`_activity_chains_report.json` beside the observed value.

### The second incoherence: an escort trip made BY `ride`

4,791 escort trips on the relaxed 25% arm were made as a car **passenger** — a
person being driven in order to convey somebody, with no driver bound to
either. `B.activity.escort_requires_licence` constrains *generation*; mode
choice could still hand the tour to `ride`. Fixed where the lock already
exists: `build_matsim_plans.py` writes `rideAvail = never` for a person-day
whose plan carries an escort activity, and the existing
`AvailabilityModesCalculator` withholds `ride` with **no Java change**
(`B.activity.escort_excludes_ride`, derived from the same the-traveller-is-
the-driver identity). The approximation is plan-level because
`PermissibleModesCalculator` is per-plan, not per-subtour: the escorting
driver also cannot be *driven* on their other tours that day — stated, small,
and plausibly the truth.

### What this deliberately does not do

- **No invented target.** Eligibility derives from licence and household
  membership only; the binding priority is declared and swept, not fitted.
- **No return symmetry.** Return trips pair independently (§9.44); the
  measured direction split was uniform, and forcing symmetry would manufacture
  car trips — the error direction this project is most exposed to.
- **No non-household lifts.** Still not built; no target exists (§9.44).

### Consequences

- **A third comparability break, planned**: every run from here is a new
  demand family (with §9.44's model change and §9.45's sampler change, three
  breaks have landed as one).
- Whether the binding actually moves **realised pairability** is re-measured
  on the next 25% arm with `measure_ride_pairability.py` — "CHECKED, not
  assumed", and either answer is publishable.

---

## 9.47 The population had ~40,000 phantom elderly commuters and almost nobody over 84 (18 August 2026)

Task 4.2.6, sequenced after §9.46 because the escorted population — children
attending education, elderly non-drivers — is exactly the population this
entry repairs. Full evidence:
[`docs/design/age-structure.md`](design/age-structure.md). Three defects, all
in `build_population.py`, all measured on the built package before fixing
(the brief's numbers were reproduced, not trusted):

1. **The 75+ population mostly did not exist.** `age_sex_dist()` read
   single-year `Age_yr_<N>` columns, which G04 stops publishing at 79; ages
   80–99 live in grouped columns it never touched. Built: **186 persons 85+
   against a census 15,151**; 75–84 short 32%; ≈27,000 missing elderly, their
   mass redistributed to younger bands (+13–19% each). Fixed by apportioning
   the grouped columns to bands by year overlap.
2. **One flat employment rate for every adult.** The docstring claimed
   age-conditional labour force status; the code applied one flat G43 15+ rate
   (~57%), one flat FT share and a hardcoded 6% unemployment to everyone:
   65–74 built at **52.2% employed against a census 16.1%**, 75–84 at 47.8%
   against 2.4% — and prime age at 59% against 83%, so the model
   simultaneously over-generated elderly commuters and under-generated
   prime-age ones. Now drawn per **(SA1, sex, ABS band)** from G46A/B — loaded
   since P1, read by nothing — with the core-region band rate as fallback for
   the 7.4% of empty cells. Employment, FT/PT split and unemployment all take
   the cell's own rates; the flat scalars are deleted.
3. **Every under-18 was a full-time student, including all 22,115 aged 0–4.**
   G01 measures attendance: 32.0% at 0–4, 94.9% at 5–14, 72.6% at 15–19,
   37.9% at 20–24, 5.5% at 25+ — now drawn per SA1 with regional fallback.
   Under-18 attendees are full-time by definition (school); how an 18+
   attendee splits full/part-time is **not held** (G15 is the table, a
   deliberate non-acquisition) and is declared and swept as
   `B.population.tertiary_ft_share`.

**One structural consequence in B2:** the tour draw was `employed → work, elif
full-time student → education`, sending every employed student to work. With
real rates that would misdirect the 15–19 band, whose employment is 67%
part-time alongside study. Priority is now full-time work → full-time study →
part-time work; the rate solve uses the same reclassified fractions, so the
week-average trip rate stays calibrated to the HTS 3.473.

**Rebuilt population (612,687 persons):** 75–84 = 41,791 and 85+ = 16,188
(census 38,507 / 15,151); employment 65–74 = 15.3%, 75–84 = 1.5%, prime-age
83–84%, overall **53.3%** of persons (was 50.4% — the phantom elderly left,
the understated prime-age returned); students 0–4 = 31.9%, 5–14 = 94.7%.
Occupation and income stay drawn from SA1-wide distributions (they drive no
tour); the mobility-impairment ramp stays the only brake on the restored 85+
band's travel, and the private-dwelling assumption (no aged-care institutions)
is a stated limitation.

---

## 9.48 The re-measure arm: the binding moves pairability by two orders of magnitude, and the defect changes sign (20 August 2026, issues #31, #28, #9)

§9.46 ended with the measurement it owed: whether binding escort tours to the
person escorted moves **realised** pairability. The approved 25% × 1000
WEEKDAY arm (`bind1000_25pct` — S2 reference scenario, seed 20260810,
household sampling, threads 10, xmx 40g) is the **first run of the post-repair
demand family** (§9.44 + §9.45 + §9.46/§9.47, the planned triple break). It is
a valid run record: rc = 0, wall 34 h 44 m, median iteration 105.9 s,
**`relaxed: true`** (largest post-margin drift +0.09 pp, car), accounting
closes on every mode, stuck agents 0.028%, controler `5724c0df81fc1af9`.
`ITERS` pruned (124.5 GiB reclaimed); `_run.json`, `_summary.json`,
`_metrics.json`, `_fit.json` and `pairability_bind1000_25pct.json` stand in
`results/bind1000_25pct/`.

### The headline: pairability moved materially

| measure | pre-repair (`conv1000_25pct`) | post-repair (`bind1000_25pct`) |
|---|---:|---:|
| ride trips sharing an OD with a household car trip, at any time | 0.104% | **15.31%** (23,738 of 155,085) |
| paired under the declared regime (`both_links`, ±15 min) | 0.00004 | **0.0130** (2,014 trips) |

78.5% of ride trips are now in a household that drives at all that day.
Sensitivity across the declared grid: `both_links` ±60 min 0.0561;
`window_only` ±15 min 0.1303; `dest_link` ±60 min 0.1511 — full surface in the
JSON. Pairing is no longer outbound-only (engine telemetry at iteration 1000:
1,679 outbound, 239 return; the §9.44-era all-zero direction split stays
fixed). Capacity refusals: 0.

### The realisation gap, named and deliberately not chased

The demand provably contains the coincidence (15.31% OD-coincident; the build
placed 120,980 exact OD+time weekday bindings) but the declared regime
realises 1.30%. The factor of ~12 between them lives in the realisation
layers the handover brief anticipated: co-evolution must hand the escorter
`car` and the escortee `ride` on the same day before a bound pair can pair;
the ±15 min window applies to **realised**, not planned, departures; and
`both_links` requires both trips to resolve identical coordinates to
identical links. Under the brief's §4D branch this diagnosis is **not**
pursued now — pairability moved, the ride lane rests — and the gap is
recorded as the first question to reopen if #31's realised occupancy under
the declared regime (0.0053) ever becomes load-bearing.

### What else the arm measured (pre-calibration; §8.5's first branch was on record before this run)

- **The #28 residual**: `mean_driver_minus_baseline_s` settled at **~11.6 s**
  (was ~5 s at 25% pre-repair) — a paired passenger now takes a realised time
  measurably different from the router's estimate. Still not a fitted
  friction; `B.ride.pickup_dwell_s` stays 0.0, swept.
- **Mode share, Newcastle LGA linked, calibration targets only (35 of 67
  scorable)**: ride **31.05** (was 37.17; observed 20.60), car **63.95** (was
  57.76; observed 59.00), pt 0.36 (observed 3.80), walk-only 0.71 (observed
  13.40), other 3.92 (observed 3.20); MAE 6.45 pp over the 5 mode rows. The
  repair moved ride 6.1 pp toward its target; car crossed its own (−1.24 →
  +4.95 pp error).
- **Occupancy**: **0.4855** passengers per driver against the observed 0.3503,
  **outside** the declared [0.2493, 0.394] — the defect changed sign. The
  demand used to starve ride of drivers; the model now carries too many
  passengers per driver, and that is the **flattering** direction (more ride,
  fewer cars) for a rail forecast. Recorded, not tuned; it is the calibration
  decision's (4.2.4) problem to confront in the open.
- **ride:car trip-length ratio** 0.862 against the observed 0.961 (car
  geometry itself near-exact: modelled 10.40 km vs observed 10.20).
- **The restored elderly travel like the census says**: in the arm's plans,
  75–84 makes **0.7%** of its trips to work (52.4% other, 26.0% shopping);
  85+ **0%** work; 65–74 6.9% work; 0–14 zero work, zero escort, 49.5%
  education.
- **Traffic counts remain unusable as fit evidence** (mean −91%): the
  leg→vehicle conversion (#20's `B.counts.vehicles_per_*` fields) is
  declared-ahead and unwired, and 7 stations carry modelled zero (#19).
  Not new to this arm; recorded so −91% is not read as a finding.

### What this does not say

No number above is a finding about the light rail: the arm is the reference
scenario alone, pre-calibration (deliverable 5 not met), one seed, one day
type, no counterfactual. The fit rows are diagnostics feeding the calibration
decision. **No holdout row was opened.**

### The decision this evaluation feeds (brief §4D)

Pairability moved materially → **the ride lane rests**. Next in value order,
unchanged from the brief and pending the project's confirmation: **#24 freight**
(measured 6.52% of vehicles; improves every mode's congestion denominator),
then **4.2.4 / #14** — the §8.5 calibration decision, whose first branch
(ASCs on era 3, held fixed) was on record before this arm ran.

---

## 9.49 Freight enters the mobsim as a physical background load (20 August 2026, issue #24)

**Decision:** a `truck` mode is added to the model as a **declared, sweepable
background load** — not a freight demand model. Taken 20 August 2026, on the
recorded confirmation of the §9.48 value order. Issue #24's business-travel
half stays struck (B2 already generates WB at 2.11% against an observed 2.0%);
this entry is the freight half.

### What was absent, and what was silently wrong

No truck object existed anywhere in the build. `B.counts.heavy_vehicle_share`
(**measured** median 0.0652 across the classified stations) was applied at
comparison time only, so the corridor's road-space externality — hypothesis
B3, the decisive test of Claim B — was measured without the 6.52% of vehicles
that consume the most capacity per vehicle. Worse, the through tier (§9.41)
anchored each cordon gate's volume on an observed AADT **that includes its
heavy vehicles** and locked all of it to `car`: through trucks were already in
the model, riding as PCE-1 cars. The Hunter Expressway gate is observed at
**15.29% heavy** — roughly one in seven of its through vehicles was a truck
travelling with a car's footprint.

### The mechanism, in three parts

1. **Physical simulation.** `qsim.mainMode` = `car,truck`;
   `qsim.vehiclesSource` moves from `defaultVehicle` to
   `modeVehicleTypesFromVehiclesData`, with the run inputs emitting an explicit
   vehicles file: the `car` type restates MATSim's own default **exactly**
   (`RUN.qsim.car_vehicle`, 7.5 m / 1.0 m / PCE 1.0 — equality is what keeps
   the car fleet's physics unchanged), and the `truck` type carries
   `B.freight.pce` (**literature** 2.0, swept 1.5–3.5) and the regulated
   100 km/h cap (`B.freight.max_speed_kmh`, definition). The harness
   regenerates the vehicles file per run from that run's own resolution, so a
   swept PCE reaches the mobsim rather than a stale shipped file. Truck is
   allowed on every car link; **truck routing is otherwise unconstrained and
   is a stated limitation** — no truck-route network, curfew or bridge-limit
   layer exists in the package.
2. **Through freight.** Each §9.41 gate's volume now splits into car and truck
   by the gate station's **own observed heavy share** where classified (the
   Hunter Expressway, 0.1529) and the declared median where not (the M1 and
   the southern Pacific Highway, 0.0652 — their calibration stations carry no
   classified count). Each half takes its own observed day-of-week behaviour:
   the external day factor for cars, the **measured** freight day factor for
   trucks.
3. **Internal freight.** Truck trips = `B.freight.trip_ratio` (**assumed**
   0.0697 = 0.0652/(1−0.0652), swept **0.0–0.14** — zero turns the layer off
   so its whole effect is a sweep member) × the **observed** HTS car-driver
   share × the day's generated core person trips, re-shaped from the person
   day-of-week curve to freight's own measured one. Origins draw on an
   **observed** attractor — SA1 jobs weighted by the SA2's census
   place-of-work employment in the declared freight-generating ANZSIC
   divisions (`B.freight.attractor_divisions`) — and destinations draw on the
   same attractor under `B.freight.gravity_beta_per_km` (**assumed** 0.08,
   swept 0.03–0.20; no freight OD observation exists). One agent is one
   one-way trip: no local observation supports a tour or depot structure.

### What is measured, and what is assumed

**Measured, new to this change** (`extract_freight_profile.py`, from the RMS
classified hourly counts — 33,816 complete non-holiday station-days at 12
study-area stations): the heavy-vehicle **hourly departure profile** per day
type (the freight double-hump — 6.8% at 06:00, 6.9% at 07:00, 6.7% at 15:00 —
against near-zero overnight person travel) and the **weekend day factors**
(SAT 0.4627, SUN 0.4104 of weekday — person travel drops far less, which is
why the person shape is divided out before the freight factor applies).
**Assumed and swept:** the flow-share→trip-share transfer (`trip_ratio`), the
distance decay, the PCE. **Locked, not chosen:** a freight agent carries
`lockedMode=truck` in subpopulation `freight` — the existing
`AvailabilityModesCalculator` singleton path, no Java change — so mode choice
never trades a truck against anything; its scoring block exists because MATSim
requires one and is inert by construction.

### Verified, not asserted

- **The trucks physically move.** Smoke run `freight_smoke` (1% × 2
  iterations, rc=0, accounting closes): **913 truck trips completed, 922
  truck vehicles entered traffic, 140,380 link traversals across 28,428
  distinct links** — and 913 of the generated 90,393 weekday trucks at a 1%
  person-hash sample is exactly the expected scaling. Trucks appear in
  `all_residents_pct` visibly labelled and are structurally absent from
  `target_lga_pct` (a truck is not a resident of anywhere).
- **The car fleet's physics is unchanged, proven against the tool's
  bytecode, not the API docs** (the §9.44 discipline): the shaded jar's
  `VehicleType` constructor defaults are width 1.0 m, maxVelocity ∞, length
  7.5 m, PCE 1.0, flowEfficiencyFactor 1.0 — exactly what
  `RUN.qsim.car_vehicle` declares (omitted elements keep the constructor
  value). `createDefaultVehicleType()` adds only seats = 4, which is inert
  for a private vehicle: nobody boards a qsim car but its driver.
- **The loading path is real**: the first smoke attempt FAILED with `Could
  not find requested vehicle type = ride` — PrepareForSim demands a type for
  every NETWORK mode, not only the main modes — which is how we know the
  vehicles file is read at all. `ride` now carries a type restating the car
  values (a passenger rides in a car); it never enters the mobsim.
- **Generation conserves the through tier exactly**: 16,264 through cars +
  1,691 through trucks = the 17,955 through agents the §9.41 tier carried
  before the split. The escort binding is untouched: 121,621 of 177,370
  weekday HX tours bound, identical to §9.46. Week trip rate 3.383 vs HTS
  3.473 (trucks are not persons and do not enter the rate).

### What this is not, and what it breaks

Not an estimate of freight demand: a background load whose only purpose is to
make the congestion denominator every mode is judged against carry the heavy
vehicles the counts say are there. **No holdout row is read** — the gate split
uses the same structurally-filtered calibration rows §9.41 already reads.
**This is a planned comparability break**: the demand family changes again
(through composition, new freight tier, new vehicles source), so
`bind1000_25pct` becomes the last run of the §9.46/§9.47 family and nothing
run after this change compares to it. The count-comparison interaction is
recorded, not silently absorbed: modelled link volumes now contain trucks
while the #20 leg→vehicle conversion remains unwired — counts stay unusable as
fit evidence either way, and #20 owns making the light-vehicle comparison
truck-aware when it lands.

---

## 9.50 The calibrated base is constrained-and-reported, and the decision is logged before its run exists (20 August 2026, issues #14, #9)

**Decision:** deliverable 5 takes **§8.5's second branch — constrain and
report** — and this entry is written **before the base run of the §9.49
family has produced a single result**, which is the ordering §8.5 demands.
Taken 20 August 2026.

### Why not the first branch, which was on record

The plan of record said *ASCs on era 3 (2018), held fixed*. Attempting to
make that concrete exposes what it needs and does not have: **no 2018 demand
exists.** The population is synthesised from the 2021 census for a 2026 base
year; the era-3 GTFS feed is mapped, but a schedule is not a travel demand,
and the historical reconstruction that could carry one was **considered and
dropped** (backlog — *do not reopen*). Estimating 2018 constants by running a
2018 schedule under a 2026 population would fit the constants to a
year-hybrid that exists in no observation — manufacturing exactly the
confound §8.5 exists to prevent, with the extra step of looking rigorous.
The second branch is the one the rule offers for this situation, and the
project has used it before (§9.8, §9.17: `asc_car_passenger` constrained to
observed occupancy, the constraint reported).

### What "constrained" means, exactly

- **The six mode constants stay at their §8.5 priors, held fixed** —
  car passenger −0.85, bus −1.05, light rail −0.75, rail −0.65, walk +0.35,
  cycle −1.35 — with `asc_car_passenger` keeping its §9.8 occupancy-derived
  value. **Issue #9 (re-solve `asc_car_passenger`) is resolved by DECISION,
  not by a solve:** §9.48 measured occupancy at 0.4855 against the observed
  0.3503 — outside the declared range, in the flattering direction — and
  re-solving the constant against that would absorb a modelled defect into a
  behavioural parameter, the precise ASC-absorption move proposal §9 names as
  the primary threat to validity. **The excess is REPORTED in the calibration
  record instead.**
- **No parameter search runs.** The corrected loop (this change also fixed
  its rebuild-stage table, which had been defaulting unclassified consumers
  to "movable at run time" — the OSM harvest margins were in the movable
  set) identifies exactly **two** legitimately searchable parameters:
  `A.parking.max_stay_min` and `C.scoring.activity_minimal_duration_s`, at
  up to 21 full runs ≈ a month of 25% × 1000 compute. Neither can reach the
  structural misfits (§9.48: pt −3.4 pp, walk −12.7 pp, both diagnosed
  structural in §9.25/§9.28), so the search would spend weeks polishing a
  6.45 pp MAE it cannot materially move while LOOKING like calibration.
  Declined, with the cost stated. The loop remains built and gated for a
  future approved search.
- **The base is one reference run** of the §9.49 family — S2 × WEEKDAY,
  25% × 1000, seed 20260810 — whose fit against the 67 calibration targets
  is reported **as it comes out**. `params/C5_calibration.json` records the
  constrained parameter set with provenance, the branch decision, and that
  run's fit; the calibration report (deliverable 3) is generated from it.
  Misfits are stated with their §9.25 diagnoses, never tuned away by a
  constant.

### What this claims, and what it does not

This meets deliverable 5 in the only form the evidence supports: **a
declared, constrained base whose distance from observation is stated**, not
a fitted base whose distance has been absorbed. Every headline downstream
carries its sweep band (§8.1); the ASCs' provenance is `assumed (priors,
held fixed under 8.5)`; and the pre-registered 67/143 split is untouched.
If a future search is approved, it starts from this record and its
already-stated costs.

---

## 9.51 Four standing directives reset the value order, and the base arm is stopped (20 August 2026)

**Decision: four standing directives were issued at session close, each
overriding a recorded stance.** The 4.2.4 base arm (`base1000_25pct`,
~iteration 20 of 1000) was **stopped by instruction** and
quarantined to `results/_aborted_20260820/` — deliverable 5's C5/report
therefore remain open (#14, #9 stay open; PR #47 lands the §9.50 decision and
machinery only). Taken 20 August 2026, recorded before any research begins.

The directives, and what each supersedes:

1. **Every `ride` trip is a passenger PHYSICALLY in a car — no exceptions,
   no teleportation — and the ride share tuned to real life** (modelled
   31.05 vs observed 20.60; occupancy 0.4855 vs 0.3503). This **un-rests the
   ride lane** (§9.48's §4D branch) and **re-opens the joint-plans question**
   was previously closed by decision (socnetsim measured ~10× and reverted) —
   the cost is on record and any mechanism must re-confront it. Tier 1
   (§9.44) stays merged as the baseline mechanism until its successor lands.
2. **All nine or more modes distinguished and unique** — bus, train, light
   rail and ferry never reported under a `pt` umbrella; motorbike and
   taxi/rideshare individualised out of `car`/`Other`. This supersedes the
   *"motorcycle as its own mode: declined for want of a target"* stance to
   the extent an observed target exists — and one does: **verified at
   handoff, `census2021_G62_SA1.csv` carries per-SA1 journey-to-work counts
   for Motorbike/scooter, Taxi/Rideshare, Tram/light rail, Train, Bus,
   Ferry and Truck as distinct observed modes.** The no-invented-data rule
   stands: non-commute shares without an observation are swept, never
   pinned.
3. **The walk deficit is the priority structural defect**: the model
   generates too little sub-1 km trip mass (measured 2.5% of trips under
   1 km against an observed >~10%; walk 0.71% modelled vs 13.40% observed;
   modelled walk trips 2.43 km mean vs ~0.7 observed). **Issue #30 re-opens
   under its own REOPEN IF clause** — the first-run evaluation showed
   exactly the condition it named.
4. **Mode distributions conditioned on demographics — age, employment and
   the like — must match real life.** New observables enter as
   **constraints, never targets** (§9.8/§9.13 pattern); the pre-registered
   67/143 split is untouched.

**What did not change:** no target value moved, no holdout row was read,
nothing here is a finding. The §9.49 freight layer and the §9.50 branch
decision stand; what stopped was the base *run*, which needs relaunching
(~35 h at 25% × 1000, explicit approval required per the standing directive)
before C5 and the calibration report can exist.

---

## 9.52 Motorbike becomes a physical mode, carved from the demand that always contained it (20 August 2026, issue #49)

**Decision:** motorbike enters the mobsim as a **person-level locked carve
from car-driver demand**, anchored on the measured census journey-to-work
share. Taken 20 August 2026 under the §9.51 mode-individualisation
directive. This partially supersedes the old *"motorcycle as its own mode:
declined for want of a target"* stance — a target was found (below); the
no-invented-data rule still bounds what the mode can claim.

### The observed anchor, and what stays assumed

`census2021_G62_SA1.csv`, one-method journeys to work, 1,500 core SA1s:
**653 of 179,761 journeys (0.363%) by motorbike/scooter** — a genuinely
observed commute share for a mode the HTS cannot see (its data document
places motorcyclists inside `Vehicle driver`/`Vehicle passenger`, NOT in
`Other`). What remains assumed is the commute→all-purpose transfer:
`B.motorbike.trip_share` = 0.0036, **swept 0.0–0.01** (zero turns the mode
off). PCE is literature (0.4, swept 0.3–0.75 — a motorbike consumes LESS
road space than a car).

### The mechanism

- A licensed, car-available person becomes a motorbike user with the
  probability that makes carved persons' trips the declared share
  (q = 0.00518 over 426,129 eligible of 612,687). The draw is a **hash of
  the person id and the master seed** — deterministic, identical across day
  types, and consuming no rng stream, so every pre-existing draw sequence is
  byte-identical.
- **The day locks to the mode** (`lockedMode=motorbike`, the same generic
  availability-calculator path as through and freight): vehicle continuity
  is chain-based by nature, and no preference observation exists to let
  motorbike compete in mode choice — an invented constant is exactly what
  §8.5 forbids. **Except on escort days**: a pillion passenger is not how an
  escorted child travels in any held data, and the ride pairing pairs
  passengers with CAR legs — so an escort day falls back to normal choice
  (the `ESCORT_EXCLUDES_RIDE` day-plan pattern). This makes the realised
  share undershoot the declared 0.36% by roughly the escort-day incidence
  (~20% of weekday persons); stated, absorbed by the sweep, not compensated.
- Physically: `motorbike` joins `qsim.mainMode` and the per-mode vehicles
  file (PCE 0.4, no speed cap — it takes each link's own limit), and rides
  on car links like the other companions. The carve is FROM car seeding, so
  **no trip is invented** — car loses exactly what motorbike gains.
- **The comparison folds it back**: the HTS `Vehicle driver` target contains
  motorcyclists, so `fit.py` compares **car + motorbike** against it (the
  row is labelled `car+motorbike`), and the occupancy constraint's driver
  denominator does the same. Comparing car alone would under-read the model
  by exactly the declared carve.

### Verified, not asserted

Smoke run `motorbike_smoke` (1% × 2, rc=0, accounting closes): **12 carved
riders, 52 motorbike trips completed, 6,286 link traversals, zero stuck**.
Registry 319 fields, ledger 0 `--strict`; `check_city_agnostic` 13/13.
Landed in the SAME comparability family as §9.49 — the freight family has no
completed run, so no additional boundary is created.

### What this deliberately does not do

No motorbike CHOICE model (no constant, no competition — the share is
declared and swept); no non-commute observation is claimed; no separate
motorbike network layer (filtering/lane-splitting is inside the PCE sweep);
taxi/rideshare stays with task 4.4 and the tier plan in
[`docs/design/mode-individualisation.md`](design/mode-individualisation.md).

---

## 9.53 A paired passenger physically boards the driver's car (20 August 2026, issues #48, #28, #31)

**Decision:** the mechanism the #48 directive requires is **option C of the
dossier** ([`design/physical-ride.md`](design/physical-ride.md)) — chosen by
the measurement, not by taste: the §9.48 gap decomposition showed the three
realisation layers lose ×2.24 (mode co-assignment), ×6.91 (the realised
window) and ×2.73 (link resolution), and a passenger who is IN the vehicle
makes all three structurally unable to fail. Taken 20 August 2026.

### The mechanism

`JointRideEngine` — a qsim `MobsimEngine` + `DepartureHandler`, consulted
before the teleportation engine (teleportation claims everything, so the
component order is rearranged: network → jointRide → teleportation):

- **Pairing stays at BeforeMobsim** in `RidePairingEngine` (§9.44's
  soundness argument is untouched). With `ridePairing.physicalBoarding`
  (declared, `B.ride.physical_boarding`) each paired ride leg becomes a
  **booking** naming the driver.
- **Board**: the passenger departs on a ride leg holding a booking from that
  link, and the driver's car is still parked there → a real
  `PersonEntersVehicleEvent`, and the passenger rides every link the car
  traverses. Car vehicle ids are the person's BARE id — measured from the
  events (trucks are `<person>_truck`; car is unsuffixed), after the first
  probe missed 100% on the guessed `_car` form.
- **Alight**: when the car, having left the boarding link, reaches the
  passenger's destination link (under `both_links` it is the driver's own
  destination), the passenger leaves — `PersonLeavesVehicleEvent`, leg ended
  at the real clock, plan continues.
- **Miss = Tier 1 verbatim**: a booking whose car has already left falls
  through to the teleport carrying the driver's time §9.44 already wrote
  into the route — never a third behaviour, always counted. A passenger
  still aboard at mobsim end aborts through the standard stuck path.
- **The qsim's own boarding refusal now carries the declared cap**: the car
  type states seats = `B.ride.max_passengers_per_vehicle` (the jar's
  `QVehicleImpl` counts passenger capacity as seats + standing, driver
  excluded, and DEFAULTS TO 4 when unset — equal to the declared value,
  i.e. right by accident; now it is right by declaration).

### Verified, not asserted (probe `jointride_probe`, 1% × 2, rc=0, accounting closes)

- Engine counters: **boarded 67–71 per iteration, alighted 62–65, missed 2
  (driver already gone — the window layer wearing its physical face),
  absent 0, full 0**, aborted-at-sim-end 5–6 (drivers themselves stuck at
  2 unconverged iterations; re-measure at convergence).
- **Independently confirmed from the events**: 71 `PersonEntersVehicle`
  events at the exact second of a ride departure into ANOTHER person's
  unsuffixed car — household-adjacent ids visible — matching the engine's
  own count exactly.

### What this does and does not claim

Every PAIRED ride trip is now a passenger physically in a car. The
**unpaired majority is still teleported** on the router's estimate: making
them physical is not an engine question but the project's §4 re-moding policy
in the dossier — household-only service caps pairable ride FAR below the
observed 20.6%, and what unpairable demand becomes (re-moded, or a declared
unvalidatable lift allowance) is the decision #48 still awaits. The #28
residual ends for boarded pairs (their time IS the realised ride); the
missed count is the window layer's physical remainder and is reported per
iteration in `matsim.log`.

---

## 9.54 Walking and cycling become physical, and the qsim learns to tolerate the transit router's stubs (20 August 2026, issues #48, #49, #30)

**Decision:** `walk` and `bike` join the qsim's main modes — a pedestrian at
**PCE 0.0** (the sidewalk, expressed in queue arithmetic: physically on every
link, speed-capped at the declared walking speed, neither impeding nor
impeded by motor traffic) and a cyclist at **literature PCE 0.2 (swept
0.1–0.4)** who genuinely takes carriageway space. Taken 20 August 2026 under
the §9.51 all-modes-physical directive.

### The mechanism

- **Speeds are the declared quantities, consumed twice**: the vehicle type's
  `maximumVelocity` (walk = `A.transit.walk_speed_ms` 1.25; bike =
  `B.bike.speed_ms` 4.2, carried verbatim from the retired teleported field
  with its unresolved MATSim-vs-ATAP sweep) and `CappedSpeedTravelTime`, the
  router's estimate — read from the SAME loaded vehicle type, so estimate and
  physics cannot drift.
- **The road graph is the footpath proxy** (the observed footway network is
  data, not part of the one mapped build — §3.5 forbids a remap), with the
  road rules declared: walk excluded from motorway/trunk classes, bike from
  motorways (`A.network.pedestrian/bicycle_excluded_classes`). Exclusion
  severs pockets, and MATSim refuses a mode whose subnetwork has unreachable
  links (measured — the first probe died on it), so the build now strips each
  mode from links outside its largest strongly-connected component, MATSim's
  own MultimodalNetworkCleaner rule: **walk stripped from 16,726 links, bike
  from 5,177, counts reported never silent**.
- **Four teleported fields retired** (`teleported_walk/bike_speed_ms`, the
  two beeline factors): walk and bike no longer teleport, so their
  parameters ceased to exist. The **measured** walk detour factor (1.6902)
  survives in its one remaining teleported role — the access/egress stub —
  as `RUN.routing.access_walk_beeline_factor`; realised MAIN walk now
  detours at the road graph's own geometry (~1.34, the measured car factor),
  which **flatters walk slightly less than truth** and is stated rather than
  corrected (the direction is at least not against walk, which sits 12.7 pp
  under target).
- **MATSim's built-in teleported defaults cleared**
  (`routing.clearDefaultTeleportedModeParams` — they conflict with network
  walk outright, measured) and the helper mode `non_network_walk` declared
  explicitly: the stub's speed by identity with walking, the measured
  beeline factor, and — caught by the fixture-city test — its SCORING, which
  MATSim had been silently defaulting: stubs now carry walk's marginal time
  rate by identity and a zero constant, declared instead of inherited.

### The sharp edge, measured three times before it yielded

The transit router's access/egress and direct-walk legs keep **mode `walk`
with a generic route** (measured: 9,466 in a 1% day, all `routingMode=pt`),
and the stock agent source casts every main-mode leg's route to a
NetworkRoute — the probe died at agent insertion. `accessEgressType=none` is
declared (the vehicular stubs were beeline artefacts; measured to still
leave the transit stubs), and two narrow qsim components carry the rest:
`TolerantAgentSource` (parks mode vehicles only for network-routed legs;
refuses any vehiclesSource other than the declared one) and
`GenericRouteTeleporter` (claims main-mode departures whose route is not a
network route and teleports them on their own travel time — 4,100–4,300 PT
stubs per 1% iteration, refusing to invent a duration where none exists).
Main walking is network-simulated; the sofa-to-stop stub stays a stub.

### Verified, not asserted (probe `allmodes_probe`, 1% × 2, rc=0)

Walk 9,050 trips / bike 2,311 / car 3,785 / truck 912 / motorbike 52 / pt
1,166 in the final iteration, every network mode conserving in the events;
`vehicleBehavior=teleport` (MATSim's default, verified in bytecode) carries
vehicle relocation for the non-chained modes. One known reporting defect:
the summariser's per-mode STUCK attribution over-assigns a handful of
end-of-day aborts (events conserve exactly; the attribution does not) — fix
with the first converged run's close-out.

---

## 9.55 The unpaired ride trip walks, and the ride share becomes emergent (20 August 2026, issues #48, #28, #31)

**Decision:** with physical boarding on, an UNPAIRED ride leg is re-moded to
**network-simulated walk** at the BeforeMobsim boundary
(`B.ride.remode_unpaired`). This enacts the §9.51 directive's own ruling —
*every ride trip physically in a car, no exceptions, no teleportation* —
**without inventing a parameter**: a ride trip no household driver can
physically serve is not a ride trip; it walks, physically, at walking speed;
a long forced walk scores terribly; and co-evolution reassigns those tours
to feasible modes across iterations. **The surviving ride share is emergent
from the physical driver supply rather than declared.** Taken 20 August
2026.

- The re-moded leg's route is CLEARED, not kept: the car route may traverse
  walk-excluded links and PersonPrepareForSim refuses a route inconsistent
  with link modes (measured); a null route is re-routed as walk before the
  mobsim, so the leg is properly walked from its first iteration.
- Measured on the probe (1% × 2): iteration 0 re-moded **2,758** unpaired
  ride legs; by the final iteration **ride = 67 trips and every one of them
  is physically boarded** (64 boarded + missed fallbacks counted), walk
  carries the displaced mass for the co-evolution to redistribute. The only
  ride teleportation left is the counted boarding-miss fallback (5–6 per
  iteration — the ×6.91 window layer's remainder; ending it is a
  joint-departure-time replanning question, stated on #48).
- **The consequence accepted by issuing the ruling**: modelled
  ride at equilibrium is bounded by household pairability (OD-coincidence
  15.31%) and will sit FAR below the observed 20.60%; the gap is the
  unobserved non-household-lift share, REPORTED as such (dossier §4 option
  i). Where the displaced 30-odd percentage points of demand settle is the
  first converged run's headline measurement.

## 9.56 The events pipeline gets its own threads — a wall-time knob, measured before it was turned (21 August 2026)

**What was measured.** The all-physical model roughly triples the event
stream (a million-plus walk departures at 25%, each walking the road graph
link by link), and the first 25% shakedown of it (`phys50_25pct`, 50
iterations, rc=0, accounting closes) ran at a median **261.1 s/iteration**
against the §9.48 family's 105.9. The log attributes the difference: MATSim's
default events manager runs every handler on ONE thread
(`SimStepParallelEventsManagerImpl$ProcessEventsRunnable0`), and that thread
burned **172–177 s CPU per ~261 s iteration** — 10 qsim threads waiting on
one events thread at every sim-step sync, on a 24-CPU machine. On
event-writing iterations the same thread spiked to ~342 s.

**The decision.** `RUN.machine.event_handler_threads` = 4, bound to
`eventsManager.numberOfThreads`. UNLIKE `RUN.machine.threads` (§9.5) this is
NOT run identity: handlers are observers, each still receives the complete
stream, so nothing the model computes can change. That claim was VERIFIED,
not assumed, on 1% × 2-iteration twins of `allmodes_probe`: mode stats,
score stats and the event MULTISET are bit-identical with the knob off, on,
and on-again (`evthreads_ab`, `evthreads_ab2`).

**What the knob costs.** The serialised ORDER of events within a timestep
becomes thread-schedule-dependent: the two knob-on twins differ byte-wise in
`output_events.xml.gz` while agreeing on the sorted stream. Every consumer
in this repository aggregates events (summariser, metrics, telemetry), so
nothing reads order — but byte-identical reproducibility of the events
artefact is LOST, and this entry is where that trade is recorded. A
consumer that ever comes to depend on within-timestep event order must
revisit this decision.

**What the knob buys, measured at scale.** `evthreads_timing` (25% × 5, same
demand, same seed, same 10 qsim threads): iterations 2–4 ran 191/181/201 s
against the single-thread baseline's 233/243/243 s on `phys50_25pct` —
**~21% off the wall**. The heaviest single handler still bounds one thread
(242 s CPU on the event-writing final iteration), which is why
`RUN.controler.write_events_interval` and `write_plans_interval` are set to
**100** (from 10) in the converged arm's overlay: both are declared
wall-time-only fields (§15), the final iteration is always written
regardless (the #54 events-based accounting gate needs it), and ten
intermediate dumps of a 1000-iteration arm are checkpoints enough.

**What was NOT done.** `oneThreadPerHandler` (experimental in the shipped
MATSim), more qsim threads (run identity, §9.5), and any change to the
model to buy speed. At 1% the knob is SLOWER (27.6–29.4 vs 19.9
s/iteration — sync overhead with no saturation to relieve), so 1% probes
remain comparable only to 1% probes, as §9.12 already requires.

## 9.57 The first all-physical arm: decided at 1000, launched, measured to iteration 136, stopped (21 August 2026, issues #30, #48, #60)

**The horizon decision — full 1000; ~500 considered and REJECTED.** Decided
before launch on `bind1000_25pct`'s own trajectory and re-affirmed after the
attempt on the new arm's: in the reference arm, car still moved **+2.14 pp**
and ride **−1.28 pp** between iterations 500 and 790 — pre-cutoff SEARCH,
which a 500-iteration horizon (cutoff 400) would truncate mid-slope — while
the post-cutoff window was genuinely flat (car +0.09 pp over 190
iterations). The attempted arm agreed: at iteration 133 car was still
climbing ~+3.3 pp per 25 iterations. §9.43's declared 1000 stands.

**The attempt.** `phys1000_25pct` (S2 × WEEKDAY, 25% × 1000, the §9.56
events threads, write intervals 100) launched 21 Aug 00:40 with stated-cost
approval (~48–58 h). Healthy through 135 complete iterations at median
**~234 s/iteration**: car 19.53 → 46.32%, walk 52.37 → 32.77, bike 11.71 →
9.92, pt (aggregate) 11.97 → 6.62, ride 0.31 → 0.26 (the §9.55 emergent
floor), truck 3.89 and motorbike 0.22 constant by construction; per-iteration
stuck falling 41.8k → ~21k. **Stopped by instruction ~11:52 during
iteration 136** and quarantined to `results/_aborted_20260821/phys1000_25pct`
— no `_run.json`, NOT a result; the 135 iterations of trajectory diagnostics
are preserved. Relaunch requires fresh stated-cost approval.

**Two measurements the attempt produced, both diagnostics of an aborted run:**

- **The iteration-110 outlier**: 7,867 s against the ~234 s median — a
  mid-day walk gridlock knot (13,006 walk stuck that iteration vs ~2,600
  typical) that cleared itself through stuck timeouts and did not recur in
  the remaining 25 iterations. Same unattributed family as §9.36's 2,415 s
  event on `conv1000_10pct`; still unattributed, now twice-seen.
- **The walk-leg decomposition** (iteration-100 events, 25%): 242,073
  completed walk legs = **160,812 whole-trip network walks (66%, mean 8,800
  s ≈ 11 km at the capped 1.25 m/s)** + **81,261 teleported PT access/egress
  stubs (34%, mean 1,159 s)**; car access/egress contributes ZERO
  (`accessEgressType = none`). The 11 km mean is #30's generation defect
  surfacing physically — mid-search, the model carries walks no person would
  make, and they are most of the event volume §9.56 paid for. The §9.55
  re-mode contributes 5,533–5,792 unpaired ride legs per iteration to the
  whole-trip class (engine counts, logged each iteration).

**A defect found and not fixed, filed as #60**: 424,056 `Cannot move vehicle
<person>_walk` refusals from `DefaultTurnAcceptanceLogic` over ~110
iterations (~3.8k/iteration) — walk vehicles arriving at a junction whose
next route link the qsim refuses. SUSPICION, not verified: the walk router
ignores `disallowedNextLinks` (turn restrictions harvested for motor
vehicles) while the qsim enforces them, wedging pedestrians until the stuck
timeout; plausibly the mechanism inside the iteration-110 knot. Numbers
measured; mechanism unproven; nothing here changes a declared value.

**What this deliberately does not do**: no finding about the light rail, no
comparison against any other run (aborted, and its own family), no change to
any target; the 67/143 split untouched.

---

## 9.58 The walk wedge: #60 verified to be a different defect, and the four repairs (21 August 2026, issues #60, #48, #30)

**The verification came first, and the filed suspicion is dead.** #60 suspected
the walk router ignores `disallowedNextLinks` while the qsim enforces them.
Bytecode of the pinned engine says the OPPOSITE division of labour:
`DefaultTurnAcceptanceLogic` never reads `disallowedNextLinks` at all — its
only refusal conditions are a null next link, a next link absent from the
network, and a next link that does not start at the current link's end node —
while `SpeedyGraphBuilder` applies turn restrictions PER MODE in the router
(`TurnRestrictionsContext.build(network, mode)`). Car and bus routes comply
with the observed restrictions because their routes are built under them; walk
never had a restriction to violate. The filed fix (exempt walk from
motor-vehicle turn restrictions) would have changed nothing.

**What the 491,349 refusals actually are: a first-hop topology break.** All of
them — 478,360 walk, 12,989 bike, classified against the run's own network —
are the third refusal condition, and the broken pair is the leg's ACTIVITY
link against the route's FIRST link. With `routing.accessEgressType = none`
there is no access leg, and when an activity sits on a link outside the leg
mode's subnetwork, MATSim's `decideOnLink` silently starts the route at the
NEAREST in-network link while the qsim inserts the vehicle at the activity's
link. The vehicle reaches the junction, the next route link does not connect,
and the agent wedges there until the stuck timeout ABORTS it mid-day. Measured
at iteration 100 of the aborted arm (25%): **11,402 walk and 218 bike legs per
iteration** carry the break (the egress side mirrors it: 11,497), from
**50,240 activities (6.81%) sitting on walk-less links** — 30,330 in pockets
the per-mode SCC strip had severed, 19,910 on walk-excluded road classes
(trunk 10,288, motorway 9,040 — the motorway ones almost all external cordon
gates). The recurring hotspot pattern (many activity links funnelling into one
nearest walk link) is also a congestion knot generator — plausibly the
mechanism inside §9.57's 7,867 s iteration, though that remains unattributed.

**Repair 1 — the pedestrian exclusion was wrong about the law, and it severed
the walkable city.** §9.54 excluded walk from `motorway, motorway_link, trunk,
trunk_link` claiming road rules; NSW Road Rules prohibit pedestrians on
motorways (r. 288, signposted) and nowhere else — an urban trunk road
(Stewart Avenue, Maitland Road) is a legal pedestrian route with footpaths.
The over-broad list disconnected every neighbourhood whose only walk connector
is a trunk segment, which is what the SCC strip was then reporting (16,726
links stripped). `A.network.pedestrian_excluded_classes` is corrected to
`[motorway, motorway_link]` — the same list bike already had, and a correction
of a mis-stated legal fact, not a tuning.

**Repair 2 — one-way streets walk both ways.** MATSim's network is directed; a
one-way carriageway was walkable in one direction only, which is false for
pedestrians and for a dismounted cyclist. `add_nonmotor_reverse_links`
(assembly, before the SCC strip) adds ONE reverse link per one-way node pair
carrying exactly the missing walk/bike modes: length, capacity and lanes
inherited from the forward link (nothing new is decided), free speed = the
declared `A.transit.walk_speed_ms` — a dismounted cyclist is a pedestrian —
and no osm attributes, so an E1 patch can never touch a complement and the
motor network is unchanged. S2 gained 16,603 complements.

**Repair 3 — an activity is pinned to a link its person can actually use.**
`ActivityLinkAssigner` (new, runs once on the loaded scenario before the
Controler exists, so PrepareForSim's XY2Links finds nothing left to assign):
each activity must sit on a link carrying every network mode its person can
put on an adjacent leg — the person's own leg modes, plus, for a
subpopulation that carries SubtourModeChoice, everything mode innovation
could choose (`subtourModeChoice.modes ∩ routing.networkModes`). The needed
set is DERIVED from the run's own config; nothing city-specific is declared.
Nearest-link semantics are MATSim's own, on a subnetwork of qualifying links.
A boundary agent's needed set is exactly the mode it arrived with, so cordon
gate activities stay on their motorway gate links.

**Repair 4 — a boundary agent's mode is data, not a choice.** The through tier
is seeded from classified cordon vehicle counts (§9.41, §9.49), yet the
emitter gave every subpopulation the same strategy set, so external agents
carried SubtourModeChoice over `car,ride,pt,bike,walk`. MEASURED at iteration
100: **405 external agents had abandoned car** — 451 walk legs, 164 bike, 62
pt, 256 ride — i.e. 40 km boundary crossings on foot, each also wedging at a
walk-less gate link. `RUN.replanning.strategy_subpopulations` (new,
`{"SubtourModeChoice": ["person"]}`) withholds a strategy from named
subpopulations through a declared `restrict` clause on the schema's
`repeat_over`; freight was already structurally safe (truck is not in the
choice set — its strategy block was inert) but is withheld too, as the same
statement of the same principle.

**Comparability: a new family boundary.** Repairs 1–3 change the network and
the model; nothing after this compares to `phys50_25pct`, the aborted
`phys1000_25pct` diagnostics, or anything older. The boundary is free
precisely because the all-physical family has no completed run (§9.57) — this
is the "fixing before the relaunch is free family-wise" case the handover
named.

**What this deliberately does not do.** It does not re-add access/egress
stubs (`accessEgressType = none` stands — the repair makes the activity link
itself usable rather than teleporting to a usable one); it does not touch the
walk speed, the PCEs, any scoring value, any target, or the 67/143 split; and
it does not claim the it-110 knot is explained — fewer wedged agents is a
prediction the next run must test, not a result.

---

## 9.59 Iteration wall time: every knob declared, probed at 25%, and the honest answer to the 10x ask (21 August 2026)

**The forensics first** (the §9.57 arm's own `stopwatch.csv` and 113 MB log):
median 226 s = mobsim 145 (64%) + replanning 59 (26%) + PersonPrepareForSim
19 (8%). The mobsim generates ~134.5M events/iteration, 96.4% of them
link enter/leave (car 53.5%, walk 30.2%, bike 9.7%, truck 5.5%); after the
§9.56 knob the busiest events runnable still burned ~119 s CPU against the
145 s wall. **The it-110 outlier is explained**: all strategies finished
normally except one `PlanRouter` pass over 2,245 mode-changed plans that
ran 7,594 s — ReRoute against a travel-time field poisoned by the
walk-gridlock knot (SpeedyALT's landmarks are built once at startup, so
extreme congestion degenerates the A* heuristic), with heap pressure on
top. The §9.58 repairs attack the knot's cause; `-Xms` now pre-sizes the
heap (it grew 7 → 27 GB across the arm with full-GC stalls in that pass).

**One correctness finding doubled as a lever.** The emitted config carried
no `qsim.linkDynamics`, so the all-physical model ran MATSim's FIFO
default — under which vehicles EXIT A LINK IN ENTRY ORDER, and a 1.25 m/s
pedestrian at the head of a shared link's queue holds every car behind it
regardless of its PCE 0.0. That directly contradicts §9.54's declared
semantics ("neither impeding nor impeded by motor traffic": PCE governs
capacity arithmetic, not exit order). `RUN.qsim.link_dynamics = PassingQ`
is declared — a car overtakes a walker on the carriageway, which is what
a street does.

**The probes** (`phys_timing2_*`, 25% × 5 on the §9.58 network, one at a
time, it2–4 medians):

| probe | knobs | total | mobsim | replanning |
|---|---|---:|---:|---:|
| base | PassingQ · events 4 · replanning 10 | 279 s | 185 s | 76 s |
| evt | + events 12 · replanning 20 | **233 s** | 190 s | **33 s** |
| async | + synchronizeOnSimSteps=false | 295 s | 255 s | 32 s |
| fifo | FIFO control of base | 222 s | 143 s | 64 s |

**Decisions, each carried on its own field**: `replanning_threads` = 20
(replanning 76 → 33 s, prepare ~15 → ~6 s — the one clean win; RUN
IDENTITY, free at the §9.58 boundary); `event_handler_threads` stays 4
(12 bought nothing on this network); `synchronizeOnSimSteps` stays true
(false is a measured 65 s/iteration regression);
`oneThreadPerHandler` stays false (MEASURED FATAL — the probe crashed
with `.initProcessing() has to be called before processing events!`, the
experimental path §9.56 declined now known broken); PassingQ stays ON
ITS CORRECTNESS CASE and its measured price is stated: ~42 s/iteration
over FIFO at this event volume. `RUN.controler.create_graphs` is
declared so a long arm's overlay can stop paying eight PNGs per
iteration.

**The honest statement against the 10x ask.** The repaired model is
SLOWER per iteration than the wedged one (~233 s vs ~234 s median, on a
network where 11.6k walk/bike legs per iteration used to die at the first
junction instead of being simulated to the end of their day, walk covers
16.6k more directed links, and every activity is reachable) — the wedge
fix bought back work the broken model was silently skipping. The measured
CPU floor (events handlers ~400 CPU-s + replanning + qsim) over 24 cores
puts ~10x per-iteration out of reach WITHOUT shrinking the physical work,
and every shrink path is either banned (teleportation), abandons physical
boarding (the Hermes mobsim), or trades precision (the sample fraction).
What IS available: the ~233 s stack now, and FAMILY THROUGHPUT — two
concurrent arms at qsim 8 + events 4 fit this machine's 24 CPUs and
63.5 GiB (each run peaks ~27 GB) and double arms-per-week; iteration
COUNT survives contention even though iteration duration does not (§9.5's
measured rule). The 10x directive is answered by measurement, not by a
claim.

---

## 9.60 Non-household lifts: the reported gap gets a physical mechanism (21 August 2026, issues #48, #31, #28)

**The project's new instruction supersedes §9.55's report-only stance**: fix
the non-household-lift gap. The option analysis is the dossier
[`design/non-household-lifts.md`](design/non-household-lifts.md); the
decisive fact is that the two halves of the gap are the same phenomenon
seen from two sides — B2 generates serve-passenger (HX) driver tours at the
OBSERVED 10–19.5% rate, §9.46 binds 68.6% of them to household member
trips, and the unbound remainder drive to a drawn attractor serving
nobody, while the driverless-household class generates ride demand that
household pairing structurally cannot serve.

**M0 — a booked passenger physically waits for the car**
(`B.ride.wait_for_driver`, enacted in `JointRideEngine`). The §9.53 engine
could board only a car ALREADY parked at the link; a passenger who
departed first was a counted miss falling back to teleport — the measured
×6.91 window layer wearing its physical face. Now the passenger stands at
the meeting point, boards when the booked car is parked there, and gives
up after the declared pairing window — the same tolerance the booking was
made under, so NO NEW NUMBER. A timeout completes the leg on the Tier-1
clock counted FROM the timeout: waiting costs what waiting costs, and
scores accordingly. Counted per iteration: `waited(boarded, timedOut)`.

**M1 — unbound escort tours are re-targeted to the passengers they exist
to carry** (`bind_nonhousehold_lifts`, a second deterministic pass after
each B2 day file closes; scope declared and swept as
`B.activity.escort_binding_nonhh_scope` — `household_only` restores §9.46
exactly, `same_zone` matches within the shared home SA1). An unbound HX
tour becomes home_d → passenger origin (pickup) → passenger destination
(drop) → home_d, with the serving leg's departure taken from the
passenger's own EXACTLY, so the runtime pairing matches it under the
UNCHANGED declared rule and window. Passengers rank as the §9.46 binder
ranks (unlicensed education first); the pool is the driverless-household
class only; the re-timed tour goes through `time_tour` twice (offset
probe, then pinned) so no speed or overhead constant is restated; an
infeasible re-timing is SKIPPED and the original tour kept. ADDS NO TOUR
AND NO TRIP — the observed driver supply is re-aimed, exactly the §9.46
argument one household boundary out.

**The coupling, and its integrity rules.** `build_matsim_plans` grants a
bound passenger `rideAvail` (the availability identity — a household
vehicle and someone to drive you — is satisfied by construction across
the household boundary) and stamps `liftHousehold`;
`RidePairingEngine` widens that passenger's candidate search to the
driver's household, own household first, so a binding can never displace
an intra-household pairing at equal gap. The binding is an ELIGIBILITY,
never a guarantee: the driver's leg must still match under the declared
rule, the boarding is still physical, and an unserved leg still re-modes
to walk (§9.55) — the emergent-share discipline is unchanged, with a
larger physically-realisable supply. `sample_population` unions
households joined by a binding into ONE sampling cluster hashed on a
canonical representative: sampled independently the pair would survive
intact with probability fraction² — the §9.45 defect class one level up —
and co-sampling keeps every household's inclusion probability exactly the
fraction at the stated §9.45 price (more variance at fixed size).

**Measured on the regenerated demand (full population, seed 20260810):**
WEEKDAY binds **55,280 of 55,614 unbound HX tours (99.4%)** to a
driverless-household passenger in the same SA1 (SAT 30,443/30,490, SUN
21,804/21,833) — the driver supply and the unservable demand really were
the same phenomenon. The 1% × 2 verification probe ran rc=0 with
**zero turn refusals** (the §9.58 repairs hold on the new demand),
accounting closed, and the M0 counters live: the old
`missed(gone/absent)` classes are **0** — every such case now goes
through the waiting path (`waited(boarded, timedOut)` per iteration).
What the mechanism is WORTH — where emergent ride settles against the
observed 20.60% — is the converged arm's measurement, not this entry's.

**M2 (driver-detour lifts) is designed and DEFERRED** until a converged
arm measures what M0+M1 leave unserved; M3 (a declared allowance, teleport
or phantom driver) is REJECTED — it violates no-teleportation and
no-invented-data directly. The household/non-household split of boarded
lifts is REPORTED (ride_pairing.csv), never fitted — no observation of
who-drives-whom exists to fit it to; commute carpooling stays checked
against G62 (car-as-passenger 3.35% of JTW), and occupancy is reported
against its declared range [0.2493, 0.394]. No target moves; the 67/143
split is untouched.

---

## 9.61 Deliverable 0b: three assumptions became measurements, and the scaffold constants surfaced (21 August 2026)

The 0b sweep enumerated all 136 `assumed` fields (the board's "78" was
stale) and classified every one; the backlog is issue #63. Landed now,
each from data ALREADY IN THE PACKAGE:

- **G15 was in the package all along.** `build_population.py` and the
  age-structure dossier claimed the census table that would measure the
  tertiary full-time/part-time split "is not in the package"; it is —
  `2021Census_G15_NSW_SA1.csv` inside the GCP zip, harvested by the same
  extract as every other table. The 18+ education split is now OBSERVED
  per SA1 (full-time / (full-time + part-time), Voc + Uni combined, G15's
  15_24/25_ov bands standing for 18_24/25_ov, `F_Pt_ns` excluded from both
  sides, core-aggregate fallback for empty cells), and
  `B.population.tertiary_ft_share` (assumed 0.70/0.35, ±30%) is RETIRED.
- **The weekend's inside split is measurable after all.** §9.2 rightly
  said the AADT station-year aggregates report one WEEKENDS figure; the
  HOURLY permanent-station file carries day-of-week per dated row, and
  `extract_daytype_factors.py` (the §9.49 freight-profile method verbatim,
  LIGHT VEHICLES classification) measures the SAT:SUN split, the light
  day-type factors the external tier scales by, and the weekend
  departure-time shift (argmax circular correlation of the weekend hourly
  profile against the weekday's). MEASURED over 12 stations and 33,753
  clean station-days: **SAT:SUN = 1.1473** (the assumption said 1.1875 —
  close), **SAT 0.8429 / SUN 0.7347 of the weekday level** (the external
  tier had been scaled at an assumed 0.4/0.3 — weekend boundary demand
  roughly DOUBLES), and the **departure shift is 1 h on both weekend
  days — exactly what was assumed**, which is the pleasant case of an
  assumption surviving its own measurement. Three assumed fields RETIRED
  (`B.activity.sat_to_sun_rate`, `B.activity.weekend_departure_shift_h`,
  `B.external.day_factor`); the build now refuses to run without the
  measured artefact rather than falling back to an assumption.
- **The chain-timing scaffold constants are declared.** `time_tour` timed
  every B2 leg at `26.0` km/h (car-available) / `16.0` km/h (not) plus a
  bare `+ 240` s — inside expressions, where the ledger's scanner
  structurally cannot see a value. They decide only the planning scaffold
  (whether tours fit a day and how departures space) — the mobsim re-times
  every leg physically — but a value that decides anything is declared:
  `B.activity.plan_speed_car_kmh` / `plan_speed_nocar_kmh` /
  `plan_access_s`, assumed and swept.

Every change regenerates B1/B2/plans and lands inside the §9.58/§9.59
family boundary — nothing after it compares to anything before it.

---

## 9.62 The two-arm relaunch: arm A is the base arm, arm B is the seed replication (21 August 2026)

**Approval, 21 August 2026 (the day's third directive): run two
concurrent arms with a tight watch — measured every 50 iterations, every
ridership figure evaluated against the observed references, next actions
derived when the runs finish.** This consumes the approval; none is
standing after these two arms.

**The launch enacts §9.59's two-arm pattern**, with the arms declared as
committed overlays (`phys1000_arm_a_25pct`, `phys1000_arm_b_25pct`):
qsim 8 + events 4 per arm, replanning at the declared 20, and
**`RUN.machine.xmx` 30g per arm, not 40g** — the driver pins `-Xms` to
`-Xmx` (§9.59's heap pre-sizing), so two 40g arms would commit 80 GiB on
a 63.5 GiB machine, which is the measured §9.5 three-arm pagefile
failure; the record's own sizing (a 25% run peaks ~27 GiB under this
pattern) says two fit. `create_graphs` is off — the §9.59 field exercised
for the first time. **Run identity note:** qsim threads 8 differs from
the timing probes' 10; free at this boundary because no completed run
exists in the §9.58–§9.61 family, and both arms carry one identity, so
they compare to each other.

**Arm A** (S2 × WEEKDAY, 25% × 1000, master seed 20260810) **is the base
arm** — the active lane's relaunch. C5, the §9.50 report, the #30 walk
re-baseline, the emergent ride share vs 20.60 and the #48/#31 ledgers all
read this arm and only this arm.

**Arm B is arm A with one change: `RUN.machine.seed` 20260811** — the
field's own declaration ("held at the master seed unless replications are
being drawn") exercised for the first time. It is the **seed-variance
measurement this log has demanded twice and never had**:
`E.replication.n_replications` is 30 with a provisional planning figure
of 5 "until measured seed variance exists", and §9.45's cluster-sampling
note records that no such measurement exists to separate cluster variance
from mechanism. The seed moves both the 25% household draw and MATSim's
`global.randomSeed`, which is what a replication is. Against arm A it
yields the first per-mode error bar — the noise floor under every
modelled-vs-observed delta, which any later calibration claim needs
before a fit difference can be called signal. **Arm B is not a second
base arm and nothing in the close-out reads it alone**; its product is
the A-vs-B spread.

**The watch** samples both runs' own telemetry (`telemetry.jsonl`,
`modestats.csv`, `ride_pairing.csv`, `stopwatch.csv`) every ~50
iterations against the 67-row calibration split only — the holdout stays
closed. Everything it prints is **diagnostics until `_run.json` exists**
(§9.12 rule, unchanged). Tripwires that stop an arm early are the
measured failure classes: a dead JVM, iteration wall time beyond 3× the
rolling median (the it-110 class), stuck counts rising after the early
iterations, capacity refusals, or working sets approaching the machine's
memory.

---

## 9.63 Both relaunch arms crashed at replanning: overlapping lift re-targets interleaved a driver's tours (21 August 2026, issue #65)

**The event.** Both §9.62 arms died within 440 s at their first
replanning — MATSim's `ChooseRandomLegModeForSubtour` threw `Subtour
contains a mix of chain- and non-chainbased modes` on both seeds
(20260810 and 20260811). Systematic, not stochastic.

**The measurement.** 152 of 155,623 persons in arm A's input plans carry
a closed subtour mixing chain-based (`car`, `bike`) with non-chain modes
(car+pt 68, car+walk 38, bike+walk 24, bike+pt 20, two triples — no
`ride` in any, exonerating the M0 waiting path). The pre-§9.60 demand
has ZERO such persons in 155,349, so the §9.60/§9.61 regeneration
introduced the class. The B2 tables show the mechanism: **1,191 WEEKDAY
persons (305 SAT, 137 SUN) held INTERLEAVED tours** — e.g. person 62708,
tours 2 and 5 both 3-leg lift tours at `trip_seq` 8,9,12 and 10,11,13.
Mode is drawn per tour, so interleaved tours emit alternating modes, and
coincident escort stops (within SubtourModeChoice's 100 m coordDistance)
close a mixed subtour.

**The cause** (`bind_nonhousehold_lifts`, the §9.60 M1 pass): when one
driver's day held two unbound HX tours and both were re-targeted, the
second binding's busy-interval check read the first tour's ORIGINAL rows
— its re-targeted times lived only in `replaced` and were never
consulted — so two lifts could overlap, and the chronological
re-sequencing splice then interleaved their legs. The 1% probes passed
because ~6 affected persons at that fraction × SubtourModeChoice's ~10%
per-iteration touch gave the crash no reliable chance to fire —
**verified-at-1% is not verified**, which the §9.10 rule already said.

**The repair** (in the same pass): the busy check consults the
re-targeted times of already-replaced sibling tours; and a post-splice
assertion refuses to write any demand in which a person's tours are
non-contiguous in `trip_seq` — with one mode per tour and every tour
anchored at home, contiguity structurally excludes the mixed-subtour
class. B2/plans regenerated: **0 interleaved persons on all three day
types**; weekday lift bindings 55,280 → **55,249** of 55,614 (31
formerly-overlapping bindings now correctly skipped as infeasible), SAT
30,442, SUN 21,803. Free at the family boundary — no completed run
exists in the §9.58–§9.61 family; §9.62's identity is otherwise
unchanged and both arms relaunch on the repaired demand.

**Recorded softness, not chased here:** a re-targeted lift tour's mode
is still drawn from the seed split, so a bound driver can hold a
walk-mode lift tour the pairing engine can never realise as a ride. The
realised pairing rate is measured and reported at the arm (§9.48
pattern), so this dilutes binding efficacy visibly rather than silently;
it belongs with the #48 measurement lane, not this repair.

---

## 9.64 The first converged all-physical arms: C5 exists, ride collapses under scoring, and the seed noise floor is measured (24 August 2026, issues #48, #31, #30, #28, #14, #9)

**Both §9.62 arms completed** — 1000 iterations each, rc=0, ~67.4 h wall
apiece (the §9.59 estimate was ~65 h; the #66 stall and two-arm
contention account for the rest). Arm A: `relaxed: true` at max drift
**0.031 pp** (tolerance 0.5; the cutoff snap 4.23 pp reported
separately), events-based conservation closes on every mode. These are
the FIRST valid runs of the §9.58–§9.63 family.

**The fit (arm A, 35 of 67 calibration targets scorable, MAE 10.65 pp):**
driver **73.19 / 59.0 (+14.19)** · passenger **0.09 / 20.6 (−20.51)** ·
walk-only **7.28 / 13.4 (−6.12)** · bike **11.21 / 3.2 (+8.01)** · pt
**8.22 / 3.8 (+4.42)**. Submodes (Tier R): bus 6.13, rail 0.77 + combos,
tram 0.02, ferry 0.02. **Light rail: modelled 1,260 weekday boardings
(B: 1,212) against the observed 3,417/day — the intervention under study
realises ~37% of its patronage in the uncalibrated base.** Counts:
mean −91.8% with 6 modelled-zero stations — statistically unchanged from
`bind1000_25pct`'s −91.05%, the recorded no-through-demand structure,
not a new defect. Trip-length constraints: walk mean **5.56 km vs 0.70
observed (7.9×)** — #30's generation diagnosis reproduces on the
physical family; bike 1.66×, car 1.07×, pt 0.44×.

**The central finding — ride collapses under scoring, not under
physics.** Through iteration ~799 the arms carried ~6,800 ride legs at
pairing rates 0.08–0.20; at the innovation cutoff selection kept ~540,
of which **100% pair and board**. The §9.53/§9.60 machinery works —
what died is the CHOICE: with waiting priced at the declared 0 utils/h,
a paired ride still loses to self-driving for the licensed and to
bike/pt/walk for the carless. The observed 20.6 passenger share sits
recognisably in the overshoots (+14 driver, +8 bike, +4.4 pt).
Occupancy 0.0013 vs 0.3503. **M2 (driver detours) is a NO-GO on this
evidence** — supply is not the binding constraint when 100% of surviving
requests are served; the binding constraint is demand-side scoring, and
which lever to pull (the §8.5-held constants stay held) is the project's
next decision. The next diagnostic is a decomposition of where ride
plans die: never-proposed vs proposed-and-scored-out vs
unpairable-re-moded.

**C5 EXISTS (deliverable 5, closing #14 and #9).**
`params/C5_calibration.json` written by `--constrained-base` from arm A
under the §9.50 branch: every parameter at its declared value, objective
10.65, **feasible=False with five stated violations** (occupancy + four
trip-length ranges) — reported, never absorbed. #9 closes as decided by
§9.50: ASCs stay priors. `docs/audit/CALIBRATION_REPORT.md` regenerated.

**The seed noise floor is measured (arm B's product, n=2):** per-mode
|A−B| at fit level 0.00–0.11 pp (MAE 10.65 vs 10.66), LR boardings
1,260 vs 1,212 (±3.9%). Every gap in the table above is signal.
`E.replication.n_replications` (30, provisional planning figure 5) can
now be set from data — at this variance even 3 replications resolve
sub-pp mode-share effects; the value choice awaits a decision with the
measurement recorded here.

## 9.65 Run directories are named by the runner, never by hand (24 August 2026, standing directive)

**The decision.** A run directory is named by `run_matsim.py` at launch as
`<launch yyyymmddThhmmss>_<iterations>it_<sample pct>pct` — dated, sortable
and self-describing. The `--tag` flag is removed from `run.py`,
`run_matsim.py`, `calibrate.py` and `solve_asc_ride.py`: nobody, agent
included, hand-names a run any more. The directive asked for exactly this
(24 Aug): human-readable names, chosen by the runner and not by the agent —
the old codenames (`phys1000a_25pct`, `bind1000_25pct`, …) required session
context to decode and encoded neither the date nor the true parameters
(`rp50_declared` was 50 *iterations* at a 1% sample, not a 50% sample).

**What identity means now.** The launch stamp is a **label**, not identity.
A run's identity stays the parameter set in `_run.json` (scenario, day,
fraction, iterations, seed, `--set` overrides, controler source hash), and
resume detection now scans the records and matches on it — re-invoking with
the same parameters is still a no-op, `--force` still forces, and a
parameter match with a **changed controler** now starts a fresh directory
and leaves the stale one in place rather than deleting it (deleting a
result is never the harness's call; the old behaviour overwrote in place).
The calibration loop locates a candidate by the overrides recorded in
`_run.json` rather than by a tag it invented, and writes the runner's
directory name into its history and `best_tag`. The wall clock enters the
directory NAME only; no model input or output depends on it, so the
determinism constraint is untouched.

**The renames (applied 24 Aug to everything on disk; quarantined runs
renamed in place inside their `_aborted_*` parents).** Documents dated
before this entry — §9.44–§9.64, the audit evaluations, `C5_calibration.json`'s
`best_tag`, the calibration report — keep the old names as historical
references; this table is the bridge. Run-internal records (`_run.json`
`name`, `SUMMARY.md`) also keep the name they were written under.

| old | new |
|---|---|
| `phys1000a_25pct` (arm A, **the C5 base run**) | `20260821T175907_1000it_25pct` |
| `phys1000b_25pct` (arm B, the seed replication) | `20260821T180310_1000it_25pct` |
| `bind1000_25pct` | `20260818T235351_1000it_25pct` |
| `conv1000_10pct` | `20260816T022250_1000it_10pct` |
| `conv1000_25pct` | `20260817T011703_1000it_25pct` |
| `phys50_25pct` | `20260820T202754_50it_25pct` |
| `evthreads_timing` | `20260821T003843_5it_25pct` |
| `phys_timing2_base` / `_evt` / `_async` / `_fifo` | `20260821T131322` / `T141252` / `T144513` / `T152035` `_5it_25pct` |
| `wedge_probe` / `wedge_probe2` | `20260821T130340_2it_1pct` / `20260821T130835_2it_1pct` |
| `lift_probe` | `20260821T155944_2it_1pct` |
| `allmodes_probe` | `20260820T175133_2it_1pct` |
| `jointride_probe` | `20260820T165314_2it_1pct` |
| `motorbike_smoke` | `20260820T162958_2it_1pct` |
| `freight_smoke` | `20260820T150002_2it_1pct` |
| `evthreads_ab` / `evthreads_ab2` | `20260820T230351_2it_1pct` / `20260820T230710_2it_1pct` |
| `ride_pairing_probe` | `20260818T194826_3it_1pct` |
| `rp25_declared` / `rp25_control` / `rp25_stress` | `20260818T211301` / `T212802` / `T214527` `_10it_25pct` |
| `rp50_declared` | `20260818T205739_50it_1pct` |
| `smoke_postrebuild` | `20260816T015048_2it_1pct` |
| `_aborted_20260816/conv1000_10pct_postbatch` | `_aborted_20260816/20260816T020351_1000it_10pct` |
| `_aborted_20260816/S2_WEEKDAY_f025_i1000_s20260810` | `_aborted_20260816/20260816T020436_1000it_25pct` |
| `_aborted_20260816/conv1500_10pct_stopped` | `_aborted_20260816/20260818T080732_1500it_10pct` |
| `_aborted_20260818/bind1000_25pct` | `_aborted_20260818/20260818T233911_1000it_25pct` |
| `_aborted_20260820/S2_WEEKDAY_f025_i1000_s20260810` | `_aborted_20260820/20260818T162538_1000it_25pct` |
| `_aborted_20260820/base1000_25pct` | `_aborted_20260820/20260820T151516_1000it_25pct` |
| `_aborted_20260821/phys1000_25pct` (§9.57 stop) | `_aborted_20260821/20260821T010821_1000it_25pct` |
| `_aborted_20260821/phys1000a_25pct_smc_crash` | `_aborted_20260821/20260821T172050_1000it_25pct` |
| `_aborted_20260821/phys1000b_25pct_smc_crash` | `_aborted_20260821/20260821T172453_1000it_25pct` |

*(Superseded the same day for the dead runs: §9.66 dissolved the
`_aborted_<date>` parents, so each quarantined path above now lives at
`results/aborted_<new name>`.)*

## 9.66 Every run carries an auto-updated status card, and a dead run's name says so (24 August 2026, standing directive)

**The decision.** Every run directory carries **`_meta.json`** — a small
status card written by `run_matsim.py` at LAUNCH and updated automatically
at every transition, so runs can be observed, and considered or
disregarded, without opening a log. Contents (schema-checked against
`config/schema/outputs/meta.schema.json` through the same
`outputs.write_checked` contract as every other output): `status`
(`running` / `completed` / `failed` / `aborted`), the identifying
parameters (scenario, day, fraction **and `sample_pct`**, iterations, seed,
threads, xmx, overrides, controler hash), `started`, `ended`, `wall_s`,
`rc`, and the harness `pid`.

**Transitions.** rc=0 → `completed`. rc≠0 → `failed`. An interrupt the
harness can still catch (Ctrl+C, a terminating exception) → `aborted`,
written in a `finally`-style handler before the signal propagates. A hard
kill the harness cannot see is settled by **reconciliation**: at every
harness start, any run whose meta says `running` under a pid that no longer
exists is marked `aborted` (pid liveness via `OpenProcess`/`WaitForSingleObject`
on Windows — `os.kill(pid, 0)` there TERMINATES the target and must never
be used). A live concurrent arm has a live pid and is untouched.

**Dead runs are named so a directory listing says what happened**: the
harness renames a failed or aborted run to
**`aborted_<launch>_<iterations>it_<pct>pct`** in place, at the top level
of `results/` — the old `results/_aborted_<date>/` quarantine parents hid
exactly the data the name now shows and are **dissolved** (directive: *"not
aborted_number, that hides the other data"*). The prefix is the disregard
label; the precise cause (`failed` vs `aborted`) lives in the metadata. If
the rename loses to a Windows directory lock (a `tail -f` monitor holds
one — trap ledger), the metadata still carries the truth and the rename is
reported, not raised.

**What this does not change.** `_run.json`, written only on success,
**remains the result gate** — "a run without `_run.json` is not a result"
stands; `_meta.json` is observational and is never read by resume
detection, the fit, or the calibration loop. Backfill: all 35 existing runs
received a meta card derived from their own records (`_run.json`,
`_config.json`, log first/last timestamps — nothing invented; backfilled
cards carry a `note` saying so), the nine dead runs moved to
`results/aborted_<name>`, and the two §9.63 SMC crashes are `failed`
(the JVM exited non-zero) while the instruction-stopped and found-dead runs are
`aborted`.

## 9.67 The project is city-digital-twin (24 August 2026, standing directive)

**Renamed to `city-digital-twin`** from the earlier Newcastle-specific repository name. The project's goal
(§9.51, the brief §1) has been a digital twin of ANY city; the framework
half of the repository is city-agnostic by hard constraint, and its own
naming rule — no place name in the framework — was violated by the
repository's own name, as it had been once before ("Project Wickham",
§14 2026-08-13, renamed then only as far as the next place name up).

**What changed.** The GitHub repository is renamed (GitHub redirects the
old URL; PR #67, the issues and the stars survive); the local remote now
points at `city-digital-twin`. In-tree, the identity-bearing statements
changed: `README.md`, `.claude/CLAUDE.md` (title and the Naming rule),
`STATUS.md`, this file's header, the registry module docstring, and the
nine `config/schema/` `$id` URLs and titles. **What did not change:**
historical narrative (this log, session records, audit evaluations, the
proposal's working title — history is not rewritten); generated data
reports carrying the machine's absolute path (regenerable, manifest-hashed,
and true until the local folder is renamed); and the two tracked codename
identifiers — the `CITYSIM_*` env prefix and the `src/java/citysim/`
package — which stay with the open naming issue (renaming a compiled entry
point invalidates run records and is not done as a side effect). The local
working-copy folder was renamed to `work/city-digital-twin` on 25 Aug 2026;
nothing in the repository depends on its name.

## 9.68 The ride collapse decomposed: one-directional supply and seed decoherence, not preference — and the repair (24 August 2026, issues #48, #31, #28)

**The project's goal (24 Aug): every mode's ridership as close to real life
as possible; begin with ride; fix everything fixable before the next run.**

**The decomposition (arm A, `src/analyse/decompose_ride_choice.py`, reads
the completed run - no new run).** Of 77,626 ride-available choice persons,
**531 selected ride, 109 held a scored-out ride plan in final memory, and
76,986 (99.2%) held NO ride plan at all** - proposed during search,
re-moded, scored catastrophically, evicted. The ASC lever the §9.64 lane
contemplated could flip at most the 109: **it is not the lever.**

**Why every ride plan died (ride_pairing.csv, iterations 200-799):**
outbound legs paired at **0.196**, return legs at **0.0079**, intermediate
legs at **0.0** - and an unpaired leg re-modes to a physical walk averaging
5.56 km (§9.55). A ride subtour needs every leg paired; with returns
unserved, every proposed ride tour carried a multi-hour walk home and lost
to anything. Three structural causes, each measured:

1. **Every binding served the outward anchor only.** Both binder passes
   (§9.46 household, §9.60 non-household) bound a serve tour to the
   passenger's outward trip; nothing anywhere served a return leg. Weekday
   supply was exhausted doing it (55,249 of 55,614 unbound HX tours).
2. **The uniform seed gave a bound driver's serve tour `car` with p=0.2 -
   and 0.196 was the realised outbound pairing ceiling.** The seed
   probability WAS the ceiling: a serve tour seeded walk/pt/bike/ride
   cannot serve the passenger booked onto it, and MATSim's independent
   per-agent selection rarely rediscovers the coherent two-sided state.
3. **A drawn intermediate stop (p=0.15) on a bound serve tour replaced the
   serving leg** with two legs matching neither endpoint under the declared
   `both_links` rule - one in seven bindings unpairable by construction.

**The §9.64 reading "supply is not the binding constraint" was
survivorship bias**: 100% of *surviving* requests paired because selection
had already killed every plan whose requests could not. The binding
constraint was one-directional supply allocation plus seed decoherence.
**M2 (driver-detour lifts) stays un-built** - round-trip re-allocation
answers the return gap without adding a driver-kilometre beyond the
observed rate.

**The repair (all demand-build, no new observation, no added tour):**

- **`B.activity.escort_binding_directions` = `round_trip`** (assumed,
  swept vs `outbound_only`): both binder passes allocate the same
  observed-rate serve tours as drop-off + pick-up pairs per direct 2-leg
  passenger tour - half the passengers, both directions, all-or-nothing
  (a one-way binding cannot change any choice). The non-household pass
  prefers the same driver's second unbound tour for the pick-up.
- **`B.activity.escort_binding_direct_tour` = true** (derived): a BOUND
  serve tour suppresses the intermediate-stop draw.
- **`B.mode.serve_tour_seed` = `car`** (derived) and
  **`B.mode.bound_passenger_seed` = `ride`** (assumed, swept vs
  `uninformed`): bound serve tours seed as the one mode that can serve;
  round-trip-covered passenger tours seed at the coherent two-sided state.
  Seeds only - SubtourModeChoice remains free, ChangeExpBeta keeps or
  abandons.
- **`liftHousehold` becomes a comma-separated list** (two serving
  households possible); `RidePairingEngine` searches all of them,
  `sample_population` unions the whole chain into one sampling cluster.
  `B2_escort_bindings_<day>.csv` (new) records household-side coverage by
  direction; `B2_lift_bindings_<day>.csv` gains a `direction` column.

**Family boundary.** These are demand changes: the §9.58-§9.63 family
CLOSES with the two completed arms as its record; nothing run on the
regenerated demand compares to them. The #65 contiguity assertion guards
the new splice paths unchanged.

## 9.69 The missing short-trip mass gets its observed distribution (24 August 2026, issue #30)

**The gap (re-measured §9.64):** 4.45% of generated legs under 1 km, walk
mean trip 5.56 km vs 0.70 observed. The loss site was GENERATION
(placement, scoring and mode choice were exonerated on #30), and the
missing piece was a citable observed distance-band distribution.

**The observation found:** Bureau of Transport Statistics, *Household
Travel Survey Report: Sydney 2012/13* (Nov 2014, ISBN 978-0-7313-2869-7) -
the only Australian government-published trips-by-distance-band table
located (the modern HTS releases publish no distance bands at any
geography, checked against the Feb-2026 data dictionary). Table 4.4.7
(by purpose, linked trips): up-to-1-km shares - commute 5.9%, work
business 9.0%, education 15.8%, shopping 27.7%, personal/social/other
25.5%, serve passenger 15.7%, **all purposes 18.8%**. Table 4.4.6 (by
mode): walk is 70.9% of all up-to-1-km trips; 74.6% of walk-only trips
are up to 1 km; walk-only mean 0.78 km - a negative exponential with the
package's held Newcastle walk mean (0.70 km) reproduces the Sydney bands
within ~1.5 pp, and the Victoria Walks/VISTA Melbourne distributions
(median 630 m, 63% of sub-1-km trips walked) independently replicate
level and decay. Declared as `B.activity.short_trip_band_share`
(literature, ±25% - the Sydney-to-regional transfer), with the band edge
held fixed as part of the observation's identity.

**The mechanism:** the gravity draw becomes a two-component mixture per
purpose - a short kernel over the same attractors whose mean is the
observed walk-only trip length already held in the package
(`B.activity.short_trip_mean_km`, DERIVED from
`C.constraint.trip_length_km.walk` - no new number), and the existing
per-(purpose x LGA) solved decay. The mixture weight is solved per purpose
against the observed band share, and the long kernel is re-solved so every
observed mean stays met exactly (verified on synthetic geometry: means
exact, bands hit, weight clamps to 0 where the base already exceeds the
target). Intermediate stops draw the blended kernels automatically. What
walk share this buys is the next arm's measurement, not this entry's -
the mechanism targets an observed trip-length distribution, never a mode
share (V207 is untouched; proposal §9's ASC-absorption threat does not
arise).

## 9.70 Freight rail: the coal chain is deliberately not simulated, and the two real road interactions are named (24 August 2026)

**Standing directive (24 Aug): exhaustively include all forms of traffic -
cargo trains among them - at observed or academically studied values.**
Researched from ARTC's 2025 Hunter Valley Corridor Capacity Strategy, the
NCIG Sustainability Report 2024, PWCS performance reports, Port of
Newcastle trade reports and TfNSW's Lower Hunter Freight Corridor
assessments.

**The decision: Hunter Valley coal trains are NOT added to the simulated
rail network, because the observed infrastructure keeps them off it.**
~55 loaded + ~55 empty trains/day (ARTC 2025: "one train every 26
minutes", peak provision 72; PWCS unloaded 10,920 trains in 2025, NCIG
5,979 in FY24) run on a **dedicated double-track coal line from Maitland
to Port Waratah**, grade-separated from the modelled passenger line since
the 2006 Sandgate Flyover, diverging to Kooragang between Warabrook and
Sandgate. Adding them to the passenger network would fabricate an
interaction the real network does not have. Where sharing IS real -
Maitland-Branxton west of the study corridor - the HVCCS records that
passenger services get priority, so modelled passenger times are
unaffected. Recorded as a stated scope decision, not a gap.

**The two real road interactions, named and carried as work:**

1. **Level crossings.** TfNSW names exactly two significant crossings in
   the urban area: **St James Road, Adamstown** (shared Main North:
   interstate intermodal + southern coal + passenger) and **Clyde
   Street, Islington** (ARTC freight lines at Islington Junction).
   Officially documented road closures "up to ten minutes" when freight
   crosses (LHFC Draft SEA, 2021). Closure logs are NOT published, so
   the treatment must be closures/day x duration as assumed, swept
   parameters on time-varying link capacity - designed, declared as
   backlog (the crossings themselves are locatable from OSM
   `railway=level_crossing` nodes, no typed coordinate).
2. **Port truck traffic** already sits inside the §9.49 physical truck
   tier; the Mayfield precinct cap (462,104 movements/yr, 1,268/day -
   the only published number, a cap not an observation) is recorded as
   an upper-bound CONSTRAINT on the freight tier at the port gateway,
   never a target.

Non-coal rail freight (interstate intermodal through the shared line,
grain 2.95 Mt in 2025, Gunnedah-line services) has no published
per-day count on the shared urban section; it enters only through the
level-crossing mechanism above, whose frequency is swept.

## 9.71 Two 0b items measured: the pre-LR cross-section from OSM history, and the VoT set checked against EPV January 2025 (24 August 2026, issue #63)

**The pre-LR corridor was 1 lane per direction everywhere OSM tagged it —
the assumed 2 is contradicted.** Overpass attic queries at
`[date:"2017-01-01"]` (pre-construction) and `[date:"2016-01-01"]`
(cross-check), landed under `data/raw/osm_attic/` with provenance and the
exact query strings: of 21 named Hunter/Scott segments in the corridor,
**9 carry a `lanes` tag and every one is `lanes=2` + `oneway=no` — one
lane per direction**; zero segments tagged 4 lanes or per-direction lanes
at either date; the only one-way elements are the pedestrianised Hunter
Street Mall pair. `A.corridor.pre_lr_lanes_per_dir` moves **2 → 1**
(source `assumed` → `literature`), the sweep keeps 2 as the upper
sensitivity (57% of segments untagged; OSM records marked through-lanes,
not kerb-to-kerb). **This is the B3 counterfactual moving onto evidence:
the assumed value had doubled the pre-LR corridor's capacity.** The E1
pre-LR variants regenerate from the declaration before any P5 scenario
run; nothing already run used the variant networks. ODbL 1.0 applies to
anything published from the attic files.

**The VoT set against TfNSW Economic Parameter Values, January 2025**
(v2025.1, June-2024 dollars; the 0b "EPV check" item) — recorded, not
absorbed; no scoring value changes without its own decision:

- **Supported inside the declared ±30%:** HW 18.6 (EPV private/commute
  $20.62), WB 55.4 (business $66.90), trip-weighted 16.96 (behavioural
  all-modes $18.74), and `C.scoring.monetary_distance_rate` 0.18 AUD/km —
  consistent with EPV's *perceived* cost basis (fuel incl. taxes, 21–22
  c/km urban stop-start), which is the basis EPV itself prescribes for
  demand modelling; the full resource VOC (~50 c/km) is a different
  quantity for CBA, not for scoring.
- **Divergent:** HE 9.3 — EPV assigns education the FULL private $20.62
  (122% above; outside the sweep). Marginal: HS/HO/NHB 15.2 vs $20.62
  (35.7% above the point, just outside ±30%). Caveat recorded with them:
  EPV's CBA table deliberately flattens purposes, while its own Appendix
  A1 endorses purpose-differentiated values for demand models — so these
  are divergences from the CBA convention, not necessarily from
  behavioural practice. `C.vot.concession_factor` 0.75: the only EPV
  datum (Sydney Trains concession VoT ratio) implies **0.48**, outside
  the [0.6, 0.9] sweep — flagged with the sweep unmoved.
- **A gift for the PT-composition lane:** EPV Table 2.7 publishes
  transfer penalties in equivalent in-vehicle minutes — bus–LR **3.8**,
  train–LR **4.1**, bus–bus 14.8, train–bus 13.7 — an official anchor
  inside the declared 3–15 min transfer sweep when the corridor
  composition diagnostic (§9.64 lane 4) reaches the transfer point.

---

## 9.72 Two silent launch deaths end the first post-repair arm attempt; the project's conditional replication rule (24 August 2026, third session, issue #70)

**What happened.** The session's `/goal` (third session, 24 Aug: *"make any
fixes that can be done before the next run, then run and monitor"*)
authorised the post-repair base arm (task 4.6.9). Two launch attempts both
died silently within minutes, and the campaign was then ended at
`/handoff`:

- **Attempt 1** — `python run.py --seed 20260810 --threads 8 --xmx 30g`,
  detached via PowerShell `Start-Process` with redirected logs (the §9.68
  trap-4 pattern). Run `20260824T212729_1000it_25pct` started 21:27:29;
  `matsim.log` froze at 21:28:23 — **~54 s after launch**, mid
  `PersonPrepareForSim` at person ~65,536; launcher and JVM both gone. No
  MATSim exception, no `hs_err_pid*`, empty stderr. Closed out as
  `results/aborted_20260824T212729_1000it_25pct`, `_meta.json` status
  `failed`.
- **Attempt 2** — the same command via WMI `Win32_Process.Create`
  (parented to the WMI provider service, outside the launching tool's
  process tree). Run `20260824T225951_1000it_25pct` started 22:59:51; the
  tree died **within ~2 minutes, before config emission finished** — no
  `matsim.log` was ever written. Closed out as
  `results/aborted_20260824T225951_1000it_25pct`, status `aborted` (the
  run was ended by instruction).

**Attribution: OPEN.** Two different detachment routes died the same way —
silently, tree-wide, zero error artefacts. That matches neither OOM (no
`hs_err`), nor a MATSim defect (attempt 2 died before MATSim started), nor
the §9.36/#66 stall (processes gone, not hung). The prime suspect is the
agent-session sandbox reaping processes spawned from tool calls — including
WMI-created ones — shortly after a call or turn ends; the second death was
also coincident with a user interrupt. Not proven; recorded as
unattributed with both timelines. Issue **#70** tracks the fix.

**Operative consequence (until #70 closes or the deaths are attributed):**
launch convergence arms from a shell outside the agent session — a plain terminal, or
a Task Scheduler job created outside the agent session — never from agent
tool calls, by any detachment route. A launch is verified only when
`matsim.log` progresses PAST `PersonPrepareForSim` into iterations with
the launching context gone. A 1% probe does not cover this class: the
§9.68 probe survived because it finished inside its launching context.

**Directives recorded this session:**

1. The `/goal` run approval was consumed by the two dead attempts and the
   end-run instruction. **No run approval is standing**; the next
   arm needs a fresh stated-cost yes (~65–67 h at 25%×1000).
2. **Conditional replication rule (standing):** arm B (the seed
   replication) launches ONLY if arm A's early iterations, running alone,
   pace at the prior campaign's per-iteration time — compare iterations
   2–5 against the closed family's 217–253 s/it band (~233 s/it
   single-arm, §9.59). If slower, arm A runs alone.

**What this deliberately does not do:** no model, data, registry or target
value changed; the regenerated §9.68/§9.69 demand package is untouched and
stays probe-verified; the two aborted directories are launch records, not
results (`_run.json` absent by definition); the 67/143 split is untouched.

---

## §9.73 — The simulator stack re-examined: MATSim re-affirmed, and the embedded MATSim version recorded (25 Aug 2026, fourth session)

The session's `/goal` asked whether MATSim is still the best tool or whether a
materially better or faster framework exists. Answered by a documented survey
(web-researched 25 Aug 2026, sources in the session's research record), not by
habit:

- **BEAM** (LBNL, built on MATSim): ~10× *slower* per iteration at comparable
  scale (reported ~56 min/it for 315k agents), actor-model concurrency
  undermines seeded determinism, no documented Windows path.
- **POLARIS** (Argonne) — the one serious rival: reported 1–2 orders faster
  (mesoscopic, not like-for-like with a per-agent queue mobsim carrying
  physical walk/bike), actively developed, Windows-viable. Fails this
  project's gates: distribution by licence request rather than a public repo
  (fatal for a study whose premise is being more transparent than the
  business case it examines), determinism and GTFS-fidelity unverified, and
  the 13 custom `citysim` Java sources would be rewritten into a C++ core
  with a gated contribution process.
- **SimMobility / mobiliti / TRANSIMS**: dormant, HPC-proof-of-concept, or
  dead. **DTALite and the GPU simulators (MOSS, LPSim)**: fast trip
  *assignment*, no co-evolutionary activity-based demand, no
  transit-schedule fidelity, no custom modes. **Commercial (Aimsun, PTV,
  Caliper)**: capable and seedable but closed — a third party cannot rerun
  the study without buying the licence.
- MATSim's own trajectory is healthy (annual year-named releases through
  2026, an active association and institutional development); the **DSim**
  distributed-mobsim prototype (reported ~119× over QSim) is recorded as
  watch-only; Hermes (~2.5×) drops signals and dynamic vehicle handling and
  is presumed incompatible with the ride-pairing engine — not adopted.

**Decision: MATSim stands. Migration is rejected** — every faster framework
drops something this study cannot lose, and a migration would invalidate
every run and port all custom code for a speed problem better attacked by
concurrent arms and, later, surrogate-guided sweeps.

**The embedded MATSim version is now recorded:** the pinned
`pt2matsim-26.6-shaded.jar` carries `org.matsim:matsim` **`2027.0-2026w25`**
(verified 25 Aug 2026 from the jar's own `META-INF/maven` metadata) — a
current-generation 2026-week-25 weekly snapshot, not a 16.x-era MATSim as
previously assumed in conversation. The jar digest is unchanged; nothing was
re-pinned. Consequence for any future contrib adoption (#73): contribs must
match this version and must not share a classpath with the shaded jar — a
separate Maven-built run stack, which is a §14 toolchain change when it lands.

**What this deliberately does not do:** no toolchain change, no re-pin, no
model or data value changed; nothing here is a result.

---

## §9.74 — SUMO descoped by recorded decision: MATSim is the single simulator (25 Aug 2026; the fifth premise correction — supersedes proposal §5's twin-simulator architecture)

**Decision required (25 Aug 2026): the study is "officially free of SUMO".**
Recorded here as a decision with its consequences; executed mechanically as
issue #72 (deliberately not bundled with this record). Nothing is rewritten
in history: the SUMO corridor artefacts, their build scripts and their
DECISIONS entries stay in the record as what they are — built six times,
simulated zero times.

**Evidence basis.** The 25 Aug absorption research established that every
SUMO-deferred corridor question except two has an adequate native MATSim
representation: level crossings via core `NetworkChangeEvents` (#68),
charging dwell via mapped-schedule `departureOffset` + `awaitDepartureTime`
(#74, the §3.5 derivation rule), taxi as a priced mode (§9.42, #49), the
Hunter St lane loss via the E1 patches, and frontage volumes from the
physically simulated walk events. SUMO's unique residual was (a)
signal-accurate S2b and (b) reliability variance from ≥30 seeded
replications — and `RUN.sumo.replications` has been `unobtained`/null since
§9.5 measured that load does not fit this machine (issue #6's record).

**Where each SUMO-unique deliverable lands:**

1. **S-b (transit signal priority)**: answered natively — a standing directive orders
   an explicit corridor signal + tram-priority build in MATSim
   (§9.75, #73). Until that lands, S2b remains the scalar
   `E.s2b.signal_delay_removed_share` sweep, and every corridor number stays
   a band per §7.2/§9.21 either way.
2. **Reliability variance** (GJT standard deviation across micro
   replications): **descoped as a stated limitation** — it was never
   affordable on this machine, and the method note (deliverable 6) reports
   it as such.
3. **Deliverable 7 / §9.16** (the 5 s MATSim↔SUMO outer-loop tolerance):
   **retired with the loop it governed.** The §9.16 derivation stands in the
   record as the analysis it was.
4. **P5 tasks 5.1 and 5.2 are deleted** (5.2's standing DELETE proposal is
   thereby decided); **5.3 resolves to its REWORK form** — the charging
   dwell stays swept, never pinned, and lives natively (#74).
5. **Pedestrian delay/LOS is formally out of scope** (it was already barred
   from SUMO by the §3.6 segfault); pedestrian *volumes* stay in scope from
   the physical walk events.

**What this deliberately does not do:** it does not delete anything from
history or from `data/raw/`; it does not change a registry value in this
change (that is #72's execution, a logged toolchain change when it happens);
it does not invalidate any run — no completed run ever consumed a SUMO
artefact; and it does not weaken the sweep discipline — the signal
assumption set (`A.signals.*`, the S2b/S2c/bus delay shares) is untouched
and remains the operative representation until #73 lands.

---

## §9.75 — The signalling dossier, the operated-SCATS-data discovery, and the project's all-modes-first batch (25 Aug 2026; issues #49, #68, #72–#78)

**The dossier.** A ten-file research dossier on SCATS and Newcastle
signalling landed at
[`design/signalling/`](design/signalling/README.md) (moved from a temporary
holding area; design-dossier class, the point-to-point-mode precedent). Its
epistemic discipline matches the project's: every claim tagged
`[documented]` / `[commonly claimed]` / `[gap]`. Substance: SCATS mechanics
head-to-toe from the public corpus (functional closure checklist in file 09);
the MATSim signals contrib mapped in detail (data model, SYLVIA, Lämmer, the
custom-controller seam, the two regional-scale traps); the algorithms in
pseudo-code; and the data-availability map (open / refused / purchasable).
**`A.signals.scats_phasing` stays `unobtained` for the 14 modelled
intersections** — the dossier changes the evidence base, not that status.

**The discovery (file 08).** Operated SCATS interpreted history for two
Newcastle intersections is legitimately public inside planning-portal TIA
PPSHCC-137 (121 Hunter St, exhibited 2023): 24 h of 15-minute per-phase,
per-group and cycle statistics for **TCS 923 (King/Steel)** and **TCS 1138
(Hunter/Steel)**, Tuesday 19 July 2022. Operated cycles: corridor-adjacent
**72–81 s**, parallel arterial **104–113 s**, against the assumed 110 s swept
80–140 s — evidence that supports the sweep's lower half and the assumed
value's realism for arterials, and **not a registry change**: neither site is
one of the 14 modelled intersections (A2 `scats_site_id` list). This opens a
free third acquisition route (TIA harvest) beside "refused" (§9.21) and
"purchasable ~AU$200–600"; both routes are parked as decisions required on
issue #78, with an immediate recommendation to archive the TIA PDF against
link rot.

**The project's batch (directive, 25 Aug): all modes covered first.** The
next session implements, as one work programme: corridor signals + tram
priority + lanes natively in MATSim (#73 — signal rungs 2+4 of the dossier's
ladder; the Maven run-stack build rides with it as a logged toolchain
change), **taxi/rideshare as a priced mode (#49 — this supersedes §9.42's
"nothing built before deliverable 5" sequencing by recorded direction)**, level
crossings (#68), native charging dwell (#74), the SUMO descope execution
(#72), warm restart (#75), the run progress digest (#76), the cross-run
index (#77), and the rung-1 registry sharpening (sweep-basis citations from
the dossier and the TIA evidence; `E.s2b.n_segments` derived from the mapped
feed). Rung 3 of the ladder (a SCATS strategic emulator) is **not** ticked.

**Constraints carried into the batch (from the dossier, each already paid
for elsewhere):** the double-count rule — explicit signals meter
saturation-flow approaches, and the implicit `A.signals` delay must come out
of the same movements, one representation per effect; the sample-size
discretisation trap — a 10–25% sample discharges 0–2 vehicles per short
green, so the batch adds a per-green discharge-count check before any signal
effect is trusted; the `QSignalsNetworkFactory` single-binding risk against
the hand-assembled `citysim` QSim — a toy probe precedes any scenario; and
Stewart Avenue is a T-aspect signal site, never a boom-gate closure — #68
and #73 must not double-treat it.

**Sequencing tension, stated rather than resolved here:** the
recorded order runs the 4.6.9 arm first (measuring the §9.68/§9.69 repairs
in isolation, ~65–67 h) and then activates this batch as ONE new family
boundary; folding the batch in before that arm runs would save one arm but
confound the ride/walk repair measurement with the signals/taxi/crossings
changes. The 4.6.9 approval remains spent (§9.72); whichever order is picked,
the batch activates as a single boundary, not several.

**What this deliberately does not do:** no code was built this session; no
registry value, scenario, run input or target changed; the 67/143 split is
untouched; the TIA numbers are cited evidence, not acquired inputs (that is
#78); nothing here is a result.

---

## §9.76 — Batch 4.7 BUILT, inert: the all-modes batch lands as code, data and probes; the descope executed; the harness safety set live (25 Aug 2026, overnight session; issues #49, #62, #63, #68, #70, #72–#78)

**Directive.** The session's `/goal` ordered the 25 Aug batch (§9.75)
implemented overnight — signals, taxi and the full simulation factors first,
the free TIA harvest for SCATS, and every other runless issue worked — with
everything model-changing built INERT per the one-boundary rule. That is what
happened; **no scenario ran, no target moved, the 67/143 split is untouched,
and nothing below is a result.** The 4.6.9 ordering decision (run-first vs
fold-in) remains open and is untouched by any of it.

**The harness safety set is LIVE (no model change, no boundary):**

- **Warm restart (4.7.1, #75).** `--warm-start <dead_run_dir>` starts a NEW
  runner-named run from the dead run's newest `ITERS/it.N` plans with
  `firstIteration` aligned; `warm_started_from` is written into `_meta.json`
  and `_run.json` and resume matching refuses to cross it. **Caveat, recorded
  as the issue demanded: a warm-started run is NOT bit-identical to an
  uninterrupted one** — the RNG stream and travel-time memory reset at the
  checkpoint. **Whether a warm-completed arm counts as a valid arm or a
  diagnostic is an OPEN project decision**; until it is taken, the provenance
  link makes either ruling applicable after the fact, and the cross-run index
  labels warm runs distinctly.
- **Progress digest (4.7.2, #76).** `_progress.json`, written by an observer
  daemon beside the live view (the 9.36 isolation discipline: atomic replace
  with bounded retry, failures surfaced in the next write, structurally unable
  to reach the mobsim): every mode individually, drift vs the declared
  tolerance via the one `summarise_run.relaxation` implementation, pace vs the
  new declared `RUN.monitor.pace_band_s` ([217, 253] s/it — the §9.72 band as
  a field, held fixed as a monitoring reference), and `solo_in_band` over the
  declared `RUN.monitor.solo_check_iterations` [2, 5] — the conditional-
  replication rule, mechanised. Contract: `outputs/progress.schema.json`.
  **Verified live inside a real run** (the detached smoke probe below).
- **Cross-run index (4.7.3, #77).** `build_run_index.py` → `results/INDEX.md`
  + `.csv`: one row per directory with status, record, relaxed, comparability
  FAMILY and per-mode fit. Families are DECLARED once in
  `docs/audit/run_families.json` (F1 pilot → F5 ride/walk repairs, each with
  its decisions refs), never re-derived; one 18 Aug dead launch is left
  explicitly unattributed rather than guessed. The probe/arm boundary is the
  declared sweep floor of `RUN.controler.last_iteration`, not a constant.
- **Detached launch (#70) — built AND verified.** `run.py --detach` registers
  the run as a Task Scheduler one-shot whose lifetime is independent of the
  launching shell. Verified by the issue's own criterion: smoke probe
  `20260825T033850_2it_1pct` progressed past `PersonPrepareForSim` through
  both iterations to rc=0 with `_run.json` written, the launching context
  gone throughout — passing through exactly the minutes-scale window where
  both §9.72 launches died. (An earlier attempt the same night,
  `aborted_20260825T033406_2it_1pct`, failed rc=1 in 10 s on a REAL defect
  the detachment surfaced — see the unmaterialised-module lesson below — and
  closed itself out correctly with the launcher gone: the death-reporting
  path is verified too.) The first arm-scale detached launch should still be
  watched; §9.72's attribution stays open as history.

**The descope is EXECUTED (4.7.4, #72; §9.74's mechanics; §14 row).** The 17
`RUN.sumo.*` fields, the SUMO fetch, the corridor package checks, 12 manifest
rows, the `sumo_param` binding, the basemap's SUMO lane layer and the city's
SUMO corridor builder are gone; the A2↔E1 signal-variant contract check
survives (it was never about SUMO — the native build reads the same table).
`E.coupling.outer_loop_tolerance_s` retired with deliverable 7 (§9.16's
derivation stands in the record). The basemap loses its corridor lane
geometry — stated, not silent.

**The model-changing set is BUILT INERT (4.7.5–4.7.8).** Nothing consumes any
of it until the batched family boundary; the assembled §9.68/§9.69 run inputs
are byte-untouched, and the one emitted-config difference (below) is read by
nothing on the standard stack.

- **Level crossings (4.7.5, #68).** `build_level_crossings.py` derives the two
  boom-gated freight crossings from OSM `railway=level_crossing` barrier tags
  clustered and matched to car links through the network's own `osm:way:name`
  against the DECLARED road names (`A.crossings.freight_road_names`,
  literature-held: the network spells it "Saint James Road" — TfNSW documents
  abbreviate). 9 new `A.crossings.*` fields; closures/day 30 swept [10, 60]
  and duration 240 s swept [60, 600] are ASSUMED AND SWEPT (logs unpublished,
  §9.70; the official "up to ten minutes" is the sweep top); closures spread
  uniformly per site and PHASE-OFFSET between sites (any richer pattern would
  be invented); each link restored to ITS OWN recorded capacity/freespeed.
  **The Stewart Avenue rule (§9.75) is ASSERTED**: the builder refuses any
  closure within 500 m of an A2 corridor intersection — the emitted sites sit
  3,798 m and 2,282 m away. `RUN.travel_time.bin_size_s` is declared at
  MATSim's own 900 s default (inert) with the ≤300 s activation basis in its
  sweep — a closure shorter than a bin is invisible to the router.
- **Charging dwell (4.7.6, #74).** `build_charging_dwell_offsets.py` derives
  `transitSchedule_dwell.xml.gz` per scenario from each scenario's OWN mapped
  schedule (never the mapper, §3.5): every INTERMEDIATE intervention-mode stop
  holds `departureOffset = arrivalOffset + max(existing gap, the scenario's
  resolved dwell)` with `awaitDeparture` on. Arrival offsets untouched, so the
  12.00 min anchor is unchanged by construction, and the builder refuses a
  hold that does not fit the timeline. **DECISION: charging is CONCURRENT with
  boarding** — dwell = max(board, charge), the point of charge-at-stop; the
  additive reading would need a custom `TransitStopHandler` and would
  double-count boarding. S2/S2b/S2c hold 8 stops at 20 s, S4 18, S5 24; S2a
  (0 s) is the identity, which is what S2a means. The field stays swept 10–35.
- **Explicit signals + tram priority (4.7.7, #73; rungs 2+4).** Everything the
  §9.75 traps demanded, together:
  * `build_matsim_signals.py` generates `signal_systems/groups/control.xml`
    for the 14 intersections per scenario from the A2 declared values against
    each scenario's own mapped network. The A2 clusters are stop-line OSM
    nodes the network build simplifies away (measured: 12 of 14 keep none),
    so a system is the SET of car-carrying network nodes within the declared
    `junction_match_m` — the SUMO junctions-join semantics, ported with the
    retiming arithmetic. Approaches classify corridor/cross by the corridor's
    own derived axis; sites with no cross-street car approach are recognised
    as MID-BLOCK crossing signals (8 of 14 were installed for the light rail,
    §9.24) with their own one-car-phase structure.
  * **Phase structure is link-level and says so**: observed turn-lane coverage
    on the corridor trunk is 46 of 280 edges (16%), so movement-level lanes
    would be invented geometry — corridor approaches take the A2 split's
    45+15, cross approaches 30+10, the tram group ties to the corridor phase
    (the T-aspect moves with parallel traffic, dossier 02 §2). Lanes and
    protected turns stay OPEN on #73.
  * **The double-count rule lands as artefacts, both halves at once**:
    `signals_capacity_patch.csv` re-raises every signalised approach to the
    declared `A.signals.saturation_flow_veh_h_lane` (1900, literature, swept
    1800–2050) × lanes, and `transitSchedule_signals.xml.gz` removes the
    variant's OWN embedded per-intersection tram delay (A2
    `mean_delay_to_tram_s`; removing the generic 26 s everywhere
    over-subtracted on S2b — measured, refused by the builder) from arrival
    offsets, derived from the dwell variant. `A.signals.representation`
    (categorical `implicit_delay`/`explicit_signals`) is the switch code
    CHECKS: the emitter adds the signals module, the harness swaps stack and
    entry point, and `build_scenario_schedules.py` now REFUSES to bake the
    implicit delay under `explicit_signals`.
  * **Per-green discharge check (dossier 04 §6.2)**: worst approach 7.1–7.9
    veh/green at 25%, ~0.3 at 1% — in the report, per approach, so nobody
    trusts an explicit-arm effect the discretisation cannot carry.
  * **The Java run stack**: `TramPriorityController`
    (`CitysimTramPriority`) wraps the generated fixed-time plan; detection
    from the events stream on the system's own tram-group links (transit
    vehicles identified by `TransitDriverStartsEvent`, never id convention);
    green extension bounded by the declared per-cycle budget;
    `extension_recall` truncates after min green; `conditional` gates on the
    vehicle's own `VehicleArrivesAtFacility` delay; borrowed green REPAID to
    its phase next cycle (the Melbourne compensation rule). Deterministic —
    no wall clock, no Random. Parameters arrive only through the emitted
    `tramPriority` module from the declared `A.signals.tsp.*` fields.
  * **Both §9.75 toy probes PASS on the Maven stack**: the
    `QSignalsNetworkFactory` single-binding probe (red gates the buffer under
    the full citysim component reordering, per-green discharge counted, the
    `TolerantAgentSource` walk path alive) and the priority probe (a REAL
    `TransitSchedule` tram: extension granted, tram clears in the extended
    green 32 s vs 60 s fixed-time, compensation repaid next cycle).
  * **Recorded consequences for activation**: the contrib requires
    `qsim.usingFastCapacityUpdate=false`; S3's priority controller currently
    has no tram-group members (BRT bus detection is open on #73); and the
    `tramPriority` module now emits into EVERY config — its fields are
    registry-bound, so the reach probe must see them move — and is read by
    nothing on the standard stack. **The unmaterialised-module lesson**: this
    MATSim REFUSES a config module no registered ConfigGroup materialises
    ("Unmaterialized config group: tramPriority", measured on the first
    detached smoke probe), so `TramPriorityConfigGroup` lives in `src/java/`
    and registers on every stack while the controller stays signals-side.
- **Taxi (4.7.8, #49; supersedes nothing — §9.75 already resequenced it).**
  ONE priced point-to-point mode blending two services at the declared
  `B.taxi.rideshare_trip_share` (0.66, IPART 2025 last-trip split, swept
  0.4–0.8): the MEASURED urban taxi schedule — the Point to Point Transport
  (Fares) Order 2025, archived at `data/raw/p2p/` with provenance: flagfall
  $5.00, $2.52/km first 12 km, and clause 2(g)(ii) naming the Newcastle
  Transport District URBAN — blended with literature rideshare rates
  ($1.95 + $1.50/km, swept). **A premise correction rides with it: the §9.42
  dossier's "$5.17 flagfall / $2.61/km" is NOT in the instrument** —
  corrected in the dossier against the archived order. Mechanics: per-km fare
  as `monetaryDistanceRate` (native), flagfall through the new `fare` module
  to `FareChargeHandler` (deferred `PersonMoneyEvent`s, the
  ParkingChargeHandler discipline), wait/booking time folded into the mode
  constant at the trip-weighted VOT (`C.taxi.wait_min`, 5 min swept 2–12),
  the ASC swept over the negative half-axis (`C.taxi.asc` — no target
  exists), travel time bound to the congested network like ride (#28's
  lesson), and the realised volume REPORTED against `B.taxi.daily_trips_band`
  [15k, 25k] as a CONSTRAINT, never a target. `fit.py` folds bike+taxi
  against HTS "Other" exactly as car+motorbike folds. INERT: everything gates
  on `taxi` entering the declared choice/routing vocabularies at the
  boundary; the default emission is verified unchanged.

**Registry sharpening and 0b moves (4.7.9, #63) — six fields onto
measurement, one candidate rejected on evidence, one new falsifier:**

- `E.s2b.lr_segment_count` assumed 5.0 [4, 8] → **measured 5** from the mapped
  route profile (6 stops), closing its own "outstanding work" note.
- `E.schedule.weekend_headway_factor` assumed 1.5 → **measured 1.875**: the
  operated NLR's own weekend factor (median daytime headways 8 → 15 min, SAT
  and SUN alike, base2026 feed); still swept — the S1/S3 services it scales
  are invented.
- `E.s1.shuttle_speed_kmh` — **the assumption is CONFIRMED by measurement**:
  the operated 2015–2019 era3 route 110 shuttle (426 trips, shape distances)
  ran a dwell-inclusive median 23.4 km/h ≡ 26.0 km/h running speed at the
  declared dwell. Value unchanged, source now measured.
- `E.s1.first_hour`/`last_hour` → measured 4 and 27 against the operated span
  04:03–27:35 (the old sweep top understated the operated span; 27 → 28).
- `A.lightrail.line_speed_kmh` assumed 40 → the **measured regulated
  ceiling**: 40 km/h over 73.4% of corridor-trunk regulated length in the
  held Speed Zones join; sweep retained because running speed sits at or
  below a ceiling. (Never derived from GTFS — unidentifiable, #63's own
  caveat.)
- `A.parking.capacity_default` — derivation ATTEMPTED and REJECTED: the 4,880
  observed OSM capacities are tagged micro-features (median 1 space), not an
  estimator for the systematically larger untagged facilities. Stays
  assumed+swept, with the verdict recorded so nobody re-attempts it blind.
- **The departure-profile constraint (#63 item 6)**:
  `measure_departure_constraint.py` compares the realised B2 departure-hour
  distribution (person trips, freight excluded) against the observed RMS
  light-vehicle profile → `params/C6_departure_profile_check.json`. First
  reading: WEEKDAY overlap 0.858 with peaks MATCHING at 16:00; **SAT/SUN
  modelled peaks sit at 15:00/14:00 against the observed 11:00 — the assumed
  weekend shapes skew 3–4 h late.** A recorded, falsifiable finding on 144
  previously unexaminable numbers; a constraint, never a target.
- Sweep-basis citations (§9.75's rung 1): `scats_phasing`,
  `delay_per_intersection_s` and `min_green_s` now cite the operated TIA
  evidence and the TTD/dossier bases.

**The SCATS acquisition (#78) — DECIDED by the session's directive: the free
TIA route, no LX purchase.** PPSHCC-137 is ARCHIVED (`data/raw/planning_tia/`,
sha256-recorded, 245 pp) with the licence position stated:
validation/sweep-basis evidence only, never merged into a CC-BY artefact, no
registry value set from it — `A.signals.scats_phasing` STAYS `unobtained`.
**A correction to §9.75's record rides with the archive: the TIA's site is
643 Hunter Street, Newcastle West — not "121 Hunter St" as first recorded**
(the document's own title page; both dossier files corrected). The companion
PPSHCC-306 could not be fetched (its attachment URL needs a per-document
timestamp); the systematic corridor harvest stays a standing opportunistic
lane on the closed issue's record. Two further dossier defects fixed while in
there: file 04's stale A2 path and file 06's wrong field name.

**City-agnosticism (#62, finding A1 — half landed).** The output schemas no
longer enumerate one city's scenarios and day types: the files are city-free
and `outputs.py` injects the enum from `city.json` at validation time —
exactly as strict for the active city, correct for any other, weaker-never-
wrong if the descriptor is unreadable. The `light_rail_boardings` key rename
and findings A2/A5/B1/B4/B5 remain open on #62. The fixture test's scored-
mode extraction now reads actual `modeParams` parametersets (the flat
`<param name="mode">` read miscounted the new tramPriority regime as a mode).

**What activation at the family boundary requires, so it is a checklist and
not archaeology:** flip `A.signals.representation` → `explicit_signals`; add
`taxi` to `RUN.mode_choice.modes` and `RUN.routing.network_modes`; lower
`RUN.travel_time.bin_size_s` to ≤300; set `qsim.usingFastCapacityUpdate=false`
for signal runs (the contrib refuses otherwise); regenerate the run-input
sets consuming `transitSchedule_signals.xml.gz` (which carries the dwell
transform), the crossings change events and the capacity patch; author the
boundary's DECISIONS entry naming the new family. ONE boundary (§9.75), and
the 4.6.9 ordering decision still governs when.

**Toolchain (§14 rows).** SUMO 1.27.1 OUT; Apache Maven 3.9.9 IN
(sha256-pinned); the signals RUN STACK in: `org.matsim:matsim` +
`org.matsim.contrib:signals` at **2027.0-2026w25** — exactly the version the
shaded jar embeds (§9.73) — resolved by the committed `run-stack-pom.xml`
into `.tools/run-stack/lib` (201 jars, every one sha256-recorded in
`toolchain.json`; visualisation-only dependencies excluded). Signal runs use
that stack and `citysim.CitysimSignalsControler`; nothing else changed
stacks, and the two never share a classpath.

**Also live from this session**: the sandbox allowlist gained the NSW
planning portal, the Maven repositories (repo1.maven.org, repo.osgeo.org)
and the TfNSW corporate + IPART domains — each tied to a provenance record
or the pinned toolchain; `_launch/` wrappers under `results/` are the
detached launcher's artefacts.

**What this deliberately does not do:** no scenario ran (two 1% smoke probes
verified plumbing; both are labelled probes in the index and neither is a
result); no family boundary was crossed; the assembled 4.6.9 run inputs are
byte-identical; `E.replication.n_replications` and the 4.6.9 re-approval and
ordering decisions remain the project's to take; the §8.5-held constants
stayed held.

---

## §9.77 — The activation boundary is CROSSED: explicit signals, crossings, native dwell and taxi are LIVE in the assembled inputs; S3 gets bus-keyed priority; family F6 declared (25 Aug 2026, sixth session; issues #49, #68, #73)

**Directive.** The session's `/goal` ordered every runless GitHub issue
implemented — signals, taxi and the full simulation factors first, the free
planning-portal TIA route for SCATS — and that directive RESOLVES the §9.75
ordering question by consequence: no run is authorised, so the
run-the-repairs-arm-first option (which needed a ~65–67 h launch) is not
available to this session, and the batch activates first. **The cost of that
order is recorded, not hidden: family F5 (§9.68/§9.69) closes UNMEASURED — the
ride-repair and short-trip-mixture effects will never be attributed separately
from the §9.76 batch.** The F5 inputs stay regenerable by construction
(`A.signals.representation=implicit_delay`, `A.crossings.representation=absent`,
taxi out of the two `RUN` vocabularies, regenerate), so the repairs-first
measurement is revivable if it is ever worth an arm.

**The checklist executed (§9.76's closing block, item by item):**

- `A.signals.representation` → `explicit_signals`. The run-input assembly now
  consumes, per scenario: the generated signal data model (systems, groups,
  control), `signals_capacity_patch.csv` applied to the emitted run network
  AFTER the E1 variant patch (a missing patch link is a refusal — it means a
  different network build), and `transitSchedule_signals.xml.gz` — which
  carries the dwell transform (#74) — as the schedule the day-type filter
  reads. `qsim.usingFastCapacityUpdate=false` is written into every signal
  config by the emitter (the contrib refuses it true).
- **A new gate, `A.crossings.representation`** (categorical
  `absent`/`change_events`, mirroring the signals switch): under
  `change_events` every config carries `network.timeVariantNetwork=true` and
  the derived closures file, and the assembly refuses a change-event link the
  scenario network lacks. Flipped to `change_events` at this boundary.
- `RUN.travel_time.bin_size_s` 900 → **300** (the largest bin that resolves
  the central 240 s closure; basis unchanged).
- `taxi` into `RUN.mode_choice.modes` AND `RUN.routing.network_modes`; the
  inert §9.76 plumbing (blended fares, `fare` module, car-bodied vehicle,
  congested network travel time, ASC) engaged without further change.
- The 30 run-input sets regenerated; the boundary is ONE boundary, and
  **family F6 is declared in `docs/audit/run_families.json` in this change.**

**Two defects found by the activation probe, not by reading (both fixed):**

1. **The crossings XML violated the MATSim schema** — `networkChangeEvents.xsd`
   requires `flowCapacity` BEFORE `freespeed` inside an event;
   `build_level_crossings.py` emitted the reverse and MATSim's validating
   reader refused the whole network load. Measured on the first activated
   probe (`aborted_20260825T094456_2it_1pct`, rc=1 in 4 s); element order
   swapped, file regenerated (540 events, 16 links, 2 sites — unchanged
   content, valid order).
2. **The console metrics line hardcoded "taxi/rideshare: not modelled"** while
   the JSON's `not_modelled` row was computed correctly — the print now reads
   the document it summarises.

**The activated stack is VERIFIED at plumbing scale** (probe
`20260825T094638_2it_1pct`, 1%×2, rc=0, F6): the signals contrib engages
(controllers instantiated per system; S2 correctly fixed-time under
`S2_base`'s `tsp_enabled=0`), the change events load, and **taxi is chosen,
routed and priced on the congested network** — 1.44% of Newcastle-LGA trips at
1%, mean 14.94 km / 18.25 min (car-like speeds, exactly the #28 lesson's
intent). A 1% probe verifies PLUMBING ONLY (§9.76's discharge warning: ~0.3
veh/green at 1% — no signal EFFECT is trustworthy below arm scale), and
nothing here is a result.

**S3's priority is now bus-keyed (#73 remainder 2).** The priority stage is a
declared field, not a literal: `A.signals.tsp.priority_group` (definition;
`tram` in the base, `corridor` in S3's overlay) reaches
`tramPriority.priorityGroupId`, `TramPriorityController` resolves the
configured group and watches ITS links for detections, and
`TramPriorityConfigGroup.checkConsistency` refuses a bound module that never
named one. For S3 that means link-level bus priority: detection fires for
every SCHEDULED transit vehicle entering a corridor approach — the BRT trunk
and any local bus on the same approach, which is what a link-level detector
would see; stated, not hidden. **The toy probe grew the matching third case**
(the same signalised toy with the priority group named `corridor` and the
scheduled vehicle a bus): extension granted through the configured id (first
red 40 s vs plan 30 s), vehicle cleared in the extended green — PASS, alongside
the two §9.75 cases which still pass byte-identically.

**Movement-level lanes stay OPEN on #73** (turn-lane coverage still 16%; the
refusal to invent geometry stands).

**What this deliberately does not do:** no arm ran; the pre-repair report card
(§9.64) remains the latest measurement; nothing is a finding about the light
rail. The 4.6.9 arm — now an F6 arm on the activated inputs — still requires
its own fresh stated-cost approval (~65–67 h at 25%×1000), and
`E.replication.n_replications` and the warm-restart validity ruling remain
open.

---

## §9.78 — The runless lanes closed out: score-distinct PT submodes (Tier C), seven 0b source upgrades incl. the CWANZ-cited bike availability, the corridor-composition answer, the demographic sex-structure finding, the empty TIA sweep, the stall capture armed (25 Aug 2026, sixth session; issues #49, #50, #63, #66, #78-record)

**Tier C — the PT submodes are SCORE-DISTINCT (#49), verified against the
pinned jar's own bytecode.** SwissRailRaptor (confirmed the default and only
transit router in 2027.0-2026w25) supports `useModeMappingForPassengers` +
`modeMapping` parametersets (`routeMode` → `passengerMode`); router pricing
reads a per-mode marginal utility from `scoring.modeParams`, so the mapping
makes route choice itself respond to the per-submode constants C1 has
declared since P4 opened (asc_bus −1.05, asc_lr −0.75, asc_rail −0.65 — the
§9.3 `not_representable` loss, now representable). Landed behind the declared
switch `RUN.routing.pt_submode_scoring` (categorical
`per_submode`/`aggregate`, default `per_submode`): the emitter writes the
raptor module and one modeParams per scheduled submode;
`RUN.transit.transit_modes` carries the submodes (the QSim serves a departure
only for a declared transit mode); `split_schedule` REFUSES a route
transportMode outside the declared vocabulary (an unmapped mode's passenger
mode is a silent null in the jar). **Two jar-measured traps pre-empted**: the
stock `AnalysisMainModeIdentifier` THROWS on a bus+rail interchange trip
(133 such trips in the probe alone) — a new `PtSubmodeMainModeIdentifier`
folds submode legs back to `pt` for trip labelling, so the HTS aggregate and
every existing pt comparison hold unchanged; and the raptor config group must
be registered at config load (the §9.76 unmaterialised-module refusal).
Probe-verified (S2 1%×2, rc=0): PersonDeparture legs bus 1,414 / rail 450 /
tram 10 / ferry 3 and ZERO `pt` legs — the umbrella is gone at leg level —
while every trip's main_mode stays `pt` and conservation closes per submode.
**Stated limits**: C1 declares no ferry constant (ferry keeps the aggregate's
−1.05, stated in the report) and one beta_ivt (submodes differ in constants
only). Plan-level SubtourModeChoice still offers `pt`; the submodes are
route-choice alternatives, which is what the jar supports.

**One more probe-caught defect (the S3 scenario probe, not the toy):** under
`priorityGroupId=corridor` the 8 mid-block crossing systems carry ONLY the
corridor group, so `longestCompetingGreen` was null and the compensation
ledger threw on the null key (rc=1 at 29 s). Guarded: with no competing stage
the extension eats the unmodelled pedestrian interruption within the same
budget and owes nobody. The S3 1%×2 probe then completes with all 14
`CitysimTramPriority` controllers instantiated — the bus-priority path is
verified in the scenario, not only in the toy.

**0b source upgrades (#63, seven fields; conservative by instruction, every
non-move recorded in the session log of the change):**
`A.signals.min_green_s` → literature (TfNSW TTD 2018/002, the dossier's own
table); `A.signals.scats_match_radius_m`, `A.crossings.link_match_radius_m`,
`A.osm.harvest_tile_deg`, `A.corridor.dedupe_tolerance_m`,
`A.corridor.nearest_node_max_rings` → definition (join tolerances and search
bounds whose outputs are invariant or refusal-guarded — each keeps its
held-fixed caution); and **`B.population.bike_available_rate` assumed 0.5 →
literature 0.493** — CWANZ *Walking & Cycling Participation Survey, NSW
Report 2025* (Painted Dog Research, NSW n=700, p.72: 49.3% total bicycle
ownership; 46.6% of households ≥1 working traditional bicycle 2025, 53.1%
2023 reweighted), sweep [0.3, 1.0] retained, the ownership→per-person
transfer stated as the step that stays assumed. **The B plans were
regenerated on the cited value in the same change** (all three day types;
weekday 620,553 persons / 2,343,321 legs) — inside F6, which has no arms, so
no boundary is created. The `C.scoring.activity_typical_duration_s` ↔
`B.activity.act_duration_min` derived-identity candidate was checked and
REFUSED: different vocabularies, different consumers, values disagree where
comparable (work 480 vs 465 min) — independent quantities.

**The corridor-composition question has its answer (the §9.64 lane), measured
on arm A (closed F4 family, pre-repair — a diagnostic, not a result):
COVERAGE carries the bus-over-tram composition; the transfer penalty prices
it; frequency is exonerated.** Of 2,140 realised PT trips touching the tram's
own 300 m walk band, only 36 (1.7%) have BOTH ends inside it — the 6-stop,
2.5 km alignment structurally requires an interchange for 98.3% of corridor
demand while 485 parallel bus patterns run through (74.6% of corridor bus
trips are one-seat rides). Within sight of the platforms boardings run 10.8
bus : 1 tram. Tram users paid 61.1 min door-to-door vs 52.3 for corridor bus
at EQUAL in-vehicle time — the gap is wait plus the extra boarding, priced at
`utilityOfLineSwitch` −2.2614 (≈12 min in-vehicle). Tram headway (11.4
min/direction) is denser than almost any single bus route — the bus
advantage is aggregate coverage, not line frequency. Full tables:
`docs/audit/CORRIDOR_PT_COMPOSITION.md`; re-measures on the first F6 arm.

**The demographic measurement (#50) is on the record** (`docs/audit/
DEMOGRAPHIC_MODES.md`): the held data carries exactly ONE demographic mode
observation (G62 JTW mode × sex; NO mode × age cell exists anywhere in the
package), and against it the modelled split is nearly SEX-INVARIANT (M/F
≤0.5 pp apart on every mode) while the observation has real sex structure
(bus F ≈2× M, motorbike M ≈10× F, passenger F ≈1.5× M — the COVID-robust
part of G62). The mechanism decision is deliberately deferred to the first
F6 arm's re-measure; new observables stay constraints, never targets.

**The systematic TIA sweep came back EMPTY — recorded so nobody repeats it
blind** (the §9.76 standing lane on #78's record): PPSHCC-306 resolved (the
per-document-timestamp blocker solved via the case page's server-rendered
listing) and scanned — no SCATS content, and a dossier correction rides
along (it is the s8.2 review of East End Stages 3–4 at 105–121 Hunter St,
not the 643 Hunter St site); 19 applications examined, 13 documents scanned;
the portal's own search confirms PPSHCC-137 remains the ONLY SCATS
Interpreted History for Newcastle today. Nothing archived because nothing
qualifies; watch items (700 Hunter St SSD EIS, DA2025/00512) in
`design/signalling/tia-harvest-log.md`. `A.signals.scats_phasing` STAYS
`unobtained`.

**The #66 settlement condition is mechanised**: the progress-digest observer
captures Defender + Task Scheduler event history on the transition INTO a
stall, over exactly the window since its own last healthy observation — the
next arm that hits the ~10:00 pattern attributes itself.

**What this deliberately does not do**: no arm ran; nothing is a result; the
F6 arm approval, `E.replication.n_replications` and the warm-restart ruling
remain open; the 67/143 split is untouched.

---

## 9.79 The documents drifted away from the artefacts, and nothing was checking (25 August 2026, seventh session; issue #82)

**Decision:** a number written into a living document is a claim about an
artefact and is now checked mechanically, exactly as a number written into a
script already was. Taken 25 August 2026, by directive, after an `/onboard`
gap scan found the front-door `README.md` three phases out of date.

### What was wrong

`check_hardcoding.py` has refused a value decided in a script since P4. Nothing
made the equivalent refusal of a value decided in PROSE, and the prose had been
quietly rotting:

| document | stated | artefact | wrong since |
|---|---:|---:|---|
| `README.md` files in the manifest | 376 | **489** | the 16 Aug rebuild |
| `README.md` synthetic agents | 612,680 | **612,687** | the age-structure repair |
| `README.md` road network edges | 43,112 | **50,182** | the #32 re-harvest |
| `README.md` active network edges | 35,653 | **40,195** | the #32 re-harvest |
| `README.md` registry fields | 210 | **356** | many entries |
| `STATUS.md` deliverable 2 files | 376 | **489** | the 16 Aug rebuild |
| `STATUS.md` synthetic agents | 612,680 | **612,687** | disagreed with its OWN P3 row |
| `STATUS.md` road / active edges | 43,112 / 35,653 | **50,182 / 40,195** | the #32 re-harvest |
| `.claude/CLAUDE.md` hardcoding ledger | 95 | **0** | the ledger reached 0 |

Two statements were false rather than merely stale: `README.md` warned that
`networks/osm/` was empty and `check_package.py` could not pass - nine days
after the re-harvest filled it and #32 closed - and `STATUS.md`'s deliverable 2
described 10 OSM layers as "pending the #32 re-harvest" while its own P1 phase
row recorded that re-harvest as done. A new reader was being told the package
was broken.

**The mechanism is duplication.** `README.md` and `STATUS.md` carried the SAME
figures table. One home was updated at the rebuild and the other was not, and
nothing could see the divergence. The `/onboard` and `/handoff` skills had
likewise each grown their own copy of the six state-of-the-project questions.

### What changed

- **`tests/check_doc_currency.py`** - a portable harness that pins each
  live-state figure to the artefact that decides it and fails when they
  disagree. `--strict` exits 1 and **gates CI**. Truths are derived from
  `MANIFEST.csv` and the registry, both committed, so it needs no bulk data:
  a claim whose artefact is absent is SKIPPED, the way `check_manifest.py`
  already treats gitignored rows.
- **`cities/<city>/tests/doc_currency.json`** - the city-owned claims (22 for
  Newcastle). The harness names no city, no document and no number; a second
  city supplies its own. Same split as `check_package.py` and
  `package_expectations.json` (#62 B4).
- **A second claim kind, `absent`** - a regex that must NOT appear, for a
  statement that was true once and is now false in a way no number would catch.
  Both stale warnings above are pinned this way.
- Every figure in the table above corrected; the two false statements replaced.
- **`docs/HANDOVER_CONTRACT.md`** - the six questions, the trust order, the
  environment gate and the expiry rule, defined ONCE and read by both skills,
  which now reference it instead of each carrying a copy.
- `src/calibrate/report.py`'s counts rationale corrected - see below.

### The distinction the check is built on

**A dated record is FROZEN; a live-state cell must equal its artefact today.**
Section 14 saying "manifest 436" on 24 August is history and must never be
rewritten to keep a check green - that would be the reproducibility rule running
backwards. Only live-state cells in `README.md` and `STATUS.md` are pinned.
`NEXT_AGENT_BRIEF.md` is deliberately exempt: `/handoff` rewrites it wholesale
every session, so pinned patterns there would break by design and train readers
to ignore the check.

### A stale attribution found while checking, and filed rather than fixed

The calibration report justified leaving traffic counts unfitted with 9.14/9.15
- *the external tier carries no boundary through traffic*. **9.41 built that
through tier** on 15 August, and **9.64 re-measured the counts and they did not
move** (-91.8% against `bind1000_25pct`'s -91.05%), yet still attributed them to
"the recorded no-through-demand structure". The generator's prose now states the
supersession; the residual - -91.8% across 30 stations, 6 of them carrying no
modelled traffic at all - is **unexplained and owned by issue #82**.

**What this deliberately does not do**: no model or data value changed; no run
was launched; no target moved; the 67/143 split is untouched; the counts are NOT
fitted and remain a reported constraint, never a target; nothing here is a
result.

---

## 9.80 The front door shows the model's fit, a dead run says why it died, and two documents stop duplicating the record (25 August 2026, eighth session; issue #84)

`README.md` described the package — 489 files, 50,182 edges, 356 fields — and
said nothing whatever about whether the model reproduces the city it models. A
reader could not learn, without opening an audit document, that the base arm puts
vehicle passengers at 0.09% against an observed 20.60%. It also described the
corridor's traffic signals only as an input that could not be obtained, nine days
after §9.77 made signal control **mechanical** in every assembled run-input set.
Both are the same defect: the front door was a description of inputs, and the
project had moved on to measurement.

**The figures are generated, not written.** New
`src/analyse/build_fit_figures.py` draws three panels — scored mode share, the
trip-length constraint against its observed range, and the 30 traffic counts on
log axes against the line of perfect agreement — as SVG, in a light and a dark
variant, with no plotting dependency and no wall-clock stamp. Four properties
were chosen deliberately:

- **It draws the calibrated base's own run.** Not the newest directory (usually a
  two-iteration probe, never a result), and not a hand-named tag:
  `params/C5_calibration.json`'s `best_tag` selects it, so the figures and
  `docs/audit/CALIBRATION_REPORT.md` always describe the same arm and both follow
  the base forward when a new one is calibrated.
- **No wall-clock, anywhere.** A figure that restamps itself on every
  regeneration churns the diff and cannot be checked; the provenance is the run,
  and the run does not move. `--check` therefore proves the committed figures
  still describe the run they name, and `check_package.py` runs it.
- **Hand-written SVG rather than a plotting library.** matplotlib is present on
  this machine but is not in the declared dependency set, and its SVG output is
  not byte-stable across versions — which would make `--check` a source of false
  failures rather than a gate.
- **It refuses to draw what the fit refused to score** — below.

**THE CORRECTION: the light rail's boardings were being reported as a −63%
error against a target the model's own fit declines to score.** `fit.py` marks
V001/V002 (3,417 boardings/day) *unscorable* and states the reason: March 2019 –
February 2020 is a pre-pandemic PT market, PT mode share roughly halved before
the 2026 base year (§12.1), and V002 is V001 ÷ 30.4 rather than an independent
datum. The modelled 1,260 is a **level**; the gap between it and that observation
is not a fit statistic. The framing had propagated into
`docs/audit/CORRIDOR_PT_COMPOSITION.md` and through three consecutive handover
briefs, and it is the same class of error §9.79 corrected in
`src/calibrate/report.py`: a comparison whose stated justification the record had
already withdrawn. Corrected in the audit document, banned in the generator
(unscored observations are recorded as context, with their reason, in
`FIGURES.json`), and written into both session skills and the handover contract.
**No target moved and the split is untouched** — what changed is what may be said
about a number, never the number. Filed as **#84** so the same claim can be
hunted wherever else it survives.

**The calibration report was silent on patronage, and the silence is part of how
this happened.** It reported only what scored, which is correct as far as it
goes, but it left the study's most policy-relevant number unmentioned - so the
number was quoted from elsewhere, wrongly. `report.py` now carries a patronage
section that states the modelled level and tabulates every patronage-family
observation in the calibration half with the reason it identifies nothing,
including the bus and share rows, which are algebraically the same datum. It
still scores nothing: deliverable 3 asks for honest reporting of where fit is
poor, and "there is no target for the headline number" is exactly that.

**A dead run now says why it died.** `_meta.json` recorded `status: failed`,
`rc: 1` and nothing else, so the reason survived only in whoever was watching:
three failed 25 August probes reached the next session as directories that could
not explain themselves, their causes present only as narrative in §9.77. New
`src/run/run_failure.py` reads the **terminating exception out of the run's own
`matsim.log`** — the last `Exception in thread`, its `Caused by` chain, and the
line it was read from — so the cause is evidence rather than recollection, and a
log that says nothing yields a cause that says the log said nothing. The meta
contract now **requires** `cause` on `failed` and `aborted` (schema condition plus
a semantic rule in `outputs.py`, because jsonschema is optional); `mark_dead`
writes it on every death path, with the caller's knowledge as the headline where
it has some (an interrupt, a reconciled dead harness) and the log's last word
beside it. All fourteen dead runs were backfilled **from their own logs**, and
the three the parser recovered match the narrative independently: the
unmaterialised `tramPriority` config group, the crossings XML's element-order
violation, and the S3 mid-block null-payee NPE. `results/INDEX.md` prints every
cause. Their §9.66 backfill notes are untouched.

**The currency check can now see decimals and strings.** `check_doc_currency.py`
compared integers only, so a fit statistic written as `10.65 pp` and the run id a
figure claims to draw were both structurally exempt — and a stale *name* is
exactly as wrong as a stale count. A claim may now declare `decimals`, and a new
`text` kind compares a captured string against one from an artefact. Ten new
claims pin the README's results section, including the run directory and its
comparability family. Verified to exit 1 on an injected regression of each kind.

**The stale-statement ban was too narrow to catch its own case.** §9.79 banned
the wording *"layers pending the #32 re-harvest"*; the same false claim survived
in `STATUS.md`'s resume instructions as *"It cannot pass until the harvest above
is re-run"*, and was found by hand on 25 August — which is the work the check
exists to abolish. The two bans are now one pattern covering every phrasing of
"the package is not built yet".

**`P4_CHECKPOINT.md` is retired as a live document and frozen as the 12 August
record it always was.** It duplicated the phase board and the deliverable
checklist that are `STATUS.md`'s job, and thirteen days later six of its
deliverables, twelve of its issues, its manifest count (364), its registry count
(171), its whole mode-share table, its relaxation verdict, its counts residual,
its walk ratio, its SUMO scope and its branch line were all superseded. Every
fact in it that is still true is recorded in `DECISIONS.md` — the machine and the
absent GPU path (§9.5), the visual-only Overpass layers, `consumers` being a read
log, `modestats.csv` versus `_metrics.json` — so **nothing needed migrating**.
The body is preserved unedited; a header states that it is an archive, lists what
superseded what, and points at the live sources. `STATUS.md` no longer sends
readers to it. This is the §9.79 mechanism observed a second time: **a document
that restates another document's job will drift, and refreshing it only resets
the clock.** Both session skills now carry the rule — find the duplicate, migrate
what is unique, freeze the rest.

`docs/README.md` carried the same class of drift: it named five output schemas
against seven, two `tests/` checks against four, and a Java tree that had since
split in two. Corrected. `.claude/CLAUDE.md` said the record holds *four*
premise corrections; §9.74 is the fifth.

**What this deliberately does not do**: no model or data value changed; no
registry field was added or moved; no run was launched; no target moved; the
67/143 split is untouched; the traffic counts remain a reported constraint and
are still not fitted; the figures are a pre-calibration diagnostic of a CLOSED
family's arm and nothing here is a result.

---

## 9.85 The joint binding does not survive translation, and the pair is re-found with the clock the model itself moves (28 August 2026, twelfth session; issues #48, #86, #49, #50)

The session's `/goal` restated the gate loop — read every 100 iterations, stop
any mode heading past 20% deviation, fix the cause from the root, no
workarounds and no biasing — and the F9 gate-2 arm
(`20260828T111708_1000it_25pct`) reached iteration 100 while this session was
opening. **The gate fired on all five scored categories** and the arm was
stopped.

### The gate reading

Linked main-mode trips, Newcastle LGA residents, from `100.trips.csv.gz`
through `fit.py`'s own `score_mode_share` (§9.83's basis, not `modestats`):

| survey category | modelled | observed | deviation |
|---|---:|---:|---:|
| Other (`bike+taxi`) | 18.28 | 3.20 | **+471.2%** |
| Public transport (`pt`) | 8.49 | 3.80 | **+123.4%** |
| Vehicle driver (`car+motorbike`) | 47.57 | 59.00 | **−19.4%** |
| Vehicle passenger (`ride`) | 4.87 | 20.60 | **−76.3%** |
| Walk only (`walk`) | 20.79 | 13.40 | **+55.2%** |
| **mean abs error, pp** | | | **10.864** |

Per mode individually: car 47.41, walk 20.79, bike 9.79, taxi 8.49, pt 8.49,
ride 4.87, motorbike 0.16, truck 0.00 (freight is not an LGA resident).

**The gate-1 repair was inert.** Against `aborted_20260827T181709` at the same
depth the driver-side pass of §9.84 moved the mean absolute error 10.920 →
10.864 and ride 4.91 → 4.87 — 0.056 pp, and ride marginally *worse*. That
inertness is the evidence that located the cause.

### The cause: the binding is generated, then discarded at translation

`ride` is not decaying because agents dislike it. **The seeded demand is
right**: `modestats` at iteration 0 carries ride 0.1903 against an observed
0.206. It decays to 0.1250 by iteration 100 because the pairing that has to
realise it keeps failing — `pair_rate` 0.556 → 0.362,
`occupancy_from_pairings` 0.3097 → 0.0956 against a **measured** 0.3503.

All three B2 binding tables name the driver — `B2_joint_bindings` 70,964 rows,
`B2_escort_bindings` 109,971, `B2_lift_bindings` 45,602. **`build_matsim_plans.py`
read that identity to decide SEEDING and then dropped it**, so nothing in the
MATSim population recorded that two people were ever a pair.
`RidePairingEngine` therefore had to re-discover each pair from geometry plus
`B.ride.pairing_window_min` (15 min) — and MATSim's own `TimeAllocationMutator`
moves the two members independently, at a **±1800 s default that no registry
field declared and no sweep covered**.

Measured on the stopped arm at iteration 100, per binding table:

| binding | ride legs | declared driver on the SAME OD by car | gap median | gap p90 | inside the 15-min window |
|---|---:|---:|---:|---:|---:|
| joint | 28,709 | 73.8% | 10.3 min | 45.1 min | **60.6%** |
| escort | 26,410 | 67.4% | 23.1 min | 429.4 min | **42.6%** |
| lift | 7,746 | 80.5% | 7.1 min | 76.3 min | **64.5%** |

Across the joint table, 94.3% of companions still holding a `ride` leg had
their declared driver on `car` *somewhere*, and 90.6% of same-OD declared
drivers were on `car` for that very trip. **The driver is present, driving,
making the same trip — and refused because the clock moved further than the
tolerance.** This is also why both earlier repairs were inert: §9.82's
passenger side and §9.84's driver side both re-identify through the same
15-minute window the drift has already exceeded.

### What was built (family F10)

1. **The identity survives translation.** `build_matsim_plans.py` writes
   `boundDriver` on every passenger any binding table names a driver for —
   158,898 persons. Carrying only the joint table would have covered 46% of
   the affected legs and left escort, the worst-hit, still on the clock.
   No value is invented: this is information B2 already holds.
2. **`RUN.replanning.time_mutation_range_s` is DECLARED** (1800 s, swept
   [600, 1800], `timeAllocationMutator.mutationRange`, the group name verified
   against `pt2matsim-26.6-shaded.jar`). It was reaching the mobsim as a
   framework default — the undeclared modelling choice this registry exists to
   prevent — and it is measured to be load-bearing on a quantity that is not
   its own.
3. **`B.ride.bound_pairing_window_min` is DERIVED from it**, by the identity
   `bound_pairing_window_min = time_mutation_range_s / 60`. It relaxes
   IDENTIFICATION only, for a pair the demand declares; `B.ride.pairing_window_min`
   stays 15 min and still governs every pairing the engine must INFER.
   Endpoints, vehicle capacity and physical boarding decide as before, and the
   gap becomes waiting time the passenger pays for in score — so an
   implausible pairing is refused by the scoring, not by a threshold. Setting
   it equal to `pairing_window_min` recovers the pre-9.85 behaviour exactly,
   and the config group REFUSES a bound window narrower than the inferred one:
   a binding may not be a way to buy pairings.

**A defect caught before it could report a false success.** The first build
booked a declared pair on the wider window while `JointRideEngine` still
bounded the passenger's *physical* wait by `windowMinutes`, so every pairing
the binding recovered would have timed out at the meeting point — the pair
rate would have risen while no additional passenger boarded, the trap-6/7
class this repository has already been caught by twice. `Booking` now carries
the tolerance it was made under. The probe that was running on the incomplete
build was stopped and closed out with that as its cause;
`aborted_20260828T203411` is the same session's earlier failure, a run that
loaded the previously installed classes because the build had been compiled to
a scratch directory (trap 9) and never installed.

**The mechanism is inert where there is nothing to rescue**, which is what
makes its effect measurable rather than assumed: two new telemetry columns,
`paired_declared` and `paired_by_identity`, report how many pairings used a
declared driver and how many of those the inference window alone would have
refused. At **iteration 0, before any drift has occurred, `paired_by_identity`
is 7** of 62,359 pairings — the mechanism does nothing until the mutator has
moved somebody.

### Found and NOT fixed: taxi is routed physically and simulated as a ghost (#88)

`taxi` is in `RUN.routing.network_modes` but **not** in `RUN.qsim.main_mode`,
so it is routed on the network and then handed to the teleportation engine:
at iteration 100, **39,892 of 39,923 taxi legs (99.9%) produced a teleport
arrival and none entered a link**, against car / bike / truck / motorbike
which entered on every departure. The declared taxi `vehicleType` — length
7.5 m, PCE 1.0 — is never instantiated, and every road link already permits
`taxi`. `RUN.qsim.main_mode`'s description justifies each inclusion and
explains `ride`'s exclusion but does not mention taxi; §9.77 added taxi to
the two RUN vocabularies and `city.json` and appears to have missed this one.

**What is NOT claimed.** The teleport is not a scoring hole: the leg carries
the router's congested time and its route distance (median 13,343 m), so the
IPART per-km rate and the `FareChargeHandler` flagfall are both scored. This
is a physical-fidelity and road-capacity defect — ~40,000 vehicle-trips per
iteration at PCE 1.0 missing from the network — not the cause of the `Other`
excess, and it must not be offered as one. Filed as **#88** and deliberately
left out of F10: it is a network-loading boundary, and folding it in would
have made the pairing repair's effect unattributable.

### Family F10

The population gains an attribute and the pairing gains an identity; the
mutation range becomes declared. All activate as ONE boundary — family
**F10** — and nothing run on the regenerated population compares to F9.
Registry 370 → **372**, ledger 0, doc-currency 0.

**Nothing here is a result.** No arm has run to a gate on this boundary, no
`_run.json` exists in F10, no target moved, no threshold was invented, the
67/143 holdout split is untouched, and the effect of the repair is **not yet
measured** — the numbers above are the DIAGNOSIS, taken from the stopped F9
arm.

---

## 10. Scenario construction (E1)

All ten scenarios derive from `schedules/base2026.zip` by explicit transformation,
so the "identical land use, population, parameters, non-CBD bus network"
requirement of §4.3 holds by construction rather than by discipline.

Resulting trunk run times (weekday, end-to-end):

| Scenario | Trunk | Run time | Δ vs S2 |
|---|---|---:|---:|
| S0 heavy rail to Newcastle | heavy rail | — (254 trips extended) | — |
| S1 bus shuttle from Wickham | bus | 10.83 min | −9.8% |
| **S2 light rail as built** | light rail | **12.00 min** | — |
| S2a charging dwell removed | light rail | 10.33 min | **−13.9%** |
| S2b full TSP | light rail | 7.45 min | **−37.9%** |
| S2c Option A alignment | light rail | 9.70 min | −19.2% |
| S3 bus rapid transit | BRT | 7.08 min | −41.0% |
| S4 extended to Broadmeadow | light rail | 18.08 min | +50.7% |
| S5 extended to John Hunter | light rail | 26.35 min | +119.6% |
| S6 no trunk mode | none | — | — |

Assumed in these constructions:

- **S2b** removes 75% of tram signal delay. Assumed; the realistic range is
  50–90% and should be swept.
- **S2c** assumes the reserved former-railway alignment permits 60 km/h and
  removes 60% of at-grade signal conflict.
- **S3** BRT: 40 km/h, 12 s dwell, no charging, 7.5 min headway, same six stops
  and the **same lane take as the tram** — so the road-space externality is not
  quietly removed when comparing S2 to S3.
- **S4/S5 extension stop siting** (Hamilton, Broadmeadow, Lambton, John Hunter
  Hospital) is assumed from the 2020 Strategic Business Case and 2025 Future
  Transit Corridor work, not surveyed.
- **S0/S1/S2c/S6** use `net_base2026_hunter_st_full_capacity`: 2 lanes per
  direction on Hunter/Scott, kerbside parking retained, no banned turns,
  100 s cycle. This is what makes B3 testable — a scenario without a tram must
  get its road space back.

---

## 11. Era variants (A3)

| Era | Source | Status |
|---|---|---|
| pre-Dec 2014 | **Reconstructed** | Archive begins Aug 2016. Built by restoring Wickham, Civic and Newcastle stations onto the 219 services terminating at Hamilton in the Aug-2016 feed, at 60 km/h with 30 s station dwell. **Frequency and stopping pattern are 2016, not 2014.** Must be validated against a 2014 public timetable before use in any published figure. |
| 2015 – Jul 2017 | `complete_gtfs` 29 Aug 2016 | Real feed. 112 routes, 4,991 stops. |
| Jul 2017 – Feb 2019 | `NISC001` 19 Oct 2018 + trains | Real feed. Franchise start captured exactly (NISC001 archive begins 18 Jun 2017). |
| post-Feb 2019 | `NISC001` Mar 2019 + `lightrail-newcastle` Feb 2020 | Real feeds. Light rail feed epoch is Feb 2020 — the earliest archived — so it post-dates opening by a year. |
| base 2026 | Aug 2026 feeds | Real. |

Each era feed is normalised to a common WEEKDAY / SAT / SUN calendar by
selecting the representative service day with the most active services within
each source feed's own validity window. This makes eras directly comparable and
is a **modelling choice**, not a property of the source data.

Trip ids are namespaced by day type (`WEEKDAY.<trip_id>`). A trip that runs on
several day types carries one id in the source feed, so merging the three
slices without namespacing emitted that trip's `stop_times` two or three times
under a single id — silently inflating service on every multi-day trip. The
integrity check in `tests/check_package.py` asserts `stop_sequence` uniqueness
within every trip precisely to catch this class of error.

---

## 12. Validation design

210 targets, **67 calibration / 143 holdout**. The split is fixed here, before
any scenario is run, per §9.

- **Calibration:** aggregate light rail and bus patronage, HTS mode share,
  traffic counts at permanent stations, light rail card-type mix, scheduled
  run time, alignment length.
- **Holdout:** stop-level light rail tap-on shares (6), station entries and
  exits (52), traffic counts at sample stations (~108).

Headline calibration anchors:

| Target | Value | Period |
|---|---:|---|
| Light rail boardings | 3,417 /day | Mar 2019 – Feb 2020 |
| Light rail share of local PT boardings | 20.8% | Mar 2019 – Feb 2020 |
| Newcastle LGA PT mode share | 7.3% | 2018/19 |
| Newcastle LGA PT mode share | 3.8% | 2024/25 |
| Scheduled run time | 12.00 min | 2026 |
| Alignment length | 2,729 m | 2026 |

**Note on the 20.8% figure.** It is light rail ÷ (light rail + NISC 1 bus)
*boardings*, which is **not** hypothesis A1's metric. A1 asks for light rail
person-legs ÷ *total* PT person-legs across Greater Newcastle, whose denominator
also includes heavy rail and regional buses and whose numerator is legs, not
taps. The observed 20.8% is an upper bound on A1 and must not be quoted as if it
were A1. The model produces the A1 metric properly.

**Note on the pandemic.** PT mode share roughly halved between 2018/19 and
2024/25 (7.3% → 3.8%). A 2026 base year therefore calibrates to a
pandemic-suppressed PT market. Because all scenarios share that demand, the
*comparison* between scenarios remains valid; the *absolute* patronage levels do
not transfer to a pre-2020 world. Every headline should state which it is.

### 12.1 What the 67 calibration targets can actually constrain (P4 stage 0)

The split is 67/143 and stays 67/143. But 67 targets is not 67 pieces of
information, and P4 has to say so before fitting anything to them.

| Block | n | What it can identify |
|---|---:|---|
| `road_aadt` | 34 | Car demand and assignment — **once the values are repaired, see below** |
| `lr_cardtype_share` | 13 | **Nothing.** MATSim has no fare-product dimension, and 31.7% of the mix is `CTP` — contactless payment, an instrument rather than a person attribute, so it is not even decomposable into age bands. Three of the 13 are 0.0 or 0.01 |
| `hts_mode_share` | 12 | Two mutually incompatible vintages: 2018/19 uses `Bus`/`Train`/`Vehicle Driver`, 2024/25 uses `Public transport`/`Vehicle driver`. The base year is 2026, so only the **2024/25 six** apply; `Walk linked` is structurally 0.0 and the remainder sum to 100, leaving **4 free degrees of freedom** |
| `lr_boardings_*` | 3 | V001 and V002 are the **same datum** (3,417/day = 103,892 ÷ 30.4). Both are Mar 2019 – Feb 2020, the pre-pandemic market. Only **V003** (83,753/month, 2025-07 onward) belongs to a 2026 base |
| `bus_boardings_monthly_mean` | 1 | 2019 only. There is **no contemporary bus target** in the pre-registered set, though the package holds the NISC 1 series to Jun 2026 (222,616/month). **Deliberately not added** — see §12.4 |
| `lr_share_of_local_pt_boardings` | 1 | **Nothing new** — it is algebraically V001 ÷ (V001 + V023). This is the 20.8% figure, and it is *not* hypothesis A1's metric (see the note above) |
| `lr_scheduled_runtime` | 2 | Two identical duplicates of a **schedule input**. MATSim runs transit on the schedule, so it reproduces 12.00 min by construction. This is a SUMO corridor target, not a MATSim one |
| `lr_alignment_length` | 1 | Geometry, already satisfied by the network build |

**Effective independent information: about 4 mode-share degrees of freedom, one
contemporary light rail patronage level, and 34 traffic counts.** Any fit
statistic P4 reports must name the targets it was computed over, because "fits
67 targets" would be a much stronger claim than the data supports.

**The mode-share targets are Newcastle LGA; the model is five LGAs.** The fit
has to be computed over trips made by Newcastle-LGA residents, not over the whole
synthetic population. `build_matsim_plans.py` positioned its seed against a
*five-LGA* HTS aggregate (car 57.46 / ride 21.46 / walk 16.14 / pt 3.39), which
is a different quantity from the target (59.0 / 20.6 / 13.4 / 3.8).

### 12.2 The `road_aadt` target values are the mean of incompatible periods

`build_validation_targets.py` filters the RMS counts on classification and
direction but **never on `period`**, then takes the station mean. Each target is
therefore the average of `ALL DAYS`, `AM PEAK`, `OFF PEAK`, `PM PEAK`,
`WEEKDAYS`, `WEEKENDS` and — where present — `PUBLIC HOLIDAYS`: daily totals
averaged together with peak-period counts. It is not a quantity with a physical
meaning.

Station 55710, 2021: true `ALL DAYS` = **50,133** veh/day; recorded target
**33,114**. Across all 119 stations the recorded value is **0.58–0.71×** the true
`ALL DAYS` figure (calibration mean 0.660, holdout 0.656). Because the number of
period rows varies by station it is not even a constant rescaling, so it cannot
be absorbed by a calibration constant.

The raw layer already carries the fix: the `WEEKDAYS` period is present for **all
119** stations, which is the right basis for a weekday run, and `LIGHT`/`HEAVY
VEHICLES` classification exists for 23 of them (weekday heavy share median 6.5%,
range 1.3–15.3%) — a measured handle on the freight the model does not
represent, though only **3 of the 34 calibration stations** have it, so the rest
would have to be modelled and swept.

**Repaired.** `build_validation_targets.py` now filters on `period` and uses
**`WEEKDAYS`**, two-way, all classes — published for every one of the 119
stations, and the basis that matches the day type the model runs. `ALL DAYS` is
carried alongside in `road_aadt_targets.csv` so the weekday choice stays visible
rather than baked in, and the observed `LIGHT`/`HEAVY VEHICLES` counts are
carried per station with a `heavy_share_source` of `observed` (23 stations) or
`not_classified_at_this_station` (96), so the freight the model does not
represent is never silently taken to be zero.

Effect of the repair, measured against the old file: **119 values changed and
nothing else did.** Same 210 targets, same ids, same geographies, same metrics,
**same 67/143 split** — the AADT split rule is structural (`permanent_station` →
calibration, sample station → holdout) and never depended on the value. New
values run 1.43–1.87× the old ones (median 1.64); station 55710, 2021 is now
**53,721 veh/weekday** where it was recorded as 33,114 (and its `ALL DAYS` figure
is 50,133 — a weekday is busier than the all-day average, as it should be).

`check_package.py` now asserts the split **exactly** at 67/143 rather than merely
"both non-empty", asserts that every `road_aadt` target names the period it was
measured over, and asserts the heavy-share provenance label. A target that does
not say what it is a count *of* is not a target.

### 12.2a The heavy-vehicle and unmodelled-vehicle corrections

The model carries no freight and generates no escort trips, so a modelled link
volume is not directly comparable to an observed all-classes count. The
corrections apply **at comparison time**, to the comparison and not to the model,
and are written to [`params/C3_count_comparison.json`](../params/C3_count_comparison.json)
by `build_validation_targets.py` rather than left in prose, so the sweep-range
rule can be tested rather than trusted.

| Correction | Value | Range | Basis |
|---|---|---|---|
| Heavy-vehicle share, where the station carries a classified count | the station's **own observed** share | — | 23 of 119 stations (weekday, two-way): median **0.0652**, mean 0.0776 |
| Heavy-vehicle share, where it does not | **0.0652** (median) | **0.0129–0.1529** | The observed range across those 23. Only **3 of the 34 calibration stations** are classified, so this assumed case is the usual one |
| Vehicles per person-trip by car | **1 vehicle per `car` leg, 0 per `ride` leg** | occupancy **1.2493–1.3940** | Derived, not assumed. HTS observes 1.3503 persons per vehicle (§9.8), i.e. **vehicle trips = driver trips**: passengers ride in vehicles that are already counted. So the modelled vehicle count is the `car` legs alone, and a `ride` leg correctly adds none — *provided* the modelled ride:car ratio matches the observed passenger:driver ratio, which is what §9.8 constrains it to |

The third replaces what an earlier draft of this section left as a bare 0–1
interval for "the share of ride legs whose driver is not otherwise modelled".
That framing was wrong: the HTS occupancy figure settles it. Because observed
vehicle trips *are* driver trips, teleporting `ride` is the correct treatment for
a count comparison, and the residual error is not an unknown share but the gap
between the modelled and observed passenger:driver ratio — which is measurable,
and is the thing §9.8 pins. What remains genuinely unmodelled is the **escort
trip**: B2 generates none, so a driver making a trip solely to carry someone else
is absent from both the `car` legs and the counts' explanation. That is a stated
limitation, not a fitted parameter.

Both corrections must be reported with the fit, never folded silently into a
calibrated constant.

### 12.3 The AADT holdout is a 2008–2010 snapshot

Survey years behind the traffic-count targets:

| Split | n | Years |
|---|---:|---|
| Calibration (permanent stations) | 34 | 2014×2, 2015×2, 2016×4, 2017×2, **2018×18**, 2020×3, 2021, 2024, 2025 |
| Holdout (sample stations) | 85 | **2007×2, 2008×21, 2010×62** |

Every holdout traffic count is at least fifteen years old, and they are 85 of the
143 holdout targets. The holdout remains untouched and unpeeked, but it should be
described for what it is: a 2008–2010 traffic snapshot plus stop-level Opal, not
a contemporary test set.

### 12.4 A contemporary bus target was considered and rejected

The only bus patronage target in the pre-registered set is Mar 2019 – Feb 2020
(395,539/month), i.e. pre-pandemic, while `bus_monthly_series.csv` runs to
Jun 2026 (222,616/month). Adding the current figure was considered — the timing
would have been legitimate, since nothing has been run and an amendment declared
before the first result is not goalpost-moving.

**It was not added, because it would identify nothing.** MATSim's scoring
collapses every public transport service into a single mode `pt` with a single
alternative-specific constant (§9.3 — bus, light rail and heavy rail have no
separate `modeParams`). There is therefore no parameter in the model that a bus
patronage level could pin down which the light rail level and the PT mode share
do not already pin down; a fourth PT aggregate would add a row to the fit
statistic and no information to the fit. Amending a pre-registration for that
trade is a bad bargain.

The contemporary figure will instead be reported as a **labelled post-hoc
diagnostic** alongside the calibration, clearly outside the 210. The
pre-registered set stays at 210 targets, 67/143.

If a later change gives bus and light rail distinct scoring constants — which
would require a MATSim mode-vehicle extension, not a config edit — this decision
should be revisited, because at that point the bus level *would* be identifying.

---

## 13. Outstanding data tasks, in priority order

1. **SCATS phase data** (TfNSW request) — currently the largest uncertainty in
   corridor run time; S2b shows the swing is 38%.
2. **Charging dwell field measurement** — a few hours at Civic or Crown Street
   resolves an 11% run-time term.
3. **Journey-linked Opal** (TfNSW request) — required to estimate the transfer
   penalty rather than sweep it.
4. **Manual OSM correction on the corridor** — lane counts, turn restrictions,
   kerbside. 75–98% of these fields are currently imputed; B3 depends on them.
5. **LiDAR DTM for the CBD, The Hill and Newcastle East** — replaces the GLO-30
   surface model where gradient actually matters.
6. **Pedestrian counts** — none published for Newcastle. Deploy temporary
   counters on Hunter St frontage segments (§7.2 fallback).
7. **Retail floorspace and vacancy field audit** — currently modelled from
   building footprints; vacancy is empty.
8. **2014 public timetable** — to validate the era-1 reconstruction.
9. **Event attendance data** — for the event-demand overlay (§10 item 6).
10. **GTFS-Realtime collection** — **considered and dropped (§9.23).** A collector
    was built and reverted once an Open Data Hub API key made the published
    catalogue assessable. TfNSW's own **Historical GTFS and GTFS Realtime**
    archive carries trip updates and vehicle positions but **only for Metro and
    Ferry** — verified against the live API, with Metro/Ferry returning files and
    every light rail and bus naming returning none — so it does not backfill
    Newcastle. Standing up an unbounded rolling stream is not justified until the
    published catalogue has been worked through; that assessment is §9.23.
11. **Journey-to-work origin-destination table** (ABS: SA2 usual residence ×
    SA2 place of work) — the package holds the place-of-work side (`W01A…`,
    jobs *by* SA2) but not the origin-destination pairing, which is what would
    settle `EXTERNAL_INTERACTION_RATE` (§9.2) instead of sweeping it. It is a
    standard ABS TableBuilder extract, not a formal request.
12. **A day-of-week travel split** — the HTS LGA tables have none, so the
    Saturday:Sunday division within the weekend is the last assumed part of the
    day-type shape (the weekday/weekend ratio itself is now measured from RMS
    traffic counts, §9.2).

---

## 15. The input registry — every controllable value, declared (P4)

Proposal §8.1 requires that *"every parameter chosen without direct empirical
support must be recorded with its rationale and its sweep range."* Until now that
was a discipline applied to `DECISIONS.md` prose and to `params/C1–C4`, while the
values the model actually ran on lived in **316 module-level constants across 45
scripts**, a 110-parameter MATSim config per run set, and a handful of CLI
defaults. One of those 316 carried a machine-readable `source` label. Eighteen
carried a sweep.

`config/registry/` now declares **152 fields** — every value the model consumes
that is not read from an immutable raw download — each with its units, its
provenance, and either a sweep range or an explicit rule holding it fixed.
`src/registry/` resolves them; `docs/reference/CONFIG_REFERENCE.md` is generated from them
and cannot drift; `check_package.py` tests the rules rather than trusting them.

### What the declaration buys that prose did not

| Rule | How it is now enforced |
|---|---|
| A value chosen without empirical support carries a sweep | Schema constraint: `source` of `assumed`/`literature`/`measured`/`derived` requires `sweep`, `held_fixed` or `derived_from`. There is no fourth option |
| The three unobtained inputs are never pinned (§0, §13) | They carry `value: null` and `status: unobtained`. `get()` **raises**. A caller must select a sweep member explicitly |
| The mode constants are not freely calibrated (§8.5) | `held_fixed` with the rule and what a departure requires. Any layer that tries to set one is rejected |
| A run states the inputs that produced it | The resolved snapshot is written to `_config.json` in every run directory, and `_run.json` fails its contract without one |
| Escaping a declared range is deliberate and recorded | Only a committed overlay may carry `allow_outside_sweep`, and only with a written `justification`. A shell flag cannot do it |

The one legitimate use of that escape hatch is **S2a**, which is *defined* as the
no-charging-dwell counterfactual: zero is outside the 10–35 s sweep because the
sweep is the range for a system that charges, and S2a is the case where it does
not. That is the scenario, not a parameter choice.

### Two factors that were set in code, with no rationale and no range

`run_matsim.py` set `flowCapacityFactor` and `storageCapacityFactor` to the
sample fraction. Neither string appeared anywhere in `DECISIONS.md`,
`check_package.py` or the P4 checkpoint. They are now registry fields:

- **`RUN.sample.flow_capacity_factor` is derived**, not chosen: it equals the
  sample fraction, which is the standard MATSim scaling rule. It carries a
  `derived_from` identity rather than a fabricated sweep.
- **`RUN.sample.storage_capacity_exponent` is 1.0, and it is derived, not
  chosen.** `storageCapacityFactor = fraction ** exponent`, and MATSim
  **enforces** storage == flow: `GlobalConfigGroup.checkConsistency` throws when
  the two differ by more than `global.relativeTolerance`, which defaults to 0.0.

**A correction, recorded because it was committed before it was tested.** An
earlier revision of this section declared the exponent *assumed*, swept 0.75–1.0,
and called it an open risk — the reasoning being that MATSim floors link storage
at one vehicle, so a 1% sample would produce spurious spillback, inflate car
travel times and drive agents to teleported `walk` (the discarded 250-iteration
runs showed walk at 0.38–0.55 against a 0.134 target). **That reasoning is
superseded.** The diagnostic run built to test it died in one second:

> your storageCapFactor=0.0316228 is more than the relativeTolerance=0.0
> different from the flowCapFactor=0.01. (The old approach of setting the stor
> cap fact larger than the flow cap fact is no longer needed since the qsim
> became a lot more deterministic.)

Raising storage above flow is *older MATSim practice that this version rejects*.
The declared sweep was therefore a range whose members the tool will not accept —
exactly the undisciplined declaration the registry exists to prevent, introduced
by the same change that introduced the registry. The field is now `derived` with
the identity stated, `run_matsim.py` fails in 0.1 s rather than handing MATSim an
inconsistent pair, and `check_package.py` asserts the equality instead of the
sweep.

**What survives the correction.** The question the exponent was a proxy for —
whether behaviour moves with the **sample fraction**, given that every P4
behavioural result was measured at 1% — is untouched, and is what the 1% versus
10% arms of the diagnostic test. The mechanism is no longer a candidate
explanation; the phenomenon, if there is one, still needs a cause.

### Note also the shipped configs

`scenarios/matsim/<S>/<DAY>/config.xml` still carries `flowCapacityFactor 1.0`.
Running one of those directly — as the §9.4 load test did — simulates a **sampled
demand against full supply**. The harness must be used.

### The SUMO corridor layer, migrated and verified

`build_sumo_corridor.py` now reads the registry rather than holding its own
constants — 17 fields in `config/registry/RUN_sumo.json`. The netconvert options
that are **modelling choices** are named fields rather than entries in a flag
list, so a choice cannot hide inside one:

| Field | Why it is a choice, not a flag |
|---|---|
| `RUN.sumo.lefthand` | With it off netconvert builds right-hand connections and **every turning movement on the corridor is wrong** |
| `RUN.sumo.tls_default_type` | `actuated` vs `static` stands in for the unobtained SCATS phasing — part of the 38% run-time uncertainty, not a build detail |
| `RUN.sumo.junctions_join` | Moves junction centroids, which is why the A2 match radius is 60 m rather than A2's own 45 m |
| `RUN.sumo.no_turnarounds` | Uncontrolled U-turns on a trunk corridor are a build artefact, not observed behaviour |
| `RUN.sumo.crossings_enabled` | **False because `--osm.crossings` segfaults netconvert 1.27.1** (§3.6) — a tool defect, not a judgement that pedestrians do not matter |

**The refactor is inert, and that was verified rather than asserted.** The
assembled option list is identical to the literal list it replaced, in the same
order, and `check_package.py` asserts it. The corridor was then rebuilt: all four
`corridor.net.xml` and all seven `tls_*.add.xml` are **byte-identical** to the
pre-migration build.

**Nine files did differ, and they are not the model.** The plain XML
(`corridor.{nod,edg,con,tll,typ}.xml`), the `netccfg`, two netconvert logs and
the build report. Running the build **twice more with no code change between
them** produced the same nine differences, so they are inherently
non-deterministic — netconvert stamps a wall-clock timestamp into each. This
refines a claim made at P2: *"netconvert output is byte-identical on rebuild"* is
true of **the nets and the signal programs**, and false of the intermediates.
Anything that hashes `networks/sumo/_work/` will see spurious churn.

**A determinism defect found by the gate, and fixed.** `_sumo_build_report.json`
is a **committed** artefact carrying a manifest hash, and it recorded
`netconvert_seconds` — wall-clock timing. Its digest therefore changed on every
rebuild even when the four nets were byte-identical, so a committed file could
not be regenerated to the same bytes. That is the reproducibility gate failing,
and CLAUDE.md forbids wall-clock dependence in a build script outright. Timings
now go to `networks/sumo/_work/netconvert_timings.json`, which is gitignored;
the committed report is byte-identical across consecutive rebuilds, verified by
building twice and comparing. The manifest was regenerated. The defect predates
this change and was only exposed because the migration forced a rebuild.

**A SUMO run still does not exist.** The corridor nets have been built four times
and simulated zero times. Proposal §5.1 gives SUMO the entire supply-and-operations
layer — run time, dwell, reliability variance, car delay, frontage throughput —
and §5.2 the outer loop. The fields such a run would need are declared
(`step_length_s`, `begin_h`, `end_h`, `outer_loop_max_iterations`), and two carry
no value on purpose: `RUN.sumo.replications`, because proposal §5.2 asks for at
least 30 and §9.5 shows the budget does not fit and nobody has decided what to cut
(issue #6); and `E.coupling.outer_loop_tolerance_s`, which has never been defined
(issue #8). Declaring them null means a SUMO harness cannot be built on an
unexamined default.

### What is declared but not yet consumed

**Superseded in part — see "The build layer, migrated" below.** The migration
landed, so the drift check that pinned duplicate constants is now nearly empty by
design: a migrated script reads the registry, and its duplicate constant was
deleted along with the `legacy_symbol` that pinned it. **One field remains
pinned**, one deliberately diverges. Writing that check originally found four
values transcribed wrongly into the registry; the code was authoritative and the
registry was corrected.

**Of the 152 declared fields, 66 are referenced by no code in `src/` or
`tests/`.** That is not drift and not a defect: a registry field is a
*declaration* first — units, provenance and a sweep for a value the model relies
on — and only a runtime lookup second. The 66 divide into three kinds, and the
distinction matters:

- **constraints**, which mirror a measured artefact rather than feed a script.
  `C.constraint.*` declares occupancy (§9.8) and trip length and time (§9.13);
  the values live in `params/C4_mode_constraints.json`, which is what `fit.py`
  reads, and `check_package.py` pins declaration to artefact so they cannot
  drift.
- **values consumed through an intermediate artefact** rather than by key —
  `B.counts.*` reaches `fit.py` through `params/C3_count_comparison.json`, for
  instance.
- **values genuinely not yet wired**, including the seven that carry no value at
  all and must never be pinned (§0, §13).

**A `consumers` entry is a machine-readable claim and is verified.** It asserts
that a named file reads that field, and `check_package.py` now checks the file
exists *and* references the key. An untrue claim is worse than an absent one: it
makes a value look wired into the model when nothing reads it, which is the very
drift the registry exists to prevent, asserted in the registry's own hand. Ten
fields added at §9.13 named two readers that in fact read the C4 artefact; the
check caught it, and every one of the sixty pre-existing claims was already
true.

### The build layer, migrated (P6 cleared)

`src/build/*.py` no longer hold their own copies of the values the registry
declares. 52 fields across 13 scripts now resolve from `config/registry/`, taking
runtime consumption from **16 of 140 to 68 of 140**. The migration was mechanical
— by AST, so no value was retyped — and gated by rebuilding the package in README
order and asserting byte-identical output. `build_matsim_network.py` was
**deliberately not re-run**: §3.5 forbids re-running the mapper, and the gate
instead proves the feeds it was mapped from are unchanged, which `check_package`
confirms through the stop→link fingerprints.

**The gate did its job — it caught three defects, all pre-existing.**

| Defect | Consequence |
|---|---|
| `build_landuse_parking.py` iterated an **unsorted set** to build `frontage_retail_m2_by_street` | The report was **hash-seed dependent**: three runs at different `PYTHONHASHSEED` gave three different digests. Identical data, different bytes. Same defect as the P3 stage 0 `stop_times.txt` bug, in a different file |
| Every GTFS **zip embedded the wall clock** in each entry's header | The 11 scenario and era feeds could never regenerate byte-identically, so their manifest digests were unreproducible by construction. `det_io.py` already solved this one container up, for gzip |
| `_landuse_report.json` and `_run_inputs_report.json` carried **dict-insertion order** as output order | A benign reordering changed the digest |

All three are the same failure the project has fought before, and all three were
invisible while nobody re-ran the builds. **A manifest digest only proves
reproducibility if something actually re-derives it.** The package had not been
rebuilt end to end since the manifest was written, so the gate had never fired.

Fixed: the set iteration is sorted, `det_io.zip_entry` pins every zip entry to a
fixed timestamp, and the registry key order matches the output order it feeds. The
manifest was regenerated. Two fields keep their `legacy_symbol` deliberately —
`B.activity.detour_factor` (the build keeps a labelled 1.30 fallback for when the
C2 file is absent) and `A.lightrail.dwell_charging_s` (declared unobtained; the
literal is the baseline sweep point, which lives in the scenario overlays).

### Fields whose value is null, and why that is the honest encoding

| Field | Why |
|---|---|
| `A.signals.scats_phasing` | Unobtained; TfNSW request outstanding. 38% swing in corridor run time |
| `A.lightrail.dwell_charging_s` | Unmeasured; a few hours of field observation resolves it. 11% of run time |
| `B.opal.journey_linked` | Unobtained; it is what would let the transfer penalty be estimated rather than swept |
| `D.retail.vacancy_rate` | No Newcastle frontage audit exists. Registered so hypothesis B2 cannot quietly acquire one |
| `E.coupling.outer_loop_tolerance_s` | Proposal §5.2 defers it to calibration and **it has never been defined** (issue #8) |
| `RUN.controler.last_iteration` | §9.7 shows 100 and 250 are both too low and no justified value has been measured (issue #5) |

The last two are not missing data — they are **decisions nobody has taken**.
Declaring them with a null value means the model cannot run past them silently:
`run_matsim.py` now refuses to start without an explicit iteration count, which
is the same refusal `--iterations` already implemented, moved from one script's
argument parser into the registry where it binds everything.

---

## 9.86 A hired car is a car on the road: taxi stops being a ghost in the mobsim (28 August 2026, thirteenth session; issues #88, #49, #48)

The session's `/goal` puts a precondition ahead of the gate loop: *the groundwork
must be as-is compared to real life; every mode physically simulated, monitored
and scored - no teleportation.* Issue **#88** is the one measured breach of it.

### What was wrong

`taxi` was carried correctly everywhere except the one place that decides road
space. It is in `RUN.routing.network_modes`, it is permitted on 143,891 links,
`CitysimControler` binds it to the congested car travel time and the car
disutility (so a taxi cannot out-run the traffic it rides in), its fare is
scored in two parts, and `build_matsim_run_inputs.write_mode_vehicles` already
emits a car-bodied `taxi` vehicle type. But it was **not in
`RUN.qsim.main_mode`**, and MATSim's contract is that a mode outside the main
modes is teleported no matter how carefully it was routed. Measured on the F9
gate-2 arm: **39,892 of 39,923 taxi legs per iteration** arrived by clock rather
than by carriageway.

Two consequences, and only the second is obvious:

1. **The road was under-loaded.** ~40,000 vehicle-trips an iteration - at a
   declared PCE of 1.0, the same road space as the same number of cars - were
   absent from every link, every queue and every count station. `car` measuring
   **-19.4%** against its target while `Other` (the `bike+taxi` fold) measured
   **+471.2%** was being read on a network that never carried the taxis.
2. **The taxi's own time was free of the congestion it causes.** The travel-time
   binding gives a taxi the *car's observed* link times, which is right; but a
   teleported taxi contributes nothing back to those times, so the mode was
   priced against a road it did not load.

### The change

`RUN.qsim.main_mode` gains `taxi` - one value, in the registry, where every
other physical-simulation decision is declared. Nothing else needed building:
the vehicle type, the link permissions, the travel-time binding and the fare
were all already in place and had been waiting on this one enum.

The vehicle body is **not a new declaration**. A taxi restates
`RUN.qsim.car_vehicle` exactly - 7.5 m, PCE 1.0, the declared ride seat cap -
because a hired car *is* a car, and inventing a separate taxi body would be a
modelling choice with no observation behind it.

### What is deliberately NOT claimed

**Deadheading is not modelled.** A real taxi fleet also drives empty between
fares, and that load is real. Nothing here fabricates it: what is now on the
road is the *occupied* leg, which is the leg the demand model actually produces.
The empty-running share is unobserved for Newcastle, so it stays unobserved
rather than becoming an assumed multiplier. Recorded here so the next reader
knows the boundary is deliberate.

### Measured, on the 1% two-iteration plumbing probe `20260828T220751_2it_1pct`

rc=0, accounting closes. Every link-entry event in `2.events.xml.gz` attributed
to the vehicle class that produced it:

| vehicle class | link enters | departures | vehicles entering traffic |
|---|---:|---:|---:|
| walk | 825,231 | 10,223 | 7,856 |
| car | 794,330 | 9,052 | 8,899 |
| bus (transit) | 237,057 | 1,309 | driven by transit driver |
| bike | 181,964 | 1,547 | 1,547 |
| truck | 136,897 | 907 | 907 |
| rail (transit) | 87,001 | 382 | driven by transit driver |
| **taxi** | **29,994** | **197** | **197** |
| tram (transit) | 4,145 | 15 | driven by transit driver |
| motorbike | 3,652 | 45 | 45 |
| ferry (transit) | 214 | 14 | driven by transit driver |
| **total** | **2,300,485** | | |

**Every taxi departure now enters traffic: 197 of 197.** Before this change the
same column read 0.

The same probe measures what remains teleported and why: **`ride` - 1,166 of
2,101 legs physically boarded, 935 (44.5%) teleported.** That is *not* a mobsim
defect and must not be closed by giving a passenger their own vehicle: a car
passenger is not a second car, and a phantom vehicle per unpaired passenger
would double-count road load to make a physicality statistic look better. An
unpaired `ride` leg is a **demand-side** failure - the passenger chose a mode
no driver realised - which is exactly what 9.85's `boundDriver` repair
addresses. The probe confirms that repair is live: `paired_by_identity` is 98 at
iteration 2, and `pair_rate` holds 0.5410 -> 0.5030 -> 0.5224 rather than decaying.

### The comparability boundary

This changes network loading, so nothing run before it compares to anything run
after it. Declared as family **F11** in
[`audit/run_families.json`](audit/run_families.json). F10 has no completed arm to
lose: its only launches were a 1-iteration abort and a 5-iteration plumbing
probe, both stopped on instruction.

---

## 9.87 A folded target cannot answer a per-mode question: twelve modes get twelve targets (28 August 2026, thirteenth session; issues #49, #84, #88)

The standing directive is that **every mode is checked against real life on its
own**, and that every numbers table lists each mode individually. The model
could not answer that, and neither could the record: the NSW Household Travel
Survey publishes **six categories**, and this city simulates **twelve modes**.

### What the survey actually says

Quoted from the acquired data document
(`data/raw/hts/hts_data_document_2020_2024.pdf`), not paraphrased:

> Vehicle Driver · Vehicle Passenger · **Public Transport (includes Train,
> Metro, Bus, Light Rail, Ferry)** · Walk linked · Walk only · **Other
> (includes Taxi/rideshare/carshare, wheelchair, bicycle, aircraft)**
>
> ⁴ "Other" mode category from 2020/21 is not comparable to previous waves as
> it does not include Light Rail and Ferry. These modes are now included under
> the Public Transport mode

Two things this settles that were previously taken on trust:

1. **`fit.py`'s folds are correct**, and now evidenced rather than assumed.
   `bike+taxi → Other` is the document's own list. `car+motorbike → Vehicle
   driver` follows because motorbike appears in **none** of the other five
   categories, so it can only be a vehicle driver.
2. **Four modes share ONE target.** bus, light rail, heavy rail and ferry are
   a single 3.8% Public Transport row. A fold cannot say which of the four is
   wrong, and it lets an excess in one hide behind a deficit in another —
   which is exactly what the gate loop exists to catch.

### The disaggregation, and what each piece rests on

`cities/newcastle/build/build_mode_targets.py` writes one row per mode to
`data/processed/validation/mode_targets_by_mode.csv`. Every number is an HTS
level, a count measured from an acquired artefact, or the product of the two.

| mode | target % | from |
|---|---:|---|
| car | 58.1631 | HTS Vehicle driver 59.0 × census G62 car-as-driver 157,832 of 160,103 |
| ride | 20.6000 | HTS Vehicle passenger, **read directly** |
| walk | 13.4000 | HTS Walk only, **read directly** |
| bike | 3.0131 | HTS Other 3.2 × G62 bicycle 903 of 959 |
| motorbike | 0.2406 | HTS Vehicle driver × G62 motorbike/scooter 653 of 160,103 |
| taxi | 0.1869 | HTS Other × G62 taxi/rideshare 56 of 959 |
| bus | 1.3039 | HTS Public transport 3.8 × Opal boardings 34.31% |
| heavy_rail | 2.0922 | HTS Public transport × station entries 55.06% |
| light_rail | 0.4039 | HTS Public transport × station entries 10.63% |
| ferry | **unobtained** | nothing published for this city — swept, never pinned |
| truck | 15.4698 | TfNSW classified weekday counts, heavy share of all vehicles |
| freight_train | **not simulated** | §9.70 — the modelled zero is the decision |

The person-trip targets sum to **99.4037%**, and the missing 0.596 pp is not a
rounding slip: it is the **resident truck-driving** slice of HTS Vehicle
driver (G62 truck, 1,618 of 160,103 driver journeys). This city represents road
freight as its own vehicle subpopulation rather than as a resident's person
trip, so that travel cannot appear on the person-trip denominator at all. It is
written out as a named deduction rather than folded into car, which would have
inflated the car target by 0.6 pp and made the model's car deficit look worse
than it is.

### Why the PT split is taken on boardings and not on the census

The 2021 Census was enumerated on **10 August 2021, inside the Delta lockdown**,
which suppressed public-transport commuting specifically. Its PT composition
(bus 78.5%, train 15.4%, tram 3.5%, ferry 2.7% of one-method PT journeys)
disagrees sharply with current patronage (bus 34.3%, heavy rail 55.1%, light
rail 10.6% over 2025-07..2026-06). **The disagreement is real uncertainty, not
a source to pick between**: the point value is the current boardings — actual,
current-vintage patronage — and the census figure sets the far end of each
mode's sweep. Nothing is averaged, and nothing is discarded.

### Ferry stays unobtained, and that is the honest answer

No Newcastle ferry patronage exists in any acquired artefact. The Opal
all-modes series carries a Ferry row but it is **NSW-wide and Sydney-dominated**,
so it identifies nothing here; the station entries/exits publication carries
Train and Light rail only. The one city-specific observation — the census
one-method count of 40 journeys — is lockdown-vintage. So ferry takes the same
treatment as SCATS phasing, journey-linked Opal and charging dwell (§0, §13):
**value null, status `unobtained`, swept 0 to twice the census-implied figure,
and never pinned to a point value.** The gate reading prints the ferry's
modelled level and refuses to print a deviation, because there is nothing to
deviate from.

### Three modelling choices, declared

`CAL.pt_split.window_months` (12, swept 6–24) · `CAL.mode_split.commute_transfer_tolerance`
(0.25, swept 0.1–0.5 — the half-width of the interval placed on any target that
applies a **commute** composition to an **all-purpose** level, because commuting
is not a random sample of travel) · `CAL.truck.count_year_from` (2023, swept
2019–2025). Plus the acceptance criterion itself, which was previously typed
into a script: `CAL.gate.stop_deviation_pct` (20) and
`CAL.gate.pass_deviation_pct` (10), both `definition` — they state the bar, they
do not model anything, and sweeping them would sweep the question.

### These targets are deliberately NOT added to `validation_targets.csv`

They are a **disaggregation of targets already in that file**. Scoring them
beside their own parents would count one observation twice, move the reported
MAE for a reason that is not a model change, and disturb the 67/143 split.
`fit.py` is untouched; this is a second, finer view of the same observation,
read by `src/analyse/report_mode_ridership.py`.

### A parse bug caught on the way — worth the trap list

A scratch measurement of the PT window sorted month labels (`Sep-2025`,
`Jun-2026`) as **strings**, so it read the alphabetically-last label as the
chronologically-last month and computed the split over the wrong twelve months
(bus 45.8% instead of 34.3%). The builder parses to `YYYY-MM` first and
disagreed with it, which is how the bug surfaced. **A confident number from a
throwaway script is not a measurement until something else reproduces it.**

---

## 9.88 SCATS stops being an assumed constant and becomes an algorithm (28 August 2026, thirteenth session; issue #73)

The `/goal` directive was amended mid-session to forbid the handling this
project had used for three unobtainable inputs: **an unavailable value may no
longer be left SWEPT if it can be derived**, and it named signalling as the
worked example - *if SCATS signalling is not available, exhaustively research
and implement its various algorithms.*

### What was actually wrong

`A.signals.scats_phasing` is `unobtained` with a null value, and the fallback
was a swept fixed cycle time. So every arm this project has ever run drove all
**14 corridor intersections on a fixed 110 s plan with fixed splits**
(corridor 0-56 s, cross 64-102 s, offset 0, identical at every intersection).
That is not an approximation of SCATS. A SCATS intersection re-times itself
every cycle against measured saturation, and the difference between the two
lands exactly where this study looks: corridor run time, and the queues the
light rail sits in.

The derivable thing was never the timings - it is the **algorithm** that
produces them.

### What SCATS does, and what is implemented

`citysim.ScatsSignalController` (`src/java_signals/`) implements the published
control logic on one measured primitive and two adaptations of it.

**The primitive - degree of saturation.** Measured from the mobsim, not
modelled: every vehicle crossing a signalised stop line emits a
`LinkLeaveEvent`, and

```
DS = served / (saturation flow per lane x lanes x green / 3600)
```

is what was served against what that green could have discharged at
saturation. No detector model, and nothing inferred from the plan being
evaluated.

**Adaptation 1 - cycle length.** Lengthen while the CRITICAL movement runs
above the target DS, shorten while every movement runs below, in bounded
increments rather than jumping to a computed optimum, so one noisy cycle
cannot destroy coordination. Bounded by the declared min/max **and** by the
intersection geometry: every clearance plus a minimum green per stage, a floor
that outranks the declared minimum wherever it is higher.

**Adaptation 2 - splits.** Green distributed to EQUALISE DS across stages.
Clearances are preserved exactly - they are safety geometry derived from the
intersection, not capacity to reallocate.

**Adaptation 3 - offsets: NOT implemented, deliberately.** SCATS selects
offsets from an operator-tuned per-subsystem library. That library IS the
unreleased artefact, and unlike cycle and splits there is no algorithm to fall
back on. An offset invented here would be this repository asserting a
coordination pattern nobody measured - the precise failure the exercise exists
to avoid. Each system keeps its generated offset, and corridor coordination
stays a **stated limitation** rather than a fabricated input.

### Two defects the build surfaced, both worth the record

**1. The degree of saturation was measured against full-scale capacity.** The
declared 1900 veh/h/lane is real-world, but MATSim scales every link discharge
by `qsim.flowCapacityFactor`, so a 25% run's links pass a quarter of the
vehicles per hour of green. Dividing a sampled count by a full-scale capacity
read DS **0.000 at a 1% sample**, and the first probe drove every cycle from
110 s to the floor with traffic present. The denominator now carries the factor
that is already in the physics. **A sampled mobsim is not a small city; it is a
city whose capacities were scaled, and any measurement against a real-world
rate has to scale with them.**

**2. Modular arithmetic cannot survive a variable cycle.** A fixed-time
controller finds its place with `(t - offset) mod cycle`. The moment cycle
length changes that expression silently reinterprets every past boundary and
the plan jumps. The controller keeps an EXPLICIT cycle start and length, and
re-times only at a boundary - a cycle in progress is never re-timed underneath
itself.

### Transit priority composes, and compensation becomes intrinsic

A signal system names exactly ONE controller, so an adaptive corridor that
could not grant tram priority would silently drop it. The priority layer
therefore lives inside this controller too, on the same declared
`tramPriority` parameters and the same detection service, in the same order:
SCATS decides the plan for cycle N, and a detected tram may deform THAT cycle.

One mechanism becomes unnecessary. The fixed-time controller keeps a
compensation LEDGER, repaying in cycle N+1 what a competing stage lost in cycle
N, because a fixed plan has no other route back to its declared splits. **Under
SCATS the repayment is intrinsic**: a stage that gave up green discharges the
same traffic through a shorter green, its measured DS rises, and the next
split hands the time back for that reason. No ledger is kept that could
disagree with the feedback.

### Measured

Probe `20260828T230050_2it_1pct` (1%, 2 iterations, rc=0, accounting closes):
all **14 systems re-time**; NLR_SIG_01 runs 110 -> 104 -> 98 -> 92 s against
criticalDS 0.564 -> 0.282 -> 0.141. Probe `20260828T230739_2it_1pct` on **S2b**
(rc=0) carries SCATS and `green_extension` priority together, 168 logged
re-timings across the 14 systems.

### Declared, and the guard that keeps it honest

`A.signals.control_regime` (**`scats_adaptive`**, categorical sweep against
`fixed_time`) plus six algorithm parameters, all bound into the emitted `scats`
module so the reach probe can move them:
`target_degree_saturation` 0.90 [0.80-0.98] · `cycle_step_s` 6 [3-12] ·
`min_cycle_s` 30 [20-60] · `max_cycle_s` 150 [110-180] · `ds_deadband` 0.05
[0.02-0.10] · `ds_smoothing` 0.5 [0.1-0.9]. The min/max bracket the documented
SCATS user limits (dossier 03/09); the operated corridor evidence of 9.75 (TIA
PPSHCC-137: TCS 1138 at 72-81 s, TCS 923 at 104-113 s) sits well inside them.

**`fixed_time` is kept, and reproduces every earlier arm exactly.** That is the
comparison that says what the control logic is worth.

The controller identifier is baked into the generated control file, so a
declared regime disagreeing with the committed artefact would reach NOTHING -
the run would execute the other controller and complete happily. `run_matsim.py`
now refuses that mismatch in 0.1 s and names the command that fixes it.

### Comparability

Signal control decides corridor travel time, so nothing run before this
compares to anything run after it. Declared as family **F12**.

---

## 9.89 The ferry gets a derived target instead of no target at all (28 August 2026, thirteenth session; issues #49, #84)

Under the same amended directive, ferry stops being `unobtained`.

**What does not exist:** any published Newcastle ferry patronage. The Opal
all-modes series carries a Ferry row, but it is NSW-wide and Sydney-dominated,
so it identifies nothing here; the station entries/exits publication carries
Train and Light rail only. That was the basis for 9.87 leaving the mode with
**no target at all**, which meant mode 10 of 12 could not be gated.

**What does exist:** the census G62 one-method count - **40 of 1,501** core-SA1
public-transport journeys to work, 2.665%. It sets the ferry share WITHIN
public transport, which the HTS PT level of 3.8% then scales:
**0.1013% of resident person trips.**

**Why the transfer is more defensible for this mode than for the others.** Two
reasons, both specific to this service. The Stockton crossing is **captive** -
the road alternative is a ~20 km detour via Hexham - so its riders are not
choosing it on the margin a bus rider is, and the commute-to-all-purpose
transfer distorts less. And a share WITHIN public transport is far less
sensitive to the August 2021 lockdown than an absolute level would be, because
the lockdown suppressed numerator and denominator together.

**The sweep stays wide - 0 to twice the point value.** The lockdown vintage is
real and unquantified, and a derived value is not a measured one. What changes
is that the mode now HAS a target and can be gated; what does not change is
that the number is labelled `derived`, never `observed`.

---

## 9.90 A crossing closes for every train that crosses it, and the timetable says which (28 August 2026, thirteenth session; issue #68)

The third input the amended directive reaches. `A.crossings.closures_per_day`
was **30, assumed, swept 10-60, and the same number at both sites**, spread
uniformly across 24 hours because no closure log is published. Every arm since
§9.77 has run that.

### It was derivable from data already in the package

A level crossing closes for **every train that crosses it**, and this city's
own mapped rail timetable says exactly which trains those are and when. Nothing
new had to be acquired.

`build_level_crossings.py` now finds the mapped RAIL links at each crossing
(within a held-fixed 40 m join tolerance; measured midpoint distances are
29.6 m at Saint James Road and 8.0 m at Clyde Street), counts every scheduled
service whose mapped route traverses them, and times each closure from that
service's own stop time at its nearest rail stop.

| site | assumed before | **derived** | shape |
|---|---:|---:|---|
| Saint James Road (Adamstown) | 30 | **110** | peaked: 17h carries 9, 13h and 14h carry 8 |
| Clyde Street (Islington) | 30 | **204** | peaked: 17h carries 14, 08h and 14h carry 12 |
| total change events | 541 | **3,014** | |

Two things the assumed value got wrong, and neither is a small correction:

1. **The count, by 3.7x at one site and 6.8x at the other.** The uniform member
   gave both crossings the same 30, and the two are not alike - Islington sits
   on a busier line than Adamstown.
2. **The shape, which is what actually matters.** A closure spread uniformly
   across 24 hours puts most of its closures where there is no traffic to
   delay. The derived pattern is peaked where the service is peaked, which is
   also where the road is busiest - the interaction the crossing exists to
   represent.

### What is still not derived, and is declared rather than hidden

Freight movements are **not** in a passenger timetable.
`A.crossings.freight_closures_per_day` is declared for them, and its point
value is **zero on recorded evidence**, not for want of a number: §9.70
established that the coal chain - the overwhelming majority of freight on this
network, ~110 movements/day - has run on dedicated track **grade-separated
since 2006**, so it does not cross these roads at grade at all. What the zero
does not assert is that no non-coal freight ever uses these lines; ARTC
publishes no movement log, so that remainder is unquantified and the field is
swept 0-30 rather than left out.

The residual in the timing is stated too: the offset between a train's nearest
stop and the crossing itself is not modelled. At both sites the nearest rail
stop is the adjacent station, so it is well under a minute.

### The guard, and the member that is kept

`A.crossings.closure_source` is categorical - `assumed_uniform` reproduces
every arm before this exactly, `schedule_derived` is the value. The builder
**refuses** rather than degrades: a crossing with no mapped rail link within
the tolerance, or mapped links carrying no scheduled movement, stops the build,
because a silent zero there would delete the crossing from the model while the
build reported success.

The schedule read is the scenario's **already-mapped** feed, never a re-run of
the mapper (§3.5): mapping is not reproducible run to run, and a second mapping
would put the trains on different links from the ones the scenario simulates.

### Mode 12 finally has a target

`mode_targets_by_mode.csv` carries `freight_train` = **314 closures/weekday**,
`derived`, on its own denominator. With §9.89's ferry, **all twelve modes now
carry a target and none is ungateable** - which was the point.

---

## 9.91 The gate fires at iteration 50, and the first defect found is in the yardstick (29 August 2026, thirteenth session; issues #49, #84, #48)

The F12 arm reached iteration 50 with **ten of twelve modes past the 20% bar**
and was stopped. Taxi was not merely past it, it was **diverging**: 1.20% at
iteration 1, 7.75% at iteration 50, against a target of 0.19%.

### The reading

| mode | modelled | target | deviation | trend it. 1 → 50 |
|---|---:|---:|---:|---|
| car | 40.5301 | 58.1631 | −30.3% | −39.6 → −30.3, converging |
| ride | 7.2143 | 20.6000 | −65.0% | −53.7 → −65.0, **worsening** |
| walk | 26.0547 | 13.4000 | +94.4% | +169.1 → +94.4, converging |
| bike | 9.1408 | 3.0131 | +203.4% | worsening |
| motorbike | 0.1589 | 0.2406 | −34.0% | |
| taxi | 7.7482 | 0.1869 | **+4045.6%** | **diverging** |
| bus | 8.3717 | 1.3039 | +542.1% | |
| heavy_rail | 2.0771 | 2.0922 | **−0.7%** | the only mode inside the bar |
| light_rail | 0.2570 | 0.4039 | −36.4% | |
| ferry | 0.1532 | 0.1013 | +51.2% | |
| truck | 7.6812 | 15.4698 | −50.3% | |
| freight_train | 314 | 314 | representation | not a fit |

### The defect was in the target, not only the model

The taxi target of 0.1869% came from §9.87 splitting the HTS "Other" category
by the **census journey-to-work** share. That is the wrong instrument, and it
is wrong by about fivefold. The census counts journeys **to work**, and
taxi/rideshare is overwhelmingly not a commute mode - it carries nights out,
airport runs, medical trips and the carless. Sizing it by commuting understates
it by roughly the ratio of those two populations.

The city had already declared a better source, and §9.87 overlooked it:
**`B.taxi.daily_trips_band`**, the IPART 2025 point-to-point incidence band of
**15,000-25,000 trips a day across the study area**. Against 2,017,000
study-area weekday trips that is **0.744%-1.240%**, and the target becomes the
midpoint, **0.9916%**.

**Bike moves with it, because it must.** Bicycle and taxi/rideshare sit in ONE
survey category, so neither can be set alone: bike now takes the residual,
**2.2084%**. The residual also carries wheelchair, carshare and aircraft, so it
slightly OVER-states cycling - a direction worth stating, because it means
bike's measured excess is if anything understated.

One assumption joins a study-area count to a target-LGA share, and it is
declared rather than buried: `CAL.taxi.lga_concentration`, point value **1.0**,
swept **upward only** to 2.0. The target LGA holds the regional CBD, the base
hospital, the nightlife precinct and the airport link, so the true
concentration is more likely above 1.0 than below - the neutral value is
deliberately the unflattering one.

**This does not make the model right.** Taxi still reads far above 0.9916%. It
removes a defect in the yardstick before the model is judged against it, which
is the order the work has to happen in.

### What the model's own taxi behaviour was measured to be

Everything below was measured on the stopped arm rather than reasoned from the
config, because the arithmetic and the outcome disagreed and one of them had to
be wrong.

- **Scoring is not the culprit.** A median taxi trip is **13,072 m** costing
  **27.13 AUD** against car's 2.35 AUD for the same distance, and plans
  containing a taxi leg score **mean −128.2 / median −81.2** against **−44.0 /
  +44.1** for plans without one. Taxi is priced, and it is priced heavily.
- **The flagfall binds.** 42,835 taxi departures produced ~42,835 `personMoney`
  events inside a total of 70,657 (the remainder being parking).
- **It is not unmet carless demand.** Taxi is **7.52% of trips among agents
  holding BOTH a car and a licence**, against 8.06% for the carless. A mode
  absorbing genuine captive demand would not look like that.
- **It is not degenerate short trips.** Only 0.72% of taxi trips are
  zero-distance, against 23.33% of `ride` legs - which is its own finding, filed
  below.
- **Taxi is seeded at exactly 0.0.** The demand model generates no taxi trips at
  all; every one of them arrives through mode-choice innovation and is then
  retained.

The remaining candidate is the one term in the taxi price that emits no event
and so has never been proven to bind: `monetaryDistanceRate`, applied inside
scoring, worth 24.14 AUD of the 27.13. Reading the code cannot settle it -
`RUN.mode_choice.proba_random_single_trip_mode` sits at the very top of its
declared sweep [0.0, 0.5] and would also inflate a rarely-good mode, so two
mechanisms remain live. The overlay `taxi_fare_stress_1pct` separates them by
multiplying both fare rates by twenty: if taxi collapses the rate binds, and if
taxi still climbs the rate is inert.

### A held-fixed rule whose own departure condition has now been met

`B.taxi.fare_per_km_taxi_aud` is HELD FIXED, and its recorded justification
reads: *"The corridor and CBD trips this mode competes for sit far under 12 km,
so the $2.29 beyond-12 km tail is recorded, not modelled."* The measured median
taxi trip in this arm is **13,072 m**, and the mean is **18,295 m**. The
premise is false in the model's own output, and the field's stated departure
condition - *"trip-length evidence that the 12 km tail binds"* - is therefore
**met**. Recorded here rather than acted on in the same breath: the tail makes
taxi MORE expensive, so changing it now would confound the diagnostic that is
currently running.

### Filed, not fixed here

**`ride` legs are 23.33% zero-distance** (9,306 of 39,888) against 1.09% for
car. Whatever produces a degenerate ride leg is doing so at twenty times the
rate of any other network mode, and the ride collapse this session is
diagnosing runs through the same mechanism.

**`miss_endpoints` dominates the pairing failures** at 27,807, against
`miss_window` 4,981 and `miss_capacity` 1,432 - and `B.ride.pairing_rule` is
`both_links`, an ASSUMED value and the strictest of four declared members. It
is NOT relaxed in this entry, deliberately: loosening an endpoint rule until
more pairs match would raise `ride` by inventing shared travel the demand model
never declared, which is the "no biasing" line rather than a repair.

**§9.85's repair is working**, and this is the first arm to show it:
`paired_by_identity` climbs **29 → 8,883** and `pair_rate` has **stopped
decaying** - 0.5563 → 0.4585 at iteration 20, then back up to 0.4794 by
iteration 50. That was the stated success criterion, and it is met.

### The paired diagnostic, and two readings it corrected on the way

The stress overlay and its matched control ran at 1% for 40 iterations, with
innovation disabled after iteration 32 in both.

| iteration | taxi, control | taxi, 20x fare |
|---:|---:|---:|
| 10 | 0.0428 | 0.0308 |
| 20 | 0.0587 | 0.0256 |
| 30 | 0.0669 | 0.0192 |
| **40** (innovation off) | **0.0596** | **0.0054** |

Every other mode agrees between the two arms within about 13%, so the fare is
the only thing that moved.

**The per-kilometre rate binds, and hard: an elevenfold difference.** The one
term in the taxi price that emits no event, and had therefore never been
proven, does reach the score. That closes the question §9.91 opened.

**Two intermediate readings were wrong, and both were wrong the same way -
read off a transient.** First, the stress arm at iteration 20 showed taxi at
2.56% and was read as "price cannot discipline taxi"; by iteration 40 it was
0.54%, and the arm had simply not finished falling. Second, the collapse
appeared to begin at the innovation cutoff, and was read as innovation
sustaining the mode; the control shows the cutoff moving taxi only 0.0669 to
0.0596, about 11%, while the fare moved it elevenfold. **A curve that is still
moving is not a level, and this file now carries two instances of that same
error inside one investigation.**

### What that leaves as the cause

Taxi's equilibrium at the DECLARED fare is about 6% at 1% sample, against a
0.9916% target. It is a genuine model outcome rather than an artefact, and the
arithmetic that said it should be rare is missing something structural.

The structural asymmetry is availability. Every other mode in this model is
constrained by something physical or personal: car by ownership and licence and
by subtour chain consistency, `ride` by a declared driver existing and by
`rideAvail`, bike by `bikeAvail` and an age gate, pt by a timetable and a stop,
truck by being a separate subpopulation, motorbike by a person-level locked
carve. **Taxi is constrained by an age gate and nothing else** - every adult may
take a taxi on every trip, with no fleet, no booking friction and no supply
limit, at a flat declared 5-minute wait.

That also explains the puzzle in §9.91's measurement that taxi is 7.52% even
among agents holding a car AND a licence. `car` is a CHAIN-BASED mode: a
single-trip mode change cannot assign it without breaking the subtour, so an
agent whose chain has been perturbed onto another mode genuinely cannot drive
that leg. Their remaining options are walk, pt, bike, ride and taxi - and for a
13 km leg, taxi beats walking on score. Taxi is not winning against car; it is
winning the trips where car is structurally unavailable, and it wins them
because nothing limits it.

**Not fixed in this entry, and deliberately.** The candidate repairs are a
person-level taxi availability basis anchored on the IPART incidence behind
`B.taxi.daily_trips_band` (mirroring `rideAvail` and `bikeAvail`), or a genuine
fleet with finite vehicles. Both are model changes that open a family, and the
second is the one that makes taxi physically constrained the way the standing
directive asks. Neither is chosen on a 1% forty-iteration diagnostic.

### A held-fixed rule re-read, and the correction points the other way

§9.91 recorded that `B.taxi.fare_per_km_taxi_aud`'s premise - trips "far under
12 km" - is contradicted by a measured 13,072 m median. That still stands. But
the tail it excludes is **$2.29/km beyond 12 km against $2.52/km within**, so
modelling it makes a long taxi trip slightly CHEAPER, not dearer. Correcting it
is a fidelity improvement that moves taxi the wrong way for the fit, which is
exactly why it is recorded here before anyone reaches for it as a lever.

---

## 9.92 The seed is a bad guess on purpose, and the gate was read before the model had answered (29 August 2026, thirteenth session; issues #48, #49, #50)

§9.91 left three candidate causes for the iteration-50 gate. Three paired 1%
diagnostics at 40 iterations settle which of them matter, and the answer
reframes what the gate reading was measuring at all.

### The chain hypothesis: real, and small

`car` and `bike` are MATSim chain-based modes, so a subtour uses them end to
end. `RUN.mode_choice.proba_random_single_trip_mode` assigns a mode to ONE
trip, which breaks that chain, and a broken chain cannot be repaired by another
single-trip change because returning to car needs the whole subtour at once.
The control ran it at 0.5 (the top of its declared sweep) and
`subtour_chain_1pct` at 0.0, everything else identical:

| mode | p = 0.5 | p = 0.0 | target |
|---|---:|---:|---:|
| car | 36.2649% | **40.3358%** | 58.1631 |
| walk | 23.4251% | **20.8958%** | 13.4000 |
| ride | 16.7991% | 15.0857% | 20.6000 |
| bike | 7.6523% | 8.3695% | 2.2084 |
| taxi | 5.9647% | 5.7758% | 0.9916 |

The mechanism is real - car gains 4.07 pp and walk loses 2.53 pp - but it is
**worth about a sixth of car's 22 pp deficit**, and it does nothing for taxi
while making ride and bike slightly worse. **It is not the lever, and this
entry exists partly so nobody reaches for it as one.**

### What the deficit actually is: the seed, and it is deliberate

The seeded split at iteration 0, before any mode choice has run:

| mode | seeded | target | error |
|---|---:|---:|---:|
| car | 32.71% | 58.16% | **−25.45 pp** |
| walk | 29.75% | 13.40% | **+16.35 pp** |
| bike | 7.41% | 2.21% | +5.20 pp |
| pt | 6.82% | 3.80% | +3.02 pp |
| ride | 19.23% | 20.60% | −1.37 pp |
| taxi | 0.00% | 0.99% | −0.99 pp |

Almost every large deviation at the gate is inherited from that. And the seed
is uniform **by recorded design**: `B.mode.seed_split` is "UNIFORM OVER THE
USABLE MODES AND DELIBERATELY A BAD GUESS: it starts the search far from the
observed point so that arriving there is evidence about the model rather than
about the seed."

A declared `informed` alternative exists, approximately the observed split, and
its own description says why it is not the default: **"seeding at the answer
makes reaching the answer uninformative."**

**So the seed is NOT to be changed to close the gap.** Doing so would make
every subsequent fit a restatement of the seed, which is the precise shape of
the biasing this project refuses. Recorded here because the temptation is
obvious and the numbers make it look like a fix.

Note what the seed gets RIGHT: **ride, at 19.23% against a 20.60% target.**
§9.84's binder work is sound, and ride's gate deviation is therefore not a
demand defect at all - see below.

### The gate was read while innovation was still running

Both arms show car flat-to-drifting while innovation is on and then **jumping
at the cutoff**: 31.96% at iteration 30, **35.90% at iteration 35**, with
innovation disabled after 32. The same shape appears in taxi (§9.91).

The model **prefers car**; innovation noise was suppressing it. A reading taken
at iteration 50 of a 1000-iteration arm - where innovation runs until 800 - is
therefore not a statement about the model's answer. **Every "mode past 20%"
verdict this session has produced was taken in that regime**, and the only
honest verdict comes from an arm read after its own innovation cutoff.

### Ride's deficit and walk's excess are ONE mechanism, measured

At iteration 50 of the F12 arm, across all agents:

| | legs |
|---|---:|
| planned `ride` legs | 84,609 |
| paired with a driver | 40,565 (47.9%) |
| **unpaired** | **44,044 (52.1%)** |
| `ride` departures in the events | 40,965 |

Ride departures match the PAIRED count, not the planned one. With
`ridePairing.remodeUnpaired = true`, an unpaired ride leg never departs as
ride: it is remoded before the mobsim and the events-derived trips table
records it as **walk**. The planned-versus-realised split says the same thing -
`modestats` carries ride 14.76% and walk 20.94%, the realised trips carry ride
7.21% and walk 26.05%.

**So ride −65% and walk +94% are not two defects. They are the same 44,044
legs**, and the cause is the 52% pairing failure, dominated by `miss_endpoints`
at 27,807 against `miss_window` 4,981 and `miss_capacity` 1,432.

`miss_endpoints` is not a rule that is too strict. The engine's own recorded
measurement is that such legs mostly have **no endpoint-matching driver at any
hour** - the household genuinely drove elsewhere, because per-agent replanning
moved the driver. That is the §9.82 defect class: B2 generates the pair, and
`SubtourModeChoice` moves one agent at a time, so the two-sided state is
unreachable by any per-agent strategy once lost.

The declared instrument for it is already built and is deliberately a SEARCH
parameter rather than a preference: `B.ride.escort_coherence_rate` and
`B.ride.joint_coherence_rate` set how often a decohered pair is **offered** the
coherent plan back, with `ChangeExpBeta` still deciding on score - "propose,
never impose". Both sit at **0.1 in a declared [0.0, 0.5]**, and
`ride_coherence_1pct` measures 0.4 against the control.

### What is NOT being done, and why

- **The seed stays uniform.** Seeding at the answer makes the answer
  uninformative.
- **`B.ride.pairing_rule` stays `both_links`.** §9.91 floated relaxing it;
  the engine's own measurement says the missing pairs have no matching trip at
  any hour, so relaxing would pair passengers with drivers going elsewhere.
- **`proba_random_single_trip_mode` stays at its declared value.** Measured
  worth ~4 pp of a 22 pp deficit; moving it would be buying a small fit
  improvement with an exploration parameter.

---

## 9.94 The uniform seed is recoverable for three modes and diverges for three others (29 August 2026, thirteenth session; issues #48, #49, #50, #88)

The first F12 arm to reach a gate: `20260829T054941_1000it_10pct`, 10% sample,
1000 iterations, innovation off at 800, stopped on the standing directive at
iteration 102 after the iteration-100 gate. Pace **108 s/iteration**, so the
iteration-800 cutoff was ~21 h further on.

### The gate reading, on trips

| mode | modelled | target | deviation |
|---|---:|---:|---:|
| car | 45.5103 | 58.1631 | −21.8% |
| ride | 7.1512 | 20.6000 | −65.3% |
| walk | 20.6445 | 13.4000 | +54.1% |
| bike | 8.9434 | 2.2084 | +305.0% |
| motorbike | 0.1174 | 0.2406 | −51.2% |
| taxi | 9.2720 | 0.9916 | +835.1% |
| bus | 6.4360 | 1.3039 | +393.6% |
| heavy_rail | 1.8735 | 2.0922 | **−10.5%** |
| light_rail | 0.0407 | 0.4039 | −89.9% |
| ferry | 0.0110 | 0.1013 | −89.2% |
| truck | 6.7974 | 15.4698 | −56.1% |
| freight_train | 314 | 314 | representation |

### The level is not the finding. The DIRECTION is

§9.92 established that this model starts from a deliberately uniform seed, so a
level read while innovation is running says more about the seed than the model.
The trend separates the two cleanly, and it is the first evidence either way:

**CONVERGING - the co-evolution works, and this had never been demonstrated:**

| mode | it. 0 | it. 25 | it. 50 | it. 100 | target |
|---|---:|---:|---:|---:|---:|
| car | 34.09 | 34.04 | 37.90 | **44.22** | 58.16 |
| walk | 28.88 | 24.72 | 20.32 | **15.22** | 13.40 |
| pt | 6.88 | 6.42 | 6.02 | **5.30** | 3.80 |

Walk has travelled from +115% to +14% of its target. That is the seed being
recovered from, which is the whole purpose of seeding it badly.

**DIVERGING - running longer will not fix these:**

| mode | it. 0 | it. 25 | it. 50 | it. 100 | target |
|---|---:|---:|---:|---:|---:|
| taxi | 0.00 | 5.52 | 7.45 | **8.81** | 0.99 |
| bike | 7.08 | 7.45 | 7.99 | **8.24** | 2.21 |
| ride | 19.03 | 17.84 | 16.30 | **14.19** | 20.60 |

Motorbike is flat at 0.18 against 0.24.

**Ride is the serious one, because it starts almost exactly right.** The seed is
19.03% against a 20.60% target - §9.84's binder is sound and the demand is not
the defect. Two losses then compound: planned ride falls to 14.19% as agents
abandon it, and only about half of what remains realises (7.15% in the trips
table) through §9.92's remode mechanism. That is a feedback loop - pairing
fails, the unpaired leg is walked, the ride plan scores badly, the agent drops
ride, and the thinner ride demand leaves fewer pairing candidates. The
coherence listener at 0.4 pushes against it and does not reverse it.

The arm was stopped rather than spend ~21 h more confirming three divergences
whose causes are identified and unfixed.

### Taxi: the cause is supply, and a real fleet is NOT buildable here

Taxi is the only mode in this model constrained by nothing but an age gate -
no ownership, no fleet, no booking friction, no availability attribute - while
car is limited by ownership and chain consistency, ride by a declared driver,
bike by `bikeAvail` and age, pt by a timetable, truck by being its own
subpopulation and motorbike by a locked carve. §9.91 measured that taxi wins
the trips where car is structurally unavailable, and it wins them because
nothing limits it.

**The correct repair is a finite fleet**, which would also close the standing
directive's "physically simulated" requirement for this mode properly: waiting
would EMERGE from supply instead of being the declared 5-minute constant
`C.taxi.wait_min`. It is recorded here as **NOT DONE, with the reason**:

- The pinned run stack resolves `org.matsim:matsim` plus
  `org.matsim.contrib:signals` only - 201 jars, **no DVRP and no DRT**.
- Adding them is a TOOLCHAIN CHANGE, which this project treats as a model
  change requiring a re-resolve, re-hash and a §14 entry, and the network
  sandbox does not list Maven Central.

**The demand-side alternative was considered and refused for now.** A
person-level `taxiAvail` attribute mirroring `rideAvail`/`bikeAvail` is
buildable today, but sizing it needs a point-to-point USER INCIDENCE, and the
package holds no such figure: `data/raw/p2p/` carries the Fares Order and
nothing else, and `B.taxi.daily_trips_band` cites IPART incidence that was
consumed OUTSIDE the package to build the band. Choosing a user share so that
taxi lands on its target would be fitting the availability to the answer -
the §9.92 error in a different costume. **The honest next step is to acquire
the incidence, not to assume it.**

### What the arm did establish

That the uniform seed is recoverable. Before this arm, no evidence existed
either way, and §9.92 could only say the question was open. Car, walk and pt
move monotonically toward their targets across 100 iterations with innovation
still running. The model's co-evolution is working; three modes have specific,
identified mechanisms that it cannot fix on its own.

---

## 9.95 The bound pairing window was half the drift it exists to cover, and a third of ride demand names nobody (29 August 2026, thirteenth session; issues #48, #91)

§9.94 named ride the largest fixable deviation and said the next step was to
measure WHY declared pairs fail, because `ride_pairing.csv` reports
`miss_endpoints` as a total with no explanation attached. That measurement now
exists: `src/analyse/diagnose_ride_pairing.py` reads the SAME artefact the
engine reads - the selected plans at `BeforeMobsim`, where a ride leg is still a
ride leg - and classifies every declared ride leg by what its named driver was
actually doing.

The realised legs table cannot answer this question at all, because
`remodeUnpaired` converts every unpaired ride leg BEFORE the mobsim (§9.92).

### The reading, arm `20260829T054941` at iteration 100

| verdict | ride legs | share |
|---|---:|---:|
| paired_ok | 11,525 | 37.96% |
| **no_declared_driver** | **9,036** | **29.76%** |
| **window_only** | **3,987** | **13.13%** |
| dest_only | 2,109 | 6.95% |
| origin_only | 1,864 | 6.14% |
| driver_no_car_leg | 1,391 | 4.58% |
| neither_endpoint | 451 | 1.49% |
| **total** | **30,363** | |

**The suspected cause was wrong.** `neither_endpoint` - the household genuinely
driving somewhere else, which is what `miss_endpoints` was read as - is
**1.49%**. The declared bindings largely survive replanning. §9.92 was right to
refuse relaxing `B.ride.pairing_rule`, and now it is right for a measured reason
rather than an inherited one.

### Defect 1: the window was derived from one agent's drift, not two

`B.ride.bound_pairing_window_min` was `time_mutation_range_s / 60` = **30 min**.
But `time_mutation_range_s` is the half-width `TimeAllocationMutator` applies to
**each agent independently** - the field's own description already said so:
*"the mutator moves each member independently, so a pair generated to depart
together drifts apart."*

Two independent draws on ±1800 s can land **3600 s apart**. The relative drift a
declared pair accumulates is **twice** the half-width, not equal to it, so the
window was **half the size of the drift it exists to cover** and was refusing
pairs the model itself had separated.

The data shows the old window's own edge: of the 3,987 `window_only` legs -
declared pairs with **both endpoints matching exactly**, refused on the clock
alone - the median gap is **53.6 minutes** and the **minimum is exactly 30.0**,
which is the discarded boundary printing itself in the measurement.

Corrected identity:

```
bound_pairing_window_min = 2 * time_mutation_range_s / 60      -> 60 min
```

**This is a correction to a derivation, not a tuning.** The value still cannot
move without moving the mutation range that produces the drift, it is still an
identity rather than a free parameter, and the realised gap is still paid for as
waiting time in score. What changes is that the identity now describes the
quantity it always named.

### Defect 2: three in ten ride legs name nobody (#91)

**9,036 of 30,363 ride legs carry no `boundDriver` at all.** B2 generates them
as ride demand without binding them to anybody, so the engine can only pair them
by geometric discovery - the strict `both_links` test against an unrelated
household member, inside the 15-minute INFERRED window.

That reframes the ride deficit again. Ride **seeds at 19.03% against a 20.60%
target** (§9.94), so demand generation is right in aggregate; but a third of it
is generated in a form the realisation machinery structurally cannot serve, and
those legs become walk before the mobsim - which is the same mechanism inflating
walk. Filed as **#91**, not fixed here: the question is which B2 pathway
produces an unbound ride leg, and that is a demand-build investigation rather
than an engine one.

### What this predicts, and what it does not

Correcting the window should convert the `window_only` legs whose gap is under
60 minutes - a little over half of 3,987 by the median - which moves the paired
share from 37.96% toward roughly 45%. **It is a prediction, not a result**, and
the arm that tests it has not been run. Nothing here changes `dest_only` (6.95%)
or `origin_only` (6.14%), which remain rule questions, or `no_declared_driver`,
which is #91.

---

## 9.96 CORRECTION: ride's seeded share is the uniform draw, not evidence the binder is sound (29 August 2026, thirteenth session; issues #48, #91)

**§9.94 and §9.95 both state that ride seeding at 19.03% against a 20.60% target
shows "the demand is right" and vindicates §9.84's binder. That inference is
wrong, and it was repeated twice before it was checked.**

### The arithmetic

A tour's initial mode is `tour_mode[tour_id]`, drawn from `B.mode.seed_split` -
the DELIBERATELY UNIFORM table (§9.92): ride at p=0.20 for a car-available
person and p=0.25 for the rest. Measured on the F12 arm, 76.3% of trips are made
by car-available persons, so the uniform draw ALONE predicts

```
0.763 x 0.20  +  0.237 x 0.25  =  21.2%
```

against an observed seeded ride share of **19.03%** - the shortfall explained by
bound serve-tours being seeded to car instead (§9.68).

**So ride's seeded share is the uniform table showing through.** It sits close
to the observed 20.60% by coincidence, because 0.2 happens to be near 0.206. It
is not a measurement of the binder, and it cannot vindicate anything.

### What that changes

- **§9.94's "what the seed gets RIGHT is ride" is withdrawn.** The seed gets
  ride *numerically close* for a reason unrelated to whether ride demand is
  correctly generated.
- **§9.95's reading of #91 is corrected.** The 29.76% of ride legs with no
  `boundDriver` is the expected consequence of a uniform seed assigning ride at
  random, NOT a demand build that forgot to bind them. #91's framing has been
  corrected on the issue itself.
- **Whether the binder is correctly sized remains OPEN.** No measurement in this
  session bears on it, and the seed cannot supply one while it is uniform.

### What survives unchanged

The two defects §9.95 found stand on their own measurements and are unaffected:
the bound window was half the drift it covers (median gap 53.6 min, minimum
exactly 30.0 against a 30-min window), and `neither_endpoint` is 1.49%, so
relaxing the pairing rule would recover nothing.

And the structural point sharpens rather than weakens: **most seeded ride legs
are random and unpairable by identity**, so mode choice has to discover that
ride realises only for bound pairs - migrating toward them and away from random
ride. That is a slow search, and it is consistent with realised ride (−65.3%)
being far worse than planned ride (−31%).

**The open question is now better posed:** can the model discover that within a
converged arm, or should ride demand be generated FROM the bindings rather than
from a mode seed at all? The second would be a demand-build change, and it is
not made here.

### Why this is recorded rather than quietly fixed

The claim was stated twice, in two committed entries, and used to argue that the
ride problem was purely one of realisation. A reader who took that at face value
would stop looking at demand generation entirely. The trap it belongs to is
already at the top of §8 in the brief - **a number that agrees with your
expectation still has to be explained** - and this is the same error as reading
a moving curve as a level, in a different costume.

---

## 9.97 A diagnostic that read today's window into yesterday's arm, and the third instance of one error (29 August 2026, thirteenth session; issue #48)

§9.95 corrected the bound pairing window from 30 to 60 minutes and predicted the
paired share would move from 37.96% toward ~45%. The arm testing it reached
iteration 50, and the first reading appeared to confirm it: paired_ok **42.02%**
against the previous arm's **37.96%**.

**That comparison was invalid three times over, and the tool itself had a
defect that would have flattered every future one.**

### The tool defect

`diagnose_ride_pairing.py` took the bound window from the LIVE REGISTRY rather
than from the run that executed it. Classifying a historical arm therefore
applies today's rule to plans that never ran under it — and the reclassification
is indistinguishable from a model improvement.

It announced itself in the data: the previous arm, which **ran a 30-minute
window**, reported a minimum observed gap of **60.1 minutes**. A minimum gap
cannot sit above the window that produced it; the current window was printing
itself into an arm that never saw it. The tool now reads the tolerances from the
run's own `config.xml` and refuses a run whose config declares none, rather than
falling back to the registry.

### The comparison, done properly

Depth-matched at iteration 50, each arm classified under the window it actually
ran, and differing in **only** that window (the coherence rate was already 0.4
in both):

| verdict | old arm, 30 min | new arm, 60 min | change |
|---|---:|---:|---:|
| paired_ok | 40.07% | **42.02%** | **+1.95 pp** |
| window_only | 10.68% | **8.37%** | **−2.31 pp** |
| dest_only | 7.15% | 7.30% | +0.15 |
| origin_only | 6.28% | 6.34% | +0.06 |
| neither_endpoint | 1.73% | 1.81% | +0.08 |
| driver_no_car_leg | 4.55% | 4.38% | −0.17 |
| no_declared_driver | 29.55% | 29.78% | +0.23 |

**The correction is real, it moves only what it should, and it is worth about
+1.95 pp — roughly a quarter of the ~7 pp §9.95 predicted.** The prediction was
extrapolated from the previous arm at iteration 100, where drift has had twice
as long to accumulate and the `window_only` pool is correspondingly larger;
reading it against iteration 50 compared two different points on a transient.

The residual `window_only` legs are not a case for widening further: their
median gap is now **344 minutes**, nearly six hours. Those are genuinely
different trips at different times of day, not replanning drift, and a window
that admitted them would be pairing people who are not travelling together.

### The pattern — three instances, one error

This session has now made the same mistake three times, in three costumes:

1. **§9.91** — a stress arm read at iteration 20 said "price cannot discipline
   taxi"; by iteration 40 it said the opposite. *A moving curve read as a level.*
2. **§9.96** — ride seeding at 19.03% against a 20.60% target was read as
   evidence the binder was sound; it is the uniform seed's own p=0.20 showing
   through. *A number that agreed with the expectation, not explained.*
3. **§9.97, here** — a tool compared an arm against itself under a changed rule
   and produced a confirmation. *A yardstick that moved with the thing it
   measured.*

All three share one shape: **a comparison whose two sides were not the same
kind of thing**, presented as a measurement. The discipline that catches it is
not more care in the moment; it is asking, before quoting any difference, what
ELSE differs between the two numbers besides the thing under test. The first was
caught by waiting, the second by arithmetic, the third by an impossible value in
the output — and only the third would have been caught by a check.

**What is NOT withdrawn:** the derivation correction in §9.95 stands on its own
argument. `time_mutation_range_s` is applied to each agent independently, so a
pair drifts up to twice it; the identity was wrong before and is right now,
whatever the size of the effect turns out to be.

---

## 9.98 The window correction measured at depth: real, and not the bottleneck (29 August 2026, thirteenth session; issues #48, #91)

The arm carrying §9.95's corrected identity reached iteration 100, the depth
§9.95's prediction was actually about. Depth-matched against the previous arm,
each classified under **the window it itself ran** (§9.97's fix), and differing
in only that window:

| verdict | old, 30 min | new, 60 min | change |
|---|---:|---:|---:|
| paired_ok | 37.96% | **41.53%** | **+3.57 pp** |
| window_only | 13.13% | **8.82%** | **−4.31 pp** |
| dest_only | 6.95% | 7.17% | +0.22 |
| origin_only | 6.14% | 6.28% | +0.14 |
| neither_endpoint | 1.49% | 1.57% | +0.08 |
| driver_no_car_leg | 4.58% | 4.46% | −0.12 |
| no_declared_driver | 29.76% | 30.16% | +0.40 |

The effect is **larger at depth than at iteration 50** (+3.57 pp against
+1.95 pp), which is what accumulating drift predicts and is a small independent
confirmation of the mechanism. It remains **about half the ~7 pp §9.95
predicted**, and that prediction is not retrospectively rescued.

### What it bought in ridership: almost nothing

| mode | previous arm | this arm | change |
|---|---:|---:|---:|
| car | 45.5103 | 46.0231 | +0.51 |
| ride | 7.1512 | **7.3417** | **+0.19** |
| walk | 20.6445 | 20.1224 | −0.52 |
| bike | 8.9434 | 8.7576 | −0.19 |
| taxi | 9.2720 | 9.3525 | +0.08 |

**A +3.57 pp pairing improvement bought +0.19 pp of ride mode share.** Every
mode moved in the direction its target lies, and all of it is marginal.

**The pairing window was a real defect and never the bottleneck.** The
constraint on ride is upstream of the engine: 30.16% of ride legs carry no
declared driver at all (#91, and §9.96 explains why - the uniform seed assigns
ride at random), and the plan-level abandonment that turns a 19.03% seed into a
14.19% planned share happens before any pairing is attempted.

### Recorded so the next agent does not re-buy it

Widening the window further is now measurably pointless: the residual
`window_only` legs have a median gap of **344 minutes**. Those are different
trips at different times of day, and a window admitting them would pair people
who are not travelling together.

---

## 9.99 Taxi gets a finite fleet, and a refused request walks (29 August 2026, thirteenth session; issue #90)

§9.94 recorded taxi's repair as **blocked**: the correct fix was a fleet, the
MATSim DRT contrib is absent from the pinned run stack, and `repo1.maven.org`
returns 404 while allowed hosts return 200. The blocker was real. **The
conclusion drawn from it was not.**

A fleet does not need a mobsim dispatcher. It needs the point where every
selected plan is stable and nothing will re-route underneath the decision - the
`BeforeMobsim` boundary, which is **exactly where `RidePairingEngine` has been
pairing ride legs since §9.44.** The pattern was already in the repository.

### What was wrong

Taxi was the only mode constrained by nothing:

| mode | constraint |
|---|---|
| car | ownership, licence, subtour chain consistency |
| ride | a declared driver must exist; `rideAvail` |
| bike | `bikeAvail` and an age gate |
| pt | a timetable and a stop |
| truck | its own subpopulation |
| motorbike | a person-level locked carve |
| **taxi** | **an age gate. Nothing else.** |

Seeded at exactly 0.0 because the demand generates none, it climbed through
mode-choice innovation to 8.8% against a 0.99% target, at 7.52% even among
agents holding both a car and a licence (§9.91). It was not out-competing car -
car is chain-based, so a perturbed subtour cannot use it - it was winning those
trips because nothing said no.

### The mechanism

`citysim.TaxiFleetEngine` collects every taxi leg in the selected plans, sorts
by (departure, person, leg index), and serves them greedily from the
earliest-free vehicle. A vehicle becomes busy for the fare's own travel time
plus a declared deadhead. A request whose earliest-free vehicle is further off
than `B.taxi.max_wait_min` is **refused**, and a refused request **walks this
iteration** with the mode restored at `AfterMobsim`.

That last clause is §9.81's correction carried across: a refusal that deleted
the alternative would be the one-way ratchet where failure is permanent and
success creates nothing.

**Nothing caps the mode share.** The supply constraint is the price, and taxi
becomes emergent - the same reasoning §9.55 applies to ride.

Serving in departure order from the earliest-free vehicle maximises the number
served for a given fleet, so this is the fleet's **best case**: a real
dispatcher does worse, and any refusal here is one a real fleet would also have
made.

### The fleet size is derived, not declared

The observed quantity is a TRIP volume - `B.taxi.daily_trips_band`, the IPART
2025 point-to-point band. Turning it into vehicles needs one thing:

```
fleet_size = mean(daily_trips_band) / vehicle_trips_per_day
           = 20,000 / 25  =  800 vehicles at full scale
```

`B.taxi.vehicle_trips_per_day` is the ONE free quantity, declared `literature`
and swept 15-35 - a factor of 2.3 on the fleet, which is the honest width given
that no Newcastle utilisation figure is published. The engine scales the fleet
by `qsim.flowCapacityFactor` for the same reason the SCATS saturation flow is
scaled (§9.88): a sampled run is a city whose capacities were scaled, and a
full-scale fleet serving a tenth of the demand would constrain nothing.

### Two simplifications, stated rather than hidden

**Empty running does not load the road.** The deadhead is time a vehicle is
unavailable, not a routed leg, so dead legs consume no link capacity. This is
the one thing a full demand-responsive implementation would add.

**There is no spatial dispatch.** Which vehicle is nearest is not modelled,
because vehicle positions would require those routed empty legs. The declared
`B.taxi.deadhead_min` stands in for the average cost of reaching the next fare,
and zero recovers a fleet that teleports between them.

### Measured

Probe `20260829T171626_2it_1pct`, rc=0, accounting closes:

| iteration | requests | served | refused | mean wait |
|---:|---:|---:|---:|---:|
| 0 | 0 | - | - | the seed generates no taxi |
| 1 | 274 | 250 | **24 (8.8%)** | 340 s |
| 2 | 177 | 177 | 0 | 7 s |

Requests fall 274 to 177 because the refusals price taxi down. **The fleet binds
under load and relaxes when it does not**, which is the behaviour a supply
constraint should have and a cap would not.

`absent` is kept as a declared member and reproduces every arm before this
exactly, so the fleet's effect stays measurable rather than asserted.

### The lesson worth carrying

**"Blocked on a dependency" deserves the same scepticism as any other claim.**
The dependency was genuinely unavailable and the inference from it was still
wrong, because the thing it was needed for could be built another way - out of
a pattern this repository already used for a different mode. §9.94's blocker is
withdrawn; the sandbox measurement it rests on stands.

---

## 9.81 A missed pairing was deleting the ride alternative, and the model was walking back to its pre-repair answer (26 August 2026, ninth session; issues #48, #49, #30)

The first F6 arm was launched 25 August at 13:57 and **stopped by instruction at
iteration 200** under the session's goal directive: stop if car bias, near-zero
ride, or any over-chosen mode persists. Every clause held. Whole-scenario leg
shares moved from the seed to iteration 200 as car 30.81 -> 54.33, walk 44.25 ->
15.96, ride 4.35 -> **0.41**, taxi 0.00 -> 9.47, bike 8.86 -> 11.38, pt 7.74 ->
4.46. Its record is `results/aborted_20260825T135734_1000it_25pct`, status
`aborted`, cause stated. **Its 200 iterations are diagnostic evidence, not a
result**: no `_run.json`, unconverged, innovation still on.

### What the arm measured

`RidePairingEngine` re-moded an unpaired ride leg to a network walk, per the
§9.55 ruling that a ride no household driver can serve is not a ride trip. But
it did so by **mutating the plan** — `setMode(walk)`, `setRoute(null)`, and the
`continue` skipped the restore the paired path uses. Pairing failure therefore
DESTROYED an alternative while pairing success created none.

That is a one-way ratchet, and it ran regardless of what the scores said:

| iteration | ride legs | paired | unpaired | occupancy |
|---|---:|---:|---:|---:|
| 0 | 87,019 | 25,610 | 61,409 | 0.1410 |
| 1 | 28,228 | 22,188 | 6,040 | — |
| 50 | 12,306 | 7,320 | 4,986 | 0.0370 |
| 199 | 6,841 | 2,394 | 4,447 | 0.0075 |

**58,791 legs — 95.7% of the 61,409 that failed to pair at iteration 0 — were
gone by iteration 1 and never returned.** Occupancy decayed exponentially with a
36-iteration half-life toward the pre-repair arm's converged 0.0013. The seed
(`B.mode.bound_passenger_seed`) was the only reason it started anywhere else.

The damage was not confined to ride. At iteration 0 those 61,409 destroyed legs
were **23.5% of all walk legs**, each a ~9.7 km forced walk scoring about −26
utils. That manufactured pool is the feedstock replanning converted into taxi
(0 -> 9.47%) and bike, which is why taxi gained more than ride lost.

### Why it is a defect and not the ruling

§9.55 says an unservable ride walks and **scores accordingly**. It does not say
the plan must be rewritten so the alternative can never be re-evaluated. MATSim's
design is that plans persist and are re-scored; a mobsim-boundary listener
deleting one breaks that contract.

**The walk is now an EXECUTION, not an amputation.** The leg's mode and route are
restored at `AfterMobsim`, after the mobsim has emitted the events scoring reads,
so the agent is charged in full for the walk it actually made while the plan
keeps `ride` for co-evolution to re-select when driver supply returns. The
surviving ride share stays emergent from the physical driver supply. **No
parameter was added, moved or swept; `B.ride.remode_unpaired` stays `true`.**

### The window was a red herring, and measuring said so

A first funnel put 61% of misses on the pairing window, which would have argued
for moving `B.ride.pairing_window_min` (assumed, swept [5, 60]) — a parameter
change made to fix a symptom. **Measuring the gaps refused it.** Of 1,529 window
misses only 112 had an endpoint-matching driver at ANY hour, median **253.7
minutes** away; ONE was within 30 minutes and 13 within an hour. Widening 15 ->
60 would have recovered 13 legs of 1,529.

The funnel had asked "was anyone in the window?" before "was anyone going there
at all?", so it labelled as a timing miss every passenger whose household drove
somewhere else entirely. **Ordered geometry-first, ~90% of misses are passengers
no household driver was ever going to serve** — the uniform seed's random ride
legs, which have no driver by construction and SHOULD fail. They now die by
scoring rather than by deletion.

**The aggregate pair rate was therefore meaningless**: it averaged ~2,260
structurally unpairable seed legs against ~930 genuinely bound ones. Split, the
bound population pairs at 0.7552 by iteration 1 and **0.9964 by iteration 2**
(probe `20260826T051545_2it_1pct`), and at that rate ride's expected score beats
bike, taxi and walk outright. `ride_pairing.csv` now carries the funnel and the
gap distribution so the two populations can never again be read as one.

### Correction, same day: the first implementation of this fix did nothing

The restore above was first written as `ride.leg.setMode(ride)` at AfterMobsim,
holding the `Leg` reference the pairing had collected at BeforeMobsim. **That
version was a no-op, and the arm it ran on proves it**: arm
`20260826T051938` returned ride-leg counts byte-identical to the unfixed F6 arm
— 87,019 / 28,228 / 25,889 — while its log reported 61,409 legs "restored".

A `Leg` object cannot be held across the mobsim. The re-mode nulls the route so
the walk is routed on the walk network; a null route is precisely what makes
`PersonPrepareForSim` run `PlanRouter` over that trip; and
`TripRouter.insertTrip` **replaces the trip's plan elements with new `Leg`
objects**. The restore therefore wrote to an orphan.

It was caught in ten minutes, at iteration 3, by comparing the new arm's counts
against the old one's rather than trusting the log line — the same discipline
that refused the window hypothesis. The arm was stopped and is recorded as
`results/aborted_20260826T051938_1000it_25pct`.

The corrected restore **re-finds** the leg in the person's selected plan by the
endpoints the pairing recorded, and logs restored-of-attempted so the count can
never again be a claim about intent rather than effect. Probe
`20260826T053412` holds ride legs at **3,435 / 3,441 / 3,443** across three
iterations where the broken version fell to 1,062 / 834, with 2,508 of 2,508,
2,637 of 2,637 and 2,592 of 2,592 legs actually restored.

The aggregate pair rate now sits near 0.25 rather than climbing to 0.996, and
that is the CORRECT consequence: structurally unpairable legs are retained and
keep failing, so they are abandoned by scoring over many iterations instead of
being deleted in one. That is what "emergent from the physical driver supply"
was always supposed to mean.

### Second correction: a trip has ONE routing mode, so the restore replaces the trip

The re-found-leg restore then killed arm `20260826T053741` at iteration 1:
`RuntimeException: Found a trip whose legs have different routingModes`
(agents 223559, 539119, 522667). Re-routing a forced walk can produce a
MULTI-LEG trip, and MATSim requires every leg of a trip to carry the same
routing mode; setting one leg back to `ride` and leaving its siblings on `walk`
is an inconsistent plan. **The 1% probe could not have caught this** - no
matching agent there held a multi-leg walk trip - which is trap 13's
"verified-at-1% is not verified" in its exact form.

The restore now replaces the whole trip through `TripRouter.insertTrip`, with a
single `ride` leg carrying the route the pairing set aside, matched on the
trip's origin and destination link ids and guarded so it only ever replaces a
trip whose legs are ALL walk.

**Validated at 25% x 2 before relaunch** (`20260826T055023`, completed rc 0):
zero routing-mode errors, 61,409 of 61,409 / 63,712 of 63,712 / 62,718 of
62,718 legs restored, and ride legs held at **87,019 / 85,873 / 86,118** where
the unfixed F6 arm fell to 28,228 / 25,889. Two failed attempts, both caught in
minutes by measuring rather than by trusting a log line; from here a scale
validation runs before any long arm.

### Family F7

The engine change alters what the model does, so nothing compares across it.
**F7-ride-alternative-retained** is declared from launch stamp 20260826T060000.
F6's only arm is the aborted diagnostic above; it never produced a converged arm,
exactly as F5 never did.

**Nothing here is a result.** No converged arm exists in F7, and the fit is
unchanged from the pre-repair F4 report card until one runs.


---

## 9.82 The escort drives and the escorted cycles: a pair the replanner cannot rejoin (26 August 2026, ninth session; issues #48, #50, #30)

The §9.81 arm `20260826T060938` was stopped by instruction at iteration 200. The
§9.81 restore had **worked** — ride legs held at 87,019 / 85,873 / 86,118 across
the first three iterations where the unfixed F6 arm fell to 28,228 / 25,889 —
and it was **not sufficient**. Realised shares at the gate (events stream,
it.190): car 47.90, walk 23.17, bike 9.97, taxi 8.36, pt 6.09, **ride 0.95**,
truck 3.38. Bike and taxi still over-chosen.

### The fix repaired a real defect that was not the one holding ridership down

Across every checkpoint, F7 and the unfixed F6 arm agreed to within **0.15 pp**
on car, bike, taxi and pt, while ride and walk traded an equal and opposite
~10 pp. That is what a clean single-cause repair looks like, and it is precisely
how it was possible to see that a second, independent cause remained.

### What the arm measured

From its own selected plans at iteration 150:

| | |
|---|---|
| trips arriving at an `escort` activity that are **car** | **84.53%** |
| escort-bound members (93,528 in B2) actually on **ride** | **11.45%** |

**The drivers are still driving. The passengers have gone.** A parent drives to
the school and the child has independently decided to cycle, so tens of
thousands of escort car trips run each iteration carrying nobody. One mechanism
suppresses `ride` and inflates `car` and `bike` together — which is exactly the
trio that stayed wrong.

*(The 11.45% counts all legs of escort-bound members, not only their bound tour,
so it is diluted; the 84.53%-against-11.45% asymmetry is the finding, not the
second figure's precision.)*

### Why no per-agent strategy can repair it

B2 generates escort travel as a PAIR — `B2_escort_bindings_<DAY>.csv`, 125,475
rows for a weekday, from census household structure and the HTS escort rates.
MATSim replans the two agents independently and `SubtourModeChoice` moves one
agent at a time, so the two-sided state **cannot be proposed by any per-agent
strategy** and cannot recohere once lost. This is the same structural gap
`B.mode.bound_passenger_seed` already documents for the seed, showing up again
after the seed's advantage has been replanned away.

### What was built, and the line it does not cross

`EscortCoherenceListener` finds, after replanning, car legs arriving at an
`escort` activity and the household members whose own trip shares those
endpoints inside the declared pairing window, and **proposes** the coherent plan
back to a member who is not on `ride`.

**It proposes and never imposes.** The plan is scored like any other and
`ChangeExpBeta` keeps it only if it earns its place: a member whose ride keeps
failing to pair walks a long way, scores badly and abandons it, exactly as
before. The driver is never touched — if the escort cycles, no ride is offered
to anyone.

The only assertion is that **two people travelling together travel by the same
means**, which is a physical identity rather than a calibration. No mode's
utility changes and nothing is fitted to any target. The one declared field,
`B.ride.escort_coherence_rate`, is a SEARCH parameter — how often an unreachable
alternative is offered — and **its zero recovers the previous behaviour exactly**,
which is what makes the mechanism's effect measurable rather than assumed.

The coupling is discovered from the selected plans, so no plans regeneration and
no new run input; the run emits its config from the registry, so the 30 assembled
sets are untouched.

**Validated at 25% x 2 before launch** (`20260826T220340`, completed rc 0): zero
routing-mode errors, the listener firing at 10.2% and 10.3% against the declared
0.10, and ride legs at 87,019 / 85,873 / **87,348** against 86,118 for the same
two iterations without it.

### Correction: a subtour has ONE mode class, and a two-iteration probe cannot see replanning

The first build of this listener re-moded ONE trip of a subtour to `ride` and
left its siblings on `car`. MATSim refuses a subtour mixing chain-based modes
(`car`, `bike`) with non-chain-based ones - the vehicle would be stranded - and
arm `20260826T222352` died at **iteration 2** with `Subtour contains a mix of
chain- and non-chainbased modes: [car, ride]` (persons 93508, 451935). That is
this project's own **trap 13**, the §9.63/#65 mixed-subtour failure, met again.

**The 25% x 2 validation had passed rc=0 on the same code, and could not have
caught it.** Innovation switches off at
`RUN.replanning.fraction_to_disable_innovation x lastIteration`, so a
two-iteration probe runs its LAST replanning with `SubtourModeChoice` already
disabled (0.8 x 2 = 1.6) and never sees the plans the listener modified. Three
probes have now been structurally blind in this session for the same reason -
too small, or too short, to contain the case - so the fix is a committed
artefact rather than a flag: **`probe_replanning_25pct`** runs eight iterations
at the arm's own 25%, keeping innovation on through 6.4.

Two repairs:

- **The whole SUBTOUR is converted, never one trip of it.** This is also the
  more faithful model: an escorted member is dropped AND collected, which is
  exactly what the drop/pickup pairs in `B2_escort_bindings_<DAY>.csv` record.
- **Only a member who cannot drive themselves is offered `ride`**
  (`carAvail != always`). Offering it to a licensed car-available adult would
  second-guess a choice they are entitled to make, and it is not the population
  the defect is about: at `licence = 0` the model puts **48.8%** of trips on a
  bicycle and **0.5%** on ride.

Probe `20260826T224343_8it_25pct`, completed rc 0, zero mixed-subtour errors:
ride legs held at 85-86k throughout and **the pair rate stopped falling** -
0.2943 at iteration 0 down to a trough of 0.2125 at iteration 6, then back to
0.2387 and 0.2526 - with the decohered count falling each iteration (4,349 ->
3,862 -> 3,523 -> 3,296). In F7 the same rate fell monotonically to 0.157 by
iteration 200. Eight iterations settles nothing about convergence; the reversal
of direction is what the probe establishes.

### Family F8

**F8-escort-coherence** is declared from launch stamp 20260826T230000. F7's only
arm is the aborted diagnostic above.

**Nothing here is a result.** No converged arm exists in F8.


---

## 9.83 The gate was being read on the wrong quantity, and the ride gap is a demand ceiling rather than a choice defect (27 August 2026, tenth session; issues #48, #49, #50, #30)

**What this session did:** it launched nothing and changed no model or data value.
It read the three arms of the §9.81/§9.82 lineage on the quantity `fit.py` actually
scores, found the comparison had been made on a different one, and measured the
cause of the residual. The F8 arm was stopped on instruction at iteration 163,
**before** its iteration-200 gate.

### The measurement basis was wrong, and it had inverted one verdict

Every mode table in the §9.81/§9.82 record is **whole-scenario leg counts**, either
from `modestats.csv` or from the events stream. `fit.py` scores neither. It scores
**linked main-mode TRIPS for target-LGA residents only**, and the difference is not
cosmetic:

- `modestats.csv` counts **planned** modes. It is written at `IterationEnds`, after
  the §9.81 `AfterMobsim` restore, so a leg the agent physically WALKED is counted
  as a ride trip. §9.81 already recorded this trap; what was not noticed is that the
  events-leg fallback it prescribed is *also* not the scored quantity.
- Events give **legs**, so a PT access walk inflates the walk denominator, and the
  count spans five LGAs including freight — the §12.1 geography error the fit code
  guards against.

MATSim writes `<n>.trips.csv.gz` per iteration on its own interval, derived from the
**events** stream, already linked and already main-mode: the same quantity
`output_trips` carries. It was present in every arm all along, at iterations 0, 1,
50, 100 and 150. New `src/analyse/measure_iteration_modes.py` reads it and hands it
to `fit.py`'s OWN `score_mode_share`, so the folds and the vintage filter cannot
drift from the real fit; nothing is re-implemented but the choice of file.

**The verdict this inverts: car is NOT over-chosen.** The record's "car bias" —
54.33% planned, 47.90% realised legs — is 52.12% on the scored basis against an
observed 59.00, i.e. **11.7% UNDER**. The whole gate loop had been reading a bias
that the scored quantity does not show.

**And `fit.py` folds bike and taxi into ONE target.** `MODE_TO_HTS` maps the
survey's residual category to `bike`, and `score_mode_share` adds `taxi` to it once
the priced mode exists (§9.76) — exactly the car+motorbike fold. The two
independently over-chosen modes compound into a single miss.

### The three arms compared on the scored basis, at the same iteration

Iteration 150, the deepest snapshot all three arms hold. One change at a time:

| survey category | observed | F6 unfixed | F7 (§9.81) | F8 (§9.82) |
|---|---:|---:|---:|---:|
| Other (`bike+taxi`) | 3.20 | 21.95 | 21.30 | 21.31 |
| Public transport | 3.80 | 7.88 | 7.70 | 7.44 |
| Vehicle driver (`car+motorbike`) | 59.00 | 51.52 | 52.05 | 52.12 |
| Vehicle passenger (`ride`) | 20.60 | 0.61 | 1.39 | 1.61 |
| Walk only | 13.40 | 18.05 | 17.55 | 17.52 |
| **mean abs error, pp** | | **10.991** | **10.460** | **10.348** |

**Both repairs work and neither is sufficient.** §9.81 is worth −0.531 pp of mean
abs error, §9.82 a further −0.112 pp; every scored category moved toward its
observation across F6 → F7 → F8 and **none regressed**; ride nearly tripled, 0.61 →
1.61. Against a 20.60 target that is 7.8% of the gap closed by both repairs
together. The escort-coherence gain also DECAYS with iteration — +0.32 pp at
iteration 50, +0.26 at 100, +0.22 at 150 — and ride is still falling in F8 (2.66 →
2.05 → 1.61) on the same shape it fell in F7 (2.34 → 1.79 → 1.39).

**CORRECTION to §9.82, which stays as written.** That section reports the
8-iteration probe's pair rate reversing — trough 0.2125 at iteration 6, then 0.2387
and 0.2526 — as the evidence that the fix arrests the decay. The probe's config sets
`fractionOfIterationsToDisableInnovation = 0.8`, which for an 8-iteration run is
**iteration 6.4**: the reversal is the innovation cutoff's selection snap, the same
artefact `_progress.json`'s own relaxation basis text excludes and reports
separately as `snap_pp`. The 1000-iteration arm cuts innovation at 800, and its pair
rate duly kept falling through the same iterations (0.2114 at 6 against the probe's
0.2125). **The probe established nothing about convergence.** This is trap §9.1 — a
short probe is blind — met inside the overlay built to defeat it: the overlay
correctly keeps innovation on *through* 6.4, which cannot make iterations 7 and 8
informative.

### Why the residual is not a mode-choice defect

**Every B2 trip has `party_size = 1`** — all 2,343,321 of them. The only two-person
travel the demand generator produces is the escort binding: `dest_placement` counts
`escorted` 125,409 with `lift_pickup` and `lift_serve` 49,030 each. **Escort-bound
travel is 5.4% of all trips against an observed vehicle-passenger share of 20.6%.**
Three-quarters of the demand for the target was never generated, so no repair inside
the escort path — coherence, pairing window, seeding — can reach it.

Two **measured** observations agree on the size of the gap:

| | modelled (F8, it.150) | observed | source |
|---|---:|---:|---|
| vehicle occupancy | 1.0013 | **1.3503** (sweep 1.2493–1.394) | `C.constraint.vehicle_occupancy`, measured |
| vehicle-passenger share | 1.61% | **20.60%** | V205 |

They are mutually consistent: 0.3503 passengers per driver over the arm's 83,421
target-LGA car trips is ~29,200 ride trips, ≈18% of trips. The seats exist — those
car trips carry on the order of 330,000 free seat-trips against the ~33,000 needed.

This is the measurement §9.55 named as decisive. That section accepted, knowingly,
that ride would sit far below 20.60% under household-only pairing and said *"where
the displaced 30-odd percentage points of demand settle is the first converged run's
headline measurement"*. **They settle in the four over-chosen categories**: bike
+8.82 pp, taxi +9.29 pp (together the +18.11 pp `Other` miss), walk +4.12 pp, pt
+3.64 pp. §9.60 already superseded §9.55's report-only stance and built the
non-household mechanism, whose scope `B.activity.escort_binding_nonhh_scope` is at
`same_zone`; the ceiling above is measured WITH that mechanism live, so widening the
scope is the declared, swept lever the next session should measure first.

### Two further causes, measured and NOT acted on

**No age gate on bicycle, and none at all on taxi.**
`AvailabilityModesCalculator` gates `rideAvail`, `bikeAvail` and `lockedMode`, and
core MATSim gates `carAvail`; **taxi is gated by nothing**. `age` is written as a
person attribute and consulted by nothing. Measured on the F7 arm at iteration 150,
mode share by age band:

| age band | trips | walk | bike | taxi | ride | car |
|---|---:|---:|---:|---:|---:|---:|
| 00–04 | 6,938 | 35.6% | **31.1%** | **19.5%** | 4.2% | 0.0% |
| 05–09 | 14,822 | 35.9% | **30.4%** | **19.8%** | 5.5% | 0.0% |
| 10–14 | 18,253 | 35.8% | 29.4% | 22.5% | 4.0% | 0.0% |
| 15–17 | 11,481 | 34.6% | 29.7% | 24.0% | 3.6% | 0.0% |
| 25–44 | 180,398 | 15.3% | 9.8% | 9.5% | 0.8% | 60.0% |

Children ride and hail at ~3× the adult rate. **Bounded**: moving every under-18
bike and taxi trip off those modes takes `Other` from 21.30 to 17.81 — **19% of the
excess**, so this is real and secondary. No threshold was invented: no age × mode
cell exists in the held data (`hts_mode.csv` has none), so a gate needs a declared,
swept, labelled-assumed field, which is what §8 of the ninth session's own handover
instructed.

**Gradient reaches mode choice through nothing, and the network is hilly.**
`build_matsim_run_inputs.py` declares it honestly in `not_representable` — *"MATSim
scores a leg from time and distance and has no gradient term, so the gradient
attached to 43,112 road and 35,653 footway edges reaches mode choice through
nothing"* — and #21 was closed on that record. Measured now on `A1_road_edges.csv`:
all 50,182 rows carry a gradient, none missing, mean |grade| **3.68%**, median
2.03%, **30.5% of edges steeper than 4%**, 12.6% steeper than 8%, p95 13.26%. The
signature is in the geometry:

| | modelled mean | observed (measured) | modelled mean min | observed min |
|---|---:|---:|---:|---:|
| bike | **9.21 km** | 5.2 (`C.constraint.trip_length_km.bike`) | **41.7** | 19.2 |
| walk | 4.38 km | 0.7 | 59.5 | 12.3 |
| car | 11.51 km | 10.2 | 15.7 | 17.2 |

**28.5% of modelled bike trips exceed 10 km and 13.0% exceed 20 km**; 24.3% of walk
trips exceed 5 km and 4.7% exceed 20 km, the §9.81 forced walk executing as designed.
Car geometry sits close to observation; the two unconstrained active modes do not.
Observed cyclists ride SHORTER trips FASTER (5.2 km at 16.3 km/h) than the model
(9.21 km at 13.2 km/h), which is the shape a gradient term produces and a flat speed
cap cannot. `bike` and `walk` are qsim main modes on the network, so gradient has a
physically correct channel — link travel time — and `LinkSpeedCalculator` is present
in the pinned run stack, so no toolchain change is implied. **Not built this
session.**

### What this deliberately does not do

No parameter was moved, no target value changed, no threshold invented, no run
launched, and the 67/143 split is untouched. The non-household scope, the age gate
and the gradient channel are all named as the next levers and none was implemented,
because the arm that would measure them was stopped before its gate. **Nothing here
is a result**: no converged arm exists in F7 or F8, and no `_run.json` was written.

---

## 9.84 The demand ceiling gets its mechanism, gradient gets its channel, and the age gates close (27 August 2026, eleventh session; issues #86, #48, #49, #50, #21)

The session's `/goal` renewed the gate-loop directive — every 100 iterations,
stop on any mode heading past 20% deviation, fix the cause from the root, no
workarounds, no biasing, data and parameter tuning only — and authorised the
decisions §9.83 left open. This section records the three root-cause builds
made under it, one measurement that settled a §0 decision without a run, and
the family boundary they form. **Nothing here is a result**: every number is
an input, a build report figure, or a measurement of an earlier arm.

### The scope decision is settled by measurement: the lever was already spent

The tenth session's active lane was "widen `B.activity.escort_binding_nonhh_scope`
(§9.60) from `same_zone`". Read from `_activity_chains_report.json` before
anything was built: the §9.60 lift pass binds **49,030 of 50,014 unbound HX
tours (98.0%) at `same_zone`** on WEEKDAY (SAT 27,808/28,566; SUN 19,808/20,566),
against 126,321 passenger candidates. **The binding constraint is DRIVER SUPPLY
— the observed serve-passenger rate — not matching scope.** Widening the scope
enum could add at most ~2% more bindings (~0.08% of trips) against a ~15 pp
shortfall. The scope stays `same_zone`; the field and its sweep are unchanged;
the decision consumed no run.

### M4, the joint-tour binder: the party the generator never created (#86, #48)

§9.83 located the residual ride gap as a DEMAND CEILING — all 2,343,321 B2
trips carried `party_size = 1`, so the model structurally could not supply the
observed 20.6% vehicle-passenger share however well the escort machinery
worked. The missing travel is not chauffeuring (HX carries that at its
observed rate): it is ADULTS TRAVELLING TOGETHER — the shopping trip made in
one car, the social visit as a couple. `bind_joint_tours`
(`build_activity_chains.py`), the third binder pass on the closed day file:

- **Candidates**: a household companion's own drawn direct tour of a shareable
  purpose (`B.activity.joint_tour_purposes`, assumed, swept — HS/HO; HW and
  HE excluded in every sweep option because the one observed commute cell,
  G62 car-as-passenger 3.35% of JTW, says commute joint travel is rare) and a
  licensed co-member's direct tour of a shareable purpose.
- **Binding**: the companion's tour becomes a MIRROR of the driver's — same
  endpoints, same times, `party_size = 2` on both sides, `dest_placement =
  joint` on the outbound leg (a copy of the driver's own drawn destination,
  exactly the `escorted` sense; excluded from the drawn-share assertion in
  `check_package.py` on the same ground). ADDS NO TRIP: one activity is
  relocated to be done jointly. The #65 contiguity invariant is asserted
  before the file is written.
- **Volume**: anchored on two observed quantities and one identity.
  `B.activity.joint_tour_passenger_ratio` = 0.3503 is **derived** from the
  measured occupancy constraint (`C.constraint.vehicle_occupancy` 1.3503,
  HTS 2024/25 driver+passenger trip counts) as occupancy − 1; it multiplies
  the observed HTS Vehicle-driver share (`hts_car_driver_share()`, already a
  generator input); and the escort- and lift-covered trips already generated
  count toward the target FIRST. Deterministic seeded thinning to the target.
  **No new number enters the model.**
- **Eligibility, not outcome**: `build_matsim_plans` seeds the companion tour
  as `B.mode.bound_passenger_seed` (ride) and the driver tour as car (the
  serve-tour rule — the pairing engine pairs ride legs with CAR legs only);
  the physical pairing, boarding and ChangeExpBeta still decide what
  realises. The scored share stays emergent, so the fit remains a real test —
  the model can still fail it by under- or over-realising the eligibility.
- **Runtime coherence**: per-agent replanning splits a generated pair exactly
  as it split the escort pairs (§9.82), so `EscortCoherenceListener` gains a
  JOINT path — any household car leg whose endpoints a co-member's trip
  shares within the declared window, whatever activity it arrives at, at
  `B.ride.joint_coherence_rate` (assumed, swept [0, 0.5], **zero recovers the
  escort-only behaviour exactly**). On the joint path the offer extends to
  car-available adults — they ARE the generated population — where the escort
  path keeps its unlicensed-only guard.
- **Parties and negotiated timing, each forced by a measurement.** The first
  build bound one companion to one driver tour, once per person, nearest
  departure first: 52,713 of 114,820 WEEKDAY candidates. Allowing the party
  (several companions in one car, capped by the declared
  `B.ride.max_passengers_per_vehicle`) and repeat bindings against properly
  tracked re-timed intervals: 59,752 of 146,001. Trying EVERY household
  driver tour instead of only the nearest: 63,360 of 201,931 — which located
  the true constraint as TEMPORAL: for two-thirds of companion tours no
  household driver tour fits the companion's day as independently drawn.
  Joint travel is a negotiated departure, and the §9.60 M1 binder already
  re-times a serve tour to its passenger's departure exactly — so the same
  move lands here: an unloaded driver tour may be rigidly SHIFTED into the
  slot the companion's replaced tour vacates (durations preserved, no
  constant restated, the driver's own day and the horizon both checked, the
  #65 contiguity assertion over every re-sorted day). Final WEEKDAY
  attainment: **74,663 bindings (16,473 by shift), coordinated supply
  251,632 trips = 56% of the 448,229-trip occupancy target — ~11.5% of core
  trips ride-eligible against the 4.7% the escort path alone supplied.**
  **The household-only mechanism saturates here**: two members of one
  household must share a free window, and with independently drawn days
  they often do not. The remaining ~9 pp of the observed vehicle-passenger
  share is non-household joint travel — the #86 decision the queue already
  names — or unreachable, and the F9 arm measures which.

### Gradient reaches link travel time, as physics (#21)

§9.83 measured the cost of `not_representable`'s honest register line: 30.5%
of 50,182 road edges exceed 4% grade while modelled bike trips ran 9.21 km /
41.7 min against a measured 5.2 / 19.2. Built, behind the one-gate discipline
(`A.gradient.representation`, `absent` recovering the flat network exactly):

- `build_matsim_run_inputs.py` stamps a signed `grade_pct` attribute on every
  run-network link from the **node elevations** the A1/A6 layers already
  carry — matching by node identity survives pt2matsim's re-segmentation
  (measured on the S0 network: whole-edge matching reached 34.9% of links;
  node matching 78.6%, and 81.9% of walk/bike-capable links). Clamped by
  `A.gradient.grade_clamp_pct` (node differencing over very short links
  produces outliers no street sustains — p99 32.5%, max 283% unclamped).
  A link without both endpoint elevations stays flat and is counted.
- `citysim.GradientLinkSpeed` converts grade to a speed factor with ONE
  formula and two consumers — the router (`Router`, the
  `CappedSpeedTravelTime` discipline times the factor) and the mobsim
  (`Mobsim`, a `LinkSpeedCalculator`) — so estimate and physics cannot
  drift. Walk takes the Tobler hiking function (Tobler 1993, the same
  published source that produced A6's own `walk_speed_factor` columns;
  coefficient and offset declared, literature, swept). Bike takes a linear
  slowdown per grade percent (Parkin & Rotheram 2010; slowdown, speedup,
  floor and ceiling all declared and swept). Nothing is a behavioural
  weight: a cyclist genuinely climbs slower, and the extra seconds are
  priced by the mode's own scoring parameters.
- **The signals stack needed its own seam.** The core injects
  `Multibinder<LinkSpeedCalculator>` into `DefaultQNetworkFactory`, which the
  non-signal stack uses — but the contrib's `QSignalsNetworkFactory` news its
  link delegate PAST Guice, so a calculator added there is silently dropped
  on a signals run, and replacing the factory wholesale would silently drop
  every signal instead. `GradientSignalsNetworkFactory`
  (`src/java_signals/qnetsimengine/`, in the package because the node-side
  classes are package-private) ports the signals factory's node logic
  verbatim from the pinned jar — signals turn acceptance per the declared
  intersection logic — and swaps only the link delegate for the public
  `ConfigurableQNetworkFactory` carrying the gradient calculator. Lanes are
  refused loudly rather than half-ported. A toolchain change invalidates the
  port by construction, and a toolchain change is already a recorded model
  change (§14).

### The age gates (#49, #50)

Taxi was gated by NOTHING and `age` was consulted by nothing — 0–4 year olds
hailed 19.5% and cycled 31.1% of their trips on the F7 arm, bounding the two
gates together at 19% of the `Other` excess. No mode × age cell exists in the
held data, so both thresholds are ASSUMED, declared, labelled and swept with
**zero disabling the gate**: `B.taxi.min_unaccompanied_age` (18, swept
[0, 18]) and `B.population.bike_min_age` (12, swept [0, 16], composing with
the CWANZ ownership draw). Consumed by `AvailabilityModesCalculator` against
the person's own `age` attribute through the new `modeAvailability` config
module. No threshold is fitted to any target.

### The availability contract was porous on half the innovations: MATSim's single-trip path never consults the calculator

The first F9 probe (`20260827T152032_8it_25pct`, 8 × 25%, rc 0) measured the
age gates and found bike under-12 at exactly **zero** but taxi under-18 at
**747 trips — 5.5% of all taxi, spread uniformly over ages 0–17**. The
cause is a STOCK seam, read from the pinned jar's bytecode: with
`subtourModeChoice.probaForRandomSingleTripMode` at the declared 0.5, half
of all mode innovations run through `ChooseRandomSingleLegMode`, which is
constructed from the raw non-chain mode array and **never consults
`PermissibleModesCalculator`** — the calculator gates only the subtour
choice-set path. Every per-person availability rule this project has built
on that calculator was porous there: the same seam has leaked `ride` to
persons with nobody to drive them since §9.11, invisibly, because an
unpaired ride re-modes to physical walk and prices itself out; bike never
leaked because bike is chain-based and the single-trip path deals only in
non-chain modes.

**`GatedSubtourModeChoice`** closes it at the citysim seam: the stock
strategy chain, with one addition — after the stock algorithm runs, a trip
now carrying a mode the calculator does not permit is REVERTED to its
pre-innovation main mode. The single-trip path changes exactly one trip, so
the revert restores the valid pre-innovation plan and the refused draw is a
no-op; the subtour path draws from the filtered choice set and can never
trigger it. **When nothing is impermissible the wrapper changes nothing** —
stock behaviour recovered exactly. No draw is re-rolled and no distribution
reweighted: an illegal proposal is refused, never replaced. Verified on a
second probe before any arm.

### Gate 1 on the F9 arm: the driver's half of the pair was unreachable

The second F9 arm (`20260827T181709`, launched after the coordDistance fix)
passed the previous crash depth and ran to the iteration-100 gate. Scored on
the fit basis, F9 beat F8 on EVERY mode at equal depth — ride 4.91 vs 2.05,
Other 18.26 vs 21.96-class, MAE 10.920 at it.100 against F8's 10.348 at
it.150 — and the gate still fired: **ride was >20% off and heading away**
(9.09 → 5.92 → 4.91 across iterations 1/50/100, a ~36-iteration half-life)
while taxi rose. The arm was stopped at the gate
(`aborted_20260827T181709_1000it_25pct`).

`ride_pairing.csv` locates the decay. The pair rate among persistent ride
plans is STABLE (~0.36 from iteration 10) — plans are being ABANDONED, and
the misses say why: at iteration 100, **52% are `miss_endpoints`** — the
household no longer holds ANY car leg matching the trip, because
SubtourModeChoice moved the DRIVER's tour off car and the driver's own score
never sees the passenger's loss — with 26% `miss_window` (TimeAllocationMutator
walking the two departures apart) behind it. This is §9.82's empty-escort
wound generalised: a pair is ONE choice made by two agents, and while only
the passenger half could be re-proposed, the coherent state was structurally
unreachable whenever the driver left.

**The driver side becomes proposable** (superseding §9.82's driver-is-never-
touched clause on this measurement): for a planned ride no household car leg
serves, the listener finds the member whose own non-car trip matches it and
proposes THAT member's home-anchored subtour back to car — under the enforced
subtour structure, at the same declared rates, scored by ChangeExpBeta on the
driver's own plan, zero still recovering the one-sided behaviour exactly.
`miss_window` is deliberately not addressed in the same change: one
mechanism per arm, and the endpoint channel is twice its size.

Also measured on this arm: the §9.36/#66 stall class recurred at scale —
iteration 71 took **23,916 s (6.6 h)** and iteration 72 another 1.8 h against
a 282 s median, self-recovering, still unattributed.

### A probe blindness found on the way: `--max-persons` cannot see households

`build_activity_chains.py --max-persons N` samples `persons.iloc[::step]` — a
stride across the whole population that keeps AT MOST ONE MEMBER PER
HOUSEHOLD. Measured at 20,000 persons: 5,833 multi-member households exist in
a contiguous 20,000-person prefix, yet the strided sample held **zero**, so
`HX bound = 0` (against 72% at full scale) and every intra-household
mechanism — escort binding, joint binding — is structurally invisible to such
a probe **while the run completes happily**. The pre-change baseline shows
the identical zero, so nothing regressed; but a max-persons probe is BLIND to
household mechanisms and must never be read as evidence about them (the trap-4
class: a probe too small to see a defect will pass).

### Family F9

The joint tours change the demand and the plans; the gradient changes the
network attributes and the physics; the gates change the choice sets. All
activate as ONE boundary — family **F9**, declared in
[`run_families.json`](../audit/run_families.json) — and nothing run on the
regenerated inputs compares to F6/F7/F8. Registry 357 → **370** (+13: the
ratio, purposes, joint rate, two age gates, the gradient gate, four bike
factors, two Tobler constants, the clamp), ledger 0, reach 102/102.

### What this deliberately does not do

No mode constant moved. No behavioural weight was added. The scored
vehicle-passenger share was not written into the generator — the anchor is
the occupancy constraint's ratio and the observed driver share, the binder
supplies eligibility, and realisation stays emergent. The 67/143 split is
untouched. The measured occupancy constraint keeps its constraint role: the
arm's realised occupancy is REPORTED against [1.2493, 1.394], and an arm that
overshoots it is a failed arm, not a success.

---

## 14. Change log

| Date | Change |
|---|---|
| 2026-08-29 | **Taxi gets a finite fleet, and a refused request walks (§9.99; issue #90; thirteenth session).** §9.94 recorded taxi’s repair as blocked on the MATSim DRT contrib, absent from the pinned stack and unreachable from the sandbox. **The blocker was real and the conclusion was wrong**: a fleet needs no mobsim dispatcher, only the `BeforeMobsim` boundary where selected plans are stable — exactly where `RidePairingEngine` has paired ride legs since §9.44, a pattern already in the repository. `citysim.TaxiFleetEngine` collects every taxi leg, sorts by departure, serves greedily from the earliest-free vehicle, and REFUSES any request whose earliest vehicle is beyond `B.taxi.max_wait_min`; a refused request walks that iteration with the mode restored at `AfterMobsim`, carrying §9.81’s correction that a refusal must not delete the alternative. **Nothing caps the mode share — the supply constraint is the price, so taxi becomes emergent**, the same reasoning §9.55 applies to ride. The fleet is DERIVED, not declared: `mean(daily_trips_band) / vehicle_trips_per_day` = 20,000/25 = **800 vehicles** at full scale, scaled by `flowCapacityFactor` for the §9.88 reason, with `vehicle_trips_per_day` the one free quantity (literature, swept 15–35). Two simplifications stated not hidden: empty running is unavailable TIME rather than routed legs so dead legs load no link, and there is no spatial dispatch. Probe `20260829T171626_2it_1pct` rc=0, accounting closes: iteration 0 has no taxi legs at all, iteration 1 serves 250 of 274 and refuses 24 at 340 s mean wait, and requests then fall to 177 as refusals price taxi down — **the fleet binds under load and relaxes when it does not**, which a cap would not do. `absent` is kept and reproduces every earlier arm. **Lesson: "blocked on a dependency" deserves the same scepticism as any other claim.** Nothing here is a result. |
| 2026-08-29 | **The pairing-window correction measured at depth: real, and not the bottleneck (§9.98; issues #48/#91; thirteenth session).** The arm carrying §9.95’s corrected identity reached iteration 100. Depth-matched against the previous arm, each classified under the window it itself ran and differing in only that window: **paired_ok 37.96% → 41.53% (+3.57 pp)** and window_only 13.13% → 8.82%, with every other verdict inside 0.4 pp. The effect is larger at depth than the +1.95 pp measured at iteration 50, which is what accumulating drift predicts — but it is still about half the ~7 pp §9.95 forecast, and that forecast is not retrospectively rescued. **What it bought in ridership was +0.19 pp of ride** (7.1512 → 7.3417), with car +0.51, walk −0.52 and bike −0.19: every mode moving toward its target, all of it marginal. **The window was a real defect and never the bottleneck** — that sits upstream, in the 30.16% of ride legs carrying no declared driver (#91) and in the plan-level abandonment that turns a 19.03% seed into a 14.19% planned share before pairing is ever attempted. Recorded so it is not re-bought: widening the window further is measurably pointless, the residual window_only legs having a median gap of 344 minutes — different trips, not drift. Nothing here is a result. |
| 2026-08-29 | **A diagnostic that read today’s window into yesterday’s arm, and the third instance of one error (§9.97; issue #48; thirteenth session).** `diagnose_ride_pairing.py` took the bound pairing window from the live registry instead of from the run that executed it, so classifying a historical arm applied today’s rule to plans that never ran under it — and the reclassification is indistinguishable from a model improvement. The defect announced itself in the data: an arm that RAN a 30-minute window reported a minimum observed gap of 60.1 minutes, which cannot happen. The tool now reads tolerances from the run’s own config.xml and refuses a run that declares none. Done properly — depth-matched at iteration 50, each arm classified under the window it actually ran, differing in only that window — **paired_ok 40.07% → 42.02% and window_only 10.68% → 8.37%**, with every other verdict moving less than a quarter point. So §9.95’s derivation correction is real and touches only what it should, but it is worth **+1.95 pp, about a quarter of the ~7 pp predicted**; that prediction extrapolated from iteration 100, where drift has had twice as long to accumulate. The residual `window_only` legs have a median gap of 344 minutes — different trips at different times of day, not drift, and widening further would pair people who are not travelling together. **Recorded as a pattern: three instances this session (§9.91 a moving curve read as a level, §9.96 a number that agreed with expectation and went unexplained, §9.97 a yardstick that moved with the thing it measured) of ONE error — a comparison whose two sides were not the same kind of thing.** The §9.95 derivation itself is not withdrawn: the mutation range applies per agent, so a pair drifts up to twice it, whatever the effect size. |
| 2026-08-29 | **CORRECTION: ride’s seeded share is the uniform draw showing through, not evidence about the binder (§9.96; issues #48/#91; thirteenth session).** §9.94 and §9.95 both stated that ride seeding at 19.03% against a 20.60% target showed the demand was right and vindicated §9.84’s binder. The claim was repeated twice before it was checked, and it is wrong. A tour’s initial mode is drawn from the deliberately uniform `B.mode.seed_split` — ride at p=0.20 for car-available persons and p=0.25 otherwise — and with 76.3% of trips car-available the uniform draw alone predicts 21.2%, against the observed 19.03% with bound serve-tours seeded to car explaining the shortfall. The near-match to the target is a coincidence of 0.2 sitting close to 0.206. **Withdrawn**: that the seed vindicates the binder — whether the binder is correctly sized remains OPEN, and no measurement this session bears on it. **Corrected**: #91’s 29.76% of ride legs with no `boundDriver` is the expected consequence of a uniform seed assigning ride at random, not a demand build that forgot to bind them; the issue has been corrected on itself. **Unchanged**: §9.95’s two defects stand on their own measurements. The structural point sharpens — most seeded ride legs are random and unpairable by identity, so mode choice must discover that ride realises only for bound pairs, which is consistent with realised ride (−65.3%) trailing planned ride (−31%). |
| 2026-08-29 | **The bound pairing window was half the drift it exists to cover, and a third of ride demand names no driver (§9.95; issues #48/#91; thirteenth session).** New `src/analyse/diagnose_ride_pairing.py` reads the selected plans the engine reads at BeforeMobsim — the realised legs table cannot answer this, because `remodeUnpaired` converts unpaired ride legs before the mobsim — and classifies every declared ride leg by what its named driver was doing. **The suspected cause was wrong**: `neither_endpoint`, the household genuinely driving elsewhere, is only 1.49% of 30,363 legs, so §9.92 was right to refuse relaxing the pairing rule and is now right for a measured reason. Two real defects instead. **(1)** `B.ride.bound_pairing_window_min` was derived as `time_mutation_range_s / 60` = 30 min, but that half-width is applied to EACH agent independently, so a pair drifts up to twice it — the window was half the size of the drift it covers. 3,987 legs (13.13%) with BOTH endpoints matching exactly were refused on the clock alone, median gap 53.6 min and **minimum exactly 30.0**, the discarded boundary printing itself in the data. Identity corrected to `2 * time_mutation_range_s / 60` = 60 min; a derivation correction, not a tuning, since the value still moves only with the mutation range. **(2)** 9,036 legs (29.76%) carry no `boundDriver` at all, so the engine can only reach them by geometric discovery — filed as **#91**, a demand-build question rather than an engine one. Predicted effect of the window fix: paired share 37.96% toward ~45%. **A prediction, not a result — the arm testing it has not been run.** |
| 2026-08-29 | **The first F12 gate: the uniform seed is recoverable for car, walk and pt, and three modes diverge (§9.94; issues #48/#49/#50/#88; thirteenth session).** Arm `20260829T054941_1000it_10pct` at 108 s/it reached the iteration-100 gate and was stopped at 102 on the standing directive, with ten of twelve modes past the 20% bar. **The level is not the finding — the direction is**, because §9.92 established the seed is deliberately uniform. Converging: car 34.09 → 44.22 (target 58.16), walk 28.88 → 15.22 (13.40), pt 6.88 → 5.30 (3.80); walk travelled from +115% to +14% of target, and this is the FIRST evidence that the co-evolution recovers from the seed at all. Diverging: taxi 0.00 → 8.81 (0.99), bike 7.08 → 8.24 (2.21), ride 19.03 → 14.19 (20.60); motorbike flat at 0.18 (0.24). **Ride is the serious one** — it seeds at 19.03 against 20.60, so the demand is right and the model destroys it: planned ride falls to 14.19% and only half of that realises, a feedback loop in which pairing failure walks the leg, the ride plan scores badly, the agent abandons ride and the thinner demand leaves fewer pairing candidates. Stopped rather than spend ~21 h more reaching the innovation cutoff to confirm three divergences whose causes are already identified. **Taxi’s correct repair is a finite fleet and it is recorded as NOT DONE with its reason**: the pinned run stack resolves matsim + signals only, with no DVRP or DRT, and adding them is a toolchain change against a Maven host the network sandbox does not list. The buildable demand-side alternative — a `taxiAvail` attribute mirroring `rideAvail` — needs a point-to-point USER INCIDENCE that the package does not hold (`data/raw/p2p/` carries the Fares Order alone), and choosing that share so taxi lands on target would be fitting availability to the answer. **The honest next step is to acquire the incidence, not to assume it.** Nothing here is a result. |
| 2026-08-29 | **Three paired diagnostics: the chain effect is small, the deficit is an intentional seed, and ride/walk are one mechanism (§9.92; issues #48/#49/#50; thirteenth session).** `subtour_chain_1pct` against `taxi_fare_control_1pct` shows the random single-trip innovation is a REAL but modest effect — car 36.26% → 40.34% and walk 23.43% → 20.90% at p=0.0, about a sixth of car’s 22 pp deficit, with taxi unmoved — so it is **not** the lever and this entry records that so nobody reaches for it as one. The deficit is inherited from the SEEDED split (car 32.71% against a 58.16% target, walk 29.75% against 13.40%), and that seed is uniform **by recorded design**: `B.mode.seed_split` is "deliberately a bad guess" so that reaching the observed point is evidence about the model, and the `informed` table is kept out of the default because "seeding at the answer makes reaching the answer uninformative". **The seed is therefore NOT changed** — doing so would make every later fit a restatement of the seed. What the seed gets RIGHT is ride, 19.23% against 20.60%, which vindicates §9.84’s binder. Both arms show car jumping at the innovation cutoff (31.96% → 35.90% across iteration 32), so **every "past 20%" verdict this session produced was read in an innovation-dominated regime** and only a post-cutoff arm can judge the model. Measured and filed: ride −65% and walk +94% are the SAME 44,044 legs — 52.1% of planned ride fails to pair, and with `remodeUnpaired` none of them departs as ride, so the events record them as walk. `miss_endpoints` is not an over-strict rule (the engine’s own measurement finds no endpoint-matching driver at any hour); it is the §9.82 decoherence class, whose declared SEARCH instrument sits at 0.1 in a [0.0, 0.5] sweep. Nothing here is a result. |
| 2026-08-29 | **The iteration-50 gate fires on ten of twelve modes, and the taxi target is corrected from a commute source to a point-to-point one (§9.91; issues #49/#84/#48; thirteenth session).** The F12 arm was stopped at iteration 50 with taxi DIVERGING — 1.20% → 7.75% against a 0.19% target — and ten modes past the 20% bar; only heavy rail was inside it at −0.7%. **The first defect found was in the yardstick, not the model**: §9.87 sized taxi by splitting HTS "Other" with the census JOURNEY-TO-WORK share, and taxi/rideshare is overwhelmingly a non-commute mode, so the target was about fivefold low. `B.taxi.daily_trips_band` — the IPART 2025 point-to-point band of 15,000–25,000 trips/day across the study area, already declared and overlooked — gives **0.9916%** of resident trips, and **bike takes the residual 2.2084%** because bicycle and taxi sit in ONE survey category and cannot be set independently. One declared assumption joins the study-area count to the LGA share (`CAL.taxi.lga_concentration` 1.0, swept upward only). Measured on the arm rather than reasoned, because arithmetic and outcome disagreed: a median taxi trip is 13,072 m costing 27.13 AUD against car’s 2.35; plans with a taxi leg score mean −128.2 against −44.0; the flagfall fires (42,835 events); taxi is **7.52% even among agents holding both a car and a licence**, so it is not captive demand; and taxi is **seeded at exactly 0.0**, arriving entirely through innovation. The one unproven term is `monetaryDistanceRate` (24.14 of the 27.13 AUD), which emits no event — separated by the committed diagnostic overlay `taxi_fare_stress_1pct`. Two findings filed not fixed: the held-fixed fare rule’s OWN departure condition is now met (its "far under 12 km" premise against a 13.1 km median), and `ride` legs are 23.33% zero-distance against car’s 1.09%. `B.ride.pairing_rule` deliberately NOT relaxed — loosening an endpoint rule until more pairs match would invent shared travel the demand never declared. **§9.85’s repair is confirmed working in its first arm**: `paired_by_identity` 29 → 8,883 and `pair_rate` stopped decaying (0.4585 → 0.4794). Nothing here is a result. |
| 2026-08-28 | **Level-crossing closures stop being assumed and are derived from the mapped rail timetable (§9.90; issue #68; thirteenth session, amended `/goal` directive).** `A.crossings.closures_per_day` was 30 per site, assumed, swept 10–60, spread uniformly across 24 hours and identical at both crossings — and every arm since §9.77 ran it. The data to derive it was already in the package: a crossing closes for every train that crosses, and the city’s own mapped timetable says which. `build_level_crossings.py` now finds the mapped RAIL links at each site (held-fixed 40 m join; measured 29.6 m and 8.0 m), counts every scheduled service traversing them and times each closure from that service’s stop time at its nearest rail stop: **Saint James Road (Adamstown) 110/weekday and Clyde Street (Islington) 204**, against 30 each — 541 → 3,014 network change events. The SHAPE is the bigger correction: uniform closures put most of their closures where there is no traffic to delay, while the derived pattern peaks at 17h (9 and 14) where the road is busiest. Freight is separated out as `A.crossings.freight_closures_per_day`, point value **zero on recorded evidence** (§9.70: the coal chain is grade-separated since 2006 and does not cross these roads at grade), swept 0–30 because ARTC publishes no log for non-coal movements. `A.crossings.closure_source` keeps `assumed_uniform` as a member that reproduces every earlier arm exactly. The builder REFUSES a site with no rail link or no scheduled movement rather than emitting a silent zero that would delete the crossing while reporting success. Mode 12 gains a target — **314 closures/weekday, derived** — so with §9.89 all twelve modes now carry one and none is ungateable. Part of family F12. Nothing here is a result. |
| 2026-08-28 | **SCATS becomes an implemented algorithm and the ferry gets a derived target; family F12 opens (§9.88, §9.89; issue #73; thirteenth session, amended `/goal` directive).** The directive was amended mid-session to forbid leaving an unavailable input SWEPT where it can be DERIVED, naming SCATS as the worked example. Every arm to date ran 14 corridor intersections on a fixed 110 s plan; `ScatsSignalController` now implements the published control logic — degree of saturation measured at every signalised stop line, incremental cycle adaptation toward a target DS on the critical movement, splits equalising DS across stages, the intersection’s own clearances preserved. **Offsets are deliberately not adapted**: that library is exactly the unreleased artefact and no algorithm replaces it, so corridor coordination stays a stated limitation rather than a fabricated input. Two defects recorded: DS measured against FULL-SCALE saturation read 0.000 at a 1% sample and drove every cycle to the floor (`qsim.flowCapacityFactor` belongs in the denominator), and modular cycle arithmetic silently reinterprets past boundaries once the cycle length varies. Transit priority composes inside the same controller, and its compensation ledger becomes unnecessary — a stage that gave up green shows higher DS and the next split repays it. Probes `20260828T230050_2it_1pct` (14 systems re-timing, 110→104→98 s against criticalDS 0.564→0.282→0.141) and `20260828T230739_2it_1pct` on S2b (SCATS + green_extension together), both rc=0, accounting closes. Seven fields declared and bound; `fixed_time` kept and reproduces every earlier arm exactly; `run_matsim.py` refuses a regime that disagrees with the committed control file. **§9.89**: ferry stops being unobtained — the census G62 one-method count (40 of 1,501 PT journeys) sets its share within PT, scaled by the HTS level to **0.1013%**, `derived` with a wide 0–2x sweep, so mode 10 of 12 can finally be gated. **New comparability family F12: signal control decides corridor travel time, so nothing before compares to anything after. Nothing here is a result.** |
| 2026-08-28 | **Twelve modes get twelve individual targets, and the acceptance bar stops being typed into a script (§9.87; issues #49/#84; thirteenth session, `/goal` monitoring directive).** The NSW HTS publishes SIX categories against TWELVE simulated modes: bus, light rail, heavy rail and ferry shared ONE 3.8% Public Transport row, and a fold lets an excess in one member hide behind a deficit in the other. The acquired data document’s own category lists **evidence** `fit.py`’s existing folds rather than leaving them assumed. New city builder `build_mode_targets.py` writes `mode_targets_by_mode.csv` — car 58.1631, ride 20.6000, walk 13.4000, bike 3.0131, motorbike 0.2406, taxi 0.1869, bus 1.3039, heavy_rail 2.0922, light_rail 0.4039, ferry **unobtained**, truck 15.4698 on the classified-count denominator, freight_train **not simulated** — each row carrying the derivation it came from. **The PT split is taken on CURRENT Opal/station boardings (2025-07..2026-06), not on the 2021 census enumerated inside the Delta lockdown; the census composition sets each sweep’s far end, because the disagreement between them is real uncertainty rather than a source to choose between.** Ferry is declared `unobtained` and swept — no Newcastle ferry patronage exists in any acquired artefact, and the NSW-wide Opal ferry series identifies nothing here. Person-trip targets sum to 99.4037%; the missing 0.596 pp is resident truck-driving, named rather than folded into car. Five fields declared: three derivation choices with sweeps, plus `CAL.gate.stop_deviation_pct` 20 and `CAL.gate.pass_deviation_pct` 10 as `definition`. New framework reader `src/analyse/report_mode_ridership.py` prints all twelve modes individually with a timestamp, never an umbrella row. **Deliberately NOT added to `validation_targets.csv`** — a disaggregation scored beside its own parents would double-count and disturb the 67/143 split; `fit.py` is untouched. Ledger 0, currency 0, manifest 494, registry 377. Nothing here is a result. |
| 2026-08-28 | **A hired car is a car on the road: taxi becomes a physically simulated mode, and family F11 opens (§9.86; issue #88; thirteenth session, `/goal` precondition).** `taxi` was network-routed, link-permitted, congestion-bound and car-bodied but absent from `RUN.qsim.main_mode`, so the mobsim teleported it — **39,892 of 39,923 legs per iteration**, ~40,000 vehicle-trips of road space missing from every link and count station while `car` read −19.4% and the `bike+taxi` fold read +471.2%. The fix is one registry enum; nothing else needed building. The taxi body restates `RUN.qsim.car_vehicle` exactly rather than declaring a second one, and **empty running (deadheading) stays unobserved rather than becoming an assumed multiplier**. Probe `20260828T220751_2it_1pct` rc=0, accounting closes: **197 of 197 taxi departures enter traffic, 29,994 link traversals**, all 2,300,485 link-entry events attributed to a vehicle class. Also measured there: `ride` is 1,166 of 2,101 legs physically boarded (44.5% teleported) — a DEMAND failure §9.85 addresses, never to be closed with a phantom vehicle per passenger; §9.85’s `boundDriver` is live (`paired_by_identity` 98 at iteration 2, `pair_rate` 0.5410 → 0.5030 → 0.5224, not decaying). **New comparability family F11: network loading changed, so nothing before it compares to anything after. Nothing here is a result.** |
| 2026-08-28 | **The joint binding does not survive translation, and the pair is re-found with the clock the model itself moves (§9.85; issues #48, #86, #49, #50; twelfth session).** The F9 gate-2 arm was stopped on the iteration-100 gate with all five scored categories past 20% — Other +471.2%, pt +123.4%, driver −19.4%, ride −76.3%, walk +55.2%, mean abs error 10.864 pp — and §9.84's driver-side pass measured INERT against the previous arm at equal depth (10.920 → 10.864, ride 4.91 → 4.87). The located cause: all three B2 binding tables NAME the driver, `build_matsim_plans.py` read that identity for seeding and DISCARDED it, so `RidePairingEngine` re-discovered every declared pair from geometry plus a 15-minute window — while MATSim's `TimeAllocationMutator`, at an UNDECLARED ±1800 s default, moved the two members apart independently. Measured: 73.8% (joint) / 67.4% (escort) / 80.5% (lift) of bound ride legs still had their declared driver on the same OD BY CAR, but only 60.6% / 42.6% / 64.5% fell inside the window. The driver is present, driving the same trip, and refused on the clock — which is why §9.82's and §9.84's repairs were both inert, each re-identifying through the window the drift had already exceeded. Built as family **F10**: `boundDriver` carries the identity for all three tables (158,898 persons); `RUN.replanning.time_mutation_range_s` is declared and swept; `B.ride.bound_pairing_window_min` is DERIVED from it, relaxing IDENTIFICATION only, with the inferred window unchanged at 15 min and a bound window narrower than it REFUSED. Caught before it could report a false success: `JointRideEngine` still bounded the physical wait by the narrow window, so the pair rate would have risen while nobody boarded (trap 6/7) — `Booking` now carries its own tolerance. At iteration 0, before any drift, `paired_by_identity` is 7 of 62,359. Registry 370 → **372**, ledger 0, doc-currency 0. **Nothing here is a result**: no arm has reached a gate on this boundary and the repair's effect is not yet measured. |
| 2026-08-27 | **The demand ceiling gets its mechanism, gradient gets its channel, and the age gates close (§9.84; issues #86, #48, #49, #50, #21; eleventh session).** Three root-cause builds under the renewed gate-loop `/goal`, forming family **F9**: `bind_joint_tours` generates adult joint household travel as pairs — companion tours mirroring a co-member driver's tour, `party_size` 2, volume anchored on the measured occupancy ratio (0.3503 passengers per driver trip, derived) times the observed driver share with escort/lift coverage counted first, eligibility only, realisation emergent; gradient reaches walk/bike link travel time on BOTH router and mobsim sides (`grade_pct` stamped from A1/A6 node elevations, 81.9% of walk/bike links matched; Tobler for walk, Parkin & Rotheram for bike, all constants declared and swept; `GradientSignalsNetworkFactory` ports the signals node logic so signals and gradient survive together); and the taxi/bike age gates land as declared, swept, zero-disables fields. One §0 decision settled by measurement WITHOUT a run: the §9.60 non-household scope lever was already 98% consumed at `same_zone` — the binding constraint is driver supply, so the scope stays. Found: `--max-persons` probes stride-sample one member per household and are structurally BLIND to every intra-household mechanism. Registry 357 → **370**, ledger 0, reach 102/102. The scored share was not written into the generator; occupancy keeps its constraint role. Nothing here is a result. |
| 2026-08-27 | **The gate was being read on the wrong quantity, and the ride gap is a demand ceiling (§9.83; issues #48, #49, #50, #30; tenth session).** No run was launched and no model or data value changed. The §9.81/§9.82 gate loop had been reading whole-scenario LEG counts (`modestats` planned, or events realised) while `fit.py` scores linked main-mode TRIPS for target-LGA residents; MATSim's per-iteration `<n>.trips.csv.gz` carries that quantity and was present in every arm at iterations 0, 1, 50, 100, 150. New `src/analyse/measure_iteration_modes.py` reads it through `fit.py`'s OWN `score_mode_share`. **This inverts one verdict — car is not over-chosen but 11.7% UNDER (52.12 vs 59.00)** — and shows `fit.py` folds bike and taxi into ONE target, so the two over-chosen modes compound into a +18.11 pp miss. Scored at iteration 150, mean abs error **10.991 (F6 unfixed) → 10.460 (§9.81) → 10.348 (§9.82)**: both repairs work, every category improved, none regressed, ride 0.61 → 1.39 → 1.61, and together they close 7.8% of the ride gap. **CORRECTION to §9.82, which stays as written**: its 8-iteration probe's pair-rate "reversal" is the innovation cutoff at 0.8 × 8 = 6.4, not convergence — the 1000-iteration arm kept falling through the same iterations. The residual is a DEMAND CEILING, not a choice defect: **every B2 trip has `party_size = 1`**, escort-bound travel is 5.4% of trips against an observed 20.6% vehicle-passenger share, and two measured observations agree (occupancy 1.0013 vs the measured 1.3503; ride 1.61% vs 20.60%). This is the measurement §9.55 named as decisive, and the displaced mass lands in bike +8.82, taxi +9.29, walk +4.12 and pt +3.64 pp. Two further causes measured and NOT acted on: **taxi is gated by nothing** and `age` reaches nothing (0–4 year olds take 31.1% of trips by bike and 19.5% by taxi, but this bounds at 19% of the excess); **gradient reaches mode choice through nothing** on a network where 30.5% of 50,182 edges exceed 4% grade, with modelled bike trips at 9.21 km / 41.7 min against a measured 5.2 km / 19.2 min. The F8 arm was stopped on instruction at iteration 163 of 1000, before its gate, and closed out as `aborted_20260826T233658_1000it_25pct` with a measured cause. No target moved, no threshold invented, the 67/143 split is untouched, nothing here is a result. |
| 2026-08-26 | **The escort drives and the escorted cycles (§9.82; issues #48, #50, #30; ninth session).** The §9.81 arm was stopped at its iteration-200 gate: the ride-alternative restore WORKED (ride legs 87,019 / 85,873 / 86,118 against the unfixed 28,228 / 25,889) and was NOT SUFFICIENT - realised car 47.90, bike 9.97, taxi 8.36, ride 0.95. F7 and the unfixed arm agreed within 0.15 pp on car, bike, taxi and pt while ride and walk traded ~10 pp, which is how the second cause became visible. Measured at iteration 150: **84.53% of trips arriving at an escort activity are car while only 11.45% of escort-bound members ride** - the escort tours run empty, suppressing ride and inflating car and bike together. B2 generates escort travel as a pair and SubtourModeChoice moves one agent at a time, so no per-agent strategy can propose the two-sided state. `EscortCoherenceListener` PROPOSES the coherent plan back and ChangeExpBeta decides; the driver is never touched. The only assertion is that two people travelling together travel by the same means. `B.ride.escort_coherence_rate` is a SEARCH rate whose zero recovers the previous behaviour exactly. Registry 356 -> 357, reach 92/92. Family **F8** declared. Nothing here is a result. |
| 2026-08-26 | **A missed pairing was deleting the ride alternative, and the model was walking back to its pre-repair answer (§9.81; issues #48, #49, #30; ninth session).** The first F6 arm was stopped by instruction at iteration 200 with car 54.33%, ride 0.41% and taxi 9.47% (whole-scenario legs). `RidePairingEngine` was MUTATING THE PLAN when a ride leg failed to pair - 95.7% of the 61,409 iteration-0 misses were gone by iteration 1 and never returned, an exponential decay with a 36-iteration half-life toward the pre-repair 0.0013 occupancy. Those destroyed legs were 23.5% of all walk legs as ~9.7 km forced walks, the pool replanning turned into taxi. The forced walk is now an EXECUTION, restored at AfterMobsim so the walk is still scored and the alternative is still there; §9.55 is kept, no parameter moved. A window hypothesis was REFUSED BY MEASUREMENT (median gap 253.7 min; widening 15->60 would recover 13 legs of 1,529), and the funnel reordered geometry-first. Family **F7** declared. Nothing here is a result. |
| 2026-08-25 | **The front door shows the model's fit, a dead run states its cause, and two documents stop duplicating the record (§9.80; issue #84; eighth session).** `README.md` described the package and never said whether the model reproduces the city, and described the corridor's signals only as an input that could not be obtained - nine days after §9.77 made signal control mechanical. New `src/analyse/build_fit_figures.py` generates the modelled-against-observed panels (mode share, the trip-length constraint, the 30 counts) from the run the calibrated base was written from - selected via `C5_calibration.json`'s `best_tag`, so the figures and the calibration report always describe the same arm - as dependency-free SVG carrying no wall-clock, which is what lets `--check` gate them in `check_package.py`. **CORRECTION: the light rail's 1,260 boardings had been reported as a -63% error against V001/V002, targets `fit.py` marks UNSCORABLE** because 2019-20 is a pre-pandemic market against a 2026 base (§12.1); the modelled figure is a LEVEL, the gap is not a fit statistic, and the framing had propagated through `CORRIDOR_PT_COMPOSITION.md` and three handover briefs - corrected there, banned in the generator, written into both skills and the handover contract, filed as #84. **`_meta.json` now REQUIRES a `cause` on `failed`/`aborted`**, read from the run's own `matsim.log` by new `src/run/run_failure.py` (terminating exception + `Caused by` chain + the line it came from); all fourteen dead runs backfilled from their logs, the three 25 August probe failures independently reproducing the §9.77 narrative; `results/INDEX.md` prints every cause. `check_doc_currency.py` gains `decimals` and a `text` claim kind (a stale NAME was structurally exempt), ten new README claims, and one stale-statement ban covering every phrasing of "the package is not built yet" - the §9.79 ban named one wording and the same false claim survived under another. **`P4_CHECKPOINT.md` retired as a live document and frozen as the 12 August record it was**: it restated `STATUS.md`'s job, had drifted on deliverables, issues, manifest, registry, mode share, relaxation, counts, walk ratio and SUMO scope, and held nothing the record does not. `docs/README.md` (five output schemas against seven, two `tests/` checks against four) and `.claude/CLAUDE.md` (four premise corrections against five) corrected. **No model or data value changed, no registry field moved, no run was launched, no target moved, the 67/143 split is untouched, and nothing here is a result.** |
| 2026-08-25 | **The living documents are pinned to the artefacts, and a stale counts attribution is filed (§9.79; issue #82; seventh session).** An `/onboard` gap scan found `README.md` three phases out of date - a 376-row manifest against 489, a 210-field registry against 356, a road network 7,070 edges short, 612,680 agents against 612,687 - plus two statements that were false rather than stale (`networks/osm/` described as empty and the #32 re-harvest as pending, nine days after it ran and closed). `STATUS.md` carried the same figures and disagreed with its own P3 phase row; `.claude/CLAUDE.md` put the hardcoding ledger at 95 when it is 0. The mechanism was DUPLICATION: two documents holding one figures table, and the two session skills each holding their own copy of the six state-of-the-project questions. New: `tests/check_doc_currency.py` (portable harness, `--strict` gates CI) over `cities/<city>/tests/doc_currency.json` (22 city-owned claims), pinning every live figure to the artefact that decides it and banning two named false statements; `docs/HANDOVER_CONTRACT.md` defines the six questions, the trust order, the environment gate and the facts-that-expire rule ONCE for both skills. **A dated record stays frozen - only live-state cells are pinned.** Found while checking and filed rather than fixed: the calibration report justified unfitted counts by the absence of a through tier that §9.41 built and §9.64 measured as making no difference - the generator now states the supersession and the -91.8% residual across 30 stations (6 modelled-zero) is issue #82. **No model or data value changed, no run was launched, no target moved, the 67/143 split is untouched, nothing here is a result.** |
| 2026-08-25 | **THE ACTIVATION BOUNDARY IS CROSSED — family F6 (§9.77; #73 #68 #74 #49; sixth session).** The §9.76 checklist executed as ONE boundary by the session's directive: `A.signals.representation=explicit_signals` (generated fixed-time plans at the 14 corridor intersections in every set; signalised approaches re-capacitated to saturation flow on the emitted run networks; each variant's OWN embedded tram delay removed from the schedule the day-type filter reads — the dwell transform riding inside it); a new declared gate `A.crossings.representation=change_events` puts the two freight level crossings into every config as a time-variant network (540 events, 16 links); `RUN.travel_time.bin_size_s` 900 → 300; `qsim.usingFastCapacityUpdate=false` written into every signal config; `taxi` into `RUN.mode_choice.modes`, `RUN.routing.network_modes` AND `city.json` — the §9.76 inert plumbing (blended Fares Order 2025 rates, the `fare` module, congested-network travel time) engaged unchanged. All 30 run-input sets regenerated; **family F5 closes UNMEASURED (the recorded cost of activate-first; its inputs regenerable from the declared switches)**. S3's priority is bus-keyed via the new `A.signals.tsp.priority_group` (`corridor` in S3's overlay). Three defects were caught by PROBES, not reading: the crossings XML violated the schema's element order (flowCapacity before freespeed); the S3 mid-block systems NPE'd the priority ledger on a null payee; a console line hardcoded a not-modelled row. Verified at plumbing scale only (S2 + S3, 1%×2, rc=0; all 14 S3 `CitysimTramPriority` controllers instantiate). **No arm ran, no target moved, the 67/143 split is untouched, nothing here is a result; the first F6 arm still requires its own stated-cost approval.** |
| 2026-08-25 | **The runless lanes close out (§9.78; #49 #50 #62 #63 #66; sixth session).** Tier C: PT submodes SCORE-DISTINCT via SwissRailRaptor mode mapping (verified against the pinned jar's bytecode; the stock main-mode identifier's interchange crash pre-empted by `PtSubmodeMainModeIdentifier`; probe shows zero `pt` legs — bus 1,414 / rail 450 / tram 10 / ferry 3 — with trip labels and per-submode conservation intact; behind `RUN.routing.pt_submode_scoring`, folded into F6 while it has no arms). Seven 0b source upgrades: `min_green_s` → literature (TfNSW TTD 2018/002), five tolerances/search bounds → definition, and **`B.population.bike_available_rate` assumed 0.5 → literature 0.493** (CWANZ NSW 2025, p.72) with the B plans regenerated on the cited value. The corridor-composition question ANSWERED on arm A (a diagnostic, not a result): COVERAGE carries the bus-over-tram split — 98.3% of corridor-band demand has an end the 6-stop alignment cannot reach without the interchange the through-running buses avoid; the transfer penalty prices it; frequency exonerated. The demographic measurement recorded (#50): the modelled split is sex-invariant against G62's real sex structure; NO mode × age cell exists in the held data. The systematic TIA sweep came back EMPTY (19 applications; PPSHCC-137 stays the only SCATS evidence; PPSHCC-306 corrected to East End 105–121 Hunter St). #66's settlement mechanised (Defender/TaskScheduler capture on the stall transition). #62's six strata landed: `light_rail_boardings` → `intervention_boardings` (an ACCEPTED schema break — pre-rename run records cannot be scored, the `target_lga_pct` precedent), manifest lineage into the city descriptor (manifest byte-identical), currency/base-year tokenised (the agnostic fixture passes at AUD_2031), layers.json parameterised, `check_package` split into a portable harness over city-owned expectations (1,433 checks, nothing dropped), the reader-shape contract + Newcastle adapter (HTS/counts readers byte-identical; the census family recorded as remaining source-shaped). **No target moved, the 67/143 split is untouched, nothing here is a result.** |
| 2026-08-25 | **TOOLCHAIN CHANGE: SUMO 1.27.1 removed; Apache Maven 3.9.9 and the MATSim signals run stack pinned (§9.76; #72, #73; overnight fifth session).** The SUMO component leaves `.tools/toolchain.json` (the §9.74 descope executed — no completed run ever consumed a SUMO artefact, so nothing is invalidated); Maven 3.9.9 is pinned by sha256 from Maven Central; the committed `src/java/run-stack-pom.xml` resolves `org.matsim:matsim` + `org.matsim.contrib:signals` at **2027.0-2026w25** — exactly the version the pinned shaded jar embeds (§9.73) — into `.tools/run-stack/lib` (201 jars, each sha256-recorded; visualisation-only dependencies excluded). Signal-enabled runs execute `citysim.CitysimSignalsControler` on that stack; every other run executes the unchanged shaded-jar stack, and the two never share a classpath. `bootstrap_toolchain.py --verify` re-hashes both and compiles both class trees. |
| 2026-08-25 | **Batch 4.7 BUILT, INERT (§9.76; #49 #62 #63 #68 #70 #72–#78; overnight fifth session).** Harness safety set LIVE (warm restart with the recorded non-bit-identity caveat; the `_progress.json` digest with the declared pace band and solo-check window; the cross-run index over declared families; the detached Task Scheduler launch path VERIFIED past `PersonPrepareForSim` with the launcher gone). Model-changing set BUILT INERT for ONE boundary: level-crossing closures derived from OSM barrier tags with the Stewart Avenue exclusion asserted; native charging dwell (concurrent-with-boarding DECIDED) holding intermediate stops with anchors preserved; explicit corridor signals + tram-priority controller with both §9.75 toy probes PASSING, the double-count rule landed as artefacts (saturation re-capacitation + per-variant embedded-delay schedule removal) and the per-green discharge check reported; taxi as one blended priced mode on the archived Fares Order 2025 (flagfall $5.00 / $2.52/km urban — correcting the dossier's $5.17/$2.61, values not in the instrument). Six 0b fields moved onto measurement (weekend headway 1.875; shuttle speed CONFIRMED at 26; spans; the LR regulated ceiling; the segment count) and the departure-profile constraint filed its first finding (weekend shapes skew 3–4 h late). PPSHCC-137 archived with provenance under the decided free-TIA route (site corrected to 643 Hunter St). The assembled 4.6.9 run inputs are byte-identical; no run, no result, no boundary crossed. |
| 2026-08-25 | **Build reports record city-relative paths, and the record's vocabulary is normalised (fourth session, follow-up; no model value changed).** Three committed build reports (`_matsim_build_report.json`, `_corridor_attributes_report.json`, `_plans_report.json`) and the calibration report carried this machine's absolute checkout path in `feed`/provenance strings — the §9.67 entry had noted them as true-until-rename. The four producing scripts now pass those paths through `city.rel()` (the module that already renders manifest paths city-relative), the committed reports were normalised to the same city-relative form, `CALIBRATION_REPORT.md` was regenerated by its generator, and the manifest re-hashed. The role word "owner" is retired from the living record, GitHub issues, PR bodies and comments in favour of decision-required/standing-directive phrasing; issue labels normalised (phase + `awaiting-implementation`/`awaiting-run`/`decision-needed`); the `/handoff` and `/onboard` skills made city-generic (`cities/<city>` via `CITYSIM_CITY`). The local working-copy folder renamed to `work/city-digital-twin`. **No model, data or target value changed; the 67/143 split is untouched; nothing here is a result.** |
| 2026-08-25 | **The signalling dossier lands, operated SCATS data is discovered public, and the all-modes-first batch is set (§9.75; issues #49/#68/#72–#78; fourth session).** A ten-file SCATS/Newcastle-signalling research dossier lands at `design/signalling/` (every claim tagged documented/commonly-claimed/gap; `A.signals.scats_phasing` STAYS `unobtained` for the 14 modelled sites). Discovery: planning-portal TIA PPSHCC-137 republishes TfNSW-supplied SCATS interpreted history for TCS 923 and TCS 1138 (24 h × 15-min, 19 Jul 2022) — operated cycles 72–81 s corridor-adjacent / 104–113 s arterial vs the assumed 110 s swept 80–140 s: sweep-basis evidence (neither is a modelled site), and a free third acquisition route parked with the LX-purchase decision on #78. Standing directive: the next session implements corridor signals + tram priority + lanes natively (#73, with the Maven run-stack toolchain change), taxi as a priced mode (#49 — supersedes §9.42's after-deliverable-5 sequencing), level crossings (#68), native charging dwell (#74), the descope execution (#72), warm restart (#75), the progress digest (#76) and the cross-run index (#77) — activating as ONE family boundary; the 4.6.9-first-vs-fold-in ordering is stated in §9.75. **No code built, no model, data, registry or target value changed, the 67/143 split is untouched, nothing here is a result.** |
| 2026-08-25 | **SUMO is descoped by recorded decision — MATSim is the single simulator (§9.74; issue #72; the fifth premise correction, superseding proposal §5's twin-simulator architecture).** Every SUMO-deferred corridor question except two has an adequate native representation (crossings #68, dwell #74, taxi #49, lane loss via E1, frontage volumes from physical walk); the residual lands as: S-b answered natively when #73 builds (a swept band regardless, per §7.2/§9.21), reliability variance descoped as a stated limitation (the ≥30-replication load never fit this machine — #6's record), deliverable 7/§9.16 retired with the outer loop, P5 tasks 5.1/5.2 deleted (the standing 5.2 DELETE proposal thereby decided) and 5.3 resolved to stays-swept-never-pinned. Mechanical retirement (registry `RUN.sumo.*`, the toolchain fetch, package checks, manifest) is #72, a logged toolchain change when executed. **Nothing deleted from history, no registry value changed in this record, no run invalidated (none ever consumed a SUMO artefact), no target moved, nothing here is a result.** |
| 2026-08-25 | **MATSim re-affirmed against the 2026 field, and the embedded MATSim version recorded (§9.73; fourth session).** A documented survey (BEAM ~10× slower with actor nondeterminism; POLARIS fast but licence-gated, C++, determinism/GTFS-fidelity unverified; SimMobility/mobiliti/TRANSIMS dormant; DTALite/GPU assignment-only; commercial closed) rejects migration — every faster framework drops co-evolutionary demand, transit fidelity, open reproducibility or Windows. The pinned `pt2matsim-26.6-shaded.jar` is verified from its own Maven metadata to embed `org.matsim:matsim` **2027.0-2026w25** (current-generation weekly, not 16.x); digest unchanged, nothing re-pinned; DSim recorded watch-only. **No toolchain, model or data value changed; nothing here is a result.** |
| 2026-08-24 | **Two silent launch deaths end the first post-repair arm attempt; no model or data value changed (§9.72; issue #70; third session).** The session's `/goal` authorised the 4.6.9 base arm; two detached launches (`Start-Process`, then WMI `Win32_Process.Create`) both died silently — ~54 s in mid `PersonPrepareForSim`, and ~2 min in before config emission — with no error artefact, and the campaign was ended at `/handoff`. Both closed out as `aborted_*` with cause-stating `_meta.json` (§9.66 scheme). Attribution open (#70; agent-session process reaping suspected); operative rule: launch arms from an interactive shell outside the agent session and verify past `PersonPrepareForSim`. Standing directives recorded: no run approval standing (the `/goal` approval is spent); arm B launches only if arm A's solo iterations 2–5 pace at the closed family's 217–253 s/it band. No target moved, the 67/143 split is untouched, nothing here is a result. |
| 2026-08-24 | **The ride collapse decomposed and repaired in the demand build, the short-trip mass gets its observed distribution, and two 0b items become measurements — a NEW comparability family (§9.68–§9.71; issues #48/#31/#30/#63/#68; /goal directive).** The decomposition read the completed arms (no new run): 76,986 of 77,626 ride-available persons held NO ride plan in final memory (an ASC could flip 109), return legs paired at 0.0079 and intermediate at 0.0 across the search — the §9.64 "supply is not binding" reading was survivorship bias, and the uniform seed's 0.2 car probability WAS the 0.196 outbound pairing ceiling. Repairs, all declared and swept: round-trip serve-tour allocation in both binder passes (household pending-pickup ledger; non-household all-or-nothing pairs), direct bound tours, serve tours seeded car, round-trip-covered passengers seeded ride, `liftHousehold` a comma list unioned into one sampling cluster. The gravity draw becomes a two-component mixture per purpose against HTS Sydney 2012/13 Table 4.4.7 band shares (18.8% of trips ≤1 km observed vs 4.45% generated), short kernel mean = the held observed walk mean, every observed per-(purpose × LGA) mean still met exactly. B2/plans/30 run-input sets regenerated (WEEKDAY: 26,638 household + 24,515 non-household round-trip-covered tours; band shares exact on every purpose); 1% probe rc=0, accounting closes, **return legs pair 347/347 at it-2** (old family: 2 of 2,818), pairing occupancy 0.12 vs the converged 0.0013; `check_package` ALL PASSED, manifest 436. Freight rail researched: the coal chain (~110 movements/day, ARTC/PWCS/NCIG) runs on dedicated grade-separated track and is deliberately NOT simulated; the two real road interactions (Adamstown + Islington level crossings) are #68. 0b: `A.corridor.pre_lr_lanes_per_dir` measured from OSM history **2 → 1** (every tagged pre-2017 segment one lane/direction; attic responses landed with provenance, ODbL) — hypothesis B3's counterfactual onto evidence; the VoT set checked against EPV Jan 2025 (HE and concession divergent, flagged, values unchanged). #50's modelled mode × demographics table delivered from arm A. **The §9.58–§9.63 family CLOSES with the two completed arms as its record; nothing run on the regenerated demand compares to them. No target moved, the 67/143 split is untouched, and nothing here is a result.** |
| 2026-08-24 | **Runs name, describe and status-track themselves, and the project is city-digital-twin (§9.65–§9.67; standing directives).** The run harness now names every run directory itself — `<launch yyyymmddThhmmss>_<iterations>it_<pct>pct` — and `--tag` is gone from every caller; run identity moved fully into the `_run.json` parameter set (resume scans records, prefers a matching controler hash, and no longer deletes a stale run on a controler change). Every run carries **`_meta.json`**, a schema-checked status card (`running`/`completed`/`failed`/`aborted` + started/ended/parameters) written at launch and updated automatically at every transition, with stale `running` states reconciled by pid at the next harness start; a dead run is renamed **`aborted_<name>`** in place and the `results/_aborted_<date>/` quarantine parents are dissolved. All 35 existing run directories were renamed (maps in §9.65/§9.66) and backfilled with metadata derived from their own records — nothing invented, backfilled cards say so. **The repository is renamed to `city-digital-twin`** (from the earlier Newcastle-specific name) (GitHub redirects stand; schema `$id`s and identity docs updated; `CITYSIM_*`/`citysim` stay with the open naming issue). The board's stale open-issue count was corrected against live GitHub (8 open, 42 filed, 34 closed). **No model or data value changed, no run was made, no target moved, the 67/143 split is untouched and nothing here is a result.** |
| 2026-08-24 | **The first converged all-physical arms complete, and C5 exists (§9.64; issues #48/#31/#30/#28/#14/#9).** Both §9.62 arms ran 1000 iterations to `relaxed: true` (drift 0.031 pp) with events-based conservation closing on every mode — the first valid runs of the §9.58–§9.63 family, ~67.4 h each under the two-arm pattern. Fit (35 of 67 calibration targets scorable, MAE 10.65 pp): driver +14.19, **passenger −20.51**, walk-only −6.12, bike +8.01, pt +4.42; submodes split per Tier R (tram 0.02%); **light rail 1,260 modelled weekday boardings vs 3,417 observed**. The central measurement: **ride collapses under SCORING, not physics** — ~6,800 ride legs/iteration until the cutoff, ~540 after selection, 100% of survivors paired and physically boarded, 0 capacity refusals across 1000 iterations — so M2 (driver detours) is a NO-GO and the next lever is demand-side choice (decision required). `params/C5_calibration.json` written from arm A under the §9.50 constrain-and-report branch (objective 10.65, **feasible=False, five violations STATED**); the calibration report regenerated; #14/#9 CLOSED. **The seed noise floor is measured from arm B (n=2): ≤0.11 pp per mode, LR boardings ±3.9%** — the `E.replication.n_replications` input the record has waited for. The count fit (−91.8%, 6 modelled-zero stations) is statistically unchanged from the previous family (−91.05%): the recorded no-through-demand structure, not a new defect. No target moved; the 67/143 split untouched; the fit rows are the base model's report card — **nothing here is a finding about the light rail** (no counterfactual has run). |
| 2026-08-21 | **The two-arm relaunch launched, crashed on both seeds, and was repaired the same afternoon (§9.62, §9.63; issue #65).** Approval was given for the §9.59 two-arm pattern: arm A `phys1000a_25pct` (the base arm, master seed) + arm B `phys1000b_25pct` (`RUN.machine.seed` 20260811 — the field's replication clause exercised for the first time), qsim 8 + events 4 + xmx 30g per arm (the driver pins -Xms to -Xmx; two 40g heaps would commit 80 GiB on 63.5). Both arms died at their FIRST replanning: MATSim refuses a subtour mixing chain- and non-chainbased modes, and 152 sampled persons carried one — the §9.60 M1 pass checked a second lift binding against a sibling tour's STALE pre-retarget times, two lifts per driver could overlap, and the chronological splice interleaved their tours (1,191 WEEKDAY / 305 SAT / 137 SUN persons; per-tour modes then alternated inside one home-anchored loop). The 1% probes could not have caught it (~6 affected persons at that fraction — verified-at-1% is not verified, §9.10's rule again). Repair: the busy check consults re-targeted sibling times, and a post-splice assertion refuses to write a demand whose tours are non-contiguous in trip_seq. B2/plans/run-inputs regenerated: 0 interleaved persons, 0 mixed subtours in all 621,722 weekday plans; weekday lift bindings 55,280 → **55,249** (31 overlaps now correctly skipped). Free at the family boundary — no completed run existed. No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-21 | **Deliverable 0b: three assumptions became measurements from data already held, and the chain-timing constants surfaced (§9.61; issue #63).** G15 was in the package all along (the "not in the package" claim in `build_population.py` and the age-structure dossier was FALSE): the 18+ tertiary full-time split is now OBSERVED per SA1 and the assumed field is retired. The hourly permanent counts settle what the AADT aggregates could not: **SAT:SUN = 1.1473** (assumed 1.1875), external weekend scaling **0.8429/0.7347** (assumed 0.4/0.3 — weekend boundary demand roughly doubles), and the 1 h weekend departure shift measured EQUAL to its assumption (12 stations, 33,753 clean station-days, the §9.49 method verbatim); three assumed fields retired, the build refuses to run without the measured artefact. The B2 scaffold speeds (26/16 km/h + 240 s) left their expressions for declared, swept fields. B1/B2/plans regenerated on the full population; manifest 429; `check_package` ALL PASSED. The remaining ranked backlog (two attended acquisitions, the Overpass attic query, ~25 reclassifications) is issue #63. No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-21 | **The non-household-lift gap gets its physical mechanism (§9.60; issues #48/#31/#28; /goal directive supersedes §9.55's report-only stance).** M0: a booked passenger physically WAITS at the meeting point for the driver's car, bounded by the declared pairing window, and a timeout completes on the Tier-1 clock counted from the timeout — no new number; the old missed(gone/absent) boarding classes measure 0 at the verification probe. M1: unbound serve-passenger tours — generated at the OBSERVED 10–19.5% rate, un-placeable by the §9.46 household binder — are re-targeted to driverless-household passengers in the declared scope (same SA1, swept): **WEEKDAY binds 55,280 of 55,614 (99.4%)**; the serving leg departs at the passenger's own departure from their O to their D, so the unchanged pairing rule matches it and the unchanged JointRideEngine physically boards it. ADDS NO TRIP; the binding is an eligibility, never a guarantee; ride stays emergent; sampling co-clusters bound household pairs (the §9.45 class one level up). M2 (bounded driver detours) designed and deferred to the converged arm's measurement; M3 (declared allowance) rejected as teleportation/invented data. Who-drives-whom stays unobserved — the household/non-household split is REPORTED, never fitted. No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-21 | **Every wall-time knob declared and probed, and the 10× ask answered by measurement (§9.59).** The §9.57 arm's forensics: mobsim 64% / replanning 26% / prepare 8% of a 226 s median; 134.5M events per iteration; the it-110 outlier explained (one PlanRouter pass poisoned by the walk-gridlock knot ran 7,594 s). FIFO link dynamics — MATSim's silent default — let a 1.25 m/s pedestrian hold a link's queue head against the cars behind it, contradicting §9.54's declared PCE-0 semantics: **`qsim.linkDynamics = PassingQ` declared on correctness**, at a measured ~42 s/iteration price over FIFO. Probes (25% × 5, one at a time): `replanning_threads` = 20 is the one clean win (replanning 76→33 s); events 12 buys nothing over 4; `synchronizeOnSimSteps=false` is a 65 s REGRESSION; `oneThreadPerHandler` is measured FATAL — each verdict recorded on its declared field. The declared stack runs ~233 s/iteration → **~65 h/arm**; `-Xms` pre-sizes the heap; `create_graphs` declared for long arms. The repaired model is not faster than the wedged one — it simulates MORE (the aborted 11.6k legs/iteration now walk their whole day). **~10× per iteration is not reachable without shrinking the physical work; the available multiplier is two concurrent arms** (family throughput doubles; iteration count survives contention, duration does not). No target moved; nothing is a result. |
| 2026-08-21 | **#60 verified to be a different defect than filed, and the walk wedge repaired four ways — a NEW comparability family (§9.58; issues #60/#48/#30).** The pinned engine's bytecode refutes the filed suspicion: the qsim never reads `disallowedNextLinks` (its only refusal conditions are null/absent/disconnected next links) while the routers apply them PER MODE — so car/bus routes comply via routing and walk never had a restriction to violate. All 491,349 refusals are first-hop topology breaks: 6.81% of activities sat on links outside the walk/bike subnetworks and MATSim's `decideOnLink` silently started routes at the nearest in-network link while the qsim inserted the vehicle at the activity link — ~11.6k walk/bike legs aborted mid-day per iteration, flattering to car. Repairs: `pedestrian_excluded_classes` corrected to the actual road rules (motorways only — excluding trunk severed the walkable city); ONE reverse walk/bike complement per one-way street (16,603 on S2; a dismounted cyclist wheels at the declared walking speed by identity); `ActivityLinkAssigner` pins every activity to a link carrying every network mode its person can use (config-derived, incl. walk for transit persons whose raptor fallback is a network walk; boundary agents keep their gates); SubtourModeChoice restricted to `person` via a declared schema restrict clause (405 externals had mode-innovated off their measured cordon counts by iteration 100). Probe-verified refusals 3.8k/iteration → **0**, before and after the demand regeneration. Reporting: #49 Tier R — the pt umbrella is split by scheduled submode in every table, and intervention patronage is attributed by the declared `intervention.mode`, not a name heuristic. No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-21 | **The first all-physical arm: decided at the full 1000, launched, measured, stopped (§9.57; issues #30/#48/#60).** ~500 iterations considered and REJECTED on both arms' trajectories (reference: car +2.14 pp between 500 and 790; attempt: car still +3.3 pp/25 it at 133). `phys1000_25pct` ran 135 healthy iterations at median ~234 s (one 7,867 s walk-knot outlier, self-recovered, §9.36's family) and was stopped by instruction during iteration 136 — quarantined, no `_run.json`, diagnostics preserved. Measured en route: 66% of walk legs are whole-trip network walks at mean ~11 km (#30 surfacing physically), 34% PT access/egress stubs, zero car access/egress; 424,056 walk turn-refusals filed as #60. No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-21 | **Run accounting reads the events stream, and the events pipeline gets its own threads (§9.56; issue #54, PRs #58/#59).** The summariser's stuck attribution came from telemetry's in-flight tracking, which double-counted the engines' end-of-day aborts and false-negatived the accounting gate on runs whose events balance (measured: ride 3 stuck events vs 2 unfinished legs; 12 vs 7) — it now attributes each stuck event to the person's open leg from `output_events.xml.gz`, counts duplicate aborts separately, and reports telemetry-vs-events disagreement. `RUN.machine.event_handler_threads` = 4 declared (`eventsManager.numberOfThreads`) after the framework-default SINGLE events thread was measured saturated under the all-physical event volume (172–177 s CPU per ~261 s iteration; the knob buys ~21% of the wall; model outputs verified bit-identical; the events file's within-timestep byte order becomes schedule-dependent — recorded cost). Registry count verified **327** against the generated contract (the 20 Aug close-out's 327 was an off-by-one over an on-disk 326). Measurement and execution layer only: no target moved; nothing is a result. |
| 2026-08-20 | **Every person-transport mode is now IN ACTION physically (§9.54, §9.55; issues #48/#49/#30).** Walk joins the qsim at PCE 0.0 capped at the declared 1.25 m/s (the sidewalk in queue arithmetic — present on every link, exchanging no capacity with motor traffic); bike at literature PCE 0.2 (swept 0.1–0.4) at its declared 4.2 m/s. Road-rule exclusions declared (walk off motorways/trunks, bike off motorways) with per-mode largest-SCC cleaning (walk stripped from 16,726 unreachable links, bike 5,177 — MATSim refuses islands, measured). The four teleported walk/bike fields retire; the MEASURED 1.6902 walk detour survives as the declared access-stub factor; the transit router's 9,466 generic-route walk stubs are carried by two narrow qsim components (`TolerantAgentSource`, `GenericRouteTeleporter`) after three measured probe failures located the exact collision. The silently-defaulted non_network_walk SCORING is now declared (walk's rate by identity, zero constant). **§9.55: an unpaired ride leg re-modes to physical walk — no exceptions, no teleportation, no invented parameter — making the ride share EMERGENT from household driver supply** (probe: 2,758 re-moded at iteration 0; final iteration ride = 67 trips, every one physically boarded). Probe rc=0, all gates green. No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-20 | **A paired car passenger physically boards the driver's vehicle (§9.53, issues #48/#28/#31).** The mechanism the gap decomposition forced: `JointRideEngine`, a qsim departure handler + engine consulted before teleportation — board when the booked driver's car is still parked at the shared origin (real PersonEntersVehicleEvent, every link ridden, alight at the shared destination); a miss falls back to Tier 1 verbatim and is counted; the qsim's boarding cap now carries the declared `B.ride.max_passengers_per_vehicle` instead of MATSim's coincidentally-equal default. Probe (1% × 2, rc=0): 67–71 boarded/iteration, 2 missed, 0 absent/full — confirmed independently from the events (71 Enter events at the ride-departure second into another person's car). Car vehicle ids measured to be the person's bare id after the guessed `_car` form missed 100%. The unpaired majority stays teleported pending #48's re-moding policy. No target moved; nothing is a result. |
| 2026-08-20 | **Motorbike becomes a physical mode (§9.52, issue #49): a person-level locked carve from car-driver demand, anchored on the measured census JTW share.** 653 of 179,761 core-SA1 one-method JTW journeys (0.363%) are by motorbike/scooter — the observed anchor the old "declined for want of a target" stance lacked. `B.motorbike.trip_share` 0.0036 (assumed commute→all-purpose transfer, swept 0.0–0.01), PCE 0.4 literature (swept 0.3–0.75). Hash-drawn per person (no rng perturbation — every existing draw sequence byte-identical), day locked to the mode except escort days, carved FROM car so no trip is invented; `fit.py` compares car+motorbike against the Vehicle-driver target that contains motorcyclists. Smoke-verified physical: 12 riders, 52 trips, 6,286 link traversals at 1%. Same comparability family as §9.49 (no completed run exists in it). **Seven of nine-plus modes are now physical.** No target moved; the 67/143 split untouched; nothing is a result. |
| 2026-08-20 | **Four standing directives reset the value order, and the base arm is stopped (§9.51).** (1) Every ride trip physically in a car — no teleportation — and the share tuned to the observed 20.60%; re-opens the joint-plans question (socnetsim ~10× is the recorded cost to beat). (2) All 9+ modes distinguished — pt never an umbrella; motorbike and taxi/rideshare individualised, anchored on the VERIFIED per-mode G62 journey-to-work columns (Motorbike/scooter, Taxi/Rideshare, Tram/LR, Train, Bus, Ferry, Truck). (3) The sub-1 km walk deficit is the priority structural defect — #30 re-opens under its own REOPEN IF. (4) Mode × demographic distributions must match real life — new observables enter as constraints, never targets. `base1000_25pct` stopped at ~iteration 20 by instruction and quarantined; #14/#9 stay open until it relaunches. No target moved, the 67/143 split untouched, nothing is a finding. |
| 2026-08-20 | **The calibrated base takes §8.5's second branch — constrain and report — and the decision is logged before its run exists (§9.50, issues #14, #9).** The first branch (ASCs on era 3) is recorded infeasible as stated: no 2018 demand exists and the historical reconstruction is dropped, so estimating 2018 constants under a 2026 population would manufacture the confound §8.5 prevents. ASCs stay at the §8.5 priors, held fixed; `asc_car_passenger` is NOT re-solved against the §9.48 occupancy excess (that would be ASC absorption — #9 resolved by decision, the excess reported). No parameter search: the corrected loop identifies exactly two searchable parameters at ~21 × 35 h runs, neither able to reach the structural misfits — declined with the cost stated. Also fixed: the loop's rebuild-stage table defaulted unclassified consumers to "movable at run time", putting the OSM harvest margins in the movable set — unclassified consumers are now excluded with the reason stated. The base is one reference run of the §9.49 family whose fit is reported as it comes out. |
| 2026-08-20 | **Freight becomes physical (§9.49, issue #24): a `truck` mode in the mobsim at declared PCE, seeded from the counts the model already holds.** `qsim.mainMode` = `car,truck`; `vehiclesSource` → `modeVehicleTypesFromVehiclesData` with the car type restating MATSim's default exactly (`RUN.qsim.car_vehicle`) and the truck type at `B.freight.pce` (literature 2.0, swept 1.5–3.5) under the regulated 100 km/h cap. Through-gate volumes split into car and truck by each gate station's own observed heavy share (Hunter Expressway 0.1529 observed; median 0.0652 fallback) — through trucks had been riding as PCE-1 cars. An internal freight tier draws over the observed freight-industry attractor at the assumed, swept `B.freight.trip_ratio` (0.0697, sweep 0.0–0.14). NEW MEASUREMENTS from the classified RMS hourly counts (`extract_freight_profile.py`, 33,816 station-days): the heavy hourly profile per day type and the weekend factors (SAT 0.4627, SUN 0.4104). Six new registry fields + `RUN.qsim.car_vehicle`; subpopulation `freight` with `lockedMode=truck` (no Java change). **A planned comparability break: the demand family changes again — `bind1000_25pct` is the last run of the §9.46/§9.47 family.** No toolchain change; no target touched; nothing here is a result. |
| 2026-08-20 | **Session close-out and onboarding become procedure, not recollection — no model or data value changed.** Two project skills land in `.claude/skills/`: **`/handoff`** (evidence-gated close-out: deletion-disciplined hygiene, issue grooming that closes only with evidence and a REOPEN IF condition, the DECISIONS entry + §14 row + index, the board repaired in the same commit, and the brief rewritten in place with completed sections flipped from instructions to record) and **`/onboard`** (session start: read in precedence order — constraints → record → board → brief, artefact over document — run the §0 checks, cross-check the documents against live GitHub state, answer the six state-of-the-project questions with sourced numbers, recite the invalidating constraints, then brief and stop). The handover is now REQUIRED to answer six questions exhaustively — goals vs achievement, phase states, tasks done-and-evaluated, simulator vs observation, the issue ledger, PR history + next PR — so a next agent reconstructs the whole picture from `main` alone. One home per document class is stated as a rule (new audit reports under `docs/audit/<YYYY-MM-DD>/`; a new document class is an decision required). **PR titles now carry the phase and task number** (`P<phase> (<task>): …`; `P<n> board:` / `P<n> handover:` / `Tooling:`), and all twelve existing PRs were retitled to the scheme. No target value changed, the 67/143 split is untouched, nothing here is a result. |
| 2026-08-20 | **The re-measure arm ran, and the escort binding is measured to move realised pairability by two orders of magnitude (§9.48, issues #31, #28, #9).** `bind1000_25pct` — 25% × 1000 WEEKDAY on the §9.46/§9.47 demand, the first run of the post-repair family — completed rc=0 in 34 h 44 m, median iteration 105.9 s, **`relaxed: true`** (max post-margin drift +0.09 pp), accounting closed, stuck 0.028%. **OD-coincidence 0.104% → 15.31%; declared-regime (`both_links` ±15 min) pairing 0.00004 → 0.0130**; the #28 residual is ~11.6 s at 25% (was ~5 s); the direction split stays non-zero (239 return pairings at iteration 1000). The defect **changed sign**: occupancy is now 0.4855 passengers per driver against the observed 0.3503, outside the declared range in the **flattering** direction — recorded, not tuned, and handed to the 4.2.4 calibration decision. Ride's LGA linked share moved 37.17 → 31.05 against observed 20.60; the restored 75+ cohort makes 0.7% of its trips to work. The realisation gap (15.31% coincident vs 1.30% paired) is named and deliberately not chased. Per the brief's §4D branch the ride lane rests; next in value order, pending confirmation: #24 freight, then 4.2.4/#14. **Pre-calibration, one scenario, one seed, no counterfactual: nothing here is a finding about the light rail, and no holdout row was opened.** |
| 2026-08-15 | **The city selector never worked, Java was never audited, and G2 is now exercised rather than asserted (§9.38 cont.).** Reporting zero hardcoding against an audit that did not look at Java, for a framework whose second-city claim had never been run, was a verdict on a scoreboard rather than on the repository. Both gaps contained a live defect. **THE CITY SELECTOR WAS BROKEN AND ALWAYS HAD BEEN.** `README.md`, `docs/README.md` and `.claude/CLAUDE.md` all state that the city is selected by `CITYSIM_CITY`. Setting it to ANY value - *including its own default* - made every `registry.load()` raise *"env CITYSIM_CITY matches no registry field"*, because the resolver reads `CITYSIM_*` from the environment as field overrides and skipped only `CITYSIM_REPO`. Nobody had ever set it: there is one city and the default applies when the variable is absent. The documented mechanism for goal G2 could not be used, and it took actually building a second city to find out. `city.py` now owns the reserved names and the resolver skips them, so the two copies cannot disagree; an EMPTY value also resolved to `cities/` itself and now falls back. **JAVA WAS NEVER SCANNED.** `check_hardcoding` read `src/java/` only for key mentions, never for values, and two MATSim `ConfigGroup` defaults EQUALLED the registry values they shadow - `TelemetryConfigGroup.liveIntervalS = 3600.0` against `RUN.telemetry.live_interval_s = 3600`, and `ParkingConfigGroup.chargedModes = "car"` against `A.parking.charged_modes`. That is the signature defect in its worst form: right by accident, every test passing, and silently wrong the moment anyone sweeps the field, because a config that lost the binding would run on the Java number and report success. Both are now a sentinel or a neutral value with `checkConsistency` refusing the run, and the audit gained a detector for the class - **verified by reintroducing the defect and watching the gate go red**. **G2 IS EXERCISED.** `tests/check_city_agnostic.py` builds a second city from the reference city's own declarations under a different identity - different projection, base year, seed, day types, **three modes not five**, different scenarios - emits its MATSim config through the same emitter and asserts DIFFERENCES, because a test that only checked the config parsed would pass even if every value in it were Newcastle's. It **invents no observation**: fabricating a city's census or counts would breach the rule that no unsupported number may be presented as observed, so the fixture is explicitly not a study, is built at test time and is deleted after. It also hashes `src/`, `config/schema/` and `run.py` either side to prove **no framework file changed while it ran**. 13 assertions, all passing, and a CI job runs it on every push. **THE CONTRACT WAS OVER-STRICT AND SAID SO ABOUT ITSELF.** `required_fields.json` demanded all 292 fields of every city while its own caveat admitted *"a city with no light rail has no use for A.lightrail.dwell_fixed_s - narrowing this set per model layer is not done"*; a three-mode city was refused for not declaring bike parameters it has no bike to apply to. The mode case is the one narrowing that can be DERIVED rather than judged, because the mode name is in the tool binding: fields carry `required_if_mode`, and `check_city` both excuses a missing one and now FAILS a city that declares a mode it does not run. **THE THIRTY RUN-INPUT SETS WERE REGENERATED** and now carry the emitter's output rather than the deleted template's - `lastIteration` 100 → 250 (the declared sweep floor, set through the resolver), threads 8 → 10 (`RUN.machine.threads`), and both capacity factors 1.0 → the resolved sample fraction. Manifest **376 → 378** files. Rebuilding the scenario GTFS feeds is **blocked by the empty OSM harvest (#32)** and was not attempted; the scenario rewiring was instead proved **value-neutral against git** - 23 declared values and every relocated coordinate identical to the literals they replaced. One more defect found by running the builder: `split_schedule` still referenced the deleted module-level `CFG`, which compiles and dies on use, exactly trap #11 - and a repo-wide AST sweep for the class now returns zero. **No scenario was run, no target value changed, the 67/143 split is untouched and nothing here is a result.** |
| 2026-08-15 | **Zero hardcoding: the config is BUILT from the registry, and 69 bound fields are PROVEN to reach the model by moving them (§9.38).** The MATSim config was a hand-written template with substitution holes, so every parameter nobody had cut a hole for stayed a literal - **47 of them**, including `fractionOfIterationsToDisableInnovation`, which the entire relaxation measurement hinges on, the four strategy weights that bound how far co-evolution can move mode share, and `BrainExpBeta`, the logit scale, which **had no registry field at all**. Six more had fields carrying a `matsim_param` binding the template ignored: right by accident, and wrong the moment anyone swept them. Patching them one at a time leaves the template, and **the template is the defect** - a place where typing a number is possible. `src/registry/param_config.py` now builds the MATSim config and pt2matsim's two from the fields that declare a binding; a parameter exists only if a field claims it or the caller supplies it under one of three declared runtime roles (a path, the city's own identity, a value derived from declared fields), and `closure()` returns anything else. **Emitting rather than patching also fixed what an overlay could reach**: `run_matsim.py` read the shipped config and rewrote SIX parameters, so a run overlay setting any other field was validated against its sweep, written into `_config.json` as the run's provenance, and changed nothing - the snapshot said one thing and the run did another. **Four quantities were bound to a parameter of a different kind, and the emitter found each by refusing to write it**: an exponent to a factor (`storage_capacity_exponent` 1.0 into a 0.01 factor - MATSim rejects that in one second), a time RATIO to a util/hour rate (`beta_walk_mode`, `beta_bike_mode`), a per-day-type window dict to two scalar hours (parking), and an activity duration table with no clock format. Each is now the input to a `computed` field carrying its identity. **The network builder held a second copy of the road class defaults** and the comment above it said it was kept there so the MATSim network, the SUMO corridor and `A1_road_edges.csv` could not drift apart; **they had** - six classes carried a different free speed from `A.road.speed_default`, in both directions (motorway 100 v 110, trunk 80 v 60, plus motorway_link, primary_link, secondary_link, service). Nothing compared them, because a second copy with no `legacy_symbol` is invisible to `check_legacy_drift.py`. One copy now, and **the network takes the declared speed** - a real change to six classes' free speed, taken because the registry is the declared source of truth and the network is rebuilt by #32 anyway. **The shipped configs stopped carrying a value supplied past the resolver**: `RUN.controler.last_iteration` is `unobtained` because 100 is MEASURED to be too low, and an argparse default shipped exactly 100 into all thirty sets; a shipped config now carries the sweep's lower bound, set THROUGH the resolver so it is recorded and range-checked. **22 coordinates left the scripts** into `cities/<city>/geometry/scenario_alignments.json` - among them the eight stops of the S1 shuttle and the six of the S3 BRT, the whole alignment of both counterfactuals the light rail is reported against, with the S3 list a copy of the S1 list that could drift; S3 is now expressed as which S1 stops it omits. Their service specifications went too, and were worse than unswept: `make_bus_shuttle(speed_kmh=28.0, dwell_s=15.0)` were **dead defaults** - the S1 call site passed 26.0 and 18.0, so the signature advertised a specification the model never used. **`0.75` was the S2b intervention**: "full transit signal priority" removes 75% of corridor signal delay, and that share - the thing S2b exists to measure - was a bare literal inside an arithmetic expression. `A.lightrail.tsp_enabled`, which all ten scenario overlays set, **reached nothing**; it now decides whether the S2b saving applies at all. **`DWELL_CHARGING = 20.0` pinned an UNOBTAINED input in a script**, walking past the one refusal the registry exists to make; the handover brief said it was pinned by `legacy_symbol` and should be left alone, and it carried none - its `EXPECTED_DIVERGENCE` entry compared nothing and the constant was unguarded. The seed existed in **nine copies** against a declared `B.seed.master`. `DEPART` was **144 assumed numbers** deciding when every tour starts. `build_matsim_plans.py` held a second activity-duration table, six keys against the field's seven - it had no `escort`. **The audit itself was counting the wrong things**: it asked whether a key was a SUBSTRING of any file, so a key named only in a comment or a test passed as wired, and **the count FELL when someone added a comment**. It now counts a key only where it appears as a complete string literal, understands a key built by format at the call site, and asks a sixth question no text search can - change each bound value and watch the emitted config change. **69 of 69 pass, 0 inert.** Honest baseline **185 items, not the 95 the previous audit could see; now 0**, with 18 structural exceptions and 7 declared-ahead-of-consumer fields each carrying a written reason and the issue that will wire it. `--strict` is a CI gate. **The CI provenance job had been failing since the city restructure** - it tested `docs/DECISIONS.md`, which moved. **No scenario was run, no target value changed, the 67/143 split is untouched and nothing here is a result.** |
| 2026-08-14 | **One city moves into `cities/<city>/`, and the framework stops knowing which city it models (§9.37).** No model or data value changed: the manifest was regenerated and diffed - **376 rows before and after, no path added or removed, not one sha256 changed**, only `produced_by`. `cities/newcastle/` now holds the registry, the overlays, the acquisition adapters, the seven builders that encode this city's intervention, and every data, network, schedule, demand and scenario artefact; `config/` is `config/schema/` alone. `src/city.py` is the only module that knows where a city lives and 338 path literals across 46 scripts resolve through it. **The input contract now exists**: `city.schema.json` (identity, and a boundary that must be DERIVED - `bbox` is deliberately not a property), plus the generated `required_fields.json` (210 keys) and `layers.json` (119 artefacts, read from the framework's own `city.path(...)` calls), gated by `check_city.py` in CI. The CRS left seven modules and the mode-share filter value left three, into `city.json`; the #34 CBD box and the harbourside window are declared in `geometry/` at **byte-identical values** - relocated, NOT fixed, #34 still open. **#36 closed**: `CITYSIM_*`, `src/java/citysim/`, `CitysimControler`, generic OSM layer names. **One breaking output change taken deliberately**: `newcastle_lga_pct` -> `target_lga_pct`, so run records written earlier cannot be read by `fit.py`. **Two defects found by measurement**: four scripts named a city directory relative to the working directory and one wrote 32 MB of GTFS into the repo root (`check_city.py` now fails on the class, verified by reintroducing it), and `build_manifest.py` still stamped **GDA2020** where §2.6 established GDA94. Still no scenario run; no falsification condition altered. |
| 2026-08-13 | **Repository context cleanup — no model or data value changed (issue #36 filed).** The documents had drifted from the model. `STATUS.md`, whose whole purpose is to be readable at session start, had become **1,191 lines of which 944 were dated session narrative** duplicating §9.1–§9.35; that narrative moved to `docs/handover/SESSION_LOG.md` as an archive and `STATUS.md` is a board again at 317 lines. **Four figures in it were stale and one was self-contradictory**: it claimed 364 manifest files against a real 386, "four runs exist" against seven directories, "~960 checks", and a header reading *"Stage: P4 stages 0–3"* under a *"last updated: P4 stage 17"* line. **A correction recorded in §2.6 had never propagated**: `CLAUDE.md` and `README.md` still labelled EPSG:28356 as GDA2020 when §2.6 establishes it is GDA94 — the one file that overrides all others was stating the wrong datum. `DECISIONS.md` gained a **topical index**, because its section numbers are not in file order (§15 precedes §14) and §9 had accumulated 35 subsections spanning parking, network, toolchain and registry decisions under a heading that says *Synthetic population and demand*; nothing was renumbered, since §9.x ids are referenced from code comments, issues and both other documents. Documents were filed under `docs/{design,reference,audit,handover}/` with `docs/README.md` marking **which four are generated and must never be hand-edited**; the three generators and `check_package.py` were repointed and `render_docs.py --check` re-verified. **The project codename was a suburb**: "Project Wickham" named the whole five-LGA Newcastle model after one suburb of it, contradicting this repo's own rule that no place name belongs in the framework — and the city-selection mechanism reads `CITYSIM_CITY=newcastle`. Prose, the three schema titles and the manifest `project` string are renamed to the then repository name (itself superseded by `city-digital-twin`, §9.67); the `CITYSIM_*` prefix and the `src/java/citysim/` package are **deliberately left** and tracked in #36, to be renamed inside the #32 re-harvest batch, which already invalidates every run record and recompiles the Java — a rename of a compiled entry point cannot be gated now, because `networks/osm/` is empty and `check_package.py` cannot pass. Every Wickham-the-suburb reference is untouched: the zone, stop and POI data, the Newcastle Interchange transfer, scenario S1 and the era-1 reconstruction. **#16 closed** — §9.12 ran the measurement it specified and §9.17 took the decision it gated; the other eleven open issues were each checked against the package and **none of the rest is resolved**. Four fully-merged local branches deleted (zero unique commits each). One broken relative link in §9.13 fixed; all 40 links in the extracted narrative repointed; **0 broken links** across every document. `check_manifest.py` passes and `compileall` is clean. **Nothing in this repository is a result**, and the OSM harvest is still empty. |
| 2026-08-13 | **The corridor speed limit becomes the REGULATED one, and the rest stays imputed and says so (§9.34, issue #27).** TfNSW's statewide **Speed Zones** layer - the legal instrument, not a mapper's transcription of a sign - clipped to the dissolved LGA boundary plus a declared margin, never a typed extent. Corridor edges on a regulated speed **0 → 669 of 714**; imputed **75 → 41**. Network-wide, imputation falls **53.7% → 38.3%**, and 15,804 of the 16,515 still imputed are `service` roads, so on the roads anyone drives it is **2.6%**. **The join was validated and the validation changed it**: at 20 m it agreed with OSM only 73.5%, and looking showed agreement collapsing from 72% at 10 m to **30% at 10-20 m and 15% at 20-40 m**, plus service roads matching the arterial beside them at 37% against residential's 83%. Radius tightened to 10 m on that measurement and `service` excluded by class - excluding by measured agreement would be fitting the join to its own validation. **What did not close is asserted as still open**: kerbside 678 of 714 imputed, lane width 704, capacity 714, turn lanes 644 absent. TfNSW publishes kerbside for the **Sydney CBD only** and no statewide lane or capacity inventory exists, so B3 - proposal §3.3's *decisive test of Claim B* - must report them as uncertainty, and check_package now fails if the gap is quietly relabelled. Two more copies of a number found on the way: the corridor builder kept its OWN speed, lanes and capacity defaults, which had **diverged** from the measured ones (trunk 80 vs 60), and a second bare 3.2 lane width with the same carriageway-versus-lane error. **No scenario was run, no target value changed and nothing here is a result.** |
| 2026-08-13 | **P4 deliverable 0b - six defaults stop being guesses, and a suspected duplicate turns out to be two different numbers (§9.33, issue #23).** **88 → 84 assumed, 15 → 21 measured**, plus one field that existed nowhere. `RUN.routing.beeline_distance_factor` and `B.activity.detour_factor` were flagged as probably the same quantity declared twice; they are not - one is the road graph at zone spacing, the other the ACTIVE network at walk and bike trip lengths, and circuity falls with distance. Measured: **walk 1.6902, bike 1.5231** against a shared assumed 1.30, so the field is **split in two**. A first sampling by random bearing gave 1.96 and was **rejected on its own evidence** - it sent walk trips across the harbour; sampling observed POI destinations, which is where B2 puts activities, gives 1.69. The walk SPEED, though, WAS a genuine duplicate: `A.transit.walk_speed_ms` 1.25 and `RUN.routing.teleported_walk_speed_ms` 1.05, both `literature`, each describing the other as a different quantity - and the pinned jar's bytecode shows `travelTime = (beeline x factor) / teleportedModeSpeed`, so the speed is ALONG the path and they are one number. Now `derived` by identity at 1.25. Per-class defaults measured from the city's own OSM tags where at least 30 edges are tagged: **trunk speed 80 → 60** over 1,702 tagged edges, **motorway 100 → 110**, and a **lane width that was a bare 3.2 in no registry at all**, now measured at **3.5 m** - and NOT from the `width` tag, which on a road is the whole carriageway at 6.5 m and would have doubled every carriageway in the model. Three things the data looked able to settle and could not, all the same trap: parking capacity has 4,861 observed values of which **4,623 are 1** because they are individual bays, not car parks. The reclassification #23 proposed was reviewed and **mostly declined** - the SUMO booleans and corridor buffers each change a result, and relabelling a real assumption to make a percentage look better is the opposite of what 0b is for. **No scenario was run, no target value changed, the 67/143 split is untouched and nothing here is a result.** |
| 2026-08-13 | **P4 deliverable 8 - the transfer penalty cannot be estimated from this package, and the parameter was reaching nothing anyway (§9.32, issues #25, #35).** Proposal §7.2's fallback asks for tap-on/tap-off **timing** at the Interchange plus a matching model. **Every Opal source held is a monthly aggregate** - no timestamp, no tap-off paired to a tap-on, nothing for a matching model to match. The stop-level tap data that would substitute is **holdout**, and the 67 calibration rows contain nothing bearing on interchange, so the constrain-to-an-observable route (§9.8) has no observable either. No published interchange percentage for Newcastle could be located; and published interchange **times** are the wrong quantity - MATSim already simulates the walk and scores the wait at 2.0x in-vehicle time, and this parameter is the premium **on top of** the measured 112 s Interchange walk, so substituting one would double-count. Per the deliverable's own bar the reason is recorded and **the sweep stands** at 3-15 minutes across seven points. Tracing where the parameter goes found that it went nowhere: `build_params.py` read **one** registry field and typed the other **26** in as literals, so setting the value through the resolver's own override path left `C1_parameters.json` **byte-identical**. Seventh instance of the class. Two consequences sharper than usual - the **mode constants are `held_fixed` under §8.5** and the model was not reading the value being protected, so deliverable 5 (#14) would have estimated seven ASCs, written them to the registry, changed nothing and reported success; and the **sweep grid was a literal too**, making #25's own bar unmeetable by construction. The prior check compared **bases only** and its comment conceded *"the registry copy is a mirror"* - three RANGES had already drifted apart unnoticed. C1 is now **generated from** the registry rather than checked against it, with five missing declarations added; declaring a sampling grid for the charging dwell did **not** pin it, which stays unobtained and null. **Value-neutral and proved so** - no base moved and all 30 run-input sets regenerated unchanged - and **reach proved by changing a value**: the override now moves `utilityOfLineSwitch` -2.2613 to -3.3922, exactly the VOT conversion. `check_package.py` 1,435 -> **1,440**. **No scenario was run, no target value changed, no holdout row was opened and nothing here is a result.** |
| 2026-08-13 | **P4 stage 13 - a car stops parking for free, and the price stops being a drawn rectangle (§9.31, issue #33).** Parking price is the prime competitive lever between car and PT for a city-centre trip, and this study is about city-centre access. `A5_parking_facilities.csv` has declared `is_priced`, `price_aud_hr` and a sweep on both since P1 and **no script read any of it** - the "declared value that reaches nothing" class on its **sixth** instance. Its spatial basis was four hand-drawn lat/lon rectangles with place names, literal prices and hand-typed occupancy profiles, and **one of the four, `honeysuckle`, was fully contained in the box tested before it and could never match a facility** - dead for three phases, because a typed rectangle cannot be wrong in a way anyone notices. Price is now derived from **the city's own core-zone job-density distribution** (p90 = 1,500.9 and p99 = 8,710.5 jobs/km², pricing 150 of 1,500 core zones and 22,353 of 143,891 car links), so a new city computes its own thresholds and no extent is typed. OSM `fee=yes` was reproduced and rejected as the basis: **452 of its 472 facilities are University of Newcastle car parks**. The charge reaches the model through `ParkingChargeHandler`, which bills a car from arrival to the next car departure as a `PersonMoneyEvent`; roadpricing is **not** in the pinned jar, so its deferred-emission pattern is reproduced rather than reused, and Java does no spatial work. **Reach was established by changing values, not by reading `consumers`** - halving `price_aud_hr_max` halved the charges (−721.42 → −361.62 AUD), Sunday charges nothing, and the largest single charge is exactly the max-stay cap. **That test caught a real defect**: `accessEgressType` inserts a `car interaction` activity after every car arrival, so the `home` exemption matched nothing and **267 of the first 641 charges were levied at people's own homes** - a nightly penalty on living in a dense zone that no observation supports. What the formula still gets wrong is measured rather than supposed: it prices Kotara, Glendale and Charlestown at or near the maximum where parking is free, and a contiguity refinement that would separate the centre cleanly (one 80-zone cluster against 49 of 1–5) was **built and rejected** because it also excludes the University and John Hunter Hospital, the two places outside the centre that verifiably do charge. Price is common to all scenarios, so it largely differences out of the S-vs-S comparison and bites on the base calibration instead. `check_package.py` 1,248 → **1,435** passing, the key check re-deriving every zone price from the registry so a typed price cannot survive. **No scenario was run, no target value changed, the 67/143 split is untouched and nothing here is a result.** |
| 2026-08-13 | **P4 stage 10 - the passenger stops outrunning the driver (§9.26, issue #28).** `ride` was routed over the network on **free-flow** times because it is in `routing.networkModes` but is not the qsim `mainMode`. `CitysimControler` now binds its travel time to `networkTravelTime()` and its disutility to the car factory. Verified against a like-for-like 10% baseline differing only in the controler: **car 32.54 -> 52.30%, ride 50.03 -> 29.45%**, total absolute gap to target **84.2 -> 44.6 pp** - the largest single correction this model has had, and it came from a defect rather than a constant. It confirms §9.25's claim that the symptom was **two** inversions: car↔ride moved ±20 points while walk↔bike moved -0.03/+0.81, untouched. **The defect is reduced, not eliminated** - ride is still 1.01-1.11x faster at matched distance, worst on short trips, so #28 stays open. The audit's headline was also corrected: the original 13% was an aggregate confounded by trip-length composition; stratified it is 4-8%, present in every bin. A first verification at 1% was **discarded as uninterpretable** - §15's storage floor produces spurious spillback that inflates car delay while teleported ride is immune, so a cross-fraction comparison is invalid. Two reproducibility defects exposed and closed: **nothing compiled the committed Java**, so a fresh clone could not run; and a run record could not say which controler produced it, so re-running would have served pre-fix results silently - records now carry `controler_sha256` and the harness refuses to resume across a change. `prune_run.py` drops MATSim's per-iteration scratch, **95% of a run's bytes** and read by nothing, reclaiming 36.6 GiB. **Not a result:** 250 iterations is short of relaxation, demand still lacks through traffic and freight, no target was fitted, the 67/143 split is untouched and no holdout row was opened. |
| 2026-08-12 | **P4 stage 8 - own realtime collection dropped, and the published catalogue assessed instead (§9.23).** A GTFS-Realtime collector was built and **reverted in full** once an Open Data Hub API key made the 230-dataset catalogue assessable. TfNSW's own **Historical GTFS Realtime** archive was verified against the live API and carries **Metro and Ferry only** - controls return files, every light rail and bus naming returns none - so it cannot backfill Newcastle, and §7.2's contingency for the SCATS refusal is recorded as an **open gap**. What the catalogue does settle, verified against the data rather than the titles: **Traffic Lights Location** matches **all 14 corridor intersections within 60 m**, supplies the `scats_site_id` that `A2_signal_control_corridor.csv` declares but leaves empty, and dates **8 of the 14 as 2018 light-rail installations** - so the pre-intervention corridor had 6 signals, not 14, which is an observed basis for a counterfactual now assumed; **SFM22** gives origin-destination freight for issue #24; the **GTFS reference tables** carry Hunter Line running times bearing on the assumed era-1 constants; **school and public holiday** dates stratify the dated RMS counts. Recorded as *not* settled: no SCATS phasing exists in the catalogue, the kerbside and lane-width datasets are **Sydney-only** so issue #27 is untouched, JTW 2016 is withdrawn by TfNSW, and Opal tap data is **not journey-linked** so deliverable 8 keeps its fallback. **No value was acquired, changed or registered** - this is an assessment. No parameter value changed, no target value changed, the 67/143 split is untouched and no scenario was run. |
| 2026-08-11 | **The input registry (§15).** Every value the model consumes that is not read from an immutable raw download is now declared in `config/registry/` with its units, its provenance and either a sweep range or an explicit rule holding it fixed — **123 fields**, against 316 module-level constants of which exactly one carried a machine-readable source label. Proposal §8.1 becomes a schema constraint rather than a discipline: `assumed` without a sweep does not validate. The three unobtained inputs carry `value: null` and the resolver **raises** rather than returning a point value, so §0 and §13 are enforced structurally; the §8.5 mode constants are `held_fixed` and no overlay, environment variable or flag can move them. Two factors that governed every P4 result were found set in code with no rationale and no range — `flowCapacityFactor` (derived, and now stated as such) and `storageCapacityFactor` (assumed, exponent swept 0.75–1.0, and an open risk at 1% because MATSim floors link storage at one vehicle). Outputs are declared to the same standard: `_run.json`, `_metrics.json`, `_fit.json` and `_config.json` each carry a JSON Schema, and a fit block that does not name its target ids fails its contract. `docs/reference/CONFIG_REFERENCE.md` is generated and checked for staleness. `check_package.py` 860 → **908 checks**, 1 standing warning. The build layer is declared but not yet migrated and is pinned to the registry by a drift test, which caught four transcription errors on its first run. No parameter value was changed, no target value was changed, the 67/143 split is untouched and no scenario was run. |
| 2026-08-10 | **P4 stage 0 — the assembled run inputs did not load, and what a run actually costs (§9.4, §9.5, §12.1–12.3).** MATSim was pointed at `scenarios/matsim/S2/WEEKDAY/` and refused it. Three independent defects, none visible to a check that treats the artefacts as data: the day-type filter dropped the doctype MATSim selects its reader from (all 30 sets); it left stop facilities and `minimalTransferTimes` relations orphaned by the routes it removed, which makes SwissRailRaptor dereference a null array (all 30); and the kerbside patch appended a second `<attributes>` block to links that already had one, invalidating **6 of the 10** run networks — precisely the six carrying an E1 road change. Fixed, rebuilt byte-identically with the patch counts unchanged, and **all 30 sets now load and run**. `check_package.py` 556 → **657 checks**, with the three failure modes asserted per set. Run cost measured on this machine rather than estimated: **9.8 s/iteration at 1%, 29.9 s at 10%, ~64 s at 25%**, memory 9.8/18.4/31.5 GiB, extrapolating to ~4.5 min and ~97 GiB at 100% — so **a 100% weekday run does not fit in 63.5 GiB** and the specified 5,100 run-days is ~765 days of wall clock. Also recorded, without acting on either: 13 of the 67 calibration targets (`lr_cardtype_share`) can identify nothing in MATSim and several others are duplicates or schedule inputs, leaving ~4 mode-share degrees of freedom + 1 patronage level + 34 counts; and the 119 `road_aadt` values are the mean of `ALL DAYS` with the peak-period rows, 0.58–0.71× the true figure. **The 67/143 split is untouched, no holdout value was used, no target value was changed and no falsification condition altered. Still no scenario run.** |
| 2026-08-10 | **P3 stage 3 — assumptions replaced by Newcastle measurements where the data allows, and the sweep-range rule made mechanical.** Three constants derived rather than typed: the **detour factor** is now routed over the observed A1 road graph (**1.3376**, 551 zone pairs, was assumed 1.30); the **weekday/weekend travel split** comes from the RMS counts' own `WEEKDAYS`/`WEEKENDS` periods (**0.752**, 551 station-years, was implied 0.825); and census G62 gives an observed **lower bound** on work attendance (0.651) without being allowed to set the value, since census night carries the 2021 lockdown (§2.4). Seven parameters that breached proposal §8.1 by carrying no sweep range now carry one, and `check_package.py` **enforces the rule as a test** rather than leaving it to discipline. What genuinely cannot be localised is labelled so: MATSim's `performing`, distance rates, typical durations and replanning weights are properties of the scoring formulation, not of Newcastle. `EXTERNAL_INTERACTION_RATE` stays swept and the missing ABS journey-to-work origin-destination table is added to §13. 497 → **556 checks**, all passing. Still no scenario run; no falsification condition altered. |
| 2026-08-10 | **P3 stage 2 — MATSim plans, day-type run inputs and the C1 scoring translation (§9.3).** 517,936 weekday agents wired to the single P2 build; the day-type filter works on the already-mapped schedule and is verified to preserve all 1,714 route link sequences and the whole stop→link map. What C1 loses in translation — the nest structure, per-purpose VOT, crowding — is recorded, not dropped. Two defects caught by the new checks: the day-type token is underscore-delimited for the S1 shuttle and S3 BRT, so both were being dropped from every day type and each scenario would have run without its intervention; and banned-turn removal was network-wide, deleting 1,235 observed restrictions instead of 8. `check_package.py` 322 → **497 checks**, all passing. Still no scenario run; no falsification condition altered. |
| 2026-08-10 | **P3 stage 1 — B2 activity chains rebuilt as tours (§9.2).** The P1 chains put 1,452,065 activity legs on 1,481 zone centroids, labelled every return-home leg NHB, and gave each agent a single subtour; they are replaced, not patched. Destinations are now placed on observed POIs and building footprints, the gravity decay is solved against the HTS journey distance per purpose, three day types are produced, and the 201 external SA1s finally generate boundary demand. `build_population.py` keeps B1 and no longer writes B2; because it no longer draws for chains, the B1 sample shifted 612,680 → 612,668 persons with every fit statistic unchanged. Still no scenario run; no falsification condition altered. |
| 2026-08-10 | **P3 stage 0 — the §3.4 shape defect closed, and one determinism bug with it.** S0/S2c/S4/S5 alignments rebuilt from observed geometry (§3.4); extension stop sitings anchored on observed features, one of them 548 m out. E1 patch set 195 → 414 rows as a consequence. **`build_scenario_schedules.py` iterated a `set` of trip ids in two places, so `stop_times.txt` row order varied with the Python hash seed** — a violation of the determinism rule that predates this branch and was caught by a repeat-build check; now sorted, and two consecutive builds are byte-identical across all 10 feeds. One MATSim build of all 15 feeds and 4 SUMO nets regenerated on the corrected feeds; 322 package checks pass. Still no scenario run; no falsification condition altered. |
| 2026-08-10 | **P2 network build.** Toolchain pinned (§3.6). Corridor attributes graded by evidence and the E1 road variants derived as edge-level deltas (§3.4); premise corrected — the corridor is not 75–98% imputed (§2.5). pt2matsim's run-to-run drift measured and bounded (§3.5). Three missing signal variants built (§5). CRS label corrected (§2.6). MATSim network + 15 mapped schedules and 4 SUMO corridor nets produced. Still no scenario run; no falsification condition altered. |
| 2026-08-10 | Initial. P1 data acquisition. Scope decisions §10.1–3, 4, 5 closed. Proposal premises corrected per §2.1–2.4. No scenario run; no falsification condition altered. |
