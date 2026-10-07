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
 *
 * <p>Under {@code householdVehicles.motorcycle = household} (D28, F39;
 * RUN.qsim.motorcycle_roster) the same roster maps a household's riders to
 * its one motorcycle, {@code hh<id>_moto1} ({@link #rosterMotorcycles}); under
 * {@code per_person} no motorcycle is mapped and F38 is recovered exactly.
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
        if (cfg == null || !cfg.anyRoster()) {
            return;
        }
        final long started = System.currentTimeMillis();
        final boolean first = !applied;
        applied = true;
        if (cfg.isCensusRoster()) {
            rosterCars(event, first);
        }
        if (cfg.isHouseholdMotorcycle()) {
            rosterMotorcycles(event, first);
        }
        // One line per listener per iteration, in the one shape every citysim
        // listener logs it, so the performance lane can attribute the phase
        // from matsim.log alone (sixteenth report).
        LOG.info("householdVehicles: it.{} iterationStarts listener=HouseholdVehicleRoster ms={}",
                 event.getIteration(), System.currentTimeMillis() - started);
    }

    /** The census car roster (9.146), exactly as it ran before D28. */
    private void rosterCars(final IterationStartsEvent event, final boolean first) {
        // 9.148: asserted before EVERY mobsim, not once. A 1 % smoke under the
        // once-only version died in iteration 1 asking for a person-id car:
        // something between iterations had put the per-person mapping back,
        // and a fresh route then carried it. Re-mapping 155k persons costs
        // well under a second; the log line says how many mappings it had
        // to restore, so a rewrite by any other component is visible.
        //
        // MEASURED, 12 September 2026 (eighth project report, area 6, asked
        // what rewrites the mapping): the restore line was printed 0 times
        // across the 300 iterations of 20260909T015217_300it_25pct and the
        // 98 of aborted_20260910T222830_300it_25pct, and `javap` over the
        // pinned jar finds ONE writer of the per-person vehicle map -
        // PrepareForSimImpl.createAndAddVehiclesForEveryNetworkMode, run
        // once at controler start, before iteration 0. So the once-only
        // version died because it ran BEFORE PrepareForSim overwrote its
        // work, not because anything fights the roster between iterations;
        // the per-iteration pass is kept as the guard it is, and a restore
        // after iteration 0 is now a WARN that names the person and the id
        // it found, so a writer that ever appears can be traced.
        final VehicleType carType = scenario.getVehicles().getVehicleTypes()
                .get(Id.create(TransportMode.car, VehicleType.class));
        if (carType == null) {
            throw new IllegalStateException(
                    "householdVehicles.roster=census needs the `car` vehicle type "
                    + "the run inputs' vehicles file declares (RUN.qsim.car_vehicle)");
        }
        final Map<String, List<Person>> byHousehold = new HashMap<>();
        final Map<String, Integer> vehiclesOf = new HashMap<>();
        collectDrivers(byHousehold, vehiclesOf);
        final Pass p = new Pass(event.getIteration(), first, carType);
        for (final Map.Entry<String, List<Person>> e : byHousehold.entrySet()) {
            final int n = vehiclesOf.getOrDefault(e.getKey(), 0);
            if (n <= 0) {
                continue;                          // car_available already denies
            }
            rosterHousehold(p, e.getKey(), e.getValue(), n);
        }
        if (first) {
            LOG.info("householdVehicles: roster=census - {} households, {} drivers "
                     + "mapped to {} shared cars; {} households hold fewer cars than "
                     + "drivers and will share (B.population.vehicle_roster, 9.146)",
                     p.households, p.drivers, p.created, p.sharing);
        } else if (p.restored > 0) {
            LOG.info("householdVehicles: iteration {} - {} of {} driver mappings "
                     + "had been put back to a person-owned car and were restored "
                     + "(9.148)", event.getIteration(), p.restored, p.drivers);
        }
    }

    /** The shared motorcycle's id: {@code hh<household>_moto1}. */
    public static final String MOTORCYCLE_SUFFIX = "_moto1";

    /**
     * The household motorcycle (D28, F39; RUN.qsim.motorcycle_roster =
     * household): every rider of a household - a member whose
     * {@code motorbikeAvail} is not {@code never}, i.e. who holds a rider
     * licence in a household the plans builder drew a motorcycle for - is
     * mapped, for {@code motorbike}, to ONE shared {@code hh<id>_moto1}.
     *
     * <p>ONE, because that is what the plans carry: the builder draws
     * possession per household by the Poisson at-least-one identity (9.214,
     * {@code B.population.household_motorcycle_share}), so a household holds a
     * motorcycle or does not, and every rider of it sees the same one. Two
     * riders of one household then cannot ride it at once: the second waits
     * for it ({@link HouseholdCarDepartureHandler}), as a second driver waits
     * for a one-car household's car. Mirrors the car roster: asserted before
     * every mobsim, created once, restores counted.
     */
    private void rosterMotorcycles(final IterationStartsEvent event, final boolean first) {
        final VehicleType motoType = scenario.getVehicles().getVehicleTypes()
                .get(Id.create(AvailabilityModesCalculator.MOTORBIKE, VehicleType.class));
        if (motoType == null) {
            throw new IllegalStateException(
                    "householdVehicles.motorcycle=household needs the `motorbike` vehicle "
                    + "type the run inputs' vehicles file declares (RUN.qsim.main_mode)");
        }
        final Map<String, List<Person>> byHousehold = new HashMap<>();
        for (final Person person : scenario.getPopulation().getPersons().values()) {
            final Object hh = person.getAttributes()
                    .getAttribute(RidePairingEngine.HOUSEHOLD_ATTRIBUTE);
            final Object avail = person.getAttributes()
                    .getAttribute(AvailabilityModesCalculator.MOTORBIKE_ATTRIBUTE);
            if (hh == null || avail == null
                    || AvailabilityModesCalculator.NEVER.equals(avail.toString())) {
                continue;                          // no rider, or no household
            }
            byHousehold.computeIfAbsent(hh.toString(), k -> new ArrayList<>()).add(person);
        }
        final Pass p = new Pass(event.getIteration(), first, motoType);
        for (final Map.Entry<String, List<Person>> e : byHousehold.entrySet()) {
            final List<Person> riders = e.getValue();
            Collections.sort(riders, (a, b) -> a.getId().compareTo(b.getId()));
            p.households++;
            if (riders.size() > 1) {
                p.sharing++;
            }
            final Id<Vehicle> vid = Id.createVehicleId(
                    VEHICLE_ID_PREFIX + e.getKey() + MOTORCYCLE_SUFFIX);
            if (!scenario.getVehicles().getVehicles().containsKey(vid)) {
                scenario.getVehicles().addVehicle(VehicleUtils.createVehicle(vid, motoType));
                p.created++;
            }
            for (final Person rider : riders) {
                mapShared(p, rider, AvailabilityModesCalculator.MOTORBIKE, vid);
            }
        }
        if (first) {
            LOG.info("householdVehicles: motorcycle=household - {} households, {} riders "
                     + "mapped to {} shared motorcycles; {} households hold more riders than "
                     + "their one motorcycle and will share (RUN.qsim.motorcycle_roster, D28)",
                     p.households, p.drivers, p.created, p.sharing);
        } else if (p.restored > 0) {
            LOG.info("householdVehicles: iteration {} - {} of {} rider mappings had been put "
                     + "back to a person-owned motorbike and were restored",
                     event.getIteration(), p.restored, p.drivers);
        }
    }

    /** Map one member, for one mode, to the household's shared vehicle. */
    private static void mapShared(final Pass p, final Person member, final String mode,
                                  final Id<Vehicle> vid) {
        Map<String, Id<Vehicle>> map;
        try {
            map = new HashMap<>(VehicleUtils.getVehicleIds(member));
        } catch (final RuntimeException none) {
            map = new HashMap<>();
        }
        if (!vid.equals(map.get(mode))) {
            if (p.restored == 0 && !p.first) {
                LOG.warn("householdVehicles: iteration {} - person {} carried {} vehicle {} "
                         + "instead of the roster's {}; SOMETHING REWROTE THE MAPPING "
                         + "BETWEEN ITERATIONS (9.148)", p.iteration, member.getId(), mode,
                         map.get(mode), vid);
            }
            p.restored++;
        }
        map.put(mode, vid);
        VehicleUtils.insertVehicleIdsIntoPersonAttributes(member, map);
        p.drivers++;
    }

    /**
     * One roster pass: what it needs from the event and the tallies its log
     * line reports. notifyIterationStarts held these as locals in one
     * 112-line method until 27 September 2026 (fourteenth report,
     * recommendation 9).
     */
    private static final class Pass {
        final int iteration;
        final boolean first;
        final VehicleType carType;
        int households = 0;
        int drivers = 0;
        int sharing = 0;                           // households with drivers > cars
        int created = 0;
        int restored = 0;                          // 9.148: mappings put back

        Pass(final int iteration, final boolean first, final VehicleType carType) {
            this.iteration = iteration;
            this.first = first;
            this.carType = carType;
        }
    }

    /** Every licensed, car-available household member, by household, and the
     *  vehicles the census gives that household. */
    private void collectDrivers(final Map<String, List<Person>> byHousehold,
                                final Map<String, Integer> vehiclesOf) {
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
    }

    /** Map one household's drivers, in person-id order, round-robin onto its
     *  `n` shared cars, creating any car the vehicles container lacks. */
    private void rosterHousehold(final Pass p, final String household,
                                 final List<Person> members, final int n) {
        Collections.sort(members, (a, b) -> a.getId().compareTo(b.getId()));
        p.households++;
        if (members.size() > n) {
            p.sharing++;
        }
        for (int i = 0; i < members.size(); i++) {
            final Person driver = members.get(i);
            final Id<Vehicle> vid = Id.createVehicleId(
                    VEHICLE_ID_PREFIX + household + "_car" + (i % n + 1));
            if (!scenario.getVehicles().getVehicles().containsKey(vid)) {
                scenario.getVehicles().addVehicle(
                        VehicleUtils.createVehicle(vid, p.carType));
                p.created++;
            }
            Map<String, Id<Vehicle>> map;
            try {
                map = new HashMap<>(VehicleUtils.getVehicleIds(driver));
            } catch (final RuntimeException none) {
                map = new HashMap<>();
            }
            if (!vid.equals(map.get(TransportMode.car))) {
                if (p.restored == 0 && !p.first) {
                    LOG.warn("householdVehicles: iteration {} - person {} "
                             + "carried car vehicle {} instead of the roster's "
                             + "{}; SOMETHING REWROTE THE MAPPING BETWEEN "
                             + "ITERATIONS (9.148 - measured 0 times over "
                             + "398 iterations to 12 Sep 2026; PrepareForSim "
                             + "is the only writer in the pinned jar)",
                             p.iteration, driver.getId(),
                             map.get(TransportMode.car), vid);
                }
                p.restored++;
            }
            map.put(TransportMode.car, vid);
            VehicleUtils.insertVehicleIdsIntoPersonAttributes(driver, map);
            p.drivers++;
        }
    }
}
