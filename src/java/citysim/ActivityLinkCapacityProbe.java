package citysim;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.Node;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PopulationFactory;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.config.groups.ReplanningConfigGroup.StrategySettings;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.scenario.ScenarioUtils;

/**
 * The gate on capacity-aware activity links (D28, F39;
 * RUN.routing.activity_link_capacity), on a toy built in memory.
 *
 * <p>A service lane {@code lane} (10 veh/h) runs 10 m from a car park where
 * 50 residents and one locked boundary agent start and end their day by car;
 * a road {@code near} (1,000 veh/h) runs 190 m away and another, {@code far},
 * 510 m away. At a 0.25 flow factor over a 30 h day the lane moves 75 trip
 * ends; each person puts 2 there.
 * <ul>
 * <li>{@code nearest_is_f38}: under {@code nearest} every car-park activity
 *     sits on the lane (102 trip ends on a 75 trip-end link);</li>
 * <li>{@code lane_within_capacity}: under {@code capacity_bounded} the lane
 *     keeps 74 trip ends - the locked agent's 2 first, then residents in file
 *     order while they fit - and the rest move;</li>
 * <li>{@code moved_to_next_nearest}: the moved residents are the LAST in file
 *     order and sit on {@code near}, not {@code far};</li>
 * <li>{@code plans_agree}: a moved person's second plan moved with the first;</li>
 * <li>{@code locked_kept}: the boundary agent keeps the lane;</li>
 * <li>{@code deterministic}: two independent builds give identical links.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class ActivityLinkCapacityProbe {

    private static final int RESIDENTS = 50;

    private ActivityLinkCapacityProbe() {
    }

    public static void main(final String[] args) {
        final Scenario nearest = build(ActivityLinksConfigGroup.CAPACITY_NEAREST);
        ActivityLinkAssigner.run(nearest);
        final List<String> f38 = homeLinks(nearest);
        final boolean nearestIsF38 = f38.stream().allMatch("lane"::equals);

        final Scenario bounded = build(ActivityLinksConfigGroup.CAPACITY_BOUNDED);
        ActivityLinkAssigner.run(bounded);
        final List<String> after = homeLinks(bounded);
        final Scenario again = build(ActivityLinksConfigGroup.CAPACITY_BOUNDED);
        ActivityLinkAssigner.run(again);
        final boolean deterministic = after.equals(homeLinks(again));

        // after: index 0 is the locked agent, then residents r00..r49 in order
        final boolean lockedKept = "lane".equals(after.get(0));
        int onLane = 0;
        int firstMoved = -1;
        boolean movedNear = true;
        boolean contiguous = true;
        for (int i = 1; i < after.size(); i++) {
            if ("lane".equals(after.get(i))) {
                onLane++;
                if (firstMoved >= 0) {
                    contiguous = false;           // a later person kept, an earlier moved
                }
            } else {
                if (firstMoved < 0) {
                    firstMoved = i;
                }
                movedNear &= "near".equals(after.get(i));
            }
        }
        // the lane: 10 veh/h x 0.25 x 30 h = 75 trip ends; the locked agent's
        // 2 plus 36 residents' 72 = 74, and a 37th would make 76
        final boolean laneWithin = onLane == 36 && (onLane + 1) * 2 <= 75;
        final boolean movedToNext = contiguous && movedNear && firstMoved == 37;
        boolean plansAgree = true;
        for (final Person p : bounded.getPopulation().getPersons().values()) {
            final Id<Link> selected = firstLink(p.getSelectedPlan());
            for (final Plan plan : p.getPlans()) {
                plansAgree &= firstLink(plan).equals(selected);
            }
        }
        final boolean ok = nearestIsF38 && laneWithin && movedToNext && plansAgree
                && lockedKept && deterministic;
        System.out.println("{\"probe\":\"ActivityLinkCapacityProbe\",\"nearest_is_f38\":" + nearestIsF38
                + ",\"lane_within_capacity\":" + laneWithin
                + ",\"residents_on_lane\":" + onLane
                + ",\"moved_to_next_nearest\":" + movedToNext
                + ",\"plans_agree\":" + plansAgree
                + ",\"locked_kept\":" + lockedKept
                + ",\"deterministic\":" + deterministic
                + ",\"ok\":" + ok + "}");
        System.exit(ok ? 0 : 1);
    }

    private static Id<Link> firstLink(final Plan plan) {
        return ((Activity) plan.getPlanElements().get(0)).getLinkId();
    }

    /** Each person's first activity link, in population order. */
    private static List<String> homeLinks(final Scenario s) {
        final List<String> out = new ArrayList<>();
        for (final Person p : s.getPopulation().getPersons().values()) {
            out.add(firstLink(p.getSelectedPlan()).toString());
        }
        return out;
    }

    private static Scenario build(final String rule) {
        final ActivityLinksConfigGroup links = new ActivityLinksConfigGroup();
        links.assignment = ActivityLinksConfigGroup.COMMON;
        links.capacityRule = rule;
        links.serviceHours = 30.0;
        final Config config = ConfigUtils.createConfig(links);
        config.qsim().setFlowCapFactor(0.25);
        config.routing().setNetworkModes(List.of("car"));
        config.subtourModeChoice().setModes(new String[] {"car", "walk"});
        final StrategySettings smc = new StrategySettings();
        smc.setStrategyName("SubtourModeChoice");
        smc.setWeight(0.1);
        config.replanning().addStrategySettings(smc);   // residents: subpopulation null
        final Scenario s = ScenarioUtils.createScenario(config);
        final Network net = s.getNetwork();
        net.setCapacityPeriod(3600.0);
        link(net, "lane", 0, 0, 100, 0, 10.0);
        link(net, "near", 0, 200, 100, 200, 1000.0);
        link(net, "far", 0, -500, 100, -500, 1000.0);
        link(net, "work", 5000, 0, 5100, 0, 1000.0);
        final PopulationFactory pf = s.getPopulation().getFactory();
        final Person locked = person(pf, "external0", 1);
        PopulationUtils.putSubpopulation(locked, "external");
        s.getPopulation().addPerson(locked);
        for (int i = 0; i < RESIDENTS; i++) {
            s.getPopulation().addPerson(person(pf, String.format("r%02d", i), 2));
        }
        return s;
    }

    private static void link(final Network net, final String id, final double x0,
                             final double y0, final double x1, final double y1,
                             final double capacity) {
        final Node a = net.getFactory().createNode(Id.createNodeId(id + "_a"), new Coord(x0, y0));
        final Node b = net.getFactory().createNode(Id.createNodeId(id + "_b"), new Coord(x1, y1));
        net.addNode(a);
        net.addNode(b);
        final Link l = net.getFactory().createLink(Id.createLinkId(id), a, b);
        l.setLength(Math.hypot(x1 - x0, y1 - y0));
        l.setCapacity(capacity);
        l.setFreespeed(10.0);
        l.setNumberOfLanes(1.0);
        l.setAllowedModes(Set.of("car"));
        net.addLink(l);
    }

    /** Home at the car park, work far away, by car; {@code plans} copies. */
    private static Person person(final PopulationFactory pf, final String id, final int plans) {
        final Person p = pf.createPerson(Id.createPersonId(id));
        for (int k = 0; k < plans; k++) {
            final Plan plan = pf.createPlan();
            final Activity home = pf.createActivityFromCoord("home", new Coord(50, 10));
            home.setEndTime(8 * 3600);
            plan.addActivity(home);
            plan.addLeg(pf.createLeg("car"));
            final Activity work = pf.createActivityFromCoord("work", new Coord(5050, 10));
            work.setEndTime(17 * 3600);
            plan.addActivity(work);
            plan.addLeg(pf.createLeg("car"));
            plan.addActivity(pf.createActivityFromCoord("home", new Coord(50, 10)));
            p.addPlan(plan);
        }
        p.setSelectedPlan(p.getPlans().get(0));
        return p;
    }
}
