package citysim;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.Node;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.utils.geometry.CoordUtils;

/**
 * No link receives more car-capable trip ends than it can move in the
 * modelled day (D28, F39; {@code activityLinks.capacityRule =
 * capacity_bounded}, RUN.routing.activity_link_capacity).
 *
 * <h2>The defect (fifteenth report)</h2>
 *
 * <p>The nearest-link rule of {@link ActivityLinkAssigner} attached the trip
 * ends of a big car park to the single service lane nearest its coordinate:
 * on F37, 29 service and living-street links carried trip ends needing up to
 * 38 h of their own sampled capacity, and car trips touching them averaged
 * 72.6 min at 13.4 km/h against a car mean of 25.0 min (HTS 17.2).
 *
 * <h2>The rule</h2>
 *
 * <p>A link's day capacity is an identity, not a choice: its own capacity in
 * vehicles an hour ({@code capacity x 3600 / capacityPeriod}) times the run's
 * {@code qsim.flowCapacityFactor} (the sample) times the modelled service
 * hours ({@code activityLinks.serviceHours}, RUN.routing.activity_link_service_hours,
 * derived from the mobsim's day).
 * The load is the planned trip ends of car-capable persons - a person whose
 * needed modes include {@code car} - counted on each person's SELECTED plan:
 * an activity reached by a leg and left by one is two trip ends, the day's
 * first and last one each. It is an upper bound on the vehicles the link will
 * see, which is the right side for a feasibility bound.
 *
 * <p>An overloaded link keeps, in population file order, every trip end it
 * can carry, and always keeps the trip ends of a person whose modes are
 * locked (a boundary agent on its cordon gate link, 9.58). Each later
 * person's activities at that coordinate - in EVERY plan, so a person's plans
 * agree on where a place is - move together to the next-nearest link that
 * carries the same needed modes (the {@link ActivityLinkAssigner} coverage
 * rule) and still has room; the search widens in rings over the mode
 * subnetwork's nodes and ranks candidates by point-to-segment distance, ties
 * by link id. Nothing is random, so the answer is a pure function of the
 * files. A person whose trip ends fit no link within the subnetwork's extent
 * stays where the nearest rule put them and is counted as unresolved.
 */
final class ActivityLinkCapacity {

    private static final Logger LOG = LogManager.getLogger(ActivityLinkCapacity.class);

    private ActivityLinkCapacity() {
    }

    /** One person's activities at one coordinate on one link, all plans. */
    static final class Group {
        final Person person;
        final Set<String> needed;
        final Coord coord;
        Id<Link> link;
        final List<Activity> activities = new ArrayList<>();
        int tripEnds = 0;
        final boolean movable;
        /** Position in population file order, then first appearance. */
        int order;

        Group(final Person person, final Set<String> needed, final Coord coord,
              final Id<Link> link, final boolean movable) {
            this.person = person;
            this.needed = needed;
            this.coord = coord;
            this.link = link;
            this.movable = movable;
        }
    }

    /** What the pass did, for the log line and the probe. */
    static final class Result {
        long overloadedBefore = 0;
        long groupsMoved = 0;
        long activitiesMoved = 0;
        long tripEndsMoved = 0;
        long unresolved = 0;
        long overloadedAfter = 0;
        double worstHours = 0.0;
        Id<Link> worstLink = null;
    }

    /**
     * Apply the bound to activities the nearest rule has already linked.
     *
     * @param neededOf each linked person's needed modes, in population order
     * @param subnetOf the mode subnetworks the nearest rule searched
     * @param movable  subpopulations whose modes innovate (a locked agent's
     *                 activities never move)
     */
    static Result apply(final Scenario scenario,
                        final Map<Person, Set<String>> neededOf,
                        final Map<Set<String>, Network> subnetOf,
                        final Set<String> movable,
                        final double serviceHours) {
        final Network network = scenario.getNetwork();
        final double perHour = 3600.0 / network.getCapacityPeriod()
                * scenario.getConfig().qsim().getFlowCapFactor();
        final List<Group> groups = collect(neededOf, movable);
        final Map<Id<Link>, List<Group>> onLink = new LinkedHashMap<>();
        for (final Group g : groups) {
            onLink.computeIfAbsent(g.link, k -> new ArrayList<>()).add(g);
        }
        final Result r = new Result();
        final Map<Id<Link>, Double> load = new HashMap<>();
        final List<Group> overflow = new ArrayList<>();
        for (final Map.Entry<Id<Link>, List<Group>> e : onLink.entrySet()) {
            final double cap = dayCapacity(network.getLinks().get(e.getKey()), perHour, serviceHours);
            double total = 0.0;
            for (final Group g : e.getValue()) {
                total += g.tripEnds;
            }
            if (total <= cap) {
                load.put(e.getKey(), total);
                continue;
            }
            r.overloadedBefore++;
            double kept = 0.0;
            for (final Group g : e.getValue()) {
                if (!g.movable) {
                    kept += g.tripEnds;
                }
            }
            for (final Group g : e.getValue()) {
                if (!g.movable) {
                    continue;
                }
                if (kept + g.tripEnds <= cap) {
                    kept += g.tripEnds;
                } else {
                    overflow.add(g);
                }
            }
            load.put(e.getKey(), kept);
        }
        // overflow in population order, the order the groups were collected
        overflow.sort((a, b) -> Integer.compare(a.order, b.order));
        final Map<Network, Double> spanOf = new HashMap<>();
        for (final Group g : overflow) {
            final Network subnet = subnetOf.get(g.needed);
            final Link target = subnet == null ? null
                    : nearestWithRoom(network, subnet, spanOf.computeIfAbsent(subnet,
                              ActivityLinkCapacity::span),
                              g, load, perHour, serviceHours);
            if (target == null) {
                r.unresolved++;
                load.merge(g.link, (double) g.tripEnds, Double::sum);
                continue;
            }
            load.merge(target.getId(), (double) g.tripEnds, Double::sum);
            g.link = target.getId();
            for (final Activity a : g.activities) {
                a.setLinkId(target.getId());
            }
            r.groupsMoved++;
            r.activitiesMoved += g.activities.size();
            r.tripEndsMoved += g.tripEnds;
        }
        for (final Map.Entry<Id<Link>, Double> e : load.entrySet()) {
            final Link link = network.getLinks().get(e.getKey());
            final double hourly = link.getCapacity() * perHour;
            final double hours = hourly > 0.0 ? e.getValue() / hourly : Double.POSITIVE_INFINITY;
            if (e.getValue() > dayCapacity(link, perHour, serviceHours)) {
                r.overloadedAfter++;
            }
            if (hours > r.worstHours || (hours == r.worstHours && r.worstLink != null
                    && e.getKey().compareTo(r.worstLink) < 0)) {
                r.worstHours = hours;
                r.worstLink = e.getKey();
            }
        }
        LOG.info("activityLinkCapacity: {} link(s) over their {} h of sampled capacity; moved "
                 + "{} activities ({} person-places, {} trip ends) to the next-nearest link "
                 + "with room; {} person-place(s) found none and stay; {} link(s) still over; "
                 + "worst remaining load {} h of its own capacity on link {} "
                 + "(RUN.routing.activity_link_capacity, D28)",
                 r.overloadedBefore, serviceHours, r.activitiesMoved, r.groupsMoved,
                 r.tripEndsMoved, r.unresolved, r.overloadedAfter,
                 String.format(java.util.Locale.ROOT, "%.2f", r.worstHours), r.worstLink);
        return r;
    }

    /** Trip ends the link can move in the modelled day at this sample. */
    static double dayCapacity(final Link link, final double perHour, final double serviceHours) {
        return link.getCapacity() * perHour * serviceHours;
    }

    /** Every person's activities, grouped by link and coordinate, in file order. */
    private static List<Group> collect(final Map<Person, Set<String>> neededOf,
                                       final Set<String> movable) {
        final List<Group> out = new ArrayList<>();
        for (final Map.Entry<Person, Set<String>> e : neededOf.entrySet()) {
            final Person person = e.getKey();
            final boolean carCapable = e.getValue().contains(TransportMode.car);
            final boolean canMove = movable.contains(PopulationUtils.getSubpopulation(person));
            final Map<String, Group> mine = new LinkedHashMap<>();
            final Plan selected = person.getSelectedPlan() != null
                    ? person.getSelectedPlan()
                    : (person.getPlans().isEmpty() ? null : person.getPlans().get(0));
            for (final Plan plan : person.getPlans()) {
                final List<PlanElement> pes = plan.getPlanElements();
                for (int i = 0; i < pes.size(); i++) {
                    if (!(pes.get(i) instanceof Activity)) {
                        continue;
                    }
                    final Activity act = (Activity) pes.get(i);
                    if (act.getLinkId() == null || act.getCoord() == null) {
                        continue;
                    }
                    final String key = act.getLinkId() + "|" + act.getCoord().getX()
                            + "|" + act.getCoord().getY();
                    final Group g = mine.computeIfAbsent(key, k -> new Group(
                            person, e.getValue(), act.getCoord(), act.getLinkId(), canMove));
                    g.activities.add(act);
                    if (carCapable && plan == selected) {
                        if (i > 0 && pes.get(i - 1) instanceof Leg) {
                            g.tripEnds++;
                        }
                        if (i + 1 < pes.size() && pes.get(i + 1) instanceof Leg) {
                            g.tripEnds++;
                        }
                    }
                }
            }
            for (final Group g : mine.values()) {
                if (g.tripEnds > 0) {
                    g.order = out.size();
                    out.add(g);
                }
            }
        }
        return out;
    }

    /**
     * The nearest link of the mode subnetwork, other than the group's own,
     * with room for the group's trip ends: rings over the subnetwork's nodes,
     * doubling from the length of the link being left, until the ring spans
     * the subnetwork. Null when no link anywhere has room.
     */
    private static Link nearestWithRoom(final Network network, final Network subnet,
                                        final double span,
                                        final Group g, final Map<Id<Link>, Double> load,
                                        final double perHour, final double serviceHours) {
        final Link from = network.getLinks().get(g.link);
        double radius = Math.max(from.getLength(),
                CoordUtils.distancePointLinesegment(from.getFromNode().getCoord(),
                        from.getToNode().getCoord(), g.coord));
        if (!(radius > 0.0)) {
            radius = Math.max(span / subnet.getNodes().size(), Double.MIN_NORMAL);
        }
        final java.util.Set<Id<Link>> tried = new java.util.HashSet<>();
        tried.add(g.link);
        while (true) {
            final List<Link> ring = candidates(subnet, g.coord, radius, tried);
            for (final Link c : ring) {
                tried.add(c.getId());
                final Link full = network.getLinks().get(c.getId());
                final double cap = dayCapacity(full, perHour, serviceHours);
                if (load.getOrDefault(c.getId(), 0.0) + g.tripEnds <= cap) {
                    return full;
                }
            }
            if (radius > span) {
                return null;
            }
            radius *= 2.0;
        }
    }

    /** The diagonal of the subnetwork's bounding box: the widest ring needed. */
    private static double span(final Network subnet) {
        final double[] box = NetworkUtils.getBoundingBox(subnet.getNodes().values());
        return Math.hypot(box[2] - box[0], box[3] - box[1]);
    }

    /** Subnetwork links touching a node within the radius, whose segment lies
     *  within it, not yet tried; nearest first, ties by id. */
    private static List<Link> candidates(final Network subnet, final Coord coord,
                                         final double radius,
                                         final java.util.Set<Id<Link>> tried) {
        final Collection<Node> nodes = NetworkUtils.getNearestNodes(subnet, coord, radius);
        final Map<Id<Link>, Double> dist = new HashMap<>();
        for (final Node n : nodes) {
            for (final Link l : n.getOutLinks().values()) {
                if (tried.contains(l.getId()) || dist.containsKey(l.getId())) {
                    continue;
                }
                final double d = CoordUtils.distancePointLinesegment(
                        l.getFromNode().getCoord(), l.getToNode().getCoord(), coord);
                if (d <= radius) {
                    dist.put(l.getId(), d);
                }
            }
            for (final Link l : n.getInLinks().values()) {
                if (tried.contains(l.getId()) || dist.containsKey(l.getId())) {
                    continue;
                }
                final double d = CoordUtils.distancePointLinesegment(
                        l.getFromNode().getCoord(), l.getToNode().getCoord(), coord);
                if (d <= radius) {
                    dist.put(l.getId(), d);
                }
            }
        }
        final List<Id<Link>> ids = new ArrayList<>(dist.keySet());
        ids.sort((a, b) -> {
            final int c = Double.compare(dist.get(a), dist.get(b));
            return c != 0 ? c : a.compareTo(b);
        });
        final List<Link> out = new ArrayList<>(ids.size());
        for (final Id<Link> id : ids) {
            out.add(subnet.getLinks().get(id));
        }
        return out;
    }
}
