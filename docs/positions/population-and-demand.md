# Population and demand — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 27 September 2026 (sixty-fourth session) · **Record read through:** §9.214 · **Written against family:** `F38`

## What is built

- **The TfNSW bespoke-table request is DRAFTED, not sent** (§9.167, #50): `docs/requests/tfnsw_hts_bespoke_tables.md` asks for the four cells the CKAN API lacks; HELD; the four cells searched everywhere public, found nowhere (§9.172).

- **Mumbai's households carry their 2026 vehicles** (§9.209): `derive_vehicle_possession_growth.py` grows each district's 2011 HL-14 two-wheeler and car shares by the registered stock per household through the Poisson at-least-one identity (`B.population.vehicle_possession_projection`): Mumbai Suburban 15.3 → 39.9 % and 12.8 → 31.6 % (`_vehicle_possession_growth_report.json`).
- **Mumbai's workers go where the buildings are** (§9.209): `build_activity_attraction.py` weights every work candidate by the GHSL 2025 built volume within 300 m (`B.activities.work_attraction`); `build_plans.py` draws inside the B-28 band by it.

**B1 — persons and households (`src/build/build_population.py`, seed 20260810, the 1,500 core SA1s only).**

- Fitted per SA1 to the census marginals — G35, G34, G36, G04, G43/G46, G17, G60; homes jittered at `B.population.home_jitter_radius_factor` 0.6 of the equivalent-circle radius (§9.1, §9.170); the tables are read through `cities/newcastle/extract/reader_shapes.py`, no ABS column named (§9.140, #62).
- **The G17 income band reaches scoring** (§9.138, #108): the weekly band midpoint is the `income` attribute (top band × `C.income.top_band_factor` 1.25); marginalUtilityOfMoney scales by (average/personal)^`C.income.exponent` (1.0, sweep 0.5–1.5); `C.income.representation = absent` recovers the flat-money model.
- Age structure reads G04's grouped 80+ columns; employment per (SA1, sex, band) from G46A/B; school attendance from G01; the 18+ education split from G15 (§9.47, §9.61). The household-size tail `B.population.household_size_tail_p` = 1/(`household_size_top_band_mean` − 5) = 0.625, `derived` (§9.211, #196).
- Licence holding is **measured**: `B.population.licence_rate_by_age_band` is the TfNSW Driver Licence Statistics July 2026 over the ABS ERP — 18–24 0.78, 25–34 0.94, 35–44 1.00, 75–84 0.92, 85+ 0.51 — at each person's own LGA rate (`licence_rates_by_age_lga.csv`, §9.131, §9.133).
- **A household drives the cars it owns** (§9.146, #145): under `B.population.vehicle_roster` = `census` each licensed member maps to one `hh<id>_car<k>`, enforced CAR-ONLY by `HouseholdCarDepartureHandler` (§9.148). 81,384 households (33.0 %) have more licensed drivers than vehicles (`B1_synthetic_population.csv`).
- Car availability is a licence plus a household vehicle; bike availability a draw at `B.population.bike_available_rate` 0.493 (`literature`, sweep 0.30–1.00) above `B.population.bike_min_age` 12; taxi above `B.taxi.min_unaccompanied_age` 18 (§9.39, §9.78, §9.84).
- **Motorbike availability is drawn from observations** (§9.214, D22, #257): rider licence from the TfNSW snapshot's Rider class, learners included, over ERP by age band and LGA (`B.population.rider_licence_rate_by_age_band`, derived); household motorcycle possession from BITRE's garaging-postcode registrations over census dwellings by the Poisson at-least-one identity (`B.population.household_motorcycle_share` 0.1254, derived); `B.motorbike.rider_coupling` = `riders_first` (assumed, `independent` the other member).
- **Motorbike availability as drawn** (§9.214): **35,416** persons available (5.78 %); 77,100 riders drawn against 76,675.5 observed, 31,010 possessing households against 31,061.1 (`_plans_report.json` `motorbike_availability`). See [motorbike-truck-and-freight](motorbike-truck-and-freight.md).

**B2 — activity chains as tours (`src/build/build_activity_chains.py`, one file per day type).**

- Home-anchored tours closing at home under the 30 h horizon; a tour that will not fit is dropped alone and counted (§9.2, §9.38, §9.164). Purposes HW, HE, HS, HO, WB, HX (serve passenger); NHB is a leg label (§9.15); `Serve passenger` is HX everywhere (§9.151, `src/build/hts_purpose.py`).
- The week trip rate is solved to the HTS 3.473 per person-day; weekend/weekday 0.7521 from 551 RMS station-years, SAT:SUN 1.1473; the weekday purpose mix renormalised to the HTS share (§9.2, §9.61).
- **Destinations follow each person's own mobility** (§9.214): `B.activity.destination_mobility` = `own_speed` (`absent` = F37) — the long kernel is one time decay at each segment's planning speed, the car-less matrix decaying **1.2506** times faster per km, solved against each origin's car-less share of production (0.2339) so both segments together realise the survey's mean per purpose and home LGA. Car-less against car, network km: HW 15.9 / 18.6, HE 5.0 / 6.7, HS 7.1 / 9.2, HO 9.4 / 10.9, WB 19.9 / 22.0, HX 6.6 / 8.3 (`_activity_chains_report.json` `decay`).
- **The planning speeds are derived** (§9.214): `B.activity.plan_speed_car_kmh` 26.0 assumed → **26.80** (HTS car 10.2 km in 17.2 min over the measured detour 1.3276); `B.activity.plan_speed_nocar_kmh` 16.0 assumed → **21.43** (the survey's non-driver trips at their observed shares: 311.66 km over 657.24 min).
- Destinations on observed POIs and CBD footprints (§9.2); each draw a two-component mixture — a short kernel at `B.activity.short_trip_mean_km` weighted to `B.activity.short_trip_band_share` (literature, ±25%) plus the long kernel re-solved so every mean stays exact (§9.69).
- Still assumed, each swept: `P_MANDATORY` 0.78 / 0.85, `P_INTERMEDIATE_STOP` 0.12–0.30, `P_SECOND_STOP` 0.25, `CHILD_TOUR_RETENTION` 0.4, weekend multipliers ±30%, activity durations ±25% (§9.2); `plan_access_s` 240 (§9.61).
- Mode is not assigned in B2; departure times are seed plans for co-evolution, not predictions (§9.2).

**The binder passes, in order.** Pairing mechanics, seeding and runtime belong to [`ride-and-pairing.md`](ride-and-pairing.md).

1. **Escort** (§9.46, §9.144): an HX tour takes an already-drawn member trip's destination and departure exactly; **a binding requires a licence AND a household vehicle** (§9.144, #142). **A one-way binding survives only on a member who cannot drive** (§9.214): `B.activity.escort_oneway_scope` = `cannot_drive` (assumed; `any_member` = F37); for anyone else it is released and the serve tour, still placed, is labelled `escort_released` and offered to the lift pass. Weekday: **50,011** drops and 12 pick-ups released; one-way member tours **70,591 → 20,365**; bound escort km 11.88 → 9.92.
2. **Lift** (§9.60, §9.144): an unbound HX tour is re-targeted to a driverless-household passenger within `B.activity.escort_binding_nonhh_scope` = `same_zone`; the driver must own a car. Lifts bound **44,632 → 93,318** (round trip) with the released tours (§9.214).
3. **Joint** (§9.84, §9.111, §9.116): a companion's HS/HO tour mirrors a licensed co-member's drive, `party_size` 2; volume `B.activity.joint_tour_passenger_ratio` 0.3503 (`derived`, occupancy − 1) × the HTS driver share.
4. **Shared** (§9.124, §9.129): a car-less person's direct tour binds to another household's trip at `B.ride.shared_lift_scope` = `same_sa2_od` within `B.ride.pairing_window_min` 15 min, sharing a `B.ride.shared_lift_hash_bucket` of **0.25** (§9.149); **longest servable tours first** (`B.ride.shared_lift_priority` = `longest_first`, #86).

**Other tiers.**

- External: the 201 boundary SA1s enter the core at `B.external.interaction_rate` 0.0900 (`derived`, sweep 0.06–0.12) (§9.140, #63); weekend factors SAT 0.8429 / SUN 0.7347 (§9.61).
- Through: gate to gate at the observed AADT × `B.external.through_share` 0.35 (`assumed`) (§9.41, §9.49). Freight: `truck` a declared background load (`freight_trip_ratio` 0.0697, §9.49). One resident carve in `src/build/build_matsim_plans.py`: truck `B.truck.resident_trip_share` 0.002993 (§9.125); motorbike's carve is retired under `B.motorbike.representation` = `choice` (§9.214).

## The state on disk

- **F38's plans** (§9.214, `_plans_report.json`): WEEKDAY **622,174 persons** (core 510,346, external 6,142, through 16,264, freight 89,422), **2,393,473 selected-plan legs, 1,102,769 tours**; **612,667** synthetic persons. The builder refuses a plan that loses any tier's agents (§9.213). Family **F38** opened on it (`20260927T125424`).

## What is measured

- **The week trip rate reads 3.470 against the HTS 3.473** (§9.214, `realised_week_trip_rate`): it was 3.398 on F37's demand; fewer tours overran the day. WEEKDAY still drops 17,495 tours over the horizon (`_activity_chains_report.json`).
- **What the one-way escort cost on F37's result** (§9.214, item 2): the binder covered 70,571 weekday member tours ONE way against 24,993 round trip at a mean 11.88 network km against the survey's 7.84 for serve-passenger travel; held to ride, the car stayed home and the tour's other trips walked (35.6 % of walk km) or took taxi.
- **What one kernel per purpose cost on F37's result** (§9.214, item 3): the car-less (23.4 % of production) made 57 % of bike trips, 37 % of taxi trips and walked a mean 6.0 km.
- **Income's own effect is not separable** (§9.163, #108): nothing has been read with `C.income.representation` OFF at the same depth in the same family.
- **The PLANS carry OSM geometry** (§9.158, #159): **3,000 of 3,000 sampled `dest_placement=poi` destinations within 5 m of an OSM POI or building** — `demand/plans/*` is **ODbL 1.0**; the POPULATION stays CC-BY.
- The drawn household-size distribution tracks the census within 0.6 pp in every band, top band mean 6.596 against 6.6 (§9.211, `_population_report.json`). On the measured licence rates the unlicensed share of the employed is 4.8–5.9% (§9.131); joint binding is supply-limited on WEEKDAY (`thin_p` 1.0000, §9.116).

## What is open

- **F38's arm 0 reads the two demand changes** (§9.214): walk km inside held-ride tours against 35.6 %, the car-less split and trip lengths against F37's; see [walk-and-bike](walk-and-bike.md) and [ride-and-pairing](ride-and-pairing.md).
- **#86 — the held passenger** (§9.211, §9.214): bound escort and joint trips executed as ride on 100 % of F37's; see [ride-and-pairing](ride-and-pairing.md).
- **#145 — measured on a full arm** (§9.169): the wait distribution and where the self-driven bound trips settle remain unread.
- **The four HTS cells exist nowhere public** (§9.172, #50): the request is the only route; sending it is the user's decision (D2).
- Still assumed and swept: `B.external.through_share`, `B.activity.escort_oneway_scope`, `B.motorbike.rider_coupling`, `P_INTERMEDIATE_STOP`, `P_SECOND_STOP`, `CHILD_TOUR_RETENTION`, the activity durations (§9.2, §9.61, §9.214). The rider licence rate for 12-17 applies to 12-15 year olds as the car rate does (§9.214).
- **The sub-1 km supply is AT the seed, and #30 is re-aimed at allocation** (§9.177, §9.211, user decision): placed core legs **17.81 %** at ≤ 0.748 km straight against the Sydney 18.8 % band.

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

- §9.214 — destinations by mobility; escorts released
- §9.213 — the external tier restored
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
