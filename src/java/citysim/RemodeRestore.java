package citysim;

import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import com.google.inject.Provider;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.api.core.v01.population.Route;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Trip;
import org.matsim.core.utils.misc.OptionalTime;
import org.matsim.core.utils.timing.TimeInterpretation;
import org.matsim.core.utils.timing.TimeTracker;
import org.matsim.facilities.ActivityFacilities;
import org.matsim.facilities.FacilitiesUtils;

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
     * One trip to be executed in another mode this iteration - ROUTED by the
     * engine that forces it, never left for {@code PersonPrepareForSim}
     * (F35, 12 September 2026).
     *
     * <p>The re-mode used to leave the fallback leg's route null "so the
     * router rebuilds the trip" - which it did, and a great deal more: MATSim's
     * {@code PersonPrepareForSim.run(Person)} hands the WHOLE plan to
     * {@code PlanRouter} when any one leg of it has no route, for every plan
     * the person holds, not the selected one. The taxi engine refuses ~48,000
     * requests an iteration at 25 % and restored each with a null taxi route,
     * so every plan that had ever carried a refused taxi trip was re-routed
     * end to end - every car trip, every pt request through the raptor and
     * the network-walk router - every iteration, for good. The profile of
     * {@code 20260912T162831_4it_25pct} read it at 24 % of every CPU sample
     * in the run (62,094 of 257,332 under {@code PersonPrepareForSim}, all in
     * {@code NetworkRoutingInclAccessEgressModule}). That was an undeclared
     * ReRoute strategy on a third of the population, and it is gone: the
     * trip is routed here, in parallel, exactly as {@code PlanRouter} would
     * route it - same {@link TripRouter}, same facilities, same departure
     * time from a {@link TimeTracker} over the plan up to the origin - and
     * the elements it replaces are kept so the restore puts the ORIGINAL
     * trip back, routes and all, and nothing is left null.
     */
    static final class Remode {
        final Plan plan;
        final Trip trip;
        final String mode;
        /** When the trip leaves if the plan's own times cannot say. */
        final double fallbackDeparture;
        /** Filled by {@link #route}: the routed trip, or null if unroutable. */
        List<? extends PlanElement> routed;
        /** Filled by {@link #apply}: the elements the routed trip replaced. */
        List<PlanElement> original;

        Remode(final Plan plan, final Trip trip, final String mode,
               final double fallbackDeparture) {
            this.plan = plan;
            this.trip = trip;
            this.mode = mode;
            this.fallbackDeparture = fallbackDeparture;
        }
    }

    /**
     * The clock at which the trip leaves, as {@code PlanRouter} computes it:
     * a {@link TimeTracker} fed every element before the origin activity.
     */
    static double departureOf(final Remode job, final TimeInterpretation time) {
        final TimeTracker tracker = new TimeTracker(time);
        for (final Trip t : TripStructureUtils.getTrips(job.plan)) {
            final OptionalTime at = tracker.addActivity(t.getOriginActivity());
            if (t.getOriginActivity() == job.trip.getOriginActivity()) {
                return at.isDefined() ? at.seconds() : job.fallbackDeparture;
            }
            tracker.addElements(t.getTripElements());
        }
        return job.fallbackDeparture;
    }

    /**
     * Route every job on {@code threads} workers, one {@link TripRouter}
     * each, results written back onto the jobs so the caller applies them in
     * its own order. A job the router cannot serve (a null or an exception)
     * is left {@code routed == null}; {@link #apply} then falls back to the
     * null-route leg the engines always wrote, and the caller counts it. A
     * worker's own failure is the iteration's failure.
     */
    static void route(final List<Remode> jobs, final Provider<TripRouter> routers,
                      final ActivityFacilities facilities,
                      final TimeInterpretation time, final int threads) {
        final int n = jobs.size();
        if (n == 0) {
            return;
        }
        final int workers = Math.max(1, Math.min(n, threads));
        final ExecutorService pool = Executors.newFixedThreadPool(workers);
        final List<Future<?>> futures = new ArrayList<>(workers);
        for (int w = 0; w < workers; w++) {
            final int from = (int) ((long) w * n / workers);
            final int to = (int) ((long) (w + 1) * n / workers);
            futures.add(pool.submit(() -> {
                final TripRouter router = routers.get();
                for (int i = from; i < to; i++) {
                    final Remode job = jobs.get(i);
                    try {
                        job.routed = router.calcRoute(job.mode,
                                FacilitiesUtils.toFacility(
                                        job.trip.getOriginActivity(), facilities),
                                FacilitiesUtils.toFacility(
                                        job.trip.getDestinationActivity(), facilities),
                                departureOf(job, time), job.plan.getPerson(),
                                job.trip.getTripAttributes());
                    } catch (final RuntimeException unroutable) {
                        job.routed = null;
                    }
                }
            }));
        }
        pool.shutdown();
        try {
            for (final Future<?> f : futures) {
                f.get();
            }
        } catch (final InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("re-mode routing interrupted", ex);
        } catch (final ExecutionException ex) {
            throw new IllegalStateException("re-mode routing failed", ex.getCause());
        }
    }

    /**
     * Put the routed trip into the plan and keep what it replaced. Returns
     * true if the trip was routed, false if the null-route fallback was used.
     */
    static boolean apply(final Remode job) {
        final boolean routed = job.routed != null && !job.routed.isEmpty();
        List<? extends PlanElement> elements = job.routed;
        if (!routed) {
            final Leg leg = PopulationUtils.createLeg(job.mode);
            TripStructureUtils.setRoutingMode(leg, job.mode);
            leg.setRoute(null);
            elements = Collections.singletonList(leg);
        }
        job.original = TripRouter.insertTrip(job.plan,
                job.trip.getOriginActivity(), elements,
                job.trip.getDestinationActivity());
        return routed;
    }

    /**
     * Give the trip its ORIGINAL elements back - the legs, routes and stage
     * activities the re-mode took out - re-found by endpoints and executed
     * mode as {@link #restore} does; true if a trip was found and replaced.
     */
    static boolean restoreOriginal(final Plan plan, final Id<Link> from,
                                   final Id<Link> to, final String executedMode,
                                   final List<PlanElement> original,
                                   final Set<Activity> consumed) {
        final Trip target = findTrip(plan, from, to, executedMode, consumed);
        if (target == null || original == null || original.isEmpty()) {
            return false;
        }
        TripRouter.insertTrip(plan, target.getOriginActivity(), original,
                target.getDestinationActivity());
        if (consumed != null) {
            consumed.add(target.getOriginActivity());
        }
        return true;
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
