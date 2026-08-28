package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.concurrent.ConcurrentHashMap;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.LinkLeaveEvent;
import org.matsim.api.core.v01.events.handler.LinkLeaveEventHandler;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.contrib.signals.controller.AbstractSignalController;
import org.matsim.contrib.signals.controller.SignalController;
import org.matsim.contrib.signals.controller.SignalControllerFactory;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalGroupSettingsData;
import org.matsim.contrib.signals.model.DatabasedSignalPlan;
import org.matsim.contrib.signals.model.Signal;
import org.matsim.contrib.signals.model.SignalGroup;
import org.matsim.contrib.signals.model.SignalPlan;
import org.matsim.contrib.signals.model.SignalSystem;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;

/**
 * SCATS-style adaptive signal control (DECISIONS.md 9.88, issue #73).
 *
 * <p><b>Why this exists.</b> The operated SCATS phase data for the Hunter/Scott
 * corridor was never released. The project's earlier handling was to leave
 * {@code A.signals.scats_phasing} unobtained and sweep a FIXED cycle time, and
 * every arm to date has therefore run 14 intersections on a fixed 110 s plan.
 * The standing directive forbids leaving an unavailable input swept when it can
 * be derived, and for signalling the derivable thing is not the timings — it is
 * the ALGORITHM that would have produced them. This class implements that
 * algorithm and lets the intersection compute its own timings from the traffic
 * the mobsim actually presents.
 *
 * <h2>What SCATS does, and what this implements</h2>
 *
 * <p>SCATS is built on one measured primitive and three adaptations of it.
 *
 * <p><b>The primitive — degree of saturation (DS).</b> For each movement,
 * the fraction of the green that was actually used to discharge vehicles. Here
 * it is measured directly from the mobsim rather than modelled: every vehicle
 * crossing a signalised stop line emits a {@link LinkLeaveEvent} on the
 * approach link, {@link Discharge} counts them, and
 *
 * <pre>   DS = served / (saturationFlowPerLane × lanes × green ÷ 3600)</pre>
 *
 * is the served count against what that green COULD have discharged at
 * saturation. A movement that discharges everything it is given reads 1.0; one
 * that empties halfway through its green reads 0.5.
 *
 * <p><b>Adaptation 1 — cycle length (CL).</b> SCATS lengthens the cycle while
 * the CRITICAL (busiest) movement runs above a target degree of saturation and
 * shortens it while every movement runs below, in bounded increments rather
 * than jumping to a computed optimum, because a single noisy cycle must not
 * destroy coordination. Implemented in {@link #adaptCycle}.
 *
 * <p><b>Adaptation 2 — phase splits (SP).</b> SCATS distributes the available
 * green so that the degree of saturation is EQUALISED across competing stages:
 * a stage running hotter than its neighbours is given more of the next cycle.
 * Implemented in {@link #adaptSplits}, subject to the declared minimum green,
 * and preserving the plan's own clearance (intergreen) times exactly — those
 * are safety values derived from the intersection's geometry, not capacity
 * knobs, and nothing here may trade them away.
 *
 * <p><b>Adaptation 3 — offsets (OS).</b> <b>NOT implemented, deliberately.</b>
 * SCATS selects offsets from a per-subsystem library that operators tune
 * against observed platoon behaviour. That library is exactly the unreleased
 * artefact, and there is no algorithm to fall back on: an offset invented here
 * would be this file asserting a coordination pattern nobody measured, which is
 * the failure mode the whole exercise exists to avoid. Each system therefore
 * keeps the offset its generated plan declares, and the corridor's coordination
 * remains a stated limitation rather than a fabricated input.
 *
 * <h2>The variable-cycle clock</h2>
 *
 * <p>A fixed-time controller can find its place in the cycle with modular
 * arithmetic — {@code (t − offset) mod cycle}. An adaptive one cannot: the
 * moment the cycle length changes, that arithmetic silently reinterprets every
 * past cycle boundary and the plan jumps. This controller therefore keeps an
 * EXPLICIT cycle start ({@link #cycleStart}) and length ({@link #cycleLen}),
 * advances the start by the length actually served, and re-times only at a
 * boundary. A cycle in progress is never re-timed underneath itself.
 *
 * <h2>Determinism</h2>
 *
 * <p>No wall clock and no {@code Random}. Every per-system map is a
 * {@link TreeMap} or {@link LinkedHashMap} built in a fixed order, and the
 * per-cycle arithmetic is integer seconds, so two runs of one build produce
 * identical switching.
 *
 * <h2>What this does NOT claim</h2>
 *
 * <p>This is SCATS's published control LOGIC applied to measured saturation.
 * It is not the operated Newcastle configuration, and no arm run under it may
 * be described as reproducing observed signal timings. It replaces an assumed
 * constant with a derived mechanism, and the mechanism's own parameters are
 * declared and swept like every other.
 */
public final class ScatsSignalController extends AbstractSignalController {

    private static final Logger LOG =
            LogManager.getLogger(ScatsSignalController.class);

    /** The identifier a signal system names to select this controller. */
    public static final String IDENTIFIER = "CitysimScats";

    private static final int SECONDS_PER_HOUR = 3600;

    // ------------------------------------------------------------------
    // discharge measurement
    // ------------------------------------------------------------------

    /**
     * Counts stop-line discharges per link, for every signalised link.
     *
     * <p>One instance is shared by every system's controller and registered
     * once on the events manager. A vehicle leaving a signalised approach link
     * has crossed that stop line, so the count IS the served volume — no
     * detector model, no occupancy proxy, and nothing inferred from the plan
     * the controller is trying to evaluate.
     */
    public static final class Discharge implements LinkLeaveEventHandler {

        private final Map<Id<Link>, int[]> counts = new ConcurrentHashMap<>();

        void watch(final Id<Link> linkId) {
            this.counts.computeIfAbsent(linkId, k -> new int[1]);
        }

        @Override
        public void handleEvent(final LinkLeaveEvent event) {
            final int[] cell = this.counts.get(event.getLinkId());
            if (cell != null) {
                cell[0]++;
            }
        }

        int read(final Id<Link> linkId) {
            final int[] cell = this.counts.get(linkId);
            return cell == null ? 0 : cell[0];
        }

        @Override
        public void reset(final int iteration) {
            for (final int[] cell : this.counts.values()) {
                cell[0] = 0;
            }
        }
    }

    // ------------------------------------------------------------------
    // one stage of the plan
    // ------------------------------------------------------------------

    /**
     * A stage: the groups that turn green and red together, and the green they
     * are given.
     *
     * <p>Groups are keyed by their (onset, dropping) window rather than
     * one-per-group, because the generated plans deliberately run more than one
     * group on the same window — the corridor stage and the tram stage share
     * theirs. Re-timing them independently would split a stage in half.
     */
    private static final class Stage {
        final List<Id<SignalGroup>> groups = new ArrayList<>();
        final TreeSet<Id<Link>> links = new TreeSet<>();
        int onset;
        int drop;
        int green;              // seconds of green as planned this cycle
        int clearanceAfter;     // intergreen to the next stage, preserved
        double lanes;           // summed lanes across the stage's approaches
        double ds;              // smoothed degree of saturation
        int servedAtCycleStart; // discharge counter reading when green began
    }

    // ------------------------------------------------------------------
    // state
    // ------------------------------------------------------------------

    private final ScatsConfigGroup params;
    private final Discharge discharge;
    private final Network network;
    /**
     * Saturation flow per lane AS THE MOBSIM ENFORCES IT, veh/h of green.
     *
     * <p>The declared 1900 veh/h/lane is a full-scale, real-world value, but a
     * sampled run does not move full-scale traffic: MATSim scales every link's
     * discharge by {@code qsim.flowCapacityFactor}, so a 25% run's links pass
     * a quarter of the vehicles per hour of green and a 1% run's a hundredth.
     * Measuring the degree of saturation against the UNSCALED value therefore
     * divides a sampled count by a full-scale capacity and reads a quarter (or
     * a hundredth) of the truth - every intersection would look permanently
     * empty and SCATS would drive every cycle to its floor. Measured on the
     * first probe: criticalDS=0.000 at a 1% sample, cycle collapsing 110 -> 38 s
     * with traffic present. The factor belongs in the denominator because it is
     * already in the physics.
     */
    private final double effectiveSaturationFlow;

    private SignalPlan activePlan;
    private final List<Stage> stages = new ArrayList<>();
    private int offset;
    private int baseCycle;

    /** The explicit cycle clock — see the class comment. */
    private double cycleStart = Double.NEGATIVE_INFINITY;
    private int cycleLen;

    private final TreeSet<Id<SignalGroup>> onsetFired = new TreeSet<>();
    private final TreeSet<Id<SignalGroup>> dropFired = new TreeSet<>();

    private long cyclesServed;
    private double cycleLenSum;
    /** Throttle on the re-timing log: proof, not a firehose. */
    private int retimingsLogged;
    private static final int RETIMINGS_LOGGED_MAX = 12;

    ScatsSignalController(final ScatsConfigGroup params,
                          final Discharge discharge,
                          final Network network,
                          final double effectiveSaturationFlow) {
        this.params = params;
        this.discharge = discharge;
        this.network = network;
        this.effectiveSaturationFlow = effectiveSaturationFlow;
    }

    // ------------------------------------------------------------------
    // lifecycle
    // ------------------------------------------------------------------

    @Override
    public void simulationInitialized(final double timeSeconds) {
        resolvePlan();
        this.cyclesServed = 0;
        this.cycleLenSum = 0;
        this.cycleLen = this.baseCycle;

        // Start the first cycle on the same boundary a fixed-time controller
        // would have used, so an adaptive run and a fixed-time run of the same
        // plan begin identically and diverge only where the algorithm acts.
        final long tSec = (long) Math.floor(timeSeconds);
        final long rel = tSec - this.offset;
        final long idx = Math.floorDiv(rel, Math.max(1, this.baseCycle));
        this.cycleStart = (double) (this.offset + idx * (long) this.baseCycle);

        beginCycle();
        // Set every group's PRESENT colour explicitly: a mobsim starting
        // mid-cycle must not leave a group in an undefined state.
        final int pos = (int) Math.floor(timeSeconds - this.cycleStart);
        for (final Stage st : this.stages) {
            for (final Id<SignalGroup> gid : st.groups) {
                if (pos >= st.onset) {
                    this.onsetFired.add(gid);
                }
                if (pos >= st.drop) {
                    this.dropFired.add(gid);
                }
                if (pos >= st.onset && pos < st.drop) {
                    this.system.scheduleOnset(timeSeconds, gid);
                } else {
                    this.system.scheduleDropping(timeSeconds, gid);
                }
            }
        }
    }

    @Override
    public void updateState(final double timeSeconds) {
        if (this.activePlan == null) {
            return;
        }
        // Close and re-time the cycle at its boundary. `while` rather than
        // `if`: a mobsim step longer than a short cycle must not leave the
        // clock behind the simulation.
        while (timeSeconds >= this.cycleStart + this.cycleLen) {
            endCycle();
            this.cycleStart += this.cycleLen;
            if (this.params.isScats()) {
                adaptCycle();
                adaptSplits();
            }
            beginCycle();
        }
        final int pos = (int) Math.floor(timeSeconds - this.cycleStart);
        for (final Stage st : this.stages) {
            for (final Id<SignalGroup> gid : st.groups) {
                if (!this.onsetFired.contains(gid) && pos >= st.onset) {
                    this.system.scheduleOnset(timeSeconds, gid);
                    this.onsetFired.add(gid);
                    st.servedAtCycleStart = servedNow(st);
                }
                if (!this.dropFired.contains(gid) && pos >= st.drop) {
                    this.system.scheduleDropping(timeSeconds, gid);
                    this.dropFired.add(gid);
                }
            }
        }
    }

    private void beginCycle() {
        this.onsetFired.clear();
        this.dropFired.clear();
        for (final Stage st : this.stages) {
            st.servedAtCycleStart = servedNow(st);
        }
    }

    /** Read each stage's realised saturation and fold it into the filter. */
    private void endCycle() {
        this.cyclesServed++;
        this.cycleLenSum += this.cycleLen;
        if (!this.params.isScats()) {
            return;
        }
        final double alpha = this.params.getDsSmoothing();
        for (final Stage st : this.stages) {
            final int served = servedNow(st) - st.servedAtCycleStart;
            final double capacity = this.effectiveSaturationFlow
                    * st.lanes * st.green / SECONDS_PER_HOUR;
            final double raw = capacity <= 0 ? 0.0 : served / capacity;
            // A stage cut to its floor can read above 1.0 - it discharged more
            // than a saturated green of that length should allow, because the
            // queue kept moving through the clearance. That IS the signal that
            // it is starved, so it is kept rather than clipped.
            st.ds = alpha * raw + (1.0 - alpha) * st.ds;
        }
    }

    private int servedNow(final Stage st) {
        int n = 0;
        for (final Id<Link> l : st.links) {
            n += this.discharge.read(l);
        }
        return n;
    }

    // ------------------------------------------------------------------
    // the two adaptations
    // ------------------------------------------------------------------

    /**
     * Cycle length toward the target degree of saturation, one bounded step.
     *
     * <p>The critical movement decides: while the busiest stage runs above the
     * target the cycle grows (a longer cycle spends proportionally less of the
     * hour on clearance, so it carries more), and only when EVERY stage is
     * comfortably below does it shrink. The deadband is what stops the cycle
     * hunting either side of a target it can never land on exactly.
     */
    private void adaptCycle() {
        double critical = 0.0;
        for (final Stage st : this.stages) {
            critical = Math.max(critical, st.ds);
        }
        final double target = this.params.getTargetDegreeSaturation();
        final double band = this.params.getDsDeadband();
        final int step = (int) Math.round(this.params.getCycleStepS());
        int next = this.cycleLen;
        if (critical > target + band) {
            next = this.cycleLen + step;
        } else if (critical < target - band) {
            next = this.cycleLen - step;
        }
        final int before = this.cycleLen;
        final int lo = (int) Math.round(this.params.getMinCycleS());
        final int hi = (int) Math.round(this.params.getMaxCycleS());
        // The cycle can never be shorter than the clearance it must serve plus
        // a minimum green for every stage; that floor is the intersection's
        // geometry, and it outranks the declared minimum cycle.
        int floor = 0;
        for (final Stage st : this.stages) {
            floor += st.clearanceAfter + (int) Math.round(
                    this.params.getMinGreenS());
        }
        this.cycleLen = Math.max(Math.max(lo, floor), Math.min(hi, next));
        // Proof that the algorithm is ALIVE, not a firehose: the first dozen
        // re-timings per system are logged with the measurement that caused
        // them, so a probe can show cycle length actually moving off the
        // generated plan instead of the run merely completing happily.
        if (this.cycleLen != before
                && this.retimingsLogged < RETIMINGS_LOGGED_MAX) {
            this.retimingsLogged++;
            LOG.info("scats system={} cycle {}s -> {}s (criticalDS={} "
                     + "target={} band={})", this.system.getId(), before,
                     this.cycleLen, String.format("%.3f", critical), target,
                     band);
        }
    }

    /**
     * Green in proportion to demand, so saturation equalises across stages.
     *
     * <p>The available green is what the cycle leaves after every clearance is
     * paid — clearances are preserved exactly, because they are the
     * intersection's safety geometry rather than capacity to reallocate. What
     * remains is split in proportion to each stage's smoothed degree of
     * saturation, then every stage is lifted to the declared minimum green and
     * the excess taken back from the stages that have most to spare.
     */
    private void adaptSplits() {
        int clearance = 0;
        for (final Stage st : this.stages) {
            clearance += st.clearanceAfter;
        }
        final int minGreen = (int) Math.round(this.params.getMinGreenS());
        final int available = this.cycleLen - clearance;
        if (available < this.stages.size() * minGreen) {
            return;                       // cannot re-split; adaptCycle's floor
        }
        double total = 0.0;
        for (final Stage st : this.stages) {
            total += st.ds;
        }
        final int[] green = new int[this.stages.size()];
        if (total <= 0) {
            // no demand anywhere this cycle: hold the plan's own proportions
            // rather than inventing an even split
            int planned = 0;
            for (final Stage st : this.stages) {
                planned += st.green;
            }
            for (int i = 0; i < this.stages.size(); i++) {
                green[i] = planned <= 0 ? available / this.stages.size()
                        : (int) Math.round(
                                available * (this.stages.get(i).green
                                        / (double) planned));
            }
        } else {
            for (int i = 0; i < this.stages.size(); i++) {
                green[i] = (int) Math.round(
                        available * (this.stages.get(i).ds / total));
            }
        }
        // minimum green, then reconcile the rounding against the widest stage
        // so the greens sum to the available time exactly
        for (int i = 0; i < green.length; i++) {
            green[i] = Math.max(minGreen, green[i]);
        }
        int sum = 0;
        for (final int g : green) {
            sum += g;
        }
        int slack = available - sum;
        while (slack != 0) {
            int pick = -1;
            for (int i = 0; i < green.length; i++) {
                if (slack < 0 && green[i] <= minGreen) {
                    continue;             // never cut a stage below its floor
                }
                if (pick < 0 || green[i] > green[pick]) {
                    pick = i;
                }
            }
            if (pick < 0) {
                break;                    // everything is at the floor
            }
            final int move = slack > 0 ? 1 : -1;
            green[pick] += move;
            slack -= move;
        }
        // rebuild the cycle: stage, its clearance, next stage
        int cursor = 0;
        for (int i = 0; i < this.stages.size(); i++) {
            final Stage st = this.stages.get(i);
            st.onset = cursor;
            st.green = green[i];
            st.drop = cursor + green[i];
            cursor = st.drop + st.clearanceAfter;
        }
    }

    // ------------------------------------------------------------------
    // plan resolution
    // ------------------------------------------------------------------

    /**
     * Read the generated plan into stages, once per mobsim.
     *
     * <p>The plan is the STARTING point, never a constraint: SCATS begins from
     * the timings the builder generated and re-times from there, so a run whose
     * first cycles look like the fixed-time plan is behaving correctly.
     */
    private void resolvePlan() {
        this.stages.clear();
        this.activePlan = null;
        if (this.signalPlans == null || this.signalPlans.isEmpty()) {
            throw new IllegalStateException(
                    "signal system " + this.system.getId() + " selects "
                    + IDENTIFIER + " but carries no signal plan - the control "
                    + "file names the controller, the plan generator writes "
                    + "the timings, and one of them did not happen");
        }
        this.activePlan = this.signalPlans.values().iterator().next();
        if (!(this.activePlan instanceof DatabasedSignalPlan)) {
            throw new IllegalStateException(
                    "signal system " + this.system.getId() + " carries a "
                    + this.activePlan.getClass().getSimpleName()
                    + ", not the contrib's DatabasedSignalPlan; " + IDENTIFIER
                    + " reads the plan's own seconds and cannot proceed");
        }
        final DatabasedSignalPlan plan = (DatabasedSignalPlan) this.activePlan;
        this.offset = plan.getOffset().intValue();
        this.baseCycle = plan.getCycleTime().intValue();

        // group the plan's groups by their (onset, dropping) window
        final TreeMap<Long, Stage> byWindow = new TreeMap<>();
        for (final Map.Entry<Id<SignalGroup>, SignalGroupSettingsData> e
                : plan.getPlanData().getSignalGroupSettingsDataByGroupId()
                        .entrySet()) {
            final SignalGroupSettingsData s = e.getValue();
            final int on = s.getOnset();
            final int off = s.getDropping();
            final long key = ((long) on << 20) | (long) off;
            final Stage st = byWindow.computeIfAbsent(key, k -> {
                final Stage fresh = new Stage();
                fresh.onset = on;
                fresh.drop = off;
                return fresh;
            });
            st.groups.add(e.getKey());
        }
        this.stages.addAll(byWindow.values());
        this.stages.sort((a, b) -> Integer.compare(a.onset, b.onset));

        // approach links and lanes per stage, and register them for counting
        for (final Stage st : this.stages) {
            for (final Id<SignalGroup> gid : st.groups) {
                final SignalGroup g = this.system.getSignalGroups().get(gid);
                if (g == null) {
                    continue;
                }
                for (final Signal sig : g.getSignals().values()) {
                    st.links.add(sig.getLinkId());
                }
            }
            for (final Id<Link> lid : st.links) {
                final Link link = this.network.getLinks().get(lid);
                st.lanes += link == null ? 1.0 : link.getNumberOfLanes();
                this.discharge.watch(lid);
            }
            st.green = Math.max(0, st.drop - st.onset);
            st.ds = 0.0;
        }
        // clearance to the NEXT stage, wrapping the last back to the first;
        // taken from the plan so the intersection's own intergreens survive
        for (int i = 0; i < this.stages.size(); i++) {
            final Stage st = this.stages.get(i);
            final Stage next = this.stages.get((i + 1) % this.stages.size());
            st.clearanceAfter = i + 1 < this.stages.size()
                    ? Math.max(0, next.onset - st.drop)
                    : Math.max(0, this.baseCycle - st.drop + next.onset);
        }
    }

    /** Mean served cycle length, for the run's own telemetry. */
    public double meanCycleS() {
        return this.cyclesServed == 0 ? 0.0
                : this.cycleLenSum / this.cyclesServed;
    }

    // ------------------------------------------------------------------
    // factory
    // ------------------------------------------------------------------

    /**
     * Builds one controller per signal system and shares the discharge
     * counter, which is registered on the events manager exactly once.
     */
    public static final class Factory implements SignalControllerFactory {

        private final ScatsConfigGroup params;
        private final Discharge discharge;
        private final Network network;
        private final double effectiveSaturationFlow;

        @Inject
        Factory(final Config config, final EventsManager events,
                final Scenario scenario) {
            this.params = ConfigUtils.addOrGetModule(config,
                    ScatsConfigGroup.NAME, ScatsConfigGroup.class);
            if (this.params.getRegime().isEmpty()) {
                throw new IllegalStateException(
                        "a signal system selects " + IDENTIFIER + " but the "
                        + "scats config module was never populated - the entry "
                        + "point registers it and the run-input builder writes "
                        + "it; refusing to run on a regime nobody chose");
            }
            this.network = scenario.getNetwork();
            this.discharge = new Discharge();
            events.addHandler(this.discharge);
            final double flowCapFactor = config.qsim().getFlowCapFactor();
            if (flowCapFactor <= 0) {
                throw new IllegalStateException(
                        "qsim.flowCapacityFactor is " + flowCapFactor
                        + "; the degree of saturation is measured against the "
                        + "saturation flow the mobsim actually enforces, and "
                        + "that is the declared flow times this factor");
            }
            this.effectiveSaturationFlow =
                    this.params.getSaturationFlowVehHLane() * flowCapFactor;
            LOG.info("scats: regime={} targetDS={} cycle {}..{} step {} "
                     + "smoothing={} satflow={}/lane/h x flowCapFactor {} = "
                     + "{}/lane/h effective minGreen={}",
                     this.params.getRegime(),
                     this.params.getTargetDegreeSaturation(),
                     this.params.getMinCycleS(), this.params.getMaxCycleS(),
                     this.params.getCycleStepS(), this.params.getDsSmoothing(),
                     this.params.getSaturationFlowVehHLane(), flowCapFactor,
                     this.effectiveSaturationFlow,
                     this.params.getMinGreenS());
        }

        @Override
        public SignalController createSignalSystemController(
                final SignalSystem signalSystem) {
            final ScatsSignalController controller =
                    new ScatsSignalController(this.params, this.discharge,
                                              this.network,
                                              this.effectiveSaturationFlow);
            controller.setSignalSystem(signalSystem);
            return controller;
        }
    }
}
