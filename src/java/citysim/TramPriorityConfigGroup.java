package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `tramPriority` config module: how the corridor's explicit signals treat
 * an approaching tram (issue #73, DECISIONS.md 9.73-9.75).
 *
 * <p>Every value here is written from the registry by the run-input builder.
 * None of them may be typed into a script, and following the lesson
 * {@link RidePairingConfigGroup} records from {@code TelemetryConfigGroup}:
 * no parameter keeps a usable Java default. A default that EQUALS its registry
 * value is right by accident, passes every test, and silently stops being
 * right the moment anyone sweeps the field. {@link #checkConsistency} refuses
 * a run whose binding was lost instead.
 *
 * <p>This class lives in {@code src/java_signals/} because it exists only for
 * the signal-enabled entry point; it deliberately imports NOTHING from the
 * signals contrib, so the base stack could compile it — it is kept out of
 * {@code src/java/} so the base artefact carries no signal vocabulary at all.
 *
 * <p>See {@link TramPriorityController} for what each mode does.
 */
public final class TramPriorityConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "tramPriority";

    /** Sentinel meaning "the config never set it", NOT a usable value. */
    private static final double UNSET = -1.0;

    /** The four regimes `mode` may take, in increasing strength. */
    public static final String MODE_OFF = "off";
    public static final String MODE_GREEN_EXTENSION = "green_extension";
    public static final String MODE_EXTENSION_RECALL = "extension_recall";
    public static final String MODE_CONDITIONAL = "conditional";

    private String mode = "";
    private double extensionWindowS = UNSET;
    private double detectionDistanceM = UNSET;
    private double priorityBudgetShare = UNSET;
    private boolean compensationEnabled = false;
    private double latenessThresholdS = UNSET;

    public TramPriorityConfigGroup() {
        super(NAME);
    }

    /**
     * Which priority regime the corridor controllers run.
     *
     * <p>{@code off} executes every fixed-time plan verbatim — byte-for-byte
     * the behaviour of {@code DefaultPlanbasedSignalSystemController} — so a
     * signal run without priority is comparable to one with it within one
     * build. {@code green_extension} may only delay a tram-stage dropping;
     * {@code extension_recall} may additionally truncate a competing stage and
     * recall the tram stage early; {@code conditional} grants either action
     * only to a tram already late by more than {@link #getLatenessThresholdS}.
     */
    @StringGetter("mode")
    public String getMode() {
        return this.mode;
    }

    @StringSetter("mode")
    public void setMode(final String value) {
        this.mode = value == null ? "" : value.trim();
    }

    /**
     * How many seconds before its scheduled dropping a green tram stage may
     * still be held green for a detected tram, and the maximum length of that
     * hold, in seconds.
     */
    @StringGetter("extensionWindowS")
    public double getExtensionWindowS() {
        return this.extensionWindowS;
    }

    @StringSetter("extensionWindowS")
    public void setExtensionWindowS(final double value) {
        this.extensionWindowS = value;
    }

    /**
     * The declared upstream detection distance, in metres.
     *
     * <p>DOCUMENTED APPROXIMATION: MATSim's queue model has no intra-link
     * vehicle position, so a detector "X metres upstream of the stop line"
     * cannot be placed literally. Detection fires when a transit vehicle
     * ENTERS the tram approach link — i.e. at the approach link's upstream
     * boundary — which stands in for the declared distance. The value is
     * carried so the registry sweep range stays attached to the run that used
     * it and so a future lane-resolved corridor can honour it literally; the
     * present mechanism does not vary with it.
     */
    @StringGetter("detectionDistanceM")
    public double getDetectionDistanceM() {
        return this.detectionDistanceM;
    }

    @StringSetter("detectionDistanceM")
    public void setDetectionDistanceM(final double value) {
        this.detectionDistanceM = value;
    }

    /**
     * The maximum share of one cycle the priority machinery may borrow from
     * competing stages within that cycle, dimensionless in [0, 1].
     *
     * <p>This is the Melbourne PU/AU-style stability bound: however many trams
     * arrive, the cross-street cannot lose more than this share of its cycle,
     * so fixed-time coordination degrades gracefully instead of collapsing.
     */
    @StringGetter("priorityBudgetShare")
    public double getPriorityBudgetShare() {
        return this.priorityBudgetShare;
    }

    @StringSetter("priorityBudgetShare")
    public void setPriorityBudgetShare(final double value) {
        this.priorityBudgetShare = value;
    }

    /**
     * Whether time borrowed from a competing stage in one cycle is returned
     * to that stage in the next cycle, out of the tram stage's slack, so the
     * plan's long-run green splits are conserved.
     *
     * <p>Boolean with a false default is acceptable here where the doubles
     * refuse one: false is not a magnitude that could drift from the registry,
     * it is the absence of the mechanism, the same contract as
     * {@code ridePairing.enabled}.
     */
    @StringGetter("compensationEnabled")
    public boolean isCompensationEnabled() {
        return this.compensationEnabled;
    }

    @StringSetter("compensationEnabled")
    public void setCompensationEnabled(final boolean value) {
        this.compensationEnabled = value;
    }

    /**
     * Schedule delay, in seconds, beyond which a detected tram earns priority
     * under {@code mode=conditional}. Unused by every other mode.
     *
     * <p>Delay is taken from the transit events' own bookkeeping
     * ({@code VehicleArrivesAtFacilityEvent#getDelay()} at the stop the tram
     * most recently touched), never from a parallel clock of ours.
     */
    @StringGetter("latenessThresholdS")
    public double getLatenessThresholdS() {
        return this.latenessThresholdS;
    }

    @StringSetter("latenessThresholdS")
    public void setLatenessThresholdS(final double value) {
        this.latenessThresholdS = value;
    }

    /**
     * Refuse a priority module whose regime or magnitudes were never bound.
     *
     * <p>The module being PRESENT in a signal run's config is itself the
     * declaration that a regime was chosen; a missing parameter means the
     * registry binding was lost, and the one thing that must not then happen
     * is for the run to continue on a number nobody chose.
     */
    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        // The group is materialised on EVERY stack (this MATSim refuses an
        // unmaterialised module outright - measured on the first detached
        // smoke probe), so a config in which nothing ever set a tramPriority
        // value is a legitimate non-signal run, not a lost binding. Only a
        // PARTIALLY bound module is the defect the checks below refuse.
        if (this.mode.isEmpty() && this.extensionWindowS == UNSET
                && this.detectionDistanceM == UNSET
                && this.priorityBudgetShare == UNSET
                && this.latenessThresholdS == UNSET) {
            return;
        }
        require(!this.mode.isEmpty(), "mode", "A.signals.tsp.mode");
        if (!MODE_OFF.equals(this.mode)
                && !MODE_GREEN_EXTENSION.equals(this.mode)
                && !MODE_EXTENSION_RECALL.equals(this.mode)
                && !MODE_CONDITIONAL.equals(this.mode)) {
            throw new IllegalStateException(
                    "tramPriority.mode is '" + this.mode + "', which is not one "
                    + "of " + MODE_OFF + ", " + MODE_GREEN_EXTENSION + ", "
                    + MODE_EXTENSION_RECALL + ", " + MODE_CONDITIONAL + ".");
        }
        if (MODE_OFF.equals(this.mode)) {
            // Pure fixed time reads none of the magnitudes; leaving them unset
            // in an off run is legitimate (the registry only binds what the
            // regime uses).
            return;
        }
        require(this.extensionWindowS >= 0.0, "extensionWindowS",
                "A.signals.tsp.extension_window_s");
        require(this.detectionDistanceM >= 0.0, "detectionDistanceM",
                "A.signals.tsp.detection_distance_m");
        require(this.priorityBudgetShare >= 0.0
                        && this.priorityBudgetShare <= 1.0,
                "priorityBudgetShare", "A.signals.tsp.priority_budget_share");
        if (MODE_CONDITIONAL.equals(this.mode)) {
            require(this.latenessThresholdS >= 0.0, "latenessThresholdS",
                    "A.signals.tsp.lateness_threshold_s");
        }
    }

    private static void require(final boolean ok, final String param,
                                final String field) {
        if (!ok) {
            throw new IllegalStateException(
                    "tramPriority." + param + " was never set (or is out of "
                    + "range), but the tramPriority module is present. It is "
                    + "declared as " + field + " in the registry and written "
                    + "into the config by the run-input builder; this class "
                    + "keeps no usable default, because a default equal to the "
                    + "declared value is right by accident.");
        }
    }
}
