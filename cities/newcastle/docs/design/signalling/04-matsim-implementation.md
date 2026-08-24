# Implementing signal control in MATSim

How signals are modelled in MATSim, what ships, what must be built, and how it
lands in this repository. Algorithms referenced here are specified in
[05-algorithms.md](05-algorithms.md); the SUMO-removal consequences are drawn
out in [06-project-implications.md](06-project-implications.md).

## 1. The signals contrib (`org.matsim.contrib.signals`)

Originally by Dominik Grether, extended and maintained by Theresa Thunig
(TU Berlin/VSP). Vocabulary:

- **Signal** — one physical light, attached to a *link* or a *lane*.
- **Signal group** — signals that always show the same colour (the unit
  control acts on).
- **Signal system** — one signalised intersection: all groups under one
  controller.
- **Signal control** — the algorithm deciding colours (fixed-time by default;
  adaptive controllers plug in per system).

### 1.1 Data model

Everything lives in a `SignalsData` container
(`org.matsim.contrib.signals.data`), attached to the `Scenario` as a scenario
element, loaded by `SignalsDataLoader`, written by `SignalsScenarioWriter`:

| File | Schema | Content |
|---|---|---|
| `signal_systems.xml` | `signalSystems_v2.0.xsd` | `<signalSystem id>` → `<signal id linkIdRef>` with optional `<lane refId>` and optional turning-move restrictions |
| `signal_groups.xml` | `signalGroups_v2.0.xsd` | grouping of signals into groups per system |
| `signal_control.xml` | `signalControl_v2.0.xsd` | per system a `<signalSystemController>` with `<controllerIdentifier>` and one or more `<signalPlan>`: `<cycleTime sec>`, `<offset sec>`, plan start/end, and per group `<signalGroupSettings refId>` with `<onset sec>` / `<dropping sec>` |
| `amber_times_v1.0.xml` (optional) | `amberTimes_v1.0.xsd` | amber behaviour (`AmberLogic`) |
| `intergreen_times_v1.0.xml` (optional) | `intergreenTimes_v1.0.xsd` | intergreen constraints (`IntergreensLogic`; config `actionOnIntergreenViolation`) |
| `conflicting_directions_v1.0.xml` (optional) | — | conflict matrix (`ConflictingDirectionsLogic`) |

Config module: `SignalSystemsConfigGroup` (`signalsystems`): `useSignalsystems`,
file paths, `useAmbertimes`, `useIntergreentimes`, `intersectionLogic`.

**Lanes are effectively mandatory for protected turns.** Signals usually
control *turning movements*, not whole links. MATSim's core lanes model
(`org.matsim.lanes`, `laneDefinitions_v2.0.xsd`) splits the downstream end of
a link into parallel FIFO queues with their own `toLinks`. Without lanes, a
red left-turn arrow blocks through traffic queued behind it in the single link
FIFO; with lanes each turning queue is separately signalised (Thunig et al.
2019; MATSim book ch. 12). The contrib ships tutorial examples with and
without lanes; the OSM generator (§5) emits both together.

### 1.2 Engine

`org.matsim.contrib.signals.builder`:

- `SignalsQSimModule` installs `QSimSignalEngine` (a `SignalEngine`) into the
  QSim. On `MobsimInitializedEvent` and **every** `MobsimBeforeSimStepEvent` —
  i.e. once per second — the `SignalSystemsManager` fires and each system's
  `SignalController.updateState(timeSeconds)` runs.
- States are pushed to the QSim's `SignalizeableItem` (a QLink or QLane):
  while red, vehicles at that buffer **cannot leave the link**; green restores
  the normal flow-capacity-constrained outflow. This is the whole physics —
  red gates the buffer, nothing else changes.
- Signal state changes are events (`org.matsim.contrib.signals.events`);
  `SignalEvents2ViaCSVWriter` exports for Via; OTFVis supported via
  `OTFVisWithSignalsLiveModule`.

### 1.3 Wiring

Minimal pattern (from `RunSignalSystemsExample` in the contrib):

```java
Config config = ConfigUtils.loadConfig("config.xml", new SignalSystemsConfigGroup());
Scenario scenario = ScenarioUtils.loadScenario(config);
scenario.addScenarioElement(SignalsData.ELEMENT_NAME,
        new SignalsDataLoader(config).loadSignalsData());
Controler controler = new Controler(scenario);
Signals.configure(controler);   // installs SignalsModule + SignalsQSimModule
controler.run();
```

`new Signals.Configurator(controler)` is the variant that registers custom
controllers (§4). Internally `SignalsModule` binds `SignalModelFactory`,
`LinkSensorManager` and `DownstreamSensor` as singletons, builds
`SignalSystemsManager` from data via `FromDataBuilder`, and holds a Guice
`MapBinder<String, SignalControllerFactory>` from controller-identifier
strings to factories — different systems can run different controllers in one
run.

### 1.4 Maintenance state

Still in `matsim-org/matsim-libs` master under `contribs/signals` and in every
release train, but **dormant**: 2025–2026 commits are repo-wide refactors and
chores only; no feature development since the Thunig era (~2019–2020). Treat
as *stable but unmaintained*: fixed-time, SYLVIA and `laemmerFix` work and are
exercised by tests and examples; the fully-flexible Lämmer variant
(`laemmerFlex`) never merged and lives as research code in
`matsim-vsp/teach-telematics`, pinned to an older MATSim.

## 2. Controllers that ship

Package `org.matsim.contrib.signals.controller`, interface `SignalController`.

### 2.1 Fixed-time

`DefaultPlanbasedSignalSystemController` — executes `signal_control.xml` plans
verbatim: cycle, offset, per-group onset/dropping seconds.

### 2.2 SYLVIA (`controller.sylvia`) — the SCATS-tactical analogue

Identifier `"SylviaSignalControl"`; classes `SylviaSignalController`,
`SylviaPreprocessData`, `SylviaSignalPlan`, `SylviaConfigGroup` (module
`actuatedSylviaSignals`). After the commercial SYLVIA method (Schlothauer &
Wauer); MATSim implementation Grether, Bischoff & Nagel (2011).

A traffic-actuated gap/presence-extension controller **inside a fixed-time
plan**: the plan is compressed to minimum greens (5 s standard), producing a
shortened cycle plus **extension points**; at each extension point the green
is prolonged second-by-second while vehicles are detected within
`sensorDistanceMeter` (default **10 m** — an inductive-loop emulation) of the
stop line, bounded by `maxGreenScale` × the fixed-time green and (default) by
the fixed-time cycle, so **cycle and offsets are preserved** and corridor
coordination survives. Optional `checkDownstream=true` extends only if the
downstream links can absorb the flow (gridlock guard).

Phase order and stage composition never change — SYLVIA redistributes green
*within* the engineered plan. Functionally this is **SCATS's tactical layer**
(gap-out, time returned to the through movement) with the fixed plan standing
in for the strategic layer. Cottbus benchmark: −32% total delay vs fixed-time,
nearly matching fully-adaptive Lämmer (−35%) (Thunig, Kühnel & Nagel 2019).

### 2.3 Lämmer (`controller.laemmerFix`)

`LaemmerSignalController`, `LaemmerConfigGroup` (module
`adaptiveLaemmerSignals`). Lämmer & Helbing (2008); MATSim implementation
Kühnel, Thunig & Nagel (2018), extended Thunig et al. (2019). Two regimes
(see [05-algorithms.md](05-algorithms.md) for the maths): an **optimising
regime** (serve the stage with the highest clearance-efficiency priority
index, with a switching penalty) and a **stabilising regime** (every approach
served at least once per maximal service interval via a FIFO stabilisation
queue); under sustained overload it degenerates gracefully into
fixed-time-like periodic service. Parameters: `activeRegime` (COMBINED |
OPTIMIZING | STABILIZING), `desiredCycleTime` (default 90 s),
`maximalCycleTime` (default 135 s), `intergreenTime` (5 s),
`minimalGreenTime` (5 s). Requires **fixed signal stages** (non-conflicting
movement groups) as modelling input.

### 2.4 Sensors (`org.matsim.contrib.signals.sensor`)

- `LinkSensorManager` — an events-based virtual detector layer
  (`LinkEnterEvent`/`LinkLeaveEvent`, lane variants, vehicle enter/leave
  traffic). API: `registerNumberOfCarsMonitoring(linkId)`,
  `registerNumberOfCarsInDistanceMonitoring(linkId, d)`, per-lane variants,
  `registerAverageNumberOfCarsPerSecondMonitoring(...)` for arrival rates;
  queries `getNumberOfCarsInDistance(...)`, `getAverageArrivalRateOnLane(...)`.
  `CarLocator` decides whether a vehicle is within distance d of the stop line
  from its entry time and free-flow speed — MATSim vehicles have no position
  within a link, so "within d" is a free-flow-time approximation, and the
  forecast horizon is limited by link length (short links = short horizons).
- `DownstreamSensor` — occupancy check on receiving links
  (`linkEmpty(linkId)`, threshold hard-coded at 0.75 of storage capacity),
  plus whole-system convenience methods. The SCATS "exit blocked" analogue;
  used by SYLVIA's `checkDownstream` and available to custom controllers.

## 3. What does NOT exist

- **No SCATS implementation for MATSim** — none published, anywhere.
- **No transit signal priority out of the box** — Thunig et al. (2019)
  explicitly list PT prioritisation as future work; nothing landed since.
- **SCATSIM (software-in-the-loop, the fidelity gold standard) does not
  interface to MATSim** — only Aimsun Next, PTV VISSIM, Paramics, Commuter.
  It exchanges detector actuations for signal-group states every second over
  TCP/IP and requires the real regional personality data (`.tc`, `.lx`,
  `.ram` files) plus a 1:1 mapping of every controller, group and detector.
  Even if the interface existed, the input data is the purchasable/restricted
  set in [03-data-availability.md](03-data-availability.md). True SCATS
  fidelity is off the table for MATSim; the honest target is *SCATS-like
  behaviour with declared, swept parameters*.

## 4. The custom-controller seam

Small and clean — this is where SCATS-like strategic control and tram priority
would be built:

```java
public interface SignalController {
    void updateState(double timeSeconds);   // called every sim step (1 s)
    void addPlan(SignalPlan plan);
    void simulationInitialized(double simStartTimeSeconds);
    void setSignalSystem(SignalSystem signalSystem);
}
public interface SignalControllerFactory {
    SignalController createSignalSystemController(SignalSystem signalSystem);
}
```

Extend `AbstractSignalController`; drive groups with
`signalSystem.scheduleOnset(...)` / `scheduleDropping(...)` (as SYLVIA does);
inject `LinkSensorManager` / `DownstreamSensor` / `Scenario` into the factory;
register:

```java
Signals.Configurator c = new Signals.Configurator(controler);
c.addSignalControllerFactory("ScatsLikeControl", ScatsLikeFactory.class);
```

then reference `ScatsLikeControl` as `<controllerIdentifier>` in
`signal_control.xml` for the systems it governs. Tram detection needs no new
infrastructure: transit vehicles are ordinary QSim network vehicles emitting
`LinkEnterEvent`s, so a handler filtered on the tram's dedicated approach
link/lane (or on transit vehicle ids) is a faithful proxy for a SCATS PT
detector or Hurry Call input.

## 5. Generating the input data without phasing

- **From the registry (preferred here):** the A2 values
  (`cycle_time_s`, `phase_split_pct`, `ped_clearance_s`,
  `A.signals.min_green_s`) generate fixed-time plans for the 14 corridor
  intersections directly — the same single source the SUMO `retime_tls` step
  consumed, so the signal assumption stays declared once. Phase *structure*
  (which approaches move together) must come from intersection geometry and
  turn restrictions already in the network layers, analogous to what
  netconvert derived geometrically.
- **From OSM automatically:** the contrib includes
  `org.matsim.contrib.signals.network.SignalsAndLanesOsmNetworkReader`
  (Procedia CS 2021) — generates signal systems, groups, lanes and default
  fixed-time plans from OSM tags. Useful as a cross-check or scaffold;
  output is assumed-labelled input like everything else.
- **Webster's method:** compute cycle and splits from turning counts if any
  become available; also the fallback delay formula for the no-explicit-signals
  representation ([05-algorithms.md](05-algorithms.md) §6).

## 6. The two traps at regional scale

1. **Double counting.** A conventional MATSim link `capacity` already encodes
   average intersection throughput *including red time*. Adding explicit
   signals on top counts the signal twice. When signals are modelled
   explicitly, approach (or lane) flow capacity must be raised to **saturation
   flow** (~1,800–2,050 veh/h/lane) so that red time does the metering.
   Symmetrically: stacking crossing penalties on top of calibrated capacities
   over-penalises ("Modeling Crossroads in MATSim", Procedia CS 2021).
2. **Sample-size discretisation.** With a 10–25% population sample,
   `flowCapacityFactor` scales saturation flow to a few vehicles per green: a
   10–20 s green then discharges 0–2 vehicles and discretisation noise swamps
   the signal effect. Signalised focus areas want a high sample share, or at
   minimum a per-green discharge-count check. **This interacts directly with
   this project's `<pct>` run naming and §0.1b pace band** — an explicit-signals
   arm at a small sample percentage may be structurally unable to show the
   effect it was built to measure.

**Focus-area practice is the norm**: the reference application (Cottbus,
Thunig et al. 2019) modelled signals at 22 inner-city intersections inside a
~10,000-link regional network, everything else capacity-based. The contrib
supports this natively — only systems listed in `signal_systems.xml` are
signalised. For this project the focus area is exactly the **14 corridor
intersections** already inventoried in
`cities/newcastle/data/processed/network/A2_signal_control_corridor.csv`.

Time step: signals and sensors run at 1 s; QSim `timeStepSize` stays 1 s
(the default). Computational cost is localised — per-second updates per
signalised system plus sensor event handling; it grows with signalised
intersection count, not regional network size.

## 7. Integration into this repository specifically

Constraints that bind (none of this is done yet; recorded for the plan):

1. **Toolchain.** MATSim is embedded in the pinned pt2matsim 26.6 **shaded
   jar** (`src/setup/bootstrap_toolchain.py`); the signals contrib is a
   separate artefact the shaded jar does **not** carry. Adopting it means a
   new pinned jar (or a Maven build for the run stack, task B8 in the
   absorption list) — a §14 toolchain change, logged, with runs invalidated
   across the boundary.
2. **QSim assembly risk.** `citysim.CitysimControler` hand-assembles QSim
   components (`JointRideEngine`, `TolerantAgentSource`, etc.).
   `SignalsQSimModule` and the lanes-aware network factory
   (`QSignalsNetworkFactory`) must compose with that assembly — this is the
   highest-risk integration point (task B6's stated reason for deferral) and
   needs a two-vehicle toy probe before any scenario touches it, in the same
   spirit as the PassingQ × NetworkChangeEvents probe planned for level
   crossings.
3. **Registry discipline.** Every controller parameter (min green, sensor
   distance, `maxGreenScale`, desired/max cycle, extension window, detection
   distance, priority conditionality) is a declared `cities/newcastle/registry/`
   field with provenance (`literature`: TTD 2018/002 / SCATS 6 FD values) and
   a sweep or held-fixed rule. `check_hardcoding.py` must not gain items.
4. **Sweep discipline.** SCATS phasing stays `unobtained`; an explicit signal
   model does not change that — it changes *where* the swept parameters bite
   (controller inputs instead of scalar delay shares). The corridor result
   remains a band, never a point (§9.21).
5. **Both directions stay honest.** If explicit signals go in, the implicit
   representation must come out on those links: corridor approach capacities
   re-raised to saturation flow, and the run-time decomposition's
   `A.signals.delay_per_intersection_s` no longer *also* applied to the same
   movement — one representation per effect, chosen per scenario, recorded in
   the scenario config.

## Sources

- Signals contrib README: https://github.com/matsim-org/matsim-libs/blob/master/contribs/signals/README.md
- Contrib source: https://github.com/matsim-org/matsim-libs/tree/master/contribs/signals/src/main/java/org/matsim/contrib/signals
- `RunSignalSystemsExample`: https://github.com/matsim-org/matsim-libs/blob/master/contribs/signals/src/main/java/org/matsim/codeexamples/fixedTimeSignals/RunSignalSystemsExample.java
- Tutorial inputs: https://github.com/matsim-org/matsim-libs/tree/master/contribs/signals/examples/tutorial/example90TrafficLights
- API docs (v11.0): https://matsim.org/apidocs/signals/11.0/org/matsim/contrib/signals/package-summary.html
- laemmerFlex research code: https://github.com/matsim-vsp/teach-telematics
- Thunig, Kühnel, Nagel (2019): https://www.sciencedirect.com/science/article/pii/S2352146518306343 (OA PDF: https://api-depositonce.tu-berlin.de/server/api/core/bitstreams/7d6ed653-29fd-427c-9176-9b5df67497a5/content)
- Kühnel, Thunig, Nagel (2018): https://www.sciencedirect.com/science/article/pii/S1877050918304484
- Grether & Thunig (2016), MATSim book ch. 12: http://www.ubiquitypress.com/books/e/10.5334/baw
- Modeling Crossroads in MATSim (2021): https://www.sciencedirect.com/science/article/pii/S187705092100716X
- OSM signals+lanes generator (2021): https://www.sciencedirect.com/science/article/pii/S1877050921007328
- Aimsun–SCATSim: https://www.aimsun.com/technical-notes/running-a-simulation-in-aimsun-next-connected-to-scatsim/ ; https://docs.aimsun.com/next/22.0.1/UsersManual/ScatsInterface.html
- Aldridge SCATSIM: https://www.aldridgetrafficcontrollers.com.au/scats/testing-simulation
- SCOOT & SCATS in VISSIM: https://www.researchgate.net/publication/325094132_Integration_of_SCOOT_SCATS_in_VISSIM_Environment
- Lämmer & Helbing (2008): https://arxiv.org/pdf/0802.0403
