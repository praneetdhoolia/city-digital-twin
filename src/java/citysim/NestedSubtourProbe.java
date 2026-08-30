package citysim;

import java.util.List;

import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Population;
import org.matsim.api.core.v01.population.PopulationFactory;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Subtour;
import org.matsim.core.router.TripStructureUtils.Trip;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.api.core.v01.Scenario;

/**
 * What does {@code TripStructureUtils.getSubtours} return for a NESTED plan,
 * and in what order?
 *
 * <p>{@code EscortCoherenceListener.subtourContaining} returns the FIRST
 * subtour that contains a given trip. If the innermost subtour is returned
 * first, converting "the whole subtour" to ride converts only the inner one and
 * leaves the OUTER subtour holding both car and ride - which is the exact state
 * {@code ChooseRandomLegModeForSubtour} refuses with
 * {@code IllegalStateException: Subtour contains a mix of chain- and
 * non-chainbased modes}.
 *
 * <p>This probe settles the ordering and the containment semantics on a plan
 * built here, so the answer does not depend on any run. It asserts nothing and
 * changes nothing; it prints what MATSim does.
 *
 * <p>The plan is home -&gt; work -&gt; lunch -&gt; work -&gt; home, every trip
 * by car. That has an inner subtour (work-lunch-work) nested inside an outer
 * one (home..home).
 */
public final class NestedSubtourProbe {

    private NestedSubtourProbe() {
    }

    private static Activity act(final PopulationFactory f, final String type,
                                final double x, final double y,
                                final String link, final double end) {
        final Activity a = f.createActivityFromCoord(type, new Coord(x, y));
        a.setLinkId(Id.create(link, Link.class));
        a.setEndTime(end);
        return a;
    }

    public static void main(final String[] args) {
        final Scenario sc = ScenarioUtils.createScenario(
                ConfigUtils.createConfig());
        final Population pop = sc.getPopulation();
        final PopulationFactory f = pop.getFactory();

        final Person p = f.createPerson(Id.createPersonId("probe1"));
        final Plan plan = f.createPlan();

        // home -> work -> lunch -> work -> home, all by car
        plan.addActivity(act(f, "home", 0, 0, "L_home", 8 * 3600));
        plan.addLeg(leg(f, "car"));
        plan.addActivity(act(f, "work", 1000, 0, "L_work", 12 * 3600));
        plan.addLeg(leg(f, "car"));
        plan.addActivity(act(f, "lunch", 1200, 0, "L_lunch", 13 * 3600));
        plan.addLeg(leg(f, "car"));
        plan.addActivity(act(f, "work", 1000, 0, "L_work", 17 * 3600));
        plan.addLeg(leg(f, "car"));
        plan.addActivity(act(f, "home", 0, 0, "L_home", 24 * 3600));

        p.addPlan(plan);
        pop.addPerson(p);

        final double coordDist =
                sc.getConfig().subtourModeChoice().getCoordDistance();
        System.out.println("coordDistance = " + coordDist);

        final List<Trip> trips = TripStructureUtils.getTrips(plan);
        System.out.println("trips in plan = " + trips.size());
        for (int i = 0; i < trips.size(); i++) {
            System.out.println("   trip " + i + "  "
                    + trips.get(i).getOriginActivity().getType() + " -> "
                    + trips.get(i).getDestinationActivity().getType());
        }

        final List<Subtour> subs = new java.util.ArrayList<>(
                TripStructureUtils.getSubtours(plan, coordDist));
        System.out.println("subtours returned = " + subs.size()
                + "   (in the order getSubtours returns them)");
        for (int i = 0; i < subs.size(); i++) {
            final Subtour st = subs.get(i);
            System.out.println("   subtour " + i
                    + "  getTrips()=" + st.getTrips().size()
                    + "  withoutSubSubtours="
                    + st.getTripsWithoutSubSubtours().size()
                    + "  closed=" + st.isClosed()
                    + "  hasParent=" + (st.getParent() != null));
            for (final Trip t : st.getTrips()) {
                System.out.println("        "
                        + t.getOriginActivity().getType() + " -> "
                        + t.getDestinationActivity().getType());
            }
        }

        // Reproduce subtourContaining's selection for the work->lunch trip,
        // which is the one an escort binding would name.
        final Trip lunchTrip = trips.get(1);
        System.out.println("subtourContaining(work->lunch) picks:");
        for (final Subtour st : subs) {
            boolean found = false;
            for (final Trip t : st.getTrips()) {
                if (t.getOriginActivity() == lunchTrip.getOriginActivity()
                        && t.getDestinationActivity()
                            == lunchTrip.getDestinationActivity()) {
                    found = true;
                    break;
                }
            }
            if (found) {
                System.out.println("   -> first match: a subtour with "
                        + st.getTrips().size() + " trip(s), hasParent="
                        + (st.getParent() != null));
                Subtour root = st;
                while (root.getParent() != null) {
                    root = root.getParent();
                }
                System.out.println("   -> AFTER walking to the root: "
                        + root.getTrips().size() + " trip(s), hasParent="
                        + (root.getParent() != null));
                System.out.println(root.getTrips().size() == trips.size()
                        ? "   ROOT COVERS EVERY TRIP - no enclosing subtour "
                          + "can be left mixed"
                        : "   root does NOT cover every trip");
                System.out.println(st.getTrips().size() < trips.size()
                        ? "   THIS IS NOT THE WHOLE PLAN: converting only these "
                          + "leaves the enclosing subtour MIXED"
                        : "   this covers every trip, so no mix can remain");
                break;
            }
        }
    }

    private static Leg leg(final PopulationFactory f, final String mode) {
        final Leg l = f.createLeg(mode);
        TripStructureUtils.setRoutingMode(l, mode);
        return l;
    }
}
