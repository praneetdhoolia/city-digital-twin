# BEST operational data specification

Draft for the Mumbai simulation, 19 September 2026. Not sent.

The public operator website supplies fares, passes and depot-route listings.
The community GTFS package supplies candidate schedules. Neither establishes
current operating departures, vehicle capacities or observed passenger loads.
The [evidence notes](../evidence_notes.md) record the checks and conflicts.

## Records identified in BEST's own disclosures

The [Traffic Department manual](https://www.bestundertaking.com/assets/pdf/rti/traffic_Departmental_manual_2021.pdf),
PDF page 146, describes computerised bus and crew schedules, timewise buses on
road, route kilometres and trips, turnout/stabling, terminal details, loading
and waiting surveys, and origin–destination surveys. Page 126 distinguishes
seating certificates and additional permitted capacity.

The [Transport Engineering manual](https://www.bestundertaking.com/assets/pdf/Transport_Engineering.pdf),
PDF pages 62–63, identifies the monthly Operational Statistical Bulletin, fleet
availability, late/not-out and terminal-detention records, and bus-wise carrying
capacity held in computer records and the Bus Office.

The [Budget Department manual](https://www.bestundertaking.com/assets/pdf/rti/budget_manual_2021.pdf),
PDF page 3, identifies monthly Buses Operational Results, Annual Financial
Statistics and quarterly performance returns to MoRTH. These are historical
manual descriptions; current custodians and record coverage need confirmation.

## Required fields and interpretation

| Record | Required fields | Simulation use |
|---|---|---|
| Effective route and stop register | Stable IDs, stop coordinates, direction, variant, ordered stops, path, fare stages, start/end validity | Reconcile GTFS, geometry and fare-stage distance |
| Scheduled and operated departures | Service date, route/variant/trip IDs, scheduled and actual stop times, cancellation, short turn, diversion and calendar exception | Distinguish planned supply from actual service |
| Vehicle configuration and allocation | Vehicle/type IDs, model and variant, length, permitted seated/standing passengers separately, accessibility, fuel, validity, trip/block/depot allocation | Preserve capacity, dwell, road footprint and fleet feasibility |
| Availability and blocks | Owned/wet-lease distinction, daily available and operated vehicles, turnout/stabling, dead running, breakdown and replacement, depot/terminal detention | Model empty movement and unavailable stock |
| Passenger observations | Date, route/trip/stop or fare stage, boardings/alightings, loads, source method, coverage, missingness, ticket/pass/concession treatment | Calibrate boardings, crowding and passenger journeys without conflation |
| Loading, waiting and OD surveys | Anonymous aggregate OD, time band, vehicle/load counts, waiting observations, survey dates and sampling weights | Reconstruct demand and validate route choice and waits |
| Fare and pass rules | Dated fare-stage register, taxes, toll additions, eligibility, transfers, products, validity and amendments | Calculate the price actually faced by different travellers |

Request existing machine-readable records with data dictionaries and ID
crosswalks. Keep typical weekdays, Saturdays, Sundays, public holidays,
festival diversions and monsoon disruption dates distinguishable. Date ranges
must cover the selected model period and state where historical comparisons
use a different service regime.

No passenger names, contact details, payment identifiers or staff identities
are needed. Aggregate observations and anonymous operational IDs suffice.
Record disclosure and reuse terms with the supplied files. Preserve raw bytes,
source timestamps and hashes before extraction.

## Acceptance checks

- Join stops, routes, trips, blocks and vehicles using documented identifiers.
- Reconcile trips and kilometres with operational returns on the same dates.
- Check boardings against the same reporting universe, including pass users.
- Reconcile permitted seats and standing places with assigned configurations;
  retain missing values and configuration changes.
- Distinguish registered, procured, delivered, available and operated fleets.
- Preserve actual times, scheduled times, missing reports and cancellation
  flags separately; do not treat a stale tracking response as a fresh vehicle.
- Resolve the dated fare-table conflict with the undated concessions page.

These checks establish input usability. They do not replace independent
validation of simulated travel, crowding, waiting and ridership.
