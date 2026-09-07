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
    /**
     * The stress factor by {@code Id<Link>.index()}, 1.0 where there is none.
     *
     * <p>It was a {@code Map<Id<Link>, Double>}, and the lookup was measured
     * (DECISIONS.md 9.154) at <b>3.3 % of every CPU sample in a 25 % probe</b>
     * - a hash of the link id and an unbox on every relaxation of every bike
     * route search. The membership is fixed when the network is read, so it is
     * an array indexed by the id MATSim already assigns. Same factors, same
     * arithmetic, same answer.
     */
    private final double[] factorByLink;

    private BikeStressDisutility(final TravelTime travelTime,
                                 final double[] factorByLink) {
        this.travelTime = travelTime;
        this.factorByLink = factorByLink;
    }

    @Override
    public double getLinkTravelDisutility(final Link link, final double time,
                                          final Person person,
                                          final Vehicle vehicle) {
        final double t = this.travelTime.getLinkTravelTime(
                link, time, person, vehicle);
        final int i = link.getId().index();
        if (i < 0 || i >= this.factorByLink.length) {
            return t;
        }
        final double factor = this.factorByLink[i];
        // 1.0 is the "no stamped factor" entry, and multiplying by it is the
        // identity - so the branch the map's null took is not needed.
        return t * factor;
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

        private final double[] factorByLink;

        public Factory(final Network network) {
            int highest = -1;
            for (final Link link : network.getLinks().values()) {
                highest = Math.max(highest, link.getId().index());
            }
            this.factorByLink = new double[highest + 1];
            java.util.Arrays.fill(this.factorByLink, 1.0);
            for (final Link link : network.getLinks().values()) {
                final Object raw = link.getAttributes()
                        .getAttribute(BikeStressConfigGroup.STRESS_ATTRIBUTE);
                if (raw == null) {
                    continue;
                }
                final double factor = Double.parseDouble(raw.toString());
                final int i = link.getId().index();
                // > 1.0 only, exactly as before: the stamp is a SURPLUS and a
                // value at or below 1 would make a stressed link cheaper.
                if (factor > 1.0 && i >= 0) {
                    this.factorByLink[i] = factor;
                }
            }
        }

        /** The tabled factor for one link - the probe's window into the
         * table, so a test can compare it against the stamped attribute. */
        public double factorOf(final Link link) {
            final int i = link.getId().index();
            return i >= 0 && i < this.factorByLink.length
                    ? this.factorByLink[i] : 1.0;
        }

        @Override
        public TravelDisutility createTravelDisutility(
                final TravelTime travelTime) {
            return new BikeStressDisutility(travelTime, this.factorByLink);
        }
    }
}
