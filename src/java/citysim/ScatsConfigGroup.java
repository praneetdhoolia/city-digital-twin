package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `scats` config module: the parameters of the SCATS adaptive control
 * algorithm (DECISIONS.md 9.88, issue #73).
 *
 * <p>SCATS phase data for this corridor was never released — a formal TfNSW
 * request stands unanswered — and the project's earlier handling was to leave
 * {@code A.signals.scats_phasing} unobtained and SWEEP a fixed cycle time. The
 * standing directive now forbids that: an unavailable input must be DERIVED,
 * and for signalling that means implementing the control ALGORITHM rather than
 * guessing the timings it would have produced. A fixed 110 s plan is not what
 * a SCATS intersection does; SCATS re-times itself every cycle against
 * measured saturation, and an adaptive intersection and a fixed-time one
 * differ most exactly where this study looks — corridor run time and the
 * queues the light rail sits in.
 *
 * <p>This class lives in {@code src/java/} for the reason
 * {@link TramPriorityConfigGroup} records: the `scats` module is emitted into
 * EVERY config (its fields are registry-bound, so the reach probe must see
 * them move), and MATSim REFUSES an unmaterialised config group at its
 * consistency check. It imports nothing from the signals contrib, so the base
 * compile stays clean; the CONTROLLER that acts on it exists only in
 * {@code src/java_signals/}.
 *
 * <p>Every value here is written from the registry by the run-input builder.
 * Following the lesson {@link TramPriorityConfigGroup} records: no parameter
 * keeps a usable Java default, because a default that EQUALS its registry
 * value is right by accident and stops being right the moment anyone sweeps
 * the field. {@link #checkConsistency} refuses a run whose binding was lost.
 *
 * <p>What each parameter means in the algorithm is documented on its getter,
 * and the algorithm itself in {@link ScatsSignalController}.
 */
public final class ScatsConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "scats";

    /** Sentinel meaning "the config never set it", NOT a usable value. */
    private static final double UNSET = -1.0;

    /** Fixed-time: execute the generated plan verbatim. */
    public static final String REGIME_FIXED_TIME = "fixed_time";
    /** Re-time cycle and splits every cycle from measured saturation. */
    public static final String REGIME_SCATS = "scats_adaptive";

    private String regime = "";
    private double targetDegreeSaturation = UNSET;
    private double dsDeadband = UNSET;
    private double cycleStepS = UNSET;
    private double minCycleS = UNSET;
    private double maxCycleS = UNSET;
    private double dsSmoothing = UNSET;
    private double saturationFlowVehHLane = UNSET;
    private double minGreenS = UNSET;

    public ScatsConfigGroup() {
        super(NAME);
    }

    /**
     * Which control regime the signal systems run.
     *
     * <p>{@code fixed_time} executes the generated plan exactly, which is the
     * behaviour every arm before DECISIONS.md 9.88 measured, so the two are
     * comparable within one build. {@code scats_adaptive} keeps the generated
     * plan as the STARTING point and re-times it each cycle.
     */
    @StringGetter("regime")
    public String getRegime() {
        return this.regime;
    }

    @StringSetter("regime")
    public void setRegime(final String value) {
        this.regime = value == null ? "" : value.trim();
    }

    public boolean isScats() {
        return REGIME_SCATS.equals(this.regime);
    }

    /**
     * The degree of saturation SCATS holds the CRITICAL movement near.
     *
     * <p>The core of SCATS's cycle-length logic: the system lengthens the
     * cycle while the busiest movement is running above this, and shortens it
     * while every movement is below it. Published descriptions of SCATS
     * operation put the working target near 0.9 — high enough to use the
     * intersection, low enough to leave recovery room.
     */
    @StringGetter("targetDegreeSaturation")
    public double getTargetDegreeSaturation() {
        return this.targetDegreeSaturation;
    }

    @StringSetter("targetDegreeSaturation")
    public void setTargetDegreeSaturation(final double value) {
        this.targetDegreeSaturation = value;
    }

    /**
     * The band around the target inside which the cycle is left alone.
     *
     * <p>Without it the cycle would hunt: every cycle would move by a step in
     * one direction or the other, because a measured DS is never exactly the
     * target. SCATS is deliberately sluggish, and this is that sluggishness.
     */
    @StringGetter("dsDeadband")
    public double getDsDeadband() {
        return this.dsDeadband;
    }

    @StringSetter("dsDeadband")
    public void setDsDeadband(final double value) {
        this.dsDeadband = value;
    }

    /**
     * The most the cycle length may move in ONE cycle, in seconds.
     *
     * <p>SCATS changes cycle length incrementally rather than jumping to a
     * computed optimum, so that coordination with neighbouring intersections
     * is not destroyed by a single noisy measurement.
     */
    @StringGetter("cycleStepS")
    public double getCycleStepS() {
        return this.cycleStepS;
    }

    @StringSetter("cycleStepS")
    public void setCycleStepS(final double value) {
        this.cycleStepS = value;
    }

    /** Shortest cycle the controller may choose, in seconds. */
    @StringGetter("minCycleS")
    public double getMinCycleS() {
        return this.minCycleS;
    }

    @StringSetter("minCycleS")
    public void setMinCycleS(final double value) {
        this.minCycleS = value;
    }

    /** Longest cycle the controller may choose, in seconds. */
    @StringGetter("maxCycleS")
    public double getMaxCycleS() {
        return this.maxCycleS;
    }

    @StringSetter("maxCycleS")
    public void setMaxCycleS(final double value) {
        this.maxCycleS = value;
    }

    /**
     * Exponential smoothing weight on the NEW cycle's measured DS.
     *
     * <p>SCATS does not re-time from a single cycle's counts; it filters them.
     * 1.0 would react to the last cycle alone (noisy at low flow, which is
     * most of the day), 0.0 would never react at all.
     */
    @StringGetter("dsSmoothing")
    public double getDsSmoothing() {
        return this.dsSmoothing;
    }

    @StringSetter("dsSmoothing")
    public void setDsSmoothing(final double value) {
        this.dsSmoothing = value;
    }

    /**
     * Saturation flow per lane, vehicles per hour of green.
     *
     * <p>The denominator of the degree of saturation: what a lane WOULD have
     * discharged had the green been fully used. Declared once in the registry
     * and shared with the plan generator, so the measurement and the plan that
     * produced it cannot drift apart.
     */
    @StringGetter("saturationFlowVehHLane")
    public double getSaturationFlowVehHLane() {
        return this.saturationFlowVehHLane;
    }

    @StringSetter("saturationFlowVehHLane")
    public void setSaturationFlowVehHLane(final double value) {
        this.saturationFlowVehHLane = value;
    }

    /**
     * The shortest green any stage may be cut to, in seconds.
     *
     * <p>A safety floor, not a tuning knob: a re-timing that starves a
     * movement below the pedestrian and clearance minimum is not a re-timing
     * a real controller would execute.
     */
    @StringGetter("minGreenS")
    public double getMinGreenS() {
        return this.minGreenS;
    }

    @StringSetter("minGreenS")
    public void setMinGreenS(final double value) {
        this.minGreenS = value;
    }

    @Override
    protected void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (this.regime.isEmpty()) {
            throw new IllegalStateException(
                    "scats.regime was never set: the run-input builder writes "
                    + "it from A.signals.control_regime. Refusing to run on a "
                    + "regime nobody chose.");
        }
        if (!REGIME_FIXED_TIME.equals(this.regime) && !isScats()) {
            throw new IllegalStateException(
                    "scats.regime must be '" + REGIME_FIXED_TIME + "' or '"
                    + REGIME_SCATS + "', not '" + this.regime + "'");
        }
        if (!isScats()) {
            return;                       // nothing below is read under fixed time
        }
        requirePositive("targetDegreeSaturation", this.targetDegreeSaturation);
        requirePositive("cycleStepS", this.cycleStepS);
        requirePositive("minCycleS", this.minCycleS);
        requirePositive("maxCycleS", this.maxCycleS);
        requirePositive("saturationFlowVehHLane", this.saturationFlowVehHLane);
        requirePositive("minGreenS", this.minGreenS);
        if (this.dsDeadband < 0 || this.dsSmoothing < 0) {
            throw new IllegalStateException(
                    "scats.dsDeadband and scats.dsSmoothing must be set and "
                    + "non-negative; the run-input builder writes both");
        }
        if (this.dsSmoothing > 1.0) {
            throw new IllegalStateException(
                    "scats.dsSmoothing is a weight on the newest measurement "
                    + "and cannot exceed 1.0 (got " + this.dsSmoothing + ")");
        }
        if (this.minCycleS >= this.maxCycleS) {
            throw new IllegalStateException(
                    "scats.minCycleS (" + this.minCycleS + ") must be below "
                    + "scats.maxCycleS (" + this.maxCycleS + ")");
        }
    }

    private static void requirePositive(final String name, final double v) {
        if (v <= 0) {
            throw new IllegalStateException(
                    "scats." + name + " was never set (or is not positive): "
                    + "the run-input builder writes it from the registry, and "
                    + "this class keeps no usable default on purpose - a "
                    + "default that happens to equal the declared value is "
                    + "right by accident and stops being right the moment the "
                    + "field is swept");
        }
    }
}
