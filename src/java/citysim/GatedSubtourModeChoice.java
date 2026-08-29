package citysim;

import com.google.inject.Inject;
import com.google.inject.Provider;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.core.config.groups.GlobalConfigGroup;
import org.matsim.core.config.groups.SubtourModeChoiceConfigGroup;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.population.algorithms.PermissibleModesCalculator;
import org.matsim.core.population.algorithms.PlanAlgorithm;
import org.matsim.core.replanning.PlanStrategy;
import org.matsim.core.replanning.PlanStrategyImpl;
import org.matsim.core.replanning.modules.ReRoute;
import org.matsim.core.replanning.selectors.RandomPlanSelector;
import org.matsim.core.router.TripRouter;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Trip;
import org.matsim.core.utils.geometry.CoordUtils;
import org.matsim.core.utils.timing.TimeInterpretation;
import org.matsim.facilities.ActivityFacilities;

/**
 * {@code SubtourModeChoice} that cannot hand out a mode the person may not
 * use (DECISIONS.md 9.84, issues #49, #50; the 9.15 defect class).
 *
 * <h2>The stock seam this closes</h2>
 *
 * <p>With {@code subtourModeChoice.probaForRandomSingleTripMode} &gt; 0, the
 * stock module flips a coin and changes a SINGLE trip's mode through
 * {@code ChooseRandomSingleLegMode} — which is constructed from the raw
 * non-chain mode array and never consults {@link PermissibleModesCalculator}
 * (read from the pinned jar's bytecode: the calculator gates only the
 * subtour choice-set path). Every per-person availability rule is therefore
 * porous on exactly half the mode innovations at the declared 0.5: measured
 * on the first F9 probe at iteration 8, 747 taxi trips — 5.5% of all taxi —
 * were made by under-18s the {@code modeAvailability} gate had barred, spread
 * uniformly over ages 0–17. The same seam has leaked `ride` to persons with
 * nobody to drive them since the availability rule existed; that leak was
 * invisible because an unpaired ride re-modes to walk and prices itself out.
 *
 * <h2>What this does</h2>
 *
 * <p>The strategy is the stock chain — random plan selector, the stock
 * {@code SubtourModeChoice} module, {@code ReRoute} — with one addition: after
 * the stock algorithm runs, any trip now carrying a mode the calculator does
 * not permit for this plan is REVERTED to its pre-innovation main mode. The
 * single-trip path changes exactly one trip, so the revert restores the plan
 * to its (valid) pre-innovation state and the refused draw becomes a no-op;
 * the subtour path draws from the calculator-filtered choice set and can
 * never trigger it. <b>When nothing is impermissible the wrapper changes
 * nothing</b> — stock behaviour is recovered exactly, which is what makes its
 * effect measurable. No draw is re-rolled and no distribution is reweighted:
 * an illegal proposal is refused, never replaced.
 */
public final class GatedSubtourModeChoice implements Provider<PlanStrategy> {

    @Inject
    private Provider<TripRouter> tripRouterProvider;
    @Inject
    private GlobalConfigGroup globalConfigGroup;
    @Inject
    private SubtourModeChoiceConfigGroup subtourModeChoiceConfigGroup;
    @Inject
    private ActivityFacilities facilities;
    @Inject
    private PermissibleModesCalculator permissibleModesCalculator;
    @Inject
    private TimeInterpretation timeInterpretation;

    @Inject
    private ModeAvailabilityConfigGroup availability;

    @Override
    public PlanStrategy get() {
        final PlanStrategyImpl.Builder builder =
                new PlanStrategyImpl.Builder(new RandomPlanSelector<>());
        // The two bounds applied here are the declared registry fields
        // B.mode.walk_feasible_km and B.mode.bike_feasible_km, reaching this
        // class through ModeAvailabilityConfigGroup's accessors rather than by
        // name. Both are 0.0 - DISABLED and measured worse (9.106) - and the
        // keys are spelled out so the registry's `consumers` claim about this
        // file is verifiable by text and not merely by intent.
        builder.addStrategyModule(new GatedModule(
                globalConfigGroup, subtourModeChoiceConfigGroup,
                permissibleModesCalculator,
                availability.getWalkFeasibleKm(),
                availability.getBikeFeasibleKm()));
        builder.addStrategyModule(new ReRoute(
                facilities, tripRouterProvider, globalConfigGroup,
                timeInterpretation));
        return builder.build();
    }

    /** The stock module with the post-run permissibility enforcement. */
    static final class GatedModule
            extends org.matsim.core.replanning.modules.SubtourModeChoice {

        private final PermissibleModesCalculator calc;
        private final double walkFeasibleM;
        private final double bikeFeasibleM;

        GatedModule(final GlobalConfigGroup global,
                    final SubtourModeChoiceConfigGroup config,
                    final PermissibleModesCalculator calc,
                    final double walkFeasibleKm,
                    final double bikeFeasibleKm) {
            super(global, config, calc);
            this.calc = calc;
            this.walkFeasibleM = walkFeasibleKm * 1000.0;
            this.bikeFeasibleM = bikeFeasibleKm * 1000.0;
        }

        /**
         * Whether this trip is beyond the declared reach of the mode proposed.
         *
         * <p>Measured on the straight line between the two activities, which is
         * a LOWER bound on what the agent would actually cover, so a trip
         * refused here is refused on a distance it certainly exceeds. A bound of
         * zero is off.
         */
        private boolean beyondReach(final String mode, final Trip trip) {
            final double limit = TransportMode.walk.equals(mode) ? walkFeasibleM
                    : TransportMode.bike.equals(mode) ? bikeFeasibleM : 0.0;
            if (Double.isNaN(limit) || limit <= 0.0) {
                return false;
            }
            final Coord a = trip.getOriginActivity().getCoord();
            final Coord b = trip.getDestinationActivity().getCoord();
            if (a == null || b == null) {
                return false;
            }
            return CoordUtils.calcEuclideanDistance(a, b) > limit;
        }

        @Override
        public PlanAlgorithm getPlanAlgoInstance() {
            final PlanAlgorithm inner = super.getPlanAlgoInstance();
            return new PlanAlgorithm() {
                @Override
                public void run(final Plan plan) {
                    // the pre-innovation main mode of each trip, by its
                    // routing mode - present on every routed leg, and the
                    // identity ReRoute itself routes by
                    final List<Trip> before = TripStructureUtils.getTrips(plan);
                    final List<String> oldModes = new ArrayList<>(before.size());
                    for (final Trip t : before) {
                        final List<Leg> legs = t.getLegsOnly();
                        String m = legs.isEmpty() ? null
                                : TripStructureUtils.getRoutingMode(legs.get(0));
                        if (m == null && !legs.isEmpty()) {
                            m = legs.get(0).getMode();
                        }
                        oldModes.add(m);
                    }
                    inner.run(plan);
                    final List<Trip> after = TripStructureUtils.getTrips(plan);
                    if (after.size() != before.size()) {
                        return;   // structure changed: not the single-trip path
                    }
                    // A reach refusal rejects the ENTIRE proposal. Putting
                    // one trip of a subtour back would leave that subtour
                    // mixing chain- and non-chain-based modes, which MATSim
                    // refuses with an IllegalStateException - measured, and it
                    // kills the run at the first iteration. The pre-innovation
                    // plan is consistent by construction, so restoring all of
                    // it is the only safe refusal.
                    boolean infeasible = false;
                    for (final Trip t : after) {
                        final List<Leg> legs = t.getLegsOnly();
                        if (!legs.isEmpty()
                                && beyondReach(legs.get(0).getMode(), t)) {
                            infeasible = true;
                            break;
                        }
                    }
                    if (infeasible) {
                        for (int i = 0; i < after.size(); i++) {
                            final String old = oldModes.get(i);
                            final Trip t = after.get(i);
                            final List<Leg> legs = t.getLegsOnly();
                            if (old == null || legs.isEmpty()
                                    || old.equals(legs.get(0).getMode())) {
                                continue;
                            }
                            final Leg leg = PopulationUtils.createLeg(old);
                            TripStructureUtils.setRoutingMode(leg, old);
                            TripRouter.insertTrip(
                                    plan, t.getOriginActivity(),
                                    Collections.singletonList(leg),
                                    t.getDestinationActivity());
                        }
                        return;
                    }

                    final Collection<String> allowed =
                            calc.getPermissibleModes(plan);
                    for (int i = 0; i < after.size(); i++) {
                        final Trip t = after.get(i);
                        final List<Leg> legs = t.getLegsOnly();
                        if (legs.size() != 1) {
                            continue;              // untouched, still routed
                        }
                        final String mode = legs.get(0).getMode();
                        final String old = oldModes.get(i);
                        if (allowed.contains(mode) || old == null
                                || old.equals(mode)) {
                            continue;
                        }
                        final Leg leg = PopulationUtils.createLeg(old);
                        TripStructureUtils.setRoutingMode(leg, old);
                        TripRouter.insertTrip(
                                plan, t.getOriginActivity(),
                                Collections.singletonList(leg),
                                t.getDestinationActivity());
                    }
                }
            };
        }
    }
}
