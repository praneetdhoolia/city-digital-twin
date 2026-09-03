package citysim;

import java.util.Collections;
import java.util.List;
import java.util.Set;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripStructureUtils;

/**
 * The gate on {@link RemodeRestore} (issue #113): a trip forced to walk for
 * one iteration gets its mode back through a re-find by endpoints, after the
 * router has replaced the plan's leg objects - and a restore through the
 * stale leg reference, which is what the taxi engine did, changes nothing.
 *
 * <p>No scenario and no mobsim: the probe builds a plan by hand, re-modes a
 * taxi trip the way the engines do (mode walk, routing mode walk, route
 * null), then does to the plan exactly what {@code PersonPrepareForSim}
 * does to a trip with a null route - {@code TripRouter.insertTrip} with a
 * freshly routed walk leg, which replaces the trip's elements - and checks:
 * <ul>
 * <li>the stale reference: setting the OLD leg back to taxi leaves the
 *     plan's leg on walk (the defect, reproduced);</li>
 * <li>the re-find: {@code RemodeRestore.restore} puts taxi back on the
 *     plan's leg, with the routing mode, and leaves the other trip alone;</li>
 * <li>consume-once: a person with two trips between the same links has
 *     each restored, not the first twice.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class RemodeRestoreProbe {

    private static final String TAXI = "taxi";
    private static final Id<Link> HOME = Id.createLinkId("L1");
    private static final Id<Link> WORK = Id.createLinkId("L2");

    private RemodeRestoreProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json = new StringBuilder("{");
        boolean ok = true;

        // --- 1. the stale reference changes nothing -----------------------
        Plan plan = twoTripPlan();
        Leg forced = firstLeg(plan);
        remodeToWalk(forced);
        replaceTripAsRouterWould(plan, 0);
        forced.setMode(TAXI);                    // the old engine's restore
        TripStructureUtils.setRoutingMode(forced, TAXI);
        final boolean staleIsOrphan = TransportMode.walk.equals(
                firstLeg(plan).getMode());
        ok &= staleIsOrphan;
        json.append("\"stale_reference_leaves_walk\":").append(staleIsOrphan);

        // --- 2. the re-find restores the plan's own leg ------------------
        plan = twoTripPlan();
        forced = firstLeg(plan);
        remodeToWalk(forced);
        replaceTripAsRouterWould(plan, 0);
        final Set<Activity> ledger = RemodeRestore.ledger();
        final boolean found = RemodeRestore.restore(
                plan, HOME, WORK, TransportMode.walk, TAXI, null, ledger);
        final Leg restored = firstLeg(plan);
        final boolean restoredMode = TAXI.equals(restored.getMode())
                && TAXI.equals(TripStructureUtils.getRoutingMode(restored));
        final boolean otherUntouched = TAXI.equals(legs(plan).get(1).getMode())
                && legs(plan).size() == 2;
        ok &= found && restoredMode && otherUntouched;
        json.append(",\"refind_found\":").append(found)
            .append(",\"refind_restores_taxi\":").append(restoredMode)
            .append(",\"other_trip_untouched\":").append(otherUntouched);

        // --- 3. consume-once over two trips with the same endpoints -------
        plan = PopulationUtils.createPlan();
        addAct(plan, "home", HOME, 8 * 3600);
        plan.addLeg(PopulationUtils.createLeg(TAXI));
        addAct(plan, "work", WORK, 12 * 3600);
        plan.addLeg(PopulationUtils.createLeg(TAXI));
        addAct(plan, "home", HOME, 14 * 3600);
        plan.addLeg(PopulationUtils.createLeg(TAXI));
        addAct(plan, "work", WORK, 18 * 3600);
        plan.addLeg(PopulationUtils.createLeg(TAXI));
        addAct(plan, "home", HOME, Double.NaN);
        for (final Leg leg : legs(plan)) {
            TripStructureUtils.setRoutingMode(leg, TAXI);
        }
        remodeToWalk(legs(plan).get(0));
        remodeToWalk(legs(plan).get(2));
        replaceTripAsRouterWould(plan, 0);
        replaceTripAsRouterWould(plan, 2);
        final Set<Activity> once = RemodeRestore.ledger();
        int count = 0;
        for (int i = 0; i < 2; i++) {
            if (RemodeRestore.restore(plan, HOME, WORK, TransportMode.walk,
                                      TAXI, null, once)) {
                count++;
            }
        }
        final List<Leg> after = legs(plan);
        final boolean bothRestored = count == 2 && after.size() == 4
                && TAXI.equals(after.get(0).getMode())
                && TAXI.equals(after.get(2).getMode());
        ok &= bothRestored;
        json.append(",\"consume_once_restores_both\":").append(bothRestored)
            .append(",\"restored_count\":").append(count);

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    private static Plan twoTripPlan() {
        final Plan plan = PopulationUtils.createPlan();
        addAct(plan, "home", HOME, 8 * 3600);
        plan.addLeg(PopulationUtils.createLeg(TAXI));
        addAct(plan, "work", WORK, 17 * 3600);
        plan.addLeg(PopulationUtils.createLeg(TAXI));
        addAct(plan, "home", HOME, Double.NaN);
        for (final Leg leg : legs(plan)) {
            TripStructureUtils.setRoutingMode(leg, TAXI);
        }
        return plan;
    }

    private static void addAct(final Plan plan, final String type,
                               final Id<Link> link, final double end) {
        final Activity act = PopulationUtils.createActivityFromLinkId(type, link);
        if (!Double.isNaN(end)) {
            act.setEndTime(end);
        }
        plan.addActivity(act);
    }

    /** What the engines do to a leg the supply refused. */
    private static void remodeToWalk(final Leg leg) {
        leg.setMode(TransportMode.walk);
        TripStructureUtils.setRoutingMode(leg, TransportMode.walk);
        leg.setRoute(null);
    }

    /** What PersonPrepareForSim's PlanRouter does to a trip with no route:
     *  the trip's elements are REPLACED by freshly created legs. */
    private static void replaceTripAsRouterWould(final Plan plan,
                                                 final int tripIndex) {
        final TripStructureUtils.Trip trip =
                TripStructureUtils.getTrips(plan).get(tripIndex);
        final Leg routed = PopulationUtils.createLeg(TransportMode.walk);
        TripStructureUtils.setRoutingMode(routed, TransportMode.walk);
        TripRouter.insertTrip(plan, trip.getOriginActivity(),
                Collections.singletonList(routed),
                trip.getDestinationActivity());
    }

    private static List<Leg> legs(final Plan plan) {
        final List<Leg> out = new java.util.ArrayList<>();
        for (final PlanElement pe : plan.getPlanElements()) {
            if (pe instanceof Leg) {
                out.add((Leg) pe);
            }
        }
        return out;
    }

    private static Leg firstLeg(final Plan plan) {
        return legs(plan).get(0);
    }
}
