package citysim;

import com.google.inject.Guice;
import java.util.*;
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.events.*;
import org.matsim.api.core.v01.network.*;
import org.matsim.api.core.v01.population.*;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.groups.QSimConfigGroup;
import org.matsim.core.events.EventsUtils;
import org.matsim.core.events.handler.BasicEventHandler;
import org.matsim.core.mobsim.qsim.*;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.router.*;
import org.matsim.core.router.util.TravelTime;
import org.matsim.core.utils.timing.TimeInterpretation;
import org.matsim.facilities.FacilitiesUtils;
import org.matsim.vehicles.Vehicle;

/** A tiny QSim execution, not a city scenario or calibration observation. */
public final class PhysicalAccessProbe {
    public static void main(String[] args) {
        Scenario scenario = ActivityLinksProbe.scenario(ActivityLinksConfigGroup.ACCESS);
        var config = scenario.getConfig();
        config.global().setRandomSeed(20260810);
        config.qsim().setMainModes(Set.of("car", "compact", "walk"));
        config.qsim().setVehiclesSource(QSimConfigGroup.VehiclesSource.modeVehicleTypesFromVehiclesData);
        config.qsim().setNumberOfThreads(1);
        config.qsim().setEndTime(20000);
        config.qsim().setStuckTime(1000);
        // Walking vehicles are QSim's person proxies, not a fleet left behind
        // when their person rides. This is the existing vehicle-placement policy.
        config.qsim().setVehicleBehavior(QSimConfigGroup.VehicleBehavior.teleport);
        ActivityLinkAssigner.run(scenario);
        List<Activity> ends = ActivityLinksProbe.activities(scenario);
        Network walking = ActivityLinksProbe.filtered(scenario, "walk");
        Network compact = ActivityLinksProbe.filtered(scenario, "compact");
        TravelTime walkTime = new CappedSpeedTravelTime(1);
        TravelTime vehicleTime = new CappedSpeedTravelTime(10);
        RoutingModule walk = DefaultRoutingModules.createPureNetworkRouter("walk",
                scenario.getPopulation().getFactory(), scenario, walking, ActivityLinksProbe.path(walking, walkTime));
        RoutingModule router = DefaultRoutingModules.createAccessEgressNetworkRouter("compact",
                ActivityLinksProbe.path(compact, vehicleTime), scenario, compact, walk,
                TimeInterpretation.create(config), Guice.createInjector().getInstance(MultimodalLinkChooserDefaultImpl.class));
        Person person = scenario.getPopulation().getPersons().values().iterator().next();
        List<? extends PlanElement> route = router.calcRoute(DefaultRoutingRequest.withoutAttributes(
                FacilitiesUtils.wrapActivity(ends.get(0)), FacilitiesUtils.wrapActivity(ends.get(1)), 100, person));
        List<String> expectedModes = new ArrayList<>();
        List<Id<Link>> expectedStarts = new ArrayList<>(), expectedEnds = new ArrayList<>();
        for (PlanElement element : route) {
            if (element instanceof Leg leg) {
                ActivityLinksProbe.require(leg.getRoute() instanceof NetworkRoute, "non-network route in physical probe");
                expectedModes.add(leg.getMode());
                expectedStarts.add(leg.getRoute().getStartLinkId());
                expectedEnds.add(leg.getRoute().getEndLinkId());
            }
        }
        ActivityLinksProbe.require(expectedModes.equals(List.of("walk", "compact", "walk")), "access trip changed");
        Plan plan = person.getSelectedPlan(); plan.getPlanElements().clear();
        plan.addActivity(ends.get(0)); plan.getPlanElements().addAll(route); plan.addActivity(ends.get(1));
        List<Event> observed = new ArrayList<>();
        EventsManager events = EventsUtils.createEventsManager();
        events.addHandler((BasicEventHandler) observed::add);
        QSimBuilder builder = new QSimBuilder(config).useDefaults();
        builder.addOverridingQSimModule(new AbstractQSimModule() {
            @Override protected void configureQSim() {
                bind(TolerantAgentSource.class).asEagerSingleton();
                addQSimComponentBinding("probeAgentSource").to(TolerantAgentSource.class);
            }
        });
        builder.configureQSimComponents(components -> {
            components.removeNamedComponent(PopulationModule.COMPONENT_NAME);
            components.addNamedComponent("probeAgentSource");
        });
        QSim qsim = builder.build(scenario, events);
        events.initProcessing(); qsim.run(); events.finishProcessing();
        List<String> arrivals = new ArrayList<>(), departures = new ArrayList<>();
        List<Id<Link>> starts = new ArrayList<>(), finishes = new ArrayList<>();
        Map<Id<Vehicle>, String> modeOfVehicle = new HashMap<>();
        Map<String, Integer> entered = new TreeMap<>();
        int destinationActivities = 0;
        for (Event event : observed) {
            ActivityLinksProbe.require(!(event instanceof PersonStuckEvent), "person became stuck");
            ActivityLinksProbe.require(!event.getEventType().toLowerCase(Locale.ROOT).contains("teleport"),
                    "traveller teleported: " + event.getEventType());
            if (event instanceof PersonDepartureEvent departure) departures.add(departure.getLegMode());
            if (event instanceof PersonArrivalEvent arrival) {
                arrivals.add(arrival.getLegMode()); finishes.add(arrival.getLinkId());
            }
            if (event instanceof VehicleEntersTrafficEvent entry) {
                modeOfVehicle.put(entry.getVehicleId(), entry.getNetworkMode()); starts.add(entry.getLinkId());
                ActivityLinksProbe.require(scenario.getNetwork().getLinks().get(entry.getLinkId()).getAllowedModes()
                        .contains(entry.getNetworkMode()), "vehicle inserted onto prohibited road");
            }
            if (event instanceof LinkEnterEvent entry) {
                String mode = modeOfVehicle.get(entry.getVehicleId());
                ActivityLinksProbe.require(mode != null, "link event before vehicle-mode evidence");
                ActivityLinksProbe.require(scenario.getNetwork().getLinks().get(entry.getLinkId()).getAllowedModes()
                        .contains(mode), "vehicle entered prohibited road");
                entered.merge(mode, 1, Integer::sum);
            }
            if (event instanceof ActivityStartEvent start && "work".equals(start.getActType())) destinationActivities++;
        }
        ActivityLinksProbe.require(arrivals.equals(expectedModes) && departures.equals(expectedModes),
                "journey did not complete each physical leg: " + departures + " -> " + arrivals);
        ActivityLinksProbe.require(starts.equals(expectedStarts) && finishes.equals(expectedEnds),
                "vehicle insertion or arrival differs from routed links: " + starts + " / " + finishes);
        ActivityLinksProbe.require(entered.getOrDefault("walk", 0) > 0 && entered.getOrDefault("compact", 0) > 0,
                "no physical link traversal for an expected mode: " + entered);
        ActivityLinksProbe.require(destinationActivities == 1, "destination activity was not reached exactly once");
        System.out.println("PASS: QSim completed walk/compact/walk; actual link entries=" + entered
                + "; all insertion, traversal and arrival links match legal routes; no stuck or traveller teleport events");
    }
}
