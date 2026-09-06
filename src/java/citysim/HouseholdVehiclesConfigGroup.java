package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/**
 * Whether a household's drivers share the cars the census says it owns.
 *
 * <p>Declared as {@code B.population.vehicle_roster} (DECISIONS.md 9.146).
 * {@code census}: every licensed, car-available member of a household is mapped
 * to one of {@code householdVehicles} shared vehicles, {@code hh<id>_car<k>},
 * so a one-car household has ONE car in the mobsim and the second member to
 * want it waits for it (qsim.vehicleBehavior, RUN.qsim.vehicle_behavior).
 * {@code per_person}: MATSim's own behaviour and every arm before 9.146 - each
 * person drives a vehicle of their own, so a household can put more cars on
 * the road than it owns. Measured at the F26 iteration-100 gate: 12,317 car
 * legs (3.28 % of resident car legs, 5,279 households) began while every
 * vehicle the household owns was already out, 4,265 of them a one-car
 * household with two members driving at once.
 *
 * <p>Absent from the emitted config the group reads {@code per_person}, so a
 * config written before the field existed runs exactly as it did.
 */
public final class HouseholdVehiclesConfigGroup extends ReflectiveConfigGroup {

    public static final String NAME = "householdVehicles";

    public static final String ROSTER_CENSUS = "census";
    public static final String ROSTER_PER_PERSON = "per_person";

    private String roster = ROSTER_PER_PERSON;

    public HouseholdVehiclesConfigGroup() {
        super(NAME);
    }

    /** B.population.vehicle_roster: `census` or `per_person`. */
    @StringGetter("roster")
    public String getRoster() {
        return this.roster;
    }

    @StringSetter("roster")
    public void setRoster(final String value) {
        this.roster = value == null || value.trim().isEmpty()
                ? ROSTER_PER_PERSON : value.trim();
    }

    public boolean isCensusRoster() {
        return ROSTER_CENSUS.equals(this.roster);
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!ROSTER_CENSUS.equals(this.roster)
                && !ROSTER_PER_PERSON.equals(this.roster)) {
            throw new IllegalArgumentException(
                    "householdVehicles.roster must be one of " + ROSTER_CENSUS
                    + " | " + ROSTER_PER_PERSON
                    + " (B.population.vehicle_roster); got '" + this.roster + "'");
        }
    }
}
