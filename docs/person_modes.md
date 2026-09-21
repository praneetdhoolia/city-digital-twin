# Person-specific mode availability

A population can supply `permittedModes`, a comma-separated String attribute
on each person. It lists that person's complete permitted choice set using the
run's configured mode names. This lets a city represent access to motorcycles,
shared services or other modes separately from car ownership.

```xml
<attribute name="permittedModes" class="java.lang.String">walk,motorbike,pt</attribute>
```

This is a data contract, not an ownership estimate. The city must derive each
person's set from evidenced licence eligibility, household access, service
eligibility and any modelled allocation, with provenance and uncertainty. A
household possessing a motorcycle does not prove that every member can drive
it. Asset-possession percentages do not give vehicle counts or simultaneous
availability. Unknown access must be resolved before writing a complete set.

`AvailabilityModesCalculator` intersects this set with configured mode choices
and the existing car, ride, bicycle and age restrictions. Inclusion cannot
grant a mode missing from the run's choice configuration. Car-licence and
car-availability flags constrain car; they do not automatically deny a different
driving mode. Its own eligibility must be represented in `permittedModes`.
Empty entries, duplicate entries, unconfigured names and non-String attributes
are errors. Mode names may also be declared by the routing, QSim or transit
configuration, which permits a locked external mode outside the resident
choice list. A locked mode must be included in an explicit set.

Before constructing the controller, the simulator checks every stored plan
for people carrying this attribute, including unselected alternatives. It
checks each trip's routing mode; when that is absent, the existing transit
main-mode identifier interprets the trip. Physical access legs and transit
transfer legs do not need separate main-mode permission. Conflicting routing
mode labels or an unavailable initial trip are refused. Replanning uses the
same availability calculator through the existing gated mode-choice strategy.

An absent attribute preserves the existing treatment. This migration path is
not evidence that all modes are available in another city's population. The
current population and plan builders still use fixed employment, vehicle and
motorcycle-allocation assumptions. A new city must supply a compatible builder
and complete person data before this mechanism can support a runnable twin.

This choice set does not allocate a particular household vehicle over time,
couple a pillion to a rider, dispatch an autorickshaw, enforce road access or
validate reduced-sample behaviour. Those mechanisms and observations remain
separate requirements.

Run `python tests/check_person_modes.py` for the native MATSim check. It checks
synthetic person data, legacy restrictions, malformed input, locked modes,
unselected plans, access legs, transfers and an XML round trip. It is not a city
simulation or an estimate of mode shares. Decision record: [§9.186](DECISIONS.md#9186-person-specific-mode-availability-19-september-2026).
