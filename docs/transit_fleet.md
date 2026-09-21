# Assign transit vehicles to capacity profiles

`A.transit.fleet_assignment_mode` selects how the run-input builder resolves
passenger capacities. `mode_capacity` uses the city's existing capacity fields
for the mapper's broad vehicle types. `explicit_vehicle` preserves different
configurations within those types. An active vehicle without a declared
capacity is refused in either representation.

The explicit representation is required when one broad type cannot describe
the operated configurations. It does not supply missing observations or prove
that a sampled simulation preserves boarding and crowding.

## Input contract

Each mapped scenario supplies `fleet_assignments.json` beside its
`transitVehicles.xml.gz` and `transitSchedule.xml.gz`. The file must satisfy
[`transit_fleet.schema.json`](../config/schema/transit_fleet.schema.json).
The city owns its production and the evidence for its vehicle assignments.

| Field | Meaning |
|---|---|
| `schema_version` | Contract version |
| `mapped_vehicles_sha256` | SHA-256 of the original mapped vehicle file bytes |
| `mapped_schedule_sha256` | SHA-256 of the original mapped schedule file bytes, before signal/dwell transformations or day filtering |
| `profiles` | Profile IDs mapped to `base_type`, `seats_field` and `standing_field` |
| `vehicles` | Original mapped vehicle IDs mapped to profile IDs |

Profile IDs must differ from the original mapped type IDs. Capacity field
references resolve through the city's registry and applicable scenario/day
overlays. Both fields must use `persons_per_vehicle`. Counts must be finite,
nonnegative integers, and their sum must be positive. An unobtained registry
value is not replaced with a default. A real zero component is preserved.

Every active vehicle must have an assignment. Entries for vehicles removed by
day filtering are permitted, so the same assignment file can cover the whole
mapped schedule. Unknown vehicles, undefined profiles, incompatible base types
and duplicate JSON keys fail validation. A profile's base type must equal the
vehicle's original mapped type; an assignment cannot silently turn a bus into
a rail vehicle.

The hashes bind the assignment to one mapped input pair. When using a derived
signal/dwell schedule, the comparison still uses that scenario's original
mapped schedule. Re-mapping requires a newly derived, evidenced assignment;
it cannot reuse an old file merely because some identifiers happen to match.

## What the builder preserves

The builder clones each used profile's mapped base type, sets its passenger
capacities and reassigns the surviving vehicle references to it. Departure IDs,
departure times, stop offsets and mapped route links retain the existing
schedule-filtering semantics. The capacity sampler then operates separately
on every emitted profile, including both seated and standing components.

Physical dimensions, passenger-car equivalents, speed, doors, boarding and
alighting settings, and engine attributes are inherited from the base type.
The source type therefore still needs the correct physical configuration.
A capacity profile does not turn generic mapper dimensions into measured
vehicle dimensions or establish fleet availability and block feasibility.

Fleet validation completes before either filtered transit XML file is written.
This is not an atomic transaction for the whole scenario assembly. The build
report records the active vehicle-to-profile mapping and the capacities changed.

## Verification and remaining evidence

[`test_transit_fleet.py`](../tests/unit/test_transit_fleet.py) exercises the
run-input builder and the capacity sampler together. It checks heterogeneous
configurations, zero standing room, unchanged clocks and route links, invalid
capacities, missing assignments, duplicate definitions and mapped-build hashes.
The existing mode path is compared with its prior XML behaviour.

These checks prove software behaviour, not operating truth. Before enabling
explicit assignment for a city, acquire or derive the dated vehicle/configuration
crosswalk, configuration capacities and physical type definitions, and preserve
their provenance. Validate current service and fleet feasibility independently.
Capacity rounding and sampling equivalence still require measured experiments.

The city producer must also establish auditable consumer wiring for any new
registry capacity fields. References in bulk assignment JSON alone are not
recognised by the static hardcoding audit; a producer names the fields it
resolves. Mumbai's producer is `cities/mumbai/build/build_transit_fleet.py`
(DECISIONS.md 9.206): it assigns every mapped vehicle a profile from the
registry's `A.transit.fleet_profiles` table - by the OSM route relation the
feed builder writes into a generated line's id, or by transport mode and
mapped base type - and resolves each profile's capacity fields once, so an
unobtained declaration refuses the assignment before the assembly reads it.

The sample scaler also scales each vehicle type's passenger-car equivalent by
the fraction when `RUN.sample.transit_pce_scaling` is set (9.206): transit
vehicles run at full frequency on links whose flow capacity is scaled, and at
their full PCE a bus took a hundred times its real share of a 1 % lane.
