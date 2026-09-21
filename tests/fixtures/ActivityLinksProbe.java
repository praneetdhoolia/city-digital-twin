package citysim;

import com.google.inject.Guice;
import java.util.*;
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.network.*;
import org.matsim.api.core.v01.population.*;
import org.matsim.core.config.*;
import org.matsim.core.config.groups.RoutingConfigGroup.AccessEgressType;
import org.matsim.core.config.groups.ReplanningConfigGroup.StrategySettings;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.algorithms.TransportModeNetworkFilter;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.router.*;
import org.matsim.core.router.costcalculators.OnlyTimeDependentTravelDisutilityFactory;
import org.matsim.core.router.util.*;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.timing.TimeInterpretation;
import org.matsim.facilities.FacilitiesUtils;

/** Synthetic geometry only. It represents no city or observed parameter. */
public final class ActivityLinksProbe {
    static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    static void node(Network network, String id, double x, double y) {
        network.addNode(network.getFactory().createNode(Id.createNodeId(id), new Coord(x, y)));
    }
    static void link(Network network, String id, String from, String to, Set<String> modes) {
        Link link = network.getFactory().createLink(Id.createLinkId(id),
                network.getNodes().get(Id.createNodeId(from)), network.getNodes().get(Id.createNodeId(to)));
        link.setLength(NetworkUtils.getEuclideanDistance(link.getFromNode().getCoord(), link.getToNode().getCoord()));
        link.setFreespeed(10); link.setCapacity(1000); link.setNumberOfLanes(1);
        link.setAllowedModes(modes); network.addLink(link);
    }
    static Scenario scenario(String assignment) {
        ActivityLinksConfigGroup group = new ActivityLinksConfigGroup(); group.assignment = assignment;
        Config config = ConfigUtils.createConfig(group);
        config.routing().setNetworkModes(Set.of("car", "compact", "walk"));
        config.routing().setAccessEgressType(AccessEgressType.accessEgressModeToLink);
        config.subtourModeChoice().setModes(new String[] {"car", "compact", "walk"});
        StrategySettings strategy = new StrategySettings(); strategy.setStrategyName("SubtourModeChoice");
        strategy.setWeight(1); config.replanning().addStrategySettings(strategy);
        Scenario scenario = ScenarioUtils.createScenario(config); Network n = scenario.getNetwork();
        for (int i = 0; i < 4; i++) {
            node(n, "a" + i, 0, i * 1000); node(n, "b" + i, 1000, i * 1000);
            link(n, "cross" + i, "a" + i, "b" + i, Set.of("walk"));
            link(n, "backCross" + i, "b" + i, "a" + i, Set.of("walk"));
        }
        for (int i = 0; i < 3; i++) {
            link(n, "car" + i, "a" + i, "a" + (i + 1), Set.of("car", "walk"));
            link(n, "backCar" + i, "a" + (i + 1), "a" + i, Set.of("car", "walk"));
            link(n, "compact" + i, "b" + i, "b" + (i + 1), Set.of("compact", "walk"));
            link(n, "backCompact" + i, "b" + (i + 1), "b" + i, Set.of("compact", "walk"));
        }
        node(n, "far0", 20000, 0); node(n, "far1", 20000, 3000);
        link(n, "commonFarAway", "far0", "far1", Set.of("car", "compact", "walk"));
        Person person = scenario.getPopulation().getFactory().createPerson(Id.createPersonId("test"));
        for (String mode : List.of("car", "compact", "walk")) {
            org.matsim.vehicles.VehicleType type = org.matsim.vehicles.VehicleUtils.createVehicleType(
                    Id.create(mode, org.matsim.vehicles.VehicleType.class));
            type.setNetworkMode(mode); type.setMaximumVelocity("walk".equals(mode) ? 1 : 10);
            scenario.getVehicles().addVehicleType(type);
            scenario.getVehicles().addVehicle(org.matsim.vehicles.VehicleUtils.createVehicle(Id.createVehicleId(mode), type));
        }
        org.matsim.vehicles.VehicleUtils.insertVehicleIdsIntoAttributes(person,
                Map.of("car", Id.createVehicleId("car"), "compact", Id.createVehicleId("compact"),
                       "walk", Id.createVehicleId("walk")));
        Plan plan = PopulationUtils.createPlan(person);
        Activity home = PopulationUtils.createActivityFromCoord("home", new Coord(0, 500));
        home.setLinkId(Id.createLinkId("car0")); home.setEndTime(100);
        Activity work = PopulationUtils.createActivityFromCoord("work", new Coord(0, 2500));
        work.setLinkId(Id.createLinkId("car2"));
        plan.addActivity(home); plan.addLeg(PopulationUtils.createLeg("compact")); plan.addActivity(work);
        person.addPlan(plan); scenario.getPopulation().addPerson(person);
        return scenario;
    }
    static List<Activity> activities(Scenario scenario) {
        return scenario.getPopulation().getPersons().values().iterator().next().getSelectedPlan()
                .getPlanElements().stream().filter(e -> e instanceof Activity).map(e -> (Activity)e).toList();
    }
    static Network filtered(Scenario scenario, String mode) {
        Network network = NetworkUtils.createNetwork();
        new TransportModeNetworkFilter(scenario.getNetwork()).filter(network, Set.of(mode));
        return network;
    }
    static LeastCostPathCalculator path(Network network, TravelTime time) {
        return new DijkstraFactory().createPathCalculator(network,
                new OnlyTimeDependentTravelDisutilityFactory().createTravelDisutility(time), time);
    }
    public static void main(String[] args) {
        Config emitted = ConfigUtils.loadConfig(args[0], new ActivityLinksConfigGroup());
        ActivityLinksConfigGroup declared = (ActivityLinksConfigGroup)emitted.getModules().get(ActivityLinksConfigGroup.NAME);
        require(ActivityLinksConfigGroup.ACCESS.equals(declared.assignment), "registry assignment did not reach MATSim");
        declared.checkConsistency(emitted);
        Scenario legacy = scenario(ActivityLinksConfigGroup.COMMON);
        ActivityLinkAssigner.run(legacy);
        require(activities(legacy).stream().allMatch(a -> "commonFarAway".equals(a.getLinkId().toString())),
                "common-mode behaviour changed");
        Scenario scenario = scenario(declared.assignment);
        List<Activity> ends = activities(scenario);
        ActivityLinkAssigner.run(scenario);
        require("car0".equals(ends.get(0).getLinkId().toString()) && "car2".equals(ends.get(1).getLinkId().toString()),
                "mode-specific access relocated activities");
        require(ends.get(0).getCoord().getX() == 0 && ends.get(1).getCoord().getY() == 2500, "coordinates changed");
        Network walking = filtered(scenario, "walk"), compact = filtered(scenario, "compact");
        TravelTime time = (l,t,p,v) -> l.getLength() / l.getFreespeed(t);
        RoutingModule walk = DefaultRoutingModules.createPureNetworkRouter("walk",
                scenario.getPopulation().getFactory(), scenario, walking, path(walking, time));
        RoutingModule router = DefaultRoutingModules.createAccessEgressNetworkRouter("compact", path(compact, time),
                scenario, compact, walk, TimeInterpretation.create(scenario.getConfig()),
                Guice.createInjector().getInstance(MultimodalLinkChooserDefaultImpl.class));
        Person person = scenario.getPopulation().getPersons().values().iterator().next();
        List<? extends PlanElement> routed = router.calcRoute(DefaultRoutingRequest.withoutAttributes(
                FacilitiesUtils.wrapActivity(ends.get(0)), FacilitiesUtils.wrapActivity(ends.get(1)), 100, person));
        int walked = 0, driven = 0;
        for (PlanElement element : routed) {
            if (!(element instanceof Leg leg)) continue;
            require(leg.getRoute() instanceof NetworkRoute, "unexpected non-network access leg: " + leg.getMode());
            NetworkRoute route = (NetworkRoute) leg.getRoute();
            List<Id<Link>> ids = new ArrayList<>(); ids.add(route.getStartLinkId());
            ids.addAll(route.getLinkIds()); ids.add(route.getEndLinkId());
            for (Id<Link> id : ids) require(scenario.getNetwork().getLinks().get(id).getAllowedModes().contains(leg.getMode()),
                    "route uses forbidden mode/link " + leg.getMode() + "/" + id);
            if ("walk".equals(leg.getMode())) walked++;
            if ("compact".equals(leg.getMode())) driven++;
        }
        require(walked == 2 && driven == 1, "expected network walk / compact / network walk");
        // Neither absent nor misspelt policy may silently choose a regime.
        for (String policy : List.of("", "misspelt")) {
            Scenario invalid = scenario(policy);
            boolean refused = false;
            try { ActivityLinkAssigner.run(invalid); } catch (IllegalStateException expected) { refused = true; }
            require(refused, "undeclared assignment accepted");
            require("car0".equals(activities(invalid).get(0).getLinkId().toString()), "refusal mutated plan");
        }
        for (AccessEgressType type : List.of(AccessEgressType.none, AccessEgressType.walkConstantTimeToLink)) {
            scenario.getConfig().routing().setAccessEgressType(type);
            boolean refused = false;
            try { ActivityLinkAssigner.run(scenario); } catch (IllegalStateException expected) { refused = true; }
            require(refused, "unsafe access policy accepted: " + type);
            require("car0".equals(ends.get(0).getLinkId().toString()), "refusal changed an activity");
        }
        System.out.println("PASS: registry policy loaded; legacy common links unchanged; mode-specific locations retained; "
                + "native router produced two physical walking connections and one legally restricted compact route; "
                + "incompatible access policies refused before mutation");
    }
}
