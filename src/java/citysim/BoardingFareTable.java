package citysim;

import com.google.inject.Inject;
import com.google.inject.Singleton;
import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVRecord;
import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;

/** Immutable tariffs shared by executed boarding charges and transit routing. */
@Singleton
public final class BoardingFareTable {
    static final class Rule {
        final String profile;
        final double[] bounds;
        final double[] fares;
        final double rate;

        Rule(final String profile, final String bounds, final String fares,
                final double rate) {
            this.profile = profile;
            this.bounds = parse(bounds);
            this.fares = parse(fares);
            this.rate = rate;
            if (this.bounds.length != this.fares.length || !Double.isFinite(rate) || rate < 0) {
                throw new IllegalArgumentException("Invalid fare table: " + profile);
            }
            for (int i = 0; i < this.bounds.length; i++) {
                if (!Double.isFinite(this.bounds[i]) || this.bounds[i] <= 0
                        || !Double.isFinite(this.fares[i]) || this.fares[i] < 0
                        || (i > 0 && this.bounds[i] <= this.bounds[i - 1])) {
                    throw new IllegalArgumentException("Invalid fare bands: " + profile);
                }
            }
        }

        private static double[] parse(final String value) {
            return value.isBlank() ? new double[0]
                    : Arrays.stream(value.split("\\|", -1)).mapToDouble(Double::parseDouble).toArray();
        }

        double price(final double distance) {
            if (!Double.isFinite(distance) || distance < 0) {
                throw new IllegalArgumentException("Invalid travelled fare distance");
            }
            for (int i = 0; i < this.bounds.length; i++) {
                if (distance <= this.bounds[i]) {
                    return this.fares[i];
                }
            }
            final int last = this.bounds.length - 1;
            return last < 0 ? distance * this.rate
                    : this.fares[last] + (distance - this.bounds[last]) * this.rate;
        }
    }

    private final Map<String, Rule> lineRules = new HashMap<>();
    private final Map<String, Rule> modeRules = new HashMap<>();
    private final Map<String, String> currencies = new HashMap<>();

    @Inject
    public BoardingFareTable(final Config config, final Scenario scenario) {
        final String table = ConfigUtils.addOrGetModule(config, BoardingFareConfigGroup.class).tableFile;
        try (Reader reader = Files.newBufferedReader(Path.of(table), StandardCharsets.UTF_8)) {
            for (final CSVRecord row : CSVFormat.DEFAULT.withFirstRecordAsHeader().parse(reader)) {
                final Rule rule = new Rule(row.get("profile_id"), row.get("upper_bounds_m"),
                        row.get("fares_money"), Double.parseDouble(row.get("linear_rate_money_per_m")));
                if (!rule.profile.matches("[A-Za-z0-9_.-]+") || !row.get("currency_code").matches("[A-Z]{3}")) {
                    throw new IllegalArgumentException("Fare profile or currency is not a valid identifier");
                }
                this.currencies.put(rule.profile, row.get("currency_code"));
                final Map<String, Rule> target;
                if (row.get("match_kind").equals("line")) {
                    target = this.lineRules;
                } else if (row.get("match_kind").equals("mode")) {
                    target = this.modeRules;
                } else {
                    throw new IllegalArgumentException("Unknown fare match kind: " + row.get("match_kind"));
                }
                if (target.putIfAbsent(row.get("match_id"), rule) != null) {
                    throw new IllegalArgumentException("Duplicate fare match: " + row.get("match_id"));
                }
            }
        } catch (final IOException e) {
            throw new IllegalArgumentException("Cannot read boarding fare table", e);
        }
        scenario.getTransitSchedule().getTransitLines().values().forEach(line ->
            line.getRoutes().values().forEach(route -> rule(line.getId().toString(), route.getTransportMode())));
    }

    Rule rule(final String line, final String mode) {
        final Rule selected = this.lineRules.containsKey(line) ? this.lineRules.get(line) : this.modeRules.get(mode);
        if (selected == null) {
            throw new IllegalArgumentException("No fare policy for transit line " + line + " / " + mode);
        }
        return selected;
    }

    String currency(final String profile) { return this.currencies.get(profile); }
}
