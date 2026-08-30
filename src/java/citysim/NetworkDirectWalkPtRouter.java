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
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.config.Config;
import org.matsim.core.router.RoutingModule;
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
    private int decided = 0;
    private int walked = 0;
    private int noTransit = 0;

    NetworkDirectWalkPtRouter(final RoutingModule transit, final RoutingModule walk,
                              final RaptorParametersForPerson parameters,
                              final Config config) {
        this.transit = transit;
        this.walk = walk;
        this.parameters = parameters;
        this.directWalkFactor = config.transitRouter().getDirectWalkFactor();
        this.transitModes = new HashSet<>(config.transit().getTransitModes());
    }

    @Override
    public List<? extends PlanElement> calcRoute(final RoutingRequest request) {
        final List<? extends PlanElement> transitLegs = this.transit.calcRoute(request);
        final List<? extends PlanElement> walkLegs = this.walk.calcRoute(request);
        if (transitLegs == null || !boardsTransit(transitLegs)) {
            // the raptor found no transit route: the walk is the walk the
            // network offers, not a line across the map
            this.noTransit++;
            return walkLegs;
        }
        final double transitCost = transitCost(transitLegs);
        if (Double.isNaN(transitCost)) {
            return transitLegs;              // cost unreadable: keep the raptor's answer
        }
        final Person person = request.getPerson();
        final RaptorParameters p = this.parameters.getRaptorParameters(person);
        final double walkUtlPerS = p.getMarginalUtilityOfTravelTime_utl_s(TransportMode.walk);
        final double walkSeconds = travelSeconds(walkLegs);
        // the raptor's own pricing of a direct walk, applied to the network walk
        final double walkCost = -walkUtlPerS * walkSeconds * this.directWalkFactor;
        this.decided++;
        if (walkCost < transitCost) {
            this.walked++;
            if (this.walked <= 3) {
                LOG.info("ptDirectWalk: network walk {} s (cost {}) beats transit (cost {}) for person {}",
                         Math.round(walkSeconds), Math.round(walkCost), Math.round(transitCost),
                         person == null ? "?" : person.getId());
            }
            return walkLegs;
        }
        if (this.decided % 100000 == 0) {
            LOG.info("ptDirectWalk: {} decisions, {} network walks chosen, {} without any transit route",
                     this.decided, this.walked, this.noTransit);
        }
        return transitLegs;
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

        @Override
        public RoutingModule get() {
            return new NetworkDirectWalkPtRouter(this.raptorModule.get(), this.walkRouter,
                                                 this.parameters, this.config);
        }
    }
}
