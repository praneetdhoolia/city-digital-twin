package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.PersonScoreEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.PersonEntersVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.TransitDriverStartsEventHandler;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.api.experimental.events.VehicleArrivesAtFacilityEvent;
import org.matsim.core.api.experimental.events.handler.VehicleArrivesAtFacilityEventHandler;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.core.utils.misc.OptionalTime;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitRouteStop;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.vehicles.Vehicle;

/**
 * Charges a boarding passenger for the SERVICE INTERVAL of the route they
 * boarded and for how VARIABLE that route ran, as a
 * {@link PersonScoreEvent}.
 *
 * <p>The why, the identity chain and the two literature definitions are in
 * {@link ServiceQualityConfigGroup}. This class is the mechanism, and it holds
 * no number of its own: both prices arrive as derived config values and the
 * standard deviation is measured from the run's own events.
 *
 * <h2>The headway a passenger boards on</h2>
 *
 * <p>The service interval IN FORCE AT THE BOARDING STOP WHEN THE PASSENGER
 * BOARDS: the departures of every {@link TransitRoute} of the boarded
 * {@link TransitLine} that call at that stop (the mapper's child facilities of
 * one source stop are that one stop: {@link #parentStop}), sorted, and the mean of the gap
 * before and the gap after the boarded one (the one gap there is at the
 * first or last departure of the day). A stop the line calls at once a day
 * has no gap to measure, and the honest reading is that its interval is the
 * whole service day — it is charged {@code serviceQuality.headwayCapMin},
 * derived from {@code RUN.qsim.end_time_h} rather than typed here, and the
 * count of such stops is logged.
 *
 * <p><b>Why the line at the stop and not the route (9.219).</b> The mapped
 * schedule writes one {@code TransitRoute} per stop pattern, and on the F39
 * build 1,080 of 1,270 routes carried a single departure; a charge keyed on
 * the route priced an all-day bus as a once-a-day service. A passenger can
 * board any trip of the line that calls where they stand, so that is the
 * service they face, and the gap around their own departure is PDFH's
 * interval by time of day rather than a daily mean that gives a 22:00
 * boarding the peak's frequency.
 *
 * <h2>The variability of a route</h2>
 *
 * <p>The population standard deviation of
 * {@link VehicleArrivesAtFacilityEvent#getDelay()} over every stop arrival the
 * route made in the PREVIOUS mobsim. Delay is the deviation from the mapped
 * timetable, in seconds, produced by the mobsim itself — a bus held on a
 * shared carriageway accumulates it and a tram on its own alignment does not.
 *
 * <p><b>The first scored iteration carries no reliability charge and says
 * so.</b> There is no previous mobsim to measure, and a seeded standard
 * deviation would be an invented observation. It is reported in the log rather
 * than back-filled.
 *
 * <h2>What is deliberately not charged</h2>
 *
 * <p>The DRIVER is not a passenger and is excluded by identity, exactly as in
 * {@code citysim.PtCrowdingScoring}: a person entering a vehicle this class
 * has no open service for, or who is that service's own driver, is skipped.
 * A non-transit vehicle never appears here at all, because the only way a
 * vehicle enters {@link #inService} is a {@link TransitDriverStartsEvent}.
 */
public final class ServiceQualityScoring implements TransitDriverStartsEventHandler,
        PersonEntersVehicleEventHandler, VehicleArrivesAtFacilityEventHandler,
        AfterMobsimListener {

    private static final Logger LOG =
            LogManager.getLogger(ServiceQualityScoring.class);

    /** Kind string carried on every emitted PersonScoreEvent. */
    public static final String KIND = "serviceQuality";

    private static final double SECONDS_PER_MINUTE = 60.0;

    private final EventsManager events;
    private final double headwayUtilsPerMin;
    private final double reliabilityUtilsPerMin;
    private final boolean reliability;
    /** ATAP M1 (9.219): the whole config group, read only when {@link #atap}. */
    private final boolean atap;
    private final ServiceQualityConfigGroup cfg;

    /** stopKey (line at a stop) -> its departures in seconds, sorted, once. */
    private final Map<String, double[]> departuresAtStop = new HashMap<>();
    /**
     * The same arrays reached by the ids the events carry, with no string
     * built on the way: line -> child facility -> the (line, parent stop)
     * departures. Resolved ONCE per vehicle arrival ({@link Service#departures})
     * rather than once per boarding, which concatenated a key String for
     * every passenger entering a transit vehicle (sixteenth report).
     */
    private final Map<Id<TransitLine>, Map<Id<TransitStopFacility>, double[]>>
            departuresByFacility;
    private final double capMin;
    /** The mobsim's end time, the clock every afterMobsim charge is stamped
     *  with - as {@code PtUnservedScoring} stamps its own. */
    private final Config config;
    /** vehicle in service -> (line, routeKey, driver, the departures at the
     *  stop it is standing at). */
    private static final class Service {
        private final Id<TransitLine> line;
        private final String routeKey;
        private final Id<Person> driver;
        /** The boarded line's departures at the stop the vehicle last
         *  arrived at; null until its first arrival, or at a stop the
         *  schedule does not list for the line. */
        private double[] departures;

        private Service(final Id<TransitLine> line, final String routeKey,
                        final Id<Person> driver) {
            this.line = line;
            this.routeKey = routeKey;
            this.driver = driver;
        }
    }

    private final Map<Id<Vehicle>, Service> inService = new HashMap<>();
    /** routeKey -> this mobsim's stop-arrival delays, in seconds. */
    private final Map<String, List<Double>> delays = new HashMap<>();
    /** routeKey -> sd of delay in minutes, MEASURED IN THE PREVIOUS mobsim. */
    private final Map<String, Double> sdMin = new HashMap<>();
    /** Charge accrued this mobsim, emitted at afterMobsim. */
    private final Map<Id<Person>, Double> charge = new HashMap<>();

    private boolean firstMobsim = true;
    private long boardings;
    private long boardingsWithoutRoute;
    private long boardingsAtCap;
    private double headwayMinSum;

    @Inject
    public ServiceQualityScoring(final Config config, final Scenario scenario,
                                 final EventsManager events) {
        final ServiceQualityConfigGroup cfg =
                ConfigUtils.addOrGetModule(config, ServiceQualityConfigGroup.class);
        this.events = events;
        this.headwayUtilsPerMin = cfg.getHeadwayUtilsPerMin();
        this.reliabilityUtilsPerMin = cfg.getReliabilityUtilsPerMin();
        this.reliability = cfg.isReliability();
        this.atap = cfg.isAtap();
        this.cfg = cfg;
        this.config = config;
        this.capMin = cfg.getHeadwayCapMin();
        this.departuresAtStop.putAll(indexDepartures(scenario.getTransitSchedule()));
        this.departuresByFacility =
                indexByFacility(scenario.getTransitSchedule(), this.departuresAtStop);
        int once = 0;
        final TreeMap<String, Integer> routesBySubmode = new TreeMap<>();
        for (final TransitLine line
                : scenario.getTransitSchedule().getTransitLines().values()) {
            for (final TransitRoute route : line.getRoutes().values()) {
                routesBySubmode.merge(String.valueOf(route.getTransportMode()), 1,
                                      Integer::sum);
            }
        }
        for (final double[] t : this.departuresAtStop.values()) {
            if (t.length <= 1) {
                once++;
            }
        }
        LOG.info("serviceQuality: departures indexed for {} line-stop(s) over "
                 + "route(s) {} - {} line-stop(s) are called at once a day and "
                 + "are charged the {} min cap derived from RUN.qsim.end_time_h",
                 this.departuresAtStop.size(), routesBySubmode, once, this.capMin);
    }

    static String routeKey(final Id<TransitLine> line, final Id<TransitRoute> route) {
        return line + " " + route;
    }

    /**
     * pt2matsim's {@code PublicTransitMappingStrings.SUFFIX_CHILD_STOP_FACILITIES}
     * (26.6, read from the pinned jar): the mapper writes one child facility
     * per source stop per link it maps that stop to, named
     * {@code <stop><suffix><link>}. Two trips of one line that the mapper put
     * on different links stand at the SAME stop, so the key is the parent.
     * The station-level {@code stopAreaId} is not used: it groups both
     * directions' platforms and would halve every interval (9.219).
     */
    static final String CHILD_STOP_SUFFIX = ".link:";

    static String parentStop(final String facility) {
        final int at = facility.indexOf(CHILD_STOP_SUFFIX);
        return at < 0 ? facility : facility.substring(0, at);
    }

    static String stopKey(final String line, final String stop) {
        return line + " " + parentStop(stop);
    }

    /**
     * Every line's departures at every stop it calls at, over all of the
     * line's routes: a departure's time at a stop is the route departure plus
     * that stop's departure offset (its arrival offset where the departure
     * offset is undefined). Sorted ascending.
     */
    static Map<String, double[]> indexDepartures(final TransitSchedule schedule) {
        final Map<String, List<Double>> times = new HashMap<>();
        for (final TransitLine line : schedule.getTransitLines().values()) {
            for (final TransitRoute route : line.getRoutes().values()) {
                for (final TransitRouteStop stop : route.getStops()) {
                    final OptionalTime off = stop.getDepartureOffset().isDefined()
                            ? stop.getDepartureOffset() : stop.getArrivalOffset();
                    final double offset = off.isDefined() ? off.seconds() : 0.0;
                    final List<Double> at = times.computeIfAbsent(
                            stopKey(line.getId().toString(),
                                    stop.getStopFacility().getId().toString()),
                            k -> new ArrayList<>());
                    for (final Departure dep : route.getDepartures().values()) {
                        at.add(dep.getDepartureTime() + offset);
                    }
                }
            }
        }
        final Map<String, double[]> out = new HashMap<>();
        for (final Map.Entry<String, List<Double>> e : times.entrySet()) {
            final double[] t = new double[e.getValue().size()];
            for (int i = 0; i < t.length; i++) {
                t[i] = e.getValue().get(i);
            }
            Arrays.sort(t);
            out.put(e.getKey(), t);
        }
        return out;
    }

    /**
     * {@link #indexDepartures}'s arrays, reachable by the ids an event carries.
     * For every line, every child facility of every parent stop the line calls
     * at maps to that line-stop's array - EVERY child of the parent, not only
     * the ones the line's routes list, so the answer is exactly what
     * {@code departuresAtStop.get(stopKey(line, facility))} gave for any
     * facility of the schedule, with no String built per lookup.
     */
    static Map<Id<TransitLine>, Map<Id<TransitStopFacility>, double[]>> indexByFacility(
            final TransitSchedule schedule, final Map<String, double[]> atStop) {
        final Map<String, List<Id<TransitStopFacility>>> childrenOf = new HashMap<>();
        for (final Id<TransitStopFacility> facility : schedule.getFacilities().keySet()) {
            childrenOf.computeIfAbsent(parentStop(facility.toString()),
                                       k -> new ArrayList<>()).add(facility);
        }
        final Map<Id<TransitLine>, Map<Id<TransitStopFacility>, double[]>> out =
                new HashMap<>();
        for (final TransitLine line : schedule.getTransitLines().values()) {
            final Map<Id<TransitStopFacility>, double[]> byFacility =
                    out.computeIfAbsent(line.getId(), k -> new HashMap<>());
            for (final TransitRoute route : line.getRoutes().values()) {
                for (final TransitRouteStop stop : route.getStops()) {
                    final String facility = stop.getStopFacility().getId().toString();
                    final double[] departures =
                            atStop.get(stopKey(line.getId().toString(), facility));
                    if (departures == null) {
                        continue;
                    }
                    for (final Id<TransitStopFacility> child
                            : childrenOf.getOrDefault(parentStop(facility),
                                                      List.of())) {
                        byFacility.put(child, departures);
                    }
                }
            }
        }
        return out;
    }

    /**
     * ATAP M1's valuation of a service interval of {@code siMin} minutes, in
     * equivalent in-vehicle minutes (Supporting Technical Report section 4.3,
     * equation 4.3.2, 9.219): the expected wait - the least of the random-arrival
     * half, the estimated square-root term and the ceiling (equation 4.1) - at
     * the wait weight, plus every minute of the interval as timetable
     * displacement. Every coefficient is the config group's, from the registry.
     */
    static double atapIvtMinutes(final double siMin, final ServiceQualityConfigGroup c) {
        final double wait = Math.min(Math.min(c.atapWaitHalf * siMin,
                                              c.atapWaitSqrtMin * Math.sqrt(siMin)),
                                     c.atapWaitCapMin);
        return c.atapWaitWeight * wait + c.atapDisplacementWeight * siMin;
    }

    /**
     * The service interval in minutes around a boarding at {@code timeS}: the
     * mean of the gap before and the gap after the departure nearest that
     * time, the one gap there is at either end of the day, and {@code capMin}
     * where the line calls at the stop once. Never above {@code capMin}.
     */
    static double headwayAt(final double[] departures, final double timeS,
                            final double capMin) {
        if (departures == null || departures.length <= 1) {
            return capMin;
        }
        int i = Arrays.binarySearch(departures, timeS);
        if (i < 0) {
            final int ins = -i - 1;      // first departure after timeS
            if (ins == 0) {
                i = 0;
            } else if (ins == departures.length) {
                i = departures.length - 1;
            } else {
                i = timeS - departures[ins - 1] <= departures[ins] - timeS
                        ? ins - 1 : ins;
            }
        }
        double sumS = 0.0;
        int gaps = 0;
        if (i > 0) {
            sumS += departures[i] - departures[i - 1];
            gaps++;
        }
        if (i < departures.length - 1) {
            sumS += departures[i + 1] - departures[i];
            gaps++;
        }
        return Math.min(capMin, sumS / gaps / SECONDS_PER_MINUTE);
    }

    // -- events ------------------------------------------------------------
    @Override
    public void handleEvent(final TransitDriverStartsEvent event) {
        this.inService.put(event.getVehicleId(),
                           new Service(event.getTransitLineId(),
                                       routeKey(event.getTransitLineId(),
                                                event.getTransitRouteId()),
                                       event.getDriverId()));
    }

    @Override
    public void handleEvent(final VehicleArrivesAtFacilityEvent event) {
        final Service service = this.inService.get(event.getVehicleId());
        if (service == null) {
            return;
        }
        // The line's departures at THIS stop, resolved once for every
        // passenger who boards here; null where the schedule lists no such
        // line-stop, which the boarding counts rather than prices at zero.
        final Map<Id<TransitStopFacility>, double[]> atLine =
                this.departuresByFacility.get(service.line);
        service.departures = atLine == null ? null : atLine.get(event.getFacilityId());
        this.delays.computeIfAbsent(service.routeKey, k -> new ArrayList<>())
                .add(event.getDelay());
    }

    @Override
    public void handleEvent(final PersonEntersVehicleEvent event) {
        final Service service = this.inService.get(event.getVehicleId());
        if (service == null || event.getPersonId().equals(service.driver)) {
            return;                      // not a transit passenger
        }
        this.boardings++;
        final double[] departures = service.departures;
        if (departures == null) {
            // A boarding before the vehicle reached a stop, or at a stop the
            // schedule does not list for its line. Neither can happen while
            // the mobsim serves the schedule this class indexed, so it is
            // counted and reported rather than silently priced at zero.
            this.boardingsWithoutRoute++;
            return;
        }
        final double h = headwayAt(departures, event.getTime(), this.capMin);
        if (h >= this.capMin) {
            this.boardingsAtCap++;
        }
        this.headwayMinSum += h;
        double utils = this.atap
                ? this.cfg.ivtUtilsPerMin * atapIvtMinutes(h, this.cfg)
                : this.headwayUtilsPerMin * h;
        if (this.reliability) {
            final Double sd = this.sdMin.get(service.routeKey);
            if (sd != null) {
                utils += this.reliabilityUtilsPerMin * sd;
            }
        }
        if (utils > 0.0) {
            this.charge.merge(event.getPersonId(), utils, Double::sum);
        }
    }

    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        final long started = System.currentTimeMillis();
        // Stamped at the mobsim's end (qsim.endTime, RUN.qsim.end_time_h), as
        // PtUnservedScoring stamps its own afterMobsim charge: the charge is
        // for the day's boardings as a whole, and an events file that carried
        // it should place it at the day's end, not at the iteration INDEX it
        // was stamped with until the sixteenth report (a time of 231 s on
        // iteration 231). The score is additive and unchanged by the stamp.
        final double time = this.config.qsim().getEndTime().orElse(0.0);
        for (final Map.Entry<Id<Person>, Double> e : this.charge.entrySet()) {
            this.events.processEvent(new PersonScoreEvent(
                    time, e.getKey(), -e.getValue(), KIND));
        }
        // Roll this mobsim's measured spread forward as NEXT iteration's
        // reliability. Measured, never seeded: see the class comment.
        double worst = 0.0;
        String worstRoute = null;
        this.sdMin.clear();
        for (final Map.Entry<String, List<Double>> e : this.delays.entrySet()) {
            final List<Double> d = e.getValue();
            if (d.size() < 2) {
                continue;
            }
            double mean = 0.0;
            for (final double v : d) {
                mean += v;
            }
            mean /= d.size();
            double var = 0.0;
            for (final double v : d) {
                var += (v - mean) * (v - mean);
            }
            final double sd = Math.sqrt(var / d.size()) / SECONDS_PER_MINUTE;
            this.sdMin.put(e.getKey(), sd);
            if (sd > worst) {
                worst = sd;
                worstRoute = e.getKey();
            }
        }
        final long priced = this.boardings - this.boardingsWithoutRoute;
        LOG.info("serviceQuality: it.{} charged {} passenger(s) over {} boarding(s) "
                 + "at a mean headway of {} min ({} at the {} min cap); "
                 + "{} boarding(s) had no indexed line-stop; reliability {}; "
                 + "worst measured sd {} min on {} - carried into the next iteration",
                 event.getIteration(), this.charge.size(), this.boardings,
                 String.format("%.2f", priced > 0 ? this.headwayMinSum / priced : 0.0),
                 this.boardingsAtCap, this.capMin,
                 this.boardingsWithoutRoute,
                 !this.reliability ? "not represented"
                         : this.firstMobsim
                                 ? "ZERO this iteration - no previous mobsim to "
                                   + "measure, and a seeded standard deviation "
                                   + "would be an invented observation"
                                 : "measured from the previous mobsim",
                 String.format("%.3f", worst),
                 worstRoute == null ? "-" : worstRoute.replace(' ', '/'));
        this.firstMobsim = false;
        this.charge.clear();
        this.delays.clear();
        this.inService.clear();
        this.boardings = 0;
        this.boardingsWithoutRoute = 0;
        this.boardingsAtCap = 0;
        this.headwayMinSum = 0.0;
        // One line per listener per iteration, in the one shape every citysim
        // listener logs it, so the performance lane can attribute a phase's
        // time from matsim.log alone (sixteenth report).
        LOG.info("serviceQuality: it.{} afterMobsim listener=ServiceQualityScoring ms={}",
                 event.getIteration(), System.currentTimeMillis() - started);
    }

    @Override
    public void reset(final int iteration) {
        // The per-mobsim state is cleared at afterMobsim, where the carried
        // standard deviation is computed from it. Clearing it here as well
        // would discard the measurement before it was taken.
    }
}
