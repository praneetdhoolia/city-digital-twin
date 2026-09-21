# Network-mode vehicle definitions

`RUN.qsim.mode_vehicle_fields` lets a city declare a physical vehicle type for
each of its network routing modes. Both scenario assembly and per-run input
generation resolve the referenced registry fields, so run overlays reach the
vehicle file. The definition follows
[`mode_vehicles.schema.json`](../config/schema/mode_vehicles.schema.json).

A nonempty mapping must cover exactly `RUN.routing.network_modes`. Each mode
needs references for length, width, passenger-car equivalents (PCE), seated
passenger capacity and standing passenger capacity. Capacities exclude the
driver. A zero capacity or zero PCE stays zero. Unknown modes are not assigned
the car's body or PCE.

For example, the structure for a city's additional mode is:

```json
{
  "additional_mode": {
    "length_m_field": "B.additional_vehicle.length_m",
    "width_m_field": "B.additional_vehicle.width_m",
    "pce_field": "B.additional_vehicle.pce",
    "seats_field": "B.additional_vehicle.passenger_seats",
    "standing_field": "B.additional_vehicle.standing",
    "maximum_speed_kmh_field": "B.additional_vehicle.maximum_speed_kmh"
  }
}
```

These example field names are references, not supplied observations or model
values. Each referenced field must exist in that city's registry and carry its
own source, units and uncertainty treatment. References resolve to scalar
numbers. Dimensions and speeds must be finite and positive; PCE and passenger
capacities must be finite and nonnegative. Capacities must be integers.

Dimensions accept `m` or `metres`; PCE accepts `passenger_car_equivalents`;
capacities accept `persons_per_vehicle` or `persons`. A speed cap can use
`maximum_speed_ms_field` with `m/s` or `metres_per_second`, or
`maximum_speed_kmh_field` with `km/h`. Supplying both is an error. Omitting both
leaves the vehicle without a separate cap; link speed still applies. The writer
checks the whole definition before replacing an existing file.

An empty mapping retains the existing vehicle writer during migration. This
keeps existing scenario inputs unchanged; it does not make that writer's fixed
mode vocabulary suitable for a new city. Explicit definitions have no such
fixed vocabulary and emit only the declared routing modes.

A vehicle type is one part of a physical mode. The city must also supply legal
network permissions, demand, scoring, routing travel times and any fleet or
passenger-service mechanism. [Network assembly](network_access.md) can preserve
an upstream permission model without adding fixed companion modes or deleting
disconnected components. Several router/fleet bindings still use fixed mode
lists. Those paths must be extended and validated before an additional mode
can be claimed as simulated. Sample
scaling must not alter a private vehicle's physical body or PCE.

Checks:

```powershell
python -m pytest -q tests/unit/test_mode_vehicles.py
python tests/check_mode_vehicle_loading.py
```

The second check uses the pinned local MATSim stack. It loads synthetic vehicle
definitions and constructs `QVehicleImpl` instances to check PCE, maximum speed
and passenger capacity. It does not execute a city simulation.
