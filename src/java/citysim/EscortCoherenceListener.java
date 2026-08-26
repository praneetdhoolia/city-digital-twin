package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.core.controler.events.ReplanningEvent;
import org.matsim.core.controler.listener.ReplanningListener;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Trip;

/**
 * Keeps an escort and the person being escorted on the SAME journey.
 *
 * <h2>The defect this exists for</h2>
 *
 * <p>B2 generates escort travel as a PAIR: a driver's escort tour and the bound
 * member's trip are one physical journey, recorded in
 * {@code B2_escort_bindings_<DAY>.csv} from census household structure and the
 * HTS escort rates. MATSim then replans the two agents INDEPENDENTLY, and
 * {@code SubtourModeChoice} moves one agent at a time, so the two-sided state
 * cannot be proposed by any per-agent strategy. Once the pair decoheres it
 * cannot recohere: re-establishing it needs both sides to move together, which
 * has vanishing probability.
 *
 * <p>Measured on arm 20260826T060938 at iteration 150: <b>84.53% of trips
 * arriving at an {@code escort} activity are car</b> — the drivers are still
 * driving — while only <b>11.45%</b> of the escort-bound members are riding.
 * Tens of thousands of escort car trips run each iteration carrying nobody,
 * which suppresses `ride` and inflates `car` at the same time.
 *
 * <h2>What this does, and what it deliberately does not</h2>
 *
 * <p>Two people travelling together travel by the same means. That is a
 * physical identity, not a calibration, and it is the only thing asserted here.
 * After replanning, for each household, this finds car legs arriving at an
 * {@code escort} activity and the household members whose own trip has the same
 * endpoints inside the declared pairing window. Where such a member is NOT on
 * `ride`, it PROPOSES a copy of their plan in which that trip is `ride`.
 *
 * <p>It <b>proposes, never imposes</b>. The proposed plan is scored like any
 * other and {@code ChangeExpBeta} keeps it only if it earns its place — a
 * member whose ride keeps failing to pair walks a long way, scores badly and
 * abandons it, exactly as today. What changes is that the coherent state is
 * REACHABLE, which is what MATSim's innovation strategies exist to ensure and
 * what no per-agent strategy can do here.
 *
 * <p>It does not touch the driver: the escorting person's mode is their own
 * choice, and if they cycle, no ride is proposed to anyone. It invents no
 * value; the one declared parameter is how often a decohered pair is
 * re-proposed ({@code B.ride.escort_coherence_rate}), whose zero recovers
 * today's behaviour exactly so its effect is measurable rather than assumed.
 */
public final class EscortCoherenceListener implements ReplanningListener {

    private static final Logger LOG =
            LogManager.getLogger(EscortCoherenceListener.class);

    /** The activity an escort trip exists to reach. */
    public static final String ESCORT_ACTIVITY = "escort";
    /** Written by build_matsim_plans.py: `always` or `never`. */
    public static final String CAR_AVAIL = "carAvail";
    public static final String CAR_ALWAYS = "always";

    private final Scenario scenario;
    private final RidePairingConfigGroup cfg;

    /** Household id per person, resolved once: membership never changes. */
    private final Map<Id<Person>, String> household = new HashMap<>();
    private final Map<String, List<Person>> byHousehold = new HashMap<>();
    private boolean indexed = false;

    @Inject
    EscortCoherenceListener(final Scenario scenario) {
        this.scenario = scenario;
        this.cfg = (RidePairingConfigGroup) scenario.getConfig().getModules()
                .get(RidePairingConfigGroup.NAME);
    }

    @Override
    public void notifyReplanning(final ReplanningEvent event) {
        if (cfg == null || !cfg.isEnabled() || cfg.getEscortCoherenceRate() <= 0.0) {
            return;
        }
        index();
        // Seeded on the iteration so a run is reproducible; never wall-clock.
        final Random rng = new Random(scenario.getConfig().global().getRandomSeed()
                                      + 7919L * event.getIteration());
        final double window = cfg.getWindowMinutes() * 60.0;
        final double rate = cfg.getEscortCoherenceRate();
        int proposed = 0;
        int decohered = 0;

        for (final Map.Entry<String, List<Person>> e : byHousehold.entrySet()) {
            final List<Person> members = e.getValue();
            if (members.size() < 2) {
                continue;
            }
            final List<double[]> escortRuns = new ArrayList<>();
            final List<Id<Link>[]> escortEnds = new ArrayList<>();
            final List<Id<Person>> escortDrivers = new ArrayList<>();
            for (final Person driver : members) {
                final Plan plan = driver.getSelectedPlan();
                if (plan == null) {
                    continue;
                }
                for (final Trip trip : TripStructureUtils.getTrips(plan)) {
                    if (!ESCORT_ACTIVITY.equals(
                            trip.getDestinationActivity().getType())) {
                        continue;
                    }
                    if (!isAllMode(trip, TransportMode.car)) {
                        continue;      // the escort chose something else: fine
                    }
                    @SuppressWarnings("unchecked")
                    final Id<Link>[] ends = new Id[] {
                        trip.getOriginActivity().getLinkId(),
                        trip.getDestinationActivity().getLinkId()};
                    escortEnds.add(ends);
                    escortDrivers.add(driver.getId());
                    escortRuns.add(new double[] {
                        departure(trip, plan)});
                }
            }
            if (escortEnds.isEmpty()) {
                continue;
            }
            for (final Person member : members) {
                final Plan plan = member.getSelectedPlan();
                if (plan == null) {
                    continue;
                }
                // Only someone who cannot drive themselves. Offering `ride` to
                // a licensed car-available adult would second-guess a choice
                // they are entitled to make, and it is not the population the
                // defect is about: at licence = 0 the model puts 48.8% of
                // trips on a bicycle and 0.5% on ride (DEMOGRAPHIC_MODES.md).
                final Object avail = member.getAttributes().getAttribute(CAR_AVAIL);
                if (avail != null && CAR_ALWAYS.equals(avail.toString())) {
                    continue;
                }
                Trip target = null;
                for (final Trip trip : TripStructureUtils.getTrips(plan)) {
                    if (isAllMode(trip, TransportMode.ride)) {
                        continue;                  // already coherent
                    }
                    final Id<Link> from = trip.getOriginActivity().getLinkId();
                    final Id<Link> to = trip.getDestinationActivity().getLinkId();
                    final double dep = departure(trip, plan);
                    for (int i = 0; i < escortEnds.size(); i++) {
                        if (escortDrivers.get(i).equals(member.getId())) {
                            continue;              // you cannot escort yourself
                        }
                        if (from.equals(escortEnds.get(i)[0])
                                && to.equals(escortEnds.get(i)[1])
                                && Math.abs(dep - escortRuns.get(i)[0]) <= window) {
                            target = trip;
                            break;
                        }
                    }
                    if (target != null) {
                        break;
                    }
                }
                if (target == null) {
                    continue;
                }
                decohered++;
                if (rng.nextDouble() >= rate) {
                    continue;                      // re-proposed only sometimes
                }
                final Plan copy = PopulationUtils.createPlan(member);
                PopulationUtils.copyFromTo(plan, copy);
                // Re-find the trip in the COPY: the objects differ.
                Trip inCopy = null;
                for (final Trip trip : TripStructureUtils.getTrips(copy)) {
                    if (trip.getOriginActivity().getLinkId()
                            .equals(target.getOriginActivity().getLinkId())
                            && trip.getDestinationActivity().getLinkId()
                            .equals(target.getDestinationActivity().getLinkId())) {
                        inCopy = trip;
                        break;
                    }
                }
                if (inCopy == null) {
                    continue;
                }
                // THE WHOLE SUBTOUR, never one trip of it. MATSim refuses a
                // subtour mixing chain-based modes (car, bike) with
                // non-chain-based ones, because the vehicle would be stranded:
                // re-moding a single trip to ride left [car, ride] and killed
                // arm 20260826T222352 at iteration 2 with
                // "Subtour contains a mix of chain- and non-chainbased modes"
                // (persons 93508, 451935). That is this project's own trap 13,
                // the 9.63/#65 failure, met again. An escorted member is
                // dropped AND collected, which is what the drop/pickup pairs
                // in B2_escort_bindings say, so the coherent proposal is the
                // whole subtour rather than half of it.
                final List<Trip> subtourTrips = subtourContaining(copy, inCopy);
                if (subtourTrips.isEmpty()) {
                    continue;
                }
                boolean built = true;
                for (final Trip t : subtourTrips) {
                    final Leg leg = PopulationUtils.createLeg(TransportMode.ride);
                    TripStructureUtils.setRoutingMode(leg, TransportMode.ride);
                    try {
                        TripRouter.insertTrip(copy, t.getOriginActivity(),
                                              Collections.singletonList(leg),
                                              t.getDestinationActivity());
                    } catch (final RuntimeException ex) {
                        built = false;
                        break;
                    }
                }
                if (!built) {
                    continue;
                }
                member.addPlan(copy);
                member.setSelectedPlan(copy);
                trim(member);
                proposed++;
            }
        }
        if (decohered > 0) {
            LOG.info("escortCoherence: {} decohered escort pair(s) seen, {} "
                     + "re-proposed as ride at rate {} - proposed, never imposed",
                     decohered, proposed, rate);
        }
    }

    /** The trips of the subtour that contains `trip`, or empty if unresolved. */
    private static List<Trip> subtourContaining(final Plan plan, final Trip trip) {
        for (final TripStructureUtils.Subtour st
                : TripStructureUtils.getSubtours(plan)) {
            for (final Trip t : st.getTrips()) {
                if (t.getOriginActivity() == trip.getOriginActivity()
                        && t.getDestinationActivity() == trip.getDestinationActivity()) {
                    return new ArrayList<>(st.getTrips());
                }
            }
        }
        return Collections.emptyList();
    }

    /** Every leg of the trip carries `mode`. */
    private static boolean isAllMode(final Trip trip, final String mode) {
        if (trip.getLegsOnly().isEmpty()) {
            return false;
        }
        for (final Leg leg : trip.getLegsOnly()) {
            if (!mode.equals(leg.getMode())) {
                return false;
            }
        }
        return true;
    }

    /** The trip's departure, from its first leg or its origin activity. */
    private static double departure(final Trip trip, final Plan plan) {
        for (final Leg leg : trip.getLegsOnly()) {
            if (leg.getDepartureTime().isDefined()) {
                return leg.getDepartureTime().seconds();
            }
        }
        if (trip.getOriginActivity().getEndTime().isDefined()) {
            return trip.getOriginActivity().getEndTime().seconds();
        }
        return 0.0;
    }

    /** Keep the agent inside the declared plan memory, dropping the worst. */
    private void trim(final Person person) {
        final int cap = scenario.getConfig().replanning().getMaxAgentPlanMemorySize();
        if (cap <= 0) {
            return;
        }
        while (person.getPlans().size() > cap) {
            Plan worst = null;
            for (final Plan p : person.getPlans()) {
                if (p == person.getSelectedPlan() || p.getScore() == null) {
                    continue;
                }
                if (worst == null || p.getScore() < worst.getScore()) {
                    worst = p;
                }
            }
            if (worst == null) {
                return;                            // nothing safe to drop
            }
            person.removePlan(worst);
        }
    }

    private void index() {
        if (indexed) {
            return;
        }
        for (final Person person : scenario.getPopulation().getPersons().values()) {
            final Object hh = person.getAttributes()
                    .getAttribute(RidePairingEngine.HOUSEHOLD_ATTRIBUTE);
            if (hh == null) {
                continue;
            }
            final String id = hh.toString();
            household.put(person.getId(), id);
            byHousehold.computeIfAbsent(id, k -> new ArrayList<>()).add(person);
        }
        for (final List<Person> members : byHousehold.values()) {
            Collections.sort(members, (a, b) -> a.getId().compareTo(b.getId()));
        }
        indexed = true;
    }
}
