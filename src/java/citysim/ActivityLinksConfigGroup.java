package citysim;

import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;
import org.matsim.core.config.ReflectiveConfigGroup.Parameter;
import org.matsim.core.config.groups.RoutingConfigGroup.AccessEgressType;

/** Whether activities require a common link or use each mode's access legs. */
public final class ActivityLinksConfigGroup extends ReflectiveConfigGroup {
    public static final String NAME = "activityLinks";
    public static final String COMMON = "common_modes";
    public static final String ACCESS = "mode_specific_access";

    /** RUN.routing.activity_link_capacity: {@code nearest} is F38 exactly -
     *  the nearest link carrying every needed mode, however many trip ends it
     *  collects; {@code capacity_bounded} (D28, F39) moves an activity whose
     *  car-capable trip ends would take its link past what the link can move
     *  in the modelled day to the next-nearest eligible link that can. */
    public static final String CAPACITY_NEAREST = "nearest";
    public static final String CAPACITY_BOUNDED = "capacity_bounded";

    @Parameter("assignment")
    public String assignment = "";

    @Parameter("capacityRule")
    public String capacityRule = CAPACITY_NEAREST;

    /** RUN.routing.activity_link_service_hours (derived): the hours of the
     *  modelled day a link's sampled capacity is counted over. */
    @Parameter("serviceHours")
    public double serviceHours = 0.0;

    public ActivityLinksConfigGroup() {
        super(NAME);
    }

    public boolean isCapacityBounded() {
        return CAPACITY_BOUNDED.equals(capacityRule == null ? "" : capacityRule.trim());
    }

    @Override
    public void checkConsistency(final Config config) {
        super.checkConsistency(config);
        if (!COMMON.equals(assignment) && !ACCESS.equals(assignment)) {
            throw new IllegalStateException("activityLinks.assignment must explicitly be "
                    + COMMON + " or " + ACCESS + "; got '" + assignment + "'");
        }
        if (ACCESS.equals(assignment)) {
            final AccessEgressType access = config.routing().getAccessEgressType();
            if (access != AccessEgressType.accessEgressModeToLink
                    && access != AccessEgressType.accessEgressModeToLinkPlusTimeConstant) {
                throw new IllegalStateException("mode_specific_access requires routed access/egress; "
                        + "routing.accessEgressType=" + access);
            }
        }
        final String rule = capacityRule == null ? CAPACITY_NEAREST : capacityRule.trim();
        if (!CAPACITY_NEAREST.equals(rule) && !CAPACITY_BOUNDED.equals(rule)) {
            throw new IllegalStateException("activityLinks.capacityRule must be "
                    + CAPACITY_NEAREST + " or " + CAPACITY_BOUNDED
                    + " (RUN.routing.activity_link_capacity); got '" + capacityRule + "'");
        }
        capacityRule = rule;
        if (CAPACITY_BOUNDED.equals(rule)) {
            if (!COMMON.equals(assignment)) {
                throw new IllegalStateException(CAPACITY_BOUNDED + " moves the common link "
                        + "an activity is given, so it needs assignment=" + COMMON
                        + "; got '" + assignment + "'");
            }
            if (!(serviceHours > 0.0)) {
                throw new IllegalStateException(CAPACITY_BOUNDED + " needs a positive "
                        + "activityLinks.serviceHours (RUN.routing.activity_link_service_hours); got "
                        + serviceHours);
            }
        }
    }
}
