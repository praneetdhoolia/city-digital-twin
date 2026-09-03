#!/usr/bin/env python
"""Run the Java gate probes on the signals run stack (issue #73, #125, #113).

The probes are the ONLY gate between the citysim QSim assembly and the
signals contrib physics (DECISIONS.md 9.74): `SignalsAssemblyProbe` proves a
red light actually gates the buffer under the citysim component reordering,
and `TramPriorityProbe` proves the tram-priority controller extends a green
for a detected tram and runs the plan verbatim when told `off`. No scenario
touches signals before both PASS.

Stdlib only, no arguments. It assembles the classpath from
`.tools/run-stack/lib` (every jar, resolved and sha256-pinned by
`src/setup/bootstrap_toolchain.py --run-stack`) plus `.tools/classes-signals`
(compiled by the same bootstrap, or by this script if the sources are newer),
runs every probe with the pinned JDK, and echoes each probe's one-line JSON
verdict. Exit code 0 only if every probe exits 0. `ScatsPriorityProbe` (#125)
proves the SCATS priority extension moves the tram's drop on a three-stage
plan and refuses honestly when the tram stage is last; `RemodeRestoreProbe`
(#113) proves a trip forced to walk gets its mode back through the re-find
both engines now share.
"""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, '.tools')
LIB = os.path.join(TOOLS, 'run-stack', 'lib')
CLASSES_SIGNALS = os.path.join(TOOLS, 'classes-signals')
PROBES = ('citysim.SignalsAssemblyProbe', 'citysim.TramPriorityProbe',
          # #125: SCATS priority on a three-stage plan, donor direction
          'citysim.ScatsPriorityProbe',
          # #113: the re-moded trip restore, shared by ride and taxi
          'citysim.RemodeRestoreProbe')


def java_exe():
    for cand in (os.path.join(TOOLS, 'jdk', 'bin', 'java.exe'),
                 os.path.join(TOOLS, 'jdk', 'bin', 'java')):
        if os.path.exists(cand):
            return cand
    raise SystemExit('no pinned JDK under .tools/jdk - run '
                     'python src/setup/bootstrap_toolchain.py')


def javac_exe():
    for cand in (os.path.join(TOOLS, 'jdk', 'bin', 'javac.exe'),
                 os.path.join(TOOLS, 'jdk', 'bin', 'javac')):
        if os.path.exists(cand):
            return cand
    raise SystemExit('no pinned javac under .tools/jdk - run '
                     'python src/setup/bootstrap_toolchain.py')


def classpath(jars):
    return os.pathsep.join([CLASSES_SIGNALS] + jars)


def ensure_compiled(jars):
    """Recompile into .tools/classes-signals when any source is newer."""
    srcs = sorted(glob.glob(os.path.join(ROOT, 'src', 'java', '*', '*.java'))
                  + glob.glob(os.path.join(ROOT, 'src', 'java_signals', '*',
                                           '*.java')))
    if not srcs:
        raise SystemExit('no java sources - checkout incomplete')
    marker = os.path.join(CLASSES_SIGNALS, 'citysim',
                          'CitysimSignalsControler.class')
    newest_src = max(os.path.getmtime(s) for s in srcs)
    if os.path.exists(marker) and os.path.getmtime(marker) >= newest_src:
        return
    os.makedirs(CLASSES_SIGNALS, exist_ok=True)
    out = subprocess.run(
        [javac_exe(), '-cp', os.pathsep.join(jars), '-d', CLASSES_SIGNALS]
        + srcs,
        capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit('javac (signals) FAILED\n%s'
                         % (out.stderr or out.stdout))


def main():
    jars = sorted(glob.glob(os.path.join(LIB, '*.jar')))
    if not jars:
        raise SystemExit('no run stack under .tools/run-stack/lib - run '
                         'python src/setup/bootstrap_toolchain.py --run-stack')
    ensure_compiled(jars)
    cp = classpath(jars)
    failed = False
    for probe in PROBES:
        print('== %s ==' % probe, flush=True)
        # the probes chatter MATSim logging on stdout/stderr and end with one
        # JSON line on stdout; keep the JSON, surface the tail on failure
        out = subprocess.run([java_exe(), '-cp', cp, probe],
                             capture_output=True, text=True)
        json_line = ''
        for line in (out.stdout or '').splitlines():
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                json_line = line
        if json_line:
            print(json_line, flush=True)
        if out.returncode != 0:
            failed = True
            print('%s FAILED (exit %d)' % (probe, out.returncode))
            if not json_line:
                tail = (out.stderr or out.stdout or '').splitlines()[-30:]
                print('\n'.join(tail))
        else:
            print('%s PASS' % probe, flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
