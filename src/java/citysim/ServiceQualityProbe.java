package citysim;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.PersonScoreEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.PersonScoreEventHandler;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.api.experimental.events.VehicleArrivesAtFacilityEvent;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.events.EventsUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitRouteStop;
import org.matsim.pt.transitSchedule.api.TransitSchedule;
import org.matsim.pt.transitSchedule.api.TransitScheduleFactory;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.vehicles.Vehicle;

/**
 * The gate on {@link ServiceQualityScoring}'s headway (9.219): the charge is
 * the service interval of the boarded LINE at the boarding STOP around the
 * boarding time, never a route variant's own departures.
 *
 * <p>The F39 probe found the class keyed on the route: the mapped schedule
 * writes one route per stop pattern, 1,080 of 1,270 routes carried a single
 * departure, and an all-day bus was charged the 1,800-minute cap. This probe
 * builds a line whose every trip is its own route variant - the shape the
 * mapper writes - and proves the charge sees the line.
 *
 * <p><b>Every number is a FIXTURE</b>: departures at 0, 600 and 1,800 s, a
 * price of 0.1 utils a minute and a cap of 1,800 minutes, chosen so each
 * interval is distinguishable. The declared prices reach the class through
 * {@link ServiceQualityConfigGroup}; this probe proves the LOOKUP.
 *
 * <p>What it checks:
 * <ul>
 * <li>three routes of one line, one departure each, index as ONE line-stop
 *     with three departures (not three single-departure routes), and the
 *     mapper's two child facilities of the one stop ({@code A.link:1},
 *     {@code A.link:2}) are that one stop;</li>
 * <li>a later stop's departures are shifted by that stop's offset;</li>
 * <li>the interval around a boarding is the mean of the gaps either side,
 *     the one gap at either end of the day, the nearest departure between
 *     two, and the cap where the line calls once;</li>
 * <li>another line at the same stop is its own line-stop;</li>
 * <li>end to end: a passenger boarding the middle trip at the first stop is
 *     charged 0.1 x 15 minutes as a negative {@link PersonScoreEvent}, the
 *     driver is not charged, and a once-a-day line is charged the cap.</li>
 * </ul>
 *
 * <p>One JSON line on stdout; exit 0 only if every asserted check holds.
 */
public final class ServiceQualityProbe {

    private static final String LINE = "L1";
    private static final String ONCE = "L2";
    private static final double[] DEPARTURES_S = {0.0, 600.0, 1800.0};
    private static final double SECOND_STOP_OFFSET_S = 120.0;
    private static final double UTILS_PER_MIN = 0.1;
    private static final double CAP_MIN = 1800.0;
    private static final double EPS = 1e-9;

    private ServiceQualityProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json = new StringBuilder("{");
        boolean ok = true;
        final Scenario scenario = scenario();
        final Map<String, double[]> index =
                ServiceQualityScoring.indexDepartures(scenario.getTransitSchedule());

        // --- 1. one line of single-departure routes is ONE line-stop -------
        final double[] atA = index.get(ServiceQualityScoring.stopKey(LINE, "A"));
        final boolean oneLineStop = atA != null && atA.length == 3
                && eq(atA[0], 0.0) && eq(atA[1], 600.0) && eq(atA[2], 1800.0);
        ok &= oneLineStop;
        json.append("\"line_stop_departures\":").append(atA == null ? 0 : atA.length)
            .append(",\"variants_of_one_line_index_as_one_line_stop\":")
            .append(oneLineStop);

        // --- 2. a later stop carries its offset ----------------------------
        final double[] atB = index.get(ServiceQualityScoring.stopKey(LINE, "B"));
        final boolean offset = atB != null && atB.length == 3
                && eq(atB[1], 600.0 + SECOND_STOP_OFFSET_S);
        ok &= offset;
        json.append(",\"stop_offset_applied\":").append(offset);

        // --- 3. the interval around a boarding -----------------------------
        final double mid = ServiceQualityScoring.headwayAt(atA, 600.0, CAP_MIN);
        final double first = ServiceQualityScoring.headwayAt(atA, 0.0, CAP_MIN);
        final double last = ServiceQualityScoring.headwayAt(atA, 1800.0, CAP_MIN);
        final double near = ServiceQualityScoring.headwayAt(atA, 650.0, CAP_MIN);
        final double[] onceAtA = index.get(ServiceQualityScoring.stopKey(ONCE, "A"));
        final double once = ServiceQualityScoring.headwayAt(onceAtA, 600.0, CAP_MIN);
        final boolean intervals = eq(mid, 15.0) && eq(first, 10.0) && eq(last, 20.0)
                && eq(near, 15.0) && eq(once, CAP_MIN);
        ok &= intervals;
        json.append(",\"headway_min_mid_first_last_near_once\":[").append(mid)
            .append(',').append(first).append(',').append(last)
            .append(',').append(near).append(',').append(once)
            .append("],\"interval_around_the_boarding\":").append(intervals);

        // --- 4. another line at the same stop is its own line-stop ---------
        final boolean separate = onceAtA != null && onceAtA.length == 1;
        ok &= separate;
        json.append(",\"another_line_is_its_own_line_stop\":").append(separate);

        // --- 5. end to end through the events ------------------------------
        final EventsManager events = EventsUtils.createEventsManager();
        final List<PersonScoreEvent> scored = new ArrayList<>();
        events.addHandler((PersonScoreEventHandler) scored::add);
        events.initProcessing();
        final ServiceQualityScoring handler =
                new ServiceQualityScoring(scenario.getConfig(), scenario, events);
        board(handler, "v_mid", LINE, "r2", "d_mid", "p_mid", 600.0);
        board(handler, "v_once", ONCE, "r_once", "d_once", "p_once", 600.0);
        handler.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        events.finishProcessing();
        final double pMid = charged(scored, "p_mid");
        final double pOnce = charged(scored, "p_once");
        final boolean driverFree = charged(scored, "d_mid") == 0.0;
        final boolean endToEnd = eq(pMid, -UTILS_PER_MIN * 15.0)
                && eq(pOnce, -UTILS_PER_MIN * CAP_MIN) && driverFree;
        ok &= endToEnd;
        json.append(",\"score_mid_once\":[").append(pMid).append(',').append(pOnce)
            .append("],\"driver_not_charged\":").append(driverFree)
            .append(",\"boarding_charged_the_line_interval\":").append(endToEnd);

        // --- 6. ATAP M1's function (9.219) ----------------------------------
        // The coefficients below are ATAP's published ones, set as fixtures;
        // the report's own check values are SI/IVT 0.8 at 10 minutes and 0.44
        // hourly (equation 4.3.2), and a once-a-day interval is 1.4 x 20 + 180.
        final ServiceQualityConfigGroup atapCfg = atap(scenario.getConfig());
        final double at10 = ServiceQualityScoring.atapIvtMinutes(10.0, atapCfg);
        final double at60 = ServiceQualityScoring.atapIvtMinutes(60.0, atapCfg);
        final double atDay = ServiceQualityScoring.atapIvtMinutes(CAP_MIN, atapCfg);
        final boolean atapShape = eq(at10 / 10.0, 0.8)
                && Math.abs(at60 / 60.0 - 0.44) < 0.005 && eq(atDay, 208.0);
        ok &= atapShape;
        json.append(",\"atap_ivt_min_10_60_day\":[").append(at10).append(',')
            .append(at60).append(',').append(atDay)
            .append("],\"atap_reproduces_the_report\":").append(atapShape);

        final EventsManager atapEvents = EventsUtils.createEventsManager();
        final List<PersonScoreEvent> atapScored = new ArrayList<>();
        atapEvents.addHandler((PersonScoreEventHandler) atapScored::add);
        atapEvents.initProcessing();
        final ServiceQualityScoring atapHandler =
                new ServiceQualityScoring(scenario.getConfig(), scenario, atapEvents);
        board(atapHandler, "v_mid", LINE, "r2", "d_mid", "p_mid", 600.0);
        board(atapHandler, "v_once", ONCE, "r_once", "d_once", "p_once", 600.0);
        atapHandler.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
        atapEvents.finishProcessing();
        final double aMid = charged(atapScored, "p_mid");
        final double aOnce = charged(atapScored, "p_once");
        final double want15 = -UTILS_PER_MIN
                * ServiceQualityScoring.atapIvtMinutes(15.0, atapCfg);
        final boolean atapEndToEnd = Math.abs(aMid - want15) < 1e-5
                && eq(aOnce, -UTILS_PER_MIN * 208.0);
        ok &= atapEndToEnd;
        json.append(",\"atap_score_mid_once\":[").append(aMid).append(',').append(aOnce)
            .append("],\"atap_boarding_charged\":").append(atapEndToEnd);

        // a function switched on without its coefficients is refused
        atapCfg.atapWaitCapMin = Double.NaN;
        boolean refused = false;
        try {
            atapCfg.checkConsistency(scenario.getConfig());
        } catch (final IllegalStateException e) {
            refused = e.getMessage().contains("atapWaitCapMin");
        }
        ok &= refused;
        json.append(",\"atap_without_coefficients_refused\":").append(refused);

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    private static void board(final ServiceQualityScoring h, final String vehicle,
                              final String line, final String route,
                              final String driver, final String person,
                              final double timeS) {
        final Id<Vehicle> v = Id.create(vehicle, Vehicle.class);
        h.handleEvent(new TransitDriverStartsEvent(timeS - 60.0,
                Id.createPersonId(driver), v, Id.create(line, TransitLine.class),
                Id.create(route, TransitRoute.class),
                Id.create(route + "_dep", Departure.class)));
        h.handleEvent(new PersonEntersVehicleEvent(timeS - 60.0,
                Id.createPersonId(driver), v));
        h.handleEvent(new VehicleArrivesAtFacilityEvent(timeS - 5.0, v,
                Id.create("A.link:2", TransitStopFacility.class), 0.0));
        h.handleEvent(new PersonEntersVehicleEvent(timeS,
                Id.createPersonId(person), v));
    }

    /** Switch the probe's config group to ATAP M1 with ATAP's published values. */
    private static ServiceQualityConfigGroup atap(final Config config) {
        final ServiceQualityConfigGroup sq =
                ConfigUtils.addOrGetModule(config, ServiceQualityConfigGroup.class);
        sq.intervalFunction = ServiceQualityConfigGroup.FUNCTION_ATAP_M1;
        sq.ivtUtilsPerMin = UTILS_PER_MIN;
        sq.atapWaitWeight = 1.4;
        sq.atapDisplacementWeight = 0.1;
        sq.atapWaitHalf = 0.5;
        sq.atapWaitSqrtMin = 1.88;
        sq.atapWaitCapMin = 20.0;
        return sq;
    }

    private static double charged(final List<PersonScoreEvent> scored,
                                  final String person) {
        double sum = 0.0;
        for (final PersonScoreEvent e : scored) {
            if (e.getPersonId().toString().equals(person)) {
                sum += e.getAmount();
            }
        }
        return Math.round(sum * 1e6) / 1e6;
    }

    /** Line L1: three routes of stops A-B, one departure each; L2: once, at A. */
    private static Scenario scenario() {
        final Config config = ConfigUtils.createConfig();
        config.transit().setUseTransit(true);
        final ServiceQualityConfigGroup sq =
                ConfigUtils.addOrGetModule(config, ServiceQualityConfigGroup.class);
        sq.representation = ServiceQualityConfigGroup.REPRESENTATION_HEADWAY;
        sq.headwayUtilsPerMin = UTILS_PER_MIN;
        sq.reliabilityUtilsPerMin = 0.0;
        sq.headwayCapMin = CAP_MIN;
        final Scenario scenario = ScenarioUtils.createScenario(config);
        final TransitSchedule schedule = scenario.getTransitSchedule();
        final TransitScheduleFactory f = schedule.getFactory();
        // stop A as the mapper writes it: one child facility per link it was
        // mapped to, the first trip on link 1 and the others on link 2
        final TransitStopFacility a = f.createTransitStopFacility(
                Id.create("A.link:1", TransitStopFacility.class), new Coord(0.0, 0.0), false);
        final TransitStopFacility a2 = f.createTransitStopFacility(
                Id.create("A.link:2", TransitStopFacility.class), new Coord(0.0, 0.0), false);
        final TransitStopFacility b = f.createTransitStopFacility(
                Id.create("B", TransitStopFacility.class), new Coord(1000.0, 0.0), false);
        schedule.addStopFacility(a);
        schedule.addStopFacility(a2);
        schedule.addStopFacility(b);
        final TransitLine line = f.createTransitLine(Id.create(LINE, TransitLine.class));
        for (int i = 0; i < DEPARTURES_S.length; i++) {
            final List<TransitRouteStop> stops = new ArrayList<>();
            stops.add(f.createTransitRouteStop(i == 0 ? a : a2, 0.0, 0.0));
            stops.add(f.createTransitRouteStop(b, SECOND_STOP_OFFSET_S,
                                               SECOND_STOP_OFFSET_S));
            final TransitRoute route = f.createTransitRoute(
                    Id.create("r" + (i + 1), TransitRoute.class), null, stops, "bus");
            route.addDeparture(f.createDeparture(
                    Id.create("r" + (i + 1) + "_dep", Departure.class), DEPARTURES_S[i]));
            line.addRoute(route);
        }
        schedule.addTransitLine(line);
        final TransitLine onceLine =
                f.createTransitLine(Id.create(ONCE, TransitLine.class));
        final List<TransitRouteStop> onceStops = new ArrayList<>();
        onceStops.add(f.createTransitRouteStop(a2, 0.0, 0.0));
        onceStops.add(f.createTransitRouteStop(b, SECOND_STOP_OFFSET_S,
                                               SECOND_STOP_OFFSET_S));
        final TransitRoute onceRoute = f.createTransitRoute(
                Id.create("r_once", TransitRoute.class), null, onceStops, "bus");
        onceRoute.addDeparture(f.createDeparture(
                Id.create("r_once_dep", Departure.class), 600.0));
        onceLine.addRoute(onceRoute);
        schedule.addTransitLine(onceLine);
        return scenario;
    }

    private static boolean eq(final double a, final double b) {
        return Math.abs(a - b) < EPS;
    }
}
