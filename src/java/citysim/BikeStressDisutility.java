package citysim;

import java.util.HashMap;
import java.util.Map;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.router.costcalculators.TravelDisutilityFactory;
import org.matsim.core.router.util.TravelDisutility;
import org.matsim.core.router.util.TravelTime;
import org.matsim.vehicles.Vehicle;

/**
 * The ROUTER half of the bike stress channel (DECISIONS.md 9.138, #107):
 * a link's cost to a cyclist is its travel time multiplied by its
 * {@code bike_stress_factor}, so the route search itself prefers the quiet
 * street — which is what Broach, Dill &amp; Gliebe 2012 measured cyclists
 * doing, and exactly the multiplier {@link BikeStressScoring} charges when a
 * stressed link is ridden anyway. One factor, two consumers, no drift.
 *
 * <p>Replaces {@code OnlyTimeDependentTravelDisutilityFactory} for bike only
 * when {@code bikeStress.representation = felt_time}; under {@code absent}
 * that stock factory stays bound and routing is byte-identical to the
 * pre-9.138 model.
 */
public final class BikeStressDisutility implements TravelDisutility {

    private final TravelTime travelTime;
    private final Map<Id<Link>, Double> factorByLink;

    private BikeStressDisutility(final TravelTime travelTime,
                                 final Map<Id<Link>, Double> factorByLink) {
        this.travelTime = travelTime;
        this.factorByLink = factorByLink;
    }

    @Override
    public double getLinkTravelDisutility(final Link link, final double time,
                                          final Person person,
                                          final Vehicle vehicle) {
        final double t = this.travelTime.getLinkTravelTime(
                link, time, person, vehicle);
        final Double factor = this.factorByLink.get(link.getId());
        return factor == null ? t : t * factor;
    }

    @Override
    public double getLinkMinimumTravelDisutility(final Link link) {
        // The admissible lower bound for A*: the stress factor only ever
        // RAISES a link's cost, so free-speed time stays a valid floor.
        return link.getLength() / link.getFreespeed();
    }

    /** Built once per mode binding, reading the stamped factors off the
     * scenario network exactly as {@link BikeStressScoring} does. */
    public static final class Factory implements TravelDisutilityFactory {

        private final Map<Id<Link>, Double> factorByLink = new HashMap<>();

        public Factory(final Network network) {
            for (final Link link : network.getLinks().values()) {
                final Object raw = link.getAttributes()
                        .getAttribute(BikeStressConfigGroup.STRESS_ATTRIBUTE);
                if (raw == null) {
                    continue;
                }
                final double factor = Double.parseDouble(raw.toString());
                if (factor > 1.0) {
                    this.factorByLink.put(link.getId(), factor);
                }
            }
        }

        @Override
        public TravelDisutility createTravelDisutility(
                final TravelTime travelTime) {
            return new BikeStressDisutility(travelTime, this.factorByLink);
        }
    }
}
