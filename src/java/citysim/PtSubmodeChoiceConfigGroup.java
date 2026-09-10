package citysim;

import java.util.LinkedHashSet;
import java.util.Set;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The {@code ptSubmodeChoice} module: whether bus, rail, tram and ferry are
 * ALTERNATIVES A PLAN CAN HOLD, or one {@code pt} alternative whose submode a
 * router picks.
 *
 * <p><b>The ceiling this exists to lift.</b> {@code RUN.mode_choice.modes}
 * offers {@code pt} as ONE alternative. Which submode a chosen pt trip uses is
 * decided downstream by SwissRailRaptor, and a whole-file pass over the F31
 * arm's plan memory (154,347 persons) found only <b>974 — 0.63 % of the
 * population</b> — holding plans that differ in which pt submode they use
 * (DECISIONS.md 9.160). A scoring constant reallocates between plans an agent
 * already holds, so under the aggregate representation
 * {@code C.asc.bus} and {@code C.asc.light_rail} are plan-choice levers (pt
 * against car) and never submode levers, for 99.37 % of the population. That
 * is the structural half of light rail at &minus;57.3 % against heavy rail at
 * +225.0 %: two halves of one split, decided in a layer whose only control
 * until PR #173 was the router's own travel time.
 *
 * <p><b>What {@code alternatives} installs.</b> One
 * {@link ch.sbb.matsim.routing.pt.raptor.SwissRailRaptor} per submode, built
 * over a TransitSchedule filtered to that submode's own routes, bound as the
 * routing module for a plan-level mode of the same name. {@code bus} then
 * means "get there by bus", answered by a router that can see only buses, and
 * {@code SubtourModeChoice} can propose it against {@code rail} the way it
 * proposes {@code car} against {@code bike}. Nothing about the SCORING changes:
 * {@code RUN.routing.pt_submode_scoring = per_submode} already writes one
 * {@code scoring.modeParams} block per submode, and those same blocks price
 * the new alternatives.
 *
 * <p><b>What it costs, stated.</b> Each submode's raptor holds its own
 * {@code SwissRailRaptorData} — stops, route stops and precomputed transfers
 * for that submode's routes only. The four together are larger than the one
 * combined structure, because a stop served by two submodes is indexed in
 * both, and smaller than four copies of it, because each holds a fraction of
 * the routes. It is measured on the probe, not asserted here.
 *
 * <p><b>What it deliberately does NOT do.</b> It does not let one plan-level
 * trip combine two submodes. A bus-then-train journey is representable only
 * under the {@code pt} umbrella, and this gate REMOVES that umbrella from the
 * choice set when it is on ({@code RUN.mode_choice.modes} swaps {@code pt} for
 * the submodes). That is a real loss of representational power against a real
 * gain in controllability, it is the honest trade this gate makes, and it is
 * why the gate ships at {@code aggregate}: the arm that turns it on must read
 * multi-leg pt trips on both sides. It is declared as
 * {@code RUN.mode_choice.pt_submode_alternatives}.
 *
 * <p><b>The seeded plan.</b> {@code build_matsim_plans.py} seeds {@code pt}.
 * With {@code pt} out of the choice set a seeded {@code pt} subtour would be
 * an ABSORBING STATE — the exact failure recorded for {@code ride} in
 * {@code RUN.mode_choice.modes}, where omitting it froze ride at 0.18311 in
 * every iteration to five decimals. So under {@code alternatives} every
 * seeded {@code pt} leg is rewritten to {@link #getSeedSubmode()} once, at
 * startup, with a count in the log. The rewrite is a STARTING POINT, not a
 * commitment: SubtourModeChoice may move it to another submode from iteration
 * one.
 */
public final class PtSubmodeChoiceConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "ptSubmodeChoice";

    public static final String REPRESENTATION_AGGREGATE = "aggregate";
    public static final String REPRESENTATION_ALTERNATIVES = "alternatives";

    private String representation = REPRESENTATION_AGGREGATE;
    /**
     * NO DEFAULT ON PURPOSE. A literal here would shadow
     * {@code RUN.mode_choice.pt_submode_seed} - the same value decided in
     * two places, right only while nobody moves the declared one - and
     * {@code check_hardcoding.py} category 6 refuses exactly that. Empty is
     * legitimate under {@code aggregate}, where nothing reads it, and
     * refused under {@code alternatives} below.
     */
    private String seedSubmode = "";

    public PtSubmodeChoiceConfigGroup() {
        super(NAME);
    }

    public boolean isAlternatives() {
        return REPRESENTATION_ALTERNATIVES.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    @StringGetter("seedSubmode")
    public String getSeedSubmode() {
        return this.seedSubmode;
    }

    @StringSetter("seedSubmode")
    public void setSeedSubmode(final String value) {
        this.seedSubmode = value == null ? "" : value.trim();
    }

    /** The scheduled submodes, {@code pt} excluded — the alternatives. */
    static Set<String> submodes(final Config config) {
        final Set<String> modes =
                new LinkedHashSet<>(config.transit().getTransitModes());
        modes.remove(TransportMode.pt);
        return modes;
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!REPRESENTATION_AGGREGATE.equals(this.representation)
                && !REPRESENTATION_ALTERNATIVES.equals(this.representation)) {
            throw new IllegalStateException(
                    "ptSubmodeChoice.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_AGGREGATE + " or "
                    + REPRESENTATION_ALTERNATIVES + ". It is declared as "
                    + "RUN.mode_choice.pt_submode_alternatives.");
        }
        if (!isAlternatives()) {
            return;
        }
        final Set<String> submodes = submodes(config);
        if (submodes.isEmpty()) {
            throw new IllegalStateException(
                    "ptSubmodeChoice.representation is "
                    + REPRESENTATION_ALTERNATIVES + " but transit.transitModes "
                    + "carries only the umbrella mode " + TransportMode.pt
                    + ", so there are no alternatives to offer. It needs the "
                    + "per-submode routing vocabulary: "
                    + "RUN.routing.pt_submode_scoring = per_submode.");
        }
        if (this.seedSubmode.isEmpty()) {
            throw new IllegalStateException(
                    "ptSubmodeChoice.representation is "
                    + REPRESENTATION_ALTERNATIVES + " and no "
                    + "ptSubmodeChoice.seedSubmode was emitted. It is declared "
                    + "as RUN.mode_choice.pt_submode_seed and this class holds "
                    + "no default for it, because a default here would be the "
                    + "same value decided twice.");
        }
        if (!submodes.contains(this.seedSubmode)) {
            throw new IllegalStateException(
                    "ptSubmodeChoice.seedSubmode is '" + this.seedSubmode
                    + "', which is not one of the declared submodes "
                    + submodes + ". A seeded pt leg rewritten to a mode "
                    + "nothing routes would abort the agent at iteration 0.");
        }
    }

    /**
     * Swap the umbrella mode out of the plan-level choice set for the
     * submodes, and say so.
     *
     * <p>The choice set is DECLARED as {@code RUN.mode_choice.modes}, which
     * carries {@code pt}. It is not declared twice: the emitter writes one
     * value for {@code subtourModeChoice.modes} and a second writer of the
     * same parameter is refused outright by {@code param_config.put}. So the
     * swap happens here, once, as a derived transformation of the declared
     * vocabulary with the identity stated in the log - the same shape as every
     * other derived runtime value in this model. {@code aggregate} never calls
     * it and the declared value stands untouched.
     *
     * @return the modes actually offered, for the caller to log
     */
    static String[] applyChoiceSet(final Config config) {
        final Set<String> submodes = submodes(config);
        final String[] declared = config.subtourModeChoice().getModes();
        final java.util.List<String> out = new java.util.ArrayList<>();
        boolean hadUmbrella = false;
        for (final String mode : declared == null ? new String[0] : declared) {
            if (TransportMode.pt.equals(mode)) {
                hadUmbrella = true;
                continue;
            }
            out.add(mode);
        }
        if (!hadUmbrella) {
            throw new IllegalStateException(
                    "ptSubmodeChoice.representation is "
                    + REPRESENTATION_ALTERNATIVES + " but subtourModeChoice."
                    + "modes does not carry " + TransportMode.pt
                    + ", so there is nothing to replace and the declared "
                    + "choice set is not the one this gate was designed "
                    + "against. Declared: "
                    + java.util.Arrays.toString(declared));
        }
        for (final String submode : submodes) {
            if (!out.contains(submode)) {
                out.add(submode);
            }
        }
        final String[] modes = out.toArray(new String[0]);
        config.subtourModeChoice().setModes(modes);
        return modes;
    }
}
