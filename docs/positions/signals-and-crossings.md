# Signals, SCATS and level crossings — current position

Living documents that still say "SCATS phasing is unobtained and handled by sweep" (the S2b overlay description and the `A.signals.tsp.mode` description) describe the pre-§9.88 state; §9.88 wins: the operated plans and the offset library are unobtained; the control logic that produces cycle and splits is implemented and live.
*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 16 September 2026 (fifty-third session) · **Record read through:** §9.176 · **Written against family:** `F35`

## What is built

- **The crossings and the corridor signals are re-derived on the footpath network** (§9.167, #183, #184): 16 rail links at the two sites, 2,478 change events, Clyde Street 203 scheduled closures (204 on the previous mapping, §3.5) plus 48 freight, Saint James Road 110 plus 44, at 160 s passenger / 277 s freight. The builder reads the MAPPED schedule's weekday routes (`networks/matsim/schedules/`), not the run-input set. The signal systems match 54 signalised approaches (49 before).
- **SCATS is implemented, not assumed.** `A.signals.control_regime` = `scats_adaptive`; all 14 corridor systems name `CitysimScats` (`src/java_signals/citysim/ScatsSignalController.java`) and every config carries the `scats` module (§9.88). Degree of saturation is measured at each stop line from `LinkLeaveEvent`s against saturation flow × lanes × green, scaled by `qsim.flowCapacityFactor`; at each cycle boundary the cycle steps toward the target on the critical movement and green is re-split to equalise DS; clearances are safety geometry (§9.88).
- Algorithm parameters in the `scats` module: `A.signals.scats.target_degree_saturation` 0.90, `cycle_step_s` 6, `min_cycle_s` 30, `max_cycle_s` 150, `ds_deadband` 0.05, `ds_smoothing` 0.5, `A.signals.min_green_s` 6 (§9.88). `fixed_time` is the kept sweep member; `run_matsim.py` refuses a regime that disagrees with the committed control file (§9.88).
- The 14 intersections (`A.signals.n_corridor_intersections`, observed) are explicit MATSim signal systems generated per scenario by `cities/newcastle/build/build_matsim_signals.py` into `cities/newcastle/networks/matsim/signals/<S>/` (§9.76); phases are link-level, with a tram group tied to the corridor phase; a site with no cross-street car approach is a mid-block crossing signal (§9.76).
- `A.signals.representation` = `explicit_signals`: every run-input set carries the `signalsystems` module, `qsim.usingFastCapacityUpdate=false`, re-capacitation to `A.signals.saturation_flow_veh_h_lane` 1900 × lanes (`signals_capacity_patch.csv`), and `transitSchedule_signals.xml.gz`, which removes each variant's embedded per-intersection tram delay (§9.77).
- Transit priority lives inside the SCATS controller (`tramPriority`): `A.signals.tsp.mode` `green_extension`, `extension_window_s` 12, `detection_distance_m` 120, `priority_budget_share` 0.2, `compensation_enabled` true, `lateness_threshold_s` 60, `priority_group` `tram` (`corridor` in S3) (§9.77, §9.88). Compensation is intrinsic through the next split (§9.88).
- **Which stage donates is decided by the layout** (§9.141, #125): an extension borrows from a stage AFTER the tram's, a recall truncates the stage before it, a tram stage last in its cycle is refused and counted. `citysim.ScatsPriorityProbe`: extension moves the drop 58 → 68 s, recall pulls the onset 30 → 20 s (§9.141). The corridor's plans are two-stage with the tram first, so the donor defect never fired there.
- Level crossings: `A.crossings.representation` = `change_events`; `cities/newcastle/networks/matsim/crossings/crossing_change_events.xml` enters every config as a time-variant network with `RUN.travel_time.bin_size_s` 300 (§9.77).
- `A.crossings.closure_source` = `schedule_derived`: `build_level_crossings.py` locates the two boom-gated crossings from OSM `railway=level_crossing` nodes on `A.crossings.freight_road_names`, finds rail links within `A.crossings.rail_match_radius_m` 40, and closes the road for every scheduled traversal for `A.crossings.closure_duration_passenger_s` 160 s (§9.167; §9.90 had 60 s) plus `A.crossings.freight_closures_per_day` movements at 277 s. It refuses a crossing with no link or movement and any closure within `A.crossings.corridor_exclusion_m` 500 of a corridor intersection (§9.75, §9.76).
- Charging dwell is native in the mapped schedule: `departureOffset = arrivalOffset + max(existing gap, resolved dwell)` (§9.76). `A.lightrail.dwell_charging_s` stays `unobtained`, swept 10–35 s; S2/S2b/S2c select 20 s, S2a 0 s (§9.76).
- Corridor signal identity: `scats_site_id` filled for all 14 from TfNSW's Traffic Lights Location inventory, mean match 8.0 m, max 26.4 m; `A.signals.scats_match_radius_m` 60 is a join tolerance, held fixed; eight were installed in 2018 for the light rail, an attribute only (§9.24).

## What is derived, and what is still unobtained

| Quantity | Position |
|---|---|
| Cycle length at each of the 14 sites | **Derived at run time** from measured DS, bounded by `min_cycle_s`/`max_cycle_s` and clearances plus minimum greens (§9.88) |
| Splits | **Derived at run time**, DS-equalised every cycle (§9.88) |
| Degree of saturation | **Measured in the mobsim** (§9.88) |
| Transit priority | **Implemented** — green extension within a budget share; `extension_recall` and `conditional` swept. Which mechanism TfNSW operates is a documented gap (dossier `02-newcastle-signalling.md`) |
| The starting plan (110 s, split 45/15/30/10) | **Assumed** A2 proxy, the starting point only; under `fixed_time` the whole plan (§5, §9.88) |
| Offsets and corridor coordination | **Not adapted, deliberately**: SCATS selects offsets from an operator-tuned library that is the unreleased artefact; each system keeps its generated offset (§9.88) |
| The operated phase plans for the 14 sites | **Unobtained**: `A.signals.scats_phasing` null, refused by TfNSW policy (§9.21); its sweep reaches no emitted parameter under `scats_adaptive` |
| Saturation flow | Literature 1900 veh/h/lane, swept 1800–2050; no Newcastle stop-line survey (§9.76) |
| Movement-level lanes and protected turns | **Data-gated**: turn-lane coverage 46 of 280 corridor trunk edges (16 %) (§9.76, #73) |
| Crossing closure count and timing | **Derived** from the already-mapped rail timetable, never from a re-run of the mapper (§9.90) |
| Freight closures | **Derived** from the Cobbora Coal Project EA's March 2012 five-day survey: `A.crossings.freight_closures_per_day` 44 (Saint James Road) and 48 (Clyde Street), 405 movements a weekday with the 313 scheduled (§9.167, #184); the coal chain stays off the network (§9.70) |
| Offset between a train's nearest stop and the crossing | Not modelled; under a minute at both sites (§9.90) |
| Charging dwell | **Unobtained**, swept, selected per scenario (§9.76) |

## What is measured

- Two defects the build surfaced and fixed: DS read 0.000 at a 1 % sample until the denominator carried `flowCapacityFactor`; modular cycle arithmetic cannot survive a variable cycle, so the controller keeps an explicit cycle start (§9.88).
- Crossings: Saint James Road 110 scheduled closures per weekday and Clyde Street 203 (204 on the previous mapping, §3.5), against 30 assumed at both, plus 44 and 48 derived freight movements; 2,478 change events (§9.90, §9.167). Mode 12 `freight_train` carries a derived target of 405 movements per weekday in `mode_targets_by_mode.csv` (§9.167).
- **Arm 0 loaded the closures, and the reader reads them like-for-like** (§9.169, `20260912T202242_300it_25pct`): the run's `crossing_change_events.xml` carried 266 merged closure spans (112 Saint James Road + 154 Clyde Street) for the 405 movements, and the `freight_train` row reads **405 against 405** - the reader now adds the freight closures the run's own `_config.json` carried to the scheduled 313, where it had read 313 against 405 on every run (ninth report finding 4).
- Operated evidence, archived and not an input: TIA PPSHCC-137 (`cities/newcastle/data/raw/planning_tia/PPSHCC-137_643_hunter_st_tia.pdf`) republishes SCATS history for TCS 1138 Hunter/Steel at 72–81 s and TCS 923 King/Steel at 104–113 s on 19 July 2022; neither is a modelled site, so it is a prior on the sweep (§9.75). The portal sweep — 19 applications, 13 documents — found nothing further (§9.78).
- No arm-scale signal or crossing EFFECT is measured yet. A 1 % probe verifies plumbing only, at about 0.3 vehicles per green; the per-green discharge at 25 % reads 7.1–7.9 on the worst approach (§9.76). Every arm since F12 runs SCATS and the derived closures; both results (§9.162, §9.169) carry both ON, and no paired arm has carried either off.

## What is open

- **Freight trains at the two crossings are derived from a 2012 survey, not counted at the gates** (#184, §9.167): `A.crossings.freight_closures_per_day` = 44 / 48 rest on the Cobbora EA's survey, Clyde Street's freight share a stated assumption; the Newcastle Herald report of 10 June 2026 is consistent. An ARTC train plan, the Lower Hunter Freight Corridor business case or a gate count would replace the derivation and open a family.
- **The signal-effect measurement at arm scale is still owed** (#73, CLOSED on the build scope): what remains is a paired reading, and neither result (§9.162, §9.169) is one. Movement-level lanes stay data-gated at 16 % coverage (§9.76). The SCATS build is not yet recorded on the issue.
- **The closure-effect measurement on a converged arm is still owed** (#68, CLOSED on the build scope); `_crossings_report.json` with `closure_source` `schedule_derived` is the evidence that closed it (§9.90).
- **The base scenario's priority state is not settled by the record**: `A.lightrail.tsp_enabled` (false in S2) and `A.signals.scats_phasing` (`proxy_no_priority` in S2) are unbound under `scats_adaptive`; the emitted S2 and S2b signal files are byte-identical and both carry `tramPriority.mode=green_extension`. The S2 probe of §9.88 ran `mode=off`, but `results/aborted_20260830T083019_1000it_25pct` (S2) logs priority on. Decide and declare before any S2-versus-S2b comparison.
- Offsets remain a stated limitation with no derivation path short of the library itself (§9.88).
- Charging dwell field measurement stays the second data priority of §13; `A.signals.delay_per_intersection_s` 26 [15–40] serves only the `implicit_delay` arm (§9.76).

## Refused — do not re-raise

- Obtaining SCATS phasing from TfNSW: refused by policy, April–July 2025, citable as a finding (§9.21). The purchase and TIA routes stay parked on #78; TIA content never enters a CC-BY artefact or sets a registry value (`cities/newcastle/docs/archived/design/signalling/tia-harvest-log.md`).
- Inventing an offset library or any corridor coordination pattern (§9.88).
- Re-deriving the S0 counterfactual from the 2018 install dates: decided no on 12 August 2026; the pre-light-rail corridor keeps all 14 signals (§9.24).
- Movement-level lanes from 16 % turn-lane coverage (§9.76).
- Sweeping a join tolerance whose output cannot vary across it (§9.24).
- Adding coal trains to the passenger network (§9.70), or treating Stewart Avenue as a boom-gate closure (§9.75).
- Modelling signals in SUMO: descoped, MATSim is the single simulator (§9.74).

## History

- §9.176 — intro fixed: which runs are results is the board's
- §9.170 — the tenth report; no change to signals or crossings
- §9.169 — arm 0 loaded 405; reader like-for-like
- §9.167 — crossings and signals re-derived; freight closures from the survey
- §9.166 — re-read against F33; freight trains at the crossings (#184)
- §9.141 — priority donor by layout; probes run
- §9.90 — crossings derived from rail timetable
- §9.88 — SCATS algorithm implemented, F12 opens; 1 % probes re-time
- §9.78 — planning-portal TIA sweep empty
- §9.77 — signals and crossings activated, F6
- §9.76 — signals, crossings, dwell built inert
- §9.75 — dossier lands, PPSHCC-137 discovered
- §9.74 — SUMO descoped, MATSim only
- §9.70 — coal chain excluded, crossings named
- §9.24 — SCATS site ids and install dates
