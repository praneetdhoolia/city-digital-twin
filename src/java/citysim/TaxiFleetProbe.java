package citysim;

import java.util.ArrayList;
import java.util.List;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.api.core.v01.population.Population;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.events.BeforeMobsimEvent;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * The gate on {@link TaxiFleetEngine}'s allocation (9.99, #90): a finite
 * fleet serves requests in departure order with the earliest-free vehicle,
 * holds a served passenger at the kerb for the wait it computed, refuses a
 * request its earliest-free vehicle cannot reach inside the declared wait,
 * walks the refused trip for the iteration and gives taxi back afterwards.
 *
 * <p>Until the sixteenth report the fleet had no probe: its allocation was
 * read from the arms' logs alone, so a change to the greedy pass could only be
 * noticed after a multi-hour run. This drives the real engine - the same
 * constructor the assembly injects, the same {@code BeforeMobsimEvent} and
 * {@code AfterMobsimEvent} the controler fires - over seven requests built in
 * memory and prints every person's modes and origin end time before and after
 * the mobsim as a fingerprint, so a refactor of the pass is compared on it.
 *
 * <p><b>Every number is a FIXTURE</b>: two vehicles, a ten-minute wait, a
 * five-minute deadhead, departures a minute or so apart, chosen so each branch
 * of the pass is taken once - served at once, served after a wait of exactly
 * the limit, refused one second over it, two requests at one clock ordered by
 * person id, and a request with no clock to allocate against. The declared
 * values reach the engine through {@link TaxiFleetConfigGroup}; this proves
 * the ALLOCATION.
 *
 * <p>The refused trip's walk is routed by the run's router in a real run; here
 * the router knows no mode, so the re-mode takes {@link RemodeRestore}'s
 * documented fallback - a walk leg with no route - which is what makes the
 * refusal visible in the plan without a network.
 *
 * <p>What it checks:
 * <ul>
 * <li>{@code absent} changes nothing (the representation every arm before
 *     9.99 ran, byte for byte);</li>
 * <li>a served request with a wait leaves at the vehicle's start, a wait of
 *     exactly the limit is served, one second over is refused and walks, a
 *     request with no clock is left alone;</li>
 * <li>after the mobsim every origin end time is the agent's own again and the
 *     refused trip holds taxi, with its travel time;</li>
 * <li>with {@code remodeRefused} off a refusal touches the plan not at all.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every asserted check holds.
 */
public final class TaxiFleetProbe {

    private static final String TAXI = "taxi";
    private static final Id<Link> HOME = Id.createLinkId("l_home");
    private static final Id<Link> WORK = Id.createLinkId("l_work");
    private static final Coord HOME_XY = new Coord(0.0, 0.0);
    private static final Coord WORK_XY = new Coord(5000.0, 0.0);

    private static final double FLEET = 2.0;
    private static final double MAX_WAIT_MIN = 10.0;
    private static final double DEADHEAD_MIN = 5.0;
    private static final double EIGHT_AM_S = 8.0 * 3600.0;

    /** id, departure (s after 08:00), travel time (s); NaN = no clock. */
    private static final Object[][] REQUESTS = {
        {"p1", 0.0, 600.0},
        {"p2", 60.0, 1200.0},
        {"p3", 300.0, 600.0},       // earliest free at +900: waits 600 = the limit
        {"p4", 360.0, 300.0},       // earliest free at +1560: 1200 over, refused
        {"p5", 1800.0, 60.0},       // free vehicle, no wait
        {"p6", 1800.0, 60.0},       // same clock as p5: ordered by id
        {"p7", 1900.0, 60.0},       // both free at +2160: waits 260
        {"p0", Double.NaN, 60.0},   // no end time, no departure: not a request
    };

    private TaxiFleetProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json = new StringBuilder("{\"probe\":\"TaxiFleetProbe\"");
        boolean ok = true;

        // --- 1. absent is the previous model exactly ------------------------
        final Scenario absent = scenario(TaxiFleetConfigGroup.REPRESENTATION_ABSENT, true);
        final String absentBefore = fingerprint(absent);
        final TaxiFleetEngine offEngine = engine(absent);
        offEngine.notifyBeforeMobsim(new BeforeMobsimEvent(null, 0, false));
        final boolean absentSilent = absentBefore.equals(fingerprint(absent));
        offEngine.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        ok &= absentSilent && absentBefore.equals(fingerprint(absent));
        json.append(",\"absent_changes_nothing\":").append(absentSilent);

        // --- 2. the allocation, as the plans carry it into the mobsim -------
        final Scenario fleet = scenario(TaxiFleetConfigGroup.REPRESENTATION_FLEET, true);
        final String before = fingerprint(fleet);
        final TaxiFleetEngine engineOn = engine(fleet);
        engineOn.notifyBeforeMobsim(new BeforeMobsimEvent(null, 0, false));
        final String during = fingerprint(fleet);
        final boolean waitAtLimitServed = originEnd(fleet, "p3") == EIGHT_AM_S + 900.0
                && TAXI.equals(modes(fleet, "p3"));
        final boolean overLimitRefused = TransportMode.walk.equals(modes(fleet, "p4"))
                && originEnd(fleet, "p4") == EIGHT_AM_S + 360.0;
        final boolean noWaitUntouched = originEnd(fleet, "p5") == EIGHT_AM_S + 1800.0
                && originEnd(fleet, "p6") == EIGHT_AM_S + 1800.0
                && TAXI.equals(modes(fleet, "p5")) && TAXI.equals(modes(fleet, "p6"));
        final boolean laterWaitServed = originEnd(fleet, "p7") == EIGHT_AM_S + 2160.0
                && TAXI.equals(modes(fleet, "p7"));
        final boolean noClockLeftAlone = Double.isNaN(originEnd(fleet, "p0"))
                && TAXI.equals(modes(fleet, "p0"));
        ok &= waitAtLimitServed && overLimitRefused && noWaitUntouched
                && laterWaitServed && noClockLeftAlone;
        json.append(",\"wait_at_the_limit_served_at_vehicle_start\":").append(waitAtLimitServed)
            .append(",\"wait_over_the_limit_refused_and_walks\":").append(overLimitRefused)
            .append(",\"free_vehicle_no_wait_untouched\":").append(noWaitUntouched)
            .append(",\"later_request_waits_for_the_first_free\":").append(laterWaitServed)
            .append(",\"no_clock_is_not_a_request\":").append(noClockLeftAlone)
            .append(",\"fingerprint_before_mobsim\":\"").append(during).append('"');

        // --- 3. the restore: every agent's own plan again --------------------
        engineOn.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        final String after = fingerprint(fleet);
        final boolean restored = before.equals(after);
        ok &= restored;
        json.append(",\"restored_after_mobsim\":").append(restored)
            .append(",\"fingerprint_after_mobsim\":\"").append(after).append('"');

        // --- 4. remodeRefused off: a refusal touches the plan not at all ----
        final Scenario keep = scenario(TaxiFleetConfigGroup.REPRESENTATION_FLEET, false);
        final TaxiFleetEngine keepEngine = engine(keep);
        keepEngine.notifyBeforeMobsim(new BeforeMobsimEvent(null, 0, false));
        final boolean refusedKept = TAXI.equals(modes(keep, "p4"))
                && originEnd(keep, "p3") == EIGHT_AM_S + 900.0;
        keepEngine.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        ok &= refusedKept;
        json.append(",\"remode_off_keeps_the_refused_trip\":").append(refusedKept);

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    /** The engine as the assembly builds it, with a router that knows no
     *  mode: the refused walk then takes RemodeRestore's null-route fallback. */
    private static TaxiFleetEngine engine(final Scenario scenario) {
        final Config config = scenario.getConfig();
        return new TaxiFleetEngine(scenario,
                                   () -> new TripRouter.Builder(config).build());
    }

    private static Scenario scenario(final String representation,
                                     final boolean remodeRefused) {
        final Config config = ConfigUtils.createConfig();
        config.global().setNumberOfThreads(1);
        final TaxiFleetConfigGroup taxi = ConfigUtils.addOrGetModule(
                config, TaxiFleetConfigGroup.NAME, TaxiFleetConfigGroup.class);
        taxi.representation = representation;
        taxi.fleetSize = FLEET;
        taxi.sampleFraction = 1.0;
        taxi.maxWaitMinutes = MAX_WAIT_MIN;
        taxi.deadheadMinutes = DEADHEAD_MIN;
        taxi.remodeRefused = remodeRefused;
        final Scenario scenario = ScenarioUtils.createScenario(config);
        final Population pop = scenario.getPopulation();
        for (final Object[] r : REQUESTS) {
            final Person p = pop.getFactory().createPerson(
                    Id.createPersonId((String) r[0]));
            final Plan plan = PopulationUtils.createPlan(p);
            final Activity home =
                    PopulationUtils.createActivityFromCoordAndLinkId("home", HOME_XY, HOME);
            final double offset = (Double) r[1];
            if (!Double.isNaN(offset)) {
                home.setEndTime(EIGHT_AM_S + offset);
            }
            plan.addActivity(home);
            final Leg leg = PopulationUtils.createLeg(TAXI);
            TripStructureUtils.setRoutingMode(leg, TAXI);
            leg.setTravelTime((Double) r[2]);
            plan.addLeg(leg);
            plan.addActivity(
                    PopulationUtils.createActivityFromCoordAndLinkId("work", WORK_XY, WORK));
            p.addPlan(plan);
            p.setSelectedPlan(plan);
            pop.addPerson(p);
        }
        return scenario;
    }

    private static Person get(final Scenario s, final String id) {
        return s.getPopulation().getPersons().get(Id.createPersonId(id));
    }

    private static List<Leg> legs(final Plan plan) {
        final List<Leg> out = new ArrayList<>();
        for (final PlanElement pe : plan.getPlanElements()) {
            if (pe instanceof Leg) {
                out.add((Leg) pe);
            }
        }
        return out;
    }

    /** The selected plan's leg modes, comma-separated. */
    private static String modes(final Scenario s, final String id) {
        final StringBuilder sb = new StringBuilder();
        for (final Leg leg : legs(get(s, id).getSelectedPlan())) {
            sb.append(sb.length() == 0 ? "" : ",").append(leg.getMode());
        }
        return sb.toString();
    }

    /** The first activity's end time in seconds, NaN where undefined. */
    private static double originEnd(final Scenario s, final String id) {
        final Activity origin =
                (Activity) get(s, id).getSelectedPlan().getPlanElements().get(0);
        return origin.getEndTime().isDefined() ? origin.getEndTime().seconds()
                                               : Double.NaN;
    }

    /** Every person in id order: modes, origin end time, the first leg's
     *  travel time where defined. */
    private static String fingerprint(final Scenario s) {
        final List<Id<Person>> ids =
                new ArrayList<>(s.getPopulation().getPersons().keySet());
        ids.sort(null);
        final StringBuilder sb = new StringBuilder();
        for (final Id<Person> id : ids) {
            final Leg first = legs(get(s, id.toString()).getSelectedPlan()).get(0);
            sb.append(id).append(':').append(modes(s, id.toString())).append('@')
              .append(originEnd(s, id.toString())).append('/')
              .append(first.getTravelTime().isDefined()
                      ? first.getTravelTime().seconds() : Double.NaN)
              .append(';');
        }
        return sb.toString();
    }
}
