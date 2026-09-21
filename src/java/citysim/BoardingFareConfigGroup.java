package citysim;

import org.matsim.core.config.ReflectiveConfigGroup;
import org.matsim.core.config.ReflectiveConfigGroup.Parameter;

/** Optional city-supplied per-boarding fares; no tariff defaults live here. */
public final class BoardingFareConfigGroup extends ReflectiveConfigGroup {
    public static final String NAME = "boardingFare";
    @Parameter("tableFile")
    public String tableFile = "";
    @Parameter("routeChoice")
    public boolean routeChoice = false;

    public BoardingFareConfigGroup() {
        super(NAME);
    }

    public boolean isEnabled() {
        return !this.tableFile.isBlank();
    }
}
