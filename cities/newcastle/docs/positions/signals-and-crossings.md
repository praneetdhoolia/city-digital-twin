# Signals, SCATS and level crossings — current position

Living documents that still say "SCATS phasing is unobtained and handled by sweep" (the S2b overlay description and the `A.signals.tsp.mode` description; `.claude/CLAUDE.md` and `STATUS.md` no longer do) describe the pre-§9.88 state; §9.88 is newer and wins. The precise statement is: the operated plans and the offset library are unobtained; the control logic that produces cycle and splits is implemented and live.
*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has reached its gate.*

**Updated:** 3 September 2026 (twenty-sixth session) · **Record read through:** §9.141 · **Written against family:** `F23`

## What is built

- **SCATS is implemented, not assumed.** `A.signals.control_regime` = `scats_adaptive`; all 14 corridor systems in every scenario name `CitysimScats` (`src/java_signals/citysim/ScatsSignalController.java`), and every emitted config carries the `scats` module (§9.88). The controller measures degree of saturation at each stop line from the mobsim's `LinkLeaveEvent`s — served against saturation flow × lanes × green, the denominator scaled by `qsim.flowCapacityFactor` — and at each cycle boundary steps cycle length toward the target on the critical movement and re-splits green to equalise DS across stages; clearances are preserved as safety geometry (§9.88).
- Algorithm parameters, all bound into the `scats` module: `A.signals.scats.target_degree_saturation` 0.90, `cycle_step_s` 6, `min_cycle_s` 30, `max_cycle_s` 150, `ds_deadband` 0.05, `ds_smoothing` 0.5, with `A.signals.min_green_s` 6 (§9.88). `fixed_time` is the kept sweep member and reproduces every pre-§9.88 arm; `run_matsim.py` refuses a declared regime that disagrees with the committed control file (§9.88).
- The 14 intersections (`A.signals.n_corridor_intersections`, observed) are explicit MATSim signal systems generated per scenario by `cities/newcastle/build/build_matsim_signals.py` from the A2 declared values against that scenario's own mapped network, into `cities/newcastle/networks/matsim/signals/<S>/` (§9.76). Phase structure is link-level: corridor approaches, cross approaches, and a tram group tied to the corridor phase because the T-aspect moves with parallel traffic; a site with no cross-street car approach is a mid-block crossing signal (§9.76).
- `A.signals.representation` = `explicit_signals`: every run-input set carries the `signalsystems` module, `qsim.usingFastCapacityUpdate=false`, the re-capacitation of signalised approaches to `A.signals.saturation_flow_veh_h_lane` 1900 × lanes (`signals_capacity_patch.csv`), and `transitSchedule_signals.xml.gz`, which removes each variant's own embedded per-intersection tram delay — one representation per effect (§9.77).
- Transit priority lives inside the SCATS controller, on the `tramPriority` module: `A.signals.tsp.mode` `green_extension`, `extension_window_s` 12, `detection_distance_m` 120, `priority_budget_share` 0.2, `compensation_enabled` true, `lateness_threshold_s` 60, `priority_group` `tram` (`corridor` in the S3 overlay, giving link-level bus priority) (§9.77, §9.88). SCATS decides the plan for cycle N and a detected vehicle may deform that cycle; compensation is intrinsic — a stage that gave up green shows a higher DS and the next split hands the time back (§9.88). **Which stage donates is decided by the layout** (§9.141, #125 closed): an extension borrows from a stage AFTER the tram's, so the re-laid drop moves later; a recall truncates the running stage before it; a tram stage that is last in its cycle is refused, counted and logged, never charged. The donor was once the stage with the most spare green, and a donor before the tram stage shifted onset and drop together and extended nothing while the budget was spent. The conditional lateness boundary is the fixed-time controller's. `citysim.ScatsPriorityProbe` drives the controller on a three-stage plan: extension moves the drop 58 → 68 s with the cycle conserved, recall pulls the onset 30 → 20 s (§9.141).
- Level crossings: `A.crossings.representation` = `change_events`; `cities/newcastle/networks/matsim/crossings/crossing_change_events.xml` enters every config as a time-variant network, with `RUN.travel_time.bin_size_s` 300 so a closure is visible to the router (§9.77). `A.crossings.closure_source` = `schedule_derived`: `build_level_crossings.py` locates the two boom-gated crossings from OSM `railway=level_crossing` nodes matched to `A.crossings.freight_road_names` (Saint James Road, Clyde Street), finds the mapped rail links within `A.crossings.rail_match_radius_m` 40, and closes the road for every scheduled service that traverses them, timed from that service's own stop time, for `A.crossings.closure_duration_passenger_s` 60 (§9.90). The builder refuses a crossing with no mapped rail link or no scheduled movement, and refuses any closure within `A.crossings.corridor_exclusion_m` 500 of a corridor intersection — Stewart Avenue is a T-aspect signal site, never a boom gate (§9.75, §9.76).
- Charging dwell is native in the mapped schedule: every intermediate light-rail stop holds `departureOffset = arrivalOffset + max(existing gap, resolved dwell)`, concurrent with boarding, anchors unchanged (§9.76). `A.lightrail.dwell_charging_s` stays `unobtained` with a null value, swept 10–35 s; S2/S2b/S2c select 20 s and S2a 0 s as the disabled arm (§9.76).
- Corridor signal identity: `scats_site_id` filled for all 14 from TfNSW's Traffic Lights Location inventory, mean match 8.0 m, maximum 26.4 m; `A.signals.scats_match_radius_m` 60 is a join tolerance, held fixed (§9.24). Eight of the 14 were installed in 2018 for the light rail; recorded as an attribute only (§9.24).

## What is derived, and what is still unobtained

| Quantity | Position |
|---|---|
| Cycle length at each of the 14 sites | **Derived at run time** by the controller from measured DS, bounded by `min_cycle_s`/`max_cycle_s` and by the intersection's clearances plus minimum greens (§9.88) |
| Splits | **Derived at run time**, DS-equalised across stages every cycle (§9.88) |
| Degree of saturation | **Measured in the mobsim**, never inferred from the plan under evaluation (§9.88) |
| Transit priority | **Implemented** — green extension within a budget share; `extension_recall` and `conditional` are swept members. Which mechanism TfNSW operates on the light rail is a documented gap (dossier `02-newcastle-signalling.md`) |
| The starting plan (110 s, split 45/15/30/10) | **Assumed** A2 proxy, now the starting point only; under `fixed_time` it is the whole plan (§5, §9.88) |
| Offsets and corridor coordination | **Not adapted, deliberately.** SCATS selects offsets from an operator-tuned per-subsystem library; that library is the unreleased artefact and has no algorithm to fall back on. Each system keeps its generated offset; coordination is a stated limitation, not a fabricated input (§9.88) |
| The operated phase plans for the 14 sites | **Unobtained**: `A.signals.scats_phasing` is null, refused by TfNSW policy (§9.21). Its three-way categorical sweep no longer reaches an emitted parameter under `scats_adaptive` |
| Saturation flow | Literature 1900 veh/h/lane, swept 1800–2050; no Newcastle stop-line survey exists (§9.76) |
| Movement-level lanes and protected turns | **Data-gated**: observed turn-lane coverage is 46 of 280 corridor trunk edges (16%), so lanes would be invented geometry (§9.76, #73) |
| Crossing closure count and timing | **Derived** from the scenario's already-mapped rail timetable, never from a re-run of the mapper (§9.90) |
| Freight closures | `A.crossings.freight_closures_per_day` 0 on recorded evidence — the coal chain has been grade-separated since 2006 — swept 0–30 because ARTC publishes no movement log (§9.70, §9.90) |
| Offset between a train's nearest stop and the crossing | Not modelled; under a minute at both sites, stated (§9.90) |
| Charging dwell | **Unobtained**, swept, selected per scenario (§9.76) |


## What is measured

- Probe `20260828T230050_2it_1pct` (S2, 1%, rc=0): all 14 systems re-time; NLR_SIG_01 runs 110 → 104 → 98 → 92 s against critical DS 0.564 → 0.282 → 0.141 (§9.88). Probe `20260828T230739_2it_1pct` (S2b, rc=0) carries SCATS and green-extension priority together, 168 logged re-timings (§9.88).
- Two defects the build surfaced and fixed: DS read 0.000 at a 1% sample until the denominator carried `flowCapacityFactor`; modular cycle arithmetic cannot survive a variable cycle, so the controller keeps an explicit cycle start and re-times only at a boundary (§9.88).
- Crossings: Saint James Road 110 closures per weekday and Clyde Street 204, against 30 assumed at both; change events 541 → 3,014; peaked where the service is peaked (§9.90). Mode 12 `freight_train` carries a derived target of 314 closures per weekday in `mode_targets_by_mode.csv` (§9.90).
- Operated evidence, archived and not an input: TIA PPSHCC-137 (`cities/newcastle/data/raw/planning_tia/PPSHCC-137_643_hunter_st_tia.pdf`) republishes SCATS interpreted history for TCS 1138 Hunter/Steel at 72–81 s and TCS 923 King/Steel at 104–113 s on 19 July 2022; neither is one of the 14 modelled sites, so it is a prior on the sweep, not a measurement (§9.75). The systematic portal sweep — 19 applications, 13 documents — found nothing further (§9.78).
- No arm-scale signal or crossing effect exists yet. A 1% probe verifies plumbing only, at about 0.3 vehicles per green (§9.76); the per-green discharge check at 25% reads 7.1–7.9 on the worst approach (§9.76). Every arm since F12 runs SCATS and the derived closures, and none has reached its gate.

## What is open

- **The signal-effect measurement at arm scale is still owed** (#73, CLOSED on the build scope): signals and priority are built, activated (§9.77) and adaptive (§9.88), and the controller and its guard are the evidence that closed it. What remains is not a build but a reading, and it needs an arm that reaches its horizon. Movement-level lanes stay data-gated at 16% coverage (§9.76). The issue's last comment predates §9.88; the SCATS build is not yet recorded on it.
- **The closure-effect measurement on a converged arm is still owed** (#68, CLOSED on the build scope): crossings are built, activated (§9.77) and derived (§9.90), and `_crossings_report.json` with `closure_source` `schedule_derived` is the evidence that closed it. Its last comment predates §9.90.
- **The base scenario's priority state is not settled by the record.** `A.lightrail.tsp_enabled` (false in S2) and `A.signals.scats_phasing` (`proxy_no_priority` in S2) are unbound fields under `scats_adaptive`; the emitted S2 and S2b signal files are byte-identical and both configs carry `tramPriority.mode=green_extension`. The S2 probe of §9.88 ran with `mode=off`, but `results/aborted_20260830T083019_1000it_25pct` (S2) logs priority on. Whether S2 grants tram priority must be decided and declared before any S2-versus-S2b comparison.
- Offsets remain a stated limitation with no derivation path short of the library itself (§9.88).
- Charging dwell field measurement stays the second data priority of §13; `A.signals.delay_per_intersection_s` 26 [15–40] now serves only the `implicit_delay` arm (§9.76).
- Comparability: every signal or crossing change is a family boundary; F12 opened at §9.88 and nothing before it compares to anything after (`cities/newcastle/docs/run_families.json`).
- **The corridor's plans are two-stage with the tram first, so the donor defect never fired there** (§9.141); it would have on any three-stage plan, on the S3 corridor group or on a movement-level refinement. The corridor pedestrian-phase flag now reaches the layer: 1 of 14 intersections carries it (`_corridor_report.json`, #120 closed). **The two signal probes could not run at HEAD** — the config modules' consistency checks refused a toy config that declared no reach bound, regime or taxi representation — and run again (§9.141).

## Refused — do not re-raise

- Obtaining SCATS phasing from TfNSW: refused by policy, April–July 2025, and citable as a finding (§9.21). The purchase route and the TIA route stay parked on #78; TIA content never enters a CC-BY artefact or sets a registry value (`cities/newcastle/docs/archived/design/signalling/tia-harvest-log.md`).
- Inventing an offset library or any corridor coordination pattern (§9.88).
- Re-deriving the S0 counterfactual from the 2018 install dates: decided no on 12 August 2026; the pre-light-rail corridor keeps all 14 signals (§9.24).
- Movement-level lanes from 16% turn-lane coverage (§9.76).
- Sweeping a join tolerance whose output cannot vary across it (§9.24).
- Adding coal trains to the passenger network (§9.70), or treating Stewart Avenue as a boom-gate closure (§9.75).
- Modelling signals in SUMO: descoped, MATSim is the single simulator (§9.74).

## History

- §9.141 — priority donor by layout; probes run
- §9.90 — crossings derived from rail timetable
- §9.88 — SCATS algorithm implemented, F12 opens
- §9.78 — planning-portal TIA sweep empty
- §9.77 — signals and crossings activated, F6
- §9.76 — signals, crossings, dwell built inert
- §9.75 — dossier lands, PPSHCC-137 discovered
- §9.74 — SUMO descoped, MATSim only
- §9.70 — coal chain excluded, crossings named
- §9.24 — SCATS site ids and install dates
- §9.21 — phasing refusal becomes citable
- §5 — the original assumed SCATS proxy
