package citysim;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.LinkLeaveEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.LinkLeaveEventHandler;
import org.matsim.api.core.v01.events.handler.TransitDriverStartsEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.Node;
import org.matsim.contrib.signals.SignalSystemsConfigGroup;
import org.matsim.contrib.signals.builder.Signals;
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
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.controler.Controler;
import org.matsim.core.mobsim.qsim.interfaces.SignalGroupState;
import org.matsim.core.network.io.NetworkWriter;
import org.matsim.core.population.io.PopulationWriter;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.population.routes.RouteUtils;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitRouteStop;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitScheduleFactory;
import org.matsim.pt.transitSchedule.api.TransitScheduleWriter;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.vehicles.MatsimVehicleWriter;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleType;

/**
 * The gate on {@link TramPriorityController} itself (issue #73): on the same
 * class of toy {@link SignalsAssemblyProbe} uses, prove that a REAL transit
 * tram arriving just before its stage's dropping gets the green extended
 * under {@code mode=green_extension}, and does NOT under {@code mode=off}.
 *
 * <p>CHOICE, stated: the tram is a real {@code TransitSchedule} departure
 * driven by the QSim's own transit engine — not synthetic events pushed into
 * the {@link org.matsim.core.api.experimental.events.EventsManager}. The
 * synthetic route was considered and rejected as the LESS robust option: the
 * detection contract is "a transit vehicle, identified by
 * {@code TransitDriverStartsEvent}, entering the approach link", and only a
 * real transit vehicle exercises that contract end to end (driver creation,
 * event ordering within the step, the vehicle physically gated by the very
 * signal it requests). A synthetic stream would prove the arithmetic while
 * silently skipping the wiring, and the wiring is what dies quietly.
 *
 * <p>The toy: four nodes in a line (three 100 m links at 10 m/s), the middle
 * link (link1) signalised, plus a cross-street stub into the junction so the
 * control has a competing stage to borrow from. Fixed plan: cycle 60, tram
 * stage (group id "tram", signal on link1) green 0-30, cross stage (group
 * "road") green 30-58. One tram departs its first stop at t=20, enters link1
 * at ~21-22 (detection), and reaches the stop line at ~32 — just AFTER the
 * plan's dropping at 30, but within a 10 s extension window of it at
 * detection time:
 * <ul>
 * <li>{@code mode=green_extension}: the dropping is delayed (observed tram
 *     RED strictly later than the plan's second 30) and the tram clears the
 *     junction without waiting out the red;</li>
 * <li>{@code mode=off}: the plan runs verbatim (observed tram RED at exactly
 *     30) and the tram waits for the next onset at 60.</li>
 * </ul>
 * Exit code 0 only if both hold; both runs' observations are printed as one
 * JSON object on stdout either way.
 */
public final class TramPriorityProbe {

    private static final String LINK_APPROACH = "link0";
    private static final String LINK_SIGNAL = "link1";
    private static final String LINK_OUT = "link2";
    private static final String LINK_CROSS = "cross";
    private static final double PLAN_TRAM_DROP_S = 30.0;

    private TramPriorityProbe() {
    }

    public static void main(final String[] args) throws Exception {
        final Path dir = Files.createTempDirectory("citysim-tram-probe");
        writeToyInputs(dir);

        final Observation off = run(dir,
                TramPriorityConfigGroup.MODE_OFF);
        final Observation ext = run(dir,
                TramPriorityConfigGroup.MODE_GREEN_EXTENSION);

        // with the plan verbatim the tram stage drops exactly at the plan's
        // second; with green extension it drops strictly later
        final boolean offVerbatim = off.firstTramRedS != null
                && off.firstTramRedS == PLAN_TRAM_DROP_S;
        final boolean extended = ext.firstTramRedS != null
                && ext.firstTramRedS > PLAN_TRAM_DROP_S;
        // and the physics agrees with the paperwork: without priority the
        // tram sits out the red until the next onset (>= 60); with it, the
        // tram clears during the extended green (before the observed drop)
        final boolean offGated = off.tramLeaveS != null
                && off.tramLeaveS >= 60.0;
        final boolean extCleared = ext.tramLeaveS != null
                && ext.firstTramRedS != null
                && ext.tramLeaveS <= ext.firstTramRedS;

        // compensation, end to end: cycle 1 borrowed 10 s from the road
        // stage (green 30-58 became 40-58), so with the ledger on, cycle 2
        // must hand them back by opening the road stage 10 s EARLY - at
        // absolute 60+20=80 instead of the plan's 60+30=90. The off run's
        // road stage must show the plan's own 90, untouched.
        final Double extRoadOnset2 = ext.roadOnsetIn(60.0, 120.0);
        final Double offRoadOnset2 = off.roadOnsetIn(60.0, 120.0);
        final boolean compensated = extRoadOnset2 != null
                && extRoadOnset2 == 80.0;
        final boolean offUnperturbed = offRoadOnset2 != null
                && offRoadOnset2 == 90.0;

        final boolean ok = offVerbatim && extended && offGated && extCleared
                && compensated && offUnperturbed;
        final StringBuilder json = new StringBuilder();
        json.append("{\"probe\": \"TramPriorityProbe\"");
        json.append(", \"plan_tram_drop_s\": ").append(PLAN_TRAM_DROP_S);
        json.append(", \"off_first_tram_red_s\": ").append(off.firstTramRedS);
        json.append(", \"ext_first_tram_red_s\": ").append(ext.firstTramRedS);
        json.append(", \"off_tram_cleared_junction_s\": ")
                .append(off.tramLeaveS);
        json.append(", \"ext_tram_cleared_junction_s\": ")
                .append(ext.tramLeaveS);
        json.append(", \"off_cycle2_road_onset_s\": ").append(offRoadOnset2);
        json.append(", \"ext_cycle2_road_onset_s\": ").append(extRoadOnset2);
        json.append(", \"off_runs_plan_verbatim\": ").append(offVerbatim);
        json.append(", \"extension_granted\": ").append(extended);
        json.append(", \"off_tram_gated_until_next_green\": ")
                .append(offGated);
        json.append(", \"ext_tram_cleared_in_extended_green\": ")
                .append(extCleared);
        json.append(", \"borrowed_time_repaid_next_cycle\": ")
                .append(compensated);
        json.append(", \"pass\": ").append(ok);
        json.append("}");
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    /** One controler run of the toy under the given tramPriority mode. */
    private static Observation run(final Path dir, final String mode) {
        final SignalSystemsConfigGroup signalsConfig =
                new SignalSystemsConfigGroup();
        signalsConfig.setUseSignalSystems(true);
        final TramPriorityConfigGroup tramPriority =
                new TramPriorityConfigGroup();
        // set programmatically BEFORE assemble: the written config carries no
        // tramPriority module, so these instance values survive the load -
        // the same mechanism the real run uses, only the source differs
        // (there, the run-input builder writes the module into the file)
        tramPriority.setMode(mode);
        if (!TramPriorityConfigGroup.MODE_OFF.equals(mode)) {
            tramPriority.setExtensionWindowS(10.0);
            tramPriority.setDetectionDistanceM(100.0);
            tramPriority.setPriorityBudgetShare(0.25);
            tramPriority.setCompensationEnabled(true);
        }

        final Controler controler = CitysimControler.assemble(
                dir.resolve("config.xml").toString(),
                List.of(signalsConfig, tramPriority));
        final Scenario scenario = controler.getScenario();
        scenario.addScenarioElement(SignalsData.ELEMENT_NAME,
                buildTramSignalsData(signalsConfig));
        final Signals.Configurator configurator =
                new Signals.Configurator(controler);
        configurator.addSignalControllerFactory(
                TramPriorityController.IDENTIFIER,
                TramPriorityController.Factory.class);

        final Observation obs = new Observation();
        controler.addOverridingModule(new AbstractModule() {
            @Override
            public void install() {
                addEventHandlerBinding().toInstance(obs);
            }
        });
        controler.run();
        return obs;
    }

    // ------------------------------------------------------------------
    // toy construction
    // ------------------------------------------------------------------

    private static void writeToyInputs(final Path dir) throws Exception {
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
        final Node n4 = net.getFactory().createNode(
                Id.createNodeId("n4"), new Coord(300, 0));
        final Node n5 = net.getFactory().createNode(
                Id.createNodeId("n5"), new Coord(200, 100));
        net.addNode(n1);
        net.addNode(n2);
        net.addNode(n3);
        net.addNode(n4);
        net.addNode(n5);
        addLink(net, LINK_APPROACH, n1, n2);
        addLink(net, LINK_SIGNAL, n2, n3);
        addLink(net, LINK_OUT, n3, n4);
        // the cross street exists so the plan has a competing stage to
        // borrow from; nothing drives on it in this probe
        addLink(net, LINK_CROSS, n5, n3);
        // return links: the router refuses a mode network that is not
        // strongly connected; nothing drives back in this probe
        addLink(net, LINK_APPROACH + "r", n2, n1);
        addLink(net, LINK_SIGNAL + "r", n3, n2);
        addLink(net, LINK_OUT + "r", n4, n3);
        addLink(net, LINK_CROSS + "r", n3, n5);

        // no private agents: the probe isolates the tram/signal interaction
        new NetworkWriter(net).write(dir.resolve("network.xml").toString());
        new PopulationWriter(scenario.getPopulation())
                .write(dir.resolve("plans.xml").toString());
        final VehicleType car = scenario.getVehicles().getFactory()
                .createVehicleType(Id.create("car", VehicleType.class));
        car.setMaximumVelocity(40.0);
        scenario.getVehicles().addVehicleType(car);
        new MatsimVehicleWriter(scenario.getVehicles())
                .writeFile(dir.resolve("vehicles.xml").toString());

        // the tram: a real TransitSchedule departure at t=20 over
        // link0 -> link1 -> link2, stops at either end, transit vehicle
        // "tram1" - it enters the signalised link at ~21-22, inside the
        // extension window of the dropping at 30
        final TransitSchedule ts = scenario.getTransitSchedule();
        final TransitScheduleFactory tf = ts.getFactory();
        final TransitStopFacility stopA = tf.createTransitStopFacility(
                Id.create("stopA", TransitStopFacility.class),
                new Coord(95, 0), false);
        stopA.setLinkId(Id.createLinkId(LINK_APPROACH));
        final TransitStopFacility stopB = tf.createTransitStopFacility(
                Id.create("stopB", TransitStopFacility.class),
                new Coord(295, 0), false);
        stopB.setLinkId(Id.createLinkId(LINK_OUT));
        ts.addStopFacility(stopA);
        ts.addStopFacility(stopB);
        final NetworkRoute route = RouteUtils.createLinkNetworkRouteImpl(
                Id.createLinkId(LINK_APPROACH),
                List.of(Id.createLinkId(LINK_SIGNAL)),
                Id.createLinkId(LINK_OUT));
        final List<TransitRouteStop> stops = new ArrayList<>();
        stops.add(tf.createTransitRouteStop(stopA, 0.0, 0.0));
        stops.add(tf.createTransitRouteStop(stopB, 60.0, 60.0));
        final TransitRoute tramRoute = tf.createTransitRoute(
                Id.create("tramRoute", TransitRoute.class), route, stops,
                "car");
        final Departure d1 = tf.createDeparture(
                Id.create("d1", Departure.class), 20.0);
        d1.setVehicleId(Id.create("tram1", Vehicle.class));
        tramRoute.addDeparture(d1);
        // a second departure keeps the mobsim alive across the next cycle
        // boundary (t=60), which is where the compensation ledger pays a
        // borrowed-from stage back - without it the toy empties out and the
        // repayment cycle never runs
        final Departure d2 = tf.createDeparture(
                Id.create("d2", Departure.class), 90.0);
        d2.setVehicleId(Id.create("tram2", Vehicle.class));
        tramRoute.addDeparture(d2);
        final TransitLine line =
                tf.createTransitLine(Id.create("tramLine", TransitLine.class));
        line.addRoute(tramRoute);
        ts.addTransitLine(line);
        new TransitScheduleWriter(ts).writeFile(
                dir.resolve("transitSchedule.xml").toString());

        final VehicleType tramType = scenario.getTransitVehicles().getFactory()
                .createVehicleType(Id.create("tram", VehicleType.class));
        tramType.setMaximumVelocity(20.0);
        tramType.getCapacity().setSeats(20);
        tramType.getCapacity().setStandingRoom(0);
        scenario.getTransitVehicles().addVehicleType(tramType);
        scenario.getTransitVehicles().addVehicle(
                scenario.getTransitVehicles().getFactory().createVehicle(
                        Id.create("tram1", Vehicle.class), tramType));
        scenario.getTransitVehicles().addVehicle(
                scenario.getTransitVehicles().getFactory().createVehicle(
                        Id.create("tram2", Vehicle.class), tramType));
        new MatsimVehicleWriter(scenario.getTransitVehicles())
                .writeFile(dir.resolve("transitVehicles.xml").toString());

        // a FRESH config for the file: the one the scenario container was
        // created from is locked against input-file changes by then
        final Config runConfig = ConfigUtils.createConfig();
        SignalsAssemblyProbe.configureToy(runConfig, dir, false);
        runConfig.transit().setUseTransit(true);
        runConfig.transit().setTransitScheduleFile("transitSchedule.xml");
        runConfig.transit().setVehiclesFile("transitVehicles.xml");
        new ConfigWriter(runConfig).write(dir.resolve("config.xml").toString());
    }

    private static void addLink(final Network net, final String id,
                                final Node from, final Node to) {
        final Link link = net.getFactory().createLink(
                Id.createLinkId(id), from, to);
        link.setLength(100.0);
        link.setFreespeed(10.0);
        link.setCapacity(1800.0);
        link.setNumberOfLanes(1.0);
        link.setAllowedModes(Set.of("car"));
        net.addLink(link);
    }

    /**
     * One system at the link1/cross junction: the tram stage IS the group
     * literally named "tram" (that name is the controller's contract), green
     * 0-30; the cross stage "road" green 30-58; cycle 60; controlled by
     * {@link TramPriorityController#IDENTIFIER}.
     */
    private static SignalsData buildTramSignalsData(
            final SignalSystemsConfigGroup cfg) {
        final Id<SignalSystem> sysId = Id.create("sys1", SignalSystem.class);
        final Id<Signal> sigTram = Id.create("sigTram", Signal.class);
        final Id<Signal> sigCross = Id.create("sigCross", Signal.class);
        final Id<SignalGroup> tramGrp = Id.create(
                TramPriorityController.TRAM_GROUP_ID, SignalGroup.class);
        final Id<SignalGroup> roadGrp = Id.create("road", SignalGroup.class);
        final SignalsData data = SignalUtils.createSignalsData(cfg);

        final SignalSystemsData systems = data.getSignalSystemsData();
        final SignalSystemData sys =
                systems.getFactory().createSignalSystemData(sysId);
        SignalUtils.createAndAddSignal(sys, systems.getFactory(), sigTram,
                Id.createLinkId(LINK_SIGNAL), null);
        SignalUtils.createAndAddSignal(sys, systems.getFactory(), sigCross,
                Id.createLinkId(LINK_CROSS), null);
        systems.addSignalSystemData(sys);

        final SignalGroupsData groups = data.getSignalGroupsData();
        final SignalGroupData tram =
                groups.getFactory().createSignalGroupData(sysId, tramGrp);
        tram.addSignalId(sigTram);
        groups.addSignalGroupData(tram);
        final SignalGroupData road =
                groups.getFactory().createSignalGroupData(sysId, roadGrp);
        road.addSignalId(sigCross);
        groups.addSignalGroupData(road);

        final SignalControlData control = data.getSignalControlData();
        final SignalSystemControllerData ctrl = control.getFactory()
                .createSignalSystemControllerData(sysId);
        ctrl.setControllerIdentifier(TramPriorityController.IDENTIFIER);
        final SignalPlanData plan = control.getFactory()
                .createSignalPlanData(Id.create("p1", SignalPlan.class));
        plan.setCycleTime(60);
        plan.setOffset(0);
        plan.setStartTime(0.0);
        plan.setEndTime(0.0); // start == end == 0.0: all day
        final SignalGroupSettingsData tramSetting = control.getFactory()
                .createSignalGroupSettingsData(tramGrp);
        tramSetting.setOnset(0);
        tramSetting.setDropping(30);
        plan.addSignalGroupSettings(tramSetting);
        final SignalGroupSettingsData roadSetting = control.getFactory()
                .createSignalGroupSettingsData(roadGrp);
        roadSetting.setOnset(30);
        roadSetting.setDropping(58);
        plan.addSignalGroupSettings(roadSetting);
        ctrl.addSignalPlanData(plan);
        control.addSignalSystemControllerData(ctrl);
        return data;
    }

    // ------------------------------------------------------------------
    // observation
    // ------------------------------------------------------------------

    /**
     * Watches the tram stage's state changes and the transit vehicle's exit
     * from the signalised link. The vehicle is identified through
     * {@code TransitDriverStartsEvent} — the same discipline the detection
     * itself is held to, so the probe cannot pass on an id coincidence.
     */
    static final class Observation implements
            SignalGroupStateChangedEventHandler, LinkLeaveEventHandler,
            TransitDriverStartsEventHandler {

        Double firstTramRedS;
        Double tramLeaveS;
        private final List<Double> roadGreenOnsetsS = new ArrayList<>();
        private final Set<Id<Vehicle>> transitVehicles =
                new java.util.TreeSet<>();

        @Override
        public void handleEvent(final SignalGroupStateChangedEvent event) {
            if (this.firstTramRedS == null
                    && TramPriorityController.TRAM_GROUP_ID.equals(
                            event.getSignalGroupId().toString())
                    && event.getNewState() == SignalGroupState.RED) {
                this.firstTramRedS = event.getTime();
            }
            if ("road".equals(event.getSignalGroupId().toString())
                    && event.getNewState() == SignalGroupState.GREEN) {
                this.roadGreenOnsetsS.add(event.getTime());
            }
        }

        /** First observed road-stage onset inside [fromS, toS), if any. */
        Double roadOnsetIn(final double fromS, final double toS) {
            for (final Double t : this.roadGreenOnsetsS) {
                if (t >= fromS && t < toS) {
                    return t;
                }
            }
            return null;
        }

        @Override
        public void handleEvent(final TransitDriverStartsEvent event) {
            this.transitVehicles.add(event.getVehicleId());
        }

        @Override
        public void handleEvent(final LinkLeaveEvent event) {
            if (this.tramLeaveS == null
                    && LINK_SIGNAL.equals(event.getLinkId().toString())
                    && this.transitVehicles.contains(event.getVehicleId())) {
                this.tramLeaveS = event.getTime();
            }
        }

        @Override
        public void reset(final int iteration) {
            this.firstTramRedS = null;
            this.tramLeaveS = null;
            this.roadGreenOnsetsS.clear();
            this.transitVehicles.clear();
        }
    }
}
