# Population and demand — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 22 September 2026 (sixty-first session) · **Record read through:** §9.211 · **Written against family:** `F35`

## What is built

- **The TfNSW bespoke-table request is DRAFTED, not sent** (§9.167, #50): `docs/requests/tfnsw_hts_bespoke_tables.md` asks for the four cells the CKAN API lacks; HELD; the four cells searched everywhere public, found nowhere (§9.172).

- **Mumbai's households carry their 2026 vehicles** (§9.209): `derive_vehicle_possession_growth.py` grows each district's 2011 HL-14 two-wheeler and car shares by the registered stock per household (RTO offices 2017 → 2025, the state series 2011 → 2017) through the Poisson at-least-one identity (`B.population.vehicle_possession_projection`): Mumbai Suburban 15.3 → 39.9 % and 12.8 → 31.6 %; the yearly pace (5–9 %) is below NFHS-4/5's state-urban 10.4 % (`_vehicle_possession_growth_report.json`).
- **Mumbai's workers go where the buildings are** (§9.209): `build_activity_attraction.py` weights every work candidate by the GHSL 2025 built volume within 300 m, non-residential and total mixed by the Economic Census own-account share (`B.activities.work_attraction`); `build_plans.py` draws inside the B-28 band by it.

**B1 — persons and households (`src/build/build_population.py`, seed 20260810, the 1,500 core SA1s only).**

- Fitted per SA1 to the census marginals — G35, G34, G36, G04, G43/G46, G17, G60; homes jittered at `B.population.home_jitter_radius_factor` 0.6 of the equivalent-circle radius (§9.1, §9.170); the tables are read through `cities/newcastle/extract/reader_shapes.py` (`config/schema/reader_shapes.json`), no ABS column named (§9.140, #62).
- **The G17 income band reaches scoring** (§9.138, #108): the weekly band midpoint is the `income` attribute (top band × `C.income.top_band_factor` 1.25; 424,190 of 621,364 WEEKDAY persons); marginalUtilityOfMoney scales by (average/personal)^`C.income.exponent` (1.0, sweep 0.5–1.5); `C.income.representation = absent` recovers the flat-money model.
- Age structure reads G04's grouped 80+ columns; employment per (SA1, sex, band) from G46A/B; school attendance from G01; the 18+ education split from G15 (§9.47, §9.61).
- Licence holding is **measured**: `B.population.licence_rate_by_age_band` (`measured`, sweep proportional 0.05) is the TfNSW Driver Licence Statistics July 2026 over the ABS ERP — 18–24 0.78, 25–34 0.94, 35–44 1.00, 75–84 0.92, 85+ 0.51 — at each person's own LGA rate (`licence_rates_by_age_lga.csv`, §9.131; asserted by `build_licence_rates.py`, §9.133).
- **A household drives the cars it owns** (§9.146, #145): under `B.population.vehicle_roster` = `census` (sweep `per_person`) each licensed member maps to one `hh<id>_car<k>`, enforced CAR-ONLY by `HouseholdCarDepartureHandler` (§9.148) — `RUN.qsim.vehicle_behavior`'s `wait` is global and measured fatal. 81,384 households (33.0 %) have more licensed drivers than vehicles (`B1_synthetic_population.csv`).
- Car availability is a licence plus a household vehicle; bike availability a draw at `B.population.bike_available_rate` 0.493 (`literature`, sweep 0.30–1.00) above `B.population.bike_min_age` 12; taxi above `B.taxi.min_unaccompanied_age` 18, both swept, zero disabling the gate (§9.39, §9.78, §9.84).

**B2 — activity chains as tours (`src/build/build_activity_chains.py`, one file per day type).**

- Home-anchored tours closing at home under the 30 h horizon; a tour that will not fit is dropped alone and counted (§9.2, §9.38, §9.164). Purposes HW, HE, HS, HO, WB, HX (serve passenger, its own rate, decay and licence requirement); NHB is a leg label (§9.15).
- The week trip rate is solved to the HTS 3.473 per person-day; weekend/weekday 0.7521 from 551 RMS station-years, SAT:SUN 1.1473; the weekday purpose mix renormalised to the HTS share (§9.2, §9.61).
- Destinations on observed POIs and CBD footprints (§9.2); gravity decay solved per purpose and LGA to the HTS network distance (`DETOUR_FACTOR` 1.3376); each draw a two-component mixture — a short kernel at `B.activity.short_trip_mean_km` weighted to `B.activity.short_trip_band_share` (literature, ±25%) plus the long kernel re-solved so every mean stays exact (§9.69).
- Still assumed, each swept: `P_MANDATORY` 0.78 / 0.85, `P_INTERMEDIATE_STOP` 0.12–0.30, `P_SECOND_STOP` 0.25, `CHILD_TOUR_RETENTION` 0.4, weekend multipliers ±30%, activity durations ±25% (§9.2); `B.activity.plan_speed_car_kmh` 26 / `plan_speed_nocar_kmh` 16 / `plan_access_s` 240 (§9.61); three intermediate-stop and decay defaults at their typed values (#198, §9.170).
- Mode is not assigned in B2; departure times are seed plans for co-evolution, not predictions (§9.2).

**The binder passes, in order.** Pairing mechanics, seeding and runtime belong to [`ride-and-pairing.md`](ride-and-pairing.md).

1. **Escort** (§9.46, §9.144): an HX tour takes an already-drawn member trip's destination and departure exactly; **a binding requires a licence AND a household vehicle** — the identity all four passes share (§9.144, #142); the HX TOUR itself is not gated.
2. **Lift** (§9.60, §9.144): an unbound HX tour is re-targeted to a driverless-household passenger within `B.activity.escort_binding_nonhh_scope` = `same_zone`; the driver must own a car.
3. **Joint** (§9.84, §9.111, §9.116): a companion's HS/HO tour (`B.activity.joint_tour_purposes`) mirrors a licensed co-member's drive, `party_size` 2; volume `B.activity.joint_tour_passenger_ratio` 0.3503 (`derived`, occupancy − 1) × the HTS driver share.
4. **Shared** (§9.124, §9.129): a car-less person's direct tour binds to another household's trip at `B.ride.shared_lift_scope` = `same_sa2_od` within `B.ride.pairing_window_min` 15 min, the households sharing a `B.ride.shared_lift_hash_bucket` of **0.25** (§9.149; 0.05 the control, at which 94 % of 27,771 unserved tours were refused on the bucket alone); **longest servable tours first** — `B.ride.shared_lift_priority` = `longest_first` (sweep `uniform`) (#86).

**Other tiers.**

- External: the 201 boundary SA1s enter the core at `B.external.interaction_rate` 0.0900 (`derived`, sweep 0.06–0.12) = `B.external.commute_share_to_core` 0.1377 × `B.external.employed_share` 0.4575 / the HW split 0.7 (§9.140, #63); weekend factors SAT 0.8429 / SUN 0.7347 (§9.61).
- Through: gate to gate at the observed AADT × `B.external.through_share` 0.35 (`assumed`) (§9.41, §9.49). Freight: `truck` a declared background load (`freight_trip_ratio` 0.0697, §9.49). Two resident carves in `src/build/build_matsim_plans.py`: motorbike `B.motorbike.trip_share` 0.0037849, truck `B.truck.resident_trip_share` 0.002993 (§9.125, §9.129).

## The state on disk

- **The demand is rebuilt at its roots and the 30 run-input sets with it** (§9.211): WEEKDAY **616,040 persons, 2,331,650 selected-plan legs, 1,095,994 tours** (`_plans_report.json`); **612,667** synthetic persons in 247,596 households. Family **F36** opened on it and nothing has run on it.

## What is measured

- **Arm 0 — the roster and the occupancy** (§9.169, `20260912T202242_300it_25pct`): **18,767** drivers waited for a household car on the last iteration, from **15,580** on F32 (#145); occupancy **0.1871** against 0.3503, OUTSIDE [0.2493, 0.394]; `occupancy_from_pairings` 0.1645.
- **The short-trip SUPPLY was unchanged on every F35 result** (§9.169, §9.177, #30): the sub-1 km share read 11.13 % routed and resident walk trips averaged **3.74 km** against **0.70** observed — −12.2 % on the scoreboard, +434 % on geometry. F36's arm 0 re-reads it.
- **The roster binds harder as the search converges** (§9.163, #145): on `20260909T015217_300it_25pct` **8,550** drivers waited on the first iteration and **15,580** on the last; car jumped +2.211 pp at the innovation cutoff alone.
- **The modelled mode × demographics table exists** (§9.163, #50; `_mode_by_demographics.json`): no licence — car 0.0 %, ride 50.9 %, walk 27.6 % (74,243 trips); licence — car 82.5 %, ride 6.1 % (467,836). The modelled half only; the observed counterpart is #50's acquisition.
- **Income's own effect is not separable** (§9.163, #108): every mode the money charges touch is OVER target except light rail; nothing has been read with `C.income.representation` OFF at the same depth in the same family.
- **The PLANS carry OSM geometry** (§9.158, #159): **3,000 of 3,000 sampled `dest_placement=poi` destinations within 5 m of an OSM POI or building** — `demand/plans/*` is **ODbL 1.0**; the POPULATION stays CC-BY. Manifest then **279 CC-BY / 218 ODbL / 15 bespoke** (§9.159).
- **`B.population.bike_min_age` is movable by the calibration loop** (§9.158); `licence_rate_by_age_band` is not, being `measured`.
- **`Serve passenger` is HX everywhere** (§9.151, #147): one purpose map (`src/build/hts_purpose.py`); `C.vot.by_purpose` re-keyed `NHB` → `HX` at the same 15.2; **140 of 141 files under `scenarios/matsim/` byte-identical**.
- **What the discard fix recovered** (§9.164, `tours_reattempted_after_a_failed_tour`): **547** weekday tours; the week trip rate reads **3.398 against the HTS 3.473**; **18,446** weekday tours are still dropped over the horizon — a different mechanism.
- On the measured licence rates the unlicensed share of the employed is 4.8–5.9% (§9.131). Joint binding is supply-limited on WEEKDAY (`thin_p` 1.0000, §9.116); lift at `same_zone` serves 97.7% of unbound HX tours (§9.84, §9.133); the shared pass reaches the occupancy identity with a shortfall of 0 (§9.124, §9.129).

## What is open

- **#86 — D12 is BUILT** (§9.211): the held passenger no longer keeps an alternative plan that takes them off `ride`; 276,816 WEEKDAY trips on 141,633 persons carry `heldRideTrips`. The binders still bind **20.62 %** of core legs, the observed passenger share, so ride's ceiling sits AT its target — what changes is that the bound trips now stay in the choice set. See [ride-and-pairing](ride-and-pairing.md); measured by `measure_bound_trips.py` on F36's arm 0.
- **#145 — measured on a full arm** (§9.169): 18,767 drivers waited on arm 0's last iteration; the wait distribution and where the self-driven bound trips settle remain unread.
- **`B.population.household_size_top_band_mean` is CONSUMED** (§9.211, #196): the geometric tail's parameter is `derived` from it — `B.population.household_size_tail_p` = 1/(mean − 5) = **0.625** (it was an independent `assumed` 0.55), and `build_population.py` computes it from the mean, asserting the two agree. The rebuilt draw's top band means **6.596** against the declared 6.6 (6.82 before), and the drawn household-size distribution tracks the census within 0.6 pp in every band (1: 26.49 vs 25.90 %; 6+: 2.59 vs 2.66 %), reported in `_population_report.json`.
- **The four HTS cells exist nowhere public** (§9.172, #50): the hub's eleven HTS resources carry mode × area and purpose × area only, none is an API; the Sydney 2012/13 report has mode × age, distance band × mode and occupancy for the Sydney GCCSA at that vintage — shapes, not targets; commute-only cells are derivable from ABS TableBuilder. The request is the only route; sending it is the user's decision (D2).
- Still assumed and swept: `B.external.through_share`, `P_INTERMEDIATE_STOP`, `P_SECOND_STOP`, `CHILD_TOUR_RETENTION`, the activity durations (§9.2, §9.61); the 9,376 `driver_is_the_companion` refusals are emergent (§9.116).
- **The sub-1 km supply is AT the seed, and #30 is re-aimed at allocation** (§9.177, §9.211, user decision): the placed core legs are **17.81 %** at ≤ 0.748 km straight (1 km at detour 1.3376) on the rebuild, against the Sydney 18.8 % band and 17.70 % before it — the chains report now states the band on PLACED coordinates beside the zone-matrix figure. The loss is at allocation: car carries half the routed short trips ([walk-and-bike](walk-and-bike.md)).

## Refused — do not re-raise

- Assigning mode in B2 — it pre-empts the question the model exists to answer (§9.2).
- A phantom driver, teleport or declared allowance for unserved lifts (§9.60).
- Fitting the household/non-household split of lifts: no observation of who drives whom (§9.60).
- Reading G62's census-night attendance as a work rate: it bounds `P_MANDATORY` from below only (§9.2).
- Blaming `B.ride.max_passengers_per_vehicle` 4: it refused 1 of 84,436 joint bindings (`_activity_chains_report.json`, §9.111).
- Sizing bike ownership against the old five-times finding (§9.39).
- Full external synthesis, a freight demand model or simulated coal trains (§9.2, §9.49, §9.70).
- Restoring the literature licence vector: superseded by the published count (§9.131).

## History

- §9.211 — the household tail derived
- §9.209 — printed timetables; possession; grades
- §9.177 — bound trips read; D12 the rebuild
- §9.176 — intro fixed: which runs are results is the board's
- §9.172 — the four HTS cells: absent from every channel
- §9.170 — placement radius from registry
- §9.169 — roster 18,767; top-band mean unconsumed
- §9.167 — one binder skeleton; HTS request drafted
- §9.166 — TfNSW bespoke tables obtainable
- §9.151 — an escort priced as an escort
- §9.149 — shared pass binds longest first
- §9.146 — a household drives the cars it owns
- §9.144 — binder driver must own a car
- §9.143 — per-trip seeded modes
- §9.142 — demand rebuilt on balanced destinations
