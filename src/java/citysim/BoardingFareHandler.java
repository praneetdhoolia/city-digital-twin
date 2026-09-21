package citysim;

import com.google.inject.Inject;
import citysim.BoardingFareTable.Rule;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.events.LinkEnterEvent;
import org.matsim.api.core.v01.events.PersonEntersVehicleEvent;
import org.matsim.api.core.v01.events.PersonLeavesVehicleEvent;
import org.matsim.api.core.v01.events.PersonMoneyEvent;
import org.matsim.api.core.v01.events.TransitDriverStartsEvent;
import org.matsim.api.core.v01.events.handler.LinkEnterEventHandler;
import org.matsim.api.core.v01.events.handler.PersonEntersVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.PersonLeavesVehicleEventHandler;
import org.matsim.api.core.v01.events.handler.TransitDriverStartsEventHandler;
import org.matsim.api.core.v01.population.Person;
import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.events.AfterMobsimEvent;
import org.matsim.core.controler.listener.AfterMobsimListener;
import org.matsim.vehicles.Vehicle;

/**
 * Prices completed boardings from city-owned line or mode tariffs. Distance is
 * the sum of network links entered after boarding and before alighting. This
 * is a modelled distance basis, not a claim about an operator's fare stages.
 * Transfers are separate tickets. Caps, concessions and passes require their
 * own declared rules and are not inferred here. Money is emitted after mobsim
 * so native income-sensitive scoring sees each fare once.
 */
public final class BoardingFareHandler implements LinkEnterEventHandler,
        PersonEntersVehicleEventHandler, PersonLeavesVehicleEventHandler,
        TransitDriverStartsEventHandler, AfterMobsimListener {
    public static final String PURPOSE = "boardingFare";

    private static final class Service {
        final String line;
        final Rule rule;
        double distance;
        Service(final String line, final Rule rule) {
            this.line = line;
            this.rule = rule;
        }
    }

    private record Boarding(Id<Vehicle> vehicle, Service service, double distance) { }
    private static final class Totals {
        long completed;
        long extended;
        long unfinished;
        double distance;
        double money;
    }

    private final Scenario scenario;
    private final EventsManager events;
    private final Path auditPath;
    private final BoardingFareTable fareTable;
    private final Map<Id<Vehicle>, Service> services = new HashMap<>();
    private final Map<Id<Person>, Boarding> aboard = new HashMap<>();
    private final Set<Id<Person>> drivers = new HashSet<>();
    private final List<PersonMoneyEvent> pending = new ArrayList<>();
    private final Map<String, Totals> totals = new TreeMap<>();
    private int iteration;

    @Inject
    public BoardingFareHandler(final Config config, final EventsManager events,
            final Scenario scenario, final BoardingFareTable fareTable) {
        this.fareTable = fareTable;
        this.scenario = scenario;
        this.events = events;
        this.auditPath = Path.of(config.controller().getOutputDirectory(), "boarding_fares.csv");
        if (ConfigUtils.addOrGetModule(config, PtFareConfigGroup.class).isEnabled()) {
            throw new IllegalArgumentException("Two public-transport fare handlers cannot charge one journey");
        }
        final Set<String> transitModes = new HashSet<>(config.transit().getTransitModes());
        scenario.getTransitSchedule().getTransitLines().values().forEach(line ->
            line.getRoutes().values().forEach(route -> transitModes.add(route.getTransportMode())));
        for (final var scoring : config.scoring().getScoringParametersPerSubpopulation().values()) {
            for (final var mode : scoring.getModes().values()) {
                if (transitModes.contains(mode.getMode()) && mode.getMonetaryDistanceRate() != 0) {
                    throw new IllegalArgumentException("Boarding fare requires zero native PT distance charge: " + mode.getMode());
                }
            }
        }
    }

    @Override
    public void handleEvent(final TransitDriverStartsEvent event) {
        this.drivers.add(event.getDriverId());
        final var line = this.scenario.getTransitSchedule().getTransitLines().get(event.getTransitLineId());
        final var route = line.getRoutes().get(event.getTransitRouteId());
        this.services.put(event.getVehicleId(), new Service(line.getId().toString(),
                this.fareTable.rule(line.getId().toString(), route.getTransportMode())));
    }

    @Override
    public void handleEvent(final LinkEnterEvent event) {
        final Service service = this.services.get(event.getVehicleId());
        if (service != null) {
            service.distance += this.scenario.getNetwork().getLinks().get(event.getLinkId()).getLength();
        }
    }

    @Override
    public void handleEvent(final PersonEntersVehicleEvent event) {
        final Service service = this.services.get(event.getVehicleId());
        if (service != null && !this.drivers.contains(event.getPersonId())) {
            if (this.aboard.putIfAbsent(event.getPersonId(), new Boarding(event.getVehicleId(),
                    service, service.distance)) != null) {
                throw new IllegalStateException("Person already aboard a priced transit vehicle");
            }
        }
    }

    @Override
    public void handleEvent(final PersonLeavesVehicleEvent event) {
        final Boarding boarding = this.aboard.remove(event.getPersonId());
        if (boarding == null) {
            return;
        }
        if (!boarding.vehicle().equals(event.getVehicleId())) {
            throw new IllegalStateException("Fare alighting vehicle differs from boarding");
        }
        final double distance = boarding.service().distance - boarding.distance();
        final Rule rule = boarding.service().rule;
        final double price = rule.price(distance);
        final Totals total = this.totals.computeIfAbsent(rule.profile, k -> new Totals());
        total.completed++;
        total.distance += distance;
        total.money += price;
        if (rule.bounds.length > 0 && distance > rule.bounds[rule.bounds.length - 1]) {
            total.extended++;
        }
        this.pending.add(new PersonMoneyEvent(event.getTime(), event.getPersonId(), -price,
                PURPOSE, rule.profile, boarding.service().line));
    }

    @Override
    public void notifyAfterMobsim(final AfterMobsimEvent event) {
        for (final Boarding boarding : this.aboard.values()) {
            this.totals.computeIfAbsent(boarding.service().rule.profile, k -> new Totals()).unfinished++;
        }
        for (final PersonMoneyEvent money : this.pending) {
            this.events.processEvent(money);
        }
        this.pending.clear();
        final StringBuilder out = new StringBuilder();
        if (!Files.exists(this.auditPath)) {
            out.append("iteration,profile_id,currency_code,completed_boardings_count,travelled_distance_m,charged_money,extended_boardings_count,unfinished_boardings_count\n");
        }
        this.totals.forEach((profile, total) -> out.append(this.iteration).append(',').append(profile)
                .append(',').append(this.fareTable.currency(profile))
                .append(',').append(total.completed).append(',').append(total.distance)
                .append(',').append(total.money).append(',').append(total.extended)
                .append(',').append(total.unfinished).append('\n'));
        try {
            Files.writeString(this.auditPath, out.toString(), StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (final IOException e) {
            throw new IllegalStateException("Cannot write fare audit", e);
        }
    }

    @Override
    public void reset(final int iteration) {
        this.iteration = iteration;
        this.services.clear();
        this.aboard.clear();
        this.drivers.clear();
        this.pending.clear();
        this.totals.clear();
    }
}
