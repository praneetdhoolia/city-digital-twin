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

    @Parameter("assignment")
    public String assignment = "";

    public ActivityLinksConfigGroup() {
        super(NAME);
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
    }
}
