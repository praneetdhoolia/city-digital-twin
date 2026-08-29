package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `modeAvailability` config module: the age gates on taxi and bike
 * (DECISIONS.md 9.84, issues #49 and #50).
 *
 * <p>Measured motivation (9.83, F7 arm at iteration 150): taxi was gated by
 * NOTHING — 0–4 year olds hailed 19.5% of their trips — and `age` was written
 * on every person and consulted by nothing, while 0–4 year olds cycled 31.1%
 * of theirs. No mode-by-age cell exists in the held data, so both thresholds
 * are ASSUMED, declared in the registry with a sweep whose zero disables the
 * gate, and never fitted.
 *
 * <p>Both values are written by {@code build_matsim_run_inputs.py} from
 * {@code cities/<city>/registry/B_demand.json} and consumed by
 * {@link AvailabilityModesCalculator} against the person's own `age`
 * attribute. A config without this module leaves both gates off — absent
 * bindings must not switch a mechanism on.
 */
public final class ModeAvailabilityConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "modeAvailability";

    private int taxiMinAge = 0;
    private int bikeMinAge = 0;
    /** NaN until the config sets it. The DECLARED value is 0.0 (the bound
     *  disabled), so a Java default of 0.0 would be right by accident and
     *  would hide a wiring that had stopped working - which is exactly what
     *  check_hardcoding.py refuses. NaN cannot be mistaken for a decision. */
    private double walkFeasibleKm = Double.NaN;
    private double bikeFeasibleKm = Double.NaN;

    public ModeAvailabilityConfigGroup() {
        super(NAME);
    }

    /** Minimum age at which `taxi` is in the choice set; 0 disables the
     * gate. Declared as {@code B.taxi.min_unaccompanied_age}. */
    /**
     * The straight-line trip distance beyond which walk is not OFFERED.
     *
     * <p>Not a preference and not a penalty - a feasibility bound. Scoring can
     * express that a long walk is bad; it cannot express that it is not a thing
     * people do, and at 0.0 (the reproducing value) the model will hand an
     * agent a sixty-kilometre walk and charge them fifteen hours for it. Zero
     * disables the bound and reproduces every arm before 9.106.
     */
    @StringGetter("walkFeasibleKm")
    public double getWalkFeasibleKm() {
        return this.walkFeasibleKm;
    }

    @StringSetter("walkFeasibleKm")
    public void setWalkFeasibleKm(final double value) {
        this.walkFeasibleKm = value;
    }

    /** The same bound for bike; zero disables it. */
    @StringGetter("bikeFeasibleKm")
    public double getBikeFeasibleKm() {
        return this.bikeFeasibleKm;
    }

    @StringSetter("bikeFeasibleKm")
    public void setBikeFeasibleKm(final double value) {
        this.bikeFeasibleKm = value;
    }

    @StringGetter("taxiMinAge")
    public int getTaxiMinAge() {
        return this.taxiMinAge;
    }

    @StringSetter("taxiMinAge")
    public void setTaxiMinAge(final int value) {
        this.taxiMinAge = value;
    }

    /** Minimum age at which `bike` is in the choice set; 0 disables the
     * gate. Declared as {@code B.population.bike_min_age}, composing with
     * the CWANZ ownership draw ({@code B.population.bike_available_rate}). */
    @StringGetter("bikeMinAge")
    public int getBikeMinAge() {
        return this.bikeMinAge;
    }

    @StringSetter("bikeMinAge")
    public void setBikeMinAge(final int value) {
        this.bikeMinAge = value;
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (Double.isNaN(this.walkFeasibleKm)
                || Double.isNaN(this.bikeFeasibleKm)) {
            throw new IllegalStateException(
                    "modeAvailability.walkFeasibleKm / bikeFeasibleKm were "
                    + "never set, so the reach bound is not wired. They are "
                    + "declared as B.mode.walk_feasible_km and "
                    + "B.mode.bike_feasible_km; zero disables a bound, which "
                    + "is a decision the config must state rather than one a "
                    + "Java default may make silently.");
        }
        if (this.walkFeasibleKm < 0.0 || this.bikeFeasibleKm < 0.0) {
            throw new IllegalStateException(
                    "modeAvailability reach bounds cannot be negative: "
                    + "walkFeasibleKm=" + this.walkFeasibleKm
                    + ", bikeFeasibleKm=" + this.bikeFeasibleKm + ".");
        }
        if (this.taxiMinAge < 0 || this.bikeMinAge < 0) {
            throw new IllegalStateException(
                    "modeAvailability age gates cannot be negative: taxiMinAge="
                    + this.taxiMinAge + ", bikeMinAge=" + this.bikeMinAge
                    + ". They are declared as B.taxi.min_unaccompanied_age "
                    + "and B.population.bike_min_age; zero disables a gate.");
        }
    }
}
