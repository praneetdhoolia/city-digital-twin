package citysim;

import ch.sbb.matsim.routing.pt.raptor.OccupancyData;
import ch.sbb.matsim.routing.pt.raptor.RaptorInVehicleCostCalculator;
import ch.sbb.matsim.routing.pt.raptor.RaptorParametersForPerson;
import ch.sbb.matsim.routing.pt.raptor.RaptorRouteSelector;
import ch.sbb.matsim.routing.pt.raptor.RaptorStopFinder;
import ch.sbb.matsim.routing.pt.raptor.RaptorTransferCostCalculator;
import ch.sbb.matsim.routing.pt.raptor.RaptorUtils;
import ch.sbb.matsim.routing.pt.raptor.SwissRailRaptor;
import ch.sbb.matsim.routing.pt.raptor.SwissRailRaptorData;
import ch.sbb.matsim.routing.pt.raptor.SwissRailRaptorRoutingModule;
import com.google.inject.Inject;
import com.google.inject.Provider;
import com.google.inject.name.Named;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.router.RoutingModule;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitScheduleFactory;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;

/**
 * One SwissRailRaptor per PT submode, over that submode's own routes.
 *
 * <p>Installed only under {@code ptSubmodeChoice.representation =
 * alternatives} ({@link PtSubmodeChoiceConfigGroup}, declared as
 * {@code RUN.mode_choice.pt_submode_alternatives}). Under {@code aggregate}
 * nothing here runs and the stock single-raptor model is untouched.
 *
 * <h2>Why a filtered schedule rather than a filtered answer</h2>
 *
 * <p>The obvious cheap implementation — ask the ordinary pt router, then
 * refuse the itinerary if it did not use the submode asked for — is WRONG in a
 * way that would not show up as an error. The raptor returns the least-cost
 * itinerary over ALL routes, so a bus request whose least-cost pt answer is a
 * train comes back a train and is refused, and the agent is told no bus
 * exists on a corridor where one does. That would report a submode as
 * infeasible exactly where it competes hardest, which is the opposite of what
 * this gate is for. Filtering the SCHEDULE instead asks a well-posed question:
 * what is the best way to get there BY BUS.
 *
 * <h2>What is shared and what is copied</h2>
 *
 * <p>The stop facilities, the route objects, the network and the vehicles are
 * SHARED — the filtered schedule holds references to the same objects, not
 * copies, so the only new memory is the per-submode
 * {@link SwissRailRaptorData} index (route stops and precomputed transfers)
 * and one {@link TransitLine} shell per line that has a route of the submode.
 * A line with no route of the submode is not added at all.
 *
 * <p>Every stop facility is added to every filtered schedule. That is
 * deliberate: {@code SwissRailRaptorData} builds its access quadtree from the
 * schedule's facilities and a facility no route of this submode calls at is
 * simply never a route stop, so carrying them all costs a quadtree entry and
 * keeps stop ids resolvable when an itinerary is converted back to legs.
 */
public final class SubmodeRaptorProvider implements Provider<RoutingModule> {

    private static final Logger LOG =
            LogManager.getLogger(SubmodeRaptorProvider.class);

    private final String submode;
    private final Scenario scenario;
    private final RaptorParametersForPerson parametersForPerson;
    private final RaptorRouteSelector routeSelector;
    private final Provider<RaptorStopFinder> stopFinder;
    private final RaptorInVehicleCostCalculator inVehicleCost;
    private final RaptorTransferCostCalculator transferCost;
    private final Provider<RoutingModule> walkRouter;

    private SwissRailRaptorData data;
    private TransitSchedule filtered;

    SubmodeRaptorProvider(final String submode, final Scenario scenario,
                          final RaptorParametersForPerson parametersForPerson,
                          final RaptorRouteSelector routeSelector,
                          final Provider<RaptorStopFinder> stopFinder,
                          final RaptorInVehicleCostCalculator inVehicleCost,
                          final RaptorTransferCostCalculator transferCost,
                          final Provider<RoutingModule> walkRouter) {
        this.submode = submode;
        this.scenario = scenario;
        this.parametersForPerson = parametersForPerson;
        this.routeSelector = routeSelector;
        this.stopFinder = stopFinder;
        this.inVehicleCost = inVehicleCost;
        this.transferCost = transferCost;
        this.walkRouter = walkRouter;
    }

    /**
     * A schedule holding only the routes whose {@code transportMode} is this
     * submode's, and every stop facility.
     */
    static TransitSchedule filter(final TransitSchedule full, final String submode) {
        final TransitScheduleFactory f = full.getFactory();
        final TransitSchedule out = f.createTransitSchedule();
        for (final TransitStopFacility stop : full.getFacilities().values()) {
            out.addStopFacility(stop);
        }
        int lines = 0;
        int routes = 0;
        for (final TransitLine line : full.getTransitLines().values()) {
            TransitLine kept = null;
            for (final TransitRoute route : line.getRoutes().values()) {
                if (!submode.equals(route.getTransportMode())) {
                    continue;
                }
                if (kept == null) {
                    kept = f.createTransitLine(line.getId());
                    kept.setName(line.getName());
                }
                kept.addRoute(route);
                routes++;
            }
            if (kept != null) {
                out.addTransitLine(kept);
                lines++;
            }
        }
        LOG.info("ptSubmodeChoice: {} schedule filtered to {} line(s), {} route(s)",
                 submode, lines, routes);
        if (routes == 0) {
            // A submode offered as a plan alternative with no service is an
            // alternative every agent is refused - a mode that cannot be
            // chosen, reported at the gate as a taste. Refuse loudly.
            throw new IllegalStateException(
                    "ptSubmodeChoice.representation is alternatives and '"
                    + submode + "' is a declared transit mode, but the mapped "
                    + "schedule holds NO route with that transportMode. It "
                    + "would be an alternative nothing can answer. Check "
                    + "RUN.transit.transit_modes against the mapped schedule.");
        }
        return out;
    }

    @Override
    public RoutingModule get() {
        if (this.data == null) {
            this.filtered = filter(this.scenario.getTransitSchedule(), this.submode);
            this.data = SwissRailRaptorData.create(
                    this.filtered, this.scenario.getTransitVehicles(),
                    RaptorUtils.createStaticConfig(this.scenario.getConfig()),
                    this.scenario.getNetwork(), new OccupancyData());
        }
        final SwissRailRaptor raptor = new SwissRailRaptor(
                this.data, this.parametersForPerson, this.routeSelector,
                this.stopFinder.get(), this.inVehicleCost, this.transferCost);
        return new SwissRailRaptorRoutingModule(
                raptor, this.filtered, this.scenario.getNetwork(),
                this.walkRouter.get());
    }

    /**
     * The Guice-visible factory: one provider instance per submode, each an
     * eager singleton so the filtered index is built once per submode rather
     * than once per routing thread.
     */
    public static final class Factory {

        private final Scenario scenario;
        private final RaptorParametersForPerson parametersForPerson;
        private final RaptorRouteSelector routeSelector;
        private final Provider<RaptorStopFinder> stopFinder;
        private final RaptorInVehicleCostCalculator inVehicleCost;
        private final RaptorTransferCostCalculator transferCost;
        private final Provider<RoutingModule> walkRouter;

        @Inject
        Factory(final Scenario scenario,
                final RaptorParametersForPerson parametersForPerson,
                final RaptorRouteSelector routeSelector,
                final Provider<RaptorStopFinder> stopFinder,
                final RaptorInVehicleCostCalculator inVehicleCost,
                final RaptorTransferCostCalculator transferCost,
                @Named(TransportMode.walk) final Provider<RoutingModule> walkRouter) {
            this.scenario = scenario;
            this.parametersForPerson = parametersForPerson;
            this.routeSelector = routeSelector;
            this.stopFinder = stopFinder;
            this.inVehicleCost = inVehicleCost;
            this.transferCost = transferCost;
            this.walkRouter = walkRouter;
        }

        public SubmodeRaptorProvider forMode(final String submode) {
            return new SubmodeRaptorProvider(
                    submode, this.scenario, this.parametersForPerson,
                    this.routeSelector, this.stopFinder, this.inVehicleCost,
                    this.transferCost, this.walkRouter);
        }
    }

    /**
     * Rewrite every seeded {@code pt} leg to the declared seed submode, once,
     * before the first replanning.
     *
     * <p>With {@code pt} out of {@code subtourModeChoice.modes} a seeded
     * {@code pt} subtour is an ABSORBING STATE: nothing proposes a change to
     * it and nothing proposes a change away from it. That is the failure
     * {@code RUN.mode_choice.modes} already records for {@code ride}, where
     * omitting the mode froze it at 0.18311 in every iteration to five
     * decimals and 18.6 % of legs were an input wearing the costume of a
     * result. The rewrite is counted and logged rather than done quietly.
     */
    static void reseedPtLegs(final Scenario scenario, final String seedSubmode) {
        long legs = 0;
        long persons = 0;
        for (final Person person : scenario.getPopulation().getPersons().values()) {
            boolean touched = false;
            for (final Plan plan : person.getPlans()) {
                for (final PlanElement el : plan.getPlanElements()) {
                    if (!(el instanceof Leg)) {
                        continue;
                    }
                    final Leg leg = (Leg) el;
                    if (!TransportMode.pt.equals(leg.getMode())) {
                        continue;
                    }
                    leg.setMode(seedSubmode);
                    leg.setRoutingMode(seedSubmode);
                    leg.setRoute(null);
                    legs++;
                    touched = true;
                }
            }
            if (touched) {
                persons++;
            }
        }
        LOG.info("ptSubmodeChoice: reseeded {} seeded `pt` leg(s) on {} person(s) "
                 + "to `{}` - the umbrella mode is not in the choice set under "
                 + "`alternatives`, so a seeded pt subtour would be absorbing",
                 legs, persons, seedSubmode);
    }
}
