package citysim;

import com.google.inject.Inject;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.core.config.Config;
import org.matsim.core.controler.events.StartupEvent;
import org.matsim.core.controler.listener.StartupListener;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.algorithms.TransportModeNetworkFilter;
import org.matsim.core.router.SingleModeNetworksCache;

/**
 * One routing network per DISTINCT link set, not one per mode.
 *
 * <p>MATSim's {@link SingleModeNetworksCache} builds one filtered copy of the
 * network per routing network mode. Seven network modes - car, ride, truck,
 * motorbike, taxi, walk, bike - made seven copies, and five of them were the
 * SAME link set, because the run-input assembler puts every car companion
 * mode on every car link. Under a time-variant network (the level-crossing
 * change events, #68) each copy is made of {@code TimeVariantLinkImpl} links
 * with three time-variant attribute objects each, and the filter copies the
 * change events onto every copy - so a copy is not cheap, and five of them
 * were the same one.
 *
 * <p>Measured 12 September 2026 on the footpath network (#183) at a 1 %
 * sample: 2.2 million link objects live for a 383,000-link network, 6.6
 * million time-variant attributes, and the JVM out of heap at 10.1 GiB where
 * the previous network's probe held 2.8 GiB. This listener seeds the cache
 * at startup - before {@code PrepareForSim} creates the first router - with
 * one copy per distinct link set, built exactly as the cache builds its own
 * (time-variant, change events copied), registered under every mode that
 * shares it. Nothing about a route changes: a mode's copy carries exactly the
 * links that admit it, with the same lengths, speeds, lane counts and closure
 * events, and {@code SpeedyALTFactory} keys its graph and landmarks by network
 * object, so the modes that share a copy also share those.
 */
public final class SharedModeNetworks implements StartupListener {

    private static final Logger LOG = LogManager.getLogger(SharedModeNetworks.class);

    private final Network network;
    private final Config config;
    private final SingleModeNetworksCache cache;

    @Inject
    SharedModeNetworks(final Network network, final Config config,
                       final SingleModeNetworksCache cache) {
        this.network = network;
        this.config = config;
        this.cache = cache;
    }

    @Override
    public void notifyStartup(final StartupEvent event) {
        final List<String> modes = new ArrayList<>(config.routing().getNetworkModes());
        if (modes.isEmpty()) {
            return;
        }
        // group the modes by the exact set of links that admit them
        final Map<String, Set<Id<Link>>> linksOf = new LinkedHashMap<>();
        for (final String mode : modes) {
            final Set<Id<Link>> ids = new HashSet<>();
            for (final Link link : network.getLinks().values()) {
                if (link.getAllowedModes().contains(mode)) {
                    ids.add(link.getId());
                }
            }
            linksOf.put(mode, ids);
        }
        final List<List<String>> groups = new ArrayList<>();
        for (final String mode : modes) {
            boolean placed = false;
            for (final List<String> group : groups) {
                if (linksOf.get(group.get(0)).equals(linksOf.get(mode))) {
                    group.add(mode);
                    placed = true;
                    break;
                }
            }
            if (!placed) {
                final List<String> group = new ArrayList<>();
                group.add(mode);
                groups.add(group);
            }
        }
        final Map<String, Network> registry = cache.getSingleModeNetworksCache();
        final StringBuilder note = new StringBuilder();
        synchronized (registry) {
            for (final List<String> group : groups) {
                // time-variant like the cache's own copies: the filter copies
                // the change events onto the copy (TransportModeNetworkFilter
                // .filter -> addNetworkChangeEvent), so a routing copy that
                // could not hold one is refused at the first crossing link
                final Network copy = NetworkUtils.createNetwork(config.network());
                new TransportModeNetworkFilter(network).filter(copy, new HashSet<>(group));
                final int expected = linksOf.get(group.get(0)).size();
                if (copy.getLinks().size() != expected) {
                    throw new IllegalStateException(String.format(
                            "sharedModeNetworks: the filtered copy for %s holds %d links "
                            + "where the network admits %d - refusing to seed a routing "
                            + "network that is not the mode's own",
                            group, copy.getLinks().size(), expected));
                }
                for (final String mode : group) {
                    registry.put(mode, copy);
                }
                note.append(String.format("%s%s: %,d links",
                        note.length() == 0 ? "" : "; ", new TreeSet<>(group), expected));
            }
        }
        LOG.info("sharedModeNetworks: {} routing network(s) for {} mode(s), seeded before "
                 + "the first router ({})", groups.size(), modes.size(), note);
    }
}
