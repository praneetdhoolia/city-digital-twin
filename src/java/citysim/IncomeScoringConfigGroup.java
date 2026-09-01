package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `incomeScoring` config module: whether the synthesised census income
 * reaches money scoring (DECISIONS.md 9.138, issue #108).
 *
 * <p>Every value here is written by {@code build_matsim_run_inputs.py} from
 * {@code cities/<city>/registry/C_behaviour.json}. The income itself is DATA —
 * a weekly `income` attribute stamped on each resident by
 * {@code build_matsim_plans.py} from the person's census G17 band midpoint —
 * and the fields here only govern how MATSim core's own
 * {@code IndividualPersonScoringParameters} reads it: each resident's
 * marginalUtilityOfMoney becomes the subpopulation value x
 * (average income / personal income)^incomeExponent. The formula was read
 * from the pinned 2027.0 source, not from memory.
 *
 * <p>A person without a positive income (the Neg_Nil band) carries no
 * attribute and keeps the subpopulation value by that class's documented
 * fallback; the subpopulations named in {@code excludeSubpopulations}
 * (external, freight — agents that are volumes, not budgets) are excluded by
 * name. {@code representation = absent} recovers the flat
 * one-marginal-utility model byte-for-byte.
 */
public final class IncomeScoringConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "incomeScoring";

    public static final String REPRESENTATION_ABSENT = "absent";
    public static final String REPRESENTATION_PERSONAL =
            "person_marginal_utility_of_money";

    /** Sentinel meaning "the config never set it" — a Java default that
     * equals its registry value is right by accident (the
     * {@link TelemetryConfigGroup} lesson). */
    private static final double UNSET = -1.0;

    private String representation = REPRESENTATION_ABSENT;
    private double incomeExponent = UNSET;
    private String excludeSubpopulations = "";

    public IncomeScoringConfigGroup() {
        super(NAME);
    }

    public boolean isEnabled() {
        return REPRESENTATION_PERSONAL.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    @StringGetter("incomeExponent")
    public double getIncomeExponent() {
        return this.incomeExponent;
    }

    @StringSetter("incomeExponent")
    public void setIncomeExponent(final double value) {
        this.incomeExponent = value;
    }

    /** Comma-separated subpopulation names excluded from income scaling. */
    @StringGetter("excludeSubpopulations")
    public String getExcludeSubpopulations() {
        return this.excludeSubpopulations;
    }

    @StringSetter("excludeSubpopulations")
    public void setExcludeSubpopulations(final String value) {
        this.excludeSubpopulations = value == null ? "" : value.trim();
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!REPRESENTATION_ABSENT.equals(this.representation)
                && !REPRESENTATION_PERSONAL.equals(this.representation)) {
            throw new IllegalStateException(
                    "incomeScoring.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_ABSENT + " or "
                    + REPRESENTATION_PERSONAL + ". It is declared as "
                    + "C.income.representation.");
        }
        if (isEnabled() && this.incomeExponent <= 0.0) {
            throw new IllegalStateException(
                    "incomeScoring.incomeExponent was never set (or is <= 0), "
                    + "but incomeScoring.representation asks for per-person "
                    + "money scoring. It is declared as C.income.exponent; "
                    + "this class keeps no usable default, because a default "
                    + "equal to the declared value is right by accident.");
        }
    }
}
