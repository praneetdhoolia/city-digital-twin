"""Convert a PBF losslessly for model geometry using the pinned Java stack.

No clipping or modal interpretation takes place. Contributor metadata and PBF
header bounds are deliberately omitted; all model entities and tags survive.
The output is staged before replacement. Simulation classes are never rebuilt.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import bootstrap_toolchain as toolchain


def convert(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Input and output must be different files')
    manifest = toolchain.load_manifest()
    stack = next((c for c in (manifest or {}).get('components', []) if c['component'] == 'run-stack'), None)
    java = toolchain.java_path()
    if not java or not stack or toolchain._verify_run_stack(stack):
        raise ValueError('The pinned Java run stack must be present and verified')
    classpath = os.pathsep.join(str(Path(toolchain.RUN_STACK_LIB, name)) for name in sorted(stack['jars']))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='osm_conversion_', dir=output.parent) as temporary:
        staged = Path(temporary, 'network.osm.gz')
        result = subprocess.run([java, '--class-path', classpath,
                                 str(Path(__file__).with_name('OsmPbfToXml.java')),
                                 str(source), str(staged)], check=True, text=True,
                                encoding='utf-8', capture_output=True)
        counts = json.loads(result.stdout)
        if not counts.get('nodes'):
            raise ValueError('PBF contains no nodes')
        os.replace(staged, output)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('output')
    args = parser.parse_args()
    print(json.dumps(convert(args.source, args.output)))


if __name__ == '__main__':
    main()
