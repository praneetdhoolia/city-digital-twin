package citysim;

import java.util.ArrayList;
import java.util.List;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.Event;
import org.matsim.api.core.v01.events.PersonScoreEvent;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.events.EventsUtils;
import org.matsim.core.events.handler.BasicEventHandler;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.population.routes.RouteUtils;
import org.matsim.core.router.DefaultRoutingRequest;
import org.matsim.core.router.RoutingModule;
import org.matsim.core.router.RoutingRequest;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.scoring.functions.SubpopulationScoringParameters;
import org.matsim.facilities.ActivityFacilitiesFactoryImpl;
import org.matsim.facilities.Facility;

/**
 * The gate on the bounded pt no-route walk (D28, F39;
 * RUN.transit_router.no_route_walk), on stub routers - no scenario, no raptor:
 * <ul>
 * <li>{@code off_unchanged}: under {@code network_walk} a 5 km no-route walk
 *     comes back exactly as the walk router made it, unstamped and uncounted
 *     (F38);</li>
 * <li>{@code beyond_reach_stamped}: under {@code refused_beyond_reach} the
 *     same answer is STILL the executable network walk (the same legs) but
 *     every leg carries its routed metres and the router's counter moves;</li>
 * <li>{@code within_reach_untouched}: a 2 km no-route walk inside the 3,224 m
 *     reach is not stamped;</li>
 * <li>{@code scored_as_aborted}: {@link PtUnservedScoring} charges the person
 *     whose executed plan holds the stamped trip exactly MATSim's
 *     {@code abortedPlanScore} for that person, once, and nobody else;</li>
 * <li>{@code refuses_bad_config}: the group refuses the gate on a beeline
 *     basis or without a positive reach.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class PtNoRouteWalkProbe {

    private static final double REACH_M = 3223.6;

    private PtNoRouteWalkProbe() {
    }

    /** A walk router answering one straight network walk of a set length. */
    private static final class StubWalk implements RoutingModule {
        double metres;

        @Override
        public List<? extends PlanElement> calcRoute(final RoutingRequest request) {
            final Leg leg = PopulationUtils.createLeg("walk");
            final org.matsim.api.core.v01.population.Route route =
                    RouteUtils.createLinkNetworkRouteImpl(Id.createLinkId("a"), Id.createLinkId("b"));
            route.setDistance(this.metres);
            route.setTravelTime(this.metres / 1.25);
            leg.setRoute(route);
            leg.setTravelTime(this.metres / 1.25);
            final List<PlanElement> out = new ArrayList<>();
            out.add(leg);
            return out;
        }
    }

    /** A raptor that finds no transit route: a walk-only answer. */
    private static final RoutingModule NO_TRANSIT = request -> {
        final List<PlanElement> out = new ArrayList<>();
        out.add(PopulationUtils.createLeg("walk"));
        return out;
    };

    private static NetworkDirectWalkPtRouter router(final String gate, final StubWalk walk) {
        final PtDirectWalkConfigGroup g = new PtDirectWalkConfigGroup();
        final Config config = ConfigUtils.createConfig(g);
        g.basis = PtDirectWalkConfigGroup.NETWORK;
        g.noRouteWalk = gate;
        g.noRouteWalkReachM = REACH_M;
        g.checkConsistency(config);
        return new NetworkDirectWalkPtRouter(NO_TRANSIT, walk, null, config,
                ScenarioUtils.createScenario(config).getNetwork());
    }

    private static RoutingRequest request(final Person p) {
        final ActivityFacilitiesFactoryImpl f = new ActivityFacilitiesFactoryImpl();
        final Facility from = f.createActivityFacility(Id.create("o",
                org.matsim.facilities.ActivityFacility.class), new Coord(0, 0), Id.createLinkId("a"));
        final Facility to = f.createActivityFacility(Id.create("d",
                org.matsim.facilities.ActivityFacility.class), new Coord(5000, 0), Id.createLinkId("b"));
        return DefaultRoutingRequest.withoutAttributes(from, to, 8 * 3600, p);
    }

    private static boolean stamped(final List<? extends PlanElement> legs) {
        for (final PlanElement pe : legs) {
            if (pe instanceof Leg && ((Leg) pe).getAttributes()
                    .getAttribute(NetworkDirectWalkPtRouter.UNSERVED_ATTRIBUTE) != null) {
                return true;
            }
        }
        return false;
    }

    public static void main(final String[] args) {
        final Scenario scenario = ScenarioUtils.createScenario(ConfigUtils.createConfig());
        final Person far = scenario.getPopulation().getFactory().createPerson(Id.createPersonId("far"));
        final Person near = scenario.getPopulation().getFactory().createPerson(Id.createPersonId("near"));
        scenario.getPopulation().addPerson(far);
        scenario.getPopulation().addPerson(near);

        // (1) gate off: F38
        final StubWalk walk = new StubWalk();
        walk.metres = 5000.0;
        final long before = NetworkDirectWalkPtRouter.beyondReachCount();
        final List<? extends PlanElement> off = router(
                PtDirectWalkConfigGroup.NO_ROUTE_NETWORK_WALK, walk).calcRoute(request(far));
        final boolean offUnchanged = off.size() == 1 && !stamped(off)
                && NetworkDirectWalkPtRouter.beyondReachCount() == before;

        // (2) gate on, 5 km: stamped, still the walk, counted
        final List<? extends PlanElement> on = router(
                PtDirectWalkConfigGroup.NO_ROUTE_REFUSED, walk).calcRoute(request(far));
        final Object metres = on.isEmpty() ? null : ((Leg) on.get(0)).getAttributes()
                .getAttribute(NetworkDirectWalkPtRouter.UNSERVED_ATTRIBUTE);
        final boolean beyondStamped = on.size() == 1
                && "walk".equals(((Leg) on.get(0)).getMode())
                && ((Leg) on.get(0)).getRoute().getDistance() == 5000.0
                && metres instanceof Double && (Double) metres == 5000.0
                && NetworkDirectWalkPtRouter.beyondReachCount() == before + 1;

        // (3) gate on, 2 km: inside the reach, untouched
        walk.metres = 2000.0;
        final List<? extends PlanElement> inside = router(
                PtDirectWalkConfigGroup.NO_ROUTE_REFUSED, walk).calcRoute(request(near));
        final boolean withinUntouched = !stamped(inside)
                && NetworkDirectWalkPtRouter.beyondReachCount() == before + 1;

        // (4) the executed plans are scored: the stamped one as aborted
        plan(far, on);
        plan(near, inside);
        final List<PersonScoreEvent> charged = new ArrayList<>();
        final EventsManager events = EventsUtils.createEventsManager();
        events.addHandler((BasicEventHandler) (final Event e) -> {
            if (e instanceof PersonScoreEvent) {
                charged.add((PersonScoreEvent) e);
            }
        });
        events.initProcessing();
        final SubpopulationScoringParameters params = new SubpopulationScoringParameters(scenario);
        new PtUnservedScoring(scenario, events, params)
                .notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        events.finishProcessing();
        final double aborted = params.getScoringParameters(far).abortedPlanScore;
        final boolean scored = charged.size() == 1
                && charged.get(0).getPersonId().equals(far.getId())
                && charged.get(0).getAmount() == aborted && aborted < 0.0
                && PtUnservedScoring.KIND.equals(charged.get(0).getKind());

        // (5) the group refuses a gate it cannot honour
        boolean refusesBeeline = false;
        boolean refusesZeroReach = false;
        final PtDirectWalkConfigGroup bad = new PtDirectWalkConfigGroup();
        final Config badConfig = ConfigUtils.createConfig(bad);
        bad.noRouteWalk = PtDirectWalkConfigGroup.NO_ROUTE_REFUSED;
        bad.noRouteWalkReachM = REACH_M;
        try {
            bad.checkConsistency(badConfig);          // basis still beeline
        } catch (final IllegalArgumentException expected) {
            refusesBeeline = true;
        }
        bad.basis = PtDirectWalkConfigGroup.NETWORK;
        bad.noRouteWalkReachM = 0.0;
        try {
            bad.checkConsistency(badConfig);
        } catch (final IllegalArgumentException expected) {
            refusesZeroReach = true;
        }
        final boolean refuses = refusesBeeline && refusesZeroReach;

        final boolean ok = offUnchanged && beyondStamped && withinUntouched && scored && refuses;
        System.out.println("{\"probe\":\"PtNoRouteWalkProbe\",\"off_unchanged\":" + offUnchanged
                + ",\"beyond_reach_stamped\":" + beyondStamped
                + ",\"within_reach_untouched\":" + withinUntouched
                + ",\"scored_as_aborted\":" + scored
                + ",\"aborted_plan_score\":" + aborted
                + ",\"refuses_bad_config\":" + refuses
                + ",\"ok\":" + ok + "}");
        System.exit(ok ? 0 : 1);
    }

    private static Plan plan(final Person p, final List<? extends PlanElement> legs) {
        final Plan plan = PopulationUtils.createPlan(p);
        plan.addActivity(PopulationUtils.createActivityFromCoord("home", new Coord(0, 0)));
        for (final PlanElement pe : legs) {
            plan.addLeg((Leg) pe);
        }
        plan.addActivity(PopulationUtils.createActivityFromCoord("work", new Coord(5000, 0)));
        p.addPlan(plan);
        p.setSelectedPlan(plan);
        return plan;
    }
}
