package citysim;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Population;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.population.algorithms.PermissibleModesCalculator;
import org.matsim.core.population.io.PopulationReader;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Subtour;
import org.matsim.core.router.TripStructureUtils.Trip;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.api.core.v01.Scenario;

/**
 * Does any plan in a population hold a SUBTOUR that mixes chain-based with
 * non-chain-based modes?
 *
 * <p>That is the exact condition MATSim's
 * {@code ChooseRandomLegModeForSubtour.applyChange} refuses with
 * {@code IllegalStateException: Subtour contains a mix of chain- and
 * non-chainbased modes}, which has now killed four arms (26, 27, 29 and 30
 * August). This scanner asks the question OFF-LINE, against a plans file, using
 * MATSim's own subtour decomposition rather than a re-implementation of it - so
 * a plan it clears is a plan the strategy cannot refuse for this reason, and a
 * plan it flags names the person to look at.
 *
 * <p>It reads and reports; it changes nothing. Usage:
 *
 * <pre>java -cp &lt;run-stack&gt;;.tools/classes-signals citysim.SubtourChainScan
 *     &lt;plans.xml.gz&gt; &lt;chainBasedModes,csv&gt; [maxExamples]</pre>
 */
public final class SubtourChainScan {

    private SubtourChainScan() {
    }

    private static org.matsim.api.core.v01.Coord firstActivityCoord(final Plan plan) {
        for (final org.matsim.api.core.v01.population.PlanElement pe
                : plan.getPlanElements()) {
            if (pe instanceof org.matsim.api.core.v01.population.Activity) {
                return ((org.matsim.api.core.v01.population.Activity) pe).getCoord();
            }
        }
        return null;
    }

    private static String metresFrom(final org.matsim.api.core.v01.Coord home,
                                     final org.matsim.api.core.v01.population.Activity act) {
        if (home == null || act.getCoord() == null) {
            return "?";
        }
        return String.valueOf(Math.round(
                org.matsim.core.utils.geometry.CoordUtils.calcEuclideanDistance(
                        home, act.getCoord())));
    }

    /**
     * What one scan counted, and the examples it kept. main() was one
     * 186-line method holding all of this as locals until 27 September 2026
     * (fourteenth report, recommendation 9); the phases below share it.
     */
    private static final class Scan {
        final Set<String> chainBased;
        final int maxExamples;
        final double coordDistance;
        long persons = 0;
        long plans = 0;
        long subtours = 0;
        long mixedSubtours = 0;
        long mixedLeafSubtours = 0;
        long mixedSpanningSubtours = 0;
        long mixedPlans = 0;
        final Set<String> mixedPersons = new HashSet<>();
        final Map<String, Long> comboCounts = new LinkedHashMap<>();
        final List<String> examples = new ArrayList<>();

        Scan(final Set<String> chainBased, final int maxExamples,
             final double coordDistance) {
            this.chainBased = chainBased;
            this.maxExamples = maxExamples;
            this.coordDistance = coordDistance;
        }
    }

    public static void main(final String[] args) {
        if (args.length < 2) {
            System.err.println("usage: SubtourChainScan <plans.xml.gz> "
                    + "<chainBasedModes,csv> [maxExamples]");
            System.exit(2);
        }
        final String plansFile = args[0];
        final Set<String> chainBased = new HashSet<>();
        for (final String m : args[1].split(",")) {
            if (!m.trim().isEmpty()) {
                chainBased.add(m.trim());
            }
        }
        final int maxExamples = args.length > 2
                ? Integer.parseInt(args[2]) : 10;
        // The run's own subtourModeChoice.coordDistance. Passed in rather than
        // assumed, so this scanner decomposes exactly as the run does.
        final double coordDistance = args.length > 3
                ? Double.parseDouble(args[3]) : 100.0;

        final Scenario scenario = ScenarioUtils.createScenario(
                ConfigUtils.createConfig());
        new PopulationReader(scenario).readFile(plansFile);
        final Population pop = scenario.getPopulation();

        final Scan scan = new Scan(chainBased, maxExamples, coordDistance);
        for (final Person person : pop.getPersons().values()) {
            scan.persons++;
            for (final Plan plan : person.getPlans()) {
                scanPlan(scan, person, plan);
            }
        }
        report(scan, plansFile);
    }

    /** Decompose one plan and scan each of its subtours. */
    private static void scanPlan(final Scan scan, final Person person,
                                 final Plan plan) {
        scan.plans++;
        boolean planMixed = false;
        final Collection<Subtour> subs;
        try {
            // The COORD-DISTANCE overload, which is what the run itself
            // uses (subtourModeChoice.coordDistance) and what
            // EscortCoherenceListener uses. The no-argument overload
            // demands facility or link ids, which an INPUT plans file
            // does not carry until PersonPrepareForSim assigns them -
            // that is why this scanner decomposed 0 subtours on its
            // first run and reported a clean it had never tested.
            subs = TripStructureUtils.getSubtours(plan, scan.coordDistance);
        } catch (final RuntimeException e) {
            // A plan whose structure MATSim cannot decompose is itself
            // a finding, and is reported rather than skipped silently.
            scan.examples.add(person.getId() + " : subtour decomposition "
                    + "FAILED: " + e);
            return;
        }
        for (final Subtour sub : subs) {
            scan.subtours++;
            if (scanSubtour(scan, person, plan, sub)) {
                planMixed = true;
            }
        }
        if (planMixed) {
            scan.mixedPlans++;
        }
    }

    /** Count one subtour; true if it mixes chain- with non-chain-based modes. */
    private static boolean scanSubtour(final Scan scan, final Person person,
                                       final Plan plan, final Subtour sub) {
        boolean sawChain = false;
        boolean sawNonChain = false;
        final Set<String> modes = new HashSet<>();
        for (final Trip trip : sub.getTrips()) {
            final List<Leg> legs = trip.getLegsOnly();
            if (legs.isEmpty()) {
                continue;
            }
            String mode = TripStructureUtils
                    .getRoutingMode(legs.get(0));
            if (mode == null) {
                mode = legs.get(0).getMode();
            }
            modes.add(mode);
            if (scan.chainBased.contains(mode)) {
                sawChain = true;
            } else {
                sawNonChain = true;
            }
        }
        if (!(sawChain && sawNonChain)) {
            return false;
        }
        scan.mixedSubtours++;
        scan.mixedPersons.add(person.getId().toString());
        // A LEAF subtour is one home-anchored excursion, and a
        // mix inside it is physically impossible - the car is
        // not where the agent left it. A subtour WITH children
        // spans several excursions, and mixing across them
        // (drive in the morning, PT in the evening) is an
        // ordinary day. Only the first is a demand defect.
        if (sub.getChildren().isEmpty()) {
            scan.mixedLeafSubtours++;
        } else {
            scan.mixedSpanningSubtours++;
        }
        final List<String> sorted = new ArrayList<>(modes);
        java.util.Collections.sort(sorted);
        final String key = String.join("+", sorted);
        scan.comboCounts.merge(key, 1L, Long::sum);
        final boolean leaf = sub.getChildren().isEmpty();
        // A LEAF mix is the defect shape (#96), so every one
        // is traced in full - the trips with their activity
        // types, modes and each activity's distance from the
        // plan's first activity (home) - whatever the example
        // budget; the budget bounds the SPANNING examples,
        // which are ordinary days.
        if (leaf || scan.examples.size() < scan.maxExamples) {
            final StringBuilder sb = new StringBuilder();
            sb.append(person.getId()).append(" : ").append(key)
                    .append("  (").append(sub.getTrips().size())
                    .append(" trips, closed=").append(sub.isClosed())
                    .append(leaf ? ", LEAF)" : ", SPANNING)");
            if (leaf) {
                traceLeaf(sb, plan, sub);
            }
            scan.examples.add(sb.toString());
        }
        return true;
    }

    /** Each trip of a leaf mix: activity types, mode, metres from home. */
    private static void traceLeaf(final StringBuilder sb, final Plan plan,
                                  final Subtour sub) {
        final org.matsim.api.core.v01.Coord home =
                firstActivityCoord(plan);
        for (final Trip trip : sub.getTrips()) {
            final List<Leg> legs = trip.getLegsOnly();
            String mode = legs.isEmpty() ? "?"
                    : TripStructureUtils.getRoutingMode(legs.get(0));
            if (mode == null && !legs.isEmpty()) {
                mode = legs.get(0).getMode();
            }
            sb.append("\n        ")
                    .append(trip.getOriginActivity().getType())
                    .append(" @")
                    .append(metresFrom(home, trip.getOriginActivity()))
                    .append("m -[").append(mode).append("]-> ")
                    .append(trip.getDestinationActivity().getType())
                    .append(" @")
                    .append(metresFrom(home, trip.getDestinationActivity()))
                    .append("m");
        }
    }

    /** Print the tallies, the combinations and the examples; exit 3 on a
     *  scan that decomposed nothing. */
    private static void report(final Scan scan, final String plansFile) {
        System.out.println("plans file      " + plansFile);
        System.out.println("chain-based     " + scan.chainBased);
        System.out.println("persons         " + scan.persons);
        System.out.println("plans           " + scan.plans);
        System.out.println("subtours        " + scan.subtours);
        System.out.println("MIXED subtours  " + scan.mixedSubtours);
        System.out.println("   of which LEAF (one excursion - a DEFECT)      "
                + scan.mixedLeafSubtours);
        System.out.println("   of which SPANNING (several excursions - normal) "
                + scan.mixedSpanningSubtours);
        System.out.println("MIXED plans     " + scan.mixedPlans);
        System.out.println("MIXED persons   " + scan.mixedPersons.size());
        if (!scan.comboCounts.isEmpty()) {
            System.out.println("mode combinations seen in mixed subtours:");
            scan.comboCounts.entrySet().stream()
                    .sorted((a, b) -> Long.compare(b.getValue(), a.getValue()))
                    .forEach(e -> System.out.println("   " + e.getValue()
                            + "  " + e.getKey()));
        }
        if (!scan.examples.isEmpty()) {
            System.out.println("examples:");
            for (final String ex : scan.examples) {
                System.out.println("   " + ex);
            }
        }
        // A scan that decomposed NOTHING must not report CLEAN. Unrouted
        // plans carry coordinates but no link ids, and MATSim's subtour
        // decomposition refuses them - so this scanner answers only for a
        // ROUTED population. Printing "clean" off zero subtours is the same
        // false green this tool exists to catch (9.117), and it did exactly
        // that on its first run before this guard was added.
        if (scan.subtours == 0) {
            System.out.println("INCONCLUSIVE - decomposed 0 subtours, so "
                    + "NOTHING was tested. This needs a ROUTED plans file "
                    + "(activities with link ids); an input plans file has "
                    + "none until PersonPrepareForSim assigns them.");
            System.exit(3);
        }
        System.out.println(scan.mixedSubtours == 0
                ? "CLEAN - no subtour mixes chain- and non-chain-based modes"
                : "MIXED SUBTOURS PRESENT");
    }
}
