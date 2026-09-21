# Evidence required before downscaling Mumbai

No Mumbai sample fraction has been shown to preserve accuracy. A smaller
population can change queues, discrete vehicle capacity, transfers and rare
services even when demand and road capacity use the same multiplier.

The existing project rule permits 25% experiment arms. A short smoke test is
not a calibration result. A new multi-hour run requires a stated-cost user
approval. A small development case has completed, with its own run record.
Its `100pct` filename means every person in the explicit 1,000-person input,
not the population of Mumbai. No citywide expansion is applied.

The user now prioritises a broad behavioural baseline before corridor precision
(decision 9.187). Coarse supply and provisional parameters may support that
first executable model, with their limitations reported. A successful smoke run
does not establish calibration or scaling equivalence.

## Preserve the mechanisms

Keep physical geometry, distances, travel times and service departure times.
Do not shrink the city, delete modes or thin a timetable to reduce runtime.
Any network simplification must retain route choice, access, barriers, transfer
paths, shared-track conflicts and measured bottlenecks relevant to the task.

Sample coupled households, drivers/passengers and travelling parties together.
Measure inclusion probabilities and design effects. Check each geographical,
income, age and mode group, particularly rare modes and cross-boundary trips.
An absent rare mode cannot pass because an aggregate fit is good.

Scale road storage and flow capacities consistently with represented vehicle
demand. Validate heterogeneous vehicles and passenger-car equivalents against
local observations; the Newcastle car model does not establish Mumbai mixed
traffic validity.

Audit every transit vehicle type, both seats and standing places, zero-capacity
components, integer rounding and minimum capacity rules. Preserve the distinction
between passenger capacity, vehicle capacity on a ferry, and cargo capacity.
Low-capacity autos, shared taxis and small ferries need explicit discrete-event
checks; assigning one sampled passenger a large expansion weight does not prove
that boarding and congestion remain equivalent.

Preserve fleet availability, physical empty movements, dispatch, depot returns,
class restrictions and time-dependent supply. Scale observed demand, stock and
operating service only through a documented, consistent mechanism.

## Demonstrate equivalence

Before a long run, profile the complete input package and a bounded execution.
Report agents, events, departures, vehicle types, memory, disk and time per
iteration. Derive the cost estimate from these measurements.

Use paired, nested population samples, fixed network construction, common
behavioural inputs and registered seeds. Replicates must measure stochastic
variation. A higher-fidelity reference must be available for each claim; if
full-region reference execution is infeasible, validate representative
corridors and retain the limitation on the whole-region claim.

Compare distributions and spatial/time cells, not only city totals: mode shares,
OD, travel times, link flows and queues, station loads, crowding, waits, denied
boarding, transfers, fleet utilisation, empty travel and freight movements.
Separate expansion-weight arithmetic from observed physical behaviour.

Choose equivalence margins from measurement uncertainty and the intended
decisions before examining the experimental outcomes. No tolerance is selected
here without evidence. Report confidence intervals and failed cells for every
mode. A sample is acceptable only when these predeclared checks support it.

## Current implementation evidence

The population sampler now reads XML structure rather than tab-indented lines.
The old reader could emit an empty file from a valid compact population even
at a 100% fraction, and could miss household couplings when attributes appeared
in another order. The streaming reader retains household clustering, the
shared-driver exclusions and the existing nested inclusion hash. It preserves
population metadata and person data, and publishes an output only after the
whole input passes parsing. Duplicate/missing person IDs, ambiguous sampling
attributes and invalid fractions are refused. Tests cover formatting variants,
coupled households, nesting and atomic failure. Eight old/new comparisons on
6,000 synthetic people retained identical IDs and person subtrees apart from
inter-person whitespace. This is data-integrity evidence, not a demonstration
of rare-mode coverage or statistical equivalence for Mumbai.

The transit-capacity sampler previously scaled only the first capacity
attribute. It now parses XML and scales seated and standing components in both
supported MATSim capacity formats, preserving zero components. Regression tests
cover the repair. Historical runs remain unchanged and do not validate the
repaired model. Integer floors and all other scaling mechanisms still require
the experiments described above.

The calibration objective now distinguishes passing scores from complete mode
coverage. Missing, unscorable or non-finite mode errors prevent `goal_met`, even
when every remaining score is within the pass band. This checks coverage of the
city's declared target modes; the mode inventory must itself be complete. A fit
statistic still cannot certify run completion or fulfil the other requirements.

The run-input assembler now supports
[explicit vehicle capacity profiles](../../../docs/transit_fleet.md), as well as
the existing broad-mode capacities. Mumbai's distinct bus configurations,
train formations and vessels still need evidenced per-vehicle assignments. The
[manufacturer evidence audit](../data/processed/acquisition/bus_capacity_evidence_audit.json)
already contains different seating configurations and a conflicting brochure.
Unknown standing capacity must not become zero. The explicit path refuses
missing active assignments, invalid capacities and mismatched mapped-build
hashes. Mumbai does not yet supply a validated assignment file or the physical
base-type configurations. Scaling a generic average correctly would still give
the wrong boarding and crowding behaviour.

## What the first citywide case measured (21 September 2026, §9.205)

The core plans are written at `B.population.plans_build_fraction` 0.05 by the
harness's own nested household hash (1,352,144 persons in 303,384 households),
and `20260921T220701_2it_0.1pct` ran 0.001 of the core (26,884 persons, 2
iterations, 354 s, 88 s an iteration) through the harness on the full mapped
regional network (846,699 links) and combined feed. It is a structural check
and nothing else, and it measured the two constraints that decide the fraction:

- **Memory.** 17.30 GiB peak against 13.74 GiB for a negligible population:
  about 140 KB an agent at two plans, the reference city's rate. The heap rule
  is now measured on two points (`RUN.machine.heap_floor_gib` 13.7,
  `RUN.machine.heap_per_fraction_gib` 3,600): 1 % of the core needs 50 GiB,
  5 % needs 194 GiB, 25 % (the reference city's fraction) 914 GiB. The host has
  63 GB.
- **Flow granularity.** The capacity factors are identities on the fraction, so
  at 0.001 a 1,800 veh/h lane passes 1.8 vehicles an hour and every second car
  on a link waits half an hour: the case's median car trip of 4.5 km took
  194 min and its pt trips 13 h, and 5,454 agents were removed stuck. That is
  the discrete queue at a fraction far below what a reading can stand, not the
  city. The reference city reads at 25 %; the MATSim literature's floor is
  about 10 %.

So on this host Mumbai can execute at about 1 % and read at none: a defensible
reading needs either a host of the order of 200-900 GB, or a leaner agent (plan
memory, event handling and telemetry measured per agent) and the equivalence
experiments above at the fraction that then fits. That is decision D14, the
user's. No fraction has been shown to preserve behaviour.

