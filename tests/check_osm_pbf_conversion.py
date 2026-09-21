"""Local integration check: pinned PBF conversion preserves routing semantics."""
import gzip
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

import bootstrap_toolchain as toolchain
from convert_osm_pbf import convert
from osm_parse import parse

FIXTURE = '''<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
<node id="5000000001" lat="0" lon="0"><tag k="name" v="द्वार &amp; café"/></node>
<node id="5000000002" lat="0.0000001" lon="-0.0000001"><tag k="barrier" v="bollard"/></node>
<node id="5000000003" lat="1.25" lon="2.5"/>
<way id="6000000001"><nd ref="5000000001"/><nd ref="5000000002"/>
<tag k="highway" v="service"/><tag k="access:conditional" v="no @ (Mo-Fr 08:00-09:00)"/></way>
<way id="6000000002"><nd ref="5000000002"/><nd ref="5000000003"/><nd ref="5000000002"/>
<tag k="oneway" v="-1"/></way>
<relation id="7000000001"><member type="way" ref="6000000001" role="from"/>
<member type="node" ref="5000000002" role="via"/><member type="way" ref="6000000002" role="to"/>
<tag k="type" v="restriction"/><tag k="restriction" v="no_left_turn"/><tag k="except" v="bus;bicycle"/></relation>
<relation id="7000000002"><member type="relation" ref="7000000001" role="subarea"/>
<member type="node" ref="5000000001" role="platform"/><tag k="type" v="collection"/></relation>
</osm>'''


def main():
    root = Path(__file__).resolve().parents[1]
    stack = next(c for c in toolchain.load_manifest()['components'] if c['component'] == 'run-stack')
    classpath = os.pathsep.join(str(Path(toolchain.RUN_STACK_LIB, n)) for n in sorted(stack['jars']))
    with tempfile.TemporaryDirectory(prefix='osm_fixture_') as temporary:
        folder = Path(temporary)
        xml, pbf = folder/'fixture.osm', folder/'fixture.osm.pbf'
        xml.write_text(FIXTURE, encoding='utf-8')
        subprocess.run([toolchain.java_path(), '--class-path', classpath,
                        str(root/'tests/fixtures/MakeOsmPbf.java'), str(xml), str(pbf)], check=True)
        expected = list(parse(xml))
        hashes = []
        for name in ('first.osm.gz', 'second.osm.gz'):
            output = folder/name
            assert convert(pbf, output) == dict(nodes=3, ways=2, relations=2)
            assert list(parse(output)) == expected
            hashes.append(hashlib.sha256(output.read_bytes()).hexdigest())
        assert hashes[0] == hashes[1], 'Identical source produced different compressed bytes'
        # A failed conversion must leave the previous successful output intact.
        pbf.write_bytes(b'not a PBF')
        try:
            convert(pbf, folder/'first.osm.gz')
        except (subprocess.CalledProcessError, ValueError):
            pass
        else:
            raise AssertionError('Malformed PBF was accepted')
        assert hashlib.sha256((folder/'first.osm.gz').read_bytes()).hexdigest() == hashes[0]
    print('OSM PBF round trip: tags, Unicode, large IDs, zero coordinates, repeated nodes, restrictions and nested relations preserved; deterministic gzip; failed conversion preserves output.')


if __name__ == '__main__':
    main()
