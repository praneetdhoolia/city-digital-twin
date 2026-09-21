"""Measure control-node loss in the pinned converter on a synthetic way.

This is a behaviour probe, not acceptance of that loss or a city simulation.
It uses source-file Java launch, leaving the project's compiled run classes alone.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import bootstrap_toolchain as toolchain

FIXTURE = '''<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0" lon="0"/>
  <node id="2" lat="0" lon="0.0001"><tag k="barrier" v="gate"/><tag k="access" v="no"/></node>
  <node id="3" lat="0" lon="0.0002"><tag k="highway" v="traffic_signals"/></node>
  <node id="4" lat="0" lon="0.0003"><tag k="railway" v="level_crossing"/></node>
  <node id="5" lat="0.0001" lon="0.0004"/>
  <node id="6" lat="0" lon="0.0005"/>
  <way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="5"/><nd ref="6"/>
    <tag k="highway" v="residential"/><tag k="oneway" v="no"/>
  </way>
</osm>'''


def probe(folder):
    java, jar = toolchain.require()
    source = Path(__file__).resolve().parent / 'fixtures/OsmControlNodeProbe.java'
    osm = folder / 'source.osm'
    osm.write_text(FIXTURE, encoding='utf-8', newline='\n')
    readings = []
    for keep in (False, True):
        name = 'keep' if keep else 'collapse'
        output = folder / (name + '.xml')
        result = subprocess.run([java, '--class-path', jar, str(source), str(osm), str(output), str(keep).lower()],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        (folder / (name + '.log')).write_text(result.stdout + '\n' + result.stderr, encoding='utf-8', newline='\n')
        if result.returncode:
            raise RuntimeError('Converter probe failed: ' + (result.stderr or result.stdout)[-4000:])
        root = ET.parse(output).getroot()
        nodes = {row.get('id'): row for row in root.findall('./nodes/node')}
        links = root.findall('./links/link')
        readings.append(dict(keep_paths=keep, retained_native_node_ids=sorted(nodes), links=len(links),
            control_nodes_present={node: node in nodes for node in ('2', '3', '4')},
            node_attributes={node: {a.get('name'): a.text for a in row.findall('./attributes/attribute')}
                             for node, row in sorted(nodes.items())},
            summed_directed_link_length_m=sum(float(row.get('length')) for row in links)))
    # Pin the measured behaviour so a changed toolchain cannot invalidate the
    # interpretation silently. These checks deliberately do not certify safety.
    assert readings[0]['retained_native_node_ids'] == ['1', '6'], readings[0]
    assert readings[1]['retained_native_node_ids'] == ['1', '2', '3', '4', '5', '6'], readings[1]
    assert not any(readings[0]['control_nodes_present'].values())
    assert all(readings[1]['control_nodes_present'].values())
    assert all(not attrs for r in readings for attrs in r['node_attributes'].values())
    with Path(jar).open('rb') as stream:
        jar_sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
    report = dict(probe='synthetic_native_control_nodes', readings=readings,
                  converter_jar_sha256=jar_sha256,
                  fixture_sha256=hashlib.sha256(FIXTURE.encode('utf-8')).hexdigest(),
                  city_network_accepted=False, simulation_executed=False,
                  conclusion='Collapsed geometry loses intermediate control nodes; preserving node geometry alone does not implement control behaviour.')
    (folder / 'probe.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Keep probe files in a new or empty scratch directory.')
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        if any(args.output.iterdir()):
            raise ValueError('Probe output directory must be empty')
        probe(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='osm-control-probe-') as folder:
            probe(Path(folder))


if __name__ == '__main__':
    main()
