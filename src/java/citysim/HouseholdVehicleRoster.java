package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.controler.events.IterationStartsEvent;
import org.matsim.core.controler.listener.IterationStartsListener;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleType;
import org.matsim.vehicles.VehicleUtils;

/**
 * A household drives the cars the census says it owns, and no more.
 *
 * <h2>The defect this exists for (DECISIONS.md 9.146)</h2>
 *
 * <p>Under {@code qsim.vehiclesSource=modeVehicleTypesFromVehiclesData},
 * PrepareForSim gives every person a car of their own, so a one-car household
 * can put two cars on the road at once. The census (B1) says how many vehicles
 * each household holds - {@code householdVehicles}, written by
 * build_matsim_plans.py from {@code household_vehicles} - and 33 % of
 * households hold fewer vehicles than licensed drivers. Measured at the F26
 * iteration-100 gate: 12,317 car legs began while every vehicle the household
 * owns was already out.
 *
 * <h2>What this does</h2>
 *
 * <p>Once, at the first iteration - AFTER PrepareForSim has created and mapped
 * the per-person vehicles, which is why this is not a StartupListener - every
 * licensed, car-available member of a household with {@code n >= 1} vehicles
 * is mapped, for {@code car}, to {@code hh<id>_car<k>} with {@code k} assigned
 * round-robin over the members in person-id order. A one-car household is then
 * EXACT: its drivers share one vehicle, and whoever wants it while it is out
 * waits for it under {@code qsim.vehicleBehavior=wait}. A multi-car household
 * is assigned rather than pooled - MATSim maps a person to ONE vehicle per
 * mode - so two drivers may still be told the same car while another stands
 * idle; that is stated here rather than hidden, and the one-car case is 81 %
 * of the measured excess. Nobody's plans, scores or modes are touched: the
 * constraint is physical, and the score pays for the wait. Under
 * {@code per_person} (B.population.vehicle_roster) nothing here runs.
 */
public final class HouseholdVehicleRoster implements IterationStartsListener {

    private static final Logger LOG = LogManager.getLogger(HouseholdVehicleRoster.class);

    /** Written by build_matsim_plans.py from B1 `household_vehicles`. */
    public static final String HOUSEHOLD_VEHICLES_ATTRIBUTE = "householdVehicles";
    /** The shared vehicle id: {@code hh<household>_car<k>}. */
    public static final String VEHICLE_ID_PREFIX = "hh";

    private final Scenario scenario;
    private final HouseholdVehiclesConfigGroup cfg;
    private boolean applied = false;

    @Inject
    HouseholdVehicleRoster(final Scenario scenario) {
        this.scenario = scenario;
        this.cfg = (HouseholdVehiclesConfigGroup) scenario.getConfig().getModules()
                .get(HouseholdVehiclesConfigGroup.NAME);
    }

    @Override
    public void notifyIterationStarts(final IterationStartsEvent event) {
        if (applied || cfg == null || !cfg.isCensusRoster()) {
            return;
        }
        applied = true;
        final VehicleType carType = scenario.getVehicles().getVehicleTypes()
                .get(Id.create(TransportMode.car, VehicleType.class));
        if (carType == null) {
            throw new IllegalStateException(
                    "householdVehicles.roster=census needs the `car` vehicle type "
                    + "the run inputs' vehicles file declares (RUN.qsim.car_vehicle)");
        }
        final Map<String, List<Person>> byHousehold = new HashMap<>();
        final Map<String, Integer> vehiclesOf = new HashMap<>();
        for (final Person person : scenario.getPopulation().getPersons().values()) {
            final Object hh = person.getAttributes()
                    .getAttribute(RidePairingEngine.HOUSEHOLD_ATTRIBUTE);
            final Object n = person.getAttributes()
                    .getAttribute(HOUSEHOLD_VEHICLES_ATTRIBUTE);
            if (hh == null || n == null) {
                continue;                          // boundary tiers, freight
            }
            final Object avail = person.getAttributes()
                    .getAttribute(EscortCoherenceListener.CAR_AVAIL);
            if (avail == null || !EscortCoherenceListener.CAR_ALWAYS
                    .equals(avail.toString())) {
                continue;                          // never drives: keeps its own
            }
            byHousehold.computeIfAbsent(hh.toString(), k -> new ArrayList<>())
                    .add(person);
            vehiclesOf.put(hh.toString(), Integer.parseInt(n.toString()));
        }
        int households = 0;
        int drivers = 0;
        int sharing = 0;                           // households with drivers > cars
        int created = 0;
        for (final Map.Entry<String, List<Person>> e : byHousehold.entrySet()) {
            final int n = vehiclesOf.getOrDefault(e.getKey(), 0);
            if (n <= 0) {
                continue;                          // car_available already denies
            }
            final List<Person> members = e.getValue();
            Collections.sort(members, (a, b) -> a.getId().compareTo(b.getId()));
            households++;
            if (members.size() > n) {
                sharing++;
            }
            for (int i = 0; i < members.size(); i++) {
                final Person driver = members.get(i);
                final Id<Vehicle> vid = Id.createVehicleId(
                        VEHICLE_ID_PREFIX + e.getKey() + "_car" + (i % n + 1));
                if (!scenario.getVehicles().getVehicles().containsKey(vid)) {
                    scenario.getVehicles().addVehicle(
                            VehicleUtils.createVehicle(vid, carType));
                    created++;
                }
                Map<String, Id<Vehicle>> map;
                try {
                    map = new HashMap<>(VehicleUtils.getVehicleIds(driver));
                } catch (final RuntimeException none) {
                    map = new HashMap<>();
                }
                map.put(TransportMode.car, vid);
                VehicleUtils.insertVehicleIdsIntoPersonAttributes(driver, map);
                drivers++;
            }
        }
        LOG.info("householdVehicles: roster=census - {} households, {} drivers "
                 + "mapped to {} shared cars; {} households hold fewer cars than "
                 + "drivers and will share (B.population.vehicle_roster, 9.146)",
                 households, drivers, created, sharing);
    }
}
