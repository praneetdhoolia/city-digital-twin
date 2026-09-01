package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.events.LinkEnterEvent;
import org.matsim.api.core.v01.events.LinkLeaveEvent;
import org.matsim.api.core.v01.events.PersonScoreEvent;
import org.matsim.api.core.v01.events.VehicleEntersTrafficEvent;
import org.matsim.api.core.v01.events.VehicleLeavesTrafficEvent;
import org.matsim.api.core.v01.events.handler.LinkEnterEventHandler;
import org.matsim.api.core.v01.events.handler.LinkLeaveEventHandler;
import org.matsim.api.core.v01.events.handler.VehicleEntersTrafficEventHandler;
import org.matsim.api.core.v01.events.handler.VehicleLeavesTrafficEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.vehicles.Vehicle;

/**
 * Charges a cyclist the felt EXTRA time of riding beside motor traffic, as a
 * {@link PersonScoreEvent} (DECISIONS.md 9.138, issue #107).
 *
 * <p><b>Why this exists.</b> The route-choice literature's dominant cycling
 * factor is adjacent traffic: Broach, Dill &amp; Gliebe 2012 measured
 * cyclists treating a mile on a 30k+ AADT arterial without a bike lane as
 * over seven miles of quiet street, and the model carried none of it — a
 * six-lane arterial cycled exactly like a cul-de-sac while modelled bike
 * stood at +185.5% at the F22 iteration-100 gate.
 *
 * <p><b>What is charged.</b> The run network carries a
 * {@code bike_stress_factor} attribute per bike-capable link (stamped by
 * {@code build_matsim_run_inputs.py} from the declared class mapping). A
 * traversal that took t seconds on a link with factor f accrues
 * (f - 1) x t seconds of felt surplus; at AfterMobsim each person's surplus
 * is charged at {@code bikeStress.penaltyUtilsPerHour} — the trip-weighted
 * VOT x beta_bike_mode x marginalUtilityOfMoney identity, i.e. the surplus
 * is priced exactly as if it were ridden.
 *
 * <p><b>What is measured, not assumed.</b> Traversal times are the mobsim's
 * own ({@link VehicleEntersTrafficEvent} / {@link LinkEnterEvent} to
 * {@link LinkLeaveEvent} / {@link VehicleLeavesTrafficEvent}), so a
 * gradient-slowed climb on a stressed link accrues its true extra seconds
 * rather than a beeline estimate.
 *
 * <p><b>Why the score events are deferred to {@code notifyAfterMobsim}.</b>
 * Emitting an event from inside an event handler re-enters the events
 * manager while it is draining its own queue — the
 * {@link ParkingChargeHandler} discipline, reproduced here for the same
 * reason.
 *
 * <p>No spatial work happens here: the class-to-factor derivation lives in
 * the build layer, and this handler reads one link attribute.
 */
public final class BikeStressScoring implements VehicleEntersTrafficEventHandler,
        VehicleLeavesTrafficEventHandler, LinkEnterEventHandler,
        LinkLeaveEventHandler, AfterMobsimListener {

    /** Kind string carried on every emitted PersonScoreEvent. */
    public static final String KIND = "bikeStress";

    private final EventsManager events;
    private final double penaltyUtilsPerHour;
    /** factor - 1 per link that carries a factor above 1; absent = 0. */
    private final Map<Id<Link>, Double> surplusByLink = new HashMap<>();

    /** One cycling vehicle currently in traffic. */
    private static final class Ride {
        private final Id<Person> person;
        private double enteredAt;

        private Ride(final Id<Person> person, final double enteredAt) {
            this.person = person;
            this.enteredAt = enteredAt;
        }
    }

    private final Map<Id<Vehicle>, Ride> riding = new HashMap<>();
    private final Map<Id<Person>, Double> surplusSeconds = new HashMap<>();

    @Inject
    public BikeStressScoring(final Config config, final Network network,
                             final EventsManager events) {
        final BikeStressConfigGroup cfg =
                ConfigUtils.addOrGetModule(config, BikeStressConfigGroup.class);
        this.events = events;
        this.penaltyUtilsPerHour = cfg.getPenaltyUtilsPerHour();
        for (final Link link : network.getLinks().values()) {
            final Object raw = link.getAttributes()
                    .getAttribute(BikeStressConfigGroup.STRESS_ATTRIBUTE);
            if (raw == null) {
                continue;
            }
            final double factor = Double.parseDouble(raw.toString());
            if (factor > 1.0) {
                this.surplusByLink.put(link.getId(), factor - 1.0);
            }
        }
    }

    // -- events ------------------------------------------------------------
    @Override
    public void handleEvent(final VehicleEntersTrafficEvent event) {
        if (!org.matsim.api.core.v01.TransportMode.bike
                .equals(event.getNetworkMode())) {
            return;
        }
        this.riding.put(event.getVehicleId(),
                        new Ride(event.getPersonId(), event.getTime()));
    }

    @Override
    public void handleEvent(final LinkEnterEvent event) {
        final Ride ride = this.riding.get(event.getVehicleId());
        if (ride != null) {
            ride.enteredAt = event.getTime();
        }
    }

    @Override
    public void handleEvent(final LinkLeaveEvent event) {
        accrue(this.riding.get(event.getVehicleId()), event.getLinkId(),
               event.getTime());
    }

    @Override
    public void handleEvent(final VehicleLeavesTrafficEvent event) {
        final Ride ride = this.riding.remove(event.getVehicleId());
        accrue(ride, event.getLinkId(), event.getTime());
    }

    private void accrue(final Ride ride, final Id<Link> link, final double now) {
        if (ride == null) {
            return;
        }
        final Double surplus = this.surplusByLink.get(link);
        if (surplus == null) {
            return;
        }
        final double dt = now - ride.enteredAt;
        if (dt <= 0.0) {
            return;
        }
        this.surplusSeconds.merge(ride.person, surplus * dt, Double::sum);
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
        this.surplusSeconds.clear();
        this.riding.clear();
    }

    @Override
    public void reset(final int iteration) {
        this.riding.clear();
        this.surplusSeconds.clear();
    }

    /** Logged once at startup, so a run's console says what it charges. */
    @Override
    public String toString() {
        return "bikeStress: " + this.surplusByLink.size()
                + " stressed links, penalty "
                + this.penaltyUtilsPerHour + " utils per felt extra hour";
    }
}
