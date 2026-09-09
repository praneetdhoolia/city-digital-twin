package citysim;

import ch.sbb.matsim.routing.pt.raptor.RaptorInVehicleCostCalculator;
import ch.sbb.matsim.routing.pt.raptor.RaptorParameters;
import com.google.inject.Inject;
import com.google.inject.Singleton;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.config.Config;
import org.matsim.core.config.groups.ScoringConfigGroup;
import org.matsim.vehicles.Vehicle;

/**
 * The stock in-vehicle cost, plus the boarded submode's own scoring constant
 * (DECISIONS.md 9.160, issue #49).
 *
 * <p><b>Why the router needed this at all.</b> SwissRailRaptor decides which
 * service a PT traveller takes, and therefore WHICH SUBMODE the traveller
 * ends up on: the mode-choice operator proposes {@code pt}, and the raptor
 * alone turns that into a bus, a train, a tram or a ferry. Its objective, in
 * stock, is
 * {@code DefaultRaptorInVehicleCostCalculator}: {@code inVehicleTime *
 * -marginalUtilityOfTravelTime_utl_s}, and nothing else. The per-submode
 * constants that {@code scoring.modeParams} carries are not in it, so the
 * router chooses between submodes as though every taste were equal. See
 * {@link RaptorModeCostConfigGroup} for the bytecode evidence and for the two
 * terms that CANNOT go here.
 *
 * <p><b>The value added is not a new value.</b> It is
 * {@code -modeParams.getConstant()} for the submode of the vehicle boarded —
 * the same constant the scoring function charges the same leg, declared once
 * as {@code C.asc.*}. The sign flips because
 * {@code getInVehicleCost} returns a COST (a disutility: the default returns
 * {@code time * -marginalUtility}, and the marginal utility of travel time is
 * negative), while a mode constant is a UTILITY. Nothing here is tunable
 * independently of scoring, which is the point: the router is being made
 * consistent with the objective the plan is later scored against, not given a
 * second set of tastes.
 *
 * <p><b>Where the constant lands.</b> Read from the pinned jar,
 * {@code SwissRailRaptorCore} calls this once per CANDIDATE ALIGHTING STOP
 * along a boarded route, and each call is handed the in-vehicle time from the
 * boarding stop to that candidate — the whole ride, not an increment — with
 * the result ADDED to the cost accumulated at boarding. So a constant added
 * here is charged exactly ONCE PER BOARDED LEG whichever alighting stop wins,
 * and, being equal across the candidates of one boarding, it cannot distort
 * the choice of alighting stop within a leg. It discriminates between legs on
 * different submodes, and between one boarding and two. (The brief's shorter
 * phrasing, "the call is once per boarding", is true of where the constant
 * lands and not of how often the method runs; this class keeps no per-call
 * state, so the difference costs nothing.)
 *
 * <p><b>It also shifts PT against direct walk.</b> The raptor compares a PT
 * path's cost against a direct walk, so charging every boarded leg a negative
 * constant as a positive cost makes PT dearer against walking than it was.
 * That is the same direction scoring already takes — walk's constant is
 * +0.35 against PT's -1.05 on the arm this was written against — and it is a
 * real change in behaviour, not a neutral one, which is why it ships behind a
 * gate with {@code absent} as the shipped value.
 *
 * <p><b>Threading.</b> MATSim routes on many threads against ONE injected
 * instance ({@code SwissRailRaptorFactory} holds a single
 * {@code RaptorInVehicleCostCalculator}). The price table is built once in the
 * constructor and never written again; the only mutable field is a concurrent
 * set used to log each unpriced vehicle type once.
 *
 * @see RaptorModeCostConfigGroup
 */
@Singleton
public final class RaptorModeCostCalculator implements RaptorInVehicleCostCalculator {

    private static final Logger LOG =
            LogManager.getLogger(RaptorModeCostCalculator.class);

    /** Submode (a vehicle type's networkMode) -> the COST of boarding it. */
    private final Map<String, Double> costByMode;

    /** Vehicle types already reported as unpriced, so the log says it once. */
    private final Set<String> unpricedReported = ConcurrentHashMap.newKeySet();

    @Inject
    public RaptorModeCostCalculator(final Config config) {
        final Map<String, Double> costs = new LinkedHashMap<>();
        for (final String mode : RaptorModeCostConfigGroup.pricedTransitModes(config)) {
            final ScoringConfigGroup.ModeParams params =
                    RaptorModeCostConfigGroup.declaredModeParams(config).get(mode);
            if (params == null) {
                // checkConsistency refuses this before the run starts; if the
                // group were ever installed without it, refusing here is still
                // better than pricing one submode at zero beside its priced
                // neighbours.
                throw new IllegalStateException(
                        "no scoring.modeParams for declared transit mode '"
                        + mode + "', so " + RaptorModeCostConfigGroup.NAME
                        + " has no constant to price it with.");
            }
            costs.put(mode, -params.getConstant());
        }
        this.costByMode = Collections.unmodifiableMap(costs);
        LOG.info("{}: pricing {} PT submode(s) by their own scoring constant: {}",
                RaptorModeCostCalculator.class.getSimpleName(),
                this.costByMode.size(), this.costByMode);
    }

    @Override
    public double getInVehicleCost(
            final double inVehicleTime,
            final double marginalUtilityOfTravelTime_utl_s,
            final Person person,
            final Vehicle vehicle,
            final RaptorParameters parameters,
            final RouteSegmentIterator iterator) {
        // DefaultRaptorInVehicleCostCalculator, restated: the whole point of
        // the gate is that `absent` and this differ by the constant alone.
        final double timeCost = inVehicleTime * -marginalUtilityOfTravelTime_utl_s;
        return timeCost + modeCost(vehicle);
    }

    /**
     * The boarded submode's cost, or 0.0 when the vehicle cannot name one.
     *
     * <p>The submode is the transit vehicle type's own {@code networkMode} —
     * {@code bus}, {@code rail}, {@code tram}, {@code ferry} in the mapped
     * schedule — which is the same vocabulary {@code scoring.modeParams} is
     * keyed by. Nothing is typed here: a city whose feeds carry other modes
     * prices them by the same identity.
     */
    private double modeCost(final Vehicle vehicle) {
        if (vehicle == null || vehicle.getType() == null
                || !vehicle.getType().hasNetworkMode()) {
            return 0.0;
        }
        final String mode = vehicle.getType().getNetworkMode();
        final Double cost = this.costByMode.get(mode);
        if (cost == null) {
            if (this.unpricedReported.add(mode)) {
                LOG.warn("{}: vehicle type networkMode '{}' is not a declared "
                        + "transit mode, so it is priced at the stock cost. "
                        + "Declared: {}",
                        RaptorModeCostCalculator.class.getSimpleName(),
                        mode, this.costByMode.keySet());
            }
            return 0.0;
        }
        return cost;
    }
}
