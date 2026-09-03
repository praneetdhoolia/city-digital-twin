package citysim;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.LinkLeaveEvent;
import org.matsim.api.core.v01.events.PersonArrivalEvent;
import org.matsim.api.core.v01.events.VehicleEntersTrafficEvent;
import org.matsim.api.core.v01.events.handler.LinkLeaveEventHandler;
import org.matsim.api.core.v01.events.handler.PersonArrivalEventHandler;
import org.matsim.api.core.v01.events.handler.VehicleEntersTrafficEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.Node;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Population;
import org.matsim.api.core.v01.population.PopulationFactory;
import org.matsim.contrib.signals.SignalSystemsConfigGroup;
import org.matsim.contrib.signals.builder.Signals;
import org.matsim.contrib.signals.controller.fixedTime.DefaultPlanbasedSignalSystemController;
import org.matsim.contrib.signals.data.SignalsData;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalControlData;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalGroupSettingsData;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalPlanData;
import org.matsim.contrib.signals.data.signalgroups.v20.SignalGroupData;
import org.matsim.contrib.signals.data.signalgroups.v20.SignalGroupsData;
import org.matsim.contrib.signals.data.signalsystems.v20.SignalSystemControllerData;
import org.matsim.contrib.signals.data.signalsystems.v20.SignalSystemData;
import org.matsim.contrib.signals.data.signalsystems.v20.SignalSystemsData;
import org.matsim.contrib.signals.events.SignalGroupStateChangedEvent;
import org.matsim.contrib.signals.events.SignalGroupStateChangedEventHandler;
import org.matsim.contrib.signals.model.Signal;
import org.matsim.contrib.signals.model.SignalGroup;
import org.matsim.contrib.signals.model.SignalPlan;
import org.matsim.contrib.signals.model.SignalSystem;
import org.matsim.contrib.signals.utils.SignalUtils;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.config.ConfigWriter;
import org.matsim.core.config.groups.QSimConfigGroup;
import org.matsim.core.config.groups.ReplanningConfigGroup;
import org.matsim.core.config.groups.RoutingConfigGroup;
import org.matsim.core.config.groups.ScoringConfigGroup;
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy;
import org.matsim.core.mobsim.qsim.interfaces.SignalGroupState;
import org.matsim.core.network.io.NetworkWriter;
import org.matsim.core.population.io.PopulationWriter;
import org.matsim.vehicles.MatsimVehicleWriter;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleType;

/**
 * THE GATE before any scenario touches signals (issue #73, DECISIONS.md 9.74):
 * proves on a three-node toy that the signals contrib's physics SURVIVES the
 * citysim QSim assembly.
 *
 * <p>Why this probe exists: the contrib injects its physics through a single
 * Guice binding — {@code QNetworkFactory -> QSignalsNetworkFactory} — made in
 * an overriding QSim module, while {@link CitysimControler#assemble} rebuilds
 * the QSim COMPONENT order (netsim engine removed and re-added, the stock
 * agent source replaced by {@link TolerantAgentSource}, the generic-route
 * teleporter inserted). If that composition broke, the failure mode would be
 * the worst kind: every signal silently ignored, vehicles free-flowing
 * through red, and the run completing without a murmur. So the probe builds
 * the controler THROUGH {@code CitysimControler.assemble} (the config is
 * written to a temp directory, since assemble takes a path — the real entry
 * point's code path, not a replica), wires signals exactly as
 * {@link CitysimSignalsControler} does, runs one iteration, and asserts on
 * the EVENT STREAM:
 * <ul>
 * <li>{@code red_gates_buffer}: a car reaching the signalised link during red
 *     leaves it only at/after the next green onset;</li>
 * <li>{@code green_releases}: that car does leave, within a green window;</li>
 * <li>{@code discharge_per_green}: the per-green discharge COUNT on the
 *     signalised link (the dossier's own acceptance check);</li>
 * <li>{@code walk_agent_completed}: a network-simulated walk agent finishes,
 *     proving the TolerantAgentSource / component-reordering path is alive
 *     alongside the signals engine.</li>
 * </ul>
 * Exit code 0 only if every assertion holds; the observations are printed as
 * one JSON object on stdout either way.
 *
 * <p>The toy: three nodes in a line, two 100 m links at 10 m/s; one signal
 * system on link1 with one group, fixed-time cycle 60 (green 0-30, red
 * 30-60) under the contrib's own {@code DefaultPlanbasedSignalSystemController}
 * — this probe gates the ASSEMBLY, not the tram controller, which
 * {@link TramPriorityProbe} gates separately. Two car agents depart at 5
 * (green) and 35 (red); one walk agent (walk is a qsim main mode with its own
 * vehicle type, as in the real model) departs at 5. Everything is seeded by
 * construction: no randomness is consulted in a 1-iteration run of this toy.
 */
public final class SignalsAssemblyProbe {

    private static final String LINK_SIGNAL = "link1";
    private static final String LINK_OUT = "link2";

    private SignalsAssemblyProbe() {
    }

    public static void main(final String[] args) throws Exception {
        final Path dir = Files.createTempDirectory("citysim-signals-probe");
        writeToyInputs(dir, true);

        final SignalSystemsConfigGroup signalsConfig =
                new SignalSystemsConfigGroup();
        signalsConfig.setUseSignalSystems(true);

        // The real entry point's code path: assemble() from the written
        // config, signals data attached to the scenario, the contrib's
        // Configurator on top. No overriding module is replicated inline.
        final Controler controler = CitysimControler.assemble(
                dir.resolve("config.xml").toString(), List.of(signalsConfig));
        final Scenario scenario = controler.getScenario();
        scenario.addScenarioElement(SignalsData.ELEMENT_NAME,
                buildSignalsData(signalsConfig,
                        DefaultPlanbasedSignalSystemController.IDENTIFIER));
        new Signals.Configurator(controler);
        // The gradient factory (DECISIONS.md 9.84): this probe's config
        // declares gradient.representation = link_speed and stamps a +10%
        // grade on link2, so the run below proves the ported
        // GradientSignalsNetworkFactory keeps the signal gating THE
        // ASSERTIONS BELOW MEASURE while the walker slows by exactly the
        // declared Tobler factor - both halves alive in one mobsim.
        CitysimSignalsControler.installGradientIfDeclared(controler);

        final ProbeHandler handler = new ProbeHandler();
        controler.addOverridingModule(new AbstractModule() {
            @Override
            public void install() {
                addEventHandlerBinding().toInstance(handler);
            }
        });
        controler.run();

        // ---- evaluate ------------------------------------------------
        final List<double[]> greens = handler.observedGreenIntervals();
        final Double carBLeave = handler.leaveTime(handler.vehicleOf("carB"));
        final Double carALeave = handler.leaveTime(handler.vehicleOf("carA"));

        // (a) the car that reached the signal on red (departed at 35, red
        // from 30) left only at/after the NEXT observed green onset
        Double nextOnsetAfter35 = null;
        for (final double[] g : greens) {
            if (g[0] > 35.0) {
                nextOnsetAfter35 = g[0];
                break;
            }
        }
        final boolean redGates = carBLeave != null && nextOnsetAfter35 != null
                && carBLeave >= nextOnsetAfter35;

        // (b) ... and it left within an observed green window
        final boolean greenReleases = carBLeave != null
                && insideAGreen(greens, carBLeave);

        // (c) per-green discharge counts on the signalised link, cars only;
        // every car leave must fall inside an observed green, and both cars
        // must have discharged
        final Map<String, Integer> discharge = new LinkedHashMap<>();
        boolean allLeavesInGreen = true;
        int carLeaves = 0;
        for (final double[] g : greens) {
            int n = 0;
            for (final Map.Entry<Id<Vehicle>, Double> e
                    : handler.carLeaves.entrySet()) {
                if (e.getValue() >= g[0] && e.getValue() < g[1]) {
                    n++;
                }
            }
            // a green still open when the mobsim ran out of agents has no
            // observed dropping; label its end "end" rather than MAX_VALUE
            discharge.put(((int) g[0]) + "-"
                    + (g[1] == Double.MAX_VALUE ? "end"
                            : String.valueOf((int) g[1])), n);
        }
        for (final Double t : handler.carLeaves.values()) {
            carLeaves++;
            if (!insideAGreen(greens, t)) {
                allLeavesInGreen = false;
            }
        }
        final boolean dischargeOk = allLeavesInGreen && carLeaves == 2
                && carALeave != null;

        // (d) the walk agent finished its walk leg on the toy's network
        final boolean walkCompleted = handler.walkerArrived;

        // (e) gradient composes with signals (DECISIONS.md 9.84): the walker
        // crossed the +10% link2 at the declared cap times the Tobler
        // factor - computed by the SAME GradientLinkSpeed.factor the mobsim
        // ran, so the assertion is that execution matches the one formula.
        // Departure 5.0; the home link is not traversed, so the walk
        // duration is link2's 100 m at the graded speed plus insertion
        // granularity.
        final GradientConfigGroup gradientCfg = (GradientConfigGroup)
                controler.getConfig().getModules()
                        .get(GradientConfigGroup.NAME);
        final Link gradedLink = scenario.getNetwork().getLinks()
                .get(Id.createLinkId(LINK_OUT));
        final double gradeFactor =
                GradientLinkSpeed.factor("walk", gradedLink, gradientCfg);
        final double expectedWalkS = 100.0 / (1.34 * gradeFactor);
        final Double walkDur = handler.walkerArrivalTime == null ? null
                : handler.walkerArrivalTime - 5.0;
        final boolean gradeRead = gradeFactor < 0.8;
        final boolean walkSlowed = walkDur != null
                && Math.abs(walkDur - expectedWalkS) <= 3.0;

        final boolean ok = redGates && greenReleases && dischargeOk
                && walkCompleted && gradeRead && walkSlowed;
        final StringBuilder json = new StringBuilder();
        json.append("{\"probe\": \"SignalsAssemblyProbe\"");
        json.append(", \"red_gates_buffer\": ").append(redGates);
        json.append(", \"green_releases\": ").append(greenReleases);
        json.append(", \"discharge_per_green\": {");
        boolean first = true;
        for (final Map.Entry<String, Integer> e : discharge.entrySet()) {
            if (!first) {
                json.append(", ");
            }
            first = false;
            json.append("\"").append(e.getKey()).append("\": ")
                    .append(e.getValue());
        }
        json.append("}");
        json.append(", \"walk_agent_completed\": ").append(walkCompleted);
        json.append(", \"walk_grade_factor\": ").append(gradeFactor);
        json.append(", \"walk_duration_s\": ").append(walkDur);
        json.append(", \"walk_expected_graded_s\": ").append(expectedWalkS);
        json.append(", \"grade_read\": ").append(gradeRead);
        json.append(", \"walk_slowed_to_formula\": ").append(walkSlowed);
        json.append(", \"car_on_green_left_at_s\": ").append(carALeave);
        json.append(", \"car_on_red_left_at_s\": ").append(carBLeave);
        json.append(", \"next_green_onset_after_red_arrival_s\": ")
                .append(nextOnsetAfter35);
        json.append(", \"pass\": ").append(ok);
        json.append("}");
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    private static boolean insideAGreen(final List<double[]> greens,
                                        final double t) {
        for (final double[] g : greens) {
            if (t >= g[0] && t < g[1]) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------------
    // toy construction (shared with TramPriorityProbe)
    // ------------------------------------------------------------------

    /**
     * Write the toy scenario next to a config that names it: a line of 100 m
     * links at 10 m/s carrying car (+walk when asked), the signalised link
     * being {@code link1}. With {@code withWalk}, walk is a qsim main mode
     * with its own vehicle type — the configuration that triggers every
     * citysim QSim override this probe exists to compose with signals.
     */
    static void writeToyInputs(final Path dir, final boolean withWalk)
            throws Exception {
        final Config config = ConfigUtils.createConfig();
        final Scenario scenario
                = org.matsim.core.scenario.ScenarioUtils.createScenario(config);
        final Network net = scenario.getNetwork();
        final Node n1 = net.getFactory().createNode(
                Id.createNodeId("n1"), new Coord(0, 0));
        final Node n2 = net.getFactory().createNode(
                Id.createNodeId("n2"), new Coord(100, 0));
        final Node n3 = net.getFactory().createNode(
                Id.createNodeId("n3"), new Coord(200, 0));
        net.addNode(n1);
        net.addNode(n2);
        net.addNode(n3);
        final Set<String> modes =
                withWalk ? Set.of("car", "walk") : Set.of("car");
        addLink(net, LINK_SIGNAL, n1, n2, modes);
        addLink(net, LINK_OUT, n2, n3, modes);
        // DECISIONS.md 9.84: a +10% grade on the walker's link, read only
        // when the config declares gradient.representation = link_speed -
        // the TramPriorityProbe shares this toy with the module absent and
        // the attribute is then inert data
        net.getLinks().get(Id.createLinkId(LINK_OUT)).getAttributes()
                .putAttribute(GradientConfigGroup.GRADE_ATTRIBUTE, "10.0");
        // return links: the router refuses a mode network that is not
        // strongly connected; nothing drives back in this probe
        addLink(net, LINK_SIGNAL + "r", n2, n1, modes);
        addLink(net, LINK_OUT + "r", n3, n2, modes);

        final Population pop = scenario.getPopulation();
        final PopulationFactory pf = pop.getFactory();
        // departs at 5, inside the first green (0-30)
        pop.addPerson(person(pf, "carA", "car", 5.0));
        // departs at 35, inside the first red (30-60): the gating test
        pop.addPerson(person(pf, "carB", "car", 35.0));
        if (withWalk) {
            pop.addPerson(person(pf, "walker", "walk", 5.0));
        }

        // vehicle types named by mode, as modeVehicleTypesFromVehiclesData
        // requires; the walk cap matches the real model's discipline of the
        // router and the physics sharing one declared speed
        final VehicleType car = scenario.getVehicles().getFactory()
                .createVehicleType(Id.create("car", VehicleType.class));
        car.setMaximumVelocity(40.0);
        scenario.getVehicles().addVehicleType(car);
        if (withWalk) {
            final VehicleType walk = scenario.getVehicles().getFactory()
                    .createVehicleType(Id.create("walk", VehicleType.class));
            walk.setMaximumVelocity(1.34);
            walk.setPcuEquivalents(0.1);
            scenario.getVehicles().addVehicleType(walk);
        }

        new NetworkWriter(net).write(dir.resolve("network.xml").toString());
        new PopulationWriter(pop).write(dir.resolve("plans.xml").toString());
        new MatsimVehicleWriter(scenario.getVehicles())
                .writeFile(dir.resolve("vehicles.xml").toString());

        // a FRESH config for the file: the one the scenario container was
        // created from is locked against input-file changes by then
        final Config runConfig = ConfigUtils.createConfig();
        configureToy(runConfig, dir, withWalk, true);
        new ConfigWriter(runConfig).write(dir.resolve("config.xml").toString());
    }

    /** The tram probe's form: no walk agent, no gradient module. */
    static void configureToy(final Config config, final Path dir,
                             final boolean withWalk) {
        configureToy(config, dir, withWalk, false);
    }

    /** The run config for the toy; file names are config-dir relative. */
    static void configureToy(final Config config, final Path dir,
                             final boolean withWalk,
                             final boolean withGradient) {
        config.network().setInputFile("network.xml");
        config.plans().setInputFile("plans.xml");
        config.vehicles().setVehiclesFile("vehicles.xml");
        config.controller().setOutputDirectory(
                dir.resolve("output").toString());
        config.controller().setOverwriteFileSetting(
                OutputDirectoryHierarchy.OverwriteFileSetting
                        .deleteDirectoryIfExists);
        config.controller().setLastIteration(0);
        config.controller().setCreateGraphs(false);
        config.controller().setDumpDataAtEnd(false);
        config.controller().setWriteEventsInterval(0);
        config.controller().setWritePlansInterval(0);
        final List<String> mainModes = withWalk
                ? List.of("car", "walk") : List.of("car");
        config.qsim().setMainModes(mainModes);
        config.qsim().setVehiclesSource(QSimConfigGroup.VehiclesSource
                .modeVehicleTypesFromVehiclesData);
        // the contrib itself refuses fast capacity update; declared here as
        // the run-input builder declares it for real signal runs
        config.qsim().setUsingFastCapacityUpdate(false);
        config.qsim().setStartTime(0.0);
        config.qsim().setSimStarttimeInterpretation(
                QSimConfigGroup.StarttimeInterpretation.onlyUseStarttime);
        config.qsim().setEndTime(3600.0);
        // The reach bound (B.mode.walk_feasible_km / bike_feasible_km), the
        // signal regime (A.signals.control_regime) and the taxi fleet
        // (A.taxi.fleet_representation) are declared, never defaulted: each
        // module refuses a run that never chose. Zero disables the bound,
        // fixed_time is the plan verbatim, absent is no fleet - stated
        // here the way every real config states them, via the config file.
        // Until these lines both probes died in checkConsistency before the
        // mobsim started: a gate that could not run (found under #125).
        final org.matsim.core.config.ConfigGroup avail =
                new org.matsim.core.config.ConfigGroup(
                        ModeAvailabilityConfigGroup.NAME);
        avail.addParam("walkFeasibleKm", "0");
        avail.addParam("bikeFeasibleKm", "0");
        config.addModule(avail);
        final org.matsim.core.config.ConfigGroup scats =
                new org.matsim.core.config.ConfigGroup(ScatsConfigGroup.NAME);
        scats.addParam("regime", ScatsConfigGroup.REGIME_FIXED_TIME);
        config.addModule(scats);
        final org.matsim.core.config.ConfigGroup taxi =
                new org.matsim.core.config.ConfigGroup(
                        TaxiFleetConfigGroup.NAME);
        taxi.addParam("representation",
                      TaxiFleetConfigGroup.REPRESENTATION_ABSENT);
        config.addModule(taxi);
        config.routing().setNetworkModes(mainModes);
        config.routing().setAccessEgressType(
                RoutingConfigGroup.AccessEgressType.none);
        // a network mode must not also carry teleportation defaults
        for (final String mode : mainModes) {
            if (config.routing().getTeleportedModeParams().containsKey(mode)) {
                config.routing().removeTeleportedModeParams(mode);
            }
        }
        final ScoringConfigGroup.ActivityParams h =
                new ScoringConfigGroup.ActivityParams("h");
        h.setTypicalDuration(12 * 3600.0);
        config.scoring().addActivityParams(h);
        final ScoringConfigGroup.ActivityParams w =
                new ScoringConfigGroup.ActivityParams("w");
        w.setTypicalDuration(8 * 3600.0);
        config.scoring().addActivityParams(w);
        final ReplanningConfigGroup.StrategySettings keep =
                new ReplanningConfigGroup.StrategySettings();
        keep.setStrategyName("ChangeExpBeta");
        keep.setWeight(1.0);
        config.replanning().addStrategySettings(keep);
        // the citysim telemetry module refuses a run whose interval was
        // never bound (no usable Java default, by design); the toy declares
        // one the way every real config does, via the config file
        final org.matsim.core.config.ConfigGroup telemetry =
                new org.matsim.core.config.ConfigGroup("telemetry");
        telemetry.addParam("liveIntervalS", "3600");
        config.addModule(telemetry);
        if (withGradient) {
            // The declared 9.84 gradient regime, as the run-input builder
            // emits it. Toy literals like every other number in this probe:
            // the assertion compares execution against the ONE shared
            // formula, not against a registry value.
            final org.matsim.core.config.ConfigGroup gradient =
                    new org.matsim.core.config.ConfigGroup(
                            GradientConfigGroup.NAME);
            gradient.addParam("representation", "link_speed");
            gradient.addParam("bikeUphillSlowdownPerPct", "0.065");
            gradient.addParam("bikeDownhillSpeedupPerPct", "0.015");
            gradient.addParam("bikeFloorFactor", "0.2");
            gradient.addParam("bikeCeilingFactor", "1.3");
            gradient.addParam("walkToblerSlopeCoeff", "3.5");
            gradient.addParam("walkToblerOffset", "0.05");
            config.addModule(gradient);
        }
    }

    private static void addLink(final Network net, final String id,
                                final Node from, final Node to,
                                final Set<String> modes) {
        final Link link = net.getFactory().createLink(
                Id.createLinkId(id), from, to);
        link.setLength(100.0);
        link.setFreespeed(10.0);
        link.setCapacity(1800.0);
        link.setNumberOfLanes(1.0);
        link.setAllowedModes(modes);
        net.addLink(link);
    }

    private static Person person(final PopulationFactory pf, final String id,
                                 final String mode, final double departS) {
        final Person p = pf.createPerson(Id.createPersonId(id));
        final Plan plan = pf.createPlan();
        final Activity home = pf.createActivityFromLinkId(
                "h", Id.createLinkId(LINK_SIGNAL));
        home.setCoord(new Coord(90, 0));
        home.setEndTime(departS);
        plan.addActivity(home);
        plan.addLeg(pf.createLeg(mode));
        final Activity work = pf.createActivityFromLinkId(
                "w", Id.createLinkId(LINK_OUT));
        work.setCoord(new Coord(190, 0));
        plan.addActivity(work);
        p.addPlan(plan);
        return p;
    }

    /**
     * One signal system on link1, one group, fixed cycle 60 with green 0-30,
     * under the given controller identifier. Built programmatically — the
     * probe gates assembly, not the contrib's file readers, which the real
     * entry point exercises through {@code SignalsDataLoader}.
     */
    static SignalsData buildSignalsData(final SignalSystemsConfigGroup cfg,
                                        final String controllerIdentifier) {
        final Id<SignalSystem> sysId = Id.create("sys1", SignalSystem.class);
        final Id<Signal> sigId = Id.create("sig1", Signal.class);
        final Id<SignalGroup> grpId = Id.create("veh", SignalGroup.class);
        final SignalsData data = SignalUtils.createSignalsData(cfg);

        final SignalSystemsData systems = data.getSignalSystemsData();
        final SignalSystemData sys =
                systems.getFactory().createSignalSystemData(sysId);
        SignalUtils.createAndAddSignal(sys, systems.getFactory(), sigId,
                Id.createLinkId(LINK_SIGNAL), null);
        systems.addSignalSystemData(sys);

        final SignalGroupsData groups = data.getSignalGroupsData();
        final SignalGroupData grp =
                groups.getFactory().createSignalGroupData(sysId, grpId);
        grp.addSignalId(sigId);
        groups.addSignalGroupData(grp);

        final SignalControlData control = data.getSignalControlData();
        final SignalSystemControllerData ctrl = control.getFactory()
                .createSignalSystemControllerData(sysId);
        ctrl.setControllerIdentifier(controllerIdentifier);
        final SignalPlanData plan = control.getFactory()
                .createSignalPlanData(Id.create("p1", SignalPlan.class));
        plan.setCycleTime(60);
        plan.setOffset(0);
        plan.setStartTime(0.0);
        plan.setEndTime(0.0); // start == end == 0.0: all day
        final SignalGroupSettingsData setting = control.getFactory()
                .createSignalGroupSettingsData(grpId);
        setting.setOnset(0);
        setting.setDropping(30);
        plan.addSignalGroupSettings(setting);
        ctrl.addSignalPlanData(plan);
        control.addSignalSystemControllerData(ctrl);
        return data;
    }

    // ------------------------------------------------------------------
    // observation
    // ------------------------------------------------------------------

    /** Collects the event stream the assertions read. */
    static final class ProbeHandler implements LinkLeaveEventHandler,
            VehicleEntersTrafficEventHandler, PersonArrivalEventHandler,
            SignalGroupStateChangedEventHandler {

        /** car-mode vehicle leaves of the signalised link, by vehicle. */
        final Map<Id<Vehicle>, Double> carLeaves = new TreeMap<>();
        private final Map<String, Id<Vehicle>> vehicleOfPerson =
                new TreeMap<>();
        private final Set<Id<Vehicle>> carVehicles = new java.util.TreeSet<>();
        private final List<double[]> stateChanges = new ArrayList<>();
        boolean walkerArrived;
        Double walkerArrivalTime;

        Id<Vehicle> vehicleOf(final String person) {
            return this.vehicleOfPerson.get(person);
        }

        Double leaveTime(final Id<Vehicle> vehicle) {
            return vehicle == null ? null : this.carLeaves.get(vehicle);
        }

        /** Observed [onset, drop) green intervals of the one signal group. */
        List<double[]> observedGreenIntervals() {
            final List<double[]> greens = new ArrayList<>();
            Double onset = null;
            for (final double[] change : this.stateChanges) {
                final boolean green = change[1] == 1.0;
                if (green && onset == null) {
                    onset = change[0];
                } else if (!green && onset != null) {
                    greens.add(new double[] {onset, change[0]});
                    onset = null;
                }
            }
            if (onset != null) {
                greens.add(new double[] {onset, Double.MAX_VALUE});
            }
            return greens;
        }

        @Override
        public void handleEvent(final VehicleEntersTrafficEvent event) {
            this.vehicleOfPerson.put(event.getPersonId().toString(),
                    event.getVehicleId());
            if ("car".equals(event.getNetworkMode())) {
                this.carVehicles.add(event.getVehicleId());
            }
        }

        @Override
        public void handleEvent(final LinkLeaveEvent event) {
            if (LINK_SIGNAL.equals(event.getLinkId().toString())
                    && this.carVehicles.contains(event.getVehicleId())) {
                this.carLeaves.put(event.getVehicleId(), event.getTime());
            }
        }

        @Override
        public void handleEvent(final PersonArrivalEvent event) {
            if ("walker".equals(event.getPersonId().toString())
                    && "walk".equals(event.getLegMode())) {
                this.walkerArrived = true;
                this.walkerArrivalTime = event.getTime();
            }
        }

        @Override
        public void handleEvent(final SignalGroupStateChangedEvent event) {
            this.stateChanges.add(new double[] {event.getTime(),
                    event.getNewState() == SignalGroupState.GREEN ? 1.0 : 0.0});
        }

        @Override
        public void reset(final int iteration) {
            this.carLeaves.clear();
            this.vehicleOfPerson.clear();
            this.carVehicles.clear();
            this.stateChanges.clear();
            this.walkerArrived = false;
            this.walkerArrivalTime = null;
        }
    }
}
