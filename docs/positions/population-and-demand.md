# Population and demand — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Two runs are results - F32's `20260909T015217_300it_25pct` and F35's arm 0 `20260912T202242_300it_25pct`, each `completion` `ran_to_last_iteration` at iteration 300 (§9.162, §9.169); nothing measured on any arm that did NOT reach its declared horizon is one.*

**Updated:** 14 September 2026 (forty-ninth session) · **Record read through:** §9.172 · **Written against family:** `F35`

## What is built

- **The four binder passes share one skeleton** (§9.167, #191): the day-file read, the per-person index, the busy-interval test, the resequence (#65) and the bindings writer live once; all 15 B2 tables byte-identical. **The heavy-rail target keeps summing the station publication** (#189): the 26 station-direction means are holdout; `audit_no_holdout` refuses a holdout id.
- **The TfNSW bespoke-table request is DRAFTED, not sent** (§9.167, #50): `docs/requests/tfnsw_hts_bespoke_tables.md` asks for the four cells the CKAN API lacks; HELD; the four cells searched everywhere public, found nowhere (§9.172).

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

- **The synthetic population** holds 612,634 persons in 246,865 households, 53.4% employed, 6.0% of households with no car (`cities/newcastle/demand/population/B1_synthetic_population.csv`, §9.131). **Which family's build is on disk and whether it is consistent are live facts with one home each** — the board's state block and `python tests/check_package.py`.
- **The demand is rebuilt and the 30 run-input sets with it** (§9.164): family `F33` opened on it, and F35's arm 0 `20260912T202242_300it_25pct` is the first result since (§9.169). No arm approval stands.

## What is measured

- **Arm 0 — the roster and the occupancy** (§9.169, `20260912T202242_300it_25pct`): **18,767** drivers waited for a household car on the last iteration, from **15,580** on F32 (#145); occupancy **0.1871** against 0.3503, OUTSIDE [0.2493, 0.394]; `occupancy_from_pairings` 0.1645.
- **The sub-1 km share reads 11.13 % of 576,893 trips, against 11.17 % on F32** (§9.169, #30): the short-trip SUPPLY is unchanged; resident walk trips average **3.74 km** against **0.70** observed — −12.2 % on the scoreboard, +434 % on geometry.
- **The roster binds harder as the search converges** (§9.163, #145): on `20260909T015217_300it_25pct` **8,550** drivers waited on the first iteration and **15,580** on the last; car jumped +2.211 pp at the innovation cutoff alone.
- **The second car is wanted because a declared passenger is driving it** (§9.163, #145, #86): of 20,902 declared escort pairs in sample, **10,224 (48.9 %)** have the passenger driving their **own car** against **7,821 (37.4 %)** co-assigned car + ride.
- **The modelled mode × demographics table exists** (§9.163, #50; `_mode_by_demographics.json`): no licence — car 0.0 %, ride 50.9 %, walk 27.6 % (74,243 trips); licence — car 82.5 %, ride 6.1 % (467,836). The modelled half only; the observed counterpart is #50's acquisition.
- **Income's own effect is not separable** (§9.163, #108): every mode the money charges touch is OVER target except light rail; nothing has been read with `C.income.representation` OFF at the same depth in the same family.
- **The PLANS carry OSM geometry** (§9.158, #159): **3,000 of 3,000 sampled `dest_placement=poi` destinations within 5 m of an OSM POI or building** — `demand/plans/*` is **ODbL 1.0**; the POPULATION stays CC-BY. Manifest then **279 CC-BY / 218 ODbL / 15 bespoke** (§9.159).
- **`B.population.bike_min_age` is movable by the calibration loop** (§9.158; the set 5 → 21 on `matsim_param` bindings); `B.population.licence_rate_by_age_band` is not, being `measured`.
- **`Serve passenger` is HX everywhere** (§9.151, #147): one purpose map (`src/build/hts_purpose.py`); `C.vot.by_purpose` re-keyed `NHB` → `HX` at the same 15.2; **140 of 141 files under `scenarios/matsim/` byte-identical**.
- **The demand was rebuilt on 4 Sep** (§9.142): WEEKDAY 2,185,896 legs / 989,347 tours, week average 3.343 trips per person-day against the HTS 3.473 (`_activity_chains_report.json`); every purpose × LGA realises its observed mean distance but two cells.
- **What the discard fix recovered** (§9.164, `tours_reattempted_after_a_failed_tour`): **547** weekday tours; the week trip rate reads **3.398 against the HTS 3.473**; **18,446** weekday tours are still dropped over the horizon — a different mechanism.
- On the measured licence rates the unlicensed share of the employed is 4.8–5.9% (§9.131). Joint binding is supply-limited on WEEKDAY (`thin_p` 1.0000, §9.116); lift at `same_zone` serves 97.7% of unbound HX tours (§9.84, §9.133); the shared pass reaches the occupancy identity with a shortfall of 0 (§9.124, §9.129).
- The ride gap was a demand ceiling: escort-bound travel was 5.4% of trips against an observed 20.6% (§9.83); the joint binder lifted it to ~11.5% (§9.84). Short trips: 4.45% of generated legs under 1 km against an observed 18.8% (§9.69).

## What is open

- **#86 — the demand seeds ride below its target** (§9.169): coverage 19.11 % of agents on arm 0 against 20.60 % observed, so no run on this seed reaches it; the passes reach the identity on paper (§9.142) while at the F26 gate 29,827 declared passengers drove themselves (§9.146). The seed must carry more ride — a demand rebuild that opens a family; not done.
- **#145 — measured on a full arm** (§9.169): 18,767 drivers waited on arm 0's last iteration; the wait distribution and where the self-driven bound trips settle remain unread.
- **`B.population.household_size_top_band_mean` REACHES NO OUTPUT** (§9.169, filed): `build_population.py` takes the geometric branch for the top band, so the declared 6.6 (sweep 6.0–7.5) is never consumed; consuming it opens a family.
- **The four HTS cells exist nowhere public** (§9.172, #50): the hub's eleven HTS resources carry mode × area and purpose × area only, none is an API; the Sydney 2012/13 report has mode × age, distance band × mode and occupancy for the Sydney GCCSA at that vintage — shapes, not targets; commute-only cells are derivable from ABS TableBuilder. The request is the only route; sending it is the user's decision (D2).
- Still assumed and swept: `B.external.through_share`, `P_INTERMEDIATE_STOP`, `P_SECOND_STOP`, `CHILD_TOUR_RETENTION`, the activity durations (§9.2, §9.61); the 9,376 `driver_is_the_companion` refusals are emergent (§9.116).
- **The sub-1 km SUPPLY is fixed at build time and its SHAPE is unobserved** (§9.164, #30): the destination model matches the HTS MEAN per (purpose × LGA) by construction (§9.40, §9.136); the share under 1 km is the kernel's SHAPE and the HTS gives no distribution — no short-end target exists that is not invented (§9.8, §9.13).

## Refused — do not re-raise

- Widening `B.activity.escort_binding_nonhh_scope` beyond `same_zone`: 97.7% of unbound HX tours already bind (§9.84, §9.133).
- Assigning mode in B2 — it pre-empts the question the model exists to answer (§9.2).
- A phantom driver, teleport or declared allowance for unserved lifts (§9.60).
- Fitting the household/non-household split of lifts: no observation of who drives whom (§9.60).
- Reading G62's census-night attendance as a work rate: it bounds `P_MANDATORY` from below only (§9.2).
- Blaming `B.ride.max_passengers_per_vehicle` 4: it refused 1 of 84,436 joint bindings (`_activity_chains_report.json`, §9.111).
- Sizing bike ownership against the old five-times finding (§9.39).
- Full external synthesis, a freight demand model or simulated coal trains (§9.2, §9.49, §9.70).
- Restoring the literature licence vector: superseded by the published count (§9.131).

## History

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
- §9.140 — interaction rate derived
