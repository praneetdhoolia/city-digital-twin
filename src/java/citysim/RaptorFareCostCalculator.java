package citysim;

import ch.sbb.matsim.routing.pt.raptor.DefaultRaptorInVehicleCostCalculator;
import ch.sbb.matsim.routing.pt.raptor.RaptorInVehicleCostCalculator;
import ch.sbb.matsim.routing.pt.raptor.RaptorParameters;
import com.google.inject.Inject;
import com.google.inject.Singleton;
import java.lang.reflect.Field;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.scoring.functions.ScoringParametersForPerson;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.vehicles.Vehicle;

/** Adds one whole-ride fare before RAPTOR prunes candidate alighting paths.
 * The read-only adapter targets the pinned engine ABI, and fails closed on
 * changes. It never advances or mutates the engine's segment iterator.
 * Distance excludes the boarding link and includes the alighting link, as do
 * the LinkEnter events used by BoardingFareHandler. Native probes guard this
 * contract and income-sensitive route choice across engine upgrades.
 */
@Singleton
public final class RaptorFareCostCalculator implements RaptorInVehicleCostCalculator {
    private final BoardingFareTable fares;
    private final ScoringParametersForPerson scoring;
    private final RaptorInVehicleCostCalculator delegate;
    private final Class<?> iteratorType;
    private final Field data, from, to, stops, distance, line, route;

    @Inject
    public RaptorFareCostCalculator(final Config config, final BoardingFareTable fares,
            final ScoringParametersForPerson scoring) {
        this.fares = fares;
        this.scoring = scoring;
        this.delegate = ConfigUtils.addOrGetModule(config, RaptorModeCostConfigGroup.class).isModeConstant()
                ? new RaptorModeCostCalculator(config) : new DefaultRaptorInVehicleCostCalculator();
        try {
            this.iteratorType = Class.forName("ch.sbb.matsim.routing.pt.raptor.SwissRailRaptorCore$RouteSegmentIteratorImpl");
            this.data = field(this.iteratorType, "data");
            this.from = field(this.iteratorType, "fromRouteStopIndex");
            this.to = field(this.iteratorType, "toRouteStopIndex");
            this.stops = field(this.data.getType(), "routeStops");
            final Class<?> stopType = this.stops.getType().getComponentType();
            this.distance = field(stopType, "distanceAlongRoute");
            this.line = field(stopType, "line");
            this.route = field(stopType, "route");
        } catch (final ReflectiveOperationException e) {
            throw new IllegalStateException("Pinned RAPTOR fare adapter ABI changed; run the native fare probe", e);
        }
    }

    private static Field field(final Class<?> type, final String name) throws NoSuchFieldException {
        final Field result = type.getDeclaredField(name);
        result.setAccessible(true);
        return result;
    }

    @Override
    public double getInVehicleCost(final double time, final double timeUtility,
            final Person person, final Vehicle vehicle, final RaptorParameters parameters,
            final RouteSegmentIterator iterator) {
        if (!this.iteratorType.isInstance(iterator)) {
            throw new IllegalArgumentException("Unsupported RAPTOR fare iterator: "
                    + (iterator == null ? "null" : iterator.getClass().getName()));
        }
        try {
            final Object[] routeStops = (Object[]) this.stops.get(this.data.get(iterator));
            final Object start = routeStops[this.from.getInt(iterator)];
            final Object end = routeStops[this.to.getInt(iterator)];
            final TransitRoute boardedRoute = (TransitRoute) this.route.get(start);
            if (boardedRoute != this.route.get(end)) {
                throw new IllegalStateException("Priced RAPTOR segment crosses a boarding boundary");
            }
            final TransitLine boardedLine = (TransitLine) this.line.get(start);
            final double metres = this.distance.getDouble(end) - this.distance.getDouble(start);
            final double price = this.fares.rule(boardedLine.getId().toString(),
                    boardedRoute.getTransportMode()).price(metres);
            final double moneyUtility = this.scoring.getScoringParameters(person).marginalUtilityOfMoney;
            if (!Double.isFinite(moneyUtility) || moneyUtility < 0) {
                throw new IllegalArgumentException("Fare routing requires finite non-negative money utility");
            }
            return this.delegate.getInVehicleCost(time, timeUtility, person, vehicle, parameters, iterator)
                    + price * moneyUtility;
        } catch (final IllegalAccessException e) {
            throw new IllegalStateException("Pinned RAPTOR fare adapter is inaccessible", e);
        }
    }
}
