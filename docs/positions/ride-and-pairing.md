# Ride and pairing — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 17 September 2026 (fifty-fourth session) · **Record read through:** §9.177 · **Written against family:** `F35`

## What is built

- **The engine routes the trip it re-modes and restores the original; the clock override is restored after the mobsim** (§9.168, §9.167, #167, #187): a ride trip under `accessEgressModeToLink` is five legs, replaced whole; `RidePairingEngine.routeRemodes` routes every unpaired leg's trip in its fallback mode on `global.numberOfThreads` workers (**644 in 0.9 s**, `20260912T185005_4it_25pct`), the restore putting the ride trip back (`RemodeRestore.Remode`); a driver's end-time override is restored at AfterMobsim.
- **The routing workers write no plan** (§9.170, #197): `routeDetour` returns a `Detour` applied by the main thread in driver order; the 1 % smoke `20260914T150700_2it_1pct` ran 2 of 2 on the recompiled controler (0 detours refused).

**Demand — four binder passes in `src/build/build_activity_chains.py`, each naming the driver.**

- Escort: an HX tour binds to the household member it escorts at that person's own school and hour (§9.46); an unbound HX tour is re-targeted to a driverless-household passenger within `B.activity.escort_binding_nonhh_scope` = `same_zone` (§9.60). **All four passes test one driver identity: a licence AND a household vehicle** (§9.144, #142); the HX TOUR is not gated.
- Joint tour: a household companion's HS/HO tour mirrors a licensed co-member's drive, `party_size` 2 (§9.84); companions with no other eligible driver are excluded before thinning, so binding is supply-limited (`p_thin` 1.0000 on WEEKDAY, §9.116).
- Shared ride (`bind_shared_rides`): a car-less person's direct non-escort tour binds, both directions, to a licensed car-available driver in another household on the same SA2-to-SA2 trip within `B.ride.pairing_window_min`, nearest departure wins; `B.ride.shared_lift_scope` = `same_sa2_od` (swept `same_sa1_od`, `none`) (§9.124); when supply exceeds the volume the pass binds the LONGEST servable tours first — `B.ride.shared_lift_priority` = `longest_first` (sweep `uniform`) — reporting the bound mean length (§9.149).
- A shared pair shares a sampling-hash bucket of `B.ride.shared_lift_hash_bucket` = **0.25** (§9.149; 0.05 the control, §9.129), so the 25 % sample keeps both members: at 0.05, **94 % of the 27,771 unserved car-less tours had a same-SA2 driver in the window and were refused on the bucket alone, at a median 9–15 km** — the observed passenger trip (#86).
- Volume: (occupancy − 1) × driver share × core trips = 448,229 WEEKDAY passenger trips; escort and lift count first, joint next, shared fills (§9.84, §9.124); `B.activity.joint_tour_passenger_ratio` = 0.3503 derives from `C.constraint.vehicle_occupancy` = 1.3503 (sweep 1.2493–1.3940) (§9.8).
- Translation (`src/build/build_matsim_plans.py`): the passenger carries `boundDriver`, `liftHousehold`, `sharedDriverHousehold` and per-trip `boundRideTrips`; the driver `boundDriveTrips` (§9.85, §9.120, §9.127). `GatedSubtourModeChoice` refuses `ride` on a trip nobody drives and refuses taking a declared driver off `car` on a serving trip (§9.120).
- Seed: `B.mode.seed_method` = `full_choice_set` gives one plan per usable mode and a declared passenger one more riding the bound trips; `RUN.replanning.max_agent_plan_memory` = 8 (§9.120). Plans carry PER-TRIP modes (§9.143): a tour bound in ONE direction rides on the covered leg and takes `B.mode.partial_bind_base` = `pt` (sweep `pt`/`walk`/`taxi`) on the other (§9.119).
- **The demand states that the passenger rides** (§9.164, #86, #48): `B.mode.bound_passenger_placement` = `every_plan` puts a round-trip-covered tour on `ride` in EVERY seeded plan, as the driver's serving tour already reads `car` (under `alternative`, 10,224 of 20,902 declared escort pairs had the passenger driving, §9.163). The seed carries ride on 14.91 % of selected-plan legs because a bound person keeps an alternative on their first base mode (`_bound_trips.json`, §9.177).
- **The partially bound tour is repaired** (§9.143, #86): 50,665 weekday bound trips on 49,514 persons become a `ride` alternative; 33,832 on 18,403 persons stay unreachable because `B.activity.*` denies them `ride` — the escort class.

**Runtime — pairing at BeforeMobsim, boarding in the qsim.**

- `RidePairingEngine` pairs each selected ride leg with a car leg at BeforeMobsim, where every plan is final, re-made every iteration (§9.44); a declared pair is accepted on identity whatever the links, the passenger's preceding activity end set to the driver's departure less the access walk (§9.120); `B.ride.bound_pairing_window_min` = 60 min, derived as 2 × `RUN.replanning.time_mutation_range_s` (1800 s), is the physical-wait bound on a booking (§9.95, §9.120).
- An inferred pair uses `B.ride.pairing_rule` = `both_links` inside `B.ride.pairing_window_min` = 15 min (sweep 5–60) (§9.81, §9.102); `route_contains` is a sweep member.
- `B.ride.declared_pair_meeting` = `driver_detour`: the driver's car leg is re-routed through each passenger's origin and destination link in departure order, written to the driver's plan and paid in the driver's score; `passenger_links` is the swept alternative (§9.128).
- `JointRideEngine` boards the passenger into the driver's real vehicle (`B.ride.physical_boarding` true) and holds a booked passenger up to the booking's tolerance (`B.ride.wait_for_driver` true) (§9.53, §9.60, §9.102). `B.ride.max_passengers_per_vehicle` = 4 refused 1 of 84,436 joint bindings on the rebuilt demand (`_activity_chains_report.json`, §9.111).
- An unpaired ride leg executes as `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (`B.ride.remode_unpaired` true) and the plan keeps `ride` at AfterMobsim (§9.55, §9.81, §9.105).
- `EscortCoherenceListener` re-offers a split pair at `B.ride.escort_coherence_rate` = 0.4 and `B.ride.joint_coherence_rate` = 0.4 (sweep 0–0.5) (§9.84), intra-household (§9.145), DECLARED pairs only under `B.ride.coherence_scope` = `declared` (sweep `inferred`) (§9.146); past the innovation cutoff it proposes nothing (§9.158); its seeded draw iterates a `TreeMap` in household-id order (§9.151, #150).
- A household drives the cars the census gives it: `B.population.vehicle_roster` = `census` maps every driver to a shared `hh<id>_car<k>`, and `HouseholdCarDepartureHandler` holds a driver whose car is out — car-only, because `RUN.qsim.vehicle_behavior` is global (§9.146, §9.148, #145; [population-and-demand](population-and-demand.md)).
- `ride_pairing.csv` carries `miss_declared_absent` since §9.145 — unpaired legs naming a declared driver who brought no car leg — appended last so no earlier column shifts meaning.
- **The calibration loop reaches ride's parameters** (§9.158): the movable set (5 → 21) includes `B.ride.pairing_window_min`, `B.ride.escort_coherence_rate`, `B.ride.joint_coherence_rate`, `B.ride.max_passengers_per_vehicle`, `B.ride.pickup_dwell_s`; `B.ride.shared_lift_hash_bucket` stays excluded, needing B2, the plans and the run inputs rebuilt.

## What is measured

- **Arm 0 pairs 99.6 % of its ride legs, and ride still reads −41.6 %** (§9.169, `20260912T202242_300it_25pct`, `output/ride_pairing.csv` at it.300): **64,578** ride legs, **64,303** paired (**0.9957**), **275** unpaired, every one `miss_declared_absent`; miss_capacity **0**. Car legs **390,968** against 242,016 at it.0 while ride legs fell from 82,662, so `occupancy_from_pairings` reads **0.1645** and the fit's occupancy **0.1871** against 0.3503 is OUTSIDE [0.2493, 0.394].
- **The engine on the same arm** (§9.169, `matsim.log`): **31,174** declared passengers picked up on **29,287** drivers' detours, mean detour **6 s**, **0** refused; **18,767** drivers waited for a household car (#145). #187's `restoreRetimed` counter is not in the log — UNMEASURED.
- **The scoreboard reads ride −41.6 %** (§9.169): **12.0233 %** of resident linked trips against 20.60, at a **10.09 km** mean (+3 % on the HTS passenger trip); coverage **19.11 %** from it.27, fixed at the seed; #48 met on the pairing.
- **Coverage is a share of TRIPS, so ride's 19.11 % IS the bound trips' share, sitting at the target** (§9.177, correcting §9.163's and §9.169's "share of agents"): the binders bind **458,886** distinct (person, tour, direction) trips, **20.62 %** of core legs — the observed passenger share (`python src/analyse/measure_bound_trips.py`); a constant can add nothing past it, and the deficit is what bound trips execute as.
- **Where the bound trips go** (§9.177, `20260915T000704_250it_25pct` at it.250, `_bound_trips.json`, #86 #145): of **109,816** bound trips in sample **59.0 %** rode, **22.6 %** drove, **10.7 %** walked, **4.6 %** cycled; car-available escort members drove themselves on **50.7 %** of their bound trips (22,575), joint companions **36.3 %** (25,069), lift passengers **65.5 %** (6,469); car-less passengers rode **73–82 %** and walked or cycled **18–27 %**.
- **The scoring pair reads the same within a point** (`20260916T063903_250it_25pct`, its `_bound_trips.json`, §9.177): 59.3 % rode; escort|always car 50.4 %, joint|always 35.8 %, lift|always 66.8 %.
- **Ride's choice set closes first** (§9.163, #86, #48): on `20260909T015217_300it_25pct` coverage was within one point of final by iteration **5**, last moving at **17**; ride sat at **12.1553 %**. (§9.163 read the 20.05 % as agents; it is trips, §9.177.)
- **In half of all declared escort pairs the passenger drives themselves** (§9.163, `measure_realisation_gap.py`): of **20,902** bound pairs with both members in sample, co-assigned car + ride **7,821 (37.4 %)**, not co-assigned **12,989 (62.1 %)**, of which the passenger drives their **own car 10,224 (48.9 %)**; both tours realised in **20,810 (99.6 %)**, endpoints and window ample. The loss is the passenger's mode assignment; `occupancy_from_pairings` **0.186** against 0.3503.
- **What the rebuilt seed carries** (§9.164, `_plans_report.json` `bound_placement`): WEEKDAY **194,131** fully and **59,705** partially bound tours over **199,329** persons; the seeded weekday ride share **0.1114** of legs equals `seed_ride_covered_share`, so every seeded ride leg is a declared binding; **268,306** duplicate plans folded rather than seeded.

## What is open

- **#86 — the root is the alternative plan a held passenger keeps, and D12 is the fix, NOT yet built** (§9.177, the lane): escort members and joint companions ride their bound tours in EVERY plan (a tour that exists because they are escorted, or as a joint activity, has no solo-car alternative), the gate refuses car on those trips (`heldRideTrips`); car-less lift and shared passengers keep walk/bike/pt against the wait. It rebuilds the demand and opens a family, after the scoring pair's reading; its arithmetic bound is the 20.62 % the binders bind.
- #187 — the `restoreRetimed` counter is not in arm 0's log under that name; the re-time restore count is unmeasured until it is (§9.169).
- **`C.asc.car_passenger` STAYS FROZEN** (§9.158): ride's deficit is VOLUME, not utility — on arm 0 the trip is 10.09 km (+3 %) at −41.6 % (§9.169); the constant is already CONSTRAINED by §9.8 to the observed 0.3503 ride:car ratio, and `src/calibrate/asc_fixed_point.py` refuses it.
- Whether a suburb is the right carpool precision is the sweep's question (§9.124); where the car-less quarter's excess settles once a fifth of their tours ride (§9.123, §9.126).

## Refused — do not re-raise

- Relaxing `B.ride.pairing_rule` to `origin_link`, `dest_link` or `window_only`: pairs passengers with drivers going elsewhere (§9.81, §9.102, §9.109).
- Widening either pairing window: residual gaps of median 344 min are different trips (§9.98); a declared pair faces no clock, so `miss_window`'s growth is not evidence about the tolerance (§9.145).
- Solving `asc_car_passenger` to close the ride gap: ASC absorption (§9.8, §9.11).
- Raising `B.activity.joint_tour_passenger_ratio`: derived from measured occupancy (§9.109).
- A directed closure pulling driver households into the sample: a 10% draw at 17.65% of persons (§9.127).
- A walking meeting point for declared pairs (§9.128).
- socnetsim joint plans: ~10× runtime (§9.44, #48).
- Re-moding an unpaired leg by mutating the plan: a one-way ratchet (§9.81).
- Reading pairing or ride share off a 1% smoke: the flow-capacity artefact and broken pairs (§9.128, §9.129).

## History

- §9.177 — coverage is trips; bound trips read
- §9.170 — engine workers return detours
- §9.169 — arm 0: pairing holds; seed caps ride
- §9.168 — unpaired walk routed by the engine
- §9.167 — whole-trip re-mode
- §9.166 — trim() through the declared selector
- §9.164 — declared passenger put on ride
- §9.163 — target above choice set
- §9.162 — first result: ride converged
- §9.160 — ride CONVERGED; it is supply
- §9.158 — listener stops past the cutoff
- §9.157 — F31 gate: gap is volume
- §9.156 — deficit is the small modes' excess
- §9.153 — F30 it.0: 8,167 paired
- §9.151 — listener draws in household order
