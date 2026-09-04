package citysim;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.ActivityStartEvent;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.PersonLeavesVehicleEvent;
import org.matsim.api.core.v01.events.PersonMoneyEvent;
import org.matsim.api.core.v01.events.handler.PersonMoneyEventHandler;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Population;
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
 * The gate on {@link PtFareChargeHandler} (issue #133, candidate 9): the
 * distance band a journey falls in, the rider class the person's own age
 * attribute puts them in, and the daily cap arithmetic that closes the day.
 *
 * <p>No mobsim and no schedule file: the probe builds a scenario in memory
 * with three stops on a straight line, one bus route and one vehicle, then
 * feeds the handler the exact event sequence a journey produces - the vehicle
 * arrives at the boarding stop, the person enters, the vehicle arrives at the
 * alighting stop, the person leaves, the person starts a real activity - and
 * reads the {@link PersonMoneyEvent}s it emits at {@code afterMobsim}.
 *
 * <p><b>Every number below is a FIXTURE</b>, not the published schedule: bands
 * at 5 and 10 km with fares 2/4/7 (adult, off-peak) chosen so each band's
 * fare is distinguishable and the cap arithmetic lands on a round number.
 * The published values live in the registry and reach the handler through
 * {@link PtFareConfigGroup}; this probe proves the LOOKUP, never a value.
 *
 * <p>What it checks:
 * <ul>
 * <li>band lookup: 3 km takes the first band, 7 km the second, 12 km the open
 *     last band, and a distance exactly on a band's upper bound takes that
 *     band (the bound is inclusive);</li>
 * <li>the peak table is read for a peak tap-on and the off-peak table
 *     otherwise;</li>
 * <li>rider class from the person's own {@code age} attribute: below
 *     {@code childMinAge} nothing is charged, a child pays the child column;</li>
 * <li>daily cap arithmetic: a journey is charged only up to what is left of
 *     the person's cap, the cap is never exceeded, and once it is reached no
 *     further money event is emitted at all.</li>
 * </ul>
 *
 * <p><b>Reported, not asserted:</b> the handler reads the age attribute as
 * {@code instanceof Integer}, while {@link AvailabilityModesCalculator} reads
 * the same attribute as {@code instanceof Number}. A {@code Long} age
 * therefore falls through to the Adult table instead of the Child one, and
 * the probe prints what it measured rather than claiming a verdict: the
 * committed population writes {@code class="java.lang.Integer"}, so this is a
 * latent divergence between two readers of one attribute, not a live defect,
 * and the probe records it where the next session will see it.
 *
 * <p>One JSON line on stdout; exit 0 only if every asserted check holds.
 */
public final class PtFareProbe {

    /** Fixture fare table - see the class comment: not a published value. */
    private static final String BANDS_KM = "5,10";
    private static final String ADULT_OFFPEAK = "2.00,4.00,7.00";
    private static final String ADULT_PEAK = "3.00,5.00,9.00";
    private static final String CHILD_OFFPEAK = "1.00,2.00,3.50";
    private static final String CHILD_PEAK = "1.50,2.50,4.50";
    private static final double CAP_ADULT = 10.00;
    private static final double CAP_CHILD = 5.00;
    private static final double CAP_SENIOR = 2.50;

    private static final String BUS = "bus";
    private static final Id<Vehicle> VEHICLE = Id.create("v1", Vehicle.class);

    /** Stop -> its position on the straight line, in metres from the origin. */
    private static final int[] STOP_M = {0, 3000, 5000, 7000, 12000};

    private static final double OFF_PEAK_H = 10.0;
    private static final double PEAK_H = 8.0;
    private static final double EPS = 1e-9;

    private PtFareProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json = new StringBuilder("{");
        boolean ok = true;

        // --- 1. band lookup, adult, off-peak -----------------------------
        final Fixture band = new Fixture();
        band.journey("p_3km", 25, 0, 1, OFF_PEAK_H);
        band.journey("p_7km", 25, 0, 3, OFF_PEAK_H);
        band.journey("p_12km", 25, 0, 4, OFF_PEAK_H);
        band.journey("p_5km", 25, 0, 2, OFF_PEAK_H);
        band.flush();
        final boolean bands = eq(band.charged("p_3km"), 2.00)
                && eq(band.charged("p_7km"), 4.00)
                && eq(band.charged("p_12km"), 7.00)
                && eq(band.charged("p_5km"), 2.00);
        ok &= bands;
        json.append("\"band_km_3_7_12_5\":[").append(band.charged("p_3km"))
            .append(',').append(band.charged("p_7km"))
            .append(',').append(band.charged("p_12km"))
            .append(',').append(band.charged("p_5km"))
            .append("],\"bands_and_inclusive_upper_bound\":").append(bands);

        // --- 2. the peak table for a peak tap-on -------------------------
        final Fixture peak = new Fixture();
        peak.journey("p_peak", 25, 0, 3, PEAK_H);
        peak.journey("p_offpeak", 25, 0, 3, OFF_PEAK_H);
        peak.flush();
        final boolean peakTable = eq(peak.charged("p_peak"), 5.00)
                && eq(peak.charged("p_offpeak"), 4.00);
        ok &= peakTable;
        json.append(",\"peak_fare\":").append(peak.charged("p_peak"))
            .append(",\"offpeak_fare\":").append(peak.charged("p_offpeak"))
            .append(",\"peak_table_read_on_a_peak_tap_on\":").append(peakTable);

        // --- 3. rider class from the age attribute -----------------------
        final Fixture rider = new Fixture();
        rider.journey("p_child", 10, 0, 3, OFF_PEAK_H);
        rider.journey("p_infant", 3, 0, 3, OFF_PEAK_H);
        rider.journey("p_no_age", null, 0, 3, OFF_PEAK_H);
        rider.journeyLongAge("p_long_child", 10L, 0, 3, OFF_PEAK_H);
        rider.flush();
        final boolean child = eq(rider.charged("p_child"), 2.00);
        final boolean infantFree = rider.count("p_infant") == 0;
        final boolean noAgeIsAdult = eq(rider.charged("p_no_age"), 4.00);
        ok &= child && infantFree && noAgeIsAdult;
        json.append(",\"child_fare\":").append(rider.charged("p_child"))
            .append(",\"child_pays_the_child_column\":").append(child)
            .append(",\"below_child_min_age_is_free\":").append(infantFree)
            .append(",\"no_age_attribute_is_adult\":").append(noAgeIsAdult);

        // reported, not asserted - see the class comment
        final double longAge = rider.charged("p_long_child");
        final boolean longAgeReadsAdult = eq(longAge, 4.00);
        json.append(",\"long_age_fare\":").append(longAge)
            .append(",\"long_age_reads_adult\":").append(longAgeReadsAdult);
        if (longAgeReadsAdult) {
            System.err.println("REPORTED, not a probe failure: a Long `age` "
                    + "attribute is charged the ADULT fare (" + longAge
                    + ") where an Integer age of the same value is charged the "
                    + "child fare (" + rider.charged("p_child") + "). "
                    + "PtFareChargeHandler reads the attribute as `instanceof "
                    + "Integer`; AvailabilityModesCalculator reads the same "
                    + "attribute as `instanceof Number`. The committed "
                    + "population writes class=\"java.lang.Integer\", so this "
                    + "is a latent divergence between two readers of one "
                    + "attribute.");
        }

        // --- 4. the daily cap ---------------------------------------------
        // Four 7 km off-peak adult journeys at 4.00 each against a cap of
        // 10.00: 4.00, 4.00, then only the 2.00 that is left, then nothing.
        final Fixture cap = new Fixture();
        for (int i = 0; i < 4; i++) {
            cap.journey("p_cap", 25, 0, 3, OFF_PEAK_H + 2 * i);
        }
        cap.flush();
        final List<Double> amounts = cap.amounts("p_cap");
        final boolean capSequence = amounts.size() == 3
                && eq(amounts.get(0), 4.00) && eq(amounts.get(1), 4.00)
                && eq(amounts.get(2), 2.00);
        final boolean capTotal = eq(cap.charged("p_cap"), CAP_ADULT);
        ok &= capSequence && capTotal;
        json.append(",\"cap_amounts\":").append(amounts)
            .append(",\"cap_charges_only_what_is_left\":").append(capSequence)
            .append(",\"cap_total_equals_daily_cap\":").append(capTotal)
            .append(",\"no_event_once_capped\":").append(amounts.size() == 3);

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    private static boolean eq(final double a, final double b) {
        return Math.abs(a - b) < 1e-6 + EPS;
    }

    /** One scenario, one handler, and the money events it emitted. */
    private static final class Fixture {

        private final Scenario scenario;
        private final PtFareChargeHandler handler;
        private final EventsManager events;
        private final List<PersonMoneyEvent> charged = new ArrayList<>();

        private Fixture() {
            final Config config = ConfigUtils.createConfig();
            final PtFareConfigGroup fares =
                    ConfigUtils.addOrGetModule(config, PtFareConfigGroup.class);
            fares.setBusBandsKm(BANDS_KM);
            fares.setBusAdultOffpeak(ADULT_OFFPEAK);
            fares.setBusAdultPeak(ADULT_PEAK);
            fares.setBusChildOffpeak(CHILD_OFFPEAK);
            fares.setBusChildPeak(CHILD_PEAK);
            fares.setDailyCapAdult(CAP_ADULT);
            fares.setDailyCapChild(CAP_CHILD);
            fares.setDailyCapSenior(CAP_SENIOR);
            fares.setSeniorPerFareCap(1.25);
            fares.setTransferDiscountAdult(2.00);
            fares.setTransferDiscountChild(1.00);
            fares.setTransferWindowMin(60);
            fares.setPeakMorningStartH(7.0);
            fares.setPeakMorningEndH(9.0);
            fares.setPeakEveningStartH(16.0);
            fares.setPeakEveningEndH(18.0);
            fares.setRailPeakMorningStartH(6.5);
            fares.setOffPeakAllDay(false);
            fares.setChildMinAge(5);
            fares.setChildMaxAge(15);
            fares.setSeniorMinAge(60);

            this.scenario = ScenarioUtils.createScenario(config);
            buildSchedule(this.scenario.getTransitSchedule());
            this.events = EventsUtils.createEventsManager();
            this.events.addHandler(new PersonMoneyEventHandler() {
                @Override
                public void handleEvent(final PersonMoneyEvent event) {
                    Fixture.this.charged.add(event);
                }
            });
            this.events.initProcessing();
            this.handler = new PtFareChargeHandler(config, this.events,
                                                   this.scenario);
        }

        /** A stop at each fixture position, one route, one vehicle. */
        private void buildSchedule(final TransitSchedule schedule) {
            final TransitScheduleFactory f = schedule.getFactory();
            for (int i = 0; i < STOP_M.length; i++) {
                schedule.addStopFacility(f.createTransitStopFacility(
                        stopId(i), new Coord((double) STOP_M[i], 0.0), false));
            }
            final TransitLine line =
                    f.createTransitLine(Id.create("line1", TransitLine.class));
            final TransitRoute route = f.createTransitRoute(
                    Id.create("route1", TransitRoute.class), null,
                    Collections.<TransitRouteStop>emptyList(), BUS);
            final Departure departure = f.createDeparture(
                    Id.create("dep1", Departure.class), 0.0);
            departure.setVehicleId(VEHICLE);
            route.addDeparture(departure);
            line.addRoute(route);
            schedule.addTransitLine(line);
        }

        private static Id<TransitStopFacility> stopId(final int i) {
            return Id.create("stop" + i, TransitStopFacility.class);
        }

        /**
         * One journey by an agent of this age, boarding and alighting at the
         * given stops and tapping on at the given hour.
         */
        private void journey(final String personId, final Integer age,
                             final int boardStop, final int alightStop,
                             final double hour) {
            ride(person(personId, age), boardStop, alightStop, hour);
        }

        /** The same, with the age attribute written as a {@code Long}. */
        private void journeyLongAge(final String personId, final Long age,
                                    final int boardStop, final int alightStop,
                                    final double hour) {
            final Person p = person(personId, null);
            p.getAttributes().putAttribute("age", age);
            ride(p, boardStop, alightStop, hour);
        }

        private Person person(final String personId, final Integer age) {
            final Population population = this.scenario.getPopulation();
            final Id<Person> id = Id.create(personId, Person.class);
            Person p = population.getPersons().get(id);
            if (p == null) {
                p = population.getFactory().createPerson(id);
                if (age != null) {
                    p.getAttributes().putAttribute("age", age);
                }
                population.addPerson(p);
            }
            return p;
        }

        private void ride(final Person p, final int boardStop,
                          final int alightStop, final double hour) {
            final double tapOn = hour * 3600.0;
            final double tapOff = tapOn + 900.0;
            this.handler.handleEvent(new VehicleArrivesAtFacilityEvent(
                    tapOn - 10.0, VEHICLE, stopId(boardStop), 0.0));
            this.handler.handleEvent(new PersonEntersVehicleEvent(
                    tapOn, p.getId(), VEHICLE));
            this.handler.handleEvent(new VehicleArrivesAtFacilityEvent(
                    tapOff - 10.0, VEHICLE, stopId(alightStop), 0.0));
            this.handler.handleEvent(new PersonLeavesVehicleEvent(
                    tapOff, p.getId(), VEHICLE));
            // a real activity closes the journey; a stage activity would not
            this.handler.handleEvent(new ActivityStartEvent(
                    tapOff + 60.0, p.getId(), null, null, "home"));
        }

        /** Emit the deferred money events, as the controler does. */
        private void flush() {
            this.handler.notifyAfterMobsim(new AfterMobsimEvent(null, 0, false));
            this.events.finishProcessing();
        }

        private List<Double> amounts(final String personId) {
            final List<Double> out = new ArrayList<>();
            for (final PersonMoneyEvent e : this.charged) {
                if (e.getPersonId().toString().equals(personId)) {
                    out.add(Math.abs(e.getAmount()));
                }
            }
            return out;
        }

        private double charged(final String personId) {
            double sum = 0.0;
            for (final Double a : amounts(personId)) {
                sum += a;
            }
            return Math.round(sum * 1e6) / 1e6;
        }

        private int count(final String personId) {
            return amounts(personId).size();
        }
    }
}
