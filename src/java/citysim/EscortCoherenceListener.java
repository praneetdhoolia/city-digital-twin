package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
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
 * <p><b>Both sides of the pair are proposable since 9.84</b> — the original
 * driver-is-never-touched stance is SUPERSEDED ON MEASUREMENT: the F9 gate at
 * iteration 100 found 52% of pairing misses were the household holding no
 * matching car leg at all, the driver having drifted off car with the
 * passenger's loss invisible to their own score, and a pair whose driver half
 * cannot be re-proposed decays however often the passenger half is offered.
 * The driver-side pass proposes the drifted member's home-anchored subtour
 * back to car; ChangeExpBeta decides on the driver's own plan, exactly as on
 * the passenger side. It invents no value; the declared rates
 * ({@code B.ride.escort_coherence_rate}, {@code B.ride.joint_coherence_rate})
 * govern both sides, and zero recovers the unassisted behaviour exactly so
 * the effect stays measurable rather than assumed.
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
        if (cfg == null || !cfg.isEnabled()
                || (cfg.getEscortCoherenceRate() <= 0.0
                    && cfg.getJointCoherenceRate() <= 0.0)) {
            return;
        }
        index();
        // Seeded on the iteration so a run is reproducible; never wall-clock.
        final Random rng = new Random(scenario.getConfig().global().getRandomSeed()
                                      + 7919L * event.getIteration());
        final double window = cfg.getWindowMinutes() * 60.0;
        final double rate = cfg.getEscortCoherenceRate();
        // DECISIONS.md 9.84: the joint extension. The 9.84 binder generates
        // adult joint travel as a PAIR, which decoheres exactly as the
        // escort pairs did (the 9.82 defect class) - so the same
        // propose-never-impose offer covers any household car leg whose
        // endpoints a co-member's trip shares, whatever activity it arrives
        // at. Zero recovers the escort-only behaviour exactly.
        final double jointRate = cfg.getJointCoherenceRate();
        // 9.146: B.ride.coherence_scope. Under `declared` this listener keeps
        // the pairs the DEMAND declared coherent and proposes nothing else -
        // a trip in `boundRideTrips`, with the driver in `boundDriver` - the
        // identity GatedSubtourModeChoice gates on since 9.120. Under
        // `inferred` it matches any household member's trip to any household
        // car leg on endpoints and clock, as every arm before 9.146 did.
        // Measured at the F26 gate: 12,461 of 66,909 selected ride legs sat
        // on persons the demand never bound, proposed here by inference,
        // while the gate refused 192,000 proposals of exactly that kind; the
        // two mechanisms contradicted, and the inferred legs were the ones
        // that never paired.
        final boolean declaredOnly = RidePairingConfigGroup.COHERENCE_DECLARED
                .equals(cfg.getCoherenceScope());
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
            final List<Boolean> escortFlags = new ArrayList<>();
            for (final Person driver : members) {
                final Plan plan = driver.getSelectedPlan();
                if (plan == null) {
                    continue;
                }
                for (final Trip trip : TripStructureUtils.getTrips(plan)) {
                    final boolean escort = ESCORT_ACTIVITY.equals(
                            trip.getDestinationActivity().getType());
                    if (!escort && jointRate <= 0.0) {
                        continue;
                    }
                    if (!isAllMode(trip, TransportMode.car)) {
                        continue;      // the driver chose something else: fine
                    }
                    @SuppressWarnings("unchecked")
                    final Id<Link>[] ends = new Id[] {
                        trip.getOriginActivity().getLinkId(),
                        trip.getDestinationActivity().getLinkId()};
                    escortEnds.add(ends);
                    escortDrivers.add(driver.getId());
                    escortFlags.add(escort);
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
                // On the ESCORT path, only someone who cannot drive
                // themselves: offering `ride` to a licensed car-available
                // adult would second-guess a choice they are entitled to
                // make, and it is not the population that defect is about
                // (at licence = 0 the model puts 48.8% of trips on a bicycle
                // and 0.5% on ride, DEMOGRAPHIC_MODES.md). On the JOINT path
                // (9.84) car-available adults ARE the generated population -
                // an adult companion in the household car - so the offer
                // extends to them there, and ChangeExpBeta still decides.
                final Object avail = member.getAttributes().getAttribute(CAR_AVAIL);
                final boolean carAvailable =
                        avail != null && CAR_ALWAYS.equals(avail.toString());
                Trip target = null;
                boolean targetEscort = false;
                final Set<Integer> boundRide = declaredOnly
                        ? GatedSubtourModeChoice.GatedModule.boundTrips(
                                plan, GatedSubtourModeChoice.GatedModule
                                        .BOUND_RIDE_ATTRIBUTE)
                        : null;
                final Set<String> namedDrivers =
                        declaredOnly ? boundDrivers(member) : null;
                int tripNo = 0;                    // 1-based, plan order (9.120)
                for (final Trip trip : TripStructureUtils.getTrips(plan)) {
                    tripNo++;
                    if (isAllMode(trip, TransportMode.ride)) {
                        continue;                  // already coherent
                    }
                    if (declaredOnly && !boundRide.contains(tripNo)) {
                        continue;                  // 9.146: not a declared trip
                    }
                    final Id<Link> from = trip.getOriginActivity().getLinkId();
                    final Id<Link> to = trip.getDestinationActivity().getLinkId();
                    final double dep = departure(trip, plan);
                    for (int i = 0; i < escortEnds.size(); i++) {
                        if (escortDrivers.get(i).equals(member.getId())) {
                            continue;              // you cannot escort yourself
                        }
                        if (escortFlags.get(i) && carAvailable) {
                            continue;              // escort path: unlicensed only
                        }
                        if (declaredOnly && !namedDrivers.contains(
                                escortDrivers.get(i).toString())) {
                            continue;              // 9.146: not the named driver
                        }
                        if (from.equals(escortEnds.get(i)[0])
                                && to.equals(escortEnds.get(i)[1])
                                && Math.abs(dep - escortRuns.get(i)[0]) <= window) {
                            target = trip;
                            targetEscort = escortFlags.get(i);
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
                if (rng.nextDouble() >= (targetEscort ? rate : jointRate)) {
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

        // ------------------------------------------------------------------
        // THE DRIVER SIDE (DECISIONS.md 9.84, superseding 9.82's driver-is-
        // never-touched clause ON MEASUREMENT). The F9 gate at iteration 100
        // located the ride decay: 52% of pairing misses were miss_endpoints -
        // the household holds NO car leg matching the planned ride any more,
        // because SubtourModeChoice moved the DRIVER's tour off car and the
        // driver's own score never sees the passenger's loss. A pair is ONE
        // choice made by two agents; while only the passenger side could be
        // re-proposed, the coherent state was unreachable whenever the driver
        // left. This pass proposes the DRIVER's half back - the subtour
        // holding their matching trip, converted to car - at the same
        // declared rates, still scored by ChangeExpBeta on the driver's own
        // plan. Zero still recovers the one-sided behaviour exactly.
        int driverDecohered = 0;
        int driverProposed = 0;
        for (final Map.Entry<String, List<Person>> e : byHousehold.entrySet()) {
            final List<Person> members = e.getValue();
            if (members.size() < 2) {
                continue;
            }
            for (final Person passenger : members) {
                final Plan pplan = passenger.getSelectedPlan();
                if (pplan == null) {
                    continue;
                }
                final Set<Integer> pBound = declaredOnly
                        ? GatedSubtourModeChoice.GatedModule.boundTrips(
                                pplan, GatedSubtourModeChoice.GatedModule
                                        .BOUND_RIDE_ATTRIBUTE)
                        : null;
                final Set<String> pDrivers =
                        declaredOnly ? boundDrivers(passenger) : null;
                int pTripNo = 0;
                for (final Trip ptrip : TripStructureUtils.getTrips(pplan)) {
                    pTripNo++;
                    if (!isAllMode(ptrip, TransportMode.ride)) {
                        continue;
                    }
                    if (declaredOnly && !pBound.contains(pTripNo)) {
                        continue;                  // 9.146: not a declared trip
                    }
                    final Id<Link> from = ptrip.getOriginActivity().getLinkId();
                    final Id<Link> to =
                            ptrip.getDestinationActivity().getLinkId();
                    final double dep = departure(ptrip, pplan);
                    // served already? then the pairing engine will carry it
                    boolean served = false;
                    for (final Person driver : members) {
                        if (driver == passenger || served) {
                            continue;
                        }
                        final Plan dplan = driver.getSelectedPlan();
                        if (dplan == null) {
                            continue;
                        }
                        for (final Trip dt : TripStructureUtils.getTrips(dplan)) {
                            if (isAllMode(dt, TransportMode.car)
                                    && from.equals(dt.getOriginActivity().getLinkId())
                                    && to.equals(dt.getDestinationActivity().getLinkId())
                                    && Math.abs(departure(dt, dplan) - dep) <= window) {
                                served = true;
                                break;
                            }
                        }
                    }
                    if (served) {
                        continue;
                    }
                    // a member whose own NON-car trip matches: the driver who
                    // drifted. Only someone the car identity permits, and only
                    // a home-anchored subtour, so the vehicle chain stays whole.
                    for (final Person driver : members) {
                        if (driver == passenger) {
                            continue;
                        }
                        if (declaredOnly && !pDrivers.contains(
                                driver.getId().toString())) {
                            continue;              // 9.146: not the named driver
                        }
                        final Object avail =
                                driver.getAttributes().getAttribute(CAR_AVAIL);
                        if (avail == null || !CAR_ALWAYS.equals(avail.toString())) {
                            continue;
                        }
                        if (driver.getAttributes().getAttribute(
                                AvailabilityModesCalculator.LOCKED_ATTRIBUTE) != null) {
                            continue;
                        }
                        final Plan dplan = driver.getSelectedPlan();
                        if (dplan == null) {
                            continue;
                        }
                        Trip match = null;
                        for (final Trip dt : TripStructureUtils.getTrips(dplan)) {
                            if (!isAllMode(dt, TransportMode.car)
                                    && from.equals(dt.getOriginActivity().getLinkId())
                                    && to.equals(dt.getDestinationActivity().getLinkId())
                                    && Math.abs(departure(dt, dplan) - dep) <= window) {
                                match = dt;
                                break;
                            }
                        }
                        if (match == null) {
                            continue;
                        }
                        driverDecohered++;
                        final boolean escortPair = ESCORT_ACTIVITY.equals(
                                match.getDestinationActivity().getType());
                        if (rng.nextDouble() >= (escortPair ? rate : jointRate)) {
                            break;
                        }
                        final Plan copy = PopulationUtils.createPlan(driver);
                        PopulationUtils.copyFromTo(dplan, copy);
                        Trip inCopy = null;
                        for (final Trip t : TripStructureUtils.getTrips(copy)) {
                            if (t.getOriginActivity().getLinkId()
                                    .equals(match.getOriginActivity().getLinkId())
                                    && t.getDestinationActivity().getLinkId()
                                    .equals(match.getDestinationActivity()
                                            .getLinkId())) {
                                inCopy = t;
                                break;
                            }
                        }
                        if (inCopy == null) {
                            break;
                        }
                        final List<Trip> subtourTrips =
                                subtourContaining(copy, inCopy);
                        // car is chain-based: convert only a subtour anchored
                        // at home, where the household's vehicle stands
                        if (subtourTrips.isEmpty()
                                || !"home".equals(subtourTrips.get(0)
                                        .getOriginActivity().getType())) {
                            break;
                        }
                        boolean built = true;
                        for (final Trip t : subtourTrips) {
                            final Leg leg =
                                    PopulationUtils.createLeg(TransportMode.car);
                            TripStructureUtils.setRoutingMode(
                                    leg, TransportMode.car);
                            try {
                                TripRouter.insertTrip(copy, t.getOriginActivity(),
                                        Collections.singletonList(leg),
                                        t.getDestinationActivity());
                            } catch (final RuntimeException ex) {
                                built = false;
                                break;
                            }
                        }
                        if (built) {
                            driver.addPlan(copy);
                            driver.setSelectedPlan(copy);
                            trim(driver);
                            driverProposed++;
                        }
                        break;
                    }
                }
            }
        }
        if (decohered > 0 || driverDecohered > 0) {
            LOG.info("escortCoherence: passenger side {} decohered / {} "
                     + "re-proposed as ride; driver side {} decohered / {} "
                     + "re-proposed as car; rates {}/{}, scope {} - proposed, "
                     + "never imposed", decohered, proposed, driverDecohered,
                     driverProposed, rate, jointRate, cfg.getCoherenceScope());
        }
    }

    /** The driver person ids the demand named for this passenger
     *  (`boundDriver`, written by build_matsim_plans.py; 9.85), or empty. */
    private static Set<String> boundDrivers(final Person person) {
        final Object raw = person.getAttributes()
                .getAttribute(RidePairingEngine.BOUND_DRIVER_ATTRIBUTE);
        final Set<String> ids = new HashSet<>();
        if (raw == null) {
            return ids;
        }
        for (final String id : raw.toString().split(",")) {
            final String t = id.trim();
            if (!t.isEmpty()) {
                ids.add(t);
            }
        }
        return ids;
    }

    /** The trips of the subtour that contains `trip`, or empty if unresolved.
     *
     * <p>Computed under THE SAME subtour structure SubtourModeChoice
     * enforces - {@code getSubtours(plan, coordDistance)} with the run's own
     * {@code subtourModeChoice.coordDistance} - because the two structures
     * genuinely differ: with coordDistance 100, activities within 100 m of
     * each other merge subtours, so a conversion that is whole-subtour under
     * the default structure is a PARTIAL conversion under the enforced one.
     * Measured cost of getting this wrong (DECISIONS.md 9.84): the first F9
     * arm died at iteration 16 on "Subtour contains a mix of chain- and
     * non-chainbased modes" - person 148091 holding [ride, bike] - after a
     * joint proposal converted a default-structure subtour that the merged
     * structure did not recognise as whole. The escort path carried the same
     * latent flaw through 163 F8 iterations; escorted school-run geometry
     * simply never triggered the merge. */
    private List<Trip> subtourContaining(final Plan plan, final Trip trip) {
        final double coordDist =
                scenario.getConfig().subtourModeChoice().getCoordDistance();
        for (final TripStructureUtils.Subtour st
                : TripStructureUtils.getSubtours(plan, coordDist)) {
            for (final Trip t : st.getTrips()) {
                if (t.getOriginActivity() == trip.getOriginActivity()
                        && t.getDestinationActivity() == trip.getDestinationActivity()) {
                    // THE OUTERMOST subtour, never the innermost. getSubtours
                    // returns NESTED subtours inner-FIRST (measured with
                    // citysim.NestedSubtourProbe: for home-work-lunch-work-home
                    // it returns the 2-trip work-lunch-work subtour at index 0
                    // with hasParent=true, and the 4-trip home..home subtour at
                    // index 1), so returning the first match returned the INNER
                    // one. Converting only an inner subtour to ride leaves the
                    // ENCLOSING subtour holding car and ride together, which is
                    // precisely what ChooseRandomLegModeForSubtour refuses with
                    // "Subtour contains a mix of chain- and non-chainbased
                    // modes" - the exception that killed arms on 26, 27, 29 and
                    // 30 August. The 26 August repair stopped this listener
                    // converting ONE TRIP of a subtour; it did not stop it
                    // converting ONE SUBTOUR of a nested plan.
                    //
                    // Subtour.getTrips() includes every nested trip, so the
                    // root's trip list covers the inner subtour too and no
                    // enclosing subtour can be left mixed. Sibling top-level
                    // subtours are untouched and stay internally consistent.
                    TripStructureUtils.Subtour root = st;
                    while (root.getParent() != null) {
                        root = root.getParent();
                    }
                    return new ArrayList<>(root.getTrips());
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
