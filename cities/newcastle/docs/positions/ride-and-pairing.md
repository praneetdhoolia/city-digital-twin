# Ride and pairing — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has passed its gate.*

**Updated:** 5 September 2026 (twenty-eighth session) · **Record read through:** §9.143 · **Open family:** F25 (read at its iteration-100 gate)

## What is built

**Demand — four binder passes in `src/build/build_activity_chains.py`, each naming the driver.**

- Escort: an HX tour binds to the household member it escorts, at that person's own school and own hour (§9.46); an unbound HX tour is re-targeted to a passenger in a driverless household within `B.activity.escort_binding_nonhh_scope` = `same_zone`, with the serving leg re-timed to the passenger's departure (§9.60).
- Joint tour: a household companion's HS/HO tour becomes a mirror of a licensed co-member's drive, `party_size` 2, the driver tour shifted into the vacated slot where needed (§9.84); companions whose household holds no other eligible driver are excluded before thinning, so binding is supply-limited (`p_thin` 1.0000 on WEEKDAY) rather than thinned (§9.116).
- Shared ride (`bind_shared_rides`): a car-less core person's direct non-escort tour binds, both directions, to a licensed car-available driver in another household making the same SA2-to-SA2 trip within `B.ride.pairing_window_min`; nearest departure wins (§9.124). `B.ride.shared_lift_scope` = `same_sa2_od` (swept `same_sa1_od`, `none`) (§9.124).
- A shared pair must share a sampling-hash bucket of `B.ride.shared_lift_hash_bucket` = 0.05, so any nested sample at a multiple of that width keeps both members (§9.129); this supersedes the at-or-below rule of §9.127, which kept pairs together but biased the sample's composition.
- Volume: (occupancy − 1) × driver share × core trips = 448,229 passenger trips on WEEKDAY; escort and lift bindings count first, joint next, shared rides fill the remainder and are thinned to it (§9.84, §9.124). `B.activity.joint_tour_passenger_ratio` = 0.3503 is derived from `C.constraint.vehicle_occupancy` = 1.3503 (HTS 2024/25; sweep 1.2493–1.3940) (§9.8, §9.84).
- Translation (`src/build/build_matsim_plans.py`): the passenger carries `boundDriver`, `liftHousehold`, `sharedDriverHousehold` and per-trip `boundRideTrips`; the driver carries `boundDriveTrips` (§9.85, §9.120, §9.127). `GatedSubtourModeChoice` refuses `ride` on a trip nobody drives and refuses taking a declared driver off `car` on a serving trip (§9.120).
- Seed: `B.mode.seed_method` = `full_choice_set` gives every person one plan per usable mode and a declared passenger one further plan riding the bound trips; `RUN.replanning.max_agent_plan_memory` = 8 (§9.120).
- A seeded plan carries PER-TRIP modes, not one mode per tour (§9.143). A tour bound in ONE direction only — a drop-off binds its first trip, a pick-up its last (§9.120) — now rides on the covered leg and takes `B.mode.partial_bind_base` = `pt` (sweep `pt`/`walk`/`taxi`) on the other, so the whole subtour is non-chain and the chain/non-chain mix `ChooseRandomLegModeForSubtour` refuses (§9.119) is unreachable rather than repaired afterwards. A car-less person folds the override onto their existing walk-based variant and spends no plan slot; plan memory peaks at 7 of 8 (§9.143).

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

- **THE DEMAND WAS NOT THE CAUSE — F25 falsifies it** (§9.143, #86). The F25 arm `aborted_20260905T125612_300it_25pct`, stopped by its own watcher at the iteration-100 gate: **ride −43.1 %**, against F24's −42.5 % at milestone 90. Three repairs made 60,273 partially bound trips seedable, freed 33,832 escort-day trips and removed 17,740 impossible bookings, raising the SEEDED ride share 0.0338 → 0.0444, and the REALISED share did not move. Being in plan memory is necessary and **not sufficient**: the ceiling is downstream of the choice set, and the whole demand-side class of explanation is closed. This was named in the run overlay before the arm as the outcome to look for, so it is a pre-registered answer.
- **Where it is lost instead: pairing at execution, and selection.** From the arm's own `ride_pairing.csv`: selected ride legs rose 25,362 (it 0) → 74,115 (it 50) → **77,214 (it 100)**, so the repairs did put the alternative in front of co-evolution; but the pair rate FELL 0.9817 → 0.8256 → **0.7827**, so **21.7 % of selected ride legs never pair** and execute as a drive or walk, which the trips table then counts as car or walk. The dominant miss is the TIME window and it grows monotonically — `miss_window` 1 → 5,339 → **7,921** — while `miss_endpoints` (5,237) and `miss_capacity` (2,012) stay smaller; the median gap closes 301.8 → 73.4 → **50.0 min**. `occupancy_from_pairings` reads **0.1642** against the measured 0.3503. Indicatively, and crossing two bases so it is an indication only: if every selected leg paired, ride would sit near 15 % rather than 11.7 %, so execution accounts for roughly 3 pp of the 8.9 pp gap and the remaining ~6 pp is ride not being SELECTED — a scoring question, and the next lane.

- F22 arm `aborted_20260831T165127_300it_25pct`, the iteration-100 gate: ride 12.10% against 20.60% (−41.3%), plateaued at 12.0–12.5% from iteration 30 — the same ~12% ceiling as F21's 12.08%, unmoved by the fare (§9.136, #86).
- F22 iteration 0, from the arm's own log (§9.136): 7,092 declared passengers picked up on 6,697 drivers' detours (mean detour 538 s), 0 unroutable, 364 unpaired legs re-moded and restored — 2.5× the F21 10% counts, exactly the fraction's scaling; pairing is healthy at 25%.
- **The generation ledger, measured on the rebuilt WEEKDAY demand** (§9.136, #86): the occupancy identity generates 448,229 passenger trips = 19.13% of 2,343,161 (`B2_activity_trips_WEEKDAY.csv`) — near the 20.6% target; the four passes bind 374,823 rows = 16.0% (escort 127,293 + shared 115,516 + joint 84,436 + lift 47,578, `B2_*_bindings_WEEKDAY.csv`); the gate realises 12.10%. ~3.1 pp is generated-but-unbindable (no driver exists, §9.109's class); ~3.9 pp is bound-but-not-realised — the choice-side gap a deeper arm must decompose.
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

- #48 — every ride physically in a car. The physical channel works at 25%: 7,092 picked up, 0 unroutable at F22 iteration 0 (§9.136).
- **#86 — the binder volume is at target and the loss is downstream of it** (§9.142). The four passes bind **447,797 trip-equivalents, 20.13 % of core trips**, against the identity's 447,711 and an observed 20.6 %, so a fifth pass would add volume that is already there.
- **The partially bound tour is REPAIRED** (§9.143, #86): **50,665 WEEKDAY bound trips (2.16 % of core trips) across 49,514 persons** now become a `ride` alternative that plan memory can hold at all, where before co-evolution was never offered them. Seed ride share 0.0338 → 0.0390; 42,920 new plans, all car-available (SAT 31,793 trips, SUN 24,626). **§9.142 under-counted this class**: it attributed all of it to the chain-mix cause at 42,019 — which matches the car-available count of 42,920 — and missed **7,745 car-LESS partial tours** excluded by the same `all(...)` test for no chain reason at all, whose walk-based variant could always have carried the ride. Verified on the built population: 0 ride legs off a declared bound trip, 0 chain/non-chain tour mixes, 0 persons over the plan cap.
- **A bound trip on a person denied `ride` outright is still unreachable, and the escort class is not small** (§9.143, #86). Measured for the first time on WEEKDAY: **33,832 bound trips across 18,403 persons** are lost to `B.activity.escort_excludes_ride`, and 4,480 across 3,419 to the vehicle-less `ride_avail` identity. The escort figure is 1.44 % of core trips — two thirds the size of the class just repaired and 7.5× the vehicle-less one §9.142 named — against a derivation that calls the collateral "stated, small and plausibly the truth". The identity is sound (an escorter is driving); the SCOPE is per-DAY, so a parent who drives a child to school cannot be a passenger afterwards. The derivation chose per-day because `PermissibleModesCalculator` is per-plan — a constraint `GatedSubtourModeChoice` no longer imposes, since it gates `ride` per trip. **Measured, not changed: a decision, not a defect.**
- #91 is closed (§9.140): the no-declared-driver class is zero at the seed since §9.120; F20's iteration-0 pair rate 0.977 and F22's 7,092 pickups with 0 unroutable are its evidence.
- The 25% × 300 costing: ~25 h stated at the F22 approval; the arm measured 630–670 s/it late pace, ~45–50 h for a full 300 (§9.136) — cost the next 25% arm on the measured pace.
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

- §9.143 — plan memory repaired and the demand cause FALSIFIED; the loss is in pairing and selection
- §9.142 — the binders reach target; the loss is in plan memory
- §9.140 — #91 closed; ride survives memory
- §9.136 — ceiling decomposed: 19/16/12
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
