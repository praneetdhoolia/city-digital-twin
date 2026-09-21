package citysim;

import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.events.*;
import org.matsim.api.core.v01.events.handler.PersonMoneyEventHandler;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.config.*;
import org.matsim.core.events.EventsUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.pt.transitSchedule.api.*;
import org.matsim.vehicles.Vehicle;

/** Synthetic tariffs and event sequences, never a city's observed values. */
public final class BoardingFareProbe {
    static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    static TransitDriverStartsEvent driver(String vehicle, String line) {
        return new TransitDriverStartsEvent(0, Id.createPersonId("driver_" + vehicle),
            Id.createVehicleId(vehicle), Id.create(line, TransitLine.class),
            Id.create("route", TransitRoute.class), Id.create("departure", Departure.class));
    }
    static void board(BoardingFareHandler handler, String person, String vehicle) {
        handler.handleEvent(new PersonEntersVehicleEvent(1, Id.createPersonId(person), Id.createVehicleId(vehicle)));
    }
    static void move(BoardingFareHandler handler, String vehicle) {
        handler.handleEvent(new LinkEnterEvent(2, Id.createVehicleId(vehicle), Id.createLinkId("link")));
    }
    static void alight(BoardingFareHandler handler, String person, String vehicle) {
        handler.handleEvent(new PersonLeavesVehicleEvent(3, Id.createPersonId(person), Id.createVehicleId(vehicle)));
    }
    public static void main(String[] args) throws Exception {
        Path work = Path.of(args[0]);
        Path table = work.resolve("fares.csv");
        Files.writeString(table, "match_kind,match_id,profile_id,upper_bounds_m,fares_money,linear_rate_money_per_m,currency_code\n"
            + "line,special,band,1000|2000,2|4,0.001,INR\n"
            + "mode,bus,linear,,,0.01,INR\n", StandardCharsets.UTF_8);
        BoardingFareConfigGroup fares = new BoardingFareConfigGroup();
        fares.tableFile = table.toString();
        Config config = ConfigUtils.createConfig(fares);
        config.controller().setOutputDirectory(work.toString());
        Scenario scenario = ScenarioUtils.createScenario(config);
        var network = scenario.getNetwork();
        var factory = network.getFactory();
        var a = factory.createNode(Id.createNodeId("a"), new Coord(0, 0));
        var b = factory.createNode(Id.createNodeId("b"), new Coord(1000, 0));
        network.addNode(a); network.addNode(b);
        var link = factory.createLink(Id.createLinkId("link"), a, b);
        link.setLength(1000); network.addLink(link);
        var schedule = scenario.getTransitSchedule();
        var sf = schedule.getFactory();
        for (String name : List.of("special", "ordinary")) {
            var line = sf.createTransitLine(Id.create(name, TransitLine.class));
            line.addRoute(sf.createTransitRoute(Id.create("route", TransitRoute.class), null, List.of(), "bus"));
            schedule.addTransitLine(line);
        }
        var events = EventsUtils.createEventsManager();
        List<PersonMoneyEvent> money = new ArrayList<>();
        events.addHandler(new PersonMoneyEventHandler() {
            public void handleEvent(PersonMoneyEvent event) { money.add(event); }
        });
        config.scoring().getModes().get("pt").setMonetaryDistanceRate(-.01);
        boolean refused = false;
        try { new BoardingFareHandler(config, events, scenario, new BoardingFareTable(config, scenario)); }
        catch (IllegalArgumentException expected) { refused = expected.getMessage().contains("zero native"); }
        require(refused, "double native PT distance charge was accepted");
        config.scoring().getModes().get("pt").setMonetaryDistanceRate(0);
        BoardingFareHandler handler = new BoardingFareHandler(config, events, scenario, new BoardingFareTable(config, scenario));
        handler.reset(0);
        handler.handleEvent(driver("v1", "special"));
        board(handler, "driver_v1", "v1");
        board(handler, "first", "v1"); move(handler, "v1");
        board(handler, "second", "v1"); move(handler, "v1"); move(handler, "v1");
        alight(handler, "first", "v1"); alight(handler, "second", "v1");
        board(handler, "first", "v1"); move(handler, "v1"); alight(handler, "first", "v1");
        handler.handleEvent(driver("v2", "ordinary"));
        board(handler, "third", "v2"); board(handler, "unfinished", "v2");
        move(handler, "v2"); alight(handler, "third", "v2");
        handler.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        events.finishProcessing();
        require(money.size() == 4, "driver or unfinished boarding charged, or transfer omitted");
        Map<String, Double> totals = new HashMap<>();
        for (var event : money) {
            require(event.getPurpose().equals(BoardingFareHandler.PURPOSE), "wrong money purpose");
            totals.merge(event.getPersonId().toString(), -event.getAmount(), Double::sum);
        }
        require(totals.equals(Map.of("first", 7.0, "second", 4.0, "third", 10.0)),
            "wrong line override, boundary, tail, concurrent rider distance or separate transfer charge: " + totals);
        String audit = Files.readString(work.resolve("boarding_fares.csv"));
        require(audit.contains("0,band,INR,3,6000.0,11.0,1,0"), "band audit mismatch");
        require(audit.contains("0,linear,INR,1,1000.0,10.0,0,1"), "unfinished boarding audit mismatch");
        System.out.println("PASS: native boarding fares, inclusive bands, extrapolation, line override, distance since boarding, transfers, driver exclusion and unfinished audit");
        System.out.println("PASS: duplicate native distance pricing refused");
    }
}
