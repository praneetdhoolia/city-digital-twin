package citysim;

import java.util.ArrayList;
import java.util.List;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * Proof that the per-link tables answer exactly what the formula answered.
 *
 * <p><b>Why a probe and not a diff of two runs.</b> A MATSim run in this
 * repository is NOT bit-for-bit reproducible: three runs of one unmodified
 * build produced 5,620,710 / 5,620,410 / 5,620,710 iteration-0 events, because
 * {@code global.numberOfThreads} is 20 and {@code MatsimRandom.getLocalInstance}
 * races (DECISIONS.md 9.142). So diffing a before-and-after run cannot prove a
 * change is result-preserving - the noise floor is larger than the thing being
 * proved.
 *
 * <p>This proves it where it can be proved: over the run's OWN network, link by
 * link, comparing the table's answer against the formula's on every link and at
 * several times of day. The claim is not "the runs looked the same"; it is
 * "for every link in this network, the two computations return the same
 * double". That is the whole of what 9.154's three tables changed.
 *
 * <pre>
 *   java -cp .tools/classes-signals;.tools/run-stack/lib/* \
 *        citysim.GradientTableProbe &lt;run-config.xml&gt;
 * </pre>
 *
 * <p>Exit code 0 when every link agrees, 1 on the first disagreement, with the
 * link, the mode, the time and both values printed.
 */
public final class GradientTableProbe {

    private GradientTableProbe() {
    }

    /** The times of day the comparison is made at, in seconds. */
    private static final double[] TIMES = {
        0.0, 6.0 * 3600, 8.5 * 3600, 12.0 * 3600, 17.5 * 3600, 23.0 * 3600,
        30.0 * 3600,
    };

    public static void main(final String[] args) {
        if (args.length < 1) {
            System.err.println("usage: GradientTableProbe <config.xml>");
            System.exit(2);
        }
        // Network and its change events only: the plans are not needed and are
        // the expensive half of a scenario load.
        final Config full = ConfigUtils.loadConfig(args[0],
                                                   new GradientConfigGroup(),
                                                   new BikeStressConfigGroup());
        final Config cfg = ConfigUtils.createConfig();
        cfg.network().setInputFile(full.network().getInputFile());
        cfg.network().setTimeVariantNetwork(
                full.network().isTimeVariantNetwork());
        cfg.network().setChangeEventsInputFile(
                full.network().getChangeEventsInputFile());
        cfg.global().setCoordinateSystem(full.global().getCoordinateSystem());
        final Scenario scenario = ScenarioUtils.loadScenario(cfg);
        final Network network = scenario.getNetwork();

        final GradientConfigGroup gradient = (GradientConfigGroup)
                full.getModules().get(GradientConfigGroup.NAME);
        if (gradient == null || !gradient.isLinkSpeed()) {
            System.out.println("gradient.representation is not link_speed - "
                               + "the tables are not built; nothing to prove");
            return;
        }

        final List<String> failures = new ArrayList<>();
        int links = 0;
        int compared = 0;

        // ---- the router table -------------------------------------------
        for (final String mode : new String[] {TransportMode.walk,
                                               TransportMode.bike}) {
            // The cap does not change what is being proved (it appears
            // identically on both sides), so a representative one is used:
            // the probe is about the TABLE, not about the declared speed.
            final double cap = TransportMode.walk.equals(mode) ? 1.4 : 4.2;
            final GradientLinkSpeed.Router tabled =
                    new GradientLinkSpeed.Router(mode, cap, gradient, network);
            final GradientLinkSpeed.Router live =
                    new GradientLinkSpeed.Router(mode, cap, gradient, null);
            for (final Link link : network.getLinks().values()) {
                for (final double t : TIMES) {
                    compared++;
                    final double a = tabled.getLinkTravelTime(link, t, null, null);
                    final double b = live.getLinkTravelTime(link, t, null, null);
                    if (Double.compare(a, b) != 0 && failures.size() < 20) {
                        failures.add(String.format(
                                "router %s link %s t=%.0f table=%s live=%s",
                                mode, link.getId(), t, a, b));
                    }
                }
            }
        }

        // ---- the mobsim table -------------------------------------------
        // getMaximumVelocity needs a QVehicle, which needs a mobsim; the table
        // it reads is the FACTOR, so the factor is what is compared.
        final GradientLinkSpeed.Mobsim mobsim =
                new GradientLinkSpeed.Mobsim(gradient, network);
        for (final Link link : network.getLinks().values()) {
            links++;
            for (final String mode : new String[] {TransportMode.walk,
                                                   TransportMode.bike}) {
                compared++;
                final double formula = GradientLinkSpeed.factor(mode, link,
                                                                gradient);
                final double tabled = mobsimFactor(mobsim, mode, link);
                if (Double.compare(formula, tabled) != 0
                        && failures.size() < 40) {
                    failures.add(String.format(
                            "mobsim %s link %s formula=%s table=%s",
                            mode, link.getId(), formula, tabled));
                }
            }
        }

        // ---- the bike-stress table ---------------------------------------
        final BikeStressDisutility.Factory stress =
                new BikeStressDisutility.Factory(network);
        for (final Link link : network.getLinks().values()) {
            compared++;
            final Object raw = link.getAttributes()
                    .getAttribute(BikeStressConfigGroup.STRESS_ATTRIBUTE);
            final double expected = raw == null
                    ? 1.0
                    : Math.max(1.0, Double.parseDouble(raw.toString()));
            final double got = stress.factorOf(link);
            if (Double.compare(expected, got) != 0 && failures.size() < 60) {
                failures.add(String.format(
                        "bikeStress link %s expected=%s table=%s",
                        link.getId(), expected, got));
            }
        }

        System.out.printf("GradientTableProbe: %,d link(s), %,d comparison(s)%n",
                          links, compared);
        if (failures.isEmpty()) {
            System.out.println("PASS - every table answers exactly what the "
                               + "formula answers");
            return;
        }
        System.out.println("FAIL - " + failures.size() + " disagreement(s):");
        for (final String f : failures) {
            System.out.println("  " + f);
        }
        System.exit(1);
    }

    /** The factor the mobsim table holds for one mode on one link. */
    private static double mobsimFactor(final GradientLinkSpeed.Mobsim m,
                                       final String mode, final Link link) {
        return m.factorFor(mode, link);
    }
}
