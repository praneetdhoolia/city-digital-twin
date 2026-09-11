package citysim;

import ch.sbb.matsim.routing.pt.raptor.RaptorParameters;
import ch.sbb.matsim.routing.pt.raptor.RaptorParametersForPerson;
import ch.sbb.matsim.routing.pt.raptor.RaptorUtils;
import ch.sbb.matsim.routing.pt.raptor.SwissRailRaptorRoutingModuleProvider;
import com.google.inject.Inject;
import com.google.inject.Provider;
import com.google.inject.Singleton;
import com.google.inject.name.Named;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicLong;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.config.Config;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.router.DefaultRoutingRequest;
import org.matsim.core.router.LinkWrapperFacility;
import org.matsim.core.router.RoutingModule;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.RoutingRequest;

/**
 * The PT routing module with the direct walk evaluated ON THE NETWORK
 * (DECISIONS.md 9.121, issue #94).
 *
 * <p>SwissRailRaptor compares every transit route against a direct walk it
 * builds from the beeline distance; a beeline crosses water, so a Stockton
 * resident bound for the CBD was handed a ~1 km "walk" the network then
 * executed as a ~20 km road detour - 88 of 110 such trips at F16 iteration
 * 10, against 1 on the ferry. This module keeps the raptor's rule and its
 * declared {@code transitRouter.directWalkFactor}; it only changes WHAT the
 * direct walk is: the walk routing module's route on the walk network, whose
 * travel time is what the agent would actually walk.
 *
 * <p>Two parts. {@link NoDirectWalkParameters} hands the raptor parameters
 * whose direct-walk factor is effectively infinite, so the raptor answers
 * with its best transit route whenever one exists and never with a beeline
 * walk. This module then routes the direct walk on the network, prices it
 * exactly as the raptor would have priced its own - walk time times the
 * raptor's marginal utility of walking, times the declared factor - reads
 * the transit route's cost from the attribute the raptor writes on its legs
 * ({@code totalRouteCost}), and returns the cheaper. When the raptor finds no
 * transit route at all, the network walk is returned: an honest walk, not a
 * beeline one.
 *
 * <p>No value is invented and no declared value moves: the factor, the
 * marginal utilities and the walk speed are the run's own; the ferry, the
 * bus and the walk compete on the ground they exist on. Bound by
 * {@link CitysimControler} when the registry field
 * {@code RUN.transit_router.direct_walk_basis} is {@code network}; the factor
 * is {@code RUN.transit_router.direct_walk_factor}.
 */
public final class NetworkDirectWalkPtRouter implements RoutingModule {
    private static final Logger LOG = LogManager.getLogger(NetworkDirectWalkPtRouter.class);

    private final RoutingModule transit;
    private final RoutingModule walk;
    private final RaptorParametersForPerson parameters;
    private final double directWalkFactor;
    private final Set<String> transitModes;
    private final Network network;
    // RUN-LIFETIME counters, and they must be static (issue #159). The
    // binding is `addRoutingModuleBinding(pt).toProvider(RouterProvider)`
    // with NO scope, so Guice builds a NEW router for every routing thread in
    // every iteration: instance counters restart at zero perhaps 1,600 times
    // in a 100-iteration arm. Two things followed. The "log the first 3"
    // sample became "log the first 3 PER THREAD PER ITERATION" and emitted
    // 19,469 lines on the F28 arm - about 36% of its log - and the
    // every-100,000th progress line has NEVER fired once, because no
    // single thread-iteration ever reaches 100,000 of anything. Static is
    // correct rather than convenient here: one JVM runs exactly one scenario,
    // so the class IS the run, and the counters describe it. Atomic because
    // the routing threads increment them concurrently; each increment is read
    // back once, from the value the increment returned, so no line reports a
    // count that never existed.
    //
    // REQUESTS is the denominator and the other three are its parts. It exists
    // because they did not share one: DECIDED counted only the requests that
    // reached the comparison, so the 853,357 requests the raptor could not
    // answer on the F31 gate arm were reported ALONGSIDE a "decisions" total
    // that excluded them, and the line could be read as either a third or a
    // half of the traffic depending on what the reader assumed. Worse, the
    // no-transit branch returns before the progress gate, so a third of the
    // arm's requests could never fire the line the comment below promises is
    // evaluated on every one of them.
    private static final AtomicLong REQUESTS = new AtomicLong();
    private static final AtomicLong DECIDED = new AtomicLong();
    private static final AtomicLong WALKED = new AtomicLong();
    private static final AtomicLong NO_TRANSIT = new AtomicLong();
    // #167: the beeline walk legs INSIDE a transit answer - the raptor's
    // transfers between stops, and any access or egress it could not route -
    // put on the walk network here, or left as the beeline they were when
    // the walk network cannot reach one end (a stop on a link walk is not
    // permitted on). Both counted, so the residual the mobsim teleports is
    // named at its source.
    private static final AtomicLong INNER_WALKS_ROUTED = new AtomicLong();
    private static final AtomicLong INNER_WALKS_UNROUTABLE = new AtomicLong();

    NetworkDirectWalkPtRouter(final RoutingModule transit, final RoutingModule walk,
                              final RaptorParametersForPerson parameters,
                              final Config config, final Network network) {
        this.transit = transit;
        this.walk = walk;
        this.parameters = parameters;
        this.network = network;
        this.directWalkFactor = config.transitRouter().getDirectWalkFactor();
        this.transitModes = new HashSet<>(config.transit().getTransitModes());
    }

    @Override
    public List<? extends PlanElement> calcRoute(final RoutingRequest request) {
        final long requests = REQUESTS.incrementAndGet();
        // Every request, before any branch can return: the counters below are
        // parts of THIS total, and a line that reports parts against a total
        // they are not parts of is a line nobody can act on.
        if (requests % 100000 == 0) {
            LOG.info("ptDirectWalk: {} pt routing requests, {} without any transit route, "
                     + "{} compared, of which {} chose the network walk",
                     requests, NO_TRANSIT.get(), DECIDED.get(), WALKED.get());
        }
        final List<? extends PlanElement> transitLegs = this.transit.calcRoute(request);
        final List<? extends PlanElement> walkLegs = this.walk.calcRoute(request);
        if (transitLegs == null || !boardsTransit(transitLegs)) {
            // the raptor found no transit route: the walk is the walk the
            // network offers, not a line across the map
            NO_TRANSIT.incrementAndGet();
            return walkLegs;
        }
        final List<? extends PlanElement> transitOnNetwork =
                networkWalksInside(transitLegs, request);
        final double transitCost = transitCost(transitOnNetwork);
        if (Double.isNaN(transitCost)) {
            return transitOnNetwork;         // cost unreadable: keep the raptor's answer
        }
        final Person person = request.getPerson();
        final RaptorParameters p = this.parameters.getRaptorParameters(person);
        final double walkUtlPerS = p.getMarginalUtilityOfTravelTime_utl_s(TransportMode.walk);
        final double walkSeconds = travelSeconds(walkLegs);
        // the raptor's own pricing of a direct walk, applied to the network walk
        final double walkCost = -walkUtlPerS * walkSeconds * this.directWalkFactor;
        DECIDED.incrementAndGet();
        if (walkCost < transitCost) {
            if (WALKED.incrementAndGet() <= 3) {
                LOG.info("ptDirectWalk: network walk {} s (cost {}) beats transit (cost {}) for person {}",
                         Math.round(walkSeconds), Math.round(walkCost), Math.round(transitCost),
                         person == null ? "?" : person.getId());
            }
            return walkLegs;
        }
        return transitOnNetwork;
    }

    /**
     * Put every beeline walk leg of a transit answer on the walk network.
     *
     * <p>SwissRailRaptor draws its transfers between stops as beelines with a
     * generic route whatever {@code useIntermodalAccessEgress} says, and the
     * mobsim can only teleport such a leg (GOAL.md requirement 1 breach,
     * #167: 386 of 553 teleported walk legs on the 12 September probe had
     * BOTH ends on walkable links - transfers, not landings). Each such leg
     * is replaced by the walk router's WHOLE answer between the leg's own two
     * links: the network walk leg, and where a stop sits on a link walk is
     * not permitted on, MATSim's own last-metre {@code non_network_walk}
     * stub from the nearest walkable link to the stop - the same way a car
     * trip reaches its parked car under {@code accessEgressModeToLink}. The
     * first cut kept only the network route and dropped the stub, and the
     * transit engine refused the agent for arriving at the wrong link
     * ("tries to enter a transit stop at link 24641 but really is at 7522").
     * Every inserted leg carries the trip's own routing mode, so the trip's
     * identity is untouched. Where the walk router cannot answer at all the
     * beeline stays and is counted.
     */
    private List<? extends PlanElement> networkWalksInside(
            final List<? extends PlanElement> legs, final RoutingRequest request) {
        final List<PlanElement> out = new java.util.ArrayList<>(legs.size() + 4);
        for (final PlanElement pe : legs) {
            if (!(pe instanceof Leg)) {
                out.add(pe);
                continue;
            }
            final Leg leg = (Leg) pe;
            if (!TransportMode.walk.equals(leg.getMode()) || leg.getRoute() == null
                    || leg.getRoute() instanceof NetworkRoute) {
                out.add(pe);
                continue;
            }
            final Link from = this.network.getLinks().get(leg.getRoute().getStartLinkId());
            final Link to = this.network.getLinks().get(leg.getRoute().getEndLinkId());
            List<? extends PlanElement> routed = null;
            if (from != null && to != null) {
                try {
                    routed = this.walk.calcRoute(DefaultRoutingRequest.withoutAttributes(
                            new LinkWrapperFacility(from), new LinkWrapperFacility(to),
                            request.getDepartureTime(), request.getPerson()));
                } catch (final RuntimeException unroutable) {   // counted below
                    routed = null;
                }
            }
            boolean hasNetworkLeg = false;
            if (routed != null) {
                for (final PlanElement r : routed) {
                    if (r instanceof Leg && ((Leg) r).getRoute() instanceof NetworkRoute) {
                        hasNetworkLeg = true;
                    }
                }
            }
            if (!hasNetworkLeg) {
                INNER_WALKS_UNROUTABLE.incrementAndGet();
                out.add(pe);
                continue;
            }
            final String routingMode = TripStructureUtils.getRoutingMode(leg);
            for (final PlanElement r : routed) {
                if (r instanceof Leg && routingMode != null) {
                    TripStructureUtils.setRoutingMode((Leg) r, routingMode);
                }
                out.add(r);
            }
            final long n = INNER_WALKS_ROUTED.incrementAndGet();
            if (n % 100000 == 0) {
                LOG.info("ptDirectWalk: {} beeline walk legs inside transit answers put on the "
                         + "walk network, {} left as beelines (no walk route at all, #167)",
                         n, INNER_WALKS_UNROUTABLE.get());
            }
        }
        return out;
    }

    private boolean boardsTransit(final List<? extends PlanElement> legs) {
        for (final PlanElement pe : legs) {
            if (pe instanceof Leg && this.transitModes.contains(((Leg) pe).getMode())) {
                return true;
            }
        }
        return false;
    }

    private static double transitCost(final List<? extends PlanElement> legs) {
        for (final PlanElement pe : legs) {
            if (pe instanceof Leg) {
                final Object cost = ((Leg) pe).getAttributes()
                        .getAttribute(RaptorUtils.TOTAL_ROUTE_COST_ATTR_NAME);
                if (cost instanceof Number) {
                    return ((Number) cost).doubleValue();
                }
            }
        }
        return Double.NaN;
    }

    private static double travelSeconds(final List<? extends PlanElement> legs) {
        double s = 0.0;
        if (legs == null) {
            return Double.POSITIVE_INFINITY;
        }
        for (final PlanElement pe : legs) {
            if (pe instanceof Leg) {
                final Leg leg = (Leg) pe;
                if (leg.getTravelTime().isDefined()) {
                    s += leg.getTravelTime().seconds();
                } else if (leg.getRoute() != null && leg.getRoute().getTravelTime().isDefined()) {
                    s += leg.getRoute().getTravelTime().seconds();
                }
            }
        }
        return s;
    }

    /** Raptor parameters that never let the raptor answer with a beeline walk. */
    @Singleton
    public static final class NoDirectWalkParameters implements RaptorParametersForPerson {
        private final RaptorParameters params;

        @Inject
        public NoDirectWalkParameters(final Config config) {
            this.params = RaptorUtils.createParameters(config);
            // large enough that no transit route ever loses to it; the real
            // comparison, with the declared factor, is made by the module
            this.params.setDirectWalkFactor(1.0e9);
        }

        @Override
        public RaptorParameters getRaptorParameters(final Person person) {
            return this.params;
        }
    }

    /** Builds the module over the stock raptor module and the walk router. */
    public static final class RouterProvider implements Provider<RoutingModule> {
        @Inject
        private SwissRailRaptorRoutingModuleProvider raptorModule;
        @Inject
        @Named(TransportMode.walk)
        private RoutingModule walkRouter;
        @Inject
        private RaptorParametersForPerson parameters;
        @Inject
        private Config config;
        @Inject
        private Network network;

        @Override
        public RoutingModule get() {
            return new NetworkDirectWalkPtRouter(this.raptorModule.get(), this.walkRouter,
                                                 this.parameters, this.config, this.network);
        }
    }
}
