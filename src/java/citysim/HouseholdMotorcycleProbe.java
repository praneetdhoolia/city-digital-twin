package citysim;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.PersonArrivalEvent;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.handler.PersonArrivalEventHandler;
import org.matsim.api.core.v01.events.handler.PersonEntersVehicleEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.NetworkWriter;
import org.matsim.api.core.v01.network.Node;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PopulationFactory;
import org.matsim.api.core.v01.population.PopulationWriter;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigGroup;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.config.ConfigWriter;
import org.matsim.core.config.groups.QSimConfigGroup;
import org.matsim.core.config.groups.ReplanningConfigGroup;
import org.matsim.core.config.groups.RoutingConfigGroup;
import org.matsim.core.config.groups.ScoringConfigGroup;
import org.matsim.core.controler.AbstractModule;
import org.matsim.core.controler.Controler;
import org.matsim.core.controler.OutputDirectoryHierarchy;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.vehicles.MatsimVehicleWriter;
import org.matsim.vehicles.VehicleType;

/**
 * The gate on the household motorcycle (D28, F39; RUN.qsim.motorcycle_roster),
 * through the real entry point: {@link CitysimControler#assemble} on a toy
 * written to a temp directory, one iteration of the mobsim, twice.
 *
 * <p>Two riders of household {@code h1} hold one drawn motorcycle. Rider
 * {@code a} leaves home on {@code link1} at 5 s and rides to {@code link2};
 * rider {@code b} leaves {@code link2} at 10 s, while {@code a} is still
 * riding.
 * <ul>
 * <li>{@code per_person_is_f38}: under {@code per_person} each rides a
 *     motorbike of their own and {@code b} leaves at once - the defect;</li>
 * <li>{@code household_shares_one}: under {@code household} both ride
 *     {@code hhh1_moto1};</li>
 * <li>{@code second_rider_waits}: and {@code b} boards it only when
 *     {@code a} has parked it at {@code link2} - a departure claims the
 *     household motorcycle as it claims the household car.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class HouseholdMotorcycleProbe {

    private HouseholdMotorcycleProbe() {
    }

    /** What one run saw: each rider's vehicle and boarding time, a's arrival. */
    static final class Seen implements PersonEntersVehicleEventHandler, PersonArrivalEventHandler {
        final Map<String, String> vehicle = new HashMap<>();
        final Map<String, Double> boarded = new HashMap<>();
        Double aArrived = null;

        @Override
        public void handleEvent(final PersonEntersVehicleEvent e) {
            final String p = e.getPersonId().toString();
            if (!this.vehicle.containsKey(p)) {
                this.vehicle.put(p, e.getVehicleId().toString());
                this.boarded.put(p, e.getTime());
            }
        }

        @Override
        public void handleEvent(final PersonArrivalEvent e) {
            if ("a".equals(e.getPersonId().toString()) && this.aArrived == null
                    && AvailabilityModesCalculator.MOTORBIKE.equals(e.getLegMode())) {
                this.aArrived = e.getTime();
            }
        }
    }

    public static void main(final String[] args) throws Exception {
        final Seen perPerson = run(HouseholdVehiclesConfigGroup.ROSTER_PER_PERSON);
        final Seen household = run(HouseholdVehiclesConfigGroup.MOTORCYCLE_HOUSEHOLD);

        final boolean perPersonIsF38 = perPerson.vehicle.get("a") != null
                && perPerson.vehicle.get("b") != null
                && !perPerson.vehicle.get("a").equals(perPerson.vehicle.get("b"))
                && perPerson.aArrived != null
                && perPerson.boarded.get("b") < perPerson.aArrived;
        final String shared = HouseholdVehicleRoster.VEHICLE_ID_PREFIX + "h1"
                + HouseholdVehicleRoster.MOTORCYCLE_SUFFIX;
        final boolean sharesOne = shared.equals(household.vehicle.get("a"))
                && shared.equals(household.vehicle.get("b"));
        final boolean waits = household.aArrived != null
                && household.boarded.get("b") != null
                && household.boarded.get("b") >= household.aArrived;
        final boolean ok = perPersonIsF38 && sharesOne && waits;
        System.out.println("{\"probe\":\"HouseholdMotorcycleProbe\",\"per_person_is_f38\":"
                + perPersonIsF38 + ",\"household_shares_one\":" + sharesOne
                + ",\"second_rider_waits\":" + waits
                + ",\"a_arrived_s\":" + household.aArrived
                + ",\"b_boarded_s\":" + household.boarded.get("b")
                + ",\"b_boarded_per_person_s\":" + perPerson.boarded.get("b")
                + ",\"ok\":" + ok + "}");
        System.exit(ok ? 0 : 1);
    }

    private static Seen run(final String motorcycle) throws Exception {
        final Path dir = Files.createTempDirectory("citysim-moto-probe");
        writeToy(dir, motorcycle);
        final Controler controler = CitysimControler.assemble(
                dir.resolve("config.xml").toString(), List.of());
        final Seen seen = new Seen();
        controler.addOverridingModule(new AbstractModule() {
            @Override
            public void install() {
                addEventHandlerBinding().toInstance(seen);
            }
        });
        controler.run();
        return seen;
    }

    private static void writeToy(final Path dir, final String motorcycle) throws Exception {
        final Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        final Network net = scenario.getNetwork();
        final Node n1 = node(net, "n1", 0);
        final Node n2 = node(net, "n2", 100);
        final Node n3 = node(net, "n3", 200);
        final Set<String> modes = Set.of("car", "motorbike", "walk");
        link(net, "link1", n1, n2, modes);
        link(net, "link2", n2, n3, modes);
        link(net, "link1r", n2, n1, modes);
        link(net, "link2r", n3, n2, modes);

        final PopulationFactory pf = scenario.getPopulation().getFactory();
        scenario.getPopulation().addPerson(rider(pf, "a", "link1", 90, "link2", 190, 5.0));
        scenario.getPopulation().addPerson(rider(pf, "b", "link2", 190, "link2r", 150, 10.0));

        vehicleType(scenario, "car", 40.0, 1.0);
        vehicleType(scenario, "motorbike", 40.0, 0.5);
        vehicleType(scenario, "walk", 1.34, 0.1);
        new NetworkWriter(net).write(dir.resolve("network.xml").toString());
        new PopulationWriter(scenario.getPopulation()).write(dir.resolve("plans.xml").toString());
        new MatsimVehicleWriter(scenario.getVehicles()).writeFile(dir.resolve("vehicles.xml").toString());

        final Config config = ConfigUtils.createConfig();
        config.network().setInputFile("network.xml");
        config.plans().setInputFile("plans.xml");
        config.vehicles().setVehiclesFile("vehicles.xml");
        config.controller().setOutputDirectory(dir.resolve("output").toString());
        config.controller().setOverwriteFileSetting(
                OutputDirectoryHierarchy.OverwriteFileSetting.deleteDirectoryIfExists);
        config.controller().setLastIteration(0);
        config.controller().setCreateGraphs(false);
        config.controller().setDumpDataAtEnd(false);
        config.controller().setWriteEventsInterval(0);
        config.controller().setWritePlansInterval(0);
        final List<String> mainModes = List.of("car", "motorbike", "walk");
        config.qsim().setMainModes(mainModes);
        config.qsim().setVehiclesSource(QSimConfigGroup.VehiclesSource.modeVehicleTypesFromVehiclesData);
        // teleport, the declared global behaviour: only the citysim handler can
        // make the second rider wait
        config.qsim().setVehicleBehavior(QSimConfigGroup.VehicleBehavior.teleport);
        config.qsim().setStartTime(0.0);
        config.qsim().setSimStarttimeInterpretation(
                QSimConfigGroup.StarttimeInterpretation.onlyUseStarttime);
        config.qsim().setEndTime(3600.0);
        module(config, ModeAvailabilityConfigGroup.NAME, "walkFeasibleKm", "0", "bikeFeasibleKm", "0");
        module(config, ScatsConfigGroup.NAME, "regime", ScatsConfigGroup.REGIME_FIXED_TIME);
        module(config, TaxiFleetConfigGroup.NAME, "representation",
               TaxiFleetConfigGroup.REPRESENTATION_ABSENT);
        module(config, ActivityLinksConfigGroup.NAME, "assignment", ActivityLinksConfigGroup.COMMON);
        module(config, "telemetry", "liveIntervalS", "3600");
        module(config, HouseholdVehiclesConfigGroup.NAME,
               "roster", HouseholdVehiclesConfigGroup.ROSTER_PER_PERSON, "motorcycle", motorcycle);
        config.routing().setNetworkModes(mainModes);
        config.routing().setAccessEgressType(RoutingConfigGroup.AccessEgressType.none);
        for (final String mode : mainModes) {
            if (config.routing().getTeleportedModeParams().containsKey(mode)) {
                config.routing().removeTeleportedModeParams(mode);
            }
        }
        for (final String type : new String[] {"h", "w"}) {
            final ScoringConfigGroup.ActivityParams a = new ScoringConfigGroup.ActivityParams(type);
            a.setTypicalDuration(8 * 3600.0);
            config.scoring().addActivityParams(a);
        }
        config.scoring().addModeParams(new ScoringConfigGroup.ModeParams("motorbike"));
        final ReplanningConfigGroup.StrategySettings keep = new ReplanningConfigGroup.StrategySettings();
        keep.setStrategyName("ChangeExpBeta");
        keep.setWeight(1.0);
        config.replanning().addStrategySettings(keep);
        new ConfigWriter(config).write(dir.resolve("config.xml").toString());
    }

    private static void module(final Config config, final String name, final String... kv) {
        final ConfigGroup g = new ConfigGroup(name);
        for (int i = 0; i + 1 < kv.length; i += 2) {
            g.addParam(kv[i], kv[i + 1]);
        }
        config.addModule(g);
    }

    private static Node node(final Network net, final String id, final double x) {
        final Node n = net.getFactory().createNode(Id.createNodeId(id), new Coord(x, 0));
        net.addNode(n);
        return n;
    }

    private static void link(final Network net, final String id, final Node from, final Node to,
                             final Set<String> modes) {
        final Link l = net.getFactory().createLink(Id.createLinkId(id), from, to);
        l.setLength(100.0);
        l.setFreespeed(10.0);
        l.setCapacity(1800.0);
        l.setNumberOfLanes(1.0);
        l.setAllowedModes(modes);
        net.addLink(l);
    }

    private static void vehicleType(final Scenario s, final String id, final double speed,
                                    final double pcu) {
        final VehicleType t = s.getVehicles().getFactory()
                .createVehicleType(Id.create(id, VehicleType.class));
        t.setMaximumVelocity(speed);
        t.setPcuEquivalents(pcu);
        s.getVehicles().addVehicleType(t);
    }

    private static Person rider(final PopulationFactory pf, final String id,
                                final String fromLink, final double fromX,
                                final String toLink, final double toX, final double departS) {
        final Person p = pf.createPerson(Id.createPersonId(id));
        p.getAttributes().putAttribute(RidePairingEngine.HOUSEHOLD_ATTRIBUTE, "h1");
        p.getAttributes().putAttribute(AvailabilityModesCalculator.MOTORBIKE_ATTRIBUTE, "always");
        final Plan plan = pf.createPlan();
        final Activity home = pf.createActivityFromLinkId("h", Id.createLinkId(fromLink));
        home.setCoord(new Coord(fromX, 0));
        home.setEndTime(departS);
        plan.addActivity(home);
        plan.addLeg(pf.createLeg(AvailabilityModesCalculator.MOTORBIKE));
        final Activity work = pf.createActivityFromLinkId("w", Id.createLinkId(toLink));
        work.setCoord(new Coord(toX, 0));
        plan.addActivity(work);
        p.addPlan(plan);
        return p;
    }
}
