package citysim;

import com.google.inject.Inject;
import java.util.*;
import org.apache.logging.log4j.LogManager;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.PersonArrivalEvent;
import org.matsim.api.core.v01.events.handler.PersonArrivalEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.mobsim.framework.MobsimAgent;
import org.matsim.core.mobsim.qsim.InternalInterface;
import org.matsim.core.mobsim.qsim.interfaces.DepartureHandler;
import org.matsim.core.mobsim.qsim.interfaces.MobsimEngine;
import org.matsim.core.mobsim.qsim.qnetsimengine.NetworkModeDepartureHandler;

/**
 * Coarse mode-specific supply pool. Requests wait in QSim, then enter the real
 * road network. A unit remains occupied until the passenger actually arrives,
 * followed by the declared turnaround. Waiting is part of experienced leg time.
 * This is not spatial dispatch: units have no location, empty repositioning does
 * not load roads, and the existing per-person vehicle proxy carries the trip.
 * Zero units are allowed and never rounded up. Timed-out requests abort the day
 * and incur native stuck scoring; a fallback journey is not invented.
 */
public final class HiredFleetQueue implements MobsimEngine, DepartureHandler,
        PersonArrivalEventHandler {
    public static final String COMPONENT = "citysimHiredFleetQueue";
    private record Request(double requested, MobsimAgent agent, Id<Link> link, String mode) { }
    private final HiredFleetConfigGroup cfg;
    private final EventsManager events;
    private InternalInterface internal;
    private NetworkModeDepartureHandler network;
    private final Map<String, PriorityQueue<Double>> free = new TreeMap<>();
    private final Map<String, PriorityQueue<Request>> pending = new TreeMap<>();
    private final Map<Id<Person>, String> active = new HashMap<>();
    private final Set<Id<Person>> waiting = new HashSet<>();
    private final Map<String, long[]> counts = new TreeMap<>();
    private final Map<String, Double> waitSeconds = new TreeMap<>();

    @Inject HiredFleetQueue(Scenario scenario, EventsManager events) {
        cfg = ConfigUtils.addOrGetModule(scenario.getConfig(), HiredFleetConfigGroup.class);
        this.events = events;
    }

    @Override public void setInternalInterface(InternalInterface value) { internal = value; }

    @Override public synchronized void beforeMobsim() {
        free.clear(); pending.clear(); active.clear(); waiting.clear(); counts.clear(); waitSeconds.clear();
        for (var entry : cfg.vehicles().entrySet()) {
            PriorityQueue<Double> units = new PriorityQueue<>();
            for (int i = 0; i < entry.getValue(); i++) units.add(Double.NEGATIVE_INFINITY);
            free.put(entry.getKey(), units);
            pending.put(entry.getKey(), new PriorityQueue<>(Comparator.comparingDouble(Request::requested)
                    .thenComparing(r -> r.agent().getId().toString())));
            counts.put(entry.getKey(), new long[3]);
            waitSeconds.put(entry.getKey(), 0.0);
        }
        network = null;
        for (DepartureHandler handler : internal.getDepartureHandlers()) {
            if (handler instanceof NetworkModeDepartureHandler found) {
                if (network != null) throw new IllegalStateException("Multiple native network departure handlers");
                network = found;
            }
        }
        if (network == null) throw new IllegalStateException("No native network departure handler");
        events.addHandler(this);
    }

    @Override public synchronized boolean handleDeparture(double now, MobsimAgent agent, Id<Link> link) {
        PriorityQueue<Request> queue = pending.get(agent.getMode());
        if (queue == null) return false;
        if (active.containsKey(agent.getId()) || !waiting.add(agent.getId()))
            throw new IllegalStateException("Duplicate hired request: " + agent.getId());
        queue.add(new Request(now, agent, link, agent.getMode()));
        counts.get(agent.getMode())[0]++;
        return true;
    }

    @Override public void doSimStep(double now) {
        List<Request> dispatch = new ArrayList<>(), refused = new ArrayList<>();
        synchronized (this) {
            for (var entry : pending.entrySet()) {
                String mode = entry.getKey();
                PriorityQueue<Request> queue = entry.getValue();
                PriorityQueue<Double> units = free.get(mode);
                while (!queue.isEmpty()) {
                    Request request = queue.peek();
                    double wait = now - request.requested();
                    // The deadline is inclusive: a unit available exactly then can serve.
                    if (wait > cfg.maxWaitSeconds) {
                        queue.poll(); waiting.remove(request.agent().getId());
                        counts.get(mode)[2]++; refused.add(request); continue;
                    }
                    if (units.isEmpty() || units.peek() > now) break;
                    queue.poll(); units.poll(); waiting.remove(request.agent().getId());
                    active.put(request.agent().getId(), mode);
                    counts.get(mode)[1]++; waitSeconds.merge(mode, wait, Double::sum);
                    dispatch.add(request);
                }
            }
        }
        for (Request request : dispatch) {
            if (!network.handleDeparture(now, request.agent(), request.link()))
                throw new IllegalStateException("Native network refused hired departure: " + request.mode());
        }
        for (Request request : refused) abort(request, now);
    }

    @Override public synchronized void handleEvent(PersonArrivalEvent event) {
        String mode = active.remove(event.getPersonId());
        if (mode == null) return;
        if (!mode.equals(event.getLegMode()))
            throw new IllegalStateException("Hired arrival mode differs from active request");
        free.get(mode).add(event.getTime() + cfg.turnaroundSeconds);
    }

    private void abort(Request request, double now) {
        request.agent().setStateToAbort(now);
        internal.arrangeNextAgentState(request.agent());
    }

    @Override public void afterMobsim() {
        events.removeHandler(this);
        double now = internal.getMobsim().getSimTimer().getTimeOfDay();
        for (var entry : pending.entrySet()) {
            String mode = entry.getKey();
            int unserved = entry.getValue().size();
            while (!entry.getValue().isEmpty()) abort(entry.getValue().poll(), now);
            long[] value = counts.get(mode);
            long unfinished = active.values().stream().filter(mode::equals).count();
            LogManager.getLogger(HiredFleetQueue.class).info(
                    "hiredFleet: mode={} vehicles={} requested={} dispatched={} timedOut={} queuedAtEnd={} activeAtEnd={} servedWaitSeconds={}",
                    mode, cfg.vehicles().get(mode), value[0], value[1], value[2], unserved, unfinished, waitSeconds.get(mode));
        }
        waiting.clear(); active.clear();
    }
}
