package citysim;

import java.util.LinkedHashSet;
import java.util.Set;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The {@code raptorModeCost} module: whether a PT SUBMODE'S OWN CONSTANT
 * reaches the router that picks the submode.
 *
 * <p><b>The gap this closes.</b> Under
 * {@code RUN.routing.pt_submode_scoring = per_submode} the emitted config
 * declares a {@code scoring.modeParams} block per submode, each with its own
 * {@code constant} — {@code bus} -1.05, {@code rail} -0.65, {@code tram}
 * -0.75, {@code ferry} -1.05 on the arm running when this was written. Those
 * constants reach SCORING. They do not reach the ROUTER. Read from the pinned
 * jar's bytecode, {@code RaptorUtils.createParameters} copies exactly one
 * per-mode value into {@link ch.sbb.matsim.routing.pt.raptor.RaptorParameters}
 * — {@code ModeParams.getMarginalUtilityOfTraveling()} — and
 * {@code SwissRailRaptorCore} then prices a boarded leg as
 * {@code DefaultRaptorInVehicleCostCalculator} does: in-vehicle seconds times
 * that one coefficient, and nothing else. The constant, the fare and any
 * distance term are invisible to it.
 *
 * <p>And the one per-submode value the raptor DOES read is emitted IDENTICALLY
 * for all four submodes ({@code marginalUtilityOfTraveling} -10.9608 each), so
 * in stock the raptor cannot tell a bus from a train except by time. That is
 * the mechanism behind the measurement in DECISIONS.md 9.160: over the F31
 * arm's whole plan memory, 974 of 154,347 persons (0.63 %) held plans that
 * differ in PT submode at all.
 *
 * <p><b>What this gate installs.</b>
 * {@link RaptorModeCostCalculator}, which is the default calculator plus the
 * boarded submode's own {@code scoring.modeParams} constant. It declares NO
 * number of its own: the constants are already declared as {@code C.asc.*} and
 * already emitted into {@code scoring.modeParams}, so the router is made
 * CONSISTENT WITH THE SCORING FUNCTION rather than given a second, separately
 * tunable set of tastes. There is nothing here to calibrate.
 *
 * <p><b>What it does NOT carry, and why.</b> The fare and a distance term were
 * designed into the same change and are not implementable at this hook.
 * {@code RaptorInVehicleCostCalculator.getInVehicleCost} is handed the
 * in-vehicle time, the marginal utility, the {@code Person}, the
 * {@code Vehicle}, the {@code RaptorParameters} and a
 * {@code RouteSegmentIterator} whose whole interface is
 * {@code hasNext/next/getInVehicleTime/getPassengerCount/getTimeOfDay}
 * (javap, pinned jar). No distance, and no stop or route identity from which
 * one could be recovered — and the published Opal schedule this project
 * charges is banded in KILOMETRES ({@link PtFareConfigGroup}), so a fare term
 * needs a distance the hook does not have. The fare is therefore still
 * charged where it can be: in scoring, by {@code citysim.PtFareChargeHandler},
 * on the route the agent actually rode.
 *
 * <p>{@code representation = absent} recovers the previous model exactly:
 * nothing binds, and the stock {@code DefaultRaptorInVehicleCostCalculator}
 * that {@code SwissRailRaptorModule} installs is left in place.
 *
 * @see RaptorModeCostCalculator
 */
public final class RaptorModeCostConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "raptorModeCost";

    public static final String REPRESENTATION_ABSENT = "absent";
    public static final String REPRESENTATION_MODE_CONSTANT = "mode_constant";

    private String representation = REPRESENTATION_ABSENT;

    public RaptorModeCostConfigGroup() {
        super(NAME);
    }

    public boolean isModeConstant() {
        return REPRESENTATION_MODE_CONSTANT.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    /**
     * The transit passenger modes this gate would price, {@code pt} excluded.
     *
     * <p>The umbrella mode is excluded because a constant applied to every
     * boarded leg alike discriminates between no two submodes; it only shifts
     * PT as a whole against the raptor's direct walk. That is a real effect
     * and not the control this gate exists to give, so a config that carries
     * only the umbrella mode is refused below rather than run.
     */
    static Set<String> pricedTransitModes(final Config config) {
        final Set<String> modes = new LinkedHashSet<>(config.transit().getTransitModes());
        modes.remove(TransportMode.pt);
        return modes;
    }

    /**
     * The declared {@code scoring.modeParams} blocks, READ ONLY.
     *
     * <p>{@code getModes()} is deprecated in favour of
     * {@code getOrCreateModeParams(mode)}, which is the wrong call here twice
     * over: it MUTATES the config, and a mode that was never declared would
     * come back as a fresh block whose constant is 0.0 — exactly the silent
     * zero the consistency check below exists to refuse. MATSim's own
     * {@code RaptorUtils.createParameters} reads the same map the same way.
     */
    @SuppressWarnings("deprecation")
    static java.util.Map<String, org.matsim.core.config.groups.ScoringConfigGroup.ModeParams>
            declaredModeParams(final Config config) {
        return config.scoring().getModes();
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!REPRESENTATION_ABSENT.equals(this.representation)
                && !REPRESENTATION_MODE_CONSTANT.equals(this.representation)) {
            throw new IllegalStateException(
                    "raptorModeCost.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_ABSENT + " or "
                    + REPRESENTATION_MODE_CONSTANT + ". It is declared as "
                    + "C.raptor.mode_cost_representation.");
        }
        if (!isModeConstant()) {
            return;
        }
        final Set<String> priced = pricedTransitModes(config);
        if (priced.isEmpty()) {
            throw new IllegalStateException(
                    "raptorModeCost.representation is "
                    + REPRESENTATION_MODE_CONSTANT + " but transit.transitModes "
                    + "carries only the umbrella mode " + TransportMode.pt
                    + ". One constant on every boarded leg alike separates no "
                    + "two submodes, so the gate would be on and control "
                    + "nothing. It needs the per-submode routing vocabulary: "
                    + "RUN.routing.pt_submode_scoring = per_submode.");
        }
        // A submode with no modeParams block would be priced at 0.0 while its
        // neighbours carry their constants - a silent, ASYMMETRIC change no
        // reader could see. The whole vocabulary must be declared or none.
        final Set<String> missing = new LinkedHashSet<>();
        for (final String mode : priced) {
            if (!declaredModeParams(config).containsKey(mode)) {
                missing.add(mode);
            }
        }
        if (!missing.isEmpty()) {
            throw new IllegalStateException(
                    "raptorModeCost.representation is "
                    + REPRESENTATION_MODE_CONSTANT + " but these declared "
                    + "transit modes have no scoring.modeParams block, so the "
                    + "router would price them at a constant of 0.0 while "
                    + "their neighbours carry theirs: " + missing
                    + ". The constants are declared as C.asc.* and emitted by "
                    + "build_matsim_run_inputs.py.");
        }
    }
}
