package citysim;

import java.util.*;
import org.matsim.api.core.v01.*;
import org.matsim.api.core.v01.population.*;
import org.matsim.core.config.*;
import org.matsim.core.population.*;
import org.matsim.core.population.io.PopulationReader;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.scenario.ScenarioUtils;

/** Synthetic person attributes, not observed ownership or a city run. */
public final class PersonModesProbe {
    static Scenario scenario() {
        ModeAvailabilityConfigGroup gates = new ModeAvailabilityConfigGroup();
        gates.taxiMinAge = 18; gates.bikeMinAge = 16;
        gates.walkFeasibleKm = 0; gates.bikeFeasibleKm = 0;
        Config config = ConfigUtils.createConfig(gates);
        config.subtourModeChoice().setModes(new String[] {"car", "walk", "compact", "shared3", "ride", "bike", "taxi", "pt"});
        config.subtourModeChoice().setConsiderCarAvailability(true);
        config.routing().setNetworkModes(Set.of("car", "walk", "compact", "shared3", "truck"));
        config.transit().setTransitModes(Set.of("bus", "rail"));
        return ScenarioUtils.createScenario(config);
    }
    static Person person(Scenario scenario, String id, Object permitted) {
        Person p = scenario.getPopulation().getFactory().createPerson(Id.createPersonId(id));
        p.getAttributes().putAttribute("age", 30);
        PersonUtils.setCarAvail(p, "never"); PersonUtils.setLicence(p, "no");
        if (permitted != null) p.getAttributes().putAttribute("permittedModes", permitted);
        scenario.getPopulation().addPerson(p); return p;
    }
    static Plan plan(Person person, String... modes) {
        Plan p = PopulationUtils.createPlan();
        p.addActivity(PopulationUtils.createActivityFromCoord("home", new Coord(0, 0)));
        for (int i = 0; i < modes.length; i++) {
            p.addLeg(PopulationUtils.createLeg(modes[i]));
            p.addActivity(PopulationUtils.createActivityFromCoord(
                    i == modes.length - 1 ? "work" : "pt interaction", new Coord(i + 1, 0)));
        }
        person.addPlan(p); return p;
    }
    static void expectModes(Scenario s, Plan p, String... expected) {
        Collection<String> actual = new AvailabilityModesCalculator(s.getConfig()).getPermissibleModes(p);
        if (!new ArrayList<>(actual).equals(Arrays.asList(expected)))
            throw new AssertionError("Expected " + Arrays.toString(expected) + "; got " + actual);
    }
    static void fails(Runnable action, String message) {
        try { action.run(); } catch (IllegalArgumentException ex) {
            if (!ex.getMessage().contains(message)) throw new AssertionError(ex);
            return;
        }
        throw new AssertionError("Expected refusal: " + message);
    }
    public static void main(String[] args) {
        Scenario s = scenario();
        Person legacy = person(s, "legacy", null); Plan lp = plan(legacy, "walk");
        expectModes(s, lp, "walk", "compact", "shared3", "ride", "bike", "taxi", "pt");
        Person owner = person(s, "owner", "walk,compact"); Plan op = plan(owner, "compact");
        expectModes(s, op, "walk", "compact");
        Person car = person(s, "no-car-licence", "car,walk");
        expectModes(s, plan(car, "walk"), "walk");
        Person young = person(s, "young", "walk,ride,bike,taxi");
        young.getAttributes().putAttribute("age", 14); young.getAttributes().putAttribute("rideAvail", "never");
        expectModes(s, plan(young, "walk"), "walk");
        Person noBike = person(s, "no-bike", "walk,bike"); noBike.getAttributes().putAttribute("bikeAvail", "never");
        expectModes(s, plan(noBike, "walk"), "walk");
        Person locked = person(s, "freight", "truck"); locked.getAttributes().putAttribute("lockedMode", "truck");
        expectModes(s, plan(locked, "truck"), "truck");
        AvailabilityModesCalculator.validateExplicitPopulation(s);
        System.out.println("PASS: arbitrary mode ownership independent of car licence; legacy gates and freight locks retained");

        for (Object invalid : new Object[] {"", "walk,", "walk,walk", "walk,typo", 1}) {
            Scenario bad = scenario(); Plan bp = plan(person(bad, "bad", invalid), "walk");
            fails(() -> new AvailabilityModesCalculator(bad.getConfig()).getPermissibleModes(bp),
                    invalid instanceof String ? "permitted mode" : "comma-separated String");
        }
        owner.getAttributes().putAttribute("lockedMode", "shared3");
        fails(() -> AvailabilityModesCalculator.validateExplicitPopulation(s), "lockedMode contradicts");
        owner.getAttributes().removeAttribute("lockedMode");
        Plan forbidden = plan(owner, "shared3"); owner.setSelectedPlan(op);
        fails(() -> AvailabilityModesCalculator.validateExplicitPopulation(s), "stored plan uses unavailable mode shared3");
        owner.removePlan(forbidden);
        System.out.println("PASS: malformed availability, contradictory locks and unavailable unselected plans refused");

        Scenario routed = scenario(); Person access = person(routed, "access", "compact");
        Plan ap = plan(access, "walk", "compact", "walk");
        for (Leg leg : TripStructureUtils.getLegs(ap)) TripStructureUtils.setRoutingMode(leg, "compact");
        Person transfer = person(routed, "transfer", "pt");
        Plan tp = plan(transfer, "walk", "bus", "rail", "walk");
        AvailabilityModesCalculator.validateExplicitPopulation(routed);
        TripStructureUtils.setRoutingMode(TripStructureUtils.getLegs(ap).get(0), "shared3");
        fails(() -> AvailabilityModesCalculator.validateExplicitPopulation(routed), "conflicting routing modes");
        TripStructureUtils.setRoutingMode(TripStructureUtils.getLegs(ap).get(0), "compact");
        new PopulationWriter(routed.getPopulation()).write(args[0]);
        Scenario loaded = scenario(); new PopulationReader(loaded).readFile(args[0]);
        AvailabilityModesCalculator.validateExplicitPopulation(loaded);
        if (!"compact".equals(loaded.getPopulation().getPersons().get(Id.createPersonId("access"))
                .getAttributes().getAttribute("permittedModes"))) throw new AssertionError("XML lost availability");
        System.out.println("PASS: physical access and transit transfer legs checked by trip mode; population XML round-trip retains availability");
    }
}
