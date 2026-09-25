package citysim;

import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Population;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * The gate on {@link ActivityRetimes}, which both the ride engine (#187) and
 * the taxi fleet's executed wait (fourteenth report) write through:
 * <ul>
 * <li>a retime is what the plan carries during the mobsim - the taxi
 *     passenger held 977 s at the kerb leaves at 08:16:17, not 08:00;</li>
 * <li>restore puts the agent's own end time back, and an UNDEFINED end time
 *     comes back undefined, not as the overridden value;</li>
 * <li>an activity no longer in the selected plan is counted as an orphan and
 *     never written through the stale reference.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class ActivityRetimesProbe {

    private ActivityRetimesProbe() {
    }

    public static void main(final String[] args) {
        final Population pop = ScenarioUtils.createScenario(
                ConfigUtils.createConfig()).getPopulation();
        final Person p = pop.getFactory().createPerson(Id.createPersonId("p"));
        final Plan plan = PopulationUtils.createPlan(p);
        final Activity home = PopulationUtils.createActivityFromCoord("home", new Coord(0, 0));
        home.setEndTime(8 * 3600);
        final Activity shop = PopulationUtils.createActivityFromCoord("shop", new Coord(1, 1));
        plan.addActivity(home);
        plan.addLeg(PopulationUtils.createLeg("taxi"));
        plan.addActivity(shop);
        p.addPlan(plan);
        p.setSelectedPlan(plan);
        pop.addPerson(p);

        final ActivityRetimes r = new ActivityRetimes();
        r.set(p.getId(), home, 8 * 3600 + 977);
        r.set(p.getId(), shop, 9 * 3600);           // was undefined
        final boolean executed = home.getEndTime().seconds() == 8 * 3600 + 977
                && shop.getEndTime().seconds() == 9 * 3600;
        final int[] back = r.restore(pop);
        final boolean restored = back[0] == 2 && back[1] == 0
                && home.getEndTime().seconds() == 8 * 3600
                && !shop.getEndTime().isDefined()
                && r.size() == 0;

        // an orphan: the selected plan is swapped before the restore
        r.set(p.getId(), home, 8 * 3600 + 60);
        final Plan other = PopulationUtils.createPlan(p);
        other.addActivity(PopulationUtils.createActivityFromCoord("home", new Coord(0, 0)));
        p.addPlan(other);
        p.setSelectedPlan(other);
        final int[] orphaned = r.restore(pop);
        final boolean orphan = orphaned[0] == 0 && orphaned[1] == 1
                && home.getEndTime().seconds() == 8 * 3600 + 60;

        final boolean ok = executed && restored && orphan;
        System.out.println("{\"probe\":\"ActivityRetimesProbe\",\"executed\":" + executed
                + ",\"restored\":" + restored + ",\"orphan\":" + orphan
                + ",\"ok\":" + ok + "}");
        System.exit(ok ? 0 : 1);
    }
}
