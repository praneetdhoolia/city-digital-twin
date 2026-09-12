package citysim;

import org.matsim.core.config.ReflectiveConfigGroup;
import org.matsim.core.config.ReflectiveConfigGroup.Parameter;

/**
 * Declares the per-trip fare charge for the point-to-point priced mode
 * (issue #49, task 4.7.8). Every value here is EMITTED by the registry-driven
 * config builder from declared fields - the flagfall is the blend of the
 * measured taxi Hiring Charge and the literature rideshare base at the
 * declared rideshare share - so nothing in this class or its consumer decides
 * a number. The per-KILOMETRE half of the fare does not pass through here at
 * all: it is native MATSim scoring ({@code monetaryDistanceRate} on the taxi
 * modeParams).
 */
public final class FareConfigGroup extends ReflectiveConfigGroup {

    public static final String GROUP_NAME = "fare";

    @Parameter("flagfall")
    public double flagfall = 0.0;
    @Parameter("mode")
    public String mode = "";

    public FareConfigGroup() {
        super(GROUP_NAME);
    }

    public double getFlagfall() {
        return this.flagfall;
    }

    public String getMode() {
        return this.mode;
    }

    /** The module is live only when a mode is named and the flagfall is set. */
    public boolean isEnabled() {
        return !this.mode.isEmpty() && this.flagfall > 0.0;
    }
}
