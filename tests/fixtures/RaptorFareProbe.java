package citysim;

import java.nio.file.*;
import java.util.*;
import ch.sbb.matsim.routing.pt.raptor.*;
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.config.*;
import org.matsim.core.population.routes.RouteUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.scoring.functions.ScoringParameters;
import org.matsim.pt.transitSchedule.api.*;
import org.matsim.vehicles.*;

/** Competing departures exercise the real pinned RAPTOR candidate pruning. */
public final class RaptorFareProbe {
    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        Config config = ConfigUtils.createConfig();
        var fareConfig = ConfigUtils.addOrGetModule(config, BoardingFareConfigGroup.class);
        Path file = Path.of(args[0], "router_fares.csv");
        Files.writeString(file, "match_kind,match_id,profile_id,upper_bounds_m,fares_money,linear_rate_money_per_m,currency_code\n"
                + "line,fast,fast,2000,10,1,INR\nline,cheap,cheap,2000,1,1,INR\n");
        fareConfig.tableFile = file.toString();
        var scenario = ScenarioUtils.createScenario(config);
        var network = scenario.getNetwork();
        var nf = network.getFactory();
        for (int i = 0; i < 4; i++) network.addNode(nf.createNode(Id.createNodeId(i), new Coord(i * 1000, 0)));
        for (int i = 0; i < 3; i++) {
            var link = nf.createLink(Id.createLinkId(i), network.getNodes().get(Id.createNodeId(i)),
                    network.getNodes().get(Id.createNodeId(i + 1)));
            link.setLength(1000); link.setFreespeed(20); link.setCapacity(1000); link.setNumberOfLanes(1);
            network.addLink(link);
        }
        var schedule = scenario.getTransitSchedule();
        var factory = schedule.getFactory();
        var start = factory.createTransitStopFacility(Id.create("start", TransitStopFacility.class), new Coord(1000, 0), false);
        var end = factory.createTransitStopFacility(Id.create("end", TransitStopFacility.class), new Coord(3000, 0), false);
        start.setLinkId(Id.createLinkId(0)); end.setLinkId(Id.createLinkId(2));
        schedule.addStopFacility(start); schedule.addStopFacility(end);
        var vehicles = scenario.getTransitVehicles();
        var type = vehicles.getFactory().createVehicleType(Id.create("bus", VehicleType.class));
        type.setNetworkMode("bus"); type.getCapacity().setSeats(50);
        vehicles.addVehicleType(type);
        for (String id : List.of("fast", "cheap")) {
            var line = factory.createTransitLine(Id.create(id, TransitLine.class));
            var route = factory.createTransitRoute(Id.create(id, TransitRoute.class),
                    RouteUtils.createLinkNetworkRouteImpl(Id.createLinkId(0), List.of(Id.createLinkId(1)), Id.createLinkId(2)),
                    List.of(factory.createTransitRouteStop(start, 0, 0),
                            factory.createTransitRouteStop(end, id.equals("fast") ? 100 : 200, id.equals("fast") ? 100 : 200)), "bus");
            var vehicle = vehicles.getFactory().createVehicle(Id.create(id, Vehicle.class), type);
            vehicles.addVehicle(vehicle);
            var dep = factory.createDeparture(Id.create(id, Departure.class), 100);
            dep.setVehicleId(vehicle.getId()); route.addDeparture(dep); line.addRoute(route); schedule.addTransitLine(line);
        }
        var fares = new BoardingFareTable(config, scenario);
        var staticConfig = RaptorUtils.createStaticConfig(config);
        staticConfig.setOptimization(RaptorStaticConfig.RaptorOptimization.OneToAllRouting);
        var data = SwissRailRaptorData.create(schedule, vehicles, staticConfig, network, null);
        var params = RaptorUtils.createParameters(config);
        params.setMarginalUtilityOfTravelTime_utl_s("pt", -.01);
        params.setMarginalUtilityOfTravelTime_utl_s("bus", -.01);
        params.setMarginalUtilityOfWaitingPt_utl_s(0);
        params.setTransferPenaltyFixCostPerTransfer(0);
        for (boolean constants : List.of(false, true)) {
            ConfigUtils.addOrGetModule(config, RaptorModeCostConfigGroup.class).representation =
                    constants ? "mode_constant" : "absent";
            config.transit().setTransitModes(Set.of("pt", "bus"));
            config.scoring().addModeParams(new org.matsim.core.config.groups.ScoringConfigGroup.ModeParams("bus").setConstant(-.5));
            var cost = new RaptorFareCostCalculator(config, fares, person ->
                    new ScoringParameters.Builder(scenario, person).setMarginalUtilityOfMoney(
                            (double) person.getAttributes().getAttribute("moneyUtility")).build());
            var router = new SwissRailRaptor(data, person -> params, new LeastCostRaptorRouteSelector(),
                    null, cost, new DefaultRaptorTransferCostCalculator());
            for (double moneyUtility : List.of(1.0, .01)) {
                Person person = scenario.getPopulation().getFactory().createPerson(Id.createPersonId("p" + moneyUtility));
                person.getAttributes().putAttribute("moneyUtility", moneyUtility);
                var info = router.calcTree(start, 0, params, person).get(end.getId());
                require(info != null, "destination unreachable");
                String line = "";
                for (var part : info.getRaptorRoute().getParts()) {
                    if (part.line != null) { line = part.line.getId().toString(); break; }
                }
                String expected = moneyUtility == 1 ? "cheap" : "fast";
                require(line.equals(expected), "income-sensitive fare choice expected " + expected + ", got " + line);
                double expectedCost = (moneyUtility == 1 ? 3 : 1.1) + (constants ? .5 : 0);
                require(Math.abs(info.travelCost - expectedCost) < 1e-8,
                        "whole-ride fare/distance or time wrong: " + info.travelCost + " != " + expectedCost);
            }
        }
        System.out.println("PASS: real RAPTOR retains slower cheaper service; person money utility reverses choice; 2000 m inclusive fare charged once");
        System.out.println("PASS: fare routing preserves the optional submode constant exactly once");
    }
}
