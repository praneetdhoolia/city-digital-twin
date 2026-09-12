package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;
import org.matsim.core.config.ReflectiveConfigGroup.Parameter;

/**
 * The `parking` config module: what a car is charged to stand still.
 *
 * <p>Every value here is written by {@code build_matsim_run_inputs.py} from
 * {@code config/registry/<city>/A_supply.json}. None of them may be typed into
 * a script, and none is a place: the price of a <em>link</em> is looked up in
 * {@link #getPriceFile()}, which the build produces by joining the run network
 * to the city's own job-density surface. Java does no spatial work at all.
 *
 * <p>Declaring this as a real {@link ReflectiveConfigGroup} rather than letting
 * MATSim absorb an unknown module has two consequences worth having: an
 * unrecognised parameter fails the run instead of being silently ignored, and
 * the module is written into the output config dump, so a result carries the
 * parking regime that produced it.
 *
 * <p>See DECISIONS.md 9.31 and issue #33.
 */
public final class ParkingConfigGroup extends ReflectiveConfigGroup {

    public static final String GROUP_NAME = "parking";

    // Every default here is NEUTRAL - it means "charge nothing" - except one,
    // which used to be `chargedModes = "car"`: exactly what
    // A.parking.charged_modes declares. A default equal to its registry value
    // is right by accident, and it would keep charging cars if the binding that
    // writes the parameter were ever lost. Empty now, and checkConsistency
    // refuses a priced run that never named a mode.
    @Parameter("priceFile")
    public String priceFile = "";
    @Parameter("maxStayMinutes")
    public double maxStayMinutes = 0.0;
    @Parameter("chargedStartHour")
    public double chargedStartHour = 0.0;
    @Parameter("chargedEndHour")
    public double chargedEndHour = 0.0;
    @Parameter("chargedModes")
    public String chargedModes = "";
    @Parameter("exemptActivityTypes")
    public String exemptActivityTypes = "";
    @Parameter("searchPenaltyUtilsPerMin")
    public double searchPenaltyUtilsPerMin = 0.0;

    public ParkingConfigGroup() {
        super(GROUP_NAME);
    }

    /**
     * Tab-separated {@code link_id\tprice_aud_hr}, one row per PRICED link.
     * A link absent from the file is free, so the file holds roughly 22k rows
     * of the run network's ~144k car links rather than all of them. Empty
     * disables parking charging entirely.
     */
    public String getPriceFile() {
        return this.priceFile;
    }

    /**
     * The charge cap, in minutes: a spell is charged for
     * {@code min(duration, maxStayMinutes)}. This UNDER-charges a long stay,
     * which is a declared modelling choice - representing over-stay properly
     * needs an infringement rate nobody has measured here.
     */
    public double getMaxStayMinutes() {
        return this.maxStayMinutes;
    }

    /** Start of the charged window, in hours after midnight. */
    public double getChargedStartHour() {
        return this.chargedStartHour;
    }

    /**
     * End of the charged window, in hours after midnight. An end at or before
     * the start means nothing is charged on this day type - which is how a
     * free Sunday is expressed, rather than by a separate flag.
     */
    public double getChargedEndHour() {
        return this.chargedEndHour;
    }

    /**
     * Comma-separated leg modes that occupy a parking space. `car` only: a
     * passenger does not pay to park the vehicle they are riding in, and
     * charging `ride` as well would bill the same vehicle twice.
     */
    public String getChargedModes() {
        return this.chargedModes;
    }

    /**
     * Comma-separated activity types at which a parked car is not charged.
     * `home` by default - see DECISIONS.md 9.31 for why charging it would be a
     * standing levy on living in a dense zone rather than a price on travel.
     */
    public String getExemptActivityTypes() {
        return this.exemptActivityTypes;
    }

    /**
     * Utils per minute of parking search/access time (DECISIONS.md 9.138):
     * the trip-weighted VOT x marginalUtilityOfMoney identity the transfer
     * penalty already prices minutes with, derived by the emitter. The
     * MINUTES are data — the third column of {@link #getPriceFile()}, the
     * declared A.parking.search_min_max scaled by each zone's 9.31
     * density_weight. The neutral default 0.0 charges nothing, which is the
     * pre-9.138 model and the A.parking.search_time_representation=absent
     * state.
     */
    public double getSearchPenaltyUtilsPerMin() {
        return this.searchPenaltyUtilsPerMin;
    }

    /**
     * A priced run must say WHICH MODES it charges.
     *
     * <p>The config is BUILT from the registry, so an empty mode list beside a
     * price file means the binding was lost - and a run that silently charges
     * nobody looks exactly like a correct run, which is how parking price sat
     * declared and unread from P1 until issue #33.
     */
    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!this.priceFile.isEmpty() && this.chargedModes.trim().isEmpty()) {
            throw new IllegalStateException(
                    "parking.priceFile is set but parking.chargedModes is empty, "
                    + "so nothing would be charged. chargedModes is declared as "
                    + "A.parking.charged_modes and written into the config by "
                    + "src/registry/param_config.py.");
        }
    }

}
