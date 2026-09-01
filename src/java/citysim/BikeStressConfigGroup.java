package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `bikeStress` config module: whether motor-traffic stress reaches
 * cycling (DECISIONS.md 9.138, issue #107).
 *
 * <p>Every value here is written by {@code build_matsim_run_inputs.py} from
 * {@code cities/<city>/registry/A_supply.json}. The stress itself is DATA —
 * a {@code bike_stress_factor} link attribute stamped onto the run network
 * from the declared road-class mapping and the Broach, Dill &amp; Gliebe 2012
 * felt-distance equivalents — and the one field here prices the extra felt
 * time: riding a link whose factor is f makes its traversal feel like f times
 * its actual duration, and the surplus (f - 1) x time is charged at
 * {@code penaltyUtilsPerHour}, the same trip-weighted
 * VOT x marginalUtilityOfMoney identity the transfer penalty uses.
 *
 * <p>The factor reaches the model twice, deliberately: in SCORE (through
 * {@link BikeStressScoring}, so mode choice feels a hostile road) and in the
 * ROUTER's link cost (through {@link BikeStressDisutility}, so a cyclist who
 * still rides detours to the quiet street, which is what the GPS study
 * measured people doing). {@code representation = absent} recovers the
 * fearless-bike model byte-for-byte.
 */
public final class BikeStressConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "bikeStress";

    /** The link attribute the run-input builder stamps: felt-distance
     * multiplier for cycling on this link. A link without it is stress-free
     * (factor 1.0). */
    public static final String STRESS_ATTRIBUTE = "bike_stress_factor";

    public static final String REPRESENTATION_ABSENT = "absent";
    public static final String REPRESENTATION_FELT_TIME = "felt_time";

    /** Sentinel meaning "the config never set it" — a Java default that
     * equals its registry value is right by accident (the
     * {@link TelemetryConfigGroup} lesson). */
    private static final double UNSET = -1.0;

    private String representation = REPRESENTATION_ABSENT;
    private double penaltyUtilsPerHour = UNSET;

    public BikeStressConfigGroup() {
        super(NAME);
    }

    public boolean isFeltTime() {
        return REPRESENTATION_FELT_TIME.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    /** Utils per felt EXTRA hour of cycling on a stressed link:
     * trip-weighted VOT x C.time_weights.beta_bike_mode x
     * marginalUtilityOfMoney, derived by the emitter and recorded in
     * {@code _config.json} like every other derived scoring value. */
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
                && !REPRESENTATION_FELT_TIME.equals(this.representation)) {
            throw new IllegalStateException(
                    "bikeStress.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_ABSENT + " or "
                    + REPRESENTATION_FELT_TIME + ". It is declared as "
                    + "A.bike_stress.representation.");
        }
        if (isFeltTime() && this.penaltyUtilsPerHour <= 0.0) {
            throw new IllegalStateException(
                    "bikeStress.penaltyUtilsPerHour was never set (or is "
                    + "<= 0), but bikeStress.representation is felt_time. It "
                    + "is derived by build_matsim_run_inputs.py from the "
                    + "trip-weighted VOT, C.time_weights.beta_bike_mode and "
                    + "C.scoring.marginal_utility_of_money; this class keeps "
                    + "no usable default, because a default equal to the "
                    + "derived value is right by accident.");
        }
    }
}
