package citysim;

import org.matsim.core.config.ReflectiveConfigGroup;
import org.matsim.core.config.ReflectiveConfigGroup.Parameter;

/**
 * How the PT router evaluates the DIRECT WALK it compares every transit
 * route against (DECISIONS.md 9.121, issue #94).
 *
 * <p>SwissRailRaptor builds its direct-walk alternative from the beeline
 * distance and {@code transitRouter.beelineWalkSpeed}, scaled by
 * {@code transitRouter.directWalkFactor}, and returns that walk whenever it
 * is cheaper than the best transit route. A beeline crosses water. Measured
 * on the F16 arm at iteration 10: of 110 CBD-bound trips in Stockton-side
 * residents' PT plans, the router returned a walk-only route for 88 - a
 * ~1 km beeline across the harbour that the network then executes as the
 * ~20 km road detour - a bus for 20 and the ferry for 1.
 *
 * <p>{@code basis = network}: the raptor is kept from answering with its
 * own direct walk, the direct walk is routed on the walk network by the
 * {@code walk} routing module, and the raptor's comparison is applied to
 * THAT walk's time with the same declared {@code directWalkFactor}. Nothing
 * else moves. {@code basis = beeline}: the stock behaviour.
 *
 * <p>Registry: {@code RUN.transit_router.direct_walk_basis} binds to
 * {@code ptDirectWalk.basis}; the factor is
 * {@code RUN.transit_router.direct_walk_factor} on
 * {@code transitRouter.directWalkFactor}.
 */
public final class PtDirectWalkConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "ptDirectWalk";
    public static final String BEELINE = "beeline";
    public static final String NETWORK = "network";

    @Parameter("basis")
    public String basis = BEELINE;

    public PtDirectWalkConfigGroup() {
        super(NAME);
    }

    public String getBasis() {
        return this.basis;
    }

    public boolean isNetwork() {
        return NETWORK.equals(this.basis);
    }

    /** The rule the removed setter applied: only the two declared members
     *  (RUN.transit_router.direct_walk_basis) are a basis (#180). */
    @Override
    public void checkConsistency(final org.matsim.core.config.Config config) {
        super.checkConsistency(config);
        final String v = this.basis == null ? BEELINE : this.basis.trim();
        if (!BEELINE.equals(v) && !NETWORK.equals(v)) {
            throw new IllegalArgumentException(
                    "ptDirectWalk.basis must be " + BEELINE + " or " + NETWORK
                    + " (RUN.transit_router.direct_walk_basis); got '"
                    + this.basis + "'");
        }
        this.basis = v;
    }
}
