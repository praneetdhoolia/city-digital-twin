package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.concurrent.ConcurrentHashMap;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.events.LinkEnterEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.LinkEnterEventHandler;
import org.matsim.api.core.v01.events.handler.TransitDriverStartsEventHandler;
import org.matsim.api.core.v01.network.Link;
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
import org.matsim.core.api.experimental.events.VehicleArrivesAtFacilityEvent;
import org.matsim.core.api.experimental.events.VehicleDepartsAtFacilityEvent;
import org.matsim.core.api.experimental.events.handler.VehicleArrivesAtFacilityEventHandler;
import org.matsim.core.api.experimental.events.handler.VehicleDepartsAtFacilityEventHandler;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.vehicles.Vehicle;

/**
 * A plan-based signal controller with bounded tram priority (issue #73).
 *
 * <p>Semantics follow the project's signalling dossier — the Melbourne PU/AU
 * machinery: the controller EXECUTES the fixed-time plan it is handed (cycle,
 * offset, per-group onset and dropping seconds), and a detected tram may
 * locally deform ONE cycle of it, never the plan itself. Every deformation is
 * bounded by a per-cycle budget ({@code priorityBudgetShare * cycleTime}), and
 * with compensation enabled whatever a competing stage lost in cycle N it is
 * given back in cycle N+1 out of the tram stage's slack, so the plan's
 * long-run splits are conserved.
 *
 * <p><b>The priority group.</b> The stage that carries the priority vehicle
 * is the signal group whose id equals the declared
 * {@code tramPriority.priorityGroupId} ({@code "tram"} for the light-rail
 * variants; {@code "corridor"} for the BRT variant, whose buses run in the
 * corridor car lanes and whose priority stage IS the corridor stage — issue
 * #73). A system without such a group runs pure fixed time under this
 * controller — identically to
 * {@code DefaultPlanbasedSignalSystemController}, whose delegation arithmetic
 * this class reimplements (cycle position {@code (t - offset) mod cycle},
 * onsets and droppings scheduled at the plan's seconds).
 *
 * <p><b>Detection.</b> A tram is detected for a system when a TRANSIT vehicle
 * (identified by {@code TransitDriverStartsEvent} — never by string-matching
 * ids) enters any link that carries one of that system's tram-group signals.
 * The declared {@code detectionDistanceM} is approximated by that approach
 * link's upstream boundary: MATSim's queue model has no intra-link position
 * (see {@link TramPriorityConfigGroup#getDetectionDistanceM()}).
 *
 * <p><b>Modes</b> (see {@link TramPriorityConfigGroup}):
 * <ul>
 * <li>{@code off}: the plan verbatim.</li>
 * <li>{@code green_extension}: a tram detected while its stage is green with
 *     the dropping at most {@code extensionWindowS} away DELAYS that dropping
 *     (and the pending competing onsets) by up to {@code extensionWindowS},
 *     within the cycle budget; the time is borrowed from the longest
 *     competing green.</li>
 * <li>{@code extension_recall}: additionally, a tram detected while its stage
 *     is red may TRUNCATE the running competing stage — but only after every
 *     currently-green group has had the plan's own minimum green (the
 *     shortest onset-to-dropping spacing the plan declares; no constant is
 *     invented here, the generated plans respect the declared minimum green)
 *     — and recall the tram stage early, same budget.</li>
 * <li>{@code conditional}: either action, but ONLY for a tram whose schedule
 *     delay (from the transit events' own {@code getDelay()} bookkeeping)
 *     exceeds {@code latenessThresholdS}.</li>
 * </ul>
 *
 * <p><b>Determinism.</b> Everything is driven by {@code updateState(t)} and
 * by event arrival within the events manager's per-step synchronisation — no
 * wall clock, no {@code Random}, and every iteration order in this class runs
 * over sorted maps/sets, so two runs of the same build produce the same
 * signal event stream.
 *
 * <p><b>Stated simplifications</b> (all documented rather than silent): the
 * deformation arithmetic assumes the corridor's plans are "normally oriented"
 * (each group's onset precedes its dropping within the cycle) — a
 * wrapped-green stage still executes correctly as fixed time but is never
 * deformed; recall pushes a not-yet-started competing onset to the tram
 * stage's dropping second, which is exact for the two-stage controls the
 * corridor builder emits and conservative for anything richer.
 */
public final class TramPriorityController extends AbstractSignalController
        implements SignalController {

    /** The identifier the signal control data names to select this class. */
    public static final String IDENTIFIER = "CitysimTramPriority";

    /** The reserved signal group id that marks the tram stage. */
    public static final String TRAM_GROUP_ID = "tram";

    private static final Logger LOG =
            LogManager.getLogger(TramPriorityController.class);

    private final TramPriorityConfigGroup params;
    private final TramDetection detection;

    // regime flags, fixed at construction
    private final boolean off;
    private final boolean allowRecall;
    private final boolean conditional;

    // plan-derived state, resolved in simulationInitialized (the model
    // objects - groups, signals - are only reliably wired by then)
    private DatabasedSignalPlan activePlan;
    private int cycle;
    private int offset;
    /** plan seconds per group: [onset, dropping], insertion-ordered by id. */
    private final TreeMap<Id<SignalGroup>, int[]> planSeconds = new TreeMap<>();
    private Id<SignalGroup> tramGroupId;
    private int minGreenFloorS;
    private Id<SignalGroup> longestCompetingGreen;

    // per-cycle working state
    private long currentCycleIdx = Long.MIN_VALUE;
    private final TreeMap<Id<SignalGroup>, Integer> workingOnset = new TreeMap<>();
    private final TreeMap<Id<SignalGroup>, Integer> workingDrop = new TreeMap<>();
    private final TreeSet<Id<SignalGroup>> onsetFired = new TreeSet<>();
    private final TreeSet<Id<SignalGroup>> dropFired = new TreeSet<>();
    private int budgetUsedS;
    /** seconds borrowed from a group this cycle, repaid next cycle. */
    private final TreeMap<Id<SignalGroup>, Integer> ledger = new TreeMap<>();

    TramPriorityController(final TramPriorityConfigGroup params,
                           final TramDetection detection) {
        this.params = params;
        this.detection = detection;
        final String mode = params.getMode();
        this.off = TramPriorityConfigGroup.MODE_OFF.equals(mode);
        this.allowRecall =
                TramPriorityConfigGroup.MODE_EXTENSION_RECALL.equals(mode)
                || TramPriorityConfigGroup.MODE_CONDITIONAL.equals(mode);
        this.conditional =
                TramPriorityConfigGroup.MODE_CONDITIONAL.equals(mode);
    }

    // ------------------------------------------------------------------
    // SignalController
    // ------------------------------------------------------------------

    /**
     * Re-entrant per-mobsim initialisation. The signals contrib may keep one
     * controller across iterations while the mobsim is rebuilt, so everything
     * here resets cleanly: plan resolution, per-cycle state, the ledger, and
     * the detection registration (the detection service clears itself at each
     * events reset).
     */
    @Override
    public void simulationInitialized(final double timeSeconds) {
        resolvePlan(timeSeconds);
        this.currentCycleIdx = Long.MIN_VALUE;
        this.ledger.clear();
        this.budgetUsedS = 0;

        // The priority stage and its approach links exist only if the plan
        // carries a group whose id equals the declared priorityGroupId
        // ("tram" for the light-rail variants, "corridor" for the BRT variant
        // whose buses run in the corridor car lanes - issue #73, S3
        // remainder); without one this controller is pure fixed time and
        // never registers for detection.
        final String priorityGid = this.params.getPriorityGroupId().isEmpty()
                ? TRAM_GROUP_ID : this.params.getPriorityGroupId();
        this.tramGroupId = null;
        for (final Id<SignalGroup> gid : this.planSeconds.keySet()) {
            if (priorityGid.equals(gid.toString())) {
                this.tramGroupId = gid;
            }
        }
        if (this.tramGroupId != null && !this.off) {
            final SignalGroup tramGroup =
                    this.system.getSignalGroups().get(this.tramGroupId);
            final TreeSet<Id<Link>> approaches = new TreeSet<>();
            if (tramGroup != null) {
                for (final Signal s : tramGroup.getSignals().values()) {
                    approaches.add(s.getLinkId());
                }
            }
            this.detection.register(this.system.getId(), approaches);
        }
        computeGreenStatistics();

        // Establish the current cycle and set every group's PRESENT state
        // explicitly, so a mobsim that starts mid-cycle does not leave groups
        // in an undefined colour until their next plan second arrives.
        final long tSec = (long) Math.floor(timeSeconds);
        final long rel = tSec - this.offset;
        beginCycle(Math.floorDiv(rel, this.cycle));
        final int pos = (int) Math.floorMod(rel, this.cycle);
        for (final Map.Entry<Id<SignalGroup>, int[]> e
                : this.planSeconds.entrySet()) {
            final Id<SignalGroup> gid = e.getKey();
            final int onset = this.workingOnset.get(gid);
            final int drop = this.workingDrop.get(gid);
            // mark the events this cycle has already passed as fired
            if (onset <= pos) {
                this.onsetFired.add(gid);
            }
            if (drop <= pos) {
                this.dropFired.add(gid);
            }
            if (inGreen(pos, onset, drop)) {
                this.system.scheduleOnset(timeSeconds, gid);
            } else {
                this.system.scheduleDropping(timeSeconds, gid);
            }
        }
    }

    @Override
    public void updateState(final double timeSeconds) {
        if (this.activePlan == null) {
            return;
        }
        final long tSec = (long) Math.floor(timeSeconds);
        final long rel = tSec - this.offset;
        final long cycleIdx = Math.floorDiv(rel, this.cycle);
        final int pos = (int) Math.floorMod(rel, this.cycle);
        if (cycleIdx != this.currentCycleIdx) {
            beginCycle(cycleIdx);
        }
        if (!this.off && this.tramGroupId != null) {
            applyPriority(pos);
        }
        // Fire the working schedule. Onset and dropping are independent
        // events within the cycle (a wrapped green drops before it onsets),
        // fired once each when the cycle position reaches their second -
        // ">=" rather than "==" so a mobsim that starts mid-cycle, or a
        // deformation applied in the same step, cannot skip one.
        for (final Id<SignalGroup> gid : this.planSeconds.keySet()) {
            if (!this.onsetFired.contains(gid)
                    && pos >= this.workingOnset.get(gid)) {
                this.system.scheduleOnset(timeSeconds, gid);
                this.onsetFired.add(gid);
            }
            if (!this.dropFired.contains(gid)
                    && pos >= this.workingDrop.get(gid)) {
                this.system.scheduleDropping(timeSeconds, gid);
                this.dropFired.add(gid);
            }
        }
    }

    // ------------------------------------------------------------------
    // cycle machinery
    // ------------------------------------------------------------------

    /**
     * Open cycle {@code cycleIdx}: reset the working schedule to the plan,
     * then - with compensation enabled - repay last cycle's borrowings by
     * moving each owed group's ONSET earlier by what it is owed, truncating
     * whatever stage (in practice the tram's) occupied the reclaimed window.
     * Extending the owed green at its start keeps the repair contiguous and
     * inside one cycle; the time comes out of the tram/priority slack, so the
     * plan's long-run splits are conserved.
     */
    private void beginCycle(final long cycleIdx) {
        this.currentCycleIdx = cycleIdx;
        this.onsetFired.clear();
        this.dropFired.clear();
        this.budgetUsedS = 0;
        this.workingOnset.clear();
        this.workingDrop.clear();
        for (final Map.Entry<Id<SignalGroup>, int[]> e
                : this.planSeconds.entrySet()) {
            this.workingOnset.put(e.getKey(), e.getValue()[0]);
            this.workingDrop.put(e.getKey(), e.getValue()[1]);
        }
        // a detection left over from the previous cycle is stale: the tram
        // either passed, or sits first in queue for the onset this new cycle
        // grants anyway - carrying it over would double-serve one tram
        if (!this.off && this.tramGroupId != null) {
            this.detection.clear(this.system.getId());
        }
        if (!this.params.isCompensationEnabled() || this.ledger.isEmpty()) {
            this.ledger.clear();
            return;
        }
        final StringBuilder repaid = new StringBuilder();
        for (final Map.Entry<Id<SignalGroup>, Integer> owed
                : this.ledger.entrySet()) {
            final Id<SignalGroup> gid = owed.getKey();
            if (gid.equals(this.tramGroupId)) {
                continue; // the tram never gets compensation, it took the time
            }
            final int oldOnset = this.workingOnset.get(gid);
            final int amount = Math.min(owed.getValue(), oldOnset);
            if (amount <= 0) {
                continue;
            }
            final int newOnset = oldOnset - amount;
            for (final Id<SignalGroup> other : this.planSeconds.keySet()) {
                if (other.equals(gid)) {
                    continue;
                }
                final int otherDrop = this.workingDrop.get(other);
                if (otherDrop > newOnset && otherDrop <= oldOnset) {
                    this.workingDrop.put(other, newOnset);
                }
            }
            this.workingOnset.put(gid, newOnset);
            if (repaid.length() > 0) {
                repaid.append(", ");
            }
            repaid.append(gid).append("+").append(amount).append("s");
        }
        if (repaid.length() > 0) {
            LOG.info("tramPriority compensation: system={} cycle={} "
                     + "returned [{}] out of the tram stage's slack",
                     this.system.getId(), cycleIdx, repaid);
        }
        this.ledger.clear();
    }

    /**
     * Act on a pending detection, deforming the current cycle within the
     * budget. The detection stays LATCHED until it is either acted on or
     * ruled out (an on-time tram in conditional mode; cycle end clears the
     * rest): a tram detected a few seconds before its dropping enters the
     * window rather than being discarded by the first non-actionable step.
     */
    private void applyPriority(final int pos) {
        final TramDetection.Pending pending =
                this.detection.peek(this.system.getId());
        if (pending == null) {
            return;
        }
        if (this.conditional
                && pending.delayS <= this.params.getLatenessThresholdS()) {
            // conditional mode: an on-time tram earns nothing; unknown delay
            // reads as 0 (never late), so an unobserved tram is not promoted
            this.detection.clear(this.system.getId());
            return;
        }
        final int budgetCap = (int) Math.floor(
                this.params.getPriorityBudgetShare() * this.cycle);
        final int remaining = budgetCap - this.budgetUsedS;
        if (remaining <= 0) {
            return;
        }
        final Id<SignalGroup> tram = this.tramGroupId;
        final int tramOnset = this.workingOnset.get(tram);
        final int tramDrop = this.workingDrop.get(tram);
        if (tramOnset >= tramDrop) {
            return; // wrapped tram green: executed as fixed time, not deformed
        }
        final boolean tramGreen = this.onsetFired.contains(tram)
                && !this.dropFired.contains(tram);
        boolean acted = false;
        if (tramGreen) {
            acted = extendGreen(pos, tramDrop, remaining);
        } else if (this.allowRecall && !this.onsetFired.contains(tram)
                && tramOnset > pos) {
            acted = recall(pos, tramOnset, remaining);
        }
        if (acted) {
            this.detection.clear(this.system.getId());
        }
    }

    /**
     * Green extension: the tram stage is green and its dropping is within
     * {@code extensionWindowS} - hold it green by up to the window, bounded
     * by the cycle budget, and push the pending competing onsets back with
     * it. The borrowed time is booked against the longest competing green.
     */
    private boolean extendGreen(final int pos, final int tramDrop,
                                final int remaining) {
        if (tramDrop <= pos
                || tramDrop - pos > this.params.getExtensionWindowS()) {
            return false; // dropping already past, or not yet within the window
        }
        int delta = Math.min(
                (int) Math.floor(this.params.getExtensionWindowS()), remaining);
        // the extended green must stay inside the cycle
        delta = Math.min(delta, this.cycle - 1 - tramDrop);
        // every pending competing onset moves with the dropping and must
        // keep at least one second of green before its own dropping
        final List<Id<SignalGroup>> shifted = new ArrayList<>();
        for (final Id<SignalGroup> gid : this.planSeconds.keySet()) {
            if (gid.equals(this.tramGroupId)
                    || this.onsetFired.contains(gid)) {
                continue;
            }
            final int onset = this.workingOnset.get(gid);
            final int drop = this.workingDrop.get(gid);
            if (onset < tramDrop || onset >= drop) {
                continue; // starts before the tram ends, or wrapped: untouched
            }
            shifted.add(gid);
            delta = Math.min(delta, drop - onset - 1);
            delta = Math.min(delta, this.cycle - 1 - onset);
        }
        if (delta <= 0) {
            return false;
        }
        this.workingDrop.put(this.tramGroupId, tramDrop + delta);
        for (final Id<SignalGroup> gid : shifted) {
            this.workingOnset.put(gid, this.workingOnset.get(gid) + delta);
        }
        this.budgetUsedS += delta;
        this.ledger.merge(this.longestCompetingGreen, delta, Integer::sum);
        return true;
    }

    /**
     * Early recall: the tram stage is red. Once every currently-green group
     * has had the plan's own minimum green (the shortest declared
     * onset-to-dropping spacing - no invented constant), truncate the running
     * stage(s) now and pull the tram onset forward, bounded by the budget.
     */
    private boolean recall(final int pos, final int tramOnset,
                           final int remaining) {
        // min-green floor first: a stage that has not had the plan's own
        // shortest green keeps its right of way, tram or no tram
        for (final Id<SignalGroup> gid : this.planSeconds.keySet()) {
            if (gid.equals(this.tramGroupId)) {
                continue;
            }
            if (this.onsetFired.contains(gid) && !this.dropFired.contains(gid)
                    && pos - this.workingOnset.get(gid) < this.minGreenFloorS) {
                return false;
            }
        }
        final int recallS = Math.min(tramOnset - (pos + 1), remaining);
        if (recallS <= 0) {
            return false;
        }
        final int newTramOnset = tramOnset - recallS;
        // truncate the running competing stage(s); book the borrowed time
        // against the longest green among them (else the longest overall)
        Id<SignalGroup> paidBy = null;
        int paidByGreen = -1;
        for (final Id<SignalGroup> gid : this.planSeconds.keySet()) {
            if (gid.equals(this.tramGroupId)) {
                continue;
            }
            if (this.onsetFired.contains(gid)
                    && !this.dropFired.contains(gid)) {
                this.workingDrop.put(gid, pos); // fires this very step
                final int green = greenLength(this.planSeconds.get(gid));
                if (green > paidByGreen) {
                    paidByGreen = green;
                    paidBy = gid;
                }
            }
        }
        // a pending competing onset that would land inside the advanced tram
        // green waits for the tram's dropping (exact for two-stage controls)
        final int tramDrop = this.workingDrop.get(this.tramGroupId);
        for (final Id<SignalGroup> gid : this.planSeconds.keySet()) {
            if (gid.equals(this.tramGroupId)
                    || this.onsetFired.contains(gid)) {
                continue;
            }
            final int onset = this.workingOnset.get(gid);
            if (onset >= newTramOnset && onset < tramDrop) {
                this.workingOnset.put(gid,
                        Math.min(tramDrop, this.cycle - 1));
            }
        }
        this.workingOnset.put(this.tramGroupId, newTramOnset);
        this.budgetUsedS += recallS;
        this.ledger.merge(paidBy != null ? paidBy : this.longestCompetingGreen,
                recallS, Integer::sum);
        return true;
    }

    // ------------------------------------------------------------------
    // plan resolution
    // ------------------------------------------------------------------

    /**
     * Pick the plan active at {@code timeSeconds} and read its arithmetic.
     *
     * <p>The corridor builder emits exactly one plan per system; when several
     * exist the one whose [start, end) contains the (day-wrapped) time wins,
     * else the lowest id - deterministic either way. The plan must be the
     * contrib's {@link DatabasedSignalPlan}: it is the only implementation
     * the {@code FromDataBuilder} constructs, and the only one that exposes
     * the settings data this controller's own delegation arithmetic needs.
     */
    private void resolvePlan(final double timeSeconds) {
        if (this.signalPlans == null || this.signalPlans.isEmpty()) {
            throw new IllegalStateException(
                    "signal system " + this.system.getId() + " selects "
                    + IDENTIFIER + " but carries no signal plan - the control "
                    + "data is incomplete");
        }
        final TreeMap<Id<SignalPlan>, SignalPlan> sorted =
                new TreeMap<>(this.signalPlans);
        SignalPlan chosen = null;
        if (sorted.size() == 1) {
            chosen = sorted.firstEntry().getValue();
        } else {
            final double dayTime = timeSeconds % 86400.0;
            for (final SignalPlan p : sorted.values()) {
                if (p.getStartTime() <= dayTime && dayTime < p.getEndTime()) {
                    chosen = p;
                    break;
                }
            }
            if (chosen == null) {
                chosen = sorted.firstEntry().getValue();
            }
        }
        if (!(chosen instanceof DatabasedSignalPlan)) {
            throw new IllegalStateException(
                    "signal system " + this.system.getId() + ": plan "
                    + chosen.getId() + " is a " + chosen.getClass().getName()
                    + ", not the contrib's DatabasedSignalPlan; " + IDENTIFIER
                    + " reads the plan's settings data and cannot wrap it");
        }
        this.activePlan = (DatabasedSignalPlan) chosen;
        final Integer cycleTime = this.activePlan.getCycleTime();
        if (cycleTime == null || cycleTime <= 0) {
            throw new IllegalStateException(
                    "signal system " + this.system.getId() + ": plan "
                    + chosen.getId() + " declares no positive cycle time");
        }
        this.cycle = cycleTime;
        final Integer off0 = this.activePlan.getOffset();
        this.offset = off0 == null ? 0 : off0;
        this.planSeconds.clear();
        for (final Map.Entry<Id<SignalGroup>, SignalGroupSettingsData> e
                : this.activePlan.getPlanData()
                        .getSignalGroupSettingsDataByGroupId().entrySet()) {
            final int onset = e.getValue().getOnset();
            final int drop = e.getValue().getDropping();
            if (onset < 0 || onset >= this.cycle
                    || drop < 0 || drop > this.cycle) {
                throw new IllegalStateException(
                        "signal system " + this.system.getId() + " group "
                        + e.getKey() + ": onset " + onset + " / dropping "
                        + drop + " outside cycle [0, " + this.cycle + "]");
            }
            // a dropping written as == cycle means "the cycle's last second"
            this.planSeconds.put(e.getKey(), new int[] {
                    onset, Math.min(drop, this.cycle - 1)});
        }
    }

    /** Shortest and longest plan greens: the recall floor and the payer. */
    private void computeGreenStatistics() {
        this.minGreenFloorS = Integer.MAX_VALUE;
        this.longestCompetingGreen = null;
        int longest = -1;
        for (final Map.Entry<Id<SignalGroup>, int[]> e
                : this.planSeconds.entrySet()) {
            final int green = greenLength(e.getValue());
            this.minGreenFloorS = Math.min(this.minGreenFloorS, green);
            if (!e.getKey().equals(this.tramGroupId) && green > longest) {
                longest = green;
                this.longestCompetingGreen = e.getKey();
            }
        }
        if (this.minGreenFloorS == Integer.MAX_VALUE) {
            this.minGreenFloorS = 0;
        }
    }

    private int greenLength(final int[] onsetDrop) {
        final int len = Math.floorMod(onsetDrop[1] - onsetDrop[0], this.cycle);
        return len == 0 ? this.cycle : len;
    }

    private static boolean inGreen(final int pos, final int onset,
                                   final int drop) {
        if (onset < drop) {
            return pos >= onset && pos < drop;
        }
        // wrapped green: green across the cycle boundary
        return pos >= onset || pos < drop;
    }

    // ------------------------------------------------------------------
    // detection
    // ------------------------------------------------------------------

    /**
     * The shared detection service: one per {@link Factory}, registered on
     * the run's {@link EventsManager} once, feeding every controller the
     * factory creates.
     *
     * <p>Concurrency: with a parallel events manager, handlers run off the
     * QSim thread but are synchronised at each sim step boundary, so a
     * detection raised in step {@code t} is visible to {@code updateState}
     * at {@code t + 1} at the latest; the concurrent maps below make the
     * hand-off safe without ordering assumptions beyond that. All
     * DECISIONS-relevant determinism lives in the event stream itself.
     */
    static final class TramDetection implements LinkEnterEventHandler,
            TransitDriverStartsEventHandler,
            VehicleArrivesAtFacilityEventHandler,
            VehicleDepartsAtFacilityEventHandler {

        static final class Pending {
            final double timeS;
            final double delayS;

            Pending(final double timeS, final double delayS) {
                this.timeS = timeS;
                this.delayS = delayS;
            }
        }

        private final Set<Id<Vehicle>> transitVehicles =
                ConcurrentHashMap.newKeySet();
        private final Map<Id<Vehicle>, Double> lastKnownDelayS =
                new ConcurrentHashMap<>();
        /** approach link -> systems watching it (rebuilt each mobsim). */
        private final Map<Id<Link>, Set<Id<SignalSystem>>> watchers =
                new ConcurrentHashMap<>();
        private final Map<Id<SignalSystem>, Set<Id<Link>>> linksOfSystem =
                new ConcurrentHashMap<>();
        private final Map<Id<SignalSystem>, Pending> pending =
                new ConcurrentHashMap<>();

        /** (Re-)register a system's tram approach links; replaces the old set. */
        void register(final Id<SignalSystem> system,
                      final Set<Id<Link>> approachLinks) {
            final Set<Id<Link>> previous = this.linksOfSystem.put(
                    system, new HashSet<>(approachLinks));
            if (previous != null) {
                for (final Id<Link> link : previous) {
                    final Set<Id<SignalSystem>> w = this.watchers.get(link);
                    if (w != null) {
                        w.remove(system);
                    }
                }
            }
            for (final Id<Link> link : approachLinks) {
                this.watchers.computeIfAbsent(link,
                        k -> ConcurrentHashMap.newKeySet()).add(system);
            }
        }

        /** Read the pending detection for one system without clearing it. */
        Pending peek(final Id<SignalSystem> system) {
            return this.pending.get(system);
        }

        /** Clear one system's pending detection (acted on, or stale). */
        void clear(final Id<SignalSystem> system) {
            this.pending.remove(system);
        }

        @Override
        public void handleEvent(final TransitDriverStartsEvent event) {
            this.transitVehicles.add(event.getVehicleId());
        }

        @Override
        public void handleEvent(final VehicleArrivesAtFacilityEvent event) {
            this.lastKnownDelayS.put(event.getVehicleId(), event.getDelay());
        }

        @Override
        public void handleEvent(final VehicleDepartsAtFacilityEvent event) {
            this.lastKnownDelayS.put(event.getVehicleId(), event.getDelay());
        }

        @Override
        public void handleEvent(final LinkEnterEvent event) {
            if (!this.transitVehicles.contains(event.getVehicleId())) {
                return; // not a transit vehicle: never a tram
            }
            final Set<Id<SignalSystem>> systems =
                    this.watchers.get(event.getLinkId());
            if (systems == null || systems.isEmpty()) {
                return;
            }
            final Double delay = this.lastKnownDelayS.get(event.getVehicleId());
            final Pending p = new Pending(event.getTime(),
                    delay == null ? 0.0 : delay);
            for (final Id<SignalSystem> system : systems) {
                this.pending.put(system, p);
            }
        }

        @Override
        public void reset(final int iteration) {
            this.transitVehicles.clear();
            this.lastKnownDelayS.clear();
            this.pending.clear();
            // registrations are rebuilt by each controller's
            // simulationInitialized, which runs after this reset
            this.watchers.clear();
            this.linksOfSystem.clear();
        }
    }

    // ------------------------------------------------------------------
    // factory
    // ------------------------------------------------------------------

    /**
     * Injectable factory, registered with the signals contrib under
     * {@link #IDENTIFIER} via
     * {@code Signals.Configurator#addSignalControllerFactory}. Guice builds
     * it inside the controler injector, so the injected {@link EventsManager}
     * is the run's own; the shared {@link TramDetection} is created and
     * registered here exactly once per factory instance.
     */
    public static final class Factory implements SignalControllerFactory {

        private final TramPriorityConfigGroup params;
        private final TramDetection detection;

        @Inject
        Factory(final Config config, final EventsManager events) {
            this.params = ConfigUtils.addOrGetModule(config,
                    TramPriorityConfigGroup.NAME, TramPriorityConfigGroup.class);
            if (this.params.getMode().isEmpty()) {
                throw new IllegalStateException(
                        "a signal system selects " + IDENTIFIER + " but the "
                        + "tramPriority config module was never populated - "
                        + "the entry point registers it and the run-input "
                        + "builder writes it; refusing to run on a regime "
                        + "nobody chose");
            }
            this.detection = new TramDetection();
            events.addHandler(this.detection);
        }

        @Override
        public SignalController createSignalSystemController(
                final SignalSystem signalSystem) {
            final TramPriorityController controller =
                    new TramPriorityController(this.params, this.detection);
            controller.setSignalSystem(signalSystem);
            return controller;
        }
    }
}
