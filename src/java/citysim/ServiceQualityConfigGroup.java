package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The {@code serviceQuality} module: what a passenger pays for a service's
 * FREQUENCY and its VARIABILITY, neither of which this twin priced at all.
 *
 * <h2>Why these are not already in the model</h2>
 *
 * <p>The obvious objection is double counting. This twin simulates the real
 * timetable, so the wait a passenger experiences is already priced by
 * {@code C.time_weights.beta_wait} through {@code scoring.waitingPt}; on that
 * reading headway is a proxy for something the model has, and retiring it is
 * right — the argument that retired the two gradient weights (DECISIONS.md
 * 9.140, #21), where gradient already reached walk and bike through link
 * travel time.
 *
 * <p><b>That argument does not transfer, and the reason is a property of
 * MATSim rather than of Newcastle.</b> A MATSim agent has PERFECT TIMETABLE
 * KNOWLEDGE. It times its arrival at the stop to the departure it has chosen,
 * so a service running once an hour costs it almost the same wait as one
 * running every five minutes. A real traveller faces SCHEDULE DELAY: the
 * service's frequency constrains WHEN THEY CAN TRAVEL AT ALL, not merely how
 * long they stand at the stop. That cost is absent from this model entirely,
 * and {@code C.time_weights.beta_headway} is the declared parameter for it.
 *
 * <p>The same holds for variability. The mobsim produces REALISED delay, which
 * {@code beta_ivt} prices on the time actually taken. What is missing is the
 * disutility of NOT KNOWING IN ADVANCE, which is what a reliability weight is
 * for.
 *
 * <h2>Both parameters are used exactly as the literature defines them</h2>
 *
 * <p>No new number enters, and neither weight is re-interpreted to make it
 * wireable:
 *
 * <ul>
 *   <li><b>Headway.</b> The penalty is
 *       {@code beta_headway x headway_minutes} of equivalent in-vehicle time
 *       on the boarded route. At the declared {@code beta_headway} of 0.5 that
 *       is exactly the appraisal convention of half the service interval as
 *       the expected schedule-delay cost — the weight IS the convention, so
 *       wiring it introduces no assumption the registry had not already
 *       declared.</li>
 *   <li><b>Reliability.</b> The penalty is
 *       {@code beta_reliability x sd_minutes}, the RELIABILITY RATIO in its
 *       standard form: the standard deviation of journey time valued as a
 *       multiple of its mean. The declared 1.3 is that ratio.</li>
 * </ul>
 *
 * <p><b>Where the standard deviation comes from, and why it is derived rather
 * than assumed.</b> It is MEASURED FROM THE RUN'S OWN EVENTS: the spread of
 * {@code VehicleArrivesAtFacilityEvent.getDelay()} over every stop the route
 * served in the PREVIOUS iteration. Nothing is invented and no variability
 * input is required — a bus held in traffic on a shared carriageway becomes
 * unreliable because the mobsim delayed it, while a tram on its own alignment
 * does not. That is the mechanism behind the service-quality inversion this
 * gate exists to test: bus at +44.8 % against light rail at &minus;57.3 %, a
 * model preferring the infrequent, unreliable mode to the frequent, reliable
 * one.
 *
 * <p>In the FIRST scored iteration there is no previous measurement, so the
 * reliability penalty is zero and says so in the log. That is stated rather
 * than back-filled: a seeded standard deviation would be exactly the invented
 * number this project cannot absorb.
 *
 * <h2>The hook, read before the mechanism was designed</h2>
 *
 * <p>Trap 8 of the 9 September handover: {@code
 * RaptorInVehicleCostCalculator.getInVehicleCost} is handed no distance and no
 * stop identity, which is why the fare and a distance term could not go there
 * (9.162). Headway is a property of the ROUTE, and this class takes the route
 * identity from {@link
 * org.matsim.pt.transitSchedule.api.TransitSchedule} at construction and from
 * {@code TransitDriverStartsEvent} at run time, which carries the line, the
 * route and the departure. So the quantity is available where it is charged,
 * and it is charged in SCORING on the route the agent actually rode — the
 * same place {@code citysim.PtFareChargeHandler} charges the fare, and for the
 * same reason.
 *
 * <p>{@code representation = absent} recovers the previous model exactly:
 * nothing installs and no {@code PersonScoreEvent} of this kind is emitted.
 * Declared as {@code C.time_weights.service_quality_representation}.
 */
public final class ServiceQualityConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "serviceQuality";

    public static final String REPRESENTATION_ABSENT = "absent";
    public static final String REPRESENTATION_HEADWAY = "headway";
    public static final String REPRESENTATION_BOTH = "headway_and_reliability";

    private String representation = REPRESENTATION_ABSENT;
    /**
     * NO DEFAULTS. Each is a derived price the emitter computes from the
     * already-declared VOT identity; a literal here would be the same value
     * decided in two places (check_hardcoding.py category 6).
     */
    private double headwayUtilsPerMin = Double.NaN;
    private double reliabilityUtilsPerMin = Double.NaN;
    /** The longest headway a single-departure route may be charged for. */
    private double headwayCapMin = Double.NaN;

    public ServiceQualityConfigGroup() {
        super(NAME);
    }

    public boolean isEnabled() {
        return REPRESENTATION_HEADWAY.equals(this.representation)
                || REPRESENTATION_BOTH.equals(this.representation);
    }

    public boolean isReliability() {
        return REPRESENTATION_BOTH.equals(this.representation);
    }

    @StringGetter("representation")
    public String getRepresentation() {
        return this.representation;
    }

    @StringSetter("representation")
    public void setRepresentation(final String value) {
        this.representation = value == null ? "" : value.trim();
    }

    @StringGetter("headwayUtilsPerMin")
    public double getHeadwayUtilsPerMin() {
        return this.headwayUtilsPerMin;
    }

    @StringSetter("headwayUtilsPerMin")
    public void setHeadwayUtilsPerMin(final double value) {
        this.headwayUtilsPerMin = value;
    }

    @StringGetter("reliabilityUtilsPerMin")
    public double getReliabilityUtilsPerMin() {
        return this.reliabilityUtilsPerMin;
    }

    @StringSetter("reliabilityUtilsPerMin")
    public void setReliabilityUtilsPerMin(final double value) {
        this.reliabilityUtilsPerMin = value;
    }

    @StringGetter("headwayCapMin")
    public double getHeadwayCapMin() {
        return this.headwayCapMin;
    }

    @StringSetter("headwayCapMin")
    public void setHeadwayCapMin(final double value) {
        this.headwayCapMin = value;
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!REPRESENTATION_ABSENT.equals(this.representation)
                && !isEnabled()) {
            throw new IllegalStateException(
                    "serviceQuality.representation is '" + this.representation
                    + "', which is not " + REPRESENTATION_ABSENT + ", "
                    + REPRESENTATION_HEADWAY + " or " + REPRESENTATION_BOTH
                    + ". It is declared as "
                    + "C.time_weights.service_quality_representation.");
        }
        if (!isEnabled()) {
            return;
        }
        require(this.headwayUtilsPerMin, "headwayUtilsPerMin",
                "C.time_weights.beta_headway");
        require(this.headwayCapMin, "headwayCapMin", "RUN.qsim.end_time_h");
        if (isReliability()) {
            require(this.reliabilityUtilsPerMin, "reliabilityUtilsPerMin",
                    "C.time_weights.beta_reliability");
        }
    }

    private static void require(final double value, final String param,
                                final String declaredAs) {
        if (Double.isNaN(value)) {
            throw new IllegalStateException(
                    "serviceQuality." + param + " was not emitted while "
                    + "serviceQuality.representation is on. It is a DERIVED "
                    + "price this class holds no default for, computed by "
                    + "build_matsim_run_inputs.py from " + declaredAs + " and "
                    + "the trip-weighted VOT identity.");
        }
        if (value < 0.0) {
            throw new IllegalStateException(
                    "serviceQuality." + param + " is " + value
                    + ". A negative price would PAY a passenger for an "
                    + "infrequent or unreliable service.");
        }
    }
}
