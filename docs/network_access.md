# Preserving mapped mode permissions

`A.network.mode_access_strategy` controls which permission and connectivity
changes the run-input assembler may make to a scenario's mapped network.

| Strategy | Assembly behaviour |
|---|---|
| `preserve_mapped` | Keeps every mapped link's mode permissions, direction and presence. It adds no companion modes or reverse links and performs no largest-component pruning. |
| `legacy_companions` | Retains the existing car-companion, road-class exclusion, nonmotor reverse-link and largest-component rules. |

The selected value is a city registry declaration. A city using
`preserve_mapped` must supply a network whose permissions already reflect its
evidence. This includes legal access, direction-specific restrictions, special
vehicle classes and any time-dependent rules relevant to the simulated period.
Preservation does not establish that the upstream permissions are correct.

In preservation mode, assembly counts permitted links for every mode and
refuses a requested `RUN.routing.network_modes` entry with no permitted link.
It reports the counts under `links_touched` in the assembly report. A positive
count establishes presence only. Route connectivity, activity and stop access,
turn restrictions and actual mobility still need validation. Disconnected
components remain visible; retaining them does not prove the runtime can route
all requested journeys between them.

Declared scenario changes to lanes, capacity, kerbside attributes and turn
restrictions still apply. These are separate from broadening a mode's access
or automatically adding reverse paths. A preservation-mode network is not
silently repaired by admitting vehicles to prohibited roads.

This policy applies when a scenario network is assembled. A run overlay cannot
change a network that has already been built; use the existing rebuild and
family-comparison rules for any change to this policy or its upstream network.
Vehicle types are supplied separately through the
[network-mode vehicle contract](mode_vehicles.md).

The regression checks cover prohibited modes, one-way access, disconnected
walking links, lane patches and refusal of missing routing modes:

```powershell
python -m pytest -q tests/unit/test_mapped_mode_permissions.py
```

## Connecting activities to distinct mode networks

`RUN.routing.activity_link_assignment` is emitted as `activityLinks.assignment`
and read before the controller is constructed. `common_modes` retains the
existing assignment: an activity connects to a road that carries all the
person's existing and potentially chosen network modes. This can move its road
connection far from its coordinate where modes have different legal extents.

`mode_specific_access` leaves activity coordinates and link IDs unchanged.
The mode's access/egress router chooses its permitted boarding and alighting
links and supplies the intervening journey. This policy requires
`routing.accessEgressType` to be `accessEgressModeToLink` or
`accessEgressModeToLinkPlusTimeConstant`. The controller refuses an undeclared
assignment, or a mode-specific assignment without those access legs, before
the activity assigner changes a plan. Regenerate configs made before this
parameter existed; the new controller requires the explicit module.

This setting does not supply a fleet, confer permission to enter a restricted
road or prove every access journey can be routed. Walking permissions,
connectivity, coordinate-to-link stubs and actual mobsim execution remain
validation obligations. Existing cities keep their declared assignment;
changing it for a calibrated city changes the model and requires a comparison
family boundary.

The local native check loads the registry-emitted policy, retains the legacy
common-link result, and tests a synthetic network with different road access
for two vehicle classes. MATSim produces network walking access and egress
around a vehicle route whose every link admits that vehicle class. It also
refuses incompatible and undeclared policies. This is a routing test, not a
city simulation:

```powershell
python tests/check_activity_links.py
```

Add `--mobsim` to execute the synthetic journey in QSim using the project's
`TolerantAgentSource`. The event checks require all walking/vehicle/walking
legs to arrive, their insertion and arrival links to match the routes, and
every traversed link to admit the actual vehicle mode. They refuse stuck and
traveller-teleport events. Walking proxy vehicles use the existing vehicle
placement policy; this does not represent passenger fleet dispatch. The check
has one traveller, no sampled demand and no congestion calibration. It does
not execute the complete project controller or a city scenario.

## Compressed source access tags

The native OSM inputs declared by a city may be plain XML or gzip-compressed
XML. Both the merge and the later pedestrian/cycle access reader explicitly
open gzip streams. Passing a compressed filename straight to the pinned XML
reader failed before access restrictions could be applied. A regression checks
that compressed and plain copies produce the same selected tags, including
conflicting tags across source files. The reader was also exercised against
the complete Mumbai native input. This verifies source reading; it does not
establish the correctness or currency of OSM access permissions.

## Explicit access evidence before conversion

`src/build/osm_access_evidence.py` resolves the documented OSM access hierarchy
for pedestrians, bicycles and distinct motor-vehicle categories. Specific tags
override broader baseline tags. Public-service vehicle tags have separate bus,
taxi, minibus and shared-taxi children. An unknown child value remains unknown;
it does not inherit a broader grant. These are OSM categories, whose mapping to
local legal classes and simulation modes still needs city evidence.

The resolver returns a source key, raw value and interpretation, not a routing
permission. It keeps private, destination, customer and permit access dependent
on the traveller's purpose or entitlement. Conditional, directional and lane
qualifiers remain unevaluated. The disputed scope of `motorcar` for other
double-tracked vehicles is flagged for review. No road-class default is added.
The conventions and scope limits come from the OSM documentation for
[access](https://wiki.openstreetmap.org/wiki/Key:access),
[public-service vehicles](https://wiki.openstreetmap.org/wiki/Key:psv) and
[motorcars](https://wiki.openstreetmap.org/wiki/Key:motorcar).

Access evidence must be combined with direction, physical suitability, node
barriers, turn restrictions and applicable legal notices before network export.
It does not change the existing conversion or assembly strategies. Unit checks
cover hierarchy exceptions, malformed tags, restricted purposes, unresolved
qualifiers and the distinction between tagged access and a routable permission.

## Native geometry before network conversion

`src/build/osm_way_geometry.py` reads road/path or rail geometry from the city's
native OSM inputs. It retains every selected way's ordered node references and
tags, including lifecycle tags and area boundaries. Junction identity comes
from shared native node IDs. Coincident coordinates and intersecting lines do
not create a connection. Geometry is not clipped, snapped, simplified or pruned.

Both geographic coordinates and the city's projected metre coordinates are
retained. Each adjacent-node segment has projected and geodesic lengths; neither
includes vertical grade. Zero-length segments remain visible for review. A
geographic or non-metre output CRS, conflicting entity copies, repeated IDs or
missing node references cause extraction to fail before replacing output files.

Node tags retain barriers, signals and crossings for later operating rules.
Area boundaries and inactive features remain labelled geometry evidence and
must not become ordinary operating links. A native node shared by road and rail
does not itself establish a passenger transfer or crossing permission. Access,
directions, speeds, capacities and control behaviour remain separate inputs.

The railway compatibility entry point delegates to this shared reader. Tests
cover grade-separated coincidence, real shared junctions, road/rail coordinate
agreement, barriers, area boundaries, lifecycle features and repeatable output.

## Retaining controls during geometry reduction

The pinned converter's `keepPaths=false` removes intermediate control nodes
from a synthetic way containing a gate, a traffic signal and a railway crossing.
`keepPaths=true` retains their coordinates, but neither setting copies their
node tags into the MATSim network. The probe in
`tests/check_osm_control_nodes.py` pins these observations to the converter jar
hash. Its passing result documents this limitation; it is not network acceptance.

`src/build/protected_way_segments.py` partitions native ways at their endpoints,
shared and repeated node identities, every tagged node and caller-supplied
anchors. A closed chain retains an existing interior node to avoid replacing
positive geometry with a self-loop. Every original adjacency remains represented
once and in source order. Internal shape points stay in the chain geometry.
Source tags, restriction members and stop/access anchors must remain available
to the network builder; retained coordinates alone do not implement controls.

This partition is a geometry candidate, not a replacement converter or a claim
of simulation equivalence. Combining segments can change queues and discrete
time-step effects. Check those effects before adopting a reduced network, and
add any stop or activity anchors introduced by later mapping. The partition
does not choose speeds, capacities, legal permissions or control rules.


## Turn-restriction evidence

`src/build/osm_turn_evidence.py` checks relation roles and native junction
membership, and uses ordered full-way geometry for via-way restrictions.
Missing roads, disconnected geometry and ambiguous orientation remain explicit.
Conditional tags and vehicle exceptions retain their original scope; they are
not flattened into a universal turn prohibition. A structurally sound relation
still requires direction, vehicle-class and legal-date checks before export.
Public object histories can diagnose an upstream defect, but an earlier member
set does not authorise restoring a historical restriction as a current rule.
