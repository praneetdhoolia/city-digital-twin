package citysim;

import com.google.inject.Inject;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Population;
import org.matsim.core.config.groups.QSimConfigGroup;
import org.matsim.core.mobsim.framework.AgentSource;
import org.matsim.core.mobsim.framework.MobsimAgent;
import org.matsim.core.mobsim.qsim.QSim;
import org.matsim.core.mobsim.qsim.agents.AgentFactory;
import org.matsim.core.mobsim.qsim.interfaces.Netsim;
import org.matsim.core.mobsim.qsim.qnetsimengine.QVehicleFactory;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleUtils;

/**
 * The population agent source, tolerant of a main-mode leg whose route is not
 * a network route (DECISIONS.md 9.54).
 *
 * <p>MATSim's own {@code PopulationAgentSource} casts EVERY main-mode leg's
 * route to a {@link NetworkRoute} while parking the mode vehicles — and once
 * {@code walk} is a qsim main mode, that cast dies on the transit router's
 * access/egress and direct-walk legs, which carry mode {@code walk} with a
 * GENERIC route (measured: 9,466 such legs in a 1% day, every one with
 * {@code routingMode=pt}). Those legs are teleported stubs by design and are
 * claimed at departure by {@link GenericRouteTeleporter}; this source simply
 * does not demand a vehicle for them.
 *
 * <p>This is a REIMPLEMENTATION for the one configuration this model
 * declares, and it refuses any other rather than half-supporting it:
 * {@code vehiclesSource=modeVehicleTypesFromVehiclesData}, where
 * PrepareForSim has already created every (person x main mode) vehicle in the
 * scenario. For each person it parks each main mode's vehicle at the mode's
 * first network-routed leg's start link (people with no such leg get the
 * vehicle at their first activity's link, where it stays unused), writes the
 * vehicle id into each network route exactly as the original does, and
 * inserts the agent.
 */
public final class TolerantAgentSource implements AgentSource {

    private final Population population;
    private final AgentFactory agentFactory;
    private final QVehicleFactory qVehicleFactory;
    private final Netsim qsim;

    @Inject
    TolerantAgentSource(final Population population,
                        final AgentFactory agentFactory,
                        final QVehicleFactory qVehicleFactory,
                        final Netsim qsim) {
        this.population = population;
        this.agentFactory = agentFactory;
        this.qVehicleFactory = qVehicleFactory;
        this.qsim = qsim;
        final QSimConfigGroup.VehiclesSource source =
                qsim.getScenario().getConfig().qsim().getVehiclesSource();
        if (source != QSimConfigGroup.VehiclesSource
                .modeVehicleTypesFromVehiclesData) {
            throw new IllegalStateException(
                    "TolerantAgentSource supports exactly the declared "
                    + "qsim.vehiclesSource=modeVehicleTypesFromVehiclesData "
                    + "(RUN.qsim.vehicles_source); got " + source
                    + ". Supporting another source silently would be the "
                    + "right-by-accident defect class.");
        }
    }

    @Override
    public void insertAgentsIntoMobsim() {
        final Set<String> mainModes = new HashSet<>(
                this.qsim.getScenario().getConfig().qsim().getMainModes());
        // 9.146: a vehicle two persons share (the household roster,
        // B.population.vehicle_roster) is parked ONCE, where the first of
        // them starts the day. A later member starting elsewhere finds no
        // car at their link and, under qsim.vehicleBehavior=wait, waits for
        // it - which is where the car actually is. Counted, never re-parked.
        final java.util.Map<Id<Vehicle>, Id<org.matsim.api.core.v01.network.Link>>
                parkedAt = new java.util.HashMap<>();
        int elsewhere = 0;
        for (final Person person : this.population.getPersons().values()) {
            // 9.148: vehicles BEFORE the agent. MATSim 26's agent is built
            // from a message that copies the plan elements, so a vehicle id
            // stamped on the person's route after the agent exists never
            // reaches the agent - which the netsim engine's own error note
            // says in as many words. The old order only worked while every
            // route already carried the id PrepareForSim gave it; under the
            // household roster the mapped car differs, and a 1 % smoke died
            // at the first car departure asking for the person-id vehicle.
            elsewhere += insertVehicles(person, mainModes, parkedAt);
            final MobsimAgent agent =
                    this.agentFactory.createMobsimAgentFromPerson(person);
            this.qsim.insertAgentIntoMobsim(agent);
        }
        if (elsewhere > 0) {
            org.apache.logging.log4j.LogManager.getLogger(TolerantAgentSource.class)
                    .info("agentSource: {} shared vehicle(s) wanted at a link other "
                          + "than where they stand; the agent waits for the car "
                          + "(qsim.vehicleBehavior)", elsewhere);
        }
    }

    private int insertVehicles(final Person person, final Set<String> mainModes,
                               final java.util.Map<Id<Vehicle>,
                                       Id<org.matsim.api.core.v01.network.Link>>
                                       parkedAt) {
        int elsewhere = 0;
        final List<Leg> legs =
                TripStructureUtils.getLegs(person.getSelectedPlan());
        final Set<String> parked = new HashSet<>();
        for (final Leg leg : legs) {
            final String mode = leg.getMode();
            if (!mainModes.contains(mode)) {
                continue;
            }
            if (!(leg.getRoute() instanceof NetworkRoute)) {
                // a teleported stub wearing a main-mode name (the transit
                // router's walk legs): no vehicle, no cast, no crash -
                // GenericRouteTeleporter moves it at departure
                continue;
            }
            final NetworkRoute route = (NetworkRoute) leg.getRoute();
            final Id<Vehicle> vehicleId =
                    VehicleUtils.getVehicleId(person, mode);
            route.setVehicleId(vehicleId);
            if (parked.contains(mode)) {
                continue;
            }
            parked.add(mode);
            final Id<org.matsim.api.core.v01.network.Link> already =
                    parkedAt.get(vehicleId);
            if (already != null) {
                if (!already.equals(route.getStartLinkId())) {
                    elsewhere++;
                }
                continue;                          // 9.146: one car, parked once
            }
            parkedAt.put(vehicleId, route.getStartLinkId());
            final Vehicle vehicle = this.qsim.getScenario().getVehicles()
                    .getVehicles().get(vehicleId);
            if (vehicle == null) {
                throw new IllegalStateException(
                        "no vehicle " + vehicleId + " for main mode '" + mode
                        + "' - PrepareForSim creates one per person and mode "
                        + "under modeVehicleTypesFromVehiclesData, so its "
                        + "absence means the vehicles file lost the type");
            }
            ((QSim) this.qsim).addParkedVehicle(
                    this.qVehicleFactory.createQVehicle(vehicle),
                    route.getStartLinkId());
        }
        return elsewhere;
    }
}
