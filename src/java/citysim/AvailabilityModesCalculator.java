package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Set;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.config.Config;
import org.matsim.core.population.algorithms.PermissibleModesCalculator;
import org.matsim.core.population.algorithms.PermissibleModesCalculatorImpl;
import org.matsim.core.router.TripStructureUtils;

/**
 * Per-person mode availability, from attributes the plans builder derives or
 * declares. Successor to {@code RideAvailabilityModesCalculator}, which handled
 * `ride` alone.
 *
 * <p><b>`rideAvail`</b> (derived): MATSim's standard treatment lets any agent
 * become a car passenger on any trip. DECISIONS.md 9.7 and 9.10 measure what
 * that costs here: `ride` reaches 0.72 of legs against an observed 0.206,
 * putting 5.9 people in every car. A person may ride only if their B1 household
 * holds a vehicle AND contains another licence holder.
 *
 * <p><b>`bikeAvail`</b> (assumed, {@code B.population.bike_available_rate},
 * swept): until this existed, car was the only mode whose ownership was
 * modelled while bike was silently available to everyone — a structural bias
 * against car in the choice set itself, undeclared anywhere (issue #29,
 * DECISIONS.md 9.39).
 *
 * <p><b>`lockedMode`</b> (declared per agent tier): an agent whose demand is
 * anchored on an observed quantity of a specific mode — a through-traffic
 * vehicle seeded from a cordon road count (issue #20, DECISIONS.md 9.41) — must
 * not be handed a different mode by replanning, or the anchoring quantity
 * silently leaks. For such an agent the permissible set is the locked mode
 * alone.
 *
 * <p>Core MATSim can restrict `car` per person, through the `carAvail`
 * attribute honoured by {@link PermissibleModesCalculatorImpl}, but has no
 * equivalent for the others, and `subtourModeChoice.modes` is global. Absent
 * attributes retain the previous treatment. A population may also supply a
 * complete {@code permittedModes} set in the run's own mode vocabulary. It
 * restricts the existing choices and is checked against every initial plan;
 * its evidence and ownership allocation belong to the city's population build.
 *
 * <p><b>What this does not do.</b> It makes a mode available or not for a
 * person. It does NOT bind a passenger to a specific driver on a specific trip
 * at a specific time, so the model can still produce more passengers than there
 * are drivers to carry them at any given hour. That is what the socnetsim joint
 * plans contrib does (Dubernet and Axhausen), which is absent from the pinned
 * jar and out of scope. The residual is stated rather than hidden (issue #31).
 */
public final class AvailabilityModesCalculator implements PermissibleModesCalculator {

    /** Person attributes written by build_matsim_plans.py. */
    public static final String RIDE_ATTRIBUTE = "rideAvail";
    public static final String BIKE_ATTRIBUTE = "bikeAvail";
    public static final String LOCKED_ATTRIBUTE = "lockedMode";
    public static final String AGE_ATTRIBUTE = "age";
    /** Optional complete, comma-separated person-level choice set. This is
     * evidence supplied with the population, not a mode-share coefficient. */
    public static final String PERMITTED_ATTRIBUTE = "permittedModes";
    /** The one value that removes a mode; anything else leaves it available. */
    public static final String NEVER = "never";
    public static final String RIDE = "ride";
    public static final String BIKE = "bike";
    public static final String TAXI = "taxi";

    private final PermissibleModesCalculator delegate;
    private final int taxiMinAge;
    private final int bikeMinAge;
    private final Set<String> configuredModes;

    @Inject
    public AvailabilityModesCalculator(final Config config) {
        this.delegate = new PermissibleModesCalculatorImpl(config);
        this.configuredModes = new HashSet<>(Arrays.asList(config.subtourModeChoice().getModes()));
        this.configuredModes.addAll(config.routing().getNetworkModes());
        this.configuredModes.addAll(config.qsim().getMainModes());
        this.configuredModes.addAll(config.transit().getTransitModes());
        // The age gates (DECISIONS.md 9.84, issues #49/#50): taxi was gated
        // by NOTHING and `age` was written on every person and consulted by
        // nothing - 0-4 year olds hailed 19.5% and cycled 31.1% of their
        // trips on the F7 arm. Both thresholds are declared, swept,
        // labelled-assumed registry fields; an absent module leaves both
        // gates off, so a population run under an older config behaves as
        // before.
        final ModeAvailabilityConfigGroup gates = (ModeAvailabilityConfigGroup)
                config.getModules().get(ModeAvailabilityConfigGroup.NAME);
        this.taxiMinAge = gates == null ? 0 : gates.getTaxiMinAge();
        this.bikeMinAge = gates == null ? 0 : gates.getBikeMinAge();
    }

    private static int age(final Person person) {
        final Object value =
                person.getAttributes().getAttribute(AGE_ATTRIBUTE);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        // an agent without an age (a boundary tier run under an older
        // population) is not a child; the gates must not bite it
        return Integer.MAX_VALUE;
    }

    private static boolean never(final Person person, final String attribute) {
        final Object flag = person.getAttributes().getAttribute(attribute);
        return flag != null && NEVER.equals(flag.toString());
    }

    private Set<String> explicitModes(final Person person) {
        final Object raw = person.getAttributes().getAttribute(PERMITTED_ATTRIBUTE);
        if (raw == null) return null;
        if (!(raw instanceof String)) {
            throw new IllegalArgumentException("Person " + person.getId()
                    + ": permittedModes must be a comma-separated String");
        }
        final Set<String> allowed = new LinkedHashSet<>();
        for (String token : ((String) raw).split(",", -1)) {
            final String mode = token.trim();
            if (mode.isEmpty() || !configuredModes.contains(mode) || !allowed.add(mode)) {
                throw new IllegalArgumentException("Person " + person.getId()
                        + ": empty, duplicate or unconfigured permitted mode '" + mode + "'");
            }
        }
        return allowed;
    }

    /** Check all stored initial plans, including unselected alternatives.
     * Mode choice only constrains innovations; it cannot repair an illegal
     * plan which ChangeExpBeta could select later. Legacy populations without
     * the explicit attribute follow the existing path unchanged. */
    public static void validateExplicitPopulation(final Scenario scenario) {
        final AvailabilityModesCalculator calculator = new AvailabilityModesCalculator(scenario.getConfig());
        final PtSubmodeMainModeIdentifier fallback = new PtSubmodeMainModeIdentifier(scenario.getConfig());
        for (Person person : scenario.getPopulation().getPersons().values()) {
            if (person.getAttributes().getAttribute(PERMITTED_ATTRIBUTE) == null) continue;
            calculator.explicitModes(person);
            for (Plan plan : person.getPlans()) {
                final Collection<String> allowed = calculator.getPermissibleModes(plan);
                for (TripStructureUtils.Trip trip : TripStructureUtils.getTrips(plan)) {
                    final Set<String> routingModes = new HashSet<>();
                    for (Leg leg : trip.getLegsOnly()) {
                        final String mode = TripStructureUtils.getRoutingMode(leg);
                        if (mode != null) routingModes.add(mode);
                    }
                    if (routingModes.size() > 1) {
                        throw new IllegalArgumentException("Person " + person.getId()
                                + ": trip has conflicting routing modes " + routingModes);
                    }
                    final String mode = routingModes.isEmpty()
                            ? fallback.identifyMainMode(trip.getTripElements()) : routingModes.iterator().next();
                    if (!allowed.contains(mode)) {
                        throw new IllegalArgumentException("Person " + person.getId()
                                + ": stored plan uses unavailable mode " + mode);
                    }
                }
            }
        }
    }

    @Override
    public Collection<String> getPermissibleModes(final Plan plan) {
        final Collection<String> modes = this.delegate.getPermissibleModes(plan);
        final Person person = plan.getPerson();
        if (person == null) {
            return modes;
        }
        final Set<String> explicit = explicitModes(person);
        final Object locked = person.getAttributes().getAttribute(LOCKED_ATTRIBUTE);
        if (locked != null) {
            final String mode = locked.toString();
            if (explicit != null && !explicit.contains(mode)) {
                throw new IllegalArgumentException("Person " + person.getId()
                        + ": lockedMode contradicts permittedModes: " + mode);
            }
            // the locked mode even if the delegate would deny it: the lock is
            // the agent's definition, not a preference
            return Collections.singletonList(mode);
        }
        final int years = (this.taxiMinAge > 0 || this.bikeMinAge > 0)
                ? age(person) : Integer.MAX_VALUE;
        final boolean noRide = never(person, RIDE_ATTRIBUTE);
        final boolean noBike = never(person, BIKE_ATTRIBUTE)
                || years < this.bikeMinAge;
        final boolean noTaxi = years < this.taxiMinAge;
        if (!noRide && !noBike && !noTaxi && explicit == null) {
            return modes;
        }
        final Collection<String> out = new ArrayList<>(modes.size());
        for (final String mode : modes) {
            if (explicit != null && !explicit.contains(mode)) continue;
            if ((noRide && RIDE.equals(mode)) || (noBike && BIKE.equals(mode))
                    || (noTaxi && TAXI.equals(mode))) {
                continue;
            }
            out.add(mode);
        }
        return out;
    }
}
