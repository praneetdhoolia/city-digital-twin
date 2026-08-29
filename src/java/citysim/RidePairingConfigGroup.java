package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * The `ridePairing` config module: how a car passenger names the household
 * member who drives them.
 *
 * <p>Every value here is written by {@code build_matsim_run_inputs.py} from
 * {@code cities/<city>/registry/B_demand.json}. None of them may be typed into
 * a script, and none of them is a place: the pairing is decided on link
 * identity and clock time, both of which come out of the agents' own plans.
 * Java does no spatial work at all.
 *
 * <p>Declaring this as a real {@link ReflectiveConfigGroup} rather than letting
 * MATSim absorb an unknown module buys what the `parking` and `telemetry`
 * modules buy: an unrecognised parameter fails the run instead of being
 * ignored, and the module lands in the output config dump, so a result carries
 * the pairing regime that produced it.
 *
 * <p>See DECISIONS.md 9.44 and issue #31.
 */
public final class RidePairingConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "ridePairing";

    /**
     * Sentinel meaning "the config never set it", NOT a usable value.
     *
     * <p>The lesson {@link TelemetryConfigGroup} records applies here in full: a
     * Java default that EQUALS its registry value is right by accident, passes
     * every test, and silently stops being right the moment anyone sweeps the
     * field. {@link #checkConsistency} refuses such a run instead.
     */
    private static final double UNSET = -1.0;

    /** The five rules {@code B.ride.pairing_rule} may take. */
    public static final String RULE_BOTH_LINKS = "both_links";
    public static final String RULE_ORIGIN_LINK = "origin_link";
    public static final String RULE_DEST_LINK = "dest_link";
    public static final String RULE_WINDOW_ONLY = "window_only";
    /**
     * The passenger's two links both lie ON the driver's routed path, in
     * order. This is the only rule that can represent a DROP-OFF EN ROUTE,
     * and that is the commonest car-passenger trip there is: a parent who
     * drives a child to school and carries on to work has a car leg from
     * home to work, so {@link #RULE_BOTH_LINKS} refuses it by construction
     * however wide the window is opened.
     */
    public static final String RULE_ROUTE_CONTAINS = "route_contains";

    /** What an unpairable ride leg is EXECUTED as, this iteration. */
    public static final String FALLBACK_WALK = "walk";
    public static final String FALLBACK_DRIVE_ELSE_WALK =
            "licensed_drive_else_walk";

    private boolean enabled = false;
    private boolean physicalBoarding = false;
    private boolean remodeUnpaired = false;
    private boolean waitForDriver = false;
    private double windowMinutes = UNSET;
    private double boundWindowMinutes = UNSET;
    private double escortCoherenceRate = UNSET;
    private double jointCoherenceRate = UNSET;
    private String rule = "";
    private String unpairedFallback = "";
    private double pickupDwellSeconds = UNSET;
    private int maxPassengersPerVehicle = -1;

    public RidePairingConfigGroup() {
        super(NAME);
    }

    /**
     * Whether a ride leg may name a driver at all.
     *
     * <p>False restores exactly the behaviour of every run made before this
     * class existed — a teleported passenger on their own routed time — so the
     * two are comparable within one build, which is what
     * {@code B.population.ride_requires_household_driver} does for the
     * availability rule. The default is false for the same reason the parking
     * price file defaults to empty: an absent binding must not switch a
     * mechanism on.
     */
    @StringGetter("enabled")
    public boolean isEnabled() {
        return this.enabled;
    }

    @StringSetter("enabled")
    public void setEnabled(final boolean value) {
        this.enabled = value;
    }

    /**
     * Whether a PAIRED passenger physically boards the driver's vehicle
     * (DECISIONS.md 9.53, issue #48) instead of inheriting its clock.
     *
     * <p>With this on, {@link JointRideEngine} claims the ride departure of
     * every booked passenger whose driver's car is parked at their shared
     * origin link, boards them (a real {@code PersonEntersVehicleEvent}), and
     * alights them when the car reaches their shared destination link. A
     * booked passenger whose car has ALREADY LEFT falls back to Tier 1's
     * teleport-on-the-driver's-clock, counted and reported — never hidden.
     * False restores Tier 1 exactly (DECISIONS.md 9.44).
     */
    @StringGetter("physicalBoarding")
    public boolean isPhysicalBoarding() {
        return this.physicalBoarding;
    }

    @StringSetter("physicalBoarding")
    public void setPhysicalBoarding(final boolean value) {
        this.physicalBoarding = value;
    }

    /**
     * Whether an UNPAIRED ride leg is re-moded to network-simulated walk at
     * the BeforeMobsim boundary (DECISIONS.md 9.55, the 9.51 directive's own
     * ruling: no exceptions, no teleportation). A ride trip no household
     * driver can physically serve is not a ride trip; it walks - physically,
     * at walking speed, which scores terribly for a long trip, so
     * co-evolution reassigns those tours to feasible modes across iterations
     * and ride becomes EMERGENT: only what the driver supply can carry
     * survives. No parameter is invented; the physical constraint is the
     * price. False keeps Tier 1's teleport for the unpaired, for
     * comparability within one build.
     */
    @StringGetter("remodeUnpaired")
    public boolean isRemodeUnpaired() {
        return this.remodeUnpaired;
    }

    @StringSetter("remodeUnpaired")
    public void setRemodeUnpaired(final boolean value) {
        this.remodeUnpaired = value;
    }

    /**
     * Whether a booked passenger whose car is NOT at the link yet physically
     * WAITS for it (DECISIONS.md 9.60): the person stands at the meeting
     * point until the booked driver's car is parked there, boards it then,
     * and gives up after the declared pairing window - the same tolerance the
     * booking itself was made under, so no second number is invented. The
     * wait is real elapsed time: a timed-out passenger completes the leg on
     * the Tier-1 fallback clock FROM THE MOMENT OF TIMEOUT, so waiting
     * costs what waiting costs. False restores the 9.53 behaviour (any miss
     * falls back immediately).
     */
    @StringGetter("waitForDriver")
    public boolean isWaitForDriver() {
        return this.waitForDriver;
    }

    @StringSetter("waitForDriver")
    public void setWaitForDriver(final boolean value) {
        this.waitForDriver = value;
    }

    /**
     * How far apart the passenger's and the driver's planned departures may be
     * and still be one trip, in minutes.
     *
     * <p>This is the tolerance the pairing is allowed, NOT a modelled waiting
     * time: Tier 1 does not move the passenger's departure, because shifting it
     * would cascade through the rest of that person's day and the blast radius
     * of this change is deliberately bounded (DECISIONS.md 9.44). The
     * unmodelled sub-window adjustment is a stated limitation, and
     * {@link #getPickupDwellSeconds()} is the only friction that is priced.
     */
    @StringGetter("windowMinutes")
    public double getWindowMinutes() {
        return this.windowMinutes;
    }

    @StringSetter("windowMinutes")
    public void setWindowMinutes(final double value) {
        this.windowMinutes = value;
    }

    /**
     * The tolerance for a pair the DEMAND DECLARES, rather than one the
     * engine has to infer (DECISIONS.md 9.85).
     *
     * <p>{@link #getWindowMinutes()} answers "are these two people making
     * the same trip?" from geometry and the clock, because for an
     * arbitrary pair of household members that is the only evidence there
     * is. For a companion and the driver named on their joint binding
     * there is better evidence: B2 generated the two tours AS A PAIR, and
     * since 9.85 the population carries the driver's identity on the
     * companion as {@code boundDriver}. Identity has already answered the
     * question the window exists to answer, so what this tolerance bounds
     * is only how far MATSim's OWN replanning has moved the two apart
     * since - which is why {@code B.ride.bound_pairing_window_min} is
     * DERIVED from {@code RUN.replanning.time_mutation_range_s} and not a
     * free value.
     *
     * <p>It relaxes IDENTIFICATION only. Endpoints, vehicle capacity and
     * physical boarding decide as before whether the pairing is made, and
     * the realised gap becomes waiting time the passenger pays for in
     * score - so an implausible pairing is refused by the scoring rather
     * than by a threshold. Setting it equal to {@code windowMinutes}
     * recovers the pre-9.85 behaviour exactly.
     */
    @StringGetter("boundWindowMinutes")
    public double getBoundWindowMinutes() {
        return this.boundWindowMinutes;
    }

    @StringSetter("boundWindowMinutes")
    public void setBoundWindowMinutes(final double value) {
        this.boundWindowMinutes = value;
    }

    /**
     * How often a DECOHERED escort pair is re-proposed as a ride.
     *
     * <p>B2 generates escort travel as a pair, and MATSim replans the two
     * agents independently, so the two-sided state cannot be proposed by any
     * per-agent strategy and cannot recohere once lost. This is the rate at
     * which {@link EscortCoherenceListener} offers the coherent plan back to
     * the escorted member; the plan is then scored like any other and kept
     * only if it earns its place.
     *
     * <p><b>Zero recovers today's behaviour exactly</b>, which is what makes
     * the effect of this mechanism measurable rather than assumed. It is a
     * search parameter - how often an unreachable alternative is offered - and
     * never a preference: nothing here changes any mode's utility.
     */
    @StringGetter("escortCoherenceRate")
    public double getEscortCoherenceRate() {
        return this.escortCoherenceRate;
    }

    @StringSetter("escortCoherenceRate")
    public void setEscortCoherenceRate(final double value) {
        this.escortCoherenceRate = value;
    }

    /**
     * How often a DECOHERED joint (non-escort) household pair is re-proposed
     * as a ride (DECISIONS.md 9.84).
     *
     * <p>The 9.84 joint binder generates two-person household travel as a
     * PAIR - a driver's tour and a companion's mirror of it - and per-agent
     * replanning splits them exactly as it split the escort pairs (the 9.82
     * defect class). This is the rate at which
     * {@link EscortCoherenceListener} offers the coherent state back to a
     * household member whose trip shares a car leg's endpoints, whatever
     * activity that car leg arrives at. <b>Zero recovers the escort-only
     * behaviour exactly</b>, so the joint extension is measurable on its
     * own. A search parameter, never a preference.
     */
    @StringGetter("jointCoherenceRate")
    public double getJointCoherenceRate() {
        return this.jointCoherenceRate;
    }

    @StringSetter("jointCoherenceRate")
    public void setJointCoherenceRate(final double value) {
        this.jointCoherenceRate = value;
    }

    /**
     * Which endpoints of the driver's leg must coincide with the passenger's.
     *
     * <p>{@link #RULE_BOTH_LINKS} and {@link #RULE_ROUTE_CONTAINS} are the
     * two rules under which handing the driver's time to the passenger is
     * CORRECT rather than merely closer. Under the first the two are the same
     * trip. Under the second the passenger occupies a SUB-SEGMENT of the
     * driver's path, so the engine apportions the driver's time by that
     * segment's share of the route's length - which reduces to the whole leg
     * when the segment is the whole route, so `both_links` reproduces exactly.
     * {@link #RULE_ORIGIN_LINK}, {@link #RULE_DEST_LINK} and
     * {@link #RULE_WINDOW_ONLY} match trips that need not overlap at all, so a
     * run made under one of them is a sensitivity, not a result.
     */
    /**
     * What an unpairable ride leg is executed as for this mobsim.
     *
     * <p>{@link #FALLBACK_WALK} was the only behaviour before 9.105 and
     * reproduces it exactly. It is not a behaviour so much as a placeholder:
     * a person denied a lift for a 10 km trip does not walk it, and forcing
     * them to made walk 12.5x its observed mean trip length.
     * {@link #FALLBACK_DRIVE_ELSE_WALK} lets a passenger who holds a licence
     * and has a car available DRIVE instead, which is what the household
     * actually does, and leaves everyone else walking as before. Either way
     * the ride alternative is restored at AfterMobsim - 9.81's ratchet must
     * not come back.
     */
    @StringGetter("unpairedFallback")
    public String getUnpairedFallback() {
        return this.unpairedFallback;
    }

    @StringSetter("unpairedFallback")
    public void setUnpairedFallback(final String value) {
        this.unpairedFallback = value == null ? "" : value.trim();
    }

    @StringGetter("rule")
    public String getRule() {
        return this.rule;
    }

    @StringSetter("rule")
    public void setRule(final String value) {
        this.rule = value == null ? "" : value.trim();
    }

    /**
     * Seconds added to a paired passenger's travel time for being picked up.
     *
     * <p>DELIBERATELY NEUTRAL BY DEFAULT. The measured car-minus-ride residual
     * this whole lane exists to remove is about 5 s at 25% and 13 s at 10%
     * (NEXT_AGENT_BRIEF.md 2), so a one-minute pickup friction would be five to
     * twelve times the entire quantity it was supposed to explain. Sizing one
     * to close that gap is calibration wearing a mechanism's clothes and was
     * REFUSED (DECISIONS.md 9.44). This field exists so the question can be
     * SWEPT — no local observation of pickup dwell exists — and its value is
     * never fitted.
     */
    @StringGetter("pickupDwellSeconds")
    public double getPickupDwellSeconds() {
        return this.pickupDwellSeconds;
    }

    @StringSetter("pickupDwellSeconds")
    public void setPickupDwellSeconds(final double value) {
        this.pickupDwellSeconds = value;
    }

    /**
     * How many passengers one driver's leg may carry.
     *
     * <p>Without a cap one driver would serve every passenger their household
     * offered, which is the same unbounded-supply defect
     * {@code rideAvail} removed on the availability side.
     */
    @StringGetter("maxPassengersPerVehicle")
    public int getMaxPassengersPerVehicle() {
        return this.maxPassengersPerVehicle;
    }

    @StringSetter("maxPassengersPerVehicle")
    public void setMaxPassengersPerVehicle(final int value) {
        this.maxPassengersPerVehicle = value;
    }

    /**
     * Refuse a pairing module that is switched on and carries no regime.
     *
     * <p>The config is BUILT from the registry by
     * {@code src/registry/param_config.py}, so a missing parameter means the
     * binding was lost — and the one thing that must not then happen is for the
     * run to continue on a number nobody chose.
     */
    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!this.enabled) {
            return;
        }
        require(this.windowMinutes >= 0.0, "windowMinutes", "B.ride.pairing_window_min");
        require(this.boundWindowMinutes >= 0.0, "boundWindowMinutes",
                "B.ride.bound_pairing_window_min");
        // A declared pair may not be recognised on LOOSER evidence than an
        // inferred one: that would make the binding a way to buy pairings
        // rather than a way to keep the ones the demand already stated.
        require(this.boundWindowMinutes >= this.windowMinutes,
                "boundWindowMinutes", "B.ride.bound_pairing_window_min");
        require(this.escortCoherenceRate >= 0.0, "escortCoherenceRate",
                "B.ride.escort_coherence_rate");
        require(this.jointCoherenceRate >= 0.0, "jointCoherenceRate",
                "B.ride.joint_coherence_rate");
        require(this.pickupDwellSeconds >= 0.0, "pickupDwellSeconds",
                "B.ride.pickup_dwell_s");
        require(this.maxPassengersPerVehicle >= 1, "maxPassengersPerVehicle",
                "B.ride.max_passengers_per_vehicle");
        require(!this.rule.isEmpty(), "rule", "B.ride.pairing_rule");
        require(!this.unpairedFallback.isEmpty(), "unpairedFallback",
                "B.ride.unpaired_fallback");
        if (!FALLBACK_WALK.equals(this.unpairedFallback)
                && !FALLBACK_DRIVE_ELSE_WALK.equals(this.unpairedFallback)) {
            throw new RuntimeException(
                    "ridePairing.unpairedFallback is '" + this.unpairedFallback
                    + "', which is not one of " + FALLBACK_WALK + ", "
                    + FALLBACK_DRIVE_ELSE_WALK
                    + ". It is declared as B.ride.unpaired_fallback.");
        }
        if (!RULE_BOTH_LINKS.equals(this.rule) && !RULE_ORIGIN_LINK.equals(this.rule)
                && !RULE_DEST_LINK.equals(this.rule)
                && !RULE_ROUTE_CONTAINS.equals(this.rule)
                && !RULE_WINDOW_ONLY.equals(this.rule)) {
            throw new IllegalStateException(
                    "ridePairing.rule is '" + this.rule + "', which is not one of "
                    + RULE_BOTH_LINKS + ", " + RULE_ORIGIN_LINK + ", "
                    + RULE_DEST_LINK + ", " + RULE_ROUTE_CONTAINS + ", "
                    + RULE_WINDOW_ONLY
                    + ". The rule is declared as B.ride.pairing_rule.");
        }
    }

    private static void require(final boolean ok, final String param,
                                final String field) {
        if (!ok) {
            throw new IllegalStateException(
                    "ridePairing." + param + " was never set, but ridePairing is "
                    + "enabled. It is declared as " + field + " and written into "
                    + "the config by src/registry/param_config.py; this class "
                    + "keeps no usable default, because a default equal to the "
                    + "declared value is right by accident.");
        }
    }
}
