package citysim;

import com.google.inject.Inject;
import com.google.inject.Provider;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.events.PersonArrivalEvent;
import org.matsim.api.core.v01.events.PersonDepartureEvent;
import org.matsim.api.core.v01.events.handler.PersonArrivalEventHandler;
import org.matsim.api.core.v01.events.handler.PersonDepartureEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.api.core.v01.population.Route;
import org.matsim.core.controler.OutputDirectoryHierarchy;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.events.BeforeMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.core.controler.listener.BeforeMobsimListener;
import java.util.LinkedHashMap;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.router.TripRouter;
import org.matsim.facilities.FacilitiesUtils;
import org.matsim.utils.objectattributes.attributable.AttributesImpl;
import org.matsim.core.router.StageActivityTypeIdentifier;
import org.matsim.core.utils.misc.OptionalTime;

/**
 * Tier 1 of the ride pairing: a car passenger NAMES a household driver, and
 * takes that driver's realised travel time instead of their own routed one.
 *
 * <h2>Why a lookup and not joint plans</h2>
 *
 * <p>What makes boarding a bus cheap in MATSim is that the timetable is fixed
 * before routing, so the passenger does a lookup rather than a search. A
 * household car can work the same way: a passenger leg only ever needs to NAME
 * a driver, and the candidate set is the household — never more than nine
 * people, ~1.5 licensed adults on average. A full socnetsim joint-plans
 * implementation was built against this scenario and measured at roughly ten
 * times the cost of the whole mobsim, all of it inside
 * {@code CourtesyEventsGenerator}'s joint-ACTIVITY machinery, which answers a
 * different research question. It was reverted by owner instruction; this class
 * is what replaced it (DECISIONS.md 9.44).
 *
 * <h2>Where the pairing happens, and why that is sound</h2>
 *
 * <p>MATSim's loop is {@code replan -> all plans final -> mobsim}. At
 * {@link BeforeMobsimListener} every selected plan is stable and nothing will
 * move until the mobsim runs. THAT is our timetable. A pairing made there is
 * valid for that iteration and re-made the next, exactly as a public-transport
 * connection is re-found on every re-route.
 *
 * <p>This dissolves the objection that sent the previous attempt to socnetsim: a
 * pairing baked into PLANS is destroyed by {@code SubtourModeChoice}, which
 * carries `ride` in its mode list; a pairing made AFTER replanning is not.
 *
 * <h2>How a passenger takes the driver's time without a mobsim change</h2>
 *
 * <p>`ride` is in {@code routing.networkModes} but is not the qsim
 * {@code mainMode}, so MATSim routes it over the network and then TELEPORTS it.
 * {@code DefaultTeleportationEngine.handleDeparture} asks the agent for
 * {@code getExpectedTravelTime()}, which is
 * {@code TimeInterpretation.decideOnLegTravelTime(leg)}, which is exactly
 * {@code route.getTravelTime().or(leg.getTravelTime())} — verified against the
 * pinned jar's bytecode, not assumed from the API.
 *
 * <p>The ROUTE's time therefore wins, and both routing modules
 * ({@code NetworkRoutingModule}, {@code NetworkRoutingInclAccessEgressModule})
 * set the leg's and the route's time TOGETHER. So this class writes only the
 * ROUTE's time and never the leg's. That single choice buys three things at
 * once and needs no bookkeeping of its own:
 *
 * <ul>
 *   <li>the router's own estimate survives untouched in
 *       {@code leg.getTravelTime()}, so it is the baseline;</li>
 *   <li>an UNPAIRED leg is restored to exactly that baseline, which is the
 *       guarantee that an unpaired leg behaves exactly as it does today;</li>
 *   <li>the baseline refreshes itself whenever the router re-routes the leg,
 *       and survives the plan-copying that replanning does, because it lives in
 *       the plan rather than in a side map.</li>
 * </ul>
 *
 * <p>Note what this deliberately does NOT do. It does not put a passenger
 * vehicle in the mobsim: a passenger travels in a car that is already there, so
 * a second vehicle would double-count the traffic. It does not move the
 * passenger's departure time, which would cascade through the rest of that
 * person's day; the pairing window is a tolerance, and the sub-window
 * adjustment is a STATED limitation. Binding the passenger physically into the
 * vehicle, with seats constraining flow, is Tier 2 and an increment on this,
 * not a prerequisite for it.
 *
 * <h2>The driver's realised time</h2>
 *
 * <p>Realised means realised in the mobsim, which is where the sample-dependent
 * queueing lives that a teleported passenger is structurally immune to — the
 * mechanism behind the fraction-dependent car/ride margin the convergence
 * pilots flagged and could not explain. It is necessarily the PREVIOUS
 * iteration's realisation, because at BeforeMobsim the current one has not
 * happened; that is the same one-iteration lag every travel time in MATSim
 * carries. Before the first mobsim, and for a driver leg with no realised
 * counterpart, the driver's own routed time is used instead and the fallback is
 * counted in the diagnostic.
 *
 * <h2>What it reports, and why the report is the point</h2>
 *
 * <p>The unpaired share, SPLIT BY DIRECTION, is written every iteration to
 * {@code ride_pairing.csv}. Return trips pair INDEPENDENTLY of outbound ones —
 * `ride` is correctly not a chain-based mode, a passenger owns no vehicle to
 * bring home, and forcing symmetry would MANUFACTURE car trips, which is the
 * direction of error this project is most exposed to. The obligation that
 * creates is to report the asymmetry rather than to remove it: a large unpaired
 * share is a finding about the DEMAND, not about this class.
 */
public final class RidePairingEngine implements BeforeMobsimListener,
        AfterMobsimListener, PersonDepartureEventHandler,
        PersonArrivalEventHandler {

    /** Person attribute written by build_matsim_plans.py; absent on the
     *  household-less external and through boundary tiers. */
    public static final String HOUSEHOLD_ATTRIBUTE = "householdId";
    /** Person attribute written by build_matsim_plans.py from the B2
     *  non-household lift bindings (DECISIONS.md 9.60): the household id of
     *  the DRIVER whose re-targeted escort tour serves this person, so the
     *  pairing may search that household's car legs in addition to the
     *  person's own. The binding is an eligibility, not a guarantee - the
     *  driver's leg must still match under the declared rule and window. */
    public static final String LIFT_HOUSEHOLD_ATTRIBUTE = "liftHousehold";
    /** Person attribute written by build_matsim_plans.py from the B2 JOINT
     *  bindings (DECISIONS.md 9.85): the person id(s) of the driver(s) this
     *  companion was generated to travel WITH. The binder has always
     *  written the identity and the population has always dropped it, so
     *  this engine had to RE-DISCOVER a declared pair from geometry and
     *  the clock - and MATSim's own TimeAllocationMutator moves the two
     *  members independently, at a range the registry did not declare
     *  until 9.85. Measured on arm 20260828T111708 at iteration 100:
     *  73.8% of companion ride legs still had their declared driver making
     *  the same-endpoint trip BY CAR, but the median gap between them had
     *  drifted to 10.3 min with p90 at 45.1, so only 60.6% were inside the
     *  15-minute inference window. The driver was there; the clock hid
     *  them. The binding is still an ELIGIBILITY, not a guarantee. */
    public static final String BOUND_DRIVER_ATTRIBUTE = "boundDriver";
    /** Written by build_matsim_plans.py, and already consumed by
     *  {@link AvailabilityModesCalculator}'s sibling attributes. */
    public static final String LICENCE_ATTRIBUTE = "hasLicense";
    public static final String LICENCE_YES = "yes";
    /** Person attribute naming whether a car is available to them. */
    public static final String CAR_AVAIL_ATTRIBUTE = "carAvail";
    public static final String CAR_AVAIL_NEVER = "never";

    private static final String OUT_FILE = "ride_pairing.csv";
    private static final String HEADER =
            "iteration,ride_legs,paired,unpaired,pair_rate,"
            + "paired_outbound,paired_return,paired_intermediate,"
            + "unpaired_outbound,unpaired_return,unpaired_intermediate,"
            + "total_outbound,total_return,total_intermediate,"
            + "car_legs,occupancy_from_pairings,"
            + "driver_time_realised,driver_time_routed,"
            + "mean_driver_minus_baseline_s,capacity_refusals,"
            + "households_with_ride,ride_legs_no_household,elapsed_ms,"
            // WHY a leg missed, as an ordered funnel. A pair rate alone cannot
            // separate a passenger no driver could ever serve from one whose
            // driver left ten minutes early, and those two want opposite
            // answers: the first should abandon ride on its score, the second
            // is a departure-time coordination MATSim does not model.
            + "miss_no_candidate,miss_window,miss_endpoints,miss_capacity,"
            // 9.85: how many pairings were made with the driver the demand
            // NAMED, and how many of those the inference window alone would
            // have thrown away. The second column is the mechanism's
            // effect; a zero in it means the binding changed nothing.
            + "paired_declared,paired_by_identity,"
            // For a leg that missed ONLY on timing, how far off was the nearest
            // driver making a geometrically matching trip? A window miss can be
            // a near miss the declared tolerance just failed to reach, or a
            // driver hours away who was never going to serve it, and widening
            // the tolerance is only defensible against the first. The buckets
            // are minutes of |driver departure - passenger departure|.
            + "gap_le30,gap_le45,gap_le60,gap_le120,gap_gt120,gap_median_min\n";

    private final Scenario scenario;
    private final OutputDirectoryHierarchy io;
    private final RidePairingConfigGroup cfg;

    /** Household id per person, resolved once: membership never changes. */
    private final Map<Id<Person>, String> household = new HashMap<>();
    /** Lift-driver household per bound passenger (9.60), resolved once. */
    private final Map<Id<Person>, String> liftHousehold = new HashMap<>();
    /** Declared joint-tour driver ids per companion (9.85), resolved once. */
    private final Map<Id<Person>, Set<String>> boundDriver = new HashMap<>();
    /** Licence holding per person, resolved once, for the same reason. */
    private final Map<Id<Person>, Boolean> licensed = new HashMap<>();
    /** Whether a car is available to this person at all. */
    private final Map<Id<Person>, Boolean> carAvailable = new HashMap<>();
    /** The mode each remoded leg was actually executed as, so the
     *  AfterMobsim restore looks for the trip it really created. */
    private final Map<RideLeg, String> remodedAs = new HashMap<>();
    private boolean indexed = false;
    /** Population membership does not change during a run, so the id-ordered
     *  traversal that makes the pairing deterministic is built once. */
    private List<Person> ordered = null;

    /** Realised car-leg durations from the mobsim that is running now. */
    /**
     * This iteration's physical-boarding bookings (DECISIONS.md 9.53): for a
     * paired ride, which driver's vehicle the passenger should be aboard.
     * Written here at BeforeMobsim, consumed by {@link JointRideEngine} on the
     * qsim thread after this listener has finished — never concurrently.
     */
    private final Map<Id<Person>, List<Booking>> bookings = new HashMap<>();

    /** One paired ride leg's claim on a driver's vehicle. */
    public static final class Booking {
        final Id<Link> from;
        final Id<Link> to;
        final double plannedDeparture;
        final Id<Person> driver;
        /** 9.85: the tolerance THIS booking was made under, in seconds.
         *  A declared pair is booked on the wider bound window, so the
         *  passenger must be allowed to wait that long for the car -
         *  otherwise the booking is made and then timed out, and the
         *  pair rate rises while no additional passenger ever boards. */
        final double waitSeconds;

        Booking(final Id<Link> from, final Id<Link> to,
                final double plannedDeparture, final Id<Person> driver,
                final double waitSeconds) {
            this.from = from;
            this.to = to;
            this.plannedDeparture = plannedDeparture;
            this.driver = driver;
            this.waitSeconds = waitSeconds;
        }

        /** How long this passenger may wait, in seconds. */
        public double waitSeconds() {
            return this.waitSeconds;
        }

        public Id<Link> destination() {
            return this.to;
        }

        public Id<Person> driver() {
            return this.driver;
        }
    }

    /**
     * The booking for this passenger departing this link now, or null. The
     * booking is CONSUMED: a person with two paired ride legs from the same
     * link holds two bookings, each redeemable once, nearest planned
     * departure first.
     */
    public Booking claimBooking(final Id<Person> person, final Id<Link> link,
                                final double now) {
        final List<Booking> list = this.bookings.get(person);
        if (list == null) {
            return null;
        }
        Booking best = null;
        for (final Booking b : list) {
            if (!b.from.equals(link)) {
                continue;
            }
            if (best == null || Math.abs(b.plannedDeparture - now)
                    < Math.abs(best.plannedDeparture - now)) {
                best = b;
            }
        }
        if (best != null) {
            list.remove(best);
        }
        return best;
    }

    private Map<Id<Person>, List<Realised>> current = new HashMap<>();
    /** ... and from the one that has finished, which is what pairing reads. */
    private Map<Id<Person>, List<Realised>> previous = new HashMap<>();
    /** Car legs in flight, one per person at a time. */
    private final Map<Id<Person>, Realised> inFlight = new HashMap<>();

    private boolean headerWritten = false;
    private int writeFailures = 0;

    /** Legs re-moded to walk for THIS mobsim only, with the ride route to give
     *  back at AfterMobsim. See {@link #notifyAfterMobsim}: the forced walk is
     *  an execution, not an amputation. */
    private final List<RideLeg> remodedThisMobsim = new ArrayList<>();

    /** Why unpaired legs missed, this iteration, as an ordered funnel:
     *  no candidate driver leg at all / none inside the window / none whose
     *  endpoints matched / all refused for capacity. Reset per pairing pass. */
    private int missNoCandidate = 0;
    private int missWindow = 0;
    private int missEndpoints = 0;
    /** Pairings whose driver was the DECLARED partner (9.85), and the
     *  subset of those the inference window alone would have refused -
     *  which is this mechanism's effect, measured rather than argued. */
    private int pairedDeclared = 0;
    private int pairedByIdentity = 0;
    private int missCapacity = 0;

    /** Minutes off the nearest ENDPOINT-MATCHING driver, for legs that missed
     *  only on timing. Kept as a list so the median is measured, not assumed. */
    private final List<Double> missGapMinutes = new ArrayList<>();

    /** One realised car leg: where it ran, when it left, how long it took. */
    private static final class Realised {
        private final Id<Link> from;
        private Id<Link> to;
        private final double departure;
        private double duration = Double.NaN;

        Realised(final Id<Link> from, final double departure) {
            this.from = from;
            this.departure = departure;
        }
    }

    /** One candidate driver leg, taken from a selected plan. */
    private static final class DriverLeg {
        private final Id<Person> person;
        private final Id<Link> from;
        private final Id<Link> to;
        private final double departure;
        private double routedTravelTime;
        /**
         * Every link the driver actually drives, start to end. A passenger can
         * only be carried on a segment of it, so the path - not the pair of
         * endpoints - is what a containment test and a time apportionment need.
         * Rewritten by a 9.128 detour, which is why it is not final.
         */
        private List<Id<Link>> path;
        private int carrying = 0;
        /** 9.128: the routed time before a detour was written over it. */
        private double routedBefore = Double.NaN;
        /** 9.128: the plan leg and its route, so a detour can be written. */
        private final Leg leg;
        private final Route route;

        DriverLeg(final Id<Person> person, final Id<Link> from, final Id<Link> to,
                  final double departure, final double routedTravelTime,
                  final List<Id<Link>> path, final Leg leg, final Route route) {
            this.leg = leg;
            this.route = route;
            this.person = person;
            this.from = from;
            this.to = to;
            this.departure = departure;
            this.routedTravelTime = routedTravelTime;
            this.path = path;
        }
    }

    /** One ride leg awaiting a driver, with the plan handles needed to retime it. */
    private static final class RideLeg {
        private final Id<Person> person;
        private final Leg leg;
        private final Route route;
        private final Id<Link> from;
        private final Id<Link> to;
        private final double departure;
        private final String direction;
        /** 9.120: the real (non-stage) activity this trip leaves from, and
         *  the planned access time between its end and the ride leg's own
         *  departure - what a declared pair's re-timing has to move. */
        private final Activity origin;
        private final double accessTravel;
        /** 9.128: the plan this leg sits in and its index there - the
         *  handles the meeting-point reshaping needs. */
        private final Plan plan;
        private final int index;

        RideLeg(final Id<Person> person, final Leg leg, final Route route,
                final Id<Link> from, final Id<Link> to, final double departure,
                final String direction, final Activity origin,
                final double accessTravel, final Plan plan, final int index) {
            this.plan = plan;
            this.index = index;
            this.person = person;
            this.leg = leg;
            this.route = route;
            this.from = from;
            this.to = to;
            this.departure = departure;
            this.direction = direction;
            this.origin = origin;
            this.accessTravel = accessTravel;
        }
    }

    /** 9.128: routes a driver's detour through a declared passenger's links
     *  with the run's own car router, so the detour is driven like every
     *  other car leg and the driver's score pays for it. */
    private final Provider<TripRouter> tripRouter;

    @Inject
    RidePairingEngine(final Scenario scenario, final OutputDirectoryHierarchy io,
                      final Provider<TripRouter> tripRouter) {
        this.scenario = scenario;
        this.io = io;
        this.tripRouter = tripRouter;
        this.cfg = (RidePairingConfigGroup) scenario.getConfig().getModules()
                .get(RidePairingConfigGroup.NAME);
    }

    // ---- the mobsim's own record of what actually happened ----------------

    @Override
    public void handleEvent(final PersonDepartureEvent event) {
        if (!enabled() || !TransportMode.car.equals(event.getLegMode())) {
            return;
        }
        inFlight.put(event.getPersonId(),
                     new Realised(event.getLinkId(), event.getTime()));
    }

    @Override
    public void handleEvent(final PersonArrivalEvent event) {
        if (!enabled() || !TransportMode.car.equals(event.getLegMode())) {
            return;
        }
        final Realised r = inFlight.remove(event.getPersonId());
        if (r == null) {
            return;
        }
        r.to = event.getLinkId();
        r.duration = event.getTime() - r.departure;
        current.computeIfAbsent(event.getPersonId(), k -> new ArrayList<>(2)).add(r);
    }

    /**
     * Deliberately NOT overriding {@code reset(int)}.
     *
     * <p>MATSim resets event handlers immediately before the mobsim, which is
     * AFTER {@link #notifyBeforeMobsim} — so a reset that cleared the realised
     * times would clear exactly the data the pairing had just been about to
     * read, and would do it silently. The buffers are swapped explicitly in
     * {@link #notifyBeforeMobsim} instead, where the ordering is visible.
     */

    // ---- the pairing ------------------------------------------------------

    @Override
    public void notifyBeforeMobsim(final BeforeMobsimEvent event) {
        if (!enabled()) {
            return;
        }
        final long started = System.currentTimeMillis();
        // The mobsim that is about to run fills `current`; the one that has
        // finished is what the pairing may read. Swapping here, rather than in
        // reset(), is what makes the ordering auditable.
        previous = current;
        current = new HashMap<>();
        inFlight.clear();
        bookings.clear();
        remodedThisMobsim.clear();
        remodedAs.clear();
        missNoCandidate = 0;
        missWindow = 0;
        missEndpoints = 0;
        missCapacity = 0;
        missGapMinutes.clear();
        pairedDeclared = 0;
        pairedByIdentity = 0;

        index();

        final double window = cfg.getWindowMinutes() * 60.0;
        // 9.85: the tolerance for a pair the DEMAND DECLARES. It relaxes
        // IDENTIFICATION only - endpoints, capacity and physical boarding
        // still decide, and the realised gap is waiting time the passenger
        // pays for in score. Equal to `window` recovers the old behaviour.
        final double boundWindow = cfg.getBoundWindowMinutes() * 60.0;
        final String rule = cfg.getRule();
        // 9.128: where a declared pair's links differ, the DRIVER detours
        // through the passenger's. Deferred to after the loop, because a
        // driver's detour is routed once through every passenger it carries.
        final boolean detour = RidePairingConfigGroup.MEETING_DRIVER_DETOUR
                .equals(cfg.getDeclaredMeeting());
        final Map<DriverLeg, List<RideLeg>> detours = new LinkedHashMap<>();
        final int capacity = cfg.getMaxPassengersPerVehicle();
        final double dwell = cfg.getPickupDwellSeconds();

        final Map<String, List<DriverLeg>> driversByHousehold = new HashMap<>();
        final List<RideLeg> rides = new ArrayList<>();
        int carLegs = 0;
        int noHousehold = 0;

        // Persons in id order, so the pairing does not depend on map iteration
        // order. Determinism is a hard constraint here, not a nicety: the same
        // seed must produce the same run.
        for (final Person person : ordered) {
            final Plan plan = person.getSelectedPlan();
            if (plan == null) {
                continue;
            }
            final String hh = household.get(person.getId());
            final List<PlanElement> elements = plan.getPlanElements();
            double clock = Double.NaN;
            String previousActivity = null;
            // 9.120: the real activity the current trip leaves from, and the
            // planned access time accumulated since its end - the handles a
            // declared pair's re-timing needs (see below)
            Activity lastReal = null;
            double accessSinceReal = 0.0;
            for (int i = 0; i < elements.size(); i++) {
                final PlanElement pe = elements.get(i);
                if (pe instanceof Activity) {
                    final Activity act = (Activity) pe;
                    final OptionalTime end = act.getEndTime();
                    if (end.isDefined()) {
                        clock = end.seconds();
                    }
                    // A ride trip under routing.accessEgressType is
                    // walk -> `ride interaction` -> ride -> `ride interaction`
                    // -> walk, so the activity ADJACENT to the ride leg is a
                    // stage activity, never the real one. Reading it as the
                    // real one classified every leg `intermediate` and made the
                    // direction split - the whole obligation this diagnostic
                    // carries - silently all-zero.
                    if (!StageActivityTypeIdentifier.isStageActivity(act.getType())) {
                        previousActivity = act.getType();
                        lastReal = act;
                        accessSinceReal = 0.0;
                    }
                    continue;
                }
                final Leg leg = (Leg) pe;
                final double departure = legDeparture(leg, clock);
                final double travel = definedOr(leg.getTravelTime(), 0.0);
                if (!Double.isNaN(clock)) {
                    clock = departure + travel;
                }
                final double accessBefore = accessSinceReal;
                accessSinceReal += travel;
                final Route route = leg.getRoute();
                if (route == null) {
                    continue;
                }
                if (TransportMode.car.equals(leg.getMode())) {
                    carLegs++;
                    if (hh != null && Boolean.TRUE.equals(licensed.get(person.getId()))) {
                        driversByHousehold
                                .computeIfAbsent(hh, k -> new ArrayList<>(2))
                                .add(new DriverLeg(person.getId(),
                                                   route.getStartLinkId(),
                                                   route.getEndLinkId(),
                                                   departure, travel,
                                                   drivenPath(route), leg, route));
                    }
                } else if (TransportMode.ride.equals(leg.getMode())) {
                    if (hh == null) {
                        // An external or through boundary agent has no household
                        // by construction, so it can never pair. It keeps
                        // today's behaviour and is counted, not hidden.
                        noHousehold++;
                        restore(leg, route);
                        continue;
                    }
                    rides.add(new RideLeg(person.getId(), leg, route,
                                          route.getStartLinkId(),
                                          route.getEndLinkId(), departure,
                                          direction(previousActivity,
                                                    nextActivity(elements, i)),
                                          lastReal, accessBefore, plan, i));
                }
            }
        }

        // Candidate order must be deterministic too. Person id, then departure.
        for (final List<DriverLeg> legs : driversByHousehold.values()) {
            legs.sort(Comparator.<DriverLeg, Id<Person>>comparing(d -> d.person)
                              .thenComparingDouble(d -> d.departure));
        }
        rides.sort(Comparator.<RideLeg, Id<Person>>comparing(r -> r.person)
                           .thenComparingDouble(r -> r.departure));

        final Map<String, int[]> paired = new HashMap<>();
        final Map<String, int[]> unpaired = new HashMap<>();
        int nPaired = 0;
        int remoded = 0;
        // 9.120: declared passengers whose departure was moved to the
        // driver's, and by how much in total - the drift the re-timing removed
        int retimed = 0;
        double retimeShiftSum = 0.0;
        int fromRealised = 0;
        int fromRouted = 0;
        int capacityRefusals = 0;
        double deltaSum = 0.0;

        for (final RideLeg ride : rides) {
            List<DriverLeg> candidates =
                    driversByHousehold.getOrDefault(household.get(ride.person),
                                                    Collections.emptyList());
            // DECISIONS.md 9.60: a bound lift widens the search to the
            // driver's household - own household first, so the binding can
            // never displace an intra-household pairing at equal gap.
            // Comma-separated since 9.68: a round-trip pair may be served by
            // drivers from two different households.
            final String lift = liftHousehold.get(ride.person);
            if (lift != null) {
                List<DriverLeg> merged = null;
                for (final String liftHh : lift.split(",")) {
                    final List<DriverLeg> liftCandidates = driversByHousehold
                            .getOrDefault(liftHh.trim(),
                                          Collections.emptyList());
                    if (!liftCandidates.isEmpty()) {
                        if (merged == null) {
                            merged = new ArrayList<>(candidates);
                        }
                        merged.addAll(liftCandidates);
                    }
                }
                if (merged != null) {
                    candidates = merged;
                }
            }
            DriverLeg best = null;
            double bestGap = Double.MAX_VALUE;
            boolean bestDeclared = false;
            boolean refusedForCapacity = false;
            // The funnel, so a miss can say WHICH gate closed on it.
            int sawCandidate = 0;
            boolean sawInWindow = false;
            boolean sawEndpoints = false;
            // The nearest driver making a geometrically matching trip, whatever
            // the clock said. This is what decides whether a window miss was a
            // near miss or a driver who was never going to serve it.
            double nearestMatchingGap = Double.MAX_VALUE;
            final Set<String> declared = boundDriver.getOrDefault(
                    ride.person, Collections.emptySet());
            for (final DriverLeg driver : candidates) {
                if (driver.person.equals(ride.person)) {
                    continue;                       // you cannot drive yourself
                }
                sawCandidate++;
                final double gap = Math.abs(driver.departure - ride.departure);
                // 9.85: for the driver the demand NAMED, identity has
                // already settled whether this is the same trip, so the
                // clock only has to cover the drift replanning introduced.
                final boolean isDeclared = declared.contains(driver.person.toString());
                // 9.120: for the driver the demand NAMED there is no clock
                // test at all. The two members were generated as ONE trip
                // and only MATSim's independent time mutation ever moved
                // them apart - measured on the F14 arm, the declared pair
                // on the same OD within 15 min fell 57.1% -> 27.5% in 30
                // iterations while gaps over 45 min rose 1.8% -> 7.5%. The
                // passenger is RE-TIMED to the driver below, so the gap is
                // not paid for as waiting: it is removed at its source.
                if (!isDeclared && gap > window) {
                    if (endpointsMatch(rule, driver, ride) && gap < nearestMatchingGap) {
                        nearestMatchingGap = gap;
                    }
                    continue;
                }
                sawInWindow = true;
                // 9.128: the driver the demand NAMED is the same trip by
                // identity; where the links differ the driver will detour
                // through the passenger's, so geometry is not a gate here.
                final boolean meets = isDeclared && detour;
                if (!meets && !endpointsMatch(rule, driver, ride)) {
                    continue;
                }
                sawEndpoints = true;
                if (driver.carrying >= capacity) {
                    refusedForCapacity = true;
                    continue;
                }
                // A declared partner outranks a coincidence at equal gap:
                // preferring the nearer stranger would let the inference
                // overwrite the binding it exists to approximate.
                if (best == null
                        || (isDeclared && !bestDeclared)
                        || (isDeclared == bestDeclared && gap < bestGap)) {
                    bestGap = gap;
                    best = driver;
                    bestDeclared = isDeclared;
                }
            }
            if (best == null) {
                if (refusedForCapacity) {
                    capacityRefusals++;
                }
                // GEOMETRY BEFORE TIMING. Asking "was anyone in the window?"
                // first labelled as a timing miss every passenger whose
                // household drove somewhere else entirely: measured 1,529 such
                // legs of which only 112 had an endpoint-matching driver at ANY
                // hour, median 253.7 minutes away. Widening the window would
                // have recovered 13. The question that separates a fixable miss
                // from a hopeless one is whether a matching TRIP exists at all.
                final boolean matchedEver =
                        sawEndpoints || nearestMatchingGap < Double.MAX_VALUE;
                if (sawCandidate == 0) {
                    missNoCandidate++;              // no household car leg at all
                } else if (!matchedEver) {
                    missEndpoints++;                // the household drove elsewhere
                } else if (!sawInWindow) {
                    missWindow++;                   // the right trip, the wrong hour
                    missGapMinutes.add(nearestMatchingGap / 60.0);
                } else {
                    missCapacity++;                 // right trip, right hour, car full
                }
                unpaired.computeIfAbsent(ride.direction, k -> new int[1])[0]++;
                if (cfg.isPhysicalBoarding() && cfg.isRemodeUnpaired()) {
                    // DECISIONS.md 9.55: a ride trip no household driver can
                    // physically serve is not a ride trip - it WALKS, on the
                    // network, THIS ITERATION. A long forced walk scores
                    // terribly, so co-evolution reassigns the tour, and ride
                    // becomes emergent: only what the driver supply carries
                    // survives. No parameter invented; the constraint is the
                    // price.
                    //
                    // The walk is an EXECUTION, not an amputation. The mode is
                    // given back at AfterMobsim (notifyAfterMobsim), because
                    // scoring is event-driven: the agent is still charged for
                    // the walk it actually made, while the plan keeps `ride`
                    // as an alternative co-evolution can re-select when the
                    // driver's selected plan serves it again. Mutating the
                    // plan permanently made pairing failure IRREVERSIBLE while
                    // pairing success created nothing - a one-way ratchet.
                    // Measured on 20260825T135734: 87,019 ride legs at
                    // iteration 0, 61,409 unpaired, and 58,791 of them gone by
                    // iteration 1 - 95.7% - never to return; paired legs then
                    // eroded 25,610 -> 7,320 on timing misses alone, an
                    // exponential decay with a 36-iteration half-life heading
                    // to the pre-repair 0.0013 occupancy. Whether ride is
                    // worth choosing is for the score to decide over many
                    // iterations, not for one missed pairing to settle.
                    remodedThisMobsim.add(ride);
                    final String fallback = fallbackMode(ride.person);
                    remodedAs.put(ride, fallback);
                    ride.leg.setMode(fallback);
                    org.matsim.core.router.TripStructureUtils.setRoutingMode(
                            ride.leg, fallback);
                    // the car route may traverse walk-excluded links, and
                    // PersonPrepareForSim refuses a route inconsistent with
                    // link modes (measured). A null route makes it re-route
                    // the leg as WALK on the walk network before the mobsim -
                    // properly walked from its first iteration.
                    ride.leg.setRoute(null);
                    remoded++;
                    continue;
                }
                restore(ride.leg, ride.route);
                continue;
            }
            // 9.128: where a declared pair's links differ, the driver
            // detours through them. The pair is accepted here and its
            // timing, booking and re-timing are written once the driver's
            // detour is routed through every passenger it carries.
            if (bestDeclared && detour && !endpointsMatch(rule, best, ride)) {
                best.carrying++;
                detours.computeIfAbsent(best, k -> new ArrayList<>(2)).add(ride);
                continue;
            }
            best.carrying++;
            nPaired++;
            if (bestDeclared) {
                pairedDeclared++;
                if (bestGap > window) {
                    // the inference window alone would have refused this
                    // pair; the demand's own binding is what kept it
                    pairedByIdentity++;
                }
                // 9.120: a declared passenger leaves when the car leaves.
                // The activity this trip departs from is ended so that the
                // planned access walk delivers the passenger to the meeting
                // link exactly at the driver's planned departure - the walk
                // is PCE 0 at a capped constant speed, so its planned time
                // is its realised time. Nothing is invented: the two
                // members' clocks were one clock when the demand generated
                // the trip. Refused only when the driver leaves before this
                // activity could start, which is a genuine miss and stays
                // one. The plan keeps the new end time, so the passenger's
                // memory converges on the driver's clock rather than being
                // re-drawn from it every round.
                if (ride.origin != null) {
                    final double target = best.departure - ride.accessTravel;
                    final OptionalTime start = ride.origin.getStartTime();
                    if (!start.isDefined() || target > start.seconds()) {
                        final OptionalTime was = ride.origin.getEndTime();
                        if (!was.isDefined()
                                || Math.abs(was.seconds() - target) > 0.5) {
                            ride.origin.setEndTime(target);
                            retimed++;
                            retimeShiftSum += Math.abs(
                                    (was.isDefined() ? was.seconds() : target)
                                    - target);
                        }
                    }
                }
            }
            paired.computeIfAbsent(ride.direction, k -> new int[1])[0]++;

            final double realised = realisedDuration(best);
            final double wholeLeg;
            if (Double.isNaN(realised)) {
                wholeLeg = best.routedTravelTime;
                fromRouted++;
            } else {
                wholeLeg = realised;
                fromRealised++;
            }
            // The passenger rides the SEGMENT, not the leg. Unity when the
            // segment is the whole route, so `both_links` is bit-for-bit what
            // it was and this change is measurable rather than asserted.
            final double driverTime = wholeLeg * carriedShare(best, ride);
            final double baseline = definedOr(ride.leg.getTravelTime(),
                                              definedOr(ride.route.getTravelTime(), 0.0));
            deltaSum += driverTime - baseline;
            // ONLY the route's travel time is written. The leg keeps the
            // router's own estimate, which is what makes an unpaired leg
            // restorable to exactly today's behaviour.
            ride.route.setTravelTime(driverTime + dwell);
            if (cfg.isPhysicalBoarding()) {
                // The booking JointRideEngine redeems at the qsim's own
                // departure (DECISIONS.md 9.53). The route time written above
                // stays: it is exactly what a MISSED boarding falls back to,
                // so the fallback is Tier 1 verbatim rather than a third
                // behaviour.
                bookings.computeIfAbsent(ride.person, k -> new ArrayList<>(2))
                        .add(new Booking(ride.from, ride.to, ride.departure,
                                         best.person,
                                         bestDeclared ? boundWindow : window));
            }
        }

        // 9.128: the deferred detours. Drivers in the order their first
        // passenger was met (rides are in person-id order, so this is
        // deterministic); each driver's car leg is routed through its
        // passengers' origin links in departure order, then their
        // destination links in the same order, then home to its own
        // destination.
        int detoured = 0;
        int detourDrivers = 0;
        double detourExtraS = 0.0;
        int detourRefused = 0;
        for (final Map.Entry<DriverLeg, List<RideLeg>> e : detours.entrySet()) {
            final DriverLeg driver = e.getKey();
            final List<RideLeg> carried = e.getValue();
            carried.sort(Comparator.<RideLeg>comparingDouble(r -> r.departure)
                                 .thenComparing(r -> r.person));
            final Map<RideLeg, Double> passAt = routeDetour(driver, carried);
            if (passAt == null) {
                detourRefused += carried.size();
                missEndpoints += carried.size();
                driver.carrying -= carried.size();
                for (final RideLeg ride : carried) {
                    restore(ride.leg, ride.route);
                }
                continue;
            }
            detourDrivers++;
            for (final RideLeg ride : carried) {
                detoured++;
                nPaired++;
                pairedDeclared++;
                paired.computeIfAbsent(ride.direction, k -> new int[1])[0]++;
                final double pass = passAt.get(ride);
                // the passenger is at their own link when the car passes it
                if (ride.origin != null) {
                    final double target = pass - ride.accessTravel;
                    final OptionalTime start = ride.origin.getStartTime();
                    if (!start.isDefined() || target > start.seconds()) {
                        final OptionalTime was = ride.origin.getEndTime();
                        if (!was.isDefined()
                                || Math.abs(was.seconds() - target) > 0.5) {
                            ride.origin.setEndTime(target);
                            retimed++;
                            retimeShiftSum += Math.abs(
                                    (was.isDefined() ? was.seconds() : target)
                                    - target);
                        }
                    }
                }
                final double realised = realisedDuration(driver);
                final double wholeLeg;
                if (Double.isNaN(realised)) {
                    wholeLeg = driver.routedTravelTime;
                    fromRouted++;
                } else {
                    wholeLeg = realised;
                    fromRealised++;
                }
                final double driverTime = wholeLeg * carriedShare(driver, ride);
                final double baseline = definedOr(ride.leg.getTravelTime(),
                                                  definedOr(ride.route.getTravelTime(), 0.0));
                deltaSum += driverTime - baseline;
                ride.route.setTravelTime(driverTime + dwell);
                if (cfg.isPhysicalBoarding()) {
                    bookings.computeIfAbsent(ride.person, k -> new ArrayList<>(2))
                            .add(new Booking(ride.from, ride.to, pass,
                                             driver.person, boundWindow));
                }
            }
            detourExtraS += driver.routedTravelTime - driver.routedBefore;
        }
        org.apache.logging.log4j.LogManager.getLogger(RidePairingEngine.class)
                .info("ridePairing: {} declared passengers picked up on {} drivers' "
                      + "detours, mean detour {} s per driver; {} refused for an "
                      + "unroutable detour (DECISIONS.md 9.128)",
                      detoured, detourDrivers,
                      detourDrivers == 0 ? 0 : Math.round(detourExtraS / detourDrivers),
                      detourRefused);

        write(event.getIteration(), rides.size(), nPaired, paired, unpaired,
              carLegs, fromRealised, fromRouted,
              nPaired == 0 ? 0.0 : deltaSum / nPaired, capacityRefusals,
              driversByHousehold.size(), noHousehold,
              System.currentTimeMillis() - started);
        if (cfg.isPhysicalBoarding() && cfg.isRemodeUnpaired()) {
            org.apache.logging.log4j.LogManager.getLogger(RidePairingEngine.class)
                    .info("ridePairing: {} unpaired ride legs re-moded to "
                          + "network walk (DECISIONS.md 9.55)", remoded);
        }
        org.apache.logging.log4j.LogManager.getLogger(RidePairingEngine.class)
                .info("ridePairing: {} declared passengers re-timed to their "
                      + "driver's departure, mean shift {} s (DECISIONS.md 9.120)",
                      retimed, retimed == 0 ? 0.0
                              : Math.round(retimeShiftSum / retimed));
    }

    // ---- 9.128: the driver's detour through a declared passenger's links ---

    /**
     * Route the driver's car leg through the carried passengers' links and
     * write it to the driver's plan. Returns, per passenger, the clock at
     * which the car reaches their origin link; null - with the plan
     * untouched - when any segment cannot be routed.
     */
    private Map<RideLeg, Double> routeDetour(final DriverLeg driver,
                                             final List<RideLeg> carried) {
        if (!(driver.route instanceof NetworkRoute)) {
            return null;
        }
        final Person person = scenario.getPopulation().getPersons().get(driver.person);
        if (person == null) {
            return null;
        }
        final List<Id<Link>> via = new ArrayList<>(2 + 2 * carried.size());
        via.add(driver.from);
        for (final RideLeg r : carried) {
            via.add(r.from);
        }
        for (final RideLeg r : carried) {
            via.add(r.to);
        }
        via.add(driver.to);
        final List<Id<Link>> path = new ArrayList<>();
        final Map<Id<Link>, Double> reached = new HashMap<>();
        path.add(driver.from);
        reached.put(driver.from, driver.departure);
        double clock = driver.departure;
        double metres = 0.0;
        for (int k = 1; k < via.size(); k++) {
            final Id<Link> a = via.get(k - 1);
            final Id<Link> b = via.get(k);
            if (a.equals(b)) {
                reached.putIfAbsent(b, clock);
                continue;
            }
            final Link la = scenario.getNetwork().getLinks().get(a);
            final Link lb = scenario.getNetwork().getLinks().get(b);
            if (la == null || lb == null) {
                return null;
            }
            final List<? extends PlanElement> routed = tripRouter.get().calcRoute(
                    TransportMode.car, FacilitiesUtils.wrapLink(la),
                    FacilitiesUtils.wrapLink(lb), clock, person, new AttributesImpl());
            if (routed == null || routed.size() != 1 || !(routed.get(0) instanceof Leg)) {
                return null;
            }
            final Leg seg = (Leg) routed.get(0);
            if (!(seg.getRoute() instanceof NetworkRoute) || !seg.getTravelTime().isDefined()) {
                return null;
            }
            final NetworkRoute nr = (NetworkRoute) seg.getRoute();
            path.addAll(nr.getLinkIds());
            path.add(b);
            for (final Id<Link> id : nr.getLinkIds()) {
                final Link l = scenario.getNetwork().getLinks().get(id);
                metres += l == null ? 0.0 : l.getLength();
            }
            metres += lb.getLength();
            clock += seg.getTravelTime().seconds();
            reached.putIfAbsent(b, clock);
        }
        final Map<RideLeg, Double> passAt = new HashMap<>();
        for (final RideLeg r : carried) {
            final Double at = reached.get(r.from);
            if (at == null) {
                return null;
            }
            passAt.put(r, at);
        }
        // write the detour to the driver's plan
        final NetworkRoute route = (NetworkRoute) driver.route;
        final List<Id<Link>> inner = path.size() > 2
                ? new ArrayList<>(path.subList(1, path.size() - 1)) : new ArrayList<>();
        route.setLinkIds(driver.from, inner, driver.to);
        route.setDistance(metres);
        route.setTravelTime(clock - driver.departure);
        driver.leg.setTravelTime(clock - driver.departure);
        driver.routedBefore = driver.routedTravelTime;
        driver.routedTravelTime = clock - driver.departure;
        driver.path = path;
        return passAt;
    }

    // ---- the rules --------------------------------------------------------

    /**
     * Give back every leg the pairing forced to walk for this mobsim.
     *
     * <p>Scoring is event-driven and this runs once the mobsim has emitted its
     * events, so the agent keeps the score of the walk it actually made -
     * DECISIONS.md 9.55's price is paid in full, and the surviving ride share
     * stays emergent from the physical driver supply. What the agent does NOT
     * keep is a plan with ride amputated out of it: the mode and the route the
     * pairing set aside go back on the leg, so the alternative is still there
     * to be re-selected when the driver's selected plan serves it again.
     *
     * <p>Without this, one missed pairing deleted the alternative for good
     * while a successful pairing created nothing - a one-way ratchet that ran
     * to zero whatever the scores said. The measurement is in the re-mode
     * comment above.
     */
    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        if (!enabled()) {
            return;
        }
        // The leg object CANNOT be held across the mobsim. The re-mode nulls
        // the route so the walk is routed on the walk network, and a null route
        // is exactly what makes PersonPrepareForSim run PlanRouter over that
        // trip - and TripRouter.insertTrip REPLACES the trip's plan elements
        // with new Leg objects. A restore through the old reference therefore
        // writes to an orphan and changes nothing: measured on arm
        // 20260826T051938, whose ride-leg counts came back byte-identical to
        // the unfixed arm (87,019 / 28,228 / 25,889) while the log cheerfully
        // reported 61,409 legs "restored".
        //
        // So the leg is RE-FOUND in the selected plan by the endpoints the
        // pairing recorded, and the count logged is what was actually restored.
        // The restore replaces the whole TRIP, never one leg of it. Re-routing a
        // forced walk can yield a MULTI-LEG trip, and MATSim requires every leg
        // of a trip to carry the same routingMode: setting one leg back to ride
        // and leaving its siblings on walk killed arm 20260826T053741 at
        // iteration 1 with "Found a trip whose legs have different
        // routingModes" (agents 223559, 539119, 522667). The 1% probe had not
        // caught it because no matching agent there held a multi-leg walk trip.
        int restored = 0;
        for (final RideLeg ride : remodedThisMobsim) {
            final Person person =
                    scenario.getPopulation().getPersons().get(ride.person);
            if (person == null || person.getSelectedPlan() == null) {
                continue;
            }
            final Plan plan = person.getSelectedPlan();
            org.matsim.core.router.TripStructureUtils.Trip target = null;
            for (final org.matsim.core.router.TripStructureUtils.Trip trip
                    : org.matsim.core.router.TripStructureUtils.getTrips(plan)) {
                final Id<Link> from = trip.getOriginActivity().getLinkId();
                final Id<Link> to = trip.getDestinationActivity().getLinkId();
                if (ride.from.equals(from) && ride.to.equals(to)
                        && isAllMode(trip, remodedAs.getOrDefault(
                                ride, TransportMode.walk))) {
                    target = trip;
                    break;
                }
            }
            if (target == null) {
                continue;
            }
            final Leg leg = org.matsim.core.population.PopulationUtils
                    .createLeg(TransportMode.ride);
            leg.setRoute(ride.route);
            org.matsim.core.router.TripStructureUtils.setRoutingMode(
                    leg, TransportMode.ride);
            org.matsim.core.router.TripRouter.insertTrip(
                    plan, target.getOriginActivity(),
                    Collections.singletonList(leg),
                    target.getDestinationActivity());
            restored++;
        }
        if (!remodedThisMobsim.isEmpty()) {
            org.apache.logging.log4j.LogManager.getLogger(RidePairingEngine.class)
                    .info("ridePairing: {} of {} forced-walk leg(s) restored to "
                          + "ride after the mobsim - the walk was scored, the "
                          + "alternative kept", restored, remodedThisMobsim.size());
        }
        remodedThisMobsim.clear();
    }

    /** Every leg of the trip is a walk leg - i.e. this is a trip the pairing
     *  forced, not some other walk the agent was always going to make. */
    /**
     * The mode an unpairable ride leg is executed as this iteration.
     *
     * <p>A passenger whose lift falls through is not thereby a pedestrian. If
     * they hold a licence and a car is available to them, the household's
     * actual answer is that they drive themselves; only someone who cannot
     * drive is left walking. Under the declared `walk` member this returns
     * walk for everyone and reproduces the pre-9.105 behaviour exactly.
     *
     * <p>Stated rather than hidden: this does NOT check that the household's
     * vehicle is free at that hour, so a household with one car can in
     * principle have two members driving it. `carAvail` is a person-level
     * attribute and the finer check would need a vehicle roster the demand
     * does not carry.
     */
    private String fallbackMode(final Id<Person> person) {
        // The choice applied here is the declared registry field
        // B.ride.unpaired_fallback (9.105 - a denied lift is not a
        // fifteen-hour walk), reaching this class through
        // RidePairingConfigGroup's accessor rather than by name. The key is
        // spelled out so the registry's `consumers` claim about this file is
        // verifiable by text and not merely by intent.
        if (!RidePairingConfigGroup.FALLBACK_DRIVE_ELSE_WALK
                .equals(cfg.getUnpairedFallback())) {
            return TransportMode.walk;
        }
        return Boolean.TRUE.equals(licensed.get(person))
                && Boolean.TRUE.equals(carAvailable.get(person))
                ? TransportMode.car : TransportMode.walk;
    }

    private static boolean isAllMode(
            final org.matsim.core.router.TripStructureUtils.Trip trip,
            final String mode) {
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

    /** How many timing misses were within `minutes` of a matching driver. */
    private int gapAtMost(final double minutes) {
        int n = 0;
        for (final Double g : missGapMinutes) {
            if (g <= minutes) {
                n++;
            }
        }
        return n;
    }

    /** Median minutes off, or 0 when nothing missed on timing alone. */
    private double gapMedian() {
        if (missGapMinutes.isEmpty()) {
            return 0.0;
        }
        final List<Double> s = new ArrayList<>(missGapMinutes);
        Collections.sort(s);
        return s.get(s.size() / 2);
    }

    private static boolean endpointsMatch(final String rule, final DriverLeg driver,
                                          final RideLeg ride) {
        switch (rule) {
            case RidePairingConfigGroup.RULE_BOTH_LINKS:
                return equalId(driver.from, ride.from) && equalId(driver.to, ride.to);
            case RidePairingConfigGroup.RULE_ORIGIN_LINK:
                return equalId(driver.from, ride.from);
            case RidePairingConfigGroup.RULE_DEST_LINK:
                return equalId(driver.to, ride.to);
            case RidePairingConfigGroup.RULE_ROUTE_CONTAINS:
                // BOTH of the passenger's links on the driver's path, in the
                // order the driver drives them. Order matters: a driver who
                // passes the passenger's destination before their origin is
                // going the other way, and pairing those two would carry
                // somebody backwards.
                final int i = driver.path.indexOf(ride.from);
                final int j = driver.path.lastIndexOf(ride.to);
                return i >= 0 && j >= 0 && i <= j;
            case RidePairingConfigGroup.RULE_WINDOW_ONLY:
                return true;
            default:
                // checkConsistency has already refused anything else; reaching
                // here would mean the config group was bypassed.
                throw new IllegalStateException("unknown ridePairing.rule " + rule);
        }
    }

    /** Every link of a routed car leg, start and end included. */
    private static List<Id<Link>> drivenPath(final Route route) {
        final List<Id<Link>> path = new ArrayList<>();
        path.add(route.getStartLinkId());
        if (route instanceof NetworkRoute) {
            path.addAll(((NetworkRoute) route).getLinkIds());
        }
        final Id<Link> end = route.getEndLinkId();
        if (path.isEmpty() || !path.get(path.size() - 1).equals(end)) {
            path.add(end);
        }
        return path;
    }

    /**
     * The share of the driver's routed LENGTH that the passenger is aboard for.
     *
     * <p>A passenger dropped off en route rides part of the driver's leg, so
     * charging them the whole leg's time would make every such pairing score
     * as though they had gone all the way. Returns 1.0 when the segment is the
     * whole route, so `both_links` reproduces the previous behaviour exactly.
     */
    private double carriedShare(final DriverLeg driver, final RideLeg ride) {
        final int i = driver.path.indexOf(ride.from);
        final int j = driver.path.lastIndexOf(ride.to);
        if (i < 0 || j < 0 || j < i) {
            return 1.0;
        }
        double total = 0.0;
        double segment = 0.0;
        for (int k = 0; k < driver.path.size(); k++) {
            final Link link = scenario.getNetwork().getLinks().get(driver.path.get(k));
            final double length = link == null ? 0.0 : link.getLength();
            total += length;
            if (k >= i && k <= j) {
                segment += length;
            }
        }
        return total <= 0.0 ? 1.0 : segment / total;
    }

    private static boolean equalId(final Id<Link> a, final Id<Link> b) {
        return a != null && a.equals(b);
    }

    /**
     * The driver's realised duration for THIS leg, or NaN if the last mobsim
     * holds no counterpart for it.
     *
     * <p>Matched on the driver's own endpoints and then on the closest
     * departure, because a person may run the same origin-destination pair more
     * than once in a day and the two realisations differ by exactly the
     * congestion this class exists to transmit.
     */
    private double realisedDuration(final DriverLeg driver) {
        final List<Realised> done = previous.get(driver.person);
        if (done == null) {
            return Double.NaN;
        }
        double best = Double.NaN;
        double bestGap = Double.MAX_VALUE;
        for (final Realised r : done) {
            if (!equalId(r.from, driver.from) || !equalId(r.to, driver.to)) {
                continue;
            }
            final double gap = Math.abs(r.departure - driver.departure);
            if (gap < bestGap) {
                bestGap = gap;
                best = r.duration;
            }
        }
        return best;
    }

    /**
     * A ride leg's direction, which is what the unpaired share must be split by.
     *
     * <p>Outbound leaves home, return arrives home, and anything else is an
     * intermediate leg of a tour. Nothing about this is a place: `home` is an
     * activity type the demand builder writes, and any city has one.
     */
    private static String direction(final String before, final String after) {
        if ("home".equals(before)) {
            return "outbound";
        }
        if ("home".equals(after)) {
            return "return";
        }
        return "intermediate";
    }

    /** The next REAL activity, stepping over the router's stage activities. */
    private static String nextActivity(final List<PlanElement> elements, final int at) {
        for (int i = at + 1; i < elements.size(); i++) {
            if (elements.get(i) instanceof Activity) {
                final String type = ((Activity) elements.get(i)).getType();
                if (!StageActivityTypeIdentifier.isStageActivity(type)) {
                    return type;
                }
            }
        }
        return null;
    }

    /** Give an unpaired leg back the router's own estimate — today's behaviour. */
    private static void restore(final Leg leg, final Route route) {
        final OptionalTime baseline = leg.getTravelTime();
        if (baseline.isDefined()) {
            route.setTravelTime(baseline.seconds());
        }
    }

    private static double legDeparture(final Leg leg, final double clock) {
        final OptionalTime declared = leg.getDepartureTime();
        if (declared.isDefined()) {
            return declared.seconds();
        }
        return Double.isNaN(clock) ? 0.0 : clock;
    }

    private static double definedOr(final OptionalTime t, final double fallback) {
        return t != null && t.isDefined() ? t.seconds() : fallback;
    }

    private boolean enabled() {
        return cfg != null && cfg.isEnabled();
    }

    /** Household and licence are properties of the person, not of the iteration. */
    private void index() {
        if (indexed) {
            return;
        }
        for (final Person person : scenario.getPopulation().getPersons().values()) {
            final Object hh = person.getAttributes().getAttribute(HOUSEHOLD_ATTRIBUTE);
            if (hh != null) {
                household.put(person.getId(), hh.toString());
            }
            final Object lift = person.getAttributes()
                    .getAttribute(LIFT_HOUSEHOLD_ATTRIBUTE);
            if (lift != null) {
                liftHousehold.put(person.getId(), lift.toString());
            }
            final Object bound = person.getAttributes()
                    .getAttribute(BOUND_DRIVER_ATTRIBUTE);
            if (bound != null) {
                final Set<String> ids = new HashSet<>();
                for (final String id : bound.toString().split(",")) {
                    final String trimmed = id.trim();
                    if (!trimmed.isEmpty()) {
                        ids.add(trimmed);
                    }
                }
                if (!ids.isEmpty()) {
                    boundDriver.put(person.getId(), ids);
                }
            }
            final Object lic = person.getAttributes().getAttribute(LICENCE_ATTRIBUTE);
            licensed.put(person.getId(), lic != null && LICENCE_YES.equals(lic.toString()));
            final Object avail =
                    person.getAttributes().getAttribute(CAR_AVAIL_ATTRIBUTE);
            carAvailable.put(person.getId(),
                             avail != null
                             && !CAR_AVAIL_NEVER.equals(avail.toString()));
        }
        ordered = new ArrayList<>(scenario.getPopulation().getPersons().values());
        ordered.sort(Comparator.comparing(Person::getId));
        indexed = true;
    }

    // ---- the diagnostic ---------------------------------------------------

    private void write(final int iteration, final int rideLegs, final int nPaired,
                       final Map<String, int[]> paired, final Map<String, int[]> unpaired,
                       final int carLegs, final int fromRealised, final int fromRouted,
                       final double meanDelta, final int capacityRefusals,
                       final int households, final int noHousehold,
                       final long elapsedMs) {
        final StringBuilder b = new StringBuilder(256);
        if (!headerWritten) {
            b.append(HEADER);
            headerWritten = true;
        }
        b.append(iteration).append(',').append(rideLegs).append(',').append(nPaired)
                .append(',').append(rideLegs - nPaired).append(',')
                .append(rate(nPaired, rideLegs)).append(',')
                .append(count(paired, "outbound")).append(',')
                .append(count(paired, "return")).append(',')
                .append(count(paired, "intermediate")).append(',')
                .append(count(unpaired, "outbound")).append(',')
                .append(count(unpaired, "return")).append(',')
                .append(count(unpaired, "intermediate")).append(',')
                .append(count(paired, "outbound") + count(unpaired, "outbound")).append(',')
                .append(count(paired, "return") + count(unpaired, "return")).append(',')
                .append(count(paired, "intermediate") + count(unpaired, "intermediate"))
                .append(',').append(carLegs).append(',')
                .append(rate(nPaired, carLegs)).append(',')
                .append(fromRealised).append(',').append(fromRouted).append(',')
                .append(String.format(java.util.Locale.ROOT, "%.3f", meanDelta))
                .append(',').append(capacityRefusals).append(',').append(households)
                .append(',').append(noHousehold).append(',').append(elapsedMs)
                .append(',').append(missNoCandidate)
                .append(',').append(missWindow)
                .append(',').append(missEndpoints)
                .append(',').append(missCapacity)
                .append(',').append(pairedDeclared)
                .append(',').append(pairedByIdentity)
                .append(',').append(gapAtMost(30.0))
                .append(',').append(gapAtMost(45.0))
                .append(',').append(gapAtMost(60.0))
                .append(',').append(gapAtMost(120.0))
                .append(',').append(missGapMinutes.size() - gapAtMost(120.0))
                .append(',').append(String.format(java.util.Locale.ROOT, "%.1f",
                                                  gapMedian()))
                .append('\n');
        try {
            Files.write(Paths.get(io.getOutputFilename(OUT_FILE)),
                        b.toString().getBytes(StandardCharsets.UTF_8),
                        java.nio.file.StandardOpenOption.CREATE,
                        java.nio.file.StandardOpenOption.APPEND);
        } catch (final IOException e) {
            // An observer may never stop a run.
            writeFailures++;
        }
    }

    private static int count(final Map<String, int[]> m, final String key) {
        final int[] v = m.get(key);
        return v == null ? 0 : v[0];
    }

    private static String rate(final int n, final int of) {
        return of == 0 ? "0.0000"
                : String.format(java.util.Locale.ROOT, "%.4f", (double) n / of);
    }

    int getWriteFailures() {
        return writeFailures;
    }
}
