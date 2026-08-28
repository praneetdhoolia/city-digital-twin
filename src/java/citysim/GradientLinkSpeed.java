package citysim;

import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.mobsim.qsim.qnetsimengine.QVehicle;
import org.matsim.core.mobsim.qsim.qnetsimengine.linkspeedcalculator.LinkSpeedCalculator;
import org.matsim.core.router.util.TravelTime;
import org.matsim.vehicles.Vehicle;

/**
 * Link gradient in walk and bike travel time — ONE formula, two consumers
 * (DECISIONS.md 9.84, issue #21).
 *
 * <p>The grade is DATA: the signed {@code grade_pct} attribute the run-input
 * builder stamps on each link from the P2 elevation layers (positive =
 * climbing in the link's direction of travel). The conversion to a speed
 * factor is published physics, with every constant declared in the registry:
 *
 * <ul>
 * <li><b>walk</b> — the Tobler hiking function, normalised so a flat link
 *     keeps the declared cap: {@code f = exp(-c|s + o|) / exp(-c o)} with
 *     slope fraction {@code s}, coefficient {@code c} and offset {@code o}
 *     (Tobler 1993 — the same function that produced the A6 footway layer's
 *     own walk_speed_factor columns).</li>
 * <li><b>bike</b> — linear in grade percent (Parkin &amp; Rotheram 2010):
 *     {@code f = 1 - up·g} climbing, {@code f = 1 + down·|g|} descending,
 *     clamped to the declared floor and ceiling.</li>
 * </ul>
 *
 * <p>The mobsim side ({@link Mobsim}) and the router side ({@link Router})
 * both call {@link #factor}, so estimate and physics cannot drift — the
 * {@link CappedSpeedTravelTime} discipline, extended by one multiplication.
 * Nothing here is a behavioural weight: the extra seconds are priced by the
 * mode's own scoring parameters, exactly as before.
 */
public final class GradientLinkSpeed {

    private GradientLinkSpeed() {
    }

    /** The grade-speed factor for one mode on one link; 1.0 off a graded
     * link, 1.0 for every mode that is neither walk nor bike. */
    public static double factor(final String mode, final Link link,
                                final GradientConfigGroup cfg) {
        final boolean walk = TransportMode.walk.equals(mode);
        final boolean bike = TransportMode.bike.equals(mode);
        if (!walk && !bike) {
            return 1.0;
        }
        final Object attr =
                link.getAttributes().getAttribute(GradientConfigGroup.GRADE_ATTRIBUTE);
        if (attr == null) {
            return 1.0;
        }
        final double gradePct = Double.parseDouble(attr.toString());
        if (walk) {
            final double s = gradePct / 100.0;
            final double c = cfg.getWalkToblerSlopeCoeff();
            final double o = cfg.getWalkToblerOffset();
            return Math.exp(-c * Math.abs(s + o)) / Math.exp(-c * o);
        }
        final double f = gradePct > 0.0
                ? 1.0 - cfg.getBikeUphillSlowdownPerPct() * gradePct
                : 1.0 + cfg.getBikeDownhillSpeedupPerPct() * -gradePct;
        return Math.max(cfg.getBikeFloorFactor(),
                        Math.min(cfg.getBikeCeilingFactor(), f));
    }

    /**
     * The qsim side: what {@code DefaultLinkSpeedCalculator} answers —
     * {@code min(link freespeed, vehicle maximum velocity)} — times the
     * grade factor for a walk or bike vehicle. Handles EVERY vehicle, so it
     * can serve as the sole calculator of a
     * {@code ConfigurableQNetworkFactory}.
     */
    public static final class Mobsim implements LinkSpeedCalculator {

        private final GradientConfigGroup cfg;

        public Mobsim(final GradientConfigGroup cfg) {
            this.cfg = cfg;
        }

        @Override
        public double getMaximumVelocity(final QVehicle vehicle,
                                         final Link link, final double time) {
            final double base = Math.min(vehicle.getMaximumVelocity(),
                                         link.getFreespeed(time));
            final String type =
                    vehicle.getVehicle().getType().getId().toString();
            return base * factor(type, link, this.cfg);
        }
    }

    /**
     * The router side: {@link CappedSpeedTravelTime}'s formula times the
     * same grade factor, from the same declared cap the qsim's vehicle type
     * carries — one declared value, two consumers, byte-equal.
     */
    public static final class Router implements TravelTime {

        private final String mode;
        private final double capMetresPerSecond;
        private final GradientConfigGroup cfg;

        public Router(final String mode, final double capMetresPerSecond,
                      final GradientConfigGroup cfg) {
            if (!(capMetresPerSecond > 0.0)) {
                throw new IllegalArgumentException(
                        "a network-simulated mode needs a positive speed cap; "
                        + "got " + capMetresPerSecond);
            }
            this.mode = mode;
            this.capMetresPerSecond = capMetresPerSecond;
            this.cfg = cfg;
        }

        @Override
        public double getLinkTravelTime(final Link link, final double time,
                                        final Person person,
                                        final Vehicle vehicle) {
            final double base = Math.min(link.getFreespeed(time),
                                         this.capMetresPerSecond);
            return link.getLength() / (base * factor(this.mode, link, this.cfg));
        }
    }
}
