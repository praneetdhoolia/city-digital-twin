package citysim;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.events.LinkEnterEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.population.Person;
import org.matsim.contrib.signals.controller.SignalController;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalControlDataImpl;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalGroupSettingsData;
import org.matsim.contrib.signals.data.signalcontrol.v20.SignalPlanData;
import org.matsim.contrib.signals.model.DatabasedSignalPlan;
import org.matsim.contrib.signals.model.Signal;
import org.matsim.contrib.signals.model.SignalGroup;
import org.matsim.contrib.signals.model.SignalPlan;
import org.matsim.contrib.signals.model.SignalSystem;
import org.matsim.contrib.signals.model.SignalSystemsManager;
import org.matsim.core.mobsim.qsim.interfaces.SignalGroupState;
import org.matsim.core.mobsim.qsim.interfaces.SignalizeableItem;
import org.matsim.core.network.NetworkUtils;
import org.matsim.lanes.Lane;
import org.matsim.pt.transitSchedule.api.Departure;
import org.matsim.pt.transitSchedule.api.TransitLine;
import org.matsim.pt.transitSchedule.api.TransitRoute;
import org.matsim.vehicles.Vehicle;

/**
 * The gate on {@link ScatsSignalController}'s transit priority (issue #125):
 * on a THREE-stage plan, an extension must move the tram stage's dropping
 * later, a recall must move its onset earlier, and a tram stage that is last
 * in its cycle must be refused rather than charged for a deformation that
 * never reaches the stop line.
 *
 * <p>The defect this guards: the controller took the extension's seconds from
 * whichever stage had the most spare green, then re-laid every stage from
 * cursor 0. With the donor BEFORE the tram stage, every later onset shifted
 * earlier by the grant and the tram's drop was unchanged - nothing extended,
 * the budget spent, the detection cleared. The corridor's two-stage plans hid
 * it because their tram stage is first and the only donor follows it.
 *
 * <p>No mobsim: the controller is driven directly, second by second, on a
 * stub signal system that records every onset and dropping it is asked to
 * schedule, with the detection injected through the same event handlers the
 * run uses. Plan: cycle 90 s, three stages of 28 s green with 2 s clearances
 * (0-28, 30-58, 60-88), fixed-time regime so SCATS does not re-time between
 * cycles, window 10 s, budget 20% (18 s), minimum green 5 s.
 * <ul>
 * <li>extension, tram stage in the middle, detected at t=50: the tram drops
 *     at 68 (not 58), the third stage runs 70-88, the next cycle starts at
 *     90 - the cycle is conserved;</li>
 * <li>extension, tram stage LAST, detected at t=80: refused - the tram drops
 *     at 88, the refusal is counted, the next cycle starts at 90;</li>
 * <li>recall, tram stage in the middle, detected at t=10 while the first
 *     stage runs: the first stage drops at 18, the tram's onset is 20 (not
 *     30) and its drop stays at 58.</li>
 * </ul>
 * One JSON line on stdout; exit 0 only if every check holds.
 */
public final class ScatsPriorityProbe {

    private static final int CYCLE = 90;
    private static final int[][] WINDOWS = {{0, 28}, {30, 58}, {60, 88}};
    private static final String TRAM = "tram";

    private ScatsPriorityProbe() {
    }

    public static void main(final String[] args) {
        final StringBuilder json = new StringBuilder("{");
        boolean ok = true;

        // --- extension, tram stage in the middle ------------------------
        Run r = run(TramPriorityConfigGroup.MODE_GREEN_EXTENSION, 1, 50);
        final boolean extDrop = r.first(r.drops, TRAM) == 68;
        final boolean extNextOnset = r.first(r.onsets, "s2") == 70;
        final boolean extCycleKept = r.first(r.drops, "s2") == 88
                && r.contains(r.onsets, "s0", 90);
        final boolean extCharged = r.refused == 0;
        ok &= extDrop && extNextOnset && extCycleKept && extCharged;
        json.append("\"extension_middle\":{\"tram_drop_s\":")
            .append(r.first(r.drops, TRAM))
            .append(",\"next_onset_s\":").append(r.first(r.onsets, "s2"))
            .append(",\"next_drop_s\":").append(r.first(r.drops, "s2"))
            .append(",\"cycle2_onset_s\":").append(r.first2(r.onsets, "s0"))
            .append(",\"refused\":").append(r.refused).append('}');

        // --- extension, tram stage last: refused honestly ----------------
        r = run(TramPriorityConfigGroup.MODE_GREEN_EXTENSION, 2, 80);
        final boolean lastUnmoved = r.first(r.drops, TRAM) == 88;
        final boolean lastRefused = r.refused >= 1;
        final boolean lastCycleKept = r.contains(r.onsets, "s0", 90);
        ok &= lastUnmoved && lastRefused && lastCycleKept;
        json.append(",\"extension_last\":{\"tram_drop_s\":")
            .append(r.first(r.drops, TRAM))
            .append(",\"cycle2_onset_s\":").append(r.first2(r.onsets, "s0"))
            .append(",\"refused\":").append(r.refused).append('}');

        // --- recall, tram stage in the middle ----------------------------
        r = run(TramPriorityConfigGroup.MODE_EXTENSION_RECALL, 1, 10);
        final boolean recallOnset = r.first(r.onsets, TRAM) == 20;
        final boolean recallDonor = r.first(r.drops, "s0") == 18;
        final boolean recallDrop = r.first(r.drops, TRAM) == 58;
        ok &= recallOnset && recallDonor && recallDrop;
        json.append(",\"recall_middle\":{\"tram_onset_s\":")
            .append(r.first(r.onsets, TRAM))
            .append(",\"running_drop_s\":").append(r.first(r.drops, "s0"))
            .append(",\"tram_drop_s\":").append(r.first(r.drops, TRAM))
            .append(",\"refused\":").append(r.refused).append('}');

        json.append(",\"ok\":").append(ok).append('}');
        System.out.println(json);
        System.exit(ok ? 0 : 1);
    }

    /** One controller driven over two cycles with one detection. */
    private static Run run(final String mode, final int tramStage,
                           final int detectAt) {
        final ScatsConfigGroup params = new ScatsConfigGroup();
        params.setRegime(ScatsConfigGroup.REGIME_FIXED_TIME);
        params.setTargetDegreeSaturation(0.9);
        params.setDsDeadband(0.05);
        params.setCycleStepS(6);
        params.setMinCycleS(60);
        params.setMaxCycleS(150);
        params.setDsSmoothing(0.5);
        params.setSaturationFlowVehHLane(1900);
        params.setMinGreenS(5);
        final TramPriorityConfigGroup priority = new TramPriorityConfigGroup();
        priority.setMode(mode);
        priority.setPriorityGroupId(TRAM);
        priority.setExtensionWindowS(10);
        priority.setDetectionDistanceM(100);
        priority.setPriorityBudgetShare(0.2);
        priority.setCompensationEnabled(false);
        priority.setLatenessThresholdS(0);

        final TramPriorityController.TramDetection detection =
                new TramPriorityController.TramDetection();
        final ScatsSignalController controller = new ScatsSignalController(
                params, priority, detection,
                new ScatsSignalController.Discharge(),
                NetworkUtils.createNetwork(), 1900.0);

        final StubSystem system = new StubSystem(
                Id.create("sys1", SignalSystem.class));
        final SignalPlanData planData = new SignalControlDataImpl().getFactory()
                .createSignalPlanData(Id.create("p1", SignalPlan.class));
        planData.setCycleTime(CYCLE);
        planData.setOffset(0);
        planData.setStartTime(0.0);
        planData.setEndTime(0.0);
        for (int i = 0; i < WINDOWS.length; i++) {
            final String name = i == tramStage ? TRAM : "s" + i;
            final Id<SignalGroup> gid = Id.create(name, SignalGroup.class);
            final StubGroup group = new StubGroup(gid);
            group.signals.put(Id.create("sig" + i, Signal.class),
                    new StubSignal(Id.create("sig" + i, Signal.class),
                                   Id.createLinkId("l" + i)));
            system.groups.put(gid, group);
            final SignalGroupSettingsData s = new SignalControlDataImpl()
                    .getFactory().createSignalGroupSettingsData(gid);
            s.setOnset(WINDOWS[i][0]);
            s.setDropping(WINDOWS[i][1]);
            planData.addSignalGroupSettings(s);
        }
        controller.setSignalSystem(system);
        controller.addPlan(new DatabasedSignalPlan(planData));
        controller.simulationInitialized(0.0);

        final Id<Vehicle> tram = Id.create("tram1", Vehicle.class);
        for (int t = 1; t < 2 * CYCLE; t++) {
            if (t == detectAt) {
                detection.handleEvent(new TransitDriverStartsEvent(
                        t, Id.create("drv", Person.class), tram,
                        Id.create("line", TransitLine.class),
                        Id.create("route", TransitRoute.class),
                        Id.create("dep", Departure.class)));
                detection.handleEvent(new LinkEnterEvent(
                        t, tram, Id.createLinkId("l" + tramStage)));
            }
            controller.updateState(t);
        }
        final Run out = new Run();
        out.onsets = system.onsets;
        out.drops = system.drops;
        out.refused = controller.priorityRefusedNoDonor();
        return out;
    }

    private static final class Run {
        Map<String, List<Integer>> onsets;
        Map<String, List<Integer>> drops;
        int refused;

        int first(final Map<String, List<Integer>> m, final String g) {
            final List<Integer> l = m.get(g);
            return l == null || l.isEmpty() ? -1 : l.get(0);
        }

        int first2(final Map<String, List<Integer>> m, final String g) {
            final List<Integer> l = m.get(g);
            return l == null || l.size() < 2 ? -1 : l.get(1);
        }

        boolean contains(final Map<String, List<Integer>> m, final String g,
                         final int t) {
            final List<Integer> l = m.get(g);
            return l != null && l.contains(t);
        }
    }

    // ------------------------------------------------------------------
    // a signal system that only records what it is asked to schedule
    // ------------------------------------------------------------------

    private static final class StubSystem implements SignalSystem {
        private final Id<SignalSystem> id;
        final Map<Id<SignalGroup>, SignalGroup> groups = new LinkedHashMap<>();
        final Map<String, List<Integer>> onsets = new LinkedHashMap<>();
        final Map<String, List<Integer>> drops = new LinkedHashMap<>();

        StubSystem(final Id<SignalSystem> id) {
            this.id = id;
        }

        @Override
        public Id<SignalSystem> getId() {
            return this.id;
        }

        @Override
        public void scheduleOnset(final double t, final Id<SignalGroup> g) {
            this.onsets.computeIfAbsent(g.toString(), k -> new ArrayList<>())
                    .add((int) Math.round(t));
        }

        @Override
        public void scheduleDropping(final double t, final Id<SignalGroup> g) {
            // simulationInitialized sets every non-green group's PRESENT
            // colour with a dropping at t=0; that is the initial state, not
            // a dropping the plan scheduled, and is not recorded
            if (t <= 0) {
                return;
            }
            this.drops.computeIfAbsent(g.toString(), k -> new ArrayList<>())
                    .add((int) Math.round(t));
        }

        @Override
        public Map<Id<SignalGroup>, SignalGroup> getSignalGroups() {
            return this.groups;
        }

        @Override
        public Map<Id<Signal>, Signal> getSignals() {
            final Map<Id<Signal>, Signal> all = new LinkedHashMap<>();
            for (final SignalGroup g : this.groups.values()) {
                all.putAll(g.getSignals());
            }
            return all;
        }

        @Override
        public void setSignalSystemsManager(final SignalSystemsManager m) {
        }

        @Override
        public void updateState(final double t) {
        }

        @Override
        public void setSignalSystemController(final SignalController c) {
        }

        @Override
        public void addSignal(final Signal s) {
        }

        @Override
        public void addSignalGroup(final SignalGroup g) {
            this.groups.put(g.getId(), g);
        }

        @Override
        public SignalController getSignalController() {
            return null;
        }

        @Override
        public void simulationInitialized(final double t) {
        }

        @Override
        public void switchOff(final double t) {
        }

        @Override
        public void startPlan(final double t) {
        }
    }

    private static final class StubGroup implements SignalGroup {
        private final Id<SignalGroup> id;
        final Map<Id<Signal>, Signal> signals = new LinkedHashMap<>();
        private SignalGroupState state;

        StubGroup(final Id<SignalGroup> id) {
            this.id = id;
        }

        @Override
        public Id<SignalGroup> getId() {
            return this.id;
        }

        @Override
        public void setState(final SignalGroupState s) {
            this.state = s;
        }

        @Override
        public SignalGroupState getState() {
            return this.state;
        }

        @Override
        public void addSignal(final Signal s) {
            this.signals.put(s.getId(), s);
        }

        @Override
        public Map<Id<Signal>, Signal> getSignals() {
            return this.signals;
        }
    }

    private static final class StubSignal implements Signal {
        private final Id<Signal> id;
        private final Id<Link> link;

        StubSignal(final Id<Signal> id, final Id<Link> link) {
            this.id = id;
            this.link = link;
        }

        @Override
        public Id<Signal> getId() {
            return this.id;
        }

        @Override
        public Id<Link> getLinkId() {
            return this.link;
        }

        @Override
        public Set<Id<Lane>> getLaneIds() {
            return Collections.emptySet();
        }

        @Override
        public void addSignalizeableItem(final SignalizeableItem item) {
        }

        @Override
        public Collection<SignalizeableItem> getSignalizeableItems() {
            return Collections.emptyList();
        }

        @Override
        public void setState(final SignalGroupState s) {
        }
    }
}
