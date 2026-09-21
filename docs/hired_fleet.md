# Hired-vehicle supply pools

The optional `hiredFleet` module limits simultaneous hired trips by mode.
Requests wait inside QSim before the native road handler dispatches them.
The experienced leg includes this wait, so the existing travel-time score
responds to supply. No mode-share target controls dispatch.

This is a pooled supply approximation. It does not locate or route individual
fleet vehicles between requests. Existing vehicle proxies carry the served
passengers on the road network. Empty vehicle movements, shifts and spatial
pickup times require a more complete dispatch model.

## Configuration

Each city declares the controllable values in its registry. The runtime
derivation supplies counts for the explicit simulated population.

| Parameter | Contract |
|---|---|
| `representation` | `absent` disables the mechanism. `pooled_queue` enables it. |
| `vehiclesByMode` | Comma-separated `mode:count` entries. Counts are nonnegative integers. Modes must be network routed and simulated. |
| `maxWaitSeconds` | Finite, nonnegative patience limit in seconds. |
| `turnaroundSeconds` | Finite, nonnegative unavailability after actual arrival, in seconds. |

Counts do not inherit `qsim.flowCapacityFactor`. A city must derive its fleet
counts explicitly and record the population basis, source coverage and rounding.
Zero supply remains zero. A minimum of one vehicle is never imposed.
The older `taxiFleet` limiter cannot also constrain the same taxi supply.

The bounded launcher accepts a hashed `hired_fleet` input file containing a
`vehicles_by_mode` object. It copies the full derivation into the run and emits
the counts with the configuration writer's `derived` provenance role.

## Execution and limits

Each mode has a separate pool. Requests enter a queue ordered by departure
time and person ID. Dispatch occurs at simulation timesteps. A unit remains
occupied until actual arrival, followed by the declared turnaround interval.
Congestion therefore extends occupation. An unfinished journey does not free
its unit before the end of the simulated day. Each iteration starts afresh.

A request that exceeds the patience limit aborts the traveller's day through
native stuck handling. The scorer penalises that outcome. This is not a
same-day fallback choice. The model does not invent a replacement walk or
silently remove the alternative from plan memory.

The completed-run behaviour report retains the declared fleet and each
iteration's requests, dispatches, timeouts, remaining queues and active trips.
It also records total and mean waiting time for dispatched passengers.
The reader rejects missing iterations, fleet-count drift and unbalanced
request accounting. These diagnostics do not establish calibration.

## Native verification

Run `python tests/check_hired_fleet.py` with the pinned toolchain installed.
The check compiles its classes into a temporary directory.
It does not replace the running simulator's compiled classes.

Synthetic cases verify physical road travel, actual-arrival release,
independent pools, supply response, zero supply, timeouts and end cleanup.
The native `EventsToLegs` reader verifies that experienced travel time includes
the queue wait. These cases verify mechanisms, not city-level supply accuracy.
