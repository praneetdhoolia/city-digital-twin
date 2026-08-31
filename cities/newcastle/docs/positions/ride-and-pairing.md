# Ride and pairing — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 31 August 2026 · **Record read through:** §9.134 · **Open family:** F21

## What is built

**Demand — four binder passes in `src/build/build_activity_chains.py`, each naming the driver.**

- Escort: an HX tour binds to the household member it escorts, at that person's own school and own hour (§9.46); an unbound HX tour is re-targeted to a passenger in a driverless household within `B.activity.escort_binding_nonhh_scope` = `same_zone`, with the serving leg re-timed to the passenger's departure (§9.60).
- Joint tour: a household companion's HS/HO tour becomes a mirror of a licensed co-member's drive, `party_size` 2, the driver tour shifted into the vacated slot where needed (§9.84); companions whose household holds no other eligible driver are excluded before thinning, so binding is supply-limited (`p_thin` 1.0000 on WEEKDAY) rather than thinned (§9.116).
- Shared ride (`bind_shared_rides`): a car-less core person's direct non-escort tour binds, both directions, to a licensed car-available driver in another household making the same SA2-to-SA2 trip within `B.ride.pairing_window_min`; nearest departure wins (§9.124). `B.ride.shared_lift_scope` = `same_sa2_od` (swept `same_sa1_od`, `none`) (§9.124).
- A shared pair must share a sampling-hash bucket of `B.ride.shared_lift_hash_bucket` = 0.05, so any nested sample at a multiple of that width keeps both members (§9.129); this supersedes the at-or-below rule of §9.127, which kept pairs together but biased the sample's composition.
- Volume: (occupancy − 1) × driver share × core trips = 448,229 passenger trips on WEEKDAY; escort and lift bindings count first, joint next, shared rides fill the remainder and are thinned to it (§9.84, §9.124). `B.activity.joint_tour_passenger_ratio` = 0.3503 is derived from `C.constraint.vehicle_occupancy` = 1.3503 (HTS 2024/25; sweep 1.2493–1.3940) (§9.8, §9.84).
- Translation (`src/build/build_matsim_plans.py`): the passenger carries `boundDriver`, `liftHousehold`, `sharedDriverHousehold` and per-trip `boundRideTrips`; the driver carries `boundDriveTrips` (§9.85, §9.120, §9.127). `GatedSubtourModeChoice` refuses `ride` on a trip nobody drives and refuses taking a declared driver off `car` on a serving trip (§9.120).
- Seed: `B.mode.seed_method` = `full_choice_set` gives every person one plan per usable mode and a declared passenger one further plan riding the bound trips; `RUN.replanning.max_agent_plan_memory` = 8 (§9.120).

**Runtime — pairing at BeforeMobsim, boarding in the qsim.**

- `RidePairingEngine` pairs each selected ride leg with a car leg at BeforeMobsim, where every plan is final — the timetable analogy — and re-makes the pairing every iteration (§9.44).
- A declared pair is accepted on identity whatever the links; the passenger's preceding activity end is set to the driver's departure less the planned access walk, so the plan converges on the driver's clock (§9.120). `B.ride.bound_pairing_window_min` = 60 min, derived as 2 × `RUN.replanning.time_mutation_range_s` (1800 s), is now only the physical-wait bound on a declared booking (§9.95 derived it as the identification tolerance; §9.120 is newer and re-purposes it).
- An inferred pair uses `B.ride.pairing_rule` = `both_links` inside `B.ride.pairing_window_min` = 15 min (sweep 5–60) (§9.81, §9.102); `route_contains` is implemented and a sweep member (§9.102).
- `B.ride.declared_pair_meeting` = `driver_detour`: once a driver's passengers are known, the driver's car leg is re-routed through each passenger's origin link and then each destination link, in departure order, with the run's own router; the detour is written to the driver's plan and paid in the driver's score; `passenger_links` is the swept alternative (§9.128).
- `JointRideEngine` boards the passenger into the driver's real vehicle (`B.ride.physical_boarding` true), alights them mid-route at their destination link, and holds a booked passenger at their link up to the booking's tolerance (`B.ride.wait_for_driver` true) (§9.53, §9.60, §9.102). `B.ride.max_passengers_per_vehicle` = 4 refused 2 of 73,258 joint bindings (§9.111).
- An unpaired ride leg executes this iteration as `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (`B.ride.remode_unpaired` true) and the plan keeps `ride` at AfterMobsim — an execution, not a deletion (§9.55, §9.81, §9.105).
- `EscortCoherenceListener` re-offers a split pair at `B.ride.escort_coherence_rate` = 0.4 and `B.ride.joint_coherence_rate` = 0.4 (sweep 0–0.5; zero recovers escort-only) (§9.84).

## What is measured

Every arm below was stopped at or before its gate; levels are readings, not results.

- F21 arm `aborted_20260830T222642_300it_10pct`, the iteration-100 gate: ride 12.08% against 20.60% (−41.3%), plateaued at 12.0–12.3% from iteration 30 — the bound demand realised its ~12% ceiling and no more (§9.134, #86).
- F20 arm `aborted_20260830T184955_300it_10pct`, iteration 10: ride 9.22% against the 20.60% target (−55.2%); 41,194 bound ride trips in the 10% plans (`NEXT_AGENT_BRIEF.md`).
- F20 iteration 0: 8,068 of 8,256 ride legs paired (0.977), 2,864 passengers on 2,683 detours, none unroutable, 23,040 named drivers (`NEXT_AGENT_BRIEF.md`).
- F19 arm `aborted_20260830T170743_300it_10pct`: iteration 0 paired 6,850 of 6,966 ride legs, endpoint refusals 2,053 → 67, 2,005 passengers on 1,888 detours; iteration 20 ride 10.86% (§9.129).
- The valid F18 arm `20260830T163010_300it_10pct` under `passenger_links`: 4,858 of 6,966 paired, 2,053 refused on endpoints because two households in one SA2 do not share a link (§9.128). A walking meeting point walked 8–11 km per passenger on a 1% smoke and was dropped before any arm (§9.128).
- Shared-ride binder on the rebuilt licence-rate demand, servable / bound / shortfall: WEEKDAY 61,682 / 57,758 / 0 (§9.133; the old population read 73,509 / 59,701 / 0, §9.129). The F21 arm sampled 61,953 persons against the F20 arm's 62,134 — a different seeded draw, as §9.127 predicts (§9.134).
- F17 arm `20260830T141222_300it_10pct` iteration 50: ride 10.09%, pair rate 0.80–0.81 on identity (§9.126); car-less residents make 24.7% of trips and put 48.1% on walk, 16.7% on bike and 18.5% on ride (§9.123).
- Planned against experienced, F14 iteration 30: residents plan ride on 22.46% of trips and realise 9.14%; 36.0% of planned ride legs then named no driver, and 5,070 passengers were still waiting at 30:00 (§9.120).
- Pairing-side levers, each real and marginal: window 30 → 60 min gave +3.57 pp pairing and +0.19 pp ride (§9.98); `route_contains` gave +0.44 pp pairing and −0.22 pp ride (§9.102); residual `window_only` legs have a median gap of 344 min (§9.98).
- Demand ceiling: 42.4% of generated ride legs were unservable by the household at any hour (§9.109); 41.7% of multi-person households have at most one licensed travelling member (§9.111); the servability filter moved joint bindings 74,663 → 82,384, not the ~110,000 §9.111 estimated (§9.116).
- Escort scope is spent: 98.0% of unbound HX tours bind at `same_zone`, so driver supply, not scope, constrains (§9.84).

## What is open

- #48 — every ride physically in a car. The F21 gate read ride 12.08% (−41.3%, §9.134); the iteration-0 `ridePairing` counts on the rebuilt demand were not read before the stop — the next arm's first check.
- #86 — the demand ceiling is now measured as the cap: the F21 arm plateaued at ~12% from iteration 30 against 20.6% observed (§9.134). The binder binds 57,758 shared WEEKDAY trips with shortfall 0 (§9.133); more ride needs more bound demand, not better pairing.
- #91 — ride legs with no declared driver. The class is closed at the seed by `boundRideTrips` gating (§9.120); next: its count in `ride_pairing.csv` at F21 iteration 0.
- Confirmation-arm fraction: the bucket rule holds at 10%, 25% and 50%; a 25% × 300 arm is ~25 h and needs approval (§9.129, `NEXT_AGENT_BRIEF.md`).
- Whether a suburb is the right carpool precision is the sweep's question, with `same_sa1_od` its lower bound (§9.124).
- Where the car-less quarter's excess on walk, bike and pt settles once a fifth of their tours ride (§9.123, §9.126).

## Refused — do not re-raise

- Relaxing `B.ride.pairing_rule` to `origin_link`, `dest_link` or `window_only`: pairs passengers with drivers going elsewhere (§9.81, §9.102, §9.109).
- Widening either pairing window beyond its identity: residual gaps of median 344 min are different trips (§9.98).
- Solving `asc_car_passenger` to close the ride gap: ASC absorption (§9.8, §9.11).
- Raising `B.activity.joint_tour_passenger_ratio`: it is derived from measured occupancy (§9.109).
- Widening `B.activity.escort_binding_nonhh_scope`: at most ~2% more bindings (§9.84).
- A directed closure that pulls driver households into the sample: lands a 10% draw at 17.65% of persons (§9.127).
- A walking meeting point for declared pairs (§9.128).
- socnetsim joint plans: ~10× runtime (§9.44, #48).
- Re-moding an unpaired leg by mutating the plan: a one-way ratchet (§9.81).
- Reading pairing or ride share off a 1% smoke: the flow-capacity artefact and broken pairs (§9.128, §9.129).

## History

- §9.134 — F21 gate: ride capped at 12%
- §9.131 — licence rate measured; F21 pending
- §9.129 — bucket rule replaces at-or-below
- §9.128 — driver detour serves declared pair
- §9.127 — shared pair is sampling unit
- §9.126 — F17 realised what was bound
- §9.124 — fourth binder pass: shared rides
- §9.123 — car-less quarter wears ride deficit
- §9.120 — ride gated to bound trips
- §9.116 — servability filter; joint 82,384
- §9.111 — refusals classified: companion is driver
- §9.109 — 42% of ride demand unservable
- §9.105 — denied lift drives, not walks
- §9.102 — `route_contains` changes nothing
- §9.98 — window correction real, not bottleneck
- §9.85 — `boundDriver` survives translation
