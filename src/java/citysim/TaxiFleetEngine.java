package citysim;

import com.google.inject.Inject;
import com.google.inject.Singleton;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.events.BeforeMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.core.controler.listener.BeforeMobsimListener;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.utils.misc.OptionalTime;

/**
 * Taxi as a FINITE fleet: a request no vehicle can serve is refused
 * (DECISIONS.md 9.99, issue #90).
 *
 * <p>Taxi was the only mode this model constrained by nothing at all, and its
 * share behaved accordingly - seeded at exactly 0.0 because the demand
 * generates none, then climbing through mode-choice innovation to 8.8% against
 * a 0.99% target, at 7.52% even among agents holding both a car and a licence
 * (9.91, 9.94). It was not out-competing car; car is chain-based, so a
 * perturbed subtour cannot use it, and taxi was winning those trips because
 * nothing said no.
 *
 * <h2>Where the allocation happens, and why there</h2>
 *
 * <p>At {@link BeforeMobsimListener}, on the selected plans, exactly where
 * {@link RidePairingEngine} pairs ride legs (9.44). That is the one point in
 * the iteration where every plan is stable and nothing will re-route
 * underneath the decision, and it means the fleet needs no mobsim engine, no
 * dispatcher and no new dependency - which matters, because the MATSim DRT
 * contrib is not in this project's pinned run stack and cannot be resolved
 * from inside its network sandbox (#90).
 *
 * <h2>The allocation</h2>
 *
 * <p>Every taxi leg in the population is collected with its departure time,
 * sorted, and served greedily by the earliest-free vehicle:
 *
 * <ul>
 *   <li>a vehicle free at or before the request departs serves it, and becomes
 *       busy for the leg's own travel time plus the declared deadhead;</li>
 *   <li>a request whose earliest-free vehicle is more than
 *       {@code maxWaitMinutes} away is REFUSED;</li>
 *   <li>a refused request WALKS this iteration, and the mode is given back at
 *       {@code AfterMobsim}.</li>
 * </ul>
 *
 * <p>Serving in departure order with the earliest-free vehicle is the
 * allocation that maximises the number served for a given fleet, so this is
 * the fleet's BEST case: a real dispatcher does worse, and any refusal here is
 * one a real fleet would also have made.
 *
 * <h2>Why the refusal is a walk rather than a parameter</h2>
 *
 * <p>The same reasoning as 9.55 for ride, and the same correction as 9.81. A
 * long forced walk scores badly, so co-evolution reassigns the tour and taxi
 * becomes EMERGENT - only what the fleet carries survives. Nothing caps the
 * mode share; the supply constraint is the price. And the walk is an
 * EXECUTION, not an amputation: the plan keeps taxi, because a refusal that
 * deleted the alternative would be the one-way ratchet 9.81 measured, where
 * failure was permanent and success created nothing.
 *
 * <h2>What this deliberately does NOT do</h2>
 *
 * <p><b>Empty running does not load the road.</b> The deadhead is time a
 * vehicle is unavailable, not a routed leg, so a taxi's dead legs consume no
 * link capacity. That is a stated simplification rather than a hidden one, and
 * it is the one thing a real DRT implementation would add.
 *
 * <p><b>No spatial dispatch.</b> A vehicle is free or it is not; which vehicle
 * is nearest is not modelled, because vehicle positions would need the routed
 * empty legs above. The declared deadhead stands in for the average cost of
 * reaching the next fare, and it is swept.
 *
 * <h2>Determinism</h2>
 *
 * <p>Requests are ordered by (departure, person id, leg index) and vehicles by
 * free-time then index, so two runs of one build allocate identically. No wall
 * clock and no {@code Random}.
 */
@Singleton
public final class TaxiFleetEngine implements BeforeMobsimListener,
        AfterMobsimListener {

    private static final Logger LOG =
            LogManager.getLogger(TaxiFleetEngine.class);

    private static final String TAXI = "taxi";
    private static final int SECONDS_PER_MINUTE = 60;

    private final TaxiFleetConfigGroup cfg;
    private final Scenario scenario;
    private final double sampleFraction;

    /**
     * Trips walked this mobsim, to be given taxi back afterwards - recorded
     * by person and endpoints, NEVER as leg objects (#113): the re-mode nulls
     * the route, PersonPrepareForSim then re-routes the trip and replaces its
     * leg objects, and a restore through the old reference wrote to an orphan.
     * Every refused taxi trip stayed walk in plan memory for good - the 9.81
     * ratchet this class says it avoids - while the log reported the list
     * size as "restored". The ride engine had measured and fixed the same
     * defect (RidePairingEngine.notifyAfterMobsim); both now restore through
     * {@link RemodeRestore}.
     */
    private final List<Refused> refusedThisMobsim = new ArrayList<>();

    @Inject
    TaxiFleetEngine(final Scenario scenario) {
        this.scenario = scenario;
        this.cfg = ConfigUtils.addOrGetModule(scenario.getConfig(),
                TaxiFleetConfigGroup.NAME, TaxiFleetConfigGroup.class);
        this.sampleFraction = scenario.getConfig().qsim().getFlowCapFactor();
        if (this.sampleFraction <= 0) {
            throw new IllegalStateException(
                    "qsim.flowCapacityFactor is " + this.sampleFraction
                    + "; the fleet is declared at full scale and scaled by it, "
                    + "so a non-positive factor cannot size a fleet");
        }
    }

    /** One taxi request: a trip, when it wants to leave, how long it takes. */
    private static final class Request {
        final Id<Person> personId;
        final List<Leg> legs;
        final Id<Link> from;
        final Id<Link> to;
        final double departure;
        final double duration;
        final String person;
        final int index;

        Request(final Id<Person> personId, final List<Leg> legs,
                final Id<Link> from, final Id<Link> to,
                final double departure, final double duration,
                final int index) {
            this.personId = personId;
            this.legs = legs;
            this.from = from;
            this.to = to;
            this.departure = departure;
            this.duration = duration;
            this.person = personId.toString();
            this.index = index;
        }
    }

    /** A refused trip, by the handles that survive the router. */
    private static final class Refused {
        final Id<Person> person;
        final Id<Link> from;
        final Id<Link> to;

        Refused(final Id<Person> person, final Id<Link> from,
                final Id<Link> to) {
            this.person = person;
            this.from = from;
            this.to = to;
        }
    }

    @Override
    public void notifyBeforeMobsim(final BeforeMobsimEvent event) {
        this.refusedThisMobsim.clear();
        if (!this.cfg.isFleet()) {
            return;                      // `absent`: every request is served
        }
        final List<Request> requests = collect();
        if (requests.isEmpty()) {
            LOG.info("taxiFleet: no taxi legs in the selected plans");
            return;
        }
        requests.sort(Comparator
                .comparingDouble((Request r) -> r.departure)
                .thenComparing(r -> r.person)
                .thenComparingInt(r -> r.index));

        final int fleet = Math.max(1, (int) Math.round(
                this.cfg.getFleetSize() * this.sampleFraction));
        final double maxWait =
                this.cfg.getMaxWaitMinutes() * SECONDS_PER_MINUTE;
        final double deadhead =
                this.cfg.getDeadheadMinutes() * SECONDS_PER_MINUTE;

        // every vehicle free from the start of the day; the queue orders them
        // by the time they next become free
        final PriorityQueue<double[]> free = new PriorityQueue<>(
                Comparator.<double[]>comparingDouble(v -> v[0])
                        .thenComparingDouble(v -> v[1]));
        for (int i = 0; i < fleet; i++) {
            free.add(new double[] {Double.NEGATIVE_INFINITY, i});
        }

        int served = 0;
        int refused = 0;
        double waitSum = 0;
        for (final Request r : requests) {
            final double[] first = free.peek();
            final double wait = Math.max(0.0, first[0] - r.departure);
            if (wait > maxWait) {
                refuse(r);
                refused++;
                continue;
            }
            free.poll();
            final double start = Math.max(first[0], r.departure);
            first[0] = start + r.duration + deadhead;
            free.add(first);
            served++;
            waitSum += wait;
        }
        LOG.info("taxiFleet: fleet={} (declared {} x sample {}) requests={} "
                 + "served={} refused={} ({}%) meanWait={}s",
                 fleet, this.cfg.getFleetSize(), this.sampleFraction,
                 requests.size(), served, refused,
                 String.format("%.1f", 100.0 * refused / requests.size()),
                 String.format("%.0f", served == 0 ? 0.0 : waitSum / served));
    }

    /**
     * Every taxi trip in a selected plan - every leg of it taxi - with its
     * endpoints, its own departure and its duration.
     */
    private List<Request> collect() {
        final List<Request> out = new ArrayList<>();
        for (final Person person : this.scenario.getPopulation()
                .getPersons().values()) {
            final Plan plan = person.getSelectedPlan();
            if (plan == null) {
                continue;
            }
            int index = 0;
            double clock = Double.NaN;
            for (final TripStructureUtils.Trip trip
                    : TripStructureUtils.getTrips(plan)) {
                index++;
                final Activity origin = trip.getOriginActivity();
                if (origin.getEndTime().isDefined()) {
                    clock = origin.getEndTime().seconds();
                }
                // ONE getLegsOnly() for the whole trip: it allocates a filtered
                // list per call and this loop used to make three of them for
                // every trip of every person, every iteration.
                final List<Leg> legs = trip.getLegsOnly();
                if (!RemodeRestore.isAllMode(legs, TAXI)) {
                    continue;
                }
                final OptionalTime dep = legs.get(0).getDepartureTime();
                final double departure = dep.isDefined() ? dep.seconds() : clock;
                if (Double.isNaN(departure)) {
                    continue;            // no clock to allocate against
                }
                double duration = 0.0;
                for (final Leg leg : legs) {
                    if (leg.getRoute() != null
                            && leg.getRoute().getTravelTime().isDefined()) {
                        duration += leg.getRoute().getTravelTime().seconds();
                    } else if (leg.getTravelTime().isDefined()) {
                        duration += leg.getTravelTime().seconds();
                    }
                }
                out.add(new Request(person.getId(), legs, origin.getLinkId(),
                                    trip.getDestinationActivity().getLinkId(),
                                    departure, Math.max(0.0, duration), index));
            }
        }
        return out;
    }

    /** A refused request walks this iteration; the plan keeps taxi (9.81). */
    private void refuse(final Request r) {
        if (!this.cfg.isRemodeRefused()) {
            return;
        }
        this.refusedThisMobsim.add(new Refused(r.personId, r.from, r.to));
        for (final Leg leg : r.legs) {
            leg.setMode(TransportMode.walk);
            TripStructureUtils.setRoutingMode(leg, TransportMode.walk);
            // the taxi route may traverse links walk is not permitted on, and
            // the router will rebuild it - the same handling RidePairingEngine
            // gives a remoded ride leg
            leg.setRoute(null);
        }
    }

    /**
     * Give every refused trip taxi back, RE-FOUND in the selected plan by its
     * endpoints (#113): the walk was scored, the alternative is kept. The
     * count logged is what was actually found and replaced.
     */
    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        if (this.refusedThisMobsim.isEmpty()) {
            return;
        }
        int restored = 0;
        final Map<Id<Person>, Set<Activity>> consumed = new HashMap<>();
        for (final Refused r : this.refusedThisMobsim) {
            final Person person =
                    this.scenario.getPopulation().getPersons().get(r.person);
            if (person == null || person.getSelectedPlan() == null) {
                continue;
            }
            if (RemodeRestore.restore(person.getSelectedPlan(), r.from, r.to,
                                      TransportMode.walk, TAXI, null,
                                      consumed.computeIfAbsent(r.person,
                                              k -> RemodeRestore.ledger()))) {
                restored++;
            }
        }
        LOG.info("taxiFleet: {} of {} refused trip(s) walked this iteration "
                 + "and had taxi restored as an alternative",
                 restored, this.refusedThisMobsim.size());
        this.refusedThisMobsim.clear();
    }
}
