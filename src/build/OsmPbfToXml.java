import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.zip.GZIPOutputStream;
import de.topobyte.osm4j.core.model.iface.*;
import de.topobyte.osm4j.pbf.seq.PbfIterator;
import de.topobyte.osm4j.xml.output.OsmXmlOutputStream;

/** Streaming format conversion with the already pinned osm4j dependencies.
 * Preserves all nodes, way references, relation members and tags. Does not
 * clip, simplify, infer permissions or retain contributor metadata.
 * Run in Java source-file mode, independently of the simulation classes.
 */
class OsmPbfToXml {
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("Expected input.osm.pbf output.osm.gz");
        }
        Path input = Path.of(args[0]), output = Path.of(args[1]);
        long nodes = 0, ways = 0, relations = 0;
        try (InputStream source = new BufferedInputStream(Files.newInputStream(input));
             OutputStream target = new GZIPOutputStream(new BufferedOutputStream(
                 Files.newOutputStream(output, StandardOpenOption.CREATE_NEW)));
             PrintWriter text = new PrintWriter(new OutputStreamWriter(target, StandardCharsets.UTF_8))) {
            PbfIterator iterator = new PbfIterator(source, false);
            OsmXmlOutputStream writer = new OsmXmlOutputStream(text, false);
            for (EntityContainer container : iterator) {
                switch (container.getType()) {
                    case Node -> { writer.write((OsmNode) container.getEntity()); nodes++; }
                    case Way -> { writer.write((OsmWay) container.getEntity()); ways++; }
                    case Relation -> { writer.write((OsmRelation) container.getEntity()); relations++; }
                    default -> throw new IOException("Unsupported OSM entity type");
                }
            }
            writer.complete();
            text.flush();
            if (text.checkError()) throw new IOException("OSM XML write failed");
        }
        System.out.println("{\"nodes\":"+nodes+",\"ways\":"+ways+",\"relations\":"+relations+"}");
    }
}
