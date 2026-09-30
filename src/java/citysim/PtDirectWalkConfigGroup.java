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

    /** RUN.transit_router.no_route_walk: what a pt request the raptor cannot
     *  serve at all is answered with. {@code network_walk} is F38 exactly: the
     *  network walk, whatever its length. {@code refused_beyond_reach}: a walk
     *  longer than {@link #noRouteWalkReachM} is still returned (the plan must
     *  stay executable for PersonPrepareForSim and the mobsim) but its legs
     *  carry {@link NetworkDirectWalkPtRouter#UNSERVED_ATTRIBUTE}, and
     *  {@link PtUnservedScoring} scores the plan that executes it as MATSim
     *  scores a plan it could not execute (the stuck penalty). */
    public static final String NO_ROUTE_NETWORK_WALK = "network_walk";
    public static final String NO_ROUTE_REFUSED = "refused_beyond_reach";

    @Parameter("noRouteWalk")
    public String noRouteWalk = NO_ROUTE_NETWORK_WALK;

    /** RUN.transit_router.no_route_walk_reach_m (derived): the routed walk
     *  distance beyond which a no-route answer is refused. */
    @Parameter("noRouteWalkReachM")
    public double noRouteWalkReachM = 0.0;

    public PtDirectWalkConfigGroup() {
        super(NAME);
    }

    /** True when a no-route walk beyond the declared reach is refused. */
    public boolean refusesBeyondReach() {
        return NO_ROUTE_REFUSED.equals(this.noRouteWalk);
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
        final String n = this.noRouteWalk == null ? NO_ROUTE_NETWORK_WALK
                : this.noRouteWalk.trim();
        if (!NO_ROUTE_NETWORK_WALK.equals(n) && !NO_ROUTE_REFUSED.equals(n)) {
            throw new IllegalArgumentException(
                    "ptDirectWalk.noRouteWalk must be " + NO_ROUTE_NETWORK_WALK
                    + " or " + NO_ROUTE_REFUSED
                    + " (RUN.transit_router.no_route_walk); got '"
                    + this.noRouteWalk + "'");
        }
        this.noRouteWalk = n;
        if (NO_ROUTE_REFUSED.equals(n)) {
            if (!NETWORK.equals(v)) {
                throw new IllegalArgumentException(
                        "ptDirectWalk.noRouteWalk=" + NO_ROUTE_REFUSED
                        + " needs basis=" + NETWORK + ": only the network"
                        + " direct-walk router answers a no-route request");
            }
            if (!(this.noRouteWalkReachM > 0.0)) {
                throw new IllegalArgumentException(
                        "ptDirectWalk.noRouteWalk=" + NO_ROUTE_REFUSED
                        + " needs a positive noRouteWalkReachM"
                        + " (RUN.transit_router.no_route_walk_reach_m); got "
                        + this.noRouteWalkReachM);
            }
        }
    }
}
