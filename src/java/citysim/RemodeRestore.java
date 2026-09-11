package citysim;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Route;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Trip;

/**
 * Giving a re-moded trip its mode back after the mobsim (DECISIONS.md 9.81,
 * issue #113) - shared by {@link RidePairingEngine} and
 * {@link TaxiFleetEngine}.
 *
 * <p>Both engines execute a trip the supply cannot serve as a walk for ONE
 * iteration and give the mode back afterwards, so the walk is scored and the
 * alternative survives. Neither can hold the {@link Leg} object across the
 * mobsim to do it: the re-mode nulls the route, a null route is what makes
 * {@code PersonPrepareForSim} run {@code PlanRouter} over the trip, and
 * {@code TripRouter.insertTrip} REPLACES the trip's plan elements with new
 * leg objects. A restore through the old reference writes to an orphan and
 * changes nothing - the ride engine measured it on arm 20260826T051938
 * (byte-identical ride-leg counts while the log reported 61,409 legs
 * "restored"), fixed it by re-finding the trip, and the taxi engine kept the
 * orphaned reference until the 3 September 2026 assessment found it.
 *
 * <p>So the trip is RE-FOUND in the selected plan by the endpoints the engine
 * recorded, the executed mode confirms it is the trip that was forced and
 * not some other walk, and the whole trip is replaced - never one leg of it,
 * because a re-routed walk can be multi-leg and MATSim requires one routing
 * mode per trip (arm 20260826T053741). Each trip is consumed once per pass:
 * a person with two trips between the same links - out in the morning, out
 * again in the afternoon - has each restored, not the first twice.
 */
final class RemodeRestore {

    private RemodeRestore() {
    }

    /** A consume-once ledger for one restore pass: origin activities done. */
    static Set<Activity> ledger() {
        return Collections.newSetFromMap(
                new IdentityHashMap<Activity, Boolean>());
    }

    /**
     * The first trip of the plan between the two links whose every leg is of
     * the executed mode and whose origin is not yet in the ledger, or null.
     */
    static Trip findTrip(final Plan plan, final Id<Link> from,
                         final Id<Link> to, final String executedMode,
                         final Set<Activity> consumed) {
        for (final Trip trip : TripStructureUtils.getTrips(plan)) {
            final Activity origin = trip.getOriginActivity();
            if (consumed != null && consumed.contains(origin)) {
                continue;
            }
            if (!from.equals(origin.getLinkId())
                    || !to.equals(trip.getDestinationActivity().getLinkId())) {
                continue;
            }
            if (!isAllMode(trip, executedMode)) {
                continue;
            }
            return trip;
        }
        return null;
    }

    /**
     * Replace the forced trip with one leg of {@code mode} carrying
     * {@code route} (null: routed afresh next iteration); true if a trip was
     * found and replaced, false if the plan no longer holds one.
     */
    static boolean restore(final Plan plan, final Id<Link> from,
                           final Id<Link> to, final String executedMode,
                           final String mode, final Route route,
                           final Set<Activity> consumed) {
        final Trip target = findTrip(plan, from, to, executedMode, consumed);
        if (target == null) {
            return false;
        }
        final Leg leg = PopulationUtils.createLeg(mode);
        leg.setRoute(route);
        TripStructureUtils.setRoutingMode(leg, mode);
        TripRouter.insertTrip(plan, target.getOriginActivity(),
                Collections.singletonList(leg),
                target.getDestinationActivity());
        if (consumed != null) {
            consumed.add(target.getOriginActivity());
        }
        return true;
    }

    /** Every leg of the trip is of the mode - the trip the engine forced,
     *  not some other trip the agent was always going to make that way. */
    static boolean isAllMode(final Trip trip, final String mode) {
        return isAllMode(trip.getLegsOnly(), mode);
    }

    /**
     * The trip the engine forced, executed as ONE leg of the fallback mode.
     *
     * <p>The whole trip is replaced, never one leg of it (#167, 12 September
     * 2026): under {@code routing.accessEgressType = accessEgressModeToLink}
     * a ride or taxi trip is five legs - {@code non_network_walk}, {@code
     * walk}, the main leg, {@code walk}, {@code non_network_walk} - every one
     * carrying the main mode as its routingMode. Re-moding the main leg alone
     * left its four siblings at the old routingMode, and MATSim's
     * {@code PersonPrepareForSim} refused the trip before iteration 0's
     * mobsim ("Found a trip whose legs have different routingModes") on every
     * such agent - which is what killed every intermodal probe and was read
     * as a failure inside MATSim's pre-simulation pass. Under {@code none} a
     * trip is one leg and the two treatments are identical, so callers keep
     * the in-place re-mode there and this is the multi-leg path. The route
     * is left null so the router rebuilds the trip in the fallback mode.
     */
    static void remodeTrip(final Plan plan, final Trip trip, final String mode) {
        final Leg leg = PopulationUtils.createLeg(mode);
        TripStructureUtils.setRoutingMode(leg, mode);
        leg.setRoute(null);
        TripRouter.insertTrip(plan, trip.getOriginActivity(),
                Collections.singletonList(leg),
                trip.getDestinationActivity());
    }

    /** The trip of the plan holding this exact leg object, or null. */
    static Trip tripOf(final Plan plan, final Leg leg) {
        for (final Trip trip : TripStructureUtils.getTrips(plan)) {
            for (final Object pe : trip.getTripElements()) {
                if (pe == leg) {
                    return trip;
                }
            }
        }
        return null;
    }

    /**
     * The same test on legs the caller already holds.
     *
     * <p>{@code Trip.getLegsOnly()} builds a fresh filtered list on every call,
     * and this test used to call it twice by itself. {@code TaxiFleetEngine}
     * then asked for the legs a third time for the trip it accepted, so every
     * taxi-eligible trip of every person, every iteration, allocated three
     * throwaway lists - on the order of 2 M an iteration at 25%.
     */
    static boolean isAllMode(final java.util.List<Leg> legs, final String mode) {
        if (legs.isEmpty()) {
            return false;
        }
        for (final Leg leg : legs) {
            // the trip's identity is its ROUTING mode where one is set: under
            // accessEgressModeToLink a taxi trip's access legs are walk legs
            // carrying routingMode taxi, and the leg-mode test found no taxi
            // trip at all ("taxiFleet: no taxi legs in the selected plans" on
            // every intermodal probe, #167). A leg without a routingMode is
            // judged by its own mode, exactly as before.
            final String rm = TripStructureUtils.getRoutingMode(leg);
            if (!mode.equals(rm != null ? rm : leg.getMode())) {
                return false;
            }
        }
        return true;
    }
}
