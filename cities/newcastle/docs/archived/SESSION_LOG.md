# Session log — P3 and P4, 10–13 August 2026

> **ARCHIVE.** Dated narrative only; some links inside were written from the documents they were moved out of and may not resolve. The board is [`../STATUS.md`](../STATUS.md).

**This is an archive, not a source of truth.** It is the dated build narrative
that accumulated inside `STATUS.md` and was moved out on 13 August 2026 so that
`STATUS.md` could go back to being a board that can be read at session start.

Where this log and another file disagree, the other file wins:

| For | Read |
|---|---|
| Why a value is what it is, and its sweep | [`DECISIONS.md`](../DECISIONS.md) — **authoritative**; §9.1–§9.35 hold the full version of nearly every entry below |
| Where the build is now, and what is next | [`STATUS.md`](../STATUS.md) |
| Picking up P4 cold | [`P4_CHECKPOINT.md`](P4_CHECKPOINT.md) |
| Conventions and hard constraints | [`CLAUDE.md`](../../../../.claude/CLAUDE.md) |

Entries are in the order they were written. **Nothing here is a result** — no
scenario has been run to a reportable state.

---

## P3 stage 0 — what changed (10 August 2026)

| | |
|---|---|
| S4/S5 extension alignment | Routed over the observed OSM centreline of the SBC street sequence. **7.00 km vs the SBC's stated 6.65 km (+5.3%)** |
| S2c / S0 alignment | The retained harbour-side former-railway strip — 33% / 21% observed OSM geometry, remainder interpolated |
| Extension stop sitings | Anchored on observed features (two intersections, a station node, a POI). The P1 Hamilton coordinate was **548 m off the published corridor** |
| E1 road patch set | 195 → **414** rows; corridor/parallel edges 605 → **714** |
| Determinism | A **pre-existing** set-iteration bug in `build_scenario_schedules.py` made `stop_times.txt` row order hash-seed dependent. Fixed; two consecutive builds are now byte-identical across all 10 feeds |
| Network | **One build** of all 15 feeds + 4 SUMO nets, on the corrected feeds. 0 unmapped stops in every feed; artificial link share 0.48–0.60% |
| Checks | `check_package.py` **322 checks pass**; `check_manifest.py` OK |

**Not done, deliberately:** S1 and S3 leave 532 and 712 shuttle/BRT trips with no
`shape_id`. That is valid GTFS, pt2matsim maps them from the network, and both routes
run on streets where a shape adds little. Recorded rather than built.

---

## P3 stage 1 — B2 rebuilt as tours (10 August 2026)

The P1 chains were a skeleton, not plans. Replaced, not patched
([`DECISIONS.md`](../DECISIONS.md) §9.2). Before → after, measured on the full output:

| | P1 | P3 |
|---|---|---|
| Distinct non-home destination coordinates | **1,481** (zone centroids) | **76,278** |
| Busiest single coordinate | **10.9%** of activity legs | **0.65%** |
| Legs with a home-based purpose not starting at home | **684,125 (47%)** | **0** |
| Return-home legs labelled NHB | **568,631 (all of them)** | **0** |
| Persons with more than one tour (real sub-tours) | **0%** | **56.7%** |
| Legs arriving after the day horizon | 1.77%, latest **36.0 h** | **0** |
| Day types | 1 generic | **3** (WEEKDAY / SAT / SUN) |
| External-tier demand | none | **5,384** weekday boundary agents |
| Realised week trip rate vs HTS 3.473 | 3.298 (−5%) | **3.397 (−2.2%)** |
| Gravity distance vs HTS, worst purpose | **+66%** (education) | **exact, all six purposes** |

95.5% of activity ends now sit on an observed POI or CBD building footprint.
Output is three files, `demand/plans/B2_activity_trips_{WEEKDAY,SAT,SUN}.csv`,
5.86M legs. `build_population.py` keeps B1 and no longer writes chains.

**Watch this one:** `P_INTERMEDIATE_STOP` (0.12–0.30, swept 0.10–0.35) decides how
many sub-tours exist, and therefore how freely MATSim's mode choice can vary within
a day. It is assumed, and it is the demand-side parameter with the most leverage
over mode share.

---

## P3 stage 2 — MATSim plans and run inputs (10 August 2026)

| | |
|---|---|
| Plans | `demand/plans/matsim/population_{WEEKDAY,SAT,SUN}.xml.gz` — **521,502** weekday persons, 2,237,373 legs, 2,758,875 activities, at **100%** of the population |
| Run inputs | `scenarios/matsim/<S>/<DAY>/` — **30 sets** (10 scenarios × 3 day types), each with a day-type-filtered schedule, its vehicles, a patched run network and a `config.xml` |
| Seed mode share | car 55.7 / ride 18.6 / walk 19.3 / pt 4.0 / bike 2.4 against HTS 57.5 / 21.5 / 16.1 / 3.4 / 1.6 — an **initial condition**, not a calibration |
| One build | day-type split runs on the **already-mapped** schedule: all 1,714 S2 route link sequences byte-identical to source, stop→link map for 4,174 facilities unchanged |
| Run network | the scenario's **own mapped** network + E1 patch by `osm:way:id`, not `networks/matsim/variants/` (which is patched over the base and has no transit links — reference only, not runnable) |

**Three defects caught here, two of which would have produced a plausible-looking
wrong answer:**

1. The day-type token is dot-delimited in the era and scenario feeds
   (`nisc001:WEEKDAY.2302960`) but **underscore-delimited** for the S1 shuttle and
   S3 BRT (`S1SHUTTLE_WEEKDAY_0_1`). Matching only the dotted form dropped both from
   every day type — **S1 would have run without its shuttle and S3 without its BRT**.
2. Banned-turn removal was applied network-wide, deleting **1,235** observed turn
   restrictions instead of the **8** on the corridor.
3. `gzip.open` stamps the wall clock into the gzip header, so identical content
   produced different manifest digests on every rebuild. Pinned in
   [`src/build/det_io.py`](../../../../src/build/det_io.py); repeat builds are byte-identical.

**Carried into P4:** what C1 loses in translation to MATSim scoring — the nested-logit
structure (`nesting_coefficient_pt = 0.65`), per-purpose value of time (collapsed to a
trip-weighted 16.96 AUD/h) and the crowding multipliers. See
[`DECISIONS.md`](../DECISIONS.md) §9.3.

---

## P3 stage 3 — assumptions replaced by measurement where the data allows

Three P3 constants are no longer typed in. `src/build/measure_network_factors.py`
derives them from layers already in the package and writes
[`params/C2_network_factors.json`](../../params/C2_network_factors.json):

| Value | Was | Now | Measured from |
|---|---|---|---|
| Detour factor (straight-line → network) | assumed 1.30 | **1.3376**, sweep 1.25–1.42 | 551 population-weighted zone pairs routed over the observed A1 road graph |
| Weekday vs weekend travel | assumed, implied 0.825 | **0.7521**, sweep 0.709–0.816 | RMS traffic counts' own `WEEKDAYS`/`WEEKENDS` periods, 551 station-years |
| Work-attendance lower bound | none | **0.651** | Census G62 — bounds the `P_MANDATORY` sweep, and is **not** allowed to set the value, because census night was August 2021 with 19.2% working from home ([`DECISIONS.md`](../DECISIONS.md) §2.4) |

**Seven parameters breached proposal §8.1** by carrying no sweep range. They now
carry one, and `check_package.py` **tests the rule** instead of relying on discipline.

**What is genuinely not localisable, and is labelled so:** MATSim's `performing`,
monetary distance rate, typical activity durations and replanning weights are
properties of the scoring formulation, not observable quantities of Newcastle.

**What is localisable but not yet available:** `EXTERNAL_INTERACTION_RATE` needs the
ABS journey-to-work origin-destination table (SA2 usual residence × SA2 place of
work). The package has the place-of-work side but not the pairing — added to
[`DECISIONS.md`](../DECISIONS.md) §13 as a standard TableBuilder extract, not a formal
request.

---

## P4 stage 0 — the run inputs did not load (10 August 2026)

P3 verified the 30 assembled sets thoroughly *as data* and every one of those
statements is still true. **None of them could be loaded by MATSim.** Found by
launching one; see [`DECISIONS.md`](../DECISIONS.md) §9.4.

| Defect | Reach | Symptom |
|---|---|---|
| The day-type filter round-trips through `ElementTree`, which drops the **doctype** | all 30 schedules | MATSim picks its reader *from* the doctype — parse fails at line 2 |
| Removing two thirds of the routes **orphans stop facilities and `minimalTransferTimes` relations** (113 + 42 on S2/WEEKDAY; 2,193 + 1,034 on S0/SAT) | all 30 schedules | `SwissRailRaptorData` dereferences a null array |
| The kerbside patch appends a **second `<attributes>` block** to links that already have one | **6 of 10** run networks — S0, S1, S2c, S6 (59 links), S4 (302), S5 (498) | network DTD rejects it. S2/S2a/S2b/S3 escaped only because `net_base2026` carries no patch rows |

The third is the dangerous one: it hits exactly the six scenarios carrying an E1
road change and leaves the four that don't alone. Fixed; the 30 sets rebuild
byte-identically with patch counts unchanged (54 lanes / 59 kerbside / 8 banned
turns), **all 30 load and run**, and `check_package.py` grew **556 → 657 checks**
asserting all three failure modes per set.

## P4 stage 0 — what a run costs, measured (10 August 2026)

S2 × WEEKDAY, nested deterministic subsamples (1% ⊂ 10% ⊂ 25%), 16 threads,
`ride` teleported. **24 cores, 63.5 GiB.**

| Sample | Persons | Steady per-iteration | Peak resident |
|---|---:|---:|---:|
| 1% | 5,209 | **9.8 s** | 9.8 GiB |
| 10% | 52,758 | **29.9 s** | 18.4 GiB |
| 25% | 131,291 | **~64 s** | 31.5 GiB |

Large fixed cost, near-linear slope: time ≈ 3.1 s + 268 s × fraction, memory ≈
9.6 + 87 GiB × fraction. So **~4.5 min/iteration and ~97 GiB at 100% — a 100%
weekday run does not fit in 63.5 GiB.** Practical ceiling ≈ 40%.

**The P3 sizing is confirmed and then some.** 1,400 sweep runs + 300 headline
runs is 5,100 run-days once each is counted across three day types; at 25% that
is ~765 days of wall clock. The gap is ~3 orders of magnitude, so it closes only
by cutting sweep breadth, replications and day types — **not** by sample
fraction, which is the weakest lever because cost is sublinear in it.

## P4 stage 0 — mode choice was not choosing (11 August 2026)

Three more defects, all in the configuration rather than the data, so the §9.4
load test could not see them — it overrode the mode handling in order to exercise
the artefacts. Full detail in [`DECISIONS.md`](../DECISIONS.md) §9.6.

| # | Defect | Consequence |
|---|---|---|
| 4 | `ride` was declared a network mode that **no link permitted** | `checking 0 nodes and 0 links` for mode ride, then a throw in `PrepareForSim`. **The shipped config could not run even after the §9.4 fixes** |
| 5 | `subtourModeChoice` was never configured, so MATSim's default `modes=car,pt,bike,walk` applied and a `ride` subtour was an **absorbing state** | `ride` sat at **0.18311 in every iteration**, to five decimals. 18.6% of legs were an input wearing the costume of a result |
| 6 | `considerCarAvailability` defaulted to `false` | B1's synthesised car availability was **ignored by mode choice** |

Fixed: `qsim.mainMode=car` (a car passenger is not a second vehicle), `ride`
added to the `modes` of 143,891 links so it is *routed* on the road network,
`travelTimeCalculator.separateModes=false` so it reads the car travel times,
`subtourModeChoice.modes=car,ride,pt,bike,walk` and `considerCarAvailability=true`.
The shipped config now runs unmodified and `ride` moves.

**The seed is now uninformed.** Uniform over the modes each person can use,
conditioned only on B1 car availability — car **14.3%** against an HTS target of
59%, deliberately a bad guess. The P3 informed seed is retained behind
`build_matsim_plans.py --seed-mode informed` so seed dependence can be **tested**
rather than asserted. `check_package.py` now asserts the seed is *far from* the
target, the inversion of the check it replaces. **814 checks**, all passing.

## P4 stage 0 — the seed test, and a model that does not converge (11 August 2026)

Two 1% runs of 250 iterations, identical except the initial mode draw
([`DECISIONS.md`](../DECISIONS.md) §9.7). 2,205 s and 2,419 s wall.

| | car | ride | pt | walk | bike |
|---|---:|---:|---:|---:|---:|
| Uninformed, iteration 0 | 0.143 | 0.223 | 0.101 | 0.323 | 0.209 |
| Informed, iteration 0 | 0.564 | 0.183 | 0.019 | 0.209 | 0.026 |
| **Uninformed, iteration 250** | **0.147** | **0.664** | 0.059 | 0.043 | 0.088 |
| **Informed, iteration 250** | **0.201** | **0.649** | 0.049 | 0.031 | 0.070 |
| HTS calibration target | 0.590 | 0.206 | 0.038 | 0.134 | 0.032 |

1. **Seed influence decays but is not gone.** A 42.1 pp gap on car closes to
   5.4 pp — 87% — and the residual cannot be separated from point 2.
2. **The model has not converged.** Innovation switches off at iteration 200;
   ride still moved 0.619 → 0.664 over the last 50 iterations with no new plans
   being created. **`lastIteration=100` is far too low and 250 is also too low.**
   The default is left at 100 rather than replaced by another unjustified number,
   and `check_package.py` now carries a **standing warning** to that effect.
3. **The attractor is wrong, and it is a specification problem.** `ride` has no
   driver-availability constraint, is charged half car's distance cost, and
   consumes no road capacity; only `asc_car_passenger = −0.85` restrains it.
   Points 2 and 3 are probably the same fact — a dominating mode drives the
   co-evolution to a corner, and corners relax slowly.

## P4 stage 1 — the ride constant, constrained to observed occupancy (11 August 2026)

§9.7 left three options open. The resolution is the second branch
[`DECISIONS.md`](../DECISIONS.md) §8.5 already permits — *"constrain them and report
the constraint"* — with the constraining quantity **measured, not chosen**
([`DECISIONS.md`](../DECISIONS.md) §9.8).

**The model produced a physically impossible car.** 4.52 ride legs per car leg is
**5.52 people per vehicle**. Newcastle's observed occupancy, from the HTS driver
and passenger trip counts, is **1.3503** and has been between **1.2493 and
1.3940** in every one of the seven survey years in the file.

| | |
|---|---|
| Constraint derived by | `src/calibrate/measure_mode_constraints.py` → [`params/C4_mode_constraints.json`](../../params/C4_mode_constraints.json) |
| Value | occupancy **1.3503**, passenger:driver **0.3503**, sweep = the observed seven-year spread |
| Also fixed | `ride` was charged **half** the car distance rate. That half was typed in and double-charges — a vehicle's cost is paid once, and at occupancy 1.35 charging both occupants makes aggregate vehicle operating cost 1.35× the real one. The only derivable value is **zero** |
| Solved by | `src/calibrate/solve_asc_ride.py`, interpolating on log(ride ÷ car) to the observed ratio. It **never opens the validation targets**, so it cannot read a holdout row |

**Why this is not ASC absorption:** the constrained constant is *car passenger*;
`asc_lr`, `asc_bus` and `asc_rail` stay at their §8.5 priors. The constraining
quantity is *how many people fit in a car*, not patronage or PT mode share. No
hypothesis in proposal §3 turns on it.

**P4 deliverable 1 exists.** `src/run/` now holds `sample_population.py` (nested
hash subsample; **transit seat capacity scaled with the fraction**, without which
a 10% sample gives every bus ten times its real capacity and crowding silently
disappears) and `run_matsim.py` (deterministic, resumable, records its own run).
`--iterations` has **no default**, because §9.7 shows both 100 and 250 are wrong
and no justified value has been measured.

---

## P4 stage 1 — the with-tram scenario had no tram on a weekday (11 August 2026)

Found by building the metric extractor: it reported **zero** light rail boardings
for S2 × WEEKDAY. Full detail in [`DECISIONS.md`](../DECISIONS.md) §9.9.

`S2.zip` carries 252 weekday light rail trips and the mapping keeps all of them.
But **pt2matsim groups trips into a route by stop sequence, not by service**, so
each of the two light rail routes holds 275 departures — 74 Saturday, 75 Sunday
and **126 weekday** — and both are *named* after a weekend trip. The day-type
filter keyed on the route name.

| | |
|---|---:|
| Routes whose departures span more than one day type | **233 of 1,714 (13.6%)** |
| Departures placed in the wrong day type | **1,261 of 4,269 (29.5%)** |
| Weekday service delivered vs true | 1,747 vs 2,139 — **18% short** |
| Saturday / Sunday delivered vs true | **18% / 19% over** |

**A weekday S2-versus-S0 comparison would have measured the effect of nothing at
all**, and reported it confidently.

**Why the check passed.** It asserted the split partitions the *route set*
exactly — 1,231 + 291 + 192 = 1,714. True, and the wrong invariant: partitioning
routes is not partitioning service when a route is not day-type homogeneous.

Fixed by filtering **departures** rather than routes, still on the already-mapped
schedule, so §3.5 holds unchanged. Light rail is now 252 / 148 / 150, matching
the GTFS calendar exactly. Two checks replace the old one: departures partition
exactly, and **the intervention is present with departures in every day type** —
light rail for S2/S2a/S2b/S2c/S4/S5, the shuttle for S1, the BRT for S3, and
correctly nothing for the S0 and S6 counterfactuals. **860 checks.**

The three `asc_car_passenger` candidate runs then in flight were **discarded, not
reported**: a constant solved on a network with no weekday tram is a solve of a
different model.

## P4 stage 1 — analysis layer (11 August 2026)

`src/analyse/` now exists, and holds the two correspondences a fit needs before
any modelled quantity can be compared with a target:

| Script | What it resolves |
|---|---|
| `map_sa1_to_lga.py` | The mode-share target is **Newcastle LGA** and the model covers five (§12.1), but nothing in the package carried SA1 → LGA — `zones_SA1.csv` has SA2/SA3/SA4 only, and SA3 "Newcastle" is not Newcastle LGA. Spatial join against the ABS LGA boundaries already in `data/raw/`: **1,701 SA1s, 0 unmatched**, 390 in Newcastle |
| `map_count_stations.py` | A count target is a two-way total at a point, so it must resolve to links. **116 of 119** stations matched, 189 of 203 links by **name and proximity** rather than proximity alone, median distance 30.6 m. The 3 unmatched — one of them a calibration station — are outside the modelled network and are **reported, not dropped** |
| `extract_metrics.py` | Mode share by LGA of residence, PT boardings by line, link volumes at mapped stations. Reads no validation target, so it cannot see the split |

## What P4 still has to build

Proposal §7.1 makes P4 *"fit to observed counts, Opal boardings, run times;
parameter estimation"*, delivering a **calibrated base** and a **calibration
report** — §8 deliverable 3, *"fit statistics against all validation targets,
with honest reporting of where fit is poor"*. None of it exists yet.

| # | Deliverable | Where | Notes |
|---|---|---|---|
| 1 | ~~**Run harness**~~ **done** | `src/run/` | Nested subsample, transit seat capacity scaled with the fraction, deterministic, resumable, records its own parameters |
| 2 | ~~**Metric extraction**~~ **done** | `src/analyse/` | Mode share by LGA of residence, PT boardings by line, link volumes at the mapped count stations |
| 3 | ~~**Fit statistic**~~ **done** | [`src/calibrate/fit.py`](../../../../src/calibrate/fit.py) | Calibration rows only, and it raises if a holdout row survives the filter. **38 scored + 29 explained = 67**, asserted rather than assumed. A modelled zero is scored at −100%, not dropped — dropping it flattered the count fit by removing the stations where the model fails hardest (issue 19). The output contract now **fails a fit block that does not name its target ids** |
| 4 | ~~**Calibration loop**~~ **done** | [`src/calibrate/calibrate.py`](../../../../src/calibrate/calibrate.py) | Deterministic, resumable by candidate tag, and unable to read a holdout row through **two** independent guards. Derives its search space from the registry: of 38 fields carrying a sweep, **21 are excluded with a stated reason** and the mode constants are unreachable because they are `held_fixed` under §8.5. Refuses to move more than the **4** independent numbers the objective contains. Counts are scored but never optimised against (§9.14) |
| 5 | **Calibrated base** + parameter provenance | `params/C5_calibration.json` | **Not met.** The loop exists; it has not been run. The report says so rather than leaving it to inference |
| 6 | ~~**Calibration report**~~ **done** | [`src/calibrate/report.py`](../../../../src/calibrate/report.py) | Computes nothing — every number comes from `fit.py`. Leads with what could *not* be scored and how little independent information the rest carries; constraints reported apart from targets so they cannot be counted as fit |
| 7 | ~~**The outer-loop tolerance**~~ **done: 5 s** | [`DECISIONS.md`](../DECISIONS.md) §9.16 | Derived, not chosen: the target is a **scheduled** 720 s published in whole minutes, so it is known only to ±30 s, and the smallest declared corridor sensitivity is ≈79 s. Held fixed, and carries a **self-policing bound** — a comparison turning on less than twice it must be re-run |

**Deliverables 4, 6 and 7 landed at P4 stage 5** ([`DECISIONS.md`](../DECISIONS.md)
§9.16). Deliverable 5 is the one that remains, and it is compute-bound rather
than design-bound: the loop has to run. The §8.5 ride departure (#16) must still
be taken, and must now be re-taken on the repaired demand, because the ride share
it was to be chosen against has moved.

## P4 stage 2 — the input registry (11 August 2026)

Every value the model consumes that is not read from an immutable raw download
is declared in [`config/registry/`](../../registry) with its units, its
provenance and either a sweep range or an explicit rule holding it fixed. Full
rationale in [`DECISIONS.md`](../DECISIONS.md) §15; the generated reference is
[`docs/reference/CONFIG_REFERENCE.md`](../reference/CONFIG_REFERENCE.md).

**What it replaced:** 316 module-level constants across 45 scripts, a
110-parameter MATSim config per run set, and a handful of CLI defaults. Exactly
**one** of those 316 carried a machine-readable `source` label; 18 carried a
sweep.

| | |
|---|---:|
| Fields declared | **152** |
| …assumed | 72 |
| …literature | 18 |
| …definition | 36 |
| …measured / derived / observed | 5 / 7 / 2 |
| Fields with **no value at all** | **7** |
| Fields **held fixed** under §8.5 | 6 |
| `check_package.py` | 860 → **925 checks**, 1 standing warning |

**Proposal §8.1 is now a schema constraint, not a discipline.** A field whose
source is `assumed`, `literature`, `measured` or `derived` must carry a sweep, a
`held_fixed` rule, or a `derived_from` identity. There is no fourth option, and
`assumed` with no sweep does not validate.

**The six fields with no value are the project's honest edge.** SCATS phasing,
charging dwell and journey-linked Opal carry `value: null` and the resolver
**raises** rather than returning a point value — §0 and §13 enforced
structurally. So do two decisions nobody has taken: the MATSim↔SUMO outer-loop
tolerance (issue #8) and **the iteration count** (issue #5). `run_matsim.py` now
refuses to start without an explicit iteration count, which is the refusal
`--iterations` already implemented, moved into the registry where it binds
everything rather than one argument parser.

**Two factors that governed every P4 result were set in code with no rationale
and no range.** Neither `flowCapacityFactor` nor `storageCapacityFactor`
appeared anywhere in `DECISIONS.md`, `check_package.py` or the P4 checkpoint.
Both are *derived*, and neither is a choice: flow equals the sample fraction,
and storage equals flow. **A correction is recorded in §15.** The registry first
declared the storage exponent *assumed* and swept 0.75–1.0, on the reasoning that
MATSim's one-vehicle storage floor would cause spurious spillback at 1%. The
diagnostic run built to test that died in one second — MATSim rejects any storage
factor different from the flow factor and states the practice is superseded
"since the qsim became a lot more deterministic". The sweep declared values the
tool will not accept, which is the very failure the registry exists to prevent.
Corrected: the field is derived, the harness fails fast, and the check asserts
the equality. **The question the exponent stood proxy for — whether behaviour
moves with the sample fraction — is unaffected**, and is what the 1% versus 10%
diagnostic tests.

**Outputs are declared to the same standard as inputs.** `_run.json`,
`_metrics.json`, `_fit.json` and `_config.json` each carry a JSON Schema in
[`config/schema/outputs/`](../../../../config/schema/outputs), validated at write time. Two
rules are enforced beyond shape: a fit block must **name the target ids it was
computed over**, and `scored + unscorable` must reconcile to the calibration
targets available. Every run directory now carries `_config.json`, the resolved
snapshot — a completed run without one fails its contract, because a result that
cannot state its inputs is not reportable.

**The SUMO corridor layer is migrated and verified.**
[`build_sumo_corridor.py`](../../build/build_sumo_corridor.py) reads the registry;
the netconvert options that are *modelling choices* — left-hand traffic, the
signal controller type, junction joining, turnarounds, crossings — are named
fields rather than entries in a flag list. The corridor was rebuilt and **all
four nets and all seven TLS programs are byte-identical** to the pre-migration
build. Nine intermediates differed, and two further rebuilds **with no code
change** reproduced exactly the same nine, so they are timestamped by netconvert
rather than affected by the change. That refines the P2 claim: byte-identical
rebuild holds for the **nets**, not for `networks/sumo/_work/`.

**The build layer is migrated (P6 cleared).** 52 fields across 13 scripts now
resolve from the registry; runtime consumption went **16 → 68 of 140**. Gated by a
full rebuild in README order with byte-identical output, without re-running the
pt2matsim mapper (§3.5) — the stop→link fingerprints confirm the feeds it was
mapped from are unchanged. **The gate caught three pre-existing defects**: a
hash-seed-dependent set iteration in `build_landuse_parking.py`, wall-clock
timestamps embedded in all 11 GTFS zips making them unreproducible by
construction, and dict-order leaking into two reports. All three were invisible
because the package had not been rebuilt end to end since the manifest was
written — a manifest digest only proves reproducibility if something re-derives
it. See [`DECISIONS.md`](../DECISIONS.md) §15.

**Superseded note.** The rest of
`src/build/*.py` still hold their own constants. Two copies of a number is the
drift this package cannot absorb, so
[`src/registry/check_legacy_drift.py`](../../../../src/registry/check_legacy_drift.py) pins
them together by test — **1 remaining**, one deliberate divergence (the migration removed the other 51 constants outright), one expression
that is not a literal. Writing that check immediately found **four values
transcribed wrongly into the registry**; the code was authoritative and the
registry was corrected. That migration needs a full package rebuild to verify
byte-identically and **has not been run**.

**One determinism defect fell out of the gate.** The committed
`_sumo_build_report.json` recorded `netconvert_seconds`, so its manifest hash
changed on every rebuild even when the nets did not — a committed artefact that
could not be regenerated to the same bytes. Timings moved to the gitignored work
directory; the report is now byte-identical across consecutive builds and the
manifest was regenerated. The defect predates this change.

**The corridor has been built four times and simulated zero times.** No SUMO run
harness exists. The fields one would need are declared, and two carry no value on
purpose: `RUN.sumo.replications` (issue #6) and
`E.coupling.outer_loop_tolerance_s` (issue #8).

**Driving it:**

```bash
# a committed overlay - the reproducible way to vary a run
cp config/runs/example.json config/runs/my_run.json
python src/run/run_matsim.py --scenario S2 --day WEEKDAY --run-config my_run

# a one-off, checked against the same sweep and held-fixed rules
python src/run/run_matsim.py --scenario S2 --day WEEKDAY \
    --set RUN.sample.fraction=0.10 --set RUN.controler.last_iteration=500

CITYSIM_RUN_SAMPLE_FRACTION=0.10 python src/run/run_matsim.py --scenario S2 ...
```

---

## P4 stage 2 — is the 1% sample representative? (11 August 2026)

Two runs identical but for the sample fraction, 250 iterations, S2 × WEEKDAY.
Full detail in [`DECISIONS.md`](../DECISIONS.md) §9.10. **Neither is a result** —
250 iterations is known non-converged; these are diagnostics.

| Mode | 1% | 10% | difference | HTS |
|---|---:|---:|---:|---:|
| car | 0.1223 | 0.1913 | **+6.91 pp** | 0.590 |
| ride | 0.7213 | 0.7190 | **−0.23 pp** | 0.206 |
| pt | 0.0395 | 0.0044 | **−3.51 pp (9×)** | 0.038 |
| walk | 0.0315 | 0.0123 | −1.93 pp | 0.134 |
| bike | 0.0854 | 0.0730 | −1.24 pp | 0.032 |

- **Ride dominance survives a ten-fold increase in population unchanged** — the
  two trajectories track within 0.006 at every checkpoint. It is a specification
  problem, not a sampling artefact, and §9.7 is confirmed at scale.
- **Non-convergence is identical at both fractions**: ride drifts +0.046 and
  +0.047 between iterations 200 and 250 *after innovation stops*.
- **Car and PT levels do not transfer from 1%.** Calibration against the
  mode-share targets cannot be done there, and the hope that sweeps could run
  cheaply at 1% is not available for those two modes.
- **The car/PT divergence has no established mechanism.** Transit capacity and
  small-sample spillback were both checked and neither survives; recorded as open
  rather than guessed.
- **An unreconciled vehicle capacity surfaced**: the fleet gives light rail 180
  seats and no standing room, while §4.1 records a published maximum of 270 and
  an assumed 60 seated. Because nothing has standing room, the C1 crowding
  multipliers can never apply in any scenario.

**Sequencing consequence.** The dominant distortion is a specification error that
scale does not cure. Coupling SUMO to a demand model in which 72% of legs are car
passengers would propagate it into every corridor number, so **SUMO waits**.

---

## P4 stage 2 — `ride` now requires a driver (11 August 2026)

The §9.10 finding acted on. Full rationale and the §8.5 departure in
[`DECISIONS.md`](../DECISIONS.md) §9.11.

A person may be a car passenger only if their household holds a vehicle **and**
contains another licence holder — derived from B1, not assumed. **22.1% of the
weekday population (115,034 of 521,502) may not ride.**

| | before | after |
|---|---:|---:|
| Illegal ride legs at iteration 30 | 4,723 | **0** |
| Seed ride share | 0.2228 | 0.1712 |
| Ride at iteration 25 | 0.3098 | **0.2548** |

**Two pieces were needed and the first alone did nothing.** MATSim's
`PermissibleModesCalculator` governs only *new* mode choices; it never strips a
mode from a plan an agent already holds. With the calculator alone, 4,723 illegal
ride legs survived 30 iterations because the *seed* had handed those agents a
ride plan that `ChangeExpBeta` kept re-selecting. Fixing the seed as well took it
to zero. Core MATSim honours `carAvail` but has no equivalent for `ride`, so the
calculator is ours: [`src/java/citysim/`](../../../../src/java/citysim), ~40 lines, compiled
by the pinned javac. **The pinned toolchain digests are unchanged** — this adds an
artefact beside the shaded jar rather than replacing one.

**Necessary, probably not sufficient — stated now rather than discovered later.**
The constraint lowers the ceiling to the 77.9% who may ride, and the
unconstrained attractor was 0.72, so it does not bind hard at the corner. Ride was
still climbing at iteration 30 (0.2787). **Whether it now settles near the
observed 0.206 is unmeasured** and needs a converged run at 1% *and* 10%.

---

## P4 stage 3 — the ride constraint measured, and 1% found unusable (11 August 2026)

The §9.11 question answered. Two runs of S2 × WEEKDAY at 250 iterations, 8 threads,
committed overlays, declared pipeline. Full detail in [`DECISIONS.md`](../DECISIONS.md) §9.12.
**Neither is a result** — §9.7 shows 250 iterations is short of relaxation.

**Mode share, Newcastle LGA** — the reportable quantity, not the five-LGA aggregate:

| | 1% | **10%** | HTS |
|---|---:|---:|---:|
| Vehicle driver | 16.01 | **30.85** | 59.0 |
| **Vehicle passenger** | 61.06 | **50.94** | **20.6** |
| mean absolute error | 23.19 pp | **17.43 pp** | |
| passengers per driver | 3.8140 | **1.6512** | 0.3503 |

**Necessary, not sufficient.** Ride fell from 0.72 to 0.56 on the five-LGA quantity
— the largest single move any P4 change has produced — and still lands at **2.5×**
the observed share, with occupancy **4.7×** observed. §9.11 predicted exactly this:
the ceiling is 0.779 and the model settles far below it, so the constraint never
binds where it would matter. **Issue #16 stays open**; the three candidates are live
and the §8.5 departure has not been chosen.

**1% is unusable, not merely unrepresentative (#17).** 1,032 car legs abort at the
30 h horizon against **4** at 10%, and 380 PT passengers board and never alight
against **0**. A tenfold population increase cuts car non-completion **258-fold**,
so it is not proportional to demand: at `flowCapacityFactor = 0.01` an 1,800 veh/h
link discharges **one vehicle every 200 s** and cars queue on arithmetic alone.
This is *flow*, distinct from the *storage* argument §9.10 already ruled out, and
it is the first mechanism for the car/PT divergence to survive measurement after
four died. It also explains why `modestats.csv` and `_metrics.json` disagree: one
records the mode agents **chose**, the other trips that **completed**.

**Confirmed at 25%.** 1% → 10% moved car **+14.8 pp**; 10% → 25% moves it **+1.6 pp**
and ride **−1.1 pp**, so the fraction sensitivity has flattened and the divergence
really was the 1% artefact. The answer stands where the artefact is absent: **ride
settles near 50% against an observed 20.6%**, at **1.535 passengers per driver**
against 0.3503. §9.11's constraint was necessary and is **not sufficient** — measured,
not suspected. The §8.5 departure is now unblocked and unchosen.

**A defect that flattered the fit (#19).** `fit.py` dropped a count station when
the model routed *zero* traffic over it, under a reason that said the station had
not resolved to a link. The M1 Pacific Motorway at Wyee — observed **48,016** AADT,
modelled **0** — was silently excluded, along with Raymond Terrace Road. A modelled
zero is a **result**, and the worst one in the set. Now scored at −100% and flagged:
**38 scored + 29 explained = 67**, counts 31 → **33 stations**, and the count error
honestly worsens (mean −72.1% → **−73.8%**). It exposes a real gap — the model puts
**no cars on the M1 at Wyee** — most likely in the external boundary tier.

**The fit statistic had no tests at all.** [`tests/check_package.py`](../../../../tests/check_package.py)
contained zero checks against [`src/calibrate/fit.py`](../../../../src/calibrate/fit.py) — which
is how #19 survived: a defect that silently *improved* the reported fit, in code the
whole suite never touched. Ten checks now drive the scoring functions on synthetic
metrics, so they need no completed run (`results/` is gitignored and a check may not
depend on one). Verified by reintroducing the defect — **3 checks fail**, and pass
again on restore. **937 checks**, 1 standing warning.

**Three values were governing the model from outside the registry**, found by audit:
`B.counts.station_match_radius_m` (**new field**, 120 m, swept 60–120 on measurement
— it decides which count targets are scorable at all); `sample_population.SEED`,
which held its own copy of 20260810; and `solve_asc_ride.py`, which carried five run
parameters and the −0.85 prior as literals **and called `run_matsim.run()` with the
pre-registry signature, so it could not execute at all**. All now resolve through
the registry. `count_station_links.csv` rebuilds **byte-identical**, which is the
gate. Two orphaned P1 probes were deleted.

---

## P4 stage 3 — trip length by mode, an observable the package always held (11 August 2026)

The HTS carries `TRIP_AVG_DISTANCE` and `TRIP_AVG_TIME` per mode for fourteen
years and **nothing used them**. Mode share says how many people choose a mode; it
cannot say whether they choose it for the right journeys. Full detail in
[`DECISIONS.md`](../DECISIONS.md) §9.13.

Now measured into [`params/C4_mode_constraints.json`](../../params/C4_mode_constraints.json)
on the same principle as the §9.8 occupancy constraint — value from the base year,
**sweep from the observed spread across every survey year**, never an interval
anyone chose — declared as **ten registry fields** (one per mode per quantity,
because the schema takes an interval per field and weakening it would have been the
wrong repair), and reported by `fit.py` beside the fit.

**It is a constraint, not a target.** The 67/143 split is pre-registered and
nothing joins it; `check_package.py` asserts no calibration metric carries a
trip-length name.

**It caught an error the moment it existed, and the error was mine.** A hand
comparison had reported car as "10.16 modelled against 10.20 observed — essentially
exact". That compared a **five-LGA** modelled mean with a **Newcastle-LGA**
published one — the same geography mismatch §12.1 records for the seed. Like for
like, both sides Newcastle LGA:

| mode | modelled km | observed km | ratio |
|---|---:|---:|---:|
| car | 6.36 | 10.20 | **0.62** |
| ride | 8.56 | 9.80 | 0.87 |
| walk | 2.90 | 0.70 | **4.14** |

So car trips are **38% too short, not exact**, and the earlier "ride is 41% too
long" was an artefact. What survives is the part that matters, because a **ratio is
robust to geography**: modelled ride ÷ car trip length is **1.346** against an
observed **0.961**. Observed passenger trips are slightly *shorter* than driver
trips; the model makes them **35% longer** — the signature the §9.8 zero distance
rate would produce. It also puts a number on a distortion nobody had looked at:
modelled **walk** trips run **4.1× their observed length**.

**Why it is in place before the §8.5 departure is chosen.** §9.8 set `ride`'s
distance rate to zero and declared it *derived, not assumed*, on an aggregate-cost
identity — and the observable that would have tested that identity was in the
package all along. A value declared `derived` is only as good as the identity
behind it. Whichever ride candidate is taken can now be judged against an
observable rather than against the mode share it was chosen to move.

**Also unused until now:** `Serve passenger` is **15.7% of observed journeys** —
87,000 a day, the second-largest purpose in Newcastle, larger than commuting. B2
generates none (#11). That is a measured demand component, not the assumption the
issue recorded, and it is the driver side of the same problem.

**942 checks**, 1 standing warning.

---

## P4 stage 3 — the external tier is 0.43% of trips and does not drive (11 August 2026)

Found by investigating the modelled **zero** on the M1 at Wyee that the §9.12
`fit.py` correction stopped discarding. It is not one station. Full detail in
[`DECISIONS.md`](../DECISIONS.md) §9.14; tracked as **#20**.

| | |
|---|---:|
| Motorway count stations, median error | **−97.4%** |
| Every other calibration station, median | −69.6% |
| External boundary trips | **962 (0.43% of all trips)** |
| …of which by car | **6** |
| …by bike, median 96.1 km over 6.35 h | **478** |

**The network is not at fault** — 263 of 314 motorway links carry traffic, so the
M1 is connected and routable. It simply carries ~400 vehicles/day scaled where one
station observes ~45,000. `B.external.interaction_rate` is **0.08, assumed**, and
its own registry entry already says it is *localisable but not yet available*: the
ABS journey-to-work SA2 × SA2 table would settle it (§13).

**Ruled out by measurement:** not permission (all 531 external agents carry
`carAvail=always`, `hasLicense=yes`), not connectivity (all 586 links they start
and end on exist and permit car), not the network. **The mechanism is not
established and is recorded as open rather than guessed** — a 96 km bike trip
costs roughly −140 utils against −38 by car, so the choice inverts the utilities,
and five hypotheses have already died between this and §9.12.

**Not fixed, deliberately.** Both halves are B2 changes, and B2 regenerates the P3
demand artefacts and breaks comparability with every run to date — a planned break,
not one to slip in beside a specification change while a fraction series is being
measured.

**Consequence: no count-based calibration should be attempted until this is
resolved.** Tuning the core network against counts that are missing their through
traffic is the count analogue of the ASC absorption proposal §9 names as the
primary threat to validity.

---

## P4 stage 4 — the external tier was walking to the network (12 August 2026)

§9.14 recorded the external tier's behaviour as open after six hypotheses died.
The seventh was measured. Full detail in [`DECISIONS.md`](../DECISIONS.md) §9.15.

**The mechanism.** `accessEgressType = accessEgressModeToLink` charges `car` and
`ride` a walk from the activity coordinate to the network link. `bike` and `walk`
are teleported and are charged **nothing**. That is harmless for the core
population, whose activities sit on observed POIs inside the network — and not
harmless for the external tier, because **all 201 external zones lie outside the
modelled area**, a median 21.3 km beyond the boundary and up to 128.7 km, while
the road network is clipped to the study area.

| tier | mode | median access walk | median main leg |
|---|---|---:|---:|
| core | car | **0.097 km** | 8.8 km |
| core | bike | 0.000 km | 7.1 km |
| **external** | **car** | **2.656 km** | 46.9 km |
| external | bike | **0.000 km** | 72.0 km |

External car access walk is **27x the core's**, with its top three deciles at
**16.4 / 39.9 / 49.8 km — of walking**. At iteration 0, where the uninformed seed
makes mode exogenous, a car tour with under half an hour of access scores
**+94.21**; one with over six hours scores **−1165.01**, and **48% of them are in
that band**. The tour truncates: **39.0%** of external car tours never get home,
against **13.9%** by bike. **Mode choice was behaving correctly** — the 478
agents cycling 96 km were choosing the only mode that did not require them to
walk to a road.

**Two further defects, found alongside.** Every one of the 531 external agents
carried `rideAvail=always` although the generator builds them household-less, so
§9.11's own rule was bypassed for the whole tier and **432 of 962 external trips
were car passengers with no possible driver**. And the tier is not a ring: all
201 zones sit in one SA4 to the north-west (SE/S/SW = **0** zones), so the M1
gap is **outside the tier's declared scope** rather than a tier-size problem —
which corrects the framing in issue #20.

**The repair**, on the standard boundary treatment: external demand now enters
at an **external station** on the cordon, on a real link, and the journey beyond
the study area is not modelled. The cordon set is *derived, not listed* — a node
is a crossing if it is the nearest cordon-class node to at least one external
zone, giving **42 crossings** — and each agent enters through the one minimising
`d(zone, cordon) + d(cordon, destination)`.

`Serve passenger` also became its own tour purpose. It was mapped to NHB and
folded into the discretionary tours, which kept the trip **rate** and lost the
trip **type**: an escort was a two-hour discretionary stay made by anyone rather
than a five-minute drop-off made by a driver. **Issue #11's premise is corrected
— the demand was not absent, it was mistyped.**

| | before | after |
|---|---:|---:|
| External leg length, median | 54.2 km | **21.6 km** |
| External destination placement | 5,385 jittered | **5,408 on an observed attractor**, 59 jittered |
| Serve-passenger share of weekday legs | **0** | **14.53%** (observed 15.7% of journeys) |
| Week trip rate vs HTS 3.473 | 3.397 (−2.2%) | **3.418 (−1.6%)** |
| Seed ride share | 0.1712 | 0.1620 |

**This is a planned comparability break.** B2 was regenerated, so the three
`ride_sufficiency_*` runs are historical and no earlier run shares this demand.

**Not repaired, deliberately:** the M1 and boundary through traffic, which needs
an external-station matrix seeded from cordon counts and is a scope decision
rather than a defect fix. **The §9.14 consequence stands: no count-based
calibration until it is resolved.** `B.external.interaction_rate` stays assumed
and swept.

## P4 stage 4 — mode coverage, checked rather than assumed (12 August 2026)

Every mode the HTS reports is carried by the model, and the one approximation is
named rather than buried:

| observed, Newcastle LGA 2024/25 | model mode | treatment |
|---|---|---|
| Vehicle driver **59.0%** | `car` | network mode, queue-simulated |
| Vehicle passenger **20.6%** | `ride` | network-routed, teleported in the qsim |
| Public transport **3.8%** | `pt` | scheduled, all four sub-modes |
| Walk only **13.4%** | `walk` | teleported |
| Other **3.2%** | `bike` | **approximate**: HTS "Other" also holds taxi, motorcycle and rideshare ([`fit.py`](../../../../src/calibrate/fit.py)) |

Public transport is not a single mode in the model either. S2 x WEEKDAY carries
**261 lines, 1,270 routes, 2,139 departures**:

| sub-mode | lines | routes | weekday departures |
|---|---:|---:|---:|
| bus | 238 | 996 | 1,448 |
| heavy rail | 21 | 270 | 332 |
| light rail | 1 | 2 | **252** |
| ferry (Stockton) | 1 | 2 | 107 |

**Freight is not modelled, and the comparison accounts for it**: traffic counts
are compared against the **light-vehicle** column, with the heavy share measured
at **6.52%** (`B.counts.heavy_vehicle_share`) rather than assumed.

## P4 stage 4 — a run replay, from the event stream (12 August 2026)

`src/analyse/` gained three scripts that turn a completed run into an overhead
animation of the simulated day. MATSim's own viewer (OTFVis) is a contrib and
the pinned jar carries **no contribs at all**, so it is unavailable and adding it
would be a toolchain change — a model change. Everything needed is in the
outputs: `entered link` / `left link` events give the time a vehicle occupied
each link, and the run's own network gives the endpoints.

| script | what it does |
|---|---|
| [`replay_events.py`](../../../../src/analyse/replay_events.py) | streams an event file once, interpolating a position per vehicle per frame |
| [`build_basemap.py`](../../../../src/analyse/build_basemap.py) | roads by class with lane counts, rail, light rail, water, green and the coastline |
| [`build_replay_page.py`](../../../../src/analyse/build_replay_page.py) | assembles one self-contained page; geometry is centimetre-precise, so it holds up at a 10 m view |

The lane-level geometry is **the SUMO corridor network's own** — netconvert
resolves each edge into per-lane polylines with a width, which is what an HD map
format carries. **17,188 lane centrelines**, corridor only. Two new Overpass
layers were fetched for the basemap (`water`, `green`); both are ODbL like every
other OSM-derived layer and **neither has a model consumer**.

The output page is **not committed** — it carries megabytes of payload and this
repo does not commit bulk data. The scripts are the committed artefacts. Every
page states its run, sample fraction and iteration count, and carries a
**"diagnostic, not a result"** flag.

---

## P4 stage 5 — the repaired demand measured (12 August 2026)

The first run on the §9.15 demand, S2 × WEEKDAY, 10%, 250 iterations, seed
20260810, `ride` distance rate still at zero — so it isolates the demand repair
and nothing else. Declared pipeline; `rc=0`, 2.05 h, 23.87 s median iteration.
**Not a result:** 250 iterations is measurably short of relaxation (§9.7).

| Newcastle LGA | pre-repair | post-repair | Δ | HTS |
|---|---:|---:|---:|---:|
| Vehicle driver | 30.85 | **32.54** | +1.69 | 59.0 |
| Vehicle passenger | 50.94 | **50.03** | −0.91 | 20.6 |
| Public transport | 0.99 | 0.83 | −0.16 | 3.8 |
| Walk only | 0.80 | 0.75 | −0.05 | 13.4 |
| Other | 16.43 | 15.86 | −0.57 | 3.2 |
| MAE over 5 targets | 17.43 pp | **16.83 pp** | −0.60 | |
| passengers per driver | 1.6512 | **1.5376** | | 0.3503 |
| ride ÷ car trip length | 1.3462 | **1.3516** | +0.005 | 0.9608 |

**Repairing the external tier and typing 14.53% of legs as escort trips did not
touch the ride problem.** Ride stays near 50% against an observed 20.6%. That is
confirmation rather than disappointment: it puts the distortion in `ride`'s
specification, where §9.17 says it is, and closes the demand-side line of
enquiry that §9.15 opened.

**§9.17's premise survives the demand rebuild.** The ride ÷ car length ratio the
departure was justified against moved 1.3462 → 1.3516 — that is, not at all. Had
it collapsed on repaired demand, §9.17 would have been justified by an artefact.

**Post-innovation drift, measured on this run:** ride still moves **+0.0367**
between iterations 200 and 250 after new plans stop being created. §9.7's finding
holds on the repaired demand: the model has not relaxed, and **#5 remains open**.

---

## P4 stage 6 — the issue backlog worked through (12 August 2026)

Twelve issues were open. Each was checked against the code and the data rather
than against its own description; several had been overtaken by later work.

| issue | outcome |
|---|---|
| **#17** car/pt diverge with sample fraction | **closed** — the mechanism was established at §9.12 and the issue predates it: `flowCapacityFactor = 0.01` discharges an 1,800 veh/h link once per 200 s, 1,032 car legs abort against 4 at 10%, and 10%→25% moves car only +1.6 pp |
| **#13** target identifiability | **closed** — the reporting rule it asked for is enforced, not remembered: `fit.py` refuses to emit a statistic without naming its target ids, and `scored + unscorable == 67` is asserted |
| **#21** gradient and walk decay reach nothing | **closed** — both are now named in `not_representable`, so the §9.3 register is complete |
| **#12** the transit capacity floor | **closed** — and it was worse than recorded: `RUN.sample.transit_capacity_floor` was declared and **swept 1–4** while the code held a literal `1`, so the sweep moved a number nothing read |
| **#10** three count stations outside the network | **closed** — answered, not fixed: they lie outside the five-LGA clip, a scope decision (§1), and closing it would mean re-running the mapper (§3.5). Reported with that reason (§9.20) |
| **#20** boundary through traffic | **halved** — the Raymond Terrace Road mis-match is fixed (§9.20); the M1 demand gap is a scope decision and **stays open** |
| **#18** light rail capacity | **halved** — the light rail vehicle now carries its published 270 (§9.18); bus, rail and ferry standing room needs a source and **stays open** |
| **#14** P4 deliverables | **corrected** — it claimed 4–6 were not started; the loop and the report landed at §9.16. Only deliverable 5 remains, blocked on a decision |
| **#16, #5, #9, #6** | **open, correctly** — each needs a run or a decision, not code |

### What the fixes changed

**#12 — a swept parameter that reached nothing.** `sample_population.py`
resolved the seed from the registry and then floored capacity at a hard-coded
`1`. Now `RUN.sample.transit_capacity_floor`, passed from the run's own resolved
config.

**#18 — the light rail vehicle carries the capacity that was published.**
180 seats and no standing room was pt2matsim's generic tram default. Now
270 = 60 seated + 210 standing, the seated split assumed and swept, the standing
count derived (§9.18). Because *nothing* in the fleet had standing room, the C1
crowding multipliers were inert by construction — the #21 defect class again.

**#20 / #10 — a count of one road is not a count of its neighbour.** The station
matcher accepted the nearest link of any name when no name matched, which
attached Raymond Terrace Road (11,810 AADT) to a one-lane Dockyard Road and
scored the model against it. It also rejected `Red Head Road` ↔ `Redhead Road`
and `St James` ↔ `Saint James` as mere proximity. Both repaired (§9.20).
**All 195 matched links are now name-and-proximity; none is proximity-only.**
The count fit improves −72.2% → −69.9%, and **that improvement is a wrong
comparison being withdrawn, not the model getting better.** The M1 at Wyee is
untouched and still scores −100%.

### A live view of a run in flight

`src/analyse/run_monitor.py` serves a run on loopback and `run_matsim.py` prints
the url as it launches MATSim:

```
live view: http://127.0.0.1:8731/
```

Progress against target with an ETA from the observed iteration time, the mode
and score trajectories, and the drift after innovation switches off — the direct
read on #5. **An observer only:** it reads the run directory, holds no lock and
writes nothing, so it is not part of the run identity and cannot alter a result.

**It is deliberately not a live map**, and that was measured rather than assumed
(§9.19): events are written every tenth iteration, and when they are, the whole
30 h day lands in ~50 s of wall clock — about 2,000× real time — then nothing for
minutes. `replay_events.py` remains the instrument for what a finished run did in
space.

**Registry: 164 → 171 fields.** `check_package.py` caught a hard-coded constant
in the new module on its first run, which is the rule working rather than being
remembered. **All checks pass, 1 standing warning** — `lastIteration`, which is
#5 and is supposed to be there.

---

## P4 stage 11 — walking was priced with the parameter for walking to a bus stop (13 August 2026)

The walk↔bike inversion §9.27 confirmed as structural turns out to be **one
mistranslated parameter**, and it took public transport down with it. Full
detail in [`DECISIONS.md`](../DECISIONS.md) §9.28.

`build_matsim_run_inputs.py` set walk's mode-scoring rate from
`C.time_weights.beta_walk_access` — the appraisal weight on walking to a stop
**inside** a PT journey, not the value of time for a walking trip. Effect,
computed from the shipped config:

| | walk | bike | car |
|---|---:|---:|---:|
| weight applied | **2.00** | **1.30**, a bare literal | 1.00 |
| effective util/hr | 33.92 | 22.05 | 16.96 |
| **util per beeline-km** | **11.666** | **1.896** | 0.61 |

**Walk beat bike only below 174 m**, against an observed mean walk trip of
**700 m** — so the 0.13% share was arithmetic, not behaviour. No published
calibrated MATSim scenario prices walking above ~1.15× car; Melbourne AToM,
estimated on Australian revealed preference, uses **1.04×** and prices *cycling*
dearer per hour than walking. Newcastle had that ordering inverted.

**It was half the PT collapse too.** MATSim scores PT access, egress and
transfer walk legs with the **`walk` mode params**, in scoring and again in the
raptor router. A 5 km PT trip cost **−18.29 utils before any in-vehicle time**,
**−9.33 of it (51%) the walk at each end**. Walk and PT were one failure.

### What changed

| | was | now |
|---|---|---|
| walk mode time weight | `beta_walk_access` = 2.00 | **`C.time_weights.beta_walk_mode` = 1.04**, swept 1.0–1.3 |
| bike mode time weight | literal `1.3`, no registry field at all | **`C.time_weights.beta_bike_mode` = 1.21**, swept 1.0–1.3 |
| `subtourModeChoice.behavior` | MATSim default — **an agent with an open subtour could not change mode at all** | `betweenAllAndFewerConstraints` |
| `probaForRandomSingleTripMode` | MATSim default 0.0 — no single-trip escape from a bike subtour | 0.5 |
| `coordDistance` | MATSim default 0.0 | 100 m |
| `maxBeelineWalkConnectionDistance` | MATSim default 100 m | **300 m** |
| `C.asc.cycle` | held fixed at the §8.5 prior | **departure logged**, status `placeholder`, to be *constrained* against measured trip lengths — **point value deliberately not moved** |

**The PT transfer radius matters more than its size suggests.** No raw TfNSW
feed carries a `transfers.txt`, so the schedule holds **zero**
`minimalTransferTimes` and that one parameter creates *every* interchange in the
model. At the unset 100 m default the light rail at Newcastle Interchange
reached Stand A (49.0 m), Stand B (95.1 m) and the heavy rail platforms
(53.9–57.8 m) but **not Stand C at 119.2–139.0 m** — the regional bus and NSW
TrainLink connection. **Hypothesis A3 falsifies on generalised journey time
rising for external-origin OD pairs, and that is the external-origin
connection.**

**Seven declared, swept values were reaching nothing.** The config template
wrote literals for `subtourModeChoice.modes`, `chainBasedModes`,
`considerCarAvailability`, `routing.networkModes`, both teleported speeds and
the beeline factor, while every one had a registry field carrying a
`matsim_param` binding. The #12 / #21 defect class again, and the drift check
could not see it because these were template strings rather than module
constants. All now resolve from the registry.

**Registry 172 → 178 fields.** 30 run-input sets rebuilt with route and
departure counts unchanged; `check_package.py` **1,107 checks**, 1 standing
warning. The five new checks were verified by reintroducing the defect — **5
fail, and pass again on restore.**

**Not done, deliberately:** the bike teleport speed is left at 4.2 m/s with its
sweep widened to 3.1–5.5 rather than repinned, because published MATSim practice
(3.14 m/s) and ATAP M4 (~15 km/h) disagree and neither was dismissed. Car still
pays **no parking charge anywhere in the scoring** and carries no daily cost —
recorded, not fixed. **Nothing has been run on the changed specification.**

---


---

## Board narrative retired 30 August 2026 (DECISIONS.md §9.132)

*The sections below were the hand-written body of `STATUS.md` as it stood at commit `3e5b036` (after PR #100), moved here verbatim when the board became one page. They are a dated record: task states, counts and timings are as of the date each row carries, and nothing here is current state. The current position per topic is in `../positions/`; the board is `../STATUS.md`.*

## ✅ The rebuild batch (4.1) is DONE — the point of no return was crossed 16 August

The issue #32 re-harvest ran to completion over the boundary-derived extent
(2.02× the old rectangle) and the whole chain was rebuilt on it in one batch:
network layers, gradients (DEM tile set now **derived** from the boundary —
100% coverage), speed zones, corridor attributes, scenario GTFS feeds, one
pt2matsim build of **all 15 feeds (0 unmapped stops each)**, land use, parking
prices, attractions, B2 demand with the five demand fixes, MATSim plans, and
the 30 run-input sets. `tests/check_package.py`: **1,456 checks, ALL PASSED**,
2 standing warnings. Verified gates: every OSM layer larger than its
`osm_pre_issue32/` counterpart; core SA1s without a road node **99 → 4, with 0
agents in them** (all 35,365 stranded agents are on the network); network link
speeds agree with `A1_road_edges.csv`. **Every run made before this batch is
incomparable with every run after it** ([`DECISIONS.md`](DECISIONS.md) §3.5) —
which is why `results/` was already empty when it landed.
`networks/osm_pre_issue32/` remains the pre-repair reference copy.

## Where the build is

| | |
|---|---|
| Phase | **P4 (calibration), in progress** — **8 of 9** deliverables met (deliverable 5 met 24 Aug in the §9.50 constrain-and-report sense, §9.64); deliverable 0 (0b backlog #63) still open |
| Blocking state | **THE MACHINE IS IDLE - no arm runs. THE PACKAGE ON DISK IS INCONSISTENT (§9.131):** `demand/population/B1_synthetic_population.csv` was rebuilt at 19:31 on 30 Aug with the measured licence rates (612,634 persons), but the demand chain was stopped at the user's direction at handoff mid-way through the WEEKDAY chains; the partial `B2_activity_trips_WEEKDAY.csv` and `B2_escort_bindings_WEEKDAY.csv` were deleted, so WEEKDAY chains are ABSENT and SAT/SUN chains, the plans and the 30 run-input sets are the F20 build on the old population. **First build of the next session:** `python src/build/build_activity_chains.py && python src/build/build_matsim_plans.py && python src/build/build_matsim_run_inputs.py`, then `normalise_eol` / `build_manifest.py` / `normalise_eol`, `tests/check_package.py`, a smoke (`run.py --run-config smoke --force`) and the F21 arm (`run.py --run-config f21_gate_10pct --detach`, overlay to be written as a copy of `f20_gate_10pct`). The F20 arm `aborted_20260830T184955_300it_10pct` was stopped at iteration 11 (F20 to iteration 10). NEVER compare across the F21 boundary, a sample fraction or a network build. |
| Committed data package | **501 files** (the licence snapshot, the ABS population by age and the measured licence rates joined it, §9.131; the disclosed pt boardings targets, §9.130; the three shared-ride binding tables, §9.124) in [`data/MANIFEST.csv`](../data/MANIFEST.csv) · `check_manifest.py` passes · `check_package.py` **ALL PASSED** (2 standing warnings; it prints its own check count, which is why one is not restated here) — **but it was NOT passing on arrival this session and this cell said it was** (§9.117): two failures stood on `main`, a `decisions_ref` naming a record that was never written (§9.93, cited by 2 fields) and three false `consumers` claims. Both classes are repaired; **run the suite before believing this cell** — now a portable harness over city-owned expectations ([`cities/newcastle/tests/package_expectations.json`], #62 B4) |
| Input registry | **414 fields** (§9.130: +`CAL.pt.weekday_factor` 1.0727 - the weekday uplift that states a disclosed all-days boardings count per WEEKDAY; §9.129: +`B.ride.shared_lift_hash_bucket` 0.05 - a shared-ride pair must share a sampling-hash bucket, so any nested sample at a multiple of it keeps both without preferring low-hash households as drivers; §9.128: +`B.ride.declared_pair_meeting` = `driver_detour` - a declared pair whose links differ is served by the driver detouring through the passenger's origin and destination links, the passenger boarding and alighting at their own; §9.125: +`CAL.mode_split.truck_driver_journey_share` 0.0050729 (measured, the target LGA's G62 Truck cell, asserted on every build) and +`B.truck.resident_trip_share` 0.002993 (derived by the motorbike carve's identity) - residents who drive a truck for a living, carved and locked like motorcyclists; §9.124: +`B.ride.shared_lift_scope` = `same_sa2_od` - the fourth binder pass, car-less residents' direct tours bound to non-household drivers on the same SA1-to-SA1 trip, built and queued; §9.122: +`B.motorbike.carve_resolution` = `sa1_thinned` - the carve at the resolution G62 observes it, built and queued for the next family; §9.121: +`RUN.transit_router.direct_walk_basis` = `network` (derived - the walk the router compares must be the walk the agent would make) and +`RUN.transit_router.direct_walk_factor` 1.0, MATSim's default that had reached every config undeclared; §9.120: +`RUN.transit_router.search_radius_m` 1000 and +`RUN.transit_router.extension_radius_m` 200 - MATSim's jar defaults that had governed every submode's access reach, the ferry's included, while declared nowhere; +`B.mode.seed_method` = `full_choice_set`, `RUN.replanning.max_agent_plan_memory` 5 → 8 inside its sweep, `B.taxi.min_unaccompanied_age` now also read by the plans builder; §9.115/§9.116: +`CAL.mode_split.vehicle_driver_level`, +`CAL.mode_split.motorbike_driver_journey_share` (both measured, and now ASSERTED against their acquired sources on every `build_mode_targets.py` run), with `B.motorbike.trip_share` moved `assumed` → **`derived`** from the two of them; §9.106: +`B.mode.walk_feasible_km`, +`B.mode.bike_feasible_km` (both derived); §9.105: +`B.ride.unpaired_fallback`; §9.100: +`CAL.pt_split.station_scope`, +`CAL.pt_split.break_ratio`, +`CAL.pt_split.lr_observed_stop_share`; §9.99: +`A.taxi.fleet_representation`, +`B.taxi.vehicle_trips_per_day`, +`B.taxi.fleet_size` (derived), +`B.taxi.max_wait_min`, +`B.taxi.deadhead_min`; §9.91: +`CAL.taxi.lga_concentration`; §9.90: +`A.crossings.closure_source`, +`A.crossings.freight_closures_per_day`, +`A.crossings.rail_match_radius_m`; §9.88: +`A.signals.control_regime` and six `A.signals.scats.*` algorithm parameters, all bound into the emitted `scats` module; §9.87: +`CAL.pt_split.window_months`, +`CAL.mode_split.commute_transfer_tolerance`, +`CAL.truck.count_year_from` and the two `CAL.gate.*` acceptance thresholds; §9.85: +`RUN.replanning.time_mutation_range_s` and +`B.ride.bound_pairing_window_min`, derived from it; §9.84: +13 for the joint-tour binder, the taxi/bike age gates and gradient link speed; §9.82: +`B.ride.escort_coherence_rate`; §9.77/§9.78: +`A.crossings.representation` and `A.signals.tsp.priority_group` gates, +`RUN.routing.pt_submode_scoring`, +`B.census.thin_cell_min_journeys`; seven 0b source upgrades incl. CWANZ bike availability 0.493) — every one with units, provenance and a sweep, held-fixed rule or derived identity; ledger **0** with `--strict` gating CI |
| Run inputs assembled | **30** scenario × day-type sets, **regenerated 30 Aug 12:40 on the §9.120 population (family F15)** - every set now loads a population with 2-6 plans per person (the full choice set) and the `boundRideTrips`/`boundDriveTrips` attributes, and its config carries `maxAgentPlanMemorySize` 8; before that, **regenerated 30 Aug 02:13 at the §9.116 rebuild (family F14)**: each config carries the signals module + generated plans, `usingFastCapacityUpdate=false`, the time-variant network + crossing change events, `travelTimeBinSize` 300, taxi in both vocabularies with blended fares via the `fare` module, the `swissRailRaptor` submode mappings + per-submode modeParams, `tramPriority` (bus-keyed on S3), PassingQ, `ridePairing`, the split thread pools and the per-mode vehicles file the harness re-emits per run; networks carry the saturation-flow re-capacitation on signalised approaches |
| What is PHYSICALLY simulated (measured 20 Aug, §9.49–§9.55) | **EVERY person-transport mode is in the mobsim**: `car`; **`truck`** PCE 2.0 (913 trips / 140,380 traversals at 1%); **`motorbike`** PCE 0.4 on the measured G62 anchor (52 trips at 1%); **`walk`** PCE 0.0 capped at 1.25 m/s — the sidewalk in queue arithmetic (9,050 trips at 1%); **`bike`** PCE 0.2 at 4.2 m/s (2,311 trips); **bus** 1,448 / **rail** 332 / **tram** 252 / **ferry** 107 transit vehicles; **`ride`: every surviving ride trip is a passenger PHYSICALLY IN a household car (§9.53), and an unpairable ride trip re-modes to physical walk (§9.55)** — final probe iteration: ride = 67 trips, all boarded. Remaining teleports: the PT access/egress stubs (declared helper, §9.54) and the counted boarding-miss fallback (5–6/iteration, the ×6.91 window layer). **Taxi/rideshare: A MODE since §9.77** — one blended priced point-to-point mode, routed on the congested car network (probe: 1.4–2.1% of LGA trips at 1%, car-like speeds), fares from the archived Fares Order 2025 + literature rideshare rates, volume reported against the 15–25k/day band as a constraint |
| **Ride pairability — the repair is MEASURED to work (§9.48)** | Pre-repair, **0.10% (25%) and 0.04% (10%) of ride trips shared an origin–destination pair with a household car trip at any time**. Both causes were fixed (§9.45 sampler, §9.46 binding), and the re-measure arm (`bind1000_25pct`) now puts numbers on the repair: **OD-coincidence 15.31% (23,738 of 155,085 ride trips), declared-regime (`both_links` ±15 min) pairing rate 0.0130 (2,014 trips), direction split non-zero (239 return pairings)**. The realisation gap — 15.31% coincident vs 1.30% paired — is named in §9.48 and deliberately not chased while occupancy sits ABOVE its observed value (0.4855 vs 0.3503, outside the declared range in the flattering direction) |
| Ride scenarios — data grade | **Commute carpooling is RARE and the demand is non-commute**: census G62 (already in the package) gives car-as-passenger **3.35% of journeys to work**, passenger:driver **0.0598**, at SA1 — against an all-purpose HTS `Vehicle passenger` share of 18–32%. OBSERVED: commute (G62), driver-side `Serve passenger` 10–19.5% of journeys, all-purpose share, ride trip length/duration, occupancy 0.35. LITERATURE ONLY: child→school (61% of school trips by private vehicle), elderly driven. **Non-household lifts now have a MECHANISM but still no target** (§9.60, directed by recorded decision): unbound observed-rate escort tours are re-targeted to driverless-household passengers — WEEKDAY binds 55,249 of 55,614 (99.3%, the §9.63 repair skips 31 overlapping bindings) — and a booked passenger physically waits for the car (M0); who-drives-whom stays unobserved, so the household/non-household split is reported, never fitted. Return-trip asymmetry remains a stated limitation |
| Comparability | **FAMILY F21 OPENS AT THE NEXT ARM'S LAUNCH (§9.131)** - the population changes (measured licence rates, per LGA), so nothing run before compares with anything after: not the 10-iteration F20 arm (§9.129, bucket rule + carve pool), the 27-iteration F19 arm (§9.128, driver detour), the 1-iteration F18 arm, the 60-iteration F17 arm, the F16 and F15 arms, nor the F4 arms `README.md` draws from. Never compare across a sample fraction (10% vs 25%) or a network build. Bus keeps its composition-derived trip-share target; heavy rail and light rail are on their DISCLOSED boardings (§9.130) since 30 Aug 19:20 - a reading taken on the earlier trip-share basis does not compare with one on the boardings basis. |
| Runs on disk | **30 Aug, sixteenth session, at handoff: NO ARM RUNS.** `aborted_20260830T184955_300it_10pct` is the F20 arm, stopped at iteration 11 at the user's direction (F20 to iteration 10: motorbike 0.378% vs 0.3785, heavy rail 37,520 boardings a weekday vs 6,529, light rail 1,650 vs 2,954); **30 Aug, sixteenth session (§9.129, F20)**: `20260830T184955_300it_10pct` is the **first F20 arm, RUNNING**; `aborted_20260830T170743_300it_10pct` is the F19 arm, stopped at iteration 27 (biased sample composition). **30 Aug, sixteenth session (§9.128, F19)**: `20260830T170743_300it_10pct` is the **first F19 arm, RUNNING** (driver detour); `aborted_20260830T163010_300it_10pct` is the valid F18 arm, stopped at iteration 1 (2,053 of 6,966 ride legs refused on endpoints); `aborted_20260830T170153_300it_10pct` is the F19 launch made inline and replaced. **30 Aug, sixteenth session (§9.127, F18)**: `20260830T163010_300it_10pct` is the **first VALID F18 arm, RUNNING** (62,134 sampled persons); `aborted_20260830T161243_300it_10pct` is the first F18 launch, stopped at iteration 2 on the half-sample (31,262 persons). **(§9.126, F18)**: `20260830T161243_300it_10pct` was the **first F18 launch**; `20260830T161030_2it_1pct` its smoke probe (rc 0); `aborted_20260830T141222_300it_10pct` is the F17 arm stopped at iteration 60 with car +1.7% and walk +11% at iteration 50 in its cause. **(§9.121, F17)**: `20260830T141222_300it_10pct` was the **first F17 arm**; `20260830T140930_2it_1pct` its smoke probe (rc 0, router live); `aborted_20260830T140646_2it_1pct` and `aborted_20260830T140727_300it_10pct` died at injector creation on the unbound raptor provider (fixed); `aborted_20260830T132843_300it_10pct` is the F16 arm stopped on the gate at iteration 17 with the ferry's cause measured. **(§9.121, F16)**: `20260830T132843_300it_10pct` was the **first F16 arm**; `aborted_20260830T124711_300it_10pct` is the F15 arm stopped on the gate at iteration 13 with its cause measured (car plans scored under the car-first seed's iteration-0 gridlock; ride pairing 88.8%); `20260830T132445_2it_1pct` is the F16 smoke probe (rc 0). **(§9.120)**: the F14 arm is closed out as `aborted_20260830T083019_1000it_25pct` (died mid-iteration 38, `0xC000013A` console stop, trigger not established; its iterations 1/10/20/30 are the measurements §9.120 rests on); `20260830T124345_2it_1pct` is the F15 smoke probe (rc 0 - the multi-plan population loads, the gate and the re-timing run: 68 declared passengers re-timed at iteration 1); `20260830T124711_300it_10pct` is the **first F15 arm, RUNNING**. `results/INDEX.md` labels every directory by the families in `run_families.json`, which now declares F13, F14 and F15. PRIOR: **All 35 run directories were renamed 24 Aug to the §9.65 runner scheme** `<launch yyyymmddThhmmss>_<iterations>it_<pct>pct`; the old→new map is DECISIONS.md §9.65, and the runner now names every new run itself (`--tag` is gone). **The FIRST VALID RUNS of the all-physical family (§9.62/§9.64, completed 24 Aug)**: `results/20260821T175907_1000it_25pct` (arm A, ex `phys1000a_25pct`) and `results/20260821T180310_1000it_25pct` (arm B, ex `phys1000b_25pct`) — 1000 iterations each, rc=0, `relaxed: true`, `_run.json` + `_fit.json` + C5 written from arm A; arm B is the seed replication (its product is the A-vs-B spread, ≤0.11 pp/mode). Prior families, none comparable to the §9.58+ model: the #5 pilot arms `20260816T022250_1000it_10pct` and `20260817T011703_1000it_25pct` (ex `conv1000_10pct`/`conv1000_25pct`, both rc=0 and `relaxed: true` — [`docs/archived/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md)) and the completed re-measure arm `20260818T235351_1000it_25pct` (ex `bind1000_25pct`, evaluated §9.48 — the LAST run of the §9.46/§9.47 family). Everything else is a PLUMBING/TIMING probe, not a result: the all-physical shakedown `20260820T202754_50it_25pct` (ex `phys50_25pct`), the §9.56/§9.59 events-and-knob probes (`20260821T003843_5it_25pct`, `20260821T131322/T141252/T144513/T152035_5it_25pct`, `20260820T230351/T230710_2it_1pct`), the §9.58/§9.60 verification probes (`20260821T130340/T130835_2it_1pct`, `20260821T155944_2it_1pct`), the §9.68 regenerated-demand verification probe (`20260824T210040_2it_1pct` — return legs pair 347/347 at it-2), the §9.76 DETACHED-launch verification probe (`20260825T033850_2it_1pct` — launched by `run.py --detach` under the Task Scheduler, past `PersonPrepareForSim` to rc=0 with the launching shell gone; its `aborted_20260825T033406_2it_1pct` predecessor died rc=1 on the unmaterialised-tramPriority defect the probe existed to catch, fixed the same hour), the §9.44–§9.55 smoke/pairing probes (`20260818T194826_3it_1pct`, `20260818T205739_50it_1pct`, `20260818T211301/T212802/T214527_10it_25pct`, `20260820T150002/T162958/T165314/T175133_2it_1pct`) and `20260816T015048_2it_1pct` (ex `smoke_postrebuild`). **Every dead run sits at `results/aborted_<launch>_<iterations>it_<pct>pct`, and each is listed with the cause it died of under *Why the dead runs died* in [`results/INDEX.md`](../../../results/INDEX.md)** — regenerate that with `build_run_index.py` rather than counting them here (§9.66; §9.80: `_meta.json` now REQUIRES a `cause`, read from the run's own `matsim.log`): the two §9.72 silent launch deaths of the 4.6.9 arm (`aborted_20260824T212729_1000it_25pct` `failed`, `aborted_20260824T225951_1000it_25pct` `aborted` — attribution open, #70), the two §9.63 SMC crashes (`failed`), the §9.57 stopped arm (135 iterations of trajectory diagnostics preserved), the cancelled 1500-iteration arm (do not relaunch it), the §9.50 base arm instruction stopped at ~iteration 20, and four older dead runs — all `aborted`. **The §9.81–§9.83 gate-loop arms, none of them a result and none carrying `_run.json`**: `aborted_20260825T135734_1000it_25pct` (F6 unfixed, stopped at the iteration-200 gate), `aborted_20260826T060938_1000it_25pct` (F7, §9.81 ride ratchet, stopped at the gate), `aborted_20260826T222352_1000it_25pct` (`failed` at iteration 2 on a mixed chain/non-chain subtour) and `aborted_20260826T233658_1000it_25pct` (F8, §9.82 escort coherence, **stopped on instruction at iteration 163 before the gate**) — all four hold `<n>.trips.csv.gz` at iterations 0, 1, 50, 100 and 150, which is what §9.83 scores them on. **Every run now carries `_meta.json`** (status · started · ended · parameters, §9.66), auto-written at launch and updated at completion/failure/abort, with stale `running` states reconciled by pid at the next harness start; relaunching any dead run needs fresh stated-cost approval |
| Open issues | **`gh issue list --state open` is the count** — a total written here is stale by the next merge, so this row tracks WHAT each open issue is waiting on rather than how many there are. **#84** (§9.80) is the newest: the light rail's boardings were being reported as an ERROR against a target `fit.py` marks unscorable, and the claim may survive where this change did not sweep. **#82** (§9.79): traffic counts run −91.8% across 30 stations with 6 carrying no modelled traffic, and the recorded explanation was retired by §9.41 without a replacement — run-gated on the F6 arm. **After §9.77/§9.78 every open issue is run-gated, data-gated or attended-only — no implementable lane remains**: **#73** (ACTIVATED + S3 bus-keyed; open for the arm-scale measurement and the data-gated movement-level lanes at 16% turn-lane coverage) · **#68** (ACTIVATED; open for the closure-effect measurement) · **#49** (taxi live + Tier C landed; open for the converged band/share measurements) · **#48** / **#30** (repairs built; measure on the F6 arm) · **#50** (measured against arm A — sex-invariance finding recorded; mechanism decision deferred to the F6 re-measure; mode × age stays an acquisition) · **#62** (all six strata landed §9.78; open only for the recorded follow-ups: currency-bearing key names, census-family readers) · **#63** (only the ATTENDED TableBuilder extract remains) · **#66** (capture armed; needs the stall to recur on an arm). |
| **Results** | **No findings about the light rail.** The reference scenario has now run to a relaxed, accounted state on the ALL-PHYSICAL family (§9.64, twice — two seeds), and **deliverable 5 is met in the §9.50 constrain-and-report sense** (C5 exists, feasible=False, five violations stated). Its fit rows are the base model's honest report card, drawn on the front page of [`README.md`](../../../README.md) and set out in [`audit/CALIBRATION_REPORT.md`](audit/CALIBRATION_REPORT.md) — MAE 10.65 pp over five scored mode shares, and the light rail at 1,260 boardings **as a level, since its 3,417 target is unscorable against a 2026 base** (§12.1, §9.80, #84). Not findings: **no counterfactual has run, and nothing in this repository is a finding about the light rail.** |

### Measured run costs — the binding constraint now that #5 is settled

The pre-rebuild pilots are dead and deleted; what survived them was the timing.
The two post-rebuild arms are on disk and evaluated. **Convergence is no longer
what limits the campaign — run economics are.** The figures below are what any
run plan must be costed against, and the standing directive stands: no multi-hour
run without explicit approval.

- **9.8 s/iteration at 1%, ~24–30 s at 10%, 56–58 s at 25%** — so a
  1,000-iteration arm is ~2.7 h / ~8.3 h / ~16 h.
- **Post-rebuild, measured on the completed arms (18 Aug):** median 33.3 s at
  10% (11.0 h, ~29 GiB WS on 30g) and 90.2 s at 25% (30.8 h, ~33–38 GiB on
  40g). Memory model ≈ 24 GiB fixed + 0.09–0.3 MB/agent → a 100% run needs
  ~80–160 GiB heap. One unexplained slow block (25% arm, iterations ~200–293)
  self-recovered — the §9.36-era stall pattern, still unattributed.
- **On the repaired demand (20 Aug, `bind1000_25pct`):** median **105.9 s** at
  25% (34 h 44 m for 1000 iterations, WS ~34–37 GiB on 40g) — ~17% slower than
  the pre-repair arm. Pace was ~66 s/iteration for the first ~150 iterations,
  then 117–160 s through the congested middle, recovering to ~127 s after the
  innovation cutoff; the log never stalled.
- **On the ALL-PHYSICAL model (21 Aug, `phys50_25pct`):** median **261.1
  s/iteration** at 25% on the framework-default single events thread — the
  physical walk/bike event volume saturates it (172–177 s CPU per iteration,
  §9.56). With `RUN.machine.event_handler_threads` = 4: **181–201 s/iteration**
  measured (`evthreads_timing`), ~21% off the wall; the arm itself ran at median
  **234 s/iteration** through iteration 135 (congestion builds faster than the
  5-iteration probe sees).
- **On the §9.58/§9.59 REPAIRED model (21 Aug, `phys_timing2_*` probes, 25% × 5,
  it2–4 medians):** the declared stack (PassingQ + events 4 + replanning
  threads 20) runs ~**233 s/iteration** → **~65 h/arm**; replanning fell 76 →
  33 s (the one clean win), events 12 bought nothing over 4,
  `synchronizeOnSimSteps=false` is a measured 65 s REGRESSION, and
  `oneThreadPerHandler` is measured FATAL (all recorded on their fields,
  §9.59). PassingQ costs ~42 s/iteration over FIFO and stands on correctness
  (FIFO let a 1.25 m/s walker hold a link's queue head against the cars
  behind it). The repaired model is not faster than the wedged one — it
  SIMULATES MORE: the 11.6k walk/bike legs/iteration that used to abort at
  the first junction now walk their whole day. **~10× per iteration is not
  reachable without shrinking the physical work** (measured CPU floor over 24
  cores, §9.59); the available multiplier is FAMILY THROUGHPUT — two
  concurrent arms at qsim 8 + events 4 fit this machine (each peaks ~27 GB)
  and double arms-per-week; iteration count survives contention, duration
  does not.
- **Never run convergence arms concurrently.** Three arms declared 78 GiB of
  heap on a 63.5 GiB machine, Windows grew the pagefile from 8.1 to 19.1 GiB,
  and the 10% arm's median iteration went from ~19 s alone to ~42 s alongside
  the others. Iteration *count* survives contention; iteration *duration* does
  not.
- **One unexplained event, unattributed — do not assume it is gone:** a 10% arm
  iteration took **2,415 s** against a ~20 s median, stalled 37 minutes between
  `PersonPrepareForSim` and QSim start at near-zero CPU (`realT=2237s at
  simT=0.0s`). Not CPU, not GC, not the monitor, not OneDrive. It did not recur
  in ~400 iterations.

### ✅ G2 is EXERCISED, not asserted — a second city runs the framework unchanged

`python tests/check_city_agnostic.py` — **13 assertions, all passing**, and a CI
job on every push. It builds a second city from this city's own declarations
under a different identity (different projection, base year, seed, day types,
**three modes not five**), emits its MATSim config through the same emitter, and
asserts **differences** — a test that only checked the config parsed would pass
even if every value in it were Newcastle's. It hashes `src/`, `config/schema/`
and `run.py` either side to prove no framework file changed while it ran. It
invents no observation and deletes its fixture afterwards.

**Building it found two defects that one city could never expose:**

- **`CITYSIM_CITY` had never worked.** Setting the documented city selector to
  *any* value — including its own default — made every `registry.load()` raise
  `env CITYSIM_CITY matches no registry field`. The resolver read `CITYSIM_*` as
  field overrides and skipped only `CITYSIM_REPO`. Nobody had set it, because
  there is one city and the default applies when it is absent.
- **The contract was over-strict, and its own caveat said so.**
  `required_fields.json` demanded all 292 fields of every city; a three-mode
  city was refused for not declaring bike parameters. Fields now carry
  `required_if_mode`, **derived** from the tool binding rather than judged.

### ✅ The hardcoding ledger — 0 items, and `--strict` is a CI gate

```
python src/registry/check_hardcoding.py            report
python src/registry/check_hardcoding.py --strict   exit 1 if anything is found
```

**The honest starting count was 185, not 95.** The audit had been asking whether
a field key was a SUBSTRING of any source file, which counted a mention in a
comment, a docstring or a test assertion as reach — so the count *fell* when
someone added an explanatory comment. Its constant scan saw only module-level,
single-target, ALL-CAPS, **scalar** assignments, which is a small minority of
the forms a decision takes: it could not see `ACCEL, DECEL = 1.2, 1.3`, a table
of stop coordinates, `def make_bus_shuttle(speed_kmh=28.0)`, or
`add_argument('--iterations', default=100)`. Its coordinate rule wanted a
literal two-tuple, so it reported 3 of this repository's 22 coordinates.

| Question | Was (as counted then) | Honest baseline | Now |
|---|---|---|---|
| Declared but unwired | 37 | 38 | **0** + 7 declared-ahead-of-consumer, each with a written reason |
| Read only by the measurement layer | — | 11 | **0** |
| Config template literals | 44 | 47 | **0** — there is no template |
| Values decided in code | 11 | 67 | **0** + 18 structural exceptions, each with a written reason |
| Coordinates in a script | 3 | 22 | **0** |
| **Inert bindings** (new) | — | — | **0 of 69** — every bound field proven to reach the model |

**The sixth question is the one that matters.** `param_config.reach()` changes
each bound field's value and diffs the emitted config. A field that resolves,
appears in the run's provenance snapshot and moves nothing is this repository's
signature defect, and no text search can see it — `consumers` is a claim, a
substring finds the key in a comment, and reading the code has never once caught
an instance. **69 of 69 pass.** It costs about a second and starts no JVM.

### What replaced the template

`src/registry/param_config.py` **builds** the MATSim config and pt2matsim's two
from the fields that declare a binding. A parameter exists only if a field
claims it or the caller supplies it under one of three declared runtime roles —
a path, the city's own identity, a value **derived** from declared fields — and
`closure()` returns anything else. There is nowhere left to type a number.

`run_matsim.py` **emits** rather than patches. It used to read the shipped
config and rewrite six parameters, so a run overlay setting any other field was
validated against its sweep, written into `_config.json` as the run's
provenance, and reached nothing: the snapshot said one thing and the run did
another. Every declared field now reaches the model.

### Four mis-bindings the emitter found by refusing to write them

| Field | Bound to | Why it is wrong |
|---|---|---|
| `RUN.sample.storage_capacity_exponent` | `qsim.storageCapacityFactor` | an **exponent** into a **factor** — 1.0 against a 0.01 flow factor, which MATSim rejects in one second |
| `C.time_weights.beta_walk_mode`, `beta_bike_mode` | `…marginalUtilityOfTraveling_util_hr` | a **ratio to in-vehicle time** into a **util/hour rate** |
| `A.parking.charged_hours_by_day_type` | `chargedStartHour`, `chargedEndHour` | a per-day-type **window dict** into two **scalar hours** |
| `C.scoring.activity_typical_duration_s` | — | declared in seconds; MATSim reads `hh:mm:ss`, and the template held a second representation of the same value |

### ⚠ One model value changed, deliberately

`build_matsim_network.py` held its own copy of the road class defaults, and the
comment above it said it was kept there *"so that the MATSim network, the SUMO
corridor and A1_road_edges.csv cannot drift apart"*. **They had drifted**, on
six classes and in both directions:

| class | script | `A.road.speed_default` |
|---|---|---|
| motorway | 100 | **110** |
| motorway_link | 60 | **80** |
| trunk | 80 | **60** |
| primary_link | 50 | **60** |
| secondary_link | 50 | **60** |
| service | 20 | **25** |

Nothing compared them: a second copy with no `legacy_symbol` is invisible to
`check_legacy_drift.py`. There is one copy now and **the network takes the
declared speed**, so the next network build changes on those six classes. Taken
because the registry is the declared source of truth and #32 rebuilds the
network anyway.

### Two things the handover brief got wrong

- **`DWELL_CHARGING = 20.0` was NOT pinned by `legacy_symbol`.** §2.7 said it
  was and told the next agent to leave it alone. It carried none, its
  `EXPECTED_DIVERGENCE` entry compared nothing, and it **pinned an `unobtained`
  input in a script** — walking past the one refusal the registry exists to
  make. It now takes the baseline sweep point from the reference scenario's
  overlay.
- **`A.lightrail.tsp_enabled` reached nothing** while all ten scenario overlays
  set it, so S2b was distinguished from S2 only by a literal `0.75` in an
  expression. Both are declared and wired.

`check_legacy_drift.py` now compares **zero** fields, and that is the point:
both `EXPECTED_DIVERGENCE` entries are retired because neither has a second copy
to diverge from.

### What the city restructure changed

**The framework no longer knows it is modelling Newcastle.** Everything specific to the
city — its registry, its scenario/day/run overlays, its acquisition adapters, its data,
networks, schedules, demand, scenarios and params, and the seven builders that encode its
intervention, corridor and history — lives under `cities/newcastle/`. `config/` is now
`config/schema/` alone: the portable half.

- **`src/city.py` is the only module that knows where a city lives.** 338 path literals
  across 46 scripts now resolve through it, and paths stay **city-relative** inside a
  city, so one manifest row means the same thing in every city. The migration was
  verified by regenerating the manifest and diffing it: **376 rows before and after, no
  path added or removed, no hash or byte count changed** — only `produced_by`.
- **The input contract is now stated, not implied.** `config/schema/city.schema.json`
  (identity, and a boundary that must be **derived**, never a typed rectangle), plus the
  generated `required_fields.json` (210 keys) and `layers.json` (119 artefacts, found by
  reading the framework's own `city.path(...)` calls). `python src/registry/check_city.py`
  gates a city **before** it runs, and CI runs it.
- **Constants that were one city's value are declared:** the CRS in seven modules, the
  mode-share filter value in three, the `#34` CBD box and the harbourside search window.
  **Both extents were relocated at byte-identical values** — #34 is still open, and
  relocating a constant is not fixing it.
- **The metrics key `newcastle_lga_pct` is now `target_lga_pct`.** This is a breaking
  output-schema change: **run records written before it cannot be read by `fit.py`.**
  Accepted deliberately in favour of a city-agnostic schema.
- **Two defects found by doing it.** Four scripts assigned a bare directory name as a
  path (`OUT = 'schedules'`), which silently wrote 32 MB of rebuilt GTFS into the
  repository root instead of the city; `check_city.py` now fails on that class, and the
  guard was verified by reintroducing the defect and watching it fail. The `build_manifest`
  CRS string still said **GDA2020** — the §2.6 correction had never reached it either.

**Second pass — the study's records moved too.** This city's research design,
decision log, board, audits, handover notes and generated references are now under
`cities/newcastle/docs/`; `docs/` documents the framework alone, and the three
generators write into the city that owns the document. `build_landuse_parking.py`,
`build_sumo_corridor.py` and `map_sa1_to_lga.py` followed their logic into
`cities/newcastle/build/`. `required_fields.json` stopped copying field
descriptions out of the registry, which had put 213 place mentions inside the one
file meant to be city-free. **Framework-wide place mentions: ~2,900 → 262.**

### What the last two sessions established

**Repository cleanup.** `STATUS.md` was 79% dated narrative; the documents had drifted
from the model (four stale figures, one self-contradictory header, and the §2.6 CRS
correction never propagated to `CLAUDE.md`). Documents are now filed under `docs/`,
`DECISIONS.md` has a topical index, and the project is no longer codenamed after one
suburb (§9.36, #36 tracks the two surviving code identifiers).

**A run now reports itself.** `RunTelemetry` publishes per-mode and per-vehicle-type
counts and per-link congestion **from inside the mobsim**, and `summarise_run.py` closes
out a finished run with `SUMMARY.md` + `_summary.json`. `writeEventsInterval` did not
need to change: a registered handler sees every event on every iteration — the package's
own 26 event files against 251 leg histograms proves it.

**Three defects found by measurement, not by reading** (§9.36):

- **The observer killed a run.** A Windows file-replace threw while the view was reading,
  and the exception propagated out of the handler, terminating a run at iteration 5.
  Telemetry is now structurally unable to reach the mobsim. *An instrument that can stop
  the experiment is not an instrument.*
- **`build_basemap.pack()` silently dropped every segment longer than 327 m**, so the
  simplified LGA boundary shattered and the landmass never filled — the map rendered as
  ocean. `build_replay_page.py` decodes the same payload: **any replay page built before
  this is wrong and must be rebuilt.**
- **A silent default that happened to be right.** The summariser read a registry key that
  does not exist and fell back to a hard-coded `0.8` — the shipped value, so it produced
  the correct answer for the wrong reason.

**Eight of this project's defects are now the same class:** a declared value that reaches
nothing, or a default that is right by accident. Establish reach by **changing a value and
watching the output**, never by reading the code.

---

## The deliverable checklist

Proposal §8 sets six project-level deliverables. P4's own list has grown from
seven to nine: one because the proposal's §7.2 fallback was found never to have
been built, and one because calibrating a model with known-missing demand would
calibrate the wrong model.

### P4 — calibration

| # | Deliverable | State | Where |
|---|---|---|---|
| **0** | **Specification and input completeness** — **NEW, and it gates 5** | ⬜ **not started** | see breakdown below |
| 1 | Run harness | ✅ done | [`src/run/`](../../../src/run) |
| 2 | Metric extraction | ✅ done | [`src/analyse/`](../../../src/analyse) |
| 3 | Fit statistic | ✅ done, 10 tests | [`src/calibrate/fit.py`](../../../src/calibrate/fit.py) |
| 4 | Calibration loop | ✅ done | [`src/calibrate/calibrate.py`](../../../src/calibrate/calibrate.py) |
| **5** | **Calibrated base + parameter provenance** | ✅ **MET in the §9.50 constrain-and-report sense (§9.64, 24 Aug)** — C5 written from the completed base arm with every parameter at its declared value, objective 10.65 pp, **feasible=False with five violations STATED** (occupancy + four trip-length ranges). The report card is honest, not flattering; improving it is the demand-side scoring lane §9.64 opens | `params/C5_calibration.json` |
| 6 | Calibration report | ✅ done | [`src/calibrate/report.py`](../../../src/calibrate/report.py) |
| 7 | MATSim↔SUMO outer-loop tolerance | **Retired 25 Aug with the outer loop it governed (§9.74)** — was ✅ done at 5 s; the §9.16 derivation stands in the record | [`DECISIONS.md`](DECISIONS.md) §9.16, §9.74 |
| **8** | **Transfer-penalty estimate** — proposal §7.2's own fallback | ✅ **met by its own fallback clause (§9.32)**: the estimate is **not possible** from this package and the reason is recorded, so the 3–15 min sweep stands and every headline stays bound to a curve across it. §7.2 needs tap-on/tap-off **timing**; every Opal source held is a monthly aggregate, the stop-level tap data is **holdout**, and no calibration row bears on interchange. Published interchange **times** are the wrong quantity — they would double-count the walk and wait MATSim already simulates. Settled only by a TfNSW unit-record request. | §9.32, §9.21 |
| 9 | Live run view | ✅ **rebuilt** (§9.36) — the run now publishes live telemetry from inside the mobsim: iteration progress, simulated clock, per-mode and per-vehicle-type counts, stuck agents, and a per-iteration congestion map. All 30 run-input sets carry the `telemetry` module, and a finished run writes `SUMMARY.md` + `_summary.json` stating whether it relaxed and whether its accounting closed. **Now actually wired**: the view was rebuilt but never re-connected, so `RUN.monitor.enabled`, `.port` and `.poll_s` reached nothing — every run prints its own `live view:` url before MATSim starts, and `.stall_s`/`.poll_s` were recorded as `consumers: null` while `run_view.py` read them. The port scan was also broken on Windows (`allow_reuse_address` set on `socketserver.TCPServer` itself let three concurrent views bind 8731; two served nothing). The relaxation panel now carries a red/green light against a **declared** tolerance, `RUN.relaxation.drift_tolerance_pp`, which replaced a hard-coded `DRIFT_THRESHOLD_PP = 0.5` in `summarise_run.py`. | [`src/analyse/run_view.py`](../../../src/analyse/run_view.py), [`src/java/citysim/RunTelemetry.java`](../../../src/java/citysim/RunTelemetry.java) |

### Deliverable 0, broken down — the work that must precede a calibrated base

Ordered. 0a is first because it may change what the rest is worth.

| | Work package | Why it gates a calibrated base |
|---|---|---|
| **0a** | **Specification audit.** DONE - the ranked register is [`docs/archived/audit/SPEC_AUDIT.md`](audit/SPEC_AUDIT.md) (§9.25). | **Two near-exact inversions, not five miscalibrations:** car -26.5 / ride +29.4 and walk -12.7 / bike +12.7. **A1: ride is routed on the network but not simulated in it**, so it realises **55.7 km/h against car's 49.3** - a passenger arrives 13% faster than the car carrying them (#28). A2/A3: ride is not chain-based and bike ownership is silently universal (#31, #29). A4: walk's 18x deficit may be trip lengths, not scoring (#30). **B1 prevented damage - #24's business-travel premise is false.** **A1's defect is verified; its mode-share effect is WITHDRAWN (§9.27) - both arms ran at 250 iterations, and the pre-fix model at 1000 fits BETTER (33.8 pp) than the post-fix model at 250 (44.6 pp), so car/ride was largely non-relaxation. Walk/bike does NOT improve at relaxation and is confirmed structural (#30, #29).** |
| **0b** | **Derive what can be derived.** Move as many of the 78 `assumed` fields as the data supports to `measured`/`derived`, and reclassify those that are methodological choices rather than empirical guesses. **Realistic target 15–25, not 78** — the HTS held is aggregate tables, so anything about tour structure (intermediate stops, activity durations, second stops) is *not* derivable without a TfNSW unit-record request. Candidates: `B.activity.day_purpose_mix`, `B.activity.p_mandatory`, `B.activity.sat_to_sun_rate` (RMS hourly counts carry dates → real day-of-week), `B.external.interaction_rate` (ABS journey-to-work table, §13 item 11 — obtainable), `A.road.*_default` (observed OSM distributions), `A.lightrail.line_speed_kmh` (GTFS ÷ measured alignment), `C.vot.*` (TfNSW published economic parameters), and `RUN.routing.beeline_distance_factor`, which is **probably a duplicate** of the measured detour factor 1.3376. | 46% of the model's controllable values are educated guesses. Every one carries a sweep, so nothing is hidden — but a calibrated base resting on 78 guesses is a weaker claim than one resting on 55. |
| **0c** | **Fleet capacities. DONE (§9.30).** Bus 44+18, ferry 149+51, rail 98+48, tram 60+210. `literature`; the ferry split is the only published one and is held fixed, rail's seated share is assumed and swept. | **Closed.** Every default overstated the real vehicle, rail by ~2.7×, and **no vehicle in the fleet had standing room at all** — so the C1 crowding multipliers were unreachable in every scenario. They can now bind. |
| **0d** | **The missing demand. DONE in all three parts.** **(1)** boundary/through traffic ✅ (§9.41, seeded from cordon counts, no holdout row); **(2)** work-related business travel ✅ struck on evidence — B2 already generates WB at 2.11% against an observed 2.0% (spec-audit finding B1); **(3)** freight ✅ (§9.49, issue #24 — a physical `truck` mode, smoke-verified). **Deferred to P5:** SUMO pedestrian crossings (a §14 toolchain change; proposed DELETE). | Each added demand ahead of calibration, so nothing needs re-calibrating after them — which was the point of the ordering. |
| **0f** | **Parking price. DONE (§9.31, issue #33).** Derived from the city's own core-zone job-density distribution (p90 = 1,500.9, p99 = 8,710.5 jobs/km²), reaching the model through a `PersonMoneyEvent` handler that charges **car only** from arrival to the next car departure. | **Closed.** The price layer had been declared since P1 and **read by nothing** — a car parked free in a study about city-centre access — and its spatial basis was four hand-drawn boxes, one of which could never match a facility. Known limitation, measured not supposed: the ramp prices suburban malls at CBD rates; the contiguity fix was built and **rejected** because it also excludes the University and John Hunter Hospital, which do charge. Price is common to all scenarios, so it bites on the base calibration rather than on the S-vs-S comparison. |

### Landed from the published catalogue (§9.23, §9.24)

| Input | State |
|---|---|
| **Corridor SCATS site ids** | ✅ **observed.** `A2_signal_control_corridor.csv` declared `scats_site_id` from P2 and left it empty on all 70 rows. TfNSW's Traffic Lights Location inventory fills all 14 intersections, mean match 8.0 m, max 26.4 m. The join tolerance `A.signals.scats_match_radius_m` is **held fixed, not swept** - no output varies across it. |
| **Corridor signal install dates** | ✅ **observed, and deliberately not acted on.** **8 of the 14 corridor signals were installed in 2018 for the light rail**, two named *light rail crossing*; the pre-intervention corridor had **6**. Recorded as an attribute only. Re-deriving the counterfactual from it would reshape the same hypothesis `A.corridor.pre_lr_lanes_per_dir` encodes, which is the B3 test - **decision taken 12 Aug 2026: NO** - the pre-light-rail corridor keeps all 14 signalised intersections and the dates stay an attribute (§9.24). |
| **SCATS phasing** | ❌ still refused. The inventory gives identity, location and install date, and **no phase plan, cycle time or split**. `A.signals.scats_phasing` stays `unobtained` and swept. |

### Declined, with reasons — recorded so they are not re-raised

| Request | Answer |
|---|---|
| Incorporate the 143 held-back targets | **No.** They are the only test the model has. The split was fixed before any fitting precisely so nobody can move a target after seeing a result. They open **once**, at the end. New observables become **constraints** (the §9.8 / §9.13 pattern), never targets. |
| Delete the targets that cannot inform anything | **No.** The 13 Opal card-type rows are *calibration* rows in the pre-registered 210. Deleting them retrospectively changes a set fixed in advance — the move that would let anyone drop whatever the model fails at. They cost one line of explanation and are reported with the reason they cannot be scored. |
| Taxi / motorcycle / rideshare as their own modes | **No target exists.** The HTS reports "Other" as one bucket; IPART's survey measures usage incidence, not Newcastle mode share. Three unfalsifiable modes would be structure pretending to be rigour. |
| Obtain SCATS phasing | **Refused by policy**, documented (§9.21). Proposal §7.2's contingency is now the operative path and binds every headline figure to a stated uncertainty band. |

### Carried over from P0–P2 — now owned by numbered plan tasks

Work carried from earlier phases that no deliverable owned is now owned by the
numbered plan below — the settled rows (GTFS-Realtime, dropped §9.23; *"requests
lodged"*, settled §9.21) and closed #27 (P2 row above: **cannot** be closed —
task 6.4 reports the imputation as uncertainty instead) are removed from this
board. Open carried items and where they went: **#34** → 4.1.6 (its floorspace
question is answerable only after the re-harvest — the verdicts showed
`buildings_cbd.osm` was itself harvested inside the box); **charging dwell field
measurement** → 5.3; **ABS journey-to-work SA2×SA2** and the **day-of-week
split** → 4.3 (deliverable 0b); **pedestrian counts** → 6.1 and **retail
floorspace/vacancy audit** → 6.2 (both block P6, not P4); **2014 timetable,
LiDAR DTM, event attendance** → backlog (nothing depends on them; do not start
before the base works).


### Project-level (proposal §8)

| # | Deliverable | State |
|---|---|---|
| 1 | Reproducible model | 🟡 on track — seeded, pinned, byte-identical rebuilds; not containerised |
| 2 | Open data package | 🟡 **501** files, provenance, licence, lineage — the ODbL/CC-BY split is recorded per row but not yet published (task 7.4) |
| 3 | Calibration report | 🟡 **regenerated from the C5 base (§9.64)** — honest report card, MAE 10.65 pp with five stated constraint violations; improves as the demand-side lanes close |
| 4 | Findings paper | ⬜ not started |
| 5 | Interactive result explorer | 🟡 replay + live run view exist; per-scenario explorer does not |
| 6 | Method note on evaluation gaps | 🟡 **strengthened** — the SCATS refusal is now a documented, citable instance (§9.21) |

---

## What P1 delivered

| | |
|---|---|
| Study area | Newcastle, Lake Macquarie, Maitland, Cessnock, Port Stephens — 4,086 km² |
| Zones | 1,500 core SA1 + 201 external SA1, 222 core DZN |
| Population | 611,915 (2021 Census) → 612,634 synthetic agents |
| Road network | 50,182 edges, 11,434 km, gradient-attached |
| Active network | 40,195 edges, 7,920 km, directional walk-speed factors |
| PT | 5 GTFS eras + 10 scenario variants |
| Validation | 210 targets (67 calibration / 143 holdout). The 119 traffic-count **values** were repaired at P4 ([`DECISIONS.md`](DECISIONS.md) §12.2); the split did not move. |
| Base year | 2026 · CRS EPSG:28356 (GDA94 / MGA Zone 56 — label corrected, [`DECISIONS.md`](DECISIONS.md) §2.6) |

---

## What P2 delivered

**Toolchain, pinned by digest** — `python src/setup/bootstrap_toolchain.py` fetches
Temurin JDK 25.0.4+7, pt2matsim 26.6 (shaded jar) and Apache Maven 3.9.9 into
`.tools/` (gitignored) and records each one's version, URL and sha256 in
`.tools/toolchain.json`; `--run-stack` additionally resolves the MATSim signals
run stack (matsim + signals contrib at 2027.0-2026w25, 201 sha256-recorded jars)
for signal-enabled runs (§9.76, §14). SUMO left the toolchain with the §9.74
descope (#72). `--verify` re-checks every digest and compiles both class trees.

**Corridor attributes, graded by evidence rather than corrected by hand**
(`cities/newcastle/build/build_corridor_road_attributes.py`):

| | |
|---|---|
| Corridor / parallel edges classified | 605 (40 trunk, 84 cross, 417 parallel) |
| As-built trunk lane counts observed in OSM | **87.5%** — the corridor is not 75–98% imputed ([`DECISIONS.md`](DECISIONS.md) §2.5) |
| Turn restrictions resolved to coordinates | 1,385 of 1,386; 10 within 40 m of the alignment vs E1's assumed 14 |
| E1 road variants expressed as edge-level deltas | 195 patch rows; the as-built variant has **zero** — it is the observed network |

**MATSim** (`src/build/build_matsim_network.py`) — one base network,
157,678 links / 73,227 nodes / 23,212 km in EPSG:28356, plus the four E1 road variants as
link-attribute patches over it (so "variants differ only where E1 says" is structural, not
a diff), and all 15 feeds mapped:

| | |
|---|---|
| Feeds mapped | 15 (5 era + 10 scenario) |
| GTFS stops without a network link | **0, in every feed** |
| Artificial link share | 0.4–0.6% |
| Turn restrictions carried into the network | 1,240 `disallowedNextLinks` |

**SUMO corridor — RETIRED (§9.74 descope, executed §9.76/#72).** P2 built 4 nets
(15,666 edges / 211 traffic lights each; all 14 A2 intersections matched, realised
cycles within 1 s of A2) and they were simulated zero times; the builder, the
`RUN.sumo.*` registry section, the package checks and the 12 manifest rows are
removed, and the same A2 declared values now generate the NATIVE MATSim signal
data model instead ([`networks/matsim/signals/`], `build_matsim_signals.py`).

**Checks** — `tests/check_package.py` grew from 180 to 374 lines: stop→link coverage and
fingerprints, orphan links and nodes, variant-vs-base containment, TLS pairing and cycle
fidelity, corridor provenance vocabulary, sweep ranges on every assumed patch, toolchain
pinning. **322 checks, all passing.**

---

## Open items carried forward

Three inputs the proposal named as critical are **unobtained**, and are handled by
**sweep, not by assumption-as-fact** ([`DECISIONS.md`](DECISIONS.md) §0, §13). Formal
requests are outstanding; do not pin any of them to a point value.

| Input | Why it matters | Current handling |
|---|---|---|
| SCATS signal phasing | Corridor run time swings 38% between no priority and full priority (S2 vs S2b) — the largest single uncertainty in the model | Swept, and stays `unobtained` for the 14 modelled sites. The [`design/signalling/`](design/signalling/README.md) dossier maps the mechanics and every data route; operated history for two NON-modelled sites is ARCHIVED (`data/raw/planning_tia/`); **the systematic portal sweep is DONE and EMPTY (§9.78** — 19 applications, PPSHCC-137 remains the only SCATS evidence; watch items in [`tia-harvest-log.md`](design/signalling/tia-harvest-log.md)); the native signals are ACTIVE (§9.77) with assumed-and-swept timings |
| Journey-linked Opal | Needed to *estimate* the transfer penalty rather than sweep it | Swept, 3–15 min |
| Measured charging dwell | Assumed 20 s per intermediate stop; worth 11% of end-to-end run time | Swept |

Also absent: pedestrian counts (none published for Newcastle), frontage-level retail
floorspace and vacancy, parking meter transactions, and a 2014 timetable to validate the
era-1 reconstruction.

**Raised by P2, not yet resolved:**

| Item | Where | Consequence if left |
|---|---|---|
| ~~S2c/S4/S5 GTFS shapes were never extended~~ **Closed at P3 stage 0.** It also affected S0. | [`DECISIONS.md`](DECISIONS.md) §3.4 | Alignments now routed over observed geometry; extension stop sitings anchored on observed features. E1 patch set grew 195 → 414 rows as a result. |
| **pt2matsim is not reproducible run to run** — ~18% of route link sequences differ between identical builds | [`DECISIONS.md`](DECISIONS.md) §3.5 | Every scenario comparison must use **one** build of the network. Comparing feeds mapped in different builds puts an 18% path difference inside the treatment effect. |
| Pre-tram Hunter/Scott cross-section is assumed (2 lanes/direction, swept 1–2) | [`DECISIONS.md`](DECISIONS.md) §3.4 | This is the counterfactual B3 rests on. It must be reported as swept, never as a point estimate. |
| `--osm.crossings` segfaults SUMO 1.27.1 | [`DECISIONS.md`](DECISIONS.md) §3.6 | No crossings/sidewalks in the SUMO corridor. Pedestrians are MATSim's job on A6, so this is acceptable — but do not model pedestrian delay in SUMO. |

---

## The plan — every open task, numbered, with ETA

Every open task and deliverable in the repository, consolidated from this
board, [`docs/archived/audit/ISSUE_VERDICTS.md`](audit/ISSUE_VERDICTS.md),
[`DECISIONS.md`](DECISIONS.md) §13 and the open issues, in dependency
order. Task numbers are `<phase>.<batch>.<step>` and replace the old ad-hoc
names (`B0` = batch 4.1). ETAs are **estimates** — *attended* is hands-on
effort, *wall* is elapsed compute/network time; run-cost figures derive from the
measured s/iteration above, the rest are judgement and say so by being
estimates.

### Batch 4.1 — the rebuild — ✅ **DONE 16 August** (this PR)

Executed as planned, in one batch. Measured outcomes against the gates:
harvest 10/10 layers, all larger; **99 → 4** core SA1s without a road node,
**0 agents** in the 4; network speeds agree with the registry; 15 feeds mapped
in one build, 0 unmapped stops each; `check_package` **1,452 ALL PASSED**;
manifest **391**; `check_hardcoding --strict` **0**, reach 69/69; #37
acceptance **zero on all three day types**; #34 floorspace damage measured
**nil** (nearest out-of-box building 281 m from any segment); smoke run
`smoke_postrebuild` rc=0, median iteration 10.1 s at 1% (was 9.8 s on the
smaller network) — full memory re-measure belongs to the first 10% arm
(4.2.1). The task table below stands as the plan of record.

| # | Task | Closes | ETA |
|---|---|---|---|
| 4.1.1 | Re-run the OSM harvest over the derived extent: `python cities/newcastle/extract/overpass.py` (10 layers × 8 tiles; expect 504s and mirror rotation; resumes from cached tiles). Gate: every layer **larger** than its `networks/osm_pre_issue32/` counterpart; `osm_tiles.verify()` passes on each | #32 (data half) | attended ~1 h · wall 3–6 h |
| 4.1.2 | Rebuild the layer chain, in order: `build_network_layers` → `attach_gradient` → `attach_speed_zones` → `build_corridor_road_attributes` → `build_matsim_network` → `build_landuse_parking` → `build_zone_attractions`. Gate: the 87 clipped core SA1s (verify against the stricter **99 SA1s / 35,365 agents with no road node**) are inside the road network; network link speeds now match `A1_road_edges.csv` (kills the 27.4%-of-links speed disagreement) | #32, speed-disagreement defect | attended 2–3 h · wall 0.5–1 day |
| 4.1.3 | Demand fixes, then regenerate B2 **once** (all three day types): **(a)** cap or wrap activity chains at the 24 h boundary, acceptance **zero** collisions on WEEKDAY/SAT/SUN (#37); **(b)** declare the bike-availability asymmetry in `DECISIONS.md` + registry, and decide (and sweep) a constraint or record why not (#29 mechanism); **(c)** destination placement against the HTS per-purpose distance constraint — placement only, the scoring half is repaired and must not be re-fixed (#30); **(d)** external-station through matrix seeded from cordon counts, touching no holdout row (#20); **(e)** heavy-vehicle background layer from the measured 6.52% share, swept never pinned (#24). Every new value: declared field + sweep + `DECISIONS.md` entry | #37, #29 (mechanism), #30, #20, #24 | attended 4–6 days · wall +hours per B2 regen |
| 4.1.4 | Rebuild scenario GTFS feeds from the declarations (needs `networks/osm/footways.osm` from 4.1.1) and regenerate the 30 run-input sets through the emitter | stale feeds | attended 1 h · wall 2–4 h |
| 4.1.5 | Gates, in order: `check_hardcoding --strict` (keep 0; keep reach 69/69 — new fields must bind), `build_manifest`, `check_manifest`, `render_docs`/`render_schema`, `check_package` (must now pass its OSM checks; manifest back to ~386) | package gate | attended 2–3 h |
| 4.1.6 | #34's floorspace question, now answerable: measure buildings outside the old CBD box fronting the seven streets against the new harvest, **before** changing the denominator; any derived replacement keeps a street-name disambiguator (the verdicts showed the box's undocumented job is name disambiguation) | #34 | attended 2–4 h |
| 4.1.7 | Stale-statement fixes: the false escort note in `params/C3_count_comparison.json`; `RUN.controler.last_iteration`'s "carry 100" description | verdict defects 2–3 | attended 1 h |
| 4.1.8 | Housekeeping riding along: restore `check_package.py` coverage of the live view (`run_view.py` / `summarise_run.py`); rebuild any replay page before use (all pre-14 Aug pages are wrong, §9.36); strike the FALSE halves from issue bodies #20/#24/#30, refresh #14/#28, drop #28's `blocker` label | board hygiene | attended 1–2 h |
| 4.1.9 | Smoke-run the rebuilt package (10%, few iterations) to prove MATSim executes it, and **re-measure memory** — a bigger network may move the ~40% sample ceiling | executability | attended 1 h · wall 1–2 h |

### Batch 4.2 — measure, then calibrate (runs, not commits; strictly after 4.1)

| # | Task | Closes | ETA |
|---|---|---|---|
| 4.2.1 | ✅ **DONE 18 Aug.** Convergence pilot, one arm at a time: 10% × 1000 and 25% × 1000. Both failed the *declared* gate identically — diagnosed as a defect in the instrument, not the runs: the window started at the innovation cutoff and so included a **one-iteration** selection snap (+3.3 pp car at both fractions), making it unpassable at any horizon. Fixed and declared in one change (§9.43): `RUN.relaxation.settle_margin_iterations` = 10, `RUN.controler.last_iteration` = **1000** (`measured`, off `unobtained`), both arms now `relaxed: true` at +0.22 / +0.17 pp. Arm 3 (`conv1500_10pct`) **cancelled by instruction** for compute economy — the ~2 pp of un-relaxed pre-cutoff search creep is carried as **declared uncertainty**. Evaluation: [`docs/archived/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md) | #5 | ✅ 42 h of compute spent |
| 4.2.2 | ✅ **DONE 18 Aug** — measured on both pilot arms: ride out-runs car in every bin below 50 km (1.13× → 1.01×), the aggregate parity is a Simpson's reversal; bike 4.0% vs 3.2 observed needs no tuning; sub-1 km mass 2.5% vs >~10% reopens #30. [`docs/archived/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md) | #28 (sized), #29 (closed) | — |
| 4.2.3 | ✅ **DONE — built 18 Aug (§9.44, PR #40), re-measured on the repaired demand 20 Aug (§9.48).** Tier 1 `BeforeMobsim` pairing: a paired passenger takes the household driver's realised time; blast radius measured against a control (7 legs rewritten vs 0, mode share bit-identical). **Step 3, the re-measure arm, is complete**: `bind1000_25pct` (25% × 1000 WEEKDAY, rc=0, relaxed) measures OD-coincidence 0.104% → **15.31%** and declared-regime pairing 0.00004 → **0.0130**; the #28 residual is ~11.6 s at 25%; occupancy 0.4855 vs observed 0.3503 (outside range, flattering direction — 4.2.4's problem). The realisation gap (15.31% vs 1.30%) is named in §9.48, not chased | #28 (sized), #31 (measured), #9 | ✅ |
| **4.2.5** | ✅ **DONE 18 Aug (§9.46).** The escort tour binds to the person being escorted: households generate whole, an HX tour takes an already-drawn member trip's destination and departure **exactly** (all 120,980 placed weekday bindings verified coincident), bound tours are immovable in the escorter's timeline, unbound tours fall back to the distribution. **68.6% of weekday HX tours bound**; rate untouched (re-target, never add); binding scope and min-gap declared and swept; escort trips can no longer be made BY `ride`. Whether realised pairability moves is the next run's measurement | #31 (supply half), §9.44, §9.46 | ✅ |
| **4.2.6** | ✅ **DONE 18 Aug (§9.47).** Employment now per (SA1, sex, ABS age band) from G46 — 65–74 realises 15.3%, 75–84 1.5% against the flat 52/48 before; **plus two defects the brief did not know**: the 75+ population was missing (grouped G04 columns never read — 85+ had 186 persons against a census 15,151, now 16,188) and student status is now observed attendance (G01) instead of 100% of under-18s. Full evidence: [`docs/archived/design/age-structure.md`](design/age-structure.md) | population defect, §9.47 | ✅ |
| **0d(3)** | ✅ **DONE 20 Aug (§9.49).** Freight is a physical `truck` mode: through-gate volumes split by each station's own observed heavy share, an internal tier over the observed freight-industry attractor at the assumed swept ratio (0.0697, sweep 0.0–0.14), departures and weekend factors MEASURED from the classified hourly counts. Smoke-verified (913 trips, 140,380 traversals at 1%); car fleet unchanged, proven against the jar's bytecode. **Comparability break: a new demand family starts here** | #24 | ✅ |
| 4.2.4 | 🟡 **DECIDED, not delivered (§9.50, PR #47).** The §8.5 branch is constrain-and-report, logged before any result: ASCs stay priors, #9 resolved by decision, the §9.48 occupancy excess reported not absorbed; the loop's rebuild-stage defect fixed (unclassified consumers were defaulting to movable); `--constrained-base` machinery built and tested. **DELIVERED 24 Aug (§9.64)**: the completed base arm `phys1000a_25pct` produced C5 via `--constrained-base` (objective 10.65, feasible=False, five violations stated) and the calibration report; #14 and #9 closed | #14, #9 | ✅ decision + delivery |
| 4.4 | **Point-to-point (taxi + rideshare) mode** — decision re-opened 18 Aug 2026 on new evidence (IPART now surveys Newcastle and Hunter as its own p2p region; the passenger service levy counts every trip). Build as a teleported priced mode: measured taxi fares, literature rideshare rates (swept), fleet assumed; validated against the inferred 10,000–35,000 trips/day band as a **constraint, never a target**. Evidence dossier and declaration plan: [`docs/archived/design/point-to-point-mode.md`](design/point-to-point-mode.md). **Strictly after 4.2.4** — a ~1% refinement does not precede the measured 10–20 pp defects. First step: extract the Newcastle and Hunter table from the IPART 2025 information paper (PDF fetch timed out on first pass) | p2p mode | attended 2–3 days |
| 4.3 | Deliverable 0b — **STARTED 21 Aug (§9.61)**: G15 education split observed per SA1; SAT:SUN split, external weekend scaling and departure shift measured from the dated RMS counts (three fields retired); the full ranked backlog is **issue #63** (the sweep found 136 assumed fields, not 78; `A.road.speed/lanes_default` were already measured; the `beeline_distance_factor` duplicate was already resolved by §9.54). Remaining top items: era3 route-110 shuttle speed, observed parking capacities, ABS TableBuilder JTW extract (attended), TfNSW EPV 2025 VoT check (attended), Overpass attic pre-LR lanes query, ~25 reclassifications | 0b, #63 | attended 1–2 days remaining |

### Batch 4.5 — the four §9.51 standing directives (research first, decision required, then build)

Set 20 August 2026, superseding the prior value order. **Each is
research-and-discussion BEFORE any build** — the directive asked for exhaustive
research, and each collides with a recorded cost or data limit that the
research must confront rather than rediscover.

| # | Task | Issue | State |
|---|---|---|---|
| **4.5.1** | **Physical ride** — every ride trip a passenger physically in a car, share tuned to the observed 20.60% | **#48 — FIRST** | 🟢 **BUILT end-to-end, probe-verified (§9.53 + §9.55 + §9.60)**: `JointRideEngine` boards paired passengers; unpaired ride re-modes to physical walk (emergent share); **the non-household-lift gap now has its mechanism (§9.60, directed by recorded decision)** — M0: a booked passenger physically WAITS at the meeting point (the old missed-gone/absent classes measured 0 at the probe); M1: unbound observed-rate escort tours re-targeted to driverless-household passengers (WEEKDAY 55,249/55,614 bound after the §9.63 overlap repair; sampling co-clusters bound household pairs). Open: the converged-run measurement (where emergent ride settles vs 20.60%), M2 (driver detours) gated on that measurement, the summariser's stuck-attribution defect (fixed by #54) |
| 4.5.2 | **Modes individualised** — pt split into bus/train/LR/ferry; motorbike + taxi/rideshare distinct | #49 | ✅ **ALL TIERS BUILT**: Tier R (21 Aug, the reporting split) · Tier P motorbike (§9.52) · **taxi live (§9.77)** · **Tier C score-distinct submodes (§9.78)** — SwissRailRaptor mode mapping carries the C1 per-submode constants into route choice, bytecode-verified; probe shows zero `pt` legs. Open: converged measurements only |
| 4.5.3 | **Sub-1 km walk mass** | #30 (re-opened) | 🟡 **decomposition MEASURED** (on #30): generation is the loss site — 4.45% of legs under 1 km / 7.85% under 1.5 km against walk-only alone observed at 13.40%; p5 trip length 1.08 km; scoring/placement/mode choice exonerated. Open: the generation mechanism choice + a citable observed distance-band source |
| 4.5.4 | **Demographic-conditional mode fidelity** | #50 | 🟡 **inventory MEASURED** (dossier §3): held = mode × sex (G62), G46/G54/G60 demographics; **mode × age is NOT held — an acquisition item**. Open: the modelled table from the next valid run + the acquisition |
| 4.5.0 | **RELAUNCHED 21 Aug (third session, §9.62)** as two concurrent arms under the §9.59 pattern: arm A `phys1000a_25pct` (the base arm) + arm B `phys1000b_25pct` (the seed replication, seed 20260811). Watched every ~50 iterations; close-out DONE 24 Aug (§9.64): C5 + calibration report from arm A, seed floor from arm B, measurements recorded on #48/#31/#30/#28, #14/#9 closed. The §9.57 attempt stays quarantined | #14 | ✅ done 24 Aug |

### Batch 4.6 — the 24 Aug goal directive: every mode's ridership toward real life, ride first (the consolidated work plan)

Set by the session's `/goal` (24 Aug): *"all ridership numbers as close to
real-life as possible; exhaustively harvest all forms of traffic at
observed or academically studied values; address all issues in a proper
work plan; fix everything fixable before the next run, beginning with
ride."* Ordered by expected pp-of-error addressed per unit cost.

| # | Task | Issue | State |
|---|---|---|---|
| 4.6.1 | **Ride decomposition** — measure where ride plans die on the completed arms | #48 | ✅ **DONE 24 Aug (§9.68)** — `src/analyse/decompose_ride_choice.py`; absent 99.2%, scored-out 0.14%: the ASC is not the lever |
| 4.6.2 | **Ride repair: round-trip bindings + coherent seeds + direct bound tours** | #48, #31 | ✅ **BUILT 24 Aug (§9.68)** — declared (`escort_binding_directions`, `escort_binding_direct_tour`, `serve_tour_seed`, `bound_passenger_seed`), wired through both binder passes, the plans builder, `RidePairingEngine` and the sampler; demand regenerating |
| 4.6.3 | **Walk short-trip mass: observed distance-band mixture** | #30 | ✅ **BUILT 24 Aug (§9.69)** — HTS Sydney 2012/13 Table 4.4.7 declared as literature; two-component gravity mixture, means preserved exactly; demand regenerating |
| 4.6.4 | **Regenerate B2 + plans + 30 run-input sets on the repaired mechanisms; 1% probe (2 it); manifest + package checks** | — | ✅ **DONE 24 Aug** — band shares exact on every purpose; WEEKDAY coverage 26,638 household + 24,515 non-household round-trip tours; probe `20260824T210040_2it_1pct` rc=0, accounting closes, **return legs pair 347/347 at it-2** (old family: 2 of 2,818), pair rate 0.9988, pairing occupancy 0.12 vs the old converged 0.0013; `check_package` ALL PASSED (2 standing warnings); manifest 436 files |
| 4.6.5 | **#50 modelled table** — mode × age/sex/employment/licence from arm A | #50 | ✅ **DONE 24 Aug** — `src/analyse/mode_by_demographics.py`; children 46–50% bike / 0% ride confirms displaced ride demand; the observed mode × age acquisition stays open |
| 4.6.6 | **Freight rail researched; coal chain scoped OUT on observed infrastructure** | — | ✅ **DECIDED 24 Aug (§9.70)** — dedicated grade-separated track; adding it would fabricate an interaction |
| 4.6.7 | **Level-crossing closures at St James Rd Adamstown + Clyde St Islington** — time-varying capacity on the two crossing links, closures/day × duration assumed and swept (logs unpublished, "up to ten minutes" official); crossings located from OSM `railway=level_crossing`, no typed coordinate | new issue at handoff | ⬜ designed (§9.70); build after the ride/walk arm validates |
| 4.6.8 | **Taxi + rideshare teleported priced mode (4.4)** — the 2025 evidence is now in hand: IPART 2025 survey (Lower Hunter & Greater Newcastle stratum: taxi 41% / rideshare 46% used in 6 months, last-trip split 34/66), Fares Order 2025 **Urban Area** rates ($5.00 flagfall, $2.52/km first 12 km — Newcastle is urban, not country, correcting the 4.4 premise), HTS Hunter "Other" ceiling 35,000 trips/weekday, derived band 15,000–25,000/day central | #49 | ⬜ evidence complete; **resequenced 25 Aug into batch 4.7 (task 4.7.8, §9.75)** — supersedes the after-the-base-arm sequencing |
| 4.6.9 | **Next base arm — NOW AN F6 ARM on the activated inputs (§9.77)** — 25% × 1000 × WEEKDAY; re-measures every mode against its observed value, jointly with the activated batch (the repairs-only measurement was forfeited with F5, recorded §9.77). Launch with `run.py --detach` (VERIFIED, #70 closed); **arm B only if arm A's `_progress.json` shows `pace.solo_in_band`** | #48 #30 #73 #68 #49 #50 | ⬜ **needs fresh stated-cost approval (~65–67 h/arm)** |
| 4.6.10 | **0b: pre-LR cross-section measured from OSM history** — Overpass attic 2017/2016: every lane-tagged Hunter/Scott segment ONE lane per direction; `pre_lr_lanes_per_dir` 2 → 1 (B3's counterfactual onto evidence); raw responses landed with provenance | #63 | ✅ **DONE 24 Aug (§9.71)** |
| 4.6.11 | **0b: VoT set checked against TfNSW EPV Jan 2025** — HW/WB/trip-weighted/distance-rate supported within ±30%; HE 9.3 and concession 0.75 divergent (flagged, values unchanged); EPV bus–LR transfer 3.8 equiv-min noted for the PT-composition lane | #63 | ✅ **DONE 24 Aug (§9.71)** |

### Batch 4.7 — the project's 25 Aug all-modes-first batch (next session; §9.75)

Implemented next session; the model-changing items activate as **ONE family
boundary** whose DECISIONS entry is authored at activation. Ordering against
the 4.6.9 arm is an open decision (board header).

| # | Task | Issue | Notes |
|---|---|---|---|
| 4.7.1 | Warm restart from written plans | #75 | ✅ **BUILT 25 Aug (§9.76)** — `--warm-start`, provenance-linked, resume-safe; the non-bit-identity caveat recorded; **the valid-arm-vs-diagnostic ruling is an OPEN decision** |
| 4.7.2 | Machine-readable `_progress.json` per-iteration digest | #76 | ✅ **LIVE 25 Aug (§9.76)** — every mode individually; drift vs the declared tolerance; pace vs the declared band; solo-check mechanises the §9.72 replication rule; verified inside a real (probe) run |
| 4.7.3 | Cross-run index with family and validity labels | #77 | ✅ **BUILT 25 Aug (§9.76)** — `results/INDEX.md`/`.csv` over the declared [`run_families.json`](run_families.json); 38 directories labelled |
| 4.7.4 | SUMO descope execution | #72 | ✅ **DONE 25 Aug (§9.76, §14)** — registry/toolchain/checks/manifest; Maven + the signals run stack pinned in the same toolchain change |
| 4.7.5 | Level crossings at Adamstown + Islington via `NetworkChangeEvents` | #68 | ✅ **ACTIVATED 25 Aug (§9.77)** — `A.crossings.representation=change_events`, time-variant network + change events in every config, `bin_size` 300; the schema-element-order defect probe-caught and fixed |
| 4.7.6 | Charging dwell natively | #74 | ✅ **ACTIVATED 25 Aug (§9.77)** — carried into the run inputs by the signals-transformed schedules |
| 4.7.7 | Corridor signals + tram priority natively | #73 | ✅ **ACTIVATED 25 Aug (§9.77)** — signals module + generated plans + saturation capacities in every set; **S3 bus-keyed priority BUILT (§9.77/§9.78)**: `A.signals.tsp.priority_group=corridor`, third toy-probe case PASS, all 14 S3 controllers instantiate in-scenario (mid-block null-payee NPE probe-caught and guarded). Remaining on #73: arm-scale measurement; movement-level lanes stay data-gated (16%) |
| 4.7.8 | Taxi/rideshare priced mode | #49 | ✅ **ACTIVATED 25 Aug (§9.77)** — taxi in both vocabularies + city.json; probe: chosen, routed and priced on the congested network (1.4–2.1% at 1%); band comparison live in the metrics |
| 4.7.9 | Rung-1 registry sharpening | #63 | ✅ **DONE 25 Aug (§9.76)** — TIA/TTD sweep-basis citations; `E.s2b.lr_segment_count` measured 5 from the mapped feed |
| 4.7.10 | Frontage volume analyser from physical walk link events | — | ✅ **BUILT 25 Aug (§9.76)** — `frontage_volumes.py`, verified on the 1% probe (556 frontage walk links); informs the pending 6.1 REWORK |

### Batch 4.8 — the 25 Aug sixth-session runless close-out (§9.77/§9.78) — ✅ ALL DONE

| # | Task | Issue | State |
|---|---|---|---|
| 4.8.1 | Execute the §9.76 activation checklist as ONE boundary; declare family F6 | #73 #68 #74 #49 | ✅ **DONE (§9.77)** — two probe-caught defects fixed en route |
| 4.8.2 | S3 bus-keyed priority (`A.signals.tsp.priority_group`) | #73 | ✅ **DONE (§9.77/§9.78)** — third toy-probe case + in-scenario instantiation verified |
| 4.8.3 | Tier C score-distinct PT submodes (raptor mode mapping) | #49 | ✅ **DONE (§9.78)** — bytecode-verified; interchange-crash pre-empted; folds into F6 |
| 4.8.4 | Seven 0b source upgrades incl. CWANZ bike availability 0.493 + plans regen | #63 | ✅ **DONE (§9.78)** — attended TableBuilder extract is the issue's only remainder |
| 4.8.5 | Corridor-composition diagnostic on arm A | — | ✅ **DONE (§9.78)** — coverage carries the bus-over-tram split; re-measures on F6 |
| 4.8.6 | Demographic mode-share measurement + inventory | #50 | ✅ **DONE (§9.78)** — sex-invariance finding; no mode × age cell held |
| 4.8.7 | Systematic planning-portal TIA sweep for SCATS | — | ✅ **DONE, EMPTY (§9.78)** — PPSHCC-137 stays the only evidence; watch items logged |
| 4.8.8 | Stall-attribution capture on the progress observer | #66 | ✅ **DONE (§9.78)** — Defender/TaskScheduler window captured at the stall transition |
| 4.8.9 | City-free input contract: all six #62 strata | #62 | ✅ **DONE (§9.78)** — `intervention_boardings` rename (accepted break), lineage/currency/zone tokens in city.json, `check_package` split, reader-shapes contract + adapter; census readers recorded as the follow-up |

### Batch 4.9 — the 25 Aug seventh-session document-currency gate (§9.79) — ✅ ALL DONE

| # | Task | Issue | State |
|---|---|---|---|
| 4.9.1 | Gap scan: every live figure in `README.md`, `STATUS.md` and `.claude/CLAUDE.md` measured against its artefact | — | ✅ **DONE** — 9 stale figures and 2 false statements found; `README.md` was three phases out of date |
| 4.9.2 | `tests/check_doc_currency.py` + city-owned `tests/doc_currency.json` | — | ✅ **DONE** — 22 claims, 2 claim kinds (`number`, `absent`), truths derived from the committed manifest and registry; verified to exit 1 on an injected regression and 0 clean |
| 4.9.3 | Wire `--strict` into CI as its own job | — | ✅ **DONE** — `.github/workflows/test.yml`, no dependencies beyond the standard library |
| 4.9.4 | Correct every drifted figure and both false statements | — | ✅ **DONE** — `README.md`, this board, `.claude/CLAUDE.md` (its ledger line said 95; the ledger is 0) |
| 4.9.5 | `docs/HANDOVER_CONTRACT.md`: the six questions, trust order, environment gate and expiry rule, defined once | — | ✅ **DONE** — both skills now reference it instead of duplicating it |
| 4.9.6 | Rewrite `/onboard` and `/handoff` to Anthropic's skill-authoring guidance | — | ✅ **DONE** — trigger-rich third-person descriptions, copyable phase checklists, mechanical drift scan before hand inspection, `check_doc_currency` in both gate sets, and the facts-that-expire rule that made the sixth brief wrong on arrival |
| 4.9.7 | The superseded counts attribution: correct the generator, file the residual | #82 | ✅ **DONE** — `src/calibrate/report.py` states the supersession; the unexplained −91.8% is #82, run-gated |

### Batch 4.10 — the 25 Aug eighth-session front door and drift sweep (§9.80) — ✅ ALL DONE

| # | Task | Issue | State |
|---|---|---|---|
| 4.10.1 | `src/analyse/build_fit_figures.py`: modelled-vs-observed panels (mode share, trip-length constraint, 30 counts) from the calibrated base's own run, light + dark, no dependency, no wall-clock | — | ✅ **DONE** — selected via `C5_calibration.json`'s `best_tag`, so the figures and the calibration report always describe the same arm; `--check` gates them in `check_package.py` |
| 4.10.2 | Rewrite `README.md` as a front door: what the project is, **what it models** (every mode + the corridor mechanisms, incl. the explicit signal control that replaced the refused SCATS phasing), how to set it up, and the base model's fit as figures | — | ✅ **DONE** — ten new doc-currency claims pin its results section |
| 4.10.3 | **CORRECTION**: the light rail's 1,260 boardings had been reported as a −63% error against V001/V002, which `fit.py` marks UNSCORABLE (pre-pandemic vintage vs a 2026 base, §12.1) | **#84** | ✅ **CORRECTED AND FILED** — fixed in `CORRIDOR_PT_COMPOSITION.md`, the DECISIONS index, the README and both skills; #84 carries the remaining sweep and the open question of what patronage IS legitimately checked against |
| 4.10.4 | `src/run/run_failure.py` + a `cause` requirement in the `_meta.json` contract; backfill every dead run from its own `matsim.log`; surface causes in `results/INDEX.md` | — | ✅ **DONE** — all 14 backfilled; the three 25 Aug probe failures independently reproduce the §9.77 narrative |
| 4.10.5 | `check_doc_currency.py` gains `decimals` and a `text` claim kind; the stale-statement ban widened to every phrasing of "the package is not built yet" | — | ✅ **DONE** — the §9.79 ban named one wording and the same false claim survived under another in this board's resume instructions |
| 4.10.6 | Retire `P4_CHECKPOINT.md` as a live document; freeze it as the 12 August record it is | — | ✅ **DONE** — it restated this board's job and had drifted on nine counts; nothing in it is unique to it |
| 4.10.7 | Sweep the remaining living documents: `docs/README.md` (five output schemas against seven, two `tests/` checks against four), `.claude/CLAUDE.md` (four premise corrections against five), the `DECISIONS.md` header (*"last entry §9.75"* with §9.79 in the file) | — | ✅ **DONE** — where a number has no artefact to be pinned to, it is replaced by a pointer to the thing that always knows |

### Batch 4.11 — the 26 Aug ninth-session iteration-200 gate loop (§9.81/§9.82) — IN PROGRESS

| # | Task | Issue | State |
|---|---|---|---|
| 4.11.1 | Run the first F6 arm and gate it at iteration 200 | #48 #30 #73 #68 #49 #50 #82 | **DONE** — `aborted_20260825T135734`, 200/1000 in 15.1 h, stopped on the gate; car 54.33 / ride 0.41 / taxi 9.47 |
| 4.11.2 | Diagnose the ride collapse | #48 | **DONE (§9.81)** — the ratchet: a missed pairing MUTATED THE PLAN, so 95.7% of iteration-0 misses vanished by iteration 1; a 36-iteration half-life toward the pre-repair 0.0013 |
| 4.11.3 | Refuse or accept the pairing-window hypothesis **on measurement** | — | **REFUSED** — median gap to an endpoint-matching driver 253.7 min; widening 15 to 60 min recovers 13 legs of 1,529. `B.ride.pairing_window_min` NOT moved |
| 4.11.4 | Repair the ratchet without touching §9.55 or any parameter | #48 | **DONE** — the forced walk is an EXECUTION; mode and route restored at AfterMobsim, after the events scoring reads. Two failed attempts first (a Leg held across the mobsim that PlanRouter had replaced; a trip left with mixed routingModes), both caught in minutes |
| 4.11.5 | Miss funnel and gap distribution in `ride_pairing.csv`, ordered geometry-first | — | **DONE** — reporting only; about 90% of misses are passengers no driver was ever going to serve |
| 4.11.6 | Run F7 and gate it | — | **DONE** — `aborted_20260826T060938`; the fix WORKED (ride legs held 87,019 / 85,873 / 86,118) and was NOT SUFFICIENT (realised ride 0.95) |
| 4.11.7 | Diagnose the residue | #50 #30 | **DONE (§9.82)** — the empty escort tours: 84.53% of escort trips car, 11.45% of escort-bound members riding |
| 4.11.8 | `EscortCoherenceListener`: propose the coherent plan back, never impose | #48 #50 | **BUILT** — validated at 25% x 2 (`20260826T220340`, rc 0); `B.ride.escort_coherence_rate` declared and swept, its zero recovering F7 exactly |
| 4.11.9 | **Run F8 and gate it at iteration 200** | — | **NOT REACHED** — the first F8 build died at iteration 2 (`aborted_20260826T222352`, mixed chain/non-chain subtour, task 4.11.11); the relaunch `aborted_20260826T233658` was STOPPED ON INSTRUCTION at iteration 163 of 1000, before the gate. Both closed out with measured causes |
| 4.11.10 | `bike` and `taxi` over-choice | #49 #50 | **DIAGNOSED, NOT BUILT (§9.83)** — three measured causes, none acted on: taxi is gated by NOTHING; `age` reaches nothing (0–4 year olds take 31.1% of trips by bike and 19.5% by taxi, but this bounds at **19%** of the excess); gradient reaches mode choice through nothing where **30.5% of 50,182 edges exceed 4% grade** and modelled bike trips run 9.21 km / 41.7 min against a measured 5.2 / 19.2. `bike+taxi` is ONE scored target, `Other` = 21.31 vs 3.20 |
| 4.11.11 | The first `EscortCoherenceListener` build re-moded one trip of a subtour | — | **DONE** — died at iteration 2 (`aborted_20260826T222352`); the listener now converts the WHOLE subtour and offers ride only to a member who cannot drive themselves. Validated by `probe_replanning_25pct` (`20260826T224343`, rc 0) |

### Batch 4.12 — the 27 Aug tenth-session measurement-basis correction (§9.83) — MEASUREMENT ONLY, NOTHING BUILT

| # | Task | Issue | State |
|---|---|---|---|
| 4.12.1 | Read the gate on the quantity `fit.py` actually scores | — | **DONE (§9.83)** — `<n>.trips.csv.gz` is events-derived, linked, main-mode, and was present in every arm at iterations 0, 1, 50, 100, 150. New `src/analyse/measure_iteration_modes.py` scores it through `fit.py`'s own `score_mode_share` |
| 4.12.2 | Compare F6 / F7 / F8 on that basis at a matched iteration | — | **DONE** — iteration 150: mean abs error 10.991 → 10.460 → 10.348; ride 0.61 → 1.39 → 1.61; every category improved, none regressed. **Both repairs work; neither is sufficient** |
| 4.12.3 | Re-check the recorded "car bias" | — | **INVERTED** — car+motorbike is 52.12 against an observed 59.00, i.e. **11.7% UNDER**. The recorded bias was whole-scenario legs across five LGAs including freight (§12.1) |
| 4.12.4 | Re-check §9.82's probe evidence | — | **CORRECTED (§9.83)** — the pair-rate "reversal" at iterations 7–8 is the innovation cutoff (0.8 × 8 = 6.4), not convergence. §9.82 stays as written; the correction lives in §9.83 |
| 4.12.5 | Locate the residual cause | #48 #50 | **DONE (§9.83)** — a DEMAND CEILING, not a choice defect: `party_size = 1` on all 2,343,321 B2 trips; escort-bound travel 5.4% vs an observed 20.6%; occupancy 1.0013 vs the **measured** 1.3503. This is the measurement §9.55 named as decisive |
| 4.12.6 | **Widen the non-household lift scope and measure it** | #48 | **OPEN — the next lever.** `B.activity.escort_binding_nonhh_scope` is declared and swept (§9.60), currently `same_zone`; the 5.4% ceiling is measured WITH that mechanism live |
| 4.12.7 | Taxi availability gate | #49 | **OPEN** — taxi is gated by nothing; it runs far above its declared `B.taxi.daily_trips_band` of 15,000–25,000/day |
| 4.12.8 | Gradient into bike/walk link travel time | #21 (closed) | **OPEN** — `bike` and `walk` are qsim main modes on the network and `LinkSpeedCalculator` is in the pinned run stack, so no toolchain change is implied. Reopen #21 or file anew |

### Batch 4.13 — the 27 Aug eleventh-session root-cause builds (§9.84) — family F9

| # | Task | Issue | State |
|---|---|---|---|
| 4.13.1 | Settle the §9.60 scope decision | #86 | **DONE BY MEASUREMENT, no run** — the lift pass already binds 98.0% of its unbound-driver supply at `same_zone` (49,030/50,014 WEEKDAY); the constraint is driver supply, not scope. The scope stays `same_zone` |
| 4.13.2 | The joint-tour binder: generate the missing adult joint travel | #86 #48 | **BUILT AND MEASURED (§9.84)** — `bind_joint_tours`, third binder pass; volume anchored on the derived occupancy ratio (0.3503) × observed driver share, escort/lift coverage counted first; parties up to the declared capacity; negotiated timing (the M1 re-timing precedent) when no driver tour fits as drawn. WEEKDAY attainment 74,663 bindings (16,473 shifted) = coordinated supply 251,632 trips, **56% of the occupancy target — the household-only ceiling**; SAT 65%, SUN 64%. Companions seed ride, drivers car; eligibility only, realisation emergent |
| 4.13.3 | Joint coherence at runtime | #48 | **BUILT** — `EscortCoherenceListener` joint path at `B.ride.joint_coherence_rate` (assumed, swept, zero recovers escort-only) |
| 4.13.4 | Gradient into bike/walk link travel time, both router and mobsim | #21 | **BUILT (§9.84)** — `grade_pct` stamped from A1/A6 node elevations (81.9% of walk/bike links); Tobler walk, Parkin & Rotheram bike, all constants declared and swept; `GradientSignalsNetworkFactory` keeps signals and gradient alive together |
| 4.13.5 | Taxi and bike age gates | #49 #50 | **BUILT (§9.84)** — `B.taxi.min_unaccompanied_age` 18 [0,18], `B.population.bike_min_age` 12 [0,16], zero disables, via the new `modeAvailability` module |
| 4.13.6 | Regenerate demand, plans and the 30 run-input sets as family F9 | — | **B2 DONE** (three day types; legs per day identical to the pre-joint build — the binder adds no trip); plans and run inputs regenerating |
| 4.13.7 | Validate on `probe_replanning_25pct`, measuring signals alive + gradient live + joint riding + gates biting | — | **SUPERSEDED** — the two F9 arms ran to depth instead, which is stronger evidence than an 8-iteration probe |
| 4.13.8 | Run the F9 arm, gate every 100 iterations on the fit basis, per-mode | #48 #49 #50 #30 #82 | **DONE — the gate FIRED twice.** Gate-1 `20260827T181709` stopped at iteration 100 (ride decaying); gate-2 `20260828T111708` stopped at iteration 100 with all five scored categories past 20% and §9.84's driver-side pass measured INERT (§9.85) |

### Batch 4.14 — the 28 Aug twelfth-session translation-loss repair (§9.85) — family F10

| # | Task | Issues | State |
|---|---|---|---|
| 4.14.1 | Read the F9 gate-2 arm at iteration 100 on the scoring basis | #48 | **DONE (§9.85)** — all five scored categories past the 20% bar: Other +471.2%, pt +123.4%, driver −19.4%, ride −76.3%, walk +55.2%; mean abs error 10.864 pp. Arm stopped |
| 4.14.2 | Attribute §9.84's driver-side pass | #48 | **DONE — INERT.** 10.920 → 10.864 mean abs error and ride 4.91 → 4.87 against the previous arm at equal depth. That inertness located the cause |
| 4.14.3 | Locate why every pairing repair has been inert | #48 #86 | **DONE (§9.85)** — a TRANSLATION LOSS. All three B2 binding tables name the driver; `build_matsim_plans.py` read the identity for seeding and discarded it, so the pair is re-found by a clock `TimeAllocationMutator` moves at an **undeclared** ±1800 s. Measured: 73.8% / 67.4% / 80.5% of joint / escort / lift bound ride legs have their declared driver on the same OD **by car**, but only 60.6% / 42.6% / 64.5% fall inside the 15-min window |
| 4.14.4 | Confirm the demand is not the constraint | #86 | **DONE** — `modestats` ride is **0.1903 at iteration 0** against an observed 0.206. §9.84's binder closed the ceiling; the realisation is what fails |
| 4.14.5 | Carry the binding identity into the population | #48 | **BUILT (§9.85)** — `boundDriver` from all three tables, 158,898 persons. Joint alone would have covered 46% of affected legs and left escort, the worst-hit, on the clock |
| 4.14.6 | Declare the mutation range; derive the bound-pair tolerance from it | #48 | **BUILT** — `RUN.replanning.time_mutation_range_s` declared and swept (group name verified against the pinned jar); `B.ride.bound_pairing_window_min` DERIVED by identity, relaxing IDENTIFICATION only. Registry 370 → **372** |
| 4.14.7 | Keep the physical wait consistent with the booked tolerance | #48 | **BUILT** — `JointRideEngine` bounded the wait by the narrow window, so the pair rate would have risen while nobody boarded (trap 6/7). `Booking` now carries its own tolerance |
| 4.14.8 | Validate F10 on `probe_replanning_25pct` | — | **PARTIAL — stopped on instruction at iteration 2 of 8.** What it established: config parses, run reaches iterations, `paired_by_identity` 7 (it.0, no drift) → 1,745 (it.1); vs F9 at equal depth pair_rate 0.4936 → **0.5095**, occupancy 0.2770 → **0.2860**, physical wait-boardings 453 → **637**, timeouts 3,964 → **3,784**. **The 8-iteration validation did not complete** |
| 4.14.9 | Run the F10 arm and gate every 100 iterations, per mode | #48 #49 #50 #30 #82 | **OPEN — the active lane.** Needs a fresh stated-cost approval (~7.6 h to iteration 100 at the measured 273.82 s/it) |
| 4.14.10 | Make taxi physical in the mobsim | **#88** (new) | **OPEN** — `taxi` is in `RUN.routing.network_modes` but not `RUN.qsim.main_mode`, so 39,892 of 39,923 taxi legs per iteration are teleported and consume no road capacity. Not a scoring hole — the fare IS charged — but it contradicts the §9.51 all-physical directive |

### Batch 4.15 — the 30 Aug sixteenth-session root-cause build (§9.120) — family F15

| # | Task | Issue | State |
|---|---|---|---|
| 4.15.1 | A twelve-mode reading at every iteration the run writes, not only the trips-table ones | — | **DONE (§9.120)** — `src/analyse/iteration_trips.py` derives the linked trips from `<n>.experienced_plans.xml.gz`; validated EXACTLY against the trips table at F14 it.0 (532,161 trips) and F13 it.100 (221,144); both readers fall back to it and name the source |
| 4.15.2 | Close out the dead F14 arm with what the record can measure | #66 | **DONE** — `0xC000013A STATUS_CONTROL_C_EXIT` from Task Scheduler, no exception, trigger not established; the scheduler's operational log is DISABLED on this machine and enabling it needs elevation (**ask the user**) |
| 4.15.3 | Measure planned vs experienced mode per trip on the arm's own iteration 30 | #48 #86 #30 | **DONE (§9.120)** — ride planned 22.46% / realised 9.14%; 7.90 pp driven, 3.81 pp walked under the fallback; 6.74% of trips never experienced (18,412 stuck at 30:00) |
| 4.15.4 | Classify every planned ride leg against its declared driver | #48 #91 | **DONE** — no declared driver 26.6% → 36.0% (it.0 → it.30); same OD within 15 min 57.1% → 27.5%; gap > 45 min 1.8% → 7.5% |
| 4.15.5 | Test whether bike persists on score or on search | #49 #30 | **DONE** — 65.1% of 4,459 cycling agents hold no bike-free plan in memory; a search failure, not a scoring one |
| 4.15.6 | `ride` only where a driver is declared; declared drivers held on car | #48 #91 | **BUILT** — `boundRideTrips`/`boundDriveTrips` from the three binding tables; refused in `GatedSubtourModeChoice` |
| 4.15.7 | Declared passenger re-timed to the driver's departure; no clock test on a declared pair | #48 | **BUILT** — `RidePairingEngine`; smoke: 68 re-timed at iteration 1, mean shift 906 s |
| 4.15.8 | The seed as the full choice set | #49 #30 #50 | **BUILT** — `B.mode.seed_method` = `full_choice_set` (supersedes §9.92), `RUN.replanning.max_agent_plan_memory` 5 → 8; unscored-first selection read from the pinned jar's bytecode |
| 4.15.9 | Motorbike carve solved on eligible persons' own trip counts | #93 | **BUILT** — q 0.00317 over 426,129 eligible; the realised share re-measures on the F15 arm |
| 4.15.10 | Rebuild plans (3 day types) + 30 run-input sets + manifest; smoke probe; local suite | — | **DONE** — `20260830T124345_2it_1pct` rc 0; `check_package.py` ALL PASSED (2 standing warnings); manifest 494 rows re-hashed |
| 4.15.11 | Run the first F15 arm and gate it per mode | #48 #86 #49 #30 #93 #82 | **STOPPED ON THE GATE at iteration 13 (§9.121)** — `aborted_20260830T124711_300it_10pct`; it established that ride pairs at 88.8% on identity (the §9.120 repairs work) and that every car plan in memory had been scored under the iteration-0 gridlock the car-first seed order created (bike plan +68 utils over car for the average car-available resident) |
| 4.15.14 | The first-executed seed plan drawn uniformly over each person's plans | #49 #30 #50 | **BUILT (§9.121)** — a hash of person id and master seed; no value, no re-scoring; plans, run inputs, manifest rebuilt as family F16 |
| 4.15.15 | Run the first F16 arm and gate it per mode | #48 #86 #49 #30 #93 #82 | **STOPPED ON THE GATE at iteration 17 (§9.121)** — `aborted_20260830T132843_300it_10pct`; it established that the seed-order artefact is gone (car the best-scored plan for 61.1% of car-available residents, F15 47.8%) and that **38.3% of residents' pt-plan trips were walk-only** (the raptor's beeline direct walk, 45.5% of them over 3 km on the network) |
| 4.15.16 | Why the router does not return the ferry | #94 | **MEASURED (§9.121)** — Stockton-side residents' 110 CBD-bound pt-plan trips: walk 88, bus 20, tram 1, ferry 1; the beeline direct walk crosses the harbour, the network's walk is the 20 km detour |
| 4.15.17 | The PT router's direct walk evaluated on the walk network | #94 #30 #49 | **BUILT (§9.121)** — `citysim.NetworkDirectWalkPtRouter` + `ptDirectWalk` config group; `RUN.transit_router.direct_walk_basis` = `network` (derived), `direct_walk_factor` 1.0 declared; classes installed, run inputs re-emitted, smoke-probed; family F17 |
| 4.15.18 | Run the first F17 arm and gate it per mode | #48 #86 #49 #30 #93 #94 #82 | **STOPPED at iteration 60 for F18 (§9.126)** — `aborted_20260830T141222_300it_10pct`: car 36.3 → 59.32 (+1.7%) and walk 42.3 → 14.88 (+11%) by iteration 50; ride at the demand's ceiling; ferry 30–36 trips against 3; the residues are the car-less quarter's, the carves', the corridor's and the fleet's |
| 4.15.25 | Run the first F18 arm | #48 #86 #91 #49 #30 #93 #94 #82 | **STOPPED at iteration 2 on a DEFECTIVE SAMPLE (§9.127)** — `aborted_20260830T161243_300it_10pct` kept 31,262 persons at 10% where F17 kept 62,134: the household sampler's union-find over `liftHousehold` made the sampling unit the connected component, and shared rides turn those into giant lumps |
| 4.15.26 | A shared ride binds only to a driver the sampler keeps whenever it keeps the passenger | #86 | **BUILT (§9.127)** — the binder applies the sampler's own unit hash (driver household hash ≤ passenger's); the plans name shared drivers' households in `sharedDriverHousehold` and the sampler excludes them from its lift clusters; a directed closure was measured to pull the sample to 17.65% and rejected |
| 4.15.27 | Run the first valid F18 arm and gate it per mode at 100 / 200 / 300 | #48 #86 #91 #49 #30 #93 #94 #82 | **STOPPED at iteration 1 (§9.128)** — `aborted_20260830T163010_300it_10pct`, 62,134 sampled persons; iteration 0 paired 4,858 of 6,966 ride legs and refused 2,053 on endpoints: the same-SA2 shared rides cannot share a link with their driver under `both_links`, so the arm could not realise the pass it existed to test |
| 4.15.28 | A declared pair whose links differ is served by the driver's detour | #86 #66 | **BUILT (§9.128)** — a walking meeting point was built first and measured on a 1% smoke at 8-11 km walked per passenger (rejected); the engine now routes the driver's car leg through each carried passenger's origin and destination links and books at the pass time; `B.ride.declared_pair_meeting` = `driver_detour` (412 fields); smoke `20260830T165440_2it_1pct`: 0 unroutable, mean detour 471-751 s per driver |
| 4.15.29 | **Run the first F19 arm and gate it per mode at 100 / 200 / 300** | #48 #86 #91 #49 #30 #93 #94 #82 | **RUNNING** — `20260830T170743_300it_10pct`, launched 17:07 detached (`citysim_run_20260830T170742`); first gate at iteration 100 (~22:15 at ~3 min/it); it.20 read car 56.76 / ride 10.86 / walk 18.05 / taxi 1.63 / bike 6.90 / motorbike 0.115 / bus 4.30 / heavy rail 1.28 / light rail 0.028 / ferry 0.039, ahead of F17 at the same iteration on every mode; **to be STOPPED when the F20 arm launches (§9.129)** |
| 4.15.30 | The 9.127 coupling rule biased every sub-sample | #86 #93 | **BUILT (§9.129)** — at-or-below named low-hash households as drivers (10% sample kept named drivers at 12.4%, everyone else at 7.95%, the motorbike carve at 5.5%); a shared pair must share a hash bucket, `B.ride.shared_lift_hash_bucket` 0.05 (413 fields); re-bound WEEKDAY 73,509 servable / 59,701 bound / 0 short |
| 4.15.31 | The carves solved on the pool that is drawn | #93 | **BUILT (§9.129)** — named drivers (42.1% of the pool's trips) excluded before the solve; rebuilt motorbike carve 5,937 trips on 1,687 persons = 0.2666% of resident trips against 0.2654% solved (was 0.153%); plans, run inputs and manifest rebuilt |
| 4.15.33 | Heavy rail and light rail held to their disclosed boardings | #84 #49 #30 | **BUILT (§9.130)** — light rail 2,954 and heavy rail 6,529 boardings per weekday (all travellers; `CAL.pt.weekday_factor` 1.0727, 414 fields); the report scores modelled boardings x 1/fraction; F19 it.20 reads light rail -51%, heavy rail +372% (suburban stations 3-13x over, Interchange right) |
| 4.15.34 | Why heavy rail boards five times the disclosed entries at suburban stations | #49 | **MEASURED (§9.131)** — long multi-leg pt trips of outer-LGA residents (Maitland-line stations 7,200 modelled entries a day vs 850); census journeys to work by home LGA are 86-91% car and 0.1-0.3% train, the model's work trips were 55-59% car and 2.4-5.4% rail, because 14.2-14.8% of employed persons held no licence |
| 4.15.35 | The licence rate is the published count over the published population, per LGA | #49 #93 | **BUILT (§9.131)** — `fetch_licences.py` (TfNSW licence snapshot + ABS ERP by age and LGA), `build_licence_rates.py`; `B.population.licence_rate_by_age_band` measured (18-24 0.78, 25-74 0.94-1.00); population, chains, plans, run inputs rebuilt The population was rebuilt at 19:31 (612,634 persons): employed persons with a car available rose from 78.9-83.0% to 90.8-91.7% in Cessnock, Lake Macquarie, Maitland and Port Stephens and to 80.8% in Newcastle (its 18-24 rate is 0.68 and 8.2% of its dwellings hold no vehicle); the unlicensed share of the employed fell from 14.2-14.8% to 4.8-5.9% (Newcastle 12.7%). The activity chains, plans and run inputs were NOT rebuilt: the chain was stopped at the user's direction at handoff, mid-way through the WEEKDAY chains, and its partial WEEKDAY trips and escort-binding files were deleted, so the package on disk holds a population newer than its chains until build_activity_chains.py, build_matsim_plans.py and build_matsim_run_inputs.py are rerun - the next session's first build. Family F21 opens at that arm's launch. |
| 4.15.36 | **Run the first F21 arm and gate it per mode at 100 / 200 / 300** | #48 #86 #91 #93 #49 #30 #94 #82 | **NEXT** — smoke, then launch detached; stop the F20 arm at that point |
| 4.15.32 | Run the first F20 arm and gate it per mode at 100 / 200 / 300 | #48 #86 #91 #93 #49 #30 #94 #82 | **STOPPED at iteration 11 at handoff (§9.131)** — `aborted_20260830T184955_300it_10pct`; iteration 0 verified the sample's composition (175 motorbike-locked, 23,040 named drivers); iteration 10 read car 48.01 / ride 9.22 / walk 25.60 / taxi 1.64 / bike 7.77 / **motorbike 0.378 (-0.1%)** / bus 5.49 / heavy rail 37,520 boardings a weekday (+475%) / light rail 1,650 (-44%) / ferry 0.035; superseded by the licence finding |
| 4.15.19 | Why motorbike reads a quarter of its target | #93 #49 | **MEASURED (§9.122)** — the carve is halved by the escort-day denial applied AFTER the draw (38.0% of eligible persons, 47% of eligible trips), delivering 0.128% of legs against 0.241%; the 10% arm then reads it off 17 sampled persons. The spatial explanation #93 offered is not in the population (0.1285% target LGA, 0.1266% elsewhere) |
| 4.15.20 | The carve solved on the persons who will not be denied; the carve at census resolution (`sa1_thinned`) | #93 | **BUILT (§9.122), NOT YET REBUILT** — queued for the next family with the ride ceiling and the resident truck carve, so the F17 arm stays a one-change comparison |
| 4.15.22 | Why bike diverges with every mode scored | #86 #49 #30 | **MEASURED (§9.123)** — 95.4% of residents preferring bike on score have no car; car-less residents (24.7% of trips) walk 48%, cycle 17%, take pt 15% for want of a lift. Bike, bus, heavy rail and walk's residue are ride's deficit; the next family boundary is lift supply (#86/#91), not a bike or pt parameter |
| 4.15.23 | Shared rides: the fourth binder pass, car-less residents' direct tours bound to non-household drivers on the same SA2-to-SA2 trip, thinned to the passenger-share identity | #86 #91 #48 | **BUILT AND MEASURED (§9.124), NOT YET REBUILT** — 59,648 tours bound on the committed WEEKDAY demand, 17 trips short of the identity (SA1 scope: 19,034); `B.ride.shared_lift_scope` = `same_sa2_od`; rebuilds with the motorbike carve as the next family after the F17 gate |
| 4.15.24 | Residents who drive a truck for a living (directive item 8) | — | **BUILT (§9.125), NOT YET REBUILT** — `B.truck.resident_trip_share` 0.002993 derived from the target LGA's G62 Truck cell by the motorbike carve's identity; carved on the same non-escorting pool and locked to `truck`; the yardstick's resident-truck deduction now describes real agents; rebuilds with F18 |
| 4.15.21 | The driver split scored on the target LGA's own G62 cell, like every other target | #93 #84 #94 | **DONE (§9.122)** — `g62_composition('target_lga')`: car 58.1631 → 58.3222, motorbike 0.2406 → 0.3785, resident-truck deduction 0.5963 → 0.2993, ferry 0.1013 → 0.1429; the two CAL/B fields moved by their unchanged identity and stay asserted against the source; `mode_targets_by_mode.csv` and the manifest regenerated |
| 4.15.12 | The demand's ride ceiling (~11% of trips bound vs 20.6% observed) | #86 #91 | **OPEN — the next root cause once 4.15.11 confirms ride realises what is bound** |
| 4.15.13 | Declare F13 and F14 in `run_families.json` (named by §9.99/§9.116, never declared) | — | **DONE** — the index no longer labels their arms F12 |

### P5 — scenario runs (blocked on 4.2)

| # | Task | ETA |
|---|---|---|
| ~~5.1~~ | ~~SUMO corridor harness + MATSim↔SUMO outer loop~~ **DELETED 25 Aug (§9.74)** — the outer loop retired with the descope | — |
| ~~5.2~~ | ~~SUMO version change for pedestrian crossings~~ **DELETED 25 Aug (§9.74)** — the standing DELETE proposal decided by the descope | — |
| ~~5.3~~ | ~~Charging dwell field measurement~~ **REWORKED 25 Aug (§9.74)** — `A.lightrail.dwell_charging_s` stays swept, never pinned; the dwell lives natively (#74); no site visit | — |
| 5.4 | Scenario × day-type runs, S0–S6, at the chosen fraction and settled iteration count — prioritise S0/S1/S2 × WEEKDAY; 30 sets total | wall: weeks; sequence by hypothesis need |
| 5.5 | Per-run close-out: metrics → fit → summary; replay pages rebuilt post-§9.36 only | attended ~1 h per run |

### P6 — analysis (blocked on P5)

| # | Task | ETA |
|---|---|---|
| 6.1 | Pedestrian counts: temporary counters on Hunter St frontage segments, or the land-use + modelled-alightings fallback — **hypothesis B1 has no observable without one of these** | elapsed weeks; attended 1–2 days |
| 6.2 | Retail floorspace + vacancy audit (`D.retail.vacancy_rate` is `unobtained`; hypothesis B2 depends on it) | attended 1–2 days |
| 6.3 | Open the 143 holdout targets **once**, at the end; score and report | attended 0.5 day |
| 6.4 | Hypothesis tests B1/B2/B3 with every headline bound to its sweep band (SCATS 38% swing, transfer penalty 3–15 min, charging dwell, corridor imputation uncertainty — the closed-as-impossible #27 reports here) | attended 1–2 weeks |
| 6.5 | Per-scenario interactive result explorer (project deliverable 5; replay + live view exist) | attended 3–5 days |

### P7 — write-up (blocked on P6)

| # | Task | ETA |
|---|---|---|
| 7.1 | Findings paper (project deliverable 4) | attended 1–2 weeks |
| 7.2 | Method note on evaluation gaps — the citable SCATS refusal (§9.21) | attended 2–3 days |
| 7.3 | Containerise the reproduction path (project deliverable 1's gap) | attended 1–2 days |
| 7.4 | Publish the data package with the ODbL / CC-BY split visible (deliverable 2; needs the 10 OSM layers from 4.1.1) | attended 1–2 days |

### ⚠ Four tasks PROPOSED FOR DELETION or rework — decision pending

Assessed against the goal (*does this help the twin predict ridership per
mode?*) in [`NEXT_AGENT_BRIEF.md`](NEXT_AGENT_BRIEF.md) §7. These four
are the most expensive per unit of goal in the whole plan, and all four are
about the corridor's street life rather than about ridership.

| # | proposal | why |
|---|---|---|
| ~~5.2~~ | ~~**DELETE**~~ **RESOLVED 25 Aug — deleted by the §9.74 descope** | — |
| ~~5.3~~ | ~~**REWORK** to "stays swept, never pinned"~~ **RESOLVED 25 Aug — reworked by §9.74**; the dwell lives natively (#74) | — |
| 6.1 | **REWORK** — try the land-use + modelled-alightings fallback only; if it fails, report hypothesis B1 as **untestable** | Elapsed *weeks* to buy pedestrian counters for a secondary retail-outcome hypothesis |
| 6.2 | **REWORK** — scope to what the existing land-use layer supports; commission no audit | Same family as 6.1, same distance from the goal |

### Backlog — do not start before the base works

2014 public timetable (era-1 validation) · LiDAR DTM (corridor grades only —
gradient reaches the behavioural model through nothing, #21) · event attendance
data (event-demand overlay, proposal §10) · socnetsim joint plans (toolchain
change) · a 2013 historical reconstruction (considered and dropped — do not
reopen without the user).

---

