package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.ActivityStartEvent;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.PersonLeavesVehicleEvent;
import org.matsim.api.core.v01.events.PersonMoneyEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.ActivityStartEventHandler;
import org.matsim.api.core.v01.events.handler.PersonEntersVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.PersonLeavesVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.TransitDriverStartsEventHandler;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.api.experimental.events.VehicleArrivesAtFacilityEvent;
import org.matsim.core.api.experimental.events.handler.VehicleArrivesAtFacilityEventHandler;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.utils.geometry.CoordUtils;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.pt.transitSchedule.api.TransitStopFacility;
import org.matsim.vehicles.Vehicle;

/**
 * Charges every public transport journey its published Opal fare, as a
 * {@link PersonMoneyEvent} (DECISIONS.md 9.135, issue #98).
 *
 * <p><b>Why this exists.</b> Until 9.135 the model charged car fuel
 * ({@code monetaryDistanceRate}), parking ({@link ParkingChargeHandler}) and
 * the taxi meter ({@link FareChargeHandler}) while every train, bus, tram and
 * ferry ride was free - asymmetric pricing that no observation supports, in a
 * model whose heavy rail read +161.8% at the F21 gate on exactly the long
 * trips a distance-banded fare prices. The schedule charged here is the
 * published one, archived at {@code data/raw/fares/} and declared field by
 * field in the registry; nothing in this class decides a number.
 *
 * <p><b>What a journey is.</b> Opal charges per fare leg within a linked
 * journey: consecutive boardings of the SAME submode within the transfer
 * window continue one fare leg (a train-to-train change is not a new fare);
 * a transfer to a DIFFERENT submode starts a new fare leg with the published
 * transfer discount applied. A journey closes when the traveller starts a
 * real (non-staging) activity. Fare distance is the crow-fly from a fare
 * leg's first boarding stop to its last alighting stop, which is the Opal
 * tap-on-to-tap-off convention.
 *
 * <p><b>Who pays what.</b> The rider class is read from the person's held
 * attributes: under {@code childMinAge} free; {@code childMinAge}..
 * {@code childMaxAge} the Child/Youth table; from {@code seniorMinAge} and
 * not employed full-time the Gold Senior/Pensioner rule (Child/Youth fare
 * capped per fare, with its own daily cap); everyone else - including agents
 * with no age attribute, such as external boundary travellers - the Adult
 * table. Each class carries its published daily cap.
 *
 * <p><b>What is deliberately not charged.</b> A traveller still aboard at
 * the end of the mobsim never tapped off; their unfinished fare leg is
 * dropped rather than priced at an invented default fare. The weekly cap
 * and the single-trip-ticket premium do not exist in a one-day simulation
 * and are recorded, not modelled (DECISIONS.md 9.135).
 *
 * <p><b>Deferred emission.</b> Money events accumulate during the mobsim and
 * are emitted at {@code notifyAfterMobsim} - the {@link ParkingChargeHandler}
 * discipline; scoring still sees them because {@code EventsToScore} finishes
 * after {@code afterMobsim}.
 */
public final class PtFareChargeHandler implements
        PersonEntersVehicleEventHandler, PersonLeavesVehicleEventHandler,
        VehicleArrivesAtFacilityEventHandler, TransitDriverStartsEventHandler,
        ActivityStartEventHandler, AfterMobsimListener {

    /** Purpose string carried on every emitted PersonMoneyEvent. */
    public static final String PURPOSE = "ptFare";
    /** Deliberately generic: naming an operator would name a place. */
    public static final String PARTNER = "publicTransportOperator";

    private final EventsManager events;
    private final PtFareConfigGroup cfg;
    private final Scenario scenario;

    /** Transit vehicle -> the submode of the route it serves. */
    private final Map<Id<Vehicle>, String> vehicleMode = new HashMap<>();
    /** Transit vehicle -> the stop facility it last arrived at. */
    private final Map<Id<Vehicle>, Id<TransitStopFacility>> vehicleAt =
            new HashMap<>();
    private final Set<Id<Person>> transitDrivers = new HashSet<>();

    /** One fare leg: consecutive same-submode boardings within the window. */
    private static final class FareLeg {
        private final String mode;
        private final Coord board;
        private final double boardTime;
        private Coord alight;
        private double alightTime;

        private FareLeg(final String mode, final Coord board,
                final double boardTime) {
            this.mode = mode;
            this.board = board;
            this.boardTime = boardTime;
        }
    }

    private final Map<Id<Person>, List<FareLeg>> journeys = new HashMap<>();
    private final Map<Id<Person>, Double> chargedToday = new HashMap<>();
    private final List<PersonMoneyEvent> pending = new ArrayList<>();
    private long fareLegs;
    private long journeysCharged;
    private double totalCharged;

    @Inject
    public PtFareChargeHandler(final Config config, final EventsManager events,
            final Scenario scenario) {
        this.events = events;
        this.scenario = scenario;
        this.cfg = ConfigUtils.addOrGetModule(config, PtFareConfigGroup.class);
        for (final TransitLine line
                : scenario.getTransitSchedule().getTransitLines().values()) {
            for (final TransitRoute route : line.getRoutes().values()) {
                for (final Departure dep : route.getDepartures().values()) {
                    this.vehicleMode.put(dep.getVehicleId(),
                            route.getTransportMode());
                }
            }
        }
    }

    @Override
    public void handleEvent(final TransitDriverStartsEvent event) {
        this.transitDrivers.add(event.getDriverId());
    }

    @Override
    public void handleEvent(final VehicleArrivesAtFacilityEvent event) {
        this.vehicleAt.put(event.getVehicleId(), event.getFacilityId());
    }

    @Override
    public void handleEvent(final PersonEntersVehicleEvent event) {
        final String mode = this.vehicleMode.get(event.getVehicleId());
        if (mode == null || this.transitDrivers.contains(event.getPersonId())) {
            return;
        }
        final Coord at = facilityCoord(event.getVehicleId());
        if (at == null) {
            return;
        }
        final List<FareLeg> legs = this.journeys.computeIfAbsent(
                event.getPersonId(), k -> new ArrayList<>());
        if (!legs.isEmpty()) {
            final FareLeg last = legs.get(legs.size() - 1);
            if (last.mode.equals(mode) && last.alight != null
                    && event.getTime() - last.alightTime
                            <= this.cfg.getTransferWindowMin() * 60.0) {
                // same submode within the window: the fare leg continues
                last.alight = null;
                return;
            }
        }
        legs.add(new FareLeg(mode, at, event.getTime()));
    }

    @Override
    public void handleEvent(final PersonLeavesVehicleEvent event) {
        final String mode = this.vehicleMode.get(event.getVehicleId());
        if (mode == null || this.transitDrivers.contains(event.getPersonId())) {
            return;
        }
        final List<FareLeg> legs = this.journeys.get(event.getPersonId());
        if (legs == null || legs.isEmpty()) {
            return;
        }
        final Coord at = facilityCoord(event.getVehicleId());
        final FareLeg leg = legs.get(legs.size() - 1);
        if (at != null) {
            leg.alight = at;
            leg.alightTime = event.getTime();
        }
    }

    @Override
    public void handleEvent(final ActivityStartEvent event) {
        if (TripStructureUtils.isStageActivityType(event.getActType())) {
            return;
        }
        final List<FareLeg> legs = this.journeys.remove(event.getPersonId());
        if (legs != null && !legs.isEmpty()) {
            charge(event.getPersonId(), legs, event.getTime());
        }
    }

    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        // a traveller still aboard never tapped off; their journey's finished
        // fare legs are still owed
        for (final Map.Entry<Id<Person>, List<FareLeg>> e
                : this.journeys.entrySet()) {
            charge(e.getKey(), e.getValue(), Double.NaN);
        }
        this.journeys.clear();
        for (final PersonMoneyEvent charge : this.pending) {
            this.events.processEvent(charge);
        }
        this.pending.clear();
    }

    @Override
    public void reset(final int iteration) {
        this.journeys.clear();
        this.chargedToday.clear();
        this.pending.clear();
        this.vehicleAt.clear();
        this.transitDrivers.clear();
        this.fareLegs = 0;
        this.journeysCharged = 0;
        this.totalCharged = 0.0;
    }

    private Coord facilityCoord(final Id<Vehicle> vehicle) {
        final Id<TransitStopFacility> facility = this.vehicleAt.get(vehicle);
        if (facility == null) {
            return null;
        }
        final TransitStopFacility stop =
                this.scenario.getTransitSchedule().getFacilities().get(facility);
        return stop == null ? null : stop.getCoord();
    }

    /** Rider classes, each with its own table, cap and transfer discount. */
    private enum RiderClass { FREE, CHILD, SENIOR, ADULT }

    private RiderClass riderClass(final Id<Person> personId) {
        final Person person =
                this.scenario.getPopulation().getPersons().get(personId);
        if (person == null) {
            return RiderClass.ADULT;
        }
        final Object ageAttr = person.getAttributes().getAttribute("age");
        if (!(ageAttr instanceof Integer)) {
            return RiderClass.ADULT;
        }
        final int age = (Integer) ageAttr;
        if (age < this.cfg.getChildMinAge()) {
            return RiderClass.FREE;
        }
        if (age <= this.cfg.getChildMaxAge()) {
            return RiderClass.CHILD;
        }
        if (age >= this.cfg.getSeniorMinAge()) {
            final Object emp =
                    person.getAttributes().getAttribute("employment");
            if (!"employed_full_time".equals(emp)) {
                return RiderClass.SENIOR;
            }
        }
        return RiderClass.ADULT;
    }

    private void charge(final Id<Person> personId, final List<FareLeg> legs,
            final double eventTime) {
        final RiderClass rc = riderClass(personId);
        if (rc == RiderClass.FREE) {
            return;
        }
        double journeyFare = 0.0;
        double lastAlight = Double.NaN;
        int priced = 0;
        for (final FareLeg leg : legs) {
            if (leg.alight == null) {
                continue;  // no tap-off: dropped, never priced at a default
            }
            final double km = CoordUtils.calcEuclideanDistance(
                    leg.board, leg.alight) / 1000.0;
            double fare = lookup(leg.mode, km, rc, isPeak(leg));
            if (priced > 0 && !Double.isNaN(lastAlight)
                    && leg.boardTime - lastAlight
                            <= this.cfg.getTransferWindowMin() * 60.0) {
                final double discount = rc == RiderClass.ADULT
                        ? this.cfg.getTransferDiscountAdult()
                        : this.cfg.getTransferDiscountChild();
                fare = Math.max(0.0, fare - discount);
            }
            journeyFare += fare;
            lastAlight = leg.alightTime;
            priced++;
            this.fareLegs++;
        }
        if (priced == 0) {
            return;
        }
        final double cap = rc == RiderClass.ADULT
                ? this.cfg.getDailyCapAdult()
                : rc == RiderClass.CHILD ? this.cfg.getDailyCapChild()
                : this.cfg.getDailyCapSenior();
        final double already = this.chargedToday.getOrDefault(personId, 0.0);
        final double amount = Math.min(journeyFare, Math.max(0.0, cap - already));
        if (amount <= 0.0) {
            return;
        }
        this.chargedToday.put(personId, already + amount);
        final double when =
                Double.isNaN(eventTime) ? lastAlight : eventTime;
        this.pending.add(new PersonMoneyEvent(when, personId, -amount,
                PURPOSE, PARTNER, null));
        this.journeysCharged++;
        this.totalCharged += amount;
    }

    /** Tap-on time decides peak, per the published rule. */
    private boolean isPeak(final FareLeg leg) {
        if (this.cfg.isOffPeakAllDay()) {
            return false;
        }
        final double h = (leg.boardTime / 3600.0) % 24.0;
        final double morningStart = "rail".equals(leg.mode)
                ? this.cfg.getRailPeakMorningStartH()
                : this.cfg.getPeakMorningStartH();
        return (h >= morningStart && h < this.cfg.getPeakMorningEndH())
                || (h >= this.cfg.getPeakEveningStartH()
                        && h < this.cfg.getPeakEveningEndH());
    }

    private double lookup(final String mode, final double km,
            final RiderClass rc, final boolean peak) {
        if ("ferry".equals(mode)) {
            final double adult = peak ? this.cfg.getFerryAdultPeak()
                    : this.cfg.getFerryAdultOffpeak();
            final double child = peak ? this.cfg.getFerryChildPeak()
                    : this.cfg.getFerryChildOffpeak();
            return classFare(rc, adult, child);
        }
        final String bands;
        final String adultCsv;
        final String childCsv;
        if ("rail".equals(mode)) {
            bands = this.cfg.getTrainBandsKm();
            adultCsv = peak ? this.cfg.getTrainAdultPeak()
                    : this.cfg.getTrainAdultOffpeak();
            childCsv = peak ? this.cfg.getTrainChildPeak()
                    : this.cfg.getTrainChildOffpeak();
        } else if ("tram".equals(mode)) {
            bands = this.cfg.getTramBandsKm();
            adultCsv = peak ? this.cfg.getTramAdultPeak()
                    : this.cfg.getTramAdultOffpeak();
            childCsv = peak ? this.cfg.getTramChildPeak()
                    : this.cfg.getTramChildOffpeak();
        } else {
            // bus, and any scheduled submode without a table of its own,
            // takes the bus table - the aggregate pt fallback of 9.78
            bands = this.cfg.getBusBandsKm();
            adultCsv = peak ? this.cfg.getBusAdultPeak()
                    : this.cfg.getBusAdultOffpeak();
            childCsv = peak ? this.cfg.getBusChildPeak()
                    : this.cfg.getBusChildOffpeak();
        }
        final double[] upper = PtFareConfigGroup.parse(bands);
        int band = upper.length;  // the open last band
        for (int i = 0; i < upper.length; i++) {
            if (km <= upper[i]) {
                band = i;
                break;
            }
        }
        final double adult = PtFareConfigGroup.parse(adultCsv)[band];
        final double child = PtFareConfigGroup.parse(childCsv)[band];
        return classFare(rc, adult, child);
    }

    private double classFare(final RiderClass rc, final double adult,
            final double child) {
        if (rc == RiderClass.ADULT) {
            return adult;
        }
        if (rc == RiderClass.CHILD) {
            return child;
        }
        return Math.min(child, this.cfg.getSeniorPerFareCap());
    }

    /** Logged once at startup, so a run's console says what it charged. */
    @Override
    public String toString() {
        return "ptFare: published Opal schedule; last iteration charged "
                + this.journeysCharged + " journeys over " + this.fareLegs
                + " fare legs, " + String.format("%.2f", this.totalCharged)
                + " AUD";
    }
}
