import org.matsim.pt2matsim.config.OsmConverterConfigGroup;
import org.matsim.pt2matsim.run.Osm2MultimodalNetwork;

/** Synthetic converter probe. Defaults here are not city modelling values. */
class OsmControlNodeProbe {
    public static void main(String[] args) {
        if (args.length != 3) throw new IllegalArgumentException("input, output, keepPaths required");
        var config = OsmConverterConfigGroup.createDefaultConfig();
        config.setOsmFile(args[0]);
        config.setOutputNetworkFile(args[1]);
        config.setOutputCoordinateSystem("EPSG:3857");
        config.setKeepPaths(Boolean.parseBoolean(args[2]));
        config.setKeepTagsAsAttributes(true);
        config.setMaxLinkLength(Double.POSITIVE_INFINITY);
        Osm2MultimodalNetwork.run(config);
    }
}
