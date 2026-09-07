"""Where an iteration's wall time actually goes, read from the JVM itself.

`RUN.machine.jfr_profile` puts a Java Flight Recorder recording beside a run
(`<run>/profile.jfr`). This reads it and answers, in one page:

  * which THREAD POOL the CPU went to — the mobsim's own workers, the
    replanning/routing pool, the event-handler pool, the JVM's collector, the
    single main thread — because a phase that is one number on MATSim's
    stopwatch is several pools underneath;
  * which PHASE each sample belongs to, attributed from the OUTERMOST frame
    that matches a known phase root, so a stack deep inside a routing call
    made from replanning is charged to replanning and not to the router;
  * which METHODS are hot, both as top-of-stack (where the cycles are spent)
    and as phase roots (which call sites they hang off);
  * how much of it is this project's OWN code (`citysim.*`) rather than
    MATSim's, which is the only figure that says whether a cut is ours to
    make.

Nothing here reads or writes model state. A recording is an observation of
threads that were running anyway: a profiled run and an unprofiled one are
the same run, and neither this script nor the flag that produces the
recording opens a comparability family.

Usage
-----
    python src/analyse/profile_run.py --run <run-name-or-dir>
    python src/analyse/profile_run.py --run <run> --iterations 2:3
    python src/analyse/profile_run.py --jfr path/to/profile.jfr --top 40
    python src/analyse/profile_run.py --run <run> --json out.json

**Pass `--iterations` for anything about an arm.** Without it the recording
includes everything before iteration 0 — MATSim routes every agent's plan once
in `PersonPrepareForSim`, which is minutes of every thread on a 25 % run and
was half of all samples on the first probe taken this way. A 300-iteration arm
pays that once; its iterations are what a cut has to move.

The `jfr` tool ships with the pinned JDK; this finds it under `.tools/jdk`
and falls back to whatever is on PATH.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, 'src'))

# ---------------------------------------------------------------------------
# The vocabulary. A phase root is the OUTERMOST frame that says what a stack
# is doing; a pool rule maps a thread name to the pool it belongs to. Both are
# framework-level MATSim/JVM facts, not one city's, and both are stated here
# rather than guessed per run so two profiles are comparable.
# ---------------------------------------------------------------------------

PHASE_ROOTS = [
    # (label, regex over the fully-qualified frame)
    ('mobsim: netsim engine',
     r'qnetsimengine\.(QNetsimEngine|AbstractQNetsimEngine'
     r'|QNetsimEngineWithThreadpool|QNetsimEngineRunner|NetElementActivator)'),
    ('mobsim: transit engine', r'qsim\.pt\.TransitQSimEngine'),
    ('mobsim: activity engine', r'qsim\.ActivityEngine'),
    ('mobsim: teleportation', r'qsim\.TeleportationEngine'),
    ('mobsim: agent source / insertion',
     r'qsim\.(PopulationAgentSource|AgentFactory)|citysim\.TolerantAgentSource'),
    ('mobsim: signals', r'contrib\.signals|citysim\.(Scats|TramPriority)'),
    ('mobsim: our qsim engines',
     r'citysim\.(JointRideEngine|GenericRouteTeleporter'
     r'|HouseholdCarDepartureHandler)'),
    ('mobsim: qsim loop', r'qsim\.QSim\.'),
    ('events: dispatch',
     r'events\.(ParallelEventsManager|EventsManagerImpl'
     r'|SimStepParallelEventsManagerImpl)'),
    ('events: travel time calculator', r'trafficmonitoring\.TravelTimeCalculator'),
    ('events: scoring (experienced plans)',
     r'scoring\.(EventsToActivities|EventsToLegs|ScoringFunctionsForPopulation)'),
    ('events: our handlers',
     r'citysim\.(RunTelemetry|BikeStressScoring|ParkingChargeHandler'
     r'|PtFareChargeHandler|FareChargeHandler)'),
    ('events: writing', r'algorithms\.EventWriter'),
    ('replanning: strategy manager',
     r'replanning\.(StrategyManager|GenericStrategyManager|PlanStrategyImpl)'),
    ('replanning: routing', r'core\.router\.|PlanRouter|TripRouter'),
    ('replanning: mode choice',
     r'ChooseRandomLegModeForSubtour|SubtourModeChoice'
     r'|citysim\.GatedSubtourModeChoice'),
    ('replanning: time mutation', r'TimeAllocationMutator|TripPlanMutate'),
    ('replanning: our listeners',
     r'citysim\.(EscortCoherenceListener|RidePairingEngine|TaxiFleetEngine'
     r'|HouseholdVehicleRoster)'),
    ('prepareForMobsim: person prepare', r'PersonPrepareForSim|PrepareForSimImpl'),
    ('prepareForMobsim: network filter',
     r'TransportModeNetworkFilter|NetworkUtils\.createNetwork'),
    ('prepareForMobsim', r'PrepareForMobsim'),
    ('scoring', r'core\.scoring\.'),
    ('io: reading',
     r'core\.(network|population|utils)\.io\.[A-Za-z]*Reader|MatsimXmlParser'),
    ('io: writing', r'core\.(network|population)\.io\.[A-Za-z]*Writer|IOUtils'),
    ('controler', r'core\.controler\.'),
]

POOL_RULES = [
    ('mobsim workers', r'^(qnetsimengine|QNetsimEngine|pool-.*netsim)'),
    ('events handlers', r'^(matsim-eventsmanager|events|SimStepParallelEvents)'),
    ('replanning / routing', r'^(pool-|ForkJoinPool|PersonAlgorithm|matsim-parallel)'),
    ('main', r'^main$'),
    ('GC', r'^(GC |G1 |Parallel GC)'),
    ('JIT', r'^(C1 |C2 |CompilerThread)'),
    ('JVM other', r'^(VM |Reference Handler|Finalizer|Signal Dispatcher|Notification|'
                  r'Common-Cleaner|Attach|JFR |Monitor Ctrl)'),
]

SAMPLE_START = re.compile(r'^jdk\.(ExecutionSample|NativeMethodSample)\s*\{')
START_LINE = re.compile(r'startTime\s*=\s*(\d{2}:\d{2}:\d{2})')
THREAD_LINE = re.compile(r'sampledThread\s*=\s*"([^"]*)"')
STATE_LINE = re.compile(r'^\s*state\s*=\s*"([^"]*)"')
FRAME_LINE = re.compile(r'^\s+([A-Za-z_$][\w$.]*\.[\w$<>]+)\(')


def jfr_tool() -> str:
    """The `jfr` binary: the pinned JDK's, else whatever is on PATH."""
    for name in ('jfr.exe', 'jfr'):
        cand = os.path.join(REPO, '.tools', 'jdk', 'bin', name)
        if os.path.exists(cand):
            return cand
    return 'jfr'


def resolve_recording(run, jfr) -> str:
    if jfr:
        return jfr
    if not run:
        raise SystemExit('give --run <name> or --jfr <file>')
    if os.path.isdir(run):
        cand = os.path.join(run, 'profile.jfr')
    else:
        cand = os.path.join(REPO, 'results', 'raw', run, 'profile.jfr')
    if not os.path.exists(cand):
        raise SystemExit(
            'no recording at %s\n'
            'A run only carries one when it was launched with '
            'RUN.machine.jfr_profile=true (an overlay, or '
            '--config-set RUN.machine.jfr_profile=true).' % cand)
    return cand


def classify_pool(thread: str) -> str:
    for label, pattern in POOL_RULES:
        if re.search(pattern, thread):
            return label
    return 'other (%s)' % re.sub(r'[-_ ]?\d+$', '', thread or 'unnamed')


def classify_phase(frames: list) -> str:
    """The OUTERMOST frame that names a phase.

    `jfr print` lists the stack innermost-first, so the outermost frame is the
    last one. Scanning from there charges a routing call made by replanning to
    replanning, which is the attribution a phase table needs; scanning from the
    top would charge every phase to the router.
    """
    for frame in reversed(frames):
        for label, pattern in PHASE_ROOTS:
            if re.search(pattern, frame):
                return label
    return 'unattributed'


def iteration_window(run_dir: str, first: int, last: int):
    """(hh:mm:ss, hh:mm:ss) spanning iterations `first`..`last` inclusive.

    Read from the run's OWN stopwatch, so the window is the iterations MATSim
    timed rather than a guess. It exists because a whole-recording profile is
    dominated by what happens BEFORE iteration 0: MATSim routes every agent's
    plan once in PersonPrepareForSim, which on a 25 % run is minutes of every
    thread and half of all samples, and which a 300-iteration arm pays once.
    Profiling an arm means profiling its iterations.
    """
    path = os.path.join(run_dir, 'output', 'stopwatch.csv')
    try:
        with open(path, encoding='utf-8') as fh:
            rows = [ln.rstrip('\n').split(';') for ln in fh if ln.strip()]
    except OSError:
        return None
    if len(rows) < 2:
        return None
    header = rows[0]
    try:
        b = header.index('BEGIN iteration')
        e = header.index('END iteration')
    except ValueError:
        return None
    begins, ends = {}, {}
    for r in rows[1:]:
        try:
            n = int(r[0])
        except (ValueError, IndexError):
            continue
        if b < len(r) and r[b]:
            begins[n] = r[b]
        if e < len(r) and r[e]:
            ends[n] = r[e]
    if first not in begins or last not in ends:
        return None
    return begins[first], ends[last]


def read_samples(recording: str, depth: int, quiet: bool = False, window=None):
    """Stream `jfr print` and yield (thread, state, frames).

    `window` is an inclusive (start, end) pair of `hh:mm:ss` strings; a sample
    outside it is dropped.
    """
    cmd = [jfr_tool(), 'print', '--events', 'jdk.ExecutionSample',
           '--stack-depth', str(depth), recording]
    if not quiet:
        print('reading %s' % recording, file=sys.stderr)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True,
                            encoding='utf-8', errors='replace', bufsize=1 << 20)
    thread = state = None
    frames = []
    inside = False
    keep = True
    for line in proc.stdout:
        if SAMPLE_START.match(line):
            if inside and frames and keep:
                yield thread, state, frames
            inside, thread, state, frames, keep = True, None, None, [], True
            continue
        if not inside:
            continue
        if window is not None:
            m = START_LINE.search(line)
            if m:
                keep = window[0] <= m.group(1) <= window[1]
                continue
        m = THREAD_LINE.search(line)
        if m:
            thread = m.group(1)
            continue
        m = STATE_LINE.match(line)
        if m:
            state = m.group(1)
            continue
        m = FRAME_LINE.match(line)
        if m:
            frames.append(m.group(1))
    if inside and frames and keep:
        yield thread, state, frames
    proc.stdout.close()
    err = proc.stderr.read()
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit('jfr print failed (%d):\n%s' % (proc.returncode, err))


def pct(n: int, total: int) -> str:
    return '%5.1f%%' % (100.0 * n / total) if total else '    -'


def table(title: str, counts, total: int, limit: int, width: int = 62) -> None:
    print()
    print(title)
    print('-' * (width + 18))
    for key, n in counts.most_common(limit):
        label = key if len(key) <= width else '...' + key[-(width - 3):]
        print('%-*s %8d %s' % (width, label, n, pct(n, total)))
    rest = total - sum(n for _, n in counts.most_common(limit))
    if rest > 0:
        print('%-*s %8d %s' % (width, '(everything else)', rest,
                               pct(rest, total)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run', help='run name under results/raw, or a directory')
    ap.add_argument('--jfr', help='a .jfr recording to read directly')
    ap.add_argument('--top', type=int, default=25,
                    help='rows per table (default 25)')
    ap.add_argument('--depth', type=int, default=64,
                    help='stack depth to read (default 64)')
    ap.add_argument('--iterations', metavar='FIRST:LAST',
                    help="profile only these iterations, read from the run's "
                         "own stopwatch. Without it the recording includes "
                         "MATSim's one-off PersonPrepareForSim, which a "
                         "300-iteration arm pays once and which dominates a "
                         "short probe.")
    ap.add_argument('--json', help='also write the tallies to this file')
    ap.add_argument('--own-only', action='store_true',
                    help='only the hot methods in this project (citysim.*)')
    args = ap.parse_args(argv)

    recording = resolve_recording(args.run, args.jfr)

    window = None
    if args.iterations:
        run_dir = os.path.dirname(recording)
        try:
            first, last = (int(x) for x in args.iterations.split(':'))
        except ValueError:
            raise SystemExit('--iterations wants FIRST:LAST, e.g. 2:3')
        window = iteration_window(run_dir, first, last)
        if window is None:
            raise SystemExit(
                'could not read iterations %s from %s'
                % (args.iterations,
                   os.path.join(run_dir, 'output', 'stopwatch.csv')))

    by_pool = collections.Counter()
    by_phase = collections.Counter()
    by_top = collections.Counter()
    by_own = collections.Counter()
    by_pool_phase = collections.defaultdict(collections.Counter)
    total = 0
    own_total = 0

    for thread, _state, frames in read_samples(recording, args.depth,
                                               window=window):
        total += 1
        pool = classify_pool(thread or '')
        phase = classify_phase(frames)
        by_pool[pool] += 1
        by_phase[phase] += 1
        by_top[frames[0]] += 1
        by_pool_phase[pool][phase] += 1
        own = next((f for f in frames if f.startswith('citysim.')), None)
        if own:
            own_total += 1
            by_own[own] += 1

    if not total:
        raise SystemExit(
            'the recording holds no execution samples in that window. A run '
            'shorter than a few seconds, or one whose JVM was killed before '
            'the recording was dumped, produces an empty profile.')

    print('=' * 80)
    print('WHERE THE TIME WENT - %s' % os.path.relpath(recording, REPO))
    print('%d execution samples; every figure below is a share of those, '
          'which is a share of CPU time, not of wall time.' % total)
    if window:
        print("iterations %s only, %s to %s from the run's own stopwatch"
              % (args.iterations, window[0], window[1]))
    print('=' * 80)

    table('BY THREAD POOL - which workers burned the CPU', by_pool, total,
          args.top)
    table('BY PHASE - attributed from the outermost frame that names one',
          by_phase, total, args.top)
    if not args.own_only:
        table('HOT METHODS - top of stack, where the cycles actually went',
              by_top, total, args.top)
    table("THIS PROJECT'S OWN CODE - innermost citysim.* frame on the stack "
          "(%s of all samples)" % pct(own_total, total),
          by_own, total, args.top)

    print()
    print('PHASE WITHIN POOL')
    print('-' * 80)
    for pool, n in by_pool.most_common(6):
        print('%s  (%s of all samples)' % (pool, pct(n, total)))
        for phase, m in by_pool_phase[pool].most_common(6):
            print('    %-58s %8d %s' % (phase, m, pct(m, n)))

    print()
    print("Read it with the run's own output/stopwatch.csv beside it: the "
          "stopwatch says how long each MATSim phase took in WALL time, this "
          "says which threads and methods filled it. Nothing here is a result.")

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump({
                'recording': os.path.relpath(recording, REPO).replace(os.sep, '/'),
                'window': list(window) if window else None,
                'samples': total,
                'own_samples': own_total,
                'by_pool': dict(by_pool),
                'by_phase': dict(by_phase),
                'by_top_frame': dict(by_top.most_common(200)),
                'by_own_frame': dict(by_own.most_common(200)),
                'phase_within_pool': {k: dict(v)
                                      for k, v in by_pool_phase.items()},
            }, fh, indent=2, sort_keys=True)
        print('wrote %s' % args.json)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
