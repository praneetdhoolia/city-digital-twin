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

        final Scenario scenario = ScenarioUtils.createScenario(
                ConfigUtils.createConfig());
        new PopulationReader(scenario).readFile(plansFile);
        final Population pop = scenario.getPopulation();

        long persons = 0;
        long plans = 0;
        long subtours = 0;
        long mixedSubtours = 0;
        long mixedPlans = 0;
        final Set<String> mixedPersons = new HashSet<>();
        final Map<String, Long> comboCounts = new LinkedHashMap<>();
        final List<String> examples = new ArrayList<>();

        for (final Person person : pop.getPersons().values()) {
            persons++;
            for (final Plan plan : person.getPlans()) {
                plans++;
                boolean planMixed = false;
                final Collection<Subtour> subs;
                try {
                    subs = TripStructureUtils.getSubtours(plan);
                } catch (final RuntimeException e) {
                    // A plan whose structure MATSim cannot decompose is itself
                    // a finding, and is reported rather than skipped silently.
                    examples.add(person.getId() + " : subtour decomposition "
                            + "FAILED: " + e);
                    continue;
                }
                for (final Subtour sub : subs) {
                    subtours++;
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
                        if (chainBased.contains(mode)) {
                            sawChain = true;
                        } else {
                            sawNonChain = true;
                        }
                    }
                    if (sawChain && sawNonChain) {
                        mixedSubtours++;
                        planMixed = true;
                        mixedPersons.add(person.getId().toString());
                        final List<String> sorted = new ArrayList<>(modes);
                        java.util.Collections.sort(sorted);
                        final String key = String.join("+", sorted);
                        comboCounts.merge(key, 1L, Long::sum);
                        if (examples.size() < maxExamples) {
                            examples.add(person.getId() + " : " + key
                                    + "  (" + sub.getTrips().size()
                                    + " trips, closed="
                                    + sub.isClosed() + ")");
                        }
                    }
                }
                if (planMixed) {
                    mixedPlans++;
                }
            }
        }

        System.out.println("plans file      " + plansFile);
        System.out.println("chain-based     " + chainBased);
        System.out.println("persons         " + persons);
        System.out.println("plans           " + plans);
        System.out.println("subtours        " + subtours);
        System.out.println("MIXED subtours  " + mixedSubtours);
        System.out.println("MIXED plans     " + mixedPlans);
        System.out.println("MIXED persons   " + mixedPersons.size());
        if (!comboCounts.isEmpty()) {
            System.out.println("mode combinations seen in mixed subtours:");
            comboCounts.entrySet().stream()
                    .sorted((a, b) -> Long.compare(b.getValue(), a.getValue()))
                    .forEach(e -> System.out.println("   " + e.getValue()
                            + "  " + e.getKey()));
        }
        if (!examples.isEmpty()) {
            System.out.println("examples:");
            for (final String ex : examples) {
                System.out.println("   " + ex);
            }
        }
        // A scan that decomposed NOTHING must not report CLEAN. Unrouted
        // plans carry coordinates but no link ids, and MATSim's subtour
        // decomposition refuses them - so this scanner answers only for a
        // ROUTED population. Printing "clean" off zero subtours is the same
        // false green this tool exists to catch (9.117), and it did exactly
        // that on its first run before this guard was added.
        if (subtours == 0) {
            System.out.println("INCONCLUSIVE - decomposed 0 subtours, so "
                    + "NOTHING was tested. This needs a ROUTED plans file "
                    + "(activities with link ids); an input plans file has "
                    + "none until PersonPrepareForSim assigns them.");
            System.exit(3);
        }
        System.out.println(mixedSubtours == 0
                ? "CLEAN - no subtour mixes chain- and non-chain-based modes"
                : "MIXED SUBTOURS PRESENT");
    }
}
