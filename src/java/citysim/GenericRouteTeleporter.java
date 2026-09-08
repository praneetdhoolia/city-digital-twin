package citysim;

import com.google.inject.Inject;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.core.config.Config;
import org.matsim.core.mobsim.framework.MobsimAgent;
import org.matsim.core.mobsim.qsim.InternalInterface;
import org.matsim.core.mobsim.qsim.interfaces.DepartureHandler;
import org.matsim.core.mobsim.qsim.interfaces.MobsimEngine;
import org.matsim.core.population.routes.NetworkRoute;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.utils.misc.OptionalTime;

/**
 * Teleports the transit router's non-network stub legs, and REFUSES every
 * other main-mode leg that arrives here without a network route.
 *
 * <p>Why it exists (DECISIONS.md 9.54): the transit router's access/egress and
 * direct-walk legs keep mode {@code walk} with a generic beeline route, and
 * once walk is a qsim main mode the vehicular machinery would otherwise claim
 * and crash on them (measured — the 9.54 probe died in
 * {@code PopulationAgentSource} exactly there). MAIN walk trips carry network
 * routes and never reach this class: it claims a departure only when the leg's
 * route is NOT a network route.
 *
 * <p>The teleport itself is MATSim's own semantics: arrive at the route's
 * travel time. A generic main-mode leg without a travel time is refused
 * loudly — inventing a duration here would be a silent modelling choice.
 *
 * <h2>The guard is mode-aware, and it names what it refuses</h2>
 *
 * <p>Until 8 September 2026 the guard asked only whether the mode was a qsim
 * main mode. It was not asking which one. A {@code car}, {@code truck},
 * {@code bike}, {@code motorbike} or {@code taxi} leg that reached the mobsim
 * carrying a generic route — a router failure, not a modelling choice — was
 * teleported like any stub: it contributed NO link volume, entered no queue,
 * met no signal, and surfaced only inside one undifferentiated
 * {@code teleported=} number (75,357 of them on the last iteration of arm
 * 20260907T182742, mode unknown). That is a direct breach of GOAL.md
 * requirement 1, <i>every mode is simulated in the mobsim — no teleportation</i>,
 * and it is the kind of leakage that bears on traffic counts running under
 * observation (#82).
 *
 * <h2>What is teleportable, and on whose say-so</h2>
 *
 * <p>The split is DECLARED, not judged. Two config facts decide it, both read
 * from the scenario at {@code beforeMobsim} and never typed in here:
 *
 * <ul>
 *   <li>{@code routing.networkModes} — the modes the city declares as routed
 *       on the network ({@code RUN.routing.network_modes}: car, ride, truck,
 *       motorbike, walk, bike, taxi). A generic route on one of these is a
 *       ROUTING FAILURE, and the house style is to refuse rather than invent
 *       (the same stance as the missing-travel-time throw above).</li>
 *   <li>{@code qsim.mainMode} — the modes the qsim simulates physically
 *       ({@code RUN.qsim.main_mode}). Anything outside it never reaches this
 *       class; it is the teleportation engine's business.</li>
 * </ul>
 *
 * <p>Their intersection — car, truck, motorbike, bike, taxi and walk under
 * today's declaration — is the set that must be physical. {@link #STUB_MODE}
 * is the single documented exception carved out of it, and it is carved out on
 * MEASUREMENT rather than on preference: over the 3.77 M legs of arm
 * 20260906T233901's output plans, EVERY main-mode leg carrying a generic route
 * is walk (520,385 with routing mode {@code pt} — the transit router's own
 * stubs, the 9.54 case — plus 441 with no routing mode recorded), and not one
 * {@code car} (1,334,892 legs), {@code taxi} (336,452), {@code bike}
 * (202,877), {@code truck} (40,612) or {@code motorbike} (2,612) leg carries
 * anything but {@code links}. So the refusal fires on nothing that the model
 * does today: it is the tripwire for the day routing fails silently, which is
 * exactly the failure that went three iterations unseen inside a single
 * counter.
 *
 * <h2>The counters</h2>
 *
 * <p>One counter per {@code mode via routingMode}, so the log says WHICH mode
 * was teleported and how often instead of how many legs in total. Two traps
 * from DECISIONS.md 9.156 are avoided by construction. <b>Scope:</b> the
 * counters live on this object, which {@code CitysimControler} binds
 * {@code asEagerSingleton()} inside the QSim module — one instance per mobsim,
 * not one per routing thread, which is how {@code NetworkDirectWalkPtRouter}'s
 * plain {@code int} fields came to count nothing on an unscoped provider
 * binding. They are {@code AtomicLong}s in a {@code ConcurrentHashMap} anyway,
 * because departures reach a qsim engine from more than the main loop.
 * <b>Sampling:</b> there is none. No {@code % N} guard is used — the one that
 * wrote 19,469 lines because it never fired is not repeated by writing a
 * cleverer one. The table is emitted once per mobsim in {@code afterMobsim},
 * sorted, bounded by the number of declared modes.
 */
public final class GenericRouteTeleporter implements MobsimEngine, DepartureHandler {

    private static final Logger LOG =
            LogManager.getLogger(GenericRouteTeleporter.class);

    /** The qsim components name this engine registers under. */
    public static final String COMPONENT = "citysimGenericRouteTeleporter";

    /**
     * The ONE main mode whose generic route is legitimate here.
     *
     * <p>MATSim's own constant, not a city value: {@code TransportMode.walk}
     * is the mode the transit router puts on the access/egress and direct-walk
     * stubs it builds without touching the network (DECISIONS.md 9.54). Every
     * other declared network mode is refused below.
     */
    public static final String STUB_MODE = TransportMode.walk;

    private InternalInterface internalInterface;

    private static final class Pending {
        final double arrival;
        final MobsimAgent agent;
        final Id<Link> destination;
        final long seq;
        /** The counter key this departure was booked under. */
        final String key;

        Pending(final double arrival, final MobsimAgent agent,
                final Id<Link> destination, final long seq, final String key) {
            this.arrival = arrival;
            this.agent = agent;
            this.destination = destination;
            this.seq = seq;
            this.key = key;
        }
    }

    /** Ordered by arrival, then insertion order - deterministic. */
    private final PriorityQueue<Pending> queue = new PriorityQueue<>(
            Comparator.<Pending>comparingDouble(p -> p.arrival)
                    .thenComparingLong(p -> p.seq));
    private long seq;

    /** Teleports completed this mobsim, per `mode via routingMode`. */
    private final Map<String, AtomicLong> teleportedByMode =
            new ConcurrentHashMap<>();
    /** Departures still in flight at sim end, per `mode via routingMode`. */
    private final Map<String, AtomicLong> abortedByMode =
            new ConcurrentHashMap<>();

    /** Declared qsim main modes; resolved from config, never typed in. */
    private volatile Set<String> mainModes;
    /** Declared network modes that are also main modes, less {@link #STUB_MODE}. */
    private volatile Set<String> mustBePhysical;

    @Inject
    GenericRouteTeleporter() {
    }

    @Override
    public boolean handleDeparture(final double now, final MobsimAgent agent,
                                   final Id<Link> linkId) {
        final org.matsim.core.mobsim.framework.PlanAgent planAgent =
                (org.matsim.core.mobsim.framework.PlanAgent) agent;
        final Object element = planAgent.getCurrentPlanElement();
        if (!(element instanceof Leg)) {
            return false;
        }
        final Leg leg = (Leg) element;
        if (leg.getRoute() == null || leg.getRoute() instanceof NetworkRoute) {
            return false;                    // physical - the netsim's business
        }
        Set<String> main = this.mainModes;
        if (main == null) {          // once per run; never on the hot path after
            resolveDeclaredModes();
            main = this.mainModes;
        }
        final String mode = leg.getMode();
        if (!main.contains(mode)) {
            return false;                    // the teleportation engine's business
        }
        final String routingMode = TripStructureUtils.getRoutingMode(leg);
        if (this.mustBePhysical.contains(mode)) {
            // The house stance of this class, applied to the mode as well as
            // to the clock: refuse rather than invent. A leg of a DECLARED
            // network mode reached the mobsim without a network route, so the
            // router failed; teleporting it would hide the failure as link
            // volume that never happened (GOAL.md requirement 1).
            throw new IllegalStateException(
                    "generic-route leg on mode `" + mode + "`, which "
                    + "routing.networkModes declares NETWORK-ROUTED: refusing "
                    + "to teleport a mode that must be simulated (GOAL.md "
                    + "requirement 1; DECISIONS.md 9.54). agent="
                    + agent.getId() + " routingMode=" + routingMode
                    + " departureLink=" + linkId
                    + " destinationLink=" + agent.getDestinationLinkId()
                    + " departureTime=" + now
                    + " route=" + leg.getRoute().getClass().getSimpleName()
                    + " teleportable main modes here: " + STUB_MODE
                    + ". The router produced no network route for this leg - "
                    + "fix the routing, do not teleport it.");
        }
        final OptionalTime time = leg.getRoute().getTravelTime();
        if (!time.isDefined()) {
            throw new IllegalStateException(
                    "generic-route main-mode leg with no travel time for agent "
                    + agent.getId() + " (" + mode + "): refusing to "
                    + "invent a duration (DECISIONS.md 9.54)");
        }
        this.queue.add(new Pending(now + time.seconds(), agent,
                                   agent.getDestinationLinkId(), this.seq++,
                                   key(mode, routingMode)));
        return true;
    }

    /** `mode via routingMode`, the granularity the run's log reports. */
    private static String key(final String mode, final String routingMode) {
        return mode + " via " + (routingMode == null ? "(none)" : routingMode);
    }

    private static void bump(final Map<String, AtomicLong> counters,
                             final String key) {
        counters.computeIfAbsent(key, k -> new AtomicLong()).incrementAndGet();
    }

    /**
     * Reads the two declared mode sets out of the scenario config once.
     *
     * <p>Called from {@code beforeMobsim} and defensively from the departure
     * path, so the sets exist however the qsim orders its callbacks.
     */
    private synchronized void resolveDeclaredModes() {
        if (this.mainModes != null) {
            return;
        }
        final Config config =
                this.internalInterface.getMobsim().getScenario().getConfig();
        final Set<String> declaredMain =
                new LinkedHashSet<>(config.qsim().getMainModes());
        final Set<String> physical = new LinkedHashSet<>(declaredMain);
        physical.retainAll(config.routing().getNetworkModes());
        physical.remove(STUB_MODE);
        this.mustBePhysical = physical;
        this.mainModes = declaredMain;      // published last: it is the guard
        LOG.info("genericRouteTeleporter: teleportable main mode is `{}` only; "
                 + "generic-route legs REFUSED for {} (qsim.mainMode {} "
                 + "intersected with routing.networkModes {})",
                 STUB_MODE, physical, declaredMain,
                 config.routing().getNetworkModes());
    }

    @Override
    public void doSimStep(final double now) {
        while (!this.queue.isEmpty() && this.queue.peek().arrival <= now) {
            final Pending p = this.queue.poll();
            p.agent.notifyArrivalOnLinkByNonNetworkMode(p.destination);
            p.agent.endLegAndComputeNextState(now);
            this.internalInterface.arrangeNextAgentState(p.agent);
            bump(this.teleportedByMode, p.key);
        }
    }

    @Override
    public void beforeMobsim() {
        this.queue.clear();
        this.seq = 0L;
        this.teleportedByMode.clear();
        this.abortedByMode.clear();
        resolveDeclaredModes();            // once per run: the config cannot move
    }

    @Override
    public void afterMobsim() {
        while (!this.queue.isEmpty()) {
            final Pending p = this.queue.poll();
            p.agent.setStateToAbort(this.internalInterface.getMobsim()
                    .getSimTimer().getTimeOfDay());
            this.internalInterface.arrangeNextAgentState(p.agent);
            bump(this.abortedByMode, p.key);
        }
        // ONE line per mobsim, every mode named, sorted so two runs of one
        // build print it identically. No sampling guard - see the class
        // Javadoc on DECISIONS.md 9.156.
        long teleported = 0L;
        final StringBuilder perMode = new StringBuilder();
        for (final Map.Entry<String, AtomicLong> e
                : new TreeMap<>(this.teleportedByMode).entrySet()) {
            teleported += e.getValue().get();
            if (perMode.length() > 0) {
                perMode.append(", ");
            }
            perMode.append(e.getKey()).append('=').append(e.getValue().get());
        }
        long aborted = 0L;
        final StringBuilder perModeAborted = new StringBuilder();
        for (final Map.Entry<String, AtomicLong> e
                : new TreeMap<>(this.abortedByMode).entrySet()) {
            aborted += e.getValue().get();
            if (perModeAborted.length() > 0) {
                perModeAborted.append(", ");
            }
            perModeAborted.append(e.getKey()).append('=')
                    .append(e.getValue().get());
        }
        LOG.info("genericRouteTeleporter: teleported={} [{}] "
                 + "abortedAtSimEnd={} [{}]",
                 teleported,
                 perMode.length() == 0 ? "none" : perMode.toString(),
                 aborted,
                 perModeAborted.length() == 0 ? "none" : perModeAborted.toString());
    }

    @Override
    public void setInternalInterface(final InternalInterface internalInterface) {
        this.internalInterface = internalInterface;
    }
}
