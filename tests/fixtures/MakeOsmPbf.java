import java.io.*;
import java.nio.file.*;
import de.topobyte.osm4j.core.model.iface.*;
import de.topobyte.osm4j.pbf.seq.PbfWriter;
import de.topobyte.osm4j.xml.dynsax.OsmXmlIterator;

/** Synthetic integration fixture encoder; uses the same pinned dependency. */
class MakeOsmPbf {
    public static void main(String[] args) throws Exception {
        try (InputStream input = Files.newInputStream(Path.of(args[0]));
             OutputStream output = Files.newOutputStream(Path.of(args[1]))) {
            PbfWriter writer = new PbfWriter(output, false);
            for (EntityContainer entry : new OsmXmlIterator(input, false)) {
                switch (entry.getType()) {
                    case Node -> writer.write((OsmNode) entry.getEntity());
                    case Way -> writer.write((OsmWay) entry.getEntity());
                    case Relation -> writer.write((OsmRelation) entry.getEntity());
                }
            }
            writer.complete();
        }
    }
}
