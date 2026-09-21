"""Exercise city-owned boarding fares against native MATSim event contracts."""
from pathlib import Path
import os
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]


def main():
    suffix = '.exe' if os.name == 'nt' else ''
    jars = str(REPO / '.tools/run-stack/lib/*')
    sources = [REPO / 'src/java/citysim' / name for name in (
        'BoardingFareTable.java', 'BoardingFareConfigGroup.java', 'BoardingFareHandler.java', 'PtFareConfigGroup.java',
        'RaptorFareCostCalculator.java', 'RaptorModeCostCalculator.java', 'RaptorModeCostConfigGroup.java')]
    sources.append(REPO / 'tests/fixtures/BoardingFareProbe.java')
    sources.append(REPO / 'tests/fixtures/RaptorFareProbe.java')
    with tempfile.TemporaryDirectory(prefix='boarding-fares-') as work:
        subprocess.run([str(REPO / ('.tools/jdk/bin/javac' + suffix)), '-cp', jars,
                        '-d', work, *map(str, sources)], check=True)
        result = subprocess.run([str(REPO / ('.tools/jdk/bin/java' + suffix)),
                                 '-cp', work + os.pathsep + jars, 'citysim.BoardingFareProbe', work],
                                capture_output=True, encoding='utf-8', errors='replace', timeout=60)
        if result.returncode:
            print(result.stdout[-6000:]); print(result.stderr[-6000:])
            raise SystemExit(result.returncode)
        print('\n'.join(line for line in result.stdout.splitlines() if line.startswith('PASS:')))
        result = subprocess.run([str(REPO / ('.tools/jdk/bin/java' + suffix)),
                                 '-cp', work + os.pathsep + jars, 'citysim.RaptorFareProbe', work],
                                capture_output=True, encoding='utf-8', errors='replace', timeout=60)
        if result.returncode:
            print(result.stdout[-6000:]); print(result.stderr[-6000:])
            raise SystemExit(result.returncode)
        print('\n'.join(line for line in result.stdout.splitlines() if line.startswith('PASS:')))


if __name__ == '__main__':
    main()
