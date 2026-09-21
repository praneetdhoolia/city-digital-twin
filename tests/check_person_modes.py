"""Check explicit person mode availability using the pinned native MATSim reader."""
from pathlib import Path
import os
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]


def main():
    suffix = '.exe' if os.name == 'nt' else ''
    jars = str(REPO / '.tools/run-stack/lib/*')
    sources = [REPO / 'src/java/citysim' / name for name in (
        'ModeAvailabilityConfigGroup.java', 'AvailabilityModesCalculator.java',
        'PtSubmodeMainModeIdentifier.java')]
    sources.append(REPO / 'tests/fixtures/PersonModesProbe.java')
    with tempfile.TemporaryDirectory(prefix='person-modes-') as work:
        subprocess.run([str(REPO / ('.tools/jdk/bin/javac' + suffix)), '-cp', jars,
                        '-d', work, *map(str, sources)], check=True)
        result = subprocess.run([str(REPO / ('.tools/jdk/bin/java' + suffix)),
                                 '-cp', work + os.pathsep + jars, 'citysim.PersonModesProbe',
                                 str(Path(work, 'population.xml'))],
                                capture_output=True, encoding='utf-8', errors='replace', timeout=60)
        if result.returncode:
            print(result.stdout[-8000:]); print(result.stderr[-8000:])
            raise SystemExit(result.returncode)
        print('\n'.join(line for line in result.stdout.splitlines() if line.startswith('PASS:')))


if __name__ == '__main__':
    main()
