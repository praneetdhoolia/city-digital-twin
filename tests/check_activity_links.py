"""Run the pinned native access-routing probe without compiling shared classes.

This synthetic routing check is not a city run or a demand/calibration result.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'src/setup')]
import install_paths
import registry
from registry import param_config

install_paths.activate(persist=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mobsim', action='store_true', help='Also execute a tiny synthetic physical access journey.')
    args = parser.parse_args()
    declaration = registry.load().field('RUN.routing.activity_link_assignment').copy()
    declaration['value'] = 'mode_specific_access'
    fields = {'RUN.routing.activity_link_assignment': declaration,
              'FIXTURE.access': dict(value='accessEgressModeToLink', units='policy', source='definition',
                                     status='active', matsim_param='routing.accessEgressType')}
    cfg = registry.Config(fields, {key: 'fixture' for key in fields}, [])
    suffix = '.exe' if os.name == 'nt' else ''
    jars = str(REPO / '.tools/run-stack/lib/*')
    with tempfile.TemporaryDirectory(prefix='activity-links-') as work:
        xml = Path(work, 'config.xml')
        xml.write_text(param_config.emit('matsim', cfg), encoding='utf-8')
        sources = [REPO / 'src/java/citysim/ActivityLinksConfigGroup.java',
                   REPO / 'src/java/citysim/ActivityLinkAssigner.java',
                   REPO / 'tests/fixtures/ActivityLinksProbe.java']
        probes = ['citysim.ActivityLinksProbe']
        if args.mobsim:
            sources.extend([REPO / 'src/java/citysim/TolerantAgentSource.java',
                            REPO / 'src/java/citysim/CappedSpeedTravelTime.java',
                            REPO / 'tests/fixtures/PhysicalAccessProbe.java'])
            probes.append('citysim.PhysicalAccessProbe')
        subprocess.run([str(REPO / ('.tools/jdk/bin/javac' + suffix)), '-cp', jars, '-d', work,
                        *map(str, sources)], check=True)
        for probe in probes:
            result = subprocess.run([str(REPO / ('.tools/jdk/bin/java' + suffix)), '-cp', work + os.pathsep + jars,
                                     probe, str(xml)], capture_output=True, text=True,
                                    encoding='utf-8', errors='replace', timeout=60)
            if result.returncode:
                print(result.stdout[-8000:]); print(result.stderr[-8000:])
                raise SystemExit(result.returncode)
            print('\n'.join(line for line in result.stdout.splitlines() if line.startswith('PASS:')))


if __name__ == '__main__':
    main()
