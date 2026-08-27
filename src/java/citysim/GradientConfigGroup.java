package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `gradient` config module: whether and how link gradient reaches walk
 * and bike travel time (DECISIONS.md 9.84, issue #21 reopened by 9.83).
 *
 * <p>Every value here is written by {@code build_matsim_run_inputs.py} from
 * {@code cities/<city>/registry/A_supply.json}. The grade itself is DATA — the
 * signed {@code grade_pct} link attribute stamped onto the run network from
 * the P2 elevation layers — and the fields here are the two published
 * grade-speed relations that convert it into a speed factor: the Tobler
 * hiking function for walk (Tobler 1993, the same function that produced the
 * A6 footway layer's own {@code walk_speed_factor} columns) and a linear
 * slowdown per grade percent for bike (Parkin &amp; Rotheram 2010).
 *
 * <p>Nothing here is a behavioural weight. A cyclist genuinely climbs slower;
 * the disutility of the extra time is priced by the mode's own scoring
 * parameters, exactly as before. {@code representation = absent} recovers the
 * flat-network behaviour byte-for-byte, which is what makes the mechanism's
 * effect measurable rather than assumed.
 */
public final class GradientConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "gradient";

    /** The link attribute the run-input builder stamps: signed percent grade
     * in the link's direction of travel, clamped by the declared
     * {@code A.gradient.grade_clamp_pct}. A link without it is flat. */
    public static final String GRADE_ATTRIBUTE = "grade_pct";

    public static final String REPRESENTATION_ABSENT = "absent";
    public static final String REPRESENTATION_LINK_SPEED = "link_speed";

    /** Sentinel meaning "the config never set it" — a Java default that
     * equals its registry value is right by accident (the
     * {@link TelemetryConfigGroup} lesson). */
    private static final double UNSET = -1.0;

    private String representation = REPRESENTATION_ABSENT;
    private double bikeUphillSlowdownPerPct = UNSET;
    private double bikeDownhillSpeedupPerPct = UNSET;
    private double bikeFloorFactor = UNSET;
    private double bikeCeilingFactor = UNSET;
    private double walkToblerSlopeCoeff = UNSET;
    private double walkToblerOffset = UNSET;

    public GradientConfigGroup() {
        super(NAME);
    }

    public boolean isLinkSpeed() {
        return REPRESENTATION_LINK_SPEED.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    @StringGetter("bikeUphillSlowdownPerPct")
    public double getBikeUphillSlowdownPerPct() {
        return this.bikeUphillSlowdownPerPct;
    }

    @StringSetter("bikeUphillSlowdownPerPct")
    public void setBikeUphillSlowdownPerPct(final double value) {
        this.bikeUphillSlowdownPerPct = value;
    }

    @StringGetter("bikeDownhillSpeedupPerPct")
    public double getBikeDownhillSpeedupPerPct() {
        return this.bikeDownhillSpeedupPerPct;
    }

    @StringSetter("bikeDownhillSpeedupPerPct")
    public void setBikeDownhillSpeedupPerPct(final double value) {
        this.bikeDownhillSpeedupPerPct = value;
    }

    @StringGetter("bikeFloorFactor")
    public double getBikeFloorFactor() {
        return this.bikeFloorFactor;
    }

    @StringSetter("bikeFloorFactor")
    public void setBikeFloorFactor(final double value) {
        this.bikeFloorFactor = value;
    }

    @StringGetter("bikeCeilingFactor")
    public double getBikeCeilingFactor() {
        return this.bikeCeilingFactor;
    }

    @StringSetter("bikeCeilingFactor")
    public void setBikeCeilingFactor(final double value) {
        this.bikeCeilingFactor = value;
    }

    @StringGetter("walkToblerSlopeCoeff")
    public double getWalkToblerSlopeCoeff() {
        return this.walkToblerSlopeCoeff;
    }

    @StringSetter("walkToblerSlopeCoeff")
    public void setWalkToblerSlopeCoeff(final double value) {
        this.walkToblerSlopeCoeff = value;
    }

    @StringGetter("walkToblerOffset")
    public double getWalkToblerOffset() {
        return this.walkToblerOffset;
    }

    @StringSetter("walkToblerOffset")
    public void setWalkToblerOffset(final double value) {
        this.walkToblerOffset = value;
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!REPRESENTATION_ABSENT.equals(this.representation)
                && !REPRESENTATION_LINK_SPEED.equals(this.representation)) {
            throw new IllegalStateException(
                    "gradient.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_ABSENT + " or "
                    + REPRESENTATION_LINK_SPEED + ". It is declared as "
                    + "A.gradient.representation.");
        }
        if (!isLinkSpeed()) {
            return;
        }
        require(this.bikeUphillSlowdownPerPct >= 0.0,
                "bikeUphillSlowdownPerPct",
                "A.gradient.bike_uphill_slowdown_per_pct");
        require(this.bikeDownhillSpeedupPerPct >= 0.0,
                "bikeDownhillSpeedupPerPct",
                "A.gradient.bike_downhill_speedup_per_pct");
        require(this.bikeFloorFactor > 0.0, "bikeFloorFactor",
                "A.gradient.bike_speed_floor_factor");
        require(this.bikeCeilingFactor >= 1.0, "bikeCeilingFactor",
                "A.gradient.bike_speed_ceiling_factor");
        require(this.walkToblerSlopeCoeff > 0.0, "walkToblerSlopeCoeff",
                "A.gradient.walk_tobler_slope_coeff");
        require(this.walkToblerOffset >= 0.0, "walkToblerOffset",
                "A.gradient.walk_tobler_offset");
    }

    private static void require(final boolean ok, final String param,
                                final String field) {
        if (!ok) {
            throw new IllegalStateException(
                    "gradient." + param + " was never set, but gradient."
                    + "representation is link_speed. It is declared as "
                    + field + " and written into the config by "
                    + "src/registry/param_config.py; this class keeps no "
                    + "usable default, because a default equal to the "
                    + "declared value is right by accident.");
        }
    }
}
