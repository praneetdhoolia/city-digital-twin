package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.PersonLeavesVehicleEvent;
import org.matsim.api.core.v01.events.PersonScoreEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.PersonEntersVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.PersonLeavesVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.TransitDriverStartsEventHandler;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleCapacity;

/**
 * Charges a public-transport passenger the EXTRA felt time of riding a crowded
 * vehicle, as a {@link PersonScoreEvent}.
 *
 * <p><b>Why this exists.</b> MATSim scores no crowding term. The mobsim's
 * capacity constraint is physical - a full vehicle refuses the next boarding -
 * and SwissRailRaptor's capacity-dependent in-vehicle cost prices load factor
 * in the ROUTER only. So the discomfort that precedes a denied boarding cost
 * nothing: an unlimited number of agents could ride a full train at zero
 * disutility while heavy rail read +247.2 % at the F31 gate, and the C1
 * crowding multipliers (1.00 seated / 1.45 standing) were declared, swept and
 * read by no scoring function at all.
 *
 * <p><b>What is charged.</b> A vehicle carrying {@code n} passengers against
 * {@code s} seats seats {@code min(n, s)} of them and stands the rest. The
 * felt multiplier on an in-vehicle second is the passenger-weighted mean of
 * the two declared multipliers,
 *
 * <pre>  m(n) = (seated x min(n, s) + standing x max(0, n - s)) / n</pre>
 *
 * and the SURPLUS over an uncrowded ride, (m(n) - 1) seconds per second, is
 * accrued while the passenger is aboard and charged at
 * {@code ptCrowding.penaltyUtilsPerHour} - the price of an in-vehicle hour, so
 * a multiplier of m makes an hour aboard cost m hours of it. With the shipped
 * seated multiplier of 1.00 an uncrowded vehicle charges exactly nothing, and
 * only standing loads are priced.
 *
 * <p><b>Why the mean and not a seat allocation.</b> Which particular passenger
 * stands is not observable and MATSim does not model it: boarding order would
 * decide it, and seat inheritance when a seated passenger alights would decide
 * it again. The passenger-weighted mean makes the VEHICLE's total charge exact
 * - it is identically {@code seated x min(n,s) + standing x max(0,n-s)} - and
 * allocates it as each passenger's expectation. Inventing a seat ballot would
 * be a modelling choice nobody declared, and a random one would break
 * determinism.
 *
 * <p><b>What is measured, not assumed.</b> The seat count is the vehicle's own
 * {@link VehicleCapacity#getSeats()} as the run actually carries it - which is
 * the published figure patched by {@code build_matsim_run_inputs.py} (bus
 * 44/18, ferry 149/51, rail 98/48, tram 60/210) and then scaled with the
 * sample fraction by {@code scale_transit_capacity}, so a 25 % arm crowds at
 * 25 % of the real vehicle. Occupancy is the mobsim's own
 * {@link PersonEntersVehicleEvent} / {@link PersonLeavesVehicleEvent} stream,
 * and time aboard is the mobsim's clock, so a vehicle held at a signal accrues
 * the crowding its passengers actually endure.
 *
 * <p><b>How a passenger is told from a driver.</b> Per-vehicle state is
 * created ONLY by {@link TransitDriverStartsEvent}, which is also what names
 * the driver. A person entering a vehicle this class has no state for is not a
 * transit passenger - that covers every car, every taxi, and the transit
 * driver in the event ordering where the driver boards before the departure is
 * announced - and the recorded driver id is skipped in the ordering where it
 * boards after.
 *
 * <p><b>Why the score events are deferred to {@code notifyAfterMobsim}.</b>
 * Emitting an event from inside an event handler re-enters the events manager
 * while it is draining its own queue - the {@link ParkingChargeHandler}
 * discipline, reproduced here for the same reason and with the same sorted,
 * deterministic emission order.
 *
 * <p>The integral is kept PER VEHICLE, not per passenger: every passenger
 * aboard shares one multiplier at any instant, so the vehicle carries a
 * running integral of (m - 1) dt and each passenger is charged the difference
 * between its value when they alighted and its value when they boarded. That
 * is O(1) per boarding rather than O(passengers) per occupancy change.
 *
 * @see PtCrowdingConfigGroup
 */
public final class PtCrowdingScoring implements TransitDriverStartsEventHandler,
        PersonEntersVehicleEventHandler, PersonLeavesVehicleEventHandler,
        AfterMobsimListener {

    /** Kind string carried on every emitted PersonScoreEvent. */
    public static final String KIND = "ptCrowding";

    private final EventsManager events;
    private final Scenario scenario;
    private final double seatedMultiplier;
    private final double standingMultiplier;
    private final double penaltyUtilsPerHour;

    /** One transit vehicle in service. */
    private static final class Aboard {
        /** Seats the vehicle carries in THIS run (sample-scaled). */
        private final double seats;
        private Id<Person> driver;
        private int occupancy;
        private double lastChange;
        /** Running integral of (multiplier - 1) dt since the vehicle first
         *  entered service. Monotone: between departures the occupancy is
         *  zero, the surplus rate is zero, and it does not grow. */
        private double surplusIntegral;

        private Aboard(final double seats, final double now) {
            this.seats = seats;
            this.lastChange = now;
        }
    }

    private final Map<Id<Vehicle>, Aboard> inService = new HashMap<>();
    /** Where a passenger currently aboard found the vehicle's integral. */
    private final Map<Id<Person>, Double> boardedAt = new HashMap<>();
    private final Map<Id<Person>, Double> surplusSeconds = new HashMap<>();
    /** Transit vehicle types with no declared seat count - reported rather
     *  than silently treated as uncrowdable, the 9.12 defect class. */
    private final java.util.Set<String> vehiclesWithoutSeats =
            new java.util.TreeSet<>();

    @Inject
    public PtCrowdingScoring(final Config config, final Scenario scenario,
                             final EventsManager events) {
        final PtCrowdingConfigGroup cfg =
                ConfigUtils.addOrGetModule(config, PtCrowdingConfigGroup.class);
        this.events = events;
        this.scenario = scenario;
        this.seatedMultiplier = cfg.getSeatedMultiplier();
        this.standingMultiplier = cfg.getStandingMultiplier();
        this.penaltyUtilsPerHour = cfg.getPenaltyUtilsPerHour();
    }

    // -- events ------------------------------------------------------------
    @Override
    public void handleEvent(final TransitDriverStartsEvent event) {
        final Aboard open = this.inService.get(event.getVehicleId());
        if (open != null) {
            // The same physical vehicle serving its next departure. Keep the
            // integral (it cannot have grown while empty) and only move the
            // clock, so a passenger who somehow stayed aboard is not charged
            // for the layover twice.
            advance(open, event.getTime());
            open.driver = event.getDriverId();
            return;
        }
        final double seats = seatsOf(event.getVehicleId());
        if (seats <= 0.0) {
            return;
        }
        final Aboard aboard = new Aboard(seats, event.getTime());
        aboard.driver = event.getDriverId();
        this.inService.put(event.getVehicleId(), aboard);
    }

    @Override
    public void handleEvent(final PersonEntersVehicleEvent event) {
        final Aboard aboard = this.inService.get(event.getVehicleId());
        if (aboard == null || event.getPersonId().equals(aboard.driver)) {
            return;                      // not a transit passenger
        }
        advance(aboard, event.getTime());
        aboard.occupancy++;
        this.boardedAt.put(event.getPersonId(), aboard.surplusIntegral);
    }

    @Override
    public void handleEvent(final PersonLeavesVehicleEvent event) {
        final Aboard aboard = this.inService.get(event.getVehicleId());
        if (aboard == null) {
            return;
        }
        final Double boarded = this.boardedAt.remove(event.getPersonId());
        if (boarded == null) {
            return;                      // the driver, or boarded before this
        }
        advance(aboard, event.getTime());
        if (aboard.occupancy > 0) {
            aboard.occupancy--;
        }
        final double surplus = aboard.surplusIntegral - boarded;
        if (surplus > 0.0) {
            this.surplusSeconds.merge(event.getPersonId(), surplus,
                                      Double::sum);
        }
    }

    /** Carry the vehicle's integral forward to `now` at the load it has been
     *  carrying since the last occupancy change. Called BEFORE the occupancy
     *  moves, so the interval just ended is priced at the load that produced
     *  it. */
    private void advance(final Aboard aboard, final double now) {
        final double dt = now - aboard.lastChange;
        if (dt > 0.0 && aboard.occupancy > 0) {
            aboard.surplusIntegral += surplusRate(aboard) * dt;
        }
        aboard.lastChange = now;
    }

    /** m(n) - 1: the extra felt second per second aboard, at this load. */
    private double surplusRate(final Aboard aboard) {
        final double n = aboard.occupancy;
        if (n <= 0.0) {
            return 0.0;
        }
        final double standing = Math.max(0.0, n - aboard.seats);
        final double seated = n - standing;
        return (this.seatedMultiplier * seated
                + this.standingMultiplier * standing) / n - 1.0;
    }

    /** The seats this run's copy of the vehicle carries, or 0 if it declares
     *  none. Read from the scenario's transit vehicles rather than from the
     *  registry: `scale_transit_capacity` rewrites them per sample fraction,
     *  and the crowding must bind on what the mobsim actually enforces. */
    private double seatsOf(final Id<Vehicle> vehicleId) {
        final Vehicle vehicle =
                this.scenario.getTransitVehicles().getVehicles().get(vehicleId);
        if (vehicle == null || vehicle.getType() == null) {
            return 0.0;
        }
        final VehicleCapacity capacity = vehicle.getType().getCapacity();
        final Integer seats = capacity == null ? null : capacity.getSeats();
        if (seats == null || seats <= 0) {
            this.vehiclesWithoutSeats.add(
                    vehicle.getType().getId().toString());
            return 0.0;
        }
        return seats;
    }

    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        // Deterministic emission order: scores are additive so order cannot
        // change a result, but a sorted event stream diffs cleanly.
        final List<Map.Entry<Id<Person>, Double>> charges =
                new ArrayList<>(this.surplusSeconds.entrySet());
        charges.sort(Map.Entry.comparingByKey());
        for (final Map.Entry<Id<Person>, Double> entry : charges) {
            final double utils =
                    -entry.getValue() / 3600.0 * this.penaltyUtilsPerHour;
            this.events.processEvent(new PersonScoreEvent(
                    24.0 * 3600.0, entry.getKey(), utils, KIND));
        }
        clear();
    }

    @Override
    public void reset(final int iteration) {
        clear();
    }

    private void clear() {
        this.surplusSeconds.clear();
        this.boardedAt.clear();
        this.inService.clear();
    }

    /** Logged once at startup, so a run's console says what it charges. */
    @Override
    public String toString() {
        return "ptCrowding: seated x" + this.seatedMultiplier + ", standing x"
                + this.standingMultiplier + ", " + this.penaltyUtilsPerHour
                + " utils per felt extra hour aboard"
                + (this.vehiclesWithoutSeats.isEmpty() ? ""
                   : "; NO SEAT COUNT (uncrowdable): "
                     + this.vehiclesWithoutSeats);
    }
}
