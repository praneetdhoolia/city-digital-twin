package citysim;

import org.matsim.core.config.ReflectiveConfigGroup;

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
 */
public final class PtDirectWalkConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "ptDirectWalk";
    public static final String BEELINE = "beeline";
    public static final String NETWORK = "network";

    private String basis = BEELINE;

    public PtDirectWalkConfigGroup() {
        super(NAME);
    }

    @StringGetter("basis")
    public String getBasis() {
        return this.basis;
    }

    @StringSetter("basis")
    public void setBasis(final String value) {
        final String v = value == null ? BEELINE : value.trim();
        if (!BEELINE.equals(v) && !NETWORK.equals(v)) {
            throw new IllegalArgumentException(
                    "ptDirectWalk.basis must be `beeline` or `network`, got `"
                            + value + "`");
        }
        this.basis = v;
    }

    public boolean isNetwork() {
        return NETWORK.equals(this.basis);
    }
}
