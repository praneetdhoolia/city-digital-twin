package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `taxiFleet` config module: taxi as a FINITE fleet (DECISIONS.md 9.99,
 * issue #90).
 *
 * <p>Taxi was the only mode in this model constrained by nothing. Car is
 * limited by ownership, a licence and subtour chain consistency; `ride` by a
 * declared driver existing; bike by an availability attribute and an age gate;
 * pt by a timetable and a stop; truck by being its own subpopulation;
 * motorbike by a person-level locked carve. Taxi was limited by an age gate
 * and nothing else - every adult could take one on every trip, with no fleet,
 * no booking friction and no supply limit, at a flat declared wait.
 *
 * <p>Measured consequence (9.91, 9.94): taxi is seeded at exactly 0.0 because
 * the demand model generates none, then rises monotonically through
 * mode-choice innovation to 8.8% against a 0.99% target, and it reads 7.52%
 * even among agents holding BOTH a car and a licence. It was not winning
 * against car - car is chain-based, so a perturbed subtour cannot use it - it
 * was winning the trips where car was structurally unavailable, and winning
 * them because nothing said no.
 *
 * <p><b>What a fleet changes.</b> Waiting stops being the declared constant
 * {@code C.taxi.wait_min} and starts EMERGING from supply: a request is served
 * only if a vehicle is free, and a request nobody can serve is refused. That
 * is the standing directive's physical-simulation requirement applied to this
 * mode, and it is the same shape the project already uses for `ride` - the
 * constraint is the price, and no parameter is invented to hold the share
 * down.
 *
 * <p>Every value here is written from the registry by the run-input builder.
 * Following the lesson {@link TramPriorityConfigGroup} records: no parameter
 * keeps a usable Java default, because a default that EQUALS its registry
 * value is right by accident and stops being right the moment anyone sweeps
 * the field.
 */
public final class TaxiFleetConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "taxiFleet";

    /** Sentinel meaning "the config never set it", NOT a usable value. */
    private static final double UNSET = -1.0;

    /** No fleet: every request is served, the pre-9.99 behaviour. */
    public static final String REPRESENTATION_ABSENT = "absent";
    /** A finite fleet: a request unserved by any vehicle is refused. */
    public static final String REPRESENTATION_FLEET = "finite_fleet";

    private String representation = "";
    private double fleetSize = UNSET;
    private double maxWaitMinutes = UNSET;
    private double deadheadMinutes = UNSET;
    private boolean remodeRefused = false;

    public TaxiFleetConfigGroup() {
        super(NAME);
    }

    /**
     * Whether taxi supply is modelled at all.
     *
     * <p>{@code absent} serves every request and reproduces every arm before
     * 9.99 exactly, which is what makes the fleet's effect measurable rather
     * than asserted.
     */
    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    public boolean isFleet() {
        return REPRESENTATION_FLEET.equals(this.representation);
    }

    /**
     * Vehicles in the fleet AT FULL SCALE, before the sample fraction.
     *
     * <p>Scaled by {@code qsim.flowCapacityFactor} inside the engine for the
     * same reason the SCATS saturation flow is (9.88): a sampled run is not a
     * small city, it is a city whose capacities were scaled, and a full-scale
     * fleet serving a tenth of the demand would not constrain anything.
     */
    @StringGetter("fleetSize")
    public double getFleetSize() {
        return this.fleetSize;
    }

    @StringSetter("fleetSize")
    public void setFleetSize(final double value) {
        this.fleetSize = value;
    }

    /**
     * The longest a passenger will wait for a vehicle before giving up.
     *
     * <p>A request no vehicle can reach inside this is REFUSED, and the refusal
     * is what makes the fleet bind. Without it a finite fleet would only delay
     * every request rather than turning any of them away.
     */
    @StringGetter("maxWaitMinutes")
    public double getMaxWaitMinutes() {
        return this.maxWaitMinutes;
    }

    @StringSetter("maxWaitMinutes")
    public void setMaxWaitMinutes(final double value) {
        this.maxWaitMinutes = value;
    }

    /**
     * Empty running between one fare's end and the next fare's start.
     *
     * <p>A taxi is not free the instant it sets a passenger down: it has to
     * reach the next one. This is the part of a vehicle's day that carries no
     * passenger, and it is what makes a fleet of N serve fewer than the
     * arithmetic of trip durations alone suggests. It is declared and swept
     * rather than modelled as routed empty legs, and that simplification is
     * stated: the deadhead does NOT load the road network here.
     */
    @StringGetter("deadheadMinutes")
    public double getDeadheadMinutes() {
        return this.deadheadMinutes;
    }

    @StringSetter("deadheadMinutes")
    public void setDeadheadMinutes(final double value) {
        this.deadheadMinutes = value;
    }

    /**
     * Whether a refused taxi request walks this iteration.
     *
     * <p>Exactly the `ride` treatment (9.55, 9.81): a trip no vehicle can
     * serve is not a taxi trip, it WALKS, and the long forced walk scores
     * badly so co-evolution reassigns the tour. The mode is given back at
     * AfterMobsim so the plan keeps taxi as an alternative - a refusal must
     * not be a one-way ratchet, which is the defect 9.81 records.
     */
    @StringGetter("remodeRefused")
    public boolean isRemodeRefused() {
        return this.remodeRefused;
    }

    @StringSetter("remodeRefused")
    public void setRemodeRefused(final boolean value) {
        this.remodeRefused = value;
    }

    @Override
    protected void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (this.representation.isEmpty()) {
            throw new IllegalStateException(
                    "taxiFleet.representation was never set: the run-input "
                    + "builder writes it from A.taxi.fleet_representation. "
                    + "Refusing to run on a regime nobody chose.");
        }
        if (!REPRESENTATION_ABSENT.equals(this.representation) && !isFleet()) {
            throw new IllegalStateException(
                    "taxiFleet.representation must be '"
                    + REPRESENTATION_ABSENT + "' or '" + REPRESENTATION_FLEET
                    + "', not '" + this.representation + "'");
        }
        if (!isFleet()) {
            return;                      // nothing below is read without a fleet
        }
        require("fleetSize", this.fleetSize);
        require("maxWaitMinutes", this.maxWaitMinutes);
        if (this.deadheadMinutes < 0) {
            throw new IllegalStateException(
                    "taxiFleet.deadheadMinutes must be set and non-negative; "
                    + "the run-input builder writes it from the registry");
        }
    }

    private static void require(final String name, final double v) {
        if (v <= 0) {
            throw new IllegalStateException(
                    "taxiFleet." + name + " was never set (or is not "
                    + "positive): the run-input builder writes it from the "
                    + "registry, and this class keeps no usable default on "
                    + "purpose - a default that happens to equal the declared "
                    + "value is right by accident and stops being right the "
                    + "moment the field is swept");
        }
    }
}
