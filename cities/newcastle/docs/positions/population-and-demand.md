# Population and demand — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Nothing here is a result: no run since family F4 has reached its gate.*

**Updated:** 30 August 2026 · **Record read through:** §9.131 · **Open family:** F20

## What is built

**B1 — persons and households (`src/build/build_population.py`, seed 20260810, the 1,500 core SA1s only).**

- Fitted per SA1 to the census marginals: household size (G35), vehicles (G34), dwelling structure (G36), age–sex (G04), labour force (G43/G46), income (G17), occupation (G60); home coordinates jittered within the SA1 at 0.6 of the equivalent-circle radius (§9.1).
- Age structure reads G04's grouped 80+ columns, so the 75+ population exists; employment, the full-time/part-time split and unemployment are drawn per (SA1, sex, ABS band) from G46A/B; school attendance per SA1 from G01; the 18+ full-time/part-time education split is observed per SA1 from G15, and `B.population.tertiary_ft_share` is retired (§9.47, §9.61).
- Licence holding is **measured**: `B.population.licence_rate_by_age_band` (`measured`, sweep proportional 0.05) is the TfNSW Driver Licence Statistics July 2026 snapshot over the ABS estimated resident population at 30 June 2024, pooled 18–24 0.78, 25–34 0.94, 35–44 1.00 (capped), 45–74 0.97–0.98, 75–84 0.92, 85+ 0.51, 12–17 0.08; each person is drawn at their own LGA's rate from `data/processed/observed/licence_rates_by_age_lga.csv` (§9.131).
- Car availability is a licence plus a household vehicle; bike availability is a per-person draw at `B.population.bike_available_rate` 0.493 (`literature`, CWANZ NSW 2025, sweep 0.30–1.00), gated below `B.population.bike_min_age` 12; taxi is gated below `B.taxi.min_unaccompanied_age` 18, both thresholds assumed and swept with zero disabling the gate (§9.39, §9.78, §9.84).

**B2 — activity chains as tours (`src/build/build_activity_chains.py`, one file per day type: WEEKDAY, SAT, SUN).**

- Home-anchored tours: every tour closes at home, the day is capped at the 30 h horizon and tours that do not fit are dropped and counted (§9.2, §9.38). Tour purposes are HW, HE, HS, HO, WB and HX (serve passenger, its own rate, decay and licence requirement); NHB is a leg label, not a tour purpose (§9.15).
- The week trip rate is solved to the HTS 3.473 per person-day; the day-type shape is measured — weekend/weekday 0.7521 from 551 RMS station-years, SAT:SUN 1.1473 from the hourly classified file — and the weekday purpose mix is renormalised against the HTS purpose share (§9.2, §9.61).
- Destinations are placed on observed POIs and CBD building footprints, with a jittered point only where a zone has neither (§9.2). The gravity decay is solved per purpose and LGA so the expected network distance equals the HTS figure, through a `DETOUR_FACTOR` of 1.3376 measured on the A1 road graph (§9.2). Each draw is a two-component mixture: a short kernel at `B.activity.short_trip_mean_km` (derived from the observed walk trip length) weighted to `B.activity.short_trip_band_share` (literature, BTS Sydney HTS 2012/13 table 4.4.7, ±25%), plus the solved long kernel re-solved so every observed mean stays exact (§9.69).
- Still assumed, each swept: `P_MANDATORY` 0.78 / 0.85 on a weekday (bounded below by G62's 0.6508), `P_INTERMEDIATE_STOP` 0.12–0.30 by purpose, `P_SECOND_STOP` 0.25, `CHILD_TOUR_RETENTION` 0.4, the weekend purpose multipliers ±30%, activity durations ±25% (§9.2); the plan-timing scaffold `B.activity.plan_speed_car_kmh` 26 / `B.activity.plan_speed_nocar_kmh` 16 / `B.activity.plan_access_s` 240 (§9.61).
- Mode is not assigned in B2, and departure times are seed plans for MATSim's co-evolution, not predictions (§9.2).

**The binder passes, in order, each on the closed day file.** Pairing mechanics, seeding and runtime realisation belong to [`ride-and-pairing.md`](ride-and-pairing.md).

1. **Escort** (§9.46): households generate whole, and an HX tour takes an already-drawn member trip's destination and departure exactly; the bound tour is immovable in the escorter's day.
2. **Lift** (§9.60): an unbound HX tour is re-targeted to a driverless-household passenger within `B.activity.escort_binding_nonhh_scope` = `same_zone`, the serving leg timed to the passenger's own departure; adds no tour and no trip.
3. **Joint** (§9.84, §9.111, §9.116): a household companion's HS/HO tour (`B.activity.joint_tour_purposes`) becomes a mirror of a licensed co-member's drive, `party_size` 2, the driver tour shifted into the vacated slot where needed; the volume is `B.activity.joint_tour_passenger_ratio` 0.3503 (`derived`, occupancy − 1) times the HTS driver share, counting escort- and lift-covered trips first; candidates whose household holds no other eligible driver are removed before thinning (§9.116).
4. **Shared** (§9.124, §9.129): a car-less person's direct tour binds to another household's trip with the same origin and destination zone at `B.ride.shared_lift_scope` = `same_sa2_od`, departing within `B.ride.pairing_window_min` 15 min, the two households sharing a `B.ride.shared_lift_hash_bucket` of 0.05; thinned to the same occupancy identity, with the shortfall reported when supply is short.

**Other tiers, all in the same builder.**

- External: the 201 boundary SA1s' residents enter the core at `B.external.interaction_rate` 0.08 (`assumed`, sweep 0.04–0.15) through derived cordon crossings, placed on the same attractors, ride withheld (`B.external.agent_ride_available`), scaled on the weekend by the measured light day factors SAT 0.8429 / SUN 0.7347 (§9.2, §9.15, §9.61).
- Through: trips enter at one derived cordon gate and exit at another at the gate's own observed AADT times `B.external.through_share` 0.35 (`assumed`), with the gate's observed heavy share carried as trucks (§9.41, §9.49).
- Freight: `truck` is a declared, swept physical background load (`freight_trip_ratio` 0.0697 in `_activity_chains_report.json`), not a freight demand model (§9.49); the coal chain is not simulated (§9.70). Two resident carves are drawn in `src/build/build_matsim_plans.py` on the pool that excludes escorters and named drivers: motorbike `B.motorbike.trip_share` 0.0037849 (`derived`, the target LGA's G62 cell — it supersedes §9.116's 0.0024064) and truck `B.truck.resident_trip_share` 0.002993 (`derived`) (§9.125, §9.129).

## The state on disk

- **The package is inconsistent.** `cities/newcastle/demand/population/B1_synthetic_population.csv` was rebuilt 30 Aug 19:31 on the measured licence rates: 612,634 persons, 246,865 households, 53.4% of persons employed, 6.0% of households with no car (`_population_report.json`, §9.131).
- The demand chain was stopped mid-way through the WEEKDAY chains and its partial `B2_activity_trips_WEEKDAY.csv` and `B2_escort_bindings_WEEKDAY.csv` were deleted; the SAT and SUN chains, the WEEKDAY joint, lift and shared binding files, all plans and the 30 run-input sets are the F20 build on the old population (§9.131, `NEXT_AGENT_BRIEF.md` §0).
- `_activity_chains_report.json` therefore describes the old population (`persons` 612,687): WEEKDAY 2,187,183 legs, 989,375 tours, 509,575 travelling persons, 5,632 external and 16,264 through agents; escort 127,203 of 177,318 HX tours bound; lift 49,030 of 50,014; joint 82,384 bound at `thin_p` 1.0; shared 73,509 servable / 59,701 bound / 0 shortfall (`_activity_chains_report.json`).
- `tests/check_package.py` is expected to fail until `build_activity_chains.py`, `build_matsim_plans.py`, `build_matsim_run_inputs.py` and `build_manifest.py` are rerun — the next session's first build, about an hour of CPU (`NEXT_AGENT_BRIEF.md` §0). Family F21 opens at that arm's launch (§9.131).
- The registry holds 414 fields at handoff (`NEXT_AGENT_BRIEF.md` §0). The manifest and `check_doc_currency.py` counts re-pin after the rebuild.

## What is measured

- The literature licence vector left 14.2–14.8% of employed persons without a licence; on the measured rates the unlicensed share of the employed is 4.8–5.9% (Newcastle 12.7%, its 18–24 rate 0.68) and employed persons with a car available rose from 78.9–83.0% to 90.8–91.7% in four LGAs and 80.8% in Newcastle (§9.131). What that does to the binder pools and the run is unmeasured until the chains are rebuilt.
- The ride gap was a demand ceiling, not a choice defect: every B2 trip carried `party_size` 1 and escort-bound travel was 5.4% of trips against an observed vehicle-passenger share of 20.6% (§9.83). The joint binder lifted ride-eligible travel to about 11.5% of core trips and saturated on household supply (§9.84); the shared pass now reaches the occupancy identity's 448,229 WEEKDAY passenger trips with a shortfall of 0 on the old population (§9.124, §9.129). The ceiling is closed at the binding level; what the run realises is F21's measurement.
- Residents without a car make 24.7% of trips and hold only the rides the demand binds; their surplus lands on walk, bike and pt, so bike's and bus's excess is ride's deficit wearing other modes (§9.123).
- Joint binding on WEEKDAY is supply-limited (`thin_p` 1.0000, 55,671 candidates unservable); on the weekend thinning still binds (SAT 0.6216, SUN 0.5955) (§9.116). 41.7% of multi-person households had at most one licensed travelling member on the old licence vector (§9.111).
- Lift binding at `same_zone` serves 98.0% of unbound HX tours; the constraint is driver supply, not scope (§9.84).
- Short trips: 4.45% of generated legs were under 1 km against an observed all-purpose band share of 18.8%; the mixture targets the distribution, and the walk share it buys is an arm's measurement (§9.69).
- Realised week trip rate 3.344 against the HTS 3.473 on the old population (`_activity_chains_report.json`); placement `poi` 2,671,691, `home` 2,521,742, `jitter` 157,136, `escorted` 243,024 (`_activity_chains_report.json`).
- The committed builder had stopped reproducing the committed demand for the life of PR #95; caught from the build report, not a gate, and `build_mode_targets.py` now asserts its declared inputs against their sources (§9.116). `check_package.py` was failing on `main` while three documents said it passed (§9.117).

## What is open

- #86 — passenger demand against the observed 20.6%: the four passes reach the identity on paper; realisation at F21 is the test (#86, §9.124).
- #91 — ride legs generated with no declared driver: the choice-set seed's question, on the ride page (#91, §9.120).
- #50 — no mode × age cell exists in the held data; the age gates are assumed and swept, and the modelled split is sex-invariant against G62 (§9.78, §9.84).
- #63 — the 0b backlog: `B.external.interaction_rate`, `B.external.through_share`, `P_INTERMEDIATE_STOP`, `P_SECOND_STOP`, `CHILD_TOUR_RETENTION` and the activity durations stay assumed; a journey-to-work origin–destination table would settle the first and is not held (§9.2, §9.61).
- #96 — 99 unclosed subtours mix chain- and non-chain-based modes, all in days that never return home (§9.119).
- The licence rebuild changes who is a driver, a companion and a car-less passenger in every binder pool; the counts above are the old population's until the rebuild (§9.131).
- The 8,150 `driver_is_the_companion` refusals that survive the filter are emergent, not structural, and stay reported (§9.116).

## Refused — do not re-raise

- Widening `B.activity.escort_binding_nonhh_scope` beyond `same_zone`: 98.0% of unbound HX tours already bind; the lever was spent (§9.84).
- Assigning mode in B2 — it would pre-empt the question the model exists to answer (§9.2).
- A phantom driver, teleport or declared allowance for unserved lifts (M3): violates no-teleportation and no-invented-data (§9.60).
- Fitting the household/non-household split of lifts: no observation of who drives whom exists; it is reported, never fitted (§9.60).
- Reading G62's census-night attendance as a behavioural work rate: it bounds `P_MANDATORY` from below only (§9.2).
- Blaming `B.ride.max_passengers_per_vehicle` 4: it refused 2 of 73,258 joint bindings (§9.111).
- Sizing bike ownership against the old five-times finding, measured on a model that no longer exists (§9.39).
- Full external synthesis, a freight demand model or simulated coal trains (§9.2, §9.49, §9.70).
- Restoring the literature licence vector: superseded by the published count over the published population (§9.131).

## History

- §9.131 — licence rate measured per LGA
- §9.129 — bucket rule; carves on drawn pool
- §9.125 — resident truck drivers carved from G62
- §9.124 — fourth pass binds shared rides
- §9.123 — car-less quarter wears ride's deficit
- §9.117 — local suite failing, record reconstructed
- §9.116 — builder stopped reproducing its demand
- §9.111 — companion was their own driver
- §9.84 — joint binder and age gates
- §9.83 — ride gap is a demand ceiling
- §9.69 — short trips get observed distribution
- §9.61 — three assumptions became measurements
- §9.60 — unbound escorts re-targeted to passengers
- §9.47 — phantom elderly commuters repaired
- §9.46 — escort binds to the escorted
