package citysim;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.config.groups.GlobalConfigGroup;
import org.matsim.core.config.groups.SubtourModeChoiceConfigGroup;
import org.matsim.core.gbl.MatsimRandom;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.population.algorithms.PermissibleModesCalculator;
import org.matsim.core.population.algorithms.PlanAlgorithm;
import org.matsim.core.router.TripStructureUtils;

/**
 * The gate on {@link GatedSubtourModeChoice} (issue #133, candidate 8): a
 * proposal that would leave a subtour mixing chain- with non-chain-based
 * modes is reverted IN FULL, and a proposal putting {@code ride} on a trip
 * outside the person's declared {@code boundRideTrips} is refused whole.
 *
 * <p>No scenario, no mobsim and no replanning loop: the probe builds the
 * strategy's inner module by hand with a stub {@link
 * PermissibleModesCalculator}, hands it a plan built in memory, and runs the
 * plan algorithm the strategy would run. Each fixture is shaped so MATSim's
 * own choice set holds EXACTLY ONE candidate, which is what makes the outcome
 * of a random module assertable: the draw has nothing to choose between.
 *
 * <p>The mixed case reproduces the 9.119 shape without needing the
 * single-trip path: a nested subtour whose parent carries a mode the run's
 * {@code modes} list does not hold (so the parent is not itself a candidate),
 * and a two-trip child on car. The only candidate changes the child to pt,
 * which leaves the parent holding a chain-based and a non-chain-based mode
 * together - the state MATSim refuses with an {@code IllegalStateException}
 * several iterations later. The wrapper must put BOTH child trips back, not
 * one: reverting part of the proposal would leave exactly the state it is
 * refusing.
 *
 * <p>A reverted trip is detected by leg identity, not only by mode: the
 * refusal rebuilds each changed trip through {@code TripRouter.insertTrip},
 * so a reverted trip carries a NEW leg object. A probe that only compared
 * modes could not tell a refusal from a proposal that was never made.
 *
 * <ul>
 * <li>mixed proposal: both child trips are back on car, both legs replaced,
 *     and the plan's other trips are untouched;</li>
 * <li>clean proposal: a subtour whose change mixes nothing is ACCEPTED - the
 *     wrapper is not simply refusing everything;</li>
 * <li>{@code boundRideTrips} absent, and naming a trip index the plan does
 *     not have: the ride proposal is refused whole and counted;</li>
 * <li>{@code boundRideTrips} naming this plan's own trips: accepted;</li>
 * <li>the attribute parser itself: a malformed token names nothing, and an
 *     absent attribute is an empty set rather than a refusal to read.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class GatedSubtourProbe {

    private static final String PT = TransportMode.pt;
    private static final String CAR = TransportMode.car;
    private static final String BIKE = TransportMode.bike;
    private static final String RIDE = TransportMode.ride;

    private GatedSubtourProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json = new StringBuilder("{");
        boolean ok = true;

        // --- 1. a mixed proposal is reverted in full ----------------------
        // acts A B C B A, legs bike car car bike: the child subtour B-C-B is
        // on car, the parent carries bike, which `modes` does not hold - so
        // the only candidate is "put the child on pt", and that leaves the
        // parent mixing bike with pt.
        final Plan mixed = plan("mixed",
                new String[] {"A", "B", "C", "B", "A"},
                new String[] {BIKE, CAR, CAR, BIKE});
        final List<Leg> mixedBefore = legs(mixed);
        // permissible is the CANDIDATE vocabulary MATSim draws from (measured
        // on the pinned jar: `modes` decides which subtours are eligible, the
        // calculator decides which modes may be proposed), so declaring pt and
        // car alone leaves the child subtour exactly one candidate: pt.
        run(mixed, new String[] {CAR, PT}, new String[] {CAR, BIKE},
            modes(CAR, PT));
        final List<Leg> mixedAfter = legs(mixed);
        final boolean revertedModes = modesOf(mixedAfter)
                .equals(Arrays.asList(BIKE, CAR, CAR, BIKE));
        final boolean bothChildLegsReplaced =
                mixedAfter.size() == 4
                && mixedAfter.get(1) != mixedBefore.get(1)
                && mixedAfter.get(2) != mixedBefore.get(2);
        final boolean parentUntouched = mixedAfter.size() == 4
                && mixedAfter.get(0) == mixedBefore.get(0)
                && mixedAfter.get(3) == mixedBefore.get(3);
        ok &= revertedModes && bothChildLegsReplaced && parentUntouched;
        json.append("\"mixed_modes_after\":\"").append(join(modesOf(mixedAfter)))
            .append("\",\"mixed_reverted_in_full\":").append(revertedModes)
            .append(",\"both_proposed_trips_replaced\":")
            .append(bothChildLegsReplaced)
            .append(",\"untouched_trips_left_alone\":").append(parentUntouched);

        // --- 2. a proposal that mixes nothing is accepted -----------------
        final Plan clean = plan("clean",
                new String[] {"A", "B", "A"}, new String[] {CAR, CAR});
        run(clean, new String[] {CAR, PT}, new String[] {CAR},
            modes(CAR, PT));
        final boolean accepted = modesOf(legs(clean))
                .equals(Arrays.asList(PT, PT));
        ok &= accepted;
        json.append(",\"clean_modes_after\":\"").append(join(modesOf(legs(clean))))
            .append("\",\"clean_proposal_accepted\":").append(accepted);

        // --- 3. ride on a trip no declared driver serves -------------------
        final int before = GatedSubtourModeChoice.GatedModule
                .BOUND_RIDE_REFUSALS.get();
        final Plan unbound = plan("unbound",
                new String[] {"A", "B", "A"}, new String[] {CAR, CAR});
        run(unbound, new String[] {CAR, RIDE}, new String[] {CAR},
            modes(CAR, RIDE));
        final boolean unboundRefused = modesOf(legs(unbound))
                .equals(Arrays.asList(CAR, CAR));

        // the same, with an index the plan does not have: two trips, and the
        // attribute names trip 3
        final Plan outOfRange = plan("out_of_range",
                new String[] {"A", "B", "A"}, new String[] {CAR, CAR});
        outOfRange.getPerson().getAttributes().putAttribute(
                GatedSubtourModeChoice.GatedModule.BOUND_RIDE_ATTRIBUTE, "3");
        run(outOfRange, new String[] {CAR, RIDE}, new String[] {CAR},
            modes(CAR, RIDE));
        final boolean outOfRangeRefused = modesOf(legs(outOfRange))
                .equals(Arrays.asList(CAR, CAR));
        final int refusals = GatedSubtourModeChoice.GatedModule
                .BOUND_RIDE_REFUSALS.get() - before;
        final boolean counted = refusals == 2;
        ok &= unboundRefused && outOfRangeRefused && counted;
        json.append(",\"no_bound_trips_refused\":").append(unboundRefused)
            .append(",\"out_of_range_index_refused\":").append(outOfRangeRefused)
            .append(",\"refusals_counted\":").append(refusals)
            .append(",\"both_refusals_counted\":").append(counted);

        // --- 4. and an in-range index is accepted -------------------------
        final Plan bound = plan("bound",
                new String[] {"A", "B", "A"}, new String[] {CAR, CAR});
        bound.getPerson().getAttributes().putAttribute(
                GatedSubtourModeChoice.GatedModule.BOUND_RIDE_ATTRIBUTE, "1,2");
        run(bound, new String[] {CAR, RIDE}, new String[] {CAR},
            modes(CAR, RIDE));
        final boolean boundAccepted = modesOf(legs(bound))
                .equals(Arrays.asList(RIDE, RIDE));
        ok &= boundAccepted;
        json.append(",\"declared_ride_trips_accepted\":").append(boundAccepted);

        // --- 5. the attribute parser --------------------------------------
        final Plan parse = plan("parse",
                new String[] {"A", "B", "A"}, new String[] {CAR, CAR});
        final boolean absentIsEmpty = GatedSubtourModeChoice.GatedModule
                .boundTrips(parse, GatedSubtourModeChoice.GatedModule
                        .BOUND_RIDE_ATTRIBUTE).isEmpty();
        parse.getPerson().getAttributes().putAttribute(
                GatedSubtourModeChoice.GatedModule.BOUND_RIDE_ATTRIBUTE,
                " 1 , x ,3 , ");
        final Set<Integer> parsed = GatedSubtourModeChoice.GatedModule
                .boundTrips(parse, GatedSubtourModeChoice.GatedModule
                        .BOUND_RIDE_ATTRIBUTE);
        final boolean parsedTokens = parsed.equals(new HashSet<>(
                Arrays.asList(Integer.valueOf(1), Integer.valueOf(3))));
        ok &= absentIsEmpty && parsedTokens;
        json.append(",\"absent_attribute_is_empty\":").append(absentIsEmpty)
            .append(",\"malformed_token_names_nothing\":").append(parsedTokens);

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    /**
     * Run the gated plan algorithm once, with the run's own mode vocabulary.
     *
     * <p>The seed is reset so the run repeats, not to steer it: every fixture
     * here leaves MATSim exactly one candidate to apply.
     */
    private static void run(final Plan plan, final String[] modes,
                            final String[] chainBased,
                            final Collection<String> permissible) {
        MatsimRandom.reset(1L);
        final SubtourModeChoiceConfigGroup config =
                new SubtourModeChoiceConfigGroup();
        config.setModes(modes);
        config.setChainBasedModes(chainBased);
        // the subtour path only: the single-trip path is the seam #133
        // candidate 8 is not about, and it would make the outcome a coin flip
        config.setProbaForRandomSingleTripMode(0.0);
        config.setCoordDistance(0.0);
        final GlobalConfigGroup global = new GlobalConfigGroup();
        global.setNumberOfThreads(1);
        // both reach bounds off, as the registry declares them (0.0 km)
        final GatedSubtourModeChoice.GatedModule module =
                new GatedSubtourModeChoice.GatedModule(
                        global, config, new StubCalculator(permissible),
                        0.0, 0.0);
        final PlanAlgorithm algorithm = module.getPlanAlgoInstance();
        algorithm.run(plan);
    }

    /** A person with this plan: the bound-trip attributes live on the person. */
    private static Plan plan(final String who, final String[] activities,
                             final String[] modes) {
        final Person person = PopulationUtils.getFactory().createPerson(
                Id.create(who, Person.class));
        final Plan plan = PopulationUtils.createPlan(person);
        person.addPlan(plan);
        for (int i = 0; i < activities.length; i++) {
            plan.addActivity(activity(activities[i]));
            if (i < modes.length) {
                final Leg leg = PopulationUtils.createLeg(modes[i]);
                TripStructureUtils.setRoutingMode(leg, modes[i]);
                plan.addLeg(leg);
            }
        }
        return plan;
    }

    /** One activity per named location, five km apart on a straight line. */
    private static Activity activity(final String where) {
        final int index = where.charAt(0) - 'A';
        final Activity act = PopulationUtils.createActivityFromCoordAndLinkId(
                where.toLowerCase(java.util.Locale.ROOT),
                new Coord(5000.0 * index, 0.0),
                Id.create("l" + where, Link.class));
        act.setEndTime(8 * 3600.0 + 3600.0 * index);
        return act;
    }

    private static Collection<String> modes(final String... modes) {
        return Arrays.asList(modes);
    }

    private static List<Leg> legs(final Plan plan) {
        final List<Leg> out = new ArrayList<>();
        for (final PlanElement pe : plan.getPlanElements()) {
            if (pe instanceof Leg) {
                out.add((Leg) pe);
            }
        }
        return out;
    }

    private static List<String> modesOf(final List<Leg> legs) {
        final List<String> out = new ArrayList<>();
        for (final Leg leg : legs) {
            out.add(leg.getMode());
        }
        return out;
    }

    private static String join(final List<String> modes) {
        final StringBuilder sb = new StringBuilder();
        for (final String mode : modes) {
            if (sb.length() > 0) {
                sb.append(' ');
            }
            sb.append(mode);
        }
        return sb.toString();
    }

    /** Every mode the fixture declares available, for any plan. */
    private static final class StubCalculator
            implements PermissibleModesCalculator {

        private final Collection<String> modes;

        private StubCalculator(final Collection<String> modes) {
            this.modes = modes;
        }

        @Override
        public Collection<String> getPermissibleModes(final Plan plan) {
            return new ArrayList<>(this.modes);
        }
    }
}
