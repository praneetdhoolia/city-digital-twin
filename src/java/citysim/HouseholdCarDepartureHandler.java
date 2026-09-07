package citysim;

import com.google.inject.Inject;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.core.mobsim.framework.MobsimAgent;
import org.matsim.core.mobsim.framework.MobsimDriverAgent;
import org.matsim.core.mobsim.framework.events.MobsimBeforeCleanupEvent;
import org.matsim.core.mobsim.framework.events.MobsimInitializedEvent;
import org.matsim.core.mobsim.framework.listeners.MobsimBeforeCleanupListener;
import org.matsim.core.mobsim.framework.listeners.MobsimInitializedListener;
import org.matsim.core.mobsim.qsim.interfaces.DepartureHandler;
import org.matsim.core.mobsim.qsim.interfaces.NetsimLink;
import org.matsim.core.mobsim.qsim.qnetsimengine.QLinkI;
import org.matsim.core.mobsim.qsim.qnetsimengine.QNetsimEngineI;
import org.matsim.vehicles.Vehicle;

/**
 * A driver whose household car is out waits for it; everyone else departs as
 * MATSim always let them.
 *
 * <h2>Why a handler of our own (DECISIONS.md 9.148)</h2>
 *
 * <p>{@code qsim.vehicleBehavior} is GLOBAL. This model runs walk and taxi as
 * network main modes with a vehicle per person, and neither is chain-based: a
 * walk after a bus leg starts where the walk "vehicle" is not. Under MATSim's
 * default {@code teleport} the vehicle is quietly moved to the agent, which
 * is what those modes need; under {@code wait} the agent stands until the
 * end of the day. Measured on the F27 arm's iteration 0 under a global
 * {@code wait}: car departures 82,388 against F26's 232,394, 55,862 car
 * agents stuck, 12,837 walk and 11,537 ride, and every later leg of a stuck
 * agent lost; by iteration 19 car had "recovered" only because co-evolution
 * abandoned every plan that strands - a bias, not a constraint.
 *
 * <h2>What this does</h2>
 *
 * <p>Registered BEFORE the netsim engine's own departure handler, so it sees
 * every departure first. It acts on exactly one case: a {@code car} departure
 * by a driver mapped to a household car ({@link HouseholdVehicleRoster},
 * {@code hh<id>_car<k>}) whose car is NOT parked at the departure link. That
 * driver is registered with the link as waiting for the car -
 * {@link QLinkI#registerDriverAgentWaitingForCar} - and MATSim's own link
 * departs them when the car is parked back there, the mechanism its
 * {@code wait} behaviour uses. Every other departure - a car that is at its
 * link, any other mode, any person-owned vehicle - is left to the default
 * handler under the declared global behaviour, so nothing else changes. The
 * constraint is physical and the score pays for the wait; a driver whose car
 * never comes back is counted stuck at the end of the day, which is the price
 * of it being a constraint rather than a penalty.
 */
public final class HouseholdCarDepartureHandler implements DepartureHandler,
        MobsimInitializedListener, MobsimBeforeCleanupListener {

    private static final Logger LOG =
            LogManager.getLogger(HouseholdCarDepartureHandler.class);
    public static final String COMPONENT = "citysimHouseholdCarDeparture";

    private final QNetsimEngineI netsim;
    private int waited = 0;

    @Inject
    HouseholdCarDepartureHandler(final QNetsimEngineI netsim) {
        this.netsim = netsim;
    }

    @Override
    public boolean handleDeparture(final double now, final MobsimAgent agent,
                                   final Id<Link> linkId) {
        if (!TransportMode.car.equals(agent.getMode())
                || !(agent instanceof MobsimDriverAgent)) {
            return false;
        }
        final MobsimDriverAgent driver = (MobsimDriverAgent) agent;
        final Id<Vehicle> vehicleId = driver.getPlannedVehicleId();
        if (vehicleId == null || !vehicleId.toString()
                .startsWith(HouseholdVehicleRoster.VEHICLE_ID_PREFIX)) {
            return false;                          // a person-owned vehicle
        }
        final NetsimLink netsimLink = netsim.getNetsimNetwork().getNetsimLink(linkId);
        if (!(netsimLink instanceof QLinkI)) {
            return false;
        }
        final QLinkI link = (QLinkI) netsimLink;
        if (link.getParkedVehicle(vehicleId) != null) {
            return false;                          // the car is here: default
        }
        // The household car is out. Wait for it, at this link; the link
        // departs the driver when the car is parked back here.
        link.registerDriverAgentWaitingForCar(driver);
        waited++;
        return true;
    }

    @Override
    public void notifyMobsimInitialized(final MobsimInitializedEvent e) {
        waited = 0;
    }

    @Override
    public void notifyMobsimBeforeCleanup(final MobsimBeforeCleanupEvent e) {
        LOG.info("householdCar: {} driver(s) waited for a household car that "
                 + "was out (B.population.vehicle_roster, 9.148)", waited);
    }
}
