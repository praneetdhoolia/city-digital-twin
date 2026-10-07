# docs/framework/ — the portable contract, in prose

Six notes that describe what [`config/schema/`](../../config/schema) requires of
any city and how the assembler honours it. They are the framework's, not the
simulator's state: nothing here names a result, a family or a run, and none of
them is rewritten at a handoff. They sat loose at `docs/` root until 8 October
2026, when three project reports in a row found them among the living documents
(the fourteenth, fifteenth and sixteenth reports); `docs/` means the simulator
and its results ([`../README.md`](../README.md)), and these are its contracts.

| Note | Describes | Schema |
|---|---|---|
| [`transit_fleet.md`](transit_fleet.md) | per-vehicle capacity profiles bound to one mapped build | `transit_fleet.schema.json` |
| [`mode_vehicles.md`](mode_vehicles.md) | an explicit physical vehicle type for each network mode, resolved from registry fields | `mode_vehicles.schema.json` |
| [`network_access.md`](network_access.md) | how assembly preserves a city's mapped mode permissions and checks the requested routing modes are present | — |
| [`boarding_fares.md`](boarding_fares.md) | operator-specific distance tariffs, realised money scoring and the routing limitations | — |
| [`person_modes.md`](person_modes.md) | explicit per-person choice sets and the checks on every stored initial plan | — |
| [`hired_fleet.md`](hired_fleet.md) | hired-vehicle supply queues, experienced waits and the limits of pooled dispatch | — |

A city's own values for any of these live under `cities/<city>/registry/`; the
generated field reference (`cities/<city>/docs/reference/CONFIG_REFERENCE.md`)
is where a value is read, never a note here.
