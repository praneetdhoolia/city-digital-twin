# STATUS — city-digital-twin (Newcastle study)

Single source of truth for **where the build is, what's next, and how to resume**. Read
this at session start. **Keep it current in the same commit/PR as the work it describes**
— if a change makes a line here wrong, fix the line in that change, not later.

**Last updated:** 25 August 2026, EIGHTH session (**§9.80**: THE FRONT DOOR SHOWS THE MODEL'S FIT, AND A DEAD RUN SAYS WHY IT DIED - `README.md` described the package and never whether the model reproduces the city, and described the corridor's signals only as an input that could not be obtained, nine days after §9.77 made signal control MECHANICAL. New **`src/analyse/build_fit_figures.py`** draws mode share, the trip-length constraint and the 30 traffic counts from the run the calibrated base was written from (`C5_calibration.json`'s `best_tag`, so the figures and the calibration report never describe different arms), as dependency-free light/dark SVG with no wall-clock - which is what lets `--check` gate them. **CORRECTION, and the finding of this session: the light rail's 1,260 boardings had been reported as a -63% ERROR against V001/V002, targets `fit.py` marks UNSCORABLE** (2019-20 is a pre-pandemic market against a 2026 base, §12.1) - the modelled figure is a LEVEL and the gap is not a fit statistic; the framing had propagated through `CORRIDOR_PT_COMPOSITION.md` and three handover briefs, is corrected in all of them, is banned in the generator, and is filed as **#84** with the open question of what patronage IS legitimately checked against. **A dead run must now say why**: `_meta.json` REQUIRES a `cause`, read from the run's own `matsim.log` by new **`src/run/run_failure.py`**; all fourteen dead runs backfilled from their logs (the three 25 Aug probe failures independently reproducing the §9.77 narrative); `results/INDEX.md` prints every cause. `check_doc_currency.py` gains `decimals` and a `text` kind - a stale NAME was structurally exempt - plus ten README claims, and its stale-statement ban now covers every phrasing of "the package is not built yet" after the §9.79 ban named one wording and the same false claim survived under another in this board's own resume instructions. **`P4_CHECKPOINT.md` is retired as a live document and frozen as the 12 August record it was** - it restated this board's job and had drifted on deliverables, issues, manifest, registry, mode share, relaxation, counts, walk ratio and SUMO scope, and holds nothing the record does not. `docs/README.md`, `.claude/CLAUDE.md` and the `DECISIONS.md` header corrected; where a number has no artefact to pin to it is now a pointer to the thing that always knows. No model or data value changed; no run launched; nothing is a result.) PREVIOUS - SEVENTH session (**§9.79**: DOCUMENT CURRENCY BECOMES A GATE — an `/onboard` gap scan found the front-door `README.md` three phases stale (manifest 376 vs **489**, registry 210 vs **356**, road edges 43,112 vs **50,182**, agents 612,680 vs **612,687**) and two statements outright FALSE (`networks/osm/` called empty and the #32 re-harvest called pending, nine days after it ran and closed); this board carried the same figures and disagreed with its OWN P3 row. The cause was DUPLICATION — one figures table living in two documents, and the two session skills each carrying their own copy of the six state-of-the-project questions. Fixed, and made unrepeatable: **`tests/check_doc_currency.py`** (`--strict` gates CI) pins every live figure to the artefact that decides it over city-owned [`tests/doc_currency.json`](../tests/doc_currency.json) (22 claims), with an `absent` kind that bans a named false statement; [`docs/HANDOVER_CONTRACT.md`](../../../docs/HANDOVER_CONTRACT.md) defines the six questions, the trust order, the environment gate and the facts-that-expire rule ONCE for both skills. **A dated record stays FROZEN — only live-state cells are pinned.** Found while checking and filed, not fixed: the calibration report justified unfitted traffic counts by the absence of a through tier that §9.41 built and §9.64 measured as making no difference — the generator now states the supersession and the −91.8% residual across 30 stations (6 modelled-zero) is **#82**. No model or data value changed; no run launched; nothing is a result. PREVIOUS — SIXTH session (**§9.77/§9.78**: THE ACTIVATION BOUNDARY IS CROSSED — the session's `/goal` (implement every runless issue; signals, taxi and the full simulation factors first) resolved the §9.75 ordering by consequence (no run authorised → activate first; **family F5 closes UNMEASURED, the recorded cost**, its inputs regenerable), and the §9.76 checklist was executed item by item: `A.signals.representation=explicit_signals`, the new `A.crossings.representation=change_events` gate, taxi in both RUN vocabularies AND city.json, `bin_size_s` 300, `usingFastCapacityUpdate=false`, all 30 run-input sets regenerated consuming the signal models + capacity patches + signals/dwell schedules + crossing change events — **family F6 declared** in [`run_families.json`](audit/run_families.json). Two probe-caught defects fixed (the crossings XML violated the schema's element order; the S3 mid-block systems NPE'd the priority ledger on a null payee). **S3 is bus-keyed** (`A.signals.tsp.priority_group`, corridor in S3's overlay; third toy-probe case PASS; all 14 S3 controllers instantiate in-scenario). **Tier C landed** (#49): PT submodes score-distinct via SwissRailRaptor mode mapping, bytecode-verified, behind `RUN.routing.pt_submode_scoring`; a new `PtSubmodeMainModeIdentifier` pre-empts the stock identifier's interchange crash; probe shows ZERO `pt` legs (bus 1,414 / rail 450 / tram 10 / ferry 3) with main modes and conservation intact. **Seven 0b source upgrades** (#63) incl. `B.population.bike_available_rate` → CWANZ 2025 **0.493** (plans regenerated inside F6). **The corridor-composition question is answered on arm A** ([`CORRIDOR_PT_COMPOSITION.md`](audit/CORRIDOR_PT_COMPOSITION.md)): COVERAGE carries the bus-over-tram split — 98.3% of corridor-band demand needs an interchange the through-running buses don't; frequency exonerated. **The demographic measurement is on the record** (#50, [`DEMOGRAPHIC_MODES.md`](audit/DEMOGRAPHIC_MODES.md)): the modelled split is sex-invariant against G62's real sex structure; NO mode × age cell exists in the held data. **The TIA sweep came back empty** (19 applications; PPSHCC-137 stays the only SCATS evidence; PPSHCC-306 resolved, corrected to East End 105–121 Hunter St). **#66's settlement is mechanised** (Defender/TaskScheduler capture on the stall transition). **#62 landed all six strata**: `intervention_boardings` replaces the city-named metrics key (accepted schema break, pre-rename records unreadable by fit), manifest LINEAGE + currency/base-year + zone-id/coord-suffix tokenised into city.json, `check_package` split portable-harness / city-owned expectations (PASS 1433, nothing dropped), reader-shapes contract + Newcastle adapter with byte-identical outputs (census family recorded as remaining source-shaped). Probes only — 1%×2 plumbing; **no arm ran, nothing is a result**; the F6 arm (~65–67 h) still needs its own stated-cost approval, and `E.replication.n_replications` + the warm-restart ruling stay open.) Fifth (overnight) session (**§9.76**: BATCH 4.7 IS BUILT — the harness safety set is LIVE (warm restart #75 with its recorded validity caveat; the `_progress.json` digest #76 with the declared pace band; the cross-run index #77 over declared families in [`docs/audit/run_families.json`](audit/run_families.json); the detached Task Scheduler launch `run.py --detach` VERIFIED past `PersonPrepareForSim` with the launcher gone, #70); the SUMO descope is EXECUTED (#72) with Maven 3.9.9 + the MATSim signals run stack (2027.0-2026w25, 201 sha256-recorded jars) pinned as the logged §14 toolchain change; and the model-changing set is BUILT INERT for ONE family boundary — level crossings from OSM barrier tags with the Stewart-Avenue exclusion ASSERTED (#68), native charging dwell with concurrent-with-boarding DECIDED and the 12.00-min anchor preserved (#74), explicit corridor signals + the tram-priority controller with BOTH §9.75 toy probes PASSING and the double-count rule landed as artefacts (#73), and taxi as one blended priced mode on the archived Fares Order 2025 (#49). Six 0b fields moved onto measurement (#63; the operated NLR weekend factor 1.875, the era3 shuttle speed CONFIRMS the assumed 26, the LR regulated ceiling, spans, the segment count) and the new departure-profile constraint files its first finding (weekend shapes skew 3–4 h late). PPSHCC-137 is ARCHIVED under the decided free-TIA route (#78; site corrected to 643 Hunter St); output-schema enums are now injected from city.json (#62 A1). The assembled 4.6.9 run inputs are BYTE-IDENTICAL; activation is one boundary whose checklist is §9.76's closing block; nothing ran beyond two 1%×2 plumbing probes and nothing is a result.) Fourth session (**§9.73–§9.75**: a research-and-decisions session — no model, data or registry value changed, no run made. MATSim re-affirmed against the 2026 field on a documented survey and the embedded MATSim version recorded from the pinned jar's own metadata (2027.0-2026w25, §9.73); **SUMO descoped by recorded decision — MATSim is the single simulator** (§9.74, the fifth premise correction; mechanical execution is **#72**; deliverable 7/§9.16 retired; P5 tasks 5.1/5.2 deleted, 5.3 resolves to stays-swept-never-pinned); the ten-file signalling dossier landed at [`design/signalling/`](design/signalling/README.md) with operated SCATS interpreted history for two non-modelled Newcastle sites discovered public in a planning-portal TIA (acquisition routes parked on **#78**; `A.signals.scats_phasing` STAYS `unobtained`); and **the all-modes-first batch was set for the next session** — corridor signals + tram priority + lanes (**#73**), taxi as a priced mode (**#49**, resequenced past §9.42's deliverable-5 gate), level crossings (**#68**), native charging dwell (**#74**), the descope execution (**#72**), warm restart (**#75**), the progress digest (**#76**) and the cross-run index (**#77**) — activating as ONE family boundary, with the run-4.6.9-first-vs-fold-in ordering an open decision (§9.75). Issues #72–#78 filed.) Third session (**§9.72**: the session's `/goal` authorised the post-repair base arm (4.6.9) and BOTH detached launch attempts died silently within minutes — ~54 s in mid `PersonPrepareForSim`, then ~2 min in before config emission, no error artefact either time; attribution open (**#70**, agent-session process reaping suspected); both closed out as `aborted_*` with cause-stating `_meta.json`; the campaign was ended at `/handoff`. **No run approval is standing; launch the next arm from an interactive shell outside the agent session and verify past `PersonPrepareForSim`; arm B launches only if arm A's solo iterations 2–5 pace at the closed family's 217–253 s/it.** No model or data value changed.) Second session (**§9.68**: the ride collapse DECOMPOSED on the completed arms — 76,986 of 77,626 ride-available persons held no ride plan at all, return legs paired at 0.0079, intermediate at 0.0, and the uniform seed's 0.2 car probability was itself the 0.196 outbound pairing ceiling — and REPAIRED in the demand build: round-trip serve-tour allocation (drop-off + pick-up pairs, declared and swept), direct bound tours, serve tours seeded car, round-trip-covered passengers seeded ride, `liftHousehold` a comma list; **§9.69**: the missing short-trip mass gets its observed distribution — HTS Sydney 2012/13 Table 4.4.7 (18.8% of trips ≤1 km vs the model's 4.45%) drives a two-component gravity mixture whose short kernel mean is the package's own observed walk mean, with every observed per-(purpose × LGA) mean still met exactly; **§9.70**: the Hunter Valley coal chain (~110 train movements/day, ARTC/PWCS/NCIG observed) is deliberately NOT simulated — it runs on dedicated track grade-separated since 2006 — and the two real road interactions are named: the St James Rd Adamstown and Clyde St Islington level crossings (closures "up to ten minutes", logs unpublished → swept closure parameters, backlog) and the Mayfield port truck cap (1,268/day) as an upper-bound constraint; **#50's modelled table delivered** from arm A — the 0–17 bands travel 46–50% by bike and 0% by ride against the literature 61% driven-to-school, locating bike's +250% as displaced child ride demand. **B2/plans/run-inputs regenerating on the repaired mechanisms — a NEW comparability family; the §9.58–§9.63 family closes with the two completed arms as its record.**) **The first launch crashed on both seeds at replanning 1 and was repaired the same afternoon (§9.63, #65)**: the §9.60 M1 pass let two lift re-targets to one driver overlap, the splice interleaved their tours, and the per-tour modes then formed mixed chain/non-chain subtours SubtourModeChoice refuses; busy-check repaired + contiguity assertion added, B2/plans regenerated (0 interleaved, weekday lift bindings 55,249/55,614), both arms relaunched on the repaired demand. This session, under the session's `/goal` (fix the non-household-lift gap · research missing data · city-agnostic · ≥10× iterations without teleportation · every runless issue): **§9.58** — #60 verified to be a DIFFERENT defect than filed (first-hop topology breaks from activities on walk-less links, not turn restrictions) and repaired four ways, refusals 3.8k/iteration → **0**; **§9.59** — every wall-time knob declared and probed at 25% (replanning 76→33 s is the clean win; PassingQ corrects FIFO's walker-blocks-cars artefact at a measured ~42 s price; the 10× ask answered by measurement: not reachable without shrinking the physical work — the multiplier is two concurrent arms); **§9.60** — the non-household-lift gap gets its mechanism (M0 physical waiting + M1 re-targeting unbound observed-rate escort tours: WEEKDAY 55,280 of 55,614 bound, verified at 1% with 0 refusals and closing accounting); **§9.61** — G15 education split observed per SA1, the weekend day-type factors measured (SAT:SUN 1.1473; external weekend scaling was assumed at half its measured level; the 1 h departure shift survived its measurement), chain-timing scaffold constants declared; **#49 Tier R done** (pt split by scheduled submode in every report); **#62/#63 filed** (deep city-agnosticism; 0b backlog). Previous session same day: #54 fix (PR #58), `phys50_25pct` shakedown, §9.56 events threads (PR #59), §9.57 arm attempt stopped by instruction at iteration 136. Start from `main`

> **This file is a board, not a diary.** The dated build narrative that used to live
> here (944 lines) is archived in
> [`docs/handover/SESSION_LOG.md`](handover/SESSION_LOG.md). Its authoritative
> version is [`DECISIONS.md`](DECISIONS.md) §9.1–§9.36. **Do not append a session
> narrative here again** — record the decision in `DECISIONS.md` and update the board
> lines below that it makes wrong.

---

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
| Blocking state | **THE ACTIVATION IS DONE (§9.77/§9.78) — ONE DECISION DEFINES THE NEXT MOVE: approve the first F6 arm** (~65–67 h at 25%×1000; `run.py --detach` is the VERIFIED launch path, #70 closed). The §9.75 ordering question is RESOLVED by the session's directive (no run authorised → activate first; F5 closed UNMEASURED, its inputs regenerable — the recorded cost, §9.77). Every model-changing lane is LIVE in the assembled inputs: explicit signals + saturation capacities + variant-own delay removal, the two freight crossings as a time-variant network, native dwell, taxi as a priced mode, score-distinct PT submodes, bus-keyed S3 priority, the CWANZ-cited bike availability. Probes verify plumbing only (1%×2, S2 and S3, rc=0); every effect measurement awaits the arm. **THE 4.6.9 ARM IS LAUNCH-BLOCKED, NOT MODEL-BLOCKED (§9.72, 24 Aug third session)** — the approved launch died silently twice (attribution open, #70); the next attempt must come from an interactive shell outside the agent session and is verified only past `PersonPrepareForSim`; the `/goal` approval is SPENT, so a fresh stated-cost yes is needed; arm B is conditional on arm A's solo pace (217–253 s/it at iterations 2–5). The model side is unchanged and ready: **THE RIDE LEVER IS ANSWERED BY MEASUREMENT (§9.68, 24 Aug second session)** — the standing goal (all ridership as close to real life as possible, ride first) is being executed: the decomposition read the completed arms and showed the §9.64 "demand-side scoring lever" framing was survivorship bias — the ASC could flip 109 persons of a 77,626 pool; the real constraints were one-directional serve-tour allocation (return pairing 0.0079), seed decoherence (p=0.2 car seed = the 0.196 outbound ceiling) and intermediate stops unmaking bound serving legs. All three repaired in the demand build (§9.68), the short-trip mass repaired with it (§9.69); **B2 + plans + run inputs regenerating; next run = new family, needs fresh stated-cost approval (~65–67 h/arm at 25%×1000)**. `E.replication.n_replications` still awaits a decision (seed floor ≤0.11 pp/mode at n=2). Previous close: **BOTH ARMS COMPLETE (§9.64, 24 Aug)** — `20260821T175907_1000it_25pct` (arm A, ex `phys1000a_25pct`) and `20260821T180310_1000it_25pct` (arm B, ex `phys1000b_25pct`; all run directories renamed 24 Aug to the §9.65 runner scheme) each ran 1000 iterations, rc=0, relaxed (drift 0.031 pp), conservation closes on every mode: the first valid runs of the §9.58–§9.63 family. **C5 exists** (`params/C5_calibration.json`, §9.50 constrained base, objective 10.65 pp, feasible=False with five stated violations) — deliverable 5's gate is passed in the constrain-and-report sense; #14/#9 close. **The next decision is pending**: which demand-side scoring lever answers ride's collapse (§9.64 — M2 is a no-go on the evidence; 100% of surviving ride requests pair and board, the loss is in choice), and what `E.replication.n_replications` becomes now the seed floor is measured (≤0.11 pp/mode at n=2). The §9.62 launch history: first launch crashed on both seeds at replanning 1 (§9.63, #65 — repaired same afternoon; the dead runs are `results/aborted_20260821T172050_1000it_25pct` and `results/aborted_20260821T172453_1000it_25pct`, `_meta.json` status `failed`); the §9.57 attempt is `results/aborted_20260821T010821_1000it_25pct` (status `aborted`). **The #60 decide-before-relaunch question is RESOLVED (§9.58)**: the defect was verified to be a different mechanism than filed (activities off the walk/bike subnetworks + MATSim's silent nearest-link route fallback, not turn restrictions), and the four repairs are BUILT and probe-verified — refusals 3.8k/iteration → **0** at 1%. §9.58–§9.61 start a NEW family (network + model + demand change, free — no completed run existed). The arm would run at a measured **~233 s/iteration → ~65 h single, or two concurrent arms (qsim 8 + events 4 each, §9.59)**; relaunch requires fresh stated-cost approval. It re-baselines everything at once: the emergent ride share (now with §9.60 lifts) vs 20.60, walk vs 13.40 (#30's numbers are from the wedged model and re-measure here), the §9.50 constrained base (C5 + report). #54's accounting fix is MERGED (PR #58), so the run's own gate is trustworthy |
| Committed data package | **489 files** in [`data/MANIFEST.csv`](../data/MANIFEST.csv) · `check_manifest.py` passes · `check_package.py` **ALL PASSED** (2 standing warnings; it prints its own check count, which is why one is not restated here) — now a portable harness over city-owned expectations ([`cities/newcastle/tests/package_expectations.json`], #62 B4) |
| Input registry | **356 fields** (§9.77/§9.78: +`A.crossings.representation` and `A.signals.tsp.priority_group` gates, +`RUN.routing.pt_submode_scoring`, +`B.census.thin_cell_min_journeys`; seven 0b source upgrades incl. CWANZ bike availability 0.493) — every one with units, provenance and a sweep, held-fixed rule or derived identity; ledger **0** with `--strict` gating CI |
| Run inputs assembled | **30** scenario × day-type sets, **regenerated 25 Aug at the §9.77 activation boundary (family F6)**: each config carries the signals module + generated plans, `usingFastCapacityUpdate=false`, the time-variant network + crossing change events, `travelTimeBinSize` 300, taxi in both vocabularies with blended fares via the `fare` module, the `swissRailRaptor` submode mappings + per-submode modeParams, `tramPriority` (bus-keyed on S3), PassingQ, `ridePairing`, the split thread pools and the per-mode vehicles file the harness re-emits per run; networks carry the saturation-flow re-capacitation on signalised approaches |
| What is PHYSICALLY simulated (measured 20 Aug, §9.49–§9.55) | **EVERY person-transport mode is in the mobsim**: `car`; **`truck`** PCE 2.0 (913 trips / 140,380 traversals at 1%); **`motorbike`** PCE 0.4 on the measured G62 anchor (52 trips at 1%); **`walk`** PCE 0.0 capped at 1.25 m/s — the sidewalk in queue arithmetic (9,050 trips at 1%); **`bike`** PCE 0.2 at 4.2 m/s (2,311 trips); **bus** 1,448 / **rail** 332 / **tram** 252 / **ferry** 107 transit vehicles; **`ride`: every surviving ride trip is a passenger PHYSICALLY IN a household car (§9.53), and an unpairable ride trip re-modes to physical walk (§9.55)** — final probe iteration: ride = 67 trips, all boarded. Remaining teleports: the PT access/egress stubs (declared helper, §9.54) and the counted boarding-miss fallback (5–6/iteration, the ×6.91 window layer). **Taxi/rideshare: A MODE since §9.77** — one blended priced point-to-point mode, routed on the congested car network (probe: 1.4–2.1% of LGA trips at 1%, car-like speeds), fares from the archived Fares Order 2025 + literature rideshare rates, volume reported against the 15–25k/day band as a constraint |
| **Ride pairability — the repair is MEASURED to work (§9.48)** | Pre-repair, **0.10% (25%) and 0.04% (10%) of ride trips shared an origin–destination pair with a household car trip at any time**. Both causes were fixed (§9.45 sampler, §9.46 binding), and the re-measure arm (`bind1000_25pct`) now puts numbers on the repair: **OD-coincidence 15.31% (23,738 of 155,085 ride trips), declared-regime (`both_links` ±15 min) pairing rate 0.0130 (2,014 trips), direction split non-zero (239 return pairings)**. The realisation gap — 15.31% coincident vs 1.30% paired — is named in §9.48 and deliberately not chased while occupancy sits ABOVE its observed value (0.4855 vs 0.3503, outside the declared range in the flattering direction) |
| Ride scenarios — data grade | **Commute carpooling is RARE and the demand is non-commute**: census G62 (already in the package) gives car-as-passenger **3.35% of journeys to work**, passenger:driver **0.0598**, at SA1 — against an all-purpose HTS `Vehicle passenger` share of 18–32%. OBSERVED: commute (G62), driver-side `Serve passenger` 10–19.5% of journeys, all-purpose share, ride trip length/duration, occupancy 0.35. LITERATURE ONLY: child→school (61% of school trips by private vehicle), elderly driven. **Non-household lifts now have a MECHANISM but still no target** (§9.60, directed by recorded decision): unbound observed-rate escort tours are re-targeted to driverless-household passengers — WEEKDAY binds 55,249 of 55,614 (99.3%, the §9.63 repair skips 31 overlapping bindings) — and a booked passenger physically waits for the car (M0); who-drives-whom stays unobserved, so the household/non-household split is reported, never fitted. Return-trip asymmetry remains a stated limitation |
| Comparability | **A FIFTH family boundary at §9.77 (25 Aug): family F6** — explicit signals, crossings, native dwell, taxi, PT submode scoring and the CWANZ bike rate all activate as ONE boundary; **F5 (§9.68/§9.69) closed with NO converged arm ever run in it** — the ride/walk repairs will re-measure only jointly with the batch on the first F6 arm (the recorded cost of the activate-first order, §9.77); F5's inputs stay regenerable from the declared switches. The prior boundary: **a fourth family boundary at §9.68/§9.69 (24 Aug)**: the ride repairs and the short-trip mixture change the demand, the seeds and the plans, so **nothing run on the regenerated demand compares to `20260821T175907_1000it_25pct` / `20260821T180310_1000it_25pct`** — those two arms stay valid as the CLOSED §9.58–§9.63 family's record and the pre-repair baseline. The prior boundary: **a third family boundary at §9.58/§9.59 (21 Aug)**: the walk-wedge repairs change the network (reverse walk/bike complements, trunk walkable, activity links pinned) and the model (SubtourModeChoice person-only, PassingQ link dynamics, split replanning threads), so **nothing run after §9.58 compares to `phys50_25pct`, the aborted `phys1000_25pct` diagnostics, or anything older**. The §9.49 boundary before it: freight changed the demand AND the model, so `bind1000_25pct` closed the §9.46/§9.47 family. The earlier triple break (§9.44/§9.45/§9.46-47) stands; the two pilot arms remain baselines for the PRE-repair model only. §9.43 (iterations=1000) is unaffected |
| Runs on disk | **All 35 run directories were renamed 24 Aug to the §9.65 runner scheme** `<launch yyyymmddThhmmss>_<iterations>it_<pct>pct`; the old→new map is DECISIONS.md §9.65, and the runner now names every new run itself (`--tag` is gone). **The FIRST VALID RUNS of the all-physical family (§9.62/§9.64, completed 24 Aug)**: `results/20260821T175907_1000it_25pct` (arm A, ex `phys1000a_25pct`) and `results/20260821T180310_1000it_25pct` (arm B, ex `phys1000b_25pct`) — 1000 iterations each, rc=0, `relaxed: true`, `_run.json` + `_fit.json` + C5 written from arm A; arm B is the seed replication (its product is the A-vs-B spread, ≤0.11 pp/mode). Prior families, none comparable to the §9.58+ model: the #5 pilot arms `20260816T022250_1000it_10pct` and `20260817T011703_1000it_25pct` (ex `conv1000_10pct`/`conv1000_25pct`, both rc=0 and `relaxed: true` — [`docs/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md)) and the completed re-measure arm `20260818T235351_1000it_25pct` (ex `bind1000_25pct`, evaluated §9.48 — the LAST run of the §9.46/§9.47 family). Everything else is a PLUMBING/TIMING probe, not a result: the all-physical shakedown `20260820T202754_50it_25pct` (ex `phys50_25pct`), the §9.56/§9.59 events-and-knob probes (`20260821T003843_5it_25pct`, `20260821T131322/T141252/T144513/T152035_5it_25pct`, `20260820T230351/T230710_2it_1pct`), the §9.58/§9.60 verification probes (`20260821T130340/T130835_2it_1pct`, `20260821T155944_2it_1pct`), the §9.68 regenerated-demand verification probe (`20260824T210040_2it_1pct` — return legs pair 347/347 at it-2), the §9.76 DETACHED-launch verification probe (`20260825T033850_2it_1pct` — launched by `run.py --detach` under the Task Scheduler, past `PersonPrepareForSim` to rc=0 with the launching shell gone; its `aborted_20260825T033406_2it_1pct` predecessor died rc=1 on the unmaterialised-tramPriority defect the probe existed to catch, fixed the same hour), the §9.44–§9.55 smoke/pairing probes (`20260818T194826_3it_1pct`, `20260818T205739_50it_1pct`, `20260818T211301/T212802/T214527_10it_25pct`, `20260820T150002/T162958/T165314/T175133_2it_1pct`) and `20260816T015048_2it_1pct` (ex `smoke_postrebuild`). **Every dead run sits at `results/aborted_<launch>_<iterations>it_<pct>pct`, and each is listed with the cause it died of under *Why the dead runs died* in [`results/INDEX.md`](../../../results/INDEX.md)** — regenerate that with `build_run_index.py` rather than counting them here (§9.66; §9.80: `_meta.json` now REQUIRES a `cause`, read from the run's own `matsim.log`): the two §9.72 silent launch deaths of the 4.6.9 arm (`aborted_20260824T212729_1000it_25pct` `failed`, `aborted_20260824T225951_1000it_25pct` `aborted` — attribution open, #70), the two §9.63 SMC crashes (`failed`), the §9.57 stopped arm (135 iterations of trajectory diagnostics preserved), the cancelled 1500-iteration arm (do not relaunch it), the §9.50 base arm instruction stopped at ~iteration 20, and four older dead runs — all `aborted`. **Every run now carries `_meta.json`** (status · started · ended · parameters, §9.66), auto-written at launch and updated at completion/failure/abort, with stale `running` states reconciled by pid at the next harness start; relaunching any dead run needs fresh stated-cost approval |
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

## Phase progress

| Phase | State | What is done | What is not |
|---|---|---|---|
| **P0** Scoping | ✅ complete | Base year 2026, zone system, S0–S6 settled (§1) | — |
| **P1** Data acquisition | ✅ complete for P4's needs | **55 immutable raw downloads**, each hashed and provenance-tagged; 10 OSM layers re-harvested 16 Aug over the derived extent; DEM tile set derived from the boundary (5 tiles, 100% gradient coverage) | Field dwell measurement never done. SCATS **refused by policy** (§9.21), journey-linked Opal unpublished — both swept, never pinned. Two ABS DataPack URLs (Mesh Blocks NSW, WPP DZN) now 404 upstream — files were never held locally; noted, not chased. |
| **P2** Network build | ✅ **rebuilt 16 Aug on the corrected extent** | 1 MATSim base (181,892 links) + 4 variants, 15 mapped feeds, **0 unmapped stops in every feed**, 4 SUMO nets; link speeds agree with the declared registry values | Corridor kerbside 95% imputed, lane width 98.6%, capacity 100% (#27 closed as *cannot* be closed — B3 must report them as uncertainty). |
| **P3** Demand synthesis | ✅ **regenerated 20 Aug with the freight tier (§9.49)**, on the 18 Aug age-structure and escort-binding repairs (§9.46, §9.47) | 612,687 agents with census age structure, employment per SA1 × sex × age band (G46), education attendance per SA1 (G01); 621,722 WEEKDAY plan persons (incl. external, 16,264 through cars and **90,393 freight trucks** — 1,691 through + 88,702 internal); **68.6% of weekday escort tours bound** (identical to §9.46); destinations solved per purpose × home LGA; through tier at 3 gates, each split car/truck by its station's observed heavy share | Northern through exits ungated (§9.41 limitation). Truck routing unconstrained (§9.49 limitation — no truck-route layer exists). Bike/walk shares re-measure on the first real run before #29 is sized. |
| **P4** Calibration | 🟡 **in progress — 8 of 9** | Harness, metrics, fit, calibration loop, report, outer-loop tolerance, live run view, **calibrated base (C5, §9.64 — constrain-and-report, feasible=False stated)** | Deliverable **0** (input completeness — the 0b backlog, #63) not met. The base's report card (MAE 10.65 pp) opens the demand-side scoring lane. |
| **P5** Scenario runs | ⬜ not started | Descope EXECUTED (§9.76, #72 closed); the native corridor mechanisms are BUILT INERT (#73/#74/#68) | The phase's substance is the S0–S6 scenario runs themselves. |
| **P6** Analysis | ⬜ not started | — | Hypothesis B1 has **no observable at all** without pedestrian counts. |
| **P7** Write-up | ⬜ not started | — | — |

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
| 1 | Run harness | ✅ done | [`src/run/`](../../../src/run/) |
| 2 | Metric extraction | ✅ done | [`src/analyse/`](../../../src/analyse/) |
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
| **0a** | **Specification audit.** DONE - the ranked register is [`docs/audit/SPEC_AUDIT.md`](audit/SPEC_AUDIT.md) (§9.25). | **Two near-exact inversions, not five miscalibrations:** car -26.5 / ride +29.4 and walk -12.7 / bike +12.7. **A1: ride is routed on the network but not simulated in it**, so it realises **55.7 km/h against car's 49.3** - a passenger arrives 13% faster than the car carrying them (#28). A2/A3: ride is not chain-based and bike ownership is silently universal (#31, #29). A4: walk's 18x deficit may be trip lengths, not scoring (#30). **B1 prevented damage - #24's business-travel premise is false.** **A1's defect is verified; its mode-share effect is WITHDRAWN (§9.27) - both arms ran at 250 iterations, and the pre-fix model at 1000 fits BETTER (33.8 pp) than the post-fix model at 250 (44.6 pp), so car/ride was largely non-relaxation. Walk/bike does NOT improve at relaxation and is confirmed structural (#30, #29).** |
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
| 2 | Open data package | 🟡 **489** files, provenance, licence, lineage — the ODbL/CC-BY split is recorded per row but not yet published (task 7.4) |
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
| Population | 611,915 (2021 Census) → 612,687 synthetic agents |
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
board, [`docs/audit/ISSUE_VERDICTS.md`](audit/ISSUE_VERDICTS.md),
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
| 4.2.1 | ✅ **DONE 18 Aug.** Convergence pilot, one arm at a time: 10% × 1000 and 25% × 1000. Both failed the *declared* gate identically — diagnosed as a defect in the instrument, not the runs: the window started at the innovation cutoff and so included a **one-iteration** selection snap (+3.3 pp car at both fractions), making it unpassable at any horizon. Fixed and declared in one change (§9.43): `RUN.relaxation.settle_margin_iterations` = 10, `RUN.controler.last_iteration` = **1000** (`measured`, off `unobtained`), both arms now `relaxed: true` at +0.22 / +0.17 pp. Arm 3 (`conv1500_10pct`) **cancelled by instruction** for compute economy — the ~2 pp of un-relaxed pre-cutoff search creep is carried as **declared uncertainty**. Evaluation: [`docs/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md) | #5 | ✅ 42 h of compute spent |
| 4.2.2 | ✅ **DONE 18 Aug** — measured on both pilot arms: ride out-runs car in every bin below 50 km (1.13× → 1.01×), the aggregate parity is a Simpson's reversal; bike 4.0% vs 3.2 observed needs no tuning; sub-1 km mass 2.5% vs >~10% reopens #30. [`docs/audit/CONVERGENCE_PILOT_EVALUATION.md`](audit/CONVERGENCE_PILOT_EVALUATION.md) | #28 (sized), #29 (closed) | — |
| 4.2.3 | ✅ **DONE — built 18 Aug (§9.44, PR #40), re-measured on the repaired demand 20 Aug (§9.48).** Tier 1 `BeforeMobsim` pairing: a paired passenger takes the household driver's realised time; blast radius measured against a control (7 legs rewritten vs 0, mode share bit-identical). **Step 3, the re-measure arm, is complete**: `bind1000_25pct` (25% × 1000 WEEKDAY, rc=0, relaxed) measures OD-coincidence 0.104% → **15.31%** and declared-regime pairing 0.00004 → **0.0130**; the #28 residual is ~11.6 s at 25%; occupancy 0.4855 vs observed 0.3503 (outside range, flattering direction — 4.2.4's problem). The realisation gap (15.31% vs 1.30%) is named in §9.48, not chased | #28 (sized), #31 (measured), #9 | ✅ |
| **4.2.5** | ✅ **DONE 18 Aug (§9.46).** The escort tour binds to the person being escorted: households generate whole, an HX tour takes an already-drawn member trip's destination and departure **exactly** (all 120,980 placed weekday bindings verified coincident), bound tours are immovable in the escorter's timeline, unbound tours fall back to the distribution. **68.6% of weekday HX tours bound**; rate untouched (re-target, never add); binding scope and min-gap declared and swept; escort trips can no longer be made BY `ride`. Whether realised pairability moves is the next run's measurement | #31 (supply half), §9.44, §9.46 | ✅ |
| **4.2.6** | ✅ **DONE 18 Aug (§9.47).** Employment now per (SA1, sex, ABS age band) from G46 — 65–74 realises 15.3%, 75–84 1.5% against the flat 52/48 before; **plus two defects the brief did not know**: the 75+ population was missing (grouped G04 columns never read — 85+ had 186 persons against a census 15,151, now 16,188) and student status is now observed attendance (G01) instead of 100% of under-18s. Full evidence: [`docs/design/age-structure.md`](design/age-structure.md) | population defect, §9.47 | ✅ |
| **0d(3)** | ✅ **DONE 20 Aug (§9.49).** Freight is a physical `truck` mode: through-gate volumes split by each station's own observed heavy share, an internal tier over the observed freight-industry attractor at the assumed swept ratio (0.0697, sweep 0.0–0.14), departures and weekend factors MEASURED from the classified hourly counts. Smoke-verified (913 trips, 140,380 traversals at 1%); car fleet unchanged, proven against the jar's bytecode. **Comparability break: a new demand family starts here** | #24 | ✅ |
| 4.2.4 | 🟡 **DECIDED, not delivered (§9.50, PR #47).** The §8.5 branch is constrain-and-report, logged before any result: ASCs stay priors, #9 resolved by decision, the §9.48 occupancy excess reported not absorbed; the loop's rebuild-stage defect fixed (unclassified consumers were defaulting to movable); `--constrained-base` machinery built and tested. **DELIVERED 24 Aug (§9.64)**: the completed base arm `phys1000a_25pct` produced C5 via `--constrained-base` (objective 10.65, feasible=False, five violations stated) and the calibration report; #14 and #9 closed | #14, #9 | ✅ decision + delivery |
| 4.4 | **Point-to-point (taxi + rideshare) mode** — decision re-opened 18 Aug 2026 on new evidence (IPART now surveys Newcastle and Hunter as its own p2p region; the passenger service levy counts every trip). Build as a teleported priced mode: measured taxi fares, literature rideshare rates (swept), fleet assumed; validated against the inferred 10,000–35,000 trips/day band as a **constraint, never a target**. Evidence dossier and declaration plan: [`docs/design/point-to-point-mode.md`](design/point-to-point-mode.md). **Strictly after 4.2.4** — a ~1% refinement does not precede the measured 10–20 pp defects. First step: extract the Newcastle and Hunter table from the IPART 2025 information paper (PDF fetch timed out on first pass) | p2p mode | attended 2–3 days |
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
| 4.7.3 | Cross-run index with family and validity labels | #77 | ✅ **BUILT 25 Aug (§9.76)** — `results/INDEX.md`/`.csv` over the declared [`run_families.json`](audit/run_families.json); 38 directories labelled |
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
mode?*) in [`NEXT_AGENT_BRIEF.md`](handover/NEXT_AGENT_BRIEF.md) §7. These four
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

## How to resume

**Run `/onboard`** — it executes the sequence below as a skill: the reading in
precedence order, the §0 environment checks, a cross-check of these documents
against live GitHub state, and the six state-of-the-project answers. At
session end, **run `/handoff`** to close out. The manual sequence, for a
session without the skills:

**Pick the work up from [`docs/handover/NEXT_AGENT_BRIEF.md`](handover/NEXT_AGENT_BRIEF.md)**,
which `/handoff` rewrites in place every session. Two files under `handover/` are
**archive only and must not be read as current state**: the dated build narrative
in [`docs/handover/SESSION_LOG.md`](handover/SESSION_LOG.md), and
[`docs/handover/P4_CHECKPOINT.md`](handover/P4_CHECKPOINT.md) — a frozen 12 August
record, retired as a live document on 25 August (§9.80) because it duplicated
this board and `DECISIONS.md` and had drifted from both. **This file stays the
source of truth for the phase board and the deliverable checklist.**

1. Read this file, then [`DECISIONS.md`](DECISIONS.md) §0 (status summary) and
   [`CLAUDE.md`](../../../.claude/CLAUDE.md) (conventions and hard constraints).
2. `python tests/check_manifest.py` — confirms the committed subset is intact.
3. `python src/setup/bootstrap_toolchain.py --verify` — confirms the toolchain and
   **compiles the Java**, or run it without `--verify` to fetch it (~1.4 GiB).
4. `python tests/check_package.py` — needs the full local package, the built networks
   **and** the P3 demand artefacts, so it runs on a workstation and never in CI.
   Run it before declaring any phase complete.
5. `python src/registry/render_docs.py` and `python src/registry/render_schema.py` after
   any change to `cities/<city>/registry/`, and
   `python src/analyse/build_fit_figures.py` after a new calibrated base, or
   `check_package.py` will report the reference or the figures as stale.
6. `python tests/check_doc_currency.py --strict` and
   `python src/registry/check_hardcoding.py --strict` — both gate CI and both
   must exit 0 before any commit.
7. Branch as `<git-handle>/<short-kebab-description>` (never `claude/*`).
