package citysim;

import com.google.inject.Inject;
import com.google.inject.Singleton;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.population.Leg;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.core.config.Config;
import org.matsim.core.population.PopulationUtils;
import org.matsim.core.router.AnalysisMainModeIdentifier;
import org.matsim.core.router.DefaultAnalysisMainModeIdentifier;

/**
 * Main-mode identification that survives score-distinct PT submodes
 * (issue #49 Tier C, DECISIONS.md 9.78).
 *
 * <p>Under {@code RUN.routing.pt_submode_scoring = per_submode} the emitted
 * config maps each scheduled route {@code transportMode} to a passenger mode
 * of the same name (SwissRailRaptor's {@code useModeMappingForPassengers}),
 * so a PT passenger's legs carry {@code bus}/{@code tram}/{@code rail}/
 * {@code ferry} rather than {@code pt}. The stock
 * {@link DefaultAnalysisMainModeIdentifier} — which writes {@code main_mode}
 * into {@code output_trips.csv} and feeds {@code modestats.csv} — does not
 * know those modes, and its bytecode (read from the pinned jar, not from
 * memory) does two wrong things with an unknown leg mode: a trip whose only
 * vehicular leg is one unknown submode is labelled with that submode alone
 * (a bus-and-walk trip becomes {@code bus}, breaking the linked-trip
 * vocabulary the HTS comparison is defined over), and a trip that boards TWO
 * distinct submodes — every bus+rail interchange, rows Tier R already
 * measured — throws {@code IllegalStateException} and kills the run at the
 * trips write.
 *
 * <p>This identifier folds every leg whose mode is in the config's declared
 * {@code transit.transitModes} back to {@link TransportMode#pt} and then
 * delegates to the stock identifier unchanged. The consequences, in order of
 * importance:
 *
 * <ul>
 * <li>{@code main_mode} keeps the SAME vocabulary on both sides of the
 *     switch — a linked PT trip is {@code pt}, exactly what the published
 *     HTS linked mode share measures (DECISIONS.md 12.1) and what
 *     {@code fit.py} compares. No comparability break in the trips table
 *     itself; the submode split is read from each boarded route's own
 *     scheduled transportMode (Tier R, {@code extract_metrics.pt_submode_split}),
 *     which never depended on the leg-mode label.</li>
 * <li>Under {@code aggregate} the fold is an identity map ({@code pt} is in
 *     {@code transitModes} and is skipped below), so behaviour is
 *     byte-identical to the stock identifier — this binding is safe to
 *     install unconditionally.</li>
 * </ul>
 *
 * <p>The transit-mode set is read from the run's own config, never typed:
 * the declared vocabulary lives in {@code RUN.transit.transit_modes} and
 * reaches this class through {@code transit.transitModes}.
 */
@Singleton
public final class PtSubmodeMainModeIdentifier implements AnalysisMainModeIdentifier {

    private final DefaultAnalysisMainModeIdentifier delegate =
            new DefaultAnalysisMainModeIdentifier();

    /** The declared transit passenger modes, {@code pt} included. */
    private final Set<String> transitModes;

    @Inject
    public PtSubmodeMainModeIdentifier(final Config config) {
        this.transitModes = new HashSet<>(config.transit().getTransitModes());
    }

    @Override
    public String identifyMainMode(final List<? extends PlanElement> tripElements) {
        final List<PlanElement> folded = new ArrayList<>(tripElements.size());
        for (final PlanElement element : tripElements) {
            if (element instanceof Leg
                    && transitModes.contains(((Leg) element).getMode())
                    && !TransportMode.pt.equals(((Leg) element).getMode())) {
                // The delegate only reads getMode(), so a bare leg carrying
                // the umbrella mode is a faithful stand-in for the mapped one.
                folded.add(PopulationUtils.createLeg(TransportMode.pt));
            } else {
                folded.add(element);
            }
        }
        return delegate.identifyMainMode(folded);
    }
}
