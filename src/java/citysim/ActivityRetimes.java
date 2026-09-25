package citysim;

import java.util.ArrayList;
import java.util.List;

import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.population.Activity;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.PlanElement;
import org.matsim.api.core.v01.population.Population;
import org.matsim.core.utils.misc.OptionalTime;

/**
 * Activity end times an engine overrides for ONE mobsim, and puts back after it.
 *
 * <p>An engine that executes something the plan did not say - the ride
 * engine moving a passenger onto a driver's clock (#187), the taxi fleet
 * holding a passenger at the kerb until a vehicle is free - writes the
 * executed time on the origin activity, lets the mobsim run and the score see
 * it, then restores the agent's own declared time so replanning stays the only
 * owner of plan memory. Both engines carried their own copy of this until 25
 * September 2026; this is the one.
 *
 * <p>An activity is restored only if it is still an element of the person's
 * selected plan: PersonPrepareForSim's PlanRouter keeps the activities and
 * replaces the legs between them, but a plan swapped by anything else must not
 * be written through a stale reference - that is counted as an orphan.
 */
final class ActivityRetimes {

    private static final class Retime {
        final Id<Person> person;
        final Activity activity;
        final OptionalTime was;

        Retime(final Id<Person> person, final Activity activity, final OptionalTime was) {
            this.person = person;
            this.activity = activity;
            this.was = was;
        }
    }

    private final List<Retime> retimes = new ArrayList<>();

    /** Override {@code activity}'s end time with {@code endTime} for this mobsim. */
    void set(final Id<Person> person, final Activity activity, final double endTime) {
        this.retimes.add(new Retime(person, activity, activity.getEndTime()));
        activity.setEndTime(endTime);
    }

    int size() {
        return this.retimes.size();
    }

    /**
     * Put every overridden end time back. Returns {restored, orphans} and
     * forgets the list.
     */
    int[] restore(final Population population) {
        int put = 0;
        int orphan = 0;
        for (final Retime r : this.retimes) {
            final Person person = population.getPersons().get(r.person);
            final Plan plan = person == null ? null : person.getSelectedPlan();
            boolean live = false;
            if (plan != null) {
                for (final PlanElement pe : plan.getPlanElements()) {
                    if (pe == r.activity) {
                        live = true;
                        break;
                    }
                }
            }
            if (!live) {
                orphan++;
                continue;
            }
            if (r.was.isDefined()) {
                r.activity.setEndTime(r.was.seconds());
            } else {
                r.activity.setEndTimeUndefined();
            }
            put++;
        }
        this.retimes.clear();
        return new int[] {put, orphan};
    }
}
