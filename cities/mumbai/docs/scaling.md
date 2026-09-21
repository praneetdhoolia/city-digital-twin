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

The run-input assembler supports
[explicit vehicle capacity profiles](../../../docs/transit_fleet.md), and since
21 September 2026 (9.206) Mumbai uses them: `build_transit_fleet.py` assigns
every one of the 114,670 mapped vehicles a profile whose seats and standing
places are registry fields with their sources - a 12-car EMU 1,168 + 3,816
(Indian Railways' EMU primer), Line 1 200 + 1,300, the BEML 6-car 239 + 1,561,
Line 3 399 + 2,601, Navi Mumbai 150 + 950, the two launches 80 and 100, every
bus 36 + 30 - in place of the mapper's defaults (Bus 70, Rail 400, Subway 300,
Ferry 250, no standing room) every case before it ran on. Which departures run
AC, 15-car or MEMU stock, and which operator's buses carry which body, are not
yet assigned per departure; the bus standing room is the one assumed capacity
(swept 20-45). The
[manufacturer evidence audit](../data/processed/acquisition/bus_capacity_evidence_audit.json)
still holds conflicting seating claims and no standing capacity. Scaling a
generic average correctly would still give the wrong boarding and crowding
behaviour, so the explicit path stays per configuration.

## What the citywide cases measured (21-22 September 2026, §9.205, §9.206)

The core plans are written at `B.population.plans_build_fraction` 0.05 by the
harness's own nested household hash (1,352,144 persons in 303,384 households).
`20260921T220701_2it_0.1pct` ran 0.001 of the core (26,884 persons) and two
1 % cases ran 0.01 (269,690 persons) with plan memory 5:
`20260921T231313_4it_1pct` on the mapper's default fleet at full PCE and
`20260922T005949_4it_1pct` on the evidenced fleet with every transit PCE
scaled by the fraction. All three are structural measurements, not readings.

- **Memory.** §9.205's 140 KB an agent was read from pre-collection peaks,
  which under ParallelGC with `-Xms = -Xmx` track the heap GIVEN (16g peaked
  at 13.74 GiB, 24g at 17.30). The live set after a full collection is 7.4 GiB
  with no population, 7.8 with 26,884 agents at two plans (18 KB an agent) and
  15.5 GiB with 269,690 agents at about 2.2 plans (31 KB an agent, ~14-19 KB
  a plan). The heap rule is `RUN.machine.heap_floor_gib` 7.4 +
  `RUN.machine.heap_per_fraction_gib` 2,400 × fraction at plan memory 5: 1 %
  needs 31 GiB, 2 % 55, 5 % 127, 10 % 247. The host has 63 GB.
- **Flow granularity.** Both 1 % cases gridlock. The first removed 122,192
  agents stuck and held 154,759 en route at 36:00; its cause was the transit
  fleet's road space - 114,670 daily departures at pt2matsim's PCEs on links
  whose flow capacity is 0.01 of the real one, a bus taking 2.8 of a lane's 18
  vehicles an hour - which `RUN.sample.transit_pce_scaling` retires. The
  second, corrected, still removed 110,173 and held 72,982 en route: at 0.01
  every link is a gate of one vehicle per 200 s with storage for one, and the
  mapped network's median link is 65 m (41 % under 50 m; 41.5 % of nodes are
  pass-through, so a merge doubles the median and still stores a sixth of a
  vehicle at 1 %). Trips completed rose from 85,255 to 149,502 and the
  reporter's iteration-4 reading put metro inside its pass band (-2.9 %) and
  bus at +18.3 %, with heavy rail at -83.9 % and nine of ten modes past the
  bar. The reference city reads at 25 %; the MATSim literature's floor for a
  congested network is about 10 %.

So on this host Mumbai executes at 1 % and reads at none: a defensible
reading needs a host of the order of 384-512 GB for a 10 % core (2.7 M
agents, 247 GiB live) - decision D15, taken by the user on 22 September 2026
(§9.207). No fraction has been shown to preserve behaviour.

## The pass-through merge, measured and not applied (22 September 2026, §9.207)

The merge D15 named as its diagnostic was measured before any run
(`python src/build/merge_pass_through_nodes.py <base network> <out> --max-length 500`,
20 s on the 846,699-link base network): a node merges only when it passes
traffic straight through (one link in and one out, or the two directions of
one two-way street), the two links agree on speed, capacity, lanes, modes and
OSM class, neither carries or is named by a turn restriction, and the merged
link stays under the converter's own `A.network.max_link_length_m` (500 m),
so every road, route, mode and metre stays (101,306 km before and after).
Under those rules **37,122 of 377,443 nodes merge (9.8 %) and 67,202 of
846,699 links fold away; 33,923 more nodes are held by the 500 m cap and 349
by turn restrictions; the median link moves 62.7 m to 69.0 m.** The lever is
weak: the storage a 1 % link offers is not changed by a tenth-of-a-node merge,
and the user chose to keep the network exactly as converted so the map draws
every vertex as OSM holds it. The script stays as the measurement's
reproduction; nothing wires it into a build.
