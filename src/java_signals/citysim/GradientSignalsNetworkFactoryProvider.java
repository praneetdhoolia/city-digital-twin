package citysim;

import com.google.inject.Inject;
import com.google.inject.Provider;
import org.matsim.api.core.v01.Scenario;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.mobsim.qsim.qnetsimengine.GradientSignalsNetworkFactory;
import org.matsim.core.mobsim.qsim.qnetsimengine.QNetworkFactory;

/**
 * Builds the {@link GradientSignalsNetworkFactory} inside the QSim's own
 * injection scope (DECISIONS.md 9.84), so the scenario and events manager it
 * carries are the run's real ones rather than whatever the assembly held when
 * the module was installed.
 */
public final class GradientSignalsNetworkFactoryProvider
        implements Provider<QNetworkFactory> {

    @Inject
    private Scenario scenario;
    @Inject
    private EventsManager events;

    @Override
    public QNetworkFactory get() {
        final GradientConfigGroup gradient = (GradientConfigGroup)
                scenario.getConfig().getModules().get(GradientConfigGroup.NAME);
        if (gradient == null || !gradient.isLinkSpeed()) {
            throw new IllegalStateException(
                    "GradientSignalsNetworkFactoryProvider bound while "
                    + "gradient.representation is not link_speed - the "
                    + "binding in CitysimSignalsControler is gated on the "
                    + "same condition, so this is an assembly defect.");
        }
        return new GradientSignalsNetworkFactory(scenario, events, gradient);
    }
}
