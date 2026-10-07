# Sampling and comparability families — current position

*A position page states the CURRENT truth for one topic. It is rewritten at every `/handoff` that touches the topic; the dated history and every rationale live in [`DECISIONS.md`](../DECISIONS.md) at the sections cited. Which runs are results is the board's fact ([`STATUS.md`](../STATUS.md), the runs block): a run is one only if its `_run.json` says `ran_to_last_iteration`, and nothing measured on an arm that did NOT reach its declared horizon is.*

**Updated:** 8 October 2026 (sixty-fifth session) · **Record read through:** §9.220 · **Written against family:** `F39`

## What is built

- **Standing room is scaled with the seats** (§9.203, §9.185, #237): the old regex scaled only `seats`, so every F35 arm ran Tram 15 + 210 at 25 % and crowding could not bind on tram, rail or ferry. `scale_transit_capacity` parses the XML and scales both (Tram 15 + 52), floor `RUN.sample.transit_capacity_floor`. **Lands in F36; its first arm measures it.**
- **Transit vehicles' road space is scaled with the sample** (§9.206, `RUN.sample.transit_pce_scaling`): each type's PCE × fraction at launch. Transit runs at full frequency on links whose flow is fraction × real, so a bus at full PCE took 4× its road share at 25 %; MOVES RESULTS, and lands in F36 with #237.
- **The sampling unit is the household.** `RUN.sample.unit` = `household` (`derived`): a household is kept when blake2b(`household|<id>|RUN.machine.seed`) / 2^64 falls below the fraction, so the sample nests (1 % is a strict subset of 10 %) and every household-coupled mechanism is fraction-independent (§9.45). External and through tiers hash on their own id. `RUN.machine.seed` = 20260810 = `B.seed.master`.
- **Lift couplings extend the unit**: the sampler union-finds (`householdId`, `liftHousehold`) pairs; shared-ride driver households are named in `sharedDriverHousehold` and excluded from those unions (§9.60, §9.127). The cluster map is memoised beside the population, keyed by its sha256 (`sample_population.lift_cluster_map`, §9.220): on F39's WEEKDAY plans at 0.25, cold and warm keep the same **158,161** persons with an identical id set and output sha, the cluster pass 74 s → 0.1 s.
- **The families table below is a generated block** (§9.220, #229): `build_status_board.py` writes it from `docs/run_families.json` (`--check` compares and writes nothing); the page's caps exclude it.
- **A shared pair shares a hash bucket the width of the campaign fraction.** `B.ride.shared_lift_hash_bucket` **0.25** (`assumed`, sweep [0.05, 0.25]; 0.05 is the control, §9.129, §9.149): the fourth binder pass (`B.ride.shared_lift_scope` = `same_sa2_od`) binds a passenger only to drivers in the same bucket, so a nested sample at a multiple of the width keeps both members. A 1 % smoke breaks pairs and never reads pairing (§9.128).
- **Run identity is the full key.** `find_completed` matches scenario, day, fraction, iterations, seed, `--set` overrides, the warm-start key, `controler_sha256`, `values_sha256` (§9.104) and `inputs_sha256` (§9.127), declared in `config/schema/outputs/meta.schema.json` and `run.schema.json`; `calibrate.py` passes the same hashes, so a search candidate cannot match the previous family (§9.169). Never compare across fractions, families or a network build (§3.5, §9.10, §9.12).
- **Run directories are named by the runner** `<launch>_<iterations>it_<pct>pct`; a dead run is renamed `aborted_<name>` with `status` and `cause`; a stopped run also carries `_run.json`, whose `completion` is the result gate (§9.65, §9.66).
- **The run index** `results/INDEX.md` / `INDEX.csv` (`src/analyse/build_run_index.py`, #77) carries every run's family, read from `docs/run_families.json` and never re-derived, and its validity (`aborted` / `failed`, `probe` under 250 iterations, `stopped-arm` with `completion` and `reached_iteration`, `arm` with relaxation).

## The families

A family boundary is a recorded model, data or network change after which nothing compares to what ran before it (§3.5). A run belongs to the newest family whose `from_launch` is at or below its launch stamp; the `overrides` block of `docs/run_families.json` wins where the record attributes a run explicitly. A new family is declared in that file in the same change as its `DECISIONS.md` entry.

<!-- generated:families start -->
| key | opened (`from_launch`) | boundary (the ledger's label) | record |
|---|---|---|---|
| `F1-postrebuild-prerepair` | 20260816T000000 | post-rebuild, pre-repair (the 9.43 pilot family) | §9.42, §9.43 |
| `F2-ride-binding` | 20260818T190000 | ride sampler + escort binding + age structure (9.44-9.47) | §9.44, §9.45, §9.46, §9.47 |
| `F3-all-physical` | 20260820T000000 | freight + all-physical modes (9.49-9.55) | §9.49, §9.52, §9.53, §9.55 |
| `F4-walk-wedge` | 20260821T100000 | walk-wedge network repairs + lifts + PassingQ (9.58-9.63) - CLOSED | §9.58, §9.59, §9.60, §9.61, §9.63 |
| `F5-ride-walk-repairs` | 20260824T000000 | round-trip ride bindings + short-trip mixture (9.68-9.69) - CLOSED UNMEASURED | §9.68, §9.69 |
| `F6-all-modes-activated` | 20260825T090000 | explicit signals + tram/bus priority + crossings + native dwell + taxi (9.77) | §9.76, §9.77 |
| `F7-ride-alternative-retained` | 20260826T060000 | the unpaired-ride fallback stops deleting the plan's ride alternative (9.81) | §9.81 |
| `F8-escort-coherence` | 20260826T230000 | the escort and the escorted stop taking different modes (9.82) | §9.82 |
| `F9-joint-demand-gradient-gates` | 20260827T120000 | the demand ceiling mechanism, gradient link speed and the age gates (9.84) | §9.84 |
| `F10-declared-pair-identity` | 20260828T210000 | the declared pair survives translation, and the mutation that breaks it is declared (9.85) - CLOSED UNMEASURED | §9.85 |
| `F11-taxi-physical` | 20260828T220000 | taxi physically simulated in the mobsim (9.86) - CLOSED UNMEASURED | §9.86 |
| `F12-scats-adaptive` | 20260828T230000 | SCATS adaptive signals + derived crossings + derived ferry target (9.88-9.90) | §9.88, §9.89, §9.90, §9.93 |
| `F13-taxi-fleet` | 20260829T170000 | finite taxi fleet, refused request walks (9.99) | §9.99 |
| `F14-servable-pool-motorbike-carve` | 20260830T021300 | joint-binding candidate-pool filter + motorbike carve conversion rebuild (9.116) | §9.116, §9.117, §9.118, §9.119 |
| `F15-choice-set-seed-bound-ride` | 20260830T124000 | full-choice-set seed + per-trip bound ride/drive + declared-pair re-timing (9.120) | §9.120 |
| `F16-choice-set-seed-drawn-order` | 20260830T133000 | F15 stack with the first-executed seed plan drawn uniformly (9.121) | §9.121 |
| `F17-network-direct-walk` | 20260830T140500 | F16 stack with the PT router direct walk evaluated on the network (9.121, #94) | §9.121 |
| `F18-shared-rides-carves` | 20260830T161200 | F17 stack on a demand with shared rides, the repaired motorbike carve at census resolution and the resident truck carve (9.122, 9.124, 9.125) | §9.122, §9.124, §9.125 |
| `F19-driver-detour` | 20260830T170742 | F18 demand with declared ride pairs served by the driver's detour through the passenger's links (9.128) | §9.128 |
| `F20-bucket-rule-carve-pool` | 20260830T184954 | F19 run stack on a demand re-bound under the same-bucket coupling rule with the carves solved on the pool that is drawn (9.129) | §9.129 |
| `F21-licence-rate-demand` | 20260830T222641 | F20 run stack and binder rules on the demand rebuilt from the measured licence-rate population (9.131, 9.133) | §9.131 |
| `F22-pt-fares-priced` | 20260831T164923 | F21 run stack and demand with every pt journey charged its published Opal fare (9.135) | §9.135 |
| `F23-behaviour-channels` | 20260901T133356 | F22 run stack, fares included, with bike traffic stress, derived parking search time and income-scaled money sensitivity (9.138) | §9.138 |
| `F24-balanced-destinations` | 20260904T181133 | F23 run stack on a demand whose destination choice is constrained at BOTH ends, with circuity re-measured on the network that runs (9.142) | §9.142 |
| `F25-ride-reaches-plan-memory` | 20260905T125346 | F24 run stack on a demand where every bound ride trip can actually become a ride alternative (9.143) | §9.143 |
| `F26-a-driver-owns-a-car` | 20260906T013531 | F25 run stack on a demand where every declared driver has a car to drive with (9.144) | §9.144 |
| `F27-a-household-drives-the-cars-it-owns` | 20260906T211406 | F26 run stack plus three physical identities the F26 gate exposed, each with a control member reproducing F26 (9.146) | §9.146 |
| `F28-the-car-waits-only-for-a-car` | 20260907T025531 | F27 stack with the household car constraint enforced car-only, in a departure handler of our own; qsim.vehicleBehavior back to teleport (9.148) | §9.148 |
| `F29-lifts-are-the-long-trips` | 20260907T114503 | F28 run stack on a demand where the shared-ride pass may draw drivers from the whole 25 % sample and binds the longest tours first (9.149) | §9.149 |
| `F30-an-escort-is-priced-as-an-escort` | 20260907T144147 | F29 demand and network with the escort listener drawing in household-id order (9.151) | §9.151 |
| `F31-the-car-router-reads-only-cars` | 20260908T095937 | F30 demand and network with the travel-time table fed by car alone, and the controler recompiled (9.154, 9.156) | §9.154, §9.156 |
| `F32-crowding-reaches-scoring` | 20260909T011135 | F31 demand and network with the controler recompiled: crowding disutility reaching MATSim scoring for the first time (9.158, 9.160) | §9.158, §9.160 |
| `F33-the-passenger-is-put-on-ride` | 20260910T203622 | F33 the demand rebuilt: a declared passenger is put on `ride` in every seeded plan, a tour that will not fit no longer discards the rest of the day, and every leg states its routing mode (9.164) | §9.164 |
| `F34-walk-has-a-footpath-network` | 20260912T062457 | F33 demand and stack on the footpath network: 40,203 harvested footway, path, cycleway, steps, track, pedestrian, bridleway and corridor ways are walk- and bike-capable links, pt access, egress and transfer walks are routed on it and executed by the qsim, and the ride and taxi engines re-mode a whole trip (9.167) | §9.167 |
| `F35-the-engines-route-what-they-remode` | 20260912T184108 | F34's network, demand and settings with the ride and taxi engines routing the trip they re-mode themselves, so PersonPrepareForSim never re-routes a whole plan over a null route (9.168) | §9.168 |
| `F36-the-passenger-is-held-and-bike-pays-for-distance` | 20260922T210005 | F35's network and stack with the demand rebuilt at its roots: escorted members and joint companions held to ride, bike priced by distance, the household tail derived from its declared mean, the ferry target on the disclosed tap-ons, and transit standing room scaled with the seats (9.211) | §9.211 |
| `F37-the-boundary-tier-returns-and-pt-reaches-every-stop` | 20260925T192302 | F36's network and demand with three defects under them removed: the external boundary tier written again, the pt access ceiling measured instead of misderived, and the taxi fleet's wait executed (9.213) | §9.213 |
| `F38-destinations-follow-mobility-escorts-come-home-and-motorbike-is-chosen` | 20260927T125424 | F37's network with a rebuilt demand and choice set: destinations drawn by each person's own mobility, one-way escort bindings on members who could drive released into round-trip lifts, and motorbike chosen instead of carved (9.214) | §9.214 |
| `F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk` | 20260929T053207 | F38's demand and network with the fifteenth report's four corrections, run as a PAIR (D28): the control with the corrections, the treatment adding the headway charge | §9.218 |

39 families in `docs/run_families.json`; the newest is `F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk`. Marked `readings: none` (the scoreboard never presents their arms): `F27-a-household-drives-the-cars-it-owns`, `F34-walk-has-a-footpath-network`.
Overrides in the file (a run the record attributes by name): `aborted_20260818T162538_1000it_25pct` → unattributed; `aborted_20260830T163010_300it_10pct` → `F18-shared-rides-carves`; `aborted_20260830T170153_300it_10pct` → `F19-driver-detour`; `aborted_20260830T170743_300it_10pct` → `F19-driver-detour`.
<!-- generated:families end -->

## What is measured

- **"One build per comparison" was broken at the READER, not the mapper** (§9.169): `extract_metrics` read pt submodes through the city's schedule path, overwritten by the F34 rebuild; every reader now opens the run's own `output/output_transitSchedule.xml.gz`.
- pt2matsim: stop-to-link assignment agrees 100.000 % between builds, route link sequences 81.9–82.3 % (§3.5); one build per comparison.
- Bucket width costs candidate supply, not bound trips (§9.129: 98,549 → 73,509 servable at 0.05, bound 59,7xx throughout).
- **F39's control arm is a RESULT** (`20260929T072135_250it_25pct`, §9.219; its wall is the board's), the first control of a pair since F35 (D28, §9.218). F38 closed with ONE result, completed across warm starts at 75, 175 and 225 (§9.215-§9.217).

## What is open

- **F39's treatment is unrun** (`atap_m1` since §9.219, #175): it needs its probe on the ATAP build and an approval (D29). The controler build moved in §9.219 inside `ServiceQualityScoring` alone, which the control never binds, so the pair stays comparable. #237's standing peak has no reader.
- **F35 is CLOSED with three results** (§9.168, §9.169, §9.176, §9.177), each citable inside F35 and against nothing after `20260922T210005`.
- Whether a separate 25 % confirmation arm is still needed now that the loop runs at 25 % (§9.129) is the user's call at convergence.
- The design-effect penalty of household cluster sampling is unestimated and no seed-variance measurement exists; `n_replications` stays 30 (§9.45). The threshold between 10 % and 25 % is unmeasured (§9.12).
- One arm at a time; the machine-level stall that hit two concurrent arms is #66.

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

- §9.220 — families generated; sampler memoised
- §9.219 — F39's control is a result
- §9.218 — F39 opens as a pair
- §9.217 — F38 closes with a result
- §9.214 — F37 closes with a result; F38 opens
- §9.213 — F36 closes, F37 opens
- §9.212 — F36 priced; arm 0 running
- §9.211 — F36 opens at the roots rebuild
- §9.206 — transit PCE scaled; 1 % gridlock 
- §9.169 — F35's arm 0 is a result
