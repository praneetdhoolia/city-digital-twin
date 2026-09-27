# Ride and pairing — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 27 September 2026 (sixty-fourth session) · **Record read through:** §9.214 · **Written against family:** `F38`

## What is built

- **The Java fold is landed** (§9.210, #187 #216 #217, D12's gate half #86): `RidePairingEngine` logs `retimed= restoreRetimed= restoreOrphan=` by name every iteration (253 of 253 restored, 0 orphans, on the F37 smoke `20260925T212929_2it_1pct`, §9.213); a timed-out joint ride is clocked by its leg's travel time, else free-flow over its links, else the beeline, never zero; one routing pool per run (`RemodeRestore.routingPool`); `GatedSubtourModeChoice` refuses a `heldRideTrips` passenger off ride. The retime and restore are shared with the taxi fleet through `citysim.ActivityRetimes` (§9.213).
- **The engine routes the trip it re-modes and restores the original; the clock override is restored after the mobsim** (§9.168, §9.167, #167, #187): a ride trip under `accessEgressModeToLink` is five legs, replaced whole; `RidePairingEngine.routeRemodes` routes every unpaired leg's trip in its fallback mode on `global.numberOfThreads` workers, the restore putting the ride trip back (`RemodeRestore.Remode`). The routing workers write no plan (§9.170, #197).
- **`EscortCoherenceListener.notifyReplanning` is split into named phases** (§9.214): 380 → 52 lines, verified identical against the old classes (`EscortCoherenceProbe`, fingerprint 56ff31af).

**Demand — four binder passes in `src/build/build_activity_chains.py`, each naming the driver.**

- Escort: an HX tour binds to the household member it escorts at that person's own school and hour (§9.46); an unbound HX tour is re-targeted to a driverless-household passenger within `B.activity.escort_binding_nonhh_scope` = `same_zone` (§9.60). **All four passes test one driver identity: a licence AND a household vehicle** (§9.144, #142); the HX TOUR is not gated.
- **A one-way escort binding survives only on a member who cannot drive** (§9.214): `B.activity.escort_oneway_scope` = `cannot_drive` (assumed; `any_member` = F37); for anyone else the binding is released and the serve tour, still placed (the observed serve-passenger rate is untouched), is labelled `escort_released` and offered to the lift pass like any unbound tour. Weekday: 50,011 drops and 12 pick-ups released; one-way tours **70,591 → 20,365**; lifts bound **44,632 → 93,318** (round trip); bound escort km 11.88 → 9.92.
- Joint tour: a household companion's HS/HO tour mirrors a licensed co-member's drive, `party_size` 2 (§9.84); companions with no other eligible driver are excluded before thinning, so binding is supply-limited (`p_thin` 1.0000 on WEEKDAY, §9.116).
- Shared ride (`bind_shared_rides`): a car-less person's direct non-escort tour binds, both directions, to a licensed car-available driver in another household on the same SA2-to-SA2 trip within `B.ride.pairing_window_min`; `B.ride.shared_lift_scope` = `same_sa2_od` (swept `same_sa1_od`, `none`) (§9.124); the LONGEST servable tours first — `B.ride.shared_lift_priority` = `longest_first` (sweep `uniform`) (§9.149).
- A shared pair shares a sampling-hash bucket of `B.ride.shared_lift_hash_bucket` = **0.25** (§9.149; 0.05 the control, §9.129), so the 25 % sample keeps both members.
- Volume: (occupancy − 1) × driver share × core trips; escort and lift count first, joint next, shared fills (§9.84, §9.124); `B.activity.joint_tour_passenger_ratio` = 0.3503 derives from `C.constraint.vehicle_occupancy` = 1.3503 (sweep 1.2493–1.3940) (§9.8).
- Translation (`src/build/build_matsim_plans.py`): the passenger carries `boundDriver`, `liftHousehold`, `sharedDriverHousehold` and per-trip `boundRideTrips`; the driver `boundDriveTrips` (§9.85, §9.120, §9.127). `GatedSubtourModeChoice` refuses `ride` on a trip nobody drives and refuses taking a declared driver off `car` on a serving trip (§9.120).
- Seed: `B.mode.seed_method` = `full_choice_set` gives one plan per usable mode and a declared passenger one more riding the bound trips; `RUN.replanning.max_agent_plan_memory` = 8 (§9.120). Plans carry PER-TRIP modes (§9.143); `B.mode.bound_passenger_placement` = `every_plan` puts a round-trip-covered tour on `ride` in EVERY seeded plan (§9.164).
- **The held passenger** (§9.211, D12, #86): an escorted member's and a joint companion's bound trips are held to `ride` in every seeded plan as `heldRideTrips`; a car-less lift or shared passenger is not held. F38's WEEKDAY seed: **232,162** held trips on **106,642** persons; 220,144 ride tours, 17,722 partial; ride on 10.43 % of selected-plan legs (`_plans_report.json` `bound_placement`, `seed_ride_covered_share`).

**Runtime — pairing at BeforeMobsim, boarding in the qsim.**

- `RidePairingEngine` pairs each selected ride leg with a car leg at BeforeMobsim, re-made every iteration (§9.44); a declared pair is accepted on identity whatever the links, the passenger's preceding activity end set to the driver's departure less the access walk (§9.120); `B.ride.bound_pairing_window_min` = 60 min, derived as 2 × `RUN.replanning.time_mutation_range_s` (§9.95, §9.120).
- An inferred pair uses `B.ride.pairing_rule` = `both_links` inside `B.ride.pairing_window_min` = 15 min (sweep 5–60) (§9.81, §9.102); `route_contains` is a sweep member.
- `B.ride.declared_pair_meeting` = `driver_detour`: the driver's car leg is re-routed through each passenger's origin and destination link in departure order, written to the driver's plan and paid in the driver's score; `passenger_links` is the swept alternative (§9.128).
- `JointRideEngine` boards the passenger into the driver's real vehicle (`B.ride.physical_boarding` true) and holds a booked passenger up to the booking's tolerance (`B.ride.wait_for_driver` true) (§9.53, §9.60, §9.102). `B.ride.max_passengers_per_vehicle` = 4 (§9.111).
- An unpaired ride leg executes as `B.ride.unpaired_fallback` = `licensed_drive_else_walk` (`B.ride.remode_unpaired` true) and the plan keeps `ride` at AfterMobsim (§9.55, §9.81, §9.105); 277 an iteration re-moded to walk on F37's arm 0 (§9.214).
- `EscortCoherenceListener` re-offers a split pair at `B.ride.escort_coherence_rate` = 0.4 and `B.ride.joint_coherence_rate` = 0.4 (sweep 0–0.5) (§9.84), intra-household (§9.145), DECLARED pairs only under `B.ride.coherence_scope` = `declared` (§9.146); past the innovation cutoff it proposes nothing (§9.158).
- A household drives the cars the census gives it: `B.population.vehicle_roster` = `census`, and `HouseholdCarDepartureHandler` holds a driver whose car is out (§9.146, §9.148, #145; [population-and-demand](population-and-demand.md)).
- **The calibration loop reaches ride's parameters** (§9.158): `B.ride.pairing_window_min`, `B.ride.escort_coherence_rate`, `B.ride.joint_coherence_rate`, `B.ride.max_passengers_per_vehicle`, `B.ride.pickup_dwell_s`; `B.ride.shared_lift_hash_bucket` stays excluded.

## What is measured

- **F37's arm 0, a RESULT at iteration 250** (§9.214, `report_mode_ridership.py --run 20260926T002526_250it_25pct --it 250`): ride **17.8204 % against 20.60 (−13.5 %)** on 26,996 trips at a **9.45 km** mean (9.8 observed); coverage **18.99 %**, headroom 1.17 pp (`report_choice_set_coverage.py`). A direction against F35's −41.6 % (§9.169), never a comparison (§3.5).
- **The bound trips are executed as bound** (§9.214, `_bound_trips.json`, #86): **106,580** bound trips in sample on 49,259 persons ride **89.17 %**; escort and joint trips, car-available or car-less, ride **100 %** (the held passenger, D12); lift passengers with a car ride 28.9 % and drive 67.1 %, car-less lift passengers ride 83.7 %; car-less shared passengers ride 80.0 %, walk 11.1 %, cycle 4.6 %.
- **A one-way escort binding strands the tour it holds** (§9.214, item 2): the F37 binder covered 70,571 weekday member tours ONE way against 24,993 round trip, 80,384 of 122,270 bindings on a licensed member's non-education trip, at a mean 11.88 network km against the survey's 7.84. The bound direction HELD to ride, the car stayed home and the tour's other trips had walk, pt, bike or taxi only: 35.6 % of walk km and 28 % of taxi trips (§9.214). §9.68 had measured the same under `outbound_only`.
- **Coverage is a share of TRIPS, so ride's coverage IS the bound trips' share** (§9.177): the binders bind about the observed passenger share of core legs; a constant can add nothing past it, and the deficit is what bound trips execute as.
- **The ride split refactor changed nothing** (§9.213): against the pre-split engine on the same inputs every iteration-0 integer counter was identical (4,247 ride legs, 3,573 paired, 674 unpaired).

## What is open

- **F38's arm 0 reads ride with the one-way escorts released into lifts** (§9.214, #86): ride against 17.82 % and coverage against 18.99 %, and what the doubled lift volume executes as (`measure_bound_trips.py`) against F37's lift rows.
- **`C.asc.car_passenger` STAYS FROZEN** (§9.158): ride's deficit is VOLUME, not utility — on F37's arm 0 the trip is 9.45 km against 9.8 at −13.5 % with 1.17 pp of headroom (§9.214); the constant is CONSTRAINED by §9.8 to the observed 0.3503 ride:car ratio, and `src/calibrate/asc_fixed_point.py` refuses it.
- Whether a suburb is the right carpool precision is the sweep's question (§9.124); #145's wait distribution is unread (§9.169).

## Refused — do not re-raise

- Relaxing `B.ride.pairing_rule` to `origin_link`, `dest_link` or `window_only`: pairs passengers with drivers going elsewhere (§9.81, §9.102, §9.109).
- Widening either pairing window: residual gaps of median 344 min are different trips (§9.98); a declared pair faces no clock (§9.145).
- Solving `asc_car_passenger` to close the ride gap: ASC absorption (§9.8, §9.11).
- Raising `B.activity.joint_tour_passenger_ratio`: derived from measured occupancy (§9.109).
- A directed closure pulling driver households into the sample: a 10% draw at 17.65% of persons (§9.127).
- A walking meeting point for declared pairs (§9.128).
- socnetsim joint plans: ~10× runtime (§9.44, #48).
- Re-moding an unpaired leg by mutating the plan: a one-way ratchet (§9.81).
- Reading pairing or ride share off a 1% smoke: the flow-capacity artefact and broken pairs (§9.128, §9.129).

## History

- §9.214 — bound trips ride; escorts released
- §9.211 — D12 built: the held passenger
- §9.169 — arm 0: 99.6 % paired, ride −41.6 %
- §9.210 — the Java fold; the metro target
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
