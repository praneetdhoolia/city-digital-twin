package citysim;

import java.util.List;
import org.matsim.api.core.v01.Scenario;
import org.matsim.contrib.signals.SignalSystemsConfigGroup;
import org.matsim.contrib.signals.builder.Signals;
import org.matsim.contrib.signals.data.SignalsData;
import org.matsim.contrib.signals.data.SignalsDataLoader;
import org.matsim.core.controler.Controler;

/**
 * The signal-enabled MATSim entry point (issue #73): the citysim assembly,
 * unchanged, plus the signals contrib.
 *
 * <p>This class lives in {@code src/java_signals/} and compiles ONLY against
 * the resolved run stack in {@code .tools/run-stack/lib} — never against the
 * shaded pt2matsim jar, whose relocated classes must not share a classpath
 * with the contrib (DECISIONS.md 9.73). {@code src/java/} keeps compiling
 * clean without the contrib; the two class trees are built into separate
 * output directories by {@code src/setup/bootstrap_toolchain.py}.
 *
 * <p>Assembly order, and why it is this order:
 * <ol>
 * <li>{@link CitysimControler#assemble} loads the config with the three
 *     citysim groups PLUS {@code signalsystems} and {@code tramPriority}, and
 *     installs every citysim module and QSim component reordering exactly as
 *     a non-signal run gets them.</li>
 * <li>The signals data is loaded from the files the {@code signalsystems}
 *     module names and attached to the scenario under
 *     {@link SignalsData#ELEMENT_NAME} — before the Controler runs, because
 *     the contrib's builders read the scenario element at injector time.</li>
 * <li>{@code new Signals.Configurator(controler)} installs the contrib's
 *     controler module and its QSim module, and the {@link
 *     TramPriorityController.Factory} is registered under
 *     {@link TramPriorityController#IDENTIFIER} so the control data can name
 *     it per system; the stock fixed-time identifier keeps working for
 *     systems that want no priority.</li>
 * </ol>
 *
 * <p><b>The one known assembly risk</b>: the contrib's QSim module rebinds
 * {@code QNetworkFactory} to {@code QSignalsNetworkFactory} — a SINGLE Guice
 * binding, not a named QSim component — while {@code CitysimControler}
 * rebuilds the QSim component ORDER (netsim engine removed and re-added,
 * agent sources swapped). The two must compose: the factory binding has to
 * survive the component reordering, or every signal silently vanishes from
 * the physics while the run completes happily. That composition is exactly
 * what {@link SignalsAssemblyProbe} exists to prove, and no scenario touches
 * signals before it has passed.
 *
 * <p>Run: {@code java -cp <run-stack>;classes-signals
 * citysim.CitysimSignalsControler config.xml}
 */
public final class CitysimSignalsControler {

    private CitysimSignalsControler() {
    }

    public static void main(final String[] args) {
        if (args.length != 1) {
            System.err.println(
                    "usage: citysim.CitysimSignalsControler <config.xml>");
            System.exit(2);
        }
        final SignalSystemsConfigGroup signalsConfig =
                new SignalSystemsConfigGroup();
        // TramPriorityConfigGroup is registered by assemble() itself on EVERY
        // stack: the tramPriority module is emitted into every config (its
        // fields are registry-bound, so the reach probe must see them move),
        // and this MATSim REFUSES an unmaterialised module at the consistency
        // check - measured on the first detached smoke probe, which is why
        // the group lives in src/java/ rather than here.
        final Controler controler = CitysimControler.assemble(
                args[0], List.of(signalsConfig));

        // The contrib refuses fast capacity update at module-install time
        // ("Fast flow capacity update does not support signals"); failing
        // here, before the scenario loads, would hide WHICH file to fix -
        // so leave the config exactly as written and let the contrib's own
        // check speak. The run-input builder writes
        // qsim.usingFastCapacityUpdate=false into every signal config.

        // Signals data is a scenario ELEMENT, not a config module: the loader
        // reads the three files the signalsystems module names (system,
        // groups, control) and the builders find the result on the scenario.
        final Scenario scenario = controler.getScenario();
        scenario.addScenarioElement(SignalsData.ELEMENT_NAME,
                new SignalsDataLoader(scenario.getConfig()).loadSignalsData());

        final Signals.Configurator configurator =
                new Signals.Configurator(controler);
        configurator.addSignalControllerFactory(
                TramPriorityController.IDENTIFIER,
                TramPriorityController.Factory.class);
        // SCATS adaptive control (DECISIONS.md 9.88, #73). Registered
        // unconditionally: which identifier a system actually runs is decided
        // per signal system in the generated control file, so a fixed-time
        // scenario never constructs one of these and behaves exactly as
        // before.
        configurator.addSignalControllerFactory(
                ScatsSignalController.IDENTIFIER,
                ScatsSignalController.Factory.class);

        // Gradient in walk/bike link speed under signals (DECISIONS.md 9.84,
        // #21). The contrib's QSignalsNetworkFactory news its link delegate
        // past Guice, so the core Multibinder seam the base stack uses never
        // reaches a signals run. This overriding QSim module - installed
        // AFTER the configurator so it wins the QNetworkFactory binding -
        // swaps in GradientSignalsNetworkFactory: the signals node logic
        // ported verbatim, the link delegate carrying the gradient
        // calculator. The SignalsAssemblyProbe discipline applies: no
        // scenario touches this before a probe has measured signals alive
        // AND bike slowed on grade.
        installGradientIfDeclared(controler);

        controler.run();
    }

    /**
     * Bind the gradient-aware signals network factory when the config
     * declares {@code gradient.representation = link_speed}; a no-op
     * otherwise. Shared with {@link SignalsAssemblyProbe}, which proves the
     * composition — signals still gating, walk slowed on grade — before any
     * scenario runs it.
     */
    public static void installGradientIfDeclared(final Controler controler) {
        final GradientConfigGroup gradient = (GradientConfigGroup)
                controler.getConfig().getModules().get(GradientConfigGroup.NAME);
        if (gradient == null || !gradient.isLinkSpeed()) {
            return;
        }
        controler.addOverridingQSimModule(
                new org.matsim.core.mobsim.qsim.AbstractQSimModule() {
            @Override
            protected void configureQSim() {
                bind(org.matsim.core.mobsim.qsim.qnetsimengine
                        .QNetworkFactory.class)
                        .toProvider(GradientSignalsNetworkFactoryProvider
                                .class);
            }
        });
    }
}
