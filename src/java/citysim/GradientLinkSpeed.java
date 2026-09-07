package citysim;

import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.network.NetworkChangeEvent;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.mobsim.qsim.qnetsimengine.QVehicle;
import org.matsim.core.mobsim.qsim.qnetsimengine.linkspeedcalculator.LinkSpeedCalculator;
import org.matsim.core.router.util.TravelTime;
import org.matsim.vehicles.Vehicle;
import org.matsim.vehicles.VehicleType;

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
     *
     * <p><b>Why this reads a table rather than the formula.</b> This is the
     * mobsim's hottest call — once per vehicle per link entry, of the order
     * of 65 M an iteration at 25 %. Answering it from {@link #factor} meant,
     * on EVERY one of those calls, materialising the vehicle type's id as a
     * String and two {@code String.equals}; and on every walk or bike call
     * additionally an attribute-map lookup, a {@code Double.parseDouble} of
     * the stamped grade and two {@code Math.exp}. The grade is a property of
     * the link and does not change during a run, and the mode is a property
     * of the vehicle type, so both are resolved ONCE here: the per-link
     * factors are filled from {@link #factor} itself at construction — the
     * one formula still decides every number — and the walk and bike vehicle
     * types are resolved to their {@code Id} indices. The answer is
     * bit-identical to the formula's, because it IS the formula's, computed
     * earlier. A link the table does not cover falls back to the formula.
     */
    public static final class Mobsim implements LinkSpeedCalculator {

        private final GradientConfigGroup cfg;
        /** {@code Id<VehicleType>.index()} of the walk vehicle type, or -1. */
        private final int walkTypeIndex;
        /** {@code Id<VehicleType>.index()} of the bike vehicle type, or -1. */
        private final int bikeTypeIndex;
        /** Walk grade factor by {@code Id<Link>.index()}. */
        private final double[] walkFactorByLink;
        /** Bike grade factor by {@code Id<Link>.index()}. */
        private final double[] bikeFactorByLink;

        /**
         * @param network the run's network, read once to fill the per-link
         *                factor tables. The mobsim never adds a link, so the
         *                tables are complete and are only read afterwards —
         *                they are published to the mobsim's threads by those
         *                threads' own start, and never written again.
         */
        public Mobsim(final GradientConfigGroup cfg, final Network network) {
            this.cfg = cfg;
            this.walkTypeIndex =
                    Id.create(TransportMode.walk, VehicleType.class).index();
            this.bikeTypeIndex =
                    Id.create(TransportMode.bike, VehicleType.class).index();
            int highest = -1;
            for (final Link link : network.getLinks().values()) {
                highest = Math.max(highest, link.getId().index());
            }
            this.walkFactorByLink = new double[highest + 1];
            this.bikeFactorByLink = new double[highest + 1];
            java.util.Arrays.fill(this.walkFactorByLink, 1.0);
            java.util.Arrays.fill(this.bikeFactorByLink, 1.0);
            for (final Link link : network.getLinks().values()) {
                final int i = link.getId().index();
                if (i < 0) {
                    continue;
                }
                this.walkFactorByLink[i] =
                        factor(TransportMode.walk, link, cfg);
                this.bikeFactorByLink[i] =
                        factor(TransportMode.bike, link, cfg);
            }
        }

        /** The tabled factor for one mode on one link - the probe's window
         * into the table, so a test can compare it against {@link #factor}
         * without needing a running mobsim to hand it a QVehicle. */
        public double factorFor(final String mode, final Link link) {
            final double[] table = TransportMode.walk.equals(mode)
                    ? this.walkFactorByLink
                    : TransportMode.bike.equals(mode)
                            ? this.bikeFactorByLink : null;
            if (table == null) {
                return 1.0;
            }
            final int i = link.getId().index();
            return i >= 0 && i < table.length
                    ? table[i] : factor(mode, link, this.cfg);
        }

        @Override
        public double getMaximumVelocity(final QVehicle vehicle,
                                         final Link link, final double time) {
            final double base = Math.min(vehicle.getMaximumVelocity(),
                                         link.getFreespeed(time));
            final int typeIndex =
                    vehicle.getVehicle().getType().getId().index();
            final double[] table;
            if (typeIndex == this.walkTypeIndex) {
                table = this.walkFactorByLink;
            } else if (typeIndex == this.bikeTypeIndex) {
                table = this.bikeFactorByLink;
            } else {
                // Every other vehicle: the default calculator's own answer,
                // as before — factor() returns exactly 1.0 for them.
                return base;
            }
            final int i = link.getId().index();
            if (i < 0 || i >= table.length) {
                // A link the table does not cover: the formula, unchanged.
                return base * factor(vehicle.getVehicle().getType().getId()
                                             .toString(), link, this.cfg);
            }
            return base * table[i];
        }
    }

    /**
     * The router side: {@link CappedSpeedTravelTime}'s formula times the
     * same grade factor, from the same declared cap the qsim's vehicle type
     * carries — one declared value, two consumers, byte-equal.
     *
     * <p><b>Why this is a table.</b> Measured, not reasoned: a flight
     * recording of a 25 % probe (DECISIONS.md 9.154) put
     * {@code Router.getLinkTravelTime} at <b>17.9 % of every CPU sample in the
     * run</b>, the largest single method in this project's own code, and
     * showed what it was doing. For a walk or bike link the formula asks the
     * link three questions on EVERY relaxation of EVERY route search:
     *
     * <ul>
     * <li>{@code link.getFreespeed(time)} — on a TIME-VARIANT network (the
     *     level-crossing closures, {@code A.crossings.representation =
     *     change_events}) that is a {@code synchronized} method doing an
     *     {@code Arrays.binarySearch} over the link's change-event times.
     *     16.2 % of all samples, on 143,891 links of which 16 can actually
     *     change;</li>
     * <li>{@code link.getAttributes().getAttribute("grade_pct")} — another
     *     binary search, 5.6 %;</li>
     * <li>{@code Double.parseDouble} of the string it returns, plus two
     *     {@code Math.exp} — 8.0 %.</li>
     * </ul>
     *
     * <p>Every one of those answers is CONSTANT for a link the network change
     * events never name. The link's length, its free speed, its grade and the
     * declared cap do not move, so neither does the travel time: it is
     * computed once per link here, from the SAME {@link #factor} the qsim and
     * the probe use, and read from an array afterwards. A link that a change
     * event does name keeps the live path exactly as it was, and so does a
     * link the table does not cover.
     *
     * <p>The answer is bit-identical because it IS the same arithmetic on the
     * same values, performed earlier: IEEE-754 double operations are
     * deterministic, and the guard below refuses to tabulate any link whose
     * free speed differs between two probe times.
     */
    public static final class Router implements TravelTime {

        /** A link whose travel time must be computed live. */
        private static final double LIVE = -1.0;

        private final String mode;
        private final double capMetresPerSecond;
        private final GradientConfigGroup cfg;
        /** Travel time by {@code Id<Link>.index()}, or {@link #LIVE}. */
        private final double[] constantTravelTime;

        /**
         * @param network the run's network. Read once, with its change events,
         *                to decide which links can vary and to tabulate the
         *                rest. Pass null to keep the live path for every link.
         */
        public Router(final String mode, final double capMetresPerSecond,
                      final GradientConfigGroup cfg, final Network network) {
            if (!(capMetresPerSecond > 0.0)) {
                throw new IllegalArgumentException(
                        "a network-simulated mode needs a positive speed cap; "
                        + "got " + capMetresPerSecond);
            }
            this.mode = mode;
            this.capMetresPerSecond = capMetresPerSecond;
            this.cfg = cfg;
            this.constantTravelTime = network == null
                    ? new double[0] : tabulate(mode, capMetresPerSecond, cfg,
                                               network);
        }

        private static double[] tabulate(final String mode, final double cap,
                                         final GradientConfigGroup cfg,
                                         final Network network) {
            // Every link a change event names, whatever it changes: those are
            // the only links MATSim ever calls applyEvent on, so every other
            // link's attributes are fixed for the run by construction.
            final java.util.Set<Id<Link>> varying = new java.util.HashSet<>();
            try {
                for (final NetworkChangeEvent e
                        : org.matsim.core.network.NetworkUtils
                                  .getNetworkChangeEvents(network)) {
                    for (final Link l : e.getLinks()) {
                        varying.add(l.getId());
                    }
                }
            } catch (final RuntimeException ignored) {
                // a network that carries no change events at all
            }
            int highest = -1;
            for (final Link link : network.getLinks().values()) {
                highest = Math.max(highest, link.getId().index());
            }
            final double[] table = new double[highest + 1];
            java.util.Arrays.fill(table, LIVE);
            for (final Link link : network.getLinks().values()) {
                final int i = link.getId().index();
                if (i < 0 || varying.contains(link.getId())) {
                    continue;
                }
                // Belt and braces: a link no event names must answer the same
                // free speed at any time. If it does not, it stays live.
                final double v0 = link.getFreespeed(0.0);
                if (v0 != link.getFreespeed(30.0 * 3600.0)
                        || v0 != link.getFreespeed(86400.0 * 2.0)) {
                    continue;
                }
                final double base = Math.min(v0, cap);
                table[i] = link.getLength() / (base * factor(mode, link, cfg));
            }
            return table;
        }

        @Override
        public double getLinkTravelTime(final Link link, final double time,
                                        final Person person,
                                        final Vehicle vehicle) {
            final int i = link.getId().index();
            if (i >= 0 && i < this.constantTravelTime.length) {
                final double t = this.constantTravelTime[i];
                if (t != LIVE) {
                    return t;
                }
            }
            final double base = Math.min(link.getFreespeed(time),
                                         this.capMetresPerSecond);
            return link.getLength() / (base * factor(this.mode, link, this.cfg));
        }
    }
}
