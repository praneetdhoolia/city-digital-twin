package citysim;

import com.google.inject.Inject;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.PersonScoreEvent;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.core.scoring.functions.ScoringParametersForPerson;

/**
 * A plan whose pt trip no transit can serve and no one would walk scores as a
 * plan MATSim could not execute (D28, F39; the fifteenth report's finding on
 * {@code NetworkDirectWalkPtRouter.java:132}).
 *
 * <h2>Why a score and not a missing route</h2>
 *
 * <p>When the raptor finds no transit route the pt router answers with the
 * network walk; on F38 that made walk trips average 3.61 km against 0.70
 * observed, with 39.5 % of pt requests unconnected rural trip ends. MATSim has
 * no "refused" route: a routing module that returns {@code null} is replaced
 * by {@code TripRouter}'s {@code FallbackRoutingModuleDefaultImpl}, which
 * TELEPORTS a beeline walk (read from the pinned jar) - a longer free walk,
 * and a teleported one. So the router keeps returning the executable network
 * walk and stamps its legs with {@link NetworkDirectWalkPtRouter#UNSERVED_ATTRIBUTE}
 * when it is longer than the declared reach; this listener then charges the
 * person whose EXECUTED plan holds such a trip, once, MATSim's own score for
 * a plan it could not execute: {@code ScoringParameters.abortedPlanScore},
 * which {@code CharyparNagelAgentStuckScoring} adds to a stuck agent - 24 h
 * at the person's worst marginal utility. No value is typed here; it is the
 * run's own scoring parameters for that person.
 *
 * <p>The plan is then never preferred to a feasible one by ChangeExpBeta and
 * is the first the plan memory drops: pt is out of that tour's choice set,
 * which is what an unservable request is. Emitted at AfterMobsim, before the
 * scoring listener closes the iteration - the {@link ServiceQualityScoring}
 * discipline. Installed only under {@code ptDirectWalk.noRouteWalk =
 * refused_beyond_reach} (RUN.transit_router.no_route_walk); under
 * {@code network_walk} nothing here exists and F38 is recovered exactly.
 */
public final class PtUnservedScoring implements AfterMobsimListener {

    private static final Logger LOG = LogManager.getLogger(PtUnservedScoring.class);

    /** Kind string carried on every emitted PersonScoreEvent. */
    public static final String KIND = "ptUnservedWalk";

    private final Scenario scenario;
    private final EventsManager events;
    private final ScoringParametersForPerson parameters;

    @Inject
    public PtUnservedScoring(final Scenario scenario, final EventsManager events,
                             final ScoringParametersForPerson parameters) {
        this.scenario = scenario;
        this.events = events;
        this.parameters = parameters;
    }

    /** True when the plan holds at least one refused no-route pt answer. */
    static boolean holdsUnserved(final Plan plan) {
        if (plan == null) {
            return false;
        }
        for (final PlanElement pe : plan.getPlanElements()) {
            if (pe instanceof Leg && ((Leg) pe).getAttributes()
                    .getAttribute(NetworkDirectWalkPtRouter.UNSERVED_ATTRIBUTE) != null) {
                return true;
            }
        }
        return false;
    }

    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        final double time = this.scenario.getConfig().qsim().getEndTime().orElse(0.0);
        long charged = 0;
        double total = 0.0;
        for (final Person person : this.scenario.getPopulation().getPersons().values()) {
            if (!holdsUnserved(person.getSelectedPlan())) {
                continue;
            }
            final double penalty =
                    this.parameters.getScoringParameters(person).abortedPlanScore;
            this.events.processEvent(new PersonScoreEvent(
                    time, person.getId(), penalty, KIND));
            charged++;
            total += penalty;
        }
        LOG.info("ptUnserved: iteration {} - {} executed plan(s) held a pt trip with no "
                 + "transit route and a network walk beyond the declared reach; each "
                 + "charged its aborted-plan score (total {}; RUN.transit_router.no_route_walk)",
                 event.getIteration(), charged, Math.round(total));
    }
}
