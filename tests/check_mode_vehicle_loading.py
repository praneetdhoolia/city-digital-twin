"""Local-only check: the pinned MATSim reader and QVehicle use declared physics.

Requires the pinned JDK/run stack and pytest (for the shared synthetic fixture).
No controller, simulation arm or shared classes compilation. MATSim may resolve
its vehicle XML schema through its normal reader.
"""
from pathlib import Path
import os
import runpy
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src/setup'))
import install_paths
install_paths.activate(persist=False)


def main():
    suffix = '.exe' if os.name == 'nt' else ''
    javac = REPO / ('.tools/jdk/bin/javac' + suffix)
    java = REPO / ('.tools/jdk/bin/java' + suffix)
    jars = str(REPO / '.tools/run-stack/lib/*')
    fixture = runpy.run_path(str(REPO / 'tests/unit/test_mode_vehicles.py'))
    cfg = fixture['configuration']({'V.compact.pce': .8, 'V.compact.speed': 54})
    with tempfile.TemporaryDirectory(prefix='mode-vehicles-') as temporary:
        xml = Path(temporary, 'vehicles.xml')
        fixture['write_mode_vehicles'](xml, cfg)
        subprocess.run([str(javac), '-cp', jars, '-d', temporary,
                        str(REPO / 'tests/fixtures/ModeVehicleProbe.java')], check=True)
        subprocess.run([str(java), '-cp', temporary + os.pathsep + jars,
                        'ModeVehicleProbe', str(xml)], check=True)


if __name__ == '__main__':
    main()
