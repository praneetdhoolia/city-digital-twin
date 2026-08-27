package org.matsim.core.mobsim.qsim.qnetsimengine;

import citysim.GradientConfigGroup;
import citysim.GradientLinkSpeed;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Node;
import org.matsim.contrib.signals.SignalSystemsConfigGroup;
import org.matsim.contrib.signals.data.SignalsData;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.mobsim.framework.MobsimTimer;
import org.matsim.core.mobsim.qsim.interfaces.AgentCounter;
import org.matsim.vis.snapshotwriters.SnapshotLinkWidthCalculator;

/**
 * {@code QSignalsNetworkFactory} with a gradient-aware link speed calculator
 * (DECISIONS.md 9.84, issue #21).
 *
 * <p><b>Why this class exists.</b> The signals contrib's
 * {@link QSignalsNetworkFactory} constructs its link-building delegate with
 * {@code new DefaultQNetworkFactory(...)} — bypassing Guice — so the core's
 * {@code Multibinder<LinkSpeedCalculator>} seam (which the non-signal stack
 * uses) never reaches a signals run: a calculator added there would be
 * silently dropped while every signal kept working, or the factory replaced
 * wholesale would keep every speed while every signal silently vanished.
 * Both halves must survive together, so this factory replicates the signals
 * factory's node logic VERBATIM from the pinned jar (signals turn acceptance
 * per the declared intersection logic) and swaps only the link delegate for a
 * public {@link ConfigurableQNetworkFactory} carrying
 * {@link GradientLinkSpeed.Mobsim} — whose behaviour for every non-walk,
 * non-bike vehicle is byte-identical to the default calculator.
 *
 * <p>It lives in this package because the node-side classes it must touch
 * ({@code QNodeImpl.Builder}, {@code SignalTurnAcceptanceLogic},
 * {@code UnprotectedLeftTurnAcceptanceLogic}) are package-private in the
 * pinned jars; the toolchain is sha256-pinned, so the port cannot drift
 * without a recorded toolchain change (a jar change is a model change,
 * CLAUDE.md).
 *
 * <p>Lanes are refused loudly: the lanes delegate path is not ported, and a
 * config that enables lanes with gradient link speed must say so rather than
 * silently lose one or the other.
 */
public final class GradientSignalsNetworkFactory implements QNetworkFactory {

    private final Scenario scenario;
    private final EventsManager events;
    private final ConfigurableQNetworkFactory delegate;
    private NetsimEngineContext context;
    private QNetsimEngineI.NetsimInternalInterface netsimEngine;

    public GradientSignalsNetworkFactory(final Scenario scenario,
                                         final EventsManager events,
                                         final GradientConfigGroup gradient) {
        this.scenario = scenario;
        this.events = events;
        if (scenario.getConfig().qsim().isUseLanes()) {
            throw new IllegalStateException(
                    "gradient.representation=link_speed is not implemented for "
                    + "qsim.useLanes=true (the lanes delegate is not ported); "
                    + "set A.gradient.representation=absent or disable lanes.");
        }
        this.delegate = new ConfigurableQNetworkFactory(events, scenario);
        this.delegate.setLinkSpeedCalculator(
                new GradientLinkSpeed.Mobsim(gradient));
    }

    @Override
    public void initializeFactory(
            final AgentCounter agentCounter, final MobsimTimer mobsimTimer,
            final QNetsimEngineI.NetsimInternalInterface netsimEngine1) {
        final SnapshotLinkWidthCalculator linkWidthCalculator =
                new SnapshotLinkWidthCalculator();
        linkWidthCalculator.setLinkWidthForVis(
                scenario.getConfig().qsim().getLinkWidthForVis());
        linkWidthCalculator.setLaneWidth(
                scenario.getNetwork().getEffectiveLaneWidth());
        final AbstractAgentSnapshotInfoBuilder snapshotBuilder =
                AbstractQNetsimEngine.createAgentSnapshotInfoBuilder(
                        scenario, linkWidthCalculator);
        this.netsimEngine = netsimEngine1;
        this.context = new NetsimEngineContext(
                events, scenario.getNetwork().getEffectiveCellSize(),
                agentCounter, snapshotBuilder, scenario.getConfig().qsim(),
                mobsimTimer, linkWidthCalculator);
        this.delegate.initializeFactory(agentCounter, mobsimTimer,
                                        netsimEngine1);
    }

    @Override
    public QNodeI createNetsimNode(final Node node) {
        final QNodeImpl.Builder builder = new QNodeImpl.Builder(
                netsimEngine, context, scenario.getConfig().qsim());
        final SignalSystemsConfigGroup signalsConfig =
                ConfigUtils.addOrGetModule(
                        scenario.getConfig(),
                        SignalSystemsConfigGroup.GROUP_NAME,
                        SignalSystemsConfigGroup.class);
        if (signalsConfig.getIntersectionLogic().equals(
                SignalSystemsConfigGroup.IntersectionLogic
                        .CONFLICTING_DIRECTIONS_AND_TURN_RESTRICTIONS)) {
            builder.setTurnAcceptanceLogic(new UnprotectedLeftTurnAcceptanceLogic(
                    ((SignalsData) scenario.getScenarioElement(
                            SignalsData.ELEMENT_NAME))
                            .getConflictingDirectionsData(),
                    scenario.getLanes()));
        } else {
            builder.setTurnAcceptanceLogic(new SignalTurnAcceptanceLogic());
        }
        return builder.build(node);
    }

    @Override
    public QLinkI createNetsimLink(final Link link, final QNodeI queueNode) {
        return this.delegate.createNetsimLink(link, queueNode);
    }
}
