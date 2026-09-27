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
import org.matsim.core.controler.events.ReplanningEvent;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.replanning.selectors.WorstPlanForRemovalSelector;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * The gate on {@link EscortCoherenceListener}: both sides of a household pair
 * are re-proposable, the declared scope proposes only what the demand
 * declared, and past the innovation cutoff the listener proposes nothing.
 *
 * <p>No mobsim, no network: three households are built in memory on four
 * locations and the listener is called with a {@link ReplanningEvent} exactly
 * as the controler calls it.
 * <ul>
 * <li>{@code e}: a driver's car tour to an {@code escort} activity and a child
 *     (no car) walking the same trip - the passenger side proposes the child's
 *     whole subtour as ride;</li>
 * <li>{@code j}: a ride passenger whose household driver has drifted to pt -
 *     the driver side proposes the driver's home-anchored subtour back to
 *     car;</li>
 * <li>{@code w}: a car-available adult on pt beside a household car leg with
 *     the same endpoints - the joint path proposes ride, and only under the
 *     {@code inferred} scope, because the demand declares nothing for it.</li>
 * </ul>
 * The last block runs a larger population at rates below one, re-selecting
 * the first plan before every iteration so proposals, draws and plan-memory
 * trimming repeat, and prints a fingerprint of every person's plans: it is
 * what a refactor of the listener is compared on, before and after.
 *
 * <p><b>Every value here is a FIXTURE</b> - locations, clocks, rates, the
 * cutoff - chosen so each path is exercised; none is a declared value.
 *
 * <p>One JSON line on stdout; exit 0 only if every asserted check holds.
 */
public final class EscortCoherenceProbe {

    private static final String HOME = "home";
    private static final Id<Link> HOME_LINK = Id.createLinkId("l_home");
    private static final Id<Link> SCHOOL_LINK = Id.createLinkId("l_school");
    private static final Id<Link> SHOP_LINK = Id.createLinkId("l_shop");
    private static final Id<Link> WORK_LINK = Id.createLinkId("l_work");
    private static final Coord HOME_XY = new Coord(0.0, 0.0);
    private static final Coord SCHOOL_XY = new Coord(2000.0, 0.0);
    private static final Coord SHOP_XY = new Coord(0.0, 3000.0);
    private static final Coord WORK_XY = new Coord(5000.0, 5000.0);

    /** Iterations 0..6 at fraction 0.5: innovation is off after iteration 3. */
    private static final int LAST_ITERATION = 6;
    private static final double INNOVATION_OFF_FRACTION = 0.5;
    private static final int FIRST_TAIL_ITERATION = 4;
    private static final double WINDOW_MIN = 10.0;

    private EscortCoherenceProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json =
                new StringBuilder("{\"probe\":\"EscortCoherenceProbe\"");
        boolean ok = true;

        // --- 1. inferred scope, innovating: all three pairs re-proposed ----
        final Scenario inferred = scenario(1.0, 1.0,
                RidePairingConfigGroup.COHERENCE_INFERRED, 5, 1);
        replan(inferred, 0);
        final boolean escortChild = allMode(inferred, "c_0", TransportMode.ride)
                && plans(inferred, "c_0") == 2;
        final boolean driftedDriver = allMode(inferred, "a1_0", TransportMode.car)
                && plans(inferred, "a1_0") == 2;
        final boolean jointAdult = allMode(inferred, "a4_0", TransportMode.ride)
                && plans(inferred, "a4_0") == 2;
        final boolean othersUntouched = plans(inferred, "d_0") == 1
                && plans(inferred, "a2_0") == 1 && plans(inferred, "a3_0") == 1;
        ok &= escortChild && driftedDriver && jointAdult && othersUntouched;
        json.append(",\"escort_child_proposed_ride\":").append(escortChild)
            .append(",\"drifted_driver_proposed_car\":").append(driftedDriver)
            .append(",\"joint_adult_proposed_ride\":").append(jointAdult)
            .append(",\"coherent_members_untouched\":").append(othersUntouched);

        // --- 2. declared scope: only the declared pairs --------------------
        final Scenario declared = scenario(1.0, 1.0,
                RidePairingConfigGroup.COHERENCE_DECLARED, 5, 1);
        replan(declared, 0);
        final boolean declaredOnly = allMode(declared, "c_0", TransportMode.ride)
                && allMode(declared, "a1_0", TransportMode.car)
                && plans(declared, "a4_0") == 1
                && allMode(declared, "a4_0", TransportMode.pt);
        ok &= declaredOnly;
        json.append(",\"declared_scope_proposes_declared_pairs_only\":")
            .append(declaredOnly);

        // --- 3. the tail: measured, nothing proposed or selected -----------
        final Scenario tail = scenario(1.0, 1.0,
                RidePairingConfigGroup.COHERENCE_INFERRED, 5, 1);
        final String tailBefore = fingerprint(tail);
        replan(tail, FIRST_TAIL_ITERATION);
        final boolean tailSilent = tailBefore.equals(fingerprint(tail));
        ok &= tailSilent;
        json.append(",\"tail_proposes_nothing\":").append(tailSilent);

        // --- 4. zero rates recover the unassisted behaviour ---------------
        final Scenario zero = scenario(0.0, 0.0,
                RidePairingConfigGroup.COHERENCE_INFERRED, 5, 1);
        final String zeroBefore = fingerprint(zero);
        replan(zero, 0);
        final boolean zeroSilent = zeroBefore.equals(fingerprint(zero));
        ok &= zeroSilent;
        json.append(",\"zero_rates_change_nothing\":").append(zeroSilent);

        // --- 5. the fingerprint: draws, repeats and trimming ---------------
        final Scenario many = scenario(0.5, 0.5,
                RidePairingConfigGroup.COHERENCE_INFERRED, 2, 25);
        for (int it = 0; it <= LAST_ITERATION; it++) {
            for (final Person p : many.getPopulation().getPersons().values()) {
                p.setSelectedPlan(p.getPlans().get(0));
            }
            replan(many, it);
        }
        final String print = fingerprint(many);
        final boolean memoryHeld = maxPlans(many) <= 2;
        ok &= memoryHeld;
        json.append(",\"plan_memory_held\":").append(memoryHeld)
            .append(",\"fingerprint\":\"")
            .append(Integer.toHexString(print.hashCode())).append('"')
            .append(",\"fingerprint_chars\":").append(print.length());

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    private static void replan(final Scenario scenario, final int iteration) {
        final EscortCoherenceListener listener = new EscortCoherenceListener(
                scenario, new WorstPlanForRemovalSelector());
        listener.notifyReplanning(new ReplanningEvent(null, iteration, false));
    }

    /** One scenario of `households` copies of the three fixture households. */
    private static Scenario scenario(final double escortRate,
                                     final double jointRate,
                                     final String scope, final int memory,
                                     final int households) {
        final Config config = ConfigUtils.createConfig();
        final RidePairingConfigGroup ride = new RidePairingConfigGroup();
        ride.enabled = true;
        ride.windowMinutes = WINDOW_MIN;
        ride.boundWindowMinutes = WINDOW_MIN;
        ride.escortCoherenceRate = escortRate;
        ride.jointCoherenceRate = jointRate;
        ride.coherenceScope = scope;
        config.addModule(ride);
        config.controller().setFirstIteration(0);
        config.controller().setLastIteration(LAST_ITERATION);
        config.replanning().setFractionOfIterationsToDisableInnovation(
                INNOVATION_OFF_FRACTION);
        config.replanning().setMaxAgentPlanMemorySize(memory);
        final Scenario scenario = ScenarioUtils.createScenario(config);
        final Population pop = scenario.getPopulation();
        for (int k = 0; k < households; k++) {
            // e: the escort pair, the child walking the driver's trip
            final String e = "e_" + k;
            person(pop, "d_" + k, e, EscortCoherenceListener.CAR_ALWAYS,
                   TransportMode.car, EscortCoherenceListener.ESCORT_ACTIVITY,
                   SCHOOL_LINK, SCHOOL_XY, 8.0, 8.1);
            final Person c = person(pop, "c_" + k, e, "never",
                   TransportMode.walk, "education", SCHOOL_LINK, SCHOOL_XY,
                   8.0, 15.0);
            declare(c, "d_" + k);
            // j: the ride passenger whose driver drifted to pt
            final String j = "j_" + k;
            person(pop, "a1_" + k, j, EscortCoherenceListener.CAR_ALWAYS,
                   TransportMode.pt, "shop", SHOP_LINK, SHOP_XY, 10.0, 11.0);
            final Person a2 = person(pop, "a2_" + k, j, "never",
                   TransportMode.ride, "shop", SHOP_LINK, SHOP_XY, 10.0, 11.0);
            declare(a2, "a1_" + k);
            // w: an undeclared car-available adult beside a household car leg
            final String w = "w_" + k;
            person(pop, "a3_" + k, w, EscortCoherenceListener.CAR_ALWAYS,
                   TransportMode.car, "work", WORK_LINK, WORK_XY, 7.5, 17.0);
            person(pop, "a4_" + k, w, EscortCoherenceListener.CAR_ALWAYS,
                   TransportMode.pt, "work", WORK_LINK, WORK_XY, 7.5, 17.0);
        }
        return scenario;
    }

    /** A person on one home-anchored two-trip tour by one mode. */
    private static Person person(final Population pop, final String id,
                                 final String household, final String carAvail,
                                 final String mode, final String outType,
                                 final Id<Link> outLink, final Coord outXy,
                                 final double leaveH, final double backH) {
        final Person p = pop.getFactory().createPerson(Id.createPersonId(id));
        p.getAttributes().putAttribute(
                RidePairingEngine.HOUSEHOLD_ATTRIBUTE, household);
        p.getAttributes().putAttribute(
                EscortCoherenceListener.CAR_AVAIL, carAvail);
        final Plan plan = PopulationUtils.createPlan(p);
        plan.addActivity(activity(HOME, HOME_LINK, HOME_XY, leaveH));
        plan.addLeg(leg(mode));
        plan.addActivity(activity(outType, outLink, outXy, backH));
        plan.addLeg(leg(mode));
        final Activity back = PopulationUtils.createActivityFromCoordAndLinkId(
                HOME, HOME_XY, HOME_LINK);
        plan.addActivity(back);
        p.addPlan(plan);
        p.setSelectedPlan(plan);
        pop.addPerson(p);
        return p;
    }

    /** The demand's declaration: both trips ride, served by `driver`. */
    private static void declare(final Person p, final String driver) {
        p.getAttributes().putAttribute(
                GatedSubtourModeChoice.GatedModule.BOUND_RIDE_ATTRIBUTE, "1,2");
        p.getAttributes().putAttribute(
                RidePairingEngine.BOUND_DRIVER_ATTRIBUTE, driver);
    }

    private static Activity activity(final String type, final Id<Link> link,
                                     final Coord xy, final double endH) {
        final Activity a =
                PopulationUtils.createActivityFromCoordAndLinkId(type, xy, link);
        a.setEndTime(endH * 3600.0);
        return a;
    }

    private static Leg leg(final String mode) {
        final Leg leg = PopulationUtils.createLeg(mode);
        TripStructureUtils.setRoutingMode(leg, mode);
        return leg;
    }

    private static Person get(final Scenario s, final String id) {
        return s.getPopulation().getPersons().get(Id.createPersonId(id));
    }

    private static int plans(final Scenario s, final String id) {
        return get(s, id).getPlans().size();
    }

    private static boolean allMode(final Scenario s, final String id,
                                   final String mode) {
        final List<Leg> legs = new ArrayList<>();
        for (final PlanElement pe : get(s, id).getSelectedPlan().getPlanElements()) {
            if (pe instanceof Leg) {
                legs.add((Leg) pe);
            }
        }
        if (legs.isEmpty()) {
            return false;
        }
        for (final Leg leg : legs) {
            if (!mode.equals(leg.getMode())) {
                return false;
            }
        }
        return true;
    }

    private static int maxPlans(final Scenario s) {
        int max = 0;
        for (final Person p : s.getPopulation().getPersons().values()) {
            max = Math.max(max, p.getPlans().size());
        }
        return max;
    }

    /** Every person, in id order: each plan's leg modes, the selected marked. */
    private static String fingerprint(final Scenario s) {
        final List<Id<Person>> ids =
                new ArrayList<>(s.getPopulation().getPersons().keySet());
        ids.sort(null);
        final StringBuilder sb = new StringBuilder();
        for (final Id<Person> id : ids) {
            final Person p = s.getPopulation().getPersons().get(id);
            sb.append(id).append(':');
            for (final Plan plan : p.getPlans()) {
                sb.append(plan == p.getSelectedPlan() ? '*' : ' ').append('[');
                for (final PlanElement pe : plan.getPlanElements()) {
                    if (pe instanceof Leg) {
                        sb.append(((Leg) pe).getMode()).append(',');
                    }
                }
                sb.append(']');
            }
            sb.append(';');
        }
        return sb.toString();
    }
}
