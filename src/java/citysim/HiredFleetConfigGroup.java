package citysim;

import java.util.Map;
import java.util.TreeMap;
import org.matsim.core.config.Config;
import org.matsim.core.config.ReflectiveConfigGroup;

/** Explicit simulated supply, independent of road-capacity multipliers. */
public final class HiredFleetConfigGroup extends ReflectiveConfigGroup {
    public static final String NAME = "hiredFleet";
    @Parameter("representation") public String representation = "absent";
    @Parameter("vehiclesByMode") public String vehiclesByMode = "";
    @Parameter("maxWaitSeconds") public double maxWaitSeconds = Double.NaN;
    @Parameter("turnaroundSeconds") public double turnaroundSeconds = Double.NaN;

    public HiredFleetConfigGroup() { super(NAME); }
    public boolean enabled() { return "pooled_queue".equals(representation); }

    public Map<String, Integer> vehicles() {
        Map<String, Integer> out = new TreeMap<>();
        for (String entry : vehiclesByMode.split(",")) {
            String[] pair = entry.trim().split(":", -1);
            if (pair.length != 2 || pair[0].isBlank())
                throw new IllegalArgumentException("hiredFleet vehiclesByMode requires mode:count entries");
            int count = Integer.parseInt(pair[1]);
            if (count < 0 || out.putIfAbsent(pair[0], count) != null)
                throw new IllegalArgumentException("hiredFleet counts must be nonnegative and modes unique");
        }
        return out;
    }

    @Override protected void checkConsistency(Config config) {
        super.checkConsistency(config);
        if (!enabled() && !"absent".equals(representation))
            throw new IllegalArgumentException("Unknown hiredFleet representation");
        if (!enabled()) return;
        if (!Double.isFinite(maxWaitSeconds) || maxWaitSeconds < 0
                || !Double.isFinite(turnaroundSeconds) || turnaroundSeconds < 0)
            throw new IllegalArgumentException("hiredFleet waiting and turnaround must be explicit finite nonnegative seconds");
        for (String mode : vehicles().keySet()) {
            if (!config.qsim().getMainModes().contains(mode)
                    || !config.routing().getNetworkModes().contains(mode))
                throw new IllegalArgumentException("hiredFleet mode must be network simulated: " + mode);
        }
        TaxiFleetConfigGroup legacy = (TaxiFleetConfigGroup) config.getModules().get(TaxiFleetConfigGroup.NAME);
        if (legacy != null && legacy.isFleet() && vehicles().containsKey("taxi"))
            throw new IllegalArgumentException("Both fleet mechanisms cannot constrain taxi");
    }
}
