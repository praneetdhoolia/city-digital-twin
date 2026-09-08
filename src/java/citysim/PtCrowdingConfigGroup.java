package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `ptCrowding` config module: whether in-vehicle crowding reaches PUBLIC
 * TRANSPORT SCORING (the Mode-Choice Ledger's rank-4 gap).
 *
 * <p><b>Why an extension is needed at all.</b> MATSim core scores no crowding
 * term. Two things in the stack look like one and are not: the mobsim's
 * capacity constraint is PHYSICAL - a vehicle at seats + standing room refuses
 * the next boarding - and SwissRailRaptor's
 * {@code CapacityDependentInVehicleCostCalculator} (enabled by
 * {@code swissRailRaptor.useCapacityConstraints}) prices a vehicle's load
 * factor inside the ROUTER's path cost, deciding which service a traveller
 * takes and not what the resulting plan is worth. So an agent could ride a
 * train at 146 of 146 for exactly the same score as one riding it empty, and
 * the C1 multipliers below were declared, swept, and read by nothing.
 *
 * <p><b>Every value here is written by {@code build_matsim_run_inputs.py}</b>
 * from {@code cities/<city>/registry/C_behaviour.json}: the two multipliers by
 * their own {@code matsim_param} bindings, and {@code penaltyUtilsPerHour} as
 * a derived value carrying its identity, exactly as {@code bikeStress} does.
 *
 * <p>{@code representation = absent} recovers the uncrowded model byte for
 * byte: nothing installs and no score event is emitted.
 *
 * @see PtCrowdingScoring
 */
public final class PtCrowdingConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "ptCrowding";

    public static final String REPRESENTATION_ABSENT = "absent";
    public static final String REPRESENTATION_IN_VEHICLE_TIME = "in_vehicle_time";

    /** Sentinel meaning "the config never set it" - a Java default that
     * equals its registry value is right by accident (the
     * {@link TelemetryConfigGroup} lesson, and what
     * {@code check_hardcoding.py}'s java-shadow-defaults test looks for). */
    private static final double UNSET = -1.0;

    private String representation = REPRESENTATION_ABSENT;
    private double seatedMultiplier = UNSET;
    private double standingMultiplier = UNSET;
    private double penaltyUtilsPerHour = UNSET;

    public PtCrowdingConfigGroup() {
        super(NAME);
    }

    public boolean isInVehicleTime() {
        return REPRESENTATION_IN_VEHICLE_TIME.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    /** What a minute SEATED in a vehicle at capacity costs relative to a
     * minute in an empty one. C.crowding.seated_multiplier. */
    @StringGetter("seatedMultiplier")
    public double getSeatedMultiplier() {
        return this.seatedMultiplier;
    }

    @StringSetter("seatedMultiplier")
    public void setSeatedMultiplier(final double value) {
        this.seatedMultiplier = value;
    }

    /** What a minute STANDING costs relative to a minute seated in an empty
     * vehicle. C.crowding.standing_multiplier. */
    @StringGetter("standingMultiplier")
    public double getStandingMultiplier() {
        return this.standingMultiplier;
    }

    @StringSetter("standingMultiplier")
    public void setStandingMultiplier(final double value) {
        this.standingMultiplier = value;
    }

    /** Utils per EXTRA felt hour aboard: trip-weighted VOT x
     * C.time_weights.beta_ivt x C.scoring.marginal_utility_of_money, derived
     * by the emitter and recorded in {@code _config.json} like every other
     * derived scoring value. It is the price of an in-vehicle hour, so a
     * multiplier of m makes an hour aboard cost m hours of it. */
    @StringGetter("penaltyUtilsPerHour")
    public double getPenaltyUtilsPerHour() {
        return this.penaltyUtilsPerHour;
    }

    @StringSetter("penaltyUtilsPerHour")
    public void setPenaltyUtilsPerHour(final double value) {
        this.penaltyUtilsPerHour = value;
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!REPRESENTATION_ABSENT.equals(this.representation)
                && !REPRESENTATION_IN_VEHICLE_TIME.equals(this.representation)) {
            throw new IllegalStateException(
                    "ptCrowding.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_ABSENT + " or "
                    + REPRESENTATION_IN_VEHICLE_TIME + ". It is declared as "
                    + "C.crowding.representation.");
        }
        if (!isInVehicleTime()) {
            return;
        }
        // No usable defaults, for the reason UNSET exists: a default that
        // equals the declared value is correct by accident and stays correct
        // only until someone sweeps the field.
        if (this.penaltyUtilsPerHour <= 0.0) {
            throw new IllegalStateException(
                    "ptCrowding.penaltyUtilsPerHour was never set (or is <= 0), "
                    + "but ptCrowding.representation is "
                    + REPRESENTATION_IN_VEHICLE_TIME + ". It is derived by "
                    + "build_matsim_run_inputs.py from the trip-weighted VOT, "
                    + "C.time_weights.beta_ivt and "
                    + "C.scoring.marginal_utility_of_money.");
        }
        if (this.seatedMultiplier < 1.0 || this.standingMultiplier < 1.0) {
            throw new IllegalStateException(
                    "ptCrowding.seatedMultiplier=" + this.seatedMultiplier
                    + " and ptCrowding.standingMultiplier="
                    + this.standingMultiplier + "; both are ratios to an "
                    + "uncrowded in-vehicle minute and neither may be below "
                    + "1.0 (a value below 1 would PAY people to ride a full "
                    + "vehicle). They are declared as "
                    + "C.crowding.seated_multiplier and "
                    + "C.crowding.standing_multiplier; the sentinel " + UNSET
                    + " means the config never carried them.");
        }
        if (this.standingMultiplier < this.seatedMultiplier) {
            throw new IllegalStateException(
                    "ptCrowding.standingMultiplier (" + this.standingMultiplier
                    + ") is below ptCrowding.seatedMultiplier ("
                    + this.seatedMultiplier + "): standing in a full vehicle "
                    + "cannot be more comfortable than sitting in it.");
        }
    }
}
