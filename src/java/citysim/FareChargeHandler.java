package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.List;
import org.matsim.api.core.v01.events.PersonDepartureEvent;
import org.matsim.api.core.v01.events.PersonMoneyEvent;
import org.matsim.api.core.v01.events.handler.PersonDepartureEventHandler;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;

/**
 * Charges the flagfall for every point-to-point trip, as a
 * {@link PersonMoneyEvent} (issue #49, task 4.7.8).
 *
 * <p><b>Why a handler at all.</b> The fare has two parts. The per-kilometre
 * part is expressible natively ({@code monetaryDistanceRate} on the taxi
 * modeParams) and never comes here. The flagfall is a fixed charge PER TRIP,
 * which no MATSim scoring parameter expresses - a constant on the mode is
 * utility, not money, and would not respond to
 * {@code marginalUtilityOfMoney}. So each taxi departure accrues one
 * flagfall, exactly as {@link ParkingChargeHandler} accrues a parking spell.
 *
 * <p><b>Charged on departure, one per leg.</b> A teleported mode has one leg
 * per trip (no transfers), so departure count equals trip count; charging on
 * departure rather than arrival means an agent who never arrives (stuck) has
 * still hailed the vehicle, which is the conservative reading.
 *
 * <p><b>Deferred emission.</b> Money events are accumulated during the mobsim
 * and emitted at {@code notifyAfterMobsim}, never from inside the handler -
 * emitting from a handler re-enters the events manager while it drains its
 * own queue (the ParkingChargeHandler discipline; scoring still sees them
 * because {@code EventsToScore} finishes after {@code afterMobsim}).
 *
 * <p>The amount is negative, matching the sign convention
 * {@code monetaryDistanceRate} uses; purpose and partner strings are generic
 * because naming an operator would name a place.
 */
public final class FareChargeHandler
        implements PersonDepartureEventHandler, AfterMobsimListener {

    /** Purpose string carried on every emitted PersonMoneyEvent. */
    public static final String PURPOSE = "fare";
    /** Deliberately generic: naming an operator here would name a place. */
    public static final String PARTNER = "pointToPointOperator";

    private final EventsManager events;
    private final String mode;
    private final double flagfall;

    private final List<PersonMoneyEvent> pending = new ArrayList<>();

    @Inject
    public FareChargeHandler(final Config config, final EventsManager events) {
        final FareConfigGroup cfg =
                ConfigUtils.addOrGetModule(config, FareConfigGroup.class);
        this.events = events;
        this.mode = cfg.getMode();
        this.flagfall = cfg.getFlagfallAud();
    }

    @Override
    public void handleEvent(final PersonDepartureEvent event) {
        if (!this.mode.equals(event.getLegMode())) {
            return;
        }
        this.pending.add(new PersonMoneyEvent(
                event.getTime(), event.getPersonId(), -this.flagfall,
                PURPOSE, PARTNER, event.getLinkId().toString()));
    }

    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        for (final PersonMoneyEvent charge : this.pending) {
            this.events.processEvent(charge);
        }
        this.pending.clear();
    }

    @Override
    public void reset(final int iteration) {
        this.pending.clear();
    }

    /** Logged once at startup, so a run's console says what it charged. */
    @Override
    public String toString() {
        return "fare: mode " + this.mode + ", flagfall " + this.flagfall
                + " AUD per departure (per-km fare is native scoring)";
    }
}
