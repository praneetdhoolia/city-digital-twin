# Sampling and comparability families — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 21 September 2026 (fifty-sixth session) · **Record read through:** §9.203 · **Written against family:** `F35`

## What is built

- **Standing room is scaled with the seats** (§9.203, §9.185, #237): the old regex scaled only `seats`; the F35 result ran Bus 11 + 18, Tram 15 + 210, Rail 24 + 48, Ferry 37 + 51 at 25 % — standing room at full size, crowding unable to bind on tram, rail or ferry. `scale_transit_capacity` now parses the XML and scales both components (Tram 15 + 52), floor `RUN.sample.transit_capacity_floor`. **Every arm after it opens a family; nothing after compares with F35.** The rewrite keeps the identical 155,233 persons at 25 % (old beside new).
- **The sampling unit is the household.** `RUN.sample.unit` = `household` (`derived`): a household is kept when blake2b(`household|<id>|RUN.machine.seed`) / 2^64 falls below the fraction, so the sample nests (1 % is a strict subset of 10 %) and every household-coupled mechanism is fraction-independent (§9.45). External and through tiers hash on their own id. `RUN.machine.seed` = 20260810 = `B.seed.master`.
- **Lift couplings extend the unit**: the sampler union-finds (`householdId`, `liftHousehold`) pairs; shared-ride driver households are named in `sharedDriverHousehold` and excluded from those unions (§9.60, §9.127).
- **A shared pair shares a hash bucket the width of the campaign fraction.** `B.ride.shared_lift_hash_bucket` **0.25** (`assumed`, sweep [0.05, 0.25]; 0.05 is the control, §9.129, §9.149): the fourth binder pass (`B.ride.shared_lift_scope` = `same_sa2_od`) binds a passenger only to drivers in the same bucket, so a nested sample at a multiple of the width keeps both members. A 1 % smoke breaks pairs and never reads pairing (§9.128); the binder records the seed it hashed under (§9.127).
- **The sample count is asserted at rebuild**: a 10 % draw must land within 8.5–11.5 % of persons (§9.127).
- **Run identity is the full key.** `find_completed` matches scenario, day, fraction, iterations, seed, `--set` overrides, the warm-start key, `controler_sha256`, `values_sha256` (§9.104) and `inputs_sha256` (§9.127), declared in `config/schema/outputs/meta.schema.json` and `run.schema.json`; `calibrate.py` passes the same hashes, so a search candidate cannot match the previous family (§9.169). Never compare across fractions, families or a network build (§3.5, §9.10, §9.12).
- **Run directories are named by the runner** `<launch>_<iterations>it_<pct>pct`; a dead run is renamed `aborted_<name>` with `status` and `cause`; a stopped run also carries `_run.json`, whose `completion` is the result gate (§9.65, §9.66).
- **The run index** `results/INDEX.md` / `INDEX.csv` (`src/analyse/build_run_index.py`, #77) carries every run's family, read from `docs/run_families.json` and never re-derived, and its validity (`aborted` / `failed`, `probe` under 250 iterations, `stopped-arm` with `completion` and `reached_iteration`, `arm` with relaxation).

## The families

A family boundary is a recorded model, data or network change after which nothing compares to what ran before it (§3.5). A run belongs to the newest family whose `from_launch` is at or below its launch stamp; the `overrides` block of `docs/run_families.json` wins where the record attributes a run explicitly. A new family is declared in that file in the same change as its `DECISIONS.md` entry.

| key | opened (`from_launch`) | boundary | decisions_ref |
|---|---|---|---|
| `F1-postrebuild-prerepair` | 20260816T000000 | the issue #32 network rebuild; pilot arms `conv1000_10pct` / `conv1000_25pct` | §9.42, §9.43 |
| `F2-ride-binding` | 20260818T190000 | ride sampler, escort binding, age structure, household sampling unit | §9.44, §9.45, §9.46, §9.47 |
| `F3-all-physical` | 20260820T000000 | freight and all-physical modes | §9.49, §9.52, §9.53, §9.55 |
| `F4-walk-wedge` | 20260821T100000 | walk-wedge repairs, lifts, PassingQ; its two completed arms are the pre-repair baseline | §9.58, §9.59, §9.60, §9.61, §9.63 |
| `F5-ride-walk-repairs` | 20260824T000000 | round-trip ride bindings, short-trip mixture; closed unmeasured | §9.68, §9.69 |
| `F6-all-modes-activated` | 20260825T090000 | explicit signals, priority, crossings, native dwell, taxi activated | §9.76, §9.77 |
| `F7-ride-alternative-retained` | 20260826T060000 | the unpaired-ride fallback keeps the plan's ride alternative | §9.81 |
| `F8-escort-coherence` | 20260826T230000 | the escort and the escorted take one mode | §9.82 |
| `F9-joint-demand-gradient-gates` | 20260827T120000 | joint household tours, gradient link speed, age gates | §9.84 |
| `F10-declared-pair-identity` | 20260828T210000 | the declared pair survives translation (`boundDriver`); closed unmeasured | §9.85 |
| `F11-taxi-physical` | 20260828T220000 | taxi a physical qsim main mode; closed unmeasured | §9.86 |
| `F12-scats-adaptive` | 20260828T230000 | SCATS adaptive signals, derived crossings, derived ferry target | §9.88, §9.89, §9.90, §9.93 |
| `F13-taxi-fleet` | 20260829T170000 | finite sample-scaled taxi fleet | §9.99 |
| `F14-servable-pool-motorbike-carve` | 20260830T021300 | joint-binding candidate-pool filter, motorbike carve rebuild | §9.116, §9.117, §9.118, §9.119 |
| `F15-choice-set-seed-bound-ride` | 20260830T124000 | full-choice-set seed, per-trip bound ride/drive | §9.120 |
| `F16-choice-set-seed-drawn-order` | 20260830T133000 | the first-executed seed plan drawn uniformly | §9.121 |
| `F17-network-direct-walk` | 20260830T140500 | the PT router's direct walk on the walk network (#94) | §9.121 |
| `F18-shared-rides-carves` | 20260830T161200 | shared rides bound; motorbike and resident truck carves | §9.122, §9.124, §9.125 |
| `F19-driver-detour` | 20260830T170742 | declared pairs served by the driver's detour | §9.128 |
| `F20-bucket-rule-carve-pool` | 20260830T184954 | the same-bucket coupling rule; carves solved on the drawn pool | §9.129 |
| `F21-licence-rate-demand` | 20260830T222641 | demand rebuilt on the measured licence rate; arm `20260830T222642_300it_10pct` | §9.131, §9.133 |
| `F22-pt-fares-priced` | 20260831T164923 | every pt journey charged its Opal fare (`citysim.PtFareChargeHandler`); first arm at 25 % | §9.135 |
| `F23-behaviour-channels` | 20260901T133356 | bike stress, derived parking search time, income-scaled money sensitivity; gate arm `aborted_20260901T165115_300it_25pct` stopped at 100 (§9.139) | §9.138 |
| `F24-balanced-destinations` | 20260904T181133 | destinations balanced at both ends; circuity re-measured; a refused taxi trip keeps taxi in memory (#113) | §9.142 |
| `F25-ride-reaches-plan-memory` | 20260905T125346 | every bound ride trip reaches plan memory (`B.mode.partial_bind_base`, `B.activity.escort_exclusion_scope` = `subtour`, no passenger offered as driver) | §9.143 |
| `F26-a-driver-owns-a-car` | 20260906T013531 | every declared ride driver owns a car; opened at the REBUILD | §9.144 |
| `F27-a-household-drives-the-cars-it-owns` | 20260906T211406 | coherence re-proposes declared pairs only (`B.ride.coherence_scope`); census roster (`B.population.vehicle_roster`); a carve never draws a bound passenger; opened at the rebuild | §9.146 |
| `F28-the-car-waits-only-for-a-car` | 20260907T025531 | the household car constraint car-only (`HouseholdCarDepartureHandler`), `RUN.qsim.vehicle_behavior` back to `teleport`; opened at the FIX | §9.148 |
| `F29-lifts-are-the-long-trips` | 20260907T114503 | `B.ride.shared_lift_hash_bucket` 0.05 → 0.25, `B.ride.shared_lift_priority` = `longest_first`; opened at the rebuild | §9.149 |
| `F30-an-escort-is-priced-as-an-escort` | 20260907T144147 | `EscortCoherenceListener` iterates a `TreeMap` (#150); the purpose-map and VOT re-key moved nothing; opened at the rebuild | §9.151 |
| `F31-the-car-router-reads-only-cars` | 20260908T095937 | `RUN.travel_time.filter_modes` true (#154); opened at the arm `20260908T100009_300it_25pct` | §9.154, §9.156 |
| `F32-crowding-reaches-scoring` | 20260909T011135 | `citysim.PtCrowdingScoring`; the coherence listener stops at the cutoff; `GenericRouteTeleporter` refuses per mode; opened at probe `20260909T011135_4it_25pct`; arm `20260909T015217_300it_25pct` is a RESULT | §9.158, §9.160 |
| `F33-the-passenger-is-put-on-ride` | 20260910T203622 | demand rebuilt: `B.mode.bound_passenger_placement` = `every_plan`, the placement loop no longer discards a day, `routingMode` on every leg; opened at probe `20260910T203622`; no reading | §9.164 |
| `F34-walk-has-a-footpath-network` | 20260912T062457 | the footpath network (40,203 ways, 181,892 → 368,230 links), pt access/egress walks executed (#167), crossings with Cobbora freight (#184); CLOSED with no arm | §9.167, §9.168 |
| `F35-the-engines-route-what-they-remode` | 20260912T184108 | the taxi and ride engines route what they re-mode; opened at the FIX; arm 0 `20260912T202242_300it_25pct` ran to 300 in 30.35 h, a RESULT | §9.168, §9.169 |

Overrides in the file: three dead 30 Aug launches are attributed by name (`aborted_20260830T163010_300it_10pct` to F18; `aborted_20260830T170153_300it_10pct` and `aborted_20260830T170743_300it_10pct` to F19); `aborted_20260818T162538_1000it_25pct` is left unattributed because the record cannot settle it.

## What is measured

- **"One build per comparison" was broken at the READER, not the mapper** (§9.169): `extract_metrics` read pt submodes through the city's schedule path, overwritten by the F34 rebuild; every reader now opens the run's own `output/output_transitSchedule.xml.gz`.
- pt2matsim: stop-to-link assignment agrees 100.000 % between builds, route link sequences 81.9–82.3 % (§3.5); one build per comparison.
- Bucket width costs candidate supply, not bound trips (§9.129: 98,549 → 73,509 servable at 0.05, bound 59,7xx throughout).
- The last asserted sample was 62,134 of 620,553 persons, 10.01 % (§9.127); the population has since been rebuilt (§9.131) and arm 0 kept 155,233 of 622,318 at 25 % (`20260912T202242_300it_25pct`, §9.169).

## What is open

- **The first 25 % arm with standing room scaled** measures what F35 could not: peak standing occupancy per vehicle type and whether `C.crowding.standing_multiplier` moves a score (#237, `AWAITING-RUN`). It opens F36.
- **F35 is open and has its reading** (§9.168, §9.169): opened at the controler fix `20260912T184108` before any F34 arm; its probes `20260912T184134_4it_1pct` and `20260912T185005_4it_25pct` (460.0 s recurring) are citable for a yes/no and a clock. Arm 0 `20260912T202242_300it_25pct` is a RESULT and the CONTROL HALF of the five pairs (#172): each pair opens a family on ONE field, runs 250 (cutoff 200) and differences against arm 0's it.300 reading, the 0.128 pp post-cutoff drift inside the tolerance. No arm was chosen, no approval stands; the routers pair is recommended first (§9.169).
- **F32's result stays a RESULT and is no longer the newest reading** (§9.162, §9.169): `20260909T015217_300it_25pct`, `reached_iteration` 300, 21.5 h, the first `_fit.json` with `is_a_result: true`; it compares with nothing in F35.
- Whether a separate 25 % confirmation arm is still needed now that the loop runs at 25 % (§9.129) is the user's call at convergence.
- The design-effect penalty of household cluster sampling is unestimated and no seed-variance measurement exists; `n_replications` stays 30 (§9.45). The threshold between 10 % and 25 % is unmeasured (§9.12).
- One arm at a time; the machine-level stall that hit two concurrent arms is #66.
- `aborted_20260818T162538_1000it_25pct` stays unattributed to a family.

## Refused — do not re-raise

- Comparing across a sample fraction (§9.10, §9.12), across a family, or across a network build or schedule mapping (§3.5).
- Sampling by person, and a side file for household membership (§9.45).
- A directed closure over driver households: nested, but 17.65 % of persons and weighted to car-owning households (§9.127).
- The at-or-below coupling rule: the count was right, the composition was not (§9.129).
- Reading a 1 % smoke's pairing: 1 % is not a multiple of the bucket width and breaks pairs (§9.129).
- Hand-named run directories and the `--tag` flag (§9.65); a harness that deletes a stale result (§9.65).
- Resuming a record without `values_sha256` or `inputs_sha256` (§9.104, §9.127).
- Deriving a family inside the index from the launch date alone: the JSON is the record (`src/analyse/build_run_index.py`).

## History

- §9.203 — standing room scaled at last
- §9.176 — intro fixed: which runs are results is the board's
- §9.170 — no family opened; a 1 % smoke on the recompiled controler
- §9.169 — F35's arm 0 is a result
- §9.168 — F35 opens at the engines' routed re-mode; arm 0 launched
- §9.167 — F34 opens at the footpath-network rebuild
- §9.166 — the families table rejoined; F33 still has no reading
- §9.165 — F33's arm 0 dies on heap; the family has no reading
- §9.164 — F33 opens at the probe; the demand is rebuilt
- §9.160 — F32 opens at the probe; crowding reaches scoring
- §9.158 — no launch, so no family row; the next arm opens one
- §9.157 — F31's first arm stopped at its gate at iteration 100
- §9.156 — F31 opened at the arm; the car router reads only cars
- §9.153 — F30's first arm stopped at 23 on its own cost
- §9.151 — F30 opens at a rebuild, on the escort listener's draw order alone
